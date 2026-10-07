from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, Index, String, Text, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payment_id: Mapped[str] = mapped_column(String(255))
    payload: Mapped[str] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_webhook_events_processed", "processed"),)
