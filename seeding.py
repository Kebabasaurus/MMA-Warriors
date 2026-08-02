import json
import random
import sys
import traceback
from bisect import bisect
from copy import deepcopy
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion
from real_sport_profiles import SPORT_PROFILE_VERSION, build_fallback_sport_profile, build_real_sport_profiles


def weighted_choice_table(values, weights):
    total = 0
    cumulative = []
    for weight in weights:
        total += weight
        cumulative.append(total)
    return tuple(values), tuple(cumulative), total


def weighted_table_pick(table):
    values, cumulative, total = table
    return values[bisect(cumulative, random.random() * total)]


DEFAULT_SIGNATURE_DETAILED_SKILLS = frozenset(("adaptability", "conditioning"))
FIGHTER_SIGNATURE_DETAILED_SKILLS = {
    "Boxer": frozenset(("punch_power", "punch_technique", "hand_speed", "head_movement")),
    "Kickboxer": frozenset(("high_kick_power", "high_kick_technique", "low_kick_technique", "kick_defence")),
    "Dutch Kickboxer": frozenset(("punch_technique", "low_kick_power", "low_kick_technique", "guard_defence")),
    "Karate": frozenset(("footwork", "high_kick_speed", "creative_kicks", "head_movement")),
    "Taekwondo": frozenset(("high_kick_technique", "high_kick_speed", "creative_kicks", "footwork")),
    "Sanda": frozenset(("creative_kicks", "clinch_takedowns", "throws", "footwork")),
    "Muay Thai": frozenset(("knees", "elbows", "thai_plum", "low_kick_power")),
    "Wrestler": frozenset(("takedowns", "takedown_setup", "chain_wrestling", "sprawl")),
    "Freestyle Wrestler": frozenset(("takedown_speed", "chain_wrestling", "scrambles", "sprawl")),
    "Catch Wrestler": frozenset(("chain_wrestling", "ride_control", "submission_attack", "top_control")),
    "BJJ": frozenset(("submission_attack", "submission_defence_detail", "guard_work", "back_control")),
    "Submission Grappler": frozenset(("submission_attack", "transitions", "back_control", "leg_locks")),
    "Sambo": frozenset(("takedowns", "throws", "submission_attack", "leg_locks")),
    "Judo": frozenset(("throws", "clinch_takedowns", "top_control", "positional_ability")),
    "Grappler": frozenset(("top_control", "submission_attack", "transitions", "scrambles")),
    "Luta Livre": frozenset(("leg_locks", "submission_attack", "scrambles", "top_control")),
}


GENERATED_FIGHTER_AGE_TABLE = weighted_choice_table(
    range(18, 34),
    (11, 13, 15, 16, 16, 15, 13, 11, 9, 8, 7, 6, 5, 4, 3, 2),
)
GENERATED_STANCE_TABLE = weighted_choice_table(("Orthodox", "Southpaw", "Switch"), (58, 29, 13))
NEGOTIATION_PERSONA_TABLE = weighted_choice_table(
    ("Professional", "Hard Bargainer", "Loyalist", "Star Chaser", "Security First", "Competitive"),
    (34, 17, 14, 12, 13, 10),
)
CAREER_ARCHETYPE_TABLE = weighted_choice_table(
    ("Early Maturation", "Balanced Development", "Late Maturation", "Durable Career"),
    (16, 53, 17, 14),
)
REGIONAL_FEEDER_AGE_TABLE = weighted_choice_table(range(17, 22), (5, 8, 10, 8, 5))
MMA_FIGHTER_DATABASE_SCHEMA = 4
COMBAT_SPORT_DATABASE_SCHEMA = 5
COMBAT_SPORT_NAMES = ("Boxing", "Kickboxing", "Muay Thai", "Lethwei", "Wrestling", "Brazilian Jiu-Jitsu")


