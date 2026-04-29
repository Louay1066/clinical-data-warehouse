from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Python is available inside the airflow docker container
# The scripts are mapped via volumes to /opt/airflow/...

with DAG(
    'clinical_pipeline_dag',
    default_args=default_args,
    description='ETL and ML pipeline for Clinical Data Warehouse',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['clinical', 'etl', 'ml'],
) as dag:

    # Task 1: Extract & Transform
    extract_transform = BashOperator(
        task_id='extract_transform',
        bash_command='python /opt/airflow/etl/extract_transform.py',
    )

    # Task 2: Train Risk Model
    train_risk_model = BashOperator(
        task_id='train_risk_model',
        bash_command='python /opt/airflow/ml/train_risk_model.py',
    )

    # Task 3: Score Patients
    score_patients = BashOperator(
        task_id='score_patients',
        bash_command='python /opt/airflow/ml/score_patients.py',
    )

    # Task 4: Data Quality Checks
    data_quality_checks = BashOperator(
        task_id='data_quality_checks',
        bash_command='python /opt/airflow/etl/data_quality.py',
    )

    # Task 5: Load to PostgreSQL
    load_to_postgres = BashOperator(
        task_id='load_to_postgres',
        bash_command='python /opt/airflow/etl/load.py',
    )

    # Define dependencies
    extract_transform >> train_risk_model >> score_patients >> data_quality_checks >> load_to_postgres
