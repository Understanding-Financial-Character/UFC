from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.groups.models import GroupStatus, MBTIType, RelationshipType

SCHEMA_VERSION = "1.0"


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    relationship_type: RelationshipType

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Group name must not be blank.")
        return normalized


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    relationship_type: RelationshipType | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Group name must not be blank.")
        return normalized

    @model_validator(mode="after")
    def require_change(self) -> "GroupUpdate":
        if self.name is None and self.relationship_type is None:
            raise ValueError("At least one field must be provided.")
        return self


class MemberCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=40)
    mbti: MBTIType

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name must not be blank.")
        return normalized


class MemberUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    mbti: MBTIType | None = None

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name must not be blank.")
        return normalized

    @model_validator(mode="after")
    def require_change(self) -> "MemberUpdate":
        if self.display_name is None and self.mbti is None:
            raise ValueError("At least one field must be provided.")
        return self


class MemberResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    group_id: str
    member_id: str
    display_name: str
    mbti: MBTIType | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    group_id: str
    name: str
    relationship_type: RelationshipType
    status: GroupStatus
    member_count: int
    can_analyze: bool
    created_at: datetime
    members: list[MemberResponse] = Field(default_factory=list)
