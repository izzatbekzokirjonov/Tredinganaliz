import os
from dotenv import load_dotenv
load_dotenv()

def _int_list(v):
    return [int(x.strip()) for x in v.split(",") if x.strip()] if v else []

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = _int_list(os.getenv("ADMIN_IDS", ""))
DATABASE_URL = os.getenv("DATABASE_URL", "")
WEB_PANEL_URL = os.getenv("WEB_PANEL_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")

TIER_DAILY_LIMITS = {"free": 5, "pro": 50, "vip": None}
REFERRAL_REWARDS = {3: 1, 10: 7}

SUPPORTED_PAIRS = [
    "EURUSD","GBPUSD","XAUUSD","BTCUSD",
    "USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
    "EURJPY","GBPJPY","EURGBP","EURAUD","EURCAD",
    "GBPAUD","GBPCAD","AUDCAD","AUDCHF","AUDJPY",
    "ETHUSD","BNBUSD","XRPUSD","SOLUSD","ADAUSD",
    "XAGUSD","USOIL","UKOIL",
]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
