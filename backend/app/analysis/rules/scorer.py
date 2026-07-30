from __future__ import annotations

from app.analysis.contracts import (
    CONSUMPTION_MBTI_SCHEMA_VERSION,
    SYNTHETIC_SOURCE_TYPES,
    AxisContribution,
    AxisDecisionStatus,
    AxisScoreResult,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    Confidence,
    ConfidenceLevel,
    ConsumptionAxis,
    ConsumptionMbtiResult,
    ResultStatus,
    RuleDirection,
    RuleEngineInput,
)
from app.analysis.rules.confidence import calculate_confidence
from app.analysis.rules.loader import (
    AxisRule,
    ConsumptionMbtiRuleSet,
    FeatureRule,
    load_consumption_mbti_rules,
)

LOW_AXIS_SCORE_MARGIN = "LOW_AXIS_SCORE_MARGIN"
LOW_AXIS_COVERAGE = "LOW_AXIS_COVERAGE"
INSUFFICIENT_AXIS_COVERAGE = "INSUFFICIENT_AXIS_COVERAGE"
AXIS_SCORE_TIE = "AXIS_SCORE_TIE"
SYNTHETIC_DATA = "SYNTHETIC_DATA"
PRIMARY_EVIDENCE_PER_AXIS = 3
AXIS_ORDER = (
    ConsumptionAxis.EI,
    ConsumptionAxis.SN,
    ConsumptionAxis.TF,
    ConsumptionAxis.JP,
)


class RuleEngineInputError(ValueError):
    pass


def score_consumption_mbti(rule_input: RuleEngineInput) -> ConsumptionMbtiResult:
    rules = load_consumption_mbti_rules()
    validate_behavior_metrics(rule_input=rule_input, rules=rules)
    features_by_code = build_feature_index(rule_input.behavior_metrics.features)
    axis_results = tuple(
        score_axis(axis_rule=rules.axes[axis], features_by_code=features_by_code, rules=rules)
        for axis in AXIS_ORDER
    )
    is_synthetic = is_synthetic_metrics(rule_input.behavior_metrics)
    provisional_reasons = collect_provisional_reasons(
        axis_results=axis_results,
        rules=rules,
        is_synthetic=is_synthetic,
    )
    mbti_type = build_mbti_type(axis_results)
    if mbti_type is None:
        result_status = ResultStatus.INSUFFICIENT_DATA
    elif provisional_reasons:
        result_status = ResultStatus.PROVISIONAL
    else:
        result_status = ResultStatus.STANDARD
    return ConsumptionMbtiResult(
        schema_version=CONSUMPTION_MBTI_SCHEMA_VERSION,
        rule_version=rules.rule_version,
        axis_scores={axis_result.axis.value: axis_result.score for axis_result in axis_results},
        axis_coverage={axis_result.axis.value: axis_result.coverage for axis_result in axis_results},
        axis_margins={axis_result.axis.value: axis_result.margin for axis_result in axis_results},
        confidence=confidence_for_result(axis_results=axis_results, is_synthetic=is_synthetic),
        mbti_type=mbti_type,
        primary_evidence=primary_evidence(axis_results),
        result_status=result_status,
        provisional_reasons=provisional_reasons,
        axis_results=axis_results,
    )


def validate_behavior_metrics(
    *,
    rule_input: RuleEngineInput,
    rules: ConsumptionMbtiRuleSet,
) -> None:
    behavior_metrics = rule_input.behavior_metrics
    if behavior_metrics.schema_version != rules.required_behavior_feature_schema_version:
        raise RuleEngineInputError("Behavior feature schema version does not match rule requirements.")
    if behavior_metrics.policy_version != rules.required_behavior_feature_policy_version:
        raise RuleEngineInputError("Behavior feature policy version does not match rule requirements.")
    if behavior_metrics.category_mapping_version != rules.required_category_mapping_version:
        raise RuleEngineInputError("Category mapping version does not match rule requirements.")
    feature_codes = [feature.feature_code for feature in behavior_metrics.features]
    if len(feature_codes) != len(set(feature_codes)):
        raise RuleEngineInputError("Behavior metrics contain duplicate feature codes.")
    required_features = {
        feature_rule.feature_code
        for axis_rule in rules.axes.values()
        for feature_rule in axis_rule.features
    }
    missing_features = sorted(required_features - set(feature_codes), key=lambda code: code.value)
    if missing_features:
        missing = ", ".join(feature_code.value for feature_code in missing_features)
        raise RuleEngineInputError(f"Behavior metrics are missing required features: {missing}.")


