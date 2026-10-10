from uuid import UUID

from job_hunt_api.identity_access.application.ports import AccountRepository
from job_hunt_api.identity_access.domain.models import Account


class GetCurrentAccount:
    def __init__(self, accounts: AccountRepository) -> None:
        self._accounts = accounts

    def execute(self, account_id: UUID) -> Account | None:
        return self._accounts.find_by_id(account_id)
