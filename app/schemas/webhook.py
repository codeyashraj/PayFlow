from pydantic import BaseModel


class PaymentWebhookRequest(BaseModel):
    event_id: str
    event_type: str
    payment_id: str
    provider_payment_id: str
