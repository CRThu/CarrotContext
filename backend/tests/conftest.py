import warnings
import pytest
import aiosqlite
from httpx import ASGITransport, AsyncClient

from app.database import DATABASE_PATH, init_db
from app.main import app

# Suppress ResourceWarning from sqlite3 connections during gc.collect()
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed database.*")


@pytest.fixture(autouse=True)
async def _clean_db():
    """Clean all tables before each test to ensure isolation."""
    await init_db()
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM permission_groups")
        await db.execute("DELETE FROM user_groups")
        await db.execute("DELETE FROM access_rules")
        await db.commit()
    yield
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM permission_groups")
        await db.execute("DELETE FROM user_groups")
        await db.execute("DELETE FROM access_rules")
        await db.commit()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "CarrotContext" in response.json()["message"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
