'use client';

import { useState } from 'react';
import styles from './settings.module.css';

const MCP_SERVERS = [
  { name: 'HubSpot', type: 'CRM', purpose: 'Deal & contact sync', status: 'active' },
  { name: 'Salesforce', type: 'CRM', purpose: 'Pipeline management', status: 'active' },
  { name: 'SendGrid', type: 'Email', purpose: 'Outbound sending', status: 'active' },
  { name: 'Apollo.io', type: 'Enrichment', purpose: 'Contact enrichment', status: 'active' },
  { name: 'Calendly', type: 'Scheduling', purpose: 'Meeting booking', status: 'active' },
  { name: 'Mixpanel', type: 'Analytics', purpose: 'Usage tracking', status: 'active' },
  { name: 'Intercom', type: 'Support', purpose: 'Ticket analysis', status: 'active' },
  { name: 'Stripe', type: 'Billing', purpose: 'Revenue data', status: 'active' },
  { name: 'Slack', type: 'Comms', purpose: 'CS notifications', status: 'active' },
  { name: 'Knowledge', type: 'RAG', purpose: 'Pinecone retrieval', status: 'active' },
  { name: 'Approvals', type: 'Internal', purpose: 'HITL workflow', status: 'active' },
  { name: 'Scraper', type: 'Intel', purpose: 'Web scraping', status: 'active' },
];

const TABS = ['General', 'Agent Config', 'Integrations', 'Team'];

