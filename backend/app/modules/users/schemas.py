from datetime import datetime

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0"


class UserCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name must not be blank.")
        return normalized


class UserResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    user_id: str
    display_name: str
    created_at: datetime
