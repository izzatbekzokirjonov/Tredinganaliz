"""Generates a natural-language explanation of a technical signal using Claude."""

from anthropic import AsyncAnthropic

from config import ANTHROPIC_API_KEY

_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


async def explain_signal(symbol: str, analysis: dict, lang: str = "uz") -> str:
    """
    Ask Claude to turn the raw indicator numbers into a short, readable
    explanation for the end user. Falls back to a template if no API key
    is configured.
    """
    latest = analysis["latest"]
    direction = analysis["direction"]
    confidence = analysis["confidence"]

    if _client is None:
        return (
            f"{symbol}: {direction} signali ({confidence}% ishonch). "
            f"RSI={latest['rsi']}, EMA20={latest['ema_20']}, EMA50={latest['ema_50']}, "
            f"MACD={latest['macd']} vs Signal={latest['macd_signal']}."
        )

    prompt = f"""Sen forex bozori bo'yicha AI tahlilchisan. Quyidagi texnik ko'rsatkichlar
asosida {symbol} juftligi uchun {direction} signalini oddiy, tushunarli tilda
({lang} tilida), 3-4 gapda tushuntir. Raqamlarni tabiiy ravishda jumla ichida
ishlat, lekin moliyaviy kafolat berma va risklarni eslatib o't.

Ko'rsatkichlar:
- Narx: {latest['price']}
- RSI(14): {latest['rsi']}
- EMA20: {latest['ema_20']}, EMA50: {latest['ema_50']}
- MACD: {latest['macd']}, Signal chizig'i: {latest['macd_signal']}, Histogram: {latest['macd_hist']}
- Signal: {direction}, Ishonch darajasi: {confidence}%
"""

    response = await _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=350,
        messages=[{"role": "user", "content": prompt}],
    )

    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts).strip()
