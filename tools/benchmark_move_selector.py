"""Repeatable 800-move selector profiling over complete, disposable MMA fights.

The reported percentage is selector cumulative time divided by simulate_fight
cumulative time in the same high-resolution cProfile sample. Profiling overhead is included;
this diagnostic is not an unprofiled player-latency or release-calibration claim.
"""
import argparse
import cProfile
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import pstats
import random
from statistics import median
import sys
from time import perf_counter, process_time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_engine
from fight_engine_audit import FightAuditHarness, fight_signature, move_report_specs, run_audited_fight, synthetic_fighter
from fight_moves import MOVE_DEFINITIONS, MoveIndex

TARGET_MOVE_COUNT = 800
MAXIMUM_SELECTOR_SHARE_PCT = 15.0


def _json_default(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"Unexpected fingerprint value: {type(value).__name__}")


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=_json_default,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def expanded_definitions(original):
    """Preserve original objects and append evenly distributed immutable clones."""
    original = tuple(original)
    if not original or len(original) > TARGET_MOVE_COUNT:
        raise ValueError("Expected a nonempty catalogue containing at most 800 moves")
    additions = tuple(replace(original[i % len(original)], move_id=f"benchmark_selector_{i:04d}")
                      for i in range(TARGET_MOVE_COUNT - len(original)))
    definitions = original + additions
    if len({m.move_id for m in definitions}) != TARGET_MOVE_COUNT:
        raise ValueError("Benchmark clone IDs collide with an existing move")
    if not all(a is b for a, b in zip(original, definitions)):
        raise AssertionError("Benchmark replaced an original definition")
    return definitions


def _fixtures(fight_count):
    specs = move_report_specs()
    fixtures = []
    for index in range(fight_count):
        spec_index, seed_index = index % len(specs), index // len(specs)
        spec = specs[spec_index]
        a = synthetic_fighter(f"Selector benchmark {spec['id']} A", spec["a_level"],
                              spec["a_style"], spec["a_behaviour"], 0)
        b = synthetic_fighter(f"Selector benchmark {spec['id']} B", spec["b_level"],
                              spec["b_style"], spec["b_behaviour"], 1)
        a.stance = spec.get("a_stance", a.stance)
        b.stance = spec.get("b_stance", b.stance)
        fixtures.append((a, b, 9_310_000 + spec_index * 10_000 + seed_index, dict(spec["fight"])))
    return fixtures


def _function_stats(stats, name):
    rows = [(key, row) for key, row in stats.stats.items()
            if Path(key[0]).resolve() == ROOT / "fight_engine.py" and key[2] == name]
    if len(rows) != 1:
        raise AssertionError(f"Expected exactly one profiled fight_engine.{name}, found {len(rows)}")
    _key, (primitive_calls, calls, own_time, cumulative_time, _callers) = rows[0]
    return {"calls": calls, "primitive_calls": primitive_calls,
            "self_seconds": own_time, "cumulative_seconds": cumulative_time}


