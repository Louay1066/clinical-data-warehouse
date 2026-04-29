import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os

PROCESSED_DIR = '/opt/airflow/data/processed'
MODEL_DIR = '/opt/airflow/ml/models'

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def train_model():
    print("Training Readmission Risk Model...")
    ensure_dir(MODEL_DIR)
    
    # We will build a simple feature set for patients based on their encounters
    patients = pd.read_csv(os.path.join(PROCESSED_DIR, 'dim_patients.csv'))
    encounters = pd.read_csv(os.path.join(PROCESSED_DIR, 'fact_encounters.csv'))
    
    # Feature 1: Total Cost
    cost_per_patient = encounters.groupby('patient_id')['total_cost'].sum().reset_index()
    
    # Feature 2: Number of Encounters
    count_per_patient = encounters.groupby('patient_id')['encounter_id'].count().reset_index()
    count_per_patient.rename(columns={'encounter_id': 'encounter_count'}, inplace=True)
    
    # Merge
    features = pd.merge(patients[['patient_id', 'birth_date']], cost_per_patient, on='patient_id', how='left')
    features = pd.merge(features, count_per_patient, on='patient_id', how='left')
    
    features['total_cost'].fillna(0, inplace=True)
    features['encounter_count'].fillna(0, inplace=True)
    
    # Feature 3: Age
    features['birth_date'] = pd.to_datetime(features['birth_date'], errors='coerce')
    features['age'] = (pd.Timestamp.now() - features['birth_date']).dt.days / 365.25
    features['age'].fillna(features['age'].mean(), inplace=True)
    
    X = features[['total_cost', 'encounter_count', 'age']]
    
    # Mock target variable: "Readmission within 30 days" (Randomized for this demo based on features to have some correlation)
    np.random.seed(42)
    # Higher age, cost, and encounters increases risk probability
    risk_prob = 1 / (1 + np.exp(-(X['age']*0.05 + X['encounter_count']*0.1 + X['total_cost']*0.0001 - 5)))
    y = np.random.binomial(1, risk_prob)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression()
    model.fit(X_scaled, y)
    
    # Save model and scaler
    with open(os.path.join(MODEL_DIR, 'risk_model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
        
    print("Model training complete and saved.")

if __name__ == "__main__":
    train_model()
