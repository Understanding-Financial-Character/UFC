from dataclasses import dataclass

import pytest

from app.ai.exceptions import LLMTimeoutError
from app.ai.grounded_report import (
    GroundedReportInput,
    GroundedReportService,
    GroundedReportValidationError,
    assert_no_prohibited_input,
    parse_grounded_report,
    validate_grounding,
)
from app.ai.report_generator import EvidenceItem, ReportGenerationRequest, ReportGenerationResult

VALID_REPORT_JSON = """
{
  "headline": "ENFP 소비 리포트",
  "summary": "ENFP 소비 MBTI는 CATEGORY_CONCENTRATION 64% 근거로 설명됩니다.",
  "strengths": ["64% 근거가 있어 설명이 가능합니다."],
  "commonPoints": ["INTJ 1명과 ENFP 1명의 구성원 요약을 함께 봅니다."],
  "differences": ["개인 MBTI와 소비 MBTI는 같은 기준이 아닙니다."],
  "observationPoints": ["결과 상태는 PROVISIONAL입니다."],
  "conversationQuestions": ["64% 소비 집중이 모임의 체감과 맞나요?"],
  "disclaimer": "이 결과는 실제 성격 진단이나 금융 진단이 아니며 금융상품을 추천하지 않습니다."
}
"""


def build_input() -> GroundedReportInput:
    return GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem(
                metric="CATEGORY_CONCENTRATION",
                value=0.64,
                basis="CATEGORY_CONCENTRATION 64%",
            ),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("표본 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )


@dataclass
class SequenceGenerator:
    responses: list[str]
    model: str = "qwen3:4b"
    calls: int = 0

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        response = self.responses[self.calls]
        self.calls += 1
        return ReportGenerationResult(
            text=response,
            provider="fake",
            model=self.model,
            metadata={"call": self.calls},
        )


class TimeoutGenerator:
    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        raise LLMTimeoutError("slow")


def test_parse_grounded_report_accepts_json_fence() -> None:
    report = parse_grounded_report(f"```json\n{VALID_REPORT_JSON}\n```")

    assert report.headline == "ENFP 소비 리포트"
    assert len(report.conversationQuestions) == 1


def test_grounded_report_service_generates_valid_report_metadata() -> None:
    generator = SequenceGenerator([VALID_REPORT_JSON])
    service = GroundedReportService(generator=generator)

    result = service.generate(build_input())

    assert result.report.headline == "ENFP 소비 리포트"
    assert result.metadata.prompt_version == "grounded-report-v1"
    assert result.metadata.model == "qwen3:4b"
    assert result.metadata.fallback_used is False
    assert result.metadata.repair_attempted is False
    assert result.metadata.validation["schema"] is True
    assert generator.calls == 1


def test_grounded_report_service_repairs_json_once() -> None:
    generator = SequenceGenerator(["not-json", VALID_REPORT_JSON])
    service = GroundedReportService(generator=generator)

    result = service.generate(build_input())

    assert result.report.headline == "ENFP 소비 리포트"
    assert result.metadata.repair_attempted is True
    assert result.metadata.fallback_used is False
    assert generator.calls == 2


def test_grounded_report_service_falls_back_after_repair_failure() -> None:
    generator = SequenceGenerator(["not-json", "still-not-json"])
    service = GroundedReportService(generator=generator)

    result = service.generate(build_input())

    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == "JSONDecodeError"
    assert result.report.disclaimer


def test_grounded_report_service_falls_back_on_timeout() -> None:
    service = GroundedReportService(generator=TimeoutGenerator())

    result = service.generate(build_input())

    assert result.metadata.fallback_used is True
    assert result.metadata.fallback_reason == "LLMTimeoutError"
    assert result.metadata.model == "template"


def test_validate_grounding_rejects_changed_mbti() -> None:
    report = parse_grounded_report(VALID_REPORT_JSON.replace("ENFP", "ISTJ", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_validate_grounding_rejects_unsupported_number() -> None:
    report = parse_grounded_report(VALID_REPORT_JSON.replace("64%", "99%", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_validate_grounding_rejects_prohibited_claims() -> None:
    report = parse_grounded_report(
        VALID_REPORT_JSON.replace("이 결과는", "투자 추천을 포함합니다. 이 결과는")
    )

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_no_prohibited_ai_input_keys() -> None:
    with pytest.raises(GroundedReportValidationError):
        assert_no_prohibited_input({"email": "blocked@example.com"})
