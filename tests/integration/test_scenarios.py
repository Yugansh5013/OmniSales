"""Scenario Integration Test for OmniSales Agents."""
import os
import time
import requests
import json

BASE_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000") + "/api"

def main():
    print("--- 🚀 OmniSales Scenario Integration Runner ---")
    
    # 1. Authenticate
    print("\n[1] Authenticating...")
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@omnisales.ai", "password": "hackathon2026"})
    if res.status_code != 200:
        print("Auth failed:", res.text)
        return
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Authenticated")

    # Fetch IDs for testing
    print("\n[2] Fetching initial data...")
    deals = requests.get(f"{BASE_URL}/deals", headers=headers).json()
    leads = requests.get(f"{BASE_URL}/leads", headers=headers).json()
    
    if not deals or not leads:
        print("No deals or leads found in DB.")
        return

    deal_id = deals[0]["id"]
    lead_id = leads[0]["id"]
    print(f"Using Deal ID: {deal_id}")
    print(f"Using Lead ID: {lead_id}")

    # SCENARIO 1: CLOSER AGENT
    print("\n▶️ [Scenario 1] Triggering Closer Agent (Deal Re-Engagement)...")
    try:
        r = requests.post(f"{BASE_URL}/deals/{deal_id}/trigger", headers=headers, timeout=30)
        print(f"Result: {r.status_code} - {r.json()}")
    except Exception as e:
        print("Closer failed:", e)

    # SCENARIO 2: PROSPECTOR AGENT
    print("\n▶️ [Scenario 2] Triggering Prospector Agent (Lead Sequence Gen)...")
    try:
        r = requests.post(f"{BASE_URL}/leads/{lead_id}/trigger", headers=headers, timeout=30)
        print(f"Result: {r.status_code} - {r.json()}")
    except Exception as e:
        print("Prospector failed:", e)

    # SCENARIO 3: GUARDIAN AGENT
    print("\n▶️ [Scenario 3] Triggering Guardian Agent (Churn Analysis)...")
    try:
        r = requests.post(f"{BASE_URL}/accounts/analyze", headers=headers, timeout=45)
        print(f"Result: {r.status_code} - {r.json()}")
    except Exception as e:
        print("Guardian failed:", e)

    # CHECK APPROVAL MESSAGES
    print("\n⏳ Waiting 5 seconds for LangGraph graph execution to reach Human-in-the-Loop interrupts...")
    time.sleep(5)
    
    print("\n📥 Fetching Pending Agent Approval Tasks (HITL):")
    tasks = requests.get(f"{BASE_URL}/tasks?status=pending_approval", headers=headers).json()
    print(json.dumps(tasks, indent=2))
    
    print("\n✅ All scenarios executed from backend!")

if __name__ == "__main__":
    main()
