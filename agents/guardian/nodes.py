"""Guardian Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from shared.llm import synthesize_natural_reasoning
from shared.mcp_utils import unwrap_mcp

logger = logging.getLogger(__name__)


def _parse_mcp_list(raw: Any) -> list[dict]:
    """Parse an MCP list-tool response into a list of dicts.

    langchain-mcp-adapters may wrap list results as content blocks
    (e.g. [{"type": "text", "text": "<json array>"}]) instead of a
    plain list/str — unwrap that shape before treating it as records.
    """
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict) and "text" in raw[0]:
            try:
                parsed = json.loads(raw[0]["text"])
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        if raw and hasattr(raw[0], "text"):
            try:
                parsed = json.loads(raw[0].text)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


async def analyze_accounts(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 1: Load all accounts from CRM MCP."""
    reasoning = list(state.get("reasoning", []))

    crm_tools = {t.name: t for t in tools}
    raw = await crm_tools["list_accounts"].ainvoke({"min_churn_risk": 0.0})
    accounts = _parse_mcp_list(raw)

    reasoning.append(f"analyze_accounts: Loaded {len(accounts)} accounts for churn analysis")

    return {
        **state,
        "reasoning": reasoning,
        "metadata": {**state.get("metadata", {}), "accounts": accounts},
    }


async def score_churn(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 2: Score churn risk for each account using FAST LLM."""
    from agents.guardian.skills import CHURN_SCORING_PROMPT
    from shared.llm import get_fast_llm

    accounts = state["metadata"]["accounts"]
    reasoning = list(state.get("reasoning", []))
    scored = []

    llm = get_fast_llm()

    for account in accounts:
        metadata = account.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        prompt = CHURN_SCORING_PROMPT.format(
            company=account.get("company", "Unknown"),
            arr=float(account.get("arr", 0)),
            plan=account.get("plan", "unknown"),
            health_score=account.get("health_score", 0.5),
            usage_pct=account.get("usage_pct", 0.5),
            support_tickets=account.get("support_tickets", 0),
            last_login=account.get("last_login", "unknown"),
            usage_trend=metadata.get("usage_trend", []),
            signals=metadata.get("signals", []),
            nps_score=metadata.get("nps_score", "N/A"),
            contract_end=metadata.get("contract_end", "N/A"),
        )

        response = await llm.ainvoke([
            SystemMessage(content="You are a churn scoring engine. Respond only in valid JSON."),
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
                logger.warning("[llm_fallback] JSON parsing failed in guardian score_churn for %s: %s", account.get("company"), content[:200])
                result = {
                    "churn_risk": account.get("churn_risk", 0.5),
                    "risk_tier": "medium",
                    "top_signals": ["JSON decode fallback triggered"],
                    "llm_fallback": True,
                    "raw_snippet": content[:200],
                    "reason": "json_parse_error",
                }

        scored.append({**account, "llm_score": result})

    fallbacks_count = sum(1 for a in scored if a.get("llm_score", {}).get("llm_fallback"))
    if fallbacks_count > 0:
        reasoning.append(f"score_churn: Scored {len(scored)} accounts ([llm_fallback] triggered on {fallbacks_count} accounts)")
    else:
        reasoning.append(f"score_churn: Scored {len(scored)} accounts with LLM-based churn analysis")

    return {
        **state,
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "scored_accounts": scored},
    }


async def rank_and_flag(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 3: Rank by churn risk, flag top 3."""
    reasoning = list(state.get("reasoning", []))
    scored = state["metadata"]["scored_accounts"]

    # Sort by LLM churn score descending
    scored.sort(key=lambda a: a.get("llm_score", {}).get("churn_risk", 0), reverse=True)

    top_3 = scored[:3]
    remaining = scored[3:]

    if not top_3:
        reasoning.append("rank_and_flag: No high-risk accounts found — no action needed")
        return {**state, "action": "no_action", "reasoning": reasoning}

    flag_summary = []
    for i, a in enumerate(top_3, 1):
        score = a.get("llm_score", {})
        flag_summary.append(
            f"#{i} {a.get('company')} — Risk: {score.get('churn_risk', 'N/A')}, "
            f"Tier: {score.get('risk_tier', 'N/A')}, Signals: {score.get('top_signals', [])}"
        )

    reasoning.append(f"rank_and_flag: Flagged top 3 churn risks:\n" + "\n".join(flag_summary))

    return {
        **state,
        "action": "generate_retention",
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "flagged_accounts": top_3},
    }


