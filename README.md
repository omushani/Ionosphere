# IONOSPHERE

IONOSPHERE is a **Streamlit** dashboard that pulls **latest end-of-day market data** from **Yahoo Finance** (via `yfinance`) and runs a small **XGBoost** regression to produce a **next-session closing price** forecast. The UI highlights a **futuristic black + neon cyan** aesthetic, a **spotlight board** of popular symbols, **search / custom ticker** entry, **interactive candlesticks**, and an **in-sample prediction track** chart.

> **Disclaimer:** This project is for **education and experimentation**. It is **not** investment, tax, or legal advice. Models can fail, especially around shocks, gaps, or regime changes. **Never** trade on this output alone.

---

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Navigation uses a **top bar** (`Home`, `About`). The default Streamlit multipage sidebar is **hidden** via `.streamlit/config.toml` so the layout stays clean.

---

## Data freshness

- **Quotes** on the home page and **OHLC history** on the intel deck are fetched when you load or refresh the page (`yfinance` → Yahoo Finance).
- There is **no backend database** and **no user accounts**; nothing is stored server-side between sessions.

Discovery uses a **curated ticker list** (major US and NSE names) for fast filtering, but you may type **any valid Yahoo Finance symbol** (for example `TATAMOTORS.NS`, `BRK-B`, `ASMI.NS`, etc.).

---

## Machine learning — what is being predicted?

### Target

The model is trained to predict **`TargetNextClose`**: the **closing price of the *next* trading day**, using **only information observable on day *T***:

- `MA10`: 10-day simple moving average of close (includes day *T*).
- `MA50`: 50-day simple moving average of close.
- `Volatility`: 10-day rolling standard deviation of daily **simple returns** \(r_t = \frac{C_t - C_{t-1}}{C_{t-1}}\).

Formally, for each history row with known future close, we supervise:

\[
y_T = \mathrm{Close}_{T+1}
\quad\text{from features}\quad
\mathbf{x}_T = (\mathrm{MA10}_T,\ \mathrm{MA50}_T,\ \mathrm{Volatility}_T)
\]

The **live forecast** uses **the most recent row’s** \(\mathbf{x}_T\) after the latest daily bar is available.

### Algorithm

- **Model:** **XGBoost regressor** (`xgboost.XGBRegressor`) — gradient-boosted decision trees on the three numeric features.
- **Training rows:** all dates where `MA10`, `MA50`, `Volatility`, and `TargetNextClose` are all non-null (warm-up period drops the first ~50 sessions; the final calendar row has no realized next close yet and is excluded from *training labels*, but its features are still used for the **live** prediction).
- **Validation:** a **time-ordered** split: the **first ~82%** of rows train, the **last ~18%** evaluate **without shuffling** (roughly mimics “past predicts future” under a single stationary regime — still an approximation).
- **Deployment weights:** after reporting validation metrics, the model is **refit on all complete rows** so the deployed prediction uses maximum history while staying honest about the simplistic setup in documentation.

**Hyper-parameters (current defaults in code):** `n_estimators=200`, `max_depth=4`, `learning_rate=0.06`, `subsample=0.85`, `colsample_bytree=0.85`, `reg_lambda=1.0`, `random_state=42`. These are sensible, regularized defaults for a tiny feature set — not a claim of optimality.

---

## Buy / Hold / Sell rule (thresholds)

The model outputs a **scalar** \(\hat{C}_{T+1}\). Let \(C_T\) be the **latest observed close**. Define the **expected return**:

\[
\mathrm{Edge} = 100 \times \frac{\hat{C}_{T+1} - C_T}{C_T}
\]

**Decision bands** (see `model.py`):

| Signal | Condition on Edge | Meaning (heuristic) |
|--------|-------------------|------------------------|
| **BUY** | Edge **≥ +0.35%** | Model expects **at least ~35 bps** upside to the *next* close vs last close. |
| **SELL** | Edge **≤ −0.35%** | Model expects **at least ~35 bps** downside to the *next* close vs last close. |
| **HOLD** | Between those bounds | The forecast is **too close** to the last close to call a directional label. |

Constants: `DEFAULT_BUY_THRESHOLD_PCT = 0.35`, `DEFAULT_SELL_THRESHOLD_PCT = -0.35`.

These thresholds are **explicitly chosen** to reduce **noise trading** on tiny model fluctuations. They are **not** derived from transaction costs, slippage, or portfolio theory — they are a **transparent, conservative band** for UI labeling.

### “How much should I buy?” (illustrary sizing)

When the signal is **BUY**, the UI shows a **capped heuristic** `suggested_position_pct` between **5% and 15%** of a notional portfolio, scaling with how far `Edge` sits above the buy threshold. **This is not Kelly criterion, not risk parity, and not personalized** — it is only a visual aid with a hard cap (`MAX_SUGGESTED_ALLOCATION_PCT = 15.0`).

---

## Charts

- **Candlesticks:** built with **Plotly** from flattened Yahoo OHLC. Session breaks (weekends) are hidden via `rangebreaks` for readability.
- **ML track chart:** overlays **realized next close** vs **in-sample predicted next close** on the training rows. This shows **historical fit quality**, not a guarantee of future accuracy — the final live point is stated numerically above the chart.

---

## Project layout

| File | Role |
|------|------|
| `app.py` | Home: spotlight board, search, navigation |
| `pages/About.py` | Short methodology / disclaimers |
| `pages/stock_details.py` | Candlesticks, model output, charts |
| `model.py` | Feature pipeline, XGBoost train/predict, signal + sizing helpers |
| `utils_data.py` | Yahoo column flattening (MultiIndex quirks) |
| `quotes.py` | Batch quotes for the home grid |
| `tickers.py` | Curated popular + searchable symbols |
| `theme.py` | Shared neon styling |
| `.streamlit/config.toml` | Theme tokens + hide sidebar navigation |

---

## Limitations (read this)

- **Holdout metrics may look weak** (for example **negative R²** on the last time slice). With only three lagging features and a single global split, the regressor is **not** tuned for maximum predictive power — it is a **transparent baseline**. Check the expander on the intel deck and prefer the candlestick + context over the label when metrics are poor.
- **Single model / few features** cannot capture fundamentals, earnings, macro, FX, or sector rotation.
- **Regime shifts** (crashes, reforms, delistings) invalidate many statistical patterns.
- **India vs US tickers** differ in tick size, liquidity, and session rules — the *same* algorithm may behave differently.
- **Survivorship & corporate actions:** you rely on Yahoo’s adjusted series handling; always verify critical numbers with your broker.

If you want **stricter backtesting**, extend the code with walk-forward evaluation, purged splits, alternative targets, and richer features — the current app prioritizes **clarity and reproducibility** in a lightweight Streamlit demo.
