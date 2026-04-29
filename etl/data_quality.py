import pandas as pd
import os

PROCESSED_DIR = '/opt/airflow/data/processed'

def test_patients_quality():
    df = pd.read_csv(os.path.join(PROCESSED_DIR, 'dim_patients.csv'))
    
    # Check for future birth dates
    df['birth_date'] = pd.to_datetime(df['birth_date'])
    future_births = df[df['birth_date'] > pd.Timestamp.now()]
    if not future_births.empty:
        print(f"FAILED: {len(future_births)} patients have a birth date in the future.")
        return False
        
    # Check for missing primary keys
    if df['patient_id'].isnull().any():
        print("FAILED: Missing patient_id detected.")
        return False
        
    print("PASSED: dim_patients quality checks.")
    return True

def test_encounters_quality():
    df = pd.read_csv(os.path.join(PROCESSED_DIR, 'fact_encounters.csv'))
    
    # Check for negative costs
    if (df['base_cost'] < 0).any() or (df['total_cost'] < 0).any():
        print("FAILED: Negative costs detected in encounters.")
        return False
        
    print("PASSED: fact_encounters quality checks.")
    return True

def main():
    print("Running Data Quality Sanity Checks...")
    passed = True
    passed &= test_patients_quality()
    passed &= test_encounters_quality()
    
    if passed:
        print("All Data Quality checks passed successfully!")
    else:
        raise Exception("Data Quality checks failed. Pipeline aborted.")

if __name__ == "__main__":
    main()
