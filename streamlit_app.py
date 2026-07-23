"""AI Intraday Trading Assistant - Streamlit front-end.

Run locally (recommended for LIVE Kotak Neo):
    pip install streamlit
    streamlit run streamlit_app.py

Deploy on Streamlit Community Cloud:
    push this repo to GitHub, then "New app" -> pick streamlit_app.py.
    For LIVE data add your keys under Settings -> Secrets (see .streamlit/
    secrets.toml.sample) and enter your TOTP in the sidebar each session.

This reuses the SAME engine as the http.server app (technicals, signal engine,
news-impact) by importing app.py and swapping its data source.
"""
import streamlit as st
import streamlit.components.v1 as components

import app                       # reuse section_* logic
from data_source import DataSource
from news_impact.assets import CURRENCIES, COMMODITIES

st.set_page_config(page_title="Intraday Desk", page_icon="📈", layout="wide")

# ---------------------------------------------------------------- data source
def sim_ds():
    ds = DataSource.__new__(DataSource)          # simulated, no config.json read
    ds.mode = "SIMULATED"; ds.broker = None
    import time as _t; ds._rng_seed = int(_t.strftime("%Y%m%d"))
    return ds

def connect_live(ck, mobile, ucc, mpin, totp, env, live_trading):
    """Build a live Kotak Neo broker and attach it to a DataSource."""
    from broker import KotakNeoBroker
    broker = KotakNeoBroker(ck, mobile, ucc, mpin, environment=env,
                            live_trading=live_trading, totp=totp)
    ds = sim_ds()
    ds.broker = broker
    ds.mode = "LIVE (Kotak Neo)"
    return ds

if "ds" not in st.session_state:
    st.session_state.ds = sim_ds()
app.ds = st.session_state.ds                     # engine uses this data source

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### ⚙️ Data source")
    st.caption(f"Current mode: **{app.ds.mode}**")
    with st.expander("🔌 Connect Kotak Neo (live)", expanded=app.ds.broker is None):
        st.caption("Keys can be pre-filled from Streamlit secrets; TOTP is typed "
                   "here each session (it changes every 30s).")
        try:
            sec = dict(st.secrets.get("kotak", {}))
        except Exception:
            sec = {}
        ck = st.text_input("Consumer key / token", value=sec.get("consumer_key", ""), type="password")
        mobile = st.text_input("Mobile (+91…)", value=sec.get("mobile_number", ""))
        ucc = st.text_input("UCC", value=sec.get("ucc", ""))
        mpin = st.text_input("MPIN", value=sec.get("mpin", ""), type="password")
        totp = st.text_input("TOTP (authenticator)", max_chars=6)
        env = st.selectbox("Environment", ["prod", "uat"], index=0)
        live_trading = st.checkbox("Allow LIVE orders (unsafe)", value=False,
                                   help="Leave OFF for signal-only / paper mode.")
        if st.button("Connect", type="primary", use_container_width=True):
            try:
                st.session_state.ds = connect_live(ck, mobile, ucc, mpin, totp, env, live_trading)
                app.ds = st.session_state.ds
                st.success("Connected to Kotak Neo.")
                st.rerun()
            except Exception as e:
                st.error(f"Connection failed: {e}")
        if app.ds.broker is not None and st.button("Disconnect", use_container_width=True):
            st.session_state.ds = sim_ds(); st.rerun()
    st.divider()
    st.caption("⚠️ Not financial advice. In SIMULATED mode prices are illustrative.")

# ---------------------------------------------------------------- helpers
def pill(action):
    color = {"BUY": "#0A7D3B", "SELL": "#C6303E", "WAIT": "#B07908"}.get(action, "#888")
    return f"<span style='background:{color}22;color:{color};font-weight:700;padding:2px 10px;border-radius:99px'>{action}</span>"

def arrow(p):
    return "▲" if p > 0 else "▼" if p < 0 else "—"

# ---------------------------------------------------------------- header
mode = app.ds.mode
badge = "🟢 LIVE" if mode.startswith("LIVE") else "🟡 SIMULATED"
st.markdown(f"## 📈 Intraday Desk &nbsp;<span style='font-size:14px'>{badge}</span>",
            unsafe_allow_html=True)

# animated moving-indices ticker (marquee) in the header
mkt = app.section_market()
def _tk(it):
    c = "#0A7D3B" if it["pct"] >= 0 else "#C6303E"
    return (f"<span style='margin:0 22px;font-size:14px'><b>{it['label']}</b> "
            f"{it['price']:,.2f} <span style='color:{c}'>{arrow(it['pct'])} {it['pct']:+.2f}%</span></span>")
row = "".join(_tk(i) for i in mkt["indices"] + mkt["currencies"])
components.html(f"""
<div style="overflow:hidden;white-space:nowrap;background:#151C19;border-radius:10px">
  <div style="display:inline-block;padding:9px 0;color:#E8EEE9;animation:sl 40s linear infinite">{row}{row}</div>
</div>
<style>@keyframes sl{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}</style>
""", height=44)

tabs = st.tabs(["🏠 Overview", "1 · Technical", "2 · News Signals", "3 · Combined Desk"])

