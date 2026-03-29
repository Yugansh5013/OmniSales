# OmniSales: The Autonomous Revenue Department

## Complete Technical Architecture & Engineering Blueprint

> **Version:** 2.0 — Hackathon Edition  
> **Stack:** LangGraph · MCP · A2A · Kafka · Kubernetes · Docker  
> **LLM:** Groq (`llama-3.3-70b-versatile` + `llama-3.1-8b-instant`)

---

## Table of Contents

1. [The Core Problem](#1-the-core-problem)
2. [The Solution](#2-the-solution)
3. [Hackathon MVP Scope](#3-hackathon-mvp-scope-2-day-plan)
4. [The AI Workforce — The 4 Agents](#4-the-ai-workforce--the-4-agents)
5. [The Human's Role](#5-the-humans-role)
6. [High-Level Architecture](#6-high-level-architecture)
7. [Technology Stack](#7-technology-stack)
8. [Agent Framework — LangGraph](#8-agent-framework--langgraph)
9. [MCP — Model Context Protocol Integration](#9-mcp--model-context-protocol-integration)
10. [Agent-to-Agent Communication](#10-agent-to-agent-communication)
11. [Data Architecture](#11-data-architecture)
12. [Specialized Agent Skills](#12-specialized-agent-skills)
13. [API Endpoints](#13-api-endpoints)
14. [Next.js Dashboard](#14-nextjs-dashboard)
15. [Containerization with Docker](#15-containerization-with-docker)
16. [Kubernetes Orchestration & Scaling](#16-kubernetes-orchestration--scaling)
17. [CI/CD Pipeline](#17-cicd-pipeline)
18. [Security & Compliance](#18-security--compliance)
19. [Observability](#19-observability)
20. [Error Handling & Resilience](#20-error-handling--resilience)
21. [Demo Scenarios](#21-demo-scenarios-track-4-mandatory-walkthrough)
22. [Impact Model](#22-impact-model-quantified-business-value)
23. [Implementation Roadmap](#23-implementation-roadmap)

---

## 1. The Core Problem

Traditional enterprise sales teams waste the majority of their time acting as **human APIs** — manually moving data between siloed software tools. This leads to:

- **Leaked revenue** from missed follow-ups and stalled deals
- **Pipeline rot** from deals that go cold without intervention
- **Customer churn** detectable weeks earlier with proper monitoring
- **Slow competitive response** — reps learn about competitor changes days late
- **Data quality degradation** — CRM data is only as good as the reps who remember to update it

The core insight: **80% of what a sales team does is information routing** — find a lead, research them, write an email, log the activity, check if they replied, follow up if not. These are automatable workflows, not tasks requiring human judgment.

---

## 2. The Solution

OmniSales is a **multi-agent AI system** that replaces the disjointed sales software stack with a fully autonomous revenue department.

Instead of just storing data like a traditional CRM, the system actively:
- **Reads** data continuously
- **Makes decisions** based on real-time signals
- **Executes workflows** with minimal human intervention
- **Self-corrects** by adjusting messaging based on engagement signals and competitor data
- **Escalates appropriately** by surfacing decisions that require human judgment

The system is built around **four specialized AI agents** that share a central memory (PostgreSQL), communicate via event streaming (Kafka) and direct peer-to-peer calls (A2A protocol), and connect to external services through the **MCP (Model Context Protocol)** standard.

### Unique Value Proposition

| Capability | Existing Tools (HubSpot, Salesforce) | OmniSales |
| :--- | :--- | :--- |
| Deal risk detection | Manual pipeline review | Real-time LLM risk classification |
| Objection handling | Static playbook templates | RAG over company docs + live competitive intel |
| Follow-up timing | Rule-based cadences | Adaptive, context-aware drafting |
| Competitive intel | Manual research / alerts | Autonomous scraping + battle card generation |
| Cross-agent coordination | None (siloed tools) | Kafka + A2A event broadcasting |

---

## 3. Hackathon MVP Scope (2-Day Plan)

> **MVP Focus: 3 core agents (Closer + Prospector + Guardian) + MCP tool integration + A2A protocol demo** — covering all 3 mandatory Track 4 scenarios with MCP-decoupled architecture, inter-agent A2A calls, HITL approval, RAG, and a live dashboard.

### Track 4 Mandatory Scenario Coverage

| Hackathon Scenario | Required Agent | Autonomous Steps | Status |
| :--- | :--- | :--- | :---: |
| **Cold outreach sequence** — research company, identify 2 decision-makers, draft personalized 3-email sequences per person | **Prospector** | 6 steps: research → enrich → ICP score → identify contacts → draft sequences → queue for approval | ✅ MVP |
| **Deal risk alert** — 10-day silence after pricing discussion, assess risk, check competitor engagement, generate re-engagement strategy | **Closer** | 8 steps: detect staleness → load context → classify risk → RAG objection handling → draft email → HITL pause → approve → send | ✅ MVP |
| **Churn prediction** — flag 3 highest churn risks from 20 accounts, explain why, propose tailored retention plays | **Guardian** | 6 steps: analyze usage data → score churn risk → rank accounts → generate tailored retention plays → queue for approval → execute | ✅ MVP |
| **Surprise scenarios (2-3)** — unknown scenarios thrown by judges during live demo | All 3 agents | Flexible reasoning via LangGraph ReAct loops | ✅ Ready |

### What We're Building

| Component | In MVP? | Detail |
| :--- | :---: | :--- |
| **The Orchestrator Agent** (Supervisor) | ✅ | Event-driven supervisor (`asyncio.gather`), stateless chat interface, central task dispatching |
| **The Closer Agent** (LangGraph) | ✅ | Full graph: analyze → classify → draft/objection → human approval → send |
| **The Prospector Agent** (LangGraph) | ✅ | Full graph: research → enrich → ICP score → draft outreach → human approval |
| **The Guardian Agent** (LangGraph) | ✅ | Full graph: analyze usage → score churn → generate retention play → human approval |
| **FastAPI Backend** | ✅ | REST API + WebSocket for real-time dashboard updates |
| **Next.js Dashboard** | ✅ | Approval queue, deal timeline, audit trail viewer |
| **PostgreSQL + Redis** | ✅ | Core CRM data + simulated dataset, agent state, caching |
| **Pinecone (RAG)** | ✅ | Semantic search over company docs for objection handling |
| **Docker Compose** | ✅ | Containerized local stack for live demo |
| **K8s Manifests + KEDA** | ✅ | Architecture showcase (manifests ready, not live-deployed) |
| **Kafka** | ✅ | Event-driven triggers, inter-agent messaging |
| **3 Custom MCP Servers** | ✅ | Approval Queue MCP, RAG Knowledge MCP, CRM Simulator MCP |
| **Spy A2A Server (minimal)** | ✅ | Battle card endpoint only — Closer calls it live via A2A protocol |
| Full Spy Agent (scraping pipeline) | ⬜ | Post-hackathon (full Playwright scraping + change detection) |

### Simulated Dataset (for Demo)

Since the hackathon requires connection to "at least one real data source," we will prepare:
- **20 accounts** with usage metrics, support tickets, and health scores (Guardian scenario)
- **15 active deals** across pipeline stages with email thread histories (Closer scenario)
- **5 target company profiles** with enrichment data (Prospector scenario)
- All seeded into PostgreSQL on `docker compose up`

### Day 1 — Foundation + MCP Servers + Closer + Prospector (~12h)

| Block | Hours | Deliverable |
| :--- | :---: | :--- |
| Project scaffold + Docker Compose | 1.5h | Postgres, Redis, Kafka, all MCP servers running locally |
| PostgreSQL schema + seed data (all 3 scenarios) | 1h | `leads`, `deals`, `accounts`, `agent_tasks` with demo data |
| **3 Custom MCP Servers** (Approvals + Knowledge + CRM Sim) | 2h | Agents connect via MCP protocol, tool discovery at runtime |
| Pinecone ingestion (company docs + battle cards) | 1h | RAG ready for Closer objection handling |
| **Closer Agent** — full LangGraph with HITL + MCP tools | 3h | Deal risk scenario working end-to-end via MCP |
| **Prospector Agent** — LangGraph + MCP tools | 2.5h | Cold outreach scenario working end-to-end via MCP |
| FastAPI endpoints + WebSocket | 1h | CRUD + real-time approval push |

### Day 2 — Guardian + A2A + Dashboard + Demo Prep (~12h)

| Block | Hours | Deliverable |
| :--- | :---: | :--- |
| **Guardian Agent** — LangGraph + churn scoring + MCP | 2.5h | Churn prediction scenario working end-to-end via MCP |
| **Spy A2A Server (minimal)** — battle card endpoint | 1.5h | Closer calls Spy via A2A protocol live — key differentiator |
| Next.js Dashboard (Approval Queue + Deal Pipeline) | 3h | Approve/reject UI, deal cards, live WebSocket updates |
| Kafka integration (inter-agent events) | 1h | Event-driven triggers between agents |
| K8s manifests + architecture diagrams | 1h | Ready for architecture presentation (not deployed) |
| End-to-end testing (all 3 scenarios + A2A demo) | 1.5h | Full walkthrough of all mandatory scenarios |
| 3-minute pitch video + polish | 1.5h | Final demo recording + README |

---

## 4. The AI Workforce — The 4 Agents

### 4.1 The Prospector — New Customer Acquisition ★ MVP

**Role:** Tireless Business Development Representative

**Function:** Scrapes public data to find ICP-matching leads, researches company news/funding/hiring signals, drafts hyper-personalized cold outreach, manages communication until a meeting is booked.

**Triggers:** Daily cron · Kafka `spy.competitor_event` · Kafka `guardian.churn_risk` · Manual API

**MCP Servers:**

| Server | Purpose |
| :--- | :--- |
| Apollo.io MCP (community) | Contact enrichment, ICP-based lead search |
| HubSpot MCP (official) | Create contacts, companies, deals in CRM |
| SendGrid MCP (community) | Send personalized outreach, track engagement |
| Web Scraper MCP (custom) | LinkedIn pages, news, tech stack signals |
| RAG Knowledge MCP (custom) | Company docs, case studies for personalization |
| Approval Queue MCP (custom) | Queue drafted emails for human review |

**Kafka:** Publishes `prospector.lead_qualified` · Subscribes `spy.competitor_event`, `guardian.churn_risk`  
**A2A:** Calls `spy-agent.get_winback_strategy()` before win-back campaigns  
**LLM:** ICP scoring (`FAST_LLM`) · Email drafting (`COMPLEX_LLM`)

```mermaid
flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#064E3B,stroke:#34D399,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Daily Cron)):::trigger
        T2((Kafka Events)):::trigger
    end

    subgraph Agent Graph ["Prospector Agent Graph"]
        direction TB
        N1[Search Leads]:::process
        N2[Enrich Data]:::process
        N3{ICP Scoring}:::llm
        N4[Draft Outreach]:::llm
        N5{Human Approval}:::process
        N6[Send & CRM Sync]:::process
        
        N1 --> N2 --> N3
        N3 -- "Score > 0.7" --> N4
        N3 -- "Score <= 0.7" --> N_Drop((Drop)):::process
        N4 --> N5
        N5 -- "Approved" --> N6
        N5 -- "Rejected" --> N_Revise[Revise Draft]:::process --> N5
    end

    subgraph Integrations
        M1[Apollo.io MCP]:::mcp
        M2[HubSpot MCP]:::mcp
        M3[SendGrid MCP]:::mcp
        M4[Approval MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1
    N6 -.-> M2
    N6 -.-> M3
    N5 -.-> M4
    
    N6 --> O1[(Publish: lead_qualified)]:::output
```

---

### 4.2 The Closer — Active Deal Management ★ MVP

**Role:** AI Co-Pilot for the Account Executive

**Function:** Monitors all pipeline deals, detects stalled/at-risk deals, drafts contextual follow-up emails, handles objections via RAG over company docs, gets live competitive intel from The Spy.

**Triggers:** Kafka `deal.stage_changed` · Cron (daily staleness check) · Email webhook · Kafka `prospector.lead_qualified`

**MCP Servers:**

| Server | Purpose |
| :--- | :--- |
| HubSpot MCP (official) | Deal stage progression, activity timeline |
| Salesforce MCP (official, beta) | Opportunity records, SOQL pipeline queries |
| SendGrid MCP (community) | Draft and send follow-up emails |
| Calendly MCP (community) | Book follow-up meetings |
| RAG Knowledge MCP (custom) | Objection handling, case studies |
| Approval Queue MCP (custom) | Queue all outbound emails for human approval |

**Kafka:** Publishes `closer.deal_won`, `closer.deal_lost` · Subscribes `spy.competitor_event`, `prospector.lead_qualified`  
**A2A:** Calls `spy-agent.get_battlecard(competitor)` when prospect mentions a competitor  
**LLM:** Risk classification (`COMPLEX_LLM`) · Objection handling (`COMPLEX_LLM`) · Follow-up drafting (`COMPLEX_LLM`)

```mermaid
flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#172554,stroke:#3B82F6,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Stage Changed)):::trigger
        T2((Lead Qualified)):::trigger
    end

    subgraph Agent Graph ["Closer Agent Graph"]
        direction TB
        N1[Analyze Deal]:::process
        N2{Classify Risk}:::llm
        N3[Draft Follow-up]:::llm
        N4[Handle Objection]:::llm
        N5{Human Approval}:::process
        N6[Send out & Update]:::process
        
        N1 --> N2
        N2 -- "Follow-up" --> N3
        N2 -- "Objection" --> N4
        N2 -- "Healthy" --> N_Wait((Wait)):::process
        N3 & N4 --> N5
        N5 -- "Approved" --> N6
        N5 -- "Rejected" --> N_Revise[Revise]:::process --> N5
    end

    subgraph Integrations
        M1[HubSpot MCP]:::mcp
        M2[Knowledge RAG]:::mcp
        M_A2A[A2A: Spy Server]:::mcp
        M3[Approval MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1
    N4 -.-> M2
    N4 -.-> M_A2A
    N5 -.-> M3
    
    N6 --> O1[(Publish: deal_won / lost)]:::output
```

---

### 4.3 The Guardian — Customer Retention & Upselling ★ MVP

**Role:** Proactive Customer Success Manager

**Function:** Watches usage metrics and support tickets, detects churn signals, sends check-in emails, detects plan limit approach (upsell signal), drafts upgrade proposals.

**Triggers:** Kafka `usage.metric_drop` · Kafka `support.ticket_opened` · Cron (weekly health) · Kafka `closer.deal_won`

**MCP Servers:**

| Server | Purpose |
| :--- | :--- |
| Mixpanel MCP (official hosted) | Usage trends, retention, session data |
| Intercom MCP (official) | Support conversations, contact management |
| Stripe MCP (custom) | Plan quota usage %, subscription status |
| Slack MCP (official, dev) | CS channel alerts, account owner notifications |
| SendGrid MCP (community) | Check-in emails, upsell proposals |
| Approval Queue MCP (custom) | Queue all outbound communications |

**Kafka:** Publishes `guardian.churn_risk`, `guardian.upsell_opportunity` · Subscribes `closer.deal_won`  
**A2A:** Calls `spy-agent.get_competitor_usage()`  
**LLM:** Churn scoring (`FAST_LLM`) · Upsell proposals (`COMPLEX_LLM`)

```mermaid
flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#4A044E,stroke:#D946EF,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Metrics Drop)):::trigger
        T2((Health Cron)):::trigger
    end

    subgraph Agent Graph ["Guardian Agent Graph"]
        direction TB
        N1[Analyze Usage & Tickets]:::process
        N2{Score Risk/Upsell}:::llm
        N3[Draft Check-in]:::llm
        N4[Draft Proposal]:::llm
        N5{Human Approval}:::process
        N6[Send Comms]:::process
        
        N1 --> N2
        N2 -- "High Churn Risk" --> N3
        N2 -- "Upsell Trigger" --> N4
        N2 -- "Stable" --> N_Wait((Wait)):::process
        N3 & N4 --> N5
        N5 -- "Approved" --> N6
    end

    subgraph Integrations
        M1[Mixpanel MCP]:::mcp
        M2[Intercom MCP]:::mcp
        M3[Stripe MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1 & M2 & M3
    
    N6 --> O1[(Publish: churn_risk/upsell)]:::output
```

---

### 4.4 The Spy — Competitive Intelligence *(Post-MVP)*

**Role:** Strategic researcher that feeds the other three agents

**Function:** Monitors competitor websites/pricing via Playwright, detects changes using HTML diffing + LLM, updates Pinecone battle cards, broadcasts events via Kafka. **Only agent that acts as an A2A server.**

**Triggers:** Cron (hourly) · RSS feed webhooks

**MCP Servers:**

| Server | Purpose |
| :--- | :--- |
| Web Scraper MCP (custom) | Playwright-based competitor page scraping |
| RAG Knowledge MCP (custom) | Update Pinecone battle cards |
| Slack MCP (official, dev) | Broadcast alerts to #competitive channel |

**Kafka:** Publishes `spy.competitor_event`  
**A2A Exposed Skills:** `get_battlecard()` · `get_price_history()` · `get_winback_strategy()` · `get_competitor_usage()`

```mermaid
flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#0F172A,stroke:#64748B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Hourly Cron)):::trigger
        T2((A2A Request)):::trigger
    end

    subgraph Agent Graph ["Spy Agent Graph"]
        direction TB
        N1[Scrape Sites]:::process
        N2{Detect Updates}:::llm
        N3[Generate Battle Card]:::process
        N4[Respond to A2A]:::process
        
        T1 --> N1 --> N2
        N2 -- "Changes Found" --> N3
        T2 --> N4
    end

    subgraph Integrations
        M1[Scraper MCP]:::mcp
        M2[Pinecone RAG MCP]:::mcp
        M3[Slack MCP]:::mcp
    end

    N1 -.-> M1
    N3 -.-> M2
    N3 -.-> M3
    
    N3 --> O1[(Publish: competitor_event)]:::output
```

---

## 5. The Human's Role

Humans are **supervisors, not operators**. The dashboard enables:

1. **Approve emails** — every draft sits in the approval queue before sending. Enforced at LangGraph level (`interrupt_before`), MCP server level, and database level.
2. **Take over complex negotiations** — step into live conversations with full context and battle card data.
3. **Review the audit trail** — every agent decision logged with full reasoning chain.
4. **Configure agent parameters** — ICP criteria, follow-up timing, churn thresholds, competitor watchlist.
5. **Override and correct** — edit drafts before approving; corrections fed back into agent memory.

---

## 6. High-Level Architecture

```mermaid
flowchart TD
    %% Node Styles
    classDef react fill:#000,stroke:#38BDF8,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef fastapi fill:#000,stroke:#10B981,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef orc fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef closer fill:#172554,stroke:#3B82F6,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef prospect fill:#064E3B,stroke:#34D399,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef guard fill:#4A044E,stroke:#D946EF,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef db fill:#022C22,stroke:#059669,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef stream fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef trace fill:#172554,stroke:#60A5FA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Frontend ["Frontend & Auth"]
        UI["⚛️ Web UI (Stitch SPA)"]:::react --> GW["⚡ FastAPI Gateway"]:::fastapi
    end

    subgraph Pipeline ["OmniSales Agentic Pipeline"]
        direction TB
        ORC["🧠 Orchestrator Agent<br/>(Supervisor • Scheduler • Chat)"]:::orc
        
        subgraph SubAgents ["Async Subagent Layer"]
            direction LR
            CL["🎯 Closer Agent<br/>(Deals & Objections)"]:::closer
            PR["🔍 Prospector Agent<br/>(Leads & ICP Scoring)"]:::prospect
            GR["🛡️ Guardian Agent<br/>(Accounts & Churn Risk)"]:::guard
        end
        
        ORC -- "Async Dispatch" --> CL
        ORC -- "Async Dispatch" --> PR
        ORC -- "Async Dispatch" --> GR
    end

    subgraph Protocols ["Model Context Protocol (MCP) Tools"]
        direction LR
        CRM["💾 CRM Server<br/>(NeonDB Bridge)"]:::mcp
        KNW["📚 Knowledge Server<br/>(Playbooks & FAQs)"]:::mcp
        APP["✅ Approvals Server<br/>(Human-in-the-Loop)"]:::mcp
        SPY["🕵️ Spy Server<br/>(A2A Intel)"]:::mcp
    end

    subgraph Infra ["Infrastructure"]
        direction LR
        NEON["🐘 Neon PostgreSQL<br/>(State, RLS & Reports)"]:::db
        KAFKA["🚂 Kafka<br/>(Event Bus)"]:::stream
        GROQ["🚀 Groq API<br/>(Llama 3 70B & 8B)"]:::llm
        PCONE["🌲 Pinecone<br/>(MRL Vectors)"]:::db
        LSMITH["🦜 LangSmith<br/>(LLM Tracing)"]:::trace
    end

    %% Connections
    GW -->|REST/HTTP| ORC
    GW -->|Status/Approvals| SubAgents
    
    SubAgents -.->|Tool Calls| Protocols
    ORC -.->|CRM Scan| CRM
    
    CRM == "SQL" ==> NEON
    KNW == "Embeddings" ==> PCONE
    SubAgents -.->|Pub/Sub| KAFKA
    
    %% Implicit universal connections to LLM/Tracing without cluttering the graph
    ORC -.- GROQ
    SubAgents -.- GROQ
```

### The Three Protocol Axes

| Protocol | Direction | Purpose |
| :--- | :--- | :--- |
| **MCP** | Vertical (agent → tool) | Agent connects down to external services |
| **A2A** | Horizontal (agent ↔ agent) | Direct peer-to-peer agent calls (sync) |
| **Kafka** | Async broadcast | One-to-many event signals between agents |

---

## 7. Technology Stack

| Layer | Technology | Why This Choice |
| :--- | :--- | :--- |
| **Agent Orchestration** | LangGraph 0.2+ | Native cyclic graphs, interrupt/resume for HITL, state checkpointing |
| **Backend API** | FastAPI + Python 3.12 | Async-first, Pydantic validation, perfect for LLM I/O |
| **LLM — Complex** | Groq `llama-3.3-70b-versatile` | Risk classification, objection handling, email drafting |
| **LLM — Simple** | Groq `llama-3.1-8b-instant` | ICP scoring, status checks, data extraction |
| **Message Queue** | Apache Kafka | Durable event log, A2A async comms, full replay audit |
| **Primary Database** | PostgreSQL 16 | ACID, RLS for multi-tenancy, JSONB |
| **Vector Store** | Pinecone | Semantic search for RAG (company docs, battle cards) |
| **Caching / State** | Redis Cluster | Agent state, rate limiting, pub/sub for real-time UI |
| **Analytics** | ClickHouse | Columnar OLAP for pipeline metrics |
| **Frontend** | Next.js 14 (App Router) | React Server Components, WebSocket integration |
| **Container Orch.** | Kubernetes (GKE) | KEDA autoscaling, namespace isolation |
| **Agent Scaling** | KEDA | Scale pods on Kafka consumer lag — the right signal for async agents |
| **Service Mesh** | Istio | mTLS, traffic management, distributed tracing |
| **Observability** | Datadog + LangSmith | APM + LLM tracing, token costs, decision audit |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps, declarative K8s deployments |
| **Secrets** | HashiCorp Vault | Dynamic secret injection, API key rotation |
| **A2A Protocol** | A2A (Google → Linux Foundation) | Peer-to-peer agent comms, Agent Cards, native LangGraph integration |

### 7.1 LLM Strategy: Groq Multi-Key Rotation

```python
# shared/llm.py
from langchain_groq import ChatGroq

COMPLEX_LLM = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=4096)
FAST_LLM = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, max_tokens=1024)
```

**Multi-Key Rotation:** Array of Groq API keys in Vault. Round-Robin/LRU selection. On `429 Too Many Requests`, middleware retries with next key instantly.

### 7.2 Why LangGraph over Google ADK

1. **GCP lock-in** — ADK is GCP-optimized; OmniSales needs cloud-agnostic deployment.
2. **Production maturity** — LangGraph has years of battle-testing vs. ADK's experimental state.
3. **Control** — ADK hides workflow logic behind abstractions. In OmniSales, precise deal routing control *is* the product.

### 7.3 Why Not ACP

ACP (IBM BeeAI) merged into A2A under the Linux Foundation (Sept 2025). No longer under active independent development. Use **A2A** — it is the direct successor with 100+ enterprise partners.

---

## 8. Agent Framework — LangGraph

### 8.1 Shared Agent State Schema

```python
# shared/state.py
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages:    Annotated[Sequence[BaseMessage], add_messages]
    lead_id:     str | None
    deal_id:     str | None
    account_id:  str | None
    action:      str          # current action being planned
    draft:       str | None   # email/proposal draft awaiting approval
    approval:    str | None   # "approved" | "rejected" | "pending"
    reasoning:   list[str]    # audit trail — why each decision was made
    metadata:    dict         # agent-specific payload
```

### 8.2 The Closer — Full Graph Implementation

```python
# agents/closer/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from .nodes import (
    analyze_deal, classify_risk, draft_followup,
    handle_objection, await_human_approval, send_email
)

def build_closer_graph(tools: list, checkpointer: PostgresSaver):
    graph = StateGraph(AgentState)
    graph.add_node("analyze",   analyze_deal)
    graph.add_node("classify",  classify_risk)
    graph.add_node("draft",     draft_followup)
    graph.add_node("objection", handle_objection)
    graph.add_node("human",     await_human_approval)  # ← INTERRUPT POINT
    graph.add_node("send",      send_email)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "classify")
    graph.add_conditional_edges("classify", lambda s: s["action"], {
        "follow_up": "draft", "objection": "objection", "no_action": END,
    })
    graph.add_edge("draft",     "human")
    graph.add_edge("objection", "human")
    graph.add_conditional_edges("human", lambda s: s["approval"], {
        "approved": "send", "rejected": END,
    })
    graph.add_edge("send", END)

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human"]  # ← PAUSE FOR HUMAN REVIEW
    )
```

**Key Pattern — HITL:** `interrupt_before=["human"]` pauses the graph and serializes state to PostgreSQL. The dashboard reads pending state, shows the draft. On approval, the graph resumes exactly where it stopped.

### 8.3 Connecting to MCP Servers Inside a Graph

```python
# agents/closer/graph.py
from langchain_mcp_adapters.client import MultiServerMCPClient

async def run_closer(deal_id: str, org_id: str):
    async with MultiServerMCPClient({
        "crm":       {"url": "http://mcp-hubspot-service:8001/mcp",   "transport": "http"},
        "email":     {"url": "http://mcp-sendgrid-service:8002/mcp",  "transport": "http"},
        "knowledge": {"url": "http://mcp-knowledge-service:8003/mcp", "transport": "http"},
        "approvals": {"url": "http://mcp-approvals-service:8004/mcp", "transport": "http"},
    }) as client:
        tools = await client.get_tools()  # auto-discovers tools at runtime
        graph = build_closer_graph(tools, checkpointer)
        result = await graph.ainvoke({"deal_id": deal_id, "org_id": org_id, "reasoning": []})
```

> **Always use `transport: "http"` in Kubernetes.** stdio is for local desktop apps. In K8s, every MCP server is a ClusterIP service.

---

## 9. MCP — Model Context Protocol Integration

### 9.1 Architecture Philosophy

Each external service is accessed through an MCP server. Agents connect only to the servers they need, discover tools at runtime. Benefits:
- Swap SendGrid for Postmark → update one MCP server, zero agent changes
- Rate limit at MCP server level, agents stay clean
- Enterprise clients extend without forking agent code
- Every tool call logged centrally for compliance

### 9.2 Existing MCP Servers (Use Directly)

| Service | Type | Key Tools | Used By |
| :--- | :--- | :--- | :--- |
| HubSpot | Official | 114 tools, OAuth 2.0, CRM read/write | Prospector, Closer |
| Salesforce | Official (beta) | SOQL queries, opportunity CRUD | Closer |
| Mixpanel | Official hosted | NL queries on analytics data | Guardian |
| Intercom | Official | Conversations, contacts (6 tools) | Guardian |
| SendGrid | Community | Email send, templates, stats | Prospector, Closer, Guardian |
| Apollo.io | Community | Contact enrichment, lead search | Prospector |
| Calendly | Community | Scheduling, booking links | Closer |
| Slack | Official (dev) | Channel posts, user lookups | Guardian, Spy |

### 9.3 Custom MCP Servers — Must Build (Only 3)

**1. Web Scraper MCP** — Playwright-based, isolated K8s pod:

```python
# mcp-servers/scraper/server.py
from fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("web-scraper")

@mcp.tool()
async def scrape_page(url: str, selector: str = "body") -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        text = await page.inner_text(selector)
        return {"text": text, "hash": hashlib.sha256(text.encode()).hexdigest(), "url": url}

@mcp.tool()
async def detect_changes(old_text: str, new_text: str) -> dict:
    diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), lineterm=""))
    return {"changed": len(diff) > 0, "diff_lines": diff[:50]}
```

**2. Approval Queue MCP** — Backs the LangGraph interrupt/resume pattern:

```python
# mcp-servers/approvals/server.py
from fastmcp import FastMCP
mcp = FastMCP("approvals")

@mcp.tool()
async def queue_for_approval(org_id: str, agent: str, draft: str, reasoning: str, thread_id: str) -> dict:
    task_id = await db.create_task(org_id=org_id, agent=agent, draft=draft,
                                    reasoning=reasoning, thread_id=thread_id, status="pending_approval")
    await ws_manager.broadcast(org_id, {"event": "new_approval", "task_id": task_id})
    return {"task_id": task_id, "status": "pending"}

@mcp.tool()
async def get_approval_status(task_id: str) -> dict:
    return await db.get_task_status(task_id)
```

**3. Stripe Billing MCP** — Plan quota data for Guardian upsell detection:

```python
# mcp-servers/stripe/server.py
import stripe
from fastmcp import FastMCP
mcp = FastMCP("stripe-billing")

@mcp.tool()
async def get_plan_usage(customer_id: str) -> dict:
    subscription = stripe.Subscription.retrieve(customer_id)
    usage = sum(r.total_usage for r in stripe.SubscriptionItem.list_usage_record_summaries(
        subscription.items.data[0].id).data)
    limit = int(subscription.items.data[0].price.metadata.get("quota_limit", 1000))
    return {"plan": subscription.items.data[0].price.nickname,
            "usage_pct": round((usage / limit) * 100, 1),
            "upsell_signal": usage / limit > 0.8}
```

### 9.4 MCP Gateway

In production, use an MCP gateway (e.g. Bifrost) for: centralized auth, per-agent rate limiting, kill switches, OPA policy-as-code, observability, and multi-tenant scoping.

---

## 10. Agent-to-Agent Communication

### 10.1 Three-Layer Model

```
MCP   → Vertical:   Agent talks DOWN to external tools
A2A   → Horizontal: Agent talks ACROSS to other agents (sync)
Kafka → Async:      Agent BROADCASTS signals to all listeners
```

**A2A** = direct phone call (ring a colleague, get an answer).  
**Kafka** = company-wide announcements (broadcast, anyone who cares picks it up).  
**MCP** = the toolbox each person uses for their job.

### 10.2 The Spy as A2A Server

The Spy is the **only A2A server** — it holds intelligence other agents need on demand.

**Agent Card** (`/.well-known/agent.json`):
```json
{
  "name": "spy-agent",
  "url": "https://spy-agent.omnisales-agents.svc:8080",
  "skills": [
    {"id": "get_battlecard", "description": "Latest competitive intelligence"},
    {"id": "get_price_history", "description": "Competitor pricing over time"},
    {"id": "get_winback_strategy", "description": "Win-back messaging and offers"},
    {"id": "get_competitor_usage", "description": "Why a customer may be switching"}
  ],
  "authentication": {"schemes": ["Bearer"]}
}
```

**Closer calling Spy mid-deal:**
```python
from a2a.client import A2AClient
spy_client = A2AClient(base_url="http://spy-agent.omnisales-agents.svc:8080")

async def handle_objection(state: AgentState) -> AgentState:
    competitor = extract_competitor_from_thread(state["messages"])
    if competitor:
        task = await spy_client.send_task({
            "skill_id": "get_battlecard",
            "input": {"competitor": competitor, "deal_stage": state["metadata"]["stage"]}
        })
        state["metadata"]["battlecard"] = task.result["battlecard"]
        state["reasoning"].append(f"Fetched {competitor} battlecard via A2A")
    return state
```

### 10.3 Kafka Topics — Full Reference

| Topic | Publisher | Subscribers | Payload |
| :--- | :--- | :--- | :--- |
| `spy.competitor_event` | Spy | Prospector, Closer | competitor, event_type, prices, timestamp |
| `prospector.lead_qualified` | Prospector | Closer | lead_id, icp_score, company, contact |
| `guardian.churn_risk` | Guardian | Prospector | account_id, churn_risk, reason, competitor |
| `guardian.upsell_opportunity` | Guardian | Closer | account_id, current_plan, usage_pct |
| `closer.deal_won` | Closer | Guardian | account_id, deal_id, arr |
| `closer.deal_lost` | Closer | — | deal_id, reason |

### 10.4 Per-Agent Communication Map

| Agent | Publishes (Kafka) | Subscribes (Kafka) | Calls (A2A) | Exposes (A2A) |
| :--- | :--- | :--- | :--- | :--- |
| Prospector | `lead_qualified` | `spy.competitor_event`, `guardian.churn_risk` | spy: `get_winback_strategy` | — |
| Closer | `deal_won`, `deal_lost` | `spy.competitor_event`, `prospector.lead_qualified` | spy: `get_battlecard` | — |
| Guardian | `churn_risk`, `upsell_opportunity` | `closer.deal_won` | spy: `get_competitor_usage` | — |
| Spy | `competitor_event` | — | — | 4 skills |

---

## 11. Data Architecture

### 11.1 PostgreSQL Core Schema

```sql
CREATE TABLE leads (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id       UUID NOT NULL,
    company      TEXT,
    contact_name TEXT,
    email        TEXT UNIQUE,
    icp_score    FLOAT,                   -- 0–1, set by Prospector LLM
    status       TEXT,                    -- new|contacted|replied|booked|dead
    source       TEXT,                    -- prospector|manual|inbound
    enrichment   JSONB,                   -- raw Clearbit/Apollo data
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE deals (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id         UUID NOT NULL,
    lead_id        UUID REFERENCES leads(id),
    stage          TEXT,                  -- discovery|proposal|negotiation|closed
    arr            NUMERIC,
    risk_level     TEXT,                  -- healthy|at_risk|stalled
    last_activity  TIMESTAMPTZ,
    closer_thread  JSONB,                 -- full conversation history for LLM context
    agent_log      JSONB[]               -- immutable audit trail
);

CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    company         TEXT,
    arr             NUMERIC,
    plan            TEXT,
    health_score    FLOAT,                -- 0–1, updated by Guardian
    churn_risk      FLOAT,               -- 0–1, updated by Guardian
    stripe_customer TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL,
    agent_name  TEXT,                     -- prospector|closer|guardian|spy
    status      TEXT,                     -- pending_approval|approved|rejected|sent
    draft       TEXT,
    reasoning   TEXT,
    thread_id   TEXT,                     -- LangGraph checkpoint thread ID
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE competitors (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL,
    name          TEXT,
    website       TEXT,
    last_scraped  TIMESTAMPTZ,
    pricing_hash  TEXT,
    data          JSONB
);

CREATE TABLE scan_reports (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_type     TEXT NOT NULL,
    status        TEXT NOT NULL,
    records_found INTEGER DEFAULT 0,
    actions_taken INTEGER DEFAULT 0,
    llm_summary   TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    completed_at  TIMESTAMPTZ
);

-- Row-Level Security — enforced at database driver level
ALTER TABLE leads       ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals       ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts    ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON leads
    USING (org_id = current_setting('app.current_org_id')::UUID);
-- (same policy applied to all tables)
```

### 11.2 Vector Store — Pinecone RAG Pipeline

```python
import os
from pinecone import Pinecone

def ingest_company_docs(org_id: str, docs: list[dict]):
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    index = pc.Index(host=os.environ.get("PINECONE_HOST"))
    
    # Using Pinecone Native Integrated Inference
    index.upsert_records(
        namespace=f"org-{org_id}",  # per-org namespace for isolation
        records=[
            {
                "_id": doc["id"],
                "text": str(doc["content"]),
                "metadata": doc["metadata"]
            }
            for doc in docs
        ]
    )
```

**Content stored:** Product docs (objection handling) · Case studies (personalization) · Pre-approved responses · Competitor battle cards · Historical email templates

### 11.3 Redis Usage

| Use | Details |
| :--- | :--- |
| Agent state cache | Ephemeral in-flight state, TTL-based cleanup |
| API rate limiting | Per-org, per-endpoint sliding window |
| WebSocket pub/sub | Real-time approval queue updates to dashboard |

### 11.4 ClickHouse Analytics

Pipeline health metrics · Agent performance (emails, reply rates, meetings) · LLM token usage/cost per org · Competitor event tracking · Churn prediction accuracy

---

## 12. Specialized Agent Skills

Skills are focused prompt engineering packages — each tuned for a specific agent sub-task. All use structured output (JSON) for LangGraph routing.

| Skill | Agent | Model | Purpose |
| :--- | :--- | :--- | :--- |
| **ICP Scoring** | Prospector | `FAST_LLM` | Score leads 0–1 against Ideal Customer Profile |
| **Personalized Outreach** | Prospector | `COMPLEX_LLM` | Hyper-personalized cold emails using company news + signals |
| **Deal Risk Classifier** | Closer | `FAST_LLM` | Classify deals as healthy/at_risk/stalled for graph routing |
| **Objection Handling** | Closer | `COMPLEX_LLM` | RAG-powered grounded responses with source citations |
| **Churn Signal Scorer** | Guardian | `FAST_LLM` | Score churn risk 0–1 from usage drops + ticket sentiment |
| **Competitive Change Detector** | Spy | `FAST_LLM` | HTML diff + LLM interpretation of competitor changes |

### Example: ICP Scoring Skill

```python
# skills/icp_scoring.py
ICP_SCORING_PROMPT = """
You are an expert B2B sales analyst. Score this company against our ICP.
Return ONLY valid JSON.

ICP Criteria: {icp_criteria}
Company Data: {enrichment_data}

Return: {
  "score": 0.0-1.0,
  "tier": "A|B|C|D",
  "matched_signals": ["series B funded", "50-200 engineers"],
  "disqualifiers": ["too small", "wrong industry"],
  "recommended_action": "pursue|deprioritize|disqualify"
}
"""
```

---

## 13. API Endpoints

### 13.1 Closer Agent API (MVP)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/deals` | List all deals with risk classification |
| `GET` | `/api/deals/{deal_id}` | Deal details + agent audit trail |
| `POST` | `/api/deals/{deal_id}/trigger` | Manually trigger Closer agent |
| `GET` | `/api/tasks/pending` | Tasks awaiting human approval |
| `POST` | `/api/tasks/{task_id}/approve` | Approve an agent-drafted action |
| `POST` | `/api/tasks/{task_id}/reject` | Reject with optional feedback |
| `WS` | `/ws/live` | WebSocket for real-time approval events |

### 13.2 Orchestrator API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/orchestrator/chat` | Stateless chat endpoint for Orchestrator to query scan histories |
| `GET` | `/api/orchestrator/history` | Orchestrator workflow history |

### 13.3 General API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | JWT login |
| `POST` | `/api/docs/ingest` | Upload company docs for RAG |
| `GET` | `/api/agents/status` | Health/status of running agents |
| `GET` | `/api/audit/{agent_name}` | Audit trail logs per agent |
---

## 14. Next.js Dashboard

The human-in-the-loop control plane:

1. **Approval Queue** — Card-based UI with deal context, risk badge, draft content, reasoning, Approve/Reject buttons
2. **Deal Pipeline** — Kanban view across stages, color-coded by risk level
3. **Agent Timeline** — Per-deal chronological log of every agent action and LLM reasoning trace
4. **Live Activity Feed** — WebSocket-powered real-time stream of agent events

---

## 15. Containerization with Docker

### 15.1 Repository Structure

```
omnisales/
├── agents/
│   ├── prospector/          ← LangGraph agent + Dockerfile
│   ├── closer/              ★ MVP
│   ├── guardian/
│   └── spy/                 ← also runs A2A server on :8080
├── mcp-servers/
│   ├── scraper/             ← Playwright, own Dockerfile
│   ├── approvals/
│   └── stripe/
├── api-gateway/             ← FastAPI, JWT, rate limiting
├── dashboard/               ← Next.js frontend
├── shared/                  ← shared Python lib (state, kafka, auth, db)
├── k8s/                     ← all Kubernetes manifests
├── docker-compose.yml       ← local dev only
└── .github/workflows/
```

### 15.2 Agent Dockerfile (Multi-Stage)

```dockerfile
# agents/closer/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY ../../shared /app/shared
COPY . /app/agent
RUN adduser --disabled-password --uid 1001 agent
USER 1001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8080/health || exit 1
CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 15.3 Scraper Dockerfile (Playwright)

```dockerfile
FROM mcr.microsoft.com/playwright/python:1.48.0-jammy
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN playwright install chromium --with-deps
RUN adduser --disabled-password --uid 1002 scraper
USER 1002
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 15.4 Dashboard Dockerfile (Next.js, 3-Stage)

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json .
RUN npm ci --only=production

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
RUN adduser -D -u 1001 nextjs
COPY --from=builder /app/.next/standalone .
COPY --from=builder /app/public ./public
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

### 15.5 Image Size Targets

| Container | Base | Target Size |
| :--- | :--- | :--- |
| Agent (×4) | python:3.12-slim | ~180 MB |
| MCP Scraper | playwright/python | ~1.4 GB |
| API Gateway | python:3.12-slim | ~140 MB |
| Dashboard | node:20-alpine | ~110 MB |

### 15.6 Docker Compose — Local Development

```yaml
version: '3.9'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: omnisales
      POSTGRES_USER: omnisales
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
    volumes: ["pgdata:/var/lib/postgresql/data"]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.0
    environment: { ZOOKEEPER_CLIENT_PORT: 2181 }

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    depends_on: [zookeeper]

  mcp-approvals:
    build: ./mcp-servers/approvals
    ports: ["8002:8002"]
    environment:
      DATABASE_URL: postgresql://omnisales:${POSTGRES_PASSWORD}@postgres/omnisales
    depends_on: [postgres]

  mcp-scraper:
    build: ./mcp-servers/scraper
    ports: ["8001:8001"]
    shm_size: '2gb'

  agent-closer:
    build: ./agents/closer
    ports: ["9002:8080"]
    environment:
      GROQ_API_KEY: "${GROQ_API_KEY}"
      KAFKA_BROKERS: kafka:9092
      DATABASE_URL: postgresql://omnisales:${POSTGRES_PASSWORD}@postgres/omnisales
      SPY_A2A_URL: http://agent-spy:8080
    depends_on: [kafka, postgres]

  api-gateway:
    build: ./api-gateway
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://omnisales:${POSTGRES_PASSWORD}@postgres/omnisales
      REDIS_URL: redis://redis:6379

  dashboard:
    build: ./dashboard
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://api-gateway:8000

volumes:
  pgdata:
```

---

## 16. Kubernetes Orchestration & Scaling

### 16.1 Namespace Strategy

| Namespace | Contents | Network Access |
| :--- | :--- | :--- |
| `omnisales-agents` | 4 agent pods | → omnisales-mcp, Kafka, Vault only |
| `omnisales-mcp` | MCP server pods | → External APIs (via egress policy) |
| `omnisales-gateway` | API gateway, dashboard | → omnisales-agents, internet |
| `omnisales-data` | Managed DB/Redis access | — |

### 16.2 Agent Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-closer
  namespace: omnisales-agents
spec:
  replicas: 2
  selector:
    matchLabels: {app: agent-closer}
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/agent-inject-secret-llm: "secret/omnisales/llm-keys"
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
      containers:
        - name: closer
          image: gcr.io/omnisales/agent-closer:"{{ .Values.tag }}"
          ports: [{containerPort: 8080}]
          resources:
            requests: { memory: "512Mi", cpu: "250m" }
            limits:   { memory: "1Gi",   cpu: "1" }
          livenessProbe:
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 30
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
            initialDelaySeconds: 10
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: agent-closer-pdb
  namespace: omnisales-agents
spec:
  minAvailable: 1
  selector:
    matchLabels: { app: agent-closer }
```

### 16.3 KEDA Autoscaling

Standard HPA scales on CPU — wrong signal for I/O-bound LLM agents. KEDA scales on Kafka consumer lag.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: closer-scaler
  namespace: omnisales-agents
spec:
  scaleTargetRef: { name: agent-closer }
  minReplicaCount: 2
  maxReplicaCount: 10
  cooldownPeriod: 60
  pollingInterval: 15
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka-broker:9092
        consumerGroup: closer-consumer-group
        topic: closer.tasks
        lagThreshold: "20"
```

### 16.4 Replica Scaling Reference

| Workload | Min | Max | Scale Trigger |
| :--- | :--- | :--- | :--- |
| Closer ★ | 2 | 10 | Kafka lag: `closer.tasks` (20) |
| Prospector | 1 | 12 | Kafka lag: `prospector.tasks` (30) |
| Guardian | 1 | 8 | Kafka lag: `guardian.tasks` (25) |
| Spy | 0 | 5 | Kafka lag + hourly cron |
| MCP Scraper | 1 | 5 | Kafka lag: `scraper.tasks` (10) |
| API Gateway | 2 | 8 | HPA CPU ≥ 70% |
| Dashboard | 2 | 4 | HPA CPU ≥ 80% |

### 16.5 Istio mTLS

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: omnisales-agents
spec:
  mtls:
    mode: STRICT
```

---

## 17. CI/CD Pipeline

### GitHub Actions + ArgoCD GitOps

```yaml
name: Build and Deploy
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r agents/closer/requirements.txt
      - run: pytest agents/ mcp-servers/ --mock-llm

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        service: [agents/closer, agents/prospector, agents/spy, agents/guardian,
                  mcp-servers/scraper, mcp-servers/approvals, mcp-servers/stripe,
                  api-gateway, dashboard]
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with: { credentials_json: "${{ secrets.GCP_SA_KEY }}" }
      - run: |
          docker build -t gcr.io/omnisales/${{ matrix.service }}:${{ github.sha }} ./${{ matrix.service }}
          docker push gcr.io/omnisales/${{ matrix.service }}:${{ github.sha }}

  deploy:
    needs: build
    steps:
      - run: sed -i 's/tag: .*/tag: "${{ github.sha }}"/' k8s/agents/*/values.yaml
      - run: git add k8s/ && git commit -m "ci: update tags" && git push
      # ArgoCD auto-syncs the cluster
```

**Strategy:** Rolling updates (25% surge) · PodDisruptionBudgets · Readiness gates · `kubectl rollout undo` for rollback

---

## 18. Security & Compliance

| Concern | Solution | Implementation |
| :--- | :--- | :--- |
| **Multi-Tenancy** | PostgreSQL RLS + Namespaces | `org_id` on every table, RLS policies, K8s namespace isolation |
| **Secret Management** | HashiCorp Vault | Vault sidecar injects secrets at pod startup; keys rotated weekly |
| **Service-to-Service** | Istio mTLS (STRICT) | All inter-pod traffic encrypted; zero-trust |
| **Prompt Injection** | Input Sanitization | Strip HTML/special chars; system prompts hardened with refusal conditioning |
| **Email Sending** | Human Approval Gate | No email without `approval = "approved"` — enforced at graph + gateway + DB level |
| **Audit Trail** | Immutable `agent_log` JSONB | Every node execution logged with timestamp, reasoning, token usage |
| **Container Security** | Non-root users | All containers UID 1001/1002; read-only root FS where possible |
| **API Security** | JWT + rate limiting | Per-org rate limits enforced at gateway |
| **Image Security** | Trivy scanning in CI | CVE scan before push; critical CVEs block deployment |
| **Data Residency** | GCP regional clusters | EU → europe-west1, US → us-central1; Kafka topics geo-fenced |
| **SOC 2 Readiness** | Datadog Compliance | All API calls logged, RBAC via GCP IAM, data access audited |

### Vault Secret Injection Pattern

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-inject-secret-llm: "secret/omnisales/llm-keys"
  vault.hashicorp.com/agent-inject-template-llm: |
    {{- with secret "secret/omnisales/llm-keys" -}}
    export GROQ_API_KEY="{{ .Data.data.groq_pool }}"
    {{- end -}}
```

Secrets are **never baked into images**, **never in plaintext K8s Secrets**, **rotated automatically**, and **every access is audited**.

---

## 19. Observability

### Three-Layer Stack

| Layer | Tool | Coverage |
| :--- | :--- | :--- |
| Infrastructure + APM | Datadog | Pod health, CPU/memory, API latency, error rates |
| LLM tracing | LangSmith | Token usage, LLM latency, decision traces, prompt versions |
| Alerting | PagerDuty | Agent failures, approval queue buildup, churn spikes |

### Key Metrics

**Agent:** Emails sent/day · Approval rate · Reply rate · Meetings booked · Deals progressed  
**System:** Kafka consumer lag · LLM p50/p95/p99 latency · Token cost/org/day · MCP tool latency · Approval queue backlog (alert >50)  
**Business:** Pipeline conversion · Churn detection lead time · Upsell conversion · ICP score accuracy

---

## 20. Error Handling & Resilience

| Failure Mode | Strategy |
| :--- | :--- |
| **LLM rate limit (429)** | Multi-key rotation — retry with next Groq key (Round-Robin) |
| **LLM timeout / error** | Exponential backoff (3 retries), fallback to `FAST_LLM` if `COMPLEX_LLM` fails |
| **Kafka consumer crash** | Consumer group auto-rebalance; messages retained for replay |
| **Database unavailable** | Circuit breaker; agent pauses and retries on reconnect |
| **Pinecone unavailable** | Graceful degradation — proceed without RAG, flag in reasoning |
| **Invalid LLM output** | Pydantic parsing with retry; `with_structured_output()` enforcement |
| **Human approval timeout** | Configurable TTL (24h default); auto-escalation notification |
| **MCP server down** | Health checks + circuit breaker; agent skips tool and logs gap |

---

## 21. Demo Scenarios (Track 4 Mandatory Walkthrough)

Each demo demonstrates **5+ autonomous steps** with error recovery and HITL approval gates.

### Scenario 1: Deal Risk Alert (Closer Agent)

> A deal goes silent for 10 days after a pricing discussion. The Closer detects the risk, generates a re-engagement strategy, and sends a follow-up on human approval.

1. **Detect:** Cron identifies Deal #4821 (Acme Corp, $120K ARR, Negotiation stage) — 10 days silent after pricing email
2. **Load Context:** Closer pulls full deal record + email thread from Postgres
3. **Classify Risk:** `COMPLEX_LLM` classifies as `at_risk` with reasoning: *"10-day silence post-pricing. Competitor AcmeCRM mentioned in last reply."*
4. **Check Competitor Engagement:** Agent detects competitor mention → queries Pinecone for AcmeCRM battle cards
5. **RAG Retrieval:** Pulls 3 relevant chunks: pricing comparison, feature differentiators, customer success case study
6. **Draft Re-engagement:** LLM drafts personalized email addressing competitor concern with specific value props and a Calendly meeting link
7. **HITL Pause:** Graph hits `interrupt_before=["human"]` → state serialized to PostgreSQL → WebSocket push to dashboard
8. **Human Approval:** Sales manager reviews draft, edits one sentence, clicks **Approve**
9. **Send + Log:** Graph resumes → email sent via SendGrid → full decision chain logged to `agent_log`

**Error recovery shown:** If Pinecone is unreachable, agent proceeds without RAG context and flags the gap in reasoning. If SendGrid fails, exponential backoff with 3 retries.

### Scenario 2: Cold Outreach Sequence (Prospector Agent)

> Given a target account profile, the Prospector researches the company, identifies 2 decision-makers, and drafts personalized 3-email sequences for each.

1. **Receive Target:** API trigger with company profile: *"Series B SaaS, 150 employees, Fintech vertical, using Salesforce"*
2. **Research & Enrich:** Agent queries enrichment data (Apollo.io/simulated), pulls company news, funding round, tech stack
3. **ICP Score:** `FAST_LLM` scores the lead 0.87 (Tier A) — *"Strong ICP match: right size, right vertical, recent funding"*
4. **Identify Decision-Makers:** Agent identifies VP Sales and CRO from enrichment data, noting different roles/priorities
5. **Draft Sequence (VP Sales):** `COMPLEX_LLM` drafts 3-email sequence tailored to VP Sales priorities (pipeline visibility, rep productivity)
6. **Draft Sequence (CRO):** `COMPLEX_LLM` drafts different 3-email sequence for CRO (revenue forecasting, board reporting)
7. **HITL Pause:** Both sequences queued for human approval with reasoning for each personalization choice
8. **Human Approval:** Manager reviews, approves VP Sales sequence, edits CRO sequence tone, approves
9. **Queue for Sending:** Approved sequences scheduled via SendGrid with engagement tracking

**Branching shown:** If ICP score < 0.5, agent deprioritizes and logs reasoning instead of drafting outreach.

### Scenario 3: Churn Prediction (Guardian Agent)

> Given usage and support data for 20 accounts, the Guardian flags the 3 highest churn risks with tailored retention plays.

1. **Analyze Dataset:** Guardian loads all 20 accounts from Postgres — usage metrics, support tickets, login frequency, plan utilization
2. **Score Churn Risk:** `FAST_LLM` scores each account 0–1 based on multi-signal analysis (usage drop %, ticket sentiment, login gaps)
3. **Rank & Flag Top 3:** Agent ranks all 20 accounts, flags top 3:
   - Account A (0.91): *"Usage dropped 45% in 30 days, 3 unresolved support tickets, competitor mentioned in ticket"*
   - Account B (0.84): *"No login in 21 days, plan utilization at 12%, billing payment delayed"*
   - Account C (0.78): *"Key user churned (left company), usage concentrated on this user"*
4. **Generate Tailored Retention Plays:** `COMPLEX_LLM` generates **specific** plays per account (not generic templates):
   - Account A: Executive check-in call + competitive feature comparison doc
   - Account B: Re-engagement email with product tour invite + usage tips
   - Account C: Onboard replacement user + expand seat allocation offer
5. **HITL Pause:** All 3 retention plays queued for CS manager approval with full reasoning
6. **Execute:** On approval, emails sent and tasks created in CRM

**Error recovery shown:** If usage data is incomplete for an account, agent flags data gap and scores based on available signals only.

---

## 22. Detailed Financial & Impact Model

> *"Can the team show the math on business value?"* — Evaluation Rubric (10%)

To accurately measure the impact of the OmniSales Multi-Agent Architecture, we must model a **Traditional B2B Sales Department** against an **OmniSales Augmented Department** over a 12-month fiscal year. 

### Baseline Assumptions

- **Average Contract Value (ACV):** $40,000
- **Sales Cycle:** 60 - 90 days
- **Productivity Limit (Human):** 1 SDR can heavily personalize 50 outbound emails/calls per day. 1 AE can maximally handle 2 meetings/day while managing their existing pipeline, follow-ups, and admin work in Salesforce.
- **Productivity Limit (Agent):** The Prospector Agent is bound only by domain reputation limits (assumed 500 emails/day to avoid spam filters), not hours worked.

---

### Scenario A: Traditional Sales Department

Our baseline is a standard mid-market SaaS sales motion heavily reliant on manual human labor for both pipeline generation and deal closing.

#### 1. Operational Costs (Annual)

*The traditional model relies heavily on human capital and per-seat software licenses. Here is the mathematical breakdown of annual operational expenses:*

| Expense Category | Unit / Role | Quantity | Annual Cost per Unit | Total Annual Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Headcount** | Account Executive (AE) | 10 | $150,000 (OTE) | $1,500,000 |
| **Headcount** | Sales Dev. Rep (SDR) | 5 | $80,000 (OTE) | $400,000 |
| **Headcount** | Sales Manager | 1 | $180,000 (OTE) | $180,000 |
| *Subtotal: Headcount* | | *16 FTEs* | | *$2,080,000* |
| **Software Stack** | CRM (e.g. Salesforce) | 16 seats | $1,800 / user | $28,800 |
| **Software Stack** | Sales Engagement (Apollo/Outreach) | 16 seats | $1,200 / user | $19,200 |
| **Software Stack** | LinkedIn Sales Navigator | 16 seats | $1,200 / user | $19,200 |
| **Data Enrichment** | B2B Contact Database (ZoomInfo) | 1 Org | $25,000 flat | $25,000 |
| *Subtotal: Software* | | | | *$92,200* |
| **Total OpEx** | **Total Traditional Department Cost** | | | **$2,172,200 / year** |

#### 2. Revenue Output
*   **Pipeline Generation:** 5 SDRs outputting 50 emails/day = 60,000 emails/year.
*   **Meeting Conversion:** Standard 2.0% conversion rate = 1,200 meetings/year.
*   **Win Rate:** Standard 20% win rate from meeting to closed-won.
*   **Deals Won:** 240 deals.
*   > **Total Revenue Generated: $9,600,000 / year** (240 × $40k ACV)

#### 3. Traditional Efficiency Metric
*   **Revenue per Dollar Spent:** $9.6M / $2.17M = **$4.42 generated per $1 spent.**
*   **Sales Customer Acquisition Cost (CAC):** $2.17M / 240 deals = **$9,050 per acquired customer.**

---

### Scenario B: OmniSales Augmented Department

In this scenario, we replace the manual heavy-lifting of SDRs and AE admin work with the 4-Agent OmniSales architecture. Humans shift to specialized "closing and relationship" roles.

#### 1. Operational Costs (Annual)

*The OmniSales model shifts OpEx from biological labor to highly efficient AI compute infrastructure, vastly reducing headcount and per-seat SaaS costs.*

| Expense Category | Unit / Role | Quantity | Annual Cost per Unit | Total Annual Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Headcount** | High-Performer AE (Meeting intensive) | 5 | $150,000 (OTE) | $750,000 |
| **Headcount** | Elite SDR (Approvals & Tier 1 Whales) | 1 | $80,000 (OTE) | $80,000 |
| **Headcount** | Director of Sales / Manager | 1 | $180,000 (OTE) | $180,000 |
| *Subtotal: Headcount* | *(51% Reduction)* | *7 FTEs* | | *$1,010,000* |
| **Software Stack** | CRM / Engagement / Sales Nav | 7 seats | $4,200 / user combined | $29,400 |
| **Data Enrichment** | B2B Contact Database (ZoomInfo) | 1 Org | $25,000 flat | $25,000 |
| **Agent Infra** | LLM Inference (Groq Dual-Model) | 4 Agents | ~$0.48 / day | $175 |
| **Agent Infra** | Cloud Infra (GKE, Kafka, DB, Pinecone) | 1 Cluster| ~$458 / month | $5,500 |
| *Subtotal: Software* | | | | *$60,075* |
| **Total OpEx** | **Total OmniSales Department Cost** | | | **$1,070,075 / year** |

#### 2. Revenue Output
*   **Pipeline Generation:** Prospector Agent safely outputs 500 hyper-personalized emails/day natively enriched with deep account logic = 120,000 emails/year.
*   **Meeting Conversion:** Boosted to **2.5%** (due to flawless personalization, Spider competitor battle-carding, and 24/7 immediate follow-ups) = 3,000 meetings/year.
    *   *Note: 5 AEs handling 3,000 meetings = ~2.5 meetings/day per AE, perfectly manageable since the Closer Agent handles all follow-up drafting, CRM updates, and objection-handling battle cards.*
*   **Win Rate:** Boosted to **25%** (The Closer Agent prevents deals from going stale, while the Guardian flags high-risk issues before they collapse the deal).
*   **Deals Won:** 750 deals.
*   > **Total Revenue Generated: $30,000,000 / year** (750 × $40k ACV)

#### 3. OmniSales Efficiency Metric
*   **Revenue per Dollar Spent:** $30M / $1.07M = **$28.03 generated per $1 spent.**
*   **Sales Customer Acquisition Cost (CAC):** $1.07M / 750 deals = **$1,426 per acquired customer.**

---

### The Final Metric: How Much Better Is It?

By comparing the two models, the ultimate financial superiority of the OmniSales Multi-Agent Architectural pattern is quantified by these conclusive metrics:

| Metric | Traditional Dept. | OmniSales Dept. | Delta (Improvement) |
| :--- | :--- | :--- | :--- |
| **Operational OpEx** | $2.17M / yr | **$1.07M / yr** | **⬇ 50.7% Cost Reduction** |
| **Annual Revenue** | $9.6M / yr | **$30.0M / yr** | **⬆ 3.1x Revenue Multiplier** |
| **Sales CAC** | $9,050 | **$1,426** | **⬇ 84% Cheaper to Acquire** |
| **Efficiency (Rev / Cost)** | $4.42 per $1 | **$28.03 per $1** | **🚀 6.3x Better ROI** |

**Conclusion:** 
An OmniSales augmented department isn't just slightly faster; it represents a **6.3x structural advantage in capital efficiency**. By decoupling pipeline generation and deal management from biological constraints (working hours, context switching, CRM data entry), the system scales outbound volume by 2x while simultaneously reducing bloated SDR headcount, allowing human AEs to act as "Editors and Closers" rather than administrators.

---

## 23. Implementation Roadmap

### Hackathon (2 Days) — What We're Shipping

- [x] Docker Compose stack (Postgres, Redis, Kafka, Pinecone)
- [x] PostgreSQL schema + seed data (20 accounts, 15 deals, 5 prospects)
- [x] Pinecone RAG pipeline (company docs + battle cards)
- [x] **3 Custom MCP Servers** — Approvals, Knowledge/RAG, CRM Simulator (all agents connect via MCP)
- [x] **Closer Agent** — deal risk detection + re-engagement via MCP tools (8 autonomous steps)
- [x] **Prospector Agent** — cold outreach research + personalized sequences via MCP tools (6 autonomous steps)
- [x] **Guardian Agent** — churn scoring + tailored retention plays via MCP tools (6 autonomous steps)
- [x] **Spy A2A Server (minimal)** — battle card endpoint, Closer calls it live via A2A protocol
- [x] FastAPI backend + WebSocket real-time updates
- [x] Next.js approval queue dashboard
- [x] Kafka inter-agent event flows
- [x] K8s manifests + KEDA scalers (architecture showcase)
- [x] 3-minute pitch video

### Post-Hackathon Roadmap

| Phase | Timeline | Deliverables |
| :--- | :--- | :--- |
| **Full Spy Agent** | Weeks 1–3 | Full Playwright scraping pipeline, change detection, auto battle card generation |
| **Live MCP Integration** | Weeks 3–5 | Connect to real HubSpot, Salesforce, Mixpanel, Intercom, Stripe APIs |
| **Production K8s** | Weeks 5–7 | GKE deployment, KEDA live autoscaling, Istio mTLS, Vault secrets |
| **Enterprise Hardening** | Weeks 7–10 | Multi-tenant RLS, ArgoCD GitOps, ClickHouse analytics, SOC 2 audit |
| **Scale Testing** | Weeks 10–12 | Load testing (1000 leads, 10K deals), chaos engineering |

---

## Appendix A — Kafka Topic Schema Reference

```json
// spy.competitor_event
{
  "competitor": "AcmeCRM", "event_type": "price_increase",
  "old_price": 499, "new_price": 699,
  "source_url": "https://acmecrm.com/pricing",
  "timestamp": "2025-09-15T14:23:00Z"
}

// prospector.lead_qualified
{
  "lead_id": "lead_abc123", "org_id": "org_xyz",
  "company": "Acme Corp", "contact": "John Smith",
  "icp_score": 0.87, "tier": "A",
  "timestamp": "2025-09-15T14:30:00Z"
}

// guardian.churn_risk
{
  "account_id": "acc_123", "org_id": "org_xyz",
  "churn_risk": 0.82, "reason": "switched_to_competitor",
  "competitor": "AcmeCRM",
  "top_signals": ["usage_drop_40pct", "support_ticket_open", "no_login_14_days"]
}

// closer.deal_won
{
  "deal_id": "deal_789", "account_id": "acc_789",
  "org_id": "org_xyz", "arr": 24000
}
```

---

## Appendix B — Environment Variables Reference

```bash
# All agents
GROQ_API_KEY=            # injected by Vault sidecar (multi-key pool)
KAFKA_BROKERS=           # kafka-broker:9092 or Confluent Cloud URL
DATABASE_URL=            # postgresql://user:pass@host/db
REDIS_URL=               # redis://redis:6379
LANGSMITH_API_KEY=       # LLM observability
ORG_ID=                  # set per deployment (multi-tenant)

# Closer-specific
SPY_A2A_URL=             # http://agent-spy.omnisales-agents.svc:8080
MCP_HUBSPOT_URL=         # https://mcp.hubspot.com/v1
MCP_SALESFORCE_URL=      # https://salesforce-mcp-host/v1
MCP_SENDGRID_URL=        # http://mcp-sendgrid-service:8002/mcp
MCP_CALENDLY_URL=        # http://mcp-calendly-service:8005/mcp
MCP_KNOWLEDGE_URL=       # http://mcp-knowledge-service:8006/mcp
MCP_APPROVALS_URL=       # http://mcp-approvals-service:8004/mcp

# Prospector-specific
MCP_APOLLO_URL=          # http://mcp-apollo-service:8001/mcp
MCP_SCRAPER_URL=         # http://mcp-scraper-service:8003/mcp

# Guardian-specific
MCP_MIXPANEL_URL=        # https://mixpanel.com/mcp/v1
MCP_INTERCOM_URL=        # https://api.intercom.io/mcp
MCP_STRIPE_URL=          # http://mcp-stripe-service:8007/mcp
MCP_SLACK_URL=           # via Composio or official when available

# Spy-specific
A2A_SERVER_PORT=8080
PINECONE_API_KEY=        # injected by Vault
PINECONE_INDEX=omnisales-knowledge
```

---

## Appendix C — Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-org/omnisales.git && cd omnisales

# 2. Copy env file and fill in your keys
cp .env.example .env

# 3. Start the full local stack
docker compose up --build

# 4. Access
open http://localhost:3000    # Dashboard
open http://localhost:8000/docs  # API docs

# 5. Trigger the Closer manually
curl -X POST http://localhost:8000/api/deals/deal_4821/trigger \
  -H "Authorization: Bearer YOUR_JWT"
```

---

*OmniSales Architecture Document — v2.0 Hackathon Edition*  
*Stack: LangGraph 0.2+ · FastMCP · A2A · Apache Kafka · PostgreSQL 16 · Pinecone · Redis · Docker · Kubernetes (GKE) · KEDA · Istio · HashiCorp Vault · Datadog · LangSmith · ArgoCD*  
*LLM: Groq (`llama-3.3-70b-versatile` + `llama-3.1-8b-instant`)*