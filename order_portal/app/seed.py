"""Idempotent seed: create tables + demo users + sample orders.

Run via ``python -m app.seed`` or automatically on app startup (see app.py).
Safe to re-run: it only seeds when a table is empty.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy import func, select

from .database import AsyncSessionLocal, engine
from .logging_conf import configure_logging, get_logger
from .models import Base, Order, User
from .auth import hash_password

configure_logging()
logger = get_logger()


CUSTOMERS = [
    "Acme Corp", "Globex", "Initech", "Umbrella", "Hooli",
    "Stark Industries", "Wayne Enterprises", "Wonka Inc", "Cyberdyne",
    "Soylent Co",
]
STATUSES = ["PENDING", "PROCESSING", "SHIPPED", "PAID"]


async def create_schema() -> None:
    """Create all tables if they don't exist (no Alembic — pragmatic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("schema_created")


async def seed_users() -> None:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        if existing > 0:
            logger.info("users_already_seeded", count=existing)
            return
        session.add_all([
            User(
                email="admin@example.com",
                name="Admin User",
                password_hash=hash_password("admin"),
                is_admin=True,
            ),
            User(
                email="ops@example.com",
                name="Ops User",
                password_hash=hash_password("ops"),
                is_admin=False,
            ),
        ])
        await session.commit()
        logger.info("users_seeded", count=2)


async def seed_orders() -> None:
    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(func.count()).select_from(Order))).scalar() or 0
        if existing > 0:
            logger.info("orders_already_seeded", count=existing)
            return

        now = datetime.utcnow()
        orders = []
        for i in range(1, 51):
            created = now - timedelta(
                days=random.randint(0, 45),
                hours=random.randint(0, 23),
            )
            orders.append(Order(
                customer=random.choice(CUSTOMERS),
                amount=round(random.uniform(25.0, 4500.0), 2),
                # Weight toward PENDING so the Approve flow has something to do.
                status=random.choices(STATUSES, weights=[0.5, 0.2, 0.15, 0.15])[0],
                created_at=created,
            ))
        session.add_all(orders)
        await session.commit()
        logger.info("orders_seeded", count=len(orders))


async def run_seed() -> None:
    await create_schema()
    await seed_users()
    await seed_orders()
    logger.info("seed_complete")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seed())
