"""
Backend Helper Utilities
========================
Provides helper functions for formatting dates, generating unique identifiers,
checking directory structures, managing system paths, and formatting clinical diagnostic labels.
"""

import os
import random
from datetime import datetime

# Central mapping for human-readable diagnostic labels
CLASS_DISPLAY_MAP = {
    "AD": "Alzheimer's Disease",
    "MildDemented": "Mild Demented",
    "ModerateDemented": "Moderate Demented",
    "NonDemented": "Non-Demented",
    "VeryMildDemented": "Very Mild Demented",
}

def format_diagnostic_label(raw_label):
    """
    Translates internal model class names (or legacy AD codes) into
    clean, human-readable clinical labels for display.
    """
    if not raw_label:
        return "Pending Upload"
    return CLASS_DISPLAY_MAP.get(str(raw_label).strip(), str(raw_label))

def ensure_directories_exist(base_dir):
    """
    Ensures that required runtime directories (uploads, reports) exist.
    """
    required_dirs = [
        os.path.join(base_dir, 'uploads'),
        os.path.join(base_dir, 'reports')
    ]
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

def format_current_timestamp():
    """
    Returns a human-readable timestamp for clinical logs.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_patient_code():
    """
    Generates a unique patient identifier code (e.g. PAT-4892).
    """
    random_id = random.randint(1000, 9999)
    return f"PAT-{random_id}"