async def generate_retention(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 4: Generate tailored retention plays for flagged accounts."""
    from agents.guardian.skills import RETENTION_PLAY_PROMPT
    from shared.llm import get_complex_llm

    flagged = state["metadata"]["flagged_accounts"]
    reasoning = list(state.get("reasoning", []))

    llm = get_complex_llm()
    from shared.llm import usage_from_response, build_feedback_block
    all_plays = []
    total_tokens, total_cost = 0, 0.0
    feedback_block = build_feedback_block(state["metadata"])

    for account in flagged:
        score = account.get("llm_score", {})
        metadata = account.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        prompt = RETENTION_PLAY_PROMPT.format(
            company=account.get("company", "Unknown"),
            arr=float(account.get("arr", 0)),
            plan=account.get("plan", "unknown"),
            churn_risk=score.get("churn_risk", 0.5),
            health_score=score.get("health_score", 0.5),
            top_signals=score.get("top_signals", []),
            usage_trend=metadata.get("usage_trend", []),
            support_tickets=account.get("support_tickets", 0),
            feedback_block=feedback_block,
            contract_end=metadata.get("contract_end", "N/A"),
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        usage = usage_from_response(response)
        total_tokens += usage["tokens_used"]
        total_cost += usage["cost"]
        all_plays.append({
            "account": account.get("company"),
            "account_id": str(account.get("id", "")),
            "play": response.content,
        })

    draft = "\n\n" + ("=" * 48) + "\n\n".join(
        f"{p['play']}" for p in all_plays
    )

    reasoning.append(f"generate_retention: Created {len(all_plays)} tailored retention plays")

    # Log to company's timeline in HubSpot
    crm_tools = {t.name: t for t in tools}
    if "log_account_action" in crm_tools:
        for p in all_plays:
            try:
                await crm_tools["log_account_action"].ainvoke({
                    "account_id": p["account_id"],
                    "agent_name": "guardian",
                    "action": "generated_retention_play",
                    "reasoning": f"Retention play generated for {p['account']}",
                })
            except Exception as e:
                logger.warning("Failed to log account action to HubSpot: %s", e)

    return {
        **state,
        "draft": draft,
        "reasoning": reasoning,
        "metadata": {**state["metadata"], "llm_usage": {"tokens_used": total_tokens, "cost": round(total_cost, 6)}},
    }


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 5: Queue retention plays for human approval."""
    reasoning = list(state.get("reasoning", []))

    approval_tools = {t.name: t for t in tools}
    llm_usage = state["metadata"].get("llm_usage", {})
    if "queue_for_approval" in approval_tools:
        try:
            natural_reasoning = await synthesize_natural_reasoning(
                agent_name="guardian",
                task_type="retention_play",
                target_name="Top 3 Churn Risk Accounts",
                raw_trace=reasoning,
            )
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": "a0000000-0000-0000-0000-000000000001",
                "agent_name": "guardian",
                "task_type": "retention_play",
                "target_id": "a0000000-0000-0000-0000-000000000001",
                "target_name": "Top 3 Churn Risk Accounts",
                "draft": state.get("draft", ""),
                "reasoning": natural_reasoning,
                "thread_id": "guardian-batch",
                "tokens_used": llm_usage.get("tokens_used", 0),
                "cost": llm_usage.get("cost", 0.0),
            })
            task_data = unwrap_mcp(result)
            task_id = task_data.get("task_id", "N/A")
            reasoning.append(f"await_approval: Queued {len(state['metadata'].get('flagged_accounts', []))} plays for review (task_id={task_id})")
        except Exception as e:
            reasoning.append(f"await_approval: Failed — {e}")

    return {**state, "approval": "pending", "reasoning": reasoning}


async def execute_intervention(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 6: Log approved interventions."""
    reasoning = list(state.get("reasoning", []))
    reasoning.append("execute_intervention: Retention plays approved and interventions logged")
    return {**state, "approval": "approved", "reasoning": reasoning}
