from typing import Protocol
from uuid import UUID

from job_hunt_api.identity_access.domain.models import Account, ExternalIdentity


class IdentityTokenVerifier(Protocol):
    def verify(self, token: str) -> ExternalIdentity: ...


class AccountRepository(Protocol):
    def find_or_create(self, identity: ExternalIdentity) -> Account: ...

    def find_by_id(self, account_id: UUID) -> Account | None: ...
