try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False

from config import ANTHROPIC_API_KEY
from utils.logger import logger

SYSTEM_PROMPT = (
    "Sen professional forex/kripto tahlilchisan. O'zbek tilida "
    "3-4 jumlali qisqa izoh yoz. Risk haqida ogohlantirish qo'sh."
)

async def generate_analysis_comment(pair, trend, entry, tp, sl, current_price):
    if not _anthropic_available or not ANTHROPIC_API_KEY:
        return _fallback(pair, trend)
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        trend_uz = {"UP": "kotarilish", "DOWN": "tushish", "FLAT": "yon tomon"}.get(trend, trend)
        prompt = f"Instrument: {pair}\nNarx: {current_price}\nTrend: {trend_uz}\nEntry: {entry}\nTP: {tp}\nSL: {sl}"
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=220,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Anthropic xatosi: {e}")
        return _fallback(pair, trend)

def _fallback(pair, trend):
    t = {"UP": "kotarilish", "DOWN": "tushish", "FLAT": "yon tomon"}.get(trend, trend)
    return f"{pair} boyicha {t} tendensiyasi. Entry/TP/SL darajalariga rioya qiling. Risk menejment muhim!"
