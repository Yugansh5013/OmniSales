"""Orchestrator Agent V2 — Supervisor with async subagents + chat.

Features:
  - Background CRM scanner (every N seconds)
  - Dispatches to Closer/Prospector/Guardian as async subagents
  - Persists scan reports to scan_reports table
  - Stateless /chat endpoint for manager Q&A
  - /history endpoint for scan report retrieval
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

from agents.orchestrator.scanner import run_full_scan, get_scan_history, get_scan_report
from agents.orchestrator.chat import handle_chat
from shared.skills import SkillRegistry, Skill, SkillInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuration ──

SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL_SECONDS", "300"))  # 5 min default

# ── Skill Registry (A2A) ──

skill_registry = SkillRegistry(
    agent_name="orchestrator-agent",
    agent_description=(
        "Autonomous supervisor agent that scans CRM data, dispatches tasks to "
        "Closer/Prospector/Guardian sub-agents, and answers manager questions."
    ),
    agent_url="http://orchestrator-agent:9004",
)

skill_registry.register(Skill(
    name="scan_crm",
    description="Scan CRM for stalled deals, new leads, and at-risk accounts, then dispatch to appropriate sub-agents",
    agent="orchestrator",
    input_schema=SkillInput(properties={}, required=[]),
    tags=["deals", "leads", "accounts", "scan"],
))
skill_registry.register(Skill(
    name="chat",
    description="Answer manager questions about ongoing workflows, scan history, and agent activity",
    agent="orchestrator",
    input_schema=SkillInput(
        properties={"message": {"type": "string", "description": "The manager's question"}},
        required=["message"],
    ),
    tags=["chat", "question", "status"],
))
skill_registry.register(Skill(
    name="scan_history",
    description="Retrieve recent scan reports with dispatch details",
    agent="orchestrator",
    input_schema=SkillInput(properties={}, required=[]),
    tags=["history", "reports", "audit"],
))

# ── State ──

_last_scan_result: dict | None = None
_scan_count = 0
_scan_task: asyncio.Task | None = None


async def _get_crm_tools() -> dict:
    """Connect to CRM MCP and return tools as a name→tool dict."""
    mcp_config = {
        "crm": {
            "url": os.environ.get("MCP_CRM_URL", "http://mcp-crm:8001/mcp"),
            "transport": "http",
        },
    }
    client = MultiServerMCPClient(mcp_config)
    tools = await client.get_tools()
    return {t.name: t for t in tools}


# ── Background Scanner Loop ──


async def _scan_loop():
    """Background loop — scans CRM every SCAN_INTERVAL seconds, saves reports to DB."""
    global _last_scan_result, _scan_count

    initial_delay = int(os.environ.get("SCAN_INITIAL_DELAY_SECONDS", "600"))  # 10 min default — demo finishes first
    await asyncio.sleep(initial_delay)
    logger.info("Orchestrator scanner started (interval=%ds)", SCAN_INTERVAL)

    while True:
        try:
            _scan_count += 1
            logger.info("── Scan cycle #%d starting ──", _scan_count)

            crm_tools = await _get_crm_tools()
            result = await run_full_scan(crm_tools, _scan_count, triggered_by="auto")
            _last_scan_result = result

            logger.info(
                "── Scan cycle #%d complete ── dispatched %d "
                "(deals=%d, leads=%d, accounts=%d) — report_id=%s",
                _scan_count, result["total_dispatched"],
                result["deals_dispatched"], result["leads_dispatched"],
                result["accounts_dispatched"], result.get("report_id", "?"),
            )
        except Exception as e:
            logger.exception("Scan cycle #%d failed: %s", _scan_count, e)
            _last_scan_result = {
                "scan_number": _scan_count,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        await asyncio.sleep(SCAN_INTERVAL)


# ── Lifespan ──


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scan_task
    auto_scan = os.environ.get("AUTO_SCAN_ENABLED", "false").lower() == "true"
    if auto_scan:
        _scan_task = asyncio.create_task(_scan_loop())
        logger.info(
            "Orchestrator V2 started — %d skills, AUTO-SCAN ON every %ds",
            len(skill_registry.list_skills()), SCAN_INTERVAL,
        )
    else:
        logger.info(
            "Orchestrator V2 started — %d skills, AUTO-SCAN OFF (use /scan endpoint)",
            len(skill_registry.list_skills()),
        )
    yield
    if _scan_task:
        _scan_task.cancel()
    logger.info("Orchestrator agent shutting down")


app = FastAPI(title="OmniSales Orchestrator Agent V2", lifespan=lifespan)


# ── Request/Response Models ──


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    context_loaded: dict
    timestamp: str


# ── Endpoints ──


@app.post("/scan")
async def manual_scan():
    """Manually trigger a full scan cycle. Report is saved to DB."""
    global _last_scan_result, _scan_count
    _scan_count += 1

    crm_tools = await _get_crm_tools()
    result = await run_full_scan(crm_tools, _scan_count, triggered_by="manual")
    _last_scan_result = result
    return result


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Stateless chat — manager can ask questions about scans and workflows."""
    result = await handle_chat(req.message)
    return result


@app.get("/history")
async def scan_history(limit: int = 10):
    """Get recent scan reports from the database."""
    reports = await get_scan_history(limit=limit)
    return {"reports": reports, "count": len(reports)}


@app.get("/report/{report_id}")
async def single_report(report_id: str):
    """Get a single scan report with full dispatch details."""
    report = await get_scan_report(report_id)
    if not report:
        return {"error": f"Report {report_id} not found"}
    return report


@app.get("/status")
async def scan_status():
    """Return current orchestrator status and last scan result."""
    return {
        "scan_count": _scan_count,
        "scan_interval_seconds": SCAN_INTERVAL,
        "last_scan": _last_scan_result,
    }


@app.get("/.well-known/agent.json")
async def agent_card():
    """A2A-compatible agent card."""
    return skill_registry.to_agent_card()


@app.get("/skills")
async def list_skills():
    return {
        "agent": skill_registry.agent_name,
        "skills": [s.to_a2a_skill() for s in skill_registry.list_skills()],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "orchestrator",
        "version": "2.0",
        "scan_count": _scan_count,
        "scan_interval": SCAN_INTERVAL,
        "skills_count": len(skill_registry.list_skills()),
        "features": ["async_subagents", "db_reports", "chat"],
    }
