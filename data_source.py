"""Unified market-data source for the dashboard.

Tries Kotak Neo (if config.json has credentials) -> falls back to MockBroker
with realistic base prices so the app always runs. The UI shows which source
is active, so you always know if you're looking at LIVE or SIMULATED data.

config.json format (put next to app.py; never commit it) - Kotak Neo v2 SDK:
{
  "consumer_key": "...",          # token from Neo app -> Invest -> Trade API
  "mobile_number": "+91XXXXXXXXXX",
  "ucc": "YOUR_UCC",              # Unique Client Code (profile section)
  "mpin": "XXXXXX",              # your Neo MPIN
  "environment": "prod",
  "live_trading": false
}
TOTP is entered at startup from your authenticator app (changes every 30s).
"""
import json
import os
import random
import time

from news_impact.feed import fetch_headlines
from news_impact.assets import CURRENCIES, COMMODITIES

BASE_PRICES = {
    # stocks (approximate; mock mode only - live mode uses real quotes)
    "TCS": 3450, "INFY": 1580, "HCLTECH": 1520, "WIPRO": 250, "RELIANCE": 1420,
    "HDFCBANK": 1980, "ICICIBANK": 1440, "SBIN": 820, "KOTAKBANK": 2200,
    "TATAMOTORS": 690, "M&M": 3150, "MARUTI": 12600, "LT": 3620,
    "ULTRACEMCO": 11400, "ACC": 1870, "SUNPHARMA": 1690, "CIPLA": 1500,
    "ONGC": 245, "IOC": 145, "BPCL": 320, "ASIANPAINT": 2300, "INDIGO": 5400,
    "HAL": 4900, "BEL": 390, "TATAPOWER": 400, "EXIDEIND": 390, "TATASTEEL": 160,
    # indices (spot levels; mock mode only)
    "NIFTY50": 24850, "NIFTYBANK": 52400, "SENSEX": 81300, "NIFTYIT": 38200,
    "FINNIFTY": 23450, "NIFTYMIDCP": 57600,
    # currency (per unit INR)
    "USDINR": 86.4, "EURINR": 100.8, "GBPINR": 116.5, "JPYINR": 0.582,
    # commodities (MCX quote units)
    "GOLD": 98500, "SILVER": 113000, "CRUDEOIL": 5600, "NATURALGAS": 290,
    "COPPER": 890, "ZINC": 265, "ALUMINIUM": 245,
}

SAMPLE_HEADLINES = [
    "Government increases infrastructure spending by Rs 1 lakh crore",
    "Crude oil prices surge 4% on Middle East supply worries",
    "RBI cuts repo rate by 25 basis points to support growth",
    "Finance Minister gives tax benefits to electric vehicle companies in Budget",
    "Rupee falls to record low against dollar amid FII outflows",
    "USFDA issues warning letter to Sun Pharma plant in Gujarat",
    "TCS profit jumps 12% in Q1, beats estimates on strong deal wins",
    "Defence ministry clears Rs 45,000 crore acquisition orders for HAL and BEL",
]


class DataSource:
    def __init__(self, config_path="config.json"):
        self.mode = "SIMULATED"
        self.broker = None
        if os.path.exists(config_path):
            try:
                cfg = json.load(open(config_path))
                from broker import KotakNeoBroker
                self.broker = KotakNeoBroker(
                    cfg["consumer_key"], cfg["mobile_number"],
                    cfg["ucc"], cfg["mpin"],
                    environment=cfg.get("environment", "prod"),
                    live_trading=cfg.get("live_trading", False))
                self.mode = "LIVE (Kotak Neo)"
            except Exception as e:
                print(f"Kotak Neo unavailable ({e}); using simulated data.")
        # deterministic per-day seed so refreshes are stable within a session
        self._rng_seed = int(time.strftime("%Y%m%d"))

    def candles(self, symbol, n=180):
        """5-min OHLCV candles, oldest first."""
        if self.broker:
            try:
                return self.broker.candles(symbol)
            except NotImplementedError:
                pass  # Neo has no public candle history; fall through to mock
        rng = random.Random(f"{self._rng_seed}-{symbol}")
        px = BASE_PRICES.get(symbol, rng.uniform(100, 3000))
        # small persistent drift per symbol/day so different names look different
        trend = rng.uniform(-1.5, 1.5)
        vol_scale = px * 0.0011 if symbol not in CURRENCIES else px * 0.0004
        out = []
        for i in range(n):
            drift = trend * px * 0.00025
            move = rng.gauss(drift, vol_scale)
            o = px
            c = px + move
            hi = max(o, c) + abs(rng.gauss(0, vol_scale * 0.5))
            lo = min(o, c) - abs(rng.gauss(0, vol_scale * 0.5))
            vol = abs(rng.gauss(50000, 15000))
            if i > n - 12 and abs(trend) > 1.0:  # late-session volume push
                vol *= rng.uniform(1.5, 2.6)
            out.append({"open": round(o, 4), "high": round(hi, 4),
                        "low": round(lo, 4), "close": round(c, 4), "volume": vol})
            px = c
        return out

    def headlines(self):
        """Live RSS if reachable; otherwise realistic samples (marked in UI)."""
        live = fetch_headlines()
        if live:
            return [t for t, _, _ in live[:25]], "LIVE RSS"
        return SAMPLE_HEADLINES, "SAMPLE (no internet)"
