# 🌐 OmniSales — Enterprise Scaling & Infrastructure Architecture

This document specifies the target enterprise production architecture and horizontal scaling topology for **OmniSales**, transitioning from local multi-container orchestration to distributed Kubernetes infrastructure.

---

## 🏗️ 1. Distributed Production Topology

```
                                  [ Internet / Customers / Webhooks ]
                                                  │
                                                  ▼
                                    [ Cloudflare DDoS & WAF ]
                                                  │
                                                  ▼
                               [ AWS ALB / NGINX Ingress Controller ]
                                      (TLS Termination & HTTP/2)
                                                  │
                  ┌───────────────────────────────┴──────────────────────────────┐
                  │                                                              │
                  ▼                                                              ▼
    ┌───────────────────────────┐                                  ┌───────────────────────────┐
    │     NEXT.JS DASHBOARD     │                                  │      FASTAPI GATEWAY      │
    │     (Replicas: 3-10)      │                                  │     (Replicas: 4-15)      │
    │  - Edge Static Assets     │                                  │  - Auth & JWT Validation  │
    │  - SSR Streaming (SSE)    │                                  │  - Deal Desk Gate         │
    │  - Command Palette        │                                  │  - Razorpay Settlement    │
    └───────────────────────────┘                                  └─────────────┬─────────────┘
                                                                                 │
                                                ┌────────────────────────────────┴──────────────────┐
                                                │ (FastMCP HTTP)                                    │ (Google A2A)
                                                ▼                                                   ▼
                                  ┌───────────────────────────┐                       ┌───────────────────────────┐
                                  │      FASTMCP SERVERS      │                       │       SPY A2A AGENT       │
                                  │   (CRM, Knowledge, HITL)  │                       │      (Replicas: 2-5)      │
                                  │     (Replicas: 3-8)       │                       │  - Agent Card Discovery   │
                                  └─────────────┬─────────────┘                       │  - Live Battlecards       │
                                                │                                     └───────────────────────────┘
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │              AGENT WORKER SWARM               │
                        │       (Autoscaled via KEDA + HPA)             │
                        ├───────────────────────┬───────────────────────┤
                        │ Closer Agent          │ Prospector Agent      │
                        │ (LangGraph Checkpoints│ (Multi-Touch Sequence │
                        │  Replicas: 2-12)      │  Replicas: 2-10)      │
                        ├───────────────────────┴───────────────────────┤
                        │ Guardian Agent                                │
                        │ (Batch Telemetry & Churn Mitigation)          │
                        │ (Replicas: 2-8)                               │
                        └───────────────────────┬───────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │             APACHE KAFKA CLUSTER              │
                        │   - `closer.deal_won`                         │
                        │   - `guardian.churn_risk`                     │
                        │   - `prospector.lead_qualified`               │
                        └───────────────────────┬───────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │    KEDA AUTOSCALER    │
                                    │ (Triggers agent pods  │
                                    │  off consumer lag)    │
                                    └───────────────────────┘

                              [ PERSISTENCE & CACHING LAYER ]
                                  │                       │
                                  ▼                       ▼
                     ┌─────────────────────────┐  ┌─────────────────────────┐
                     │   NEON CLOUD POSTGRES   │  │      REDIS CLUSTER      │
                     │  - PgBouncer Pooling    │  │  - Pub/Sub Approval Bus │
                     │  - Row-Level Security   │  │  - Rate Limit Buckets   │
                     │  - Read Replicas        │  │  - Session Cache        │
                     └─────────────────────────┘  └─────────────────────────┘
```

---

## ⚡ 2. Event-Driven Autoscaling with KEDA

OmniSales leverages **Kubernetes Event-driven Autoscaling (KEDA)** to dynamically scale agent worker pods based on real-time event queue depth rather than lagging CPU/Memory utilization.

### Why KEDA over Standard HPA?
* **Agent Bursts**: When a CRM scan imports 500 leads, CPU remains low while the queue fills. KEDA detects consumer lag instantaneously and spins up Prospector worker pods before latency degrades.
* **Scale-to-Zero**: During off-peak hours (nights and weekends), asynchronous batch processors scale down to 0-1 pods, eliminating idle LLM container costs.

### Target KEDA ScaledObject Specification:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: closer-agent-scaler
  namespace: omnisales
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: closer-agent
  minReplicaCount: 2
  maxReplicaCount: 15
  cooldownPeriod: 60
  triggers:
    - type: kafka
      metadata:
        bootstrapServers: kafka:9092
        consumerGroup: closer-group
        topic: closer.deal_stalled
        lagThreshold: "5"
```

---

## 💾 3. Database & State Scaling Strategy

### 1. Connection Pooling with PgBouncer
* **Challenge**: Each LangGraph agent pod manages concurrent async database connections. 20 agent replicas could spawn 200+ direct connections, exhausting PostgreSQL connection limits.
* **Solution**: Deploy a **PgBouncer proxy** in front of Neon PostgreSQL using transaction-level pooling (`pool_mode = transaction`). This caps backend connections at 30 while supporting thousands of client connections.

### 2. Multi-Tenant Row-Level Security (RLS) Isolation
* Every table enforces PostgreSQL Row-Level Security:
  ```sql
  CREATE POLICY tenant_isolation_policy ON deals
      USING (org_id = current_setting('app.current_org_id')::uuid);
  ```
* Before query execution, connection pools set the active tenant context using strictly validated UUIDs:
  ```python
  await conn.execute(f"SET app.current_org_id = '{safe_org_uuid}'")
  ```

### 3. Asynchronous Checkpointing (`AsyncPostgresSaver`)
* LangGraph state machines persist execution graphs into the `checkpoints` table. During multi-hour human approval pauses, no memory is retained in worker pods.
* Pods can be restarted or rescheduled without losing deal state, conversation threads, or objection memory.

---

## 🛡️ 4. High Availability & Disaster Recovery

| Component | Target SLA | Strategy |
| :--- | :---: | :--- |
| **API Gateway** | 99.99% | Multi-AZ deployment across 3 availability zones with health probes. |
| **Database** | 99.95% | Neon serverless autoscaling with multi-region read replicas. |
| **Kafka Bus** | 99.99% | Confluent Cloud managed 3-broker cluster with min in-sync replicas (`acks=all`). |
| **Redis Cache** | 99.95% | Multi-node Redis Sentinel or AWS ElastiCache cluster with automated failover. |

---

## 🔐 5. Zero-Trust Security & Network Segmentation

1. **Mutual TLS (mTLS)**: Istio service mesh enforces encrypted, authenticated communication between all internal pods.
2. **Deterministic Governance Barrier**: The Deal Desk commercial engine executes locally in memory on the Gateway prior to any database write or payment API call, guaranteeing that no rogue prompt injection can manipulate discount ceilings.
3. **Secret Management**: External keys (`GROQ_API_KEYS`, `RAZORPAY_KEY_SECRET`, `RESEND_API_KEY`) are managed via **AWS Secrets Manager** or **HashiCorp Vault** and mounted into pods as short-lived secret volumes.
