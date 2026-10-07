from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.webhook_event import WebhookEvent
class WebhookRepository:
    def __init__(self,session: AsyncSession): self.session=session
    async def get_by_event_id(self,event_id:str): return (await self.session.execute(select(WebhookEvent).where(WebhookEvent.event_id==event_id))).scalar_one_or_none()
    async def get_by_id_for_update(self,event_id:UUID): return (await self.session.execute(select(WebhookEvent).where(WebhookEvent.id==event_id).with_for_update())).scalar_one_or_none()
