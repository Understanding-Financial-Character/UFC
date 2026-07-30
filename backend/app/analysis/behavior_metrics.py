from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from math import log, sqrt
from statistics import median
from zoneinfo import ZoneInfo

from app.analysis.contracts import (
    BEHAVIOR_FEATURE_POLICY_VERSION,
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    CATEGORY_MAPPING_VERSION,
    AnalysisSourceType,
    AnalysisTransactionType,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    BehaviorGroup,
    BehaviorMetricsInput,
    BehaviorMetricsResult,
    NormalizedTransaction,
)

MVP_ANALYSIS_TIMEZONE = "Asia/Seoul"
TRAVEL_EXPERIENCE_CATEGORY_CODES = frozenset(
    {"TRAVEL", "ACCOMMODATION", "CULTURE_LEISURE"}
)
GIFT_ANNIVERSARY_CATEGORY_CODES = frozenset({"GIFT_ANNIVERSARY"})
SAVING_EDUCATION_CATEGORY_CODES = frozenset({"SAVINGS", "EDUCATION"})
NIGHT_START_HOUR = 18
NIGHT_END_HOUR = 6
MIN_MERCHANT_ROWS = 2
MIN_DIVERSITY_CATEGORIES = 2
MIN_WEEKLY_VOLATILITY_WEEKS = 2
MIN_OUTLIER_TRANSACTIONS = 5


def calculate_behavior_metrics(
    metrics_input: BehaviorMetricsInput | tuple[NormalizedTransaction, ...],
) -> BehaviorMetricsResult:
    context = coerce_metrics_input(metrics_input)
    timezone = ZoneInfo(context.timezone)
    spending_transactions = tuple(
        sorted(
            (
                transaction
                for transaction in context.transactions
                if transaction.transaction_type == AnalysisTransactionType.WITHDRAWAL
            ),
            key=lambda transaction: (transaction.occurred_at, transaction.transaction_id),
        )
    )

    features = (
        amount_ratio(
            feature_code=BehaviorFeatureCode.SHARED_EXPENSE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_shared_expense"),
            predicate=lambda transaction: transaction.is_shared_expense is True,
            unavailable_reason="No transactions have is_shared_expense markers.",
            evidence_label="Shared expense spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO,
            transactions=spending_transactions,
            predicate=lambda transaction: is_weekend_social_spending(transaction, timezone),
            unavailable_reason="No spending transactions are available for weekend social ratio.",
            evidence_label="Weekend social spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.NIGHT_SPENDING_RATIO,
            transactions=spending_transactions,
            predicate=lambda transaction: is_night_spending(transaction, timezone),
            unavailable_reason="No spending transactions are available for night spending ratio.",
            evidence_label="Night spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO,
            transactions=spending_transactions,
            predicate=is_travel_experience_spending,
            unavailable_reason="No spending transactions are available for travel experience ratio.",
            evidence_label="Travel and experience spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=is_practical_spending,
            unavailable_reason="No transactions have behavior_group for practical spending ratio.",
            evidence_label="Practical spending",
        ),
        category_concentration(spending_transactions),
        category_diversity_score(spending_transactions),
        new_merchant_ratio(spending_transactions),
        repeat_merchant_ratio(spending_transactions),
        amount_ratio(
            feature_code=BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=lambda transaction: transaction.behavior_group == BehaviorGroup.EXPERIENCE,
            unavailable_reason="No transactions have behavior_group for experience spending ratio.",
            evidence_label="Experience spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.SAVING_EDUCATION_RATIO,
            transactions=saving_education_countable_transactions(spending_transactions),
            predicate=is_saving_education_spending,
            unavailable_reason=(
                "No transactions have category_code or behavior_group for saving education ratio."
            ),
            evidence_label="Saving and education spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=lambda transaction: transaction.behavior_group == BehaviorGroup.RELATIONSHIP,
            unavailable_reason="No transactions have behavior_group for relationship spending ratio.",
            evidence_label="Relationship spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_shared_expense"),
            predicate=is_shared_experience_spending,
            unavailable_reason="No transactions have is_shared_expense markers.",
            evidence_label="Shared experience spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO,
            transactions=category_code_transactions(spending_transactions),
            predicate=lambda transaction: normalized_code(transaction)
            in GIFT_ANNIVERSARY_CATEGORY_CODES,
            unavailable_reason="No transactions have category_code for gift anniversary ratio.",
            evidence_label="Gift and anniversary spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.PLANNED_EXPENSE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_planned"),
            predicate=lambda transaction: transaction.is_planned is True,
            unavailable_reason="No transactions have is_planned markers.",
            evidence_label="Planned spending",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.RECURRING_EXPENSE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_recurring"),
            predicate=lambda transaction: transaction.is_recurring is True,
            unavailable_reason="No transactions have is_recurring markers.",
            evidence_label="Recurring spending",
        ),
        weekly_expense_volatility(spending_transactions, context, timezone),
        outlier_ratio(spending_transactions),
    )
    return BehaviorMetricsResult(
        schema_version=BEHAVIOR_FEATURE_SCHEMA_VERSION,
        policy_version=BEHAVIOR_FEATURE_POLICY_VERSION,
        category_mapping_version=CATEGORY_MAPPING_VERSION,
        analysis_timezone=context.timezone,
        source_type=context.source_type,
        is_synthetic=context.is_synthetic,
        features=features,
    )


