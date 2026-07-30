from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.analysis.behavior_metrics import calculate_behavior_metrics
from app.analysis.contracts import (
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    AnalysisSourceType,
    AnalysisTransactionType,
    BehaviorFeatureCode,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    BehaviorGroup,
    BehaviorMetricsInput,
    NormalizedTransaction,
)


def tx(
    index: int,
    *,
    amount: str = "1000",
    occurred_at: datetime | None = None,
    category_code: str | None = "FOOD",
    behavior_group: BehaviorGroup | None = BehaviorGroup.PRACTICAL,
    merchant_key: str | None = "merchant-a",
    transaction_type: AnalysisTransactionType = AnalysisTransactionType.WITHDRAWAL,
    is_shared_expense: bool | None = None,
    is_planned: bool | None = None,
    is_recurring: bool | None = None,
) -> NormalizedTransaction:
    return NormalizedTransaction(
        transaction_id=f"txn-{index:03d}",
        group_id="group-1",
        member_id="member-1",
        occurred_at=occurred_at or datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        amount=Decimal(amount),
        category_code=category_code,
        behavior_group=behavior_group,
        merchant_key=merchant_key,
        transaction_type=transaction_type,
        is_shared_expense=is_shared_expense,
        is_planned=is_planned,
        is_recurring=is_recurring,
        source_type=AnalysisSourceType.CSV,
    )


def features_by_code(
    transactions: tuple[NormalizedTransaction, ...],
    *,
    observation_started_at: datetime | None = None,
    observation_ended_at: datetime | None = None,
) -> dict[BehaviorFeatureCode, object]:
    metrics_input: BehaviorMetricsInput | tuple[NormalizedTransaction, ...] = transactions
    if observation_started_at is not None and observation_ended_at is not None:
        metrics_input = BehaviorMetricsInput(
            transactions=transactions,
            observation_started_at=observation_started_at,
            observation_ended_at=observation_ended_at,
        )
    result = calculate_behavior_metrics(metrics_input)
    return {feature.feature_code: feature for feature in result.features}


def test_feature_engine_calculates_all_core_features() -> None:
    transactions = (
        tx(
            1,
            amount="100",
            occurred_at=datetime(2026, 7, 4, 19, 0, tzinfo=UTC),
            category_code="GATHERING",
            behavior_group=BehaviorGroup.RELATIONSHIP,
            merchant_key="bar",
            is_shared_expense=True,
            is_planned=False,
            is_recurring=False,
        ),
        tx(
            2,
            amount="200",
            occurred_at=datetime(2026, 7, 5, 17, 59, tzinfo=UTC),
            category_code="TRAVEL",
            behavior_group=BehaviorGroup.EXPERIENCE,
            merchant_key="hotel",
            is_shared_expense=True,
            is_planned=True,
            is_recurring=True,
        ),
        tx(
            3,
            amount="300",
            occurred_at=datetime(2026, 7, 6, 6, 0, tzinfo=UTC),
            category_code="MART",
            behavior_group=BehaviorGroup.PRACTICAL,
            merchant_key="mart",
            is_shared_expense=False,
            is_planned=True,
            is_recurring=False,
        ),
        tx(
            4,
            amount="400",
            occurred_at=datetime(2026, 7, 13, 5, 59, tzinfo=UTC),
            category_code="SAVINGS",
            behavior_group=BehaviorGroup.SAVINGS,
            merchant_key="bank",
            is_shared_expense=None,
            is_planned=None,
            is_recurring=None,
        ),
        tx(
            5,
            amount="500",
            occurred_at=datetime(2026, 7, 19, 10, 0, tzinfo=UTC),
            category_code="GIFT_ANNIVERSARY",
            behavior_group=BehaviorGroup.RELATIONSHIP,
            merchant_key="gift-shop",
            is_shared_expense=False,
            is_planned=False,
            is_recurring=False,
        ),
    )

    result = calculate_behavior_metrics(transactions)
    features = {feature.feature_code: feature for feature in result.features}

    assert result.schema_version == BEHAVIOR_FEATURE_SCHEMA_VERSION
    assert result.policy_version == "behavior-policy-v1"
    assert result.category_mapping_version == "category-map-v2"
    assert result.analysis_timezone == "Asia/Seoul"
    assert features[BehaviorFeatureCode.SHARED_EXPENSE_RATIO].raw_value == 0.2727
    assert features[BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO].raw_value == 0.4
    assert features[BehaviorFeatureCode.NIGHT_SPENDING_RATIO].raw_value == 0.5333
    assert features[BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO].raw_value == 0.1333
    assert features[BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO].raw_value == 0.2
    assert features[BehaviorFeatureCode.CATEGORY_CONCENTRATION].raw_value == 0.3333
    assert features[BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE].status == (
        BehaviorFeatureStatus.AVAILABLE
    )
    assert features[BehaviorFeatureCode.NEW_MERCHANT_RATIO].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert features[BehaviorFeatureCode.REPEAT_MERCHANT_RATIO].raw_value == 0.0
    assert features[BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO].raw_value == 0.1333
    assert features[BehaviorFeatureCode.SAVING_EDUCATION_RATIO].raw_value == 0.2667
    assert features[BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO].raw_value == 0.4
    assert features[BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO].raw_value == 0.1818
    assert features[BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO].raw_value == 0.3333
    assert features[BehaviorFeatureCode.PLANNED_EXPENSE_RATIO].raw_value == 0.4545
    assert features[BehaviorFeatureCode.RECURRING_EXPENSE_RATIO].raw_value == 0.1818
    assert features[BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY].status == (
        BehaviorFeatureStatus.AVAILABLE
    )
    assert features[BehaviorFeatureCode.OUTLIER_RATIO].raw_value == 0.0
    assert features[BehaviorFeatureCode.PLANNED_EXPENSE_RATIO].unit == (
        BehaviorFeatureUnit.AMOUNT_RATIO
    )
    assert features[BehaviorFeatureCode.NEW_MERCHANT_RATIO].unit == BehaviorFeatureUnit.COUNT_RATIO


