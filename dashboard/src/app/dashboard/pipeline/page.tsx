"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Search,
  ArrowRight,
  Filter,
  DollarSign,
  ShieldAlert,
  Clock,
  Layers,
  User,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { fetchDeals, Deal } from "@/lib/api";
import { formatCurrency, formatDate, shortId } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";

export default function PipelinePage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [stageFilter, setStageFilter] = useState<string>("");
  const [riskFilter, setRiskFilter] = useState<string>("");
  const [ownerFilter, setOwnerFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const loadDeals = async () => {
    try {
      const data = await fetchDeals();
      setDeals(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeals();
  }, []);

  const filteredDeals = deals.filter((d) => {
    const matchesStage = !stageFilter || d.stage === stageFilter;
    const matchesRisk = !riskFilter || d.risk_level === riskFilter;
    const matchesOwner = !ownerFilter || d.owner === ownerFilter;
    const matchesSearch =
      !searchQuery ||
      d.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.contact_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.owner && d.owner.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStage && matchesRisk && matchesOwner && matchesSearch;
  });

  const uniqueOwners = Array.from(new Set(deals.map((d) => d.owner).filter(Boolean))) as string[];
  const defaultUser = uniqueOwners[0] || "Sarah Jenkins";
  const totalArr = deals.reduce((acc, d) => acc + (Number(d.arr) || 0), 0);
  const activeCount = deals.filter((d) => !["closed_won", "closed_lost"].includes(d.stage)).length;
  const atRiskCount = deals.filter((d) => ["at_risk", "stalled"].includes(d.risk_level)).length;

  if (loading) return <PageLoader label="Loading pipeline..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Sales Pipeline Management</h2>
          <p className="text-xs text-zinc-400">Track deal velocity, Closer objection handling, and commercial governance</p>
        </div>

        {/* Quick My Queue / All Deals Switcher */}
        <div className="flex items-center rounded-lg border border-zinc-800 bg-zinc-900/60 p-1 text-xs">
          <button
            onClick={() => setOwnerFilter("")}
            className={`rounded-md px-3 py-1 font-medium transition-colors ${
              ownerFilter === "" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            All Deals ({deals.length})
          </button>
          <button
            onClick={() => setOwnerFilter(defaultUser)}
            className={`rounded-md px-3 py-1 font-medium transition-colors flex items-center gap-1.5 ${
              ownerFilter === defaultUser ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <User className="h-3 w-3" />
            <span>My Queue ({deals.filter((d) => d.owner === defaultUser).length})</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Total Pipeline ARR</span>
            <span className="text-2xl font-bold text-white mt-1 block">{formatCurrency(totalArr)}</span>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <DollarSign className="h-5 w-5" />
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Active Deals</span>
            <span className="text-2xl font-bold text-white mt-1 block">{activeCount} in flight</span>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[rgba(12,163,12,0.12)] text-[#0ca30c] border border-[rgba(12,163,12,0.25)]">
            <Layers className="h-5 w-5" />
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 shadow-lg flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">At Risk / Stalled Deals</span>
            <span className="text-2xl font-bold text-white mt-1 block">{atRiskCount} flagged</span>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[rgba(250,178,25,0.12)] text-[#fab219] border border-[rgba(250,178,25,0.25)]">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Filter & Table Container */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 shadow-xl backdrop-blur-md overflow-hidden">
        {/* Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-zinc-800 bg-zinc-950/40">
          <div className="relative w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search deals..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 text-xs flex-wrap">
            {/* Owner Filter */}
            <select
              value={ownerFilter}
              onChange={(e) => setOwnerFilter(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
            >
              <option value="">All Reps</option>
              {uniqueOwners.map((owner) => (
                <option key={owner} value={owner}>
                  {owner}
                </option>
              ))}
            </select>

            {/* Stage Filter */}
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Stages</option>
              <option value="discovery">Discovery</option>
              <option value="proposal">Proposal</option>
              <option value="negotiation">Negotiation</option>
              <option value="contract_sent">Contract Sent</option>
              <option value="closed_won">Closed Won</option>
              <option value="closed_lost">Closed Lost</option>
            </select>

            {/* Risk Filter */}
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Health Statuses</option>
              <option value="healthy">Healthy</option>
              <option value="at_risk">At Risk</option>
              <option value="stalled">Stalled</option>
            </select>

            {(stageFilter || riskFilter || ownerFilter || searchQuery) && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setStageFilter("");
                  setRiskFilter("");
                  setOwnerFilter("");
                  setSearchQuery("");
                }}
                className="text-xs text-zinc-400 h-8"
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Deals Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-950/80 border-b border-zinc-800 text-[11px] font-semibold uppercase text-zinc-400">
              <tr>
                <th className="p-4">Company & Contact</th>
                <th className="p-4">Deal Owner</th>
                <th className="p-4">ARR Amount</th>
                <th className="p-4">Stage</th>
                <th className="p-4">Health Status</th>
                <th className="p-4">Last Activity</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredDeals.map((deal) => (
                <tr key={deal.id} className="hover:bg-zinc-800/40 transition-colors group">
                  <td className="p-4">
                    <Link href={`/dashboard/pipeline/${shortId(deal.id)}`} className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {deal.company}
                    </Link>
                    <div className="text-zinc-400 text-[11px]">
                      {deal.contact_name ? `${deal.contact_name} • ${deal.contact_title || ""}` : "Enterprise Direct"}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center gap-1.5 text-zinc-300 font-medium bg-zinc-900 px-2.5 py-1 rounded-md border border-zinc-800">
                      <User className="h-3 w-3 text-zinc-400" />
                      <span>{deal.owner || "Unassigned"}</span>
                    </span>
                  </td>
                  <td className="p-4 font-mono font-bold text-white">
                    {formatCurrency(deal.arr)}
                  </td>
                  <td className="p-4">
                    <span className="capitalize font-mono text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded text-[11px] border border-zinc-700">
                      {deal.stage}
                    </span>
                  </td>
                  <td className="p-4">
                    <StatusBadge status={deal.risk_level} />
                  </td>
                  <td className="p-4 text-zinc-400 font-mono text-[11px]">
                    {formatDate(deal.last_activity)}
                  </td>
                  <td className="p-4 text-right">
                    <Link href={`/dashboard/pipeline/${shortId(deal.id)}`}>
                      <Button size="sm" variant="ghost" className="h-7 text-xs text-blue-400 hover:text-blue-300 gap-1">
                        <span>View Deal</span>
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
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
