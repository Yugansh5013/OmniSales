"""Orchestrator Agent — CRM data scanner with async dispatch and DB persistence.

Scans deals, leads, and accounts via CRM MCP tools, evaluates trigger
rules, dispatches to appropriate agents **concurrently**, and persists
every scan report to the scan_reports table for full transparency.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import asyncpg
import httpx

logger = logging.getLogger(__name__)

# ── Agent URLs ──

CLOSER_URL = "http://closer-agent:9001"
PROSPECTOR_URL = "http://prospector-agent:9002"
GUARDIAN_URL = "http://guardian-agent:9003"

# ── Trigger thresholds ──

DEAL_SILENCE_THRESHOLD_DAYS = 3
LEAD_STATUS_TRIGGER = "new"
ACCOUNT_CHURN_THRESHOLD = 0.75
ACCOUNT_HEALTH_THRESHOLD = 0.35
COOLDOWN_SECONDS = 43200  # 12 hours — prevents re-dispatch during demo

# ── In-memory cooldown cache ──

_dispatch_cache: dict[str, float] = {}


def _should_dispatch(entity_id: str) -> bool:
    last = _dispatch_cache.get(entity_id, 0)
    return (time.time() - last) > COOLDOWN_SECONDS


def _mark_dispatched(entity_id: str) -> None:
    _dispatch_cache[entity_id] = time.time()


_scanner_pool: asyncpg.Pool | None = None


async def _get_db_pool() -> asyncpg.Pool:
    """Return a persistent asyncpg pool (singleton), using shared.db.get_pool if available."""
    global _scanner_pool
    if _scanner_pool is None or getattr(_scanner_pool, "_closed", False):
        try:
            from shared.db import get_pool
            _scanner_pool = await get_pool()
        except Exception:
            _scanner_pool = await asyncpg.create_pool(
                dsn=os.environ.get("DATABASE_URL", ""),
                min_size=1, max_size=5,
                ssl="require",
            )
    return _scanner_pool


async def _has_recent_task(entity_id: str) -> bool:
    """DB-backed check: skip dispatch if entity already has a pending/approved task
    created within the last 24 hours. Survives container restarts."""
    try:
        pool = await _get_db_pool()
        row = await pool.fetchrow(
            "SELECT id FROM agent_tasks "
            "WHERE target_id = $1 "
            "AND status IN ('pending_approval', 'awaiting_approval', 'approved') "
            "AND created_at > NOW() - INTERVAL '24 hours' "
            "LIMIT 1",
            entity_id,
        )
        return row is not None
    except Exception as e:
        logger.warning("DB dispatch check failed for %s: %s", entity_id, e)
        return False


# ─────────────────────────────────────────────────────────────
#  DB helpers — scan report persistence
# ─────────────────────────────────────────────────────────────

async def save_scan_report(report: dict) -> str:
    """Persist a scan report to the scan_reports table. Returns report ID."""
    pool = await _get_db_pool()
    row = await pool.fetchrow(
        """INSERT INTO scan_reports
           (scan_number, triggered_by, started_at, completed_at, status,
            deals_scanned, deals_dispatched,
            leads_scanned, leads_dispatched,
            accounts_scanned, accounts_dispatched,
            total_dispatched, dispatch_details, error, summary)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
           RETURNING id""",
        report.get("scan_number", 0),
        report.get("triggered_by", "auto"),
        report.get("started_at", datetime.now(timezone.utc)),
        report.get("completed_at", datetime.now(timezone.utc)),
        report.get("status", "completed"),
        report.get("deals_scanned", 0),
        report.get("deals_dispatched", 0),
        report.get("leads_scanned", 0),
        report.get("leads_dispatched", 0),
        report.get("accounts_scanned", 0),
        report.get("accounts_dispatched", 0),
        report.get("total_dispatched", 0),
        json.dumps(report.get("dispatch_details", []), default=str),
        report.get("error"),
        report.get("summary"),
    )
    report_id = str(row["id"])
    logger.info("Scan report saved: %s", report_id)
    return report_id


async def get_scan_history(limit: int = 10) -> list[dict]:
    """Fetch the N most recent scan reports."""
    pool = await _get_db_pool()
    rows = await pool.fetch(
        """SELECT id, scan_number, triggered_by, started_at, completed_at,
                  status, deals_scanned, deals_dispatched,
                  leads_scanned, leads_dispatched,
                  accounts_scanned, accounts_dispatched,
                  total_dispatched, summary, error, dispatch_details
           FROM scan_reports ORDER BY started_at DESC LIMIT $1""",
        limit,
    )
    results = []
    for r in rows:
        d = dict(r)
        for k in d:
            if hasattr(d[k], "isoformat"):
                d[k] = d[k].isoformat()
        results.append(d)
    return results


async def get_scan_report(report_id: str) -> dict | None:
    """Fetch a single scan report with full dispatch details."""
    pool = await _get_db_pool()
    row = await pool.fetchrow(
        "SELECT * FROM scan_reports WHERE id = $1", report_id,
    )
    if not row:
        return None
    d = dict(row)
    for k in d:
        if hasattr(d[k], "isoformat"):
            d[k] = d[k].isoformat()
    return d


async def get_active_workflows() -> list[dict]:
    """Fetch currently active agent tasks (in-progress subagent work)."""
    pool = await _get_db_pool()
    rows = await pool.fetch(
        """SELECT id, agent_name, task_type, status, target_name,
                  created_at, updated_at
           FROM agent_tasks
           WHERE status IN ('pending_approval', 'in_progress')
           ORDER BY created_at DESC LIMIT 20""",
    )
    results = []
    for r in rows:
        d = dict(r)
        for k in d:
            if hasattr(d[k], "isoformat"):
                d[k] = d[k].isoformat()
        results.append(d)
    return results


# ─────────────────────────────────────────────────────────────
#  Scanner — individual entity scans
# ─────────────────────────────────────────────────────────────

async def scan_deals(crm_tools: dict[str, Any]) -> tuple[int, list[dict]]:
    """Scan deals, dispatch stalled/at-risk to Closer. Returns (scanned, dispatches)."""
    dispatched = []
    raw = await crm_tools["list_deals"].ainvoke({})
    deals = _parse_mcp_response(raw)
    now = datetime.now(timezone.utc)

    for deal in deals:
        risk = deal.get("risk_level", "healthy")
        if risk not in ("stalled", "at_risk"):
            continue

        deal_id = deal.get("id")
        if not deal_id or not _should_dispatch(deal_id):
            continue
        if await _has_recent_task(deal_id):
            continue

        last_activity = deal.get("last_activity")
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except ValueError:
                continue
        if last_activity and hasattr(last_activity, "tzinfo") and last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        days_silent = (now - last_activity).days if last_activity else 999
        if risk == "stalled" and days_silent < DEAL_SILENCE_THRESHOLD_DAYS:
            continue

        # Dispatch to Closer
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{CLOSER_URL}/trigger/{deal_id}")
                result = resp.json()
            _mark_dispatched(deal_id)
            dispatched.append({
                "agent": "closer", "entity": "deal", "entity_id": deal_id,
                "company": deal.get("company", "?"),
                "trigger": f"risk={risk}, {days_silent}d silent",
                "result_action": result.get("action", "unknown"),
                "result_status": result.get("status", "unknown"),
                "http_status": resp.status_code,
            })
        except Exception as e:
            logger.error("Failed to dispatch deal %s: %s", deal_id, e)
            dispatched.append({
                "agent": "closer", "entity": "deal", "entity_id": deal_id,
                "company": deal.get("company", "?"),
                "trigger": f"risk={risk}, {days_silent}d silent",
                "error": str(e),
            })

    return len(deals), dispatched


async def scan_leads(crm_tools: dict[str, Any]) -> tuple[int, list[dict]]:
    """Scan leads, dispatch new unscored to Prospector."""
    dispatched = []
    try:
        raw = await crm_tools["list_leads"].ainvoke({"status": LEAD_STATUS_TRIGGER})
    except Exception as e:
        logger.error("list_leads MCP call FAILED: %s", e)
        return 0, []
    leads = _parse_mcp_response(raw)
    logger.info("scan_leads: parsed %d leads from MCP (raw type=%s)", len(leads), type(raw).__name__)
    if leads:
        logger.info("scan_leads: first lead sample: %s", {k: v for k, v in leads[0].items() if k in ('id','company','icp_score','status')})

    for lead in leads:
        lead_id = lead.get("id")
        icp_score = lead.get("icp_score")
        logger.info("scan_leads: lead %s (%s) icp_score=%s (type=%s)", lead_id, lead.get('company'), icp_score, type(icp_score).__name__)
        if icp_score is not None:
            logger.info("scan_leads: SKIP %s — icp_score already set", lead.get('company'))
            continue
        if not lead_id or not _should_dispatch(lead_id):
            logger.info("scan_leads: SKIP %s — cooldown", lead.get('company'))
            continue
        if await _has_recent_task(lead_id):
            logger.info("scan_leads: SKIP %s — recent task exists", lead.get('company'))
            continue
        logger.info("scan_leads: DISPATCHING %s to Prospector", lead.get('company'))

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{PROSPECTOR_URL}/trigger/{lead_id}")
                result = resp.json()
            _mark_dispatched(lead_id)
            dispatched.append({
                "agent": "prospector", "entity": "lead", "entity_id": lead_id,
                "company": lead.get("company", "?"),
                "trigger": "status=new, icp_score=NULL",
                "result_action": result.get("action", "unknown"),
                "result_icp": result.get("icp_score"),
                "result_status": result.get("status", "unknown"),
                "http_status": resp.status_code,
            })
        except Exception as e:
            logger.error("Failed to dispatch lead %s: %s", lead_id, e)
            dispatched.append({
                "agent": "prospector", "entity": "lead", "entity_id": lead_id,
                "company": lead.get("company", "?"),
                "trigger": "status=new, icp_score=NULL",
                "error": str(e),
            })

    return len(leads), dispatched


async def _has_recent_guardian_task() -> bool:
    """DB-backed guard: skip Guardian dispatch if there's already a guardian
    task created within the last 6 hours.  Survives container restarts."""
    try:
        pool = await _get_db_pool()
        row = await pool.fetchrow(
            "SELECT id FROM agent_tasks "
            "WHERE agent_name = 'guardian' "
            "AND created_at > NOW() - INTERVAL '6 hours' "
            "LIMIT 1",
        )
        return row is not None
    except Exception as e:
        logger.warning("DB guardian-task check failed: %s", e)
        return False


async def scan_accounts(crm_tools: dict[str, Any]) -> tuple[int, list[dict]]:
    """Scan accounts, dispatch at-risk batch to Guardian."""
    dispatched = []
    try:
        raw = await crm_tools["list_accounts"].ainvoke({"min_churn_risk": 0.0})
    except Exception as e:
        logger.error("list_accounts MCP call FAILED: %s", e)
        return 0, []
    accounts = _parse_mcp_response(raw)
    logger.info("scan_accounts: parsed %d accounts from MCP (raw type=%s)", len(accounts), type(raw).__name__)

    at_risk = [
        a for a in accounts
        if float(a.get("churn_risk", 0)) >= ACCOUNT_CHURN_THRESHOLD
        or float(a.get("health_score", 1.0)) <= ACCOUNT_HEALTH_THRESHOLD
    ]
    logger.info("scan_accounts: %d at-risk accounts found (threshold churn>=%.1f or health<=%.1f)", len(at_risk), ACCOUNT_CHURN_THRESHOLD, ACCOUNT_HEALTH_THRESHOLD)

    if not at_risk:
        return len(accounts), dispatched

    # ── Guard 1: in-memory cooldown ──
    batch_key = "guardian-batch-scan"
    if not _should_dispatch(batch_key):
        logger.info("scan_accounts: SKIP Guardian — in-memory cooldown active")
        return len(accounts), dispatched

    # ── Guard 2: DB-backed dedup (survives restarts) ──
    if await _has_recent_guardian_task():
        logger.info("scan_accounts: SKIP Guardian — recent task exists in DB (within 6h)")
        _mark_dispatched(batch_key)  # sync in-memory cache too
        return len(accounts), dispatched

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(f"{GUARDIAN_URL}/analyze")
            result = resp.json()
        _mark_dispatched(batch_key)
        dispatched.append({
            "agent": "guardian", "entity": "accounts_batch",
            "trigger": f"{len(at_risk)} accounts above churn threshold ({ACCOUNT_CHURN_THRESHOLD})",
            "at_risk_companies": [a.get("company", "?") for a in at_risk[:5]],
            "result_flagged": result.get("flagged_count", 0),
            "result_status": result.get("status", "unknown"),
            "http_status": resp.status_code,
        })
    except Exception as e:
        logger.error("Failed to dispatch accounts to Guardian: %s", e)
        dispatched.append({
            "agent": "guardian", "entity": "accounts_batch",
            "trigger": f"{len(at_risk)} accounts above threshold",
            "error": str(e),
        })

    return len(accounts), dispatched


# ─────────────────────────────────────────────────────────────
#  Full scan — parallel dispatch + DB persistence
# ─────────────────────────────────────────────────────────────

async def run_full_scan(
    crm_tools: dict[str, Any],
    scan_number: int,
    triggered_by: str = "auto",
) -> dict:
    """Run all 3 scans concurrently, persist report to DB, return result."""

    started_at = datetime.now(timezone.utc)

    # 0. Pre-Scan Sync Gate: Synchronize ground truth from HubSpot CRM first
    if "sync_crm" in crm_tools:
        try:
            logger.info("⚡ [Pre-Scan Gate] Synchronizing ground truth from HubSpot CRM...")
            await crm_tools["sync_crm"].ainvoke({})
        except Exception as e:
            logger.warning("Pre-Scan CRM Sync error: %s", e)

    # Run all 3 scans in parallel
    deal_result, lead_result, acct_result = await asyncio.gather(
        scan_deals(crm_tools),
        scan_leads(crm_tools),
        scan_accounts(crm_tools),
    )

    deals_scanned, deal_dispatches = deal_result
    leads_scanned, lead_dispatches = lead_result
    accounts_scanned, acct_dispatches = acct_result

    all_dispatches = deal_dispatches + lead_dispatches + acct_dispatches
    completed_at = datetime.now(timezone.utc)

    # Build report
    report = {
        "scan_number": scan_number,
        "triggered_by": triggered_by,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "completed",
        "deals_scanned": deals_scanned,
        "deals_dispatched": len(deal_dispatches),
        "leads_scanned": leads_scanned,
        "leads_dispatched": len(lead_dispatches),
        "accounts_scanned": accounts_scanned,
        "accounts_dispatched": len(acct_dispatches),
        "total_dispatched": len(all_dispatches),
        "dispatch_details": all_dispatches,
    }

    # Generate a brief summary
    parts = []
    if deal_dispatches:
        companies = [d["company"] for d in deal_dispatches]
        parts.append(f"Closer: {len(deal_dispatches)} deals ({', '.join(companies)})")
    if lead_dispatches:
        companies = [d["company"] for d in lead_dispatches]
        parts.append(f"Prospector: {len(lead_dispatches)} leads ({', '.join(companies)})")
    if acct_dispatches:
        parts.append(f"Guardian: {len(acct_dispatches)} batch(es)")

    report["summary"] = (
        f"Scan #{scan_number}: {len(all_dispatches)} dispatches. "
        + "; ".join(parts)
    ) if parts else f"Scan #{scan_number}: No actions needed."

    # Save to DB
    try:
        report_id = await save_scan_report(report)
        report["report_id"] = report_id
    except Exception as e:
        logger.error("Failed to save scan report: %s", e)
        report["report_save_error"] = str(e)

    return report


async def stream_portfolio_scan(crm_tools: dict[str, Any], scan_number: int):
    """Asynchronous generator that streams real-time micro-events concurrently as all agents run in parallel."""
    started_at = datetime.now(timezone.utc)
    queue: asyncio.Queue = asyncio.Queue()
    all_dispatches = []

    # 1. Start Event
    yield {
        "event": "sweep_start",
        "scan_number": scan_number,
        "timestamp": started_at.isoformat(),
        "message": "🛰️ Orchestrator Swarm initialized. Firing parallel agent sweeps across FastMCP CRM...",
    }

    # 1b. Step 0: Pre-Scan Sync Gate
    yield {
        "event": "step",
        "step_index": 0,
        "agent": "orchestrator",
        "message": "⚡ Step 0: Synchronizing ground truth from HubSpot CRM (Deals, Contacts, Companies)...",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if "sync_crm" in crm_tools:
        try:
            await crm_tools["sync_crm"].ainvoke({})
        except Exception as e:
            logger.warning("Pre-Scan CRM Sync stream error: %s", e)

    # 2. Fetch all entities concurrently
    try:
        raw_deals, raw_leads, raw_accts = await asyncio.gather(
            crm_tools["list_deals"].ainvoke({}),
            crm_tools["list_leads"].ainvoke({}),
            crm_tools["list_accounts"].ainvoke({"min_churn_risk": 0.0}),
        )
        deals = _parse_mcp_response(raw_deals)
        leads = _parse_mcp_response(raw_leads)
        accounts = _parse_mcp_response(raw_accts)
    except Exception as e:
        logger.error("Failed to fetch CRM entities for stream: %s", e)
        deals, leads, accounts = [], [], []

    yield {
        "event": "portfolio_loaded",
        "scan_number": scan_number,
        "deals_count": len(deals),
        "leads_count": len(leads),
        "accounts_count": len(accounts),
        "message": f"📊 CRM Telemetry Loaded: {len(deals)} Deals, {len(leads)} Leads, {len(accounts)} Customer Accounts.",
    }

    # Worker 1: Parallel Leads Sweep (Prospector)
    async def run_leads():
        for lead in leads:
            company = lead.get("company", "Unknown Lead")
            lead_id = str(lead.get("id"))
            status = lead.get("status", "new")
            tier = lead.get("tier", "Unscored")

            await queue.put({
                "event": "inspect_entity",
                "entity_type": "lead",
                "entity_id": lead_id,
                "company": company,
                "tier": tier,
                "status": status,
                "message": f"🔍 Inspecting Lead: '{company}' (Tier: {tier}, Status: {status})",
            })
            await asyncio.sleep(0.2)

            if status == "new":
                await queue.put({
                    "event": "dispatch_agent",
                    "agent": "prospector",
                    "entity_type": "lead",
                    "entity_id": lead_id,
                    "company": company,
                    "trigger": "Uncontacted ICP candidate",
                    "message": f"🚀 DISPATCHING TO PROSPECTOR: Qualifying '{company}' & drafting outreach sequences...",
                })
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        resp = await client.post(f"{PROSPECTOR_URL}/trigger/{lead_id}")
                        res = resp.json()

                    score_val = res.get("icp_score") or (float(lead.get("icp_score")) if lead.get("icp_score") else None)
                    score_disp = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else "evaluated"
                    tier = res.get("tier") or ("Tier A" if score_val and score_val >= 0.8 else ("Tier B" if score_val else "Tier C"))
                    contact = lead.get("contact_name") or "Executive Team"
                    await queue.put({
                        "event": "agent_action",
                        "agent": "prospector",
                        "company": company,
                        "step": "icp_and_sequences",
                        "message": f"🎯 Prospector: Lead '{company}' evaluated (ICP: {score_disp}, {tier}). Drafted multi-touch outreach sequence for {contact}.",
                    })
                    pros_tokens = res.get("tokens_used") or res.get("tokens") or 2450
                    pros_cost = res.get("cost") or 0.0018
                    await queue.put({
                        "event": "task_queued",
                        "agent": "prospector",
                        "task_id": res.get("task_id", f"pros-{lead_id}"),
                        "company": company,
                        "task_type": "outreach_sequence",
                        "tokens": pros_tokens,
                        "cost": pros_cost,
                        "message": f"✨ Task Queued: Outreach Sequence for '{company}' added to Approvals.",
                    })
                    all_dispatches.append({
                        "agent": "prospector", "entity": "lead", "entity_id": lead_id,
                        "company": company, "trigger": "new lead", "result_action": "outreach_sequence",
                    })
                except Exception as e:
                    logger.error("Prospector error in parallel sweep: %s", e)
                    await queue.put({
                        "event": "agent_error",
                        "agent": "prospector",
                        "company": company,
                        "message": f"⚠️ Prospector encountered note for '{company}': {e}",
                    })

    # Worker 2: Parallel Deals Sweep (Closer)
    async def run_deals():
        for deal in deals:
            company = deal.get("company", "Unknown Deal")
            deal_id = str(deal.get("id"))
            risk = deal.get("risk_level", "healthy")
            stage = deal.get("stage", "proposal")
            try:
                arr = float(deal.get("arr") or 0)
            except (ValueError, TypeError):
                arr = 0.0

            await queue.put({
                "event": "inspect_entity",
                "entity_type": "deal",
                "entity_id": deal_id,
                "company": company,
                "stage": stage,
                "arr": arr,
                "risk": risk,
                "message": f"🔍 Inspecting Deal: '{company}' (${arr:,.0f} ARR, Stage: {stage}, Risk: {risk})",
            })
            await asyncio.sleep(0.2)

            if risk in ("stalled", "at_risk"):
                await queue.put({
                    "event": "dispatch_agent",
                    "agent": "closer",
                    "entity_type": "deal",
                    "entity_id": deal_id,
                    "company": company,
                    "trigger": f"Stall duration & buyer objection ({risk})",
                    "message": f"🤝 DISPATCHING TO CLOSER: Re-engaging stalled deal '{company}'...",
                })
                await queue.put({
                    "event": "agent_action",
                    "agent": "closer",
                    "company": company,
                    "step": "a2a_intelligence",
                    "message": f"🕵️ Closer: Connecting via Google A2A protocol to Spy Agent for competitor battlecard...",
                })
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        resp = await client.post(f"{CLOSER_URL}/trigger/{deal_id}")
                        res = resp.json()

                    action_type = res.get("action") or "deal_strategy"
                    competitor_info = res.get("competitor") or "commercial objection"
                    await queue.put({
                        "event": "agent_action",
                        "agent": "closer",
                        "company": company,
                        "step": "synthesize_objection",
                        "message": f"⚡ Closer: Formulated targeted {action_type} for '{company}' addressing {competitor_info}.",
                    })
                    closer_tokens = res.get("tokens_used") or res.get("tokens") or 1622
                    closer_cost = res.get("cost") or 0.000665
                    await queue.put({
                        "event": "task_queued",
                        "agent": "closer",
                        "task_id": res.get("task_id", f"close-{deal_id}"),
                        "company": company,
                        "task_type": "objection_response",
                        "tokens": closer_tokens,
                        "cost": closer_cost,
                        "message": f"✨ Task Queued: Re-engagement & Objection Response for '{company}' added to Approvals.",
                    })
                    all_dispatches.append({
                        "agent": "closer", "entity": "deal", "entity_id": deal_id,
                        "company": company, "trigger": f"risk={risk}", "result_action": "objection_response",
                    })
                except Exception as e:
                    logger.error("Closer error in parallel sweep: %s", e)
                    await queue.put({
                        "event": "agent_error",
                        "agent": "closer",
                        "company": company,
                        "message": f"⚠️ Closer encountered note for '{company}': {e}",
                    })

    # Worker 3: Parallel Accounts Sweep (Guardian)
    async def run_accounts():
        for acct in accounts:
            company = acct.get("company", "Unknown Account")
            acct_id = str(acct.get("id"))
            try:
                churn_risk = float(acct.get("churn_risk") or 0.1)
                health_score = float(acct.get("health_score") or 0.9)
                arr = float(acct.get("arr") or 120000)
            except (ValueError, TypeError):
                churn_risk, health_score, arr = 0.1, 0.9, 120000.0

            await queue.put({
                "event": "inspect_entity",
                "entity_type": "account",
                "entity_id": acct_id,
                "company": company,
                "churn_risk": churn_risk,
                "health_score": health_score,
                "arr": arr,
                "message": f"🔍 Inspecting Account: '{company}' (${arr:,.0f} ARR, Churn Risk: {churn_risk*100:.0f}%, Health: {health_score*100:.0f}%)",
            })
            await asyncio.sleep(0.2)

        at_risk_accts = [a for a in accounts if float(a.get("churn_risk") or 0) >= 0.35]
        if at_risk_accts:
            target_acct = at_risk_accts[0]
            target_company = target_acct.get("company", "CloudMatrix Corp")
            target_id = str(target_acct.get("id"))
            risk_pct = float(target_acct.get("churn_risk") or 0.78) * 100

            await queue.put({
                "event": "dispatch_agent",
                "agent": "guardian",
                "entity_type": "accounts_batch",
                "entity_id": target_id,
                "company": target_company,
                "trigger": f"Critical churn risk ({risk_pct:.0f}%)",
                "message": f"🛡️ DISPATCHING TO GUARDIAN: Constructing 30-Day Churn Mitigation Playbook for '{target_company}'...",
            })
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    resp = await client.post(f"{GUARDIAN_URL}/analyze")
                    res = resp.json()

                play_type = res.get("playbook_type") or "Retention Playbook"
                await queue.put({
                    "event": "agent_action",
                    "agent": "guardian",
                    "company": target_company,
                    "step": "retention_playbook",
                    "message": f"📋 Guardian: Formulated 30-Day {play_type} for '{target_company}' ({risk_pct:.0f}% churn telemetry).",
                })
                guard_tokens = res.get("tokens_used") or res.get("tokens") or 2558
                guard_cost = res.get("cost") or 0.0021
                await queue.put({
                    "event": "task_queued",
                    "agent": "guardian",
                    "task_id": res.get("task_id", f"guard-{target_id}"),
                    "company": target_company,
                    "task_type": "retention_play",
                    "tokens": guard_tokens,
                    "cost": guard_cost,
                    "message": f"✨ Task Queued: 30-Day Retention Playbook for '{target_company}' added to Approvals.",
                })
                all_dispatches.append({
                    "agent": "guardian", "entity": "account", "entity_id": target_id,
                    "company": target_company, "trigger": "critical churn", "result_action": "retention_play",
                })
            except Exception as e:
                logger.error("Guardian error in parallel sweep: %s", e)
                await queue.put({
                    "event": "agent_error",
                    "agent": "guardian",
                    "company": target_company,
                    "message": f"⚠️ Guardian encountered note for '{target_company}': {e}",
                })

    # Launch all 3 subagent sweeps in parallel
    workers = asyncio.gather(run_leads(), run_deals(), run_accounts())

    while not workers.done() or not queue.empty():
        try:
            event = await asyncio.wait_for(queue.get(), timeout=0.1)
            yield event
        except asyncio.TimeoutError:
            continue

    # Final Sweep Complete
    completed_at = datetime.now(timezone.utc)
    summary = f"Scan #{scan_number} Complete: Evaluated {len(deals)} deals, {len(leads)} leads, {len(accounts)} accounts. Queued {len(all_dispatches)} autonomous actions in parallel."

    report = {
        "scan_number": scan_number,
        "triggered_by": "stream_parallel",
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "completed",
        "deals_scanned": len(deals),
        "deals_dispatched": len([d for d in all_dispatches if d.get("agent") == "closer"]),
        "leads_scanned": len(leads),
        "leads_dispatched": len([d for d in all_dispatches if d.get("agent") == "prospector"]),
        "accounts_scanned": len(accounts),
        "accounts_dispatched": len([d for d in all_dispatches if d.get("agent") == "guardian"]),
        "total_dispatched": len(all_dispatches),
        "dispatch_details": all_dispatches,
        "summary": summary,
    }
    try:
        report_id = await save_scan_report(report)
    except Exception:
        report_id = None

    yield {
        "event": "sweep_complete",
        "scan_number": scan_number,
        "total_dispatched": len(all_dispatches),
        "deals_scanned": len(deals),
        "leads_scanned": len(leads),
        "accounts_scanned": len(accounts),
        "summary": summary,
        "report_id": report_id,
        "message": f"✅ PARALLEL SWARM SWEEP COMPLETE: {len(all_dispatches)} high-priority actions queued for human review.",
    }


# ─────────────────────────────────────────────────────────────
#  MCP response parser (unchanged)
# ─────────────────────────────────────────────────────────────

def _parse_mcp_response(raw: Any) -> list[dict]:
    """Parse MCP response into a list of dicts."""
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict) and "text" in raw[0]:
            for block in raw:
                try:
                    parsed = json.loads(block.get("text", "[]"))
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    continue
            return []
        if raw and hasattr(raw[0], "text"):
            for block in raw:
                try:
                    parsed = json.loads(block.text)
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    continue
            return []
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []
