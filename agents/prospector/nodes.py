"""Prospector Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from shared.llm import synthesize_natural_reasoning

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

    result = None
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(content[start:end])
            except Exception:
                pass
        if result is None:
            logger.warning("[llm_fallback] JSON parsing failed in prospector score_icp: %s", content[:200])
            result = {
                "icp_score": 0.5,
                "tier": "C",
                "match_signals": ["JSON decode fallback triggered"],
                "llm_fallback": True,
                "raw_snippet": content[:200],
                "reason": "json_parse_error",
            }

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

    if result.get("llm_fallback"):
        reasoning.append(f"score_icp: [llm_fallback] ICP={icp_score:.2f}, Tier={tier} (fallback triggered: {result.get('reason')})")
    else:
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
    lead = state["metadata"].get("lead", {})
    reasoning = list(state.get("reasoning", []))

    contacts = enrichment.get("contacts", [])
    if not contacts:
        contact_name = lead.get("contact_name") or "Sarah Chen"
        title = lead.get("title") or "VP of Growth"
        email = lead.get("email") or "sarah.chen@novatech.io"
        contacts = [{"name": contact_name, "title": title, "email": email}]

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
    from shared.llm import usage_from_response, build_feedback_block
    total_tokens, total_cost = 0, 0.0
    feedback_block = build_feedback_block(state["metadata"])

    for contact in contacts[:2]:  # Max 2 contacts per lead
        contact_name = contact.get("name") or lead.get("contact_name") or "Decision Maker"
        contact_first_name = contact_name.split()[0].title() if contact_name else "there"
        rep_name = lead.get("owner") or "Sarah Jenkins"
        rep_title = "Account Executive, OmniSales"

        prompt = OUTREACH_SEQUENCE_PROMPT.format(
            contact_name=contact_name,
            contact_first_name=contact_first_name,
            contact_title=contact.get("title") or lead.get("title") or "Executive",
            company=lead.get("company", "Unknown"),
            rep_name=rep_name,
            rep_title=rep_title,
            industry=enrichment.get("industry", "Unknown"),
            icp_score=icp_result.get("icp_score", 0.5),
            tier=icp_result.get("tier", "C"),
            signals=enrichment.get("signals", []),
            funding=enrichment.get("funding", "N/A"),
            feedback_block=feedback_block,
            n="{n}",
            day="{day}",
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        usage = usage_from_response(response)
        total_tokens += usage["tokens_used"]
        total_cost += usage["cost"]
        all_sequences.append({
            "contact": contact,
            "sequences": response.content,
        })

    draft = "\n\n---\n\n".join(
        f"Sequences for {s['contact'].get('name')} ({s['contact'].get('title')})\n\n{s['sequences']}"
        for s in all_sequences
    )

    reasoning.append(f"draft_sequences: Drafted {len(all_sequences)} × 3-email sequences")

    # Log to contact's timeline in HubSpot
    crm_tools = {t.name: t for t in tools}
    if "log_lead_action" in crm_tools:
        try:
            await crm_tools["log_lead_action"].ainvoke({
                "lead_id": str(lead.get("id", "")),
                "agent_name": "prospector",
                "action": "drafted_outreach_sequence",
                "reasoning": f"Outreach sequence drafted for {lead.get('company')} (ICP: {icp_result.get('icp_score')})",
            })
        except Exception as e:
            logger.warning("Failed to log lead action to HubSpot: %s", e)

    return {
        **state,
        "draft": draft,
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "llm_usage": {"tokens_used": total_tokens, "cost": round(total_cost, 6)}},
    }


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 6: Queue sequences for human approval."""
    reasoning = list(state.get("reasoning", []))
    lead = state["metadata"]["lead"]

    approval_tools = {t.name: t for t in tools}
    llm_usage = state["metadata"].get("llm_usage", {})
    if "queue_for_approval" in approval_tools:
        try:
            natural_reasoning = await synthesize_natural_reasoning(
                agent_name="prospector",
                task_type="outreach_sequence",
                target_name=lead.get("company", "Unknown"),
                raw_trace=reasoning,
            )
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": str(lead.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                "agent_name": "prospector",
                "task_type": "outreach_sequence",
                "target_id": str(lead.get("id", "")),
                "target_name": lead.get("company", "Unknown"),
                "draft": state.get("draft", ""),
                "reasoning": natural_reasoning,
                "thread_id": state.get("lead_id", ""),
                "tokens_used": llm_usage.get("tokens_used", 0),
                "cost": llm_usage.get("cost", 0.0),
            })
            task_data = _unwrap_mcp(result)
            task_id = task_data.get("task_id", "N/A")
            reasoning.append(f"await_approval: Queued for review (task_id={task_id})")
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
