"""Generate or verify the pre-move-expansion action-frequency baseline."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import build_action_baseline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-matchup", type=int, default=120)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "analysis" / "fight_engine_action_baseline.json",
    )
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    expected = None
    if args.verify:
        expected = json.loads(args.verify.read_text(encoding="utf-8"))
        seeds = int(expected.get("seeds_per_matchup", args.seeds_per_matchup))
    else:
        seeds = max(4, int(args.seeds_per_matchup))
    payload = build_action_baseline(seeds)
    if expected is not None:
        passed = payload == expected
        print(json.dumps({
            "baseline": str(args.verify), "fights": payload["fight_count"],
            "actions": len(payload["actions"]), "passed": passed,
        }, indent=2))
        return 0 if passed else 1
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "fights": payload["fight_count"],
        "actions": len(payload["actions"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
