"""Paired complete-fight proof of increased bottom vocabulary at unchanged outcomes."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_engine
from fight_moves import MoveDefinition, DefenseDefinition, MoveIndex
from analysis.generate_move_coverage_report import build_report


def restore_definition(cls, record):
    record = dict(record)
    for key, value in record.items():
        if key in {"positions", "targets"}:
            record[key] = frozenset(value)
        elif isinstance(value, list):
            record[key] = tuple(value)
    return cls(**record)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "bottom_move_expansion_comparison.json")
    args = parser.parse_args(argv)
    reference = json.loads((ROOT / "analysis" / "move_registry_phase29.json").read_text(encoding="utf-8"))["dump"]
    by_id = {row["move_id"]: restore_definition(MoveDefinition, row) for row in reference["moves"]}
    moves = tuple(by_id[key] for key in reference["move_order"])
    defenses_by_id = {row["defense_id"]: restore_definition(DefenseDefinition, row) for row in reference["defenses"]}
    defenses = tuple(defenses_by_id[key] for key in reference["defense_order"])
    index = MoveIndex(moves)

    def legal_defenses(families, position):
        return tuple(d for d in defenses if position in d.positions and set(families).intersection(d.families))

    with patch.multiple(fight_engine, MOVE_REGISTRY=by_id, DEFENSE_REGISTRY=defenses_by_id,
                        legal_moves=index.legal_moves, legal_defenses=legal_defenses):
        before = build_report()
    after = build_report()
    before_variety = before["mean_distinct_bottom_moves_per_fighter"]
    after_variety = after["mean_distinct_bottom_moves_per_fighter"]
    failures = []
    if before["mechanical_signatures"] != after["mechanical_signatures"]:
        failures.append("Paired mechanical evidence changed")
    if after_variety <= before_variety:
        failures.append("Bottom-side move variety did not increase")
    report = {"fights_per_arm": 300, "before_mean_bottom_moves": before_variety,
              "after_mean_bottom_moves": after_variety,
              "paired_mechanics_equal": before["mechanical_signatures"] == after["mechanical_signatures"],
              "failures": failures}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
