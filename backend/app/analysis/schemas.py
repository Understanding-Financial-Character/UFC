from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.groups.models import MBTIType

ANALYSIS_INPUT_SCHEMA_VERSION = "analysis-input-v1"
BEHAVIOR_METRICS_SCHEMA_VERSION = "behavior-metrics-v1"


class TransactionCategory(str, Enum):
    FOOD = "FOOD"
    CAFE = "CAFE"
    TRANSPORT = "TRANSPORT"
    SHOPPING = "SHOPPING"
    GROCERY = "GROCERY"
    CULTURE = "CULTURE"
    TRAVEL = "TRAVEL"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    HOUSING = "HOUSING"
    FINANCE = "FINANCE"
    OTHER = "OTHER"


class AnalysisMemberInput(BaseModel):
    member_id: str = Field(alias="memberId", min_length=1)
    mbti_type: MBTIType = Field(alias="mbtiType")


class AnalysisTransactionInput(BaseModel):
    occurred_at: datetime = Field(alias="occurredAt")
    amount: int = Field(gt=0)
    category: TransactionCategory
    merchant_key: str | None = Field(default=None, alias="merchantKey", min_length=1, max_length=80)
    is_recurring: bool | None = Field(default=None, alias="isRecurring")
    is_planned: bool | None = Field(default=None, alias="isPlanned")

    @field_validator("merchant_key")
    @classmethod
    def normalize_merchant_key(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        return normalized or None


class AnalysisInput(BaseModel):
    analysis_id: str = Field(alias="analysisId", min_length=1)
    group_id: str = Field(alias="groupId", min_length=1)
    members: list[AnalysisMemberInput] = Field(min_length=1)
    transactions: list[AnalysisTransactionInput]
    schema_version: Literal["analysis-input-v1"] = Field(alias="schemaVersion")

    @model_validator(mode="after")
    def require_unique_members(self) -> AnalysisInput:
        member_ids = [member.member_id for member in self.members]
        if len(member_ids) != len(set(member_ids)):
            raise ValueError("Member ids must be unique.")
        return self


class BehaviorMetricValues(BaseModel):
    category_concentration: float | None = Field(alias="categoryConcentration")
    spending_volatility: float | None = Field(alias="spendingVolatility")
    repeat_purchase_ratio: float | None = Field(alias="repeatPurchaseRatio")
    weekend_spending_ratio: float | None = Field(alias="weekendSpendingRatio")
    planned_spending_ratio: float | None = Field(alias="plannedSpendingRatio")


class BehaviorMetricEvidence(BaseModel):
    metric: str
    value: float | None
    basis: str


class BehaviorMetricsOutput(BaseModel):
    schema_version: Literal["behavior-metrics-v1"] = Field(alias="schemaVersion")
    metrics: BehaviorMetricValues
    evidence: list[BehaviorMetricEvidence]
