"""Authored, versioned contracts for the configurable testing desk.

The catalogue is deliberately a bounded provider/quote boundary.  It describes
provider capabilities and produces deterministic quotes; the selected provider
and price are now frozen on an explicit manual screening case, but the
compatibility screening resolver still owns the result.  It does not decide a
proven violation, confirmation, appeal or sanction.  Those mechanics remain
owned by the later J5 case/confirmation implementation.
"""

from copy import deepcopy
import math


CATALOGUE_SCHEMA_VERSION = 1


SCREENING_RESULT_DEFINITIONS = {
    "preliminary_positive": {
        "label": "Preliminary alert",
        "status": "Preliminary review",
        "closed": False,
        "review_required": True,
        "note": "Preliminary evidence only; it does not prove a violation.",
    },
    "negative": {
        "label": "Negative screen",
        "status": "Closed negative",
        "closed": True,
        "review_required": False,
        "note": "No alert was recorded; no injury, violation or sanction is implied.",
    },
    "inconclusive": {
        "label": "Inconclusive screen",
        "status": "Inconclusive review",
        "closed": False,
        "review_required": True,
        "note": "The retained sample did not support a definitive result; confirmation and resample rules are not enabled.",
    },
    "invalid": {
        "label": "Invalid sample",
        "status": "Invalid sample",
        "closed": False,
        "review_required": True,
        "note": "The retained sample could not be used for a definitive result; no finding is inferred.",
    },
}


def normalize_screening_result(value):
    """Return one explicit, non-inferential retained screening result."""

    wanted = str(value or "").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "positive": "preliminary_positive",
        "preliminary_positive": "preliminary_positive",
        "alert": "preliminary_positive",
        "negative": "negative",
        "clear": "negative",
        "inconclusive": "inconclusive",
        "indeterminate": "inconclusive",
        "invalid": "invalid",
        "invalid_sample": "invalid",
        "rejected_sample": "invalid",
    }
    return aliases.get(wanted, "invalid")


def screening_result_definition(value):
    """Return a defensive display contract for one screening result."""

    return deepcopy(SCREENING_RESULT_DEFINITIONS.get(
        normalize_screening_result(value), SCREENING_RESULT_DEFINITIONS["invalid"],
    ))


def saved_screening_result(case):
    """Project a retained case result without rewriting legacy evidence."""

    row = case if isinstance(case, dict) else {}
    raw = row.get("preliminary_result")
    if raw is None or not str(raw or "").strip():
        status = str(row.get("status", "") or "").strip()
        if status == "Closed negative":
            return "negative"
        if status == "Preliminary review":
            return "preliminary_positive"
        return "invalid"
    return normalize_screening_result(raw)


_PROVIDERS = (
    {
        "provider_id": "legacy-promotion-testing",
        "name": "Promotion Testing Desk",
        "tier": "Baseline",
        "effectiveness": "Existing screening basis",
        "coverage": "Up to six roster samples",
        "turnaround": "Standard review window",
        "cost_multiplier": 1.00,
        "supported_tests": ("Standard panel",),
        "confirmation": "Not enabled in the current case slice",
        "false_positive_handling": "Preliminary review only",
        "notes": "Compatibility provider for existing saves and the current screening resolver.",
    },
    {
        "provider_id": "regional-integrity-labs",
        "name": "Regional Integrity Labs",
        "tier": "Enhanced",
        "effectiveness": "Enhanced screening service",
        "coverage": "Broader panel and capacity",
        "turnaround": "Shorter review window",
        "cost_multiplier": 1.25,
        "supported_tests": ("Standard panel", "Enhanced panel"),
        "confirmation": "Provider comparison only until J5 confirmation rules are enabled",
        "false_positive_handling": "Explicit review required",
        "notes": "A planning option; selecting it does not yet alter live screening outcomes.",
    },
    {
        "provider_id": "national-compliance-network",
        "name": "National Compliance Network",
        "tier": "Premium",
        "effectiveness": "Highest authored screening tier",
        "coverage": "Maximum panel and capacity",
        "turnaround": "Priority review window",
        "cost_multiplier": 1.50,
        "supported_tests": ("Standard panel", "Enhanced panel", "Confirmation panel"),
        "confirmation": "Provider comparison only until J5 confirmation rules are enabled",
        "false_positive_handling": "Independent confirmation planned",
        "notes": "The premium planning option costs more for broader service; no guarantee is implied.",
    },
)


