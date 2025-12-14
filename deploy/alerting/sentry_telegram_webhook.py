#!/usr/bin/env python3
"""Sentry to Telegram webhook handler.

This script receives Sentry webhook events and forwards them to a Telegram
channel/topic. Deploy as a serverless function (Cloud Functions, Lambda, etc.)
or as a simple FastAPI endpoint.

Environment Variables Required:
    TELEGRAM_BOT_TOKEN: Bot token from @BotFather
    TELEGRAM_CHAT_ID: Target chat/group ID
    TELEGRAM_THREAD_ERRORS: Thread ID for errors topic (optional)
    SENTRY_CLIENT_SECRET: Sentry webhook client secret for verification

Usage as standalone server:
    python sentry_telegram_webhook.py

Usage as Cloud Function:
    Deploy the `handle_sentry_webhook` function
"""

import hashlib
import hmac
import json
import os
from typing import Any

# Try to import FastAPI for standalone mode
try:
    from fastapi import FastAPI, HTTPException, Request
    import httpx
    import uvicorn

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def format_sentry_message(payload: dict[str, Any]) -> str:
    """Format Sentry webhook payload into a Telegram message.

    Args:
        payload: Sentry webhook event payload.

    Returns:
        HTML-formatted message for Telegram.
    """
    action = payload.get("action", "unknown")
    data = payload.get("data", {})

    # Handle different Sentry event types
    if "issue" in data:
        issue = data["issue"]
        title = issue.get("title", "Unknown Error")
        culprit = issue.get("culprit", "Unknown location")
        level = issue.get("level", "error")
        count = issue.get("count", 1)
        first_seen = issue.get("firstSeen", "")
        url = issue.get("permalink", "")

        # Choose emoji based on level
        emoji = {
            "fatal": "💀",
            "error": "🔴",
            "warning": "🟠",
            "info": "🔵",
            "debug": "⚪",
        }.get(level, "🔴")

        message = f"{emoji} <b>Sentry Alert: {action.upper()}</b>\n\n"
        message += f"<b>Error:</b> {_escape_html(title)}\n"
        message += f"<b>Location:</b> <code>{_escape_html(culprit)}</code>\n"
        message += f"<b>Level:</b> {level}\n"
        message += f"<b>Count:</b> {count}\n"

        if first_seen:
            message += f"<b>First seen:</b> {first_seen}\n"

        if url:
            message += f"\n<a href=\"{url}\">View in Sentry</a>"

        return message

    elif "event" in data:
        event = data["event"]
        title = event.get("title", "Unknown Event")
        message_text = event.get("message", "")

        message = "🔔 <b>Sentry Event</b>\n\n"
        message += f"<b>Title:</b> {_escape_html(title)}\n"
        if message_text:
            message += f"<b>Message:</b> {_escape_html(message_text[:200])}\n"

        return message

    else:
        # Generic fallback
        return f"📢 <b>Sentry Notification</b>\n\n<code>{json.dumps(payload, indent=2)[:500]}</code>"


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def verify_sentry_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Sentry webhook signature.

    Args:
        payload: Raw request body.
        signature: Sentry-Hook-Signature header value.
        secret: Sentry client secret.

    Returns:
        True if signature is valid.
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def send_telegram_message(message: str) -> bool:
    """Send message to Telegram.

    Args:
        message: HTML-formatted message.

    Returns:
        True if message was sent successfully.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    thread_id = os.environ.get("TELEGRAM_THREAD_ERRORS")

    if not bot_token or not chat_id:
        print("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if thread_id:
        data["message_thread_id"] = int(thread_id)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        return response.status_code == 200


# FastAPI standalone server (for local testing or self-hosted)
if FASTAPI_AVAILABLE:
    app = FastAPI(title="Sentry Telegram Webhook")

    @app.post("/webhook/sentry")
    async def handle_sentry_webhook(request: Request):
        """Handle incoming Sentry webhook events."""
        # Get raw body for signature verification
        body = await request.body()

        # Verify signature if secret is configured
        secret = os.environ.get("SENTRY_CLIENT_SECRET")
        if secret:
            signature = request.headers.get("Sentry-Hook-Signature", "")
            if not verify_sentry_signature(body, signature, secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Format and send message
        message = format_sentry_message(payload)
        success = await send_telegram_message(message)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification")

        return {"status": "ok"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}


# Google Cloud Function handler
def cloud_function_handler(request):
    """Google Cloud Function entry point.

    Deploy with:
        gcloud functions deploy sentry-telegram-webhook \
            --runtime python311 \
            --trigger-http \
            --allow-unauthenticated \
            --set-env-vars TELEGRAM_BOT_TOKEN=xxx,TELEGRAM_CHAT_ID=xxx
    """
    import asyncio

    # Verify signature
    secret = os.environ.get("SENTRY_CLIENT_SECRET")
    if secret:
        signature = request.headers.get("Sentry-Hook-Signature", "")
        if not verify_sentry_signature(request.data, signature, secret):
            return ("Invalid signature", 401)

    # Parse and process
    try:
        payload = request.get_json()
    except Exception:
        return ("Invalid JSON", 400)

    message = format_sentry_message(payload)

    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(send_telegram_message(message))
    loop.close()

    if not success:
        return ("Failed to send notification", 500)

    return ("OK", 200)


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn httpx")
