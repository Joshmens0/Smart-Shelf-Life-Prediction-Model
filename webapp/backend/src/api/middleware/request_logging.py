"""Structured JSON logging middleware per Universal App Template Section 8."""
import json
import logging
import sys
import time
import uuid
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Configure root logger to output JSON
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": "smart-shelf-life-api",
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = record.trace_id
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_json_logging(level: int = logging.INFO):
    """Configures root stdout handler with JsonFormatter."""
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

logger = logging.getLogger("api.request")

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to calculate execution time, inject trace IDs, and emit JSON logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.trace_id = trace_id

        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Attach trace ID header to response
            response.headers["X-Request-ID"] = trace_id

            # Avoid logging noisy health checks constantly in production
            if request.url.path != "/api/health":
                logger.info(
                    f"{request.method} {request.url.path} returned {response.status_code} ({duration_ms}ms)",
                    extra={
                        "trace_id": trace_id,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "trace_id": trace_id,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise exc
