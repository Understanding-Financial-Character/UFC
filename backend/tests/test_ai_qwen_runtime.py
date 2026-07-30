import urllib.error
from dataclasses import dataclass
from typing import Any, Self

import pytest

from app.ai.exceptions import (
    LLMConnectionError,
    LLMModelNotInstalledError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.ai.factory import build_report_generator
from app.ai.report_generator import (
    EvidenceItem,
    FakeReportGenerator,
    OllamaQwenReportGenerator,
    ReportGenerationRequest,
    TemplateReportGenerator,
    UrlLibOllamaTransport,
)
from app.core.config import Settings


def build_settings(**overrides: object) -> Settings:
    values = {
        "llm_provider": "ollama",
        "llm_base_url": "http://ollama:11434",
        "llm_model": "qwen3:4b",
        "llm_thinking_enabled": False,
        "llm_temperature": 0.2,
        "llm_timeout_seconds": 30,
    }
    values.update(overrides)
    return Settings(**values)


def build_request() -> ReportGenerationRequest:
    return ReportGenerationRequest(
        consumption_mbti="ENFP",
        axis_scores={"EI": 0.7, "SN": 0.6, "TF": 0.55, "JP": 0.8},
        confidence={"level": "MEDIUM", "score": 0.64},
        evidence=(EvidenceItem(metric="CATEGORY_CONCENTRATION", value=0.4, basis="FOOD 40%"),),
        member_mbti_summary={"INTJ": 1, "ENFP": 1},
        limitations=("샘플 기간이 짧습니다.",),
        result_status="PROVISIONAL",
    )


@dataclass
class StubTransport:
    tags: dict[str, Any]
    generated: dict[str, Any] | None = None
    posted_payload: dict[str, Any] | None = None

    def get_json(self, path: str, *, timeout_seconds: int) -> dict[str, Any]:
        assert path == "/api/tags"
        assert timeout_seconds == 30
        return self.tags

    def post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        assert path == "/api/generate"
        assert timeout_seconds == 30
        self.posted_payload = payload
        return self.generated or {"response": "요약 리포트"}


def test_fake_report_generator_returns_configured_text() -> None:
    result = FakeReportGenerator(text="test report").generate(build_request())

    assert result.text == "test report"
    assert result.provider == "fake"
    assert result.model == "fake"


def test_template_report_generator_uses_safe_aggregate_fields() -> None:
    result = TemplateReportGenerator().generate(build_request())

    assert "ENFP" in result.text
    assert "FOOD 40%" in result.text
    assert result.fallback_used is True
    assert result.provider == "template"


def test_ollama_generator_checks_model_and_posts_non_thinking_payload() -> None:
    transport = StubTransport(
        tags={"models": [{"name": "qwen3:4b"}]},
        generated={"response": "근거 기반 리포트"},
    )
    generator = OllamaQwenReportGenerator(settings=build_settings(), transport=transport)

    result = generator.generate(build_request())

    assert result.text == "근거 기반 리포트"
    assert result.provider == "ollama"
    assert result.model == "qwen3:4b"
    assert transport.posted_payload is not None
    assert transport.posted_payload["model"] == "qwen3:4b"
    assert transport.posted_payload["think"] is False
    assert transport.posted_payload["options"]["temperature"] == 0.2
    assert transport.posted_payload["options"]["top_p"] == 0.8
    assert transport.posted_payload["options"]["num_predict"] == 512
    assert transport.posted_payload["prompt"].startswith("/no_think\n")
    assert "FOOD 40%" in transport.posted_payload["prompt"]
    assert "email" not in transport.posted_payload["prompt"].lower()


def test_ollama_generator_rejects_missing_model() -> None:
    generator = OllamaQwenReportGenerator(
        settings=build_settings(),
        transport=StubTransport(tags={"models": [{"name": "llama3"}]}),
    )

    with pytest.raises(LLMModelNotInstalledError):
        generator.check_health()


def test_ollama_generator_rejects_empty_response() -> None:
    generator = OllamaQwenReportGenerator(
        settings=build_settings(),
        transport=StubTransport(
            tags={"models": [{"name": "qwen3:4b"}]},
            generated={"response": ""},
        ),
    )

    with pytest.raises(LLMResponseError):
        generator.generate(build_request())


def test_ollama_generator_rejects_non_ollama_provider() -> None:
    with pytest.raises(ValueError):
        OllamaQwenReportGenerator(settings=build_settings(llm_provider="fake"))


def test_report_generator_factory_selects_provider() -> None:
    assert isinstance(build_report_generator(build_settings(llm_provider="fake")), FakeReportGenerator)
    assert isinstance(
        build_report_generator(build_settings(llm_provider="template")),
        TemplateReportGenerator,
    )
    assert isinstance(
        build_report_generator(build_settings(llm_provider="ollama")),
        OllamaQwenReportGenerator,
    )


def test_report_generator_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        build_report_generator(build_settings(llm_provider="unknown"))


def test_url_transport_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> object:
        raise TimeoutError("slow")

    monkeypatch.setattr("urllib.request.urlopen", raise_timeout)
    transport = UrlLibOllamaTransport("http://ollama:11434")

    with pytest.raises(LLMTimeoutError):
        transport.get_json("/api/tags", timeout_seconds=1)


def test_url_transport_maps_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_url_error(*args: object, **kwargs: object) -> object:
        raise urllib.error.URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)
    transport = UrlLibOllamaTransport("http://ollama:11434")

    with pytest.raises(LLMConnectionError):
        transport.get_json("/api/tags", timeout_seconds=1)


def test_url_transport_rejects_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"not-json"

    def open_response(*args: object, **kwargs: object) -> Response:
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", open_response)
    transport = UrlLibOllamaTransport("http://ollama:11434")

    with pytest.raises(LLMResponseError):
        transport.get_json("/api/tags", timeout_seconds=1)
