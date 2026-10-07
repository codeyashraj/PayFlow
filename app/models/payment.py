from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class PaymentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING, server_default=PaymentStatus.PENDING, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    order: Mapped["Order"] = relationship(back_populates="payments")
    __table_args__ = (Index("ix_payments_order_status", "order_id", "status"),)
