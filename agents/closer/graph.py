"""Closer Agent — LangGraph graph definition with HITL interrupt pattern."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from shared.state import AgentState


def build_closer_graph(tools: list, checkpointer: AsyncPostgresSaver):
    """Build the Closer agent graph.

    Flow: analyze → classify → {draft|objection|END} → human → {send|END}

    The graph pauses at the 'human' node via interrupt_before,
    allowing the dashboard to show the draft for approval.
    """
    from agents.closer.nodes import (
        analyze_deal,
        classify_risk,
        draft_followup,
        handle_objection,
        await_human_approval,
        send_email,
    )

    # Create tool dict for nodes
    tool_dict = tools

    # Async wrapper functions — Python has no async lambda,
    # so we define proper async functions that await the coroutines.
    async def _analyze(s: AgentState) -> dict:
        return await analyze_deal(s, tool_dict)

    async def _classify(s: AgentState) -> dict:
        return await classify_risk(s, tool_dict)

    async def _draft(s: AgentState) -> dict:
        return await draft_followup(s, tool_dict)

    async def _objection(s: AgentState) -> dict:
        return await handle_objection(s, tool_dict)

    async def _human(s: AgentState) -> dict:
        return await await_human_approval(s, tool_dict)

    async def _send(s: AgentState) -> dict:
        return await send_email(s, tool_dict)

    graph = StateGraph(AgentState)

    # Add nodes — each wraps the async node function with tools
    graph.add_node("analyze", _analyze)
    graph.add_node("classify", _classify)
    graph.add_node("draft", _draft)
    graph.add_node("objection", _objection)
    graph.add_node("human", _human)
    graph.add_node("send", _send)

    # Set entry point
    graph.set_entry_point("analyze")

    # Edges
    graph.add_edge("analyze", "classify")

    # Conditional: classify → draft | objection | END
    graph.add_conditional_edges(
        "classify",
        lambda s: s["action"],
        {
            "follow_up": "draft",
            "objection": "objection",
            "no_action": END,
        },
    )

    graph.add_edge("draft", "human")
    graph.add_edge("objection", "human")

    # Conditional: human → send | END
    graph.add_conditional_edges(
        "human",
        lambda s: s["approval"],
        {
            "approved": "send",
            "rejected": END,
            "pending": END,  # Will be resumed after approval
        },
    )

    graph.add_edge("send", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human"],  # ← PAUSE FOR HUMAN REVIEW
    )
