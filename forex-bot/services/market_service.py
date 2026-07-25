from dataclasses import dataclass
import httpx
from config import BINANCE_BASE_URL, TWELVE_DATA_API_KEY
from utils.logger import logger

TWELVE_DATA_URL = "https://api.twelvedata.com/time_series"

PAIR_SOURCE_MAP = {
    "EURUSD": ("twelvedata", "EUR/USD"),
    "GBPUSD": ("twelvedata", "GBP/USD"),
    "XAUUSD": ("twelvedata", "XAU/USD"),
    "BTCUSD": ("binance",    "BTCUSDT"),
}


@dataclass
class AnalysisResult:
    pair: str
    current_price: float
    trend: str
    entry: float
    tp: float
    sl: float
    atr: float


class MarketDataError(Exception):
    pass


async def _twelvedata_closes(symbol: str, outputsize: int = 50) -> list[float]:
    if not TWELVE_DATA_API_KEY:
        raise MarketDataError("TWELVE_DATA_API_KEY sozlanmagan.")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(TWELVE_DATA_URL, params={
            "symbol": symbol, "interval": "1h",
            "outputsize": outputsize, "apikey": TWELVE_DATA_API_KEY,
        })
        data = r.json()
    if "values" not in data:
        raise MarketDataError(data.get("message", "Twelve Data xatosi."))
    return [float(v["close"]) for v in reversed(data["values"])]


async def _binance_closes(symbol: str, limit: int = 50) -> list[float]:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{BINANCE_BASE_URL}/api/v3/klines",
                        params={"symbol": symbol, "interval": "1h", "limit": limit})
        data = r.json()
    if not isinstance(data, list):
        raise MarketDataError("Binance xatosi.")
    return [float(k[4]) for k in data]


def _sma(v: list[float], p: int) -> float:
    w = v[-p:]; return sum(w) / len(w)


def _atr(closes: list[float], p: int = 14) -> float:
    diffs = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]
    w = diffs[-p:] if len(diffs) >= p else diffs
    return sum(w) / len(w) if w else 0.0


def _compute(closes: list[float]) -> AnalysisResult:
    price = closes[-1]
    fast  = _sma(closes, min(10, len(closes)))
    slow  = _sma(closes, min(30, len(closes)))
    atr   = _atr(closes) or price * 0.001

    if fast > slow:
        trend, tp, sl = "UP",   price + atr*3, price - atr*1.5
    elif fast < slow:
        trend, tp, sl = "DOWN", price - atr*3, price + atr*1.5
    else:
        trend, tp, sl = "FLAT", price + atr*2, price - atr*2

    return AnalysisResult(
        pair="", current_price=round(price,5), trend=trend,
        entry=round(price,5), tp=round(tp,5), sl=round(sl,5), atr=round(atr,5),
    )


async def analyze_pair(pair: str, interval: str = "1h") -> AnalysisResult:
    pair = pair.upper().replace("/", "")
    if pair not in PAIR_SOURCE_MAP:
        raise MarketDataError(f"'{pair}' qo'llab-quvvatlanmaydi.")
    source, symbol = PAIR_SOURCE_MAP[pair]
    closes = await (_twelvedata_closes(symbol) if source == "twelvedata" else _binance_closes(symbol))
    if len(closes) < 5:
        raise MarketDataError("Yetarli ma'lumot yo'q.")
    result = _compute(closes)
    result.pair = pair
    return result
