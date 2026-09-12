# NeuroScan AI - Alzheimer's Disease MRI Diagnosis Platform

NeuroScan AI is a web-based application for Alzheimer's disease MRI analysis. It allows a doctor to log in, register patients, upload MRI scans, run the trained VMamba model, view the prediction and confidence score, and check the patient's previous records and reports.

## Main Features

- Doctor login and logout
- Secure password-based authentication
- Patient registration and patient management
- Searchable patient list
- Individual patient details and MRI history
- MRI scan upload
- Alzheimer's disease classification using a PyTorch VMamba model
- Prediction confidence score
- Explainable AI (XAI) visualization for the prediction
- Diagnostic reports
- MySQL database integration
- Dashboard with patient and MRI information
- Health check API

## Technology Used

### Backend

- Python
- Flask
- PyTorch
- PyMySQL
- Werkzeug
- python-dotenv

### Machine Learning

- VMamba
- Explainable AI (XAI)
- Grad-CAM / heatmap visualization

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2 templates

### Database

- MySQL

## Project Structure

```text
Alzheimer_AI_Platform/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── verify_vmamba.py
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── auth.py
│   ├── patient_routes.py
│   ├── routes.py
│   └── utils.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── schema.sql
│   ├── seed.py
│   └── README.md
│
├── model/
│   ├── best_vmamba.pth
│   ├── inference.py
│   ├── vmamba.py
│   ├── xai.py
│   └── README.md
│
├── reports/
│
├── uploads/
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── dashboard.css
│   └── js/
│       ├── main.js
│       └── auth.js
│
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── patient_list.html
    ├── patient_register.html
    └── patient_detail.html
```

## Database

The application uses MySQL with the following main tables:

- `doctors`
- `patients`
- `mri_scans`
- `predictions`
- `reports`

The database uses primary keys, foreign keys, and indexes. Database queries are parameterized to reduce the risk of SQL injection.

## Setup

### 1. Install Python

Make sure Python is installed on your system.

### 2. Install the Required Packages

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Configure the Environment

Create a `.env` file from `.env.example`.

Example:

```env
SECRET_KEY=your_secret_key

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=alzheimer_db
```

Do not upload the `.env` file to GitHub because it contains local configuration and credentials.

### 4. Start MySQL

Make sure MySQL Server, XAMPP, or MariaDB is running on port `3306`, or update the database settings in `.env`.

### 5. Create and Seed the Database

Run:

```bash
python -m database.seed
```

This creates the database and required tables and adds the demo doctor account and sample records.

### 6. Run the Application

Run:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Demo Login

The database seed creates a demo doctor account:

```text
Email: dr.jenkins@hospital.org
Password: password123
```

These credentials are only for local/demo testing.

## Application Flow

1. Open the application and go to the login page.
2. Log in using the doctor account.
3. Open the dashboard.
4. Register a new patient or select an existing patient.
5. Upload an MRI scan.
6. Run the MRI analysis.
7. The VMamba model generates the prediction and confidence score.
8. The XAI module generates a visualization to help show the important areas used by the model.
9. View the assessment and patient history.
10. Check the available reports.
11. Logout when finished.

## Patient Management

The patient section provides:

- New patient registration
- Patient search
- Patient list
- Patient profile
- MRI scan history
- Previous predictions
- Reports

## MRI Analysis

The MRI analysis uses the trained model stored in:

```text
model/best_vmamba.pth
```

The model is loaded through:

```text
model/inference.py
```

The VMamba implementation is in:

```text
model/vmamba.py
```

The XAI functionality is handled through:

```text
model/xai.py
```

## Authentication

Doctor authentication is handled using Flask sessions.

Passwords are stored using Werkzeug password hashing instead of storing plain-text passwords in the database.

Protected pages require the doctor to be logged in.

## API

The Flask application also includes a health check API that can be used to check whether the application is running correctly.

## Important Notes

- The `.env` file is kept local and is not included in the GitHub repository.
- Uploaded MRI scans are stored locally and are not included in the repository.
- The trained model file is included in the `model` folder.
- Make sure MySQL is running before starting the application.
- The project is intended for educational, research, and clinical decision-support purposes. It should not be used as a replacement for a qualified medical professional's diagnosis.
