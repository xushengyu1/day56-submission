from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.auth.models import User
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.auth.service import login_user, refresh_user, register_user
from app.database import get_database_session


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    return await register_user(session, request)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    return await login_user(session, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    return await refresh_user(session, request.refresh_token)


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(user)
