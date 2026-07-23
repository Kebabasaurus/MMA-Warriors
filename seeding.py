import json
import random
import sys
import traceback
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion
from real_sport_profiles import SPORT_PROFILE_VERSION, build_fallback_sport_profile, build_real_sport_profiles


class SeedMixin:
    def active_universe_marker(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return DATABASE_DIR / "active_universe.txt"

    def universe_database_path(self, name="Default Universe"):
        return self.seed_database_file(f"{self.safe_filename(name) if hasattr(self, 'safe_filename') else str(name).replace(' ', '_')}.universe.json")

    def default_player_media(self):
        return [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]

    def default_media_rights_packages(self):
        return [
            {"id": "local_fight_stream", "name": "Local Fight Stream", "type": "Regional Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 16, "prestige": 24, "budget": 24, "selectivity": 18, "min_popularity": 8, "min_card_quality": 36, "min_production": 20, "base_fee": 9000, "editorial_style": "Local access", "audience": "Regional"},
            {"id": "regional_combat_network", "name": "Regional Combat Network", "type": "Syndicated TV", "home_region": "USA", "markets": ["USA", "Canada", "Mexico"], "reach": 30, "prestige": 38, "budget": 38, "selectivity": 32, "min_popularity": 22, "min_card_quality": 44, "min_production": 30, "base_fee": 24000, "editorial_style": "Regional rivalries", "audience": "Core fight fans"},
            {"id": "combat_cable", "name": "Combat Cable", "type": "Cable", "home_region": "USA", "markets": ["USA", "Canada", "UK"], "reach": 44, "prestige": 52, "budget": 55, "selectivity": 48, "min_popularity": 36, "min_card_quality": 52, "min_production": 42, "base_fee": 58000, "editorial_style": "Sporting analysis", "audience": "Hardcore"},
            {"id": "euro_fight_tv", "name": "Euro Fight TV", "type": "Television / Streaming", "home_region": "Europe", "markets": ["Europe", "UK"], "reach": 48, "prestige": 57, "budget": 58, "selectivity": 50, "min_popularity": 38, "min_card_quality": 52, "min_production": 44, "base_fee": 72000, "editorial_style": "European stars", "audience": "International"},
            {"id": "pacific_combat_plus", "name": "Pacific Combat Plus", "type": "Streaming", "home_region": "Japan", "markets": ["Japan", "Asia", "Australia"], "reach": 52, "prestige": 61, "budget": 64, "selectivity": 54, "min_popularity": 40, "min_card_quality": 54, "min_production": 46, "base_fee": 86000, "editorial_style": "International spectacle", "audience": "Crossover"},
            {"id": "world_fight_pass", "name": "World Fight Pass", "type": "Global Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 66, "prestige": 70, "budget": 72, "selectivity": 62, "min_popularity": 52, "min_card_quality": 60, "min_production": 54, "base_fee": 145000, "editorial_style": "Deep fight library", "audience": "Global fight fans"},
            {"id": "prime_sports_network", "name": "Prime Sports Network", "type": "Premium Television", "home_region": "USA", "markets": list(REGIONS), "reach": 80, "prestige": 84, "budget": 88, "selectivity": 78, "min_popularity": 67, "min_card_quality": 70, "min_production": 68, "base_fee": 330000, "editorial_style": "Champions and stars", "audience": "Mainstream"},
            {"id": "global_sports_plus", "name": "Global Sports Plus", "type": "Global Premium Streaming", "home_region": "Worldwide", "markets": list(REGIONS), "reach": 92, "prestige": 94, "budget": 96, "selectivity": 91, "min_popularity": 82, "min_card_quality": 78, "min_production": 80, "base_fee": 760000, "editorial_style": "Global super fights", "audience": "Mass market"},
        ]

    def default_promotion_specs(self, fighter_db=None):
        data = (fighter_db or self.build_seed_fighter_database()).get("promotions", self.expanded_real_fighter_data())
        return [
            {"name": "Ultimate Fighting Championship", "region": "USA", "size": 96, "cash": 30_000_000, "reputation": "Global", "roster_key": "UFC", "target_roster_size": 400, "personality": "Super Shows"},
            {"name": "Professional Fighters League", "region": "USA", "size": 76, "cash": 8_500_000, "reputation": "Global", "roster_key": "PFL", "target_roster_size": 320, "personality": "Seasonal"},
            {"name": "ONE Championship", "region": "Asia", "size": 78, "cash": 9_000_000, "reputation": "Global", "roster_key": "ONE Championship", "target_roster_size": 320, "personality": "Big Names"},
            {"name": "RIZIN Fighting Federation", "region": "Japan", "size": 72, "cash": 6_000_000, "reputation": "International", "roster_key": "RIZIN Fighting Federation", "target_roster_size": 310, "personality": "Super Shows"},
            {"name": "KSW", "region": "Europe", "size": 70, "cash": 5_000_000, "reputation": "International", "roster_key": "KSW", "target_roster_size": 300, "personality": "Star Builder"},
            {"name": "Cage Warriors", "region": "UK", "size": 66, "cash": 2_500_000, "reputation": "International", "roster_key": "Cage Warriors", "target_roster_size": 300, "personality": "Prospect Builder"},
            {"name": "Legacy Fighting Alliance", "region": "USA", "size": 62, "cash": 1_800_000, "reputation": "National", "roster_key": "Legacy Fighting Alliance", "target_roster_size": 290, "personality": "Prospect Builder"},
            {"name": "Oktagon MMA", "region": "Europe", "size": 70, "cash": 4_800_000, "reputation": "International", "roster_key": "Oktagon MMA", "target_roster_size": 300, "personality": "Star Builder"},
            {"name": "BRAVE Combat Federation", "region": "Middle East", "size": 64, "cash": 3_100_000, "reputation": "International", "roster_key": "BRAVE Combat Federation", "target_roster_size": 290, "personality": "Prospect Builder"},
            {"name": "Absolute Championship Akhmat", "region": "Russia", "size": 66, "cash": 3_600_000, "reputation": "International", "roster_key": "Absolute Championship Akhmat", "target_roster_size": 290, "personality": "Seasonal"},
            {"name": "PRIDE Fighting Championships", "region": "Japan", "size": 78, "cash": 11_000_000, "reputation": "Global", "roster_key": "PRIDE Fighting Championships", "target_roster_size": 320, "personality": "Super Shows"},
            {"name": "Strikeforce", "region": "USA", "size": 74, "cash": 7_500_000, "reputation": "International", "roster_key": "Strikeforce", "target_roster_size": 310, "personality": "Star Builder"},
            {"name": "World Extreme Cagefighting", "region": "USA", "size": 68, "cash": 4_600_000, "reputation": "International", "roster_key": "World Extreme Cagefighting", "target_roster_size": 300, "personality": "Prospect Builder"},
        ]

    def build_universe_database_pack(self, name="Default Universe"):
        fighter_db = self.build_seed_fighter_database()
        combat_db = self.build_combat_sport_database()
        return {
            "schema": 3,
            "type": "universe_database",
            "database_name": name,
            "notes": "Editable universe database pack. Clone this file for real-life, fake, fantasy, or historic universes. Sections are intentionally enclosed so companies, fighters, combat sports, media, and regions can evolve independently.",
            "sections": {
                "fighters": fighter_db,
                "combat_sports": combat_db,
                "companies": {
                    "player_company": {"name": PLAYER_PROMOTION_NAME, "region": "UK", "reputation": "Regional Player Company", "popularity": 38, "stability": 52, "cash": 275000},
                    "promotions": self.default_promotion_specs(fighter_db),
                    "regional_feeders": [
                        {"name": "Japan Fight Circuit", "region": "Japan"},
                        {"name": "UK Regional MMA", "region": "UK"},
                        {"name": "North American Fighting League", "region": "USA"},
                        {"name": "European Challenge MMA", "region": "Europe"},
                        {"name": "Asia Rising Championship", "region": "Asia"},
                    ],
                },
                "media": {
                    "player_broadcasters": self.default_player_media(),
                    "rights_packages": self.default_media_rights_packages(),
                },
                "regions": self.seed_regions(),
            },
        }

    def ensure_default_universe_database(self):
        path = self.universe_database_path("Default Universe")
        if not path.exists():
            self.write_seed_database_file(path, self.build_universe_database_pack("Default Universe"))
        if not self.active_universe_marker().exists():
            self.active_universe_marker().write_text(path.name, encoding="utf-8")
        return path

    def active_universe_database_path(self):
        default = self.ensure_default_universe_database()
        marker = self.active_universe_marker()
        try:
            name = marker.read_text(encoding="utf-8").strip()
        except Exception:
            name = default.name
        path = DATABASE_DIR / name
        return path if path.exists() else default

    def load_universe_database_pack(self, path=None):
        path = path or self.active_universe_database_path()
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if data.get("type") != "universe_database" or "sections" not in data:
                raise ValueError("not a universe database pack")
            changed = False
            combat_section = data.get("sections", {}).get("combat_sports")
            if isinstance(combat_section, dict):
                if "prime_divisions" not in combat_section:
                    combat_section["prime_divisions"] = COMBAT_SPORT_REAL_DIVISIONS
                    changed = True
                rosters = combat_section.get("rosters", combat_section)
                if isinstance(rosters, dict) and "Boxing" in rosters:
                    profiles = self.normalized_combat_sport_profiles(rosters, combat_section.get("profiles", {}))
                    if profiles != combat_section.get("profiles"):
                        combat_section["profiles"] = profiles
                        changed = True
                schema = max(4, int(combat_section.get("schema", 1)))
                if combat_section.get("schema") != schema:
                    combat_section["schema"] = schema
                    changed = True
                if data.get("schema", 1) < 3:
                    data["schema"] = 3
                    changed = True
            # Enrich only the shipped Default Universe. Custom universes keep
            # complete control over which outlets exist; the default database
            # gains the expanded editable market without overwriting edits.
            if Path(path).name == self.universe_database_path("Default Universe").name:
                media_section = data.get("sections", {}).setdefault("media", {})
                packages = media_section.setdefault("rights_packages", [])
                fresh_packages = self.default_media_rights_packages()
                known = {str(row.get("id", row.get("name", ""))).lower() for row in packages if isinstance(row, dict)}
                for package in fresh_packages:
                    if package["id"].lower() not in known:
                        packages.append(package)
                        known.add(package["id"].lower())
                        changed = True
                if self.merge_default_fighter_database(data["sections"].setdefault("fighters", {})):
                    changed = True
                if self.merge_default_company_database(data["sections"].setdefault("companies", {})):
                    changed = True
                default_regions = data["sections"].setdefault("regions", {})
                missing_regions = [region for region in REGIONS if region not in default_regions]
                if missing_regions:
                    fresh_regions = self.seed_regions()
                    for region in missing_regions:
                        default_regions[region] = fresh_regions[region]
                        changed = True
                if self.merge_default_combat_sport_database(combat_section):
                    changed = True
            if changed:
                self.write_seed_database_file(Path(path), data)
            return data
        except Exception as exc:
            backup = Path(path).with_suffix(f".broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                Path(path).replace(backup)
            except Exception:
                pass
            default = self.build_universe_database_pack("Default Universe")
            default["repair_note"] = f"Pack was regenerated after load failure: {type(exc).__name__}: {exc}"
            default_path = self.universe_database_path("Default Universe")
            self.write_seed_database_file(default_path, default)
            self.active_universe_marker().write_text(default_path.name, encoding="utf-8")
            return default

    def merge_default_fighter_database(self, fighters):
        """Keep the shipped real-life pool additive as the default pack evolves."""
        shipped = self.build_seed_fighter_database()
        changed = False
        promotions = fighters.setdefault("promotions", {})
        for company, rows in shipped.get("promotions", {}).items():
            current = promotions.setdefault(company, [])
            known = {row[0] for row in current if isinstance(row, (list, tuple)) and row}
            for row in rows:
                if row[0] not in known:
                    current.append(row)
                    known.add(row[0])
                    changed = True
        # This is a specific data correction for the shipped universe, not a
        # wholesale replacement of an editor-owned roster row.
        for row in promotions.get("UFC", []):
            if not isinstance(row, list) or len(row) <= 5 or row[0] != "Conor McGregor":
                continue
            # The opening universe represents prime lightweight Conor, not his
            # later-career rating. Keep this explicit in the editable default
            # database as well as in the curated profile below.
            if row[4] != 92:
                row[4] = 92
                changed = True
            if row[5] != 27:
                row[5] = 27
                changed = True
        company_names = {row[0] for rows in promotions.values() for row in rows if isinstance(row, (list, tuple)) and row}
        for key in ("player_roster", "free_agents"):
            current = fighters.setdefault(key, [])
            known = {row[0] for row in current if isinstance(row, (list, tuple)) and row}
            for row in shipped.get(key, []):
                if row[0] not in known and row[0] not in company_names:
                    current.append(row)
                    known.add(row[0])
                    changed = True
        # A prime legend assigned to a company should not also be seeded as a
        # free agent in the same new world.
        free_agents = fighters.get("free_agents", [])
        filtered_agents = [row for row in free_agents if not isinstance(row, (list, tuple)) or not row or row[0] not in company_names]
        if len(filtered_agents) != len(free_agents):
            fighters["free_agents"] = filtered_agents
            changed = True
        # Data correction: Matthew Green is a 90-rated UK kickboxing free agent,
        # not a low-rated company prospect. Fix any existing universe that seeded
        # the earlier version so he appears correctly without a full rebuild.
        target_mg = ["Matthew Green", "Middleweight", "Free Agent", 78, 90, 24, 14, 1, "UK", "Kickboxer"]
        for company, rows in promotions.items():
            trimmed = [row for row in rows if not (isinstance(row, (list, tuple)) and row and row[0] == "Matthew Green")]
            if len(trimmed) != len(rows):
                promotions[company] = trimmed
                changed = True
        agents = fighters.setdefault("free_agents", [])
        existing_mg = next((row for row in agents if isinstance(row, (list, tuple)) and row and row[0] == "Matthew Green"), None)
        if existing_mg is None:
            agents.append(list(target_mg))
            changed = True
        elif list(existing_mg) != target_mg:
            agents[agents.index(existing_mg)] = list(target_mg)
            changed = True
        fighters["real_roster_depth_version"] = 1
        return changed

    def merge_default_company_database(self, companies):
        """Add newly shipped promotion definitions without replacing edited defaults."""
        changed = False
        current = companies.setdefault("promotions", [])
        known = {row.get("name") for row in current if isinstance(row, dict)}
        shipped_specs = self.default_promotion_specs()
        shipped_by_name = {spec["name"]: spec for spec in shipped_specs}
        for spec in shipped_specs:
            if spec["name"] not in known:
                current.append(spec)
                known.add(spec["name"])
                changed = True
        # The shipped Default Universe is additive, but roster capacity is part
        # of its intended simulation baseline. Raise stale targets once without
        # lowering any editor-selected value from a custom universe.
        if int(companies.get("roster_target_version", 0) or 0) < 2:
            for spec in current:
                if not isinstance(spec, dict):
                    continue
                shipped = shipped_by_name.get(spec.get("name"))
                if not shipped:
                    continue
                old_target = int(spec.get("target_roster_size", 0) or 0)
                new_target = int(shipped.get("target_roster_size", old_target) or old_target)
                if old_target < new_target:
                    spec["target_roster_size"] = new_target
                    changed = True
            companies["roster_target_version"] = 2
            changed = True
        if int(companies.get("geography_version", 0) or 0) < 2:
            expected_regions = {spec["name"]: spec["region"] for spec in shipped_specs}
            expected_regions.update({name: region for name, region in self.regional_feeder_specs()})
            for spec in current:
                if isinstance(spec, dict) and spec.get("name") in expected_regions:
                    region = expected_regions[spec["name"]]
                    if spec.get("region") != region:
                        spec["region"] = region
                        changed = True
            player = companies.setdefault("player_company", {})
            if player.get("name") == PLAYER_PROMOTION_NAME and player.get("region") != "UK":
                player["region"] = "UK"
                changed = True
            feeders = companies.setdefault("regional_feeders", [])
            feeder_by_name = {row.get("name"): row for row in feeders if isinstance(row, dict)}
            for name, region in self.regional_feeder_specs():
                if name not in feeder_by_name:
                    feeders.append({"name": name, "region": region})
                    changed = True
                elif feeder_by_name[name].get("region") != region:
                    feeder_by_name[name]["region"] = region
                    changed = True
            companies["geography_version"] = 2
            changed = True
        return changed

    def merge_default_combat_sport_database(self, combat_section):
        """Add shipped combat-sport depth without replacing editor-owned rows.

        The Default Universe is deliberately additive: a player can edit an
        existing profile, but a later update may still contribute new real
        athletes to a thin circuit. Per-sport de-duplication keeps a stale
        editable database from producing cloned fighters.
        """
        if not isinstance(combat_section, dict):
            return False
        changed = False
        shipped = self.builtin_combat_sport_real_roster_data()
        rosters = combat_section.setdefault("rosters", {})
        for sport, names in shipped.items():
            current = rosters.setdefault(sport, [])
            if not isinstance(current, list):
                current = []
                rosters[sport] = current
                changed = True
            clean = []
            seen = set()
            for name in current:
                normalized = str(name).strip()
                if normalized and normalized not in seen:
                    clean.append(normalized)
                    seen.add(normalized)
            if clean != current:
                rosters[sport] = current = clean
                changed = True
            for name in names:
                if name not in seen:
                    current.append(name)
                    seen.add(name)
                    changed = True
        divisions = combat_section.setdefault("prime_divisions", {})
        for sport, mapping in COMBAT_SPORT_REAL_DIVISIONS.items():
            target = divisions.setdefault(sport, {})
            if not isinstance(target, dict):
                target = {}
                divisions[sport] = target
                changed = True
            for name, division in mapping.items():
                if name not in target:
                    target[name] = division
                    changed = True
        profiles = self.normalized_combat_sport_profiles(rosters, combat_section.get("profiles", {}))
        if profiles != combat_section.get("profiles", {}):
            combat_section["profiles"] = profiles
            changed = True
        if int(combat_section.get("schema", 1) or 1) < 4:
            combat_section["schema"] = 4
            changed = True
        return changed

    def universe_section(self, section, default=None):
        pack = self.load_universe_database_pack()
        return pack.get("sections", {}).get(section, default)

    def seed_database_file(self, filename):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return DATABASE_DIR / filename

    def write_seed_database_file(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp.replace(path)

    def build_seed_fighter_database(self):
        return {
            "schema": 1,
            "notes": "Canonical new-game fighter seed database. Edit this file to change new-game MMA rosters without editing Python source.",
            "player_roster": self.cage_empire_fighter_data(),
            "free_agents": self.independent_fighter_data() + self.legend_fighter_data(),
            "promotions": self.expanded_real_fighter_data(),
        }

    def load_seed_fighter_database(self):
        section = self.universe_section("fighters", None)
        if section:
            return section
        path = self.seed_database_file("core_fighter_database.json")
        if not path.exists():
            self.write_seed_database_file(path, self.build_seed_fighter_database())
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "promotions" not in data:
                raise ValueError("core fighter database is missing promotions")
            return data
        except Exception as exc:
            backup = path.with_suffix(f".broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                path.replace(backup)
            except Exception:
                pass
            data = self.build_seed_fighter_database()
            data["repair_note"] = f"Database was regenerated after load failure: {type(exc).__name__}: {exc}"
            self.write_seed_database_file(path, data)
            return data

    def build_combat_sport_database(self):
        rosters = self.builtin_combat_sport_real_roster_data()
        return {
            "schema": 3,
            "notes": "Canonical combat-sport seed database. Edit rosters, profiles, and prime_divisions to change new-game athletes. Muay Thai also imports the Lethwei list as a linked striking roster.",
            "rosters": rosters,
            "prime_divisions": COMBAT_SPORT_REAL_DIVISIONS,
            "profiles": build_real_sport_profiles(rosters),
        }

    def normalized_combat_sport_profiles(self, rosters, supplied_profiles=None):
        """Fill profile gaps without overwriting edits in a custom universe."""
        supplied_profiles = supplied_profiles if isinstance(supplied_profiles, dict) else {}
        builtin_profiles = build_real_sport_profiles(self.builtin_combat_sport_real_roster_data())
        normalized = {}
        for sport, names in rosters.items():
            if not isinstance(names, list) or sport not in ("Boxing", "Kickboxing", "Muay Thai", "Lethwei", "Wrestling", "Brazilian Jiu-Jitsu"):
                continue
            source = supplied_profiles.get(sport, {}) if isinstance(supplied_profiles.get(sport, {}), dict) else {}
            sport_profiles = {}
            for index, name in enumerate(names):
                current = source.get(name)
                if isinstance(current, dict):
                    sport_profiles[name] = dict(current)
                elif name in builtin_profiles.get(sport, {}):
                    sport_profiles[name] = dict(builtin_profiles[sport][name])
                else:
                    sport_profiles[name] = build_fallback_sport_profile(sport, name, index=index)
            normalized[sport] = sport_profiles
        return normalized

    def load_combat_sport_database(self):
        section = self.universe_section("combat_sports", None)
        if section:
            rosters = section.get("rosters", section)
            if isinstance(rosters, dict) and "Boxing" in rosters:
                self.combat_sport_seed_divisions = section.get("prime_divisions", {}) if isinstance(section, dict) else {}
                self.combat_sport_seed_profiles = self.normalized_combat_sport_profiles(rosters, section.get("profiles", {}))
                return rosters
        path = self.seed_database_file("combat_sport_database.json")
        if not path.exists():
            self.write_seed_database_file(path, self.build_combat_sport_database())
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rosters = data.get("rosters", data)
            if not isinstance(rosters, dict) or "Boxing" not in rosters:
                raise ValueError("combat sport database is missing rosters")
            if self.merge_default_combat_sport_database(data):
                rosters = data["rosters"]
                self.write_seed_database_file(path, data)
            self.combat_sport_seed_divisions = data.get("prime_divisions", {})
            profiles = self.normalized_combat_sport_profiles(rosters, data.get("profiles", {}))
            if not self.combat_sport_seed_divisions or profiles != data.get("profiles") or data.get("schema", 1) < 4:
                data = {"schema": 4, "notes": self.build_combat_sport_database()["notes"],
                        "rosters": rosters, "prime_divisions": self.combat_sport_seed_divisions or COMBAT_SPORT_REAL_DIVISIONS,
                        "profiles": profiles}
                self.write_seed_database_file(path, data)
                self.combat_sport_seed_divisions = data["prime_divisions"]
            self.combat_sport_seed_profiles = profiles
            return rosters
        except Exception as exc:
            backup = path.with_suffix(f".broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                path.replace(backup)
            except Exception:
                pass
            data = self.build_combat_sport_database()
            data["repair_note"] = f"Database was regenerated after load failure: {type(exc).__name__}: {exc}"
            self.write_seed_database_file(path, data)
            self.combat_sport_seed_divisions = data["prime_divisions"]
            self.combat_sport_seed_profiles = data["profiles"]
            return data["rosters"]

    def seed_roster(self):
        seed_db = self.load_seed_fighter_database()
        featured = seed_db.get("player_roster") or self.cage_empire_fighter_data()
        featured = self.unique_fighter_rows(featured)
        roster = [self.create_real_fighter(*row, player_owned=True) for row in featured]
        promotion_data = seed_db.get("promotions") or self.expanded_real_fighter_data()
        company_names = {row[0] for rows in promotion_data.values() for row in rows}
        existing_names = {fighter.name for fighter in roster} | company_names
        while len(roster) < 96:
            prospect = self.create_generated_fighter(8, 48, 43, 82)
            self.avoid_name_collision(prospect, existing_names)
            prospect.contract_months = random.randint(6, 22)
            prospect.exclusive = True
            prospect.contract_type = "Exclusive"
            roster.append(prospect)
        self.ensure_roster_division_depth(roster, self.player_region, self.player_company_name, self.company_pop, player_owned=True)
        self.seed_relationships(roster)
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(roster, self.belts, self.player_company_name, self.player_region, self.company_pop, player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history)
        return roster

    def seed_free_agents(self):
        seed_db = self.load_seed_fighter_database()
        promotion_data = seed_db.get("promotions") or self.expanded_real_fighter_data()
        company_names = {row[0] for rows in promotion_data.values() for row in rows}
        reserved_names = {fighter.name for fighter in getattr(self, "roster", [])}
        free_agent_rows = seed_db.get("free_agents") or (self.independent_fighter_data() + self.legend_fighter_data())
        names = [row for row in free_agent_rows if row[0] not in company_names and row[0] not in reserved_names]
        names = self.unique_fighter_rows(names)
        fighters = [self.create_real_fighter(*row, player_owned=False) for row in names]
        existing_names = {fighter.name for fighter in fighters} | company_names | reserved_names
        for fighter in fighters:
            fighter.exclusive = False
            fighter.contract_type = "Non-Exclusive"
            fighter.contract_months = 0
            if fighter.age >= 40:
                seed = sum((index + 3) * ord(char) for index, char in enumerate(fighter.name))
                fighter.media_heat = 20 + seed % 36
                fighter.popularity = min(100, fighter.popularity + 2 + seed % 7)
            else:
                seed = sum((index + 3) * ord(char) for index, char in enumerate(fighter.name))
                fighter.popularity = max(8, fighter.popularity - 4 - seed % 11)
        while len(fighters) < 220:
            fighter = self.create_generated_fighter(5, 42, 38, 80)
            self.avoid_name_collision(fighter, existing_names)
            fighters.append(fighter)
        self.ensure_free_agent_division_depth(fighters, reserved_names=existing_names)
        self.seed_relationships(fighters)
        return fighters

    def real_fighter_data(self):
        return {
            "UFC": [
                ("Islam Makhachev", "Welterweight", "UFC", 96, 95, 34, 28, 1, "Europe", "Sambo"),
                ("Ilia Topuria", "Lightweight", "UFC", 94, 94, 29, 17, 0, "Europe", "Boxer"),
                ("Justin Gaethje", "Lightweight", "UFC", 91, 90, 37, 27, 5, "USA", "Kickboxer"),
                ("Arman Tsarukyan", "Lightweight", "UFC", 82, 90, 29, 23, 3, "Europe", "Wrestler"),
                ("Charles Oliveira", "Lightweight", "UFC", 88, 89, 36, 37, 11, "Brazil", "BJJ"),
                ("Max Holloway", "Lightweight", "UFC", 93, 90, 34, 27, 9, "USA", "Boxer"),
                ("Paddy Pimblett", "Lightweight", "UFC", 84, 82, 31, 23, 3, "UK", "BJJ"),
                ("Benoit Saint Denis", "Lightweight", "UFC", 72, 82, 30, 14, 4, "Europe", "Sambo"),
                ("Ian Machado Garry", "Welterweight", "UFC", 84, 88, 28, 17, 1, "Europe", "Kickboxer"),
                ("Carlos Prates", "Welterweight", "UFC", 78, 87, 32, 24, 7, "Brazil", "Muay Thai"),
                ("Michael Morales", "Welterweight", "UFC", 74, 87, 27, 19, 0, "Mexico", "Boxer"),
                ("Jack Della Maddalena", "Welterweight", "UFC", 83, 88, 29, 18, 4, "Australia", "Boxer"),
                ("Belal Muhammad", "Welterweight", "UFC", 82, 87, 38, 24, 5, "USA", "Wrestler"),
                ("Sean Brady", "Welterweight", "UFC", 72, 84, 33, 17, 2, "USA", "Grappler"),
                ("Khamzat Chimaev", "Middleweight", "UFC", 92, 94, 32, 15, 1, "Europe", "Wrestler"),
                ("Sean Strickland", "Middleweight", "UFC", 86, 88, 35, 31, 7, "USA", "Boxer"),
                ("Dricus Du Plessis", "Middleweight", "UFC", 86, 89, 32, 23, 3, "Europe", "Well-Rounded"),
                ("Nassourdine Imavov", "Middleweight", "UFC", 76, 86, 31, 17, 4, "Europe", "Kickboxer"),
                ("Caio Borralho", "Middleweight", "UFC", 74, 86, 33, 18, 2, "Brazil", "BJJ"),
                ("Robert Whittaker", "Middleweight", "UFC", 88, 88, 35, 27, 9, "Australia", "Karate"),
                ("Alex Pereira", "Light Heavyweight", "UFC", 95, 91, 39, 13, 3, "Brazil", "Kickboxer"),
                ("Magomed Ankalaev", "Light Heavyweight", "UFC", 84, 90, 34, 20, 2, "Europe", "Sambo"),
                ("Jiri Prochazka", "Light Heavyweight", "UFC", 87, 88, 33, 32, 6, "Europe", "Dynamic Attacker"),
                ("Carlos Ulberg", "Light Heavyweight", "UFC", 77, 86, 35, 14, 1, "Australia", "Kickboxer"),
                ("Tom Aspinall", "Heavyweight", "UFC", 90, 91, 33, 15, 3, "UK", "Well-Rounded"),
                ("Ciryl Gane", "Heavyweight", "UFC", 87, 88, 36, 13, 2, "Europe", "Kickboxer"),
                ("Alexander Volkov", "Heavyweight", "UFC", 81, 86, 37, 40, 11, "Europe", "Kickboxer"),
                ("Sergei Pavlovich", "Heavyweight", "UFC", 80, 86, 34, 20, 3, "Europe", "Boxer"),
                ("Alexander Volkanovski", "Featherweight", "UFC", 90, 91, 37, 28, 4, "Australia", "Well-Rounded"),
                ("Movsar Evloev", "Featherweight", "UFC", 77, 88, 32, 20, 0, "Europe", "Wrestler"),
                ("Diego Lopes", "Featherweight", "UFC", 80, 86, 31, 27, 8, "Brazil", "BJJ"),
                ("Lerone Murphy", "Featherweight", "UFC", 73, 84, 34, 17, 1, "UK", "Boxer"),
                ("Petr Yan", "Bantamweight", "UFC", 86, 89, 33, 20, 5, "Europe", "Boxer"),
                ("Merab Dvalishvili", "Bantamweight", "UFC", 85, 89, 35, 21, 5, "Europe", "Wrestler"),
                ("Umar Nurmagomedov", "Bantamweight", "UFC", 79, 88, 30, 20, 1, "Europe", "Sambo"),
                ("Sean O'Malley", "Bantamweight", "UFC", 91, 87, 31, 19, 3, "USA", "Kickboxer"),
                ("Cory Sandhagen", "Bantamweight", "UFC", 80, 86, 34, 18, 6, "USA", "Kickboxer"),
                ("Joshua Van", "Flyweight", "UFC", 73, 84, 24, 14, 2, "USA", "Boxer"),
                ("Tatsuro Taira", "Flyweight", "UFC", 72, 84, 26, 16, 1, "Japan", "BJJ"),
                ("Brandon Royval", "Flyweight", "UFC", 78, 83, 33, 17, 7, "USA", "Submission Hunter"),
                ("Lone'er Kavanagh", "Flyweight", "UFC", 62, 78, 27, 8, 0, "UK", "Kickboxer"),
                ("Mackenzie Dern", "Flyweight", "UFC", 79, 84, 33, 16, 5, "USA", "BJJ"),
                ("Gillian Robertson", "Flyweight", "UFC", 69, 81, 31, 16, 8, "Canada", "BJJ"),
                ("Kayla Harrison", "Bantamweight", "UFC", 88, 90, 36, 19, 1, "USA", "Judo"),
            ],
            "PFL": [
                ("Usman Nurmagomedov", "Lightweight", "PFL", 86, 90, 28, 18, 0, "Europe", "Sambo"),
                ("Paul Hughes", "Lightweight", "PFL", 74, 84, 29, 13, 2, "UK", "Boxer"),
                ("Shem Rock", "Lightweight", "PFL", 58, 76, 32, 11, 2, "UK", "BJJ"),
                ("Alfie Davis", "Lightweight", "PFL", 50, 75, 34, 17, 5, "UK", "Kickboxer"),
                ("Clay Collard", "Lightweight", "PFL", 68, 79, 33, 25, 13, "USA", "Boxer"),
                ("Tunez Nurgozhay", "Light Heavyweight", "PFL", 52, 76, 27, 11, 0, "Europe", "Kickboxer"),
                ("Impa Kasanganay", "Light Heavyweight", "PFL", 70, 82, 32, 18, 5, "USA", "Well-Rounded"),
                ("Antonio Carlos Jr.", "Light Heavyweight", "PFL", 67, 81, 36, 19, 6, "Brazil", "BJJ"),
                ("Sullivan Cauley", "Light Heavyweight", "PFL", 50, 77, 30, 8, 2, "USA", "Wrestler"),
                ("Sergey Bilostenniy", "Heavyweight", "PFL", 54, 78, 30, 15, 4, "Europe", "Kickboxer"),
                ("Abraham Bably", "Heavyweight", "PFL", 45, 74, 32, 8, 3, "USA", "Wrestler"),
                ("Oleg Popov", "Heavyweight", "PFL", 58, 80, 33, 19, 1, "Europe", "Sambo"),
                ("Dakota Ditcheva", "Flyweight", "PFL", 75, 84, 28, 14, 0, "UK", "Muay Thai"),
                ("Liz Carmouche", "Flyweight", "PFL", 74, 82, 42, 26, 8, "USA", "Wrestler"),
                ("Jena Bishop", "Flyweight", "PFL", 49, 76, 38, 11, 3, "USA", "BJJ"),
                ("Taila Santos", "Flyweight", "PFL", 69, 82, 33, 22, 4, "Brazil", "Muay Thai"),
                ("Adam Borics", "Featherweight", "PFL", 61, 81, 33, 20, 4, "Europe", "Kickboxer"),
                ("Gabriel Braga", "Featherweight", "PFL", 62, 82, 28, 17, 3, "Brazil", "Kickboxer"),
                ("Brendan Loughnane", "Featherweight", "PFL", 70, 81, 36, 30, 6, "UK", "Kickboxer"),
                ("Jesus Pinedo", "Featherweight", "PFL", 62, 80, 30, 23, 6, "Brazil", "Boxer"),
                ("Magomed Umalatov", "Welterweight", "PFL", 61, 83, 33, 17, 0, "Europe", "Sambo"),
                ("Don Madge", "Welterweight", "PFL", 53, 77, 35, 11, 4, "Europe", "Muay Thai"),
                ("Logan Storley", "Welterweight", "PFL", 64, 82, 33, 16, 3, "USA", "Wrestler"),
                ("Brennan Ward", "Welterweight", "PFL", 58, 77, 38, 17, 7, "USA", "Boxer"),
                ("Johnny Eblen", "Middleweight", "PFL", 75, 87, 34, 16, 1, "USA", "Wrestler"),
                ("Costello van Steenis", "Middleweight", "PFL", 57, 78, 33, 15, 3, "Europe", "Kickboxer"),
                ("Fabian Edwards", "Middleweight", "PFL", 63, 80, 33, 13, 4, "UK", "Kickboxer"),
                ("Aaron Jeffery", "Middleweight", "PFL", 51, 78, 33, 15, 5, "Canada", "Boxer"),
            ],
            "Cage Warriors": [
                ("George Hardwick", "Lightweight", "Cage Warriors", 56, 78, 29, 13, 2, "UK", "Boxer"),
                ("Harry Hardwick", "Featherweight", "Cage Warriors", 55, 78, 31, 12, 3, "UK", "Well-Rounded"),
                ("Morgan Charriere", "Featherweight", "Cage Warriors", 61, 79, 30, 19, 10, "Europe", "Kickboxer"),
                ("Mason Jones", "Lightweight", "Cage Warriors", 66, 81, 31, 15, 2, "UK", "Boxer"),
                ("Luke Riley", "Featherweight", "Cage Warriors", 50, 76, 27, 10, 0, "UK", "Boxer"),
                ("Jordan Vucenic", "Featherweight", "Cage Warriors", 55, 77, 30, 13, 3, "UK", "Well-Rounded"),
                ("Dominique Wooding", "Bantamweight", "Cage Warriors", 49, 76, 30, 9, 5, "UK", "Kickboxer"),
                ("Lone'er Kavanagh CW", "Flyweight", "Cage Warriors", 48, 75, 27, 7, 0, "UK", "Kickboxer"),
                ("Shajidul Haque", "Flyweight", "Cage Warriors", 44, 74, 33, 16, 5, "UK", "Wrestler"),
                ("Sam Creasey", "Flyweight", "Cage Warriors", 45, 74, 38, 18, 5, "UK", "Well-Rounded"),
                ("James Sheehan", "Welterweight", "Cage Warriors", 47, 75, 29, 9, 3, "Europe", "Wrestler"),
                ("Olli Santalahti", "Welterweight", "Cage Warriors", 44, 74, 31, 14, 5, "Europe", "Wrestler"),
                ("Dario Bellandi", "Middleweight", "Cage Warriors", 46, 75, 31, 8, 2, "Europe", "Kickboxer"),
                ("Andy Clamp", "Light Heavyweight", "Cage Warriors", 43, 73, 35, 12, 3, "UK", "Wrestler"),
                ("Modestas Bukauskas", "Light Heavyweight", "Cage Warriors", 56, 78, 32, 16, 6, "UK", "Kickboxer"),
                ("Mick Stanton", "Middleweight", "Cage Warriors", 48, 74, 37, 13, 8, "UK", "Wrestler"),
                ("Darren Stewart", "Middleweight", "Cage Warriors", 58, 77, 35, 16, 10, "UK", "Boxer"),
                ("Paddy McCorry", "Middleweight", "Cage Warriors", 42, 72, 28, 6, 1, "UK", "Kickboxer"),
                ("Omiel Brown", "Welterweight", "Cage Warriors", 43, 73, 29, 6, 2, "UK", "Wrestler"),
                ("Matthew Bonner", "Middleweight", "Cage Warriors", 45, 73, 35, 16, 9, "UK", "BJJ"),
                ("Caolan Loughran", "Bantamweight", "Cage Warriors", 51, 76, 30, 10, 2, "Europe", "Wrestler"),
                ("Nathan Fletcher", "Bantamweight", "Cage Warriors", 44, 74, 28, 9, 1, "UK", "BJJ"),
                ("Jack Cartwright", "Bantamweight", "Cage Warriors", 47, 75, 31, 11, 2, "UK", "Boxer"),
                ("Agy Sardari", "Lightweight", "Cage Warriors", 43, 73, 33, 16, 5, "Europe", "Kickboxer"),
                ("Mehdi Ben Lakhdhar", "Lightweight", "Cage Warriors", 42, 72, 33, 7, 2, "Europe", "Wrestler"),
                ("James Webb", "Middleweight", "Cage Warriors", 45, 74, 36, 11, 4, "UK", "BJJ"),
                ("Ian Machado Garry CW", "Welterweight", "Cage Warriors", 58, 76, 28, 7, 0, "Europe", "Kickboxer"),
                ("Tom Aspinall CW", "Heavyweight", "Cage Warriors", 54, 76, 33, 7, 2, "UK", "Well-Rounded"),
            ],
        }

    def create_real_fighter(self, name, weight, org, popularity, skill, age, wins, losses, region, style, player_owned=False):
        spread = lambda amount=8: random.randint(-amount, amount)
        fighter = Fighter(
            name=name,
            weight=weight,
            age=age,
            record_w=wins,
            record_l=losses,
            striking=max(25, min(99, skill + spread())),
            wrestling=max(25, min(99, skill + spread())),
            grappling=max(25, min(99, skill + spread())),
            cardio=max(25, min(99, skill + spread(7))),
            chin=max(25, min(99, skill + spread(9))),
            popularity=popularity,
            momentum=random.randint(-1, 5),
            morale=random.randint(55, 92),
            purse=max(6000, round((popularity * 700 + skill * 550) * (1.6 if org == "UFC" else 1.0))),
            gender=self.infer_gender(name),
        )
        self.enrich_fighter(fighter, player_owned=player_owned)
        fighter.region = region
        fighter.nationality = self.infer_nationality(name, region)
        fighter.style = style if style in STYLES else "Well-Rounded"
        fighter.camp = org
        self.assign_regional_identity(fighter, region, birth_region=region, force=True)
        self.apply_real_fighter_birthplace(fighter, region)
        fighter.detailed_skills = None
        self.apply_real_fighter_profile(fighter, skill)
        if fighter.name == "Conor McGregor":
            fighter.prime_rating_profile_version = 1
        prime_age = self.historic_prime_age_overrides().get(fighter.name)
        if prime_age is not None:
            fighter.age = prime_age
            fighter.prime_start = max(24, prime_age - 3)
            fighter.prime_end = max(fighter.prime_start + 5, prime_age + 6)
            fighter.prime_legend_age_override_version = 1
        if fighter.name == "Matthew Green":
            # A McGregor-style southpaw striker whose signature is devastating
            # power kicks — low kicks above all: the hardest, most technical
            # weapon in his arsenal.
            fighter.height = "5'10"
            fighter.stance = "Southpaw"
            fighter.trait = "Prospect Mindset"
            fighter.behaviour = "Dynamic Attacker"
            fighter.walk_weight = 185
            fighter.detailed_skills.update({
                "low_kick_power": 98, "low_kick_technique": 96, "low_kick_speed": 94,
                "high_kick_power": 90, "high_kick_technique": 88, "high_kick_speed": 88,
                "creative_kicks": 94, "kick_defence": 88,
                "punch_power": 95, "punch_technique": 92, "hand_speed": 92, "creative_punches": 92,
                "footwork": 92, "feints": 92, "head_movement": 90,
            })
            for key in MENTAL_SKILLS:
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), 92)
            for key in PHYSICAL_SKILLS:
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), 90)
            fighter.detailed_skills["killer_instinct"] = 95
            fighter.detailed_skills["confidence"] = 96
            self.sync_broad_skills_from_details(fighter)
            # Lock the headline ratings so he debuts as a true 90 with a 96 ceiling.
            fighter.striking = 95
            fighter.wrestling = 86
            fighter.grappling = 85
            fighter.cardio = 91
            fighter.chin = 90
            fighter.power = 95
            fighter.star_quality = max(fighter.star_quality, 82)
            fighter.charisma = max(fighter.charisma, 85)
        if fighter.name == "Mikey Musumeci":
            fighter.height = "5'4"
            fighter.stance = "Orthodox"
            fighter.style = "BJJ"
            fighter.trait = "Submission Ace"
            fighter.behaviour = "Submission Hunter"
            fighter.walk_weight = 135
            # World-class submission grappling; striking is a clear work in progress.
            elite_ground = (
                "submission_attack", "guard_work", "back_control", "leg_locks", "transitions",
                "positional_ability", "scrambles", "bottom_control", "mount_control", "submission_defence_detail",
            )
            for key in elite_ground:
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), random.randint(94, 98))
            fighter.detailed_skills["ground_striking"] = max(fighter.detailed_skills.get("ground_striking", 50), 74)
            fighter.detailed_skills["top_control"] = max(fighter.detailed_skills.get("top_control", 50), 88)
            for key in ("flexibility", "composure", "consistency", "discipline", "dedication", "conditioning"):
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), random.randint(86, 93))
            # Grappling entries: strong at getting it to the mat, modest wrestling power.
            for key in ("takedowns", "takedown_setup", "chain_wrestling", "clinch_takedowns"):
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), 72)
            # Striking is his weakness relative to his ground game.
            for key in ("punch_power", "high_kick_power", "hand_speed", "creative_punches"):
                fighter.detailed_skills[key] = min(fighter.detailed_skills.get(key, 50), random.randint(58, 66))
            self.sync_broad_skills_from_details(fighter)
            fighter.grappling = max(fighter.grappling, 96)
            fighter.submissions = max(getattr(fighter, "submissions", 65), 97)
            fighter.submission_defence = max(getattr(fighter, "submission_defence", 65), 93)
            fighter.ground_control = max(fighter.ground_control, 90)
            fighter.chin = max(fighter.chin, 76)
            fighter.power = min(getattr(fighter, "power", 65), 60)
            fighter.finishing_instinct = max(fighter.finishing_instinct, 90)
            fighter.potential = 95
        profile_rating = self.real_fighter_profiles().get(fighter.name, {}).get("rating", skill)
        fighter.potential = max(fighter.overall, min(98, profile_rating + 6))
        if fighter.name in self.prime_legend_ages():
            fighter.legend_prime_age_version = 1
        fighter.contract_months = random.randint(10, 30) if player_owned else 0
        fighter.exclusive = player_owned
        fighter.contract_type = "Exclusive" if player_owned else "Non-Exclusive"
        fighter.rank_score = self.rank_value(fighter)
        return fighter

    def infer_gender(self, name):
        female_names = {
            "Mackenzie Dern", "Gillian Robertson", "Kayla Harrison", "Dakota Ditcheva",
            "Liz Carmouche", "Jena Bishop", "Taila Santos", "Elora Dana", "Ronda Rousey",
            "Amanda Nunes", "Zhang Weili", "Valentina Shevchenko", "Alexa Grasso",
            "Manon Fiorot", "Erin Blanchfield", "Rose Namajunas", "Yan Xiaonan",
            "Virna Jandiroba", "Tatiana Suarez", "Jessica Andrade", "Amanda Ribas",
            "Maycee Barber", "Natalia Silva", "Jasmine Jasudavicius", "Tracy Cortez",
            "Ketlen Vieira", "Raquel Pennington", "Julianna Pena", "Holly Holm",
            "Macy Chiasson", "Norma Dumont", "Mayra Bueno Silva", "Iasmin Lucindo",
            "Karolina Kowalkiewicz", "Loopy Godinez", "Tabatha Ricci", "Molly McCann",
            "Joanne Wood", "Cris Cyborg", "Larissa Pacheco", "Leah McCourt",
            "Sara Collins", "Danni Neilan", "Eimear Darcy", "Shanelle Dyer",
            "Mackenzie Dern", "Marina Rodriguez", "Angela Hill", "Tecia Pennington",
            "Kayla Harrison", "Irene Aldana", "Yana Santos", "Germaine de Randamie",
            "Dakota Ditcheva", "Taila Santos", "Liz Carmouche", "Kana Watanabe",
            "Aspen Ladd", "Julia Budd", "Michelle Montague", "Denise Kielholtz",
            "Mandy Bohm", "Kennedy Freeman", "Awa Sow",
            "Meng Bo", "Jihin Radzuan", "Alyona Rassohyna", "Chihiro Sawada",
            "Miyuu Yamamoto", "Si Woo Park", "Sena Kubota", "Ayaka Watanabe",
            "Wiktoria Czyzewska", "Adrianna Kreft", "Chelsea Chandler", "Katharina Lehner",
            "Sam Hughes", "Tereza Bleda", "Lucie Pudilova", "Sarah Kaufman",
            "Paige VanZant", "Miesha Tate", "Cat Zingano", "Julia Avila",
            "Pearl Gonzalez", "Vanessa Demopoulos", "Denise Gomes", "Rin Nakai",
            "Seo Hee Ham", "Ayaka Hamasaki", "Amanda Lemos", "Fatima Kline",
            "Alexia Thainara", "Mizuki", "Piera Rodriguez", "Jaqueline Amorim",
            "Talita Alencar", "Miranda Maverick", "Karine Silva", "Casey O'Neill",
            "Wang Cong", "Eduarda Moura", "JJ Aldrich", "Gabriella Fernandes",
            "Joselyne Edwards", "Ailin Perez", "Luana Santos", "Jacqueline Cavalcanti",
            "Karol Rosa", "Bia Mesquita", "Nora Cornolle", "Michelle Montague",
            "Melissa Croden", "Daria Zhelezniakova", "Julianna Peña",
            "Shayna Baszler", "Paulina Wisniewska", "Viviane Araujo", "Sabrinna de Sousa",
            "Sumiko Inaba", "Montana De La Rosa", "Angela Lee", "Stamp Fairtex",
            "Xiong Jing Nan", "Denice Zamboanga", "Itsuki Hirata", "Rena Kubota",
            "Seika Izawa", "Kanna Asakura", "Karolina Owczarz", "Ewelina Wozniak",
            "Natalia Baczynska", "Alyse Anderson", "Shinju Nozawa-Auclair",
            "Vanessa Demopoulos LFA", "Mayra Cantuaria",
            "Joanna Jedrzejczyk", "Gina Carano", "Lucia Szabova", "Sophie Renshaw", "Erin Calvert", "Mia Kellett", "Hannah Wren",
        }
        return "Female" if name in female_names else "Male"

    def infer_nationality(self, name, region):
        overrides = {
            "Darren Till": "English",
            "Yoel Romero": "Cuban",
            "Hector Lombard": "Cuban",
            "Roberto Soldic": "Croatian",
            "Anatoly Malykhin": "Russian",
            "Christian Lee": "Canadian-American",
            "Aung La Nsang": "Burmese-American",
            "Kyoji Horiguchi": "Japanese",
            "Kai Asakura": "Japanese",
            "Mikuru Asakura": "Japanese",
            "Kleber Koike Erbst": "Brazilian-Japanese",
            "Michael Page": "English",
            "Rin Nakai": "Japanese",
            "Seo Hee Ham": "South Korean",
            "Ayaka Hamasaki": "Japanese",
            "Cat Zingano": "American",
            "Miesha Tate": "American",
            "Paige VanZant": "American",
            "Julia Avila": "American",
            "Pearl Gonzalez": "American",
            "Vanessa Demopoulos": "American",
        }
        if name in overrides:
            return overrides[name]
        by_region = {
            "USA": "American",
            "UK": "British",
            "Brazil": "Brazilian",
            "Japan": "Japanese",
            "Canada": "Canadian",
            "Mexico": "Mexican",
            "Australia": "Australian",
            "Europe": "European",
            "Asia": "Asian",
            "Africa": "African",
            "New Zealand": "New Zealander",
        }
        return by_region.get(region, region)

    def weighted_birth_region(self, market_region):
        """Mostly local talent, with a small but visible migration pipeline."""
        market_region = market_region if market_region in REGIONS else random.choice(REGION_GENERATION_POOL)
        links = [region for region in REGIONAL_MIGRATION_LINKS.get(market_region, []) if region in REGIONS and region != market_region]
        outsiders = [region for region in REGIONS if region not in links and region != market_region]
        choices = [market_region] + links + outsiders
        weights = [76] + [max(3, 18 / max(1, len(links)))] * len(links) + [max(0.4, 6 / max(1, len(outsiders)))] * len(outsiders)
        return random.choices(choices, weights=weights, k=1)[0]

    def generated_birth_identity(self, birth_region):
        profiles = REGION_IDENTITY_PROFILES.get(birth_region, [])
        if not profiles:
            country = REGION_COUNTRIES.get(birth_region, birth_region)
            return country, self.infer_nationality("", birth_region), REGION_CITIES.get(birth_region, [birth_region])
        country, nationality, cities = random.choice(profiles)
        return country, nationality, cities

    def real_fighter_birthplace_data(self):
        if hasattr(self, "_real_fighter_birthplace_cache"):
            return self._real_fighter_birthplace_cache
        path = ASSET_DIR / "real_fighter_birthplaces.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            fighters = payload.get("fighters", {}) if isinstance(payload, dict) else {}
            self._real_fighter_birthplace_cache = fighters if isinstance(fighters, dict) else {}
        except (OSError, ValueError, TypeError):
            self._real_fighter_birthplace_cache = {}
        return self._real_fighter_birthplace_cache

    def apply_real_fighter_birthplace(self, fighter, fallback_region):
        identity = self.real_fighter_birthplace_data().get(fighter.name)
        if not identity:
            # Missing is preferable to assigning a real person a random city.
            fighter.hometown = ""
            return fighter
        city = str(identity.get("city", "")).strip()
        birth_country = str(identity.get("birth_country", "") or identity.get("citizenship", "")).strip()
        citizenship = str(identity.get("citizenship", "") or birth_country).strip()
        if fallback_region not in REGIONS:
            fallback_region = fighter.birth_region if fighter.birth_region in REGIONS else fighter.region if fighter.region in REGIONS else "USA"
        birth_region = COUNTRY_TO_REGION.get(birth_country, fallback_region)
        fighter.hometown = city
        fighter.birth_country = birth_country or REGION_COUNTRIES.get(birth_region, birth_region)
        fighter.birth_region = birth_region
        fighter.nationality = COUNTRY_NATIONALITIES.get(citizenship, citizenship or self.infer_nationality(fighter.name, birth_region))
        connections = list(getattr(fighter, "cultural_connections", []) or [])
        fighter.cultural_connections = list(dict.fromkeys([birth_region] + connections))
        popularity = getattr(fighter, "regional_popularity", {}) or {}
        popularity[birth_region] = max(popularity.get(birth_region, 0), min(78, 18 + fighter.popularity // 3))
        fighter.regional_popularity = popularity
        return fighter

    def assign_regional_identity(self, fighter, market_region=None, birth_region=None, generated=False, force=False):
        """Give a fighter a persistent origin, migration story, and market appeal."""
        if getattr(fighter, "birth_region", "") and not force:
            return fighter
        market_region = market_region if market_region in REGIONS else (fighter.region if fighter.region in REGIONS else random.choice(REGION_GENERATION_POOL))
        birth_region = birth_region if birth_region in REGIONS else (self.weighted_birth_region(market_region) if generated else market_region)
        residence = market_region if generated or market_region != birth_region else birth_region
        training_choices = [residence, birth_region] + [region for region in REGIONAL_MIGRATION_LINKS.get(residence, []) if region in REGIONS]
        training_region = random.choices(training_choices, weights=[64, 22] + [4] * max(0, len(training_choices) - 2), k=1)[0]
        connections = list(dict.fromkeys([birth_region, residence, training_region]))
        if random.random() < 0.22:
            cultural_options = [region for region in REGIONAL_MIGRATION_LINKS.get(birth_region, []) if region in REGIONS and region not in connections]
            if cultural_options:
                connections.append(random.choice(cultural_options))
        popularity = {region: random.randint(1, 8) for region in REGIONS}
        popularity[birth_region] = max(popularity[birth_region], min(78, random.randint(18, 34) + fighter.popularity // 3))
        popularity[residence] = max(popularity[residence], min(74, random.randint(14, 30) + fighter.popularity // 3))
        popularity[training_region] = max(popularity[training_region], min(55, random.randint(8, 22) + fighter.popularity // 5))
        for connection in connections[3:]:
            popularity[connection] = max(popularity[connection], random.randint(9, 24))
        if generated:
            birth_country, nationality, hometowns = self.generated_birth_identity(birth_region)
        else:
            birth_country = REGION_COUNTRIES.get(birth_region, birth_region)
            nationality = self.infer_nationality(fighter.name, birth_region)
            hometowns = REGION_CITIES.get(birth_region, [birth_region])
        fighter.birth_country = birth_country
        fighter.birth_region = birth_region
        fighter.hometown = random.choice(hometowns)
        fighter.residence = residence
        fighter.training_location = training_region
        fighter.fighting_base = residence
        fighter.cultural_connections = connections
        fighter.regional_popularity = popularity
        fighter.home_event_history = getattr(fighter, "home_event_history", None) or []
        fighter.region = residence  # legacy shorthand: current fighting base
        if generated:
            fighter.nationality = nationality
        return fighter

    def fighter_event_connection(self, fighter, region, city=""):
        """Return the strongest reason this market sees a fighter as one of its own."""
        if not fighter:
            return {"level": "Neutral", "strength": 0.0, "market_popularity": 0}
        market_popularity = (getattr(fighter, "regional_popularity", {}) or {}).get(region, 0)
        if city and city == getattr(fighter, "hometown", ""):
            level, strength = "Hometown", 1.0
        elif region == getattr(fighter, "birth_region", ""):
            level, strength = "National home", 0.80
        elif region == getattr(fighter, "residence", "") or region == getattr(fighter, "fighting_base", ""):
            level, strength = "Adopted home", 0.66
        elif region == getattr(fighter, "training_location", ""):
            level, strength = "Training base", 0.52
        elif region in (getattr(fighter, "cultural_connections", None) or []):
            level, strength = "Cultural connection", 0.36
        else:
            level, strength = "Neutral", 0.0
        return {"level": level, "strength": strength, "market_popularity": market_popularity}

    def update_regional_popularity(self, fighter, region, delta, note=""):
        if not fighter or region not in REGIONS:
            return
        markets = getattr(fighter, "regional_popularity", None) or {market: 0 for market in REGIONS}
        markets.setdefault(region, 0)
        markets[region] = max(0, min(100, markets[region] + delta))
        fighter.regional_popularity = markets
        if note:
            fighter.home_event_history = ([{"month": self.month, "region": region, "note": note, "market_popularity": markets[region]}] + (getattr(fighter, "home_event_history", None) or []))[:18]

    def real_fighter_profiles(self):
        """Named real-fighter calibration. Ratings are current competitive ability, not fame."""
        return {
            "Islam Makhachev": {"rating": 94, "style": "Sambo", "trait": "Title Mentality", "behaviour": "Control", "skills": {"chain_wrestling": 8, "top_control": 8, "submission_attack": 7, "conditioning": 5}},
            "Alexander Volkanovski": {"rating": 93, "style": "Well-Rounded", "trait": "Cardio Machine", "behaviour": "Pressure", "skills": {"footwork": 7, "conditioning": 9, "adaptability": 7, "takedown_defence_detail": 6}},
            "Ilia Topuria": {"rating": 93, "style": "Boxer", "trait": "Knockout Artist", "behaviour": "Pressure", "skills": {"punch_power": 10, "punch_technique": 9, "ground_striking": 5, "confidence": 7}},
            "Justin Gaethje": {"rating": 91, "style": "Kickboxer", "trait": "Big Finisher", "behaviour": "Pressure", "skills": {"low_kick_power": 9, "punch_power": 9, "killer_instinct": 8}},
            "Tom Aspinall": {"rating": 92, "style": "Well-Rounded", "trait": "Big Finisher", "behaviour": "Dynamic Attacker", "skills": {"hand_speed": 8, "submission_attack": 6, "takedowns": 5, "conditioning": 5}},
            "Alex Pereira": {"rating": 91, "style": "Kickboxer", "trait": "Knockout Artist", "behaviour": "Counter", "skills": {"punch_power": 10, "high_kick_power": 10, "kick_defence": 6, "reach": 7}},
            "Khamzat Chimaev": {"rating": 91, "style": "Wrestler", "trait": "Big Finisher", "behaviour": "Pressure", "skills": {"takedowns": 10, "chain_wrestling": 10, "top_control": 9, "ground_striking": 7}},
            "Shavkat Rakhmonov": {"rating": 90, "style": "Sambo", "trait": "Submission Ace", "behaviour": "Dynamic Attacker", "skills": {"submission_attack": 10, "clinch_control": 6, "knees": 7, "composure": 7}},
            "Arman Tsarukyan": {"rating": 90, "style": "Wrestler", "trait": "Gym Rat", "behaviour": "Dynamic Attacker", "skills": {"takedowns": 9, "scrambles": 8, "transitions": 7, "conditioning": 6}},
            "Charles Oliveira": {"rating": 89, "style": "BJJ", "trait": "Submission Ace", "behaviour": "Dynamic Attacker", "skills": {"submission_attack": 10, "back_control": 10, "knees": 6, "creative_punches": 5}},
            "Max Holloway": {"rating": 89, "style": "Boxer", "trait": "Cardio Machine", "behaviour": "Volume", "skills": {"hand_speed": 8, "punch_technique": 8, "conditioning": 10, "chin_strength": 7}},
            "Conor McGregor": {"rating": 92, "style": "Boxer", "trait": "Showman", "behaviour": "Counter", "skills": {"punch_power": 10, "punch_technique": 10, "hand_speed": 9, "footwork": 8, "confidence": 10, "high_kick_power": 6}},
            "Khabib Nurmagomedov": {"rating": 93, "style": "Sambo", "trait": "Title Mentality", "behaviour": "Control", "skills": {"chain_wrestling": 10, "top_control": 10, "ground_striking": 8, "conditioning": 7}},
            "Georges St-Pierre": {"rating": 92, "style": "Wrestler", "trait": "Title Mentality", "behaviour": "Control", "skills": {"takedown_setup": 9, "feints": 7, "adaptability": 9, "discipline": 7}},
            "Jon Jones": {"rating": 94, "style": "Well-Rounded", "trait": "Title Mentality", "behaviour": "Dynamic Attacker", "skills": {"reach": 9, "elbows": 9, "clinch_control": 8, "adaptability": 7}},
            "Dricus Du Plessis": {"rating": 89, "style": "Well-Rounded", "trait": "Pressure Fighter", "behaviour": "Pressure", "skills": {"strength": 7, "takedowns": 6, "resilience": 8, "killer_instinct": 7}},
            "Sean Strickland": {"rating": 88, "style": "Boxer", "trait": "Pressure Fighter", "behaviour": "Pressure", "skills": {"punch_technique": 7, "conditioning": 7, "guard_defence": 6}},
            "Robert Whittaker": {"rating": 87, "style": "Karate", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"footwork": 8, "head_movement": 7, "takedown_defence_detail": 6}},
            "Israel Adesanya": {"rating": 88, "style": "Kickboxer", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"footwork": 9, "high_kick_technique": 8, "head_movement": 8, "reach": 7}},
            "Yair Rodriguez": {"rating": 85, "style": "Karate", "trait": "Showman", "behaviour": "Dynamic Attacker", "skills": {"creative_kicks": 10, "high_kick_technique": 9, "footwork": 7}},
            "Paddy Pimblett": {"rating": 84, "style": "BJJ", "trait": "Fan Favourite", "behaviour": "Dynamic Attacker", "skills": {"submission_attack": 7, "back_control": 6, "scrambles": 6}},
            "Belal Muhammad": {"rating": 86, "style": "Wrestler", "trait": "Gym Rat", "behaviour": "Control", "skills": {"chain_wrestling": 7, "conditioning": 8, "cage_wrestling": 6}},
            "Leon Edwards": {"rating": 87, "style": "Kickboxer", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"head_movement": 7, "high_kick_technique": 7, "elbows": 6}},
            "Kamaru Usman": {"rating": 86, "style": "Wrestler", "trait": "Pressure Fighter", "behaviour": "Pressure", "skills": {"takedowns": 8, "cage_wrestling": 8, "strength": 7}},
            "Magomed Ankalaev": {"rating": 89, "style": "Sambo", "trait": "Gym Rat", "behaviour": "Control", "skills": {"takedown_defence_detail": 7, "punch_power": 6, "conditioning": 6}},
            "Ciryl Gane": {"rating": 88, "style": "Kickboxer", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"footwork": 8, "high_kick_technique": 7, "head_movement": 6}},
            "Petr Yan": {"rating": 90, "style": "Boxer", "trait": "Pressure Fighter", "behaviour": "Pressure", "skills": {"punch_technique": 9, "guard_defence": 8, "takedown_defence_detail": 7, "composure": 7}},
            "Merab Dvalishvili": {"rating": 90, "style": "Wrestler", "trait": "Cardio Machine", "behaviour": "Control", "skills": {"chain_wrestling": 10, "conditioning": 10, "cage_wrestling": 8, "get_ups": 7}},
            "Sean O'Malley": {"rating": 88, "style": "Kickboxer", "trait": "Showman", "behaviour": "Counter", "skills": {"reach": 8, "punch_technique": 7, "creative_kicks": 8, "head_movement": 6}},
            "Umar Nurmagomedov": {"rating": 89, "style": "Sambo", "trait": "Gym Rat", "behaviour": "Dynamic Attacker", "skills": {"takedown_setup": 8, "high_kick_technique": 5, "scrambles": 7, "adaptability": 6}},
            "Movsar Evloev": {"rating": 88, "style": "Wrestler", "trait": "Gym Rat", "behaviour": "Control", "skills": {"takedowns": 9, "ride_control": 8, "conditioning": 7}},
            "Diego Lopes": {"rating": 87, "style": "BJJ", "trait": "Big Finisher", "behaviour": "Dynamic Attacker", "skills": {"submission_attack": 8, "creative_punches": 6, "ground_striking": 6}},
            "Joshua Van": {"rating": 88, "style": "Boxer", "trait": "Cardio Machine", "behaviour": "Volume", "skills": {"hand_speed": 8, "punch_technique": 7, "conditioning": 9}},
            "Alexandre Pantoja": {"rating": 89, "style": "BJJ", "trait": "Clutch", "behaviour": "Dynamic Attacker", "skills": {"submission_attack": 9, "scrambles": 7, "back_control": 8}},
            "Brandon Royval": {"rating": 85, "style": "BJJ", "trait": "Big Finisher", "behaviour": "Dynamic Attacker", "skills": {"scrambles": 8, "submission_attack": 8, "creative_punches": 5}},
            "Manel Kape": {"rating": 86, "style": "Kickboxer", "trait": "Knockout Artist", "behaviour": "Counter", "skills": {"punch_power": 8, "hand_speed": 7, "head_movement": 7}},
            "Song Yadong": {"rating": 86, "style": "Kickboxer", "trait": "Big Finisher", "behaviour": "Pressure", "skills": {"punch_power": 8, "hand_speed": 7, "low_kick_power": 6}},
            "Cory Sandhagen": {"rating": 87, "style": "Kickboxer", "trait": "Showman", "behaviour": "Dynamic Attacker", "skills": {"footwork": 8, "creative_kicks": 9, "creative_punches": 7}},
            "Kayla Harrison": {"rating": 90, "style": "Judo", "trait": "Title Mentality", "behaviour": "Control", "skills": {"throws": 10, "clinch_takedowns": 9, "top_control": 8, "strength": 8}},
            "Valentina Shevchenko": {"rating": 90, "style": "Muay Thai", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"head_movement": 8, "high_kick_technique": 7, "takedown_defence_detail": 7, "composure": 8}},
            "Zhang Weili": {"rating": 90, "style": "Kickboxer", "trait": "Pressure Fighter", "behaviour": "Pressure", "skills": {"strength": 7, "punch_power": 7, "takedowns": 5, "conditioning": 7}},
            "Mackenzie Dern": {"rating": 85, "style": "BJJ", "trait": "Submission Ace", "behaviour": "Submission Hunter", "skills": {"submission_attack": 10, "guard_work": 9, "leg_locks": 7}},
            "Dakota Ditcheva": {"rating": 86, "style": "Muay Thai", "trait": "Knockout Artist", "behaviour": "Dynamic Attacker", "skills": {"knees": 9, "punch_power": 7, "high_kick_power": 7}},
            "Usman Nurmagomedov": {"rating": 91, "style": "Sambo", "trait": "Title Mentality", "behaviour": "Control", "skills": {"takedowns": 8, "submission_attack": 7, "kick_defence": 6, "adaptability": 7}},
            "AJ McKee": {"rating": 87, "style": "Well-Rounded", "trait": "Big Finisher", "behaviour": "Dynamic Attacker", "skills": {"head_movement": 6, "submission_attack": 6, "creative_kicks": 6}},
            "Vadim Nemkov": {"rating": 88, "style": "Sambo", "trait": "Gym Rat", "behaviour": "Control", "skills": {"takedowns": 7, "punch_power": 6, "conditioning": 6}},
            "Corey Anderson": {"rating": 86, "style": "Wrestler", "trait": "Cardio Machine", "behaviour": "Control", "skills": {"chain_wrestling": 8, "conditioning": 7, "ground_striking": 6}},
            "Johnny Eblen": {"rating": 86, "style": "Wrestler", "trait": "Gym Rat", "behaviour": "Pressure", "skills": {"takedowns": 8, "top_control": 7, "conditioning": 6}},
            "Sergio Pettis": {"rating": 85, "style": "Kickboxer", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"footwork": 7, "head_movement": 7, "kick_defence": 6}},
            "Cris Cyborg": {"rating": 86, "style": "Muay Thai", "trait": "Big Finisher", "behaviour": "Pressure", "skills": {"punch_power": 9, "knees": 7, "killer_instinct": 8}},
            "Mamed Khalidov": {"rating": 82, "style": "Well-Rounded", "trait": "Clutch", "behaviour": "Dynamic Attacker", "skills": {"creative_kicks": 6, "submission_attack": 5}},
            "Salahdine Parnasse": {"rating": 84, "style": "Well-Rounded", "trait": "Prospect Mindset", "behaviour": "Dynamic Attacker", "skills": {"footwork": 6, "adaptability": 6}},
            "Nicolas Leblond": {"rating": 78, "style": "Well-Rounded", "trait": "Clutch", "behaviour": "Dynamic Attacker"},
            "Weslley Maia": {"rating": 77, "style": "BJJ", "trait": "Submission Ace", "behaviour": "Submission Hunter"},
            "Nikita Bagley": {"rating": 78, "style": "Boxer", "trait": "Prospect Mindset", "behaviour": "Pressure"},
            "Ieuan Davies": {"rating": 77, "style": "Well-Rounded", "trait": "Prospect Mindset", "behaviour": "Dynamic Attacker"},
            "Sean Clancy Jr.": {"rating": 78, "style": "Wrestler", "trait": "Gym Rat", "behaviour": "Control"},
            "Anderson Silva": {"rating": 91, "style": "Muay Thai", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"head_movement": 10, "punch_technique": 8, "creative_kicks": 8, "clinch_control": 6, "composure": 9}},
            "Demetrious Johnson": {"rating": 93, "style": "Well-Rounded", "trait": "Adaptable", "behaviour": "Dynamic Attacker", "skills": {"adaptability": 10, "scrambles": 9, "takedown_setup": 8, "back_control": 8, "conditioning": 9}},
            "Jose Aldo": {"rating": 90, "style": "Muay Thai", "trait": "Leg Kicker", "behaviour": "Counter", "skills": {"low_kick_power": 10, "low_kick_technique": 10, "takedown_defence_detail": 9, "punch_power": 7}},
            "Daniel Cormier": {"rating": 90, "style": "Wrestler", "trait": "Title Mentality", "behaviour": "Pressure", "skills": {"chain_wrestling": 9, "clinch_control": 9, "dirty_boxing": 8, "conditioning": 8}},
            "Fedor Emelianenko": {"rating": 92, "style": "Sambo", "trait": "Fight Finisher", "behaviour": "Dynamic Attacker", "skills": {"punch_power": 9, "throws": 9, "ground_striking": 9, "submission_attack": 8, "composure": 9}},
            "Ronda Rousey": {"rating": 87, "style": "Judo", "trait": "Submission Ace", "behaviour": "Submission Hunter", "skills": {"throws": 10, "clinch_takedowns": 10, "submission_attack": 10, "killer_instinct": 9}},
            "Amanda Nunes": {"rating": 92, "style": "Well-Rounded", "trait": "Knockout Artist", "behaviour": "Pressure", "skills": {"punch_power": 10, "punch_technique": 8, "takedown_defence_detail": 8, "ground_striking": 8, "killer_instinct": 9}},
            "Nate Diaz": {"rating": 83, "style": "BJJ", "trait": "Cardio Machine", "behaviour": "Volume", "skills": {"punch_technique": 7, "hand_speed": 6, "conditioning": 10, "chin_strength": 9, "submission_attack": 8}},
            "BJ Penn": {"rating": 88, "style": "BJJ", "trait": "Veteran Savvy", "behaviour": "Dynamic Attacker", "skills": {"takedown_defence_detail": 9, "guard_work": 9, "back_control": 9, "punch_technique": 7}},
            "Frankie Edgar": {"rating": 88, "style": "Wrestler", "trait": "Comeback Artist", "behaviour": "Volume", "skills": {"takedown_setup": 8, "footwork": 8, "conditioning": 9, "stun_recovery": 8}},
            "Urijah Faber": {"rating": 86, "style": "Wrestler", "trait": "Fight Finisher", "behaviour": "Pressure", "skills": {"scrambles": 9, "back_control": 8, "submission_attack": 8, "conditioning": 8}},
            "Lyoto Machida": {"rating": 89, "style": "Karate", "trait": "Counter Specialist", "behaviour": "Counter", "skills": {"footwork": 10, "high_kick_speed": 9, "head_movement": 8, "composure": 9}},
            "Mauricio Rua": {"rating": 88, "style": "Muay Thai", "trait": "Big Finisher", "behaviour": "Pressure", "skills": {"low_kick_power": 9, "punch_power": 9, "ground_striking": 8, "killer_instinct": 8}},
            "Quinton Jackson": {"rating": 87, "style": "Boxer", "trait": "Knockout Artist", "behaviour": "Pressure", "skills": {"punch_power": 10, "strength": 9, "takedown_defence_detail": 7, "chin_strength": 8}},
            "Mirko Cro Cop": {"rating": 89, "style": "Kickboxer", "trait": "Knockout Artist", "behaviour": "Counter", "skills": {"high_kick_power": 10, "high_kick_speed": 9, "takedown_defence_detail": 8, "punch_power": 8}},
            "Wanderlei Silva": {"rating": 87, "style": "Muay Thai", "trait": "Warrior Spirit", "behaviour": "Pressure", "skills": {"punch_power": 9, "knees": 9, "thai_plum": 8, "killer_instinct": 9}},
            "Matt Hughes": {"rating": 88, "style": "Wrestler", "trait": "Title Mentality", "behaviour": "Control", "skills": {"takedowns": 9, "ride_control": 9, "top_control": 9, "strength": 9}},
            "Robbie Lawler": {"rating": 87, "style": "Boxer", "trait": "Warrior Spirit", "behaviour": "Pressure", "skills": {"punch_power": 9, "takedown_defence_detail": 8, "chin_strength": 9, "killer_instinct": 8}},
            "Demian Maia": {"rating": 88, "style": "BJJ", "trait": "Submission Ace", "behaviour": "Submission Hunter", "skills": {"submission_attack": 10, "back_control": 10, "transitions": 9, "takedown_setup": 7}},
            "Joanna Jedrzejczyk": {"rating": 89, "style": "Muay Thai", "trait": "Cardio Machine", "behaviour": "Volume", "skills": {"punch_technique": 9, "low_kick_technique": 8, "conditioning": 10, "takedown_defence_detail": 8}},
            "Jiri Prochazka": {"rating": 88, "style": "Kickboxer", "trait": "Warrior Spirit", "behaviour": "Dynamic Attacker", "skills": {"creative_punches": 10, "creative_kicks": 8, "punch_power": 9, "killer_instinct": 9}},
            "Jack Della Maddalena": {"rating": 90, "style": "Boxer", "trait": "Body Hunter", "behaviour": "Pressure", "skills": {"punch_technique": 9, "punch_power": 8, "footwork": 8, "creative_punches": 7}},
            "Carlos Prates": {"rating": 88, "style": "Muay Thai", "trait": "Knockout Artist", "behaviour": "Counter", "skills": {"punch_power": 10, "knees": 8, "reach": 8, "composure": 7}},
            "Michael Morales": {"rating": 88, "style": "Boxer", "trait": "Prospect Mindset", "behaviour": "Dynamic Attacker", "skills": {"punch_power": 8, "hand_speed": 8, "takedown_defence_detail": 7, "confidence": 7}},
            "Sean Brady": {"rating": 87, "style": "Grappler", "trait": "Gym Rat", "behaviour": "Control", "skills": {"takedowns": 8, "top_control": 9, "submission_attack": 8, "strength": 8}},
            "Nassourdine Imavov": {"rating": 89, "style": "Kickboxer", "trait": "Technical Learner", "behaviour": "Counter", "skills": {"footwork": 8, "punch_technique": 8, "kick_defence": 7, "composure": 7}},
            "Caio Borralho": {"rating": 87, "style": "Well-Rounded", "trait": "Technical Learner", "behaviour": "Control", "skills": {"takedowns": 7, "top_control": 7, "punch_technique": 6, "adaptability": 7}},
            "Carlos Ulberg": {"rating": 87, "style": "Kickboxer", "trait": "Knockout Artist", "behaviour": "Counter", "skills": {"punch_power": 9, "footwork": 8, "high_kick_technique": 7, "head_movement": 7}},
            "Alexander Volkov": {"rating": 87, "style": "Kickboxer", "trait": "Veteran Savvy", "behaviour": "Volume", "skills": {"reach": 9, "punch_technique": 8, "knees": 7, "conditioning": 7}},
            "Sergei Pavlovich": {"rating": 86, "style": "Boxer", "trait": "Knockout Artist", "behaviour": "Pressure", "skills": {"punch_power": 10, "hand_speed": 8, "killer_instinct": 9, "strength": 8}},
            "Lerone Murphy": {"rating": 87, "style": "Boxer", "trait": "Technical Learner", "behaviour": "Counter", "skills": {"punch_technique": 8, "footwork": 8, "head_movement": 7, "takedown_defence_detail": 7}},
            "Tatsuro Taira": {"rating": 86, "style": "BJJ", "trait": "Prospect Mindset", "behaviour": "Submission Hunter", "skills": {"back_control": 9, "submission_attack": 8, "takedown_setup": 7, "scrambles": 7}},
            "Gillian Robertson": {"rating": 84, "style": "BJJ", "trait": "Submission Ace", "behaviour": "Submission Hunter", "skills": {"submission_attack": 9, "back_control": 8, "top_control": 7, "transitions": 8}},
        }

    def signature_real_fighter_detailed_profiles(self):
        """Complete engine-facing profiles for fighters a generic style cannot represent."""
        grouped = {
            "Conor McGregor": {
                "Standing": [95, 96, 93, 99, 98, 97, 90, 92, 94, 85, 87, 89, 96, 94, 88, 87],
                "Ground": [88, 92, 90, 87, 89, 85, 94, 85, 89, 82, 80, 72],
                "Wrestling": [83, 87, 89, 95, 94, 81, 79, 83, 89, 82, 95],
                "Muay Thai Clinch": [88, 93, 89, 87, 83, 85, 81, 92],
                "Mental": [92, 98, 93, 99, 96, 94, 97, 99],
                "Physical": [94, 88, 94, 92, 99, 96, 99, 93, 93, 94, 90, 89],
            },
            "Ilia Topuria": {
                "Standing": [93, 94, 93, 99, 98, 97, 92, 90, 91, 93, 92, 92, 95, 90, 93, 92],
                "Ground": [91, 94, 94, 94, 96, 95, 94, 93, 90, 96, 92, 88],
                "Wrestling": [92, 91, 92, 94, 94, 88, 87, 91, 91, 90, 95],
                "Muay Thai Clinch": [91, 93, 92, 90, 86, 92, 91, 93],
                "Mental": [95, 96, 93, 99, 95, 94, 96, 98],
                "Physical": [89, 91, 94, 94, 95, 93, 97, 95, 95, 95, 91, 89],
            },
            "Khabib Nurmagomedov": {
                "Standing": [84, 82, 84, 88, 86, 84, 78, 76, 78, 82, 82, 80, 80, 76, 87, 86],
                "Ground": [96, 96, 98, 99, 98, 96, 98, 99, 95, 96, 99, 91],
                "Wrestling": [99, 98, 95, 95, 96, 95, 97, 99, 99, 99, 96],
                "Muay Thai Clinch": [99, 93, 90, 88, 82, 99, 99, 96],
                "Mental": [96, 99, 98, 96, 96, 99, 99, 99],
                "Physical": [84, 95, 99, 97, 91, 90, 93, 96, 99, 98, 96, 92],
            },
        }
        profiles = {}
        for name, groups in grouped.items():
            profiles[name] = {
                key: value
                for group_name, values in groups.items()
                for key, value in zip(DETAILED_SKILL_GROUPS[group_name], values)
            }
        return profiles

    def apply_signature_real_fighter_profile(self, fighter, preserve_career=False):
        targets = self.signature_real_fighter_detailed_profiles().get(fighter.name)
        if not targets:
            return False
        before_overall = fighter.overall
        fighter.detailed_skills.update(targets)
        self.sync_broad_skills_from_details(fighter)
        if preserve_career:
            delta = max(-5, min(5, before_overall - fighter.overall))
            if delta:
                for key in targets:
                    if key not in {"reach", "natural_size"}:
                        fighter.detailed_skills[key] = max(25, min(99, fighter.detailed_skills[key] + delta))
                self.sync_broad_skills_from_details(fighter)
        fighter.realism_profile_version = 1
        return True

    def real_fighter_stances(self):
        return {
            "Islam Makhachev": "Southpaw", "Conor McGregor": "Southpaw", "Leon Edwards": "Southpaw",
            "Magomed Ankalaev": "Southpaw", "Paddy Pimblett": "Southpaw", "Anderson Silva": "Southpaw",
            "Nate Diaz": "Southpaw", "Lyoto Machida": "Southpaw", "Mirko Cro Cop": "Southpaw",
            "Robbie Lawler": "Southpaw", "Demian Maia": "Southpaw", "Darren Till": "Southpaw",
            "Anthony Pettis": "Orthodox", "Max Holloway": "Orthodox", "Ilia Topuria": "Orthodox",
            "Alex Pereira": "Orthodox", "Israel Adesanya": "Switch", "Jon Jones": "Orthodox",
            "Sean O'Malley": "Switch", "Petr Yan": "Switch", "Shavkat Rakhmonov": "Orthodox",
            "Khabib Nurmagomedov": "Orthodox", "Georges St-Pierre": "Orthodox", "Fedor Emelianenko": "Orthodox",
            "Amanda Nunes": "Orthodox", "Jose Aldo": "Orthodox", "Demetrious Johnson": "Orthodox",
            "Daniel Cormier": "Orthodox", "Ronda Rousey": "Orthodox", "Joanna Jedrzejczyk": "Orthodox",
            "Oleksandr Usyk": "Southpaw", "Manny Pacquiao": "Southpaw", "Terence Crawford": "Switch",
        }

    def real_fighter_draws(self):
        return {
            "Demetrious Johnson": 1, "Fedor Emelianenko": 1, "Frankie Edgar": 1,
            "Brandon Moreno": 2, "Jan Blachowicz": 1, "Wanderlei Silva": 1,
            "Deiveson Figueiredo": 1, "Paul Craig": 1, "Niko Price": 2,
            "Rodrigo Nascimento": 1, "Ion Cutelaba": 1, "Marcin Held": 0,
        }

    def apply_real_fighter_profile(self, fighter, base_skill):
        profile = self.real_fighter_profiles().get(fighter.name, {})
        rating = int(profile.get("rating", base_skill))
        fighter.style = profile.get("style", fighter.style if fighter.style in STYLES else "Well-Rounded")
        trait_by_style = {
            "Boxer": "Counter Specialist", "Kickboxer": "Big Finisher", "Karate": "Counter Specialist",
            "Muay Thai": "Pressure Fighter", "Wrestler": "Gym Rat", "BJJ": "Submission Ace",
            "Sambo": "Gym Rat", "Judo": "Clutch", "Grappler": "Submission Ace", "Well-Rounded": "Gym Rat",
        }
        behaviour_by_style = {
            "Boxer": "Counter", "Kickboxer": "Dynamic Attacker", "Karate": "Counter", "Muay Thai": "Pressure",
            "Wrestler": "Control", "BJJ": "Submission Hunter", "Sambo": "Dynamic Attacker", "Judo": "Control",
            "Grappler": "Submission Hunter", "Well-Rounded": "Dynamic Attacker",
        }
        fighter.trait = profile.get("trait", trait_by_style.get(fighter.style, "Gym Rat"))
        fighter.behaviour = profile.get("behaviour", behaviour_by_style.get(fighter.style, "Dynamic Attacker"))
        default_stance = self.real_fighter_stances().get(fighter.name)
        if not default_stance:
            stance_roll = sum((index + 1) * ord(char) for index, char in enumerate(fighter.name)) % 100
            default_stance = "Orthodox" if stance_roll < 64 else "Southpaw" if stance_roll < 91 else "Switch"
        fighter.stance = profile.get("stance", default_stance)
        group_bias = {
            "Boxer": (8, -6, -7, 2, 2, 1), "Kickboxer": (8, -5, -6, 3, 1, 1),
            "Karate": (7, -6, -7, 2, 1, 2), "Muay Thai": (8, -3, -4, 5, 1, 1),
            "Wrestler": (-7, 9, 4, 2, 3, 2), "BJJ": (-8, -1, 10, -1, 2, 2),
            "Sambo": (-1, 7, 8, 2, 3, 3), "Judo": (-5, 8, 5, 4, 2, 2),
            "Grappler": (-7, 3, 9, 0, 2, 2), "Well-Rounded": (2, 2, 2, 2, 2, 2),
        }
        standing, wrestling, ground, clinch, mental, physical = group_bias.get(fighter.style, group_bias["Well-Rounded"])
        group_values = {
            "Standing": rating + standing, "Wrestling": rating + wrestling, "Ground": rating + ground,
            "Muay Thai Clinch": rating + clinch, "Mental": rating + mental, "Physical": rating + physical,
        }
        seed = sum((index + 1) * ord(char) for index, char in enumerate(fighter.name))
        details = {}
        for group, keys in DETAILED_SKILL_GROUPS.items():
            for index, key in enumerate(keys):
                variation = ((seed + index * 17 + len(group) * 7) % 7) - 3
                details[key] = max(28, min(99, group_values[group] + variation))
        style_focus = {
            "Boxer": ("punch_power", "punch_technique", "hand_speed", "head_movement"),
            "Kickboxer": ("high_kick_power", "high_kick_technique", "low_kick_technique", "kick_defence"),
            "Karate": ("footwork", "high_kick_speed", "creative_kicks", "head_movement"),
            "Muay Thai": ("knees", "elbows", "thai_plum", "low_kick_power"),
            "Wrestler": ("takedowns", "takedown_setup", "chain_wrestling", "sprawl"),
            "BJJ": ("submission_attack", "submission_defence_detail", "guard_work", "back_control"),
            "Sambo": ("takedowns", "throws", "submission_attack", "leg_locks"),
            "Judo": ("throws", "clinch_takedowns", "top_control", "positional_ability"),
            "Grappler": ("top_control", "submission_attack", "transitions", "scrambles"),
        }
        for key in style_focus.get(fighter.style, ("adaptability", "conditioning")):
            if key in details:
                details[key] = min(99, details[key] + 5)
        for key, boost in profile.get("skills", {}).items():
            if key in details:
                details[key] = max(28, min(99, details[key] + boost))
        fighter.detailed_skills = details
        self.sync_broad_skills_from_details(fighter)
        # Overall includes the detailed mental and physical groups. Keep a named
        # fighter's final OVR anchored to their curated rating rather than letting
        # a specialist template quietly inflate it by several points.
        for _ in range(2):
            adjustment = rating - fighter.overall
            if not adjustment:
                break
            fighter.detailed_skills = {
                key: max(28, min(99, value + adjustment))
                for key, value in fighter.detailed_skills.items()
            }
            self.sync_broad_skills_from_details(fighter)
        signature_profile = self.apply_signature_real_fighter_profile(fighter, preserve_career=False)
        # Broad rating calibration can push an elite specialist's whole tab to
        # the same ceiling. Retain the authored OVR while restoring technique
        # differences that make styles and individual matchups meaningful.
        if not signature_profile:
            self.rebalance_saturated_detailed_skills(fighter, max_overall_drop=1)
        fighter.finishing_instinct = max(fighter.finishing_instinct, min(99, rating + (8 if fighter.trait in ("Knockout Artist", "Big Finisher", "Submission Ace") else 2)))
        fighter.fight_iq = max(fighter.fight_iq, min(99, rating + mental - 2))
        business_seed = sum((index + 7) * ord(char) for index, char in enumerate(fighter.name))
        fighter.star_quality = max(1, min(99, round(fighter.popularity * 0.62 + rating * 0.28 + business_seed % 11)))
        fighter.charisma = max(1, min(99, round(fighter.popularity * 0.60 + 22 + business_seed % 19)))
        pro_bonus = 8 if fighter.trait in ("Title Mentality", "Technical Learner", "Quiet Professional", "Gym Rat") else 0
        fighter.professionalism = max(35, min(99, 66 + business_seed % 22 + pro_bonus))
        fighter.injury_proneness = max(4, min(70, 10 + business_seed % 22 + max(0, fighter.age - 34)))
        fighter.media_presence = max(1, min(99, round(fighter.popularity * 0.62 + fighter.charisma * 0.28)))
        fighter.sponsor_appeal = max(1, min(99, round(fighter.star_quality * 0.42 + fighter.charisma * 0.24 + fighter.professionalism * 0.20 + fighter.popularity * 0.14)))
        fighter.motivation = max(35, min(99, 72 + business_seed % 18 - max(0, fighter.age - 36)))
        fighter.record_d = self.real_fighter_draws().get(fighter.name, fighter.record_d)
        fighter.multi_sport_records = dict(fighter.multi_sport_records or {})
        fighter.multi_sport_records["MMA"] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
        fighter.rating_profile_version = 4

    def cage_empire_fighter_data(self):
        return [
            ("Tony Ferguson", "Welterweight", "Independent", 76, 78, 42, 25, 11, "USA", "Well-Rounded"),
            ("Jorge Masvidal", "Welterweight", "Independent", 84, 79, 41, 35, 17, "USA", "Boxer"),
            ("Darren Till", "Middleweight", "Independent", 72, 77, 33, 18, 5, "UK", "Muay Thai"),
            ("Mike Perry", "Welterweight", "Independent", 78, 76, 35, 14, 8, "USA", "Boxer"),
            ("Kevin Lee", "Welterweight", "Independent", 62, 76, 34, 19, 8, "USA", "Wrestler"),
            ("Ben Askren", "Welterweight", "Independent", 70, 77, 42, 19, 2, "USA", "Wrestler"),
            ("Tyron Woodley", "Welterweight", "Independent", 76, 78, 44, 19, 7, "USA", "Wrestler"),
            ("Yoel Romero", "Middleweight", "Independent", 78, 80, 49, 16, 7, "USA", "Wrestler"),
            ("Luke Rockhold", "Middleweight", "Independent", 72, 78, 41, 16, 6, "USA", "Kickboxer"),
            ("Anthony Pettis", "Lightweight", "Independent", 73, 77, 39, 25, 14, "USA", "Kickboxer"),
            ("Benson Henderson", "Lightweight", "Independent", 66, 76, 42, 30, 12, "USA", "Well-Rounded"),
            ("Eddie Alvarez", "Lightweight", "Independent", 76, 78, 42, 30, 8, "USA", "Boxer"),
            ("Jeremy Stephens", "Featherweight", "Independent", 68, 75, 40, 29, 21, "USA", "Boxer"),
            ("John Dodson", "Bantamweight", "Independent", 58, 74, 41, 24, 14, "USA", "Boxer"),
            ("Ray Borg", "Bantamweight", "Independent", 44, 72, 33, 16, 5, "USA", "Wrestler"),
            ("Wilson Reis", "Flyweight", "Independent", 38, 71, 41, 25, 12, "Brazil", "BJJ"),
            ("Mikey Musumeci", "Flyweight", "Nova Uniao", 60, 74, 28, 6, 0, "USA", "BJJ"),
            ("Hector Lombard", "Middleweight", "Independent", 55, 73, 48, 34, 10, "Australia", "Judo"),
            ("Rousimar Palhares", "Welterweight", "Independent", 52, 73, 46, 19, 11, "Brazil", "BJJ"),
            ("Paige VanZant", "Flyweight", "Independent", 66, 70, 32, 8, 5, "USA", "Kickboxer"),
            ("Miesha Tate", "Bantamweight", "Independent", 73, 77, 39, 20, 9, "USA", "Wrestler"),
            ("Cat Zingano", "Featherweight", "Independent", 52, 74, 44, 14, 5, "USA", "Wrestler"),
            ("Julia Avila", "Bantamweight", "Independent", 36, 70, 38, 9, 3, "USA", "Well-Rounded"),
            ("Pearl Gonzalez", "Flyweight", "Independent", 40, 70, 39, 10, 5, "USA", "BJJ"),
            ("Vanessa Demopoulos", "Flyweight", "Independent", 42, 70, 37, 11, 6, "USA", "BJJ"),
            ("Roberto Soldic", "Welterweight", "Independent", 68, 82, 31, 20, 4, "Europe", "Kickboxer"),
            ("Anatoly Malykhin", "Heavyweight", "Independent", 70, 85, 38, 14, 0, "Europe", "Wrestler"),
            ("Christian Lee", "Lightweight", "Independent", 64, 82, 28, 17, 4, "Asia", "Well-Rounded"),
            ("Thanh Le", "Featherweight", "Independent", 58, 78, 40, 14, 4, "USA", "Kickboxer"),
            ("Aung La Nsang", "Middleweight", "Independent", 58, 76, 41, 30, 15, "Asia", "Kickboxer"),
            ("Adriano Moraes", "Flyweight", "Independent", 54, 78, 37, 20, 5, "Brazil", "BJJ"),
            ("Kyoji Horiguchi", "Bantamweight", "Independent", 66, 82, 36, 33, 5, "Japan", "Karate"),
            ("Kai Asakura", "Bantamweight", "Independent", 62, 79, 32, 21, 5, "Japan", "Kickboxer"),
            ("Mikuru Asakura", "Featherweight", "Independent", 58, 76, 33, 17, 5, "Japan", "Kickboxer"),
            ("Kleber Koike Erbst", "Featherweight", "Independent", 48, 76, 36, 31, 7, "Japan", "BJJ"),
            ("Patricio Pitbull", "Featherweight", "Independent", 72, 82, 39, 36, 8, "Brazil", "Well-Rounded"),
            ("Douglas Lima", "Welterweight", "Independent", 64, 79, 38, 33, 11, "Brazil", "Kickboxer"),
            ("Michael Page", "Welterweight", "Independent", 68, 80, 39, 23, 3, "UK", "Karate"),
            ("Lorenz Larkin", "Middleweight", "Independent", 50, 76, 39, 26, 8, "USA", "Kickboxer"),
            ("Denise Gomes", "Flyweight", "Independent", 36, 72, 26, 10, 3, "Brazil", "Boxer"),
            ("Rin Nakai", "Bantamweight", "Independent", 38, 72, 39, 27, 3, "Japan", "Wrestler"),
            ("Seo Hee Ham", "Flyweight", "Independent", 46, 77, 39, 26, 9, "Japan", "Kickboxer"),
            ("Ayaka Hamasaki", "Flyweight", "Independent", 40, 74, 44, 24, 7, "Japan", "Judo"),
        ]

    def independent_fighter_data(self):
        return [
            ("Matthew Green", "Middleweight", "Free Agent", 78, 90, 24, 14, 1, "UK", "Kickboxer"),
            ("Nick Diaz", "Welterweight", "Free Agent", 84, 76, 42, 26, 10, "USA", "BJJ"),
            ("Frankie Edgar", "Bantamweight", "Free Agent", 74, 76, 44, 24, 11, "USA", "Wrestler"),
            ("Donald Cerrone", "Lightweight", "Free Agent", 80, 75, 43, 36, 17, "USA", "Kickboxer"),
            ("Diego Sanchez", "Welterweight", "Free Agent", 58, 70, 44, 30, 14, "USA", "Wrestler"),
            ("Carlos Condit", "Welterweight", "Free Agent", 66, 74, 42, 32, 14, "USA", "Kickboxer"),
            ("Rory MacDonald", "Welterweight", "Free Agent", 62, 78, 37, 23, 10, "Canada", "Well-Rounded"),
            ("Gegard Mousasi", "Middleweight", "Free Agent", 64, 80, 41, 49, 9, "Europe", "Kickboxer"),
            ("Jacare Souza", "Middleweight", "Free Agent", 58, 76, 46, 26, 10, "Brazil", "BJJ"),
            ("Vitor Belfort", "Middleweight", "Free Agent", 72, 75, 49, 26, 14, "Brazil", "Boxer"),
            ("Chael Sonnen", "Light Heavyweight", "Free Agent", 70, 73, 49, 31, 17, "USA", "Wrestler"),
            ("Ryan Bader", "Light Heavyweight", "Free Agent", 54, 78, 43, 31, 8, "USA", "Wrestler"),
            ("Phil De Fries", "Heavyweight", "Free Agent", 42, 78, 40, 25, 6, "UK", "BJJ"),
            ("Vitaly Minakov", "Heavyweight", "Free Agent", 38, 76, 41, 22, 2, "Europe", "Sambo"),
            ("Josh Barnett", "Heavyweight", "Free Agent", 56, 73, 48, 35, 8, "USA", "Wrestler"),
            ("Alistair Overeem", "Heavyweight", "Free Agent", 78, 77, 46, 47, 19, "Europe", "Kickboxer"),
            ("Junior Dos Santos", "Heavyweight", "Free Agent", 70, 75, 42, 21, 10, "Brazil", "Boxer"),
            ("Fabricio Werdum", "Heavyweight", "Free Agent", 66, 76, 48, 24, 10, "Brazil", "BJJ"),
            ("Germaine de Randamie", "Bantamweight", "Free Agent", 48, 76, 42, 10, 5, "Europe", "Muay Thai"),
            ("Sarah Kaufman", "Bantamweight", "Free Agent", 34, 71, 40, 22, 5, "Canada", "Boxer"),
            ("Felicia Spencer", "Featherweight", "Free Agent", 35, 72, 35, 9, 3, "Canada", "BJJ"),
            ("Jessica-Rose Clark", "Flyweight", "Free Agent", 34, 70, 38, 11, 9, "Australia", "Boxer"),
            ("Bec Rawlings", "Flyweight", "Free Agent", 35, 69, 37, 8, 9, "Australia", "Boxer"),
        ]

    def ufc_current_ranked_fighter_data(self):
        # UFC has no women's strawweight in this ruleset yet, so those names seed into women's flyweight.
        ranked = {
            "Heavyweight": [
                "Tom Aspinall", "Ciryl Gane", "Alexander Volkov", "Sergei Pavlovich", "Josh Hokit",
                "Waldo Cortes Acosta", "Serghei Spivac", "Curtis Blaydes", "Rizvan Kuniev", "Tyrell Fortune",
                "Ante Delija", "Derrick Lewis", "Marcin Tybura", "Brando Pericic", "Valter Walker",
                "Mick Parkin", "Vitor Petrino", "Mario Pinto", "Ryan Spann",
            ],
            "Light Heavyweight": [
                "Carlos Ulberg", "Magomed Ankalaev", "Jiri Prochazka", "Alex Pereira", "Jan Blachowicz",
                "Khalil Rountree Jr.", "Jamahal Hill", "Azamat Murzakanov", "Volkan Oezdemir", "Bogdan Guskov",
                "Dominick Reyes", "Nikita Krylov", "Johnny Walker", "Aleksandar Rakic", "Alonzo Menifield",
                "Dustin Jacoby", "Navajo Stirling",
            ],
            "Middleweight": [
                "Sean Strickland", "Khamzat Chimaev", "Dricus Du Plessis", "Nassourdine Imavov", "Brendan Allen",
                "Caio Borralho", "Anthony Hernandez", "Joe Pyfer", "Reinier de Ridder", "Israel Adesanya",
                "Robert Whittaker", "Jared Cannonier", "Gregory Rodrigues", "Christian Leroy Duncan", "Roman Dolidze",
                "Bo Nickal", "Ikram Aliskerov", "Abus Magomedov",
            ],
            "Welterweight": [
                "Islam Makhachev", "Ian Machado Garry", "Carlos Prates", "Michael Morales", "Jack Della Maddalena",
                "Gabriel Bonfim", "Sean Brady", "Belal Muhammad", "Leon Edwards", "Kamaru Usman",
                "Joaquin Buckley", "Yaroslav Amosov", "Mike Malott", "Michael Venom Page", "Uros Medic",
                "Daniel Rodriguez",
            ],
            "Lightweight": [
                "Justin Gaethje", "Ilia Topuria", "Arman Tsarukyan", "Charles Oliveira", "Max Holloway",
                "Benoit Saint Denis", "Paddy Pimblett", "Mauricio Ruffy", "Mateusz Gamrot", "Dan Hooker",
                "Renato Moicano", "Rafael Fiziev", "Quillan Salkilld", "Tom Nolan", "Beneil Dariush",
                "Manuel Torres", "Grant Dawson", "Rafa Garcia",
            ],
            "Featherweight": [
                "Alexander Volkanovski", "Movsar Evloev", "Diego Lopes", "Lerone Murphy", "Aljamain Sterling",
                "Yair Rodriguez", "Jean Silva", "Arnold Allen", "Youssef Zalal", "Kevin Vallejos",
                "Steve Garcia", "Brian Ortega", "Aaron Pico", "Melquizael Costa", "David Onama",
                "Patricio Pitbull", "Pat Sabatini", "Nathaniel Wood", "Joanderson Brito", "Jose Miguel Delgado",
            ],
            "Bantamweight": [
                "Petr Yan", "Merab Dvalishvili", "Sean O'Malley", "Umar Nurmagomedov", "Cory Sandhagen",
                "Song Yadong", "Aiemann Zahabi", "Mario Bautista", "David Martinez", "Deiveson Figueiredo",
                "Marlon Vera", "Payton Talbott", "Raul Rosas Jr.", "Raoni Barcelos", "Marcus McGhee",
                "Farid Basharat", "Charles Jourdain", "Montel Jackson",
            ],
            "Flyweight": [
                "Joshua Van", "Alexandre Pantoja", "Manel Kape", "Tatsuro Taira", "Brandon Royval",
                "Kyoji Horiguchi", "Lone'er Kavanagh", "Asu Almabayev", "Amir Albazi", "Brandon Moreno",
                "Steve Erceg", "Alex Perez", "Tim Elliott", "Tagir Ulanbekov", "Charles Johnson",
                "Edgar Chairez", "Kevin Borjas", "Mitch Raposo", "Sumudaerji", "Joseph Morales",
            ],
            "Women's Flyweight": [
                "Mackenzie Dern", "Zhang Weili", "Tatiana Suarez", "Virna Jandiroba", "Yan Xiaonan",
                "Gillian Robertson", "Loopy Godinez", "Amanda Lemos", "Tabatha Ricci", "Jessica Andrade",
                "Amanda Ribas", "Fatima Kline", "Angela Hill", "Denise Gomes", "Alexia Thainara",
                "Mizuki", "Piera Rodriguez", "Jaqueline Amorim", "Talita Alencar", "Valentina Shevchenko",
                "Natalia Silva", "Manon Fiorot", "Alexa Grasso", "Erin Blanchfield", "Rose Namajunas",
                "Maycee Barber", "Jasmine Jasudavicius", "Tracy Cortez", "Miranda Maverick", "Karine Silva",
                "Casey O'Neill", "Wang Cong", "Eduarda Moura", "JJ Aldrich", "Gabriella Fernandes",
            ],
            "Women's Bantamweight": [
                "Kayla Harrison", "Julianna Pena", "Raquel Pennington", "Joselyne Edwards", "Norma Dumont",
                "Ailin Perez", "Yana Santos", "Irene Aldana", "Macy Chiasson", "Luana Santos",
                "Jacqueline Cavalcanti", "Karol Rosa", "Bia Mesquita", "Nora Cornolle", "Michelle Montague",
                "Miesha Tate", "Melissa Croden", "Daria Zhelezniakova",
            ],
        }
        regions = {
            "Aspinall": "UK", "Gane": "Europe", "Volkov": "Europe", "Pavlovich": "Europe", "Kuniev": "Europe",
            "Delija": "Europe", "Pericic": "Europe", "Parkin": "UK", "Ulberg": "Australia", "Ankalaev": "Europe",
            "Prochazka": "Europe", "Blachowicz": "Europe", "Rakic": "Europe", "Oezdemir": "Europe",
            "Chimaev": "Europe", "Du Plessis": "Europe", "Imavov": "Europe", "Whittaker": "Australia",
            "Makhachev": "Europe", "Garry": "Europe", "Prates": "Brazil", "Morales": "Mexico",
            "Della Maddalena": "Australia", "Muhammad": "USA", "Edwards": "UK", "Usman": "USA",
            "Amosov": "Europe", "Medic": "Europe", "Topuria": "Europe", "Tsarukyan": "Europe",
            "Oliveira": "Brazil", "Pimblett": "UK", "Moicano": "Brazil", "Saint Denis": "Europe",
            "Volkanovski": "Australia", "Evloev": "Europe", "Lopes": "Brazil", "Murphy": "UK",
            "Rodriguez": "Mexico", "Costa": "Brazil", "Onama": "USA", "Pitbull": "Brazil",
            "Yan": "Europe", "Dvalishvili": "Europe", "Nurmagomedov": "Europe", "Yadong": "Asia",
            "Figueiredo": "Brazil", "Vera": "Brazil", "Rosas": "Mexico", "Barcelos": "Brazil",
            "Van": "USA", "Pantoja": "Brazil", "Kape": "Europe", "Taira": "Japan", "Horiguchi": "Japan",
            "Almabayev": "Europe", "Albazi": "Europe", "Moreno": "Mexico", "Chairez": "Mexico",
            "Zhang": "Asia", "Jandiroba": "Brazil", "Xiaonan": "Asia", "Godinez": "Mexico",
            "Lemos": "Brazil", "Ricci": "Brazil", "Andrade": "Brazil", "Ribas": "Brazil",
            "Silva": "Brazil", "Fiorot": "Europe", "Grasso": "Mexico", "Jasudavicius": "Canada",
            "Cong": "Asia", "Moura": "Brazil", "Fernandes": "Brazil", "Pena": "USA", "Dumont": "Brazil",
            "Perez": "Brazil", "Aldana": "Mexico", "Santos": "Brazil", "Cavalcanti": "Brazil",
            "Rosa": "Brazil", "Mesquita": "Brazil", "Cornolle": "Europe",
        }
        style_cycle = ["Well-Rounded", "Boxer", "Wrestler", "Kickboxer", "BJJ", "Muay Thai", "Grappler"]
        rows = []
        for division, names in ranked.items():
            weight = division.replace("Women's ", "")
            seen = set()
            for index, name in enumerate(names):
                if name in seen:
                    continue
                seen.add(name)
                key = next((token for token in regions if token in name), "")
                region = regions.get(key, "USA")
                popularity = max(48, 92 - index * 2)
                skill = max(76, 92 - index)
                age = max(22, min(42, 30 + (index % 9) - (2 if index < 5 else 0)))
                wins = max(6, 24 - index // 2 + random.randint(0, 4))
                losses = max(0, min(12, index // 3 + random.randint(0, 2)))
                style = style_cycle[index % len(style_cycle)]
                rows.append((name, weight, "UFC", popularity, skill, age, wins, losses, region, style))
        return rows

    def pfl_current_ranked_fighter_data(self):
        ranked = {
            "Heavyweight": [
                "Vadim Nemkov", "Oleg Popov", "Sergei Bilostenniy", "Denis Goltsov", "Alexandr Romanov",
                "Abraham Bably", "Maxwell Djantou Nana", "Jose Augusto", "Renan Ferreira", "Linton Vassell",
                "Slim Trabelsi", "Karl Williams",
            ],
            "Light Heavyweight": [
                "Corey Anderson", "Antonio Carlos Jr.", "Dovletdzhan Yagshimuradov", "Luke Trainer",
                "Sullivan Cauley", "Robert Wilkinson", "Simeon Powell", "Rasul Magomedov", "Tyson Pedro",
                "Emiliano Sordi", "Rafael Xavier",
            ],
            "Middleweight": [
                "Costello Van Steenis", "Johnny Eblen", "Fabian Edwards", "Impa Kasanganay", "Dalton Rosta",
                "Boris Atangana", "Aaron Jeffrey", "Josh Silveira", "Bryan Battle", "Josh Fremd",
                "Jhony Gregory",
            ],
            "Welterweight": [
                "Shamil Musaev", "Magomed Umalatov", "Thad Jean", "Abdoul Abdouraguimov", "Patrick Habirora",
                "Omar Al Dafrawy", "Florim Zendeli", "Ernesto Rodriguez", "Chris Mixan", "Cedric Doumbe",
            ],
            "Lightweight": [
                "Usman Nurmagomedov", "Alexander Shabliy", "Gadzhi Rabadanov", "Archie Colgan", "Alfie Davis",
                "Jakub Kaszuba", "Paul Hughes", "Jay Jay Wilson", "Natan Schulte", "Darragh Kelly",
                "Amru Magomedov",
            ],
            "Featherweight": [
                "Timur Khizriev", "AJ McKee", "Jesus Pinedo", "Salamat Isbulaev", "Gabriel Braga",
                "Ibragim Ibragimov", "Adam Borics", "Asael Adjoudj", "Alexei Pergande", "Khasan Magomedsharipov",
            ],
            "Bantamweight": [
                "Mitch McKee", "Renat Khavalov", "Sergio Pettis", "Taylor Lapilus", "Raufeon Stots",
                "Magomed Magomedov", "Sarvarjon Khamidov", "Marcirley Alves da Silva", "Naoki Inoue",
                "Lazaro Dayron",
            ],
            "Women's Flyweight": [
                "Dakota Ditcheva", "Liz Carmouche", "Taila Santos", "Jena Bishop", "Paulina Wisniewska",
                "Denise Kielholtz", "Viviane Araujo", "Sabrinna de Sousa", "Sumiko Inaba", "Montana De La Rosa",
            ],
        }
        regions = {
            "Nemkov": "Europe", "Popov": "Europe", "Bilostenniy": "Europe", "Goltsov": "Europe",
            "Romanov": "Europe", "Bably": "USA", "Nana": "Africa", "Augusto": "Brazil", "Ferreira": "Brazil",
            "Vassell": "UK", "Trabelsi": "Europe", "Anderson": "USA", "Carlos": "Brazil",
            "Yagshimuradov": "Europe", "Trainer": "UK", "Cauley": "USA", "Wilkinson": "Australia",
            "Powell": "UK", "Magomedov": "Europe", "Pedro": "Australia", "Sordi": "Brazil",
            "Xavier": "Brazil", "Steenis": "Europe", "Eblen": "USA", "Edwards": "UK",
            "Kasanganay": "USA", "Rosta": "USA", "Atangana": "Africa", "Jeffrey": "Canada",
            "Silveira": "USA", "Battle": "USA", "Fremd": "USA", "Gregory": "USA", "Musaev": "Europe",
            "Umalatov": "Europe", "Jean": "USA", "Abdouraguimov": "Europe", "Habirora": "Europe",
            "Dafrawy": "Africa", "Zendeli": "Europe", "Rodriguez": "Mexico", "Mixan": "USA",
            "Doumbe": "Europe", "Nurmagomedov": "Europe", "Shabliy": "Europe", "Rabadanov": "Europe",
            "Colgan": "USA", "Davis": "UK", "Kaszuba": "Europe", "Hughes": "UK", "Wilson": "New Zealand",
            "Schulte": "Brazil", "Kelly": "Europe", "Khizriev": "Europe", "McKee": "USA",
            "Pinedo": "Brazil", "Isbulaev": "Europe", "Braga": "Brazil", "Ibragimov": "Europe",
            "Borics": "Europe", "Adjoudj": "Europe", "Pergande": "USA", "Magomedsharipov": "Europe",
            "Pettis": "USA", "Lapilus": "Europe", "Stots": "USA", "Khamidov": "Europe",
            "Alves": "Brazil", "Inoue": "Japan", "Dayron": "Brazil", "Ditcheva": "UK",
            "Carmouche": "USA", "Santos": "Brazil", "Bishop": "USA", "Wisniewska": "Europe",
            "Kielholtz": "Europe", "Araujo": "Brazil", "Sousa": "Brazil", "Inaba": "USA",
            "Montana": "USA",
        }
        style_cycle = ["Well-Rounded", "Wrestler", "Kickboxer", "BJJ", "Boxer", "Muay Thai", "Grappler"]
        rows = []
        for division, names in ranked.items():
            weight = division.replace("Women's ", "")
            seen = set()
            for index, name in enumerate(names):
                if name in seen:
                    continue
                seen.add(name)
                key = next((token for token in regions if token in name), "")
                region = regions.get(key, "USA")
                popularity = max(42, 84 - index * 2)
                skill = max(73, 88 - index)
                age = max(23, min(43, 29 + (index % 8)))
                wins = max(6, 22 - index // 2 + random.randint(0, 4))
                losses = max(0, min(12, index // 3 + random.randint(0, 2)))
                style = style_cycle[index % len(style_cycle)]
                rows.append((name, weight, "PFL", popularity, skill, age, wins, losses, region, style))
        return rows

    def expanded_real_fighter_data(self):
        data = {company: list(fighters) for company, fighters in self.real_fighter_data().items()}
        # Curated active names which fill real competitive depth before the ranked-list importer runs.
        # The named profile table below gives these fighters deterministic ratings, styles, and traits.
        data["UFC"].extend([
            ("Manel Kape", "Flyweight", "UFC", 76, 86, 32, 21, 7, "Europe", "Kickboxer"),
            ("Asu Almabayev", "Flyweight", "UFC", 62, 82, 32, 22, 3, "Europe", "Wrestler"),
            ("Song Yadong", "Bantamweight", "UFC", 76, 86, 28, 22, 8, "Asia", "Kickboxer"),
            ("Mario Bautista", "Bantamweight", "UFC", 60, 82, 32, 16, 2, "USA", "Well-Rounded"),
            ("Jean Silva", "Featherweight", "UFC", 70, 85, 29, 16, 2, "Brazil", "Kickboxer"),
            ("Youssef Zalal", "Featherweight", "UFC", 60, 82, 29, 18, 5, "USA", "Well-Rounded"),
            ("Kevin Vallejos", "Featherweight", "UFC", 54, 80, 23, 16, 1, "Argentina", "Boxer"),
            ("Steve Garcia", "Featherweight", "UFC", 61, 81, 34, 18, 5, "USA", "Boxer"),
            ("Aaron Pico", "Featherweight", "UFC", 70, 84, 29, 13, 4, "USA", "Wrestler"),
            ("Melquizael Costa", "Featherweight", "UFC", 54, 80, 29, 23, 7, "Brazil", "BJJ"),
            ("Gabriel Bonfim", "Welterweight", "UFC", 61, 84, 28, 18, 1, "Brazil", "BJJ"),
            ("Leon Edwards", "Welterweight", "UFC", 84, 87, 34, 22, 5, "UK", "Kickboxer"),
            ("Kamaru Usman", "Welterweight", "UFC", 87, 86, 39, 21, 4, "USA", "Wrestler"),
            ("Mike Malott", "Welterweight", "UFC", 57, 80, 34, 12, 2, "Canada", "Well-Rounded"),
            ("Michael Venom Page", "Welterweight", "UFC", 82, 84, 39, 23, 3, "UK", "Karate"),
            ("Uros Medic", "Welterweight", "UFC", 48, 78, 33, 10, 3, "Europe", "Kickboxer"),
            ("Brendan Allen", "Middleweight", "UFC", 67, 85, 30, 25, 6, "USA", "BJJ"),
            ("Joe Pyfer", "Middleweight", "UFC", 58, 82, 29, 14, 3, "USA", "Boxer"),
            ("Israel Adesanya", "Middleweight", "UFC", 93, 88, 36, 24, 5, "New Zealand", "Kickboxer"),
            ("Gregory Rodrigues", "Middleweight", "UFC", 55, 81, 34, 17, 6, "Brazil", "Boxer"),
            ("Azamat Murzakanov", "Light Heavyweight", "UFC", 64, 84, 37, 16, 0, "Europe", "Boxer"),
            ("Jamahal Hill", "Light Heavyweight", "UFC", 78, 84, 35, 12, 3, "USA", "Boxer"),
            ("Volkan Oezdemir", "Light Heavyweight", "UFC", 65, 82, 36, 21, 8, "Europe", "Kickboxer"),
            ("Dominick Reyes", "Light Heavyweight", "UFC", 70, 83, 36, 15, 4, "USA", "Kickboxer"),
            ("Derrick Lewis", "Heavyweight", "UFC", 83, 81, 41, 29, 12, "USA", "Boxer"),
            ("Waldo Cortes Acosta", "Heavyweight", "UFC", 57, 79, 34, 15, 1, "USA", "Boxer"),
        ])
        data["PFL"].extend([
            ("Ramazan Kuramagomedov", "Welterweight", "PFL", 63, 85, 30, 14, 0, "Europe", "Sambo"),
            ("Thad Jean", "Welterweight", "PFL", 61, 84, 28, 11, 0, "USA", "Boxer"),
            ("Shamil Musaev", "Welterweight", "PFL", 68, 86, 31, 20, 1, "Europe", "Kickboxer"),
            ("Gadzhi Rabadanov", "Lightweight", "PFL", 61, 85, 32, 25, 4, "Europe", "Sambo"),
            ("Salamat Isbulaev", "Featherweight", "PFL", 55, 83, 35, 10, 0, "Europe", "Wrestler"),
            ("Ibragim Ibragimov", "Featherweight", "PFL", 45, 80, 24, 9, 0, "Europe", "Wrestler"),
            ("Sergio Pettis", "Bantamweight", "PFL", 72, 85, 32, 25, 7, "USA", "Kickboxer"),
            ("Viviane Araujo", "Flyweight", "PFL", 56, 80, 39, 13, 7, "Brazil", "Well-Rounded"),
        ])
        data["Cage Warriors"].extend([
            ("Nicolas Leblond", "Flyweight", "Cage Warriors", 42, 78, 28, 13, 4, "Europe", "Well-Rounded"),
            ("Weslley Maia", "Bantamweight", "Cage Warriors", 39, 77, 27, 12, 6, "Brazil", "BJJ"),
            ("Nikita Bagley", "Featherweight", "Cage Warriors", 42, 78, 26, 9, 1, "UK", "Boxer"),
            ("Ieuan Davies", "Lightweight", "Cage Warriors", 40, 77, 26, 8, 0, "UK", "Well-Rounded"),
            ("Sean Clancy Jr.", "Welterweight", "Cage Warriors", 43, 78, 28, 8, 0, "UK", "Wrestler"),
        ])
        data["UFC"].extend(self.ufc_current_ranked_fighter_data())
        data["PFL"].extend(self.pfl_current_ranked_fighter_data())
        data["UFC"].extend([
            ("Conor McGregor", "Lightweight", "UFC", 99, 92, 27, 22, 7, "Europe", "Boxer"),
            ("Mateusz Gamrot", "Lightweight", "UFC", 72, 85, 35, 25, 3, "Europe", "Wrestler"),
            ("Rafael Fiziev", "Lightweight", "UFC", 74, 84, 33, 12, 4, "Europe", "Kickboxer"),
            ("Renato Moicano", "Lightweight", "UFC", 76, 84, 37, 20, 6, "Brazil", "BJJ"),
            ("Dan Hooker", "Lightweight", "UFC", 78, 82, 36, 24, 12, "Australia", "Kickboxer"),
            ("Michael Chandler", "Lightweight", "UFC", 82, 83, 40, 23, 9, "USA", "Wrestler"),
            ("Kevin Holland", "Welterweight", "UFC", 80, 82, 33, 27, 13, "USA", "Kickboxer"),
            ("Vicente Luque", "Welterweight", "UFC", 74, 82, 34, 23, 10, "Brazil", "Muay Thai"),
            ("Geoff Neal", "Welterweight", "UFC", 70, 81, 35, 16, 6, "USA", "Boxer"),
            ("Joaquin Buckley", "Welterweight", "UFC", 73, 82, 32, 21, 6, "USA", "Kickboxer"),
            ("Shavkat Rakhmonov", "Welterweight", "UFC", 86, 90, 31, 19, 0, "Europe", "Sambo"),
            ("Paulo Costa", "Middleweight", "UFC", 78, 82, 35, 14, 4, "Brazil", "Kickboxer"),
            ("Marvin Vettori", "Middleweight", "UFC", 75, 83, 33, 19, 7, "Europe", "Wrestler"),
            ("Jared Cannonier", "Middleweight", "UFC", 77, 83, 42, 18, 8, "USA", "Kickboxer"),
            ("Anthony Hernandez", "Middleweight", "UFC", 69, 83, 32, 14, 2, "USA", "Wrestler"),
            ("Roman Dolidze", "Middleweight", "UFC", 68, 82, 37, 14, 4, "Europe", "Sambo"),
            ("Khalil Rountree Jr.", "Light Heavyweight", "UFC", 76, 82, 36, 14, 6, "USA", "Muay Thai"),
            ("Jan Blachowicz", "Light Heavyweight", "UFC", 78, 83, 43, 29, 10, "Europe", "Kickboxer"),
            ("Johnny Walker", "Light Heavyweight", "UFC", 72, 80, 34, 21, 9, "Brazil", "Kickboxer"),
            ("Marcin Tybura", "Heavyweight", "UFC", 69, 80, 40, 26, 9, "Europe", "Wrestler"),
            ("Jailton Almeida", "Heavyweight", "UFC", 73, 85, 35, 22, 4, "Brazil", "BJJ"),
            ("Curtis Blaydes", "Heavyweight", "UFC", 76, 84, 35, 18, 5, "USA", "Wrestler"),
            ("Serghei Spivac", "Heavyweight", "UFC", 66, 80, 31, 17, 5, "Europe", "Sambo"),
            ("Arnold Allen", "Featherweight", "UFC", 72, 83, 32, 20, 3, "UK", "Boxer"),
            ("Yair Rodriguez", "Featherweight", "UFC", 80, 84, 33, 19, 5, "Mexico", "Karate"),
            ("Brian Ortega", "Featherweight", "UFC", 79, 83, 35, 16, 4, "USA", "BJJ"),
            ("Aljamain Sterling", "Featherweight", "UFC", 82, 86, 36, 24, 5, "USA", "Wrestler"),
            ("Marlon Vera", "Bantamweight", "UFC", 78, 82, 33, 23, 10, "Brazil", "Kickboxer"),
            ("Deiveson Figueiredo", "Bantamweight", "UFC", 80, 84, 38, 24, 4, "Brazil", "Well-Rounded"),
            ("Brandon Moreno", "Flyweight", "UFC", 83, 85, 32, 22, 8, "Mexico", "Boxer"),
            ("Alexandre Pantoja", "Flyweight", "UFC", 84, 87, 36, 29, 5, "Brazil", "BJJ"),
            ("Zhang Weili", "Flyweight", "UFC", 91, 90, 37, 26, 4, "Japan", "Kickboxer"),
            ("Valentina Shevchenko", "Flyweight", "UFC", 90, 89, 38, 24, 4, "Europe", "Muay Thai"),
            ("Alexa Grasso", "Flyweight", "UFC", 84, 86, 33, 17, 4, "Mexico", "Boxer"),
            ("Manon Fiorot", "Flyweight", "UFC", 78, 85, 36, 12, 2, "Europe", "Kickboxer"),
            ("Erin Blanchfield", "Flyweight", "UFC", 73, 84, 27, 13, 2, "USA", "BJJ"),
            ("Rose Namajunas", "Flyweight", "UFC", 86, 84, 34, 14, 7, "USA", "Karate"),
            ("Yan Xiaonan", "Flyweight", "UFC", 76, 83, 37, 18, 4, "Japan", "Boxer"),
            ("Virna Jandiroba", "Flyweight", "UFC", 68, 83, 38, 21, 3, "Brazil", "BJJ"),
            ("Tatiana Suarez", "Flyweight", "UFC", 70, 85, 35, 11, 1, "USA", "Wrestler"),
            ("Jessica Andrade", "Flyweight", "UFC", 82, 83, 34, 26, 13, "Brazil", "Boxer"),
            ("Amanda Ribas", "Flyweight", "UFC", 72, 81, 32, 13, 5, "Brazil", "BJJ"),
            ("Maycee Barber", "Flyweight", "UFC", 70, 82, 28, 14, 2, "USA", "Kickboxer"),
            ("Natalia Silva", "Flyweight", "UFC", 68, 83, 29, 18, 5, "Brazil", "Kickboxer"),
            ("Jasmine Jasudavicius", "Flyweight", "UFC", 58, 78, 37, 12, 3, "Canada", "Wrestler"),
            ("Tracy Cortez", "Flyweight", "UFC", 62, 79, 32, 11, 2, "USA", "Wrestler"),
            ("Ketlen Vieira", "Bantamweight", "UFC", 70, 82, 34, 14, 4, "Brazil", "Judo"),
            ("Raquel Pennington", "Bantamweight", "UFC", 76, 82, 37, 16, 9, "USA", "Boxer"),
            ("Julianna Pena", "Bantamweight", "UFC", 78, 81, 36, 12, 6, "USA", "BJJ"),
            ("Holly Holm", "Bantamweight", "UFC", 84, 80, 44, 15, 7, "USA", "Boxer"),
            ("Macy Chiasson", "Bantamweight", "UFC", 61, 79, 35, 11, 3, "USA", "Kickboxer"),
            ("Norma Dumont", "Bantamweight", "UFC", 60, 79, 35, 12, 2, "Brazil", "Boxer"),
            ("Mayra Bueno Silva", "Bantamweight", "UFC", 65, 80, 34, 10, 4, "Brazil", "BJJ"),
            ("Iasmin Lucindo", "Flyweight", "UFC", 55, 78, 24, 17, 5, "Brazil", "Kickboxer"),
            ("Karolina Kowalkiewicz", "Flyweight", "UFC", 58, 77, 40, 16, 9, "Europe", "Kickboxer"),
            ("Loopy Godinez", "Flyweight", "UFC", 58, 78, 32, 13, 5, "Mexico", "Wrestler"),
            ("Tabatha Ricci", "Flyweight", "UFC", 55, 78, 31, 11, 2, "Brazil", "Judo"),
        ])
        data["PFL"].extend([
            ("Biaggio Ali Walsh", "Lightweight", "PFL", 50, 70, 28, 6, 1, "USA", "Boxer"),
            ("Mads Burnell", "Featherweight", "PFL", 55, 78, 32, 20, 6, "Europe", "BJJ"),
            ("Kai Kamaka III", "Featherweight", "PFL", 49, 75, 31, 13, 5, "USA", "Boxer"),
            ("Bubba Jenkins", "Featherweight", "PFL", 56, 77, 38, 21, 8, "USA", "Wrestler"),
            ("Leandro Higo", "Bantamweight", "PFL", 53, 76, 37, 23, 6, "Brazil", "BJJ"),
            ("Magomed Magomedov", "Bantamweight", "PFL", 57, 79, 34, 21, 4, "Europe", "Sambo"),
            ("Raufeon Stots", "Bantamweight", "PFL", 58, 79, 37, 20, 2, "USA", "Wrestler"),
            ("Archie Colgan", "Lightweight", "PFL", 48, 75, 30, 10, 0, "USA", "Wrestler"),
            ("Yaroslav Amosov", "Welterweight", "PFL", 71, 86, 32, 27, 1, "Europe", "Sambo"),
            ("Jason Jackson", "Welterweight", "PFL", 67, 82, 35, 18, 5, "USA", "Wrestler"),
            ("Dalton Rosta", "Middleweight", "PFL", 48, 75, 30, 9, 1, "USA", "Wrestler"),
            ("Tim Johnson", "Heavyweight", "PFL", 50, 74, 41, 18, 10, "USA", "Wrestler"),
            ("Linton Vassell", "Heavyweight", "PFL", 57, 77, 43, 24, 9, "UK", "Wrestler"),
            ("Phil Davis", "Light Heavyweight", "PFL", 60, 79, 41, 24, 7, "USA", "Wrestler"),
            ("Karl Moore", "Light Heavyweight", "PFL", 48, 76, 34, 12, 2, "UK", "BJJ"),
            ("Elora Dana", "Flyweight", "PFL", 42, 72, 26, 7, 0, "Brazil", "Muay Thai"),
            ("Cris Cyborg", "Featherweight", "PFL", 88, 86, 41, 28, 2, "Brazil", "Muay Thai"),
            ("Larissa Pacheco", "Featherweight", "PFL", 80, 85, 32, 23, 5, "Brazil", "Boxer"),
            ("Leah McCourt", "Featherweight", "PFL", 56, 77, 34, 8, 4, "Europe", "BJJ"),
            ("Sara Collins", "Bantamweight", "PFL", 44, 74, 30, 6, 0, "Australia", "Judo"),
        ])
        data["Cage Warriors"].extend([
            ("Jake Paul", "Cruiserweight" if "Cruiserweight" in WEIGHTS else "Light Heavyweight", "BAMMA", 88, 62, 29, 1, 0, "USA", "Boxer"),
            ("Logan Paul", "Heavyweight", "BAMMA", 86, 58, 31, 0, 0, "USA", "Boxer"),
            ("KSI", "Light Heavyweight", "BAMMA", 84, 60, 33, 0, 0, "UK", "Boxer"),
            ("Ryan Garcia", "Lightweight", "BAMMA", 82, 68, 27, 0, 0, "USA", "Boxer"),
            ("Brock Lesnar", "Heavyweight", "BAMMA", 90, 74, 48, 5, 3, "USA", "Wrestler"),
            ("CM Punk", "Welterweight", "BAMMA", 74, 48, 47, 0, 2, "USA", "Well-Rounded"),
            ("Bobby Lashley", "Heavyweight", "BAMMA", 72, 70, 50, 15, 2, "USA", "Wrestler"),
            ("Shayna Baszler", "Bantamweight", "BAMMA", 62, 67, 45, 15, 11, "USA", "Grappler"),
            ("Matt Riddle", "Middleweight", "BAMMA", 65, 71, 40, 8, 3, "USA", "Wrestler"),
            ("Will Currie", "Middleweight", "Cage Warriors", 41, 72, 27, 12, 4, "UK", "Wrestler"),
            ("Justin Burlinson", "Welterweight", "Cage Warriors", 42, 73, 29, 9, 2, "UK", "Boxer"),
            ("Tobias Harila", "Featherweight", "Cage Warriors", 40, 72, 31, 13, 5, "Europe", "Kickboxer"),
            ("James Hendin", "Featherweight", "Cage Warriors", 39, 72, 28, 8, 3, "UK", "Wrestler"),
            ("Giannis Bachar", "Welterweight", "Cage Warriors", 40, 72, 34, 8, 2, "Europe", "Kickboxer"),
            ("Teddy Stringer", "Lightweight", "Cage Warriors", 38, 71, 27, 8, 1, "UK", "BJJ"),
            ("Samuel Bark", "Featherweight", "Cage Warriors", 39, 72, 31, 10, 3, "Europe", "Muay Thai"),
            ("Dumitru Girlean", "Lightweight", "Cage Warriors", 39, 72, 26, 9, 2, "Europe", "Boxer"),
            ("Dec Dean", "Flyweight", "Cage Warriors", 36, 70, 26, 5, 1, "UK", "Well-Rounded"),
            ("Jawany Scott", "Bantamweight", "Cage Warriors", 38, 70, 32, 7, 4, "USA", "Kickboxer"),
            ("Liam Gittins", "Bantamweight", "Cage Warriors", 38, 71, 30, 11, 5, "UK", "BJJ"),
            ("Connor Wilson", "Welterweight", "Cage Warriors", 36, 70, 28, 7, 2, "UK", "Wrestler"),
            ("Shawn Da Silva", "Light Heavyweight", "Cage Warriors", 35, 70, 30, 6, 1, "Europe", "Kickboxer"),
            ("Fabrizio Fossati", "Heavyweight", "Cage Warriors", 34, 70, 31, 7, 2, "Europe", "Boxer"),
            ("Rory Evans", "Flyweight", "Cage Warriors", 36, 71, 27, 6, 3, "UK", "Wrestler"),
            ("Josh Reed", "Bantamweight", "Cage Warriors", 39, 71, 33, 14, 9, "UK", "Kickboxer"),
            ("Danni Neilan", "Flyweight", "Cage Warriors", 38, 71, 35, 7, 4, "Europe", "BJJ"),
            ("Eimear Darcy", "Flyweight", "Cage Warriors", 34, 69, 27, 6, 1, "Europe", "Kickboxer"),
            ("Shanelle Dyer", "Flyweight", "Cage Warriors", 40, 72, 25, 5, 0, "UK", "Muay Thai"),
            ("Molly McCann", "Flyweight", "Cage Warriors", 64, 77, 36, 14, 7, "UK", "Boxer"),
            ("Joanne Wood", "Flyweight", "Cage Warriors", 58, 76, 40, 17, 9, "UK", "Muay Thai"),
        ])
        data["BAMMA"] = [row for row in data["Cage Warriors"] if row[2] == "BAMMA"]
        data["Cage Warriors"] = [row for row in data["Cage Warriors"] if row[2] != "BAMMA"]
        data["ONE Championship"] = [
            ("Anatoly Malykhin", "Heavyweight", "ONE Championship", 78, 88, 38, 14, 0, "Europe", "Wrestler"),
            ("Reinier de Ridder", "Middleweight", "ONE Championship", 70, 84, 35, 17, 2, "Europe", "BJJ"),
            ("Aung La Nsang", "Middleweight", "ONE Championship", 67, 79, 41, 30, 15, "Asia", "Kickboxer"),
            ("Roberto Soldic", "Welterweight", "ONE Championship", 72, 83, 31, 20, 4, "Europe", "Kickboxer"),
            ("Christian Lee", "Lightweight", "ONE Championship", 74, 84, 28, 17, 4, "Asia", "Well-Rounded"),
            ("Ok Rae Yoon", "Lightweight", "ONE Championship", 62, 80, 35, 17, 4, "Asia", "Boxer"),
            ("Thanh Le", "Featherweight", "ONE Championship", 66, 81, 40, 14, 4, "USA", "Kickboxer"),
            ("Tang Kai", "Featherweight", "ONE Championship", 62, 82, 30, 18, 2, "Asia", "Boxer"),
            ("John Lineker", "Bantamweight", "ONE Championship", 72, 81, 36, 38, 11, "Brazil", "Boxer"),
            ("Fabricio Andrade", "Bantamweight", "ONE Championship", 65, 82, 29, 10, 2, "Brazil", "Muay Thai"),
            ("Demetrious Johnson ONE", "Flyweight", "ONE Championship", 86, 89, 39, 25, 4, "USA", "Well-Rounded"),
            ("Adriano Moraes", "Flyweight", "ONE Championship", 68, 82, 37, 20, 5, "Brazil", "BJJ"),
            ("Angela Lee", "Flyweight", "ONE Championship", 76, 83, 30, 11, 3, "Asia", "Well-Rounded"),
            ("Stamp Fairtex", "Flyweight", "ONE Championship", 78, 83, 29, 12, 2, "Asia", "Muay Thai"),
            ("Xiong Jing Nan", "Flyweight", "ONE Championship", 72, 82, 38, 18, 2, "Asia", "Boxer"),
            ("Denice Zamboanga", "Flyweight", "ONE Championship", 58, 77, 29, 11, 3, "Asia", "Wrestler"),
            ("Itsuki Hirata", "Flyweight", "ONE Championship", 52, 76, 27, 7, 3, "Japan", "Judo"),
            ("Alyse Anderson", "Flyweight", "ONE Championship", 50, 75, 31, 6, 3, "USA", "BJJ"),
        ]
        data["RIZIN Fighting Federation"] = [
            ("Luiz Gustavo", "Lightweight", "RIZIN Fighting Federation", 64, 82, 30, 16, 2, "Brazil", "Kickboxer"),
            ("Razhabali Shaidulloev", "Featherweight", "RIZIN Fighting Federation", 62, 82, 25, 13, 0, "Asia", "Wrestler"),
            ("Chihiro Suzuki", "Featherweight", "RIZIN Fighting Federation", 68, 81, 27, 13, 4, "Japan", "Kickboxer"),
            ("Danny Sabatello", "Bantamweight", "RIZIN Fighting Federation", 63, 81, 33, 16, 4, "USA", "Wrestler"),
            ("Makoto Shinryu", "Flyweight", "RIZIN Fighting Federation", 54, 78, 26, 16, 2, "Japan", "BJJ"),
            ("Yuki Motoya", "Bantamweight", "RIZIN Fighting Federation", 58, 79, 35, 35, 12, "Japan", "BJJ"),
            ("Shintaro Ishiwatari", "Bantamweight", "RIZIN Fighting Federation", 55, 77, 39, 27, 9, "Japan", "Wrestler"),
            ("Kyohei Hagiwara", "Featherweight", "RIZIN Fighting Federation", 56, 77, 30, 8, 6, "Japan", "Boxer"),
            ("Kyoji Horiguchi", "Bantamweight", "RIZIN Fighting Federation", 78, 84, 36, 33, 5, "Japan", "Karate"),
            ("Kai Asakura", "Bantamweight", "RIZIN Fighting Federation", 72, 82, 32, 21, 5, "Japan", "Kickboxer"),
            ("Juan Archuleta", "Bantamweight", "RIZIN Fighting Federation", 64, 80, 38, 29, 7, "USA", "Wrestler"),
            ("Naoki Inoue", "Bantamweight", "RIZIN Fighting Federation", 55, 78, 29, 18, 4, "Japan", "BJJ"),
            ("Mikuru Asakura", "Featherweight", "RIZIN Fighting Federation", 74, 80, 33, 17, 5, "Japan", "Kickboxer"),
            ("Kleber Koike Erbst", "Featherweight", "RIZIN Fighting Federation", 60, 81, 36, 31, 7, "Japan", "BJJ"),
            ("Vugar Karamov", "Featherweight", "RIZIN Fighting Federation", 52, 78, 34, 20, 5, "Europe", "Wrestler"),
            ("Yutaka Saito", "Featherweight", "RIZIN Fighting Federation", 53, 77, 38, 22, 8, "Japan", "Boxer"),
            ("Roberto Satoshi Souza", "Lightweight", "RIZIN Fighting Federation", 62, 82, 37, 16, 3, "Brazil", "BJJ"),
            ("Tofiq Musayev", "Lightweight", "RIZIN Fighting Federation", 58, 80, 36, 21, 6, "Europe", "Kickboxer"),
            ("Johnny Case", "Lightweight", "RIZIN Fighting Federation", 52, 77, 37, 28, 9, "USA", "Boxer"),
            ("Shinju Nozawa-Auclair", "Bantamweight", "RIZIN Fighting Federation", 52, 74, 32, 4, 2, "Japan", "Wrestler"),
            ("Rena Kubota", "Flyweight", "RIZIN Fighting Federation", 66, 78, 35, 14, 5, "Japan", "Kickboxer"),
            ("Seika Izawa", "Flyweight", "RIZIN Fighting Federation", 58, 82, 29, 13, 0, "Japan", "Judo"),
            ("Kanna Asakura", "Flyweight", "RIZIN Fighting Federation", 55, 77, 29, 20, 8, "Japan", "Wrestler"),
            ("Ayaka Hamasaki", "Flyweight", "RIZIN Fighting Federation", 58, 79, 44, 24, 6, "Japan", "Judo"),
        ]
        data["KSW"] = [
            ("Mamed Khalidov", "Middleweight", "KSW", 78, 82, 46, 37, 8, "Europe", "Kickboxer"),
            ("Roberto Soldic KSW", "Welterweight", "KSW", 68, 82, 31, 20, 4, "Europe", "Kickboxer"),
            ("Adrian Bartosinski", "Welterweight", "KSW", 62, 81, 31, 16, 1, "Europe", "Wrestler"),
            ("Salahdine Parnasse", "Lightweight", "KSW", 72, 84, 28, 20, 2, "Europe", "Well-Rounded"),
            ("Marian Ziolkowski", "Lightweight", "KSW", 58, 78, 36, 25, 9, "Europe", "Boxer"),
            ("Sebastian Przybysz", "Bantamweight", "KSW", 56, 78, 33, 13, 4, "Europe", "Kickboxer"),
            ("Jakub Wiklacz", "Bantamweight", "KSW", 55, 79, 30, 16, 3, "Europe", "BJJ"),
            ("Robert Ruchala", "Featherweight", "KSW", 52, 78, 28, 10, 1, "Europe", "Wrestler"),
            ("Daniel Rutkowski", "Featherweight", "KSW", 50, 76, 37, 17, 4, "Europe", "Boxer"),
            ("Phil De Fries", "Heavyweight", "KSW", 66, 82, 40, 25, 6, "UK", "Wrestler"),
            ("Darko Stosic", "Heavyweight", "KSW", 54, 78, 34, 19, 6, "Europe", "Kickboxer"),
            ("Ibragim Chuzhigaev", "Light Heavyweight", "KSW", 54, 78, 35, 18, 5, "Europe", "Sambo"),
            ("Tomasz Narkun", "Light Heavyweight", "KSW", 55, 77, 36, 18, 6, "Europe", "BJJ"),
            ("Karolina Owczarz", "Flyweight", "KSW", 48, 73, 33, 5, 3, "Europe", "Boxer"),
            ("Ewelina Wozniak", "Flyweight", "KSW", 44, 74, 32, 8, 2, "Europe", "Kickboxer"),
            ("Natalia Baczynska", "Bantamweight", "KSW", 42, 73, 29, 7, 2, "Europe", "Wrestler"),
        ]
        data["Legacy Fighting Alliance"] = [
            ("Bruno Souza", "Featherweight", "Legacy Fighting Alliance", 44, 76, 30, 12, 3, "Brazil", "Karate"),
            ("Josh Fremd", "Middleweight", "Legacy Fighting Alliance", 42, 75, 32, 11, 6, "USA", "Kickboxer"),
            ("Joshua Weems", "Bantamweight", "Legacy Fighting Alliance", 38, 72, 31, 11, 3, "USA", "BJJ"),
            ("Daniel Argueta", "Bantamweight", "Legacy Fighting Alliance", 42, 75, 32, 10, 2, "USA", "Wrestler"),
            ("Nick Maximov", "Middleweight", "Legacy Fighting Alliance", 42, 74, 28, 8, 2, "USA", "Wrestler"),
            ("Chris Brown LFA", "Welterweight", "Legacy Fighting Alliance", 40, 74, 36, 10, 4, "USA", "Boxer"),
            ("Harvey Park", "Lightweight", "Legacy Fighting Alliance", 38, 73, 39, 12, 4, "USA", "Boxer"),
            ("Vanessa Demopoulos LFA", "Flyweight", "Legacy Fighting Alliance", 46, 73, 37, 11, 6, "USA", "BJJ"),
            ("Mayra Cantuaria", "Flyweight", "Legacy Fighting Alliance", 36, 72, 32, 10, 5, "Brazil", "Muay Thai"),
            ("Melissa Croden", "Bantamweight", "Legacy Fighting Alliance", 34, 71, 28, 6, 2, "Canada", "Wrestler"),
            ("Darian Weeks", "Welterweight", "Legacy Fighting Alliance", 38, 73, 32, 8, 5, "USA", "Wrestler"),
            ("Anthony Ivy", "Welterweight", "Legacy Fighting Alliance", 36, 72, 36, 13, 7, "USA", "Boxer"),
        ]
        data["Oktagon MMA"] = [
            ("Will Fleury", "Heavyweight", "Oktagon MMA", 62, 83, 36, 17, 3, "Europe", "Well-Rounded"),
            ("Lazar Todev", "Heavyweight", "Oktagon MMA", 47, 77, 32, 11, 5, "Europe", "Wrestler"),
            ("Kerim Engizek", "Middleweight", "Oktagon MMA", 60, 82, 34, 22, 4, "Europe", "Kickboxer"),
            ("Krzysztof Jotko", "Middleweight", "Oktagon MMA", 64, 81, 37, 27, 6, "Europe", "Wrestler"),
            ("Kaik Brito", "Welterweight", "Oktagon MMA", 57, 81, 31, 17, 4, "Brazil", "Boxer"),
            ("Mochamed Machaev", "Welterweight", "Oktagon MMA", 50, 79, 25, 17, 2, "Europe", "Wrestler"),
            ("Mateusz Legierski", "Lightweight", "Oktagon MMA", 53, 80, 30, 13, 1, "Europe", "Well-Rounded"),
            ("Ronald Paradeiser", "Lightweight", "Oktagon MMA", 56, 80, 29, 21, 9, "Europe", "Kickboxer"),
            ("Losene Keita", "Featherweight", "Oktagon MMA", 62, 83, 28, 15, 1, "Europe", "Kickboxer"),
            ("Jonas Magard", "Bantamweight", "Oktagon MMA", 50, 79, 33, 19, 7, "Europe", "Wrestler"),
            ("Zhalgas Zhumagulov", "Flyweight", "Oktagon MMA", 60, 81, 37, 18, 9, "Asia", "Boxer"),
            ("Lucia Szabova", "Bantamweight", "Oktagon MMA", 58, 80, 27, 9, 0, "Europe", "Wrestler"),
        ]
        data["BRAVE Combat Federation"] = [
            ("Eldar Eldarov", "Lightweight", "BRAVE Combat Federation", 58, 81, 34, 16, 1, "Europe", "Sambo"),
            ("Abdisalam Uulu Kubanychbek", "Lightweight", "BRAVE Combat Federation", 50, 79, 28, 22, 4, "Asia", "Wrestler"),
            ("Muhammad Idrisov", "Featherweight", "BRAVE Combat Federation", 51, 79, 30, 14, 2, "Europe", "Wrestler"),
            ("Borislav Nikolic", "Bantamweight", "BRAVE Combat Federation", 48, 78, 31, 12, 2, "Europe", "BJJ"),
            ("Jarrah Al-Silawi", "Welterweight", "BRAVE Combat Federation", 58, 80, 34, 19, 5, "Asia", "Boxer"),
            ("Ismail Naurdiev", "Middleweight", "BRAVE Combat Federation", 52, 79, 30, 23, 7, "Europe", "Wrestler"),
            ("Mohammed Fakhreddine", "Light Heavyweight", "BRAVE Combat Federation", 54, 79, 41, 17, 5, "Asia", "Kickboxer"),
            ("Hamza Kooheji", "Bantamweight", "BRAVE Combat Federation", 46, 77, 30, 13, 3, "Asia", "Wrestler"),
        ]
        data["Absolute Championship Akhmat"] = [
            ("Abdul-Aziz Abdulvakhabov", "Lightweight", "Absolute Championship Akhmat", 62, 83, 36, 21, 3, "Europe", "Sambo"),
            ("Ali Bagov", "Lightweight", "Absolute Championship Akhmat", 55, 80, 35, 32, 12, "Europe", "Sambo"),
            ("Magomed Bibulatov", "Flyweight", "Absolute Championship Akhmat", 50, 79, 32, 20, 3, "Europe", "Wrestler"),
            ("Eduard Vartanyan", "Lightweight", "Absolute Championship Akhmat", 60, 82, 34, 25, 4, "Europe", "Kickboxer"),
            ("Mukhamed Kokov", "Featherweight", "Absolute Championship Akhmat", 48, 78, 30, 16, 4, "Europe", "Wrestler"),
            ("Abubakar Vagaev", "Welterweight", "Absolute Championship Akhmat", 48, 78, 33, 18, 4, "Europe", "Sambo"),
            ("Salambek Badaev", "Bantamweight", "Absolute Championship Akhmat", 43, 76, 28, 12, 2, "Europe", "Wrestler"),
            ("Vinicius Cruz", "Middleweight", "Absolute Championship Akhmat", 44, 76, 32, 10, 3, "Brazil", "BJJ"),
        ]
        extras = {
            "UFC": [
                ("Merab Dvalishvili", "Bantamweight", "UFC", 84, 90, 35, 19, 4, "Europe", "Wrestler"),
                ("Sean O'Malley", "Bantamweight", "UFC", 90, 88, 31, 18, 3, "USA", "Kickboxer"),
                ("Cory Sandhagen", "Bantamweight", "UFC", 78, 86, 34, 18, 5, "USA", "Kickboxer"),
                ("Umar Nurmagomedov", "Bantamweight", "UFC", 72, 88, 30, 18, 1, "Europe", "Sambo"),
                ("Petr Yan", "Bantamweight", "UFC", 80, 86, 33, 18, 5, "Europe", "Boxer"),
                ("Brandon Royval", "Flyweight", "UFC", 72, 84, 34, 17, 7, "USA", "BJJ"),
                ("Kai Kara-France", "Flyweight", "UFC", 70, 82, 33, 25, 11, "Australia", "Kickboxer"),
                ("Amir Albazi", "Flyweight", "UFC", 62, 83, 32, 17, 2, "Europe", "BJJ"),
                ("Steve Erceg", "Flyweight", "UFC", 60, 82, 30, 12, 3, "Australia", "Boxer"),
                ("Movsar Evloev", "Featherweight", "UFC", 70, 87, 32, 19, 0, "Europe", "Wrestler"),
                ("Lerone Murphy", "Featherweight", "UFC", 62, 83, 35, 15, 0, "UK", "Boxer"),
                ("Josh Emmett", "Featherweight", "UFC", 68, 81, 41, 19, 5, "USA", "Boxer"),
                ("Bryce Mitchell", "Featherweight", "UFC", 65, 81, 31, 17, 3, "USA", "Wrestler"),
                ("Mateusz Rebecki", "Lightweight", "UFC", 52, 79, 34, 19, 2, "Europe", "Wrestler"),
                ("Jalin Turner", "Lightweight", "UFC", 64, 80, 31, 14, 8, "USA", "Kickboxer"),
                ("Drew Dober", "Lightweight", "UFC", 66, 79, 37, 27, 14, "USA", "Boxer"),
                ("Beneil Dariush", "Lightweight", "UFC", 72, 82, 37, 22, 6, "USA", "BJJ"),
                ("Colby Covington", "Welterweight", "UFC", 82, 83, 38, 17, 5, "USA", "Wrestler"),
                ("Gilbert Burns", "Welterweight", "UFC", 78, 82, 39, 22, 8, "Brazil", "BJJ"),
                ("Stephen Thompson", "Welterweight", "UFC", 76, 80, 43, 17, 8, "USA", "Karate"),
                ("Bo Nickal", "Middleweight", "UFC", 67, 82, 30, 7, 0, "USA", "Wrestler"),
                ("Brendan Allen", "Middleweight", "UFC", 66, 82, 30, 24, 6, "USA", "BJJ"),
                ("Jamahal Hill", "Light Heavyweight", "UFC", 78, 82, 35, 12, 3, "USA", "Boxer"),
                ("Nikita Krylov", "Light Heavyweight", "UFC", 65, 80, 34, 30, 10, "Europe", "Sambo"),
                ("Alexander Volkov", "Heavyweight", "UFC", 72, 82, 37, 38, 11, "Europe", "Kickboxer"),
                ("Sergei Pavlovich", "Heavyweight", "UFC", 75, 83, 34, 18, 3, "Europe", "Boxer"),
                ("Kayla Harrison", "Bantamweight", "UFC", 84, 86, 35, 18, 1, "USA", "Judo"),
                ("Irene Aldana", "Bantamweight", "UFC", 70, 80, 38, 15, 8, "Mexico", "Boxer"),
                ("Mackenzie Dern", "Flyweight", "UFC", 72, 81, 33, 15, 5, "USA", "BJJ"),
                ("Marina Rodriguez", "Flyweight", "UFC", 68, 80, 39, 17, 5, "Brazil", "Muay Thai"),
                ("Angela Hill", "Flyweight", "UFC", 64, 78, 41, 18, 14, "USA", "Kickboxer"),
                ("Tecia Pennington", "Flyweight", "UFC", 58, 77, 36, 13, 7, "USA", "Karate"),
            ],
            "PFL": [
                ("Usman Nurmagomedov", "Lightweight", "PFL", 72, 86, 28, 19, 0, "Europe", "Sambo"),
                ("Patchy Mix", "Bantamweight", "PFL", 66, 84, 33, 20, 1, "USA", "BJJ"),
                ("Corey Anderson", "Light Heavyweight", "PFL", 66, 82, 37, 18, 6, "USA", "Wrestler"),
                ("Vadim Nemkov", "Light Heavyweight", "PFL", 70, 85, 34, 18, 2, "Europe", "Sambo"),
                ("Impa Kasanganay", "Light Heavyweight", "PFL", 58, 80, 32, 18, 5, "USA", "Well-Rounded"),
                ("Fabian Edwards", "Middleweight", "PFL", 55, 79, 33, 13, 4, "UK", "Kickboxer"),
                ("Johnny Eblen", "Middleweight", "PFL", 66, 86, 34, 16, 1, "USA", "Wrestler"),
                ("Logan Storley", "Welterweight", "PFL", 56, 80, 34, 16, 3, "USA", "Wrestler"),
                ("Goiti Yamauchi", "Welterweight", "PFL", 55, 79, 33, 29, 6, "Brazil", "BJJ"),
                ("Brent Primus", "Lightweight", "PFL", 54, 79, 41, 15, 4, "USA", "BJJ"),
                ("AJ McKee", "Lightweight", "PFL", 68, 83, 31, 22, 2, "USA", "Well-Rounded"),
                ("Dakota Ditcheva", "Flyweight", "PFL", 62, 82, 27, 14, 0, "UK", "Muay Thai"),
                ("Taila Santos", "Flyweight", "PFL", 66, 82, 33, 22, 4, "Brazil", "Muay Thai"),
                ("Liz Carmouche", "Flyweight", "PFL", 62, 80, 42, 22, 8, "USA", "Wrestler"),
                ("Kana Watanabe", "Flyweight", "PFL", 45, 76, 37, 13, 3, "Japan", "Judo"),
                ("Aspen Ladd", "Bantamweight", "PFL", 48, 76, 31, 12, 5, "USA", "Wrestler"),
                ("Julia Budd", "Featherweight", "PFL", 50, 76, 43, 17, 6, "Canada", "Kickboxer"),
                ("Michelle Montague", "Featherweight", "PFL", 38, 73, 28, 6, 1, "Australia", "BJJ"),
            ],
            "Cage Warriors": [
                ("Luke Riley", "Featherweight", "Cage Warriors", 44, 74, 27, 10, 0, "UK", "Boxer"),
                ("Jordan Vucenic", "Featherweight", "Cage Warriors", 45, 75, 30, 13, 3, "UK", "BJJ"),
                ("Morgan Charriere", "Featherweight", "Cage Warriors", 48, 76, 30, 19, 10, "Europe", "Kickboxer"),
                ("Paul Hughes CW", "Lightweight", "Cage Warriors", 42, 73, 24, 8, 1, "Europe", "Boxer"),
                ("Mason Jones", "Lightweight", "Cage Warriors", 46, 76, 31, 15, 2, "UK", "Well-Rounded"),
                ("George Hardwick", "Lightweight", "Cage Warriors", 44, 75, 30, 13, 2, "UK", "Kickboxer"),
                ("Modestas Bukauskas", "Light Heavyweight", "Cage Warriors", 48, 76, 32, 17, 6, "Europe", "Kickboxer"),
                ("Andy Clamp", "Light Heavyweight", "Cage Warriors", 34, 70, 36, 12, 4, "UK", "Wrestler"),
                ("Lone'er Kavanagh CW", "Flyweight", "Cage Warriors", 34, 70, 23, 5, 0, "UK", "Kickboxer"),
                ("Kennedy Freeman", "Bantamweight", "Cage Warriors", 34, 70, 28, 6, 0, "UK", "Kickboxer"),
                ("Awa Sow", "Flyweight", "Cage Warriors", 31, 69, 27, 6, 2, "Europe", "Wrestler"),
                ("Denise Kielholtz", "Flyweight", "Cage Warriors", 40, 74, 37, 8, 5, "Europe", "Kickboxer"),
            ],
            "PRIDE Fighting Championships": [
                ("Kazushi Sakuraba", "Middleweight", "PRIDE Fighting Championships", 89, 87, 31, 26, 17, "Japan", "Catch Wrestler"), ("Takanori Gomi", "Lightweight", "PRIDE Fighting Championships", 84, 85, 29, 36, 10, "Japan", "Boxer"),
                ("Igor Vovchanchyn", "Heavyweight", "PRIDE Fighting Championships", 82, 84, 30, 48, 12, "Europe", "Kickboxer"), ("Mark Kerr", "Heavyweight", "PRIDE Fighting Championships", 79, 85, 31, 15, 4, "USA", "Wrestler"),
                ("Kevin Randleman", "Heavyweight", "PRIDE Fighting Championships", 81, 84, 30, 17, 8, "USA", "Wrestler"), ("Don Frye", "Heavyweight", "PRIDE Fighting Championships", 80, 82, 32, 20, 7, "USA", "Boxer"),
                ("Gary Goodridge", "Heavyweight", "PRIDE Fighting Championships", 75, 79, 31, 18, 10, "Canada", "Kickboxer"), ("Ricardo Arona", "Light Heavyweight", "PRIDE Fighting Championships", 76, 83, 29, 14, 4, "Brazil", "BJJ"),
                ("Heath Herring", "Heavyweight", "PRIDE Fighting Championships", 74, 80, 30, 18, 8, "USA", "Kickboxer"), ("Kiyoshi Tamura", "Welterweight", "PRIDE Fighting Championships", 72, 81, 30, 13, 7, "Japan", "Catch Wrestler"),
                ("Hayato Sakurai", "Welterweight", "PRIDE Fighting Championships", 73, 82, 28, 28, 8, "Japan", "Wrestler"), ("Akihiro Gono", "Welterweight", "PRIDE Fighting Championships", 68, 79, 29, 22, 10, "Japan", "Kickboxer"),
                ("Yuki Kondo", "Middleweight", "PRIDE Fighting Championships", 67, 78, 30, 31, 14, "Japan", "Catch Wrestler"), ("Genki Sudo", "Welterweight", "PRIDE Fighting Championships", 76, 80, 28, 16, 4, "Japan", "Submission Grappler"),
                ("Kazuhiro Nakamura", "Light Heavyweight", "PRIDE Fighting Championships", 64, 77, 29, 15, 8, "Japan", "Judo"), ("Ikuhisa Minowa", "Light Heavyweight", "PRIDE Fighting Championships", 70, 78, 29, 28, 12, "Japan", "Catch Wrestler"),
            ],
            "Strikeforce": [
                ("Kimbo Slice", "Heavyweight", "Strikeforce", 86, 77, 32, 7, 2, "USA", "Boxer"), ("Cung Le", "Middleweight", "Strikeforce", 81, 84, 30, 9, 2, "USA", "Sanda"),
                ("Jake Shields", "Welterweight", "Strikeforce", 78, 86, 30, 26, 6, "USA", "BJJ"), ("Gilbert Melendez", "Lightweight", "Strikeforce", 84, 87, 29, 22, 4, "USA", "Wrestler"),
                ("Scott Smith", "Middleweight", "Strikeforce", 71, 78, 30, 17, 7, "USA", "Boxer"), ("Renato Sobral", "Light Heavyweight", "Strikeforce", 73, 81, 31, 18, 5, "Brazil", "BJJ"),
                ("Jorge Masvidal", "Lightweight", "Strikeforce", 79, 83, 28, 21, 6, "USA", "Boxer"), ("Marloes Coenen", "Featherweight", "Strikeforce", 72, 81, 29, 17, 5, "Europe", "BJJ"),
                ("Cristiane Justino", "Featherweight", "Strikeforce", 87, 88, 27, 12, 1, "Brazil", "Muay Thai"), ("Tonya Evinger", "Bantamweight", "Strikeforce", 65, 78, 28, 12, 4, "USA", "Wrestler"),
                ("Erin Toughill", "Featherweight", "Strikeforce", 61, 76, 30, 9, 3, "USA", "Boxer"), ("Julie Kedzie", "Bantamweight", "Strikeforce", 62, 77, 28, 15, 6, "USA", "Kickboxer"),
            ],
            "World Extreme Cagefighting": [
                ("Miguel Torres", "Bantamweight", "World Extreme Cagefighting", 77, 84, 28, 36, 3, "USA", "BJJ"), ("Scott Jorgensen", "Bantamweight", "World Extreme Cagefighting", 68, 79, 29, 12, 4, "USA", "Wrestler"),
                ("Brian Bowles", "Bantamweight", "World Extreme Cagefighting", 71, 81, 27, 8, 0, "USA", "Boxer"), ("Mike Brown", "Featherweight", "World Extreme Cagefighting", 73, 81, 31, 19, 4, "USA", "Wrestler"),
                ("Jens Pulver", "Lightweight", "World Extreme Cagefighting", 76, 80, 31, 22, 8, "USA", "Boxer"), ("Jamie Varner", "Lightweight", "World Extreme Cagefighting", 69, 79, 28, 16, 4, "USA", "Wrestler"),
                ("Chase Beebe", "Bantamweight", "World Extreme Cagefighting", 61, 76, 27, 10, 3, "USA", "Wrestler"), ("Antonio Banuelos", "Bantamweight", "World Extreme Cagefighting", 60, 75, 28, 15, 7, "USA", "Boxer"),
                ("Paulo Filho", "Middleweight", "World Extreme Cagefighting", 72, 82, 29, 16, 1, "Brazil", "BJJ"), ("Leonard Garcia", "Featherweight", "World Extreme Cagefighting", 68, 77, 28, 14, 5, "USA", "Boxer"),
                ("Wagnney Fabiano", "Featherweight", "World Extreme Cagefighting", 61, 78, 29, 13, 3, "Brazil", "BJJ"), ("Manny Gamburyan", "Featherweight", "World Extreme Cagefighting", 65, 79, 27, 10, 4, "USA", "Judo"),
                ("Rani Yahya", "Bantamweight", "World Extreme Cagefighting", 65, 80, 27, 15, 5, "Brazil", "BJJ"), ("Joseph Benavidez", "Flyweight", "World Extreme Cagefighting", 72, 82, 27, 12, 1, "USA", "Wrestler"),
                ("Eddie Wineland", "Bantamweight", "World Extreme Cagefighting", 67, 78, 28, 14, 4, "USA", "Boxer"), ("Chris Horodecki", "Lightweight", "World Extreme Cagefighting", 61, 76, 27, 13, 3, "Canada", "Kickboxer"),
            ],
        }
        for company, rows in extras.items():
            existing = {row[0] for row in data.setdefault(company, [])}
            for row in rows:
                if row[0] not in existing:
                    data[company].append(row)
                    existing.add(row[0])
        for company, rows in self.roster_depth_expansion().items():
            existing = {row[0] for row in data.setdefault(company, [])}
            for row in rows:
                if row[0] not in existing:
                    data[company].append(row)
                    existing.add(row[0])
        for company, rows in self.real_roster_depth_expansion_v2().items():
            existing = {row[0] for row in data.setdefault(company, [])}
            for row in rows:
                if row[0] not in existing:
                    data[company].append(row)
                    existing.add(row[0])
        return data

    def roster_depth_expansion(self):
        """Additive real-life depth for the Default Universe's opening rosters."""
        return {
            "UFC": [
                ("Tatsuro Taira", "Flyweight", "UFC", 70, 85, 25, 17, 1, "Japan", "BJJ"), ("Joshua Van", "Flyweight", "UFC", 68, 83, 24, 14, 2, "Asia", "Boxer"),
                ("Charles Johnson", "Flyweight", "UFC", 60, 80, 34, 18, 6, "USA", "Boxer"), ("Tagir Ulanbekov", "Flyweight", "UFC", 61, 82, 34, 17, 2, "Europe", "Sambo"),
                ("Alex Perez", "Flyweight", "UFC", 65, 80, 34, 25, 8, "USA", "Wrestler"), ("Aiemann Zahabi", "Bantamweight", "UFC", 62, 81, 38, 13, 2, "Canada", "Boxer"),
                ("Marcus McGhee", "Bantamweight", "UFC", 59, 80, 35, 10, 2, "USA", "Boxer"), ("Payton Talbott", "Bantamweight", "UFC", 57, 79, 27, 9, 1, "USA", "Kickboxer"),
                ("Rob Font", "Bantamweight", "UFC", 73, 81, 38, 22, 8, "USA", "Boxer"), ("Montel Jackson", "Bantamweight", "UFC", 56, 79, 33, 15, 2, "USA", "Kickboxer"),
                ("Dan Ige", "Featherweight", "UFC", 66, 81, 34, 19, 9, "USA", "Boxer"), ("Calvin Kattar", "Featherweight", "UFC", 72, 82, 37, 23, 9, "USA", "Boxer"),
                ("David Onama", "Featherweight", "UFC", 56, 80, 31, 13, 2, "USA", "Kickboxer"), ("Nathaniel Wood", "Featherweight", "UFC", 60, 81, 33, 21, 6, "UK", "Well-Rounded"),
                ("Grant Dawson", "Lightweight", "UFC", 60, 82, 32, 23, 2, "USA", "Wrestler"), ("Mauricio Ruffy", "Lightweight", "UFC", 58, 82, 30, 12, 1, "Brazil", "Kickboxer"),
                ("King Green", "Lightweight", "UFC", 71, 81, 39, 33, 17, "USA", "Boxer"), ("Terrance McKinney", "Lightweight", "UFC", 57, 80, 31, 16, 7, "USA", "Wrestler"),
                ("Randy Brown", "Welterweight", "UFC", 65, 81, 35, 20, 6, "USA", "Kickboxer"), ("Neil Magny", "Welterweight", "UFC", 69, 80, 39, 30, 13, "USA", "Well-Rounded"),
                ("Rinat Fakhretdinov", "Welterweight", "UFC", 59, 83, 34, 24, 2, "Europe", "Wrestler"), ("Michel Pereira", "Middleweight", "UFC", 72, 82, 32, 31, 12, "Brazil", "Kickboxer"),
                ("Ikram Aliskerov", "Middleweight", "UFC", 59, 83, 33, 16, 2, "Europe", "Sambo"), ("Carlos Ulberg", "Light Heavyweight", "UFC", 67, 84, 35, 12, 1, "New Zealand", "Kickboxer"),
                ("Ciryl Gane", "Heavyweight", "UFC", 83, 86, 36, 13, 2, "Europe", "Kickboxer"), ("Tai Tuivasa", "Heavyweight", "UFC", 75, 80, 33, 15, 8, "Australia", "Boxer"),
            ],
            "PFL": [
                ("Taylor Lapilus", "Bantamweight", "PFL", 55, 80, 33, 23, 4, "Europe", "Kickboxer"), ("Marcirley Alves", "Bantamweight", "PFL", 50, 79, 28, 15, 4, "Brazil", "BJJ"),
                ("Sarvajon Khamidov", "Bantamweight", "PFL", 52, 81, 30, 16, 1, "Asia", "Wrestler"), ("Ciaran Clarke", "Bantamweight", "PFL", 48, 78, 29, 10, 0, "UK", "Wrestler"),
                ("Timur Khizriev", "Featherweight", "PFL", 67, 85, 30, 18, 0, "Europe", "Wrestler"), ("Jesus Pinedo", "Featherweight", "PFL", 65, 83, 30, 26, 7, "Peru", "Boxer"),
                ("Adam Borics", "Featherweight", "PFL", 60, 81, 33, 20, 3, "Europe", "Kickboxer"), ("Gabriel Braga", "Featherweight", "PFL", 56, 80, 28, 16, 3, "Brazil", "BJJ"),
                ("Alfie Davis", "Lightweight", "PFL", 57, 80, 33, 20, 6, "UK", "Kickboxer"), ("Alexander Shabliy", "Lightweight", "PFL", 65, 84, 32, 24, 4, "Europe", "Kickboxer"),
                ("Jay Jay Wilson", "Lightweight", "PFL", 53, 80, 28, 11, 2, "New Zealand", "BJJ"), ("Natan Schulte", "Lightweight", "PFL", 56, 80, 33, 25, 5, "Brazil", "Wrestler"),
                ("Darragh Kelly", "Lightweight", "PFL", 49, 79, 27, 9, 0, "UK", "Wrestler"), ("Magomed Umalatov", "Welterweight", "PFL", 61, 83, 34, 18, 1, "Europe", "Sambo"),
                ("Costello van Steenis", "Middleweight", "PFL", 61, 83, 33, 17, 3, "Europe", "Kickboxer"), ("Jordan Newman", "Middleweight", "PFL", 48, 78, 31, 8, 0, "USA", "Wrestler"),
                ("Josh Silveira", "Middleweight", "PFL", 50, 79, 32, 15, 5, "USA", "Wrestler"), ("Oleg Popov", "Heavyweight", "PFL", 58, 81, 33, 19, 1, "Europe", "Wrestler"),
                ("Valentin Moldavsky", "Heavyweight", "PFL", 61, 82, 33, 14, 3, "Europe", "Sambo"), ("Denis Goltsov", "Heavyweight", "PFL", 60, 81, 35, 35, 8, "Europe", "Wrestler"),
                ("Eddie Alvarez", "Lightweight", "PFL", 85, 88, 34, 30, 8, "USA", "Boxer"), ("Gegard Mousasi", "Middleweight", "PFL", 84, 89, 33, 50, 8, "Europe", "Well-Rounded"),
                ("Douglas Lima", "Welterweight", "PFL", 80, 86, 31, 32, 8, "Brazil", "Boxer"),
            ],
            "Cage Warriors": [
                ("Paddy McCorry", "Middleweight", "Cage Warriors", 50, 78, 28, 8, 1, "UK", "Wrestler"), ("Aiden Lee", "Featherweight", "Cage Warriors", 48, 77, 29, 12, 6, "UK", "Kickboxer"),
                ("Nicolas Savio", "Lightweight", "Cage Warriors", 40, 74, 28, 8, 2, "Brazil", "BJJ"), ("Norbert Pietrzak", "Light Heavyweight", "Cage Warriors", 41, 75, 27, 8, 1, "Europe", "Wrestler"),
                ("Nell Ariano", "Light Heavyweight", "Cage Warriors", 39, 73, 29, 7, 2, "UK", "Kickboxer"), ("Oscar Ownsworth", "Lightweight", "Cage Warriors", 38, 72, 27, 7, 1, "UK", "Boxer"),
                ("Gabriele Galluccio", "Lightweight", "Cage Warriors", 38, 72, 28, 7, 2, "Europe", "BJJ"), ("Fraser Paterson", "Middleweight", "Cage Warriors", 38, 73, 29, 7, 2, "UK", "Wrestler"),
                ("Damiano Scogna", "Bantamweight", "Cage Warriors", 38, 73, 28, 7, 1, "Europe", "Kickboxer"), ("Ronny Henrique", "Bantamweight", "Cage Warriors", 39, 74, 30, 9, 3, "Brazil", "BJJ"),
                ("Stevie Lee", "Featherweight", "Cage Warriors", 39, 73, 29, 8, 2, "UK", "Boxer"), ("Vladimir Stanca", "Featherweight", "Cage Warriors", 38, 73, 29, 8, 3, "Europe", "Wrestler"),
                ("Anas Nfaou", "Lightweight", "Cage Warriors", 37, 72, 27, 6, 1, "Europe", "Kickboxer"), ("Randy Mboyo", "Lightweight", "Cage Warriors", 37, 72, 28, 7, 2, "Europe", "Boxer"),
                ("Luca Borando", "Lightweight", "Cage Warriors", 37, 72, 27, 6, 1, "Europe", "BJJ"), ("Zanyar Kamaran", "Featherweight", "Cage Warriors", 38, 73, 28, 8, 2, "UK", "Wrestler"),
                ("Joshua Onwordi", "Welterweight", "Cage Warriors", 38, 73, 29, 8, 2, "UK", "Boxer"), ("Ollie Sarwa", "Bantamweight", "Cage Warriors", 42, 75, 27, 9, 1, "UK", "Kickboxer"),
                ("Daniel Konrad", "Lightweight", "Cage Warriors", 40, 74, 28, 9, 2, "Europe", "Wrestler"), ("Manuel Del Valle", "Welterweight", "Cage Warriors", 39, 73, 30, 8, 2, "Europe", "Boxer"),
                ("Dan Hardy", "Welterweight", "Cage Warriors", 78, 84, 30, 25, 10, "UK", "Kickboxer"), ("Paul Daley", "Welterweight", "Cage Warriors", 82, 85, 31, 39, 15, "UK", "Boxer"),
                ("Ross Pearson", "Lightweight", "Cage Warriors", 72, 82, 30, 25, 13, "UK", "Boxer"), ("Brad Pickett", "Bantamweight", "Cage Warriors", 74, 82, 30, 25, 14, "UK", "Wrestler"),
                ("Callum Renshaw", "Flyweight", "Cage Warriors", 34, 70, 19, 4, 0, "UK", "Karate"), ("Aidan Mercer", "Flyweight", "Cage Warriors", 32, 69, 18, 3, 0, "UK", "Wrestler"),
                ("Owen Kershaw", "Bantamweight", "Cage Warriors", 36, 72, 20, 5, 1, "UK", "Boxer"), ("Rhys Maddox", "Bantamweight", "Cage Warriors", 35, 71, 19, 4, 0, "UK", "BJJ"),
                ("Elliot Vance", "Featherweight", "Cage Warriors", 37, 73, 21, 6, 1, "UK", "Kickboxer"), ("Kieran Holt", "Featherweight", "Cage Warriors", 34, 71, 20, 4, 0, "UK", "Wrestler"),
                ("Alfie Rowan", "Lightweight", "Cage Warriors", 38, 74, 21, 7, 1, "UK", "Well-Rounded"), ("Mason Kellett", "Lightweight", "Cage Warriors", 35, 72, 19, 5, 0, "UK", "Boxer"),
                ("Toby Marlow", "Welterweight", "Cage Warriors", 36, 73, 20, 6, 1, "UK", "Wrestler"), ("Harvey Quinn", "Welterweight", "Cage Warriors", 34, 71, 19, 4, 0, "UK", "Kickboxer"),
                ("Finley Shaw", "Middleweight", "Cage Warriors", 37, 73, 21, 7, 1, "UK", "BJJ"), ("Cameron Wren", "Middleweight", "Cage Warriors", 34, 71, 20, 5, 0, "UK", "Boxer"),
                ("Lewis Calder", "Light Heavyweight", "Cage Warriors", 35, 72, 22, 6, 1, "UK", "Kickboxer"), ("Reece Maddison", "Heavyweight", "Cage Warriors", 34, 71, 22, 5, 1, "UK", "Wrestler"),
                ("Sophie Renshaw", "Flyweight", "Cage Warriors", 35, 72, 20, 5, 0, "UK", "Kickboxer"), ("Erin Calvert", "Bantamweight", "Cage Warriors", 34, 71, 21, 5, 1, "UK", "BJJ"),
                ("Mia Kellett", "Featherweight", "Cage Warriors", 33, 70, 20, 4, 0, "UK", "Boxer"), ("Hannah Wren", "Lightweight", "Cage Warriors", 32, 69, 21, 4, 1, "UK", "Wrestler"),
            ],
        }

    def real_roster_depth_expansion_v2(self):
        """Named real MMA depth for opening rosters, never generated filler.

        These are deliberately conservative roster ratings. A fighter-specific profile
        still overrides the baseline where one exists, while the broad range keeps a
        newly added real athlete useful without incorrectly making every addition elite.
        """
        def rows(company, region, entries):
            built = []
            for index, (name, weight, style) in enumerate(entries):
                skill = 72 + (index % 7)
                popularity = 34 + (index % 8) * 3
                age = 24 + (index % 12)
                wins = 8 + (index % 11)
                losses = 1 + (index % 6)
                built.append((name, weight, company, popularity, skill, age, wins, losses, region, style))
            return built

        return {
            "UFC": rows("UFC", "USA", [
                ("Matt Schnell", "Flyweight", "BJJ"), ("Tim Elliott", "Flyweight", "Wrestler"),
                ("Bruno Silva Flyweight", "Flyweight", "BJJ"), ("Felipe Bunes", "Flyweight", "BJJ"),
                ("Jake Hadley", "Flyweight", "BJJ"), ("Ode Osbourne", "Flyweight", "Boxer"),
                ("Ricky Simon", "Bantamweight", "Wrestler"), ("Kyler Phillips", "Bantamweight", "Kickboxer"),
                ("Adrian Yanez", "Bantamweight", "Boxer"), ("Vinicius Oliveira", "Bantamweight", "Kickboxer"),
                ("Farid Basharat", "Bantamweight", "Wrestler"), ("Da'Mon Blackshear", "Bantamweight", "BJJ"),
                ("Cameron Smotherman", "Bantamweight", "Boxer"), ("Raul Rosas Jr.", "Bantamweight", "Wrestler"),
                ("Chris Gutierrez", "Bantamweight", "Kickboxer"), ("Kyung Ho Kang", "Bantamweight", "BJJ"),
                ("Giga Chikadze", "Featherweight", "Kickboxer"), ("Billy Quarantillo", "Featherweight", "Boxer"),
                ("Julian Erosa", "Featherweight", "BJJ"), ("Pat Sabatini", "Featherweight", "Wrestler"),
                ("Ricardo Ramos", "Featherweight", "BJJ"), ("Melsik Baghdasaryan", "Featherweight", "Kickboxer"),
                ("Hyder Amil", "Featherweight", "Boxer"), ("Choi Doo-ho", "Featherweight", "Boxer"),
                ("Andre Fili", "Featherweight", "Kickboxer"), ("Gabriel Santos", "Featherweight", "BJJ"),
                ("Michael Johnson", "Lightweight", "Boxer"), ("Matt Frevola", "Lightweight", "Wrestler"),
                ("Ignacio Bahamondes", "Lightweight", "Kickboxer"), ("Ludovit Klein", "Lightweight", "Kickboxer"),
                ("Chris Duncan", "Lightweight", "Boxer"), ("Manuel Torres", "Lightweight", "Boxer"),
                ("Thiago Moises", "Lightweight", "BJJ"), ("Chase Hooper", "Lightweight", "BJJ"),
                ("Nasrat Haqparast", "Lightweight", "Boxer"), ("Nazim Sadykhov", "Lightweight", "Kickboxer"),
                ("Carlos Prates", "Welterweight", "Muay Thai"), ("Daniel Rodriguez", "Welterweight", "Boxer"),
                ("Muslim Salikhov", "Welterweight", "Sanda"), ("Jeremiah Wells", "Welterweight", "Wrestler"),
                ("Bassil Hafez", "Welterweight", "Wrestler"), ("Santiago Ponzinibbio", "Welterweight", "Boxer"),
                ("Alex Morono", "Welterweight", "Kickboxer"), ("Nicolas Dalby", "Welterweight", "Karate"),
                ("Max Griffin", "Welterweight", "Boxer"), ("Roman Kopylov", "Middleweight", "Kickboxer"),
                ("Chris Curtis", "Middleweight", "Boxer"), ("Edmen Shahbazyan", "Middleweight", "Kickboxer"),
                ("Cesar Almeida", "Middleweight", "Kickboxer"), ("Andre Muniz", "Middleweight", "BJJ"),
                ("Jun Yong Park", "Middleweight", "Wrestler"), ("Abus Magomedov", "Middleweight", "Kickboxer"),
                ("Bogdan Guskov", "Light Heavyweight", "Boxer"), ("Alonzo Menifield", "Light Heavyweight", "Wrestler"),
                ("Ryan Spann", "Light Heavyweight", "BJJ"), ("Dustin Jacoby", "Light Heavyweight", "Kickboxer"),
                ("Oumar Sy", "Light Heavyweight", "Wrestler"), ("Ibo Aslan", "Light Heavyweight", "Kickboxer"),
                ("Jairzinho Rozenstruik", "Heavyweight", "Kickboxer"), ("Shamil Gaziev", "Heavyweight", "Wrestler"),
                ("Tallison Teixeira", "Heavyweight", "Kickboxer"), ("Marcos Rogerio de Lima", "Heavyweight", "Wrestler"),
                ("Justin Tafa", "Heavyweight", "Boxer"), ("Rodrigo Nascimento", "Heavyweight", "Wrestler"),
                ("Montana De La Rosa", "Flyweight", "Wrestler"), ("Karine Silva", "Flyweight", "BJJ"),
                ("Ariane da Silva", "Flyweight", "Muay Thai"), ("Miranda Maverick", "Flyweight", "Wrestler"),
                ("Luana Santos", "Flyweight", "Judo"), ("Ailin Perez", "Bantamweight", "Wrestler"),
                ("Karol Rosa", "Bantamweight", "Kickboxer"), ("Nora Cornolle", "Bantamweight", "Kickboxer"),
                ("Pannie Kianzad", "Bantamweight", "Boxer"), ("Joselyne Edwards", "Bantamweight", "Kickboxer"),
                ("Julia Avila", "Bantamweight", "BJJ"), ("Yana Santos", "Bantamweight", "Kickboxer"),
            ]),
            "ONE Championship": rows("ONE Championship", "Asia", [
                ("Joshua Pacio", "Flyweight", "Wrestler"), ("Jarred Brooks", "Flyweight", "Wrestler"),
                ("Yuya Wakamatsu", "Flyweight", "Boxer"), ("Reece McLaren", "Flyweight", "BJJ"),
                ("Jeremy Miado", "Flyweight", "Boxer"), ("Lito Adiwang", "Flyweight", "Wushu"),
                ("Mikey Musumeci", "Flyweight", "BJJ"), ("Kade Ruotolo", "Lightweight", "BJJ"),
                ("Tye Ruotolo", "Welterweight", "BJJ"), ("Sage Northcutt", "Welterweight", "Karate"),
                ("Zebaztian Kadestam", "Welterweight", "Muay Thai"), ("Garry Tonon", "Featherweight", "BJJ"),
                ("Shamil Gasanov", "Featherweight", "Wrestler"), ("Martin Nguyen", "Featherweight", "Boxer"),
                ("Dae Hwan Kim", "Bantamweight", "Wrestler"), ("Kevin Belingon", "Bantamweight", "Wushu"),
                ("Arjan Bhullar", "Heavyweight", "Wrestler"), ("Marcus Almeida", "Heavyweight", "BJJ"),
                ("Oumar Kane", "Heavyweight", "Wrestler"), ("Amir Aliakbari", "Heavyweight", "Wrestler"),
                ("Meng Bo", "Flyweight", "Boxer"), ("Jihin Radzuan", "Flyweight", "Muay Thai"),
                ("Alyona Rassohyna", "Flyweight", "BJJ"), ("Chihiro Sawada", "Flyweight", "Wrestler"),
            ]),
            "RIZIN Fighting Federation": rows("RIZIN Fighting Federation", "Japan", [
                ("Kintaro", "Bantamweight", "Boxer"), ("Masanori Kanehara", "Featherweight", "Wrestler"),
                ("Kazuma Kuramoto", "Bantamweight", "Wrestler"), ("Yuki Tokoro", "Bantamweight", "BJJ"),
                ("Shinobu Ota", "Bantamweight", "Wrestler"), ("Yachi Yu", "Lightweight", "Kickboxer"),
                ("Koji Takeda", "Lightweight", "Wrestler"), ("Luiz Ishihara", "Featherweight", "Boxer"),
                ("Ren Hiramoto", "Featherweight", "Kickboxer"), ("Yutaka Saito", "Featherweight", "Boxer"),
                ("Kota Miura", "Featherweight", "Karate"), ("Kouya Kanda", "Lightweight", "Wrestler"),
                ("Mikio Ueda", "Lightweight", "BJJ"), ("Kleber Koike Erbst", "Featherweight", "BJJ"),
                ("Kyoji Horiguchi", "Bantamweight", "Karate"), ("Tofiq Musayev", "Lightweight", "Kickboxer"),
                ("Satoshi Yamasu", "Featherweight", "Kickboxer"), ("Yoshinori Horie", "Featherweight", "Boxer"),
                ("Miyuu Yamamoto", "Flyweight", "Wrestler"), ("Si Woo Park", "Flyweight", "Kickboxer"),
                ("Sena Kubota", "Flyweight", "Kickboxer"), ("Ayaka Watanabe", "Flyweight", "Wrestler"),
            ]),
            "KSW": rows("KSW", "Europe", [
                ("Michal Materla", "Middleweight", "Wrestler"), ("Pawel Pawlak", "Welterweight", "Boxer"),
                ("Andrzej Grzebyk", "Welterweight", "Kickboxer"), ("Damian Janikowski", "Middleweight", "Wrestler"),
                ("Bartosz Lesko", "Middleweight", "BJJ"), ("Radek Paczuski", "Middleweight", "Kickboxer"),
                ("Artur Szpilka", "Heavyweight", "Boxer"), ("Rafal Haratyk", "Light Heavyweight", "Kickboxer"),
                ("Damian Piwowarczyk", "Light Heavyweight", "Wrestler"), ("Przemyslaw Mysiala", "Light Heavyweight", "Boxer"),
                ("Sebastian Rajewski", "Lightweight", "Kickboxer"), ("Adrian Zielinski", "Lightweight", "Wrestler"),
                ("Patryk Kaczmarczyk", "Featherweight", "Wrestler"), ("Artur Sowinski", "Featherweight", "Boxer"),
                ("Damian Stasiak", "Bantamweight", "BJJ"), ("Bruno Augusto", "Bantamweight", "BJJ"),
                ("Wiktoria Czyzewska", "Bantamweight", "Kickboxer"), ("Adrianna Kreft", "Flyweight", "BJJ"),
            ]),
            "Legacy Fighting Alliance": rows("Legacy Fighting Alliance", "USA", [
                ("Jose Johnson", "Bantamweight", "BJJ"), ("Kevin Natividad", "Bantamweight", "Boxer"),
                ("Justin Gonzales", "Featherweight", "Wrestler"), ("Cody Law", "Featherweight", "Wrestler"),
                ("Nate Jennerman", "Featherweight", "BJJ"), ("Lucas Clay", "Lightweight", "Wrestler"),
                ("Anthony Romero", "Lightweight", "Wrestler"), ("Lucas Martino", "Lightweight", "Boxer"),
                ("Solomon Renfro", "Welterweight", "Wrestler"), ("Kurt Holobaugh", "Lightweight", "BJJ"),
                ("Billy Goff", "Welterweight", "Boxer"), ("Cody Brundage", "Middleweight", "Wrestler"),
                ("Brendan Allen LFA", "Middleweight", "BJJ"), ("Tanner Boser", "Heavyweight", "Kickboxer"),
                ("Chase Sherman", "Heavyweight", "Boxer"), ("Chelsea Chandler", "Bantamweight", "Boxer"),
                ("Katharina Lehner", "Bantamweight", "Kickboxer"), ("Sam Hughes", "Flyweight", "Wrestler"),
            ]),
            "Oktagon MMA": rows("Oktagon MMA", "Europe", [
                ("Karlos Vemola", "Light Heavyweight", "Wrestler"), ("Samuel Kristofic", "Middleweight", "Kickboxer"),
                ("Marek Bartl", "Middleweight", "Wrestler"), ("Christian Jungwirth", "Welterweight", "Kickboxer"),
                ("Christian Eckerlin", "Welterweight", "Wrestler"), ("Ion Surdu", "Welterweight", "Kickboxer"),
                ("Matous Kohout", "Lightweight", "Boxer"), ("Vladimir Lengal", "Lightweight", "Boxer"),
                ("Roman Paulus", "Featherweight", "Kickboxer"), ("David Kozma", "Welterweight", "Wrestler"),
                ("Denislav Erslan", "Light Heavyweight", "Kickboxer"), ("Daniel Skvor", "Light Heavyweight", "Kickboxer"),
                ("Melvin Mane", "Heavyweight", "Kickboxer"), ("Milos Petrasek", "Light Heavyweight", "Wrestler"),
                ("Tereza Bleda", "Flyweight", "Wrestler"), ("Lucie Pudilova", "Bantamweight", "Kickboxer"),
            ]),
            "BRAVE Combat Federation": rows("BRAVE Combat Federation", "Asia", [
                ("Jose Torres", "Flyweight", "Wrestler"), ("Velimurad Alkhasov", "Bantamweight", "Wrestler"),
                ("Flavio Queiroz", "Bantamweight", "BJJ"), ("Rami Hamed", "Bantamweight", "Wrestler"),
                ("Abdoul Abdouraguimov", "Welterweight", "Wrestler"), ("Dumar Roa", "Welterweight", "Boxer"),
                ("Kamal Magomedov", "Lightweight", "Wrestler"), ("Khalid Taha", "Bantamweight", "Boxer"),
                ("Mochamed Machaev", "Welterweight", "Wrestler"), ("Mansur Azhiev", "Featherweight", "Wrestler"),
                ("Abdoul Hussein", "Featherweight", "BJJ"), ("Zia Mashwani", "Featherweight", "Kickboxer"),
                ("Elias Boudegzdame", "Featherweight", "BJJ"), ("Sami Chaoui", "Lightweight", "Boxer"),
                ("Mohamed Fakhreddine", "Light Heavyweight", "Kickboxer"), ("Aziz Karagula-Akan", "Heavyweight", "Wrestler"),
            ]),
            "Absolute Championship Akhmat": rows("Absolute Championship Akhmat", "Europe", [
                ("Artem Reznikov", "Lightweight", "Wrestler"), ("Yusuf Raisov", "Featherweight", "Wrestler"),
                ("Albert Tumenov", "Welterweight", "Boxer"), ("Rustam Kerimov", "Bantamweight", "Wrestler"),
                ("Murad Machaev", "Featherweight", "Wrestler"), ("Akhmed Aliev", "Lightweight", "Kickboxer"),
                ("Magomedrasul Khasbulaev", "Featherweight", "Wrestler"), ("Denis Smoldarev", "Heavyweight", "Wrestler"),
                ("Evgeny Erokhin", "Heavyweight", "Sambo"), ("Magomed Ismailov", "Middleweight", "Wrestler"),
                ("Arbi Agujev", "Welterweight", "Wrestler"), ("Bibir Tuvshinjargal", "Bantamweight", "Wrestler"),
                ("Gadzhimurad Antigulov", "Light Heavyweight", "Wrestler"), ("Oleg Olenichev", "Light Heavyweight", "BJJ"),
            ]),
            "PRIDE Fighting Championships": rows("PRIDE Fighting Championships", "Japan", [
                ("Antonio Rodrigo Nogueira", "Heavyweight", "BJJ"), ("Antonio Rogerio Nogueira", "Light Heavyweight", "Boxer"),
                ("Josh Barnett", "Heavyweight", "Catch Wrestler"), ("Vanderlei Silva", "Middleweight", "Muay Thai"),
                ("Mauricio Rua", "Light Heavyweight", "Muay Thai"), ("Rogério Minotouro Nogueira", "Light Heavyweight", "Boxer"),
                ("Ricardo Arona", "Light Heavyweight", "BJJ"), ("Ryo Chonan", "Welterweight", "Wrestler"),
                ("Denis Kang", "Middleweight", "BJJ"), ("Paulo Filho", "Middleweight", "BJJ"),
                ("Murilo Ninja Rua", "Middleweight", "Muay Thai"), ("Akihiro Gono", "Welterweight", "Kickboxer"),
                ("Tatsuya Kawajiri", "Lightweight", "Wrestler"), ("Shinya Aoki", "Lightweight", "BJJ"),
            ]),
            "Strikeforce": rows("Strikeforce", "USA", [
                ("Antonio Silva", "Heavyweight", "Boxer"), ("Fabricio Werdum", "Heavyweight", "BJJ"),
                ("Josh Thomson", "Lightweight", "Kickboxer"), ("Rafael Cavalcante", "Light Heavyweight", "Kickboxer"),
                ("Muhammed Lawal", "Light Heavyweight", "Wrestler"), ("Lorenz Larkin", "Welterweight", "Kickboxer"),
                ("Tyron Woodley", "Welterweight", "Wrestler"), ("Tim Kennedy", "Middleweight", "Wrestler"),
                ("Ronaldo Souza", "Middleweight", "BJJ"), ("Luke Rockhold", "Middleweight", "Kickboxer"),
                ("Tarec Saffiedine", "Welterweight", "Kickboxer"), ("Pat Healy", "Lightweight", "Wrestler"),
                ("Sarah Kaufman", "Bantamweight", "Kickboxer"), ("Miesha Tate", "Bantamweight", "Wrestler"),
                ("Gina Carano", "Featherweight", "Muay Thai"), ("Cyborg Santos", "Featherweight", "Muay Thai"),
            ]),
            "World Extreme Cagefighting": rows("World Extreme Cagefighting", "USA", [
                ("Wagnney Fabiano", "Featherweight", "BJJ"), ("Leonard Garcia", "Featherweight", "Boxer"),
                ("Manny Gamburyan", "Bantamweight", "Judo"), ("Rani Yahya", "Bantamweight", "BJJ"),
                ("Eddie Wineland", "Bantamweight", "Boxer"), ("Chris Horodecki", "Lightweight", "Kickboxer"),
                ("Shane Roller", "Lightweight", "Wrestler"), ("Donald Cerrone WEC", "Lightweight", "Kickboxer"),
                ("Ben Henderson WEC", "Lightweight", "Wrestler"), ("Anthony Njokuani", "Lightweight", "Kickboxer"),
                ("Rafael Assuncao", "Bantamweight", "BJJ"), ("Jameel Massouh", "Featherweight", "Wrestler"),
                ("Chad Mendes", "Featherweight", "Wrestler"), ("Mark Hominick", "Featherweight", "Boxer"),
            ]),
        }

    def nexgen_mma_prospect_names(self):
        return {
            "Paddy Pimblett", "Callum Renshaw", "Aidan Mercer", "Owen Kershaw", "Rhys Maddox", "Elliot Vance", "Kieran Holt", "Alfie Rowan", "Mason Kellett",
            "Toby Marlow", "Harvey Quinn", "Finley Shaw", "Cameron Wren", "Lewis Calder", "Reece Maddison", "Sophie Renshaw", "Erin Calvert", "Mia Kellett", "Hannah Wren",
        }

    def legend_fighter_data(self):
        return [
            ("Georges St-Pierre", "Welterweight", "Legend", 96, 92, 31, 26, 2, "Canada", "Wrestler"),
            ("Anderson Silva", "Middleweight", "Legend", 95, 89, 33, 34, 11, "Brazil", "Muay Thai"),
            ("Jon Jones", "Heavyweight", "Legend", 98, 94, 31, 28, 1, "USA", "Well-Rounded"),
            ("Demetrious Johnson", "Flyweight", "Legend", 91, 91, 30, 25, 4, "USA", "Well-Rounded"),
            ("Jose Aldo", "Featherweight", "Legend", 90, 87, 29, 32, 9, "Brazil", "Muay Thai"),
            ("Khabib Nurmagomedov", "Lightweight", "Legend", 96, 93, 29, 29, 0, "Europe", "Sambo"),
            ("Daniel Cormier", "Heavyweight", "Legend", 89, 88, 35, 22, 3, "USA", "Wrestler"),
            ("Fedor Emelianenko", "Heavyweight", "Legend", 92, 88, 31, 40, 7, "Europe", "Sambo"),
            ("Ronda Rousey", "Bantamweight", "Legend", 91, 84, 28, 12, 2, "USA", "Judo"),
            ("Amanda Nunes", "Bantamweight", "Legend", 94, 90, 31, 23, 5, "Brazil", "Boxer"),
            ("Nate Diaz", "Welterweight", "Legend", 90, 79, 28, 22, 13, "USA", "BJJ"),
            ("BJ Penn", "Lightweight", "Legend", 88, 85, 29, 16, 5, "USA", "BJJ"),
            ("Frankie Edgar", "Lightweight", "Legend", 89, 86, 30, 17, 4, "USA", "Wrestler"),
            ("Urijah Faber", "Bantamweight", "Legend", 88, 85, 30, 23, 3, "USA", "Wrestler"),
            ("Lyoto Machida", "Light Heavyweight", "Legend", 90, 87, 30, 16, 0, "Brazil", "Karate"),
            ("Mauricio Rua", "Light Heavyweight", "Legend", 89, 86, 29, 19, 3, "Brazil", "Muay Thai"),
            ("Quinton Jackson", "Light Heavyweight", "Legend", 88, 85, 30, 26, 6, "USA", "Boxer"),
            ("Mirko Cro Cop", "Heavyweight", "Legend", 90, 87, 31, 22, 4, "Europe", "Kickboxer"),
            ("Wanderlei Silva", "Middleweight", "Legend", 89, 85, 31, 27, 3, "Brazil", "Muay Thai"),
            ("Matt Hughes", "Welterweight", "Legend", 88, 85, 31, 34, 3, "USA", "Wrestler"),
            ("Robbie Lawler", "Welterweight", "Legend", 89, 85, 31, 22, 4, "USA", "Boxer"),
            ("Demian Maia", "Welterweight", "Legend", 88, 86, 32, 20, 4, "Brazil", "BJJ"),
            ("Joanna Jedrzejczyk", "Flyweight", "Legend", 90, 86, 29, 14, 0, "Europe", "Muay Thai"),
            ("Gina Carano", "Bantamweight", "Legend", 84, 80, 27, 7, 0, "USA", "Muay Thai"),
        ]

    def prime_legend_ages(self):
        return {row[0]: row[5] for row in self.legend_fighter_data()}

    def historic_prime_age_overrides(self):
        """Playable prime ages for historical stars seeded into the modern universe."""
        ages = self.prime_legend_ages()
        ages.update({
            "Conor McGregor": 27, "Anthony Pettis": 28, "Miesha Tate": 29,
            "Michael Venom Page": 30, "Michael Page": 30, "Eddie Alvarez": 31,
            "Cat Zingano": 29, "Carlos Condit": 29, "Holly Holm": 31,
            "Tyron Woodley": 30, "Junior Dos Santos": 30, "Nick Diaz": 28,
            "Phil Davis": 29, "Alistair Overeem": 31, "Aung La Nsang": 29,
            "Luke Rockhold": 29, "Stephen Thompson": 30, "Fabricio Werdum": 31,
            "Rousimar Palhares": 27, "Hector Lombard": 31, "Chael Sonnen": 31,
            "Jacare Souza": 29, "Josh Barnett": 31, "Mamed Khalidov": 30,
            "Yoel Romero": 31, "Kimbo Slice": 32, "Cung Le": 30,
            "Kazushi Sakuraba": 31, "Takanori Gomi": 29, "Igor Vovchanchyn": 30,
            "Mark Kerr": 31, "Kevin Randleman": 30, "Don Frye": 32,
            "Gilbert Melendez": 29, "Jake Shields": 30, "Miguel Torres": 28,
            "Jens Pulver": 31, "Joseph Benavidez": 27,
        })
        return ages

    def enrich_fighter(self, fighter, player_owned=False):
        if fighter.region == "USA" and not player_owned:
            fighter.region = random.choice(REGION_GENERATION_POOL)
        elif player_owned:
            fighter.region = random.choice(["USA", "Canada", "Brazil", "UK", "Japan"])
        fighter.style = random.choice(STYLES)
        fighter.primary_discipline = "MMA"
        fighter.combat_background = {
            "Boxer": "Boxing", "Kickboxer": "Kickboxing", "Dutch Kickboxer": "Kickboxing", "Muay Thai": "Muay Thai",
            "Wrestler": "Wrestling", "Freestyle Wrestler": "Wrestling", "Catch Wrestler": "Wrestling",
            "BJJ": "Brazilian Jiu-Jitsu", "Submission Grappler": "Brazilian Jiu-Jitsu", "Grappler": "Brazilian Jiu-Jitsu",
        }.get(fighter.style, "Mixed martial arts")
        fighter.multi_sport_records = fighter.multi_sport_records or {"MMA": f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"}
        fighter.crossover_history = fighter.crossover_history or []
        fighter.stance = random.choices(["Orthodox", "Southpaw", "Switch"], weights=[58, 29, 13], k=1)[0]
        fighter.trait = random.choice(TRAITS)
        fighter.behaviour = random.choice(BEHAVIOURS)
        fighter.camp = random.choice(CAMPS)
        fighter.exclusive = player_owned or random.random() < 0.55
        fighter.contract_type = "Exclusive" if fighter.exclusive else "Non-Exclusive"
        fighter.negotiation_heat = random.randint(0, 35)
        fighter.negotiation_persona = random.choices(
            ["Professional", "Hard Bargainer", "Loyalist", "Star Chaser", "Security First", "Competitive"],
            weights=[34, 17, 14, 12, 13, 10],
            k=1,
        )[0]
        fighter.agent_name = random.choice(["Independent", "Apex Sports", "Northstar Management", "Forge Talent", "Summit Representation"])
        fighter.media_heat = random.randint(0, 25)
        fighter.star_quality = max(1, min(99, round(fighter.popularity * 0.55 + fighter.overall * 0.25 + random.randint(0, 28))))
        fighter.charisma = max(1, min(99, round(fighter.popularity * 0.45 + random.randint(15, 55))))
        pro_trait = 10 if fighter.trait in ("Gym Rat", "Clutch", "Quiet Professional", "Coach Favourite", "Gym Leader", "Title Mentality", "Technical Learner", "Warrior Spirit") else 0
        pro_trait -= 10 if fighter.trait in ("Erratic", "Trash Talker", "Bad Weight Cut") else 0
        fighter.professionalism = max(1, min(99, random.randint(38, 88) + pro_trait))
        injury_trait = 18 if fighter.trait in ("Fragile", "Injury Magnet", "Slow Healer") else -10 if fighter.trait in ("Iron Chin", "Veteran Savvy", "Fast Healer") else 0
        fighter.injury_proneness = max(1, min(99, random.randint(8, 42) + injury_trait + max(0, fighter.age - 34)))
        finish_trait = 10 if fighter.trait in ("Big Finisher", "Knockout Artist", "Submission Ace", "Glass Cannon", "Fight Finisher") else 0
        fighter.finishing_instinct = max(1, min(99, round((fighter.striking + fighter.grappling) / 2 + random.randint(-10, 18) + finish_trait)))
        fighter.media_presence = max(1, min(99, round(fighter.popularity * 0.55 + fighter.charisma * 0.35 + fighter.media_heat * 0.7)))
        fighter.sponsor_appeal = max(1, min(99, round(fighter.star_quality * 0.35 + fighter.charisma * 0.25 + fighter.professionalism * 0.25 + fighter.popularity * 0.25)))
        fighter.portrait_bg, fighter.portrait_accent = self.generate_portrait_palette(fighter.name)
        fighter.walk_weight = self.default_walk_weight(fighter)
        fighter.fight_history = fighter.fight_history or []
        fighter.annual_overalls = fighter.annual_overalls or {"2026": fighter.overall}
        fighter.motivation = max(1, min(99, round(75 - max(0, fighter.age - 34) * 3 + fighter.morale * 0.18 + fighter.popularity * 0.12 + random.randint(-10, 12))))
        self.assign_career_goal(fighter)
        fighter.camp_quality = self.gym_quality(fighter.camp)
        fighter.power = max(25, min(99, round(fighter.striking * 0.65 + fighter.chin * 0.2 + random.randint(-10, 18))))
        fighter.takedown_defence = max(25, min(99, round(fighter.wrestling * 0.7 + fighter.cardio * 0.15 + random.randint(-10, 12))))
        fighter.ground_control = max(25, min(99, round((fighter.wrestling + fighter.grappling) / 2 + random.randint(-10, 10))))
        fighter.submissions = max(25, min(99, round(fighter.grappling * 0.82 + random.randint(-12, 14))))
        toughness_trait = 8 if fighter.trait in ("Iron Chin", "Comeback Artist", "Title Mentality") else -8 if fighter.trait == "Glass Cannon" else 0
        fighter.toughness = max(25, min(99, round(fighter.chin * 0.7 + fighter.cardio * 0.2 + random.randint(-8, 12) + toughness_trait)))
        fighter.submission_defence = max(25, min(99, round(fighter.grappling * 0.58 + fighter.wrestling * 0.22 + random.randint(-8, 14))))
        fighter.recovery = max(25, min(99, round(fighter.chin * 0.55 + fighter.toughness * 0.2 + random.randint(-8, 12))))
        fighter.fight_iq = max(25, min(99, round((fighter.cardio + fighter.overall) / 2 + random.randint(-10, 14))))
        self.generate_detailed_skills(fighter)
        self.sync_broad_skills_from_details(fighter)
        # Potential room follows a centred curve. Most entrants receive useful
        # but not elite runway, while both limited prospects and exceptional
        # late bloomers remain possible. The old 62% bottom bucket pulled the
        # entire mature-world average down even when development was working.
        potential_room = max(3, min(20, round(random.gauss(13.5, 3.2))))
        exceptional_ceiling = random.random() < 0.012
        fighter.potential = max(fighter.overall, min(98 if exceptional_ceiling else 96, fighter.overall + potential_room))
        self.assign_career_arc(fighter)
        fighter.contract_months = random.randint(8, 24) if player_owned else 0
        fighter.rank_score = self.rank_value(fighter)

    def builtin_combat_sport_real_roster_data(self):
        return {
            "Boxing": [
                "Floyd Mayweather Jr", "Manny Pacquiao", "Canelo Alvarez", "Terence Crawford", "Oleksandr Usyk",
                "Vasiliy Lomachenko", "Naoya Inoue", "Gennady Golovkin", "Wladimir Klitschko", "Vitali Klitschko",
                "Lennox Lewis", "Roy Jones Jr", "Bernard Hopkins", "Oscar De La Hoya", "Juan Manuel Marquez",
                "Erik Morales", "Marco Antonio Barrera", "Miguel Cotto", "Felix Trinidad", "Shane Mosley",
                "Andre Ward", "Sergey Kovalev", "Artur Beterbiev", "Dmitry Bivol", "Tyson Fury",
                "Anthony Joshua", "Deontay Wilder", "Andy Ruiz Jr", "Zhilei Zhang", "Joseph Parker",
                "Jermell Charlo", "Jermall Charlo", "Errol Spence Jr", "Keith Thurman", "Shawn Porter",
                "Danny Garcia", "Amir Khan", "Kell Brook", "Timothy Bradley", "Devon Alexander",
                "Roman Gonzalez", "Nonito Donaire", "Juan Francisco Estrada", "Srisaket Sor Rungvisai", "Kazuto Ioka",
                "Donnie Nietes", "Mikey Garcia", "Gervonta Davis", "Shakur Stevenson", "Devin Haney",
                # Bare-knuckle history and the modern BKFC scene deepen the
                # otherwise thin boxing circuit. Existing MMA athletes such as
                # Mike Perry, Bec Rawlings and Hector Lombard are deliberately
                # not cloned here.
                "Jem Mace", "John L Sullivan", "Tom Cribb", "Daniel Mendoza", "James Figg",
                "Jack Broughton", "Tom Sayers", "William Bendigo Thompson", "Jem Belcher", "Tom Molineaux",
                "John C Heenan", "Tom Spring", "Ben Caunt", "Jake Kilrain", "Bobby Gunn",
                "Luis Palomino", "Lorenzo Hunt", "Christine Ferea", "Britain Hart", "Arnold Adams",
                "Reggie Barnett Jr", "Joey Beltran", "David Mundell", "Dat Nguyen", "Austin Trout",
                "Paddy Ryan", "John Gentleman Jackson", "Hen Pearce", "Bartley Gorman", "James Deaf Burke",
                "Jem Ward", "Joe Goss", "Tom King", "Peter Jackson", "Mick Terrill", "Kai Stewart",
                "Francesco Ricchi", "Artem Lobov", "Jason Knight", "Thiago Alves", "Alan Belcher", "Shannon Ritch",
            ],
            "Kickboxing": [
                "Ernesto Hoost", "Giorgio Petrosyan", "Semmy Schilt", "Peter Aerts", "Remy Bonjasky",
                "Badr Hari", "Buakaw Banchamek", "Andy Hug", "Ramon Dekkers", "Rob Kaman",
                "Rico Verhoeven", "Tenshin Nasukawa", "Sitthichai Sitsongpeenong", "Superbon Singha Mawynn", "Chingiz Allazov",
                "Artem Levin", "Nieky Holzken", "Masato Kobayashi", "Andy Souwer", "Mike Zambidis",
                "Mirko Cro Cop", "Alexey Ignashov", "Gokhan Saki", "Tyrone Spong", "Jerome Le Banner",
                "Branko Cikatic", "Peter Graham", "Jorina Baars", "Lucia Rijker", "Denise Kielholtz",
                "Jemyma Betrian", "Anissa Meksen", "Petchpanomrung Kiatmookao", "Cedric Doumbe", "Marat Grigorian",
                "Robin van Roosmalen", "Albert Kraus", "Kaoklai Kaennorsing", "Ray Sefo", "Mark Hunt",
                "Francisco Filho", "Kyotaro Fujimoto", "Daniel Ghita", "Hesdy Gerges", "Jamal Ben Saddik",
                "Murthel Groenhart", "Alistair Overeem", "Sam Greco", "Stan Longinidis", "Joseph Valtellini",
            ],
            "Muay Thai": [
                "Samart Payakaroon", "Dieselnoi Chor Thanasukarn", "Saenchai", "Buakaw Banchamek", "Rodtang Jitmuangnon",
                "Nong-O Gaiyanghadao", "Sam-A Gaiyanghadao", "Petchmorakot Petchyindee", "Superbon Singha Mawynn", "Superlek Kiatmuu9",
                "Yodsanklai Fairtex", "Ramon Dekkers", "Apidej Sit-Hirun", "Sagat Petchyindee", "Namsaknoi Yudthagarngamtorn",
                "Namkabuan Nongkeepahuyuth", "Kaensak Sor Ploenjit", "Somrak Khamsing", "Pud Pad Noy Worawoot", "Karuhat Sor Supawan",
                "Jomhod Kiatadisak", "Orono Por Muang Ubon", "Lerdsila Chumpairtour", "Petchboonchu FA Group", "Singdam Kiatmuu9",
                "Anuwat Kaewsamrit", "Yodwicha Por Boonsit", "Sangmanee Sor Tienpo", "Panpayak Jitmuangnon", "Tawanchai PK Saenchai",
                "Seksan Or Kwanmuang", "Liam Harrison", "John Wayne Parr", "Dany Bill", "Coban Lookchaomaesaitong",
                "Sakmongkol Sithchuchok", "Kongtoranee Payakaroon", "Boonlai Sor Thanikul", "Oley Kiatoneway", "Hippy Singmanee",
                "Chamuakpetch Haphalung", "Veeraphol Sahaprom", "Khaosai Galaxy", "Attachai Fairtex", "Petchtanong Petchfergus",
                "Petchdam Petchyindee", "Capitan Petchyindee", "Kulabdam Sor Jor Piek Uthai", "Nadaka Yoshinari", "Somratsamee Manopgym",
            ],
            "Lethwei": [
                "Tun Tun Min", "Dave Leduc", "Saw Nga Man", "Too Too", "Tway Ma Shaung",
                "Soe Lin Oo", "Cyrus Washington", "Lone Chaw", "Shwe Sai", "Tun Lwin Moe",
                "Mite Yine", "Saw Ba Oo", "Wan Chai", "Kyar Ba Nyein", "Phoe Kay",
                "Artur Saladiak", "Sasha Moisa", "Naimjon Tuhtaboyev", "Akitoshi Tamura", "Shunichi Shimizu",
                "Shwe War Tun", "Thway Thit Win Hlaing", "Shwe Du Wun", "Win Tun", "Shan La Tway",
                "Antonio Faria", "Saw Htoo Aung", "Souris Manfredi", "Julija Stoliarenko", "Tha Pyay Nyo",
                "Yan Naing Tun", "Ba Htoo Maung", "Shwe Yar Man", "Thant Zin", "Salai Thang Khwi Shein",
                "Thet Win Aung", "Nguyen Tran Duy Nhat", "Maisha Katz", "Shwe Sin Min",
            ],
            "Wrestling": [
                "Aleksandr Karelin", "Buvaisar Saitiev", "John Smith", "Jordan Burroughs", "Abdulrashid Sadulaev",
                "Mijain Lopez", "Sergei Beloglazov", "Arsen Fadzaev", "Hamid Sourian", "Artur Taymazov",
                "Valentin Yordanov", "Dan Gable", "Cael Sanderson", "Kyle Snyder", "David Taylor",
                "Hassan Yazdani", "Gable Steveson", "Geno Petriashvili", "Taha Akgul", "Rulon Gardner",
                "Bruce Baumgartner", "Makharbek Khadartsev", "Ivan Yarygin", "Yojiro Uetake", "Osamu Watanabe",
                "Levan Tediashvili", "Sushil Kumar", "Bajrang Punia", "Yogeshwar Dutt", "Saori Yoshida",
                "Kaori Icho", "Helen Maroulis", "Adeline Gray", "Tamyra Mensah-Stock", "Iryna Merleni",
                "Aleksandr Medved", "Elbrus Tedeyev", "Besik Kudukhov", "Zaurbek Sidakov", "Roman Vlasov",
                "Frank Chamizo", "Reza Yazdani", "Ghasem Rezaei", "Komeil Ghasemi", "Henry Cejudo",
                "Daniel Cormier", "Yoel Romero", "Ben Askren", "Bo Nickal", "Kenny Monday",
            ],
            "Brazilian Jiu-Jitsu": [
                "Roger Gracie", "Marcelo Garcia", "Marcus Almeida", "Leandro Lo", "Andre Galvao",
                "Gordon Ryan", "Rafael Mendes", "Guilherme Mendes", "Rubens Charles Maciel", "Bruno Malfacine",
                "Roberto Cyborg Abreu", "Rodolfo Vieira", "Alexandre Ribeiro", "Saulo Ribeiro", "Romulo Barral",
                "Bernardo Faria", "Lucas Lepri", "Robson Moura", "Royler Gracie", "Rickson Gracie",
                "Royce Gracie", "Carlos Gracie Jr", "Carlson Gracie", "Rolls Gracie", "Jean Jacques Machado",
                "Rigan Machado", "Vitor Shaolin Ribeiro", "Murilo Bustamante", "Mario Sperry", "Fabio Gurgel",
                "Fernando Terere", "Marcio Feitosa", "Ronaldo Jacare Souza", "Demian Maia", "Kron Gracie",
                "Mikey Musumeci", "Nicholas Meregali", "Felipe Pena", "Kaynan Duarte", "Mica Galvao",
                "Tainan Dalpra", "Craig Jones", "Lachlan Giles", "Garry Tonon", "Eddie Bravo",
                "Keenan Cornelius", "Paulo Miyao", "Joao Miyao", "Gabi Garcia", "Beatriz Mesquita",
            ],
        }

    def combat_sport_real_roster_data(self):
        return self.load_combat_sport_database()

    def combat_sport_region_for_name(self, name, sport):
        region_by_name = {
            "Muhammad Ali": "USA", "Sugar Ray Robinson": "USA", "Joe Louis": "USA", "Floyd Mayweather Jr": "USA",
            "Manny Pacquiao": "Asia", "Roberto Duran": "Latin America", "Julio Cesar Chavez": "Latin America",
            "Canelo Alvarez": "Latin America", "Naoya Inoue": "Japan", "Oleksandr Usyk": "Europe",
            "Ernesto Hoost": "Europe", "Giorgio Petrosyan": "Europe", "Semmy Schilt": "Europe", "Peter Aerts": "Europe",
            "Rico Verhoeven": "Europe", "Buakaw Banchamek": "Asia", "Tenshin Nasukawa": "Japan", "Andy Hug": "Europe",
            "Samart Payakaroon": "Asia", "Dieselnoi Chor Thanasukarn": "Asia", "Saenchai": "Asia", "Rodtang Jitmuangnon": "Asia",
            "Liam Harrison": "UK", "John Wayne Parr": "Oceania", "Dany Bill": "Europe", "Ramon Dekkers": "Europe",
            "Dave Leduc": "Canada", "Cyrus Washington": "USA", "Artur Saladiak": "Europe", "Sasha Moisa": "Europe",
            "Aleksandr Karelin": "Europe", "Jordan Burroughs": "USA", "John Smith": "USA", "Dan Gable": "USA",
            "Cael Sanderson": "USA", "Kyle Snyder": "USA", "David Taylor": "USA", "Henry Cejudo": "USA",
            "Daniel Cormier": "USA", "Yoel Romero": "Latin America", "Ben Askren": "USA", "Bo Nickal": "USA",
            "Roger Gracie": "Brazil", "Marcelo Garcia": "Brazil", "Marcus Almeida": "Brazil", "Leandro Lo": "Brazil",
            "Gordon Ryan": "USA", "Craig Jones": "Oceania", "Lachlan Giles": "Oceania", "Garry Tonon": "USA",
            "Mikey Musumeci": "USA", "Keenan Cornelius": "USA",
        }
        if name in region_by_name:
            return region_by_name[name]
        europe = set("""Oleksandr Usyk|Vasiliy Lomachenko|Gennady Golovkin|Wladimir Klitschko|Vitali Klitschko|Lennox Lewis|Sergey Kovalev|Artur Beterbiev|Dmitry Bivol|Tyson Fury|Anthony Joshua|Amir Khan|Kell Brook|Ernesto Hoost|Giorgio Petrosyan|Semmy Schilt|Peter Aerts|Remy Bonjasky|Badr Hari|Ramon Dekkers|Rob Kaman|Rico Verhoeven|Andy Hug|Chingiz Allazov|Artem Levin|Nieky Holzken|Andy Souwer|Mike Zambidis|Mirko Cro Cop|Alexey Ignashov|Gokhan Saki|Jerome Le Banner|Branko Cikatic|Jorina Baars|Lucia Rijker|Denise Kielholtz|Jemyma Betrian|Anissa Meksen|Cedric Doumbe|Marat Grigorian|Robin van Roosmalen|Albert Kraus|Daniel Ghita|Hesdy Gerges|Jamal Ben Saddik|Murthel Groenhart|Alistair Overeem|Stan Longinidis|Joseph Valtellini|Dany Bill|Artur Saladiak|Sasha Moisa|Aleksandr Karelin|Buvaisar Saitiev|Abdulrashid Sadulaev|Sergei Beloglazov|Arsen Fadzaev|Hamid Sourian|Artur Taymazov|Valentin Yordanov|Hassan Yazdani|Geno Petriashvili|Taha Akgul|Makharbek Khadartsev|Ivan Yarygin|Levan Tediashvili|Iryna Merleni|Aleksandr Medved|Elbrus Tedeyev|Besik Kudukhov|Zaurbek Sidakov|Roman Vlasov|Frank Chamizo|Reza Yazdani|Ghasem Rezaei|Komeil Ghasemi""".split("|"))
        usa = set("""Floyd Mayweather Jr|Terence Crawford|Roy Jones Jr|Bernard Hopkins|Oscar De La Hoya|Shane Mosley|Andre Ward|Deontay Wilder|Andy Ruiz Jr|Jermell Charlo|Jermall Charlo|Errol Spence Jr|Keith Thurman|Shawn Porter|Danny Garcia|Timothy Bradley|Devon Alexander|Mikey Garcia|Gervonta Davis|Shakur Stevenson|Devin Haney|Cyrus Washington|John Smith|Jordan Burroughs|Dan Gable|Cael Sanderson|Kyle Snyder|David Taylor|Gable Steveson|Rulon Gardner|Bruce Baumgartner|Helen Maroulis|Adeline Gray|Tamyra Mensah-Stock|Henry Cejudo|Daniel Cormier|Ben Askren|Bo Nickal|Kenny Monday|Gordon Ryan|Mikey Musumeci|Garry Tonon|Eddie Bravo|Keenan Cornelius""".split("|"))
        japan = set("""Naoya Inoue|Kazuto Ioka|Tenshin Nasukawa|Masato Kobayashi|Kyotaro Fujimoto|Francisco Filho|Kaoklai Kaennorsing|Nadaka Yoshinari|Akitoshi Tamura|Shunichi Shimizu|Yojiro Uetake|Osamu Watanabe|Saori Yoshida|Kaori Icho""".split("|"))
        australia = set("""Joseph Parker|Peter Graham|Tyrone Spong|Ray Sefo|Mark Hunt|Sam Greco|John Wayne Parr|Craig Jones|Lachlan Giles""".split("|"))
        uk = set("""Liam Harrison|Anthony Joshua|Tyson Fury|Lennox Lewis|Amir Khan|Kell Brook""".split("|"))
        asia = set("""Gennady Golovkin|Zhilei Zhang|Nonito Donaire|Srisaket Sor Rungvisai|Donnie Nietes|Buakaw Banchamek|Sitthichai Sitsongpeenong|Superbon Singha Mawynn|Petchpanomrung Kiatmookao|Kaoklai Kaennorsing|Naimjon Tuhtaboyev|Sushil Kumar|Bajrang Punia|Yogeshwar Dutt""".split("|"))
        mexico = set("""Canelo Alvarez|Juan Manuel Marquez|Erik Morales|Marco Antonio Barrera|Andy Ruiz Jr|Juan Francisco Estrada|Roman Gonzalez""".split("|"))
        brazil = {"Francisco Filho"}
        if name in usa:
            return "USA"
        if name in asia:
            return "Asia"
        if name in mexico:
            return "Mexico"
        if name in brazil:
            return "Brazil"
        if name in japan:
            return "Japan"
        if name in australia:
            return "Australia"
        if name in uk:
            return "UK"
        if name in europe:
            return "Europe"
        if sport in ("Muay Thai", "Lethwei", "Kickboxing"):
            return "Europe" if sport == "Kickboxing" else "Asia"
        if sport == "Brazilian Jiu-Jitsu":
            return "Brazil"
        if sport == "Wrestling":
            return "Europe"
        return "USA"

    def combat_sport_weight_ladder(self, sport, gender="Male"):
        """Return the canonical ladder for a child combat sport.

        Lethwei retains its own historic divisions even though those athletes
        appear inside the linked Muay Thai world.
        """
        ladders = COMBAT_SPORT_WEIGHT_CLASSES.get(sport, {})
        return list(ladders.get(gender) or ladders.get("Male") or ())

    def combat_sport_weight_limit(self, sport, division, gender="Male"):
        return next((limit for label, limit in self.combat_sport_weight_ladder(sport, gender) if label == division), None)

    def combat_sport_mma_equivalent(self, sport, division, gender="Male"):
        """Keep a valid MMA division ready for athletes who later cross over."""
        limit = self.combat_sport_weight_limit(sport, division, gender)
        if limit is None:
            return "Heavyweight"
        return min(WEIGHTS, key=lambda weight: abs(WEIGHT_LIMITS[weight] - limit))

    def combat_sport_competition_class(self, sport, fighter):
        """Translate an athlete's native class onto the circuit's ladder.

        This mainly lets Lethwei athletes keep an authentic native class while
        being ranked and matched in the shared Muay Thai circuit.
        """
        source_sport = getattr(fighter, "primary_discipline", sport)
        native = getattr(fighter, "sport_weight_class", "") or self.infer_combat_sport_weight_class(source_sport, fighter)
        if source_sport == sport and native in {label for label, _ in self.combat_sport_weight_ladder(sport, fighter.gender)}:
            return native
        source_limit = self.combat_sport_weight_limit(source_sport, native, fighter.gender)
        ladder = self.combat_sport_weight_ladder(sport, fighter.gender)
        if not ladder:
            return native or fighter.weight
        if source_limit is None:
            return ladder[-1][0]
        return next((label for label, limit in ladder if limit is None or source_limit <= limit), ladder[-1][0])

    def infer_combat_sport_weight_class(self, sport, fighter):
        ladder = self.combat_sport_weight_ladder(sport, fighter.gender)
        if not ladder:
            return fighter.weight
        current = getattr(fighter, "sport_weight_class", "")
        valid = {label for label, _limit in ladder}
        if current in valid:
            return current
        seed_divisions = getattr(self, "combat_sport_seed_divisions", {}) or {}
        known = seed_divisions.get(getattr(fighter, "primary_discipline", sport), {}).get(fighter.name)
        if not known:
            known = COMBAT_SPORT_REAL_DIVISIONS.get(getattr(fighter, "primary_discipline", sport), {}).get(fighter.name)
        if known not in valid:
            known = seed_divisions.get(sport, {}).get(fighter.name) or COMBAT_SPORT_REAL_DIVISIONS.get(sport, {}).get(fighter.name)
        if known in valid:
            return known
        # Old saves only have an MMA division.  Treat that former limit as the
        # athlete's competition weight and move it onto the first legal class.
        target = WEIGHT_LIMITS.get(fighter.weight, getattr(fighter, "walk_weight", 170) or 170)
        return next((label for label, limit in ladder if limit is None or target <= limit), ladder[-1][0])

    def assign_combat_sport_weight(self, sport, fighter, division="", reset_walk_weight=False):
        ladder = self.combat_sport_weight_ladder(sport, fighter.gender)
        valid = {label for label, _limit in ladder}
        if division not in valid:
            division = self.infer_combat_sport_weight_class(sport, fighter)
        fighter.sport_weight_class = division
        fighter.weight = self.combat_sport_mma_equivalent(sport, division, fighter.gender)
        limit = self.combat_sport_weight_limit(sport, division, fighter.gender)
        if reset_walk_weight or not getattr(fighter, "walk_weight", 0):
            seed = sum((index + 1) * ord(char) for index, char in enumerate(f"{sport}:{fighter.name}:{division}"))
            if limit is None:
                base = max(210, WEIGHT_LIMITS.get(fighter.weight, 225))
                fighter.walk_weight = min(295, base + 5 + seed % 24)
            else:
                spread = max(3, round(limit * (0.035 if sport == "Wrestling" else 0.055)))
                fighter.walk_weight = min(295, limit + 2 + seed % (spread + 1))
        return division

    def combat_sport_seed_profile(self, sport, name, index=0):
        profiles = getattr(self, "combat_sport_seed_profiles", {}) or {}
        profile = profiles.get(sport, {}).get(name)
        if isinstance(profile, dict):
            return profile
        builtin = build_real_sport_profiles(self.builtin_combat_sport_real_roster_data())
        return builtin.get(sport, {}).get(name) or build_fallback_sport_profile(sport, name, index=index)

    def stable_sport_skill_offset(self, sport, name, key):
        seed = sum((index + 5) * ord(char) for index, char in enumerate(f"{sport}:{name}:{key}"))
        return seed % 5 - 2

    def apply_real_combat_sport_profile(self, fighter, sport, profile, preserve_career=False):
        """Apply one deterministic, editable child-sport athlete profile.

        Existing careers keep their dynamic age, ledger, popularity, employer,
        health and history. Their formerly randomized combat identity is repaired
        once, while a new universe receives the complete prime profile.
        """
        def profile_int(key, default, low=1, high=99):
            try:
                value = int(profile.get(key, default))
            except (TypeError, ValueError):
                value = int(default)
            return max(low, min(high, value))

        rating = profile_int("rating", 75)
        group_bases = {
            "Boxing": {"Standing": rating, "Ground": rating - 29, "Wrestling": rating - 25, "Muay Thai Clinch": rating - 14, "Mental": rating - 3, "Physical": rating - 4},
            "Kickboxing": {"Standing": rating, "Ground": rating - 25, "Wrestling": rating - 21, "Muay Thai Clinch": rating - 8, "Mental": rating - 3, "Physical": rating - 3},
            "Muay Thai": {"Standing": rating - 1, "Ground": rating - 24, "Wrestling": rating - 18, "Muay Thai Clinch": rating + 1, "Mental": rating - 3, "Physical": rating - 2},
            "Lethwei": {"Standing": rating - 1, "Ground": rating - 25, "Wrestling": rating - 19, "Muay Thai Clinch": rating, "Mental": rating - 3, "Physical": rating},
            "Wrestling": {"Standing": rating - 29, "Ground": rating - 7, "Wrestling": rating + 1, "Muay Thai Clinch": rating - 3, "Mental": rating - 3, "Physical": rating - 1},
            "Brazilian Jiu-Jitsu": {"Standing": rating - 31, "Ground": rating + 1, "Wrestling": rating - 8, "Muay Thai Clinch": rating - 11, "Mental": rating - 3, "Physical": rating - 3},
        }.get(sport, {group: rating - 4 for group in DETAILED_SKILL_GROUPS})
        details = {}
        for group, keys in DETAILED_SKILL_GROUPS.items():
            base = group_bases.get(group, rating - 4)
            for key in keys:
                value = base + self.stable_sport_skill_offset(sport, fighter.name, key)
                if sport == "Boxing" and key in ("high_kick_power", "high_kick_technique", "high_kick_speed", "low_kick_power", "low_kick_technique", "low_kick_speed", "creative_kicks", "kick_defence"):
                    value -= 24
                if sport in ("Wrestling", "Brazilian Jiu-Jitsu") and key in ("high_kick_power", "high_kick_technique", "low_kick_power", "low_kick_technique", "creative_kicks"):
                    value -= 8
                details[key] = max(25, min(99, round(value)))
        modifiers = profile.get("skill_mods", {})
        modifiers = modifiers if isinstance(modifiers, dict) else {}
        for key, adjustment in modifiers.items():
            if key in details:
                try:
                    details[key] = max(25, min(99, details[key] + int(adjustment)))
                except (TypeError, ValueError):
                    continue
        fighter.detailed_skills = details
        fighter.style = profile.get("style", fighter.style) if profile.get("style") in STYLES else fighter.style
        fighter.trait = profile.get("trait", fighter.trait) if profile.get("trait") in TRAITS else fighter.trait
        fighter.behaviour = profile.get("behaviour", fighter.behaviour) if profile.get("behaviour") in BEHAVIOURS else fighter.behaviour
        fighter.stance = profile.get("stance", fighter.stance) if profile.get("stance") in ("Orthodox", "Southpaw", "Switch") else fighter.stance
        fighter.career_archetype = profile.get("career_archetype", "Balanced Development")
        self.sync_broad_skills_from_details(fighter)
        if sport in ("Boxing", "Kickboxing", "Muay Thai", "Lethwei"):
            fighter.striking = rating
        elif sport == "Wrestling":
            fighter.wrestling = rating
        elif sport == "Brazilian Jiu-Jitsu":
            fighter.grappling = rating
        fighter.finishing_instinct = profile_int("finishing_instinct", fighter.finishing_instinct)
        if not preserve_career:
            fighter.age = profile_int("prime_age", fighter.age, 18, 45)
            fighter.record_w = profile_int("record_w", fighter.record_w, 0, 999)
            fighter.record_l = profile_int("record_l", fighter.record_l, 0, 500)
            fighter.record_d = profile_int("record_d", fighter.record_d, 0, 250)
            fighter.popularity = profile_int("popularity", fighter.popularity)
            for key in ("star_quality", "charisma", "professionalism", "media_presence", "sponsor_appeal", "injury_proneness"):
                if key in profile:
                    setattr(fighter, key, profile_int(key, getattr(fighter, key)))
        fighter.prime_start = profile_int("prime_start", max(21, fighter.age - 4), 18, 39)
        fighter.prime_end = max(fighter.prime_start + 3, profile_int("prime_end", fighter.prime_start + 8, 21, 45))
        fighter.career_arc_version = max(2, getattr(fighter, "career_arc_version", 0))
        fighter.sport_profile_version = max(SPORT_PROFILE_VERSION, profile_int("version", SPORT_PROFILE_VERSION, 1, 999))
        fighter.primary_discipline = sport
        fighter.combat_background = sport
        fighter.multi_sport_records = dict(fighter.multi_sport_records or {})
        fighter.multi_sport_records[sport] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
        if sport == "Lethwei":
            fighter.multi_sport_records.setdefault("Muay Thai", "0-0-0")
        fighter.potential = max(fighter.overall, min(99, rating + (1 if fighter.age >= fighter.prime_start else 4)))
        fighter.annual_overalls = dict(fighter.annual_overalls or {})
        fighter.annual_overalls.setdefault("2026", fighter.overall)
        fighter.rank_score = self.rank_value(fighter)
        return fighter

    def create_real_combat_sport_athlete(self, name, sport, promotion, index):
        women = {
            "Jorina Baars", "Lucia Rijker", "Denise Kielholtz", "Jemyma Betrian", "Anissa Meksen",
            "Christine Ferea", "Britain Hart", "Souris Manfredi", "Julija Stoliarenko", "Maisha Katz", "Shwe Sin Min",
            "Saori Yoshida", "Kaori Icho", "Helen Maroulis", "Adeline Gray", "Tamyra Mensah-Stock",
            "Iryna Merleni", "Gabi Garcia", "Beatriz Mesquita", "Somratsamee Manopgym",
        }
        style_by_sport = {
            "Boxing": "Boxer",
            "Kickboxing": "Kickboxer",
            "Muay Thai": "Muay Thai",
            "Lethwei": "Muay Thai",
            "Wrestling": "Wrestler",
            "Brazilian Jiu-Jitsu": "BJJ",
        }
        profile = self.combat_sport_seed_profile(sport, name, index)
        rating = max(1, min(99, int(profile.get("rating", 75))))
        age = int(profile.get("prime_age", 28))
        wins = int(profile.get("record_w", 0))
        losses = int(profile.get("record_l", 0))
        draws = int(profile.get("record_d", 0))
        region = self.combat_sport_region_for_name(name, sport)
        striking = rating
        wrestling = max(55, rating - 13)
        grappling = max(55, rating - 13)
        if sport == "Boxing":
            wrestling, grappling = max(52, rating - 20), max(48, rating - 24)
        elif sport in ("Kickboxing", "Muay Thai", "Lethwei"):
            wrestling, grappling = max(56, rating - 16), max(52, rating - 20)
        elif sport == "Wrestling":
            striking, wrestling, grappling = max(55, rating - 18), rating, max(62, rating - 8)
        elif sport == "Brazilian Jiu-Jitsu":
            striking, wrestling, grappling = max(52, rating - 22), max(64, rating - 8), rating
        fighter = Fighter(
            name=name,
            # The exact child-sport class is assigned below.  ``weight`` stays
            # as its MMA equivalent so a later crossover is immediately valid.
            weight="Welterweight",
            age=age,
            record_w=wins,
            record_l=losses,
            record_d=draws,
            striking=max(25, min(99, striking)),
            wrestling=max(25, min(99, wrestling)),
            grappling=max(25, min(99, grappling)),
            cardio=max(45, min(99, rating - 2)),
            chin=max(45, min(99, rating - 3)),
            popularity=max(18, min(99, int(profile.get("popularity", rating)))),
            momentum=2,
            morale=78,
            purse=max(4000, (rating - 45) * 1800),
            gender="Female" if name in women else "Male",
            region=region,
            nationality=self.infer_nationality(name, region),
            style=style_by_sport.get(sport, "Well-Rounded"),
            trait=profile.get("trait", "Technical Learner"),
            behaviour=profile.get("behaviour", "Dynamic Attacker"),
            stance=profile.get("stance", "Orthodox"),
            camp="Independent",
            primary_discipline=sport,
            combat_background=sport,
            sport_employer=promotion,
            multi_sport_records={sport: f"{wins}-{losses}-{draws}"},
            crossover_history=[],
            contract_months=0,
            exclusive=False,
            contract_type="Sport Contract",
            star_quality=int(profile.get("star_quality", rating)),
            charisma=int(profile.get("charisma", max(20, rating - 8))),
            professionalism=int(profile.get("professionalism", 78)),
            media_presence=int(profile.get("media_presence", max(15, rating - 4))),
            sponsor_appeal=int(profile.get("sponsor_appeal", max(15, rating - 3))),
            finishing_instinct=int(profile.get("finishing_instinct", rating)),
            injury_proneness=int(profile.get("injury_proneness", 18)),
        )
        if sport == "Lethwei":
            fighter.power = min(99, rating + 5)
            fighter.toughness = min(99, rating + 7)
            fighter.multi_sport_records["Muay Thai"] = "0-0-0"
        self.assign_combat_sport_weight(sport, fighter, reset_walk_weight=True)
        fighter.portrait_bg, fighter.portrait_accent = self.generate_portrait_palette(fighter.name)
        fighter.fight_history = []
        fighter.annual_overalls = {}
        fighter.motivation = 82
        fighter.camp_quality = self.gym_quality(fighter.camp)
        fighter = self.apply_real_combat_sport_profile(fighter, sport, profile, preserve_career=False)
        if sport == "Boxing" and name in {
            "Jem Mace", "John L Sullivan", "Tom Cribb", "Daniel Mendoza", "James Figg", "Jack Broughton",
            "Tom Sayers", "William Bendigo Thompson", "Jem Belcher", "Tom Molineaux", "John C Heenan",
            "Tom Spring", "Ben Caunt", "Jake Kilrain", "Bobby Gunn", "Luis Palomino", "Lorenzo Hunt",
            "Christine Ferea", "Britain Hart", "Arnold Adams", "Reggie Barnett Jr", "Joey Beltran",
            "David Mundell", "Dat Nguyen", "Austin Trout", "Paddy Ryan", "John Gentleman Jackson", "Hen Pearce",
            "Bartley Gorman", "James Deaf Burke", "Jem Ward", "Joe Goss", "Tom King", "Peter Jackson",
            "Mick Terrill", "Kai Stewart", "Francesco Ricchi", "Artem Lobov", "Jason Knight", "Thiago Alves",
            "Alan Belcher", "Shannon Ritch",
        }:
            fighter.combat_background = "Bare Knuckle"
        return fighter

    def seed_combat_sport_worlds(self):
        worlds = {}
        profiles = (
            ("Boxing", "Global Boxing Championship"),
            ("Kickboxing", "World Kickboxing League"),
            ("Muay Thai", "International Muay Thai Union"),
            ("Wrestling", "World Wrestling Circuit"),
            ("Brazilian Jiu-Jitsu", "Global BJJ Federation"),
        )
        real_rosters = self.combat_sport_real_roster_data()
        for sport, promotion in profiles:
            roster = [self.create_real_combat_sport_athlete(name, sport, promotion, index) for index, name in enumerate(real_rosters.get(sport, []))]
            if sport == "Muay Thai":
                start = len(roster)
                roster.extend(
                    self.create_real_combat_sport_athlete(name, "Lethwei", promotion, start + index)
                    for index, name in enumerate(real_rosters.get("Lethwei", []))
                )
            ranked = sorted(roster, key=lambda fighter: (fighter.overall, fighter.popularity, fighter.record_w - fighter.record_l), reverse=True)
            division_groups = {}
            for fighter in ranked:
                division = self.combat_sport_competition_class(sport, fighter)
                division_groups.setdefault(f"{fighter.gender}|{division}", []).append(fighter)
            rankings_by_division = {key: [fighter.name for fighter in fighters[:10]] for key, fighters in division_groups.items()}
            titles = {key: fighters[0].name for key, fighters in division_groups.items() if len(fighters) >= 2}
            worlds[sport] = {
                "promotion": promotion,
                "roster": roster,
                "rankings": [fighter.name for fighter in ranked[:15]],
                "champion": ranked[0].name if ranked else "",
                "titles": titles,
                "title_history": {},
                "rankings_by_division": rankings_by_division,
                "titles_initialized": True,
                "events": 0,
                "records": {},
                "record_book": {},
                "season_stats": {},
                "awards": [],
                "hall_of_fame": [],
                "media": [f"{promotion} announces a real-name {sport} roster built around {ranked[0].name}." if ranked else f"{promotion} launches."],
                "prospects": [],
                "event_history": [],
                "strategy": random.choice(["Champion Showcase", "Prospect Rotation", "Deep Roster", "Merit Ladder"]),
                "cash": {"Boxing": 8_000_000, "Kickboxing": 4_500_000, "Muay Thai": 3_800_000, "Wrestling": 3_000_000, "Brazilian Jiu-Jitsu": 2_800_000}.get(sport, 3_000_000),
                "reputation": {"Boxing": 76, "Kickboxing": 68, "Muay Thai": 72, "Wrestling": 66, "Brazilian Jiu-Jitsu": 65}.get(sport, 62),
                "stability": 72,
                "finance_history": [],
                "starting_roster_size": len(roster),
                "roster_target": len(roster) * COMBAT_SPORT_ROSTER_TARGET_MULTIPLIER,
            }
        return worlds

    def repair_combat_sport_worlds(self):
        seeded_worlds = self.seed_combat_sport_worlds()
        current_worlds = getattr(self, "combat_sport_worlds", {}) or {}
        for sport, seeded_world in seeded_worlds.items():
            if sport not in current_worlds:
                current_worlds[sport] = seeded_world
                continue
            world = current_worlds[sport]
            promotion = seeded_world.get("promotion", "")
            seeded_by_name = {fighter.name: fighter for fighter in seeded_world.get("roster", [])}
            repaired_roster = []
            seen = set()
            for fighter in world.get("roster", []):
                if not isinstance(fighter, Fighter):
                    fighter = Fighter(**fighter)
                if fighter.name in seen:
                    continue
                self.ensure_detailed_skills(fighter)
                self.ensure_fighter_business_stats(fighter)
                native_sport = getattr(fighter, "primary_discipline", sport)
                if native_sport not in COMBAT_SPORT_WEIGHT_CLASSES:
                    native_sport = sport
                profiles = getattr(self, "combat_sport_seed_profiles", {}) or {}
                profile = profiles.get(native_sport, {}).get(fighter.name)
                if isinstance(profile, dict) and getattr(fighter, "sport_profile_version", 0) < int(profile.get("version", SPORT_PROFILE_VERSION)):
                    preserve_career = bool(
                        getattr(fighter, "fight_history", None)
                        or getattr(fighter, "last_fight_month", 0)
                        or getattr(self, "month", 1) > 1
                    )
                    self.apply_real_combat_sport_profile(fighter, native_sport, profile, preserve_career=preserve_career)
                # Older saves predate sport_weight_class and retain an MMA
                # placeholder such as Bantamweight/Welterweight. Correct every
                # non-MMA athlete during load, not only after their circuit UI
                # has been opened. Real database classes always take priority.
                expected = profiles.get(native_sport, {}).get(fighter.name, {}).get("weight_class", "")
                if not expected:
                    expected = (getattr(self, "combat_sport_seed_divisions", {}) or {}).get(native_sport, {}).get(fighter.name, "")
                if not expected:
                    expected = COMBAT_SPORT_REAL_DIVISIONS.get(native_sport, {}).get(fighter.name, "")
                valid_classes = {label for label, _limit in self.combat_sport_weight_ladder(native_sport, fighter.gender)}
                current = getattr(fighter, "sport_weight_class", "")
                if current not in valid_classes or (expected and current != expected):
                    self.assign_combat_sport_weight(native_sport, fighter, expected, reset_walk_weight=True)
                else:
                    fighter.weight = self.combat_sport_mma_equivalent(native_sport, current, fighter.gender)
                repaired_roster.append(fighter)
                seen.add(fighter.name)
            for name, fighter in seeded_by_name.items():
                if name not in seen:
                    repaired_roster.append(fighter)
                    seen.add(name)
            ranked = sorted(repaired_roster, key=lambda fighter: (fighter.overall, fighter.popularity, fighter.record_w - fighter.record_l), reverse=True)
            world["promotion"] = promotion
            world["roster"] = repaired_roster
            world["rankings"] = [fighter.name for fighter in ranked[:15]]
            if world.get("champion") not in seen:
                world["champion"] = ranked[0].name if ranked else ""
            for key, value in {
                "events": 0, "records": {}, "record_book": {}, "season_stats": {}, "titles": {}, "title_history": {},
                "rankings_by_division": {}, "awards": [], "hall_of_fame": [], "media": [], "prospects": [],
                "event_history": [], "finance_history": [], "cash": seeded_world.get("cash", 3_000_000),
                "reputation": seeded_world.get("reputation", 62), "stability": 72,
                "starting_roster_size": len(seeded_world.get("roster", [])), "strategy": "Merit Ladder",
            }.items():
                world.setdefault(key, value if not isinstance(value, (list, dict)) else value.copy())
            baseline = max(36, int(world.get("starting_roster_size", len(seeded_world.get("roster", [])) or 36)))
            world["roster_target"] = max(
                int(world.get("roster_target", 0) or 0),
                baseline * COMBAT_SPORT_ROSTER_TARGET_MULTIPLIER,
            )
            world.setdefault("titles_initialized", bool(world.get("titles")))
        self.combat_sport_worlds = current_worlds

    def assign_career_arc(self, fighter):
        """Give every fighter an individual career curve instead of a shared age cliff."""
        conditioning = fighter.detailed_skills.get("conditioning", fighter.cardio) if fighter.detailed_skills else fighter.cardio
        resilience = fighter.detailed_skills.get("resilience", fighter.toughness) if fighter.detailed_skills else fighter.toughness
        dedication = fighter.detailed_skills.get("dedication", fighter.professionalism) if fighter.detailed_skills else fighter.professionalism
        durable_style = fighter.style in ("Wrestler", "Freestyle Wrestler", "Catch Wrestler", "BJJ", "Grappler", "Submission Grappler", "Sambo", "Judo")
        archetype = getattr(fighter, "career_archetype", "")
        if archetype not in ("Early Maturation", "Balanced Development", "Late Maturation", "Durable Career"):
            archetype = random.choices(
                ["Early Maturation", "Balanced Development", "Late Maturation", "Durable Career"],
                weights=[16, 53, 17, 14],
                k=1,
            )[0]
        fighter.career_archetype = archetype
        late_bonus = 2 if archetype in ("Late Maturation", "Durable Career") else 0
        early_penalty = 2 if archetype == "Early Maturation" else 0
        # A normal professional profile previously added roughly six years here,
        # keeping balanced fighters in their prime until about age 38.  A gentler
        # scale preserves genuine durability without making late-career growth the
        # default across the whole world.
        longevity = round((conditioning + resilience + dedication + fighter.professionalism) / 70)
        fighter.prime_start = max(22, min(29, 25 + random.randint(-2, 2) - (1 if archetype == "Early Maturation" else 0) + (1 if archetype == "Late Maturation" else 0)))
        fighter.prime_end = max(
            fighter.prime_start + 4,
            min(40, 31 + random.randint(-2, 3) + longevity + (1 if durable_style else 0) + late_bonus - early_penalty),
        )
        fighter.career_arc_version = 2

    def generate_detailed_skills(self, fighter):
        if fighter.detailed_skills:
            return
        base_map = {}
        for key in STANDING_SKILLS:
            base_map[key] = self.skill_noise(fighter.striking)
        for key in GROUND_SKILLS:
            base_map[key] = self.skill_noise(fighter.grappling)
        for key in WRESTLING_SKILLS:
            base_map[key] = self.skill_noise(fighter.wrestling)
        for key in CLINCH_SKILLS:
            base_map[key] = self.skill_noise(round((fighter.wrestling + fighter.striking) / 2))
        for key in MENTAL_SKILLS:
            base_map[key] = self.skill_noise(round((fighter.fight_iq + fighter.morale) / 2))
        for key in PHYSICAL_SKILLS:
            base_map[key] = self.skill_noise(round((fighter.cardio + fighter.chin) / 2))
        if fighter.style in ("Boxer", "Kickboxer", "Dutch Kickboxer", "Karate", "Taekwondo", "Sanda", "Muay Thai"):
            for key in ("footwork", "punch_technique", "hand_speed", "kick_defence"):
                base_map[key] = min(99, base_map[key] + random.randint(4, 12))
        if fighter.style in ("Wrestler", "Freestyle Wrestler", "Catch Wrestler", "Sambo"):
            for key in ("takedowns", "takedown_setup", "sprawl", "chain_wrestling", "cage_wrestling"):
                base_map[key] = min(99, base_map[key] + random.randint(5, 14))
        if fighter.style in ("BJJ", "Luta Livre", "Submission Grappler", "Sambo", "Grappler"):
            for key in ("submission_attack", "submission_defence_detail", "guard_work", "back_control"):
                base_map[key] = min(99, base_map[key] + random.randint(5, 14))
        fighter.detailed_skills = base_map

    def skill_noise(self, base):
        return max(1, min(99, round(base + random.randint(-14, 14) + random.random())))

    def sync_broad_skills_from_details(self, fighter):
        skills = fighter.detailed_skills or {}
        def avg(keys):
            return round(sum(skills.get(key, 50) for key in keys) / len(keys))
        fighter.striking = avg(STANDING_SKILLS)
        fighter.wrestling = avg(WRESTLING_SKILLS)
        fighter.grappling = avg(GROUND_SKILLS)
        fighter.cardio = round((skills.get("conditioning", fighter.cardio) + skills.get("resilience", fighter.cardio) + skills.get("dedication", fighter.cardio)) / 3)
        fighter.chin = round((skills.get("chin_strength", fighter.chin) + skills.get("stun_recovery", fighter.recovery) + skills.get("resilience", fighter.toughness)) / 3)
        fighter.power = round((skills.get("punch_power", fighter.power) + skills.get("high_kick_power", fighter.power) + skills.get("strength", fighter.power)) / 3)
        fighter.takedown_defence = round((skills.get("takedown_defence_detail", fighter.takedown_defence) + skills.get("sprawl", fighter.takedown_defence) + skills.get("get_ups", fighter.takedown_defence)) / 3)
        fighter.ground_control = round((skills.get("top_control", fighter.ground_control) + skills.get("positional_ability", fighter.ground_control) + skills.get("ride_control", fighter.ground_control)) / 3)
        fighter.submissions = round((skills.get("submission_attack", fighter.submissions) + skills.get("leg_locks", fighter.submissions) + skills.get("back_control", fighter.submissions)) / 3)
        fighter.submission_defence = round((skills.get("submission_defence_detail", fighter.submission_defence) + skills.get("guard_work", fighter.submission_defence)) / 2)
        fighter.recovery = round((skills.get("stun_recovery", fighter.recovery) + skills.get("composure", fighter.fight_iq)) / 2)
        fighter.toughness = round((skills.get("resilience", fighter.toughness) + skills.get("chin_strength", fighter.chin)) / 2)
        fighter.fight_iq = round((skills.get("adaptability", fighter.fight_iq) + skills.get("composure", fighter.fight_iq) + skills.get("discipline", fighter.fight_iq)) / 3)

    def fighter_signature_detailed_skills(self, fighter):
        """Return the small set of techniques that define a fighter's style."""
        signatures = {
            "Boxer": ("punch_power", "punch_technique", "hand_speed", "head_movement"),
            "Kickboxer": ("high_kick_power", "high_kick_technique", "low_kick_technique", "kick_defence"),
            "Dutch Kickboxer": ("punch_technique", "low_kick_power", "low_kick_technique", "guard_defence"),
            "Karate": ("footwork", "high_kick_speed", "creative_kicks", "head_movement"),
            "Taekwondo": ("high_kick_technique", "high_kick_speed", "creative_kicks", "footwork"),
            "Sanda": ("creative_kicks", "clinch_takedowns", "throws", "footwork"),
            "Muay Thai": ("knees", "elbows", "thai_plum", "low_kick_power"),
            "Wrestler": ("takedowns", "takedown_setup", "chain_wrestling", "sprawl"),
            "Freestyle Wrestler": ("takedown_speed", "chain_wrestling", "scrambles", "sprawl"),
            "Catch Wrestler": ("chain_wrestling", "ride_control", "submission_attack", "top_control"),
            "BJJ": ("submission_attack", "submission_defence_detail", "guard_work", "back_control"),
            "Submission Grappler": ("submission_attack", "transitions", "back_control", "leg_locks"),
            "Sambo": ("takedowns", "throws", "submission_attack", "leg_locks"),
            "Judo": ("throws", "clinch_takedowns", "top_control", "positional_ability"),
            "Grappler": ("top_control", "submission_attack", "transitions", "scrambles"),
            "Luta Livre": ("leg_locks", "submission_attack", "scrambles", "top_control"),
        }
        return set(signatures.get(getattr(fighter, "style", ""), ("adaptability", "conditioning")))

    @staticmethod
    def detailed_group_statistics(values):
        if not values:
            return 0.0, 0.0
        mean = sum(values) / len(values)
        deviation = (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5
        return mean, deviation

    def rebalance_saturated_detailed_skills(self, fighter, max_overall_drop=2):
        """Restore variation to old profiles whose entire skill groups hit the cap."""
        self.ensure_detailed_skills(fighter)
        details = fighter.detailed_skills
        before_overall = fighter.overall
        signature_keys = self.fighter_signature_detailed_skills(fighter)
        fixed_keys = {"reach", "natural_size"}
        repaired_groups = []
        changed_keys = set()
        original = dict(details)
        technical_groups = {"Standing", "Ground", "Wrestling", "Muay Thai Clinch"}

        style_group = {
            "Boxer": "Standing", "Kickboxer": "Standing", "Dutch Kickboxer": "Standing",
            "Karate": "Standing", "Taekwondo": "Standing", "Sanda": "Standing",
            "Muay Thai": "Muay Thai Clinch", "Wrestler": "Wrestling",
            "Freestyle Wrestler": "Wrestling", "Catch Wrestler": "Wrestling", "Judo": "Wrestling",
            "BJJ": "Ground", "Luta Livre": "Ground", "Submission Grappler": "Ground",
            "Grappler": "Ground", "Sambo": "Ground",
        }.get(getattr(fighter, "style", ""), "")

        for group_name, keys in DETAILED_SKILL_GROUPS.items():
            values = [details.get(key, 50) for key in keys]
            mean, deviation = self.detailed_group_statistics(values)
            capped = sum(value >= 98 for value in values)
            saturated = capped >= max(4, round(len(keys) * 0.45)) or (mean >= 92 and deviation <= 2.25)
            if not saturated:
                continue
            signature_group = group_name == style_group
            if group_name in technical_groups:
                target_ceiling = min(96, before_overall + (6 if signature_group else 3))
            else:
                target_ceiling = min(95, before_overall + 4)
            target_mean = min(mean, max(72, target_ceiling))
            mutable = [key for key in keys if key not in fixed_keys]
            if not mutable:
                continue
            seed = sum((index + 1) * ord(char) for index, char in enumerate(f"{fighter.fighter_id}:{group_name}"))
            proposed = {}
            for index, key in enumerate(mutable):
                old_value = details.get(key, 50)
                inherited_shape = (old_value - mean) * 0.45
                jitter = ((seed + index * 17) % 7) - 3
                signature_bonus = 2 if key in signature_keys else 0
                proposed[key] = max(25, min(99, round(target_mean + inherited_shape + jitter + signature_bonus)))

            fixed_total = sum(details.get(key, 50) for key in keys if key not in mutable)
            desired_total = round(target_mean * len(keys))
            mutable_target = max(len(mutable) * 25, min(len(mutable) * 99, desired_total - fixed_total))
            difference = mutable_target - sum(proposed.values())
            order = sorted(mutable, key=lambda key: (key not in signature_keys, proposed[key], key))
            cursor = 0
            while difference and order and cursor < len(order) * 100:
                key = order[cursor % len(order)]
                step = 1 if difference > 0 else -1
                if 25 <= proposed[key] + step <= 99:
                    proposed[key] += step
                    difference -= step
                cursor += 1
            for key, value in proposed.items():
                if value != details.get(key, 50):
                    details[key] = value
                    changed_keys.add(key)
            repaired_groups.append(group_name)

        if not repaired_groups:
            return {"fighter": fighter.name, "groups": [], "changed": 0, "before": before_overall, "after": before_overall}

        self.sync_broad_skills_from_details(fighter)
        minimum_overall = max(1, before_overall - max(0, int(max_overall_drop)))
        # Restore a little ability if several inflated groups were corrected at
        # once. This bounds migration impact without flattening a whole tab again.
        restoration_order = sorted(changed_keys, key=lambda key: (key not in signature_keys, details.get(key, 50), key))
        cursor = 0
        while fighter.overall < minimum_overall and restoration_order and cursor < len(restoration_order) * 120:
            key = restoration_order[cursor % len(restoration_order)]
            if details.get(key, 50) < 99:
                details[key] += 1
                self.sync_broad_skills_from_details(fighter)
            cursor += 1
        return {
            "fighter": fighter.name, "groups": repaired_groups, "changed": len(changed_keys),
            "before": before_overall, "after": fighter.overall,
            "original_capped": sum(value >= 98 for value in original.values()),
            "new_capped": sum(value >= 98 for value in details.values()),
        }

    def seed_relationships(self, fighters):
        by_weight = {}
        for fighter in fighters:
            by_weight.setdefault(fighter.weight, []).append(fighter)
        for division in by_weight.values():
            random.shuffle(division)
            for index, fighter in enumerate(division):
                if len(division) > 1 and random.random() < 0.38:
                    rival = division[(index + 1) % len(division)]
                    fighter.rival = rival.name
                    fighter.rivalry_origin = "Pre-existing divisional rivalry"
                    fighter.rivalry_heat = random.randint(18, 46)
                if len(division) > 2 and random.random() < 0.25:
                    fighter.friend = division[(index + 2) % len(division)].name

    def generated_name_parts(self, gender, region=None):
        pool = REGIONAL_NAME_POOLS.get(region or "", {})
        first_pool = pool.get("female" if gender == "Female" else "male") or (FEMALE_FIRST_NAMES if gender == "Female" else FIRST_NAMES)
        last_pool = pool.get("last") or LAST_NAMES
        return random.choice(first_pool), random.choice(last_pool)

    def create_generated_fighter(self, min_pop=6, max_pop=45, min_skill=45, max_skill=82, weight=None, gender=None, region=None, apply_entry_balance=True, age_override=None, pre_universe=None):
        # The world deliberately creates more men than women. Female divisions
        # remain healthy, but a century simulation should not drift to 50/50
        # solely because the depth-repair routines create equal buckets.
        gender = gender or ("Female" if random.random() < 0.18 else "Male")
        market_region = region if region in REGIONS else random.choice(REGION_GENERATION_POOL)
        birth_region = self.weighted_birth_region(market_region)
        first, last = self.generated_name_parts(gender, birth_region)
        name = self.unique_generated_name(first, last, gender=gender)
        # New entrants are predominantly prospects. Established veterans should
        # emerge through records and regional careers, not every generated name.
        age = (max(18, min(45, int(age_override))) if age_override is not None else
               random.choices(range(18, 34), weights=[11, 13, 15, 16, 16, 15, 13, 11, 9, 8, 7, 6, 5, 4, 3, 2], k=1)[0])
        age_skill_adjustment = 0
        if apply_entry_balance:
            if age <= 24:
                age_skill_adjustment = max(-4, -int((24 - age) * 2 / 3 + 0.5))
            else:
                age_skill_adjustment = min(3, int((age - 24) / 2 + 0.5))
        base = max(min_skill, min(max_skill, random.randint(min_skill, max_skill) + age_skill_adjustment))
        # Opening-universe filler represents people already fighting when the
        # save begins. Every later generated fighter is a genuine entrant to
        # this universe: their professional record starts clean and grows only
        # through simulated bouts.
        if pre_universe is None:
            pre_universe = bool(getattr(self, "_seeding_universe", False))
        entry_month = 0 if pre_universe else max(1, int(getattr(self, "month", 1)))
        entry_year = 2026 if pre_universe else 2026 + (entry_month - 1) // 12
        if pre_universe and apply_entry_balance:
            record_cap = max(2, min(25, (age - 18) * 4 + 2))
            record_w = random.randint(0, min(18, record_cap))
            record_l = random.randint(0, min(7, record_cap - record_w))
        elif pre_universe:
            # Feeder promotions apply their own younger age, record, and upside
            # profile after creation, so keep their legacy starting roll intact.
            record_w = random.randint(0, 18)
            record_l = random.randint(0, 7)
        else:
            record_w = record_l = 0
        fighter = Fighter(
            name=name,
            weight=weight or random.choice(WEIGHTS),
            age=age,
            record_w=record_w,
            record_l=record_l,
            striking=max(25, min(99, base + random.randint(-13, 13))),
            wrestling=max(25, min(99, base + random.randint(-13, 13))),
            grappling=max(25, min(99, base + random.randint(-13, 13))),
            cardio=max(25, min(99, base + random.randint(-12, 12))),
            chin=max(25, min(99, base + random.randint(-12, 12))),
            popularity=random.randint(min_pop, max_pop),
            momentum=random.randint(-2, 3),
            morale=random.randint(45, 90),
            purse=random.randint(5000, 38000),
            gender=gender,
        )
        # Generated fighters receive a real weighted profile roll; the dataclass
        # default is only a safe fallback for imported or hand-authored fighters.
        fighter.career_archetype = ""
        self.enrich_fighter(fighter, player_owned=False)
        fighter.generated = True
        # Exceptional generated fighters still need an identifiable profile.
        # High broad rolls plus style boosts can otherwise cap most techniques
        # before their career even begins.
        self.rebalance_saturated_detailed_skills(fighter, max_overall_drop=1)
        fighter.universe_entry_month = entry_month
        fighter.universe_entry_year = entry_year
        fighter.record_history_baseline_w = record_w if pre_universe else 0
        fighter.record_history_baseline_l = record_l if pre_universe else 0
        fighter.record_history_baseline_d = 0
        fighter.multi_sport_records = {"MMA": f"{record_w}-{record_l}-0"}
        fighter.annual_overalls = {str(entry_year): fighter.overall}
        if apply_entry_balance:
            potential_floor = 12 if age <= 21 else 9 if age <= 25 else 7
            fighter.potential = min(98, max(fighter.potential, fighter.overall + potential_floor))
        self.assign_regional_identity(fighter, market_region, birth_region=birth_region, generated=True, force=True)
        return fighter

    def division_depth_targets(self, size):
        if size >= 90:
            return 18, 5
        if size >= 70:
            return 14, 4
        if size >= 50:
            return 10, 3
        return 8, 2

    def prepare_company_generated_fighter(self, fighter, region, company_name, player_owned=False):
        fighter.region = region
        fighter.residence = region
        fighter.fighting_base = region
        self.assign_regional_identity(fighter, region, force=not bool(getattr(fighter, "birth_region", "")))
        fighter.contract_months = random.randint(6, 24)
        fighter.exclusive = True
        fighter.contract_type = "Exclusive"
        fighter.camp = company_name
        if player_owned:
            fighter.morale = min(100, fighter.morale + 4)
        fighter.rank_score = self.rank_value(fighter)
        return fighter

    def ensure_roster_division_depth(self, roster, region, company_name, size, player_owned=False, reserved_names=None):
        min_total, min_gender = self.division_depth_targets(size)
        min_male = min_gender
        min_female = max(1, round(min_gender * 0.5))
        generated = 0
        generated_names = set()
        existing_names = set(reserved_names or ())
        existing_names.update(fighter.name for fighter in roster)
        for weight in WEIGHTS:
            for gender, minimum in (("Male", min_male), ("Female", min_female)):
                while len([f for f in roster if f.weight == weight and f.gender == gender]) < minimum:
                    fighter = self.create_generated_fighter(8, min(72, size), 42, min(90, 50 + size // 2), weight=weight, gender=gender, region=region)
                    self.avoid_name_collision(fighter, existing_names)
                    generated_names.add(fighter.name)
                    roster.append(self.prepare_company_generated_fighter(fighter, region, company_name, player_owned=player_owned))
                    generated += 1
            while len([f for f in roster if f.weight == weight]) < min_total:
                male_count = len([f for f in roster if f.weight == weight and f.gender == "Male"])
                female_count = len([f for f in roster if f.weight == weight and f.gender == "Female"])
                gender = "Male" if male_count < max(2, female_count * 2.5) else "Female"
                fighter = self.create_generated_fighter(8, min(72, size), 42, min(90, 50 + size // 2), weight=weight, gender=gender, region=region)
                self.avoid_name_collision(fighter, existing_names)
                generated_names.add(fighter.name)
                roster.append(self.prepare_company_generated_fighter(fighter, region, company_name, player_owned=player_owned))
                generated += 1
        return generated_names

    def ensure_free_agent_division_depth(self, fighters, min_per_bucket=6, reserved_names=None):
        existing_names = set(reserved_names or ())
        existing_names.update(fighter.name for fighter in fighters)
        for weight in WEIGHTS:
            for gender, minimum in (("Male", min_per_bucket), ("Female", max(2, round(min_per_bucket * 0.5)))):
                while len([f for f in fighters if f.weight == weight and f.gender == gender]) < minimum:
                    fighter = self.create_generated_fighter(4, 44, 36, 80, weight=weight, gender=gender)
                    self.avoid_name_collision(fighter, existing_names)
                    fighter.exclusive = False
                    fighter.contract_type = "Non-Exclusive"
                    fighter.contract_months = 0
                    fighters.append(fighter)

    def unique_generated_name(self, first, last, gender=None):
        base = f"{first} {last}"
        if self.name_counts.get(base, 0) == 0:
            self.name_counts[base] = 1
            return base
        gender = gender or ("Female" if first in FEMALE_FIRST_NAMES else "Male")
        return self.generate_clean_unique_name(gender, set(self.name_counts))

    def seed_promotions(self):
        fighter_db = self.load_seed_fighter_database()
        data = fighter_db.get("promotions") or self.expanded_real_fighter_data()
        company_section = self.universe_section("companies", {}) or {}
        specs = company_section.get("promotions") or self.default_promotion_specs(fighter_db)
        promotions = []
        global_names = self.active_fighter_names()
        for spec in specs:
            if isinstance(spec, dict):
                name = spec.get("name", "Unnamed Promotion")
                region = spec.get("region", "USA")
                size = spec.get("size", 60)
                cash = spec.get("cash", 2_000_000)
                reputation = spec.get("reputation", "National")
                roster_key = spec.get("roster_key", name)
                fighters = data.get(roster_key, data.get(name, []))
                target_roster_size = spec.get("target_roster_size", 100)
                personality = spec.get("personality", spec.get("show_personality", "Balanced"))
            else:
                name, region, size, cash, reputation, fighters, target_roster_size, personality = spec
            # A deeper launch roster needs enough runway to sign, recover from
            # early cards, and build divisions before financial pressure takes
            # over. Feeders intentionally remain at zero because they do not
            # use the commercial finance model.
            if cash > 0:
                cash = round(cash * 1.5)
            fighters = self.unique_fighter_rows(fighters)
            roster = []
            for row in fighters:
                if row[0] in global_names:
                    continue
                fighter = self.create_real_fighter(*row, player_owned=False)
                roster.append(fighter)
                global_names.add(fighter.name)
            for fighter in roster:
                fighter.region = fighter.region or region
                fighter.popularity = min(100, fighter.popularity + size // 8)
                fighter.contract_months = random.randint(8, 30)
                fighter.exclusive = True
                fighter.contract_type = "Exclusive"
                fighter.camp = "NexGen MMA" if fighter.name in self.nexgen_mma_prospect_names() else name
                fighter.rank_score = self.rank_value(fighter)
            existing_names = set(global_names)
            while len(roster) < target_roster_size:
                fighter = self.create_generated_fighter(10, min(72, size), 48, min(90, 50 + size // 2), region=region)
                self.avoid_name_collision(fighter, existing_names)
                global_names.add(fighter.name)
                fighter.region = region
                fighter.contract_months = random.randint(6, 24)
                fighter.exclusive = True
                fighter.contract_type = "Exclusive"
                fighter.camp = name
                roster.append(fighter)
            generated_names = self.ensure_roster_division_depth(roster, region, name, size, reserved_names=global_names)
            global_names.update(generated_names)
            self.seed_relationships(roster)
            belts, interim_belts, belt_history = self.ensure_company_champions(roster, {}, name, region, size, player_owned=False)
            broadcasters = self.promotion_broadcasters(name, size)
            rules = {
                "rounds": 3,
                "title_rounds": 5,
                "round_length": 5,
                "drug_testing": "Enhanced" if size > 70 else "Standard",
                "judging_randomness": 2 if size > 70 else 3,
                "allow_mixed_gender": False,
                "active_fighter_target": 1200,
            }
            promotions.append(Promotion(
                name,
                region,
                size,
                cash,
                roster,
                reputation=reputation,
                reputation_score=size,
                stability=max(45, min(96, size - random.randint(0, 12))),
                show_history=[],
                belts=belts,
                interim_belts=interim_belts,
                belt_history=belt_history,
                rules=rules,
                broadcasters=broadcasters,
                weight_classes=list(WEIGHTS),
                show_personality=personality,
                strategy=self.seed_promotion_strategy(name, personality),
                executive=self.seed_promotion_executive(name),
                era_history=[],
            ))
        promotions.extend(self.seed_regional_feeder_promotions(global_names))
        return promotions

    def create_regional_feeder_fighter(self, region, used_names, gender, feeder_name=""):
        pre_universe = bool(getattr(self, "_seeding_universe", False))
        fighter = self.create_generated_fighter(2, 22, 40, 70, gender=gender, region=region, apply_entry_balance=False, pre_universe=pre_universe)
        fighter.age = random.choices(range(17, 22), weights=[5, 8, 10, 8, 5], k=1)[0]
        fighter.record_w = random.randint(0, 6) if pre_universe else 0
        fighter.record_l = random.randint(0, min(4, fighter.record_w + 1)) if pre_universe else 0
        fighter.record_d = 0
        fighter.record_history_baseline_w = fighter.record_w if pre_universe else 0
        fighter.record_history_baseline_l = fighter.record_l if pre_universe else 0
        fighter.record_history_baseline_d = 0
        fighter.multi_sport_records = {"MMA": f"{fighter.record_w}-{fighter.record_l}-0"}
        # Regional intake is the long-term talent engine. Most entrants should
        # be capable of becoming credible professionals, with strong and elite
        # ceilings remaining progressively rarer. Ability is not granted here:
        # fighters must still realise this ceiling through gyms, activity,
        # mentality and results over the following decade.
        potential_roll = random.random()
        if potential_roll < 0.12:
            potential = random.randint(65, 71)
        elif potential_roll < 0.68:
            potential = random.randint(72, 81)
        elif potential_roll < 0.92:
            potential = random.randint(82, 88)
        elif potential_roll < 0.985:
            potential = random.randint(89, 94)
        else:
            potential = random.randint(95, 98)
        fighter.potential = min(98, max(fighter.overall + 6, potential))
        fighter.popularity = min(24, fighter.popularity)
        fighter.purse = max(500, min(4000, fighter.purse // 3))
        fighter.contract_months = 0
        fighter.exclusive = False
        fighter.contract_type = "Developmental"
        fighter.feeder_origin = feeder_name or region
        pool = REGIONAL_NAME_POOLS.get(region, {})
        allowed_first = set(pool.get("female" if gender == "Female" else "male", ()))
        allowed_last = set(pool.get("last", ()))
        first, _, last = fighter.name.partition(" ")
        needs_regional_replacement = bool(pool) and (first not in allowed_first or last not in allowed_last)
        if fighter.name in used_names or needs_regional_replacement:
            for _ in range(250):
                first, last = self.generated_name_parts(gender, region)
                candidate = f"{first} {last}"
                if candidate not in used_names:
                    fighter.name = candidate
                    break
            else:
                self.avoid_name_collision(fighter, used_names)
        used_names.add(fighter.name)
        return fighter

    def regional_feeder_specs(self):
        return [
            ("Japan Fight Circuit", "Japan"),
            ("UK Regional MMA", "UK"),
            ("North American Fighting League", "USA"),
            ("European Challenge MMA", "Europe"),
            ("Asia Rising Championship", "Asia"),
            ("Brazilian Combat Circuit", "Brazil"),
            ("Latin American MMA League", "Mexico"),
            ("Canadian Fight Alliance", "Canada"),
            ("Oceania Combat League", "Australia"),
            ("African MMA Championship", "Africa"),
            ("Midwest Fight League", "USA"),
            ("Nordic Combat League", "Europe"),
            ("Korean Fighting Championship", "South Korea"),
            ("South American Vale Tudo Circuit", "Brazil"),
            ("British Fight League", "UK"),
        ]

    def seed_regional_feeder_promotions(self, global_names, specs=None):
        specs = list(specs or self.regional_feeder_specs())
        promotions = []
        for name, region in specs:
            roster = []
            for weight in WEIGHTS:
                # 70 fighters per feeder: deeper at the most active male
                # divisions, while every female division remains bookable.
                male_count = 5 if weight in ("Light Heavyweight", "Heavyweight") else 6
                for gender, count in (("Male", male_count), ("Female", 3)):
                    for _ in range(count):
                        fighter = self.create_regional_feeder_fighter(region, global_names, gender, feeder_name=name)
                        fighter.weight = weight
                        fighter.region = region
                        fighter.nationality = self.infer_nationality(fighter.name, region)
                        fighter.camp = name
                        roster.append(fighter)
                        global_names.add(fighter.name)
            promotions.append(Promotion(
                name=name, region=region, size=24, cash=0, roster=roster,
                reputation="Regional Feeder", reputation_score=24, stability=70,
                show_history=[], belts=self.blank_belts(), interim_belts=self.blank_belts(), belt_history=self.blank_belt_history(),
                rules={"rounds": 3, "title_rounds": 3, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 4, "allow_mixed_gender": False, "active_fighter_target": 1200},
                broadcasters=[], weight_classes=list(WEIGHTS), show_personality="Regional Development", is_regional_feeder=True,
                strategy=self.seed_promotion_strategy(name, "Regional Development"),
                executive=self.seed_promotion_executive(name),
                era_history=[],
            ))
        return promotions

    def seed_promotion_executive(self, company_name):
        names = {
            "Ultimate Fighting Championship": ("Mason Rourke", "Empire Builder"),
            "Professional Fighters League": ("Elena Ward", "Competition Architect"),
            "ONE Championship": ("Arun Vichai", "Global Visionary"),
            "RIZIN Fighting Federation": ("Kenji Mori", "Event Showman"),
            "Cage Warriors": ("Claire Hargreaves", "Talent Developer"),
            "PRIDE Fighting Championships": ("Hiroshi Tanaka", "Event Showman"),
            "Strikeforce": ("Dana Calder", "Aggressive Promoter"),
            "World Extreme Cagefighting": ("Rafael Stone", "Talent Developer"),
        }
        name, archetype = names.get(company_name, (f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}", random.choice(["Pragmatic Operator", "Talent Developer", "Aggressive Promoter", "Cost Controller"])))
        profile = {
            "Empire Builder": (76, 62, 58), "Competition Architect": (54, 74, 76),
            "Global Visionary": (72, 66, 55), "Event Showman": (82, 48, 46),
            "Talent Developer": (42, 86, 74), "Pragmatic Operator": (52, 60, 82),
            "Aggressive Promoter": (82, 48, 42), "Cost Controller": (32, 54, 92),
        }[archetype]
        mandate = {
            "Empire Builder": "Reputation Growth", "Competition Architect": "Title Success", "Global Visionary": "Reputation Growth",
            "Event Showman": "Event Cadence", "Talent Developer": "Roster Pipeline", "Pragmatic Operator": "Financial Stability",
            "Aggressive Promoter": "Event Cadence", "Cost Controller": "Financial Stability",
        }[archetype]
        return {"name": name, "archetype": archetype, "aggression": profile[0], "patience": profile[1], "discipline": profile[2], "job_security": random.randint(62, 92), "tenure_years": 0,
                "board_mandate": mandate, "mandate_target": 0, "mandate_progress": 0, "mandate_deadline": 0, "mandate_history": []}

    def seed_promotion_strategy(self, name, show_personality="Balanced"):
        """Persistent company identity. Current mode can change, core values do not."""
        presets = {
            "Ultimate Fighting Championship": ("Championship First", "Global spectacle", "Title Push", 82, 76, 58),
            "Professional Fighters League": ("Season Structure", "Competitive merit", "Contender Cycle", 68, 62, 70),
            "ONE Championship": ("International Stars", "Cross-cultural stars", "Star Chasing", 74, 72, 55),
            "RIZIN Fighting Federation": ("Event Spectacle", "National heroes", "Star Chasing", 78, 74, 48),
            "KSW": ("Homegrown Icons", "Regional heroes", "Star Chasing", 72, 66, 52),
            "Cage Warriors": ("Talent Pipeline", "Future contenders", "Prospect Rebuild", 44, 82, 74),
            "Legacy Fighting Alliance": ("Talent Pipeline", "Future contenders", "Prospect Rebuild", 40, 84, 72),
            "Oktagon MMA": ("Regional Expansion", "European stars", "Contender Cycle", 62, 68, 58),
            "BRAVE Combat Federation": ("Global Scouting", "International prospects", "Prospect Rebuild", 52, 78, 64),
            "Absolute Championship Akhmat": ("Competitive Merit", "Hard-nosed contenders", "Contender Cycle", 48, 64, 70),
            "PRIDE Fighting Championships": ("Grand Prix Spectacle", "Japanese legends and global stars", "Star Chasing", 84, 62, 58),
            "Strikeforce": ("Big Fight Crossover", "Stars, challengers and storylines", "Star Chasing", 78, 66, 54),
            "World Extreme Cagefighting": ("Elite Lightweights", "Fast-rising division talent", "Prospect Rebuild", 50, 82, 66),
        }
        identity, voice, mode, star_focus, prospect_focus, merit_focus = presets.get(
            name,
            ("Development Circuit", "Local opportunity", "Prospect Rebuild", 25, 92, 56) if show_personality == "Regional Development" else ("Balanced Growth", "Reliable fights", "Balanced", 50, 55, 58),
        )
        # A promotion's commercial situation is separate from sporting quality.
        # This gives the world a mix of dependable broadcasters, fragile growth
        # companies, and boom/bust operators instead of identical balance sheets.
        commercial_strength, market_volatility = {
            "Ultimate Fighting Championship": (94, 7), "Professional Fighters League": (67, 16),
            "ONE Championship": (84, 11), "RIZIN Fighting Federation": (72, 17),
            "KSW": (65, 18), "Cage Warriors": (50, 24), "Legacy Fighting Alliance": (45, 27),
            "Oktagon MMA": (64, 19), "BRAVE Combat Federation": (54, 23),
            "Absolute Championship Akhmat": (59, 21), "PRIDE Fighting Championships": (80, 13),
            "Strikeforce": (70, 17), "World Extreme Cagefighting": (58, 20), "BAMMA": (43, 28),
        }.get(name, (35, 18) if show_personality == "Regional Development" else (55, 20))
        return {
            "identity": identity,
            "media_voice": voice,
            "current_mode": mode,
            "star_focus": star_focus,
            "prospect_focus": prospect_focus,
            "merit_focus": merit_focus,
            "risk_tolerance": max(20, min(90, round((star_focus + prospect_focus + merit_focus) / 3))),
            "commercial_strength": commercial_strength,
            "market_volatility": market_volatility,
            "market_momentum": 0.0,
            "market_review_month": 0,
            "finance_model_version": 2,
            "growth_ceiling": {
                "Ultimate Fighting Championship": 100, "Professional Fighters League": 88, "ONE Championship": 92,
                "RIZIN Fighting Federation": 88, "KSW": 84, "Cage Warriors": 78, "Legacy Fighting Alliance": 74,
            "Oktagon MMA": 84, "BRAVE Combat Federation": 80, "Absolute Championship Akhmat": 80,
            "PRIDE Fighting Championships": 92, "Strikeforce": 86, "World Extreme Cagefighting": 82, "BAMMA": 72,
            }.get(name, 42 if show_personality == "Regional Development" else 76),
            "last_review_month": 0,
        }

    def repair_core_promotions(self, restore_missing=False):
        """Repair lightweight metadata without changing an existing save's world."""
        self.promotions = [promo for promo in self.promotions if promo.name != self.player_company_name]
        names = {promo.name for promo in self.promotions}
        regional_names = [name for name, _region in self.regional_feeder_specs()]
        required = ["Cage Warriors", "ONE Championship", "RIZIN Fighting Federation", "KSW", "Legacy Fighting Alliance", "Oktagon MMA", "BRAVE Combat Federation", "Absolute Championship Akhmat", "PRIDE Fighting Championships", "Strikeforce", "World Extreme Cagefighting", *regional_names]
        defunct = set(getattr(self, "defunct_promotions", []))
        missing = [name for name in required if self.player_company_name != name and name not in names and name not in defunct]
        if missing and restore_missing:
            seeded = self.seed_promotions()
            for company_name in missing:
                promo = next((item for item in seeded if item.name == company_name), None)
                if promo:
                    self.promotions.append(promo)
            self.news.insert(0, f"World database repaired: restored missing promotions ({', '.join(missing)}).")

        # Versioned expansion: existing saves gain only the five additional
        # feeder circuits, with no resurrection of unrelated defunct companies.
        pipeline_version = int(getattr(self, "rules", {}).get("regional_pipeline_version", 0) or 0)
        if pipeline_version < 2:
            original_names = {
                "Japan Fight Circuit", "UK Regional MMA", "North American Fighting League",
                "European Challenge MMA", "Asia Rising Championship", "Brazilian Combat Circuit",
                "Latin American MMA League", "Canadian Fight Alliance", "Oceania Combat League",
                "African MMA Championship",
            }
            expansion_specs = [
                spec for spec in self.regional_feeder_specs()
                if spec[0] not in original_names and spec[0] not in names and spec[0] not in defunct
            ]
            if expansion_specs:
                self.promotions.extend(self.seed_regional_feeder_promotions(self.active_fighter_names(), specs=expansion_specs))
                added = ", ".join(name for name, _region in expansion_specs)
                self.news.insert(0, f"Regional pathway expanded: {added} opened as new development circuits.")
            self.rules["regional_pipeline_version"] = 2

    def promotion_broadcasters(self, name, size):
        if name == "Ultimate Fighting Championship":
            return [{"name": "Paramount+ / ESPN Global", "reach": 96, "fee": 1_500_000, "type": "Premium Streaming"}]
        if name == "Professional Fighters League":
            return [{"name": "PFL Global Broadcast", "reach": 78, "fee": 550_000, "type": "Streaming / TV"}]
        if name == "ONE Championship":
            return [{"name": "ONE Global Streaming", "reach": 82, "fee": 720_000, "type": "Global Streaming"}]
        if name == "RIZIN Fighting Federation":
            return [{"name": "RIZIN PPV / Fuji Network", "reach": 70, "fee": 420_000, "type": "PPV / TV"}]
        if name == "KSW":
            return [{"name": "KSW TV International", "reach": 66, "fee": 330_000, "type": "Streaming / TV"}]
        if name == "Legacy Fighting Alliance":
            return [{"name": "UFC Fight Pass", "reach": 58, "fee": 150_000, "type": "Streaming"}]
        if name == "Oktagon MMA":
            return [{"name": "Oktagon TV / European Broadcast", "reach": 68, "fee": 360_000, "type": "Streaming / TV"}]
        if name == "BRAVE Combat Federation":
            return [{"name": "BRAVE Global Network", "reach": 61, "fee": 245_000, "type": "Streaming / TV"}]
        if name == "Absolute Championship Akhmat":
            return [{"name": "ACA Fight Network", "reach": 63, "fee": 275_000, "type": "Streaming / TV"}]
        if name == "PRIDE Fighting Championships":
            return [{"name": "PRIDE World PPV / Fuji Network", "reach": 82, "fee": 760_000, "type": "PPV / TV"}]
        if name == "Strikeforce":
            return [{"name": "Strikeforce Premium Network", "reach": 72, "fee": 420_000, "type": "Premium TV / Streaming"}]
        if name == "World Extreme Cagefighting":
            return [{"name": "WEC Fight Network", "reach": 64, "fee": 285_000, "type": "Streaming / TV"}]
        return [{"name": "UFC Fight Pass / Local TV", "reach": 54, "fee": 120_000, "type": "Streaming"}]

    def seed_regions(self):
        economies = ["struggling but improving", "below average but improving", "stable", "strong", "booming"]
        legality = ["fully legal", "regulated by athletic commissions", "loosely regulated", "restricted in some areas"]
        states = {
            "USA": ["California", "Nevada", "New York", "Texas", "Florida", "Hawaii", "Illinois", "Georgia"],
            "Canada": ["Ontario", "Quebec", "Alberta", "British Columbia"],
            "Brazil": ["Rio de Janeiro", "Sao Paulo", "Parana", "Bahia"],
            "Mexico": ["Mexico City", "Jalisco", "Nuevo Leon", "Baja California"],
            "UK": ["England", "Scotland", "Wales", "Northern Ireland"],
            "Europe": ["France", "Germany", "Netherlands", "Poland", "Spain"],
            "Russia": ["Moscow", "Saint Petersburg", "Kazan", "Dagestan"],
            "Japan": ["Tokyo", "Osaka", "Saitama", "Fukuoka"],
            "South Korea": ["Seoul", "Busan", "Incheon", "Daegu"],
            "Australia": ["New South Wales", "Victoria", "Queensland", "Western Australia"],
            "Asia": ["Thailand", "Singapore", "Philippines", "South Korea"],
            "Middle East": ["Bahrain", "United Arab Emirates", "Saudi Arabia", "Qatar"],
            "Africa": ["South Africa", "Nigeria", "Egypt", "Kenya"],
        }
        return {
            region: {
                "economy": random.choice(economies),
                "legality": random.choice(legality),
                "drug_accuracy": random.choice([35, 50, 65, 80, 95]),
                "mma_love": random.randint(35, 85),
                "promo_benefit": REGION_PROMO_BENEFITS.get(region, {"media": 1.0, "gate": 1.0, "morale": 1}),
                "teams": random.sample(CAMPS, k=min(3, len(CAMPS))),
                "areas": areas,
                "last_major_show": "No major shows yet",
                "fan_identity": {
                    "USA": "Big-fight spectacle", "Canada": "Technical respect", "Brazil": "Passionate national pride",
                    "Mexico": "Action-first intensity", "UK": "Loud fight-night culture", "Europe": "Hardcore technique",
                    "Russia": "Wrestling and sambo tradition", "Japan": "Respectful combat tradition",
                    "South Korea": "Fast-growing combat culture", "Australia": "Festival fight fans",
                    "Asia": "Global crossover audience", "Middle East": "Prestige event market", "Africa": "Emerging regional pride",
                }.get(region, "Local MMA community"),
                "crowd_preference": {
                    "USA": "Stars and finishes", "Canada": "Competitive skill", "Brazil": "Local heroes and submissions",
                    "Mexico": "Aggressive action", "UK": "Rivalries and underdogs", "Europe": "Technical matchups",
                    "Russia": "Grappling and durable contenders", "Japan": "Respect and elite technique",
                    "South Korea": "Pace and technical action", "Australia": "High-energy action",
                    "Asia": "International stars", "Middle East": "Champions and global names", "Africa": "Local heroes and finishes",
                }.get(region, "Competitive fights"),
            }
            for region, areas in states.items()
        }

    def seed_gyms(self):
        specs = [
            ("Independent", "USA", "Anywhere", 42, 35, ["Prospect Development"], "Local Coach", 999, 0, 50, 40, 35),
            ("Iron Vale", "USA", "Chicago", 58, 45, ["Wrestling", "Conditioning"], "Ray Mercer Jr.", 45, 900, 61, 55, 50),
            ("Blackstone MMA", "USA", "Las Vegas", 72, 68, ["Boxing", "Gameplanning"], "Dante Black", 70, 1800, 68, 74, 62),
            ("American Top Team", "USA", "Florida", 88, 90, ["Wrestling", "BJJ", "Conditioning"], "Ricardo Alvarez", 130, 4200, 78, 91, 80),
            ("AKA", "USA", "California", 86, 88, ["Wrestling", "Kickboxing", "Gameplanning"], "Javier Stone", 95, 3900, 72, 88, 77),
            ("Team Alpha Male", "USA", "California", 82, 82, ["Wrestling", "Boxing", "Prospect Development"], "Urijah Cole", 75, 3100, 76, 82, 72),
            ("Jackson Wink", "USA", "New Mexico", 80, 78, ["Gameplanning", "Kickboxing", "Clinch"], "Greg Winkle", 80, 2800, 65, 80, 74),
            ("Nova Uniao", "Brazil", "Rio de Janeiro", 84, 86, ["BJJ", "Boxing", "Prospect Development"], "Andre Pederneiras Jr.", 85, 2400, 80, 82, 69),
            ("Chute Boxe", "Brazil", "Curitiba", 83, 84, ["Kickboxing", "Clinch", "Conditioning"], "Rafael Cordeiro Jr.", 80, 2600, 74, 81, 68),
            ("Sakuraba Dojo", "Japan", "Tokyo", 76, 74, ["BJJ", "Wrestling", "Gameplanning"], "Kazushi Sato", 55, 1700, 72, 73, 62),
            ("Shootbox Japan", "Japan", "Osaka", 78, 70, ["Kickboxing", "Clinch", "Conditioning"], "Takeshi Mori", 50, 1600, 68, 76, 60),
            ("City Kickboxing", "Australia", "Auckland", 87, 88, ["Kickboxing", "Gameplanning", "Conditioning"], "Eugene Park", 90, 3600, 77, 89, 78),
            ("Sydney Elite MMA", "Australia", "Sydney", 76, 68, ["Boxing", "Wrestling", "Prospect Development"], "Mark Hennessy", 65, 1900, 67, 74, 58),
            ("Tiger Muay Thai", "Asia", "Phuket", 84, 82, ["Kickboxing", "Clinch", "Conditioning"], "Kru Somchai", 120, 2700, 72, 86, 70),
            ("Tristar", "Canada", "Montreal", 82, 80, ["Gameplanning", "Wrestling", "Boxing"], "Firas Laurent", 70, 2600, 75, 82, 72),
            ("Northstar Combat", "Canada", "Toronto", 68, 58, ["Wrestling", "Prospect Development"], "Owen Grant", 55, 1300, 66, 64, 55),
            ("Kings Road", "UK", "London", 63, 55, ["Boxing", "Conditioning"], "Billy Rhodes", 50, 1200, 60, 60, 48),
            ("NexGen MMA", "UK", "Manchester", 78, 72, ["Prospect Development", "Wrestling", "Conditioning"], "Mara Keene", 64, 1800, 74, 78, 76),
            ("London Shootfighters", "UK", "London", 77, 74, ["Wrestling", "Kickboxing", "BJJ"], "Alex Turner", 75, 2200, 70, 76, 65),
            ("Altitude Fight Team", "Europe", "Amsterdam", 79, 76, ["Kickboxing", "Conditioning", "Clinch"], "Mika De Vries", 70, 2300, 69, 78, 64),
            ("Mexico City Combat", "Mexico", "Mexico City", 74, 66, ["Boxing", "Wrestling", "Prospect Development"], "Santiago Reyes", 65, 1500, 73, 70, 57),
            ("Xtreme Couture", "USA", "Las Vegas", 82, 83, ["Wrestling", "Boxing", "Gameplanning"], "Eric Warren", 105, 3200, 74, 84, 73),
            ("Kill Cliff FC", "USA", "Florida", 84, 84, ["Wrestling", "Conditioning", "Prospect Development"], "Henri Hooft Jr.", 110, 3400, 76, 86, 78),
            ("Fortis MMA", "USA", "Dallas", 77, 74, ["Boxing", "Wrestling", "Prospect Development"], "Sayif Stone", 90, 2200, 72, 77, 75),
            ("Roufusport", "USA", "Milwaukee", 76, 72, ["Kickboxing", "Conditioning", "Gameplanning"], "Duke Rhodes", 85, 2100, 70, 76, 67),
            ("Alliance MMA", "USA", "San Diego", 79, 78, ["Wrestling", "BJJ", "Gameplanning"], "Eric Del Fierro Jr.", 90, 2500, 72, 80, 71),
            ("Elevation Fight Team", "USA", "Denver", 80, 79, ["Conditioning", "Wrestling", "Kickboxing"], "Eliot Marshall Jr.", 95, 2600, 76, 82, 72),
            ("Sanford Combat Club", "USA", "Florida", 78, 75, ["Kickboxing", "Clinch", "Conditioning"], "Marcus Silveira", 95, 2500, 71, 79, 69),
            ("Brazilian Top Team", "Brazil", "Rio de Janeiro", 80, 80, ["BJJ", "Wrestling", "Gameplanning"], "Murilo Costa", 100, 2100, 75, 79, 72),
            ("Team Nogueira", "Brazil", "Sao Paulo", 77, 78, ["BJJ", "Boxing", "Prospect Development"], "Rogerio Santos", 90, 1900, 77, 76, 74),
            ("Parana Vale Tudo", "Brazil", "Curitiba", 72, 66, ["BJJ", "Clinch", "Conditioning"], "Jorge Lima", 85, 1400, 70, 71, 63),
            ("Lobo Gym", "Mexico", "Guadalajara", 78, 74, ["Boxing", "Kickboxing", "Prospect Development"], "Francisco Lobo", 90, 1600, 78, 76, 73),
            ("Entram Gym", "Mexico", "Tijuana", 73, 68, ["Boxing", "Wrestling", "Conditioning"], "Raul Arvizu Jr.", 80, 1400, 73, 72, 66),
            ("SBG Ireland", "UK", "Dublin", 80, 82, ["Boxing", "Gameplanning", "BJJ"], "John Kavanagh Jr.", 90, 2500, 75, 81, 72),
            ("Kaobon", "UK", "Liverpool", 75, 70, ["Kickboxing", "Wrestling", "Prospect Development"], "Colin Heron Jr.", 80, 1700, 72, 75, 70),
            ("Great Britain Top Team", "UK", "London", 76, 72, ["Wrestling", "BJJ", "Prospect Development"], "Brad Pickett Jr.", 90, 1900, 74, 76, 75),
            ("Straight Blast Toronto", "Canada", "Toronto", 72, 66, ["BJJ", "Gameplanning", "Prospect Development"], "Claude Patrick Jr.", 80, 1600, 72, 72, 69),
            ("Niagara Top Team", "Canada", "Ontario", 76, 73, ["Wrestling", "Conditioning", "Prospect Development"], "Chris Prickett Jr.", 85, 1800, 75, 76, 72),
            ("Allstars Training Center", "Europe", "Stockholm", 82, 82, ["Wrestling", "Boxing", "Gameplanning"], "Andreas Michael Jr.", 95, 2700, 76, 83, 76),
            ("UFD Gym", "Europe", "Dusseldorf", 78, 75, ["Kickboxing", "Wrestling", "Conditioning"], "Ivan Hippolyte Jr.", 90, 2200, 73, 79, 69),
            ("Warsaw Combat Academy", "Europe", "Warsaw", 73, 67, ["Wrestling", "Kickboxing", "Prospect Development"], "Marek Kowalski", 90, 1500, 75, 72, 74),
            ("MMA Factory Paris", "Europe", "Paris", 80, 77, ["Wrestling", "Boxing", "Prospect Development"], "Fernand Lopez Jr.", 95, 2300, 77, 80, 78),
            ("Red Fury Team", "Russia", "Moscow", 84, 84, ["Wrestling", "Sambo", "Conditioning"], "Magomed Kerimov", 120, 2100, 78, 84, 82),
            ("Dagestan Fight School", "Russia", "Makhachkala", 87, 88, ["Wrestling", "BJJ", "Conditioning"], "Abdul Nurmagomedov", 130, 2300, 80, 87, 88),
            ("Akhmat Fight Club", "Russia", "Grozny", 82, 83, ["Wrestling", "Clinch", "Gameplanning"], "Mansur Isaev", 115, 2100, 72, 83, 81),
            ("Alexander Nevsky Club", "Russia", "St Petersburg", 75, 70, ["Sambo", "Boxing", "Prospect Development"], "Viktor Petrov", 90, 1500, 74, 75, 73),
            ("Paraestra Tokyo", "Japan", "Tokyo", 77, 76, ["BJJ", "Wrestling", "Prospect Development"], "Yuki Nakahara", 85, 1800, 77, 76, 75),
            ("Krazy Bee", "Japan", "Tokyo", 78, 79, ["Wrestling", "Boxing", "Conditioning"], "Kiyoshi Yamamoto", 85, 1900, 75, 78, 73),
            ("Busan Team MAD", "South Korea", "Busan", 76, 72, ["Kickboxing", "Wrestling", "Prospect Development"], "Yang Sung-ho", 95, 1600, 78, 76, 79),
            ("Korean Top Team", "South Korea", "Seoul", 79, 78, ["Wrestling", "Kickboxing", "Conditioning"], "Ha Dong-jin", 100, 1900, 77, 80, 78),
            ("Evolve MMA", "Asia", "Singapore", 83, 82, ["Kickboxing", "BJJ", "Gameplanning"], "Siyar Bahadur", 110, 3000, 80, 87, 82),
            ("Bali MMA", "Asia", "Bali", 74, 68, ["Kickboxing", "Conditioning", "Prospect Development"], "Don Carlo", 90, 1500, 78, 75, 72),
            ("Team Lakay", "Asia", "Baguio", 76, 75, ["Kickboxing", "Wrestling", "Prospect Development"], "Mark Sangiao Jr.", 100, 1300, 82, 75, 84),
            ("Freestyle Fighting Gym", "Australia", "Sydney", 81, 79, ["Wrestling", "Kickboxing", "Gameplanning"], "Joe Frey", 95, 2500, 76, 81, 74),
            ("Australian Top Team", "Australia", "Melbourne", 73, 67, ["Boxing", "Wrestling", "Prospect Development"], "Daniel Kelly Jr.", 90, 1600, 73, 74, 72),
            ("KHK MMA", "Middle East", "Manama", 80, 81, ["Wrestling", "Gameplanning", "Conditioning"], "Eldar Eldarov Jr.", 105, 2800, 74, 82, 80),
            ("Dubai Fight Lab", "Middle East", "Dubai", 76, 72, ["Kickboxing", "BJJ", "Conditioning"], "Omar Al Hassan", 100, 2600, 77, 84, 75),
            ("Abu Dhabi Combat Team", "Middle East", "Abu Dhabi", 78, 77, ["BJJ", "Wrestling", "Prospect Development"], "Khalid Al Mansoori", 110, 2500, 76, 82, 81),
            ("Team CIT", "Africa", "Pretoria", 79, 78, ["Wrestling", "Boxing", "Conditioning"], "Morne Visser Jr.", 105, 1600, 81, 78, 80),
            ("Lagos Fight House", "Africa", "Lagos", 72, 67, ["Boxing", "Wrestling", "Prospect Development"], "Chidi Okafor", 100, 1100, 80, 72, 82),
            ("Atlas Combat Club", "Africa", "Casablanca", 71, 65, ["Kickboxing", "Clinch", "Prospect Development"], "Youssef Amrani", 90, 1100, 78, 71, 76),
        ]
        gyms = []
        for name, region, city, quality, reputation, specialties, coach, capacity, fee, morale, facilities, scouting in specs:
            gyms.append(Gym(name, region, city, quality, reputation, specialties, coach, capacity, fee, morale, facilities, scouting, 0, self.gym_note(name, specialties)))
        return gyms

    def gym_note(self, name, specialties):
        if name == "Independent":
            return "Low cost and flexible, but development is inconsistent."
        return f"Known for {', '.join(specialties).lower()} and producing fighters with a clear camp identity."

    def gym_by_name(self, name):
        for gym in getattr(self, "gyms", []):
            if gym.name == name:
                return gym
        return None

    def gym_quality(self, name):
        gym = self.gym_by_name(name)
        if gym:
            return gym.quality
        return CAMP_QUALITY.get(name, 45)

    def gym_specialty_bonus(self, fighter, gym=None):
        gym = gym or self.gym_by_name(fighter.camp)
        if not gym:
            return 0
        style_fit = {
            "Boxer": "Boxing", "Kickboxer": "Kickboxing", "Muay Thai": "Clinch", "Wrestler": "Wrestling",
            "BJJ": "BJJ", "Grappler": "BJJ", "Sambo": "Wrestling", "Judo": "Wrestling",
            "Karate": "Kickboxing", "Well-Rounded": "Gameplanning",
        }.get(fighter.style, "Gameplanning")
        bonus = 7 if style_fit in gym.specialties else 0
        if "Prospect Development" in gym.specialties and fighter.age < fighter.prime_start:
            bonus += 6
        if "Conditioning" in gym.specialties:
            bonus += 3
        return bonus

    def gym_attention_multiplier(self, gym):
        """Individual coaching attention, bounded so a busy elite room remains useful."""
        if not gym or gym.capacity >= 500:
            return 1.0
        load = gym.member_count / max(1, gym.capacity)
        if load <= 0.65:
            return 1.05
        if load <= 0.90:
            return 1.02 - (load - 0.65) * 0.08
        return max(0.62, 1.0 - (load - 0.90) * 0.31)

    def gym_effective_training(self, gym, fighter=None):
        if not gym:
            return 42
        specialty = self.gym_specialty_bonus(fighter, gym) if fighter else 0
        base = gym.quality * 0.48 + gym.facilities * 0.22 + gym.morale * 0.16 + gym.development_reputation * 0.14
        return round(max(25, min(99, (base + specialty * 0.45) * self.gym_attention_multiplier(gym))))

    def gym_tier(self, gym):
        score = gym.quality * 0.55 + gym.reputation * 0.30 + gym.facilities * 0.15
        return "World Class" if score >= 84 else "Elite" if score >= 77 else "National" if score >= 68 else "Regional" if score >= 56 else "Local"

    def sync_gym_membership(self):
        gyms = getattr(self, "gyms", [])
        gym_lookup = {gym.name: gym for gym in gyms}
        for gym in gyms:
            gym.member_count = 0
        all_fighters = list(getattr(self, "roster", [])) + list(getattr(self, "free_agents", []))
        for promo in getattr(self, "promotions", []):
            all_fighters.extend(promo.roster)
        for world in getattr(self, "combat_sport_worlds", {}).values():
            all_fighters.extend(world.get("roster", []))
        seen = set()
        for fighter in all_fighters:
            if id(fighter) in seen or getattr(fighter, "retired", False):
                continue
            seen.add(id(fighter))
            gym = gym_lookup.get(fighter.camp)
            if gym:
                gym.member_count += 1

    def seed_finance(self):
        return {
            "ticket_price": 55,
            "sponsor_income": 26000,
            "merch_rate": 0.12,
            "broadcast_cut": 0.18,
            "monthly_office": 12000,
            "staff_payroll": 0,
            "marketing_budget": 18000,
            "production_base": 24000,
            "medical_base": 9000,
            "drug_test_cost": 2500,
            "tax_rate": 0.18,
            "sponsor_deals": [],
            "media_rights": {"name": "No rights package", "months": 0, "fee": 0, "reach": 0},
            "commentators": [
                {"name": "Mike Lane", "role": "Play-by-play", "quality": 62, "salary": 3500, "chemistry": 58},
                {"name": "Laura Nash", "role": "Analyst", "quality": 66, "salary": 4200, "chemistry": 64},
            ],
            "last_event": {},
            "ledger": [],
            "weekly_history": [],
            "week_transactions": [],
        }

    def seed_engine_settings(self):
        return {
            "ko_power": 1.0,
            "submission_finish": 1.0,
            "decision_noise": 1.0,
            "gas_cost": 1.0,
            "damage": 1.0,
            "gate_multiplier": 1.0,
        }

    def seed_staff(self):
        return [
            {"name": "Dana Holt", "role": "Matchmaker", "skill": 72, "salary": 8500, "morale": 76, "specialty": "Contender logic", "reputation": 68},
            {"name": "Maya Quinn", "role": "Scout", "skill": 68, "salary": 6200, "morale": 80, "specialty": "Prospect eye", "reputation": 62},
            {"name": "Reed Wallace", "role": "Doctor", "skill": 64, "salary": 7000, "morale": 70, "specialty": "Injury prevention", "reputation": 59},
            {"name": "Felix Park", "role": "Marketing", "skill": 60, "salary": 5800, "morale": 74, "specialty": "Regional campaigns", "reputation": 56},
        ]

    def create_staff_candidate(self):
        roles = ["Scout", "Doctor", "Marketing", "Matchmaker", "Drug Testing Officer", "Broadcast Producer", "Talent Relations"]
        famous = [
            ("Mick Maynard", "Matchmaker", 86), ("Sean Shelby", "Matchmaker", 88),
            ("Laura Sanko", "Broadcast Producer", 82), ("Marc Ratner", "Drug Testing Officer", 84),
            ("Din Thomas", "Scout", 78), ("Ray Longo", "Talent Relations", 80),
        ]
        if random.random() < 0.18:
            name, role, skill = random.choice(famous)
        else:
            role = random.choice(roles)
            name = f"{random.choice(FIRST_NAMES + FEMALE_FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            skill = random.randint(42, 90)
        salary = round((skill * random.randint(95, 185)) / 10) * 10
        specialties = {
            "Scout": ["Prospect eye", "International network", "Women’s divisions"],
            "Doctor": ["Injury prevention", "Weight-cut safety", "Recovery planning"],
            "Marketing": ["Regional campaigns", "Digital promotion", "Sponsor sales"],
            "Matchmaker": ["Contender logic", "Prospect protection", "Grudge booking"],
            "Drug Testing Officer": ["Targeted testing", "Compliance"],
            "Broadcast Producer": ["Live production", "Story packages"],
            "Talent Relations": ["Contract trust", "Veteran management"],
        }
        return {"name": name, "role": role, "skill": skill, "salary": max(3500, salary), "morale": random.randint(55, 92), "specialty": random.choice(specialties[role]), "reputation": random.randint(40, min(94, skill + 8))}

    def seed_staff_candidates(self):
        return [self.create_staff_candidate() for _ in range(14)]

    def seed_owner_goals(self):
        return [
            {"goal": "Keep cash above $150,000", "metric": "cash", "target": 150000, "deadline": 12, "status": "Active"},
            {"goal": "Reach company popularity 50", "metric": "popularity", "target": 50, "deadline": 18, "status": "Active"},
            {"goal": "Run at least 4 shows", "metric": "shows", "target": 4, "deadline": 12, "status": "Active"},
        ]
