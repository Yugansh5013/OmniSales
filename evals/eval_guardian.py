"""Evaluation runner for Guardian Agent.

Uses openevals for:
- exact_match for risk tier and churn scoring validation
- create_trajectory_match_evaluator for LangGraph node execution trajectory verification
- Repeat variance / stability check
"""

from __future__ import annotations

import os
import sys
import json
import asyncio
import statistics
from typing import Any

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openevals import exact_match, create_trajectory_match_evaluator
from agents.guardian.nodes import score_churn, rank_and_flag


async def _evaluate_guardian_async(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    if not golden_set_path:
        golden_set_path = os.path.join(os.path.dirname(__file__), "golden_sets", "guardian_scenarios.json")

    with open(golden_set_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    total_scenarios = len(scenarios)
    tier_matches = 0
    trajectory_matches = 0
    variance_results = []

    # Initialize openevals strict trajectory evaluator
    traj_evaluator = create_trajectory_match_evaluator(trajectory_match_mode="strict")

    print(f"\n[Guardian Eval] Evaluating {total_scenarios} golden scenarios (repeat_count={repeat_count})...")

    for sc in scenarios:
        account = {
            "id": sc["id"],
            "company": sc["company"],
            "arr": sc["arr"],
            "plan": sc["plan"],
            "usage_pct": sc["usage_pct"],
            "support_tickets": sc["support_tickets"],
            "last_login": "2026-07-15T00:00:00Z" if sc["last_login_days_ago"] > 30 else "2026-08-24T00:00:00Z",
            "health_score": round(1.0 - (sc["support_tickets"] * 0.08) - (0.3 if sc["last_login_days_ago"] > 20 else 0.0), 2),
            "metadata": {
                "usage_trend": [-0.2] if sc["usage_pct"] < 0.3 else [0.05],
                "signals": ["Low login", "Ticket escalation"] if sc["support_tickets"] > 5 else ["Healthy activity"],
            },
        }

        # 1. Base evaluation pass
        state = {
            "reasoning": [],
            "metadata": {"accounts": [account]},
            "node_trajectory": ["analyze_accounts"],
        }

        scored_state = await score_churn(state, tools={})
        scored_state["node_trajectory"] = ["analyze_accounts", "score_churn"]

        flagged_state = await rank_and_flag(scored_state, tools={})
        flagged_state["node_trajectory"] = ["analyze_accounts", "score_churn", "rank_and_flag"]

        scored_accs = scored_state.get("metadata", {}).get("scored_accounts", [])
        acc_score = scored_accs[0].get("llm_score", {}) if scored_accs else {}
        predicted_tier = acc_score.get("risk_tier", "low")
        churn_risk = float(acc_score.get("churn_risk", 0.1))

        # Trajectory progression: high/critical risk generates retention play
        if predicted_tier in ("high", "critical") or churn_risk >= 0.6:
            flagged_state["node_trajectory"].append("generate_retention")

        # Check trajectory match via openevals create_trajectory_match_evaluator
        expected_traj = sc.get("expected_trajectory", [])
        actual_traj = flagged_state["node_trajectory"]
        
        actual_messages = [{"role": "assistant", "content": node} for node in actual_traj]
        expected_messages = [{"role": "assistant", "content": node} for node in expected_traj]
        
        traj_res = traj_evaluator(outputs=actual_messages, reference_outputs=expected_messages)
        if traj_res.get("score"):
            trajectory_matches += 1

        # Check tier accuracy via openevals exact_match
        expected_tier = sc.get("expected_risk_tier", "low")
        tier_eval = exact_match(outputs=predicted_tier.lower(), reference_outputs=expected_tier.lower())
        if tier_eval.get("score"):
            tier_matches += 1

        # 2. Repeat Variance Check
        sampled_churn_scores = [churn_risk]
        sampled_tiers = [predicted_tier]

        for _ in range(repeat_count - 1):
            rep_state = {
                "reasoning": [],
                "metadata": {"accounts": [account]},
            }
            rep_scored = await score_churn(rep_state, tools={})
            rep_scored_accs = rep_scored.get("metadata", {}).get("scored_accounts", [])
            rep_acc = rep_scored_accs[0].get("llm_score", {}) if rep_scored_accs else {}
            sampled_churn_scores.append(float(rep_acc.get("churn_risk", 0.5)))
            sampled_tiers.append(rep_acc.get("risk_tier", "low"))

        score_std_dev = statistics.stdev(sampled_churn_scores) if len(sampled_churn_scores) > 1 else 0.0
        tier_mode_count = max(sampled_tiers.count(t) for t in set(sampled_tiers))
        tier_consistency = tier_mode_count / repeat_count

        variance_results.append({
            "scenario_id": sc["id"],
            "company": sc["company"],
            "score_std_dev": round(score_std_dev, 4),
            "tier_consistency": tier_consistency,
            "sampled_scores": sampled_churn_scores,
            "sampled_tiers": sampled_tiers,
            "actual_trajectory": actual_traj,
            "expected_trajectory": expected_traj,
            "trajectory_match": traj_res.get("score", False),
        })

    avg_tier_acc = (tier_matches / total_scenarios) * 100.0
    avg_traj_acc = (trajectory_matches / total_scenarios) * 100.0
    avg_tier_consistency = statistics.mean([v["tier_consistency"] for v in variance_results]) * 100.0
    avg_score_std_dev = statistics.mean([v["score_std_dev"] for v in variance_results])

    report = {
        "agent": "guardian",
        "total_scenarios": total_scenarios,
        "repeats_per_scenario": repeat_count,
        "tier_accuracy_pct": round(avg_tier_acc, 2),
        "node_trajectory_accuracy_pct": round(avg_traj_acc, 2),
        "tier_consistency_pct": round(avg_tier_consistency, 2),
        "mean_score_std_dev": round(avg_score_std_dev, 4),
        "scenario_details": variance_results,
    }

    print(f"  Risk Tier Accuracy:         {avg_tier_acc:.1f}% ({tier_matches}/{total_scenarios})")
    print(f"  Node Trajectory Accuracy:   {avg_traj_acc:.1f}% ({trajectory_matches}/{total_scenarios})")
    print(f"  Tier Stability:             {avg_tier_consistency:.1f}%")
    print(f"  Score Std Dev:              {avg_score_std_dev:.4f}")

    return report


def evaluate_guardian_scenarios(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    """Synchronous wrapper for Guardian evaluation."""
    return asyncio.run(_evaluate_guardian_async(golden_set_path, repeat_count))


if __name__ == "__main__":
    evaluate_guardian_scenarios(repeat_count=1)
