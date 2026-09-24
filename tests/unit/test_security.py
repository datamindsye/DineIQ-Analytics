"""Tests for security, password hashing, and JWT tokens."""

from datetime import timedelta

import pytest

from packages.common.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    """Verify passwords can be hashed and accurately validated."""
    password = "SecretPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    """Verify JWT access tokens can be issued and decoded."""
    secret = "test-secret-key-32-characters-minimum-length"
    data = {"sub": "user_123", "role": "admin"}
    token = create_access_token(data, secret_key=secret, expires_delta=timedelta(minutes=15))
    payload = decode_access_token(token, secret_key=secret)
    assert payload["sub"] == "user_123"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_jwt_token_invalid_secret_fails():
    """Verify decoding with wrong secret fails."""
    secret = "test-secret-key-32-characters-minimum-length"
    token = create_access_token({"sub": "user_1"}, secret_key=secret)
    with pytest.raises(ValueError):
        decode_access_token(token, secret_key="wrong-secret-key-fails-decoding")
