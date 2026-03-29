"""
OmniSales — Demo Database Reset & Seed Script
================================================
Run this ONCE before recording your hackathon demo.
It clears ALL agent activity and re-seeds the database
with optimized data designed for maximum demo impact.

Usage:
    python scripts/reset_demo.py
"""

import json
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
ORG = 'a0000000-0000-0000-0000-000000000001'


# ──────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────

LEADS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "company": "NovaTech Solutions", "contact_name": "Sarah Chen",
        "email": "sarah.chen@novatech.io", "title": "VP of Sales",
        "enrichment": {
            "founded": 2019, "employees": 125, "funding": "Series B ($18M)",
            "industry": "SaaS", "tech_stack": ["Salesforce", "Outreach", "Gong"],
            "revenue_est": "$12M ARR",
            "signals": ["Hiring 3 AEs", "New CRO appointed Q1", "Just launched enterprise tier"],
            "contacts": [
                {"name": "Sarah Chen", "title": "VP of Sales", "linkedin": "linkedin.com/in/sarachen"},
                {"name": "James Park", "title": "CRO", "linkedin": "linkedin.com/in/jamespark"}
            ]
        }
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "company": "CloudScale AI", "contact_name": "Marcus Johnson",
        "email": "marcus@cloudscale.ai", "title": "Head of Revenue",
        "enrichment": {
            "founded": 2021, "employees": 85, "funding": "Series A ($9M)",
            "industry": "AI/ML Platform", "tech_stack": ["HubSpot", "Apollo"],
            "revenue_est": "$5M ARR",
            "signals": ["170% YoY growth", "Expanding EU market", "Posted VP Sales role"],
            "contacts": [
                {"name": "Marcus Johnson", "title": "Head of Revenue", "linkedin": "linkedin.com/in/marcusj"},
                {"name": "Priya Patel", "title": "VP Sales", "linkedin": "linkedin.com/in/priyap"}
            ]
        }
    },
    {
        "id": "10000000-0000-0000-0000-000000000003",
        "company": "DataVault Security", "contact_name": "Elena Rodriguez",
        "email": "elena@datavault.com", "title": "CRO",
        "enrichment": {
            "founded": 2018, "employees": 210, "funding": "Series C ($45M)",
            "industry": "Cybersecurity", "tech_stack": ["Salesforce", "ZoomInfo"],
            "revenue_est": "$28M ARR",
            "signals": ["IPO prep rumored", "New enterprise tier launched", "Evaluating sales automation"],
            "contacts": [
                {"name": "Elena Rodriguez", "title": "CRO", "linkedin": "linkedin.com/in/elenarodriguez"},
                {"name": "Tom Wright", "title": "VP Enterprise Sales", "linkedin": "linkedin.com/in/tomwright"}
            ]
        }
    },
    {
        "id": "10000000-0000-0000-0000-000000000004",
        "company": "FinFlow Analytics", "contact_name": "David Kim",
        "email": "dkim@finflow.co", "title": "VP Sales",
        "enrichment": {
            "founded": 2020, "employees": 60, "funding": "Seed ($3M)",
            "industry": "FinTech", "tech_stack": ["Pipedrive", "Lemlist"],
            "revenue_est": "$2M ARR",
            "signals": ["Pivoting to enterprise", "Hired first VP Sales"],
            "contacts": [
                {"name": "David Kim", "title": "VP Sales", "linkedin": "linkedin.com/in/davidkim"},
                {"name": "Lisa Tran", "title": "CEO", "linkedin": "linkedin.com/in/lisatran"}
            ]
        }
    },
    {
        "id": "10000000-0000-0000-0000-000000000005",
        "company": "MediConnect Pro", "contact_name": "Rachel Green",
        "email": "rgreen@mediconnect.health", "title": "Director of Growth",
        "enrichment": {
            "founded": 2017, "employees": 320, "funding": "Series D ($72M)",
            "industry": "HealthTech", "tech_stack": ["Salesforce", "Marketo", "6sense"],
            "revenue_est": "$40M ARR",
            "signals": ["Launched APAC office", "200 new enterprise contracts"],
            "contacts": [
                {"name": "Rachel Green", "title": "Director of Growth", "linkedin": "linkedin.com/in/rachelgreen"},
                {"name": "Alex Morales", "title": "SVP Revenue", "linkedin": "linkedin.com/in/alexmorales"}
            ]
        }
    },
]

