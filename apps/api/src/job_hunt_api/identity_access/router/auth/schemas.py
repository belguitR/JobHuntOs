from uuid import UUID

from pydantic import BaseModel


class GoogleSignInRequest(BaseModel):
    id_token: str


class CurrentUserResponse(BaseModel):
    id: UUID
    email: str
    is_email_verified: bool
