import pytest
from unittest.mock import AsyncMock, patch
from main import app
from app.api.dependencies import rate_limiter, get_redis, get_repository
from app.models.job import Job, JobStatus
import asyncio

# Create a sample job for mocking
sample_job_data = {
    "_id": "664f1a2b3c4d5e6f7a8b9c0d",
    "status": JobStatus.QUEUED,
    "document_source": "http://example.com/doc.pdf",
    "webhook_url": "http://webhook.com",
    "created_at": "2026-03-29T15:00:00Z",
    "updated_at": "2026-03-29T15:00:00Z",
    "result": None
}
sample_job = Job(**sample_job_data)

# A fake Redis client to track increments
class FakeRedis:
    def __init__(self):
        self.count = 0
    
    async def incr(self, key):
        self.count += 1
        return self.count

    async def expire(self, key, seconds):
        return True

    async def close(self):
        pass

@pytest.mark.asyncio
async def test_rate_limit_load(client, repo_override):
    """
    Simulates sending 11 requests in the same second and verifies
    that the 11th request is blocked with 429 Too Many Requests.
    """
    
    # 1. Setup mock repository for successful creation
    repo_override.create_job.return_value = sample_job

    # 2. Setup fake redis for rate limiting
    fake_redis = FakeRedis()
    
    async def get_fake_redis():
        yield fake_redis

    # 3. Apply the overrides specifically for this test
    # We remove the global mock_rate_limiter and use the real one with fake redis
    original_overrides = app.dependency_overrides.copy()
    try:
        app.dependency_overrides[get_redis] = get_fake_redis
        if rate_limiter in app.dependency_overrides:
            del app.dependency_overrides[rate_limiter]
            
        # 4. Send 11 requests
        # We need to ensure request.client.host is not None for the rate limiter
        responses = []
        with patch("fastapi.Request.client", new_callable=AsyncMock) as mock_client:
            mock_client.host = "127.0.0.1"
            for _ in range(11):
                response = client.post(
                    "/api/v1/jobs",
                    json={
                        "document_source": "http://example.com/doc.pdf",
                        "webhook_url": "http://webhook.com"
                    }
                )
                responses.append(response)

        # 5. Assertions
        # First 10 should be successful (201)
        for i in range(10):
            assert responses[i].status_code == 201, f"Request {i+1} failed with {responses[i].status_code}"
            
        # The 11th should be rate-limited (429)
        assert responses[10].status_code == 429, f"11th request was not rate limited: {responses[10].status_code}"
        assert responses[10].json()["detail"] == "Rate limit exceeded. Max 10 requests per second."
        
    finally:
        # Restore environment
        app.dependency_overrides = original_overrides
