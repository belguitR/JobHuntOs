# Job Hunt OS

## Terminal workflow (new)

The requested job-finding and approval-gated outreach tool lives in [cli](cli/README.md). It is local, terminal-first and independent from the older web workspace below. It reads only configured public ATS boards, stores data in its own SQLite file, and cannot send an email unless someone types `SEND` after seeing the recipient, content and attached CV.

A local country-based job-search workspace. Countries own companies, contacts and CVs; applications belong to companies. All screens use saved API records, with no seeded metrics or fake applications.

## Start

With dependencies installed, run `./start.ps1` from PowerShell. Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs.

Install backend dependencies with `python -m venv .venv` then `.venv/Scripts/python -m pip install -r requirements.txt` from backend. Install frontend dependencies with `npm ci` from frontend. See each folder's README for manual startup.

Alternative: `docker compose up --build`. Containers expose the same loopback ports and persist to backend/data. Docker is optional.

## Features

- Country strategy workspaces with nested company, contact, CV, application and follow-up views
- Company profiles with applications and contacts
- Applications with table/board views, filters, notes, exact CV selection, stage history and recorded response dates
- Contacts with LinkedIn/email links, conversation logs and follow-ups
- CV upload, download, PDF preview, DOCX text editing into new versions and archival
- Interviews with local-time scheduling, preparation and feedback
- Follow-up completion/reopening, global search, analytics and JSON records export
- Chrome/Edge extension for confirmed job/contact capture and optional submission hints

Load `frontend/extension` as an unpacked browser extension; see its README. No automatic tracking occurs until you install and enable it.

Run backend tests with `python -m pytest -q` in backend; run `npm run build` in frontend. Frontend and backend remain separate local Git repositories. No remote push has been performed.

This local workspace has no authentication and should not be exposed publicly. Back up backend/data to preserve the database and CV files. JSON export covers records only.
