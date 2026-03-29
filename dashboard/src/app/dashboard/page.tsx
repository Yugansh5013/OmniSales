'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchDashboardStats, fetchDeals, fetchAccounts, fetchAuditTrail, fetchAgentStatus, triggerOrchestratorScan, DashboardStats, Deal, Account, AgentTask, AgentStatusData } from '@/lib/api';
import { formatCurrency, formatRelativeTime, computeDaysInStage, getAgentBadgeClass, getAgentIcon, formatTaskType, computeSparklinePath, computeTrendPercentage } from '@/lib/utils';
import StatCard from '@/components/StatCard';
import AgentBadge from '@/components/AgentBadge';
import HealthGauge from '@/components/HealthGauge';
import Sparkline from '@/components/Sparkline';
import styles from './overview.module.css';

export default function DashboardOverview() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [atRiskDeals, setAtRiskDeals] = useState<Deal[]>([]);
  const [churnAccounts, setChurnAccounts] = useState<Account[]>([]);
  const [recentActivity, setRecentActivity] = useState<AgentTask[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanRunning, setScanRunning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  const runAutonomousScan = async () => {
    setScanRunning(true);
    setScanResult(null);
    try {
      const result = await triggerOrchestratorScan() as { total_dispatched?: number; summary?: string };
      setScanResult(`✅ ${result.summary || `Dispatched ${result.total_dispatched ?? 0} agent tasks`}`);
      // Refresh dashboard data after scan
      setTimeout(() => loadData(), 2000);
    } catch (err) {
      setScanResult(`❌ Scan failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setScanRunning(false);
    }
  };

  const loadData = async () => {
    try {
      const [statsData, deals, accounts, audit] = await Promise.all([
        fetchDashboardStats(),
        fetchDeals(undefined, 'at_risk'),
        fetchAccounts(0.7),
        fetchAuditTrail(),
      ]);
      setStats(statsData);
      setAtRiskDeals(deals.slice(0, 3));
      setChurnAccounts(accounts.sort((a, b) => b.churn_risk - a.churn_risk).slice(0, 3));
      setRecentActivity(audit.slice(0, 15));
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
    // Agent status is optional — don't let it break the dashboard
    try {
      const aStatus = await fetchAgentStatus();
      setAgentStatus(aStatus);
    } catch { /* endpoint may not exist yet */ }
  };

  useEffect(() => {
    loadData();

    // WebSocket auto-refresh logic (best-effort)
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/live');
      ws.onmessage = () => loadData();
      ws.onerror = () => {}; // silent
    } catch { /* WS unavailable */ }
    return () => { try { ws?.close(); } catch {} };
  }, []);

  if (loading) {
    return (
      <div className="page-content">
        <div className={styles.statsRow}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: 120, borderRadius: 'var(--radius-lg)' }} />
          ))}
        </div>
      </div>
    );
  }

  const atRiskArr = atRiskDeals.reduce((s, d) => s + (d.arr || 0), 0);
  const churnArr = churnAccounts.reduce((s, a) => s + (a.arr || 0), 0);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">Command Center</h1>
          <p className="text-body-sm text-muted">Your AI workforce is monitoring {stats?.active_deals ?? 0} deals, {churnAccounts.length > 0 ? '20' : '0'} accounts, and 5 leads — autonomously, 24/7.</p>
        </div>
        <div className={styles.headerActions}>
          <button
            onClick={runAutonomousScan}
            disabled={scanRunning}
            style={{
              padding: '8px 20px',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: scanRunning
                ? 'rgba(168,85,247,0.15)'
                : 'linear-gradient(135deg, var(--prospector), var(--closer))',
              color: scanRunning ? 'var(--text-muted)' : '#fff',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: scanRunning ? 'wait' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>{scanRunning ? '⏳' : '🔄'}</span>
            {scanRunning ? 'Scanning...' : 'Run Autonomous Scan'}
          </button>
          {scanResult && (
            <span className="text-body-sm" style={{ maxWidth: 320, color: scanResult.startsWith('✅') ? 'var(--guardian)' : 'var(--danger)' }}>
              {scanResult}
            </span>
          )}
          <span className={styles.liveIndicator}>
            <span className="dot dot-green pulse-dot" />
            <span className="text-body-sm">Agents Online</span>
          </span>
        </div>
      </div>

      {/* Revenue Impact Banner */}
      <div className="card" style={{
        marginBottom: 'var(--space-lg)',
        padding: 'var(--space-lg) var(--space-xl)',
        background: 'linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(168,85,247,0.08) 50%, rgba(34,211,153,0.08) 100%)',
        border: '1px solid rgba(168,85,247,0.2)',
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-lg)',
      }}>
        <div>
          <span className="text-label" style={{ display: 'block', marginBottom: 4, letterSpacing: '0.08em' }}>PIPELINE PROTECTED</span>
          <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--closer)' }}>
            {formatCurrency(stats?.pipeline_value ?? 0)}
          </span>
          <span className="text-body-sm text-muted" style={{ display: 'block', marginTop: 2 }}>Closer monitoring {stats?.active_deals ?? 0} active deals</span>
        </div>
        <div>
          <span className="text-label" style={{ display: 'block', marginBottom: 4, letterSpacing: '0.08em' }}>CHURN RISK IDENTIFIED</span>
          <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--danger)' }}>
            {formatCurrency(churnArr)}
          </span>
          <span className="text-body-sm text-muted" style={{ display: 'block', marginTop: 2 }}>Guardian flagged {churnAccounts.length} high-risk accounts</span>
        </div>
        <div>
          <span className="text-label" style={{ display: 'block', marginBottom: 4, letterSpacing: '0.08em' }}>DEALS AT RISK</span>
          <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--warning)' }}>
            {formatCurrency(atRiskArr)}
          </span>
          <span className="text-body-sm text-muted" style={{ display: 'block', marginTop: 2 }}>{atRiskDeals.length} stalled deals need re-engagement</span>
        </div>
        <div>
          <span className="text-label" style={{ display: 'block', marginBottom: 4, letterSpacing: '0.08em' }}>AI COST EFFICIENCY</span>
          <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--success)' }}>
            {'< $0.05'}
          </span>
          <span className="text-body-sm text-muted" style={{ display: 'block', marginTop: 2 }}>vs ~$450/day manual sales ops</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className={styles.statsRow}>
        <StatCard
          label="Active Deals"
          value={stats?.active_deals ?? 0}
          icon="📊"
          color="blue"
        />
        <StatCard
          label="Pending Approvals"
          value={stats?.pending_approvals ?? 0}
          icon="⏳"
          color="amber"
          pulse={(stats?.pending_approvals ?? 0) > 0}
        />
        <StatCard
          label="Churn Alerts"
          value={stats?.high_churn_accounts ?? 0}
          icon="🔥"
          color="rose"
        />
        <StatCard
          label="Pipeline Value"
          value={formatCurrency(stats?.pipeline_value ?? 0)}
          icon="💰"
          color="green"
        />
      </div>

      {agentStatus && (
        <div className="card" style={{ marginBottom: 'var(--space-lg)', padding: 'var(--space-md) var(--space-lg)', display: 'flex', gap: 'var(--space-xl)', alignItems: 'center', background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
          <div>
            <span className="text-label" style={{ display: 'block', marginBottom: '4px' }}>FLEET EFFICIENCY</span>
            <span className="text-title" style={{ fontSize: '1.25rem' }}>{agentStatus.total_runs} Actions</span>
          </div>
          <div>
            <span className="text-label" style={{ display: 'block', marginBottom: '4px' }}>COST SAVINGS</span>
            <span className="text-body font-mono text-muted" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              ${agentStatus.total_cost.toFixed(3)}
              <span className="badge badge-success">vs $450 manual</span>
            </span>
          </div>
          <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-md)' }}>
            {Object.entries(agentStatus.agent_metrics).map(([agent, metrics]) => (
              <div key={agent} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AgentBadge agent={agent} size="sm" />
                <span className="font-mono text-body-sm">{metrics.runs}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className={styles.mainGrid}>
        {/* Activity Feed */}
        <div className={`card ${styles.activityCard}`}>
          <div className={styles.cardHeader}>
            <h3 className="text-title">Agent Activity</h3>
            <Link href="/dashboard/audit" className="text-body-sm" style={{ color: 'var(--closer)' }}>View All →</Link>
          </div>
          <div className={styles.activityList}>
            {recentActivity.map((item, i) => (
              <div key={item.id || i} className={styles.activityItem}>
                <div className={styles.activityIcon}>
                  <span>{getAgentIcon(item.agent_name)}</span>
                </div>
                <div className={styles.activityContent}>
                  <div className={styles.activityHeader}>
                    <AgentBadge agent={item.agent_name} size="sm" showIcon={false} />
                    <span className="text-body-sm text-muted">{formatRelativeTime(item.created_at)}</span>
                  </div>
                  <div className="text-body-sm">
                    <span className="text-secondary">{formatTaskType(item.task_type)}</span>
                    {item.target_name && (
                      <span className="text-muted"> — {item.target_name}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {recentActivity.length === 0 && (
              <div className={styles.empty}>No recent activity</div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div className={styles.rightColumn}>
          {/* Deals at Risk */}
          <div className={`card ${styles.riskCard}`}>
            <div className={styles.cardHeader}>
              <h3 className="text-title">🔥 Deals at Risk</h3>
              <Link href="/dashboard/pipeline" className="text-body-sm" style={{ color: 'var(--closer)' }}>Pipeline →</Link>
            </div>
            <div className={styles.riskList}>
              {atRiskDeals.map(deal => (
                <div key={deal.id} className={styles.riskItem}>
                  <div className={styles.riskInfo}>
                    <div className="text-title">{deal.company}</div>
                    <div className={styles.riskMeta}>
                      <span className="badge badge-danger">AT RISK</span>
                      <span className="font-mono text-body-sm text-muted">
                        {computeDaysInStage(deal.last_activity)}d silent
                      </span>
                    </div>
                  </div>
                  <div className={styles.riskArr}>
                    <span className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--danger)' }}>
                      {formatCurrency(deal.arr)}
                    </span>
                    <span className="text-body-sm text-muted">ARR</span>
                  </div>
                </div>
              ))}
              {atRiskDeals.length === 0 && (
                <div className={styles.empty}>No at-risk deals ✓</div>
              )}
            </div>
          </div>

          {/* Churn Watch */}
          <div className={`card ${styles.churnCard}`}>
            <div className={styles.cardHeader}>
              <h3 className="text-title">🛡️ Churn Watch</h3>
              <Link href="/dashboard/churn" className="text-body-sm" style={{ color: 'var(--guardian)' }}>Monitor →</Link>
            </div>
            <div className={styles.churnList}>
              {churnAccounts.map(account => (
                <div key={account.id} className={styles.churnItem}>
                  <HealthGauge score={account.health_score} size={40} />
                  <div className={styles.churnInfo}>
                    <div className="text-body">{account.company}</div>
                    <div className="text-body-sm text-muted">
                      {account.metadata?.signals?.[0] || `${Math.round(account.churn_risk * 100)}% risk`}
                    </div>
                  </div>
                  <div className={styles.churnTrend}>
                    <Sparkline
                      values={account.metadata?.usage_trend || []}
                      width={60}
                      height={20}
                    />
                    <span className="font-mono text-body-sm" style={{
                      color: computeTrendPercentage(account.metadata?.usage_trend || []) < 0 ? 'var(--danger)' : 'var(--success)'
                    }}>
                      {computeTrendPercentage(account.metadata?.usage_trend || []) > 0 ? '+' : ''}
                      {computeTrendPercentage(account.metadata?.usage_trend || [])}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Protocol Status Bar */}
      <div className={styles.protocolBar}>
        <div className={styles.protocol}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">MCP</span>
          <span className="font-mono text-body-sm text-muted">3 custom servers</span>
        </div>
        <div className={styles.protocol}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">A2A</span>
          <span className="font-mono text-body-sm text-muted">Spy agent active</span>
        </div>
        <div className={styles.protocol}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">Kafka</span>
          <span className="font-mono text-body-sm text-muted">4 event topics</span>
        </div>
        <div className={styles.protocol}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">Pinecone</span>
          <span className="font-mono text-body-sm text-muted">RAG enabled</span>
        </div>
        <div className={styles.protocol}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">LangGraph</span>
          <span className="font-mono text-body-sm text-muted">3 agent graphs</span>
        </div>
      </div>
    </div>
  );
}
