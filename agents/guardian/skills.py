"""Guardian Agent — Structured skills for churn prediction and retention.

Each skill is an executable unit with A2A-compatible schema.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from shared.skills import Skill, SkillInput

logger = logging.getLogger(__name__)

# ── Prompt templates ──

CHURN_SCORING_PROMPT = """\
You are an expert customer health analyst. Analyze this account and score churn risk.

## Account Data
- Company: {company}
- ARR: ${arr:,.0f}
- Plan: {plan}
- Current Health Score: {health_score}
- Usage %: {usage_pct}
- Support Tickets: {support_tickets}
- Last Login: {last_login}
- Usage Trend (last 6 periods): {usage_trend}
- Known Signals: {signals}
- NPS Score: {nps_score}
- Contract End: {contract_end}

## Instructions
Assess churn risk on a 0-1 scale. Consider:
- Declining usage trends (strongest signal)
- Support ticket volume and severity
- Login frequency drops
- Contract approaching renewal with poor health
- NPS score degradation

Respond in JSON:
{{
    "churn_risk": 0.0-1.0,
    "health_score": 0.0-1.0,
    "risk_tier": "critical" | "high" | "medium" | "low",
    "top_signals": ["signal 1", "signal 2", "signal 3"],
    "reasoning": "Brief explanation"
}}
"""

RETENTION_PLAY_PROMPT = """\
You are a world-class customer success strategist. Generate a TAILORED retention play for this at-risk account.

## Account Data
- Company: {company}
- ARR: ${arr:,.0f}
- Plan: {plan}
- Churn Risk: {churn_risk}
- Health Score: {health_score}
- Top Risk Signals: {top_signals}
- Usage Trend: {usage_trend}
- Support Tickets: {support_tickets}
- Contract End: {contract_end}

## Instructions
Create a specific, actionable retention play that:
1. Directly addresses the TOP risk signals (not generic advice)
2. Proposes a concrete intervention (executive sponsor call, custom training, feature unlock, credit, etc.)
3. Includes a 30-day action plan with 3 milestones
4. Estimates the retention probability if executed

This must be TAILORED to this specific account. Do NOT use generic templates.

Format:
## Retention Play: {company}
**Intervention Type:** ...
**Urgency:** ...
**Strategy:** ... (2-3 sentences)
**30-Day Plan:**
1. Week 1: ...
2. Week 2: ...
3. Week 3-4: ...
**Retention Probability:** ...%
"""

USAGE_ANALYSIS_PROMPT = """\
You are a product analytics expert. Analyze this account's usage pattern and identify the root cause of any decline.

## Account Data
- Company: {company}
- Plan: {plan}
- Usage Trend (last 6 periods): {usage_trend}
- Current Usage: {usage_pct}%
- Support Tickets: {support_tickets}
- Last Login: {last_login}
- Feature Adoption: {feature_adoption}

## Instructions
Analyze the usage curve and determine:

Respond in JSON:
{{
    "usage_trajectory": "growing|stable|declining|cratering",
    "decline_rate": 0.0-1.0,
    "root_cause_hypothesis": ["cause 1", "cause 2"],
    "at_risk_features": ["feature1"],
    "engagement_score": 0.0-1.0,
    "recommended_interventions": ["intervention 1", "intervention 2"],
    "time_to_churn_estimate": "X weeks/months"
}}
"""

UPSELL_DETECTION_PROMPT = """\
You are a revenue expansion analyst. Identify upsell and cross-sell opportunities for this account.

## Account Data
- Company: {company}
- ARR: ${arr:,.0f}
- Current Plan: {plan}
- Usage %: {usage_pct}
- Health Score: {health_score}
- Feature Adoption: {feature_adoption}
- Team Size: {team_size}
- Contract End: {contract_end}

## Available Plans
- Starter: $19/user/mo (basic features)
- Professional: $49/user/mo (advanced analytics, 3 agents)
- Enterprise: $99/user/mo (unlimited agents, custom MCP, SLA)

## Instructions
Analyze and identify expansion opportunities.

Respond in JSON:
{{
    "upsell_opportunity": true|false,
    "recommended_plan": "professional|enterprise",
    "expansion_revenue": 0,
    "confidence": 0.0-1.0,
    "triggers": ["trigger 1"],
    "pitch_angle": "2 sentence pitch for the upgrade",
    "timing": "immediate|next_qbr|at_renewal",
    "blockers": ["potential blocker"]
}}
"""

HEALTH_REPORT_PROMPT = """\
You are a customer success reporting engine. Generate a comprehensive health report for this account.

