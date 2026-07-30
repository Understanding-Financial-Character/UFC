from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.ai.exceptions import (
    LLMConnectionError,
    LLMModelNotInstalledError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.ai.report_generator import (
    EvidenceItem,
    EvidenceValueType,
    ReportGenerationRequest,
    ReportGenerator,
)

PROMPT_VERSION = "grounded-report-v1"
MAX_EVIDENCE_ITEMS = 5

PROHIBITED_INPUT_KEYS = {
    "contact",
    "contactEmail",
    "display_name",
    "displayName",
    "email",
    "nickname",
    "user_id",
    "userId",
    "internalUserId",
    "rawTransactions",
    "transactions",
    "transactionMemo",
    "memo",
    "encrypted",
    "ciphertext",
    "accessToken",
    "refreshToken",
    "token",
    "secret",
}

PROHIBITED_REPORT_PATTERNS = (
    "성격 진단입니다",
    "금융 진단입니다",
    "진단 결과입니다",
    "투자 추천",
    "대출 추천",
    "보험 추천",
    "카드 추천",
    "금융상품 추천",
    "신용점수",
    "반드시 수익",
)

MBTI_PATTERN = re.compile(r"\b[EI][SN][TF][JP]\b")
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?%?")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
FINANCIAL_PRODUCT_PATTERN = re.compile(
    r"(금융상품|카드|대출|보험|예금|적금|펀드|주식).{0,15}"
    r"(추천(?!하지)|가입|신청|구매|선택|사용하는 것이 좋|고려해 보세요)"
)
PERSONALITY_DIAGNOSIS_PATTERN = re.compile(
    r"(실제 성격은|당신은 .{0,20}한 사람|충동적인 사람이라는 뜻)"
)
NORMALIZED_PROHIBITED_INPUT_KEYS = {
    re.sub(r"[^a-z0-9]", "", key.lower()) for key in PROHIBITED_INPUT_KEYS
}


class GroundedReportValidationError(ValueError):
    """Raised when a generated report violates grounding policy."""


class GroundedReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=700)
    strengths: list[str] = Field(min_length=1, max_length=5)
    commonPoints: list[str] = Field(min_length=1, max_length=5)
    differences: list[str] = Field(min_length=1, max_length=5)
    observationPoints: list[str] = Field(min_length=1, max_length=5)
    conversationQuestions: list[str] = Field(min_length=1, max_length=5)
    disclaimer: str = Field(min_length=1, max_length=300)

    @field_validator(
        "strengths",
        "commonPoints",
        "differences",
        "observationPoints",
        "conversationQuestions",
    )
    @classmethod
    def reject_empty_items(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("Report list fields must not contain empty items.")
        return value

    def combined_text(self) -> str:
        parts: list[str] = [self.headline, self.summary, self.disclaimer]
        for values in (
            self.strengths,
            self.commonPoints,
            self.differences,
            self.observationPoints,
            self.conversationQuestions,
        ):
            parts.extend(values)
        return "\n".join(parts)


@dataclass(frozen=True)
class GroundedReportInput:
    spending_mbti: str | None
    axis_scores: dict[str, float]
    confidence: dict[str, Any]
    evidence: tuple[EvidenceItem, ...]
    member_mbti_summary: dict[str, int]
    limitations: tuple[str, ...]
    result_status: str

    def prompt_context(self) -> GroundedPromptContext:
        context = GroundedPromptContext(
            spending_mbti=self.spending_mbti,
            axis_scores=self.axis_scores,
            confidence=self.confidence,
            evidence=self.evidence[:MAX_EVIDENCE_ITEMS],
            member_mbti_summary=self.member_mbti_summary,
            limitations=self.limitations,
            result_status=self.result_status,
        )
        assert_no_prohibited_input(context.safe_payload())
        return context

    def safe_payload(self) -> dict[str, Any]:
        return self.prompt_context().safe_payload()

    def to_generation_request(self, *, repair_instruction: str | None = None) -> ReportGenerationRequest:
        context = self.prompt_context()
        limitations = context.limitations
        if repair_instruction:
            limitations = (*limitations, repair_instruction)
        return ReportGenerationRequest(
            consumption_mbti=context.spending_mbti,
            axis_scores=context.axis_scores,
            confidence=context.confidence,
            evidence=context.evidence,
            member_mbti_summary=context.member_mbti_summary,
            limitations=limitations,
            result_status=context.result_status,
            language="ko",
        )


@dataclass(frozen=True)
class GroundedPromptContext:
    spending_mbti: str | None
    axis_scores: dict[str, float]
    confidence: dict[str, Any]
    evidence: tuple[EvidenceItem, ...]
    member_mbti_summary: dict[str, int]
    limitations: tuple[str, ...]
    result_status: str

    def safe_payload(self) -> dict[str, Any]:
        return {
            "spending_mbti": self.spending_mbti,
            "axis_scores": self.axis_scores,
            "confidence": self.confidence,
            "evidence": [
                {
                    "metric": item.metric,
                    "value": item.value,
                    "valueType": item.value_type.value,
                    "basis": item.basis,
                }
                for item in self.evidence
            ],
            "member_mbti_summary": self.member_mbti_summary,
            "limitations": list(self.limitations),
            "result_status": self.result_status,
        }


@dataclass(frozen=True)
class GroundedReportMetadata:
    prompt_version: str
    model: str
    latency_ms: int
    fallback_used: bool
    repair_attempted: bool
    validation: dict[str, bool | str]
    fallback_reason: str | None = None


@dataclass(frozen=True)
class GroundedReportResult:
    report: GroundedReport
    metadata: GroundedReportMetadata


@dataclass(frozen=True)
class GroundedReportService:
    generator: ReportGenerator
    fallback_model: str = "template"

    def generate(self, report_input: GroundedReportInput) -> GroundedReportResult:
        report_input.safe_payload()
        started_at = time.monotonic()
        repair_attempted = False
        try:
            result = self.generator.generate(report_input.to_generation_request())
            try:
                report = parse_grounded_report(result.text)
                validation = validate_grounding(report, report_input)
            except (json.JSONDecodeError, ValidationError):
                repair_attempted = True
                result = self.generator.generate(
                    report_input.to_generation_request(
                        repair_instruction=(
                            "REPAIR_JSON_ONLY: 이전 응답은 JSON Schema를 통과하지 못했습니다. "
                            "필수 키만 포함한 JSON 객체 하나로 다시 출력하세요."
                        )
                    )
                )
                report = parse_grounded_report(result.text)
                validation = validate_grounding(report, report_input)
            return GroundedReportResult(
                report=report,
                metadata=GroundedReportMetadata(
                    prompt_version=PROMPT_VERSION,
                    model=result.model,
                    latency_ms=elapsed_ms(started_at),
                    fallback_used=result.fallback_used,
                    repair_attempted=repair_attempted,
                    validation=validation,
                    fallback_reason=result.metadata.get("fallbackReason"),
                ),
            )
        except (
            LLMConnectionError,
            LLMTimeoutError,
            LLMModelNotInstalledError,
            LLMResponseError,
            json.JSONDecodeError,
            ValidationError,
            GroundedReportValidationError,
        ) as exc:
            report = build_template_report(report_input)
            validation = validate_grounding(report, report_input)
            return GroundedReportResult(
                report=report,
                metadata=GroundedReportMetadata(
                    prompt_version=PROMPT_VERSION,
                    model=self.fallback_model,
                    latency_ms=elapsed_ms(started_at),
                    fallback_used=True,
                    repair_attempted=repair_attempted,
                    validation=validation,
                    fallback_reason=type(exc).__name__,
                ),
            )


def parse_grounded_report(raw_text: str) -> GroundedReport:
    return GroundedReport.model_validate_json(extract_json_object(raw_text))


def extract_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError("JSON object not found", raw_text, 0)
    return text[start : end + 1]


def validate_grounding(report: GroundedReport, report_input: GroundedReportInput) -> dict[str, bool | str]:
    context = report_input.prompt_context()
    text = report.combined_text()
    validate_mbti_not_changed(
        text,
        context.spending_mbti,
        set(context.member_mbti_summary),
    )
    validate_prohibited_claims(text)
    validate_supported_numbers(text, context)
    return {
        "schema": True,
        "evidenceNumbers": True,
        "unsupportedClaims": False,
        "unsupportedClaimsCheck": "LIMITED",
        "diagnosisLanguage": True,
        "financialProductRecommendation": True,
    }


def validate_mbti_not_changed(
    text: str,
    spending_mbti: str | None,
    member_mbti_types: set[str],
) -> None:
    if not spending_mbti:
        return
    mentioned = {match.group(0) for match in MBTI_PATTERN.finditer(text)}
    changed = mentioned - {spending_mbti} - member_mbti_types
    if changed:
        raise GroundedReportValidationError("Report changed the supplied spending MBTI.")


def validate_prohibited_claims(text: str) -> None:
    lowered = text.lower()
    for pattern in PROHIBITED_REPORT_PATTERNS:
        if pattern.lower() in lowered:
            raise GroundedReportValidationError(f"Report contains prohibited wording: {pattern}")
    for pattern in (FINANCIAL_PRODUCT_PATTERN, PERSONALITY_DIAGNOSIS_PATTERN):
        if pattern.search(text):
            raise GroundedReportValidationError("Report contains prohibited diagnosis or recommendation wording.")


def validate_supported_numbers(text: str, context: GroundedPromptContext) -> None:
    allowed = supported_number_tokens(context)
    for raw in NUMBER_PATTERN.findall(text):
        token = raw.rstrip("%")
        if token not in allowed and raw not in allowed:
            raise GroundedReportValidationError(f"Report contains unsupported number: {raw}")


def supported_number_tokens(context: GroundedPromptContext) -> set[str]:
    tokens: set[str] = set()
    ratio_values: set[float | int] = set()
    collect_numeric_values(context.axis_scores, ratio_values)
    collect_numeric_values(context.confidence, ratio_values)
    for value in ratio_values:
        add_ratio_number_tokens(tokens, value)
    for value in context.member_mbti_summary.values():
        add_plain_number_tokens(tokens, value)
    for item in context.evidence:
        add_evidence_number_tokens(tokens, item)
    return tokens


def add_evidence_number_tokens(tokens: set[str], item: EvidenceItem) -> None:
    if not isinstance(item.value, int | float):
        return
    if item.value_type == EvidenceValueType.RATIO:
        add_ratio_number_tokens(tokens, item.value)
        return
    if item.value_type == EvidenceValueType.PERCENTAGE:
        tokens.add(format_number(item.value))
        tokens.add(f"{format_number(item.value)}%")
        return
    add_plain_number_tokens(tokens, item.value)


def add_ratio_number_tokens(tokens: set[str], value: float) -> None:
    tokens.add(format_number(value))
    tokens.add(format_number(value * 100))
    tokens.add(f"{format_number(value * 100)}%")


def add_plain_number_tokens(tokens: set[str], value: float) -> None:
    tokens.add(format_number(value))


def collect_numeric_values(value: Any, values: set[float | int]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int | float):
        values.add(value)
        return
    if isinstance(value, dict):
        for child in value.values():
            collect_numeric_values(child, values)
        return
    if isinstance(value, list | tuple):
        for child in value:
            collect_numeric_values(child, values)


def format_number(value: float) -> str:
    rounded = round(float(value), 2)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def evidence_display(item: EvidenceItem) -> str:
    if item.value is None:
        return item.metric
    if not isinstance(item.value, int | float):
        return f"{item.metric} {item.value}"
    if item.value_type == EvidenceValueType.RATIO:
        return f"{item.metric} {format_number(item.value * 100)}%"
    if item.value_type == EvidenceValueType.PERCENTAGE:
        return f"{item.metric} {format_number(item.value)}%"
    if item.value_type == EvidenceValueType.COUNT:
        return f"{item.metric} {format_number(item.value)}건"
    if item.value_type == EvidenceValueType.AMOUNT:
        return f"{item.metric} {format_number(item.value)}원"
    if item.value_type == EvidenceValueType.DURATION:
        return f"{item.metric} {format_number(item.value)}일"
    return f"{item.metric} {format_number(item.value)}"


def assert_no_prohibited_input(payload: Any, path: str = "$") -> None:
    if isinstance(payload, dict):
        for key, child in payload.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if normalized in NORMALIZED_PROHIBITED_INPUT_KEYS:
                raise GroundedReportValidationError(f"Prohibited AI input key detected at {path}.{key}")
            assert_no_prohibited_input(child, f"{path}.{key}")
        return
    if isinstance(payload, list | tuple):
        for index, child in enumerate(payload):
            assert_no_prohibited_input(child, f"{path}[{index}]")
        return
    if isinstance(payload, str) and EMAIL_PATTERN.search(payload):
        raise GroundedReportValidationError(f"Prohibited email-like AI input value detected at {path}")


def build_template_report(report_input: GroundedReportInput) -> GroundedReport:
    context = report_input.prompt_context()
    mbti = context.spending_mbti or "판정 보류"
    top_basis = evidence_display(context.evidence[0]) if context.evidence else "사용 가능한 근거 부족"
    limitation_text = (
        "제공된 제한사항을 함께 고려해야 합니다."
        if context.limitations
        else "제공된 기간과 근거 안에서만 해석해야 합니다."
    )
    return GroundedReport(
        headline=f"{mbti} 소비 리포트",
        summary=(
            f"현재 결과 상태는 {context.result_status}입니다. "
            f"가장 중요한 근거는 {top_basis}입니다."
        ),
        strengths=["제공된 근거를 기준으로 소비 성향을 요약했습니다."],
        commonPoints=["구성원 MBTI 요약과 소비 MBTI를 함께 비교할 수 있습니다."],
        differences=["개인 MBTI와 소비 MBTI는 서로 다른 기준의 해석입니다."],
        observationPoints=[limitation_text],
        conversationQuestions=["이 소비 패턴이 모임의 실제 합의와 잘 맞는지 함께 이야기해 보세요."],
        disclaimer="이 결과는 실제 성격 진단이나 금융 진단이 아니며 금융상품을 추천하지 않습니다.",
    )


def elapsed_ms(started_at: float) -> int:
    return int((time.monotonic() - started_at) * 1000)
