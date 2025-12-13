"""Conversational AI agent API endpoint.

This module provides the REST API endpoint for the conversational AI agent.
The agent is powered by Claude and can handle natural language conversations,
including greetings, questions, and subscription management tasks.

The agent uses Claude's tool-use capability to interact with the subscription
database while maintaining a natural conversational flow.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.conversational_agent import ConversationalAgent
from src.agent.executor import AgentExecutor
from src.core.config import settings
from src.core.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentRequest(BaseModel):
    """Request schema for agent chat.

    Attributes:
        command: Natural language message from the user.
        user_id: User identifier for RAG context isolation.
        session_id: Session identifier for conversation tracking.
        history: Optional conversation history for context.

    Example:
        >>> request = AgentRequest(command="Hello!", user_id="user-123")
        >>> request.command
        'Hello!'
    """

    command: str = Field(
        ...,
        description="Natural language message to the agent",
        min_length=1,
        examples=[
            "Hello!",
            "Add Netflix for £15.99 monthly",
            "Show all subscriptions",
            "How much am I spending?",
        ],
    )
    user_id: str = Field(
        default="default",
        description="User ID for RAG context isolation",
    )
    session_id: str | None = Field(
        default=None,
        description="Session ID for conversation tracking. Auto-generated if not provided.",
    )
    history: list[ChatMessage] = Field(
        default=[],
        description="Previous conversation messages for context",
    )


class AgentResponse(BaseModel):
    """Response schema from agent.

    Attributes:
        success: Whether the request was processed successfully.
        message: The agent's response message.
        data: Optional data payload containing subscription info or analytics.

    Example:
        >>> response = AgentResponse(
        ...     success=True,
        ...     message="Hello! I'm your subscription assistant.",
        ...     data=None
        ... )
    """

    success: bool = Field(..., description="Whether request succeeded")
    message: str = Field(..., description="Agent's response message")
    data: dict | list | None = Field(
        default=None,
        description="Optional data payload with subscription or analytics info",
    )


@router.post("/execute", response_model=AgentResponse)
async def execute_command(
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """Chat with the conversational AI agent.

    Sends the user's message to the Claude-powered agent which can handle
    natural conversations, answer questions, and perform subscription
    management tasks.

    Args:
        request: Agent request containing the user's message.
        db: Async database session from dependency injection.

    Returns:
        AgentResponse with the agent's reply and optional data.

    Raises:
        HTTPException: 500 error if an unexpected error occurs.

    Example:
        POST /api/agent/execute
        {"command": "Hello!"}

        Response:
        {
            "success": true,
            "message": "Hello! I'm your subscription assistant...",
            "data": null
        }
    """
    # Check if we have an API key for the conversational agent
    if settings.anthropic_api_key:
        try:
            agent = ConversationalAgent(db)

            # Load conversation history if provided
            if request.history:
                for msg in request.history:
                    agent.conversation_history.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                        }
                    )

            result = await agent.chat(request.command)
            return AgentResponse(
                success=True,
                message=result.get("message", ""),
                data=result.get("data"),
            )
        except ValueError as e:
            # API key issues - fall back to legacy executor
            logger.warning(f"Conversational agent error: {e}, falling back to legacy")
        except Exception as e:
            logger.exception(f"Agent error: {e}")
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Fallback to legacy regex-based executor if no API key
    try:
        executor = AgentExecutor(
            db,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        result = await executor.execute(request.command)
        return AgentResponse(
            success=True,
            message=result.get("message", "Command executed successfully"),
            data=result.get("data"),
        )
    except ValueError as e:
        return AgentResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
