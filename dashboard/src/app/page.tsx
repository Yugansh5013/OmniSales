import Link from 'next/link';
import styles from './landing.module.css';

export default function LandingPage() {
  return (
    <div className={styles.container}>
      {/* Hero Section */}
      <nav className={styles.nav}>
        <div className={styles.navLogo}>
          <span className={styles.logoIcon}>⚡</span>
          <span className={styles.logoText}>OmniSales</span>
        </div>
        <div className={styles.navLinks}>
          <span className={styles.navLink}>Features</span>
          <span className={styles.navLink}>Architecture</span>
          <span className={styles.navLink}>ROI</span>
          <Link href="/login" className="btn btn-primary">Login →</Link>
        </div>
      </nav>

      <section className={styles.hero}>
        <div className={styles.heroGlow} />
        <div className={styles.heroBadge}>🚀 Built with LangGraph · MCP · A2A Protocol</div>
        <h1 className={styles.heroTitle}>
          The <span className={styles.gradient}>Autonomous</span><br />Revenue Department
        </h1>
        <p className={styles.heroSub}>
          4 AI agents that prospect, close, retain, and spy — autonomously.<br />
          Human-in-the-loop when it matters. Fully transparent reasoning.
        </p>
        <div className={styles.heroCta}>
          <Link href="/login" className="btn btn-primary" style={{ padding: '12px 32px', fontSize: '1rem' }}>
            Launch Dashboard →
          </Link>
          <Link href="/login" className="btn btn-secondary" style={{ padding: '12px 32px', fontSize: '1rem' }}>
            View Demo
          </Link>
        </div>
        <div className={styles.demoCredentials}>
          <span className="font-mono text-body-sm text-muted">
            Demo: admin@omnisales.ai / hackathon2026
          </span>
        </div>
      </section>

      {/* Agents Grid */}
      <section className={styles.agents}>
        <h2 className={styles.sectionTitle}>Four Specialized AI Agents</h2>
        <div className={styles.agentGrid}>
          {[
            { icon: '🎯', name: 'Closer', color: 'var(--closer)', desc: 'Monitors deal health, classifies risk, drafts re-engagement emails with RAG-powered objection handling.', stats: '8 autonomous steps' },
            { icon: '🔍', name: 'Prospector', color: 'var(--prospector)', desc: 'Researches targets, scores ICP fit, crafts hyper-personalized outbound sequences for 2 decision-makers.', stats: '6 autonomous steps' },
            { icon: '🛡️', name: 'Guardian', color: 'var(--guardian)', desc: 'Analyzes 20 accounts with multi-signal churn scoring, generates tailored retention playbooks.', stats: '6 autonomous steps' },
            { icon: '🕵️', name: 'Spy', color: 'var(--spy)', desc: 'Scrapes competitor pricing and features via A2A protocol, provides real-time battle cards on demand.', stats: 'A2A Protocol' },
          ].map(agent => (
            <div key={agent.name} className={styles.agentCard} style={{ borderTopColor: agent.color }}>
              <div className={styles.agentIcon}>{agent.icon}</div>
              <h3 className={styles.agentName} style={{ color: agent.color }}>{agent.name}</h3>
              <p className={styles.agentDesc}>{agent.desc}</p>
              <span className={styles.agentStat}>{agent.stats}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ROI Section */}
      <section className={styles.roi}>
        <h2 className={styles.sectionTitle}>The Financial Impact</h2>
        <p className={styles.sectionSub}>OmniSales vs. Traditional Sales Department — 12-month model</p>
        <div className={styles.roiGrid}>
          {[
            { label: 'OpEx Reduction', value: '50.7%', desc: '$2.17M → $1.07M/yr' },
            { label: 'Revenue Multiplier', value: '3.1×', desc: '$9.6M → $30.0M/yr' },
            { label: 'CAC Reduction', value: '84%', desc: '$9,050 → $1,426' },
            { label: 'ROI Efficiency', value: '6.3×', desc: '$4.42 → $28.03 per $1' },
          ].map(stat => (
            <div key={stat.label} className={styles.roiCard}>
              <div className={styles.roiValue}>{stat.value}</div>
              <div className={styles.roiLabel}>{stat.label}</div>
              <div className={styles.roiDesc}>{stat.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className={styles.stack}>
        <h2 className={styles.sectionTitle}>Three-Protocol Architecture</h2>
        <div className={styles.stackGrid}>
          <div className={styles.stackCard}>
            <div className={styles.stackIcon}>🔧</div>
            <h3>MCP Servers</h3>
            <p>12 Model Context Protocol servers for CRM, email, enrichment, billing, and knowledge retrieval.</p>
          </div>
          <div className={styles.stackCard}>
            <div className={styles.stackIcon}>🤝</div>
            <h3>A2A Protocol</h3>
            <p>Google&apos;s Agent-to-Agent protocol enabling live inter-agent intelligence (Closer ↔ Spy).</p>
          </div>
          <div className={styles.stackCard}>
            <div className={styles.stackIcon}>📡</div>
            <h3>Kafka Events</h3>
            <p>Apache Kafka for asynchronous event-driven coordination between all four agents.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <span>⚡ OmniSales — The Autonomous Revenue Department</span>
          <span className={styles.footerTech}>
            LangGraph · FastMCP · A2A · Kafka · PostgreSQL · Pinecone · Redis · Kubernetes
          </span>
        </div>
      </footer>
    </div>
  );
}
