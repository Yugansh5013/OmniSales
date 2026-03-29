"""CRM Simulator MCP Server — simulates HubSpot/Salesforce against PostgreSQL."""

import json
import logging
from uuid import uuid4

import asyncpg
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("CRM Simulator MCP")

_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        import os
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", ""),
            min_size=2, max_size=5,
            ssl="require",
        )
    return _pool


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
    # Convert special types for JSON serialization
    for key in result:
        if hasattr(result[key], 'isoformat'):
            result[key] = result[key].isoformat()
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
            if hasattr(d[key], 'isoformat'):
                d[key] = d[key].isoformat()
        results.append(d)
    return results


@mcp.tool()
async def update_deal(deal_id: str, stage: str = "", risk_level: str = "") -> dict:
    """Update a deal's stage and/or risk level.

    Args:
        deal_id: UUID of the deal
        stage: New pipeline stage
        risk_level: New risk assessment
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
    query = f"UPDATE deals SET {', '.join(updates)} WHERE id = ${idx}"
    await pool.execute(query, *params)
    return {"deal_id": deal_id, "updated": True}


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
        if hasattr(result[key], 'isoformat'):
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
    """Update a lead's ICP score, tier, and/or status."""
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
    query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ${idx}"
    await pool.execute(query, *params)
    return {"lead_id": lead_id, "updated": True}


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
        if hasattr(result[key], 'isoformat'):
            result[key] = result[key].isoformat()
    return result


@mcp.tool()
async def list_accounts(min_churn_risk: float = 0.0) -> list[dict]:
    """List all accounts, optionally filtered by minimum churn risk threshold."""
    pool = await _get_pool()
    query = ("SELECT id, company, arr, plan, health_score, churn_risk, usage_pct, "
             "support_tickets, last_login, metadata FROM accounts")
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
            if hasattr(d[key], 'isoformat'):
                d[key] = d[key].isoformat()
        results.append(d)
    return results


@mcp.tool()
async def log_agent_action(deal_id: str, agent_name: str, action: str, reasoning: str) -> dict:
    """Append an entry to a deal's immutable agent_log audit trail.

    Args:
        deal_id: UUID of the deal
        agent_name: Name of the agent (closer|prospector|guardian)
        action: Action taken (e.g., "classified_risk", "drafted_email")
        reasoning: Why this action was taken
    """
    pool = await _get_pool()
    import datetime
    log_entry = json.dumps({
        "agent": agent_name,
        "action": action,
        "reasoning": reasoning,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    await pool.execute(
        "UPDATE deals SET agent_log = array_append(agent_log, $1::jsonb), updated_at = NOW() WHERE id = $2",
        log_entry, deal_id,
    )
    return {"deal_id": deal_id, "logged": True}


if __name__ == "__main__":
    import uvicorn
    mcp_app = mcp.http_app(path="/mcp")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8001)
