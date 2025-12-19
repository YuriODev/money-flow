"""PDF Report Generation Service.

This module provides PDF report generation for subscription/payment data
using ReportLab. Reports include summaries, payment lists, and visual charts.
"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING

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


class PDFReportService:
    """Service for generating PDF reports of subscription/payment data.

    Generates professional PDF reports with:
    - Summary statistics
    - Payment lists by category
    - Monthly spending breakdown
    - Upcoming payments section
    """

    def __init__(
        self,
        page_size: str = "a4",
        include_inactive: bool = False,
        currency: str = "GBP",
    ):
        """Initialize PDF report service.

        Args:
            page_size: Page size ('a4' or 'letter').
            include_inactive: Whether to include inactive subscriptions.
            currency: Primary display currency.
        """
        self.page_size = PAGE_SIZES.get(page_size.lower(), A4)
        self.include_inactive = include_inactive
        self.currency = currency
        self.currency_symbol = CURRENCY_SYMBOLS.get(currency, "£")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

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

        # Title and header
        elements.extend(self._build_header(report_title, user_email))

        # Summary section
        elements.extend(self._build_summary(subscriptions))

        # Payment breakdown by category
        elements.extend(self._build_category_breakdown(subscriptions))

        # Upcoming payments
        elements.extend(self._build_upcoming_payments(subscriptions))

        # All payments table
        elements.extend(self._build_payments_table(subscriptions))

        # Footer
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

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Summary", self.styles["SectionHeader"]))

        # Calculate totals
        active_count = sum(1 for s in subscriptions if s.is_active)
        inactive_count = len(subscriptions) - active_count

        monthly_total = Decimal("0")
        yearly_total = Decimal("0")

        for sub in subscriptions:
            if not sub.is_active:
                continue
            monthly = self._to_monthly(sub.amount, sub.frequency.value)
            monthly_total += monthly
            yearly_total += monthly * 12

        # Summary table
        summary_data = [
            ["Active Payments", str(active_count)],
            ["Inactive Payments", str(inactive_count)],
            ["Monthly Total", f"{self.currency_symbol}{monthly_total:.2f}"],
            ["Yearly Total", f"{self.currency_symbol}{yearly_total:.2f}"],
        ]

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
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build spending breakdown by category.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Spending by Category", self.styles["SectionHeader"]))

        # Group by category
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
            monthly = self._to_monthly(sub.amount, sub.frequency.value)
            category_totals[cat_name] = category_totals.get(cat_name, Decimal("0")) + monthly

        if not category_totals:
            elements.append(Paragraph("No active payments.", self.styles["ReportBody"]))
            elements.append(Spacer(1, 10))
            return elements

        # Sort by amount descending
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

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

    def _build_upcoming_payments(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table]:
        """Build upcoming payments section.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            List of flowable elements.
        """
        elements: list[Paragraph | Spacer | Table] = []
        elements.append(Paragraph("Upcoming Payments (Next 30 Days)", self.styles["SectionHeader"]))

        # Filter to active with upcoming dates
        today = datetime.utcnow().date()
        upcoming = []
        for sub in subscriptions:
            if not sub.is_active or not sub.next_payment_date:
                continue
            days_until = (sub.next_payment_date - today).days
            if 0 <= days_until <= 30:
                upcoming.append((sub, days_until))

        if not upcoming:
            elements.append(
                Paragraph("No upcoming payments in the next 30 days.", self.styles["ReportBody"])
            )
            elements.append(Spacer(1, 10))
            return elements

        # Sort by date
        upcoming.sort(key=lambda x: x[1])

        # Build table
        table_data = [["Payment", "Date", "Amount", "Days"]]
        for sub, days in upcoming[:15]:  # Limit to 15 for space
            date_str = sub.next_payment_date.strftime("%b %d, %Y") if sub.next_payment_date else ""
            days_str = "Today" if days == 0 else f"{days}d"
            table_data.append(
                [
                    sub.name[:30],  # Truncate long names
                    date_str,
                    f"{self.currency_symbol}{sub.amount:.2f}",
                    days_str,
                ]
            )

        upcoming_table = Table(
            table_data, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch]
        )
        upcoming_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    # Highlight urgent (today or tomorrow)
                    *[
                        ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#fff3cd"))
                        for i, (_, days) in enumerate(upcoming[:15])
                        if days <= 1
                    ],
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
        elements.append(Spacer(1, 20))

        return elements

    def _build_payments_table(
        self, subscriptions: list["Subscription"]
    ) -> list[Paragraph | Spacer | Table | PageBreak]:
        """Build full payments table.

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

        # Build table
        table_data = [["Name", "Amount", "Frequency", "Category", "Status"]]
        for sub in sorted_subs:
            cat_name = get_category_name(sub) if get_category_name(sub) != "ZZZ" else "-"
            status = "Active" if sub.is_active else "Inactive"
            table_data.append(
                [
                    sub.name[:25],
                    f"{self.currency_symbol}{sub.amount:.2f}",
                    sub.frequency.value.title(),
                    cat_name[:15],
                    status,
                ]
            )

        payments_table = Table(
            table_data,
            colWidths=[2.2 * inch, 1 * inch, 1 * inch, 1.2 * inch, 0.8 * inch],
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
                    # Inactive rows grayed out
                    *[
                        ("TEXTCOLOR", (0, i + 1), (-1, i + 1), colors.gray)
                        for i, sub in enumerate(sorted_subs)
                        if not sub.is_active
                    ],
                    # All cells
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]
            )
        )

        elements.append(payments_table)
        elements.append(Spacer(1, 20))

        return elements

    def _build_footer(self) -> list[Spacer | Paragraph]:
        """Build report footer.

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
        return elements

    def _to_monthly(self, amount: Decimal, frequency: str) -> Decimal:
        """Convert amount to monthly equivalent.

        Args:
            amount: Payment amount.
            frequency: Payment frequency (daily, weekly, monthly, yearly).

        Returns:
            Monthly equivalent amount.
        """
        frequency_multipliers = {
            "daily": Decimal("30"),
            "weekly": Decimal("4.33"),
            "biweekly": Decimal("2.17"),
            "monthly": Decimal("1"),
            "quarterly": Decimal("0.33"),
            "yearly": Decimal("0.083"),
            "one-time": Decimal("0"),
        }
        multiplier = frequency_multipliers.get(frequency.lower(), Decimal("1"))
        return amount * multiplier
