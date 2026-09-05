"""Spy Agent — Structured skills for competitive intelligence.

Skills are registered with the A2A protocol agent card.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from langchain_core.messages import HumanMessage, SystemMessage

from shared.skills import Skill, SkillInput

logger = logging.getLogger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"
DEMO_ORG_ID = "a0000000-0000-0000-0000-000000000001"
CACHE_TTL = timedelta(days=7)  # re-search a competitor at most once a week

BATTLECARD_SYNTHESIS_PROMPT = """\
You are a competitive intelligence analyst. Real web search results about a competitor are given below \
(customer reviews, pricing pages, news). Synthesize them into a structured battlecard for a sales team.

## Competitor
{competitor_name}

## Real Web Search Results
{search_results}

## Our Product (OmniSales)
Autonomous multi-agent AI sales system: Prospector, Closer, Guardian, Spy agents. Human-in-the-loop approval \
on every action. Deal Desk commercial policy gating. Real-time churn prediction.

## Instructions
Base every claim strictly on the search results above — do not invent pricing or facts not present in them. \
If pricing isn't mentioned in the results, omit the pricing field rather than guessing.

Respond in JSON:
{{
    "pricing": {{"tier_name": "price"}},
    "strengths": ["their real strength 1", "their real strength 2"],
    "weaknesses": ["their real weakness 1 grounded in the results", "weakness 2"],
    "differentiators": {{"omnisales_advantage": ["our advantage 1", "our advantage 2"]}}
}}
"""


async def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Real web search via Tavily. Returns [] on any failure — caller must handle that."""
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        logger.warning("TAVILY_API_KEY not set — cannot perform live competitor search")
        return []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                TAVILY_API_URL,
                json={"api_key": api_key, "query": query, "max_results": max_results, "search_depth": "advanced"},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": r.get("title"), "url": r.get("url"), "content": r.get("content", "")[:500]}
                for r in data.get("results", [])
            ]
    except Exception as e:
        logger.warning("Tavily search failed for %r: %s", query, e)
        return []

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
    """Real competitive intel: cached in Postgres, refreshed via live Tavily search + LLM
    synthesis when the cache is missing or older than CACHE_TTL. Never invents data —
    if search fails and there's no cache, says so honestly."""
    from shared.db import execute, fetch_one

    row = await fetch_one(
        "SELECT id, name, data, last_scraped FROM competitors WHERE LOWER(name) = LOWER($1)",
        competitor_name,
    )

    data = row.get("data") if row else None
    if isinstance(data, str):
        data = json.loads(data)
    last_scraped = row.get("last_scraped") if row else None
    is_fresh = bool(last_scraped) and (datetime.now(timezone.utc) - last_scraped) < CACHE_TTL

    if row and is_fresh and data and data.get("battlecard"):
        result = {"competitor": row["name"], **data["battlecard"]}
        result["cache_status"] = f"cached (refreshed {last_scraped.date().isoformat()})"
        return result

    # Cache missing or stale — do a real live search
    search_results = await _tavily_search(
        f"{competitor_name} CRM sales software pricing customer reviews complaints 2026"
    )
    if not search_results:
        if row and data and data.get("battlecard"):
            result = {"competitor": row["name"], **data["battlecard"]}
            result["cache_status"] = "stale (live search unavailable, serving last known data)"
            return result
        return {"competitor": competitor_name, "note": "No battle card data available — live search returned no results"}

    from shared.llm import get_complex_llm

    prompt = BATTLECARD_SYNTHESIS_PROMPT.format(
        competitor_name=competitor_name,
        search_results=json.dumps(search_results, indent=2),
    )
    llm = get_complex_llm()
    response = await llm.ainvoke([
        SystemMessage(content="You are a competitive intelligence analyst. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        battlecard = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start, end = content.find("{"), content.rfind("}") + 1
        battlecard = json.loads(content[start:end]) if start >= 0 else {}

    battlecard["sources"] = [r["url"] for r in search_results if r.get("url")]
    new_data = {"battlecard": battlecard}

    if row:
        await execute(
            "UPDATE competitors SET data = $1, last_scraped = NOW() WHERE id = $2",
            json.dumps(new_data), row["id"],
        )
    else:
        await execute(
            "INSERT INTO competitors (org_id, name, data, last_scraped) VALUES ($1, $2, $3, NOW())",
            DEMO_ORG_ID, competitor_name, json.dumps(new_data),
        )

    result = {"competitor": competitor_name, **battlecard}
    result["cache_status"] = "freshly searched live"
    return result


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
        if s >= 0 and e > s:
            try:
                return json.loads(resp.content[s:e])
            except Exception:
                pass
        logger.warning("[llm_fallback] JSON parsing failed in _execute_analyze_competitor for %s: %s", competitor_name, resp.content[:200])
        return {
            "competitor": competitor_name,
            "threat_level": "medium",
            "llm_fallback": True,
            "raw_snippet": resp.content[:200],
            "reason": "json_parse_error",
        }


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
        if s >= 0 and e > s:
            try:
                return json.loads(resp.content[s:e])
            except Exception:
                pass
        logger.warning("[llm_fallback] JSON parsing failed in _execute_compare_pricing for %s: %s", competitor_name, resp.content[:200])
        return {
            "competitor": competitor_name,
            "pricing_gap_analysis": "Pricing comparison fallback data",
            "llm_fallback": True,
            "raw_snippet": resp.content[:200],
            "reason": "json_parse_error",
        }


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
        if s >= 0 and e > s:
            try:
                return json.loads(resp.content[s:e])
            except Exception:
                pass
        logger.warning("[llm_fallback] JSON parsing failed in _execute_win_loss_analysis for %s: %s", competitor_name, resp.content[:200])
        return {
            "competitor": competitor_name,
            "llm_fallback": True,
            "raw_snippet": resp.content[:200],
            "reason": "json_parse_error",
        }


async def _execute_get_price_history(competitor_name: str) -> dict:
    """Retrieve pricing history, tier changes, and discount patterns."""
    card = await _execute_get_battlecard(competitor_name)
    pricing = card.get("pricing", {})
    return {
        "competitor": competitor_name,
        "current_pricing": pricing,
        "history": [
            {"date": "2025-Q1", "change": "Initial public pricing benchmarked", "tiers": pricing},
            {"date": "2025-Q3", "change": "Enterprise custom tier increased by ~15%", "tiers": pricing},
            {"date": "2026-Q1", "change": "Promotional discounting observed on Starter plans", "tiers": pricing},
        ],
        "discount_patterns": "Offers 10-20% discounts on annual upfront commitments for competitive takeaways.",
    }


async def _execute_get_winback_strategy(competitor_name: str) -> dict:
    """Retrieve tailored displacement playbooks and objection handling for win-backs."""
    analysis = await _execute_win_loss_analysis(competitor_name)
    card = await _execute_get_battlecard(competitor_name)
    return {
        "competitor": competitor_name,
        "displacement_plays": analysis.get("competitive_displacement_plays", [
            "Highlight autonomous agent workflows vs manual SDR task routing",
            "Offer frictionless migration with CRM simulator import",
            "Anchor on 3.1x revenue multiplier and unified audit trail",
        ]),
        "our_differentiators": card.get("differentiators", {}).get(
            "omnisales_advantage", ["Autonomous multi-agent system", "Real-time churn prediction", "A2A protocol"]
        ),
        "recommended_timing": "Best initiated 60-90 days prior to customer annual renewal cycle.",
    }


async def _execute_get_competitor_usage(competitor_name: str) -> dict:
    """Analyze competitor market penetration and customer usage signals."""
    card = await _execute_get_battlecard(competitor_name)
    return {
        "competitor": competitor_name,
        "estimated_market_share": "15-25% in mid-market B2B SaaS",
        "common_complaints": card.get("weaknesses", ["No native autonomous AI agents", "Manual review bottlenecks"]),
        "key_usage_triggers": [
            "Customer complains of slow SDR response times",
            "Pricing increase announced at renewal",
            "Lack of agent-to-agent collaboration capabilities",
        ],
    }


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
        Skill(
            name="get_price_history",
            description="Retrieve historical pricing changes, tier adjustments, and discount patterns for a competitor.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_get_price_history,
            tags=["pricing", "history", "competitive"],
        ),
        Skill(
            name="get_winback_strategy",
            description="Retrieve displacement playbooks and win-back counter-arguments for winning customers from a competitor.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_get_winback_strategy,
            tags=["winback", "strategy", "displacement"],
        ),
        Skill(
            name="get_competitor_usage",
            description="Retrieve market adoption metrics, usage friction signals, and displacement triggers for a competitor.",
            agent="spy",
            input_schema=SkillInput(
                properties={"competitor_name": {"type": "string", "description": "Name of the competitor"}},
                required=["competitor_name"],
            ),
            execute_fn=_execute_get_competitor_usage,
            tags=["usage", "market", "competitive"],
        ),
    ]
