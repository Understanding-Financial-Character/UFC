from __future__ import annotations

from app.analysis.contracts import (
    BEHAVIOR_FEATURE_POLICY_VERSION,
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    CATEGORY_MAPPING_VERSION,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    BehaviorMetricsResult,
    ResultStatus,
    RuleEngineInput,
)
from app.analysis.rules.scorer import (
    INSUFFICIENT_AXIS_COVERAGE,
    LOW_AXIS_SCORE_MARGIN,
    SYNTHETIC_DATA,
    score_consumption_mbti,
)

ALL_RULE_FEATURES = (
    BehaviorFeatureCode.SHARED_EXPENSE_RATIO,
    BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO,
    BehaviorFeatureCode.NIGHT_SPENDING_RATIO,
    BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO,
    BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO,
    BehaviorFeatureCode.CATEGORY_CONCENTRATION,
    BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE,
    BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO,
    BehaviorFeatureCode.SAVING_EDUCATION_RATIO,
    BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO,
    BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO,
    BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO,
    BehaviorFeatureCode.PLANNED_EXPENSE_RATIO,
    BehaviorFeatureCode.RECURRING_EXPENSE_RATIO,
    BehaviorFeatureCode.REPEAT_MERCHANT_RATIO,
    BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY,
    BehaviorFeatureCode.OUTLIER_RATIO,
)


def test_golden_strong_e_and_strong_i() -> None:
    strong_e = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("EI", "E")))
    )
    strong_i = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("EI", "I")))
    )

    assert strong_e.axis_scores["EI"] == 1.0
    assert strong_i.axis_scores["EI"] == 0.0


def test_golden_strong_s_and_strong_n() -> None:
    strong_s = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("SN", "S")))
    )
    strong_n = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("SN", "N")))
    )

    assert strong_s.axis_scores["SN"] == 0.0
    assert strong_n.axis_scores["SN"] == 1.0


def test_golden_strong_t_and_strong_f() -> None:
    strong_t = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("TF", "T")))
    )
    strong_f = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("TF", "F")))
    )

    assert strong_t.axis_scores["TF"] == 0.0
    assert strong_f.axis_scores["TF"] == 1.0


def test_golden_strong_j_and_strong_p_with_outlier() -> None:
    strong_j = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("JP", "J")))
    )
    strong_p = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(axis_values("JP", "P")))
    )

    assert strong_j.axis_scores["JP"] == 0.0
    assert strong_p.axis_scores["JP"] == 1.0
    assert any(
        contribution.feature_code == BehaviorFeatureCode.OUTLIER_RATIO
        and contribution.axis.value == "JP"
        for contribution in strong_p.primary_evidence
    )


def test_borderline_axis_records_low_margin() -> None:
    result = score_consumption_mbti(RuleEngineInput(behavior_metrics=neutral_metrics()))

    assert result.mbti_type == "ENFP"
    assert result.result_status == ResultStatus.PROVISIONAL
    assert LOW_AXIS_SCORE_MARGIN in result.provisional_reasons
    assert result.axis_margins == {"EI": 0.0, "SN": 0.0, "TF": 0.0, "JP": 0.0}


def test_insufficient_data_defers_axis_and_final_type() -> None:
    result = score_consumption_mbti(
        RuleEngineInput(
            behavior_metrics=metrics_from_values(
                {BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 1.0}
            )
        )
    )

    assert result.mbti_type is None
    assert result.result_status == ResultStatus.INSUFFICIENT_DATA
    assert result.axis_scores["EI"] == 1.0
    assert result.axis_coverage["EI"] == 0.25
    assert "EI_INSUFFICIENT_AXIS_COVERAGE" in result.provisional_reasons
    assert INSUFFICIENT_AXIS_COVERAGE in result.provisional_reasons


