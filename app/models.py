from datetime import datetime
from app.extensions import db

# ---------------------------
# Lab Table
# ---------------------------
class Lab(db.Model):
    __tablename__ = 'labs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    discord_webhook = db.Column(db.String(255), nullable=True)

    # Relationship to complaints
    complaints = db.relationship('Complaint', backref='lab', lazy=True)

    def __repr__(self):
        return f"<Lab {self.name}>"


# ---------------------------
# Admin Table
# ---------------------------
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin')  # 'admin' or 'superadmin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Admin {self.email}>"


# ---------------------------
# Complaint Table
# ---------------------------
class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(20), unique=True, nullable=False)  # CMP2025-0001
    email = db.Column(db.String(150), nullable=False)  # user email
    name = db.Column(db.String(100), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Hardware / Software / Network / Other
    description = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # Pending / In Progress / Resolved
    priority = db.Column(db.String(20), nullable=True)  # Low / Medium / High
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to logs
    logs = db.relationship('ComplaintLog', backref='complaint', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Complaint {self.complaint_id}>"


# ---------------------------
# Complaint Log Table
# ---------------------------
class ComplaintLog(db.Model):
    __tablename__ = 'complaint_logs'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., Status changed, Priority set
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to admin who performed the action
    admin = db.relationship('Admin', backref='logs')

    def __repr__(self):
        return f"<ComplaintLog {self.id} for Complaint {self.complaint_id}>"
