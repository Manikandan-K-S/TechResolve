import os
from dotenv import load_dotenv
from datetime import timedelta

# Load .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    """
    Configuration for TechResolve
    """

    # --------------------------
    # Flask settings
    # --------------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key')
    DEBUG = True

    # --------------------------
    # Database settings
    # --------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://username:password@localhost:5432/techresolve_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------
    # File upload settings
    # --------------------------
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif', 'txt', 'doc', 'docx'}

    # --------------------------
    # Flask-Mail settings
    # --------------------------
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('EMAIL_USER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = os.getenv('EMAIL_USER')


    # --------------------------
    # Session settings
    # --------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # --------------------------
    # Discord webhook settings
    # --------------------------
    DISCORD_CC_WEBHOOK = os.getenv('DISCORD_CC_WEBHOOK')
    DISCORD_ISL_WEBHOOK = os.getenv('DISCORD_ISL_WEBHOOK')
    DISCORD_TECHNOSPHERE_WEBHOOK = os.getenv('DISCORD_TECHNOSPHERE_WEBHOOK')
    DISCORD_IBM_WEBHOOK = os.getenv('DISCORD_IBM_WEBHOOK')

