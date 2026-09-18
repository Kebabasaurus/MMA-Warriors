"""Report median lookup time at current and fourfold catalogue size."""
from dataclasses import replace
import json
from pathlib import Path
from statistics import median
import sys
from timeit import repeat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_moves import MOVE_DEFINITIONS, MoveIndex


def main():
    results = []
    for size in (len(MOVE_DEFINITIONS), max(800, len(MOVE_DEFINITIONS))):
        definitions = tuple(replace(MOVE_DEFINITIONS[index % len(MOVE_DEFINITIONS)],
                                    move_id=f"benchmark_{index}") for index in range(size))
        index = MoveIndex(definitions)
        elapsed = median(repeat(lambda: index.legal_moves("power_punch", "range", "head"),
                                number=200_000, repeat=7))
        results.append({"moves": len(definitions),
                        "microseconds_per_lookup": round(elapsed / 200_000 * 1e6, 3)})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
