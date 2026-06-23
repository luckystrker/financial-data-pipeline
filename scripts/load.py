"""
Load extracted JSON data into ClickHouse raw_prices table.

Usage:
    python scripts/load.py <extract_file_path>
"""
import json
import os
import sys

import clickhouse_connect


def get_client() -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )


def load_file(file_path: str) -> int:
    """Insert rows from a JSON extract file into raw_prices.

    Uses INSERT…VALUES with a single batch per ticker.
    Returns the number of rows inserted.
    """
    with open(file_path) as f:
        rows = json.load(f)

    if not rows:
        print("No rows to load.")
        return 0

    client = get_client()

    # Ensure the table exists (idempotent)
    client.command("""
        CREATE TABLE IF NOT EXISTS financial.raw_prices (
            ticker        String,
            date          Date,
            open          Float64,
            high          Float64,
            low           Float64,
            close         Float64,
            volume        UInt64,
            ingested_at   DateTime DEFAULT now()
        ) ENGINE = ReplacingMergeTree()
        ORDER BY (ticker, date)
    """)

    column_names = ["ticker", "date", "open", "high", "low", "close", "volume"]
    data = [[r[col] for col in column_names] for r in rows]

    client.insert(
        table="financial.raw_prices",
        column_names=column_names,
        data=data,
    )

    row_count = len(rows)
    print(f"Loaded {row_count} rows into financial.raw_prices")
    return row_count


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/load.py <extract_file_path>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    load_file(file_path)


if __name__ == "__main__":
    main()