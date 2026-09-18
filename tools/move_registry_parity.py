"""Capture and verify the ordered move registry before structural changes.

Capture is explicit and refuses to overwrite an existing reference. Verification
never writes files. Sets are sorted, while tuple/list order remains significant.
"""

import argparse
from dataclasses import asdict
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_REFERENCE = ROOT / "analysis" / "move_registry_parity.json"
TARGETS = ("", "head", "body", "leg")


def normalize(value):
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, (set, frozenset)):
        return sorted(normalize(item) for item in value)
    if isinstance(value, (tuple, list)):
        return [normalize(item) for item in value]
    return value


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_dump(registry):
    """Include definitions, definition order, and the entire supported key space."""
    actions = sorted(registry.KNOWN_PARENT_ACTIONS)
    positions = sorted(registry.ALL_POSITIONS)
    return {
        "schema_version": getattr(registry, "REGISTRY_SCHEMA_VERSION", 1),
        "move_order": [move.move_id for move in registry.MOVE_DEFINITIONS],
        "moves": sorted((normalize(asdict(move)) for move in registry.MOVE_DEFINITIONS),
                        key=lambda row: row["move_id"]),
        "defense_order": [defense.defense_id for defense in registry.DEFENSE_DEFINITIONS],
        "defenses": sorted((normalize(asdict(defense)) for defense in registry.DEFENSE_DEFINITIONS),
                           key=lambda row: row["defense_id"]),
        "legal_moves": [
            {"action": action, "position": position, "target": target,
             "ids": [move.move_id for move in registry.legal_moves(action, position, target)]}
            for action in actions for position in positions for target in TARGETS
        ],
    }


def envelope(dump, source_ref):
    return {"source_ref": source_ref, "sha256": hashlib.sha256(canonical_bytes(dump)).hexdigest(),
            "dump": dump}


def compare(reference, actual):
    expected = reference["dump"]
    failures = []
    if reference["sha256"] != hashlib.sha256(canonical_bytes(expected)).hexdigest():
        failures.append("Reference checksum does not match its dump")
    for key in sorted(set(expected) | set(actual)):
        if expected.get(key) != actual.get(key):
            failures.append(f"Registry parity changed: {key}")
    return failures


def compare_legacy(reference, actual):
    """Allow additions while requiring every historical record and order to survive."""
    from copy import deepcopy
    projected = deepcopy(actual)
    original = reference["dump"]
    move_ids, defense_ids = set(original["move_order"]), set(original["defense_order"])
    projected["move_order"] = [key for key in actual["move_order"] if key in move_ids]
    projected["moves"] = [row for row in actual["moves"] if row["move_id"] in move_ids]
    projected["defense_order"] = [key for key in actual["defense_order"] if key in defense_ids]
    projected["defenses"] = [row for row in actual["defenses"] if row["defense_id"] in defense_ids]
    original_keys = {(r["action"], r["position"], r["target"]) for r in original["legal_moves"]}
    projected["legal_moves"] = [dict(row, ids=[key for key in row["ids"] if key in move_ids])
                               for row in actual["legal_moves"]
                               if (row["action"], row["position"], row["target"]) in original_keys]
    return compare(reference, projected)


