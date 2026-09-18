"""Evaluate the approved split-sample policy against a pinned historical bundle.

This does not certify current source, runtime integration, performance or packaging.
The saved reports lack per-bout fixture hashes; their recognized, byte-exact envelopes
bind the reviewed schedules and observations, not an independently reconstructed run.
Fresh complete-bout integration parity and shipping checks are separate requirements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
UNUSED_FAILURE = "More than eight active moves unobserved"
PINS = {
    "standard": ("survival_expansion_440_release_check_300.json",
                 "c32663c9602ac75cfba9b7061fb28dd8b5bc950d2cfccb969a79ce102d307cc3"),
    "frequency": ("survival_expansion_440_defense_fix_25000.json",
                  "da70d12613957ad2391f8e65e2a3714b8326d6ee34feaf8066bf6a4b0cb57327"),
    "calibration": ("survival_expansion_440_calibration.json",
                    "d3d813eaa88dfa900983b0a60a44d22fa1f35e6a31cd6d4680c3efec11bc60f0"),
}
REGISTRY = "7e6428db43f0e25011975e954db97746cb55d9721837a7377b5bbb7ead1d6a39"
GATE_FIELDS = ("content_gate_failures", "chain_gate_failures",
               "measured_final_target_failures")
ENABLED = {"heel_hook_identity", "hold_transitions", "cradle_setup",
           "standing_head_damage", "kick_power", "survival_expansion", "gift_wrap_mount"}
DISABLED = {"continuation_branch", "stronger_continuation", "repertoire_readaptation",
            "jab_readaptation", "boxing_chain_pool", "continuation_commitment",
            "gift_wrap_control"}
REVIEWED_POST_COLLECTION_FILES = frozenset({
    "identity_persistence_regression_test.py",
    "fight_move_deprecation_regression_test.py",
    "fight_release_acceptance_test.py",
    "analysis/validate_fight_release.py",
})


def source_projection(recorded, current):
    """Allow only reviewed test/policy edits, never missing files or runtime drift."""
    if not isinstance(recorded, dict) or set(recorded) != set(current):
        return ["source inventory differs from current files"], []
    failures, reviewed = [], []
    for name in sorted(current):
        old, new = recorded[name], current[name]
        if (not isinstance(old, str) or len(old) != 64
                or any(char not in "0123456789abcdef" for char in old)):
            failures.append(f"invalid recorded source hash: {name}")
        elif old != new:
            if name in REVIEWED_POST_COLLECTION_FILES:
                reviewed.append({"path": name, "recorded_sha256": old, "current_sha256": new})
            else:
                failures.append(f"bound source changed: {name}")
    return failures, reviewed


def load_reviewed_bundle(paths=None):
    """Reject edited, incomplete or substituted reports before policy evaluation."""
    reports = {}
    for role, (filename, expected) in PINS.items():
        path = Path(paths[role]) if paths else ROOT / "analysis" / filename
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"{role}: unrecognized historical evidence checksum")
        reports[role] = json.loads(raw)
    return reports


def policy_failures(reports):
    """Pure policy check; public CLI additionally requires all immutable byte pins."""
    failures = []
    standard, frequency, calibration = (reports[k] for k in PINS)
    expected_arms = {"normal", "content_only", "entries", "chains", "combined"}
    if standard.get("fights_per_arm") != 300 or set(standard.get("arms", {})) != expected_arms:
        failures.append("Standard evidence must retain the complete five-arm 300-bout report")
    if frequency.get("fights_per_arm") != 25000 or set(frequency.get("arms", {})) != {"combined"}:
        failures.append("Rare-move evidence must contain exactly 25,000 combined-arm bouts")
    for role, report in reports.items():
        for flag in ENABLED | DISABLED:
            if report.get(flag + "_trial") is not (flag in ENABLED):
                failures.append(f"{role}: wrong or missing retained candidate option {flag}")
        if report.get("continuation_bonus_multiplier") != 1.0:
            failures.append(f"{role}: changed continuation multiplier")
        if not report.get("source_sha256") or len(report.get("engine_sha256", "")) != 64:
            failures.append(f"{role}: source provenance missing")
    for role, report in (("standard", standard), ("frequency", frequency)):
        arm = report.get("arms", {}).get("combined", {})
        if arm.get("registry_sha256") != REGISTRY or arm.get("active_moves") != 440:
            failures.append(f"{role}: wrong active registry")
        if len(arm.get("mechanical_signature_sha256", "")) != 64:
            failures.append(f"{role}: mechanical signature missing")
        for field in GATE_FIELDS:
            if not isinstance(arm.get(field), list):
                failures.append(f"{role}: missing {field}")
                continue
            failures.extend(f"{role}: {finding}" for finding in arm[field]
                            if not (role == "standard" and field == "measured_final_target_failures"
                                    and finding == UNUSED_FAILURE))
        # Control arms are retained for attribution, not judged against candidate-only
        # targets. Reject unexplained root failures rather than ignoring the root list.
        known = {f"{name}: {finding}" for name, data in report.get("arms", {}).items()
                 for field in GATE_FIELDS for finding in data.get(field, [])}
        failures.extend(f"{role}: {finding}" for finding in report.get("failures", [])
                        if finding not in known)
        if (arm.get("defense_repetition_window_fights") != 300
                or arm.get("maximum_identical_defense_clause", 10) >= 10):
            failures.append(f"{role}: rolling-300 defense repetition failed")
        # Recheck the important measured thresholds rather than trusting empty lists.
        for valid, message in (
            (arm.get("top_ten_move_share_pct", 100) <= 25, "move concentration"),
            (arm.get("chained_selection_pct", 0) >= 15, "chained-selection share"),
            (arm.get("top_submission_largest_share_pct", 100) <= 20, "submission concentration"),
            (arm.get("active_moves_with_follow_ups", 0) >= 200, "follow-up inventory"),
            (arm.get("pocket_exchange_share_pct", 0) >= 8, "pocket occupancy"),
        ):
            if not valid:
                failures.append(f"{role}: {message} failed")
    absent = frequency.get("arms", {}).get("combined", {}).get("unobserved_active_move_ids")
    if not isinstance(absent, list) or len(absent) > 8 or len(set(absent)) != len(absent):
        failures.append("frequency: more than eight unused active moves or malformed inventory")
    if (calibration.get("fights") != 3840 or len(calibration.get("groups", {})) != 39
            or calibration.get("overall", {}).get("total") != 3840):
        failures.append("Calibration must retain all 3,840 bouts and 39 canonical groups")
    if calibration.get("registry_sha256") != REGISTRY:
        failures.append("Calibration registry differs from coverage")
    if not isinstance(calibration.get("failures"), list):
        failures.append("Calibration failures missing")
    failures.extend(f"calibration: {finding}" for finding in calibration.get("failures", []))
    return list(dict.fromkeys(failures))


def validate_reviewed_bundle(paths=None):
    reports = load_reviewed_bundle(paths)
    failures = policy_failures(reports)
    return {
        "scope": "Historical evidence policy evaluation only; not current runtime release certification",
        "policy": {"standard_fights": 300, "rare_move_fights": 25000,
                   "maximum_unobserved_active_moves": 8, "calibration_fights": 3840},
        "historical_policy_passed": not failures,
        "runtime_release_certified": False,
        "failures": failures,
        "evidence_sha256": {role: value[1] for role, value in PINS.items()},
        "historical_engine_sha256": {role: report["engine_sha256"] for role, report in reports.items()},
        "unobserved_active_move_ids": reports["frequency"]["arms"]["combined"]["unobserved_active_move_ids"],
        "raw_standard_findings": reports["standard"]["failures"],
        "remaining_requirements": ["Current native engine complete-bout parity with retained candidate",
                                   "Current shipping regressions and whole-bout performance",
                                   "Build and packaged runtime launch verification"],
    }


def validate_native_reports(standard, frequency, parity):
    """Check current, complete evidence; hashes establish consistency, not authorship.

    This certifies the engine evidence gate only. Shipping regressions and packaged
    launch verification are still required before distributing the executable.
    """
    from analysis.evaluate_release_runtime import source_hashes, schedule_fingerprint, registry_fingerprint
    from analysis.verify_release_integration import sources, fixture_schedule, digest
    from analysis.evaluate_joint_fight_candidate import measured_target_failures
    from fight_moves.release_registry import RELEASE_MOVE_DEFINITIONS
    failures = []
    current = source_hashes()
    reviewed_changes = {}
    retained = load_reviewed_bundle()
    for role, report, count in (("standard", standard, 300), ("frequency", frequency, 25000)):
        if (report.get("native_release_runtime") is not True
                or report.get("experimental_only") is not False
                or report.get("source_guard_passed") is not True
                or report.get("fights_per_arm") != count
                or set(report.get("arms", {})) != {"combined"}):
            failures.append(f"{role}: incomplete native coverage identity")
        source_failures, changes = source_projection(report.get("source_sha256"), current)
        failures.extend(f"{role}: {finding}" for finding in source_failures)
        reviewed_changes[role] = changes
        if report.get("engine_sha256") != current["fight_engine.py"]:
            failures.append(f"{role}: engine hash is not current")
        if report.get("schedule_sha256") != schedule_fingerprint(count):
            failures.append(f"{role}: wrong canonical coverage schedule")
        arm = report.get("arms", {}).get("combined", {})
        if arm.get("registry_sha256") != REGISTRY or registry_fingerprint() != REGISTRY:
            failures.append(f"{role}: wrong release registry")
        if arm.get("fight_count") != count:
            failures.append(f"{role}: incomplete observed bouts")
        diagnostic_fields = ("survival_expansion_counts", "hold_transition_counts", "cradle_setup_counts",
            "top_leg_entry_counts", "bottom_leg_entry_counts", "von_flue_setup_counts",
            "scarf_hold_setup_counts", "guillotine_defense_counts", "von_flue_angle_counts",
            "control_award_counts", "prepared_submission_diagnostics")
        if any(not isinstance(arm.get(field), dict) for field in diagnostic_fields):
            failures.append(f"{role}: required diagnostic evidence missing")
        try:
            observed = dict(arm, contexts=[("", position, "") for position in arm["preselection_positions"]],
                            observed_move_ids=list(arm["move_selection_counts"]))
            findings = measured_target_failures(observed, RELEASE_MOVE_DEFINITIONS, expected_active_moves=440)
            failures.extend(f"{role}: {finding}" for finding in findings
                            if not (role == "standard" and finding == UNUSED_FAILURE))
        except (KeyError, TypeError, ValueError):
            failures.append(f"{role}: malformed measured target evidence")
    # Reuse the strict threshold/failure policy without mistaking historical control
    # arms or trial metadata for native runtime evidence.
    import copy
    policy = copy.deepcopy(retained)
    for role, report in (("standard", standard), ("frequency", frequency)):
        policy[role]["arms"]["combined"] = report.get("arms", {}).get("combined", {})
        policy[role]["failures"] = report.get("failures", [])
    failures.extend(policy_failures(policy))
    for role, report in (("standard", standard), ("frequency", frequency)):
        if not isinstance(report.get("failures"), list):
            failures.append(f"{role}: missing top-level failures")
    if (parity.get("fights") != 3840 or parity.get("calibration_corpus") is not True
            or parity.get("all_complete_bouts_and_rng_equal") is not True):
        failures.append("Native calibration must prove 3,840 complete-bout/RNG pairs")
    if sources() != current:
        failures.append("Native coverage and parity disagree on the current source inventory")
    source_failures, changes = source_projection(parity.get("source_sha256"), current)
    failures.extend(f"native parity: {finding}" for finding in source_failures)
    reviewed_changes["parity"] = changes
    # Original reports must agree with one another for every simulation/audit source,
    # not just claim to agree with whatever is installed at certification time.
    for name in set(current) - REVIEWED_POST_COLLECTION_FILES:
        values = [report.get("source_sha256", {}).get(name) for report in (standard, frequency, parity)]
        if len(set(values)) != 1:
            failures.append(f"Native evidence disagrees on bound source: {name}")
    reference_hashes = {name: hashlib.sha256((ROOT / "analysis" / name).read_bytes()).hexdigest()
                       for name in ("fight_engine_baseline.json", "survival_expansion_440_calibration.json")}
    if (parity.get("reference_sha256") != reference_hashes
            or reference_hashes["fight_engine_baseline.json"] != retained["calibration"]["reference_sha256"]):
        failures.append("Native parity calibration references changed or are missing")
    schedule = fixture_schedule(None, calibration_corpus=True)
    if parity.get("schedule_sha256") != digest(schedule):
        failures.append("Native parity has the wrong canonical calibration schedule")
    pairs = parity.get("pairs", [])
    def sha(value):
        return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    if (not isinstance(pairs, list) or len(pairs) != 3840
            or any(not isinstance(pair, dict)
                   or pair.get("seed") != item["seed"] or pair.get("spec_id") != item["spec"]["id"]
                   or not sha(pair.get("audit_sha256")) or not sha(pair.get("terminal_rng_sha256"))
                   for pair, item in zip(pairs, schedule))
            or not sha(parity.get("fixture_sha256"))):
        failures.append("Native parity pairs or fixture provenance are incomplete")
    if parity.get("groups") != retained["calibration"]["groups"]:
        failures.append("Native calibration does not reproduce all 39 accepted groups")
    if not isinstance(parity.get("failures"), list):
        failures.append("Native calibration failures are missing")
    failures.extend(f"native calibration: {value}" for value in parity.get("failures", []))
    for kind, field in (("cradle", "cradle_setup_counts"), ("holds", "hold_transition_counts"),
                        ("survival", "survival_expansion_counts")):
        counts = parity.get("validations", {}).get(kind)
        if (not isinstance(counts, dict) or not counts or counts.get("invalid") != 0
                or counts != retained["calibration"][field]):
            failures.append(f"Native calibration {kind} provenance is incomplete or invalid")
    failures = list(dict.fromkeys(failures))
    return {"scope": "Current native engine evidence gate; packaging and shipping tests remain separate",
            "runtime_release_certified": not failures, "failures": failures,
            "source_sha256": current,
            "certification_policy_sha256": current["analysis/validate_fight_release.py"],
            "reviewed_post_collection_source_changes": reviewed_changes,
            "source_scope": "All original simulation/audit sources must match; only the four explicitly reviewed test/policy files may differ. Original collection guards and report bytes are unchanged.",
            "reference_sha256": reference_hashes,
            "unobserved_active_move_ids": frequency.get("arms", {}).get("combined", {}).get("unobserved_active_move_ids"),
            "raw_standard_findings": standard.get("failures"),
            "remaining_requirements": ["Shipping regressions", "Build and packaged launch verification"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-historical-bundle", action="store_true")
    parser.add_argument("--native-standard", type=Path)
    parser.add_argument("--native-frequency", type=Path)
    parser.add_argument("--native-parity", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    paths = (args.native_standard, args.native_frequency, args.native_parity)
    if args.reviewed_historical_bundle:
        if any(paths):
            parser.error("Historical and native modes cannot be combined")
        result = validate_reviewed_bundle()
    else:
        if not all(paths):
            parser.error("Choose the historical bundle or supply all three native evidence paths")
        payloads = [path.read_bytes() for path in paths]
        result = validate_native_reports(*(json.loads(raw) for raw in payloads))
        result["evidence_sha256"] = {str(path): hashlib.sha256(raw).hexdigest()
                                    for path, raw in zip(paths, payloads)}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
    print(rendered, end="")
    return int(bool(result["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
