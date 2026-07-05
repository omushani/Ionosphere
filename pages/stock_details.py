from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from model import (
    DEFAULT_BUY_THRESHOLD_PCT,
    DEFAULT_SELL_THRESHOLD_PCT,
    in_sample_prediction_series,
    predict_next_close,
    signal_from_prediction,
    suggested_position_pct,
    train_model,
)
from theme import inject_base_style, render_top_bar
from utils_data import ensure_datetime_index

st.set_page_config(page_title="IONOSPHERE — Intel deck", layout="wide", initial_sidebar_state="collapsed")

inject_base_style()
render_top_bar()

stock = (st.session_state.get("stock") or "").strip().upper()
if not stock:
    st.warning("No symbol selected. Return **Home** and open a spotlight or search result.")
    st.stop()

@st.cache_data(ttl=300)
def load_ohlc(symbol: str):
    raw = yf.download(symbol, period="18mo", interval="1d", progress=False, auto_adjust=False)
    return ensure_datetime_index(raw)


def _safe_float(value):
    try:
        if value is None:
            return None
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except Exception:
        return None


def _fmt_ratio(value: float | None, digits: int = 2) -> str:
    return f"{value:.{digits}f}" if value is not None else "N/A"


def _fmt_pct(value: float | None, digits: int = 2) -> str:
    return f"{value:.{digits}f}%" if value is not None else "N/A"


def _pe_view(pe: float | None) -> tuple[str, str]:
    if pe is None or pe <= 0:
        return "N/A", "Insufficient earnings data"
    if pe < 15:
        return "Undervalued zone", "Lower vs many peers"
    if pe <= 30:
        return "Fairly valued zone", "Near common growth bands"
    return "Expensive zone", "High multiple risk"


def _pb_view(pb: float | None) -> tuple[str, str]:
    if pb is None or pb <= 0:
        return "N/A", "Book value data unavailable"
    if pb < 1:
        return "Undervalued zone", "Below book-value range"
    if pb <= 3:
        return "Fairly valued zone", "Typical capital-light range"
    return "Expensive zone", "Paying large premium to book"


def _roe_view(roe_pct: float | None) -> tuple[str, str]:
    if roe_pct is None:
        return "N/A", "Profitability data unavailable"
    if roe_pct >= 15:
        return "Strong profitability", "Efficient equity compounding"
    if roe_pct >= 8:
        return "Moderate profitability", "Acceptable efficiency"
    return "Weak profitability", "Low return on equity base"


def _de_view(de_ratio: float | None) -> tuple[str, str]:
    if de_ratio is None:
        return "N/A", "Leverage data unavailable"
    if de_ratio < 0.5:
        return "Low leverage", "Balance sheet appears stable"
    if de_ratio <= 1.0:
        return "Medium leverage", "Debt level is manageable"
    return "High leverage risk", "Debt load is elevated"


def _latest_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    feat = df.copy()
    feat["Return"] = feat["Close"].pct_change()
    feat["MA10"] = feat["Close"].rolling(10).mean()
    feat["MA50"] = feat["Close"].rolling(50).mean()
    feat["Volatility"] = feat["Return"].rolling(10).std()
    return feat.dropna(subset=["MA10", "MA50", "Volatility"])

try:
    df_chart = load_ohlc(stock)
    if df_chart.empty or "Close" not in df_chart.columns:
        st.error("No price data for this symbol. Check the ticker (e.g. `.NS` for NSE).")
        st.stop()
except Exception:
    st.error("Could not download prices. Check connectivity or the symbol.")
    st.stop()

ticker_meta = yf.Ticker(stock)
try:
    meta = ticker_meta.info or {}
except Exception:
    meta = {}

name = meta.get("longName") or meta.get("shortName") or stock
sector = meta.get("sector") or "—"
industry = meta.get("industry") or "—"
cur = meta.get("currency") or ("INR" if stock.endswith(".NS") or stock.endswith(".BO") else "USD")

pe = _safe_float(meta.get("trailingPE")) or _safe_float(meta.get("forwardPE"))
pb = _safe_float(meta.get("priceToBook"))
roe_raw = _safe_float(meta.get("returnOnEquity"))
roe_pct = (roe_raw * 100.0) if (roe_raw is not None and abs(roe_raw) <= 1.5) else roe_raw
de_raw = _safe_float(meta.get("debtToEquity"))
# Yahoo often returns D/E in percent points for many symbols. Normalize heuristically for risk labels.
de_ratio = (de_raw / 100.0) if (de_raw is not None and de_raw > 20) else de_raw

