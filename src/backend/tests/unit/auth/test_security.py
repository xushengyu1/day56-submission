from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.auth.security import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.enums import UserRole


NOW = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def test_password_hash_is_not_plaintext_and_verifies() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_password_policy_rejects_short_passwords() -> None:
    with pytest.raises(ValueError, match="password"):
        hash_password("short")


def test_access_token_has_typed_claims_and_round_trips() -> None:
    token = create_access_token(USER_ID, UserRole.ADMIN, now=NOW)

    claims = decode_access_token(token, now=NOW)

    assert claims.subject == USER_ID
    assert claims.role is UserRole.ADMIN
    assert claims.token_type == "access"
    assert claims.expires_at > NOW


def test_access_token_rejects_expired_and_wrong_token_type() -> None:
    expired = create_access_token(
        USER_ID,
        UserRole.USER,
        now=NOW - timedelta(minutes=20),
    )
    refresh, _ = create_refresh_token(USER_ID, UserRole.USER, now=NOW)

    with pytest.raises(AuthenticationError, match="INVALID_TOKEN"):
        decode_access_token(expired, now=NOW)
    with pytest.raises(AuthenticationError, match="INVALID_TOKEN"):
        decode_access_token(refresh, now=NOW)


def test_refresh_token_is_random_and_only_digest_is_persisted() -> None:
    first, claims = create_refresh_token(USER_ID, UserRole.USER, now=NOW)
    second, _ = create_refresh_token(USER_ID, UserRole.USER, now=NOW)

    assert first != second
    assert claims.token_type == "refresh"
    assert hash_refresh_token(first) == hash_refresh_token(first)
    assert hash_refresh_token(first) != hash_refresh_token(second)
    assert first not in hash_refresh_token(first)


def test_invalid_access_token_does_not_echo_token() -> None:
    with pytest.raises(AuthenticationError) as error:
        decode_access_token("not-a-token", now=NOW)

    assert "not-a-token" not in str(error.value)
