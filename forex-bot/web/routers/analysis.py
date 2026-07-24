"""
Tahlil API:
  POST /api/analysis/screenshot  — rasm yuklash va GPT-4o tahlil
  GET  /api/analysis/price/{pair} — joriy narx va OHLC
  GET  /api/analysis/chart/{pair} — grafik uchun shamlar (vaqt+narx)
"""
import base64
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from config import BINANCE_BASE_URL, TWELVE_DATA_API_KEY
from web.auth import get_premium_user
from web.dependencies import get_pool

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

PAIR_MAP = {
    "EURUSD": ("twelvedata","EUR/USD"),
    "GBPUSD": ("twelvedata","GBP/USD"),
    "XAUUSD": ("twelvedata","XAU/USD"),
    "GBPJPY": ("twelvedata","GBP/JPY"),
    "EURJPY": ("twelvedata","EUR/JPY"),
    "USDJPY": ("twelvedata","USD/JPY"),
    "AUDUSD": ("twelvedata","AUD/USD"),
    "USDCHF": ("twelvedata","USD/CHF"),
    "USDCAD": ("twelvedata","USD/CAD"),
    "NZDUSD": ("twelvedata","NZD/USD"),
    "BTCUSD": ("binance","BTCUSDT"),
    "ETHUSD": ("binance","ETHUSDT"),
    "BNBUSD": ("binance","BNBUSDT"),
    "XRPUSD": ("binance","XRPUSDT"),
    "SOLUSD": ("binance","SOLUSDT"),
    "ADAUSD": ("binance","ADAUSDT"),
    "DOTUSD": ("binance","DOTUSDT"),
    "AVAXUSD":("binance","AVAXUSDT"),
    "LTCUSD": ("binance","LTCUSDT"),
    "LINKUSD":("binance","LINKUSDT"),
}


async def _twelvedata_candles(symbol: str, interval: str, outputsize: int = 50):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get("https://api.twelvedata.com/time_series", params={
            "symbol": symbol, "interval": interval,
            "outputsize": outputsize, "apikey": TWELVE_DATA_API_KEY,
        })
        data = r.json()
    if "values" not in data:
        raise HTTPException(502, data.get("message","Twelve Data xatosi"))
    return list(reversed(data["values"]))


async def _binance_candles(symbol: str, interval: str, limit: int = 50):
    tf_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h","4h":"4h","1D":"1d","1W":"1w"}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{BINANCE_BASE_URL}/api/v3/klines",
                        params={"symbol":symbol,"interval":tf_map.get(interval,"1h"),"limit":limit})
        data = r.json()
    if not isinstance(data, list):
        raise HTTPException(502, "Binance xatosi")
    return [{"open":k[1],"high":k[2],"low":k[3],"close":k[4],"volume":k[5]} for k in data]


@router.get("/price/{pair}")
async def get_price(
    pair:     str,
    interval: str = Query("1h"),
    _:        dict = Depends(get_premium_user),
):
    pair = pair.upper()
    if pair not in PAIR_MAP:
        raise HTTPException(404, f"'{pair}' qo'llab-quvvatlanmaydi")

    source, symbol = PAIR_MAP[pair]
    try:
        if source == "twelvedata":
            candles = await _twelvedata_candles(symbol, interval, 50)
            latest  = candles[-1]
            prev    = candles[-2] if len(candles) > 1 else candles[-1]
            close   = float(latest["close"])
            prev_c  = float(prev["close"])
            change_pct = round((close - prev_c) / prev_c * 100, 3)
            return {
                "pair":    pair,
                "price":   close,
                "open":    float(latest["open"]),
                "high":    float(latest["high"]),
                "low":     float(latest["low"]),
                "volume":  float(latest.get("volume", 0)),
                "change_pct": change_pct,
                "up":      change_pct >= 0,
            }
        else:
            candles = await _binance_candles(symbol, interval)
            latest  = candles[-1]
            prev    = candles[-2] if len(candles) > 1 else candles[-1]
            close   = float(latest["close"])
            prev_c  = float(prev["close"])
            change_pct = round((close - prev_c) / prev_c * 100, 3)
            return {
                "pair":    pair,
                "price":   close,
                "open":    float(latest["open"]),
                "high":    float(latest["high"]),
                "low":     float(latest["low"]),
                "volume":  float(latest["volume"]),
                "change_pct": change_pct,
                "up":      change_pct >= 0,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))


@router.get("/chart/{pair}")
async def get_chart_data(
    pair:     str,
    interval: str = Query("1h"),
    limit:    int = Query(50, ge=10, le=200),
    _:        dict = Depends(get_premium_user),
):
    pair = pair.upper()
    if pair not in PAIR_MAP:
        raise HTTPException(404, f"'{pair}' qo'llab-quvvatlanmaydi")

    source, symbol = PAIR_MAP[pair]
    try:
        if source == "twelvedata":
            candles = await _twelvedata_candles(symbol, interval, limit)
            return {"pair": pair, "candles": [
                {"o": float(c["open"]), "h": float(c["high"]),
                 "l": float(c["low"]),  "c": float(c["close"]),
                 "t": c["datetime"]}
                for c in candles
            ]}
        else:
            candles = await _binance_candles(symbol, interval, limit)
            return {"pair": pair, "candles": [
                {"o": float(c["open"]), "h": float(c["high"]),
                 "l": float(c["low"]),  "c": float(c["close"]),
                 "t": ""}
                for c in candles
            ]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))


@router.post("/screenshot")
async def analyze_screenshot(
    request: Request,
    file: UploadFile = File(...),
    _:    dict = Depends(get_premium_user),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Faqat rasm fayli yuklang")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(400, "Rasm hajmi 20MB dan oshmasligi kerak")

    b64 = base64.b64encode(content).decode()

    from services.vision_service import VisionAnalysisError
    from openai import AsyncOpenAI
    from config import OPENAI_API_KEY
    from services.vision_service import VISION_SYSTEM_PROMPT

    if not OPENAI_API_KEY:
        raise HTTPException(503, "OpenAI API kaliti sozlanmagan")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=700,
            temperature=0.4,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:{file.content_type};base64,{b64}",
                        "detail": "high",
                    }},
                    {"type": "text", "text": "Ushbu forex/kripto chartini tahlil qiling."},
                ]},
            ],
        )
        return {"ok": True, "analysis": response.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(502, f"AI tahlil xatosi: {e}")
