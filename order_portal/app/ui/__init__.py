"""NiceGUI presentation layer (PDF p.8-11, p.13).

Importing this package imports each page module, which registers its
``@ui.page`` routes as a side effect. ``app.py`` imports this package so the
routes are wired before ``ui.run()``.
"""
from . import dashboard, orders, users  # noqa: F401  (side-effect: route registration)

__all__ = ["dashboard", "orders", "users"]
