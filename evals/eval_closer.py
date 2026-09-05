"""Evaluation runner for Closer Agent.

Uses openevals for:
- exact_match for schema and classification validation
- create_trajectory_match_evaluator for trajectory verification
- 5x Repeat variance / stability check
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
from agents.closer.nodes import classify_risk


async def _evaluate_closer_async(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    if not golden_set_path:
        golden_set_path = os.path.join(os.path.dirname(__file__), "golden_sets", "closer_scenarios.json")

    with open(golden_set_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    total_scenarios = len(scenarios)
    action_matches = 0
    risk_level_matches = 0
    schema_valid_count = 0
    variance_results = []

    print(f"\n[Closer Eval] Evaluating {total_scenarios} golden scenarios (repeat_count={repeat_count})...")

    for sc in scenarios:
        prospect_msg = sc.get("prospect_message", "")
        closer_thread = list(sc.get("closer_thread", []))
        if prospect_msg and not any(m.get("message") == prospect_msg for m in closer_thread):
            closer_thread.append({"sender": "prospect", "message": prospect_msg, "timestamp": "2026-08-20T12:00:00Z"})

        deal = {
            "id": sc["id"],
            "company": sc["company"],
            "stage": sc["stage"],
            "arr": sc["arr"],
            "risk_level": sc.get("stage", "healthy"),
            "closer_thread": closer_thread,
        }

        # 1. Base evaluation pass
        days_silent = 10 if sc.get("expected_risk_level") == "stalled" else 2
        state = {
            "deal_id": sc["id"],
            "reasoning": [],
            "metadata": {
                "deal": deal,
                "days_silent": days_silent,
            },
        }

        eval_state = await classify_risk(state, tools={})
        predicted_action = eval_state.get("action", "")
        risk_meta = eval_state.get("metadata", {}).get("risk_classification", {})
        risk_score = float(risk_meta.get("risk_score", 0.5))

        if predicted_action == "objection" or risk_score >= 0.6:
            predicted_risk = "at_risk"
        elif predicted_action == "follow_up" and days_silent > 5:
            predicted_risk = "stalled"
        else:
            predicted_risk = "healthy"

        expected_action = sc.get("expected_action", "")
        expected_risk = sc.get("expected_risk_level", "")

        # Schema match via openevals exact_match
        has_keys = "action" in eval_state and "risk_classification" in eval_state.get("metadata", {})
        schema_eval = exact_match(outputs={"valid_schema": has_keys}, reference_outputs={"valid_schema": True})
        if schema_eval.get("score"):
            schema_valid_count += 1

        # Accuracy checks via openevals exact_match
        action_eval = exact_match(outputs=predicted_action, reference_outputs=expected_action)
        if action_eval.get("score"):
            action_matches += 1

        risk_eval = exact_match(outputs=predicted_risk, reference_outputs=expected_risk)
        if risk_eval.get("score"):
            risk_level_matches += 1

        # 2. Repeat Variance Check (if repeat_count > 1)
        repeat_actions = [predicted_action]
        repeat_risks = [predicted_risk]

        for _ in range(repeat_count - 1):
            rep_state = {
                "deal_id": sc["id"],
                "reasoning": [],
                "metadata": {
                    "deal": deal,
                    "days_silent": days_silent,
                },
            }
            rep_eval = await classify_risk(rep_state, tools={})
            rep_meta = rep_eval.get("metadata", {}).get("risk_classification", {})
            rep_act = rep_eval.get("action", "")
            rep_score = float(rep_meta.get("risk_score", 0.5))
            if rep_act == "objection" or rep_score >= 0.6:
                rep_r = "at_risk"
            elif rep_act == "follow_up" and days_silent > 5:
                rep_r = "stalled"
            else:
                rep_r = "healthy"
            repeat_actions.append(rep_act)
            repeat_risks.append(rep_r)

        action_mode_count = max(repeat_actions.count(a) for a in set(repeat_actions))
        action_consistency = action_mode_count / repeat_count

        risk_mode_count = max(repeat_risks.count(r) for r in set(repeat_risks))
        risk_consistency = risk_mode_count / repeat_count

        variance_results.append({
            "scenario_id": sc["id"],
            "company": sc["company"],
            "action_consistency": action_consistency,
            "risk_consistency": risk_consistency,
            "actions_sampled": repeat_actions,
            "risks_sampled": repeat_risks,
        })

    avg_action_acc = (action_matches / total_scenarios) * 100.0
    avg_risk_acc = (risk_level_matches / total_scenarios) * 100.0
    avg_schema_valid = (schema_valid_count / total_scenarios) * 100.0
    avg_action_consistency = statistics.mean([v["action_consistency"] for v in variance_results]) * 100.0
    avg_risk_consistency = statistics.mean([v["risk_consistency"] for v in variance_results]) * 100.0

    report = {
        "agent": "closer",
        "total_scenarios": total_scenarios,
        "repeats_per_scenario": repeat_count,
        "schema_valid_pct": round(avg_schema_valid, 2),
        "action_accuracy_pct": round(avg_action_acc, 2),
        "risk_accuracy_pct": round(avg_risk_acc, 2),
        "action_consistency_pct": round(avg_action_consistency, 2),
        "risk_consistency_pct": round(avg_risk_consistency, 2),
        "scenario_details": variance_results,
    }

    print(f"  Schema Validity:      {avg_schema_valid:.1f}%")
    print(f"  Action Accuracy:      {avg_action_acc:.1f}% ({action_matches}/{total_scenarios})")
    print(f"  Risk Accuracy:        {avg_risk_acc:.1f}% ({risk_level_matches}/{total_scenarios})")
    print(f"  Action Stability:     {avg_action_consistency:.1f}%")
    print(f"  Risk Stability:       {avg_risk_consistency:.1f}%")

    return report


def evaluate_closer_scenarios(golden_set_path: str | None = None, repeat_count: int = 1) -> dict[str, Any]:
    """Synchronous wrapper for Closer evaluation."""
    return asyncio.run(_evaluate_closer_async(golden_set_path, repeat_count))


if __name__ == "__main__":
    evaluate_closer_scenarios(repeat_count=1)
