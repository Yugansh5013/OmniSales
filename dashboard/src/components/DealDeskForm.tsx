"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  CreditCard,
  CheckCircle2,
  ExternalLink,
  Copy,
  AlertTriangle,
  RefreshCw,
  Zap,
} from "lucide-react";
import { Button } from "@/lib/../components/ui/button";
import { Input } from "@/lib/../components/ui/input";
import { Textarea } from "@/lib/../components/ui/textarea";
import { evaluateDealDesk, generatePaymentLink, DealDeskEvaluation, PaymentLinkResponse } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface DealDeskFormProps {
  dealId: string;
  arr: number;
  initialDiscount?: number;
  initialMonths?: number;
  initialTerms?: string;
  initialCustomSla?: boolean;
  companyName: string;
  onLinkCreated?: (link: PaymentLinkResponse) => void;
}

export function DealDeskForm({
  dealId,
  arr,
  initialDiscount = 0,
  initialMonths = 12,
  initialTerms = "annual_upfront",
  initialCustomSla = false,
  companyName,
  onLinkCreated,
}: DealDeskFormProps) {
  const [discountPct, setDiscountPct] = useState<number>(initialDiscount);
  const [contractMonths, setContractMonths] = useState<number>(initialMonths);
  const [paymentTerms, setPaymentTerms] = useState<string>(initialTerms);
  const [customSla, setCustomSla] = useState<boolean>(initialCustomSla);

  const [override, setOverride] = useState<boolean>(false);
  const [overrideReason, setOverrideReason] = useState<string>("");

  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<DealDeskEvaluation | null>(null);

  const [generating, setGenerating] = useState<boolean>(false);
  const [paymentLink, setPaymentLink] = useState<PaymentLinkResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Run pre-flight evaluation whenever terms change
  useEffect(() => {
    let active = true;
    async function runEval() {
      setEvaluating(true);
      setErrorMessage(null);
      try {
        const res = await evaluateDealDesk(dealId, {
          discount_pct: Number(discountPct),
          contract_months: Number(contractMonths),
          payment_terms: paymentTerms,
          custom_sla: customSla,
          override,
          override_reason: overrideReason,
        });
        if (active) setEvaluation(res);
      } catch (err: unknown) {
        if (active) {
          const res = (err as { response?: { violations?: [] } })?.response;
          if (res) setEvaluation(res as unknown as DealDeskEvaluation);
        }
      } finally {
        if (active) setEvaluating(false);
      }
    }
    const timer = setTimeout(runEval, 300);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [dealId, discountPct, contractMonths, paymentTerms, customSla, override, overrideReason]);

  const effectiveArr = Math.max(arr * (1 - discountPct / 100), 100);

  const handleGenerateLink = async () => {
    setGenerating(true);
    setErrorMessage(null);
    try {
      const res = await generatePaymentLink(dealId, {
        discount_pct: Number(discountPct),
        contract_months: Number(contractMonths),
        payment_terms: paymentTerms,
        custom_sla: customSla,
        override,
        override_reason: overrideReason,
      });
      setPaymentLink(res);
      if (onLinkCreated) onLinkCreated(res);
    } catch (err: unknown) {
      const errorMsg = (err as Error).message || "Failed to generate payment link";
      setErrorMessage(errorMsg);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyLink = () => {
    if (paymentLink?.short_url) {
      navigator.clipboard.writeText(paymentLink.short_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isBlocked = evaluation?.status === "policy_violation" && !override;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <CreditCard className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Deal Desk Commercial Governance</h3>
            <p className="text-xs text-zinc-400">Deterministic corporate policy gating & Razorpay payment links</p>
          </div>
        </div>
        {evaluating ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-blue-400">
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            Evaluating...
          </span>
        ) : evaluation?.status === "approved" || evaluation?.status === "approved_with_override" ? (
          <span className="inline-flex items-center gap-1 text-xs text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2.5 py-1 rounded-full font-medium">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Policy Cleared
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs text-[#d03b3b] bg-[rgba(208,59,59,0.12)] border border-[rgba(208,59,59,0.25)] px-2.5 py-1 rounded-full font-medium">
            <ShieldAlert className="h-3.5 w-3.5" />
            {evaluation?.violations_count || 1} Violation(s)
          </span>
        )}
      </div>

      {/* Interactive Terms Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Discount % */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-zinc-300 font-medium">Discount Requested</label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                min="0"
                max="60"
                value={discountPct}
                onChange={(e) => setDiscountPct(Math.min(60, Math.max(0, Number(e.target.value) || 0)))}
                className="w-14 bg-zinc-950 border border-zinc-800 rounded px-2 py-0.5 text-right font-mono font-bold text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-zinc-400 font-bold">%</span>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="60"
            step="1"
            value={discountPct}
            onChange={(e) => setDiscountPct(Number(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-zinc-500 font-mono">
            <span>0% (Standard)</span>
            <span>20% (Rep Max)</span>
            <span>60% (VP Hard Cap)</span>
          </div>
        </div>

        {/* Contract Duration */}
        <div className="space-y-1.5">
          <label className="text-zinc-300 font-medium">Contract Duration (Months)</label>
          <select
            value={contractMonths}
            onChange={(e) => setContractMonths(Number(e.target.value))}
            className="flex h-9 w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1 text-xs text-white shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value={3}>3 Months (Non-Standard)</option>
            <option value={6}>6 Months (Short Term)</option>
            <option value={12}>12 Months (Standard Annual)</option>
            <option value={24}>24 Months (2-Year Multi-Year)</option>
            <option value={36}>36 Months (3-Year Strategic)</option>
          </select>
        </div>

        {/* Payment Terms */}
        <div className="space-y-1.5">
          <label className="text-zinc-300 font-medium">Payment Terms</label>
          <select
            value={paymentTerms}
            onChange={(e) => setPaymentTerms(e.target.value)}
            className="flex h-9 w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1 text-xs text-white shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="annual_upfront">Annual Upfront (Standard)</option>
            <option value="net_30">Net 30 Days</option>
            <option value="net_60">Net 60 Days</option>
            <option value="net_90">Net 90 Days (Extended)</option>
            <option value="quarterly">Quarterly Installments</option>
            <option value="monthly">Monthly Recurring</option>
          </select>
        </div>

        {/* Custom SLA */}
        <div className="space-y-1.5 flex flex-col justify-end">
          <label className="flex items-center gap-2 p-2.5 rounded-lg border border-zinc-800 bg-zinc-950 cursor-pointer hover:border-zinc-700 transition-colors">
            <input
              type="checkbox"
              checked={customSla}
              onChange={(e) => setCustomSla(e.target.checked)}
              className="rounded accent-blue-500 h-4 w-4"
            />
            <span className="text-zinc-200">Include Custom Enterprise SLA (99.99%)</span>
          </label>
        </div>
      </div>

      {/* Effective Amount Summary */}
      <div className="flex items-center justify-between rounded-lg bg-zinc-950/80 p-3.5 border border-zinc-800 font-mono text-xs">
        <span className="text-zinc-400">Base ARR: <strong className="text-zinc-200">{formatCurrency(arr)}</strong></span>
        <span className="text-zinc-400">Discount: <strong className="text-[#fab219]">-{discountPct}%</strong></span>
        <span className="text-zinc-300 font-bold">
          Effective Payment: <span className="text-[#0ca30c] text-sm">{formatCurrency(effectiveArr)}</span>
        </span>
      </div>

      {/* Policy Violations Callout */}
      {evaluation?.status === "policy_violation" && (
        <div className="rounded-lg border border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.08)] p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#d03b3b]">
            <ShieldAlert className="h-4 w-4 shrink-0" />
            <span>Commercial Terms Violate Deal Desk Corporate Governance</span>
          </div>

          <div className="space-y-2">
            {evaluation.violations?.map((v, idx) => (
              <div key={idx} className="text-xs text-zinc-300 flex items-start gap-2 bg-zinc-950/50 p-2.5 rounded border border-[rgba(208,59,59,0.25)]">
                <span className="text-[#d03b3b] font-bold uppercase text-[10px] bg-[rgba(208,59,59,0.15)] px-1.5 py-0.5 rounded border border-[rgba(208,59,59,0.3)] shrink-0">
                  {v.code}
                </span>
                <span className="text-zinc-300 leading-relaxed">{v.message}</span>
              </div>
            ))}
          </div>

          {/* Counter-Proposal Card */}
          {evaluation.counter_proposal && (
            <div className="rounded-lg border border-[rgba(250,178,25,0.3)] bg-[rgba(250,178,25,0.08)] p-3 space-y-2 mt-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#fab219]">
                <Zap className="h-3.5 w-3.5" />
                <span>Automated Deal Desk Counter-Proposal:</span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">{evaluation.counter_proposal.explanation}</p>
              <div className="flex flex-wrap gap-3 text-[11px] font-mono text-zinc-300 pt-1">
                <span>Max Allowed Discount: <strong className="text-white">{evaluation.counter_proposal.proposed_discount_pct}%</strong></span>
                <span>Term: <strong className="text-white">{evaluation.counter_proposal.proposed_contract_months}mo</strong></span>
                <span>Payment: <strong className="text-white">{evaluation.counter_proposal.proposed_payment_terms}</strong></span>
              </div>
            </div>
          )}

          {/* Executive Override Section */}
          <div className="pt-2 border-t border-[rgba(208,59,59,0.25)] space-y-2">
            <label className="flex items-center gap-2 text-xs font-semibold text-zinc-200 cursor-pointer">
              <input
                type="checkbox"
                checked={override}
                onChange={(e) => setOverride(e.target.checked)}
                className="rounded accent-blue-500 h-4 w-4"
              />
              <span>Executive / VP Sales Override</span>
            </label>
            {override && (
              <div className="space-y-1.5 animate-in fade-in">
                <Textarea
                  placeholder="Enter executive override justification (required for compliance audit trail)..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="text-xs min-h-[60px]"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="rounded-lg border border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.1)] p-3 text-xs text-[#d03b3b] flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Generated Razorpay Link Result Card */}
      {paymentLink && (
        <div className="rounded-lg border border-[rgba(12,163,12,0.3)] bg-[rgba(12,163,12,0.08)] p-4 space-y-3 animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#0ca30c]">
              <CheckCircle2 className="h-4 w-4" />
              <span>Razorpay Payment Link Generated & Persisted</span>
            </div>
            {paymentLink.is_simulated && (
              <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700">
                Safe Simulation
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 bg-zinc-950 p-2.5 rounded-lg border border-zinc-800">
            <input
              type="text"
              readOnly
              value={paymentLink.short_url}
              className="w-full bg-transparent text-xs text-blue-400 font-mono focus:outline-none"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={handleCopyLink}
              className="gap-1.5 text-xs h-7 shrink-0"
            >
              <Copy className="h-3 w-3" />
              <span>{copied ? "Copied!" : "Copy"}</span>
            </Button>
            <a
              href={paymentLink.short_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-zinc-400 hover:text-white transition-colors"
              title="Open link in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          <p className="text-[11px] text-zinc-400">
            Link ID: <strong className="text-zinc-300 font-mono">{paymentLink.id}</strong> • Persisted to deal agent log & tasks queue.
          </p>
        </div>
      )}

      {/* Action Button */}
      <Button
        onClick={handleGenerateLink}
        disabled={generating || isBlocked || (override && !overrideReason.trim())}
        className="w-full gap-2 text-xs h-10 font-semibold"
        variant={isBlocked ? "outline" : "default"}
      >
        {generating ? (
          <>
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Generating Razorpay Link...</span>
          </>
        ) : (
          <>
            <CreditCard className="h-4 w-4" />
            <span>
              {override
                ? "Authorize & Generate Override Payment Link"
                : isBlocked
                ? "Resolve Policy Violations to Generate Link"
                : "Generate Razorpay Payment Link"}
            </span>
          </>
        )}
      </Button>
    </div>
  );
}
