from .base import Strategy, empty_targets


class MovingAverage(Strategy):
    """Strategy D: hold when price > N-day moving average, otherwise cash."""
    def __init__(self, ticker="SPY", window=200, name="Moving Avg"):
        self.tickers, self.window, self.name = [ticker], window, name

    def generate_signals(self, prices):
        t = self.tickers[0]
        p = prices[t]
        sma = p.rolling(self.window).mean()
        w = empty_targets(prices)
        ok = sma.notna()
        w.loc[ok, t] = (p[ok] > sma[ok]).astype(float)
        return w
