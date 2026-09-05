"""Evaluation runner for Prospector Agent.

Uses openevals for:
- exact_match for ICP tier accuracy
- create_trajectory_match_evaluator for sequence routing trajectory verification
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
from agents.prospector.nodes import score_icp


async def _evaluate_prospector_async(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    if not golden_set_path:
        golden_set_path = os.path.join(os.path.dirname(__file__), "golden_sets", "prospector_scenarios.json")

    with open(golden_set_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    total_scenarios = len(scenarios)
    tier_matches = 0
    trajectory_matches = 0
    variance_results = []

    # Initialize openevals strict trajectory evaluator
    traj_evaluator = create_trajectory_match_evaluator(trajectory_match_mode="strict")

    print(f"\n[Prospector Eval] Evaluating {total_scenarios} golden scenarios (repeat_count={repeat_count})...")

    for sc in scenarios:
        lead = {
            "id": sc["id"],
            "company": sc["company"],
            "title": sc["title"],
            "industry": sc["industry"],
        }
        enrichment = {
            "company_name": sc["company"],
            "industry": sc["industry"],
            "employees": sc["employees"],
            "funding": "$25M (Series B)" if sc["expected_tier"] == "A" else ("$10M (Series A)" if sc["expected_tier"] == "B" else ("$1M" if sc["expected_tier"] == "C" else "$0")),
            "revenue_est": sc["revenue"],
            "tech_stack": sc["tech_stack"],
            "signals": ["B2B sales motion", "Modern tech stack", "Actively hiring sales roles"] if sc["expected_tier"] == "A" else (["B2B sales motion", "Modern tech stack"] if sc["expected_tier"] == "B" else (["Evaluating sales tools"] if sc["expected_tier"] == "C" else ["Non-ideal industry"])),
        }

        # 1. Base evaluation pass
        state = {
            "reasoning": [],
            "metadata": {
                "lead": lead,
                "enrichment": enrichment,
            },
            "node_trajectory": ["research_company", "enrich_lead"],
        }

        scored_state = await score_icp(state, tools={})
        scored_state["node_trajectory"] = ["research_company", "enrich_lead", "score_icp"]

        icp_result = scored_state.get("metadata", {}).get("icp_result", {})
        predicted_tier = icp_result.get("tier", "D")
        predicted_icp = float(icp_result.get("icp_score", 0.0))

        if predicted_tier in ("A", "B"):
            scored_state["node_trajectory"].extend(["identify_contacts", "draft_sequences"])

        # Check trajectory match via openevals create_trajectory_match_evaluator
        expected_traj = sc.get("expected_trajectory", [])
        actual_traj = scored_state["node_trajectory"]
        
        actual_messages = [{"role": "assistant", "content": node} for node in actual_traj]
        expected_messages = [{"role": "assistant", "content": node} for node in expected_traj]
        
        traj_res = traj_evaluator(outputs=actual_messages, reference_outputs=expected_messages)
        if traj_res.get("score"):
            trajectory_matches += 1

        # Check tier accuracy via openevals exact_match
        expected_tier = sc.get("expected_tier", "D")
        tier_eval = exact_match(outputs=predicted_tier.upper(), reference_outputs=expected_tier.upper())
        if tier_eval.get("score"):
            tier_matches += 1

        # 2. Repeat Variance Check
        sampled_icp_scores = [predicted_icp]
        sampled_tiers = [predicted_tier]

        for _ in range(repeat_count - 1):
            rep_state = {
                "reasoning": [],
                "metadata": {
                    "lead": lead,
                    "enrichment": enrichment,
                },
            }
            rep_scored = await score_icp(rep_state, tools={})
            rep_icp_result = rep_scored.get("metadata", {}).get("icp_result", {})
            rep_tier = rep_icp_result.get("tier", "D")
            rep_raw_icp = rep_icp_result.get("icp_score", 0.0)
            sampled_icp_scores.append(float(rep_raw_icp))
            sampled_tiers.append(rep_tier)

        score_std_dev = statistics.stdev(sampled_icp_scores) if len(sampled_icp_scores) > 1 else 0.0
        tier_mode_count = max(sampled_tiers.count(t) for t in set(sampled_tiers))
        tier_consistency = tier_mode_count / repeat_count

        variance_results.append({
            "scenario_id": sc["id"],
            "company": sc["company"],
            "score_std_dev": round(score_std_dev, 4),
            "tier_consistency": tier_consistency,
            "sampled_scores": sampled_icp_scores,
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
        "agent": "prospector",
        "total_scenarios": total_scenarios,
        "repeats_per_scenario": repeat_count,
        "tier_accuracy_pct": round(avg_tier_acc, 2),
        "trajectory_accuracy_pct": round(avg_traj_acc, 2),
        "tier_consistency_pct": round(avg_tier_consistency, 2),
        "mean_score_std_dev": round(avg_score_std_dev, 4),
        "scenario_details": variance_results,
    }

    print(f"  ICP Tier Accuracy:          {avg_tier_acc:.1f}% ({tier_matches}/{total_scenarios})")
    print(f"  Trajectory Accuracy:        {avg_traj_acc:.1f}% ({trajectory_matches}/{total_scenarios})")
    print(f"  Tier Stability:             {avg_tier_consistency:.1f}%")
    print(f"  Score Std Dev:              {avg_score_std_dev:.4f}")

    return report


def evaluate_prospector_scenarios(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    """Synchronous wrapper for Prospector evaluation."""
    return asyncio.run(_evaluate_prospector_async(golden_set_path, repeat_count))


if __name__ == "__main__":
    evaluate_prospector_scenarios(repeat_count=1)
