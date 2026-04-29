import pandas as pd
from sqlalchemy import create_engine
import os

PROCESSED_DIR = '/opt/airflow/data/processed'
# This connection string is for the Docker container. When running from outside docker, we use localhost.
# In Airflow, we use postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
# Locally, it's postgresql+psycopg2://airflow:airflow@localhost:5432/airflow
DB_URI = os.getenv('DB_URI', 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow')

def load_data():
    print(f"Connecting to Database: {DB_URI}")
    engine = create_engine(DB_URI)
    
    tables = [
        'dim_patients',
        'dim_providers',
        'dim_clinical_codes',
        'dim_date',
        'fact_encounters',
        'fact_conditions',
        'fact_observations'
    ]
    
    for table in tables:
        file_path = os.path.join(PROCESSED_DIR, f"{table}.csv")
        if not os.path.exists(file_path):
            print(f"File {file_path} not found. Skipping {table}.")
            continue
            
        print(f"Loading {table}...")
        df = pd.read_csv(file_path)
        
        # Load into Postgres. Using 'append' because we assume schema is managed by sql/schema.sql
        # But if we want idempotency without complex upserts, we can clear the table first.
        # Since this is a demo, we'll just replace or append. Let's append to existing schema.
        try:
            with engine.connect() as conn:
                conn.execute(f"TRUNCATE TABLE {table} CASCADE;")
                
            df.to_sql(table, engine, if_exists='append', index=False)
            print(f"Successfully loaded {len(df)} rows into {table}.")
        except Exception as e:
            print(f"Error loading {table}: {e}")

if __name__ == "__main__":
    load_data()
