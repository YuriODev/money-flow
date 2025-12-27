"""PDF Report Generation Service.

This module provides PDF report generation for subscription/payment data
using ReportLab. Reports include summaries, payment lists, and visual charts.

Supports multi-currency handling with automatic conversion to report currency.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING

from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if TYPE_CHECKING:
    from src.models.subscription import Subscription
    from src.schemas.report import ReportConfig
    from src.services.currency_service import CurrencyService

logger = logging.getLogger(__name__)

# Page size constants
PAGE_SIZES = {
    "a4": A4,
    "letter": letter,
}

# Currency symbols
CURRENCY_SYMBOLS = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "UAH": "₴",
}

# Chart colors for pie chart (10 visually distinct colors)
CHART_COLORS = [
    colors.HexColor("#3b82f6"),  # Blue
    colors.HexColor("#10b981"),  # Green
    colors.HexColor("#f59e0b"),  # Amber
    colors.HexColor("#ef4444"),  # Red
    colors.HexColor("#8b5cf6"),  # Purple
    colors.HexColor("#ec4899"),  # Pink
    colors.HexColor("#06b6d4"),  # Cyan
    colors.HexColor("#84cc16"),  # Lime
    colors.HexColor("#f97316"),  # Orange
    colors.HexColor("#6366f1"),  # Indigo
]


class PDFReportService:
    """Service for generating PDF reports of subscription/payment data.

    Generates professional PDF reports with:
    - Summary statistics (with multi-currency conversion)
    - Payment lists by category
    - Monthly spending breakdown
    - Upcoming payments section
    - Payment history section
    - Currency column showing original and converted amounts

    Supports configurable sections via ReportConfig.
    """

    def __init__(
        self,
        page_size: str = "a4",
        include_inactive: bool = False,
        currency: str = "GBP",
        currency_service: "CurrencyService | None" = None,
        config: "ReportConfig | None" = None,
    ):
        """Initialize PDF report service.

        Args:
            page_size: Page size ('a4' or 'letter').
            include_inactive: Whether to include inactive subscriptions.
            currency: Target currency for report (all amounts converted to this).
            currency_service: CurrencyService instance for conversions. If None,
                amounts are displayed in original currency without conversion.
            config: Optional ReportConfig for advanced customization. If provided,
                overrides page_size, include_inactive, and currency parameters.
        """
        # If config provided, use its values
        if config:
            self.config = config
            self.page_size = PAGE_SIZES.get(config.page_size.value.lower(), A4)
            self.include_inactive = config.filters.include_inactive
            self.currency = config.target_currency or currency
            self.date_range_days = config.date_range_days
            self.history_days = config.history_days
            self.show_original_currency = config.options.show_original_currency
        else:
            self.config = None
            self.page_size = PAGE_SIZES.get(page_size.lower(), A4)
            self.include_inactive = include_inactive
            self.currency = currency
            self.date_range_days = 30
            self.history_days = 30
            self.show_original_currency = True

        self.currency_symbol = CURRENCY_SYMBOLS.get(self.currency, "£")
        self.currency_service = currency_service
        self._conversion_cache: dict[str, Decimal] = {}  # Cache converted amounts
        self._failed_conversions: set[str] = set()  # Track failed currency conversions
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _convert_amount(self, amount: Decimal, from_currency: str) -> Decimal:
        """Convert amount to report currency synchronously using cached rates.

        Args:
            amount: Amount to convert.
            from_currency: Source currency code.

        Returns:
            Converted amount in report currency. Returns original if conversion fails.
        """
        from_currency = from_currency.upper()

        # Same currency = no conversion needed
        if from_currency == self.currency:
            return amount

        # Check cache first
        cache_key = f"{from_currency}_{self.currency}"
        if cache_key in self._conversion_cache:
            rate = self._conversion_cache[cache_key]
            return (amount * rate).quantize(Decimal("0.01"))

        # No currency service = return original
        if not self.currency_service:
            return amount

        # If we already failed for this currency, don't retry
        if from_currency in self._failed_conversions:
            return amount

        # Try to get rate from service cache (synchronously)
        try:
            # The currency service caches rates - we can access them synchronously
            # if they were pre-fetched during async initialization
            if self.currency_service._cache and not self.currency_service._cache.is_expired():
                rates = self.currency_service._cache.rates
                from_rate = rates.get(from_currency)
                to_rate = rates.get(self.currency)

                if from_rate and to_rate and from_rate != Decimal("0"):
                    rate = to_rate / from_rate
                    self._conversion_cache[cache_key] = rate
                    return (amount * rate).quantize(Decimal("0.01"))

            # If cache not available, mark as failed for this session
            self._failed_conversions.add(from_currency)
            logger.warning(f"Could not convert {from_currency} to {self.currency}, using original")
            return amount

        except Exception as e:
            logger.warning(f"Currency conversion failed for {from_currency}: {e}")
            self._failed_conversions.add(from_currency)
            return amount

    def _get_amount_display(
        self, amount: Decimal, currency: str, show_original: bool = True
    ) -> str:
        """Format amount for display, optionally showing original currency.

        Args:
            amount: Original amount.
            currency: Original currency code.
            show_original: Whether to show original amount if different from report currency.

        Returns:
            Formatted amount string.
        """
        original_symbol = CURRENCY_SYMBOLS.get(currency.upper(), currency)
        converted = self._convert_amount(amount, currency)

        # Same currency or no conversion
        if currency.upper() == self.currency or converted == amount:
            return f"{self.currency_symbol}{amount:.2f}"

        # Show both original and converted
        if show_original:
            return f"{self.currency_symbol}{converted:.2f} ({original_symbol}{amount:.2f})"

        return f"{self.currency_symbol}{converted:.2f}"

    async def _prefetch_rates(self) -> None:
        """Pre-fetch exchange rates to populate cache for synchronous access."""
        if self.currency_service:
            try:
                await self.currency_service._get_rates()
                logger.info("Pre-fetched exchange rates for PDF report")
            except Exception as e:
                logger.warning(f"Failed to pre-fetch exchange rates: {e}")

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for the report."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                "ReportTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor("#1a1a2e"),
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                "SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=16,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor("#16213e"),
            )
        )

        # Subsection header style
        self.styles.add(
            ParagraphStyle(
                "SubsectionHeader",
                parent=self.styles["Heading3"],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=8,
                textColor=colors.HexColor("#0f3460"),
            )
        )

        # Normal text style
        self.styles.add(
            ParagraphStyle(
                "ReportBody",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
            )
        )

        # Footer style
        self.styles.add(
            ParagraphStyle(
                "Footer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.gray,
            )
        )

    async def generate_report_async(
        self,
        subscriptions: list["Subscription"],
        user_email: str | None = None,
        report_title: str = "Money Flow Report",
    ) -> bytes:
        """Generate a PDF report asynchronously (with currency conversion).

        Args:
            subscriptions: List of Subscription objects to include in report.
            user_email: Optional user email for personalization.
            report_title: Title for the report.

        Returns:
            PDF file as bytes.
        """
        # Pre-fetch exchange rates for currency conversion
        await self._prefetch_rates()

        # Delegate to synchronous method
        return self.generate_report(subscriptions, user_email, report_title)

    def generate_report(
        self,
        subscriptions: list["Subscription"],
        user_email: str | None = None,
        report_title: str = "Money Flow Report",
    ) -> bytes:
        """Generate a PDF report for the given subscriptions.

        Args:
            subscriptions: List of Subscription objects to include in report.
            user_email: Optional user email for personalization.
            report_title: Title for the report.

        Returns:
            PDF file as bytes.

        Note:
            For proper currency conversion, use generate_report_async() instead,
            or ensure the currency_service cache is pre-populated.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        # Filter subscriptions if needed
        if not self.include_inactive:
            subscriptions = [s for s in subscriptions if s.is_active]

        # Build document elements
        elements = []

        # Title and header (always included)
        elements.extend(self._build_header(report_title, user_email))

        # Determine which sections to include
        include_summary = True
        include_category = True
        include_one_time = True
        include_card = False
        include_upcoming = True
        include_history = True
        include_debt = False
        include_savings = False
        include_budget = False
        include_all_payments = True
        include_charts = False

        if self.config and self.config.sections:
            include_summary = self.config.sections.summary
            include_category = self.config.sections.category_breakdown
            include_one_time = self.config.sections.one_time_payments
            include_charts = self.config.sections.charts
            include_card = self.config.sections.card_breakdown
            include_upcoming = self.config.sections.upcoming_payments
            include_history = self.config.sections.payment_history
            include_debt = self.config.sections.debt_progress
            include_savings = self.config.sections.savings_progress
            include_budget = self.config.sections.budget_status
            include_all_payments = self.config.sections.all_payments

        # Also check options.include_charts for backward compatibility
        if self.config and self.config.options and self.config.options.include_charts:
            include_charts = True

        # Summary section
        if include_summary:
            elements.extend(self._build_summary(subscriptions))

        # Payment breakdown by category (with optional pie chart)
        if include_category:
            elements.extend(self._build_category_breakdown(subscriptions, include_charts))

        # One-time payments section (separate from recurring)
        if include_one_time:
            elements.extend(self._build_one_time_payments_section(subscriptions))

        # Spending bar charts (current month and year-to-date)
        if include_charts:
            elements.extend(self._build_spending_bar_charts(subscriptions))

        # Payment breakdown by card
        if include_card:
            elements.extend(self._build_card_breakdown(subscriptions))

        # Upcoming payments
        if include_upcoming:
            elements.extend(self._build_upcoming_payments(subscriptions))

        # Payment history (recent transactions)
        if include_history:
            elements.extend(self._build_payment_history(subscriptions, self.history_days))

        # Debt progress section
        if include_debt:
            elements.extend(self._build_debt_progress(subscriptions))

        # Savings goals section
        if include_savings:
            elements.extend(self._build_savings_progress(subscriptions))

        # Budget status section
        if include_budget:
            elements.extend(self._build_budget_status(subscriptions))

        # All payments table
        if include_all_payments:
            elements.extend(self._build_payments_table(subscriptions))

        # Footer with currency note
        elements.extend(self._build_footer())

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, title: str, user_email: str | None) -> list[Paragraph | Spacer]:
        """Build report header section.

        Args:
            title: Report title.
            user_email: User email for personalization.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer] = []

        # Title
        elements.append(Paragraph(title, self.styles["ReportTitle"]))

        # Generated date and user info
        generated_at = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
        info_text = f"Generated: {generated_at}"
        if user_email:
            info_text += f"<br/>Account: {user_email}"
        elements.append(Paragraph(info_text, self.styles["ReportBody"]))
        elements.append(Spacer(1, 20))

        return elements

    def _build_summary(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build summary statistics section.

        All amounts are converted to the report currency for accurate totals.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Summary", self.styles["SectionHeader"]))

        # Calculate totals - convert each amount to report currency first
        active_count = sum(1 for s in subscriptions if s.is_active)
        inactive_count = len(subscriptions) - active_count

        monthly_total = Decimal("0")
        yearly_total = Decimal("0")
        currencies_used: set[str] = set()

        for sub in subscriptions:
            if not sub.is_active:
                continue
            # Convert amount to report currency before calculating monthly
            converted_amount = self._convert_amount(sub.amount, sub.currency)
            # Pass payment_mode to properly handle one-time payments
            payment_mode = (
                sub.payment_mode.value
                if hasattr(sub, "payment_mode") and sub.payment_mode
                else None
            )
            monthly = self._to_monthly(converted_amount, sub.frequency.value, payment_mode)
            monthly_total += monthly
            yearly_total += monthly * 12
            currencies_used.add(sub.currency.upper())

        # Summary table
        summary_data = [
            ["Active Payments", str(active_count)],
            ["Inactive Payments", str(inactive_count)],
            ["Monthly Total", f"{self.currency_symbol}{monthly_total:.2f}"],
            ["Yearly Total", f"{self.currency_symbol}{yearly_total:.2f}"],
        ]

        # Add note if multiple currencies were converted
        other_currencies = currencies_used - {self.currency}
        if other_currencies:
            summary_data.append(["Currencies Converted", ", ".join(sorted(other_currencies))])

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_category_breakdown(
        self, subscriptions: list["Subscription"], include_chart: bool = False
    ) -> list[Paragraph | Spacer | Table | Drawing]:
        """Build spending breakdown by category with optional pie chart.

        All amounts are converted to report currency before summing.

        Args:
            subscriptions: List of subscriptions.
            include_chart: Whether to include a pie chart visualization.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table | Drawing] = []
        elements.append(Paragraph("Spending by Category", self.styles["SectionHeader"]))

        # Group by category - convert amounts to report currency
        category_totals: dict[str, Decimal] = {}
        for sub in subscriptions:
            if not sub.is_active:
                continue
            # Use category name from relationship, or string category, or "Uncategorized"
            cat_name = "Uncategorized"
            if hasattr(sub, "category_rel") and sub.category_rel:
                cat_name = sub.category_rel.name
            elif sub.category:
                cat_name = sub.category
            # Convert to report currency before calculating monthly
            converted_amount = self._convert_amount(sub.amount, sub.currency)
            # Pass payment_mode to properly handle one-time payments
            payment_mode = (
                sub.payment_mode.value
                if hasattr(sub, "payment_mode") and sub.payment_mode
                else None
            )
            monthly = self._to_monthly(converted_amount, sub.frequency.value, payment_mode)
            category_totals[cat_name] = category_totals.get(cat_name, Decimal("0")) + monthly

        # Filter out categories with zero monthly spend (only one-time payments)
        category_totals = {k: v for k, v in category_totals.items() if v > 0}

        if not category_totals:
            elements.append(Paragraph("No active payments.", self.styles["ReportBody"]))
            elements.append(Spacer(1, 10))
            return elements

        # Sort by amount descending
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

        # Add pie chart if enabled
        if include_chart and sorted_categories:
            chart = self._build_category_pie_chart(sorted_categories)
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 15))

        # Build table
        table_data = [["Category", "Monthly", "Yearly"]]
        for cat_name, monthly in sorted_categories:
            yearly = monthly * 12
            table_data.append(
                [
                    cat_name,
                    f"{self.currency_symbol}{monthly:.2f}",
                    f"{self.currency_symbol}{yearly:.2f}",
                ]
            )

        # Add total row
        total_monthly = sum(category_totals.values())
        total_yearly = total_monthly * 12
        table_data.append(
            [
                "TOTAL",
                f"{self.currency_symbol}{total_monthly:.2f}",
                f"{self.currency_symbol}{total_yearly:.2f}",
            ]
        )

        category_table = Table(table_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        category_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Total row
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    # All cells
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(category_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_one_time_payments_section(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build a section showing one-time payments.

        One-time payments are excluded from monthly recurring totals but are
        significant expenses that should be visible in the report.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        from src.models.subscription import PaymentMode

        elements: list[Paragraph | Spacer | Table] = []

        # Filter for one-time payments only
        one_time_payments = [
            s
            for s in subscriptions
            if hasattr(s, "payment_mode") and s.payment_mode == PaymentMode.ONE_TIME
        ]

        if not one_time_payments:
            return elements  # No one-time payments, skip section

        elements.append(Paragraph("One-Time Payments", self.styles["SectionHeader"]))
        elements.append(
            Paragraph(
                "These payments are not included in recurring monthly totals.",
                self.styles["ReportBody"],
            )
        )
        elements.append(Spacer(1, 10))

        # Group by category
        category_totals: dict[str, list[tuple[str, Decimal, str, bool]]] = {}
        grand_total = Decimal("0")

        for sub in one_time_payments:
            cat_name = "Uncategorized"
            if hasattr(sub, "category_rel") and sub.category_rel:
                cat_name = sub.category_rel.name
            elif sub.category:
                cat_name = sub.category

            converted_amount = self._convert_amount(sub.amount, sub.currency)
            grand_total += converted_amount

            if cat_name not in category_totals:
                category_totals[cat_name] = []

            # Store: (name, amount, status_label, is_paid)
            status = "Paid" if not sub.is_active else "Pending"
            category_totals[cat_name].append(
                (sub.name, converted_amount, status, not sub.is_active)
            )

        # Build table
        table_data = [["Payment", "Amount", "Status"]]
        status_styles = []

        row_idx = 1
        for cat_name in sorted(category_totals.keys()):
            payments = category_totals[cat_name]
            # Category header row
            cat_total = sum(p[1] for p in payments)
            table_data.append([f"📁 {cat_name}", f"{self.currency_symbol}{cat_total:.2f}", ""])
            status_styles.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#f0f4f8"))
            )
            status_styles.append(("FONTNAME", (0, row_idx), (-1, row_idx), "Helvetica-Bold"))
            row_idx += 1

            # Payment rows
            for name, amount, status, is_paid in payments:
                table_data.append([f"    {name}", f"{self.currency_symbol}{amount:.2f}", status])
                if is_paid:
                    status_styles.append(
                        ("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor("#16a34a"))
                    )
                else:
                    status_styles.append(
                        ("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor("#f59e0b"))
                    )
                row_idx += 1

        # Grand total row
        table_data.append(["TOTAL", f"{self.currency_symbol}{grand_total:.2f}", ""])

        one_time_table = Table(table_data, colWidths=[3.5 * inch, 1.5 * inch, 1 * inch])
        one_time_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Total row
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ede9fe")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    # Column alignment - Payment: LEFT, Amount: RIGHT, Status: CENTER
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
                + status_styles
            )
        )

        elements.append(one_time_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_category_pie_chart(self, category_data: list[tuple[str, Decimal]]) -> Drawing | None:
        """Build a pie chart showing spending by category.

        Creates a ReportLab pie chart with category labels and percentages.
        Limited to top 8 categories to keep the chart readable, with others
        grouped into "Other" category.

        Args:
            category_data: List of (category_name, monthly_amount) tuples,
                           sorted by amount descending.

        Returns:
            Drawing containing the pie chart, or None if no data.
        """
        if not category_data:
            return None

        # Calculate total for percentages
        total = sum(amount for _, amount in category_data)
        if total <= 0:
            return None

        # Limit to top 8 categories, group rest into "Other"
        max_slices = 8
        if len(category_data) > max_slices:
            top_categories = category_data[: max_slices - 1]
            other_total = sum(amount for _, amount in category_data[max_slices - 1 :])
            chart_data = top_categories + [("Other", other_total)]
        else:
            chart_data = category_data

        # Create drawing
        drawing = Drawing(400, 200)

        # Create pie chart
        pie = Pie()
        pie.x = 100
        pie.y = 25
        pie.width = 150
        pie.height = 150

        # Set data and labels
        pie.data = [float(amount) for _, amount in chart_data]
        pie.labels = [
            f"{name[:12]} ({float(amount) / float(total) * 100:.0f}%)"
            for name, amount in chart_data
        ]

        # Set slice colors
        for i, _ in enumerate(chart_data):
            pie.slices[i].fillColor = CHART_COLORS[i % len(CHART_COLORS)]
            pie.slices[i].strokeColor = colors.white
            pie.slices[i].strokeWidth = 1

        # Configure label positioning
        pie.sideLabels = True
        pie.slices.labelRadius = 1.2
        pie.slices.fontName = "Helvetica"
        pie.slices.fontSize = 8

        # Add pie to drawing
        drawing.add(pie)

        # Add title
        title = String(200, 185, "Monthly Spending Distribution", fontSize=10, textAnchor="middle")
        title.fontName = "Helvetica-Bold"
        drawing.add(title)

        return drawing

    def _build_spending_bar_charts(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Drawing]:
        """Build bar charts showing spending by category for current month and YTD.

        Creates two horizontal bar charts:
        1. Current month spending by category
        2. Year-to-date spending by category

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements including the bar charts.
        """
        elements: list[Paragraph | Spacer | Drawing] = []
        elements.append(Paragraph("Spending Analysis", self.styles["SectionHeader"]))

        # Calculate spending by category
        category_monthly: dict[str, Decimal] = {}
        for sub in subscriptions:
            if not sub.is_active:
                continue
            # Get category name
            cat_name = "Uncategorized"
            if hasattr(sub, "category_rel") and sub.category_rel:
                cat_name = sub.category_rel.name
            elif sub.category:
                cat_name = sub.category

            # Convert to report currency
            converted_amount = self._convert_amount(sub.amount, sub.currency)
            payment_mode = (
                sub.payment_mode.value
                if hasattr(sub, "payment_mode") and sub.payment_mode
                else None
            )
            monthly = self._to_monthly(converted_amount, sub.frequency.value, payment_mode)
            category_monthly[cat_name] = category_monthly.get(cat_name, Decimal("0")) + monthly

        # Filter out zero values
        category_monthly = {k: v for k, v in category_monthly.items() if v > 0}

        if not category_monthly:
            elements.append(
                Paragraph("No active recurring payments to analyze.", self.styles["ReportBody"])
            )
            elements.append(Spacer(1, 10))
            return elements

        # Sort by amount descending and limit to top 8
        sorted_categories = sorted(category_monthly.items(), key=lambda x: x[1], reverse=True)[:8]

        # Current month bar chart
        current_month = datetime.now().strftime("%B %Y")
        month_chart = self._build_horizontal_bar_chart(
            sorted_categories,
            f"Current Month Spending ({current_month})",
            self.currency_symbol,
        )
        if month_chart:
            elements.append(month_chart)
            elements.append(Spacer(1, 15))

        # Year-to-date bar chart (multiply monthly by months elapsed + current)
        today = datetime.now()
        months_elapsed = today.month  # Jan=1, so this gives months including current
        ytd_categories = [(name, amount * months_elapsed) for name, amount in sorted_categories]

        ytd_chart = self._build_horizontal_bar_chart(
            ytd_categories,
            f"Year-to-Date Spending ({today.year})",
            self.currency_symbol,
        )
        if ytd_chart:
            elements.append(ytd_chart)
            elements.append(Spacer(1, 20))

        return elements

    def _build_horizontal_bar_chart(
        self,
        data: list[tuple[str, Decimal]],
        title: str,
        currency_symbol: str,
    ) -> Drawing | None:
        """Build a horizontal bar chart for category spending.

        Creates a clean horizontal bar chart with category labels on the left
        and amounts on the right.

        Args:
            data: List of (category_name, amount) tuples.
            title: Chart title.
            currency_symbol: Currency symbol for labels.

        Returns:
            Drawing containing the bar chart, or None if no data.
        """
        if not data:
            return None

        # Calculate dimensions based on number of categories
        num_categories = len(data)
        bar_height = 20
        chart_height = num_categories * (bar_height + 8) + 40
        drawing_height = chart_height + 50
        drawing_width = 500

        drawing = Drawing(drawing_width, drawing_height)

        # Add title
        title_text = String(
            drawing_width / 2,
            drawing_height - 15,
            title,
            fontSize=11,
            textAnchor="middle",
        )
        title_text.fontName = "Helvetica-Bold"
        drawing.add(title_text)

        # Find max value for scaling
        max_value = float(max(amount for _, amount in data))
        if max_value <= 0:
            return None

        # Chart area dimensions
        left_margin = 120  # Space for category labels
        right_margin = 80  # Space for amount labels
        chart_width = drawing_width - left_margin - right_margin
        chart_top = drawing_height - 40

        # Draw bars
        for i, (category, amount) in enumerate(data):
            y = chart_top - (i + 1) * (bar_height + 8)
            bar_width = (float(amount) / max_value) * chart_width

            # Draw bar with gradient effect (main bar + highlight)
            color = CHART_COLORS[i % len(CHART_COLORS)]

            # Main bar
            bar = Rect(left_margin, y, bar_width, bar_height)
            bar.fillColor = color
            bar.strokeColor = None
            drawing.add(bar)

            # Highlight effect (lighter bar at top)
            if bar_width > 4:
                highlight = Rect(left_margin, y + bar_height - 4, bar_width, 4)
                highlight.fillColor = colors.Color(
                    min(color.red + 0.15, 1),
                    min(color.green + 0.15, 1),
                    min(color.blue + 0.15, 1),
                )
                highlight.strokeColor = None
                drawing.add(highlight)

            # Category label (left side)
            cat_label = category[:15] + "..." if len(category) > 15 else category
            label = String(
                left_margin - 5,
                y + bar_height / 2 - 3,
                cat_label,
                fontSize=9,
                textAnchor="end",
            )
            label.fontName = "Helvetica"
            drawing.add(label)

            # Amount label (right side)
            amount_str = f"{currency_symbol}{float(amount):,.2f}"
            amount_label = String(
                left_margin + bar_width + 5,
                y + bar_height / 2 - 3,
                amount_str,
                fontSize=9,
                textAnchor="start",
            )
            amount_label.fontName = "Helvetica-Bold"
            drawing.add(amount_label)

        # Draw baseline
        baseline = Line(
            left_margin,
            chart_top - num_categories * (bar_height + 8) - 5,
            left_margin,
            chart_top + 5,
        )
        baseline.strokeColor = colors.HexColor("#cccccc")
        baseline.strokeWidth = 1
        drawing.add(baseline)

        return drawing

    def _build_card_breakdown(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build spending breakdown by payment card.

        Groups payments by their assigned payment card and shows
        monthly and yearly totals for each card.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Spending by Payment Card", self.styles["SectionHeader"]))

        # Group by card - convert amounts to report currency
        card_totals: dict[str, Decimal] = {}
        card_names: dict[str, str] = {}  # Map card_id to display name

        for sub in subscriptions:
            if not sub.is_active:
                continue

            # Get card name or use "Unassigned"
            if hasattr(sub, "payment_card") and sub.payment_card:
                card_key = str(sub.card_id)
                card_names[card_key] = sub.payment_card.name
            else:
                card_key = "unassigned"
                card_names[card_key] = "Unassigned"

            # Convert to report currency before calculating monthly
            converted_amount = self._convert_amount(sub.amount, sub.currency)
            # Pass payment_mode to properly handle one-time payments
            payment_mode = (
                sub.payment_mode.value
                if hasattr(sub, "payment_mode") and sub.payment_mode
                else None
            )
            monthly = self._to_monthly(converted_amount, sub.frequency.value, payment_mode)
            card_totals[card_key] = card_totals.get(card_key, Decimal("0")) + monthly

        if not card_totals:
            elements.append(Paragraph("No active payments.", self.styles["ReportBody"]))
            elements.append(Spacer(1, 10))
            return elements

        # Sort by amount descending
        sorted_cards = sorted(card_totals.items(), key=lambda x: x[1], reverse=True)

        # Build table
        table_data = [["Payment Card", "Monthly", "Yearly"]]
        for card_key, monthly in sorted_cards:
            yearly = monthly * 12
            table_data.append(
                [
                    card_names.get(card_key, card_key)[:25],
                    f"{self.currency_symbol}{monthly:.2f}",
                    f"{self.currency_symbol}{yearly:.2f}",
                ]
            )

        # Add total row
        total_monthly = sum(card_totals.values())
        total_yearly = total_monthly * 12
        table_data.append(
            [
                "TOTAL",
                f"{self.currency_symbol}{total_monthly:.2f}",
                f"{self.currency_symbol}{total_yearly:.2f}",
            ]
        )

        card_table = Table(table_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch])
        card_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Total row
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    # All cells
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(card_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_upcoming_payments(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build upcoming payments section with overdue detection.

        Shows amounts converted to report currency with original amount in parentheses
        when currencies differ. Overdue payments are highlighted in red.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        date_range = self.date_range_days
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(
            Paragraph(
                f"Upcoming & Overdue Payments (Next {date_range} Days)",
                self.styles["SectionHeader"],
            )
        )

        # Filter to active with payment dates
        today = datetime.utcnow().date()
        upcoming = []
        overdue = []

        for sub in subscriptions:
            if not sub.is_active or not sub.next_payment_date:
                continue
            days_until = (sub.next_payment_date - today).days
            if days_until < 0:
                # Overdue payment
                overdue.append((sub, days_until))
            elif days_until <= date_range:
                # Upcoming payment within date range
                upcoming.append((sub, days_until))

        if not upcoming and not overdue:
            elements.append(
                Paragraph(
                    f"No upcoming or overdue payments in the next {date_range} days.",
                    self.styles["ReportBody"],
                )
            )
            elements.append(Spacer(1, 10))
            return elements

        # Sort overdue by most overdue first, upcoming by soonest first
        overdue.sort(key=lambda x: x[1])  # Most overdue (most negative) first
        upcoming.sort(key=lambda x: x[1])  # Soonest first

        # Combine: overdue first, then upcoming
        all_payments = overdue + upcoming

        # Build table with Status column
        table_data = [["Payment", "Date", "Amount", "Status"]]
        row_styles = []

        for i, (sub, days) in enumerate(all_payments[:15]):  # Limit to 15 for space
            date_str = sub.next_payment_date.strftime("%b %d, %Y") if sub.next_payment_date else ""
            # Use _get_amount_display for proper formatting with conversion
            amount_str = self._get_amount_display(sub.amount, sub.currency)

            # Determine status with color-coded urgency levels
            if days < 0:
                days_overdue = abs(days)
                if days_overdue == 1:
                    status_str = "⚠ 1 day overdue"
                else:
                    status_str = f"⚠ {days_overdue}d overdue"
                # Red background for overdue rows
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fee2e2"))
                )
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#dc2626")))
            elif days == 0:
                status_str = "⚡ Due Today"
                # Orange/amber background for due today
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#ffedd5"))
                )
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#ea580c")))
            elif days == 1:
                status_str = "⚡ Tomorrow"
                # Light orange background for tomorrow
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fff7ed"))
                )
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#ea580c")))
            elif days <= 3:
                status_str = f"○ In {days}d"
                # Light yellow background for within 3 days
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fefce8"))
                )
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#ca8a04")))
            elif days <= 7:
                status_str = f"○ In {days}d"
                # Light blue background for within a week
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#eff6ff"))
                )
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#2563eb")))
            else:
                status_str = f"In {days}d"
                # Green text for safe distance
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#16a34a")))

            table_data.append(
                [
                    sub.name[:30],  # Truncate long names
                    date_str,
                    amount_str,
                    status_str,
                ]
            )

        upcoming_table = Table(
            table_data, colWidths=[2.0 * inch, 1.1 * inch, 1.4 * inch, 1.2 * inch]
        )
        upcoming_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Dynamic row styles for overdue/urgent
                    *row_styles,
                    # All cells
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("ALIGN", (3, 0), (3, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(upcoming_table)

        # Add summary counts
        if overdue:
            overdue_text = f"<b>{len(overdue)} overdue payment(s)</b> require attention."
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(overdue_text, self.styles["ReportBody"]))

        elements.append(Spacer(1, 20))

        return elements

    def _build_payment_history(
        self, subscriptions: list["Subscription"], history_days: int = 30
    ) -> list[Paragraph | Spacer | Table]:
        """Build recent payment history section.

        Shows actual payments made from the payment_history relationship,
        sorted by most recent first.

        Args:
            subscriptions: List of subscriptions with payment_history loaded.
            history_days: Number of days of history to show (default 30).

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(
            Paragraph(f"Recent Payments (Last {history_days} Days)", self.styles["SectionHeader"])
        )

        # Collect all payment history from subscriptions
        today = datetime.utcnow().date()
        cutoff_date = today - timedelta(days=history_days)
        all_payments = []

        for sub in subscriptions:
            # Check if subscription has payment_history loaded
            if not hasattr(sub, "payment_history") or not sub.payment_history:
                continue

            for payment in sub.payment_history:
                if payment.payment_date >= cutoff_date:
                    all_payments.append((sub.name, payment))

        if not all_payments:
            elements.append(
                Paragraph(
                    f"No payments recorded in the last {history_days} days.",
                    self.styles["ReportBody"],
                )
            )
            elements.append(Spacer(1, 10))
            return elements

        # Sort by payment date, most recent first
        all_payments.sort(key=lambda x: x[1].payment_date, reverse=True)

        # Build table
        table_data = [["Date", "Payment", "Amount", "Status"]]

        # Status symbols
        status_symbols = {
            "completed": "✓",
            "pending": "⋯",
            "failed": "✗",
            "cancelled": "—",
        }

        for sub_name, payment in all_payments[:20]:  # Limit to 20 for space
            date_str = payment.payment_date.strftime("%b %d, %Y")
            amount_str = self._get_amount_display(payment.amount, payment.currency)
            status_val = (
                payment.status.value if hasattr(payment.status, "value") else str(payment.status)
            )
            status_symbol = status_symbols.get(status_val.lower(), "?")
            status_str = f"{status_symbol} {status_val.title()}"

            table_data.append(
                [
                    date_str,
                    sub_name[:25],
                    amount_str,
                    status_str,
                ]
            )

        history_table = Table(
            table_data, colWidths=[1.2 * inch, 2.2 * inch, 1.4 * inch, 1.0 * inch]
        )

        # Determine row styles based on status
        row_styles = []
        for i, (_, payment) in enumerate(all_payments[:20]):
            status_val = (
                payment.status.value if hasattr(payment.status, "value") else str(payment.status)
            )
            if status_val.lower() == "failed":
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#dc2626")))
            elif status_val.lower() == "completed":
                row_styles.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor("#16a34a")))

        history_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Dynamic status colors
                    *row_styles,
                    # Alternating row colors
                    *[
                        ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8f9fa"))
                        for i in range(2, len(table_data), 2)
                    ],
                    # Column alignment - Date: LEFT, Payment: LEFT, Amount: RIGHT, Status: CENTER
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("ALIGN", (3, 0), (3, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(history_table)

        # Summary of payment history
        completed_count = sum(
            1
            for _, p in all_payments
            if (p.status.value if hasattr(p.status, "value") else str(p.status)).lower()
            == "completed"
        )
        failed_count = sum(
            1
            for _, p in all_payments
            if (p.status.value if hasattr(p.status, "value") else str(p.status)).lower() == "failed"
        )

        if failed_count > 0:
            summary_text = (
                f"Total: {len(all_payments)} payments | "
                f"<font color='#16a34a'>{completed_count} completed</font> | "
                f"<font color='#dc2626'>{failed_count} failed</font>"
            )
        else:
            summary_text = f"Total: {len(all_payments)} payments, all completed successfully."

        elements.append(Spacer(1, 6))
        elements.append(Paragraph(summary_text, self.styles["ReportBody"]))
        elements.append(Spacer(1, 20))

        return elements

    def _build_debt_progress(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build debt progress tracking section.

        Shows all debt-type payments with total owed, remaining balance,
        paid amount, and progress percentage with visual progress bar.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        from src.models.subscription import PaymentMode, PaymentType

        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Debt Tracker", self.styles["SectionHeader"]))

        # Filter to debt payments only
        debts = []
        for sub in subscriptions:
            is_debt = sub.payment_mode == PaymentMode.DEBT or sub.payment_type == PaymentType.DEBT
            if is_debt and sub.total_owed and sub.total_owed > 0:
                debts.append(sub)

        if not debts:
            elements.append(Paragraph("No debt payments found.", self.styles["ReportBody"]))
            elements.append(Spacer(1, 10))
            return elements

        # Build table
        table_data = [["Debt Name", "Total Owed", "Paid", "Remaining", "Progress"]]
        total_owed_sum = Decimal("0")
        total_remaining_sum = Decimal("0")

        for debt in debts:
            total_owed = self._convert_amount(debt.total_owed, debt.currency)
            remaining = self._convert_amount(debt.remaining_balance or Decimal("0"), debt.currency)
            paid = total_owed - remaining
            percentage = debt.debt_paid_percentage or 0.0

            # Create text-based progress bar
            filled_blocks = int(percentage / 10)
            progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
            progress_str = f"{progress_bar} {percentage:.0f}%"

            creditor = f" ({debt.creditor})" if debt.creditor else ""
            name = f"{debt.name}{creditor}"[:30]

            table_data.append(
                [
                    name,
                    f"{self.currency_symbol}{total_owed:.2f}",
                    f"{self.currency_symbol}{paid:.2f}",
                    f"{self.currency_symbol}{remaining:.2f}",
                    progress_str,
                ]
            )

            total_owed_sum += total_owed
            total_remaining_sum += remaining

        # Add total row
        total_paid_sum = total_owed_sum - total_remaining_sum
        if total_owed_sum > 0:
            total_percentage = float(total_paid_sum / total_owed_sum) * 100
        else:
            total_percentage = 0.0
        filled = int(total_percentage / 10)
        total_progress = "█" * filled + "░" * (10 - filled)
        table_data.append(
            [
                "TOTAL",
                f"{self.currency_symbol}{total_owed_sum:.2f}",
                f"{self.currency_symbol}{total_paid_sum:.2f}",
                f"{self.currency_symbol}{total_remaining_sum:.2f}",
                f"{total_progress} {total_percentage:.0f}%",
            ]
        )

        debt_table = Table(
            table_data, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.3 * inch]
        )
        debt_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Total row
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    # All cells
                    ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                    ("ALIGN", (4, 1), (4, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(debt_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_savings_progress(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build savings goals progress section.

        Shows all savings-type payments with target amount, current saved,
        remaining to save, and progress percentage with visual progress bar.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        from src.models.subscription import PaymentMode, PaymentType

        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Savings Goals", self.styles["SectionHeader"]))

        # Filter to savings payments only
        savings = []
        for sub in subscriptions:
            is_savings = (
                sub.payment_mode == PaymentMode.SAVINGS or sub.payment_type == PaymentType.SAVINGS
            )
            if is_savings and sub.target_amount and sub.target_amount > 0:
                savings.append(sub)

        if not savings:
            elements.append(Paragraph("No savings goals found.", self.styles["ReportBody"]))
            elements.append(Spacer(1, 10))
            return elements

        # Build table
        table_data = [["Goal Name", "Target", "Saved", "Remaining", "Progress"]]
        total_target_sum = Decimal("0")
        total_saved_sum = Decimal("0")

        for goal in savings:
            target = self._convert_amount(goal.target_amount, goal.currency)
            saved = self._convert_amount(goal.current_saved or Decimal("0"), goal.currency)
            remaining = target - saved
            percentage = goal.savings_progress_percentage or 0.0

            # Create text-based progress bar
            filled_blocks = min(int(percentage / 10), 10)  # Cap at 10 for >100%
            progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
            progress_str = f"{progress_bar} {percentage:.0f}%"

            recipient = f" → {goal.recipient}" if goal.recipient else ""
            name = f"{goal.name}{recipient}"[:30]

            table_data.append(
                [
                    name,
                    f"{self.currency_symbol}{target:.2f}",
                    f"{self.currency_symbol}{saved:.2f}",
                    f"{self.currency_symbol}{remaining:.2f}",
                    progress_str,
                ]
            )

            total_target_sum += target
            total_saved_sum += saved

        # Add total row
        total_remaining = total_target_sum - total_saved_sum
        if total_target_sum > 0:
            total_percentage = float(total_saved_sum / total_target_sum) * 100
        else:
            total_percentage = 0.0
        filled = min(int(total_percentage / 10), 10)
        total_progress = "█" * filled + "░" * (10 - filled)
        table_data.append(
            [
                "TOTAL",
                f"{self.currency_symbol}{total_target_sum:.2f}",
                f"{self.currency_symbol}{total_saved_sum:.2f}",
                f"{self.currency_symbol}{total_remaining:.2f}",
                f"{total_progress} {total_percentage:.0f}%",
            ]
        )

        savings_table = Table(
            table_data, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.3 * inch]
        )
        savings_table.setStyle(
            TableStyle(
                [
                    # Header row - green theme for savings
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Total row
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    # All cells
                    ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                    ("ALIGN", (4, 1), (4, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(savings_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_budget_status(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build budget status section by category.

        Shows spending vs budget for each category that has a budget set,
        with visual indicators for on-track/over-budget status.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Budget Status", self.styles["SectionHeader"]))

        # Group spending by category and check budgets
        category_spending: dict[str, Decimal] = {}
        category_budgets: dict[str, Decimal] = {}

        for sub in subscriptions:
            if not sub.is_active:
                continue

            # Get category info
            cat_name = "Uncategorized"
            cat_budget = None

            if hasattr(sub, "category_rel") and sub.category_rel:
                cat_name = sub.category_rel.name
                if sub.category_rel.budget_amount:
                    cat_budget = sub.category_rel.budget_amount
            elif sub.category:
                cat_name = sub.category

            # Convert and sum spending
            converted = self._convert_amount(sub.amount, sub.currency)
            # Pass payment_mode to properly handle one-time payments
            payment_mode = (
                sub.payment_mode.value
                if hasattr(sub, "payment_mode") and sub.payment_mode
                else None
            )
            monthly = self._to_monthly(converted, sub.frequency.value, payment_mode)
            category_spending[cat_name] = category_spending.get(cat_name, Decimal("0")) + monthly

            # Store budget if available
            if cat_budget and cat_name not in category_budgets:
                category_budgets[cat_name] = cat_budget

        # Filter to categories with budgets
        budgeted_categories = {k: v for k, v in category_spending.items() if k in category_budgets}

        if not budgeted_categories:
            elements.append(
                Paragraph(
                    "No category budgets configured. Set budgets in Settings → Categories.",
                    self.styles["ReportBody"],
                )
            )
            elements.append(Spacer(1, 10))
            return elements

        # Build table
        table_data = [["Category", "Budget", "Spent", "Remaining", "Status"]]
        row_styles = []

        for i, (cat_name, spent) in enumerate(sorted(budgeted_categories.items())):
            budget = category_budgets[cat_name]
            remaining = budget - spent
            percentage = float(spent / budget) * 100 if budget > 0 else 0

            # Determine status
            if percentage > 100:
                status = "⚠ OVER"
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fee2e2"))
                )
                row_styles.append(("TEXTCOLOR", (4, i + 1), (4, i + 1), colors.HexColor("#dc2626")))
            elif percentage > 90:
                status = "⚡ WARNING"
                row_styles.append(
                    ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fff3cd"))
                )
                row_styles.append(("TEXTCOLOR", (4, i + 1), (4, i + 1), colors.HexColor("#d97706")))
            else:
                status = "✓ OK"
                row_styles.append(("TEXTCOLOR", (4, i + 1), (4, i + 1), colors.HexColor("#16a34a")))

            table_data.append(
                [
                    cat_name[:20],
                    f"{self.currency_symbol}{budget:.2f}",
                    f"{self.currency_symbol}{spent:.2f}",
                    f"{self.currency_symbol}{remaining:.2f}",
                    status,
                ]
            )

        budget_table = Table(
            table_data, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.2 * inch]
        )
        budget_table.setStyle(
            TableStyle(
                [
                    # Header row - blue theme
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Dynamic row styles for over/warning/ok
                    *row_styles,
                    # All cells
                    ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(budget_table)

        # Summary
        over_count = sum(
            1 for s, b in zip(category_spending.values(), category_budgets.values()) if s > b
        )
        if over_count > 0:
            elements.append(Spacer(1, 6))
            elements.append(
                Paragraph(
                    f"<b>{over_count} category/categories over budget</b> - review spending.",
                    self.styles["ReportBody"],
                )
            )

        elements.append(Spacer(1, 20))

        return elements

    def _build_payments_table(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table | PageBreak]:
        """Build full payments table with currency column.

        Shows each payment with its original currency and converted amount
        when different from the report currency.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table | PageBreak] = []
        elements.append(PageBreak())
        elements.append(Paragraph("All Payments", self.styles["SectionHeader"]))

        if not subscriptions:
            elements.append(Paragraph("No payments found.", self.styles["ReportBody"]))
            return elements

        # Sort by category then name
        def get_category_name(s: "Subscription") -> str:
            if hasattr(s, "category_rel") and s.category_rel:
                return s.category_rel.name
            elif s.category:
                return s.category
            return "ZZZ"

        sorted_subs = sorted(
            subscriptions,
            key=lambda s: (get_category_name(s), s.name.lower()),
        )

        # Build table with Currency column
        table_data = [["Name", "Amount", "Currency", "Frequency", "Category", "Status"]]
        status_styles = []  # For status column color coding

        for idx, sub in enumerate(sorted_subs):
            cat_name = get_category_name(sub) if get_category_name(sub) != "ZZZ" else "-"
            # Status with symbol
            if sub.is_active:
                status = "✓ Active"
                status_styles.append(
                    ("TEXTCOLOR", (5, idx + 1), (5, idx + 1), colors.HexColor("#16a34a"))
                )
            else:
                status = "○ Inactive"
                status_styles.append(
                    ("TEXTCOLOR", (5, idx + 1), (5, idx + 1), colors.HexColor("#9ca3af"))
                )
            # Show converted amount with original if different
            amount_str = self._get_amount_display(sub.amount, sub.currency, show_original=False)
            # Show original currency
            currency_display = sub.currency.upper()
            if sub.currency.upper() != self.currency:
                original_symbol = CURRENCY_SYMBOLS.get(sub.currency.upper(), sub.currency)
                currency_display = f"{sub.currency} ({original_symbol}{sub.amount:.2f})"
            table_data.append(
                [
                    sub.name[:22],
                    amount_str,
                    currency_display[:18],
                    sub.frequency.value.title(),
                    cat_name[:12],
                    status,
                ]
            )

        payments_table = Table(
            table_data,
            colWidths=[1.8 * inch, 0.9 * inch, 1.2 * inch, 0.9 * inch, 1.0 * inch, 0.7 * inch],
        )
        payments_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Alternating row colors
                    *[
                        ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8f9fa"))
                        for i in range(2, len(table_data), 2)
                    ],
                    # Inactive rows have lighter text (except status column)
                    *[
                        ("TEXTCOLOR", (0, i + 1), (4, i + 1), colors.HexColor("#9ca3af"))
                        for i, sub in enumerate(sorted_subs)
                        if not sub.is_active
                    ],
                    # Status column colors
                    *status_styles,
                    # All cells
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ALIGN", (5, 0), (5, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(payments_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_footer(self) -> list[Spacer | Paragraph]:
        """Build report footer with currency conversion note.

        Returns:
            List of flowable elements.
        """
        elements: list[Spacer | Paragraph] = []
        elements.append(Spacer(1, 30))

        footer_text = (
            "Generated by Money Flow | "
            f"Report Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        elements.append(Paragraph(footer_text, self.styles["Footer"]))

        # Add note about currency conversions if any occurred
        if self._failed_conversions:
            failed_note = (
                f"<br/><i>Note: Currency conversion unavailable for: "
                f"{', '.join(sorted(self._failed_conversions))}. "
                "Amounts shown in original currency.</i>"
            )
            elements.append(Paragraph(failed_note, self.styles["Footer"]))
        elif self.currency_service:
            currency_note = (
                f"<br/><i>All amounts converted to {self.currency} using live exchange rates.</i>"
            )
            elements.append(Paragraph(currency_note, self.styles["Footer"]))

        return elements

    def _to_monthly(
        self, amount: Decimal, frequency: str, payment_mode: str | None = None
    ) -> Decimal:
        """Convert amount to monthly equivalent.

        Args:
            amount: Payment amount.
            frequency: Payment frequency (daily, weekly, monthly, yearly).
            payment_mode: Payment mode (recurring, one_time, debt, savings).
                If one_time, returns 0 regardless of frequency.

        Returns:
            Monthly equivalent amount.
        """
        # One-time payments should not be included in monthly totals
        if payment_mode and payment_mode.lower() == "one_time":
            return Decimal("0")

        frequency_multipliers = {
            "daily": Decimal("30"),
            "weekly": Decimal("4.33"),
            "biweekly": Decimal("2.17"),
            "monthly": Decimal("1"),
            "quarterly": Decimal("0.33"),
            "yearly": Decimal("0.083"),
            "one-time": Decimal("0"),
            "custom": Decimal("1"),  # Default to monthly for custom
        }
        multiplier = frequency_multipliers.get(frequency.lower(), Decimal("1"))
        return amount * multiplier