DEALS = [
    # Discovery (4)
    {"id": "20000000-0000-0000-0000-000000000001", "company": "Zenith Applications", "stage": "discovery", "arr": 18000, "risk": "healthy", "days_ago": 2,
     "thread": [{"from": "rep", "to": "cto@zenith.io", "subject": "Quick intro", "body": "Hi Alex, saw your Series A — congrats! Would love to show how we can help your sales team scale with AI.", "date": "2026-03-20"}]},
    {"id": "20000000-0000-0000-0000-000000000002", "company": "ByteWave Labs", "stage": "discovery", "arr": 24000, "risk": "healthy", "days_ago": 1,
     "thread": [{"from": "rep", "to": "vp@bytewave.dev", "subject": "AI Sales Automation", "body": "Hi Jordan, noticed your team is hiring 5 SDRs — what if AI could do the prospecting work of 3 of them?", "date": "2026-03-22"}]},
    {"id": "20000000-0000-0000-0000-000000000003", "company": "Orbitron Systems", "stage": "discovery", "arr": 36000, "risk": "at_risk", "days_ago": 8,
     "thread": [{"from": "rep", "to": "cro@orbitron.com", "subject": "Revenue Operations", "body": "Hi Maria, your revenue ops role posting caught my eye. Our platform automates the exact workflows that role would handle.", "date": "2026-03-15"}]},
    {"id": "20000000-0000-0000-0000-000000000004", "company": "PrimeLogistics AI", "stage": "discovery", "arr": 12000, "risk": "healthy", "days_ago": 3,
     "thread": [{"from": "rep", "to": "head@primelogistics.ai", "subject": "Streamlining outbound", "body": "Hi Sam, saw your LinkedIn post about scaling outbound — our AI agents draft and manage the entire sequence.", "date": "2026-03-19"}]},
    # Proposal (4) — ★ KEY DEMO TARGETS
    {"id": "20000000-0000-0000-0000-000000000005", "company": "Acme Corp", "stage": "proposal", "arr": 120000, "risk": "at_risk", "days_ago": 10,
     "thread": [
         {"from": "rep", "to": "vp@acme.com", "subject": "OmniSales Proposal", "body": "Hi Jennifer, as discussed, attached is our proposal for the 50-seat deployment.", "date": "2026-03-10"},
         {"from": "rep", "to": "vp@acme.com", "subject": "Following up on proposal", "body": "Hi Jennifer, just checking in on the proposal I sent last week.", "date": "2026-03-13"},
         {"from": "vp@acme.com", "to": "rep", "subject": "Re: Following up", "body": "Thanks for following up. We are evaluating a few options including AcmeCRM. Will get back to you.", "date": "2026-03-15"}
     ]},
    {"id": "20000000-0000-0000-0000-000000000006", "company": "TechFlow Inc", "stage": "proposal", "arr": 84000, "risk": "stalled", "days_ago": 14,
     "thread": [
         {"from": "rep", "to": "cfo@techflow.io", "subject": "Enterprise pricing", "body": "Hi Robert, here is the pricing breakdown for your 30-person team.", "date": "2026-03-08"},
         {"from": "cfo@techflow.io", "to": "rep", "subject": "Re: Enterprise pricing", "body": "The pricing looks steep compared to what we are paying now. Can you do better?", "date": "2026-03-11"}
     ]},
    {"id": "20000000-0000-0000-0000-000000000007", "company": "DataVista Analytics", "stage": "proposal", "arr": 60000, "risk": "healthy", "days_ago": 4,
     "thread": [{"from": "rep", "to": "head@datavista.co", "subject": "Custom package", "body": "Hi Lin, based on our call, here is a custom package tailored to your analytics team needs.", "date": "2026-03-18"}]},
    {"id": "20000000-0000-0000-0000-000000000008", "company": "GreenGrid Energy", "stage": "proposal", "arr": 96000, "risk": "healthy", "days_ago": 3,
     "thread": [{"from": "rep", "to": "svp@greengrid.com", "subject": "Proposal v2", "body": "Hi Kate, updated proposal with the requested add-ons for your sustainability reporting team.", "date": "2026-03-20"}]},
    # Negotiation (5)
    {"id": "20000000-0000-0000-0000-000000000009", "company": "QuantumLeap AI", "stage": "negotiation", "arr": 200000, "risk": "healthy", "days_ago": 1,
     "thread": [{"from": "cto@quantumleap.ai", "to": "rep", "subject": "Final terms", "body": "We are ready to move forward. Can we discuss annual vs monthly billing?", "date": "2026-03-24"}]},
    {"id": "20000000-0000-0000-0000-000000000010", "company": "NexGen Robotics", "stage": "negotiation", "arr": 150000, "risk": "at_risk", "days_ago": 7,
     "thread": [
         {"from": "rep", "to": "coo@nexgenrobotics.io", "subject": "Updated terms", "body": "Hi Mark, here are the revised terms with the volume discount.", "date": "2026-03-16"},
         {"from": "coo@nexgenrobotics.io", "to": "rep", "subject": "Re: Updated terms", "body": "Our legal team has concerns about the data processing addendum. Also we got a demo from PipeDrive Pro.", "date": "2026-03-18"}
     ]},
    {"id": "20000000-0000-0000-0000-000000000011", "company": "SkyBridge Networks", "stage": "negotiation", "arr": 180000, "risk": "healthy", "days_ago": 2,
     "thread": [{"from": "vp@skybridge.net", "to": "rep", "subject": "Going forward", "body": "Team is aligned. Just need final approval from our CFO next week.", "date": "2026-03-23"}]},
    {"id": "20000000-0000-0000-0000-000000000012", "company": "PeakPerformance SaaS", "stage": "negotiation", "arr": 72000, "risk": "stalled", "days_ago": 12,
     "thread": [{"from": "rep", "to": "director@peakperf.com", "subject": "Q1 deadline reminder", "body": "Hi Amy, wanted to check if you had a chance to review the contract. Our Q1 pricing expires Friday.", "date": "2026-03-10"}]},
    {"id": "20000000-0000-0000-0000-000000000013", "company": "VelocityStack", "stage": "negotiation", "arr": 48000, "risk": "healthy", "days_ago": 3,
     "thread": [{"from": "ceo@velocitystack.io", "to": "rep", "subject": "Ready to sign", "body": "Let us finalize this. Send over the DocuSign.", "date": "2026-03-22"}]},
    # Closed (2)
    {"id": "20000000-0000-0000-0000-000000000014", "company": "AlphaWave Digital", "stage": "closed_won", "arr": 96000, "risk": "healthy", "days_ago": 5,
     "thread": [{"from": "cfo@alphawave.co", "to": "rep", "subject": "Signed!", "body": "Contract signed. Looking forward to onboarding.", "date": "2026-03-20"}]},
    {"id": "20000000-0000-0000-0000-000000000015", "company": "RapidScale Corp", "stage": "closed_lost", "arr": 60000, "risk": "healthy", "days_ago": 7,
     "thread": [{"from": "vp@rapidscale.com", "to": "rep", "subject": "Going another direction", "body": "Appreciate the effort but we decided to go with AcmeCRM. Their pricing was more competitive.", "date": "2026-03-18"}]},
]

