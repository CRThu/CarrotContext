"""Tests for permissions and user management"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import DATABASE_PATH
import aiosqlite


@pytest.fixture(autouse=True)
async def setup_db():
    """Initialize database for tests - clean ALL users to ensure first-user-is-admin works"""
    from app.database import init_db

    await init_db()
    # Clean ALL users before tests to ensure first-user-is-admin logic works
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM kb_permissions")
        await db.commit()
    yield
    # Cleanup after
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM kb_permissions")
        await db.commit()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def admin_token(client: AsyncClient):
    """Register and login as first user (admin)"""
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": "test_admin",
            "email": "admin@test.com",
            "password": "test123",
        },
    )
    assert resp.status_code == 200
    resp = await client.post(
        "/api/auth/login",
        json={"username": "test_admin", "password": "test123"},
    )
    return resp.json()["access_token"]


@pytest.fixture
async def user_token(client: AsyncClient, admin_token: str):
    """Register a regular user (second user) - depends on admin_token to ensure admin exists first"""
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": "test_regular_user",
            "email": "regular@test.com",
            "password": "test123",
        },
    )
    assert resp.status_code == 200
    resp = await client.post(
        "/api/auth/login",
        json={"username": "test_regular_user", "password": "test123"},
    )
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ============ Auth Tests ============


@pytest.mark.anyio
async def test_first_user_is_admin(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": "test_first_admin",
            "email": "first@test.com",
            "password": "test123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


@pytest.mark.anyio
async def test_second_user_is_regular(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/auth/register",
        json={
            "username": "test_second_user",
            "email": "second@test.com",
            "password": "test123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "user"


@pytest.mark.anyio
async def test_me_returns_role(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/auth/me", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


# ============ Admin Endpoints Tests ============


@pytest.mark.anyio
async def test_admin_list_users(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/auth/users", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert len(data["users"]) >= 1


@pytest.mark.anyio
async def test_non_admin_cannot_list_users(client: AsyncClient, user_token: str):
    resp = await client.get("/api/auth/users", headers=auth_header(user_token))
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_admin_change_user_role(
    client: AsyncClient, admin_token: str, user_token: str
):
    # Get user list to find user_id
    resp = await client.get("/api/auth/users", headers=auth_header(admin_token))
    users = resp.json()["users"]
    regular_user = next(u for u in users if u["username"] == "test_regular_user")

    resp = await client.put(
        f"/api/auth/users/{regular_user['id']}/role",
        json={"role": "admin"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


@pytest.mark.anyio
async def test_admin_cannot_change_own_role(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/auth/me", headers=auth_header(admin_token))
    admin_id = resp.json()["id"]

    resp = await client.put(
        f"/api/auth/users/{admin_id}/role",
        json={"role": "user"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_admin_delete_user(client: AsyncClient, admin_token: str, user_token: str):
    resp = await client.get("/api/auth/users", headers=auth_header(admin_token))
    users = resp.json()["users"]
    regular_user = next(u for u in users if u["username"] == "test_regular_user")

    resp = await client.delete(
        f"/api/auth/users/{regular_user['id']}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_admin_cannot_delete_self(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/auth/me", headers=auth_header(admin_token))
    admin_id = resp.json()["id"]

    resp = await client.delete(
        f"/api/auth/users/{admin_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


# ============ Permission Tests ============


@pytest.mark.anyio
async def test_set_kb_permission(client: AsyncClient, admin_token: str):
    # Create a knowledge base first
    resp = await client.post(
        "/api/knowledge",
        json={"name": "Perm Test KB", "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    if resp.status_code != 201:
        # KB might already exist from previous test run, try to get it
        resp = await client.get("/api/knowledge", headers=auth_header(admin_token))
        kbs = resp.json()
        kb = next((k for k in kbs if k["name"] == "Perm Test KB"), None)
        if kb:
            kb_id = kb["id"]
        else:
            pytest.skip("Cannot create KB")
            return
    else:
        kb_id = resp.json()["id"]

    # Set permission
    resp = await client.post(
        f"/api/knowledge/{kb_id}/permissions",
        json={"role": "editor"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_get_kb_permissions(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/knowledge",
        json={"name": "Perm Test KB2", "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    if resp.status_code != 201:
        resp = await client.get("/api/knowledge", headers=auth_header(admin_token))
        kbs = resp.json()
        kb = next((k for k in kbs if k["name"] == "Perm Test KB2"), None)
        if kb:
            kb_id = kb["id"]
        else:
            pytest.skip("Cannot create KB")
            return
    else:
        kb_id = resp.json()["id"]

    resp = await client.get(
        f"/api/knowledge/{kb_id}/permissions",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert "permissions" in resp.json()


@pytest.mark.anyio
async def test_non_admin_cannot_set_permissions(
    client: AsyncClient, user_token: str
):
    resp = await client.post(
        "/api/knowledge",
        json={"name": "Test Perm KB3", "description": "", "tags": []},
        headers=auth_header(user_token),
    )
    # Non-admin might not be able to create KB depending on permissions
    if resp.status_code == 201:
        kb_id = resp.json()["id"]
        resp = await client.post(
            f"/api/knowledge/{kb_id}/permissions",
            json={"role": "editor"},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 403
