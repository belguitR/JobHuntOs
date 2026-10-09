# Job Hunt OS

Job Hunt OS is a planned web app for managing a job search across countries. A user will have an account, add a profile and CVs, choose target countries, discover relevant job offers, track applications, adapt a copy of a CV for an offer, and review outreach drafts. Gmail drafts and sending require the user's approval. The writing model is still an open product decision.

The agreed high-level direction is documented in [ADR 001: Initial architecture](docs/adr/001-initial-architecture.md). It is separate from the local prototypes below.

## Current state

This repository contains two working local prototypes that have **not yet been merged**:

| Folder | What works today |
| --- | --- |
| `backend/` | FastAPI API for countries, companies, CVs, applications, contacts, interviews, and follow-ups. It uses a local SQLite database. |
| `frontend/` | React interface for that application tracker. |
| `cli/` | Separate terminal tool that reads public job-board APIs, scores offers, stores job decisions, and supports Gmail drafts with explicit approval before sending. It has its own local SQLite database. |

The web app currently has no accounts, job discovery, or Gmail integration. The terminal tool has no web interface. Neither prototype is ready to be deployed as a multi-user service. The repository is a starting point for one product; the hosted architecture and data model are still to be designed.

## Product flow to design

```text
Account and profile → target countries → job discovery → match review
→ application tracking → CV adaptation → outreach draft → user approval
```

Job offers should link to their original postings. A match score should explain the criteria used; it is not a prediction of hiring. The original CV must remain intact when a version is adapted for an offer. An offer becomes an application when the user chooses to pursue it. Each user's documents, applications, and Gmail connection must remain private to that account.

## Run the existing prototypes locally

The tracker needs Python and Node.js. On Windows PowerShell, run these from the repository root:

```powershell
python -m venv backend/.venv
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm --prefix frontend ci
./start.ps1
```

Open `http://127.0.0.1:5173`; the FastAPI docs are at `http://127.0.0.1:8000/docs`.

The terminal tool is separate. From `cli/`, install `requirements.txt`, install the package with `pip install -e .`, and run `jobhunt init` to create local profile and source configuration. Then use `jobhunt find` and `jobhunt jobs` to retrieve and review offers. Its OAuth credentials, tokens, profile, source settings, and local data stay on your machine and are ignored by Git.

## Before deployment

The account model, shared database, private CV storage, background job collection, per-user Gmail authorization, and optional writing engine need to be designed and implemented. Current local data is not a deployed user account. No automatic outreach should occur without the user's approval.
