from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.constants import AXIS_SCORE_DIRECTIONS
from app.modules.analysis_results.models import (
    AIReport,
    AIReportStatus,
    AnalysisRun,
    AnalysisRunStatus,
    AnalysisSourceType,
    BehaviorMetric,
    ConsumptionMBTIResult,
    ConsumptionMBTIType,
    ResultStatus,
)

VALID_AXES = frozenset(AXIS_SCORE_DIRECTIONS)
VALID_HIGH_POLES = {axis: values["high"] for axis, values in AXIS_SCORE_DIRECTIONS.items()}
VALID_LOW_POLES = {axis: values["low"] for axis, values in AXIS_SCORE_DIRECTIONS.items()}


class AnalysisResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_analysis_run(
        self,
        *,
        group_id: str,
        status: AnalysisRunStatus,
        result_status: ResultStatus,
        provisional_reasons: Sequence[str],
        analysis_period_started_at: datetime,
        analysis_period_ended_at: datetime,
        source_type: AnalysisSourceType,
        is_synthetic: bool,
        input_schema_version: str,
        analysis_version: str,
        snapshot_hash: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AnalysisRun:
        self._validate_nonblank("input_schema_version", input_schema_version)
        self._validate_nonblank("analysis_version", analysis_version)
        self._validate_nonblank("snapshot_hash", snapshot_hash)
        if analysis_period_started_at > analysis_period_ended_at:
            raise ValueError("analysis_period_started_at must be before or equal to analysis_period_ended_at.")
        run = AnalysisRun(
            group_id=group_id,
            status=status,
            result_status=result_status,
            provisional_reasons=list(provisional_reasons),
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
        metric_code: str,
        metric_value: Decimal | None,
        is_available: bool,
        unavailable_reason: str | None,
        evidence: Sequence[dict[str, Any]],
        metric_metadata: dict[str, Any],
        schema_version: str,
        calculation_version: str,
        snapshot_hash: str,
    ) -> BehaviorMetric:
        self._validate_nonblank("metric_code", metric_code)
        self._validate_nonblank("schema_version", schema_version)
        self._validate_nonblank("calculation_version", calculation_version)
        self._validate_nonblank("snapshot_hash", snapshot_hash)
        if is_available and metric_value is None:
            raise ValueError("metric_value is required when a behavior metric is available.")
        self._validate_axis_contributions(metric_metadata)
        metric = BehaviorMetric(
            analysis_run_id=analysis_run_id,
            metric_code=metric_code,
            metric_value=metric_value,
            is_available=is_available,
            unavailable_reason=unavailable_reason,
            evidence=list(evidence),
            metric_metadata=metric_metadata,
            schema_version=schema_version,
            calculation_version=calculation_version,
            snapshot_hash=snapshot_hash,
        )
        self.db.add(metric)
        self.db.flush()
        return metric

    def list_behavior_metrics(self, analysis_run_id: str) -> list[BehaviorMetric]:
        return list(
            self.db.scalars(
                select(BehaviorMetric)
                .where(BehaviorMetric.analysis_run_id == analysis_run_id)
                .order_by(BehaviorMetric.metric_code)
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
        snapshot_hash: str,
    ) -> ConsumptionMBTIResult:
        self._validate_nonblank("schema_version", schema_version)
        self._validate_nonblank("rule_version", rule_version)
        self._validate_nonblank("snapshot_hash", snapshot_hash)
        analysis_run = self._require_analysis_run(analysis_run_id)
        if analysis_run.result_status == ResultStatus.INSUFFICIENT_DATA and mbti_type is not None:
            raise ValueError("mbti_type must be null when result_status is INSUFFICIENT_DATA.")
        result = ConsumptionMBTIResult(
            analysis_run_id=analysis_run_id,
            mbti_type=mbti_type,
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
            snapshot_hash=snapshot_hash,
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
        validation_result: dict[str, Any],
        failure_reason: str | None,
        schema_version: str,
        snapshot_hash: str,
    ) -> AIReport:
        self._validate_nonblank("schema_version", schema_version)
        self._validate_nonblank("snapshot_hash", snapshot_hash)
        if status in {AIReportStatus.COMPLETED, AIReportStatus.FALLBACK_COMPLETED} and report_content is None:
            raise ValueError("report_content is required for completed AI reports.")
        if status == AIReportStatus.FAILED and not failure_reason:
            raise ValueError("failure_reason is required for failed AI reports.")
        report = AIReport(
            analysis_run_id=analysis_run_id,
            status=status,
            report_content=report_content,
            model_name=model_name,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            validation_result=validation_result,
            failure_reason=failure_reason,
            schema_version=schema_version,
            snapshot_hash=snapshot_hash,
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
