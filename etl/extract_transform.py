import pandas as pd
import os
import numpy as np

RAW_DIR = '/opt/airflow/data/raw/csv'
PROCESSED_DIR = '/opt/airflow/data/processed'

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def clean_patients(df):
    # Select columns for dim_patients
    dim_patients = df[['Id', 'FIRST', 'LAST', 'GENDER', 'RACE', 'ETHNICITY', 'MARITAL', 'BIRTHDATE', 'CITY', 'STATE', 'ZIP']].copy()
    dim_patients.rename(columns={
        'Id': 'patient_id',
        'FIRST': 'first_name',
        'LAST': 'last_name',
        'GENDER': 'gender',
        'RACE': 'race',
        'ETHNICITY': 'ethnicity',
        'MARITAL': 'marital_status',
        'BIRTHDATE': 'birth_date',
        'CITY': 'city',
        'STATE': 'state',
        'ZIP': 'zip'
    }, inplace=True)
    dim_patients['marital_status'].fillna('Unknown', inplace=True)
    dim_patients['zip'] = dim_patients['zip'].astype(str).str.replace(r'\.0', '', regex=True)
    # Risk score will be added later by ML model
    dim_patients['risk_score'] = np.nan
    return dim_patients

def clean_providers(df):
    dim_providers = df[['Id', 'NAME', 'SPECIALITY', 'ORGANIZATION', 'CITY', 'STATE']].copy()
    dim_providers.rename(columns={
        'Id': 'provider_id',
        'NAME': 'name',
        'SPECIALITY': 'specialty',
        'ORGANIZATION': 'organization_id',
        'CITY': 'city',
        'STATE': 'state'
    }, inplace=True)
    return dim_providers

def clean_codes(conditions_df, observations_df):
    # Extract unique codes from conditions and observations to build dim_clinical_codes
    cond_codes = conditions_df[['CODE', 'DESCRIPTION']].drop_duplicates().copy()
    cond_codes['code_type'] = 'SNOMED-CT' # Synthea mostly uses SNOMED
    
    obs_codes = observations_df[['CODE', 'DESCRIPTION']].drop_duplicates().copy()
    obs_codes['code_type'] = 'LOINC' # Synthea observations are LOINC
    
    dim_clinical_codes = pd.concat([cond_codes, obs_codes]).drop_duplicates(subset=['CODE'])
    dim_clinical_codes.rename(columns={
        'CODE': 'code',
        'DESCRIPTION': 'description'
    }, inplace=True)
    return dim_clinical_codes

def generate_date_dim(start_date, end_date):
    df = pd.DataFrame({'full_date': pd.date_range(start_date, end_date)})
    df['date_id'] = df['full_date'].dt.strftime('%Y%m%d').astype(int)
    df['year'] = df['full_date'].dt.year
    df['month'] = df['full_date'].dt.month
    df['day'] = df['full_date'].dt.day
    df['quarter'] = df['full_date'].dt.quarter
    df['is_weekend'] = df['full_date'].dt.weekday >= 5
    return df[['date_id', 'full_date', 'year', 'month', 'day', 'quarter', 'is_weekend']]

def get_date_id(series):
    return pd.to_datetime(series, errors='coerce').dt.strftime('%Y%m%d').fillna(19000101).astype(int)

def clean_encounters(df):
    fact_encounters = df[['Id', 'PATIENT', 'PROVIDER', 'START', 'STOP', 'ENCOUNTERCLASS', 'BASE_ENCOUNTER_COST', 'TOTAL_CLAIM_COST', 'REASONCODE']].copy()
    fact_encounters.rename(columns={
        'Id': 'encounter_id',
        'PATIENT': 'patient_id',
        'PROVIDER': 'provider_id',
        'ENCOUNTERCLASS': 'encounter_class',
        'BASE_ENCOUNTER_COST': 'base_cost',
        'TOTAL_CLAIM_COST': 'total_cost',
        'REASONCODE': 'reason_code'
    }, inplace=True)
    
    fact_encounters['start_date_id'] = get_date_id(fact_encounters['START'])
    fact_encounters['stop_date_id'] = get_date_id(fact_encounters['STOP'])
    fact_encounters.drop(columns=['START', 'STOP'], inplace=True)
    return fact_encounters

