from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from app.ai.exceptions import LLMTimeoutError
from app.ai.grounded_report import (
    GroundedReportInput,
    GroundedReportService,
    GroundedReportValidationError,
    assert_no_prohibited_input,
    parse_grounded_report,
    validate_grounding,
)
from app.ai.report_generator import (
    EvidenceItem,
    EvidenceValueType,
    ReportGenerationRequest,
    ReportGenerationResult,
)

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
    assert result.metadata.validation["unsupportedClaims"] is False
    assert result.metadata.validation["unsupportedClaimsCheck"] == "LIMITED"
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


def test_template_fallback_accepts_period_number_in_basis_and_limitations() -> None:
    report_input = GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem(
                metric="CATEGORY_CONCENTRATION",
                value=0.64,
                basis="최근 12개월 동안 외식 카테고리가 64%였습니다.",
            ),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("최근 3개월 데이터만 사용했습니다.",),
        result_status="PROVISIONAL",
    )
    service = GroundedReportService(generator=TimeoutGenerator())

    result = service.generate(report_input)

    assert result.metadata.fallback_used is True
    assert "12개월" not in result.report.combined_text()
    assert "3개월" not in result.report.combined_text()


def test_template_fallback_does_not_convert_count_to_percent() -> None:
    report_input = GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem(
                metric="WEEKEND_TRANSACTION_COUNT",
                value=12,
                value_type=EvidenceValueType.COUNT,
                basis="주말 거래는 12건입니다.",
            ),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("표본 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )
    service = GroundedReportService(generator=TimeoutGenerator())

    result = service.generate(report_input)

    assert "WEEKEND_TRANSACTION_COUNT 12건" in result.report.summary
    assert "1200%" not in result.report.combined_text()


def test_template_fallback_does_not_convert_amount_to_percent() -> None:
    report_input = GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem(
                metric="AVERAGE_PAYMENT_AMOUNT",
                value=35000,
                value_type=EvidenceValueType.AMOUNT,
                basis="평균 결제 금액은 35,000원입니다.",
            ),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("표본 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )
    service = GroundedReportService(generator=TimeoutGenerator())

    result = service.generate(report_input)

    assert "AVERAGE_PAYMENT_AMOUNT 35000원" in result.report.summary
    assert "3500000%" not in result.report.combined_text()


def test_validate_grounding_rejects_changed_mbti() -> None:
    report = parse_grounded_report(VALID_REPORT_JSON.replace("ENFP", "ISTJ", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_validate_grounding_rejects_unsupported_number() -> None:
    report = parse_grounded_report(VALID_REPORT_JSON.replace("64%", "99%", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_validator_rejects_percent_conversion_for_count_evidence() -> None:
    report_input = GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem(
                metric="WEEKEND_TRANSACTION_COUNT",
                value=12,
                value_type=EvidenceValueType.COUNT,
                basis="주말 거래는 12건입니다.",
            ),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("표본 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )
    report = parse_grounded_report(VALID_REPORT_JSON.replace("64%", "1200%", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, report_input)


def test_ratio_evidence_allows_decimal_and_percentage_forms() -> None:
    report_input = build_input()
    report = parse_grounded_report(
        VALID_REPORT_JSON.replace("64% 근거로", "0.64와 64% 근거로")
    )

    validation = validate_grounding(report, report_input)

    assert validation["evidenceNumbers"] is True


def test_number_from_unsent_sixth_evidence_is_rejected() -> None:
    report_input = GroundedReportInput(
        spending_mbti="ENFP",
        axis_scores={"EI": 0.64, "SN": 0.52, "TF": 0.48, "JP": 0.7},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(
            EvidenceItem("M1", 0.11, "M1 11%"),
            EvidenceItem("M2", 0.22, "M2 22%"),
            EvidenceItem("M3", 0.33, "M3 33%"),
            EvidenceItem("M4", 0.44, "M4 44%"),
            EvidenceItem("M5", 0.55, "M5 55%"),
            EvidenceItem("M6", 0.66, "M6 66%"),
        ),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("표본 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )
    report = parse_grounded_report(VALID_REPORT_JSON.replace("64%", "66%", 1))

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, report_input)


def test_validate_grounding_rejects_prohibited_claims() -> None:
    report = parse_grounded_report(
        VALID_REPORT_JSON.replace("이 결과는", "투자 추천을 포함합니다. 이 결과는")
    )

    with pytest.raises(GroundedReportValidationError):
        validate_grounding(report, build_input())


def test_parse_grounded_report_rejects_unknown_output_field() -> None:
    report_json = VALID_REPORT_JSON.replace(
        '"disclaimer": "이 결과는 실제 성격 진단이나 금융 진단이 아니며 금융상품을 추천하지 않습니다."',
        (
            '"disclaimer": "이 결과는 실제 성격 진단이나 금융 진단이 아니며 금융상품을 추천하지 않습니다.",'
            '"recommendedProduct": "프리미엄 카드"'
        ),
    )

    with pytest.raises(ValidationError):
        parse_grounded_report(report_json)


def test_no_prohibited_ai_input_keys() -> None:
    with pytest.raises(GroundedReportValidationError):
        assert_no_prohibited_input({"email": "blocked@example.com"})


def test_no_prohibited_ai_input_uses_structural_key_check() -> None:
    assert_no_prohibited_input({"basis": "token과 nickname이라는 단어가 일반 문장에 있습니다."})

    with pytest.raises(GroundedReportValidationError):
        assert_no_prohibited_input({"confidence": {"contact": "blocked@example.com"}})

    with pytest.raises(GroundedReportValidationError):
        assert_no_prohibited_input({"confidence": {"level": "HIGH", "score": "blocked@example.com"}})
