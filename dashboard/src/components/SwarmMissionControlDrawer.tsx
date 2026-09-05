"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  X,
  RefreshCw,
  Search,
  Zap,
  Shield,
  Terminal,
  Activity,
  ArrowRight,
  Sparkles,
  Radio,
  Cpu,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface LogEntry {
  id: string;
  timestamp: string;
  agent: "orchestrator" | "prospector" | "closer" | "guardian" | "spy" | "crm";
  message: string;
  type: "info" | "success" | "warning" | "highlight" | "target";
}

interface ActiveTarget {
  name: string;
  type: "lead" | "deal" | "account";
  subtitle: string;
  status: string;
  riskOrScore?: string;
}

interface SwarmMissionControlDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onScanCompleted?: () => void;
}

export function SwarmMissionControlDrawer({
  isOpen,
  onClose,
  onScanCompleted,
}: SwarmMissionControlDrawerProps) {
  const router = useRouter();
  const [scanning, setScanning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeTarget, setActiveTarget] = useState<ActiveTarget | null>(null);
  const [tokenCounter, setTokenCounter] = useState(0);
  const [signalsCount, setSignalsCount] = useState(0);
  const [tasksQueuedCount, setTasksQueuedCount] = useState(0);
  const [scanSummary, setScanSummary] = useState<string | null>(null);

  const [agentStates, setAgentStates] = useState<{
    prospector: { status: "idle" | "inspecting" | "synthesizing" | "done"; detail: string; tasks: number };
    closer: { status: "idle" | "inspecting" | "a2a" | "done"; detail: string; tasks: number };
    guardian: { status: "idle" | "inspecting" | "synthesizing" | "done"; detail: string; tasks: number };
  }>({
    prospector: { status: "idle", detail: "Standing by", tasks: 0 },
    closer: { status: "idle", detail: "Standing by", tasks: 0 },
    guardian: { status: "idle", detail: "Standing by", tasks: 0 },
  });

  const logsEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const getTimestamp = () => {
    const d = new Date();
    return d.toTimeString().split(" ")[0];
  };

  const appendLog = (
    agent: LogEntry["agent"],
    message: string,
    type: LogEntry["type"] = "info"
  ) => {
    const newEntry: LogEntry = {
      id: Math.random().toString(36).substring(2, 9),
      timestamp: getTimestamp(),
      agent,
      message,
      type,
    };
    setLogs((prev) => [...prev, newEntry]);
  };

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const handleStreamEvent = (data: Record<string, any>) => {
    const eventType = data.event;

    if (eventType === "sweep_start") {
      appendLog("orchestrator", data.message || "🛰️ Swarm Sweep initialized.", "highlight");
    } else if (eventType === "portfolio_loaded") {
      appendLog("crm", data.message, "info");
    } else if (eventType === "inspect_entity") {
      const isLead = data.entity_type === "lead";
      const isDeal = data.entity_type === "deal";
      const isAccount = data.entity_type === "account";

      setActiveTarget({
        name: data.company,
        type: data.entity_type,
        subtitle: isLead
          ? `Tier: ${data.tier} • Status: ${data.status}`
          : isDeal
          ? `$${(data.arr || 0).toLocaleString()} ARR • Stage: ${data.stage} • Risk: ${data.risk}`
          : `$${(data.arr || 0).toLocaleString()} ARR • Churn Risk: ${(data.churn_risk * 100).toFixed(0)}%`,
        status: "ANALYZING TELEMETRY",
        riskOrScore: isLead ? `Tier ${data.tier}` : isDeal ? `${data.risk}` : `${(data.churn_risk * 100).toFixed(0)}% Risk`,
      });

      appendLog(
        "orchestrator",
        `🔍 [INSPECT] ${data.company} (${data.entity_type.toUpperCase()})`,
        "target"
      );

      if (isLead) {
        setAgentStates((prev) => ({
          ...prev,
          prospector: { ...prev.prospector, status: "inspecting", detail: `Evaluating '${data.company}'` },
        }));
      } else if (isDeal) {
        setAgentStates((prev) => ({
          ...prev,
          closer: { ...prev.closer, status: "inspecting", detail: `Evaluating '${data.company}'` },
        }));
      } else if (isAccount) {
        setAgentStates((prev) => ({
          ...prev,
          guardian: { ...prev.guardian, status: "inspecting", detail: `Evaluating '${data.company}'` },
        }));
      }
    } else if (eventType === "dispatch_agent") {
      setSignalsCount((prev) => prev + 1);
      appendLog(
        data.agent as LogEntry["agent"],
        `⚡ DISPATCH → ${data.message}`,
        "highlight"
      );

      if (data.agent === "prospector") {
        setAgentStates((prev) => ({
          ...prev,
          prospector: { ...prev.prospector, status: "synthesizing", detail: `Qualifying ${data.company}` },
        }));
      } else if (data.agent === "closer") {
        setAgentStates((prev) => ({
          ...prev,
          closer: { ...prev.closer, status: "a2a", detail: `A2A Intel & Objections` },
        }));
      } else if (data.agent === "guardian") {
        setAgentStates((prev) => ({
          ...prev,
          guardian: { ...prev.guardian, status: "synthesizing", detail: `30-Day Churn Playbook` },
        }));
      }
    } else if (eventType === "agent_action") {
      const isA2A = data.step === "a2a_intelligence";
      appendLog(
        isA2A ? "spy" : (data.agent as LogEntry["agent"]),
        data.message,
        isA2A ? "highlight" : "info"
      );
    } else if (eventType === "task_queued") {
      setTasksQueuedCount((prev) => prev + 1);
      setTokenCounter((prev) => prev + (data.tokens || 1800));

      appendLog(
        data.agent as LogEntry["agent"],
        `✨ ${data.message} (+${data.tokens || 1800} tokens)`,
        "success"
      );

      if (data.agent === "prospector") {
        setAgentStates((prev) => ({
          ...prev,
          prospector: { ...prev.prospector, status: "done", tasks: prev.prospector.tasks + 1, detail: "Outreach Queued" },
        }));
      } else if (data.agent === "closer") {
        setAgentStates((prev) => ({
          ...prev,
          closer: { ...prev.closer, status: "done", tasks: prev.closer.tasks + 1, detail: "Re-engagement Queued" },
        }));
      } else if (data.agent === "guardian") {
        setAgentStates((prev) => ({
          ...prev,
          guardian: { ...prev.guardian, status: "done", tasks: prev.guardian.tasks + 1, detail: "Retention Plan Queued" },
        }));
      }
    } else if (eventType === "sweep_complete") {
      appendLog("orchestrator", data.message, "success");
      setScanSummary(data.summary);
      setScanning(false);
      setActiveTarget(null);

      if (onScanCompleted) {
        onScanCompleted();
      }
    }
  };

  // Start real-time stream using fetch ReadableStream
  const startStreamScan = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setScanning(true);
    setLogs([]);
    setActiveTarget(null);
    setTokenCounter(0);
    setSignalsCount(0);
    setTasksQueuedCount(0);
    setScanSummary(null);

    setAgentStates({
      prospector: { status: "idle", detail: "Standing by", tasks: 0 },
      closer: { status: "idle", detail: "Standing by", tasks: 0 },
      guardian: { status: "idle", detail: "Standing by", tasks: 0 },
    });

    const apiBase =
      process.env.NEXT_PUBLIC_API_URL ||
      (typeof window !== "undefined" && window.location.hostname !== ""
        ? `http://${window.location.hostname}:8000`
        : "http://localhost:8000");

    const streamUrl = `${apiBase}/api/orchestrator/scan/stream`;

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(streamUrl, {
        signal: controller.signal,
        headers: { Accept: "text/event-stream" },
      });

      if (!response.ok || !response.body) {
        throw new Error(`Failed to connect to stream (HTTP ${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const trimmed = part.trim();
          if (!trimmed || !trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const data = JSON.parse(jsonStr);
            handleStreamEvent(data);
          } catch (e) {
            console.error("JSON parse error on stream chunk:", jsonStr, e);
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        console.error("Stream reader error:", err);
        appendLog("orchestrator", `Stream ended: ${err.message || "Cycle finished"}`, "info");
      }
    } finally {
      setScanning(false);
      setActiveTarget(null);
    }
  };

  useEffect(() => {
    if (isOpen && logs.length === 0 && !scanning) {
      startStreamScan();
    }
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const getAgentBadge = (agent: LogEntry["agent"]) => {
    switch (agent) {
      case "orchestrator":
        return <span className="text-purple-400 font-bold">[ORCHESTRATOR]</span>;
      case "prospector":
        return <span className="text-cyan-400 font-bold">[PROSPECTOR]</span>;
      case "closer":
        return <span className="text-blue-400 font-bold">[CLOSER]</span>;
      case "guardian":
        return <span className="text-emerald-400 font-bold">[GUARDIAN]</span>;
      case "spy":
        return <span className="text-amber-400 font-bold">[SPY A2A]</span>;
      case "crm":
        return <span className="text-zinc-400 font-bold">[CRM MCP]</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-md transition-opacity">
      {/* Backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Slide-out Drawer */}
      <div className="fixed inset-y-0 right-0 flex max-w-full pl-6 sm:pl-10">
        <div className="w-screen max-w-2xl bg-zinc-950/95 border-l border-zinc-800/80 shadow-2xl flex flex-col backdrop-blur-2xl animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/80 bg-zinc-900/80 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 shadow-inner">
                <Radio className="h-4 w-4 animate-pulse" />
                {scanning && (
                  <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
                  </span>
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-white tracking-wide">Swarm Mission Control</h2>
                  {scanning ? (
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-blue-500/20 border border-blue-500/40 text-blue-400 flex items-center gap-1.5 animate-pulse">
                      <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping"></span>
                      LIVE EVENT STREAM
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      CYCLE FINISHED
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400">High-velocity microsecond orchestration telemetry</p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="rounded-lg p-2 text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Active Target Spotlight (Animated Scanning Laser) */}
          {activeTarget && scanning && (
            <div className="px-6 pt-4">
              <div className="relative overflow-hidden rounded-xl border border-blue-500/40 bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-zinc-950 p-3.5 shadow-lg shadow-blue-950/50 animate-in fade-in zoom-in duration-200">
                {/* Laser scan line animation */}
                <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-[pulse_1.5s_infinite]" />

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-500/20 border border-blue-400/30 text-blue-300">
                      <Activity className="h-3.5 w-3.5 animate-spin" />
                    </span>
                    <div>
                      <div className="text-[10px] font-mono uppercase tracking-wider text-blue-400 font-semibold">
                        CURRENT TARGET UNDER ANALYSIS
                      </div>
                      <div className="text-sm font-bold text-white flex items-center gap-2">
                        {activeTarget.name}
                        <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300 border border-zinc-700">
                          {activeTarget.type.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60 font-semibold">
                      {activeTarget.riskOrScore || "EVALUATING"}
                    </span>
                    <p className="text-[10px] text-zinc-400 pt-0.5">{activeTarget.subtitle}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {/* 3 Autonomous Agents Matrix */}
            <div className="grid grid-cols-3 gap-3">
              {/* Prospector */}
              <div
                className={`p-3 rounded-xl border transition-all ${
                  agentStates.prospector.status !== "idle"
                    ? "bg-cyan-950/30 border-cyan-500/50 shadow-lg shadow-cyan-950/30"
                    : "bg-zinc-900/60 border-zinc-800/80"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                    <Search className="h-3.5 w-3.5" /> Prospector
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                      agentStates.prospector.status === "synthesizing"
                        ? "bg-cyan-900/80 text-cyan-200 animate-pulse"
                        : agentStates.prospector.status === "done"
                        ? "bg-emerald-950 border border-emerald-500/40 text-emerald-300"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {agentStates.prospector.status}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-300 truncate">{agentStates.prospector.detail}</p>
                {agentStates.prospector.tasks > 0 && (
                  <div className="mt-1.5 text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> +{agentStates.prospector.tasks} sequence queued
                  </div>
                )}
              </div>

              {/* Closer */}
              <div
                className={`p-3 rounded-xl border transition-all ${
                  agentStates.closer.status !== "idle"
                    ? "bg-blue-950/30 border-blue-500/50 shadow-lg shadow-blue-950/30"
                    : "bg-zinc-900/60 border-zinc-800/80"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-blue-300 flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5" /> Closer
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                      agentStates.closer.status === "a2a"
                        ? "bg-amber-900/80 text-amber-200 animate-pulse"
                        : agentStates.closer.status === "done"
                        ? "bg-emerald-950 border border-emerald-500/40 text-emerald-300"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {agentStates.closer.status}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-300 truncate">{agentStates.closer.detail}</p>
                {agentStates.closer.tasks > 0 && (
                  <div className="mt-1.5 text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> +{agentStates.closer.tasks} objection draft queued
                  </div>
                )}
              </div>

              {/* Guardian */}
              <div
                className={`p-3 rounded-xl border transition-all ${
                  agentStates.guardian.status !== "idle"
                    ? "bg-emerald-950/30 border-emerald-500/50 shadow-lg shadow-emerald-950/30"
                    : "bg-zinc-900/60 border-zinc-800/80"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                    <Shield className="h-3.5 w-3.5" /> Guardian
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                      agentStates.guardian.status === "synthesizing"
                        ? "bg-emerald-900/80 text-emerald-200 animate-pulse"
                        : agentStates.guardian.status === "done"
                        ? "bg-emerald-950 border border-emerald-500/40 text-emerald-300"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {agentStates.guardian.status}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-300 truncate">{agentStates.guardian.detail}</p>
                {agentStates.guardian.tasks > 0 && (
                  <div className="mt-1.5 text-[10px] font-mono text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> +{agentStates.guardian.tasks} retention plan queued
                  </div>
                )}
              </div>
            </div>

            {/* Live Telemetry Ticker */}
            <div className="grid grid-cols-3 gap-2.5 p-3 rounded-xl border border-zinc-800 bg-zinc-900/40 text-center font-mono">
              <div className="p-2 rounded-lg bg-zinc-950/70 border border-zinc-800/80">
                <div className="text-[10px] text-zinc-400 uppercase">Tokens Streamed</div>
                <div className="text-sm font-bold text-blue-400 flex items-center justify-center gap-1 pt-0.5">
                  <Cpu className="h-3 w-3 text-blue-400" />
                  {tokenCounter.toLocaleString()}
                </div>
              </div>
              <div className="p-2 rounded-lg bg-zinc-950/70 border border-zinc-800/80">
                <div className="text-[10px] text-zinc-400 uppercase">Signals Found</div>
                <div className="text-sm font-bold text-cyan-400 pt-0.5">
                  {signalsCount}
                </div>
              </div>
              <div className="p-2 rounded-lg bg-zinc-950/70 border border-zinc-800/80">
                <div className="text-[10px] text-zinc-400 uppercase">Tasks Queued</div>
                <div className="text-sm font-bold text-emerald-400 pt-0.5">
                  +{tasksQueuedCount}
                </div>
              </div>
            </div>

            {/* Live Terminal Stream */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/90 shadow-xl overflow-hidden backdrop-blur-md">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-900/80 text-xs text-zinc-400 font-mono">
                <span className="flex items-center gap-2">
                  <Terminal className="h-3.5 w-3.5 text-zinc-500" />
                  High-Frequency Swarm Execution Stream
                </span>
                <span className="text-[10px] text-zinc-500">{logs.length} micro-events logged</span>
              </div>

              <div className="p-4 font-mono text-xs space-y-2.5 max-h-72 overflow-y-auto bg-black/50 scrollbar-thin scrollbar-thumb-zinc-800">
                {logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-2.5 leading-relaxed animate-in fade-in duration-150">
                    <span className="text-[10px] text-zinc-500 whitespace-nowrap pt-0.5 font-mono">
                      {log.timestamp}
                    </span>
                    <div className="flex-1 space-x-1.5">
                      {getAgentBadge(log.agent)}
                      <span
                        className={`text-xs ${
                          log.type === "highlight"
                            ? "text-white font-bold"
                            : log.type === "target"
                            ? "text-cyan-300 font-semibold"
                            : log.type === "success"
                            ? "text-emerald-300 font-semibold"
                            : log.type === "warning"
                            ? "text-amber-300"
                            : "text-zinc-300"
                        }`}
                      >
                        {log.message}
                      </span>
                    </div>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </div>

            {/* Sweep Summary Banner */}
            {scanSummary && (
              <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-emerald-400">
                  <Sparkles className="h-4 w-4" />
                  Orchestrator Sweep Summary
                </div>
                <p className="text-zinc-300">{scanSummary}</p>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-5 border-t border-zinc-800 bg-zinc-900/90 backdrop-blur-md flex items-center justify-between gap-3">
            <Button
              onClick={startStreamScan}
              disabled={scanning}
              variant="outline"
              size="sm"
              className="gap-2 border-zinc-700 text-zinc-300 hover:text-white"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${scanning ? "animate-spin" : ""}`} />
              <span>{scanning ? "Streaming..." : "Re-trigger Swarm"}</span>
            </Button>

            <Button
              onClick={() => {
                onClose();
                router.push("/dashboard/approvals");
              }}
              className="gap-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-400 text-white font-semibold text-xs h-9 px-5 shadow-lg shadow-blue-900/40 transition-all cursor-pointer"
            >
              <span>Review Approvals Queue</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