ACCOUNTS = [
    # ★ HIGH CHURN RISK — Guardian MUST flag these
    {"id": "30000000-0000-0000-0000-000000000001", "company": "Acme Corp", "arr": 120000, "plan": "enterprise", "hs": 0.23, "cr": 0.91, "usage": 0.15, "tickets": 3, "login_days": 14,
     "meta": {"usage_trend": [0.80,0.72,0.58,0.41,0.22,0.15], "signals": ["Usage dropped 45% in 30 days","3 unresolved P1 tickets","Champion left company","Contract renewal in 90 days"], "nps_score": 3, "contract_end": "2026-06-30"}},
    {"id": "30000000-0000-0000-0000-000000000002", "company": "TechFlow Inc", "arr": 84000, "plan": "professional", "hs": 0.31, "cr": 0.84, "usage": 0.12, "tickets": 1, "login_days": 21,
     "meta": {"usage_trend": [0.65,0.60,0.55,0.40,0.18,0.12], "signals": ["No login in 21 days","Plan utilization at 12%","Competitor demo scheduled","CFO asked about cancellation"], "nps_score": 4, "contract_end": "2026-05-15"}},
    {"id": "30000000-0000-0000-0000-000000000003", "company": "DataVista Analytics", "arr": 60000, "plan": "professional", "hs": 0.38, "cr": 0.78, "usage": 0.25, "tickets": 2, "login_days": 7,
     "meta": {"usage_trend": [0.90,0.85,0.70,0.45,0.30,0.25], "signals": ["Key power user churned","Usage concentrated on 1 user","Downgraded API tier last week"], "nps_score": 5, "contract_end": "2026-07-31"}},
    # MEDIUM RISK
    {"id": "30000000-0000-0000-0000-000000000004", "company": "Orbitron Systems", "arr": 36000, "plan": "starter", "hs": 0.52, "cr": 0.55, "usage": 0.45, "tickets": 1, "login_days": 5,
     "meta": {"usage_trend": [0.60,0.55,0.50,0.48,0.45,0.45], "signals": ["Flat usage trend","Only using 2 of 8 features"], "nps_score": 6, "contract_end": "2026-09-30"}},
    {"id": "30000000-0000-0000-0000-000000000005", "company": "NexGen Robotics", "arr": 150000, "plan": "enterprise", "hs": 0.55, "cr": 0.48, "usage": 0.50, "tickets": 0, "login_days": 4,
     "meta": {"usage_trend": [0.70,0.65,0.58,0.52,0.50,0.50], "signals": ["Gradual decline in API calls","No expansion in 6 months"], "nps_score": 6, "contract_end": "2026-08-15"}},
    # HEALTHY
    {"id": "30000000-0000-0000-0000-000000000006", "company": "QuantumLeap AI", "arr": 200000, "plan": "enterprise", "hs": 0.92, "cr": 0.05, "usage": 0.95, "tickets": 0, "login_days": 0,
     "meta": {"usage_trend": [0.88,0.90,0.91,0.93,0.94,0.95], "signals": ["Power user growth +30%","Exploring API v2"], "nps_score": 9, "contract_end": "2026-12-31"}},
    {"id": "30000000-0000-0000-0000-000000000007", "company": "SkyBridge Networks", "arr": 180000, "plan": "enterprise", "hs": 0.88, "cr": 0.08, "usage": 0.88, "tickets": 0, "login_days": 1,
     "meta": {"usage_trend": [0.82,0.84,0.85,0.86,0.87,0.88], "signals": ["Steady growth","Requested enterprise SSO"], "nps_score": 9, "contract_end": "2027-01-15"}},
    {"id": "30000000-0000-0000-0000-000000000008", "company": "Zenith Applications", "arr": 18000, "plan": "starter", "hs": 0.75, "cr": 0.18, "usage": 0.70, "tickets": 0, "login_days": 2,
     "meta": {"usage_trend": [0.60,0.63,0.65,0.68,0.70,0.70], "signals": ["Organic adoption growing"], "nps_score": 7, "contract_end": "2026-10-31"}},
    {"id": "30000000-0000-0000-0000-000000000009", "company": "ByteWave Labs", "arr": 24000, "plan": "professional", "hs": 0.82, "cr": 0.12, "usage": 0.78, "tickets": 0, "login_days": 1,
     "meta": {"usage_trend": [0.70,0.72,0.74,0.76,0.77,0.78], "signals": ["Added 5 new users","Upgraded plan last month"], "nps_score": 8, "contract_end": "2026-11-30"}},
    {"id": "30000000-0000-0000-0000-000000000010", "company": "GreenGrid Energy", "arr": 96000, "plan": "enterprise", "hs": 0.78, "cr": 0.15, "usage": 0.72, "tickets": 0, "login_days": 3,
     "meta": {"usage_trend": [0.68,0.69,0.70,0.71,0.72,0.72], "signals": ["Stable usage","Renewed early"], "nps_score": 8, "contract_end": "2027-03-31"}},
    {"id": "30000000-0000-0000-0000-000000000011", "company": "PrimeLogistics AI", "arr": 12000, "plan": "starter", "hs": 0.68, "cr": 0.22, "usage": 0.60, "tickets": 0, "login_days": 4,
     "meta": {"usage_trend": [0.55,0.57,0.58,0.59,0.60,0.60], "signals": ["Small but growing team"], "nps_score": 7, "contract_end": "2026-08-31"}},
    {"id": "30000000-0000-0000-0000-000000000012", "company": "AlphaWave Digital", "arr": 96000, "plan": "enterprise", "hs": 0.85, "cr": 0.10, "usage": 0.82, "tickets": 0, "login_days": 1,
     "meta": {"usage_trend": [0.78,0.79,0.80,0.81,0.82,0.82], "signals": ["Recently onboarded","Very engaged CSM calls"], "nps_score": 9, "contract_end": "2027-03-20"}},
    {"id": "30000000-0000-0000-0000-000000000013", "company": "VelocityStack", "arr": 48000, "plan": "professional", "hs": 0.72, "cr": 0.20, "usage": 0.65, "tickets": 0, "login_days": 2,
     "meta": {"usage_trend": [0.60,0.61,0.62,0.63,0.64,0.65], "signals": ["Consistent usage","Exploring integrations"], "nps_score": 7, "contract_end": "2026-09-15"}},
    {"id": "30000000-0000-0000-0000-000000000014", "company": "PeakPerformance SaaS", "arr": 72000, "plan": "professional", "hs": 0.65, "cr": 0.30, "usage": 0.55, "tickets": 1, "login_days": 6,
     "meta": {"usage_trend": [0.62,0.60,0.58,0.56,0.55,0.55], "signals": ["Slight decline","1 open ticket"], "nps_score": 6, "contract_end": "2026-07-15"}},
    {"id": "30000000-0000-0000-0000-000000000015", "company": "NovaTech Solutions", "arr": 0, "plan": "trial", "hs": 0.60, "cr": 0.25, "usage": 0.50, "tickets": 0, "login_days": 3,
     "meta": {"usage_trend": [0.30,0.35,0.40,0.45,0.48,0.50], "signals": ["Trial user, increasing engagement"], "nps_score": 7, "contract_end": "2026-04-30"}},
    {"id": "30000000-0000-0000-0000-000000000016", "company": "CloudScale AI", "arr": 0, "plan": "trial", "hs": 0.55, "cr": 0.35, "usage": 0.40, "tickets": 0, "login_days": 5,
     "meta": {"usage_trend": [0.50,0.48,0.45,0.42,0.40,0.40], "signals": ["Trial engagement declining"], "nps_score": 5, "contract_end": "2026-04-15"}},
    {"id": "30000000-0000-0000-0000-000000000017", "company": "IronClad Security", "arr": 144000, "plan": "enterprise", "hs": 0.90, "cr": 0.06, "usage": 0.92, "tickets": 0, "login_days": 0,
     "meta": {"usage_trend": [0.88,0.89,0.90,0.91,0.92,0.92], "signals": ["Top customer","Expanding to 2nd BU"], "nps_score": 10, "contract_end": "2027-06-30"}},
    {"id": "30000000-0000-0000-0000-000000000018", "company": "BlueStar Analytics", "arr": 36000, "plan": "starter", "hs": 0.70, "cr": 0.22, "usage": 0.62, "tickets": 0, "login_days": 3,
     "meta": {"usage_trend": [0.58,0.59,0.60,0.61,0.62,0.62], "signals": ["Steady small customer"], "nps_score": 7, "contract_end": "2026-10-15"}},
    {"id": "30000000-0000-0000-0000-000000000019", "company": "AgilePath Consulting", "arr": 60000, "plan": "professional", "hs": 0.74, "cr": 0.19, "usage": 0.68, "tickets": 0, "login_days": 2,
     "meta": {"usage_trend": [0.64,0.65,0.66,0.67,0.68,0.68], "signals": ["Consistent mid-tier customer"], "nps_score": 7, "contract_end": "2026-11-15"}},
    {"id": "30000000-0000-0000-0000-000000000020", "company": "FusionWorks Digital", "arr": 84000, "plan": "enterprise", "hs": 0.80, "cr": 0.14, "usage": 0.75, "tickets": 0, "login_days": 1,
     "meta": {"usage_trend": [0.70,0.71,0.72,0.73,0.74,0.75], "signals": ["Growing steadily","Interested in API access"], "nps_score": 8, "contract_end": "2027-02-28"}},
]

