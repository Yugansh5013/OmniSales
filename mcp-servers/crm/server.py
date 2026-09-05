"""CRM MCP Server — Dual-Mode Gateway supporting HubSpot CRM v3 with PostgreSQL."""

import datetime
import json
import logging
import os
from uuid import uuid4

import asyncpg
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("CRM Simulator & HubSpot Gateway MCP")

_pool: asyncpg.Pool | None = None

HUBSPOT_BASE = "https://api.hubapi.com/crm/v3"

# Mapping between OmniSales pipeline stages and HubSpot deal stages
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


def _get_hubspot_token() -> str:
    return os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()


def _hubspot_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_hubspot_token()}",
        "Content-Type": "application/json",
    }


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", ""),
            min_size=2,
            max_size=5,
            ssl="require",
        )
    return _pool


# ── HubSpot API Helpers ──


async def _hubspot_search_deal(company: str) -> str | None:
    """Search HubSpot deals by company name keyword."""
    token = _get_hubspot_token()
    if not token or not company:
        return None
    keyword = company.split()[0].strip()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{HUBSPOT_BASE}/objects/deals/search",
                headers=_hubspot_headers(),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "dealname",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": keyword,
                                }
                            ]
                        }
                    ]
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return str(results[0]["id"])
    except Exception as e:
        logger.warning(f"HubSpot deal search error for {company}: {e}")
    return None


async def _hubspot_update_deal_stage(hs_deal_id: str, stage: str) -> bool:
    """Update dealstage property on live HubSpot deal."""
    token = _get_hubspot_token()
    if not token or not hs_deal_id:
        return False
    hs_stage = STAGE_TO_HUBSPOT.get(stage.lower(), stage)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.patch(
                f"{HUBSPOT_BASE}/objects/deals/{hs_deal_id}",
                headers=_hubspot_headers(),
                json={"properties": {"dealstage": hs_stage}},
            )
            if resp.status_code == 200:
                logger.info(f"HubSpot live deal {hs_deal_id} updated to {hs_stage}")
                return True
            logger.warning(f"HubSpot update deal failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"HubSpot update deal exception: {e}")
    return False


async def _hubspot_create_engagement_note(object_type: str, object_id: str, note_body: str) -> str | None:
    """Add timeline engagement note to live HubSpot entity (deal, contact, or company)."""
    token = _get_hubspot_token()
    if not token or not object_id:
        return None
    assoc_type = ASSOCIATION_TYPE_IDS.get(object_type.lower(), 214)
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{HUBSPOT_BASE}/objects/notes",
                headers=_hubspot_headers(),
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
                logger.info(f"HubSpot note {note_id} attached to {object_type} {object_id}")
                return note_id
            else:
                logger.warning(f"HubSpot create note failed for {object_type} {object_id}: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"HubSpot create note exception: {e}")
    return None


async def _hubspot_create_deal_note(hs_deal_id: str, note_body: str) -> str | None:
    """Add timeline engagement note to live HubSpot deal."""
    return await _hubspot_create_engagement_note("deal", hs_deal_id, note_body)


async def _hubspot_search_contact(email: str) -> str | None:
    """Search HubSpot contact by email."""
    token = _get_hubspot_token()
    if not token or not email:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{HUBSPOT_BASE}/objects/contacts/search",
                headers=_hubspot_headers(),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email,
                                }
                            ]
                        }
                    ]
                },
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    return str(results[0]["id"])
    except Exception as e:
        logger.warning(f"HubSpot contact search error for {email}: {e}")
    return None


async def _hubspot_update_contact_lead(hs_contact_id: str, status: str = "", note_body: str = "") -> bool:
    """Update lead status and append note on HubSpot contact."""
    token = _get_hubspot_token()
    if not token or not hs_contact_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            if status:
                hs_status = STATUS_TO_HUBSPOT_LEAD.get(status.lower(), "IN_PROGRESS")
                await client.patch(
                    f"{HUBSPOT_BASE}/objects/contacts/{hs_contact_id}",
                    headers=_hubspot_headers(),
                    json={"properties": {"hs_lead_status": hs_status}},
                )
            if note_body:
                now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                await client.post(
                    f"{HUBSPOT_BASE}/objects/notes",
                    headers=_hubspot_headers(),
                    json={
                        "properties": {
                            "hs_note_body": note_body,
                            "hs_timestamp": now_iso,
                        },
                        "associations": [
                            {
                                "to": {"id": hs_contact_id},
                                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
                            }
                        ],
                    },
                )
            logger.info(f"HubSpot live contact {hs_contact_id} updated with status={status}")
            return True
    except Exception as e:
        logger.warning(f"HubSpot contact update exception: {e}")
    return False


