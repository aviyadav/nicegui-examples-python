"""SQLAlchemy domain models.

``Order`` follows PDF p.6 verbatim (no UI code, no framework coupling).
``User`` is added to back the authentication layer shown on PDF p.13.

Status values: PENDING, PROCESSING, SHIPPED, PAID.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer: Mapped[str]
    amount: Mapped[float]
    status: Mapped[str]
    created_at: Mapped[datetime]


class User(Base):
    """Application user for the NiceGUI login flow (PDF p.13 + pragmatic ext)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    password_hash: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)
