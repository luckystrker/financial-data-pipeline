"""
Streamlit dashboard for the Financial Data Pipeline.

Displays stock price data from ClickHouse marts.
"""
import os

import clickhouse_connect
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financial Data Dashboard",
    layout="wide",
)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")


@st.cache_resource
def get_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
    )


def query_df(sql: str) -> pd.DataFrame:
    client = get_client()
    result = client.query_df(sql)
    return result


# ── Sidebar ──────────────────────────────────────────────────────────
st.sidebar.title("Financial Data Pipeline")
st.sidebar.markdown("Built with **Airflow · dbt · ClickHouse · Streamlit**")
st.sidebar.markdown("---")

tickers = st.sidebar.multiselect(
    "Tickers",
    ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    default=["AAPL", "MSFT"],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data sourced from Yahoo Finance via yfinance. "
    "Refreshes daily at 09:00 UTC."
)

# ── Main ─────────────────────────────────────────────────────────────
st.title("Stock Market Dashboard")

try:
    # ── Price chart ────────────────────────────────────────────────
    st.subheader("Closing Prices")

    ticker_filter = ", ".join(f"'{t}'" for t in tickers)
    prices = query_df(f"""
        SELECT ticker, date, close
        FROM financial.mart_moving_averages
        WHERE ticker IN ({ticker_filter})
        ORDER BY date
    """)

    if not prices.empty:
        fig_prices = px.line(
            prices,
            x="date",
            y="close",
            color="ticker",
            title="Closing Price History",
            labels={"close": "Close ($)", "date": "Date"},
        )
        st.plotly_chart(fig_prices, use_container_width=True)
    else:
        st.info("No price data available. Run the pipeline first.")

    # ── Moving averages ────────────────────────────────────────────
    st.subheader("Moving Averages (7d & 30d)")

    ma_data = query_df(f"""
        SELECT ticker, date, close, ma_7d, ma_30d
        FROM financial.mart_moving_averages
        WHERE ticker IN ({ticker_filter})
        ORDER BY date
    """)

    if not ma_data.empty:
        selected = st.selectbox("Select ticker", tickers)
        ma_df = ma_data[ma_data["ticker"] == selected]

        fig_ma = px.line(
            ma_df,
            x="date",
            y=["close", "ma_7d", "ma_30d"],
            title=f"{selected} — Price & Moving Averages",
            labels={"value": "Price ($)", "date": "Date", "variable": "Series"},
        )
        st.plotly_chart(fig_ma, use_container_width=True)
    else:
        st.info("No moving-average data yet.")

    # ── Daily returns ──────────────────────────────────────────────
    st.subheader("Daily Returns (%)")

    returns = query_df(f"""
        SELECT ticker, date, daily_return_pct
        FROM financial.mart_daily_returns
        WHERE ticker IN ({ticker_filter})
        ORDER BY date
    """)

    if not returns.empty:
        fig_ret = px.line(
            returns,
            x="date",
            y="daily_return_pct",
            color="ticker",
            title="Daily Returns (%)",
            labels={"daily_return_pct": "Return (%)", "date": "Date"},
        )
        st.plotly_chart(fig_ret, use_container_width=True)
    else:
        st.info("No return data yet.")

    # ── Volatility ─────────────────────────────────────────────────
    st.subheader("Weekly Volatility")

    vol = query_df(f"""
        SELECT ticker, week_start, volatility_pct
        FROM financial.mart_volatility
        WHERE ticker IN ({ticker_filter})
        ORDER BY week_start DESC
        LIMIT 52
    """)

    if not vol.empty:
        fig_vol = px.bar(
            vol,
            x="week_start",
            y="volatility_pct",
            color="ticker",
            barmode="group",
            title="Weekly Volatility (Std Dev of Daily Returns)",
            labels={
                "volatility_pct": "Volatility (%)",
                "week_start": "Week Starting",
            },
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("No volatility data yet.")

    # ── Raw data table ─────────────────────────────────────────────
    with st.expander("View raw data"):
        raw = query_df(f"""
            SELECT ticker, date, open, high, low, close, volume
            FROM financial.stg_prices
            WHERE ticker IN ({ticker_filter})
            ORDER BY date DESC
            LIMIT 100
        """)
        st.dataframe(raw, use_container_width=True)

except Exception as e:
    st.error(f"Could not connect to ClickHouse: {e}")
    st.info(
        "Make sure the pipeline is running. "
        "Start with `docker compose up -d` then trigger the DAG."
    )