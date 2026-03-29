'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import styles from './architecture.module.css';

/* ───────────────────────────────────────────
   Mermaid definitions from project_des.md
   ─────────────────────────────────────────── */

const MAIN_ARCHITECTURE = `flowchart TD
    %% Node Styles
    classDef react fill:#000,stroke:#38BDF8,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef fastapi fill:#000,stroke:#10B981,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef orc fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef closer fill:#172554,stroke:#3B82F6,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef prospect fill:#064E3B,stroke:#34D399,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef guard fill:#4A044E,stroke:#D946EF,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    
    classDef db fill:#022C22,stroke:#059669,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef stream fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef trace fill:#172554,stroke:#60A5FA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Frontend ["Frontend & Auth"]
        UI["⚛️ Web UI · Next.js"]:::react --> GW["⚡ FastAPI Gateway"]:::fastapi
    end

    subgraph Pipeline ["OmniSales Agentic Pipeline"]
        direction TB
        ORC["🧠 Orchestrator Agent<br/>(Supervisor · Scheduler · Chat)"]:::orc
        
        subgraph SubAgents ["Async Subagent Layer"]
            direction LR
            CL["🎯 Closer Agent<br/>⬇ click to explore"]:::closer
            PR["🔍 Prospector Agent<br/>⬇ click to explore"]:::prospect
            GR["🛡️ Guardian Agent<br/>⬇ click to explore"]:::guard
        end
        
        ORC -- "Async Dispatch" --> CL
        ORC -- "Async Dispatch" --> PR
        ORC -- "Async Dispatch" --> GR
    end

    subgraph Protocols ["Model Context Protocol · MCP Tools"]
        direction LR
        CRM["💾 CRM Server<br/>(NeonDB Bridge)"]:::mcp
        KNW["📚 Knowledge Server<br/>(Playbooks & FAQs)"]:::mcp
        APP["✅ Approvals Server<br/>(Human-in-the-Loop)"]:::mcp
        SPY["🕵️ Spy Server<br/>(A2A Intel)"]:::mcp
    end

    subgraph Infra ["Infrastructure"]
        direction LR
        NEON["🐘 Neon PostgreSQL<br/>(State & Reports)"]:::db
        KAFKA["🚂 Kafka<br/>(Event Bus)"]:::stream
        GROQ["🚀 Groq API<br/>(Llama 3 70B & 8B)"]:::llm
        PCONE["🌲 Pinecone<br/>(MRL Vectors)"]:::db
        LSMITH["🦜 LangSmith<br/>(LLM Tracing)"]:::trace
    end

    %% Connections
    GW -->|REST/HTTP| ORC
    GW -->|Status/Approvals| SubAgents
    
    SubAgents -.->|Tool Calls| Protocols
    ORC -.->|CRM Scan| CRM
    
    CRM == "SQL" ==> NEON
    KNW == "Embeddings" ==> PCONE
    SubAgents -.->|Pub/Sub| KAFKA
    
    ORC -.- GROQ
    SubAgents -.- GROQ`;

