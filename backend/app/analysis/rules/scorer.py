from __future__ import annotations

from app.analysis.contracts import (
    CONSUMPTION_MBTI_SCHEMA_VERSION,
    AxisContribution,
    AxisDecisionStatus,
    AxisScoreResult,
    BehaviorFeatureCode,
    BehaviorFeatureResult,
    BehaviorFeatureStatus,
    ConsumptionAxis,
    ConsumptionMbtiResult,
    ResultStatus,
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
SYNTHETIC_DATA = "SYNTHETIC_DATA"
HIGH_DIRECTION = "HIGH"
LOW_DIRECTION = "LOW"
AXIS_ORDER = (
    ConsumptionAxis.EI,
    ConsumptionAxis.SN,
    ConsumptionAxis.TF,
    ConsumptionAxis.JP,
)


def score_consumption_mbti(rule_input: RuleEngineInput) -> ConsumptionMbtiResult:
    rules = load_consumption_mbti_rules()
    features_by_code = {
        feature.feature_code: feature for feature in rule_input.behavior_metrics.features
    }
    axis_results = tuple(
        score_axis(axis_rule=rules.axes[axis], features_by_code=features_by_code, rules=rules)
        for axis in AXIS_ORDER
    )
    provisional_reasons = collect_provisional_reasons(
        axis_results=axis_results,
        rules=rules,
        is_synthetic=rule_input.is_synthetic,
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
        confidence=calculate_confidence(axis_results),
        mbti_type=mbti_type,
        primary_evidence=primary_evidence(axis_results),
        result_status=result_status,
        provisional_reasons=provisional_reasons,
        axis_results=axis_results,
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
    contributions = tuple(
        build_contribution(
            axis_rule=axis_rule,
            feature_rule=feature_rule,
            feature=features_by_code[feature_rule.feature_code],
            available_weight=available_weight,
        )
        for feature_rule in used_rules
    )
    score = None
    margin = None
    if contributions:
        score = round_axis_score(sum(contribution.contribution for contribution in contributions))
        margin = round(abs(score - 0.5) * 100, 4)
    status = (
        AxisDecisionStatus.DECIDED
        if coverage >= rules.min_decision_coverage and score is not None
        else AxisDecisionStatus.DEFERRED
    )
    decided_pole = None
    if status == AxisDecisionStatus.DECIDED and score is not None:
        decided_pole = axis_rule.high_pole if score >= 0.5 else axis_rule.low_pole
    return AxisScoreResult(
        axis=axis_rule.axis,
        score=score,
        coverage=coverage,
        margin=margin,
        low_pole=axis_rule.low_pole,
        high_pole=axis_rule.high_pole,
        decided_pole=decided_pole,
        status=status,
        provisional_reasons=axis_reasons(axis_status=status, coverage=coverage, margin=margin, rules=rules),
        contributions=contributions,
    )


def build_contribution(
    *,
    axis_rule: AxisRule,
    feature_rule: FeatureRule,
    feature: BehaviorFeatureResult,
    available_weight: float,
) -> AxisContribution:
    feature_score = clamp01(feature.normalized_score or 0.0)
    contribution_score = (
        feature_score if feature_rule.direction == HIGH_DIRECTION else 1.0 - feature_score
    )
    normalized_weight = feature_rule.weight / available_weight
    contribution = normalized_weight * contribution_score
    return AxisContribution(
        axis=axis_rule.axis,
        feature_code=feature.feature_code,
        direction=feature_rule.direction,
        weight=round_ratio(feature_rule.weight),
        normalized_weight=round_ratio(normalized_weight),
        feature_score=round_ratio(feature_score),
        contribution_score=round_ratio(contribution_score),
        contribution=round_ratio(contribution),
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
    rules: ConsumptionMbtiRuleSet,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if axis_status == AxisDecisionStatus.DEFERRED:
        reasons.append(INSUFFICIENT_AXIS_COVERAGE)
    elif coverage < rules.standard_coverage:
        reasons.append(LOW_AXIS_COVERAGE)
    if margin is not None and margin < rules.low_margin_threshold:
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
        reasons.extend(axis_result.provisional_reasons)
        if (
            axis_result.status == AxisDecisionStatus.DECIDED
            and axis_result.coverage < rules.standard_coverage
        ):
            reasons.append(f"{axis_result.axis.value}_{LOW_AXIS_COVERAGE}")
        if axis_result.margin is not None and axis_result.margin < rules.low_margin_threshold:
            reasons.append(f"{axis_result.axis.value}_{LOW_AXIS_SCORE_MARGIN}")
        if axis_result.status == AxisDecisionStatus.DEFERRED:
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
                key=lambda contribution: (-abs(contribution.contribution), contribution.feature_code.value),
            )
        )
    return tuple(selected)


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
