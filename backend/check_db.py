import aiosqlite
import asyncio

async def check():
    async with aiosqlite.connect('./data/carrotcontext.db') as db:
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
            print("Tables:", tables)
        
        async with db.execute("SELECT * FROM users") as cursor:
            users = await cursor.fetchall()
            print("Users:", users)

asyncio.run(check())
