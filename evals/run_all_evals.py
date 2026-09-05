"""Master CLI Runner for OmniSales Evaluation Suite.

Executes:
1. Closer Golden Set Eval (25 scenarios, exact_match, trajectory, variance)
2. Guardian Golden Set Eval (20 scenarios, tier accuracy, node trajectory, variance)
3. Prospector Golden Set Eval (20 scenarios, ICP accuracy, sequence routing, variance)
4. RAG Faithfulness & Context Relevance Eval (openevals LLM-as-judge, 10+10 cases)
5. Generates consolidated evals/eval_report.json
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import datetime, timezone

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evals.eval_closer import evaluate_closer_scenarios
from evals.eval_guardian import evaluate_guardian_scenarios
from evals.eval_prospector import evaluate_prospector_scenarios
from evals.eval_rag_faithfulness import evaluate_rag_faithfulness_and_relevance


def run_full_evaluation_suite(repeat_count: int = 1, agent: str | None = None, skip_rag: bool = False) -> dict:
    """Execute all agent and RAG evaluations."""
    start_time = datetime.now(timezone.utc)
    print("=" * 75)
    print("  OmniSales Enterprise Agent Evaluation & Reliability Suite")
    print("  Framework: OpenEvals + LangSmith Golden Sets")
    print(f"  Configuration: repeats={repeat_count} | agent={agent or 'all'} | skip_rag={skip_rag}")
    print(f"  Started: {start_time.isoformat()}")
    print("=" * 75)

    closer_report = {}
    guardian_report = {}
    prospector_report = {}
    rag_report = {}

    # 1. Closer Evaluation
    if not agent or agent == "closer":
        closer_report = evaluate_closer_scenarios(repeat_count=repeat_count)

    # 2. Guardian Evaluation
    if not agent or agent == "guardian":
        guardian_report = evaluate_guardian_scenarios(repeat_count=repeat_count)

    # 3. Prospector Evaluation
    if not agent or agent == "prospector":
        prospector_report = evaluate_prospector_scenarios(repeat_count=repeat_count)

    # 4. RAG Faithfulness & Relevance
    if not skip_rag and (not agent or agent == "rag"):
        rag_report = evaluate_rag_faithfulness_and_relevance()

    end_time = datetime.now(timezone.utc)
    duration_s = round((end_time - start_time).total_seconds(), 2)

    report_path = os.path.join(os.path.dirname(__file__), "eval_report.json")
    consolidated_report = {}
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                consolidated_report = json.load(f)
        except Exception:
            consolidated_report = {}

    if not consolidated_report:
        consolidated_report = {
            "suite_version": "2026.1",
            "summary": {},
        }

    consolidated_report["generated_at"] = end_time.isoformat()
    consolidated_report["duration_seconds"] = duration_s
    consolidated_report["repeats_per_scenario"] = repeat_count

    summary = consolidated_report.get("summary", {})
    if closer_report:
        summary["closer_action_accuracy_pct"] = closer_report.get("action_accuracy_pct", 0)
        summary["closer_stability_pct"] = closer_report.get("action_consistency_pct", 0)
        consolidated_report["closer"] = closer_report
    if guardian_report:
        summary["guardian_tier_accuracy_pct"] = guardian_report.get("tier_accuracy_pct", 0)
        summary["guardian_trajectory_accuracy_pct"] = guardian_report.get("node_trajectory_accuracy_pct", 0)
        consolidated_report["guardian"] = guardian_report
    if prospector_report:
        summary["prospector_tier_accuracy_pct"] = prospector_report.get("tier_accuracy_pct", 0)
        summary["prospector_trajectory_accuracy_pct"] = prospector_report.get("trajectory_accuracy_pct", 0)
        consolidated_report["prospector"] = prospector_report
    if rag_report:
        summary["rag_faithfulness_pct"] = rag_report.get("faithfulness_accuracy_pct", 0)
        summary["rag_context_relevance_pct"] = rag_report.get("context_relevance_accuracy_pct", 0)
        consolidated_report["rag"] = rag_report

    consolidated_report["summary"] = summary

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(consolidated_report, f, indent=2)

    print("\n" + "=" * 75)
    print(f"  Evaluation Suite Completed in {duration_s}s")
    print("=" * 75)
    if closer_report:
        print(f"  Closer Action Accuracy:        {closer_report.get('action_accuracy_pct')}% (Stability: {closer_report.get('action_consistency_pct')}%)")
    if guardian_report:
        print(f"  Guardian Tier Accuracy:        {guardian_report.get('tier_accuracy_pct')}% (Trajectory Match: {guardian_report.get('node_trajectory_accuracy_pct')}%)")
    if prospector_report:
        print(f"  Prospector Tier Accuracy:      {prospector_report.get('tier_accuracy_pct')}% (Trajectory Match: {prospector_report.get('trajectory_accuracy_pct')}%)")
    if rag_report:
        print(f"  RAG Draft Faithfulness:        {rag_report.get('faithfulness_accuracy_pct')}%")
        print(f"  RAG Context Relevance:         {rag_report.get('context_relevance_accuracy_pct')}%")
    print("=" * 75)
    print(f"  Detailed JSON report written to {report_path}\n")

    return consolidated_report


def main():
    parser = argparse.ArgumentParser(description="OmniSales OpenEvals Master Suite")
    parser.add_argument("--repeats", type=int, default=1, help="Repeats per scenario for variance testing (default: 1)")
    parser.add_argument("--agent", choices=["closer", "guardian", "prospector", "rag"], default=None, help="Run specific agent eval")
    parser.add_argument("--skip-rag", action="store_true", help="Skip RAG LLM-as-judge tests")
    args = parser.parse_args()

    run_full_evaluation_suite(repeat_count=args.repeats, agent=args.agent, skip_rag=args.skip_rag)


if __name__ == "__main__":
    main()
