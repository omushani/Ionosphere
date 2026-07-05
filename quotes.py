"""Batch quote helpers for the home page grid."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from utils_data import ensure_datetime_index


def latest_quotes(symbols: list[str]) -> pd.DataFrame:
    """Last close and session-over-session % change (daily bars)."""
    symbols = [s.strip().upper() for s in symbols if s and str(s).strip()]
    if not symbols:
        return pd.DataFrame(columns=["symbol", "last", "chg_pct", "currency_hint"])

    joined = " ".join(symbols)
    raw = yf.download(
        joined,
        period="15d",
        interval="1d",
        progress=False,
        group_by="ticker",
        threads=True,
        auto_adjust=False,
    )
    if raw.empty:
        return pd.DataFrame(columns=["symbol", "last", "chg_pct", "currency_hint"])

    rows: list[dict] = []

    def _hint(sym: str) -> str:
        if sym.endswith(".NS") or sym.endswith(".BO"):
            return "INR"
        return "USD"

    if len(symbols) == 1:
        sym = symbols[0]
        df = ensure_datetime_index(raw)
        close = df["Close"].dropna()
        if len(close) < 2:
            return pd.DataFrame(columns=["symbol", "last", "chg_pct", "currency_hint"])
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        chg = 100.0 * (last - prev) / prev if prev else 0.0
        rows.append(
            {"symbol": sym, "last": last, "chg_pct": chg, "currency_hint": _hint(sym)}
        )
        return pd.DataFrame(rows)

    cols = raw.columns
    if not isinstance(cols, pd.MultiIndex):
        return pd.DataFrame(columns=["symbol", "last", "chg_pct", "currency_hint"])

    level0 = cols.get_level_values(0).unique()
    for sym in symbols:
        if sym not in level0:
            continue
        try:
            sub = raw[sym].copy()
            if isinstance(sub.columns, pd.MultiIndex):
                sub.columns = sub.columns.get_level_values(-1)
            sub = ensure_datetime_index(sub)
            if "Close" not in sub.columns:
                continue
            close = sub["Close"].dropna()
            if len(close) < 2:
                continue
            last = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            chg = 100.0 * (last - prev) / prev if prev else 0.0
            rows.append(
                {"symbol": sym, "last": last, "chg_pct": chg, "currency_hint": _hint(sym)}
            )
        except Exception:
            continue

    return pd.DataFrame(rows)
