"""Read-only, explicitly opt-in calibration of unfinished specialist mechanics.

This is not a release baseline generator. It never writes or accepts a reference.
Normal game instances do not enable the experimental switch.
"""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import (
    FightAuditHarness, build_baseline, compare_to_accepted_calibration, compare_to_baseline,
)


def main():
    reference = ROOT / "analysis" / "fight_engine_baseline.json"
    baseline = json.loads(reference.read_text(encoding="utf-8"))
    with patch.object(FightAuditHarness, "_experimental_specialist_entries", True, create=True):
        result = build_baseline(int(baseline["seeds_per_matchup"]))
    failures = compare_to_baseline(result, baseline)
    failures.extend(compare_to_accepted_calibration(result))
    print(json.dumps({
        "candidate": "current experimental specialist-entry mechanics",
        "experimental_only": True,
        "engine_sha256": hashlib.sha256((ROOT / "fight_engine.py").read_bytes()).hexdigest(),
        "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "fights": result["fight_count"],
        "overall": result["groups"]["Overall"],
        "failures": failures,
    }, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
