import pytest
from freezegun import freeze_time
from datetime import timedelta

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/user-service'))

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


def test_hash_password_returns_hash():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 20


def test_verify_password_correct():
    hashed = hash_password("correctpassword")
    assert verify_password("correctpassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_hash_is_different_each_time():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


def test_create_and_decode_token():
    token = create_access_token("user-123", "user@example.com")
    data = decode_token(token)
    assert data.user_id == "user-123"
    assert data.email == "user@example.com"


def test_decode_invalid_token():
    with pytest.raises(ValueError):
        decode_token("invalid.token.here")


def test_decode_tampered_token():
    token = create_access_token("user-123", "user@example.com")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(ValueError):
        decode_token(tampered)


@freeze_time("2024-01-01 12:00:00")
def test_create_token_has_expiry():
    from app.config import settings
    token = create_access_token("user-999", "test@test.com")
    from jose import jwt
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert "exp" in payload
    assert payload["sub"] == "user-999"
    assert payload["email"] == "test@test.com"