const AGENT_DIAGRAMS: Record<string, { title: string; icon: string; color: string; diagram: string; description: string }> = {
  closer: {
    title: 'Closer Agent',
    icon: '🎯',
    color: '#3B82F6',
    description: 'Monitors all pipeline deals, detects stalled/at-risk deals, drafts contextual follow-up emails, handles objections via RAG, gets live competitive intel from The Spy via A2A.',
    diagram: `flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#172554,stroke:#3B82F6,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Stage Changed)):::trigger
        T2((Lead Qualified)):::trigger
    end

    subgraph Agent_Graph ["Closer Agent Graph"]
        direction TB
        N1[Analyze Deal]:::process
        N2{Classify Risk}:::llm
        N3[Draft Follow-up]:::llm
        N4[Handle Objection]:::llm
        N5{Human Approval}:::process
        N6[Send out & Update]:::process
        
        N1 --> N2
        N2 -- "Follow-up" --> N3
        N2 -- "Objection" --> N4
        N2 -- "Healthy" --> N_Wait((Wait)):::process
        N3 & N4 --> N5
        N5 -- "Approved" --> N6
        N5 -- "Rejected" --> N_Revise[Revise]:::process --> N5
    end

    subgraph Integrations
        M1[HubSpot MCP]:::mcp
        M2[Knowledge RAG]:::mcp
        M_A2A[A2A: Spy Server]:::mcp
        M3[Approval MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1
    N4 -.-> M2
    N4 -.-> M_A2A
    N5 -.-> M3
    
    N6 --> O1[(Publish: deal_won / lost)]:::output`
  },

  prospector: {
    title: 'Prospector Agent',
    icon: '🔍',
    color: '#34D399',
    description: 'Scrapes public data, finds ICP-matching leads, researches company signals, drafts hyper-personalized cold outreach, manages communication until a meeting is booked.',
    diagram: `flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#064E3B,stroke:#34D399,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Daily Cron)):::trigger
        T2((Kafka Events)):::trigger
    end

    subgraph Agent_Graph ["Prospector Agent Graph"]
        direction TB
        N1[Search Leads]:::process
        N2[Enrich Data]:::process
        N3{ICP Scoring}:::llm
        N4[Draft Outreach]:::llm
        N5{Human Approval}:::process
        N6[Send & CRM Sync]:::process
        
        N1 --> N2 --> N3
        N3 -- "Score > 0.7" --> N4
        N3 -- "Score <= 0.7" --> N_Drop((Drop)):::process
        N4 --> N5
        N5 -- "Approved" --> N6
        N5 -- "Rejected" --> N_Revise[Revise Draft]:::process --> N5
    end

    subgraph Integrations
        M1[Apollo.io MCP]:::mcp
        M2[HubSpot MCP]:::mcp
        M3[SendGrid MCP]:::mcp
        M4[Approval MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1
    N6 -.-> M2
    N6 -.-> M3
    N5 -.-> M4
    
    N6 --> O1[(Publish: lead_qualified)]:::output`
  },

  guardian: {
    title: 'Guardian Agent',
    icon: '🛡️',
    color: '#D946EF',
    description: 'Watches usage metrics and support tickets, detects churn signals, sends check-in emails, detects plan limit approach (upsell signal), drafts upgrade proposals.',
    diagram: `flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#4A044E,stroke:#D946EF,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Metrics Drop)):::trigger
        T2((Health Cron)):::trigger
    end

    subgraph Agent_Graph ["Guardian Agent Graph"]
        direction TB
        N1[Analyze Usage & Tickets]:::process
        N2{Score Risk/Upsell}:::llm
        N3[Draft Check-in]:::llm
        N4[Draft Proposal]:::llm
        N5{Human Approval}:::process
        N6[Send Comms]:::process
        
        N1 --> N2
        N2 -- "High Churn Risk" --> N3
        N2 -- "Upsell Trigger" --> N4
        N2 -- "Stable" --> N_Wait((Wait)):::process
        N3 & N4 --> N5
        N5 -- "Approved" --> N6
    end

    subgraph Integrations
        M1[Mixpanel MCP]:::mcp
        M2[Intercom MCP]:::mcp
        M3[Stripe MCP]:::mcp
    end

    T1 & T2 --> N1
    N1 -.-> M1 & M2 & M3
    
    N6 --> O1[(Publish: churn_risk/upsell)]:::output`
  },

  spy: {
    title: 'Spy Agent',
    icon: '🕵️',
    color: '#F97316',
    description: 'Monitors competitor websites/pricing via Playwright, detects changes using HTML diffing + LLM, updates Pinecone battle cards, broadcasts events via Kafka. Only agent that acts as an A2A server.',
    diagram: `flowchart TD
    classDef trigger fill:#1E1B4B,stroke:#A855F7,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef process fill:#0F172A,stroke:#64748B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef mcp fill:#18181B,stroke:#A1A1AA,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef llm fill:#422006,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px
    classDef output fill:#450A0A,stroke:#DC2626,stroke-width:2px,color:#F8FAFC,rx:8px,ry:8px

    subgraph Triggers
        T1((Hourly Cron)):::trigger
        T2((A2A Request)):::trigger
    end

    subgraph Agent_Graph ["Spy Agent Graph"]
        direction TB
        N1[Scrape Sites]:::process
        N2{Detect Updates}:::llm
        N3[Generate Battle Card]:::process
        N4[Respond to A2A]:::process
        
        T1 --> N1 --> N2
        N2 -- "Changes Found" --> N3
        T2 --> N4
    end

    subgraph Integrations
        M1[Scraper MCP]:::mcp
        M2[Pinecone RAG MCP]:::mcp
        M3[Slack MCP]:::mcp
    end

    N1 -.-> M1
    N3 -.-> M2
    N3 -.-> M3
    
    N3 --> O1[(Publish: competitor_event)]:::output`
  }
};