COMPETITORS = [
    {"id": "40000000-0000-0000-0000-000000000001", "name": "AcmeCRM", "website": "https://acmecrm.io", "hours_ago": 2, "hash": "hash_abc123",
     "data": {"battlecard": {"pricing": {"starter": "$39/user/mo", "professional": "$69/user/mo", "enterprise": "$99/user/mo"}, "strengths": ["Strong brand recognition","Large partner ecosystem","SOC 2 Type II"], "weaknesses": ["No AI agents","3 native integrations","Manual review process","6-month implementation"], "differentiators": {"omnisales_advantage": ["Autonomous AI agents vs static rules","14x faster risk detection","A2A inter-agent intelligence","24-hour deployment via Docker"]}, "recent_changes": [{"date": "2026-03-01", "type": "price_increase", "detail": "Enterprise tier increased from $89 to $99/user/mo"}]}}},
    {"id": "40000000-0000-0000-0000-000000000002", "name": "PipeDrive Pro", "website": "https://pipedrivepro.com", "hours_ago": 4, "hash": "hash_def456",
     "data": {"battlecard": {"pricing": {"starter": "$29/user/mo", "professional": "$49/user/mo", "enterprise": "$79/user/mo"}, "strengths": ["Lower price point","User-friendly UI","Good mobile app"], "weaknesses": ["No multi-agent system","Limited enterprise features","No A2A or MCP support","Basic reporting only"], "differentiators": {"omnisales_advantage": ["Enterprise-grade AI autonomy","Real-time churn prediction","RAG-powered objection handling","Kafka event-driven architecture"]}}}},
    {"id": "40000000-0000-0000-0000-000000000003", "name": "ZoomInfo Sales", "website": "https://zoominfo.com", "hours_ago": 6, "hash": "hash_ghi789",
     "data": {"battlecard": {"pricing": {"professional": "$14,995/year", "advanced": "$24,995/year", "elite": "$39,995/year"}, "strengths": ["Best-in-class data enrichment","Massive contact database","Intent data signals"], "weaknesses": ["Enrichment only","No deal management","No churn prediction","Very expensive for small teams"], "differentiators": {"omnisales_advantage": ["Full-cycle autonomy","3 AI agents vs data-only platform","10x cheaper per seat","Built-in approval workflows"]}}}},
]


