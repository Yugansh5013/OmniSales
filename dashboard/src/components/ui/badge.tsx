import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "good" | "warning" | "serious" | "critical";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "border-transparent bg-zinc-800 text-zinc-100",
    secondary: "border-transparent bg-zinc-800 text-zinc-300",
    destructive: "border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.12)] text-[#d03b3b]",
    outline: "border-zinc-700 text-zinc-300",
    good: "border-[rgba(12,163,12,0.3)] bg-[rgba(12,163,12,0.12)] text-[#0ca30c]",
    warning: "border-[rgba(250,178,25,0.3)] bg-[rgba(250,178,25,0.12)] text-[#fab219]",
    serious: "border-[rgba(236,131,90,0.3)] bg-[rgba(236,131,90,0.12)] text-[#ec835a]",
    critical: "border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.12)] text-[#d03b3b]",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
