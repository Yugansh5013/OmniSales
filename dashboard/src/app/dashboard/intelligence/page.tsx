"use client";

import React, { useState, useEffect } from "react";
import { Compass, Swords, DollarSign, ShieldAlert, Sparkles, RefreshCw, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchCompetitors, fetchA2ABattlecard, fetchA2AWinback, Competitor } from "@/lib/api";
import { PageLoader } from "@/components/ui/page-loader";

const DEFAULT_TABS = ["AcmeCRM", "PipeDrive", "HubSpot", "Salesforce", "Zoho"];

export default function CompetitiveIntelligencePage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [tabs, setTabs] = useState<string[]>(DEFAULT_TABS);
  const [selectedComp, setSelectedComp] = useState<string>("AcmeCRM");
  const [battlecard, setBattlecard] = useState<Record<string, unknown> | null>(null);
  const [winback, setWinback] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [fetchingCard, setFetchingCard] = useState<boolean>(false);
  const [newCompetitor, setNewCompetitor] = useState<string>("");

  useEffect(() => {
    fetchCompetitors()
      .then((data) => setCompetitors(data))
      .catch(() => {})
      .finally(() => setLoading(false));
    handleFetchBattlecard("AcmeCRM");
  }, []);

  const handleFetchBattlecard = async (name: string) => {
    setSelectedComp(name);
    setFetchingCard(true);
    setWinback(null);
    try {
      const [card, wb] = await Promise.all([fetchA2ABattlecard(name), fetchA2AWinback(name)]);
      setBattlecard(card as Record<string, unknown>);
      setWinback(wb as Record<string, unknown>);
    } catch {
      // silent
    } finally {
      setFetchingCard(false);
    }
  };

  const handleAddCompetitor = () => {
    const name = newCompetitor.trim();
    if (!name) return;
    if (!tabs.some((t) => t.toLowerCase() === name.toLowerCase())) {
      setTabs((prev) => [...prev, name]);
    }
    setNewCompetitor("");
    handleFetchBattlecard(name);
  };

  if (loading) return <PageLoader label="Loading competitive intelligence..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="border-b border-zinc-800 pb-5">
        <h2 className="text-xl font-bold tracking-tight text-white">Competitive Intelligence (Spy A2A Agent)</h2>
        <p className="text-xs text-zinc-400">
          Agent-to-Agent protocol battlecards, pricing history models, and automated winback playbooks
        </p>
      </div>

      {/* Competitor Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 pb-3">
        {tabs.map((name) => (
          <button
            key={name}
            onClick={() => handleFetchBattlecard(name)}
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
              selectedComp === name
                ? "bg-blue-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            }`}
          >
            {name}
          </button>
        ))}
        <div className="flex items-center gap-1 ml-2">
          <input
            type="text"
            value={newCompetitor}
            onChange={(e) => setNewCompetitor(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddCompetitor()}
            placeholder="Add any competitor..."
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 w-40 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <Button size="sm" variant="outline" onClick={handleAddCompetitor} className="h-8 w-8 p-0">
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Battlecard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Battlecard Breakdown */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <div className="flex items-center gap-2">
              <Swords className="h-4 w-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-white">{selectedComp} Tactical Battlecard</h3>
            </div>
            <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700">
              A2A Agent Card v1.0
            </span>
          </div>

          <div className="space-y-4 text-xs">
            {fetchingCard ? (
              <p className="text-zinc-500">Searching the live web via Tavily + synthesizing...</p>
            ) : (
              <>
                {battlecard?.cache_status && (
                  <p className="text-[10px] text-zinc-500 font-mono">{battlecard.cache_status as string}</p>
                )}

                {(() => {
                  const advantage = (battlecard?.differentiators as Record<string, unknown> | undefined)?.omnisales_advantage;
                  return Array.isArray(advantage) && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] uppercase font-semibold text-[#0ca30c] block">Where OmniSales Wins</span>
                      <ul className="list-disc list-inside text-zinc-300 space-y-1">
                        {(advantage as string[]).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })()}

                {Array.isArray(battlecard?.weaknesses) && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-semibold text-[#fab219] block">Competitor Vulnerabilities</span>
                    <ul className="list-disc list-inside text-zinc-300 space-y-1">
                      {(battlecard!.weaknesses as string[]).map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {battlecard?.pricing && typeof battlecard.pricing === "object" && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-semibold text-blue-400 block">Their Pricing</span>
                    <ul className="text-zinc-300 space-y-1 font-mono">
                      {Object.entries(battlecard.pricing as Record<string, string>).map(([tier, price]) => (
                        <li key={tier}>{tier}: {price}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {Array.isArray(battlecard?.sources) && (battlecard!.sources as string[]).length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-zinc-800/60">
                    <span className="text-[10px] uppercase font-semibold text-zinc-500 block">Live Sources</span>
                    <ul className="space-y-1">
                      {(battlecard!.sources as string[]).map((url, i) => (
                        <li key={i}>
                          <a href={url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate block">
                            {url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {!battlecard?.differentiators && !battlecard?.weaknesses && (
                  <p className="text-zinc-500">{(battlecard?.note as string) || "No battle card data available for this competitor."}</p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Right: Displacement Strategy */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-[#0ca30c]" />
              <h3 className="text-sm font-semibold text-white">Displacement & Winback Playbook</h3>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            {fetchingCard ? (
              <p className="text-zinc-500">Generating displacement strategy via LLM win/loss analysis...</p>
            ) : winback && Array.isArray(winback.displacement_plays) ? (
              <>
                <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800 space-y-2">
                  <span className="font-semibold text-zinc-200 block">Displacement Plays</span>
                  <ul className="list-disc list-inside text-zinc-400 space-y-1 leading-relaxed">
                    {(winback.displacement_plays as string[]).map((play, i) => (
                      <li key={i}>{play}</li>
                    ))}
                  </ul>
                </div>

                {Array.isArray(winback.our_differentiators) && (
                  <div className="rounded-lg bg-zinc-950/80 p-4 border border-zinc-800 space-y-2">
                    <span className="font-semibold text-zinc-200 block">Lead With</span>
                    <ul className="list-disc list-inside text-zinc-400 space-y-1 leading-relaxed">
                      {(winback.our_differentiators as string[]).map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {winback.recommended_timing && (
                  <p className="text-zinc-500 italic">{winback.recommended_timing as string}</p>
                )}
              </>
            ) : (
              <p className="text-zinc-500">{(winback?.note as string) || "No winback playbook available for this competitor."}</p>
            )}

            <div className="pt-2 border-t border-zinc-800/80 flex items-center justify-between text-zinc-400 font-mono text-[11px]">
              <span>Port: <strong>8080 (A2A Server)</strong></span>
              <span>FastMCP Tool: <strong>get_winback_strategy</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
