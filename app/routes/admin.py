from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import Complaint, ComplaintLog, db, Admin, Lab
from ..utils import verify_password
from ..notifications import notify_assignment, notify_status_change

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


# ----------------------
# Admin session check decorator
# ----------------------
def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('admin.login'))
        
        # Check if the logged-in admin is still active
        admin_id = session.get('admin_id')
        if admin_id:
            admin = Admin.query.get(admin_id)
            if admin and not admin.is_active:
                # Admin has been deactivated - log them out
                session.clear()
                flash('Your account has been deactivated. Please contact the superadmin.', 'error')
                return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)

    return decorated_function


# ----------------------
# Admin Dashboard
# ----------------------
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Basic metrics
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    in_progress = Complaint.query.filter_by(status='In Progress').count()
    high_priority = Complaint.query.filter_by(priority='High').count()

    # Calculate average resolution time
    resolved_issues = Complaint.query.filter_by(status='Resolved').all()
    if resolved_issues:
        total_resolution_time = sum(
            (issue.updated_at - issue.created_at).total_seconds() / 3600 
            for issue in resolved_issues
        )
        avg_time = f"{total_resolution_time / len(resolved_issues):.1f} hours"
    else:
        avg_time = "N/A"

    # Get recent activity logs
    recent_logs = ComplaintLog.query\
        .order_by(ComplaintLog.timestamp.desc())\
        .limit(5)\
        .all()
    
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    # Always use the same template path whether it's SPA or not
    template = 'admin/dashboard.html'

    return render_template(
        template,
        total=total_complaints,
        pending=pending_complaints,
        resolved=resolved_complaints,
        in_progress=in_progress,
        high_priority=high_priority,
        avg_resolution_time=avg_time,
        recent_logs=recent_logs,
        current_year=datetime.utcnow().year
    )


# ----------------------
# List All Complaints
# ----------------------
@admin_bp.route('/complaints')
@admin_required
def complaint_list():
    threshold = datetime.utcnow() - timedelta(days=30)
    stale_complaints = Complaint.query.filter(
        Complaint.status.in_(['Resolved', 'Terminated']),
        Complaint.updated_at < threshold,
        Complaint.archived.is_(False)
    ).all()

    if stale_complaints:
        for item in stale_complaints:
            item.archived = True
        db.session.commit()

    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    # Always use the same template path whether it's SPA or not
    template = 'admin/complaint_list.html'
    
    return render_template(
        template, 
        complaints=complaints,
        current_year=datetime.utcnow().year
    )


