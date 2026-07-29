from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

REQUIRED_SECURITY_SETTINGS = (
    "auth_token_secret",
    "field_encryption_key",
    "field_lookup_hmac_key",
    "field_key_version",
)
MIN_HMAC_KEY_BYTES = 32

password_hasher = PasswordHasher()


class KeyProvider(Protocol):
    def get_field_key(self) -> bytes:
        raise NotImplementedError

    def get_lookup_key(self) -> bytes:
        raise NotImplementedError

    def get_key_version(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class EnvironmentKeyProvider:
    settings: Settings

    def get_field_key(self) -> bytes:
        return decode_aes256_key(require_setting(self.settings.field_encryption_key))

    def get_lookup_key(self) -> bytes:
        return require_setting(self.settings.field_lookup_hmac_key).encode("utf-8")

    def get_key_version(self) -> str:
        return require_setting(self.settings.field_key_version)


def validate_required_security_settings(settings: Settings) -> None:
    missing = [
        field_name
        for field_name in REQUIRED_SECURITY_SETTINGS
        if not getattr(settings, field_name)
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required security settings: {joined}")
    decode_aes256_key(require_setting(settings.field_encryption_key))
    validate_hmac_secret("AUTH_TOKEN_SECRET", settings.auth_token_secret)
    validate_hmac_secret("FIELD_LOOKUP_HMAC_KEY", settings.field_lookup_hmac_key)


def validate_hmac_secret(name: str, value: str | None) -> str:
    secret = require_setting(value)
    if len(secret.encode("utf-8")) < MIN_HMAC_KEY_BYTES:
        raise RuntimeError(f"{name} must be at least 32 bytes.")
    return secret


def require_setting(value: str | None) -> str:
    if not value:
        raise RuntimeError("Missing required security setting.")
    return value


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(
    *,
    user_id: str,
    role: str,
    secret_key: str,
    ttl_seconds: int,
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role,
        "typ": "access",
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": secrets.token_urlsafe(16),
    }
    encoded_payload = encode_json(payload)
    signature = sign_token(encoded_payload, secret_key)
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str, secret_key: str) -> dict[str, object]:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise ValueError("Invalid token format.") from exc
    expected_signature = sign_token(encoded_payload, secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature.")
    payload = decode_json(encoded_payload)
    if payload.get("typ") != "access":
        raise ValueError("Invalid token type.")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise ValueError("Token expired.")
    return payload


def encrypt_text(value: str, key_provider: KeyProvider, aad: bytes | None = None) -> str:
    aesgcm = AESGCM(key_provider.get_field_key())
    nonce = secrets.token_bytes(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), aad)
    return ".".join(
        [
            key_provider.get_key_version(),
            base64.urlsafe_b64encode(nonce).decode("ascii"),
            base64.urlsafe_b64encode(ciphertext).decode("ascii"),
        ]
    )


def decrypt_text(value: str, key_provider: KeyProvider, aad: bytes | None = None) -> str:
    try:
        key_version, encoded_nonce, encoded_ciphertext = value.split(".", maxsplit=2)
        if key_version != key_provider.get_key_version():
            raise ValueError("Unsupported key version.")
        nonce = base64.urlsafe_b64decode(encoded_nonce.encode("ascii"))
        ciphertext = base64.urlsafe_b64decode(encoded_ciphertext.encode("ascii"))
        plaintext = AESGCM(key_provider.get_field_key()).decrypt(nonce, ciphertext, aad)
    except (InvalidTag, ValueError) as exc:
        raise ValueError("Ciphertext could not be decrypted.") from exc
    return plaintext.decode("utf-8")


def lookup_hmac(value: str, key_provider: KeyProvider) -> str:
    normalized = normalize_email(value)
    return hmac.new(
        key_provider.get_lookup_key(),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def normalize_email(value: str) -> str:
    return value.strip().lower()


def mask_email(value: str) -> str:
    local, separator, domain = value.partition("@")
    if not separator:
        return "***"
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def refresh_token_expires_at(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_seconds)


def decode_aes256_key(value: str) -> bytes:
    try:
        key = base64.b64decode(value, validate=True)
    except ValueError as exc:
        raise RuntimeError("FIELD_ENCRYPTION_KEY must be base64 encoded.") from exc
    if len(key) != 32:
        raise RuntimeError("FIELD_ENCRYPTION_KEY must decode to 32 bytes.")
    return key


def encode_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_json(value: str) -> dict[str, object]:
    padding = "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Token payload must be an object.")
    return payload


def sign_token(encoded_payload: str, secret_key: str) -> str:
    digest = hmac.new(
        secret_key.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
