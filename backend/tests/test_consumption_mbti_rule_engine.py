from __future__ import annotations

import copy
import json
from importlib import resources

import pytest

from app.analysis.contracts import (
    BEHAVIOR_FEATURE_POLICY_VERSION,
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    CATEGORY_MAPPING_VERSION,
    AnalysisSourceType,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    BehaviorMetricsResult,
    ResultStatus,
    RuleEngineInput,
)
from app.analysis.rules.loader import RuleConfigurationError, parse_consumption_mbti_rules
from app.analysis.rules.scorer import (
    AXIS_SCORE_TIE,
    INSUFFICIENT_AXIS_COVERAGE,
    LOW_AXIS_SCORE_MARGIN,
    SYNTHETIC_DATA,
    RuleEngineInputError,
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
        for contribution in strong_p.axis_results[3].contributions
    )


def test_borderline_axis_records_low_margin() -> None:
    feature_values = strong_values(ei="E", sn="N", tf="F", jp="P")
    feature_values.update(
        {
            BehaviorFeatureCode.SHARED_EXPENSE_RATIO: 0.53,
            BehaviorFeatureCode.WEEKEND_SOCIAL_SPENDING_RATIO: 0.53,
            BehaviorFeatureCode.NIGHT_SPENDING_RATIO: 0.53,
            BehaviorFeatureCode.TRAVEL_EXPERIENCE_RATIO: 0.53,
            BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO: 0.47,
        }
    )
    result = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_from_values(feature_values))
    )

    assert result.mbti_type == "ENFP"
    assert result.result_status == ResultStatus.PROVISIONAL
    assert "EI_LOW_AXIS_SCORE_MARGIN" in result.provisional_reasons
    assert LOW_AXIS_SCORE_MARGIN in result.axis_results[0].provisional_reasons


def test_exact_neutral_axis_tie_is_deferred() -> None:
    result = score_consumption_mbti(RuleEngineInput(behavior_metrics=neutral_metrics()))

    assert result.mbti_type is None
    assert result.result_status == ResultStatus.INSUFFICIENT_DATA
    assert result.axis_margins == {"EI": 0.0, "SN": 0.0, "TF": 0.0, "JP": 0.0}
    assert "EI_AXIS_SCORE_TIE" in result.provisional_reasons
    assert AXIS_SCORE_TIE in result.axis_results[0].provisional_reasons


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
    assert INSUFFICIENT_AXIS_COVERAGE in result.axis_results[0].provisional_reasons


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
            behavior_metrics=metrics_for_profile(
                ei="E",
                sn="N",
                tf="F",
                jp="P",
                source_type=AnalysisSourceType.MOCK,
                is_synthetic=True,
            ),
        )
    )

    assert result.mbti_type == "ENFP"
    assert result.result_status == ResultStatus.PROVISIONAL
    assert SYNTHETIC_DATA in result.provisional_reasons
    assert result.confidence.level.value == "MEDIUM"


def test_mock_source_is_provisional_even_when_boolean_is_false() -> None:
    metrics = metrics_for_profile(
        ei="E",
        sn="N",
        tf="F",
        jp="P",
        source_type=AnalysisSourceType.MOCK,
        is_synthetic=False,
    )

    result = score_consumption_mbti(RuleEngineInput(behavior_metrics=metrics))

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
        and contribution.low_pole_support == 1.0
        and contribution.decided_pole_contribution == 0.0
        for contribution in result.axis_results[0].contributions
    )


def test_low_pole_evidence_has_decided_pole_contribution() -> None:
    result = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_for_profile(ei="I", sn="S", tf="T", jp="J"))
    )

    practical = next(
        contribution
        for contribution in result.axis_results[0].contributions
        if contribution.feature_code == BehaviorFeatureCode.PRACTICAL_SPENDING_RATIO
    )

    assert result.axis_results[0].decided_pole == "I"
    assert practical.low_pole_support == 1.0
    assert practical.signed_contribution < 0
    assert practical.decided_pole_contribution > 0
    assert practical in result.primary_evidence


def test_primary_evidence_is_limited_but_axis_trace_is_complete() -> None:
    result = score_consumption_mbti(
        RuleEngineInput(behavior_metrics=metrics_for_profile(ei="E", sn="N", tf="F", jp="P"))
    )

    assert len([item for item in result.primary_evidence if item.axis.value == "EI"]) == 3
    assert len(result.axis_results[0].contributions) == 5


