from fastapi import APIRouter, Header, HTTPException, Request, status
from app.core.exceptions import InvalidPaymentStateError
from app.schemas.webhook import PaymentWebhookRequest
from app.services.webhooks import WebhookService, SUPPORTED
from app.webhooks.signature import verify
from app.workers.tasks import process_webhook_event
from app.core.database import SessionLocal

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/payment", status_code=202)
async def payment_webhook(
    request: Request,
    x_webhook_id: str = Header(...),
    x_webhook_timestamp: str = Header(...),
    x_webhook_signature: str = Header(...),
):
    body = await request.body()
    if not verify(x_webhook_id, x_webhook_timestamp, x_webhook_signature, body):
        raise HTTPException(401, "Invalid webhook signature")
    try:
        payload = PaymentWebhookRequest.model_validate_json(body)
    except Exception:
        raise HTTPException(422, "Invalid webhook payload")
    if payload.event_id != x_webhook_id:
        raise HTTPException(400, "Webhook ID does not match event ID")
    if payload.event_type not in SUPPORTED:
        raise HTTPException(400, "Unsupported webhook event")
    async with SessionLocal() as session:
        event, is_new = await WebhookService(session).ingest(payload)
    if is_new:
        process_webhook_event.delay(str(event.id))
    return {"status": "accepted", "event_id": payload.event_id}
