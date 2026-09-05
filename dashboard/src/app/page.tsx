"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Bot,
  Sparkles,
  TrendingUp,
  UserPlus,
  ShieldCheck,
  Compass,
  ArrowRight,
  CheckCircle2,
  Lock,
  Layers,
  Cpu,
  Zap,
  Activity,
  CreditCard,
  FileText,
  Copy,
  ExternalLink,
  Radio,
  Server,
  Key,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"closer" | "prospector" | "guardian" | "spy">("closer");

  const handleCopyCredentials = () => {
    navigator.clipboard.writeText("admin@omnisales.ai / hackathon2026");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans selection:bg-blue-500/30 selection:text-white">
      {/* Top Glassmorphic Navigation Bar */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-6">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 group-hover:scale-105 transition-transform">
              <Bot className="h-5 w-5" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">OmniSales</span>
              <span className="rounded-full bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 text-[10px] font-mono text-blue-400 font-semibold">
                v2.0 Swarm
              </span>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-8 text-xs font-medium text-zinc-400">
            <a href="#agents" className="hover:text-zinc-100 transition-colors">
              Agent Departments
            </a>
            <a href="#architecture" className="hover:text-zinc-100 transition-colors">
              Architecture & Protocols
            </a>
            <a href="#dealdesk" className="hover:text-zinc-100 transition-colors">
              Deal Desk & Gating
            </a>
            <a href="#roi" className="hover:text-zinc-100 transition-colors">
              ROI & Evals
            </a>
          </div>

          {/* Actions & Swarm Health Pill */}
          <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1 text-[11px] font-mono text-zinc-400">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#0ca30c] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0ca30c]"></span>
              </span>
              <span className="text-zinc-300">4 Swarm Agents Active</span>
            </div>

            <Link href="/login">
              <Button
                size="sm"
                className="gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs h-9 px-4 shadow-lg shadow-blue-600/20"
              >
                <span>Launch Dashboard</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-16 md:pt-28 md:pb-24 overflow-hidden">
        {/* Background Mesh Gradient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-blue-600/10 blur-[130px] pointer-events-none rounded-full" />
        <div className="absolute top-1/3 right-1/4 w-[400px] h-[300px] bg-purple-600/10 blur-[120px] pointer-events-none rounded-full" />

        <div className="max-w-6xl mx-auto px-6 text-center space-y-8 relative z-10">
          {/* Top Pill Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-xs text-blue-300 shadow-sm backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5 text-blue-400" />
            <span className="font-medium">Multi-Agent Swarm · LangGraph · FastMCP · Google A2A</span>
          </div>

          {/* Hero Headline */}
          <div className="space-y-4 max-w-4xl mx-auto">
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1]">
              The <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">Autonomous</span> Revenue Department
            </h1>
            <p className="text-base sm:text-lg md:text-xl text-zinc-400 max-w-3xl mx-auto leading-relaxed font-normal">
              Four specialized AI agents that prospect leads, close enterprise pipeline, protect retention, and gather live competitor intelligence — backed by deterministic Deal Desk policy gating and human-in-the-loop authorization.
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link href="/login" className="w-full sm:w-auto">
              <Button
                size="lg"
                className="w-full sm:w-auto gap-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm h-12 px-7 shadow-xl shadow-blue-600/25 transition-all"
              >
                <span>Launch Live Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>

            <a href="#architecture" className="w-full sm:w-auto">
              <Button
                variant="outline"
                size="lg"
                className="w-full sm:w-auto gap-2 border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800 text-zinc-300 text-sm h-12 px-6"
              >
                <Layers className="h-4 w-4 text-zinc-400" />
                <span>Explore Architecture</span>
              </Button>
            </a>
          </div>

          {/* 1-Click Demo Credentials Pill */}
          <div className="pt-2 flex items-center justify-center">
            <button
              onClick={handleCopyCredentials}
              className="inline-flex items-center gap-2.5 rounded-xl border border-zinc-800 bg-zinc-900/60 px-4 py-2 text-xs font-mono text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 transition-all shadow-sm group"
              title="Click to copy demo credentials"
            >
              <Key className="h-3.5 w-3.5 text-blue-400" />
              <span>Demo Login: <strong className="text-zinc-200">admin@omnisales.ai</strong> / <strong className="text-zinc-200">hackathon2026</strong></span>
              <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-700 group-hover:bg-zinc-700">
                {copied ? "Copied!" : "Copy"}
              </span>
            </button>
          </div>

          {/* Live Interactive Swarm Terminal / Telemetry Preview */}
          <div className="pt-8 max-w-4xl mx-auto">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/90 shadow-2xl overflow-hidden backdrop-blur-2xl text-left font-mono text-xs">
              {/* Window Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/80 bg-zinc-900/60">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500/80" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
                  <div className="h-3 w-3 rounded-full bg-green-500/80" />
                  <span className="ml-2 font-sans font-medium text-xs text-zinc-400">
                    OmniSales Swarm Orchestrator — Live Reasoning Stream
                  </span>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-zinc-500">
                  <span className="inline-block h-2 w-2 rounded-full bg-[#0ca30c] animate-pulse" />
                  <span>Streaming Telemetry</span>
                </div>
              </div>

              {/* Agent Tabs */}
              <div className="flex border-b border-zinc-800/80 bg-zinc-950/40 px-2 overflow-x-auto text-[11px]">
                <button
                  onClick={() => setActiveTab("closer")}
                  className={`flex items-center gap-2 px-4 py-2.5 font-sans font-medium border-b-2 transition-colors ${
                    activeTab === "closer"
                      ? "border-blue-500 text-blue-400 bg-blue-500/5"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>Closer Agent (Pipeline)</span>
                </button>
                <button
                  onClick={() => setActiveTab("prospector")}
                  className={`flex items-center gap-2 px-4 py-2.5 font-sans font-medium border-b-2 transition-colors ${
                    activeTab === "prospector"
                      ? "border-blue-500 text-blue-400 bg-blue-500/5"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  <span>Prospector (Outreach)</span>
                </button>
                <button
                  onClick={() => setActiveTab("guardian")}
                  className={`flex items-center gap-2 px-4 py-2.5 font-sans font-medium border-b-2 transition-colors ${
                    activeTab === "guardian"
                      ? "border-blue-500 text-blue-400 bg-blue-500/5"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Guardian (Retention)</span>
                </button>
                <button
                  onClick={() => setActiveTab("spy")}
                  className={`flex items-center gap-2 px-4 py-2.5 font-sans font-medium border-b-2 transition-colors ${
                    activeTab === "spy"
                      ? "border-blue-500 text-blue-400 bg-blue-500/5"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Compass className="h-3.5 w-3.5" />
                  <span>Spy A2A (Battlecards)</span>
                </button>
              </div>

              {/* Tab Content Display */}
              <div className="p-5 space-y-3 bg-zinc-950/80 text-zinc-300">
                {activeTab === "closer" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-zinc-400 text-[11px]">
                      <span>Target: <strong className="text-white">NexGen Robotics</strong> (ARR: $150,000)</span>
                      <span className="text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2 py-0.5 rounded">Risk: Stalled &gt; 14 Days</span>
                    </div>
                    <p className="text-zinc-300 font-sans text-xs leading-relaxed bg-zinc-900/60 p-3 rounded-lg border border-zinc-800">
                      &gt; LangGraph Chain Step 4/8: Scanned email thread via FastMCP CRM. Detected competitor price pushback. Retrieved technical objection battlecard via Spy A2A protocol. Generated tailored re-engagement draft and submitted to Human-in-the-Loop approval queue.
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1">
                      <span>RAG Relevance: 98.4% · Tokens: 4,120</span>
                      <span className="text-blue-400 font-sans font-semibold">Awaiting Rep One-Click Approval</span>
                    </div>
                  </div>
                )}

                {activeTab === "prospector" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-zinc-400 text-[11px]">
                      <span>Lead: <strong className="text-white">Apex FinTech</strong> · CEO & VP Engineering</span>
                      <span className="text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2 py-0.5 rounded">ICP Fit Score: 0.98 (Tier 1)</span>
                    </div>
                    <p className="text-zinc-300 font-sans text-xs leading-relaxed bg-zinc-900/60 p-3 rounded-lg border border-zinc-800">
                      &gt; LangGraph Sequencer: Crawled tech stack (PostgreSQL, Kafka, Kubernetes). Crafted 2 distinct personalized outreach sequences tailored to executive value-drivers. Queued for human dispatch review.
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1">
                      <span>Enrichment Source: FastMCP CRM & Web Crawl</span>
                      <span className="text-purple-400 font-sans font-semibold">Multi-Persona Outreach Ready</span>
                    </div>
                  </div>
                )}

                {activeTab === "guardian" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-zinc-400 text-[11px]">
                      <span>Account Portfolio: <strong className="text-white">20 Accounts Monitored</strong></span>
                      <span className="text-[#fab219] bg-[rgba(250,178,25,0.12)] border border-[rgba(250,178,25,0.25)] px-2 py-0.5 rounded">3 Flagged At-Risk</span>
                    </div>
                    <p className="text-zinc-300 font-sans text-xs leading-relaxed bg-zinc-900/60 p-3 rounded-lg border border-zinc-800">
                      &gt; Guardian Portfolio Evaluator: Detected 42% API usage decay and 3 unresolved support tickets on CloudMatrix ($180k ARR). Synthesized immediate retention playbook and drafted executive check-in email.
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1">
                      <span>Signal Vectors: API Telemetry + Ticket Sentiment</span>
                      <span className="text-[#fab219] font-sans font-semibold">Retention Playbook Queued</span>
                    </div>
                  </div>
                )}

                {activeTab === "spy" && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-zinc-400 text-[11px]">
                      <span>Protocol: <strong className="text-white">Google A2A (Agent-to-Agent)</strong></span>
                      <span className="text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">Port 8080 · 47.6ms Latency</span>
                    </div>
                    <p className="text-zinc-300 font-sans text-xs leading-relaxed bg-zinc-900/60 p-3 rounded-lg border border-zinc-800">
                      &gt; A2A Skill Invocation: Closer Agent dispatched skill request &quot;get_battlecard&quot; for &quot;Salesflow Pro&quot;. Spy A2A agent responded with real-time pricing matrix, technical vulnerabilities, and win-back displacement strategy.
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1">
                      <span>Inter-Agent Interop: 100% Deterministic JSON</span>
                      <span className="text-[#0ca30c] font-sans font-semibold">Battlecard Synthesized</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Four Specialized AI Agent Departments */}
      <section id="agents" className="py-20 border-t border-zinc-800 bg-zinc-950/50 relative">
        <div className="max-w-6xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Four Specialized AI Agent Departments
            </h2>
            <p className="text-sm text-zinc-400">
              Each agent operates with its own LangGraph execution state, tool schemas, and specialized domain knowledge.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Closer Agent */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl space-y-4 hover:border-blue-500/40 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Closer Agent</h3>
                    <p className="text-xs text-zinc-400">Enterprise Pipeline & Deal Velocity</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-full border border-blue-500/20">
                  8 Execution Steps
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Continuously evaluates active deals, flags stalling risks, conducts semantic objection analysis, and drafts hyper-personalized responses with RAG-grounded product context.
              </p>
              <div className="space-y-1.5 pt-2 border-t border-zinc-800/80 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>RAG-powered pricing & security objection handling</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Direct integration with Deal Desk policy engine</span>
                </div>
              </div>
            </div>

            {/* Prospector Agent */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl space-y-4 hover:border-purple-500/40 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-400">
                    <UserPlus className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Prospector Agent</h3>
                    <p className="text-xs text-zinc-400">Target ICP Discovery & Outbound</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-purple-400 bg-purple-500/10 px-2.5 py-1 rounded-full border border-purple-500/20">
                  6 Execution Steps
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Ingests inbound leads and target accounts, evaluates ICP fit against 10+ signals, enriches decision-maker profiles, and writes high-converting outbound sequences.
              </p>
              <div className="space-y-1.5 pt-2 border-t border-zinc-800/80 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Dual persona tailoring (Executive vs Technical)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Bulk CSV lead ingest & asynchronous qualification</span>
                </div>
              </div>
            </div>

            {/* Guardian Agent */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl space-y-4 hover:border-emerald-500/40 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(12,163,12,0.15)] border border-[rgba(12,163,12,0.3)] text-[#0ca30c]">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Guardian Agent</h3>
                    <p className="text-xs text-zinc-400">Portfolio Health & Churn Prevention</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-[#0ca30c] bg-[rgba(12,163,12,0.1)] px-2.5 py-1 rounded-full border border-[rgba(12,163,12,0.25)]">
                  20 Accounts
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Monitors product usage decay, unaddressed support escalations, and executive sponsor departures to compute dynamic churn risk scores and trigger tailored retention plays.
              </p>
              <div className="space-y-1.5 pt-2 border-t border-zinc-800/80 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Multi-signal health telemetry & risk tiering</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Discrete per-account retention playbooks</span>
                </div>
              </div>
            </div>

            {/* Spy A2A Agent */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl space-y-4 hover:border-amber-500/40 transition-all">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(250,178,25,0.15)] border border-[rgba(250,178,25,0.3)] text-[#fab219]">
                    <Compass className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Spy A2A Agent</h3>
                    <p className="text-xs text-zinc-400">Google Agent-to-Agent Competitive Intel</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-[#fab219] bg-[rgba(250,178,25,0.1)] px-2.5 py-1 rounded-full border border-[rgba(250,178,25,0.25)]">
                  A2A Protocol
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Exposes standardized Google A2A skill interfaces to provide on-demand competitor price scraping, feature matrices, and displacement playbooks to other agents.
              </p>
              <div className="space-y-1.5 pt-2 border-t border-zinc-800/80 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Deterministic Agent-to-Agent skill exchange</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#0ca30c]" />
                  <span>Real-time competitor displacement battlecards</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Three-Protocol Architecture & Deal Desk */}
      <section id="architecture" className="py-20 border-t border-zinc-800 relative">
        <div className="max-w-6xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Three-Protocol Enterprise Architecture
            </h2>
            <p className="text-sm text-zinc-400">
              Built on production-grade asynchronous microservices with full observability and fault isolation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
                <Server className="h-4 w-4" />
              </div>
              <h3 className="font-bold text-sm text-white">FastMCP Protocol</h3>
              <p className="text-zinc-400 leading-relaxed">
                Dedicated FastMCP servers for CRM state (8001), Knowledge RAG (8003), and Approvals (8004) ensure sandboxed, typed tool execution without context leakage.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30">
                <Zap className="h-4 w-4" />
              </div>
              <h3 className="font-bold text-sm text-white">Google A2A Protocol</h3>
              <p className="text-zinc-400 leading-relaxed">
                Agent-to-Agent protocol enables autonomous inter-agent coordination. Closer requests competitive intel from Spy dynamically during deal negotiation.
              </p>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600/20 text-[#0ca30c] border border-[rgba(12,163,12,0.3)]">
                <Radio className="h-4 w-4" />
              </div>
              <h3 className="font-bold text-sm text-white">Apache Kafka + Redis</h3>
              <p className="text-zinc-400 leading-relaxed">
                Event-driven Kafka message broker (7 topics) guarantees auditability, durable task queuing, and multi-agent heartbeat telemetry.
              </p>
            </div>
          </div>

          {/* Deal Desk Callout Banner */}
          <div id="dealdesk" className="rounded-2xl border border-blue-500/30 bg-gradient-to-r from-blue-950/40 via-zinc-900/80 to-purple-950/40 p-8 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2 text-blue-400 font-mono text-xs font-semibold uppercase tracking-wider">
                <CreditCard className="h-4 w-4" />
                <span>Deterministic Commercial Governance</span>
              </div>
              <h3 className="text-2xl font-bold text-white">
                Deal Desk Gating &amp; Instant Razorpay Checkout
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-sans">
                Agents cannot offer off-policy discounts. Commercial terms are evaluated in pre-flight against strict corporate rules (&le;30% rep cap, 12mo minimum). Violations trigger automated counter-proposals and require VP Sales override before generating live Razorpay payment links.
              </p>
            </div>

            <Link href="/login" className="shrink-0">
              <Button className="gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs h-10 px-5 shadow-lg shadow-blue-600/20">
                <span>View Deal Desk Flow</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Financial ROI & Reliability Benchmarks */}
      <section id="roi" className="py-20 border-t border-zinc-800 bg-zinc-950/50 relative">
        <div className="max-w-6xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Proven Financial ROI &amp; Reliability
            </h2>
            <p className="text-sm text-zinc-400">
              Empirical metrics measured across enterprise CRM deployments and OpenEvals testing.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-1.5 shadow-lg">
              <div className="text-3xl sm:text-4xl font-extrabold text-[#0ca30c] font-mono">50.7%</div>
              <div className="text-xs font-bold text-white">OpEx Reduction</div>
              <div className="text-[11px] text-zinc-500 font-mono">$2.17M &rarr; $1.07M/yr</div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-1.5 shadow-lg">
              <div className="text-3xl sm:text-4xl font-extrabold text-blue-400 font-mono">3.1&times;</div>
              <div className="text-xs font-bold text-white">Revenue Multiplier</div>
              <div className="text-[11px] text-zinc-500 font-mono">$9.6M &rarr; $30.0M/yr</div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-1.5 shadow-lg">
              <div className="text-3xl sm:text-4xl font-extrabold text-purple-400 font-mono">84%</div>
              <div className="text-xs font-bold text-white">CAC Reduction</div>
              <div className="text-[11px] text-zinc-500 font-mono">$9,050 &rarr; $1,426</div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 text-center space-y-1.5 shadow-lg">
              <div className="text-3xl sm:text-4xl font-extrabold text-[#0ca30c] font-mono">98.3%</div>
              <div className="text-xs font-bold text-white">Human Approval Rate</div>
              <div className="text-[11px] text-zinc-500 font-mono">65/65 Evals Passed</div>
            </div>
          </div>
        </div>
      </section>

      {/* Enterprise Security & Trust */}
      <section className="py-16 border-t border-zinc-800 relative">
        <div className="max-w-5xl mx-auto px-6 text-center space-y-8">
          <div className="space-y-3">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Enterprise Governance &amp; Security Standards
            </h2>
            <p className="text-xs text-zinc-400 max-w-2xl mx-auto leading-relaxed">
              Designed from the ground up for strict enterprise data privacy and regulatory compliance.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-left text-xs">
            <div className="flex gap-3 items-start p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/40">
              <Lock className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-white">Postgres Row-Level Security</h4>
                <p className="text-zinc-400 mt-1 text-[11px] leading-relaxed">
                  Strict tenant data isolation enforced at the database layer via automated tenant context tokens.
                </p>
              </div>
            </div>

            <div className="flex gap-3 items-start p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/40">
              <CheckCircle2 className="h-5 w-5 text-[#0ca30c] shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-white">Human-In-The-Loop Control</h4>
                <p className="text-zinc-400 mt-1 text-[11px] leading-relaxed">
                  Zero external emails or pricing modifications dispatched without explicit sales rep authorization.
                </p>
              </div>
            </div>

            <div className="flex gap-3 items-start p-4 rounded-xl border border-zinc-800/80 bg-zinc-900/40">
              <FileText className="h-5 w-5 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-white">Audit Trail Logging</h4>
                <p className="text-zinc-400 mt-1 text-[11px] leading-relaxed">
                  Immutable event stream logging every agent prompt, token consumption, and override decision.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA & Footer */}
      <footer className="border-t border-zinc-800 bg-zinc-950 py-12 text-xs text-zinc-500">
        <div className="max-w-6xl mx-auto px-6 space-y-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-bold text-sm text-white">OmniSales</span>
              <span className="text-zinc-500 font-mono text-[11px]">— The Autonomous Revenue Department</span>
            </div>

            <div className="flex items-center gap-6 font-medium text-zinc-400 text-xs">
              <Link href="/login" className="hover:text-white transition-colors">
                Sign In
              </Link>
              <Link href="/dashboard" className="hover:text-white transition-colors">
                Overview
              </Link>
              <Link href="/dashboard/pipeline" className="hover:text-white transition-colors">
                Pipeline
              </Link>
              <Link href="/dashboard/evals" className="hover:text-white transition-colors">
                Evals
              </Link>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-zinc-800/80 text-[11px]">
            <span>&copy; 2026 OmniSales AI. Built for enterprise autonomous revenue operations.</span>
            <span className="font-mono text-zinc-400">
              LangGraph · FastMCP · Google A2A · Kafka · Neon Cloud PostgreSQL · Redis · Razorpay
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
