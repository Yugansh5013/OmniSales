"""RAG Knowledge MCP Server — wraps Pinecone vector search for OmniSales agents."""

import logging
import os

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("RAG Knowledge MCP")


def _get_pinecone_index():
    """Init Pinecone client for integrated inference index."""
    from pinecone import Pinecone

    api_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX", "omnisales-knowledge")
    
    if not api_key or api_key == "your_pinecone_api_key":
        raise ValueError("PINECONE_API_KEY is not configured properly.")

    pc = Pinecone(api_key=api_key)
    return pc.Index(index_name)


@mcp.tool()
async def search_documents(query: str, org_id: str = "org_default", top_k: int = 5) -> list[dict]:
    """Semantic search over the knowledge base.

    Use this to find relevant product docs, case studies, battle cards,
    pre-approved responses, and email templates.

    Args:
        query: Natural language search query
        org_id: Organization namespace for isolation
        top_k: Number of results to return (default 5)

    Returns list of matching document chunks with scores.
    """
    try:
        index = _get_pinecone_index()
        # Using integrated inference search syntax
        results = index.search(
            namespace=f"org-{org_id}",
            query={"inputs": {"text": query}, "top_k": top_k}
        )
        
        # Convert Object to dict if necessary, or just access attributes
        try:
            hits = results.result.hits if hasattr(results, "result") else results.get("result", {}).get("hits", [])
        except Exception:
            try:
                hits = results["result"]["hits"]
            except Exception:
                hits = []
        
        return [
            {
                "content": getattr(match.fields, "text", match.fields.get("text", "")) if hasattr(match, "fields") else match.get("fields", {}).get("text", ""),
                "source": getattr(match.fields, "source", match.fields.get("source", "unknown")) if hasattr(match, "fields") else match.get("fields", {}).get("source", "unknown"),
                "doc_type": getattr(match.fields, "doc_type", match.fields.get("doc_type", "general")) if hasattr(match, "fields") else match.get("fields", {}).get("doc_type", "general"),
                "relevance_score": round(float(getattr(match, "_score", match.get("_score", 0.0))), 4),
            }
            for match in hits
        ]
    except Exception as e:
        logger.warning("Pinecone search failed (may not be configured): %s", e)
        # Fallback: return hardcoded knowledge for demo
        return _fallback_search(query)


@mcp.tool()
async def ingest_document(org_id: str, title: str, content: str, doc_type: str = "general") -> dict:
    """Ingest a new document into the knowledge base.

    Chunks the content, generates embeddings, and upserts to Pinecone.

    Args:
        org_id: Organization namespace
        title: Document title
        content: Full document text
        doc_type: Type (product_doc|case_study|battle_card|email_template|faq)
    """
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_text(content)

        records = []
        for i, chunk in enumerate(chunks):
            # For integrated inference, we use upsert_records and provide the target field 'text'
            records.append({
                "_id": f"{title.replace(' ', '_').lower()}_{i}",
                "text": chunk,
                "source": title,
                "doc_type": doc_type
            })

        index = _get_pinecone_index()
        index.upsert_records(namespace=f"org-{org_id}", records=records)

        return {"ingested": True, "title": title, "chunks": len(chunks)}
    except Exception as e:
        logger.warning("Pinecone ingest failed: %s", e)
        return {"ingested": False, "error": str(e)}


@mcp.tool()
async def get_battle_card(competitor_name: str) -> dict:
    """Get a competitor battle card from the knowledge base.

    Returns pricing, strengths, weaknesses, and differentiators for the competitor.
    This is a convenience wrapper that searches for battle card documents.
    """
    results = await search_documents(
        query=f"battle card {competitor_name} pricing strengths weaknesses",
        top_k=3,
    )

    if results:
        return {"competitor": competitor_name, "results": results}

    # Fallback to hardcoded battle cards for demo
    return _fallback_battle_card(competitor_name)


# ── Fallback data for demo (when Pinecone isn't configured) ──


def _fallback_search(query: str) -> list[dict]:
    """Return hardcoded knowledge chunks for demo when Pinecone is unavailable."""
    knowledge = [
        {
            "content": "OmniSales provides a 14x faster deal risk detection compared to manual review. "
            "Our autonomous agents monitor deal activity 24/7 and classify risk levels in real-time.",
            "source": "Product Overview",
            "doc_type": "product_doc",
            "relevance_score": 0.92,
        },
        {
            "content": "When a prospect raises pricing concerns, acknowledge their budget constraints, "
            "highlight ROI metrics ($6.1M annual impact), and offer a phased deployment starting "
            "with the Closer agent only at $29/user/mo.",
            "source": "Objection Handling Playbook",
            "doc_type": "faq",
            "relevance_score": 0.88,
        },
        {
            "content": "Case Study: DataVault Security reduced sales cycle by 40% using OmniSales. "
            "The Prospector agent identified 12 qualified leads in the first week, and the Closer "
            "agent re-engaged 3 stalled deals worth $180K total ARR.",
            "source": "DataVault Case Study",
            "doc_type": "case_study",
            "relevance_score": 0.85,
        },
    ]
    return knowledge[:3]


def _fallback_battle_card(competitor_name: str) -> dict:
    """Return hardcoded battle card data for demo."""
    cards = {
        "acmecrm": {
            "competitor": "AcmeCRM",
            "pricing": {"starter": "$39/user/mo", "professional": "$69/user/mo", "enterprise": "$99/user/mo"},
            "strengths": ["Strong brand", "Large ecosystem", "SOC 2 Type II"],
            "weaknesses": ["No AI agents", "3 native integrations only", "Manual review only"],
            "our_advantage": ["Autonomous AI agents", "14x faster risk detection", "12 MCP servers", "A2A protocol"],
        },
        "pipedrivepro": {
            "competitor": "PipeDrive Pro",
            "pricing": {"starter": "$29/user/mo", "professional": "$49/user/mo"},
            "strengths": ["Lower price point", "Good mobile UX"],
            "weaknesses": ["No multi-agent system", "Basic reporting"],
            "our_advantage": ["Enterprise-grade AI", "Real-time churn prediction", "Kafka event architecture"],
        },
    }
    key = competitor_name.lower().replace(" ", "")
    return cards.get(key, {"competitor": competitor_name, "note": "No battle card data available"})


if __name__ == "__main__":
    import uvicorn
    mcp_app = mcp.http_app(path="/mcp")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8003)
