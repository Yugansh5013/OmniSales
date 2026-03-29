"""Guardian Agent — LangGraph graph definition."""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from shared.state import AgentState


def build_guardian_graph(tools: list, checkpointer: AsyncPostgresSaver):
    """Build the Guardian agent graph.

    Flow: analyze → score → rank → {generate|END} → human → execute
    """
    from agents.guardian.nodes import (
        analyze_accounts, score_churn, rank_and_flag,
        generate_retention, await_human_approval, execute_intervention,
    )

    tool_dict = tools

    # Async wrapper functions (Python has no async lambda)
    async def _analyze(s: AgentState) -> dict:
        return await analyze_accounts(s, tool_dict)

    async def _score(s: AgentState) -> dict:
        return await score_churn(s, tool_dict)

    async def _rank(s: AgentState) -> dict:
        return await rank_and_flag(s, tool_dict)

    async def _generate(s: AgentState) -> dict:
        return await generate_retention(s, tool_dict)

    async def _human(s: AgentState) -> dict:
        return await await_human_approval(s, tool_dict)

    async def _execute(s: AgentState) -> dict:
        return await execute_intervention(s, tool_dict)

    graph = StateGraph(AgentState)
    graph.add_node("analyze", _analyze)
    graph.add_node("score", _score)
    graph.add_node("rank", _rank)
    graph.add_node("generate", _generate)
    graph.add_node("human", _human)
    graph.add_node("execute", _execute)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "score")
    graph.add_edge("score", "rank")

    graph.add_conditional_edges("rank", lambda s: s["action"], {
        "generate_retention": "generate",
        "no_action": END,
    })

    graph.add_edge("generate", "human")

    graph.add_conditional_edges("human", lambda s: s["approval"], {
        "approved": "execute",
        "rejected": END,
        "pending": END,
    })

    graph.add_edge("execute", END)

    return graph.compile(checkpointer=checkpointer, interrupt_before=["human"])
