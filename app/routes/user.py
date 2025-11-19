from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import Complaint, Lab, ComplaintLog, db
from ..utils import generate_complaint_id, save_attachment
from ..notifications import notify_complaint_creation

user_bp = Blueprint('user', __name__, template_folder='../templates/user')

@user_bp.route('/submit', methods=['GET', 'POST'])
def submit_complaint():
    """
    Submit a new complaint and immediately show it on the track page
    """
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        lab_id = request.form.get('lab')
        category = request.form.get('category')
        description = request.form.get('description')
        attachment = request.files.get('attachment')

        # Generate sequential complaint ID
        complaint_id = generate_complaint_id()

        # Save attachment locally
        attachment_path = save_attachment(attachment, complaint_id)

        # Save complaint to DB
        complaint = Complaint(
            complaint_id=complaint_id,
            email=email,
            name=name,
            lab_id=lab_id,
            category=category,
            description=description,
            attachment_path=attachment_path,
            status='Pending',
            priority='Low'
        )
        db.session.add(complaint)
        db.session.flush()

        # Log initial tag state
        initial_log = ComplaintLog(
            complaint_id=complaint.id,
            admin_id=None,
            action='TAG_CHANGED',
            old_value='',
            new_value=complaint.tags,
            description='Initial tag set to none'
        )
        db.session.add(initial_log)
        db.session.commit()

        # Send notifications
        notify_complaint_creation(complaint)
        flash(f'Complaint submitted successfully! Your ID: {complaint_id}', 'success')

        # Instead of redirecting to submit page, show track page with this complaint
        complaints = [complaint]  # Wrap in list for track template
        return render_template('track_complaint.html', complaints=complaints)

    labs = Lab.query.all()
    return render_template('submit_complaint.html', labs=labs)


@user_bp.route('/track', methods=['GET', 'POST'])
def track_complaint():
    """
    Track complaint by email or complaint ID
    """
    complaints = []
    if request.method == 'POST':
        email = request.form.get('email')
        complaint_id = request.form.get('complaint_id')

        query = Complaint.query
        if email:
            query = query.filter_by(email=email)
        if complaint_id:
            query = query.filter_by(complaint_id=complaint_id)

        complaints = query.all()

        if not complaints:
            flash('No complaints found.', 'warning')

    return render_template('track_complaint.html', complaints=complaints)


@user_bp.route('/complaint/<complaint_id>')
def complaint_detail(complaint_id):
    """
    Show full details of a single complaint, including logs
    """
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first()
    if not complaint:
        flash('Complaint not found.', 'warning')
        return redirect(url_for('user.track_complaint'))

    # complaint.logs will give all related ComplaintLog entries
    return render_template('complaint_detail.html', complaint=complaint)
