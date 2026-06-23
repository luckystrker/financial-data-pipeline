# Public Financial Data Pipeline

Batch pipeline for loading, transforming, and visualizing public financial data.

**Stack:** Python · Apache Airflow · dbt · ClickHouse · Docker · Streamlit

---

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Yahoo       │    │  Airflow     │    │  ClickHouse  │    │  Streamlit   │
│  Finance API │───▶│  Scheduler   │───▶│  (OLAP DB)   │───▶│  Dashboard   │
│  (yfinance)  │    │              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                    ▲
                           ▼                    │
                    ┌──────────────┐    ┌──────────────┐
                    │  Python      │    │  dbt         │
                    │  Extract +   │───▶│  Transform   │
                    │  Load        │    │  (4 models)   │
                    └──────────────┘    └──────────────┘
```

### Data Flow

1. **Extract** — Python script (`scripts/extract.py`) pulls Yahoo Finance data via `yfinance` (free, no API key required). Fetches historical prices for AAPL, GOOGL, MSFT, AMZN, TSLA.
2. **Load** — `scripts/load.py` inserts raw data into ClickHouse, table `financial.raw_prices` (`ReplacingMergeTree` engine).
3. **Transform** — dbt runs 4 models:
   - `stg_prices` — raw data cleaning
   - `mart_daily_returns` — daily return in %
   - `mart_volatility` — weekly volatility
   - `mart_moving_averages` — moving averages (7 and 30 days)
4. **Dashboard** — Streamlit dashboard with price charts, moving averages, returns, and volatility.

### Orchestration

Airflow DAG (`financial_pipeline`) runs daily at 09:00 UTC:

```
extract → capture_path → load → dbt_run → dbt_test
```

### dbt Tests

- `not_null` on ticker, date, close
- `unique` composite key (ticker + date)
- Tests run automatically after each `dbt run`

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (>= 2.x)

### Launch

```bash
# 1. Clone
git clone https://github.com/luckystrker/financial-data-pipeline.git
cd financial-data-pipeline

# 2. Start services
docker compose up -d

# 3. Wait 30-60 sec for ClickHouse and Airflow to initialize
docker compose logs -f
# Wait for "Listening at: http://0.0.0.0:8080" from airflow
```

### Run the Pipeline

```bash
# Airflow UI: http://localhost:8080
# Login: admin / Password: admin
# Enable DAG "financial_pipeline" → Trigger DAG

# Or manually:
docker compose exec airflow bash -c "python /opt/airflow/scripts/extract.py"
docker compose exec airflow bash -c "python /opt/airflow/scripts/load.py /opt/airflow/scripts/extract_<timestamp>.json"
docker compose exec airflow bash -c "cd /opt/airflow/dbt && dbt run --profiles-dir ."
docker compose exec airflow bash -c "cd /opt/airflow/dbt && dbt test --profiles-dir ."
```

### Dashboard

Open **[http://localhost:8501](http://localhost:8501)**

### Shutdown

```bash
docker compose down -v   # -v removes ClickHouse data volumes
```

---

## Project Structure

```
financial-data-pipeline/
├── docker-compose.yml          # service orchestration
├── Dockerfile                  # Airflow + dbt + dependencies
├── .env.example                # environment variable template
│
├── dags/
│   └── financial_pipeline.py   # Airflow DAG
│
├── scripts/
│   ├── extract.py              # Yahoo Finance data extraction
│   ├── load.py                 # ClickHouse data loading
│   └── init-clickhouse.sql     # database schema initialization
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml            # ClickHouse connection config
│   └── models/
│       ├── staging/
│       │   └── stg_prices.sql
│       └── marts/
│           ├── mart_daily_returns.sql
│           ├── mart_volatility.sql
│           └── mart_moving_averages.sql
│
├── dashboard/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py                  # Streamlit UI
│
└── README.md
```


## License

MIT
