"""Unified API response schemas for consistent API responses.

This module provides standardized response envelope schemas for all API endpoints.
Ensures consistent response format across the entire API for better client-side handling.

Response Format:
    Success: {
        "success": true,
        "data": {...} or [...],
        "meta": {...},  # optional
        "message": "..."  # optional
    }

    Error: {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...}  # optional
        }
    }

    Paginated: {
        "success": true,
        "data": [...],
        "meta": {
            "pagination": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": true,
                "has_prev": false
            }
        }
    }
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for response data
T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for paginated responses.

    Attributes:
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_pages: Total number of pages.
        has_next: Whether there's a next page.
        has_prev: Whether there's a previous page.

    Example:
        >>> meta = PaginationMeta(total=100, page=1, page_size=20)
        >>> meta.total_pages
        5
    """

    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Items per page", ge=1, le=100)
    total_pages: int = Field(..., description="Total pages", ge=0)
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")

    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "PaginationMeta":
        """Create pagination meta from basic parameters.

        Args:
            total: Total number of items.
            page: Current page (1-indexed).
            page_size: Items per page.

        Returns:
            Populated PaginationMeta instance.
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class ResponseMeta(BaseModel):
    """Metadata for API responses.

    Attributes:
        timestamp: When the response was generated.
        request_id: Unique request identifier for tracing.
        pagination: Optional pagination info for list responses.

    Example:
        >>> meta = ResponseMeta(request_id="abc-123")
    """

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str | None = Field(default=None, description="Request ID for tracing")
    pagination: PaginationMeta | None = Field(default=None, description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Structured error detail for API errors.

    Attributes:
        code: Machine-readable error code.
        message: Human-readable error message.
        details: Optional additional error context.
        field: Optional field name for validation errors.

    Example:
        >>> error = ErrorDetail(
        ...     code="VALIDATION_ERROR",
        ...     message="Invalid email format",
        ...     field="email"
        ... )
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error context")
    field: str | None = Field(default=None, description="Field name for validation errors")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    This is the base response format for all API endpoints.
    All successful responses should use this format for consistency.

    Attributes:
        success: Whether the request was successful.
        data: The response payload.
        meta: Optional response metadata.
        message: Optional human-readable message.

    Example:
        >>> response = APIResponse(
        ...     success=True,
        ...     data={"id": "123", "name": "Netflix"},
        ...     message="Subscription created"
        ... )
    """

    success: bool = Field(default=True, description="Request success status")
    data: T | None = Field(default=None, description="Response payload")
    meta: ResponseMeta | None = Field(default=None, description="Response metadata")
    message: str | None = Field(default=None, description="Human-readable message")


class APIErrorResponse(BaseModel):
    """Standard API error response envelope.

    All error responses should use this format for consistency.

    Attributes:
        success: Always False for errors.
        error: Structured error details.
        meta: Optional response metadata.

    Example:
        >>> error = APIErrorResponse(
        ...     error=ErrorDetail(
        ...         code="NOT_FOUND",
        ...         message="Subscription not found"
        ...     )
        ... )
    """

    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")
    meta: ResponseMeta | None = Field(default=None, description="Response metadata")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response envelope.

    Used for list endpoints that support pagination.

    Attributes:
        success: Whether the request was successful.
        data: List of items for current page.
        meta: Response metadata including pagination.
        message: Optional human-readable message.

    Example:
        >>> response = PaginatedResponse(
        ...     data=[...],
        ...     meta=ResponseMeta(
        ...         pagination=PaginationMeta.create(total=100, page=1, page_size=20)
        ...     )
        ... )
    """

    success: bool = Field(default=True, description="Request success status")
    data: list[T] = Field(default_factory=list, description="List of items")
    meta: ResponseMeta = Field(..., description="Response metadata with pagination")
    message: str | None = Field(default=None, description="Human-readable message")


# ============================================================================
# Error Codes
# ============================================================================


class ErrorCode:
    """Standard error codes for API errors.

    Use these codes for consistent error handling across the API.
    """

    # Authentication errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # Authorization errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Not found errors (404)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Validation errors (400/422)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Conflict errors (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Business logic errors (400)
    BUSINESS_ERROR = "BUSINESS_ERROR"
    OPERATION_FAILED = "OPERATION_FAILED"


# ============================================================================
# Helper Functions
# ============================================================================


def success_response(
    data: Any = None,
    message: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a success response dictionary.

    Args:
        data: Response payload.
        message: Optional message.
        request_id: Optional request ID for tracing.

    Returns:
        Dict formatted as standard success response.

    Example:
        >>> response = success_response(
        ...     data={"id": "123"},
        ...     message="Created successfully"
        ... )
    """
    response: dict[str, Any] = {
        "success": True,
        "data": data,
    }
    if message:
        response["message"] = message
    if request_id:
        response["meta"] = {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()}
    return response


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    field: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create an error response dictionary.

    Args:
        code: Error code from ErrorCode class.
        message: Human-readable error message.
        details: Optional additional context.
        field: Optional field name for validation errors.
        request_id: Optional request ID for tracing.

    Returns:
        Dict formatted as standard error response.

    Example:
        >>> response = error_response(
        ...     code=ErrorCode.NOT_FOUND,
        ...     message="Subscription not found"
        ... )
    """
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    if field:
        error["field"] = field

    response: dict[str, Any] = {
        "success": False,
        "error": error,
    }
    if request_id:
        response["meta"] = {"request_id": request_id, "timestamp": datetime.utcnow().isoformat()}
    return response


def paginated_response(
    data: list[Any],
    total: int,
    page: int,
    page_size: int,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a paginated response dictionary.

    Args:
        data: List of items for current page.
        total: Total items across all pages.
        page: Current page number (1-indexed).
        page_size: Items per page.
        request_id: Optional request ID for tracing.

    Returns:
        Dict formatted as standard paginated response.

    Example:
        >>> response = paginated_response(
        ...     data=[...],
        ...     total=100,
        ...     page=1,
        ...     page_size=20
        ... )
    """
    pagination = PaginationMeta.create(total=total, page=page, page_size=page_size)
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": pagination.total_pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        },
    }
