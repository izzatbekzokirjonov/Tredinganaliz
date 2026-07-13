"""Technical indicator calculations: RSI, MACD, EMA."""

import pandas as pd


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze(df: pd.DataFrame) -> dict:
    """
    Compute the full indicator set on a candle DataFrame and return
    the latest snapshot plus derived directional votes.
    """
    close = df["close"]

    rsi = compute_rsi(close)
    ema_20 = compute_ema(close, 20)
    ema_50 = compute_ema(close, 50)
    macd_line, signal_line, hist = compute_macd(close)

    latest = {
        "price": round(close.iloc[-1], 5),
        "rsi": round(rsi.iloc[-1], 2) if pd.notna(rsi.iloc[-1]) else None,
        "ema_20": round(ema_20.iloc[-1], 5),
        "ema_50": round(ema_50.iloc[-1], 5),
        "macd": round(macd_line.iloc[-1], 5),
        "macd_signal": round(signal_line.iloc[-1], 5),
        "macd_hist": round(hist.iloc[-1], 5),
    }

    votes = []  # each vote: +1 bullish, -1 bearish, 0 neutral

    # RSI vote
    if latest["rsi"] is not None:
        if latest["rsi"] < 30:
            votes.append(1)   # oversold -> bullish bias
        elif latest["rsi"] > 70:
            votes.append(-1)  # overbought -> bearish bias
        else:
            votes.append(0)

    # EMA trend vote
    if latest["ema_20"] > latest["ema_50"]:
        votes.append(1)
    elif latest["ema_20"] < latest["ema_50"]:
        votes.append(-1)
    else:
        votes.append(0)

    # MACD momentum vote
    if latest["macd"] > latest["macd_signal"]:
        votes.append(1)
    elif latest["macd"] < latest["macd_signal"]:
        votes.append(-1)
    else:
        votes.append(0)

    score = sum(votes)
    if score >= 2:
        direction = "BUY"
    elif score <= -2:
        direction = "SELL"
    else:
        direction = "HOLD"

    confidence = round(abs(score) / len(votes) * 100) if votes else 0

    return {
        "latest": latest,
        "direction": direction,
        "confidence": confidence,
        "votes": votes,
    }
