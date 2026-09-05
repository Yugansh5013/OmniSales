"use client";

import React, { useState, useEffect } from "react";
import { Cpu, CheckCircle2, ChevronDown, ChevronRight, Sparkles, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReasoningTraceProps {
  reasoning: string[] | string;
  isStreaming?: boolean;
  className?: string;
  agentName?: string;
}

export function ReasoningTrace({
  reasoning,
  isStreaming = false,
  className,
  agentName = "Closer",
}: ReasoningTraceProps) {
  const steps: string[] = Array.isArray(reasoning)
    ? reasoning
    : typeof reasoning === "string"
    ? reasoning.split("\n").filter((s) => s.trim().length > 0)
    : [];

  const [visibleCount, setVisibleCount] = useState(isStreaming ? 0 : steps.length);
  const [expandedIndices, setExpandedIndices] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (isStreaming) {
      setVisibleCount(0);
      const timer = setInterval(() => {
        setVisibleCount((prev) => {
          if (prev < steps.length) return prev + 1;
          clearInterval(timer);
          return prev;
        });
      }, 500);
      return () => clearInterval(timer);
    } else {
      setVisibleCount(steps.length);
    }
  }, [reasoning, isStreaming, steps.length]);

  const toggleExpand = (idx: number) => {
    setExpandedIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (steps.length === 0) {
    return (
      <div className={cn("rounded-xl border border-zinc-800 bg-zinc-950/80 p-5 text-center text-xs text-zinc-500", className)}>
        <Terminal className="mx-auto h-5 w-5 mb-2 text-zinc-600" />
        <span>No execution trace recorded yet.</span>
      </div>
    );
  }

  return (
    <div className={cn("rounded-xl border border-zinc-800 bg-zinc-950/90 shadow-xl overflow-hidden backdrop-blur-md", className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 px-4 py-3 bg-zinc-900/60">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Cpu className="h-3.5 w-3.5" />
          </div>
          <span className="text-xs font-semibold text-white tracking-tight">
            {agentName} Agent Thought Trace
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && visibleCount < steps.length ? (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full animate-pulse">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping" />
              Thinking...
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2 py-0.5 rounded-full">
              <CheckCircle2 className="h-3 w-3" />
              Complete ({steps.length} steps)
            </span>
          )}
        </div>
      </div>

      {/* Step Sequence */}
      <div className="p-4 space-y-3 font-mono text-xs">
        {steps.slice(0, visibleCount).map((step, idx) => {
          // Parse node name if in format "node_name: details"
          const parts = step.split(":");
          const hasNode = parts.length > 1 && parts[0].length < 30;
          const nodeName = hasNode ? parts[0].trim() : `Step ${idx + 1}`;
          const details = hasNode ? parts.slice(1).join(":").trim() : step;
          const isCurrent = isStreaming && idx === visibleCount - 1 && visibleCount < steps.length;
          const isExpanded = expandedIndices[idx] ?? true;

          return (
            <div
              key={idx}
              className={cn(
                "rounded-lg border transition-all duration-300 animate-in fade-in slide-in-from-left-2",
                isCurrent
                  ? "border-blue-500/40 bg-blue-950/20 shadow-sm"
                  : "border-zinc-800/80 bg-zinc-900/40"
              )}
            >
              <div
                onClick={() => toggleExpand(idx)}
                className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-zinc-800/40 transition-colors rounded-lg select-none"
              >
                <div className="flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-zinc-800 text-[10px] font-bold text-zinc-300 border border-zinc-700">
                    {idx + 1}
                  </span>
                  <span className="font-semibold text-zinc-200">{nodeName}</span>
                </div>
                <div className="flex items-center gap-2">
                  {isCurrent && (
                    <Sparkles className="h-3.5 w-3.5 text-blue-400 animate-spin" />
                  )}
                  {isExpanded ? (
                    <ChevronDown className="h-3.5 w-3.5 text-zinc-400" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 text-zinc-400" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="px-3 pb-3 pt-1 border-t border-zinc-800/40 text-zinc-400 whitespace-pre-wrap leading-relaxed">
                  {details}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
