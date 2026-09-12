"""
Doctor Authentication Module for NeuroScan AI Platform
======================================================
Provides login verification, password hashing, session management,
account registration, and access control decorators for clinical routes.
"""

import os
import logging
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import query_one, execute_db

logger = logging.getLogger(__name__)


def login_required(f):
    """
    Decorator that enforces doctor authentication on protected clinical routes.
    Redirects unauthenticated requests to the doctor login portal.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "doctor_id" not in session:
            flash("Please log in with your credentials to access protected clinical workstations.", "warning")
            return redirect(url_for("main.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def verify_doctor_login(email: str, password: str):
    """
    Verifies doctor email and password against the MySQL database.
    Uses Werkzeug password hashing verification.
    Generic error message returned on failure (prevents email enumeration).

    :param email: Doctor email address
    :param password: Provided plaintext password
    :return: (bool success, dict doctor_data or str error_message)
    """
    if not email or not password:
        return False, "Email address and password are required."

    try:
        doctor = query_one(
            "SELECT id, name, email, password_hash, department FROM doctors WHERE email = %s",
            (email.strip(),)
        )
        if doctor:
            if check_password_hash(doctor["password_hash"], password.strip()):
                return True, doctor
    except Exception as e:
        logger.error("[AUTH DB ERROR] Database lookup failed: %s", e)

    # Fallback to seed credentials if MySQL doctor record isn't in DB yet
    seed_email = os.getenv("SEED_DOCTOR_EMAIL", "dr.jenkins@hospital.org")
    seed_pass = os.getenv("SEED_DOCTOR_PASSWORD", "password123")
    seed_name = os.getenv("SEED_DOCTOR_NAME", "Dr. Sarah Jenkins")
    seed_dept = os.getenv("SEED_DOCTOR_DEPT", "Neurology Specialist")

    if email.strip().lower() == seed_email.lower() and password.strip() == seed_pass:
        demo_doctor = {
            "id": 1,
            "name": seed_name,
            "email": seed_email,
            "department": seed_dept,
        }
        return True, demo_doctor

    return False, "Invalid email or password."


def register_doctor(name: str, email: str, password: str, department: str = "Neurology Specialist"):
    """
    Registers a new doctor account with secure password hashing.

    :param name: Doctor full name (e.g. Dr. Rahul Sharma)
    :param email: Professional email address
    :param password: Plaintext password
    :param department: Department or specialty
    :return: (bool success, dict doctor_data or str error_message)
    """
    name = name.strip() if name else ""
    email = email.strip() if email else ""
    password = password.strip() if password else ""
    department = department.strip() if department else "Neurology Specialist"

    if not name or not email or not password:
        return False, "All fields (Full Name, Email Address, Password) are required."

    if len(name) < 2:
        return False, "Please enter your full professional name."

    if "@" not in email or "." not in email.split("@")[-1] or len(email) < 5:
        return False, "Please enter a valid professional email address."

    if len(password) < 6:
        return False, "Password must be at least 6 characters in length."

    try:
        existing = query_one("SELECT id FROM doctors WHERE email = %s", (email,))
        if existing:
            return False, "An account with this email address already exists. Please sign in."

        pwd_hash = generate_password_hash(password)
        doc_id = execute_db(
            "INSERT INTO doctors (name, email, password_hash, department) VALUES (%s, %s, %s, %s)",
            (name, email, pwd_hash, department)
        )
        doctor = {
            "id": doc_id,
            "name": name,
            "email": email,
            "department": department,
        }
        logger.info("[AUTH] Registered new doctor account: %s (%s)", name, email)
        return True, doctor
    except Exception as e:
        logger.error("[REGISTER ERROR] Failed to create doctor account: %s", e)
        return False, "Database error creating account. Please try again."


def get_current_doctor():
    """Returns information dictionary for the currently logged-in doctor session."""
    if "doctor_id" in session:
        return {
            "id": session.get("doctor_id"),
            "name": session.get("doctor_name"),
            "email": session.get("doctor_email"),
            "department": session.get("doctor_dept"),
        }
    return None
