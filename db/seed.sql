-- ============================================================
-- OmniSales — Seed Data for Hackathon Demo
-- 20 accounts · 15 deals · 5 leads · 3 competitors
-- ============================================================

-- Fixed org_id for demo
-- org_id = 'a0000000-0000-0000-0000-000000000001'

-- ── 5 Leads (Prospector scenario — cold outreach targets) ──

INSERT INTO leads (id, org_id, company, contact_name, email, title, icp_score, tier, status, source, enrichment) VALUES
('10000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
 'NovaTech Solutions', 'Sarah Chen', 'sarah.chen@novatech.io', 'VP of Sales',
 NULL, 'D', 'new', 'prospector',
 '{"founded": 2019, "employees": 125, "funding": "Series B ($18M)", "industry": "SaaS", "tech_stack": ["Salesforce", "Outreach", "Gong"], "revenue_est": "$12M ARR", "signals": ["Hiring 3 AEs", "New CRO appointed Q1"], "contacts": [{"name": "Sarah Chen", "title": "VP of Sales", "linkedin": "linkedin.com/in/sarachen"}, {"name": "James Park", "title": "CRO", "linkedin": "linkedin.com/in/jamespark"}]}'),

('10000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
 'CloudScale AI', 'Marcus Johnson', 'marcus@cloudscale.ai', 'Head of Revenue',
 NULL, 'D', 'new', 'prospector',
 '{"founded": 2021, "employees": 85, "funding": "Series A ($9M)", "industry": "AI/ML Platform", "tech_stack": ["HubSpot", "Apollo"], "revenue_est": "$5M ARR", "signals": ["170% YoY growth", "Expanding EU market"], "contacts": [{"name": "Marcus Johnson", "title": "Head of Revenue", "linkedin": "linkedin.com/in/marcusj"}, {"name": "Priya Patel", "title": "VP Sales", "linkedin": "linkedin.com/in/priyap"}]}'),

('10000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001',
 'DataVault Security', 'Elena Rodriguez', 'elena@datavault.com', 'CRO',
 NULL, 'D', 'new', 'prospector',
 '{"founded": 2018, "employees": 210, "funding": "Series C ($45M)", "industry": "Cybersecurity", "tech_stack": ["Salesforce", "ZoomInfo"], "revenue_est": "$28M ARR", "signals": ["IPO prep rumored", "New enterprise tier launched"], "contacts": [{"name": "Elena Rodriguez", "title": "CRO", "linkedin": "linkedin.com/in/elenarodriguez"}, {"name": "Tom Wright", "title": "VP Enterprise Sales", "linkedin": "linkedin.com/in/tomwright"}]}'),

('10000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001',
 'FinFlow Analytics', 'David Kim', 'dkim@finflow.co', 'VP Sales',
 NULL, 'D', 'new', 'prospector',
 '{"founded": 2020, "employees": 60, "funding": "Seed ($3M)", "industry": "FinTech", "tech_stack": ["Pipedrive", "Lemlist"], "revenue_est": "$2M ARR", "signals": ["Pivoting to enterprise", "Hired first VP Sales"], "contacts": [{"name": "David Kim", "title": "VP Sales", "linkedin": "linkedin.com/in/davidkim"}, {"name": "Lisa Tran", "title": "CEO", "linkedin": "linkedin.com/in/lisatran"}]}'),

('10000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001',
 'MediConnect Pro', 'Rachel Green', 'rgreen@mediconnect.health', 'Director of Growth',
 NULL, 'D', 'new', 'prospector',
 '{"founded": 2017, "employees": 320, "funding": "Series D ($72M)", "industry": "HealthTech", "tech_stack": ["Salesforce", "Marketo", "6sense"], "revenue_est": "$40M ARR", "signals": ["Launched APAC office", "200 new enterprise contracts"], "contacts": [{"name": "Rachel Green", "title": "Director of Growth", "linkedin": "linkedin.com/in/rachelgreen"}, {"name": "Alex Morales", "title": "SVP Revenue", "linkedin": "linkedin.com/in/alexmorales"}]}');


-- ── 15 Deals (Closer scenario — across all pipeline stages) ──

INSERT INTO deals (id, org_id, lead_id, company, stage, arr, risk_level, last_activity, closer_thread) VALUES
-- Discovery (4 deals)
('20000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', NULL,
 'Zenith Applications', 'discovery', 18000, 'healthy', NOW() - INTERVAL '2 days',
 '[{"from": "rep", "to": "cto@zenith.io", "subject": "Quick intro", "body": "Hi Alex, saw your Series A — congrats! Would love to show how we can help your sales team scale...", "date": "2026-03-20"}]'),

