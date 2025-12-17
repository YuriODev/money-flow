"""Global exception handler for standardized error responses.

This module provides exception handlers that convert all errors to the
standard API error response format defined in schemas/response.py.

This ensures consistent error responses across all endpoints regardless
of where the error originates.

Supported Exception Types:
    - MoneyFlowError (and subclasses): Custom application exceptions
    - HTTPException: FastAPI HTTP exceptions
    - RequestValidationError: Pydantic request validation
    - RateLimitExceeded: Rate limiting errors
    - SQLAlchemyError: Database errors
    - Exception: Catch-all for unhandled errors
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.auth.jwt import TokenError as JWTTokenError
from src.auth.security import PasswordStrengthError
from src.core.exceptions import MoneyFlowError
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


async def moneyflow_exception_handler(request: Request, exc: MoneyFlowError) -> JSONResponse:
    """Handle MoneyFlowError and subclasses with standard error format.

    Converts custom application exceptions to standardized error responses.
    The exception carries its own status code and error code.
    """
    request_id = _get_request_id(request)

    # Log based on severity (5xx errors are more severe)
    if exc.status_code >= 500:
        logger.error(
            f"Application error: {exc.message}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
            },
        )
    else:
        logger.warning(
            f"Application error: {exc.message}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
            },
        )

    response = error_response(
        code=exc.error_code,
        message=exc.message,
        details=exc.details if exc.details else None,
        request_id=request_id,
    )

    return JSONResponse(status_code=exc.status_code, content=response)


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors with standard error format.

    Logs the full error for debugging while returning a safe message.
    """
    request_id = _get_request_id(request)

    # Log the full error for debugging (but don't expose to client)
    logger.exception(
        "Database error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    response = error_response(
        code=ErrorCode.DATABASE_ERROR,
        message="A database error occurred",
        request_id=request_id,
    )

    return JSONResponse(status_code=503, content=response)


async def password_strength_exception_handler(
    request: Request, exc: PasswordStrengthError
) -> JSONResponse:
    """Handle PasswordStrengthError with standard error format.

    Converts password validation errors to standardized error responses.
    """
    request_id = _get_request_id(request)

    response = error_response(
        code=ErrorCode.INVALID_INPUT,
        message=exc.message,
        details={"errors": exc.errors} if exc.errors else None,
        request_id=request_id,
    )

    return JSONResponse(status_code=422, content=response)


async def jwt_token_exception_handler(request: Request, exc: JWTTokenError) -> JSONResponse:
    """Handle JWT token errors with standard error format.

    Handles TokenError, TokenExpiredError, TokenInvalidError from auth/jwt.py.
    """
    request_id = _get_request_id(request)

    # Determine specific error code based on exception type
    from src.auth.jwt import TokenExpiredError as JWTExpiredError
    from src.auth.jwt import TokenInvalidError as JWTInvalidError

    if isinstance(exc, JWTExpiredError):
        error_code = ErrorCode.TOKEN_EXPIRED
    elif isinstance(exc, JWTInvalidError):
        error_code = ErrorCode.TOKEN_INVALID
    else:
        error_code = ErrorCode.UNAUTHORIZED

    response = error_response(
        code=error_code,
        message=str(exc),
        request_id=request_id,
    )

    return JSONResponse(status_code=401, content=response)


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

    Handler order matters! More specific exceptions should be registered first.
    The handlers are checked in reverse registration order, so the most
    specific handlers (registered last) are checked first.

    Args:
        app: The FastAPI application instance.

    Example:
        >>> app = FastAPI()
        >>> setup_exception_handlers(app)
    """
    # Generic handler for any unhandled exception (lowest priority)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Rate limiting
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    # Validation errors
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PasswordStrengthError, password_strength_exception_handler)

    # JWT token errors
    app.add_exception_handler(JWTTokenError, jwt_token_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Custom Money Flow exceptions (highest priority)
    app.add_exception_handler(MoneyFlowError, moneyflow_exception_handler)

    logger.info("Exception handlers configured for standardized error responses")
