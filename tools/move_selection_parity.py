"""Capture strict pre-refactor selection semantics from complete deterministic bouts.

Default corpus: one bout for every move_report_specs entry (currently 44). The
registry digest binds the complete build_dump, including ordered legal pools.
Each bout hashes the entire ordered native trace, complete move/defense payloads,
all sequence/chain-prefixed trace fields, and all audit mechanics fields except
the redundant audit signature. Resolver prose (events[*].result) is excluded
from the mechanics projection only; native trace prose remains protected. No
timing or object-address fields are introduced. Stable synthetic fighter IDs,
names, simulation ticks, fixture records and full specs are retained, not erased.

This supplements registry parity and the full result/action corpus. It does not
replace those gates. Capture refuses overwrite; verify never writes.
"""
import argparse
import ast
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import inspect
from pathlib import Path
import random
import sys
import textwrap
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_moves
import fight_engine
from fight_engine_audit import FightAuditHarness, move_report_specs, run_audited_fight, synthetic_fighter
from tools.move_registry_parity import build_dump, canonical_bytes, normalize, compare_deprecation_update

SEED_BASE = 9_310_000
# These immutable captures predate f62cf08's two portrait-only Fighter fields.
# A historical reconstruction is explicit and never applies to new captures.
PRE_PORTRAIT_REFERENCES = frozenset({
    "988689fc6615e8369868ae6644cae299681e52073074c88fd65c4d7873eded7f",
    "d15acf267482cef7d44139784a66838349f5ebb7715f961de6ffce36857800fa",
})


def historical_fixture_record(fighter):
    """Reconstruct the frozen schema; retain every original field unchanged."""
    record = asdict(fighter)
    if (type(record.get('portrait_version')) is not int or record['portrait_version'] != 0
            or type(record.get('portrait_identity')) is not dict or record['portrait_identity']):
        raise ValueError('Historical fixtures require untouched default portrait fields')
    del record['portrait_version']
    del record['portrait_identity']
    # These save-only fields were added after both recognized frozen envelopes.
    # Never hide actual progression, an injury anchor or an unexpected type.
    if (type(record.get('trait_progress')) is not dict or record['trait_progress']
            or type(record.get('trait_history')) is not list or record['trait_history']
            or record.get('trait_injury_baseline') is not None):
        raise ValueError('Historical fixtures require untouched default trait fields')
    del record['trait_progress']
    del record['trait_history']
    del record['trait_injury_baseline']
    # Development-loan return boundaries were added after the immutable
    # phase-31 captures.  They are save fields, not fight-selection inputs;
    # permit omission only for their exact zero defaults so the old fixture
    # remains byte-for-byte reproducible without hiding live loan state.
    for field in ('loan_return_month', 'loan_return_week'):
        if type(record.get(field)) is not int or record[field] != 0:
            raise ValueError('Historical fixtures require untouched default loan fields')
        del record[field]
    return record


def validate_historical_reference(reference):
    if (not isinstance(reference, dict) or compare_snapshot(reference, reference.get('snapshot'))
            or reference.get('sha256') not in PRE_PORTRAIT_REFERENCES):
        raise ValueError('Historical reconstruction requires a recognized immutable reference')


@contextmanager
def historical_wording():
    """Reconstruct frozen display copy only; strict native trace hashes still apply."""
    with ExitStack() as stack:
        for name in ('commentary_defense_clause', 'exchange_display_move', 'evidence_driven_exchange_pool'):
            source = textwrap.dedent(inspect.getsource(getattr(fight_engine.FightEngineMixin, name)))
            tree = ast.parse(source)
            function = tree.body[0]
            static = any(isinstance(node, ast.Name) and node.id == 'staticmethod'
                         for node in function.decorator_list)
            function.decorator_list = []
            if name == 'commentary_defense_clause':
                targets = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                           and any(isinstance(target, ast.Name) and target.id == 'options' for target in node.targets)]
                if (len(targets) != 1 or not isinstance(targets[0], ast.Tuple)
                        or len(targets[0].elts) != 15 or not isinstance(targets[0].elts[1], ast.Starred)):
                    raise ValueError('Historical defense wording structure changed')
                targets[0].elts = targets[0].elts[:2]
            elif name == 'exchange_display_move':
                targets = [node for node in function.body if isinstance(node, ast.If)
                           and any(isinstance(value, ast.Constant) and value.value == 'single_jab'
                                   for value in ast.walk(node.test))]
                if len(targets) != 1:
                    raise ValueError('Historical jab wording structure changed')
                function.body.remove(targets[0])
            else:
                targets = [value for node in ast.walk(tree) if isinstance(node, ast.Dict)
                           for key, value in zip(node.keys, node.values)
                           if isinstance(key, ast.Constant) and key.value == 'survived']
                if len(targets) != 2 or any(not isinstance(value, ast.Tuple) or len(value.elts) != 25 for value in targets):
                    raise ValueError('Historical survival wording structure changed')
                for value in targets:
                    value.elts = value.elts[:8]
            ast.fix_missing_locations(tree)
            namespace = dict(vars(fight_engine))
            exec(compile(tree, '<frozen-selection-wording>', 'exec'), namespace)
            replacement = staticmethod(namespace[name]) if static else namespace[name]
            stack.enter_context(patch.object(fight_engine.FightEngineMixin, name, replacement))
        yield


