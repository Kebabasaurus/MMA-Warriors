import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence import load_save_payload


def summarize(data):
    summary = {}
    for key, value in data.items():
        if isinstance(value, (list, dict, str)):
            summary[key] = len(value)
        else:
            summary[key] = value
    return summary


def main():
    parser = argparse.ArgumentParser(description="Compare two save payloads after hydrating external blocks.")
    parser.add_argument("expected")
    parser.add_argument("actual")
    args = parser.parse_args()

    expected = load_save_payload(Path(args.expected))
    actual = load_save_payload(Path(args.actual))
    if expected == actual:
        print("MATCH: hydrated save payloads are identical.")
        print(f"top_level_keys={len(actual)}")
        for key in ("result_index", "result_records", "ai_event_archive", "player_event_archive", "promotions", "combat_sport_worlds", "roster", "free_agents"):
            value = actual.get(key)
            if isinstance(value, (list, dict)):
                print(f"{key}={len(value):,}")
        return

    expected_keys = set(expected)
    actual_keys = set(actual)
    print("MISMATCH: hydrated save payloads differ.")
    print(f"missing_keys={sorted(expected_keys - actual_keys)}")
    print(f"extra_keys={sorted(actual_keys - expected_keys)}")
    for key in sorted(expected_keys & actual_keys):
        if expected[key] != actual[key]:
            print(f"first_different_key={key}")
            print(f"expected_summary={summarize({key: expected[key]})[key]}")
            print(f"actual_summary={summarize({key: actual[key]})[key]}")
            break
    raise SystemExit(1)


if __name__ == "__main__":
    main()
