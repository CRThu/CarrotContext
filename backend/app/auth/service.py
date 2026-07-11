from datetime import UTC, datetime, timedelta

import aiosqlite
import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.database import DATABASE_PATH


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_user_by_username(username: str) -> dict | None:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(username: str, email: str, password: str) -> dict:
    hashed_password = get_password_hash(password)
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        # First user becomes admin
        async with db.execute("SELECT COUNT(*) as cnt FROM users") as cursor:
            row = await cursor.fetchone()
            is_first_user = row[0] == 0

        role = "admin" if is_first_user else "user"
        cursor = await db.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, role),
        )
        await db.commit()
        user_id = cursor.lastrowid
        return await get_user_by_id(user_id)


async def authenticate_user(username: str, password: str) -> dict | None:
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


async def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            return None
        return {"username": username, "user_id": user_id}
    except JWTError:
        return None


async def get_current_user_from_token(token: str) -> dict | None:
    """Unified auth entry point: decode JWT token and return user dict."""
    token_data = await decode_token(token)
    if not token_data:
        return None
    return await get_user_by_id(token_data["user_id"])


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY id") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_user_role(user_id: int, role: str) -> dict | None:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return None
        return await get_user_by_id(user_id)


async def delete_user(user_id: int) -> bool:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount > 0


# --- Group CRUD ---


async def create_group(name: str, description: str = "") -> dict:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "INSERT INTO permission_groups (name, description) VALUES (?, ?)",
            (name, description),
        )
        await db.commit()
        row = await db.execute(
            "SELECT * FROM permission_groups WHERE id = ?", (cursor.lastrowid,)
        )
        return dict(await row.fetchone())


async def get_all_groups() -> list[dict]:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM permission_groups ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_group(group_id: int) -> dict | None:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM permission_groups WHERE id = ?", (group_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def delete_group(group_id: int) -> bool:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "DELETE FROM permission_groups WHERE id = ?", (group_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def add_user_to_group(user_id: int, group_id: int) -> bool:
    try:
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute(
                "INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)",
                (user_id, group_id),
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_user_from_group(user_id: int, group_id: int) -> bool:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        cursor = await db.execute(
            "DELETE FROM user_groups WHERE user_id = ? AND group_id = ?",
            (user_id, group_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_group_members(group_id: int) -> list[dict]:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT u.id as user_id, u.username
            FROM user_groups ug
            JOIN users u ON u.id = ug.user_id
            WHERE ug.group_id = ?
            ORDER BY u.username
            """,
            (group_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_user_groups(user_id: int) -> list[dict]:
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT pg.id, pg.name, pg.description
            FROM user_groups ug
            JOIN permission_groups pg ON pg.id = ug.group_id
            WHERE ug.user_id = ?
            ORDER BY pg.name
            """,
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
