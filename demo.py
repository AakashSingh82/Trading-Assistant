"""Demo: run headlines through the News Impact Engine and the final signal engine."""
from news_impact import analyze, format_report
from signal_engine import TechSnapshot, make_signal

HEADLINES = [
    # your two examples
    "US President declares war against Iran, oil facilities under threat",
    "Finance Minister gives tax benefits to electric vehicle companies in the Budget bill",
    # the examples from the design doc
    "Government increases infrastructure spending by Rs 1 lakh crore",
    "USFDA issues warning letter to Sun Pharma plant in Gujarat",
    # more scenarios
    "RBI cuts repo rate by 50 basis points to support growth",
    "TCS profit jumps 12% in Q1, beats estimates on strong deal wins",
    "SEBI probe into Adani group entities over disclosure lapses",
    "Rupee falls to record low against dollar",
    "Reliance wins major contract for new energy business",
]

print("=" * 78)
print("NEWS IMPACT ENGINE - demo run")
print("=" * 78)
for h in HEADLINES:
    r = analyze(h)
    print()
    print(format_report(r))

# --- end-to-end: news score + (mock) technicals -> final tradeable signal ---
print()
print("=" * 78)
print("FINAL SIGNAL (news + technicals combined, Rs 5,000 account)")
print("=" * 78)
r = analyze("Government increases infrastructure spending by Rs 1 lakh crore")
news_lt = r.stock_scores.get("LT", 0.0)
sector = r.sector_scores.get("INFRA", 0.0)
tech = TechSnapshot(ema_trend=7, vwap=6, volume=8, rsi=6, candle=5)  # from live-data layer
sig = make_signal("LT", news_lt, sector, tech, price=3620.0, atr=28.0,
                  reason="Infra capex news + price above VWAP with volume")
print(f"\n{sig.symbol}: {sig.action}  (confidence {sig.confidence}%, composite {sig.composite:+.2f})")
if sig.action != "WAIT":
    print(f"  Entry {sig.entry} | SL {sig.stop} | T1 {sig.target1} | T2 {sig.target2} | Qty {sig.qty}")
print(f"  Why: {sig.reason}")
