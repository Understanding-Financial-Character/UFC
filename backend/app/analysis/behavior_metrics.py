from __future__ import annotations

from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from math import sqrt

from app.analysis.schemas import (
    BEHAVIOR_METRICS_SCHEMA_VERSION,
    AnalysisInput,
    AnalysisTransactionInput,
    BehaviorMetricEvidence,
    BehaviorMetricsOutput,
    BehaviorMetricValues,
)

MIN_TRANSACTIONS_CATEGORY_CONCENTRATION = 1
MIN_TRANSACTIONS_WEEKEND_RATIO = 1
MIN_TRANSACTIONS_REPEAT_RATIO = 2
MIN_TRANSACTIONS_PLANNED_RATIO = 1
MIN_DISTINCT_DAYS_VOLATILITY = 2


def calculate_behavior_metrics(analysis_input: AnalysisInput) -> BehaviorMetricsOutput:
    transactions = sorted(
        analysis_input.transactions,
        key=lambda transaction: (
            transaction.occurred_at,
            transaction.category.value,
            transaction.amount,
            transaction.merchant_key or "",
        ),
    )

    category_concentration, category_evidence = calculate_category_concentration(transactions)
    spending_volatility, volatility_evidence = calculate_spending_volatility(transactions)
    repeat_purchase_ratio, repeat_evidence = calculate_repeat_purchase_ratio(transactions)
    weekend_spending_ratio, weekend_evidence = calculate_weekend_spending_ratio(transactions)
    planned_spending_ratio, planned_evidence = calculate_planned_spending_ratio(transactions)

    return BehaviorMetricsOutput(
        schemaVersion=BEHAVIOR_METRICS_SCHEMA_VERSION,
        metrics=BehaviorMetricValues(
            categoryConcentration=category_concentration,
            spendingVolatility=spending_volatility,
            repeatPurchaseRatio=repeat_purchase_ratio,
            weekendSpendingRatio=weekend_spending_ratio,
            plannedSpendingRatio=planned_spending_ratio,
        ),
        evidence=[
            category_evidence,
            volatility_evidence,
            repeat_evidence,
            weekend_evidence,
            planned_evidence,
        ],
    )


def calculate_category_concentration(
    transactions: list[AnalysisTransactionInput],
) -> tuple[float | None, BehaviorMetricEvidence]:
    if len(transactions) < MIN_TRANSACTIONS_CATEGORY_CONCENTRATION:
        return skipped(
            "categoryConcentration",
            f"최소 거래 {MIN_TRANSACTIONS_CATEGORY_CONCENTRATION}건이 필요합니다.",
        )

    total_amount = sum(transaction.amount for transaction in transactions)
    category_amounts: dict[str, int] = defaultdict(int)
    for transaction in transactions:
        category_amounts[transaction.category.value] += transaction.amount
    top_category, top_amount = max(
        sorted(category_amounts.items()),
        key=lambda item: item[1],
    )
    value = rounded_ratio(top_amount, total_amount)
    return value, BehaviorMetricEvidence(
        metric="categoryConcentration",
        value=value,
        basis=f"{top_category} 카테고리가 전체 지출의 {percent(value)}를 차지합니다.",
    )


def calculate_spending_volatility(
    transactions: list[AnalysisTransactionInput],
) -> tuple[float | None, BehaviorMetricEvidence]:
    daily_amounts: dict[str, int] = defaultdict(int)
    for transaction in transactions:
        daily_amounts[transaction.occurred_at.date().isoformat()] += transaction.amount
    if len(daily_amounts) < MIN_DISTINCT_DAYS_VOLATILITY:
        return skipped(
            "spendingVolatility",
            f"서로 다른 지출일 {MIN_DISTINCT_DAYS_VOLATILITY}일 이상이 필요합니다.",
        )

    values = list(daily_amounts.values())
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    coefficient = min(sqrt(variance) / mean, 1.0)
    value = round_metric(coefficient)
    return value, BehaviorMetricEvidence(
        metric="spendingVolatility",
        value=value,
        basis=f"{len(values)}일의 일별 지출 변동계수를 1.0 상한으로 정규화했습니다.",
    )


