-- ============================================================
-- OmniSales — PostgreSQL Schema
-- Run on first startup via Docker init scripts
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Leads (Prospector domain) ──

CREATE TABLE leads (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL,
    company       TEXT,
    contact_name  TEXT,
    email         TEXT,
    title         TEXT,                     -- job title
    icp_score     FLOAT,                    -- 0–1, set by Prospector LLM
    tier          TEXT DEFAULT 'D',          -- A/B/C/D
    status        TEXT DEFAULT 'new',        -- new|contacted|replied|booked|dead
    source        TEXT DEFAULT 'prospector', -- prospector|manual|inbound
    enrichment    JSONB DEFAULT '{}',        -- raw Apollo/Clearbit data
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Deals (Closer domain) ──

CREATE TABLE deals (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id         UUID NOT NULL,
    lead_id        UUID REFERENCES leads(id),
    company        TEXT,
    stage          TEXT DEFAULT 'discovery',  -- discovery|proposal|negotiation|closed_won|closed_lost
    arr            NUMERIC DEFAULT 0,
    risk_level     TEXT DEFAULT 'healthy',    -- healthy|at_risk|stalled
    last_activity  TIMESTAMPTZ DEFAULT NOW(),
    closer_thread  JSONB DEFAULT '[]',        -- email conversation history
    agent_log      JSONB[] DEFAULT '{}',      -- immutable audit trail
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── Accounts (Guardian domain) ──

CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL,
    company         TEXT,
    arr             NUMERIC DEFAULT 0,
    plan            TEXT DEFAULT 'starter',
    health_score    FLOAT DEFAULT 0.5,        -- 0–1, updated by Guardian
    churn_risk      FLOAT DEFAULT 0.0,        -- 0–1, updated by Guardian
    usage_pct       FLOAT DEFAULT 0.5,        -- 0–1 plan utilization
    support_tickets INT DEFAULT 0,
    last_login      TIMESTAMPTZ DEFAULT NOW(),
    stripe_customer TEXT,
    metadata        JSONB DEFAULT '{}',        -- usage trends, signals, etc.
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Agent Tasks (Approval Queue) ──

CREATE TABLE agent_tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL,
    agent_name  TEXT NOT NULL,                -- prospector|closer|guardian|spy
    task_type   TEXT NOT NULL,                -- email_draft|risk_classification|churn_score|outreach_sequence|retention_play
    status      TEXT DEFAULT 'pending_approval', -- pending_approval|approved|rejected|sent|error
    target_id   UUID,                         -- deal_id, lead_id, or account_id
    target_name TEXT,                         -- human-readable name
    draft       TEXT,
    reasoning   TEXT,
    feedback    TEXT,                          -- human feedback on rejection
    thread_id   TEXT,                          -- LangGraph checkpoint thread ID
    model_used  TEXT,                          -- llama-3.3-70b-versatile | llama-3.1-8b-instant
    tokens_used INT DEFAULT 0,
    cost        NUMERIC(10,6) DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Competitors (Spy domain) ──

CREATE TABLE competitors (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL,
    name          TEXT NOT NULL,
    website       TEXT,
    last_scraped  TIMESTAMPTZ,
    pricing_hash  TEXT,
    data          JSONB DEFAULT '{}',          -- battle cards, pricing, features
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Scan Reports (Orchestrator domain) ──

CREATE TABLE scan_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_number         INTEGER NOT NULL,
    triggered_by        TEXT DEFAULT 'auto',          -- auto|manual|chat
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    status              TEXT DEFAULT 'running',        -- running|completed|failed
    deals_scanned       INTEGER DEFAULT 0,
    deals_dispatched    INTEGER DEFAULT 0,
    leads_scanned       INTEGER DEFAULT 0,
    leads_dispatched    INTEGER DEFAULT 0,
    accounts_scanned    INTEGER DEFAULT 0,
    accounts_dispatched INTEGER DEFAULT 0,
    total_dispatched    INTEGER DEFAULT 0,
    dispatch_details    JSONB DEFAULT '[]',            -- full dispatch action log
    error               TEXT,
    summary             TEXT                           -- LLM-generated summary
);

-- ── Row-Level Security ──

ALTER TABLE leads        ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals        ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts     ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks  ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors  ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation_leads       ON leads       USING (org_id = current_setting('app.current_org_id')::UUID);
CREATE POLICY org_isolation_deals       ON deals       USING (org_id = current_setting('app.current_org_id')::UUID);
CREATE POLICY org_isolation_accounts    ON accounts    USING (org_id = current_setting('app.current_org_id')::UUID);
CREATE POLICY org_isolation_tasks       ON agent_tasks USING (org_id = current_setting('app.current_org_id')::UUID);
CREATE POLICY org_isolation_competitors ON competitors USING (org_id = current_setting('app.current_org_id')::UUID);

-- ── Indexes ──

CREATE INDEX idx_deals_stage      ON deals(stage);
CREATE INDEX idx_deals_risk       ON deals(risk_level);
CREATE INDEX idx_leads_status     ON leads(status);
CREATE INDEX idx_leads_icp        ON leads(icp_score);
CREATE INDEX idx_accounts_churn   ON accounts(churn_risk DESC);
CREATE INDEX idx_tasks_status     ON agent_tasks(status);
CREATE INDEX idx_tasks_agent      ON agent_tasks(agent_name);
