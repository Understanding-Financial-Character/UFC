from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from math import log, sqrt
from statistics import median

from app.analysis.contracts import (
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    AnalysisTransactionType,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    BehaviorGroup,
    BehaviorMetricsResult,
    NormalizedTransaction,
)

SOCIAL_CATEGORY_CODES = frozenset({"FOOD", "CAFE", "GATHERING", "CULTURE_LEISURE"})
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
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorMetricsResult:
    spending_transactions = tuple(
        sorted(
            (
                transaction
                for transaction in transactions
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
            unavailable_reason="공동지출 표시가 있는 거래가 없어 계산할 수 없습니다.",
            evidence_label="공동지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO,
            transactions=spending_transactions,
            predicate=is_weekend_social_spending,
            unavailable_reason="거래가 없어 주말 사회적 지출 비율을 계산할 수 없습니다.",
            evidence_label="주말 사회적 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.NIGHT_SPENDING_RATIO,
            transactions=spending_transactions,
            predicate=is_night_spending,
            unavailable_reason="거래가 없어 야간 지출 비율을 계산할 수 없습니다.",
            evidence_label="야간 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO,
            transactions=spending_transactions,
            predicate=is_travel_experience_spending,
            unavailable_reason="거래가 없어 여행·경험 지출 비율을 계산할 수 없습니다.",
            evidence_label="여행·경험 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=is_practical_spending,
            unavailable_reason="behavior_group이 있는 거래가 없어 실속 지출 비율을 계산할 수 없습니다.",
            evidence_label="실속 지출",
        ),
        category_concentration(spending_transactions),
        category_diversity_score(spending_transactions),
        merchant_ratio(
            feature_code=BehaviorFeatureCode.NEW_MERCHANT_RATIO,
            transactions=spending_transactions,
            mode="new",
        ),
        merchant_ratio(
            feature_code=BehaviorFeatureCode.REPEAT_MERCHANT_RATIO,
            transactions=spending_transactions,
            mode="repeat",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=lambda transaction: transaction.behavior_group == BehaviorGroup.EXPERIENCE,
            unavailable_reason="behavior_group이 있는 거래가 없어 경험 지출 비율을 계산할 수 없습니다.",
            evidence_label="경험 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.SAVING_EDUCATION_RATIO,
            transactions=saving_education_countable_transactions(spending_transactions),
            predicate=is_saving_education_spending,
            unavailable_reason="저축·교육 판단에 필요한 category_code 또는 behavior_group이 없습니다.",
            evidence_label="저축·교육 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO,
            transactions=behavior_group_transactions(spending_transactions),
            predicate=lambda transaction: transaction.behavior_group == BehaviorGroup.RELATIONSHIP,
            unavailable_reason="behavior_group이 있는 거래가 없어 관계형 지출 비율을 계산할 수 없습니다.",
            evidence_label="관계형 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_shared_expense"),
            predicate=is_shared_experience_spending,
            unavailable_reason="공동지출 표시가 있는 거래가 없어 공동 경험 비율을 계산할 수 없습니다.",
            evidence_label="공동 경험 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO,
            transactions=category_code_transactions(spending_transactions),
            predicate=lambda transaction: normalized_code(transaction)
            in GIFT_ANNIVERSARY_CATEGORY_CODES,
            unavailable_reason="category_code가 있는 거래가 없어 선물·기념일 비율을 계산할 수 없습니다.",
            evidence_label="선물·기념일 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.PLANNED_EXPENSE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_planned"),
            predicate=lambda transaction: transaction.is_planned is True,
            unavailable_reason="계획 지출 표시가 있는 거래가 없어 계산할 수 없습니다.",
            evidence_label="계획 지출",
        ),
        amount_ratio(
            feature_code=BehaviorFeatureCode.RECURRING_EXPENSE_RATIO,
            transactions=marked_transactions(spending_transactions, "is_recurring"),
            predicate=lambda transaction: transaction.is_recurring is True,
            unavailable_reason="정기 지출 표시가 있는 거래가 없어 계산할 수 없습니다.",
            evidence_label="정기 지출",
        ),
        weekly_expense_volatility(spending_transactions),
        outlier_ratio(spending_transactions),
    )
    return BehaviorMetricsResult(
        schema_version=BEHAVIOR_FEATURE_SCHEMA_VERSION,
        features=features,
    )


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
            reason="분모 금액이 0이라 계산할 수 없습니다.",
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
                f"{evidence_label} {format_amount(numerator)}원이 "
                f"표본 금액 {format_amount(denominator)}원의 {percent(value)}입니다."
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
            reason="category_code가 있는 거래가 없어 카테고리 집중도를 계산할 수 없습니다.",
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
                f"{top_category} 카테고리가 category_code 표본 금액 "
                f"{format_amount(denominator)}원의 {percent(value)}입니다."
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
            reason=f"서로 다른 category_code {MIN_DIVERSITY_CATEGORIES}개 이상이 필요합니다.",
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
                f"{len(category_amounts)}개 카테고리의 금액 분포로 다양성 점수 "
                f"{format_score(value)}를 계산했습니다."
            ),
        ),
    )


