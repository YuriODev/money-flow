"""PDF Report Configuration Schemas.

This module defines Pydantic schemas for configuring PDF report generation,
including section toggles, date ranges, currency options, and filters.
"""

from enum import Enum

from pydantic import BaseModel, Field


class PageSize(str, Enum):
    """Page size options for PDF reports."""

    A4 = "a4"
    LETTER = "letter"


class ColorScheme(str, Enum):
    """Color scheme options for PDF reports."""

    DEFAULT = "default"
    MONOCHROME = "monochrome"
    HIGH_CONTRAST = "high_contrast"


class ReportSections(BaseModel):
    """Configuration for which sections to include in the report."""

    summary: bool = Field(default=True, description="Include summary statistics section")
    category_breakdown: bool = Field(
        default=True, description="Include spending by category section"
    )
    one_time_payments: bool = Field(default=True, description="Include one-time payments section")
    charts: bool = Field(default=True, description="Include visual charts (pie chart & bar charts)")
    card_breakdown: bool = Field(default=False, description="Include spending by card section")
    upcoming_payments: bool = Field(
        default=True, description="Include upcoming & overdue payments section"
    )
    payment_history: bool = Field(
        default=True, description="Include recent payment history section"
    )
    debt_progress: bool = Field(default=False, description="Include debt progress section")
    savings_progress: bool = Field(default=False, description="Include savings goals section")
    budget_status: bool = Field(default=False, description="Include budget status section")
    all_payments: bool = Field(default=True, description="Include full payments table")


class ReportFilters(BaseModel):
    """Filters to apply when generating the report."""

    payment_modes: list[str] | None = Field(
        default=None, description="Filter by payment modes (recurring, debt, savings, one_time)"
    )
    categories: list[str] | None = Field(
        default=None, description="Filter by category names or IDs"
    )
    cards: list[str] | None = Field(default=None, description="Filter by card names or IDs")
    include_inactive: bool = Field(default=False, description="Include inactive payments")


class ReportOptions(BaseModel):
    """Visual and display options for the report."""

    show_original_currency: bool = Field(
        default=True, description="Show original currency alongside converted amounts"
    )
    include_charts: bool = Field(default=False, description="Include visual charts (future)")
    color_scheme: ColorScheme = Field(
        default=ColorScheme.DEFAULT, description="Color scheme for the report"
    )


class ReportConfig(BaseModel):
    """Complete configuration for PDF report generation.

    This schema allows users to customize:
    - Page layout (size)
    - Currency conversion
    - Date ranges for upcoming payments and history
    - Which sections to include/exclude
    - Filters for payment types, categories, cards
    - Visual options

    Example:
        >>> config = ReportConfig(
        ...     target_currency="USD",
        ...     date_range_days=60,
        ...     sections=ReportSections(card_breakdown=True, debt_progress=True),
        ...     filters=ReportFilters(include_inactive=True),
        ... )
    """

    # Page layout
    page_size: PageSize = Field(default=PageSize.A4, description="PDF page size")

    # Currency
    target_currency: str | None = Field(
        default=None,
        description="Target currency for report totals (default: user preference or GBP)",
        min_length=3,
        max_length=3,
    )

    # Date ranges
    date_range_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Days ahead to show for upcoming payments",
    )
    history_days: int = Field(
        default=30, ge=1, le=365, description="Days of payment history to include"
    )

    # Sections
    sections: ReportSections = Field(
        default_factory=ReportSections, description="Which sections to include"
    )

    # Filters
    filters: ReportFilters = Field(default_factory=ReportFilters, description="Filters to apply")

    # Options
    options: ReportOptions = Field(
        default_factory=ReportOptions, description="Visual and display options"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_size": "a4",
                    "target_currency": "USD",
                    "date_range_days": 60,
                    "history_days": 30,
                    "sections": {
                        "summary": True,
                        "category_breakdown": True,
                        "card_breakdown": True,
                        "upcoming_payments": True,
                        "payment_history": True,
                        "debt_progress": True,
                        "savings_progress": True,
                        "budget_status": False,
                        "all_payments": True,
                    },
                    "filters": {
                        "payment_modes": ["recurring", "debt"],
                        "categories": None,
                        "cards": None,
                        "include_inactive": False,
                    },
                    "options": {
                        "show_original_currency": True,
                        "include_charts": False,
                        "color_scheme": "default",
                    },
                }
            ]
        }
    }


class ReportConfigResponse(BaseModel):
    """Response schema for report configuration validation."""

    valid: bool = Field(description="Whether the configuration is valid")
    config: ReportConfig = Field(description="The validated configuration")
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings about the configuration"
    )
