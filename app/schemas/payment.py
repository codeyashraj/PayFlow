from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict
class PaymentCreateRequest(BaseModel):
    simulate_success: bool = True
class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; order_id: UUID; provider_payment_id: str | None; amount: Decimal; currency: str
    status: str; created_at: datetime; updated_at: datetime | None