def compare_followup_update(reference, actual, manifest):
    """Permit only explicit successor updates bound to an untouched source dump.

The manifest is a reviewed document, never inferred from the current registry.
Its source_sha256 is the source envelope's canonical dump digest, checked before
any expected-data transformation. This mode does not permit content additions.
"""
    from copy import deepcopy
    if not isinstance(reference, dict) or not isinstance(reference.get("dump"), dict):
        return ["Malformed source reference"]
    source = reference["dump"]
    source_hash = hashlib.sha256(canonical_bytes(source)).hexdigest()
    if reference.get("sha256") != source_hash:
        return ["Reference checksum does not match its dump"]
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "source_sha256", "updates"}:
        return ["Manifest must contain only schema_version, source_sha256 and updates"]
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        return ["Unsupported follow-up manifest schema_version"]
    if manifest["source_sha256"] != source_hash:
        return ["Follow-up manifest does not match the source checksum"]
    updates = manifest["updates"]
    if not isinstance(updates, dict) or not updates:
        return ["Follow-up manifest updates must be a nonempty object"]
    rows = source.get("moves")
    if not isinstance(rows, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("move_id"), str)
            or not isinstance(row.get("follow_ups"), list) for row in rows):
        return ["Malformed source move records"]
    by_id = {row["move_id"]: row for row in rows}
    source_order = source.get("move_order")
    if (not isinstance(source_order, list) or any(not isinstance(key, str) for key in source_order)
            or len(by_id) != len(rows) or len(source_order) != len(by_id)
            or set(source_order) != set(by_id)):
        return ["Malformed source move identities/order"]
    failures = []
    for move_id, update in updates.items():
        if not isinstance(move_id, str) or move_id not in by_id:
            failures.append(f"Unknown follow-up source ID: {move_id!r}")
            continue
        if not isinstance(update, dict) or set(update) != {"follow_ups"}:
            failures.append(f"{move_id}: update must contain only follow_ups")
            continue
        successors = update["follow_ups"]
        if not isinstance(successors, list) or any(not isinstance(key, str) for key in successors):
            failures.append(f"{move_id}: follow_ups must be a list of move IDs")
            continue
        if len(successors) > 3 or len(set(successors)) != len(successors):
            failures.append(f"{move_id}: follow_ups must contain at most three unique IDs")
        unknown = set(successors) - by_id.keys()
        if unknown:
            failures.append(f"{move_id}: unknown successor IDs: {sorted(unknown)}")
        if move_id in successors:
            failures.append(f"{move_id}: self-follow-up is not allowed")
        if successors == by_id[move_id]["follow_ups"]:
            failures.append(f"{move_id}: no-op update is not allowed")
    if failures:
        return failures
    expected = deepcopy(source)
    for row in expected["moves"]:
        if row["move_id"] in updates:
            row["follow_ups"] = list(updates[row["move_id"]]["follow_ups"])
    if not isinstance(actual, dict):
        return ["Actual registry dump must be an object"]
    # All other records, fields, order and ordered lookup keys remain exact.
    return compare(envelope(expected, reference.get("source_ref", "")), actual)


def compare_deprecation_update(reference, actual):
    """Allow only schema 1 -> 2 plus a literal deprecated=False on every move.

    This separate migration mode never projects away retirement metadata or
    relaxes the ordinary, legacy or approved-successor comparison contracts.
    """
    from copy import deepcopy
    if not isinstance(reference, dict) or not isinstance(reference.get("dump"), dict):
        return ["Malformed source reference"]
    source = reference["dump"]
    if reference.get("sha256") != hashlib.sha256(canonical_bytes(source)).hexdigest():
        return ["Reference checksum does not match its dump"]
    if type(source.get("schema_version")) is not int or source["schema_version"] != 1:
        return ["Deprecation migration requires a schema-1 source"]
    required_dump_fields = {"schema_version", "move_order", "moves", "defense_order", "defenses", "legal_moves"}
    if set(source) != required_dump_fields:
        return ["Malformed schema-1 registry fields"]
    # This is the fixed schema-1 contract, not the current runtime dataclass:
    # adding future fields must not silently broaden this migration's authority.
    move_fields = {
        "move_id", "name", "parent_action", "positions", "targets", "attack_skills", "defense_skills",
        "preferred_styles", "minimum_skill", "energy", "miss_risk", "counter_risk", "follow_ups", "tags",
        "side", "range_band", "defense_families", "entry_family", "finish_positions", "attack_path",
        "failure_outcomes", "components",
    }
    rows, order = source["moves"], source["move_order"]
    if (not isinstance(rows, list) or not rows
            or any(not isinstance(row, dict) or set(row) != move_fields
                   or not isinstance(row["move_id"], str) for row in rows)):
        return ["Malformed schema-1 move fields"]
    ids = [row["move_id"] for row in rows]
    if (len(set(ids)) != len(ids) or not isinstance(order, list)
            or any(not isinstance(key, str) for key in order)
            or len(order) != len(ids) or set(order) != set(ids)):
        return ["Malformed schema-1 move identities/order"]
    if not isinstance(actual, dict):
        return ["Actual registry dump must be an object"]
    if type(actual.get("schema_version")) is not int or actual["schema_version"] != 2:
        return ["Deprecation migration requires a schema-2 destination"]
    actual_rows = actual.get("moves")
    if (not isinstance(actual_rows, list) or len(actual_rows) != len(rows)
            or any(not isinstance(row, dict) or set(row) != move_fields | {"deprecated"}
                   or type(row["deprecated"]) is not bool or row["deprecated"] is not False
                   for row in actual_rows)):
        return ["Every destination move must add only the literal boolean deprecated=False"]
    expected = deepcopy(source)
    expected["schema_version"] = 2
    for row in expected["moves"]:
        row["deprecated"] = False
    # Canonical JSON comparison also distinguishes 0/False and 1/1.0 in fields
    # unrelated to this migration; Python's permissive numeric equality cannot.
    return [f"Deprecation migration changed an unapproved field: {key}"
            for key in sorted(set(expected) | set(actual))
            if key not in expected or key not in actual
            or canonical_bytes(expected[key]) != canonical_bytes(actual[key])]