('20000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', NULL,
 'ByteWave Labs', 'discovery', 24000, 'healthy', NOW() - INTERVAL '1 day',
 '[{"from": "rep", "to": "vp@bytewave.dev", "subject": "AI Sales Automation", "body": "Hi Jordan, noticed your team is hiring 5 SDRs...", "date": "2026-03-22"}]'),

('20000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', NULL,
 'Orbitron Systems', 'discovery', 36000, 'at_risk', NOW() - INTERVAL '8 days',
 '[{"from": "rep", "to": "cro@orbitron.com", "subject": "Revenue Operations", "body": "Hi Maria, your revenue ops role posting caught my eye...", "date": "2026-03-15"}]'),

('20000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', NULL,
 'PrimeLogistics AI', 'discovery', 12000, 'healthy', NOW() - INTERVAL '3 days',
 '[{"from": "rep", "to": "head@primelogistics.ai", "subject": "Streamlining outbound", "body": "Hi Sam, saw your LinkedIn post about scaling outbound...", "date": "2026-03-19"}]'),

-- Proposal (4 deals)
('20000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', NULL,
 'Acme Corp', 'proposal', 120000, 'at_risk', NOW() - INTERVAL '10 days',
 '[{"from": "rep", "to": "vp@acme.com", "subject": "OmniSales Proposal", "body": "Hi Jennifer, as discussed, attached is our proposal for the 50-seat deployment...", "date": "2026-03-10"}, {"from": "rep", "to": "vp@acme.com", "subject": "Following up on proposal", "body": "Hi Jennifer, just checking in on the proposal I sent last week...", "date": "2026-03-13"}, {"from": "vp@acme.com", "to": "rep", "subject": "Re: Following up", "body": "Thanks for following up. We''re evaluating a few options including AcmeCRM. Will get back to you.", "date": "2026-03-15"}]'),

('20000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001', NULL,
 'TechFlow Inc', 'proposal', 84000, 'stalled', NOW() - INTERVAL '14 days',
 '[{"from": "rep", "to": "cfo@techflow.io", "subject": "Enterprise pricing", "body": "Hi Robert, here is the pricing breakdown for your 30-person team...", "date": "2026-03-08"}, {"from": "cfo@techflow.io", "to": "rep", "subject": "Re: Enterprise pricing", "body": "The pricing looks steep compared to what we are paying now. Can you do better?", "date": "2026-03-11"}]'),

('20000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000001', NULL,
 'DataVista Analytics', 'proposal', 60000, 'healthy', NOW() - INTERVAL '4 days',
 '[{"from": "rep", "to": "head@datavista.co", "subject": "Custom package", "body": "Hi Lin, based on our call, I have put together a custom package...", "date": "2026-03-18"}]'),

('20000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000001', NULL,
 'GreenGrid Energy', 'proposal', 96000, 'healthy', NOW() - INTERVAL '3 days',
 '[{"from": "rep", "to": "svp@greengrid.com", "subject": "Proposal v2", "body": "Hi Kate, updated proposal with the requested add-ons...", "date": "2026-03-20"}]'),

-- Negotiation (5 deals)
('20000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000001', NULL,
 'QuantumLeap AI', 'negotiation', 200000, 'healthy', NOW() - INTERVAL '1 day',
 '[{"from": "cto@quantumleap.ai", "to": "rep", "subject": "Final terms", "body": "We are ready to move forward. Can we discuss annual vs monthly billing?", "date": "2026-03-24"}]'),

('20000000-0000-0000-0000-000000000010', 'a0000000-0000-0000-0000-000000000001', NULL,
 'NexGen Robotics', 'negotiation', 150000, 'at_risk', NOW() - INTERVAL '7 days',
 '[{"from": "rep", "to": "coo@nexgenrobotics.io", "subject": "Updated terms", "body": "Hi Mark, here are the revised terms with the volume discount...", "date": "2026-03-16"}, {"from": "coo@nexgenrobotics.io", "to": "rep", "subject": "Re: Updated terms", "body": "Our legal team has concerns about the data processing addendum.", "date": "2026-03-18"}]'),

('20000000-0000-0000-0000-000000000011', 'a0000000-0000-0000-0000-000000000001', NULL,
 'SkyBridge Networks', 'negotiation', 180000, 'healthy', NOW() - INTERVAL '2 days',
 '[{"from": "vp@skybridge.net", "to": "rep", "subject": "Going forward", "body": "Team is aligned. Just need final approval from our CFO next week.", "date": "2026-03-23"}]'),

