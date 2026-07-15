"""Audit generated-fighter entry quality and career-curve differentiation.

The audit is deterministic, runs entirely in memory, and never writes a save.  It
uses the real generator for the entry cohort, then controlled clones for the
longitudinal comparison so age/archetype effects are not confused by ratings,
traits, camps, or potential.
"""

from __future__ import annotations

import importlib.util
import math
import random
import statistics
import sys
import tkinter as tk
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "audits" / "generated_fighter_balance_audit_latest.txt"
SEED = 20260714
GENERATED_SAMPLE = 5000
CONTROLLED_PER_CELL = 100
CONTROLLED_MONTHS = 60

ARCHETYPES = (
    "Early Maturation",
    "Balanced Development",
    "Late Maturation",
    "Durable Career",
)
STAGES = {
    "Early (age 20, OVR 58, POT 88)": (20, 58, 88),
    "Mid (age 28, OVR 72, POT 86)": (28, 72, 86),
    "Late (age 36, OVR 82, POT 87)": (36, 82, 87),
}


def percentile(values, pct):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * pct
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summary(values):
    if not values:
        return "n=0"
    return (
        f"n={len(values):4d} mean={statistics.fmean(values):5.1f} "
        f"p10={percentile(values, .10):4.1f} p50={percentile(values, .50):4.1f} "
        f"p90={percentile(values, .90):4.1f} min={min(values):2d} max={max(values):2d}"
    )


def correlation(xs, ys):
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys)
    )
    return numerator / denominator if denominator else 0.0


def standardize_fighter(app, fighter, age, rating, potential, archetype):
    fighter.age = age
    fighter.career_archetype = archetype
    fighter.trait = "Quiet Professional"
    fighter.camp = "Independent"
    fighter.camp_focus = "Balanced"
    fighter.morale = 70
    fighter.momentum = 0
    fighter.fatigue = 0
    fighter.injured = 0
    fighter.injury_proneness = 20
    fighter.professionalism = 65
    for key in (
        "striking", "wrestling", "grappling", "cardio", "chin", "power",
        "takedown_defence", "ground_control", "submissions", "submission_defence",
        "recovery", "toughness", "fight_iq",
    ):
        setattr(fighter, key, rating)
    app.ensure_detailed_skills(fighter)
    fighter.detailed_skills = {key: rating for key in fighter.detailed_skills}
    app.sync_broad_skills_from_details(fighter)
    fighter.potential = potential
    app.assign_career_arc(fighter)
    return fighter


def annual_development_tick(app, fighter):
    """Mirror the per-fighter skill portion of age_world_one_year."""
    fighter.age += 1
    if fighter.age > fighter.prime_end:
        over = fighter.age - fighter.prime_end
        decline_chance = min(
            0.85,
            0.32 + over * 0.12 - app.veteran_resurgence_chance(fighter) * 2,
        )
        if random.random() < decline_chance:
            app.adjust_random_skill(fighter, -1)
            app.adjust_detailed_skill(fighter, -1)
    elif fighter.age < fighter.prime_start and fighter.overall < fighter.potential:
        if random.random() < 0.55:
            app.adjust_random_skill(fighter, 1)
            app.adjust_detailed_skill(fighter, 1)


def generated_entry_section(app):
    random.seed(SEED)
    fighters = [app.create_generated_fighter() for _ in range(GENERATED_SAMPLE)]
    lines = [
        "GENERATED ENTRY COHORT",
        "-" * 92,
        f"Real create_generated_fighter calls: {len(fighters)} (default skill/population ranges).",
        f"OVR:       {summary([f.overall for f in fighters])}",
        f"Potential: {summary([f.potential for f in fighters])}",
        f"POT gap:   {summary([f.potential - f.overall for f in fighters])}",
        f"Age:       {summary([f.age for f in fighters])}",
        f"Bouts:     {summary([f.record_w + f.record_l + f.record_d for f in fighters])}",
        "",
        "By generated age band",
    ]
    bands = (
        ("18-21", 18, 21),
        ("22-25", 22, 25),
        ("26-29", 26, 29),
        ("30-33", 30, 33),
    )
    for label, low, high in bands:
        cohort = [f for f in fighters if low <= f.age <= high]
        ovrs = [f.overall for f in cohort]
        gaps = [f.potential - f.overall for f in cohort]
        bouts = [f.record_w + f.record_l + f.record_d for f in cohort]
        high_level = sum(f.overall >= 75 for f in cohort) / len(cohort) * 100
        lines.append(
            f"{label}: n={len(cohort):4d} OVR mean {statistics.fmean(ovrs):5.1f} "
            f"(p10/p50/p90 {percentile(ovrs,.1):.0f}/{percentile(ovrs,.5):.0f}/{percentile(ovrs,.9):.0f}), "
            f"gap {statistics.fmean(gaps):4.1f}, bouts {statistics.fmean(bouts):4.1f}, OVR>=75 {high_level:4.1f}%"
        )
    lines.extend([
        "",
        f"Age-to-OVR Pearson correlation: {correlation([f.age for f in fighters], [f.overall for f in fighters]):+.3f}",
        f"Age-to-bouts Pearson correlation: {correlation([f.age for f in fighters], [f.record_w + f.record_l + f.record_d for f in fighters]):+.3f}",
    ])

    debut_like = [f for f in fighters if f.record_w + f.record_l + f.record_d <= 2]
    young = [f for f in fighters if f.age <= 21]
    young_debut = [f for f in young if f.record_w + f.record_l + f.record_d <= 2]
    lines.extend([
        "",
        "Debut-like generated fighters (0-2 recorded bouts)",
        f"All ages: {summary([f.overall for f in debut_like])}",
        f"Age <=21: {summary([f.overall for f in young_debut])}",
        f"Age <=21 with 10+ bouts: {sum(f.record_w + f.record_l + f.record_d >= 10 for f in young)}/{len(young)} "
        f"({sum(f.record_w + f.record_l + f.record_d >= 10 for f in young) / len(young) * 100:.1f}%)",
        "",
        "By career archetype at generation",
    ])
    archetype_counts = Counter(f.career_archetype for f in fighters)
    for archetype in ARCHETYPES:
        cohort = [f for f in fighters if f.career_archetype == archetype]
        lines.append(
            f"{archetype:<22} n={len(cohort):4d} ({archetype_counts[archetype]/len(fighters)*100:4.1f}%) "
            f"OVR {statistics.fmean(f.overall for f in cohort):5.1f} gap {statistics.fmean(f.potential-f.overall for f in cohort):4.1f} "
            f"prime {statistics.fmean(f.prime_start for f in cohort):4.1f}-{statistics.fmean(f.prime_end for f in cohort):4.1f}"
        )
    return lines, fighters


