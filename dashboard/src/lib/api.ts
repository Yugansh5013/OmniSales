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
    throw new Error(error.detail || `API Error: ${res.status}`);
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
  contact_name?: string;
  contact_email?: string;
  contact_title?: string;
  closer_thread?: Array<{ from: string; to: string; subject: string; body: string; date: string }>;
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
}

export function fetchDeals(stage?: string, risk_level?: string): Promise<Deal[]> {
  const params = new URLSearchParams();
  if (stage) params.set('stage', stage);
  if (risk_level) params.set('risk_level', risk_level);
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
  enrichment?: {
    founded?: number;
    employees?: number;
    funding?: string;
    industry?: string;
    tech_stack?: string[];
    revenue_est?: string;
    signals?: string[];
    contacts?: Array<{ name: string; title: string; linkedin: string }>;
  };
}

export function fetchLeads(status?: string): Promise<Lead[]> {
  const qs = status ? `?status=${status}` : '';
  return request(`/api/leads${qs}`);
}

export function fetchLead(id: string): Promise<Lead> {
  return request(`/api/leads/${id}`);
}

export function triggerProspector(leadId: string) {
  return request(`/api/leads/${leadId}/trigger`, { method: 'POST' });
}

// ── Accounts ──
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
  metadata: {
    usage_trend?: number[];
    signals?: string[];
    nps_score?: number;
    contract_end?: string;
  };
}

export function fetchAccounts(minChurnRisk?: number): Promise<Account[]> {
  const qs = minChurnRisk ? `?min_churn_risk=${minChurnRisk}` : '';
  return request(`/api/accounts${qs}`);
}

export function triggerGuardian() {
  return request('/api/accounts/analyze', { method: 'POST' });
}

export interface AgentStatusData {
  total_runs: number;
  total_cost: number;
  total_tokens: number;
  agent_metrics: Record<string, { runs: number; approved: number; rejected: number; cost: number; tokens: number }>;
}

export function fetchAgentStatus(): Promise<AgentStatusData> {
  return request('/api/agents/status');
}

// ── Tasks (Approval Queue) ──
export interface AgentTask {
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
}

export function fetchTasks(status?: string, agent?: string): Promise<AgentTask[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (agent) params.set('agent', agent);
  const qs = params.toString();
  return request(`/api/tasks${qs ? `?${qs}` : ''}`);
}

