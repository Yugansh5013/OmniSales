"""Closer Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
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
        # Content block list from MCP adapters
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
        # Plain list of dicts (e.g. query results) — return first element
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
    # Unknown type — try to extract text attribute
    if hasattr(result, "text"):
        try:
            return json.loads(result.text)
        except (json.JSONDecodeError, TypeError):
            return {"raw": str(result.text)}
    return {"raw": str(result)}


async def analyze_deal(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 1: Load deal data from CRM MCP and calculate silence duration."""
    deal_id = state["deal_id"]
    reasoning = list(state.get("reasoning", []))

    # Call CRM MCP to get deal details
    crm_tools = {t.name: t for t in tools}
    raw_deal = await crm_tools["get_deal"].ainvoke({"deal_id": deal_id})
    deal_data = _unwrap_mcp(raw_deal)

    if "error" in deal_data:
        reasoning.append(f"analyze_deal: ERROR — {deal_data['error']}")
        return {**state, "reasoning": reasoning, "action": "no_action"}

    # Parse closer_thread — asyncpg may return JSON arrays as strings
    closer_thread = deal_data.get("closer_thread", [])
    if isinstance(closer_thread, str):
        try:
            closer_thread = json.loads(closer_thread)
        except (json.JSONDecodeError, TypeError):
            closer_thread = []
    if not isinstance(closer_thread, list):
        closer_thread = []
    deal_data["closer_thread"] = closer_thread

    # Calculate days since last activity
    last_activity = deal_data.get("last_activity")
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    days_silent = (datetime.now(timezone.utc) - last_activity).days if last_activity else 0

    reasoning.append(
        f"analyze_deal: Loaded deal '{deal_data.get('company')}' — "
        f"stage={deal_data.get('stage')}, ARR=${float(deal_data.get('arr', 0)):,.0f}, "
        f"risk={deal_data.get('risk_level')}, {days_silent} days silent"
    )

    return {
        **state,
        "reasoning": reasoning,
        "metadata": {
            **state.get("metadata", {}),
            "deal": deal_data,
            "days_silent": days_silent,
        },
    }


async def classify_risk(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 2: Use LLM to classify deal risk and determine action."""
    from agents.closer.skills import RISK_CLASSIFICATION_PROMPT
    from shared.llm import get_complex_llm

    deal = state["metadata"]["deal"]
    days_silent = state["metadata"]["days_silent"]
    reasoning = list(state.get("reasoning", []))

    # Format email thread for context
    email_thread = deal.get("closer_thread", [])
    if isinstance(email_thread, str):
        try:
            email_thread = json.loads(email_thread)
        except (json.JSONDecodeError, TypeError):
            email_thread = []
    email_thread_str = json.dumps(email_thread, indent=2)

    prompt = RISK_CLASSIFICATION_PROMPT.format(
        company=deal.get("company", "Unknown"),
        stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)),
        days_silent=days_silent,
        risk_level=deal.get("risk_level", "unknown"),
        email_thread=email_thread_str,
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([
        SystemMessage(content="You are a deal risk classification engine. Respond only in valid JSON."),
        HumanMessage(content=prompt),
    ])

    # Parse structured output
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        result = json.loads(content[start:end]) if start >= 0 else {"action": "no_action"}

    action = result.get("action", "no_action")
    reasoning.append(
        f"classify_risk: Action={action}, Risk Score={result.get('risk_score', 'N/A')}, "
        f"Signals={result.get('risk_signals', [])}"
    )

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": f"classified_risk_as_{action}",
                "reasoning": f"Risk classified as {result.get('risk_score', 'N/A')}. Signals: {result.get('risk_signals', [])}",
            })
        except Exception as e:
            logger.warning("Failed to log classify_risk: %s", e)

    return {
        **state,
        "action": action,
        "reasoning": reasoning,
        "metadata": {
            **state["metadata"],
            "risk_classification": result,
        },
    }


async def draft_followup(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3a: Draft a follow-up email using RAG context."""
    from agents.closer.skills import FOLLOWUP_DRAFT_PROMPT
    from shared.llm import get_complex_llm

    deal = state["metadata"]["deal"]
    reasoning = list(state.get("reasoning", []))

    # Search knowledge base for relevant context
    knowledge_context = "No relevant documents found."
    knowledge_tools = {t.name: t for t in tools}
    if "search_documents" in knowledge_tools:
        try:
            results = await knowledge_tools["search_documents"].ainvoke({
                "query": f"follow up email stalled deal {deal.get('company', '')} {deal.get('stage', '')}",
            })
            if isinstance(results, str):
                results = json.loads(results)
            if results:
                knowledge_context = "\n\n".join(
                    f"[{r.get('source', 'Unknown')}]: {r.get('content', '')}" for r in results[:3]
                )
        except Exception as e:
            logger.warning("Knowledge search failed: %s", e)

    email_thread = deal.get("closer_thread", [])
    if isinstance(email_thread, str):
        try:
            email_thread = json.loads(email_thread)
        except (json.JSONDecodeError, TypeError):
            email_thread = []
    if not isinstance(email_thread, list):
        email_thread = []
    email_thread_str = json.dumps(email_thread, indent=2)
    last_email = email_thread[-1] if email_thread and isinstance(email_thread[-1], dict) else {}

    prompt = FOLLOWUP_DRAFT_PROMPT.format(
        company=deal.get("company", "Unknown"),
        contact_email=last_email.get("to", "prospect@company.com"),
        stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)),
        days_silent=state["metadata"]["days_silent"],
        risk_signals=state["metadata"].get("risk_classification", {}).get("risk_signals", []),
        email_thread=email_thread_str,
        knowledge_context=knowledge_context,
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    reasoning.append(f"draft_followup: Drafted email using RAG context ({len(knowledge_context)} chars)")

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": "drafted_followup_email",
                "reasoning": f"Follow-up email drafted for {deal.get('company')} using RAG context",
            })
        except Exception as e:
            logger.warning("Failed to log draft_followup: %s", e)

    return {
        **state,
        "draft": response.content,
        "reasoning": reasoning,
    }


