import re
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response

TRACE_ID_HEADER = "X-Trace-Id"
TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="-")


def resolve_trace_id(value: str | None) -> str:
    if value and TRACE_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


async def trace_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = resolve_trace_id(request.headers.get(TRACE_ID_HEADER))
    token = trace_id_context.set(trace_id)
    request.state.trace_id = trace_id
    try:
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
    finally:
        trace_id_context.reset(token)
