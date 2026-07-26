try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False

import base64
import httpx
from config import ANTHROPIC_API_KEY
from utils.logger import logger

VISION_SYSTEM_PROMPT = "Sen forex tahlilchisan. Chart rasmini o'zbek tilida tahlil qil."

class VisionAnalysisError(Exception):
    pass

async def _download_photo(bot, file_id):
    file = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content

async def analyze_chart_image(bot, file_id):
    if not _anthropic_available or not ANTHROPIC_API_KEY:
        raise VisionAnalysisError("AI xizmati mavjud emas.")
    try:
        image_bytes = await _download_photo(bot, file_id)
        image_b64 = base64.standard_b64encode(image_bytes).decode()
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=700,
            system=VISION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": "Chartni tahlil qiling."},
            ]}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Vision xatosi: {e}")
        raise VisionAnalysisError("Tahlil qilishda xato.")
