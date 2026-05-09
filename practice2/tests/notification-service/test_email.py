import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/notification-service'))

from app.notifiers.email_notifier import send_email
from app.schemas.notification import ReminderMessage
from conftest import make_message


def make_reminder(**kwargs) -> ReminderMessage:
    return ReminderMessage(**make_message(**kwargs))


@pytest.mark.asyncio
async def test_send_email_success():
    reminder = make_reminder(channels=["email"])
    with patch("app.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock) as mock_send, \
         patch("app.notifiers.email_notifier.settings") as mock_settings:
        mock_settings.smtp_user = "bot@example.com"
        mock_settings.smtp_password = "secret"
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_from = "Calendar <bot@example.com>"
        await send_email(reminder)
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_no_credentials_skips():
    reminder = make_reminder(channels=["email"])
    with patch("app.notifiers.email_notifier.settings") as mock_settings:
        mock_settings.smtp_user = ""
        mock_settings.smtp_password = ""
        with patch("app.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(reminder)
            mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_email_no_address_skips():
    reminder = make_reminder(user_email=None)
    with patch("app.notifiers.email_notifier.settings") as mock_settings:
        mock_settings.smtp_user = "bot@example.com"
        mock_settings.smtp_password = "secret"
        with patch("app.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(reminder)
            mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_email_smtp_error_raises():
    import aiosmtplib
    reminder = make_reminder()
    with patch("app.notifiers.email_notifier.aiosmtplib.send", new_callable=AsyncMock, side_effect=aiosmtplib.SMTPException("Connection refused")), \
         patch("app.notifiers.email_notifier.settings") as mock_settings:
        mock_settings.smtp_user = "bot@example.com"
        mock_settings.smtp_password = "secret"
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_from = "bot@example.com"
        with pytest.raises(Exception):
            await send_email(reminder)
