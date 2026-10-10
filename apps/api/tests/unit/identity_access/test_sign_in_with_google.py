from uuid import uuid4

import pytest

from job_hunt_api.identity_access.application.use_cases.sign_in_with_google import (
    InvalidGoogleIdentityError,
    SignInWithGoogle,
)
from job_hunt_api.identity_access.domain.models import Account, ExternalIdentity


class FakeVerifier:
    def __init__(self, identity: ExternalIdentity | ValueError) -> None:
        self.identity = identity

    def verify(self, _token: str) -> ExternalIdentity:
        if isinstance(self.identity, ValueError):
            raise self.identity
        return self.identity


class FakeAccountRepository:
    def find_or_create(self, identity: ExternalIdentity) -> Account:
        return Account(id=uuid4(), email=identity.email, is_email_verified=identity.email_verified)

    def find_by_id(self, _account_id):
        return None


def test_sign_in_rejects_an_unverified_external_identity() -> None:
    use_case = SignInWithGoogle(
        FakeVerifier(
            ExternalIdentity(
                provider="google",
                subject="subject",
                email="rami@example.com",
                email_verified=False,
            )
        ),
        FakeAccountRepository(),
    )

    with pytest.raises(InvalidGoogleIdentityError):
        use_case.execute("google-id-token")
