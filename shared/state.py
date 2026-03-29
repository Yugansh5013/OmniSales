"""Shared LangGraph agent state schema used by all agents."""

from __future__ import annotations

from typing import Annotated, Any, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Unified state object that flows through every LangGraph node.

    All 3 agents (Closer, Prospector, Guardian) share this schema so the
    API gateway, approval queue, and audit trail can handle them uniformly.
    """

    # LangGraph message accumulator
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Entity references (only one is set per invocation)
    lead_id: str | None
    deal_id: str | None
    account_id: str | None

    # Current agent action being planned / taken
    action: str  # e.g. "follow_up", "objection", "no_action", "draft_outreach"

    # Output draft awaiting human approval
    draft: str | None

    # HITL approval status
    approval: str | None  # "approved" | "rejected" | "pending"

    # Immutable audit trail — each node appends its reasoning
    reasoning: list[str]

    # Agent-specific payload (flexible per agent)
    metadata: dict[str, Any]
