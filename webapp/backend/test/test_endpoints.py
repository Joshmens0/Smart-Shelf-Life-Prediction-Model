import io
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from PIL import Image
from httpx import AsyncClient, ASGITransport

# Setup import paths
test_dir = Path(__file__).resolve().parent
backend_src_dir = test_dir.parent / "src"

if str(backend_src_dir) not in sys.path:
    sys.path.insert(0, str(backend_src_dir))

from core.config import settings

# Force SQLite in-memory for tests
settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.REQUIRE_AUTH = False

from api.main import app
from database import init_engine, create_tables

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Initializes in-memory SQLite tables before running each test case."""
    init_engine(settings.DATABASE_URL)
    await create_tables()
    yield

@pytest.mark.asyncio
async def test_health_endpoint():
    """Verifies that the health check endpoint returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Smart Shelf Life API"

@pytest.mark.asyncio
async def test_auth_config_endpoint():
    """Verifies that system configuration variables are returned correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/config")
        assert response.status_code == 200
        assert "require_auth" in response.json()

@pytest.mark.asyncio
async def test_auth_register_and_login():
    """Verifies user registration and login flow."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_resp = await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123!"}
        )
        assert reg_resp.status_code == 200
        assert reg_resp.json()["status"] == "ok"

        # Duplicate registration failure
        dup_resp = await client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "SecurePassword123!"}
        )
        assert dup_resp.status_code == 400

        # Login
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "SecurePassword123!"}
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert data["logged_in"] is True
        assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_history_list_empty():
    """Verifies history list returns pagination wrappers empty items on startup."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

@pytest.mark.asyncio
async def test_stats_empty():
    """Verifies stats values yield zero sums when empty."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["average_shelf_life"] == 0.0

@pytest.mark.asyncio
async def test_predict_validation_errors():
    """Verifies that invalid environment parameter returns 422 error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a small dummy image in memory
        img = Image.new("RGB", (224, 224), color=(73, 109, 137))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        response = await client.post(
            "/api/predict",
            files={"image": ("test.png", img_bytes.getvalue(), "image/png")},
            data={
                "temp": "25.0",
                "humidity": "65.0",
                "environment": "invalid-env",
                "item_name": "Test Mango"
            }
        )
        assert response.status_code == 422
