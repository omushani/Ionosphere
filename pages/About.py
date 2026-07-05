"""About IONOSPHERE — methodology pointers and disclaimers."""

from __future__ import annotations

import streamlit as st

from theme import inject_base_style, render_top_bar

st.set_page_config(page_title="IONOSPHERE — About", layout="wide", initial_sidebar_state="collapsed")

inject_base_style()
render_top_bar()

st.title("About IONOSPHERE")
st.markdown(
    """
This interface streams **end-of-day prices** through `yfinance` and runs an **XGBoost regressor**
that forecasts the **next trading day’s closing price** from recent momentum and volatility features.

**What you should know**

- Quotes and history refresh when you load a page; there is **no account system** and no server-side storage.
- The **Buy / Hold / Sell** label is a **rule applied to the model output** (see the project `README.md`
  for thresholds). It is **not** a guarantee of performance.
- Markets are non-stationary; any statistical model can be wrong — use this as a **learning tool**.

**Indicators shown**

- **MA10 / MA50**: short- and medium-term moving averages of close.
- **Volatility**: rolling standard deviation of daily returns (riskiness of recent moves).

For the full algorithm, validation split, and exact decision thresholds, open **`README.md`** in the repository.
"""
)

st.info("Not financial advice. Past model behaviour does not predict future results.")
