import logging
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.messaging import publish_reminder_message
from app.models.reminder import Reminder
from app.repositories.event_repository import EventRepository
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.reminder import ReminderCreate, ReminderUpdate

logger = logging.getLogger(__name__)


async def _fetch_user_email(token: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.user_service_url}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json().get("email")
    except Exception as exc:
        logger.warning("Could not fetch user email from user-service: %s", exc)
    return None


async def _build_message(reminder: Reminder, session: AsyncSession, token: str | None = None) -> dict:
    event_repo = EventRepository(session)
    event = await event_repo.get_by_id(reminder.event_id)

    user_email = None
    if token:
        user_email = await _fetch_user_email(token)

    return {
        "reminder_id": reminder.id,
        "user_id": reminder.user_id,
        "event_id": reminder.event_id,
        "event_title": event.title if event else "Unknown Event",
        "event_start": event.start_time.isoformat() if event else None,
        "remind_at": reminder.remind_at.isoformat() if hasattr(reminder.remind_at, "isoformat") else str(reminder.remind_at),
        "channels": reminder.channels,
        "message": reminder.message,
        "user_email": user_email,
    }


async def create_reminder(data: ReminderCreate, user_id: str, session: AsyncSession, token: str | None = None) -> Reminder:
    event_repo = EventRepository(session)
    event = await event_repo.get_by_id(data.event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    reminder = Reminder(
        id=str(uuid4()),
        event_id=data.event_id,
        user_id=user_id,
        remind_at=data.remind_at,
        channels=[ch.value for ch in data.channels],
        message=data.message,
        status="pending",
    )
    repo = ReminderRepository(session)
    reminder = await repo.create(reminder)

    try:
        payload = await _build_message(reminder, session, token)
        await publish_reminder_message(payload)
    except Exception as exc:
        logger.warning("Failed to publish reminder message: %s", exc)

    return reminder


async def get_reminders(user_id: str, event_id: str | None, session: AsyncSession) -> list[Reminder]:
    repo = ReminderRepository(session)
    if event_id:
        reminders = await repo.get_by_event(event_id)
        return [r for r in reminders if r.user_id == user_id]
    return await repo.get_by_user(user_id)


async def get_reminder(reminder_id: str, user_id: str, session: AsyncSession) -> Reminder:
    repo = ReminderRepository(session)
    reminder = await repo.get_by_id(reminder_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    if reminder.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return reminder


async def update_reminder(
    reminder_id: str, data: ReminderUpdate, user_id: str, session: AsyncSession, token: str | None = None
) -> Reminder:
    reminder = await get_reminder(reminder_id, user_id, session)
    repo = ReminderRepository(session)
    if data.remind_at is not None:
        reminder.remind_at = data.remind_at
    if data.channels is not None:
        reminder.channels = [ch.value for ch in data.channels]
    if data.message is not None:
        reminder.message = data.message
    reminder.updated_at = datetime.now(timezone.utc)
    reminder = await repo.update(reminder)

    try:
        payload = await _build_message(reminder, session, token)
        await publish_reminder_message(payload)
    except Exception as exc:
        logger.warning("Failed to re-publish reminder message: %s", exc)

    return reminder


async def cancel_reminder(reminder_id: str, user_id: str, session: AsyncSession) -> None:
    reminder = await get_reminder(reminder_id, user_id, session)
    reminder.status = "cancelled"
    reminder.updated_at = datetime.now(timezone.utc)
    repo = ReminderRepository(session)
    await repo.update(reminder)