def test_many_nullable_features_reduce_coverage_without_zero_fill() -> None:
    feature_values = strong_values(ei="E", sn="N", tf="F", jp="P")
    unavailable_features = {
        BehaviorFeatureCode.PLANNED_EXPENSE_RATIO,
        BehaviorFeatureCode.RECURRING_EXPENSE_RATIO,
    }
    result = score_consumption_mbti(
        RuleEngineInput(
            behavior_metrics=metrics_from_values(
                feature_values,
                unavailable_features=unavailable_features,
            )
        )
    )

    assert result.mbti_type == "ENFP"
    assert result.axis_coverage["JP"] == 0.55
    assert result.axis_scores["JP"] == 1.0
    assert result.result_status == ResultStatus.PROVISIONAL
    assert "JP_LOW_AXIS_COVERAGE" in result.provisional_reasons


def test_mock_data_adds_synthetic_provisional_reason() -> None:
    result = score_consumption_mbti(
        RuleEngineInput(
            behavior_metrics=metrics_for_profile(ei="E", sn="N", tf="F", jp="P"),
            is_synthetic=True,
        )
    )

    assert result.mbti_type == "ENFP"
    assert result.result_status == ResultStatus.PROVISIONAL
    assert SYNTHETIC_DATA in result.provisional_reasons


def test_conflicting_signals_keep_axis_specific_contributions() -> None:
    feature_values = strong_values(ei="E", sn="N", tf="F", jp="P")
    feature_values[BehaviorFeatureCode.SHARED_EXPENSE_RATIO] = 1.0
    feature_values[BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO] = 1.0

    result = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(feature_values))
    )

    ei_contributions = [
        contribution for contribution in result.primary_evidence if contribution.axis.value == "EI"
    ]

    assert result.axis_scores["EI"] == 0.8
    assert any(
        contribution.feature_code == BehaviorFeatureCode.SHARED_EXPENSE_RATIO
        and contribution.contribution_score == 1.0
        for contribution in ei_contributions
    )
    assert any(
        contribution.feature_code == BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO
        and contribution.contribution_score == 0.0
        for contribution in result.axis_results[0].contributions
    )


def metrics_for_profile(*, ei: str, sn: str, tf: str, jp: str) -> BehaviorMetricsResult:
    return metrics_from_values(strong_values(ei=ei, sn=sn, tf=tf, jp=jp))


def axis_values(axis: str, pole: str) -> dict[BehaviorFeatureCode, float]:
    values = {feature_code: 0.5 for feature_code in ALL_RULE_FEATURES}
    if axis == "EI":
        values.update(ei_values(pole))
    elif axis == "SN":
        values.update(sn_values(pole))
    elif axis == "TF":
        values.update(tf_values(pole))
    elif axis == "JP":
        values.update(jp_values(pole))
    return values


def neutral_metrics() -> BehaviorMetricsResult:
    return metrics_from_values({feature_code: 0.5 for feature_code in ALL_RULE_FEATURES})


def strong_values(*, ei: str, sn: str, tf: str, jp: str) -> dict[BehaviorFeatureCode, float]:
    values = {feature_code: 0.5 for feature_code in ALL_RULE_FEATURES}
    values.update(ei_values(ei))
    values.update(sn_values(sn))
    values.update(tf_values(tf))
    values.update(jp_values(jp))
    return values


def ei_values(pole: str) -> dict[BehaviorFeatureCode, float]:
    if pole == "E":
        return {
            BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 1.0,
            BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO: 1.0,
            BehaviorFeatureCode.NIGHT_SPENDING_RATIO: 1.0,
            BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO: 1.0,
            BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO: 0.0,
        }
    return {
        BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 0.0,
        BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO: 0.0,
        BehaviorFeatureCode.NIGHT_SPENDING_RATIO: 0.0,
        BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO: 0.0,
        BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO: 1.0,
    }


