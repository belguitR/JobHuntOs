from job_hunt_api.identity_access.domain.models import Account
from job_hunt_api.identity_access.infrastructure.persistence.models import AccountRecord


def to_domain_account(record: AccountRecord) -> Account:
    return Account(
        id=record.id,
        email=record.email,
        is_email_verified=record.is_email_verified,
    )
