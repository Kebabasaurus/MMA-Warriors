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


def main():
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root, startup_progress=lambda *_: None)
        source = app.build_seed_fighter_database()
        universe = json.loads(DEFAULT_UNIVERSE.read_text(encoding="utf-8"))
        fighters = universe.get("sections", {}).get("fighters", {})
        source_placements, source_names = grouped_keys(app, source)
        database_placements, database_names = grouped_keys(app, fighters)
        missing_names = sorted(source_names - database_names)
        extra_names = sorted(database_names - source_names)
        missing_placements = sorted(source_placements - database_placements)
        print(f"Default Universe schema: {fighters.get('schema')}")
        print(f"Flat fighter records: {len(fighters.get('all_fighters', []))}")
        print(f"Source unique names: {len(source_names)}")
        print(f"Database unique names: {len(database_names)}")
        print(f"Missing unique names: {len(missing_names)}")
        print(f"Extra unique names: {len(extra_names)}")
        print(f"Missing source placements: {len(missing_placements)}")
        if missing_names:
            print("Missing names:")
            for name in missing_names[:50]:
                print(f"  {name}")
        if missing_placements:
            print("Missing placements sample:")
            for placement, name in missing_placements[:50]:
                print(f"  {placement}: {name}")
        if missing_names:
            raise SystemExit(1)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
