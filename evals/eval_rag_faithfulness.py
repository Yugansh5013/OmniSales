"""RAG Evaluation Suite: Faithfulness & Context Relevance.

Uses openevals built-in judges:
- RAG_GROUNDEDNESS_PROMPT: Evaluates whether generated email drafts only state claims grounded in CRM context and battle cards (hallucination detection).
- RAG_RETRIEVAL_RELEVANCE_PROMPT: Evaluates precision of knowledge retrieval against queries.
"""

from __future__ import annotations

import os
import sys
import time
import json
import logging
from typing import Any

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openevals import create_llm_as_judge
from openevals.prompts import RAG_GROUNDEDNESS_PROMPT, RAG_RETRIEVAL_RELEVANCE_PROMPT
from shared.llm import get_fast_llm

logger = logging.getLogger(__name__)


def evaluate_rag_faithfulness_and_relevance() -> dict[str, Any]:
    """Run faithfulness (groundedness) and retrieval context relevance checks on 10+10 cases."""
    llm = get_fast_llm()

    # Create openevals LLM-as-judge instances
    groundedness_judge = create_llm_as_judge(
        prompt=RAG_GROUNDEDNESS_PROMPT,
        feedback_key="groundedness",
        judge=llm,
    )

    relevance_judge = create_llm_as_judge(
        prompt=RAG_RETRIEVAL_RELEVANCE_PROMPT,
        feedback_key="context_relevance",
        judge=llm,
    )

    # 1. 10 Expanded Faithfulness Test Scenarios (Draft vs Ground-Truth Context)
    faithfulness_test_cases = [
        {
            "name": "Faithful Competitor Objection Draft",
            "context": "AcmeCRM charges $45/user/month with no SLA and lacks native multi-agent AI orchestration. OmniSales offers full autonomous revenue department.",
            "draft": "While AcmeCRM is priced at $45/user/mo, it lacks multi-agent AI orchestration and SLAs, whereas OmniSales provides an autonomous revenue department.",
            "is_faithful_ground_truth": True,
        },
        {
            "name": "Faithful Follow-Up Draft",
            "context": "Prospect CloudScale AI has ARR of $120k, legal approved MSA yesterday.",
            "draft": "Following up with CloudScale AI regarding the signed MSA approved yesterday for your $120k ARR subscription.",
            "is_faithful_ground_truth": True,
        },
        {
            "name": "Subtle Price Discount Hallucination",
            "context": "OmniSales standard enterprise discount policy permits up to 15% discount on 12-month contracts, or 25% on 24-month commitments.",
            "draft": "I have gone ahead and approved a 40% discount on a monthly rolling contract with no annual commitment.",
            "is_faithful_ground_truth": False,
        },
        {
            "name": "Subtle SLA Uptime Hallucination",
            "context": "OmniSales standard enterprise SLA provides 99.9% uptime and 1-hour response times for critical P1 issues.",
            "draft": "We guarantee 99.999% uptime with 30-second dedicated Slack response times for any question.",
            "is_faithful_ground_truth": False,
        },
        {
            "name": "Subtle Integration Hallucination",
            "context": "OmniSales integrates natively with Salesforce, HubSpot, and PostgreSQL databases via REST API and webhooks.",
            "draft": "OmniSales features an out-of-the-box native real-time bi-directional connector for legacy AS400 mainframe systems.",
            "is_faithful_ground_truth": False,
        },
        {
            "name": "Faithful Commercial Terms Draft",
            "context": "Standard commercial terms require Annual Upfront billing with Net 30 payment terms for contracts over $20k ARR.",
            "draft": "Our proposal reflects Net 30 payment terms with annual upfront billing as standard for your $35k ARR tier.",
            "is_faithful_ground_truth": True,
        },
        {
            "name": "Unfaithful Competitor Status Claim",
            "context": "PipeDrive Pro is a CRM competitor. Their weakness is lack of AI agent orchestration.",
            "draft": "PipeDrive Pro is shutting down their service next quarter so you should switch to OmniSales immediately.",
            "is_faithful_ground_truth": False,
        },
        {
            "name": "Faithful Security Response",
            "context": "OmniSales is SOC2 Type II compliant and encrypts all customer data with AES-256 at rest and TLS 1.3 in transit.",
            "draft": "Regarding security compliance, OmniSales is SOC2 Type II certified and employs AES-256 encryption at rest and TLS 1.3 in transit.",
            "is_faithful_ground_truth": True,
        },
        {
            "name": "Subtle Payment Term Hallucination",
            "context": "Corporate policy strictly prohibits Net 90 and Net 120 terms without CFO Board approval.",
            "draft": "We can easily set up Net 120 deferred payment terms for your invoice without any special executive approvals.",
            "is_faithful_ground_truth": False,
        },
        {
            "name": "Faithful Retention Playbook Draft",
            "context": "When customer seat utilization drops below 30%, account executives offer complimentary onboarding workshops and a 10% renewal concession.",
            "draft": "To help your team maximize platform adoption, we would love to provide a complimentary team training workshop along with a 10% concession on your upcoming renewal.",
            "is_faithful_ground_truth": True,
        },
    ]

    # 2. 10 Expanded Context Relevance Test Scenarios (Query vs Retrieved Document)
    relevance_test_cases = [
        {
            "name": "Relevant Battle Card: AcmeCRM",
            "query": "How do we win against AcmeCRM pricing objections?",
            "retrieved_context": "AcmeCRM Battle Card: Price: $45/user/mo. Strengths: Simple UI. Weaknesses: No autonomous agents, weak reporting, hidden add-on costs. Win Strategy: Highlight 4-agent autonomous pipeline and lower total cost of ownership.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Relevant Retention Playbook: Low Utilization",
            "query": "What is the recommended retention playbook for low seat utilization?",
            "retrieved_context": "Retention Playbook: When usage drops below 30%, trigger CS executive check-in, offer free team retraining, and extend a 15% annual renewal concession if multi-year commitment is secured.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Irrelevant Office Policy Retrieval",
            "query": "How do we respond to Salesforce CRM displacement objection?",
            "retrieved_context": "Office kitchen policy: Coffee beans are refilled every Monday morning. Please clean up the breakroom after lunch.",
            "is_relevant_ground_truth": False,
        },
        {
            "name": "Relevant Salesforce Battle Card",
            "query": "Prospect says Salesforce already integrates with their ERP.",
            "retrieved_context": "Salesforce Displacement Card: Acknowledge Salesforce breadth. Differentiate on autonomous execution (OmniSales agents take action, not just store records). Offer two-way bi-directional sync with existing Salesforce setup.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Irrelevant Marketing Blog Post",
            "query": "What is our SOC2 Type II compliance audit status?",
            "retrieved_context": "Top 10 B2B Marketing Trends for 2026: Why video marketing on LinkedIn is growing 40% year-over-year.",
            "is_relevant_ground_truth": False,
        },
        {
            "name": "Relevant PipeDrive Migration Guide",
            "query": "Prospect is currently trained on PipeDrive and concerned about switching friction.",
            "retrieved_context": "PipeDrive Migration Guide: We offer automated 1-click CSV and API migration mapping all pipeline stages, custom fields, and contact histories in under 15 minutes.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Relevant HubSpot Comparison Card",
            "query": "Prospect comparing OmniSales with HubSpot Enterprise marketing hub.",
            "retrieved_context": "HubSpot Battle Card: HubSpot is strong for inbound content marketing. OmniSales leads on autonomous outbound prospecting, real-time objection closing, and churn prevention.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Irrelevant Password Reset Guide",
            "query": "Can we offer 99.999% SLA and 15-minute response time?",
            "retrieved_context": "IT Helpdesk: To reset your Google Workspace password, visit the SSO portal and enter your 2FA verification code.",
            "is_relevant_ground_truth": False,
        },
        {
            "name": "Relevant Commercial Governance Policy",
            "query": "Can we offer Net 90 payment terms to an enterprise deal?",
            "retrieved_context": "Deal Desk Policy Manual: Standard payment terms are Annual Upfront Net 30. Net 60 allowed for >=$50k ARR. Net 90/120 terms are strictly prohibited without CFO Board approval.",
            "is_relevant_ground_truth": True,
        },
        {
            "name": "Irrelevant Cafeteria Menu",
            "query": "How to handle budget freeze objection from CFO?",
            "retrieved_context": "Weekly Lunch Menu: Tuesday taco bar, Wednesday curry bowls, Thursday artisan sandwiches, Friday pizza.",
            "is_relevant_ground_truth": False,
        },
    ]

    faithfulness_passed = 0
    relevance_passed = 0
    judge_errors = 0

    print(f"\n[RAG Evals] Running OpenEvals Faithfulness (10 cases) and Context Relevance (10 cases)...")

    # Run Groundedness Judge
    for tc in faithfulness_test_cases:
        time.sleep(0.5)
        try:
            res = groundedness_judge(
                context=tc["context"],
                outputs=tc["draft"],
            )
            score_val = res.get("score")
            is_faithful = bool(score_val is True or score_val == 1.0)
            tc["judge_score"] = 1.0 if is_faithful else 0.0
            tc["judge_feedback"] = str(res.get("comment", ""))[:150]
            tc["passed"] = (is_faithful == tc["is_faithful_ground_truth"])
            if tc["passed"]:
                faithfulness_passed += 1
            print(f"  Groundedness [{tc['name']}]: Faithful={is_faithful} (Expected={tc['is_faithful_ground_truth']}, Match={tc['passed']})")
        except Exception as e:
            judge_errors += 1
            tc["judge_score"] = 0.0
            tc["judge_error"] = repr(e)[:150]
            tc["passed"] = False
            logger.error("Groundedness LLM judge failed on '%s': %s", tc["name"], e)
            print(f"  [ERROR] Groundedness Judge Failed [{tc['name']}]: {repr(e)[:100]}")

    # Run Context Relevance Judge
    for tc in relevance_test_cases:
        time.sleep(0.5)
        try:
            res = relevance_judge(
                inputs=tc["query"],
                context=tc["retrieved_context"],
            )
            score_val = res.get("score")
            is_relevant = bool(score_val is True or score_val == 1.0)
            tc["judge_score"] = 1.0 if is_relevant else 0.0
            tc["judge_feedback"] = str(res.get("comment", ""))[:150]
            tc["passed"] = (is_relevant == tc["is_relevant_ground_truth"])
            if tc["passed"]:
                relevance_passed += 1
            print(f"  Relevance    [{tc['name']}]: Relevant={is_relevant} (Expected={tc['is_relevant_ground_truth']}, Match={tc['passed']})")
        except Exception as e:
            judge_errors += 1
            tc["judge_score"] = 0.0
            tc["judge_error"] = repr(e)[:150]
            tc["passed"] = False
            logger.error("Relevance LLM judge failed on '%s': %s", tc["name"], e)
            print(f"  [ERROR] Relevance Judge Failed [{tc['name']}]: {repr(e)[:100]}")

    f_rate = (faithfulness_passed / len(faithfulness_test_cases)) * 100.0
    r_rate = (relevance_passed / len(relevance_test_cases)) * 100.0

    report = {
        "faithfulness_accuracy_pct": round(f_rate, 2),
        "context_relevance_accuracy_pct": round(r_rate, 2),
        "judge_errors_count": judge_errors,
        "faithfulness_cases": faithfulness_test_cases,
        "relevance_cases": relevance_test_cases,
    }

    print(f"\n  Faithfulness Accuracy:      {f_rate:.1f}% ({faithfulness_passed}/{len(faithfulness_test_cases)})")
    print(f"  Context Relevance Accuracy: {r_rate:.1f}% ({relevance_passed}/{len(relevance_test_cases)})")
    if judge_errors > 0:
        print(f"  [WARNING] LLM Judge Errors: {judge_errors}")

    return report


if __name__ == "__main__":
    evaluate_rag_faithfulness_and_relevance()
