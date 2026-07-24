"""order_portal — a NiceGUI internal business app (order operations portal).

Implements the architecture described in
"Why NiceGUI Is Perfect for Internal Business Apps":

    UI -> Service -> Repository -> PostgreSQL

Layered so the domain (models, repositories, services) knows nothing
about NiceGUI, and the UI is just another presentation layer.
"""

__version__ = "0.1.0"
