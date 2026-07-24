"""Celery app + background tasks (PDF p.12).

The UI never blocks on PDF exports / nightly reports — it enqueues a task and
returns immediately. This module is importable both by the worker
(``celery -A app.celery_app worker``) and by the app (to call ``.delay()``).
"""
from __future__ import annotations

import asyncio
import os

from celery import Celery, shared_task

from .database import AsyncSessionLocal
from .logging_conf import configure_logging, get_logger
from .repositories import OrderRepository
from .services import ReportService

configure_logging()
logger = get_logger()


def _broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL", "redis://redis:6379/1")


def _result_backend() -> str:
    return (
        os.getenv("CELERY_RESULT_BACKEND")
        or os.getenv("CELERY_BROKER_URL")
        or os.getenv("REDIS_URL", "redis://redis:6379/2")
    )


celery_app = Celery(
    "order_portal",
    broker=_broker_url(),
    backend=_result_backend(),
)
celery_app.conf.update(
    task_default_queue="order_portal",
    worker_prefetch_multiplier=1,
)


async def _run_report(month: str) -> str:
    async with AsyncSessionLocal() as session:
        repo = OrderRepository(session)
        service = ReportService(repo)
        return await service.create(month)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def generate_monthly_report(month: str) -> str:
    """Build the monthly CSV report.

    PDF p.12 signature + retry policy verbatim; the body bridges Celery's sync
    world into the async ReportService via a fresh event loop.
    """
    logger.info("monthly_report_started", month=month)
    path = asyncio.run(_run_report(month))
    logger.info("monthly_report_done", month=month, path=path)
    return path
