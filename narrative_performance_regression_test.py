"""Paired 12-week aggregate A/B audit for narrative correctness and calendar overhead."""

import random
import time
import tkinter as tk
import hashlib
import inspect
import statistics
import gc
from copy import deepcopy
from uuid import UUID

import models
import persistence
import world
from main import FightEmpireApp


WEEKS_PER_SAMPLE = 4
SAMPLES = 3


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def core_signature(app):
    fighters = sorted(
        (
            fighter.name, fighter.gender, fighter.weight, fighter.record_w, fighter.record_l, fighter.record_d,
            fighter.overall, fighter.popularity, fighter.momentum, fighter.morale,
            fighter.contract_months, fighter.injured, fighter.retired,
        )
        for fighter in app.all_fighter_objects()
    )
    promotions = sorted(
        (
            promotion.name, promotion.cash, promotion.reputation_score, promotion.size,
            promotion.event_counter, len(promotion.roster),
        )
        for promotion in app.promotions
    )
    return (
        app.month, app.week, app.cash, app.company_pop, app.company_stability,
        tuple(fighters), tuple(promotions),
    )


def run_year(snapshot, rng_state, enabled):
    """Run one clean A/B arm without carrying transient caches between arms."""
    counters = {}
    original_uuid4 = (models.uuid4, persistence.uuid4, world.uuid4)

    def deterministic_uuid():
        caller = inspect.currentframe().f_back.f_code.co_name
        counters[caller] = counters.get(caller, 0) + 1
        namespace = int.from_bytes(hashlib.sha256(caller.encode("utf-8")).digest()[:8], "big")
        return UUID(int=(namespace << 64) + counters[caller])

    # Fighter IDs normally use OS entropy. That is appropriate in the game,
    # but it makes two benchmark arms incomparable when replacement fighters
    # enter the market. Story IDs use world.uuid4 and remain separate.
    models.uuid4 = persistence.uuid4 = world.uuid4 = deterministic_uuid
    random.setstate(rng_state)
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda _exc, value, _tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root, startup_progress=lambda _value, _text: None)
        app.apply_world_data(deepcopy(snapshot))
        app.narrative_tracking_enabled = enabled
        # This A/B isolates the cost and RNG purity of story tracking itself.
        # Story-aware AI matchmaking intentionally changes future opponents,
        # so hold that decision feature constant in both comparison arms.
        app.narrative_ai_intent_enabled = False
        random.setstate(rng_state)
        # Fresh app/load construction leaves generational-GC counters at
        # allocation-dependent points. Normalize both arms immediately before
        # timing so a deferred startup collection is not misclassified as
        # narrative calendar work.
        gc.collect()
        wall_started = time.perf_counter()
        cpu_started = time.process_time()
        for _index in range(WEEKS_PER_SAMPLE):
            app.advance_month()
        cpu_elapsed = time.process_time() - cpu_started
        wall_elapsed = time.perf_counter() - wall_started
        return cpu_elapsed, wall_elapsed, core_signature(app), random.getstate(), callback_errors
    finally:
        root.destroy()
        models.uuid4, persistence.uuid4, world.uuid4 = original_uuid4


def signature_difference(left, right):
    labels = ("month", "week", "cash", "company_pop", "company_stability")
    for index, label in enumerate(labels):
        if left[index] != right[index]:
            return f"{label}: {left[index]!r} != {right[index]!r}"
    for label, left_rows, right_rows in (("fighter", left[5], right[5]), ("promotion", left[6], right[6])):
        if len(left_rows) != len(right_rows):
            return f"{label} row count: {len(left_rows)} != {len(right_rows)}"
        for index, (left_row, right_row) in enumerate(zip(left_rows, right_rows)):
            if left_row != right_row:
                return f"{label} row {index}: {left_row!r} != {right_row!r}"
    return "unknown difference"


