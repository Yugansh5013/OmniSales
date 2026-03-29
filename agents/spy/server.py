"""Spy A2A Server — Agent-to-Agent protocol server for competitive intelligence.

Implements the Google A2A protocol with:
- /.well-known/agent.json — agent card discovery (auto-generated from skill registry)
- /tasks/send — A2A task routing
- /skills — skill listing
- /skills/{name}/execute — direct skill execution
"""

import json
import logging
import os
from datetime import datetime, timezone

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agents.spy.skills import build_spy_skills
from shared.skills import SkillRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Skill Registry ──

skill_registry = SkillRegistry(
    agent_name="spy-agent",
    agent_description="Competitive intelligence agent for OmniSales. Provides battle cards, pricing comparisons, competitor analysis, and win/loss frameworks.",
    agent_url="http://spy-a2a:8080",
)
for skill in build_spy_skills():
    skill_registry.register(skill)

# ── App ──

app = FastAPI(title="OmniSales Spy A2A Server")

_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", ""),
            min_size=1, max_size=3,
            ssl="require",
        )
    return _pool


# ── A2A Agent Card (auto-generated from registry) ──


@app.get("/.well-known/agent.json")
async def agent_card():
    """A2A agent card discovery endpoint — generated from skill registry."""
    return JSONResponse(content=skill_registry.to_agent_card())


# ── A2A Task Handling ──


@app.post("/tasks/send")
async def handle_task(request: Request):
    """A2A task endpoint — routes to the appropriate skill.

    Request format (A2A standard):
    {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": "unique-task-id",
            "message": {
                "role": "user",
                "parts": [{"text": "get_battlecard AcmeCRM"}]
            }
        }
    }
    """
    body = await request.json()
    params = body.get("params", {})
    task_id = params.get("id", "unknown")
    message = params.get("message", {})
    parts = message.get("parts", [])
    text = parts[0].get("text", "") if parts else ""

    logger.info("A2A task received: id=%s, text=%s", task_id, text)

    # Route to skill based on text content
    result = None
    text_lower = text.lower()

    if "battlecard" in text_lower or "battle_card" in text_lower:
        competitor = text.split()[-1] if text.split() else "AcmeCRM"
        result = await skill_registry.execute_skill("get_battlecard", competitor_name=competitor)
    elif "analyze" in text_lower and "competitor" in text_lower:
        competitor = text.split()[-1] if text.split() else "AcmeCRM"
        result = await skill_registry.execute_skill("analyze_competitor", competitor_name=competitor)
    elif "pricing" in text_lower or "compare" in text_lower:
        competitor = text.split()[-1] if text.split() else "AcmeCRM"
        result = await skill_registry.execute_skill("compare_pricing", competitor_name=competitor)
    elif "win_loss" in text_lower or "win/loss" in text_lower:
        competitor = text.split()[-1] if text.split() else "AcmeCRM"
        result = await skill_registry.execute_skill("win_loss_analysis", competitor_name=competitor)
    elif "list" in text_lower:
        result = await skill_registry.execute_skill("list_competitors")
    else:
        result = {"error": f"Unknown skill request: {text}. Available skills: {[s.name for s in skill_registry.list_skills()]}"}

    return JSONResponse(content={
        "jsonrpc": "2.0",
        "result": {
            "id": task_id,
            "status": {"state": "completed"},
            "artifacts": [
                {
                    "parts": [{"text": json.dumps(result, indent=2, default=str)}],
                    "metadata": {
                        "source": "spy-agent",
                        "skill_count": len(skill_registry.list_skills()),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ],
        },
    })


# ── Skill endpoints ──


@app.get("/skills")
async def list_skills():
    """List all registered skills."""
    return {"agent": skill_registry.agent_name, "skills": [s.to_a2a_skill() for s in skill_registry.list_skills()]}


@app.post("/skills/{skill_name}/execute")
async def execute_skill(skill_name: str, params: dict = {}):
    """Execute a specific skill by name."""
    result = await skill_registry.execute_skill(skill_name, **params)
    return {"skill": skill_name, "result": result}


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "spy-a2a", "skills_count": len(skill_registry.list_skills())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
