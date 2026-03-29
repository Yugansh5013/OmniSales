"""Orchestrator Chat — stateless conversational interface for managers.

Each /chat request:
1. Loads context from DB (recent scan reports, active workflows, CRM stats)
2. Sends the user message + context to the LLM
3. Returns the LLM's response (no memory across requests)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from langchain_groq import ChatGroq

from agents.orchestrator.scanner import (
    get_scan_history,
    get_active_workflows,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the OmniSales Orchestrator — an autonomous supervisor agent that manages three AI sales sub-agents:

1. **Closer Agent** — Handles stalled/at-risk deals. Analyzes deal data, classifies risk, drafts follow-up emails, handles objections.
2. **Prospector Agent** — Processes new leads. Researches companies, scores ICP fit (0-1), drafts personalized outreach sequences.
3. **Guardian Agent** — Monitors account health. Calculates churn risk, flags at-risk accounts, creates retention plays.

You continuously scan the CRM database and dispatch work to these agents when trigger rules are met.

## Your Trigger Rules
- **Deals → Closer**: risk_level = 'stalled' or 'at_risk' AND silent for ≥3 days
- **Leads → Prospector**: status = 'new' AND icp_score is NULL (unprocessed)
- **Accounts → Guardian**: churn_risk ≥ 0.5 OR health_score ≤ 0.4

## What You Know
Below is your current operational context. Use it to answer the manager's question.

### Recent Scan Reports
{scan_history}

### Active Agent Workflows
{active_workflows}

## Instructions
- Answer concisely and accurately using the context above.
- If asked about a specific company, entity, or agent, reference the relevant data.
- If asked to trigger a scan, say you'll initiate one and suggest using the /scan endpoint.
- If you don't have enough context, say so honestly.
- Use a professional but conversational tone — you're reporting to a sales manager.
"""


def _get_llm() -> ChatGroq:
    """Get a Groq LLM for chat."""
    # Use key rotation via shared config if available, else fall back to env
    keys = os.environ.get("GROQ_API_KEYS", "")
    key = keys.split(",")[0].strip() if keys else ""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=key,
        temperature=0.3,
        max_tokens=2048,
    )


async def handle_chat(user_message: str) -> dict:
    """Process a user chat message with full DB context. Returns LLM response."""
    # 1. Load context from DB
    scan_history = await get_scan_history(limit=5)
    active_workflows = await get_active_workflows()

    # 2. Format context for the prompt
    scan_ctx = _format_scan_history(scan_history)
    workflow_ctx = _format_workflows(active_workflows)

    # 3. Build the system prompt with context
    system = SYSTEM_PROMPT.format(
        scan_history=scan_ctx,
        active_workflows=workflow_ctx,
    )

    # 4. Call LLM
    llm = _get_llm()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    try:
        response = await llm.ainvoke(messages)
        answer = response.content
    except Exception as e:
        logger.error("Chat LLM call failed: %s", e)
        answer = f"I'm having trouble processing your request right now. Error: {str(e)}"

    return {
        "response": answer,
        "context_loaded": {
            "scan_reports": len(scan_history),
            "active_workflows": len(active_workflows),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _format_scan_history(reports: list[dict]) -> str:
    """Format scan reports for the LLM context window."""
    if not reports:
        return "No scan reports yet."

    lines = []
    for r in reports:
        line = (
            f"- **Scan #{r.get('scan_number', '?')}** ({r.get('triggered_by', '?')}) "
            f"at {r.get('started_at', '?')} — "
            f"Status: {r.get('status', '?')}, "
            f"Dispatched: {r.get('total_dispatched', 0)} "
            f"(deals={r.get('deals_dispatched', 0)}, "
            f"leads={r.get('leads_dispatched', 0)}, "
            f"accounts={r.get('accounts_dispatched', 0)})"
        )
        summary = r.get("summary")
        if summary:
            line += f"\n  Summary: {summary}"
        error = r.get("error")
        if error:
            line += f"\n  Error: {error}"
        lines.append(line)

    return "\n".join(lines)


def _format_workflows(workflows: list[dict]) -> str:
    """Format active agent workflows for the LLM context window."""
    if not workflows:
        return "No active workflows."

    lines = []
    for w in workflows:
        line = (
            f"- **{w.get('agent_name', '?')}** → {w.get('task_type', '?')} "
            f"for {w.get('target_name', '?')} — "
            f"Status: {w.get('status', '?')}, "
            f"Created: {w.get('created_at', '?')}"
        )
        lines.append(line)

    return "\n".join(lines)
