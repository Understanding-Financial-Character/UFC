from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.analysis.contracts import (
    AnalysisSourceType,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    ResultStatus,
)
from app.db.base import Base

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(UTC)


class AnalysisRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ConsumptionMBTIType(str, enum.Enum):
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    INFJ = "INFJ"
    INTJ = "INTJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    INFP = "INFP"
    INTP = "INTP"
    ESTP = "ESTP"
    ESFP = "ESFP"
    ENFP = "ENFP"
    ENTP = "ENTP"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ENFJ = "ENFJ"
    ENTJ = "ENTJ"


class AIReportStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    FALLBACK_COMPLETED = "FALLBACK_COMPLETED"
    FAILED = "FAILED"


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(
            "analysis_period_started_at <= analysis_period_ended_at",
            name="ck_analysis_runs_period_order",
        ),
        CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_analysis_runs_snapshot_hash_nonblank",
        ),
        CheckConstraint(
            "length(analysis_version) > 0",
            name="ck_analysis_runs_analysis_version_nonblank",
        ),
        CheckConstraint(
            "((status = 'COMPLETED' AND result_status IS NOT NULL) "
            "OR (status IN ('PENDING', 'RUNNING') AND result_status IS NULL) "
            "OR status = 'FAILED')",
            name="ck_analysis_runs_result_status_lifecycle",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(AnalysisRunStatus, name="analysis_run_status"),
        nullable=False,
        default=AnalysisRunStatus.PENDING,
    )
    result_status: Mapped[ResultStatus | None] = mapped_column(
        Enum(ResultStatus, name="analysis_result_status"), nullable=True
    )
    provisional_reasons: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    analysis_period_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    analysis_period_ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[AnalysisSourceType] = mapped_column(
        Enum(AnalysisSourceType, name="analysis_source_type"), nullable=False
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    input_schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    analysis_version: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    behavior_metrics: Mapped[list[BehaviorMetric]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )
    consumption_mbti_result: Mapped[ConsumptionMBTIResult | None] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan", uselist=False
    )
    ai_report: Mapped[AIReport | None] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan", uselist=False
    )


class BehaviorMetric(Base):
    __tablename__ = "behavior_metrics"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "feature_code", name="uq_behavior_metrics_run_feature"),
        CheckConstraint(
            "normalized_score IS NULL OR (normalized_score >= 0 AND normalized_score <= 1)",
            name="ck_behavior_metrics_normalized_score_range",
        ),
        CheckConstraint(
            "sample_count >= 0",
            name="ck_behavior_metrics_sample_count_nonnegative",
        ),
        CheckConstraint(
            "((status = 'AVAILABLE' AND raw_value IS NOT NULL AND normalized_score IS NOT NULL) "
            "OR (status = 'UNAVAILABLE' AND unavailable_reason IS NOT NULL))",
            name="ck_behavior_metrics_status_payload",
        ),
        CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_behavior_metrics_snapshot_hash_nonblank",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[BehaviorFeatureStatus] = mapped_column(
        Enum(BehaviorFeatureStatus, name="behavior_feature_status"), nullable=False
    )
    raw_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    normalized_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    unit: Mapped[BehaviorFeatureUnit] = mapped_column(
        Enum(BehaviorFeatureUnit, name="behavior_feature_unit"), nullable=False
    )
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unavailable_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    metric_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="behavior_metrics")


class ConsumptionMBTIResult(Base):
    __tablename__ = "consumption_mbti_results"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", name="uq_consumption_mbti_results_run"),
        CheckConstraint("ei_score IS NULL OR (ei_score >= 0 AND ei_score <= 1)", name="ck_mbti_ei_score_range"),
        CheckConstraint("sn_score IS NULL OR (sn_score >= 0 AND sn_score <= 1)", name="ck_mbti_sn_score_range"),
        CheckConstraint("tf_score IS NULL OR (tf_score >= 0 AND tf_score <= 1)", name="ck_mbti_tf_score_range"),
        CheckConstraint("jp_score IS NULL OR (jp_score >= 0 AND jp_score <= 1)", name="ck_mbti_jp_score_range"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_mbti_confidence_score_range",
        ),
        CheckConstraint("coverage IS NULL OR (coverage >= 0 AND coverage <= 1)", name="ck_mbti_coverage_range"),
        CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_consumption_mbti_results_snapshot_hash_nonblank",
        ),
        CheckConstraint(
            "(result_status != 'INSUFFICIENT_DATA' OR mbti_type IS NULL)",
            name="ck_consumption_mbti_results_insufficient_mbti_null",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mbti_type: Mapped[ConsumptionMBTIType | None] = mapped_column(
        Enum(ConsumptionMBTIType, name="consumption_mbti_type"), nullable=True
    )
    result_status: Mapped[ResultStatus] = mapped_column(
        Enum(ResultStatus, name="analysis_result_status"), nullable=False
    )
    ei_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    sn_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    tf_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    jp_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    coverage: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    limitations: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False, default=list)
    axis_score_directions: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    result_metadata: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="consumption_mbti_result")


class AIReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", name="uq_ai_reports_run"),
        CheckConstraint(
            "((status = 'COMPLETED' AND fallback_used = false AND report_content IS NOT NULL "
            "AND failure_reason IS NULL) "
            "OR (status = 'FALLBACK_COMPLETED' AND fallback_used = true "
            "AND report_content IS NOT NULL AND fallback_reason IS NOT NULL "
            "AND failure_reason IS NULL) "
            "OR (status = 'FAILED' AND report_content IS NULL AND failure_reason IS NOT NULL))",
            name="ck_ai_reports_status_payload",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_ai_reports_latency_nonnegative",
        ),
        CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_ai_reports_snapshot_hash_nonblank",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AIReportStatus] = mapped_column(
        Enum(AIReportStatus, name="ai_report_status"), nullable=False
    )
    report_content: Mapped[dict[str, Any] | None] = mapped_column(JSON_DOCUMENT, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fallback_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    repair_attempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_result: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False, default=dict)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="ai_report")