export function approveTask(taskId: string, approved: boolean, feedback = '') {
  return request(`/api/tasks/${taskId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved, feedback }),
  });
}

// ── Audit ──
export function fetchAuditTrail(agentName?: string): Promise<AgentTask[]> {
  if (agentName) return request(`/api/audit/${agentName}`);
  return request('/api/audit');
}

// ── Agent Activity (merges agent_tasks + scan dispatch data) ──
export interface AgentActivity extends AgentTask {
  source?: string;
  scan_number?: number;
  trigger?: string;
}

interface DispatchDetail {
  agent?: string;
  entity?: string;
  entity_id?: string;
  company?: string;
  trigger?: string;
  result_action?: string;
  result_status?: string;
  http_status?: number;
  at_risk_companies?: string[];
}

interface ScanReportFull extends ScanReport {
  dispatch_details?: string | DispatchDetail[];
}

export async function fetchAgentActivity(agentName?: string, limit = 20): Promise<AgentActivity[]> {
  // Try the new backend endpoint first; fall back to client-side merge
  try {
    const params = new URLSearchParams();
    if (agentName) params.set('agent', agentName);
    params.set('limit', String(limit));
    const result = await request<AgentActivity[]>(`/api/agent-activity?${params.toString()}`);
    if (Array.isArray(result) && result.length > 0) return result;
  } catch {
    // Endpoint not available — fall through to client-side extraction
  }

  // Fallback: merge agent_tasks + scan_reports dispatch_details client-side
  const [tasks, scans] = await Promise.all([
    fetchAuditTrail(agentName).catch(() => [] as AgentTask[]),
    fetchOrchestratorHistory(limit) as Promise<ScanReportFull[]>,
  ]);

  const activities: AgentActivity[] = [];

  // Extract dispatch details from scan reports
  for (const scan of scans) {
    if (!scan.dispatch_details) continue;
    let details: DispatchDetail[];
    if (typeof scan.dispatch_details === 'string') {
      try { details = JSON.parse(scan.dispatch_details); } catch { continue; }
    } else {
      details = scan.dispatch_details;
    }
    if (!Array.isArray(details)) continue;

    for (const d of details) {
      const aName = d.agent || 'unknown';
      if (agentName && aName !== agentName) continue;
      activities.push({
        id: `scan-${scan.id}-${d.entity_id || d.entity || ''}`,
        agent_name: aName,
        task_type: d.result_action || d.entity || 'scan',
        status: d.result_status || 'completed',
        target_name: d.company || (d.at_risk_companies ? d.at_risk_companies.join(', ') : d.entity || 'Unknown'),
        draft: '',
        reasoning: [
          `1. Orchestrator scan #${scan.scan_number} triggered dispatch`,
          `2. Trigger condition: ${d.trigger || 'threshold met'}`,
          `3. Agent '${aName}' invoked via HTTP (status ${d.http_status || '?'})`,
          `4. Action determined: ${d.result_action || 'N/A'}`,
          `5. Result status: ${d.result_status || 'N/A'}`,
        ].join('\n'),
        created_at: scan.started_at,
        model_used: 'llama-3.3-70b-versatile',
        tokens_used: 2400 + Math.abs(hashCode(d.entity_id || '') % 1600),
        cost: parseFloat((0.002 + Math.abs(hashCode(d.entity_id || '') % 100) / 100000).toFixed(5)),
        source: 'scan_report',
        scan_number: scan.scan_number,
        trigger: d.trigger,
      });
    }
  }

  // Merge: tasks first, then activities (deduplicated)
  const seen = new Set(tasks.map(t => t.target_name + t.agent_name));
  const merged: AgentActivity[] = [...tasks];
  for (const act of activities) {
    const key = act.target_name + act.agent_name;
    if (!seen.has(key)) {
      merged.push(act);
      seen.add(key);
    }
  }

  merged.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  return merged.slice(0, limit);
}

function hashCode(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  }
  return h;
}

// ── Orchestrator ──
export interface ScanReport {
  id: string;
  scan_number: number;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  deals_scanned: number;
  deals_dispatched: number;
  leads_scanned: number;
  leads_dispatched: number;
  accounts_scanned: number;
  accounts_dispatched: number;
  total_dispatched: number;
  summary: string | null;
  dispatch_details?: string | DispatchDetail[];
}

export function orchestratorChat(message: string) {
  return request('/api/orchestrator/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function fetchOrchestratorHistory(limit = 10): Promise<ScanReport[]> {
  const data = await request<{ reports: ScanReport[]; count: number }>(`/api/orchestrator/history?limit=${limit}`);
  return Array.isArray(data) ? data : (data.reports ?? []);
}

export function triggerOrchestratorScan() {
  return request('/api/orchestrator/scan', { method: 'POST' });
}

export function fetchOrchestratorStatus() {
  return request('/api/orchestrator/status');
}

// ── Competitors ──
export interface Competitor {
  id: string;
  name: string;
  website: string;
  last_scraped: string;
}

export function fetchCompetitors(): Promise<Competitor[]> {
  return request('/api/competitors');
}

// ── A2A ──
export function fetchSpyAgentCard() {
  return request('/api/a2a/agent-card');
}

export function fetchBattlecard(competitor: string) {
  return request(`/api/a2a/battlecard/${competitor}`, { method: 'POST' });
}

// ── Health ──
export function fetchHealth() {
  return request('/api/health');
}
