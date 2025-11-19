from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Admin, db
from ..utils import hash_password, verify_superadmin
from flask import session

superadmin_bp = Blueprint('superadmin', __name__, template_folder='../templates/superadmin')

def superadmin_required(f):
    from functools import wraps
    from flask import redirect, url_for, session, flash

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'superadmin_logged_in' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('superadmin.login'))
        return f(*args, **kwargs)

    return decorated_function



# Superadmin login route
@superadmin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'superadmin_logged_in' in session:
        return redirect(url_for('superadmin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if verify_superadmin(email, password):
            session['superadmin_logged_in'] = True
            session['superadmin_email'] = email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('superadmin.dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('super_login.html')


# Superadmin logout
@superadmin_bp.route('/logout')
def logout():
    session.pop('superadmin_logged_in', None)
    session.pop('superadmin_email', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('superadmin.login'))

# ----------------------
# Dashboard
# ----------------------
@superadmin_bp.route('/dashboard')
@superadmin_required
def dashboard():
    # Only count active admins for dashboard stats
    active_admins = Admin.query.filter_by(is_active=True).all()
    recent_admins = Admin.query.filter_by(is_active=True).order_by(Admin.created_at.desc()).limit(5).all()
    total_admins = len(active_admins)
    return render_template('super_dashboard.html', total_admins=total_admins, recent_admins=recent_admins)


# ----------------------
# Manage Admins
# ----------------------
@superadmin_bp.route('/manage_admins', methods=['GET', 'POST'])
@superadmin_required
def manage_admins():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        password_hash = hash_password(password)
        admin = Admin(name=name, email=email, password_hash=password_hash, role='admin')
        db.session.add(admin)
        db.session.commit()
        flash(f'Admin {name} created successfully.', 'success')
        return redirect(url_for('superadmin.manage_admins'))

    # Show all admins (active and inactive) with status indicator
    admins = Admin.query.order_by(Admin.is_active.desc(), Admin.created_at.desc()).all()
    return render_template('manage_admins.html', admins=admins)


# ----------------------
# Delete Admin (Soft Delete)
# ----------------------
@superadmin_bp.route('/delete_admin/<int:admin_id>', methods=['POST'])
@superadmin_required
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    # Prevent self-deletion
    if admin.id == session.get('admin_id'):
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('superadmin.manage_admins'))
    
    # Soft delete the admin
    admin.soft_delete()
    db.session.commit()
    
    flash(f'Admin {admin.name} has been deactivated. All their records and logs are preserved.', 'success')
    return redirect(url_for('superadmin.manage_admins'))


# ----------------------
# Restore Admin (Reactivate)
# ----------------------
@superadmin_bp.route('/restore_admin/<int:admin_id>', methods=['POST'])
@superadmin_required
def restore_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    
    if admin.is_active:
        flash(f'Admin {admin.name} is already active.', 'info')
        return redirect(url_for('superadmin.manage_admins'))
    
    # Reactivate the admin
    admin.is_active = True
    admin.deleted_at = None
    db.session.commit()
    
    flash(f'Admin {admin.name} has been restored and reactivated.', 'success')
    return redirect(url_for('superadmin.manage_admins'))
