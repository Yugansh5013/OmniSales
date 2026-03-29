"""Prospector Agent — Structured skills for lead qualification and outreach.

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

ICP_SCORING_PROMPT = """\
You are an ICP (Ideal Customer Profile) scoring engine. Analyze the company data and score how well they match our ideal customer.

## Company Data
- Company: {company}
- Industry: {industry}
- Employees: {employees}
- Funding: {funding}
- Estimated Revenue: {revenue_est}
- Tech Stack: {tech_stack}
- Buying Signals: {signals}

## Our ICP Criteria
- SaaS company with 50-500 employees (sweet spot: 100-300)
- Series A to Series C stage
- $5M-$50M ARR
- Already using a CRM (Salesforce, HubSpot, Pipedrive)
- Actively hiring sales roles (AEs, SDRs, RevOps)
- Recent leadership change in sales/revenue org

Score from 0.0 to 1.0 and assign a tier. Respond in JSON:
{{
    "icp_score": 0.0-1.0,
    "tier": "A" | "B" | "C" | "D",
    "match_signals": ["signal 1", "signal 2"],
    "gap_signals": ["gap 1"],
    "reasoning": "Brief explanation"
}}
"""

OUTREACH_SEQUENCE_PROMPT = """\
You are an expert cold outreach copywriter. Draft a 3-email sequence for a decision-maker.

## Target Contact
- Name: {contact_name}
- Title: {contact_title}
- Company: {company}

## Company Context
- Industry: {industry}
- ICP Score: {icp_score} (Tier {tier})
- Key Signals: {signals}
- Funding: {funding}

## Instructions
Write 3 emails in a sequence:
1. **Email 1 (Day 1 — Pattern Interrupt):** Open with a specific insight about THEIR company, not about us. Reference a signal. Under 80 words.
2. **Email 2 (Day 3 — Value Drop):** Share a relevant case study or data point. Under 100 words.
3. **Email 3 (Day 7 — Direct Ask):** Direct ask for a 15-minute call. Reference the previous emails. Under 60 words.

Each email must be hyper-personalized to the contact's role and company. No generic templates.

Format each as:
### Email {{n}} (Day {{day}})
Subject: ...
Body: ...
"""

COMPANY_RESEARCH_PROMPT = """\
You are a lead research analyst. Analyze the available data about this company and identify key insights for sales outreach.

## Available Data
- Company: {company}
- Contact: {contact_name} ({contact_title})
- Industry: {industry}
- Employees: {employees}
- Funding: {funding}
- Tech Stack: {tech_stack}
- Signals: {signals}

## Instructions
Produce a structured research brief that a sales rep can use for personalized outreach:

Respond in JSON:
{{
    "company_summary": "2-3 sentence overview",
    "pain_points": ["likely pain 1", "likely pain 2", "likely pain 3"],
    "personalization_hooks": ["hook for contact's role", "hook based on company signal"],
    "competitor_risk": "low|medium|high",
    "timing_score": 0.0-1.0,
    "recommended_approach": "consultative|challenger|solution|value",
    "ice_breakers": ["opening line 1", "opening line 2"]
}}
"""

LEAD_PRIORITIZATION_PROMPT = """\
You are a lead prioritization engine. Rank these leads by outreach priority.

## Leads
{leads_json}

## Scoring Criteria (weighted)
- ICP Fit (35%): How well does the company match our ICP?
- Timing Signals (25%): Are there active buying signals?
- Deal Size Potential (20%): Estimated ARR opportunity
- Accessibility (10%): Do we have direct contact info for a decision-maker?
- Competition (10%): Are there competitor mentions?

Respond in JSON:
{{
    "ranked_leads": [
        {{
            "lead_id": "...",
            "company": "...",
            "priority_score": 0.0-1.0,
            "rationale": "Brief explanation"
        }}
    ],
    "recommended_batch_size": 3-5,
    "reasoning": "Overall strategy note"
}}
"""

LINKEDIN_MESSAGE_PROMPT = """\
You are a LinkedIn outreach specialist. Draft a personalized LinkedIn connection request + follow-up message.

