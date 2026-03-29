'use client';

import { useEffect, useState, useRef } from 'react';
import { fetchOrchestratorHistory, triggerOrchestratorScan, fetchOrchestratorStatus, orchestratorChat, ScanReport } from '@/lib/api';
import { formatDateTime, formatRelativeTime } from '@/lib/utils';
import styles from './orchestrator.module.css';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function OrchestratorPage() {
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      fetchOrchestratorHistory(),
      fetchOrchestratorStatus().catch(() => null),
    ]).then(([history, statusData]) => {
      setScans(history);
      if (statusData) setStatus(statusData as Record<string, unknown>);
    }).catch(console.error)
    .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const runScan = async () => {
    setScanning(true);
    try {
      await triggerOrchestratorScan();
      const updated = await fetchOrchestratorHistory();
      setScans(updated);
    } catch (err) { console.error(err); }
    finally { setScanning(false); }
  };

  const sendChat = async () => {
    if (!chatInput.trim() || chatSending) return;
    const userMsg: ChatMessage = {
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatSending(true);
    try {
      const response = await orchestratorChat(userMsg.content) as Record<string, string>;
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.response || response.message || JSON.stringify(response),
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setChatSending(false);
    }
  };

  const totalDispatched = scans.reduce((s, r) => s + (r.total_dispatched || 0), 0);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">🧠 Orchestrator Control Center</h1>
          <p className="text-body-sm text-muted">
            {scans.length} scans completed · {totalDispatched} total dispatches
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
          <button className="btn btn-primary" onClick={() => setChatOpen(!chatOpen)}>
            💬 {chatOpen ? 'Close Chat' : 'Chat with Orchestrator'}
          </button>
          <button className="btn btn-primary" onClick={runScan} disabled={scanning}>
            {scanning ? '⏳ Scanning...' : '🚀 Run Full Scan'}
          </button>
        </div>
      </div>

      {/* Status Strip */}
      <div className={styles.statusStrip}>
        <div className={styles.statusItem}>
          <span className="dot dot-green pulse-dot" />
          <span className="text-body-sm">Orchestrator Online</span>
        </div>
        <div className={styles.statusItem}>
          <span className="text-label">LAST SCAN</span>
          <span className="font-mono text-body-sm">{scans.length > 0 ? formatRelativeTime(scans[0].started_at) : 'Never'}</span>
        </div>
        <div className={styles.statusItem}>
          <span className="text-label">TOTAL SCANS</span>
          <span className="font-mono text-body-sm">{scans.length}</span>
        </div>
        <div className={styles.statusItem}>
          <span className="text-label">DISPATCHES</span>
          <span className="font-mono text-body-sm">{totalDispatched}</span>
        </div>
      </div>

      {/* Main Content + Chat Panel */}
      <div className={styles.mainLayout}>
        {/* Scan History */}
        <div className={styles.scanSection}>
          {loading ? (
            <div className="skeleton" style={{ height: 300, borderRadius: 'var(--radius-lg)' }} />
          ) : (
            <div className={styles.scanGrid}>
              {scans.map(scan => (
                <div key={scan.id} className={`card ${styles.scanCard}`}>
                  <div className={styles.scanHeader}>
                    <div>
                      <span className="text-title">Scan #{scan.scan_number}</span>
                      <span className={`badge ${scan.status === 'completed' ? 'badge-success' : scan.status === 'running' ? 'badge-warning' : 'badge-muted'}`} style={{ marginLeft: 'var(--space-sm)' }}>
                        {scan.status}
                      </span>
                    </div>
                    <span className="text-body-sm text-muted">{formatDateTime(scan.started_at)}</span>
                  </div>

                  <div className={styles.scanStats}>
                    <div className={styles.scanStat}>
                      <span className="text-label">DEALS</span>
                      <div className={styles.scanStatValue}>
                        <span className="font-mono">{scan.deals_scanned}</span>
                        <span className="text-body-sm text-muted">scanned</span>
                        <span className="font-mono" style={{ color: 'var(--closer)' }}>{scan.deals_dispatched}</span>
                        <span className="text-body-sm text-muted">dispatched</span>
                      </div>
                    </div>
                    <div className={styles.scanStat}>
                      <span className="text-label">LEADS</span>
                      <div className={styles.scanStatValue}>
                        <span className="font-mono">{scan.leads_scanned}</span>
                        <span className="text-body-sm text-muted">scanned</span>
                        <span className="font-mono" style={{ color: 'var(--prospector)' }}>{scan.leads_dispatched}</span>
                        <span className="text-body-sm text-muted">dispatched</span>
                      </div>
                    </div>
                    <div className={styles.scanStat}>
                      <span className="text-label">ACCOUNTS</span>
                      <div className={styles.scanStatValue}>
                        <span className="font-mono">{scan.accounts_scanned}</span>
                        <span className="text-body-sm text-muted">scanned</span>
                        <span className="font-mono" style={{ color: 'var(--guardian)' }}>{scan.accounts_dispatched}</span>
                        <span className="text-body-sm text-muted">dispatched</span>
                      </div>
                    </div>
                  </div>

                  {scan.summary && (
                    <div className={styles.scanSummary}>
                      <span className="text-label">SUMMARY</span>
                      <p className="text-body-sm text-secondary">{scan.summary}</p>
                    </div>
                  )}

                  <div className={styles.scanFooter}>
                    <span className="font-mono text-body-sm text-muted">
                      Total dispatched: {scan.total_dispatched}
                    </span>
                    <span className="text-body-sm text-muted">
                      by {scan.triggered_by}
                    </span>
                  </div>
                </div>
              ))}

              {scans.length === 0 && (
                <div className={styles.empty}>
                  <span style={{ fontSize: '2rem' }}>🧠</span>
                  <p className="text-muted">No scans yet. Click &ldquo;Run Full Scan&rdquo; to begin.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Slide-out Chat Panel */}
        {chatOpen && (
          <div className={styles.chatPanel}>
            <div className={styles.chatHeader}>
              <div>
                <span className="text-title" style={{ fontSize: '0.9rem' }}>🧠 Orchestrator Chat</span>
                <p className="text-body-sm text-muted">Ask about scans, agents, or system status</p>
              </div>
              <button className={styles.chatClose} onClick={() => setChatOpen(false)}>✕</button>
            </div>

            <div className={styles.chatMessages}>
              {chatMessages.length === 0 && (
                <div className={styles.chatEmpty}>
                  <span style={{ fontSize: '1.5rem' }}>💬</span>
                  <p className="text-body-sm text-muted">Ask me anything about the system</p>
                  <div className={styles.chatSuggestions}>
                    {['What is the current system status?', 'Show me recent dispatches', 'Which deals need attention?'].map(s => (
                      <button key={s} className={styles.chatSuggestion} onClick={() => { setChatInput(s); }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} className={`${styles.chatMsg} ${styles[`chatMsg_${msg.role}`]}`}>
                  <span className={styles.chatMsgRole}>{msg.role === 'user' ? '👤' : '🧠'}</span>
                  <div className={styles.chatMsgContent}>
                    <div className="text-body-sm" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.content}</div>
                    <span className="text-body-sm text-muted" style={{ fontSize: '0.65rem' }}>{formatRelativeTime(msg.timestamp)}</span>
                  </div>
                </div>
              ))}
              {chatSending && (
                <div className={`${styles.chatMsg} ${styles.chatMsg_assistant}`}>
                  <span className={styles.chatMsgRole}>🧠</span>
                  <div className={styles.chatMsgContent}>
                    <div className={styles.chatTyping}>
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className={styles.chatInputBar}>
              <input
                type="text"
                placeholder="Ask the orchestrator..."
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendChat()}
                className={styles.chatInputField}
                disabled={chatSending}
              />
              <button className={styles.chatSendBtn} onClick={sendChat} disabled={chatSending || !chatInput.trim()}>
                ↑
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
