"""Final signal = news + sector + technicals, using the weight table from the design.

Technical inputs (EMA/VWAP/RSI/volume/candles) come from your live-data layer;
here each is a normalized score in -10..+10. Position sizing assumes signal-only
manual execution for a Rs 5,000 account (risk 1-2% per trade).
"""
from dataclasses import dataclass

WEIGHTS = {
    "news":       0.30,
    "sector":     0.20,
    "ema_trend":  0.15,
    "vwap":       0.10,
    "volume":     0.10,
    "rsi":        0.10,
    "candle":     0.05,
}

@dataclass
class TechSnapshot:
    ema_trend: float = 0.0   # +10 strong uptrend (9>20>50), -10 strong downtrend
    vwap: float = 0.0        # +10 well above VWAP with support, -10 below
    volume: float = 0.0      # +10 big spike in direction of move
    rsi: float = 0.0         # +10 momentum up (55-70), -10 momentum down; ~0 if overbought/oversold
    candle: float = 0.0      # +10 bullish pattern, -10 bearish

@dataclass
class Signal:
    symbol: str
    action: str        # BUY / SELL / WAIT
    confidence: int    # 0-100
    composite: float   # -10..+10
    entry: float = 0.0
    stop: float = 0.0
    target1: float = 0.0
    target2: float = 0.0
    qty: int = 0
    reason: str = ""

def make_signal(symbol, news_score, sector_score, tech: TechSnapshot,
                price=0.0, atr=0.0, capital=5000.0, risk_pct=0.02, reason=""):
    # Weighted AVERAGE over only the signals that are actually present.
    # Technicals are always active; news/sector count only when non-zero, so a
    # stock with no news is judged purely on its chart (weights renormalized)
    # instead of being dragged to zero by empty news/sector slots.
    parts = [
        (WEIGHTS["ema_trend"], tech.ema_trend),
        (WEIGHTS["vwap"],      tech.vwap),
        (WEIGHTS["volume"],    tech.volume),
        (WEIGHTS["rsi"],       tech.rsi),
        (WEIGHTS["candle"],    tech.candle),
    ]
    if news_score:
        parts.append((WEIGHTS["news"], news_score))
    if sector_score:
        parts.append((WEIGHTS["sector"], sector_score))
    active_w = sum(w for w, _ in parts) or 1.0
    composite = sum(w * v for w, v in parts) / active_w   # -10..+10

    # bonus when news and the trend agree; penalty when they fight
    if news_score:
        agree = news_score * (tech.ema_trend + tech.vwap) >= 0
        bump = 8 if agree else -15
    else:
        agree, bump = True, 0
    # Calibrated so a clean directional chart is actionable:
    #   |composite| 2.5 -> ~55,  5 -> ~70,  8+ -> ~90+.  Composite is the gate.
    confidence = max(0, min(97, int(42 + abs(composite) * 5.5 + bump)))

    if composite >= 2.5:
        action = "BUY"
    elif composite <= -2.5:
        action = "SELL"
    else:
        action = "WAIT"
        confidence = min(confidence, 45)   # never show high conviction on a no-trade

    sig = Signal(symbol=symbol, action=action, confidence=confidence,
                 composite=round(composite, 2), reason=reason)

    if action != "WAIT" and price > 0 and atr > 0:
        d = 1 if action == "BUY" else -1
        sig.entry = round(price, 2)
        sig.stop = round(price - d * 1.0 * atr, 2)
        sig.target1 = round(price + d * 1.5 * atr, 2)
        sig.target2 = round(price + d * 2.5 * atr, 2)
        risk_per_share = abs(sig.entry - sig.stop)
        if risk_per_share > 0:
            sig.qty = max(0, int((capital * risk_pct) / risk_per_share))
    return sig
