# Database Area (MySQL & ORM Integration)

This directory is reserved for future database models, ORM configurations (e.g. SQLAlchemy), and migration scripts.

## Planned Schema Architecture

1. **`users` Table**
   - `id` (INT, Primary Key)
   - `doctor_name` (VARCHAR)
   - `email` (VARCHAR, Unique)
   - `password_hash` (VARCHAR)
   - `hospital_department` (VARCHAR)
   - `created_at` (TIMESTAMP)

2. **`patients` Table**
   - `id` (INT, Primary Key)
   - `patient_code` (VARCHAR, Unique - e.g., PAT-9082)
   - `full_name` (VARCHAR)
   - `age` (INT)
   - `gender` (VARCHAR)
   - `medical_history` (TEXT)

3. **`mri_scans` Table**
   - `id` (INT, Primary Key)
   - `patient_id` (INT, Foreign Key -> `patients.id`)
   - `file_path` (VARCHAR)
   - `upload_date` (TIMESTAMP)

4. **`predictions` Table**
   - `id` (INT, Primary Key)
   - `mri_scan_id` (INT, Foreign Key -> `mri_scans.id`)
   - `predicted_class` (ENUM: CN, MCI, AD)
   - `confidence_score` (FLOAT)
   - `report_file_path` (VARCHAR)
   - `created_at` (TIMESTAMP)
