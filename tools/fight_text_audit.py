"""Run a reproducible 500-fight commentary and metric audit for MMA Warriors.

This is a development tool only. It clones fighters, so careers and saves stay unchanged.
"""

import importlib.util
import random
import sys
import tkinter as tk
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent  # game root (scripts live in tools/)
OUTPUT = ROOT / "audits" / "fight_text_500_audit_latest.txt"
RUNS = 500
SEED = 20260711


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors_audit", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strip_clock(line):
    line = line.strip()
    if line.startswith("[") and "] " in line:
        return line.split("] ", 1)[1]
    return line


def main():
    random.seed(SEED)
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root)
        pools = {}
        for fighter in app.all_database_fighters():
            pools.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        usable = [pool for pool in pools.values() if len(pool) >= 2]

        methods = Counter()
        phrase_counts = Counter()
        anomalies = Counter()
        stat_rows = []
        excerpts = []
        for index in range(1, RUNS + 1):
            pool = random.choice(usable)
            original_a = random.choice(pool)
            comparable = [fighter for fighter in pool if fighter.name != original_a.name and abs(fighter.overall - original_a.overall) <= 6]
            original_b = random.choice(comparable or [fighter for fighter in pool if fighter.name != original_a.name])
            a = app.clone_fighter_for_sim(original_a)
            b = app.clone_fighter_for_sim(original_b)
            app.prepare_sim_fighter(a, random.randint(2, 12), title_fight=random.random() < 0.16)
            app.prepare_sim_fighter(b, random.randint(2, 12), title_fight=random.random() < 0.16)
            winner, loser, method, round_no, lines = app.simulate_fight(a, b, {"main": random.random() < 0.22, "title": False})
            methods[method] += 1
            for line in lines:
                text = strip_clock(line)
                if text and not text.startswith(("Round ", "Metrics -", "FIGHT METRICS", "Fighter", "-", "Tale of", "Official", "Judges", "After the", "The cards")):
                    phrase_counts[text] += 1
                if "stalls from top and the referee stands them up" in text:
                    anomalies["instant_standup_phrase"] += 1
                if "Scale: -" in text:
                    anomalies["empty_scale"] += 1
            for fighter in (a, b):
                stats = fighter.last_fight_stats or {}
                stat_rows.append(stats)
            if index <= 12:
                excerpts.extend(["", "=" * 96, f"FIGHT {index:03d}: {winner.name} def. {loser.name} by {method} R{round_no}", "-" * 96, *lines])

        def average(key):
            return sum(row.get(key, 0) for row in stat_rows) / max(1, len(stat_rows))

        repeated = [(phrase, count) for phrase, count in phrase_counts.most_common(20) if count >= 8]
        report = [
            "MMA WARRIORS - 500 FIGHT TEXT / METRIC AUDIT",
            "=" * 96,
            f"Seed: {SEED}",
            f"Fights: {RUNS}",
            "Matchmaking: same gender/division, overall gap <= 6 where available.",
            "",
            "METHOD MIX",
            "-" * 96,
        ]
        report.extend(f"{method:<24}{count:>4}  {count / RUNS:>5.1%}" for method, count in methods.most_common())
        report.extend([
            "",
            "AVERAGE PER-FIGHT FIGHTER METRICS",
            "-" * 96,
            f"Significant strikes: {average('sig'):.1f}/{average('sig_att'):.1f}",
            f"Takedowns:          {average('td'):.1f}/{average('td_att'):.1f}",
            f"Submission attempts: {average('sub_att'):.1f}",
            f"Control time:        {average('control_secs'):.0f} sec",
            f"Knockdowns:          {average('knockdowns'):.2f}",
            "",
            "TEXT / STATE CHECKS",
            "-" * 96,
            f"Instant stand-up phrase occurrences: {anomalies['instant_standup_phrase']}",
            f"Empty scale fields: {anomalies['empty_scale']}",
            "",
            "MOST REPEATED COMMENTARY LINES",
            "-" * 96,
        ])
        report.extend(f"{count:>4}  {phrase}" for phrase, count in repeated) if repeated else report.append("No exact phrase reached the reporting threshold.")
        report.extend(["", "EXCERPTED FIGHT LOGS", "=" * 96, *excerpts])
        OUTPUT.write_text("\n".join(report), encoding="utf-8")
        print(f"Wrote {OUTPUT}")
    finally:
        root.destroy()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        raise
