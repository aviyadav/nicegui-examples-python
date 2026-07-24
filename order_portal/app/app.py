"""NiceGUI application entrypoint.

Wires the layered architecture into a running server:

* configures structlog (PDF p.15)
* imports the UI pages so their ``@ui.page`` routes register (PDF p.8-13)
* mounts the ``/health`` FastAPI router (PDF p.15)
* runs ``seed.run_seed()`` on startup (tables + demo data)
* starts Uvicorn via ``ui.run`` (PDF p.16)
"""
from __future__ import annotations

import os

import redis.asyncio as aioredis
from fastapi import APIRouter
from nicegui import app, ui
from sqlalchemy import text

from .database import engine
from .logging_conf import configure_logging
from .seed import run_seed

configure_logging()

# Importing the ui package registers all @ui.page routes as a side effect.
# auth.py registers /login and /logout.
from . import ui as _ui  # noqa: E402,F401  (registers routes)
from . import auth as _auth  # noqa: E402,F401  (registers /login, /logout)


# --------------------------------------------------------------------------- #
# Health endpoint (PDF p.15)
# --------------------------------------------------------------------------- #
router = APIRouter()


@router.get("/health")
async def health():
    """Container-friendly health check for orchestrators."""
    database = "disconnected"
    redis_status = "disconnected"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database = "connected"
    except Exception:  # noqa: BLE001
        database = "error"

    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        try:
            client = aioredis.from_url(redis_url, decode_responses=True)
            await client.ping()
            redis_status = "connected"
            await client.aclose()
        except Exception:  # noqa: BLE001
            redis_status = "error"
    else:
        redis_status = "unconfigured"

    return {"status": "ok", "database": database, "redis": redis_status}


# Mount the API router onto NiceGUI's underlying FastAPI app.
app.include_router(router)


# --------------------------------------------------------------------------- #
# Startup: create schema + seed demo data
# --------------------------------------------------------------------------- #
@app.on_startup
async def _startup_seed():
    try:
        await run_seed()
    except Exception as e:  # noqa: BLE001
        # Don't crash the app if seeding fails — surface it in logs + /health.
        from .logging_conf import get_logger
        get_logger().error("startup_seed_failed", error=str(e))


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def main():
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8080"))
    # reload must be False in the container; storage_secret enables app.storage.
    ui.run(
        host=host,
        port=port,
        title="Order Portal",
        reload=False,
        storage_secret=os.getenv("SESSION_SECRET", "dev-insecure-secret"),
        show=False,
    )


if __name__ == "__main__":
    main()
