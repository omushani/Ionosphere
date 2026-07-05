"""
XGBoost regression: predict next trading day's close from prior EOD indicators.
See README for methodology, thresholds, and limitations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from xgboost import XGBRegressor

from utils_data import ensure_datetime_index


def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = ensure_datetime_index(df).copy()
    out["Return"] = out["Close"].pct_change()
    out["MA10"] = out["Close"].rolling(10).mean()
    out["MA50"] = out["Close"].rolling(50).mean()
    out["Volatility"] = out["Return"].rolling(10).std()
    # Target: next session close (walk-forward target)
    out["TargetNextClose"] = out["Close"].shift(-1)
    return out


def prepare_training(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with full features + known next-day close (excludes last bar)."""
    f = _feature_frame(df)
    cols = ["MA10", "MA50", "Volatility", "TargetNextClose", "Close"]
    f = f.dropna(subset=cols)
    return f


def train_model(df: pd.DataFrame) -> tuple[XGBRegressor, dict]:
    """
    Time-ordered split: last 18% of training rows as validation (no shuffle).
    Refit on all complete rows for production predictions used in the app.
    """
    train_tbl = prepare_training(df)
    if len(train_tbl) < 80:
        raise ValueError("Not enough history to train (need ~80+ trading days after warm-up).")

    X = train_tbl[["MA10", "MA50", "Volatility"]].values
    y = train_tbl["TargetNextClose"].values

    split = int(len(train_tbl) * 0.82)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    val_pred = model.predict(X_val)
    metrics = {
        "val_mape": float(mean_absolute_percentage_error(y_val, val_pred)),
        "val_r2": float(r2_score(y_val, val_pred)),
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
    }

    # Refit on all rows for deployment prediction
    model.fit(X, y)
    return model, metrics


def predict_next_close(model: XGBRegressor, df: pd.DataFrame) -> tuple[float, float, np.ndarray]:
    """
    Returns (predicted_next_close, last_observed_close, aligned_close_series_for_plot).
    Uses the latest bar's features to forecast the next close.
    """
    f = _feature_frame(df)
    feat = f.dropna(subset=["MA10", "MA50", "Volatility"])
    if feat.empty:
        raise ValueError("Insufficient data for features.")

    last_row = feat.iloc[-1]
    X_last = last_row[["MA10", "MA50", "Volatility"]].values.reshape(1, -1)
    pred = float(model.predict(X_last)[0])
    last_close = float(last_row["Close"])
    return pred, last_close, feat["Close"].values


def expected_return_pct(predicted_next: float, last_close: float) -> float:
    if last_close == 0:
        return 0.0
    return 100.0 * (predicted_next - last_close) / last_close


# Decision thresholds (documented in README)
DEFAULT_BUY_THRESHOLD_PCT = 0.35   # predicted edge vs last close
DEFAULT_SELL_THRESHOLD_PCT = -0.35
MAX_SUGGESTED_ALLOCATION_PCT = 15.0  # cap for displayed “suggested stake” (not financial advice)


def signal_from_prediction(
    predicted_next: float,
    last_close: float,
    buy_thr: float = DEFAULT_BUY_THRESHOLD_PCT,
    sell_thr: float = DEFAULT_SELL_THRESHOLD_PCT,
) -> tuple[str, str, float]:
    """
    Returns (label, detail_key, expected_return_percent).
    BUY if expected next close is > buy_thr% above last close.
    SELL if < sell_thr% (model expects pullback).
    Else HOLD.
    """
    er = expected_return_pct(predicted_next, last_close)
    if er >= buy_thr:
        return "BUY", "buy", er
    if er <= sell_thr:
        return "SELL", "sell", er
    return "HOLD", "hold", er


def suggested_position_pct(expected_return_pct: float, buy_threshold: float = DEFAULT_BUY_THRESHOLD_PCT) -> float:
    """
    Heuristic display only: scale conviction from threshold to cap.
    Not investment advice; README explains the formula.
    """
    if expected_return_pct <= buy_threshold:
        return 0.0
    # Linear ramp from threshold to ~3x threshold maps toward max allocation cap
    span = max(buy_threshold * 3.0 - buy_threshold, 1e-6)
    frac = (expected_return_pct - buy_threshold) / span
    frac = float(np.clip(frac, 0.0, 1.0))
    return round(5.0 + frac * (MAX_SUGGESTED_ALLOCATION_PCT - 5.0), 1)


def in_sample_prediction_series(model: XGBRegressor, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Aligned actual next closes vs model predictions on training rows (for charting)."""
    tbl = prepare_training(df)
    X = tbl[["MA10", "MA50", "Volatility"]].values
    pred = model.predict(X)
    # Index: date when features were observed; values correspond to target next close date conceptually
    actual_next = tbl["TargetNextClose"]
    predicted = pd.Series(pred, index=tbl.index, name="PredictedNextClose")
    actual = pd.Series(actual_next.values, index=tbl.index, name="ActualNextClose")
    return actual, predicted
