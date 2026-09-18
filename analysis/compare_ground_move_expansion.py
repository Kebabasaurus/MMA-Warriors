"""Paired 300-fight evidence for the 44-move common-ground/wrestling slice."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.compare_striking_move_expansion import compare_expansion
from fight_moves.catalogue.bottom_submission_development import BOTTOM_SUBMISSION_DEVELOPMENT
from fight_moves.catalogue.wrestling_development import WRESTLING_DEVELOPMENT
from fight_moves.catalogue.ground_top_development import GROUND_TOP_DEVELOPMENT

SLICE_6 = WRESTLING_DEVELOPMENT + GROUND_TOP_DEVELOPMENT + BOTTOM_SUBMISSION_DEVELOPMENT


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "ground_move_expansion_comparison.json")
    args = parser.parse_args(argv)
    output = compare_expansion("move_registry_slice5.json", SLICE_6, "Slice 6")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output))
    return int(bool(output["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