c1, c2, c3, c4 = st.columns(4)
c1.metric("Symbol", stock)
c2.metric("Listing currency", cur)
c3.metric("Sector", sector)
c4.metric("Industry", industry)

st.markdown(f"## {name}")

st.markdown(
    f"""
<div class="neon-card">
  <div style="font-size:0.9rem;opacity:0.85;margin-bottom:0.35rem;">Company context</div>
  <div style="display:flex;flex-wrap:wrap;gap:1rem;">
    <div><span class="neon-pill">Sector</span> <span style="margin-left:0.45rem;">{sector}</span></div>
    <div><span class="neon-pill">Industry</span> <span style="margin-left:0.45rem;">{industry}</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---- Candlesticks (ensure numpy arrays for Plotly - fixes some Streamlit/yfinance dtypes) ----
dc = df_chart.dropna(subset=["Open", "High", "Low", "Close"]).copy()
xs = dc.index
o = np.asarray(dc["Open"], dtype=float)
h = np.asarray(dc["High"], dtype=float)
l = np.asarray(dc["Low"], dtype=float)
c = np.asarray(dc["Close"], dtype=float)

fig_c = go.Figure(
    data=[
        go.Candlestick(
            x=xs,
            open=o,
            high=h,
            low=l,
            close=c,
            name="OHLC",
            increasing_line_color="#2cefff",
            decreasing_line_color="#ff3d71",
            increasing_fillcolor="rgba(44,239,255,0.35)",
            decreasing_fillcolor="rgba(255,61,113,0.32)",
        )
    ]
)
fig_c.update_layout(
    template="plotly_dark",
    title="Candlesticks (daily)",
    xaxis_rangeslider_visible=False,
    paper_bgcolor="rgba(8,10,16,0)",
    plot_bgcolor="rgba(12,16,24,0.65)",
    font=dict(color="#dbefff"),
    margin=dict(l=12, r=12, t=48, b=12),
    xaxis=dict(gridcolor="rgba(0,212,255,0.08)", showgrid=True),
    yaxis=dict(gridcolor="rgba(0,212,255,0.08)", showgrid=True),
)
fig_c.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
st.plotly_chart(fig_c, use_container_width=True)

# ---- Fundamental ratio panel ----
st.markdown("### Fundamental Snapshot")
r1, r2, r3, r4 = st.columns(4)

pe_title, pe_note = _pe_view(pe)
pb_title, pb_note = _pb_view(pb)
roe_title, roe_note = _roe_view(roe_pct)
de_title, de_note = _de_view(de_ratio)

with r1:
    st.markdown(
        f"""
<div class="neon-card">
  <div class="neon-pill">P/E Ratio</div>
  <div style="font-size:1.45rem;font-weight:700;margin-top:0.4rem;">{_fmt_ratio(pe)}</div>
  <div style="margin-top:0.25rem;font-weight:600;">{pe_title}</div>
  <div style="opacity:0.85;font-size:0.9rem;">{pe_note}</div>
</div>
""",
        unsafe_allow_html=True,
    )
with r2:
    st.markdown(
        f"""
<div class="neon-card">
  <div class="neon-pill">P/B Ratio</div>
  <div style="font-size:1.45rem;font-weight:700;margin-top:0.4rem;">{_fmt_ratio(pb)}</div>
  <div style="margin-top:0.25rem;font-weight:600;">{pb_title}</div>
  <div style="opacity:0.85;font-size:0.9rem;">{pb_note}</div>
</div>
""",
        unsafe_allow_html=True,
    )
with r3:
    st.markdown(
        f"""
<div class="neon-card">
  <div class="neon-pill">ROE</div>
  <div style="font-size:1.45rem;font-weight:700;margin-top:0.4rem;">{_fmt_pct(roe_pct)}</div>
  <div style="margin-top:0.25rem;font-weight:600;">{roe_title}</div>
  <div style="opacity:0.85;font-size:0.9rem;">{roe_note}</div>
</div>
""",
        unsafe_allow_html=True,
    )
with r4:
    st.markdown(
        f"""
<div class="neon-card">
  <div class="neon-pill">Debt / Equity</div>
  <div style="font-size:1.45rem;font-weight:700;margin-top:0.4rem;">{_fmt_ratio(de_ratio)}</div>
  <div style="margin-top:0.25rem;font-weight:600;">{de_title}</div>
  <div style="opacity:0.85;font-size:0.9rem;">{de_note}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---- ML ----
with st.spinner("Training / scoring XGBoost regressor …"):
    try:
        model, metrics = train_model(df_chart)
        pred_next, last_close, _ = predict_next_close(model, df_chart)
        actual_next, pred_series = in_sample_prediction_series(model, df_chart)
    except Exception as e:
        st.error(f"Model error: {e}")
        st.stop()

label, _, exp_ret = signal_from_prediction(pred_next, last_close)
suggest = suggested_position_pct(exp_ret)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Last close", f"{last_close:,.2f}")
m2.metric("Model next close", f"{pred_next:,.2f}")
m3.metric("Implied move", f"{exp_ret:+.2f}%")
if label == "BUY":
    m4.metric("Stance", label, delta=f"~{suggest}% suggested sizing cap")
elif label == "SELL":
    m4.metric("Stance", label, delta="Downside bias vs last close")
else:
    m4.metric("Stance", label, delta="Inside dead-band")

if label == "BUY":
    st.success(
        f"**BUY bias** — expected next close **{exp_ret:+.2f}%** vs last close "
        f"(threshold ≥ **{DEFAULT_BUY_THRESHOLD_PCT}%**)."
    )
elif label == "SELL":
    st.error(
        f"**SELL / risk-off bias** — expected next close **{exp_ret:+.2f}%** "
        f"(threshold ≤ **{DEFAULT_SELL_THRESHOLD_PCT}%**)."
    )
else:
    st.warning(
        f"**HOLD band** — model edge **{exp_ret:+.2f}%** sits between "
        f"{DEFAULT_SELL_THRESHOLD_PCT}% and +{DEFAULT_BUY_THRESHOLD_PCT}%."
    )

st.caption(
    "Suggested stake is a capped heuristic from signal strength — illustrative only, not advice."
)

# ---- Explainable AI (SHAP) ----
st.markdown("### Explainable AI (SHAP)")
try:
    import shap

    latest_feat = _latest_feature_frame(df_chart).iloc[-1]
    feature_names = ["MA10", "MA50", "Volatility"]
    x_latest = latest_feat[feature_names].values.reshape(1, -1)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x_latest)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    shap_latest = np.asarray(shap_values).reshape(-1)

    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.asarray(base_value).reshape(-1)[0])
    else:
        base_value = float(base_value)

    contrib_df = pd.DataFrame(
        {
            "Feature": feature_names,
            "SHAPContribution": shap_latest,
            "FeatureValue": [float(latest_feat[f]) for f in feature_names],
        }
    ).sort_values("SHAPContribution", key=lambda s: np.abs(s), ascending=False)
    contrib_df["Direction"] = np.where(contrib_df["SHAPContribution"] >= 0, "Pushes up", "Pushes down")
    contrib_df["Color"] = np.where(contrib_df["SHAPContribution"] >= 0, "#29ffb0", "#ff5f87")

    x1, x2, x3 = st.columns(3)
    x1.metric("SHAP base value", f"{base_value:,.2f}")
    x2.metric("SHAP sum contribution", f"{contrib_df['SHAPContribution'].sum():+,.2f}")
    x3.metric("Predicted next close", f"{pred_next:,.2f}")

    fig_shap = go.Figure(
        data=[
            go.Bar(
                x=contrib_df["SHAPContribution"],
                y=contrib_df["Feature"],
                orientation="h",
                marker_color=contrib_df["Color"],
                text=[
                    f"{row.Direction}: {row.SHAPContribution:+.3f}<br>Value: {row.FeatureValue:,.3f}"
                    for row in contrib_df.itertuples(index=False)
                ],
                hovertemplate="%{text}<extra></extra>",
            )
        ]
    )
    fig_shap.update_layout(
        template="plotly_dark",
        title="Feature contribution to this stock's latest prediction",
        paper_bgcolor="rgba(8,10,16,0)",
        plot_bgcolor="rgba(12,16,24,0.65)",
        font=dict(color="#dbefff"),
        margin=dict(l=12, r=12, t=56, b=12),
        xaxis=dict(title="SHAP value impact on predicted next close", gridcolor="rgba(0,212,255,0.08)"),
        yaxis=dict(gridcolor="rgba(0,212,255,0.08)", categoryorder="array", categoryarray=list(contrib_df["Feature"])[::-1]),
    )
    st.plotly_chart(fig_shap, use_container_width=True)
    st.caption(
        "Positive SHAP values push the prediction up; negative values pull it down. "
        "This explains this stock card's current forecast in feature-level terms."
    )
