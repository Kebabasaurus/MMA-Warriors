"""Synthetic 25/50/100-year narrative storage and lookup-scaling regression."""

import json
import random
import statistics
import time
import tkinter as tk

from constants import STORY_THREAD_RESOLVED_LIMIT
from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def lookup_probe(app, fighter, start, count=5_000):
    samples = []
    for sample in range(3):
        began = time.perf_counter()
        for index in range(count):
            app.upsert_story_thread(
                "long-run-active-probe", "Long Run Probe", fighters=[fighter],
                beat_ref=f"probe:{start + sample * count + index}", summary="Bounded update",
            )
        samples.append(time.perf_counter() - began)
    return statistics.median(samples)


def main():
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda _exc, value, _tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root, startup_progress=lambda _value, _text: None)
        fighter = app.roster[0]
        app.repair_story_threads([])
        rng_before = random.getstate()
        empty_lookup = lookup_probe(app, fighter, 0)

        checkpoints = {}
        for month in range(1, 1201):
            app.month = month
            app.week = (month % 4) + 1
            key = f"long-run:{month}"
            app.upsert_story_thread(
                key, "Long Career", status="active", phase="opened", importance=2,
                fighters=[fighter], beat_ref=f"{key}:open", summary=f"Story month {month} opened.",
            )
            app.upsert_story_thread(
                key, "Long Career", status="resolved", phase="closed", importance=2,
                fighters=[fighter], beat_ref=f"{key}:close", summary=f"Story month {month} closed.",
                resolution=f"Story month {month} reached its outcome.",
            )
            if month in (300, 600, 1200):
                years = month // 12
                payload = json.dumps(app.story_threads, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                checkpoints[years] = {"threads": len(app.story_threads), "bytes": len(payload)}

        mature_lookup = lookup_probe(app, fighter, 20_000)
        require(random.getstate() == rng_before,
                "Long-run narrative storage consumed the shared simulation RNG.")
        require(checkpoints[25]["threads"] == 301 and checkpoints[50]["threads"] == 601,
                f"Unexpected pre-cap thread growth: {checkpoints!r}")
        require(checkpoints[100]["threads"] == STORY_THREAD_RESOLVED_LIMIT + 1,
                "The 100-year fixture did not reach the resolved cap plus its one active probe.")
        require(checkpoints[100]["bytes"] < 1_500_000,
                f"Bounded 100-year narrative payload is unexpectedly large ({checkpoints[100]['bytes']:,} bytes).")
        require(mature_lookup <= empty_lookup * 1.50 + 0.02,
                f"Indexed update time grew with resolved history: empty={empty_lookup:.4f}s mature={mature_lookup:.4f}s.")

        # Continue beyond a century to prove resolved storage stays capped.
        for offset in range(1, 101):
            key = f"overflow:{offset}"
            app.upsert_story_thread(key, "Overflow", fighters=[fighter], beat_ref=f"{key}:open", summary="Opened")
            app.upsert_story_thread(
                key, "Overflow", status="resolved", phase="closed", fighters=[fighter],
                beat_ref=f"{key}:close", summary="Closed", resolution="Closed",
            )
        resolved = [row for row in app.story_threads if row.get("status") in {"resolved", "abandoned"}]
        require(len(resolved) == STORY_THREAD_RESOLVED_LIMIT,
                "Resolved narrative history exceeded its century-scale cap.")
        require(not callback_errors, f"Tk callback errors occurred: {callback_errors}")
        print(
            "NARRATIVE LONG-RUN STORAGE REGRESSION PASSED | "
            f"25y {checkpoints[25]['bytes']:,} B | 50y {checkpoints[50]['bytes']:,} B | "
            f"100y {checkpoints[100]['bytes']:,} B | lookup {empty_lookup:.4f}s->{mature_lookup:.4f}s"
        )
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
