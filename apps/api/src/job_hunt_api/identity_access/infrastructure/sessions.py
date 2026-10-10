from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from job_hunt_api.config import Settings

SESSION_ISSUER = "job-hunt-api"


class SessionTokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def issue(self, account_id: UUID) -> str:
        issued_at = datetime.now(UTC)
        payload = {
            "sub": str(account_id),
            "iss": SESSION_ISSUER,
            "iat": issued_at,
            "exp": issued_at + timedelta(seconds=self._settings.session_duration_seconds),
        }
        return jwt.encode(
            payload,
            self._settings.session_signing_key.get_secret_value(),
            algorithm="HS256",
        )

    def read_account_id(self, token: str) -> UUID | None:
        try:
            payload = jwt.decode(
                token,
                self._settings.session_signing_key.get_secret_value(),
                algorithms=["HS256"],
                issuer=SESSION_ISSUER,
            )
            return UUID(payload["sub"])
        except (InvalidTokenError, KeyError, ValueError):
            return None
