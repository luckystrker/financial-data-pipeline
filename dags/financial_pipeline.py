"""
Financial Data Pipeline DAG.

Orchestrates: extract → load → dbt run
Schedule: daily at 09:00 UTC
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

EXTRACT_SCRIPT = "/opt/airflow/scripts/extract.py"
LOAD_SCRIPT = "/opt/airflow/scripts/load.py"
DBT_DIR = "/opt/airflow/dbt"


def _capture_extract_path(ti, **context):
    """Pull the file path from the extract task's last line and push to XCom."""
    output = ti.xcom_pull(task_ids="extract", key="return_value")
    # The extract script prints the output path as its last line
    lines = output.strip().split("\n")
    ti.xcom_push(key="extract_path", value=lines[-1])
    print(f"Extract path captured: {lines[-1]}")


with DAG(
    dag_id="financial_pipeline",
    description="Fetch stock data → ClickHouse → dbt transforms",
    default_args=DEFAULT_ARGS,
    schedule="0 9 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["financial", "pipeline"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"python {EXTRACT_SCRIPT}",
        do_xcom_push=True,
    )

    capture_path = PythonOperator(
        task_id="capture_extract_path",
        python_callable=_capture_extract_path,
    )

    load = BashOperator(
        task_id="load",
        bash_command=(
            "python {{ "
            "  ti.xcom_pull(task_ids='capture_extract_path', key='extract_path') "
            "}}"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir .",
    )

    extract >> capture_path >> load >> dbt_run >> dbt_test