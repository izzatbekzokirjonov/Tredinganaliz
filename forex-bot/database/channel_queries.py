"""
Kanallar va foydalanuvchi a'zolik holati bilan bog'liq barcha SQL so'rovlari.
"""
from typing import Optional

import asyncpg


# ═══════════════════════════════════════════
#  KANALLAR BOSHQARUVI
# ═══════════════════════════════════════════

async def add_channel(
    pool: asyncpg.Pool,
    channel_id: int,
    username: Optional[str],
    title: str,
    type_: str,          # 'mandatory' | 'signal' | 'lesson' | 'info'
    is_mandatory: bool,
    added_by: int,
) -> asyncpg.Record:
    return await pool.fetchrow(
        """
        INSERT INTO channels (channel_id, username, title, type, is_mandatory, added_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (channel_id) DO UPDATE
        SET username     = EXCLUDED.username,
            title        = EXCLUDED.title,
            type         = EXCLUDED.type,
            is_mandatory = EXCLUDED.is_mandatory,
            is_active    = TRUE
        RETURNING *
        """,
        channel_id, username, title, type_, is_mandatory, added_by,
    )


async def remove_channel(pool: asyncpg.Pool, channel_id: int) -> bool:
    result = await pool.execute(
        "UPDATE channels SET is_active = FALSE WHERE channel_id = $1", channel_id
    )
    return result != "UPDATE 0"


async def get_all_channels(pool: asyncpg.Pool, only_active: bool = True) -> list[asyncpg.Record]:
    if only_active:
        return await pool.fetch(
            "SELECT * FROM channels WHERE is_active = TRUE ORDER BY added_at"
        )
    return await pool.fetch("SELECT * FROM channels ORDER BY added_at")


async def get_mandatory_channels(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
        SELECT * FROM channels
        WHERE is_active = TRUE AND is_mandatory = TRUE
        ORDER BY added_at
        """
    )


async def get_channel_by_id(pool: asyncpg.Pool, channel_id: int) -> Optional[asyncpg.Record]:
    return await pool.fetchrow(
        "SELECT * FROM channels WHERE channel_id = $1", channel_id
    )


async def update_channel_type(
    pool: asyncpg.Pool, channel_id: int, type_: str, is_mandatory: bool
) -> bool:
    result = await pool.execute(
        """
        UPDATE channels SET type = $1, is_mandatory = $2
        WHERE channel_id = $3 AND is_active = TRUE
        """,
        type_, is_mandatory, channel_id,
    )
    return result != "UPDATE 0"


# ═══════════════════════════════════════════
#  FOYDALANUVCHI A'ZOLIK HOLATI
# ═══════════════════════════════════════════

async def upsert_user_channel_status(
    pool: asyncpg.Pool,
    telegram_id: int,
    channel_id: int,
    is_member: bool,
) -> None:
    await pool.execute(
        """
        INSERT INTO user_channel_status (telegram_id, channel_id, is_member, checked_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (telegram_id, channel_id) DO UPDATE
        SET is_member  = EXCLUDED.is_member,
            checked_at = NOW()
        """,
        telegram_id, channel_id, is_member,
    )


async def get_user_channel_statuses(
    pool: asyncpg.Pool, telegram_id: int
) -> list[asyncpg.Record]:
    """
    Foydalanuvchining barcha faol kanallardagi holati.
    Tekshirilmagan kanallar ham qaytariladi (is_member=NULL ko'rinishida NULL sifatida).
    """
    return await pool.fetch(
        """
        SELECT
            c.channel_id,
            c.title,
            c.username,
            c.type,
            c.is_mandatory,
            ucs.is_member,
            ucs.checked_at
        FROM channels c
        LEFT JOIN user_channel_status ucs
            ON ucs.channel_id = c.channel_id AND ucs.telegram_id = $1
        WHERE c.is_active = TRUE
        ORDER BY c.is_mandatory DESC, c.added_at
        """,
        telegram_id,
    )


async def get_channel_members_count(pool: asyncpg.Pool, channel_id: int) -> dict:
    """Bitta kanal bo'yicha a'zolar statistikasi."""
    row = await pool.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE is_member = TRUE)  AS members,
            COUNT(*) FILTER (WHERE is_member = FALSE) AS non_members,
            COUNT(*)                                   AS checked
        FROM user_channel_status
        WHERE channel_id = $1
        """,
        channel_id,
    )
    return dict(row) if row else {"members": 0, "non_members": 0, "checked": 0}


async def get_non_members(pool: asyncpg.Pool, channel_id: int) -> list[int]:
    """Kanalga a'zo bo'lmagan foydalanuvchilarning telegram_id lari."""
    rows = await pool.fetch(
        """
        SELECT telegram_id FROM user_channel_status
        WHERE channel_id = $1 AND is_member = FALSE
        """,
        channel_id,
    )
    return [r["telegram_id"] for r in rows]
