"""Global exception handler for standardized error responses.

This module provides exception handlers that convert all errors to the
standard API error response format defined in schemas/response.py.

This ensures consistent error responses across all endpoints regardless
of where the error originates.
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.schemas.response import ErrorCode, error_response

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from request state if available."""
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with standard error format.

    Converts HTTPException to standardized error response.
    Handles both string and dict detail formats.
    """
    request_id = _get_request_id(request)

    # Map status codes to error codes
    status_code_map = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = status_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Handle detail that might be a dict or string
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("errors") or exc.detail.get("details")
    else:
        message = str(exc.detail)
        details = None

    response = error_response(
        code=error_code,
        message=message,
        details={"errors": details} if details else None,
        request_id=request_id,
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def starlette_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPException with standard error format."""
    request_id = _get_request_id(request)

    status_code_map = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.INVALID_INPUT,
        500: ErrorCode.INTERNAL_ERROR,
    }

    error_code = status_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    response = error_response(
        code=error_code,
        message=str(exc.detail),
        request_id=request_id,
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with standard error format.

    Converts validation errors to a structured format with field-level details.
    """
    request_id = _get_request_id(request)

    # Extract validation error details
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    response = error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details={"validation_errors": errors},
        request_id=request_id,
    )

    return JSONResponse(status_code=422, content=response)


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError (not from request body)."""
    request_id = _get_request_id(request)

    errors = [
        {
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    response = error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Data validation failed",
        details={"validation_errors": errors},
        request_id=request_id,
    )

    return JSONResponse(status_code=422, content=response)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors with standard error format."""
    request_id = _get_request_id(request)

    response = error_response(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=f"Rate limit exceeded: {exc.detail}",
        details={"retry_after": getattr(exc, "retry_after", None)},
        request_id=request_id,
    )

    return JSONResponse(status_code=429, content=response)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exception with standard error format.

    This is the catch-all handler for unexpected errors.
    Logs the full exception for debugging while returning a safe error message.
    """
    request_id = _get_request_id(request)

    # Log the full error for debugging
    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    response = error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        request_id=request_id,
    )

    return JSONResponse(status_code=500, content=response)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app.

    This should be called during app initialization to ensure
    consistent error handling across all endpoints.

    Args:
        app: The FastAPI application instance.

    Example:
        >>> app = FastAPI()
        >>> setup_exception_handlers(app)
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    # Generic handler for any unhandled exception
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers configured for standardized error responses")
