"""Technical analysis engine: OHLCV candles -> indicator values -> normalized scores.

Input: list of candles, oldest first. Each candle:
    {"open": float, "high": float, "low": float, "close": float, "volume": float}
Use 5-minute candles for intraday (needs at least 60 candles for EMA-50 to settle).

Output: TechSnapshot (each field -10..+10) that plugs straight into
signal_engine.make_signal(), plus raw indicator values for display/journal.
"""
from dataclasses import dataclass, field


# ---------------- raw indicators ----------------

def ema(values, period):
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    out = [sum(values[:period]) / period]
    for v in values[period:]:
        out.append(v * k + out[-1] * (1 - k))
    return out

def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)

def macd(closes, fast=12, slow=26, signal=9):
    ef, es = ema(closes, fast), ema(closes, slow)
    if not ef or not es:
        return 0.0, 0.0
    n = min(len(ef), len(es))
    line = [a - b for a, b in zip(ef[-n:], es[-n:])]
    sig = ema(line, signal)
    return line[-1], (sig[-1] if sig else 0.0)

def atr(candles, period=14):
    if len(candles) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["high"], candles[i]["low"], candles[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    a = sum(trs[:period]) / period
    for t in trs[period:]:
        a = (a * (period - 1) + t) / period
    return a

def vwap(candles):
    """Session VWAP - pass only today's candles."""
    pv = vol = 0.0
    for c in candles:
        tp = (c["high"] + c["low"] + c["close"]) / 3
        pv += tp * c["volume"]
        vol += c["volume"]
    return pv / vol if vol else 0.0

def support_resistance(candles, lookback=40):
    """Nearest pivot low below price (support) and pivot high above (resistance)."""
    window = candles[-lookback:]
    price = window[-1]["close"]
    piv_hi = [window[i]["high"] for i in range(2, len(window) - 2)
              if window[i]["high"] >= max(window[j]["high"] for j in range(i - 2, i + 3))]
    piv_lo = [window[i]["low"] for i in range(2, len(window) - 2)
              if window[i]["low"] <= min(window[j]["low"] for j in range(i - 2, i + 3))]
    sup = max([p for p in piv_lo if p < price], default=min(c["low"] for c in window))
    res = min([p for p in piv_hi if p > price], default=max(c["high"] for c in window))
    return sup, res

def candle_pattern(candles):
    """Return (score -10..+10, pattern name) for the last completed candles."""
    if len(candles) < 3:
        return 0.0, "none"
    a, b = candles[-2], candles[-1]
    body = abs(b["close"] - b["open"])
    rng = b["high"] - b["low"] or 1e-9
    up_wick = b["high"] - max(b["close"], b["open"])
    dn_wick = min(b["close"], b["open"]) - b["low"]

    # engulfing
    if (b["close"] > b["open"] and a["close"] < a["open"]
            and b["close"] >= a["open"] and b["open"] <= a["close"] and body / rng > 0.6):
        return 8.0, "bullish_engulfing"
    if (b["close"] < b["open"] and a["close"] > a["open"]
            and b["open"] >= a["close"] and b["close"] <= a["open"] and body / rng > 0.6):
        return -8.0, "bearish_engulfing"
    # hammer / shooting star
    if dn_wick > 2 * body and up_wick < body:
        return 6.0, "hammer"
    if up_wick > 2 * body and dn_wick < body:
        return -6.0, "shooting_star"
    # strong momentum candle
    if body / rng > 0.7:
        return (5.0, "bullish_marubozu") if b["close"] > b["open"] else (-5.0, "bearish_marubozu")
    return 0.0, "none"


# ---------------- snapshot: raw values -> -10..+10 scores ----------------

@dataclass
class TechReport:
    price: float = 0.0
    ema9: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    vwap: float = 0.0
    rsi: float = 50.0
    macd_line: float = 0.0
    macd_signal: float = 0.0
    atr: float = 0.0
    vol_ratio: float = 1.0        # last-candle volume / 20-candle average
    support: float = 0.0
    resistance: float = 0.0
    pattern: str = "none"
    scores: dict = field(default_factory=dict)   # the -10..+10 normalized scores


def analyze_technicals(candles_today, candles_full=None) -> TechReport:
    """candles_today: today's session candles (for VWAP).
    candles_full: longer history including today (for EMA-50/RSI); defaults to candles_today."""
    full = candles_full or candles_today
    closes = [c["close"] for c in full]
    r = TechReport(price=closes[-1])

    e9, e20, e50 = ema(closes, 9), ema(closes, 20), ema(closes, 50)
    r.ema9 = e9[-1] if e9 else r.price
    r.ema20 = e20[-1] if e20 else r.price
    r.ema50 = e50[-1] if e50 else r.price
    r.vwap = vwap(candles_today)
    r.rsi = rsi(closes)
    r.macd_line, r.macd_signal = macd(closes)
    r.atr = atr(full)
    vols = [c["volume"] for c in full[-21:-1]]
    r.vol_ratio = full[-1]["volume"] / (sum(vols) / len(vols)) if vols else 1.0
    r.support, r.resistance = support_resistance(full)
    pat_score, r.pattern = candle_pattern(full)

    # --- normalize to -10..+10 ---
    s = {}
    # EMA trend: alignment + price position
    if r.price > r.ema9 > r.ema20 > r.ema50:
        s["ema_trend"] = 9.0
    elif r.price < r.ema9 < r.ema20 < r.ema50:
        s["ema_trend"] = -9.0
    elif r.price > r.ema20 > r.ema50:
        s["ema_trend"] = 5.0
    elif r.price < r.ema20 < r.ema50:
        s["ema_trend"] = -5.0
    else:
        s["ema_trend"] = 2.0 if r.price > r.ema20 else -2.0

    # VWAP: distance in ATR units, capped
    if r.atr > 0 and r.vwap > 0:
        s["vwap"] = max(-10.0, min(10.0, (r.price - r.vwap) / r.atr * 5))
    else:
        s["vwap"] = 0.0

    # Volume: spike in the direction of the last candle
    direction = 1 if full[-1]["close"] >= full[-1]["open"] else -1
    if r.vol_ratio >= 2.5:
        s["volume"] = 9.0 * direction
    elif r.vol_ratio >= 1.5:
        s["volume"] = 6.0 * direction
    elif r.vol_ratio >= 1.0:
        s["volume"] = 2.0 * direction
    else:
        s["volume"] = 0.0

    # RSI: momentum zone, faded at extremes (chasing overbought is not an edge)
    if 55 <= r.rsi <= 70:
        s["rsi"] = 7.0
    elif 45 <= r.rsi < 55:
        s["rsi"] = 0.0
    elif 30 <= r.rsi < 45:
        s["rsi"] = -7.0
    elif r.rsi > 70:
        s["rsi"] = 2.0     # strong but extended
    else:
        s["rsi"] = -2.0    # weak but oversold

    # MACD adds/cuts a little via rsi slot? keep separate for display
    s["macd"] = 5.0 if r.macd_line > r.macd_signal else -5.0
    s["candle"] = pat_score
    r.scores = s
    return r
