"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  UserPlus,
  TrendingUp,
  CheckSquare,
  ShieldCheck,
  Activity,
  Compass,
  FileText,
  Settings,
  ArrowRight,
  Play,
} from "lucide-react";
import { Dialog, DialogContent } from "@/lib/../components/ui/dialog";
import { fetchDeals, fetchLeads, fetchAccounts, scanOrchestrator } from "@/lib/api";
import { shortId } from "@/lib/utils";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [deals, setDeals] = useState<Array<{ id: string; company: string; stage: string; arr: number }>>([]);
  const [leads, setLeads] = useState<Array<{ id: string; company: string; contact_name: string }>>([]);
  const [accounts, setAccounts] = useState<Array<{ id: string; company: string; plan: string }>>([]);

  useEffect(() => {
    if (open) {
      fetchDeals().then((d) => setDeals(d.slice(0, 10))).catch(() => {});
      fetchLeads().then((l) => setLeads(l.slice(0, 10))).catch(() => {});
      fetchAccounts().then((a) => setAccounts(a.slice(0, 10))).catch(() => {});
    }
  }, [open]);

  // Global Keyboard Shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  const navPages = [
    { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { label: "Prospecting & Leads", href: "/dashboard/prospecting", icon: UserPlus },
    { label: "Sales Pipeline", href: "/dashboard/pipeline", icon: TrendingUp },
    { label: "Approvals Queue", href: "/dashboard/approvals", icon: CheckSquare },
    { label: "Retention & Churn", href: "/dashboard/churn", icon: ShieldCheck },
    { label: "Evals & Reliability", href: "/dashboard/evals", icon: Activity },
    { label: "Competitive Intel", href: "/dashboard/intelligence", icon: Compass },
    { label: "Audit Trail", href: "/dashboard/audit", icon: FileText },
    { label: "Settings", href: "/dashboard/settings", icon: Settings },
  ];

  const filteredPages = navPages.filter((p) => p.label.toLowerCase().includes(query.toLowerCase()));
  const filteredDeals = deals.filter((d) => d.company.toLowerCase().includes(query.toLowerCase()));
  const filteredLeads = leads.filter((l) => l.company.toLowerCase().includes(query.toLowerCase()) || l.contact_name.toLowerCase().includes(query.toLowerCase()));
  const filteredAccounts = accounts.filter((a) => a.company.toLowerCase().includes(query.toLowerCase()));

  const handleSelect = (href: string) => {
    onOpenChange(false);
    setQuery("");
    router.push(href);
  };

  const handleRunScan = async () => {
    onOpenChange(false);
    await scanOrchestrator().catch(() => {});
    router.push("/dashboard");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 max-w-xl overflow-hidden bg-zinc-950/95 border-zinc-800 shadow-2xl">
        {/* Search Input */}
        <div className="flex items-center border-b border-zinc-800 px-4 py-3">
          <Search className="h-4 w-4 text-zinc-400 mr-3 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, search deals, leads, or jump to page..."
            className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
            autoFocus
          />
          <kbd className="rounded border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono text-zinc-400 ml-2">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-3">
          {/* Quick Actions */}
          <div>
            <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">Quick Actions</div>
            <button
              onClick={handleRunScan}
              className="w-full flex items-center justify-between px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800/80 rounded-lg transition-colors group"
            >
              <span className="flex items-center gap-2">
                <Play className="h-4 w-4 text-blue-400" />
                <span>Trigger Autonomous CRM Scan</span>
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-zinc-400 group-hover:text-white" />
            </button>
          </div>

          {/* Navigation Pages */}
          {filteredPages.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">Navigation</div>
              {filteredPages.map((page) => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.href}
                    onClick={() => handleSelect(page.href)}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800/80 rounded-lg transition-colors group"
                  >
                    <span className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-zinc-400 group-hover:text-blue-400 transition-colors" />
                      <span>{page.label}</span>
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-zinc-400 group-hover:text-white" />
                  </button>
                );
              })}
            </div>
          )}

          {/* Deals */}
          {filteredDeals.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">Deals</div>
              {filteredDeals.slice(0, 4).map((deal) => (
                <button
                  key={deal.id}
                  onClick={() => handleSelect(`/dashboard/pipeline/${shortId(deal.id)}`)}
                  className="w-full flex items-center justify-between px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800/80 rounded-lg transition-colors group"
                >
                  <div className="flex flex-col text-left">
                    <span className="font-medium text-white">{deal.company}</span>
                    <span className="text-xs text-zinc-400">Stage: {deal.stage} • ${deal.arr?.toLocaleString()}</span>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-zinc-400 group-hover:text-white" />
                </button>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