def build_feature_index(
    features: tuple[BehaviorFeatureResult, ...],
) -> dict[BehaviorFeatureCode, BehaviorFeatureResult]:
    return {feature.feature_code: feature for feature in features}


def is_synthetic_metrics(behavior_metrics: object) -> bool:
    return (
        getattr(behavior_metrics, "is_synthetic", False)
        or getattr(behavior_metrics, "source_type", None) in SYNTHETIC_SOURCE_TYPES
    )


def score_axis(
    *,
    axis_rule: AxisRule,
    features_by_code: dict[BehaviorFeatureCode, BehaviorFeatureResult],
    rules: ConsumptionMbtiRuleSet,
) -> AxisScoreResult:
    total_weight = sum(feature_rule.weight for feature_rule in axis_rule.features)
    used_rules = tuple(
        feature_rule
        for feature_rule in axis_rule.features
        if is_feature_available(features_by_code.get(feature_rule.feature_code))
    )
    available_weight = sum(feature_rule.weight for feature_rule in used_rules)
    coverage = round_ratio(available_weight / total_weight) if total_weight > 0 else 0.0
    high_score_parts = tuple(
        build_high_score_part(
            feature_rule=feature_rule,
            feature=features_by_code[feature_rule.feature_code],
            available_weight=available_weight,
        )
        for feature_rule in used_rules
    )
    score = None
    margin = None
    if high_score_parts:
        score = round_axis_score(sum(high_score_parts))
        margin = round(abs(score - 0.5) * 100, 4)
    is_tie = score == 0.5
    status = axis_status(coverage=coverage, score=score, is_tie=is_tie, rules=rules)
    decided_pole = None
    if status == AxisDecisionStatus.DECIDED and score is not None:
        decided_pole = axis_rule.high_pole if score > 0.5 else axis_rule.low_pole
    contributions = tuple(
        build_contribution(
            axis_rule=axis_rule,
            feature_rule=feature_rule,
            feature=features_by_code[feature_rule.feature_code],
            available_weight=available_weight,
            decided_pole=decided_pole,
        )
        for feature_rule in used_rules
    )
    return AxisScoreResult(
        axis=axis_rule.axis,
        score=score,
        coverage=coverage,
        margin=margin,
        low_pole=axis_rule.low_pole,
        high_pole=axis_rule.high_pole,
        decided_pole=decided_pole,
        status=status,
        provisional_reasons=axis_reasons(
            axis_status=status,
            coverage=coverage,
            margin=margin,
            is_tie=is_tie,
            rules=rules,
        ),
        contributions=contributions,
    )


def axis_status(
    *,
    coverage: float,
    score: float | None,
    is_tie: bool,
    rules: ConsumptionMbtiRuleSet,
) -> AxisDecisionStatus:
    if coverage < rules.min_decision_coverage or score is None or is_tie:
        return AxisDecisionStatus.DEFERRED
    return AxisDecisionStatus.DECIDED


def build_high_score_part(
    *,
    feature_rule: FeatureRule,
    feature: BehaviorFeatureResult,
    available_weight: float,
) -> float:
    feature_score = clamp01(feature.normalized_score or 0.0)
    high_support = (
        feature_score if feature_rule.direction == RuleDirection.HIGH else 1.0 - feature_score
    )
    return (feature_rule.weight / available_weight) * high_support


def build_contribution(
    *,
    axis_rule: AxisRule,
    feature_rule: FeatureRule,
    feature: BehaviorFeatureResult,
    available_weight: float,
    decided_pole: str | None,
) -> AxisContribution:
    feature_score = clamp01(feature.normalized_score or 0.0)
    high_pole_support = (
        feature_score if feature_rule.direction == RuleDirection.HIGH else 1.0 - feature_score
    )
    low_pole_support = 1.0 - high_pole_support
    normalized_weight = feature_rule.weight / available_weight
    contribution = normalized_weight * high_pole_support
    low_pole_contribution = normalized_weight * low_pole_support
    signed_contribution = contribution - low_pole_contribution
    decided_pole_contribution = 0.0
    if decided_pole == axis_rule.high_pole:
        decided_pole_contribution = contribution
    elif decided_pole == axis_rule.low_pole:
        decided_pole_contribution = low_pole_contribution
    return AxisContribution(
        axis=axis_rule.axis,
        feature_code=feature.feature_code,
        direction=feature_rule.direction,
        weight=round_ratio(feature_rule.weight),
        normalized_weight=round_ratio(normalized_weight),
        feature_score=round_ratio(feature_score),
        contribution_score=round_ratio(high_pole_support),
        contribution=round_ratio(contribution),
        high_pole_support=round_ratio(high_pole_support),
        low_pole_support=round_ratio(low_pole_support),
        signed_contribution=round_ratio(signed_contribution),
        decided_pole_contribution=round_ratio(decided_pole_contribution),
        evidence=feature.evidence,
    )


