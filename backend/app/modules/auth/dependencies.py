from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import DatabaseSession
from app.core.config import settings
from app.core.exceptions import ApiException
from app.core.security import decode_access_token
from app.modules.users.models import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentPrincipal:
    user_id: str
    role: UserRole


def get_current_principal(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiException(
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
            status_code=401,
        )
    try:
        payload = decode_access_token(credentials.credentials, settings.auth_token_secret or "")
        user_id = str(payload["sub"])
        role = UserRole(str(payload["role"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiException(
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
            status_code=401,
        ) from exc
    user = db.get(User, user_id)
    if user is None or user.role != role:
        raise ApiException(
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
            status_code=401,
        )
    return CurrentPrincipal(user_id=user.id, role=user.role)


def require_admin(
    principal: Annotated[CurrentPrincipal, Depends(get_current_principal)],
) -> CurrentPrincipal:
    if principal.role != UserRole.ADMIN:
        raise ApiException(
            code="PERMISSION_DENIED",
            message="Admin role is required.",
            status_code=403,
        )
    return principal


AuthenticatedPrincipal = Annotated[CurrentPrincipal, Depends(get_current_principal)]
AdminPrincipal = Annotated[CurrentPrincipal, Depends(require_admin)]
