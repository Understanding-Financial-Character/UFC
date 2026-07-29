from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

TRACE_ID_HEADER = "X-Trace-Id"


async def trace_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers[TRACE_ID_HEADER] = trace_id
    return response
