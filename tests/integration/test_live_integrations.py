"""Integration tests for live external APIs (Resend, Razorpay, Pinecone).

Validates:
1. Live Resend email dispatch with real API transaction IDs (not simulated).
2. Live Razorpay payment links API contract & gateway connectivity.
"""

from __future__ import annotations

import asyncio
import os
import sys
import pytest
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.config import get_settings
from shared.email import send_email
from shared.razorpay import create_payment_link, RAZORPAY_API_URL


@pytest.mark.asyncio
async def test_live_resend_email_dispatch():
    """Verify Resend dispatches live emails with is_simulated=False and genuine message ID."""
    settings = get_settings()
    assert settings.resend_api_key, "RESEND_API_KEY must be configured in .env"

    recipient = settings.demo_notification_email or "yugansh5014.s@gmail.com"
    subject = "OmniSales Live API Verification [TEST]"
    body_html = "<h3>OmniSales Engine Verification</h3><p>Live external Resend dispatch confirmed.</p>"

    result = await send_email(
        to_email=recipient,
        subject=subject,
        body_html=body_html,
        body_text="OmniSales Live API Verification confirmed.",
    )

    assert result["status"] == "sent", f"Expected sent status, got {result}"
    assert result["is_simulated"] is False, "Expected live dispatch, but returned simulated"
    assert result.get("id"), "Expected real Resend message ID"
    print(f"\n[OK] [Resend Live Evidence] Message ID: {result['id']} delivered to <{recipient}>")


@pytest.mark.asyncio
async def test_razorpay_api_connectivity():
    """Verify connectivity to official Razorpay Payment Links API endpoint."""
    settings = get_settings()
    key_id = settings.razorpay_key_id or os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = settings.razorpay_key_secret or os.environ.get("RAZORPAY_KEY_SECRET", "")

    is_configured = bool(key_id and key_secret and not key_id.startswith("rzp_test_YOUR"))

    if is_configured:
        # Full live payment link creation
        result = await create_payment_link(
            amount_inr=5000.0,
            description="OmniSales Enterprise Test Payment",
            customer_name="Test Enterprise Client",
            customer_email="billing@example.com",
        )
        assert result["status"] == "created"
        assert result["is_simulated"] is False
        assert result["short_url"].startswith("https://rzp.io/")
        print(f"\n[OK] [Razorpay Live Evidence] Link ID: {result['id']} | URL: {result['short_url']}")
    else:
        # Live endpoint contract probe: verify direct connection to api.razorpay.com
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                RAZORPAY_API_URL,
                json={"amount": 500000, "currency": "INR", "description": "Probe"},
                auth=("rzp_probe_key", "invalid_secret"),
            )
            # Razorpay returns 401 with structured error JSON from their real edge servers
            assert resp.status_code == 401, f"Expected 401 from Razorpay API, got {resp.status_code}"
            body = resp.json()
            assert "error" in body, "Expected Razorpay error payload from api.razorpay.com"
            print(f"\n[OK] [Razorpay Edge Verification] api.razorpay.com reachable and responded with authentic Razorpay error: {body['error'].get('code')}")

        # Verify fallback simulation returns properly tagged response
        sim_res = await create_payment_link(
            amount_inr=5000.0,
            description="OmniSales Enterprise Test Payment",
        )
        assert sim_res["status"] == "created"
        assert sim_res["is_simulated"] is True
        print("[INFO] [Razorpay Sandbox Fallback] Clean simulation active (set RAZORPAY_KEY_ID in .env for live test-mode keys)")
