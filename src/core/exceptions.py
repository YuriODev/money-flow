"""Custom exception hierarchy for Money Flow application.

This module provides a structured exception hierarchy that maps to HTTP status codes
and error codes for consistent error handling across the application.

Exception Hierarchy:
    MoneyFlowError (base)
    ├── ValidationError (422)
    │   ├── InvalidInputError
    │   └── MissingFieldError
    ├── AuthenticationError (401)
    │   ├── InvalidCredentialsError
    │   ├── TokenExpiredError
    │   └── TokenInvalidError
    ├── AuthorizationError (403)
    │   └── InsufficientPermissionsError
    ├── NotFoundError (404)
    │   ├── SubscriptionNotFoundError
    │   ├── UserNotFoundError
    │   └── CardNotFoundError
    ├── ConflictError (409)
    │   ├── DuplicateEntryError
    │   └── AlreadyExistsError
    ├── RateLimitError (429)
    ├── ExternalServiceError (502/503)
    │   ├── ClaudeAPIError
    │   ├── DatabaseConnectionError
    │   └── CacheConnectionError
    └── BusinessLogicError (400)
        └── OperationFailedError

Usage:
    from src.core.exceptions import SubscriptionNotFoundError

    async def get_subscription(subscription_id: str):
        sub = await service.get_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundError(subscription_id)
        return sub
"""

from typing import Any

from src.schemas.response import ErrorCode


class MoneyFlowError(Exception):
    """Base exception for all Money Flow application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and response formatting.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code from ErrorCode class.
        status_code: HTTP status code for the error response.
        details: Optional additional context for the error.

    Example:
        >>> raise MoneyFlowError(
        ...     message="Something went wrong",
        ...     error_code=ErrorCode.INTERNAL_ERROR,
        ...     status_code=500
        ... )
    """

    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code.
            status_code: HTTP status code.
            details: Optional additional context.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response.

        Returns:
            Dictionary with error details.
        """
        result = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# =============================================================================
# Validation Errors (422)
# =============================================================================


class ValidationError(MoneyFlowError):
    """Base exception for validation errors.

    Raised when input data fails validation checks.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details,
        )
        self.field = field
        if field:
            self.details["field"] = field


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(self, message: str = "Invalid input", field: str | None = None) -> None:
        super().__init__(message=message, field=field)
        self.error_code = ErrorCode.INVALID_INPUT


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field: str) -> None:
        super().__init__(
            message=f"Missing required field: {field}",
            field=field,
        )
        self.error_code = ErrorCode.MISSING_FIELD


class PasswordWeakError(ValidationError):
    """Raised when password doesn't meet strength requirements.

    Attributes:
        errors: List of specific validation failures.
    """

    def __init__(
        self,
        message: str = "Password does not meet requirements",
        errors: list[str] | None = None,
    ) -> None:
        details = {}
        if errors:
            details["errors"] = errors
        super().__init__(message=message, details=details if details else None)
        self.error_code = ErrorCode.INVALID_INPUT
        self.errors = errors or []


# =============================================================================
# Authentication Errors (401)
# =============================================================================


class AuthenticationError(MoneyFlowError):
    """Base exception for authentication errors.

    Raised when authentication fails or credentials are invalid.
    """

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message=message)
        self.error_code = ErrorCode.INVALID_CREDENTIALS


class TokenExpiredError(AuthenticationError):
    """Raised when an authentication token has expired."""

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message=message)
        self.error_code = ErrorCode.TOKEN_EXPIRED


class TokenInvalidError(AuthenticationError):
    """Raised when an authentication token is invalid."""

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message=message)
        self.error_code = ErrorCode.TOKEN_INVALID


class AccountLockedError(AuthenticationError):
    """Raised when an account is locked due to too many failed attempts.

    Attributes:
        locked_until: When the lockout expires (if known).
    """

    def __init__(
        self,
        message: str = "Account is locked",
        locked_until: str | None = None,
    ) -> None:
        details = {}
        if locked_until:
            details["locked_until"] = locked_until
        super().__init__(message=message, details=details if details else None)
        self.error_code = ErrorCode.ACCOUNT_LOCKED
        self.locked_until = locked_until


class AccountInactiveError(AuthenticationError):
    """Raised when attempting to authenticate an inactive account."""

    def __init__(self, message: str = "Account is inactive") -> None:
        super().__init__(message=message)
        self.error_code = ErrorCode.ACCOUNT_INACTIVE


# =============================================================================
# Authorization Errors (403)
# =============================================================================


class AuthorizationError(MoneyFlowError):
    """Base exception for authorization errors.

    Raised when user lacks permission to perform an action.
    """

    def __init__(
        self,
        message: str = "Access denied",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details,
        )


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""

    def __init__(self, required_permission: str | None = None) -> None:
        message = "Insufficient permissions"
        details = {}
        if required_permission:
            message = f"Insufficient permissions: {required_permission} required"
            details["required_permission"] = required_permission
        super().__init__(message=message, details=details)
        self.error_code = ErrorCode.INSUFFICIENT_PERMISSIONS


# =============================================================================
# Not Found Errors (404)
# =============================================================================


