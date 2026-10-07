from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id_for_user(
        self, order_id: UUID, user_id: UUID, *, for_update=False
    ):
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.user_id == user_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, order_id: UUID, *, for_update=False):
        stmt = select(Order).where(Order.id == order_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, order: Order):
        self.session.add(order)
        await self.session.flush()
        return order

    async def list_for_user(self, user_id, offset, limit):
        total = (
            await self.session.execute(
                select(func.count()).select_from(Order).where(Order.user_id == user_id)
            )
        ).scalar_one()
        rows = (
            (
                await self.session.execute(
                    select(Order)
                    .options(selectinload(Order.items))
                    .where(Order.user_id == user_id)
                    .order_by(Order.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return rows, total
