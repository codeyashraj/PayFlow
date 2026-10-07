import pytest
from app.services import order_cache,idempotency

class FakeRedis:
    def __init__(self): self.data={}
    async def get(self,k): return self.data.get(k)
    async def set(self,k,v,**kwargs):
        if kwargs.get("nx") and k in self.data: return False
        self.data[k]=v; return True
    async def delete(self,k): self.data.pop(k,None)
    async def expire(self,k,v): pass
    async def incr(self,k): self.data[k]=int(self.data.get(k,0))+1; return self.data[k]
    async def ttl(self,k): return 60

@pytest.mark.asyncio
async def test_cache_miss_then_hit(monkeypatch):
    r=FakeRedis(); monkeypatch.setattr(order_cache,"redis",r)
    assert await order_cache.get("u","o") is None
    await order_cache.set("u","o",{"id":"o"})
    assert await order_cache.get("u","o")=={"id":"o"}

@pytest.mark.asyncio
async def test_idempotency_claim_is_atomic(monkeypatch):
    r=FakeRedis(); monkeypatch.setattr(idempotency,"redis",r)
    assert await idempotency.claim("u","k") is True
    assert await idempotency.claim("u","k") is False
