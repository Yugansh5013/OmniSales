"""Guardian Agent — FastAPI service."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel

from agents.guardian.graph import build_guardian_graph
from agents.guardian.skills import build_guardian_skills
from shared.errors import setup_error_handlers
from shared.llm import synthesize_natural_reasoning
from shared.mcp_utils import unwrap_mcp
from shared.skills import SkillRegistry
from shared.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Skill Registry ──

skill_registry = SkillRegistry(
    agent_name="guardian-agent",
    agent_description="Account health monitoring agent. Scores churn risk, generates retention plays, analyzes usage patterns, and detects upsell opportunities.",
    agent_url="http://guardian-agent:8006",
)
for skill in build_guardian_skills():
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
    logger.info("Guardian agent started — %d skills registered", len(skill_registry.list_skills()))
    yield


app = FastAPI(title="OmniSales Guardian Agent", lifespan=lifespan)
setup_error_handlers(app, service_name="guardian-agent")


async def _get_tools():
    mcp_config = {
        "crm": {"url": os.environ.get("MCP_CRM_URL", "http://mcp-crm:8001/mcp"), "transport": "http"},
        "approvals": {"url": os.environ.get("MCP_APPROVALS_URL", "http://mcp-approvals:8004/mcp"), "transport": "http"},
    }
    client = MultiServerMCPClient(mcp_config)
    return await client.get_tools()


# ── Graph endpoints ──


@app.post("/analyze")
async def trigger_guardian():
    """Run Guardian portfolio-wide health scan across all CRM accounts.
    
    Architecture Note:
    Unlike Closer and Prospector which operate on single entities (/trigger/{id}),
    Guardian performs portfolio batch analysis (/analyze). It returns aggregate batch
    metrics (accounts_analyzed, flagged_count, combined retention draft, task_id)
    along with individually enriched account objects in `flagged` for consistent UI/API consumption.
    """
    tools = await _get_tools()

    # Fresh checkpointer per-request to avoid stale Neon connections
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_guardian_graph(tools, checkpointer)
        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [], "lead_id": None, "deal_id": None, "account_id": None,
            "action": "", "draft": None, "approval": None, "reasoning": [], "metadata": {},
        }

        result = await graph.ainvoke(initial_state, config)
    flagged = result.get("metadata", {}).get("flagged_accounts", [])

    # Publish Kafka events for flagged high churn-risk accounts
    try:
        from shared.kafka import publish
        for a in flagged:
            score = a.get("llm_score", {})
            await publish("guardian.churn_risk", {
                "org_id": "a0000000-0000-0000-0000-000000000001",
                "account_id": str(a.get("id", "")),
                "company": a.get("company", "Unknown"),
                "churn_risk": float(score.get("churn_risk", 0.7)),
                "reason": f"Flagged by Guardian: {score.get('risk_tier', 'high')} risk",
                "top_signals": score.get("top_signals", []),
            })
    except Exception as e:
        logger.warning("Kafka event publish skipped/failed: %s", e)

    # The graph interrupts BEFORE the "human" node, so queue_for_approval
    # in await_human_approval never runs. Queue the task here instead.
    task_id = None
    if result.get("draft"):
        llm_usage = result.get("metadata", {}).get("llm_usage", {})
        approval_tools = {t.name: t for t in tools}
        if "queue_for_approval" in approval_tools:
            try:
                target_title = f"Top {len(flagged)} Churn Risk Accounts"
                raw_trace = result.get("reasoning", [])
                natural_reasoning = await synthesize_natural_reasoning(
                    agent_name="guardian",
                    task_type="retention_play",
                    target_name=target_title,
                    raw_trace=raw_trace,
                    context={"flagged_count": len(flagged)},
                )
                qr = await approval_tools["queue_for_approval"].ainvoke({
                    "org_id": "a0000000-0000-0000-0000-000000000001",
                    "agent_name": "guardian",
                    "task_type": "retention_play",
                    "target_id": "a0000000-0000-0000-0000-000000000001",
                    "target_name": target_title,
                    "draft": result.get("draft", ""),
                    "reasoning": natural_reasoning,
                    "thread_id": thread_id,
                    "model_used": "openai/gpt-oss-120b",
                    "tokens_used": llm_usage.get("tokens_used", 0),
                    "cost": llm_usage.get("cost", 0.0),
                })
                task_data = unwrap_mcp(qr)
                task_id = task_data.get("task_id")
                logger.info("✅ Queued guardian approval: %s for %d accounts", task_id, len(flagged))
            except Exception as e:
                logger.exception("Failed to queue guardian approval: %s", e)

    # Structured, enriched per-account list matching single-entity schema
    enriched_flagged = [
        {
            "account_id": str(a.get("id", "")),
            "company": a.get("company", "Unknown"),
            "arr": float(a.get("arr", 0.0)) if a.get("arr") is not None else None,
            "plan": a.get("plan"),
            "churn_risk": a.get("llm_score", {}).get("churn_risk"),
            "risk_tier": a.get("llm_score", {}).get("risk_tier"),
            "action": "retention_play" if a.get("llm_score", {}).get("risk_tier") in ("critical", "high") else "monitor",
            "top_signals": a.get("llm_score", {}).get("top_signals", []),
        }
        for a in flagged
    ]

    return {
        "thread_id": thread_id,
        "accounts_analyzed": len(result.get("metadata", {}).get("accounts", [])),
        "flagged_count": len(flagged),
        "flagged": enriched_flagged,
        "draft": result.get("draft"),
        "reasoning": result.get("reasoning", []),
        "status": "awaiting_approval" if result.get("draft") else "no_action",
        "task_id": task_id,
    }


class RegenerateRequest(BaseModel):
    feedback: str
    previous_draft: str = ""


@app.post("/regenerate")
async def regenerate_guardian(body: RegenerateRequest):
    """Re-draft the retention batch after a human rejection, folding their feedback
    into the prompt. Guardian has no single-entity id — it re-scans the current
    top-risk accounts fresh (same as /analyze always does) and regenerates plays
    for them with the feedback attached."""
    from agents.guardian.nodes import analyze_accounts, score_churn, rank_and_flag, generate_retention

    tools = await _get_tools()
    state: AgentState = {
        "messages": [], "lead_id": None, "deal_id": None, "account_id": None,
        "action": "", "draft": None, "approval": None, "reasoning": [],
        "metadata": {"revision_feedback": body.feedback, "previous_draft": body.previous_draft},
    }
    state = await analyze_accounts(state, tools)
    state = await score_churn(state, tools)
    state = await rank_and_flag(state, tools)
    if state.get("action") == "no_action":
        return {"status": "no_action", "draft": None, "task_id": None}
    state = await generate_retention(state, tools)

    flagged = state["metadata"].get("flagged_accounts", [])
    llm_usage = state["metadata"].get("llm_usage", {})
    approval_tools = {t.name: t for t in tools}
    task_id = None
    if "queue_for_approval" in approval_tools:
        try:
            target_title = f"Top {len(flagged)} Churn Risk Accounts"
            raw_trace = state.get("reasoning", []) + [f"Human feedback addressed: {body.feedback}"]
            natural_reasoning = await synthesize_natural_reasoning(
                agent_name="guardian",
                task_type="retention_play",
                target_name=target_title,
                raw_trace=raw_trace,
                context={"feedback": body.feedback},
            )
            qr = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": "a0000000-0000-0000-0000-000000000001",
                "agent_name": "guardian",
                "task_type": "retention_play",
                "target_id": "a0000000-0000-0000-0000-000000000001",
                "target_name": target_title,
                "draft": state.get("draft", ""),
                "reasoning": natural_reasoning,
                "thread_id": str(uuid4()),
                "model_used": "openai/gpt-oss-120b",
                "tokens_used": llm_usage.get("tokens_used", 0),
                "cost": llm_usage.get("cost", 0.0),
            })
            task_data = unwrap_mcp(qr)
            task_id = task_data.get("task_id")
            logger.info("✅ Regenerated guardian retention plays per feedback → task %s", task_id)
        except Exception as e:
            logger.exception("Failed to queue regenerated guardian retention plays: %s", e)

    return {"task_id": task_id, "draft": state.get("draft"), "status": "awaiting_approval" if task_id else "error"}


@app.post("/resume/{thread_id}")
async def resume_guardian(thread_id: str, approved: bool = True):
    tools = await _get_tools()
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_guardian_graph(tools, checkpointer)
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
    return {"status": "healthy", "agent": "guardian", "skills_count": len(skill_registry.list_skills())}
