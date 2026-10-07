import pytest
from app.services import rate_limit


class FakeRedis:
    def __init__(self):
        self.count = 0

    async def incr(self, key):
        self.count += 1
        return self.count

    async def expire(self, key, seconds):
        pass

    async def ttl(self, key):
        return 60


@pytest.mark.asyncio
async def test_rate_limit_allows_five_and_blocks_six(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(rate_limit, "redis", r)
    for _ in range(5):
        assert (await rate_limit.check_login("1.2.3.4"))[0]
    assert not (await rate_limit.check_login("1.2.3.4"))[0]
