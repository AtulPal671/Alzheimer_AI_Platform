Redesign the current NeuroScan AI clinical dashboard UI again, but ONLY the frontend/UI layer. Do NOT change, remove, or break any existing Flask routes, MySQL queries, database schema, authentication, MRI upload logic, prediction logic, patient management, reports, or backend functionality.

The current UI is functional, but it still looks like a generic admin dashboard and feels visually heavy. I want a polished, modern, minimalistic medical application that a doctor can understand and use immediately without any learning curve.

DESIGN GOAL:
Create a premium, calm, trustworthy clinical workstation similar to modern medical software. It should feel professional, clean, attractive, spacious and extremely easy to use.

CORE UX PRINCIPLE:
Prioritize the doctor's workflow over displaying lots of statistics.

The most important actions should be:
1. Start a New MRI Analysis
2. Select/Register a Patient
3. Review Recent Analyses
4. Open Reports

VISUAL DIRECTION:
- Use a clean medical aesthetic.
- Prefer a light/very-light neutral background with white cards and subtle blue/teal accents, OR an extremely refined dark theme if the existing application architecture strongly depends on it.
- Avoid the current heavy dark-blue dashboard appearance.
- Use lots of whitespace.
- Use subtle borders and very soft shadows.
- Avoid excessive glowing effects, gradients, colorful boxes, and decorative elements.
- Use one primary accent color consistently.
- Use a highly readable modern font.
- Keep typography hierarchy very clear.
- Rounded corners should be subtle and consistent, not excessive.
- Make the interface feel premium rather than flashy.

HEADER:
Simplify the top navigation.

Keep:
- NeuroScan AI logo/name
- Dashboard
- Patients
- Reports
- Doctor profile
- Logout

Do not make the header visually dominant.

DASHBOARD HERO:
Instead of immediately showing four large statistic cards, create a clean welcome section:

"Good morning, Dr. Sarah Jenkins"
"Review your patients and MRI analyses from one place."

Then place the primary action:
"+ New MRI Analysis"

And a secondary action:
"Register Patient"

The primary MRI action should be visually obvious.

STATISTICS:
Reduce the visual weight of statistics.

Keep useful information such as:
- Active Patients
- High Risk Cases
- Pending Reviews
- MRI Analyses

But make them compact and subtle, preferably as a single clean summary row rather than four huge dashboard cards.

MAIN WORKFLOW:
Make "New MRI Analysis" the central workflow.

Create a clean upload/analysis panel containing:

1. Select Patient
2. Upload MRI Scan
3. Analyze MRI

The interface should visually communicate the workflow:
Patient → MRI Scan → Analysis

The upload area should be simple and intuitive.

Use clear language such as:
"Upload MRI Scan"
"Drag and drop your MRI file here"
"Browse Files"

Do not overwhelm the doctor with technical terminology.

RECENT ANALYSES:
Keep the recent patient analyses section, but simplify the table considerably.

Columns should preferably be:
Patient
Age / Gender
Date
Result
Confidence
Action

Avoid unnecessary technical information.

Use subtle status badges for:
- Alzheimer's Disease
- Mild Cognitive Impairment
- Cognitively Normal
- Pending Review

Make patient names easy to scan.

The "Review Assessment" button should be compact and clear.

PATIENT SECTION:
Make "Patients" feel like a proper patient-management area rather than another dashboard table.

Provide:
- Search patient
- Patient list
- Patient details
- Recent MRI analysis
- Reports

Keep it extremely clean.

REPORTS:
Make the Reports section visually simple and professional.
Doctors should be able to quickly find:
- Patient
- Diagnosis
- Date
- Confidence
- View Report

IMPORTANT UX RULES:
- Do not add unnecessary widgets.
- Do not add charts unless they provide meaningful clinical value.
- Do not add decorative analytics.
- Do not create huge empty sections.
- Do not use excessive icons.
- Do not use multiple competing accent colors.
- Do not make every element look like a card.
- Do not make the interface feel like a SaaS analytics dashboard.
- Keep the number of visible decisions/actions low.
- Make buttons descriptive rather than icon-only.
- Maintain strong accessibility and readability.
- Make the application responsive.

MEDICAL UX:
This is a clinical decision-support interface, so the UI must communicate:
calmness, trust, clarity, accuracy and professionalism.

The doctor should be able to understand the page in approximately 5 seconds.

