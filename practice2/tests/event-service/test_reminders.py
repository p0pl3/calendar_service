import pytest
from conftest import future_dt, past_dt
import app.messaging as messaging_module


async def create_test_event(client):
    resp = await client.post("/events/", json={
        "title": "Reminder Test Event",
        "start_time": future_dt(120),
    })
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_reminder_success(client):
    event_id = await create_test_event(client)
    resp = await client.post("/reminders/", json={
        "event_id": event_id,
        "remind_at": future_dt(60),
        "channels": ["email"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_id"] == event_id
    assert data["status"] == "pending"
    assert "email" in data["channels"]


@pytest.mark.asyncio
async def test_create_reminder_publishes_to_rabbitmq(client):
    event_id = await create_test_event(client)

    messaging_module._channel.default_exchange.publish.reset_mock()

    resp = await client.post("/reminders/", json={
        "event_id": event_id,
        "remind_at": future_dt(60),
        "channels": ["email"],
    })
    assert resp.status_code == 201
    messaging_module._channel.default_exchange.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_reminder_in_past(client):
    event_id = await create_test_event(client)
    resp = await client.post("/reminders/", json={
        "event_id": event_id,
        "remind_at": past_dt(10),
        "channels": ["email"],
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_reminder_event_not_found(client):
    resp = await client.post("/reminders/", json={
        "event_id": "00000000-0000-0000-0000-999999999999",
        "remind_at": future_dt(60),
        "channels": ["email"],
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_reminders_by_event(client):
    event_id = await create_test_event(client)
    await client.post("/reminders/", json={"event_id": event_id, "remind_at": future_dt(60), "channels": ["email"]})
    await client.post("/reminders/", json={"event_id": event_id, "remind_at": future_dt(120), "channels": ["email"]})

    resp = await client.get(f"/reminders/?event_id={event_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    for r in data:
        assert r["event_id"] == event_id


@pytest.mark.asyncio
async def test_get_reminder_by_id(client):
    event_id = await create_test_event(client)
    create_resp = await client.post("/reminders/", json={"event_id": event_id, "remind_at": future_dt(60), "channels": ["email"]})
    reminder_id = create_resp.json()["id"]

    resp = await client.get(f"/reminders/{reminder_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == reminder_id


@pytest.mark.asyncio
async def test_cancel_reminder(client):
    event_id = await create_test_event(client)
    create_resp = await client.post("/reminders/", json={"event_id": event_id, "remind_at": future_dt(60), "channels": ["email"]})
    reminder_id = create_resp.json()["id"]

    resp = await client.delete(f"/reminders/{reminder_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/reminders/{reminder_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_update_reminder(client):
    event_id = await create_test_event(client)
    create_resp = await client.post("/reminders/", json={"event_id": event_id, "remind_at": future_dt(60), "channels": ["email"]})
    reminder_id = create_resp.json()["id"]

    resp = await client.put(f"/reminders/{reminder_id}", json={"message": "Updated message"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Updated message"


@pytest.mark.asyncio
async def test_create_reminder_with_message(client):
    event_id = await create_test_event(client)
    resp = await client.post("/reminders/", json={
        "event_id": event_id,
        "remind_at": future_dt(60),
        "channels": ["email"],
        "message": "Don't forget!",
    })
    assert resp.status_code == 201
    assert resp.json()["message"] == "Don't forget!"
