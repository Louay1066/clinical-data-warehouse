# Data Dictionary: Clinical Data Warehouse

## Dimension Tables

### `dim_patients`
Contains patient demographic data.
- **patient_id** (VARCHAR, PK): Unique identifier for the patient.
- **first_name** (VARCHAR): Patient's first name.
- **last_name** (VARCHAR): Patient's last name.
- **gender** (VARCHAR): Patient's gender (M, F).
- **race** (VARCHAR): Patient's race.
- **ethnicity** (VARCHAR): Patient's ethnicity.
- **marital_status** (VARCHAR): Patient's marital status (M, S, etc.).
- **birth_date** (DATE): Date of birth.
- **city** (VARCHAR): Patient's city of residence.
- **state** (VARCHAR): Patient's state of residence.
- **zip** (VARCHAR): Patient's zip code.
- **risk_score** (FLOAT): ML-derived probability (0.0 to 1.0) of 30-day hospital readmission based on age, number of encounters, and total historical cost.

### `dim_providers`
Contains provider/physician registry data.
- **provider_id** (VARCHAR, PK): Unique identifier for the provider.
- **name** (VARCHAR): Provider's name.
- **specialty** (VARCHAR): Provider's medical specialty.
- **organization_id** (VARCHAR): ID of the organization the provider belongs to.
- **city** (VARCHAR): Provider's city.
- **state** (VARCHAR): Provider's state.

### `dim_clinical_codes`
Centralized mapping for all diagnosis and observation codes.
- **code** (VARCHAR, PK): Unique clinical code (e.g., SNOMED, LOINC).
- **description** (TEXT): Textual description of the code (e.g., "Prediabetes").
- **code_type** (VARCHAR): The vocabulary the code belongs to (e.g., 'SNOMED-CT', 'LOINC').

### `dim_date`
Standard date dimension for analytical roll-ups.
- **date_id** (INT, PK): Date formatted as YYYYMMDD (e.g., 20231024).
- **full_date** (DATE): Standard date format.
- **year** (INT): Year.
- **month** (INT): Month of year (1-12).
- **day** (INT): Day of month (1-31).
- **quarter** (INT): Quarter (1-4).
- **is_weekend** (BOOLEAN): True if Saturday or Sunday.

## Fact Tables

### `fact_encounters`
Contains records of patient visits/encounters.
- **encounter_id** (VARCHAR, PK): Unique identifier for the encounter.
- **patient_id** (VARCHAR, FK): References `dim_patients`.
- **provider_id** (VARCHAR, FK): References `dim_providers`.
- **start_date_id** (INT, FK): References `dim_date` for encounter start.
- **stop_date_id** (INT, FK): References `dim_date` for encounter end.
- **encounter_class** (VARCHAR): Setting of care (e.g., ambulatory, emergency).
- **base_cost** (DECIMAL): Base cost of the encounter.
- **total_cost** (DECIMAL): Total cost including claims.
- **reason_code** (VARCHAR): Primary reason code for the visit.

### `fact_conditions`
Contains diagnosed patient conditions.
- **condition_id** (SERIAL, PK): Surrogate primary key.
- **patient_id** (VARCHAR, FK): References `dim_patients`.
- **encounter_id** (VARCHAR, FK): References `fact_encounters`.
- **start_date_id** (INT, FK): References `dim_date` for condition onset.
- **condition_code** (VARCHAR, FK): References `dim_clinical_codes`.

### `fact_observations`
Contains clinical observations (e.g., Lab tests, Vital signs).
- **observation_id** (SERIAL, PK): Surrogate primary key.
- **patient_id** (VARCHAR, FK): References `dim_patients`.
- **encounter_id** (VARCHAR, FK): References `fact_encounters`.
- **date_id** (INT, FK): References `dim_date` for observation date.
- **observation_code** (VARCHAR, FK): References `dim_clinical_codes`.
- **numeric_value** (FLOAT): Value of the observation if numeric (e.g., HbA1c %).
- **text_value** (VARCHAR): Value if text.
- **units** (VARCHAR): Unit of measurement (e.g., '%', 'mmHg').

## Views

### `vw_diabetes_registry`
A curated dataset filtering for patients with an active or historical diagnosis related to Diabetes. Used as the core dataset for the Power BI Dashboard.
Includes demographics, latest risk scores, age calculation, and diagnosis details.
