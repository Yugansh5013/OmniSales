"""IMAP Reply Watcher — Polls incoming emails and re-triggers Closer with prospect replies."""

from __future__ import annotations

import os
import sys
import json
import time
import email
import imaplib
import logging
from email.header import decode_header
from datetime import datetime
import asyncio
import httpx

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.db import execute, fetch_all, fetch_one
from shared.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("reply_watcher")

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")


def _decode_str(header_val: str | None) -> str:
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result)


def _extract_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in cdispo:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return body.strip()


async def process_incoming_reply(from_email: str, subject: str, body: str) -> bool:
    """Match incoming reply against active deals and trigger Closer."""
    logger.info("Processing reply from <%s> | Subject: '%s'", from_email, subject)

    # Search for matching deal by company name or recipient in email thread
    deals = await fetch_all("SELECT id, company, closer_thread, risk_level FROM deals WHERE status = 'active' OR status = 'open' LIMIT 50")
    if not deals:
        logger.warning("No active deals found to match reply.")
        return False

    matched_deal = None
    clean_from = from_email.lower()
    clean_sub = subject.lower()

    for d in deals:
        company = (d.get("company") or "").lower()
        if company and (company in clean_sub or company in clean_from or company in body.lower()):
            matched_deal = d
            break
        # Also check thread
        th = d.get("closer_thread", [])
        if isinstance(th, str):
            try:
                th = json.loads(th)
            except Exception:
                th = []
        if isinstance(th, list):
            for m in th:
                if isinstance(m, dict) and m.get("to", "").lower() in clean_from:
                    matched_deal = d
                    break
        if matched_deal:
            break

    # Fallback to first stalled deal if demo message
    if not matched_deal and deals:
        matched_deal = deals[0]
        logger.info("Defaulting demo reply to deal: %s (%s)", matched_deal.get("id"), matched_deal.get("company"))

    deal_id = matched_deal.get("id")
    company = matched_deal.get("company")

    # Update thread
    thread = matched_deal.get("closer_thread", [])
    if isinstance(thread, str):
        try:
            thread = json.loads(thread)
        except Exception:
            thread = []
    if not isinstance(thread, list):
        thread = []

    thread.append({
        "from": from_email,
        "to": "sales@omnisales.ai",
        "subject": subject,
        "body": body,
        "timestamp": datetime.utcnow().isoformat(),
    })

    await execute(
        "UPDATE deals SET closer_thread = $1, risk_level = 'stalled', last_activity = NOW(), updated_at = NOW() WHERE id = $2",
        json.dumps(thread),
        deal_id,
        org_id="a0000000-0000-0000-0000-000000000001",
    )
    logger.info("Updated closer_thread for deal %s (%s). Triggering Closer agent...", deal_id, company)

    # Re-trigger Closer agent via API Gateway
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{GATEWAY_URL}/api/deals/{deal_id}/trigger")
            logger.info("Closer triggered successfully for deal %s: status=%d", deal_id, resp.status_code)
            return True
    except Exception as e:
        logger.exception("Failed to trigger Closer for deal %s: %s", deal_id, e)
        return False


def run_imap_poll_loop(poll_interval: int = 30):
    """Poll IMAP mailbox continuously."""
    imap_host = os.environ.get("IMAP_HOST", "").strip()
    imap_port = int(os.environ.get("IMAP_PORT", "993"))
    imap_user = os.environ.get("IMAP_USER", "").strip()
    imap_pass = os.environ.get("IMAP_PASSWORD", "").strip()

    if not imap_host or not imap_user or not imap_pass:
        logger.warning("IMAP credentials not fully configured in environment (IMAP_HOST, IMAP_USER, IMAP_PASSWORD).")
        logger.info("Running in demo mock mode — listening for simulated reply triggers.")
        return

    logger.info("Starting IMAP poll loop on %s:%d for %s (interval=%ds)", imap_host, imap_port, imap_user, poll_interval)
    while True:
        try:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            mail.login(imap_user, imap_pass)
            mail.select("INBOX")

            status, messages = mail.search(None, "UNSEEN")
            if status == "OK" and messages[0]:
                for num in messages[0].split():
                    res, data = mail.fetch(num, "(RFC822)")
                    if res != "OK" or not data or not data[0]:
                        continue
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    from_hdr = _decode_str(msg.get("From"))
                    sub_hdr = _decode_str(msg.get("Subject"))
                    body = _extract_body(msg)

                    asyncio.run(process_incoming_reply(from_hdr, sub_hdr, body))

                    # Mark as seen
                    mail.store(num, "+FLAGS", "\\Seen")

            mail.close()
            mail.logout()
        except Exception as e:
            logger.error("IMAP poll iteration failed: %s", e)

        time.sleep(poll_interval)


if __name__ == "__main__":
    run_imap_poll_loop()
