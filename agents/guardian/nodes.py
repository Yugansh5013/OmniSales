"""Guardian Agent — LangGraph node functions."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


async def analyze_accounts(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 1: Load all accounts from CRM MCP."""
    reasoning = list(state.get("reasoning", []))

    crm_tools = {t.name: t for t in tools}
    accounts = await crm_tools["list_accounts"].ainvoke({"min_churn_risk": 0.0})

    if isinstance(accounts, str):
        accounts = json.loads(accounts)

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

        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            result = json.loads(content[start:end]) if start >= 0 else {
                "churn_risk": account.get("churn_risk", 0.5),
                "risk_tier": "medium",
            }

        scored.append({**account, "llm_score": result})

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
    all_plays = []

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
            contract_end=metadata.get("contract_end", "N/A"),
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        all_plays.append({
            "account": account.get("company"),
            "account_id": str(account.get("id", "")),
            "play": response.content,
        })

    draft = "\n\n---\n\n".join(
        f"### {p['account']}\n\n{p['play']}" for p in all_plays
    )

    reasoning.append(f"generate_retention: Created {len(all_plays)} tailored retention plays")

    return {**state, "draft": draft, "reasoning": reasoning}


async def await_human_approval(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 5: Queue retention plays for human approval."""
    reasoning = list(state.get("reasoning", []))

    approval_tools = {t.name: t for t in tools}
    if "queue_for_approval" in approval_tools:
        try:
            result = await approval_tools["queue_for_approval"].ainvoke({
                "org_id": "a0000000-0000-0000-0000-000000000001",
                "agent_name": "guardian",
                "task_type": "retention_play",
                "target_id": "a0000000-0000-0000-0000-000000000001",
                "target_name": "Top 3 Churn Risk Accounts",
                "draft": state.get("draft", ""),
                "reasoning": "\n".join(reasoning),
                "thread_id": "guardian-batch",
            })
            reasoning.append(f"await_approval: Queued {len(state['metadata'].get('flagged_accounts', []))} plays for review")
        except Exception as e:
            reasoning.append(f"await_approval: Failed — {e}")

    return {**state, "approval": "pending", "reasoning": reasoning}


async def execute_intervention(state: dict[str, Any], tools: dict) -> dict[str, Any]:
    """Node 6: Log approved interventions."""
    reasoning = list(state.get("reasoning", []))
    reasoning.append("execute_intervention: Retention plays approved and interventions logged")
    return {**state, "approval": "approved", "reasoning": reasoning}
