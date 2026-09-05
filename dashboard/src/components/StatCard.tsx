import React from "react";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  icon: LucideIcon;
  variant?: "default" | "good" | "warning" | "serious" | "critical";
  className?: string;
}

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  variant = "default",
  className,
}: StatCardProps) {
  const iconVariants = {
    default: "bg-blue-600/10 text-blue-400 border-blue-500/20",
    good: "bg-[rgba(12,163,12,0.12)] text-[#0ca30c] border-[rgba(12,163,12,0.25)]",
    warning: "bg-[rgba(250,178,25,0.12)] text-[#fab219] border-[rgba(250,178,25,0.25)]",
    serious: "bg-[rgba(236,131,90,0.12)] text-[#ec835a] border-[rgba(236,131,90,0.25)]",
    critical: "bg-[rgba(208,59,59,0.12)] text-[#d03b3b] border-[rgba(208,59,59,0.25)]",
  };

  return (
    <div
      className={cn(
        "relative rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-lg backdrop-blur-md transition-all hover:border-zinc-700/80 group",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          {title}
        </span>
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg border",
            iconVariants[variant]
          )}
        >
          <Icon className="h-4 w-4 shrink-0" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {trend && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 text-xs font-medium",
              trend.isPositive ? "text-[#0ca30c]" : "text-[#d03b3b]"
            )}
          >
            {trend.isPositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-xs text-zinc-400">{subtitle}</p>}
    </div>
  );
}
