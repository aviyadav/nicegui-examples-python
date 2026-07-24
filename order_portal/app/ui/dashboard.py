"""Operations dashboard (PDF p.8).

``/`` shows the revenue + pending-orders cards and embeds the refreshable
orders table. The cards are themselves refreshable so approving an order
immediately bumps the revenue. Also wires the "Export monthly report" button
to the Celery task (PDF p.12-13).
"""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..auth import do_logout, get_current_user, require_user
from ..celery_app import generate_monthly_report
from ..database import AsyncSessionLocal
from ..repositories import OrderRepository
from ..services import DashboardService
from .orders import make_orders_section


@ui.page("/")
@require_user()
async def dashboard():
    user = await get_current_user()

    # ----- Header ---------------------------------------------------------- #
    with ui.header().classes("items-center justify-between"):
        ui.label("Order Portal").classes("text-h6")
        ui.space()
        ui.label(user.email if user else "").classes("text-subtitle2")
        ui.button("Logout", on_click=do_logout).props("flat")

    with ui.column().classes("w-full q-pa-md q-gutter-md"):
        ui.label("Operations Dashboard").classes("text-h4")

        # ----- KPI cards (refreshable so approvals update them live) ------- #
        @ui.refreshable
        async def kpi_cards():
            async with AsyncSessionLocal() as session:
                data = await DashboardService(OrderRepository(session)).dashboard()
            with ui.row().classes("w-full q-gutter-md"):
                with ui.card():
                    ui.label("Revenue")
                    ui.label(f"${data['revenue']:,.2f}").classes("text-h5 text-green")
                with ui.card():
                    ui.label("Pending Orders")
                    ui.label(str(data["pending"])).classes("text-h5")
                with ui.card():
                    ui.label("Orders Shown")
                    ui.label(str(len(data["orders"]))).classes("text-h5")

        await kpi_cards()

        # ----- Orders table ------------------------------------------------- #
        orders_table = make_orders_section(on_change=kpi_cards.refresh)
        await orders_table()

        # ----- Background export (Celery, PDF p.12-13) ---------------------- #
        with ui.row().classes("items-center q-gutter-sm"):
            ui.button(
                "Export monthly report",
                icon="download",
                on_click=lambda: enqueue_report(),
            ).props("color=secondary")
            ui.label(
                "Enqueues a Celery task; the CSV appears under ./reports/."
            ).classes("text-caption text-grey-7")

        def enqueue_report():
            month = datetime.utcnow().strftime("%Y-%m")
            generate_monthly_report.delay(month)
            ui.notify(f"Report generation started for {month}.")
