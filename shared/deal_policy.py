"""Deal Desk Commercial Governance & Policy Engine.

Evaluates proposed B2B SaaS deal terms against deterministic corporate policy:
- Discount limits by contract length and payment frequency
- Payment term eligibility (Annual Upfront, Net 30, Net 60, Prohibited Net 90)
- Custom SLA eligibility by plan tier and ARR
- Prompt injection protection in deal notes
- Mathematical counter-proposal generation for policy-violating deals
"""

from __future__ import annotations

import re
import logging
import unicodedata
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Corporate Commercial Policy Rules ──

POLICY_RULES = {
    "version": "2026.1",
    "max_standard_discount_pct": 15.0,     # Auto-cleared for 12+ month contracts
    "max_extended_discount_pct": 30.0,     # Allowed for 24+ month contracts with annual upfront
    "hard_max_discount_pct": 30.0,         # Absolute limit without executive board approval
    "min_contract_months_for_discount": 12,
    "net_30_min_arr": 20000.0,             # Net 30 requires at least $20k ARR
    "net_60_min_arr": 50000.0,             # Net 60 requires at least $50k ARR and <= 10% discount
    "net_60_max_discount_pct": 10.0,
    "custom_sla_min_arr": 50000.0,         # Custom SLA requires Enterprise tier or >= $50k ARR
    "custom_sla_allowed_tiers": ["enterprise"],
    "allowed_payment_terms": [
        "annual_upfront",
        "quarterly_upfront",
        "net_30",
        "net_60",
        "monthly",
    ],
    "prohibited_payment_terms": ["net_90", "net_120"],
}

# Prompt injection signatures in free-form deal notes (adversarially hardened)
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|preceding)\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(deal\s+desk\s+|corporate\s+)?policy", re.IGNORECASE),
    re.compile(r"please\s+disregard\s+(all\s+)?(previous|prior|preceding|rules|guidelines)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|preceding|rules|instructions)", re.IGNORECASE),
    re.compile(r"act\s+as\s+if\s+(you\s+have|there\s+is)\s+no\s+policy", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?(deal\s+desk|policy|rules|guardrails)", re.IGNORECASE),
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"(approve|grant)\s+(\d{2,3}%\s+)?discount\s+unconditionally", re.IGNORECASE),
    re.compile(r"i\s+am\s+(the\s+)?(ceo|vp|executive|admin)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
]


def check_prompt_injection(text: str | None) -> str | None:
    """Check text for known prompt injection / policy override attack signatures with Unicode normalization."""
    if not text:
        return None
    # Normalize unicode to strip combining diacritics / homoglyph variations
    norm_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text) or pattern.search(norm_text)
        if match:
            return match.group(0)
    return None


