"""Paired complete-fight evidence for the reviewed successor-only content update."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_engine
import fight_moves
from analysis.compare_bottom_move_expansion import restore_definition
from analysis.generate_move_coverage_report import build_report, summarize_variety
from tools.move_registry_parity import build_dump, compare_followup_update


def compare_reports(before, after):
    failures = []
    if before["mechanical_signatures"] != after["mechanical_signatures"]:
        failures.append("Paired broad mechanical evidence changed")
    if after["chained_selection_pct"] <= before["chained_selection_pct"]:
        failures.append("Follow-up selection share did not increase")
    return failures


def compare_diversity(reference, manifest):
    failures = compare_followup_update(reference, build_dump(fight_moves), manifest)
    if failures:
        raise ValueError("Unapproved registry update: " + "; ".join(failures))
    rows = {row["move_id"]: restore_definition(fight_moves.MoveDefinition, row)
            for row in reference["dump"]["moves"]}
    original = tuple(rows[key] for key in reference["dump"]["move_order"])
    reports = []
    for definitions in (original, fight_moves.MOVE_DEFINITIONS):
        index = fight_moves.MoveIndex(definitions)
        with patch.multiple(fight_engine, MOVE_REGISTRY={m.move_id: m for m in definitions},
                            legal_moves=index.legal_moves):
            reports.append(build_report())
    before, after = reports
    keys = summarize_variety({}, [], 0).keys()
    extra_keys = ("attempted_chain_occurrences_round2_fights", "completed_chain_occurrences_round2_fights",
                  "median_attempted_chain_length_round2_fights", "top_submission_largest_share_pct")
    keys = (*keys, *extra_keys)
    return {"fights_per_arm": 300, "source_sha256": reference["sha256"],
            "updated_roots": len(manifest["updates"]),
            "before": {key: before[key] for key in keys},
            "after": {key: after[key] for key in keys},
            "mechanics_equal": before["mechanical_signatures"] == after["mechanical_signatures"],
            "failures": compare_reports(before, after)}


def main():
    reference = json.loads((ROOT / "analysis/move_registry_followup_diversity.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "analysis/move_followup_continuity_manifest.json").read_text(encoding="utf-8"))
    report = compare_diversity(reference, manifest)
    print(json.dumps(report))
    return int(bool(report["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
