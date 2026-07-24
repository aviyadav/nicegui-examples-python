"""Repository pattern (PDF p.6).

Repositories know about SQLAlchemy and the models — nothing about NiceGUI,
FastAPI, or the service layer. That isolation is the whole point: frameworks
come and go, domain logic shouldn't.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Order, User


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def latest(self, limit: int = 50):
        """Most recent orders, newest first (PDF p.6)."""
        stmt = (
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def by_id(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def update_status(self, order: Order, status: str) -> Order:
        order.status = status
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def all(self) -> list[User]:
        stmt = select(User).order_by(User.id.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
