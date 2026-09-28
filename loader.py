"""Download OHLCV data with yfinance and cache it as CSV in data/."""
from pathlib import Path
import pandas as pd
import yfinance as yf

CACHE = Path(__file__).parent


def load_ohlcv(ticker, start, end, refresh=False):
    """Date, Open, High, Low, Close, Adj Close, Volume for one ticker."""
    f = CACHE / f"{ticker}_{start}_{end}.csv"
    if f.exists() and not refresh:
        return pd.read_csv(f, index_col=0, parse_dates=True)
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.to_csv(f)
    return df


def load_prices(tickers, start, end):
    """Adjusted close prices (dividends reinvested) for several tickers."""
    return pd.concat(
        {t: load_ohlcv(t, start, end)["Adj Close"] for t in tickers}, axis=1
    ).dropna()
