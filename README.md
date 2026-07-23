# AI Intraday Trading Assistant - News Impact Engine

The module that answers: **"This news just broke - which sector and which specific
stocks will go UP or DOWN?"**

## What it does

Headline in -> analysis out:

1. **Event detection** - 20+ rules for macro/policy events (war near oil regions,
   crude moves, RBI rate cuts/hikes, budget incentives for EVs, infra/railway/defence
   spending, USFDA warnings/approvals, monsoon, rupee moves, telecom tariffs...).
   Each rule maps to sector scores from -10 to +10.
2. **Company detection** - finds named companies ("Sun Pharma", "L&T", "Tata Motors")
   and maps them to NSE symbols.
3. **Company events** - earnings beat/miss, order wins, SEBI/ED probes, CEO exits,
   rating changes -> direct score for the named stock.
4. **Impact propagation** - sector score flows to member stocks (x0.8); a named
   stock's shock flows to its closest peers (x0.5). News on TCS also flags
   INFY/HCLTECH/WIPRO.
5. **Sentiment layer** - keyword tone score as a tiebreaker for unmatched headlines.

Output: ranked LIKELY UP / LIKELY DOWN stock lists with scores and reasons.

## Files

| File | Purpose |
|---|---|
| `news_impact/events.py` | Event rules (add new scenarios here) |
| `news_impact/mappings.py` | Sector->stocks, peers, company aliases |
| `news_impact/sentiment.py` | Keyword sentiment scorer |
| `news_impact/analyzer.py` | Core pipeline |
| `news_impact/feed.py` | Free RSS ingestion (ET, Moneycontrol, Mint, BS) |
| `signal_engine.py` | Combines news (30%) + sector (20%) + technicals (50%) into BUY/SELL/WAIT with entry/SL/targets and position size |
| `live_scanner.py` | Run during market hours - polls feeds, prints alerts |
| `demo.py` | Offline demo with sample headlines |

## Run

```
python3 demo.py           # offline demo
python3 live_scanner.py   # live (needs internet)
```

No dependencies - pure Python 3 standard library.

## Extending it

- **New event type**: add a dict to `EVENT_RULES` in `events.py` (triggers + sector scores).
- **New stock/alias**: add to `mappings.py`.
- **Smarter sentiment**: route high-impact headlines to the Claude API in
  `analyzer.py` and blend with the rule score.
- **Kotak Neo execution**: after the signal-only phase proves profitable, wire
  `signal_engine.Signal` into the Neo API order call. Keep manual approval first.

## Honest limitations (read before trading real money)

- Rules are hand-written priors, not learned from data - **backtest before trusting**.
- Free RSS is delayed 1-15 min; big moves often happen in the first seconds.
  Institutional desks with paid low-latency feeds will react before you.
- A headline can match no rule (falls back to weak sentiment-only analysis).
- News score alone should never trigger a trade - the signal engine requires
  technical confirmation and cuts confidence when news and technicals disagree.
- With Rs 5,000 capital, brokerage + slippage eat a large % of each trade.
  Signal-only + paper trading first is the right call.

## Technical analysis + broker layer (added)

| File | Purpose |
|---|---|
| `technicals.py` | Computes EMA 9/20/50, session VWAP, RSI, MACD, ATR, volume spike, support/resistance, candlestick patterns (engulfing, hammer, shooting star, marubozu) from raw OHLCV candles, and normalizes each to a -10..+10 score |
| `broker.py` | `KotakNeoBroker` (real, uses `pip install neo-api-client`, paper-mode by default - refuses live orders unless `live_trading=True`) and `MockBroker` (random-walk candles for testing) |
| `scanner.py` | The algo loop: candles -> technicals -> merge with news -> ranked BUY/SELL/WAIT with entry/SL/T1/T2/qty |
| `demo_algo.py` | End-to-end demo with simulated market reacting to news |

```
python3 demo_algo.py      # full pipeline, no credentials needed
```

### Going live with Kotak Neo

1. Get API keys at napi.kotaksecurities.com (consumer key/secret).
2. `pip install neo-api-client`
3. Replace `MockBroker` with `KotakNeoBroker(...)` in your run script; it will
   ask for the OTP once per session.
4. IMPORTANT: the public Neo SDK has no historical-candles endpoint. Warm up
   indicators from another source (e.g. `yfinance` 5-min data for NSE symbols,
   suffix `.NS`) and build live candles from Neo's websocket ticks.
5. Keep `live_trading=False` (paper mode) until weeks of paper results are
   consistently positive.

## Dashboard (added)

`python3 app.py` then open **http://localhost:8420** — no pip installs needed.

Three sections:
1. **Technical Analysis** - pick stock / currency (USDINR, EURINR, GBPINR, JPYINR) /
   commodity (MCX gold, silver, crude, natgas, copper, zinc, aluminium). Shows EMA 9/20/50,
   session VWAP, RSI, MACD, ATR, volume spike, support/pivot/resistance, candlestick
   pattern, a session sparkline - and a verdict strip: BUY/SELL/WAIT with entry, stop
   loss, T1, T2.
2. **News Signals** - live headlines (RSS) analyzed for affected stocks, currencies and
   commodities; each recommendation shows BULLISH/BEARISH, trade side, entry, stop, target.
3. **Combined Desk** - news (30%) + sector (20%) + technicals (50%) merged across the
   whole watchlist plus currencies/commodities, ranked by confidence; trades only fire
   when news and technicals agree.

Light/dark toggle in the header (remembered between visits). The badge shows whether
data is LIVE (Kotak Neo configured via config.json) or SIMULATED - you always know
which one you're looking at.

To go live: create `config.json` next to `app.py` (see data_source.py docstring) and
`pip install neo-api-client`. Without it the app runs fully in simulation mode.

---

## Deploying to GitHub

1. On your machine, open a terminal in this folder (the one with `app.py`).
2. Run:
   ```bash
   git init
   git add .
   git commit -m "AI Intraday Trading Assistant"
   git remote add origin https://github.com/<your-username>/trading-assistant.git
   git branch -M main
   git push -u origin main
   ```
3. `config.json` and `.streamlit/secrets.toml` are gitignored, so your Kotak Neo
   credentials never leave your machine. Verify with `git status --ignored`.

## Running on Streamlit

The Streamlit UI lives in `streamlit_app.py` and reuses the same engine.

### Local (recommended for LIVE Kotak Neo)
```bash
pip install streamlit
streamlit run streamlit_app.py
```
Open the sidebar -> "Connect Kotak Neo (live)", fill in consumer key / mobile /
UCC / MPIN, type your current 6-digit TOTP, and press Connect.

### Streamlit Community Cloud (public URL)
1. Push this repo to GitHub (above).
2. On share.streamlit.io -> New app -> pick your repo and `streamlit_app.py`.
3. For LIVE data:
   - Uncomment the `neo_api_client` line in `requirements.txt`.
   - App -> Settings -> Secrets -> paste the block from
     `.streamlit/secrets.toml.sample` with your real values.
   - Enter your TOTP in the sidebar each session (it changes every 30s and
     cannot be stored).

### Live-data caveats (read before relying on it)
- **TOTP is per-session and manual** — Kotak's login needs a fresh authenticator
  code; there is no way to automate it on a headless host.
- **Kotak Neo has no historical-candle REST endpoint.** Live *quotes* work, but
  the multi-candle technicals need candles built from the live websocket feed
  (or warmed from another source). Until that's wired up, technical indicators
  fall back to simulated candles even in LIVE mode. Quotes, news and the signal
  logic are all real.
- Keep `live_trading` OFF (default) so the app is signal-only / paper.