def test_nullable_behavior_signals_are_excluded_from_denominators() -> None:
    features = features_by_code(
        (
            tx(1, amount="100", is_shared_expense=True, is_planned=True, is_recurring=None),
            tx(2, amount="300", is_shared_expense=None, is_planned=None, is_recurring=True),
            tx(3, amount="600", is_shared_expense=False, is_planned=False, is_recurring=False),
        )
    )

    assert features[BehaviorFeatureCode.SHARED_EXPENSE_RATIO].raw_value == 0.1429
    assert features[BehaviorFeatureCode.PLANNED_EXPENSE_RATIO].raw_value == 0.1429
    assert features[BehaviorFeatureCode.RECURRING_EXPENSE_RATIO].raw_value == 0.3333


def test_zero_and_one_transaction_inputs_return_unavailable_when_sample_is_missing() -> None:
    empty_features = features_by_code(())
    one_features = features_by_code((tx(1, merchant_key="solo"),))

    assert empty_features[BehaviorFeatureCode.SHARED_EXPENSE_RATIO].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert empty_features[BehaviorFeatureCode.CATEGORY_CONCENTRATION].raw_value is None
    assert one_features[BehaviorFeatureCode.CATEGORY_CONCENTRATION].raw_value == 1.0
    assert one_features[BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert one_features[BehaviorFeatureCode.REPEAT_MERCHANT_RATIO].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert one_features[BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert one_features[BehaviorFeatureCode.OUTLIER_RATIO].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )


def test_repeat_merchant_uses_visits_after_first_and_new_requires_baseline() -> None:
    transactions = (
        tx(3, occurred_at=datetime(2026, 7, 3, tzinfo=UTC), merchant_key="new"),
        tx(1, occurred_at=datetime(2026, 7, 1, tzinfo=UTC), merchant_key="same"),
        tx(2, occurred_at=datetime(2026, 7, 2, tzinfo=UTC), merchant_key="same"),
        tx(4, occurred_at=datetime(2026, 7, 4, tzinfo=UTC), merchant_key=None),
    )

    first = calculate_behavior_metrics(transactions)
    second = calculate_behavior_metrics(tuple(reversed(transactions)))
    features = {feature.feature_code: feature for feature in first.features}

    assert features[BehaviorFeatureCode.NEW_MERCHANT_RATIO].status == (
        BehaviorFeatureStatus.UNAVAILABLE
    )
    assert features[BehaviorFeatureCode.REPEAT_MERCHANT_RATIO].raw_value == 0.3333
    assert first == second


def test_weekend_and_night_use_analysis_timezone_boundaries() -> None:
    features = features_by_code(
        (
            tx(
                1,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 14, 59, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
            tx(
                2,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 15, 0, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
            tx(
                3,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 20, 59, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
            tx(
                4,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 21, 0, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
            tx(
                5,
                amount="100",
                occurred_at=datetime(2026, 7, 4, 8, 59, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
            tx(
                6,
                amount="100",
                occurred_at=datetime(2026, 7, 4, 9, 0, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.RELATIONSHIP,
            ),
        )
    )

    assert features[BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO].raw_value == 0.8333
    assert features[BehaviorFeatureCode.NIGHT_SPENDING_RATIO].raw_value == 0.6667


def test_weekend_social_spending_uses_strong_social_signals() -> None:
    features = features_by_code(
        (
            tx(
                1,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 15, 0, tzinfo=UTC),
                category_code="FOOD",
                behavior_group=BehaviorGroup.PRACTICAL,
                is_shared_expense=False,
            ),
            tx(
                2,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 15, 0, tzinfo=UTC),
                category_code="GATHERING",
                behavior_group=BehaviorGroup.PRACTICAL,
                is_shared_expense=False,
            ),
            tx(
                3,
                amount="100",
                occurred_at=datetime(2026, 7, 3, 15, 0, tzinfo=UTC),
                category_code="MART",
                behavior_group=BehaviorGroup.PRACTICAL,
                is_shared_expense=True,
            ),
        )
    )

    assert features[BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO].raw_value == 0.6667


def test_category_concentration_and_diversity_distinguish_distributions() -> None:
    concentrated = features_by_code(
        (
            tx(1, amount="800", category_code="FOOD"),
            tx(2, amount="100", category_code="MART"),
            tx(3, amount="100", category_code="TRAVEL"),
        )
    )
    diverse = features_by_code(
        (
            tx(1, amount="100", category_code="FOOD"),
            tx(2, amount="100", category_code="MART"),
            tx(3, amount="100", category_code="TRAVEL"),
        )
    )

    assert concentrated[BehaviorFeatureCode.CATEGORY_CONCENTRATION].raw_value == 0.8
    assert diverse[BehaviorFeatureCode.CATEGORY_CONCENTRATION].raw_value == 0.3333
    assert concentrated[BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE].raw_value < (
        diverse[BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE].raw_value
    )


def test_outlier_ratio_detects_large_transaction() -> None:
    features = features_by_code(
        (
            tx(1, amount="100"),
            tx(2, amount="100"),
            tx(3, amount="100"),
            tx(4, amount="100"),
            tx(5, amount="1000"),
        )
    )

    assert features[BehaviorFeatureCode.OUTLIER_RATIO].raw_value == 0.2


def test_weekly_volatility_includes_zero_spend_weeks_and_separates_raw_score() -> None:
    features = features_by_code(
        (
            tx(
                1,
                amount="100000",
                occurred_at=datetime(2026, 7, 6, 1, 0, tzinfo=UTC),
            ),
        ),
        observation_started_at=datetime(2026, 7, 5, 15, 0, tzinfo=UTC),
        observation_ended_at=datetime(2026, 8, 2, 14, 59, tzinfo=UTC),
    )

    volatility = features[BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY]

    assert volatility.sample_count == 4
    assert volatility.raw_value == 1.7321
    assert volatility.normalized_score == 1.0


def test_non_withdrawal_transactions_are_not_used_by_feature_engine() -> None:
    features = features_by_code(
        (
            tx(1, amount="100", transaction_type=AnalysisTransactionType.REFUND),
            tx(2, amount="200", transaction_type=AnalysisTransactionType.DEPOSIT),
        )
    )

    assert all(feature.status == BehaviorFeatureStatus.UNAVAILABLE for feature in features.values())
