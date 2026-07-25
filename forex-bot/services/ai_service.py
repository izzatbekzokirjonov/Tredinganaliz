import anthropic
from config import ANTHROPIC_API_KEY
from utils.logger import logger

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = (
    "Sen professional forex/kripto tahlilchisan. Foydalanuvchiga faqat senga "
    "berilgan raqamlar asosida, o'zbek tilida, 3-4 jumlali qisqa va tushunarli "
    "izoh yoz. Yangi narx yoki raqam to'qima. Oxirida risk haqida ogohlantirish qo'sh."
)

async def generate_analysis_comment(pair, trend, entry, tp, sl, current_price):
    if _client is None:
        return _fallback(pair, trend)
    trend_uz = {"UP": "kotarilish", "DOWN": "tushish", "FLAT": "yon tomon"}.get(trend, trend)
    prompt = f"Instrument: {pair}\nJoriy narx: {current_price}\nTrend: {trend_uz}\nEntry: {entry}\nTP: {tp}\nSL: {sl}"
    try:
        response = _client.messages.create(
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
    return f"{pair} boyicha hozirgi holat {t} tendensiyasini korsatmoqda. Berilgan Entry/TP/SL darajalariga etibor bering. Risk menejmentga rioya qiling."
