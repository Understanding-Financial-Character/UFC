from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from importlib import resources
from math import isfinite
from typing import Any

from app.analysis.contracts import (
    BEHAVIOR_FEATURE_POLICY_VERSION,
    BEHAVIOR_FEATURE_SCHEMA_VERSION,
    CATEGORY_MAPPING_VERSION,
    CONSUMPTION_MBTI_SCHEMA_VERSION,
    BehaviorFeatureCode,
    ConsumptionAxis,
    RuleDirection,
)

CONSUMPTION_MBTI_RULE_VERSION = "consumption-mbti-v1"
EXPECTED_AXIS_POLES = {
    ConsumptionAxis.EI: ("I", "E"),
    ConsumptionAxis.SN: ("S", "N"),
    ConsumptionAxis.TF: ("T", "F"),
    ConsumptionAxis.JP: ("J", "P"),
}


class RuleConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class FeatureRule:
    feature_code: BehaviorFeatureCode
    direction: RuleDirection
    weight: float


@dataclass(frozen=True)
class AxisRule:
    axis: ConsumptionAxis
    low_pole: str
    high_pole: str
    features: tuple[FeatureRule, ...]


@dataclass(frozen=True)
class ConsumptionMbtiRuleSet:
    rule_version: str
    schema_version: str
    required_behavior_feature_schema_version: str
    required_behavior_feature_policy_version: str
    required_category_mapping_version: str
    min_decision_coverage: float
    standard_coverage: float
    low_margin_threshold: float
    axes: dict[ConsumptionAxis, AxisRule]


@cache
def load_consumption_mbti_rules() -> ConsumptionMbtiRuleSet:
    rule_text = (
        resources.files("app.analysis.rules")
        .joinpath("consumption-mbti-v1.yaml")
        .read_text(encoding="utf-8")
    )
    payload = json.loads(rule_text)
    return parse_consumption_mbti_rules(payload)


def parse_consumption_mbti_rules(payload: dict[str, Any]) -> ConsumptionMbtiRuleSet:
    axes: dict[ConsumptionAxis, AxisRule] = {}
    for axis_key, axis_payload in payload.get("axes", {}).items():
        axis = enum_value(ConsumptionAxis, axis_key, "axis")
        features = tuple(
            FeatureRule(
                feature_code=enum_value(
                    BehaviorFeatureCode,
                    feature_payload.get("feature_code"),
                    f"{axis.value}.feature_code",
                ),
                direction=enum_value(
                    RuleDirection,
                    feature_payload.get("direction"),
                    f"{axis.value}.direction",
                ),
                weight=finite_float(feature_payload.get("weight"), f"{axis.value}.weight"),
            )
            for feature_payload in axis_payload.get("features", ())
        )
        axes[axis] = AxisRule(
            axis=axis,
            low_pole=axis_payload.get("low_pole"),
            high_pole=axis_payload.get("high_pole"),
            features=features,
        )
    requirements = payload.get("requires", {})
    rule_set = ConsumptionMbtiRuleSet(
        rule_version=payload.get("rule_version"),
        schema_version=payload.get("schema_version"),
        required_behavior_feature_schema_version=requirements.get(
            "behavior_feature_schema_version"
        ),
        required_behavior_feature_policy_version=requirements.get(
            "behavior_feature_policy_version"
        ),
        required_category_mapping_version=requirements.get("category_mapping_version"),
        min_decision_coverage=finite_float(
            payload.get("min_decision_coverage"),
            "min_decision_coverage",
        ),
        standard_coverage=finite_float(payload.get("standard_coverage"), "standard_coverage"),
        low_margin_threshold=finite_float(
            payload.get("low_margin_threshold"),
            "low_margin_threshold",
        ),
        axes=axes,
    )
    validate_rules(rule_set)
    return rule_set


def validate_rules(rule_set: ConsumptionMbtiRuleSet) -> None:
    if rule_set.schema_version != CONSUMPTION_MBTI_SCHEMA_VERSION:
        raise RuleConfigurationError("Rule schema_version does not match contract.")
    if rule_set.rule_version != CONSUMPTION_MBTI_RULE_VERSION:
        raise RuleConfigurationError("Rule version does not match loader expectation.")
    if rule_set.required_behavior_feature_schema_version != BEHAVIOR_FEATURE_SCHEMA_VERSION:
        raise RuleConfigurationError("Behavior feature schema version requirement is invalid.")
    if rule_set.required_behavior_feature_policy_version != BEHAVIOR_FEATURE_POLICY_VERSION:
        raise RuleConfigurationError("Behavior feature policy version requirement is invalid.")
    if rule_set.required_category_mapping_version != CATEGORY_MAPPING_VERSION:
        raise RuleConfigurationError("Category mapping version requirement is invalid.")
    expected_axes = set(ConsumptionAxis)
    if set(rule_set.axes) != expected_axes:
        raise RuleConfigurationError("Rule set must define every consumption axis exactly once.")
    validate_thresholds(rule_set)
    for axis, axis_rule in rule_set.axes.items():
        expected_low_pole, expected_high_pole = EXPECTED_AXIS_POLES[axis]
        if axis_rule.low_pole != expected_low_pole or axis_rule.high_pole != expected_high_pole:
            raise RuleConfigurationError(f"{axis.value} poles do not match the contract.")
        feature_codes = [feature_rule.feature_code for feature_rule in axis_rule.features]
        if len(feature_codes) != len(set(feature_codes)):
            raise RuleConfigurationError(f"{axis.value} contains duplicate feature rules.")
        for feature_rule in axis_rule.features:
            if not isfinite(feature_rule.weight) or feature_rule.weight <= 0:
                raise RuleConfigurationError(f"{axis.value} feature weights must be positive.")


def validate_thresholds(rule_set: ConsumptionMbtiRuleSet) -> None:
    thresholds = (
        rule_set.min_decision_coverage,
        rule_set.standard_coverage,
        rule_set.low_margin_threshold,
    )
    if any(not isfinite(threshold) for threshold in thresholds):
        raise RuleConfigurationError("Rule thresholds must be finite.")
    if not 0 <= rule_set.min_decision_coverage <= rule_set.standard_coverage <= 1:
        raise RuleConfigurationError("Coverage thresholds must be ordered within 0..1.")
    if not 0 <= rule_set.low_margin_threshold <= 50:
        raise RuleConfigurationError("Low margin threshold must be within 0..50.")


def enum_value(enum_type: type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise RuleConfigurationError(f"Invalid {field_name}: {value}") from exc


def finite_float(value: Any, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise RuleConfigurationError(f"Invalid numeric value for {field_name}: {value}") from exc
    if not isfinite(parsed):
        raise RuleConfigurationError(f"{field_name} must be finite.")
    return parsed