# ----------------------
# Complaint Detail / Update
# ----------------------
@admin_bp.route('/complaint/<int:id>', methods=['GET', 'POST'])
@admin_required
def complaint_detail(id):
    complaint = Complaint.query.get_or_404(id)
    admins = Admin.query.order_by(Admin.name.asc()).all()
    view_log_id = None

    if request.method == 'GET' and not request.args.get('spa') == 'true':
        view_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=session.get('admin_id'),
            action='ISSUE_VIEWED',
            timestamp=datetime.utcnow()
        )
        db.session.add(view_log)
        db.session.commit()
        view_log_id = view_log.id

    if request.method == 'POST':
        # Get form data
        new_status = request.form.get('status')
        new_priority = request.form.get('priority')
        new_tags = request.form.get('tags', 'none')  # Default to 'none' if not provided
        assigned_admin_id = request.form.get('assigned_admin') or None
        description = request.form.get('description')
        remarks = request.form.get('remarks')
        resolution_notes = request.form.get('resolution_notes')
        archive_flag = request.form.get('archived') == 'on'

        acting_admin = Admin.query.get(session.get('admin_id'))

        # Log status change if status was updated
        if new_status and new_status != complaint.status:
            status_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='STATUS_CHANGED',
                old_value=complaint.status,
                new_value=new_status,
                description=remarks
            )
            db.session.add(status_log)
            complaint.status = new_status
            notify_status_change(complaint, acting_admin)

        # Log tag changes if tags were updated
        if new_tags != complaint.tags:
            tag_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='TAG_CHANGED',
                old_value=complaint.tags,
                new_value=new_tags,
                description=remarks
            )
            db.session.add(tag_log)
            complaint.tags = new_tags

        # Log priority changes if priority was updated
        if new_priority and new_priority != complaint.priority:
            priority_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='PRIORITY_CHANGED',
                old_value=complaint.priority,
                new_value=new_priority,
                description=remarks
            )
            db.session.add(priority_log)
            complaint.priority = new_priority
        previous_admin = complaint.assigned_admin
        if assigned_admin_id:
            assigned_admin = Admin.query.get(int(assigned_admin_id))
        else:
            assigned_admin = None

        if assigned_admin != previous_admin:
            assignment_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='ADMIN_ASSIGNED' if assigned_admin else 'ADMIN_UNASSIGNED',
                old_value=previous_admin.name if previous_admin else None,
                new_value=assigned_admin.name if assigned_admin else None,
                description=remarks,
                target_admin_id=assigned_admin.id if assigned_admin else None
            )
            db.session.add(assignment_log)
            complaint.assigned_admin = assigned_admin
            if assigned_admin:
                notify_assignment(complaint, assigned_admin, acting_admin)

        # Log resolution notes changes if updated
        old_resolution_notes = complaint.resolution_notes or ''
        new_resolution_notes = resolution_notes or ''
        if new_resolution_notes != old_resolution_notes:
            notes_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='RESOLUTION_NOTES_UPDATED',
                old_value=old_resolution_notes[:100] if old_resolution_notes else None,  # Truncate for log
                new_value=new_resolution_notes[:100] if new_resolution_notes else None,  # Truncate for log
                description=remarks
            )
            db.session.add(notes_log)
            complaint.resolution_notes = new_resolution_notes

        # Log archive status changes if updated
        if archive_flag != complaint.archived:
            archive_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='ARCHIVED' if archive_flag else 'UNARCHIVED',
                old_value='Archived' if complaint.archived else 'Active',
                new_value='Archived' if archive_flag else 'Active',
                description=remarks
            )
            db.session.add(archive_log)
            complaint.archived = archive_flag

        # Log description if provided (admin notes/investigation)
        if description:
            desc_log = ComplaintLog(
                complaint_id=complaint.id,
                admin_id=session.get('admin_id'),
                action='DESCRIPTION_ADDED',
                description=description,
                timestamp=datetime.utcnow()
            )
            db.session.add(desc_log)

        db.session.commit()
        flash('Complaint updated successfully.', 'success')
        return redirect(url_for('admin.complaint_detail', id=id))

    # Get complaint history
    complaint_logs = ComplaintLog.query.filter_by(complaint_id=complaint.id)\
        .order_by(ComplaintLog.timestamp.desc()).all()
    
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    # Always use the same template path whether it's SPA or not
    template = 'admin/complaint_detail.html'
        
    return render_template(
        template, 
        complaint=complaint,
        complaint_logs=complaint_logs,
        admins=admins,
        view_log_id=view_log_id,
        current_year=datetime.utcnow().year
    )


@admin_bp.route('/complaint/<int:id>/view-duration', methods=['POST'])
@admin_required
def complaint_view_duration(id):
    complaint = Complaint.query.get_or_404(id)
    payload = request.get_json(silent=True) or {}
    log_id = payload.get('log_id')
    duration = payload.get('duration')

    if not log_id:
        abort(400)

    log_entry = ComplaintLog.query.filter_by(id=log_id, complaint_id=complaint.id).first()
    if not log_entry:
        abort(404)

    try:
        log_entry.view_duration = int(float(duration))
        db.session.commit()
    except Exception:
        db.session.rollback()
        abort(400)

    return ('', 204)


