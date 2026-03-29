'use client';

import React, { useEffect, useState } from 'react';
import { fetchAccounts, triggerGuardian, Account } from '@/lib/api';
import { formatCurrency, formatRelativeTime, computeChurnCategory, computeTrendPercentage, formatPercent } from '@/lib/utils';
import HealthGauge from '@/components/HealthGauge';
import Sparkline from '@/components/Sparkline';
import styles from './churn.module.css';

interface GuardianResult {
  thread_id: string;
  accounts_analyzed: number;
  flagged_count: number;
  flagged: Array<{ company: string; churn_risk: number }>;
  draft: string | null;
  reasoning: string[];
  status: string;
}

export default function ChurnPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<GuardianResult | null>(null);

  const loadAccounts = async () => {
    try {
      const data = await fetchAccounts();
      setAccounts(data.sort((a, b) => b.churn_risk - a.churn_risk));
      return data;
    } catch (err) {
      console.error(err);
      return [];
    }
  };

  useEffect(() => {
    loadAccounts().finally(() => setLoading(false));
  }, []);

  const runScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const result = await triggerGuardian() as GuardianResult;
      setScanResult(result);
      // Refresh accounts to show updated churn scores
      await loadAccounts();
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const avgHealth = accounts.length > 0
    ? accounts.reduce((s, a) => s + a.health_score, 0) / accounts.length
    : 0;

  const highRisk = accounts.filter(a => computeChurnCategory(a.churn_risk) === 'high');
  const medRisk = accounts.filter(a => computeChurnCategory(a.churn_risk) === 'medium');
  const totalAtRiskArr = [...highRisk, ...medRisk].reduce((s, a) => s + a.arr, 0);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">🛡️ Account Health Monitor</h1>
          <p className="text-body-sm text-muted">
            The Guardian agent continuously scores churn risk across your {accounts.length} accounts using LLM analysis and generates tailored retention plays for high-risk customers.
          </p>
        </div>
        <button className="btn btn-primary" onClick={runScan} disabled={scanning}>
          {scanning ? 'Scanning...' : '🔍 Run Guardian Scan'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className={styles.summaryRow}>
        <div className={`card ${styles.summaryCard}`}>
          <span className="text-label">HIGH RISK</span>
          <span className={styles.summaryValue} style={{ color: 'var(--danger)' }}>{highRisk.length}</span>
          <span className="font-mono text-body-sm text-muted">{formatCurrency(highRisk.reduce((s, a) => s + a.arr, 0))} ARR</span>
        </div>
        <div className={`card ${styles.summaryCard}`}>
          <span className="text-label">MEDIUM RISK</span>
          <span className={styles.summaryValue} style={{ color: 'var(--warning)' }}>{medRisk.length}</span>
          <span className="font-mono text-body-sm text-muted">{formatCurrency(medRisk.reduce((s, a) => s + a.arr, 0))} ARR</span>
        </div>
        <div className={`card ${styles.summaryCard}`}>
          <span className="text-label">AVG HEALTH</span>
          <span className={styles.summaryValue}>{Math.round(avgHealth * 100)}%</span>
          <HealthGauge score={avgHealth} size={36} showLabel={false} />
        </div>
        <div className={`card ${styles.summaryCard}`}>
          <span className="text-label">TOTAL ACCOUNTS</span>
          <span className={styles.summaryValue}>{accounts.length}</span>
          <span className="font-mono text-body-sm text-muted">{formatCurrency(accounts.reduce((s, a) => s + a.arr, 0))} total ARR</span>
        </div>
      </div>

      {/* Guardian Scan Result */}
      {scanResult && (
        <>
        <div className={styles.scanResult}>
          <div className={styles.scanResultHeader}>
            <div>
              <span className="text-title" style={{ fontWeight: 700 }}>🛡️ Guardian Analysis Complete</span>
              <span className="text-body-sm text-muted" style={{ marginLeft: 'var(--space-sm)' }}>
                {scanResult.accounts_analyzed} accounts analyzed · {scanResult.flagged_count} flagged
              </span>
            </div>
            <span className={`badge ${scanResult.status === 'awaiting_approval' ? 'badge-warning' : 'badge-success'}`}>
              {scanResult.status === 'awaiting_approval' ? '⏳ Awaiting Approval' : '✓ Complete'}
            </span>
          </div>
          {scanResult.flagged.length > 0 && (
            <div className={styles.flaggedList}>
              <span className="text-label">FLAGGED ACCOUNTS</span>
              <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap', marginTop: 'var(--space-sm)' }}>
                {scanResult.flagged.map((f, i) => (
                  <span key={i} className="badge badge-danger" style={{ fontSize: '0.8rem' }}>
                    {f.company} ({f.churn_risk ? formatPercent(f.churn_risk) : '?'})
                  </span>
                ))}
              </div>
            </div>
          )}
          {scanResult.reasoning.length > 0 && (
            <div style={{ marginTop: 'var(--space-md)' }}>
              <span className="text-label">REASONING</span>
              <div style={{ marginTop: 'var(--space-sm)', display: 'flex', flexDirection: 'column' as const, gap: 'var(--space-xs)' }}>
                {scanResult.reasoning.map((r, i) => (
                  <div key={i} className="text-body-sm" style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'flex-start' }}>
                    <span style={{ color: 'var(--guardian)', fontWeight: 700 }}>•</span>
                    <span>{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {scanResult.draft && (
            <div style={{ marginTop: 'var(--space-md)' }}>
              <span className="text-label">DRAFT RETENTION PLAY</span>
              <pre style={{
                marginTop: 'var(--space-sm)', padding: 'var(--space-md)',
                background: 'var(--surface-low)', borderRadius: 'var(--radius-md)',
                fontSize: '0.82rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                maxHeight: '200px', overflowY: 'auto', color: 'var(--text-secondary)'
              }}>{scanResult.draft}</pre>
            </div>
          )}
        </div>
        {scanResult.status === 'awaiting_approval' && (
          <a href="/dashboard/approvals" style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: 'var(--space-sm) var(--space-md)',
            background: 'rgba(34, 211, 153, 0.12)', border: '1px solid rgba(34, 211, 153, 0.3)',
            borderRadius: 'var(--radius-md)', color: 'var(--guardian)',
            fontWeight: 600, fontSize: '0.85rem', textDecoration: 'none',
            marginTop: 'var(--space-md)', transition: 'all 0.2s',
          }}>
            ✅ Retention plays ready → Go to Approvals to review
          </a>
        )}
        </>
      )}

      {/* Table */}
      {loading ? (
        <div className="skeleton" style={{ height: 400, borderRadius: 'var(--radius-lg)' }} />
      ) : (
        <div className={`card ${styles.tableCard}`}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Account</th>
                <th>Health</th>
                <th>Churn Risk</th>
                <th>Usage Trend</th>
                <th>ARR</th>
                <th>Top Signal</th>
                <th>Last Login</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map(account => {
                const category = computeChurnCategory(account.churn_risk);
                const trend = account.metadata?.usage_trend || [];
                const trendPct = computeTrendPercentage(trend);
                return (
                  <React.Fragment key={account.id}>
                    <tr
                      className={styles[`row_${category}`]}
                      onClick={() => setExpandedId(expandedId === account.id ? null : account.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td>
                        <div className="text-body" style={{ fontWeight: 600 }}>{account.company}</div>
                        <div className="text-body-sm text-muted">{account.plan}</div>
                      </td>
                      <td><HealthGauge score={account.health_score} size={40} /></td>
                      <td>
                        <span className="font-mono" style={{
                          fontSize: '0.9rem', fontWeight: 700,
                          color: category === 'high' ? 'var(--danger)' : category === 'medium' ? 'var(--warning)' : 'var(--success)',
                        }}>
                          {formatPercent(account.churn_risk)}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                          <Sparkline values={trend} width={70} height={20} />
                          <span className="font-mono text-body-sm" style={{
                            color: trendPct < 0 ? 'var(--danger)' : 'var(--success)',
                          }}>
                            {trendPct > 0 ? '+' : ''}{trendPct}%
                          </span>
                        </div>
                      </td>
                      <td className="font-mono">{formatCurrency(account.arr)}</td>
                      <td className="text-body-sm text-muted" style={{ maxWidth: 200 }}>
                        {account.metadata?.signals?.[0] || '—'}
                      </td>
                      <td className="text-body-sm text-muted">{formatRelativeTime(account.last_login)}</td>
                    </tr>
                    {expandedId === account.id && (
                      <tr key={`${account.id}-expanded`}>
                        <td colSpan={7} className={styles.expandedRow}>
                          <div className={styles.signals}>
                            <span className="text-label">ALL SIGNALS</span>
                            <div className={styles.signalList}>
                              {account.metadata?.signals?.map((sig, i) => (
                                <span key={i} className="badge badge-warning">{sig}</span>
                              )) || <span className="text-muted">No signals</span>}
                            </div>
                          </div>
                          <div className={styles.accountMeta}>
                            <div><span className="text-label">NPS</span> <span className="font-mono">{account.metadata?.nps_score || '—'}</span></div>
                            <div><span className="text-label">CONTRACT ENDS</span> <span className="font-mono">{account.metadata?.contract_end || '—'}</span></div>
                            <div><span className="text-label">SUPPORT TICKETS</span> <span className="font-mono">{account.support_tickets}</span></div>
                            <div><span className="text-label">USAGE</span> <span className="font-mono">{formatPercent(account.usage_pct)}</span></div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
