'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchDeals, fetchDealTimeline, triggerCloser, Deal, TimelineEvent } from '@/lib/api';
import { formatCurrency, computeDaysInStage, computeStageStats, formatStage, computeRiskBadge } from '@/lib/utils';
import AgentBadge from '@/components/AgentBadge';
import styles from './pipeline.module.css';

const STAGES = ['discovery', 'proposal', 'negotiation', 'closed_won'];

function formatTaskType(t: string): string {
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function timelineIcon(status: string): string {
  switch (status) {
    case 'approved': return '✅';
    case 'rejected': return '❌';
    case 'pending_approval': return '⏳';
    case 'awaiting_approval': return '⏳';
    default: return '🔵';
  }
}

export default function PipelinePage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'email' | 'agent'>('timeline');
  const [search, setSearch] = useState('');
  const [triggeringId, setTriggeringId] = useState<string | null>(null);

  useEffect(() => {
    fetchDeals()
      .then(data => setDeals(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const openDeal = async (deal: Deal) => {
    // Parse closer_thread and agent_log if they come as JSON strings from the DB
    const parsed = { ...deal };
    if (typeof parsed.closer_thread === 'string') {
      try { parsed.closer_thread = JSON.parse(parsed.closer_thread); } catch { parsed.closer_thread = []; }
    }
    if (!Array.isArray(parsed.closer_thread)) parsed.closer_thread = [];

    if (typeof parsed.agent_log === 'string') {
      try { parsed.agent_log = JSON.parse(parsed.agent_log as unknown as string); } catch { parsed.agent_log = []; }
    }
    if (!Array.isArray(parsed.agent_log)) parsed.agent_log = [];

    setSelectedDeal(parsed);
    setActiveTab('timeline');
    setTimelineLoading(true);
    try {
      const tl = await fetchDealTimeline(deal.id);
      setTimeline(tl);
    } catch {
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  const handleTriggerCloser = async (e: React.MouseEvent, dealId: string) => {
    e.stopPropagation();
    setTriggeringId(dealId);
    try {
      await triggerCloser(dealId);
      // Refresh deals
      const updated = await fetchDeals();
      setDeals(updated);
    } catch (err) {
      console.error('Closer trigger failed:', err);
    } finally {
      setTriggeringId(null);
    }
  };

  // Compute stats
  const activeDeals = deals.filter(d => !d.stage.startsWith('closed'));
  const pipelineValue = activeDeals.reduce((s, d) => s + d.arr, 0);
  const avgCycleDays = activeDeals.length > 0
    ? Math.round(activeDeals.reduce((s, d) => s + computeDaysInStage(d.last_activity), 0) / activeDeals.length)
    : 0;
  const stageStats = computeStageStats(deals);

  // Search filter
  const filteredDeals = search.trim()
    ? deals.filter(d => d.company.toLowerCase().includes(search.toLowerCase()))
    : deals;
  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = filteredDeals.filter(d => d.stage === stage);
    return acc;
  }, {} as Record<string, Deal[]>);

  return (
    <div className="page-content">
      {/* Header + Search */}
      <div className={styles.topBar}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Deal Pipeline</h1>
          <p className="text-body-sm text-muted" style={{ margin: '4px 0 0 0' }}>The Closer agent monitors stalled deals, classifies risk with LLM analysis, and drafts re-engagement emails using RAG context from your knowledge base.</p>
        </div>
        <div className={styles.searchBox}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            className={styles.searchInput}
            type="text"
            placeholder="Search deals, companies…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Stats Bar */}
      <div className={styles.statsBar}>
        <div className={styles.statItem}>
          <span className="text-label">PIPELINE VALUE</span>
          <div className={styles.statValue}>
            <span className="font-mono">{formatCurrency(pipelineValue)}</span>
            <span className={styles.trendUp}>↑ 12%</span>
          </div>
        </div>
        <div className={styles.statItem}>
          <span className="text-label">ACTIVE DEALS</span>
          <span className={`font-mono ${styles.statBig}`}>{activeDeals.length}</span>
        </div>
        <div className={styles.statItem}>
          <span className="text-label">AVG. CYCLE</span>
          <span className={`font-mono ${styles.statBig}`}>{avgCycleDays}d</span>
        </div>
      </div>

      {/* Kanban */}
      {loading ? (
        <div className={styles.kanban}>
          {STAGES.map(s => (
            <div key={s} className="skeleton" style={{ height: 400, borderRadius: 'var(--radius-lg)' }} />
          ))}
        </div>
      ) : (
        <div className={styles.kanban}>
          {STAGES.map(stage => (
            <div key={stage} className={styles.column}>
              <div className={styles.columnHeader}>
                <h3 className={styles.columnTitle}>{formatStage(stage)}</h3>
                <div className={styles.columnMeta}>
                  <span className="badge badge-muted">{stageStats[stage]?.count || 0}</span>
                  <span className="font-mono text-body-sm text-muted">
                    {formatCurrency(stageStats[stage]?.totalArr || 0)}
                  </span>
                </div>
              </div>
              <div className={styles.columnBody}>
                {dealsByStage[stage]?.map(deal => {
                  const risk = computeRiskBadge(deal.risk_level);
                  const days = computeDaysInStage(deal.last_activity);
                  return (
                    <div
                      key={deal.id}
                      className={`${styles.dealCard} card`}
                      onClick={() => openDeal(deal)}
                    >
                      <div className={styles.dealTop}>
                        <span className={styles.dealCompany}>{deal.company}</span>
                        {deal.risk_level !== 'healthy' && (
                          <span className={styles.riskDot} data-risk={deal.risk_level} />
                        )}
                      </div>
                      {deal.contact_name && (
                        <div className={styles.dealContact}>
                          {deal.contact_name}{deal.contact_title ? ` (${deal.contact_title})` : ''}
                        </div>
                      )}
                      <div className={styles.dealBottom}>
                        <div className={styles.dealBadges}>
                          <span className={styles.arrBadge}>{formatCurrency(deal.arr)} ARR</span>
                          <span className={`badge ${risk.className}`} style={{ fontSize: '0.65rem' }}>{risk.label}</span>
                        </div>
                        <span className="text-body-sm text-muted">{days}d in stage</span>
                      </div>
                      <button
                        className={styles.runCloserBtn}
                        onClick={(e) => handleTriggerCloser(e, deal.id)}
                        disabled={triggeringId === deal.id}
                      >
                        {triggeringId === deal.id ? '⏳ Running...' : '⚡ Run Closer'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Deal Detail Slide-over */}
      {selectedDeal && (
        <>
          <div className={styles.overlay} onClick={() => setSelectedDeal(null)} />
          <div className={`${styles.slideOver} slide-right`}>
            {/* Header */}
            <div className={styles.slideHeader}>
              <div>
                <h2 className={styles.slideTitle}>{selectedDeal.company}</h2>
                <div className={styles.slideBadges}>
                  <span className="badge badge-muted">{formatStage(selectedDeal.stage)}</span>
                  <span className={`badge ${computeRiskBadge(selectedDeal.risk_level).className}`}>
                    {computeRiskBadge(selectedDeal.risk_level).label}
                  </span>
                </div>
                <div className={styles.slideMeta}>
                  <span>ARR: <strong className="font-mono">{formatCurrency(selectedDeal.arr)}</strong></span>
                  {selectedDeal.id && <span className="text-muted">OPP-{selectedDeal.id.slice(0, 4).toUpperCase()}</span>}
                </div>
              </div>
              <button className="btn btn-ghost" onClick={() => setSelectedDeal(null)}>✕</button>
            </div>

            {/* Tabs */}
            <div className={styles.tabBar}>
              <button
                className={`${styles.tab} ${activeTab === 'timeline' ? styles.tabActive : ''}`}
                onClick={() => setActiveTab('timeline')}
              >Timeline</button>
              <button
                className={`${styles.tab} ${activeTab === 'email' ? styles.tabActive : ''}`}
                onClick={() => setActiveTab('email')}
              >Email History</button>
              <button
                className={`${styles.tab} ${activeTab === 'agent' ? styles.tabActive : ''}`}
                onClick={() => setActiveTab('agent')}
              >Agent Log</button>
            </div>

            {/* Tab Content */}
            <div className={styles.slideContent}>
              {/* TIMELINE TAB */}
              {activeTab === 'timeline' && (
                <div className={styles.timelineContainer}>
                  {timelineLoading ? (
                    <div style={{ padding: 'var(--space-lg)', textAlign: 'center' }} className="text-muted">Loading timeline...</div>
                  ) : timeline.length === 0 ? (
                    <div style={{ padding: 'var(--space-lg)', textAlign: 'center' }} className="text-muted">
                      No agent activity yet. Trigger the Closer to begin.
                    </div>
                  ) : (
                    timeline.map((evt) => (
                      <div key={evt.id} className={styles.timelineItem}>
                        <div className={styles.timelineDot}>
                          <span>{timelineIcon(evt.status)}</span>
                        </div>
                        <div className={styles.timelineContent}>
                          <div className={styles.timelineHeader}>
                            <span className="text-body-sm text-muted">
                              {new Date(evt.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                            <AgentBadge agent={evt.agent_name} size="sm" />
                          </div>
                          <div className={styles.timelineTitle}>
                            {formatTaskType(evt.task_type)}
                            {evt.status === 'approved' && <span className={styles.sentTag}>SENT</span>}
                          </div>
                          {evt.draft && (
                            <div className={styles.timelineDesc}>
                              &quot;{evt.draft.length > 120 ? evt.draft.slice(0, 120) + '…' : evt.draft}&quot;
                            </div>
                          )}
                          {evt.reasoning && (
                            <div className={styles.timelineReason}>
                              {evt.reasoning.length > 150 ? evt.reasoning.slice(0, 150) + '…' : evt.reasoning}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                  <Link href="/dashboard/thinking" className={styles.viewThinking}>
                    View Full Thinking →
                  </Link>
                </div>
              )}

              {/* EMAIL HISTORY TAB */}
              {activeTab === 'email' && (
                <div className={styles.emailContainer}>
                  {!selectedDeal.closer_thread || selectedDeal.closer_thread.length === 0 ? (
                    <div style={{ padding: 'var(--space-lg)', textAlign: 'center' }} className="text-muted">
                      No email history for this deal yet.
                    </div>
                  ) : (
                    selectedDeal.closer_thread.map((email, i) => (
                      <div key={i} className={styles.emailItem}>
                        <div className={styles.emailMeta}>
                          <span className={styles.emailFrom}>{email.from}</span>
                          <span className="text-body-sm text-muted">{email.date}</span>
                        </div>
                        <div className={styles.emailSubject}>{email.subject}</div>
                        <div className={styles.emailBody}>{email.body}</div>
                        {email.to && (
                          <div className={styles.emailTo}>To: {email.to}</div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* AGENT LOG TAB */}
              {activeTab === 'agent' && (
                <div className={styles.agentLogContainer}>
                  {!selectedDeal.agent_log || selectedDeal.agent_log.length === 0 ? (
                    <div style={{ padding: 'var(--space-lg)', textAlign: 'center' }} className="text-muted">
                      No agent log entries for this deal.
                    </div>
                  ) : (
                    selectedDeal.agent_log.map((entry: Record<string, string>, i: number) => {
                      const parsed = typeof entry === 'string' ? (() => { try { return JSON.parse(entry); } catch { return { raw: entry }; } })() : entry;
                      return (
                        <div key={i} className={styles.logEntry}>
                          <div style={{ padding: 'var(--space-md) var(--space-lg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-ghost)' }}>
                            <span style={{ fontWeight: 700, fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              🤖 {parsed.agent || 'system'}
                            </span>
                            <span className="text-body-sm text-muted">
                              {parsed.timestamp ? new Date(parsed.timestamp).toLocaleString() : '—'}
                            </span>
                          </div>
                          <div style={{ padding: 'var(--space-md) var(--space-lg)' }}>
                            <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '4px', color: 'var(--accent)' }}>
                              {(parsed.action || 'unknown').replace(/_/g, ' ').toUpperCase()}
                            </div>
                            <div className="text-body-sm text-muted" style={{ lineHeight: 1.5 }}>
                              {parsed.reasoning || JSON.stringify(parsed, null, 2)}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className={styles.slideActions}>
              <button
                className={styles.updateStageBtn}
                onClick={(e) => handleTriggerCloser(e, selectedDeal.id)}
                disabled={triggeringId === selectedDeal.id}
              >
                {triggeringId === selectedDeal.id ? '⏳ Running Closer...' : '⚡ Run Closer Agent'}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