def benchmark(fight_count=44, repeats=3):
    if fight_count < 1 or repeats < 1:
        raise ValueError("Fight count and repeats must be positive")
    original = tuple(MOVE_DEFINITIONS)
    original_fingerprint = _fingerprint([asdict(m) for m in original])
    original_registry = fight_engine.MOVE_REGISTRY
    original_lookup = fight_engine.legal_moves
    registry_fingerprint = _fingerprint({key: asdict(value) for key, value in original_registry.items()})
    rng_before = random.getstate()
    definitions = expanded_definitions(original)
    expanded_fingerprint = _fingerprint([asdict(m) for m in definitions])
    index = MoveIndex(definitions)
    fixtures = _fixtures(fight_count)
    fighters_before = _fingerprint([(asdict(a), asdict(b), seed, fight) for a, b, seed, fight in fixtures])
    samples = []
    try:
        with patch.multiple(fight_engine, MOVE_REGISTRY={m.move_id: m for m in definitions},
                            legal_moves=index.legal_moves):
            for repeat_index in range(repeats):
                engine = FightAuditHarness()
                # Use cProfile's high-resolution default timer. On Windows,
                # process_time may advance in 15.625 ms increments and cannot
                # reliably attribute the many tiny selector helper calls. CPU
                # time remains a separate whole-sample diagnostic below.
                profiler = cProfile.Profile()
                signatures = []
                wall_start, cpu_start = perf_counter(), process_time()
                for a, b, seed, fight in fixtures:
                    # Fixture creation, index construction and result hashing are
                    # outside the profiler. Full simulation and its audit wrapper
                    # remain intact; the denominator excludes the wrapper itself.
                    result = profiler.runcall(run_audited_fight, engine, a, b, seed, fight)
                    signatures.append(fight_signature(result))
                cpu_elapsed, wall_elapsed = process_time() - cpu_start, perf_counter() - wall_start
                stats = pstats.Stats(profiler)
                selector = _function_stats(stats, "select_exchange_move")
                simulation = _function_stats(stats, "simulate_fight")
                if simulation["calls"] != fight_count or simulation["cumulative_seconds"] <= 0:
                    raise AssertionError("Profile did not contain the requested complete fights")
                ratio = 100 * selector["cumulative_seconds"] / simulation["cumulative_seconds"]
                samples.append({"sample": repeat_index + 1, "fights": fight_count,
                                "wall_seconds": wall_elapsed, "cpu_seconds": cpu_elapsed,
                                "selector": selector, "simulation": simulation,
                                "selector_share_pct": ratio,
                                "mechanical_signature_sha256": _fingerprint(signatures)})
    finally:
        rng_unchanged = random.getstate() == rng_before
        random.setstate(rng_before)
        if fight_engine.MOVE_REGISTRY is not original_registry or fight_engine.legal_moves is not original_lookup:
            raise AssertionError("Benchmark failed to restore registry/lookup globals")
        if _fingerprint([asdict(m) for m in original]) != original_fingerprint:
            raise AssertionError("Benchmark mutated an original definition")
        if _fingerprint({key: asdict(value) for key, value in original_registry.items()}) != registry_fingerprint:
            raise AssertionError("Benchmark mutated the original registry")
        if _fingerprint([asdict(m) for m in definitions]) != expanded_fingerprint:
            raise AssertionError("Benchmark mutated an expanded definition")
        if _fingerprint([(asdict(a), asdict(b), seed, fight) for a, b, seed, fight in fixtures]) != fighters_before:
            raise AssertionError("Benchmark mutated its source fighter fixtures")
        if not rng_unchanged:
            raise AssertionError("Benchmark consumed caller RNG (state has been restored)")
    if len({sample["mechanical_signature_sha256"] for sample in samples}) != 1:
        raise AssertionError("Repeated fixture corpus changed mechanical outcomes")
    share = median(sample["selector_share_pct"] for sample in samples)
    return {"scope": "High-resolution cProfile diagnostic; full disposable bouts, no career loading",
            "python": platform.python_version(), "platform": platform.system(),
            "original_moves": len(original), "profiled_moves": len(definitions),
            "original_registry_sha256": original_fingerprint,
            "expanded_registry_sha256": expanded_fingerprint,
            "fixture_sha256": fighters_before, "fights_per_sample": fight_count,
            "samples": samples, "median_selector_share_pct": share,
            "median_wall_seconds": median(s["wall_seconds"] for s in samples),
            "median_cpu_seconds": median(s["cpu_seconds"] for s in samples),
            "maximum_selector_share_pct": MAXIMUM_SELECTOR_SHARE_PCT,
            "within_15_percent_target": share <= MAXIMUM_SELECTOR_SHARE_PCT,
            "self_checks": {"original_definitions_unchanged": True, "expanded_definitions_unchanged": True,
                            "registry_and_lookup_restored": True, "caller_rng_unchanged": True,
                            "source_fighters_unchanged": True, "repeat_outcomes_identical": True}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fights", type=int, default=44, help="Complete fights per sample (default: 44)")
    parser.add_argument("--repeats", type=int, default=3, help="Identical corpus repetitions (default: 3)")
    parser.add_argument("--check", action="store_true", help="Exit nonzero above the fixed 15%% target")
    parser.add_argument("--output", type=Path, help="Optional new JSON file; existing files are never overwritten")
    args = parser.parse_args()
    if args.fights < 1 or args.repeats < 1:
        parser.error("--fights and --repeats must be positive")
    if args.output and args.output.exists():
        parser.error("--output already exists; choose a new diagnostic artifact")
    report = benchmark(args.fights, args.repeats)
    rendered = json.dumps(report, indent=2)
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(rendered + "\n")
    print(rendered)
    return int(args.check and not report["within_15_percent_target"])


if __name__ == "__main__":
    raise SystemExit(main())
