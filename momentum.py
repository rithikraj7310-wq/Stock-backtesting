import pandas as pd
from .base import Strategy, empty_targets, period_ends


class Momentum(Strategy):
    """Strategy B: each month-end, stay invested if the last 6-month return > 0, else cash."""
    name = "Momentum"

    def __init__(self, ticker="SPY", lookback=126):  # ~6 months of trading days
        self.tickers, self.lookback = [ticker], lookback

    def generate_signals(self, prices):
        w = empty_targets(prices)
        ret = prices[self.tickers[0]].pct_change(self.lookback)
        for d in period_ends(prices.index, "M"):
            if pd.notna(ret[d]):
                w.loc[d] = float(ret[d] > 0)
        return w
