"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Search, Bell, Play, RefreshCw, Filter, User } from "lucide-react";
import { Button } from "@/lib/../components/ui/button";
import { scanOrchestrator, fetchTasks, triggerCrmSync } from "@/lib/api";

interface HeaderProps {
  onOpenCommandPalette: () => void;
  onOpenMissionControl?: () => void;
}

export function Header({ onOpenCommandPalette, onOpenMissionControl }: HeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [pendingApprovals, setPendingApprovals] = useState<number>(0);

  useEffect(() => {
    async function loadPending() {
      try {
        const tasks = await fetchTasks("pending_approval");
        setPendingApprovals(tasks.length);
      } catch {
        // silent
      }
    }
    loadPending();
    const interval = setInterval(loadPending, 10000);
    return () => clearInterval(interval);
  }, []);

  // Compute Page Title from Pathname
  let pageTitle = "Dashboard Overview";
  if (pathname?.includes("/orchestrator")) pageTitle = "Central Orchestrator Assistant";
  else if (pathname?.includes("/prospecting")) pageTitle = "Lead Prospecting & Enrichment";
  else if (pathname?.includes("/pipeline")) pageTitle = "Sales Pipeline & Deals";
  else if (pathname?.includes("/approvals")) pageTitle = "Human-in-the-Loop Approvals";
  else if (pathname?.includes("/churn")) pageTitle = "Retention & Account Health";
  else if (pathname?.includes("/evals")) pageTitle = "Evals & System Reliability";
  else if (pathname?.includes("/intelligence")) pageTitle = "Competitive Intelligence (Spy A2A)";
  else if (pathname?.includes("/audit")) pageTitle = "Audit Trail & Logs";
  else if (pathname?.includes("/settings")) pageTitle = "System Settings & Probes";

  const [syncingCrm, setSyncingCrm] = useState(false);

  const handleScan = async () => {
    setSyncingCrm(true);
    try {
      await triggerCrmSync();
    } catch {
      // silent fallback
    } finally {
      setSyncingCrm(false);
      if (onOpenMissionControl) {
        onOpenMissionControl();
      }
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-zinc-800 bg-zinc-950/80 px-6 backdrop-blur-md">
      {/* Title & Path */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold tracking-tight text-white">{pageTitle}</h1>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        {/* Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="flex h-9 w-60 items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 text-xs text-zinc-400 hover:border-zinc-700 hover:text-zinc-200 transition-all shadow-sm"
        >
          <span className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5 text-zinc-400" />
            <span>Search or command...</span>
          </span>
          <kbd className="rounded border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono text-zinc-400">
            ⌘K
          </kbd>
        </button>

        {/* Autonomous Scan Trigger - Ingests from HubSpot then Opens Swarm Mission Control */}
        <Button
          onClick={handleScan}
          disabled={syncingCrm}
          variant="outline"
          size="sm"
          className="gap-2 border-blue-500/40 bg-blue-950/30 text-blue-300 hover:bg-blue-600 hover:text-white transition-all shadow-sm shadow-blue-950/50"
        >
          {syncingCrm ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
          <span>{syncingCrm ? "Syncing CRM..." : "Scan CRM"}</span>
        </Button>

        {/* Real Live Notification Bell */}
        <button
          onClick={() => router.push("/dashboard/approvals")}
          className="relative rounded-lg border border-zinc-800 bg-zinc-900/60 p-2 text-zinc-400 hover:text-white hover:border-zinc-700 transition-colors cursor-pointer"
          title={
            pendingApprovals > 0
              ? `${pendingApprovals} pending approvals awaiting review — Click to open`
              : "0 pending approvals"
          }
        >
          <Bell className="h-4 w-4" />
          {pendingApprovals > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#fab219] px-1 text-[10px] font-bold text-zinc-950 ring-2 ring-zinc-950">
              {pendingApprovals}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
