"""Razorpay payment link integration with test-mode API and simulated fallback."""

from __future__ import annotations

import os
import logging
from uuid import uuid4
from typing import Any
import httpx

logger = logging.getLogger(__name__)

RAZORPAY_API_URL = "https://api.razorpay.com/v1/payment_links"


async def create_payment_link(
    amount_inr: float,
    description: str,
    customer_name: str = "Valued Customer",
    customer_email: str = "billing@customer.com",
    notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate a Razorpay Payment Link in test mode or provide clean simulation."""
    from shared.config import get_settings
    settings = get_settings()

    key_id = settings.razorpay_key_id or os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = settings.razorpay_key_secret or os.environ.get("RAZORPAY_KEY_SECRET", "").strip()

    # Amount in paise (1 INR = 100 paise), min 100 paise (1 INR)
    amount_paise = max(int(amount_inr * 100), 100)

    demo_redirect = settings.demo_notification_email or os.environ.get("DEMO_NOTIFICATION_EMAIL", "").strip()
    safe_email = demo_redirect if demo_redirect else (customer_email if "@example.com" in customer_email else "billing@example.com")

    if not key_id or not key_secret or key_id.startswith("rzp_test_YOUR"):
        logger.info(
            "💳 [Razorpay Simulated] No live RAZORPAY_KEY_ID/SECRET configured. Generating simulated test payment link for INR %.2f",
            amount_inr,
        )
        sim_id = f"plink_sim_{uuid4().hex[:12]}"
        return {
            "status": "created",
            "id": sim_id,
            "short_url": f"https://rzp.io/i/{sim_id[6:]}",
            "amount": amount_inr,
            "currency": "INR",
            "description": description,
            "customer": {"name": customer_name, "email": safe_email},
            "is_simulated": True,
            "note": "Simulated payment link (set real RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET in .env for live test-mode)",
        }

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "name": customer_name,
            "email": safe_email,
        },
        "notify": {
            "sms": False,
            "email": False,
        },
        "reminder_enable": False,
        "notes": notes or {"source": "omnisales_autonomous_engine"},
    }

    # Retry up to 2 attempts
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15.0, auth=(key_id, key_secret)) as client:
                resp = await client.post(RAZORPAY_API_URL, json=payload)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    logger.info("💳 [Razorpay Link Created] ID: %s | URL: %s", data.get("id"), data.get("short_url"))
                    return {
                        "status": "created",
                        "id": data.get("id"),
                        "short_url": data.get("short_url"),
                        "amount": amount_inr,
                        "currency": "INR",
                        "description": description,
                        "customer": {"name": customer_name, "email": customer_email},
                        "is_simulated": False,
                    }
                else:
                    logger.warning("Razorpay API attempt %d failed (%d): %s", attempt + 1, resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Razorpay request exception on attempt %d: %s", attempt + 1, e)

    # Fallback if both attempts fail
    sim_id = f"plink_fallback_{uuid4().hex[:12]}"
    return {
        "status": "created",
        "id": sim_id,
        "short_url": f"https://rzp.io/i/{sim_id[6:]}",
        "amount": amount_inr,
        "currency": "INR",
        "description": description,
        "is_simulated": True,
        "error": "Failed to reach Razorpay API after 2 attempts — fallback simulated link generated",
    }