('20000000-0000-0000-0000-000000000012', 'a0000000-0000-0000-0000-000000000001', NULL,
 'PeakPerformance SaaS', 'negotiation', 72000, 'stalled', NOW() - INTERVAL '12 days',
 '[{"from": "rep", "to": "director@peakperf.com", "subject": "Q1 deadline", "body": "Hi Amy, wanted to check if you had a chance to review the contract...", "date": "2026-03-10"}]'),

('20000000-0000-0000-0000-000000000013', 'a0000000-0000-0000-0000-000000000001', NULL,
 'VelocityStack', 'negotiation', 48000, 'healthy', NOW() - INTERVAL '3 days',
 '[{"from": "ceo@velocitystack.io", "to": "rep", "subject": "Ready to sign", "body": "Let us finalize this. Send over the DocuSign.", "date": "2026-03-22"}]'),

-- Closed (2 deals)
('20000000-0000-0000-0000-000000000014', 'a0000000-0000-0000-0000-000000000001', NULL,
 'AlphaWave Digital', 'closed_won', 96000, 'healthy', NOW() - INTERVAL '5 days',
 '[{"from": "cfo@alphawave.co", "to": "rep", "subject": "Signed!", "body": "Contract signed. Looking forward to onboarding.", "date": "2026-03-20"}]'),

('20000000-0000-0000-0000-000000000015', 'a0000000-0000-0000-0000-000000000001', NULL,
 'RapidScale Corp', 'closed_lost', 60000, 'healthy', NOW() - INTERVAL '7 days',
 '[{"from": "vp@rapidscale.com", "to": "rep", "subject": "Going another direction", "body": "Appreciate the effort but we have decided to go with AcmeCRM.", "date": "2026-03-18"}]');


-- ── 20 Accounts (Guardian scenario — churn monitoring) ──

INSERT INTO accounts (id, org_id, company, arr, plan, health_score, churn_risk, usage_pct, support_tickets, last_login, metadata) VALUES
-- HIGH CHURN RISK (top 3 — Guardian should flag these)
('30000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
 'Acme Corp', 120000, 'enterprise', 0.23, 0.91, 0.15, 3, NOW() - INTERVAL '14 days',
 '{"usage_trend": [0.80, 0.72, 0.58, 0.41, 0.22, 0.15], "signals": ["Usage dropped 45% in 30 days", "3 unresolved P1 tickets", "Champion left company"], "nps_score": 3, "contract_end": "2026-06-30"}'),

('30000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
 'TechFlow Inc', 84000, 'professional', 0.31, 0.84, 0.12, 1, NOW() - INTERVAL '21 days',
 '{"usage_trend": [0.65, 0.60, 0.55, 0.40, 0.18, 0.12], "signals": ["No login in 21 days", "Plan utilization at 12%", "Competitor demo scheduled"], "nps_score": 4, "contract_end": "2026-05-15"}'),

('30000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001',
 'DataVista Analytics', 60000, 'professional', 0.38, 0.78, 0.25, 2, NOW() - INTERVAL '7 days',
 '{"usage_trend": [0.90, 0.85, 0.70, 0.45, 0.30, 0.25], "signals": ["Key power user churned", "Usage concentrated on 1 user", "Downgraded API tier"], "nps_score": 5, "contract_end": "2026-07-31"}'),

-- MEDIUM RISK (amber zone)
('30000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001',
 'Orbitron Systems', 36000, 'starter', 0.52, 0.55, 0.45, 1, NOW() - INTERVAL '5 days',
 '{"usage_trend": [0.60, 0.55, 0.50, 0.48, 0.45, 0.45], "signals": ["Flat usage trend", "Only using 2 of 8 features"], "nps_score": 6, "contract_end": "2026-09-30"}'),

('30000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001',
 'NexGen Robotics', 150000, 'enterprise', 0.55, 0.48, 0.50, 0, NOW() - INTERVAL '4 days',
 '{"usage_trend": [0.70, 0.65, 0.58, 0.52, 0.50, 0.50], "signals": ["Gradual decline in API calls", "No expansion in 6 months"], "nps_score": 6, "contract_end": "2026-08-15"}'),

-- HEALTHY (green zone)
('30000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001',
 'QuantumLeap AI', 200000, 'enterprise', 0.92, 0.05, 0.95, 0, NOW() - INTERVAL '0 days',
 '{"usage_trend": [0.88, 0.90, 0.91, 0.93, 0.94, 0.95], "signals": ["Power user growth +30%", "Exploring API v2"], "nps_score": 9, "contract_end": "2026-12-31"}'),

