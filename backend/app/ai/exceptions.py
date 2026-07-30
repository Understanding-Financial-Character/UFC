class ReportGenerationError(Exception):
    """Base error for AI report generation failures."""


class LLMConnectionError(ReportGenerationError):
    """Raised when the configured LLM runtime cannot be reached."""


class LLMTimeoutError(ReportGenerationError):
    """Raised when the configured LLM runtime does not respond in time."""


class LLMModelNotInstalledError(ReportGenerationError):
    """Raised when the configured model is not available in the runtime."""


class LLMResponseError(ReportGenerationError):
    """Raised when the LLM runtime returns an unusable response."""
