"""Tests for the centralized exception hierarchy.

Tests the custom exception classes and their integration with the
global exception handler middleware.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    CardNotFoundError,
    ClaudeAPIError,
    ConflictError,
    DatabaseConnectionError,
    DuplicateEntryError,
    ExternalServiceError,
    InsufficientBalanceError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    InvalidInputError,
    MissingFieldError,
    MoneyFlowError,
    NotFoundError,
    OperationFailedError,
    PasswordWeakError,
    RateLimitError,
    SubscriptionNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
    VectorStoreError,
)
from src.middleware.exception_handler import setup_exception_handlers
from src.schemas.response import ErrorCode


class TestMoneyFlowError:
    """Tests for the base MoneyFlowError exception."""

    def test_default_values(self):
        """Test default error code and status code."""
        error = MoneyFlowError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.status_code == 500
        assert error.details == {}

    def test_custom_values(self):
        """Test custom error code and status code."""
        error = MoneyFlowError(
            message="Custom error",
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={"key": "value"},
        )
        assert error.message == "Custom error"
        assert error.error_code == ErrorCode.NOT_FOUND
        assert error.status_code == 404
        assert error.details == {"key": "value"}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = MoneyFlowError(
            message="Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": "test"},
        )
        result = error.to_dict()
        assert result == {
            "code": ErrorCode.VALIDATION_ERROR,
            "message": "Test error",
            "details": {"field": "test"},
        }

    def test_to_dict_without_details(self):
        """Test conversion to dictionary without details."""
        error = MoneyFlowError("Test error")
        result = error.to_dict()
        assert result == {
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "Test error",
        }
        assert "details" not in result


class TestValidationErrors:
    """Tests for validation error classes."""

    def test_validation_error(self):
        """Test base validation error."""
        error = ValidationError("Validation failed", field="email")
        assert error.status_code == 422
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "email"

    def test_invalid_input_error(self):
        """Test invalid input error."""
        error = InvalidInputError("Invalid email format", field="email")
        assert error.status_code == 422
        assert error.error_code == ErrorCode.INVALID_INPUT

    def test_missing_field_error(self):
        """Test missing field error."""
        error = MissingFieldError("name")
        assert error.message == "Missing required field: name"
        assert error.error_code == ErrorCode.MISSING_FIELD
        assert error.details["field"] == "name"

    def test_password_weak_error(self):
        """Test password weak error."""
        errors = ["Too short", "No uppercase"]
        error = PasswordWeakError("Password is weak", errors=errors)
        assert error.status_code == 422
        assert error.error_code == ErrorCode.INVALID_INPUT
        assert error.errors == errors
        assert error.details["errors"] == errors


class TestAuthenticationErrors:
    """Tests for authentication error classes."""

    def test_authentication_error(self):
        """Test base authentication error."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert error.error_code == ErrorCode.UNAUTHORIZED

    def test_invalid_credentials_error(self):
        """Test invalid credentials error."""
        error = InvalidCredentialsError()
        assert error.message == "Invalid email or password"
        assert error.error_code == ErrorCode.INVALID_CREDENTIALS
        assert error.status_code == 401

    def test_token_expired_error(self):
        """Test token expired error."""
        error = TokenExpiredError()
        assert error.message == "Token has expired"
        assert error.error_code == ErrorCode.TOKEN_EXPIRED

    def test_token_invalid_error(self):
        """Test token invalid error."""
        error = TokenInvalidError()
        assert error.message == "Invalid token"
        assert error.error_code == ErrorCode.TOKEN_INVALID

    def test_account_locked_error(self):
        """Test account locked error."""
        error = AccountLockedError(
            message="Account locked",
            locked_until="2024-01-01T00:00:00",
        )
        assert error.error_code == ErrorCode.ACCOUNT_LOCKED
        assert error.locked_until == "2024-01-01T00:00:00"
        assert error.details["locked_until"] == "2024-01-01T00:00:00"

    def test_account_inactive_error(self):
        """Test account inactive error."""
        error = AccountInactiveError()
        assert error.message == "Account is inactive"
        assert error.error_code == ErrorCode.ACCOUNT_INACTIVE


class TestAuthorizationErrors:
    """Tests for authorization error classes."""

    def test_authorization_error(self):
        """Test base authorization error."""
        error = AuthorizationError()
        assert error.status_code == 403
        assert error.error_code == ErrorCode.FORBIDDEN

    def test_insufficient_permissions_error(self):
        """Test insufficient permissions error."""
        error = InsufficientPermissionsError("admin")
        assert "admin required" in error.message
        assert error.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert error.details["required_permission"] == "admin"


