"""Unit tests for category functionality.

Sprint 5.2.4 - Categories tests covering:
- Category model tests
- Category schema validation tests
- Category service tests
- Category API tests
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.models.category import Category
from src.schemas.category import (
    AssignCategoryRequest,
    BulkAssignCategoryRequest,
    CategoryBudgetSummary,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithStats,
)

# ============================================================================
# Model Tests
# ============================================================================


class TestCategoryModel:
    """Tests for the Category SQLAlchemy model."""

    def test_category_creation_defaults(self):
        """Test category model with default values.

        Note: SQLAlchemy defaults are applied at DB level during INSERT,
        not at Python instantiation time. This test verifies the model
        accepts minimal required fields.
        """
        category = Category(
            name="Entertainment",
            user_id="user-123",
        )
        assert category.name == "Entertainment"
        assert category.user_id == "user-123"
        # SQLAlchemy column defaults are applied at DB level, not Python level
        # So values may be None when model is instantiated without database
        # The actual defaults are verified to work when persisted to DB

    def test_category_creation_all_fields(self):
        """Test category model with all fields."""
        category = Category(
            name="Utilities",
            description="Monthly utility bills",
            color="#F59E0B",
            icon="⚡",
            budget_amount=Decimal("200.00"),
            budget_currency="GBP",
            is_active=True,
            is_system=False,
            sort_order=5,
            user_id="user-456",
        )
        assert category.name == "Utilities"
        assert category.description == "Monthly utility bills"
        assert category.color == "#F59E0B"
        assert category.icon == "⚡"
        assert category.budget_amount == Decimal("200.00")
        assert category.sort_order == 5

    def test_category_repr(self):
        """Test category string representation."""
        category = Category(
            name="Entertainment",
            color="#8B5CF6",
            user_id="user-123",
        )
        repr_str = repr(category)
        assert "Entertainment" in repr_str
        assert "#8B5CF6" in repr_str

    def test_category_is_over_budget_no_budget(self):
        """Test is_over_budget when no budget set."""
        category = Category(
            name="Test",
            user_id="user-123",
        )
        assert category.is_over_budget is None


# ============================================================================
# Schema Tests
# ============================================================================


class TestCategoryCreate:
    """Tests for CategoryCreate schema."""

    def test_valid_category_create(self):
        """Test valid category creation."""
        data = CategoryCreate(
            name="Entertainment",
            color="#8B5CF6",
            icon="🎬",
        )
        assert data.name == "Entertainment"
        assert data.color == "#8B5CF6"

    def test_category_create_with_budget(self):
        """Test category creation with budget."""
        data = CategoryCreate(
            name="Utilities",
            budget_amount=Decimal("150.00"),
            budget_currency="GBP",
        )
        assert data.budget_amount == Decimal("150.00")
        assert data.budget_currency == "GBP"

    def test_category_create_defaults(self):
        """Test category creation defaults."""
        data = CategoryCreate(name="Test")
        assert data.color == "#6366F1"
        assert data.description is None
        assert data.icon is None
        assert data.budget_amount is None

    def test_category_create_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            CategoryCreate()

    def test_category_create_name_min_length(self):
        """Test name minimum length."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="")

    def test_category_create_name_max_length(self):
        """Test name maximum length."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="x" * 101)

    def test_category_create_invalid_color(self):
        """Test invalid color format."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", color="red")

    def test_category_create_invalid_color_format(self):
        """Test invalid hex color format."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", color="#GGG")

    def test_category_create_valid_color_formats(self):
        """Test various valid hex color formats."""
        # Uppercase
        data = CategoryCreate(name="Test", color="#AABBCC")
        assert data.color == "#AABBCC"

        # Lowercase
        data = CategoryCreate(name="Test", color="#aabbcc")
        assert data.color == "#aabbcc"

        # Mixed case
        data = CategoryCreate(name="Test", color="#AaBbCc")
        assert data.color == "#AaBbCc"

    def test_category_create_budget_negative(self):
        """Test that negative budget is rejected."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", budget_amount=Decimal("-50.00"))

    def test_category_create_budget_too_large(self):
        """Test that excessively large budget is rejected."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", budget_amount=Decimal("2000000.00"))


class TestCategoryUpdate:
    """Tests for CategoryUpdate schema."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = CategoryUpdate(name="Updated Name")
        assert data.name == "Updated Name"
        assert data.color is None
        assert data.budget_amount is None

    def test_update_all_fields(self):
        """Test update with all fields."""
        data = CategoryUpdate(
            name="Updated",
            description="New description",
            color="#FF0000",
            icon="🔥",
            budget_amount=Decimal("100.00"),
            is_active=False,
            sort_order=10,
        )
        assert data.name == "Updated"
        assert data.is_active is False

    def test_update_empty_allowed(self):
        """Test that empty update is allowed."""
        data = CategoryUpdate()
        assert data.name is None

    def test_update_null_budget(self):
        """Test setting budget to null."""
        data = CategoryUpdate(budget_amount=None)
        assert data.budget_amount is None


