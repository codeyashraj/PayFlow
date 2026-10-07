from fastapi import FastAPI
from app.api.routes import auth,health,orders,payments,users,webhooks
app=FastAPI(title="PayFlow",description="Event-driven payment and order processing backend",version="0.1.0")
for router in (health.router,auth.router,users.router,orders.router,payments.router,webhooks.router): app.include_router(router)
