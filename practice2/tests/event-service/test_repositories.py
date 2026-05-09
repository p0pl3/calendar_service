import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/event-service'))

from app.models.event import Event
from app.models.reminder import Reminder
from app.repositories.event_repository import EventRepository
from app.repositories.reminder_repository import ReminderRepository


def make_event(user_id=None):
    return Event(
        id=str(uuid4()),
        user_id=user_id or str(uuid4()),
        title="Repo Test Event",
        start_time=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.mark.asyncio
async def test_event_repo_create_and_get(db_session):
    repo = EventRepository(db_session)
    uid = str(uuid4())
    event = make_event(uid)
    created = await repo.create(event)
    assert created.id == event.id

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.title == "Repo Test Event"


@pytest.mark.asyncio
async def test_event_repo_get_by_user(db_session):
    repo = EventRepository(db_session)
    uid = str(uuid4())
    e1 = make_event(uid)
    e2 = make_event(uid)
    e_other = make_event()

    await repo.create(e1)
    await repo.create(e2)
    await repo.create(e_other)

    results = await repo.get_by_user(uid)
    ids = [r.id for r in results]
    assert e1.id in ids
    assert e2.id in ids
    assert e_other.id not in ids


@pytest.mark.asyncio
async def test_event_repo_delete(db_session):
    repo = EventRepository(db_session)
    event = make_event()
    await repo.create(event)
    await repo.delete(event)

    fetched = await repo.get_by_id(event.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_event_repo_not_found(db_session):
    repo = EventRepository(db_session)
    result = await repo.get_by_id(str(uuid4()))
    assert result is None


@pytest.mark.asyncio
async def test_reminder_repo_get_pending_due(db_session):
    event_repo = EventRepository(db_session)
    uid = str(uuid4())
    event = make_event(uid)
    await event_repo.create(event)

    repo = ReminderRepository(db_session)
    now = datetime.now(timezone.utc)

    # due reminder
    due = Reminder(
        id=str(uuid4()),
        event_id=event.id,
        user_id=uid,
        remind_at=now + timedelta(seconds=30),
        channels=["email"],
        status="pending",
    )
    # future reminder (not due yet)
    future = Reminder(
        id=str(uuid4()),
        event_id=event.id,
        user_id=uid,
        remind_at=now + timedelta(hours=2),
        channels=["email"],
        status="pending",
    )
    await repo.create(due)
    await repo.create(future)

    results = await repo.get_pending_due(lookahead_seconds=60)
    ids = [r.id for r in results]
    assert due.id in ids
    assert future.id not in ids
