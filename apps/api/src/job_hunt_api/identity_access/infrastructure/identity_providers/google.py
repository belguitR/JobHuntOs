from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token

from job_hunt_api.identity_access.domain.models import ExternalIdentity


class GoogleIdTokenVerifier:
    def __init__(self, client_id: str) -> None:
        self._client_id = client_id
        self._request = requests.Request()

    def verify(self, token: str) -> ExternalIdentity:
        try:
            claims = id_token.verify_oauth2_token(token, self._request, self._client_id)
        except GoogleAuthError as error:
            raise ValueError("Google ID token verification failed.") from error
        email = claims.get("email")
        subject = claims.get("sub")
        email_verified = claims.get("email_verified") is True
        if not isinstance(email, str) or not isinstance(subject, str) or not email_verified:
            raise ValueError("Google ID token does not contain a verified email identity.")
        return ExternalIdentity(
            provider="google",
            subject=subject,
            email=email,
            email_verified=email_verified,
        )
