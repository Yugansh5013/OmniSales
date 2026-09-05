"use client";

import React, { useState, useRef, useEffect } from "react";
import { Bot, User, Send, Sparkles, RefreshCw, Play, X, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { orchestratorChat, scanOrchestrator } from "@/lib/api";

interface ChatMessage {
  id: string;
  sender: "user" | "orchestrator";
  text: string;
  timestamp: string;
  contextLoaded?: boolean;
}

const PROMPT_SUGGESTIONS = [
  "What is the current status of our revenue pipeline?",
  "Which accounts need immediate churn intervention?",
  "Summarize Closer deals stalled > 7 days",
];

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      sender: "orchestrator",
      text: "Hi, I'm the OmniSales Orchestrator. Ask me about pipeline risk, churn accounts, or autonomous outreach decisions.",
      timestamp: new Date().toISOString(),
      contextLoaded: true,
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, open]);

  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputMessage;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInputMessage("");
    setLoading(true);

    try {
      const res = await orchestratorChat(textToSend);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "orchestrator",
          text: res.response || "Task processed by orchestrator.",
          timestamp: res.timestamp || new Date().toISOString(),
          contextLoaded: Boolean(res.context_loaded),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "orchestrator",
          text: "Encountered an issue communicating with the orchestrator agent.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerScan = async () => {
    setScanning(true);
    try {
      await scanOrchestrator();
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: "orchestrator",
          text: "Autonomous CRM portfolio scan completed across all agents.",
          timestamp: new Date().toISOString(),
          contextLoaded: true,
        },
      ]);
    } finally {
      setScanning(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg shadow-blue-950/40 border border-blue-500/40 hover:bg-blue-500 transition-colors"
        title="Chat with the Orchestrator"
      >
        <MessageSquare className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex h-[560px] w-[380px] flex-col rounded-xl border border-zinc-800 bg-zinc-950/95 shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
            <Bot className="h-4 w-4" />
          </span>
          <div>
            <p className="text-xs font-semibold text-white leading-none">Orchestrator</p>
            <p className="text-[10px] text-zinc-500">Central agent supervisor</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="outline"
            onClick={handleTriggerScan}
            disabled={scanning}
            className="h-7 gap-1 text-[10px] border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
          >
            {scanning ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            <span>Scan</span>
          </Button>
          <button
            onClick={() => setOpen(false)}
            className="rounded-md p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((m) => (
          <div key={m.id} className={`flex gap-2 ${m.sender === "user" ? "justify-end" : "justify-start"}`}>
            {m.sender === "orchestrator" && (
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Bot className="h-3.5 w-3.5" />
              </span>
            )}
            <div
              className={`max-w-[78%] rounded-lg px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
                m.sender === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-900 border border-zinc-800 text-zinc-200"
              }`}
            >
              {m.text}
              {m.contextLoaded && (
                <div className="mt-1 flex items-center gap-1 text-[9px] text-blue-400/80">
                  <Sparkles className="h-2.5 w-2.5" />
                  <span>Live DB context loaded</span>
                </div>
              )}
            </div>
            {m.sender === "user" && (
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-zinc-300">
                <User className="h-3.5 w-3.5" />
              </span>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-[10px] text-zinc-500 pl-8">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Orchestrator is thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions (only when conversation is fresh) */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-1.5 px-3 pb-2">
          {PROMPT_SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleSendMessage(s)}
              className="rounded-full border border-zinc-800 bg-zinc-900/60 px-2.5 py-1 text-[10px] text-zinc-400 hover:text-white hover:border-zinc-700 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex items-center gap-2 border-t border-zinc-800 bg-zinc-900/40 p-2.5">
        <Input
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          placeholder="Ask the orchestrator..."
          className="h-8 text-xs bg-zinc-950 border-zinc-800"
          disabled={loading}
        />
        <Button
          size="sm"
          onClick={() => handleSendMessage()}
          disabled={loading || !inputMessage.trim()}
          className="h-8 w-8 p-0 bg-blue-600 hover:bg-blue-500"
        >
          <Send className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
