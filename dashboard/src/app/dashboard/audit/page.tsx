'use client';

import React, { useEffect, useState } from 'react';
import { fetchAuditTrail, fetchAgentActivity, AgentTask } from '@/lib/api';
import { formatDateTime, formatTaskType, formatTokens, formatCost, getAgentIcon } from '@/lib/utils';
import AgentBadge from '@/components/AgentBadge';
import styles from './audit.module.css';

const AGENTS = ['all', 'closer', 'prospector', 'guardian', 'spy'];

export default function AuditPage() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const agent = filter === 'all' ? undefined : filter;

    // Try audit trail first, fall back to agent activity (scan_reports) if empty
    fetchAuditTrail(agent)
      .then(data => {
        if (data && data.length > 0) {
          setTasks(data);
        } else {
          // Fallback — use agent activity which pulls from scan_reports
          return fetchAgentActivity(agent, 50).then(activities => {
            setTasks(activities.map(a => ({
              id: a.id,
              agent_name: a.agent_name,
              task_type: a.task_type,
              status: a.status,
              target_name: a.target_name,
              draft: a.draft || '',
              reasoning: a.reasoning,
              created_at: a.created_at,
              model_used: a.model_used,
              tokens_used: a.tokens_used,
              cost: a.cost,
            })));
          });
        }
      })
      .catch(err => {
        console.error('Audit load failed:', err);
        // Last resort fallback
        fetchAgentActivity(agent, 50)
          .then(activities => setTasks(activities as AgentTask[]))
          .catch(() => setTasks([]));
      })
      .finally(() => setLoading(false));
  }, [filter]);

  const totalTokens = tasks.reduce((sum, t) => sum + (t.tokens_used || 0), 0);
  const totalCost = tasks.reduce((sum, t) => sum + (t.cost || 0), 0);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">📋 Audit Trail</h1>
          <p className="text-body-sm text-muted">
            Full accountability — every LLM call, token cost, and agent decision is recorded. {tasks.length} entries · {formatTokens(totalTokens)} tokens · {formatCost(totalCost)} total cost.
          </p>
        </div>
      </div>

      <div className="tab-bar" style={{ marginBottom: 'var(--space-xl)' }}>
        {AGENTS.map(a => (
          <button key={a} className={`tab-item ${filter === a ? 'active' : ''}`} onClick={() => setFilter(a)}>
            {a === 'all' ? 'All Agents' : `${getAgentIcon(a)} ${a.charAt(0).toUpperCase() + a.slice(1)}`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 400, borderRadius: 'var(--radius-lg)' }} />
      ) : (
        <div className={`card ${styles.tableCard}`}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Agent</th>
                <th>Action</th>
                <th>Target</th>
                <th>Model</th>
                <th>Tokens</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map(task => (
                <React.Fragment key={task.id}>
                  <tr onClick={() => setExpandedId(expandedId === task.id ? null : task.id)} style={{ cursor: 'pointer' }}>
                    <td className="font-mono text-body-sm">{formatDateTime(task.created_at)}</td>
                    <td><AgentBadge agent={task.agent_name} size="sm" /></td>
                    <td className="text-body-sm">{formatTaskType(task.task_type)}</td>
                    <td className="text-body-sm">{task.target_name || '—'}</td>
                    <td><span className="badge badge-muted font-mono">{task.model_used || '—'}</span></td>
                    <td className="font-mono text-body-sm">{task.tokens_used ? formatTokens(task.tokens_used) : '—'}</td>
                    <td className="font-mono text-body-sm">{task.cost ? formatCost(task.cost) : '—'}</td>
                    <td>
                      <span className={`badge ${task.status === 'approved' ? 'badge-success' : task.status === 'rejected' ? 'badge-danger' : task.status === 'pending_approval' ? 'badge-warning' : 'badge-muted'}`}>
                        {task.status}
                      </span>
                    </td>
                  </tr>
                  {expandedId === task.id && (
                    <tr key={`${task.id}-exp`}>
                      <td colSpan={8} className={styles.expandedCell}>
                        <div className={styles.expandedContent}>
                          <div>
                            <span className="text-label">REASONING</span>
                            <div className={styles.reasoningText}>{task.reasoning || 'No reasoning recorded'}</div>
                          </div>
                          {task.draft && (
                            <div>
                              <span className="text-label">DRAFT</span>
                              <div className={styles.draftText}>{task.draft}</div>
                            </div>
                          )}
                          {task.feedback && (
                            <div>
                              <span className="text-label">FEEDBACK</span>
                              <div className="text-body-sm">{task.feedback}</div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
