from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from job_hunt_api.database import Base, get_db_session
from job_hunt_api.identity_access.domain.models import ExternalIdentity
from job_hunt_api.identity_access.infrastructure.persistence.models import (
    AccountRecord,
    ExternalIdentityRecord,
)
from job_hunt_api.identity_access.router.auth import get_google_token_verifier
from job_hunt_api.main import app


class FakeGoogleTokenVerifier:
    def __init__(self, identity: ExternalIdentity | ValueError) -> None:
        self.identity = identity

    def verify(self, token: str) -> ExternalIdentity:
        if isinstance(self.identity, ValueError):
            raise self.identity
        assert token == "google-id-token"
        return self.identity


@pytest.fixture
def identity_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    def session_override() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = session_override
    client = TestClient(app)
    try:
        yield client, session_factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def set_google_identity(identity: ExternalIdentity | ValueError) -> None:
    app.dependency_overrides[get_google_token_verifier] = lambda: FakeGoogleTokenVerifier(identity)


def test_google_sign_in_creates_identity_and_authenticates_user(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = identity_client
    set_google_identity(
        ExternalIdentity(
            provider="google",
            subject="google-subject-123",
            email="rami@example.com",
            email_verified=True,
        )
    )

    response = client.post("/auth/google", json={"id_token": "google-id-token"})
    current_user = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "rami@example.com"
    assert "httponly" in response.headers["set-cookie"].lower()
    assert current_user.status_code == 200
    assert current_user.json() == response.json()
    with session_factory() as session:
        identity = session.scalar(select(ExternalIdentityRecord))
        assert identity is not None
        assert identity.provider == "google"
        assert identity.provider_subject == "google-subject-123"


def test_google_subject_reuses_its_existing_account(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = identity_client
    verified_identity = ExternalIdentity(
        provider="google",
        subject="google-subject-123",
        email="rami@example.com",
        email_verified=True,
    )
    set_google_identity(verified_identity)

    first_response = client.post("/auth/google", json={"id_token": "google-id-token"})
    second_response = client.post("/auth/google", json={"id_token": "google-id-token"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["id"] == second_response.json()["id"]
    with session_factory() as session:
        assert len(session.scalars(select(AccountRecord)).all()) == 1
        assert len(session.scalars(select(ExternalIdentityRecord)).all()) == 1


def test_google_sign_in_does_not_identify_accounts_by_email(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = identity_client
    set_google_identity(
        ExternalIdentity(
            provider="google",
            subject="google-subject-123",
            email="rami@example.com",
            email_verified=True,
        )
    )
    first_response = client.post("/auth/google", json={"id_token": "google-id-token"})
    set_google_identity(
        ExternalIdentity(
            provider="google",
            subject="different-google-subject",
            email="rami@example.com",
            email_verified=True,
        )
    )
    second_response = client.post("/auth/google", json={"id_token": "google-id-token"})

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    with session_factory() as session:
        assert len(session.scalars(select(AccountRecord)).all()) == 1
        assert len(session.scalars(select(ExternalIdentityRecord)).all()) == 1


def test_google_sign_in_rejects_invalid_token(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _session = identity_client
    set_google_identity(ValueError("invalid token"))

    response = client.post("/auth/google", json={"id_token": "google-id-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Google ID token is invalid."}


def test_google_sign_in_rejects_unverified_email(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _session = identity_client
    set_google_identity(
        ExternalIdentity(
            provider="google",
            subject="google-subject-123",
            email="rami@example.com",
            email_verified=False,
        )
    )

    response = client.post("/auth/google", json={"id_token": "google-id-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Google ID token is invalid."}


def test_authenticated_user_requires_session(
    identity_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _session = identity_client

    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}