# ----------------------
# Admin Login
# ----------------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = Admin.query.filter_by(email=email).first()
        
        # Check if admin exists and password is correct
        if admin and verify_password(admin.password_hash, password):
            # Check if admin account is active
            if not admin.is_active:
                flash('Your account has been deactivated. Please contact the superadmin.', 'error')
                return render_template('admin_login.html')
            
            # Login successful
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_name'] = admin.name
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('admin_login.html')

# ----------------------
# Admin Logout
# ----------------------
@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

# ----------------------
# API Endpoints for SPA
# ----------------------

@admin_bp.route('/api/dashboard')
@admin_required
def api_dashboard():
    # Basic metrics
    total_complaints = Complaint.query.count()
    pending_complaints = Complaint.query.filter_by(status='Pending').count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    in_progress_complaints = Complaint.query.filter_by(status='In Progress').count()
    terminated_complaints = Complaint.query.filter_by(status='Terminated').count()
    high_priority = Complaint.query.filter_by(priority='High').count()
    medium_priority = Complaint.query.filter_by(priority='Medium').count()
    low_priority = Complaint.query.filter_by(priority='Low').filter(Complaint.priority.is_(None)).count()

    # Calculate average resolution time
    resolved_issues = Complaint.query.filter_by(status='Resolved').all()
    if resolved_issues:
        total_resolution_time = sum(
            (issue.updated_at - issue.created_at).total_seconds() / 3600 
            for issue in resolved_issues
        )
        avg_time = f"{total_resolution_time / len(resolved_issues):.1f}"
    else:
        avg_time = "0"

    # Get recent activity logs
    recent_logs = ComplaintLog.query\
        .order_by(ComplaintLog.timestamp.desc())\
        .limit(10)\
        .all()
    
    logs_data = []
    for log in recent_logs:
        log_data = {
            'id': log.id,
            'action': log.action,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'timestamp': log.timestamp.isoformat(),
            'complaint': {
                'id': log.complaint.id,
                'complaint_id': log.complaint.complaint_id
            }
        }
        
        if log.admin:
            log_data['admin'] = {
                'id': log.admin.id,
                'name': log.admin.name
            }
        
        logs_data.append(log_data)

    return jsonify({
        'total': total_complaints,
        'pending': pending_complaints,
        'in_progress': in_progress_complaints,
        'resolved': resolved_complaints,
        'terminated': terminated_complaints,
        'avg_resolution_time': avg_time,
        'status_counts': {
            'pending': pending_complaints,
            'in_progress': in_progress_complaints,
            'resolved': resolved_complaints,
            'terminated': terminated_complaints
        },
        'priority_counts': {
            'high': high_priority,
            'medium': medium_priority,
            'low': low_priority
        },
        'recent_logs': logs_data
    })

@admin_bp.route('/api/complaints')
@admin_required
def api_complaints():
    # Archive old resolved complaints
    threshold = datetime.utcnow() - timedelta(days=30)
    stale_complaints = Complaint.query.filter(
        Complaint.status.in_(['Resolved', 'Terminated']),
        Complaint.updated_at < threshold,
        Complaint.archived.is_(False)
    ).all()

    if stale_complaints:
        for item in stale_complaints:
            item.archived = True
        db.session.commit()

    # Get all complaints
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    
    # Convert to JSON serializable format
    complaints_data = []
    for c in complaints:
        complaint_data = {
            'id': c.id,
            'complaint_id': c.complaint_id,
            'email': c.email,
            'name': c.name,
            'category': c.category,
            'status': c.status,
            'priority': c.priority,
            'tags': c.tags,
            'archived': c.archived,
            'created_at': c.created_at.isoformat(),
            'updated_at': c.updated_at.isoformat(),
            'lab': {
                'id': c.lab.id,
                'name': c.lab.name
            }
        }
        
        if c.assigned_admin:
            complaint_data['assigned_admin'] = {
                'id': c.assigned_admin.id,
                'name': c.assigned_admin.name
            }
            
        complaints_data.append(complaint_data)

    return jsonify({
        'complaints': complaints_data
    })

