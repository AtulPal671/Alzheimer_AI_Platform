"""
Patient Management Routes Module — Doctor Scoped
=================================================
Defines URL routes and request handlers for registering new patients,
listing patient records, and viewing detailed clinical profiles.
All queries enforce doctor-account ownership isolation.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.auth import login_required
from backend.utils import generate_patient_code, format_current_timestamp
from database.db import query_all, query_one, execute_db

patient_bp = Blueprint('patients', __name__)

@patient_bp.route('/patients')
@login_required
def list_patients():
    """
    Renders the patient registry list page with records fetched from MySQL strictly scoped to the logged-in doctor.
    """
    search_query = request.args.get('q', '').strip()
    doctor_id = session.get('doctor_id')
    try:
        if search_query:
            sql = """
                SELECT p.*, d.name AS doctor_name,
                       (SELECT COUNT(*) FROM mri_scans WHERE patient_id = p.id) AS total_scans
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.doctor_id = %s AND (p.name LIKE %s OR p.patient_code LIKE %s)
                ORDER BY p.created_at DESC
            """
            like_term = f"%{search_query}%"
            patients = query_all(sql, (doctor_id, like_term, like_term))
        else:
            sql = """
                SELECT p.*, d.name AS doctor_name,
                       (SELECT COUNT(*) FROM mri_scans WHERE patient_id = p.id) AS total_scans
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.doctor_id = %s
                ORDER BY p.created_at DESC
            """
            patients = query_all(sql, (doctor_id,))
        db_connected = True
    except Exception as e:
        print(f"[PATIENTS DB ERROR] {e}")
        patients = []
        db_connected = False
        flash("Unable to fetch patient list from database.", "warning")

    return render_template(
        'patient_list.html',
        title="Patient Registry - NeuroScan AI",
        patients=patients,
        search_query=search_query,
        db_connected=db_connected
    )

@patient_bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def register_patient():
    """
    Renders patient registration form (GET) and processes form submission (POST).
    Automatically binds patient record to current authenticated doctor.
    """
    doctor_id = session.get('doctor_id')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        medical_history = request.form.get('medical_history', '').strip()
        patient_code = request.form.get('patient_code', '').strip() or generate_patient_code()

        # Input Validation
        if not name or not age or not gender:
            flash("Patient Name, Age, and Gender are required fields.", "danger")
            return render_template(
                'patient_register.html',
                title="Register New Patient - NeuroScan AI",
                suggested_code=patient_code,
                form_data=request.form
            )

        try:
            age_int = int(age)

            sql = """
                INSERT INTO patients (patient_code, name, age, gender, contact_info, medical_history, doctor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            new_id = execute_db(sql, (patient_code, name, age_int, gender, contact_info, medical_history, doctor_id))
            flash(f"Patient '{name}' ({patient_code}) successfully registered.", "success")
            return redirect(url_for('patients.view_patient', patient_id=new_id))

        except Exception as e:
            print(f"[REGISTER PATIENT ERROR] {e}")
            flash(f"Error registering patient: {e}", "danger")

    suggested_code = generate_patient_code()
    return render_template(
        'patient_register.html',
        title="Register New Patient - NeuroScan AI",
        suggested_code=suggested_code
    )

@patient_bp.route('/patients/<int:patient_id>')
@login_required
def view_patient(patient_id):
    """
    Renders the detailed clinical profile for a specific patient owned by the authenticated doctor.
    """
    doctor_id = session.get('doctor_id')
    try:
        patient_sql = """
            SELECT p.*, d.name AS attending_doctor, d.department AS doctor_dept
            FROM patients p
            LEFT JOIN doctors d ON p.doctor_id = d.id
            WHERE p.id = %s AND p.doctor_id = %s
        """
        patient = query_one(patient_sql, (patient_id, doctor_id))

        if not patient:
            flash("Patient record not found or access unauthorized.", "warning")
            return redirect(url_for('patients.list_patients'))

        scans_sql = """
            SELECT m.id AS scan_id, m.file_name, m.file_path, m.upload_date,
                   pr.predicted_class, pr.confidence_score, pr.id AS prediction_id,
                   r.report_file_path, r.clinical_notes
            FROM mri_scans m
            LEFT JOIN predictions pr ON m.id = pr.mri_scan_id
            LEFT JOIN reports r ON pr.id = r.prediction_id
            WHERE m.patient_id = %s
            ORDER BY m.upload_date DESC
        """
        scans = query_all(scans_sql, (patient_id,))

        return render_template(
            'patient_detail.html',
            title=f"Patient Profile - {patient['name']} ({patient['patient_code']})",
            patient=patient,
            scans=scans,
            current_time=format_current_timestamp()
        )
    except Exception as e:
        print(f"[VIEW PATIENT ERROR] {e}")
        flash("Database error retrieving patient profile.", "danger")
        return redirect(url_for('patients.list_patients'))
