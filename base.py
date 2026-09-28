from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    name: str
    portfolio_value: pd.Series
    daily_returns: pd.Series
    trades: pd.DataFrame
    weights: pd.DataFrame

    def trim(self, start, initial):
        """Cut off the warm-up period and rebase the portfolio to `initial`."""
        s = pd.Timestamp(start)
        v = self.portfolio_value.loc[s:]
        scale = initial / v.iloc[0]
        v = v * scale
        tr = self.trades[self.trades["date"] >= s].copy().reset_index(drop=True)
        tr["value"] = tr["value"] * scale
        return BacktestResult(self.name, v, v.pct_change().fillna(0), tr, self.weights.loc[s:])


def period_ends(index, freq):
    """Last trading day of each month ('M') or quarter ('Q')."""
    s = pd.Series(index, index=index)
    return s.groupby(index.to_period(freq)).last().values


def empty_targets(prices):
    """Target-weight table. NaN row = no rebalance that day."""
    return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)


def equal_weight_targets(prices, freq):
    w = empty_targets(prices)
    n = len(prices.columns)
    w.iloc[0] = 1 / n
    for d in period_ends(prices.index, freq):
        w.loc[d] = 1 / n
    return w


class Strategy:
    name = "Strategy"
    tickers = []

    def generate_signals(self, prices):
        """Return target weights per date (NaN row = hold, no trade)."""
        raise NotImplementedError

    def backtest(self, prices, initial=10_000, cost=0.001):
        # Signals use data up to day t-1 and are executed at day t's close (no look-ahead).
        targets = self.generate_signals(prices).shift(1)
        cols = list(prices.columns)
        shares = pd.Series(0.0, index=cols)
        cash = float(initial)
        vals, wts, trades = [], [], []
        for dt, px in prices.iterrows():
            total = cash + (shares * px).sum()
            w = targets.loc[dt]
            if not w.isna().all():
                w = w.fillna(0.0)
                fee = (w * total - shares * px).abs().sum() * cost
                total -= fee
                new_val = w * total
                for t in cols:
                    d = new_val[t] - shares[t] * px[t]
                    if abs(d) > 1:
                        trades.append((dt, t, "BUY" if d > 0 else "SELL", abs(d), px[t]))
                shares = new_val / px
                cash = total - new_val.sum()
            vals.append(total)
            wts.append(pd.concat([shares * px, pd.Series({"CASH": cash})]) / total)
        pv = pd.Series(vals, index=prices.index, name=self.name)
        return BacktestResult(
            self.name, pv, pv.pct_change().fillna(0),
            pd.DataFrame(trades, columns=["date", "ticker", "action", "value", "price"]),
            pd.DataFrame(wts, index=prices.index),
        )
