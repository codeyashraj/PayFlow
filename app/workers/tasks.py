import asyncio,logging
from sqlalchemy.exc import OperationalError
from app.core.database import SessionLocal,engine
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.repositories.orders import OrderRepository
from app.repositories.payments import PaymentRepository
from app.services import order_cache
from app.workers.celery_app import celery_app
logger=logging.getLogger(__name__)
async def _process(payment_id,simulate_success):
    async with SessionLocal() as session:
        payment=await PaymentRepository(session).get_by_id(__import__('uuid').UUID(payment_id),for_update=True)
        if not payment: logger.warning("payment_not_found",extra={"payment_id":payment_id}); return
        if payment.status in {PaymentStatus.SUCCEEDED,PaymentStatus.FAILED,PaymentStatus.REFUNDED}: return
        order=await OrderRepository(session).get_by_id(payment.order_id,for_update=True)
        if not order or order.status==OrderStatus.CANCELLED: return
        payment.status=PaymentStatus.PROCESSING
        await session.flush()
        payment.status=PaymentStatus.SUCCEEDED if simulate_success else PaymentStatus.FAILED
        if payment.status==PaymentStatus.SUCCEEDED: order.status=OrderStatus.PAID
        await session.commit()
        await order_cache.invalidate(order.user_id,order.id)
        logger.info("payment_processed",extra={"payment_id":payment_id,"status":payment.status})
@celery_app.task(bind=True,autoretry_for=(OperationalError,),retry_backoff=True,retry_backoff_max=60,retry_jitter=True,max_retries=3)
def process_payment(self,payment_id:str,simulate_success:bool=True):
    logger.info("payment_task_started",extra={"payment_id":payment_id})
    return asyncio.run(_process(payment_id,simulate_success))
@celery_app.task(bind=True,autoretry_for=(OperationalError,),retry_backoff=True,retry_backoff_max=60,retry_jitter=True,max_retries=3)
def process_webhook_event(self,event_id:str):
    from app.services.webhooks import WebhookService
    async def run():
        async with SessionLocal() as session: await WebhookService(session).process(__import__('uuid').UUID(event_id))
    return asyncio.run(run())
