from flask import Flask, session
from .config import Config
from .extensions import db, mail, setup_jinja_filters
from datetime import datetime
from sqlalchemy import inspect, text

# --------------------------
# Context processor
# --------------------------
def inject_current_year():
    """
    Makes current_year available in all templates
    """
    return {'current_year': datetime.now().year}


# --------------------------
# Create Flask App
# --------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Register custom Jinja2 filters
    setup_jinja_filters(app)

    # Register context processor
    app.context_processor(inject_current_year)

    # Import and register blueprints
    from .routes.main import main_bp
    from .routes.user import user_bp
    from .routes.admin import admin_bp
    from .routes.superadmin import superadmin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

    # --------------------------
    # Optional: create tables automatically in development
    # --------------------------
    with app.app_context():
        db.create_all()
        ensure_schema()

    return app


def ensure_schema():
    """Apply missing schema changes without relying on external migrations."""
    inspector = inspect(db.engine)

    complaint_columns = {col['name'] for col in inspector.get_columns('complaints')}
    log_columns = {col['name'] for col in inspector.get_columns('complaint_logs')}
    admin_columns = {col['name'] for col in inspector.get_columns('admins')}

    statements = []

    # Complaints table updates
    if 'assigned_admin_id' not in complaint_columns:
        statements.append('ALTER TABLE complaints ADD COLUMN assigned_admin_id INTEGER')
    if 'resolution_notes' not in complaint_columns:
        statements.append('ALTER TABLE complaints ADD COLUMN resolution_notes TEXT')
    if 'archived' not in complaint_columns:
        statements.append("ALTER TABLE complaints ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE")

    # Complaint logs table updates
    if 'target_admin_id' not in log_columns:
        statements.append('ALTER TABLE complaint_logs ADD COLUMN target_admin_id INTEGER')

    # Fix admin_id to allow NULL (for system-generated logs)
    statements.append('ALTER TABLE complaint_logs ALTER COLUMN admin_id DROP NOT NULL')

    # Admins table updates for soft delete
    if 'is_active' not in admin_columns:
        statements.append("ALTER TABLE admins ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE")
    if 'deleted_at' not in admin_columns:
        statements.append("ALTER TABLE admins ADD COLUMN deleted_at TIMESTAMP")

    for stmt in statements:
        try:
            db.session.execute(text(stmt))
        except Exception:
            db.session.rollback()
        else:
            db.session.commit()

    # Add foreign keys if missing
    complaint_fks = {fk['name'] for fk in inspector.get_foreign_keys('complaints') if fk.get('name')}
    if 'fk_complaints_assigned_admin' not in complaint_fks:
        try:
            db.session.execute(text(
                'ALTER TABLE complaints ADD CONSTRAINT fk_complaints_assigned_admin '
                'FOREIGN KEY (assigned_admin_id) REFERENCES admins(id)'
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()

    log_fks = {fk['name'] for fk in inspector.get_foreign_keys('complaint_logs') if fk.get('name')}
    if 'fk_logs_target_admin' not in log_fks:
        try:
            db.session.execute(text(
                'ALTER TABLE complaint_logs ADD CONSTRAINT fk_logs_target_admin '
                'FOREIGN KEY (target_admin_id) REFERENCES admins(id)'
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
