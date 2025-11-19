from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from markupsafe import Markup
import re

# --------------------------
# SQLAlchemy
# --------------------------
db = SQLAlchemy()


# --------------------------
# Flask-Mail
# --------------------------
mail = Mail()


# --------------------------
# Custom Jinja2 Filters
# --------------------------
def nl2br_filter(text):
    if not text:
        return ""
    return Markup(text.replace('\n', '<br>'))

def setup_jinja_filters(app):
    """Register custom Jinja2 filters with the Flask app"""
    app.jinja_env.filters['nl2br'] = nl2br_filter
