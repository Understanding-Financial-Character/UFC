from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import DatabaseSession
from app.modules.analyses.schemas import (
    AIReportResponse,
    AnalysisCreateRequest,
    AnalysisResponse,
    BehaviorMetricResponse,
    ConsumptionMbtiResponse,
)
from app.modules.analysis_results.models import (
    AIReport,
    AnalysisRun,
    BehaviorMetric,
    ConsumptionMBTIResult,
)
from app.modules.auth.dependencies import AuthenticatedPrincipal
from app.orchestration import analysis_service

router = APIRouter(tags=["analyses"])


@router.post(
    "/groups/{group_id}/analyses",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_analysis(
    group_id: str,
    payload: AnalysisCreateRequest,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> AnalysisResponse:
    result = analysis_service.execute_group_analysis(
        db,
        group_id=group_id,
        owner_user_id=principal.user_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    return build_analysis_response(result.analysis_run)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> AnalysisResponse:
    analysis_run = analysis_service.require_owned_analysis_run(
        db,
        analysis_run_id=analysis_id,
        owner_user_id=principal.user_id,
    )
    return build_analysis_response(analysis_run)


@router.get("/groups/{group_id}/analyses/latest", response_model=AnalysisResponse)
def get_latest_group_analysis(
    group_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> AnalysisResponse:
    analysis_run = analysis_service.get_latest_group_analysis(
        db,
        group_id=group_id,
        owner_user_id=principal.user_id,
    )
    return build_analysis_response(analysis_run)


@router.post(
    "/analyses/{analysis_id}/retry",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_analysis(
    analysis_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> AnalysisResponse:
    result = analysis_service.retry_analysis(
        db,
        analysis_run_id=analysis_id,
        owner_user_id=principal.user_id,
    )
    return build_analysis_response(result.analysis_run)


@router.post(
    "/analyses/{analysis_id}/report/retry",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_analysis_report(
    analysis_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> AnalysisResponse:
    result = analysis_service.retry_analysis_report(
        db,
        analysis_run_id=analysis_id,
        owner_user_id=principal.user_id,
    )
    return build_analysis_response(result.analysis_run)


def build_analysis_response(analysis_run: AnalysisRun) -> AnalysisResponse:
    return AnalysisResponse(
        analysis_id=analysis_run.id,
        group_id=analysis_run.group_id,
        status=analysis_run.status,
        result_status=analysis_run.result_status,
        provisional_reasons=list(analysis_run.provisional_reasons),
        analysis_period_started_at=analysis_run.analysis_period_started_at,
        analysis_period_ended_at=analysis_run.analysis_period_ended_at,
        source_type=analysis_run.source_type,
        is_synthetic=analysis_run.is_synthetic,
        input_schema_version=analysis_run.input_schema_version,
        analysis_version=analysis_run.analysis_version,
        snapshot_hash=analysis_run.snapshot_hash,
        error_code=analysis_run.error_code,
        error_message=analysis_run.error_message,
        created_at=analysis_run.created_at,
        updated_at=analysis_run.updated_at,
        behavior_metrics=[
            build_behavior_metric_response(metric) for metric in analysis_run.behavior_metrics
        ],
        consumption_mbti_result=build_consumption_mbti_response(
            analysis_run.consumption_mbti_result
        ),
        ai_report=build_ai_report_response(analysis_run.ai_report),
    )


def build_behavior_metric_response(metric: BehaviorMetric) -> BehaviorMetricResponse:
    return BehaviorMetricResponse(
        feature_code=metric.feature_code,
        status=metric.status.value,
        raw_value=metric.raw_value,
        normalized_score=metric.normalized_score,
        unit=metric.unit.value,
        sample_count=metric.sample_count,
        unavailable_reason=metric.unavailable_reason,
        evidence=list(metric.evidence),
    )


def build_consumption_mbti_response(
    result: ConsumptionMBTIResult | None,
) -> ConsumptionMbtiResponse | None:
    if result is None:
        return None
    return ConsumptionMbtiResponse(
        mbti_type=result.mbti_type.value if result.mbti_type else None,
        result_status=result.result_status,
        axis_scores={
            "EI": result.ei_score,
            "SN": result.sn_score,
            "TF": result.tf_score,
            "JP": result.jp_score,
        },
        confidence={
            "level": result.confidence_level,
            "score": result.confidence_score,
        },
        coverage=result.coverage,
        limitations=list(result.limitations),
        rule_version=result.rule_version,
        metadata=result.result_metadata,
    )


def build_ai_report_response(report: AIReport | None) -> AIReportResponse | None:
    if report is None:
        return None
    return AIReportResponse(
        status=report.status.value,
        fallback_used=report.fallback_used,
        fallback_reason=report.fallback_reason,
        model_name=report.model_name,
        prompt_version=report.prompt_version,
        report_content=report.report_content,
    )
