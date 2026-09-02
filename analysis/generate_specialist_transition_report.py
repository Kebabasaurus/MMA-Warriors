"""Generate the deterministic full-fight specialist-transition report."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import build_specialist_transition_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds-per-matchup", type=int, default=240)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "analysis" / "fight_engine_specialist_transition_report.json",
    )
    args = parser.parse_args()
    payload = build_specialist_transition_report(max(1, args.seeds_per_matchup))
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "fights": payload["fight_count"],
        "diagnostics": payload["diagnostics"],
    }, indent=2))
    return 1 if any(payload["diagnostics"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
