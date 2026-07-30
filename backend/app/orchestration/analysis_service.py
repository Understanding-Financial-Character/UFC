from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.ai.factory import build_report_generator
from app.ai.grounded_report import (
    PROMPT_VERSION,
    GroundedReportInput,
    GroundedReportService,
)
from app.ai.report_generator import EvidenceItem, EvidenceValueType
from app.analysis.behavior_metrics import calculate_behavior_metrics
from app.analysis.contracts import (
    ANALYSIS_INPUT_SCHEMA_VERSION,
    BEHAVIOR_FEATURE_POLICY_VERSION,
    SYNTHETIC_SOURCE_TYPES,
    AnalysisInput,
    AnalysisMemberInput,
    AnalysisPeriod,
    AnalysisSourceType,
    AnalysisTransactionInput,
    AnalysisTransactionType,
    BehaviorGroup,
    BehaviorMetricsInput,
    BehaviorMetricsResult,
    ConsumptionMbtiResult,
    GroupPurposeType,
    ResultStatus,
    RuleEngineInput,
)
from app.analysis.preprocessing.normalizer import (
    normalize_datetime,
    normalize_merchant_key,
    preprocess_analysis_input,
)
from app.analysis.rules.scorer import score_consumption_mbti
from app.core.config import settings
from app.core.exceptions import ApiException
from app.modules.analysis_results.models import (
    AIReport,
    AIReportStatus,
    AnalysisRun,
    AnalysisRunStatus,
    BehaviorMetric,
    ConsumptionMBTIResult,
    ConsumptionMBTIType,
)
from app.modules.analysis_results.repository import (
    ACTIVE_ANALYSIS_STATUSES,
    AnalysisResultRepository,
)
from app.modules.groups.models import Group, GroupMember, MemberPersonality, RelationshipType
from app.modules.groups.service import get_owned_group_for_update, group_can_analyze
from app.modules.transactions.models import (
    Category,
    Transaction,
    TransactionSourceType,
    TransactionType,
)

ANALYSIS_VERSION = "be-orchestration-v1"
AI_REPORT_SCHEMA_VERSION = "grounded-ai-report-v1"
ANALYSIS_TIMEZONE = ZoneInfo("Asia/Seoul")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisExecutionResult:
    analysis_run: AnalysisRun
    behavior_metrics: tuple[BehaviorMetric, ...]
    consumption_mbti_result: ConsumptionMBTIResult | None
    ai_report: AIReport | None


def execute_group_analysis(
    db: Session,
    *,
    group_id: str,
    owner_user_id: str,
    period_start: date,
    period_end: date,
    report_service: GroundedReportService | None = None,
) -> AnalysisExecutionResult:
    if period_start > period_end:
        raise ApiException(
            code="VALIDATION_ERROR",
            message="period_start must be before or equal to period_end.",
            status_code=400,
            details={"field": "period_start"},
        )
    group = get_owned_group_for_update(db, group_id, owner_user_id)
    if not group_can_analyze(group):
        raise ApiException(
            code="GROUP_NOT_READY",
            message="Group must have 2-4 members with MBTI before analysis.",
            status_code=409,
        )
    prevent_concurrent_analysis(db, group.id)

    period = analysis_period_from_dates(period_start, period_end)
    transaction_rows = load_transaction_rows(db, group.id, period)
    source_type = infer_analysis_source_type(tuple(row[0] for row in transaction_rows))
    is_synthetic = source_type in SYNTHETIC_SOURCE_TYPES
    analysis_run_id = str(uuid.uuid4())
    analysis_input = build_analysis_input(
        analysis_id=analysis_run_id,
        group=group,
        period=period,
        transaction_rows=transaction_rows,
        source_type=source_type,
        is_synthetic=is_synthetic,
    )
    analysis_input_snapshot = build_analysis_input_snapshot(analysis_input)
    snapshot_hash = calculate_snapshot_hash(analysis_input_snapshot)

    repository = AnalysisResultRepository(db)
    analysis_run = repository.create_analysis_run(
        analysis_run_id=analysis_run_id,
        group_id=group.id,
        analysis_period_started_at=period.started_at,
        analysis_period_ended_at=period.ended_at,
        source_type=source_type,
        is_synthetic=is_synthetic,
        input_schema_version=analysis_input.schema_version,
        analysis_version=ANALYSIS_VERSION,
        snapshot_hash=snapshot_hash,
        analysis_input_snapshot=analysis_input_snapshot,
        status=AnalysisRunStatus.READY,
    )
    db.commit()
    return execute_analysis_run_from_input(
        db=db,
        repository=repository,
        analysis_run=analysis_run,
        group=group,
        analysis_input=analysis_input,
        source_type=source_type,
        report_service=report_service,
    )


