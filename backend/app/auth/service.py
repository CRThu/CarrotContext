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
