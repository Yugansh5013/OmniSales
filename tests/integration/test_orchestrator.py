"""Test the Orchestrator Agent integration — trigger a manual scan and print results."""
import requests
import json
import sys
import os

BASE = os.environ.get("GATEWAY_URL", "http://localhost:8000") + "/api"

def main():
    print("\n" + "="*60)
    print("  🤖 OmniSales — Orchestrator Agent Test")
    print("="*60)

    # Authenticate
    print("\n[0] Authenticating...")
    r = requests.post(f"{BASE}/auth/login", json={"email":"admin@omnisales.ai","password":"hackathon2026"})
    if r.status_code != 200:
        print(f"❌ Auth failed: {r.text}")
        sys.exit(1)
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    print("✅ JWT obtained")

    # Trigger manual scan
    print("\n[1] Triggering Orchestrator scan...")
    print("    (This will scan all deals, leads, accounts and dispatch to agents)")
    print("    ⏳ Running swarm sweep...")

    try:
        r = requests.post(f"{BASE}/orchestrator/scan", headers=h, timeout=300)
        print(f"\n    HTTP {r.status_code}")
        result = r.json()
    except requests.exceptions.ReadTimeout:
        print("    ⏱️ Scan timed out (agents may still be processing)")
        sys.exit(1)
    except Exception as e:
        print(f"    ❌ Error: {e}")
        sys.exit(1)

    # Pretty print results
    print("\n" + "="*60)
    print("  📊 Orchestrator Scan Results")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))

    # Summary
    print("\n" + "─"*60)
    print("  📋 Dispatch Summary")
    print("─"*60)

    deals = result.get("deals", {})
    leads = result.get("leads", {})
    accounts = result.get("accounts", {})

    print(f"\n  🔴 Deals  → {deals.get('dispatched', 0)} dispatched to Closer")
    for action in deals.get("actions", []):
        status = action.get("result_status", action.get("error", "?"))
        print(f"     • {action.get('company', '?')} — trigger: {action.get('trigger', '?')} → {status}")

    print(f"\n  🟢 Leads  → {leads.get('dispatched', 0)} dispatched to Prospector")
    for action in leads.get("actions", []):
        icp = action.get("result_icp", "?")
        print(f"     • {action.get('company', '?')} — ICP={icp} → {action.get('result_status', action.get('error', '?'))}")

    print(f"\n  🟡 Accounts → {accounts.get('dispatched', 0)} dispatched to Guardian")
    for action in accounts.get("actions", []):
        print(f"     • {action.get('trigger', '?')} → flagged={action.get('result_flagged', '?')}")

    total = result.get("total_dispatched", 0)
    print(f"\n  ✅ Total dispatches: {total}")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
