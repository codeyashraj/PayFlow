from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payment):
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: UUID, *, for_update=False):
        stmt = select(Payment).where(Payment.id == payment_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_active_for_order(self, order_id: UUID, *, for_update=False):
        stmt = (
            select(Payment)
            .where(
                Payment.order_id == order_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING]),
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()
