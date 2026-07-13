"""One-off CLI helper: create a promo code.

Usage:
    python create_promocode.py SUMMER30 premium 30 100

    args: <code> <plan: premium|pro> <duration_days> <max_uses>
"""

import asyncio
import sys

from db.database import async_session, init_db
from db.models import PromoCode


async def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return

    code, plan, duration_days, max_uses = sys.argv[1:5]

    await init_db()
    async with async_session() as session:
        promo = PromoCode(
            code=code.upper(),
            plan=plan,
            duration_days=int(duration_days),
            max_uses=int(max_uses),
        )
        session.add(promo)
        await session.commit()

    print(f"Promo kod yaratildi: {code.upper()} -> {plan}, {duration_days} kun, {max_uses} marta ishlatilishi mumkin")


if __name__ == "__main__":
    asyncio.run(main())
