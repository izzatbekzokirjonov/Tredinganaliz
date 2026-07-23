from typing import Optional
from database import queries

TIERS = ("free", "pro", "vip")


async def grant_premium(pool, telegram_id: int, tier: str, days: Optional[int]) -> None:
    if tier not in TIERS:
        raise ValueError(f"Noma'lum tarif: {tier}")
    await queries.set_subscription(pool, telegram_id, tier, days, granted_by="admin")


async def revoke_premium(pool, telegram_id: int) -> None:
    await queries.set_subscription(pool, telegram_id, "free", None, granted_by="admin")
