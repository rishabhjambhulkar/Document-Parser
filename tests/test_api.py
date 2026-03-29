import pytest
from app.models.job import JobStatus
from unittest.mock import AsyncMock

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_create_job_with_url(client, repo_override):
    # Mock the return value
    repo_override.create_job.return_value = AsyncMock(
        id="test-job-id",
        status=JobStatus.QUEUED,
        document_source="http://example.com/doc.pdf",
        created_at="2024-03-29T12:00:00Z"
    )

    response = client.post(
        "/api/v1/jobs",
        data={"document_url": "http://example.com/doc.pdf"}
    )
    
    # In my actual code, Job has `_id` alias, but response JSON should show `id` (or `_id` depending on alias setup)
    # pydantic `alias` on `_id` means input has `_id`, output uses `id` if `populate_by_name` is true.
    # Actually, response JSON uses the alias for the field unless `by_alias=False` is set in fastapi.
    # I set `id: str = Field(..., alias="_id")`.
    
    assert response.status_code == 201
    assert "document_source" in response.json()
    assert response.json()["document_source"] == "http://example.com/doc.pdf"

def test_create_job_no_data(client):
    response = client.post("/api/v1/jobs", data={})
    assert response.status_code == 400

def test_get_job(client, repo_override):
    # Mock get_job
    repo_override.get_job.return_value = AsyncMock(
        id="test-job-id",
        status=JobStatus.PROCESSING,
        document_source="test.pdf"
    )

    response = client.get("/api/v1/jobs/test-job-id")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

def test_get_job_not_found(client, repo_override):
    repo_override.get_job.return_value = None
    response = client.get("/api/v1/jobs/non-existent")
    assert response.status_code == 404
