from app.ai.report_generator import (
    FakeReportGenerator,
    OllamaQwenReportGenerator,
    ReportGenerator,
    TemplateReportGenerator,
)
from app.core.config import Settings


def build_report_generator(settings: Settings) -> ReportGenerator:
    if settings.llm_provider == "ollama":
        return OllamaQwenReportGenerator(settings=settings)
    if settings.llm_provider == "fake":
        return FakeReportGenerator()
    if settings.llm_provider == "template":
        return TemplateReportGenerator()
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