except Exception as shap_err:
    st.warning(f"SHAP explanation unavailable for this session: {shap_err}")
    st.caption("Install dependency with `pip install shap` to enable per-stock explainable AI charts.")

with st.expander("Model Health (Holdout Slice)"):
    st.markdown("#### Validation metrics")
    st.write( 
        {
            "validation MAPE": round(metrics["val_mape"], 4),
            #"validation R²": round(metrics["val_r2"], 4),
            "train rows": metrics["n_train"],
            #"validation rows": metrics["n_val"],
        }
    )
    if metrics["val_r2"] < 0:
        st.caption(
            "Negative R² on this tail means a naive mean benchmark beat the model there — "
            "treat directional labels as weakly informative, not authoritative."
        )

# ---- Prediction vs realized next close (in-sample, lagged alignment) ----
fig_p = go.Figure()
fig_p.add_trace(
    go.Scatter(
        x=actual_next.index,
        y=actual_next.values,
        mode="lines",
        name="Realized next close",
        line=dict(color="#8af8ff", width=2),
    )
)
fig_p.add_trace(
    go.Scatter(
        x=pred_series.index,
        y=pred_series.values,
        mode="lines",
        name="Predicted next close (in-sample)",
        line=dict(color="#7c4dff", width=2, dash="dash"),
    )
)
fig_p.update_layout(
    template="plotly_dark",
    title="Model track: fitted next-day close vs actual (historical rows)",
    paper_bgcolor="rgba(8,10,16,0)",
    plot_bgcolor="rgba(12,16,24,0.65)",
    font=dict(color="#dbefff"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
    margin=dict(l=12, r=12, t=56, b=12),
    xaxis=dict(gridcolor="rgba(0,212,255,0.08)"),
    yaxis=dict(gridcolor="rgba(0,212,255,0.08)"),
)
st.plotly_chart(fig_p, use_container_width=True)

st.markdown("### Investment Simulator")
slider_col, stats_col = st.columns([1.4, 1])
with slider_col:
    invest_amount = st.slider(
        "Select investment amount",
        min_value=1000,
        max_value=2_000_000,
        value=100_000,
        step=1000,
    )
with stats_col:
    expected_profit = invest_amount * (exp_ret / 100.0)
    expected_value = invest_amount + expected_profit
    st.metric("Invested amount", f"{cur} {invest_amount:,.0f}")
    st.metric("Estimated profit/loss", f"{cur} {expected_profit:,.2f}")
    st.metric("Estimated next value", f"{cur} {expected_value:,.2f}")

fig_inv = go.Figure()
fig_inv.add_trace(
    go.Bar(
        x=["Invested", "Estimated next value"],
        y=[invest_amount, expected_value],
        marker_color=["#00d4ff", "#7c4dff"],
        opacity=0.9,
        text=[f"{cur} {invest_amount:,.0f}", f"{cur} {expected_value:,.0f}"],
        textposition="outside",
        name="Value comparison",
    )
)
fig_inv.add_trace(
    go.Scatter(
        x=["Invested", "Estimated next value"],
        y=[invest_amount, expected_value],
        mode="lines+markers",
        line=dict(color="#2cefff", width=2),
        name="Trend",
    )
)
fig_inv.update_layout(
    template="plotly_dark",
    title="Investment vs estimated next-session value",
    paper_bgcolor="rgba(8,10,16,0)",
    plot_bgcolor="rgba(12,16,24,0.65)",
    font=dict(color="#dbefff"),
    margin=dict(l=12, r=12, t=56, b=12),
    yaxis=dict(gridcolor="rgba(0,212,255,0.08)"),
    xaxis=dict(gridcolor="rgba(0,212,255,0.08)"),
    showlegend=False,
)
st.plotly_chart(fig_inv, use_container_width=True)

with st.expander("Glossary - Terms Used in the Forecast"):
    st.markdown("#### Core terms")
    st.markdown(
        """
- **Next close prediction**: XGBoost regression output for the upcoming session’s closing price, using
  the most recent fully formed features.
- **MA10 / MA50**: mean close over 10 / 50 sessions; capture short and medium drift.
- **Volatility**: dispersion of recent daily returns — higher values imply wider swings.
- **Implied move**: percent gap between predicted next close and the latest observed close.
- **Dead-band (HOLD)**: small predicted edge where the app does not call a directional trade
  (see README thresholds).
"""
    )

if st.button("Back to home", use_container_width=False):
    st.switch_page("app.py")

st.caption("IONOSPHERE prototype — educational use only.")