('30000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000001',
 'SkyBridge Networks', 180000, 'enterprise', 0.88, 0.08, 0.88, 0, NOW() - INTERVAL '1 day',
 '{"usage_trend": [0.82, 0.84, 0.85, 0.86, 0.87, 0.88], "signals": ["Steady growth", "Requested enterprise SSO"], "nps_score": 9, "contract_end": "2027-01-15"}'),

('30000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000001',
 'Zenith Applications', 18000, 'starter', 0.75, 0.18, 0.70, 0, NOW() - INTERVAL '2 days',
 '{"usage_trend": [0.60, 0.63, 0.65, 0.68, 0.70, 0.70], "signals": ["Organic adoption growing"], "nps_score": 7, "contract_end": "2026-10-31"}'),

('30000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000001',
 'ByteWave Labs', 24000, 'professional', 0.82, 0.12, 0.78, 0, NOW() - INTERVAL '1 day',
 '{"usage_trend": [0.70, 0.72, 0.74, 0.76, 0.77, 0.78], "signals": ["Added 5 new users", "Upgraded plan last month"], "nps_score": 8, "contract_end": "2026-11-30"}'),

('30000000-0000-0000-0000-000000000010', 'a0000000-0000-0000-0000-000000000001',
 'GreenGrid Energy', 96000, 'enterprise', 0.78, 0.15, 0.72, 0, NOW() - INTERVAL '3 days',
 '{"usage_trend": [0.68, 0.69, 0.70, 0.71, 0.72, 0.72], "signals": ["Stable usage", "Renewed early"], "nps_score": 8, "contract_end": "2027-03-31"}'),

('30000000-0000-0000-0000-000000000011', 'a0000000-0000-0000-0000-000000000001',
 'PrimeLogistics AI', 12000, 'starter', 0.68, 0.22, 0.60, 0, NOW() - INTERVAL '4 days',
 '{"usage_trend": [0.55, 0.57, 0.58, 0.59, 0.60, 0.60], "signals": ["Small but growing team"], "nps_score": 7, "contract_end": "2026-08-31"}'),

('30000000-0000-0000-0000-000000000012', 'a0000000-0000-0000-0000-000000000001',
 'AlphaWave Digital', 96000, 'enterprise', 0.85, 0.10, 0.82, 0, NOW() - INTERVAL '1 day',
 '{"usage_trend": [0.78, 0.79, 0.80, 0.81, 0.82, 0.82], "signals": ["Recently onboarded", "Very engaged CSM calls"], "nps_score": 9, "contract_end": "2027-03-20"}'),

('30000000-0000-0000-0000-000000000013', 'a0000000-0000-0000-0000-000000000001',
 'VelocityStack', 48000, 'professional', 0.72, 0.20, 0.65, 0, NOW() - INTERVAL '2 days',
 '{"usage_trend": [0.60, 0.61, 0.62, 0.63, 0.64, 0.65], "signals": ["Consistent usage", "Exploring integrations"], "nps_score": 7, "contract_end": "2026-09-15"}'),

('30000000-0000-0000-0000-000000000014', 'a0000000-0000-0000-0000-000000000001',
 'PeakPerformance SaaS', 72000, 'professional', 0.65, 0.30, 0.55, 1, NOW() - INTERVAL '6 days',
 '{"usage_trend": [0.62, 0.60, 0.58, 0.56, 0.55, 0.55], "signals": ["Slight decline", "1 open ticket"], "nps_score": 6, "contract_end": "2026-07-15"}'),

('30000000-0000-0000-0000-000000000015', 'a0000000-0000-0000-0000-000000000001',
 'NovaTech Solutions', 0, 'trial', 0.60, 0.25, 0.50, 0, NOW() - INTERVAL '3 days',
 '{"usage_trend": [0.30, 0.35, 0.40, 0.45, 0.48, 0.50], "signals": ["Trial user, increasing engagement"], "nps_score": 7, "contract_end": "2026-04-30"}'),

('30000000-0000-0000-0000-000000000016', 'a0000000-0000-0000-0000-000000000001',
 'CloudScale AI', 0, 'trial', 0.55, 0.35, 0.40, 0, NOW() - INTERVAL '5 days',
 '{"usage_trend": [0.50, 0.48, 0.45, 0.42, 0.40, 0.40], "signals": ["Trial engagement declining"], "nps_score": 5, "contract_end": "2026-04-15"}'),

