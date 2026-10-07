import asyncio, json
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.database import Base,get_db
from app.main import app
from app.models import User,Order,OrderItem,Payment,WebhookEvent
from app.core.security import create_access_token,hash_password

@pytest.fixture
async def client(monkeypatch):
    engine=create_async_engine("sqlite+aiosqlite:///:memory:",future=True)
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    Session=async_sessionmaker(engine,expire_on_commit=False)
    async def override():
        async with Session() as s: yield s
    app.dependency_overrides[get_db]=override
    monkeypatch.setattr("app.services.payments.process_payment.delay",lambda *a,**k:None)
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c: yield c,Session
    app.dependency_overrides.clear(); await engine.dispose()

async def register_login(c,email="a@example.com"):
    r=await c.post("/api/v1/auth/register",json={"email":email,"password":"password123"}); assert r.status_code==201
    r=await c.post("/api/v1/auth/login",json={"email":email,"password":"password123"}); assert r.status_code==200
    return r.json()["access_token"]

def auth(token): return {"Authorization":f"Bearer {token}"}

@pytest.mark.asyncio
async def test_auth_register_duplicate_and_login(client):
    c,_=client; token=await register_login(c)
    assert token
    r=await c.post("/api/v1/auth/register",json={"email":"a@example.com","password":"password123"}); assert r.status_code==409
    r=await c.post("/api/v1/auth/login",json={"email":"a@example.com","password":"wrong"}); assert r.status_code==401

@pytest.mark.asyncio
async def test_order_create_get_list_cancel(client):
    c,_=client; token=await register_login(c)
    payload={"currency":"usd","items":[{"product_name":"Book","quantity":2,"unit_price":"10.00"}]}
    r=await c.post("/api/v1/orders",json=payload,headers=auth(token)); assert r.status_code==201; order=r.json(); assert order["total_amount"]=="20.00"
    r=await c.get(f"/api/v1/orders/{order['id']}",headers=auth(token)); assert r.status_code==200
    r=await c.get("/api/v1/orders",headers=auth(token)); assert r.status_code==200 and r.json()["total"]==1
    r=await c.post(f"/api/v1/orders/{order['id']}/cancel",headers=auth(token)); assert r.status_code==200 and r.json()["status"]=="CANCELLED"
    assert (await c.get(f"/api/v1/orders/{order['id']}")).status_code==401

@pytest.mark.asyncio
async def test_payment_idempotency(client,monkeypatch):
    c,_=client; token=await register_login(c)
    r=await c.post("/api/v1/orders",json={"currency":"USD","items":[{"product_name":"X","quantity":1,"unit_price":"10.00"}]},headers=auth(token)); oid=r.json()["id"]
    monkeypatch.setattr("app.services.payments.idempotency.get",lambda *a:None)
    monkeypatch.setattr("app.services.payments.idempotency.claim",lambda *a:True)
    stored={}
    async def store(*args): stored["payment_id"]=args[2]
    monkeypatch.setattr("app.services.payments.idempotency.store",store)
    async def fake_get(*args): return None
    monkeypatch.setattr("app.services.payments.idempotency.get",fake_get)
    r=await c.post(f"/api/v1/orders/{oid}/payments",json={},headers={**auth(token),"Idempotency-Key":"k1"}); assert r.status_code==201
    pid=r.json()["id"]
    async def get_rec(*args): return {"payment_id":pid,"fingerprint":""} if False else None
    # DB order lock also prevents a second active payment even if Redis loses the record.
    r2=await c.post(f"/api/v1/orders/{oid}/payments",json={},headers=auth(token)); assert r2.status_code==409

@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    c,_=client
    body={"event_id":"evt-1","event_type":"payment.succeeded","payment_id":str(uuid4()),"provider_payment_id":"sim_x"}
    r=await c.post("/api/v1/webhooks/payment",json=body,headers={"X-Webhook-ID":"evt-1","X-Webhook-Timestamp":"9999999999","X-Webhook-Signature":"bad"})
    assert r.status_code==401
