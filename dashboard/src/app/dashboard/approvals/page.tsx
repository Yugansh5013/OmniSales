"use client";

import React, { useState, useEffect } from "react";
import {
  CheckSquare,
  CheckCircle2,
  XCircle,
  Edit3,
  Bot,
  RefreshCw,
  Clock,
  Sparkles,
  Filter,
  DollarSign,
  Shield,
  Send,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { DraftEditorModal } from "@/components/DraftEditorModal";
import { FormattedDraft } from "@/components/FormattedDraft";
import { fetchTasks, approveTask, AgentTask } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { PageLoader } from "@/components/ui/page-loader";

export default function ApprovalsPage() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("pending_approval");
  const [agentFilter, setAgentFilter] = useState<string>("");
  const [ownerFilter, setOwnerFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const [activeTask, setActiveTask] = useState<AgentTask | null>(null);
  const [editorOpen, setEditorOpen] = useState<boolean>(false);
  const [actionInProgress, setActionInProgress] = useState<Record<string, boolean>>({});

  const loadTasks = async () => {
    try {
      const data = await fetchTasks(statusFilter, agentFilter, ownerFilter);
      setTasks(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [statusFilter, agentFilter, ownerFilter]);

  const handleQuickAction = async (taskId: string, approved: boolean) => {
    setActionInProgress((prev) => ({ ...prev, [taskId]: true }));
    try {
      await approveTask(taskId, approved, "");
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch {
      // handled
    } finally {
      setActionInProgress((prev) => ({ ...prev, [taskId]: false }));
    }
  };

  const handleOpenEditor = (task: AgentTask) => {
    setActiveTask(task);
    setEditorOpen(true);
  };

  const handleResolved = (taskId: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  };

  if (loading) return <PageLoader label="Loading approvals queue..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white">Human-In-The-Loop Approval Queue</h2>
          <p className="text-xs text-zinc-400">Review, edit, and dispatch agent-generated outreach, discount terms, and retention plays</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStatusFilter("pending_approval")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              statusFilter === "pending_approval"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            }`}
          >
            Pending Queue ({tasks.length})
          </button>
          <button
            onClick={() => setStatusFilter("approved")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              statusFilter === "approved"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            }`}
          >
            Approved History
          </button>
          <button
            onClick={() => setStatusFilter("rejected")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              statusFilter === "rejected"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            }`}
          >
            Rejected History
          </button>
        </div>

        {/* Owner + Agent Filters */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center rounded-lg border border-zinc-800 bg-zinc-900/60 p-0.5">
            <button
              onClick={() => setOwnerFilter("")}
              className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                ownerFilter === "" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              All Tasks
            </button>
            <button
              onClick={() => setOwnerFilter("Sarah Jenkins")}
              className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                ownerFilter === "Sarah Jenkins" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              My Tasks
            </button>
          </div>
          <span className="text-zinc-500">Agent:</span>
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Agents</option>
            <option value="closer">Closer</option>
            <option value="prospector">Prospector</option>
            <option value="guardian">Guardian</option>
          </select>
        </div>
      </div>

      {/* Task Queue List */}
      <div className="space-y-4">
        {tasks.length > 0 ? (
          tasks.map((task) => {
            const inProgress = actionInProgress[task.id] || false;

            return (
              <div
                key={task.id}
                className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-xl backdrop-blur-md space-y-4 hover:border-zinc-700 transition-all"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold uppercase text-xs">
                      {task.agent_name.slice(0, 2)}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-sm">{task.target_name}</h3>
                        <span className="text-zinc-400 text-xs">•</span>
                        <span className="text-xs text-blue-400 font-mono uppercase font-semibold">
                          {task.agent_name} Agent
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-500 font-mono">
                        Task: <strong className="text-zinc-300">{task.task_type}</strong> • Queued: {formatDate(task.created_at)}
                      </p>
                    </div>
                  </div>

                  <StatusBadge status={task.status} />
                </div>

                {/* Reasoning Callout */}
                {task.reasoning && (
                  <div className="rounded-lg bg-zinc-950/80 p-3.5 border border-zinc-800/80 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400 uppercase text-[10px] font-bold tracking-wider flex items-center gap-1.5">
                        <Sparkles className="h-3 w-3 text-blue-400" />
                        Agent Strategy & Executive Reasoning
                      </span>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        {task.model_used?.includes("20b") ? "openai/gpt-oss-20b" : "Executive Strategy Brief"}
                      </span>
                    </div>
                    <div className="space-y-1.5">
                      {(() => {
                        const raw = task.reasoning || "";
                        const regex = /(?:^|\s)([a-z_]{3,25}:)/g;
                        const matches = [...raw.matchAll(regex)];
                        if (matches.length <= 1) {
                          return (
                            <div className="text-zinc-200 leading-relaxed text-[11px] space-y-2 bg-zinc-900/40 p-2.5 rounded border border-zinc-800/50">
                              {raw.split("\n\n").map((para, pIdx) => (
                                <p key={pIdx}>{para}</p>
                              ))}
                            </div>
                          );
                        }
                        const steps: { step: string; text: string }[] = [];
                        for (let i = 0; i < matches.length; i++) {
                          const currentMatch = matches[i];
                          const stepName = currentMatch[1].replace(":", "");
                          const startIndex = currentMatch.index + currentMatch[0].length;
                          const endIndex = i + 1 < matches.length ? matches[i + 1].index : raw.length;
                          const text = raw.substring(startIndex, endIndex).trim();
                          steps.push({ step: stepName, text });
                        }
                        return steps.map((s, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-zinc-300">
                            <span className="font-mono text-[10px] font-semibold bg-zinc-900 border border-zinc-800 text-blue-400 px-1.5 py-0.5 rounded shrink-0">
                              {s.step}
                            </span>
                            <span className="leading-relaxed text-[11px] text-zinc-300">{s.text}</span>
                          </div>
                        ));
                      })()}
                    </div>
                  </div>
                )}

                {/* Draft Preview Box */}
                {task.draft && (
                  <div className="rounded-lg bg-zinc-950/90 p-4 border border-blue-900/30 text-xs space-y-2">
                    {(() => {
                      const isRetention = task.task_type === "retention_play" || task.agent_name === "guardian";
                      const isProspector = task.task_type === "outreach_sequence" || task.agent_name === "prospector";
                      const title = isRetention
                        ? "Tailored Retention Playbook & Action Plan"
                        : isProspector
                        ? "Generated Multi-Persona Outreach Sequences"
                        : "Generated Email Draft";
                      return (
                        <div className="flex items-center justify-between text-[11px] font-semibold text-blue-400">
                          <span className="flex items-center gap-1.5">
                            {isRetention ? <Shield className="h-3.5 w-3.5" /> : isProspector ? <Send className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
                            {title}
                          </span>
                          <span className="text-zinc-500 font-mono">{task.draft.length} chars</span>
                        </div>
                      );
                    })()}
                    <div className="max-h-72 overflow-y-auto bg-zinc-900/60 p-4 rounded-lg border border-zinc-800/80 pr-3 scrollbar-thin">
                      <FormattedDraft content={task.draft} />
                    </div>
                  </div>
                )}

                {/* Feedback left on this task (visible in history views) */}
                {task.feedback && (
                  <div className="rounded-lg bg-blue-950/20 p-3 border border-blue-900/30 text-xs">
                    <span className="text-blue-400 uppercase text-[10px] font-bold block mb-0.5">Your Feedback</span>
                    <p className="text-zinc-300">{task.feedback}</p>
                  </div>
                )}

                {/* Footer Action Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                  <div className="text-[11px] text-zinc-500 font-mono">
                    Model: {task.model_used || "openai/gpt-oss-120b"}{task.tokens_used ? ` • Tokens: ${task.tokens_used.toLocaleString()}` : ""}
                  </div>

                  {statusFilter === "pending_approval" && (
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenEditor(task)}
                        className="text-xs h-8 gap-1.5 border-zinc-700 text-zinc-200 hover:text-white"
                      >
                        <Edit3 className="h-3.5 w-3.5 text-blue-400" />
                        <span>Edit Draft</span>
                      </Button>

                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleQuickAction(task.id, false)}
                        disabled={inProgress}
                        className="text-xs h-8 gap-1.5"
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        <span>Reject</span>
                      </Button>

                      <Button
                        size="sm"
                        variant="success"
                        onClick={() => handleQuickAction(task.id, true)}
                        disabled={inProgress}
                        className="text-xs h-8 gap-1.5 bg-[#0ca30c]/90 hover:bg-[#0ca30c] text-white"
                      >
                        {inProgress ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                        <span>Approve & Send</span>
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-16 text-center text-zinc-500 text-xs">
            <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-[#0ca30c] opacity-80" />
            <p className="font-medium text-zinc-300">Approval queue is empty.</p>
            <p className="mt-1">All agent outreach and discount plays have been reviewed.</p>
          </div>
        )}
      </div>

      {/* Draft Editor Modal */}
      <DraftEditorModal
        task={activeTask}
        open={editorOpen}
        onOpenChange={setEditorOpen}
        onResolved={handleResolved}
      />
    </div>
  );
}
