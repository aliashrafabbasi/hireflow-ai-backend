"""Keep Docker health probes out of the terminal access log."""

from __future__ import annotations

import logging


class _HealthAccessLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/health" not in message and "/healthz" not in message


def silence_health_access_logs() -> None:
    logging.getLogger("uvicorn.access").addFilter(_HealthAccessLogFilter())
