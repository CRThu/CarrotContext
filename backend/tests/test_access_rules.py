"""Tests for knowledge/access_rules.py module"""
import pytest
import aiosqlite

from app.database import DATABASE_PATH
from app.knowledge.access_rules import (
    AccessRuleCreate,
    AccessRuleListResponse,
    AccessRuleResponse,
    delete_access_rule,
    get_access_rules,
    set_access_rule,
)


@pytest.fixture(autouse=True)
async def setup_db():
    from app.database import init_db

    await init_db()
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM access_rules")
        await db.execute("DELETE FROM permission_groups")
        await db.commit()
    yield
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM access_rules")
        await db.execute("DELETE FROM permission_groups")
        await db.commit()


# ========== set_access_rule Tests ==========


@pytest.mark.anyio
async def test_set_access_rule_create():
    result = await set_access_rule("kb1", None, "read")
    assert result["knowledge_id"] == "kb1"
    assert result["group_id"] is None
    assert result["access_level"] == "read"


@pytest.mark.anyio
async def test_set_access_rule_update():
    await set_access_rule("kb2", None, "read")
    result = await set_access_rule("kb2", None, "write")
    assert result["access_level"] == "write"

    rules = await get_access_rules("kb2")
    assert len(rules) == 1
    assert rules[0]["access_level"] == "write"


@pytest.mark.anyio
async def test_set_access_rule_with_group():
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "INSERT INTO permission_groups (name) VALUES (?)", ("test_group",)
        )
        await db.commit()
        group_id = cursor.lastrowid

    result = await set_access_rule("kb3", group_id, "manage")
    assert result["group_id"] == group_id
    assert result["access_level"] == "manage"


# ========== get_access_rules Tests ==========


@pytest.mark.anyio
async def test_get_access_rules_empty():
    rules = await get_access_rules("nonexistent-kb")
    assert rules == []


@pytest.mark.anyio
async def test_get_access_rules_with_data():
    await set_access_rule("kb4", None, "read")
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "INSERT INTO permission_groups (name) VALUES (?)", ("grp",)
        )
        await db.commit()
        group_id = cursor.lastrowid
    await set_access_rule("kb4", group_id, "write")

    rules = await get_access_rules("kb4")
    assert len(rules) == 2
    # Check group_name is resolved
    group_rules = [r for r in rules if r["group_id"] == group_id]
    assert len(group_rules) == 1
    assert group_rules[0]["group_name"] == "grp"


# ========== delete_access_rule Tests ==========


@pytest.mark.anyio
async def test_delete_access_rule_success():
    await set_access_rule("kb5", None, "read")
    rules = await get_access_rules("kb5")
    rule_id = rules[0]["id"]

    result = await delete_access_rule(rule_id)
    assert result is True

    rules = await get_access_rules("kb5")
    assert len(rules) == 0


@pytest.mark.anyio
async def test_delete_access_rule_nonexistent():
    result = await delete_access_rule(99999)
    assert result is False


# ========== Model Tests ==========


def test_access_rule_create_model():
    rule = AccessRuleCreate(group_id=1, access_level="read")
    assert rule.group_id == 1
    assert rule.access_level == "read"


def test_access_rule_create_anonymous():
    rule = AccessRuleCreate(group_id=None, access_level="write")
    assert rule.group_id is None


def test_access_rule_response_model():
    resp = AccessRuleResponse(
        id=1,
        knowledge_id="kb1",
        group_id=None,
        group_name=None,
        access_level="read",
    )
    assert resp.id == 1
    assert resp.group_name is None


def test_access_rule_list_response_model():
    resp = AccessRuleListResponse(rules=[])
    assert len(resp.rules) == 0
