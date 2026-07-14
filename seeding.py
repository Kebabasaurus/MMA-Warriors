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


class SeedMixin:
    def active_universe_marker(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        return DATABASE_DIR / "active_universe.txt"

    def universe_database_path(self, name="Default Universe"):
        return self.seed_database_file(f"{self.safe_filename(name) if hasattr(self, 'safe_filename') else str(name).replace(' ', '_')}.universe.json")

    def default_player_media(self):
        return [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]

    def default_promotion_specs(self, fighter_db=None):
        data = (fighter_db or self.build_seed_fighter_database()).get("promotions", self.expanded_real_fighter_data())
        return [
            {"name": "Ultimate Fighting Championship", "region": "USA", "size": 96, "cash": 30_000_000, "reputation": "Global", "roster_key": "UFC", "target_roster_size": 170, "personality": "Super Shows"},
            {"name": "Professional Fighters League", "region": "USA", "size": 76, "cash": 8_500_000, "reputation": "Global", "roster_key": "PFL", "target_roster_size": 110, "personality": "Seasonal"},
            {"name": "ONE Championship", "region": "Asia", "size": 78, "cash": 9_000_000, "reputation": "Global", "roster_key": "ONE Championship", "target_roster_size": 120, "personality": "Big Names"},
            {"name": "RIZIN Fighting Federation", "region": "Japan", "size": 72, "cash": 6_000_000, "reputation": "International", "roster_key": "RIZIN Fighting Federation", "target_roster_size": 105, "personality": "Super Shows"},
            {"name": "KSW", "region": "Europe", "size": 70, "cash": 5_000_000, "reputation": "International", "roster_key": "KSW", "target_roster_size": 105, "personality": "Star Builder"},
            {"name": "Cage Warriors", "region": "UK", "size": 66, "cash": 2_500_000, "reputation": "International", "roster_key": "Cage Warriors", "target_roster_size": 115, "personality": "Prospect Builder"},
            {"name": "Legacy Fighting Alliance", "region": "USA", "size": 62, "cash": 1_800_000, "reputation": "National", "roster_key": "Legacy Fighting Alliance", "target_roster_size": 100, "personality": "Prospect Builder"},
            {"name": "Oktagon MMA", "region": "Europe", "size": 70, "cash": 4_800_000, "reputation": "International", "roster_key": "Oktagon MMA", "target_roster_size": 105, "personality": "Star Builder"},
            {"name": "BRAVE Combat Federation", "region": "Asia", "size": 64, "cash": 3_100_000, "reputation": "International", "roster_key": "BRAVE Combat Federation", "target_roster_size": 100, "personality": "Prospect Builder"},
            {"name": "Absolute Championship Akhmat", "region": "Europe", "size": 66, "cash": 3_600_000, "reputation": "International", "roster_key": "Absolute Championship Akhmat", "target_roster_size": 100, "personality": "Seasonal"},
        ]

    def build_universe_database_pack(self, name="Default Universe"):
        fighter_db = self.build_seed_fighter_database()
        combat_db = self.build_combat_sport_database()
        return {
            "schema": 2,
            "type": "universe_database",
            "database_name": name,
            "notes": "Editable universe database pack. Clone this file for real-life, fake, fantasy, or historic universes. Sections are intentionally enclosed so companies, fighters, combat sports, media, and regions can evolve independently.",
            "sections": {
                "fighters": fighter_db,
                "combat_sports": combat_db,
                "companies": {
                    "player_company": {"name": PLAYER_PROMOTION_NAME, "region": "USA", "reputation": "Regional Player Company", "popularity": 38, "stability": 52, "cash": 275000},
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
                    "rights_packages": [
                        {"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"},
                        {"name": "Cable Sports", "reach": 42, "fee": 32000, "type": "Cable"},
                        {"name": "Global Fight Pass", "reach": 70, "fee": 85000, "type": "Streaming"},
                    ],
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
        return {
            "schema": 1,
            "notes": "Canonical combat-sport seed database. Muay Thai also imports the Lethwei list as a linked striking roster.",
            "rosters": self.builtin_combat_sport_real_roster_data(),
        }

    def load_combat_sport_database(self):
        section = self.universe_section("combat_sports", None)
        if section:
            rosters = section.get("rosters", section)
            if isinstance(rosters, dict) and "Boxing" in rosters:
                return rosters
        path = self.seed_database_file("combat_sport_database.json")
        if not path.exists():
            self.write_seed_database_file(path, self.build_combat_sport_database())
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rosters = data.get("rosters", data)
            if not isinstance(rosters, dict) or "Boxing" not in rosters:
                raise ValueError("combat sport database is missing rosters")
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
                fighter.trait = random.choice(["Fan Favourite", "Marketable", "Clutch", "Big Finisher"])
                fighter.media_heat = random.randint(20, 55)
                fighter.popularity = min(100, fighter.popularity + random.randint(2, 8))
            else:
                fighter.popularity = max(8, fighter.popularity - random.randint(4, 14))
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
        fighter.detailed_skills = None
        self.apply_real_fighter_profile(fighter, skill)
        if fighter.name == "Matthew Green":
            fighter.height = "5'10"
            fighter.stance = "Southpaw"
            fighter.trait = "Prospect Mindset"
            fighter.behaviour = "Dynamic Attacker"
            fighter.walk_weight = 185
            fighter.striking = max(fighter.striking, 92)
            fighter.wrestling = max(fighter.wrestling, 82)
            fighter.grappling = max(fighter.grappling, 82)
            fighter.cardio = max(fighter.cardio, 88)
            fighter.chin = max(fighter.chin, 86)
            for key in MENTAL_SKILLS + PHYSICAL_SKILLS:
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), 84)
            for key in ("high_kick_power", "high_kick_speed", "high_kick_technique", "low_kick_power", "creative_kicks"):
                fighter.detailed_skills[key] = max(fighter.detailed_skills.get(key, 50), 94)
            fighter.power = max(fighter.power, 92)
            self.sync_broad_skills_from_details(fighter)
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
            "Mandy Bohm", "Lone'er Kavanagh", "Kennedy Freeman", "Awa Sow",
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
            "Joanna Jedrzejczyk", "Gina Carano", "Lucia Szabova",
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
        market_region = market_region if market_region in REGIONS else random.choice(REGIONS)
        links = [region for region in REGIONAL_MIGRATION_LINKS.get(market_region, []) if region in REGIONS and region != market_region]
        outsiders = [region for region in REGIONS if region not in links and region != market_region]
        choices = [market_region] + links + outsiders
        weights = [76] + [max(3, 18 / max(1, len(links)))] * len(links) + [max(0.4, 6 / max(1, len(outsiders)))] * len(outsiders)
        return random.choices(choices, weights=weights, k=1)[0]

    def assign_regional_identity(self, fighter, market_region=None, birth_region=None, generated=False, force=False):
        """Give a fighter a persistent origin, migration story, and market appeal."""
        if getattr(fighter, "birth_region", "") and not force:
            return fighter
        market_region = market_region if market_region in REGIONS else (fighter.region if fighter.region in REGIONS else random.choice(REGIONS))
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
        fighter.birth_country = REGION_COUNTRIES.get(birth_region, birth_region)
        fighter.birth_region = birth_region
        fighter.hometown = random.choice(REGION_CITIES.get(birth_region, [birth_region]))
        fighter.residence = residence
        fighter.training_location = training_region
        fighter.fighting_base = residence
        fighter.cultural_connections = connections
        fighter.regional_popularity = popularity
        fighter.home_event_history = getattr(fighter, "home_event_history", None) or []
        fighter.region = residence  # legacy shorthand: current fighting base
        if generated:
            fighter.nationality = self.infer_nationality(fighter.name, birth_region)
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
            "Conor McGregor": {"rating": 82, "style": "Boxer", "trait": "Showman", "behaviour": "Counter", "skills": {"punch_power": 8, "punch_technique": 7, "hand_speed": 6, "confidence": 7}},
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
        fighter.stance = profile.get("stance", fighter.stance)
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
        fighter.finishing_instinct = max(fighter.finishing_instinct, min(99, rating + (8 if fighter.trait in ("Knockout Artist", "Big Finisher", "Submission Ace") else 2)))
        fighter.fight_iq = max(fighter.fight_iq, min(99, rating + mental - 2))
        fighter.rating_profile_version = 2

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
            ("Conor McGregor", "Lightweight", "UFC", 99, 82, 37, 22, 7, "Europe", "Boxer"),
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
            ("Matthew Green", "Middleweight", "BAMMA", 45, 85, 17, 0, 0, "UK", "Kickboxer"),
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
        }
        for company, rows in extras.items():
            existing = {row[0] for row in data[company]}
            for row in rows:
                if row[0] not in existing:
                    data[company].append(row)
                    existing.add(row[0])
        return data

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

    def enrich_fighter(self, fighter, player_owned=False):
        if fighter.region == "USA" and not player_owned:
            fighter.region = random.choice(REGIONS)
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
        fighter.potential = max(fighter.overall, min(98, fighter.overall + random.randint(2, 18)))
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
        if sport in ("Muay Thai", "Lethwei", "Kickboxing"):
            return "Asia"
        if sport == "Brazilian Jiu-Jitsu":
            return "Brazil"
        if sport == "Wrestling":
            return random.choice(["USA", "Europe", "Asia"])
        return random.choice(REGIONS)

    def create_real_combat_sport_athlete(self, name, sport, promotion, index):
        women = {
            "Jorina Baars", "Lucia Rijker", "Denise Kielholtz", "Jemyma Betrian", "Anissa Meksen",
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
        rating = max(68, 96 - index // 3 + random.randint(-2, 2))
        if index < 5:
            rating = max(rating, 94 - index)
        age = 27 + (index % 7)
        wins = max(8, 62 - index + random.randint(-4, 8))
        losses = max(0, min(18, index // 4 + random.randint(0, 4)))
        draws = random.randint(0, 3 if sport in ("Muay Thai", "Lethwei", "Boxing") else 1)
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
            weight=random.choice(WEIGHTS),
            age=age,
            record_w=wins,
            record_l=losses,
            record_d=draws,
            striking=max(25, min(99, striking)),
            wrestling=max(25, min(99, wrestling)),
            grappling=max(25, min(99, grappling)),
            cardio=max(45, min(99, rating + random.randint(-4, 5))),
            chin=max(45, min(99, rating + random.randint(-5, 7))),
            popularity=max(18, min(99, rating + 2 - index // 2 + random.randint(-4, 6))),
            momentum=random.randint(0, 5),
            morale=random.randint(62, 92),
            purse=max(4000, (rating - 45) * 1800),
            gender="Female" if name in women else "Male",
            region=region,
            nationality=self.infer_nationality(name, region),
            style=style_by_sport.get(sport, "Well-Rounded"),
            trait=random.choice(["Title Mentality", "Veteran Savvy", "Warrior Spirit", "Clutch", "Technical Learner"]),
            behaviour=random.choice(["Pressure Fighter", "Technical Counter", "Dynamic Attacker", "Patient Finisher"]),
            camp=random.choice(CAMPS),
            primary_discipline=sport,
            combat_background=sport,
            sport_employer=promotion,
            multi_sport_records={sport: f"{wins}-{losses}-{draws}"},
            crossover_history=[],
            contract_months=0,
            exclusive=False,
            contract_type="Sport Contract",
            star_quality=max(20, min(99, rating + random.randint(-5, 8))),
            charisma=max(20, min(99, rating - 8 + random.randint(-7, 12))),
            professionalism=random.randint(58, 96),
            media_presence=max(15, min(99, rating - 4 + random.randint(-8, 10))),
            sponsor_appeal=max(15, min(99, rating - 3 + random.randint(-6, 10))),
            finishing_instinct=max(35, min(99, rating + random.randint(-7, 10))),
            injury_proneness=random.randint(8, 34),
        )
        if sport == "Lethwei":
            fighter.power = min(99, rating + 5)
            fighter.toughness = min(99, rating + 7)
            fighter.multi_sport_records["Muay Thai"] = "0-0-0"
        fighter.portrait_bg, fighter.portrait_accent = self.generate_portrait_palette(fighter.name)
        fighter.walk_weight = self.default_walk_weight(fighter)
        fighter.fight_history = []
        fighter.annual_overalls = {"2026": fighter.overall}
        fighter.motivation = random.randint(64, 94)
        fighter.camp_quality = self.gym_quality(fighter.camp)
        fighter.fight_iq = max(45, min(99, rating + random.randint(-5, 6)))
        fighter.power = max(getattr(fighter, "power", 65), min(99, round(fighter.striking * 0.72 + fighter.chin * 0.14 + random.randint(-4, 8))))
        fighter.takedown_defence = max(40, min(99, round(fighter.wrestling * 0.7 + fighter.cardio * 0.15 + random.randint(-6, 8))))
        fighter.ground_control = max(40, min(99, round((fighter.wrestling + fighter.grappling) / 2 + random.randint(-5, 7))))
        fighter.submissions = max(35, min(99, round(fighter.grappling * 0.84 + random.randint(-8, 8))))
        fighter.submission_defence = max(38, min(99, round(fighter.grappling * 0.62 + fighter.wrestling * 0.18 + random.randint(-6, 8))))
        fighter.recovery = max(40, min(99, round(fighter.chin * 0.58 + random.randint(-6, 8))))
        fighter.toughness = max(getattr(fighter, "toughness", 65), min(99, round(fighter.chin * 0.74 + fighter.cardio * 0.16 + random.randint(-4, 8))))
        self.generate_detailed_skills(fighter)
        self.sync_broad_skills_from_details(fighter)
        fighter.potential = max(fighter.overall, min(99, fighter.overall + random.randint(1, 9)))
        self.assign_career_arc(fighter)
        fighter.rank_score = self.rank_value(fighter)
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
            worlds[sport] = {
                "promotion": promotion,
                "roster": roster,
                "rankings": [fighter.name for fighter in ranked[:15]],
                "champion": ranked[0].name if ranked else "",
                "events": 0,
                "records": {},
                "awards": [],
                "hall_of_fame": [],
                "media": [f"{promotion} announces a real-name {sport} roster built around {ranked[0].name}." if ranked else f"{promotion} launches."],
                "prospects": [],
                "event_history": [],
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
                is_flagship_filler = fighter.sport_employer == promotion and fighter.name not in seeded_by_name
                if is_flagship_filler:
                    continue
                if fighter.name in seen:
                    continue
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
            for key, value in {"events": 0, "records": {}, "awards": [], "hall_of_fame": [], "media": [], "prospects": [], "event_history": []}.items():
                world.setdefault(key, value if not isinstance(value, (list, dict)) else value.copy())
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
        longevity = round((conditioning + resilience + dedication + fighter.professionalism) / 42)
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

    def create_generated_fighter(self, min_pop=6, max_pop=45, min_skill=45, max_skill=82, weight=None, gender=None, region=None):
        # The world deliberately creates more men than women. Female divisions
        # remain healthy, but a century simulation should not drift to 50/50
        # solely because the depth-repair routines create equal buckets.
        gender = gender or ("Female" if random.random() < 0.18 else "Male")
        market_region = region if region in REGIONS else random.choice(REGIONS)
        birth_region = self.weighted_birth_region(market_region)
        first, last = self.generated_name_parts(gender, birth_region)
        name = self.unique_generated_name(first, last)
        base = random.randint(min_skill, max_skill)
        # New entrants are predominantly prospects. Established veterans should
        # emerge through records and regional careers, not every generated name.
        age = random.choices(range(18, 34), weights=[11, 13, 15, 16, 16, 15, 13, 11, 9, 8, 7, 6, 5, 4, 3, 2], k=1)[0]
        fighter = Fighter(
            name=name,
            weight=weight or random.choice(WEIGHTS),
            age=age,
            record_w=random.randint(0, 18),
            record_l=random.randint(0, 7),
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

    def unique_generated_name(self, first, last):
        base = f"{first} {last}"
        if self.name_counts.get(base, 0) == 0:
            self.name_counts[base] = 1
            return base
        gender = "Female" if first in FEMALE_FIRST_NAMES else "Male"
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
                fighter.camp = name
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

    def create_regional_feeder_fighter(self, region, used_names, gender):
        fighter = self.create_generated_fighter(2, 22, 40, 70, gender=gender, region=region)
        fighter.age = random.choices(range(16, 27), weights=[6, 9, 12, 12, 11, 10, 8, 6, 5, 3, 2], k=1)[0]
        fighter.record_w = random.randint(0, 6)
        fighter.record_l = random.randint(0, min(4, fighter.record_w + 1))
        fighter.record_d = 0
        fighter.potential = min(96, max(fighter.overall + random.randint(8, 24), fighter.potential))
        fighter.popularity = min(24, fighter.popularity)
        fighter.purse = max(500, min(4000, fighter.purse // 3))
        fighter.contract_months = 0
        fighter.exclusive = False
        fighter.contract_type = "Developmental"
        fighter.feeder_origin = region
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

    def seed_regional_feeder_promotions(self, global_names):
        specs = [
            ("Japan Fight Circuit", "Japan"),
            ("UK Regional MMA", "UK"),
            ("North American Fighting League", "USA"),
            ("European Challenge MMA", "Europe"),
            ("Asia Rising Championship", "Asia"),
            ("Brazilian Combat Circuit", "Brazil"),
            ("Latin American MMA League", "Mexico"),
            ("Canadian Fight Alliance", "Canada"),
            ("Oceania Combat League", "Australia"),
            ("African MMA Championship", "Europe"),
        ]
        promotions = []
        for name, region in specs:
            roster = []
            for weight in WEIGHTS:
                for gender, count in (("Male", 5), ("Female", 3)):
                    for _ in range(count):
                        fighter = self.create_regional_feeder_fighter(region, global_names, gender)
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
            "Absolute Championship Akhmat": (59, 21), "BAMMA": (43, 28),
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
            "growth_ceiling": {
                "Ultimate Fighting Championship": 100, "Professional Fighters League": 88, "ONE Championship": 92,
                "RIZIN Fighting Federation": 88, "KSW": 84, "Cage Warriors": 78, "Legacy Fighting Alliance": 74,
                "Oktagon MMA": 84, "BRAVE Combat Federation": 80, "Absolute Championship Akhmat": 80,
                "BAMMA": 72,
            }.get(name, 42 if show_personality == "Regional Development" else 76),
            "last_review_month": 0,
        }

    def repair_core_promotions(self):
        self.promotions = [promo for promo in self.promotions if promo.name != self.player_company_name]
        names = {promo.name for promo in self.promotions}
        required = ["Cage Warriors", "ONE Championship", "RIZIN Fighting Federation", "KSW", "Legacy Fighting Alliance", "Oktagon MMA", "BRAVE Combat Federation", "Absolute Championship Akhmat", "Japan Fight Circuit", "UK Regional MMA", "North American Fighting League", "European Challenge MMA", "Asia Rising Championship", "Brazilian Combat Circuit", "Latin American MMA League", "Canadian Fight Alliance", "Oceania Combat League", "African MMA Championship"]
        defunct = set(getattr(self, "defunct_promotions", []))
        missing = [name for name in required if self.player_company_name != name and name not in names and name not in defunct]
        if missing:
            seeded = self.seed_promotions()
            for company_name in missing:
                promo = next((item for item in seeded if item.name == company_name), None)
                if promo:
                    self.promotions.append(promo)
            self.news.insert(0, f"World database repaired: restored missing promotions ({', '.join(missing)}).")

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
            "Japan": ["Tokyo", "Osaka", "Saitama", "Fukuoka"],
            "Australia": ["New South Wales", "Victoria", "Queensland", "Western Australia"],
            "Asia": ["Thailand", "Singapore", "Philippines", "South Korea"],
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
                    "Japan": "Respectful combat tradition", "Australia": "Festival fight fans", "Asia": "Global crossover audience",
                }.get(region, "Local MMA community"),
                "crowd_preference": {
                    "USA": "Stars and finishes", "Canada": "Competitive skill", "Brazil": "Local heroes and submissions",
                    "Mexico": "Aggressive action", "UK": "Rivalries and underdogs", "Europe": "Technical matchups",
                    "Japan": "Respect and elite technique", "Australia": "High-energy action", "Asia": "International stars",
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
            ("London Shootfighters", "UK", "London", 77, 74, ["Wrestling", "Kickboxing", "BJJ"], "Alex Turner", 75, 2200, 70, 76, 65),
            ("Altitude Fight Team", "Europe", "Amsterdam", 79, 76, ["Kickboxing", "Conditioning", "Clinch"], "Mika De Vries", 70, 2300, 69, 78, 64),
            ("Mexico City Combat", "Mexico", "Mexico City", 74, 66, ["Boxing", "Wrestling", "Prospect Development"], "Santiago Reyes", 65, 1500, 73, 70, 57),
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

    def sync_gym_membership(self):
        for gym in getattr(self, "gyms", []):
            gym.member_count = 0
        all_fighters = list(getattr(self, "roster", [])) + list(getattr(self, "free_agents", []))
        for promo in getattr(self, "promotions", []):
            all_fighters.extend(promo.roster)
        for fighter in all_fighters:
            gym = self.gym_by_name(fighter.camp)
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
