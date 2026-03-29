'use client';

import { useEffect, useState } from 'react';
import { fetchLeads, fetchLead, triggerProspector, Lead } from '@/lib/api';
import { computeIcpColor, formatPercent } from '@/lib/utils';
import AgentBadge from '@/components/AgentBadge';
import styles from './prospecting.module.css';

interface ProspectorResult {
  thread_id: string;
  lead_id: string;
  action: string;
  draft: string | null;
  reasoning: string[];
  icp_score: number | null;
  status: string;
}

export default function ProspectingPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selected, setSelected] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<ProspectorResult | null>(null);

  const loadLeads = async () => {
    try {
      const data = await fetchLeads();
      setLeads(data);
      return data;
    } catch (err) {
      console.error(err);
      return [];
    }
  };

  useEffect(() => {
    loadLeads()
      .then(data => { if (data.length > 0) setSelected(data[0]); })
      .finally(() => setLoading(false));
  }, []);

  const handleTrigger = async (leadId: string) => {
    setTriggering(leadId);
    setLastResult(null);
    try {
      const result = await triggerProspector(leadId) as ProspectorResult;
      setLastResult(result);

      // Refresh the individual lead to get updated enrichment/icp_score
      try {
        const updatedLead = await fetchLead(leadId);
        setLeads(prev => prev.map(l => l.id === leadId ? { ...l, ...updatedLead } : l));
        setSelected(prev => prev?.id === leadId ? { ...prev, ...updatedLead } : prev);
      } catch {
        // Fallback: refresh all leads
        const data = await loadLeads();
        const refreshed = data.find(l => l.id === leadId);
        if (refreshed) setSelected(refreshed);
      }
    } catch (err) { console.error(err); }
    finally { setTriggering(null); }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">🎯 Prospecting</h1>
          <p className="text-body-sm text-muted">The Prospector agent researches leads, scores them against your ICP using LLM analysis, and drafts personalized multi-email outreach sequences — automatically.</p>
        </div>
      </div>

      <div className={styles.layout}>
        {/* Left — Lead List */}
        <div className={`card ${styles.listPanel}`}>
          <div className={styles.listHeader}>
            <h3 className="text-title">Leads</h3>
          </div>
          {loading ? (
            <div style={{ padding: 'var(--space-lg)' }}>{[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 60, marginBottom: 8, borderRadius: 'var(--radius-md)' }} />)}</div>
          ) : (
            <div className={styles.listBody}>
              {leads.map(lead => (
                <div
                  key={lead.id}
                  className={`${styles.leadItem} ${selected?.id === lead.id ? styles.active : ''}`}
                  onClick={() => setSelected(lead)}
                >
                  <div className={styles.leadInfo}>
                    <div className="text-body" style={{ fontWeight: 600 }}>{lead.company}</div>
                    <div className="text-body-sm text-muted">{lead.contact_name} · {lead.title}</div>
                  </div>
                  <div className={styles.leadRight}>
                    <span className={`badge ${lead.tier === 'A' ? 'badge-success' : lead.tier === 'B' ? 'badge-info' : 'badge-muted'}`}>
                      Tier {lead.tier}
                    </span>
                    {lead.icp_score !== null && (
                      <div className={styles.icpBar}>
                        <div className={styles.icpFill} style={{ width: `${lead.icp_score * 100}%`, backgroundColor: computeIcpColor(lead.icp_score) }} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right — Lead Detail */}
        <div className={`card ${styles.detailPanel}`}>
          {selected ? (
            <>
              <div className={styles.detailHeader}>
                <div>
                  <h2 className="text-headline">{selected.company}</h2>
                  <p className="text-body-sm text-muted">{selected.contact_name} · {selected.email}</p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => handleTrigger(selected.id)}
                  disabled={triggering === selected.id}
                >
                  {triggering === selected.id ? 'Running...' : '🔍 Run Prospector'}
                </button>
              </div>

              {/* Prospector Result Banner */}
              {lastResult && lastResult.lead_id === selected.id && (
                <div className={styles.resultBanner}>
                  <div className={styles.resultHeader}>
                    <span className={`badge ${lastResult.status === 'awaiting_approval' ? 'badge-warning' : lastResult.action === 'no_action' ? 'badge-muted' : 'badge-success'}`}>
                      {lastResult.status === 'awaiting_approval' ? '⏳ Awaiting Approval' : lastResult.action === 'no_action' ? 'No Action Needed' : `✓ ${lastResult.action}`}
                    </span>
                    {lastResult.icp_score !== null && (
                      <span className="font-mono text-body-sm" style={{ color: computeIcpColor(lastResult.icp_score) }}>
                        ICP: {formatPercent(lastResult.icp_score)}
                      </span>
                    )}
                  </div>
                  {lastResult.reasoning.length > 0 && (
                    <div className={styles.resultReasoning}>
                      <span className="text-label">REASONING CHAIN</span>
                      <div className={styles.reasoningSteps}>
                        {lastResult.reasoning.map((step, i) => (
                          <div key={i} className={styles.reasoningStep}>
                            <span className={styles.stepDot} />
                            <span className="text-body-sm">{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {lastResult.draft && (
                    <div className={styles.resultDraft}>
                      <span className="text-label">DRAFT OUTPUT</span>
                      <pre className={styles.draftPre}>{lastResult.draft}</pre>
                    </div>
                  )}
                </div>
              )}
              {lastResult && lastResult.lead_id === selected.id && lastResult.status === 'awaiting_approval' && (
                <a href="/dashboard/approvals" style={{
                  display: 'inline-flex', alignItems: 'center', gap: '8px',
                  padding: 'var(--space-sm) var(--space-md)',
                  background: 'rgba(168, 85, 247, 0.12)', border: '1px solid rgba(168, 85, 247, 0.3)',
                  borderRadius: 'var(--radius-md)', color: 'var(--prospector)',
                  fontWeight: 600, fontSize: '0.85rem', textDecoration: 'none',
                  marginBottom: 'var(--space-md)', transition: 'all 0.2s',
                }}>
                  ✅ Draft ready → Go to Approvals to review
                </a>
              )}

              {selected.enrichment && (
                <div className={styles.enrichment}>
                  <h3 className="text-label" style={{ marginBottom: 'var(--space-md)' }}>COMPANY INTEL</h3>
                  <div className={styles.enrichGrid}>
                    <div className={styles.enrichItem}>
                      <span className="text-label">INDUSTRY</span>
                      <span className="text-body">{selected.enrichment.industry || '—'}</span>
                    </div>
                    <div className={styles.enrichItem}>
                      <span className="text-label">EMPLOYEES</span>
                      <span className="font-mono text-body">{selected.enrichment.employees || '—'}</span>
                    </div>
                    <div className={styles.enrichItem}>
                      <span className="text-label">FUNDING</span>
                      <span className="text-body">{selected.enrichment.funding || '—'}</span>
                    </div>
                    <div className={styles.enrichItem}>
                      <span className="text-label">EST. REVENUE</span>
                      <span className="font-mono text-body">{selected.enrichment.revenue_est || '—'}</span>
                    </div>
                  </div>

                  {selected.enrichment.tech_stack && (
                    <div style={{ marginTop: 'var(--space-lg)' }}>
                      <span className="text-label">TECH STACK</span>
                      <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-sm)', flexWrap: 'wrap' }}>
                        {selected.enrichment.tech_stack.map(t => (
                          <span key={t} className="badge badge-info">{t}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selected.enrichment.signals && (
                    <div style={{ marginTop: 'var(--space-lg)' }}>
                      <span className="text-label">BUY SIGNALS</span>
                      <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-sm)', flexWrap: 'wrap' }}>
                        {selected.enrichment.signals.map((s, i) => (
                          <span key={i} className="badge badge-success">{s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selected.enrichment.contacts && (
                    <div style={{ marginTop: 'var(--space-lg)' }}>
                      <span className="text-label">DECISION MAKERS</span>
                      <div className={styles.contactList}>
                        {selected.enrichment.contacts.map((c, i) => (
                          <div key={i} className={styles.contactCard}>
                            <div className="text-body" style={{ fontWeight: 600 }}>{c.name}</div>
                            <div className="text-body-sm text-muted">{c.title}</div>
                            <div className="text-body-sm" style={{ color: 'var(--closer)' }}>{c.linkedin}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div style={{ padding: 'var(--space-3xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a lead to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