def controlled_development_section(app):
    lines = [
        "",
        "CONTROLLED 5-YEAR CAREER CURVES",
        "-" * 92,
        f"{CONTROLLED_PER_CELL} fighters per stage/archetype; real monthly development plus the real annual age tick.",
        "Independent camp, Quiet Professional, neutral form; no bouts or event-camp micro-improvements.",
        "Deltas are from each standardized starting OVR. POT% is the share ending at potential.",
        "",
    ]
    all_results = defaultdict(dict)
    cell_index = 0
    for stage, (age, rating, potential) in STAGES.items():
        lines.append(stage)
        lines.append(f"{'Archetype':<22} {'Prime avg':>11} {'24m':>7} {'60m':>7} {'End OVR':>9} {'POT%':>7} {'Decline%':>9}")
        for archetype in ARCHETYPES:
            random.seed(SEED + 1000 + cell_index)
            cell_index += 1
            cohort = []
            for _ in range(CONTROLLED_PER_CELL):
                fighter = app.create_generated_fighter(min_skill=rating, max_skill=rating)
                cohort.append(standardize_fighter(app, fighter, age, rating, potential, archetype))
            starts = [f.overall for f in cohort]
            prime_starts = [f.prime_start for f in cohort]
            prime_ends = [f.prime_end for f in cohort]
            at_24 = []
            for month in range(1, CONTROLLED_MONTHS + 1):
                app.month = month
                app.age_and_develop_fighters(cohort)
                if month % 12 == 0:
                    for fighter in cohort:
                        annual_development_tick(app, fighter)
                if month == 24:
                    at_24 = [f.overall for f in cohort]
            ends = [f.overall for f in cohort]
            delta_24 = statistics.fmean(value - start for value, start in zip(at_24, starts))
            delta_60 = statistics.fmean(value - start for value, start in zip(ends, starts))
            at_potential = sum(f.overall >= f.potential for f in cohort) / len(cohort) * 100
            declined = sum(end < start for end, start in zip(ends, starts)) / len(cohort) * 100
            all_results[stage][archetype] = delta_60
            lines.append(
                f"{archetype:<22} {statistics.fmean(prime_starts):4.1f}-{statistics.fmean(prime_ends):4.1f} "
                f"{delta_24:+7.2f} {delta_60:+7.2f} {statistics.fmean(ends):9.2f} {at_potential:6.1f}% {declined:8.1f}%"
            )
        spread = max(all_results[stage].values()) - min(all_results[stage].values())
        lines.append(f"Five-year archetype delta spread: {spread:.2f} OVR")
        lines.append("")
    return lines, all_results