async def sync_hubspot_crm() -> dict:
    """Full synchronization: pulls deals, contacts, companies from HubSpot into PostgreSQL."""
    token = _get_hubspot_token()
    if not token:
        return {"status": "skipped", "reason": "No HubSpot token configured", "deals": 0, "contacts": 0, "companies": 0}

    pool = await _get_pool()
    headers = _hubspot_headers()
    synced_deals = 0
    synced_contacts = 0
    synced_companies = 0

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Sync Deals
        try:
            r = await client.get(
                f"{HUBSPOT_BASE}/objects/deals?properties=dealname,dealstage,amount,closedate,pipeline&associations=contacts,companies",
                headers=headers,
            )
            if r.status_code == 200:
                deals = r.json().get("results", [])
                for d in deals:
                    hs_id = str(d["id"])
                    props = d.get("properties", {})
                    dealname = props.get("dealname", "") or "Unnamed Deal"
                    company = dealname
                    for suffix in [" Growth License", " Enterprise License", " Enterprise", " Expansion", " Deal", " Pilot"]:
                        if company.endswith(suffix):
                            company = company[:-len(suffix)].strip()
                            break

                    raw_stage = props.get("dealstage", "")
                    stage = HUBSPOT_TO_STAGE.get(raw_stage.lower(), "proposal")
                    raw_amount = props.get("amount")
                    try:
                        arr = float(raw_amount) if raw_amount is not None else 50000.0
                    except (ValueError, TypeError):
                        arr = 50000.0

                    row = await pool.fetchrow("SELECT id FROM deals WHERE hubspot_id = $1 OR company ILIKE $2", hs_id, f"%{company}%")
                    if row:
                        await pool.execute(
                            "UPDATE deals SET hubspot_id = $1, stage = $2, arr = $3, company = $4, updated_at = NOW() WHERE id = $5",
                            hs_id, stage, arr, company, row["id"]
                        )
                    else:
                        new_id = str(uuid4())
                        await pool.execute(
                            "INSERT INTO deals (id, org_id, company, stage, arr, risk_level, hubspot_id, created_at, updated_at) "
                            "VALUES ($1, 'a0000000-0000-0000-0000-000000000001', $2, $3, $4, 'healthy', $5, NOW(), NOW())",
                            new_id, company, stage, arr, hs_id
                        )
                    synced_deals += 1
        except Exception as e:
            logger.error(f"Error syncing deals from HubSpot: {e}")

        # 2. Sync Contacts
        try:
            r = await client.get(
                f"{HUBSPOT_BASE}/objects/contacts?properties=firstname,lastname,email,company,jobtitle,hs_lead_status",
                headers=headers,
            )
            if r.status_code == 200:
                contacts = r.json().get("results", [])
                for c in contacts:
                    hs_id = str(c["id"])
                    props = c.get("properties", {})
                    email = props.get("email", "") or ""
                    if not email or "hubspot.com" in email:
                        continue
                    first = props.get("firstname", "") or ""
                    last = props.get("lastname", "") or ""
                    name = f"{first} {last}".strip() or "Prospect Lead"
                    company = props.get("company", "") or ""
                    if not company:
                        domain = email.split("@")[-1].split(".")[0] if "@" in email else ""
                        company = domain.title() if domain else "Unknown Company"
                    title = props.get("jobtitle", "") or "Executive"
                    raw_status = props.get("hs_lead_status", "")
                    lead_status = HUBSPOT_LEAD_TO_STATUS.get(str(raw_status).upper(), "new")

                    row = await pool.fetchrow("SELECT id FROM leads WHERE hubspot_id = $1 OR email = $2", hs_id, email)
                    if row:
                        await pool.execute(
                            "UPDATE leads SET hubspot_id = $1, contact_name = $2, company = COALESCE(NULLIF($3, ''), company), "
                            "title = $4, status = $5, updated_at = NOW() WHERE id = $6",
                            hs_id, name, company, title, lead_status, row["id"]
                        )
                    else:
                        new_id = str(uuid4())
                        await pool.execute(
                            "INSERT INTO leads (id, org_id, company, contact_name, email, title, status, hubspot_id, created_at, updated_at) "
                            "VALUES ($1, 'a0000000-0000-0000-0000-000000000001', $2, $3, $4, $5, $6, $7, NOW(), NOW())",
                            new_id, company, name, email, title, lead_status, hs_id
                        )
                    synced_contacts += 1
        except Exception as e:
            logger.error(f"Error syncing contacts from HubSpot: {e}")

        # 3. Sync Companies
        try:
            r = await client.get(
                f"{HUBSPOT_BASE}/objects/companies?properties=name,domain,annualrevenue,numberofemployees,industry",
                headers=headers,
            )
            if r.status_code == 200:
                companies = r.json().get("results", [])
                for comp in companies:
                    hs_id = str(comp["id"])
                    props = comp.get("properties", {})
                    name = props.get("name", "") or ""
                    if not name or name.lower() == "hubspot":
                        continue
                    rev_raw = props.get("annualrevenue")
                    try:
                        arr = float(rev_raw) if rev_raw else 120000.0
                    except (ValueError, TypeError):
                        arr = 120000.0

                    row = await pool.fetchrow("SELECT id FROM accounts WHERE hubspot_id = $1 OR company ILIKE $2", hs_id, f"%{name}%")
                    if row:
                        await pool.execute(
                            "UPDATE accounts SET hubspot_id = $1, company = $2, arr = $3, updated_at = NOW() WHERE id = $4",
                            hs_id, name, arr, row["id"]
                        )
                    else:
                        new_id = str(uuid4())
                        await pool.execute(
                            "INSERT INTO accounts (id, org_id, company, arr, plan, health_score, churn_risk, hubspot_id, created_at, updated_at) "
                            "VALUES ($1, 'a0000000-0000-0000-0000-000000000001', $2, $3, 'enterprise', 0.85, 0.15, $4, NOW(), NOW())",
                            new_id, name, arr, hs_id
                        )
                    synced_companies += 1
        except Exception as e:
            logger.error(f"Error syncing companies from HubSpot: {e}")

    logger.info(f"HubSpot CRM sync complete: {synced_deals} deals, {synced_contacts} contacts, {synced_companies} companies")
    return {
        "status": "success",
        "synced": True,
        "deals_count": synced_deals,
        "contacts_count": synced_contacts,
        "companies_count": synced_companies,
    }


