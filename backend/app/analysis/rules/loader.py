from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from importlib import resources

from app.analysis.contracts import BehaviorFeatureCode, ConsumptionAxis


@dataclass(frozen=True)
class FeatureRule:
    feature_code: BehaviorFeatureCode
    direction: str
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
    axes: dict[ConsumptionAxis, AxisRule] = {}
    for axis_key, axis_payload in payload["axes"].items():
        axis = ConsumptionAxis(axis_key)
        features = tuple(
            FeatureRule(
                feature_code=BehaviorFeatureCode(feature_payload["feature_code"]),
                direction=feature_payload["direction"],
                weight=float(feature_payload["weight"]),
            )
            for feature_payload in axis_payload["features"]
        )
        axes[axis] = AxisRule(
            axis=axis,
            low_pole=axis_payload["low_pole"],
            high_pole=axis_payload["high_pole"],
            features=features,
        )
    return ConsumptionMbtiRuleSet(
        rule_version=payload["rule_version"],
        schema_version=payload["schema_version"],
        min_decision_coverage=float(payload["min_decision_coverage"]),
        standard_coverage=float(payload["standard_coverage"]),
        low_margin_threshold=float(payload["low_margin_threshold"]),
        axes=axes,
    )
