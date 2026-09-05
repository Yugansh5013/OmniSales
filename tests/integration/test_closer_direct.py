"""Direct integration test of the Closer agent graph with a stalled deal."""
import asyncio
import traceback
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

async def main():
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from agents.closer.graph import build_closer_graph
    from uuid import uuid4

    DB_URL = os.environ.get("DATABASE_URL", "")

    mcp_config = {
        "crm": {"url": os.environ.get("MCP_CRM_URL", "http://localhost:8001/mcp"), "transport": "http"},
        "knowledge": {"url": os.environ.get("MCP_KNOWLEDGE_URL", "http://localhost:8003/mcp"), "transport": "http"},
        "approvals": {"url": os.environ.get("MCP_APPROVALS_URL", "http://localhost:8004/mcp"), "transport": "http"},
    }
    client = MultiServerMCPClient(mcp_config)
    tools = await client.get_tools()

    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        graph = build_closer_graph(tools, checkpointer)
        config = {"configurable": {"thread_id": str(uuid4())}}

        initial_state = {
            "messages": [], "lead_id": None,
            "deal_id": "20000000-0000-0000-0000-000000000010",
            "account_id": None,
            "action": "", "draft": None, "approval": None,
            "reasoning": [], "metadata": {},
        }

        try:
            result = await graph.ainvoke(initial_state, config)
            print(f"SUCCESS! action={result.get('action')}")
            print(f"draft preview: {str(result.get('draft',''))[:300]}")
            print(f"reasoning: {result.get('reasoning', [])}")
        except Exception as e:
            print(f"EXCEPTION: {type(e).__name__}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
