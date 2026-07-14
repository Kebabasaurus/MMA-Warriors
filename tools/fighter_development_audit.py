"""Controlled development audit; uses cloned fighters and never saves the world."""
import importlib.util, random, sys, tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "audits" / "fighter_development_audit_latest.txt"
SEED = 20260712
MONTHS = 24

def main():
    random.seed(SEED)
    spec = importlib.util.spec_from_file_location("audit_game", ROOT / "main.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    root = tk.Tk(); root.withdraw()
    try:
        app = mod.FightEmpireApp(root)
        templates = [f for f in app.all_database_fighters() if f.gender == "Male"][:24]
        conditions = {
            "Independent / balanced": ("Independent", "Balanced", "Quiet Professional"),
            "Elite gym / balanced": ("American Top Team", "Balanced", "Quiet Professional"),
            "Elite gym / wrestling focus": ("American Top Team", "Wrestling", "Quiet Professional"),
            "Elite gym / Gym Rat": ("American Top Team", "Balanced", "Gym Rat"),
        }
        stages = {"Early career (age 20 / OVR 58)": (20, 58, 88, 25, 33), "Mid career (age 28 / OVR 72)": (28, 72, 86, 25, 33), "Late career (age 36 / OVR 82)": (36, 82, 87, 25, 33)}
        lines = ["MMA WARRIORS - CONTROLLED DEVELOPMENT / FIGHT EXPERIENCE AUDIT", "=" * 78, f"Seed {SEED}; {len(templates)} clones per stage; {MONTHS} monthly checks; competitive fights every 3 months in the fight cohort.", ""]
        for stage_index, (stage, (age, rating, potential, prime_start, prime_end)) in enumerate(stages.items()):
            lines.extend([stage, "-" * 78])
            for fight_cohort in (False, True):
                changes, details, fights = [], [], 0
                random.seed(SEED + stage_index * 100 + (50 if fight_cohort else 0))
                for original in templates:
                    f = app.clone_fighter_for_sim(original); f.age, f.prime_start, f.prime_end, f.potential = age, prime_start, prime_end, potential
                    f.camp, f.camp_focus, f.trait, f.fatigue, f.injured, f.morale, f.momentum = "American Top Team", "Balanced", "Quiet Professional", 0, 0, 70, 0
                    for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "takedown_defence", "ground_control", "submissions", "submission_defence", "recovery", "toughness", "fight_iq") : setattr(f, key, rating)
                    app.ensure_detailed_skills(f); f.detailed_skills = {key: rating for key in f.detailed_skills}; app.sync_broad_skills_from_details(f)
                    start, start_detail = f.overall, sum(f.detailed_skills.values())
                    for month in range(MONTHS):
                        app.age_and_develop_fighters([f]); app.apply_gym_camp_micro_improvement(f, app.gym_by_name(f.camp), 8)
                        if fight_cohort and month % 3 == 2:
                            opponent = app.clone_fighter_for_sim(f); opponent.name = f"Audit Opponent {stage_index}-{month}-{original.name}"; opponent.momentum = 0
                            winner, loser, method, _round, _lines = app.simulate_fight(f, opponent, {"main": False, "title": False})
                            if winner is f: f.momentum = min(5, f.momentum + 1)
                            else: f.momentum = max(-5, f.momentum - 1)
                            fights += 1
                    changes.append(f.overall - start); details.append(sum(f.detailed_skills.values()) - start_detail)
                label = "Training + competitive fights" if fight_cohort else "Training only"
                lines.append(f"{label:<30} OVR {sum(changes)/len(changes):+.2f} | detailed {sum(details)/len(details):+.1f} | bouts {fights}")
            lines.append("")
        lines += ["Interpretation: early fighters should grow most; mid-career fighters should progress more slowly; late fighters should be stable or decline. The fight cohort measures momentum/conditioning context without forcing a winner."]
        OUT.write_text("\n".join(lines), encoding="utf-8"); print(f"Wrote {OUT}")
    finally: root.destroy()
if __name__ == "__main__": main()
