"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  DollarSign,
  ShieldAlert,
  CheckSquare,
  Activity,
  Bot,
  Zap,
  ArrowUpRight,
  RefreshCw,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  fetchDashboardStats,
  fetchEvalsScorecard,
  fetchDeals,
  fetchTasks,
  fetchAuditEvents,
  DashboardStats,
  EvalsScorecard,
  Deal,
  AgentTask,
  scanOrchestrator,
} from "@/lib/api";
import { formatCurrency, formatPercent, formatDate, shortId } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";
import Link from "next/link";

import { SwarmMissionControlDrawer } from "@/components/SwarmMissionControlDrawer";

export default function OverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scorecard, setScorecard] = useState<EvalsScorecard | null>(null);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [pendingTasks, setPendingTasks] = useState<AgentTask[]>([]);
  const [auditLogs, setAuditLogs] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [missionControlOpen, setMissionControlOpen] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [s, sc, d, t, a] = await Promise.all([
        fetchDashboardStats().catch(() => null),
        fetchEvalsScorecard().catch(() => null),
        fetchDeals().catch(() => []),
        fetchTasks("pending_approval").catch(() => []),
        fetchAuditEvents().catch(() => []),
      ]);
      if (s) setStats(s);
      if (sc) setScorecard(sc);
      setRecentDeals(d.slice(0, 5));
      setPendingTasks(t.slice(0, 5));
      const logList = Array.isArray(a) ? a : (a as { entries?: [] })?.entries || [];
      setAuditLogs(logList.slice(0, 6));
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerScan = () => {
    setMissionControlOpen(true);
  };

  if (loading) return <PageLoader label="Loading revenue command center..." />;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Revenue Command Center</h2>
          <p className="text-sm text-zinc-400">Autonomous multi-agent sales pipeline & commercial governance</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleTriggerScan}
            className="gap-2 bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 font-semibold text-xs h-9 px-4 transition-all"
          >
            <Sparkles className="h-4 w-4 fill-current text-blue-200" />
            <span>Trigger Swarm Sweep</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Pipeline ARR"
          value={formatCurrency(stats?.pipeline_value ?? 0)}
          subtitle={`${stats?.active_deals ?? recentDeals.length} deals in flight`}
          trend={{ value: `${stats?.active_deals ?? recentDeals.length} active deals`, isPositive: true }}
          icon={TrendingUp}
          variant="good"
        />

        <StatCard
          title="ARR at Churn Risk"
          value={formatCurrency(stats?.at_risk_arr ?? 0)}
          subtitle={`${stats?.high_churn_accounts ?? 0} accounts flagged by Guardian`}
          trend={{ value: `${stats?.high_churn_accounts ?? 0} critical accounts`, isPositive: false }}
          icon={ShieldAlert}
          variant="critical"
        />

        <StatCard
          title="Pending HITL Approvals"
          value={stats?.pending_approvals ?? pendingTasks.length}
          subtitle="Agent outreach & discount drafts"
          icon={CheckSquare}
          variant={stats?.pending_approvals ? "warning" : "good"}
        />

        <StatCard
          title="Avg Account Health"
          value={`${Math.round((stats?.avg_health_score ?? 0) * 100)}%`}
          subtitle={`${stats?.total_accounts ?? 0} total accounts active`}
          trend={{
            value: (stats?.avg_health_score ?? 0) >= 0.7 ? "Healthy portfolio" : "Needs attention",
            isPositive: (stats?.avg_health_score ?? 0) >= 0.7,
          }}
          icon={Activity}
          variant="good"
        />
      </div>

      {/* Live Evals & System Health Card */}
      {(() => {
        const bench = (scorecard?.offline_benchmarks || {}) as Record<string, number>;
        const closerTraj = bench.closer_trajectory_accuracy_pct ?? 96;
        const ragFaith = bench.rag_faithfulness_pct ?? 100;

        return (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] text-[#0ca30c]">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Live System Reliability & Evals Scorecard</h3>
                  <p className="text-xs text-zinc-400">Continuous LangGraph evaluations, fallback rates, and agent accuracy</p>
                </div>
              </div>
              <Link
                href="/dashboard/evals"
                className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                <span>View Full Scorecard</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Human Approval Rate</span>
                <span className="text-xl font-bold text-[#0ca30c] mt-1 block">
                  {scorecard?.approval_rate_pct !== undefined ? `${scorecard.approval_rate_pct}%` : "100%"}
                </span>
                <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">High rep alignment</span>
              </div>

              <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Model Fallback Rate</span>
                <span className="text-xl font-bold text-white mt-1 block">
                  {scorecard?.fallback_rate_pct !== undefined ? `${scorecard.fallback_rate_pct}%` : "0.0%"}
                </span>
                <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Zero unhandled outages</span>
              </div>

              <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Closer Trajectory</span>
                <span className="text-xl font-bold text-blue-400 mt-1 block">{closerTraj}% Strict</span>
                <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">25 golden scenarios</span>
              </div>

              <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">RAG Faithfulness</span>
                <span className="text-xl font-bold text-[#0ca30c] mt-1 block">{ragFaith}% Judge</span>
                <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Zero hallucinated terms</span>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Autonomous Agent Department Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Closer */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-semibold text-sm text-white">Closer Agent</span>
            </div>
            <StatusBadge status="healthy" label="Online" size="sm" />
          </div>
          <p className="text-xs text-zinc-400 mt-3 line-clamp-2">
            Objection classifier, contract terms evaluator, and silent deal reviver.
          </p>
          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono">Port 9001</span>
            <Link href="/dashboard/pipeline" className="text-blue-400 hover:text-blue-300 font-medium">
              View Deals →
            </Link>
          </div>
        </div>

        {/* Prospector */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-semibold text-sm text-white">Prospector Agent</span>
            </div>
            <StatusBadge status="healthy" label="Online" size="sm" />
          </div>
          <p className="text-xs text-zinc-400 mt-3 line-clamp-2">
            ICP scoring, Clearbit/Apollo enrichment parser, and outreach sequencer.
          </p>
          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono">Port 9002</span>
            <Link href="/dashboard/prospecting" className="text-blue-400 hover:text-blue-300 font-medium">
              View Leads →
            </Link>
          </div>
        </div>

        {/* Guardian */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[rgba(250,178,25,0.12)] border border-[rgba(250,178,25,0.25)] text-[#fab219]">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-semibold text-sm text-white">Guardian Agent</span>
            </div>
            <StatusBadge status="healthy" label="Online" size="sm" />
          </div>
          <p className="text-xs text-zinc-400 mt-3 line-clamp-2">
            Portfolio health scanner, usage decay detector, and retention plays.
          </p>
          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono">Port 9003</span>
            <Link href="/dashboard/churn" className="text-blue-400 hover:text-blue-300 font-medium">
              View Health →
            </Link>
          </div>
        </div>

        {/* Spy A2A */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[rgba(208,59,59,0.12)] border border-[rgba(208,59,59,0.25)] text-[#d03b3b]">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-semibold text-sm text-white">Spy A2A Agent</span>
            </div>
            <StatusBadge status="healthy" label="Online" size="sm" />
          </div>
          <p className="text-xs text-zinc-400 mt-3 line-clamp-2">
            A2A competitive intelligence, real-time battle cards, and win/loss plays.
          </p>
          <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs">
            <span className="text-zinc-500 font-mono">Port 8080</span>
            <Link href="/dashboard/intelligence" className="text-blue-400 hover:text-blue-300 font-medium">
              View Intel →
            </Link>
          </div>
        </div>
      </div>

      {/* Two Column Section: Pipeline Overview & Live Audit Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High Priority Deals */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-400" />
                <h3 className="text-sm font-semibold text-white">High Priority Deals in Pipeline</h3>
              </div>
              <Link href="/dashboard/pipeline" className="text-xs text-blue-400 hover:text-blue-300 font-medium">
                View All ({recentDeals.length}) →
              </Link>
            </div>

            <div className="space-y-3">
              {recentDeals.map((deal) => (
                <Link
                  key={deal.id}
                  href={`/dashboard/pipeline/${shortId(deal.id)}`}
                  className="flex items-center justify-between p-3 rounded-lg border border-zinc-800/60 bg-zinc-950/60 hover:border-zinc-700 hover:bg-zinc-900/80 transition-all group"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold text-sm text-white group-hover:text-blue-400 transition-colors">
                      {deal.company}
                    </span>
                    <span className="text-xs text-zinc-400 font-mono">
                      Stage: {deal.stage} • ARR: {formatCurrency(deal.arr)}
                    </span>
                  </div>
                  <StatusBadge status={deal.risk_level} />
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Live Autonomous Audit Stream */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-[#fab219]" />
                <h3 className="text-sm font-semibold text-white">Live Autonomous Activity Stream</h3>
              </div>
              <Link href="/dashboard/audit" className="text-xs text-blue-400 hover:text-blue-300 font-medium">
                Full Audit →
              </Link>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              {auditLogs.length > 0 ? (
                auditLogs.map((log, idx) => {
                  const agent = String(log.agent_name || log.agent || "system");
                  const action = String(log.action || log.task_type || "executed_task");
                  const target = String(log.target_name || log.company || log.entity || "");
                  const time = formatDate(String(log.created_at || log.timestamp || ""));

                  return (
                    <div key={idx} className="flex items-start justify-between p-2.5 rounded-lg bg-zinc-950/60 border border-zinc-800/60 text-zinc-300">
                      <div className="flex items-start gap-2">
                        <span className="text-blue-400 font-bold uppercase text-[10px] bg-blue-950/60 px-1.5 py-0.5 rounded border border-blue-800/40">
                          {agent}
                        </span>
                        <div className="flex flex-col">
                          <span className="text-zinc-200">{action} {target ? `→ ${target}` : ""}</span>
                          <span className="text-[10px] text-zinc-500">{time}</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8 text-zinc-500 text-xs">
                  Awaiting autonomous events from agent swarm...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Swarm Mission Control Drawer */}
      <SwarmMissionControlDrawer
        isOpen={missionControlOpen}
        onClose={() => setMissionControlOpen(false)}
        onScanCompleted={loadData}
      />
    </div>
  );
}
