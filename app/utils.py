import os
from werkzeug.utils import secure_filename
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from .models import Complaint

# --------------------------
# Password Hashing
# --------------------------
def hash_password(password: str) -> str:
    """Hash a password for storing in DB (admins)"""
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """Verify a plaintext password against the hashed version"""
    return check_password_hash(password_hash, password)

# --------------------------
# Superadmin Verification
# --------------------------
def verify_superadmin(email: str, password: str) -> bool:
    """
    Verify superadmin credentials from .env
    """
    super_email = os.getenv('SUPERADMIN_EMAIL')
    super_pass = os.getenv('SUPERADMIN_PASSWORD')
    return email == super_email and password == super_pass

# --------------------------
# Sequential Complaint ID
# --------------------------
def generate_complaint_id() -> str:
    """
    Generates a sequential complaint ID: CMP2025-0001, CMP2025-0002, etc.
    """
    last_complaint = Complaint.query.order_by(Complaint.id.desc()).first()
    if last_complaint:
        last_number = int(last_complaint.complaint_id.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    complaint_id = f"CMP2025-{new_number:04d}"
    return complaint_id

# --------------------------
# Save Attachment
# --------------------------
def save_attachment(file, complaint_id: str):
    """
    Saves the uploaded attachment locally under /uploads
    :param file: FileStorage object
    :param complaint_id: string
    :return: relative file path or None
    """
    if not file:
        return None

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in current_app.config['ALLOWED_EXTENSIONS']:
        raise ValueError(f"File type .{ext} not allowed.")

    # Folder path
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Save file with complaint ID prefix
    saved_filename = f"{complaint_id}_{filename}"
    file_path = os.path.join(upload_folder, saved_filename)
    file.save(file_path)

    return saved_filename