def execute_analysis_run_from_input(
    *,
    db: Session,
    repository: AnalysisResultRepository,
    analysis_run: AnalysisRun,
    group: Group,
    analysis_input: AnalysisInput,
    source_type: AnalysisSourceType,
    report_service: GroundedReportService | None,
) -> AnalysisExecutionResult:
    period = analysis_input.analysis_period

    try:
        repository.update_analysis_run_status(analysis_run.id, status=AnalysisRunStatus.ANALYZING)
        db.commit()

        preprocessing_result = preprocess_analysis_input(analysis_input)
        behavior_metrics_result = calculate_behavior_metrics(
            BehaviorMetricsInput(
                transactions=preprocessing_result.normalized_transactions,
                observation_started_at=period.started_at,
                observation_ended_at=period.ended_at,
                source_type=source_type,
            )
        )
        rule_result = score_consumption_mbti(RuleEngineInput(behavior_metrics=behavior_metrics_result))
        result_status = combine_result_status(
            preprocessing_result.data_quality_report.result_status_candidate,
            rule_result.result_status,
        )
        provisional_reasons = combine_reasons(
            preprocessing_result.provisional_reasons,
            rule_result.provisional_reasons,
        )
        if result_status != ResultStatus.STANDARD and not provisional_reasons:
            provisional_reasons = ("ANALYSIS_LIMITED",)

        repository.complete_analysis_run(
            analysis_run.id,
            result_status=result_status,
            provisional_reasons=provisional_reasons,
            status=AnalysisRunStatus.COMPLETED,
        )
        behavior_metrics = tuple(
            save_behavior_metrics(
                repository=repository,
                analysis_run_id=analysis_run.id,
                behavior_metrics_result=behavior_metrics_result,
                rule_result=rule_result,
            )
        )
        consumption_result = save_consumption_result(
            repository=repository,
            analysis_run_id=analysis_run.id,
            rule_result=rule_result,
            result_status=result_status,
            limitations=preprocessing_result.limitations,
            data_quality=preprocessing_result.data_quality_report.__dict__,
        )
        if result_status == ResultStatus.INSUFFICIENT_DATA:
            db.commit()
            return AnalysisExecutionResult(
                analysis_run=refresh_analysis_run(db, analysis_run.id),
                behavior_metrics=behavior_metrics,
                consumption_mbti_result=consumption_result,
                ai_report=None,
            )

        repository.update_analysis_run_status(
            analysis_run.id,
            status=AnalysisRunStatus.REPORT_GENERATING,
        )
        db.commit()

        ai_report = generate_and_save_report(
            db=db,
            repository=repository,
            analysis_run=analysis_run,
            group=group,
            rule_result=rule_result,
            result_status=result_status,
            provisional_reasons=provisional_reasons,
            limitations=preprocessing_result.limitations,
            report_service=report_service,
        )
        final_status = final_analysis_status(ai_report)
        repository.complete_analysis_run(
            analysis_run.id,
            result_status=result_status,
            provisional_reasons=provisional_reasons,
            status=final_status,
        )
        db.commit()
        return AnalysisExecutionResult(
            analysis_run=refresh_analysis_run(db, analysis_run.id),
            behavior_metrics=behavior_metrics,
            consumption_mbti_result=consumption_result,
            ai_report=ai_report,
        )
    except Exception as exc:
        db.rollback()
        try:
            repository.fail_analysis_run(
                analysis_run.id,
                error_code="ANALYSIS_EXECUTION_FAILED",
                error_message=type(exc).__name__,
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to persist analysis failure state.",
                extra={"analysis_run_id": analysis_run.id},
            )
        raise


