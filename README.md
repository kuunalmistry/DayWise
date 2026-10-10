<div align="center">

# DayWIse

### Local Development Edition

**Organize. Manage. Store. Study.**

A Flask-based student productivity application for managing assignments, subtasks, subjects, and academic files from one local workspace.

</div>

---

## About

This version of DayWIse is intentionally **cloud-independent**. It is designed for local development and future product upgrades without requiring Azure, AWS, Cloudflare, MySQL, or any cloud credentials.

The original cloud deployment architecture can remain documented separately for the project presentation. This local edition is the development baseline for improving the application itself.

## Local Architecture

```text
+---------------------------+
|       DayWIse UI        |
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

### Local replacements

| Previous deployment component | Local development replacement |
|---|---|
| Azure Database for MySQL | SQLite (`studysync.db`) |
| AWS S3 | `uploads/` directory |
| Azure App Service | Flask development server |
| Cloudflare edge layer | Not required locally |
| Application Insights | Flask console/debug logging |

## Features

- Dashboard with assignment statistics and weekly activity
- Assignment creation, editing, deletion, and completion
- Assignment priorities and due-date indicators
- Assignment subtasks and progress tracking
- Subject organization
- Local academic file uploads
- File search and category filtering
- Local file download and deletion
- Account sign-up, sign-in, and sign-out
- Private per-account assignments and study files
- Editable profile details and local profile photos
- Six account-saved glass color themes with account-saved light and dark appearance modes
- Mobile-specific layouts and touch-friendly controls
- Responsive web interface
- SQLite database with SQLAlchemy ORM

Choose Light or Dark glass mode and pair it with Blue, Purple, Red, Yellow, or Green from **Settings → Glass appearance**. Black is available only with Dark mode.
Both preferences are stored on the signed-in account; Light and Blue remain the defaults.

## Requirements

- Python 3.10+
- pip

No MySQL server, AWS account, Azure account, Cloudflare configuration, or cloud credentials are required.

## Run Locally

### 1. Open the project

```powershell
cd StudySync
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

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

### 5. Start DayWIse

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

The actual uploaded files are stored here. The database stores their metadata and generated local filename.

## Security Notes

- `.env` is ignored by Git.
- Set a private `SECRET_KEY` in `.env` before using accounts beyond local development.
- Local databases are ignored by Git.
- Uploaded files are ignored by Git.
- No AWS, Azure, MySQL, or cloud credentials are required by the application.
- `secure_filename()` is used before local file storage.
- Maximum upload size is 10 MB.

## Development Direction

This local version is the foundation for the next DayWIse development phase. The application can now be upgraded independently of the cloud deployment architecture, including:

- premium UI/UX
- richer dashboard analytics
- improved assignment workflows
- calendar and planning features
- enhanced file management
- notes and study workflows
- animations and micro-interactions
- better responsive behavior
- additional productivity features

The deployment architecture can be reintroduced later when the upgraded application is ready for production.