def merchant_ratio(
    *,
    feature_code: BehaviorFeatureCode,
    transactions: tuple[NormalizedTransaction, ...],
    mode: str,
) -> BehaviorFeatureResult:
    merchant_transactions = tuple(
        transaction for transaction in transactions if transaction.merchant_key
    )
    if len(merchant_transactions) < MIN_MERCHANT_ROWS:
        return unavailable(
            feature_code=feature_code,
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            reason=f"merchant_key가 있는 거래 {MIN_MERCHANT_ROWS}건 이상이 필요합니다.",
            sample_count=len(merchant_transactions),
        )
    merchant_counts = Counter(transaction.merchant_key for transaction in merchant_transactions)
    if mode == "new":
        seen: set[str] = set()
        numerator_count = 0
        for transaction in merchant_transactions:
            merchant_key = transaction.merchant_key
            if merchant_key not in seen:
                numerator_count += 1
                seen.add(merchant_key)
        evidence_label = "신규 가맹점"
    else:
        numerator_count = sum(
            1
            for transaction in merchant_transactions
            if merchant_counts[transaction.merchant_key] > 1
        )
        evidence_label = "반복 가맹점"
    value = ratio(Decimal(numerator_count), Decimal(len(merchant_transactions)))
    return available(
        feature_code=feature_code,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.COUNT_RATIO,
        sample_count=len(merchant_transactions),
        evidence=(
            (
                f"{evidence_label} 거래 {numerator_count}건이 merchant_key 표본 "
                f"{len(merchant_transactions)}건의 {percent(value)}입니다."
            ),
        ),
    )


def weekly_expense_volatility(
    transactions: tuple[NormalizedTransaction, ...],
) -> BehaviorFeatureResult:
    weekly_amounts: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal(0))
    for transaction in transactions:
        iso_year, iso_week, _ = transaction.occurred_at.isocalendar()
        weekly_amounts[(iso_year, iso_week)] += transaction.amount
    if len(weekly_amounts) < MIN_WEEKLY_VOLATILITY_WEEKS:
        return unavailable(
            feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
            unit=BehaviorFeatureUnit.SCORE,
            reason=f"서로 다른 지출 주 {MIN_WEEKLY_VOLATILITY_WEEKS}주 이상이 필요합니다.",
            sample_count=len(weekly_amounts),
        )
    values = [float(amount) for amount in weekly_amounts.values()]
    mean = sum(values) / len(values)
    if mean <= 0:
        return unavailable(
            feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
            unit=BehaviorFeatureUnit.SCORE,
            reason="주별 평균 지출이 0이라 변동성을 계산할 수 없습니다.",
            sample_count=len(weekly_amounts),
        )
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    value = round_score(min(sqrt(variance) / mean, 1.0))
    return available(
        feature_code=BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.SCORE,
        sample_count=len(weekly_amounts),
        evidence=(
            (
                f"{len(weekly_amounts)}주 주별 지출의 변동계수를 1.0 상한으로 "
                f"{format_score(value)}로 계산했습니다."
            ),
        ),
    )


def outlier_ratio(transactions: tuple[NormalizedTransaction, ...]) -> BehaviorFeatureResult:
    if len(transactions) < MIN_OUTLIER_TRANSACTIONS:
        return unavailable(
            feature_code=BehaviorFeatureCode.OUTLIER_RATIO,
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            reason=f"이상치 판단에는 거래 {MIN_OUTLIER_TRANSACTIONS}건 이상이 필요합니다.",
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
                f"거래 {len(transactions)}건 중 {outlier_count}건이 "
                f"기준 금액 {format_score(threshold)}원을 초과했습니다."
            ),
        ),
    )


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


def is_weekend_social_spending(transaction: NormalizedTransaction) -> bool:
    return transaction.occurred_at.weekday() >= 5 and (
        transaction.behavior_group == BehaviorGroup.RELATIONSHIP
        or normalized_code(transaction) in SOCIAL_CATEGORY_CODES
    )


def is_night_spending(transaction: NormalizedTransaction) -> bool:
    return transaction.occurred_at.hour >= NIGHT_START_HOUR or transaction.occurred_at.hour < NIGHT_END_HOUR


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
