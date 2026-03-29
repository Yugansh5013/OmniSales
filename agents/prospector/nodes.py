"""Prospector Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def _unwrap_mcp(result: Any) -> dict:
    """Unwrap MCP tool responses into a plain dict.

    langchain-mcp-adapters 0.1.0+ may return:
      - a list of content blocks  [{"type":"text","text":"..."}]
      - a JSON string
      - a list of dicts (query results)
      - a plain dict
    """
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and "text" in block:
                try:
                    return json.loads(block["text"])
                except (json.JSONDecodeError, TypeError):
                    return block
            if hasattr(block, "text"):
                try:
                    return json.loads(block.text)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": block.text}
        if result and isinstance(result[0], dict):
            return result[0]
        return {"raw": str(result)}
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            if isinstance(parsed, list) and parsed:
                return parsed[0] if isinstance(parsed[0], dict) else {"raw": str(parsed)}
            return parsed if isinstance(parsed, dict) else {"raw": str(parsed)}
        except json.JSONDecodeError:
            return {"raw": result}
    if isinstance(result, dict):
        return result
    if hasattr(result, "text"):
        try:
            return json.loads(result.text)
        except (json.JSONDecodeError, TypeError):
            return {"raw": str(result.text)}
    return {"raw": str(result)}


async def research_company(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 1: Load lead data from CRM MCP."""
    lead_id = state["lead_id"]
    reasoning = list(state.get("reasoning", []))

    crm_tools = {t.name: t for t in tools}
    raw_lead = await crm_tools["get_lead"].ainvoke({"lead_id": lead_id})
    lead_data = _unwrap_mcp(raw_lead)

    if "error" in lead_data:
        reasoning.append(f"research_company: ERROR — {lead_data['error']}")
        return {**state, "reasoning": reasoning, "action": "deprioritize"}

    enrichment = lead_data.get("enrichment", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)

    reasoning.append(
        f"research_company: Loaded lead '{lead_data.get('company')}' — "
        f"{enrichment.get('employees', '?')} employees, {enrichment.get('funding', 'N/A')}"
    )

    return {
        **state,
        "reasoning": reasoning,
        "metadata": {**state.get("metadata", {}), "lead": lead_data, "enrichment": enrichment},
    }


