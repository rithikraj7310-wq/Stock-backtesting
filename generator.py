import pandas as pd

PCT = ["Total Return", "Annual Return", "Volatility", "Max Drawdown"]


def md_table(m):
    cols = ["Total Return", "Annual Return", "Volatility", "Sharpe", "Max Drawdown", "Trades"]
    lines = ["| Strategy | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for name, row in m.iterrows():
        cells = [f"{row[c]:.1%}" if c in PCT else (f"{row[c]:.2f}" if c == "Sharpe" else f"{int(row[c])}") for c in cols]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(m, params):
    base = "Buy & Hold"
    best, safest = m["Sharpe"].idxmax(), m["Max Drawdown"].idxmax()
    top_ret, busiest = m["Total Return"].idxmax(), m["Trades"].idxmax()
    beat = [n for n in m.index if n != base and m.loc[n, "Sharpe"] > m.loc[base, "Sharpe"]]
    summary = (
        f"Over {params['start']} to {params['end']}, **{best}** delivered the best risk-adjusted return "
        f"(Sharpe {m.loc[best, 'Sharpe']:.2f}) with a maximum drawdown of {m.loc[best, 'Max Drawdown']:.1%}, "
        f"versus {m.loc[base, 'Max Drawdown']:.1%} for Buy & Hold."
    )
    conclusion = (
        f"{', '.join(beat)} beat Buy & Hold on a risk-adjusted basis, though active strategies "
        "trade more and pay more in costs." if beat else
        "No strategy beat Buy & Hold on a risk-adjusted basis in this period; simple holding was hard to beat."
    )
    return f"""# Investment Strategy Analysis

## Executive Summary
{summary}

## Methodology
- **Data:** Daily prices from Yahoo Finance via `yfinance`; Adjusted Close is used so dividends are included.
- **Period:** {params['start']} to {params['end']}, starting with ${params['initial']:,.0f}.
- **Rules:** Buy & Hold (SPY); Momentum (SPY, monthly check, 6-month return > 0 = invested, else cash);
  Dividend (KO, PG, JNJ, PEP equal-weighted, rebalanced quarterly);
  Moving Average (SPY, invested while price > {params['ma_window']}-day average, checked daily).
- **Assumptions:** Signals use the prior day's data and trade at the next close. Transaction cost {params['cost']:.2%} of traded value.
  Cash earns 0%. Sharpe ratio uses a {params['rf']:.1%} risk-free rate and 252 trading days per year. No taxes.

## Results
{md_table(m)}

**Key observations**
- Highest total return: **{top_ret}** ({m.loc[top_ret, 'Total Return']:.1%}).
- Smallest maximum drawdown: **{safest}** ({m.loc[safest, 'Max Drawdown']:.1%}).
- Most trades: **{busiest}** ({int(m.loc[busiest, 'Trades'])}).

## Conclusion
{conclusion}

*Limitations: backtests use hindsight (the stock lists were picked knowing which companies survived and thrived), and past performance doesn't predict future results. This is a school project, not financial advice.*
"""
