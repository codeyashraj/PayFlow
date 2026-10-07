from app.workers.celery_app import celery_app
from app.workers.tasks import process_payment


def test_celery_uses_rabbitmq_and_retry_safe_config():
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert process_payment.max_retries == 3
    assert process_payment.retry_backoff is True
