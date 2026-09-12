"""
Main Application Entrypoint - NeuroScan AI Platform

Initializes Flask application with environment variables, registers route blueprints
for authentication, dashboard, and patient management, ensures file directories exist,
and provides session context and filters to Jinja2 templates.
"""

import os
from flask import Flask, session
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

from backend.routes import main_bp
from backend.patient_routes import patient_bp
from backend.auth import get_current_doctor
from backend.utils import ensure_directories_exist, format_diagnostic_label

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    
    # App Configuration from Environment
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-alzheimer-platform-2026')
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB Max Upload Limit
    
    # Path Configurations
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
    app.config['REPORTS_FOLDER'] = os.path.join(base_dir, 'reports')
    
    # Ensure uploads/ and reports/ directories exist
    ensure_directories_exist(base_dir)
    
    # Register backend route blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(patient_bp)

    # Provide active doctor session context to all HTML templates
    @app.context_processor
    def inject_current_doctor():
        return dict(current_doctor=get_current_doctor())

    # Register custom Jinja filters
    @app.template_filter('format_diagnosis')
    def jinja_format_diagnosis(raw_label):
        return format_diagnostic_label(raw_label)

    return app

app = create_app()

if __name__ == '__main__':
    print("==========================================================")
    print("  NeuroScan AI - Alzheimer's Disease MRI Diagnosis Platform")
    print("  Status: Server running on http://127.0.0.1:5000")
    print("  Phase 2: MySQL Database & Doctor Authentication Active")
    print("==========================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
