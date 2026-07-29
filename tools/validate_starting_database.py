import importlib.util
import json
import sys
import tkinter as tk
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
DEFAULT_UNIVERSE = ROOT / "Databases" / "Default Universe.universe.json"
MMA_PROFILE_KEYS = {
    "profile_rating", "profile_style", "trait", "behaviour", "skill_mods",
    "stance", "signature_skills", "special_profile", "record_d",
}


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


def incomplete_mma_records(database):
    required = {
        "placement", "owner", "name", "gender", "weight", "region", "nationality",
        "popularity", "rating", "age", "record_w", "record_l", "record_d", "style",
    }
    incomplete = []
    for record in database.get("all_fighters", []):
        if not isinstance(record, dict):
            incomplete.append("<non-dict record>")
            continue
        missing = sorted(key for key in required if record.get(key) in ("", None))
        if missing:
            incomplete.append(f"{record.get('placement', '?')}: {record.get('name', '?')} missing {', '.join(missing)}")
    return incomplete


def record_key(app, record):
    return (
        str(record.get("placement", "")),
        str(record.get("owner", "")),
        app.fighter_name_key(record.get("name", "")),
    )


def profile_payload(record):
    return {key: record.get(key) for key in MMA_PROFILE_KEYS if key in record}


def profile_payload_mismatches(app, source, database):
    source_records = {
        record_key(app, record): profile_payload(record)
        for record in source.get("all_fighters", [])
        if isinstance(record, dict)
    }
    database_records = {
        record_key(app, record): profile_payload(record)
        for record in database.get("all_fighters", [])
        if isinstance(record, dict)
    }
    mismatches = []
    for key, payload in source_records.items():
        if payload and database_records.get(key) != payload:
            mismatches.append(key)
    return mismatches


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
        incomplete_mma = incomplete_mma_records(fighters)
        profile_mismatches = profile_payload_mismatches(app, source, fighters)
        missing_sport_keys = sorted(source_sport_keys - database_sport_keys)
        missing_sport_names = sorted(source_sport_names - database_sport_names)
        incomplete_sports = incomplete_combat_records(combat_sports)
        mma_records = fighters.get("all_fighters", [])
        profiled_mma = sum(1 for record in mma_records if isinstance(record, dict) and any(key in record for key in MMA_PROFILE_KEYS - {"record_d"}))
        print(f"Default Universe schema: {fighters.get('schema')}")
        print(f"Flat fighter records: {len(fighters.get('all_fighters', []))}")
        print(f"Source unique names: {len(source_names)}")
        print(f"Database unique names: {len(database_names)}")
        print(f"Missing unique names: {len(missing_names)}")
        print(f"Extra unique names: {len(extra_names)}")
        print(f"Missing source placements: {len(missing_placements)}")
        print(f"Incomplete MMA records: {len(incomplete_mma)}")
        print(f"Profiled MMA records: {profiled_mma}")
        print(f"MMA profile payload mismatches: {len(profile_mismatches)}")
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
        if incomplete_mma:
            print("Incomplete MMA records sample:")
            for line in incomplete_mma[:50]:
                print(f"  {line}")
        if profile_mismatches:
            print("MMA profile payload mismatch sample:")
            for placement, owner, name in profile_mismatches[:50]:
                print(f"  {placement}: {owner}: {name}")
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
        if missing_names or missing_placements or incomplete_mma or profile_mismatches or missing_sport_names or missing_sport_keys or incomplete_sports:
            raise SystemExit(1)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
