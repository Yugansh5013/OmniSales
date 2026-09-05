# 💾 FastMCP CRM Server & HubSpot Sync

The **FastMCP CRM Server** (`:8001`) exposes standardized CRM data access and mutation tools to the agent swarm via the **Model Context Protocol (FastMCP)**. It serves as an abstraction layer between the AI agents, the local PostgreSQL database, and external enterprise CRMs like **HubSpot**.

---

## 1. FastMCP Tools Exposed

| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `get_deal` | `deal_id: str` | Retrieves deal record, ARR, stage, close date, and conversation thread |
| `list_deals` | `limit: int = 50, stage: str = None` | Lists active pipeline opportunities |
| `update_deal` | `deal_id: str, updates: dict` | Updates deal properties in PostgreSQL and triggers HubSpot CRM sync |
| `get_lead` | `lead_id: str` | Retrieves lead profile, domain, funding, and employee count |
| `list_leads` | `status: str = "new"` | Fetches uncontacted leads for the Prospector Agent |
| `update_lead` | `lead_id: str, updates: dict` | Updates lead ICP score, tier, and contact status |
| `get_account` | `account_id: str` | Retrieves customer account telemetry, health score, and open tickets |
| `list_accounts` | `limit: int = 50` | Fetches customer accounts for portfolio churn audit |
| `log_agent_action` | `agent_name, action, target_type, target_id, details` | Appends an immutable record to the audit trail |

---

## 2. Live HubSpot CRM Synchronization Engine

The FastMCP CRM server integrates directly with HubSpot's CRM v3 REST API via `shared.hubspot_client`:

```mermaid
flowchart LR
    AGENT["🤖 Autonomous Agent\n(Closer / Prospector)"] -->|Tool Call: update_deal| MCP["💾 FastMCP CRM Server :8001"]
    
    subgraph SYNC ["Bidirectional Sync Logic"]
        MCP -->|1. Write Transaction| PG[(Neon PostgreSQL)]
        MCP -->|2. Asynchronous REST Call| HS_CLIENT["shared.hubspot_client"]
    end
    
    HS_CLIENT -->|PATCH /crm/v3/objects/deals/{id}| HS["🟧 Live HubSpot CRM API"]
    HS -->|Update Pipeline Board| HS_UI["HubSpot Deals Board UI"]
```

### Supported HubSpot Sync Operations
1. **Live Deal Stage Movement**:
   When Closer completes an action or a rep approves a task, the deal stage moves in PostgreSQL and immediately issues:
   `PATCH https://api.hubapi.com/crm/v3/objects/deals/{hubspot_id}`
   Mapping:
   - `proposal` -> `presentationscheduled`
   - `negotiation` -> `decisionmakerboughtin`
   - `contract_sent` -> `contractsent`
   - `closed_won` -> `closedwon`
2. **Engagement & Meeting Notes**:
   Generates HubSpot engagement notes capturing agent reasoning and customer email copy.
3. **Contact & Company Associations**:
   Maintains bidirectional associations between contacts, companies, and deals (`associations/contacts` and `associations/companies`).

---

## 3. Endpoints & Protocol Mount

- **MCP Protocol Endpoint**: `http://mcp-crm:8001/mcp` (Handles FastMCP tool discovery, schema inspection, and tool execution)
- **Health Endpoint**: `http://mcp-crm:8001/health` (HTTP 200 health probe)
