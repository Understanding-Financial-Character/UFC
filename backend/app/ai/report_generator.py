from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urljoin

from app.ai.exceptions import (
    LLMConnectionError,
    LLMHttpError,
    LLMModelNotInstalledError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.core.config import Settings

SAFE_PROMPT_PREFIX = "/no_think\n"  # Qwen3 non-thinking mode hint for Ollama prompts.


class EvidenceValueType(StrEnum):
    RATIO = "RATIO"
    PERCENTAGE = "PERCENTAGE"
    COUNT = "COUNT"
    AMOUNT = "AMOUNT"
    DURATION = "DURATION"
    SCORE = "SCORE"
    TEXT = "TEXT"


class ReportGenerator(Protocol):
    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        raise NotImplementedError


@dataclass(frozen=True)
class EvidenceItem:
    metric: str
    value: float | int | str | None
    basis: str
    value_type: EvidenceValueType = EvidenceValueType.RATIO


@dataclass(frozen=True)
class ReportGenerationRequest:
    consumption_mbti: str | None
    axis_scores: dict[str, float]
    confidence: dict[str, Any]
    evidence: tuple[EvidenceItem, ...] = ()
    member_mbti_summary: dict[str, int] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    result_status: str = "INSUFFICIENT_DATA"
    language: str = "ko"

    def safe_payload(self) -> dict[str, Any]:
        return {
            "consumptionMbti": self.consumption_mbti,
            "axisScores": self.axis_scores,
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
            "memberMbtiSummary": self.member_mbti_summary,
            "limitations": list(self.limitations),
            "resultStatus": self.result_status,
            "language": self.language,
        }


@dataclass(frozen=True)
class ReportGenerationResult:
    text: str
    provider: str
    model: str
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OllamaHealth:
    available: bool
    model_installed: bool
    model: str
    runtime: str = "ollama"


class OllamaTransport(Protocol):
    def get_json(self, path: str, *, timeout_seconds: int) -> dict[str, Any]:
        raise NotImplementedError

    def post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class UrlLibOllamaTransport:
    base_url: str

    def get_json(self, path: str, *, timeout_seconds: int) -> dict[str, Any]:
        request = urllib.request.Request(urljoin(self.base_url, path), method="GET")
        return self._open_json(request, timeout_seconds=timeout_seconds)

    def post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            urljoin(self.base_url, path),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._open_json(request, timeout_seconds=timeout_seconds)

    def _open_json(
        self,
        request: urllib.request.Request,
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise LLMTimeoutError("LLM runtime request timed out.") from exc
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMHttpError(exc.code, body) from exc
        except urllib.error.URLError as exc:
            raise LLMConnectionError("LLM runtime is not reachable.") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMResponseError("LLM runtime returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise LLMResponseError("LLM runtime returned a non-object response.")
        return data


@dataclass(frozen=True)
class TemplateReportGenerator:
    model: str = "template"

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        mbti = request.consumption_mbti or "판정 보류"
        evidence = "; ".join(item.basis for item in request.evidence[:3]) or "사용 가능한 근거 부족"
        limitations = " ".join(request.limitations) or "추가 제한사항 없음."
        text = (
            f"소비 MBTI 결과는 {mbti}입니다. "
            f"현재 결과 상태는 {request.result_status}이며, 주요 근거는 {evidence}입니다. "
            f"{limitations}"
        )
        return ReportGenerationResult(
            text=text,
            provider="template",
            model=self.model,
            fallback_used=True,
        )


@dataclass(frozen=True)
class FakeReportGenerator:
    text: str = "fake report"

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        return ReportGenerationResult(
            text=self.text,
            provider="fake",
            model="fake",
            metadata={"resultStatus": request.result_status},
        )


@dataclass(frozen=True)
class FallbackReportGenerator:
    primary: ReportGenerator
    fallback: ReportGenerator

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        try:
            return self.primary.generate(request)
        except (
            LLMConnectionError,
            LLMTimeoutError,
            LLMModelNotInstalledError,
            LLMResponseError,
        ) as exc:
            result = self.fallback.generate(request)
            return replace(
                result,
                fallback_used=True,
                metadata={
                    **result.metadata,
                    "fallbackReason": type(exc).__name__,
                },
            )


@dataclass(frozen=True)
class OllamaQwenReportGenerator:
    settings: Settings
    transport: OllamaTransport | None = None

    def __post_init__(self) -> None:
        if self.settings.llm_provider != "ollama":
            raise ValueError("OllamaQwenReportGenerator requires LLM_PROVIDER=ollama.")
        if self.settings.llm_timeout_seconds <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be positive.")

    @property
    def client(self) -> OllamaTransport:
        return self.transport or UrlLibOllamaTransport(self.settings.llm_base_url)

    def check_health(self) -> OllamaHealth:
        data = self.client.get_json("/api/tags", timeout_seconds=self.settings.llm_timeout_seconds)
        models = data.get("models")
        if not isinstance(models, list):
            raise LLMResponseError("Ollama tags response is missing models.")
        model_names = {
            value
            for model in models
            if isinstance(model, dict)
            for value in (str(model.get("name", "")), str(model.get("model", "")))
            if value
        }
        model_installed = self.settings.llm_model in model_names
        if not model_installed:
            raise LLMModelNotInstalledError(f"LLM model is not installed: {self.settings.llm_model}")
        return OllamaHealth(
            available=True,
            model_installed=True,
            model=self.settings.llm_model,
        )

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        payload = {
            "model": self.settings.llm_model,
            "prompt": self._build_prompt(request),
            "stream": False,
            "think": self.settings.llm_thinking_enabled,
            "options": {
                "temperature": self.settings.llm_temperature,
                "top_p": 0.8,
                "num_predict": 512,
            },
        }
        try:
            data = self.client.post_json(
                "/api/generate",
                payload,
                timeout_seconds=self.settings.llm_timeout_seconds,
            )
        except LLMHttpError as exc:
            self._raise_for_http_error(exc)
        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise LLMResponseError("Ollama response is missing report text.")
        return ReportGenerationResult(
            text=text.strip(),
            provider="ollama",
            model=self.settings.llm_model,
            metadata={
                "thinkingEnabled": self.settings.llm_thinking_enabled,
                "temperature": self.settings.llm_temperature,
            },
        )

    def _build_prompt(self, request: ReportGenerationRequest) -> str:
        payload = json.dumps(request.safe_payload(), ensure_ascii=False, sort_keys=True)
        prefix = "" if self.settings.llm_thinking_enabled else SAFE_PROMPT_PREFIX
        return (
            f"{prefix}"
            "UFC 소비 MBTI 결과를 사용자에게 설명하는 한국어 리포트를 작성하세요. "
            "제공된 JSON 근거만 사용하고, 실제 성격 진단이나 금융 조언처럼 말하지 마세요. "
            "응답은 반드시 JSON 객체 하나만 출력하세요. "
            "필수 키는 headline, summary, strengths, commonPoints, differences, "
            "observationPoints, conversationQuestions, disclaimer 입니다. "
            "정의된 8개 키 외의 추가 키는 절대 출력하지 마세요. "
            "strengths, commonPoints, differences, observationPoints, conversationQuestions는 "
            "문자열 배열이어야 합니다. "
            "소비 MBTI를 다시 계산하거나 변경하지 마세요.\n"
            f"{payload}"
        )

    def _raise_for_http_error(self, exc: LLMHttpError) -> None:
        body = exc.response_body.lower()
        if exc.status_code == 404 and "model" in body:
            raise LLMModelNotInstalledError(
                f"LLM model is not installed: {self.settings.llm_model}"
            ) from exc
        raise LLMResponseError(f"LLM runtime returned HTTP {exc.status_code}.") from exc