_POLICIES = (
    {
        "policy_id": "None",
        "name": "Off",
        "strictness": "Disabled",
        "coverage": "No samples",
        "confirmation": "No case workflow",
        "description": "Testing is disabled. No samples, charges or test rolls are created.",
    },
    {
        "policy_id": "Standard",
        "name": "Standard",
        "strictness": "Routine",
        "coverage": "Current standard roster sample",
        "confirmation": "Preliminary review only in the current slice",
        "description": "The compatibility default for ordinary promotion screening.",
    },
    {
        "policy_id": "Strict",
        "name": "Strict",
        "strictness": "High",
        "coverage": "Higher scrutiny setting",
        "confirmation": "Confirmation policy is not yet enabled",
        "description": "A stricter planning setting; exact frequency and sanction rules are still gated.",
    },
    {
        "policy_id": "Olympic",
        "name": "Olympic",
        "strictness": "Highest",
        "coverage": "Maximum scrutiny setting",
        "confirmation": "Confirmation policy is not yet enabled",
        "description": "The most rigorous authored planning preset; it does not guarantee a finding.",
    },
)


def provider_catalogue():
    """Return defensive provider rows in stable authored order."""

    return deepcopy(list(_PROVIDERS))


def policy_catalogue():
    """Return defensive policy rows in stable authored order."""

    return deepcopy(list(_POLICIES))


def provider_by_id(provider_id):
    wanted = str(provider_id or "")
    return deepcopy(next((row for row in _PROVIDERS if row["provider_id"] == wanted), _PROVIDERS[0]))


def policy_by_id(policy_id):
    wanted = str(policy_id or "")
    match = next((row for row in _POLICIES if row["policy_id"] == wanted), None)
    if match is not None:
        return deepcopy(match)
    # Some seeded AI promotions use the pre-catalogue ``Enhanced`` label.  It
    # remains a readable legacy preset rather than being silently relabelled as
    # Standard; no new player-facing option or live mechanic is implied.
    if wanted == "Enhanced":
        return {
            "policy_id": "Enhanced", "name": "Enhanced", "strictness": "Enhanced",
            "coverage": "Legacy enhanced screening setting",
            "confirmation": "Confirmation policy is not yet enabled",
            "description": "Legacy promotion setting retained for compatibility; exact J5 rules remain gated.",
        }
    return deepcopy(_POLICIES[1])


