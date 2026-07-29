from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApiException
from app.core.security import (
    EnvironmentKeyProvider,
    create_access_token,
    decrypt_text,
    encrypt_text,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    lookup_hmac,
    mask_email,
    normalize_email,
    refresh_token_expires_at,
    verify_password,
)
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import SignupRequest
from app.modules.users.models import User, UserRole, utc_now

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15
LOGIN_RATE_LIMIT_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60
_login_attempts: dict[str, list[float]] = {}


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


def signup(db: Session, payload: SignupRequest) -> tuple[User, IssuedTokens]:
    key_provider = EnvironmentKeyProvider(settings)
    email = normalize_email(str(payload.email))
    user = User(
        display_name=payload.display_name,
        email_ciphertext=encrypt_text(email, key_provider),
        email_lookup_hmac=lookup_hmac(email, key_provider),
        email_key_version=key_provider.get_key_version(),
        password_hash=hash_password(payload.password),
        role=UserRole.USER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiException(
            code="CONFLICT",
            message="Email already exists.",
            status_code=409,
            details={"field": "email"},
        ) from exc
    db.refresh(user)
    return user, issue_tokens(db, user)


def authenticate(db: Session, email: str, password: str) -> tuple[User, IssuedTokens]:
    check_login_rate_limit(email)
    user = find_user_by_email(db, email)
    if user is None or user.password_hash is None:
        raise_invalid_credentials()
    if user.locked_until and ensure_aware(user.locked_until) > datetime.now(UTC):
        raise ApiException(
            code="AUTHENTICATION_REQUIRED",
            message="Login is temporarily locked.",
            status_code=401,
        )
    if not verify_password(password, user.password_hash):
        register_failed_login(db, user)
        raise_invalid_credentials()
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utc_now()
    db.commit()
    return user, issue_tokens(db, user)


def refresh_access_token(db: Session, refresh_token: str) -> IssuedTokens:
    token_hash = hash_refresh_token(refresh_token)
    statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    stored_token = db.scalar(statement)
    if (
        stored_token is None
        or stored_token.revoked_at is not None
        or ensure_aware(stored_token.expires_at) <= datetime.now(UTC)
    ):
        raise_invalid_credentials()
    user = db.get(User, stored_token.user_id)
    if user is None:
        raise_invalid_credentials()
    stored_token.revoked_at = utc_now()
    db.commit()
    return issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    stored_token = db.scalar(statement)
    if stored_token is not None and stored_token.revoked_at is None:
        stored_token.revoked_at = utc_now()
        db.commit()


def issue_tokens(db: Session, user: User) -> IssuedTokens:
    refresh_token = generate_refresh_token()
    stored_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_token_expires_at(settings),
    )
    db.add(stored_token)
    db.commit()
    return IssuedTokens(
        access_token=create_access_token(
            user_id=user.id,
            role=user.role.value,
            secret_key=settings.auth_token_secret or "",
            ttl_seconds=settings.access_token_ttl_seconds,
        ),
        refresh_token=refresh_token,
        expires_in=settings.access_token_ttl_seconds,
    )


def find_user_by_email(db: Session, email: str) -> User | None:
    key_provider = EnvironmentKeyProvider(settings)
    statement = select(User).where(User.email_lookup_hmac == lookup_hmac(email, key_provider))
    return db.scalar(statement)


def register_failed_login(db: Session, user: User) -> None:
    user.failed_login_count += 1
    if user.failed_login_count >= MAX_FAILED_LOGINS:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
    db.commit()


def raise_invalid_credentials() -> None:
    raise ApiException(
        code="AUTHENTICATION_REQUIRED",
        message="Invalid credentials.",
        status_code=401,
    )


def check_login_rate_limit(email: str) -> None:
    now = time.monotonic()
    key = email.strip().lower()
    attempts = [
        attempted_at
        for attempted_at in _login_attempts.get(key, [])
        if now - attempted_at < LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ]
    if len(attempts) >= LOGIN_RATE_LIMIT_ATTEMPTS:
        _login_attempts[key] = attempts
        raise ApiException(
            code="RATE_LIMITED",
            message="Too many login attempts.",
            status_code=429,
        )
    attempts.append(now)
    _login_attempts[key] = attempts


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def masked_email_for_user(user: User) -> str | None:
    if not user.email_ciphertext:
        return None
    email = decrypt_text(user.email_ciphertext, EnvironmentKeyProvider(settings))
    return mask_email(email)
