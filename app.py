import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data.loader import load_prices
from strategies import BuyHold, Momentum, Dividend, MovingAverage, EqualWeight
from metrics.performance import metrics_table, compute_metrics, drawdown_series, monte_carlo
from report.generator import build_report

st.set_page_config(page_title="Strategy Backtester", page_icon="📈", layout="wide")
st.title("📈 Investment Strategy Backtester")
st.caption("Downloads real market data, simulates strategies, and compares risk and return.")

with st.sidebar:
    st.header("Settings")
    start = str(st.date_input("Start date", pd.Timestamp("2015-01-01")))
    end = str(st.date_input("End date", pd.Timestamp("2025-01-01")))
    initial = st.number_input("Initial investment ($)", 1000, 1_000_000, 10_000, step=1000)
    cost = st.slider("Transaction cost (% of trade)", 0.0, 1.0, 0.1, 0.05) / 100
    rf = st.slider("Risk-free rate (%)", 0.0, 6.0, 3.0, 0.25) / 100
    ma_window = st.slider("Moving average window (days)", 20, 250, 200, 10)
    use_ew = st.checkbox("Include Equal Weight (Strategy E)", True)
    use_qqq = st.checkbox("Include QQQ benchmark", False)


def run(strategy, start, end, initial, cost):
    # load 2 extra years so indicators (6-mo momentum, 200-day MA) are ready on day 1
    warm = (pd.Timestamp(start) - pd.DateOffset(years=2)).strftime("%Y-%m-%d")
    prices = load_prices(strategy.tickers, warm, end)
    return strategy.backtest(prices, initial, cost).trim(start, initial)


@st.cache_data(show_spinner="Downloading data and running backtests…")
def run_all(start, end, initial, cost, ma_window, use_ew, use_qqq):
    strats = [BuyHold(), Momentum(), Dividend(), MovingAverage(window=ma_window)]
    if use_ew:
        strats.append(EqualWeight())
    if use_qqq:
        strats.append(BuyHold("QQQ", "QQQ Benchmark"))
    return {s.name: run(s, start, end, initial, cost) for s in strats}


@st.cache_data(show_spinner="Testing moving-average windows…")
def ma_sweep(start, end, initial, cost, rf):
    out = {}
    for w in (50, 100, 200):
        r = run(MovingAverage(window=w, name=f"{w}-day MA"), start, end, initial, cost)
        out[r.name] = compute_metrics(r, rf)
    return pd.DataFrame(out).T


try:
    results = run_all(start, end, initial, cost, ma_window, use_ew, use_qqq)
except Exception as e:
    st.error(f"Couldn't load data: {e}. Check your internet connection and date range.")
    st.stop()

m = metrics_table(results, rf)
FMT = {"Total Return": "{:.1%}", "Annual Return": "{:.1%}", "Volatility": "{:.1%}",
       "Sharpe": "{:.2f}", "Max Drawdown": "{:.1%}", "Trades": "{:.0f}"}

tabs = st.tabs(["Overview", "Strategy detail", "Drawdowns", "MA optimization", "Monte Carlo", "Report"])

with tabs[0]:
    growth = pd.DataFrame({n: r.portfolio_value for n, r in results.items()})
    st.plotly_chart(px.line(growth, title=f"Growth of ${initial:,.0f}", labels={"value": "Portfolio value ($)", "index": "Date", "variable": "Strategy"}), use_container_width=True)
    st.subheader("Strategy comparison")
    st.dataframe(m.style.format(FMT), use_container_width=True)

with tabs[1]:
    pick = st.selectbox("Strategy", list(results))
    r, row = results[pick], m.loc[pick]
    c = st.columns(5)
    c[0].metric("Total return", f"{row['Total Return']:.1%}")
    c[1].metric("Annual return", f"{row['Annual Return']:.1%}")
    c[2].metric("Volatility", f"{row['Volatility']:.1%}")
    c[3].metric("Sharpe", f"{row['Sharpe']:.2f}")
    c[4].metric("Max drawdown", f"{row['Max Drawdown']:.1%}")
    dd = drawdown_series(r.portfolio_value)
    st.plotly_chart(px.area(dd, title=f"{pick}: drawdown from peak", labels={"value": "Drawdown", "index": "Date"}), use_container_width=True)
    left, right = st.columns(2)
    cur = r.weights.iloc[-1]
    cur = cur[cur > 0.0001]
    left.plotly_chart(px.pie(values=cur.values, names=cur.index, title="Current holdings"), use_container_width=True)
    right.plotly_chart(px.area(r.weights, title="Weights over time", labels={"value": "Weight", "index": "Date", "variable": ""}), use_container_width=True)
    with st.expander(f"Trade log ({len(r.trades)} trades)"):
        st.dataframe(r.trades, use_container_width=True)

with tabs[2]:
    dds = pd.DataFrame({n: drawdown_series(r.portfolio_value) for n, r in results.items()})
    st.plotly_chart(px.line(dds, title="Drawdown from peak, all strategies", labels={"value": "Drawdown", "index": "Date", "variable": "Strategy"}), use_container_width=True)

with tabs[3]:
    st.write("Same rule, different moving-average windows (on SPY):")
    st.dataframe(ma_sweep(start, end, initial, cost, rf).style.format(FMT), use_container_width=True)

with tabs[4]:
    pick_mc = st.selectbox("Strategy to simulate", list(results), key="mc")
    years = st.slider("Horizon (years)", 1, 10, 3)
    sims = monte_carlo(results[pick_mc].daily_returns.iloc[1:], 1000, 252 * years, initial)
    x = np.arange(sims.shape[1])
    fig = go.Figure()
    for q, name in [(5, "5th pct"), (50, "Median"), (95, "95th pct")]:
        fig.add_scatter(x=x, y=np.percentile(sims, q, axis=0), name=name)
    fig.update_layout(title="Bootstrapped outcomes (1,000 simulations)", xaxis_title="Trading days", yaxis_title="Portfolio value ($)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Chance of ending below your starting ${initial:,.0f}: {(sims[:, -1] < initial).mean():.0%}")

with tabs[5]:
    report = build_report(m, dict(start=start, end=end, initial=initial, cost=cost, rf=rf, ma_window=ma_window))
    st.markdown(report)
    st.download_button("Download report (.md)", report, "investment_report.md", "text/markdown")