def calculate_repeat_purchase_ratio(
    transactions: list[AnalysisTransactionInput],
) -> tuple[float | None, BehaviorMetricEvidence]:
    explicit_transactions = [
        transaction for transaction in transactions if transaction.is_recurring is not None
    ]
    if explicit_transactions:
        if len(explicit_transactions) < MIN_TRANSACTIONS_REPEAT_RATIO:
            return skipped(
                "repeatPurchaseRatio",
                f"반복성 표시 거래 {MIN_TRANSACTIONS_REPEAT_RATIO}건 이상이 필요합니다.",
            )
        repeat_count = sum(1 for transaction in explicit_transactions if transaction.is_recurring)
        value = rounded_ratio(repeat_count, len(explicit_transactions))
        return value, BehaviorMetricEvidence(
            metric="repeatPurchaseRatio",
            value=value,
            basis=f"반복성 표시 거래 {len(explicit_transactions)}건 중 {repeat_count}건이 반복 소비입니다.",
        )

    merchant_transactions = [
        transaction for transaction in transactions if transaction.merchant_key is not None
    ]
    if len(merchant_transactions) < MIN_TRANSACTIONS_REPEAT_RATIO:
        return skipped(
            "repeatPurchaseRatio",
            f"merchantKey가 있는 거래 {MIN_TRANSACTIONS_REPEAT_RATIO}건 이상이 필요합니다.",
        )

    merchant_counts = Counter(transaction.merchant_key for transaction in merchant_transactions)
    repeat_count = sum(
        1
        for transaction in merchant_transactions
        if merchant_counts[transaction.merchant_key] > 1
    )
    value = rounded_ratio(repeat_count, len(merchant_transactions))
    return value, BehaviorMetricEvidence(
        metric="repeatPurchaseRatio",
        value=value,
        basis=(
            f"merchantKey가 있는 거래 {len(merchant_transactions)}건 중 "
            f"{repeat_count}건이 반복 merchant 소비입니다."
        ),
    )


def calculate_weekend_spending_ratio(
    transactions: list[AnalysisTransactionInput],
) -> tuple[float | None, BehaviorMetricEvidence]:
    if len(transactions) < MIN_TRANSACTIONS_WEEKEND_RATIO:
        return skipped(
            "weekendSpendingRatio",
            f"최소 거래 {MIN_TRANSACTIONS_WEEKEND_RATIO}건이 필요합니다.",
        )

    total_amount = sum(transaction.amount for transaction in transactions)
    weekend_amount = sum(
        transaction.amount for transaction in transactions if transaction.occurred_at.weekday() >= 5
    )
    value = rounded_ratio(weekend_amount, total_amount)
    return value, BehaviorMetricEvidence(
        metric="weekendSpendingRatio",
        value=value,
        basis=f"주말 지출이 전체 지출의 {percent(value)}를 차지합니다.",
    )


def calculate_planned_spending_ratio(
    transactions: list[AnalysisTransactionInput],
) -> tuple[float | None, BehaviorMetricEvidence]:
    planned_transactions = [
        transaction for transaction in transactions if transaction.is_planned is not None
    ]
    if len(planned_transactions) < MIN_TRANSACTIONS_PLANNED_RATIO:
        return skipped(
            "plannedSpendingRatio",
            f"계획성 표시 거래 {MIN_TRANSACTIONS_PLANNED_RATIO}건 이상이 필요합니다.",
        )

    total_amount = sum(transaction.amount for transaction in planned_transactions)
    planned_amount = sum(
        transaction.amount for transaction in planned_transactions if transaction.is_planned
    )
    value = rounded_ratio(planned_amount, total_amount)
    return value, BehaviorMetricEvidence(
        metric="plannedSpendingRatio",
        value=value,
        basis=(
            f"계획성 표시 거래 {len(planned_transactions)}건에서 계획 지출이 "
            f"표시 대상 지출의 {percent(value)}를 차지합니다."
        ),
    )


def rounded_ratio(numerator: int, denominator: int) -> float:
    return round_metric(numerator / denominator)


def round_metric(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def percent(value: float) -> str:
    return f"{int(Decimal(str(value * 100)).quantize(Decimal(1), rounding=ROUND_HALF_UP))}%"


def skipped(metric: str, basis: str) -> tuple[None, BehaviorMetricEvidence]:
    return None, BehaviorMetricEvidence(metric=metric, value=None, basis=basis)
