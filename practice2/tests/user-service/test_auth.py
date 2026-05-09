import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, registered_user):
    resp = await client.post("/auth/register", json={
        "email": "testuser@example.com",
        "username": "another",
        "password": "password123",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    resp = await client.post("/auth/register", json={
        "email": "not-an-email",
        "username": "user",
        "password": "password123",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post("/auth/register", json={
        "email": "short@example.com",
        "username": "user",
        "password": "short",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_username(client):
    resp = await client.post("/auth/register", json={
        "email": "short@example.com",
        "username": "ab",
        "password": "password123",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, registered_user):
    resp = await client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, registered_user):
    resp = await client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", data={
        "username": "unknown@example.com",
        "password": "password123",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_logout_success(client, auth_headers):
    resp = await client.post("/auth/logout", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_logout_without_token(client):
    resp = await client.post("/auth/logout")
    assert resp.status_code == 401


