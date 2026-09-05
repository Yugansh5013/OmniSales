"""Direct integration test of the Prospector agent graph."""
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
    from agents.prospector.graph import build_prospector_graph
    from uuid import uuid4

    DB_URL = os.environ.get("DATABASE_URL", "")
    
    print("[1] Getting MCP tools...")
    mcp_config = {
        "crm": {"url": os.environ.get("MCP_CRM_URL", "http://localhost:8001/mcp"), "transport": "http"},
        "knowledge": {"url": os.environ.get("MCP_KNOWLEDGE_URL", "http://localhost:8003/mcp"), "transport": "http"},
        "approvals": {"url": os.environ.get("MCP_APPROVALS_URL", "http://localhost:8004/mcp"), "transport": "http"},
    }
    client = MultiServerMCPClient(mcp_config)
    tools = await client.get_tools()
    print(f"   Got {len(tools)} tools")

    print("[2] Creating checkpointer...")
    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        print("[3] Building graph...")
        graph = build_prospector_graph(tools, checkpointer)

        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [], "lead_id": "10000000-0000-0000-0000-000000000001",
            "deal_id": None, "account_id": None,
            "action": "", "draft": None, "approval": None,
            "reasoning": [], "metadata": {},
        }

        print(f"[4] Running graph with lead_id={initial_state['lead_id']}...")
        try:
            result = await graph.ainvoke(initial_state, config)
            print(f"\n✅ SUCCESS!")
            print(f"   action:  {result.get('action')}")
            print(f"   draft:   {str(result.get('draft', ''))[:200]}")
            print(f"   reasoning: {result.get('reasoning', [])}")
        except Exception as e:
            print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