def retry_analysis(
    db: Session,
    *,
    analysis_run_id: str,
    owner_user_id: str,
    report_service: GroundedReportService | None = None,
) -> AnalysisExecutionResult:
    analysis_run = require_owned_analysis_run(db, analysis_run_id, owner_user_id)
    if analysis_run.status != AnalysisRunStatus.FAILED:
        raise ApiException(
            code="ANALYSIS_RETRY_NOT_ALLOWED",
            message="Only failed analyses can be retried.",
            status_code=409,
        )
    group = get_owned_group_for_update(db, analysis_run.group_id, owner_user_id)
    prevent_concurrent_analysis(db, group.id)
    if not has_valid_analysis_snapshot(analysis_run.analysis_input_snapshot):
        raise ApiException(
            code="ANALYSIS_SNAPSHOT_UNAVAILABLE",
            message="This analysis was created before input snapshots were supported and cannot be retried.",
            status_code=409,
        )
    analysis_input = analysis_input_from_snapshot(analysis_run.analysis_input_snapshot)
    repository = AnalysisResultRepository(db)
    retry_run = repository.create_analysis_run(
        analysis_run_id=str(uuid.uuid4()),
        group_id=group.id,
        analysis_period_started_at=analysis_run.analysis_period_started_at,
        analysis_period_ended_at=analysis_run.analysis_period_ended_at,
        source_type=analysis_run.source_type,
        is_synthetic=analysis_run.is_synthetic,
        input_schema_version=analysis_run.input_schema_version,
        analysis_version=ANALYSIS_VERSION,
        snapshot_hash=analysis_run.snapshot_hash,
        analysis_input_snapshot=analysis_run.analysis_input_snapshot,
        retried_from_analysis_id=analysis_run.id,
        status=AnalysisRunStatus.READY,
    )
    db.commit()
    return execute_analysis_run_from_input(
        db=db,
        repository=repository,
        analysis_run=retry_run,
        group=group,
        analysis_input=analysis_input,
        source_type=analysis_run.source_type,
        report_service=report_service,
    )


def retry_analysis_report(
    db: Session,
    *,
    analysis_run_id: str,
    owner_user_id: str,
    report_service: GroundedReportService | None = None,
) -> AnalysisExecutionResult:
    analysis_run = require_owned_analysis_run(db, analysis_run_id, owner_user_id)
    if (
        analysis_run.status != AnalysisRunStatus.PARTIALLY_COMPLETED
        or analysis_run.ai_report is None
        or analysis_run.ai_report.status != AIReportStatus.FAILED
        or analysis_run.consumption_mbti_result is None
        or not analysis_run.behavior_metrics
    ):
        raise ApiException(
            code="ANALYSIS_REPORT_RETRY_NOT_ALLOWED",
            message="Only analyses with failed AI reports and saved deterministic results can retry the report.",
            status_code=409,
        )
    if analysis_run.result_status is None:
        raise ApiException(
            code="ANALYSIS_REPORT_RETRY_NOT_ALLOWED",
            message="Analysis result status is required before retrying the report.",
            status_code=409,
        )
    result_status = analysis_run.result_status
    provisional_reasons = tuple(analysis_run.provisional_reasons)
    report_input = grounded_report_input_from_persisted_result(
        analysis_run=analysis_run,
        consumption_result=analysis_run.consumption_mbti_result,
    )

    repository = AnalysisResultRepository(db)
    repository.update_analysis_run_status(analysis_run.id, status=AnalysisRunStatus.REPORT_GENERATING)
    db.commit()

    ai_report = regenerate_saved_report(
        db=db,
        repository=repository,
        analysis_run=analysis_run,
        report_input=report_input,
        report_service=report_service,
    )
    final_status = final_analysis_status(ai_report)
    repository.complete_analysis_run(
        analysis_run.id,
        result_status=result_status,
        provisional_reasons=provisional_reasons,
        status=final_status,
    )
    db.commit()
    refreshed = refresh_analysis_run(db, analysis_run.id)
    return AnalysisExecutionResult(
        analysis_run=refreshed,
        behavior_metrics=tuple(refreshed.behavior_metrics),
        consumption_mbti_result=refreshed.consumption_mbti_result,
        ai_report=refreshed.ai_report,
    )


def require_owned_analysis_run(db: Session, analysis_run_id: str, owner_user_id: str) -> AnalysisRun:
    statement = analysis_run_query().where(AnalysisRun.id == analysis_run_id)
    analysis_run = db.scalar(statement)
    if analysis_run is None or analysis_run.group.owner_user_id != owner_user_id:
        raise ApiException(code="NOT_FOUND", message="Analysis was not found.", status_code=404)
    return analysis_run


def get_latest_group_analysis(
    db: Session,
    *,
    group_id: str,
    owner_user_id: str,
) -> AnalysisRun:
    group = get_owned_group_for_update(db, group_id, owner_user_id)
    analysis_run = db.scalar(
        analysis_run_query()
        .where(AnalysisRun.group_id == group.id)
        .order_by(AnalysisRun.created_at.desc())
        .limit(1)
    )
    if analysis_run is None:
        raise ApiException(code="NOT_FOUND", message="Analysis was not found.", status_code=404)
    return analysis_run