IMPORTANT:
Preserve all existing functionality and backend behavior.
Do not rewrite working backend code.
Do not modify MySQL schema.
Do not modify authentication.
Do not modify prediction/model logic.
Do not remove existing routes.
Only refactor frontend templates, CSS and frontend JavaScript where necessary.

Before making changes, inspect the existing templates and CSS and reuse existing components where appropriate.

After implementation:
1. Run the application.
2. Verify every existing dashboard action still works.
3. Verify patient registration still works.
4. Verify patient list still works.
5. Verify MRI upload still works.
6. Verify reports still work.
7. Verify logout still works.
8. Check for frontend console errors.
9. Check for Python/Flask errors.
10. Ensure there are no broken routes.

The final result should look like a real modern clinical application, not a generic admin dashboard.Redesign the current NeuroScan AI clinical dashboard UI again, but ONLY the frontend/UI layer. Do NOT change, remove, or break any existing Flask routes, MySQL queries, database schema, authentication, MRI upload logic, prediction logic, patient management, reports, or backend functionality.

The current UI is functional, but it still looks like a generic admin dashboard and feels visually heavy. I want a polished, modern, minimalistic medical application that a doctor can understand and use immediately without any learning curve.

DESIGN GOAL:
Create a premium, calm, trustworthy clinical workstation similar to modern medical software. It should feel professional, clean, attractive, spacious and extremely easy to use.

CORE UX PRINCIPLE:
Prioritize the doctor's workflow over displaying lots of statistics.

The most important actions should be:
1. Start a New MRI Analysis
2. Select/Register a Patient
3. Review Recent Analyses
4. Open Reports

VISUAL DIRECTION:
- Use a clean medical aesthetic.
- Prefer a light/very-light neutral background with white cards and subtle blue/teal accents, OR an extremely refined dark theme if the existing application architecture strongly depends on it.
- Avoid the current heavy dark-blue dashboard appearance.
- Use lots of whitespace.
- Use subtle borders and very soft shadows.
- Avoid excessive glowing effects, gradients, colorful boxes, and decorative elements.
- Use one primary accent color consistently.
- Use a highly readable modern font.
- Keep typography hierarchy very clear.
- Rounded corners should be subtle and consistent, not excessive.
- Make the interface feel premium rather than flashy.

HEADER:
Simplify the top navigation.

Keep:
- NeuroScan AI logo/name
- Dashboard
- Patients
- Reports
- Doctor profile
- Logout

Do not make the header visually dominant.

DASHBOARD HERO:
Instead of immediately showing four large statistic cards, create a clean welcome section:

"Good morning, Dr. Sarah Jenkins"
"Review your patients and MRI analyses from one place."

Then place the primary action:
"+ New MRI Analysis"

And a secondary action:
"Register Patient"

The primary MRI action should be visually obvious.

STATISTICS:
Reduce the visual weight of statistics.

Keep useful information such as:
- Active Patients
- High Risk Cases
- Pending Reviews
- MRI Analyses

But make them compact and subtle, preferably as a single clean summary row rather than four huge dashboard cards.

MAIN WORKFLOW:
Make "New MRI Analysis" the central workflow.

Create a clean upload/analysis panel containing:

1. Select Patient
2. Upload MRI Scan
3. Analyze MRI

The interface should visually communicate the workflow:
Patient → MRI Scan → Analysis

The upload area should be simple and intuitive.

Use clear language such as:
"Upload MRI Scan"
"Drag and drop your MRI file here"
"Browse Files"

Do not overwhelm the doctor with technical terminology.

RECENT ANALYSES:
Keep the recent patient analyses section, but simplify the table considerably.

Columns should preferably be:
Patient
Age / Gender
Date
Result
Confidence
Action

Avoid unnecessary technical information.

Use subtle status badges for:
- Alzheimer's Disease
- Mild Cognitive Impairment
- Cognitively Normal
- Pending Review

Make patient names easy to scan.

The "Review Assessment" button should be compact and clear.

PATIENT SECTION:
Make "Patients" feel like a proper patient-management area rather than another dashboard table.

Provide:
- Search patient
- Patient list
- Patient details
- Recent MRI analysis
- Reports

Keep it extremely clean.

REPORTS:
Make the Reports section visually simple and professional.
Doctors should be able to quickly find:
- Patient
- Diagnosis
- Date
- Confidence
- View Report

IMPORTANT UX RULES:
- Do not add unnecessary widgets.
- Do not add charts unless they provide meaningful clinical value.
- Do not add decorative analytics.
- Do not create huge empty sections.
- Do not use excessive icons.
- Do not use multiple competing accent colors.
- Do not make every element look like a card.
- Do not make the interface feel like a SaaS analytics dashboard.
- Keep the number of visible decisions/actions low.
- Make buttons descriptive rather than icon-only.
- Maintain strong accessibility and readability.
- Make the application responsive.

