from .base import Strategy, empty_targets


class BuyHold(Strategy):
    """Strategy A: invest everything on day 1, hold to the end."""
    def __init__(self, ticker="SPY", name="Buy & Hold"):
        self.tickers, self.name = [ticker], name

    def generate_signals(self, prices):
        w = empty_targets(prices)
        w.iloc[0] = 1.0
        return w