@admin_bp.route('/api/complaint/<int:id>')
@admin_required
def api_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    admins = Admin.query.order_by(Admin.name.asc()).all()
    
    # Log the view action
    view_log = ComplaintLog(
        complaint_id=complaint.id,
        admin_id=session.get('admin_id'),
        action='ISSUE_VIEWED',
        timestamp=datetime.utcnow()
    )
    db.session.add(view_log)
    db.session.commit()
    
    # Get complaint history
    complaint_logs = ComplaintLog.query.filter_by(complaint_id=complaint.id)\
        .order_by(ComplaintLog.timestamp.desc()).all()
    
    # Serialize complaint
    complaint_data = {
        'id': complaint.id,
        'complaint_id': complaint.complaint_id,
        'email': complaint.email,
        'name': complaint.name,
        'category': complaint.category,
        'description': complaint.description,
        'status': complaint.status,
        'priority': complaint.priority,
        'tags': complaint.tags,
        'archived': complaint.archived,
        'attachment_path': complaint.attachment_path,
        'resolution_notes': complaint.resolution_notes,
        'created_at': complaint.created_at.isoformat(),
        'updated_at': complaint.updated_at.isoformat(),
        'lab': {
            'id': complaint.lab.id,
            'name': complaint.lab.name
        },
        'view_log_id': view_log.id
    }
    
    if complaint.assigned_admin:
        complaint_data['assigned_admin'] = {
            'id': complaint.assigned_admin.id,
            'name': complaint.assigned_admin.name
        }
    
    # Serialize logs
    logs_data = []
    for log in complaint_logs:
        log_data = {
            'id': log.id,
            'action': log.action,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'view_duration': log.view_duration,
            'timestamp': log.timestamp.isoformat()
        }
        
        if log.admin:
            log_data['admin'] = {
                'id': log.admin.id,
                'name': log.admin.name
            }
        
        if log.target_admin:
            log_data['target_admin'] = {
                'id': log.target_admin.id,
                'name': log.target_admin.name
            }
            
        logs_data.append(log_data)
    
    # Serialize admins
    admins_data = [
        {'id': a.id, 'name': a.name} for a in admins
    ]
    
    return jsonify({
        'complaint': complaint_data,
        'logs': logs_data,
        'admins': admins_data
    })