# ================================================================ OVERVIEW
with tabs[0]:
    st.markdown("#### Live indices")
    cols = st.columns(len(mkt["indices"]))
    for col, i in zip(cols, mkt["indices"]):
        col.metric(i["label"], f"{i['price']:,.0f}", f"{i['change']:+,.0f} ({i['pct']:+.2f}%)")

    st.markdown("#### Currencies")
    cols = st.columns(len(mkt["currencies"]))
    for col, c in zip(cols, mkt["currencies"]):
        col.metric(c["label"], f"{c['price']:,.3f}", f"{c['pct']:+.2f}%")

    g, l = st.columns(2)
    with g:
        st.markdown("#### 🟢 Top gainers")
        st.dataframe([{"Symbol": x["symbol"], "Price": x["price"], "%": x["pct"]}
                      for x in mkt["gainers"]], hide_index=True, use_container_width=True)
    with l:
        st.markdown("#### 🔴 Top losers")
        st.dataframe([{"Symbol": x["symbol"], "Price": x["price"], "%": x["pct"]}
                      for x in mkt["losers"]], hide_index=True, use_container_width=True)

    st.markdown("#### 📰 Market news")
    for h in mkt["news"]:
        st.markdown(f"- {h}")
    st.caption(f"News source: {mkt['source']}")

# ================================================================ SECTION 1
with tabs[1]:
    st.markdown("#### Technical analysis")
    kind = st.radio("Market", ["Stocks", "Currency", "Commodity"], horizontal=True)
    if kind == "Stocks":
        sym = st.text_input("NSE symbol (type any, then press Enter)", value="TCS").strip().upper() or "TCS"
    elif kind == "Currency":
        sym = st.selectbox("Instrument", CURRENCIES)
    else:
        sym = st.selectbox("Instrument", COMMODITIES)

    t = app.section_technical(sym)
    p = t["plan"]
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"### {t['label']}", unsafe_allow_html=True)
        st.markdown(f"# {pill(p['action'])} &nbsp;<span style='font-size:18px;color:#888'>{p['confidence']}%</span>",
                    unsafe_allow_html=True)
        st.metric("Last price", f"{t['price']:,.2f}")
        if t.get("placeholder"):
            st.info("No mock base price for this symbol — values are illustrative. Connect live for real data.")
    with c2:
        if p["action"] != "WAIT":
            st.markdown(f"**Entry** {p['entry']} · **Stop** :red[{p['stop']}] · "
                        f"**T1** :green[{p['target1']}] · **T2** :green[{p['target2']}] · **Qty** {p['qty']}")
        st.caption(p["reason"])
    ind = t["indicators"]
    st.markdown("#### Indicators")
    a, b, c, d = st.columns(4)
    a.metric("EMA 9 / 20 / 50", f"{ind['ema9']}", f"{ind['ema20']} / {ind['ema50']}")
    b.metric("VWAP", ind["vwap"]); b.metric("RSI", ind["rsi"])
    c.metric("MACD", ind["macd"], f"sig {ind['macd_signal']}"); c.metric("ATR", ind["atr"])
    d.metric("Support", ind["support"]); d.metric("Resistance", ind["resistance"])
    st.caption(f"Pattern: {ind['pattern']} · Volume ratio {ind['volume_ratio']}× · Pivot {ind['pivot']}")
    st.markdown("#### Price (last 75 candles)")
    st.line_chart([c["c"] for c in t["candles"]], height=200)

# ================================================================ SECTION 2
with tabs[2]:
    st.markdown("#### News-driven recommendations")
    n = app.section_news()
    st.caption(f"Source: {n['source']} · mode {n['mode']}")
    def rec_table(items, title):
        if not items:
            return
        st.markdown(f"##### {title}")
        st.dataframe([{"Symbol": r["symbol"], "View": r["view"], "Side": r["side"],
                       "News": r["news_score"], "Entry": r["entry"], "Stop": r["stop"],
                       "Target": r["target"], "Trigger": r["headline"][:70]}
                      for r in items], hide_index=True, use_container_width=True)
    rec_table(n["stocks"], "📊 Stocks")
    rec_table(n["currencies"], "💱 Currencies")
    rec_table(n["commodities"], "🛢️ Commodities")
    st.markdown("##### Headlines & impact")
    for it in n["news"]:
        up = ", ".join(it["stocks_up"] + it["assets_up"]) or "—"
        dn = ", ".join(it["stocks_down"] + it["assets_down"]) or "—"
        st.markdown(f"- **{it['headline']}**  \n:green[▲ {up}]  ·  :red[▼ {dn}]")

# ================================================================ SECTION 3
with tabs[3]:
    st.markdown("#### Combined desk — news + technicals, ranked")
    cmb = app.section_combined()
    st.caption(f"Source: {cmb['source']} · mode {cmb['mode']}")
    st.dataframe([{"Instrument": r["label"], "Kind": r["kind"], "Action": r["action"],
                   "Conf%": r["confidence"], "Price": r["price"], "Entry": r["entry"],
                   "Stop": r["stop"], "T1": r["target1"], "T2": r["target2"],
                   "News": r["news_score"], "Reason": r["reason"][:50]}
                  for r in cmb["signals"]], hide_index=True, use_container_width=True)
