import hashlib, hmac, time
from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models import User, Order, OrderItem, Payment, PaymentStatus, OrderStatus
from app.services.webhooks import WebhookService
from app.schemas.webhook import PaymentWebhookRequest


@pytest.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    yield Session
    await engine.dispose()


async def payment(Session, status=PaymentStatus.PROCESSING):
    async with Session() as s:
        u = User(email=f"{uuid4()}@example.com", password_hash="x")
        s.add(u)
        await s.flush()
        o = Order(
            user_id=u.id, total_amount=10, currency="USD", status=OrderStatus.PENDING
        )
        s.add(o)
        await s.flush()
        p = Payment(
            order_id=o.id,
            provider_payment_id=f"sim_{uuid4().hex}",
            amount=10,
            currency="USD",
            status=status,
        )
        s.add(p)
        await s.commit()
        return p.id, p.provider_payment_id, o.id


@pytest.mark.asyncio
async def test_success_webhook_updates_payment_and_order(db):
    pid, provider, oid = await payment(db)
    async with db() as s:
        svc = WebhookService(s)
        event, _ = await svc.ingest(
            PaymentWebhookRequest(
                event_id="evt-success",
                event_type="payment.succeeded",
                payment_id=str(pid),
                provider_payment_id=provider,
            )
        )
        await svc.process(event.id)
        p = await s.get(Payment, pid)
        o = await s.get(Order, oid)
        assert p.status == PaymentStatus.SUCCEEDED and o.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_failed_webhook_updates_payment_but_leaves_order_pending(db):
    pid, provider, oid = await payment(db)
    async with db() as s:
        svc = WebhookService(s)
        event, _ = await svc.ingest(
            PaymentWebhookRequest(
                event_id="evt-failed",
                event_type="payment.failed",
                payment_id=str(pid),
                provider_payment_id=provider,
            )
        )
        await svc.process(event.id)
        p = await s.get(Payment, pid)
        o = await s.get(Order, oid)
        assert p.status == PaymentStatus.FAILED and o.status == OrderStatus.PENDING


@pytest.mark.asyncio
async def test_duplicate_webhook_is_not_inserted_twice(db):
    pid, provider, _ = await payment(db)
    payload = PaymentWebhookRequest(
        event_id="evt-dup",
        event_type="payment.succeeded",
        payment_id=str(pid),
        provider_payment_id=provider,
    )
    async with db() as s:
        svc = WebhookService(s)
        first, new1 = await svc.ingest(payload)
        second, new2 = await svc.ingest(payload)
        assert new1 is True and new2 is False and first.id == second.id


@pytest.mark.asyncio
async def test_late_failed_webhook_cannot_overwrite_succeeded(db):
    pid, provider, oid = await payment(db, PaymentStatus.SUCCEEDED)
    async with db() as s:
        o = await s.get(Order, oid)
        o.status = OrderStatus.PAID
        await s.commit()
        svc = WebhookService(s)
        event, _ = await svc.ingest(
            PaymentWebhookRequest(
                event_id="evt-late",
                event_type="payment.failed",
                payment_id=str(pid),
                provider_payment_id=provider,
            )
        )
        await svc.process(event.id)
        p = await s.get(Payment, pid)
        assert p.status == PaymentStatus.SUCCEEDED
