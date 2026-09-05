"""Shared HubSpot Client — Bidirectional sync, timeline logging, and property updates."""

from __future__ import annotations

import datetime
import json
import logging
import os
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)

HUBSPOT_BASE = "https://api.hubapi.com/crm/v3"

STAGE_TO_HUBSPOT = {
    "discovery": "appointmentscheduled",
    "proposal": "presentationscheduled",
    "negotiation": "decisionmakerboughtin",
    "contract_sent": "contractsent",
    "closed_won": "closedwon",
    "closed_lost": "closedlost",
}

HUBSPOT_TO_STAGE = {
    "appointmentscheduled": "discovery",
    "presentationscheduled": "proposal",
    "decisionmakerboughtin": "negotiation",
    "contractsent": "contract_sent",
    "closedwon": "closed_won",
    "closedlost": "closed_lost",
}

STATUS_TO_HUBSPOT_LEAD = {
    "new": "NEW",
    "contacted": "IN_PROGRESS",
    "replied": "CONNECTED",
    "booked": "OPEN_DEAL",
    "dead": "UNQUALIFIED",
}

HUBSPOT_LEAD_TO_STATUS = {
    "NEW": "new",
    "IN_PROGRESS": "contacted",
    "OPEN": "contacted",
    "CONNECTED": "replied",
    "OPEN_DEAL": "booked",
    "UNQUALIFIED": "dead",
}

ASSOCIATION_TYPE_IDS = {
    "deal": 214,
    "deals": 214,
    "contact": 202,
    "contacts": 202,
    "company": 190,
    "companies": 190,
}


def get_hubspot_token() -> str:
    return os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()


def hubspot_headers() -> dict:
    return {
        "Authorization": f"Bearer {get_hubspot_token()}",
        "Content-Type": "application/json",
    }


async def post_hubspot_engagement_note(object_type: str, object_id: str, note_body: str) -> str | None:
    """Post an audit note to an object's timeline in HubSpot."""
    token = get_hubspot_token()
    if not token or not object_id:
        return None
    assoc_type = ASSOCIATION_TYPE_IDS.get(object_type.lower(), 214)
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{HUBSPOT_BASE}/objects/notes",
                headers=hubspot_headers(),
                json={
                    "properties": {
                        "hs_note_body": note_body,
                        "hs_timestamp": now_iso,
                    },
                    "associations": [
                        {
                            "to": {"id": str(object_id)},
                            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": assoc_type}],
                        }
                    ],
                },
            )
            if resp.status_code in (200, 201):
                note_id = str(resp.json().get("id"))
                logger.info("✅ Attached HubSpot note %s to %s %s", note_id, object_type, object_id)
                return note_id
            else:
                logger.warning("HubSpot note failed for %s %s: %s %s", object_type, object_id, resp.status_code, resp.text)
    except Exception as e:
        logger.warning("HubSpot note exception: %s", e)
    return None


async def update_hubspot_deal_stage(deal_id: str, stage: str) -> bool:
    """Patch dealstage property on HubSpot deal."""
    token = get_hubspot_token()
    if not token or not deal_id:
        return False
    hs_stage = STAGE_TO_HUBSPOT.get(stage.lower(), stage)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.patch(
                f"{HUBSPOT_BASE}/objects/deals/{deal_id}",
                headers=hubspot_headers(),
                json={"properties": {"dealstage": hs_stage}},
            )
            if resp.status_code == 200:
                logger.info("✅ HubSpot deal %s stage patched to %s", deal_id, hs_stage)
                return True
    except Exception as e:
        logger.warning("HubSpot deal stage patch exception: %s", e)
    return False


async def update_hubspot_contact_status(contact_id: str, status: str) -> bool:
    """Patch hs_lead_status on HubSpot contact."""
    token = get_hubspot_token()
    if not token or not contact_id:
        return False
    hs_status = STATUS_TO_HUBSPOT_LEAD.get(status.lower(), "IN_PROGRESS")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.patch(
                f"{HUBSPOT_BASE}/objects/contacts/{contact_id}",
                headers=hubspot_headers(),
                json={"properties": {"hs_lead_status": hs_status}},
            )
            if resp.status_code == 200:
                logger.info("✅ HubSpot contact %s status patched to %s", contact_id, hs_status)
                return True
    except Exception as e:
        logger.warning("HubSpot contact status patch exception: %s", e)
    return False


async def associate_deal_and_contact(deal_id: str, contact_id: str) -> bool:
    """Create a default association between a deal and a contact in HubSpot."""
    token = get_hubspot_token()
    if not token or not deal_id or not contact_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.put(
                f"https://api.hubapi.com/crm/v4/objects/deals/{deal_id}/associations/default/contacts/{contact_id}",
                headers=hubspot_headers(),
            )
            return resp.status_code in (200, 201, 204)
    except Exception as e:
        logger.warning("HubSpot association error: %s", e)
        return False
