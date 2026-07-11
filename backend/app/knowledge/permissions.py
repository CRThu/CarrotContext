import aiosqlite

from app.database import DATABASE_PATH

# Role hierarchy: admin > editor > viewer
ROLE_HIERARCHY = {"admin": 3, "editor": 2, "viewer": 1}


def has_required_role(user_role: str, required_role: str) -> bool:
    """Check if user_role >= required_role in hierarchy"""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


async def get_user_role(user_id: int | None) -> str:
    """Get user's system role. Returns 'viewer' for anonymous (None user_id)"""
    if user_id is None:
        # Check anonymous default from system_settings
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT value FROM system_settings WHERE key = ?",
                ("anonymous_default_role",),
            ) as cursor:
                row = await cursor.fetchone()
                return row["value"] if row else "viewer"

    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT role FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row["role"] if row else "viewer"


async def check_permission(user_id: int | None, knowledge_id: str, required_role: str) -> bool:
    """Check if user has required permission for a knowledge base"""
    # Get user's system role
    system_role = await get_user_role(user_id)

    # Admin users bypass all permission checks
    if system_role == "admin":
        return True

    # Check KB-specific permissions
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row

        if user_id is not None:
            # Check user-specific permission
            async with db.execute(
                "SELECT role FROM kb_permissions WHERE knowledge_id = ? AND user_id = ?",
                (knowledge_id, user_id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return has_required_role(row["role"], required_role)

        # Check anonymous permission (user_id = NULL)
        async with db.execute(
            "SELECT role FROM kb_permissions WHERE knowledge_id = ? AND user_id IS NULL",
            (knowledge_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return has_required_role(row["role"], required_role)

    # Default: viewer access for all authenticated users
    return has_required_role("viewer", required_role)


async def set_kb_permission(knowledge_id: str, user_id: int | None, role: str) -> None:
    """Set or update a permission for a knowledge base"""
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute(
            """
            INSERT INTO kb_permissions (knowledge_id, user_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT(knowledge_id, user_id) DO UPDATE SET role = ?
            """,
            (knowledge_id, user_id, role, role),
        )
        await db.commit()


async def get_kb_permissions(knowledge_id: str) -> list[dict]:
    """Get all permissions for a knowledge base"""
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT p.*, u.username
            FROM kb_permissions p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.knowledge_id = ?
            """,
            (knowledge_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_kb_permission(perm_id: int) -> bool:
    """Delete a permission entry"""
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute("DELETE FROM kb_permissions WHERE id = ?", (perm_id,))
        await db.commit()
        return cursor.rowcount > 0