async def enrich_lead(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 2: Process enrichment data (simulated Apollo.io)."""
    enrichment = state["metadata"]["enrichment"]
    reasoning = list(state.get("reasoning", []))

    reasoning.append(
        f"enrich_lead: Processed enrichment — industry={enrichment.get('industry', 'N/A')}, "
        f"signals={enrichment.get('signals', [])}, tech_stack={enrichment.get('tech_stack', [])}"
    )

    return {**state, "reasoning": reasoning}


async def score_icp(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3: Score lead against ICP using FAST LLM."""
    from agents.prospector.skills import ICP_SCORING_PROMPT
    from shared.llm import get_fast_llm

    enrichment = state["metadata"]["enrichment"]
    reasoning = list(state.get("reasoning", []))

    prompt = ICP_SCORING_PROMPT.format(
        company=state["metadata"]["lead"].get("company", "Unknown"),
        industry=enrichment.get("industry", "Unknown"),
        employees=enrichment.get("employees", "Unknown"),
        funding=enrichment.get("funding", "Unknown"),
        revenue_est=enrichment.get("revenue_est", "Unknown"),
        tech_stack=enrichment.get("tech_stack", []),
        signals=enrichment.get("signals", []),
    )

    llm = get_fast_llm()
    response = await llm.ainvoke([
        SystemMessage(content="You are an ICP scoring engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        result = json.loads(content[start:end]) if start >= 0 else {"icp_score": 0.5, "tier": "C"}

    try:
        icp_score = float(result.get("icp_score", 0.5))
    except (TypeError, ValueError):
        icp_score = 0.5
    tier = result.get("tier", "C")

    # Update lead in CRM
    crm_tools = {t.name: t for t in tools}
    if "update_lead" in crm_tools:
        await crm_tools["update_lead"].ainvoke({
            "lead_id": state["lead_id"],
            "icp_score": icp_score,
            "tier": tier,
        })

    reasoning.append(f"score_icp: ICP={icp_score:.2f}, Tier={tier}, Signals={result.get('match_signals', [])}")

    return {
        **state,
        "action": "deprioritize" if icp_score < 0.5 else "draft_outreach",
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "icp_result": result},
    }


async def identify_contacts(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 4: Extract decision-makers from enrichment data."""
    enrichment = state["metadata"]["enrichment"]
    reasoning = list(state.get("reasoning", []))

    contacts = enrichment.get("contacts", [])
    reasoning.append(f"identify_contacts: Found {len(contacts)} decision-makers: "
                     f"{', '.join(c.get('name', '') + ' (' + c.get('title', '') + ')' for c in contacts)}")

    return {
        **state,
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "contacts": contacts},
    }


async def draft_sequences(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 5: Draft personalized 3-email sequences per contact."""
    from agents.prospector.skills import OUTREACH_SEQUENCE_PROMPT
    from shared.llm import get_complex_llm

    contacts = state["metadata"]["contacts"]
    enrichment = state["metadata"]["enrichment"]
    icp_result = state["metadata"]["icp_result"]
    lead = state["metadata"]["lead"]
    reasoning = list(state.get("reasoning", []))

    all_sequences = []
    llm = get_complex_llm()

    for contact in contacts[:2]:  # Max 2 contacts per lead
        prompt = OUTREACH_SEQUENCE_PROMPT.format(
            contact_name=contact.get("name", "Decision Maker"),
            contact_title=contact.get("title", "Executive"),
            company=lead.get("company", "Unknown"),
            industry=enrichment.get("industry", "Unknown"),
            icp_score=icp_result.get("icp_score", 0.5),
            tier=icp_result.get("tier", "C"),
            signals=enrichment.get("signals", []),
            funding=enrichment.get("funding", "N/A"),
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        all_sequences.append({
            "contact": contact,
            "sequences": response.content,
        })

    draft = "\n\n---\n\n".join(
        f"## Sequences for {s['contact'].get('name')} ({s['contact'].get('title')})\n\n{s['sequences']}"
        for s in all_sequences
    )

    reasoning.append(f"draft_sequences: Drafted {len(all_sequences)} × 3-email sequences")

    return {**state, "draft": draft, "reasoning": reasoning}


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 6: Queue sequences for human approval."""
    reasoning = list(state.get("reasoning", []))
    lead = state["metadata"]["lead"]

    approval_tools = {t.name: t for t in tools}
    if "queue_for_approval" in approval_tools:
        try:
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": str(lead.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                "agent_name": "prospector",
                "task_type": "outreach_sequence",
                "target_id": str(lead.get("id", "")),
                "target_name": lead.get("company", "Unknown"),
                "draft": state.get("draft", ""),
                "reasoning": "\n".join(reasoning),
                "thread_id": state.get("lead_id", ""),
            })
            reasoning.append(f"await_approval: Queued for review (task_id={result.get('task_id', 'N/A')})")
        except Exception as e:
            reasoning.append(f"await_approval: Failed — {e}")

    return {**state, "approval": "pending", "reasoning": reasoning}


async def queue_send(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 7: Log approved sequences and update lead status."""
    reasoning = list(state.get("reasoning", []))
    lead = state["metadata"]["lead"]

    crm_tools = {t.name: t for t in tools}
    if "update_lead" in crm_tools:
        await crm_tools["update_lead"].ainvoke({
            "lead_id": state["lead_id"],
            "status": "contacted",
        })

    reasoning.append(f"queue_send: Sequences approved and queued for {lead.get('company')}")
    return {**state, "approval": "approved", "reasoning": reasoning}


async def deprioritize(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Dead-end node: Lead doesn't meet ICP threshold."""
    reasoning = list(state.get("reasoning", []))
    reasoning.append("deprioritize: ICP score below 0.5 — lead deprioritized")
    return {**state, "reasoning": reasoning, "action": "deprioritize"}
