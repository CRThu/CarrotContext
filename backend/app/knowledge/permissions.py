from fastapi import Depends, HTTPException, Request, status
from loguru import logger

from app.auth.router import get_current_user
from app.auth.service import get_user_by_id
from app.database import DATABASE_PATH

import aiosqlite

ACCESS_LEVELS = {"manage": 3, "write": 2, "read": 1, "none": 0}


async def check_access(user_id: int | None, knowledge_id: str, required: str) -> bool:
    """Check if user has required access level for a knowledge base."""
    # Admin bypass
    if user_id is not None:
        user = await get_user_by_id(user_id)
        if user and user.get("role") == "admin":
            return True

    required_level = ACCESS_LEVELS.get(required, 0)
    if required_level == 0:
        return True

    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row

        if user_id is not None:
            max_level = 0
            has_group_rule = False
            async with db.execute(
                """
                SELECT ar.access_level
                FROM access_rules ar
                JOIN user_groups ug ON ug.group_id = ar.group_id
                WHERE ar.knowledge_id = ? AND ug.user_id = ?
                """,
                (knowledge_id, user_id),
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    has_group_rule = True
                    level = ACCESS_LEVELS.get(row["access_level"], 0)
                    if level > max_level:
                        max_level = level

            if has_group_rule:
                granted = max_level >= required_level
                if granted:
                    logger.debug("Access GRANTED: user={}, kb={}, level={}", user_id, knowledge_id, required)
                else:
                    logger.warning("Access DENIED: user={}, kb={}, required={}", user_id, knowledge_id, required)
                return granted

            logger.warning("Access DENIED: user={}, kb={}, required={} (no group rules)", user_id, knowledge_id, required)
            return False

        async with db.execute(
            """
            SELECT access_level FROM access_rules
            WHERE knowledge_id = ? AND group_id IS NULL
            """,
            (knowledge_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                level = ACCESS_LEVELS.get(row["access_level"], 0)
                if level >= required_level:
                    return True

    return False


def require_access(required: str):
    """FastAPI Depends factory. Extracts knowledge_id from path params."""

    async def _check(
        request: Request,
        current_user: dict | None = Depends(get_current_user),
    ):
        knowledge_id = request.path_params.get("knowledge_id")
        if not knowledge_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少知识库ID",
            )
        user_id = current_user["id"] if current_user else None
        has_access = await check_access(user_id, knowledge_id, required)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required} 权限",
            )
        return current_user

    return _check


def require_access_body(required: str):
    """FastAPI Depends factory for endpoints where knowledge_id is in the request body."""

    async def _check(
        request: Request,
        current_user: dict | None = Depends(get_current_user),
    ):
        import json as _json

        body = await request.body()
        try:
            data = _json.loads(body)
            knowledge_id = data.get("knowledge_id")
        except (ValueError, UnicodeDecodeError):
            knowledge_id = None

        if not knowledge_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少知识库ID",
            )
        user_id = current_user["id"] if current_user else None
        has_access = await check_access(user_id, knowledge_id, required)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required} 权限",
            )
        return current_user

    return _check
