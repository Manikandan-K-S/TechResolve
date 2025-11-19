from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app
import os

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/')
def home():
    """
    Landing page for TechResolve.
    Options: Submit complaint, Track complaint, Admin login
    """
    return render_template('index.html')

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Serve uploaded files from the uploads directory.
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)
