"""Full algo loop: candles -> technical scores -> merge with news -> ranked signals.

    from broker import MockBroker            # or KotakNeoBroker
    scan(broker, WATCHLIST, headlines)  ->  top signals with entry/SL/targets

Momentum slot = average of RSI-zone score and MACD-cross score (the 10%
"RSI/Momentum" weight from the design table).
"""
from news_impact import analyze
from news_impact.mappings import STOCK_SECTOR
from signal_engine import TechSnapshot, make_signal
from technicals import analyze_technicals

WATCHLIST = ["TCS", "INFY", "HCLTECH", "RELIANCE", "HDFCBANK", "ICICIBANK",
             "SBIN", "TATAMOTORS", "M&M", "MARUTI", "LT", "ULTRACEMCO", "ACC",
             "SUNPHARMA", "CIPLA", "ONGC", "IOC", "BPCL", "ASIANPAINT",
             "INDIGO", "HAL", "BEL", "TATAPOWER", "EXIDEIND", "TATASTEEL"]


def merge_news(headlines):
    """Analyze all fresh headlines, keep the strongest score per stock/sector."""
    stock_news, sector_news, why = {}, {}, {}
    for h in headlines:
        r = analyze(h)
        for sym, sc in r.stock_scores.items():
            if abs(sc) > abs(stock_news.get(sym, 0.0)):
                stock_news[sym] = sc
                why[sym] = f'{r.reasons.get(sym, "news")}: "{h[:60]}"'
        for sec, sc in r.sector_scores.items():
            if abs(sc) > abs(sector_news.get(sec, 0.0)):
                sector_news[sec] = sc
    return stock_news, sector_news, why


def scan(broker, watchlist, headlines, capital=5000.0, top_n=10):
    stock_news, sector_news, why = merge_news(headlines)
    signals = []
    for sym in watchlist:
        candles = broker.candles(sym)
        if len(candles) < 60:
            continue
        # with 5-min candles, one day ~ 75 candles; last 75 approximates today's session
        tr = analyze_technicals(candles[-75:], candles)
        tech = TechSnapshot(
            ema_trend=tr.scores["ema_trend"],
            vwap=tr.scores["vwap"],
            volume=tr.scores["volume"],
            rsi=(tr.scores["rsi"] + tr.scores["macd"]) / 2,
            candle=tr.scores["candle"],
        )
        news = stock_news.get(sym, 0.0)
        sector = sector_news.get(STOCK_SECTOR.get(sym, ""), 0.0)
        sig = make_signal(sym, news, sector, tech,
                          price=tr.price, atr=tr.atr, capital=capital,
                          reason=why.get(sym, "technical setup only"))
        sig.tech_report = tr
        signals.append(sig)
    signals.sort(key=lambda s: (s.action == "WAIT", -s.confidence))
    return signals[:top_n]


def print_signals(signals):
    print(f"{'SYMBOL':<12}{'ACTION':<7}{'CONF':<6}{'ENTRY':<9}{'SL':<9}{'T1':<9}{'T2':<9}{'QTY':<5}REASON")
    print("-" * 100)
    for s in signals:
        if s.action == "WAIT":
            print(f"{s.symbol:<12}{'WAIT':<7}{s.confidence:<6}{'-':<9}{'-':<9}{'-':<9}{'-':<9}{'-':<5}"
                  f"composite {s.composite:+.1f}")
        else:
            print(f"{s.symbol:<12}{s.action:<7}{s.confidence:<6}{s.entry:<9}{s.stop:<9}"
                  f"{s.target1:<9}{s.target2:<9}{s.qty:<5}{s.reason[:45]}")
