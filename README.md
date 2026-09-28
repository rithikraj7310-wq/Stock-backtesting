# Investment Strategy Backtester

Streamlit + Plotly app that downloads stock data (yfinance), backtests strategies, compares risk/return, and writes a short report.

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```

## Structure
- `data/loader.py` – downloads OHLCV data and caches CSVs
- `strategies/` – `Strategy` base class (`generate_signals`, `backtest`) + Buy & Hold, Momentum, Dividend, Moving Average, Equal Weight
- `metrics/performance.py` – total/annualized return, volatility, Sharpe, max drawdown, Monte Carlo
- `report/generator.py` – builds the markdown report
- `app.py` – the dashboard

## Add a strategy
Subclass `Strategy`, set `name` and `tickers`, and return a target-weights table from `generate_signals` (NaN row = no trade). Add it to `run_all` in `app.py`.