def sn_values(pole: str) -> dict[BehaviorFeatureCode, float]:
    if pole == "N":
        return {
            BehaviorFeatureCode.CATEGORY_CONCENTRATION: 0.0,
            BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE: 1.0,
            BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO: 1.0,
            BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO: 1.0,
            BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO: 0.0,
        }
    return {
        BehaviorFeatureCode.CATEGORY_CONCENTRATION: 1.0,
        BehaviorFeatureCode.CATEGORY_DIVERSITY_SCORE: 0.0,
        BehaviorFeatureCode.EXPERIENCE_SPENDING_RATIO: 0.0,
        BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO: 0.0,
        BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO: 1.0,
    }


def tf_values(pole: str) -> dict[BehaviorFeatureCode, float]:
    if pole == "F":
        return {
            BehaviorFeatureCode.SAVING_EDUCATION_RATIO: 0.0,
            BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO: 1.0,
            BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO: 1.0,
            BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO: 1.0,
            BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 1.0,
        }
    return {
        BehaviorFeatureCode.SAVING_EDUCATION_RATIO: 1.0,
        BehaviorFeatureCode.RELATIONSHIP_SPENDING_RATIO: 0.0,
        BehaviorFeatureCode.SHARED_EXPERIENCE_RATIO: 0.0,
        BehaviorFeatureCode.GIFT_ANNIVERSARY_RATIO: 0.0,
        BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 0.0,
    }


def jp_values(pole: str) -> dict[BehaviorFeatureCode, float]:
    if pole == "P":
        return {
            BehaviorFeatureCode.PLANNED_EXPENSE_RATIO: 0.0,
            BehaviorFeatureCode.RECURRING_EXPENSE_RATIO: 0.0,
            BehaviorFeatureCode.REPEAT_MERCHANT_RATIO: 1.0,
            BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY: 1.0,
            BehaviorFeatureCode.OUTLIER_RATIO: 1.0,
        }
    return {
        BehaviorFeatureCode.PLANNED_EXPENSE_RATIO: 1.0,
        BehaviorFeatureCode.RECURRING_EXPENSE_RATIO: 1.0,
        BehaviorFeatureCode.REPEAT_MERCHANT_RATIO: 0.0,
        BehaviorFeatureCode.WEEKLY_EXPENSE_VOLATILITY: 0.0,
        BehaviorFeatureCode.OUTLIER_RATIO: 0.0,
    }


def metrics_from_values(
    values: dict[BehaviorFeatureCode, float],
    *,
    unavailable_features: set[BehaviorFeatureCode] | None = None,
) -> BehaviorMetricsResult:
    unavailable_features = unavailable_features or set()
    features = []
    for feature_code in ALL_RULE_FEATURES:
        if feature_code in unavailable_features or feature_code not in values:
            features.append(unavailable_feature(feature_code))
            continue
        features.append(available_feature(feature_code, values[feature_code]))
    return BehaviorMetricsResult(
        schema_version=BEHAVIOR_FEATURE_SCHEMA_VERSION,
        policy_version=BEHAVIOR_FEATURE_POLICY_VERSION,
        category_mapping_version=CATEGORY_MAPPING_VERSION,
        analysis_timezone="Asia/Seoul",
        features=tuple(features),
    )


def available_feature(feature_code: BehaviorFeatureCode, value: float) -> BehaviorFeatureResult:
    return BehaviorFeatureResult(
        feature_code=feature_code,
        status=BehaviorFeatureStatus.AVAILABLE,
        raw_value=value,
        normalized_score=value,
        unit=BehaviorFeatureUnit.SCORE,
        sample_count=10,
        evidence=(f"{feature_code.value} evidence",),
    )


def unavailable_feature(feature_code: BehaviorFeatureCode) -> BehaviorFeatureResult:
    return BehaviorFeatureResult(
        feature_code=feature_code,
        status=BehaviorFeatureStatus.UNAVAILABLE,
        raw_value=None,
        normalized_score=None,
        unit=BehaviorFeatureUnit.SCORE,
        sample_count=0,
        evidence=(f"{feature_code.value} unavailable",),
    )
