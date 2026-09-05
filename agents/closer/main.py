"""Closer Agent — FastAPI service for triggering and resuming the graph."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel

from agents.closer.graph import build_closer_graph
from agents.closer.skills import build_closer_skills
from shared.errors import setup_error_handlers
from shared.llm import synthesize_natural_reasoning
from shared.mcp_utils import unwrap_mcp
from shared.skills import SkillRegistry
from shared.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Skill Registry ──

skill_registry = SkillRegistry(
    agent_name="closer-agent",
    agent_description="Deal risk management agent. Classifies deal risk, drafts follow-ups, handles objections, and forecasts win probability.",
    agent_url="http://closer-agent:8002",
)
for skill in build_closer_skills():
    skill_registry.register(skill)

# ── Lifespan ──

DB_URL = os.environ.get("DATABASE_URL", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Just ensure the checkpoint table exists once at startup
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as cp:
        try:
            await cp.setup()
        except Exception as e:
            logger.info("Checkpointer setup skipped (likely already exists): %s", e)
    logger.info("Closer agent started — %d skills registered", len(skill_registry.list_skills()))
    yield
    logger.info("Closer agent shutting down")


app = FastAPI(title="OmniSales Closer Agent", lifespan=lifespan)
setup_error_handlers(app, service_name="closer-agent")


async def _get_tools():
    """Connect to MCP servers and get tools."""
    mcp_config = {
        "crm": {"url": os.environ.get("MCP_CRM_URL", "http://mcp-crm:8001/mcp"), "transport": "http"},
        "knowledge": {"url": os.environ.get("MCP_KNOWLEDGE_URL", "http://mcp-knowledge:8003/mcp"), "transport": "http"},
        "approvals": {"url": os.environ.get("MCP_APPROVALS_URL", "http://mcp-approvals:8004/mcp"), "transport": "http"},
    }
    client = MultiServerMCPClient(mcp_config)
    return await client.get_tools()


# ── Graph endpoints ──


@app.post("/trigger/{deal_id}")
async def trigger_closer(deal_id: str):
    """Trigger the Closer agent on a specific deal.
    The graph runs: analyze → classify → draft/objection → pause at human node.
    """
    tools = await _get_tools()

    # Fresh checkpointer per-request to avoid stale Neon connections
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_closer_graph(tools, checkpointer)

        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [], "lead_id": None, "deal_id": deal_id, "account_id": None,
            "action": "", "draft": None, "approval": None, "reasoning": [], "metadata": {},
        }

        result = await graph.ainvoke(initial_state, config)

    # The graph interrupts BEFORE the "human" node, so queue_for_approval
    # in await_human_approval never runs. Queue the task here instead.
    task_id = None
    if result.get("draft"):
        deal = result.get("metadata", {}).get("deal", {})
        llm_usage = result.get("metadata", {}).get("llm_usage", {})
        approval_tools = {t.name: t for t in tools}
        if "queue_for_approval" in approval_tools:
            try:
                action_val = result.get("action", "")
                if action_val == "objection":
                    task_type = "objection_response"
                elif action_val in ("schedule_meeting", "meeting"):
                    task_type = "meeting_confirmation"
                elif action_val in ("send_payment_link", "payment_link", "contract_and_payment"):
                    task_type = "send_contract_and_payment"
                else:
                    task_type = "email_draft"
                raw_trace = result.get("reasoning", [])
                natural_reasoning = await synthesize_natural_reasoning(
                    agent_name="closer",
                    task_type=task_type,
                    target_name=deal.get("company", "Unknown"),
                    raw_trace=raw_trace,
                    context={"arr": deal.get("arr"), "stage": deal.get("stage"), "risk": deal.get("risk_level")},
                )
                qr = await approval_tools["queue_for_approval"].ainvoke({
                    "org_id": str(deal.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                    "agent_name": "closer",
                    "task_type": task_type,
                    "target_id": str(deal.get("id", "a0000000-0000-0000-0000-000000000001")),
                    "target_name": deal.get("company", "Unknown"),
                    "draft": result.get("draft", ""),
                    "reasoning": natural_reasoning,
                    "thread_id": thread_id,
                    "model_used": llm_usage.get("model_used", "openai/gpt-oss-120b"),
                    "tokens_used": llm_usage.get("tokens_used", 0),
                    "cost": llm_usage.get("cost", 0.0),
                })
                task_data = unwrap_mcp(qr)
                task_id = task_data.get("task_id")
                logger.info("✅ Queued closer approval: %s for %s", task_id, deal.get("company"))
            except Exception as e:
                logger.exception("Failed to queue closer approval: %s", e)

    return {
        "thread_id": thread_id, "deal_id": deal_id,
        "action": result.get("action"), "draft": result.get("draft"),
        "approval": result.get("approval"), "reasoning": result.get("reasoning", []),
        "status": "awaiting_approval" if result.get("draft") else "no_action",
        "task_id": task_id,
    }


class RegenerateRequest(BaseModel):
    feedback: str
    previous_draft: str = ""


@app.post("/regenerate/{deal_id}")
async def regenerate_closer(deal_id: str, body: RegenerateRequest):
    """Re-draft after a human rejection, folding their feedback into the prompt.
    Bypasses the graph/checkpointer (the /trigger flow already does — the graph
    interrupts before human review and never actually resumes) and re-runs the
    node functions directly so the feedback reaches the LLM this time."""
    from agents.closer.nodes import analyze_deal, classify_risk, draft_followup, handle_objection

    tools = await _get_tools()
    state: AgentState = {
        "messages": [], "lead_id": None, "deal_id": deal_id, "account_id": None,
        "action": "", "draft": None, "approval": None, "reasoning": [],
        "metadata": {"revision_feedback": body.feedback, "previous_draft": body.previous_draft},
    }
    state = await analyze_deal(state, tools)
    state = await classify_risk(state, tools)
    if state["action"] == "objection":
        state = await handle_objection(state, tools)
    elif state["action"] == "follow_up":
        state = await draft_followup(state, tools)
    else:
        return {"status": "no_action", "draft": None, "task_id": None}

    deal = state["metadata"]["deal"]
    llm_usage = state["metadata"].get("llm_usage", {})
    approval_tools = {t.name: t for t in tools}
    task_id = None
    if "queue_for_approval" in approval_tools:
        try:
            task_type = "objection_response" if state.get("action") == "objection" else "email_draft"
            raw_trace = state.get("reasoning", []) + [f"Human feedback addressed: {body.feedback}"]
            natural_reasoning = await synthesize_natural_reasoning(
                agent_name="closer",
                task_type=task_type,
                target_name=deal.get("company", "Unknown"),
                raw_trace=raw_trace,
                context={"feedback": body.feedback, "arr": deal.get("arr"), "stage": deal.get("stage")},
            )
            qr = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": str(deal.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                "agent_name": "closer",
                "task_type": task_type,
                "target_id": str(deal.get("id", deal_id)),
                "target_name": deal.get("company", "Unknown"),
                "draft": state.get("draft", ""),
                "reasoning": natural_reasoning,
                "thread_id": str(uuid4()),
                "model_used": llm_usage.get("model_used", "openai/gpt-oss-120b"),
                "tokens_used": llm_usage.get("tokens_used", 0),
                "cost": llm_usage.get("cost", 0.0),
            })
            task_data = unwrap_mcp(qr)
            task_id = task_data.get("task_id")
            logger.info("✅ Regenerated closer draft for %s per feedback → task %s", deal.get("company"), task_id)
        except Exception as e:
            logger.exception("Failed to queue regenerated closer draft: %s", e)

    return {"task_id": task_id, "draft": state.get("draft"), "status": "awaiting_approval" if task_id else "error"}


@app.post("/resume/{thread_id}")
async def resume_closer(thread_id: str, approved: bool = True, feedback: str = ""):
    """Resume the Closer graph after human approval/rejection."""
    tools = await _get_tools()
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_closer_graph(tools, checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        result = await graph.ainvoke({"approval": "approved" if approved else "rejected"}, config)
    return {
        "thread_id": thread_id, "approval": result.get("approval"),
        "reasoning": result.get("reasoning", []),
        "status": "sent" if approved else "rejected",
    }


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
    return {"status": "healthy", "agent": "closer", "skills_count": len(skill_registry.list_skills())}
