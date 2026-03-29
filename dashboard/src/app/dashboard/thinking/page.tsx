'use client';

import { useEffect, useState } from 'react';
import { fetchAgentActivity, fetchDeals, AgentActivity, Deal } from '@/lib/api';
import { formatRelativeTime, formatTaskType, getAgentIcon, getAgentColor, formatTokens, formatCost } from '@/lib/utils';
import AgentBadge from '@/components/AgentBadge';
import styles from './thinking.module.css';

export default function ThinkingPage() {
  const [tasks, setTasks] = useState<AgentActivity[]>([]);
  const [selectedTask, setSelectedTask] = useState<AgentActivity | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchAgentActivity(agentFilter === 'all' ? undefined : agentFilter),
      fetchDeals(),
    ]).then(([taskData, dealData]) => {
      setTasks(taskData);
      
      const parsedDeals = dealData.map(d => {
        const pd = { ...d };
        if (typeof pd.closer_thread === 'string') {
          try { pd.closer_thread = JSON.parse(pd.closer_thread); } catch { pd.closer_thread = []; }
        }
        if (!Array.isArray(pd.closer_thread)) pd.closer_thread = [];
        return pd;
      });
      setDeals(parsedDeals);

      if (taskData.length > 0 && (!selectedTask || !taskData.find(t => t.id === selectedTask.id))) {
        setSelectedTask(taskData[0]);
      }
    }).catch(console.error)
    .finally(() => setLoading(false));
  }, [agentFilter]);

  const relatedDeal = selectedTask?.target_name
    ? deals.find(d => d.company === selectedTask.target_name)
    : null;

  // Parse reasoning into steps (split by newlines or numbered items)
  const reasoningSteps = selectedTask?.reasoning
    ? selectedTask.reasoning.split(/\n(?=\d+\.|Step |[-•])/).filter(Boolean)
    : [];

  const totalTokens = tasks.reduce((s, t) => s + (t.tokens_used || 0), 0);
  const totalCost = tasks.reduce((s, t) => s + (t.cost || 0), 0);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">🧠 Agent Thinking</h1>
          <p className="text-body-sm text-muted">See exactly how each agent reasons — every step of the LangGraph execution chain is logged, traceable, and explainable.</p>
        </div>
        <div className="tab-bar">
          {['all', 'closer', 'prospector', 'guardian'].map(a => (
            <button key={a} className={`tab-item ${agentFilter === a ? 'active' : ''}`} onClick={() => setAgentFilter(a)}>
              {a === 'all' ? 'All Agents' : `${getAgentIcon(a)} ${a.charAt(0).toUpperCase() + a.slice(1)}`}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 600, borderRadius: 'var(--radius-lg)' }} />
      ) : tasks.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-3xl)' }}>
          <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: 'var(--space-md)' }}>🧠</span>
          <p className="text-muted">No agent activity recorded yet. Run an orchestrator scan to generate reasoning data.</p>
        </div>
      ) : (
        <div className={styles.layout}>
          {/* Left — Timeline */}
          <div className={`card ${styles.timelinePanel}`}>
            <div className={styles.taskSelector}>
              <select
                className={styles.selector}
                value={selectedTask?.id || ''}
                onChange={e => setSelectedTask(tasks.find(t => t.id === e.target.value) || null)}
              >
                {tasks.map(t => (
                  <option key={t.id} value={t.id}>
                    {getAgentIcon(t.agent_name)} {formatTaskType(t.task_type)} — {t.target_name || 'Unknown'}
                  </option>
                ))}
              </select>
            </div>

            {selectedTask && (
              <div className={styles.timeline}>
                <div className={styles.timelineHeader}>
                  <AgentBadge agent={selectedTask.agent_name} />
                  <span className={`badge ${selectedTask.status === 'approved' || selectedTask.status === 'awaiting_approval' ? 'badge-success' : selectedTask.status === 'pending_approval' ? 'badge-warning' : 'badge-muted'}`}>
                    {selectedTask.status}
                  </span>
                  <span className="text-body-sm text-muted">{formatRelativeTime(selectedTask.created_at)}</span>
                </div>

                {/* Source indicator */}
                {selectedTask.source === 'scan_report' && (
                  <div className={styles.sourceTag}>
                    <span className="badge badge-muted" style={{ fontSize: '0.65rem' }}>
                      📊 From Scan #{selectedTask.scan_number}
                    </span>
                    {selectedTask.trigger && (
                      <span className="text-body-sm text-muted" style={{ marginLeft: 'var(--space-sm)' }}>
                        Trigger: {selectedTask.trigger}
                      </span>
                    )}
                  </div>
                )}

                {/* Reasoning Steps */}
                <div className={styles.steps}>
                  {reasoningSteps.length > 0 ? reasoningSteps.map((step, i) => (
                    <div key={i} className={styles.step}>
                      <div className={styles.stepLine}>
                        <div className={styles.stepDot} style={{ background: getAgentColor(selectedTask.agent_name) }} />
                        {i < reasoningSteps.length - 1 && <div className={styles.stepConnector} />}
                      </div>
                      <div className={styles.stepContent}>
                        <div className={styles.stepHeader}>
                          <span className="text-body-sm" style={{ fontWeight: 600 }}>Step {i + 1}</span>
                        </div>
                        <div className="text-body-sm text-secondary" style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                          {step.trim()}
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div className={styles.step}>
                      <div className={styles.stepLine}>
                        <div className={styles.stepDot} style={{ background: getAgentColor(selectedTask.agent_name) }} />
                      </div>
                      <div className={styles.stepContent}>
                        <div className="text-body-sm text-muted">
                          {selectedTask.reasoning || 'No reasoning chain recorded for this task'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Draft Output */}
                {selectedTask.draft && (
                  <div className={styles.outputSection}>
                    <span className="text-label">📝 GENERATED OUTPUT</span>
                    <div className={styles.outputContent}>{selectedTask.draft}</div>
                  </div>
                )}

                {/* Audit Strip */}
                <div className={styles.auditStrip}>
                  <div className={styles.auditItem}>
                    <span className="text-label">MODEL</span>
                    <span className="font-mono text-body-sm">{selectedTask.model_used || '—'}</span>
                  </div>
                  <div className={styles.auditItem}>
                    <span className="text-label">TOKENS</span>
                    <span className="font-mono text-body-sm">{selectedTask.tokens_used ? formatTokens(selectedTask.tokens_used) : '—'}</span>
                  </div>
                  <div className={styles.auditItem}>
                    <span className="text-label">COST</span>
                    <span className="font-mono text-body-sm">{selectedTask.cost ? formatCost(selectedTask.cost) : '—'}</span>
                  </div>
                  <div className={styles.auditItem}>
                    <span className="text-label">STEPS</span>
                    <span className="font-mono text-body-sm">{reasoningSteps.length}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right — Context */}
          <div className={styles.contextPanel}>
            {relatedDeal ? (
              <div className={`card ${styles.contextCard}`}>
                <div className={styles.contextHeader}>
                  <span className="text-label">DEAL CONTEXT</span>
                </div>
                <div className={styles.contextBody}>
                  <div className={styles.ctxRow}><span className="text-label">COMPANY</span><span>{relatedDeal.company}</span></div>
                  <div className={styles.ctxRow}><span className="text-label">STAGE</span><span>{relatedDeal.stage}</span></div>
                  <div className={styles.ctxRow}><span className="text-label">ARR</span><span className="font-mono">${relatedDeal.arr.toLocaleString()}</span></div>
                  <div className={styles.ctxRow}><span className="text-label">RISK</span><span className={`badge badge-${relatedDeal.risk_level === 'at_risk' ? 'danger' : relatedDeal.risk_level === 'stalled' ? 'warning' : 'success'}`}>{relatedDeal.risk_level}</span></div>
                </div>

                {relatedDeal.closer_thread && relatedDeal.closer_thread.length > 0 && (
                  <div className={styles.threadSection}>
                    <span className="text-label">EMAIL THREAD</span>
                    {relatedDeal.closer_thread.map((email, i) => (
                      <div key={i} className={styles.emailItem}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span className="text-body-sm" style={{ fontWeight: 600 }}>{email.from}</span>
                          <span className="text-body-sm text-muted">{email.date}</span>
                        </div>
                        <div className="text-body-sm" style={{ fontWeight: 500, margin: '2px 0' }}>{email.subject}</div>
                        <div className="text-body-sm text-muted">{email.body}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : selectedTask ? (
              <div className={`card ${styles.contextCard}`}>
                <div className={styles.contextHeader}>
                  <span className="text-label">DISPATCH CONTEXT</span>
                </div>
                <div className={styles.contextBody}>
                  <div className={styles.ctxRow}><span className="text-label">TARGET</span><span>{selectedTask.target_name}</span></div>
                  <div className={styles.ctxRow}><span className="text-label">AGENT</span><span style={{ textTransform: 'capitalize' }}>{selectedTask.agent_name}</span></div>
                  <div className={styles.ctxRow}><span className="text-label">ACTION</span><span style={{ textTransform: 'capitalize' }}>{selectedTask.task_type}</span></div>
                  {selectedTask.trigger && (
                    <div className={styles.ctxRow}><span className="text-label">TRIGGER</span><span className="text-body-sm">{selectedTask.trigger}</span></div>
                  )}
                  {selectedTask.scan_number && (
                    <div className={styles.ctxRow}><span className="text-label">SCAN</span><span className="font-mono">#{selectedTask.scan_number}</span></div>
                  )}
                </div>
              </div>
            ) : (
              <div className={`card ${styles.contextCard}`}>
                <div className={styles.contextBody} style={{ textAlign: 'center', padding: 'var(--space-3xl)', color: 'var(--text-muted)' }}>
                  Select a task to view context
                </div>
              </div>
            )}

            {/* Global Stats */}
            <div className={`card ${styles.globalStats}`}>
              <h3 className="text-label" style={{ marginBottom: 'var(--space-md)' }}>SESSION TOTALS</h3>
              <div className={styles.statGrid}>
                <div><span className="text-label">TASKS</span><span className="font-mono">{tasks.length}</span></div>
                <div><span className="text-label">TOKENS</span><span className="font-mono">{formatTokens(totalTokens)}</span></div>
                <div><span className="text-label">COST</span><span className="font-mono">{formatCost(totalCost)}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
