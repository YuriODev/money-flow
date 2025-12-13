"""Conversational AI agent powered by Claude.

This module provides a true LLM-powered conversational agent that can handle
natural language interactions, including greetings, questions, and subscription
management tasks. It uses Claude's tool-use capability to interact with the
subscription database.
"""

import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.subscription import Frequency
from src.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from src.services.currency_service import CurrencyService
from src.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

# Define the tools the agent can use
AGENT_TOOLS = [
    {
        "name": "list_subscriptions",
        "description": "List all subscriptions. Can filter by active status or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "is_active": {
                    "type": "boolean",
                    "description": "Filter by active status. If not provided, returns all.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category name.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_subscription",
        "description": "Create a new subscription/recurring payment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the subscription (e.g., Netflix, Spotify, Gym)",
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount (e.g., 15.99)",
                },
                "currency": {
                    "type": "string",
                    "description": "Currency code (GBP, USD, EUR, UAH). Defaults to GBP.",
                    "enum": ["GBP", "USD", "EUR", "UAH"],
                },
                "frequency": {
                    "type": "string",
                    "description": "Payment frequency",
                    "enum": ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"],
                },
                "category": {
                    "type": "string",
                    "description": "Category (e.g., entertainment, health, utilities)",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about this subscription",
                },
            },
            "required": ["name", "amount"],
        },
    },
    {
        "name": "update_subscription",
        "description": "Update an existing subscription by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the subscription to update (partial match works)",
                },
                "new_amount": {
                    "type": "number",
                    "description": "New payment amount",
                },
                "new_frequency": {
                    "type": "string",
                    "description": "New payment frequency",
                    "enum": ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"],
                },
                "new_category": {
                    "type": "string",
                    "description": "New category",
                },
                "is_active": {
                    "type": "boolean",
                    "description": "Set active/inactive status",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "delete_subscription",
        "description": "Delete/cancel a subscription by name or ID. Use ID when there are multiple subscriptions with similar names.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the subscription to delete (partial match works)",
                },
                "subscription_id": {
                    "type": "string",
                    "description": "UUID of the subscription to delete (use when name is ambiguous)",
                },
                "delete_all_matching": {
                    "type": "boolean",
                    "description": "If true, delete ALL subscriptions matching the name. Use carefully!",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_summary",
        "description": "Get a summary of all spending including monthly/yearly totals and breakdown by category.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_upcoming_payments",
        "description": "Get payments due in the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default: 7)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "convert_currency",
        "description": "Convert an amount between currencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Amount to convert",
                },
                "from_currency": {
                    "type": "string",
                    "description": "Source currency code",
                    "enum": ["GBP", "USD", "EUR", "UAH"],
                },
                "to_currency": {
                    "type": "string",
                    "description": "Target currency code",
                    "enum": ["GBP", "USD", "EUR", "UAH"],
                },
            },
            "required": ["amount", "from_currency", "to_currency"],
        },
    },
]

SYSTEM_PROMPT = """You are a friendly and helpful subscription management assistant. You help users track and manage their recurring payments and subscriptions.

## Your Personality
- Be conversational and friendly, not robotic
- Use natural language, not formal commands
- Add appropriate emojis to make responses engaging
- Be proactive in offering helpful suggestions

## What You Can Do
- Create, view, update, and delete subscriptions
- Show spending summaries and analytics
- Check upcoming payments
- Convert between currencies (GBP, USD, EUR, UAH)
- Answer questions about subscriptions and spending

## Guidelines
- Default currency is GBP (£)
- When creating subscriptions, default to monthly frequency if not specified
- For destructive actions (delete), confirm what you're about to do
- Format currency amounts with proper symbols (£, $, €, ₴)
- When listing subscriptions, format them in a readable way
- If the user greets you, respond warmly and offer to help
- If you don't understand something, ask for clarification

## Response Style
- Keep responses concise but informative
- Use bullet points for lists
- Include relevant numbers and totals when discussing money
- Offer follow-up suggestions when appropriate

Remember: You're having a conversation, not just executing commands. Be helpful and engaging!"""


