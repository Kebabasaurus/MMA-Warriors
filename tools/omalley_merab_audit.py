"""Controlled Sean O'Malley vs Merab Dvalishvili engine audit.

Uses disposable fighter clones and a seeded RNG.  It never applies results to
the game world or writes a save; its only output is the audit report.
"""

import importlib.util
import random
import re
import sys
import tkinter as tk
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "audits" / "omalley_dvalishvili_matchup_audit_latest.txt"
SEED = 20260712
RUNS_PER_CONDITION = 160
CONDITIONS = ((8, 8, "Equal eight-week camps"), (2, 8, "O'Malley short camp / Merab full camp"), (8, 2, "O'Malley full camp / Merab short camp"))

# Scripts run from tools/ need the flat game modules at the project root.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors_omalley_audit", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentage(value, total):
    return f"{(100 * value / max(1, total)):.1f}%"


def average(rows, key):
    return sum(row.get(key, 0) for row in rows) / max(1, len(rows))


def scorecard(lines):
    for index, line in enumerate(lines):
        if "Official scorecards:" in line:
            return " | ".join(item.strip() for item in lines[index + 1:index + 5])
    return "No decision scorecard (finish or draw)."


def commentary_flags(lines):
    text = "\n".join(lines).lower()
    return {
        "takedown attempts": text.count("takedown") + text.count("shot for"),
        "stuffed/defended shots": text.count("stuff") + text.count("defend"),
        "cage/clinch mentions": text.count("cage") + text.count("clinch"),
        "range/counter mentions": text.count("range") + text.count("counter"),
    }


def profile_lines(fighter, app):
    app.ensure_detailed_skills(fighter)
    keys = (
        "reach", "footwork", "hand_speed", "punch_technique", "punch_power",
        "creative_kicks", "high_kick_technique", "head_movement", "guard_defence",
        "takedown_defence_detail", "takedowns", "takedown_setup", "chain_wrestling",
        "cage_wrestling", "top_control", "ride_control", "conditioning", "recovery",
    )
    details = ", ".join(f"{key} {fighter.detailed_skills.get(key, 50)}" for key in keys)
    return [
        f"{fighter.name}: OVR {fighter.overall}; {fighter.style}/{fighter.behaviour}; trait {fighter.trait}.",
        f"Broad: striking {fighter.striking}, wrestling {fighter.wrestling}, grappling {fighter.grappling}, cardio {fighter.cardio}, chin {fighter.chin}, power {fighter.power}, TDD {fighter.takedown_defence}.",
        f"Detailed: {details}",
    ]


def main():
    random.seed(SEED)
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root)
        originals = {fighter.name: fighter for fighter in app.all_database_fighters(include_retired=True)}
        omalley = originals.get("Sean O'Malley")
        merab = originals.get("Merab Dvalishvili")
        if not omalley or not merab:
            raise RuntimeError("Could not locate both Sean O'Malley and Merab Dvalishvili in the loaded database.")

        report = [
            "MMA WARRIORS - SEAN O'MALLEY VS MERAB DVALISHVILI MATCHUP AUDIT",
            "=" * 96,
            f"Seed: {SEED}",
            f"Format: 5-round title/main-event simulator bouts; {RUNS_PER_CONDITION} fights per camp condition.",
            "Method: cloned fighters only. Results, careers, save data, and the live world are untouched.",
            "",
            "PROFILE INPUTS",
            "-" * 96,
            *profile_lines(omalley, app),
            *profile_lines(merab, app),
        ]

        all_examples = []
        for camp_a, camp_b, label in CONDITIONS:
            results = Counter()
            winner_methods = defaultdict(Counter)
            stats = defaultdict(list)
            flags = Counter()
            scorecards = []
            examples = []
            camp = defaultdict(list)
            for index in range(RUNS_PER_CONDITION):
                a = app.clone_fighter_for_sim(omalley)
                b = app.clone_fighter_for_sim(merab)
                weigh_a = app.prepare_sim_fighter(a, camp_a, title_fight=True)
                weigh_b = app.prepare_sim_fighter(b, camp_b, title_fight=True)
                camp[a.name].append({"boost": a.camp_boost, "penalty": weigh_a["penalty"], "missed": not weigh_a["made"]})
                camp[b.name].append({"boost": b.camp_boost, "penalty": weigh_b["penalty"], "missed": not weigh_b["made"]})
                winner, loser, method, round_no, lines = app.simulate_fight(a, b, {"main": True, "title": True, "tier": "Main Card"})
                outcome = "Draw" if method == "Draw" else winner.name
                results[outcome] += 1
                winner_methods[outcome][method] += 1
                stats[a.name].append(dict(a.last_fight_stats or {}))
                stats[b.name].append(dict(b.last_fight_stats or {}))
                flags.update(commentary_flags(lines))
                if method in ("Decision", "Draw"):
                    scorecards.append(scorecard(lines))
                if index < 2:
                    examples.append((winner.name, loser.name, method, round_no, weigh_a, weigh_b, lines))

            total = sum(results.values())
            report.extend(["", label, "-" * 96])
            for outcome in (omalley.name, merab.name, "Draw"):
                methods = ", ".join(f"{method} {count}" for method, count in winner_methods[outcome].most_common()) or "none"
                report.append(f"{outcome:<24}{results[outcome]:>3}/{total} ({percentage(results[outcome], total)}) | {methods}")
            report.append("Average fight metrics (per fighter):")
            for fighter in (omalley.name, merab.name):
                rows = stats[fighter]
                report.append(
                    f"  {fighter:<22} sig {average(rows, 'sig'):.1f}/{average(rows, 'sig_att'):.1f}; "
                    f"TD {average(rows, 'td'):.2f}/{average(rows, 'td_att'):.2f}; "
                    f"control {average(rows, 'control_secs'):.0f}s; subs {average(rows, 'sub_att'):.2f}; "
                    f"KD {average(rows, 'knockdowns'):.2f}; head damage taken {average(rows, 'damage_taken'):.1f}."
                )
            report.append("Camp / weight-cut diagnostics:")
            for fighter in (omalley.name, merab.name):
                rows = camp[fighter]
                report.append(
                    f"  {fighter:<22} camp boost {average(rows, 'boost'):.1f}; cut penalty {average(rows, 'penalty'):.1f}; "
                    f"missed weight {sum(row['missed'] for row in rows)}/{len(rows)}."
                )
            report.append("Commentary/action indicators across the condition: " + "; ".join(f"{key} {value}" for key, value in flags.items()) + ".")
            if scorecards:
                report.append("Decision-card samples: " + " | ".join(scorecards[:3]))
            all_examples.extend([(label, *example) for example in examples])

        report.extend(["", "WATCHED LOG EXCERPTS", "=" * 96])
        for label, winner, loser, method, round_no, weigh_a, weigh_b, lines in all_examples:
            report.extend([
                "", f"{label}: {winner} def. {loser} by {method}, round {round_no}.",
                f"Weigh-ins: O'Malley {weigh_a['scale_weight']} lb (penalty {weigh_a['penalty']}); Merab {weigh_b['scale_weight']} lb (penalty {weigh_b['penalty']}).",
                *lines,
            ])
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
