"""Spy Agent — Structured skills for competitive intelligence.

Skills are registered with the A2A protocol agent card.
"""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from shared.skills import Skill, SkillInput

logger = logging.getLogger(__name__)

# ── Prompt templates ──

COMPETITOR_ANALYSIS_PROMPT = """\
You are a competitive intelligence analyst. Analyze the competitor data and produce a strategic assessment.

## Competitor Data
{competitor_data}

## Our Product Strengths
- Autonomous multi-agent AI system (Closer, Prospector, Guardian)
- 16+ MCP tool integrations
- Real-time churn prediction with <5min latency
- A2A protocol for agent collaboration
- Human-in-the-loop approval workflows
- Kafka event-driven architecture

## Instructions
Produce a strategic competitive assessment.

Respond in JSON:
{{
    "competitor": "...",
    "threat_level": "low|medium|high|critical",
    "market_positioning": "...",
    "key_differentiators": ["our advantage 1", "our advantage 2"],
    "vulnerability_windows": ["scenario where they might win"],
    "recommended_counter_strategy": "...",
    "deal_talking_points": ["point 1", "point 2", "point 3"]
}}
"""

PRICING_COMPARISON_PROMPT = """\
You are a pricing strategy analyst. Compare our pricing against a competitor.

## Our Pricing
- Starter: $19/user/mo
- Professional: $49/user/mo
- Enterprise: $99/user/mo

## Competitor Pricing
{competitor_pricing}

## Instructions
Analyze the pricing gap and produce a comparison matrix.

Respond in JSON:
{{
    "competitor": "...",
    "pricing_gap_analysis": "...",
    "value_per_dollar": {{"ours": 0.0-1.0, "theirs": 0.0-1.0}},
    "price_anchoring_strategy": "...",
    "discount_threshold": "Maximum % discount before we lose margin",
    "counter_talk_track": "2-3 sentence script when prospect mentions competitor pricing"
}}
"""

WIN_LOSS_PROMPT = """\
You are a win/loss analysis specialist. Generate a win/loss analysis template for deals involving this competitor.

## Competitor
{competitor_name}

## Competitor Data
{competitor_data}

## Instructions
Generate a structured analysis framework.

Respond in JSON:
{{
    "competitor": "...",
    "common_win_patterns": ["pattern 1", "pattern 2"],
    "common_loss_patterns": ["pattern 1", "pattern 2"],
    "decision_criteria_ranking": ["criteria 1 (we win)", "criteria 2 (they win)"],
    "stakeholder_preferences": {{
        "CTO": "our_advantage | their_advantage",
        "CFO": "our_advantage | their_advantage",
        "VP_Sales": "our_advantage | their_advantage"
    }},
    "competitive_displacement_plays": ["play 1", "play 2"]
}}
"""


# ── Skill execute functions ──


async def _execute_get_battlecard(competitor_name: str) -> dict:
    """Fetch battle card from DB (same as the A2A implementation)."""
    from shared.db import fetch_one
    row = await fetch_one(
        "SELECT name, data FROM competitors WHERE LOWER(name) = LOWER($1)",
        competitor_name,
    )
    if row:
        data = row.get("data", {})
        if isinstance(data, str):
            data = json.loads(data)
        return {"competitor": row["name"], **data.get("battlecard", {})}
    return {"competitor": competitor_name, "note": "No battle card found"}


async def _execute_list_competitors() -> dict:
    """List all tracked competitors."""
    from shared.db import fetch_all
    rows = await fetch_all("SELECT name, website, last_scraped FROM competitors ORDER BY name")
    return {"competitors": [
        {"name": r["name"], "website": r.get("website"), "last_scraped": str(r.get("last_scraped", ""))}
        for r in rows
    ]}


async def _execute_analyze_competitor(competitor_name: str) -> dict:
    """Deep strategic analysis of a competitor."""
    from shared.llm import get_complex_llm
    card = await _execute_get_battlecard(competitor_name)
    if "note" in card:
        return {"error": f"No data found for {competitor_name}"}

    prompt = COMPETITOR_ANALYSIS_PROMPT.format(competitor_data=json.dumps(card, indent=2))
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a competitive intelligence analyst. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"threat_level": "unknown"}


async def _execute_compare_pricing(competitor_name: str) -> dict:
    """Compare pricing against a competitor."""
    from shared.llm import get_fast_llm
    card = await _execute_get_battlecard(competitor_name)
    competitor_pricing = card.get("pricing", {})

    prompt = PRICING_COMPARISON_PROMPT.format(competitor_pricing=json.dumps(competitor_pricing, indent=2))
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a pricing analyst. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"pricing_gap_analysis": "Analysis unavailable"}


async def _execute_win_loss_analysis(competitor_name: str) -> dict:
    """Generate win/loss analysis framework for a competitor."""
    from shared.llm import get_complex_llm
    card = await _execute_get_battlecard(competitor_name)

    prompt = WIN_LOSS_PROMPT.format(
        competitor_name=competitor_name,
        competitor_data=json.dumps(card, indent=2),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a win/loss analysis specialist. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"competitor": competitor_name}


# ── Skill Definitions ──


def build_spy_skills() -> list[Skill]:
    """Build and return all Spy agent skills."""
    return [
        Skill(
            name="get_battlecard",
            description="Retrieve a competitor battle card with pricing, strengths, weaknesses, and our differentiators.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor (e.g., 'AcmeCRM')"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_get_battlecard,
            tags=["battlecard", "competitor", "intelligence"],
        ),
        Skill(
            name="list_competitors",
            description="List all tracked competitors with names, websites, and last scraped timestamps.",
            agent="spy",
            input_schema=SkillInput(properties={}, required=[]),
            execute_fn=_execute_list_competitors,
            tags=["competitor", "list"],
        ),
        Skill(
            name="analyze_competitor",
            description="Deep strategic competitive analysis including threat level, vulnerability windows, counter-strategies, and deal talking points.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_analyze_competitor,
            tags=["analysis", "strategy", "competitive"],
        ),
        Skill(
            name="compare_pricing",
            description="Compare our pricing tiers against a competitor's. Returns pricing gap analysis, value-per-dollar, and counter talk tracks.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_compare_pricing,
            tags=["pricing", "comparison", "competitive"],
        ),
        Skill(
            name="win_loss_analysis",
            description="Generate a win/loss analysis framework for deals involving a specific competitor, including stakeholder preferences and displacement plays.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_win_loss_analysis,
            tags=["win-loss", "analysis", "displacement"],
        ),
    ]
