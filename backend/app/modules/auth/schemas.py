from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.users.models import UserRole

SCHEMA_VERSION = "1.0"


class SignupRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name must not be blank.")
        return normalized


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class TokenResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    user_id: str
    display_name: str
    role: UserRole
    created_at: datetime


class LogoutResponse(BaseModel):
    status: str = "ok"
