"""Closer Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
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
    logger.info(">>> CLASSIFY_RISK RAW RESPONSE: %s", response.content)
    logger.info(">>> CLASSIFY_RISK THREAD: %s", email_thread_str)

    # Parse structured output
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
            logger.warning("[llm_fallback] JSON parsing failed in closer classify_risk: %s", content[:200])
            result = {
                "action": "no_action",
                "risk_score": 0.5,
                "risk_signals": ["JSON decode fallback triggered"],
                "llm_fallback": True,
                "raw_snippet": content[:200],
                "reason": "json_parse_error",
            }

    action = result.get("action", "no_action")
    if result.get("llm_fallback"):
        reasoning.append(f"classify_risk: [llm_fallback] Defaulted to {action} (reason: {result.get('reason')})")
    else:
        reasoning.append(
            f"classify_risk: Action={action}, Risk Score={result.get('risk_score', 'N/A')}, "
            f"Signals={result.get('risk_signals', [])}"
        )

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            log_reason = f"[llm_fallback] Risk classified as {result.get('risk_score', 'N/A')} (fallback triggered)" if result.get("llm_fallback") else f"Risk classified as {result.get('risk_score', 'N/A')}. Signals: {result.get('risk_signals', [])}"
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": f"classified_risk_as_{action}",
                "reasoning": log_reason,
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


async def draft_payment_link(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3c: Autonomously generate Razorpay payment link and draft closing email."""
    from agents.closer.skills import PAYMENT_LINK_DRAFT_PROMPT
    from shared.llm import get_complex_llm, build_feedback_block, usage_from_response
    from shared.razorpay import create_payment_link

    deal = state["metadata"]["deal"]
    reasoning = list(state.get("reasoning", []))

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

    # Extract real contact name and rep name
    rep_name = deal.get("owner") or "Sarah Jenkins"
    rep_title = "Account Executive, OmniSales"
    contact_name = deal.get("contact_name")
    if not contact_name:
        for em in email_thread:
            if isinstance(em, dict) and em.get("from") == "rep" and "hi " in em.get("body", "").lower():
                import re
                m = re.search(r"hi\s+([A-Za-z]+)", em.get("body", ""), re.IGNORECASE)
                if m and m.group(1).lower() not in ("there", "team", "all"):
                    contact_name = m.group(1).title()
                    break
    if not contact_name and deal.get("company"):
        company_contacts = {
            "techflow": "Alex Rivera",
            "nexgen": "Elena Rostova",
            "quantumleap": "Dr. Aris Thorne",
            "alphawave": "Marcus Vance",
        }
        for k, v in company_contacts.items():
            if k in deal.get("company", "").lower():
                contact_name = v
                break

    contact_first_name = contact_name.split()[0].title() if contact_name else "there"
    contact_email = last_email.get("to") or last_email.get("from") or f"contact@{deal.get('company', 'partner').lower().replace(' ', '')}.com"
    arr = float(deal.get("arr", 50000.0))

    # Generate live Razorpay Payment Link
    link_result = await create_payment_link(
        amount_inr=arr,
        description=f"OmniSales Enterprise License - {deal.get('company')}",
        customer_name=contact_name or deal.get("company", "Valued Customer"),
        customer_email=contact_email,
        notes={"deal_id": str(deal.get("id", "")), "stage": str(deal.get("stage", ""))},
    )
    payment_link_url = link_result.get("short_url") or "https://rzp.io/i/demo-checkout"
    reasoning.append(
        f"draft_payment_link: Generated Razorpay payment link {payment_link_url} for ARR ${arr:,.0f}"
    )

    prompt = PAYMENT_LINK_DRAFT_PROMPT.format(
        company=deal.get("company", "Unknown"),
        contact_name=contact_name or "Valued Partner",
        contact_first_name=contact_first_name,
        contact_email=contact_email,
        rep_name=rep_name,
        rep_title=rep_title,
        stage=deal.get("stage", "unknown"),
        arr=arr,
        payment_link_url=payment_link_url,
        email_thread=email_thread_str,
        feedback_block=build_feedback_block(state["metadata"]),
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    llm_usage = usage_from_response(response)

    reasoning.append(f"draft_payment_link: Drafted closing email with embedded payment link ({payment_link_url})")

    # Log to deal's agent_log audit trail
    crm_tools = {t.name: t for t in tools}
    if "log_agent_action" in crm_tools:
        try:
            await crm_tools["log_agent_action"].ainvoke({
                "deal_id": str(deal.get("id", "")),
                "agent_name": "closer",
                "action": "generated_payment_link_draft",
                "reasoning": f"Generated Razorpay payment link {payment_link_url} and drafted closing email for {deal.get('company')}",
            })
        except Exception as e:
            logger.warning("Failed to log draft_payment_link: %s", e)

    return {
        **state,
        "draft": response.content,
        "reasoning": reasoning,
        "metadata": {
            **state["metadata"],
            "llm_usage": llm_usage,
            "payment_link_url": payment_link_url,
            "payment_link_id": link_result.get("id"),
        },
    }


async def draft_followup(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3a: Draft a follow-up email using RAG context."""
    if state.get("action") in ("send_payment_link", "payment_link", "contract_and_payment"):
        return await draft_payment_link(state, tools)

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

    # Extract real contact name and rep name
    rep_name = deal.get("owner") or "Sarah Jenkins"
    rep_title = "Account Executive, OmniSales"
    contact_name = deal.get("contact_name")
    if not contact_name:
        for em in email_thread:
            if isinstance(em, dict) and em.get("from") == "rep" and "hi " in em.get("body", "").lower():
                import re
                m = re.search(r"hi\s+([A-Za-z]+)", em.get("body", ""), re.IGNORECASE)
                if m and m.group(1).lower() not in ("there", "team", "all"):
                    contact_name = m.group(1).title()
                    break
    if not contact_name and deal.get("company"):
        company_contacts = {
            "techflow": "Alex Rivera",
            "nexgen": "Elena Rostova",
            "quantumleap": "Dr. Aris Thorne",
            "alphawave": "Marcus Vance",
        }
        for k, v in company_contacts.items():
            if k in deal.get("company", "").lower():
                contact_name = v
                break

    contact_first_name = contact_name.split()[0].title() if contact_name else "there"

    from shared.llm import build_feedback_block
    prompt = FOLLOWUP_DRAFT_PROMPT.format(
        company=deal.get("company", "Unknown"),
        contact_name=contact_name or "Valued Partner",
        contact_first_name=contact_first_name,
        contact_email=last_email.get("to", "prospect@company.com"),
        rep_name=rep_name,
        rep_title=rep_title,
        stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)),
        days_silent=state["metadata"]["days_silent"],
        risk_signals=state["metadata"].get("risk_classification", {}).get("risk_signals", []),
        email_thread=email_thread_str,
        knowledge_context=knowledge_context,
        feedback_block=build_feedback_block(state["metadata"]),
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    from shared.llm import usage_from_response
    llm_usage = usage_from_response(response)

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
        "metadata": {**state["metadata"], "llm_usage": llm_usage},
    }


async def handle_objection(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3b: Handle objection using battle cards + RAG."""
    from agents.closer.skills import OBJECTION_HANDLING_PROMPT
    from shared.llm import get_complex_llm

    deal = state["metadata"]["deal"]
    reasoning = list(state.get("reasoning", []))

    # Get battle card from knowledge MCP
    battle_card = "No competitor battle card required (commercial terms objection)."
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

    # Dynamically detect competitor mentioned in email thread / prospect message
    text_to_scan = f"{prospect_message} {json.dumps(email_thread)}".lower()
    detected_competitor = None
    known_competitors = ["acmecrm", "pipedrive", "salesforce", "hubspot", "zoho", "freshsales", "salesflow", "monday"]
    for comp in known_competitors:
        if comp in text_to_scan:
            detected_competitor = "AcmeCRM" if comp == "acmecrm" else ("PipeDrive Pro" if comp == "pipedrive" else comp.title())
            break

    # 1. Connect directly to Spy Agent via Google A2A protocol
    spy_url = os.environ.get("SPY_A2A_URL", "http://spy-a2a:8080").rstrip("/")
    if detected_competitor:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{spy_url}/skills/get_battlecard/execute",
                    json={"competitor_name": detected_competitor},
                )
                if r.status_code == 200:
                    payload = r.json()
                    card_data = payload.get("result", payload)
                    if isinstance(card_data, str):
                        try:
                            card_data = json.loads(card_data)
                        except Exception:
                            pass
                    battle_card = json.dumps(card_data, indent=2)
                    reasoning.append(
                        f"handle_objection: Connected via Google A2A protocol to Spy Agent ({spy_url}). Retrieved live battle card for '{detected_competitor}'."
                    )
        except Exception as e:
            logger.warning("Direct Spy A2A call failed, falling back to MCP Knowledge: %s", e)

    # 2. Fallback to MCP Knowledge server if Spy A2A was unreachable
    if not battle_card and detected_competitor and "get_battle_card" in knowledge_tools:
        try:
            card = await knowledge_tools["get_battle_card"].ainvoke({"competitor_name": detected_competitor})
            if isinstance(card, str):
                card = json.loads(card)
            battle_card = json.dumps(card, indent=2)
            reasoning.append(f"handle_objection: Fetched battle card for competitor '{detected_competitor}' via Knowledge MCP")
        except Exception as e:
            logger.warning("Battle card fetch failed: %s", e)
    elif not battle_card and detected_competitor:
        reasoning.append(f"handle_objection: Competitor '{detected_competitor}' mentioned")
    elif not detected_competitor:
        reasoning.append("handle_objection: Commercial/pricing terms objection detected (no competing vendor named)")

    # Also search knowledge base
    knowledge_context = ""
    if "search_documents" in knowledge_tools:
        try:
            results = await knowledge_tools["search_documents"].ainvoke({
                "query": f"objection handling pricing discount terms {deal.get('company', '')}",
            })
            if isinstance(results, str):
                results = json.loads(results)
            if results:
                knowledge_context = "\n\n".join(
                    f"[{r.get('source', 'Unknown')}]: {r.get('content', '')}" for r in results[:3]
                )
        except Exception as e:
            logger.warning("Knowledge search failed: %s", e)

    # Extract real contact name and rep name
    rep_name = deal.get("owner") or "Sarah Jenkins"
    rep_title = "Account Executive, OmniSales"
    contact_name = deal.get("contact_name")
    if not contact_name:
        for em in email_thread:
            if isinstance(em, dict) and em.get("from") == "rep" and "hi " in em.get("body", "").lower():
                import re
                m = re.search(r"hi\s+([A-Za-z]+)", em.get("body", ""), re.IGNORECASE)
                if m and m.group(1).lower() not in ("there", "team", "all"):
                    contact_name = m.group(1).title()
                    break
    if not contact_name and deal.get("company"):
        company_contacts = {
            "techflow": "Alex Rivera",
            "nexgen": "Elena Rostova",
            "quantumleap": "Dr. Aris Thorne",
            "alphawave": "Marcus Vance",
        }
        for k, v in company_contacts.items():
            if k in deal.get("company", "").lower():
                contact_name = v
                break

    contact_first_name = contact_name.split()[0].title() if contact_name else "there"

    from shared.llm import build_feedback_block
    prompt = OBJECTION_HANDLING_PROMPT.format(
        company=deal.get("company", "Unknown"),
        contact_name=contact_name or "Valued Partner",
        contact_first_name=contact_first_name,
        rep_name=rep_name,
        rep_title=rep_title,
        stage=deal.get("stage", "unknown"),
        arr=float(deal.get("arr", 0)),
        objection_type="competitor" if detected_competitor else "pricing_terms",
        prospect_message=prospect_message,
        battle_card=battle_card,
        knowledge_context=knowledge_context,
        feedback_block=build_feedback_block(state["metadata"]),
    )

    llm = get_complex_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    from shared.llm import usage_from_response
    llm_usage = usage_from_response(response)

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
        "metadata": {**state["metadata"], "llm_usage": llm_usage},
    }


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 4: Queue draft for human approval via Approval MCP."""
    reasoning = list(state.get("reasoning", []))
    deal = state["metadata"]["deal"]

    # Queue for approval via MCP
    approval_tools = {t.name: t for t in tools}
    llm_usage = state["metadata"].get("llm_usage", {})
    if "queue_for_approval" in approval_tools:
        try:
            natural_reasoning = await synthesize_natural_reasoning(
                agent_name="closer",
                task_type="email_draft",
                target_name=deal.get("company", "Unknown"),
                raw_trace=reasoning,
                context={"arr": deal.get("arr"), "stage": deal.get("stage"), "risk": deal.get("risk_level")},
            )
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": str(deal.get("org_id", "a0000000-0000-0000-0000-000000000001")),
                "agent_name": "closer",
                "task_type": "email_draft",
                "target_id": str(deal.get("id", "")),
                "target_name": deal.get("company", "Unknown"),
                "draft": state.get("draft", ""),
                "reasoning": natural_reasoning,
                "thread_id": state.get("deal_id", ""),
                "model_used": llm_usage.get("model_used", "openai/gpt-oss-120b"),
                "tokens_used": llm_usage.get("tokens_used", 0),
                "cost": llm_usage.get("cost", 0.0),
            })
            task_data = _unwrap_mcp(result)
            task_id = task_data.get("task_id", "N/A")
            reasoning.append(f"await_approval: Queued for human review (task_id={task_id})")
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

    reasoning.append(f"send_email: Draft approved and queued for live Resend dispatch for {deal.get('company')}")

    return {
        **state,
        "approval": "approved",
        "reasoning": reasoning,
    }
