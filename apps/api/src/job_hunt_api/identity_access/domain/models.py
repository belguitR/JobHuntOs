from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Account:
    id: UUID
    email: str
    is_email_verified: bool


@dataclass(frozen=True)
class ExternalIdentity:
    provider: str
    subject: str
    email: str
    email_verified: bool
