"""Password and signed-token primitives used by the auth service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.db.enums import UserRole
from app.settings import settings


_PASSWORD_HASH = PasswordHash.recommended()
_ALGORITHM = "HS256"


class AuthenticationError(ValueError):
    """Stable authentication failure without sensitive details."""

    def __init__(self, code: str = "INVALID_TOKEN") -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class TokenClaims:
    subject: UUID
    role: UserRole
    token_type: str
    issued_at: datetime
    expires_at: datetime
    token_id: str


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("password must be at least eight characters")
    return _PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str) or not isinstance(password_hash, str):
        return False
    try:
        return _PASSWORD_HASH.verify(password, password_hash)
    except (TypeError, ValueError):
        return False


def _utc_now(now: datetime | None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _encode_token(
    user_id: UUID,
    role: UserRole,
    token_type: str,
    now: datetime | None,
    lifetime: timedelta,
) -> tuple[str, TokenClaims]:
    issued_at = _utc_now(now)
    expires_at = issued_at + lifetime
    claims = TokenClaims(
        subject=user_id,
        role=UserRole(role),
        token_type=token_type,
        issued_at=issued_at,
        expires_at=expires_at,
        token_id=str(uuid.uuid4()),
    )
    payload = {
        "sub": str(claims.subject),
        "role": claims.role.value,
        "token_type": claims.token_type,
        "iat": int(claims.issued_at.timestamp()),
        "exp": int(claims.expires_at.timestamp()),
        "jti": claims.token_id,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM), claims


def create_access_token(
    user_id: UUID,
    role: UserRole,
    *,
    now: datetime | None = None,
) -> str:
    token, _ = _encode_token(
        user_id,
        role,
        "access",
        now,
        timedelta(minutes=settings.jwt_access_ttl_minutes),
    )
    return token


def create_refresh_token(
    user_id: UUID,
    role: UserRole,
    *,
    now: datetime | None = None,
) -> tuple[str, TokenClaims]:
    return _encode_token(
        user_id,
        role,
        "refresh",
        now,
        timedelta(days=settings.jwt_refresh_ttl_days),
    )


def hash_refresh_token(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise ValueError("refresh token must not be empty")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _decode_token(token: str, now: datetime | None = None) -> TokenClaims:
    if not isinstance(token, str) or not token:
        raise AuthenticationError()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[_ALGORITHM],
            options={"verify_exp": False},
        )
        subject = UUID(str(payload["sub"]))
        role = UserRole(payload["role"])
        token_type = str(payload["token_type"])
        issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=timezone.utc)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        token_id = str(payload["jti"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError, OverflowError):
        raise AuthenticationError() from None

    if expires_at <= _utc_now(now) or token_type not in {"access", "refresh"}:
        raise AuthenticationError()
    return TokenClaims(subject, role, token_type, issued_at, expires_at, token_id)


def decode_access_token(token: str, *, now: datetime | None = None) -> TokenClaims:
    claims = _decode_token(token, now)
    if claims.token_type != "access":
        raise AuthenticationError()
    return claims


def decode_refresh_token(token: str, *, now: datetime | None = None) -> TokenClaims:
    claims = _decode_token(token, now)
    if claims.token_type != "refresh":
        raise AuthenticationError()
    return claims
