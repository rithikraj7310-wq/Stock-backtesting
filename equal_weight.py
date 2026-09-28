from .base import Strategy, equal_weight_targets


class EqualWeight(Strategy):
    """Strategy E (optional): equal-weight big tech, rebalanced monthly."""
    name = "Equal Weight"

    def __init__(self, tickers=("AAPL", "MSFT", "GOOGL", "AMZN", "NVDA")):
        self.tickers = list(tickers)

    def generate_signals(self, prices):
        return equal_weight_targets(prices, "M")
