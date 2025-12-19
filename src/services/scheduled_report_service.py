"""Scheduled Report Service.

This module provides scheduled report generation and delivery.
Reports can be sent on a daily, weekly, or monthly schedule.
"""

import logging
from datetime import date, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from src.services.email_service import EmailService
from src.services.pdf_report_service import PDFReportService

if TYPE_CHECKING:
    from src.models.subscription import Subscription

logger = logging.getLogger(__name__)


class ReportFrequency(str, Enum):
    """Report delivery frequency."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportType(str, Enum):
    """Type of report to generate."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    UPCOMING = "upcoming"


class ScheduledReportService:
    """Service for generating and delivering scheduled reports.

    Generates PDF reports on a schedule and delivers them via email.

    Attributes:
        email_service: EmailService for sending reports.
        pdf_service: PDFReportService for generating reports.

    Example:
        >>> service = ScheduledReportService()
        >>> await service.send_weekly_report(
        ...     user_email="user@example.com",
        ...     subscriptions=[...],
        ... )
        True
    """

    def __init__(
        self,
        email_service: EmailService | None = None,
        pdf_service: PDFReportService | None = None,
    ):
        """Initialize ScheduledReportService.

        Args:
            email_service: EmailService instance (defaults to new instance).
            pdf_service: PDFReportService instance (defaults to new instance).
        """
        self.email_service = email_service or EmailService()
        self.pdf_service = pdf_service or PDFReportService()

    @property
    def is_configured(self) -> bool:
        """Check if the service is configured.

        Returns:
            True if email service is configured.
        """
        return self.email_service.is_configured

    async def send_daily_report(
        self,
        user_email: str,
        subscriptions: list["Subscription"],
        currency: str = "GBP",
    ) -> bool:
        """Send a daily summary report.

        Args:
            user_email: Recipient email address.
            subscriptions: List of user's subscriptions.
            currency: Currency code for the report.

        Returns:
            True if report sent successfully.
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping report")
            return False

        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Filter today's and tomorrow's payments
        today_payments = [
            s
            for s in subscriptions
            if s.is_active and s.next_payment_date and s.next_payment_date == today
        ]
        tomorrow_payments = [
            s
            for s in subscriptions
            if s.is_active and s.next_payment_date and s.next_payment_date == tomorrow
        ]

        # Generate PDF report
        pdf_bytes = self.pdf_service.generate_report(
            subscriptions=subscriptions,
            title=f"Daily Payment Report - {today.strftime('%d %B %Y')}",
            currency=currency,
            include_charts=False,  # Keep daily report simple
        )

        # Build email subject
        payment_count = len(today_payments) + len(tomorrow_payments)
        subject = f"📊 Daily Report: {payment_count} payment(s) coming up"

        # Build email body
        html_body = self._build_daily_email_html(
            today_payments=today_payments,
            tomorrow_payments=tomorrow_payments,
            currency=currency,
        )

        # Send email with PDF attachment
        return await self.email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            attachments=[
                {
                    "filename": f"daily_report_{today.strftime('%Y-%m-%d')}.pdf",
                    "content": pdf_bytes,
                    "content_type": "application/pdf",
                }
            ],
        )

    async def send_weekly_report(
        self,
        user_email: str,
        subscriptions: list["Subscription"],
        currency: str = "GBP",
    ) -> bool:
        """Send a weekly summary report.

        Args:
            user_email: Recipient email address.
            subscriptions: List of user's subscriptions.
            currency: Currency code for the report.

        Returns:
            True if report sent successfully.
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping report")
            return False

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Filter this week's payments
        week_payments = [
            s
            for s in subscriptions
            if s.is_active and s.next_payment_date and week_start <= s.next_payment_date <= week_end
        ]

        # Calculate total
        total = sum(float(s.amount) for s in week_payments)

        # Generate PDF report
        pdf_bytes = self.pdf_service.generate_report(
            subscriptions=subscriptions,
            title=f"Weekly Report - Week of {week_start.strftime('%d %B %Y')}",
            currency=currency,
            include_charts=True,
        )

        # Build email subject
        subject = f"📅 Weekly Report: {len(week_payments)} payments this week"

        # Build email body
        html_body = self._build_weekly_email_html(
            week_payments=week_payments,
            total=total,
            week_start=week_start,
            week_end=week_end,
            currency=currency,
        )

        # Send email with PDF attachment
        return await self.email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            attachments=[
                {
                    "filename": f"weekly_report_{week_start.strftime('%Y-%m-%d')}.pdf",
                    "content": pdf_bytes,
                    "content_type": "application/pdf",
                }
            ],
        )

    async def send_monthly_report(
        self,
        user_email: str,
        subscriptions: list["Subscription"],
        currency: str = "GBP",
    ) -> bool:
        """Send a monthly summary report.

        Args:
            user_email: Recipient email address.
            subscriptions: List of user's subscriptions.
            currency: Currency code for the report.

        Returns:
            True if report sent successfully.
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping report")
            return False

        today = date.today()
        month_start = today.replace(day=1)
        # Calculate last day of month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        month_end = next_month - timedelta(days=1)

        # Filter this month's payments
        month_payments = [
            s
            for s in subscriptions
            if s.is_active
            and s.next_payment_date
            and month_start <= s.next_payment_date <= month_end
        ]

        # Calculate totals by category
        category_totals = self._calculate_category_totals(month_payments)
        total = sum(float(s.amount) for s in month_payments)

        # Generate PDF report
        pdf_bytes = self.pdf_service.generate_report(
            subscriptions=subscriptions,
            title=f"Monthly Report - {month_start.strftime('%B %Y')}",
            currency=currency,
            include_charts=True,
        )

        # Build email subject
        subject = f"📊 Monthly Report: {month_start.strftime('%B %Y')}"

        # Build email body
        html_body = self._build_monthly_email_html(
            month_payments=month_payments,
            category_totals=category_totals,
            total=total,
            month_name=month_start.strftime("%B %Y"),
            currency=currency,
        )

        # Send email with PDF attachment
        return await self.email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            attachments=[
                {
                    "filename": f"monthly_report_{month_start.strftime('%Y-%m')}.pdf",
                    "content": pdf_bytes,
                    "content_type": "application/pdf",
                }
            ],
        )

    def _calculate_category_totals(self, subscriptions: list["Subscription"]) -> dict[str, float]:
        """Calculate total spending by category.

        Args:
            subscriptions: List of subscriptions.

        Returns:
            Dict mapping category to total amount.
        """
        totals: dict[str, float] = {}
        for sub in subscriptions:
            category = sub.category or "Uncategorized"
            totals[category] = totals.get(category, 0.0) + float(sub.amount)
        return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))

    def _get_currency_symbol(self, currency: str) -> str:
        """Get currency symbol for a currency code.

        Args:
            currency: Currency code (GBP, USD, EUR, UAH).

        Returns:
            Currency symbol.
        """
        symbols = {
            "GBP": "£",
            "USD": "$",
            "EUR": "€",
            "UAH": "₴",
        }
        return symbols.get(currency, "£")

    def _build_daily_email_html(
        self,
        today_payments: list["Subscription"],
        tomorrow_payments: list["Subscription"],
        currency: str,
    ) -> str:
        """Build HTML email body for daily report.

        Args:
            today_payments: Payments due today.
            tomorrow_payments: Payments due tomorrow.
            currency: Currency code.

        Returns:
            HTML email body.
        """
        symbol = self._get_currency_symbol(currency)
        today = date.today()

        def format_payment_list(payments: list, title: str, emoji: str) -> str:
            if not payments:
                return ""
            total = sum(float(p.amount) for p in payments)
            items_html = ""
            for p in payments:
                items_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{p.name}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{symbol}{float(p.amount):.2f}</td>
                </tr>
                """
            return f"""
            <h3 style="color: #1f2937; margin-top: 24px;">{emoji} {title}</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                <thead>
                    <tr style="background-color: #f3f4f6;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Name</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr style="background-color: #f9fafb; font-weight: bold;">
                        <td style="padding: 8px;">Total</td>
                        <td style="padding: 8px; text-align: right;">{symbol}{total:.2f}</td>
                    </tr>
                </tfoot>
            </table>
            """

        today_section = format_payment_list(today_payments, "Due Today", "💳")
        tomorrow_section = format_payment_list(tomorrow_payments, "Due Tomorrow", "📅")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #374151;">
            <h1 style="color: #1f2937;">📊 Daily Payment Report</h1>
            <p style="color: #6b7280;">{today.strftime("%A, %d %B %Y")}</p>

            {today_section if today_section else '<p style="color: #6b7280;">No payments due today.</p>'}
            {tomorrow_section if tomorrow_section else '<p style="color: #6b7280;">No payments due tomorrow.</p>'}

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
            <p style="color: #9ca3af; font-size: 14px;">
                See the attached PDF for your full subscription overview.<br>
                <em>Money Flow - Your Personal Finance Tracker</em>
            </p>
        </body>
        </html>
        """

    def _build_weekly_email_html(
        self,
        week_payments: list["Subscription"],
        total: float,
        week_start: date,
        week_end: date,
        currency: str,
    ) -> str:
        """Build HTML email body for weekly report.

        Args:
            week_payments: Payments due this week.
            total: Total amount due.
            week_start: Start of the week.
            week_end: End of the week.
            currency: Currency code.

        Returns:
            HTML email body.
        """
        symbol = self._get_currency_symbol(currency)

        # Group by day
        day_groups: dict[date, list] = {}
        for p in week_payments:
            if p.next_payment_date:
                day = p.next_payment_date
                if day not in day_groups:
                    day_groups[day] = []
                day_groups[day].append(p)

        days_html = ""
        for day in sorted(day_groups.keys()):
            payments = day_groups[day]
            day_total = sum(float(p.amount) for p in payments)
            items = ", ".join(p.name for p in payments)
            days_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{day.strftime("%A, %d %b")}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{items}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{symbol}{day_total:.2f}</td>
            </tr>
            """

        if not days_html:
            days_html = """
            <tr>
                <td colspan="3" style="padding: 16px; text-align: center; color: #6b7280;">No payments scheduled this week</td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #374151;">
            <h1 style="color: #1f2937;">📅 Weekly Report</h1>
            <p style="color: #6b7280;">{week_start.strftime("%d %B")} - {week_end.strftime("%d %B %Y")}</p>

            <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h2 style="margin: 0; color: #1f2937;">{symbol}{total:.2f}</h2>
                <p style="margin: 4px 0 0 0; color: #6b7280;">Total this week ({len(week_payments)} payment(s))</p>
            </div>

            <h3 style="color: #1f2937;">Payment Schedule</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f3f4f6;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Day</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Payments</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {days_html}
                </tbody>
            </table>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
            <p style="color: #9ca3af; font-size: 14px;">
                See the attached PDF for detailed charts and breakdowns.<br>
                <em>Money Flow - Your Personal Finance Tracker</em>
            </p>
        </body>
        </html>
        """

    def _build_monthly_email_html(
        self,
        month_payments: list["Subscription"],
        category_totals: dict[str, float],
        total: float,
        month_name: str,
        currency: str,
    ) -> str:
        """Build HTML email body for monthly report.

        Args:
            month_payments: Payments due this month.
            category_totals: Total by category.
            total: Total amount due.
            month_name: Name of the month.
            currency: Currency code.

        Returns:
            HTML email body.
        """
        symbol = self._get_currency_symbol(currency)

        # Category breakdown
        categories_html = ""
        for category, cat_total in category_totals.items():
            percentage = (cat_total / total * 100) if total > 0 else 0
            categories_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{category}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{symbol}{cat_total:.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">{percentage:.1f}%</td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #374151;">
            <h1 style="color: #1f2937;">📊 Monthly Report</h1>
            <p style="color: #6b7280;">{month_name}</p>

            <div style="background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h2 style="margin: 0; color: #1f2937;">{symbol}{total:.2f}</h2>
                <p style="margin: 4px 0 0 0; color: #6b7280;">Total this month ({len(month_payments)} payment(s))</p>
            </div>

            <h3 style="color: #1f2937;">Spending by Category</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f3f4f6;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Category</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Amount</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">%</th>
                    </tr>
                </thead>
                <tbody>
                    {categories_html}
                </tbody>
            </table>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
            <p style="color: #9ca3af; font-size: 14px;">
                See the attached PDF for the full report with charts.<br>
                <em>Money Flow - Your Personal Finance Tracker</em>
            </p>
        </body>
        </html>
        """


# Global service instance
_scheduled_report_service: ScheduledReportService | None = None


def get_scheduled_report_service() -> ScheduledReportService:
    """Get the global ScheduledReportService instance.

    Returns:
        ScheduledReportService singleton instance.
    """
    global _scheduled_report_service
    if _scheduled_report_service is None:
        _scheduled_report_service = ScheduledReportService()
    return _scheduled_report_service
