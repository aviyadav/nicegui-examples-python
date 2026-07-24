"""Admin-only users page (PDF p.13).

Gated behind ``require_user(admin=True)``. Non-admins see "Access denied" —
the same shape as the article's snippet, but backed by a real seeded users
table and the shared auth dependency.
"""
from __future__ import annotations

from nicegui import ui

from ..auth import do_logout, require_user
from ..database import AsyncSessionLocal
from ..repositories import UserRepository


@ui.page("/admin")
@require_user(admin=True)
async def admin_page():
    with ui.header().classes("items-center justify-between"):
        ui.label("Order Portal — Admin").classes("text-h6")
        ui.space()
        ui.button("Dashboard", on_click=lambda: ui.navigate.to("/")).props("flat")
        ui.button("Logout", on_click=do_logout).props("flat")

    with ui.column().classes("w-full q-pa-md q-gutter-md"):
        ui.label("Users").classes("text-h4")

        async with AsyncSessionLocal() as session:
            users = await UserRepository(session).all()

        ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id", "align": "left"},
                {"name": "email", "label": "Email", "field": "email", "align": "left"},
                {"name": "name", "label": "Name", "field": "name", "align": "left"},
                {"name": "is_admin", "label": "Admin", "field": "is_admin", "align": "left"},
            ],
            rows=[
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "is_admin": "Yes" if u.is_admin else "No",
                }
                for u in users
            ],
            row_key="id",
            pagination=25,
        ).classes("w-full")
