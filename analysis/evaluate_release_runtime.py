"""Source-bound native release coverage; no candidate runtime or registry patches.

Only the disposable coverage builder's two harness references are substituted.
300-bout non-frequency gates and the 25,000-bout rare-ID gate remain distinct.
Both outputs retain every original finding; this tool alone is not release approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_moves
from fight_release import ReleaseFightEngineMixin
from fight_engine_audit import FightAuditHarness, move_report_specs
from fight_moves.release_registry import RELEASE_MOVE_DEFINITIONS, RELEASE_MOVE_INDEX
from analysis.prepared_submission_diagnostics import PreparedFightAuditHarness
from analysis import generate_move_coverage_report as coverage
from analysis.evaluate_joint_fight_candidate import (
    DRAFT_MOVE_DEFINITIONS, measured_target_failures, observed_drafts,
    partition_content_findings, registered_move_inventory, reported_failures,
    variety_advisories,
)
from tools.move_registry_parity import build_dump, canonical_bytes


class NativeFightAuditHarness(ReleaseFightEngineMixin, FightAuditHarness):
    pass


class NativePreparedFightAuditHarness(ReleaseFightEngineMixin, PreparedFightAuditHarness):
    pass


def source_hashes():
    """Bind all root runtime modules, catalogue/package code and audit tooling.

    Generated dist/build and user save/database folders are deliberately excluded.
    The application runtime consists of root modules and the fight_moves package.
    """
    paths = set(ROOT.glob("*.py"))
    for directory in ("fight_moves", "analysis", "tools"):
        paths.update((ROOT / directory).rglob("*.py"))
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def registry_fingerprint():
    facade = SimpleNamespace(**{key: getattr(fight_moves, key) for key in (
        "KNOWN_PARENT_ACTIONS", "ALL_POSITIONS", "DEFENSE_DEFINITIONS")},
        MOVE_DEFINITIONS=RELEASE_MOVE_DEFINITIONS, legal_moves=RELEASE_MOVE_INDEX.legal_moves,
        REGISTRY_SCHEMA_VERSION=getattr(fight_moves, "REGISTRY_SCHEMA_VERSION", 1))
    return hashlib.sha256(canonical_bytes(build_dump(facade))).hexdigest()


def schedule_fingerprint(fights):
    specs = move_report_specs()
    schedule = [{"bout_index": index, "spec": specs[index % len(specs)],
                 "seed": 9_310_000 + (index % len(specs)) * 10_000 + index // len(specs)}
                for index in range(fights)]
    return hashlib.sha256(canonical_bytes(schedule)).hexdigest()


def _build_native_report(fights):
    """Internal arbitrary-count entry for narrow tests, never the acceptance CLI."""
    with patch.object(coverage, "FightAuditHarness", NativeFightAuditHarness), patch.object(
            coverage, "PreparedFightAuditHarness", NativePreparedFightAuditHarness):
        return coverage.build_report(fights, definitions=RELEASE_MOVE_DEFINITIONS)


def summarize_report(report):
    # Preserve the complete coverage report apart from its large per-bout signatures
    # and tuple-keyed contexts. Their lossless summaries/hashes are stored below.
    arm = {key: value for key, value in report.items()
           if key not in ("mechanical_signatures", "contexts")}
    findings = (coverage.phase_29_failures(report) + coverage.phase_30_33_failures(report)
                + coverage.slice_5_failures(report) + coverage.slice_6_failures(report))
    findings, frequency = partition_content_findings(findings)
    arm.update(registered_move_inventory(report, RELEASE_MOVE_DEFINITIONS))
    arm.update(
        active_moves=sum(not move.deprecated for move in RELEASE_MOVE_DEFINITIONS),
        preselection_positions=sorted({position for _, position, _ in report["contexts"]}),
        generic_move_ids=[key for key in report["observed_move_ids"] if key.startswith("generic_")],
        observed_draft_ids=observed_drafts(report["observed_move_ids"]),
        draft_selection_counts={move.move_id: report["move_selection_counts"].get(move.move_id, 0)
                                for move in DRAFT_MOVE_DEFINITIONS},
        unobserved_draft_ids=sorted({move.move_id for move in DRAFT_MOVE_DEFINITIONS}
                                   - set(report["observed_move_ids"])),
        registry_sha256=registry_fingerprint(),
        content_gate_failures=findings, content_frequency_advisories=frequency,
        chain_gate_failures=coverage.phase_31_failures(report),
        chain_advisories=coverage.phase_31_advisories(report),
        variety_advisories=variety_advisories(report),
        measured_final_target_failures=measured_target_failures(
            report, RELEASE_MOVE_DEFINITIONS, expected_active_moves=440),
        mechanical_signature_sha256=hashlib.sha256(
            json.dumps(report["mechanical_signatures"]).encode()).hexdigest(),
    )
    return arm


def evaluate(fights):
    if type(fights) is not int or fights not in (300, 25000):
        raise ValueError("Native release evidence requires exactly 300 or 25,000 bouts")
    before = source_hashes()
    schedule_hash = schedule_fingerprint(fights)
    registry_hash = registry_fingerprint()
    arm = summarize_report(_build_native_report(fights))
    if source_hashes() != before or registry_fingerprint() != registry_hash:
        raise RuntimeError("Source or registry changed during native coverage collection")
    result = {"experimental_only": False, "native_release_runtime": True,
              "fights_per_arm": fights, "arms": {"combined": arm},
              "scope": "Native release coverage only; calibration, parity and performance are separate gates",
              "source_sha256": before, "engine_sha256": before["fight_engine.py"],
              "schedule_sha256": schedule_hash, "source_guard_passed": True}
    result["failures"] = reported_failures(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fights", type=int, choices=(300, 25000), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate(args.fights)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), "fights": args.fights,
                      "failures": result["failures"]}, indent=2))
    return int(bool(result["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