def main():
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda _exc, value, _tb: callback_errors.append(value)
    try:
        random.seed(937_421)
        app = FightEmpireApp(root, startup_progress=lambda _value, _text: None)
        # Preserve real calendar, AI-event, fighter-development, finance,
        # rivalry and retirement flows while keeping this A/B check suitable
        # for every shipping run. Long-horizon/full-universe scale remains the
        # responsibility of stability_test.py and explicit audit runs.
        app.promotions = [promotion for promotion in app.promotions if not getattr(promotion, "is_regional_feeder", False)][:3]
        # Stay above the emergency market floor so this benchmark measures
        # narrative tracking rather than non-deterministic UUID assignment for
        # freshly generated replacement fighters.
        app.free_agents = app.free_agents[:220]
        first_sport = next(iter(app.combat_sport_worlds), None)
        if first_sport:
            sport_world = app.combat_sport_worlds[first_sport]
            sport_world["roster"] = list(sport_world.get("roster", []))[:40]
            app.combat_sport_worlds = {first_sport: sport_world}
        app.rules["active_fighter_target"] = 300
        app.rules["ai_offer_market_target"] = 60
        snapshot = app.serialize_world()
        rng_state = random.getstate()

        # The seed app is not reused for either timed arm: several simulation
        # caches are deliberately transient and are not part of save data.
        root.destroy()
        root = None
        baseline_samples = []
        narrative_samples = []
        baseline_wall_samples = []
        narrative_wall_samples = []
        for sample in range(SAMPLES):
            order = (False, True) if sample % 2 == 0 else (True, False)
            results = {}
            for enabled in order:
                results[enabled] = run_year(snapshot, rng_state, enabled=enabled)
            baseline_seconds, baseline_wall, baseline_signature, baseline_rng, baseline_errors = results[False]
            narrative_seconds, narrative_wall, narrative_signature, narrative_rng, narrative_errors = results[True]
            require(narrative_signature == baseline_signature,
                    f"Narrative tracking changed core sample {sample + 1} world outcomes: "
                    + signature_difference(baseline_signature, narrative_signature))
            require(narrative_rng == baseline_rng,
                    f"Narrative tracking changed sample {sample + 1}'s shared simulation RNG state.")
            baseline_samples.append(baseline_seconds)
            narrative_samples.append(narrative_seconds)
            baseline_wall_samples.append(baseline_wall)
            narrative_wall_samples.append(narrative_wall)
            callback_errors.extend(baseline_errors)
            callback_errors.extend(narrative_errors)

        baseline_seconds = statistics.median(baseline_samples)
        narrative_seconds = statistics.median(narrative_samples)
        baseline_wall = statistics.median(baseline_wall_samples)
        narrative_wall = statistics.median(narrative_wall_samples)
        # CPU time isolates simulation work from unrelated Windows scheduler
        # pauses. Alternating order and medians still control thermal/cache
        # drift; wall time remains visible as a diagnostic rather than being
        # allowed to turn an external pause into a release failure.
        allowed = baseline_seconds * 1.05 + 0.15
        require(narrative_seconds <= allowed,
                f"Narrative median {narrative_seconds:.3f}s exceeded the "
                f"{allowed:.3f}s budget over a {baseline_seconds:.3f}s median baseline. "
                f"Samples: baseline={baseline_samples!r}, narrative={narrative_samples!r}")
        require(not callback_errors, f"Tk callback errors occurred: {callback_errors}")
        overhead = ((narrative_seconds / max(0.000001, baseline_seconds)) - 1) * 100
        print(
            "NARRATIVE PERFORMANCE REGRESSION PASSED | "
            f"CPU baseline median {baseline_seconds:.3f}s | CPU narrative median {narrative_seconds:.3f}s | "
            f"CPU overhead {overhead:+.2f}% | wall diagnostic {baseline_wall:.3f}s->{narrative_wall:.3f}s | "
            f"{SAMPLES * WEEKS_PER_SAMPLE} aggregate weeks per arm"
        )
    finally:
        if root is not None:
            root.destroy()


if __name__ == "__main__":
    main()