def generate_counter_proposal(terms: dict[str, Any], violations: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate mathematically and commercially compliant alternative deal terms."""
    raw_arr = terms.get("arr")
    arr = 50000.0 if raw_arr is None else float(raw_arr)
    raw_disc = terms.get("discount_pct")
    discount_pct = 0.0 if raw_disc is None else float(raw_disc)
    raw_months = terms.get("contract_months")
    contract_months = 12 if raw_months is None else int(raw_months)
    payment_terms = str(terms.get("payment_terms") or "annual_upfront").lower()
    tier = str(terms.get("tier") or "growth").lower()
    custom_sla = bool(terms.get("custom_sla", False))

    counter_discount = discount_pct
    counter_months = contract_months
    counter_payment = payment_terms
    counter_tier = tier
    counter_sla = custom_sla
    explanations = []

    violation_codes = {v.get("code") for v in violations}

    # 1. Address excessive discount
    if "EXCESSIVE_DISCOUNT" in violation_codes or "PROHIBITED_DISCOUNT" in violation_codes:
        if discount_pct > POLICY_RULES["hard_max_discount_pct"]:
            counter_discount = POLICY_RULES["max_extended_discount_pct"]
            counter_months = max(contract_months, 24)
            counter_payment = "annual_upfront"
            explanations.append(
                f"Discount capped at {counter_discount:.0f}% on a {counter_months}-month contract with Annual Upfront payment."
            )
        elif discount_pct > POLICY_RULES["max_standard_discount_pct"]:
            if contract_months < 24:
                counter_months = 24
                counter_payment = "annual_upfront"
                explanations.append(
                    f"To maintain {discount_pct:.0f}% discount, contract length must be extended to 24 months with Annual Upfront payment."
                )

    # 2. Address discount on short contract
    if "DISCOUNT_SHORT_CONTRACT" in violation_codes:
        if contract_months < POLICY_RULES["min_contract_months_for_discount"]:
            counter_months = POLICY_RULES["min_contract_months_for_discount"]
            explanations.append(
                f"To qualify for {discount_pct:.0f}% discount, contract duration extended to standard {counter_months} months."
            )

    # 3. Address prohibited or ineligible payment terms
    if "PROHIBITED_PAYMENT_TERMS" in violation_codes or "INELIGIBLE_PAYMENT_TERMS" in violation_codes or "DISCOUNT_PAYMENT_MISMATCH" in violation_codes:
        if counter_discount > POLICY_RULES["max_standard_discount_pct"]:
            counter_payment = "annual_upfront"
            explanations.append(
                f"Discounts > {POLICY_RULES['max_standard_discount_pct']:.0f}% require Annual Upfront payment."
            )
        elif payment_terms in POLICY_RULES["prohibited_payment_terms"]:
            counter_payment = "net_30" if arr >= POLICY_RULES["net_30_min_arr"] else "annual_upfront"
            explanations.append(
                f"Prohibited '{payment_terms}' payment terms adjusted to compliant '{counter_payment}'."
            )
        elif payment_terms == "net_60":
            if arr < POLICY_RULES["net_60_min_arr"] or discount_pct > POLICY_RULES["net_60_max_discount_pct"]:
                counter_payment = "net_30" if arr >= POLICY_RULES["net_30_min_arr"] else "annual_upfront"
                explanations.append(
                    f"Net 60 terms require ARR >= $50k and discount <= 10%. Adjusted to '{counter_payment}'."
                )

    # Ensure high discount always pairs with upfront payment
    if counter_discount > POLICY_RULES["max_standard_discount_pct"] and counter_payment not in ("annual_upfront", "quarterly_upfront"):
        counter_payment = "annual_upfront"

    # 4. Address custom SLA violation
    if "CUSTOM_SLA_INELIGIBLE" in violation_codes:
        counter_tier = "enterprise"
        counter_sla = True
        explanations.append(
            "Custom SLA requires Enterprise Tier. Upgraded plan tier to Enterprise."
        )

    # Compute financial impact
    effective_arr = max(arr * (1.0 - (counter_discount / 100.0)), 100.0)
    total_contract_value = effective_arr * (counter_months / 12.0)
    annual_savings = (arr * (counter_discount / 100.0))

    return {
        "proposed_discount_pct": round(counter_discount, 2),
        "proposed_contract_months": counter_months,
        "proposed_payment_terms": counter_payment,
        "proposed_tier": counter_tier,
        "proposed_custom_sla": counter_sla,
        "base_arr": round(arr, 2),
        "discounted_arr": round(effective_arr, 2),
        "total_contract_value": round(total_contract_value, 2),
        "customer_annual_savings": round(annual_savings, 2),
        "explanation": " ".join(explanations) if explanations else "Standard commercial terms applied.",
    }


def evaluate_deal_terms(
    deal: dict[str, Any],
    override: bool = False,
    override_reason: str = "",
) -> dict[str, Any]:
    """Evaluate commercial deal terms against corporate Deal Desk policy.

    Returns structured evaluation with status ('approved', 'policy_violation', 'overridden'),
    detailed violations, and a compliant counter-proposal.
    """
    violations: list[dict[str, Any]] = []

    # Extract terms
    raw_arr = deal.get("arr")
    arr = 0.0 if raw_arr is None else float(raw_arr)
    raw_disc = deal.get("discount_pct")
    discount_pct = 0.0 if raw_disc is None else float(raw_disc)
    raw_months = deal.get("contract_months")
    contract_months = 12 if raw_months is None else int(raw_months)
    payment_terms = str(deal.get("payment_terms") or "annual_upfront").lower().strip()
    tier = str(deal.get("tier") or "growth").lower().strip()
    custom_sla = bool(deal.get("custom_sla", False))
    notes = str(deal.get("notes") or deal.get("reasoning") or "")

    # ── Rule 1: ARR Guardrail ──
    if arr <= 0:
        violations.append({
            "code": "INVALID_ARR",
            "field": "arr",
            "message": f"ARR must be greater than $0. Received ${arr:,.2f}.",
            "severity": "critical",
        })
    elif arr > 10_000_000:
        violations.append({
            "code": "EXCESSIVE_ARR",
            "field": "arr",
            "message": f"Deals exceeding $10,000,000 ARR require custom executive committee review.",
            "severity": "critical",
        })

    # ── Rule 2: Contract Duration Guardrail ──
    if contract_months <= 0:
        violations.append({
            "code": "INVALID_CONTRACT_MONTHS",
            "field": "contract_months",
            "message": f"Contract duration must be at least 1 month. Received {contract_months} months.",
            "severity": "critical",
        })

    # ── Rule 3: Discount Policy ──
    if discount_pct < 0:
        violations.append({
            "code": "NEGATIVE_DISCOUNT",
            "field": "discount_pct",
            "message": f"Discount percentage cannot be negative. Received {discount_pct}%.",
            "severity": "critical",
        })
    elif discount_pct > POLICY_RULES["hard_max_discount_pct"]:
        violations.append({
            "code": "PROHIBITED_DISCOUNT",
            "field": "discount_pct",
            "message": f"Proposed discount of {discount_pct:.1f}% exceeds absolute limit of {POLICY_RULES['hard_max_discount_pct']}%.",
            "severity": "critical",
        })
    elif discount_pct > POLICY_RULES["max_standard_discount_pct"]:
        # 16% to 30% discount requires 24+ months and annual upfront
        if contract_months < 24:
            violations.append({
                "code": "EXCESSIVE_DISCOUNT",
                "field": "discount_pct",
                "message": f"Discount of {discount_pct:.1f}% requires a minimum 24-month contract (currently {contract_months} months).",
                "severity": "high",
            })
        if payment_terms not in ("annual_upfront", "quarterly_upfront"):
            violations.append({
                "code": "DISCOUNT_PAYMENT_MISMATCH",
                "field": "payment_terms",
                "message": f"Discount of {discount_pct:.1f}% requires Annual or Quarterly Upfront payment (currently '{payment_terms}').",
                "severity": "high",
            })
    elif discount_pct > 0 and contract_months < POLICY_RULES["min_contract_months_for_discount"]:
        violations.append({
            "code": "DISCOUNT_SHORT_CONTRACT",
            "field": "discount_pct",
            "message": f"Discounts > 0% require at least 12-month contract duration. Month-to-month contracts cannot receive discounts.",
            "severity": "high",
        })

    # ── Rule 4: Payment Terms Policy ──
    if payment_terms in POLICY_RULES["prohibited_payment_terms"]:
        violations.append({
            "code": "PROHIBITED_PAYMENT_TERMS",
            "field": "payment_terms",
            "message": f"Payment terms '{payment_terms}' are strictly prohibited for standard SaaS subscriptions.",
            "severity": "critical",
        })
    elif payment_terms == "net_60":
        if arr < POLICY_RULES["net_60_min_arr"]:
            violations.append({
                "code": "INELIGIBLE_PAYMENT_TERMS",
                "field": "payment_terms",
                "message": f"Net 60 terms require minimum ARR of ${POLICY_RULES['net_60_min_arr']:,.2f} (current ARR: ${arr:,.2f}).",
                "severity": "medium",
            })
        if discount_pct > POLICY_RULES["net_60_max_discount_pct"]:
            violations.append({
                "code": "INELIGIBLE_PAYMENT_TERMS",
                "field": "payment_terms",
                "message": f"Net 60 terms cannot be combined with discounts exceeding {POLICY_RULES['net_60_max_discount_pct']:.0f}% (current: {discount_pct:.1f}%).",
                "severity": "medium",
            })
    elif payment_terms == "net_30" and arr < POLICY_RULES["net_30_min_arr"]:
        violations.append({
            "code": "INELIGIBLE_PAYMENT_TERMS",
            "field": "payment_terms",
            "message": f"Net 30 terms require minimum ARR of ${POLICY_RULES['net_30_min_arr']:,.2f} (current ARR: ${arr:,.2f}).",
            "severity": "medium",
        })

    # ── Rule 5: Custom SLA Policy ──
    if custom_sla:
        if tier not in POLICY_RULES["custom_sla_allowed_tiers"] and arr < POLICY_RULES["custom_sla_min_arr"]:
            violations.append({
                "code": "CUSTOM_SLA_INELIGIBLE",
                "field": "custom_sla",
                "message": f"Custom SLA guarantees require Enterprise tier or ARR >= ${POLICY_RULES['custom_sla_min_arr']:,.2f} (current tier: '{tier}', ARR: ${arr:,.2f}).",
                "severity": "high",
            })

    # ── Rule 6: Prompt Injection & Security Defense ──
    injection_match = check_prompt_injection(notes)
    if injection_match:
        violations.append({
            "code": "PROMPT_INJECTION_DETECTED",
            "field": "notes",
            "message": f"Security violation: Detected policy override / prompt injection attempt ('{injection_match}') in deal notes.",
            "severity": "security_critical",
        })

    # ── Decision Resolution ──
    is_compliant = len(violations) == 0
    counter_proposal = None if is_compliant else generate_counter_proposal(deal, violations)

    if is_compliant:
        status = "approved"
    elif override and override_reason and override_reason.strip():
        # Security critical prompt injection violations cannot be overridden
        has_security_violation = any(v.get("code") == "PROMPT_INJECTION_DETECTED" for v in violations)
        if has_security_violation:
            status = "policy_violation"
        else:
            status = "overridden"
    else:
        status = "policy_violation"

    return {
        "status": status,
        "is_compliant": is_compliant,
        "violations": violations,
        "violations_count": len(violations),
        "counter_proposal": counter_proposal,
        "override_applied": status == "overridden",
        "override_reason": override_reason if status == "overridden" else None,
        "policy_version": POLICY_RULES["version"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