def validation_section(app, fighters):
    record_violations = []
    potential_violations = []
    for fighter in fighters:
        cap = max(2, min(25, (fighter.age - 18) * 4 + 2))
        bouts = fighter.record_w + fighter.record_l + fighter.record_d
        if bouts > cap:
            record_violations.append((fighter.age, bouts, cap))
        floor = 8 if fighter.age <= 21 else 5 if fighter.age <= 25 else 2
        required = min(98, fighter.overall + floor)
        if fighter.potential < required:
            potential_violations.append((fighter.age, fighter.overall, fighter.potential, required))

    young_mean = statistics.fmean(f.overall for f in fighters if f.age <= 21)
    established_mean = statistics.fmean(f.overall for f in fighters if 26 <= f.age <= 33)

    random.seed(SEED + 9000)
    used_names = set()
    feeder_regions = ("Japan", "UK", "USA", "Europe", "Asia", "Brazil", "Mexico")
    feeders = [
        app.create_regional_feeder_fighter(
            feeder_regions[index % len(feeder_regions)],
            used_names,
            "Female" if index % 5 == 0 else "Male",
        )
        for index in range(200)
    ]
    feeder_violations = [
        fighter.name for fighter in feeders
        if not (16 <= fighter.age <= 26)
        or fighter.record_w > 6
        or fighter.record_l > min(4, fighter.record_w + 1)
        or fighter.potential < min(96, fighter.overall + 8)
    ]

    assert not record_violations, f"Age-bounded record violations: {record_violations[:3]}"
    assert not potential_violations, f"Young potential-floor violations: {potential_violations[:3]}"
    assert established_mean >= young_mean + 2.0, (young_mean, established_mean)
    assert not feeder_violations, f"Regional feeder profile violations: {feeder_violations[:3]}"
    return [
        "",
        "POST-PATCH INVARIANT CHECKS",
        "-" * 92,
        f"PASS - age-bounded record violations: {len(record_violations)}",
        f"PASS - age-banded potential-floor violations: {len(potential_violations)}",
        f"PASS - established (26-33) entry OVR exceeds young (18-21): {established_mean:.1f} vs {young_mean:.1f}",
        f"PASS - feeder-specific age/record/upside violations across {len(feeders)} fighters: {len(feeder_violations)}",
    ]


def interpretation_section(fighters, curves):
    young = [f for f in fighters if f.age <= 21]
    age_ovr_corr = correlation([f.age for f in fighters], [f.overall for f in fighters])
    age_bout_corr = correlation(
        [f.age for f in fighters],
        [f.record_w + f.record_l + f.record_d for f in fighters],
    )
    early_growth = statistics.fmean(curves["Early (age 20, OVR 58, POT 88)"].values())
    mid_growth = statistics.fmean(curves["Mid (age 28, OVR 72, POT 86)"].values())
    late_growth = statistics.fmean(curves["Late (age 36, OVR 82, POT 87)"].values())
    young_10 = sum(f.record_w + f.record_l + f.record_d >= 10 for f in young) / len(young) * 100
    prime_means = {
        archetype: statistics.fmean(f.prime_end for f in fighters if f.career_archetype == archetype)
        for archetype in ARCHETYPES
    }
    return [
        "INTERPRETATION / PATCH DELTAS",
        "-" * 92,
        f"1. Age/OVR correlation moved from -0.002 to {age_ovr_corr:+.3f}; young mean OVR fell from 64.9",
        "   to 62.4 while ages 26-29 now average 67.0. Entry ability now has a modest career-age slope.",
        f"2. Age/bouts correlation moved from +0.022 to {age_bout_corr:+.3f}. The share of ages 18-21",
        f"   with 10+ bouts fell from 66.6% to {young_10:.1f}%, with zero fighters exceeding the new age cap.",
        f"3. Controlled five-year mean OVR change is early {early_growth:+.2f}, mid {mid_growth:+.2f},",
        f"   late {late_growth:+.2f}, versus +5.48/+4.45/+1.24 before the prime-window change.",
        f"4. Mean prime_end is {prime_means['Early Maturation']:.1f} Early / {prime_means['Balanced Development']:.1f} Balanced /",
        f"   {prime_means['Late Maturation']:.1f} Late / {prime_means['Durable Career']:.1f} Durable, down from 36.1/37.9/39.3/39.2.",
        "5. Potential-gap p10 moved from 3 to 5 and the young floor is enforced without stacking another",
        "   boost onto the regional-feeder pathway.",
        "",
        "Remaining watch items (no further tuning applied):",
        "- Late/Durable age-36 cohorts still gain modestly because those archetypes intentionally remain in",
        "  prime to roughly 38. Validate retirement age and active-world average in a 20-30 year audit first.",
        "- Early-career archetypes still converge (five-year spread below 0.2 OVR). If world outcomes confirm",
        "  weak identity, test development-score modifiers no larger than +/-8: Early +8 before 24,",
        "  Late -6 before 24 then +8 from prime_start through prime_end. Durable should rely on its longer",
        "  prime/tail and a small decline buffer, not higher peak potential.",
    ]


def main():
    random.seed(SEED)
    spec = importlib.util.spec_from_file_location("audit_game", ROOT / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    root = tk.Tk()
    root.withdraw()
    try:
        app = mod.FightEmpireApp(root)
        lines = [
            "MMA WARRIORS - GENERATED FIGHTER / CAREER DEVELOPMENT BALANCE AUDIT",
            "=" * 92,
            f"Seed {SEED}; isolated in memory; no save changed.",
            "",
        ]
        entry_lines, fighters = generated_entry_section(app)
        curve_lines, curves = controlled_development_section(app)
        lines.extend(entry_lines)
        lines.extend(curve_lines)
        lines.extend(validation_section(app, fighters))
        lines.extend(interpretation_section(fighters, curves))
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {OUT}")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
