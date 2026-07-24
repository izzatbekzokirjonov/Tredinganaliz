"""
Vision Service: foydalanuvchi yuborgan chart screenshotini
Claude claude-opus-4-6 Vision orqali tahlil qiladi.
"""
import base64
import httpx
import anthropic

from config import ANTHROPIC_API_KEY
from utils.logger import logger

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

VISION_SYSTEM_PROMPT = """
Sen professional forex va kripto texnik tahlilchisan.
Foydalanuvchi sanga chart (grafik) rasmini yuboradi.

Quyidagi tartibda o'zbek tilida tahlil yoz:

📈 TREND: (Ko'tarilish / Tushish / Yon tomon)
📍 Joriy zona: (Qo'llab-quvvatlash / Qarshilik / Neytral)
🎯 Asosiy darajalar: (Ko'rinib turgan S/R darajalarini sanab o't)
💡 Pattern: (Pinbar, Engulfing, Doji va h.k. — ko'rinsa)
⚡ Qisqa tavsiya: (Qaysi tomonga pozitsiya, TP/SL haqida umumiy fikr)
⚠️ Risk: (Bir qisqa ogohlantirish)

Raqamlar to'qima — faqat grafikda ko'ringan narsalarni izohlang.
Javob 250-350 so'zdan oshmasin.
"""


class VisionAnalysisError(Exception):
    pass


async def _download_photo(bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def analyze_chart_image(bot, file_id: str) -> str:
    if _client is None:
        raise VisionAnalysisError("Anthropic API kaliti sozlanmagan.")

    try:
        image_bytes = await _download_photo(bot, file_id)
    except Exception as e:
        logger.error(f"Rasm yuklab olinmadi: {e}")
        raise VisionAnalysisError("Rasmni yuklab bo'lmadi. Qayta urinib ko'ring.")

    if len(image_bytes) > 20 * 1024 * 1024:
        raise VisionAnalysisError("Rasm hajmi juda katta (max 20MB).")

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        response = _client.messages.create(
            model="claude-opus-4-6",
            max_tokens=700,
            system=VISION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Ushbu forex/kripto chartini tahlil qiling.",
                        },
                    ],
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude Vision xatosi: {e}")
        raise VisionAnalysisError("Tahlil qilishda xato yuz berdi.")