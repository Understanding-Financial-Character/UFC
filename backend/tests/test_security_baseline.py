from __future__ import annotations

import os
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.config import Settings
from app.core.security import (
    EnvironmentKeyProvider,
    decrypt_text,
    encrypt_text,
    hash_refresh_token,
    validate_required_security_settings,
)
from app.db.base import Base
from app.main import create_app
from app.modules.auth.models import RefreshToken
from app.modules.users.models import User, UserRole


@dataclass(frozen=True)
class SecurityTestContext:
    client: TestClient
    session_local: sessionmaker[Session]


def build_context(*, raise_server_exceptions: bool = True) -> SecurityTestContext:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return SecurityTestContext(
        client=TestClient(app, raise_server_exceptions=raise_server_exceptions),
        session_local=testing_session_local,
    )


def signup(context: SecurityTestContext, email: str | None = None) -> dict[str, str]:
    user_email = email or f"user-{uuid4().hex}@example.com"
    response = context.client.post(
        "/api/v1/auth/signup",
        json={
            "email": user_email,
            "display_name": "security user",
            "password": "correct-password",
        },
    )
    assert response.status_code == 201
    token_body = response.json()
    me_response = context.client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )
    assert me_response.status_code == 200
    return {
        "email": user_email,
        "user_id": str(me_response.json()["user_id"]),
        "access_token": str(token_body["access_token"]),
        "refresh_token": str(token_body["refresh_token"]),
    }


def auth_headers(user: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['access_token']}"}


def test_sec_01_password_and_refresh_token_are_not_stored_in_plaintext() -> None:
    context = build_context()
    password = "correct-password"
    user = signup(context)

    with context.session_local() as db:
        db_user = db.get(User, user["user_id"])
        assert db_user is not None
        assert db_user.password_hash != password
        assert password not in (db_user.password_hash or "")
        stored_token = db.scalar(select(RefreshToken))
        assert stored_token is not None
        assert stored_token.token_hash == hash_refresh_token(user["refresh_token"])
        assert stored_token.token_hash != user["refresh_token"]


def test_sec_02_users_cannot_read_other_users_groups() -> None:
    context = build_context()
    owner = signup(context)
    other = signup(context)
    group_response = context.client.post(
        "/api/v1/groups",
        headers=auth_headers(owner),
        json={"name": "security group", "relationship_type": "FRIENDS"},
    )
    assert group_response.status_code == 201

    response = context.client.get(
        f"/api/v1/groups/{group_response.json()['group_id']}",
        headers=auth_headers(other),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_sec_03_admin_user_list_masks_email() -> None:
    context = build_context()
    normal_user = signup(context, "visible-user@example.com")
    admin_user = signup(context, "admin-user@example.com")
    promote_to_admin(context, admin_user["user_id"])
    admin_tokens = login(context, admin_user["email"], "correct-password")

    response = context.client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )

    assert response.status_code == 200
    body_text = response.text
    assert normal_user["email"] not in body_text
    assert "v***r@example.com" in body_text


def test_sec_04_api_responses_do_not_expose_password_hash_or_ciphertext() -> None:
    context = build_context()
    user = signup(context)

    me_response = context.client.get("/api/v1/me", headers=auth_headers(user))
    admin_denied_response = context.client.get("/api/v1/admin/users", headers=auth_headers(user))

    combined = me_response.text + admin_denied_response.text
    assert "password_hash" not in combined
    assert "email_ciphertext" not in combined
    assert "email_lookup_hmac" not in combined


def test_sec_05_required_secrets_are_validated() -> None:
    insecure_settings = Settings(
        auth_token_secret=None,
        field_encryption_key=None,
        field_lookup_hmac_key=None,
        field_key_version=None,
    )

    with pytest.raises(RuntimeError, match="Missing required security settings"):
        validate_required_security_settings(insecure_settings)


def test_short_auth_token_secret_is_rejected() -> None:
    weak_settings = Settings(
        auth_token_secret="short",
        field_encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        field_lookup_hmac_key="test-email-lookup-hmac-key-32-bytes",
        field_key_version="test-v1",
    )
    with pytest.raises(RuntimeError, match="AUTH_TOKEN_SECRET must be at least 32 bytes"):
        validate_required_security_settings(weak_settings)


def test_short_lookup_hmac_key_is_rejected() -> None:
    weak_settings = Settings(
        auth_token_secret="test-auth-token-secret-32-bytes-min",
        field_encryption_key="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        field_lookup_hmac_key="short",
        field_key_version="test-v1",
    )
    with pytest.raises(RuntimeError, match="FIELD_LOOKUP_HMAC_KEY must be at least 32 bytes"):
        validate_required_security_settings(weak_settings)


