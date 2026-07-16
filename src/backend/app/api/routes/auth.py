from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.auth.service import AuthServiceError, login_user, refresh_user, register_user
from app.auth.security import AuthenticationError
from app.database import get_database_session


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _error(error: ValueError) -> HTTPException:
    code = getattr(error, "code", "INVALID_CREDENTIALS")
    if code == "EMAIL_EXISTS":
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code)
    if code in {"INVALID_CREDENTIALS", "TOKEN_REVOKED", "INVALID_TOKEN"}:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=code)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    try:
        return await register_user(session, request)
    except AuthServiceError as error:
        raise _error(error) from None


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    try:
        return await login_user(session, request)
    except AuthenticationError as error:
        raise _error(error) from None


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_database_session),
) -> TokenResponse:
    try:
        return await refresh_user(session, request.refresh_token)
    except AuthenticationError as error:
        raise _error(error) from None