def prevent_concurrent_analysis(db: Session, group_id: str) -> None:
    active_run = db.scalar(
        select(AnalysisRun.id)
        .where(AnalysisRun.group_id == group_id, AnalysisRun.status.in_(ACTIVE_ANALYSIS_STATUSES))
        .limit(1)
    )
    if active_run is not None:
        raise ApiException(
            code="ANALYSIS_ALREADY_RUNNING",
            message="An analysis is already running for this group.",
            status_code=409,
        )


def analysis_period_from_dates(period_start: date, period_end: date) -> AnalysisPeriod:
    local_start = datetime.combine(period_start, time.min, tzinfo=ANALYSIS_TIMEZONE)
    local_end = datetime.combine(period_end, time.max, tzinfo=ANALYSIS_TIMEZONE)
    return AnalysisPeriod(
        started_at=local_start.astimezone(UTC),
        ended_at=local_end.astimezone(UTC),
    )


def analysis_run_query() -> Select[tuple[AnalysisRun]]:
    return select(AnalysisRun).options(
        selectinload(AnalysisRun.behavior_metrics),
        selectinload(AnalysisRun.consumption_mbti_result),
        selectinload(AnalysisRun.ai_report),
        selectinload(AnalysisRun.group),
    )


def refresh_analysis_run(db: Session, analysis_run_id: str) -> AnalysisRun:
    analysis_run = db.scalar(analysis_run_query().where(AnalysisRun.id == analysis_run_id))
    if analysis_run is None:
        raise RuntimeError("analysis_run disappeared after execution.")
    return analysis_run


def load_transaction_rows(
    db: Session,
    group_id: str,
    period: AnalysisPeriod,
) -> list[tuple[Transaction, Category | None]]:
    statement = (
        select(Transaction, Category)
        .join(Category, Transaction.category_id == Category.id, isouter=True)
        .where(
            Transaction.group_id == group_id,
            Transaction.transaction_at >= period.started_at,
            Transaction.transaction_at <= period.ended_at,
        )
        .order_by(Transaction.transaction_at, Transaction.id)
    )
    return list(db.execute(statement).all())


def infer_analysis_source_type(transactions: tuple[Transaction, ...]) -> AnalysisSourceType:
    if any(transaction.source_type == TransactionSourceType.MOCK for transaction in transactions):
        return AnalysisSourceType.MOCK
    if any(transaction.source_type == TransactionSourceType.MANUAL_ENTRY for transaction in transactions):
        return AnalysisSourceType.MANUAL
    return AnalysisSourceType.CSV


def build_analysis_input(
    *,
    analysis_id: str,
    group: Group,
    period: AnalysisPeriod,
    transaction_rows: list[tuple[Transaction, Category | None]],
    source_type: AnalysisSourceType,
    is_synthetic: bool,
) -> AnalysisInput:
    return AnalysisInput(
        analysis_id=analysis_id,
        group_id=group.id,
        group_purpose_type=group_purpose_type(group.relationship_type),
        analysis_period=period,
        source_type=source_type,
        is_synthetic=is_synthetic,
        members=tuple(
            AnalysisMemberInput(
                member_id=member.id,
                mbti_type=member.personality.mbti.value,
            )
            for member in group.members
            if member.personality is not None
        ),
        transactions=tuple(
            build_transaction_input(transaction, category)
            for transaction, category in transaction_rows
        ),
        schema_version=ANALYSIS_INPUT_SCHEMA_VERSION,
    )


def build_transaction_input(
    transaction: Transaction,
    category: Category | None,
) -> AnalysisTransactionInput:
    return AnalysisTransactionInput(
        transaction_id=transaction.id,
        group_id=transaction.group_id,
        member_id=transaction.member_id,
        occurred_at=ensure_aware_utc(transaction.transaction_at),
        amount=transaction.amount,
        category_code=category.code if category is not None and category.is_active else None,
        behavior_group=behavior_group_from_category(category),
        merchant_key=normalize_merchant_key(transaction.merchant_name),
        transaction_type=analysis_transaction_type(transaction.transaction_type),
        is_shared_expense=transaction.is_shared_expense,
        is_planned=transaction.is_planned,
        is_recurring=transaction.is_recurring,
        source_type=analysis_source_type(transaction.source_type),
        is_excluded=transaction.is_excluded,
    )