('30000000-0000-0000-0000-000000000017', 'a0000000-0000-0000-0000-000000000001',
 'IronClad Security', 144000, 'enterprise', 0.90, 0.06, 0.92, 0, NOW() - INTERVAL '0 days',
 '{"usage_trend": [0.88, 0.89, 0.90, 0.91, 0.92, 0.92], "signals": ["Top customer", "Expanding to 2nd BU"], "nps_score": 10, "contract_end": "2027-06-30"}'),

('30000000-0000-0000-0000-000000000018', 'a0000000-0000-0000-0000-000000000001',
 'BlueStar Analytics', 36000, 'starter', 0.70, 0.22, 0.62, 0, NOW() - INTERVAL '3 days',
 '{"usage_trend": [0.58, 0.59, 0.60, 0.61, 0.62, 0.62], "signals": ["Steady small customer"], "nps_score": 7, "contract_end": "2026-10-15"}'),

('30000000-0000-0000-0000-000000000019', 'a0000000-0000-0000-0000-000000000001',
 'AgilePath Consulting', 60000, 'professional', 0.74, 0.19, 0.68, 0, NOW() - INTERVAL '2 days',
 '{"usage_trend": [0.64, 0.65, 0.66, 0.67, 0.68, 0.68], "signals": ["Consistent mid-tier customer"], "nps_score": 7, "contract_end": "2026-11-15"}'),

('30000000-0000-0000-0000-000000000020', 'a0000000-0000-0000-0000-000000000001',
 'FusionWorks Digital', 84000, 'enterprise', 0.80, 0.14, 0.75, 0, NOW() - INTERVAL '1 day',
 '{"usage_trend": [0.70, 0.71, 0.72, 0.73, 0.74, 0.75], "signals": ["Growing steadily", "Interested in API access"], "nps_score": 8, "contract_end": "2027-02-28"}');


-- ── 3 Competitors (Spy domain — battle card data) ──

INSERT INTO competitors (id, org_id, name, website, last_scraped, pricing_hash, data) VALUES
('40000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
 'AcmeCRM', 'https://acmecrm.io', NOW() - INTERVAL '2 hours', 'hash_abc123',
 '{"battlecard": {"pricing": {"starter": "$39/user/mo", "professional": "$69/user/mo", "enterprise": "$99/user/mo"}, "strengths": ["Strong brand recognition", "Large partner ecosystem", "SOC 2 Type II"], "weaknesses": ["No AI agents — rules-based automation only", "3 native integrations vs our 12 MCP servers", "Manual review process, no HITL workflow", "6-month implementation timeline"], "differentiators": {"omnisales_advantage": ["Autonomous AI agents vs static rules", "14x faster risk detection", "A2A inter-agent intelligence", "24-hour deployment via Docker"]}, "recent_changes": [{"date": "2026-03-01", "type": "price_increase", "detail": "Enterprise tier increased from $89 to $99/user/mo"}, {"date": "2026-02-15", "type": "new_feature", "detail": "Added basic lead scoring (rule-based)"}]}}'),

('40000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001',
 'PipeDrive Pro', 'https://pipedrivepro.com', NOW() - INTERVAL '4 hours', 'hash_def456',
 '{"battlecard": {"pricing": {"starter": "$29/user/mo", "professional": "$49/user/mo", "enterprise": "$79/user/mo"}, "strengths": ["Lower price point", "User-friendly UI", "Good mobile app"], "weaknesses": ["No multi-agent system", "Limited enterprise features", "No A2A or MCP support", "Basic reporting only"], "differentiators": {"omnisales_advantage": ["Enterprise-grade AI autonomy", "Real-time churn prediction", "RAG-powered objection handling", "Kafka event-driven architecture"]}, "recent_changes": [{"date": "2026-03-10", "type": "new_feature", "detail": "Added AI email writing (single-shot, no reasoning chain)"}]}}'),

('40000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001',
 'ZoomInfo Sales', 'https://zoominfo.com', NOW() - INTERVAL '6 hours', 'hash_ghi789',
 '{"battlecard": {"pricing": {"professional": "$14,995/year", "advanced": "$24,995/year", "elite": "$39,995/year"}, "strengths": ["Best-in-class data enrichment", "Massive contact database", "Intent data signals"], "weaknesses": ["Enrichment only — no autonomous actions", "No deal management", "No churn prediction", "Very expensive for small teams"], "differentiators": {"omnisales_advantage": ["Full-cycle autonomy: prospect → close → retain", "3 AI agents vs data-only platform", "10x cheaper per seat", "Built-in approval workflows"]}, "recent_changes": [{"date": "2026-02-28", "type": "acquisition", "detail": "Acquired small AI startup for email personalization"}]}}');
