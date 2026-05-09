import pytest
from datetime import datetime, timezone, timedelta
from conftest import future_dt, past_dt


def event_payload(**kwargs):
    base = {
        "title": "Test Event",
        "start_time": future_dt(30),
        "description": "A test event",
    }
    base.update(kwargs)
    return base


@pytest.mark.asyncio
async def test_create_event_success(client):
    resp = await client.post("/events/", json=event_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Event"
    assert "id" in data
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_create_event_with_end_time(client):
    resp = await client.post("/events/", json=event_payload(
        start_time=future_dt(30),
        end_time=future_dt(90),
    ))
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_event_end_before_start(client):
    resp = await client.post("/events/", json={
        "title": "Bad Event",
        "start_time": future_dt(90),
        "end_time": future_dt(30),
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_event_empty_title(client):
    resp = await client.post("/events/", json={
        "title": "",
        "start_time": future_dt(30),
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_events(client):
    await client.post("/events/", json=event_payload(title="Event A"))
    await client.post("/events/", json=event_payload(title="Event B"))

    resp = await client.get("/events/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    titles = [e["title"] for e in data]
    assert "Event A" in titles
    assert "Event B" in titles


@pytest.mark.asyncio
async def test_get_event_by_id(client):
    create_resp = await client.post("/events/", json=event_payload(title="Fetch Me"))
    event_id = create_resp.json()["id"]

    resp = await client.get(f"/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Fetch Me"


@pytest.mark.asyncio
async def test_get_event_not_found(client):
    resp = await client.get("/events/00000000-0000-0000-0000-999999999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_event(client):
    create_resp = await client.post("/events/", json=event_payload(title="Original"))
    event_id = create_resp.json()["id"]

    resp = await client.put(f"/events/{event_id}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_event(client):
    create_resp = await client.post("/events/", json=event_payload(title="ToDelete"))
    event_id = create_resp.json()["id"]

    resp = await client.delete(f"/events/{event_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/events/{event_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "event-service"
