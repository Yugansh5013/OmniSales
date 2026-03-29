"""Closer Agent — Structured skills for deal risk management.

Each skill is an executable unit with A2A-compatible schema.
Prompt templates are embedded within the skill execute functions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from shared.skills import Skill, SkillInput, SkillRegistry

logger = logging.getLogger(__name__)

# ── Prompt templates (internal to skills) ──

RISK_CLASSIFICATION_PROMPT = """\
You are an expert sales risk analyst. Analyze the following deal data and classify the risk level.

## Deal Context
- Company: {company}
- Stage: {stage}
- ARR: ${arr:,.0f}
- Days since last activity: {days_silent}
- Current risk level: {risk_level}

## Email Thread History
{email_thread}

## Instructions
Based on the deal context and email history, classify this deal into one of three actions:

1. **follow_up** — Deal shows signs of stalling (>5 days silence, unanswered emails, or slow momentum). Draft a re-engagement email.
2. **objection** — Prospect has raised a specific concern (pricing, competitor, timeline, features). Handle the objection with data.
3. **no_action** — Deal is healthy and progressing normally. No intervention needed.

Respond in JSON format:
{{
    "action": "follow_up" | "objection" | "no_action",
    "risk_score": 0.0-1.0,
    "risk_signals": ["signal 1", "signal 2"],
    "reasoning": "One paragraph explaining your assessment"
}}
"""

FOLLOWUP_DRAFT_PROMPT = """\
You are a world-class sales email writer. Draft a follow-up email for a stalled deal.

## Deal Context
- Company: {company}
- Contact: {contact_email}
- Stage: {stage}
- ARR: ${arr:,.0f}
- Days silent: {days_silent}
- Risk signals: {risk_signals}

## Previous Email Thread
{email_thread}

## Relevant Knowledge (RAG)
{knowledge_context}

## Instructions
Write a short, personalized follow-up email that:
1. Acknowledges the silence without being pushy
2. Adds new value (a relevant insight, case study, or resource)
3. Proposes a specific next step (call, demo, or resource share)
4. Is under 150 words
5. Matches the tone of previous emails in the thread

Format as:
Subject: ...
Body: ...
"""

OBJECTION_HANDLING_PROMPT = """\
You are an expert at handling sales objections with data-driven responses.

## Deal Context
- Company: {company}
- Stage: {stage}
- ARR: ${arr:,.0f}
- Objection Type: {objection_type}

## Prospect's Objection
{prospect_message}

## Battle Card Data
{battle_card}

## Relevant Knowledge (RAG)
{knowledge_context}

