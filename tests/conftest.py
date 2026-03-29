import pytest
from fastapi.testclient import TestClient
from main import app
from app.api.dependencies import rate_limiter, get_repository
from unittest.mock import MagicMock, AsyncMock

# Mock Repository
class MockRepository:
    def __init__(self):
        self.create_job = AsyncMock()
        self.get_job = AsyncMock()
        self.list_jobs = AsyncMock()
        self.update_job = AsyncMock()

@pytest.fixture
def client():
    # Use the test client for the app
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def mock_repo():
    return MockRepository()

@pytest.fixture
def repo_override(mock_repo):
    async def get_mock_repo():
        return mock_repo
    
    app.dependency_overrides[get_repository] = get_mock_repo
    yield mock_repo
    app.dependency_overrides.clear()
