from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.ai.grounded_report import GroundedReportInput, GroundedReportService
from app.ai.report_generator import (
    EvidenceItem,
    EvidenceValueType,
    ReportGenerationRequest,
    ReportGenerationResult,
)
from app.analysis.behavior_metrics import calculate_behavior_metrics
from app.analysis.contracts import (
    AnalysisInput,
    AnalysisMemberInput,
    AnalysisPeriod,
    AnalysisSourceType,
    AnalysisTransactionInput,
    AnalysisTransactionType,
    BehaviorGroup,
    GroupPurposeType,
    ResultStatus,
    RuleEngineInput,
)
from app.analysis.preprocessing import preprocess_analysis_input
from app.analysis.rules import score_consumption_mbti

ROOT = Path(__file__).resolve().parents[1]
MOCK_TRANSACTION_PATH = ROOT / "app/modules/transactions/fixtures/transactions_mock_v2.csv"
CATEGORY_SEED_PATH = ROOT / "migrations/data/20260730_0004_categories.csv"

EXPECTED_MOCK_RESULTS = {
    "SCN-01": "ENFJ",
    "SCN-02": "ISTJ",
    "SCN-03": "ENTJ",
    "SCN-04": "ENFJ",
    "SCN-05": "ENFP",
    "SCN-06": "ISTJ",
    "SCN-07": "INTP",
}


@dataclass(frozen=True)
class CategorySeed:
    code: str
    behavior_group: BehaviorGroup


@dataclass
class JsonReportGenerator:
    calls: int = 0

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        self.calls += 1
        report = {
            "headline": f"{request.consumption_mbti} 소비 리포트",
            "summary": f"{request.consumption_mbti} 결과는 CATEGORY_CONCENTRATION 64% 근거로 설명됩니다.",
            "strengths": ["64% 근거가 있어 설명이 가능합니다."],
            "commonPoints": ["구성원 MBTI 요약과 함께 해석합니다."],
            "differences": ["개인 MBTI와 소비 MBTI는 같은 기준이 아닙니다."],
            "observationPoints": [f"결과 상태는 {request.result_status}입니다."],
            "conversationQuestions": ["64% 소비 집중이 모임의 체감과 맞나요?"],
            "disclaimer": "이 결과는 실제 성격 진단이나 금융 진단이 아니며 금융상품을 추천하지 않습니다.",
        }
        import json

        return ReportGenerationResult(
            text=json.dumps(report, ensure_ascii=False),
            provider="fake",
            model="qwen3:4b",
        )


def test_mock_scenarios_produce_expected_consumption_mbti_without_db_or_llm() -> None:
    scenarios = load_mock_scenarios()

    for scenario_id, expected_mbti in EXPECTED_MOCK_RESULTS.items():
        preprocessing, metrics, result = run_mock_pipeline(scenarios[scenario_id])

        assert preprocessing.analysis_eligible is True
        assert metrics.source_type == AnalysisSourceType.MOCK
        assert result.mbti_type == expected_mbti
        assert result.result_status == ResultStatus.PROVISIONAL
        assert "SYNTHETIC_DATA" in result.provisional_reasons
        assert all(coverage >= 0.5 for coverage in result.axis_coverage.values())


def test_sparse_mock_scenario_stops_before_rule_and_llm_judgment() -> None:
    scenario_rows = load_mock_scenarios()["SCN-08"]
    analysis_input = build_analysis_input(scenario_rows)

    preprocessing = preprocess_analysis_input(analysis_input)

    assert preprocessing.analysis_eligible is False
    assert preprocessing.result_status_candidate == ResultStatus.INSUFFICIENT_DATA
    assert "Transaction count is below the minimum analysis threshold." in preprocessing.limitations


