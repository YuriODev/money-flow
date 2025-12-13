"""Authentication dependencies for FastAPI.

This module provides reusable authentication dependencies for protecting
API endpoints. Includes user authentication, role-based access control,
and optional authentication for public endpoints.

Dependencies:
    get_current_user: Require valid JWT token, return authenticated user.
    get_current_active_user: Same as above, but also verify user is active.
    get_optional_user: Return user if authenticated, None otherwise.
    require_admin: Require user has admin role.
    require_verified: Require user has verified email.

Example:
    >>> from src.auth.dependencies import get_current_active_user, require_admin
    >>>
    >>> @router.get("/profile")
    >>> async def get_profile(user: User = Depends(get_current_active_user)):
    ...     return {"email": user.email}
    >>>
    >>> @router.delete("/users/{id}")
    >>> async def delete_user(
    ...     id: str,
    ...     admin: User = Depends(require_admin),
    ... ):
    ...     # Only admins can delete users
    ...     ...
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import (
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenPayload,
    TokenType,
    decode_token,
)
from src.core.dependencies import get_db
from src.models.user import User, UserRole
from src.services.user_service import UserNotFoundError, UserService

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Security schemes
# auto_error=True: Return 401 if no token provided
# auto_error=False: Return None if no token (for optional auth)
security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the currently authenticated user.

    Extracts and validates JWT access token from Authorization header,
    then loads the user from the database.

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.

    Returns:
        Authenticated User model instance.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If user not found in database.

    Example:
        >>> @router.get("/me")
        >>> async def get_me(user: User = Depends(get_current_user)):
        ...     return {"id": user.id, "email": user.email}

    Security Notes:
        - Only accepts access tokens (not refresh tokens)
        - Does not verify user is active (use get_current_active_user for that)
        - Token validation is synchronous, user lookup is async
    """
    try:
        payload = decode_token(
            credentials.credentials,
            expected_type=TokenType.ACCESS,
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load user from database
    service = UserService(db)
    try:
        user = await service.get_by_id(payload.user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Get the currently authenticated user, ensuring they are active.

    Extends get_current_user to also verify the user account is active.
    Use this for most protected endpoints.

    Args:
        user: User from get_current_user dependency.

    Returns:
        Active User model instance.

    Raises:
        HTTPException 401: If user account is inactive.

    Example:
        >>> @router.post("/orders")
        >>> async def create_order(user: User = Depends(get_current_active_user)):
        ...     # Only active users can create orders
        ...     ...

    Security Notes:
        - Recommended for most protected endpoints
        - Prevents deactivated users from accessing resources
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get user if authenticated, otherwise return None.

    For endpoints that behave differently for authenticated vs anonymous users.
    Does not require authentication but will validate token if provided.

    Args:
        credentials: Optional bearer token from Authorization header.
        db: Database session.

    Returns:
        User if authenticated, None if not.

    Example:
        >>> @router.get("/products")
        >>> async def list_products(user: User | None = Depends(get_optional_user)):
        ...     if user:
        ...         # Show personalized recommendations
        ...         return get_personalized_products(user.id)
        ...     else:
        ...         # Show general products
        ...         return get_featured_products()

    Security Notes:
        - Returns None on any auth failure (doesn't raise)
        - Useful for public endpoints with optional personalization
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(
            credentials.credentials,
            expected_type=TokenType.ACCESS,
        )
    except TokenError:
        # Invalid token, treat as unauthenticated
        return None

    # Try to load user
    service = UserService(db)
    try:
        user = await service.get_by_id(payload.user_id)
        if user.is_active:
            return user
    except UserNotFoundError:
        pass

    return None


async def require_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Require the current user to be an admin.

    Use this dependency for admin-only endpoints.

    Args:
        user: Active user from get_current_active_user dependency.

    Returns:
        Admin User model instance.

    Raises:
        HTTPException 403: If user is not an admin.

    Example:
        >>> @router.delete("/users/{user_id}")
        >>> async def delete_user(
        ...     user_id: str,
        ...     admin: User = Depends(require_admin),
        ... ):
        ...     # Only admins can delete users
        ...     await user_service.delete(user_id)

    Security Notes:
        - Always use with get_current_active_user (already included)
        - Returns 403 Forbidden, not 401 Unauthorized
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_verified(
    user: User = Depends(get_current_active_user),
) -> User:
    """Require the current user to have a verified email.

    Use this for sensitive operations that require email verification.

    Args:
        user: Active user from get_current_active_user dependency.

    Returns:
        Verified User model instance.

    Raises:
        HTTPException 403: If user's email is not verified.

    Example:
        >>> @router.post("/payments")
        >>> async def create_payment(
        ...     user: User = Depends(require_verified),
        ... ):
        ...     # Only verified users can make payments
        ...     ...

    Security Notes:
        - Use for sensitive operations (payments, data export, etc.)
        - Returns 403 Forbidden with clear error message
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return user


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """Get decoded token payload without database lookup.

    Lightweight dependency when you only need token claims,
    not the full user object. Useful for performance-critical endpoints.

    Args:
        credentials: Bearer token from Authorization header.

    Returns:
        Decoded TokenPayload with user_id, email, etc.

    Raises:
        HTTPException 401: If token is invalid or expired.

    Example:
        >>> @router.get("/quick-check")
        >>> async def quick_check(payload: TokenPayload = Depends(get_token_payload)):
        ...     return {"user_id": payload.user_id}

    Security Notes:
        - Does NOT verify user still exists in database
        - Does NOT check if user is active
        - Use only when you trust token validity is sufficient
    """
    try:
        return decode_token(
            credentials.credentials,
            expected_type=TokenType.ACCESS,
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """Dependency class for checking user roles.

    Create instances to check for specific roles in endpoints.

    Attributes:
        allowed_roles: Set of roles that are allowed access.

    Example:
        >>> # Allow both users and admins
        >>> allow_users = RoleChecker([UserRole.USER, UserRole.ADMIN])
        >>>
        >>> @router.get("/dashboard")
        >>> async def dashboard(user: User = Depends(allow_users)):
        ...     return {"welcome": user.email}

    Security Notes:
        - Builds on get_current_active_user for base authentication
        - Flexible for multi-role requirements
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        """Initialize RoleChecker with allowed roles.

        Args:
            allowed_roles: List of UserRole values that are permitted.
        """
        self.allowed_roles = set(allowed_roles)

    async def __call__(
        self,
        user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if user has one of the allowed roles.

        Args:
            user: Active user from dependency.

        Returns:
            User if role is allowed.

        Raises:
            HTTPException 403: If user's role is not in allowed_roles.
        """
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role.value} not permitted for this operation",
            )
        return user
