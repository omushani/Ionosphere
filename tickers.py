"""
Curated symbols for the home grid and typeahead search.
Live quotes come from yfinance at runtime; this list drives discovery in a static app.
"""

# Featured on the home page (mix of US ADRs / mega-caps and India NSE)
POPULAR_TICKERS = [
    # US
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "JPM",
    "V",
    "JNJ",
    # India (NSE)
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "HINDUNILVR.NS",
    "ITC.NS",
    "LT.NS",
]

# Broader set for search (major US + common NSE names). Users can still type any yfinance symbol.
SEARCH_TICKERS = sorted(
    set(
        POPULAR_TICKERS
        + [
            "WMT",
            "PG",
            "MA",
            "UNH",
            "HD",
            "DIS",
            "BAC",
            "XOM",
            "CVX",
            "COST",
            "ADBE",
            "NFLX",
            "AMD",
            "INTC",
            "PYPL",
            "CRM",
            "COIN",
            "UBER",
            "ABNB",
            "NKE",
            "MCD",
            "PEP",
            "KO",
            "PFE",
            "MRK",
            "ABBV",
            "WFC",
            "CSCO",
            "ORCL",
            "IBM",
            "QCOM",
            "TXN",
            "AMAT",
            "NOW",
            "PANW",
            "SHOP",
            "BABA",
            "NIO",
            "DIVISLAB.NS",
            "WIPRO.NS",
            "HCLTECH.NS",
            "TECHM.NS",
            "AXISBANK.NS",
            "KOTAKBANK.NS",
            "ASIANPAINT.NS",
            "MARUTI.NS",
            "TITAN.NS",
            "SUNPHARMA.NS",
            "ULTRACEMCO.NS",
            "NESTLEIND.NS",
            "BAJFINANCE.NS",
            "ONGC.NS",
            "POWERGRID.NS",
            "NTPC.NS",
            "COALINDIA.NS",
            "TATAMOTORS.NS",
            "M&M.NS",
        ]
    )
)


def filter_tickers(query: str, limit: int = 40) -> list[str]:
    q = (query or "").strip().upper()
    if not q:
        return SEARCH_TICKERS[:limit]
    return [t for t in SEARCH_TICKERS if q in t][:limit]
