"""Structured logging setup (PDF p.15).

``get_logger()`` returns a structlog logger so every call site can write
key/value context — e.g. ``logger.info("order_approved", order_id=..., user=...)``
— and later answer "who approved this order three weeks ago?" from the logs.
"""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging() -> None:
    """Configure structlog once at process start (idempotent)."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger():
    """Return a configured structlog logger."""
    try:
        return structlog.get_logger()
    except Exception:  # pragma: no cover - defensive
        return structlog.get_logger("order_portal")
