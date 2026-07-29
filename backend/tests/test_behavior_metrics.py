from __future__ import annotations

from app.analysis.behavior_metrics import calculate_behavior_metrics
from app.analysis.schemas import (
    ANALYSIS_INPUT_SCHEMA_VERSION,
    BEHAVIOR_METRICS_SCHEMA_VERSION,
    AnalysisInput,
    BehaviorMetricsOutput,
)


def build_analysis_input(transactions: list[dict[str, object]]) -> AnalysisInput:
    return AnalysisInput(
        analysisId="analysis-1",
        groupId="group-1",
        members=[
            {"memberId": "member-1", "mbtiType": "INTJ"},
            {"memberId": "member-2", "mbtiType": "ENFP"},
        ],
        transactions=transactions,
        schemaVersion=ANALYSIS_INPUT_SCHEMA_VERSION,
    )


def test_normal_spending_metrics_are_calculated() -> None:
    analysis_input = build_analysis_input(
        [
            transaction("2026-07-01T12:30:00", 10_000, "FOOD", "meal-a", False, True),
            transaction("2026-07-02T09:00:00", 12_000, "TRANSPORT", "metro", True, True),
            transaction("2026-07-04T18:00:00", 8_000, "CAFE", "cafe-a", False, False),
            transaction("2026-07-05T14:00:00", 10_000, "CULTURE", "movie", False, False),
        ]
    )

    output = calculate_behavior_metrics(analysis_input)

    assert output.schema_version == BEHAVIOR_METRICS_SCHEMA_VERSION
    assert output.metrics.category_concentration == 0.3
    assert output.metrics.spending_volatility == 0.14
    assert output.metrics.repeat_purchase_ratio == 0.25
    assert output.metrics.weekend_spending_ratio == 0.45
    assert output.metrics.planned_spending_ratio == 0.55
    assert {evidence.metric for evidence in output.evidence} == {
        "categoryConcentration",
        "spendingVolatility",
        "repeatPurchaseRatio",
        "weekendSpendingRatio",
        "plannedSpendingRatio",
    }


def test_concentrated_spending_scenario_marks_category_dominance() -> None:
    analysis_input = build_analysis_input(
        [
            transaction("2026-07-01T12:00:00", 64_000, "FOOD", "restaurant", False, False),
            transaction("2026-07-02T12:00:00", 20_000, "SHOPPING", "store", False, True),
            transaction("2026-07-03T12:00:00", 16_000, "TRANSPORT", "metro", False, True),
        ]
    )

    output = calculate_behavior_metrics(analysis_input)

    assert output.metrics.category_concentration == 0.64
    assert evidence_for(output, "categoryConcentration").basis == (
        "FOOD 카테고리가 전체 지출의 64%를 차지합니다."
    )


def test_repeat_spending_uses_merchant_repetition_when_explicit_marker_is_missing() -> None:
    analysis_input = build_analysis_input(
        [
            transaction_without_markers("2026-07-01T08:00:00", 5_000, "CAFE", "daily-cafe"),
            transaction_without_markers("2026-07-02T08:00:00", 5_000, "CAFE", "daily-cafe"),
            transaction_without_markers("2026-07-03T18:00:00", 20_000, "FOOD", "restaurant"),
        ]
    )

    output = calculate_behavior_metrics(analysis_input)

    assert output.metrics.repeat_purchase_ratio == 0.67
    assert "2건이 반복 merchant 소비" in evidence_for(output, "repeatPurchaseRatio").basis


def test_volatile_spending_scenario_caps_volatility_at_one() -> None:
    analysis_input = build_analysis_input(
        [
            transaction("2026-07-01T12:00:00", 1_000, "CAFE", "cafe", False, False),
            transaction("2026-07-02T12:00:00", 1_000, "CAFE", "cafe", False, False),
            transaction("2026-07-03T12:00:00", 100_000, "TRAVEL", "hotel", False, True),
        ]
    )

    output = calculate_behavior_metrics(analysis_input)

    assert output.metrics.spending_volatility == 1.0
    assert "일별 지출 변동계수" in evidence_for(output, "spendingVolatility").basis


def test_sparse_or_missing_metric_inputs_are_not_forced() -> None:
    analysis_input = build_analysis_input(
        [
            transaction_without_markers("2026-07-01T12:00:00", 10_000, "FOOD", None),
        ]
    )

    output = calculate_behavior_metrics(analysis_input)

    assert output.metrics.category_concentration == 1.0
    assert output.metrics.weekend_spending_ratio == 0.0
    assert output.metrics.spending_volatility is None
    assert output.metrics.repeat_purchase_ratio is None
    assert output.metrics.planned_spending_ratio is None
    assert "서로 다른 지출일 2일 이상" in evidence_for(output, "spendingVolatility").basis
    assert "merchantKey가 있는 거래 2건 이상" in evidence_for(output, "repeatPurchaseRatio").basis
    assert "계획성 표시 거래 1건 이상" in evidence_for(output, "plannedSpendingRatio").basis


def test_same_input_produces_same_behavior_metrics() -> None:
    analysis_input = build_analysis_input(
        [
            transaction("2026-07-03T12:00:00", 30_000, "FOOD", "restaurant", True, False),
            transaction("2026-07-01T12:00:00", 10_000, "CAFE", "cafe", False, True),
            transaction("2026-07-02T12:00:00", 10_000, "CAFE", "cafe", True, True),
        ]
    )

    first = calculate_behavior_metrics(analysis_input)
    second = calculate_behavior_metrics(analysis_input)

    assert first.model_dump(by_alias=True) == second.model_dump(by_alias=True)


def transaction(
    occurred_at: str,
    amount: int,
    category: str,
    merchant_key: str,
    is_recurring: bool,
    is_planned: bool,
) -> dict[str, object]:
    return {
        "occurredAt": occurred_at,
        "amount": amount,
        "category": category,
        "merchantKey": merchant_key,
        "isRecurring": is_recurring,
        "isPlanned": is_planned,
    }


def transaction_without_markers(
    occurred_at: str,
    amount: int,
    category: str,
    merchant_key: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "occurredAt": occurred_at,
        "amount": amount,
        "category": category,
    }
    if merchant_key is not None:
        payload["merchantKey"] = merchant_key
    return payload


def evidence_for(output: BehaviorMetricsOutput, metric: str) -> object:
    return next(evidence for evidence in output.evidence if evidence.metric == metric)
