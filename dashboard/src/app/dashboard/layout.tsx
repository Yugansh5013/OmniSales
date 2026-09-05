"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { CommandPalette } from "@/components/CommandPalette";
import { ChatWidget } from "@/components/ChatWidget";
import { SwarmMissionControlDrawer } from "@/components/SwarmMissionControlDrawer";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [missionControlOpen, setMissionControlOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#09090b] text-zinc-100 font-sans">
      {/* Collapsible Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenMissionControl={() => setMissionControlOpen(true)}
        />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#09090b]/90">
          {children}
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />

      {/* Slide-out Swarm Mission Control Drawer */}
      <SwarmMissionControlDrawer
        isOpen={missionControlOpen}
        onClose={() => setMissionControlOpen(false)}
      />

      {/* Floating Orchestrator Chat Widget */}
      <ChatWidget />
    </div>
  );
}
