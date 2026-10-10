from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from job_hunt_api.database import get_db_session
from job_hunt_api.main import app


def test_health_is_available() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database_connectivity() -> None:
    engine = create_engine("sqlite://")

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = session_override
    client = TestClient(app)

    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_reports_database_failure() -> None:
    class UnavailableSession:
        def execute(self, _statement):
            raise SQLAlchemyError("database offline")

    def session_override():
        yield UnavailableSession()

    app.dependency_overrides[get_db_session] = session_override
    client = TestClient(app)

    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}