## Account Data
- Company: {company}
- ARR: ${arr:,.0f}
- Plan: {plan}
- Health Score: {health_score}
- Churn Risk: {churn_risk}
- Usage %: {usage_pct}
- Support Tickets: {support_tickets}
- NPS Score: {nps_score}
- Last Login: {last_login}
- Usage Trend: {usage_trend}
- Contract End: {contract_end}

## Instructions
Generate a structured health report suitable for a Customer Success Manager.

Respond in JSON:
{{
    "overall_health": "excellent|good|fair|poor|critical",
    "health_grade": "A|B|C|D|F",
    "key_metrics": {{
        "usage": {{"value": 0.0, "trend": "up|stable|down", "benchmark": "above|at|below"}},
        "engagement": {{"value": 0.0, "trend": "up|stable|down"}},
        "support": {{"tickets": 0, "resolution_trend": "improving|stable|worsening"}}
    }},
    "risk_factors": ["risk 1"],
    "bright_spots": ["positive 1"],
    "recommended_actions": [
        {{"action": "...", "priority": "high|medium|low", "owner": "CSM|Support|Product"}}
    ],
    "executive_summary": "2-3 sentence summary for quarterly business review"
}}
"""


# ── Skill execute functions ──


async def _execute_score_churn(account_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_fast_llm
    account = {"company": "Demo", "arr": 50000, "plan": "professional", "health_score": 0.5, "usage_pct": 0.5, "support_tickets": 3, "last_login": "2026-03-20", "churn_risk": 0.5, "metadata": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_account" in crm:
            account = await crm["get_account"].ainvoke({"account_id": account_id})
            if isinstance(account, str):
                account = json.loads(account)
    metadata = account.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    prompt = CHURN_SCORING_PROMPT.format(
        company=account.get("company", "Unknown"), arr=float(account.get("arr", 0)),
        plan=account.get("plan", "unknown"), health_score=account.get("health_score", 0.5),
        usage_pct=account.get("usage_pct", 0.5), support_tickets=account.get("support_tickets", 0),
        last_login=account.get("last_login", "unknown"), usage_trend=metadata.get("usage_trend", []),
        signals=metadata.get("signals", []), nps_score=metadata.get("nps_score", "N/A"),
        contract_end=metadata.get("contract_end", "N/A"),
    )
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a churn scoring engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"churn_risk": 0.5, "risk_tier": "medium"}


async def _execute_retention_play(account_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_complex_llm
    account = {"company": "Demo", "arr": 50000, "plan": "professional", "health_score": 0.4, "churn_risk": 0.7, "support_tickets": 5, "metadata": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_account" in crm:
            account = await crm["get_account"].ainvoke({"account_id": account_id})
            if isinstance(account, str):
                account = json.loads(account)
    metadata = account.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    prompt = RETENTION_PLAY_PROMPT.format(
        company=account.get("company", "Unknown"), arr=float(account.get("arr", 0)),
        plan=account.get("plan", "unknown"), churn_risk=account.get("churn_risk", 0.5),
        health_score=account.get("health_score", 0.5), top_signals=metadata.get("signals", []),
        usage_trend=metadata.get("usage_trend", []), support_tickets=account.get("support_tickets", 0),
        contract_end=metadata.get("contract_end", "N/A"),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"retention_play": resp.content, "account_id": account_id}


async def _execute_analyze_usage(account_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_fast_llm
    account = {"company": "Demo", "plan": "professional", "usage_pct": 0.5, "support_tickets": 3, "last_login": "2026-03-20", "metadata": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_account" in crm:
            account = await crm["get_account"].ainvoke({"account_id": account_id})
            if isinstance(account, str):
                account = json.loads(account)
    metadata = account.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    prompt = USAGE_ANALYSIS_PROMPT.format(
        company=account.get("company", "Unknown"), plan=account.get("plan", "unknown"),
        usage_trend=metadata.get("usage_trend", []),
        usage_pct=round(float(account.get("usage_pct", 0.5)) * 100),
        support_tickets=account.get("support_tickets", 0),
        last_login=str(account.get("last_login", "unknown")),
        feature_adoption=metadata.get("feature_adoption", "N/A"),
    )
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a product analytics expert. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"usage_trajectory": "unknown"}


async def _execute_detect_upsell(account_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_fast_llm
    account = {"company": "Demo", "arr": 50000, "plan": "professional", "usage_pct": 0.8, "health_score": 0.85, "metadata": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_account" in crm:
            account = await crm["get_account"].ainvoke({"account_id": account_id})
            if isinstance(account, str):
                account = json.loads(account)
    metadata = account.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    prompt = UPSELL_DETECTION_PROMPT.format(
        company=account.get("company", "Unknown"), arr=float(account.get("arr", 0)),
        plan=account.get("plan", "unknown"), usage_pct=round(float(account.get("usage_pct", 0.5)) * 100),
        health_score=account.get("health_score", 0.5),
        feature_adoption=metadata.get("feature_adoption", "N/A"),
        team_size=metadata.get("team_size", "Unknown"),
        contract_end=metadata.get("contract_end", "N/A"),
    )
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a revenue expansion analyst. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"upsell_opportunity": False}


async def _execute_health_report(account_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_complex_llm
    account = {"company": "Demo", "arr": 50000, "plan": "professional", "health_score": 0.5, "churn_risk": 0.3, "usage_pct": 0.6, "support_tickets": 2, "last_login": "2026-03-20", "metadata": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_account" in crm:
            account = await crm["get_account"].ainvoke({"account_id": account_id})
            if isinstance(account, str):
                account = json.loads(account)
    metadata = account.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    prompt = HEALTH_REPORT_PROMPT.format(
        company=account.get("company", "Unknown"), arr=float(account.get("arr", 0)),
        plan=account.get("plan", "unknown"), health_score=account.get("health_score", 0.5),
        churn_risk=account.get("churn_risk", 0.3), usage_pct=round(float(account.get("usage_pct", 0.5)) * 100),
        support_tickets=account.get("support_tickets", 0),
        nps_score=metadata.get("nps_score", "N/A"),
        last_login=str(account.get("last_login", "unknown")),
        usage_trend=metadata.get("usage_trend", []),
        contract_end=metadata.get("contract_end", "N/A"),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a CS reporting engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"overall_health": "unknown"}


# ── Skill Definitions ──


def build_guardian_skills() -> list[Skill]:
    """Build and return all Guardian agent skills."""
    return [
        Skill(
            name="score_churn_risk",
            description="Score an account's churn risk (0-1) using usage trends, support tickets, NPS, login frequency, and contract timeline. Returns risk tier and top signals.",
            agent="guardian",
            input_schema=SkillInput(
                properties={"account_id": {"type": "string", "description": "UUID of the account"}},
                required=["account_id"],
            ),
            execute_fn=_execute_score_churn,
            tags=["churn", "scoring", "risk"],
        ),
        Skill(
            name="generate_retention_play",
            description="Generate a tailored retention strategy for an at-risk account with a 30-day action plan, specific interventions, and estimated retention probability.",
            agent="guardian",
            input_schema=SkillInput(
                properties={"account_id": {"type": "string", "description": "UUID of the account"}},
                required=["account_id"],
            ),
            execute_fn=_execute_retention_play,
            tags=["retention", "strategy", "churn"],
        ),
        Skill(
            name="analyze_usage_pattern",
            description="Analyze an account's usage trajectory, identify root causes of decline, estimate time-to-churn, and recommend interventions.",
            agent="guardian",
            input_schema=SkillInput(
                properties={"account_id": {"type": "string", "description": "UUID of the account"}},
                required=["account_id"],
            ),
            execute_fn=_execute_analyze_usage,
            tags=["usage", "analytics", "pattern"],
        ),
        Skill(
            name="detect_upsell_opportunity",
            description="Identify upsell/cross-sell opportunities based on usage patterns, plan limits, and account health. Returns recommended plan and expansion revenue estimate.",
            agent="guardian",
            input_schema=SkillInput(
                properties={"account_id": {"type": "string", "description": "UUID of the account"}},
                required=["account_id"],
            ),
            execute_fn=_execute_detect_upsell,
            tags=["upsell", "expansion", "revenue"],
        ),
        Skill(
            name="generate_health_report",
            description="Generate a comprehensive account health report for CSM review, including health grade, key metrics, risk factors, bright spots, and executive summary.",
            agent="guardian",
            input_schema=SkillInput(
                properties={"account_id": {"type": "string", "description": "UUID of the account"}},
                required=["account_id"],
            ),
            execute_fn=_execute_health_report,
            tags=["health", "report", "csm"],
        ),
    ]
