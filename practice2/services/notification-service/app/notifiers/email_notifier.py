import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings
from app.schemas.notification import ReminderMessage

logger = logging.getLogger(__name__)


async def send_email(data: ReminderMessage) -> None:
    if not data.user_email:
        logger.warning("No email address for reminder_id=%s, skipping email", data.reminder_id)
        return
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured, skipping email")
        return

    body = (
        f"Reminder: {data.event_title}\n\n"
        f"{data.message or ''}\n\n"
        f"Event starts: {data.event_start or 'N/A'}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reminder: {data.event_title}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = data.user_email
    msg.attach(MIMEText(body, "plain"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info("Email sent to %s for reminder_id=%s", data.user_email, data.reminder_id)
    except Exception as exc:
        logger.error("Failed to send email for reminder_id=%s: %s", data.reminder_id, exc)
        raise
