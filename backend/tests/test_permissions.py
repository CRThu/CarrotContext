"""Tests for permissions, groups, and access rules"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import DATABASE_PATH
import aiosqlite


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def admin_token(client: AsyncClient):
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
    assert resp.json()["role"] == "admin"


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
    assert resp.json()["role"] == "user"


# ============ Group Management Tests ============


@pytest.mark.anyio
async def test_create_group(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "editors", "description": "Editors group"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "editors"


@pytest.mark.anyio
async def test_list_groups(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/auth/groups",
        json={"name": "viewers"},
        headers=auth_header(admin_token),
    )
    resp = await client.get(
        "/api/auth/groups",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["groups"]) >= 1


@pytest.mark.anyio
async def test_non_admin_cannot_create_group(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "test"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_add_remove_group_member(client: AsyncClient, admin_token: str, user_token: str):
    # Create group
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "test_group"},
        headers=auth_header(admin_token),
    )
    group_id = resp.json()["id"]

    # Get user id
    resp = await client.get("/api/auth/me", headers=auth_header(user_token))
    user_id = resp.json()["id"]

    # Add member
    resp = await client.post(
        f"/api/auth/groups/{group_id}/members",
        json={"user_id": user_id},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200

    # List members
    resp = await client.get(
        f"/api/auth/groups/{group_id}/members",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert any(m["user_id"] == user_id for m in resp.json())

    # Remove member
    resp = await client.delete(
        f"/api/auth/groups/{group_id}/members/{user_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


# ============ Access Rules Tests ============


@pytest.mark.anyio
async def test_set_access_rule(client: AsyncClient, admin_token: str):
    # Create KB
    kb_name = f"perm-test-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Create group
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "readers"},
        headers=auth_header(admin_token),
    )
    group_id = resp.json()["id"]

    # Set access rule
    resp = await client.post(
        f"/api/knowledge/{kb_id}/permissions",
        json={"group_id": group_id, "access_level": "read"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["access_level"] == "read"


@pytest.mark.anyio
async def test_get_access_rules(client: AsyncClient, admin_token: str):
    kb_name = f"perm-test-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    resp = await client.get(
        f"/api/knowledge/{kb_id}/permissions",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert "rules" in resp.json()


@pytest.mark.anyio
async def test_non_admin_cannot_set_access_rules(client: AsyncClient, user_token: str):
    kb_name = f"perm-test-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(user_token),
    )
    if resp.status_code == 201:
        kb_id = resp.json()["id"]
        resp = await client.post(
            f"/api/knowledge/{kb_id}/permissions",
            json={"group_id": None, "access_level": "read"},
            headers=auth_header(user_token),
        )
        assert resp.status_code == 403


@pytest.mark.anyio
async def test_admin_bypasses_access_control(client: AsyncClient, admin_token: str):
    """Admin should be able to access any KB regardless of access rules"""
    kb_name = f"admin-bypass-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Admin can always read
    resp = await client.get(
        f"/api/knowledge/{kb_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_user_allowed_with_access_rule(client: AsyncClient, admin_token: str, user_token: str):
    """User with access rule should be allowed"""
    kb_name = f"allow-test-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Create group and add user
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "allowed_group"},
        headers=auth_header(admin_token),
    )
    group_id = resp.json()["id"]

    resp = await client.get("/api/auth/me", headers=auth_header(user_token))
    user_id = resp.json()["id"]

    await client.post(
        f"/api/auth/groups/{group_id}/members",
        json={"user_id": user_id},
        headers=auth_header(admin_token),
    )

    # Set access rule
    await client.post(
        f"/api/knowledge/{kb_id}/permissions",
        json={"group_id": group_id, "access_level": "read"},
        headers=auth_header(admin_token),
    )

    # User should now be allowed to read
    resp = await client.get(
        f"/api/knowledge/{kb_id}",
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_user_denied_write_without_write_access(client: AsyncClient, admin_token: str, user_token: str):
    """User with only read access should be denied write"""
    kb_name = f"write-deny-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Create group and add user
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "read_only_group"},
        headers=auth_header(admin_token),
    )
    group_id = resp.json()["id"]

    resp = await client.get("/api/auth/me", headers=auth_header(user_token))
    user_id = resp.json()["id"]

    await client.post(
        f"/api/auth/groups/{group_id}/members",
        json={"user_id": user_id},
        headers=auth_header(admin_token),
    )

    # Set read-only access
    await client.post(
        f"/api/knowledge/{kb_id}/permissions",
        json={"group_id": group_id, "access_level": "read"},
        headers=auth_header(admin_token),
    )

    # User should be denied write
    resp = await client.put(
        f"/api/knowledge/{kb_id}",
        json={"name": "Updated Name"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 403


# ============ check_access() Unit Tests ============


@pytest.mark.anyio
async def test_check_access_admin_bypass():
    """Admin should bypass all permission checks"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user

    user = await create_user("perm_admin_check", "perm_admin_check@test.com", "test123")
    # Manually set role to admin
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user["id"],))
        await db.commit()

    result = await check_access(user["id"], "any-kb-id", "manage")
    assert result is True


