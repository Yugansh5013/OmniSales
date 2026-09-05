"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UserPlus,
  TrendingUp,
  CheckSquare,
  ShieldCheck,
  Activity,
  Compass,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
  Zap,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchTasks } from "@/lib/api";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  priority?: boolean;
}

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [currentUser, setCurrentUser] = useState<{ name: string; email: string }>({
    name: "Admin User",
    email: "admin@omnisales.ai",
  });

  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("omnisales_user");
      if (savedUser) {
        const u = JSON.parse(savedUser);
        if (u && (u.name || u.email)) {
          setCurrentUser({
            name: u.name || "Admin User",
            email: u.email || "admin@omnisales.ai",
          });
        }
      }
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    async function loadBadge() {
      try {
        const tasks = await fetchTasks("pending_approval");
        setPendingCount(tasks.length);
      } catch {
        // silent fallback
      }
    }
    loadBadge();
    const interval = setInterval(loadBadge, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems: NavItem[] = [
    { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { label: "Prospecting", href: "/dashboard/prospecting", icon: UserPlus },
    { label: "Pipeline", href: "/dashboard/pipeline", icon: TrendingUp },
    {
      label: "Approvals",
      href: "/dashboard/approvals",
      icon: CheckSquare,
      badge: pendingCount,
      priority: true,
    },
    { label: "Retention", href: "/dashboard/churn", icon: ShieldCheck },
    { label: "Evals & Reliability", href: "/dashboard/evals", icon: Activity },
    { label: "Competitive Intel", href: "/dashboard/intelligence", icon: Compass },
    { label: "Audit Trail", href: "/dashboard/audit", icon: FileText },
    { label: "Settings", href: "/dashboard/settings", icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-300 select-none z-30 shrink-0",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-zinc-800/80">
        <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 shrink-0">
            <Bot className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-white">OmniSales</span>
              <span className="text-[10px] text-zinc-400 uppercase tracking-widest font-mono">Autonomous AI</span>
            </div>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-md p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100 border border-transparent"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-blue-400" : "text-zinc-400 group-hover:text-zinc-200"
                )}
              />
              {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
              {!collapsed && item.badge !== undefined && item.badge > 0 && (
                <span className="rounded-full bg-[rgba(250,178,25,0.15)] border border-[rgba(250,178,25,0.3)] px-2 py-0.5 text-[11px] font-semibold text-[#fab219]">
                  {item.badge}
                </span>
              )}
              {collapsed && item.badge !== undefined && item.badge > 0 && (
                <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-[#fab219] ring-2 ring-zinc-950" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Autonomous Department Status Mini-Widget */}
      {!collapsed && (
        <div className="p-3 mx-2 mb-3 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-[#0ca30c]" />
              Agent Swarm
            </span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#0ca30c] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0ca30c]"></span>
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-[11px] text-zinc-400">
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0ca30c]" />
              <span>Closer</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0ca30c]" />
              <span>Prospector</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0ca30c]" />
              <span>Guardian</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0ca30c]" />
              <span>Spy A2A</span>
            </div>
          </div>
        </div>
      )}

      {/* User Footer */}
      {(() => {
        const initials =
          currentUser.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .slice(0, 2)
            .toUpperCase() || "AD";

        return (
          <div className="border-t border-zinc-800/80 p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800 text-xs font-semibold text-zinc-200 border border-zinc-700 shrink-0">
                {initials}
              </div>
              {!collapsed && (
                <div className="flex flex-col truncate">
                  <span className="text-xs font-medium text-zinc-200">{currentUser.name}</span>
                  <span className="text-[10px] text-zinc-400 font-mono">{currentUser.email}</span>
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </aside>
  );
}
