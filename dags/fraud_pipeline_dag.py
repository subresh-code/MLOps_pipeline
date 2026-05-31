"""Lightweight Airflow orchestration DAG for the MLOps pipeline.

This DAG runs the four core pipeline stages sequentially as BashOperator tasks.
It is designed as optional coursework evidence for Airflow orchestration.
The primary reproducible pipeline remains driven via the Makefile.
"""

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

default_args = {
    "owner": "subresh",
    "retries": 1,
}

with DAG(
    dag_id="fraud_detection_mlops_pipeline",
    default_args=default_args,
    description=(
        "Sequential MLOps pipeline for IEEE-CIS Fraud Detection: "
        "data ingestion, training, evaluation, drift monitoring"
    ),
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 1, 1),
    tags=["mlops", "fraud-detection"],
) as dag:

    ingest_data = BashOperator(
        task_id="ingest_data",
        bash_command="PYTHONPATH={} python -m src.data_processing".format(
            PROJECT_ROOT
        ),
        cwd=PROJECT_ROOT,
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command="PYTHONPATH={} python -m src.train".format(PROJECT_ROOT),
        cwd=PROJECT_ROOT,
    )

    evaluate_model = BashOperator(
        task_id="evaluate_model",
        bash_command="PYTHONPATH={} python -m src.evaluate".format(PROJECT_ROOT),
        cwd=PROJECT_ROOT,
    )

    monitor_drift = BashOperator(
        task_id="monitor_drift",
        bash_command="PYTHONPATH={} python -m src.monitor".format(PROJECT_ROOT),
        cwd=PROJECT_ROOT,
    )

    ingest_data >> train_model >> evaluate_model >> monitor_drift
