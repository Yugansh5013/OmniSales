"""Resend email dispatch integration with graceful fallback for simulation."""

from __future__ import annotations

import os
import logging
from uuid import uuid4
from typing import Any
import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
    reply_to: str | None = None,
) -> dict[str, Any]:
    """Send an email via Resend API or simulate cleanly when no key is set."""
    from shared.config import get_settings
    settings = get_settings()

    api_key = settings.resend_api_key or os.environ.get("RESEND_API_KEY", "").strip()
    from_email = settings.resend_from_email or os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev").strip()
    demo_redirect = settings.demo_notification_email or os.environ.get("DEMO_NOTIFICATION_EMAIL", "").strip()

    # In demo mode, redirect to test recipient if configured
    recipient = demo_redirect if demo_redirect else to_email

    if not api_key:
        logger.info(
            "📧 [Resend Simulated] No RESEND_API_KEY set. Simulated email to <%s> | Subject: '%s'",
            recipient,
            subject,
        )
        return {
            "status": "simulated",
            "id": f"sim_{uuid4().hex[:12]}",
            "to": recipient,
            "subject": subject,
            "is_simulated": True,
            "note": "Simulated dispatch (set RESEND_API_KEY in .env for live Resend delivery)",
        }

    payload: dict[str, Any] = {
        "from": from_email,
        "to": [recipient],
        "subject": subject,
        "html": body_html,
    }
    if body_text:
        payload["text"] = body_text
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info("📧 [Resend Sent] Email delivered to <%s> (id=%s)", recipient, data.get("id"))
                return {
                    "status": "sent",
                    "id": data.get("id"),
                    "to": recipient,
                    "subject": subject,
                    "is_simulated": False,
                }
            else:
                logger.error("Resend API error (%d): %s", resp.status_code, resp.text)
                return {
                    "status": "error",
                    "error": f"Resend returned {resp.status_code}: {resp.text[:200]}",
                    "is_simulated": False,
                }
    except Exception as e:
        logger.exception("Failed to dispatch email via Resend: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "is_simulated": False,
        }
