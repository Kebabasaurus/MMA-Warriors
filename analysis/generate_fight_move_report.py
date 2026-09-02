"""Generate the deterministic move-usage and registry-safety release report."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import build_move_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-matchup", type=int, default=20)
    parser.add_argument("--minimum-group-sample", type=int, default=30)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "analysis" / "fight_engine_move_report.json",
    )
    args = parser.parse_args()
    payload = build_move_report(
        max(1, int(args.seeds_per_matchup)), max(1, int(args.minimum_group_sample)),
    )
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "fights": payload["fight_count"],
        "registered_moves": payload["registered_move_count"],
        "observed_moves": payload["observed_move_count"],
        "diagnostics": {
            key: len(value) for key, value in payload["diagnostics"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
