-- StudySync Local database reference schema.
-- The Flask application creates/updates the SQLite database automatically
-- through SQLAlchemy, so you normally do not need to run this file manually.

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    bio VARCHAR(300) NOT NULL DEFAULT '',
    avatar_filename VARCHAR(255),
    theme VARCHAR(20) NOT NULL DEFAULT 'blue',
    theme_mode VARCHAR(10) NOT NULL DEFAULT 'light'
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    priority VARCHAR(20) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME,
    completed_at DATETIME,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
);

CREATE TABLE uploaded_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    subject VARCHAR(100),
    uploaded_at DATETIME,
    user_id INTEGER REFERENCES users(id)
);
