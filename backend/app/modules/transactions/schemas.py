from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.transactions.models import (
    CategoryBehaviorGroup,
    TransactionSourceType,
    TransactionType,
)

SCHEMA_VERSION = "1.0"


class CategoryResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    category_id: str
    code: str
    name: str
    behavior_group: CategoryBehaviorGroup
    display_order: int
    is_active: bool


class CsvImportRequest(BaseModel):
    csv_text: str = Field(min_length=1, max_length=2_000_000)


class RowValidationError(BaseModel):
    field: str
    code: str
    message: str


class TransactionImportRowResult(BaseModel):
    row_number: int
    source_row_key: str | None = None
    status: str
    transaction_id: str | None = None
    errors: list[RowValidationError] = Field(default_factory=list)


class TransactionImportResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    group_id: str
    source_type: TransactionSourceType
    accepted_count: int
    rejected_count: int
    status: str
    rows: list[TransactionImportRowResult]


class MockScenarioResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    scenario_id: str
    name: str
    description: str
    transaction_count: int


class TransactionResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    transaction_id: str
    group_id: str
    member_id: str | None
    category_id: str | None
    transaction_at: datetime
    transaction_type: TransactionType
    amount: Decimal
    merchant_name: str | None
    description: str | None
    is_shared_expense: bool | None
    is_planned: bool | None
    is_recurring: bool | None
    is_excluded: bool
    exclusion_reason: str | None
    source_type: TransactionSourceType
    source_row_key: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionUpdate(BaseModel):
    member_id: str | None = None
    category_id: str | None = None
    transaction_at: datetime | None = None
    transaction_type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    merchant_name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    is_shared_expense: bool | None = None
    is_planned: bool | None = None
    is_recurring: bool | None = None
    is_excluded: bool | None = None
    exclusion_reason: str | None = Field(default=None, max_length=255)

    @field_validator("merchant_name", "description", "exclusion_reason")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_change(self) -> "TransactionUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self
