"""Authentication API endpoints.

This module provides REST API endpoints for user authentication including
registration, login, token refresh, and profile management.

Endpoints:
    POST /auth/register - Create new user account
    POST /auth/login - Authenticate and get tokens
    POST /auth/refresh - Refresh access token
    GET /auth/me - Get current user profile
    PUT /auth/me - Update current user profile
    POST /auth/change-password - Change password

Note:
    This module intentionally does NOT use `from __future__ import annotations`
    because it causes FastAPI to misidentify Pydantic body parameters as query
    parameters during OpenAPI schema generation.

    Exceptions from services are allowed to propagate to the global exception
    handler which converts them to standardized error responses.
"""

import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_active_user
from src.core.config import settings
from src.core.dependencies import get_db
from src.models.user import User
from src.schemas.user import (
    LoginResponse,
    PasswordChangeRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from src.security.rate_limit import limiter, rate_limit_auth, rate_limit_get, rate_limit_write
from src.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
)
@limiter.limit(rate_limit_auth)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account.

    Creates a new user with validated email and password.
    Password is hashed before storage.

    Args:
        user_data: Registration data (email, password, optional name).
        db: Database session.

    Returns:
        Created user profile.

    Raises:
        UserAlreadyExistsError: If email already exists.
        PasswordStrengthError: If password doesn't meet requirements.

    Example:
        POST /auth/register
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
    """
    service = UserService(db)
    user = await service.create_user(user_data)
    logger.info(f"New user registered: {user.email}")
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user and return JWT tokens.",
)
@limiter.limit(rate_limit_auth)
async def login(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return tokens.

    Validates credentials and returns access/refresh token pair.
    Handles account lockout after too many failed attempts.

    Args:
        login_data: Login credentials (email, password).
        db: Database session.

    Returns:
        User profile and JWT tokens.

    Raises:
        InvalidCredentialsError: If credentials are invalid.
        AccountLockedError: If account is locked.
        AccountInactiveError: If account is inactive.

    Example:
        POST /auth/login
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    """
    service = UserService(db)
    user, access_token, refresh_token = await service.authenticate(
        email=login_data.email,
        password=login_data.password,
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token.",
)
@limiter.limit(rate_limit_auth)
async def refresh_token(
    request: Request,
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Validates refresh token and returns new token pair.
    Refresh tokens are rotated for security.

    Args:
        refresh_data: Refresh token request.
        db: Database session.

    Returns:
        New access and refresh tokens.

    Raises:
        TokenExpiredError: If refresh token is expired.
        TokenInvalidError: If refresh token is invalid.
        UserNotFoundError: If user no longer exists.
        AccountInactiveError: If account is inactive.

    Example:
        POST /auth/refresh
        {
            "refresh_token": "eyJ..."
        }
    """
    service = UserService(db)
    access_token, new_refresh_token = await service.refresh_tokens(refresh_data.refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get profile of currently authenticated user.",
)
@limiter.limit(rate_limit_get)
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user's profile.

    Returns the profile of the authenticated user.

    Args:
        current_user: Authenticated user from dependency.

    Returns:
        User profile.

    Example:
        GET /auth/me
        Authorization: Bearer eyJ...
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update profile of currently authenticated user.",
)
@limiter.limit(rate_limit_write)
async def update_me(
    request: Request,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update current user's profile.

    Updates profile fields for the authenticated user.

    Args:
        user_data: Profile update data.
        current_user: Authenticated user from dependency.
        db: Database session.

    Returns:
        Updated user profile.

    Example:
        PUT /auth/me
        Authorization: Bearer eyJ...
        {
            "full_name": "Jane Doe"
        }
    """
    service = UserService(db)
    user = await service.update_user(current_user.id, user_data)
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change password for currently authenticated user.",
)
@limiter.limit(rate_limit_auth)
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change current user's password.

    Verifies current password and updates to new password.

    Args:
        password_data: Current and new passwords.
        current_user: Authenticated user from dependency.
        db: Database session.

    Raises:
        InvalidCredentialsError: If current password is incorrect.
        PasswordStrengthError: If new password doesn't meet requirements.

    Example:
        POST /auth/change-password
        Authorization: Bearer eyJ...
        {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }
    """
    service = UserService(db)
    await service.change_password(
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )
