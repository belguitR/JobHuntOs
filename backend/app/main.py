"""Local-only API. The web client uses a same-origin development proxy."""

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError

from .database import connect, initialize
from .documents import MAX_SIZE, document_parts, editable_runs, rewrite, store_resume
from .schemas import MODELS, ResumeMetadata
from .service import get, now, save

BASE_DIR = Path(__file__).resolve().parents[1]


class EditDocument(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    changes: dict[str, str]


def create_app(database_path=None, upload_dir=None):
    database_path = Path(
        database_path or os.environ.get("JOBHUNT_DATABASE", BASE_DIR / "data" / "jobhunt.sqlite3")
    )
    upload_dir = Path(upload_dir or BASE_DIR / "data" / "uploads")
    initialize(database_path)
    app = FastAPI(title="Job Hunt OS API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_origin_regex=r"^(chrome-extension|extension)://[a-z]+$",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValidationError)
    async def validation_error(request, error):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()
                )
            },
        )

    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error(request, error):
        message = (
            "This record has linked data. Remove the linked records first."
            if "FOREIGN KEY" in str(error)
            else "A record with these details already exists."
        )
        return JSONResponse(status_code=409, content={"detail": message})

    @app.get("/api/health")
    def health():
        with connect(database_path) as connection:
            connection.execute("SELECT 1")
        return {"status": "ok"}

    @app.get("/api/workspace")
    def workspace():
        with connect(database_path) as connection:
            result = {
                table: [
                    dict(row)
                    for row in connection.execute(f"SELECT * FROM {table} ORDER BY id DESC")
                ]
                for table in [*MODELS, "resumes", "status_history"]
            }
            for cv in result["resumes"]:
                cv.pop("storage_key")
        return result

    @app.get("/api/export")
    def export():
        return JSONResponse(
            workspace(),
            headers={"Content-Disposition": 'attachment; filename="job-hunt-records.json"'},
        )

    @app.post("/api/resumes/upload", status_code=201)
    async def upload(
        country_id: int = Form(...),
        name: str = Form(...),
        language: str = Form(""),
        target_role: str = Form(""),
        file: UploadFile = File(...),
    ):
        metadata = ResumeMetadata(name=name, language=language, target_role=target_role)
        content = await file.read(MAX_SIZE + 1)
        await file.close()
        if not content or len(content) > MAX_SIZE:
            raise HTTPException(422, "Upload a nonempty file up to 15 MB")
        filename = Path((file.filename or "").replace("\\", "/")).name
        extension = Path(filename).suffix.lower()
        if extension == ".docx":
            document_parts(content).close()
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif extension == ".pdf" and content.startswith(b"%PDF-"):
            mime = "application/pdf"
        else:
            raise HTTPException(422, "Only valid PDF and DOCX files are supported")
        with connect(database_path) as connection:
            get(connection, "countries", country_id)
            result = store_resume(
                connection,
                upload_dir,
                {
                    **metadata.model_dump(),
                    "country_id": country_id,
                    "filename": filename,
                    "mime": mime,
                    "version": 1,
                },
                content,
            )
            result.pop("storage_key")
            return result

    @app.get("/api/resumes/{record_id}/file")
    def download(record_id: int, preview: bool = False):
        with connect(database_path) as connection:
            cv = get(connection, "resumes", record_id)
        path = upload_dir / cv["storage_key"]
        if not path.is_file():
            raise HTTPException(404, "The CV file is missing from storage")
        return FileResponse(
            path,
            filename=cv["filename"],
            media_type=cv["mime"],
            content_disposition_type="inline"
            if preview and cv["mime"] == "application/pdf"
            else "attachment",
        )

    @app.get("/api/resumes/{record_id}/text")
    def resume_text(record_id: int):
        with connect(database_path) as connection:
            cv = get(connection, "resumes", record_id)
        if not cv["filename"].lower().endswith(".docx"):
            raise HTTPException(
                422, "Text editing supports DOCX. PDFs can be previewed and downloaded."
            )
        return editable_runs((upload_dir / cv["storage_key"]).read_bytes())

    @app.post("/api/resumes/{record_id}/versions", status_code=201)
    def edit_resume(record_id: int, payload: EditDocument):
        with connect(database_path) as connection:
            cv = get(connection, "resumes", record_id)
            if not cv["filename"].lower().endswith(".docx"):
                raise HTTPException(422, "Only DOCX text can be edited")
            content = rewrite((upload_dir / cv["storage_key"]).read_bytes(), payload.changes)
            data = {
                key: cv[key]
                for key in [
                    "country_id",
                    "language",
                    "target_role",
                    "notes",
                    "mime",
                    "filename",
                ]
            }
            result = store_resume(
                connection,
                upload_dir,
                {
                    **data,
                    "name": payload.name.strip(),
                    "version": cv["version"] + 1,
                    "parent_id": record_id,
                },
                content,
            )
            result.pop("storage_key")
            return result

    @app.patch("/api/resumes/{record_id}")
    def resume_metadata(record_id: int, payload: dict):
        with connect(database_path) as connection:
            old = get(connection, "resumes", record_id)
            data = ResumeMetadata.model_validate(
                {**{key: old[key] for key in ResumeMetadata.model_fields}, **payload}
            ).model_dump()
            connection.execute(
                f"UPDATE resumes SET {','.join(f'{key}=?' for key in data)}, updated_at=? WHERE id=?",
                [*data.values(), now(), record_id],
            )
            result = get(connection, "resumes", record_id)
            result.pop("storage_key")
            return result

    @app.get("/api/applications/{record_id}/history")
    def history(record_id: int):
        with connect(database_path) as connection:
            get(connection, "applications", record_id)
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM status_history WHERE application_id=? ORDER BY id",
                    (record_id,),
                )
            ]

    @app.get("/api/{resource}")
    def listing(resource: str):
        if resource not in MODELS:
            raise HTTPException(404)
        with connect(database_path) as connection:
            return [
                dict(row)
                for row in connection.execute(f"SELECT * FROM {resource} ORDER BY id DESC")
            ]

    @app.post("/api/{resource}", status_code=201)
    def create(resource: str, payload: dict):
        with connect(database_path) as connection:
            return save(connection, resource, payload)

    @app.patch("/api/{resource}/{record_id}")
    def update(resource: str, record_id: int, payload: dict):
        with connect(database_path) as connection:
            return save(connection, resource, payload, record_id)

    @app.delete("/api/{resource}/{record_id}", status_code=204)
    def delete(resource: str, record_id: int):
        if resource not in MODELS:
            raise HTTPException(404)
        with connect(database_path) as connection:
            get(connection, resource, record_id)
            connection.execute(f"DELETE FROM {resource} WHERE id=?", (record_id,))

    return app


app = create_app()
