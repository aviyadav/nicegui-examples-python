"""Service layer (PDF p.7, p.14).

Business rules live here. Services depend on repositories, never on the UI.
Kept framework-agnostic so the same services back both the NiceGUI pages and
the FastAPI ``/health``-style endpoints.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import redis.asyncio as aioredis

from .logging_conf import get_logger
from .repositories import OrderRepository

logger = get_logger()


def _redis_client() -> aioredis.Redis | None:
    """Return an async Redis client, or None if Redis is unreachable/unconfigured.

    The dashboard must still work without Redis (cache is an optimization, not
    a hard dependency), so callers treat None as "no cache".
    """
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return None
    return aioredis.from_url(url, decode_responses=True)


class DashboardService:
    """Aggregates order data for the operations dashboard."""

    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def dashboard(self):
        """Raw dashboard data (PDF p.7): latest orders + revenue + pending count."""
        orders = await self.repository.latest()
        revenue = sum(
            order.amount
            for order in orders
            if order.status == "PAID"
        )
        pending = sum(
            1
            for order in orders
            if order.status == "PENDING"
        )
        return {
            "orders": orders,
            "revenue": revenue,
            "pending": pending,
        }

    async def calculate(self):
        """Compute the metrics payload that gets cached in Redis."""
        data = await self.dashboard()
        return {
            "revenue": data["revenue"],
            "pending": data["pending"],
            "order_count": len(data["orders"]),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def metrics(self):
        """Cached metrics (PDF p.14).

        Avoids hammering PostgreSQL on every dashboard refresh. A 60-second
        cache is plenty for internal users who need dashboards that respond
        instantly, not millisecond-perfect analytics.
        """
        cache_key = "dashboard_metrics"
        client = _redis_client()
        if client is not None:
            try:
                cached = await client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:  # noqa: BLE001 - cache failures must never break the page
                logger.warning("redis_cache_read_failed", key=cache_key)

        metrics = await self.calculate()

        if client is not None:
            try:
                await client.setex(cache_key, 60, json.dumps(metrics))
            except Exception:  # noqa: BLE001
                logger.warning("redis_cache_write_failed", key=cache_key)
            finally:
                await client.aclose()

        return metrics


class OrderService:
    """Operations on individual orders (approve, status transitions)."""

    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def approve(self, order_id: int, actor: str | None = None) -> str:
        """Mark a PENDING order as PAID and log who approved it.

        Mirrors the real-time approve flow on PDF p.9 — the UI calls this, then
        refreshes the table. The status transition + structured log live here so
        the "who approved this three weeks ago?" question (PDF p.15) is
        answerable from logs alone.
        """
        order = await self.repository.by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} not found")

        await self.repository.update_status(order, "PAID")

        logger.info(
            "order_approved",
            order_id=order.id,
            customer=order.customer,
            user=actor,
        )
        return order.status


class ReportService:
    """Generates files (CSV summary) for the monthly report Celery task."""

    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def create(self, month: str) -> str:
        """Write a CSV report for ``month`` (YYYY-MM) and return its path."""
        orders = await self.repository.latest(limit=1000)
        # Keep only orders whose created_at falls in the requested month.
        rows = [o for o in orders if o.created_at.strftime("%Y-%m") == month]

        reports_dir = Path(os.getenv("REPORTS_DIR", "/app/reports"))
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = reports_dir / f"monthly_report_{month}_{stamp}.csv"

        lines = ["id,customer,amount,status,created_at"]
        for o in rows:
            lines.append(
                f"{o.id},{o.customer},{o.amount:.2f},{o.status},"
                f"{o.created_at.isoformat()}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")

        logger.info(
            "monthly_report_generated",
            month=month,
            rows=len(rows),
            path=str(path),
        )
        return str(path)
