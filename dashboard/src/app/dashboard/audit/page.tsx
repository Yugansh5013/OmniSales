"use client";

import React, { useState, useEffect } from "react";
import { FileText, Search, RefreshCw, Filter, ShieldCheck, User } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { fetchAuditEvents } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";

export default function AuditTrailPage() {
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const loadAudit = async () => {
    try {
      const data = await fetchAuditEvents();
      const list = Array.isArray(data) ? data : (data as { entries?: [] })?.entries || [];
      setEvents(list);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, []);

  const filtered = events.filter((e) => {
    const text = JSON.stringify(e).toLowerCase();
    return text.includes(search.toLowerCase());
  });

  if (loading) return <PageLoader label="Loading audit trail..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Immutable Audit Trail & Compliance Log</h2>
          <p className="text-xs text-zinc-400">Complete execution record of all agent tasks, Deal Desk policy gates, and human approvals</p>
        </div>
        <Button size="sm" variant="outline" onClick={loadAudit} className="text-xs gap-1.5 border-zinc-700 text-zinc-200">
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Logs</span>
        </Button>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 shadow-xl backdrop-blur-md overflow-hidden">
        <div className="p-4 border-b border-zinc-800 bg-zinc-950/40">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search audit trail logs..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-zinc-950/80 border-b border-zinc-800 text-[11px] font-semibold uppercase text-zinc-400">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">Agent / Service</th>
                <th className="p-3.5">Action / Task</th>
                <th className="p-3.5">Target Entity</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Audit Record</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {filtered.map((e, idx) => (
                <tr key={idx} className="hover:bg-zinc-800/40">
                  <td className="p-3.5 text-zinc-500 text-[11px]">
                    {formatDate(String(e.created_at || e.timestamp || ""))}
                  </td>
                  <td className="p-3.5">
                    <span className="text-blue-400 font-bold uppercase text-[10px] bg-blue-950/80 px-2 py-0.5 rounded border border-blue-800/40">
                      {String(e.agent_name || e.agent || "gateway")}
                    </span>
                  </td>
                  <td className="p-3.5 font-semibold text-zinc-200">
                    {String(e.task_type || e.action || "audit_log")}
                  </td>
                  <td className="p-3.5 text-white font-sans font-medium">
                    {String(e.target_name || e.company || e.entity || "-")}
                  </td>
                  <td className="p-3.5">
                    <StatusBadge status={String(e.status || "completed")} size="sm" />
                  </td>
                  <td className="p-3.5 text-zinc-400 max-w-xs truncate font-sans">
                    {String(e.reasoning || e.draft || e.payment_link_id || "-")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
