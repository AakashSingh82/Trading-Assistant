"""AI Intraday Trading Assistant - dashboard server (stdlib only, no pip installs).

Run:  python3 app.py     then open  http://localhost:8420

Sections served as JSON:
  /api/instruments  - stock/currency/commodity lists for the picker
  /api/technical    - Section 1: full TA of one user-selected instrument + trade plan
  /api/news         - Section 2: news -> recommended stocks/currencies/commodities
  /api/combined     - Section 3: news + technicals merged, ranked signals
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from data_source import DataSource
from news_impact import analyze
from news_impact.mappings import STOCK_SECTOR
from news_impact.assets import CURRENCIES, COMMODITIES, ASSET_LABEL
from scanner import WATCHLIST, merge_news
from signal_engine import TechSnapshot, make_signal
from technicals import analyze_technicals
from universe import STOCK_UNIVERSE
from data_source import BASE_PRICES

PORT = 8420
ds = DataSource()


def tech_snapshot(tr):
    return TechSnapshot(
        ema_trend=tr.scores["ema_trend"], vwap=tr.scores["vwap"],
        volume=tr.scores["volume"],
        rsi=(tr.scores["rsi"] + tr.scores["macd"]) / 2,
        candle=tr.scores["candle"])


def trade_plan(symbol, tr, news_score=0.0, sector_score=0.0, reason=""):
    sig = make_signal(symbol, news_score, sector_score, tech_snapshot(tr),
                      price=tr.price, atr=tr.atr, reason=reason)
    return {"action": sig.action, "confidence": sig.confidence,
            "composite": sig.composite, "entry": sig.entry, "stop": sig.stop,
            "target1": sig.target1, "target2": sig.target2, "qty": sig.qty,
            "reason": sig.reason}


INDEX_LIST = [
    ("NIFTY 50", "NIFTY50"), ("NIFTY BANK", "NIFTYBANK"), ("SENSEX", "SENSEX"),
    ("NIFTY IT", "NIFTYIT"), ("NIFTY FIN", "FINNIFTY"), ("NIFTY MIDCAP", "NIFTYMIDCP"),
]
_INDEX_SYMS = {sym for _, sym in INDEX_LIST}
# liquid names for the gainers/losers board (all have realistic mock base prices)
GL_POOL = [s for s in BASE_PRICES
           if s not in CURRENCIES and s not in COMMODITIES and s not in _INDEX_SYMS]


def _quote(sym):
    """Last price, absolute change and % change vs the session open (from candles)."""
    c = ds.candles(sym)
    price = c[-1]["close"]
    ref = c[-75] if len(c) >= 75 else c[0]          # intraday-session open
    op = ref["open"] or price
    return round(price, 2), round(price - op, 2), round((price - op) / op * 100, 2)


def section_market():
    indices = []
    for label, sym in INDEX_LIST:
        p, ch, pct = _quote(sym)
        indices.append({"label": label, "symbol": sym, "price": p, "change": ch, "pct": pct})
    quotes = []
    for sym in GL_POOL:
        p, ch, pct = _quote(sym)
        quotes.append({"symbol": sym, "label": STOCK_UNIVERSE.get(sym, sym),
                       "price": p, "change": ch, "pct": pct})
    quotes.sort(key=lambda x: -x["pct"])
    gainers = quotes[:6]
    losers = quotes[-6:][::-1]
    currencies = []
    for sym in CURRENCIES:
        p, ch, pct = _quote(sym)
        currencies.append({"symbol": sym, "label": ASSET_LABEL.get(sym, sym),
                           "price": p, "change": ch, "pct": pct})
    headlines, source = ds.headlines()
    return {"mode": ds.mode, "source": source, "indices": indices,
            "gainers": gainers, "losers": losers, "currencies": currencies,
            "news": headlines[:12]}


def section_technical(symbol):
    symbol = (symbol or "").strip().upper()
    candles = ds.candles(symbol)
    tr = analyze_technicals(candles[-75:], candles)
    pivot = (tr.price + tr.support + tr.resistance) / 3  # classic pivot approximation
    from data_source import BASE_PRICES
    placeholder = ds.mode == "SIMULATED" and symbol not in BASE_PRICES
    return {
        "symbol": symbol, "label": ASSET_LABEL.get(symbol, symbol),
        "mode": ds.mode, "placeholder": placeholder, "price": round(tr.price, 2),
        "indicators": {
            "ema9": round(tr.ema9, 2), "ema20": round(tr.ema20, 2),
            "ema50": round(tr.ema50, 2), "vwap": round(tr.vwap, 2),
            "rsi": round(tr.rsi, 1), "macd": round(tr.macd_line, 3),
            "macd_signal": round(tr.macd_signal, 3), "atr": round(tr.atr, 2),
            "volume_ratio": round(tr.vol_ratio, 2), "support": round(tr.support, 2),
            "resistance": round(tr.resistance, 2), "pivot": round(pivot, 2),
            "pattern": tr.pattern,
        },
        "scores": {k: round(v, 1) for k, v in tr.scores.items()},
        # technical-only plan (news weight redistributed onto technicals)
        "plan": trade_plan(symbol, tr, news_score=0.0, sector_score=0.0,
                           reason="technical setup"),
        "candles": [{"c": round(c["close"], 4), "v": round(c["volume"])}
                    for c in candles[-75:]],
    }


def section_news():
    headlines, source = ds.headlines()
    items, agg_stocks, agg_assets = [], {}, {}
    for h in headlines:
        r = analyze(h)
        ups, downs = r.ranked("up"), r.ranked("down")
        a_ups = r.ranked("up", r.asset_scores)
        a_downs = r.ranked("down", r.asset_scores)
        if not (ups or downs or a_ups or a_downs):
            continue
        items.append({
            "headline": h, "sentiment": round(r.sentiment, 2),
            "events": [n for n, _ in r.events],
            "stocks_up": [s for s, _ in ups[:5]], "stocks_down": [s for s, _ in downs[:5]],
            "assets_up": [a for a, _ in a_ups[:4]], "assets_down": [a for a, _ in a_downs[:4]],
        })
        for sym, sc in r.stock_scores.items():
            if abs(sc) > abs(agg_stocks.get(sym, (0, ""))[0]):
                agg_stocks[sym] = (sc, h)
        for a, sc in r.asset_scores.items():
            if abs(sc) > abs(agg_assets.get(a, (0, ""))[0]):
                agg_assets[a] = (sc, h)

    def recommend(agg, kind):
        recs = []
        for sym, (sc, h) in sorted(agg.items(), key=lambda x: -abs(x[1][0]))[:8]:
            if abs(sc) < 3.0:
                continue
            candles = ds.candles(sym)
            tr = analyze_technicals(candles[-75:], candles)
            side = "BUY" if sc > 0 else "SELL"
            d = 1 if sc > 0 else -1
            entry = round(tr.price, 2)
            stop = round(tr.price - d * tr.atr, 2)
            target = round(tr.price + d * 1.5 * tr.atr, 2)
            recs.append({"symbol": sym, "label": ASSET_LABEL.get(sym, sym),
                         "kind": kind, "view": "BULLISH" if sc > 0 else "BEARISH",
                         "side": side, "news_score": round(sc, 1),
                         "entry": entry, "stop": stop, "target": target,
                         "headline": h})
        return recs

    stock_recs = recommend(agg_stocks, "stock")
    asset_agg_cur = {k: v for k, v in agg_assets.items() if k in CURRENCIES}
    asset_agg_com = {k: v for k, v in agg_assets.items() if k in COMMODITIES}
    return {"source": source, "mode": ds.mode, "news": items,
            "stocks": stock_recs,
            "currencies": recommend(asset_agg_cur, "currency"),
            "commodities": recommend(asset_agg_com, "commodity")}


def section_combined():
    headlines, source = ds.headlines()
    stock_news, sector_news, why = merge_news(headlines)
    # include currencies/commodities in the combined scan
    agg_assets = {}
    for h in headlines:
        r = analyze(h)
        for a, sc in r.asset_scores.items():
            if abs(sc) > abs(agg_assets.get(a, (0, ""))[0]):
                agg_assets[a] = (sc, h)

    rows = []
    for sym in WATCHLIST:
        candles = ds.candles(sym)
        tr = analyze_technicals(candles[-75:], candles)
        news = stock_news.get(sym, 0.0)
        sector = sector_news.get(STOCK_SECTOR.get(sym, ""), 0.0)
        plan = trade_plan(sym, tr, news, sector, why.get(sym, "technical only"))
        rows.append({"symbol": sym, "kind": "stock", "label": sym,
                     "news_score": round(news, 1), "tech_score": tr.scores["ema_trend"],
                     "price": round(tr.price, 2), **plan})
    for sym, (sc, h) in agg_assets.items():
        candles = ds.candles(sym)
        tr = analyze_technicals(candles[-75:], candles)
        plan = trade_plan(sym, tr, sc, sc, f'news: "{h[:60]}"')
        rows.append({"symbol": sym, "kind": "currency" if sym in CURRENCIES else "commodity",
                     "label": ASSET_LABEL.get(sym, sym), "news_score": round(sc, 1),
                     "tech_score": tr.scores["ema_trend"],
                     "price": round(tr.price, 2), **plan})
    rows.sort(key=lambda r: (r["action"] == "WAIT", -r["confidence"]))
    return {"source": source, "mode": ds.mode, "signals": rows}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/" or u.path == "/index.html":
                body = open("index.html", "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif u.path == "/api/instruments":
                from news_impact.mappings import SECTOR_STOCKS
                all_stocks = sorted({s for lst in SECTOR_STOCKS.values() for s in lst}
                                    | set(WATCHLIST) | {"RELIANCE", "ADANIENT", "ADANIPORTS"})
                self._json({"stocks": all_stocks, "currencies": CURRENCIES,
                            "commodities": COMMODITIES, "labels": ASSET_LABEL,
                            "mode": ds.mode})
            elif u.path == "/api/market":
                self._json(section_market())
            elif u.path == "/api/technical":
                self._json(section_technical(q.get("symbol", ["TCS"])[0]))
            elif u.path == "/api/news":
                self._json(section_news())
            elif u.path == "/api/combined":
                self._json(section_combined())
            else:
                self._json({"error": "not found"}, 404)
        except Exception as e:
            self._json({"error": str(e)}, 500)


if __name__ == "__main__":
    print(f"Data source: {ds.mode}")
    print(f"Dashboard:   http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