class NotFoundError(MoneyFlowError):
    """Base exception for resource not found errors.

    Raised when a requested resource does not exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details if details else None,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class SubscriptionNotFoundError(NotFoundError):
    """Raised when a subscription is not found."""

    def __init__(self, subscription_id: str) -> None:
        super().__init__(
            message=f"Subscription '{subscription_id}' not found",
            resource_type="subscription",
            resource_id=subscription_id,
        )


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""

    def __init__(self, user_id: str | None = None, email: str | None = None) -> None:
        identifier = user_id or email or "unknown"
        super().__init__(
            message=f"User '{identifier}' not found",
            resource_type="user",
            resource_id=identifier,
        )


class CardNotFoundError(NotFoundError):
    """Raised when a payment card is not found."""

    def __init__(self, card_id: str) -> None:
        super().__init__(
            message=f"Card '{card_id}' not found",
            resource_type="card",
            resource_id=card_id,
        )


# =============================================================================
# Conflict Errors (409)
# =============================================================================


class ConflictError(MoneyFlowError):
    """Base exception for conflict errors.

    Raised when an operation conflicts with existing state.
    """

    def __init__(
        self,
        message: str = "Operation conflicts with existing resource",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            details=details,
        )


class DuplicateEntryError(ConflictError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource_type: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource_type} '{identifier}' already exists",
            details={"resource_type": resource_type, "identifier": identifier},
        )
        self.error_code = ErrorCode.DUPLICATE_ENTRY


class AlreadyExistsError(ConflictError):
    """Raised when a resource already exists."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message=message)
        self.error_code = ErrorCode.ALREADY_EXISTS


class UserAlreadyExistsError(ConflictError):
    """Raised when attempting to create a user that already exists.

    Attributes:
        email: The email that already exists.
    """

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"User with email '{email}' already exists",
            details={"email": email},
        )
        self.error_code = ErrorCode.DUPLICATE_ENTRY
        self.email = email


# =============================================================================
# Rate Limit Errors (429)
# =============================================================================


class RateLimitError(MoneyFlowError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details if details else None,
        )
        self.retry_after = retry_after


# =============================================================================
# External Service Errors (502/503)
# =============================================================================


class ExternalServiceError(MoneyFlowError):
    """Base exception for external service errors.

    Raised when an external service (API, database, cache) fails.
    """

    def __init__(
        self,
        message: str = "External service error",
        service_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if service_name:
            details["service"] = service_name

        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details=details if details else None,
        )
        self.service_name = service_name


class ClaudeAPIError(ExternalServiceError):
    """Raised when Claude API request fails."""

    def __init__(
        self,
        message: str = "Claude API request failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            service_name="claude_api",
            details=details,
        )


class DatabaseConnectionError(ExternalServiceError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            service_name="database",
            details=details,
        )
        self.error_code = ErrorCode.DATABASE_ERROR


class CacheConnectionError(ExternalServiceError):
    """Raised when cache (Redis) connection fails."""

    def __init__(
        self,
        message: str = "Cache connection failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            service_name="redis",
            details=details,
        )


class VectorStoreError(ExternalServiceError):
    """Raised when vector store (Qdrant) operation fails."""

    def __init__(
        self,
        message: str = "Vector store operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            service_name="qdrant",
            details=details,
        )


# =============================================================================
# Business Logic Errors (400)
# =============================================================================


class BusinessLogicError(MoneyFlowError):
    """Base exception for business logic errors.

    Raised when a business rule is violated.
    """

    def __init__(
        self,
        message: str = "Business rule violation",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_ERROR,
            status_code=400,
            details=details,
        )


class OperationFailedError(BusinessLogicError):
    """Raised when an operation fails due to business rules."""

    def __init__(
        self,
        message: str = "Operation failed",
        reason: str | None = None,
    ) -> None:
        details = {}
        if reason:
            details["reason"] = reason
        super().__init__(message=message, details=details if details else None)
        self.error_code = ErrorCode.OPERATION_FAILED


class InsufficientBalanceError(BusinessLogicError):
    """Raised when there's insufficient balance for an operation."""

    def __init__(
        self,
        message: str = "Insufficient balance",
        required: str | None = None,
        available: str | None = None,
    ) -> None:
        details = {}
        if required:
            details["required"] = required
        if available:
            details["available"] = available
        super().__init__(message=message, details=details if details else None)


# =============================================================================
# Export all exceptions
# =============================================================================

__all__ = [
    # Base
    "MoneyFlowError",
    # Validation
    "ValidationError",
    "InvalidInputError",
    "MissingFieldError",
    "PasswordWeakError",
    # Authentication
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "AccountLockedError",
    "AccountInactiveError",
    # Authorization
    "AuthorizationError",
    "InsufficientPermissionsError",
    # Not Found
    "NotFoundError",
    "SubscriptionNotFoundError",
    "UserNotFoundError",
    "CardNotFoundError",
    # Conflict
    "ConflictError",
    "DuplicateEntryError",
    "AlreadyExistsError",
    "UserAlreadyExistsError",
    # Rate Limit
    "RateLimitError",
    # External Service
    "ExternalServiceError",
    "ClaudeAPIError",
    "DatabaseConnectionError",
    "CacheConnectionError",
    "VectorStoreError",
    # Business Logic
    "BusinessLogicError",
    "OperationFailedError",
    "InsufficientBalanceError",
]
