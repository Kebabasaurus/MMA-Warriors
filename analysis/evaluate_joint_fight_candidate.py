"""Compare joint chain/specialist mechanics without changing accepted references."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.fight_candidate_context import candidate_context, DRAFT_MOVE_DEFINITIONS
from analysis.generate_move_coverage_report import (
    build_report, phase_29_failures, phase_30_33_failures, phase_31_failures, phase_31_advisories, slice_5_failures, slice_6_failures,
)
from fight_engine_audit import build_baseline, compare_to_baseline, compare_to_accepted_calibration
from tools.move_registry_parity import build_dump, canonical_bytes
from fight_moves.catalogue.survival_development import SURVIVAL_DEVELOPMENT


def registry_fingerprint():
    import fight_moves
    return hashlib.sha256(canonical_bytes(build_dump(fight_moves))).hexdigest()


def observed_drafts(observed):
    draft_ids = {move.move_id for move in DRAFT_MOVE_DEFINITIONS}
    return sorted(draft_ids.intersection(observed))


def prepared_diagnostics_consistent(report):
    """Missing whole observations cannot silently pass the diagnostic integrity gate."""
    diagnostics = report.get("prepared_submission_diagnostics", {})
    observations = diagnostics.get("observations", [])
    identities = [(row.get("bout_index"), row.get("kind"), row.get("round"), row.get("created_tick"),
                   row.get("top"), row.get("bottom")) for row in observations]
    if len(set(identities)) != len(identities):
        return False
    if any(row.get("kind") not in ("scarf", "von_flue") for row in observations):
        return False
    for kind, field in (("scarf", "scarf_hold_followthrough_counts"),
                        ("von_flue", "von_flue_followthrough_counts")):
        follow = report.get(field, {})
        actual = diagnostics.get("by_setup", {}).get(kind, {})
        opportunities = sum(follow.get(key, 0) for key in
                            ("opponent_intervened", "top_other_action", "used", "top_other_submission"))
        expected = {"opportunities": opportunities,
                    "opponent_interventions": follow.get("opponent_intervened", 0),
                    "submission_choices": follow.get("used", 0) + follow.get("top_other_submission", 0),
                    "prepared_choices": follow.get("used", 0)}
        if any(actual.get(key, 0) != value for key, value in expected.items()):
            return False
        if sum(row.get("kind") == kind for row in observations) != opportunities:
            return False
        if actual.get("weighted_menus", 0) + actual.get("emergency_survival", 0) != (
                opportunities - expected["opponent_interventions"]):
            return False
    return True


def registered_move_inventory(report, definitions):
    """Count the complete active catalogue, never generic fallback or draft-only IDs."""
    active = tuple(move for move in definitions if not move.deprecated)
    observed = set(report.get("observed_move_ids", ()))
    return {
        "unobserved_active_move_ids": sorted(move.move_id for move in active if move.move_id not in observed),
        "active_moves_with_follow_ups": sum(bool(move.follow_ups) for move in active),
    }


def partition_content_findings(findings):
    """Named sample absences are advisory by user policy; other failures stay hard.

    This does not relax aggregate unused-ID, concentration, legality or pool-depth
    limits. Unknown findings fail closed rather than being silently reclassified.
    """
    prefixes = ('Phase 29 move absent from ordinary fights: ', 'Phase 30 move absent: ',
                'Slice 5 move absent: ', 'Slice 6 move absent: ')
    return ([f for f in findings if not f.startswith(prefixes)],
            [f for f in findings if f.startswith(prefixes)])


def variety_advisories(report):
    """Retain the unconditional mean as information, not a release gate."""
    return (["Mean distinct moves outside 20-24 (advisory by user approval)"]
            if not 20 <= report["mean_distinct_moves_per_fighter"] <= 24 else [])


def measured_target_failures(report, definitions, *, expected_active_moves=400):
    """Only measured final targets; passing is not a substitute for the full plan audit."""
    inventory = registered_move_inventory(report, definitions)
    checks = (
        (report.get('survival_expansion_counts', {}).get('invalid', 0) == 0, 'Survival move contradicts position or ownership'),
        (report.get('survival_expansion_counts', {}).get('selected', 0) == sum(
            report.get('move_selection_counts', {}).get(m.move_id,0) for m in SURVIVAL_DEVELOPMENT),
         'Survival validation does not reconcile with selected IDs'),
        (report.get('hold_transition_counts', {}).get('invalid', 0) == 0, 'Submission chain lacks consecutive held-technique provenance'),
        (report.get('cradle_setup_counts', {}).get('invalid', 0) == 0, 'Cradle submission lacks contested setup provenance'),
        (sum(not m.deprecated for m in definitions) == expected_active_moves, f"Active move count is not {expected_active_moves}"),
        (len(inventory["unobserved_active_move_ids"]) <= 8, "More than eight active moves unobserved"),
        (inventory["active_moves_with_follow_ups"] >= 200, "Fewer than 200 active moves declare follow-ups"),
        (report["chained_selection_pct"] >= 15, "Chained selections below 15%"),
        (report["top_ten_move_share_pct"] <= 25, "Top-ten move share exceeds 25%"),
        (report["top_submission_largest_share_pct"] <= 20, "Top submission share exceeds 20%"),
        (len({p for _, p, _ in report["contexts"]}) == 14, "Not all 14 preselection positions observed"),
        (report.get("pocket_exchange_share_pct", 0) >= 8, "Pocket share of standing exchanges below 8%"),
        (report.get("incompatible_submission_identity_count", 0) == 0, "Named submission identity contradicts resolved technique"),
        (report.get("missing_submission_technique_count", 0) == 0, "Submission attempt lacks resolved technique evidence"),
        (report.get("incompatible_submission_defense_count", 0) == 0, "Leg-only defense contradicts resolved non-leg submission"),
        (report.get("top_leg_entry_counts", {}).get("invalid", 0) == 0, "Top leg-entry evidence contradicts trace"),
        (report.get("bottom_leg_entry_counts", {}).get("invalid", 0) == 0, "Bottom leg-entry evidence contradicts trace"),
        (report.get("von_flue_setup_counts", {}).get("invalid", 0) == 0, "Von Flue attempt lacks valid retained-wrap provenance"),
        (report.get("scarf_hold_setup_counts", {}).get("invalid", 0) == 0, "Scarf-hold attempt lacks valid isolation provenance"),
        (report.get("guillotine_defense_counts", {}).get("invalid", 0) == 0, "Guillotine grip/angle evidence contradicts trace"),
        (report.get("von_flue_angle_counts", {}).get("invalid", 0) == 0, "Von Flue angle work lacks consecutive retained-wrap provenance"),
        (report.get("control_award_counts", {}).get("invalid", 0) == 0, "Physical-control award contradicts ownership or control delta"),
        (report.get("missing_control_award_count", 0) == 0, "Experimental exchange lacks control-award evidence"),
        (not any(counts.get(key, 0) for counts in
                 report.get("prepared_submission_diagnostics", {}).get("by_setup", {}).values()
                 for key in ("invalid_observations", "missing_draws", "incomplete", "unobserved_menus")),
         "Prepared-submission diagnostic evidence is incomplete or ambiguous"),
        (prepared_diagnostics_consistent(report), "Prepared-submission observations do not reconcile with trace roots"),
    )
    return [message for passed, message in checks if not passed]


def coverage_trial(fights=300, *, combined_only=False, continuation_branches=False,
                   stronger_continuation=False, repertoire_readaptation=False, continuation_commitment=False,
                   gift_wrap_control=False, gift_wrap_mount=False, jab_readaptation=False, boxing_chain_pool=False,
                   heel_hook_identity=False, hold_transitions=False, cradle_setup=False, standing_head_damage=False,
                   kick_power=False, survival_expansion=False):
    arms = {}
    configurations = (
        ("normal", False, False, False),
        ("content_only", False, False, True),
        ("entries", True, False, True),
        ("chains", False, True, True),
        ("combined", True, True, True),
    )
    for name, entries, chains, content in configurations:
        if combined_only and name != "combined":
            continue
        with candidate_context(entries=entries, chains=chains, draft_content=content,
                               continuation_branches=continuation_branches and chains,
                               stronger_continuation=stronger_continuation and chains,
                               repertoire_readaptation=repertoire_readaptation and chains,
                               jab_readaptation=jab_readaptation and chains,
                               boxing_chain_pool=boxing_chain_pool and chains,
                               continuation_commitment=continuation_commitment and chains,
                               gift_wrap_control=gift_wrap_control and chains,
                               gift_wrap_mount=gift_wrap_mount and chains,
                               heel_hook_identity=heel_hook_identity and entries,
                               hold_transitions=hold_transitions and entries,
                               cradle_setup=cradle_setup and entries,
                               standing_head_damage=standing_head_damage and entries and chains,
                               kick_power=kick_power and entries and chains,
                               survival_expansion=survival_expansion and entries and chains and content) as definitions:
            registry_sha256 = registry_fingerprint()
            report = build_report(fights, definitions=definitions)
            failures = (phase_29_failures(report) + phase_30_33_failures(report)
                        + slice_5_failures(report) + slice_6_failures(report))
            failures, frequency_advisories = partition_content_findings(failures)
        keep = ("survival_expansion_counts", "move_selection_counts", "hold_transition_counts", "cradle_setup_counts", "total_move_selections", "mean_distinct_moves_per_fighter", "top_ten_move_share_pct",
                "chained_selection_pct", "attempted_chain_occurrences_round2_fights",
                "completed_chain_occurrences_round2_fights", "median_attempted_chain_length_round2_fights",
                "top_submission_largest_share_pct", "pocket_exchange_share_pct",
                "exchange_position_counts", "action_selection_counts", "pocket_entry_count",
                "pocket_observed_episodes", "pocket_mean_residence_beats",
                "pocket_residence_histogram", "pocket_exit_counts", "submission_attempt_identity_count",
                "generic_submission_identity_count", "incompatible_submission_identity_count", "missing_submission_technique_count",
                "submission_identity_contexts", "incompatible_submission_defense_count", "top_leg_entry_counts",
                "bottom_leg_entry_counts",
                "von_flue_setup_counts", "scarf_hold_setup_counts", "guillotine_defense_counts", "von_flue_angle_counts",
                "von_flue_followthrough_counts", "scarf_hold_followthrough_counts", "control_award_counts",
                "missing_control_award_count", "prepared_submission_diagnostics",
                "maximum_identical_defense_clause", "defense_repetition_window_fights",
                "aggregate_maximum_identical_defense_clause")
        arms[name] = {key: report[key] for key in keep}
        arms[name].update(registered_move_inventory(report, definitions))
        arms[name].update(active_moves=sum(not move.deprecated for move in definitions),
                          preselection_positions=sorted({p for _, p, _ in report["contexts"]}),
                          generic_move_ids=[m for m in report["observed_move_ids"] if m.startswith("generic_")],
                          observed_draft_ids=observed_drafts(report["observed_move_ids"]),
                          draft_selection_counts={m.move_id: report["move_selection_counts"].get(m.move_id, 0)
                                                  for m in DRAFT_MOVE_DEFINITIONS} if content else {},
                          unobserved_draft_ids=sorted({m.move_id for m in DRAFT_MOVE_DEFINITIONS}
                                                      - set(report["observed_move_ids"])) if content else [],
                          registry_sha256=registry_sha256,
                          content_gate_failures=failures,
                          content_frequency_advisories=frequency_advisories,
                          chain_gate_failures=phase_31_failures(report),
                          chain_advisories=phase_31_advisories(report),
                          variety_advisories=variety_advisories(report),
                          measured_final_target_failures=measured_target_failures(report, definitions,
                              expected_active_moves=440 if survival_expansion and entries and chains and content else 400),
                          mechanical_signature_sha256=hashlib.sha256(
                              json.dumps(report["mechanical_signatures"]).encode()).hexdigest())
    return {"experimental_only": True, "fights_per_arm": fights, "arms": arms,
            "scope": ("Combined-candidate frequency diagnostic; no calibration or final target acceptance implied"
                      if combined_only else
                      "Diagnostic factorial comparison; no calibration or final target acceptance implied")}


def calibration_trial(*, continuation_branches=False, stronger_continuation=False,
                      repertoire_readaptation=False, continuation_commitment=False, gift_wrap_control=False,
                      gift_wrap_mount=False, jab_readaptation=False, boxing_chain_pool=False,
                      heel_hook_identity=False, hold_transitions=False, cradle_setup=False, standing_head_damage=False,
                      kick_power=False, survival_expansion=False):
    reference = ROOT / "analysis/fight_engine_baseline.json"
    baseline = json.loads(reference.read_text(encoding="utf-8"))
    import fight_engine_audit
    from analysis.submission_chain_candidate import validate_hold_transitions
    from analysis.cradle_setup_candidate import validate_cradle_setups
    original_run = fight_engine_audit.run_audited_fight
    hold_counts, cradle_counts = Counter(), Counter()
    survival_counts = Counter()
    def observed_run(*args, **kwargs):
        audit = original_run(*args, **kwargs)
        if hold_transitions:
            hold_counts.update(validate_hold_transitions(audit['trace']))
        if cradle_setup:
            cradle_counts.update(validate_cradle_setups(audit['trace']))
        if survival_expansion:
            from analysis.survival_expansion_candidate import validate_survival_trace
            survival_counts.update(validate_survival_trace(audit['trace']))
        return audit
    with candidate_context(entries=True, chains=True, draft_content=True,
                           continuation_branches=continuation_branches,
                           stronger_continuation=stronger_continuation,
                           repertoire_readaptation=repertoire_readaptation,
                           jab_readaptation=jab_readaptation,
                           boxing_chain_pool=boxing_chain_pool,
                           continuation_commitment=continuation_commitment, gift_wrap_control=gift_wrap_control,
                           gift_wrap_mount=gift_wrap_mount, heel_hook_identity=heel_hook_identity,
                           hold_transitions=hold_transitions, cradle_setup=cradle_setup,
                           standing_head_damage=standing_head_damage, kick_power=kick_power,
                           survival_expansion=survival_expansion):
        registry_sha256 = registry_fingerprint()
        with patch.object(fight_engine_audit, 'run_audited_fight', observed_run):
            result = build_baseline(int(baseline["seeds_per_matchup"]))
    baseline_failures = compare_to_baseline(result, baseline)
    balance_advisories = []
    if standing_head_damage:
        timing = 'Middle finish timing moved by more than 2.0 percentage points'
        if timing in baseline_failures:
            baseline_failures.remove(timing)
            balance_advisories.append('Middle finish timing drift accepted by user for the 2% head-damage trial')
    failures = baseline_failures + compare_to_accepted_calibration(result)
    if survival_counts.get('invalid',0):
        failures.append('Survival ownership failed in full calibration')
    if hold_counts.get('invalid', 0) or cradle_counts.get('invalid', 0):
        failures.append('Submission development provenance failed in full calibration')
    return {"experimental_only": True, "fights": result["fight_count"],
            "overall": result["groups"]["Overall"], "failures": failures,
            "groups": result["groups"],
            "hold_transition_counts": dict(hold_counts), "cradle_setup_counts": dict(cradle_counts),
            "survival_expansion_counts": dict(survival_counts),
            "balance_advisories": balance_advisories,
            "registry_sha256": registry_sha256,
            "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest()}


def reported_failures(result):
    """Keep all arm gates visible to callers and the command's exit status.

    An extended frequency run is still diagnostic even when this list is empty.
    The control arms are reported by name; they are not candidate acceptance.
    """
    failures = list(result.get('failures', ()))
    for name, arm in result.get('arms', {}).items():
        for field in ('content_gate_failures', 'chain_gate_failures',
                      'measured_final_target_failures'):
            failures.extend(f'{name}: {failure}' for failure in arm.get(field, ()))
    return list(dict.fromkeys(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--survival-expansion', action='store_true', help='User-approved 440-move candidate with 50 survival techniques')
    parser.add_argument('--kick-power', action='store_true', help='Audit-only +1% resolved kick power')
    parser.add_argument('--standing-head-damage', action='store_true', help='Audit-only +2% standing head-strike impact')
    parser.add_argument('--hold-transitions', action='store_true', help='Audit-only proven adjacent submission chains')
    parser.add_argument('--cradle-setup', action='store_true', help='Audit-only contested cradle preparation and crank')
    parser.add_argument('--heel-hook-identity', action='store_true', help='Audit-only real heel-hook submission identity repair')
    parser.add_argument('--boxing-chain-pool', action='store_true', help='Audit-only current-pool boxing continuation demand')
    parser.add_argument("--coverage", action="store_true", help="Five-arm variety diagnostic instead of full calibration")
    parser.add_argument('--gift-wrap-control', action='store_true', help='Single-root audit-only control branch repair')
    parser.add_argument('--gift-wrap-mount', action='store_true', help='Mount-only branch refinement retaining original back branches')
    parser.add_argument('--continuation-commitment', action='store_true',
                        help='Audit-only fresh/unhurt probability-bounded action commitment')
    parser.add_argument('--repertoire-readaptation', action='store_true',
                        help='Audit-only earlier independent-move repetition preference; live chains unchanged')
    parser.add_argument('--jab-readaptation', action='store_true',
                        help='Audit-only earlier repetition preference restricted to independent jabs')
    parser.add_argument('--stronger-continuation', action='store_true',
                        help='Audit-only double action-continuation bonus; initiative and release targets unchanged')
    parser.add_argument("--continuation-branches", action="store_true",
                        help="Opt into the additive sparse-root branch trial; never changes release targets")
    parser.add_argument("--fights", type=int, default=300, help="Coverage fights per arm; never shortens calibration")
    parser.add_argument("--combined-only", action="store_true",
                        help="With --coverage, measure only the combined candidate for extended frequency diagnostics")
    parser.add_argument("--output", type=Path, help="Optional NEW diagnostic artifact; existing files are never overwritten")
    args = parser.parse_args()
    if args.jab_readaptation and args.repertoire_readaptation:
        parser.error('Jab and broad readaptation are mutually exclusive')
    if args.combined_only and not args.coverage:
        parser.error("--combined-only requires --coverage; full calibration cannot be shortened")
    if args.output and args.output.exists():
        raise FileExistsError(f"Diagnostic output already exists: {args.output}")
    engine_sha256 = hashlib.sha256((ROOT / "fight_engine.py").read_bytes()).hexdigest()
    source_sha256 = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "analysis/fight_candidate_context.py", "analysis/evaluate_joint_fight_candidate.py",
        "analysis/continuation_branch_candidate.py",
        "analysis/continuation_strength_candidate.py",
        "analysis/continuation_commitment_candidate.py",
        "analysis/gift_wrap_control_candidate.py",
        "analysis/gift_wrap_mount_candidate.py",
        "analysis/repertoire_readaptation_candidate.py",
        "analysis/boxing_chain_pool_candidate.py",
        "analysis/heel_hook_identity_candidate.py",
        "analysis/submission_chain_candidate.py", "analysis/cradle_setup_candidate.py",
        "analysis/standing_head_damage_candidate.py",
        "analysis/kick_power_candidate.py",
        "analysis/survival_expansion_candidate.py", "fight_moves/catalogue/survival_development.py",
        "fight_moves/submission_transition.py",
        "analysis/prepared_submission_diagnostics.py",
        "analysis/von_flue_angle_provenance.py",
        "analysis/generate_move_coverage_report.py", "fight_moves/catalogue/specialist_entry_development.py",
        "fight_moves/catalogue/front_headlock_development.py",
        "fight_moves/catalogue/turtle_development.py", "fight_moves/catalogue/failed_shot_development.py",
        "fight_moves/catalogue/standing_back_development.py",
        "fight_moves/catalogue/leg_entanglement_development.py",
        "fight_moves/submission_identity.py",
        "fight_moves/submission_pool.py",
        "fight_moves/selection_pool.py", "fight_moves/specialist_intent.py",
        "fight_engine_audit.py",
    )}
    trial_options = {"continuation_branches": True} if args.continuation_branches else {}
    if args.survival_expansion:
        trial_options['survival_expansion'] = True
    if args.kick_power:
        trial_options['kick_power'] = True
    if args.standing_head_damage:
        trial_options['standing_head_damage'] = True
    if args.hold_transitions:
        trial_options['hold_transitions'] = True
    if args.cradle_setup:
        trial_options['cradle_setup'] = True
    if args.heel_hook_identity:
        trial_options['heel_hook_identity'] = True
    if args.stronger_continuation:
        trial_options['stronger_continuation'] = True
    if args.repertoire_readaptation:
        trial_options['repertoire_readaptation'] = True
    if args.jab_readaptation:
        trial_options['jab_readaptation'] = True
    if args.boxing_chain_pool:
        trial_options['boxing_chain_pool'] = True
    if args.continuation_commitment:
        trial_options['continuation_commitment'] = True
    if args.gift_wrap_control:
        trial_options['gift_wrap_control'] = True
    if args.gift_wrap_mount:
        trial_options['gift_wrap_mount'] = True
    result = (coverage_trial(args.fights, combined_only=args.combined_only, **trial_options)
              if args.coverage else calibration_trial(**trial_options))
    result['failures'] = reported_failures(result)
    result["continuation_branch_trial"] = bool(args.continuation_branches)
    result['heel_hook_identity_trial'] = bool(args.heel_hook_identity)
    result['hold_transitions_trial'] = bool(args.hold_transitions)
    result['cradle_setup_trial'] = bool(args.cradle_setup)
    result['standing_head_damage_trial'] = bool(args.standing_head_damage)
    result['kick_power_trial'] = bool(args.kick_power)
    result['survival_expansion_trial'] = bool(args.survival_expansion)
    result['stronger_continuation_trial'] = bool(args.stronger_continuation)
    result['repertoire_readaptation_trial'] = bool(args.repertoire_readaptation)
    result['jab_readaptation_trial'] = bool(args.jab_readaptation)
    result['boxing_chain_pool_trial'] = bool(args.boxing_chain_pool)
    result['continuation_commitment_trial'] = bool(args.continuation_commitment)
    result['gift_wrap_control_trial'] = bool(args.gift_wrap_control)
    result['gift_wrap_mount_trial'] = bool(args.gift_wrap_mount)
    result['continuation_bonus_multiplier'] = 2.0 if args.stronger_continuation else 1.0
    if hashlib.sha256((ROOT / "fight_engine.py").read_bytes()).hexdigest() != engine_sha256 or any(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value
            for name, value in source_sha256.items()):
        raise RuntimeError("Candidate sources changed during collection")
    result.update(engine_sha256=engine_sha256, source_sha256=source_sha256)
    if args.output:
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    print(json.dumps(result, indent=2))
    return int(bool(result.get("failures")))


if __name__ == "__main__":
    raise SystemExit(main())
