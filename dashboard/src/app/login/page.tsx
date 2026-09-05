"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, ArrowRight, Lock, Mail, AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@omnisales.ai");
  const [password, setPassword] = useState("hackathon2026");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await login(email, password);
      localStorage.setItem("omnisales_token", res.token);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError((err as Error).message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-4 font-sans text-zinc-100">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 shadow-2xl backdrop-blur-xl">
        {/* Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
            <Bot className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">OmniSales AI</h2>
          <p className="text-xs text-zinc-400">Autonomous Sales Department & Governance Platform</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          {error && (
            <div className="rounded-lg border border-[rgba(208,59,59,0.3)] bg-[rgba(208,59,59,0.1)] p-3 text-[#d03b3b] flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-zinc-300 font-medium">Work Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-zinc-300 font-medium">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs h-10 gap-2 shadow-lg shadow-blue-600/20 mt-2"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <span>Sign in to Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>

          <div className="rounded-lg bg-zinc-950/80 p-3 border border-zinc-800 text-[11px] text-zinc-400 font-mono text-center">
            Demo Credentials: <strong className="text-zinc-200">admin@omnisales.ai</strong> / <strong className="text-zinc-200">hackathon2026</strong>
          </div>
        </form>
      </div>
    </div>
  );
}
