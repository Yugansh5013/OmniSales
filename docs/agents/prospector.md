# 🔍 Prospector Agent

The **Prospector Agent** (`:9002`) is an autonomous outbound sales development representative (SDR). It automates the top-of-funnel pipeline by ingesting uncontacted leads, enriching company firmographics and technology stacks, computing quantitative Ideal Customer Profile (ICP) fit scores, identifying key executive buyer personas, and generating personalized multi-touch outreach sequences.

---

## 1. Architectural Overview

The Prospector Agent executes an autonomous pipeline using a **LangGraph state graph** with checkpointing in PostgreSQL. It qualifies inbound and cold prospects before gating the drafted sequences behind the Human-in-the-Loop approvals queue.

```mermaid
flowchart TD
    START([Lead Ingested / Trigger]) --> RESEARCH[research_company]
    RESEARCH --> ENRICH[enrich_lead]
    ENRICH --> SCORE[score_icp]
    
    SCORE --> TIER_CHECK{ICP Score >= 0.50?}
    TIER_CHECK -->|No / Tier D| DISQUALIFY[Disqualify Lead\nStatus: unqualified]
    TIER_CHECK -->|Yes / Tier A-C| CONTACTS[identify_contacts]
    
    CONTACTS --> DRAFT[draft_sequences\n3-Email Multi-Touch Cadence]
    DRAFT --> HITL[interrupt_before: Human Gate\nQueue in agent_tasks]
    
    HITL --> APPROVE{Rep Approves?}
    APPROVE -->|Approve| SEND[Dispatch Sequence via Resend\nUpdate Lead: contacted]
    APPROVE -->|Reject with Feedback| REGEN[/regenerate Loop]
    REGEN --> DRAFT
```

---

## 2. Graph Pipeline & Execution Stages

### 1. `research_company`
- Reads lead profile from CRM MCP (`get_lead`).
- Extracts company domain, employee count, sector, geographic region, and reported ARR.

### 2. `enrich_lead`
- Synthesizes technical firmographics:
  - **Tech Stack**: Identifies cloud providers, database systems, event streaming, and API architecture.
  - **Funding & Stage**: Evaluates funding rounds (Seed, Series A/B, Growth) and hiring momentum.
  - **Contact Persona**: If contact records are missing or sparse, synthesizes qualified executive buyer profiles (e.g., CTO, VP Engineering, VP Growth) based on industry standards.

### 3. `score_icp` (Ideal Customer Profile)
- Evaluates firmographics using `shared.llm.FAST_LLM` (`openai/gpt-oss-20b`) against our enterprise B2B ICP criteria.
- **Scoring Dimensions**:
  1. Company Size & Employee Scale (20%)
  2. Technical Architecture & Tech Stack Overlap (30%)
  3. Funding Signals & Capital Runway (25%)
  4. Market Fit & B2B SaaS Vertical (25%)
- **Tier Classification**:
  - **Tier A (0.85 – 1.00)**: Immediate priority outreach; tailored C-level sequence.
  - **Tier B (0.70 – 0.84)**: Strong fit; standard 3-email sequence.
  - **Tier C (0.50 – 0.69)**: Moderate fit; product-led nurture track.
  - **Tier D (< 0.50)**: Unqualified; deprioritized with zero rep time wasted.

### 4. `identify_contacts`
- Identifies technical and business decision-makers.
- Extracts role priorities:
  - *Technical Buyer (CTO/VP Eng)*: Latency, uptime, security, developer ergonomics.
  - *Commercial Buyer (CRO/VP Sales)*: Revenue acceleration, pipeline visibility, quota attainment.

### 5. `draft_sequences`
- Uses `shared.llm.COMPLEX_LLM` (`openai/gpt-oss-120b`) to craft a personalized 3-email cadence:
  - **Email 1 (The Hook)**: Specific firmographic observation (e.g., Series B expansion, Kafka scaling) and strategic value proposition.
  - **Email 2 (The Proof)**: Case study demonstration and ROI metric.
  - **Email 3 (The Low-Friction Ask)**: Direct call to action offering a 10-minute technical architecture walk-through.

---

## 3. Human Gate & Editorial Controls

- Once drafted, Prospector saves the sequence into `agent_tasks` with full executive reasoning and firmographic briefing.
- In the dashboard (`/dashboard/approvals`), reps can:
  - Inspect the synthesized ICP breakdown.
  - Edit email subject lines and body copy directly in the Draft Editor.
  - Approve for immediate delivery via Resend API or reject with prompt corrections.

---

## 4. Endpoints & API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/trigger/{lead_id}` | Triggers ICP qualification and sequence drafting for a lead |
| `POST` | `/batch` | Triggers parallel evaluation for all uncontacted leads |
| `POST` | `/regenerate/{task_id}` | Regenerates sequences incorporating human feedback |
| `GET` | `/health` | Lightweight service health probe |
| `GET` | `/.well-known/agent.json` | Google A2A Agent Card specification metadata |
