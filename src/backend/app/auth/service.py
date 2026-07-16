from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.auth.security import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.enums import UserRole


_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing")


class AuthServiceError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _issue_tokens(session: AsyncSession, user: User) -> TokenResponse:
    now = _now()
    access_token = create_access_token(user.id, user.role, now=now)
    refresh_token, refresh_claims = create_refresh_token(user.id, user.role, now=now)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_claims.expires_at,
        )
    )
    await session.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserPublic.model_validate(user),
    )


async def register_user(session: AsyncSession, request: RegisterRequest) -> TokenResponse:
    existing = await session.scalar(select(User).where(User.email == request.email))
    if existing is not None:
        raise AuthServiceError("EMAIL_EXISTS")

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        role=UserRole.USER,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise AuthServiceError("EMAIL_EXISTS") from None
    return await _issue_tokens(session, user)


async def login_user(session: AsyncSession, request: LoginRequest) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == request.email))
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    if user is None or not verify_password(request.password, password_hash):
        raise AuthenticationError("INVALID_CREDENTIALS")
    return await _issue_tokens(session, user)


async def refresh_user(session: AsyncSession, refresh_token: str) -> TokenResponse:
    claims = decode_refresh_token(refresh_token)
    token_hash = hash_refresh_token(refresh_token)
    stored = await session.scalar(
        select(RefreshToken).where(
            RefreshToken.user_id == claims.subject,
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > _now(),
        ).with_for_update()
    )
    if stored is None:
        raise AuthenticationError("TOKEN_REVOKED")

    user = await session.get(User, claims.subject)
    if user is None:
        raise AuthenticationError("TOKEN_REVOKED")
    stored.revoked_at = _now()
    return await _issue_tokens(session, user)
