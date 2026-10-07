import json, logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import InvalidPaymentStateError, NotFoundError
from app.models.payment import PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.repositories.payments import PaymentRepository
from app.repositories.webhooks import WebhookRepository
from app.services import order_cache

logger = logging.getLogger(__name__)
SUPPORTED = {"payment.succeeded", "payment.failed", "payment.refunded"}


class WebhookService:
    def __init__(self, session):
        self.session = session
        self.events = WebhookRepository(session)
        self.payments = PaymentRepository(session)

    async def ingest(self, payload):
        existing = await self.events.get_by_event_id(payload.event_id)
        if existing:
            return existing, False
        event = WebhookEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            payment_id=payload.payment_id,
            payload=payload.model_dump_json(),
        )
        self.session.add(event)
        try:
            await self.session.commit()
            await self.session.refresh(event)
            return event, True
        except IntegrityError:
            await self.session.rollback()
            existing = await self.events.get_by_event_id(payload.event_id)
            return existing, False

    async def process(self, event_id):
        event = await self.events.get_by_id_for_update(event_id)
        if not event or event.processed:
            return
        payload = json.loads(event.payload)
        payment = await self.payments.get_by_id(
            UUID(payload["payment_id"]), for_update=True
        )
        if not payment:
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.warning(
                "webhook_unknown_payment", extra={"event_id": event.event_id}
            )
            return
        if payment.provider_payment_id != payload["provider_payment_id"]:
            raise InvalidPaymentStateError("Provider payment ID mismatch")
        new_status = {
            "payment.succeeded": PaymentStatus.SUCCEEDED,
            "payment.failed": PaymentStatus.FAILED,
            "payment.refunded": PaymentStatus.REFUNDED,
        }.get(event.event_type)
        if not new_status:
            raise InvalidPaymentStateError("Unsupported webhook event")
        current = payment.status
        allowed = {
            PaymentStatus.PENDING: {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED},
            PaymentStatus.PROCESSING: {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED},
            PaymentStatus.SUCCEEDED: {PaymentStatus.REFUNDED},
            PaymentStatus.FAILED: set(),
            PaymentStatus.REFUNDED: set(),
        }
        if current != new_status:
            if new_status not in allowed.get(current, set()):
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)
                await self.session.commit()
                logger.info(
                    "webhook_state_ignored",
                    extra={"event_id": event.event_id, "payment_id": str(payment.id)},
                )
                return
            payment.status = new_status
        from app.repositories.orders import OrderRepository

        order = await OrderRepository(self.session).get_by_id(
            payment.order_id, for_update=True
        )
        if new_status == PaymentStatus.SUCCEEDED:
            order.status = "PAID"
        elif new_status == PaymentStatus.REFUNDED and order.status == "PAID":
            order.status = "CANCELLED"
        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await order_cache.invalidate(order.user_id, order.id)
