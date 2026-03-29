import asyncio
from shared.db import execute

async def inject_test_data():
    # Insert high risk account
    await execute(
        '''
        INSERT INTO accounts (id, company, plan, health_score, churn_risk, arr, usage_pct, support_tickets)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (id) DO UPDATE SET health_score=$4, churn_risk=$5
        ''',
        "b0000000-0000-0000-0000-0000000critical",
        "Critical Corp",
        "enterprise",
        0.1,  # Critical health
        0.95, # High churn
        50000,
        0.2,
        10
    )
    print("Injected critical account!")

if __name__ == "__main__":
    asyncio.run(inject_test_data())
