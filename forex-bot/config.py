import os
from dotenv import load_dotenv

load_dotenv()


def _int_list(v: str) -> list[int]:
    return [int(x.strip()) for x in v.split(",") if x.strip()] if v else []


BOT_TOKEN: str        = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int]  = _int_list(os.getenv("ADMIN_IDS", ""))
DATABASE_URL: str     = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/forex_bot")

WEB_PANEL_URL: str    = os.getenv("WEB_PANEL_URL", "")

# AI — Anthropic (OpenAI o'rniga)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# Narx ma'lumotlari
TWELVE_DATA_API_KEY: str = os.getenv("TWELVE_DATA_API_KEY", "")
BINANCE_BASE_URL: str    = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")

TIER_DAILY_LIMITS: dict[str, int | None] = {
    "free": 5,
    "pro":  50,
    "vip":  None,
}

REFERRAL_REWARDS: dict[int, int] = {3: 1, 10: 7}

SUPPORTED_PAIRS = ["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")