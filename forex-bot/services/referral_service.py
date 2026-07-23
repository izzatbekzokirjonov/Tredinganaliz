from typing import Optional
from config import REFERRAL_REWARDS
from database import queries


def build_referral_link(bot_username: str, telegram_id: int) -> str:
    return f"https://t.me/{bot_username}?start=ref_{telegram_id}"


async def register_referral(pool, referrer_id: int, referred_id: int) -> Optional[str]:
    if referrer_id == referred_id:
        return None
    new_count = await queries.add_referral(pool, referrer_id, referred_id)
    if new_count is None:
        return None
    reward_days = REFERRAL_REWARDS.get(new_count)
    if reward_days:
        await queries.set_subscription(
            pool, referrer_id, "pro", reward_days, granted_by="referral", extend=True
        )
        return (
            f"🎉 Tabriklaymiz! {new_count} ta do'stingizni taklif qildingiz — "
            f"{reward_days} kunlik Pro tarif yutib oldingiz!"
        )
    return None
