from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventUpdate


async def create_event(data: EventCreate, user_id: str, session: AsyncSession) -> Event:
    event = Event(
        id=str(uuid4()),
        user_id=user_id,
        title=data.title,
        description=data.description,
        start_time=data.start_time,
        end_time=data.end_time,
        location=data.location,
        is_all_day=data.is_all_day,
    )
    repo = EventRepository(session)
    return await repo.create(event)


async def get_events(
    user_id: str,
    session: AsyncSession,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Event]:
    repo = EventRepository(session)
    return await repo.get_by_user(user_id, from_date, to_date, skip, limit)


async def get_event(event_id: str, user_id: str, session: AsyncSession) -> Event:
    repo = EventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return event


async def update_event(event_id: str, data: EventUpdate, user_id: str, session: AsyncSession) -> Event:
    event = await get_event(event_id, user_id, session)
    repo = EventRepository(session)
    if data.title is not None:
        event.title = data.title
    if data.description is not None:
        event.description = data.description
    if data.start_time is not None:
        event.start_time = data.start_time
    if data.end_time is not None:
        event.end_time = data.end_time
    if data.location is not None:
        event.location = data.location
    if data.is_all_day is not None:
        event.is_all_day = data.is_all_day
    event.updated_at = datetime.now(timezone.utc)
    return await repo.update(event)


async def delete_event(event_id: str, user_id: str, session: AsyncSession) -> None:
    event = await get_event(event_id, user_id, session)
    repo = EventRepository(session)
    await repo.delete(event)
