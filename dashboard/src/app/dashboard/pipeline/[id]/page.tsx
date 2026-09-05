"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  TrendingUp,
  Bot,
  RefreshCw,
  Sparkles,
  ArrowLeft,
  Mail,
  User,
  Clock,
  CheckCircle2,
  FileText,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { ReasoningTrace } from "@/components/ReasoningTrace";
import { DealDeskForm } from "@/components/DealDeskForm";
import { fetchDeal, fetchDealTimeline, triggerCloser, Deal, TimelineEvent, PaymentLinkResponse } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";
import Link from "next/link";

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const dealId = String(params?.id || "");

  const [deal, setDeal] = useState<Deal | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [triggerResult, setTriggerResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadDeal = async () => {
    if (!dealId) return;
    try {
      // The URL carries a short id (first 8 hex chars) — resolve to the full
      // UUID before fetching the timeline, whose target_id column needs it.
      const d = await fetchDeal(dealId).catch(() => null);
      const fullId = d?.id || dealId;
      const t = await fetchDealTimeline(fullId).catch(() => []);
      if (d) setDeal(d);
      setTimeline(t);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeal();
  }, [dealId]);

  const handleTriggerCloser = async () => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await triggerCloser(deal?.id || dealId);
      setTriggerResult(res as Record<string, unknown>);
      await loadDeal();
    } catch (err: unknown) {
      setTriggerResult({ error: (err as Error).message });
    } finally {
      setTriggering(false);
    }
  };

  if (loading) return <PageLoader label="Loading deal..." />;

  if (!deal && !loading) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-zinc-400">Deal not found.</p>
        <Link href="/dashboard/pipeline">
          <Button variant="outline">Back to Pipeline</Button>
        </Link>
      </div>
    );
  }

  let thread: Array<{ from?: string; body?: string; date?: string; timestamp?: string }> = [];
  if (Array.isArray(deal?.closer_thread)) {
    thread = deal.closer_thread;
  } else if (typeof deal?.closer_thread === "string") {
    try {
      const parsed = JSON.parse(deal.closer_thread);
      if (Array.isArray(parsed)) thread = parsed;
    } catch {
      thread = [];
    }
  }

  const timelineList: TimelineEvent[] = Array.isArray(timeline) ? timeline : [];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div className="flex items-center gap-3">
          <Link href="/dashboard/pipeline">
            <Button size="icon" variant="ghost" className="h-8 w-8 text-zinc-400 hover:text-white">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-white">{deal?.company}</h2>
              {deal && <StatusBadge status={deal.risk_level} />}
            </div>
            <p className="text-xs text-zinc-400">
              Stage: <strong className="text-zinc-200 capitalize">{deal?.stage}</strong> • ARR: <strong className="text-[#0ca30c]">{formatCurrency(deal?.arr)}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={handleTriggerCloser}
            disabled={triggering}
            className="gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs h-9"
          >
            {triggering ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Bot className="h-3.5 w-3.5" />}
            <span>{triggering ? "Running Closer..." : "Trigger Closer Agent"}</span>
          </Button>
        </div>
      </div>

      {/* Main Grid: Left (Thread & Trace) | Right (Deal Desk Form & Timeline) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (6 cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* Dynamic Agent Reasoning Trace */}
          {(Boolean(triggerResult) || timelineList.length > 0) && (
            <ReasoningTrace
              reasoning={
                (triggerResult?.reasoning as string[]) ||
                (timelineList[0]?.reasoning
                  ? [timelineList[0].reasoning]
                  : [
                      `analyze_deal: Deal loaded in stage '${deal?.stage || "discovery"}', ARR ${formatCurrency(deal?.arr || 0)}`,
                      `classify_risk: Health status '${deal?.risk_level || "healthy"}' evaluated -> Commercial governance active`,
                    ])
              }
              isStreaming={triggering}
              agentName={
                triggering || Boolean(triggerResult)
                  ? "Closer"
                  : timelineList[0]?.agent_name
                  ? timelineList[0].agent_name
                      .split("_")
                      .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(" ")
                  : "Closer"
              }
            />
          )}

          {/* Generated Follow-up / Objection Draft */}
          {Boolean(triggerResult?.draft) && (
            <div className="rounded-xl border border-blue-500/30 bg-blue-950/20 p-5 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-blue-400">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4" />
                  Closer Re-Engagement Draft Generated
                </span>
                <span className="text-[10px] font-mono bg-blue-900/60 px-2 py-0.5 rounded">
                  Status: {String(triggerResult?.status || "completed")}
                </span>
              </div>
              <p className="text-xs text-zinc-200 whitespace-pre-wrap leading-relaxed bg-zinc-950/60 p-3 rounded-lg border border-blue-900/40">
                {String(triggerResult?.draft || "")}
              </p>
            </div>
          )}

          {/* Customer Conversation Thread */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-xl backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-zinc-400" />
                <h3 className="text-sm font-semibold text-white">Email Conversation History</h3>
              </div>
              <span className="text-xs text-zinc-500 font-mono">{thread.length} messages</span>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
              {thread.length > 0 ? (
                thread.map((msg, idx) => {
                  const isOutbound = msg.from?.includes("omnisales") || msg.from?.includes("sales") || msg.from === "rep";
                  return (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                        isOutbound
                          ? "bg-blue-950/20 border-blue-900/40 text-blue-100 ml-4"
                          : "bg-zinc-950/80 border-zinc-800 text-zinc-200 mr-4"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400">
                        <span className="font-semibold">
                          {isOutbound ? "OmniSales Closer Rep (Outbound)" : `Buyer (${msg.from || "Prospect"})`}
                        </span>
                        <span>{formatDate(msg.timestamp || msg.date)}</span>
                      </div>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.body}</p>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-10 text-xs text-zinc-500">
                  No previous email threads logged for this deal.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column (6 cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* Deal Desk Commercial Terms & Razorpay Payment Link Generator */}
          {deal && (
            <DealDeskForm
              dealId={deal.id}
              arr={Number(deal.arr) || 0}
              companyName={deal.company}
              initialDiscount={Number(deal.discount_pct) || 0}
              initialMonths={Number(deal.contract_months) || 12}
              initialTerms={deal.payment_terms || "annual_upfront"}
              initialCustomSla={Boolean(deal.custom_sla)}
              onLinkCreated={() => loadDeal()}
            />
          )}

          {/* Deal Agent Timeline */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-xl backdrop-blur-md space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-zinc-400" />
                <h3 className="text-sm font-semibold text-white">Deal Governance Audit Timeline</h3>
              </div>
              <span className="text-xs text-zinc-500 font-mono">{timelineList.length} events</span>
            </div>

            <div className="space-y-3 font-mono text-xs max-h-80 overflow-y-auto">
              {timelineList.length > 0 ? (
                timelineList.map((event) => (
                  <div key={event.id} className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-blue-400 font-bold uppercase text-[10px]">
                        {event.agent_name} • {event.task_type}
                      </span>
                      <StatusBadge status={event.status} size="sm" />
                    </div>
                    <p className="text-zinc-300 font-sans text-xs">{event.reasoning}</p>
                    <div className="text-[10px] text-zinc-500 pt-1">
                      {formatDate(event.created_at)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-xs text-zinc-500">
                  No governance timeline events recorded yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
