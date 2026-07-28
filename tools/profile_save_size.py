import gzip
import json
import sys
from pathlib import Path


def read_text(path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


def compact_size(value):
    return len(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def main(argv):
    for raw in argv[1:]:
        path = Path(raw)
        text = read_text(path)
        data = json.loads(text)
        print(f"\nPROFILE {path}")
        print(f"file_bytes={len(text.encode('utf-8')):,}")
        print(f"top_level_keys={len(data):,}")
        rows = sorted(
            ((compact_size(value), key, type(value).__name__) for key, value in data.items()),
            reverse=True,
        )
        for size, key, value_type in rows[:40]:
            print(f"{size:>13,}  {value_type:<8} {key}")


if __name__ == "__main__":
    main(sys.argv)