def testing_quote(*, provider_id="legacy-promotion-testing", policy_id="Standard",
                  base_cost=2500, sample_count=6, currency="$", planning_only=True):
    """Build a deterministic provider/policy comparison quote.

    ``planning_only`` is intentionally surfaced in the returned payload.  A
    quote never draws RNG, changes cash, or implies that provider effectiveness
    has been wired into the screening resolver.
    """

    provider = provider_by_id(provider_id)
    policy = policy_by_id(policy_id)
    try:
        base = max(0, int(base_cost or 0))
    except (TypeError, ValueError, OverflowError):
        base = 0
    try:
        samples = max(0, min(100, int(sample_count or 0)))
    except (TypeError, ValueError, OverflowError):
        samples = 0
    effective_samples = 0 if policy["policy_id"] == "None" else samples
    try:
        multiplier = float(provider.get("cost_multiplier", 1.0) or 1.0)
        multiplier = multiplier if math.isfinite(multiplier) and multiplier >= 0 else 1.0
    except (TypeError, ValueError, OverflowError):
        multiplier = 1.0
    base_subtotal = base * effective_samples
    amount = round(base_subtotal * multiplier)
    provider_adjustment = amount - base_subtotal
    return {
        "schema_version": CATALOGUE_SCHEMA_VERSION,
        "provider_id": provider["provider_id"],
        "provider": provider["name"],
        "provider_tier": provider["tier"],
        "policy_id": policy["policy_id"],
        "policy": policy["name"],
        "strictness": policy["strictness"],
        "sample_count": effective_samples,
        "requested_sample_count": samples,
        "base_cost_per_sample": base,
        "base_subtotal": base_subtotal,
        "cost_multiplier": provider["cost_multiplier"],
        "provider_adjustment": provider_adjustment,
        "amount": amount,
        "currency": str(currency or "$"),
        "coverage": policy["coverage"] if policy["policy_id"] == "None" else provider["coverage"],
        "policy_coverage": policy["coverage"],
        "policy_confirmation": policy["confirmation"],
        "policy_description": policy["description"],
        "effectiveness": provider["effectiveness"],
        "turnaround": provider["turnaround"],
        "assumptions": [
            "Planning quote only; no cash, RNG, sample or case mutation.",
            "Provider effectiveness does not guarantee a positive finding.",
            "Confirmation, appeals and sanctions require the later J5 case rules.",
        ] if planning_only else [],
        "planning_only": bool(planning_only),
    }