def group_purpose_type(relationship_type: RelationshipType) -> GroupPurposeType:
    if relationship_type == RelationshipType.FAMILY:
        return GroupPurposeType.LIVING_EXPENSE
    return GroupPurposeType.OTHER


def behavior_group_from_category(category: Category | None) -> BehaviorGroup | None:
    if category is None:
        return None
    return BehaviorGroup(category.behavior_group.value)


def analysis_transaction_type(transaction_type: TransactionType) -> AnalysisTransactionType:
    return AnalysisTransactionType(transaction_type.value)


def analysis_source_type(source_type: TransactionSourceType) -> AnalysisSourceType:
    if source_type == TransactionSourceType.MOCK:
        return AnalysisSourceType.MOCK
    if source_type == TransactionSourceType.MANUAL_ENTRY:
        return AnalysisSourceType.MANUAL
    return AnalysisSourceType.CSV


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value


def build_analysis_input_snapshot(analysis_input: AnalysisInput) -> dict[str, Any]:
    return {
        "schemaVersion": analysis_input.schema_version,
        "analysisId": analysis_input.analysis_id,
        "groupId": analysis_input.group_id,
        "groupPurposeType": analysis_input.group_purpose_type.value,
        "analysisPeriod": {
            "startedAt": normalize_datetime(analysis_input.analysis_period.started_at).isoformat(),
            "endedAt": normalize_datetime(analysis_input.analysis_period.ended_at).isoformat(),
        },
        "sourceType": analysis_input.source_type.value,
        "isSynthetic": analysis_input.is_synthetic,
        "members": [
            {"memberId": member.member_id, "mbtiType": member.mbti_type}
            for member in analysis_input.members
        ],
        "transactions": [
            {
                "transactionId": transaction.transaction_id,
                "memberId": transaction.member_id,
                "occurredAt": normalize_datetime(transaction.occurred_at).isoformat(),
                "amount": str(transaction.amount),
                "categoryCode": transaction.category_code,
                "behaviorGroup": transaction.behavior_group.value
                if transaction.behavior_group is not None
                else None,
                "merchantKey": transaction.merchant_key,
                "transactionType": transaction.transaction_type.value,
                "isSharedExpense": transaction.is_shared_expense,
                "isPlanned": transaction.is_planned,
                "isRecurring": transaction.is_recurring,
                "sourceType": transaction.source_type.value if transaction.source_type else None,
                "isExcluded": transaction.is_excluded,
            }
            for transaction in analysis_input.transactions
        ],
    }


def analysis_input_from_snapshot(snapshot: dict[str, Any]) -> AnalysisInput:
    period = snapshot["analysisPeriod"]
    return AnalysisInput(
        analysis_id=snapshot["analysisId"],
        group_id=snapshot["groupId"],
        group_purpose_type=GroupPurposeType(snapshot["groupPurposeType"]),
        analysis_period=AnalysisPeriod(
            started_at=datetime.fromisoformat(period["startedAt"]),
            ended_at=datetime.fromisoformat(period["endedAt"]),
        ),
        source_type=AnalysisSourceType(snapshot["sourceType"]),
        is_synthetic=bool(snapshot["isSynthetic"]),
        members=tuple(
            AnalysisMemberInput(
                member_id=member["memberId"],
                mbti_type=member["mbtiType"],
            )
            for member in snapshot["members"]
        ),
        transactions=tuple(
            AnalysisTransactionInput(
                transaction_id=transaction["transactionId"],
                group_id=snapshot["groupId"],
                member_id=transaction["memberId"],
                occurred_at=datetime.fromisoformat(transaction["occurredAt"]),
                amount=Decimal(transaction["amount"]),
                category_code=transaction["categoryCode"],
                behavior_group=(
                    BehaviorGroup(transaction["behaviorGroup"])
                    if transaction["behaviorGroup"] is not None
                    else None
                ),
                merchant_key=transaction["merchantKey"],
                transaction_type=AnalysisTransactionType(transaction["transactionType"]),
                is_shared_expense=transaction["isSharedExpense"],
                is_planned=transaction["isPlanned"],
                is_recurring=transaction["isRecurring"],
                source_type=(
                    AnalysisSourceType(transaction["sourceType"])
                    if transaction["sourceType"] is not None
                    else None
                ),
                is_excluded=transaction["isExcluded"],
            )
            for transaction in snapshot["transactions"]
        ),
        schema_version=snapshot["schemaVersion"],
    )


