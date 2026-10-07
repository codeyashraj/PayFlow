from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID):
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str):
        return (
            await self.session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

    async def create(self, user: User):
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
