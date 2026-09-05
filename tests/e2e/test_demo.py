"""
OmniSales — 3 Demo Scenario Runner
Runs each scenario sequentially with generous timeouts and full output.
"""
import requests
import json
import time
import sys
import os

BASE = os.environ.get("GATEWAY_URL", "http://localhost:8000") + "/api"
TIMEOUT = 120  # seconds per agent call

def pp(label, obj):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(json.dumps(obj, indent=2, default=str))

def main():
    print("\n" + "="*60)
    print("  🚀 OmniSales — Full Demo Scenario Runner")
    print("="*60)

    # ── Step 0: Authenticate ──
    print("\n[0] Authenticating...")
    r = requests.post(f"{BASE}/auth/login", json={"email":"admin@omnisales.ai","password":"hackathon2026"})
    if r.status_code != 200:
        print(f"❌ Auth failed ({r.status_code}): {r.text}")
        sys.exit(1)
    token = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    print("✅ JWT obtained")

    # ── Step 1: Fetch seed data IDs ──
    print("\n[1] Fetching deals, leads, accounts...")
    deals = requests.get(f"{BASE}/deals", headers=h).json()
    leads = requests.get(f"{BASE}/leads", headers=h).json()
    accounts = requests.get(f"{BASE}/accounts", headers=h).json()
    print(f"   Deals: {len(deals)}  |  Leads: {len(leads)}  |  Accounts: {len(accounts)}")

    # Pick the BEST demo data:
    #  Closer  → TechFlow Inc  (stalled, $84K, 14 days silent, pricing objection)
    #  Prospector → NovaTech Solutions (new lead, 125 employees, Series B, hiring AEs)
    stalled_deals = [d for d in deals if d.get("risk_level") in ("stalled", "at_risk")]
    deal_id = stalled_deals[0]["id"] if stalled_deals else deals[0]["id"]
    deal_name = next((d["company"] for d in deals if d["id"] == deal_id), "?")

    new_leads = [l for l in leads if l.get("status") == "new"]
    lead_id = new_leads[0]["id"] if new_leads else leads[0]["id"]
    lead_name = next((l["company"] for l in leads if l["id"] == lead_id), "?")

    print(f"   🎯 Closer deal  = {deal_name} ({deal_id})")
    print(f"   🎯 Prospector lead = {lead_name} ({lead_id})")

    results = {}

    # ══════════════════════════════════════════════════════════
    # SCENARIO 1: CLOSER AGENT — Deal Re-Engagement
    # ══════════════════════════════════════════════════════════
    print("\n" + "─"*60)
    print("▶️  SCENARIO 1: Closer Agent — Deal Re-Engagement")
    print("─"*60)
    try:
        r = requests.post(f"{BASE}/deals/{deal_id}/trigger", headers=h, timeout=TIMEOUT)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"RAW BODY: {r.text[:2000]}")
            results["closer"] = {"error": f"HTTP {r.status_code}", "body": r.text[:500]}
        else:
            results["closer"] = r.json()
            pp("Closer Response", results["closer"])
    except requests.exceptions.ReadTimeout:
        print("⏱️  Closer timed out (this may mean the graph is still running)")
        results["closer"] = {"error": "timeout"}
    except Exception as e:
        print(f"❌ Closer error: {e}")
        results["closer"] = {"error": str(e)}

    # ══════════════════════════════════════════════════════════
    # SCENARIO 2: PROSPECTOR AGENT — Lead Outreach Sequence
    # ══════════════════════════════════════════════════════════
    print("\n" + "─"*60)
    print("▶️  SCENARIO 2: Prospector Agent — Lead Outreach Sequence")
    print("─"*60)
    try:
        r = requests.post(f"{BASE}/leads/{lead_id}/trigger", headers=h, timeout=TIMEOUT)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"RAW BODY: {r.text[:2000]}")
            results["prospector"] = {"error": f"HTTP {r.status_code}", "body": r.text[:500]}
        else:
            results["prospector"] = r.json()
            pp("Prospector Response", results["prospector"])
    except requests.exceptions.ReadTimeout:
        print("⏱️  Prospector timed out")
        results["prospector"] = {"error": "timeout"}
    except Exception as e:
        print(f"❌ Prospector error: {e}")
        results["prospector"] = {"error": str(e)}

    # ══════════════════════════════════════════════════════════
    # SCENARIO 3: GUARDIAN AGENT — Churn Risk Analysis
    # ══════════════════════════════════════════════════════════
    print("\n" + "─"*60)
    print("▶️  SCENARIO 3: Guardian Agent — Churn Risk Analysis")
    print("─"*60)
    try:
        r = requests.post(f"{BASE}/accounts/analyze", headers=h, timeout=TIMEOUT)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"RAW BODY: {r.text[:2000]}")
            results["guardian"] = {"error": f"HTTP {r.status_code}", "body": r.text[:500]}
        else:
            results["guardian"] = r.json()
            pp("Guardian Response", results["guardian"])
    except requests.exceptions.ReadTimeout:
        print("⏱️  Guardian timed out")
        results["guardian"] = {"error": "timeout"}
    except Exception as e:
        print(f"❌ Guardian error: {e}")
        results["guardian"] = {"error": str(e)}

    # ══════════════════════════════════════════════════════════
    # HITL CHECK: Pending Approval Tasks
    # ══════════════════════════════════════════════════════════
    print("\n" + "─"*60)
    print("📋 Checking HITL Approval Queue...")
    print("─"*60)
    time.sleep(3)
    tasks = requests.get(f"{BASE}/tasks?status=pending_approval", headers=h).json()
    pp("Pending Approval Tasks", tasks)

    # Also check all tasks (any status)
    all_tasks = requests.get(f"{BASE}/tasks?status=", headers=h).json()
    pp("ALL Agent Tasks (any status)", all_tasks)

    # ── Summary ──
    print("\n" + "="*60)
    print("  📊 SCENARIO SUMMARY")
    print("="*60)
    for name, res in results.items():
        status = res.get("status", res.get("error", "unknown"))
        action = res.get("action", "N/A")
        has_draft = bool(res.get("draft"))
        reasoning_count = len(res.get("reasoning", []))
        print(f"   {name:12s} | status={status:20s} | action={action:15s} | draft={'✅' if has_draft else '❌':3s} | reasoning_steps={reasoning_count}")

    print("\n✅ Demo scenario run complete!")

if __name__ == "__main__":
    main()
