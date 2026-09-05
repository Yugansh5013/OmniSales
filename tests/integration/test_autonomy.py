import asyncio
import os
import asyncpg
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable is required.")
ORG_ID = "a0000000-0000-0000-0000-000000000001"

async def inject_data():
    print("Connecting to Neon Postgres...")
    conn = await asyncpg.connect(DB_URL)
    try:
        print("Injecting Leads (Prospector targets)...")
        await conn.execute('''
            INSERT INTO leads (org_id, company, contact_name, email, title, status) VALUES
            ($1, 'Auto-Test Lead 1', 'Alice Tester', 'alice@autotest1.com', 'CEO', 'new'),
            ($1, 'Auto-Test Lead 2', 'Bob Automator', 'bob@autotest2.com', 'CTO', 'new'),
            ($1, 'Auto-Test Lead 3', 'Charlie System', 'charlie@autotest3.com', 'Director', 'new')
        ''', ORG_ID)

        print("Injecting Deals (Closer targets)...")
        old_date = datetime.now(timezone.utc) - timedelta(days=10)
        await conn.execute('''
            INSERT INTO deals (org_id, company, stage, arr, risk_level, last_activity) VALUES
            ($1, 'Auto-Test Deal 1', 'negotiation', 150000, 'stalled', $2),
            ($1, 'Auto-Test Deal 2', 'proposal', 85000, 'at_risk', $2),
            ($1, 'Auto-Test Deal 3', 'discovery', 250000, 'stalled', $2)
        ''', ORG_ID, old_date)

        print("Injecting Accounts (Guardian targets)...")
        await conn.execute('''
            INSERT INTO accounts (org_id, company, arr, plan, health_score, churn_risk) VALUES
            ($1, 'Auto-Test Account 1', 50000, 'enterprise', 0.2, 0.9),
            ($1, 'Auto-Test Account 2', 75000, 'professional', 0.3, 0.8),
            ($1, 'Auto-Test Account 3', 30000, 'starter', 0.1, 0.95)
        ''', ORG_ID)

        print("Successfully injected autonomous test data. The Orchestrator should pick this up within 60 seconds.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(inject_data())