async def main():
    print("\n🔄 OmniSales Demo Reset")
    print("=" * 50)

    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env")
        sys.exit(1)

    conn = await asyncpg.connect(DATABASE_URL, ssl='require')

    try:
        # ── CLEAR ──
        print("\n🗑️  Clearing all tables...")
        for tbl in ['agent_tasks', 'scan_reports', 'competitors', 'deals', 'accounts', 'leads']:
            r = await conn.execute(f"DELETE FROM {tbl}")
            print(f"   ✓ {tbl}: {r}")

        # ── LEADS ──
        print("\n🌱 Seeding 5 leads...")
        for lead in LEADS:
            await conn.execute("""
                INSERT INTO leads (id, org_id, company, contact_name, email, title, icp_score, tier, status, source, enrichment)
                VALUES ($1, $2, $3, $4, $5, $6, NULL, 'D', 'new', 'prospector', $7::jsonb)
            """, lead['id'], ORG, lead['company'], lead['contact_name'], lead['email'], lead['title'], json.dumps(lead['enrichment']))
        c = await conn.fetchval("SELECT count(*) FROM leads")
        print(f"   ✓ {c} leads inserted")

        # ── DEALS ──
        print("\n🌱 Seeding 15 deals...")
        for d in DEALS:
            await conn.execute("""
                INSERT INTO deals (id, org_id, lead_id, company, stage, arr, risk_level, last_activity, closer_thread)
                VALUES ($1, $2, NULL, $3, $4, $5, $6, NOW() - ($7 || ' days')::interval, $8::jsonb)
            """, d['id'], ORG, d['company'], d['stage'], d['arr'], d['risk'], str(d['days_ago']), json.dumps(d['thread']))
        c = await conn.fetchval("SELECT count(*) FROM deals")
        print(f"   ✓ {c} deals inserted")

        # ── ACCOUNTS ──
        print("\n🌱 Seeding 20 accounts...")
        for a in ACCOUNTS:
            await conn.execute("""
                INSERT INTO accounts (id, org_id, company, arr, plan, health_score, churn_risk, usage_pct, support_tickets, last_login, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW() - ($10 || ' days')::interval, $11::jsonb)
            """, a['id'], ORG, a['company'], a['arr'], a['plan'], a['hs'], a['cr'], a['usage'], a['tickets'], str(a['login_days']), json.dumps(a['meta']))
        c = await conn.fetchval("SELECT count(*) FROM accounts")
        print(f"   ✓ {c} accounts inserted")

        # ── COMPETITORS ──
        print("\n🌱 Seeding 3 competitors...")
        for comp in COMPETITORS:
            await conn.execute("""
                INSERT INTO competitors (id, org_id, name, website, last_scraped, pricing_hash, data)
                VALUES ($1, $2, $3, $4, NOW() - ($5 || ' hours')::interval, $6, $7::jsonb)
            """, comp['id'], ORG, comp['name'], comp['website'], str(comp['hours_ago']), comp['hash'], json.dumps(comp['data']))
        c = await conn.fetchval("SELECT count(*) FROM competitors")
        print(f"   ✓ {c} competitors inserted")

        # ── VERIFY ──
        tasks = await conn.fetchval("SELECT count(*) FROM agent_tasks")
        scans = await conn.fetchval("SELECT count(*) FROM scan_reports")

        print(f"\n{'='*50}")
        print("✅ DATABASE READY FOR DEMO")
        print(f"{'='*50}")
        print(f"""
📊 Counts: 5 leads | 15 deals | 20 accounts | 3 competitors
📋 Audit:  {tasks} tasks | {scans} scans (clean)

🎬 Demo Flow:
   1. Prospecting → Run on "NovaTech Solutions"
   2. Pipeline    → Run Closer on "TechFlow Inc" ($84K)
   3. Churn       → Run Guardian scan (3 high-risk)
   4. Chat 🧠     → Ask "What's the pipeline status?"
   5. Approvals   → Approve a pending task
   6. Thinking    → Show LangGraph reasoning
   7. Audit       → Show activity history
   8. Architecture→ Click agent node → flowchart

🔐 Login: admin@omnisales.ai / hackathon2026
""")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