@pytest.mark.anyio
async def test_check_access_no_user_anonymous_rule():
    """Unauthenticated user should be checked against anonymous rule"""
    from app.knowledge.permissions import check_access

    # No anonymous rule set - should deny
    result = await check_access(None, "test-kb", "read")
    assert result is False


@pytest.mark.anyio
async def test_check_access_authenticated_no_group_denied():
    """Authenticated user with no group access should be denied (no default write)"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user

    user = await create_user("perm_no_group", "perm_no_group@test.com", "test123")
    # Ensure user is NOT admin
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    # Should be denied write (no default write permission)
    result = await check_access(user["id"], "any-kb", "write")
    assert result is False

    # Should be denied read
    result = await check_access(user["id"], "any-kb", "read")
    assert result is False

    # Should be denied manage
    result = await check_access(user["id"], "any-kb", "manage")
    assert result is False


@pytest.mark.anyio
async def test_check_access_group_access_level():
    """User in group should get the group's access level"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user, create_group, add_user_to_group
    from app.knowledge.access_rules import set_access_rule

    user = await create_user("perm_group_level", "perm_group_level@test.com", "test123")
    # Ensure user is NOT admin
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    group = await create_group("read_level_group")
    await add_user_to_group(user["id"], group["id"])
    await set_access_rule("test-kb-123", group["id"], "read")

    # Should be allowed read
    result = await check_access(user["id"], "test-kb-123", "read")
    assert result is True

    # Should be denied write (higher than read)
    result = await check_access(user["id"], "test-kb-123", "write")
    assert result is False


@pytest.mark.anyio
async def test_check_access_highest_group_wins():
    """When user is in multiple groups, highest access level wins"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user, create_group, add_user_to_group
    from app.knowledge.access_rules import set_access_rule

    user = await create_user("perm_highest", "perm_highest@test.com", "test123")
    # Ensure user is NOT admin
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    group_low = await create_group("low_group")
    group_high = await create_group("high_group")
    await add_user_to_group(user["id"], group_low["id"])
    await add_user_to_group(user["id"], group_high["id"])

    await set_access_rule("test-kb-456", group_low["id"], "read")
    await set_access_rule("test-kb-456", group_high["id"], "write")

    # Should be allowed write (highest wins)
    result = await check_access(user["id"], "test-kb-456", "write")
    assert result is True

    # Should be denied manage
    result = await check_access(user["id"], "test-kb-456", "manage")
    assert result is False


@pytest.mark.anyio
async def test_check_access_manage_level_allows_delete():
    """Manage level should allow all operations including delete"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user, create_group, add_user_to_group
    from app.knowledge.access_rules import set_access_rule

    user = await create_user("perm_manage", "perm_manage@test.com", "test123")
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    group = await create_group("manage_group")
    await add_user_to_group(user["id"], group["id"])
    await set_access_rule("test-kb-manage", group["id"], "manage")

    # Manage allows everything
    assert await check_access(user["id"], "test-kb-manage", "manage") is True
    assert await check_access(user["id"], "test-kb-manage", "write") is True
    assert await check_access(user["id"], "test-kb-manage", "read") is True