def test_sec_06_failed_login_logs_do_not_include_password_or_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    context = build_context()
    user = signup(context)

    response = context.client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "wrong-password-secret"},
        headers={"Authorization": "Bearer leaked-token-value"},
    )

    assert response.status_code == 401
    assert "wrong-password-secret" not in caplog.text
    assert "leaked-token-value" not in caplog.text


def test_sec_07_tampered_ciphertext_cannot_be_decrypted() -> None:
    settings = Settings()
    key_provider = EnvironmentKeyProvider(settings)
    ciphertext = encrypt_text("private@example.com", key_provider)
    tampered = f"{ciphertext[:-1]}A"

    with pytest.raises(ValueError, match="Ciphertext could not be decrypted"):
        decrypt_text(tampered, key_provider)


def test_email_ciphertext_is_bound_to_user_context() -> None:
    context = build_context(raise_server_exceptions=False)
    first_user = signup(context, "first-user@example.com")
    second_user = signup(context, "second-user@example.com")

    with context.session_local() as db:
        first = db.get(User, first_user["user_id"])
        second = db.get(User, second_user["user_id"])
        assert first is not None
        assert second is not None
        second.email_ciphertext = first.email_ciphertext
        db.commit()

    promote_to_admin(context, first_user["user_id"])
    admin_tokens = login(context, first_user["email"], "correct-password")
    response = context.client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"


def test_login_rate_limit_blocks_repeated_failures() -> None:
    context = build_context()
    user = signup(context)

    statuses = [
        context.client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "wrong-password-secret"},
        ).status_code
        for _ in range(6)
    ]

    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429


def test_successful_login_clears_login_rate_limit_attempts() -> None:
    context = build_context()
    user = signup(context)

    for _ in range(4):
        response = context.client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "wrong-password-secret"},
        )
        assert response.status_code == 401

    success_response = context.client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "correct-password"},
    )
    next_success_response = context.client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "correct-password"},
    )

    assert success_response.status_code == 200
    assert next_success_response.status_code == 200


def test_refresh_and_logout_flow() -> None:
    context = build_context()
    user = signup(context)

    refresh_response = context.client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user["refresh_token"]},
    )
    assert refresh_response.status_code == 200

    logout_response = context.client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_response.json()["refresh_token"]},
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}


def test_refresh_token_reuse_revokes_token_family() -> None:
    context = build_context()
    user = signup(context)

    refresh_response = context.client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user["refresh_token"]},
    )
    reuse_response = context.client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    assert reuse_response.status_code == 401
    with context.session_local() as db:
        tokens = list(db.scalars(select(RefreshToken)).all())
        assert len(tokens) == 2
        assert all(token.revoked_at is not None for token in tokens)
        assert {token.revocation_reason for token in tokens} == {"ROTATED", "REUSE_DETECTED"}


def test_cors_allows_configured_origin_only() -> None:
    context = build_context()

    allowed_response = context.client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    blocked_response = context.client.get(
        "/health",
        headers={"Origin": "https://evil.example"},
    )

    assert allowed_response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked_response.headers


def test_postgres_concurrent_refresh_token_allows_single_rotation() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL refresh token concurrency test.")
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    refresh_columns = {
        column["name"] for column in sqlalchemy_inspect(engine).get_columns("refresh_tokens")
    }
    if "family_id" not in refresh_columns:
        pytest.skip("Refresh token rotation migration is required for this integration test.")
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    context = SecurityTestContext(client=client, session_local=testing_session_local)
    user = signup(context)

    def refresh_once() -> int:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": user["refresh_token"]},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _index: refresh_once(), range(2)))

    with context.session_local() as db:
        token_rows = list(
            db.scalars(
                select(RefreshToken).where(RefreshToken.user_id == user["user_id"])
            ).all()
        )

    assert sorted(statuses) == [200, 401]
    assert len(token_rows) == 2
    assert sum(token.revocation_reason == "ROTATED" for token in token_rows) == 1
    assert sum(token.revocation_reason == "REUSE_DETECTED" for token in token_rows) == 1
    assert all(token.revoked_at is not None for token in token_rows)


def login(context: SecurityTestContext, email: str, password: str) -> dict[str, str]:
    response = context.client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {
        "access_token": str(response.json()["access_token"]),
        "refresh_token": str(response.json()["refresh_token"]),
    }


def promote_to_admin(context: SecurityTestContext, user_id: str) -> None:
    with context.session_local() as db:
        user = db.get(User, user_id)
        assert user is not None
        user.role = UserRole.ADMIN
        db.commit()
