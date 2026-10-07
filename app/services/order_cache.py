import json, logging
from uuid import UUID
from redis.exceptions import RedisError
from app.core.redis import redis
logger=logging.getLogger(__name__)
TTL=60

def key(user_id:UUID,order_id:UUID)->str: return f"payflow:cache:order:{user_id}:{order_id}"
async def get(user_id,order_id):
    try:
        raw = await redis.get(key(user_id, order_id))
        return json.loads(raw) if raw else None
    except RedisError: logger.exception("redis_cache_read_failed",extra={"order_id":str(order_id)}); return None
async def set(user_id,order_id,data):
    try: await redis.set(key(user_id,order_id),json.dumps(data),ex=TTL)
    except RedisError: logger.exception("redis_cache_write_failed",extra={"order_id":str(order_id)})
async def invalidate(user_id,order_id):
    try: await redis.delete(key(user_id,order_id))
    except RedisError: logger.exception("redis_cache_invalidation_failed",extra={"order_id":str(order_id)})
