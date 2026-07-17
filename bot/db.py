import aiosqlite

from bot.config import DB_PATH, FREE_ATTEMPTS


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                attempts_left INTEGER NOT NULL DEFAULT 0,
                is_blocked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.commit()


async def get_user(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        return await cursor.fetchone()


async def create_user(chat_id: int, phone_number: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO users (chat_id, phone_number, attempts_left) VALUES (?, ?, ?)",
            (chat_id, phone_number, FREE_ATTEMPTS),
        )
        await conn.commit()


async def decrement_attempt(chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET attempts_left = attempts_left - 1 WHERE chat_id = ? AND attempts_left > 0",
            (chat_id,),
        )
        await conn.commit()


async def add_credit(chat_id: int, count: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET attempts_left = attempts_left + ? WHERE chat_id = ?",
            (count, chat_id),
        )
        await conn.commit()


async def set_blocked(chat_id: int, blocked: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET is_blocked = ? WHERE chat_id = ?",
            (1 if blocked else 0, chat_id),
        )
        await conn.commit()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT COUNT(*), COALESCE(SUM(is_blocked), 0) FROM users")
        total, blocked = await cursor.fetchone()
        return total or 0, blocked or 0


async def list_users(offset: int, limit: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return await cursor.fetchall()
