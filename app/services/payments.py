import logging
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    ConflictError,
    InvalidOrderStateError,
    InvalidPaymentStateError,
    NotFoundError,
)
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.repositories.orders import OrderRepository
from app.repositories.payments import PaymentRepository
from app.services import idempotency, order_cache
from app.workers.tasks import process_payment

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session):
        self.session = session
        self.orders = OrderRepository(session)
        self.payments = PaymentRepository(session)

    async def initiate_payment(self, user_id, order_id, payload, idempotency_key=None):
        fp = (
            idempotency.fingerprint(order_id, payload.simulate_success)
            if idempotency_key
            else None
        )
        if idempotency_key:
            rec = await idempotency.get(user_id, idempotency_key)
            if rec:
                if rec["fingerprint"] != fp:
                    raise ConflictError(
                        "Idempotency-Key was already used for a different request"
                    )
                existing = await self.payments.get_by_id(UUID(rec["payment_id"]))
                if existing:
                    return existing
            claimed = await idempotency.claim(user_id, idempotency_key)
            if claimed is False:
                rec = await idempotency.wait_for_record(user_id, idempotency_key)
                if rec and rec["fingerprint"] == fp:
                    existing = await self.payments.get_by_id(UUID(rec["payment_id"]))
                    if existing:
                        return existing
                raise ConflictError("Idempotency-Key is currently being processed")
        try:
            order = await self.orders.get_by_id_for_user(
                order_id, user_id, for_update=True
            )
            if not order:
                raise NotFoundError("Order not found")
            if order.status != OrderStatus.PENDING:
                raise InvalidOrderStateError(
                    "Order cannot be paid in its current state"
                )
            active = await self.payments.get_active_for_order(order_id, for_update=True)
            if active:
                if idempotency_key:
                    await idempotency.store(user_id, idempotency_key, active.id, fp)
                raise ConflictError("A payment is already in progress for this order")
            payment = Payment(
                order_id=order.id,
                provider_payment_id=f"sim_{uuid4().hex}",
                amount=order.total_amount,
                currency=order.currency,
                status=PaymentStatus.PENDING,
            )
            await self.payments.create(payment)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            if idempotency_key:
                await idempotency.release(user_id, idempotency_key)
            raise
        if idempotency_key:
            await idempotency.store(user_id, idempotency_key, payment.id, fp)
        try:
            process_payment.delay(str(payment.id), payload.simulate_success)
        except Exception:
            logger.exception(
                "payment_task_publish_failed", extra={"payment_id": str(payment.id)}
            )
            raise ConflictError(
                "Payment was created but processing could not be queued"
            )
        return payment

    async def get_payment(self, user_id, payment_id):
        payment = await self.payments.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        order = await self.orders.get_by_id_for_user(payment.order_id, user_id)
        if not order:
            raise NotFoundError("Payment not found")
        return payment
