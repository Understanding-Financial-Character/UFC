from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.analysis.contracts import AnalysisSourceType, ResultStatus
from app.modules.analysis_results.models import AnalysisRunStatus

SCHEMA_VERSION = "1.0"


class AnalysisCreateRequest(BaseModel):
    period_start: date
    period_end: date

    @model_validator(mode="after")
    def validate_period(self) -> AnalysisCreateRequest:
        if self.period_start > self.period_end:
            raise ValueError("period_start must be before or equal to period_end.")
        return self


class BehaviorMetricResponse(BaseModel):
    feature_code: str
    status: str
    raw_value: Decimal | None
    normalized_score: Decimal | None
    unit: str
    sample_count: int
    unavailable_reason: str | None
    evidence: list[str] = Field(default_factory=list)


class ConsumptionMbtiResponse(BaseModel):
    mbti_type: str | None
    result_status: ResultStatus
    axis_scores: dict[str, Decimal | None]
    confidence: dict[str, Any]
    coverage: Decimal | None
    limitations: list[str] = Field(default_factory=list)
    rule_version: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIReportResponse(BaseModel):
    status: str
    fallback_used: bool
    fallback_reason: str | None
    model_name: str | None
    prompt_version: str | None
    report_content: dict[str, Any] | None


class AnalysisResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    analysis_id: str
    group_id: str
    status: AnalysisRunStatus
    result_status: ResultStatus | None
    provisional_reasons: list[str] = Field(default_factory=list)
    analysis_period_started_at: datetime
    analysis_period_ended_at: datetime
    source_type: AnalysisSourceType
    is_synthetic: bool
    input_schema_version: str
    analysis_version: str
    snapshot_hash: str
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    behavior_metrics: list[BehaviorMetricResponse] = Field(default_factory=list)
    consumption_mbti_result: ConsumptionMbtiResponse | None = None
    ai_report: AIReportResponse | None = None

    model_config = ConfigDict(from_attributes=True)