def test_grounded_report_accepts_rule_engine_output_without_sensitive_inputs() -> None:
    _preprocessing, _metrics, result = run_mock_pipeline(load_mock_scenarios()["SCN-05"])
    generator = JsonReportGenerator()
    service = GroundedReportService(generator=generator)

    report_result = service.generate(
        GroundedReportInput(
            spending_mbti=result.mbti_type,
            axis_scores={axis: score or 0.0 for axis, score in result.axis_scores.items()},
            confidence={
                "level": result.confidence.level.value,
                "score": result.confidence.score,
            },
            evidence=(
                EvidenceItem(
                    metric="CATEGORY_CONCENTRATION",
                    value=0.64,
                    value_type=EvidenceValueType.RATIO,
                    basis="CATEGORY_CONCENTRATION 64%",
                ),
            ),
            member_mbti_summary={"INTJ": 1, "ENFP": 1},
            limitations=("Mock data is synthetic.",),
            result_status=result.result_status.value,
        )
    )

    assert generator.calls == 1
    assert report_result.report.headline == "ENFP 소비 리포트"
    assert report_result.metadata.model == "qwen3:4b"
    assert report_result.metadata.fallback_used is False
    assert report_result.metadata.validation["schema"] is True


def run_mock_pipeline(rows: list[dict[str, str]]):
    analysis_input = build_analysis_input(rows)
    preprocessing = preprocess_analysis_input(analysis_input)
    metrics = calculate_behavior_metrics(preprocessing.normalized_transactions)
    result = score_consumption_mbti(RuleEngineInput(behavior_metrics=metrics))
    return preprocessing, metrics, result


def build_analysis_input(rows: list[dict[str, str]]) -> AnalysisInput:
    category_map = load_categories()
    transactions = tuple(build_transaction(row, category_map) for row in rows)
    occurred_at_values = tuple(transaction.occurred_at for transaction in transactions)
    scenario_id = rows[0]["source_row_key"].split("-TXN-", maxsplit=1)[0]
    members = tuple(
        AnalysisMemberInput(member_id=member_id, mbti_type="INTJ")
        for member_id in sorted({row["member_id"] for row in rows if row["member_id"]})
    )
    return AnalysisInput(
        analysis_id=f"analysis-{scenario_id}",
        group_id=rows[0]["group_id"],
        group_purpose_type=GroupPurposeType.OTHER,
        analysis_period=AnalysisPeriod(
            started_at=min(occurred_at_values),
            ended_at=max(occurred_at_values),
        ),
        source_type=AnalysisSourceType.MOCK,
        is_synthetic=True,
        members=members,
        transactions=transactions,
    )


def build_transaction(
    row: dict[str, str],
    category_map: dict[str, CategorySeed],
) -> AnalysisTransactionInput:
    category = category_map[row["category_id"]]
    return AnalysisTransactionInput(
        transaction_id=row["id"],
        group_id=row["group_id"],
        member_id=row["member_id"] or None,
        occurred_at=datetime.fromisoformat(row["transaction_at"]),
        amount=Decimal(row["amount"]),
        category_code=category.code,
        behavior_group=category.behavior_group,
        merchant_key=row["merchant_name"] or None,
        transaction_type=AnalysisTransactionType(row["transaction_type"]),
        is_shared_expense=parse_nullable_bool(row["is_shared_expense"]),
        is_planned=parse_nullable_bool(row["is_planned"]),
        is_recurring=parse_nullable_bool(row["is_recurring"]),
        source_type=AnalysisSourceType.MOCK,
        is_excluded=parse_nullable_bool(row["is_excluded"]) is True,
    )


def load_categories() -> dict[str, CategorySeed]:
    with CATEGORY_SEED_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return {
            row["id"]: CategorySeed(
                code=row["code"],
                behavior_group=BehaviorGroup(row["behavior_group"]),
            )
            for row in csv.DictReader(handle)
        }


def load_mock_scenarios() -> dict[str, list[dict[str, str]]]:
    rows_by_scenario: dict[str, list[dict[str, str]]] = defaultdict(list)
    with MOCK_TRANSACTION_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            scenario_id = row["source_row_key"].split("-TXN-", maxsplit=1)[0]
            rows_by_scenario[scenario_id].append(row)
    return dict(rows_by_scenario)


def parse_nullable_bool(value: str) -> bool | None:
    stripped = value.strip()
    if not stripped:
        return None
    return stripped.upper() == "TRUE"