MEDICAL UX:
This is a clinical decision-support interface, so the UI must communicate:
calmness, trust, clarity, accuracy and professionalism.

The doctor should be able to understand the page in approximately 5 seconds.

IMPORTANT:
Preserve all existing functionality and backend behavior.
Do not rewrite working backend code.
Do not modify MySQL schema.
Do not modify authentication.
Do not modify prediction/model logic.
Do not remove existing routes.
Only refactor frontend templates, CSS and frontend JavaScript where necessary.

Before making changes, inspect the existing templates and CSS and reuse existing components where appropriate.

After implementation:
1. Run the application.
2. Verify every existing dashboard action still works.
3. Verify patient registration still works.
4. Verify patient list still works.
5. Verify MRI upload still works.
6. Verify reports still work.
7. Verify logout still works.
8. Check for frontend console errors.
9. Check for Python/Flask errors.
10. Ensure there are no broken routes.

The final result should look like a real modern clinical application, not a generic admin dashboard.Redesign the current NeuroScan AI clinical dashboard UI again, but ONLY the frontend/UI layer. Do NOT change, remove, or break any existing Flask routes, MySQL queries, database schema, authentication, MRI upload logic, prediction logic, patient management, reports, or backend functionality.

The current UI is functional, but it still looks like a generic admin dashboard and feels visually heavy. I want a polished, modern, minimalistic medical application that a doctor can understand and use immediately without any learning curve.

DESIGN GOAL:
Create a premium, calm, trustworthy clinical workstation similar to modern medical software. It should feel professional, clean, attractive, spacious and extremely easy to use.

CORE UX PRINCIPLE:
Prioritize the doctor's workflow over displaying lots of statistics.

The most important actions should be:
1. Start a New MRI Analysis
2. Select/Register a Patient
3. Review Recent Analyses
4. Open Reports

VISUAL DIRECTION:
- Use a clean medical aesthetic.
- Prefer a light/very-light neutral background with white cards and subtle blue/teal accents, OR an extremely refined dark theme if the existing application architecture strongly depends on it.
- Avoid the current heavy dark-blue dashboard appearance.
- Use lots of whitespace.
- Use subtle borders and very soft shadows.
- Avoid excessive glowing effects, gradients, colorful boxes, and decorative elements.
- Use one primary accent color consistently.
- Use a highly readable modern font.
- Keep typography hierarchy very clear.
- Rounded corners should be subtle and consistent, not excessive.
- Make the interface feel premium rather than flashy.

HEADER:
Simplify the top navigation.

Keep:
- NeuroScan AI logo/name
- Dashboard
- Patients
- Reports
- Doctor profile
- Logout

Do not make the header visually dominant.

DASHBOARD HERO:
Instead of immediately showing four large statistic cards, create a clean welcome section:

"Good morning, Dr. Sarah Jenkins"
"Review your patients and MRI analyses from one place."

Then place the primary action:
"+ New MRI Analysis"

And a secondary action:
"Register Patient"

The primary MRI action should be visually obvious.

STATISTICS:
Reduce the visual weight of statistics.

Keep useful information such as:
- Active Patients
- High Risk Cases
- Pending Reviews
- MRI Analyses

But make them compact and subtle, preferably as a single clean summary row rather than four huge dashboard cards.

MAIN WORKFLOW:
Make "New MRI Analysis" the central workflow.

Create a clean upload/analysis panel containing:

1. Select Patient
2. Upload MRI Scan
3. Analyze MRI

The interface should visually communicate the workflow:
Patient → MRI Scan → Analysis

The upload area should be simple and intuitive.

Use clear language such as:
"Upload MRI Scan"
"Drag and drop your MRI file here"
"Browse Files"

Do not overwhelm the doctor with technical terminology.

RECENT ANALYSES:
Keep the recent patient analyses section, but simplify the table considerably.

Columns should preferably be:
Patient
Age / Gender
Date
Result
Confidence
Action

Avoid unnecessary technical information.

Use subtle status badges for:
- Alzheimer's Disease
- Mild Cognitive Impairment
- Cognitively Normal
- Pending Review

Make patient names easy to scan.

The "Review Assessment" button should be compact and clear.

PATIENT SECTION:
Make "Patients" feel like a proper patient-management area rather than another dashboard table.

