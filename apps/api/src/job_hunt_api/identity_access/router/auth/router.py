from functools import lru_cache

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from job_hunt_api.config import Settings, get_settings
from job_hunt_api.database import get_db_session
from job_hunt_api.identity_access.application.ports import IdentityTokenVerifier
from job_hunt_api.identity_access.application.use_cases.get_current_account import GetCurrentAccount
from job_hunt_api.identity_access.application.use_cases.sign_in_with_google import (
    AccountEmailConflictError,
    InvalidGoogleIdentityError,
    SignInWithGoogle,
)
from job_hunt_api.identity_access.domain.models import Account
from job_hunt_api.identity_access.infrastructure.identity_providers.google import (
    GoogleIdTokenVerifier,
)
from job_hunt_api.identity_access.infrastructure.persistence.repository import (
    SqlAlchemyAccountRepository,
)
from job_hunt_api.identity_access.infrastructure.sessions import SessionTokenService
from job_hunt_api.identity_access.router.auth.schemas import (
    CurrentUserResponse,
    GoogleSignInRequest,
)

SESSION_COOKIE = "job_hunt_session"

router = APIRouter(prefix="/auth", tags=["identity-access"])


@lru_cache
def get_google_token_verifier() -> IdentityTokenVerifier:
    return GoogleIdTokenVerifier(get_settings().google_client_id)


def get_session_token_service(settings: Settings = Depends(get_settings)) -> SessionTokenService:
    return SessionTokenService(settings)


def get_account_repository(session: Session = Depends(get_db_session)) -> SqlAlchemyAccountRepository:
    return SqlAlchemyAccountRepository(session)


def get_current_account(
    accounts: SqlAlchemyAccountRepository = Depends(get_account_repository),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    token_service: SessionTokenService = Depends(get_session_token_service),
) -> Account:
    account_id = token_service.read_account_id(session_token) if session_token else None
    account = GetCurrentAccount(accounts).execute(account_id) if account_id else None
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return account


@router.post("/google", response_model=CurrentUserResponse)
def sign_in_with_google(
    payload: GoogleSignInRequest,
    response: Response,
    accounts: SqlAlchemyAccountRepository = Depends(get_account_repository),
    verifier: IdentityTokenVerifier = Depends(get_google_token_verifier),
    token_service: SessionTokenService = Depends(get_session_token_service),
    settings: Settings = Depends(get_settings),
) -> Account:
    try:
        account = SignInWithGoogle(verifier, accounts).execute(payload.id_token)
    except InvalidGoogleIdentityError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Google ID token is invalid."
        ) from error
    except AccountEmailConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account already uses this email address."
        ) from error
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token_service.issue(account.id),
        max_age=settings.session_duration_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
    return account


@router.get("/me", response_model=CurrentUserResponse)
def current_user(account: Account = Depends(get_current_account)) -> Account:
    return account


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(key=SESSION_COOKIE, httponly=True, samesite="lax")
    return response
