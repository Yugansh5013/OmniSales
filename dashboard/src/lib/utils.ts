import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Combines Tailwind class names cleanly */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formats currency amounts */
export function formatCurrency(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "$0";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Formats percentages */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "0%";
  return `${Math.round(value * 100)}%`;
}

/** Formats relative or standard dates */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return "Never";
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
}

export const formatDateTime = formatDate;
export const formatRelativeTime = formatDate;

export function getAgentColor(agent: string): string {
  const norm = agent.toLowerCase();
  if (norm.includes("closer")) return "#3b82f6";
  if (norm.includes("prospector")) return "#a855f7";
  if (norm.includes("guardian")) return "#f59e0b";
  if (norm.includes("spy")) return "#ef4444";
  return "#71717a";
}

export function formatTokens(tokens: number | null | undefined): string {
  if (!tokens) return "0";
  return tokens.toLocaleString();
}

export function formatCost(cost: number | null | undefined): string {
  if (!cost) return "$0.00";
  return `$${cost.toFixed(4)}`;
}

export function formatTaskType(taskType: string): string {
  return taskType.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function getAgentBadgeClass(agent: string): string {
  const norm = agent.toLowerCase();
  if (norm.includes("closer")) return "text-blue-400 bg-blue-500/10 border-blue-500/20";
  if (norm.includes("prospector")) return "text-purple-400 bg-purple-500/10 border-purple-500/20";
  if (norm.includes("guardian")) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
  if (norm.includes("spy")) return "text-red-400 bg-red-500/10 border-red-500/20";
  return "text-zinc-400 bg-zinc-800 border-zinc-700";
}

export function getAgentIcon(agent: string): string {
  const norm = agent.toLowerCase();
  if (norm.includes("closer")) return "Closer";
  if (norm.includes("prospector")) return "Prospector";
  if (norm.includes("guardian")) return "Guardian";
  if (norm.includes("spy")) return "Spy";
  return "Agent";
}

export function getRiskBadgeClass(risk: string): string {
  const norm = risk.toLowerCase();
  if (norm === "healthy") return "text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border-[rgba(12,163,12,0.25)]";
  if (norm === "at_risk") return "text-[#fab219] bg-[rgba(250,178,25,0.12)] border-[rgba(250,178,25,0.25)]";
  if (norm === "stalled") return "text-[#ec835a] bg-[rgba(236,131,90,0.12)] border-[rgba(236,131,90,0.25)]";
  return "text-zinc-400 bg-zinc-800 border-zinc-700";
}

export function getStageBadgeClass(stage: string): string {
  return "text-zinc-300 bg-zinc-800 border-zinc-700";
}

export function computeGaugeArc(score: number, radius: number) {
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - Math.min(Math.max(score, 0), 1) * circumference;
  return { circumference, offset };
}

export function computeHealthColor(score: number): string {
  if (score >= 0.7) return "#0ca30c";
  if (score >= 0.4) return "#fab219";
  return "#d03b3b";
}

export function computeSparklinePath(values: number[], width: number, height: number): string {
  if (values.length < 2) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);

  return values
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

export function computeTrendDirection(values: number[]): "up" | "down" | "flat" {
  if (values.length < 2) return "flat";
  const diff = values[values.length - 1] - values[0];
  if (diff > 0.01) return "up";
  if (diff < -0.01) return "down";
  return "flat";
}

/** Last 8 hex chars of a UUID — used in URLs so /dashboard/pipeline/00000011 reads
 * clean instead of the full 20000000-0000-0000-0000-000000000011. Uses the *last*
 * segment, not the first, because this dataset's seed UUIDs all share the same
 * leading "20000000-0000-0000-0000-" prefix — only the tail actually varies.
 * The backend resolves this suffix back to the full row. */
export function shortId(id: string): string {
  return id.slice(-8);
}
