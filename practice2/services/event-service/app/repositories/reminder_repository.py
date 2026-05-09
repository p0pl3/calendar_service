from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, reminder_id: str) -> Reminder | None:
        result = await self.session.execute(select(Reminder).where(Reminder.id == reminder_id))
        return result.scalar_one_or_none()

    async def get_by_event(self, event_id: str) -> list[Reminder]:
        result = await self.session.execute(
            select(Reminder).where(Reminder.event_id == event_id).order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: str, status: str | None = None) -> list[Reminder]:
        q = select(Reminder).where(Reminder.user_id == user_id)
        if status:
            q = q.where(Reminder.status == status)
        result = await self.session.execute(q.order_by(Reminder.remind_at))
        return list(result.scalars().all())

    async def get_pending_due(self, lookahead_seconds: int = 60) -> list[Reminder]:
        due_before = datetime.now(timezone.utc) + timedelta(seconds=lookahead_seconds)
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.status == "pending")
            .where(Reminder.remind_at <= due_before)
            .order_by(Reminder.remind_at)
        )
        return list(result.scalars().all())

    async def create(self, reminder: Reminder) -> Reminder:
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def update(self, reminder: Reminder) -> Reminder:
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder
