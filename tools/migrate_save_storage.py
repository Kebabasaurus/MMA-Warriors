import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence import atomic_write_json_gzip, atomic_write_split_save, load_save_payload, read_json_text


def unique_destination(path):
    if not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def migrate_primary(path):
    data = load_save_payload(path)
    before = path.stat().st_size
    atomic_write_split_save(path, data)
    after = path.stat().st_size
    return before, after


def gzip_recovery_json(path, archive_root):
    data = json.loads(read_json_text(path))
    target = path.with_suffix(path.suffix + ".gz")
    target = unique_destination(target)
    atomic_write_json_gzip(target, data, compresslevel=3)
    archive_root.mkdir(parents=True, exist_ok=True)
    archived = archive_root / path.name
    archived = unique_destination(archived)
    shutil.move(str(path), str(archived))
    return target, archived


def main():
    parser = argparse.ArgumentParser(description="Split large primary saves and gzip recovery JSONs.")
    parser.add_argument("root", help="Save root to scan, for example dist/MMA Warriors/Saves")
    parser.add_argument("--archive-root", default="", help="Where original recovery JSON files should be moved.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    archive_root = Path(args.archive_root).resolve() if args.archive_root else root / "Migrated Plain JSON Originals"
    if not root.exists():
        raise SystemExit(f"Save root does not exist: {root}")

    primary_count = 0
    recovery_count = 0
    for path in sorted(root.rglob("*.json")):
        if path.name.endswith(".metadata"):
            continue
        if path.name == "savegame.json":
            before, after = migrate_primary(path)
            print(f"PRIMARY {path} {before:,} -> {after:,} bytes")
            primary_count += 1
            continue
        target, archived = gzip_recovery_json(path, archive_root)
        print(f"RECOVERY {path} -> {target} | original archived {archived}")
        recovery_count += 1
    print(f"Migrated primaries={primary_count}, recovery_json={recovery_count}")


if __name__ == "__main__":
    main()
