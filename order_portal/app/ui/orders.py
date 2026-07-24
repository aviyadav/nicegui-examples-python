"""Orders table (PDF p.9-11).

A ``@ui.refreshable`` table of the latest orders with a per-row "Approve"
button. Approving flips PENDING -> PAID via ``OrderService.approve``, fires a
``ui.notify``, and refreshes the table (and any cards the caller passes in)
without a full page reload — the real-time UX described on PDF p.9.
"""
from __future__ import annotations

from nicegui import app, ui

from ..database import AsyncSessionLocal
from ..logging_conf import get_logger
from ..repositories import OrderRepository
from ..services import OrderService

logger = get_logger()


# Quasar column definitions — id / customer / status / amount from PDF p.10-11,
# plus an "actions" column for the Approve button.
#
# Note: the "amount" value is pre-formatted as a string in `_row_from` rather
# than using a Quasar `format` callable here. NiceGUI serializes the whole
# column spec to JSON for the browser, and Python lambdas are not JSON
# serializable (which raised "Type is not JSON serializable: function").
ORDER_COLUMNS = [
    {"name": "id", "label": "Order", "field": "id", "sortable": True, "align": "left"},
    {"name": "customer", "label": "Customer", "field": "customer", "sortable": True, "align": "left"},
    {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "left"},
    {"name": "amount", "label": "Amount", "field": "amount", "sortable": True, "align": "right"},
    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
]


def _row_from(order) -> dict:
    return {
        "id": order.id,
        "customer": order.customer,
        "status": order.status,
        # Pre-formatted string keeps the column spec JSON-serializable and
        # sorts correctly because Quasar compares strings lexicographically
        # only when the field type is text; numeric sorting on a "$1,234.56"
        # string would be wrong, so we keep a numeric `amount` for sorting and
        # render via a body-cell slot below.
        "amount": float(order.amount),
    }


def make_orders_section(*, on_change=None):
    """Build a refreshable orders table bound to the current page.

    Returns the refreshable callable; call it (``orders_table()``) to render.
    ``on_change`` is an optional sync callback invoked after an approval, so the
    dashboard cards can refresh too.
    """
    @ui.refreshable
    async def orders_table():
        async with AsyncSessionLocal() as session:
            rows = await OrderRepository(session).latest(100)

        table = ui.table(
            columns=ORDER_COLUMNS,
            rows=[_row_from(o) for o in rows],
            row_key="id",
            pagination=25,
        ).classes("w-full")

        # Format the amount column as currency on the client side. Done as a
        # Quasar body-cell slot (HTML/JS template) rather than a Python
        # `format` callable, because NiceGUI JSON-serializes the column spec
        # and functions are not JSON serializable.
        table.add_slot(
            "body-cell-amount",
            r'''
            <q-td :props="props">
                {{ new Intl.NumberFormat('en-US',
                    { style: 'currency', currency: 'USD' }).format(props.row.amount) }}
            </q-td>
            ''',
        )

        # Per-row Approve button rendered via a Quasar body-cell slot.
        table.add_slot(
            "body-cell-actions",
            r'''
            <q-td :props="props">
                <q-btn
                    flat dense color="primary" label="Approve"
                    :disable="props.row.status !== 'PENDING'"
                    @click="$parent.$emit('approve', props.row)" />
            </q-td>
            ''',
        )

        async def handle_approve(e):
            order_id = e.args["id"]
            actor = app.storage.user.get("current_user_email")
            async with AsyncSessionLocal() as session:
                await OrderService(OrderRepository(session)).approve(order_id, actor=actor)
            ui.notify(f"Order #{order_id} approved", color="positive")
            orders_table.refresh()
            if on_change is not None:
                on_change()

        table.on("approve", handle_approve)

    return orders_table
