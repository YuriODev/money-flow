"""Command executor for the agentic interface (Money Flow).

This module provides the AgentExecutor class that bridges natural language
commands to actual database operations. It uses CommandParser to understand
user intent and SubscriptionService to perform CRUD operations.

The executor supports create, read, update, delete, summary, and upcoming
payment operations for all Money Flow payment types:
- Subscriptions, Housing, Utilities, Professional Services
- Insurance, Debts, Savings, Transfers

RAG integration provides conversation context and reference resolution
for improved command understanding.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.parser import CommandParser
from src.core.config import settings
from src.models.subscription import PaymentType
from src.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from src.services.conversation_service import ConversationService
from src.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

# Currency symbols for display
CURRENCY_SYMBOLS = {
    "GBP": "£",
    "USD": "$",
    "EUR": "€",
    "UAH": "₴",
}

# Payment type display names
PAYMENT_TYPE_NAMES = {
    PaymentType.SUBSCRIPTION: "subscription",
    PaymentType.HOUSING: "housing payment",
    PaymentType.UTILITY: "utility payment",
    PaymentType.PROFESSIONAL_SERVICE: "professional service",
    PaymentType.INSURANCE: "insurance payment",
    PaymentType.DEBT: "debt payment",
    PaymentType.SAVINGS: "savings",
    PaymentType.TRANSFER: "transfer",
}


class AgentExecutor:
    """Execute parsed commands against the subscription service.

    This class takes natural language commands, parses them to extract
    intent and entities, then routes to appropriate handler methods
    that perform database operations.

    RAG integration provides conversation context for reference resolution
    (e.g., "cancel it" → "cancel Netflix") and improved command understanding.

    Attributes:
        db: Async database session for operations.
        parser: CommandParser instance for NL understanding.
        service: SubscriptionService for database operations.
        conversation_service: ConversationService for RAG context.
        user_id: Current user ID for context isolation.
        session_id: Current session ID for conversation tracking.

    Example:
        >>> async with get_db() as session:
        ...     executor = AgentExecutor(session, user_id="user-1", session_id="sess-1")
        ...     result = await executor.execute("Add Netflix £15.99 monthly")
        ...     print(result["message"])
        "Added 'Netflix' - £15.99 monthly"
    """

    def __init__(
        self,
        db: AsyncSession,
        user_id: str = "default",
        session_id: str | None = None,
    ) -> None:
        """Initialize the agent executor.

        Args:
            db: Async database session for performing operations.
                Should be provided via FastAPI dependency injection.
            user_id: User ID for context isolation (default: "default").
            session_id: Session ID for conversation tracking. If None,
                a new session ID is generated.

        Example:
            >>> executor = AgentExecutor(db_session, user_id="user-123")
        """
        self.db = db
        self.parser = CommandParser()
        self.service = SubscriptionService(db)
        self.conversation_service = ConversationService(db)
        self.user_id = user_id
        self.session_id = session_id or "default-session"

    async def execute(self, command: str) -> dict[str, Any]:
        """Execute a natural language command with RAG context.

        Parses the command to determine intent (CREATE, READ, UPDATE,
        DELETE, SUMMARY, UPCOMING) and extracts relevant entities,
        then routes to the appropriate handler.

        RAG integration provides:
        - Reference resolution: "cancel it" → "cancel Netflix"
        - Conversation context for improved understanding
        - Entity tracking across turns

        Args:
            command: Natural language command string from user.

        Returns:
            Dictionary containing:
            - message: Human-readable result message
            - data: Operation result data (subscription info, list, summary)
            - context: Optional RAG context used (if enabled)

        Raises:
            ValueError: If command cannot be understood or required
                entities are missing.

        Example:
            >>> result = await executor.execute("Show all subscriptions")
            >>> result["message"]
            "Found 5 subscription(s)"
        """
        # Get RAG context for reference resolution
        resolved_command = command
        context = None

        if settings.rag_enabled:
            try:
                context = await self.conversation_service.get_context(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    query=command,
                )
                resolved_command = context.resolved_query
                logger.debug(f"Resolved command: '{command}' → '{resolved_command}'")
            except Exception as e:
                logger.warning(f"RAG context retrieval failed: {e}")

        # Parse the (possibly resolved) command
        parsed = self.parser.parse(resolved_command)

        intent = parsed.get("intent", "UNKNOWN")
        entities = parsed.get("entities", {})

        handlers = {
            "CREATE": self._handle_create,
            "READ": self._handle_read,
            "UPDATE": self._handle_update,
            "DELETE": self._handle_delete,
            "SUMMARY": self._handle_summary,
            "UPCOMING": self._handle_upcoming,
        }

        handler = handlers.get(intent)
        if not handler:
            # Store the failed command for context
            if settings.rag_enabled:
                await self.conversation_service.add_turn(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    role="user",
                    content=command,
                )
            raise ValueError(
                "I didn't understand that command. Try something like:\n"
                "- 'Add Netflix for £15.99 monthly'\n"
                "- 'Add rent payment £1137.50 monthly'\n"
                "- 'Add debt to John £500, paying £50 monthly'\n"
                "- 'Add savings goal £10000 for holiday'\n"
                "- 'Show all my payments'\n"
                "- 'How much am I spending?'\n"
                "- 'What's my total debt?'"
            )

        # Execute the handler
        result = await handler(entities)

        # Store the conversation turn with extracted entities
        if settings.rag_enabled:
            # Store user message
            await self.conversation_service.add_turn(
                user_id=self.user_id,
                session_id=self.session_id,
                role="user",
                content=command,
                entities=ConversationService.extract_entities_from_response(result),
            )
            # Store assistant response
            await self.conversation_service.add_turn(
                user_id=self.user_id,
                session_id=self.session_id,
                role="assistant",
                content=result.get("message", ""),
                entities=ConversationService.extract_entities_from_response(result),
            )

        return result

    async def _handle_create(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle payment creation with Money Flow support.

        Creates a new payment with the extracted entities including
        name, amount, frequency, payment type, and type-specific fields.

        Args:
            entities: Extracted entities containing:
                - name (required): Payment name
                - amount (required): Payment amount as Decimal
                - frequency: Payment frequency (default: MONTHLY)
                - payment_type: Type of payment (subscription, debt, savings, etc.)
                - category: Optional subcategory string
                - currency: Currency code (default: GBP)
                For debt payments:
                - total_owed: Total debt amount
                - remaining_balance: Current remaining balance
                - creditor: Who you owe
                For savings:
                - target_amount: Savings goal
                - current_saved: Current progress
                - recipient: Who receives the transfer

        Returns:
            Dictionary with success message and payment data.

        Raises:
            ValueError: If name or amount is missing.

        Example:
            >>> result = await executor._handle_create({
            ...     "name": "Credit Card",
            ...     "amount": Decimal("200"),
            ...     "payment_type": PaymentType.DEBT,
            ...     "total_owed": Decimal("5000"),
            ... })
        """
        if "name" not in entities or "amount" not in entities:
            raise ValueError(
                "Please specify the payment name and amount. "
                "Examples:\n"
                "- 'Add Netflix for £15.99 monthly'\n"
                "- 'Add rent £1137.50 monthly'\n"
                "- 'Add debt to John £500, paying £50 monthly'"
            )

        # Get currency symbol for display
        currency = entities.get("currency", "GBP")
        symbol = CURRENCY_SYMBOLS.get(currency, "£")

        # Get payment type
        payment_type = entities.get("payment_type", PaymentType.SUBSCRIPTION)
        if isinstance(payment_type, str):
            payment_type = PaymentType(payment_type.lower())

        # Build create data with all Money Flow fields
        data = SubscriptionCreate(
            name=entities["name"],
            amount=entities["amount"],
            currency=currency,
            frequency=entities.get("frequency"),
            payment_type=payment_type,
            category=entities.get("category"),
            start_date=date.today(),
            # Debt-specific fields
            total_owed=entities.get("total_owed"),
            remaining_balance=entities.get("remaining_balance") or entities.get("total_owed"),
            creditor=entities.get("creditor"),
            # Savings-specific fields
            target_amount=entities.get("target_amount"),
            current_saved=entities.get("current_saved", Decimal("0")),
            recipient=entities.get("recipient"),
        )

        subscription = await self.service.create(data)

        # Build response message based on payment type
        type_name = PAYMENT_TYPE_NAMES.get(payment_type, "payment")
        base_msg = f"✅ Added {type_name}: '{subscription.name}' - {symbol}{subscription.amount} {subscription.frequency.value}"

        # Add type-specific info
        extra_info = []
        if payment_type == PaymentType.DEBT and subscription.total_owed:
            extra_info.append(f"Total owed: {symbol}{subscription.total_owed}")
            if subscription.remaining_balance:
                extra_info.append(f"Remaining: {symbol}{subscription.remaining_balance}")
        elif payment_type == PaymentType.SAVINGS and subscription.target_amount:
            extra_info.append(f"Goal: {symbol}{subscription.target_amount}")
            if subscription.current_saved:
                progress = (subscription.current_saved / subscription.target_amount) * 100
                extra_info.append(f"Progress: {progress:.0f}%")

        message = base_msg
        if extra_info:
            message += "\n" + " | ".join(extra_info)

        return {
            "message": message,
            "data": SubscriptionResponse.model_validate(subscription).model_dump(mode="json"),
        }

    async def _handle_read(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle listing payments with Money Flow filtering.

        Retrieves payments with optional filtering by active status,
        category, and payment type.

        Args:
            entities: Optional filter entities:
                - is_active: Filter by active status
                - category: Filter by subcategory name
                - payment_type: Filter by payment type (debt, savings, etc.)

        Returns:
            Dictionary with count message and list of payments.

        Example:
            >>> result = await executor._handle_read({"payment_type": PaymentType.DEBT})
            >>> result["message"]
            "Found 3 debt payment(s)"
        """
        is_active = entities.get("is_active")
        category = entities.get("category")
        payment_type = entities.get("payment_type")

        subscriptions = await self.service.get_all(
            is_active=is_active,
            category=category,
            payment_type=payment_type,
        )

        if not subscriptions:
            type_label = (
                PAYMENT_TYPE_NAMES.get(payment_type, "payment") if payment_type else "payment"
            )
            return {
                "message": f"📭 No {type_label}s found.",
                "data": [],
            }

        # Build appropriate label
        if payment_type:
            type_label = PAYMENT_TYPE_NAMES.get(payment_type, "payment")
            label = f"{type_label}(s)"
        else:
            label = "payment(s)"

        return {
            "message": f"📋 Found {len(subscriptions)} {label}",
            "data": [
                SubscriptionResponse.model_validate(s).model_dump(mode="json")
                for s in subscriptions
            ],
        }

    async def _handle_update(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle payment update with Money Flow support.

        Updates an existing payment found by partial name match.
        Supports updating amount, frequency, category, and type-specific fields
        like remaining_balance (for debt) or current_saved (for savings).

        Args:
            entities: Update entities containing:
                - name (required): Partial name to search for
                - amount: New payment amount
                - frequency: New payment frequency
                - category: New subcategory
                - remaining_balance: New debt balance (for debt type)
                - current_saved: New saved amount (for savings type)
                - target_amount: New savings goal (for savings type)
                - payment_amount: Amount paid off debt (special handling)
                - add_amount: Amount to add to savings (special handling)

        Returns:
            Dictionary with success message and updated payment data.

        Raises:
            ValueError: If name not specified, no match found, or
                multiple matches found.

        Example:
            >>> result = await executor._handle_update({
            ...     "name": "Credit Card",
            ...     "payment_amount": Decimal("500")  # Paid £500 off
            ... })
        """
        name = entities.get("name")
        if not name:
            raise ValueError("Please specify which payment to update.")

        # Find subscription by name (partial match)
        subscriptions = await self.service.get_all()
        matching = [s for s in subscriptions if name.lower() in s.name.lower()]

        if not matching:
            raise ValueError(f"No payment found matching '{name}'")
        if len(matching) > 1:
            names = ", ".join(s.name for s in matching)
            raise ValueError(f"Multiple matches found: {names}. Please be more specific.")

        subscription = matching[0]
        currency = subscription.currency
        symbol = CURRENCY_SYMBOLS.get(currency, "£")

        # Build update fields
        update_fields: dict[str, Any] = {}

        # Standard fields
        if "amount" in entities:
            update_fields["amount"] = entities["amount"]
        if "frequency" in entities:
            update_fields["frequency"] = entities["frequency"]
        if "category" in entities:
            update_fields["category"] = entities["category"]

        # Handle debt payment (reduce remaining balance)
        if "payment_amount" in entities and subscription.remaining_balance:
            new_balance = subscription.remaining_balance - entities["payment_amount"]
            update_fields["remaining_balance"] = max(Decimal("0"), new_balance)

        # Handle adding to savings
        if "add_amount" in entities:
            current = subscription.current_saved or Decimal("0")
            update_fields["current_saved"] = current + entities["add_amount"]

        # Direct field updates
        if "remaining_balance" in entities:
            update_fields["remaining_balance"] = entities["remaining_balance"]
        if "current_saved" in entities:
            update_fields["current_saved"] = entities["current_saved"]
        if "target_amount" in entities:
            update_fields["target_amount"] = entities["target_amount"]

        update_data = SubscriptionUpdate(**update_fields)
        updated = await self.service.update(subscription.id, update_data)

        # Build response message
        message = f"✅ Updated '{updated.name}'"

        # Add type-specific details
        if subscription.payment_type == PaymentType.DEBT and updated.remaining_balance is not None:
            if updated.remaining_balance == 0:
                message += " - 🎉 Debt paid off!"
            else:
                message += f" - Remaining: {symbol}{updated.remaining_balance}"
        elif subscription.payment_type == PaymentType.SAVINGS and updated.target_amount:
            progress = ((updated.current_saved or 0) / updated.target_amount) * 100
            message += f" - Progress: {progress:.0f}% ({symbol}{updated.current_saved or 0}/{symbol}{updated.target_amount})"

        return {
            "message": message,
            "data": SubscriptionResponse.model_validate(updated).model_dump(mode="json"),
        }

    async def _handle_delete(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle payment deletion.

        Deletes a payment found by partial name match.

        Args:
            entities: Entities containing:
                - name (required): Partial name to search for

        Returns:
            Dictionary with removal message and deleted ID.

        Raises:
            ValueError: If name not specified, no match found, or
                multiple matches found.

        Example:
            >>> result = await executor._handle_delete({"name": "Netflix"})
            >>> result["message"]
            "Removed 'Netflix'"
        """
        name = entities.get("name")
        if not name:
            raise ValueError("Please specify which payment to remove.")

        subscriptions = await self.service.get_all()
        matching = [s for s in subscriptions if name.lower() in s.name.lower()]

        if not matching:
            raise ValueError(f"No payment found matching '{name}'")
        if len(matching) > 1:
            names = ", ".join(s.name for s in matching)
            raise ValueError(f"Multiple matches found: {names}. Please be more specific.")

        subscription = matching[0]
        payment_type = subscription.payment_type
        type_name = PAYMENT_TYPE_NAMES.get(payment_type, "payment")

        await self.service.delete(subscription.id)

        # Custom message based on type
        if payment_type == PaymentType.DEBT:
            message = f"🎉 Marked '{subscription.name}' as paid off!"
        elif payment_type == PaymentType.SAVINGS:
            message = f"🗑️ Removed savings goal '{subscription.name}'"
        else:
            message = f"🗑️ Removed {type_name} '{subscription.name}'"

        return {
            "message": message,
            "data": {"deleted_id": subscription.id},
        }

    async def _handle_summary(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle spending summary request with Money Flow details.

        Calculates and returns spending analytics including monthly/yearly
        totals, breakdown by category and payment type, plus debt and
        savings totals.

        Args:
            entities: Optional filter:
                - payment_type: Filter summary by payment type

        Returns:
            Dictionary with formatted summary message and summary data
            containing total_monthly, total_yearly, active_count,
            by_category, by_payment_type, and debt/savings totals.

        Example:
            >>> result = await executor._handle_summary({})
            >>> "Monthly:" in result["message"]
            True
        """
        payment_type = entities.get("payment_type")
        summary = await self.service.get_summary(payment_type=payment_type)

        # Get currency symbol
        symbol = CURRENCY_SYMBOLS.get(summary.currency, "£")

        # Build category breakdown
        category_breakdown = "\n".join(
            f"  • {cat}: {symbol}{amt}" for cat, amt in summary.by_category.items()
        )

        # Build payment type breakdown
        type_breakdown = "\n".join(
            f"  • {pt.title()}: {symbol}{amt}" for pt, amt in summary.by_payment_type.items()
        )

        # Build main message
        lines = [
            "💰 Money Flow Summary",
            f"Monthly spending: {symbol}{summary.total_monthly}",
            f"Yearly total: {symbol}{summary.total_yearly}",
            f"Active payments: {summary.active_count}",
        ]

        # Add debt info if present
        if summary.total_debt > 0:
            lines.append(f"\n💳 Total Debt: {symbol}{summary.total_debt}")

        # Add savings info if present
        if summary.total_savings_target > 0:
            progress = (summary.total_current_saved / summary.total_savings_target) * 100
            lines.append(
                f"\n🐷 Savings: {symbol}{summary.total_current_saved} / "
                f"{symbol}{summary.total_savings_target} ({progress:.0f}%)"
            )

        # Add breakdowns
        if type_breakdown:
            lines.append(f"\nBy payment type:\n{type_breakdown}")
        if category_breakdown:
            lines.append(f"\nBy category:\n{category_breakdown}")

        return {
            "message": "\n".join(lines),
            "data": summary.model_dump(mode="json"),
        }

    async def _handle_upcoming(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Handle upcoming payments request.

        Returns payments due in the next 7 days with proper currency display.

        Args:
            entities: Currently unused, reserved for future filtering.

        Returns:
            Dictionary with formatted upcoming payments message and
            list of payment data due within the week.

        Example:
            >>> result = await executor._handle_upcoming({})
            >>> "Upcoming payments" in result["message"] or "No payments" in result["message"]
            True
        """
        summary = await self.service.get_summary()
        upcoming = summary.upcoming_week

        if not upcoming:
            return {
                "message": "📅 No payments due in the next 7 days!",
                "data": [],
            }

        # Format items with proper currency symbols
        items = []
        for s in upcoming:
            symbol = CURRENCY_SYMBOLS.get(s.currency, "£")
            items.append(f"  • {s.name}: {symbol}{s.amount} on {s.next_payment_date}")

        return {
            "message": "📅 Upcoming payments (next 7 days):\n" + "\n".join(items),
            "data": [s.model_dump(mode="json") for s in upcoming],
        }
