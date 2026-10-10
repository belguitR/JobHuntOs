from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VerifiedExternalIdentity:
    provider: str
    subject: str
    email: str
    email_verified: bool


class IdentityTokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedExternalIdentity: ...