@pytest.mark.anyio
async def test_check_access_none_level_denies_all():
    """None level should deny all operations"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user, create_group, add_user_to_group
    from app.knowledge.access_rules import set_access_rule

    user = await create_user("perm_none", "perm_none@test.com", "test123")
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    group = await create_group("none_group")
    await add_user_to_group(user["id"], group["id"])
    await set_access_rule("test-kb-none", group["id"], "none")

    # None denies everything
    assert await check_access(user["id"], "test-kb-none", "read") is False
    assert await check_access(user["id"], "test-kb-none", "write") is False
    assert await check_access(user["id"], "test-kb-none", "manage") is False


@pytest.mark.anyio
async def test_check_access_anonymous_with_read_rule():
    """Anonymous user with read rule should be allowed to read"""
    from app.knowledge.permissions import check_access
    from app.knowledge.access_rules import set_access_rule

    await set_access_rule("test-kb-anon", None, "read")

    # Anonymous user can read
    assert await check_access(None, "test-kb-anon", "read") is True
    # But cannot write
    assert await check_access(None, "test-kb-anon", "write") is False


@pytest.mark.anyio
async def test_check_access_anonymous_no_rule_denied():
    """Anonymous user without any rule should be denied"""
    from app.knowledge.permissions import check_access

    assert await check_access(None, "test-kb-no-rule", "read") is False
    assert await check_access(None, "test-kb-no-rule", "write") is False


@pytest.mark.anyio
async def test_new_user_no_default_permissions():
    """Newly registered user without group assignment should have no access"""
    from app.knowledge.permissions import check_access
    from app.auth.service import create_user

    user = await create_user("perm_new_user", "perm_new_user@test.com", "test123")
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
        await db.commit()

    # No access to any KB without explicit group assignment
    assert await check_access(user["id"], "any-kb", "read") is False
    assert await check_access(user["id"], "any-kb", "write") is False
    assert await check_access(user["id"], "any-kb", "manage") is False


# ============ Access Rule Deletion Tests ============


@pytest.mark.anyio
async def test_delete_access_rule(client: AsyncClient, admin_token: str):
    """Admin should be able to delete access rules"""
    kb_name = f"perm-del-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Create group and set rule
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "del_group"},
        headers=auth_header(admin_token),
    )
    group_id = resp.json()["id"]

    resp = await client.post(
        f"/api/knowledge/{kb_id}/permissions",
        json={"group_id": group_id, "access_level": "read"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    rule_id = resp.json()["id"]

    # Verify we have 1 rule (no auto-granted rules)
    resp = await client.get(
        f"/api/knowledge/{kb_id}/permissions",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["rules"]) == 1

    # Delete the rule
    resp = await client.delete(
        f"/api/knowledge/{kb_id}/permissions/{rule_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200

    # Verify no rules remain
    resp = await client.get(
        f"/api/knowledge/{kb_id}/permissions",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["rules"]) == 0


@pytest.mark.anyio
async def test_delete_nonexistent_rule_returns_404(client: AsyncClient, admin_token: str):
    """Deleting a nonexistent rule should return 404"""
    kb_name = f"perm-404-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    resp = await client.delete(
        f"/api/knowledge/{kb_id}/permissions/99999",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


# ============ Group Deletion Tests ============


@pytest.mark.anyio
async def test_delete_group(client: AsyncClient, admin_token: str):
    """Admin should be able to delete groups"""
    resp = await client.post(
        "/api/auth/groups",
        json={"name": "to_delete"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    group_id = resp.json()["id"]

    resp = await client.delete(
        f"/api/auth/groups/{group_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200

    # Verify group is gone
    resp = await client.get(
        "/api/auth/groups",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert not any(g["id"] == group_id for g in resp.json()["groups"])


@pytest.mark.anyio
async def test_delete_nonexistent_group_returns_404(client: AsyncClient, admin_token: str):
    """Deleting a nonexistent group should return 404"""
    resp = await client.delete(
        "/api/auth/groups/99999",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


# ============ No Default Permission Tests ============


@pytest.mark.anyio
async def test_user_without_group_cannot_access_kb(client: AsyncClient, admin_token: str, user_token: str):
    """Authenticated user without group access should be denied by default"""
    kb_name = f"no-access-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # User without group access should be denied
    resp = await client.get(
        f"/api/knowledge/{kb_id}",
        headers=auth_header(user_token),
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_kb_create_no_auto_grant(client: AsyncClient, admin_token: str):
    """KB creation should NOT auto-grant any access rules"""
    kb_name = f"no-grant-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/knowledge",
        json={"name": kb_name, "description": "", "tags": []},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    kb_id = resp.json()["id"]

    # Check that no rules were auto-created
    resp = await client.get(
        f"/api/knowledge/{kb_id}/permissions",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["rules"]) == 0
