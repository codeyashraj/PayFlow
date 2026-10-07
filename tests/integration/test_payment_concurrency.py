import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.models import User, Order, Payment, OrderStatus, PaymentStatus
from app.repositories.orders import OrderRepository
from app.repositories.payments import PaymentRepository


@pytest.mark.asyncio
async def test_active_payment_is_visible_as_conflict_after_creation():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        u = User(email=f"{uuid4()}@example.com", password_hash="x")
        s.add(u)
        await s.flush()
        o = __import__("app.models", fromlist=["Order"]).Order(
            user_id=u.id, total_amount=10, currency="USD", status=OrderStatus.PENDING
        )
        s.add(o)
        await s.flush()
        p = Payment(
            order_id=o.id,
            provider_payment_id="sim_test",
            amount=10,
            currency="USD",
            status=PaymentStatus.PENDING,
        )
        s.add(p)
        await s.commit()
        assert (await PaymentRepository(s).get_active_for_order(o.id)).id == p.id
    await engine.dispose()