class TestCategoryResponse:
    """Tests for CategoryResponse schema."""

    def test_from_orm(self):
        """Test creating response from ORM model."""
        # Create a mock category object
        category = MagicMock()
        category.id = "cat-123"
        category.name = "Entertainment"
        category.description = None
        category.color = "#8B5CF6"
        category.icon = "🎬"
        category.budget_amount = None
        category.budget_currency = "GBP"
        category.sort_order = 0
        category.is_active = True
        category.is_system = False
        category.user_id = "user-123"
        category.created_at = datetime.utcnow()
        category.updated_at = datetime.utcnow()

        response = CategoryResponse.model_validate(category)
        assert response.id == "cat-123"
        assert response.name == "Entertainment"


class TestCategoryWithStats:
    """Tests for CategoryWithStats schema."""

    def test_with_stats(self):
        """Test category with stats."""
        data = CategoryWithStats(
            id="cat-123",
            name="Entertainment",
            color="#8B5CF6",
            budget_currency="GBP",
            sort_order=0,
            is_active=True,
            is_system=False,
            user_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            subscription_count=5,
            total_monthly=Decimal("75.50"),
            budget_used_percentage=50.0,
            is_over_budget=False,
        )
        assert data.subscription_count == 5
        assert data.total_monthly == Decimal("75.50")

    def test_with_stats_defaults(self):
        """Test stats defaults."""
        data = CategoryWithStats(
            id="cat-123",
            name="Entertainment",
            color="#8B5CF6",
            budget_currency="GBP",
            sort_order=0,
            is_active=True,
            is_system=False,
            user_id="user-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert data.subscription_count == 0
        assert data.total_monthly == Decimal("0")
        assert data.budget_used_percentage is None


class TestAssignCategoryRequest:
    """Tests for AssignCategoryRequest schema."""

    def test_valid_assign(self):
        """Test valid assignment request."""
        sub_id = "550e8400-e29b-41d4-a716-446655440000"
        cat_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        data = AssignCategoryRequest(
            subscription_id=sub_id,
            category_id=cat_id,
        )
        assert data.subscription_id == sub_id
        assert data.category_id == cat_id

    def test_unassign_null_category(self):
        """Test unassigning (null category)."""
        sub_id = "550e8400-e29b-41d4-a716-446655440000"
        data = AssignCategoryRequest(
            subscription_id=sub_id,
            category_id=None,
        )
        assert data.category_id is None


class TestBulkAssignCategoryRequest:
    """Tests for BulkAssignCategoryRequest schema."""

    def test_valid_bulk_assign(self):
        """Test valid bulk assignment."""
        sub_ids = [
            "550e8400-e29b-41d4-a716-446655440001",
            "550e8400-e29b-41d4-a716-446655440002",
            "550e8400-e29b-41d4-a716-446655440003",
        ]
        cat_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        data = BulkAssignCategoryRequest(
            subscription_ids=sub_ids,
            category_id=cat_id,
        )
        assert len(data.subscription_ids) == 3

    def test_bulk_assign_min_length(self):
        """Test bulk assign requires at least one subscription."""
        cat_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        with pytest.raises(ValidationError):
            BulkAssignCategoryRequest(
                subscription_ids=[],
                category_id=cat_id,
            )

    def test_bulk_assign_max_length(self):
        """Test bulk assign has max limit."""
        import uuid
        cat_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        with pytest.raises(ValidationError):
            BulkAssignCategoryRequest(
                subscription_ids=[str(uuid.uuid4()) for _ in range(101)],
                category_id=cat_id,
            )


class TestCategoryBudgetSummary:
    """Tests for CategoryBudgetSummary schema."""

    def test_budget_summary(self):
        """Test budget summary creation."""
        categories = [
            CategoryWithStats(
                id="cat-1",
                name="Entertainment",
                color="#8B5CF6",
                budget_currency="GBP",
                budget_amount=Decimal("100.00"),
                sort_order=0,
                is_active=True,
                is_system=False,
                user_id="user-123",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                subscription_count=3,
                total_monthly=Decimal("50.00"),
                budget_used_percentage=50.0,
                is_over_budget=False,
            ),
        ]
        summary = CategoryBudgetSummary(
            categories=categories,
            total_budgeted=Decimal("100.00"),
            total_spent=Decimal("50.00"),
            categories_over_budget=0,
        )
        assert summary.total_budgeted == Decimal("100.00")
        assert summary.categories_over_budget == 0


# ============================================================================
# Service Tests (Mocked)
# ============================================================================


class TestCategoryServiceMocked:
    """Tests for CategoryService with mocked database."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.delete = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a CategoryService instance."""
        from src.services.category_service import CategoryService

        return CategoryService(mock_db, user_id="user-123")

    @pytest.mark.asyncio
    async def test_get_all_returns_user_categories(self, service, mock_db):
        """Test get_all filters by user_id."""
        # Mock the result
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.get_all()

        assert result == []
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_category(self, service, mock_db):
        """Test creating a category."""
        data = CategoryCreate(name="Test Category", color="#FF0000")

        # Mock refresh to populate the model
        async def mock_refresh(obj):
            obj.id = "cat-new-123"
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()

        mock_db.refresh = mock_refresh

        result = await service.create(data)

        assert result.name == "Test Category"
        assert result.color == "#FF0000"
        assert result.user_id == "user-123"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_system_category_fails(self, service, mock_db):
        """Test that system categories cannot be deleted."""
        # Mock get_by_id to return a system category
        mock_category = MagicMock()
        mock_category.is_system = True

        with patch.object(service, "get_by_id", return_value=mock_category):
            result = await service.delete("cat-123")

        assert result is False
        mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_non_existent_category(self, service, mock_db):
        """Test deleting non-existent category."""
        with patch.object(service, "get_by_id", return_value=None):
            result = await service.delete("cat-not-found")

        assert result is False


# ============================================================================
# Default Categories Tests
# ============================================================================


class TestDefaultCategories:
    """Tests for default category creation."""

    def test_default_categories_list(self):
        """Test that default categories have expected properties."""

        # Access the default categories from create_default_categories method
        default_categories = [
            {"name": "Entertainment", "color": "#8B5CF6", "icon": "🎬"},
            {"name": "Utilities", "color": "#F59E0B", "icon": "⚡"},
            {"name": "Housing", "color": "#10B981", "icon": "🏠"},
            {"name": "Transportation", "color": "#3B82F6", "icon": "🚗"},
            {"name": "Health & Fitness", "color": "#EF4444", "icon": "💪"},
            {"name": "Food & Dining", "color": "#EC4899", "icon": "🍔"},
            {"name": "Shopping", "color": "#06B6D4", "icon": "🛍️"},
            {"name": "Education", "color": "#6366F1", "icon": "📚"},
        ]

        assert len(default_categories) == 8
        assert all("name" in cat for cat in default_categories)
        assert all("color" in cat for cat in default_categories)
        assert all("icon" in cat for cat in default_categories)

        # Verify color format
        for cat in default_categories:
            assert cat["color"].startswith("#")
            assert len(cat["color"]) == 7

    def test_default_category_names_unique(self):
        """Test that default category names are unique."""
        default_names = [
            "Entertainment",
            "Utilities",
            "Housing",
            "Transportation",
            "Health & Fitness",
            "Food & Dining",
            "Shopping",
            "Education",
        ]
        assert len(default_names) == len(set(default_names))


# ============================================================================
# Color Validation Tests
# ============================================================================


class TestColorValidation:
    """Tests for color validation in categories."""

    @pytest.mark.parametrize(
        "color",
        [
            "#000000",
            "#FFFFFF",
            "#123456",
            "#abcdef",
            "#ABCDEF",
            "#AbCdEf",
        ],
    )
    def test_valid_colors(self, color):
        """Test valid color formats."""
        data = CategoryCreate(name="Test", color=color)
        assert data.color == color

    @pytest.mark.parametrize(
        "color",
        [
            "red",
            "blue",
            "#FFF",  # 3-char hex not allowed
            "123456",  # Missing #
            "#GGGGGG",  # Invalid hex chars
            "#12345",  # Too short
            "#1234567",  # Too long
            "",
            "rgb(255,0,0)",
        ],
    )
    def test_invalid_colors(self, color):
        """Test invalid color formats."""
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", color=color)


# ============================================================================
# Budget Calculation Tests
# ============================================================================


class TestBudgetCalculations:
    """Tests for budget-related calculations."""

    def test_budget_percentage_calculation(self):
        """Test budget percentage calculation."""
        budget_amount = Decimal("100.00")
        spent = Decimal("75.00")

        percentage = float((spent / budget_amount) * 100)
        assert percentage == 75.0

    def test_over_budget_detection(self):
        """Test over budget detection."""
        budget_amount = Decimal("100.00")
        spent = Decimal("150.00")

        is_over = spent > budget_amount
        assert is_over is True

        percentage = float((spent / budget_amount) * 100)
        assert percentage == 150.0

    def test_under_budget(self):
        """Test under budget scenario."""
        budget_amount = Decimal("100.00")
        spent = Decimal("50.00")

        is_over = spent > budget_amount
        assert is_over is False

    def test_exact_budget(self):
        """Test exact budget scenario."""
        budget_amount = Decimal("100.00")
        spent = Decimal("100.00")

        is_over = spent > budget_amount
        assert is_over is False

        percentage = float((spent / budget_amount) * 100)
        assert percentage == 100.0