@admin_bp.route('/api/complaint/<int:id>', methods=['POST'])
@admin_required
def api_update_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    admins = Admin.query.order_by(Admin.name.asc()).all()
    
    # Get form data
    new_status = request.form.get('status')
    new_priority = request.form.get('priority')
    new_tags = request.form.get('tags', 'none')  # Default to 'none' if not provided
    assigned_admin_id = request.form.get('assigned_admin') or None
    description = request.form.get('description')
    remarks = request.form.get('remarks')
    resolution_notes = request.form.get('resolution_notes')
    archive_flag = request.form.get('archived') == 'on'

    acting_admin = Admin.query.get(session.get('admin_id'))

    complaint.resolution_notes = resolution_notes
    complaint.archived = archive_flag
    changes_made = False

    # Log status change if status was updated
    if new_status and new_status != complaint.status:
        status_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=session.get('admin_id'),
            action='STATUS_CHANGED',
            old_value=complaint.status,
            new_value=new_status,
            description=remarks
        )
        db.session.add(status_log)
        complaint.status = new_status
        notify_status_change(complaint, acting_admin)
        changes_made = True

    # Log tag changes if tags were updated
    if new_tags != complaint.tags:
        tag_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=session.get('admin_id'),
            action='TAG_CHANGED',
            old_value=complaint.tags,
            new_value=new_tags,
            description=remarks
        )
        db.session.add(tag_log)
        complaint.tags = new_tags
        changes_made = True

    # Admin assignment / tagging
    previous_admin = complaint.assigned_admin
    if assigned_admin_id:
        assigned_admin = Admin.query.get(int(assigned_admin_id))
    else:
        assigned_admin = None

    if assigned_admin != previous_admin:
        assignment_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=session.get('admin_id'),
            action='ADMIN_ASSIGNED' if assigned_admin else 'ADMIN_UNASSIGNED',
            old_value=previous_admin.name if previous_admin else None,
            new_value=assigned_admin.name if assigned_admin else None,
            description=remarks,
            target_admin_id=assigned_admin.id if assigned_admin else None
        )
        db.session.add(assignment_log)
        complaint.assigned_admin = assigned_admin
        if assigned_admin:
            notify_assignment(complaint, assigned_admin, acting_admin)
        changes_made = True

    # Update priority
    if new_priority and new_priority != complaint.priority:
        complaint.priority = new_priority
        changes_made = True

    # Log description if provided
    if description:
        desc_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=session.get('admin_id'),
            action='DESCRIPTION_ADDED',
            description=description,
            timestamp=datetime.utcnow()
        )
        db.session.add(desc_log)
        changes_made = True

    db.session.commit()
    
    # Get updated complaint and logs
    complaint = Complaint.query.get(id)
    complaint_logs = ComplaintLog.query.filter_by(complaint_id=complaint.id)\
        .order_by(ComplaintLog.timestamp.desc()).all()
    
    # Serialize complaint
    complaint_data = {
        'id': complaint.id,
        'complaint_id': complaint.complaint_id,
        'email': complaint.email,
        'name': complaint.name,
        'category': complaint.category,
        'description': complaint.description,
        'status': complaint.status,
        'priority': complaint.priority,
        'tags': complaint.tags,
        'archived': complaint.archived,
        'attachment_path': complaint.attachment_path,
        'resolution_notes': complaint.resolution_notes,
        'created_at': complaint.created_at.isoformat(),
        'updated_at': complaint.updated_at.isoformat(),
        'lab': {
            'id': complaint.lab.id,
            'name': complaint.lab.name
        }
    }
    
    if complaint.assigned_admin:
        complaint_data['assigned_admin'] = {
            'id': complaint.assigned_admin.id,
            'name': complaint.assigned_admin.name
        }
    
    # Serialize logs
    logs_data = []
    for log in complaint_logs:
        log_data = {
            'id': log.id,
            'action': log.action,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'view_duration': log.view_duration,
            'timestamp': log.timestamp.isoformat()
        }
        
        if log.admin:
            log_data['admin'] = {
                'id': log.admin.id,
                'name': log.admin.name
            }
        
        if log.target_admin:
            log_data['target_admin'] = {
                'id': log.target_admin.id,
                'name': log.target_admin.name
            }
            
        logs_data.append(log_data)
    
    # Serialize admins
    admins_data = [
        {'id': a.id, 'name': a.name} for a in admins
    ]
    
    return jsonify({
        'success': True,
        'message': 'Complaint updated successfully' if changes_made else 'No changes were made',
        'complaint': complaint_data,
        'logs': logs_data,
        'admins': admins_data
    })

