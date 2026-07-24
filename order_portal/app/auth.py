"""Authentication (PDF p.13).

NiceGUI is built on FastAPI, so we reuse one authentication source for both the
UI pages and any REST endpoints. This module provides:

* ``hash_password`` / ``verify_password`` — bcrypt helpers (used by seed + login).
* ``current_user`` — a FastAPI dependency (PDF p.13 pattern) that resolves the
  signed session cookie into a ``User``.
* ``require_user`` — a NiceGUI page decorator that redirects anonymous users
  to ``/login`` and (optionally) enforces ``is_admin``.
* ``@ui.page("/login")`` — the login form.

Set ``AUTH_DISABLED=1`` to bypass auth entirely (debugging only).
"""
from __future__ import annotations

import asyncio
import os
import secrets
from functools import wraps

import bcrypt
from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from nicegui import app, ui

from .database import AsyncSessionLocal
from .logging_conf import get_logger
from .models import User
from .repositories import UserRepository

logger = get_logger()

SESSION_COOKIE = "order_portal_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 hours

# Public paths that never require auth (the login page itself + the API health
# check, which is meant for orchestrators).
PUBLIC_PATHS = {"/login", "/health"}


# --------------------------------------------------------------------------- #
# Password hashing (bcrypt directly — avoids passlib/bcrypt>=4 incompatibility)
# --------------------------------------------------------------------------- #
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Session cookie (signed, timestamped)
# --------------------------------------------------------------------------- #
def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET", "dev-insecure-secret")
    return URLSafeTimedSerializer(secret, salt="order_portal-session")


def issue_session(user: User) -> str:
    """Create + store a signed session token for ``user``."""
    token = _serializer().dumps({"uid": user.id, "email": user.email})
    app.storage.user[SESSION_COOKIE] = token
    return token


async def clear_session() -> None:
    """Remove the session token and any cached user info from browser storage.

    Must be awaited: NiceGUI persists ``app.storage.user`` to the browser
    asynchronously. If we clear it and navigate in the same tick without
    waiting, the navigation can interrupt the flush and leave the token in
    storage — so the user would still appear logged in after "logout".
    """
    app.storage.user.pop(SESSION_COOKIE, None)
    app.storage.user.pop("current_user_email", None)
    app.storage.user.pop("current_user_is_admin", None)
    # Yield to the event loop so NiceGUI can flush the storage mutation to the
    # browser before any navigation runs.
    await asyncio.sleep(0)


def auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "0") == "1"


def _read_token() -> str | None:
    # app.storage.user is shared across tabs for a browser; the browser tab
    # storage is the NiceGUI-native place to keep a session token.
    return app.storage.user.get(SESSION_COOKIE)


async def _resolve_user_from_token(token: str) -> User | None:
    try:
        data = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    email = data.get("email")
    if not email:
        return None
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        return await repo.by_email(email)


async def get_current_user() -> User | None:
    """Resolve the current user from the session cookie, or None."""
    if auth_disabled():
        async with AsyncSessionLocal() as session:
            repo = UserRepository(session)
            return await repo.by_email("admin@example.com") or None
    token = _read_token()
    if not token:
        return None
    return await _resolve_user_from_token(token)


# FastAPI dependency variant (PDF p.13: ``async def current_user(): ...``).
async def current_user(request: Request) -> User:  # noqa: ARG001 - kept for FastAPI signature parity
    """FastAPI dependency returning the authenticated user (or 401)."""
    user = await get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_user(*, admin: bool = False):
    """NiceGUI page decorator: gate a page behind auth (and optionally admin).

    Usage::

        @ui.page("/admin")
        @require_user(admin=True)
        async def admin_page():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if auth_disabled():
                return await func(*args, **kwargs)
            user = await get_current_user()
            if user is None:
                ui.navigate.to("/login")
                return
            if admin and not user.is_admin:
                ui.label("Access denied").classes("text-h5 text-negative")
                ui.label("You do not have permission to view this page.")
                return
            # Expose the user to the page via the nicegui context for convenience.
            app.storage.user["current_user_email"] = user.email
            app.storage.user["current_user_is_admin"] = user.is_admin
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# --------------------------------------------------------------------------- #
# Login / logout pages
# --------------------------------------------------------------------------- #
@ui.page("/login")
async def login_page():
    """Username/password login form.

    Verifies against the seeded ``users`` table via bcrypt, then issues a
    signed session cookie and redirects to ``/``.
    """
    # If already logged in, skip the form.
    if not auth_disabled():
        existing = await get_current_user()
        if existing is not None:
            ui.navigate.to("/")
            return

    ui.add_head_html(
        "<style>"
        "body { background: #f5f7fa; }"
        ".login-card { min-width: 360px; }"
        "</style>"
    )

    with ui.column().classes("absolute-center items-center"):
        ui.label("Order Portal").classes("text-h4 q-mb-md")
        ui.label("Sign in to continue").classes("text-subtitle1 text-grey-7 q-mb-lg")

        with ui.card().classes("login-card"):
            email_input = ui.input("Email").props("autofocus").classes("w-full")
            password_input = ui.input("Password").props("type=password").classes("w-full")
            error_label = ui.label("").classes("text-negative text-caption")

            async def submit_login():
                email = (email_input.value or "").strip().lower()
                password = password_input.value or ""
                if not email or not password:
                    error_label.text = "Enter email and password."
                    return
                async with AsyncSessionLocal() as session:
                    repo = UserRepository(session)
                    user = await repo.by_email(email)
                if user is None or not verify_password(password, user.password_hash):
                    error_label.text = "Invalid email or password."
                    logger.info("login_failed", email=email)
                    return
                issue_session(user)
                logger.info("login_success", email=email)
                ui.navigate.to("/")

            ui.button("Sign in", on_click=submit_login).classes("w-full q-mt-md")
            ui.keyboard(on_key=lambda e: submit_login() if e.key == "Enter" else None)

        ui.markdown(
            "Demo credentials — `admin@example.com` / `admin` (admin) "
            "· `ops@example.com` / `ops`"
        ).classes("text-caption text-grey-7 q-mt-md")


async def do_logout() -> None:
    """Clear the session and navigate to the login page.

    Use this as the ``on_click`` handler for any "Logout" button::

        ui.button("Logout", on_click=do_logout).props("flat")

    The storage clear is awaited before navigating so the token is actually
    flushed from browser storage (see ``clear_session``).
    """
    await clear_session()
    logger.info("logout")
    ui.navigate.to("/login")


@ui.page("/logout")
async def logout_page():
    """Defensive logout route — clears the session even on direct navigation."""
    await clear_session()
    ui.navigate.to("/login")


def random_token() -> str:
    """Helper exposed for tests / token generation."""
    return secrets.token_urlsafe(32)
