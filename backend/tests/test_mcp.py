import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_mcp_endpoint(client: AsyncClient):
    response = await client.get("/mcp/", follow_redirects=True)
    assert response.status_code in [200, 404, 405, 307]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "CarrotContext" in data["message"]
