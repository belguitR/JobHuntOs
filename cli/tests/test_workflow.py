from pathlib import Path
from types import SimpleNamespace

from jobhunt import cli, contacts, scoring, sources, storage


def profile():
    return {
        "name": "Rami", "target_roles": ["Backend Engineer"], "target_locations": ["Berlin"],
        "target_countries": ["Germany"], "skills": ["Python", "Go", "Terraform", "Docker"],
        "facts": ["Worked with Python."], "preferred_languages": ["English", "French"],
        "blocked_companies": [], "minimum_salary_eur": 55000,
    }


def job(**overrides):
    value = {
        "job_title": "Backend Engineer", "description": "Python Go Docker Terraform. 1+ years. English.",
        "location": "Berlin", "country": "Germany", "workplace_type": "", "salary_text": "70000 EUR",
        "language_requirements": "English", "company_name": "Acme",
    }
    value.update(overrides)
    return value


def test_scoring_is_explainable_and_penalizes_senior_roles():
    value, reasons = scoring.score(job(), profile())
    assert value >= 80
    assert any("skills:" in reason for reason in reasons)
    senior, senior_reasons = scoring.score(job(job_title="Senior Backend Engineer"), profile())
    assert senior < value
    assert any("senior" in reason for reason in senior_reasons)


def test_source_key_upsert_prevents_duplicates(tmp_path: Path):
    database = tmp_path / "jobhunt.sqlite3"
    storage.initialize(database)
    record = {
        "source_key": "greenhouse:acme:42", "dedupe_key": "acme|backend|berlin", "source_kind": "greenhouse", "source_label": "Acme",
        "external_id": "42", "company_name": "Acme", "job_title": "Backend", "job_url": "https://example.com/42",
        "location": "Berlin", "country": "Germany", "workplace_type": "", "description": "Python",
        "salary_text": "", "language_requirements": "", "posted_at": "", "discovered_at": "now",
        "score": 80, "score_reasons": "good", "content_hash": "a", "updated_at": "now",
    }
    with storage.connect(database) as connection:
        first, created = storage.upsert_job(connection, record)
        record["score"] = 90
        second, created_again = storage.upsert_job(connection, record)
        count = connection.execute("SELECT count(*) FROM jobs").fetchone()[0]
    assert created and not created_again and first == second and count == 1


def test_company_title_location_dedupes_across_sources(tmp_path: Path):
    database = tmp_path / "jobhunt.sqlite3"
    storage.initialize(database)
    record = {
        "source_key": "greenhouse:acme:42", "dedupe_key": "acme|backend|berlin", "source_kind": "greenhouse", "source_label": "Acme",
        "external_id": "42", "company_name": "Acme", "job_title": "Backend", "job_url": "https://example.com/42",
        "location": "Berlin", "country": "Germany", "workplace_type": "", "description": "Python",
        "salary_text": "", "language_requirements": "", "posted_at": "", "discovered_at": "now",
        "score": 80, "score_reasons": "good", "content_hash": "a", "updated_at": "now",
    }
    with storage.connect(database) as connection:
        first, _ = storage.upsert_job(connection, record)
        record["source_key"] = "lever:acme:99"
        second, created = storage.upsert_job(connection, record)
        count = connection.execute("SELECT count(*) FROM jobs").fetchone()[0]
    assert first == second and not created and count == 1


def test_init_creates_an_editable_local_workspace(tmp_path: Path):
    cli.init(SimpleNamespace(home=str(tmp_path)))
    assert (tmp_path / "profile.json").is_file()
    assert (tmp_path / "sources.json").is_file()
    assert (tmp_path / "data" / "jobhunt.sqlite3").is_file()


def test_company_cooldown_detects_pending_or_sent_drafts(tmp_path: Path):
    database = tmp_path / "jobhunt.sqlite3"
    storage.initialize(database)
    with storage.connect(database) as connection:
        connection.execute(
            "INSERT INTO jobs(source_key,dedupe_key,source_kind,source_label,external_id,company_name,job_title,job_url,discovered_at,updated_at) "
            "VALUES ('a','a','test','test','a','Acme','Backend','https://example.com','now','now')"
        )
        connection.execute("INSERT INTO cvs(label,path,created_at) VALUES ('CV','C:/cv.pdf','now')")
        connection.execute(
            "INSERT INTO drafts(job_id,cv_id,recipient,subject,body,created_at) VALUES (1,1,'jobs@acme.com','Hi','Body',?)",
            (storage.timestamp(),),
        )
        recent = storage.recent_company_draft(connection, "acme")
    assert recent["state"] == "pending"


def test_normalization_converts_null_ats_fields_to_empty_strings():
    source = sources.Source(kind="ashby", board="acme", label="Acme")
    normalized = sources._job(
        source, "42", "Acme", "Backend Engineer", "https://example.com/job", location=None,
        workplace_type=None, salary_text=None, language_requirements=None,
    )
    assert normalized["location"] == ""
    assert normalized["workplace_type"] == ""


def test_normalization_strips_escaped_html_from_job_descriptions():
    source = sources.Source(kind="greenhouse", board="acme", label="Acme")
    normalized = sources._job(
        source, "42", "Acme", "Backend Engineer", "https://example.com/job",
        description="&lt;p&gt;Build &amp; ship services.&lt;/p&gt;",
    )
    assert normalized["description"] == "Build & ship services."


def test_timestamp_accepts_seconds_and_milliseconds():
    assert sources._stamp(1789862116) == "2026-09-19"
    assert sources._stamp(1789862116000) == "2026-09-19"


def test_contact_finder_only_returns_explicit_public_emails():
    emails = contacts.public_emails("Email careers@acme.com or mailto:jobs@acme.com")
    assert emails == ["careers@acme.com", "jobs@acme.com"]


def test_contact_finder_ignores_script_and_telemetry_emails():
    emails = contacts.public_emails(
        '<script>const telemetry="abc@o123.ingest.sentry.io";</script><p>jobs@acme.com</p>'
    )
    assert emails == ["jobs@acme.com"]
