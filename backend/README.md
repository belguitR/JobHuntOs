# Job Hunt OS Backend

FastAPI + SQLite local API. Run from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API starts at http://127.0.0.1:8000 and exposes interactive docs at `/docs`.

Data is stored in `data/jobhunt.sqlite3`, with CVs in `data/uploads`. `JOBHUNT_DATABASE` can select a separate database for isolated checks. Tests use temporary databases and upload folders: `python -m pytest -q`.

Modules: `database.py` (schema), `schemas.py` (input contracts), `service.py` (aggregate rules and transactions), `documents.py` (CV storage and DOCX editing), `main.py` (routes).