def digest(value):
    return hashlib.sha256(canonical_bytes(normalize(value))).hexdigest()


def project_audit(audit):
    """Keep every payload field and trace ordering; never select a small allow-list."""
    trace = deepcopy(audit["trace"])
    mechanics = deepcopy({key: value for key, value in audit.items() if key not in {"trace", "signature"}})
    mechanics["events"] = [{key: value for key, value in event.items() if key != "result"}
                           for event in mechanics["events"]]
    moves, defenses, sequences = [], [], []
    for index, event in enumerate(trace):
        if "move" in event:
            moves.append({"trace_index": index, "payload": deepcopy(event["move"])})
        if "defense" in event:
            defenses.append({"trace_index": index, "payload": deepcopy(event["defense"])})
        sequence = {key: deepcopy(value) for key, value in event.items()
                    if key.startswith(("sequence", "chain")) or key == "move_sequence"}
        if sequence:
            sequences.append({"trace_index": index, "fields": sequence})
    return {"trace": trace, "mechanics": mechanics, "moves": moves,
            "defenses": defenses, "sequences": sequences}


def bout_fingerprints(audit):
    projection = project_audit(audit)
    return {**{f"{key}_sha256": digest(value) for key, value in projection.items()},
            "trace_events": len(projection["trace"]),
            "move_payloads": len(projection["moves"]),
            "defense_payloads": len(projection["defenses"]),
            "sequence_events": len(projection["sequences"])}


def build_snapshot(seeds_per_matchup=1, *, historical_fixture_reference=None, historical_wording_reference=None):
    if type(seeds_per_matchup) is not int or not 1 <= seeds_per_matchup < 10_000:
        raise ValueError("seeds_per_matchup must be an integer from 1 to 9999")
    if historical_fixture_reference is not None:
        validate_historical_reference(historical_fixture_reference)
    if historical_wording_reference is not None:
        validate_historical_reference(historical_wording_reference)
    fixture_record = historical_fixture_record if historical_fixture_reference is not None else asdict
    original_rng = random.getstate()
    scopes = ExitStack()
    try:
        if historical_wording_reference is not None:
            scopes.enter_context(historical_wording())
        specs = deepcopy(move_report_specs())
        engine = FightAuditHarness()
        bouts = []
        for spec_index, spec in enumerate(specs):
            a = synthetic_fighter(f"Move audit {spec['id']} A", spec["a_level"],
                                  spec["a_style"], spec["a_behaviour"], 0)
            b = synthetic_fighter(f"Move audit {spec['id']} B", spec["b_level"],
                                  spec["b_style"], spec["b_behaviour"], 1)
            a.stance = spec.get("a_stance", a.stance)
            b.stance = spec.get("b_stance", b.stance)
            fixture_hash = digest({"a": fixture_record(a), "b": fixture_record(b), "fight": spec["fight"]})
            for seed_index in range(seeds_per_matchup):
                seed = SEED_BASE + spec_index * 10_000 + seed_index
                audit = run_audited_fight(engine, a, b, seed, deepcopy(spec["fight"]))
                bouts.append({"case_id": f"{spec['id']}:{seed_index}", "seed": seed,
                              "fixture_sha256": fixture_hash, **bout_fingerprints(audit)})
        return {"schema_version": 1, "projection_version": 1,
                "registry_sha256": digest(build_dump(fight_moves)),
                "seed_base": SEED_BASE, "seeds_per_matchup": seeds_per_matchup,
                "specs": normalize(specs), "fight_count": len(bouts), "bouts": bouts}
    finally:
        scopes.close()
        random.setstate(original_rng)


