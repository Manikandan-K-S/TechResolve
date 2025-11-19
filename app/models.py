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
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Soft delete flag
    deleted_at = db.Column(db.DateTime, nullable=True)  # Timestamp of soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Admin {self.email}>"
    
    def soft_delete(self):
        """Soft delete the admin by marking as inactive"""
        self.is_active = False
        self.deleted_at = datetime.utcnow()


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
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # Hardware / Software / Network / Other
    description = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # Pending / In Progress / Resolved
    priority = db.Column(db.String(20), nullable=True)  # Low / Medium / High
    tags = db.Column(db.String(255), nullable=False, default='none')  # Comma-separated tags
    resolution_notes = db.Column(db.Text, nullable=True)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to logs
    logs = db.relationship('ComplaintLog', backref='complaint', lazy=True, cascade='all, delete-orphan')
    assigned_admin = db.relationship('Admin', backref='assigned_complaints', foreign_keys=[assigned_admin_id])

    def __repr__(self):
        return f"<Complaint {self.complaint_id}>"


# ---------------------------
# Complaint Log Table
# ---------------------------
class ComplaintLog(db.Model):
    __tablename__ = 'complaint_logs'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # e.g., Status changed, Priority set, Issue viewed, Tag changed
    old_value = db.Column(db.String(255), nullable=True)  # Old status/tags/etc
    new_value = db.Column(db.String(255), nullable=True)  # New status/tags/etc
    description = db.Column(db.Text, nullable=True)  # Admin's description/comments
    view_duration = db.Column(db.Integer, nullable=True)  # Duration of view in seconds
    target_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to admin who performed the action
    admin = db.relationship(
        'Admin',
        foreign_keys=[admin_id],
        backref=db.backref('activity_logs', lazy='dynamic')
    )
    target_admin = db.relationship(
        'Admin',
        foreign_keys=[target_admin_id],
        backref=db.backref('tagged_logs', lazy='dynamic')
    )

    def __repr__(self):
        return f"<ComplaintLog {self.id} for Complaint {self.complaint_id}>"
