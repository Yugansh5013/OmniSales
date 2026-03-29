"""Prospector Agent — FastAPI service."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agents.prospector.graph import build_prospector_graph
from agents.prospector.skills import build_prospector_skills
from shared.skills import SkillRegistry
from shared.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Skill Registry ──

skill_registry = SkillRegistry(
    agent_name="prospector-agent",
    agent_description="Lead qualification and outreach agent. Scores ICP fit, researches companies, drafts personalized email sequences and LinkedIn messages.",
    agent_url="http://prospector-agent:8005",
)
for skill in build_prospector_skills():
    skill_registry.register(skill)

# ── Lifespan ──

DB_URL = os.environ.get("DATABASE_URL", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure checkpoint table exists once at startup
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as cp:
        try:
            await cp.setup()
        except Exception as e:
            logger.info("Checkpointer setup skipped (likely already exists): %s", e)
    logger.info("Prospector agent started — %d skills registered", len(skill_registry.list_skills()))
    yield


app = FastAPI(title="OmniSales Prospector Agent", lifespan=lifespan)


async def _get_tools():
    mcp_config = {
        "crm": {"url": os.environ.get("MCP_CRM_URL", "http://mcp-crm:8001/mcp"), "transport": "http"},
        "knowledge": {"url": os.environ.get("MCP_KNOWLEDGE_URL", "http://mcp-knowledge:8003/mcp"), "transport": "http"},
        "approvals": {"url": os.environ.get("MCP_APPROVALS_URL", "http://mcp-approvals:8004/mcp"), "transport": "http"},
    }
    client = MultiServerMCPClient(mcp_config)
    return await client.get_tools()


# ── Graph endpoints ──


@app.post("/trigger/{lead_id}")
async def trigger_prospector(lead_id: str):
    tools = await _get_tools()

    # Fresh checkpointer per-request to avoid stale Neon connections
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_prospector_graph(tools, checkpointer)
        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [], "lead_id": lead_id, "deal_id": None, "account_id": None,
            "action": "", "draft": None, "approval": None, "reasoning": [], "metadata": {},
        }

        result = await graph.ainvoke(initial_state, config)

    # The graph interrupts BEFORE the "human" node, so queue_for_approval
    # in await_human_approval never runs. Queue the task here instead.
    task_id = None
    if result.get("draft"):
        lead = result.get("metadata", {}).get("lead", {})
        approval_tools = {t.name: t for t in tools}
        if "queue_for_approval" in approval_tools:
            try:
                qr = await approval_tools["queue_for_approval"].ainvoke({
                    "org_id": str(lead.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                    "agent_name": "prospector",
                    "task_type": "outreach_sequence",
                    "target_id": str(lead.get("id", "a0000000-0000-0000-0000-000000000001")),
                    "target_name": lead.get("company", "Unknown"),
                    "draft": result.get("draft", ""),
                    "reasoning": "\n".join(result.get("reasoning", [])),
                    "thread_id": thread_id,
                    "model_used": "llama-3.3-70b-versatile",
                    "tokens_used": 0,
                    "cost": 0.0,
                })
                task_id = qr.get("task_id") if isinstance(qr, dict) else None
                logger.info("✅ Queued prospector approval: %s for %s", task_id, lead.get("company"))
            except Exception as e:
                logger.exception("Failed to queue prospector approval: %s", e)

    return {
        "thread_id": thread_id, "lead_id": lead_id,
        "action": result.get("action"), "draft": result.get("draft"),
        "reasoning": result.get("reasoning", []),
        "icp_score": result.get("metadata", {}).get("icp_result", {}).get("icp_score"),
        "status": "awaiting_approval" if result.get("draft") else result.get("action", "no_action"),
        "task_id": task_id,
    }


@app.post("/resume/{thread_id}")
async def resume_prospector(thread_id: str, approved: bool = True):
    tools = await _get_tools()
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_prospector_graph(tools, checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke({"approval": "approved" if approved else "rejected"}, config)
    return {"thread_id": thread_id, "approval": result.get("approval"), "reasoning": result.get("reasoning", [])}


# ── Skill endpoints ──


@app.get("/.well-known/agent.json")
async def agent_card():
    """A2A-compatible agent card with registered skills."""
    return skill_registry.to_agent_card()


@app.get("/skills")
async def list_skills():
    """List all registered skills."""
    return {"agent": skill_registry.agent_name, "skills": [s.to_a2a_skill() for s in skill_registry.list_skills()]}


@app.post("/skills/{skill_name}/execute")
async def execute_skill(skill_name: str, params: dict = {}):
    """Execute a specific skill by name."""
    tools = await _get_tools()
    result = await skill_registry.execute_skill(skill_name, tools=tools, **params)
    return {"skill": skill_name, "result": result}


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "prospector", "skills_count": len(skill_registry.list_skills())}