Provide:
- Search patient
- Patient list
- Patient details
- Recent MRI analysis
- Reports

Keep it extremely clean.

REPORTS:
Make the Reports section visually simple and professional.
Doctors should be able to quickly find:
- Patient
- Diagnosis
- Date
- Confidence
- View Report

IMPORTANT UX RULES:
- Do not add unnecessary widgets.
- Do not add charts unless they provide meaningful clinical value.
- Do not add decorative analytics.
- Do not create huge empty sections.
- Do not use excessive icons.
- Do not use multiple competing accent colors.
- Do not make every element look like a card.
- Do not make the interface feel like a SaaS analytics dashboard.
- Keep the number of visible decisions/actions low.
- Make buttons descriptive rather than icon-only.
- Maintain strong accessibility and readability.
- Make the application responsive.

MEDICAL UX:
This is a clinical decision-support interface, so the UI must communicate:
calmness, trust, clarity, accuracy and professionalism.

The doctor should be able to understand the page in approximately 5 seconds.

IMPORTANT:
Preserve all existing functionality and backend behavior.
Do not rewrite working backend code.
Do not modify MySQL schema.
Do not modify authentication.
Do not modify prediction/model logic.
Do not remove existing routes.
Only refactor frontend templates, CSS and frontend JavaScript where necessary.

Before making changes, inspect the existing templates and CSS and reuse existing components where appropriate.

After implementation:
1. Run the application.
2. Verify every existing dashboard action still works.
3. Verify patient registration still works.
4. Verify patient list still works.
5. Verify MRI upload still works.
6. Verify reports still work.
7. Verify logout still works.
8. Check for frontend console errors.
9. Check for Python/Flask errors.
10. Ensure there are no broken routes.

The final result should look like a real modern clinical application, not a generic admin dashboard.v# NeuroScan AI - Web-Based Alzheimer's Disease MRI Diagnosis Platform

A clinical web platform designed to assist doctors and medical researchers in staging and diagnosing Alzheimer's Disease using PyTorch-based Deep Learning MRI classification (VMamba baseline) integrated with a relational MySQL database and secure doctor authentication.

---

## Phase 2 Architecture & Features

This release introduces **Phase 2: Database and Doctor Authentication**:
- 🗄️ **MySQL Relational Database Integration**: 5 relational tables (`doctors`, `patients`, `mri_scans`, `predictions`, `reports`) designed with explicit primary keys, foreign keys, and indexes.
- 🔒 **Secure Doctor Authentication**: Password hashing using `werkzeug.security` (PBKDF2/SHA256) and Flask session management. Protected routes redirect unauthenticated users to `/login`.
- 👥 **Patient Management Workstation**: Patient intake registration form (`/patients/new`), searchable patient directory registry (`/patients`), and individual clinical profile views (`/patients/<id>`).
- 📊 **Dynamic Clinical Dashboard**: Hardcoded mock stats and patient queue replaced with live parameterized MySQL database queries.
- 🛡️ **SQL Injection Prevention**: All database operations use strict parameterized SQL queries (`%s`).
- ⚙️ **Configurable Environment Setup**: Database credentials and secret keys stored in `.env` (using `python-dotenv`) without hardcoded secrets in source code.

---

## Project Folder Structure

```
Alzheimer_AI_Platform/
├── app.py                     # Main Flask application entrypoint & factory
├── requirements.txt           # Python dependencies (Flask, Werkzeug, PyMySQL, python-dotenv, cryptography)
├── .env.example               # Environment variables configuration template
├── .env                       # Local environment variables (DB host, port, credentials)
├── README.md                  # Project setup and testing guide
├── backend/                   # Flask blueprints & business logic
│   ├── __init__.py
│   ├── auth.py                # Session control, login verification & @login_required decorator
│   ├── patient_routes.py      # Patient registration, listing, & profile routes
│   ├── routes.py              # Main dashboard, login/logout, and health API routes
│   └── utils.py               # Unique code generation, directory setup & helpers
├── database/                  # MySQL schema & database manager
│   ├── __init__.py
│   ├── db.py                  # PyMySQL connection pool & parameterized query functions
│   ├── schema.sql             # SQL DDL statements for creating 5 database tables
│   ├── seed.py                # Database seed script for initial schema & demo doctor account
│   └── README.md              # Database architecture documentation
├── model/                     # Reserved for PyTorch VMamba baseline model (Phase 3)
│   └── README.md
├── uploads/                   # Storage directory for uploaded MRI scans
├── reports/                   # Storage directory for generated diagnostic reports
├── static/                    # Frontend static assets (CSS, Vanilla JS)
│   ├── css/
│   │   ├── style.css          # Master design system (typography, glassmorphism, buttons, navbar)
│   │   └── dashboard.css      # Dashboard grids, dropzone styling, clinical table
│   └── js/
│       ├── main.js            # Frontend utilities, drag-drop indicators & toast notifications
│       └── auth.js            # Login form submit button state handler
└── templates/                 # Jinja2 HTML templates
    ├── base.html              # Master layout with session doctor profile navbar & flash messages
    ├── login.html             # Secure doctor portal login screen
    ├── dashboard.html         # Clinical doctor dashboard with live MySQL queue & stats
    ├── patient_list.html      # Searchable patient directory registry table
    ├── patient_register.html  # Intake registration form for new patients
    └── patient_detail.html    # Detailed patient clinical profile and MRI scan history
```

