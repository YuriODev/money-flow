"""Email notification service for payment reminders.

This module provides the EmailService class for sending payment reminders
and notifications via email. Supports SMTP with TLS/SSL.

Features:
- Payment reminder emails
- Daily/weekly digest emails
- HTML formatted emails with styling
- Async email sending via aiosmtplib
"""

import logging
from datetime import date
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib

from src.core.config import settings

if TYPE_CHECKING:
    from src.models.subscription import Subscription

logger = logging.getLogger(__name__)

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "UAH": "₴",
}


class EmailService:
    """Service for sending email notifications.

    Handles sending payment reminders, daily/weekly digests via email.
    Uses SMTP with TLS for secure delivery.

    Attributes:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_user: SMTP username for authentication.
        smtp_password: SMTP password for authentication.
        from_email: Sender email address.
        from_name: Sender display name.

    Example:
        >>> service = EmailService()
        >>> await service.send_reminder("user@example.com", subscription, days_until=3)
        True
    """

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_email: str | None = None,
        from_name: str = "Money Flow",
    ):
        """Initialize EmailService.

        Args:
            smtp_host: SMTP server hostname (defaults to config).
            smtp_port: SMTP server port (defaults to config).
            smtp_user: SMTP username (defaults to config).
            smtp_password: SMTP password (defaults to config).
            from_email: Sender email address (defaults to config).
            from_name: Sender display name.
        """
        self.smtp_host = smtp_host or getattr(settings, "smtp_host", "")
        self.smtp_port = smtp_port or getattr(settings, "smtp_port", 587)
        self.smtp_user = smtp_user or getattr(settings, "smtp_user", "")
        self.smtp_password = smtp_password or getattr(settings, "smtp_password", "")
        self.from_email = from_email or getattr(settings, "smtp_from_email", "")
        self.from_name = from_name

    @property
    def is_configured(self) -> bool:
        """Check if email service is configured.

        Returns:
            True if SMTP settings are configured.
        """
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_body: HTML formatted email body.
            text_body: Plain text fallback (optional).

        Returns:
            True if email sent successfully, False otherwise.
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping send")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add plain text part (fallback)
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # Add HTML part
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_reminder(
        self,
        to_email: str,
        subscription: "Subscription",
        days_until: int,
    ) -> bool:
        """Send a payment reminder email.

        Args:
            to_email: Recipient email address.
            subscription: Subscription object for the reminder.
            days_until: Number of days until payment is due.

        Returns:
            True if email sent successfully.
        """
        # Determine urgency and styling
        if days_until < 0:
            urgency = "overdue"
            urgency_text = f"{abs(days_until)} days overdue"
            color = "#dc2626"  # Red
        elif days_until == 0:
            urgency = "today"
            urgency_text = "Due today"
            color = "#f59e0b"  # Orange
        elif days_until == 1:
            urgency = "tomorrow"
            urgency_text = "Due tomorrow"
            color = "#f59e0b"  # Orange
        else:
            urgency = "upcoming"
            urgency_text = f"Due in {days_until} days"
            color = "#3b82f6"  # Blue

        # Get currency symbol
        currency_symbol = CURRENCY_SYMBOLS.get(subscription.currency, "£")
        amount = f"{currency_symbol}{subscription.amount:.2f}"

        # Build subject
        if urgency == "overdue":
            subject = f"⚠️ Overdue: {subscription.name} payment is {abs(days_until)} days late"
        elif urgency == "today":
            subject = f"💳 Payment Due Today: {subscription.name} - {amount}"
        else:
            subject = f"📅 Upcoming Payment: {subscription.name} - {amount} ({urgency_text})"

        # Build HTML body
        html_body = self._build_reminder_html(
            subscription=subscription,
            amount=amount,
            urgency_text=urgency_text,
            color=color,
        )

        # Plain text fallback
        text_body = (
            f"Payment Reminder: {subscription.name}\n\n"
            f"Amount: {amount}\n"
            f"Status: {urgency_text}\n"
            f"Frequency: {subscription.frequency.value.title()}\n\n"
            f"--\nMoney Flow - Your payment tracking assistant"
        )

        return await self.send_email(to_email, subject, html_body, text_body)

    async def send_daily_digest(
        self,
        to_email: str,
        subscriptions: list["Subscription"],
        currency: str = "GBP",
    ) -> bool:
        """Send a daily payment digest email.

        Args:
            to_email: Recipient email address.
            subscriptions: List of upcoming subscriptions.
            currency: Display currency for totals.

        Returns:
            True if email sent successfully.
        """
        if not subscriptions:
            return False

        currency_symbol = CURRENCY_SYMBOLS.get(currency, "£")
        today = date.today()

        # Calculate totals
        total = sum(s.amount for s in subscriptions)
        today_payments = [s for s in subscriptions if s.next_payment_date == today]
        week_payments = [
            s for s in subscriptions if s.next_payment_date and s.next_payment_date > today
        ]

        subject = f"📊 Daily Digest: {len(subscriptions)} payments this week ({currency_symbol}{total:.2f})"

        html_body = self._build_digest_html(
            subscriptions=subscriptions,
            today_payments=today_payments,
            week_payments=week_payments,
            currency_symbol=currency_symbol,
            total=total,
            period="Daily",
        )

        text_body = (
            f"Daily Payment Digest\n\n"
            f"Total: {currency_symbol}{total:.2f}\n"
            f"Payments today: {len(today_payments)}\n"
            f"Payments this week: {len(week_payments)}\n\n"
            f"--\nMoney Flow"
        )

        return await self.send_email(to_email, subject, html_body, text_body)

    async def send_weekly_digest(
        self,
        to_email: str,
        subscriptions: list["Subscription"],
        currency: str = "GBP",
    ) -> bool:
        """Send a weekly payment digest email.

        Args:
            to_email: Recipient email address.
            subscriptions: List of upcoming subscriptions for the week.
            currency: Display currency for totals.

        Returns:
            True if email sent successfully.
        """
        if not subscriptions:
            return False

        currency_symbol = CURRENCY_SYMBOLS.get(currency, "£")
        today = date.today()

        # Calculate totals
        total = sum(s.amount for s in subscriptions)

        subject = f"📅 Weekly Summary: {len(subscriptions)} payments ({currency_symbol}{total:.2f})"

        html_body = self._build_digest_html(
            subscriptions=subscriptions,
            today_payments=[s for s in subscriptions if s.next_payment_date == today],
            week_payments=subscriptions,
            currency_symbol=currency_symbol,
            total=total,
            period="Weekly",
        )

        text_body = (
            f"Weekly Payment Summary\n\n"
            f"Total: {currency_symbol}{total:.2f}\n"
            f"Payments: {len(subscriptions)}\n\n"
            f"--\nMoney Flow"
        )

        return await self.send_email(to_email, subject, html_body, text_body)

    async def send_test_notification(self, to_email: str) -> bool:
        """Send a test notification email.

        Args:
            to_email: Recipient email address.

        Returns:
            True if email sent successfully.
        """
        subject = "✅ Money Flow Email Test"
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                         color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }
                .success { color: #059669; font-size: 24px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Money Flow</h1>
                </div>
                <div class="content">
                    <div class="success">✅ Email notifications are working!</div>
                    <p>Your email notifications are now configured correctly.</p>
                    <p>You'll receive payment reminders and digests at this email address.</p>
                </div>
            </div>
        </body>
        </html>
        """
        text_body = "Money Flow Email Test\n\nEmail notifications are working correctly!"

        return await self.send_email(to_email, subject, html_body, text_body)

    def _build_reminder_html(
        self,
        subscription: "Subscription",
        amount: str,
        urgency_text: str,
        color: str,
    ) -> str:
        """Build HTML for reminder email.

        Args:
            subscription: Subscription object.
            amount: Formatted amount string.
            urgency_text: Status text (e.g., "Due tomorrow").
            color: Status color hex code.

        Returns:
            HTML string for the email body.
        """
        date_str = ""
        if subscription.next_payment_date:
            date_str = subscription.next_payment_date.strftime("%B %d, %Y")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       margin: 0; padding: 0; background: #f3f4f6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 8px 8px;
                           box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .status {{ display: inline-block; padding: 8px 16px; border-radius: 20px;
                          color: white; font-weight: 600; margin-bottom: 20px; }}
                .amount {{ font-size: 36px; font-weight: 700; color: #1f2937; margin: 20px 0; }}
                .details {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0;
                              border-bottom: 1px solid #e5e7eb; }}
                .detail-row:last-child {{ border-bottom: none; }}
                .label {{ color: #6b7280; }}
                .value {{ font-weight: 600; color: #1f2937; }}
                .footer {{ text-align: center; padding: 20px; color: #9ca3af; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">💰 Money Flow</h1>
                    <p style="margin: 10px 0 0;">Payment Reminder</p>
                </div>
                <div class="content">
                    <div class="status" style="background: {color};">{urgency_text}</div>
                    <h2 style="margin: 0; color: #1f2937;">{subscription.name}</h2>
                    <div class="amount">{amount}</div>
                    <div class="details">
                        <div class="detail-row">
                            <span class="label">Payment Date</span>
                            <span class="value">{date_str}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Frequency</span>
                            <span class="value">{subscription.frequency.value.title()}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Category</span>
                            <span class="value">{subscription.category or "Uncategorized"}</span>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <p>Money Flow - Your payment tracking assistant</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_digest_html(
        self,
        subscriptions: list["Subscription"],
        today_payments: list["Subscription"],
        week_payments: list["Subscription"],
        currency_symbol: str,
        total: Decimal,
        period: str,
    ) -> str:
        """Build HTML for digest email.

        Args:
            subscriptions: All subscriptions in the digest.
            today_payments: Payments due today.
            week_payments: Payments due this week.
            currency_symbol: Currency symbol for display.
            total: Total amount.
            period: "Daily" or "Weekly".

        Returns:
            HTML string for the email body.
        """
        # Build payment rows
        payment_rows = ""
        for sub in subscriptions[:10]:  # Limit to 10 for email length
            date_str = sub.next_payment_date.strftime("%b %d") if sub.next_payment_date else ""
            payment_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{sub.name}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                    {currency_symbol}{sub.amount:.2f}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">
                    {date_str}
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       margin: 0; padding: 0; background: #f3f4f6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 8px 8px;
                           box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-value {{ font-size: 28px; font-weight: 700; color: #667eea; }}
                .stat-label {{ color: #6b7280; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #f8fafc; padding: 12px; text-align: left; font-weight: 600; }}
                .footer {{ text-align: center; padding: 20px; color: #9ca3af; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📊 Money Flow</h1>
                    <p style="margin: 10px 0 0;">{period} Payment Digest</p>
                </div>
                <div class="content">
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">{len(subscriptions)}</div>
                            <div class="stat-label">Payments</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{currency_symbol}{total:.2f}</div>
                            <div class="stat-label">Total</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{len(today_payments)}</div>
                            <div class="stat-label">Due Today</div>
                        </div>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Payment</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {payment_rows}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p>Money Flow - Your payment tracking assistant</p>
                </div>
            </div>
        </body>
        </html>
        """
