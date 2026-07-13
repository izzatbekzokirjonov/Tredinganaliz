"""Fetches OHLC candle data from the Twelve Data API."""

import aiohttp
import pandas as pd

from config import TWELVE_DATA_API_KEY, DEFAULT_INTERVAL, CANDLES_LOOKBACK

BASE_URL = "https://api.twelvedata.com/time_series"


class MarketDataError(Exception):
    pass


async def fetch_candles(symbol: str, interval: str = DEFAULT_INTERVAL,
                         outputsize: int = CANDLES_LOOKBACK) -> pd.DataFrame:
    """
    Fetch historical candles for a symbol like 'EUR/USD'.
    Returns a DataFrame sorted oldest -> newest with columns:
    datetime, open, high, low, close, volume (volume may be NaN for FX).
    """
    if not TWELVE_DATA_API_KEY:
        raise MarketDataError(
            "TWELVE_DATA_API_KEY sozlanmagan. .env faylga kalitni qo'shing."
        )

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": TWELVE_DATA_API_KEY,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()

    if data.get("status") == "error":
        raise MarketDataError(data.get("message", "Noma'lum API xatoligi"))

    values = data.get("values")
    if not values:
        raise MarketDataError(f"{symbol} uchun ma'lumot topilmadi")

    df = pd.DataFrame(values)
    df = df.rename(columns={"datetime": "datetime"})
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    return df
