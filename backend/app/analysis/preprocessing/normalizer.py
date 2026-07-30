from __future__ import annotations

import unicodedata
from datetime import UTC, datetime

from app.analysis.contracts import (
    AnalysisInput,
    AnalysisSourceType,
    ExcludedTransaction,
    NormalizedTransaction,
    PreprocessingResult,
)
from app.analysis.errors import AnalysisInputError
from app.analysis.preprocessing.quality import build_data_quality_report
from app.analysis.preprocessing.transaction_policy import exclusion_reason_for


def preprocess_analysis_input(analysis_input: AnalysisInput) -> PreprocessingResult:
    validate_analysis_input(analysis_input)
    normalized_transactions: list[NormalizedTransaction] = []
    excluded_transactions: list[ExcludedTransaction] = []

    for transaction in analysis_input.transactions:
        reason = exclusion_reason_for(transaction)
        if reason is not None:
            excluded_transactions.append(
                ExcludedTransaction(
                    transaction_id=transaction.transaction_id,
                    reason=reason,
                    transaction_type=transaction.transaction_type,
                )
            )
            continue
        normalized_transactions.append(
            NormalizedTransaction(
                transaction_id=transaction.transaction_id,
                group_id=transaction.group_id,
                member_id=transaction.member_id,
                occurred_at=normalize_datetime(transaction.occurred_at),
                amount=transaction.amount,
                category_code=normalize_optional_code(transaction.category_code),
                behavior_group=transaction.behavior_group,
                merchant_key=normalize_merchant_key(transaction.merchant_key),
                transaction_type=transaction.transaction_type,
                is_shared_expense=transaction.is_shared_expense,
                is_planned=transaction.is_planned,
                is_recurring=transaction.is_recurring,
                source_type=transaction.source_type or analysis_input.source_type,
            )
        )

    ordered_transactions = tuple(
        sorted(
            normalized_transactions,
            key=lambda transaction: (transaction.occurred_at, transaction.transaction_id),
        )
    )
    data_quality_report = build_data_quality_report(
        analysis_input=analysis_input,
        normalized_transactions=ordered_transactions,
        excluded_count=len(excluded_transactions),
    )
    return PreprocessingResult(
        normalized_transactions=ordered_transactions,
        excluded_transactions=tuple(excluded_transactions),
        included_count=data_quality_report.included_count,
        excluded_count=data_quality_report.excluded_count,
        data_quality_score=data_quality_report.data_quality_score,
        analysis_eligible=data_quality_report.analysis_eligible,
        result_status_candidate=data_quality_report.result_status_candidate,
        provisional_reasons=data_quality_report.provisional_reasons,
        limitations=data_quality_report.limitations,
        data_quality_report=data_quality_report,
    )


def validate_analysis_input(analysis_input: AnalysisInput) -> None:
    if analysis_input.schema_version != "analysis-input-v1":
        raise AnalysisInputError("Unsupported analysis input schema version.")
    if analysis_input.analysis_period.started_at > analysis_input.analysis_period.ended_at:
        raise AnalysisInputError("Analysis period start must be before or equal to end.")
    if analysis_input.source_type in {
        AnalysisSourceType.MOCK,
        AnalysisSourceType.INTERNAL_TEST,
    } and not analysis_input.is_synthetic:
        raise AnalysisInputError("Synthetic source types must be marked as synthetic.")
    for value, field in (
        (analysis_input.analysis_period.started_at, "analysis_period.started_at"),
        (analysis_input.analysis_period.ended_at, "analysis_period.ended_at"),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            raise AnalysisInputError(f"{field} must include timezone information.")
    period_start = normalize_datetime(analysis_input.analysis_period.started_at)
    period_end = normalize_datetime(analysis_input.analysis_period.ended_at)
    for transaction in analysis_input.transactions:
        if transaction.group_id != analysis_input.group_id:
            raise AnalysisInputError("Transaction group_id must match analysis group_id.")
        if transaction.occurred_at.tzinfo is None or transaction.occurred_at.utcoffset() is None:
            raise AnalysisInputError("Transaction occurred_at must include timezone information.")
        if transaction.source_type is not None and transaction.source_type != analysis_input.source_type:
            raise AnalysisInputError("Transaction source_type must match analysis source_type.")
        transaction_time = normalize_datetime(transaction.occurred_at)
        if not period_start <= transaction_time <= period_end:
            raise AnalysisInputError("Transaction occurred_at must fall within analysis_period.")
        if transaction.amount <= 0:
            raise AnalysisInputError("Transaction amount must be positive.")


def normalize_datetime(value: datetime) -> datetime:
    return value.astimezone(UTC)


def normalize_optional_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def normalize_merchant_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    key_parts: list[str] = []
    previous_was_separator = False
    for character in normalized:
        if character.isalnum():
            key_parts.append(character)
            previous_was_separator = False
            continue
        if not previous_was_separator:
            key_parts.append("-")
            previous_was_separator = True
    return "".join(key_parts).strip("-") or None
