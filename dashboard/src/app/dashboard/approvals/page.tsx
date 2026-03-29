'use client';

import { useEffect, useState } from 'react';
import { fetchTasks, approveTask, fetchAgentActivity, AgentTask } from '@/lib/api';
import { formatRelativeTime, formatTaskType, getAgentIcon } from '@/lib/utils';
import AgentBadge from '@/components/AgentBadge';
import styles from './approvals.module.css';

const FILTERS = ['all', 'closer', 'prospector', 'guardian'] as const;

export default function ApprovalsPage() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const agent = filter === 'all' ? undefined : filter;

        // Primary: fetch tasks with pending status (backend now checks both statuses + scan fallback)
        let data = await fetchTasks('pending_approval', agent);

        // If still empty, try fetching agent activity that has awaiting/pending status
        if (!data || data.length === 0) {
          const activities = await fetchAgentActivity(agent, 30);
          data = activities
            .filter(a => 
              a.status === 'pending_approval' || 
              a.status === 'awaiting_approval' ||
              a.status === 'queued' ||
              a.draft // Any activity with a draft is likely an approval candidate
            )
            .map(a => ({
              id: a.id,
              agent_name: a.agent_name,
              task_type: a.task_type,
              status: a.status === 'completed' ? 'pending_approval' : a.status,
              target_name: a.target_name,
              draft: a.draft || 'Agent-generated action pending review',
              reasoning: a.reasoning || '',
              created_at: a.created_at,
              model_used: a.model_used,
              tokens_used: a.tokens_used,
              cost: a.cost,
            }));
        }

        setTasks(data);
      } catch (err) {
        console.error('Failed to load approvals:', err);
      } finally {
        setLoading(false);
      }
    }
    load();

    const ws = new WebSocket('ws://localhost:8000/ws/live');
    ws.onmessage = (event) => {
      load();
    };
    return () => ws.close();
  }, [filter]);

  const handleAction = async (taskId: string, approved: boolean) => {
    setActioningId(taskId);
    try {
      await approveTask(taskId, approved, feedback[taskId] || '');
      setTasks(prev => prev.map(t =>
        t.id === taskId ? { ...t, status: approved ? 'approved' : 'rejected' } : t
      ));
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setActioningId(null);
    }
  };

  const pendingCount = tasks.filter(t => t.status === 'pending_approval').length;

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Approval Queue
            {pendingCount > 0 && (
              <span className={styles.countBadge}>{pendingCount}</span>
            )}
          </h1>
          <p className="text-body-sm text-muted">Every AI-generated action pauses here for human review. You approve, reject, or edit before anything is sent — full human-in-the-loop control.</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="tab-bar" style={{ marginBottom: 'var(--space-xl)' }}>
        {FILTERS.map(f => (
          <button
            key={f}
            className={`tab-item ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : `${getAgentIcon(f)} ${f.charAt(0).toUpperCase() + f.slice(1)}`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className={styles.grid}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 260, borderRadius: 'var(--radius-lg)' }} />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>✅</div>
          <h3>All caught up!</h3>
          <p className="text-muted">No pending approvals right now.</p>
        </div>
      ) : (
        <div className={styles.grid}>
          {tasks.map(task => {
            const isResolved = task.status !== 'pending_approval';
            return (
              <div
                key={task.id}
                className={`card ${styles.approvalCard} ${isResolved ? styles.resolved : ''}`}
              >
                {/* Card Header */}
                <div className={styles.cardTop}>
                  <div className={styles.cardTopLeft}>
                    <AgentBadge agent={task.agent_name} />
                    <span className="text-body-sm text-muted">{formatRelativeTime(task.created_at)}</span>
                  </div>
                  {isResolved && (
                    <span className={`badge ${task.status === 'approved' ? 'badge-success' : 'badge-danger'}`}>
                      {task.status === 'approved' ? '✓ Approved' : '✕ Rejected'}
                    </span>
                  )}
                </div>

                {/* Target */}
                <div className={styles.target}>
                  <span className="text-label">TARGET</span>
                  <span className="text-title">{task.target_name || 'Unknown'}</span>
                  <span className="badge badge-muted">{formatTaskType(task.task_type)}</span>
                </div>

                {/* Draft Preview */}
                <div className={styles.draftSection}>
                  <span className="text-label">DRAFT</span>
                  <div className={styles.draftContent}>
                    {task.draft || 'No draft content available'}
                  </div>
                </div>

                {/* Reasoning */}
                <div className={styles.reasoningSection}>
                  <button
                    className={styles.reasoningToggle}
                    onClick={() => setExpandedId(expandedId === task.id ? null : task.id)}
                  >
                    <span className="text-label">💭 REASONING</span>
                    <span>{expandedId === task.id ? '▲' : '▼'}</span>
                  </button>
                  {expandedId === task.id && (
                    <div className={styles.reasoningContent}>
                      {task.reasoning || 'No reasoning provided'}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {!isResolved && (
                  <div className={styles.actions}>
                    <input
                      className={styles.feedbackInput}
                      placeholder="Optional feedback..."
                      value={feedback[task.id] || ''}
                      onChange={e => setFeedback(prev => ({ ...prev, [task.id]: e.target.value }))}
                    />
                    <div className={styles.actionBtns}>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleAction(task.id, false)}
                        disabled={actioningId === task.id}
                      >
                        ✕ Reject
                      </button>
                      <button
                        className="btn btn-success"
                        onClick={() => handleAction(task.id, true)}
                        disabled={actioningId === task.id}
                      >
                        ✓ Approve & Send
                      </button>
                    </div>
                  </div>
                )}

                {/* Meta */}
                {task.model_used && (
                  <div className={styles.meta}>
                    <span className="font-mono text-body-sm text-muted">{task.model_used}</span>
                    {task.tokens_used && <span className="font-mono text-body-sm text-muted">{task.tokens_used} tokens</span>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
