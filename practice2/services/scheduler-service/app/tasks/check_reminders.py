import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.celery_app import celery_app
from app.database import get_db_session
from app.models.event import Event
from app.models.reminder import Reminder
from app.models.user import User
from app.publisher import publish_reminder_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.check_reminders.check_and_publish_due_reminders")
def check_and_publish_due_reminders() -> None:
    due_before = datetime.now(timezone.utc) + timedelta(seconds=70)
    logger.info("Checking reminders due before %s", due_before.isoformat())

    with get_db_session() as session:
        rows = session.execute(
            select(Reminder)
            .where(Reminder.status == "pending")
            .where(Reminder.remind_at <= due_before)
            .with_for_update(skip_locked=True)
        ).scalars().all()

        if not rows:
            logger.debug("No due reminders found")
            return

        for reminder in rows:
            event = session.get(Event, reminder.event_id)
            user = session.get(User, reminder.user_id)
            payload = {
                "reminder_id": reminder.id,
                "user_id": reminder.user_id,
                "event_id": reminder.event_id,
                "event_title": event.title if event else "Unknown",
                "event_start": event.start_time.isoformat() if event else None,
                "remind_at": reminder.remind_at.isoformat() if hasattr(reminder.remind_at, "isoformat") else str(reminder.remind_at),
                "channels": reminder.channels,
                "message": reminder.message,
                "user_email": user.email if user else None,
            }
            publish_reminder_sync(payload)
            reminder.status = "processing"

        session.commit()
        logger.info("Processed %d reminders", len(rows))
