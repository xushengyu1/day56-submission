from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.security import AuthenticationError, TokenClaims, decode_access_token
from app.database import get_database_session


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise AuthenticationError()
    scheme, separator, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not separator or not token.strip():
        raise AuthenticationError()
    return token.strip()


async def get_current_claims(
    authorization: str | None = Header(default=None),
) -> TokenClaims:
    return decode_access_token(extract_bearer_token(authorization))


async def get_current_user(
    claims: TokenClaims = Depends(get_current_claims),
    session: AsyncSession = Depends(get_database_session),
) -> User:
    user = await session.scalar(select(User).where(User.id == claims.subject))
    if user is None or user.role is not claims.role:
        raise AuthenticationError("INVALID_TOKEN")
    return user


CurrentUser = Depends(get_current_user)
