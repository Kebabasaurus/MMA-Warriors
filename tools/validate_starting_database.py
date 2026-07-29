import importlib.util
import json
import sys
import tkinter as tk
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
DEFAULT_UNIVERSE = ROOT / "Databases" / "Default Universe.universe.json"


def load_game_module():
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("mma_warriors_database_validation", MAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grouped_keys(app, database):
    placements = set()
    names = set()
    for row in app.unique_fighter_rows(database.get("player_roster", [])):
        placements.add(("player", row[0]))
        names.add(row[0])
    for row in app.unique_fighter_rows(database.get("free_agents", [])):
        placements.add(("free", row[0]))
        names.add(row[0])
    for company, rows in database.get("promotions", {}).items():
        for row in app.unique_fighter_rows(rows):
            placements.add((company, row[0]))
            names.add(row[0])
    return placements, names


def combat_sport_keys(database):
    keys = set()
    names = set()
    for sport, roster in (database.get("rosters") or {}).items():
        if not isinstance(roster, list):
            continue
        for name in roster:
            keys.add((sport, name))
            names.add(name)
    return keys, names


def incomplete_combat_records(database):
    required = {
        "sport", "name", "gender", "region", "nationality", "weight_class",
        "rating", "prime_age", "record_w", "record_l", "record_d",
        "style", "trait", "behaviour", "stance",
    }
    incomplete = []
    for record in database.get("all_athletes", []):
        if not isinstance(record, dict):
            incomplete.append("<non-dict record>")
            continue
        missing = sorted(key for key in required if record.get(key) in ("", None))
        if missing:
            incomplete.append(f"{record.get('sport', '?')}: {record.get('name', '?')} missing {', '.join(missing)}")
    return incomplete


def main():
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root, startup_progress=lambda *_: None)
        source = app.build_seed_fighter_database()
        combat_source = app.build_combat_sport_database()
        universe = json.loads(DEFAULT_UNIVERSE.read_text(encoding="utf-8"))
        fighters = universe.get("sections", {}).get("fighters", {})
        combat_sports = universe.get("sections", {}).get("combat_sports", {})
        source_placements, source_names = grouped_keys(app, source)
        database_placements, database_names = grouped_keys(app, fighters)
        source_sport_keys, source_sport_names = combat_sport_keys(combat_source)
        database_sport_keys, database_sport_names = combat_sport_keys(combat_sports)
        missing_names = sorted(source_names - database_names)
        extra_names = sorted(database_names - source_names)
        missing_placements = sorted(source_placements - database_placements)
        missing_sport_keys = sorted(source_sport_keys - database_sport_keys)
        missing_sport_names = sorted(source_sport_names - database_sport_names)
        incomplete_sports = incomplete_combat_records(combat_sports)
        print(f"Default Universe schema: {fighters.get('schema')}")
        print(f"Flat fighter records: {len(fighters.get('all_fighters', []))}")
        print(f"Source unique names: {len(source_names)}")
        print(f"Database unique names: {len(database_names)}")
        print(f"Missing unique names: {len(missing_names)}")
        print(f"Extra unique names: {len(extra_names)}")
        print(f"Missing source placements: {len(missing_placements)}")
        print(f"Combat-sport schema: {combat_sports.get('schema')}")
        print(f"Flat combat-sport records: {len(combat_sports.get('all_athletes', []))}")
        print(f"Combat-sport source placements: {len(source_sport_keys)}")
        print(f"Combat-sport database placements: {len(database_sport_keys)}")
        print(f"Missing combat-sport names: {len(missing_sport_names)}")
        print(f"Missing combat-sport placements: {len(missing_sport_keys)}")
        print(f"Incomplete combat-sport records: {len(incomplete_sports)}")
        if missing_names:
            print("Missing names:")
            for name in missing_names[:50]:
                print(f"  {name}")
        if missing_placements:
            print("Missing placements sample:")
            for placement, name in missing_placements[:50]:
                print(f"  {placement}: {name}")
        if missing_sport_names:
            print("Missing combat-sport names:")
            for name in missing_sport_names[:50]:
                print(f"  {name}")
        if missing_sport_keys:
            print("Missing combat-sport placements sample:")
            for sport, name in missing_sport_keys[:50]:
                print(f"  {sport}: {name}")
        if incomplete_sports:
            print("Incomplete combat-sport records sample:")
            for line in incomplete_sports[:50]:
                print(f"  {line}")
        if missing_names or missing_sport_names or missing_sport_keys or incomplete_sports:
            raise SystemExit(1)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
