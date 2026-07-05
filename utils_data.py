"""Helpers for market data (yfinance quirks, OHLC normalization)."""

import pandas as pd


def flatten_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse yfinance MultiIndex columns so Open/High/Low/Close are single level."""
    if df is None or df.empty:
        return df
    out = df.copy()
    if not isinstance(out.columns, pd.MultiIndex):
        return out
    level0 = out.columns.get_level_values(0)
    level1 = out.columns.get_level_values(1)
    ohlcv = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
    if ohlcv.intersection(set(level0)):
        out.columns = level0
    elif ohlcv.intersection(set(level1)):
        out.columns = level1
    else:
        out.columns = level0
    return out


def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    out = flatten_ohlc(df)
    if not isinstance(out.index, pd.DatetimeIndex):
        out.index = pd.to_datetime(out.index)
    return out.sort_index()


def fetch_ohlc(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
    return ensure_datetime_index(raw)
