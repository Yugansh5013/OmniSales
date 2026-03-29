/** OmniSales Utility Library — All computed metrics, zero hardcoded values */

// ── Currency Formatting ──
export function formatCurrency(amount: number): string {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
  return `$${amount.toFixed(0)}`;
}

export function formatCurrencyFull(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);
}

// ── Time Formatting ──
export function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

// ── Deal / Pipeline Calculations ──
export function computeDaysInStage(lastActivity: string): number {
  const now = Date.now();
  const activity = new Date(lastActivity).getTime();
  return Math.max(0, Math.floor((now - activity) / 86_400_000));
}

export function computeDaysSince(dateStr: string): number {
  return computeDaysInStage(dateStr);
}

export function computePipelineValue(deals: Array<{ arr: number; stage: string }>): number {
  return deals
    .filter(d => d.stage !== 'closed_won' && d.stage !== 'closed_lost')
    .reduce((sum, d) => sum + Number(d.arr), 0);
}

export function computeStageStats(deals: Array<{ arr: number; stage: string }>) {
  const stages: Record<string, { count: number; totalArr: number }> = {};
  for (const deal of deals) {
    if (!stages[deal.stage]) stages[deal.stage] = { count: 0, totalArr: 0 };
    stages[deal.stage].count++;
    stages[deal.stage].totalArr += Number(deal.arr);
  }
  return stages;
}

// ── Health / Risk Calculations ──
export function computeHealthColor(score: number): string {
  if (score >= 0.7) return 'var(--success)';
  if (score >= 0.4) return 'var(--warning)';
  return 'var(--danger)';
}

export function computeRiskBadge(riskLevel: string): { label: string; className: string } {
  switch (riskLevel) {
    case 'at_risk': return { label: 'AT RISK', className: 'badge-danger' };
    case 'stalled': return { label: 'STALLED', className: 'badge-warning' };
    case 'healthy': return { label: 'HEALTHY', className: 'badge-success' };
    default: return { label: riskLevel.toUpperCase(), className: 'badge-muted' };
  }
}

export function computeStatusBadge(status: string): { label: string; className: string } {
  switch (status) {
    case 'pending_approval': return { label: 'Pending', className: 'badge-warning' };
    case 'approved': return { label: 'Approved', className: 'badge-success' };
    case 'rejected': return { label: 'Rejected', className: 'badge-danger' };
    case 'sent': return { label: 'Sent', className: 'badge-info' };
    case 'error': return { label: 'Error', className: 'badge-danger' };
    default: return { label: status, className: 'badge-muted' };
  }
}

export function computeChurnCategory(risk: number): 'high' | 'medium' | 'low' {
  if (risk >= 0.7) return 'high';
  if (risk >= 0.4) return 'medium';
  return 'low';
}

export function computeIcpColor(score: number | null): string {
  if (score === null) return 'var(--text-muted)';
  if (score > 0.7) return 'var(--success)';
  if (score > 0.4) return 'var(--warning)';
  return 'var(--danger)';
}

// ── Sparkline Math ──
export function computeSparklinePath(values: number[], width = 80, height = 24): string {
  if (!values || values.length < 2) return '';
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const dx = width / (values.length - 1);

  return values
    .map((v, i) => {
      const x = i * dx;
      const y = height - ((v - min) / range) * height;
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

export function computeTrendDirection(values: number[]): 'up' | 'down' | 'flat' {
  if (!values || values.length < 2) return 'flat';
  const first = values[0];
  const last = values[values.length - 1];
  if (last > first * 1.02) return 'up';
  if (last < first * 0.98) return 'down';
  return 'flat';
}

export function computeTrendPercentage(values: number[]): number {
  if (!values || values.length < 2 || values[0] === 0) return 0;
  return Number(((values[values.length - 1] - values[0]) / values[0] * 100).toFixed(1));
}

// ── Agent Helpers ──
export function getAgentColor(agentName: string): string {
  switch (agentName?.toLowerCase()) {
    case 'closer': return 'var(--closer)';
    case 'prospector': return 'var(--prospector)';
    case 'guardian': return 'var(--guardian)';
    case 'spy': return 'var(--spy)';
    default: return 'var(--text-muted)';
  }
}

export function getAgentBadgeClass(agentName: string): string {
  switch (agentName?.toLowerCase()) {
    case 'closer': return 'badge-closer';
    case 'prospector': return 'badge-prospector';
    case 'guardian': return 'badge-guardian';
    case 'spy': return 'badge-spy';
    default: return 'badge-muted';
  }
}

export function getAgentIcon(agentName: string): string {
  switch (agentName?.toLowerCase()) {
    case 'closer': return '🎯';
    case 'prospector': return '🔍';
    case 'guardian': return '🛡️';
    case 'spy': return '🕵️';
    default: return '🤖';
  }
}

// ── Percentage ──
export function formatPercent(value: number, decimals = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// ── Gauge Arc Math ──
export function computeGaugeArc(score: number, radius = 20): { circumference: number; offset: number } {
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score * circumference);
  return { circumference, offset };
}

// ── Task Type Formatting ──
export function formatTaskType(taskType: string): string {
  return taskType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ── Stage Formatting ──
export function formatStage(stage: string): string {
  return stage
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ── Cost Formatting ──
export function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

// ── Token Formatting ──
export function formatTokens(tokens: number): string {
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
  return tokens.toString();
}
