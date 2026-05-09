import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/notification-service'))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def make_message(**kwargs):
    base = {
        "reminder_id": "rem-001",
        "user_id": "usr-001",
        "event_id": "evt-001",
        "event_title": "Team Meeting",
        "event_start": "2024-06-15T09:00:00+00:00",
        "remind_at": "2024-06-15T08:45:00+00:00",
        "channels": ["email"],
        "message": "Don't forget!",
        "user_email": "user@example.com",
    }
    base.update(kwargs)
    return base
