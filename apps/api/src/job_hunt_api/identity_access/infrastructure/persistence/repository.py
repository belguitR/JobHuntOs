from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_hunt_api.identity_access.domain.models import Account, ExternalIdentity
from job_hunt_api.identity_access.infrastructure.persistence.mappers import to_domain_account
from job_hunt_api.identity_access.infrastructure.persistence.models import (
    AccountRecord,
    ExternalIdentityRecord,
)


class SqlAlchemyAccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_or_create(self, identity: ExternalIdentity) -> Account:
        existing_identity = self._session.scalar(
            select(ExternalIdentityRecord).where(
                ExternalIdentityRecord.provider == identity.provider,
                ExternalIdentityRecord.provider_subject == identity.subject,
            )
        )
        if existing_identity is not None:
            return to_domain_account(existing_identity.account)

        existing_account = self._session.scalar(
            select(AccountRecord).where(AccountRecord.email == identity.email)
        )
        if existing_account is not None:
            raise ValueError("An account already uses this email address.")

        account = AccountRecord(email=identity.email, is_email_verified=identity.email_verified)
        self._session.add(account)
        self._session.flush()
        self._session.add(
            ExternalIdentityRecord(
                account_id=account.id,
                provider=identity.provider,
                provider_subject=identity.subject,
            )
        )
        self._session.commit()
        self._session.refresh(account)
        return to_domain_account(account)

    def find_by_id(self, account_id: UUID) -> Account | None:
        account = self._session.get(AccountRecord, account_id)
        return to_domain_account(account) if account else None
