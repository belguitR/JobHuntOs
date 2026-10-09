"""SQLite persistence for discovered jobs, CVs and approval-gated email drafts."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE,
    dedupe_key TEXT NOT NULL UNIQUE,
    source_kind TEXT NOT NULL,
    source_label TEXT NOT NULL,
    external_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_url TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    workplace_type TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    salary_text TEXT NOT NULL DEFAULT '',
    language_requirements TEXT NOT NULL DEFAULT '',
    posted_at TEXT NOT NULL DEFAULT '',
    discovered_at TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    score_reasons TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    content_hash TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cvs (
    id INTEGER PRIMARY KEY,
    label TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
    email TEXT NOT NULL,
    source_url TEXT NOT NULL,
    discovered_at TEXT NOT NULL,
    UNIQUE(job_id, email)
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE RESTRICT,
    cv_id INTEGER NOT NULL REFERENCES cvs(id) ON DELETE RESTRICT,
    recipient TEXT NOT NULL,
    recipient_source TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    sent_at TEXT,
    gmail_message_id TEXT,
    gmail_draft_id TEXT,
    UNIQUE(job_id, recipient)
);
CREATE INDEX IF NOT EXISTS ix_jobs_score ON jobs(score DESC, discovered_at DESC);
CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS ix_drafts_state ON drafts(state);
CREATE INDEX IF NOT EXISTS ix_contacts_job ON contacts(job_id);
"""


def timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@contextmanager
def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path: Path) -> None:
    with connect(path) as connection:
        connection.executescript(SCHEMA)
        draft_columns = {row["name"] for row in connection.execute("PRAGMA table_info(drafts)")}
        if "gmail_draft_id" not in draft_columns:
            connection.execute("ALTER TABLE drafts ADD COLUMN gmail_draft_id TEXT")


def upsert_job(connection: sqlite3.Connection, job: dict) -> tuple[int, bool]:
    existing = connection.execute(
        "SELECT id FROM jobs WHERE source_key=? OR dedupe_key=?",
        (job["source_key"], job["dedupe_key"]),
    ).fetchone()
    columns = [
        "source_key", "dedupe_key", "source_kind", "source_label", "external_id", "company_name",
        "job_title", "job_url", "location", "country", "workplace_type", "description",
        "salary_text", "language_requirements", "posted_at", "discovered_at", "score",
        "score_reasons", "content_hash", "updated_at",
    ]
    if existing:
        connection.execute(
            f"UPDATE jobs SET {','.join(f'{key}=?' for key in columns[1:])} WHERE id=?",
            [*(job[key] for key in columns[1:]), existing["id"]],
        )
        return int(existing["id"]), False
    connection.execute(
        f"INSERT INTO jobs ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        [job[key] for key in columns],
    )
    return int(connection.execute("SELECT last_insert_rowid()").fetchone()[0]), True


def row(connection: sqlite3.Connection, table: str, record_id: int):
    result = connection.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
    if result is None:
        raise ValueError(f"{table.rstrip('s').capitalize()} #{record_id} does not exist.")
    return result


def recent_company_draft(connection: sqlite3.Connection, company_name: str):
    cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat(timespec="seconds")
    return connection.execute(
        "SELECT d.id, d.state, d.created_at FROM drafts d "
        "JOIN jobs j ON j.id=d.job_id "
        "WHERE j.company_name=? COLLATE NOCASE "
        "AND d.state IN ('pending','sent') AND d.created_at>=? "
        "ORDER BY d.created_at DESC LIMIT 1",
        (company_name, cutoff),
    ).fetchone()


def save_contact(connection: sqlite3.Connection, job_id: int, email: str, source_url: str):
    connection.execute(
        "INSERT OR IGNORE INTO contacts(job_id,email,source_url,discovered_at) VALUES (?,?,?,?)",
        (job_id, email, source_url, timestamp()),
    )
    return connection.execute(
        "SELECT * FROM contacts WHERE job_id=? AND email=?", (job_id, email)
    ).fetchone()
