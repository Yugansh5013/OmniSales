"""Inbound email polling — detects prospect replies via IMAP and feeds them back
into the Closer agent's deal thread so it can react (classify risk / handle
objection / draft next follow-up) to what the human actually wrote.

Scoped to Closer only: it's the only agent with a real two-way conversation
concept (deals.closer_thread). Matches replies back to a deal via a hidden
[ref:xxxxxxxx] tag embedded in the outbound subject line (the last 8 chars
of the deal's UUID — kept in Re: subjects by every mail client). Uses the
*last* 8 chars, not the first, because this dataset's seed UUIDs all share
the same leading "20000000-0000-0000-0000-" prefix — only the tail varies.
"""

from __future__ import annotations

import email
import imaplib
import logging
import os
import re
from email.header import decode_header

logger = logging.getLogger(__name__)

REF_TAG_RE = re.compile(r"\[ref:([0-9a-fA-F]{8})\]")
QUOTE_MARKERS = [
    re.compile(r"^On .+wrote:\s*$", re.IGNORECASE),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}", re.IGNORECASE),
    re.compile(r"^From:\s.+$", re.IGNORECASE),
    re.compile(r"^>"),
]


def build_ref_tag(deal_id: str) -> str:
    """Last 8 hex chars of a deal UUID — where this dataset's actual entropy is, short enough to survive Re: subjects."""
    return str(deal_id)[-8:]


def _decode(raw) -> str:
    if raw is None:
        return ""
    parts = decode_header(raw)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _strip_quoted(body: str) -> str:
    """Keep only the human-written portion of a reply, dropping the quoted original thread below it."""
    lines = body.splitlines()
    kept = []
    for line in lines:
        if any(marker.match(line.strip()) for marker in QUOTE_MARKERS):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def _extract_plain_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
        return ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""


def fetch_new_replies() -> list[dict]:
    """Poll the configured IMAP inbox for unseen replies tagged with [ref:xxxxxxxx].

    Returns [] on missing config or any IMAP failure — never raises, since this
    runs on a background timer and one bad poll shouldn't crash the loop.
    """
    user = os.environ.get("GMAIL_IMAP_USER", "").strip() or os.environ.get("IMAP_USER", "").strip()
    app_password = os.environ.get("GMAIL_IMAP_APP_PASSWORD", "").strip() or os.environ.get("IMAP_PASSWORD", "").strip()
    if not user or not app_password:
        return []

    host = os.environ.get("IMAP_HOST", "imap.gmail.com").strip()
    try:
        port = int(os.environ.get("IMAP_PORT", "993").strip())
    except (ValueError, TypeError):
        port = 993

    results = []
    try:
        with imaplib.IMAP4_SSL(host, port) as conn:
            conn.login(user, app_password)
            conn.select("INBOX")
            status, data = conn.search(None, "UNSEEN")
            if status != "OK":
                return []
            for num in data[0].split():
                status, msg_data = conn.fetch(num, "(RFC822)")
                if status != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                subject = _decode(msg.get("Subject"))
                match = REF_TAG_RE.search(subject)
                if not match:
                    continue
                from_addr = email.utils.parseaddr(_decode(msg.get("From")))[1].lower().strip()
                # Ignore messages sent from Resend outbound domain (the system's own outgoing emails)
                if "resend.dev" in from_addr or from_addr.startswith("onboarding@") or from_addr.startswith("notifications@"):
                    continue

                body = _strip_quoted(_extract_plain_text(msg))
                if not body:
                    continue
                results.append({
                    "deal_ref": match.group(1),
                    "from_addr": from_addr,
                    "subject": subject,
                    "body": body,
                })
    except Exception as e:
        logger.warning("IMAP poll failed: %s", e)
        return []

    return results
