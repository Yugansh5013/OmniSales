import React from "react";
import { ShieldAlert, AlertTriangle, CheckCircle2, TrendingDown, LifeBuoy, Clock, ArrowRight } from "lucide-react";
import { Account } from "@/lib/api";
import { StatusBadge } from "@/lib/../components/StatusBadge";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { Button } from "@/lib/../components/ui/button";

interface AccountCardProps {
  account: Account;
  onPlaybookTrigger?: (account: Account) => void;
}

export function AccountCard({ account, onPlaybookTrigger }: AccountCardProps) {
  const churnRisk = account.churn_risk ?? 0;
  const healthScore = account.health_score ?? 0.5;

  let riskTier = account.metadata?.risk_tier || "healthy";
  if (churnRisk >= 0.75) riskTier = "critical";
  else if (churnRisk >= 0.5) riskTier = "at_risk";
  else if (churnRisk >= 0.25) riskTier = "warning";
  else riskTier = "healthy";

  const topSignals = account.metadata?.top_signals || account.metadata?.signals || [];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-lg backdrop-blur-md transition-all hover:border-zinc-700/80 flex flex-col justify-between space-y-4">
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-white text-sm tracking-tight">{account.company}</h3>
            <span className="text-[11px] text-zinc-400 font-mono uppercase">{account.plan} Plan</span>
          </div>
          <StatusBadge status={riskTier} label={`Churn Risk ${Math.round(churnRisk * 100)}%`} />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-zinc-800/80 text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] text-zinc-500 uppercase font-semibold">ARR</span>
            <span className="font-bold text-white block">{formatCurrency(account.arr)}</span>
          </div>
          <div className="space-y-0.5">
            <span className="text-[10px] text-zinc-500 uppercase font-semibold">Health Score</span>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white">{Math.round(healthScore * 100)}</span>
              <div className="w-12 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    healthScore >= 0.7 ? "bg-[#0ca30c]" : healthScore >= 0.4 ? "bg-[#fab219]" : "bg-[#d03b3b]"
                  }`}
                  style={{ width: `${Math.min(healthScore * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
          <div className="space-y-0.5">
            <span className="text-[10px] text-zinc-500 uppercase font-semibold">Usage & Tickets</span>
            <span className="text-zinc-300 block font-mono">
              {formatPercent(account.usage_pct)} • {account.support_tickets} tkts
            </span>
          </div>
        </div>
      </div>

      {/* Signals Callout */}
      {topSignals.length > 0 && (
        <div className="rounded-lg bg-zinc-950/70 p-3 border border-zinc-800/60 space-y-1.5">
          <span className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400 block">
            Guardian Risk Signals
          </span>
          <div className="space-y-1">
            {topSignals.slice(0, 2).map((sig, idx) => (
              <div key={idx} className="text-xs text-zinc-300 flex items-start gap-1.5">
                <AlertTriangle className="h-3 w-3 text-[#fab219] shrink-0 mt-0.5" />
                <span className="line-clamp-1">{sig}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer Action */}
      <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between">
        <span className="text-[11px] text-zinc-500 font-mono">
          Last active: {account.last_login ? new Date(account.last_login).toLocaleDateString() : "Active"}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPlaybookTrigger && onPlaybookTrigger(account)}
          className="text-xs h-7 gap-1 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
        >
          <span>Retention Play</span>
          <ArrowRight className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}