## Instructions
Draft a response email that:
1. Validates their concern (don't dismiss it)
2. Addresses the specific objection with data from the battle card
3. Pivots to our strengths (reference specific differentiators)
4. Proposes a concrete next step
5. Is under 200 words

Format as:
Subject: ...
Body: ...
"""

SENTIMENT_ANALYSIS_PROMPT = """\
You are a sentiment and intent analysis engine for sales email threads.

## Email Thread
{email_thread}

## Instructions
Analyze the sentiment and buyer intent of this email thread. For each email, determine:
- Sentiment: positive / neutral / negative / mixed
- Buyer signals: interest, urgency, hesitation, objection, ghosting
- Key phrases that indicate intent

Then provide an overall thread assessment.

Respond in JSON:
{{
    "emails": [
        {{
            "from": "...",
            "sentiment": "positive|neutral|negative|mixed",
            "intent_signals": ["signal1"],
            "key_phrases": ["phrase1"]
        }}
    ],
    "overall_sentiment": "positive|neutral|negative|mixed",
    "buyer_readiness": 0.0-1.0,
    "recommended_action": "...",
    "reasoning": "..."
}}
"""

NEXT_STEP_PROMPT = """\
You are a sales strategy advisor. Recommend the optimal next action for this deal.

## Deal Context
- Company: {company}
- Stage: {stage}
- ARR: ${arr:,.0f}
- Risk Level: {risk_level}
- Days Silent: {days_silent}
- Deal Age (days): {deal_age}
- Email Thread Length: {thread_length} emails

## Risk Classification
{risk_classification}

## Email Sentiment
{sentiment}

## Instructions
Recommend the single best next action. Pick from:
1. schedule_call — Book a call with the prospect
2. send_case_study — Share a relevant success story
3. executive_intro — Loop in an executive sponsor
4. discount_offer — Propose a time-limited discount
5. technical_demo — Schedule a technical deep-dive
6. pause — Wait for prospect to respond (no action)
7. escalate — Flag to sales manager for manual intervention

Respond in JSON:
{{
    "recommended_action": "...",
    "confidence": 0.0-1.0,
    "reasoning": "...",
    "talk_track": "2-3 sentence script for the recommended action"
}}
"""

WIN_PROBABILITY_PROMPT = """\
You are a deal forecasting engine. Predict the win probability for this deal.

## Deal Data
- Company: {company}
- Stage: {stage}
- ARR: ${arr:,.0f}
- Risk Level: {risk_level}
- Days in Current Stage: {days_in_stage}
- Thread Length: {thread_length}
- Sentiment: {sentiment}
- Competitor Mentions: {competitor_mentions}

## Historical Benchmarks
- Average deal cycle: 45 days
- Avg close rate by stage: discovery=15%, proposal=35%, negotiation=65%
- Deals mentioning competitors close at 22% lower rate

Respond in JSON:
{{
    "win_probability": 0.0-1.0,
    "confidence_interval": [0.0, 1.0],
    "key_factors": ["factor1", "factor2"],
    "risk_factors": ["risk1"],
    "forecast_reasoning": "..."
}}
"""


# ── Skill execute functions ──


async def _execute_classify_risk(deal_id: str, tools: list | None = None) -> dict:
    """Execute the risk classification skill."""
    from shared.llm import get_complex_llm

    if tools:
        crm = {t.name: t for t in tools}
        deal = await crm.get("get_deal", tools[0]).ainvoke({"deal_id": deal_id})
        if isinstance(deal, str):
            deal = json.loads(deal)
    else:
        deal = {"company": "Demo", "stage": "proposal", "arr": 50000, "risk_level": "at_risk", "closer_thread": [], "last_activity": datetime.now(timezone.utc).isoformat()}

    last_activity = deal.get("last_activity")
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    days_silent = (datetime.now(timezone.utc) - last_activity).days if last_activity else 0

    prompt = RISK_CLASSIFICATION_PROMPT.format(
        company=deal.get("company", "Unknown"), stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)), days_silent=days_silent,
        risk_level=deal.get("risk_level", "unknown"),
        email_thread=json.dumps(deal.get("closer_thread", []), indent=2),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a deal risk classification engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"action": "no_action"}


async def _execute_draft_followup(deal_id: str, tools: list | None = None) -> dict:
    """Execute follow-up email drafting."""
    from shared.llm import get_complex_llm

    deal = {"company": "Demo", "stage": "proposal", "arr": 50000, "closer_thread": [], "last_activity": datetime.now(timezone.utc).isoformat()}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_deal" in crm:
            deal = await crm["get_deal"].ainvoke({"deal_id": deal_id})
            if isinstance(deal, str):
                deal = json.loads(deal)

    last_activity = deal.get("last_activity")
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    days_silent = (datetime.now(timezone.utc) - last_activity).days if last_activity else 0
    thread = deal.get("closer_thread", [])
    last_email = thread[-1] if thread else {}

    prompt = FOLLOWUP_DRAFT_PROMPT.format(
        company=deal.get("company", "Unknown"),
        contact_email=last_email.get("to", "prospect@company.com"),
        stage=deal.get("stage", "unknown"), arr=float(deal.get("arr", 0)),
        days_silent=days_silent, risk_signals=[],
        email_thread=json.dumps(thread, indent=2), knowledge_context="",
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"draft": resp.content, "deal_id": deal_id}


async def _execute_handle_objection(deal_id: str, objection_type: str = "pricing", tools: list | None = None) -> dict:
    """Execute objection handling with battle card data."""
    from shared.llm import get_complex_llm

    deal = {"company": "Demo", "stage": "proposal", "arr": 50000, "closer_thread": []}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_deal" in crm:
            deal = await crm["get_deal"].ainvoke({"deal_id": deal_id})
            if isinstance(deal, str):
                deal = json.loads(deal)

    thread = deal.get("closer_thread", [])
    prospect_msg = thread[-1].get("body", "") if thread else ""

    prompt = OBJECTION_HANDLING_PROMPT.format(
        company=deal.get("company", "Unknown"), stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)), objection_type=objection_type,
        prospect_message=prospect_msg, battle_card="", knowledge_context="",
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"draft": resp.content, "deal_id": deal_id, "objection_type": objection_type}


async def _execute_analyze_sentiment(deal_id: str, tools: list | None = None) -> dict:
    """Analyze email thread sentiment and buyer intent."""
    from shared.llm import get_fast_llm

    deal = {"closer_thread": []}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_deal" in crm:
            deal = await crm["get_deal"].ainvoke({"deal_id": deal_id})
            if isinstance(deal, str):
                deal = json.loads(deal)

    prompt = SENTIMENT_ANALYSIS_PROMPT.format(email_thread=json.dumps(deal.get("closer_thread", []), indent=2))
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a sentiment analysis engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"overall_sentiment": "unknown"}


async def _execute_suggest_next_step(deal_id: str, tools: list | None = None) -> dict:
    """Recommend the optimal next action for a deal."""
    from shared.llm import get_complex_llm

    deal = {"company": "Demo", "stage": "proposal", "arr": 50000, "risk_level": "at_risk", "closer_thread": [], "last_activity": datetime.now(timezone.utc).isoformat(), "created_at": datetime.now(timezone.utc).isoformat()}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_deal" in crm:
            deal = await crm["get_deal"].ainvoke({"deal_id": deal_id})
            if isinstance(deal, str):
                deal = json.loads(deal)

    last_activity = deal.get("last_activity")
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    days_silent = (datetime.now(timezone.utc) - last_activity).days if last_activity else 0

    created = deal.get("created_at")
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    deal_age = (datetime.now(timezone.utc) - created).days if created else 0

    prompt = NEXT_STEP_PROMPT.format(
        company=deal.get("company", "Unknown"), stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)), risk_level=deal.get("risk_level", "unknown"),
        days_silent=days_silent, deal_age=deal_age,
        thread_length=len(deal.get("closer_thread", [])),
        risk_classification="N/A", sentiment="N/A",
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a sales strategy advisor. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"recommended_action": "pause"}


async def _execute_forecast_win(deal_id: str, tools: list | None = None) -> dict:
    """Forecast deal win probability."""
    from shared.llm import get_fast_llm

    deal = {"company": "Demo", "stage": "proposal", "arr": 50000, "risk_level": "healthy", "closer_thread": [], "last_activity": datetime.now(timezone.utc).isoformat()}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_deal" in crm:
            deal = await crm["get_deal"].ainvoke({"deal_id": deal_id})
            if isinstance(deal, str):
                deal = json.loads(deal)

    prompt = WIN_PROBABILITY_PROMPT.format(
        company=deal.get("company", "Unknown"), stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)), risk_level=deal.get("risk_level", "unknown"),
        days_in_stage=5, thread_length=len(deal.get("closer_thread", [])),
        sentiment="neutral", competitor_mentions="none",
    )
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a deal forecasting engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"win_probability": 0.5}


# ── Skill Definitions ──


def build_closer_skills() -> list[Skill]:
    """Build and return all Closer agent skills."""
    return [
        Skill(
            name="classify_deal_risk",
            description="Analyze a deal's email thread, silence duration, and stage to classify risk as follow_up, objection, or no_action. Returns structured risk score and signals.",
            agent="closer",
            input_schema=SkillInput(
                properties={"deal_id": {"type": "string", "description": "UUID of the deal to analyze"}},
                required=["deal_id"],
            ),
            execute_fn=_execute_classify_risk,
            tags=["risk", "classification", "deal"],
        ),
        Skill(
            name="draft_followup_email",
            description="Draft a personalized follow-up email for a stalled deal using RAG context from the knowledge base. Under 150 words, value-first approach.",
            agent="closer",
            input_schema=SkillInput(
                properties={"deal_id": {"type": "string", "description": "UUID of the deal"}},
                required=["deal_id"],
            ),
            execute_fn=_execute_draft_followup,
            tags=["email", "follow-up", "draft"],
        ),
        Skill(
            name="handle_objection",
            description="Handle a prospect's objection (pricing, competitor, timeline) using battle card data and RAG context. Produces a response email draft.",
            agent="closer",
            input_schema=SkillInput(
                properties={
                    "deal_id": {"type": "string", "description": "UUID of the deal"},
                    "objection_type": {"type": "string", "description": "Type: pricing|competitor|timeline|features", "default": "pricing"},
                },
                required=["deal_id"],
            ),
            execute_fn=_execute_handle_objection,
            tags=["objection", "email", "battle-card"],
        ),
        Skill(
            name="analyze_email_sentiment",
            description="Analyze the sentiment and buyer intent signals in a deal's email thread. Returns per-email sentiment, buyer readiness score, and recommended action.",
            agent="closer",
            input_schema=SkillInput(
                properties={"deal_id": {"type": "string", "description": "UUID of the deal"}},
                required=["deal_id"],
            ),
            execute_fn=_execute_analyze_sentiment,
            tags=["sentiment", "analysis", "email"],
        ),
        Skill(
            name="suggest_next_step",
            description="Recommend the optimal next action for a deal (schedule_call, send_case_study, executive_intro, discount_offer, technical_demo, pause, or escalate).",
            agent="closer",
            input_schema=SkillInput(
                properties={"deal_id": {"type": "string", "description": "UUID of the deal"}},
                required=["deal_id"],
            ),
            execute_fn=_execute_suggest_next_step,
            tags=["strategy", "recommendation", "deal"],
        ),
        Skill(
            name="forecast_win_probability",
            description="Predict the win probability for a deal based on stage, risk signals, email sentiment, and historical benchmarks.",
            agent="closer",
            input_schema=SkillInput(
                properties={"deal_id": {"type": "string", "description": "UUID of the deal"}},
                required=["deal_id"],
            ),
            execute_fn=_execute_forecast_win,
            tags=["forecast", "probability", "deal"],
        ),
    ]
