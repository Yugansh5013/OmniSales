"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  ShieldCheck,
  Database,
  Key,
  Radio,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Mail,
  Save,
  Cpu,
  Server,
  Zap,
  Clock,
  ArrowRightLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchSystemProbes,
  fetchNotificationEmail,
  updateNotificationEmail,
  fetchCrmSyncSettings,
  updateCrmSyncSettings,
  triggerCrmSync,
  SystemProbesResponse,
  CrmSyncSettings,
} from "@/lib/api";
import { PageLoader } from "@/components/ui/page-loader";

export default function SettingsPage() {
  const [probes, setProbes] = useState<SystemProbesResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);

  const [notificationEmail, setNotificationEmail] = useState("team@omnisales.ai");
  const [savingEmail, setSavingEmail] = useState(false);
  const [emailStatusMessage, setEmailStatusMessage] = useState<string | null>(null);

  // CRM Sync State
  const [crmSettings, setCrmSettings] = useState<CrmSyncSettings | null>(null);
  const [savingCrm, setSavingCrm] = useState(false);
  const [syncingCrm, setSyncingCrm] = useState(false);
  const [crmStatusMessage, setCrmStatusMessage] = useState<string | null>(null);

  const loadProbes = async () => {
    setTesting(true);
    try {
      const data = await fetchSystemProbes();
      setProbes(data);
    } catch {
      // fallback
    } finally {
      setTesting(false);
    }
  };

  const loadEmailSettings = async () => {
    try {
      const data = await fetchNotificationEmail();
      if (data?.email) setNotificationEmail(data.email);
    } catch {
      // fallback
    }
  };

  const loadCrmSettings = async () => {
    try {
      const data = await fetchCrmSyncSettings();
      setCrmSettings(data);
    } catch {
      // fallback
    }
  };

  useEffect(() => {
    Promise.all([loadProbes(), loadEmailSettings(), loadCrmSettings()]).finally(() =>
      setLoading(false)
    );
  }, []);

  const handleSaveEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingEmail(true);
    setEmailStatusMessage(null);
    try {
      await updateNotificationEmail(notificationEmail);
      setEmailStatusMessage("Notification email updated and persisted to Redis.");
      setTimeout(() => setEmailStatusMessage(null), 3500);
    } catch {
      setEmailStatusMessage("Failed to update notification email.");
    } finally {
      setSavingEmail(false);
    }
  };

  const handleToggleAutoSync = async (enabled: boolean) => {
    if (!crmSettings) return;
    setSavingCrm(true);
    try {
      await updateCrmSyncSettings({
        auto_sync: enabled,
        interval_seconds: crmSettings.interval_seconds,
      });
      setCrmSettings((prev) => (prev ? { ...prev, auto_sync: enabled } : prev));
      setCrmStatusMessage(`Automated CRM sync ${enabled ? "enabled" : "disabled"}.`);
      setTimeout(() => setCrmStatusMessage(null), 3500);
    } catch {
      setCrmStatusMessage("Failed to update auto sync setting.");
    } finally {
      setSavingCrm(false);
    }
  };

  const handleChangeInterval = async (interval: number) => {
    if (!crmSettings) return;
    setSavingCrm(true);
    try {
      await updateCrmSyncSettings({
        auto_sync: crmSettings.auto_sync,
        interval_seconds: interval,
      });
      setCrmSettings((prev) => (prev ? { ...prev, interval_seconds: interval } : prev));
      setCrmStatusMessage(
        `CRM sync frequency updated to every ${interval < 60 ? interval + "s" : interval / 60 + " min"}.`
      );
      setTimeout(() => setCrmStatusMessage(null), 3500);
    } catch {
      setCrmStatusMessage("Failed to update interval.");
    } finally {
      setSavingCrm(false);
    }
  };

  const handleManualSync = async () => {
    setSyncingCrm(true);
    setCrmStatusMessage(null);
    try {
      const res = await triggerCrmSync();
      setCrmStatusMessage(
        `✓ Inbound sync complete: Pulled ${res.synced_leads} leads & ${res.synced_deals} deals from HubSpot.`
      );
      await loadCrmSettings();
      setTimeout(() => setCrmStatusMessage(null), 4500);
    } catch {
      setCrmStatusMessage("Manual CRM sync failed.");
    } finally {
      setSyncingCrm(false);
    }
  };

  const services = probes?.services || {};
  const serviceKeys = Object.keys(services);

  if (loading) return <PageLoader label="Loading system diagnostics..." />;

  return (
    <div className="space-y-6 animate-in fade-in duration-300 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-zinc-800 pb-5">
        <h2 className="text-xl font-bold tracking-tight text-white">System Settings & Connection Diagnostics</h2>
        <p className="text-xs text-zinc-400">
          Live service health probes, autonomous email routing, CRM ingestion, and LLM model pool diagnostics
        </p>
      </div>

      <div className="space-y-6 text-xs">
        {/* Live Infrastructure Probes Grid */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] text-[#0ca30c]">
                <Server className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Live Infrastructure Probes & Microservices</h3>
                <p className="text-[11px] text-zinc-400">
                  Real-time network probes across FastMCP servers, Neon PostgreSQL, and Redis
                </p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={loadProbes}
              disabled={testing}
              className="text-xs h-8 gap-1.5 border-blue-500/30 text-blue-400 hover:bg-blue-500/10 hover:text-blue-300"
            >
              {testing ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Radio className="h-3.5 w-3.5" />}
              <span>{testing ? "Probing..." : "Test Probes Now"}</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-[11px]">
            {serviceKeys.length > 0 ? (
              serviceKeys.map((key) => {
                const svc = services[key];
                const isHealthy = svc.status === "healthy";
                return (
                  <div
                    key={key}
                    className="bg-zinc-950/80 p-3.5 rounded-lg border border-zinc-800 space-y-2 flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-sans font-semibold text-zinc-200 text-xs">{svc.name}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isHealthy
                            ? "text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)]"
                            : "text-[#d03b3b] bg-[rgba(208,59,59,0.12)] border border-[rgba(208,59,59,0.25)]"
                        }`}
                      >
                        {svc.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-zinc-500 text-[10px] pt-2 border-t border-zinc-800/60">
                      <span>{svc.port ? `Port ${svc.port}` : svc.detail}</span>
                      <span className="text-zinc-400">{svc.latency_ms ? `${svc.latency_ms}ms` : "Active"}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-full p-6 text-center text-zinc-500 font-mono text-xs">
                {testing
                  ? "Probing microservice ports..."
                  : "No live service telemetry returned. Click 'Test Probes Now' to refresh."}
              </div>
            )}
          </div>
        </div>

        {/* HubSpot CRM Ingestion & Automated Synchronization */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400">
                <ArrowRightLeft className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">
                  HubSpot CRM Ingestion & Automated Synchronization
                </h3>
                <p className="text-[11px] text-zinc-400">
                  Bi-directional real-time sync between HubSpot CRM v3 and PostgreSQL System of Intelligence
                </p>
              </div>
            </div>
            {crmSettings?.connected ? (
              <span className="text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2.5 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                HubSpot Live (Portal #{crmSettings.portal_id})
              </span>
            ) : (
              <span className="text-zinc-500 bg-zinc-800 px-2.5 py-0.5 rounded-full text-[11px] font-medium">
                Simulation Mode
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Auto-Sync Toggle Control */}
            <div className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-3 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-200">Automated Background CRM Ingestion</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      crmSettings?.auto_sync
                        ? "text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)]"
                        : "text-zinc-400 bg-zinc-800 border border-zinc-700"
                    }`}
                  >
                    {crmSettings?.auto_sync ? "Active" : "Paused"}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-1">
                  Automatically pulls new leads and updated deal stages from HubSpot into PostgreSQL in the background.
                </p>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  size="sm"
                  variant={crmSettings?.auto_sync ? "default" : "outline"}
                  onClick={() => handleToggleAutoSync(!crmSettings?.auto_sync)}
                  disabled={savingCrm}
                  className={`text-xs h-8 ${
                    crmSettings?.auto_sync
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  }`}
                >
                  {crmSettings?.auto_sync ? "Pause Automated Sync" : "Enable Automated Sync"}
                </Button>
              </div>
            </div>

            {/* Sync Frequency Selector */}
            <div className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-3 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-200">Poll Frequency</span>
                  <span className="text-orange-400 font-mono text-[10px]">
                    {crmSettings?.interval_seconds === 60
                      ? "1 minute"
                      : crmSettings?.interval_seconds === 300
                      ? "5 minutes"
                      : crmSettings?.interval_seconds === 900
                      ? "15 minutes"
                      : "1 hour"}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400 mt-1">
                  Set how frequently the background worker scans HubSpot for new contacts and deals.
                </p>
              </div>

              <div className="flex items-center gap-1.5 flex-wrap pt-2">
                {[
                  { label: "1 min (Demo)", val: 60 },
                  { label: "5 min", val: 300 },
                  { label: "15 min", val: 900 },
                  { label: "1 hour", val: 3600 },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    type="button"
                    onClick={() => handleChangeInterval(opt.val)}
                    disabled={savingCrm}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all ${
                      crmSettings?.interval_seconds === opt.val
                        ? "bg-orange-500/20 text-orange-300 border border-orange-500/40 font-bold"
                        : "bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Manual Inbound Trigger Bar */}
          <div className="flex items-center justify-between pt-2 border-t border-zinc-800/80">
            <div className="flex items-center gap-2 text-zinc-400 text-[11px]">
              <Clock className="h-3.5 w-3.5" />
              <span>
                {crmSettings?.last_sync
                  ? `Last synced: ${new Date(crmSettings.last_sync).toLocaleTimeString()}`
                  : "Never synced yet"}
              </span>
            </div>

            <Button
              size="sm"
              variant="outline"
              onClick={handleManualSync}
              disabled={syncingCrm}
              className="gap-2 border-orange-500/40 bg-orange-950/20 text-orange-300 hover:bg-orange-600 hover:text-white text-xs h-8"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${syncingCrm ? "animate-spin" : ""}`} />
              <span>{syncingCrm ? "Syncing from HubSpot..." : "Sync Now from HubSpot"}</span>
            </Button>
          </div>

          {crmStatusMessage && (
            <div className="p-2.5 rounded-lg bg-[rgba(12,163,12,0.1)] border border-[rgba(12,163,12,0.3)] text-[#0ca30c] text-xs flex items-center gap-2">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              <span>{crmStatusMessage}</span>
            </div>
          )}
        </div>

        {/* Demo Notification Email Routing Settings */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Mail className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Demo Notification Email Routing</h3>
                <p className="text-[11px] text-zinc-400">
                  Redirect all approved autonomous outreach and Razorpay payment links to controlled inboxes
                </p>
              </div>
            </div>
            <span className="text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2.5 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Safe Demo Isolation
            </span>
          </div>

          <form onSubmit={handleSaveEmail} className="space-y-3 max-w-xl">
            <div className="space-y-1.5">
              <label className="text-zinc-300 font-medium">Demo Notification Email Address</label>
              <div className="flex gap-2">
                <Input
                  type="email"
                  required
                  value={notificationEmail}
                  onChange={(e) => setNotificationEmail(e.target.value)}
                  placeholder="e.g. your-team@domain.com"
                  className="text-xs bg-zinc-950 border-zinc-800 focus:ring-blue-500 text-white"
                />
                <Button
                  type="submit"
                  disabled={savingEmail}
                  className="gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs px-4 shrink-0"
                >
                  {savingEmail ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  <span>Save Email</span>
                </Button>
              </div>
            </div>

            {emailStatusMessage && (
              <div className="p-2.5 rounded-lg bg-[rgba(12,163,12,0.1)] border border-[rgba(12,163,12,0.3)] text-[#0ca30c] text-xs flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                <span>{emailStatusMessage}</span>
              </div>
            )}

            <p className="text-[11px] text-zinc-500 leading-relaxed font-sans">
              To prevent accidental cold sends to synthetic demo domains during live evaluation, Resend email dispatches are intercepted and safely routed to this controlled destination inbox.
            </p>
          </form>
        </div>

        {/* Groq Key Rotation Pool Status */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <Key className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Groq LLM Model & Key Rotation Pool</h3>
                <p className="text-[11px] text-zinc-400">
                  Multi-key rotation engine with automatic 429 backoff and model tiering
                </p>
              </div>
            </div>
            <span className="text-[#0ca30c] bg-[rgba(12,163,12,0.12)] border border-[rgba(12,163,12,0.25)] px-2.5 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {probes?.groq_keys_count || 3} API Keys Pooled
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-zinc-200">Complex Reasoning Model</span>
                <span className="text-blue-400 font-mono text-[10px]">Tier 1</span>
              </div>
              <p className="font-mono text-white text-sm font-bold">openai/gpt-oss-120b</p>
              <p className="text-[11px] text-zinc-400">
                Used by Closer for objection analysis and Guardian for multi-account churn synthesis.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-zinc-200">Fast Extraction & Fallback Model</span>
                <span className="text-purple-400 font-mono text-[10px]">Tier 2</span>
              </div>
              <p className="font-mono text-white text-sm font-bold">openai/gpt-oss-20b</p>
              <p className="text-[11px] text-zinc-400">
                Used for instant ICP classification, structured JSON parsing, and rapid token extraction.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