def is_feature_available(feature: BehaviorFeatureResult | None) -> bool:
    return (
        feature is not None
        and feature.status == BehaviorFeatureStatus.AVAILABLE
        and feature.normalized_score is not None
    )


def axis_reasons(
    *,
    axis_status: AxisDecisionStatus,
    coverage: float,
    margin: float | None,
    is_tie: bool,
    rules: ConsumptionMbtiRuleSet,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if is_tie:
        reasons.append(AXIS_SCORE_TIE)
    elif axis_status == AxisDecisionStatus.DEFERRED:
        reasons.append(INSUFFICIENT_AXIS_COVERAGE)
    elif coverage < rules.standard_coverage:
        reasons.append(LOW_AXIS_COVERAGE)
    if margin is not None and 0 < margin < rules.low_margin_threshold:
        reasons.append(LOW_AXIS_SCORE_MARGIN)
    return tuple(reasons)


def collect_provisional_reasons(
    *,
    axis_results: tuple[AxisScoreResult, ...],
    rules: ConsumptionMbtiRuleSet,
    is_synthetic: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if is_synthetic:
        reasons.append(SYNTHETIC_DATA)
    for axis_result in axis_results:
        if (
            axis_result.status == AxisDecisionStatus.DECIDED
            and axis_result.coverage < rules.standard_coverage
        ):
            reasons.append(f"{axis_result.axis.value}_{LOW_AXIS_COVERAGE}")
        if axis_result.margin is not None and 0 < axis_result.margin < rules.low_margin_threshold:
            reasons.append(f"{axis_result.axis.value}_{LOW_AXIS_SCORE_MARGIN}")
        if AXIS_SCORE_TIE in axis_result.provisional_reasons:
            reasons.append(f"{axis_result.axis.value}_{AXIS_SCORE_TIE}")
        elif axis_result.status == AxisDecisionStatus.DEFERRED:
            reasons.append(f"{axis_result.axis.value}_{INSUFFICIENT_AXIS_COVERAGE}")
    return tuple(dict.fromkeys(reasons))


def build_mbti_type(axis_results: tuple[AxisScoreResult, ...]) -> str | None:
    if any(axis_result.status == AxisDecisionStatus.DEFERRED for axis_result in axis_results):
        return None
    poles = [axis_result.decided_pole for axis_result in axis_results]
    if any(pole is None for pole in poles):
        return None
    return "".join(pole or "" for pole in poles)


def primary_evidence(axis_results: tuple[AxisScoreResult, ...]) -> tuple[AxisContribution, ...]:
    selected: list[AxisContribution] = []
    for axis_result in axis_results:
        selected.extend(
            sorted(
                axis_result.contributions,
                key=lambda contribution: (
                    -contribution.decided_pole_contribution,
                    contribution.feature_code.value,
                ),
            )[:PRIMARY_EVIDENCE_PER_AXIS]
        )
    return tuple(selected)


def confidence_for_result(
    *,
    axis_results: tuple[AxisScoreResult, ...],
    is_synthetic: bool,
) -> Confidence:
    confidence = calculate_confidence(axis_results)
    if is_synthetic and confidence.level == ConfidenceLevel.HIGH:
        return Confidence(level=ConfidenceLevel.MEDIUM, score=min(confidence.score, 0.7999))
    return confidence


def clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def round_ratio(value: float) -> float:
    return round(value, 4)


def round_axis_score(value: float) -> float:
    rounded = round_ratio(value)
    if abs(rounded) < 0.0002:
        return 0.0
    if abs(rounded - 1.0) < 0.0002:
        return 1.0
    return rounded