/* ───────────────────────────────────────────
   Mermaid rendering component
   ─────────────────────────────────────────── */

function MermaidDiagram({ chart, id, onNodeClick }: { chart: string; id: string; onNodeClick?: (nodeId: string) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rendered, setRendered] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      const mermaid = (await import('mermaid')).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        themeVariables: {
          darkMode: true,
          background: '#0a0a0f',
          primaryColor: '#172554',
          primaryTextColor: '#F8FAFC',
          primaryBorderColor: '#3B82F6',
          lineColor: '#64748B',
          secondaryColor: '#1E1B4B',
          tertiaryColor: '#064E3B',
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize: '13px',
        },
        flowchart: {
          htmlLabels: true,
          curve: 'basis',
          padding: 12,
          nodeSpacing: 30,
          rankSpacing: 40,
        },
        securityLevel: 'loose',
      });

      if (containerRef.current && !cancelled) {
        containerRef.current.innerHTML = '';
        try {
          const { svg } = await mermaid.render(`mermaid-${id}-${Date.now()}`, chart);
          if (!cancelled && containerRef.current) {
            containerRef.current.innerHTML = svg;
            setRendered(true);

            // Attach click handlers to agent nodes
            if (onNodeClick) {
              const svgEl = containerRef.current.querySelector('svg');
              if (svgEl) {
                // Make agent nodes clickable
                const nodeGroups = svgEl.querySelectorAll('.node');
                nodeGroups.forEach((node) => {
                  const textEl = node.querySelector('foreignObject span, text');
                  const text = textEl?.textContent?.toLowerCase() || '';
                  
                  let agentKey = '';
                  if (text.includes('closer')) agentKey = 'closer';
                  else if (text.includes('prospector')) agentKey = 'prospector';
                  else if (text.includes('guardian')) agentKey = 'guardian';
                  else if (text.includes('spy')) agentKey = 'spy';
                  
                  if (agentKey) {
                    (node as HTMLElement).style.cursor = 'pointer';
                    node.addEventListener('click', () => onNodeClick(agentKey));
                  }
                });
              }
            }
          }
        } catch (e) {
          console.error('Mermaid render error:', e);
          if (!cancelled && containerRef.current) {
            containerRef.current.innerHTML = `<pre style="color:#f87171;padding:1rem">${e}</pre>`;
          }
        }
      }
    }
    render();
    return () => { cancelled = true; };
  }, [chart, id, onNodeClick]);

  return (
    <div
      ref={containerRef}
      className={styles.mermaidContainer}
      style={{ opacity: rendered ? 1 : 0.3, transition: 'opacity 0.4s ease' }}
    />
  );
}

/* ───────────────────────────────────────────
   Modal for agent flowcharts
   ─────────────────────────────────────────── */

function AgentModal({ agent, onClose }: { agent: string; onClose: () => void }) {
  const data = AGENT_DIAGRAMS[agent];
  if (!data) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '2rem' }}>{data.icon}</span>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.4rem', color: data.color }}>{data.title} — LangGraph Flow</h2>
              <p className="text-body-sm text-muted" style={{ margin: '4px 0 0 0', maxWidth: '600px' }}>{data.description}</p>
            </div>
          </div>
          <button className={styles.modalClose} onClick={onClose}>✕</button>
        </div>
        <div className={styles.modalBody}>
          <MermaidDiagram chart={data.diagram} id={`modal-${agent}`} />
        </div>
        <div className={styles.modalFooter}>
          <div className={styles.legendRow}>
            <span className={styles.legendItem}><span style={{ background: '#A855F7' }} className={styles.legendDot} /> Trigger</span>
            <span className={styles.legendItem}><span style={{ background: data.color }} className={styles.legendDot} /> Process Node</span>
            <span className={styles.legendItem}><span style={{ background: '#F59E0B' }} className={styles.legendDot} /> LLM Decision</span>
            <span className={styles.legendItem}><span style={{ background: '#A1A1AA' }} className={styles.legendDot} /> MCP Integration</span>
            <span className={styles.legendItem}><span style={{ background: '#DC2626' }} className={styles.legendDot} /> Event Output</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────────────────────────
   Main Page
   ─────────────────────────────────────────── */

