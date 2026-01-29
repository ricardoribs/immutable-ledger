import logging
import os
from pythonjsonlogger import jsonlogger
from opentelemetry import trace


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        trace_id = ctx.trace_id if ctx else 0
        record.trace_id = format(trace_id, "032x") if trace_id else ""
        return True


def configure_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    fallback_dir = os.getenv("LOG_DIR_FALLBACK", "/tmp/immutable-ledger-logs")
    log_dir = os.getenv("LOG_DIR") or fallback_dir
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "app.log")
        handler = logging.FileHandler(log_path)
    except OSError:
        os.makedirs(fallback_dir, exist_ok=True)
        log_path = os.path.join(fallback_dir, "app.log")
        try:
            handler = logging.FileHandler(log_path)
        except OSError:
            handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(TraceIdFilter())

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = []
    root.addHandler(handler)