@mcp.tool()
async def sync_crm() -> dict:
    """Synchronize deals, contacts, and companies from HubSpot CRM into PostgreSQL before scanning."""
    return await sync_hubspot_crm()


# ── Status & Diagnostic Tools ──


@mcp.tool()
async def get_crm_status() -> dict:
    """Get live status and provider info for the CRM gateway."""
    token = _get_hubspot_token()
    portal_id = os.environ.get("HUBSPOT_PORTAL_ID", "247282404")
    if token:
        masked = f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"
        return {
            "mode": "hubspot_live",
            "provider": "HubSpot CRM v3",
            "connected": True,
            "portal_id": portal_id,
            "token_masked": masked,
            "status": "LIVE_SYNC_ACTIVE",
            "capabilities": ["deals_sync", "contacts_sync", "timeline_notes", "kanban_stage_updates"],
        }
    return {
        "mode": "postgres_local",
        "provider": "PostgreSQL System of Intelligence",
        "connected": True,
        "status": "SIMULATION_FALLBACK",
        "capabilities": ["local_deals", "local_leads", "local_accounts"],
    }


# ── Deal Tools ──


@mcp.tool()
async def get_deal(deal_id: str) -> dict:
    """Get full deal details including email conversation thread and agent log.

    Returns deal record with all fields from the deals table.
    """
    pool = await _get_pool()
    row = await pool.fetchrow("SELECT * FROM deals WHERE id = $1", deal_id)
    if not row:
        return {"error": f"Deal {deal_id} not found"}
    result = dict(row)
    for key in result:
        if hasattr(result[key], "isoformat"):
            result[key] = result[key].isoformat()

    # If HubSpot is active, check if deal has associated HubSpot link
    token = _get_hubspot_token()
    if token and result.get("company"):
        hs_id = await _hubspot_search_deal(result["company"])
        if hs_id:
            result["hubspot_id"] = hs_id
            portal = os.environ.get("HUBSPOT_PORTAL_ID", "247282404")
            result["hubspot_url"] = f"https://app-na2.hubspot.com/contacts/{portal}/record/0-3/{hs_id}"
    return result


