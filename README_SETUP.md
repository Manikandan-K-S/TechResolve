TechResolve — Setup & Quickstart
=================================

This README explains how to set up the TechResolve project locally (development) on Windows (PowerShell). It includes environment variable guidance, database setup, running the server, and running tests.

This guide assumes you cloned the repository to `D:\TechResolve` (or similar) and that you have Python and PostgreSQL installed.

Table of contents
-----------------
- Prerequisites
- Prepare the repository
- Create & activate virtual environment (PowerShell)
- Install dependencies
- Environment variables (.env)
- Database setup
- Create uploads directory
- Run the application (development)
- Run the application (production example)
- Run tests
- Troubleshooting & notes
- Useful commands summary

Prerequisites
-------------
- Python 3.9+ (3.11 recommended)
- PostgreSQL (server)
- Git
- PowerShell (pwsh)

Optional but recommended:
- A mail account (SMTP) for email notifications
- Discord webhook URLs for labs (if using Discord integration)

Prepare the repository
----------------------
Open PowerShell in the project root (example path used below):

```powershell
cd D:\TechResolve
```

Create & activate a virtual environment (PowerShell)
---------------------------------------------------
```powershell
python -m venv .venv
# Activate in PowerShell
.\.venv\Scripts\Activate.ps1
# If you use cmd.exe:
# .\.venv\Scripts\activate.bat
```

Install dependencies
--------------------
(Uses the provided `requirements.txt`.)

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Environment variables — create `.env`
-------------------------------------
Create a `.env` file in the project root (`D:\TechResolve\.env`) and add required variables. Example minimal `.env` for local development:

```
# Security
SECRET_KEY=changeme_to_a_secure_random_string

# Database (Postgres example)
# Replace user, password, host, port, dbname accordingly
DATABASE_URL=postgresql://techresolve_user:password@localhost:5432/techresolve_db

# Mail (optional, for email notifications)
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_app_specific_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True

# Superadmin (for superadmin access)
SUPERADMIN_EMAIL=superadmin@example.com
SUPERADMIN_PASSWORD=supersecurepassword

# Other optional configs
# UPLOAD_FOLDER will be set via app/config.py by default to ../uploads
```

Make sure `.env` is added to `.gitignore` (it should be by default).

Database setup
--------------
1. Create a PostgreSQL user and database.

Example (psql):

```sql
-- connect as postgres or an admin user
CREATE USER techresolve_user WITH PASSWORD 'password';
CREATE DATABASE techresolve_db OWNER techresolve_user;
GRANT ALL PRIVILEGES ON DATABASE techresolve_db TO techresolve_user;
```

2. Apply schema / create tables

This project may use SQLAlchemy to create tables automatically. You can use the application factory to create tables:

```powershell
# ensure .env is present and virtualenv is active
python -c "from app import create_app; from app.extensions import db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()"
```

Note: The project mentions an `ensure_schema()` helper in the docs. If migrations are required (Alembic not included), check `app` for methods that apply the schema.

Create uploads directory
------------------------
Uploads are stored in the project root folder `uploads/` by default. Create it and ensure the app user can write to it:

```powershell
# from project root
New-Item -ItemType Directory -Path .\uploads -Force
```

The app serves uploaded files via an app route `/uploads/<filename>` and expects `UPLOAD_FOLDER` configured in `app/config.py`.

Run the application (development)
---------------------------------
The project contains `run.py` (project entry) and `wsgi.py`. The simplest approach for development is:

```powershell
# Activate venv (if not active)
.\.venv\Scripts\Activate.ps1
# Run
python run.py
```

The dev server usually runs at `http://127.0.0.1:5050` (or port specified by the app). Check `run.py` for exact behavior.

Alternatively, set FLASK_APP and use `flask run` (if app factory exported appropriately):

```powershell
$env:FLASK_APP = 'run.py'
$env:FLASK_ENV = 'development'
flask run --host=127.0.0.1 --port=5050
```

Run the application (production example)
---------------------------------------
For production use a WSGI server such as Gunicorn (Linux) or use a process manager. Example (on Linux):

```bash
# From project root (Unix example)
pip install gunicorn
gunicorn "wsgi:app" -w 4 -b 0.0.0.0:8000
```

On Windows you can use `waitress`:

```powershell
pip install waitress
python -m waitress --call "wsgi:create_app" --listen=0.0.0.0:8000
```

Run tests
---------
The repository includes a `tests/` folder. Run tests with pytest:

```powershell
# From project root with venv active
pip install pytest
pytest -q
```

Troubleshooting & notes
-----------------------
- 404 when accessing `http://127.0.0.1:5050/static/uploads/...`:
  - Uploads are stored in `./uploads` (project root) and served via an application route `/uploads/<filename>`. Use the `/uploads/` path or ensure files are placed under `app/static/uploads` if you want to serve via static route.

- If templates call `url_for('main.home')` ensure `app/routes/main.py` registers the `main` blueprint and the view is named `home()`.

- If you get a BuildError complaining about `main.index` vs `main.home`, update templates to use the actual endpoint name defined in `app/routes/main.py` (example: `url_for('main.home')`).

- Mail delivery requires correct SMTP credentials and may need "App Passwords" for Gmail accounts.

- If the app raises database model/column missing errors, check `app/models.py` and the project docs. There is an `ensure_schema()` helper indicated in docs to help create missing columns.

- Maximum upload size is set in `app/config.py` (2MB by default). Adjust `MAX_CONTENT_LENGTH` if required.

Useful commands (PowerShell)
----------------------------
```powershell
# Create venv and activate
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements.txt

# Create uploads folder
New-Item -ItemType Directory -Path .\uploads -Force

# Create DB (psql example)
# psql -U postgres -c "CREATE DATABASE techresolve_db;"

# Create DB tables via SQLAlchemy
python -c "from app import create_app; from app.extensions import db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()"

# Run dev server
python run.py

# Run tests
pytest -q
```

Contributing
------------
- Fork the repo and open a pull request
- Write tests for any new behavior
- Keep environment secrets out of source control

Support
-------
If you get stuck, open an issue in the repository with details (OS, Python version, log output). Include what you tried and any error tracebacks.

License
-------
This project uses a proprietary license (see repository top-level LICENSE or contact the project owner).

---

Last updated: November 19, 2025
