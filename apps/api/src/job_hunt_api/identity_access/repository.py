from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_hunt_api.identity_access.models import Account, ExternalIdentity
from job_hunt_api.identity_access.ports import VerifiedExternalIdentity


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_or_create_account(self, identity: VerifiedExternalIdentity) -> Account:
        existing_identity = self._session.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.provider == identity.provider,
                ExternalIdentity.provider_subject == identity.subject,
            )
        )
        if existing_identity is not None:
            return existing_identity.account

        existing_account = self._session.scalar(select(Account).where(Account.email == identity.email))
        if existing_account is not None:
            raise ValueError("An account already uses this email address.")

        account = Account(email=identity.email, is_email_verified=identity.email_verified)
        self._session.add(account)
        self._session.flush()

        self._session.add(
            ExternalIdentity(
                account_id=account.id,
                provider=identity.provider,
                provider_subject=identity.subject,
            )
        )
        self._session.commit()
        self._session.refresh(account)
        return account

    def find_account(self, account_id: UUID) -> Account | None:
        return self._session.get(Account, account_id)
