import React from "react";
import { CheckCircle2, AlertTriangle, Clock, XCircle, ShieldAlert, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export type StatusType =
  | "healthy"
  | "approved"
  | "completed"
  | "active"
  | "at_risk"
  | "pending_approval"
  | "awaiting_approval"
  | "stalled"
  | "warning"
  | "rejected"
  | "policy_violation"
  | "critical"
  | "good"
  | "serious"
  | string;

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, label, className, size = "md" }: StatusBadgeProps) {
  const norm = String(status || "").toLowerCase();

  let category: "good" | "warning" | "serious" | "critical" = "warning";
  let Icon = AlertTriangle;
  let text = label || status;

  if (["healthy", "approved", "completed", "active", "good", "closed_won", "tier_1", "approved_with_override"].includes(norm)) {
    category = "good";
    Icon = CheckCircle2;
    if (!label) {
      if (norm === "healthy") text = "Healthy";
      else if (norm === "approved") text = "Approved";
      else if (norm === "completed") text = "Completed";
      else if (norm === "closed_won") text = "Closed Won";
      else if (norm === "tier_1") text = "Tier 1 ICP";
      else text = "Active";
    }
  } else if (["at_risk", "pending", "pending_approval", "awaiting_approval", "warning", "proposal", "negotiation", "tier_2"].includes(norm)) {
    category = "warning";
    Icon = AlertTriangle;
    if (!label) {
      if (norm === "at_risk") text = "At Risk";
      else if (norm.includes("approval")) text = "Pending Approval";
      else if (norm === "proposal") text = "Proposal";
      else if (norm === "negotiation") text = "Negotiation";
      else if (norm === "tier_2") text = "Tier 2 Fit";
      else text = "Pending";
    }
  } else if (["stalled", "serious", "monitor", "tier_3", "discovery"].includes(norm)) {
    category = "serious";
    Icon = Clock;
    if (!label) {
      if (norm === "stalled") text = "Stalled";
      else if (norm === "discovery") text = "Discovery";
      else if (norm === "tier_3") text = "Tier 3 Low";
      else text = "Serious";
    }
  } else if (["rejected", "policy_violation", "critical", "closed_lost", "churn_risk"].includes(norm)) {
    category = "critical";
    Icon = norm === "policy_violation" ? ShieldAlert : XCircle;
    if (!label) {
      if (norm === "policy_violation") text = "Policy Violation";
      else if (norm === "rejected") text = "Rejected";
      else if (norm === "closed_lost") text = "Closed Lost";
      else text = "Critical";
    }
  }

  // Exact Validated Dataviz Skill Hex Styling
  const styles = {
    good: "border-[rgba(12,163,12,0.3)] bg-[rgba(12,163,12,0.12)] text-[#0ca30c]",
    warning: "border-[rgba(250,178,25,0.3)] bg-[rgba(250,178,25,0.12)] text-[#fab219]",
    serious: "border-[rgba(236,131,90,0.3)] bg-[rgba(236,131,90,0.12)] text-[#ec835a]",
    critical: "border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.12)] text-[#d03b3b]",
  };

  const iconSizes = {
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
  };

  const paddingSizes = {
    sm: "px-2 py-0.5 text-[11px]",
    md: "px-2.5 py-1 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium tracking-tight select-none",
        styles[category],
        paddingSizes[size],
        className
      )}
    >
      <Icon className={cn(iconSizes[size], "shrink-0")} />
      <span>{text}</span>
    </span>
  );
}
