import numpy as np
import pandas as pd


def drawdown_series(values):
    return values / values.cummax() - 1


def compute_metrics(res, rf=0.03):
    v, r = res.portfolio_value, res.daily_returns.iloc[1:]
    n = len(r)
    total = v.iloc[-1] / v.iloc[0] - 1
    ann = (1 + total) ** (252 / n) - 1
    vol = r.std() * np.sqrt(252)
    return {
        "Total Return": total,
        "Annual Return": ann,
        "Volatility": vol,
        "Sharpe": (ann - rf) / vol if vol > 0 else np.nan,
        "Max Drawdown": drawdown_series(v).min(),
        "Trades": len(res.trades),
    }


def metrics_table(results, rf=0.03):
    return pd.DataFrame({n: compute_metrics(r, rf) for n, r in results.items()}).T


def monte_carlo(returns, n_sims=1000, horizon=252, initial=10_000, seed=0):
    """Bootstrap daily returns to see the spread of possible outcomes."""
    rng = np.random.default_rng(seed)
    draws = rng.choice(returns.values, size=(n_sims, horizon))
    return initial * np.cumprod(1 + draws, axis=1)
