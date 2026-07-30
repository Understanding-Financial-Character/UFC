from __future__ import annotations

from datetime import UTC

from app.analysis.contracts import (
    AnalysisInput,
    CoverageReport,
    DataQualityReport,
    NormalizedTransaction,
    ProvisionalReason,
    ResultStatus,
)

MIN_ANALYZABLE_WITHDRAWALS = 10
MIN_ANALYSIS_PERIOD_DAYS = 14
MIN_CATEGORY_COVERAGE = 0.7
MIN_MERCHANT_COVERAGE = 0.5


def calculate_coverage(transactions: tuple[NormalizedTransaction, ...]) -> CoverageReport:
    if not transactions:
        return CoverageReport(category_coverage=0.0, merchant_coverage=0.0)
    count = len(transactions)
    category_count = sum(1 for transaction in transactions if transaction.category_code)
    merchant_count = sum(1 for transaction in transactions if transaction.merchant_key)
    return CoverageReport(
        category_coverage=category_count / count,
        merchant_coverage=merchant_count / count,
    )


def build_data_quality_report(
    analysis_input: AnalysisInput,
    normalized_transactions: tuple[NormalizedTransaction, ...],
    excluded_count: int,
) -> DataQualityReport:
    period_days = calculate_period_days(analysis_input)
    coverage = calculate_coverage(normalized_transactions)
    provisional_reasons: list[ProvisionalReason] = []
    limitations: list[str] = []

    if not normalized_transactions:
        provisional_reasons.append(ProvisionalReason.NO_ANALYZABLE_WITHDRAWALS)
        limitations.append("No non-excluded withdrawal transactions are available for analysis.")
    if len(normalized_transactions) < MIN_ANALYZABLE_WITHDRAWALS:
        provisional_reasons.append(ProvisionalReason.INSUFFICIENT_TRANSACTION_COUNT)
        limitations.append("Transaction count is below the minimum analysis threshold.")
    if period_days < MIN_ANALYSIS_PERIOD_DAYS:
        provisional_reasons.append(ProvisionalReason.INSUFFICIENT_ANALYSIS_PERIOD)
        limitations.append("Analysis period is shorter than the minimum observation window.")
    if coverage.category_coverage < MIN_CATEGORY_COVERAGE:
        provisional_reasons.append(ProvisionalReason.LOW_CATEGORY_COVERAGE)
        limitations.append("Category coverage is too low for complete category-based evidence.")
    if coverage.merchant_coverage < MIN_MERCHANT_COVERAGE:
        provisional_reasons.append(ProvisionalReason.LOW_MERCHANT_COVERAGE)
        limitations.append("Merchant coverage is too low for complete merchant-based evidence.")
    if analysis_input.is_synthetic:
        provisional_reasons.append(ProvisionalReason.SYNTHETIC_DATA)
        limitations.append("Synthetic or mock data should be treated as provisional evidence.")

    unique_reasons = tuple(dict.fromkeys(provisional_reasons))
    analysis_eligible = (
        normalized_transactions
        and len(normalized_transactions) >= MIN_ANALYZABLE_WITHDRAWALS
        and period_days >= MIN_ANALYSIS_PERIOD_DAYS
    )
    if not normalized_transactions:
        result_status = ResultStatus.INSUFFICIENT_DATA
    elif unique_reasons:
        result_status = ResultStatus.PROVISIONAL
    else:
        result_status = ResultStatus.STANDARD

    score = calculate_quality_score(
        included_count=len(normalized_transactions),
        period_days=period_days,
        category_coverage=coverage.category_coverage,
        merchant_coverage=coverage.merchant_coverage,
        is_synthetic=analysis_input.is_synthetic,
    )
    return DataQualityReport(
        included_count=len(normalized_transactions),
        excluded_count=excluded_count,
        analysis_period_days=period_days,
        category_coverage=round(coverage.category_coverage, 4),
        merchant_coverage=round(coverage.merchant_coverage, 4),
        data_quality_score=score,
        analysis_eligible=bool(analysis_eligible),
        result_status_candidate=result_status,
        provisional_reasons=unique_reasons,
        limitations=tuple(dict.fromkeys(limitations)),
    )


def calculate_period_days(analysis_input: AnalysisInput) -> int:
    started_at = analysis_input.analysis_period.started_at.astimezone(UTC)
    ended_at = analysis_input.analysis_period.ended_at.astimezone(UTC)
    delta = ended_at - started_at
    return max(delta.days + 1, 0)


def calculate_quality_score(
    included_count: int,
    period_days: int,
    category_coverage: float,
    merchant_coverage: float,
    is_synthetic: bool,
) -> float:
    count_score = min(included_count / MIN_ANALYZABLE_WITHDRAWALS, 1.0)
    period_score = min(period_days / MIN_ANALYSIS_PERIOD_DAYS, 1.0)
    synthetic_penalty = 0.9 if is_synthetic else 1.0
    score = (
        0.35 * count_score
        + 0.25 * period_score
        + 0.25 * category_coverage
        + 0.15 * merchant_coverage
    )
    return round(max(0.0, min(score * synthetic_penalty, 1.0)), 4)
