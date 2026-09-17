import jwt
import pytest
from pydantic import ValidationError

from app.auth import ALGORITHM, create_access_token, get_secret_key
from app.schemas import UserCreate


def test_registration_payload_does_not_accept_a_role():
    with pytest.raises(ValidationError):
        UserCreate(
            username="new_user",
            password="strong-password",
            role="admin",
        )


def test_password_must_have_at_least_eight_characters():
    with pytest.raises(ValidationError):
        UserCreate(username="new_user", password="short")


def test_secret_key_must_be_configured(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        get_secret_key()


def test_access_token_contains_the_username_but_not_the_role(monkeypatch):
    secret = "a-secure-test-secret-with-32-characters"
    monkeypatch.setenv("SECRET_KEY", secret)

    token = create_access_token(subject="student")
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

    assert payload["sub"] == "student"
    assert "role" not in payload