---

## How to Configure MySQL & Setup Database

### 1. MySQL Prerequisites
Make sure MySQL Server (e.g. MySQL Server 8.0+, XAMPP, or MariaDB) is installed and running on your machine (default port `3306`).

### 2. Configure Environment Variables (`.env`)
Copy `.env.example` to `.env` if not already present:

```bash
cp .env.example .env
```

Edit `.env` to match your MySQL database credentials:

```ini
# Flask Secret Key
SECRET_KEY=dev-secret-key-alzheimer-platform-2026

# MySQL Database Connection Credentials
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=alzheimer_db

# Demo Doctor Account Credentials (for database seeding)
SEED_DOCTOR_NAME=Dr. Sarah Jenkins
SEED_DOCTOR_EMAIL=dr.jenkins@hospital.org
SEED_DOCTOR_PASSWORD=password123
SEED_DOCTOR_DEPT=Neurology Specialist
```

### 3. Initialize Database & Seed Demo Data
Run the seeding script to automatically create the `alzheimer_db` database, execute `database/schema.sql`, create the 5 tables, and seed the demo doctor account along with initial sample patient records:

```bash
python -m database.seed
```

Output:
```text
Connecting to MySQL server at localhost:3306...
[OK] Database 'alzheimer_db' verified.
[OK] All database tables (doctors, patients, mri_scans, predictions, reports) created.
[OK] Demo Doctor Account created: dr.jenkins@hospital.org
[OK] Successfully seeded 3 initial demo patients, MRI scans, and predictions.
==========================================================
  Database Seeding Completed Successfully!
==========================================================
```

---

## How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Flask Application
```bash
python app.py
```

### 3. Access the Medical Platform
Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## Demo Doctor Account Credentials

- **Email**: `dr.jenkins@hospital.org`
- **Password**: `password123`

---

## Complete Authentication & Patient Management Testing Flow

1. **Test Authentication Protection:**
   - Attempt to access `http://127.0.0.1:5000/dashboard` or `http://127.0.0.1:5000/patients` while unauthenticated.
   - You will be automatically redirected to `/login` with a warning message: *"Please log in with your credentials to access protected clinical workstations."*

2. **Test Doctor Login:**
   - Submit invalid credentials (e.g. `wrong@email.com` / `wrongpass`) -> verify the red error alert appears.
   - Enter `dr.jenkins@hospital.org` and `password123` -> verify successful login and redirection to `/dashboard`.
   - Observe the top right navigation bar displays **Dr. Sarah Jenkins** and her initials **SJ**.

3. **Test Dashboard MySQL Data:**
   - Verify stat counters (Total MRI Scans, High Risk Cases, Registered Patients) display live data from MySQL.
   - Verify the patient diagnostics queue table displays the sample patients (`PAT-9082 Eleanor Vance`, `PAT-8721 Arthur Pendelton`, `PAT-7634 Martha Stewart`) fetched from MySQL.

4. **Test Patient Management (Create & Retrieve):**
   - Click **"+ Register New Patient"** or navigate to `/patients/new`.
   - Fill out the intake form (e.g., Name: *Margaret Thatcher*, Age: *74*, Gender: *Female*, Contact: *+1 555-9012*, History: *Early onset memory difficulties*).
   - Click **"Save & Create Patient Record"**.
   - Verify you are redirected to the new patient's profile page (`/patients/<id>`).
   - Click **"Patient Registry"** (`/patients`) to see the new patient in the searchable list.

5. **Test Doctor Logout:**
   - Click **"Logout"** in the top navigation bar.
   - Verify session destruction and redirect back to `/login`.
