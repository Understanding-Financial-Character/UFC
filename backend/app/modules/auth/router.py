from fastapi import APIRouter, status

from app.api.dependencies import DatabaseSession
from app.modules.auth import service
from app.modules.auth.dependencies import AuthenticatedPrincipal
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DatabaseSession) -> TokenResponse:
    _user, tokens = service.signup(db, payload)
    return build_token_response(tokens)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DatabaseSession) -> TokenResponse:
    _user, tokens = service.authenticate(db, str(payload.email), payload.password)
    return build_token_response(tokens)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DatabaseSession) -> TokenResponse:
    tokens = service.refresh_access_token(db, payload.refresh_token)
    return build_token_response(tokens)


@router.post("/logout", response_model=LogoutResponse)
def logout(payload: LogoutRequest, db: DatabaseSession) -> LogoutResponse:
    service.logout(db, payload.refresh_token)
    return LogoutResponse()


def build_token_response(tokens: service.IssuedTokens) -> TokenResponse:
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


me_router = APIRouter(tags=["me"])


@me_router.get("/me", response_model=MeResponse)
def me(principal: AuthenticatedPrincipal, db: DatabaseSession) -> MeResponse:
    user = db.get(User, principal.user_id)
    if user is None:
        service.raise_invalid_credentials()
    return MeResponse(
        user_id=user.id,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
    )
