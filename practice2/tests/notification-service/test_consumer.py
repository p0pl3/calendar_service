import json
import pytest
from unittest.mock import AsyncMock, patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/notification-service'))

from app.main import handle_message
from conftest import make_message


@pytest.mark.asyncio
async def test_handle_email_channel():
    payload = make_message(channels=["email"])
    body = json.dumps(payload).encode()

    with patch("app.main.send_email", new_callable=AsyncMock) as mock_email:
        await handle_message(body)
        mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_handle_invalid_json_no_crash():
    body = b"this is not json at all"
    await handle_message(body)


@pytest.mark.asyncio
async def test_handle_missing_required_field():
    payload = {"reminder_id": "x", "channels": ["email"]}
    body = json.dumps(payload).encode()
    await handle_message(body)


@pytest.mark.asyncio
async def test_handle_no_channels():
    payload = make_message(channels=[])
    body = json.dumps(payload).encode()

    with patch("app.main.send_email", new_callable=AsyncMock) as mock_email:
        await handle_message(body)
        mock_email.assert_not_called()


@pytest.mark.asyncio
async def test_handle_notifier_exception_does_not_propagate():
    payload = make_message(channels=["email"])
    body = json.dumps(payload).encode()

    with patch("app.main.send_email", new_callable=AsyncMock, side_effect=Exception("SMTP down")):
        await handle_message(body)
