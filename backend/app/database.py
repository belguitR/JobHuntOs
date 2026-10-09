"""Local relational storage with versioned migrations and enforced foreign keys."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS countries (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE, code TEXT NOT NULL UNIQUE,
 priority TEXT NOT NULL DEFAULT 'Medium', notes TEXT NOT NULL DEFAULT '', visa_notes TEXT NOT NULL DEFAULT '',
 language_notes TEXT NOT NULL DEFAULT '', target_roles TEXT NOT NULL DEFAULT '', salary_notes TEXT NOT NULL DEFAULT '',
 job_boards TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS companies (
 id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE RESTRICT,
 name TEXT NOT NULL, website TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', linkedin TEXT NOT NULL DEFAULT '',
 sponsorship TEXT NOT NULL DEFAULT 'Unknown', notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(country_id,name));
CREATE TABLE IF NOT EXISTS resumes (
 id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE RESTRICT,
 name TEXT NOT NULL, language TEXT NOT NULL DEFAULT '', target_role TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
 filename TEXT NOT NULL, storage_key TEXT NOT NULL UNIQUE, mime TEXT NOT NULL, sha256 TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1, parent_id INTEGER REFERENCES resumes(id) ON DELETE RESTRICT,
 archived INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS applications (
 id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
 resume_id INTEGER REFERENCES resumes(id) ON DELETE RESTRICT, title TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'Saved', priority TEXT NOT NULL DEFAULT 'Medium', source TEXT NOT NULL DEFAULT '',
 job_url TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', salary_notes TEXT NOT NULL DEFAULT '',
 location TEXT NOT NULL DEFAULT '', date_applied TEXT, first_response_at TEXT, notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contacts (
 id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE RESTRICT,
 company_id INTEGER REFERENCES companies(id) ON DELETE RESTRICT, name TEXT NOT NULL,
 title TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', linkedin TEXT NOT NULL DEFAULT '',
 contact_type TEXT NOT NULL DEFAULT 'Recruiter', relationship TEXT NOT NULL DEFAULT 'Discovered',
 notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS interactions (
 id INTEGER PRIMARY KEY, contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
 application_id INTEGER REFERENCES applications(id) ON DELETE RESTRICT,
 kind TEXT NOT NULL DEFAULT 'Note', content TEXT NOT NULL, occurred_at TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS followups (
 id INTEGER PRIMARY KEY, country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE RESTRICT,
 application_id INTEGER REFERENCES applications(id) ON DELETE RESTRICT,
 contact_id INTEGER REFERENCES contacts(id) ON DELETE RESTRICT, title TEXT NOT NULL, due_date TEXT NOT NULL,
 completed INTEGER NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS interviews (
 id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE RESTRICT,
 title TEXT NOT NULL, scheduled_at TEXT NOT NULL, duration_minutes INTEGER NOT NULL DEFAULT 60,
 interviewer TEXT NOT NULL DEFAULT '', meeting_url TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Scheduled',
 notes_before TEXT NOT NULL DEFAULT '', notes_after TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS status_history (
 id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
 previous_status TEXT, new_status TEXT NOT NULL, changed_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_companies_country ON companies(country_id);
CREATE INDEX IF NOT EXISTS ix_contacts_country ON contacts(country_id);
CREATE INDEX IF NOT EXISTS ix_applications_company ON applications(company_id);
CREATE INDEX IF NOT EXISTS ix_followups_due ON followups(due_date,completed);
CREATE INDEX IF NOT EXISTS ix_history_application ON status_history(application_id);
INSERT OR IGNORE INTO schema_version VALUES(1);
"""


def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.executescript(SCHEMA)


@contextmanager
def connect(path: Path):
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    try:
        with connection:
            yield connection
    finally:
        connection.close()
