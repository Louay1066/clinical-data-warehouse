import pandas as pd
import pickle
import os

PROCESSED_DIR = '/opt/airflow/data/processed'
MODEL_DIR = '/opt/airflow/ml/models'

def score_patients():
    print("Scoring patients...")
    
    with open(os.path.join(MODEL_DIR, 'risk_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
        
    patients = pd.read_csv(os.path.join(PROCESSED_DIR, 'dim_patients.csv'))
    encounters = pd.read_csv(os.path.join(PROCESSED_DIR, 'fact_encounters.csv'))
    
    # Feature 1: Total Cost
    cost_per_patient = encounters.groupby('patient_id')['total_cost'].sum().reset_index()
    # Feature 2: Number of Encounters
    count_per_patient = encounters.groupby('patient_id')['encounter_id'].count().reset_index()
    count_per_patient.rename(columns={'encounter_id': 'encounter_count'}, inplace=True)
    
    # Merge features
    features = pd.merge(patients[['patient_id', 'birth_date']], cost_per_patient, on='patient_id', how='left')
    features = pd.merge(features, count_per_patient, on='patient_id', how='left')
    
    features['total_cost'].fillna(0, inplace=True)
    features['encounter_count'].fillna(0, inplace=True)
    
    features['birth_date'] = pd.to_datetime(features['birth_date'], errors='coerce')
    features['age'] = (pd.Timestamp.now() - features['birth_date']).dt.days / 365.25
    features['age'].fillna(features['age'].mean(), inplace=True)
    
    X = features[['total_cost', 'encounter_count', 'age']]
    X_scaled = scaler.transform(X)
    
    # Predict probabilities
    risk_scores = model.predict_proba(X_scaled)[:, 1]
    
    # Update dim_patients
    patients['risk_score'] = risk_scores
    patients.to_csv(os.path.join(PROCESSED_DIR, 'dim_patients.csv'), index=False)
    
    print("Scoring complete. dim_patients.csv updated with risk_score.")

if __name__ == "__main__":
    score_patients()
