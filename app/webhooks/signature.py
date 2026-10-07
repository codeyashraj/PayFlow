import hashlib,hmac,time
from app.core.config import settings
MAX_AGE=300
def verify(webhook_id,timestamp,signature,body):
    try: ts=int(timestamp)
    except ValueError: return False
    if abs(time.time()-ts)>MAX_AGE: return False
    signed=f"{webhook_id}.{timestamp}.".encode()+body
    expected=hmac.new(settings.webhook_secret.encode(),signed,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature)
