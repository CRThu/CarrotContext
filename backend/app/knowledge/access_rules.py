import aiosqlite
from pydantic import BaseModel

from app.database import DATABASE_PATH


# --- Models ---


class AccessRuleCreate(BaseModel):
    group_id: int | None = None  # None = anonymous
    access_level: str  # 'manage', 'write', 'read', 'none'


class AccessRuleResponse(BaseModel):
    id: int
    knowledge_id: str
    group_id: int | None
    group_name: str | None
    access_level: str

    model_config = {"from_attributes": True}


class AccessRuleListResponse(BaseModel):
    rules: list[AccessRuleResponse]


# --- CRUD ---


async def set_access_rule(
    knowledge_id: str, group_id: int | None, access_level: str
) -> dict:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        if group_id is None:
            # SQLite NULL != NULL in UNIQUE, so handle anonymous rules separately
            await db.execute(
                "DELETE FROM access_rules WHERE knowledge_id = ? AND group_id IS NULL",
                (knowledge_id,),
            )
            await db.execute(
                "INSERT INTO access_rules (knowledge_id, group_id, access_level) VALUES (?, NULL, ?)",
                (knowledge_id, access_level),
            )
        else:
            await db.execute(
                """
                INSERT INTO access_rules (knowledge_id, group_id, access_level)
                VALUES (?, ?, ?)
                ON CONFLICT(knowledge_id, group_id) DO UPDATE SET access_level = ?
                """,
                (knowledge_id, group_id, access_level, access_level),
            )
        await db.commit()
        return {"knowledge_id": knowledge_id, "group_id": group_id, "access_level": access_level}


async def get_access_rules(knowledge_id: str) -> list[dict]:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT ar.id, ar.knowledge_id, ar.group_id, ar.access_level,
                   pg.name as group_name
            FROM access_rules ar
            LEFT JOIN permission_groups pg ON pg.id = ar.group_id
            WHERE ar.knowledge_id = ?
            ORDER BY ar.id
            """,
            (knowledge_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def delete_access_rule(rule_id: int) -> bool:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "DELETE FROM access_rules WHERE id = ?", (rule_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
