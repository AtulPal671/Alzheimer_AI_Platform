"""
Backend Main Routes Module — Doctor Scoped & Authenticated
=========================================================
Defines core application routes for physician authentication, clinical workstation dashboard,
MRI analysis file uploads, clinical diagnostic reports, and health monitoring.
All queries strictly enforce doctor account isolation.
"""

import os
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, session, flash, current_app
from werkzeug.utils import secure_filename
from backend.auth import login_required, verify_doctor_login, register_doctor
from backend.utils import format_current_timestamp, format_diagnostic_label
from database.db import query_all, query_one, execute_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles physician login portal (GET) and authentication verification (POST).
    """
    if 'doctor_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')

        success, result = verify_doctor_login(email, password)

        if success:
            session.permanent = bool(remember)
            session['doctor_id'] = result['id']
            session['doctor_name'] = result['name']
            session['doctor_email'] = result['email']
            session['doctor_dept'] = result['department']

            flash(f"Welcome back, {result['name']}!", "success")
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash(result, "danger")

    return render_template('login.html', title="Physician Portal Login - NeuroScan")

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles doctor account registration (GET) and creation (POST).
    """
    if 'doctor_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        department = request.form.get('department', 'Neurology Specialist').strip()

        if password != confirm_password:
            flash("Passwords do not match. Please verify passwords and try again.", "danger")
            return render_template('register.html', title="Create Account - NeuroScan", name=name, email=email, department=department)

        success, result = register_doctor(name, email, password, department)

        if success:
            session.permanent = True
            session['doctor_id'] = result['id']
            session['doctor_name'] = result['name']
            session['doctor_email'] = result['email']
            session['doctor_dept'] = result['department']

            flash(f"Account created successfully! Welcome to your workstation, {result['name']}.", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash(result, "danger")

    return render_template('register.html', title="Create Doctor Account - NeuroScan")

@main_bp.route('/logout')
def logout():
    """Destroys doctor session and redirects to login portal."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the clinical doctor workstation dashboard with distinct patient select queue,
    recent MRI analyses, and diagnostic stats. Strictly scoped to the currently authenticated doctor.
    """
    doctor_id = session.get('doctor_id')
    db_connected = True
    patients_list = []
    recent_analyses = []
    stats = {
        "total_scans": 0,
        "high_risk_cases": 0,
        "pending_review": 0,
        "total_patients": 0
    }

    try:
        # 1. Total Scans Count
        scans_count_res = query_one("""
            SELECT COUNT(*) AS total FROM mri_scans m 
            JOIN patients p ON m.patient_id = p.id 
            WHERE p.doctor_id = %s
        """, (doctor_id,))
        if scans_count_res:
            stats["total_scans"] = scans_count_res["total"]

        # 2. High Risk Cases Count
        high_risk_res = query_one("""
            SELECT COUNT(*) AS total FROM predictions pr 
            JOIN mri_scans m ON pr.mri_scan_id = m.id 
            JOIN patients p ON m.patient_id = p.id 
            WHERE p.doctor_id = %s AND (pr.predicted_class LIKE %s OR pr.predicted_class LIKE %s OR pr.predicted_class = 'AD')
        """, (doctor_id, '%Moderate%', '%Alzheimer%'))
        if high_risk_res:
            stats["high_risk_cases"] = high_risk_res["total"]

        # 3. Total Patients Count
        total_patients_res = query_one("SELECT COUNT(*) AS total FROM patients WHERE doctor_id = %s", (doctor_id,))
        if total_patients_res:
            stats["total_patients"] = total_patients_res["total"]

        # 4. Pending Reviews Count (Reports without clinical notes or unreviewed)
        pending_res = query_one("""
            SELECT COUNT(*) AS total FROM reports r
            JOIN predictions pr ON r.prediction_id = pr.id
            JOIN mri_scans m ON pr.mri_scan_id = m.id
            JOIN patients p ON m.patient_id = p.id
            WHERE p.doctor_id = %s AND (r.clinical_notes IS NULL OR r.reviewed_at IS NULL)
        """, (doctor_id,))
        if pending_res:
            stats["pending_review"] = pending_res["total"]

        # 5. Distinct Patients for Upload Dropdowns
        patients_list = query_all("""
            SELECT id AS db_id, patient_code AS id, name, age, gender
            FROM patients
            WHERE doctor_id = %s
            ORDER BY name ASC
        """, (doctor_id,))

        # 6. Recent MRI Analyses Queue (One row per scan analysis)
        scans_sql = """
            SELECT 
                m.id AS scan_id,
                m.file_name,
                DATE_FORMAT(m.upload_date, '%%Y-%%m-%%d') AS date,
                p.id AS patient_db_id,
                p.patient_code AS id,
                p.name,
                p.age,
                p.gender,
                pr.predicted_class,
                pr.confidence_score
            FROM mri_scans m
            JOIN patients p ON m.patient_id = p.id
            LEFT JOIN predictions pr ON m.id = pr.mri_scan_id
            WHERE p.doctor_id = %s
            ORDER BY m.upload_date DESC
            LIMIT 20
        """
        raw_scans = query_all(scans_sql, (doctor_id,))

        for row in raw_scans:
            diag = row.get('predicted_class')
            confidence = row.get('confidence_score')
            
            if not diag:
                diag_label = "Pending Upload"
                conf_label = "N/A"
                badge_class = "badge-neutral"
                mri_status = "Awaiting Image"
            else:
                diag_label = format_diagnostic_label(diag)
                conf_label = f"{round(confidence * 100, 1)}%" if (confidence is not None and confidence <= 1.0) else (f"{confidence}%" if confidence is not None else "N/A")
                mri_status = "Analyzed"

                if "NonDemented" in diag or "Normal" in diag or "CN" in diag:
                    badge_class = "badge-success"
                elif "Moderate" in diag or "Alzheimer" in diag or "AD" in diag:
                    badge_class = "badge-danger"
                elif "Mild" in diag or "Impairment" in diag or "MCI" in diag:
                    badge_class = "badge-warning"
                else:
                    badge_class = "badge-warning"

            recent_analyses.append({
                "scan_id": row['scan_id'],
                "db_id": row['patient_db_id'],
                "id": row['id'],
                "name": row['name'],
                "age": row['age'],
                "gender": row['gender'],
                "date": row['date'] or "—",
                "mri_status": mri_status,
                "diagnosis": diag_label,
                "confidence": conf_label,
                "badge_class": badge_class
            })

    except Exception as e:
        print(f"[DASHBOARD DB ERROR] {e}")
        db_connected = False

    return render_template(
        'dashboard.html',
        title="Clinical Workstation - NeuroScan",
        patients=patients_list,
        recent_analyses=recent_analyses,
        stats=stats,
        db_connected=db_connected,
        current_time=format_current_timestamp()
    )

@main_bp.route('/upload_mri', methods=['POST'])
@login_required
def upload_mri():
    """
    Handles MRI scan file upload and generates diagnostic staging record.
    Verifies patient ownership against current authenticated doctor.
    Performs domain validation BEFORE any database operations.
    """
    doctor_id = session.get('doctor_id')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    patient_id = request.form.get('patient_id')
    file = request.files.get('mri_file')

    if not patient_id or not file:
        if is_ajax:
            return jsonify({"success": False, "error": "Please select a patient and an MRI file to upload."}), 400
        flash("Please select a patient and an MRI file to upload.", "danger")
        return redirect(url_for('main.dashboard'))

    # Ownership check on patient
    patient_record = query_one("SELECT id FROM patients WHERE id = %s AND doctor_id = %s", (patient_id, doctor_id))
    if not patient_record:
        if is_ajax:
            return jsonify({"success": False, "error": "Patient record not found or access unauthorized."}), 403
        flash("Patient record not found or access unauthorized.", "danger")
        return redirect(url_for('main.dashboard'))

    filename = secure_filename(file.filename)
    if not filename:
        filename = "brain_scan.dcm"

    # Doctor-isolated upload directory
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    doc_upload_folder = os.path.join(base_upload_folder, f"doctor_{doctor_id}")
    os.makedirs(doc_upload_folder, exist_ok=True)
    
    file_path = os.path.join(doc_upload_folder, filename)
    file.save(file_path)

    try:
        # 1. Run domain validation and VMamba inference BEFORE any database insertion
        from model.inference import run_inference
        inference_result = run_inference(file_path)

        if not inference_result.get("is_valid") or inference_result.get("error") or not inference_result.get("predicted_class"):
            err_msg = inference_result.get("error") or "Invalid input: Please upload a valid brain MRI scan."
            print(f"[INPUT VALIDATION / INFERENCE REJECTED] {err_msg}")
            
            # Remove the rejected non-MRI/corrupted file from disk
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as rm_err:
                print(f"[FILE CLEANUP ERROR] {rm_err}")

            if is_ajax:
                return jsonify({"success": False, "error": err_msg}), 400
            flash(err_msg, "danger")
            return redirect(url_for('main.dashboard'))

        chosen_class = inference_result["predicted_class"]
        conf         = inference_result["confidence"]

        # 2. Save scan record (ONLY for verified valid brain MRIs)
        scan_id = execute_db(
            "INSERT INTO mri_scans (patient_id, file_name, file_path) VALUES (%s, %s, %s)",
            (patient_id, filename, file_path)
        )

        # 3. Save prediction record
        pred_id = execute_db(
            "INSERT INTO predictions (mri_scan_id, predicted_class, confidence_score) VALUES (%s, %s, %s)",
            (scan_id, chosen_class, conf)
        )

        # 4. Create report entry
        execute_db(
            "INSERT INTO reports (prediction_id, clinical_notes) VALUES (%s, NULL)",
            (pred_id,)
        )

        if is_ajax:
            return jsonify({
                "success": True,
                "scan_id": scan_id,
                "predicted_class": chosen_class,
                "display_class": format_diagnostic_label(chosen_class),
                "confidence": conf,
                "redirect_url": url_for('main.view_report', scan_id=scan_id)
            })

        flash("MRI Scan successfully uploaded and analyzed.", "success")
        return redirect(url_for('main.view_report', scan_id=scan_id))

    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass
        if is_ajax:
            return jsonify({"success": False, "error": f"Error processing MRI upload: {e}"}), 500
        flash("Error processing MRI upload.", "danger")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/uploads/<path:filename>')
@login_required
def serve_uploaded_mri(filename):
    """
    Serves uploaded MRI scan files directly from the doctor's isolated upload directory.
    Validates ownership of the requesting doctor.
    """
    from flask import send_from_directory
    upload_folder = current_app.config['UPLOAD_FOLDER']
    doctor_id = session.get('doctor_id')

    # Verify authorization for this file
    authorized_scan = query_one("""
        SELECT m.id, m.file_path FROM mri_scans m
        JOIN patients p ON m.patient_id = p.id
        WHERE (m.file_name = %s OR m.file_path LIKE %s) AND p.doctor_id = %s
    """, (filename, f"%{filename}%", doctor_id))

    doc_folder = f"doctor_{doctor_id}"
    target_dir = os.path.join(upload_folder, doc_folder)
    
    if os.path.isfile(os.path.join(target_dir, filename)):
        return send_from_directory(target_dir, filename)
    elif os.path.isfile(os.path.join(upload_folder, filename)) and authorized_scan:
        return send_from_directory(upload_folder, filename)
    elif authorized_scan:
        full_p = authorized_scan['file_path']
        if os.path.isfile(full_p):
            return send_from_directory(os.path.dirname(full_p), os.path.basename(full_p))

    return "Access denied or file not found.", 403

@main_bp.route('/reports')
@login_required
def list_reports():
    """
    Renders clinical diagnostic reports directory strictly for the logged-in doctor.
    """
    doctor_id = session.get('doctor_id')
    try:
        reports_sql = """
            SELECT 
                m.id AS scan_id, 
                m.file_name, 
                DATE_FORMAT(m.upload_date, '%%Y-%%m-%%d') AS upload_date,
                p.patient_code, 
                p.name AS patient_name, 
                p.age, 
                p.gender, 
                pr.predicted_class, 
                pr.confidence_score, 
                r.clinical_notes
            FROM mri_scans m
            JOIN patients p ON m.patient_id = p.id
            LEFT JOIN predictions pr ON m.id = pr.mri_scan_id
            LEFT JOIN reports r ON pr.id = r.prediction_id
            WHERE p.doctor_id = %s
            ORDER BY m.upload_date DESC
        """
        reports = query_all(reports_sql, (doctor_id,))
    except Exception as e:
        print(f"[REPORTS LIST ERROR] {e}")
        reports = []

    return render_template('reports.html', title="Diagnostic Reports - NeuroScan", reports=reports)

@main_bp.route('/reports/<int:scan_id>')
@login_required
def view_report(scan_id):
    """
    Renders printable clinical report view for a specific MRI scan assessment owned by doctor.
    """
    doctor_id = session.get('doctor_id')
    try:
        report_sql = """
            SELECT 
                m.id AS scan_id, 
                m.file_name, 
                DATE_FORMAT(m.upload_date, '%%Y-%%m-%%d') AS upload_date,
                p.patient_code, 
                p.name AS patient_name, 
                p.age, 
                p.gender, 
                pr.predicted_class, 
                pr.confidence_score, 
                r.clinical_notes,
                DATE_FORMAT(r.reviewed_at, '%%Y-%%m-%%d %%H:%%i') AS reviewed_at,
                d.name AS reviewer_name
            FROM mri_scans m
            JOIN patients p ON m.patient_id = p.id
            LEFT JOIN predictions pr ON m.id = pr.mri_scan_id
            LEFT JOIN reports r ON pr.id = r.prediction_id
            LEFT JOIN doctors d ON r.doctor_id = d.id
            WHERE m.id = %s AND p.doctor_id = %s
        """
        report = query_one(report_sql, (scan_id, doctor_id))

        if not report:
            flash("Diagnostic report record not found or access unauthorized.", "warning")
            return redirect(url_for('main.list_reports'))

        # Check / auto-generate XAI attribution artifacts for this scan
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_name = report['file_name']
        base_name, _ = os.path.splitext(file_name)
        heatmap_name = f"{base_name}_xai_heatmap.png"
        overlay_name = f"{base_name}_xai_overlay.png"

        doc_folder = f"doctor_{doctor_id}"
        target_dir = os.path.join(upload_folder, doc_folder)
        os.makedirs(target_dir, exist_ok=True)

        heatmap_path = os.path.join(target_dir, heatmap_name)
        overlay_path = os.path.join(target_dir, overlay_name)

        if not (os.path.isfile(heatmap_path) and os.path.isfile(overlay_path)):
            mri_file_path = os.path.join(target_dir, file_name)
            if not os.path.isfile(mri_file_path):
                mri_file_path = os.path.join(upload_folder, file_name)

            if os.path.isfile(mri_file_path):
                try:
                    from model.inference import get_model, _preprocess
                    from model.xai import generate_xai_explanation
                    model = get_model()
                    generate_xai_explanation(mri_file_path, model, _preprocess)
                except Exception as xai_err:
                    print(f"[XAI AUTO-GEN ERROR] {xai_err}")

        report['heatmap_filename'] = heatmap_name if (os.path.isfile(heatmap_path) or os.path.isfile(os.path.join(upload_folder, heatmap_name))) else None
        report['overlay_filename'] = overlay_name if (os.path.isfile(overlay_path) or os.path.isfile(os.path.join(upload_folder, overlay_name))) else None

        return render_template('reports.html', title=f"Report - {report['patient_name']}", selected_report=report)
    except Exception as e:
        print(f"[VIEW REPORT ERROR] {e}")
        flash("Error loading report details.", "danger")
        return redirect(url_for('main.list_reports'))

@main_bp.route('/reports/<int:scan_id>/notes', methods=['POST'])
@login_required
def save_clinical_notes(scan_id):
    """
    Saves attending physician clinical observations and marks report as clinically Reviewed.
    Verifies ownership before saving.
    """
    notes = request.form.get('clinical_notes', '').strip()
    doctor_id = session.get('doctor_id')

    try:
        pred = query_one("""
            SELECT pr.id FROM predictions pr
            JOIN mri_scans m ON pr.mri_scan_id = m.id
            JOIN patients p ON m.patient_id = p.id
            WHERE m.id = %s AND p.doctor_id = %s
        """, (scan_id, doctor_id))

        if not pred:
            flash("Diagnostic report record not found or access unauthorized.", "danger")
            return redirect(url_for('main.list_reports'))

        pred_id = pred['id']
        rep = query_one("SELECT id FROM reports WHERE prediction_id = %s", (pred_id,))

        saved_notes = notes if notes else None

        if rep:
            execute_db("""
                UPDATE reports 
                SET clinical_notes = %s, doctor_id = %s, reviewed_at = NOW() 
                WHERE prediction_id = %s
            """, (saved_notes, doctor_id, pred_id))
        else:
            execute_db("""
                INSERT INTO reports (prediction_id, clinical_notes, doctor_id, reviewed_at) 
                VALUES (%s, %s, %s, NOW())
            """, (pred_id, saved_notes, doctor_id))

        flash("Clinical notes saved successfully. Study marked as Reviewed.", "success")
    except Exception as e:
        print(f"[SAVE NOTES ERROR] {e}")
        flash("Error saving clinical notes.", "danger")

    return redirect(url_for('main.view_report', scan_id=scan_id))

@main_bp.route('/api/health')
def health_check():
    """API health status endpoint."""
    db_status = "offline"
    try:
        from database.db import check_db_health
        if check_db_health():
            db_status = "connected"
    except Exception:
        pass

    return jsonify({
        "status": "online",
        "service": "NeuroScan Diagnostic Workstation",
        "database": db_status,
        "timestamp": format_current_timestamp()
    })
