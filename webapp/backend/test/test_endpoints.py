import os
import sys
from pathlib import Path
import pytest
import asyncio
from fastapi.testclient import TestClient

# Setup import paths
test_dir = Path(__file__).resolve().parent
backend_src_dir = test_dir.parent / "src"

if str(backend_src_dir) not in sys.path:
    sys.path.insert(0, str(backend_src_dir))

from core.config import settings

# Force SQLite in-memory for tests
settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.REQUIRE_AUTH = False  # Bypassed by default for easier integration checks

from api.main import app
from database import init_engine, create_tables

@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes in-memory SQLite tables before running each test case."""
    init_engine(settings.DATABASE_URL)
    
    # Run async table creation inside synchronous fixture
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(create_tables())
    finally:
        loop.close()
        
    yield

def test_health_endpoint():
    """Verifies that the health check endpoint returns 200 OK."""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_auth_config_endpoint():
    """Verifies that system configuration variables are returned correctly."""
    with TestClient(app) as client:
        response = client.get("/api/auth/config")
        assert response.status_code == 200
        assert response.json()["require_auth"] is False

def test_history_list_empty():
    """Verifies history list returns pagination wrappers empty items on startup."""
    with TestClient(app) as client:
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

def test_stats_empty():
    """Verifies stats values yield zero sums when empty."""
    with TestClient(app) as client:
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["average_shelf_life"] == 0.0
