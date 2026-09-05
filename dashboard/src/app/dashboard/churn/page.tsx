"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Sparkles,
  Bot,
  Filter,
  DollarSign,
  HeartHandshake,
  LifeBuoy,
} from "lucide-react";
import { AccountCard } from "@/components/AccountCard";
import { Button } from "@/components/ui/button";
import { fetchAccounts, triggerGuardian, Account } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";

export default function ChurnRetentionPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);
  const [scanning, setScanning] = useState<boolean>(false);
  const [guardianResult, setGuardianResult] = useState<Record<string, unknown> | null>(null);

  const loadAccounts = async () => {
    try {
      const data = await fetchAccounts();
      setAccounts(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  const handleRunGuardianScan = async () => {
    setScanning(true);
    setGuardianResult(null);
    try {
      const res = await triggerGuardian();
      setGuardianResult(res);
      await loadAccounts();
    } catch (err: unknown) {
      setGuardianResult({ error: (err as Error).message });
    } finally {
      setScanning(false);
    }
  };

  const handlePlaybookTrigger = async (account: Account) => {
    setScanning(true);
    try {
      await triggerGuardian();
    } finally {
      setScanning(false);
      router.push(`/dashboard/approvals?agent=guardian&company=${encodeURIComponent(account.company)}`);
    }
  };

  const filteredAccounts = accounts.filter((a) => {
    const risk = a.churn_risk ?? 0;
    if (riskFilter === "critical") return risk >= 0.7;
    if (riskFilter === "at_risk") return risk >= 0.4 && risk < 0.7;
    if (riskFilter === "healthy") return risk < 0.4;
    return true;
  });

  const totalArr = accounts.reduce((acc, a) => acc + (Number(a.arr) || 0), 0);
  const criticalAccounts = accounts.filter((a) => (a.churn_risk ?? 0) >= 0.7);
  const arrAtRisk = criticalAccounts.reduce((acc, a) => acc + (Number(a.arr) || 0), 0);
  const avgHealth = accounts.length > 0 ? accounts.reduce((acc, a) => acc + (a.health_score ?? 0.5), 0) / accounts.length : 0;

  if (loading) return <PageLoader label="Loading account health data..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Retention & Account Health Guardian</h2>
          <p className="text-xs text-zinc-400">Autonomous Guardian agent: early warning telemetry, usage decay detection, and proactive retention plays</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleRunGuardianScan}
            disabled={scanning}
            className="gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs h-9 shadow-sm"
          >
            {scanning ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Bot className="h-3.5 w-3.5" />}
            <span>{scanning ? "Scanning Portfolio..." : "Run Guardian Scan"}</span>
          </Button>
        </div>
      </div>

      {/* Portfolio Health Summary Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Total Accounts</span>
          <span className="text-2xl font-bold text-white mt-1 block">{accounts.length}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">{formatCurrency(totalArr)} Total ARR</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-[#d03b3b] uppercase tracking-wider block">ARR at Critical Risk</span>
          <span className="text-2xl font-bold text-white mt-1 block">{formatCurrency(arrAtRisk)}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">{criticalAccounts.length} accounts flagged</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-[#0ca30c] uppercase tracking-wider block">Avg Health Score</span>
          <span className="text-2xl font-bold text-white mt-1 block">{Math.round(avgHealth * 100)}%</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Portfolio utilization stable</span>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg">
          <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider block">Guardian Telemetry</span>
          <span className="text-2xl font-bold text-white mt-1 block">Kafka Active</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Live event ingestion</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
        <button
          onClick={() => setRiskFilter("all")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
            riskFilter === "all" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-white"
          }`}
        >
          All Accounts ({accounts.length})
        </button>
        <button
          onClick={() => setRiskFilter("critical")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
            riskFilter === "critical" ? "bg-[rgba(208,59,59,0.15)] border border-[rgba(208,59,59,0.35)] text-[#d03b3b]" : "text-zinc-400 hover:text-white"
          }`}
        >
          Critical Churn Risk ({criticalAccounts.length})
        </button>
        <button
          onClick={() => setRiskFilter("at_risk")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
            riskFilter === "at_risk" ? "bg-[rgba(250,178,25,0.15)] border border-[rgba(250,178,25,0.35)] text-[#fab219]" : "text-zinc-400 hover:text-white"
          }`}
        >
          Warning Tier ({accounts.filter((a) => (a.churn_risk ?? 0) >= 0.4 && (a.churn_risk ?? 0) < 0.7).length})
        </button>
        <button
          onClick={() => setRiskFilter("healthy")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
            riskFilter === "healthy" ? "bg-[rgba(12,163,12,0.15)] border border-[rgba(12,163,12,0.35)] text-[#0ca30c]" : "text-zinc-400 hover:text-white"
          }`}
        >
          Healthy Tier ({accounts.filter((a) => (a.churn_risk ?? 0) < 0.4).length})
        </button>
      </div>

      {/* Discrete Per-Account Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAccounts.map((account) => (
          <AccountCard key={account.id} account={account} onPlaybookTrigger={handlePlaybookTrigger} />
        ))}
      </div>
    </div>
  );
}