@mcp.tool()
async def list_deals(stage: str = "", risk_level: str = "") -> list[dict]:
    """List deals, optionally filtered by stage and/or risk level.

    Args:
        stage: Filter by pipeline stage (discovery|proposal|negotiation|closed_won|closed_lost)
        risk_level: Filter by risk (healthy|at_risk|stalled)
    """
    pool = await _get_pool()
    query = "SELECT id, company, stage, arr, risk_level, last_activity FROM deals WHERE 1=1"
    params = []
    idx = 1

    if stage:
        query += f" AND stage = ${idx}"
        params.append(stage)
        idx += 1
    if risk_level:
        query += f" AND risk_level = ${idx}"
        params.append(risk_level)
        idx += 1

    query += " ORDER BY arr DESC"
    rows = await pool.fetch(query, *params)
    results = []
    for r in rows:
        d = dict(r)
        for key in d:
            if hasattr(d[key], "isoformat"):
                d[key] = d[key].isoformat()
        results.append(d)
    return results


@mcp.tool()
async def update_deal(deal_id: str, stage: str = "", risk_level: str = "") -> dict:
    """Update a deal's stage and/or risk level across PostgreSQL and HubSpot CRM.

    Args:
        deal_id: UUID or identifier of the deal
        stage: New pipeline stage (e.g., proposal, negotiation, closed_won)
        risk_level: New risk assessment (healthy, at_risk, stalled)
    """
    pool = await _get_pool()
    updates = []
    params = []
    idx = 1

    if stage:
        updates.append(f"stage = ${idx}")
        params.append(stage)
        idx += 1
    if risk_level:
        updates.append(f"risk_level = ${idx}")
        params.append(risk_level)
        idx += 1

    if not updates:
        return {"error": "No fields to update"}

    updates.append("updated_at = NOW()")
    params.append(deal_id)
    query = f"UPDATE deals SET {', '.join(updates)} WHERE id = ${idx} RETURNING company"
    row = await pool.fetchrow(query, *params)

    company_name = row["company"] if row else ""

    # Live sync to HubSpot if enabled
    hubspot_synced = False
    hs_deal_id = None
    token = _get_hubspot_token()
    if token:
        if str(deal_id).isdigit():
            hs_deal_id = str(deal_id)
        elif company_name:
            hs_deal_id = await _hubspot_search_deal(company_name)

        if hs_deal_id and stage:
            hubspot_synced = await _hubspot_update_deal_stage(hs_deal_id, stage)
            if risk_level:
                await _hubspot_create_deal_note(
                    hs_deal_id,
                    f"[OmniSales Swarm] Stage updated to '{stage}'. Deal Risk evaluated as '{risk_level}'.",
                )

    return {
        "deal_id": deal_id,
        "updated": True,
        "hubspot_synced": hubspot_synced,
        "hubspot_deal_id": hs_deal_id,
    }


# ── Lead Tools ──


@mcp.tool()
async def get_lead(lead_id: str) -> dict:
    """Get full lead details including enrichment data."""
    pool = await _get_pool()
    row = await pool.fetchrow("SELECT * FROM leads WHERE id = $1", lead_id)
    if not row:
        return {"error": f"Lead {lead_id} not found"}
    result = dict(row)
    for key in result:
        if hasattr(result[key], "isoformat"):
            result[key] = result[key].isoformat()
    return result


@mcp.tool()
async def list_leads(status: str = "", min_icp_score: float = 0.0) -> list[dict]:
    """List leads, optionally filtered by status and minimum ICP score.

    Args:
        status: Filter by lead status (new|contacted|replied|booked|dead)
        min_icp_score: Minimum ICP score threshold (0-1)
    """
    pool = await _get_pool()
    query = "SELECT id, company, contact_name, email, title, icp_score, tier, status FROM leads WHERE 1=1"
    params = []
    idx = 1

    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1
    if min_icp_score > 0:
        query += f" AND (icp_score IS NULL OR icp_score >= ${idx})"
        params.append(min_icp_score)
        idx += 1

    query += " ORDER BY icp_score DESC NULLS LAST"
    rows = await pool.fetch(query, *params)
    return [dict(r) for r in rows]


