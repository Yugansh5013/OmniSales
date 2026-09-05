"use client";

import React, { useState } from "react";
import { CheckCircle2, XCircle, Send, Edit3, MessageSquare } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/lib/../components/ui/dialog";
import { Button } from "@/lib/../components/ui/button";
import { Textarea } from "@/lib/../components/ui/textarea";
import { AgentTask, approveTask } from "@/lib/api";
import { FormattedDraft } from "./FormattedDraft";

interface DraftEditorModalProps {
  task: AgentTask | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onResolved: (taskId: string, approved: boolean) => void;
}

export function DraftEditorModal({ task, open, onOpenChange, onResolved }: DraftEditorModalProps) {
  const [draft, setDraft] = useState<string>(task?.draft || "");
  const [feedback, setFeedback] = useState<string>("");
  const [viewMode, setViewMode] = useState<"edit" | "preview">("edit");
  const [submitting, setSubmitting] = useState<boolean>(false);

  React.useEffect(() => {
    if (task) {
      setDraft(task.draft || "");
      setFeedback("");
    }
  }, [task]);

  if (!task) return null;

  const handleApprove = async () => {
    setSubmitting(true);
    try {
      await approveTask(task.id, true, feedback, draft);
      onResolved(task.id, true);
      onOpenChange(false);
    } catch {
      // handled
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    setSubmitting(true);
    try {
      await approveTask(task.id, false, feedback, draft);
      onResolved(task.id, false);
      onOpenChange(false);
    } catch {
      // handled
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl w-[min(48rem,95vw)] bg-zinc-950 border-zinc-800 shadow-2xl p-6" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Edit3 className="h-4 w-4" />
            </span>
            <DialogTitle>Review & Edit Draft before Dispatch</DialogTitle>
          </div>
          <DialogDescription>
            Target: <strong className="text-white">{task.target_name}</strong> • Agent: <strong className="text-blue-400 uppercase">{task.agent_name}</strong> • Task: {task.task_type}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-2">
          {/* Agent Reasoning Summary */}
          {task.reasoning && (
            <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/40 p-3 text-xs text-zinc-400">
              <span className="font-semibold text-zinc-300 block mb-1">Agent Strategy Reasoning:</span>
              <p className="max-h-28 overflow-y-auto leading-relaxed whitespace-pre-wrap pr-1">{task.reasoning}</p>
            </div>
          )}

          {/* Editable Draft Area / Formatted Preview */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-zinc-300">
                {task.task_type === "retention_play" || task.agent_name === "guardian"
                  ? "Retention Playbook & Plan"
                  : task.task_type === "outreach_sequence" || task.agent_name === "prospector"
                  ? "Outreach Sequences"
                  : "Email Content"}
              </label>

              <div className="flex items-center gap-2">
                <span className="text-[10px] text-zinc-500 font-mono">{draft.length} chars</span>
                <div className="flex items-center gap-1 rounded bg-zinc-900 p-0.5 border border-zinc-800 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setViewMode("edit")}
                    className={`px-2.5 py-1 rounded font-medium transition-colors ${
                      viewMode === "edit" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Write / Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode("preview")}
                    className={`px-2.5 py-1 rounded font-medium transition-colors ${
                      viewMode === "preview" ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    Preview Formatted
                  </button>
                </div>
              </div>
            </div>

            {viewMode === "edit" ? (
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={16}
                className="font-sans text-sm bg-zinc-900 border-zinc-800 leading-relaxed text-zinc-100 min-h-[360px]"
                placeholder="Draft email content..."
              />
            ) : (
              <div className="bg-zinc-900/90 border border-zinc-800 rounded-md p-4 min-h-[360px] max-h-[460px] overflow-y-auto scrollbar-thin">
                <FormattedDraft content={draft} />
              </div>
            )}
          </div>

          {/* Rep Guidance / Feedback */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5 text-zinc-400" />
              <span>Feedback / Rejection Reason (Optional)</span>
            </label>
            <input
              type="text"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="e.g. Tone adjusted for C-suite prospect, added 10% discount mention..."
              className="flex h-9 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs text-white shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="destructive"
            size="sm"
            onClick={handleReject}
            disabled={submitting}
            className="gap-1.5 text-xs"
          >
            <XCircle className="h-3.5 w-3.5" />
            <span>Reject Task</span>
          </Button>

          <Button
            variant="success"
            size="sm"
            onClick={handleApprove}
            disabled={submitting}
            className="gap-1.5 text-xs bg-[#0ca30c]/90 hover:bg-[#0ca30c] text-white"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Approve & Dispatch Email</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
