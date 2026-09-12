"""
Database Seeding Script for NeuroScan AI Platform
=================================================
Initializes MySQL schema and populates initial demo doctor account.
Does NOT create dummy/fake patient records automatically so new accounts remain clean.
"""

import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from database.db import get_db_credentials, get_db_connection

load_dotenv()

def init_db_and_seed():
    """Initializes MySQL schema and verifies base system configuration."""
    creds = get_db_credentials()
    db_name = creds['database']
    
    print(f"Connecting to MySQL server at {creds['host']}:{creds['port']}...")
    
    # Step 1: Ensure database exists
    try:
        conn = get_db_connection(include_db=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4;")
            print(f"[OK] Database '{db_name}' verified.")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to connect or create database '{db_name}': {e}")
        return False

    # Step 2: Run schema DDL
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_file):
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_statements = f.read()

        conn = get_db_connection(include_db=True)
        try:
            with conn.cursor() as cursor:
                for statement in sql_statements.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
            print("[OK] Database schema verified.")
        except Exception as e:
            print(f"[ERROR] Error executing schema DDL: {e}")
            return False
        finally:
            conn.close()

    # Step 3: Seed Demo Doctor Account ONLY (if missing)
    doc_name = os.getenv('SEED_DOCTOR_NAME', 'Dr. Sarah Jenkins')
    doc_email = os.getenv('SEED_DOCTOR_EMAIL', 'dr.jenkins@hospital.org')
    doc_password = os.getenv('SEED_DOCTOR_PASSWORD', 'password123')
    doc_dept = os.getenv('SEED_DOCTOR_DEPT', 'Neurology Specialist')

    hashed_password = generate_password_hash(doc_password)

    conn = get_db_connection(include_db=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM doctors WHERE email = %s", (doc_email,))
            existing_doctor = cursor.fetchone()

            if not existing_doctor:
                cursor.execute("""
                    INSERT INTO doctors (name, email, password_hash, department)
                    VALUES (%s, %s, %s, %s)
                """, (doc_name, doc_email, hashed_password, doc_dept))
                print(f"[OK] Seed Demo Doctor Account created: {doc_email}")

        print("==========================================================")
        print("  Database Schema & Seed Doctor Active!")
        print("==========================================================")
        return True
    except Exception as e:
        print(f"[ERROR] Seed setup failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    init_db_and_seed()
