"""Commands for a small personal job-search workflow."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from email.utils import parseaddr
from pathlib import Path
from urllib.parse import urlparse

from . import contacts, gmail, profile, scoring, sources, storage

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "jobhunt.sqlite3"


def _paths(args) -> tuple[Path, Path, Path]:
    root = Path(args.home).resolve()
    return root / "data" / "jobhunt.sqlite3", root / "profile.json", root / "sources.json"


def _read_sources(path: Path) -> list[sources.Source]:
    if not path.exists():
        raise ValueError(f"Source file not found: {path}. Run 'jobhunt init'.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("sources.json must contain a JSON array.")
    configured = [sources.Source(**item) for item in data]
    placeholders = {"company-board-token", "company-site-token", "company-board-name"}
    if any(source.board in placeholders for source in configured):
        raise ValueError(
            "sources.json still contains placeholder board names. Replace it with real public board tokens."
        )
    return configured


def init(args) -> None:
    root = Path(args.home).resolve()
    root.mkdir(parents=True, exist_ok=True)
    database, profile_path, sources_path = _paths(args)
    storage.initialize(database)
    for name, target in (("profile.example.json", profile_path), ("sources.example.json", sources_path)):
        if not target.exists():
            shutil.copyfile(ROOT / name, target)
            print(f"Created {target}")
    print("Ready. Edit profile.json and sources.json, then run: jobhunt find")


def find(args) -> None:
    database, profile_path, sources_path = _paths(args)
    storage.initialize(database)
    person = profile.load(profile_path)
    configured_sources = _read_sources(sources_path)
    if not configured_sources:
        print("No sources configured. Add real public boards to sources.json first.")
        return
    added = updated = 0
    with storage.connect(database) as connection:
        for source in configured_sources:
            try:
                records = sources.read(source)
            except sources.SourceError as error:
                print(f"{source.label}: skipped — {error}", file=sys.stderr)
                continue
            for job in records:
                job["discovered_at"] = storage.timestamp()
                job["updated_at"] = storage.timestamp()
                job["score"], reasons = scoring.score(job, person)
                job["score_reasons"] = "\n".join(reasons)
                _, is_new = storage.upsert_job(connection, job)
                added += int(is_new)
                updated += int(not is_new)
            print(f"{source.label}: read {len(records)} jobs")
    print(f"Done: {added} new, {updated} refreshed.")


def jobs(args) -> None:
    database, _, _ = _paths(args)
    storage.initialize(database)
    query = "SELECT id, score, job_title, company_name, location, status, job_url, source_label FROM jobs"
    values: list = []
    filters = []
    if args.status:
        filters.append("status=?")
        values.append(args.status)
    if args.min_score is not None:
        filters.append("score>=?")
        values.append(args.min_score)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY score DESC, discovered_at DESC LIMIT ?"
    values.append(args.limit)
    with storage.connect(database) as connection:
        records = connection.execute(query, values).fetchall()
    if not records:
        print("No jobs found. Run 'jobhunt find' or change your filters.")
        return
    for job in records:
        print(f"[{job['id']:>3}] {job['score']:>3}/100  {job['job_title']} — {job['company_name']}")
        print(
            f"      {job['location'] or 'Location unknown'} | {job['status']} | "
            f"Source: {job['source_label']} | {job['job_url']}"
        )


def show(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        job = storage.row(connection, "jobs", args.job_id)
    labels = {
        "company_name": "Company", "job_title": "Title", "source_label": "Source", "job_url": "Job URL", "location": "Location",
        "workplace_type": "Workplace", "salary_text": "Salary", "posted_at": "Posted", "status": "Status",
        "score": "Score", "score_reasons": "Score explanation", "description": "Description",
    }
    for key, label in labels.items():
        print(f"\n{label}:\n{job[key] or 'Unknown'}")


def set_status(args) -> None:
    allowed = {"new", "interesting", "ignored", "applied", "contacted"}
    if args.status not in allowed:
        raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        storage.row(connection, "jobs", args.job_id)
        connection.execute("UPDATE jobs SET status=?, updated_at=? WHERE id=?", (args.status, storage.timestamp(), args.job_id))
    print(f"Job #{args.job_id} marked {args.status}.")


def add_cv(args) -> None:
    cv_path = Path(args.path).resolve()
    if not cv_path.is_file() or cv_path.suffix.casefold() != ".pdf":
        raise ValueError("CV must be an existing PDF file.")
    database, _, _ = _paths(args)
    storage.initialize(database)
    with storage.connect(database) as connection:
        connection.execute(
            "INSERT INTO cvs(label,path,created_at) VALUES (?,?,?)",
            (args.label, str(cv_path), storage.timestamp()),
        )
    print(f"Saved CV '{args.label}'.")


def cvs(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        records = connection.execute("SELECT id,label,path FROM cvs ORDER BY id").fetchall()
    for cv in records:
        print(f"[{cv['id']}] {cv['label']} — {cv['path']}")


def prepare(args) -> None:
    database, profile_path, _ = _paths(args)
    person = profile.load(profile_path)
    with storage.connect(database) as connection:
        job = storage.row(connection, "jobs", args.job_id)
        cv = storage.row(connection, "cvs", args.cv_id)
    print("WRITER PACKET — use only the verified facts below. Do not invent metrics or skills.\n")
    print(f"JOB #{job['id']}: {job['job_title']} at {job['company_name']}")
    print(f"Job link: {job['job_url']}\nLocation: {job['location'] or 'Unknown'}")
    print(f"\nCV: {cv['label']} ({cv['path']})")
    print(f"\nAvailability: {person.get('availability', 'Not specified')}")
    print("\nVERIFIED FACTS:")
    print("\n".join(f"- {fact}" for fact in person["facts"]))
    print(f"\nJOB DESCRIPTION:\n{job['description']}")


def discover_contact(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        job = storage.row(connection, "jobs", args.job_id)
    try:
        page = contacts.fetch_public_page(job["job_url"])
    except RuntimeError as error:
        page = ""
        print(f"Note: {error}", file=sys.stderr)
    emails = contacts.public_emails(job["description"], page)
    with storage.connect(database) as connection:
        connection.execute("DELETE FROM contacts WHERE job_id=?", (args.job_id,))
    if not emails:
        print("No public email found. Use the official application page; no address was guessed.")
        return
    with storage.connect(database) as connection:
        saved = [storage.save_contact(connection, args.job_id, email, job["job_url"]) for email in emails]
    for contact in saved:
        print(f"[{contact['id']}] {contact['email']} — source: {contact['source_url']}")


def contacts_list(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        records = connection.execute(
            "SELECT c.id,c.email,c.source_url,j.job_title,j.company_name FROM contacts c "
            "JOIN jobs j ON j.id=c.job_id ORDER BY c.id DESC"
        ).fetchall()
    if not records:
        print("No public contacts saved yet.")
        return
    for contact in records:
        print(f"[{contact['id']}] {contact['email']} — {contact['company_name']} | {contact['job_title']}")
        print(f"    {contact['source_url']}")


def save_draft(args) -> None:
    body_path = Path(args.body_file).resolve()
    if not body_path.is_file():
        raise ValueError(f"Draft body file not found: {body_path}")
    body = body_path.read_text(encoding="utf-8").strip()
    if not body:
        raise ValueError("Draft body cannot be empty.")
    database, _, _ = _paths(args)
    if args.contact_id:
        if args.to or args.contact_source:
            raise ValueError("Use either --contact-id or --to with --contact-source, not both.")
        with storage.connect(database) as connection:
            contact = storage.row(connection, "contacts", args.contact_id)
        recipient = contact["email"]
        contact_source = contact["source_url"]
    else:
        recipient = args.to
        contact_source = args.contact_source
    if bool(recipient) != bool(contact_source):
        raise ValueError("Provide both --to and --contact-source, or neither to save a needs-contact draft.")
    if recipient:
        _, address = parseaddr(recipient)
        if address != recipient or "@" not in address:
            raise ValueError("Recipient must be one valid email address.")
        source_url = urlparse(contact_source)
        if source_url.scheme not in {"https", "http"} or not source_url.netloc:
            raise ValueError("Provide --contact-source with the public webpage where the email is listed.")
    with storage.connect(database) as connection:
        job = storage.row(connection, "jobs", args.job_id)
        storage.row(connection, "cvs", args.cv_id)
        recent = storage.recent_company_draft(connection, job["company_name"])
        if recipient and recent:
            raise ValueError(
                f"Company already has {recent['state']} draft #{recent['id']} from "
                f"{recent['created_at'][:10]}. Wait 30 days or continue that conversation."
            )
        connection.execute(
            "INSERT INTO drafts(job_id,cv_id,recipient,recipient_source,subject,body,state,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                args.job_id,
                args.cv_id,
                recipient,
                contact_source,
                args.subject,
                body,
                "pending" if recipient else "needs_contact",
                storage.timestamp(),
            ),
        )
        draft_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    if recipient:
        print(f"Saved pending draft #{draft_id}. It cannot send until you run 'jobhunt send {draft_id}'.")
    else:
        print(f"Saved draft #{draft_id} as needs_contact. Add a verified contact before it can send.")


def attach_contact(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        draft = storage.row(connection, "drafts", args.draft_id)
        contact = storage.row(connection, "contacts", args.contact_id)
        if draft["state"] != "needs_contact":
            raise ValueError(f"Draft #{args.draft_id} is {draft['state']}; it cannot receive a new contact.")
        if contact["job_id"] != draft["job_id"]:
            raise ValueError("The contact must have been discovered for the same job as the draft.")
        job = storage.row(connection, "jobs", draft["job_id"])
        recent = storage.recent_company_draft(connection, job["company_name"])
        if recent:
            raise ValueError(
                f"Company already has {recent['state']} draft #{recent['id']} from "
                f"{recent['created_at'][:10]}."
            )
        connection.execute(
            "UPDATE drafts SET recipient=?, recipient_source=?, state='pending' WHERE id=?",
            (contact["email"], contact["source_url"], args.draft_id),
        )
    print(f"Draft #{args.draft_id} is pending approval for {contact['email']}.")


def drafts(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        records = connection.execute(
            "SELECT d.id,d.state,d.recipient,d.subject,j.job_title,j.company_name,c.label FROM drafts d "
            "JOIN jobs j ON j.id=d.job_id JOIN cvs c ON c.id=d.cv_id ORDER BY d.id DESC"
        ).fetchall()
    for draft in records:
        recipient = draft["recipient"] or "No verified recipient yet"
        print(f"[{draft['id']}] {draft['state']} — {recipient} | {draft['subject']}")
        print(f"    {draft['job_title']} at {draft['company_name']} | CV: {draft['label']}")


def send(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        draft = storage.row(connection, "drafts", args.draft_id)
        cv = storage.row(connection, "cvs", draft["cv_id"])
    if draft["state"] != "pending":
        raise ValueError(f"Draft #{args.draft_id} is already {draft['state']}; it cannot be sent again.")
    print(f"To: {draft['recipient']}\nSubject: {draft['subject']}\nCV: {cv['path']}\n\n{draft['body']}\n")
    confirmation = input("Type SEND to approve this exact email: ").strip()
    if confirmation != "SEND":
        print("Not sent. The draft remains pending.")
        return
    message_id = gmail.send(
        credentials_path=Path(args.credentials).resolve(), token_path=Path(args.token).resolve(),
        recipient=draft["recipient"], subject=draft["subject"], body=draft["body"], cv=Path(cv["path"]),
    )
    with storage.connect(database) as connection:
        connection.execute(
            "UPDATE drafts SET state='sent', sent_at=?, gmail_message_id=? WHERE id=?",
            (storage.timestamp(), message_id, args.draft_id),
        )
        connection.execute(
            "UPDATE jobs SET status='contacted', updated_at=? WHERE id=?",
            (storage.timestamp(), draft["job_id"]),
        )
    print(f"Sent Gmail message {message_id}. Job marked contacted.")


def create_gmail_draft(args) -> None:
    database, _, _ = _paths(args)
    with storage.connect(database) as connection:
        draft = storage.row(connection, "drafts", args.draft_id)
        cv = storage.row(connection, "cvs", draft["cv_id"])
    if draft["state"] != "pending":
        raise ValueError(f"Draft #{args.draft_id} is {draft['state']}; attach a public contact first.")
    if draft["gmail_draft_id"]:
        print(f"Draft #{args.draft_id} already exists in Gmail as {draft['gmail_draft_id']}.")
        return
    gmail_draft_id = gmail.create_draft(
        credentials_path=Path(args.credentials).resolve(), token_path=Path(args.token).resolve(),
        recipient=draft["recipient"], subject=draft["subject"], body=draft["body"], cv=Path(cv["path"]),
    )
    with storage.connect(database) as connection:
        connection.execute("UPDATE drafts SET gmail_draft_id=? WHERE id=?", (gmail_draft_id, args.draft_id))
    print(f"Created Gmail draft {gmail_draft_id}. It has not been sent.")


def authorize_gmail(args) -> None:
    gmail.authorize(
        credentials_path=Path(args.credentials).resolve(), token_path=Path(args.token).resolve()
    )
    print("Gmail authorized locally. You can now create Gmail drafts when a draft has a public contact.")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="jobhunt", description="Local personal job-search workflow")
    root.add_argument("--home", default=str(ROOT), help="Directory containing profile, sources and local data")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init").set_defaults(function=init)
    commands.add_parser("find").set_defaults(function=find)
    list_parser = commands.add_parser("jobs")
    list_parser.add_argument("--min-score", type=int)
    list_parser.add_argument("--status")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.set_defaults(function=jobs)
    one = commands.add_parser("show")
    one.add_argument("job_id", type=int)
    one.set_defaults(function=show)
    status = commands.add_parser("set-status")
    status.add_argument("job_id", type=int)
    status.add_argument("status")
    status.set_defaults(function=set_status)
    cv = commands.add_parser("add-cv")
    cv.add_argument("label")
    cv.add_argument("path")
    cv.set_defaults(function=add_cv)
    commands.add_parser("cvs").set_defaults(function=cvs)
    packet = commands.add_parser("prepare")
    packet.add_argument("job_id", type=int)
    packet.add_argument("--cv", dest="cv_id", required=True, type=int)
    packet.set_defaults(function=prepare)
    contact = commands.add_parser("discover-contact")
    contact.add_argument("job_id", type=int)
    contact.set_defaults(function=discover_contact)
    commands.add_parser("contacts").set_defaults(function=contacts_list)
    draft = commands.add_parser("save-draft")
    draft.add_argument("job_id", type=int)
    draft.add_argument("--cv", dest="cv_id", required=True, type=int)
    draft.add_argument("--to", default="")
    draft.add_argument("--contact-source", default="")
    draft.add_argument("--contact-id", type=int)
    draft.add_argument("--subject", required=True)
    draft.add_argument("--body-file", required=True)
    draft.set_defaults(function=save_draft)
    attach = commands.add_parser("attach-contact")
    attach.add_argument("draft_id", type=int)
    attach.add_argument("--contact-id", required=True, type=int)
    attach.set_defaults(function=attach_contact)
    commands.add_parser("drafts").set_defaults(function=drafts)
    send_parser = commands.add_parser("send")
    send_parser.add_argument("draft_id", type=int)
    send_parser.add_argument("--credentials", default=str(ROOT / "credentials.json"))
    send_parser.add_argument("--token", default=str(ROOT / "token.json"))
    send_parser.set_defaults(function=send)
    gmail_draft = commands.add_parser("create-gmail-draft")
    gmail_draft.add_argument("draft_id", type=int)
    gmail_draft.add_argument("--credentials", default=str(ROOT / "credentials.json"))
    gmail_draft.add_argument("--token", default=str(ROOT / "token.json"))
    gmail_draft.set_defaults(function=create_gmail_draft)
    gmail_auth = commands.add_parser("gmail-auth")
    gmail_auth.add_argument("--credentials", default=str(ROOT / "credentials.json"))
    gmail_auth.add_argument("--token", default=str(ROOT / "token.json"))
    gmail_auth.set_defaults(function=authorize_gmail)
    return root


def main(argv=None) -> None:
    args = parser().parse_args(argv)
    try:
        if args.command != "init":
            database, _, _ = _paths(args)
            storage.initialize(database)
        args.function(args)
    except (RuntimeError, ValueError, OSError, sqlite3.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
