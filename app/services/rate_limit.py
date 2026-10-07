import logging
from redis.exceptions import RedisError
from app.core.redis import redis
logger=logging.getLogger(__name__)
LIMIT=5; WINDOW=60
async def check_login(ip:str)->tuple[bool,int]:
    key=f"payflow:rate-limit:login:{ip}"
    try:
        count=await redis.incr(key)
        if count==1: await redis.expire(key,WINDOW)
        ttl=await redis.ttl(key)
        return count<=LIMIT,max(ttl,1)
    except RedisError:
        logger.exception("redis_rate_limit_failed",extra={"ip":ip}); return True,0
