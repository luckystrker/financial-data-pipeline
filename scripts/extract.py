"""
Extract stock price data from Yahoo Finance.

Usage:
    python scripts/extract.py
"""
import json
import os
from datetime import datetime, timedelta

import yfinance as yf

TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
DAYS_BACK = 365 * 2  # 2 years of history


def extract_ticker(ticker: str) -> list[dict]:
    """Fetch historical data for a single ticker.

    Returns a list of row dicts ready for loading.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=f"{DAYS_BACK}d")

    rows = []
    for date_idx, row in df.iterrows():
        rows.append({
            "ticker": ticker,
            "date": date_idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
        })
    return rows


def main() -> None:
    all_rows = []
    for ticker in TICKERS:
        print(f"Extracting {ticker} …")
        rows = extract_ticker(ticker)
        all_rows.extend(rows)
        print(f"  → {len(rows)} rows")

    # Write to a timestamped JSON file for the loader
    output_path = f"/opt/airflow/scripts/extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w") as f:
        json.dump(all_rows, f)

    print(f"\nDone — {len(all_rows)} total rows written to {output_path}")
    print(output_path)  # last line = output path for the Airflow task to capture


if __name__ == "__main__":
    main()