def coerce_metrics_input(
    metrics_input: BehaviorMetricsInput | tuple[NormalizedTransaction, ...],
) -> BehaviorMetricsInput:
    if isinstance(metrics_input, BehaviorMetricsInput):
        return metrics_input
    transactions = metrics_input
    if transactions:
        started_at = min(transaction.occurred_at for transaction in transactions)
        ended_at = max(transaction.occurred_at for transaction in transactions)
    else:
        started_at = datetime(1970, 1, 1, tzinfo=UTC)
        ended_at = started_at
    source_type = infer_source_type(transactions)
    return BehaviorMetricsInput(
        transactions=transactions,
        observation_started_at=started_at,
        observation_ended_at=ended_at,
        timezone=MVP_ANALYSIS_TIMEZONE,
        source_type=source_type,
        is_synthetic=is_synthetic_source(source_type),
    )


def infer_source_type(transactions: tuple[NormalizedTransaction, ...]) -> AnalysisSourceType:
    if not transactions:
        return AnalysisSourceType.CSV
    source_types = {transaction.source_type for transaction in transactions}
    if len(source_types) == 1:
        return next(iter(source_types))
    if AnalysisSourceType.MOCK in source_types:
        return AnalysisSourceType.MOCK
    if AnalysisSourceType.INTERNAL_TEST in source_types:
        return AnalysisSourceType.INTERNAL_TEST
    return AnalysisSourceType.CSV


def is_synthetic_source(source_type: AnalysisSourceType) -> bool:
    return source_type in {AnalysisSourceType.MOCK, AnalysisSourceType.INTERNAL_TEST}


def amount_ratio(
    *,
    feature_code: BehaviorFeatureCode,
    transactions: tuple[NormalizedTransaction, ...],
    predicate: Callable[[NormalizedTransaction], bool],
    unavailable_reason: str,
    evidence_label: str,
) -> BehaviorFeatureResult:
    if not transactions:
        return unavailable(
            feature_code=feature_code,
            unit=BehaviorFeatureUnit.AMOUNT_RATIO,
            reason=unavailable_reason,
        )
    denominator = sum_amount(transactions)
    if denominator <= 0:
        return unavailable(
            feature_code=feature_code,
            unit=BehaviorFeatureUnit.AMOUNT_RATIO,
            reason="Denominator amount is zero.",
            sample_count=len(transactions),
        )
    numerator_transactions = tuple(transaction for transaction in transactions if predicate(transaction))
    numerator = sum_amount(numerator_transactions)
    value = ratio(numerator, denominator)
    return available(
        feature_code=feature_code,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.AMOUNT_RATIO,
        sample_count=len(transactions),
        evidence=(
            (
                f"{evidence_label}: {format_amount(numerator)} of "
                f"{format_amount(denominator)} amount, {percent(value)}."
            ),
        ),
    )


