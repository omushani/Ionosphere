"""IONOSPHERE — home: featured quotes, search, navigation."""

from __future__ import annotations

import streamlit as st

from quotes import latest_quotes
from theme import inject_base_style, render_top_bar
from tickers import POPULAR_TICKERS, SEARCH_TICKERS, filter_tickers

st.set_page_config(
    page_title="IONOSPHERE — Market intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_base_style()
render_top_bar()

st.markdown("### Neural market brief")
st.caption(
    "Live end-of-day context from Yahoo Finance. Pick a spotlight symbol or search thousands of tickers."
)

with st.spinner("Pulling spotlight tape …"):
    qdf = latest_quotes(POPULAR_TICKERS)

if not qdf.empty:
    qdf = qdf.copy()
    order_map = {s: i for i, s in enumerate(POPULAR_TICKERS)}
    qdf["_ord"] = qdf["symbol"].map(order_map)
    qdf = qdf.sort_values("_ord").drop(columns=["_ord"])

st.markdown("#### Spotlight board")
if qdf.empty:
    st.warning("Could not load featured quotes (network or symbol issue). Search below still works.")
else:
    cols_per_row = 3
    for i in range(0, len(qdf), cols_per_row):
        row = qdf.iloc[i : i + cols_per_row]
        c = st.columns(len(row))
        for j, (_, r) in enumerate(row.iterrows()):
            sym = r["symbol"]
            chg = r["chg_pct"]
            last = r["last"]
            hint = r.get("currency_hint", "")
            color = "#5cffa8" if chg >= 0 else "#ff6b8a"
            glow = "0 0 18px rgba(92, 255, 168, 0.35)" if chg >= 0 else "0 0 18px rgba(255, 107, 138, 0.35)"
            with c[j]:
                st.markdown(
                    f"""
<div class="neon-card">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span class="neon-pill">{sym}</span>
    <span style="font-size:0.82rem;opacity:0.85;">{hint}</span>
  </div>
  <div style="font-size:1.35rem;font-weight:700;margin:0.35rem 0 0.15rem 0;">{last:,.2f}</div>
  <div style="color:{color};text-shadow:{glow};font-weight:600;">{chg:+.2f}% session Δ</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                if st.button("Intel deck", key=f"deck_{sym}", use_container_width=True):
                    st.session_state["stock"] = sym
                    st.switch_page("pages/stock_details.py")

st.divider()
st.markdown("#### Symbol search")
st.caption(
    f"Curated list covers major US and NSE names ({len(SEARCH_TICKERS)}). "
    "You can also type any valid Yahoo Finance ticker (e.g. `BRK-B`, `TATAMOTORS.NS`)."
)

c1, c2 = st.columns([2, 1])
with c1:
    needle = st.text_input("Filter curated list", placeholder="Type TCS, AAPL, RELIANCE…")
with c2:
    custom_sym = st.text_input("Custom ticker", placeholder="SYMBOL or SYMBOL.NS")

matches = filter_tickers(needle, limit=60)
choice: str | None
if matches:
    choice = st.selectbox("Matches", matches, index=0)
else:
    choice = None
    st.info("No curated matches for that filter — enter a **custom ticker** (Yahoo format).")

go = st.button("Open intel deck", type="primary", use_container_width=False)
symbol_to_open = (custom_sym or "").strip().upper() or (choice or "")

if go:
    if not symbol_to_open:
        st.error("Choose a match or enter a custom ticker.")
    else:
        st.session_state["stock"] = symbol_to_open
        st.switch_page("pages/stock_details.py")

st.caption("Educational prototype — not financial advice.")
