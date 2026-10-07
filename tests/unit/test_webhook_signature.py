import hashlib,hmac,time
from app.webhooks.signature import verify
from app.core.config import settings

def signed(wid,ts,body):
    return hmac.new(settings.webhook_secret.encode(),f"{wid}.{ts}.".encode()+body,hashlib.sha256).hexdigest()

def test_valid_signature():
    wid="evt-1"; ts=str(int(time.time())); body=b'{"ok":true}'
    assert verify(wid,ts,signed(wid,ts,body),body)

def test_invalid_signature():
    assert not verify("evt-1",str(int(time.time())),"bad",b"{}")

def test_stale_timestamp():
    ts=str(int(time.time())-301); body=b"{}"
    assert not verify("evt-1",ts,signed("evt-1",ts,body),body)