export default function SettingsPage() {
  const [tab, setTab] = useState('General');
  const [ingestTitle, setIngestTitle] = useState('');
  const [ingestContent, setIngestContent] = useState('');
  const [ingestStatus, setIngestStatus] = useState<'idle'|'loading'|'success'|'error'>('idle');

  const handleIngest = async () => {
    if (!ingestTitle || !ingestContent) return;
    setIngestStatus('loading');
    try {
      const resp = await fetch('http://localhost:8000/api/docs/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: ingestTitle, content: ingestContent, doc_type: 'general' })
      });
      if (resp.ok) {
        setIngestStatus('success');
        setIngestTitle('');
        setIngestContent('');
        setTimeout(() => setIngestStatus('idle'), 3000);
      } else {
        setIngestStatus('error');
      }
    } catch {
      setIngestStatus('error');
    }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">⚙️ Settings</h1>
      </div>

      <div className="tab-bar" style={{ marginBottom: 'var(--space-xl)' }}>
        {TABS.map(t => (
          <button key={t} className={`tab-item ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'General' && (
        <div className={styles.section}>
          <div className={`card ${styles.settingCard}`}>
            <h3 className="text-title">Organization</h3>
            <div className={styles.fieldGroup}>
              <div className={styles.field}><label className="text-label">ORG NAME</label><input defaultValue="OmniSales Demo" /></div>
              <div className={styles.field}><label className="text-label">ORG ID</label><input defaultValue="a0000000-0000-0000-0000-000000000001" disabled className="font-mono" /></div>
            </div>
          </div>
          <div className={`card ${styles.settingCard}`}>
            <h3 className="text-title">LLM Configuration</h3>
            <div className={styles.fieldGroup}>
              <div className={styles.field}><label className="text-label">COMPLEX MODEL</label><input defaultValue="llama-3.3-70b-versatile" disabled className="font-mono" /></div>
              <div className={styles.field}><label className="text-label">FAST MODEL</label><input defaultValue="llama-3.1-8b-instant" disabled className="font-mono" /></div>
              <div className={styles.field}><label className="text-label">PROVIDER</label><input defaultValue="Groq" disabled /></div>
            </div>
          </div>
        </div>
      )}

      {tab === 'Agent Config' && (
        <div className={styles.agentGrid}>
          {[
            { name: 'Closer', icon: '🎯', color: 'var(--closer)', desc: 'Deal risk detection & re-engagement' },
            { name: 'Prospector', icon: '🔍', color: 'var(--prospector)', desc: 'Cold outreach & lead qualification' },
            { name: 'Guardian', icon: '🛡️', color: 'var(--guardian)', desc: 'Churn prediction & retention' },
            { name: 'Spy', icon: '🕵️', color: 'var(--spy)', desc: 'Competitive intelligence via A2A' },
          ].map(agent => (
            <div key={agent.name} className={`card ${styles.agentConfigCard}`} style={{ borderTopColor: agent.color }}>
              <div className={styles.agentHeader}>
                <span style={{ fontSize: '1.5rem' }}>{agent.icon}</span>
                <div>
                  <h3 className="text-title" style={{ color: agent.color }}>{agent.name}</h3>
                  <p className="text-body-sm text-muted">{agent.desc}</p>
                </div>
              </div>
              <div className={styles.agentFields}>
                <div className={styles.sliderField}>
                  <div className={styles.sliderHeader}>
                    <span className="text-label">AUTO-APPROVAL THRESHOLD</span>
                    <span className="font-mono text-body-sm">85%</span>
                  </div>
                  <input type="range" min={0} max={100} defaultValue={85} />
                </div>
                <div className={styles.toggleField}>
                  <span className="text-body-sm">HITL Required</span>
                  <div className="toggle active" />
                </div>
                <div className={styles.toggleField}>
                  <span className="text-body-sm">Active</span>
                  <div className="toggle active" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'Integrations' && (
        <div className={styles.section}>
          <div className={`card ${styles.settingCard}`}>
            <h3 className="text-title">MCP Servers ({MCP_SERVERS.length})</h3>
            <p className="text-body-sm text-muted" style={{ marginBottom: 'var(--space-lg)' }}>Model Context Protocol server connections</p>
            <div className={styles.mcpGrid}>
              {MCP_SERVERS.map(server => (
                <div key={server.name} className={styles.mcpCard}>
                  <div className={styles.mcpHeader}>
                    <span className="text-body" style={{ fontWeight: 600 }}>{server.name}</span>
                    <span className="dot dot-green pulse-dot" />
                  </div>
                  <span className="badge badge-muted">{server.type}</span>
                  <span className="text-body-sm text-muted">{server.purpose}</span>
                </div>
              ))}
            </div>
          </div>
          <div className={`card ${styles.settingCard}`}>
            <h3 className="text-title">Pinecone RAG</h3>
            <div className={styles.fieldGroup}>
              <div className={styles.field}><label className="text-label">INDEX</label><input defaultValue="omnisales-knowledge" disabled className="font-mono" /></div>
              <div className={styles.field}><label className="text-label">EMBEDDING</label><input defaultValue="multilingual-e5-large" disabled className="font-mono" /></div>
            </div>
            
            <div style={{ marginTop: 'var(--space-lg)', paddingTop: 'var(--space-md)', borderTop: '1px solid var(--border)' }}>
              <h4 className="text-body" style={{ fontWeight: 600, marginBottom: 'var(--space-md)' }}>Ingest Knowledge Document</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                <input 
                  placeholder="Document Title (e.g., Acme Battlecard)" 
                  value={ingestTitle}
                  onChange={e => setIngestTitle(e.target.value)}
                  style={{ width: '100%', maxWidth: '400px' }}
                />
                <textarea 
                  placeholder="Paste document text here..."
                  value={ingestContent}
                  onChange={e => setIngestContent(e.target.value)}
                  style={{ width: '100%', height: '120px', resize: 'vertical' }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', marginTop: 'var(--space-xs)' }}>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleIngest}
                    disabled={ingestStatus === 'loading' || !ingestTitle || !ingestContent}
                  >
                    {ingestStatus === 'loading' ? 'Ingesting...' : 'Ingest to Pinecone'}
                  </button>
                  {ingestStatus === 'success' && <span className="text-body-sm" style={{ color: 'var(--success)' }}>✓ Document ingested successfully</span>}
                  {ingestStatus === 'error' && <span className="text-body-sm" style={{ color: 'var(--danger)' }}>✗ Ingestion failed</span>}
                </div>
              </div>
            </div>
          </div>
          <div className={`card ${styles.settingCard}`}>
            <h3 className="text-title">A2A Protocol</h3>
            <div className={styles.fieldGroup}>
              <div className={styles.field}><label className="text-label">SPY SERVER</label><input defaultValue="http://agent-spy:8080" disabled className="font-mono" /></div>
              <div className={styles.field}><label className="text-label">STATUS</label><div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}><span className="dot dot-green pulse-dot" /><span className="text-body-sm">Connected</span></div></div>
            </div>
          </div>
        </div>
      )}

      {tab === 'Team' && (
        <div className={`card ${styles.settingCard}`}>
          <h3 className="text-title">Team Members</h3>
          <table className="data-table" style={{ marginTop: 'var(--space-md)' }}>
            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
            <tbody>
              <tr><td>Admin</td><td className="font-mono">admin@omnisales.ai</td><td>Admin</td><td><span className="badge badge-success">Active</span></td></tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
