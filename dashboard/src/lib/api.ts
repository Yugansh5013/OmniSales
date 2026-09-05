/** OmniSales API Client — wraps fetch with JWT auth */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('omnisales_token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = error.detail || error.error?.message || `API Error: ${res.status}`;
    const errObj = new Error(msg);
    (errObj as unknown as { response: unknown }).response = error;
    throw errObj;
  }
  return res.json();
}

// ── Auth ──
export interface LoginResponse {
  token: string;
  user: { email: string; name: string; role: string };
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

// ── Dashboard ──
export interface DashboardStats {
  pipeline_value: number;
  active_deals: number;
  at_risk_deals: number;
  high_churn_accounts: number;
  at_risk_arr?: number;
  pending_approvals: number;
  total_accounts: number;
  avg_health_score: number;
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request('/api/dashboard/stats');
}

// ── Deals ──
export interface Deal {
  id: string;
  company: string;
  stage: string;
  arr: number;
  risk_level: string;
  last_activity: string;
  lead_id?: string;
  discount_pct?: number;
  contract_months?: number;
  payment_terms?: string;
  custom_sla?: boolean;
  tier?: string;
  owner?: string;
  contact_name?: string;
  contact_email?: string;
  contact_title?: string;
  closer_thread?: Array<{ from: string; to: string; subject?: string; body: string; date?: string; timestamp?: string }>;
  agent_log?: Record<string, unknown>[];
  created_at?: string;
}

export interface TimelineEvent {
  id: string;
  agent_name: string;
  task_type: string;
  status: string;
  target_name: string;
  draft: string;
  reasoning: string;
  created_at: string;
  model_used?: string;
  tokens_used?: number;
  cost?: number;
  feedback?: string;
  source?: string;
  scan_number?: number;
  trigger?: string;
  [key: string]: unknown;
}

export function fetchDeals(stage?: string, risk_level?: string, owner?: string): Promise<Deal[]> {
  const params = new URLSearchParams();
  if (stage) params.set('stage', stage);
  if (risk_level) params.set('risk_level', risk_level);
  if (owner) params.set('owner', owner);
  const qs = params.toString();
  return request(`/api/deals${qs ? `?${qs}` : ''}`);
}

export function fetchDeal(id: string): Promise<Deal> {
  return request(`/api/deals/${id}`);
}

export function fetchDealTimeline(dealId: string): Promise<TimelineEvent[]> {
  return request(`/api/deals/${dealId}/timeline`);
}

export function triggerCloser(dealId: string) {
  return request(`/api/deals/${dealId}/trigger`, { method: 'POST' });
}

export interface DealDeskEvaluation {
  status: 'approved' | 'policy_violation' | 'approved_with_override';
  violations_count: number;
  violations: Array<{ code: string; field: string; message: string; severity: string }>;
  counter_proposal: {
    proposed_discount_pct: number;
    proposed_contract_months: number;
    proposed_payment_terms: string;
    proposed_tier: string;
    proposed_custom_sla: boolean;
    base_arr: number;
    discounted_arr: number;
    total_contract_value: number;
    customer_annual_savings: number;
    explanation: string;
  } | null;
  policy_version: string;
}

export function evaluateDealDesk(dealId: string, terms: {
  discount_pct?: number;
  contract_months?: number;
  payment_terms?: string;
  custom_sla?: boolean;
  override?: boolean;
  override_reason?: string;
}): Promise<DealDeskEvaluation> {
  return request(`/api/deals/${dealId}/deal-desk/evaluate`, {
    method: 'POST',
    body: JSON.stringify(terms),
  });
}

export interface PaymentLinkResponse {
  id: string;
  short_url: string;
  amount: number;
  status: string;
  is_simulated: boolean;
  deal_desk_evaluation?: DealDeskEvaluation;
}

export function generatePaymentLink(dealId: string, payload: {
  discount_pct?: number;
  contract_months?: number;
  payment_terms?: string;
  custom_sla?: boolean;
  override?: boolean;
  override_reason?: string;
}): Promise<PaymentLinkResponse> {
  return request(`/api/deals/${dealId}/payment-link`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ── Leads ──
export interface Lead {
  id: string;
  company: string;
  contact_name: string;
  email: string;
  title: string;
  icp_score: number | null;
  tier: string;
  status: string;
  owner?: string;
  enrichment?: {
    founded?: number;
    employees?: number;
    funding?: string;
    tech_stack?: string[];
    signals?: string[];
    industry?: string;
    revenue_est?: string;
  };
}

export function fetchLeads(status?: string, owner?: string): Promise<Lead[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (owner) params.set('owner', owner);
  const qs = params.toString();
  return request(`/api/leads${qs ? `?${qs}` : ''}`);
}

export function fetchLead(id: string): Promise<Lead> {
  return request(`/api/leads/${id}`);
}

export function triggerProspector(leadId: string) {
  return request(`/api/leads/${leadId}/trigger`, { method: 'POST' });
}

export function importLeads(leads: Array<{
  company: string;
  contact_name?: string;
  email?: string;
  title?: string;
  source?: string;
  owner?: string;
}>): Promise<{ status: string; imported: number }> {
  return request('/api/leads/import', {
    method: 'POST',
    body: JSON.stringify(leads),
  });
}

// ── Accounts (Guardian) ──
export interface Account {
  id: string;
  company: string;
  arr: number;
  plan: string;
  health_score: number;
  churn_risk: number;
  usage_pct: number;
  support_tickets: number;
  last_login: string;
  owner?: string;
  metadata?: {
    signals?: string[];
    contract_renewal?: string;
    top_signals?: string[];
    risk_tier?: string;
  };
}

export function fetchAccounts(minChurnRisk?: number, owner?: string): Promise<Account[]> {
  const params = new URLSearchParams();
  if (minChurnRisk) params.set('min_churn_risk', String(minChurnRisk));
  if (owner) params.set('owner', owner);
  const qs = params.toString();
  return request(`/api/accounts${qs ? `?${qs}` : ''}`);
}

export function triggerGuardian(): Promise<{
  accounts_analyzed: number;
  flagged_count: number;
  flagged: Array<{
    account_id: string;
    company: string;
    arr?: number;
    plan?: string;
    churn_risk?: number;
    risk_tier?: string;
    action?: string;
    top_signals?: string[];
  }>;
  draft?: string;
  task_id?: string;
  status?: string;
}> {
  return request('/api/accounts/analyze', { method: 'POST' });
}

// ── Tasks / Approvals ──
export interface AgentTask {
  id: string;
  agent_name: string;
  task_type: string;
  status: string;
  target_name: string;
  target_id?: string;
  draft: string | null;
  reasoning: string;
  model_used?: string;
  tokens_used?: number;
  cost?: number;
  created_at: string;
  feedback?: string;
}

export function fetchTasks(status = 'pending_approval', agent = '', owner = ''): Promise<AgentTask[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (agent) params.set('agent', agent);
  if (owner) params.set('owner', owner);
  const qs = params.toString();
  return request(`/api/tasks${qs ? `?${qs}` : ''}`);
}

export function approveTask(taskId: string, approved: boolean, feedback = '', draft?: string) {
  return request(`/api/tasks/${taskId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved, feedback, draft }),
  });
}

// ── Orchestrator ──
export function triggerOrchestratorScan(): Promise<ScanReport> {
  return request<ScanReport>('/api/orchestrator/scan', { method: 'POST' });
}
export const scanOrchestrator = triggerOrchestratorScan;

export interface OrchestratorChatResponse {
  response?: string;
  reply?: string;
  timestamp?: string;
  context_loaded?: boolean;
  [key: string]: unknown;
}

export function orchestratorChat(message: string, threadId?: string): Promise<OrchestratorChatResponse> {
  return request<OrchestratorChatResponse>('/api/orchestrator/chat', {
    method: 'POST',
    body: JSON.stringify({ message, thread_id: threadId }),
  });
}

export interface ScanReport {
  id: string;
  scan_number: number;
  status?: string;
  started_at: string;
  completed_at: string;
  total_dispatched: number;
  dispatch_details: Array<Record<string, unknown>>;
  summary?: string;
  triggered_by?: string;
  deals_scanned?: number;
  deals_dispatched?: number;
  leads_scanned?: number;
  leads_dispatched?: number;
  accounts_scanned?: number;
  accounts_dispatched?: number;
  [key: string]: unknown;
}

export function fetchOrchestratorHistory(limit = 10): Promise<ScanReport[]> {
  return request<ScanReport[]>(`/api/orchestrator/history?limit=${limit}`);
}

// ── Evals Scorecard ──
export interface EvalsScorecard {
  total_tasks_evaluated: number;
  approved_count: number;
  rejected_count: number;
  approval_rate_pct: number;
  rejection_rate_pct: number;
  fallback_count: number;
  fallback_rate_pct: number;
  model_distribution: Record<string, number>;
  agent_breakdown: Record<string, {
    total: number;
    approved: number;
    rejected: number;
    approval_rate_pct: number;
    avg_tokens: number;
    total_cost_usd: number;
  }>;
  offline_benchmarks?: Record<string, unknown>;
}

export async function fetchEvalsScorecard(): Promise<EvalsScorecard> {
  const res = await request<Record<string, any>>('/api/evals/scorecard');
  if (res && res.scorecard) {
    return {
      ...res.scorecard,
      offline_benchmarks: res.latest_offline_eval,
      evaluated_at: res.evaluated_at,
    };
  }
  return res as unknown as EvalsScorecard;
}

// ── Spy A2A / Competitors ──
export interface Competitor {
  id: string;
  name: string;
  strengths: string[];
  weaknesses: string[];
  pricing: string;
  displacement_strategy: string;
}

export function fetchCompetitors(): Promise<Competitor[]> {
  return request('/api/competitors');
}

export function fetchA2ABattlecard(competitor: string) {
  return request(`/api/a2a/battlecard/${competitor}`, { method: 'POST' });
}

export function fetchA2AWinback(competitor: string) {
  return request(`/api/a2a/winback/${competitor}`, { method: 'POST' });
}

// ── Audit & Agent Activity ──
export function fetchAuditEvents() {
  return request('/api/audit');
}

export function fetchAgentActivity(filter?: string | number): Promise<TimelineEvent[]> {
  return fetchAuditEvents() as unknown as Promise<TimelineEvent[]>;
}

export type AgentActivity = TimelineEvent;

export interface SystemServiceProbe {
  name: string;
  status: "healthy" | "degraded" | "unhealthy" | "unreachable";
  port?: string;
  latency_ms?: number;
  detail?: string;
}

export interface SystemProbesResponse {
  timestamp: string;
  services: Record<string, SystemServiceProbe>;
  groq_keys_count?: number;
}

export function fetchSystemProbes(): Promise<SystemProbesResponse> {
  return request('/api/system/probes');
}

export function fetchNotificationEmail(): Promise<{ email: string }> {
  return request('/api/settings/notification-email');
}

export function updateNotificationEmail(email: string): Promise<{ status: string; email: string }> {
  return request('/api/settings/notification-email', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

// ── CRM Sync & Ingestion ──
export interface CrmSyncSettings {
  auto_sync: boolean;
  interval_seconds: number;
  last_sync?: string | null;
  provider?: string;
  portal_id?: string;
  connected?: boolean;
}

export interface CrmSyncResult {
  status: string;
  synced_leads: number;
  synced_deals: number;
  timestamp: string;
  hubspot_portal?: string;
}

export function fetchCrmSyncSettings(): Promise<CrmSyncSettings> {
  return request<CrmSyncSettings>('/api/settings/crm-sync');
}

export function updateCrmSyncSettings(settings: { auto_sync: boolean; interval_seconds: number }): Promise<{ status: string }> {
  return request('/api/settings/crm-sync', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

export function triggerCrmSync(): Promise<CrmSyncResult> {
  return request<CrmSyncResult>('/api/crm/sync', { method: 'POST' });
}

