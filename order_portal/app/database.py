"""Async SQLAlchemy engine + session factory.

Mirrors the snippet on PDF p.5. ``DATABASE_URL`` is read from the environment
(defaulting to the article's ``postgresql+asyncpg://admin:secret@db/orders``)
so the same code runs locally and inside Docker Compose.
"""
from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _resolve_database_url() -> str:
    """Build the async SQLAlchemy URL from env vars.

    Priority: explicit ``DATABASE_URL`` > composed ``POSTGRES_*`` values >
    the article's default.
    """
    explicit = os.getenv("DATABASE_URL", "").strip()
    if explicit:
        return explicit

    user = os.getenv("POSTGRES_USER", "admin")
    password = os.getenv("POSTGRES_PASSWORD", "secret")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "orders")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = _resolve_database_url()

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """FastAPI / NiceGUI dependency yielding an async session."""
    async with AsyncSessionLocal() as session:
        yield session
