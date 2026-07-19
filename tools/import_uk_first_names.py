"""Convert the supplied UK name directory into a compact packaged game asset."""
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path.home() / "Downloads" / "UK_First_Names_Directory_with_Gender.txt"
DEFAULT_OUTPUT = ROOT / "assets" / "uk_first_names.json"
ROW = re.compile(r"^([FMN])\d{4}\.\s+(.+?)\s*$")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    groups = {"F": [], "M": [], "N": []}
    for line in args.source.read_text(encoding="utf-8-sig").splitlines():
        match = ROW.match(line)
        if match:
            code, name = match.groups()
            if name not in groups[code]:
                groups[code].append(name)
    expected = {"F": 712, "M": 744, "N": 54}
    counts = {key: len(value) for key, value in groups.items()}
    if counts != expected:
        raise ValueError(f"Directory counts did not match its manifest: expected {expected}, read {counts}")
    payload = {
        "schema": 1,
        "source": args.source.name,
        "female": groups["F"],
        "male": groups["M"],
        "neutral": groups["N"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: {counts}")


if __name__ == "__main__":
    main()
