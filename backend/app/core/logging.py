import logging

from app.core.config import Settings
from app.core.trace import trace_id_context


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = trace_id_context.get()
        return True


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s trace_id=%(trace_id)s [%(name)s] %(message)s",
    )

    trace_filter = TraceIdFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(trace_filter)
