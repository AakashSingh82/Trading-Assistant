"""Broker layer: Kotak Neo API adapter + a mock broker for testing without login.

Real adapter uses Kotak's official SDK:
    pip install neo-api-client
    (docs: https://github.com/Kotak-Neo/kotak-neo-api)

You need from Kotak Neo:
  - consumer_key / consumer_secret  (from Neo developer portal, napi.kotaksecurities.com)
  - your mobile number + login password/MPIN
  - OTP at login time (interactive, once per session)

SAFETY: KotakNeoBroker.place_order() refuses to send real orders unless you
construct it with live_trading=True. Default is signal-only / paper mode.
"""
import random
from dataclasses import dataclass


@dataclass
class Order:
    symbol: str
    side: str          # BUY / SELL
    qty: int
    price: float       # 0 = market
    stop_loss: float = 0.0
    tag: str = ""


class KotakNeoBroker:
    """Thin wrapper around neo-api-client. All methods raise a clear error
    if the SDK is missing so the rest of the system keeps working."""

    def __init__(self, consumer_key, mobile_number, ucc, mpin,
                 environment="prod", live_trading=False, totp=None):
        """Kotak Neo v2 SDK login (consumer_key + TOTP + MPIN; no consumer secret).

        Install the v2 SDK:
          pip install --force-reinstall \
            "git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git@v2.0.2#egg=neo_api_client"
        """
        self.live_trading = live_trading
        try:
            from neo_api_client import NeoAPI
        except ImportError as e:
            raise RuntimeError(
                "Install the Kotak Neo v2 SDK: pip install --force-reinstall "
                "'git+https://github.com/Kotak-Neo/Kotak-neo-api-v2.git"
                "@v2.0.2#egg=neo_api_client'") from e
        self.client = NeoAPI(environment=environment, access_token=None,
                             neo_fin_key=None, consumer_key=consumer_key)
        # TOTP comes from your authenticator app; ask for it if not supplied.
        if not totp:
            totp = input("Enter Kotak Neo TOTP (from authenticator app): ").strip()
        # Step 1: generates view token + session id
        self.client.totp_login(mobile_number=mobile_number, ucc=ucc, totp=totp)
        # Step 2: MPIN validation -> trade token
        self.client.totp_validate(mpin=mpin)

    def quote(self, symbol):
        return self.client.quotes(
            instrument_tokens=[{"instrument_token": symbol, "exchange_segment": "nse_cm"}],
            quote_type="ltp")

    def candles(self, symbol, interval="5", days=5):
        """Kotak Neo does not ship a rich historical-candles endpoint in the public SDK.
        Standard approach: subscribe to live ticks (client.subscribe) and build your
        own 5-min candles, or pull history from NSE/yfinance for the warm-up window."""
        raise NotImplementedError("Build candles from live ticks; see docstring.")

    def place_order(self, order: Order):
        if not self.live_trading:
            print(f"[PAPER] {order.side} {order.qty} {order.symbol} "
                  f"@ {'MKT' if not order.price else order.price} SL {order.stop_loss}")
            return {"paper": True, "order": order}
        return self.client.place_order(
            exchange_segment="nse_cm", product="MIS", price=str(order.price or 0),
            order_type="MKT" if not order.price else "L",
            quantity=str(order.qty), validity="DAY",
            trading_symbol=order.symbol + "-EQ",
            transaction_type="B" if order.side == "BUY" else "S",
            amo="NO", disclosed_quantity="0", market_protection="0",
            pf="N", trigger_price="0", tag=order.tag or "ai-assistant")

    def positions(self):
        return self.client.positions()


class MockBroker:
    """Generates realistic random-walk candles so the full pipeline can be
    developed and tested without credentials or internet."""

    REALISTIC_BASE = {
        "USDINR": 87.4, "EURINR": 101.2, "GBPINR": 117.8, "JPYINR": 0.585,
        "GOLD": 98500.0, "SILVER": 113000.0, "CRUDEOIL": 6350.0,
        "NATURALGAS": 245.0, "COPPER": 872.0, "ZINC": 268.0,
    }

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.base = dict(self.REALISTIC_BASE)

    def candles(self, symbol, n=120, trend=0.0, spike_at=None):
        px = self.base.setdefault(symbol, self.rng.uniform(200, 3000))
        out = []
        for i in range(n):
            drift = trend * px * 0.0004
            move = self.rng.gauss(drift, px * 0.0012)
            o = px
            c = px + move
            hi = max(o, c) + abs(self.rng.gauss(0, px * 0.0006))
            lo = min(o, c) - abs(self.rng.gauss(0, px * 0.0006))
            vol = abs(self.rng.gauss(50000, 15000))
            if spike_at is not None and i >= spike_at:
                vol *= 2.8
                c = o + abs(move) * (1 if trend >= 0 else -1)  # push with the news
            out.append({"open": o, "high": hi, "low": lo, "close": c, "volume": vol})
            px = c
        self.base[symbol] = px
        return out

    def place_order(self, order: Order):
        print(f"[MOCK] {order.side} {order.qty} {order.symbol} SL {order.stop_loss}")
        return {"mock": True}