def clean_conditions(df):
    fact_conditions = df[['PATIENT', 'ENCOUNTER', 'START', 'CODE']].copy()
    fact_conditions.rename(columns={
        'PATIENT': 'patient_id',
        'ENCOUNTER': 'encounter_id',
        'CODE': 'condition_code'
    }, inplace=True)
    fact_conditions['start_date_id'] = get_date_id(fact_conditions['START'])
    fact_conditions.drop(columns=['START'], inplace=True)
    return fact_conditions

def clean_observations(df):
    fact_obs = df[['PATIENT', 'ENCOUNTER', 'DATE', 'CODE', 'VALUE', 'UNITS', 'TYPE']].copy()
    fact_obs.rename(columns={
        'PATIENT': 'patient_id',
        'ENCOUNTER': 'encounter_id',
        'CODE': 'observation_code',
        'UNITS': 'units'
    }, inplace=True)
    fact_obs['date_id'] = get_date_id(fact_obs['DATE'])
    
    # Split VALUE into numeric and text based on TYPE
    fact_obs['numeric_value'] = np.where(fact_obs['TYPE'] == 'numeric', pd.to_numeric(fact_obs['VALUE'], errors='coerce'), np.nan)
    fact_obs['text_value'] = np.where(fact_obs['TYPE'] == 'text', fact_obs['VALUE'], None)
    
    fact_obs.drop(columns=['DATE', 'VALUE', 'TYPE'], inplace=True)
    return fact_obs

def main():
    print("Extracting and Transforming Data...")
    ensure_dir(PROCESSED_DIR)
    
    patients = pd.read_csv(os.path.join(RAW_DIR, 'patients.csv'))
    providers = pd.read_csv(os.path.join(RAW_DIR, 'providers.csv'))
    encounters = pd.read_csv(os.path.join(RAW_DIR, 'encounters.csv'))
    conditions = pd.read_csv(os.path.join(RAW_DIR, 'conditions.csv'))
    observations = pd.read_csv(os.path.join(RAW_DIR, 'observations.csv'))
    
    dim_patients = clean_patients(patients)
    dim_providers = clean_providers(providers)
    dim_clinical_codes = clean_codes(conditions, observations)
    
    # Dim Date range from earliest event to latest
    min_date = pd.to_datetime(encounters['START']).min()
    max_date = pd.to_datetime(encounters['STOP']).max()
    if pd.isna(min_date): min_date = '2000-01-01'
    if pd.isna(max_date): max_date = '2030-12-31'
    dim_date = generate_date_dim(min_date, max_date)
    
    fact_encounters = clean_encounters(encounters)
    fact_conditions = clean_conditions(conditions)
    fact_observations = clean_observations(observations)
    
    # Save transformed to processed
    dim_patients.to_csv(os.path.join(PROCESSED_DIR, 'dim_patients.csv'), index=False)
    dim_providers.to_csv(os.path.join(PROCESSED_DIR, 'dim_providers.csv'), index=False)
    dim_clinical_codes.to_csv(os.path.join(PROCESSED_DIR, 'dim_clinical_codes.csv'), index=False)
    dim_date.to_csv(os.path.join(PROCESSED_DIR, 'dim_date.csv'), index=False)
    fact_encounters.to_csv(os.path.join(PROCESSED_DIR, 'fact_encounters.csv'), index=False)
    fact_conditions.to_csv(os.path.join(PROCESSED_DIR, 'fact_conditions.csv'), index=False)
    fact_observations.to_csv(os.path.join(PROCESSED_DIR, 'fact_observations.csv'), index=False)
    print("Transformation Complete. Transformed data saved to data/processed.")

if __name__ == "__main__":
    main()
