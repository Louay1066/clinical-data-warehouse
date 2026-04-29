-- sql/schema.sql

-- Drop tables if they exist (for idempotency)
DROP TABLE IF EXISTS fact_conditions CASCADE;
DROP TABLE IF EXISTS fact_observations CASCADE;
DROP TABLE IF EXISTS fact_encounters CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_clinical_codes CASCADE;
DROP TABLE IF EXISTS dim_providers CASCADE;
DROP TABLE IF EXISTS dim_patients CASCADE;

-- Dimension Tables
CREATE TABLE dim_patients (
    patient_id VARCHAR(255) PRIMARY KEY,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    gender VARCHAR(50),
    race VARCHAR(100),
    ethnicity VARCHAR(100),
    marital_status VARCHAR(50),
    birth_date DATE,
    city VARCHAR(255),
    state VARCHAR(255),
    zip VARCHAR(50),
    risk_score FLOAT -- ML Readmission Risk Score
);

CREATE TABLE dim_providers (
    provider_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    specialty VARCHAR(255),
    organization_id VARCHAR(255),
    city VARCHAR(255),
    state VARCHAR(255)
);

CREATE TABLE dim_clinical_codes (
    code VARCHAR(255) PRIMARY KEY,
    description TEXT,
    code_type VARCHAR(50) -- e.g., 'SNOMED-CT', 'ICD-10', 'LOINC'
);

CREATE TABLE dim_date (
    date_id INT PRIMARY KEY, -- e.g. 20231024
    full_date DATE,
    year INT,
    month INT,
    day INT,
    quarter INT,
    is_weekend BOOLEAN
);

-- Fact Tables
CREATE TABLE fact_encounters (
    encounter_id VARCHAR(255) PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES dim_patients(patient_id),
    provider_id VARCHAR(255) REFERENCES dim_providers(provider_id),
    start_date_id INT REFERENCES dim_date(date_id),
    stop_date_id INT REFERENCES dim_date(date_id),
    encounter_class VARCHAR(100),
    base_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    reason_code VARCHAR(255)
);

CREATE TABLE fact_conditions (
    condition_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES dim_patients(patient_id),
    encounter_id VARCHAR(255) REFERENCES fact_encounters(encounter_id),
    start_date_id INT REFERENCES dim_date(date_id),
    condition_code VARCHAR(255) REFERENCES dim_clinical_codes(code)
);

CREATE TABLE fact_observations (
    observation_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES dim_patients(patient_id),
    encounter_id VARCHAR(255) REFERENCES fact_encounters(encounter_id),
    date_id INT REFERENCES dim_date(date_id),
    observation_code VARCHAR(255) REFERENCES dim_clinical_codes(code),
    numeric_value FLOAT,
    text_value VARCHAR(255),
    units VARCHAR(50)
);

-- Views
-- Phase 4: Diabetes Patient Registry View
CREATE OR REPLACE VIEW vw_diabetes_registry AS
SELECT DISTINCT
    p.patient_id,
    p.first_name,
    p.last_name,
    p.gender,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) AS age,
    p.city,
    p.state,
    p.risk_score,
    c_code.description AS diagnosis,
    fc.start_date_id
FROM dim_patients p
JOIN fact_conditions fc ON p.patient_id = fc.patient_id
JOIN dim_clinical_codes c_code ON fc.condition_code = c_code.code
WHERE c_code.description ILIKE '%diabetes%'
   OR c_code.code IN ('44054006', 'E08', 'E09', 'E10', 'E11', 'E13'); -- Common SNOMED/ICD-10 codes for Diabetes
