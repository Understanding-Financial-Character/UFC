from app.ai.report_generator import (
    FakeReportGenerator,
    FallbackReportGenerator,
    OllamaQwenReportGenerator,
    ReportGenerator,
    TemplateReportGenerator,
)
from app.core.config import Settings


def build_report_generator(settings: Settings) -> ReportGenerator:
    if settings.llm_provider == "ollama":
        return OllamaQwenReportGenerator(settings=settings)
    if settings.llm_provider == "ollama_with_template_fallback":
        return FallbackReportGenerator(
            primary=OllamaQwenReportGenerator(
                settings=settings.model_copy(update={"llm_provider": "ollama"})
            ),
            fallback=TemplateReportGenerator(),
        )
    if settings.llm_provider == "fake":
        return FakeReportGenerator()
    if settings.llm_provider == "template":
        return TemplateReportGenerator()
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
