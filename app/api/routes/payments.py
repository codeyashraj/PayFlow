from fastapi import APIRouter, Header, HTTPException
from app.api.dependencies import CurrentUser, DBSession
from app.core.exceptions import ConflictError, InvalidOrderStateError, NotFoundError
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.services.payments import PaymentService

router = APIRouter(prefix="/api/v1", tags=["payments"])


@router.post(
    "/orders/{order_id}/payments", response_model=PaymentResponse, status_code=201
)
async def initiate(
    order_id: str,
    payload: PaymentCreateRequest,
    current_user: CurrentUser,
    session: DBSession,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    try:
        return await PaymentService(session).initiate_payment(
            current_user.id, __import__("uuid").UUID(order_id), payload, idempotency_key
        )
    except ValueError:
        raise HTTPException(422, "Invalid order ID")
    except NotFoundError:
        raise HTTPException(404, "Order not found")
    except (ConflictError, InvalidOrderStateError) as e:
        raise HTTPException(409, str(e))


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get(payment_id: str, current_user: CurrentUser, session: DBSession):
    try:
        return await PaymentService(session).get_payment(
            current_user.id, __import__("uuid").UUID(payment_id)
        )
    except (ValueError, NotFoundError):
        raise HTTPException(404, "Payment not found")
