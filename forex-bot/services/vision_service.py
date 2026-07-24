"""
Vision Service: foydalanuvchi yuborgan chart screenshotini
GPT-4o Vision orqali tahlil qiladi.
"""
import base64

import httpx
from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from utils.logger import logger

_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

VISION_SYSTEM_PROMPT = """
Sen professional forex va kripto texnik tahlilchisan.
Foydalanuvchi sanga chart (grafik) rasmini yuboradi.

Vazifang:
1. Grafikda qaysi instrument (juftlik) ko'rinishini aniqlashga harakat qil.
2. Timeframeni (1m, 5m, 1h, 4h, 1D va h.k.) aniqlashga harakat qil.
3. Quyidagi tartibda o'zbek tilida tahlil yoz:

📈 TREND: (Ko'tarilish / Tushish / Yon tomon)
📍 Joriy zona: (Qo'llab-quvvatlash / Qarshilik / Neytral)
🎯 Asosiy darajalar: (Ko'rinib turgan S/R darajalarini sanab o't)
💡 Pattern: (Pinbar, Engulfing, Doji va h.k. — ko'rinsa)
⚡ Qisqa tavsiya: (Qaysi tomonga pozitsiya, TP/SL haqida umumiy fikr)
⚠️ Risk: (Bir qisqa ogohlantirish)

Agar rasm chart emas yoki noaniq bo'lsa, buni ochiq ayt.
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
        raise VisionAnalysisError("OpenAI API kaliti sozlanmagan.")

    try:
        image_bytes = await _download_photo(bot, file_id)
    except Exception as e:
        logger.error(f"Rasm yuklab olinmadi: {e}")
        raise VisionAnalysisError("Rasmni yuklab bo'lmadi. Qayta urinib ko'ring.")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Fayl hajmini tekshiramiz (20MB limit)
    if len(image_bytes) > 20 * 1024 * 1024:
        raise VisionAnalysisError("Rasm hajmi juda katta (max 20MB).")

    try:
        response = await _client.chat.completions.create(
            model="gpt-4o",
            max_tokens=700,
            temperature=0.4,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": "Ushbu forex/kripto chartini tahlil qiling.",
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Vision API xatosi: {e}")
        raise VisionAnalysisError(f"Tahlil qilishda xato yuz berdi.")
