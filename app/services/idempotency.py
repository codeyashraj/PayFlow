import asyncio, hashlib, json, logging
from uuid import UUID
from redis.exceptions import RedisError
from app.core.redis import redis
logger=logging.getLogger(__name__)
TTL=86400
LOCK_TTL=15

def record_key(user_id,key): return f"payflow:idempotency:payment:{user_id}:{key}"
def lock_key(user_id,key): return f"payflow:idempotency-lock:payment:{user_id}:{key}"
def fingerprint(order_id,simulate_success): return hashlib.sha256(f"{order_id}:{simulate_success}".encode()).hexdigest()
async def get(user_id,key):
    try:
        raw=await redis.get(record_key(user_id,key)); return json.loads(raw) if raw else None
    except RedisError: logger.exception("redis_idempotency_read_failed"); return None
async def claim(user_id,key):
    try: return bool(await redis.set(lock_key(user_id,key),"1",nx=True,ex=LOCK_TTL))
    except RedisError: logger.exception("redis_idempotency_claim_failed"); return None
async def store(user_id,key,payment_id,fp):
    try: await redis.set(record_key(user_id,key),json.dumps({"payment_id":str(payment_id),"fingerprint":fp}),ex=TTL); await redis.delete(lock_key(user_id,key))
    except RedisError: logger.exception("redis_idempotency_store_failed")
async def release(user_id,key):
    try: await redis.delete(lock_key(user_id,key))
    except RedisError: logger.exception("redis_idempotency_release_failed")
async def wait_for_record(user_id,key,attempts=10):
    for _ in range(attempts):
        rec=await get(user_id,key)
        if rec: return rec
        await asyncio.sleep(0.05)
    return None