def registry_at_ref(ref):
    """Load the historical registry without modifying the working checkout."""
    def source(path):
        return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT).decode("utf-8")

    # The historical registry imports constants. Refuse mixed-revision evidence.
    if source("constants.py").replace("\r\n", "\n") != (ROOT / "constants.py").read_text(encoding="utf-8"):
        raise ValueError("Historical constants differ; capture from a checkout of the requested revision")
    module = types.ModuleType("_historical_move_registry")
    sys.modules[module.__name__] = module
    try:
        exec(compile(source("fight_moves.py"), f"{ref}:fight_moves.py", "exec"), module.__dict__)
    finally:
        del sys.modules[module.__name__]
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture-ref", help="Capture the original registry from a git revision")
    mode.add_argument("--verify", type=Path, help="Verify the current registry against this reference")
    mode.add_argument("--verify-legacy", type=Path, help="Check the original records/order while allowing additions")
    mode.add_argument("--verify-followups", type=Path, help="Verify only manifest-approved successor changes against this exact source")
    mode.add_argument("--verify-deprecation", type=Path, help="Verify only schema-1 to schema-2 plus deprecated=False on every move")
    mode.add_argument("--capture-current", action="store_true", help="Capture a separately reviewed content expansion snapshot")
    parser.add_argument("--followup-manifest", type=Path, help="Reviewed successor-only manifest for --verify-followups")
    parser.add_argument("--output", type=Path, default=DEFAULT_REFERENCE)
    args = parser.parse_args(argv)
    if bool(args.verify_followups) != bool(args.followup_manifest):
        parser.error("--verify-followups and --followup-manifest must be supplied together")
    if args.capture_current:
        if args.output.resolve() == DEFAULT_REFERENCE.resolve():
            parser.error("Content snapshots must use a separate output; the historical reference is immutable")
        payload = envelope(build_dump(importlib.import_module("fight_moves")), "reviewed-content-expansion")
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(payload))
        print(json.dumps({"output": str(args.output), "sha256": payload["sha256"]}))
        return 0
    if args.capture_ref:
        revision = subprocess.check_output(
            ["git", "rev-parse", args.capture_ref], cwd=ROOT, text=True).strip()
        payload = envelope(build_dump(registry_at_ref(revision)), revision)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(payload))
        print(json.dumps({"output": str(args.output), "sha256": payload["sha256"]}))
        return 0
    reference = json.loads((args.verify or args.verify_legacy or args.verify_followups or args.verify_deprecation).read_text(encoding="utf-8"))
    actual = build_dump(importlib.import_module("fight_moves"))
    if args.verify_deprecation:
        failures = compare_deprecation_update(reference, actual)
    elif args.verify_followups:
        manifest = json.loads(args.followup_manifest.read_text(encoding="utf-8"))
        failures = compare_followup_update(reference, actual, manifest)
    else:
        failures = (compare_legacy if args.verify_legacy else compare)(reference, actual)
    print(json.dumps({"moves": len(actual["moves"]), "defenses": len(actual["defenses"]),
                      "lookup_keys": len(actual["legal_moves"]), "failures": failures}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
