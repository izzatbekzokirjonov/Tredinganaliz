import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Postgres connection string, e.g. postgresql+asyncpg://user:pass@localhost:5432/nexforexai
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://nexforex:nexforex@db:5432/nexforexai")
# Replit's managed Postgres exposes DATABASE_URL as a plain "postgresql://" string;
# SQLAlchemy's async engine needs the "+asyncpg" driver marker to use it.
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.split("://", 1)[1]
    DATABASE_URL = "postgresql+asyncpg://" + DATABASE_URL
# asyncpg's connect() has no "sslmode" kwarg (libpq/psycopg naming) — it uses "ssl" instead.
# Rewrite the query param so SQLAlchemy's asyncpg dialect passes a kwarg asyncpg understands.
if "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sslmode=", "ssl=")

# Telegram Payments provider token (from BotFather -> Payments, e.g. Payme/Click/Stripe)
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# Telegram user IDs allowed to use /admin commands (comma-separated)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Subscription plans: name -> (daily signal limit, price in smallest currency unit, label)
PLAN_LIMITS = {
    "free": 3,
    "premium": 30,
    "pro": 10_000,  # effectively unlimited
}

PLAN_PRICES_USD = {
    "premium": 9.99,
    "pro": 29.99,
}

# Currency pairs supported in the MVP menu
SUPPORTED_PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "XAU/USD",
    "USD/CHF",
    "AUD/USD",
]

# Timeframe used for indicator calculation (Twelve Data interval format)
DEFAULT_INTERVAL = "1h"
CANDLES_LOOKBACK = 100

RISK_DISCLAIMER = (
    "⚠️ Bu signal faqat ta'lim/axborot maqsadida yaratilgan AI tahlili bo'lib, "
    "moliyaviy maslahat hisoblanmaydi. Savdo qarorlarini faqat o'z tavakkalingiz "
    "asosida qabul qiling."
)