@mcp.tool()
async def update_lead(lead_id: str, icp_score: float = -1, tier: str = "", status: str = "") -> dict:
    """Update a lead's ICP score, tier, and/or status across PostgreSQL and HubSpot.

    Args:
        lead_id: UUID or identifier of the lead
        icp_score: Computed ICP qualification score (0.0 to 1.0)
        tier: Lead tier (e.g., Tier 1 / A)
        status: Lead status (new, contacted, replied, booked, dead)
    """
    pool = await _get_pool()
    updates = []
    params = []
    idx = 1

    if icp_score >= 0:
        updates.append(f"icp_score = ${idx}")
        params.append(icp_score)
        idx += 1
    if tier:
        updates.append(f"tier = ${idx}")
        params.append(tier)
        idx += 1
    if status:
        updates.append(f"status = ${idx}")
        params.append(status)
        idx += 1

    if not updates:
        return {"error": "No fields to update"}

    updates.append("updated_at = NOW()")
    params.append(lead_id)
    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ${idx} RETURNING email, contact_name"
    row = await pool.fetchrow(query, *params)

    lead_email = row["email"] if row else ""
    lead_name = row["contact_name"] if row else ""

    # Live sync to HubSpot if enabled
    hubspot_synced = False
    hs_contact_id = None
    token = _get_hubspot_token()
    if token and lead_email:
        hs_contact_id = await _hubspot_search_contact(lead_email)
        if hs_contact_id:
            note_content = (
                f"[OmniSales Prospector] Lead Qualified: {lead_name}\n"
                f"• ICP Score: {icp_score}\n"
                f"• Tier: {tier}\n"
                f"• Status: {status}"
            )
            hubspot_synced = await _hubspot_update_contact_lead(
                hs_contact_id, status=status, note_body=note_content
            )

    return {
        "lead_id": lead_id,
        "updated": True,
        "hubspot_synced": hubspot_synced,
        "hubspot_contact_id": hs_contact_id,
    }


# ── Account Tools ──


@mcp.tool()
async def get_account(account_id: str) -> dict:
    """Get full account details including health scores and metadata."""
    pool = await _get_pool()
    row = await pool.fetchrow("SELECT * FROM accounts WHERE id = $1", account_id)
    if not row:
        return {"error": f"Account {account_id} not found"}
    result = dict(row)
    for key in result:
        if hasattr(result[key], "isoformat"):
            result[key] = result[key].isoformat()
    return result


@mcp.tool()
async def list_accounts(min_churn_risk: float = 0.0) -> list[dict]:
    """List all accounts, optionally filtered by minimum churn risk threshold."""
    pool = await _get_pool()
    query = (
        "SELECT id, company, arr, plan, health_score, churn_risk, usage_pct, "
        "support_tickets, last_login, metadata FROM accounts"
    )
    params = []
    if min_churn_risk > 0:
        query += " WHERE churn_risk >= $1"
        params.append(min_churn_risk)
    query += " ORDER BY churn_risk DESC"
    rows = await pool.fetch(query, *params)
    results = []
    for r in rows:
        d = dict(r)
        for key in d:
            if hasattr(d[key], "isoformat"):
                d[key] = d[key].isoformat()
        results.append(d)
    return results