export default function ArchitecturePage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const handleNodeClick = useCallback((agentKey: string) => {
    setSelectedAgent(agentKey);
  }, []);

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">🔗 System Architecture</h1>
          <p className="text-body-sm text-muted">
            Three-protocol architecture powering autonomous revenue operations — MCP for tool access, A2A for agent collaboration, Kafka for event coordination.
          </p>
        </div>
      </div>

      {/* Main Architecture Diagram */}
      <div className={styles.diagramSection}>
        <div className={styles.diagramHeader}>
          <span className="text-label">HIGH-LEVEL ARCHITECTURE</span>
          <span className="text-body-sm text-muted">From the project engineering blueprint</span>
        </div>
        <MermaidDiagram chart={MAIN_ARCHITECTURE} id="main-arch" onNodeClick={handleNodeClick} />
      </div>

      {/* Clickable Agent Cards */}
      <div className={styles.agentCardsSection}>
        <span className="text-label" style={{ display: 'block', marginBottom: 'var(--space-md)' }}>
          AGENT FLOWCHARTS — Click an agent to view its LangGraph execution flow
        </span>
        <div className={styles.agentCards}>
          {Object.entries(AGENT_DIAGRAMS).map(([key, agent]) => (
            <button
              key={key}
              className={styles.agentCard}
              style={{ '--agent-color': agent.color } as React.CSSProperties}
              onClick={() => setSelectedAgent(key)}
            >
              <div className={styles.agentCardIcon}>{agent.icon}</div>
              <div className={styles.agentCardTitle}>{agent.title}</div>
              <div className={styles.agentCardDesc}>{agent.description.slice(0, 80)}…</div>
              <div className={styles.clickHint}>
                <span className={styles.clickPulse} />
                Click to explore flow →
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Protocol Legend */}
      <div className={styles.protocolSection}>
        <span className="text-label" style={{ display: 'block', marginBottom: 'var(--space-md)' }}>THE THREE PROTOCOL AXES</span>
        <div className={styles.protocolCards}>
          <div className={styles.protocolCard}>
            <span className={styles.protocolIcon}>🔧</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>MCP (Model Context Protocol)</div>
              <div className="text-body-sm text-muted">Vertical — Agent connects <em>down</em> to external services. 3 custom servers built.</div>
            </div>
          </div>
          <div className={styles.protocolCard}>
            <span className={styles.protocolIcon}>🤝</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>A2A (Agent-to-Agent)</div>
              <div className="text-body-sm text-muted">Horizontal — Direct peer-to-peer agent calls (sync). Spy serves battle cards on demand.</div>
            </div>
          </div>
          <div className={styles.protocolCard}>
            <span className={styles.protocolIcon}>📡</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Apache Kafka</div>
              <div className="text-body-sm text-muted">Async broadcast — One-to-many event signals between agents. 4 topics in production.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tech Stack Summary */}
      <div className="card" style={{
        marginTop: 'var(--space-xl)',
        padding: 'var(--space-lg) var(--space-xl)',
        background: 'linear-gradient(135deg, rgba(59,130,246,0.06) 0%, rgba(168,85,247,0.06) 100%)',
        border: '1px solid var(--border)',
      }}>
        <span className="text-label" style={{ display: 'block', marginBottom: 'var(--space-md)', letterSpacing: '0.08em' }}>BUILT WITH</span>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
          {[
            'LangGraph', 'MCP (3 Custom Servers)', 'A2A Protocol', 'Pinecone RAG',
            'Groq LLM', 'PostgreSQL', 'Redis', 'Apache Kafka', 'Docker', 'Next.js 15', 'FastAPI', 'Kubernetes (manifests)',
          ].map(tech => (
            <span key={tech} className="badge badge-info" style={{ fontSize: '0.82rem', padding: '6px 12px' }}>{tech}</span>
          ))}
        </div>
      </div>

      {/* Agent Flowchart Modal */}
      {selectedAgent && (
        <AgentModal agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
      )}
    </div>
  );
}