def case_workflow_snapshot(case):
    """Return a pure, honest lifecycle projection for one saved case.

    The projection makes the eventual J5 workflow visible without pretending
    that confirmation, appeals or sanctions are enabled.  It never changes the
    case and never infers a violation from a preliminary result.
    """

    row = case if isinstance(case, dict) else {}
    result_key = saved_screening_result(row)
    result_definition = screening_result_definition(result_key)
    status = str(row.get("status", "Recorded") or "Recorded")
    collected = f"M{row.get('collected_month', 0)} W{row.get('collected_week', 0)}"
    # Legacy rows with the old status but a missing result remain preliminary
    # review evidence; do not turn them into a closed negative by inference.
    if status == "Preliminary review" and not str(row.get("preliminary_result", "") or "").strip():
        result_key = "preliminary_positive"
        result_definition = screening_result_definition(result_key)
    positive = result_key == "preliminary_positive"
    if positive:
        confirmation_status = "Gated"
        confirmation_note = "Confirmation rules are not enabled; preliminary evidence is not a proven violation."
        final_status = "Gated"
        final_note = "No sanction or sporting consequence can be applied in this case slice."
        actions = [
            {"action_id": "review_evidence", "label": "Review evidence", "status": "Available", "effect": "Read-only inspection of the frozen screening record."},
            {"action_id": "request_confirmation", "label": "Request confirmation", "status": "Gated", "effect": confirmation_note},
            {"action_id": "open_appeal", "label": "Open appeal", "status": "Gated", "effect": "Appeal timing and payer rules are not enabled."},
        ]
    elif result_key == "inconclusive":
        confirmation_status = "Gated"
        confirmation_note = "The sample is inconclusive; confirmation and resample rules are not enabled."
        final_status = "Gated"
        final_note = result_definition["note"]
        actions = [
            {"action_id": "review_evidence", "label": "Review evidence", "status": "Available", "effect": "Read-only inspection of the frozen screening record."},
            {"action_id": "request_confirmation", "label": "Request confirmation", "status": "Gated", "effect": confirmation_note},
        ]
    elif result_key == "invalid":
        confirmation_status = "Not applicable"
        confirmation_note = "No confirmation can proceed from an invalid sample."
        final_status = "Invalid sample"
        final_note = result_definition["note"]
        actions = [
            {"action_id": "review_evidence", "label": "Review evidence", "status": "Available", "effect": "Read-only inspection of the frozen sample-quality record."},
        ]
    else:
        confirmation_status = "Not required"
        confirmation_note = "No preliminary alert was recorded."
        final_status = "Closed negative"
        final_note = "Negative screening is closed; no injury, violation or sanction is implied."
        actions = [
            {"action_id": "review_evidence", "label": "Review evidence", "status": "Available", "effect": "Read-only inspection of the frozen screening record."},
        ]
    screening_status = {
        "preliminary_positive": "Alert",
        "negative": "Complete",
        "inconclusive": "Inconclusive",
        "invalid": "Invalid",
    }.get(result_key, "Invalid")
    stages = [
        {"stage_id": "collection", "label": "Sample collected", "status": "Complete", "date": collected, "note": "The sample identity and collection boundary are frozen."},
        {"stage_id": "screening", "label": "Preliminary screening", "status": screening_status, "date": collected, "note": result_definition["note"]},
        {"stage_id": "confirmation", "label": "Confirmation", "status": confirmation_status, "date": "—", "note": confirmation_note},
        {"stage_id": "appeal", "label": "Review / appeal", "status": "Gated" if result_definition["review_required"] and result_key != "invalid" else "Not applicable", "date": "—", "note": "Appeal rules and deadlines are not enabled in this version." if result_key == "preliminary_positive" else ("No appeal is opened until the retained sample has a definitive result." if result_key == "inconclusive" else "No appeal is opened for this sample result.")},
        {"stage_id": "final", "label": "Final outcome", "status": final_status, "date": "—", "note": final_note},
    ]
    confirmation = row.get("confirmation") if isinstance(row.get("confirmation"), dict) else {}
    appeals = row.get("appeals") if isinstance(row.get("appeals"), list) else []
    restriction = row.get("provisional_restriction") if isinstance(row.get("provisional_restriction"), dict) else {}
    sanction = row.get("sanction") if isinstance(row.get("sanction"), dict) else {}
    final_resolution = row.get("final_resolution") if isinstance(row.get("final_resolution"), dict) else {}
    # Keep one defensive contract projection alongside the lifecycle stages.
    # Future confirmation/appeal handlers can consume these exact accepted
    # terms without reading mutable current settings or re-quoting the case.
    provider_snapshot = row.get("provider_snapshot") if isinstance(row.get("provider_snapshot"), dict) else {}
    policy_snapshot = row.get("policy_snapshot") if isinstance(row.get("policy_snapshot"), dict) else {}
    quote_snapshot = row.get("quote_snapshot") if isinstance(row.get("quote_snapshot"), dict) else {}
    frozen_contract = {
        "provider_id": str(row.get("provider_id", "") or provider_snapshot.get("provider_id", "") or ""),
        "provider_version": row.get("provider_version", 1),
        "provider_snapshot": deepcopy(provider_snapshot),
        "policy_id": str(row.get("policy", "") or policy_snapshot.get("policy_id", "") or ""),
        "policy_version": row.get("policy_version", 1),
        "policy_snapshot": deepcopy(policy_snapshot),
        "sample_count": row.get("sample_count", 0),
        "quote_snapshot": deepcopy(quote_snapshot),
    }
    return {
        "schema_version": CATALOGUE_SCHEMA_VERSION,
        "case_id": str(row.get("case_id", "") or ""),
        "test_id": str(row.get("test_id", "") or ""),
        "fighter_id": str(row.get("fighter_id", "") or ""),
        "event_id": str(row.get("event_id", "") or ""),
        "event_reference": deepcopy(row.get("event_reference")) if isinstance(row.get("event_reference"), dict) else {},
        "screening_result": result_key,
        "screening_definition": result_definition,
        "status": status,
        "stages": stages,
        "confirmation_record_count": len(confirmation.get("records", [])) if isinstance(confirmation.get("records", []), list) else 0,
        "appeal_count": len(appeals),
        "provisional_restriction": deepcopy(restriction),
        "sanction": deepcopy(sanction),
        "final_resolution": deepcopy(final_resolution),
        "frozen_contract": frozen_contract,
        "next_actions": actions,
        "sanctions_enabled": False,
        "sporting_effects_enabled": False,
    }
