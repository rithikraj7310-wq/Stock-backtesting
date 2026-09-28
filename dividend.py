from .base import Strategy, equal_weight_targets


class Dividend(Strategy):
    """Strategy C: equal-weight dividend payers, rebalanced quarterly."""
    name = "Dividend"

    def __init__(self, tickers=("KO", "PG", "JNJ", "PEP")):
        self.tickers = list(tickers)

    def generate_signals(self, prices):
        return equal_weight_targets(prices, "Q")
