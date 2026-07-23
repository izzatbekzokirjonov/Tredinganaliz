"""
PostgreSQL ulanish puli (asyncpg).
"""
import asyncpg

from database.models import ALL_TABLES
from utils.logger import logger


async def create_pool(database_url: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)
    logger.info("PostgreSQL ulanish puli yaratildi.")
    return pool


async def init_db(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        for ddl in ALL_TABLES:
            await conn.execute(ddl)
    logger.info("Jadvallar tayyor.")


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
    logger.info("PostgreSQL ulanish puli yopildi.")
