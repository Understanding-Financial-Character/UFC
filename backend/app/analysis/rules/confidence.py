from __future__ import annotations

from app.analysis.contracts import AxisDecisionStatus, AxisScoreResult, Confidence, ConfidenceLevel


def calculate_confidence(axis_results: tuple[AxisScoreResult, ...]) -> Confidence:
    if not axis_results or any(
        axis_result.status == AxisDecisionStatus.DEFERRED for axis_result in axis_results
    ):
        return Confidence(level=ConfidenceLevel.LOW, score=0.0)
    coverage_score = sum(axis_result.coverage for axis_result in axis_results) / len(axis_results)
    margin_score = sum(min((axis_result.margin or 0.0) / 50.0, 1.0) for axis_result in axis_results) / len(
        axis_results
    )
    score = round((0.7 * coverage_score) + (0.3 * margin_score), 4)
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.6:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
    return Confidence(level=level, score=score)
