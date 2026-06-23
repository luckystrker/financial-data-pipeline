CREATE DATABASE IF NOT EXISTS financial;

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
ORDER BY (ticker, date);