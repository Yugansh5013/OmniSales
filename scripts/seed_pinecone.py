"""Seed the Pinecone Knowledge vector store via the MCP Server."""

import asyncio
import os
import sys

from httpx import AsyncClient


async def main():
    # Attempt to load the .env to see if they provided keys
    if not os.path.exists(".env"):
        print("❌ Error: .env file missing. Please configure Pinecone first.")
        sys.exit(1)

    with open(".env", "r") as f:
        env_content = f.read()
        if "your_pinecone_api_key" in env_content:
            print("❌ Error: You haven't added your Pinecone API key to the .env file yet.")
            print("Please follow the setup guide first before running this script.")
            sys.exit(1)

    print("🌱 Connecting to the OmniSales Knowledge MCP Server...")

    documents = [
        {
            "org_id": "org_default",
            "title": "OmniSales Overview",
            "doc_type": "product_doc",
            "content": (
                "OmniSales provides 14x faster deal risk detection compared to manual review. "
                "Our autonomous agents monitor deal activity 24/7 and classify risk levels in real-time. "
                "The Closer agent handles stalled deals, the Prospector agent analyzes leads, and the "
                "Guardian agent monitors active accounts for churn telemetry."
            )
        },
        {
            "org_id": "org_default",
            "title": "Objection Handling Playbook",
            "doc_type": "faq",
            "content": (
                "When a prospect raises pricing concerns, acknowledge their budget constraints, "
                "highlight ROI metrics (average $6.1M annual impact), and offer a phased deployment "
                "starting with the Closer agent only at $29/user/mo so they can prove value fast."
            )
        },
        {
            "org_id": "org_default",
            "title": "DataVault Security Case Study",
            "doc_type": "case_study",
            "content": (
                "Case Study: DataVault Security reduced their entire sales cycle by 40% using OmniSales. "
                "The Prospector agent identified 12 qualified leads in the first week automatically, and "
                "the Closer agent re-engaged 3 stalled deals worth $180K total ARR without any human intervention."
            )
        },
        {
            "org_id": "org_default",
            "title": "Battle Card: AcmeCRM",
            "doc_type": "battle_card",
            "content": (
                "Pricing: $39/user/mo (starter), $69/user/mo (professional), $99/user/mo (enterprise). "
                "Strengths: Strong brand, Large ecosystem, SOC 2 Type II compliance. "
                "Weaknesses: No AI agents, only 3 native integrations, manual pipeline review only. "
                "Our Advantage: OmniSales provides fully autonomous AI agents, 14x faster risk detection, "
                "a robust Model Context Protocol (MCP) server architecture, and real-time Agent-to-Agent (A2A) insights."
            )
        },
        {
            "org_id": "org_default",
            "title": "Battle Card: PipeDrive Pro",
            "doc_type": "battle_card",
            "content": (
                "Pricing: $29/user/mo (starter), $49/user/mo (professional). "
                "Strengths: Lower price point, excellent mobile UX. "
                "Weaknesses: No multi-agent system, basic reporting, no automation beyond simple triggers. "
                "Our Advantage: Enterprise-grade autonomous RAG AI, real-time churn prediction, "
                "and an enterprise event architecture using Apache Kafka."
            )
        }
    ]

    # We will invoke the 'ingest_document' tool directly against the FastMCP HTTP transport
    async with AsyncClient(timeout=60.0) as client:
        # Check if the server is up
        try:
            await client.get("http://localhost:8003/mcp")
        except Exception:
            print("❌ Error: Cannot reach Knowledge MCP Server at http://localhost:8003.")
            print("Are your Docker containers running? Have you restarted them after updating .env?")
            sys.exit(1)

        for doc in documents:
            print(f"📥 Upserting: {doc['title']}...")
            
            # FastMCP format
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "ingest_document",
                    "arguments": doc
                }
            }

            resp = await client.post("http://localhost:8003/mcp", json=payload)
            
            if resp.status_code == 200:
                result = resp.json().get("result", {})
                if result.get("isError"):
                    print(f"   ⚠️ Failed: {result}")
                else:
                    print(f"   ✅ Success!")
            else:
                print(f"   ❌ HTTP Error {resp.status_code}: {resp.text}")

        print("\n🎉 Seeding complete! The agents are now using your live Pinecone DB.")

if __name__ == "__main__":
    asyncio.run(main())