@mcp.tool()
async def log_agent_action(deal_id: str, agent_name: str, action: str, reasoning: str) -> dict:
    """Append an entry to a deal's immutable agent_log audit trail and HubSpot timeline.

    Args:
        deal_id: UUID of the deal
        agent_name: Name of the agent (closer|prospector|guardian|orchestrator)
        action: Action taken (e.g., "classified_risk", "drafted_email")
        reasoning: Why this action was taken
    """
    pool = await _get_pool()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_entry = json.dumps({
        "agent": agent_name,
        "action": action,
        "reasoning": reasoning,
        "timestamp": now_iso,
    })
    row = await pool.fetchrow(
        "UPDATE deals SET agent_log = array_append(agent_log, $1::jsonb), updated_at = NOW() WHERE id = $2 RETURNING company, hubspot_id",
        log_entry,
        deal_id,
    )

    company_name = row["company"] if row else ""
    hubspot_id = row["hubspot_id"] if row and row.get("hubspot_id") else None
    hs_note_id = None
    token = _get_hubspot_token()
    if token:
        hs_deal_id = hubspot_id
        if not hs_deal_id and company_name:
            hs_deal_id = await _hubspot_search_deal(company_name)
        if hs_deal_id:
            note_body = (
                f"🤖 [OmniSales Swarm: {agent_name.upper()}]\n"
                f"Action: {action}\n"
                f"Reasoning: {reasoning}\n"
                f"Audit Timestamp: {now_iso}"
            )
            hs_note_id = await _hubspot_create_deal_note(hs_deal_id, note_body)

    return {
        "deal_id": deal_id,
        "logged": True,
        "hubspot_note_id": hs_note_id,
    }


@mcp.tool()
async def log_lead_action(lead_id: str, agent_name: str, action: str, reasoning: str) -> dict:
    """Log an agent action and append timeline note to contact in HubSpot.

    Args:
        lead_id: UUID of the lead
        agent_name: Name of the agent (prospector|orchestrator)
        action: Action taken (e.g., "qualified_lead", "drafted_sequence")
        reasoning: Why this action was taken
    """
    pool = await _get_pool()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = await pool.fetchrow("SELECT contact_name, email, hubspot_id FROM leads WHERE id = $1", lead_id)
    if not row:
        return {"error": f"Lead {lead_id} not found"}

    hs_note_id = None
    token = _get_hubspot_token()
    if token:
        hs_contact_id = row["hubspot_id"]
        if not hs_contact_id and row["email"]:
            hs_contact_id = await _hubspot_search_contact(row["email"])
        if hs_contact_id:
            note_body = (
                f"🤖 [OmniSales Swarm: {agent_name.upper()}]\n"
                f"Action: {action}\n"
                f"Reasoning: {reasoning}\n"
                f"Audit Timestamp: {now_iso}"
            )
            hs_note_id = await _hubspot_create_engagement_note("contact", hs_contact_id, note_body)

    return {
        "lead_id": lead_id,
        "logged": True,
        "hubspot_note_id": hs_note_id,
    }


@mcp.tool()
async def log_account_action(account_id: str, agent_name: str, action: str, reasoning: str) -> dict:
    """Log an agent action and append timeline note to company in HubSpot.

    Args:
        account_id: UUID of the account
        agent_name: Name of the agent (guardian|orchestrator)
        action: Action taken (e.g., "churn_assessment", "retention_play")
        reasoning: Why this action was taken
    """
    pool = await _get_pool()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = await pool.fetchrow("SELECT company, hubspot_id FROM accounts WHERE id = $1", account_id)
    if not row:
        return {"error": f"Account {account_id} not found"}

    hs_note_id = None
    token = _get_hubspot_token()
    if token:
        hs_company_id = row["hubspot_id"]
        if hs_company_id:
            note_body = (
                f"🤖 [OmniSales Swarm: {agent_name.upper()}]\n"
                f"Action: {action}\n"
                f"Reasoning: {reasoning}\n"
                f"Audit Timestamp: {now_iso}"
            )
            hs_note_id = await _hubspot_create_engagement_note("company", hs_company_id, note_body)

    return {
        "account_id": account_id,
        "logged": True,
        "hubspot_note_id": hs_note_id,
    }


if __name__ == "__main__":
    import uvicorn
    from starlette.responses import JSONResponse
    from shared.errors import setup_error_handlers

    async def _health(request):
        token = _get_hubspot_token()
        return JSONResponse({
            "status": "healthy",
            "service": "mcp-crm",
            "hubspot_live": bool(token),
            "hubspot_portal": os.environ.get("HUBSPOT_PORTAL_ID", "247282404") if token else None,
        })

    async def _sync_route(request):
        res = await sync_hubspot_crm()
        return JSONResponse(res)

    mcp_app = mcp.http_app(path="/mcp")
    setup_error_handlers(mcp_app, service_name="mcp-crm")
    mcp_app.add_route("/health", _health, methods=["GET"])
    mcp_app.add_route("/sync", _sync_route, methods=["POST", "GET"])
    uvicorn.run(mcp_app, host="0.0.0.0", port=8001)
