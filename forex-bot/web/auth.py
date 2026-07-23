"""
JWT autentifikatsiya va Telegram Login Widget tekshiruvi.

Telegram Login Widget:
  - Bot token orqali HMAC-SHA256 bilan hash tekshiriladi
  - Tasdiqlangan foydalanuvchiga JWT token beriladi

JWT:
  - HS256 algoritm
  - 24 soat amal qiladi
  - payload: {sub: telegram_id, role: "admin"|"premium"|"free", exp: ...}
"""
import hashlib
import hmac
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    import jwt
except ImportError:
    import jose.jwt as jwt  # type: ignore

from config import ADMIN_IDS, BOT_TOKEN

SECRET_KEY = BOT_TOKEN  # JWT imzolash uchun
ALGORITHM  = "HS256"
TOKEN_TTL  = 60 * 60 * 24  # 24 soat

security = HTTPBearer(auto_error=False)


# ─── TELEGRAM WIDGET TEKSHIRUVI ──────────────────────────────────

def verify_telegram_auth(data: dict) -> bool:
    """
    Telegram Login Widget dan kelgan ma'lumotlarni tekshiradi.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    # auth_date juda eski bo'lmasin (1 soat)
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 3600:
        return False

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_hash, check_hash)


# ─── JWT YARATISH ─────────────────────────────────────────────────

def create_token(telegram_id: int, role: str) -> str:
    payload = {
        "sub":  str(telegram_id),
        "role": role,
        "exp":  int(time.time()) + TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ─── JWT TEKSHIRUVI ───────────────────────────────────────────────

def _decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


def _role_from_tier(tier: str, telegram_id: int) -> str:
    if telegram_id in ADMIN_IDS:
        return "admin"
    if tier in ("pro", "vip"):
        return "premium"
    return "free"


# ─── FASTAPI DEPENDENCIES ─────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Har qanday autentifikatsiyalangan foydalanuvchi."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token topilmadi",
        )
    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
        )
    return payload


def get_admin_user(
    user: dict = Depends(get_current_user),
) -> dict:
    """Faqat admin."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat adminlar uchun",
        )
    return user


def get_premium_user(
    user: dict = Depends(get_current_user),
) -> dict:
    """Admin yoki premium foydalanuvchi."""
    if user.get("role") not in ("admin", "premium"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium tarif talab qilinadi",
        )
    return user