class SeedMixin:
    def active_universe_marker(self):
        """Store selection metadata beside, not inside, the universe database folder."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        marker = DATA_DIR / "active_universe.txt"
        legacy = DATABASE_DIR / "active_universe.txt"
        if not marker.exists() and legacy.exists():
            marker.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
        return marker

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
        path = self.universe_database_path("Default Universe")
        if not path.exists():
            raise RuntimeError("The required Default Universe.universe.json starting database is missing. Restore the packaged database file before starting a new game.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("type") != "universe_database" or not data.get("sections"):
            raise RuntimeError("Default Universe.universe.json is not a valid universe database pack.")
        data["database_name"] = name
        return data

    def ensure_default_universe_database(self):
        path = self.universe_database_path("Default Universe")
        if not path.exists():
            raise RuntimeError("The required Default Universe.universe.json starting database is missing. Restore the packaged database file before starting a new game.")
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
        path = Path(path or self.active_universe_database_path())
        try:
            signature = (path.stat().st_mtime_ns, path.stat().st_size)
        except OSError:
            signature = None
        cached = getattr(self, "_universe_database_cache", None)
        if cached and cached.get("path") == path and cached.get("signature") == signature:
            return cached["data"]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
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
                self.write_seed_database_file(path, data)
            try:
                signature = (path.stat().st_mtime_ns, path.stat().st_size)
            except OSError:
                signature = None
            self._universe_database_cache = {"path": path, "signature": signature, "data": data}
            return data
        except Exception as exc:
            default_path = self.universe_database_path("Default Universe")
            if path.resolve() == default_path.resolve():
                raise RuntimeError(
                    "Default Universe.universe.json could not be read. Restore the packaged starting database file before starting a new game."
                ) from exc
            backup = Path(path).with_suffix(f".broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                Path(path).replace(backup)
            except Exception:
                pass
            default = self.build_universe_database_pack("Default Universe")
            default["repair_note"] = f"Pack was regenerated after load failure: {type(exc).__name__}: {exc}"
            self.write_seed_database_file(default_path, default)
            self.active_universe_marker().write_text(default_path.name, encoding="utf-8")
            try:
                signature = (default_path.stat().st_mtime_ns, default_path.stat().st_size)
            except OSError:
                signature = None
            self._universe_database_cache = {"path": default_path, "signature": signature, "data": default}
            return default

    def merge_default_fighter_database(self, fighters):
        """Normalize the shipped editable fighter database without code-owned rows."""
        normalized = self.normalize_seed_fighter_database(fighters)
        changed = False
        for key, value in normalized.items():
            if fighters.get(key) != value:
                fighters[key] = value
                changed = True
        for key, value in (("bamma_addins_embedded", True), ("opening_replacements_embedded", True)):
            if fighters.get(key) != value:
                fighters[key] = value
                changed = True
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
        """Upgrade legacy combat-sport databases without overriding flat edits."""
        if not isinstance(combat_section, dict):
            return False
        changed = False
        if combat_section.get("all_athletes") and int(combat_section.get("schema", 1) or 1) >= COMBAT_SPORT_DATABASE_SCHEMA:
            normalized = self.normalize_combat_sport_database(combat_section)
            for key in ("rosters", "prime_divisions", "profiles", "schema", "database_name", "notes"):
                if combat_section.get(key) != normalized.get(key):
                    combat_section[key] = normalized.get(key)
                    changed = True
            return changed

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
        rebuilt_records = self.combat_sport_records_from_views(rosters, profiles, divisions)
        if combat_section.get("all_athletes") != rebuilt_records:
            combat_section["all_athletes"] = rebuilt_records
            changed = True
        if int(combat_section.get("schema", 1) or 1) < COMBAT_SPORT_DATABASE_SCHEMA:
            combat_section["schema"] = COMBAT_SPORT_DATABASE_SCHEMA
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
        cached = getattr(self, "_universe_database_cache", None)
        if cached and cached.get("path") == Path(path):
            self._universe_database_cache = None

    def seed_fighter_record_from_row(self, row, placement, owner=None, gender=None):
        row = list(row)
        if len(row) < 10:
            raise ValueError(f"Fighter database row for {row[0] if row else 'unknown'} is incomplete")
        identity = self.real_fighter_identity_data(row[0]) or {}
        profile = self.real_fighter_profiles().get(row[0], {})
        signature_skills = self.signature_real_fighter_detailed_profiles().get(row[0], {})
        special_profile = self.special_real_fighter_profiles().get(row[0], {})
        stance = self.real_fighter_stances().get(row[0], "")
        birth_country = str(row[14] if len(row) > 14 else identity.get("birth_country", "") or identity.get("citizenship", "") or "").strip()
        citizenship = str(identity.get("citizenship", "") or birth_country).strip()
        nationality = str(row[13] if len(row) > 13 else "").strip()
        if not nationality:
            nationality = COUNTRY_NATIONALITIES.get(citizenship, citizenship or self.infer_nationality(row[0], row[8]))
        record = {
            "database_type": "mma",
            "generated": False,
            "placement": placement,
            "owner": owner or row[2],
            "seed_org": row[2],
            "name": row[0],
            "weight": row[1],
            "gender": gender or (row[11] if len(row) > 11 else "") or self.infer_gender(row[0]),
            "popularity": row[3],
            "rating": row[4],
            "age": row[5],
            "record_w": row[6],
            "record_l": row[7],
            "record_d": self.real_fighter_draws().get(row[0], 0),
            "region": row[8],
            "nationality": nationality,
            "birth_country": birth_country,
            "hometown": str(row[15] if len(row) > 15 else identity.get("city", "") or "").strip(),
            "style": row[9],
            "source_url": row[10] if len(row) > 10 else "",
            "potential": row[12] if len(row) > 12 else "",
        }
        if profile:
            record["profile_rating"] = profile.get("rating", row[4])
            record["profile_style"] = profile.get("style", row[9])
            if profile.get("trait"):
                record["trait"] = profile["trait"]
            if profile.get("behaviour"):
                record["behaviour"] = profile["behaviour"]
            if profile.get("skills"):
                record["skill_mods"] = dict(profile["skills"])
        if stance:
            record["stance"] = stance
        if signature_skills:
            record["signature_skills"] = dict(signature_skills)
        if special_profile:
            record["special_profile"] = special_profile
        return record

    def enrich_seed_fighter_record(self, record):
        if not isinstance(record, dict):
            return record
        row = self.seed_fighter_row_from_record(record)
        enriched = self.seed_fighter_record_from_row(
            row,
            record.get("placement", "promotion"),
            owner=record.get("owner"),
            gender=record.get("gender"),
        )
        for key in (
            "database_type", "generated", "seed_org", "record_d", "nationality", "birth_country",
            "hometown", "profile_rating", "profile_style", "trait", "behaviour", "skill_mods",
            "stance", "signature_skills", "special_profile",
        ):
            if key in enriched and key not in record:
                record[key] = enriched[key]
        return record

    def cache_seed_fighter_database(self, data):
        self._seed_fighter_database = data
        lookup = {}
        owner_lookup = {}
        for record in (data or {}).get("all_fighters", []):
            if not isinstance(record, dict):
                continue
            name = record.get("name")
            if not name:
                continue
            lookup.setdefault(self.fighter_name_key(name), record)
            owner = record.get("owner") or record.get("seed_org") or ""
            if owner:
                owner_lookup.setdefault((self.fighter_name_key(name), str(owner).casefold()), record)
        self._seed_fighter_record_lookup = lookup
        self._seed_fighter_record_owner_lookup = owner_lookup
        self.opening_replacements_embedded = bool((data or {}).get("opening_replacements_embedded"))
        return data

    def seed_fighter_record_for(self, name, owner=""):
        lookup = getattr(self, "_seed_fighter_record_lookup", None)
        if lookup is None:
            data = getattr(self, "_seed_fighter_database", {}) or {}
            self.cache_seed_fighter_database(data)
            lookup = getattr(self, "_seed_fighter_record_lookup", {})
        if owner:
            owner_lookup = getattr(self, "_seed_fighter_record_owner_lookup", {})
            matched = owner_lookup.get((self.fighter_name_key(name), str(owner).casefold()))
            if matched:
                return matched
        return lookup.get(self.fighter_name_key(name), {})

    def seed_fighter_row_from_record(self, record):
        if isinstance(record, (list, tuple)):
            return list(record)
        owner = record.get("owner") or record.get("company") or record.get("promotion") or "Free Agent"
        seed_org = record.get("seed_org") or owner
        row = [
            record.get("name", "Unnamed Fighter"),
            record.get("weight", "Lightweight"),
            seed_org,
            int(record.get("popularity", record.get("pop", 35)) or 35),
            int(record.get("rating", record.get("skill", record.get("overall", 65))) or 65),
            int(record.get("age", 28) or 28),
            int(record.get("record_w", record.get("wins", 0)) or 0),
            int(record.get("record_l", record.get("losses", 0)) or 0),
            record.get("region", "USA"),
            record.get("style", "Well-Rounded"),
        ]
        extra_values = (
            record.get("source_url", ""),
            record.get("gender", ""),
            record.get("potential", ""),
            record.get("nationality", ""),
            record.get("birth_country", ""),
            record.get("hometown", ""),
        )
        extras = []
        if any(value not in ("", None) for value in extra_values):
            extras.append(record.get("source_url", ""))
        if any(value not in ("", None) for value in extra_values[1:]):
            extras.append(record.get("gender", ""))
        for value in extra_values[2:]:
            if extras or value not in ("", None):
                extras.append(value)
        return row + extras

    def starting_fighter_records(self):
        """Return the active editable MMA records without reintroducing code tables."""
        data = getattr(self, "_seed_fighter_database", None)
        if not isinstance(data, dict) or not data.get("all_fighters"):
            data = self.load_seed_fighter_database()
        return [record for record in data.get("all_fighters", []) if isinstance(record, dict)]

    def starting_fighter_rows(self, *, owners=(), placements=()):
        owners = set(owners)
        placements = set(placements)
        rows = []
        for record in self.starting_fighter_records():
            if owners and record.get("owner") not in owners:
                continue
            if placements and record.get("placement") not in placements:
                continue
            rows.append(self.seed_fighter_row_from_record(record))
        return rows

    def starting_fighter_records_by_name(self):
        return {
            self.fighter_name_key(record.get("name", "")): record
            for record in self.starting_fighter_records()
            if record.get("name")
        }

    def fighter_database_records_from_groups(self, player_roster, free_agents, promotions):
        records = []
        seen = set()

        def add(row, placement, owner=None, gender=None):
            try:
                record = self.seed_fighter_record_from_row(row, placement, owner=owner, gender=gender)
            except ValueError:
                return
            key = (self.fighter_name_key(record["name"]), record.get("owner", ""))
            if key in seen:
                return
            seen.add(key)
            records.append(record)

        for row in player_roster:
            add(row, "player_roster", PLAYER_PROMOTION_NAME)
        for row in free_agents:
            add(row, "free_agents", row[2] if isinstance(row, (list, tuple)) and len(row) > 2 else "Free Agent")
        for company, rows in (promotions or {}).items():
            for row in rows:
                add(row, "promotion", company)
        return records

    def normalize_seed_fighter_database(self, data):
        data = dict(data or {})
        records = data.get("all_fighters")
        if isinstance(records, list) and records:
            needs_enrichment = int(data.get("schema", 1) or 1) < MMA_FIGHTER_DATABASE_SCHEMA
            records = [
                self.enrich_seed_fighter_record(dict(record)) if needs_enrichment else dict(record)
                for record in records
                if isinstance(record, dict)
            ]
            data["all_fighters"] = records
            player_roster, free_agents, promotions = [], [], {}
            for record in records:
                if not isinstance(record, dict):
                    continue
                row = self.seed_fighter_row_from_record(record)
                owner = record.get("owner") or row[2]
                placement = str(record.get("placement", "")).lower()
                if placement in ("promotion", "promotions"):
                    promotions.setdefault(owner, []).append(row)
                elif placement in ("player", "player_roster") or owner == PLAYER_PROMOTION_NAME:
                    player_roster.append(row)
                elif placement in ("free_agent", "free_agents") or owner in ("Free Agent", "Legend"):
                    free_agents.append(row)
                else:
                    promotions.setdefault(owner, []).append(row)
            data["player_roster"] = self.unique_fighter_rows(player_roster)
            data["free_agents"] = self.unique_fighter_rows(free_agents)
            data["promotions"] = {company: self.unique_fighter_rows(rows) for company, rows in promotions.items()}
        else:
            player_roster = data.get("player_roster") or []
            free_agents = data.get("free_agents") or []
            promotions = data.get("promotions") or {}
            data["all_fighters"] = self.fighter_database_records_from_groups(player_roster, free_agents, promotions)
        data["schema"] = max(MMA_FIGHTER_DATABASE_SCHEMA, int(data.get("schema", 1) or 1))
        data.setdefault("database_name", "Core MMA Fighter Database")
        data.setdefault(
            "notes",
            "Canonical new-game MMA fighter seed database. Edit all_fighters to change named starting rosters; grouped sections are compatibility views.",
        )
        return data

    def build_seed_fighter_database(self):
        path = self.universe_database_path("Default Universe")
        data = json.loads(path.read_text(encoding="utf-8"))
        fighters = data.get("sections", {}).get("fighters", {})
        if not isinstance(fighters, dict) or not fighters.get("all_fighters"):
            raise RuntimeError("Default Universe.universe.json has no MMA fighter records")
        return self.normalize_seed_fighter_database(fighters)

    def load_seed_fighter_database(self):
        section = self.universe_section("fighters", None)
        if section:
            normalized = self.normalize_seed_fighter_database(section)
            return self.cache_seed_fighter_database(normalized)
        raise RuntimeError("The active universe database is missing its fighters section.")

    def build_combat_sport_database(self):
        rosters = self.builtin_combat_sport_real_roster_data()
        profiles = build_real_sport_profiles(rosters)
        return {
            "schema": COMBAT_SPORT_DATABASE_SCHEMA,
            "database_name": "Combat Sport Fighter Database",
            "notes": "Canonical combat-sport seed database. Edit all_athletes to change named starting rosters; rosters, profiles, and prime_divisions are compatibility views.",
            "rosters": rosters,
            "prime_divisions": COMBAT_SPORT_REAL_DIVISIONS,
            "profiles": profiles,
            "all_athletes": self.combat_sport_records_from_views(rosters, profiles, COMBAT_SPORT_REAL_DIVISIONS),
        }

    def combat_sport_seed_women(self):
        return {
            "Jorina Baars", "Lucia Rijker", "Denise Kielholtz", "Jemyma Betrian", "Anissa Meksen",
            "Christine Ferea", "Britain Hart", "Souris Manfredi", "Julija Stoliarenko", "Maisha Katz", "Shwe Sin Min",
            "Saori Yoshida", "Kaori Icho", "Helen Maroulis", "Adeline Gray", "Tamyra Mensah-Stock",
            "Iryna Merleni", "Gabi Garcia", "Beatriz Mesquita", "Somratsamee Manopgym",
        }

    def combat_sport_record_from_view(self, sport, name, index, profile, divisions):
        profile = dict(profile or {})
        region = profile.get("region") or self.combat_sport_region_for_name(name, sport)
        weight_class = profile.get("weight_class") or (divisions.get(sport, {}) if isinstance(divisions, dict) else {}).get(name, "")
        record = {
            "database_type": "combat_sport",
            "generated": False,
            "sport": sport,
            "name": name,
            "gender": profile.get("gender") or ("Female" if name in self.combat_sport_seed_women() else "Male"),
            "region": region,
            "nationality": profile.get("nationality") or self.infer_nationality(name, region),
            "weight_class": weight_class,
            "roster_index": index,
        }
        for key, value in profile.items():
            if key not in record:
                record[key] = value
        return record

    def combat_sport_profile_from_record(self, record):
        profile = {}
        for key, value in (record or {}).items():
            if key in {"database_type", "generated", "sport", "name", "roster_index"}:
                continue
            profile[key] = value
        return profile

    def combat_sport_records_from_views(self, rosters, profiles, divisions):
        records = []
        seen = set()
        profiles = profiles if isinstance(profiles, dict) else {}
        divisions = divisions if isinstance(divisions, dict) else {}
        for sport, names in (rosters or {}).items():
            if sport not in COMBAT_SPORT_NAMES or not isinstance(names, list):
                continue
            for index, name in enumerate(names):
                name = str(name).strip()
                if not name:
                    continue
                key = (sport, name)
                if key in seen:
                    continue
                seen.add(key)
                profile = (profiles.get(sport, {}) if isinstance(profiles.get(sport, {}), dict) else {}).get(name, {})
                records.append(self.combat_sport_record_from_view(sport, name, index, profile, divisions))
        return records

    def normalize_combat_sport_database(self, data):
        data = dict(data or {})
        records = data.get("all_athletes")
        if isinstance(records, list) and records:
            rosters, profiles, divisions = {}, {}, {}
            seen = set()
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                sport = record.get("sport")
                name = str(record.get("name", "")).strip()
                if sport not in COMBAT_SPORT_NAMES or not name:
                    continue
                key = (sport, name)
                if key in seen:
                    continue
                seen.add(key)
                rosters.setdefault(sport, []).append(name)
                profile = self.combat_sport_profile_from_record(record)
                profile.setdefault("version", SPORT_PROFILE_VERSION)
                profile.setdefault("rating", max(55, 82 - index // 8))
                profile.setdefault("prime_age", 27 + index % 5)
                profile.setdefault("record_w", 0)
                profile.setdefault("record_l", 0)
                profile.setdefault("record_d", 0)
                profile.setdefault("style", "Boxer" if sport == "Boxing" else "Wrestler" if sport == "Wrestling" else "BJJ" if sport == "Brazilian Jiu-Jitsu" else "Kickboxer")
                profile.setdefault("trait", "Technical Learner")
                profile.setdefault("behaviour", "Dynamic Attacker")
                profile.setdefault("stance", "Orthodox")
                profile.setdefault("gender", "Female" if name in self.combat_sport_seed_women() else "Male")
                region = profile.get("region") or self.combat_sport_region_for_name(name, sport)
                profile["region"] = region
                profile.setdefault("nationality", self.infer_nationality(name, region))
                weight_class = profile.get("weight_class") or record.get("weight_class") or COMBAT_SPORT_REAL_DIVISIONS.get(sport, {}).get(name, "")
                if weight_class:
                    profile["weight_class"] = weight_class
                    divisions.setdefault(sport, {})[name] = weight_class
                profiles.setdefault(sport, {})[name] = profile
            data["rosters"] = rosters
            data["profiles"] = profiles
            data["prime_divisions"] = divisions
        else:
            rosters = data.get("rosters", data if "Boxing" in data else {})
            profiles = self.normalized_combat_sport_profiles(rosters, data.get("profiles", {}))
            divisions = data.get("prime_divisions") or COMBAT_SPORT_REAL_DIVISIONS
            data["rosters"] = rosters
            data["profiles"] = profiles
            data["prime_divisions"] = divisions
            data["all_athletes"] = self.combat_sport_records_from_views(rosters, profiles, divisions)
        data["schema"] = max(COMBAT_SPORT_DATABASE_SCHEMA, int(data.get("schema", 1) or 1))
        data.setdefault("database_name", "Combat Sport Fighter Database")
        data.setdefault(
            "notes",
            "Canonical combat-sport seed database. Edit all_athletes to change named starting rosters; rosters, profiles, and prime_divisions are compatibility views.",
        )
        return data

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
            section = self.normalize_combat_sport_database(section)
            rosters = section.get("rosters", section)
            if isinstance(rosters, dict) and "Boxing" in rosters:
                self.combat_sport_seed_divisions = section.get("prime_divisions", {}) if isinstance(section, dict) else {}
                self.combat_sport_seed_profiles = section.get("profiles", {})
                return rosters
        raise RuntimeError("The active universe database is missing its combat_sports section.")

    def seed_roster(self):
        seed_db = self.load_seed_fighter_database()
        featured = seed_db.get("player_roster") or self.cage_empire_fighter_data()
        featured = self.unique_fighter_rows(featured)
        roster = [self.create_real_fighter_from_seed_row(row, player_owned=True) for row in featured]
        existing_featured = {self.fighter_name_key(fighter.name) for fighter in roster}
        if not seed_db.get("bamma_addins_embedded"):
            for row, gender in self.bamma_initial_addin_data():
                if self.fighter_name_key(row[0]) in existing_featured:
                    continue
                fighter = self.create_real_fighter_from_seed_row(row, player_owned=True)
                fighter.gender = gender
                roster.append(fighter)
                existing_featured.add(self.fighter_name_key(fighter.name))
        promotion_data = seed_db.get("promotions") or self.expanded_real_fighter_data()
        company_names = {row[0] for rows in promotion_data.values() for row in rows}
        existing_names = {fighter.name for fighter in roster} | company_names
        # BAMMA's curated add-ins are intentionally additional depth. Keep the
        # normal generated-divisional safety net, but open with a promotion-
        # sized 190-fighter roster instead of crowding real names out.
        while len(roster) < 190:
            prospect = self.create_generated_fighter(8, 48, 43, 82)
            self.avoid_name_collision(prospect, existing_names)
            prospect.contract_months = random.randint(6, 22)
            prospect.exclusive = True
            prospect.contract_type = "Exclusive"
            roster.append(prospect)
        self.ensure_roster_division_depth(roster, self.player_region, self.player_company_name, self.company_pop, player_owned=True)
        closed_divisions = self.bamma_initial_closed_divisions()
        self.reassign_closed_division_fighters(roster, closed_divisions)
        self.ensure_bamma_womens_division_depth(roster)
        self.seed_relationships(roster)
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(
            roster, self.belts, self.player_company_name, self.player_region, self.company_pop,
            player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history,
            closed_divisions=closed_divisions,
        )
        return roster

    def bamma_initial_closed_divisions(self):
        return {
            self.belt_key("Female", weight)
            for weight in ("Middleweight", "Light Heavyweight", "Heavyweight")
        }

    def reassign_closed_division_fighters(self, roster, closed_divisions):
        """Keep an opening roster inside the divisions the promotion actually runs.

        Applies to whichever promotion the player starts with, not one company:
        any promotion can open with divisions closed. The fighter moves to the
        nearest division that is still open for their gender rather than a
        hardcoded class, because dropping a heavyweight into welterweight moved
        them ninety pounds and left a frame that fitted neither.
        """
        for fighter in roster:
            if self.belt_key(fighter.gender, fighter.weight) not in closed_divisions:
                continue
            try:
                index = WEIGHTS.index(fighter.weight)
            except ValueError:
                index = len(WEIGHTS) // 2
            options = sorted(
                (
                    candidate for candidate in WEIGHTS
                    if self.belt_key(fighter.gender, candidate) not in closed_divisions
                ),
                key=lambda candidate: abs(WEIGHTS.index(candidate) - index),
            )
            if options:
                self.assign_fighter_division(fighter, options[0], reset_walk_weight=True)

    def ensure_bamma_womens_division_depth(self, roster):
        """Guarantee viable fresh-start depth in BAMMA's women's divisions."""
        existing_names = {fighter.name for fighter in roster}
        for weight in ("Featherweight", "Bantamweight"):
            while sum(
                fighter.gender == "Female" and fighter.weight == weight
                for fighter in roster
            ) < 6:
                fighter = self.create_generated_fighter(
                    8, 48, 43, 82, weight=weight, gender="Female", region=self.player_region,
                )
                self.avoid_name_collision(fighter, existing_names)
                existing_names.add(fighter.name)
                roster.append(self.prepare_company_generated_fighter(
                    fighter, self.player_region, self.player_company_name, player_owned=True,
                ))

    def bamma_initial_addin_data(self):
        """Compatibility view of BAMMA's database-owned opening additions."""
        return [
            (self.seed_fighter_row_from_record(record), record.get("gender", ""))
            for record in self.starting_fighter_records()
            if record.get("placement") == "player_roster" and record.get("owner") == PLAYER_PROMOTION_NAME
        ]

    def seed_free_agents(self):
        seed_db = self.load_seed_fighter_database()
        promotion_data = seed_db.get("promotions") or self.expanded_real_fighter_data()
        company_names = {row[0] for rows in promotion_data.values() for row in rows}
        reserved_names = {fighter.name for fighter in getattr(self, "roster", [])}
        free_agent_rows = seed_db.get("free_agents") or (self.independent_fighter_data() + self.legend_fighter_data())
        names = [row for row in free_agent_rows if row[0] not in company_names and row[0] not in reserved_names]
        names = self.unique_fighter_rows(names)
        fighters = [self.create_real_fighter_from_seed_row(row, player_owned=False) for row in names]
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
        self.replace_generated_opening_slots(fighters, "Free Agents", existing_names)
        self.seed_relationships(fighters)
        return fighters

    def real_fighter_data(self):
        """Compatibility view of the database-owned promotion rosters."""
        grouped = {}
        for record in self.starting_fighter_records():
            if record.get("placement") != "promotion":
                continue
            grouped.setdefault(record.get("owner", "Free Agent"), []).append(self.seed_fighter_row_from_record(record))
        return grouped

    def game_weight_class(self, weight):
        """Map real-world classes onto MMA Warriors' eight supported divisions."""
        return {"Atomweight": "Flyweight", "Strawweight": "Flyweight"}.get(weight, weight if weight in WEIGHTS else "Lightweight")

    def create_real_fighter_from_seed_row(self, row, player_owned=False):
        row = list(row)
        kwargs = {"player_owned": player_owned}
        if len(row) > 10:
            kwargs["source_url"] = row[10]
        if len(row) > 11:
            kwargs["gender"] = row[11]
        if len(row) > 12:
            kwargs["potential"] = row[12]
        if len(row) > 13:
            kwargs["nationality"] = row[13]
        if len(row) > 14:
            kwargs["birth_country"] = row[14]
        if len(row) > 15:
            kwargs["hometown"] = row[15]
        kwargs["seed_record"] = self.seed_fighter_record_for(row[0], row[2] if len(row) > 2 else "")
        return self.create_real_fighter(*row[:10], **kwargs)

    def apply_authored_fighter_overrides(self, fighter, record):
        """Apply explicit universe-database values after generated profile defaults.

        Curated records still use their rating/profile helpers for a useful
        baseline, but a database author must be able to pin any persisted
        Fighter field without a later seed step silently replacing it.
        """
        if not isinstance(record, dict):
            return fighter
        generated_details = dict(getattr(fighter, "detailed_skills", None) or {})
        for key in Fighter.__dataclass_fields__:
            if key in record:
                value = record[key]
                # Older authored records use empty strings for optional
                # numeric values such as potential. Treat those as unset so
                # they retain their generated/profile baseline.
                if value in ("", None) and isinstance(getattr(fighter, key), (bool, int, float)):
                    continue
                setattr(fighter, key, deepcopy(value))
        fighter.weight = self.game_weight_class(fighter.weight)
        # Only synchronize broad ratings when the author supplied a detailed
        # sheet. Existing generated detail values must not overwrite an
        # explicitly authored broad skill such as striking or fight_iq.
        if "detailed_skills" in record and isinstance(record.get("detailed_skills"), dict):
            # Database authors may pin one attribute without accidentally
            # replacing the rest of the generated detailed profile with 50s.
            generated_details.update({
                key: max(1, min(99, int(value)))
                for key, value in record["detailed_skills"].items()
                if isinstance(value, (int, float))
            })
            fighter.detailed_skills = generated_details
            self.sync_broad_skills_from_details(fighter)
        return fighter

    def create_real_fighter(self, name, weight, org, popularity, skill, age, wins, losses, region, style, player_owned=False, source_url="", gender="", potential=None, nationality="", birth_country="", hometown="", seed_record=None):
        record = seed_record if isinstance(seed_record, dict) else self.seed_fighter_record_for(name, org)
        weight = self.game_weight_class(weight)
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
            gender=gender or self.infer_gender(name),
        )
        self.enrich_fighter(fighter, player_owned=player_owned)
        fighter.region = region
        fighter.nationality = self.infer_nationality(name, region)
        fighter.style = style if style in STYLES else "Well-Rounded"
        fighter.camp = org
        fighter.source_url = source_url
        self.assign_regional_identity(fighter, region, birth_region=region, force=True)
        self.apply_real_fighter_birthplace(fighter, region)
        if nationality:
            fighter.nationality = nationality
        if birth_country:
            fighter.birth_country = birth_country
            fighter.birth_region = COUNTRY_TO_REGION.get(birth_country, fighter.birth_region or region)
        if hometown:
            fighter.hometown = hometown
        fighter.detailed_skills = None
        self.apply_real_fighter_profile(fighter, skill, record=record)
        self.apply_special_real_fighter_profile(fighter, record=record)
        # A fully authored database sheet is the final authority. Special
        # profiles may contain legacy random ranges; reapplying the complete
        # signature here guarantees that an editor-locked opening profile is
        # identical in every newly seeded game.
        if isinstance(record.get("signature_skills"), dict) and record["signature_skills"]:
            self.apply_signature_real_fighter_profile(fighter, preserve_career=False, record=record)
        if record.get("prime_rating_profile_version"):
            fighter.prime_rating_profile_version = int(record["prime_rating_profile_version"])
        prime_age = self.historic_prime_age_overrides().get(fighter.name)
        if prime_age is None:
            prime_age = self.real_fighter_capped_age(fighter.name, fighter.age)
        if prime_age is not None:
            fighter.age = prime_age
            fighter.prime_start = max(24, prime_age - 3)
            fighter.prime_end = max(fighter.prime_start + 5, prime_age + 6)
            fighter.prime_legend_age_override_version = 1
        profile_rating = int(record.get("profile_rating", record.get("rating", skill)) or skill)
        fighter.potential = max(fighter.overall, min(98, profile_rating + 6))
        if potential not in ("", None):
            try:
                fighter.potential = max(fighter.overall, int(potential))
            except (TypeError, ValueError):
                pass
        # Authored records are history that predates this save. Store that
        # baseline explicitly instead of waiting for a later profile refresh to
        # infer it from the current record.
        fighter.record_d = int(record.get("record_d", fighter.record_d) or 0)
        fighter.record_history_baseline_w = fighter.record_w
        fighter.record_history_baseline_l = fighter.record_l
        fighter.record_history_baseline_d = fighter.record_d
        fighter.universe_entry_month = 0
        fighter.universe_entry_year = 2026
        fighter.multi_sport_records = {"MMA": f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"}
        fighter.real_record_baseline_version = 1
        fighter.real_identity_version = 1
        if fighter.name in self.prime_legend_ages():
            fighter.legend_prime_age_version = 1
        fighter.contract_months = random.randint(10, 30) if player_owned else 0
        fighter.exclusive = player_owned
        fighter.contract_type = "Exclusive" if player_owned else "Non-Exclusive"
        fighter.rank_score = self.rank_value(fighter)
        self.apply_authored_fighter_overrides(fighter, record)
        if "rank_score" not in record:
            fighter.rank_score = self.rank_value(fighter)
        return fighter

    def initial_real_fighter_replacements(self, destination):
        """Legacy migration data now held on the relevant database records."""
        return ()

    def replace_generated_opening_slots(self, roster, destination, global_names=None):
        """Replace same-division generated opening slots with curated athletes."""
        if getattr(self, "opening_replacements_embedded", False):
            return []
        global_names = global_names if global_names is not None else set()
        known = {self.fighter_name_key(name) for name in global_names if isinstance(name, str)}
        known.update(self.fighter_name_key(fighter.name) for fighter in roster)
        replacements = []
        for row in self.initial_real_fighter_replacements(destination):
            name, weight, popularity, skill, age, wins, losses, region, style, potential, source_url, *gender_value = row
            name_key = self.fighter_name_key(name)
            if name_key in known:
                continue
            gender = gender_value[0] if gender_value else self.infer_gender(name)
            slot = next((fighter for fighter in roster if fighter.generated and fighter.weight == weight and fighter.gender == gender), None)
            if slot is None:
                continue
            replacement = self.create_real_fighter(name, weight, destination, popularity, skill, age, wins, losses, region, style, source_url=source_url)
            replacement.gender = gender
            replacement.potential = max(replacement.overall, potential)
            replacement.contract_months = slot.contract_months
            replacement.exclusive = slot.exclusive
            replacement.contract_type = slot.contract_type
            replacement.camp = slot.camp
            record = self.seed_fighter_record_for(name)
            adjustments = record.get("legacy_opening_skill_adjustments", {}) if record else {}
            if adjustments:
                self.ensure_detailed_skills(replacement)
                for key, adjustment in adjustments.items():
                    if key in replacement.detailed_skills:
                        replacement.detailed_skills[key] = max(35, replacement.detailed_skills[key] + int(adjustment))
                self.sync_broad_skills_from_details(replacement)
            replacement.rank_score = self.rank_value(replacement)
            roster[roster.index(slot)] = replacement
            known.add(name_key)
            global_names.update((name, name_key))
            replacements.append(name)
        return replacements

    def infer_gender(self, name):
        record = self.seed_fighter_record_for(name)
        if record.get("gender") in ("Male", "Female"):
            return record["gender"]
        first_name = str(name).replace("-", " ").split()[0] if name else ""
        return "Female" if first_name in FEMALE_FIRST_NAMES else "Male"

    def infer_nationality(self, name, region):
        record = self.seed_fighter_record_for(name)
        if record.get("nationality"):
            return record["nationality"]
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

    def real_fighter_identity_data(self, name):
        """Return verified identity data, with fighter records taking precedence."""
        record = self.seed_fighter_record_for(name)
        if record and any(record.get(key) for key in ("hometown", "birth_country", "nationality")):
            return {
                "city": record.get("hometown", ""),
                "birth_country": record.get("birth_country", ""),
                "citizenship": record.get("birth_country", ""),
            }
        data = self.real_fighter_birthplace_data()
        aliases = {
            "Donald Cerrone WEC": "Donald Cerrone",
            "Ben Henderson WEC": "Ben Henderson",
            "Ian Machado Garry CW": "Ian Machado Garry",
            "Lone'er Kavanagh CW": "Lone'er Kavanagh",
        }
        identity = data.get(name) or data.get(aliases.get(name, ""))
        if identity:
            return identity
        return None

    def apply_real_fighter_birthplace(self, fighter, fallback_region):
        identity = self.real_fighter_identity_data(fighter.name)
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
        popularity = {}
        popularity[birth_region] = min(78, random.randint(18, 34) + fighter.popularity // 3)
        popularity[residence] = max(popularity.get(residence, 0), min(74, random.randint(14, 30) + fighter.popularity // 3))
        popularity[training_region] = max(popularity.get(training_region, 0), min(55, random.randint(8, 22) + fighter.popularity // 5))
        for connection in connections[3:]:
            popularity[connection] = max(popularity.get(connection, 0), random.randint(9, 24))
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
        markets = getattr(fighter, "regional_popularity", None) or {}
        markets.setdefault(region, 0)
        markets[region] = max(0, min(100, markets[region] + delta))
        fighter.regional_popularity = markets
        if note:
            fighter.home_event_history = ([{"month": self.month, "region": region, "note": note, "market_popularity": markets[region]}] + (getattr(fighter, "home_event_history", None) or []))[:18]

    def real_fighter_profiles(self):
        profiles = {}
        for record in self.starting_fighter_records():
            profile = {}
            if "profile_rating" in record:
                profile["rating"] = record["profile_rating"]
            if record.get("profile_style"):
                profile["style"] = record["profile_style"]
            if record.get("trait"):
                profile["trait"] = record["trait"]
            if record.get("behaviour"):
                profile["behaviour"] = record["behaviour"]
            if record.get("skill_mods"):
                profile["skills"] = dict(record["skill_mods"])
            if profile:
                profiles[record["name"]] = profile
        return profiles

    def signature_real_fighter_detailed_profiles(self):
        return {
            record["name"]: dict(record["signature_skills"])
            for record in self.starting_fighter_records()
            if record.get("signature_skills")
        }

    def special_real_fighter_profiles(self):
        return {
            record["name"]: dict(record["special_profile"])
            for record in self.starting_fighter_records()
            if record.get("special_profile")
        }

    def apply_signature_real_fighter_profile(self, fighter, preserve_career=False, record=None):
        record = record if isinstance(record, dict) else self.seed_fighter_record_for(fighter.name)
        targets = record.get("signature_skills") if record else self.signature_real_fighter_detailed_profiles().get(fighter.name)
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

    def apply_special_real_fighter_profile(self, fighter, record=None):
        record = record if isinstance(record, dict) else self.seed_fighter_record_for(fighter.name)
        profile = record.get("special_profile") if record else self.special_real_fighter_profiles().get(fighter.name)
        if not isinstance(profile, dict) or not profile:
            return False
        if profile.get("height"):
            fighter.height = profile["height"]
        if profile.get("stance"):
            fighter.stance = profile["stance"]
        if profile.get("style") in STYLES:
            fighter.style = profile["style"]
        if profile.get("trait"):
            fighter.trait = profile["trait"]
        if profile.get("behaviour"):
            fighter.behaviour = profile["behaviour"]
        if profile.get("walk_weight") not in ("", None):
            fighter.walk_weight = int(profile["walk_weight"])
        details = dict(getattr(fighter, "detailed_skills", None) or {})
        for key, value in (profile.get("skill_minimums") or {}).items():
            details[key] = max(details.get(key, 50), int(value))
        for key, value in (profile.get("skill_values") or {}).items():
            details[key] = int(value)
        for group, value in (profile.get("group_minimums") or {}).items():
            for key in DETAILED_SKILL_GROUPS.get(group, ()):
                details[key] = max(details.get(key, 50), int(value))
        for key, bounds in (profile.get("skill_random_minimums") or {}).items():
            low, high = [int(item) for item in bounds]
            details[key] = max(details.get(key, 50), random.randint(low, high))
        for key, bounds in (profile.get("skill_random_maximums") or {}).items():
            low, high = [int(item) for item in bounds]
            details[key] = min(details.get(key, 50), random.randint(low, high))
        if details:
            fighter.detailed_skills = details
            self.sync_broad_skills_from_details(fighter)
        for key, value in (profile.get("broad_values") or {}).items():
            if hasattr(fighter, key):
                setattr(fighter, key, int(value))
        for key, value in (profile.get("broad_minimums") or {}).items():
            if hasattr(fighter, key):
                setattr(fighter, key, max(getattr(fighter, key), int(value)))
        for key, value in (profile.get("broad_maximums") or {}).items():
            if hasattr(fighter, key):
                setattr(fighter, key, min(getattr(fighter, key), int(value)))
        if profile.get("potential") not in ("", None):
            fighter.potential = max(fighter.overall, int(profile["potential"]))
        return True

    def real_fighter_stances(self):
        return {
            record["name"]: record["stance"]
            for record in self.starting_fighter_records()
            if record.get("stance")
        }

    def real_fighter_draws(self):
        return {
            record["name"]: int(record.get("record_d", 0) or 0)
            for record in self.starting_fighter_records()
            if int(record.get("record_d", 0) or 0)
        }

    def apply_real_fighter_profile(self, fighter, base_skill, record=None):
        record = record if isinstance(record, dict) else self.seed_fighter_record_for(fighter.name)
        if record:
            profile = {
                "rating": record.get("profile_rating", record.get("rating", base_skill)),
                "style": record.get("profile_style", record.get("style", fighter.style)),
                "stance": record.get("stance", ""),
            }
            if record.get("trait"):
                profile["trait"] = record["trait"]
            if record.get("behaviour"):
                profile["behaviour"] = record["behaviour"]
            if isinstance(record.get("skill_mods"), dict):
                profile["skills"] = record["skill_mods"]
        else:
            profile = dict(self.real_fighter_profiles().get(fighter.name, {}))
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
        default_stance = record.get("stance", "") if record else self.real_fighter_stances().get(fighter.name)
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
        signature_profile = self.apply_signature_real_fighter_profile(fighter, preserve_career=False, record=record)
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
        fighter.record_d = int(record.get("record_d", fighter.record_d) if record else self.real_fighter_draws().get(fighter.name, fighter.record_d) or 0)
        fighter.multi_sport_records = dict(fighter.multi_sport_records or {})
        fighter.multi_sport_records["MMA"] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
        fighter.rating_profile_version = 4

    def cage_empire_fighter_data(self):
        return self.starting_fighter_rows(owners=(PLAYER_PROMOTION_NAME,), placements=("player_roster",))

    def independent_fighter_data(self):
        return self.starting_fighter_rows(owners=("Free Agent",), placements=("free_agents",))

    def ufc_current_ranked_fighter_data(self):
        return self.starting_fighter_rows(owners=("UFC",), placements=("promotion",))

    def pfl_current_ranked_fighter_data(self):
        return self.starting_fighter_rows(owners=("PFL",), placements=("promotion",))

    def expanded_real_fighter_data(self):
        return self.real_fighter_data()

    def real_roster_depth_expansion_v3(self):
        return self.real_fighter_data()

    def real_roster_depth_expansion_v4(self):
        return self.real_fighter_data()

    def real_roster_depth_expansion_v5(self):
        return self.real_fighter_data()

    def real_roster_depth_expansion_v6(self):
        return self.real_fighter_data()

    def roster_depth_expansion(self):
        return self.real_fighter_data()

    def real_roster_depth_expansion_v2(self):
        return self.real_fighter_data()

    def nexgen_mma_prospect_names(self):
        return {
            record["name"] for record in self.starting_fighter_records()
            if record.get("nexgen_prospect")
        }

    def legend_fighter_data(self):
        return self.starting_fighter_rows(owners=("Legend",), placements=("free_agents",))

    def prime_legend_ages(self):
        seed_db = getattr(self, "_seed_fighter_database", {}) or {}
        records = seed_db.get("all_fighters", [])
        ages = {}
        if isinstance(records, list):
            for record in records:
                if not isinstance(record, dict):
                    continue
                if record.get("seed_org") == "Legend" or record.get("owner") == "Legend":
                    try:
                        ages[record["name"]] = int(record.get("age", 0) or 0)
                    except (KeyError, TypeError, ValueError):
                        continue
        if ages:
            return ages
        return {row[0]: row[5] for row in self.legend_fighter_data()}

    REAL_FIGHTER_AGE_CAP = 37

    def real_fighter_capped_age(self, name, age):
        """Pull a real fighter's seeded age back into a competitive range.

        The curated tables record fighters at roughly their real present-day
        age, so a new world opened with dozens of active fighters in their
        forties -- and a few approaching fifty -- who were past the point of
        being useful to sign or book. An explicit entry in
        historic_prime_age_overrides always wins; this only catches everyone
        who never got one, so adding a row to a roster table cannot quietly
        reintroduce the problem.

        Derived from the name so a given fighter is the same age in every save
        rather than being re-rolled, and returns None when no change is needed.
        """
        if age <= self.REAL_FIGHTER_AGE_CAP:
            return None
        spread = sum((index + 1) * ord(char) for index, char in enumerate(name))
        return 32 + spread % 6

    def historic_prime_age_overrides(self):
        return {
            record["name"]: int(record["prime_age"])
            for record in self.starting_fighter_records()
            if record.get("prime_age") is not None
        }

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
        fighter.stance = weighted_table_pick(GENERATED_STANCE_TABLE)
        fighter.trait = random.choice(TRAITS)
        fighter.behaviour = random.choice(BEHAVIOURS)
        fighter.camp = random.choice(CAMPS)
        fighter.exclusive = player_owned or random.random() < 0.55
        fighter.contract_type = "Exclusive" if fighter.exclusive else "Non-Exclusive"
        fighter.negotiation_heat = random.randint(0, 35)
        fighter.negotiation_persona = weighted_table_pick(NEGOTIATION_PERSONA_TABLE)
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
        region = profile.get("region") or self.combat_sport_region_for_name(name, sport)
        gender = profile.get("gender") or ("Female" if name in self.combat_sport_seed_women() else "Male")
        nationality = profile.get("nationality") or self.infer_nationality(name, region)
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
            gender=gender,
            region=region,
            nationality=nationality,
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
        self.assign_combat_sport_weight(sport, fighter, profile.get("weight_class", ""), reset_walk_weight=True)
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
            archetype = weighted_table_pick(CAREER_ARCHETYPE_TABLE)
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
        return max(1, min(99, base + random.randrange(-14, 15) + random.getrandbits(1)))

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
        return FIGHTER_SIGNATURE_DETAILED_SKILLS.get(
            getattr(fighter, "style", ""),
            DEFAULT_SIGNATURE_DETAILED_SKILLS,
        )

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
               weighted_table_pick(GENERATED_FIGHTER_AGE_TABLE))
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
            weight=self.game_weight_class(weight) if weight else random.choice(WEIGHTS),
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
        # Regional banks keep their own spellings, so "Angel Martin" and
        # "Angel Martín" are distinct keys here while reading as the same
        # fighter. Reserve both the name and its folded identity.
        key = self.fighter_name_key(base)
        if self.name_counts.get(base, 0) == 0 and self.name_counts.get(key, 0) == 0:
            self.name_counts[base] = 1
            self.name_counts[key] = 1
            return base
        gender = gender or ("Female" if first in FEMALE_FIRST_NAMES else "Male")
        return self.generate_clean_unique_name(gender, set(self.name_counts))

    def apply_authored_promotion_overrides(self, promotion, spec):
        """Apply every authored Promotion field after the usable seed baseline."""
        if not isinstance(spec, dict):
            return promotion
        for key in Promotion.__dataclass_fields__:
            if key in spec:
                value = spec[key]
                if value in ("", None) and isinstance(getattr(promotion, key), (bool, int, float)):
                    continue
                setattr(promotion, key, deepcopy(value))
        return promotion

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
            fighters = self.unique_fighter_rows(fighters)
            roster = []
            for row in fighters:
                fighter = self.create_real_fighter_from_seed_row(row, player_owned=False)
                roster.append(fighter)
                global_names.add(fighter.name)
                global_names.add(self.fighter_name_key(fighter.name))
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
            self.replace_generated_opening_slots(roster, name, global_names)
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
            promotion = Promotion(
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
            )
            self.apply_authored_promotion_overrides(promotion, spec if isinstance(spec, dict) else {})
            promotions.append(promotion)
        promotions.extend(self.seed_regional_feeder_promotions(global_names))
        return promotions

    def create_regional_feeder_fighter(self, region, used_names, gender, feeder_name="", weight=None):
        # The division has to be known here, not patched on afterwards: the
        # generator derives walk weight from whatever class the fighter is
        # built in, so a caller that overwrote .weight later left behind a
        # frame belonging to a completely unrelated division.
        pre_universe = bool(getattr(self, "_seeding_universe", False))
        fighter = self.create_generated_fighter(2, 22, 40, 70, weight=weight, gender=gender, region=region, apply_entry_balance=False, pre_universe=pre_universe)
        fighter.age = weighted_table_pick(REGIONAL_FEEDER_AGE_TABLE)
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
                if candidate not in used_names and self.fighter_name_key(candidate) not in used_names:
                    fighter.name = candidate
                    break
            else:
                self.avoid_name_collision(fighter, used_names)
        used_names.add(fighter.name)
        used_names.add(self.fighter_name_key(fighter.name))
        return fighter

    def apply_eurasian_origin(self, fighter, sub_region=None, used_names=None):
        """Give a fighter a Caucasus/Central Asian identity, name and style lean.

        Style is a weighted roll rather than a rule, so the region's wrestling
        and sambo reputation shows up in aggregate while still producing the
        occasional Georgian boxer or Dagestani kickboxer.
        """
        if not EURASIAN_NAME_POOLS:
            return fighter
        if sub_region not in EURASIAN_NAME_POOLS:
            options = [item for item in EURASIAN_REGION_WEIGHTS if item in EURASIAN_NAME_POOLS]
            sub_region = random.choices(options, weights=[EURASIAN_REGION_WEIGHTS[item] for item in options], k=1)[0]
        pool = EURASIAN_NAME_POOLS[sub_region]
        taken = used_names if used_names is not None else set()
        for _ in range(250):
            candidate = f"{random.choice(pool['male'])} {random.choice(pool['last'])}"
            if candidate not in taken:
                fighter.name = candidate
                break
        else:
            fighter.name = f"{random.choice(pool['male'])} {random.choice(pool['last'])}"
            self.avoid_name_collision(fighter, taken)
        self.apply_eurasian_identity(fighter, sub_region)
        styles = EURASIAN_REGION_STYLES.get(sub_region)
        if styles:
            fighter.style = random.choices([item[0] for item in styles], weights=[item[1] for item in styles], k=1)[0]
        # The circuit's identity is grappling-heavy volume: strong takedowns,
        # clinch control and work rate, with striking polish lagging behind so
        # the region produces specialists rather than uniformly better fighters.
        self.ensure_detailed_skills(fighter)
        for skill, delta in (("takedowns", 7), ("chain_wrestling", 7), ("clinch_control", 6),
                             ("top_control", 6), ("strength", 5), ("conditioning", 4), ("discipline", 4),
                             ("creative_kicks", -6), ("high_kick_technique", -5), ("feints", -4)):
            fighter.detailed_skills[skill] = max(1, min(99, fighter.detailed_skills.get(skill, 50) + delta))
        self.sync_broad_skills_from_details(fighter)
        return fighter

    def apply_eurasian_identity(self, fighter, sub_region):
        """Keep Caucasus/Central Asian origin fields aligned after a regional name roll."""
        russian_regions = {
            "Dagestan": "Makhachkala", "Chechnya": "Grozny", "Ingushetia": "Magas",
            "North Ossetia-Alania": "Vladikavkaz", "Kabardino-Balkaria": "Nalchik",
            "Karachay-Cherkessia": "Cherkessk",
        }
        origin_cities = {
            "Georgia": "Tbilisi", "Azerbaijan": "Baku", "Kazakhstan": "Almaty",
            "Uzbekistan": "Tashkent", "Armenia": "Yerevan", "Kyrgyzstan": "Bishkek",
            "Tajikistan": "Dushanbe", "Turkmenistan": "Ashgabat",
        }
        country = "Russia" if sub_region in russian_regions else sub_region
        hometown = russian_regions.get(sub_region, origin_cities.get(sub_region, sub_region))
        birth_region = COUNTRY_TO_REGION.get(country, "Russia")
        fighter.nationality = EURASIAN_REGION_NATIONALITY.get(sub_region, "Russian")
        fighter.birth_country = country
        fighter.birth_region = birth_region
        fighter.hometown = hometown
        fighter.market_origin = sub_region
        connections = list(getattr(fighter, "cultural_connections", []) or [])
        fighter.cultural_connections = list(dict.fromkeys([birth_region] + connections))
        popularity = dict(getattr(fighter, "regional_popularity", {}) or {})
        popularity[birth_region] = max(popularity.get(birth_region, 0), min(72, 18 + fighter.popularity // 3))
        fighter.regional_popularity = popularity
        return fighter

    def install_eurasian_headliner(self, roster, used_names, promo_name, region):
        record = next((record for record in self.starting_fighter_records()
                       if record.get("regional_feeder_headliner") and record.get("owner") == promo_name), None)
        if not record or any(fighter.name == record["name"] for fighter in roster):
            return None
        slot = next((fighter for fighter in roster if fighter.weight == record.get("weight") and fighter.gender == record.get("gender")), None)
        if slot is None:
            return None
        replacement = self.create_real_fighter_from_seed_row(self.seed_fighter_row_from_record(record), player_owned=False)
        replacement.camp = promo_name
        replacement.region = region
        replacement.generated = False
        replacement.rank_score = self.rank_value(replacement)
        roster[roster.index(slot)] = replacement
        used_names.add(replacement.name)
        return replacement

    def calibrate_fighter_overall(self, fighter, target, preserve=()):
        """Shift detailed skills until the derived overall lands on target.

        `Fighter.overall` is computed from the detailed skill groups, so a
        specific rating has to be reached by moving the underlying numbers
        rather than assigning the property. Keys in `preserve` define the
        fighter's signature strengths and are held at their authored values.
        """
        self.ensure_detailed_skills(fighter)
        adjustable = [key for key in fighter.detailed_skills if key not in set(preserve)]
        for _ in range(60):
            self.sync_broad_skills_from_details(fighter)
            gap = target - fighter.overall
            if gap == 0:
                return fighter
            step = 1 if gap > 0 else -1
            for key in adjustable:
                fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills[key] + step))
        self.sync_broad_skills_from_details(fighter)
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
            (EURASIAN_FIGHT_CIRCUIT_NAME, "Russia"),
        ]

    def regional_feeder_company_specs(self, company_section=None):
        """Return editable feeder specs while retaining a complete fallback set."""
        company_section = company_section if isinstance(company_section, dict) else self.universe_section("companies", {})
        supplied = company_section.get("regional_feeders", []) if isinstance(company_section, dict) else []
        by_name = {
            row.get("name"): dict(row)
            for row in supplied
            if isinstance(row, dict) and row.get("name")
        }
        specs = []
        for name, region in self.regional_feeder_specs():
            spec = by_name.pop(name, {"name": name, "region": region})
            spec.setdefault("region", region)
            specs.append(spec)
        specs.extend(by_name.values())
        return specs

    def seed_regional_feeder_promotions(self, global_names, specs=None):
        specs = list(specs or self.regional_feeder_company_specs())
        promotions = []
        for feeder_spec in specs:
            if isinstance(feeder_spec, dict):
                name = feeder_spec.get("name", "Regional MMA")
                region = feeder_spec.get("region", "USA")
            else:
                name, region = feeder_spec
                feeder_spec = {}
            roster = []
            male_only = name == EURASIAN_FIGHT_CIRCUIT_NAME
            for weight in WEIGHTS:
                # Give every active division a bookable base. The roster size
                # follows the division list, so adding a legitimate class does
                # not silently squeeze out another class.
                # A male-only circuit spends its whole allocation on the men's
                # divisions instead, so each one is meaningfully deeper.
                if male_only:
                    division_counts = (("Male", 8 if weight in ("Light Heavyweight", "Heavyweight") else 9),)
                else:
                    male_count = 5 if weight in ("Light Heavyweight", "Heavyweight") else 6
                    division_counts = (("Male", male_count), ("Female", 3))
                for gender, count in division_counts:
                    for _ in range(count):
                        fighter = self.create_regional_feeder_fighter(region, global_names, gender, feeder_name=name, weight=weight)
                        fighter.region = region
                        fighter.nationality = self.infer_nationality(fighter.name, region)
                        fighter.camp = name
                        if male_only:
                            self.apply_eurasian_origin(fighter, used_names=global_names)
                        roster.append(fighter)
                        global_names.add(fighter.name)
            if male_only:
                self.install_eurasian_headliner(roster, global_names, name, region)
            strategy = self.seed_promotion_strategy(name, "Regional Development")
            if male_only:
                strategy["description"] = EURASIAN_FIGHT_CIRCUIT_DESCRIPTION
            promotion = Promotion(
                name=name, region=region, size=24, cash=0, roster=roster,
                reputation="Regional Feeder",
                reputation_score=24, stability=70,
                show_history=[], belts=self.blank_belts(), interim_belts=self.blank_belts(), belt_history=self.blank_belt_history(),
                rules={"rounds": 3, "title_rounds": 3, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 4, "allow_mixed_gender": False, "active_fighter_target": 1200},
                broadcasters=[], weight_classes=list(WEIGHTS), show_personality="Regional Development", is_regional_feeder=True,
                strategy=strategy,
                executive=self.seed_promotion_executive(name),
                era_history=[],
            )
            self.apply_authored_promotion_overrides(promotion, feeder_spec)
            promotion.is_regional_feeder = True
            promotions.append(promotion)
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
            "finance_model_version": 3,
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

        bamma = next((promo for promo in self.promotions if promo.name == PLAYER_PROMOTION_NAME), None)
        if bamma is not None and not getattr(bamma, "closed_division_policy_set", False):
            bamma.closed_divisions = sorted(self.bamma_initial_closed_divisions())
            bamma.closed_division_policy_set = True

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
            pipeline_version = 2

        # Version 3 adds the male-only Eurasian circuit to saves that predate it.
        # Presence is checked against the live promotion list rather than the
        # rules version, because a save's stored rules are restored after this
        # repair runs and would otherwise let the circuit be seeded twice.
        existing_eurasian = [promo for promo in self.promotions if promo.name == EURASIAN_FIGHT_CIRCUIT_NAME]
        if len(existing_eurasian) > 1:
            for duplicate in existing_eurasian[1:]:
                self.promotions.remove(duplicate)
        elif (not existing_eurasian
                and EURASIAN_FIGHT_CIRCUIT_NAME not in defunct
                and self.player_company_name != EURASIAN_FIGHT_CIRCUIT_NAME):
            self.promotions.extend(self.seed_regional_feeder_promotions(
                self.active_fighter_names(),
                specs=[(EURASIAN_FIGHT_CIRCUIT_NAME, "Russia")],
            ))
            self.news.insert(0, f"{EURASIAN_FIGHT_CIRCUIT_NAME} opened as a new development circuit for Caucasus and Central Asian talent.")
        self.rules["regional_pipeline_version"] = 3

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
        regional_teams = {
            "USA": ["American Top Team", "AKA", "Kill Cliff FC"],
            "Canada": ["Tristar", "Niagara Top Team", "Northstar Combat"],
            "Brazil": ["Nova Uniao", "Chute Boxe", "Brazilian Top Team"],
            "Mexico": ["Lobo Gym", "Mexico City Combat", "Entram Gym"],
            "UK": ["SBG Ireland", "NexGen MMA", "London Shootfighters"],
            "Europe": ["Allstars Training Center", "MMA Factory Paris", "UFD Gym"],
            "Russia": ["Dagestan Fight School", "Red Fury Team", "Akhmat Fight Club"],
            "Japan": ["Krazy Bee", "Shootbox Japan", "Paraestra Tokyo"],
            "South Korea": ["Korean Top Team", "Busan Team MAD"],
            "Australia": ["City Kickboxing", "Freestyle Fighting Gym", "Sydney Elite MMA"],
            "Asia": ["Tiger Muay Thai", "Evolve MMA", "Team Lakay"],
            "Middle East": ["KHK MMA", "Abu Dhabi Combat Team", "Dubai Fight Lab"],
            "Africa": ["Team CIT", "Lagos Fight House", "Atlas Combat Club"],
        }
        return {
            region: {
                "economy": random.choice(economies),
                "legality": random.choice(legality),
                "drug_accuracy": random.choice([35, 50, 65, 80, 95]),
                "mma_love": random.randint(35, 85),
                "promo_benefit": REGION_PROMO_BENEFITS.get(region, {"media": 1.0, "gate": 1.0, "morale": 1}),
                "teams": list(regional_teams.get(region, [])),
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
        # The opening universe contains thousands of authored and generated
        # fighters. Do not begin a career with famous camps at 200-400% load,
        # which would suppress their training before the player acts. Later
        # roster movement remains subject to the normal crowding model.
        if int(getattr(self, "month", 2) or 2) == 1 and int(getattr(self, "week", 1) or 1) == 1:
            for gym in gyms:
                if gym.name == "Independent" or gym.capacity >= 500:
                    continue
                minimum_capacity = (max(0, gym.member_count) * 100 + 134) // 135
                if minimum_capacity > gym.capacity:
                    gym.capacity = minimum_capacity

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
            {"name": "Dana Holt", "role": "Matchmaker", "skill": 72, "salary": 8500, "morale": 76, "specialty": "Contender logic", "reputation": 68, "contract_months": 24},
            {"name": "Maya Quinn", "role": "Scout", "skill": 68, "salary": 6200, "morale": 80, "specialty": "Prospect eye", "reputation": 62, "contract_months": 24},
            {"name": "Reed Wallace", "role": "Doctor", "skill": 64, "salary": 7000, "morale": 70, "specialty": "Injury prevention", "reputation": 59, "contract_months": 24},
            {"name": "Felix Park", "role": "Marketing", "skill": 60, "salary": 5800, "morale": 74, "specialty": "Regional campaigns", "reputation": 56, "contract_months": 24},
        ]

    def create_starting_scout(self, region=None, company_scale="Regional"):
        base = {"Local": 56, "Regional": 64, "National": 72}.get(company_scale, 64)
        skill = max(48, min(84, base + random.randint(-8, 8)))
        name = f"{random.choice(FIRST_NAMES + FEMALE_FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        specialty = random.choice(["Prospect eye", "International network", "Women’s divisions"])
        profile = {"name": name, "role": "Scout", "skill": skill, "salary": max(4200, round(skill * random.randint(78, 112) / 10) * 10), "morale": random.randint(66, 88), "specialty": specialty, "reputation": max(42, min(88, skill + random.randint(-6, 8))), "region": region or random.choice(REGIONS)}
        profile.update({
            "fighter_judging": max(30, min(95, skill + random.randint(-7, 8))),
            "potential_judging": max(30, min(95, skill + random.randint(-8, 9) + (4 if specialty == "Prospect eye" else 0))),
            "efficiency": max(30, min(95, skill + random.randint(-8, 8))),
            "regional_knowledge": max(30, min(95, skill + random.randint(-6, 10) + (4 if profile["region"] == region else 0))),
            "networking": max(30, min(95, skill + random.randint(-7, 10) + (5 if specialty == "International network" else 0))),
            "reliability": max(30, min(95, skill + random.randint(-6, 8))),
            "negotiation": max(25, min(92, skill + random.randint(-10, 5))),
            "professionalism": max(30, min(95, skill + random.randint(-6, 8))),
        })
        return profile

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
        return {
            "name": name, "role": role, "skill": skill, "salary": max(3500, salary),
            "morale": random.randint(55, 92), "specialty": random.choice(specialties[role]),
            "reputation": random.randint(40, min(94, skill + 8)),
            "contract_months": random.randint(12, 36), "contract_type": "Exclusive",
        }

    def seed_staff_candidates(self):
        return [self.create_staff_candidate() for _ in range(14)]

    def seed_owner_goals(self):
        return [
            {"goal": "Keep cash above $150,000", "metric": "cash", "target": 150000, "deadline": 12, "status": "Active"},
            {"goal": "Reach company popularity 50", "metric": "popularity", "target": 50, "deadline": 18, "status": "Active"},
            {"goal": "Run at least 4 shows", "metric": "shows", "target": 4, "deadline": 12, "status": "Active"},
        ]
