"""Lightweight keyword sentiment for financial headlines (-1.0 .. +1.0).

This is the fast, free layer. If you later add an LLM (e.g. Claude API),
call it only for headlines this layer marks as high-impact, and blend both.
"""
import re

POSITIVE = {
    "surge": 2, "soar": 2, "jump": 2, "rally": 2, "record": 2, "beats": 2,
    "profit": 1, "growth": 1, "wins": 2, "bags": 2, "approval": 2, "upgrade": 2,
    "boost": 2, "benefit": 2, "incentive": 2, "subsidy": 2, "gain": 1, "rise": 1,
    "strong": 1, "expansion": 1, "breakthrough": 2, "relief": 1, "cut" : 0,
}
NEGATIVE = {
    "crash": -3, "plunge": -3, "slump": -2, "fall": -1, "drop": -1, "decline": -1,
    "loss": -2, "fraud": -3, "probe": -2, "raid": -2, "penalty": -2, "warning": -2,
    "war": -3, "attack": -3, "strike": -2, "recession": -3, "downgrade": -2,
    "miss": -2, "weak": -1, "resign": -1, "ban": -2, "curb": -1, "default": -3,
}

_WORD = re.compile(r"[a-z']+")

def score_sentiment(text: str) -> float:
    words = _WORD.findall(text.lower())
    if not words:
        return 0.0
    total = sum(POSITIVE.get(w, 0) + NEGATIVE.get(w, 0) for w in words)
    # squash to -1..+1; 6 points ~= saturation
    return max(-1.0, min(1.0, total / 6.0))
