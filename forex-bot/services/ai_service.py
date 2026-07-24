from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from utils.logger import logger

_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = (
    "Sen professional forex/kripto tahlilchisan. Foydalanuvchiga faqat senga "
    "berilgan raqamlar asosida, o'zbek tilida, 3-4 jumlali qisqa va tushunarli "
    "izoh yoz. Yangi narx yoki raqam to'qima. Oxirida risk haqida ogohlantirish qo'sh."
)


async def generate_analysis_comment(
    pair: str, trend: str, entry: float, tp: float, sl: float, current_price: float
) -> str:
    if _client is None:
        return _fallback(pair, trend)

    trend_uz = {"UP": "ko'tarilish", "DOWN": "tushish", "FLAT": "yon tomon"}.get(trend, trend)
    prompt = (
        f"Instrument: {pair}\nJoriy narx: {current_price}\n"
        f"Trend: {trend_uz}\nEntry: {entry}\nTP: {tp}\nSL: {sl}"
    )
    try:
        r = await _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=220,
            temperature=0.6,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI xatosi: {e}")
        return _fallback(pair, trend)


def _fallback(pair: str, trend: str) -> str:
    t = {"UP": "ko'tarilish", "DOWN": "tushish", "FLAT": "yon tomon"}.get(trend, trend)
    return (
        f"{pair} bo'yicha hozirgi holat {t} tendensiyasini ko'rsatmoqda. "
        f"Berilgan Entry/TP/SL darajalariga e'tibor bering. "
        f"⚠️ Bu signal kafolat emas — risk menejmentga rioya qiling."
    )
