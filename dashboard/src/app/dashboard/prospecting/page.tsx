"use client";

import React, { useState, useEffect } from "react";
import {
  UserPlus,
  Search,
  Upload,
  Bot,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Building,
  Mail,
  Send,
  X,
  FileSpreadsheet,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { ReasoningTrace } from "@/components/ReasoningTrace";
import { fetchLeads, triggerProspector, importLeads, Lead } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";

export default function ProspectingPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [tierFilter, setTierFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const [qualifying, setQualifying] = useState<boolean>(false);
  const [qualificationResult, setQualificationResult] = useState<Record<string, unknown> | null>(null);

  const [importOpen, setImportOpen] = useState<boolean>(false);
  const [csvText, setCsvText] = useState<string>("");
  const [importing, setImporting] = useState<boolean>(false);

  const loadLeads = async () => {
    try {
      const data = await fetchLeads();
      setLeads(data);
      if (data.length > 0 && !selectedLead) {
        setSelectedLead(data[0]);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, []);

  const handleQualify = async (leadId: string) => {
    setQualifying(true);
    setQualificationResult(null);
    try {
      const res = await triggerProspector(leadId);
      setQualificationResult(res as unknown as Record<string, unknown>);
      await loadLeads();
    } catch (err: unknown) {
      setQualificationResult({ error: (err as Error).message });
    } finally {
      setQualifying(false);
    }
  };

  const handleCsvImport = async () => {
    if (!csvText.trim()) return;
    setImporting(true);
    try {
      const lines = csvText.trim().split("\n");
      const parsedLeads: Array<{ company: string; contact_name?: string; email?: string; title?: string }> = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || (i === 0 && line.toLowerCase().includes("company"))) continue;
        const parts = line.split(",").map((p) => p.trim().replace(/^["']|["']$/g, ""));
        if (parts[0]) {
          parsedLeads.push({
            company: parts[0],
            contact_name: parts[1] || "",
            email: parts[2] || "",
            title: parts[3] || "",
          });
        }
      }

      if (parsedLeads.length > 0) {
        await importLeads(parsedLeads);
        await loadLeads();
        setImportOpen(false);
        setCsvText("");
      }
    } catch {
      // handled
    } finally {
      setImporting(false);
    }
  };

  const filteredLeads = leads.filter((l) => {
    const matchesTier = !tierFilter || l.tier === tierFilter;
    const matchesSearch =
      !searchQuery ||
      l.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.contact_name?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTier && matchesSearch;
  });

  const tier1Count = leads.filter((l) => l.tier === "A" || (l.icp_score && l.icp_score >= 0.8)).length;
  const tier2Count = leads.filter((l) => l.tier === "B" || (l.icp_score && l.icp_score >= 0.5 && l.icp_score < 0.8)).length;
  const tier3Count = leads.filter((l) => l.tier === "C" || l.tier === "D" || (l.icp_score && l.icp_score < 0.5)).length;

  if (loading) return <PageLoader label="Loading prospecting pipeline..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Lead Prospecting & Autonomous Enrichment</h2>
          <p className="text-xs text-zinc-400">Prospector agent: ICP matching, tech stack inference, and cold outreach drafting</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => setImportOpen(true)}
            variant="outline"
            size="sm"
            className="gap-2 border-zinc-700 text-zinc-200 hover:text-white"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Import CSV</span>
          </Button>
        </div>
      </div>

      {/* ICP Tier Metric Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div
          onClick={() => setTierFilter("")}
          className={`cursor-pointer rounded-xl border p-4 transition-all ${
            tierFilter === "" ? "border-blue-500/50 bg-blue-950/20" : "border-zinc-800 bg-zinc-900/60 hover:border-zinc-700"
          }`}
        >
          <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">Total Leads</span>
          <span className="text-2xl font-bold text-white mt-1 block">{leads.length}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">In active pipeline</span>
        </div>

        <div
          onClick={() => setTierFilter("A")}
          className={`cursor-pointer rounded-xl border p-4 transition-all ${
            tierFilter === "A" ? "border-[rgba(12,163,12,0.4)] bg-[rgba(12,163,12,0.1)]" : "border-zinc-800 bg-zinc-900/60 hover:border-zinc-700"
          }`}
        >
          <span className="text-[11px] font-semibold text-[#0ca30c] uppercase tracking-wider block">Tier 1 ICP Fit</span>
          <span className="text-2xl font-bold text-white mt-1 block">{tier1Count}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">High urgency conversion</span>
        </div>

        <div
          onClick={() => setTierFilter("B")}
          className={`cursor-pointer rounded-xl border p-4 transition-all ${
            tierFilter === "B" ? "border-[rgba(250,178,25,0.4)] bg-[rgba(250,178,25,0.1)]" : "border-zinc-800 bg-zinc-900/60 hover:border-zinc-700"
          }`}
        >
          <span className="text-[11px] font-semibold text-[#fab219] uppercase tracking-wider block">Tier 2 Mid-Fit</span>
          <span className="text-2xl font-bold text-white mt-1 block">{tier2Count}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Standard nurture play</span>
        </div>

        <div
          onClick={() => setTierFilter("C")}
          className={`cursor-pointer rounded-xl border p-4 transition-all ${
            tierFilter === "C" ? "border-[rgba(236,131,90,0.4)] bg-[rgba(236,131,90,0.1)]" : "border-zinc-800 bg-zinc-900/60 hover:border-zinc-700"
          }`}
        >
          <span className="text-[11px] font-semibold text-[#ec835a] uppercase tracking-wider block">Tier 3 / Non-ICP</span>
          <span className="text-2xl font-bold text-white mt-1 block">{tier3Count}</span>
          <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">Deprioritized</span>
        </div>
      </div>

      {/* Main Grid: Leads Table + Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Table (7 cols) */}
        <div className="lg:col-span-7 rounded-xl border border-zinc-800 bg-zinc-900/60 shadow-xl backdrop-blur-md overflow-hidden">
          {/* Filter Bar */}
          <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950/40 gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search leads by company or contact..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {tierFilter && (
              <Button size="sm" variant="ghost" onClick={() => setTierFilter("")} className="text-xs text-zinc-400">
                Clear Filter
              </Button>
            )}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-950/80 border-b border-zinc-800 text-[11px] font-semibold uppercase text-zinc-400">
                <tr>
                  <th className="p-3.5">Company & Contact</th>
                  <th className="p-3.5">ICP Score</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60">
                {filteredLeads.map((lead) => {
                  const isSelected = selectedLead?.id === lead.id;
                  const score = lead.icp_score !== null ? Math.round(lead.icp_score * 100) : null;

                  return (
                    <tr
                      key={lead.id}
                      onClick={() => setSelectedLead(lead)}
                      className={`cursor-pointer transition-colors hover:bg-zinc-800/40 ${
                        isSelected ? "bg-blue-950/20 border-l-2 border-blue-500" : ""
                      }`}
                    >
                      <td className="p-3.5">
                        <div className="font-semibold text-white">{lead.company}</div>
                        <div className="text-zinc-400 text-[11px]">
                          {lead.contact_name} • {lead.title}
                        </div>
                      </td>
                      <td className="p-3.5">
                        {score !== null ? (
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-white">{score}%</span>
                            <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  score >= 80 ? "bg-[#0ca30c]" : score >= 50 ? "bg-[#fab219]" : "bg-[#ec835a]"
                                }`}
                                style={{ width: `${score}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <span className="text-zinc-500 font-mono">Unscored</span>
                        )}
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={lead.tier === "A" ? "tier_1" : lead.tier === "B" ? "tier_2" : "tier_3"} />
                      </td>
                      <td className="p-3.5 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedLead(lead);
                            handleQualify(lead.id);
                          }}
                          className="h-7 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-950/40 gap-1"
                        >
                          <Sparkles className="h-3 w-3" />
                          <span>Qualify</span>
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Detail Drawer (5 cols) */}
        <div className="lg:col-span-5 rounded-xl border border-zinc-800 bg-zinc-900/60 shadow-xl backdrop-blur-md p-5 flex flex-col justify-between space-y-4">
          {selectedLead ? (
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between border-b border-zinc-800 pb-3">
                <div>
                  <h3 className="font-bold text-base text-white">{selectedLead.company}</h3>
                  <p className="text-xs text-zinc-400">
                    {selectedLead.contact_name} • {selectedLead.title}
                  </p>
                </div>
                <Button
                  size="sm"
                  onClick={() => handleQualify(selectedLead.id)}
                  disabled={qualifying}
                  className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white"
                >
                  {qualifying ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Bot className="h-3.5 w-3.5" />}
                  <span>{qualifying ? "Evaluating..." : "Run Prospector"}</span>
                </Button>
              </div>

              {/* Enrichment Data Grid */}
              <div className="rounded-lg bg-zinc-950/80 p-3.5 border border-zinc-800 space-y-2.5 text-xs">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400 block">
                  Enriched Company Profile
                </span>
                <div className="grid grid-cols-2 gap-2 text-zinc-300">
                  <div>
                    <span className="text-zinc-500 block text-[10px]">Industry</span>
                    <span className="font-medium">{selectedLead.enrichment?.industry || "Not Specified"}</span>
                  </div>
                  <div>
                    <span className="text-zinc-500 block text-[10px]">Employees</span>
                    <span className="font-medium">
                      {selectedLead.enrichment?.employees ? `${selectedLead.enrichment.employees}+` : "Unspecified"}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 block text-[10px]">Funding</span>
                    <span className="font-medium">{selectedLead.enrichment?.funding || "Not Disclosed"}</span>
                  </div>
                  <div>
                    <span className="text-zinc-500 block text-[10px]">Estimated ARR</span>
                    <span className="font-medium">{selectedLead.enrichment?.revenue_est || "Not Estimated"}</span>
                  </div>
                </div>

                {/* Tech Stack Tags */}
                {selectedLead.enrichment?.tech_stack && selectedLead.enrichment.tech_stack.length > 0 && (
                  <div className="pt-2 border-t border-zinc-800/80">
                    <span className="text-[10px] font-semibold text-zinc-500 block mb-1">Tech Stack</span>
                    <div className="flex flex-wrap gap-1">
                      {selectedLead.enrichment.tech_stack.map((t, idx) => (
                        <span key={idx} className="bg-zinc-800 text-zinc-300 text-[10px] px-2 py-0.5 rounded font-mono">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Live Qualification Reasoning Trace or Sequence Draft */}
              {Boolean(qualificationResult) && (
                <div className="space-y-3">
                  <ReasoningTrace
                    reasoning={
                      (qualificationResult?.reasoning as string[]) || [
                        `score_icp: Evaluated ICP match for ${selectedLead.company} -> ICP Fit ${selectedLead.icp_score ? Math.round(selectedLead.icp_score * 100) + '%' : 'Tier ' + selectedLead.tier}`,
                        "generate_outreach: Crafted personalized executive sequence addressing enterprise scale",
                      ]
                    }
                    isStreaming={qualifying}
                    agentName="Prospector"
                  />

                  {Boolean(qualificationResult?.draft) && (
                    <div className="rounded-lg bg-zinc-950 p-3.5 border border-zinc-800 text-xs space-y-1.5">
                      <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider block">
                        Generated Outreach Sequence
                      </span>
                      <p className="text-zinc-300 whitespace-pre-wrap leading-relaxed">
                        {String(qualificationResult?.draft)}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-zinc-500 text-xs">
              Select a lead from the table to view enrichment details and trigger Prospector qualification.
            </div>
          )}
        </div>
      </div>

      {/* CSV Import Modal */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent className="max-w-md bg-zinc-950 border-zinc-800 p-6">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="h-4 w-4 text-blue-400" />
              <DialogTitle>Import Leads via CSV</DialogTitle>
            </div>
            <DialogDescription>
              Paste CSV rows below in the format: <code className="text-zinc-300 font-mono">Company, Contact Name, Email, Title</code>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 my-2">
            <textarea
              rows={6}
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder="Acme Corp, Jane Doe, jane@acme.com, VP Sales&#10;Starlight AI, John Smith, john@starlight.io, Head of RevOps"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-xs text-zinc-100 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" size="sm" onClick={() => setImportOpen(false)} className="text-xs">
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleCsvImport}
              disabled={importing || !csvText.trim()}
              className="text-xs bg-blue-600 hover:bg-blue-500 text-white gap-1.5"
            >
              {importing ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
              <span>Import Leads</span>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
