import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "test.sqlite3", tmp_path / "uploads"))


def create(client, resource, **payload):
    response = client.post(f"/api/{resource}", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def setup_country(client, name="Japan", code="JP"):
    country = create(client, "countries", name=name, code=code)
    company = create(client, "companies", name="Example Company", country_id=country["id"])
    return country, company


def docx_bytes():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Original summary</w:t></w:r><w:r><w:t>More experience</w:t></w:r></w:p></w:body></w:document>',
        )
        archive.writestr("word/styles.xml", "<styles>unchanged</styles>")
        archive.writestr("word/media/image1.png", b"unchanged-image")
    return output.getvalue()


def upload_cv(client, country_id, name="Backend CV", filename="cv.docx", content=None):
    response = client.post(
        "/api/resumes/upload",
        data={"country_id": country_id, "name": name},
        files={"file": (filename, content or docx_bytes())},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_country_aggregate_and_restart_persistence(tmp_path):
    database = tmp_path / "persistent.sqlite3"
    client = TestClient(create_app(database, tmp_path / "files"))
    country, company = setup_country(client)
    contact = create(
        client,
        "contacts",
        name="Recruiter",
        country_id=country["id"],
        company_id=company["id"],
    )
    application = create(client, "applications", title="Backend Engineer", company_id=company["id"])
    client = TestClient(create_app(database, tmp_path / "files"))
    data = client.get("/api/workspace").json()
    assert data["companies"][0]["country_id"] == country["id"]
    assert data["contacts"][0]["company_id"] == company["id"]
    assert data["contacts"][0]["id"] == contact["id"]
    assert data["applications"][0]["id"] == application["id"]
    assert len(data["status_history"]) == 1


def test_status_history_is_atomic_and_partial_updates_preserve_fields(client):
    country, company = setup_country(client)
    app = create(
        client,
        "applications",
        title="Backend",
        company_id=company["id"],
        notes="Keep these",
    )
    path = f"/api/applications/{app['id']}"
    response = client.patch(path, json={"status": "Applied"})
    assert response.status_code == 200
    assert response.json()["notes"] == "Keep these"
    assert response.json()["date_applied"]
    assert client.patch(path, json={"status": "Applied"}).status_code == 200
    assert client.patch(path, json={"status": "invented"}).status_code == 422
    history = client.get(path + "/history").json()
    assert [h["new_status"] for h in history] == ["Saved", "Applied"]


def test_cross_country_links_are_rejected(client):
    japan, japanese_company = setup_country(client)
    france, french_company = setup_country(client, "France", "FR")
    cv = upload_cv(client, japan["id"])
    app = create(client, "applications", title="France role", company_id=french_company["id"])
    assert (
        client.post(
            "/api/applications",
            json={
                "title": "Invalid",
                "company_id": french_company["id"],
                "resume_id": cv["id"],
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/contacts",
            json={
                "name": "Invalid",
                "country_id": japan["id"],
                "company_id": french_company["id"],
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/followups",
            json={
                "title": "Invalid",
                "country_id": japan["id"],
                "application_id": app["id"],
                "due_date": "2026-09-20",
            },
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/companies/{japanese_company['id']}",
            json={"country_id": france["id"]},
        ).status_code
        == 422
    )


def test_reply_followup_interview_workflow(client):
    country, company = setup_country(client)
    app = create(
        client,
        "applications",
        title="Backend",
        company_id=company["id"],
        status="Applied",
    )
    contact = create(
        client,
        "contacts",
        name="Recruiter",
        country_id=country["id"],
        company_id=company["id"],
    )
    create(
        client,
        "interactions",
        contact_id=contact["id"],
        application_id=app["id"],
        kind="Reply received",
        content="Let us schedule a call",
        occurred_at="2026-09-12T12:00:00Z",
    )
    followup = create(
        client,
        "followups",
        country_id=country["id"],
        application_id=app["id"],
        contact_id=contact["id"],
        title="Confirm time",
        due_date="2026-09-13",
    )
    assert (
        client.patch(f"/api/followups/{followup['id']}", json={"completed": True}).json()[
            "completed"
        ]
        == 1
    )
    interview = create(
        client,
        "interviews",
        application_id=app["id"],
        title="Technical interview",
        scheduled_at="2026-09-20T14:00:00Z",
    )
    assert (
        client.patch(
            f"/api/interviews/{interview['id']}",
            json={"notes_after": "Asked about indexes", "status": "Completed"},
        ).status_code
        == 200
    )
    data = client.get("/api/workspace").json()
    assert data["applications"][0]["first_response_at"] == "2026-09-12"
    assert data["interviews"][0]["notes_after"] == "Asked about indexes"


def test_deletion_cannot_orphan_related_records(client):
    country, company = setup_country(client)
    app = create(client, "applications", title="Backend", company_id=company["id"])
    assert client.delete(f"/api/countries/{country['id']}").status_code == 409
    assert client.delete(f"/api/companies/{company['id']}").status_code == 409
    assert client.delete(f"/api/applications/{app['id']}").status_code == 204
    assert client.get("/api/workspace").json()["status_history"] == []
    assert client.delete(f"/api/companies/{company['id']}").status_code == 204
    assert client.delete(f"/api/countries/{country['id']}").status_code == 204


def test_cv_text_edit_preserves_formatting_original_and_application(client):
    country, company = setup_country(client)
    cv = upload_cv(client, country["id"])
    _application = create(
        client,
        "applications",
        title="Backend",
        company_id=company["id"],
        resume_id=cv["id"],
    )
    original = client.get(f"/api/resumes/{cv['id']}/file").content
    segments = client.get(f"/api/resumes/{cv['id']}/text").json()
    response = client.post(
        f"/api/resumes/{cv['id']}/versions",
        json={
            "name": "Tailored CV",
            "changes": {segments[0]["id"]: "Updated & improved summary"},
        },
    )
    assert response.status_code == 201, response.text
    new_cv = response.json()
    assert new_cv["parent_id"] == cv["id"] and new_cv["version"] == 2
    assert new_cv["sha256"] != cv["sha256"]
    updated = client.get(f"/api/resumes/{new_cv['id']}/file").content
    with zipfile.ZipFile(io.BytesIO(updated)) as archive:
        assert b"<w:b/>" in archive.read("word/document.xml")
        assert b"Updated &amp; improved summary" in archive.read("word/document.xml")
        assert archive.read("word/styles.xml") == b"<styles>unchanged</styles>"
        assert archive.read("word/media/image1.png") == b"unchanged-image"
    assert client.get(f"/api/resumes/{cv['id']}/file").content == original
    assert client.get("/api/workspace").json()["applications"][0]["resume_id"] == cv["id"]


def test_upload_validation_and_same_filename_do_not_overwrite(client):
    country, _ = setup_country(client)
    cv1 = upload_cv(client, country["id"])
    cv2 = upload_cv(client, country["id"], filename="../../cv.docx")
    assert cv1["id"] != cv2["id"]
    assert cv2["filename"] == "cv.docx"
    assert "storage_key" not in cv2
    response = client.post(
        "/api/resumes/upload",
        data={"country_id": country["id"], "name": "Invalid"},
        files={"file": ("bad.docx", b"not a zip")},
    )
    assert response.status_code == 422
    response = client.post(
        f"/api/resumes/{cv1['id']}/versions",
        json={"name": "Bad", "changes": {"unknown": "bad"}},
    )
    assert response.status_code == 422


def test_validation_unknown_resources_and_duplicates(client):
    setup_country(client)
    assert client.post("/api/countries", json={"name": "Japan", "code": "JP"}).status_code == 409
    assert client.post("/api/countries", json={"name": "", "code": "J"}).status_code == 422
    assert client.get("/api/arbitrary_sql").status_code == 404
    assert (
        client.post(
            "/api/companies", json={"country_id": 999, "name": "Missing country"}
        ).status_code
        == 404
    )
    assert client.patch("/api/countries/1", json={"unknown": "value"}).status_code == 422
    assert (
        client.post(
            "/api/companies",
            json={"country_id": 1, "name": "Bad URL", "website": "javascript:alert(1)"},
        ).status_code
        == 422
    )
