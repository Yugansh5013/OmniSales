# 📚 FastMCP Knowledge Server & RAG

The **FastMCP Knowledge Server** (`:8003`) provides semantic document retrieval and competitive battlecard lookups to the agent swarm using the **Model Context Protocol (FastMCP)**. It connects to **Pinecone** vector indexes to empower agents with Retrieval-Augmented Generation (RAG) over sales playbooks, pricing policies, objection handling guides, and compliance documentation.

---

## 1. FastMCP Tools Exposed

| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `search_documents` | `query: str, category: str = None, top_k: int = 3` | Semantic similarity search across sales playbooks, objection guides, and case studies |
| `get_battle_card` | `competitor: str` | Fetches dedicated competitor positioning, weaknesses, and pricing tactics from the knowledge base |

---

## 2. Pinecone Vector Architecture

- **Vector Database**: Pinecone Cloud
- **Index Name**: `omnisales-knowledge`
- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions, cosine similarity)
- **Document Chunking**: Markdown-aware recursive character chunking (500 tokens per chunk with 50-token overlap).

### Seeded Knowledge Corpus
The RAG index is pre-seeded with sales intelligence documents via [`scripts/seed_pinecone.py`](file:///c:/use_this/ET_genai/OmniSales/scripts/seed_pinecone.py):
1. **Competitive Battlecards**: In-depth positioning against legacy CRMs (Salesforce, HubSpot, AcmeCRM).
2. **Enterprise Pricing Playbooks**: Volume discount tiers, annual commitment policies, and custom SLA parameters.
3. **Security & Compliance Briefs**: SOC 2 Type II certifications, HIPAA compliance, zero-data-retention guarantees, and data residency policies.
4. **Customer Success Win Stories**: Technical case studies demonstrating sub-second agent latency and 3x SDR productivity gains.

---

## 3. Reliability & Fallback Tagging

To ensure the system never crashes during offline evaluation or API rate limit events, the Knowledge Server implements a graceful fallback mode. 

**Strict Honesty & Provenance**: Every fallback response is explicitly tagged with `"source": "fallback_demo_data"`. The agents and evaluation suite check this metadata tag so fallback results are never misrepresented as live vector retrievals.

---

## 4. Endpoints & Protocol Mount

- **MCP Protocol Endpoint**: `http://mcp-knowledge:8003/mcp`
- **Health Endpoint**: `http://mcp-knowledge:8003/health`