def category_concentration(
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorFeatureResult:
    category_transactions = category_code_transactions(transactions)
    if not category_transactions:
        return unavailable(
            feature_code=BehaviorFeatureCode.CATEGORY_CONCENTRATION,
            unit=BehaviorFeatureUnit.AMOUNT_RATIO,
            reason="No transactions have category_code for category concentration.",
        )
    category_amounts = amount_by_category(category_transactions)
    top_category, top_amount = max(sorted(category_amounts.items()), key=lambda item: item[1])
    denominator = sum(category_amounts.values(), Decimal(0))
    value = ratio(top_amount, denominator)
    return available(
        feature_code=BehaviorFeatureCode.CATEGORY_CONCENTRATION,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.AMOUNT_RATIO,
        sample_count=len(category_transactions),
        evidence=(
            (
                f"Top category {top_category}: {format_amount(top_amount)} of "
                f"{format_amount(denominator)} category-coded amount, {percent(value)}."
            ),
        ),
    )


def category_diversity_score(
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorFeatureResult:
    category_transactions = category_code_transactions(transactions)
    category_amounts = amount_by_category(category_transactions)
    if len(category_amounts) < MIN_DIVERSITY_CATEGORIES:
        return unavailable(
            feature_code=BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE,
            unit=BehaviorFeatureUnit.SCORE,
            reason=f"At least {MIN_DIVERSITY_CATEGORIES} distinct category codes are required.",
            sample_count=len(category_transactions),
        )
    total = sum(category_amounts.values(), Decimal(0))
    entropy = Decimal(0)
    for amount in category_amounts.values():
        proportion = amount / total
        entropy += Decimal(str(float(proportion) * log(float(proportion))))
    value = round_score(float(-entropy / Decimal(str(log(len(category_amounts))))))
    return available(
        feature_code=BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.SCORE,
        sample_count=len(category_transactions),
        evidence=(
            (
                f"Category diversity score {format_score(value)} from "
                f"{len(category_amounts)} category amount buckets."
            ),
        ),
    )


def new_merchant_ratio(
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorFeatureResult:
    merchant_transactions = tuple(
        transaction for transaction in transactions if transaction.merchant_key
    )
    return unavailable(
        feature_code=BehaviorFeatureCode.NEW_MERCHANT_RATIO,
        unit=BehaviorFeatureUnit.COUNT_RATIO,
        reason=(
            "Historical merchant baseline is unavailable, so true new merchant status "
            "cannot be determined in AN Phase 2."
        ),
        sample_count=len(merchant_transactions),
    )


def repeat_merchant_ratio(
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorFeatureResult:
    merchant_transactions = tuple(
        transaction for transaction in transactions if transaction.merchant_key
    )
    if len(merchant_transactions) < MIN_MERCHANT_ROWS:
        return unavailable(
            feature_code=BehaviorFeatureCode.REPEAT_MERCHANT_RATIO,
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            reason=f"At least {MIN_MERCHANT_ROWS} transactions with merchant_key are required.",
            sample_count=len(merchant_transactions),
        )
    seen: set[str] = set()
    repeat_count = 0
    for transaction in merchant_transactions:
        merchant_key = transaction.merchant_key
        if merchant_key in seen:
            repeat_count += 1
        else:
            seen.add(merchant_key)
    value = ratio(Decimal(repeat_count), Decimal(len(merchant_transactions)))
    return available(
        feature_code=BehaviorFeatureCode.REPEAT_MERCHANT_RATIO,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.COUNT_RATIO,
        sample_count=len(merchant_transactions),
        evidence=(
            (
                f"Repeat merchant visits after first occurrence: {repeat_count} of "
                f"{len(merchant_transactions)} merchant-key transactions, {percent(value)}."
            ),
        ),
    )


def weekly_expense_volatility(
    transactions: tuple[NormalizedTransaction, ...],
    context: BehaviorMetricsInput,
    timezone: ZoneInfo,
) -> BehaviorFeatureResult:
    week_starts = tuple(iter_week_starts(context, timezone))
    if len(week_starts) < MIN_WEEKLY_VOLATILITY_WEEKS:
        return unavailable(
            feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
            unit=BehaviorFeatureUnit.SCORE,
            reason=f"At least {MIN_WEEKLY_VOLATILITY_WEEKS} observed calendar weeks are required.",
            sample_count=len(week_starts),
        )
    weekly_amounts: dict[date, Decimal] = {week_start: Decimal(0) for week_start in week_starts}
    for transaction in transactions:
        local_time = local_occurred_at(transaction, timezone)
        week_start = local_time.date() - timedelta(days=local_time.weekday())
        if week_start in weekly_amounts:
            weekly_amounts[week_start] += transaction.amount
    values = [float(weekly_amounts[week_start]) for week_start in week_starts]
    mean = sum(values) / len(values)
    if mean <= 0:
        return unavailable(
            feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
            unit=BehaviorFeatureUnit.SCORE,
            reason="Average weekly spending is zero.",
            sample_count=len(week_starts),
        )
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    raw_cv = sqrt(variance) / mean
    normalized = min(raw_cv, 1.0)
    return available(
        feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
        raw_value=round_score(raw_cv),
        normalized_score=round_score(normalized),
        unit=BehaviorFeatureUnit.SCORE,
        sample_count=len(week_starts),
        evidence=(
            (
                f"Weekly spending CV from {len(week_starts)} calendar weeks is "
                f"{format_score(raw_cv)}; normalized cap is {format_score(normalized)}."
            ),
        ),
    )


def outlier_ratio(transactions: tuple[NormalizedTransaction, ...]) -> BehaviorFeatureResult:
    if len(transactions) < MIN_OUTLIER_TRANSACTIONS:
        return unavailable(
            feature_code=BehaviorFeatureCode.OUTLIER_RATIO,
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            reason=f"At least {MIN_OUTLIER_TRANSACTIONS} transactions are required.",
            sample_count=len(transactions),
        )
    amounts = [float(transaction.amount) for transaction in transactions]
    median_amount = median(amounts)
    deviations = [abs(amount - median_amount) for amount in amounts]
    median_deviation = median(deviations)
    if median_amount <= 0:
        threshold = max(amounts)
    elif median_deviation == 0:
        threshold = median_amount * 3
    else:
        threshold = median_amount + 3 * median_deviation
    outlier_count = sum(1 for amount in amounts if amount > threshold)
    value = ratio(Decimal(outlier_count), Decimal(len(transactions)))
    return available(
        feature_code=BehaviorFeatureCode.OUTLIER_RATIO,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.COUNT_RATIO,
        sample_count=len(transactions),
        evidence=(
            (
                f"Outlier transactions above {format_score(threshold)} amount: "
                f"{outlier_count} of {len(transactions)}, {percent(value)}."
            ),
        ),
    )


def iter_week_starts(context: BehaviorMetricsInput, timezone: ZoneInfo) -> tuple[date, ...]:
    started_at = context.observation_started_at.astimezone(timezone)
    ended_at = context.observation_ended_at.astimezone(timezone)
    current = started_at.date() - timedelta(days=started_at.weekday())
    last = ended_at.date() - timedelta(days=ended_at.weekday())
    week_starts: list[date] = []
    while current <= last:
        week_starts.append(current)
        current += timedelta(days=7)
    return tuple(week_starts)


def marked_transactions(
    transactions: tuple[NormalizedTransaction, ...],
    marker: str,
) -> tuple[NormalizedTransaction, ...]:
    return tuple(transaction for transaction in transactions if getattr(transaction, marker) is not None)


def behavior_group_transactions(
    transactions: tuple[NormalizedTransaction, ...],
) -> tuple[NormalizedTransaction, ...]:
    return tuple(transaction for transaction in transactions if transaction.behavior_group is not None)


def category_code_transactions(
    transactions: tuple[NormalizedTransaction, ...],
) -> tuple[NormalizedTransaction, ...]:
    return tuple(transaction for transaction in transactions if transaction.category_code)


def saving_education_countable_transactions(
    transactions: tuple[NormalizedTransaction, ...],
) -> tuple[NormalizedTransaction, ...]:
    return tuple(
        transaction
        for transaction in transactions
        if transaction.behavior_group is not None or transaction.category_code
    )


def is_weekend_social_spending(transaction: NormalizedTransaction, timezone: ZoneInfo) -> bool:
    local_time = local_occurred_at(transaction, timezone)
    return local_time.weekday() >= 5 and (
        transaction.behavior_group == BehaviorGroup.RELATIONSHIP
        or normalized_code(transaction) == "GATHERING"
        or transaction.is_shared_expense is True
    )


def is_night_spending(transaction: NormalizedTransaction, timezone: ZoneInfo) -> bool:
    local_time = local_occurred_at(transaction, timezone)
    return local_time.hour >= NIGHT_START_HOUR or local_time.hour < NIGHT_END_HOUR


def local_occurred_at(transaction: NormalizedTransaction, timezone: ZoneInfo) -> datetime:
    return transaction.occurred_at.astimezone(timezone)


def is_travel_experience_spending(transaction: NormalizedTransaction) -> bool:
    return (
        transaction.behavior_group == BehaviorGroup.EXPERIENCE
        or normalized_code(transaction) in TRAVEL_EXPERIENCE_CATEGORY_CODES
    )


def is_practical_spending(transaction: NormalizedTransaction) -> bool:
    return transaction.behavior_group in {BehaviorGroup.PRACTICAL, BehaviorGroup.REGULAR}


def is_saving_education_spending(transaction: NormalizedTransaction) -> bool:
    return (
        transaction.behavior_group == BehaviorGroup.SAVINGS
        or normalized_code(transaction) in SAVING_EDUCATION_CATEGORY_CODES
    )


def is_shared_experience_spending(transaction: NormalizedTransaction) -> bool:
    return transaction.is_shared_expense is True and transaction.behavior_group == BehaviorGroup.EXPERIENCE


def amount_by_category(
    transactions: tuple[NormalizedTransaction, ...],
) -> dict[str, Decimal]:
    category_amounts: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    for transaction in transactions:
        category_amounts[normalized_code(transaction)] += transaction.amount
    return dict(category_amounts)


def normalized_code(transaction: NormalizedTransaction) -> str:
    return (transaction.category_code or "").strip().upper()


def sum_amount(transactions: tuple[NormalizedTransaction, ...]) -> Decimal:
    return sum((transaction.amount for transaction in transactions), Decimal(0))


def ratio(numerator: Decimal, denominator: Decimal) -> float:
    if denominator <= 0:
        return 0.0
    return round_score(float(numerator / denominator))


def round_score(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def percent(value: float) -> str:
    rounded = Decimal(str(value * 100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{rounded}%"


def format_amount(value: Decimal) -> str:
    return str(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def format_score(value: float) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def available(
    *,
    feature_code: BehaviorFeatureCode,
    raw_value: float,
    normalized_score: float,
    unit: BehaviorFeatureUnit,
    sample_count: int,
    evidence: tuple[str, ...],
) -> BehaviorFeatureResult:
    return BehaviorFeatureResult(
        feature_code=feature_code,
        status=BehaviorFeatureStatus.AVAILABLE,
        raw_value=raw_value,
        normalized_score=normalized_score,
        unit=unit,
        sample_count=sample_count,
        evidence=evidence,
    )


def unavailable(
    *,
    feature_code: BehaviorFeatureCode,
    unit: BehaviorFeatureUnit,
    reason: str,
    sample_count: int = 0,
) -> BehaviorFeatureResult:
    return BehaviorFeatureResult(
        feature_code=feature_code,
        status=BehaviorFeatureStatus.UNAVAILABLE,
        raw_value=None,
        normalized_score=None,
        unit=unit,
        sample_count=sample_count,
        evidence=(reason,),
    )
