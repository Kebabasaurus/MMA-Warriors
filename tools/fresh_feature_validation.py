"""Fresh-world gameplay validation for recently added MMA Warriors systems."""
import importlib.util, random, sys, tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "audits" / "fresh_feature_validation_latest.txt"

def main():
    random.seed(20260714)
    spec = importlib.util.spec_from_file_location("fresh_validation_game", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    root = tk.Tk(); root.withdraw()
    try:
        app = module.FightEmpireApp(root)
        checks = []
        app.rules["scouting_mode"] = True
        target = app.free_agents[0]
        app.market_tree.selection_set(target.name)
        app.start_selected_scout_report("basic")
        for _ in range(2): app.process_scouting_reports()
        checks.append(("Basic scouting", app.scouting_reports[target.name]["status"] == "Complete"))
        app.academy.update({
            "owned": True, "level": 1, "capacity": 8, "weekly_cost": 4500,
            "network_active": True, "network_weeks": 0, "network_region": app.player_region,
            "network_scout": "Validation Scout", "network_scout_skill": 99,
        })
        app.month, app.week = 1, 4
        app.process_academy_week()
        checks.append(("Academy talent generation", bool(app.academy["talent_pool"])))
        talent = app.academy["talent_pool"].pop(0)
        talent.update({"plan": "Wrestling", "amateur_w": 0, "amateur_l": 0, "amateur_d": 0, "amateur_history": [], "weeks": 0, "development": 0})
        app.repair_academy_prospect(talent)
        app.academy["prospects"].append(talent)
        app.process_academy_week()
        checks.append(("Academy weekly development", app.academy["prospects"][0]["weeks"] > 0))
        promo = next(p for p in app.promotions if not p.is_regional_feeder)
        ready = [f for f in promo.roster if not f.injured and f.fatigue < app.ai_fatigue_limit(promo)]
        card = app.build_ai_card(promo, ready, 7)
        checks.append(("AI event hierarchy", bool(card) and any(f.get("main") for f in card) and all(f.get("tier") for f in card)))
        a, b = app.roster[:2]
        entry = {"fighters": [a.name, b.name], "tier": "Prelims", "main": False, "source_event": "Validation", "target_month": 1}
        app.pending_rebookings = [entry]
        app.process_pending_rebookings()
        checks.append(("Automatic rebooking", not app.pending_rebookings and bool(app.scheduled_events)))
        lines = ["MMA WARRIORS - FRESH FEATURE VALIDATION", "=" * 72]
        for name, passed in checks: lines.append(f"{'PASS' if passed else 'FAIL'}  {name}")
        lines.append("\nThis harness uses a new in-memory world only; no user save was opened or written.")
        OUT.write_text("\n".join(lines), encoding="utf-8")
        if not all(passed for _name, passed in checks): raise RuntimeError("One or more fresh-world feature checks failed")
        print(f"Wrote {OUT}")
    finally: root.destroy()
if __name__ == "__main__": main()