class TestNotFoundErrors:
    """Tests for not found error classes."""

    def test_not_found_error(self):
        """Test base not found error."""
        error = NotFoundError(
            message="Item not found",
            resource_type="item",
            resource_id="123",
        )
        assert error.status_code == 404
        assert error.error_code == ErrorCode.NOT_FOUND
        assert error.resource_type == "item"
        assert error.resource_id == "123"

    def test_subscription_not_found_error(self):
        """Test subscription not found error."""
        error = SubscriptionNotFoundError("sub-123")
        assert "sub-123" in error.message
        assert error.details["resource_type"] == "subscription"
        assert error.details["resource_id"] == "sub-123"

    def test_user_not_found_error(self):
        """Test user not found error."""
        error = UserNotFoundError(user_id="user-123")
        assert "user-123" in error.message
        assert error.details["resource_type"] == "user"

    def test_user_not_found_error_by_email(self):
        """Test user not found error by email."""
        error = UserNotFoundError(email="test@example.com")
        assert "test@example.com" in error.message

    def test_card_not_found_error(self):
        """Test card not found error."""
        error = CardNotFoundError("card-123")
        assert "card-123" in error.message
        assert error.details["resource_type"] == "card"


class TestConflictErrors:
    """Tests for conflict error classes."""

    def test_conflict_error(self):
        """Test base conflict error."""
        error = ConflictError()
        assert error.status_code == 409
        assert error.error_code == ErrorCode.CONFLICT

    def test_duplicate_entry_error(self):
        """Test duplicate entry error."""
        error = DuplicateEntryError("user", "email@test.com")
        assert "user" in error.message
        assert "email@test.com" in error.message
        assert error.error_code == ErrorCode.DUPLICATE_ENTRY

    def test_already_exists_error(self):
        """Test already exists error."""
        error = AlreadyExistsError("Resource already exists")
        assert error.error_code == ErrorCode.ALREADY_EXISTS

    def test_user_already_exists_error(self):
        """Test user already exists error."""
        error = UserAlreadyExistsError("test@example.com")
        assert "test@example.com" in error.message
        assert error.email == "test@example.com"
        assert error.details["email"] == "test@example.com"


class TestRateLimitError:
    """Tests for rate limit error."""

    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError(retry_after=60)
        assert error.status_code == 429
        assert error.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60


class TestExternalServiceErrors:
    """Tests for external service error classes."""

    def test_external_service_error(self):
        """Test base external service error."""
        error = ExternalServiceError(service_name="api")
        assert error.status_code == 503
        assert error.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert error.service_name == "api"

    def test_claude_api_error(self):
        """Test Claude API error."""
        error = ClaudeAPIError("API request failed")
        assert error.service_name == "claude_api"
        assert "API request failed" in error.message

    def test_database_connection_error(self):
        """Test database connection error."""
        error = DatabaseConnectionError()
        assert error.service_name == "database"
        assert error.error_code == ErrorCode.DATABASE_ERROR

    def test_vector_store_error(self):
        """Test vector store error."""
        error = VectorStoreError()
        assert error.service_name == "qdrant"


class TestBusinessLogicErrors:
    """Tests for business logic error classes."""

    def test_business_logic_error(self):
        """Test base business logic error."""
        error = BusinessLogicError()
        assert error.status_code == 400
        assert error.error_code == ErrorCode.BUSINESS_ERROR

    def test_operation_failed_error(self):
        """Test operation failed error."""
        error = OperationFailedError(message="Failed", reason="Invalid state")
        assert error.error_code == ErrorCode.OPERATION_FAILED
        assert error.details["reason"] == "Invalid state"

    def test_insufficient_balance_error(self):
        """Test insufficient balance error."""
        error = InsufficientBalanceError(
            required="100.00",
            available="50.00",
        )
        assert error.details["required"] == "100.00"
        assert error.details["available"] == "50.00"


class TestExceptionHandlerIntegration:
    """Integration tests for exception handler middleware."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with exception handlers."""
        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/not-found")
        async def raise_not_found():
            raise SubscriptionNotFoundError("test-123")

        @app.get("/unauthorized")
        async def raise_unauthorized():
            raise InvalidCredentialsError()

        @app.get("/validation")
        async def raise_validation():
            raise MissingFieldError("name")

        @app.get("/conflict")
        async def raise_conflict():
            raise UserAlreadyExistsError("test@example.com")

        @app.get("/rate-limit")
        async def raise_rate_limit():
            raise RateLimitError(retry_after=30)

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_not_found_handler(self, client):
        """Test not found exception is handled correctly."""
        response = client.get("/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.NOT_FOUND
        assert "test-123" in data["error"]["message"]

    def test_unauthorized_handler(self, client):
        """Test unauthorized exception is handled correctly."""
        response = client.get("/unauthorized")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.INVALID_CREDENTIALS

    def test_validation_handler(self, client):
        """Test validation exception is handled correctly."""
        response = client.get("/validation")
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.MISSING_FIELD

    def test_conflict_handler(self, client):
        """Test conflict exception is handled correctly."""
        response = client.get("/conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.DUPLICATE_ENTRY

    def test_rate_limit_handler(self, client):
        """Test rate limit exception is handled correctly."""
        response = client.get("/rate-limit")
        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.RATE_LIMIT_EXCEEDED
        assert data["error"]["details"]["retry_after"] == 30
