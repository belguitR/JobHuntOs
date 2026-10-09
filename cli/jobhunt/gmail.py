"""Optional Gmail sender. OAuth tokens stay local; sending always needs terminal confirmation."""

from __future__ import annotations

import base64
import os
from email.message import EmailMessage
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
TRUST_BUNDLE = Path(__file__).resolve().parents[1] / "data" / "windows-trust.pem"


def _configure_trust() -> None:
    """Use the locally exported Windows trust store when Python lacks a CA bundle."""
    if TRUST_BUNDLE.is_file():
        os.environ.setdefault("SSL_CERT_FILE", str(TRUST_BUNDLE))
        os.environ.setdefault("REQUESTS_CA_BUNDLE", str(TRUST_BUNDLE))


def _service(credentials_path: Path, token_path: Path):
    _configure_trust()
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as error:
        raise RuntimeError("Install the optional Gmail dependencies: pip install -r requirements.txt") from error
    if not credentials_path.is_file():
        raise RuntimeError(f"Gmail OAuth client file not found: {credentials_path}")
    credentials = Credentials.from_authorized_user_file(token_path, SCOPES) if token_path.exists() else None
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            credentials = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES).run_local_server(port=0)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=credentials)


def _message(*, recipient: str, subject: str, body: str, cv: Path) -> str:
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(cv.read_bytes(), maintype="application", subtype="pdf", filename=cv.name)
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def authorize(*, credentials_path: Path, token_path: Path) -> None:
    """Open the local OAuth consent flow and store the local refresh token."""
    _service(credentials_path, token_path)


def create_draft(
    *, credentials_path: Path, token_path: Path, recipient: str, subject: str, body: str, cv: Path
) -> str:
    service = _service(credentials_path, token_path)
    encoded = _message(recipient=recipient, subject=subject, body=body, cv=cv)
    result = service.users().drafts().create(userId="me", body={"message": {"raw": encoded}}).execute()
    return result["id"]


def send(*, credentials_path: Path, token_path: Path, recipient: str, subject: str, body: str, cv: Path) -> str:
    service = _service(credentials_path, token_path)
    encoded = _message(recipient=recipient, subject=subject, body=body, cv=cv)
    result = service.users().messages().send(
        userId="me", body={"raw": encoded}
    ).execute()
    return result["id"]
