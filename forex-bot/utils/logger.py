import logging
import sys

from config import LOG_LEVEL


def _build_logger() -> logging.Logger:
    log = logging.getLogger("forex_bot")
    log.setLevel(LOG_LEVEL)
    if not log.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        fh = logging.FileHandler("bot.log", encoding="utf-8")
        fh.setFormatter(fmt)
        log.addHandler(ch)
        log.addHandler(fh)
    return log


logger = _build_logger()
