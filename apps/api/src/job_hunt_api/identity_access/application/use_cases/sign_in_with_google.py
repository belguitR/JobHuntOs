from job_hunt_api.identity_access.application.ports import AccountRepository, IdentityTokenVerifier
from job_hunt_api.identity_access.domain.models import Account


class InvalidGoogleIdentityError(Exception):
    pass


class AccountEmailConflictError(Exception):
    pass


class SignInWithGoogle:
    def __init__(self, verifier: IdentityTokenVerifier, accounts: AccountRepository) -> None:
        self._verifier = verifier
        self._accounts = accounts

    def execute(self, id_token: str) -> Account:
        try:
            identity = self._verifier.verify(id_token)
        except ValueError as error:
            raise InvalidGoogleIdentityError from error
        if not identity.email_verified:
            raise InvalidGoogleIdentityError
        try:
            return self._accounts.find_or_create(identity)
        except ValueError as error:
            raise AccountEmailConflictError from error