def test_duplicate_behavior_feature_result_is_rejected() -> None:
    metrics = metrics_for_profile(ei="E", sn="N", tf="F", jp="P")
    duplicate_features = metrics.features + (metrics.features[0],)
    duplicate_metrics = BehaviorMetricsResult(
        schema_version=metrics.schema_version,
        policy_version=metrics.policy_version,
        category_mapping_version=metrics.category_mapping_version,
        analysis_timezone=metrics.analysis_timezone,
        source_type=metrics.source_type,
        is_synthetic=metrics.is_synthetic,
        features=duplicate_features,
    )

    with pytest.raises(RuleEngineInputError):
        score_consumption_mbti(RuleEngineInput(behavior_metrics=duplicate_metrics))


def test_missing_required_behavior_feature_is_rejected() -> None:
    metrics = metrics_from_values(
        {
            feature_code: value
            for feature_code, value in strong_values(ei="E", sn="N", tf="F", jp="P").items()
            if feature_code != BehaviorFeatureCode.OUTLIER_RATIO
        },
        include_only_values=True,
    )

    with pytest.raises(RuleEngineInputError):
        score_consumption_mbti(RuleEngineInput(behavior_metrics=metrics))


def test_rule_configuration_validation_rejects_invalid_direction() -> None:
    payload = rule_payload()
    payload["axes"]["EI"]["features"][0]["direction"] = "SIDEWAYS"

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_invalid_weight() -> None:
    payload = rule_payload()
    payload["axes"]["EI"]["features"][0]["weight"] = -1

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_malformed_numeric_values() -> None:
    payload = rule_payload()
    payload["axes"]["EI"]["features"][0]["weight"] = None

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)

    payload = rule_payload()
    payload["min_decision_coverage"] = "not-a-number"

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_missing_axis() -> None:
    payload = rule_payload()
    del payload["axes"]["JP"]

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_duplicate_axis_feature() -> None:
    payload = rule_payload()
    payload["axes"]["EI"]["features"].append(copy.deepcopy(payload["axes"]["EI"]["features"][0]))

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_invalid_pole() -> None:
    payload = rule_payload()
    payload["axes"]["EI"]["high_pole"] = "X"

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_invalid_thresholds() -> None:
    payload = rule_payload()
    payload["min_decision_coverage"] = 0.8
    payload["standard_coverage"] = 0.7

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def test_rule_configuration_validation_rejects_version_mismatch() -> None:
    payload = rule_payload()
    payload["requires"]["behavior_feature_schema_version"] = "behavior-features-v0"

    with pytest.raises(RuleConfigurationError):
        parse_consumption_mbti_rules(payload)


def metrics_for_profile(
    *,
    ei: str,
    sn: str,
    tf: str,
    jp: str,
    source_type: AnalysisSourceType = AnalysisSourceType.CSV,
    is_synthetic: bool = False,
) -> BehaviorMetricsResult:
    return metrics_from_values(
        strong_values(ei=ei, sn=sn, tf=tf, jp=jp),
        source_type=source_type,
        is_synthetic=is_synthetic,
    )


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
    include_only_values: bool = False,
    source_type: AnalysisSourceType = AnalysisSourceType.CSV,
    is_synthetic: bool = False,
) -> BehaviorMetricsResult:
    unavailable_features = unavailable_features or set()
    features = []
    for feature_code in ALL_RULE_FEATURES:
        if include_only_values and feature_code not in values:
            continue
        if feature_code in unavailable_features or feature_code not in values:
            features.append(unavailable_feature(feature_code))
            continue
        features.append(available_feature(feature_code, values[feature_code]))
    return BehaviorMetricsResult(
        schema_version=BEHAVIOR_FEATURE_SCHEMA_VERSION,
        policy_version=BEHAVIOR_FEATURE_POLICY_VERSION,
        category_mapping_version=CATEGORY_MAPPING_VERSION,
        analysis_timezone="Asia/Seoul",
        source_type=source_type,
        is_synthetic=is_synthetic,
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


def rule_payload() -> dict:
    rule_text = (
        resources.files("app.analysis.rules")
        .joinpath("consumption-mbti-v1.yaml")
        .read_text(encoding="utf-8")
    )
    return json.loads(rule_text)
