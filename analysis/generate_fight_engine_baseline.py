"""Generate the checked-in Phase 0 MMA fight-engine preservation baseline."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import (
    build_baseline,
    compare_to_accepted_calibration,
    compare_to_baseline,
    write_baseline,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-matchup", type=int, default=120)
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "fight_engine_baseline.json")
    parser.add_argument("--verify", type=Path, help="Compare current results with an existing baseline instead of overwriting it.")
    parser.add_argument("--exact-parity", action="store_true", help="Require every frozen fight signature to remain identical.")
    args = parser.parse_args()
    if args.verify:
        baseline = json.loads(args.verify.read_text(encoding="utf-8"))
        payload = build_baseline(int(baseline.get("seeds_per_matchup", args.seeds_per_matchup)))
        failures = compare_to_baseline(payload, baseline, exact_parity=args.exact_parity)
        failures.extend(compare_to_accepted_calibration(payload))
        print(json.dumps({
            "baseline": str(args.verify), "fights": payload["fight_count"],
            "overall": payload["groups"]["Overall"],
            "five_round": payload["groups"].get("Five Round", {}),
            "failures": failures,
        }, indent=2))
        return 1 if failures else 0
    payload = write_baseline(args.output, max(4, args.seeds_per_matchup))
    print(json.dumps({
        "output": str(args.output), "fights": payload["fight_count"],
        "overall": payload["groups"]["Overall"],
        "five_round": payload["groups"].get("Five Round", {}),
    }, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
