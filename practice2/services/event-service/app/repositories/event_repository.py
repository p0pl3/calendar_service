from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, event_id: str) -> Event | None:
        result = await self.session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        q = select(Event).where(Event.user_id == user_id)
        if from_date:
            q = q.where(Event.start_time >= from_date)
        if to_date:
            q = q.where(Event.start_time <= to_date)
        q = q.order_by(Event.start_time).offset(skip).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def update(self, event: Event) -> Event:
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, event: Event) -> None:
        await self.session.delete(event)
        await self.session.commit()
