"""Prospector Agent — LangGraph graph definition."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from shared.state import AgentState


def build_prospector_graph(tools: list, checkpointer: AsyncPostgresSaver):
    """Build the Prospector agent graph.

    Flow: research → enrich → score_icp → {identify|deprioritize} → draft → human → queue_send
    """
    from agents.prospector.nodes import (
        research_company, enrich_lead, score_icp,
        identify_contacts, draft_sequences,
        await_human_approval, queue_send, deprioritize,
    )

    tool_dict = tools

    # Async wrapper functions (Python has no async lambda)
    async def _research(s: AgentState) -> dict:
        return await research_company(s, tool_dict)

    async def _enrich(s: AgentState) -> dict:
        return await enrich_lead(s, tool_dict)

    async def _score_icp(s: AgentState) -> dict:
        return await score_icp(s, tool_dict)

    async def _identify(s: AgentState) -> dict:
        return await identify_contacts(s, tool_dict)

    async def _draft(s: AgentState) -> dict:
        return await draft_sequences(s, tool_dict)

    async def _human(s: AgentState) -> dict:
        return await await_human_approval(s, tool_dict)

    async def _queue_send(s: AgentState) -> dict:
        return await queue_send(s, tool_dict)

    async def _deprioritize(s: AgentState) -> dict:
        return await deprioritize(s, tool_dict)

    graph = StateGraph(AgentState)
    graph.add_node("research", _research)
    graph.add_node("enrich", _enrich)
    graph.add_node("score_icp", _score_icp)
    graph.add_node("identify", _identify)
    graph.add_node("draft", _draft)
    graph.add_node("human", _human)
    graph.add_node("queue_send", _queue_send)
    graph.add_node("deprioritize", _deprioritize)

    graph.set_entry_point("research")
    graph.add_edge("research", "enrich")
    graph.add_edge("enrich", "score_icp")

    graph.add_conditional_edges("score_icp", lambda s: s["action"], {
        "draft_outreach": "identify",
        "deprioritize": "deprioritize",
    })

    graph.add_edge("identify", "draft")
    graph.add_edge("draft", "human")
    graph.add_edge("deprioritize", END)

    graph.add_conditional_edges("human", lambda s: s["approval"], {
        "approved": "queue_send",
        "rejected": END,
        "pending": END,
    })

    graph.add_edge("queue_send", END)

    return graph.compile(checkpointer=checkpointer, interrupt_before=["human"])
