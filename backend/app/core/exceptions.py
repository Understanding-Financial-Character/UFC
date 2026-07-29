import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApiException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def build_error_response(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "traceId": trace_id,
            }
        },
    )


def sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    for error in errors:
        location = ".".join(str(part) for part in error.get("loc", []))
        sanitized.append(
            {
                "field": location,
                "type": str(error.get("type", "validation_error")),
                "message": str(error.get("msg", "Invalid value.")),
            }
        )
    return sanitized


async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    return build_error_response(
        request=request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return build_error_response(
        request=request,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"errors": sanitize_validation_errors(exc.errors())},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    logger.exception("Unhandled request exception", extra={"trace_id": trace_id})
    return build_error_response(
        request=request,
        code="INTERNAL_ERROR",
        message="Unexpected server error.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
