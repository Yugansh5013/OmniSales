import asyncio
import datetime
import json
import os
import sys
import uuid
import asyncpg
import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
HUBSPOT_BASE = "https://api.hubapi.com/crm/v3"
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json",
}

async def setup_hubspot():
    print("🔄 1. Seeding HubSpot CRM ground truth...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Patch Companies with real ARR
        companies_to_patch = [
            ("344303594191", {"name": "TechFlow Inc", "domain": "techflow.io", "annualrevenue": "84000"}),
            ("344301791932", {"name": "NexGen Robotics", "domain": "nexgenrobotics.com", "annualrevenue": "150000"}),
            ("344401650413", {"name": "QuantumLeap AI", "domain": "quantumleap.ai", "annualrevenue": "200000"}),
            ("344282091234", {"name": "AlphaWave Digital", "domain": "alphawave.io", "annualrevenue": "96000"}),
            ("344191019734", {"name": "Cloudscale", "domain": "cloudscale.ai", "annualrevenue": "110000"}),
        ]
        for cid, props in companies_to_patch:
            r = await client.patch(f"{HUBSPOT_BASE}/objects/companies/{cid}", headers=HEADERS, json={"properties": props})
            print(f"  Company {cid} -> {props.get('name')} (ARR: ${props.get('annualrevenue')}): {r.status_code}")

        # 2. Patch Contacts
        contacts_to_patch = [
            ("546896772831", {"firstname": "Alex", "lastname": "Rivera", "email": "alex@techflow.io", "jobtitle": "VP of Engineering", "company": "TechFlow Inc"}),
            ("546789342932", {"firstname": "Elena", "lastname": "Rostova", "email": "elena@nexgenrobotics.com", "jobtitle": "VP of Procurement", "company": "NexGen Robotics"}),
            ("546759531217", {"firstname": "Aris", "lastname": "Thorne", "email": "dr.thorne@quantumleap.ai", "jobtitle": "Chief AI Officer", "company": "QuantumLeap AI"}),
            ("546824671946", {"firstname": "Marcus", "lastname": "Vance", "email": "marcus@alphawave.io", "jobtitle": "VP of Sales Operations", "company": "AlphaWave Digital"}),
            ("546622989012", {"firstname": "Sarah", "lastname": "Chen", "email": "sarah.chen@novatech.io", "jobtitle": "VP of Growth", "company": "NovaTech Solutions", "hs_lead_status": "NEW"}),
        ]
        for cid, props in contacts_to_patch:
            r = await client.patch(f"{HUBSPOT_BASE}/objects/contacts/{cid}", headers=HEADERS, json={"properties": props})
            print(f"  Contact {cid} -> {props.get('firstname')} {props.get('lastname')}: {r.status_code}")

        # 3. Patch Deals with initial showcase stages
        deals_to_patch = [
            ("345991809743", {"dealname": "TechFlow Inc Growth License", "dealstage": "presentationscheduled", "amount": "84000"}),
            ("345913758422", {"dealname": "NexGen Robotics Enterprise", "dealstage": "decisionmakerboughtin", "amount": "150000"}),
            ("345888257734", {"dealname": "QuantumLeap AI Enterprise License", "dealstage": "presentationscheduled", "amount": "200000"}),
            ("346038367974", {"dealname": "AlphaWave Digital Expansion", "dealstage": "closedwon", "amount": "96000"}),
        ]
        for did, props in deals_to_patch:
            r = await client.patch(f"{HUBSPOT_BASE}/objects/deals/{did}", headers=HEADERS, json={"properties": props})
            print(f"  Deal {did} -> {props.get('dealname')} (Stage: {props.get('dealstage')}, Amount: ${props.get('amount')}): {r.status_code}")

        # 4. Associate Deals & Contacts
        associations = [
            ("345991809743", "546896772831"),  # TechFlow -> Alex Rivera
            ("345913758422", "546789342932"),  # NexGen -> Elena Rostova
            ("345888257734", "546759531217"),  # QuantumLeap -> Aris Thorne
            ("346038367974", "546824671946"),  # AlphaWave -> Marcus Vance
        ]
        for did, cid in associations:
            r = await client.put(f"https://api.hubapi.com/crm/v4/objects/deals/{did}/associations/default/contacts/{cid}", headers=HEADERS)
            print(f"  Assoc Deal {did} <-> Contact {cid}: {r.status_code}")


async def setup_database():
    print("\n🧹 2. Cleaning and aligning Postgres database to HubSpot CRM...")
    db_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(dsn=db_url, ssl="require")

    # A. Clear all pending approval tasks and old scan reports
    await pool.execute("DELETE FROM agent_tasks")
    print("  Cleared agent_tasks table (0 pending tasks).")
    await pool.execute("DELETE FROM scan_reports")
    print("  Cleared scan_reports table.")

    # B. Clear accounts and re-seed ONLY the 5 verified HubSpot customer accounts
    await pool.execute("DELETE FROM accounts")
    print("  Cleared old accounts table.")

    hubspot_accounts = [
        {
            "id": "30000000-0000-0000-0000-000000000001",
            "company": "TechFlow Inc",
            "arr": 84000,
            "plan": "professional",
            "health_score": 0.31,
            "churn_risk": 0.84,
            "usage_pct": 0.12,
            "support_tickets": 4,
            "hubspot_id": "344303594191",
            "metadata": {
                "signals": ["No login in 21 days", "Plan utilization dropped to 12%", "Active competitor demo with AcmeCRM", "CFO requested contract termination terms"],
                "nps_score": 3,
                "contract_end": "2026-10-15"
            }
        },
        {
            "id": "30000000-0000-0000-0000-000000000002",
            "company": "NexGen Robotics",
            "arr": 150000,
            "plan": "enterprise",
            "health_score": 0.35,
            "churn_risk": 0.79,
            "usage_pct": 0.28,
            "support_tickets": 3,
            "hubspot_id": "344301791932",
            "metadata": {
                "signals": ["Usage dropped 35% in 30 days", "3 unresolved P1 support tickets", "Evaluating competitor AcmeCRM"],
                "nps_score": 5,
                "contract_end": "2026-08-15"
            }
        },
        {
            "id": "30000000-0000-0000-0000-000000000003",
            "company": "Cloudscale",
            "arr": 110000,
            "plan": "enterprise",
            "health_score": 0.85,
            "churn_risk": 0.15,
            "usage_pct": 0.65,
            "support_tickets": 0,
            "hubspot_id": "344191019734",
            "metadata": {
                "signals": ["Consistent daily active users", "High API volume"],
                "nps_score": 9
            }
        },
        {
            "id": "30000000-0000-0000-0000-000000000004",
            "company": "AlphaWave Digital",
            "arr": 96000,
            "plan": "enterprise",
            "health_score": 0.88,
            "churn_risk": 0.10,
            "usage_pct": 0.82,
            "support_tickets": 0,
            "hubspot_id": "344282091234",
            "metadata": {
                "signals": ["Expansion contract signed", "High executive engagement"],
                "nps_score": 10
            }
        },
        {
            "id": "30000000-0000-0000-0000-000000000005",
            "company": "QuantumLeap AI",
            "arr": 200000,
            "plan": "enterprise",
            "health_score": 0.92,
            "churn_risk": 0.05,
            "usage_pct": 0.90,
            "support_tickets": 0,
            "hubspot_id": "344401650413",
            "metadata": {
                "signals": ["Executive sponsor highly engaged", "Expansion evaluation in progress"],
                "nps_score": 9
            }
        }
    ]

    for acct in hubspot_accounts:
        await pool.execute(
            """INSERT INTO accounts (id, org_id, company, arr, plan, health_score, churn_risk, usage_pct, support_tickets, metadata, hubspot_id, created_at, updated_at)
            VALUES ($1, 'a0000000-0000-0000-0000-000000000001', $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())""",
            uuid.UUID(acct["id"]),
            acct["company"],
            acct["arr"],
            acct["plan"],
            acct["health_score"],
            acct["churn_risk"],
            acct["usage_pct"],
            acct["support_tickets"],
            json.dumps(acct["metadata"]),
            acct["hubspot_id"]
        )
    print(f"  Seeded {len(hubspot_accounts)} HubSpot-synced customer accounts (TechFlow, NexGen, Cloudscale, AlphaWave, QuantumLeap).")

    # C. Seed Deals with Closer showcase email threads & at_risk trigger
    techflow_thread = [
        {
            "from": "rep",
            "to": "alex@techflow.io",
            "subject": "Aligning on Terms for a Successful Pilot [ref:00000003]",
            "body": "Hi Alex,\n\nI understand the need to meet your procurement guidelines, especially around the 55% discount request and quarterly payments for the trial. Based on our experience with similar enterprise pilots, a 35% discount with a 30-day payment term for the 3-month trial delivers a proven 4-to-1 ROI while maintaining dedicated SLA support.\n\nCan we schedule a 30-minute call tomorrow to finalize terms?\n\nBest regards,\nSarah Jenkins\nAccount Executive, OmniSales",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)).isoformat(),
        },
        {
            "from": "prospect",
            "to": "sarah.jenkins@omnisales.io",
            "subject": "Re: Aligning on Terms for a Successful Pilot [ref:00000003]",
            "body": "Hi Sarah,\n\nYes, let's have a meeting tomorrow to finalize the SLA terms and kickoff timeline.",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=30)).isoformat(),
        }
    ]
    await pool.execute(
        """UPDATE deals SET
            company = 'TechFlow Inc',
            stage = 'proposal',
            arr = 84000,
            risk_level = 'at_risk',
            closer_thread = $1,
            last_activity = NOW(),
            hubspot_id = '345991809743'
        WHERE hubspot_id = '345991809743' OR company ILIKE '%TechFlow%'""",
        json.dumps(techflow_thread),
    )
    print("  Updated TechFlow Inc deal (Meeting Request Showcase, risk: at_risk).")

    nexgen_thread = [
        {
            "from": "rep",
            "to": "elena@nexgenrobotics.com",
            "subject": "OmniSales Enterprise Proposal for NexGen Robotics [ref:00000001]",
            "body": "Hi Elena,\n\nFollowing our technical architecture review, attached is our proposal for the OmniSales Enterprise deployment.\n\nBest regards,\nSarah Jenkins\nAccount Executive, OmniSales",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)).isoformat(),
        },
        {
            "from": "prospect",
            "to": "sarah.jenkins@omnisales.io",
            "subject": "Re: OmniSales Enterprise Proposal for NexGen Robotics [ref:00000001]",
            "body": "Hi Sarah,\n\nWe are currently evaluating your proposal against AcmeCRM. AcmeCRM is offering us 40% lower licensing costs and promises standard CRM workflows. Why should our engineering leadership choose OmniSales over AcmeCRM?",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat(),
        }
    ]
    await pool.execute(
        """UPDATE deals SET
            company = 'NexGen Robotics',
            stage = 'negotiation',
            arr = 150000,
            risk_level = 'at_risk',
            closer_thread = $1,
            last_activity = NOW(),
            hubspot_id = '345913758422'
        WHERE hubspot_id = '345913758422' OR company ILIKE '%NexGen%'""",
        json.dumps(nexgen_thread),
    )
    print("  Updated NexGen Robotics deal (Competitor Objection Showcase, risk: at_risk).")

    quantum_thread = [
        {
            "from": "rep",
            "to": "dr.thorne@quantumleap.ai",
            "subject": "OmniSales Enterprise Agreement & SLA Terms [ref:00000002]",
            "body": "Hi Aris,\n\nFollowing our executive alignment and review of the enterprise SLA terms, I am pleased to share the finalized terms for the QuantumLeap deployment ($200,000 ARR). Please let me know once your team is ready to complete the transaction.\n\nBest regards,\nSarah Jenkins\nAccount Executive, OmniSales",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
        },
        {
            "from": "prospect",
            "to": "sarah.jenkins@omnisales.io",
            "subject": "Re: OmniSales Enterprise Agreement & SLA Terms [ref:00000002]",
            "body": "Hi Sarah,\n\nOur executive team has approved the contract terms. We are ready to move forward. Please send over the payment link so we can complete the transaction and kick off onboarding today.",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=45)).isoformat(),
        }
    ]
    await pool.execute(
        """UPDATE deals SET
            company = 'QuantumLeap AI',
            stage = 'proposal',
            arr = 200000,
            risk_level = 'at_risk',
            closer_thread = $1,
            last_activity = NOW(),
            hubspot_id = '345888257734'
        WHERE hubspot_id = '345888257734' OR company ILIKE '%Quantum%'""",
        json.dumps(quantum_thread),
    )
    print("  Updated QuantumLeap AI deal (Live Payment Link Showcase, risk: at_risk).")

    alphawave_thread = [
        {
            "from": "prospect",
            "to": "sarah.jenkins@omnisales.io",
            "subject": "Executed Agreement [ref:00000004]",
            "body": "Hi Sarah, contract signed and payment confirmed via Stripe link. Excited to partner with OmniSales!",
            "timestamp": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)).isoformat(),
        }
    ]
    await pool.execute(
        """UPDATE deals SET
            company = 'AlphaWave Digital',
            stage = 'closed_won',
            arr = 96000,
            risk_level = 'healthy',
            closer_thread = $1,
            last_activity = NOW(),
            hubspot_id = '346038367974'
        WHERE hubspot_id = '346038367974' OR company ILIKE '%AlphaWave%'""",
        json.dumps(alphawave_thread),
    )
    print("  Updated AlphaWave Digital deal (Closed Won Benchmark).")

    # D. Clean Leads: keep only NovaTech Solutions as uncontacted new lead
    await pool.execute("DELETE FROM leads")
    enrichment_data = {
        "industry": "B2B SaaS / FinTech",
        "employees": 250,
        "funding": "Series B ($28M)",
        "revenue_est": "$20M-$50M",
        "tech_stack": ["PostgreSQL", "AWS", "React", "Python", "Kubernetes"],
        "signals": ["Raised $28M Series B", "Hiring 15+ Enterprise Sales Reps", "Evaluating modern AI sales tech stack"],
        "contacts": [
            {"name": "Sarah Chen", "title": "VP of Growth", "email": "sarah.chen@novatech.io"}
        ],
    }
    await pool.execute(
        """INSERT INTO leads (id, org_id, company, contact_name, email, title, icp_score, tier, status, source, enrichment, owner, hubspot_id)
        VALUES ('10000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'NovaTech Solutions', 'Sarah Chen', 'sarah.chen@novatech.io', 'VP of Growth', NULL, 'Unscored', 'new', 'inbound', $1, 'Sarah Jenkins', '546622989012')""",
        json.dumps(enrichment_data),
    )
    print("  Cleaned Leads: NovaTech Solutions is the single uncontacted new lead candidate.")

    await pool.close()

if __name__ == "__main__":
    asyncio.run(setup_hubspot())
    asyncio.run(setup_database())
    print("\n✅ HubSpot CRM and Postgres operational state aligned perfectly for the demo scan!")
