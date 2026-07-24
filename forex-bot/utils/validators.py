from config import SUPPORTED_PAIRS


def normalize_pair(text: str) -> str:
    return text.strip().upper().replace("/", "").replace(" ", "")


def is_supported_pair(text: str) -> bool:
    return normalize_pair(text) in SUPPORTED_PAIRS


def parse_positive_float(text: str) -> float | None:
    try:
        v = float(text.strip().replace(",", "."))
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None


def parse_telegram_id(text: str) -> int | None:
    t = text.strip()
    return int(t) if t.isdigit() else None
