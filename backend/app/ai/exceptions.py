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


class LLMHttpError(ReportGenerationError):
    """Raised when the LLM runtime returns an HTTP error response."""

    def __init__(self, status_code: int, response_body: str) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"LLM runtime returned HTTP {status_code}.")