async def handle_objection(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3b: Handle objection using battle cards + RAG."""
    from agents.closer.skills import OBJECTION_HANDLING_PROMPT
    from shared.llm import get_complex_llm

    deal = state["metadata"]["deal"]
    reasoning = list(state.get("reasoning", []))

    # Get battle card from knowledge MCP
    battle_card = "No battle card available."
    knowledge_tools = {t.name: t for t in tools}

    # Try to detect competitor and fetch battle card
    email_thread = deal.get("closer_thread", [])
    if isinstance(email_thread, str):
        try:
            email_thread = json.loads(email_thread)
        except (json.JSONDecodeError, TypeError):
            email_thread = []
    if not isinstance(email_thread, list):
        email_thread = []
    prospect_message = ""
    if email_thread and isinstance(email_thread[-1], dict):
        prospect_message = email_thread[-1].get("body", "")
    elif email_thread and isinstance(email_thread[-1], str):
        prospect_message = email_thread[-1]

    if "get_battle_card" in knowledge_tools:
        try:
            card = await knowledge_tools["get_battle_card"].ainvoke({"competitor_name": "AcmeCRM"})
            if isinstance(card, str):
                card = json.loads(card)
            battle_card = json.dumps(card, indent=2)
        except Exception as e:
            logger.warning("Battle card fetch failed: %s", e)

    # Also search knowledge base
    knowledge_context = ""
    if "search_documents" in knowledge_tools:
        try:
            results = await knowledge_tools["search_documents"].ainvoke({
                "query": f"objection handling pricing competitor {deal.get('company', '')}",
            })
            if isinstance(results, str):
                results = json.loads(results)
            if results:
                knowledge_context = "\n\n".join(
                    f"[{r.get('source', 'Unknown')}]: {r.get('content', '')}" for r in results[:3]
                )
        except Exception as e:
            logger.warning("Knowledge search failed: %s", e)

    prompt = OBJECTION_HANDLING_PROMPT.format(
        company=deal.get("company", "Unknown"),
        stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)),
        objection_type="pricing/competitor",
        prospect_message=prospect_message,
        battle_card=battle_card,
        knowledge_context=knowledge_context,
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    reasoning.append(f"handle_objection: Drafted objection response with battle card + RAG data")

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": "handled_objection",
                "reasoning": f"Objection response drafted for {deal.get('company')} with battle card + RAG",
            })
        except Exception as e:
            logger.warning("Failed to log handle_objection: %s", e)

    return {
        **state,
        "draft": response.content,
        "reasoning": reasoning,
    }


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 4: Queue draft for human approval via Approval MCP."""
    reasoning = list(state.get("reasoning", []))
    deal = state["metadata"]["deal"]

    # Queue for approval via MCP
    approval_tools = {t.name: t for t in tools}
    if "queue_for_approval" in approval_tools:
        try:
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": str(deal.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                "agent_name": "closer",
                "task_type": "email_draft",
                "target_id": str(deal.get("id", "")),
                "target_name": deal.get("company", "Unknown"),
                "draft": state.get("draft", ""),
                "reasoning": "\n".join(reasoning),
                "thread_id": state.get("deal_id", ""),
                "model_used": "llama-3.3-70b-versatile",
            })
            reasoning.append(f"await_approval: Queued for human review (task_id={result.get('task_id', 'N/A')})")
        except Exception as e:
            reasoning.append(f"await_approval: Failed to queue — {e}")
            logger.exception("Failed to queue approval")

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": "queued_for_approval",
                "reasoning": f"Draft for {deal.get('company')} queued for human review",
            })
        except Exception as e:
            logger.warning("Failed to log await_approval: %s", e)

    return {
        **state,
        "approval": "pending",
        "reasoning": reasoning,
    }


async def send_email(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 5: Simulate sending email and log to audit trail."""
    reasoning = list(state.get("reasoning", []))
    deal = state["metadata"]["deal"]

    # Log agent action to CRM
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": f"sent_{state.get('action', 'email')}",
                "reasoning": f"Email approved and sent. Action: {state.get('action')}",
            })
        except Exception as e:
            logger.warning("Failed to log action: %s", e)

    reasoning.append(f"send_email: Email sent (simulated) for {deal.get('company')}")

    return {
        **state,
        "approval": "approved",
        "reasoning": reasoning,
    }