def snapshot_envelope(snapshot):
    return {"sha256": digest(snapshot), "snapshot": deepcopy(snapshot)}


def compare_snapshot(reference, actual):
    if not isinstance(reference, dict) or set(reference) != {"sha256", "snapshot"}:
        return ["Malformed selection reference envelope"]
    expected = reference["snapshot"]
    if not isinstance(expected, dict) or reference["sha256"] != digest(expected):
        return ["Selection reference checksum does not match its snapshot"]
    if not isinstance(actual, dict):
        return ["Actual selection snapshot must be an object"]
    failures = []
    for key in sorted(set(expected) | set(actual)):
        if key not in expected or key not in actual or expected[key] != actual[key]:
            failures.append(f"Selection parity changed: {key}")
    return failures


def compare_snapshot_deprecation(reference, actual, registry_reference, current_registry_dump):
    """Rebind only a verified schema-1 -> schema-2 registry digest.

    The original selection envelope is checked before any transformation, and
    both snapshots remain bound to their exact source/destination registry dumps.
    No bout, fixture, trace, payload or sequence fingerprint may change.
    """
    failures = compare_snapshot(reference, reference.get("snapshot") if isinstance(reference, dict) else None)
    if failures:
        return failures
    failures = compare_deprecation_update(registry_reference, current_registry_dump)
    if failures:
        return [f"Selection registry migration rejected: {failure}" for failure in failures]
    if reference["snapshot"].get("registry_sha256") != digest(registry_reference["dump"]):
        return ["Selection reference is not bound to the supplied schema-1 registry"]
    current_registry_hash = digest(current_registry_dump)
    if not isinstance(actual, dict) or actual.get("registry_sha256") != current_registry_hash:
        return ["Actual selection snapshot is not bound to the current schema-2 registry"]
    expected = deepcopy(reference["snapshot"])
    expected["registry_sha256"] = current_registry_hash
    return compare_snapshot(snapshot_envelope(expected), actual)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", type=Path, help="Create a new reviewed pre-refactor snapshot")
    mode.add_argument("--verify", type=Path, help="Strict read-only verification")
    parser.add_argument("--verify-deprecation-from", type=Path,
                        help="With --verify only: approve the exact schema-1 registry's deprecated=False migration")
    parser.add_argument("--seeds-per-matchup", type=int, default=1)
    parser.add_argument("--historical-portrait-fixtures", action="store_true",
                        help="Verify only: reconstruct the recognized pre-portrait fixture schema")
    parser.add_argument("--historical-wording", action="store_true",
                        help="Verify only: reconstruct the recognized frozen jab/survival/defense copy")
    args = parser.parse_args(argv)
    if args.verify_deprecation_from and not args.verify:
        parser.error("--verify-deprecation-from requires --verify")
    if args.historical_portrait_fixtures and not args.verify:
        parser.error("--historical-portrait-fixtures requires --verify")
    if args.historical_wording and not args.verify:
        parser.error("--historical-wording requires --verify")
    if args.capture and args.capture.exists():
        parser.error("Capture refuses to overwrite an existing reference")
    reference = json.loads(args.verify.read_text(encoding="utf-8")) if args.verify else None
    options = {}
    if args.historical_portrait_fixtures:
        options['historical_fixture_reference'] = reference
    if args.historical_wording:
        options['historical_wording_reference'] = reference
    snapshot = build_snapshot(args.seeds_per_matchup, **options)
    if args.capture:
        with args.capture.open("xb") as stream:
            stream.write(canonical_bytes(snapshot_envelope(snapshot)))
        print(json.dumps({"output": str(args.capture), "fights": snapshot["fight_count"],
                          "sha256": digest(snapshot)}))
        return 0
    if args.verify_deprecation_from:
        registry_reference = json.loads(args.verify_deprecation_from.read_text(encoding="utf-8"))
        failures = compare_snapshot_deprecation(reference, snapshot, registry_reference, build_dump(fight_moves))
    else:
        failures = compare_snapshot(reference, snapshot)
    print(json.dumps({"fights": snapshot["fight_count"], "failures": failures}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
