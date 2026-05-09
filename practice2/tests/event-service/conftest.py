import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/event-service'))

import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user_id
import app.messaging as messaging_module

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "00000000-0000-0000-0000-000000000002"


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    async def override_get_user_id():
        return TEST_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_user_id

    messaging_module._channel = AsyncMock()
    messaging_module._channel.default_exchange = AsyncMock()
    messaging_module._channel.default_exchange.publish = AsyncMock()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer fake-test-token"},
    ) as c:
        yield c

    app.dependency_overrides.clear()


def future_dt(minutes=60):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def past_dt(minutes=60):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
