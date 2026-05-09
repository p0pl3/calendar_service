import pytest


@pytest.mark.asyncio
async def test_get_me(client, auth_headers, registered_user):
    resp = await client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_me_username(client, auth_headers):
    resp = await client.put("/users/me", json={"username": "updatedname"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "updatedname"


@pytest.mark.asyncio
async def test_update_me_no_token(client):
    resp = await client.put("/users/me", json={"username": "hacker"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_me(client, db_session):
    resp = await client.post("/auth/register", json={
        "email": "todelete@example.com",
        "username": "deleteuser",
        "password": "password123",
    })
    assert resp.status_code == 201

    login_resp = await client.post("/auth/login", data={
        "username": "todelete@example.com",
        "password": "password123",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.delete("/users/me", headers=headers)
    assert resp.status_code == 204

    resp = await client.get("/users/me", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["service"] == "user-service"
