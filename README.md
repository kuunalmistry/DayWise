<div align="center">

# DayWise

### Local Development & Cloud Deployment

**Organize. Manage. Store. Study.**

A Flask-based student productivity application for managing assignments, subtasks, subjects, and academic files from one local workspace.

</div>

---

## About

DayWise runs locally with SQLite and the `uploads/` directory. In production it can use PostgreSQL through `DATABASE_URL` and the private Supabase Storage bucket `daywise-files`. Database access and the Supabase service-role key remain server-side.

## Architecture

```text
+---------------------------+
|       DayWise UI        |
|     Flask + Jinja/CSS     |
+-------------+-------------+
              |
              v
+---------------------------+
|      Flask Application    |
|          app.py           |
+-------------+-------------+
              |
        +-----+------+
        |            |
        v            v
+---------------+  +----------------+
| SQLite        |  | Local Storage  |
| studysync.db  |  | uploads/       |
+---------------+  +----------------+
```

### Database and storage modes

| Component | Local development | Production |
|---|---|---|
| Database | SQLite (`studysync.db`) | PostgreSQL (`DATABASE_URL`) |
| File storage | `uploads/` directory | Private Supabase Storage bucket |
| Web server | Flask development server | Gunicorn |

## Features

- Dashboard with assignment statistics and weekly activity
- Assignment creation, editing, deletion, and completion
- Assignment priorities and due-date indicators
- Assignment subtasks and progress tracking
- Subject organization
- Academic file uploads
- File search and category filtering
- Local file download and deletion
- Account sign-up, sign-in, and sign-out
- Private per-account assignments and study files
- Editable profile details and profile photos
- Six account-saved glass color themes with account-saved light and dark appearance modes
- Mobile-specific layouts and touch-friendly controls
- Responsive web interface
- SQLite/PostgreSQL database access with SQLAlchemy ORM

Choose Light or Dark glass mode and pair it with Blue, Purple, Red, Yellow, or Green from **Settings → Glass appearance**. Black is available only with Dark mode.
Both preferences are stored on the signed-in account; Light and Blue remain the defaults.

## Requirements

- Python 3.10+
- pip

Local development needs no cloud credentials. Production requires a Render web service and Supabase PostgreSQL and Storage credentials.

## Run Locally

### 1. Open the project

```powershell
cd DayWise
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

Optional: copy `.env.example` to `.env` and set a private local `SECRET_KEY`.

### 3. Activate it on Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

Run the regression suite from the repository root with:

```powershell
python -m unittest discover -s tests -v
```

### 5. Start DayWise

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The first startup automatically creates `studysync.db` and the required tables.
Open `http://127.0.0.1:5000/signup` to create your account. Existing local
assignments and file records are assigned to the first account created after
authentication is added; accounts created afterward have separate workspaces.

Local mode always uses `studysync.db` and `uploads/`; it does not import or
modify production data. Set `SECRET_KEY` locally in `.env` when you want a
non-default development session key.

## Local Data

### Database

```text
studysync.db
```

All assignments, subtasks, and uploaded-file metadata are stored here.

### Uploaded files

```text
uploads/
```

The actual uploaded files are stored here. The database stores their metadata and generated local filename. This directory is for local development only; Render's filesystem is not treated as persistent.

## Deploy to Render with Supabase

Based on the inspected models and [`schema.sql`](./schema.sql), the current
`User`, `Assignment`, `SubTask`, and `UploadedFile` models use the existing
table and column names. `schema.sql` is a SQLite reference schema, not a
PostgreSQL deployment script; confirm that the live Supabase schema has the
same table/column shape before running migrations. No new column is needed for
Supabase Storage: `users.avatar_filename` and
`uploaded_files.stored_filename` hold opaque storage keys. Do not run a local
SQLite-to-PostgreSQL data import as part of deployment.

### Required Render environment variables

Set these in **Render → your Web Service → Environment**:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | A random value with at least 32 characters. Generate one locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste it into Render. |
| `DATABASE_URL` | Supabase PostgreSQL connection string. Prefer the Supabase **Session pooler** connection string when the Render network cannot connect to the direct endpoint; preserve the supplied credentials and URL-encode special characters. |
| `SUPABASE_URL` | Supabase project URL, for example `https://your-project.supabase.co`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase server-side service-role key. Keep it only in Render's environment; never put it in templates, JavaScript, or public files. |
| `SUPABASE_STORAGE_BUCKET` | `daywise-files` (optional; this is the default). The bucket must remain private. |

The app normalizes Render's legacy `postgres://` URLs to the psycopg 3 SQLAlchemy
driver and requires SSL for PostgreSQL connections. Production startup fails
clearly when its required settings are missing or the secret key is too short.
Secure, HTTP-only, SameSite=Lax session cookies are enabled in production.
Successful sign-up logs the new account in, and login sessions refresh while
active and remain on the same device for up to 30 days.

### Render service settings

Create a **Web Service** connected to this repository, choose a supported
Python runtime, and configure:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
Health check path: /healthz
```

The `/healthz` endpoint is public and checks database connectivity. Gunicorn
does not run Flask's debug server. Do not use the Render filesystem for
assignment files or avatars; production file bytes are uploaded to and fetched
from the private Supabase bucket through authenticated, ownership-checked Flask
routes.

### Schema setup

This repository's schema already matches the application's models. The
`flask --app app init-db` command creates missing tables and applies only the
existing additive compatibility updates; it does not drop or recreate tables.
For a fresh/older database, run it once in an environment configured with the
production variables before starting the web service. It is not a local data
migration, and deployment does not copy `studysync.db` or `uploads/` to Supabase.
Do not run it if your database schema is managed separately without first
reviewing the additive updates in `initialize_database()`.

### Private storage access

Each stored object gets a per-user, UUID-based path. The database records that
path and file metadata. Downloads and avatar requests pass through authenticated
Flask endpoints; the app fetches bytes server-side with the service-role key,
so the bucket remains private and no signed bearer URL is exposed to the browser.

## Security Notes

- `.env` and secret-key files are ignored by Git.
- Production secrets belong in Render environment variables, not in source control.
- Local databases are ignored by Git.
- Uploaded files are ignored by Git.
- Local filenames are passed through `secure_filename()`.
- Maximum upload size is 10 MB.

## Development Direction

DayWise can continue to be developed in either local or production mode, including:

- premium UI/UX
- richer dashboard analytics
- improved assignment workflows
- calendar and planning features
- enhanced file management
- notes and study workflows
- animations and micro-interactions
- better responsive behavior
- additional productivity features