@admin_bp.route('/reports')
@admin_required
def reports():
    # Get data for charts
    complaints_by_category = db.session.query(
        Complaint.category, 
        db.func.count(Complaint.id).label('count')
    ).group_by(Complaint.category).all()
    
    complaints_by_lab = db.session.query(
        Lab.name, 
        db.func.count(Complaint.id).label('count')
    ).join(Complaint).group_by(Lab.name).all()
    
    # Format for template
    cat_labels = [item.category for item in complaints_by_category]
    cat_data = [item.count for item in complaints_by_category]
    cat_details = [(item.category, item.count) for item in complaints_by_category]
    
    lab_labels = [item.name for item in complaints_by_lab]
    lab_data = [item.count for item in complaints_by_lab]
    lab_details = [(item.name, item.count) for item in complaints_by_lab]
    
    # Status counts
    status_counts = {
        'Pending': Complaint.query.filter_by(status='Pending').count(),
        'In Progress': Complaint.query.filter_by(status='In Progress').count(),
        'Resolved': Complaint.query.filter_by(status='Resolved').count(),
        'Terminated': Complaint.query.filter_by(status='Terminated').count()
    }
    
    # Priority counts
    priority_counts = {
        'High': Complaint.query.filter_by(priority='High').count(),
        'Medium': Complaint.query.filter_by(priority='Medium').count(),
        'Low': Complaint.query.filter_by(priority='Low').count()
    }
    
    # Total complaints and resolution rate
    total_complaints = Complaint.query.count()
    resolved_complaints = status_counts['Resolved']
    resolution_rate = round((resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0, 1)
    
    # Average resolution time
    resolved_with_time = Complaint.query.filter_by(status='Resolved').filter(
        Complaint.updated_at.isnot(None)
    ).all()
    
    if resolved_with_time:
        total_hours = sum([
            (c.updated_at - c.created_at).total_seconds() / 3600 
            for c in resolved_with_time
        ])
        avg_resolution_time = f"{round(total_hours / len(resolved_with_time), 1)}h"
    else:
        avg_resolution_time = "N/A"
    
    # High priority count
    high_priority_count = priority_counts['High']
    
    # Admin performance
    admins = Admin.query.filter_by(is_active=True).all()
    admin_performance = []
    
    for admin in admins:
        assigned_complaints = Complaint.query.filter_by(assigned_admin_id=admin.id).all()
        total_assigned = len(assigned_complaints)
        resolved_count = len([c for c in assigned_complaints if c.status == 'Resolved'])
        in_progress_count = len([c for c in assigned_complaints if c.status == 'In Progress'])
        
        resolution_rate_admin = round((resolved_count / total_assigned * 100) if total_assigned > 0 else 0, 1)
        
        # Average response time
        if assigned_complaints:
            response_times = []
            for complaint in assigned_complaints:
                logs = ComplaintLog.query.filter_by(
                    complaint_id=complaint.id,
                    admin_id=admin.id,
                    action='ADMIN_ASSIGNED'
                ).first()
                if logs:
                    response_time = (logs.timestamp - complaint.created_at).total_seconds() / 3600
                    response_times.append(response_time)
            
            if response_times:
                avg_response_time = f"{round(sum(response_times) / len(response_times), 1)}h"
            else:
                avg_response_time = "N/A"
        else:
            avg_response_time = "N/A"
        
        # Create a simple object to hold lab info (admins don't have direct lab association)
        class LabPlaceholder:
            def __init__(self):
                self.name = "All Labs"
        
        admin_performance.append({
            'name': admin.name,
            'email': admin.email,
            'lab': LabPlaceholder(),
            'total_assigned': total_assigned,
            'resolved_count': resolved_count,
            'in_progress_count': in_progress_count,
            'resolution_rate': resolution_rate_admin,
            'avg_response_time': avg_response_time
        })
    
    # Monthly trend data
    from sqlalchemy import func, extract
    monthly_data = db.session.query(
        extract('year', Complaint.created_at).label('year'),
        extract('month', Complaint.created_at).label('month'),
        func.count(Complaint.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').limit(12).all()
    
    trend_labels = [f"{int(row.year)}-{int(row.month):02d}" for row in monthly_data]
    trend_data = [row.count for row in monthly_data]
    
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    template = 'admin/reports.html'
    
    return render_template(
        template, 
        cat_labels=cat_labels,
        cat_data=cat_data,
        cat_details=cat_details,
        lab_labels=lab_labels,
        lab_data=lab_data,
        lab_details=lab_details,
        status_counts=status_counts,
        priority_counts=priority_counts,
        total_complaints=total_complaints,
        resolution_rate=resolution_rate,
        avg_resolution_time=avg_resolution_time,
        high_priority_count=high_priority_count,
        admin_performance=admin_performance,
        trend_labels=trend_labels,
        trend_data=trend_data,
        current_year=datetime.utcnow().year
    )

@admin_bp.route('/api/reports')
@admin_required
def api_reports():
    # Get data for reports
    complaints_by_month = db.session.query(
        db.func.strftime('%Y-%m', Complaint.created_at).label('month'),
        db.func.count(Complaint.id).label('count')
    ).group_by('month').order_by('month').all()
    
    complaints_by_category = db.session.query(
        Complaint.category, 
        db.func.count(Complaint.id).label('count')
    ).group_by(Complaint.category).all()
    
    complaints_by_lab = db.session.query(
        Lab.name, 
        db.func.count(Complaint.id).label('count')
    ).join(Complaint).group_by(Lab.name).all()
    
    resolution_time_avg = db.session.query(
        db.func.avg(db.func.extract('epoch', Complaint.updated_at - Complaint.created_at) / 3600).label('hours')
    ).filter(Complaint.status == 'Resolved').scalar()
    
    # Count of resolved complaints
    resolved_count = Complaint.query.filter_by(status='Resolved').count()
    
    # Get resolution time distribution
    resolved_complaints = Complaint.query.filter_by(status='Resolved').all()
    resolution_buckets = {
        '0-1h': 0, '1-3h': 0, '3-8h': 0, '8-24h': 0,
        '1-3d': 0, '3-7d': 0, '7d+': 0
    }
    
    if resolved_complaints:
        for complaint in resolved_complaints:
            hours = (complaint.updated_at - complaint.created_at).total_seconds() / 3600
            if hours < 1:
                resolution_buckets['0-1h'] += 1
            elif hours < 3:
                resolution_buckets['1-3h'] += 1
            elif hours < 8:
                resolution_buckets['3-8h'] += 1
            elif hours < 24:
                resolution_buckets['8-24h'] += 1
            elif hours < 72:  # 3 days
                resolution_buckets['1-3d'] += 1
            elif hours < 168:  # 7 days
                resolution_buckets['3-7d'] += 1
            else:
                resolution_buckets['7d+'] += 1

    # Get min and max resolution times
    min_resolution = None
    max_resolution = None
    if resolved_complaints:
        min_resolution_complaint = min(resolved_complaints, key=lambda x: (x.updated_at - x.created_at).total_seconds())
        max_resolution_complaint = max(resolved_complaints, key=lambda x: (x.updated_at - x.created_at).total_seconds())
        
        min_resolution_seconds = (min_resolution_complaint.updated_at - min_resolution_complaint.created_at).total_seconds()
        max_resolution_seconds = (max_resolution_complaint.updated_at - max_resolution_complaint.created_at).total_seconds()
        
        # Format the times
        min_minutes = int(min_resolution_seconds / 60)
        if min_minutes < 60:
            min_resolution = f"{min_minutes}m"
        else:
            min_hours = min_minutes // 60
            min_remaining_minutes = min_minutes % 60
            min_resolution = f"{min_hours}h {min_remaining_minutes}m"
        
        # Max resolution time formatting
        max_hours = int(max_resolution_seconds / 3600)
        if max_hours < 24:
            max_resolution = f"{max_hours}h"
        else:
            max_days = max_hours // 24
            max_remaining_hours = max_hours % 24
            max_resolution = f"{max_days}d {max_remaining_hours}h"
    
    # Count unresolved complaints
    unresolved_count = Complaint.query.filter(Complaint.status != 'Resolved').count()

    return jsonify({
        'complaints_by_month': [
            {'month': item.month, 'count': item.count}
            for item in complaints_by_month
        ],
        'complaints_by_category': [
            {'category': item.category, 'count': item.count}
            for item in complaints_by_category
        ],
        'complaints_by_lab': [
            {'lab': item.name, 'count': item.count}
            for item in complaints_by_lab
        ],
        'resolution_time_avg': resolution_time_avg or 0,
        'resolved_count': resolved_count,
        'unresolved_count': unresolved_count,
        'resolution_buckets': resolution_buckets,
        'min_resolution_time': min_resolution or '0m',
        'max_resolution_time': max_resolution or '0h'
    })

@admin_bp.route('/logs')
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs_query = ComplaintLog.query\
        .order_by(ComplaintLog.timestamp.desc())
    
    logs_paginated = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get all admins for the filter
    admins = Admin.query.order_by(Admin.name.asc()).all()
    
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    template = 'admin/logs.html'
    
    return render_template(
        template, 
        logs=logs_paginated.items,
        pagination=logs_paginated,
        admins=admins,
        current_year=datetime.utcnow().year
    )

@admin_bp.route('/api/logs')
@admin_required
def api_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs_query = ComplaintLog.query\
        .order_by(ComplaintLog.timestamp.desc())
    
    logs_paginated = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    logs_data = []
    for log in logs_paginated.items:
        log_data = {
            'id': log.id,
            'action': log.action,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'description': log.description,
            'view_duration': log.view_duration,
            'timestamp': log.timestamp.isoformat(),
            'complaint': {
                'id': log.complaint.id,
                'complaint_id': log.complaint.complaint_id
            }
        }
        
        if log.admin:
            log_data['admin'] = {
                'id': log.admin.id,
                'name': log.admin.name
            }
        
        if log.target_admin:
            log_data['target_admin'] = {
                'id': log.target_admin.id,
                'name': log.target_admin.name
            }
            
        logs_data.append(log_data)
    
    return jsonify({
        'logs': logs_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': logs_paginated.total,
            'pages': logs_paginated.pages,
            'has_next': logs_paginated.has_next,
            'has_prev': logs_paginated.has_prev
        }
    })

# ----------------------
# Settings Page
# ----------------------
@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        admin_email = session.get('admin_email')
        admin = Admin.query.filter_by(email=admin_email).first()
        
        if not admin:
            flash('Admin not found', 'error')
            return redirect(url_for('admin.settings'))
        
        # Handle profile update
        if form_type == 'profile':
            try:
                name = request.form.get('name', '').strip()
                if name:
                    admin.name = name
                    session['admin_name'] = name
                    db.session.commit()
                    flash('Profile updated successfully', 'success')
                else:
                    flash('Name cannot be empty', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'error')
        
        # Handle password change
        elif form_type == 'password':
            try:
                current_password = request.form.get('current_password', '')
                new_password = request.form.get('new_password', '')
                confirm_password = request.form.get('confirm_password', '')
                
                # Verify current password
                if not check_password_hash(admin.password_hash, current_password):
                    flash('Current password is incorrect', 'error')
                elif len(new_password) < 6:
                    flash('New password must be at least 6 characters', 'error')
                elif new_password != confirm_password:
                    flash('New passwords do not match', 'error')
                else:
                    admin.password_hash = generate_password_hash(new_password)
                    db.session.commit()
                    flash('Password updated successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating password: {str(e)}', 'error')
        
        # Handle notification preferences
        elif form_type == 'notifications':
            try:
                # Note: Since notification preferences are not in the Admin model,
                # we'll store them in session for now. In production, you'd add
                # columns to the Admin model or create a separate preferences table.
                session['email_notifications'] = 'email_notifications' in request.form
                session['assignment_notifications'] = 'assignment_notifications' in request.form
                session['status_notifications'] = 'status_notifications' in request.form
                session['daily_summary'] = 'daily_summary' in request.form
                flash('Notification preferences saved', 'success')
            except Exception as e:
                flash(f'Error saving preferences: {str(e)}', 'error')
        
        return redirect(url_for('admin.settings'))
    
    # GET request
    # Check if this is an SPA request
    is_spa = request.args.get('spa') == 'true'
    # Use the settings template
    template = 'admin/settings.html'
    
    # Get current admin details
    admin_email = session.get('admin_email')
    admin = Admin.query.filter_by(email=admin_email).first()
    
    # Get notification preferences from session (default to True)
    notification_prefs = {
        'email_notifications': session.get('email_notifications', True),
        'assignment_notifications': session.get('assignment_notifications', True),
        'status_notifications': session.get('status_notifications', True),
        'daily_summary': session.get('daily_summary', False)
    }
    
    return render_template(
        template,
        current_year=datetime.utcnow().year,
        admin=admin,
        notification_prefs=notification_prefs
    )
