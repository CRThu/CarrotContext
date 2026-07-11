import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    response = await client.post(
        "/api/auth/register",
        json={
            "username": f"user_{unique_id}",
            "email": f"{unique_id}@test.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"user_{unique_id}"
    assert "id" in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    username = f"login_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    username = f"wrong_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    username = f"dup_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    assert response.status_code == 400


# ============ get_current_user_from_token Tests ============


@pytest.mark.asyncio
async def test_get_current_user_from_token_valid(client: AsyncClient):
    from app.auth.service import create_access_token, get_current_user_from_token

    unique_id = str(uuid.uuid4())[:8]
    username = f"token_{unique_id}"
    resp = await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    user_id = resp.json()["id"]

    token = create_access_token(data={"sub": username, "user_id": user_id})
    user = await get_current_user_from_token(token)

    assert user is not None
    assert user["username"] == username
    assert user["id"] == user_id


@pytest.mark.asyncio
async def test_get_current_user_from_token_invalid():
    from app.auth.service import get_current_user_from_token

    user = await get_current_user_from_token("invalid.token.here")
    assert user is None


@pytest.mark.asyncio
async def test_get_current_user_from_token_nonexistent_user():
    from app.auth.service import create_access_token, get_current_user_from_token

    token = create_access_token(data={"sub": "ghost_user", "user_id": 99999})
    user = await get_current_user_from_token(token)
    assert user is None


# ============ Admin Endpoint Guard Tests ============


async def _register_and_login(client, username):
    unique_id = str(uuid.uuid4())[:8]
    uname = f"{username}_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": uname, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"username": uname, "password": "pass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, uname


@pytest.mark.asyncio
async def test_change_role_invalid_role(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_inv_role")
    resp = await client.put(
        "/api/auth/users/999/role",
        json={"role": "superadmin"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "无效的角色值" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_change_role_self_modification(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_self")
    # Get own user ID
    me = await client.get("/api/auth/me", headers=headers)
    user_id = me.json()["id"]
    resp = await client.put(
        f"/api/auth/users/{user_id}/role",
        json={"role": "user"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "不能修改自己的角色" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_change_role_nonexistent_user(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_ghost")
    resp = await client.put(
        "/api/auth/users/99999/role",
        json={"role": "user"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_self_forbidden(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_self_del")
    me = await client.get("/api/auth/me", headers=headers)
    user_id = me.json()["id"]
    resp = await client.delete(
        f"/api/auth/users/{user_id}",
        headers=headers,
    )
    assert resp.status_code == 400
    assert "不能删除自己" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_delete_nonexistent_user(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_del_ghost")
    resp = await client.delete(
        "/api/auth/users/99999",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_group_duplicate_name(client: AsyncClient):
    headers, _ = await _register_and_login(client, "admin_dup_grp")
    unique = str(uuid.uuid4())[:8]
    await client.post(
        "/api/auth/groups",
        json={"name": f"grp_{unique}"},
        headers=headers,
    )
    resp = await client.post(
        "/api/auth/groups",
        json={"name": f"grp_{unique}"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "组名已存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client: AsyncClient):
    # Register first user (becomes admin), then register a second user (non-admin)
    unique1 = str(uuid.uuid4())[:8]
    await client.post(
        "/api/auth/register",
        json={"username": f"admin_{unique1}", "email": f"adm_{unique1}@test.com", "password": "pass123"},
    )
    unique2 = str(uuid.uuid4())[:8]
    await client.post(
        "/api/auth/register",
        json={"username": f"normal_{unique2}", "email": f"norm_{unique2}@test.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"username": f"normal_{unique2}", "password": "pass123"},
    )
    token = resp.json()["access_token"]
    resp = await client.get(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