## Target
- Name: {contact_name}
- Title: {contact_title}
- Company: {company}
- Industry: {industry}
- Mutual Signals: {signals}

## Instructions
1. **Connection Request** (under 300 chars): Reference something specific about THEM, not us. No selling.
2. **Follow-Up Message** (after acceptance, under 150 words): Provide value first, then soft CTA.

Format:
### Connection Request
...

### Follow-Up Message
...
"""


# ── Skill execute functions ──


async def _execute_score_icp(lead_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_fast_llm
    lead = {"company": "Demo", "enrichment": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_lead" in crm:
            lead = await crm["get_lead"].ainvoke({"lead_id": lead_id})
            if isinstance(lead, str):
                lead = json.loads(lead)
    enrichment = lead.get("enrichment", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)

    prompt = ICP_SCORING_PROMPT.format(
        company=lead.get("company", "Unknown"), industry=enrichment.get("industry", "Unknown"),
        employees=enrichment.get("employees", "Unknown"), funding=enrichment.get("funding", "Unknown"),
        revenue_est=enrichment.get("revenue_est", "Unknown"), tech_stack=enrichment.get("tech_stack", []),
        signals=enrichment.get("signals", []),
    )
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are an ICP scoring engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"icp_score": 0.5, "tier": "C"}


async def _execute_draft_outreach(lead_id: str, contact_index: int = 0, tools: list | None = None) -> dict:
    from shared.llm import get_complex_llm
    lead = {"company": "Demo", "enrichment": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_lead" in crm:
            lead = await crm["get_lead"].ainvoke({"lead_id": lead_id})
            if isinstance(lead, str):
                lead = json.loads(lead)
    enrichment = lead.get("enrichment", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)
    contacts = enrichment.get("contacts", [])
    contact = contacts[contact_index] if contact_index < len(contacts) else {"name": "Decision Maker", "title": "Executive"}

    prompt = OUTREACH_SEQUENCE_PROMPT.format(
        contact_name=contact.get("name", "Decision Maker"), contact_title=contact.get("title", "Executive"),
        company=lead.get("company", "Unknown"), industry=enrichment.get("industry", "Unknown"),
        icp_score=lead.get("icp_score", 0.5), tier=lead.get("tier", "C"),
        signals=enrichment.get("signals", []), funding=enrichment.get("funding", "N/A"),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"sequences": resp.content, "contact": contact, "lead_id": lead_id}


async def _execute_research_company(lead_id: str, tools: list | None = None) -> dict:
    from shared.llm import get_complex_llm
    lead = {"company": "Demo", "contact_name": "Demo", "title": "VP", "enrichment": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_lead" in crm:
            lead = await crm["get_lead"].ainvoke({"lead_id": lead_id})
            if isinstance(lead, str):
                lead = json.loads(lead)
    enrichment = lead.get("enrichment", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)

    prompt = COMPANY_RESEARCH_PROMPT.format(
        company=lead.get("company", "Unknown"), contact_name=lead.get("contact_name", "Unknown"),
        contact_title=lead.get("title", "Unknown"), industry=enrichment.get("industry", "Unknown"),
        employees=enrichment.get("employees", "Unknown"), funding=enrichment.get("funding", "Unknown"),
        tech_stack=enrichment.get("tech_stack", []), signals=enrichment.get("signals", []),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a lead research analyst. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"company_summary": "Research unavailable"}


async def _execute_prioritize_leads(tools: list | None = None) -> dict:
    from shared.llm import get_fast_llm
    leads = []
    if tools:
        crm = {t.name: t for t in tools}
        if "list_leads" in crm:
            leads = await crm["list_leads"].ainvoke({"status": "new"})
            if isinstance(leads, str):
                leads = json.loads(leads)

    if not leads:
        return {"ranked_leads": [], "reasoning": "No leads to prioritize"}

    prompt = LEAD_PRIORITIZATION_PROMPT.format(leads_json=json.dumps(leads[:10], indent=2, default=str))
    llm = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content="You are a lead prioritization engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])
    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        s, e = resp.content.find("{"), resp.content.rfind("}") + 1
        return json.loads(resp.content[s:e]) if s >= 0 else {"ranked_leads": []}


async def _execute_draft_linkedin(lead_id: str, contact_index: int = 0, tools: list | None = None) -> dict:
    from shared.llm import get_complex_llm
    lead = {"company": "Demo", "contact_name": "Demo", "title": "VP", "enrichment": {}}
    if tools:
        crm = {t.name: t for t in tools}
        if "get_lead" in crm:
            lead = await crm["get_lead"].ainvoke({"lead_id": lead_id})
            if isinstance(lead, str):
                lead = json.loads(lead)
    enrichment = lead.get("enrichment", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)
    contacts = enrichment.get("contacts", [])
    contact = contacts[contact_index] if contact_index < len(contacts) else {"name": lead.get("contact_name", ""), "title": lead.get("title", "")}

    prompt = LINKEDIN_MESSAGE_PROMPT.format(
        contact_name=contact.get("name", "Unknown"), contact_title=contact.get("title", "Unknown"),
        company=lead.get("company", "Unknown"), industry=enrichment.get("industry", "Unknown"),
        signals=enrichment.get("signals", []),
    )
    llm = get_complex_llm()
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"linkedin_messages": resp.content, "contact": contact, "lead_id": lead_id}


# ── Skill Definitions ──


def build_prospector_skills() -> list[Skill]:
    """Build and return all Prospector agent skills."""
    return [
        Skill(
            name="score_lead_icp",
            description="Score a lead against the Ideal Customer Profile based on company size, funding, tech stack, and buying signals. Returns 0-1 score with tier (A/B/C/D).",
            agent="prospector",
            input_schema=SkillInput(
                properties={"lead_id": {"type": "string", "description": "UUID of the lead to score"}},
                required=["lead_id"],
            ),
            execute_fn=_execute_score_icp,
            tags=["icp", "scoring", "qualification"],
        ),
        Skill(
            name="draft_outreach_sequence",
            description="Draft a hyper-personalized 3-email cold outreach sequence (Day 1 pattern interrupt, Day 3 value drop, Day 7 direct ask) for a specific contact at the lead company.",
            agent="prospector",
            input_schema=SkillInput(
                properties={
                    "lead_id": {"type": "string", "description": "UUID of the lead"},
                    "contact_index": {"type": "integer", "description": "Index of contact in enrichment data (default 0)", "default": 0},
                },
                required=["lead_id"],
            ),
            execute_fn=_execute_draft_outreach,
            tags=["outreach", "email", "personalization"],
        ),
        Skill(
            name="research_company",
            description="Produce a structured research brief for a lead including pain points, personalization hooks, timing score, and recommended sales approach.",
            agent="prospector",
            input_schema=SkillInput(
                properties={"lead_id": {"type": "string", "description": "UUID of the lead"}},
                required=["lead_id"],
            ),
            execute_fn=_execute_research_company,
            tags=["research", "company", "analysis"],
        ),
        Skill(
            name="prioritize_leads",
            description="Rank all new leads by outreach priority using weighted scoring (ICP fit, timing signals, deal size, accessibility, competition).",
            agent="prospector",
            input_schema=SkillInput(properties={}, required=[]),
            execute_fn=_execute_prioritize_leads,
            tags=["prioritization", "ranking", "batch"],
        ),
        Skill(
            name="draft_linkedin_message",
            description="Draft a personalized LinkedIn connection request (<300 chars) and follow-up message for a contact. Value-first, no selling in the request.",
            agent="prospector",
            input_schema=SkillInput(
                properties={
                    "lead_id": {"type": "string", "description": "UUID of the lead"},
                    "contact_index": {"type": "integer", "description": "Index of contact (default 0)", "default": 0},
                },
                required=["lead_id"],
            ),
            execute_fn=_execute_draft_linkedin,
            tags=["linkedin", "social", "outreach"],
        ),
    ]
