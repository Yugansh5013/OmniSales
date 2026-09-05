# 🛡️ Guardian Agent

The **Guardian Agent** (`:9003`) is an autonomous customer success and predictive churn defense worker. It continuously audits account-level consumption telemetry, open support tickets, and executive engagement signals across the entire customer base. When an account exhibits behavioral decay, Guardian scores predictive churn risk, flags at-risk ARR, broadcasts Kafka events, and formulates tailored 30-day executive retention playbooks.

---

## 1. Architectural Overview

Guardian operates both as a **portfolio-wide batch auditor** (evaluating all customer accounts in parallel) and as a **single-account intervention engine** gated by Human-in-the-Loop approvals.

```mermaid
flowchart TD
    START([Telemetry Sweep / Analyze]) --> ANALYZE[analyze_accounts\nFetch 20 Accounts via CRM MCP]
    ANALYZE --> SCORE[score_churn\nMulti-Signal Predictive Scoring]
    SCORE --> RANK[rank_and_flag\nIdentify Top Churn Risks > 0.65]
    
    RANK --> KAFKA[Broadcast Kafka Event\nguardian.churn_risk]
    RANK --> PLAYBOOK[generate_retention\n30-Day Executive Playbook]
    
    PLAYBOOK --> HITL[interrupt_before: Human Gate\nQueue in agent_tasks]
    HITL --> APPROVE{CS Manager Approves?}
    
    APPROVE -->|Approve| EXECUTE[Dispatch Retention Playbook\nLog Audit Record]
    APPROVE -->|Reject with Feedback| REGEN[/regenerate Loop]
    REGEN --> PLAYBOOK
```

---

## 2. Predictive Churn Scoring Engine

Guardian processes four primary telemetry vectors to compute a normalized churn probability score between `0.00` and `1.00`:

| Signal Vector | Weight | Indicator Description |
| :--- | :--- | :--- |
| **API & Usage Decay** | **35%** | Week-over-week drop in API consumption or platform activity (>30% drop indicates operational stall) |
| **P1 Support Tickets** | **30%** | Unresolved severity-1 engineering tickets or open critical outages (>10 days without resolution) |
| **Login Frequency Decay** | **20%** | Days since last executive login (>14 days suggests executive disengagement) |
| **Renewal Proximity** | **15%** | Days remaining until contract renewal window (<90 days elevates risk multiplier) |

### Churn Risk Thresholds
- **Critical Risk (0.75 – 1.00)**: Immediate executive threat; active migration or cancellation risk. Triggers Kafka broadcast and urgent 30-day intervention playbook.
- **Elevated Risk (0.50 – 0.74)**: Early degradation; accounts assigned to CSM check-in queue.
- **Healthy (< 0.50)**: Normal telemetry and stable consumption patterns.

---

## 3. Kafka Event Broadcasting

When Guardian flags an account with critical churn risk (`churn_risk >= 0.75`), it publishes an asynchronous event to the Apache Kafka cluster:

- **Topic**: `guardian.churn_risk`
- **Payload Schema**:
  ```json
  {
    "event_id": "evt_98f41...",
    "account_id": "acc_00000003",
    "company": "CloudMatrix Corp",
    "arr": 110000,
    "churn_risk": 0.85,
    "primary_signal": "API consumption down 45% with 2 unresolved P1 tickets",
    "timestamp": "2026-09-06T00:00:00Z"
  }
  ```
- **Consumer**: Orchestrator Agent subscribes to `guardian.churn_risk` to alert account executives and correlate churn signals with ongoing renewal deals.

---

## 4. 30-Day Executive Retention Playbooks

Unlike generic automated emails, Guardian uses `shared.llm.COMPLEX_LLM` (`openai/gpt-oss-120b`) to craft concrete operational recovery plans:

1. **Week 1 (Diagnostic Alignment)**: Direct VP Engineering / CTO outreach acknowledging the specific ticket/outage and scheduling an urgent technical debrief.
2. **Week 2 (SLA & Credit Resolution)**: Automated proposal of service credits or dedicated solutions engineering support to clear migration roadblocks.
3. **Weeks 3–4 (Quarterly Roadmap Review)**: Executive business review aligning future roadmap capabilities with the client's strategic expansion goals.

---

## 5. Endpoints & API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/analyze` | Scans all customer accounts, returns flagged risks, and queues top retention playbooks |
| `POST` | `/trigger/{account_id}` | Evaluates a single specific account and generates an intervention plan |
| `POST` | `/regenerate/{task_id}` | Regenerates the retention playbook incorporating manager feedback |
| `GET` | `/health` | Lightweight service health probe |
| `GET` | `/.well-known/agent.json` | Google A2A Agent Card specification metadata |
