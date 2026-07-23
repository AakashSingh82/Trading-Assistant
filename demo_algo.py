"""End-to-end algo demo with the mock broker (no credentials needed).

Scenario: infra-spending news breaks. Infra/cement stocks get an uptrend +
volume spike in their (simulated) candles; OMCs drift down on a second
headline about crude. Watch the system find the right trades.
"""
from broker import MockBroker
from scanner import WATCHLIST, scan, print_signals

HEADLINES = [
    "Government increases infrastructure spending by Rs 1 lakh crore",
    "Crude oil prices surge 4% on supply worries",
]

class ScenarioBroker(MockBroker):
    """Mock broker where price action agrees with the news for some names."""
    UP = {"LT", "ULTRACEMCO", "ACC", "TATASTEEL", "ONGC"}
    DOWN = {"IOC", "BPCL", "ASIANPAINT", "INDIGO"}

    def candles(self, symbol, n=120):
        if symbol in self.UP:
            return super().candles(symbol, n, trend=+2.0, spike_at=100)
        if symbol in self.DOWN:
            return super().candles(symbol, n, trend=-2.0, spike_at=100)
        return super().candles(symbol, n, trend=0.0)

broker = ScenarioBroker(seed=7)
print("Headlines in play:")
for h in HEADLINES:
    print("  -", h)
print()
signals = scan(broker, WATCHLIST, HEADLINES)
print_signals(signals)

best = signals[0]
if best.action != "WAIT":
    tr = best.tech_report
    print(f"\nTop signal detail - {best.symbol}:")
    print(f"  price {tr.price:.1f} | VWAP {tr.vwap:.1f} | EMA9/20/50 "
          f"{tr.ema9:.1f}/{tr.ema20:.1f}/{tr.ema50:.1f}")
    print(f"  RSI {tr.rsi:.0f} | vol x{tr.vol_ratio:.1f} | ATR {tr.atr:.1f} | "
          f"pattern {tr.pattern} | S/R {tr.support:.1f}/{tr.resistance:.1f}")
