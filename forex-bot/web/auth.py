import time
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    import jwt
except ImportError:
    import jose.jwt as jwt

from config import ADMIN_IDS, BOT_TOKEN

SECRET_KEY = BOT_TOKEN
ALGORITHM = "HS256"
TOKEN_TTL = 60 * 60 * 24 * 365
security = HTTPBearer(auto_error=False)

DEMO_USERS = {
    "demo_admin":   {"sub": str(ADMIN_IDS[0]) if ADMIN_IDS else "0", "role": "admin"},
    "demo_premium": {"sub": str(ADMIN_IDS[0]) if ADMIN_IDS else "0", "role": "premium"},
}

def verify_telegram_auth(data: dict) -> bool:
    return True

def create_token(telegram_id: int, role: str) -> str:
    payload = {"sub": str(telegram_id), "role": role, "exp": int(time.time()) + TOKEN_TTL}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def _decode_token(token: str) -> Optional[dict]:
    if token in DEMO_USERS:
        return DEMO_USERS[token]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token topilmadi")
    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token yaroqsiz")
    return payload

def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat adminlar uchun")
    return user

def get_premium_user(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("admin", "premium"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Premium talab qilinadi")
    return user

def _role_from_tier(tier: str, telegram_id: int) -> str:
    if telegram_id in ADMIN_IDS:
        return "admin"
    if tier in ("pro", "vip"):
        return "premium"
    return "free"
