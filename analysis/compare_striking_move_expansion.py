"""Paired, in-memory proof for Slice 5, runnable before or after registration."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_engine
from fight_moves import MoveDefinition, MoveIndex
from fight_moves.catalogue.power_punch_development import POWER_PUNCH_DEVELOPMENT
from fight_moves.catalogue.jab_development import JAB_DEVELOPMENT
from fight_moves.catalogue.kick_development import SLICE_5_KICKS
from fight_moves.catalogue.clinch_development import CLINCH_DEVELOPMENT
from analysis.compare_bottom_move_expansion import restore_definition
from analysis.generate_move_coverage_report import build_report, summarize_variety

SLICE_5 = POWER_PUNCH_DEVELOPMENT + JAB_DEVELOPMENT + SLICE_5_KICKS + CLINCH_DEVELOPMENT


def compare_expansion(reference_name, additions, label):
    """Compare fixed reviewed content with an appended batch in isolated memory."""
    reference = json.loads((ROOT / "analysis" / reference_name).read_text(encoding="utf-8"))["dump"]
    old_by_id = {row["move_id"]: restore_definition(MoveDefinition, row) for row in reference["moves"]}
    original = tuple(old_by_id[key] for key in reference["move_order"])
    reports = []
    for definitions in (original, original + additions):
        index = MoveIndex(definitions)
        with patch.multiple(fight_engine, MOVE_REGISTRY={m.move_id: m for m in definitions},
                            legal_moves=index.legal_moves):
            reports.append(build_report())
    before, after = reports
    missing = sorted(m.move_id for m in additions if m.move_id not in after["observed_move_ids"])
    failures = [f"{label} move absent from ordinary fights: {move_id}" for move_id in missing]
    mechanics_equal = before["mechanical_signatures"] == after["mechanical_signatures"]
    if not mechanics_equal:
        failures.append("Paired broad mechanical evidence changed")
    if after["mean_distinct_moves_per_fighter"] <= before["mean_distinct_moves_per_fighter"]:
        failures.append("Per-fighter move variety did not increase")
    metric_keys = summarize_variety({}, [], 0).keys()
    return {"fights_per_arm": 300, "additions": len(additions),
              "before": {key: before[key] for key in metric_keys},
              "after": {key: after[key] for key in metric_keys},
              "mechanics_equal": mechanics_equal, "missing": missing, "failures": failures}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "striking_move_expansion_comparison.json")
    args = parser.parse_args(argv)
    output = compare_expansion("move_registry_phase30_33.json", SLICE_5, "Slice 5")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))
    return int(bool(output["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
