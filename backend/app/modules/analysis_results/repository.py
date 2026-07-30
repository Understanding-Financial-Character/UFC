from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.constants import AXIS_SCORE_DIRECTIONS
from app.analysis.contracts import (
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    ProvisionalReason,
    ResultStatus,
)
from app.modules.analysis_results.models import (
    AIReport,
    AIReportStatus,
    AnalysisRun,
    AnalysisRunStatus,
    AnalysisSourceType,
    BehaviorMetric,
    ConsumptionMBTIResult,
    ConsumptionMBTIType,
)

VALID_AXES = frozenset(AXIS_SCORE_DIRECTIONS)
VALID_HIGH_POLES = {axis: values["high"] for axis, values in AXIS_SCORE_DIRECTIONS.items()}
VALID_LOW_POLES = {axis: values["low"] for axis, values in AXIS_SCORE_DIRECTIONS.items()}
ACTIVE_ANALYSIS_STATUSES = frozenset(
    {
        AnalysisRunStatus.READY,
        AnalysisRunStatus.ANALYZING,
        AnalysisRunStatus.REPORT_GENERATING,
        AnalysisRunStatus.PENDING,
        AnalysisRunStatus.RUNNING,
    }
)
SUCCESSFUL_ANALYSIS_STATUSES = frozenset(
    {
        AnalysisRunStatus.COMPLETED,
        AnalysisRunStatus.COMPLETED_WITH_FALLBACK,
        AnalysisRunStatus.PARTIALLY_COMPLETED,
    }
)


class AnalysisResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_analysis_run(
        self,
        *,
        group_id: str,
        analysis_period_started_at: datetime,
        analysis_period_ended_at: datetime,
        source_type: AnalysisSourceType,
        is_synthetic: bool,
        input_schema_version: str,
        analysis_version: str,
        snapshot_hash: str,
        error_code: str | None = None,
        error_message: str | None = None,
        status: AnalysisRunStatus = AnalysisRunStatus.READY,
    ) -> AnalysisRun:
        if status not in ACTIVE_ANALYSIS_STATUSES:
            raise ValueError("create_analysis_run only supports active analysis statuses.")
        self._validate_nonblank("input_schema_version", input_schema_version)
        self._validate_nonblank("analysis_version", analysis_version)
        self._validate_nonblank("snapshot_hash", snapshot_hash)
        if analysis_period_started_at > analysis_period_ended_at:
            raise ValueError("analysis_period_started_at must be before or equal to analysis_period_ended_at.")
        run = AnalysisRun(
            group_id=group_id,
            status=status,
            result_status=None,
            provisional_reasons=[],
            analysis_period_started_at=analysis_period_started_at,
            analysis_period_ended_at=analysis_period_ended_at,
            source_type=source_type,
            is_synthetic=is_synthetic,
            input_schema_version=input_schema_version,
            analysis_version=analysis_version,
            snapshot_hash=snapshot_hash,
            error_code=error_code,
            error_message=error_message,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def complete_analysis_run(
        self,
        analysis_run_id: str,
        *,
        result_status: ResultStatus,
        provisional_reasons: Sequence[ProvisionalReason | str],
        status: AnalysisRunStatus = AnalysisRunStatus.COMPLETED,
    ) -> AnalysisRun:
        if status not in SUCCESSFUL_ANALYSIS_STATUSES:
            raise ValueError("complete_analysis_run requires a successful terminal status.")
        self._validate_result_status_reasons(result_status, provisional_reasons)
        analysis_run = self._require_analysis_run(analysis_run_id)
        analysis_run.status = status
        analysis_run.result_status = result_status
        analysis_run.provisional_reasons = [self._enum_value(reason) for reason in provisional_reasons]
        analysis_run.error_code = None
        analysis_run.error_message = None
        self.db.flush()
        return analysis_run

    def update_analysis_run_status(
        self,
        analysis_run_id: str,
        *,
        status: AnalysisRunStatus,
    ) -> AnalysisRun:
        if status in SUCCESSFUL_ANALYSIS_STATUSES:
            raise ValueError("Use complete_analysis_run for successful terminal statuses.")
        analysis_run = self._require_analysis_run(analysis_run_id)
        analysis_run.status = status
        analysis_run.result_status = None
        self.db.flush()
        return analysis_run

    def fail_analysis_run(
        self,
        analysis_run_id: str,
        *,
        error_code: str,
        error_message: str,
    ) -> AnalysisRun:
        self._validate_nonblank("error_code", error_code)
        self._validate_nonblank("error_message", error_message)
        analysis_run = self._require_analysis_run(analysis_run_id)
        analysis_run.status = AnalysisRunStatus.FAILED
        analysis_run.result_status = None
        analysis_run.error_code = error_code
        analysis_run.error_message = error_message
        self.db.flush()
        return analysis_run

    def get_analysis_run(self, analysis_run_id: str) -> AnalysisRun | None:
        return self.db.get(AnalysisRun, analysis_run_id)

    def list_group_analysis_runs(self, group_id: str) -> list[AnalysisRun]:
        return list(
            self.db.scalars(
                select(AnalysisRun)
                .where(AnalysisRun.group_id == group_id)
                .order_by(AnalysisRun.created_at.desc())
            ).all()
        )

    def add_behavior_metric(
        self,
        *,
        analysis_run_id: str,
        feature_code: str,
        status: BehaviorFeatureStatus,
        raw_value: Decimal | None,
        normalized_score: Decimal | None,
        unit: BehaviorFeatureUnit,
        sample_count: int,
        unavailable_reason: str | None,
        evidence: Sequence[str],
        metric_metadata: dict[str, Any],
        schema_version: str,
        calculation_version: str,
    ) -> BehaviorMetric:
        analysis_run = self._require_analysis_run(analysis_run_id)
        self._validate_nonblank("feature_code", feature_code)
        self._validate_nonblank("schema_version", schema_version)
        self._validate_nonblank("calculation_version", calculation_version)
        self._validate_behavior_feature_payload(
            status=status,
            raw_value=raw_value,
            normalized_score=normalized_score,
            sample_count=sample_count,
            unavailable_reason=unavailable_reason,
        )
        self._validate_axis_contributions(metric_metadata)
        metric = BehaviorMetric(
            analysis_run_id=analysis_run_id,
            feature_code=feature_code,
            status=status,
            raw_value=raw_value,
            normalized_score=normalized_score,
            unit=unit,
            sample_count=sample_count,
            unavailable_reason=unavailable_reason,
            evidence=list(evidence),
            metric_metadata=metric_metadata,
            schema_version=schema_version,
            calculation_version=calculation_version,
            snapshot_hash=analysis_run.snapshot_hash,
        )
        self.db.add(metric)
        self.db.flush()
        return metric

    def list_behavior_metrics(self, analysis_run_id: str) -> list[BehaviorMetric]:
        return list(
            self.db.scalars(
                select(BehaviorMetric)
                .where(BehaviorMetric.analysis_run_id == analysis_run_id)
                .order_by(BehaviorMetric.feature_code)
            ).all()
        )

    def save_consumption_mbti_result(
        self,
        *,
        analysis_run_id: str,
        mbti_type: ConsumptionMBTIType | None,
        ei_score: Decimal | None,
        sn_score: Decimal | None,
        tf_score: Decimal | None,
        jp_score: Decimal | None,
        confidence_level: str | None,
        confidence_score: Decimal | None,
        coverage: Decimal | None,
        limitations: Sequence[str],
        result_metadata: dict[str, Any],
        schema_version: str,
        rule_version: str,
    ) -> ConsumptionMBTIResult:
        self._validate_nonblank("schema_version", schema_version)
        self._validate_nonblank("rule_version", rule_version)
        analysis_run = self._require_analysis_run(analysis_run_id)
        if analysis_run.status not in SUCCESSFUL_ANALYSIS_STATUSES or analysis_run.result_status is None:
            raise ValueError("analysis_run must be completed before saving consumption MBTI result.")
        if analysis_run.result_status == ResultStatus.INSUFFICIENT_DATA and mbti_type is not None:
            raise ValueError("mbti_type must be null when result_status is INSUFFICIENT_DATA.")
        result = ConsumptionMBTIResult(
            analysis_run_id=analysis_run_id,
            mbti_type=mbti_type,
            result_status=analysis_run.result_status,
            ei_score=ei_score,
            sn_score=sn_score,
            tf_score=tf_score,
            jp_score=jp_score,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            coverage=coverage,
            limitations=list(limitations),
            axis_score_directions=AXIS_SCORE_DIRECTIONS,
            result_metadata=result_metadata,
            schema_version=schema_version,
            rule_version=rule_version,
            snapshot_hash=analysis_run.snapshot_hash,
        )
        self.db.add(result)
        self.db.flush()
        return result

    def save_ai_report(
        self,
        *,
        analysis_run_id: str,
        status: AIReportStatus,
        report_content: dict[str, Any] | None,
        model_name: str | None,
        prompt_version: str | None,
        latency_ms: int | None,
        fallback_used: bool,
        fallback_reason: str | None,
        repair_attempted: bool,
        validation_result: dict[str, Any],
        failure_reason: str | None,
        schema_version: str,
    ) -> AIReport:
        analysis_run = self._require_analysis_run(analysis_run_id)
        self._validate_nonblank("schema_version", schema_version)
        self._validate_ai_report_payload(
            status=status,
            report_content=report_content,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            failure_reason=failure_reason,
        )
        report = AIReport(
            analysis_run_id=analysis_run_id,
            status=status,
            report_content=report_content,
            model_name=model_name,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            repair_attempted=repair_attempted,
            validation_result=validation_result,
            failure_reason=failure_reason,
            schema_version=schema_version,
            snapshot_hash=analysis_run.snapshot_hash,
        )
        self.db.add(report)
        self.db.flush()
        return report

    def _require_analysis_run(self, analysis_run_id: str) -> AnalysisRun:
        analysis_run = self.get_analysis_run(analysis_run_id)
        if analysis_run is None:
            raise ValueError("analysis_run was not found.")
        return analysis_run

    @staticmethod
    def _validate_nonblank(field_name: str, value: str) -> None:
        if not value.strip():
            raise ValueError(f"{field_name} must not be blank.")

    @staticmethod
    def _enum_value(value: ProvisionalReason | str) -> str:
        return value.value if isinstance(value, ProvisionalReason) else value

    @classmethod
    def _validate_result_status_reasons(
        cls,
        result_status: ResultStatus,
        provisional_reasons: Sequence[ProvisionalReason | str],
    ) -> None:
        reasons = [cls._enum_value(reason) for reason in provisional_reasons]
        if any(not reason.strip() for reason in reasons):
            raise ValueError("provisional_reasons must not contain blank values.")
        if result_status == ResultStatus.STANDARD and reasons:
            raise ValueError("STANDARD result_status must not have provisional_reasons.")
        if result_status != ResultStatus.STANDARD and not reasons:
            raise ValueError("Non-standard result_status requires provisional_reasons.")

    @staticmethod
    def _validate_behavior_feature_payload(
        *,
        status: BehaviorFeatureStatus,
        raw_value: Decimal | None,
        normalized_score: Decimal | None,
        sample_count: int,
        unavailable_reason: str | None,
    ) -> None:
        if sample_count < 0:
            raise ValueError("sample_count must be non-negative.")
        if normalized_score is not None and not Decimal(0) <= normalized_score <= Decimal(1):
            raise ValueError("normalized_score must be between 0 and 1.")
        if status == BehaviorFeatureStatus.AVAILABLE and (
            raw_value is None or normalized_score is None
        ):
            raise ValueError("AVAILABLE behavior features require raw_value and normalized_score.")
        if status == BehaviorFeatureStatus.AVAILABLE and unavailable_reason is not None:
            raise ValueError("AVAILABLE behavior features must not have unavailable_reason.")
        if status == BehaviorFeatureStatus.UNAVAILABLE:
            if raw_value is not None or normalized_score is not None:
                raise ValueError("UNAVAILABLE behavior features must not have values.")
            if not unavailable_reason:
                raise ValueError("UNAVAILABLE behavior features require unavailable_reason.")

    @staticmethod
    def _validate_ai_report_payload(
        *,
        status: AIReportStatus,
        report_content: dict[str, Any] | None,
        fallback_used: bool,
        fallback_reason: str | None,
        failure_reason: str | None,
    ) -> None:
        if status == AIReportStatus.COMPLETED:
            if fallback_used or report_content is None or failure_reason is not None:
                raise ValueError("COMPLETED AI report payload is inconsistent.")
        elif status == AIReportStatus.FALLBACK_COMPLETED:
            if (
                not fallback_used
                or report_content is None
                or not fallback_reason
                or failure_reason is not None
            ):
                raise ValueError("FALLBACK_COMPLETED AI report payload is inconsistent.")
        elif status == AIReportStatus.FAILED and (report_content is not None or not failure_reason):
            raise ValueError("FAILED AI report payload is inconsistent.")

    @staticmethod
    def _validate_axis_contributions(metric_metadata: dict[str, Any]) -> None:
        axis_contributions = metric_metadata.get("axisContributions")
        if axis_contributions is None:
            return
        if not isinstance(axis_contributions, list):
            raise TypeError("metric_metadata.axisContributions must be a list.")
        for contribution in axis_contributions:
            if not isinstance(contribution, dict):
                raise TypeError("Each axis contribution must be an object.")
            axis = contribution.get("axis")
            pole = contribution.get("pole")
            if axis not in VALID_AXES:
                raise ValueError("Axis contribution has an invalid axis.")
            if pole not in {VALID_LOW_POLES[axis], VALID_HIGH_POLES[axis]}:
                raise ValueError("Axis contribution pole does not match its axis.")
            if "weight" not in contribution or "contribution" not in contribution:
                raise ValueError("Axis contribution requires weight and contribution.")