class ConversationalAgent:
    """A conversational AI agent for subscription management.

    This agent uses Claude as its brain and can handle natural conversations
    while also performing subscription management tasks through tool use.

    Attributes:
        db: Async database session
        service: SubscriptionService for database operations
        currency_service: CurrencyService for currency operations
        client: Anthropic client
        model: Claude model to use
        conversation_history: List of messages for context
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the conversational agent.

        Args:
            db: Async database session for operations.
        """
        self.db = db
        self.service = SubscriptionService(db)
        self.currency_service = CurrencyService(api_key=settings.exchange_rate_api_key or None)

        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the conversational agent")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"  # Use Sonnet for better conversation
        self.conversation_history: list[dict] = []

    async def chat(self, user_message: str) -> dict[str, Any]:
        """Process a user message and return a response.

        This method handles the full conversation flow, including:
        - Sending the message to Claude
        - Processing any tool calls
        - Returning the final response

        Args:
            user_message: The user's message

        Returns:
            Dictionary with 'message' and optionally 'data'
        """
        # Add user message to history
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        try:
            # Initial API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=AGENT_TOOLS,
                messages=self.conversation_history,
            )

            # Process the response, handling tool use
            final_response = await self._process_response(response)

            # Add assistant response to history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": final_response["message"],
                }
            )

            return final_response

        except Exception as e:
            logger.exception(f"Agent error: {e}")
            error_message = f"I encountered an error: {str(e)}. Please try again."
            return {"message": error_message, "data": None}

    async def _process_response(self, response: Any) -> dict[str, Any]:
        """Process Claude's response, handling tool calls if needed.

        Args:
            response: The API response from Claude

        Returns:
            Dictionary with final message and data
        """
        collected_data: list[Any] = []

        # Process while there are tool calls
        while response.stop_reason == "tool_use":
            # Extract tool uses and text
            tool_uses = []
            text_content = ""

            for block in response.content:
                if block.type == "tool_use":
                    tool_uses.append(block)
                elif block.type == "text":
                    text_content += block.text

            # Execute each tool
            tool_results = []
            for tool_use in tool_uses:
                result = await self._execute_tool(tool_use.name, tool_use.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result, default=str),
                    }
                )
                if result.get("data"):
                    collected_data.append(result["data"])

            # Add assistant message with tool use to history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )

            # Add tool results to history
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": tool_results,
                }
            )

            # Get next response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=AGENT_TOOLS,
                messages=self.conversation_history,
            )

        # Extract final text response
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        return {
            "message": final_text,
            "data": collected_data[0]
            if len(collected_data) == 1
            else collected_data
            if collected_data
            else None,
        }

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> dict[str, Any]:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Dictionary with tool execution result
        """
        try:
            if tool_name == "list_subscriptions":
                return await self._tool_list_subscriptions(tool_input)
            elif tool_name == "create_subscription":
                return await self._tool_create_subscription(tool_input)
            elif tool_name == "update_subscription":
                return await self._tool_update_subscription(tool_input)
            elif tool_name == "delete_subscription":
                return await self._tool_delete_subscription(tool_input)
            elif tool_name == "get_spending_summary":
                return await self._tool_get_summary()
            elif tool_name == "get_upcoming_payments":
                return await self._tool_get_upcoming(tool_input)
            elif tool_name == "convert_currency":
                return await self._tool_convert_currency(tool_input)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return {"error": str(e)}

    async def _tool_list_subscriptions(self, params: dict) -> dict[str, Any]:
        """List subscriptions with optional filters."""
        is_active = params.get("is_active")
        category = params.get("category")

        subscriptions = await self.service.get_all(
            is_active=is_active,
            category=category,
        )

        if not subscriptions:
            return {"message": "No subscriptions found", "data": []}

        data = [
            SubscriptionResponse.model_validate(s).model_dump(mode="json") for s in subscriptions
        ]

        return {
            "message": f"Found {len(subscriptions)} subscription(s)",
            "data": data,
        }

    async def _tool_create_subscription(self, params: dict) -> dict[str, Any]:
        """Create a new subscription."""
        # Map frequency string to enum
        freq_str = params.get("frequency", "monthly").lower()
        freq_map = {
            "daily": Frequency.DAILY,
            "weekly": Frequency.WEEKLY,
            "biweekly": Frequency.BIWEEKLY,
            "monthly": Frequency.MONTHLY,
            "quarterly": Frequency.QUARTERLY,
            "yearly": Frequency.YEARLY,
        }
        frequency = freq_map.get(freq_str, Frequency.MONTHLY)

        # Format name with proper title case
        name = params["name"].strip().title()

        # Format category with proper title case if provided
        category = params.get("category")
        if category:
            category = category.strip().title()

        create_data = SubscriptionCreate(
            name=name,
            amount=Decimal(str(params["amount"])),
            currency=params.get("currency", "GBP"),
            frequency=frequency,
            start_date=date.today(),
            category=category,
            notes=params.get("notes"),
        )

        subscription = await self.service.create(create_data)
        data = SubscriptionResponse.model_validate(subscription).model_dump(mode="json")

        return {
            "message": f"Created subscription: {subscription.name}",
            "data": data,
        }

    async def _tool_update_subscription(self, params: dict) -> dict[str, Any]:
        """Update an existing subscription."""
        name = params.get("name")

        # Find subscription by name (partial match)
        subscriptions = await self.service.get_all()
        matching = [s for s in subscriptions if name.lower() in s.name.lower()]

        if not matching:
            return {"error": f"No subscription found matching '{name}'"}
        if len(matching) > 1:
            names = ", ".join(s.name for s in matching)
            return {"error": f"Multiple matches found: {names}. Please be more specific."}

        subscription = matching[0]

        # Build update data
        update_fields = {}
        if "new_amount" in params:
            update_fields["amount"] = Decimal(str(params["new_amount"]))
        if "new_frequency" in params:
            freq_map = {
                "daily": Frequency.DAILY,
                "weekly": Frequency.WEEKLY,
                "biweekly": Frequency.BIWEEKLY,
                "monthly": Frequency.MONTHLY,
                "quarterly": Frequency.QUARTERLY,
                "yearly": Frequency.YEARLY,
            }
            update_fields["frequency"] = freq_map.get(
                params["new_frequency"].lower(), Frequency.MONTHLY
            )
        if "new_category" in params:
            update_fields["category"] = params["new_category"]
        if "is_active" in params:
            update_fields["is_active"] = params["is_active"]

        update_data = SubscriptionUpdate(**update_fields)
        updated = await self.service.update(subscription.id, update_data)

        data = SubscriptionResponse.model_validate(updated).model_dump(mode="json")

        return {
            "message": f"Updated subscription: {updated.name}",
            "data": data,
        }

    async def _tool_delete_subscription(self, params: dict) -> dict[str, Any]:
        """Delete a subscription by name or ID."""
        subscription_id = params.get("subscription_id")
        name = params.get("name")
        delete_all = params.get("delete_all_matching", False)

        # If ID is provided, delete by ID directly
        if subscription_id:
            try:
                subscription = await self.service.get_by_id(subscription_id)
                if not subscription:
                    return {"error": f"No subscription found with ID '{subscription_id}'"}
                await self.service.delete(subscription.id)
                return {
                    "message": f"Deleted subscription: {subscription.name}",
                    "data": {"deleted_id": str(subscription.id), "deleted_name": subscription.name},
                }
            except Exception as e:
                return {"error": f"Failed to delete subscription: {str(e)}"}

        # Otherwise, find by name
        if not name:
            return {"error": "Please provide either a name or subscription_id"}

        subscriptions = await self.service.get_all()
        matching = [s for s in subscriptions if name.lower() in s.name.lower()]

        if not matching:
            return {"error": f"No subscription found matching '{name}'"}

        # If delete_all is True, delete all matching subscriptions
        if delete_all and len(matching) > 1:
            deleted = []
            for sub in matching:
                await self.service.delete(sub.id)
                deleted.append({"id": str(sub.id), "name": sub.name})
            return {
                "message": f"Deleted {len(deleted)} subscriptions matching '{name}'",
                "data": {"deleted": deleted},
            }

        # If multiple matches and not delete_all, return details with IDs
        if len(matching) > 1:
            subs_info = [f"- {s.name} ({s.currency} {s.amount}, ID: {s.id})" for s in matching]
            return {
                "error": f"Multiple subscriptions found matching '{name}':\n"
                + "\n".join(subs_info)
                + "\n\nUse subscription_id to delete a specific one, or set delete_all_matching=true to delete all.",
                "data": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "amount": str(s.amount),
                        "currency": s.currency,
                    }
                    for s in matching
                ],
            }

        subscription = matching[0]
        await self.service.delete(subscription.id)

        return {
            "message": f"Deleted subscription: {subscription.name}",
            "data": {"deleted_id": str(subscription.id), "deleted_name": subscription.name},
        }

    async def _tool_get_summary(self) -> dict[str, Any]:
        """Get spending summary with currency conversion."""
        # Pass currency service to convert all amounts to GBP
        summary = await self.service.get_summary(
            currency_service=self.currency_service,
            display_currency="GBP",
        )

        return {
            "message": "Spending summary retrieved",
            "data": summary.model_dump(mode="json"),
        }

    async def _tool_get_upcoming(self, params: dict) -> dict[str, Any]:
        """Get upcoming payments."""
        days = params.get("days", 7)
        upcoming = await self.service.get_upcoming(days=days)

        if not upcoming:
            return {"message": f"No payments due in the next {days} days", "data": []}

        data = [SubscriptionResponse.model_validate(s).model_dump(mode="json") for s in upcoming]

        return {
            "message": f"Found {len(upcoming)} upcoming payment(s)",
            "data": data,
        }

    async def _tool_convert_currency(self, params: dict) -> dict[str, Any]:
        """Convert currency."""
        amount = Decimal(str(params["amount"]))
        from_curr = params["from_currency"]
        to_curr = params["to_currency"]

        converted = await self.currency_service.convert(amount, from_curr, to_curr)

        # Get currency symbols
        symbols = {"GBP": "£", "USD": "$", "EUR": "€", "UAH": "₴"}
        from_symbol = symbols.get(from_curr, from_curr)
        to_symbol = symbols.get(to_curr, to_curr)

        return {
            "message": f"{from_symbol}{amount} = {to_symbol}{converted}",
            "data": {
                "original_amount": str(amount),
                "original_currency": from_curr,
                "converted_amount": str(converted),
                "target_currency": to_curr,
            },
        }

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