def has_valid_analysis_snapshot(snapshot: dict[str, Any]) -> bool:
    if not snapshot:
        return False
    required_keys = {
        "schemaVersion",
        "analysisId",
        "groupId",
        "groupPurposeType",
        "analysisPeriod",
        "sourceType",
        "isSynthetic",
        "members",
        "transactions",
    }
    if not required_keys.issubset(snapshot):
        return False
    period = snapshot.get("analysisPeriod")
    if not isinstance(period, dict) or not {"startedAt", "endedAt"}.issubset(period):
        return False
    return isinstance(snapshot.get("members"), list) and isinstance(snapshot.get("transactions"), list)


def calculate_snapshot_hash(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def combine_result_status(left: ResultStatus, right: ResultStatus) -> ResultStatus:
    if ResultStatus.INSUFFICIENT_DATA in {left, right}:
        return ResultStatus.INSUFFICIENT_DATA
    if ResultStatus.PROVISIONAL in {left, right}:
        return ResultStatus.PROVISIONAL
    return ResultStatus.STANDARD


def combine_reasons(*reason_groups: tuple[Any, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_group in reason_groups:
        for reason in reason_group:
            value = reason.value if hasattr(reason, "value") else str(reason)
            if value:
                reasons.append(value)
    return tuple(dict.fromkeys(reasons))


def save_behavior_metrics(
    *,
    repository: AnalysisResultRepository,
    analysis_run_id: str,
    behavior_metrics_result: BehaviorMetricsResult,
    rule_result: ConsumptionMbtiResult,
) -> list[BehaviorMetric]:
    contributions_by_feature = axis_contributions_by_feature(rule_result)
    return [
        repository.add_behavior_metric(
            analysis_run_id=analysis_run_id,
            feature_code=feature.feature_code.value,
            status=feature.status,
            raw_value=decimal_or_none(feature.raw_value),
            normalized_score=decimal_or_none(feature.normalized_score),
            unit=feature.unit,
            sample_count=feature.sample_count,
            unavailable_reason=None if feature.raw_value is not None else first_evidence(feature.evidence),
            evidence=feature.evidence,
            metric_metadata={
                "axisContributions": contributions_by_feature.get(feature.feature_code.value, []),
            },
            schema_version=behavior_metrics_result.schema_version,
            calculation_version=BEHAVIOR_FEATURE_POLICY_VERSION,
        )
        for feature in behavior_metrics_result.features
    ]


def axis_contributions_by_feature(rule_result: ConsumptionMbtiResult) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for axis_result in rule_result.axis_results:
        if axis_result.decided_pole is None:
            continue
        for contribution in axis_result.contributions:
            grouped.setdefault(contribution.feature_code.value, []).append(
                {
                    "axis": axis_result.axis.value,
                    "pole": axis_result.decided_pole,
                    "weight": contribution.normalized_weight,
                    "contribution": contribution.decided_pole_contribution,
                    "highPoleSupport": contribution.high_pole_support,
                    "lowPoleSupport": contribution.low_pole_support,
                    "signedContribution": contribution.signed_contribution,
                }
            )
    return grouped


def save_consumption_result(
    *,
    repository: AnalysisResultRepository,
    analysis_run_id: str,
    rule_result: ConsumptionMbtiResult,
    result_status: ResultStatus,
    limitations: tuple[str, ...],
    data_quality: dict[str, Any],
) -> ConsumptionMBTIResult:
    mbti_type = None
    if result_status != ResultStatus.INSUFFICIENT_DATA and rule_result.mbti_type:
        mbti_type = ConsumptionMBTIType(rule_result.mbti_type)
    return repository.save_consumption_mbti_result(
        analysis_run_id=analysis_run_id,
        mbti_type=mbti_type,
        ei_score=decimal_or_none(rule_result.axis_scores.get("EI")),
        sn_score=decimal_or_none(rule_result.axis_scores.get("SN")),
        tf_score=decimal_or_none(rule_result.axis_scores.get("TF")),
        jp_score=decimal_or_none(rule_result.axis_scores.get("JP")),
        confidence_level=rule_result.confidence.level.value,
        confidence_score=decimal_or_none(rule_result.confidence.score),
        coverage=decimal_or_none(average_coverage(rule_result.axis_coverage)),
        limitations=limitations,
        result_metadata={
            "axisCoverage": rule_result.axis_coverage,
            "axisMargins": rule_result.axis_margins,
            "primaryEvidence": [contribution_to_dict(item) for item in rule_result.primary_evidence],
            "dataQuality": json_ready(data_quality),
        },
        schema_version=rule_result.schema_version,
        rule_version=rule_result.rule_version,
    )


def generate_and_save_report(
    *,
    db: Session,
    repository: AnalysisResultRepository,
    analysis_run: AnalysisRun,
    group: Group,
    rule_result: ConsumptionMbtiResult,
    result_status: ResultStatus,
    provisional_reasons: tuple[str, ...],
    limitations: tuple[str, ...],
    report_service: GroundedReportService | None,
) -> AIReport | None:
    service = report_service or GroundedReportService(generator=build_report_generator(settings))
    try:
        report_result = service.generate(
            GroundedReportInput(
                spending_mbti=rule_result.mbti_type,
                axis_scores={
                    axis: score
                    for axis, score in rule_result.axis_scores.items()
                    if score is not None
                },
                confidence={
                    "level": rule_result.confidence.level.value,
                    "score": rule_result.confidence.score,
                },
                evidence=tuple(evidence_item(item) for item in rule_result.primary_evidence),
                member_mbti_summary=member_mbti_summary(group.members),
                limitations=limitations,
                result_status=result_status.value,
            )
        )
        return repository.save_ai_report(
            analysis_run_id=analysis_run.id,
            status=(
                AIReportStatus.FALLBACK_COMPLETED
                if report_result.metadata.fallback_used
                else AIReportStatus.COMPLETED
            ),
            report_content=report_result.report.model_dump(),
            model_name=report_result.metadata.model,
            prompt_version=report_result.metadata.prompt_version,
            latency_ms=report_result.metadata.latency_ms,
            fallback_used=report_result.metadata.fallback_used,
            fallback_reason=report_result.metadata.fallback_reason,
            repair_attempted=report_result.metadata.repair_attempted,
            validation_result=report_result.metadata.validation,
            failure_reason=None,
            schema_version=AI_REPORT_SCHEMA_VERSION,
        )
    except Exception as exc:  # noqa: BLE001 - isolate provider/runtime report failures.
        db.rollback()
        repository.save_ai_report(
            analysis_run_id=analysis_run.id,
            status=AIReportStatus.FAILED,
            report_content=None,
            model_name=None,
            prompt_version=PROMPT_VERSION,
            latency_ms=None,
            fallback_used=False,
            fallback_reason=None,
            repair_attempted=False,
            validation_result={},
            failure_reason=type(exc).__name__,
            schema_version=AI_REPORT_SCHEMA_VERSION,
        )
        repository.complete_analysis_run(
            analysis_run.id,
            result_status=result_status,
            provisional_reasons=provisional_reasons,
            status=AnalysisRunStatus.PARTIALLY_COMPLETED,
        )
        db.commit()
        return refresh_analysis_run(db, analysis_run.id).ai_report


def regenerate_saved_report(
    *,
    db: Session,
    repository: AnalysisResultRepository,
    analysis_run: AnalysisRun,
    report_input: GroundedReportInput,
    report_service: GroundedReportService | None,
) -> AIReport | None:
    service = report_service or GroundedReportService(generator=build_report_generator(settings))
    existing_report = analysis_run.ai_report
    consumption_result = analysis_run.consumption_mbti_result
    if existing_report is None or consumption_result is None:
        raise RuntimeError("report retry requires saved deterministic analysis and failed AI report.")
    try:
        report_result = service.generate(report_input)
        return repository.update_ai_report(
            existing_report,
            status=(
                AIReportStatus.FALLBACK_COMPLETED
                if report_result.metadata.fallback_used
                else AIReportStatus.COMPLETED
            ),
            report_content=report_result.report.model_dump(),
            model_name=report_result.metadata.model,
            prompt_version=report_result.metadata.prompt_version,
            latency_ms=report_result.metadata.latency_ms,
            fallback_used=report_result.metadata.fallback_used,
            fallback_reason=report_result.metadata.fallback_reason,
            repair_attempted=report_result.metadata.repair_attempted,
            validation_result=report_result.metadata.validation,
            failure_reason=None,
            schema_version=AI_REPORT_SCHEMA_VERSION,
        )
    except Exception as exc:  # noqa: BLE001 - keep report-only retry failures isolated.
        db.rollback()
        repository.update_ai_report(
            existing_report,
            status=AIReportStatus.FAILED,
            report_content=None,
            model_name=None,
            prompt_version=PROMPT_VERSION,
            latency_ms=None,
            fallback_used=False,
            fallback_reason=None,
            repair_attempted=False,
            validation_result={},
            failure_reason=type(exc).__name__,
            schema_version=AI_REPORT_SCHEMA_VERSION,
        )
        repository.complete_analysis_run(
            analysis_run.id,
            result_status=report_input_status(report_input),
            provisional_reasons=analysis_run.provisional_reasons,
            status=AnalysisRunStatus.PARTIALLY_COMPLETED,
        )
        db.commit()
        return refresh_analysis_run(db, analysis_run.id).ai_report


def grounded_report_input_from_persisted_result(
    *,
    analysis_run: AnalysisRun,
    consumption_result: ConsumptionMBTIResult,
) -> GroundedReportInput:
    if analysis_run.result_status is None:
        raise RuntimeError("analysis result status is required.")
    return GroundedReportInput(
        spending_mbti=consumption_result.mbti_type.value if consumption_result.mbti_type else None,
        axis_scores={
            axis: float(score)
            for axis, score in {
                "EI": consumption_result.ei_score,
                "SN": consumption_result.sn_score,
                "TF": consumption_result.tf_score,
                "JP": consumption_result.jp_score,
            }.items()
            if score is not None
        },
        confidence={
            "level": consumption_result.confidence_level,
            "score": (
                float(consumption_result.confidence_score)
                if consumption_result.confidence_score is not None
                else None
            ),
        },
        evidence=tuple(
            persisted_evidence_item(item)
            for item in consumption_result.result_metadata.get("primaryEvidence", [])
        ),
        member_mbti_summary=member_mbti_summary(analysis_run.group.members),
        limitations=tuple(consumption_result.limitations),
        result_status=analysis_run.result_status.value,
    )


def persisted_evidence_item(item: dict[str, Any]) -> EvidenceItem:
    basis_values = item.get("evidence") or ()
    basis = basis_values[0] if basis_values else str(item.get("featureCode", "UNKNOWN_FEATURE"))
    return EvidenceItem(
        metric=str(item.get("featureCode", "UNKNOWN_FEATURE")),
        value=item.get("decidedPoleContribution"),
        basis=basis,
        value_type=EvidenceValueType.SCORE,
    )


def report_input_status(report_input: GroundedReportInput) -> ResultStatus:
    return ResultStatus(report_input.result_status)


def final_analysis_status(ai_report: AIReport | None) -> AnalysisRunStatus:
    if ai_report is None or ai_report.status == AIReportStatus.FAILED:
        return AnalysisRunStatus.PARTIALLY_COMPLETED
    if ai_report.fallback_used:
        return AnalysisRunStatus.COMPLETED_WITH_FALLBACK
    return AnalysisRunStatus.COMPLETED


def evidence_item(contribution: Any) -> EvidenceItem:
    basis = contribution.evidence[0] if contribution.evidence else contribution.feature_code.value
    return EvidenceItem(
        metric=contribution.feature_code.value,
        value=contribution.decided_pole_contribution,
        basis=basis,
        value_type=EvidenceValueType.SCORE,
    )


def member_mbti_summary(members: list[GroupMember]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for member in members:
        personality: MemberPersonality | None = member.personality
        if personality is None:
            continue
        summary[personality.mbti.value] = summary.get(personality.mbti.value, 0) + 1
    return summary


def contribution_to_dict(contribution: Any) -> dict[str, Any]:
    return {
        "axis": contribution.axis.value,
        "featureCode": contribution.feature_code.value,
        "direction": contribution.direction.value,
        "weight": contribution.weight,
        "normalizedWeight": contribution.normalized_weight,
        "featureScore": contribution.feature_score,
        "highPoleSupport": contribution.high_pole_support,
        "lowPoleSupport": contribution.low_pole_support,
        "signedContribution": contribution.signed_contribution,
        "decidedPoleContribution": contribution.decided_pole_contribution,
        "evidence": list(contribution.evidence),
    }


def average_coverage(axis_coverage: dict[str, float]) -> float | None:
    if not axis_coverage:
        return None
    return sum(axis_coverage.values()) / len(axis_coverage)


def decimal_or_none(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def first_evidence(evidence: tuple[str, ...]) -> str:
    return evidence[0][:120] if evidence else "Feature is unavailable."


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {key: json_ready(child) for key, child in value.items()}
    if isinstance(value, list | tuple):
        return [json_ready(child) for child in value]
    return value
