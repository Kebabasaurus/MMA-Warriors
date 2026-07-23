import importlib.util
import json
import random
import sys
import tkinter as tk
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors_balance_audit", MAIN)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def standing_summary(game, fighter):
    values = [fighter.detailed_skills.get(key, 50) for key in game.DETAILED_SKILL_GROUPS["Standing"]]
    return {
        "minimum": min(values),
        "mean": round(sum(values) / len(values), 2),
        "maximum": max(values),
        "at_98_plus": sum(value >= 98 for value in values),
    }


def population_summary(game, fighters):
    any_capped = 0
    flat_standing = 0
    for fighter in fighters:
        values = list((fighter.detailed_skills or {}).values())
        standing = [fighter.detailed_skills.get(key, 50) for key in game.DETAILED_SKILL_GROUPS["Standing"]]
        any_capped += int(any(value >= 98 for value in values))
        flat_standing += int(all(value >= 98 for value in standing))
    return {"fighters": len(fighters), "any_98_plus": any_capped, "all_standing_98_plus": flat_standing}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: detailed_skill_balance_audit.py SAVEGAME_JSON")
    game = load_game_module()
    save_path = Path(sys.argv[1])
    payload = json.loads(save_path.read_text(encoding="utf-8"))
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root)
        app.apply_world_data(payload)
        active = app.roster + app.free_agents + [fighter for promo in app.promotions for fighter in promo.roster]
        boonchai = app.find_fighter_anywhere("Boonchai Gupta")
        migration_message = next((row.get("body", "") for row in reversed(app.inbox) if row.get("subject") == "Detailed Skill Balance Repair"), "")

        random.seed(220726)
        probe = game.Fighter(**asdict(active[0]))
        probe.name = "Development Balance Probe"
        probe.style = "Kickboxer"
        probe.trait = "Gym Rat"
        probe.age = 22
        probe.potential = 99
        app.ensure_detailed_skills(probe)
        for key in probe.detailed_skills:
            if key not in {"reach", "natural_size"}:
                probe.detailed_skills[key] = 95
        app.sync_broad_skills_from_details(probe)
        before = dict(probe.detailed_skills)
        app.apply_development_growth(probe, 3)
        changed = [key for key, value in probe.detailed_skills.items() if value != before.get(key)]

        print(json.dumps({
            "save": str(save_path),
            "month": app.month,
            "week": app.week,
            "migration": migration_message,
            "version": app.rules.get("detailed_skill_balance_version"),
            "population_after": population_summary(game, active),
            "boonchai_after": None if boonchai is None else {"overall": boonchai.overall, **standing_summary(game, boonchai)},
            "second_migration": app.migrate_detailed_skill_balance(active),
            "development_probe": {
                "changed_count": len(changed),
                "changed": changed,
                "reach_changed": probe.detailed_skills.get("reach") != before.get("reach"),
                "natural_size_changed": probe.detailed_skills.get("natural_size") != before.get("natural_size"),
            },
        }, indent=2))
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
