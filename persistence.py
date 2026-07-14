import json
import logging
import os
import platform
import random
import shutil
import sys
import threading
import traceback
from collections import Counter
from datetime import datetime
from logging.handlers import RotatingFileHandler
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion


LOGGER = logging.getLogger("mma_warriors")
_CRASH_APP = None


def _crash_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def atomic_write_text(path, contents):
    """Write a file without leaving partial JSON after a power loss or crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(contents, encoding="utf-8")
    os.replace(temporary, path)


def atomic_write_json(path, data):
    atomic_write_text(path, json.dumps(data, indent=2))


def configure_runtime_logging():
    """Create durable, size-limited logs for both source and packaged builds."""
    if getattr(configure_runtime_logging, "configured", False):
        return
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False
        handler = RotatingFileHandler(
            LOG_DIR / "mma_warriors.log",
            maxBytes=1_500_000,
            backupCount=4,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ))
        LOGGER.addHandler(handler)
        configure_runtime_logging.configured = True
        LOGGER.info("Logging started | Python %s | frozen=%s | app_dir=%s | data_dir=%s", sys.version.split()[0], getattr(sys, "frozen", False), APP_DIR, DATA_DIR)
    except Exception:
        # Logging must never prevent the game starting.
        pass


def register_crash_app(app):
    global _CRASH_APP
    _CRASH_APP = app


def _crash_context(app=None):
    app = app or _CRASH_APP
    lines = [
        f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Game: {GAME_NAME}",
        f"Python: {sys.version}",
        f"Platform: {platform.platform()}",
        f"Executable: {sys.executable}",
        f"Working directory: {os.getcwd()}",
    ]
    if app:
        lines.extend([
            f"Calendar: Month {getattr(app, 'month', '?')}, Week {getattr(app, 'week', '?')}",
            f"Player company: {getattr(app, 'player_company_name', '?')}",
            f"Theme: {getattr(app, 'theme_name', '?')}",
            f"Roster/free agents: {len(getattr(app, 'roster', []))}/{len(getattr(app, 'free_agents', []))}",
            f"Scheduled events: {len(getattr(app, 'scheduled_events', []))}",
        ])
    return "\n".join(lines)


def write_crash_report(exc_type, exc_value, exc_tb, source="Unhandled exception", app=None):
    """Persist a standalone report and append a concise entry to the runtime log."""
    configure_runtime_logging()
    trace = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    report = f"{_crash_context(app)}\nSource: {source}\n\nTraceback:\n{trace}"
    report_path = None
    try:
        CRASH_DIR.mkdir(parents=True, exist_ok=True)
        report_path = CRASH_DIR / f"crash_{_crash_stamp()}.txt"
        atomic_write_text(report_path, report)
    except Exception:
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            report_path = SAVE_DIR / "crash_log.txt"
            with report_path.open("a", encoding="utf-8") as handle:
                handle.write(f"\n{'=' * 72}\n{report}\n")
        except Exception:
            report_path = None
    try:
        LOGGER.error("%s: %s: %s | report=%s", source, exc_type.__name__, exc_value, report_path, exc_info=(exc_type, exc_value, exc_tb))
    except Exception:
        pass
    return report_path, trace


def install_global_exception_handlers():
    """Catch failures outside Tk callbacks, including worker-thread failures."""
    def handle_main_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        write_crash_report(exc_type, exc_value, exc_tb, "Python main-thread exception")

    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
        write_crash_report(args.exc_type, args.exc_value, args.exc_traceback, f"Background thread exception ({args.thread.name})")

    sys.excepthook = handle_main_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = handle_thread_exception


class PersistenceMixin:
    def handle_uncaught_exception(self, exc_type, exc_value, exc_tb):
        """Global guard so a stray error never silently kills a windowed build.

        Logs the traceback, tries an emergency autosave to a separate file so a
        good quick-save is never clobbered, then tells the player what happened.
        """
        report_path, message = write_crash_report(exc_type, exc_value, exc_tb, "Tkinter callback", self)
        crash_note = f"\nCrash report: {report_path}." if report_path else "\nA crash report could not be written."
        try:
            data = self.serialize_world()
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            autosave_path = SAVE_DIR / f"crash_autosave_{_crash_stamp()}.json"
            atomic_write_json(autosave_path, data)
            crash_note += f"\nAn emergency autosave was written to {autosave_path}."
        except Exception as autosave_error:
            LOGGER.exception("Emergency crash autosave failed: %s", autosave_error)
            crash_note += "\nEmergency autosave could not be written."
        try:
            messagebox.showerror(
                "Something went wrong",
                "MMA Warriors hit an unexpected error and recovered instead of closing."
                f"\n\n{exc_type.__name__}: {exc_value}{crash_note}",
            )
        except Exception:
            print(message, file=sys.stderr)

    def save_game(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        data = self.serialize_world()
        data["_save_meta"] = self.save_metadata("Quick Save")
        backup_path = SAVE_FILE.with_name("savegame.previous.json")
        try:
            if SAVE_FILE.exists():
                shutil.copy2(SAVE_FILE, backup_path)
                self.backup_save_file(SAVE_FILE, "before_quick_save")
            atomic_write_json(SAVE_FILE, data)
            self.prune_save_backups()
        except Exception as exc:
            LOGGER.exception("Quick save failed: %s", exc)
            messagebox.showerror("Save failed", f"The existing save was left untouched.\n\n{type(exc).__name__}: {exc}")
            return
        messagebox.showinfo("Saved", f"Quick saved to {SAVE_FILE.resolve()}\n\nPrevious quick save: {backup_path.name}")

    def save_metadata(self, slot_name=""):
        return {
            "schema": 1,
            "slot_name": slot_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "company": getattr(self, "player_company_name", PLAYER_PROMOTION_NAME),
            "month": getattr(self, "month", 1),
            "week": getattr(self, "week", 1),
            "cash": getattr(self, "cash", 0),
            "active_universe": self.active_universe_database_path().name if hasattr(self, "active_universe_database_path") else "",
        }

    def save_backup_dir(self):
        path = SAVE_DIR / "Backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def backup_save_file(self, path, reason="manual"):
        path = Path(path)
        if not path.exists():
            return None
        backup_dir = self.save_backup_dir()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = backup_dir / f"{path.stem}_{reason}_{stamp}.json"
        shutil.copy2(path, target)
        manifest = target.with_suffix(".manifest.json")
        manifest.write_text(json.dumps({
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": str(path),
            "backup": str(target),
            "reason": reason,
        }, indent=2), encoding="utf-8")
        return target

    def prune_save_backups(self, keep=30):
        backup_dir = self.save_backup_dir()
        backups = sorted(backup_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        data_backups = [item for item in backups if not item.name.endswith(".manifest.json")]
        for old in data_backups[keep:]:
            try:
                manifest = old.with_suffix(".manifest.json")
                old.unlink()
                if manifest.exists():
                    manifest.unlink()
            except Exception:
                LOGGER.exception("Could not prune old save backup: %s", old)

    def serialize_world(self):
        self.ensure_all_company_champions()
        return {
            "player_company_name": self.player_company_name,
            "spectator_mode": getattr(self, "spectator_mode", False),
            "player_region": self.player_region,
            "player_reputation": self.player_reputation,
            "theme_name": self.theme_name,
            "cash": self.cash,
            "company_pop": self.company_pop,
            "company_stability": self.company_stability,
            "month": self.month,
            "week": self.week,
            "roster": [asdict(f) for f in self.roster],
            "free_agents": [asdict(f) for f in self.free_agents],
            "promotions": [asdict(p) for p in self.promotions],
            "combat_sport_worlds": {sport: {**world, "roster": [asdict(fighter) for fighter in world.get("roster", [])]} for sport, world in getattr(self, "combat_sport_worlds", {}).items()},
            "player_combat_divisions": getattr(self, "player_combat_divisions", {}),
            "regions": self.regions,
            "gyms": [asdict(g) for g in getattr(self, "gyms", [])],
            "result_history": self.result_history,
            "result_records": self.result_records,
            "ai_event_archive": self.ai_event_archive,
            "independent_showcase_counter": getattr(self, "independent_showcase_counter", 1),
            "retired_fighters": [asdict(f) for f in self.retired_fighters],
            "finance": self.finance,
            "engine_settings": self.engine_settings,
            "staff": self.staff,
            "staff_candidates": self.staff_candidates,
            "scouting": self.scouting,
            "scouting_reports": getattr(self, "scouting_reports", {}),
            "achievement_log": getattr(self, "achievement_log", []),
            "historical_records": getattr(self, "historical_records", {}),
            "fanbase": getattr(self, "fanbase", {}),
            "academy": getattr(self, "academy", {}),
            "inbox": self.inbox,
            "owner_goals": self.owner_goals,
            "belts": self.belts,
            "interim_belts": self.interim_belts,
            "belt_history": self.belt_history,
            "rules": self.rules,
            "broadcasters": self.broadcasters,
            "weight_classes": self.weight_classes,
            "post_show_bonuses": self.post_show_bonuses,
            "scheduled_events": self.scheduled_events,
            "pending_rebookings": getattr(self, "pending_rebookings", []),
            "news": self.news,
            "world_chronicle": getattr(self, "world_chronicle", []),
            "defunct_promotions": getattr(self, "defunct_promotions", []),
            "event_log": self.event_log,
            "season_stats": getattr(self, "season_stats", {}),
            "awards_history": getattr(self, "awards_history", []),
            "fight_timer_delay": self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 2150,
        }

    def load_game(self):
        if not SAVE_FILE.exists():
            messagebox.showinfo("No save", "No savegame.json exists yet.")
            return
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            self.apply_world_data(data)
        except Exception as exc:
            backup_path = SAVE_FILE.with_name("savegame.previous.json")
            if backup_path.exists():
                try:
                    self.apply_world_data(json.loads(backup_path.read_text(encoding="utf-8")))
                    self.booked.clear()
                    self.refresh_all()
                    self.write_log()
                    messagebox.showwarning("Backup loaded", "The current quick save could not be read. The previous quick save was loaded instead.")
                    LOGGER.warning("Quick save failed to load; restored previous backup: %s", exc)
                    return
                except Exception:
                    LOGGER.exception("Quick-save backup could not be loaded after primary failure")
            LOGGER.exception("Quick save could not be loaded: %s", exc)
            messagebox.showerror(
                "Load failed",
                f"That save could not be loaded and was left untouched.\n\n{type(exc).__name__}: {exc}",
            )
            return
        self.booked.clear()
        self.refresh_all()
        self.write_log()

    def apply_world_data(self, data):
        self.player_company_name = data.get("player_company_name", PLAYER_PROMOTION_NAME)
        if self.player_company_name == "Cage Empire":
            self.player_company_name = PLAYER_PROMOTION_NAME
        self.spectator_mode = bool(data.get("spectator_mode", self.player_company_name == "Spectator"))
        self.player_region = data.get("player_region", "USA")
        self.player_reputation = data.get("player_reputation", "Regional Player Company")
        self.theme_name = data.get("theme_name", getattr(self, "theme_name", "Fight Night"))
        if hasattr(self, "theme_name_var"):
            self.theme_name_var.set(self.theme_name)
            self.configure_style()
            self.retheme_plain_widgets(self.root)
        self.cash = data.get("cash", 275_000)
        self.company_pop = data.get("company_pop", 38)
        self.company_stability = data.get("company_stability", max(5, min(99, self.cash // 5000)))
        self.month = data.get("month", 1)
        self.week = data.get("week", 1)
        self.roster = [Fighter(**row) for row in data.get("roster", [])]
        self.free_agents = [Fighter(**row) for row in data.get("free_agents", [])]
        for fighter in self.roster + self.free_agents:
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.promotions = []
        self.defunct_promotions = list(data.get("defunct_promotions", []))
        for row in data.get("promotions", []):
            row["roster"] = [Fighter(**fighter) for fighter in row.get("roster", [])]
            row.setdefault("stability", max(5, min(99, row.get("cash", 0) // 20000)))
            row.setdefault("strategy", self.seed_promotion_strategy(row.get("name", ""), row.get("show_personality", "Balanced")))
            row.setdefault("strategic_rival", "")
            row.setdefault("executive", self.seed_promotion_executive(row.get("name", "")))
            row.setdefault("era_history", [])
            row.setdefault("legacy_score", 0)
            for fighter in row["roster"]:
                self.ensure_detailed_skills(fighter)
                self.ensure_fighter_business_stats(fighter)
            self.promotions.append(Promotion(**row))
        if not self.promotions:
            self.promotions = self.seed_promotions()
        self.repair_core_promotions()
        self.regions = data.get("regions", self.seed_regions())
        for region in REGIONS:
            self.regions.setdefault(region, {
                "economy": "stable",
                "legality": "regulated by athletic commissions",
                "drug_accuracy": 65,
                "mma_love": random.randint(35, 85),
                "promo_benefit": REGION_PROMO_BENEFITS.get(region, {"media": 1.0, "gate": 1.0, "morale": 1}),
                "teams": random.sample(CAMPS, k=min(3, len(CAMPS))),
                "areas": REGION_CITIES.get(region, [region]),
                "last_major_show": "No major shows yet",
            })
            self.regions[region].setdefault("fan_identity", "Local MMA community")
            self.regions[region].setdefault("crowd_preference", "Competitive fights")
        seeded_gyms = self.seed_gyms()
        if data.get("gyms"):
            self.gyms = [Gym(**row) for row in data.get("gyms", [])]
            known_gyms = {gym.name for gym in self.gyms}
            self.gyms.extend(gym for gym in seeded_gyms if gym.name not in known_gyms)
        else:
            self.gyms = seeded_gyms
        self.result_history = data.get("result_history", [])
        self.result_records = data.get("result_records", [])
        self.ai_event_archive = data.get("ai_event_archive", [])
        self.combat_sport_worlds = data.get("combat_sport_worlds", self.seed_combat_sport_worlds()) or self.seed_combat_sport_worlds()
        for world in self.combat_sport_worlds.values():
            world["roster"] = [fighter if isinstance(fighter, Fighter) else Fighter(**fighter) for fighter in world.get("roster", [])]
        self.repair_combat_sport_worlds()
        self.player_combat_divisions = data.get("player_combat_divisions", {}) or {}
        self.independent_showcase_counter = max(1, data.get("independent_showcase_counter", 1))
        self.retired_fighters = [Fighter(**row) for row in data.get("retired_fighters", [])]
        for fighter in self.retired_fighters:
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.finance = data.get("finance", self.seed_finance())
        self.engine_settings = data.get("engine_settings", self.seed_engine_settings())
        if hasattr(self, "engine_vars"):
            for key, var in self.engine_vars.items():
                var.set(self.engine_settings.get(key, 1.0))
        self.ensure_finance_defaults()
        self.staff = data.get("staff", self.seed_staff())
        self.staff_candidates = data.get("staff_candidates", self.seed_staff_candidates())
        self.ensure_staff_profiles()
        self.scouting = data.get("scouting", [])
        self.scouting_reports = data.get("scouting_reports", {})
        self.achievement_log = data.get("achievement_log", [])
        self.fanbase = data.get("fanbase", {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []})
        self.historical_records = data.get("historical_records", {}) or {}
        for key, value in {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}.items():
            self.fanbase.setdefault(key, value)
        self.academy = data.get("academy", self.academy_defaults() if hasattr(self, "academy_defaults") else {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True})
        if hasattr(self, "repair_academy"):
            self.repair_academy(self.academy)
        else:
            for key, value in {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True}.items(): self.academy.setdefault(key, value)
        for prospect in self.academy["prospects"] + self.academy["talent_pool"]:
            prospect.setdefault("amateur_weight", "Youth Openweight")
        self.inbox = data.get("inbox", [])
        self.owner_goals = data.get("owner_goals", self.seed_owner_goals())
        self.belts = self.normalize_belts(data.get("belts", self.blank_belts()))
        self.interim_belts = self.normalize_belts(data.get("interim_belts", self.blank_belts()))
        self.belt_history = self.normalize_belt_history(data.get("belt_history", self.blank_belt_history()))
        if hasattr(self, "fight_timer_delay"):
            saved_delay = int(data.get("fight_timer_delay", self.fight_timer_delay.get()))
            # 950 ms was the old shipped default. Move old-default saves to the
            # more readable live-fight pace, while respecting deliberate custom speeds.
            if saved_delay == 950:
                saved_delay = 2150
            self.fight_timer_delay.set(max(120, min(3000, saved_delay)))
        self.rules = data.get("rules", {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200})
        self.rules.setdefault("scouting_mode", False)
        self.ensure_rule_defaults()
        self.broadcasters = data.get("broadcasters", [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        self.weight_classes = data.get("weight_classes", list(WEIGHTS))
        self.post_show_bonuses = data.get("post_show_bonuses", {"fight": 5000, "ko": 5000, "sub": 5000})
        self.scheduled_events = data.get("scheduled_events", [])
        self.pending_rebookings = data.get("pending_rebookings", [])
        for event in self.scheduled_events:
            event.setdefault("week", 1)
        self.repair_booking_conflicts()
        self.news = data.get("news", [])
        self.world_chronicle = data.get("world_chronicle", [])[-800:]
        self.event_log = data.get("event_log", [])
        self.season_stats = data.get("season_stats", {})
        self.awards_history = data.get("awards_history", [])
        self.clean_numbered_fighter_names()
        self.sync_gym_membership()
        loaded_fighters = list(self.roster) + list(self.free_agents) + list(self.retired_fighters)
        for promo in self.promotions:
            loaded_fighters.extend(promo.roster)
        recalibrated = self.migrate_real_fighter_profiles(loaded_fighters)
        if recalibrated:
            self.news.insert(0, f"Database realism update: recalibrated {recalibrated} real fighter profiles.")
        rejuvenated = self.migrate_legend_prime_ages(loaded_fighters)
        if rejuvenated:
            self.news.insert(0, f"Legend database update: restored {rejuvenated} legends to their prime-era ages.")
        for fighter in loaded_fighters:
            fighter.camp_quality = self.gym_quality(fighter.camp)
        self.ensure_all_company_champions()

    def migrate_real_fighter_profiles(self, fighters):
        """One-time migration for saves made before deterministic real-fighter profiles."""
        real_names = {row[0] for rows in self.expanded_real_fighter_data().values() for row in rows}
        real_names.update(row[0] for row in self.cage_empire_fighter_data())
        real_names.update(row[0] for row in self.independent_fighter_data())
        real_names.update(row[0] for row in self.legend_fighter_data())
        profiles = self.real_fighter_profiles()
        recalibrated = 0
        for fighter in fighters:
            if fighter.name not in real_names or getattr(fighter, "rating_profile_version", 0) >= 2:
                continue
            baseline = profiles.get(fighter.name, {}).get("rating", fighter.overall)
            self.apply_real_fighter_profile(fighter, baseline)
            recalibrated += 1
        return recalibrated

    def migrate_legend_prime_ages(self, fighters):
        prime_ages = self.prime_legend_ages()
        rejuvenated = 0
        for fighter in fighters:
            target_age = prime_ages.get(fighter.name)
            if target_age is None or getattr(fighter, "legend_prime_age_version", 0) >= 1:
                continue
            fighter.age = target_age
            fighter.prime_start = max(23, target_age - 4)
            fighter.prime_end = max(target_age + 5, 33)
            fighter.legend_prime_age_version = 1
            rejuvenated += 1
        return rejuvenated

    def ensure_fighter_business_stats(self, fighter):
        if not getattr(fighter, "stance", ""):
            fighter.stance = random.choices(["Orthodox", "Southpaw", "Switch"], weights=[58, 29, 13], k=1)[0]
        if not getattr(fighter, "star_quality", 0):
            fighter.star_quality = max(1, min(99, round(fighter.popularity * 0.55 + fighter.overall * 0.25 + random.randint(0, 28))))
        if not getattr(fighter, "charisma", 0):
            fighter.charisma = max(1, min(99, round(fighter.popularity * 0.45 + random.randint(15, 55))))
        if not getattr(fighter, "professionalism", 0):
            fighter.professionalism = random.randint(38, 88)
        if not getattr(fighter, "injury_proneness", 0):
            fighter.injury_proneness = random.randint(8, 42)
        if not getattr(fighter, "finishing_instinct", 0):
            fighter.finishing_instinct = max(1, min(99, round((fighter.striking + fighter.grappling) / 2 + random.randint(-10, 18))))
        if not getattr(fighter, "media_presence", 0):
            fighter.media_presence = max(1, min(99, round(fighter.popularity * 0.55 + fighter.charisma * 0.35 + fighter.media_heat * 0.7)))
        if not getattr(fighter, "sponsor_appeal", 0):
            fighter.sponsor_appeal = max(1, min(99, round(fighter.star_quality * 0.35 + fighter.charisma * 0.25 + fighter.professionalism * 0.25 + fighter.popularity * 0.25)))
        if not getattr(fighter, "portrait_bg", "") or not getattr(fighter, "portrait_accent", ""):
            fighter.portrait_bg, fighter.portrait_accent = self.generate_portrait_palette(fighter.name)
        fighter.nationality = getattr(fighter, "nationality", "") or self.infer_nationality(fighter.name, fighter.region)
        # Identity fields were added after the original regional system.  Old
        # saves retain their existing base as a sensible local origin instead
        # of needing a destructive migration.
        if not getattr(fighter, "birth_region", ""):
            self.assign_regional_identity(fighter, fighter.region, birth_region=fighter.region, force=True)
        else:
            fighter.birth_country = getattr(fighter, "birth_country", "") or REGION_COUNTRIES.get(fighter.birth_region, fighter.birth_region)
            fighter.hometown = getattr(fighter, "hometown", "") or random.choice(REGION_CITIES.get(fighter.birth_region, [fighter.birth_region]))
            fighter.residence = getattr(fighter, "residence", "") or fighter.region
            fighter.training_location = getattr(fighter, "training_location", "") or fighter.residence
            fighter.fighting_base = getattr(fighter, "fighting_base", "") or fighter.residence
            fighter.cultural_connections = getattr(fighter, "cultural_connections", None) or list(dict.fromkeys([fighter.birth_region, fighter.residence, fighter.training_location]))
            markets = getattr(fighter, "regional_popularity", None) or {}
            fighter.regional_popularity = {region: max(0, min(100, int(markets.get(region, 0)))) for region in REGIONS}
            fighter.regional_popularity[fighter.birth_region] = max(fighter.regional_popularity.get(fighter.birth_region, 0), min(65, 18 + fighter.popularity // 3))
            fighter.home_event_history = getattr(fighter, "home_event_history", None) or []
        fighter.record_d = getattr(fighter, "record_d", 0)
        fighter.fight_history = fighter.fight_history or []
        fighter.annual_overalls = fighter.annual_overalls or {"2026": fighter.overall}
        fighter.motivation = getattr(fighter, "motivation", 65) or 65
        fighter.camp_quality = getattr(fighter, "camp_quality", 0) or self.gym_quality(fighter.camp)
        fighter.walk_weight = getattr(fighter, "walk_weight", 0) or self.default_walk_weight(fighter)
        fighter.scale_weight = getattr(fighter, "scale_weight", 0.0) or 0.0
        fighter.missed_weight = getattr(fighter, "missed_weight", False)
        fighter.weight_cut_penalty = getattr(fighter, "weight_cut_penalty", 0) or 0
        fighter.elo_rating = getattr(fighter, "elo_rating", 1500) or 1500
        fighter.rivalry_history = getattr(fighter, "rivalry_history", None) or []
        fighter.serious_injury = getattr(fighter, "serious_injury", "") or ""
        fighter.serious_injury_pending = bool(getattr(fighter, "serious_injury_pending", False))
        fighter.serious_injury_history = getattr(fighter, "serious_injury_history", None) or []
        fighter.serious_injury_recurrence = max(0, getattr(fighter, "serious_injury_recurrence", 0) or 0)
        fighter.rivalry_heat = max(0, min(100, getattr(fighter, "rivalry_heat", 0) or 0))
        fighter.rivalry_origin = getattr(fighter, "rivalry_origin", "") or ""
        fighter.rivalry_rematch_due = bool(getattr(fighter, "rivalry_rematch_due", False))
        fighter.rivalry_last_month = max(0, getattr(fighter, "rivalry_last_month", 0) or 0)
        fighter.weight_class_history = getattr(fighter, "weight_class_history", None) or []
        fighter.weight_move_last_month = getattr(fighter, "weight_move_last_month", -99)
        fighter.career_achievements = getattr(fighter, "career_achievements", None) or []
        fighter.career_goal = getattr(fighter, "career_goal", "") or ""
        fighter.career_goal_target = max(0, getattr(fighter, "career_goal_target", 0) or 0)
        fighter.career_goal_progress = max(0, min(100, getattr(fighter, "career_goal_progress", 0) or 0))
        fighter.career_goal_history = getattr(fighter, "career_goal_history", None) or []
        fighter.career_win_streak = max(0, getattr(fighter, "career_win_streak", 0) or 0)
        fighter.career_goal_last_review = max(0, getattr(fighter, "career_goal_last_review", 0) or 0)
        fighter.ranking_position = max(0, getattr(fighter, "ranking_position", 0) or 0)
        fighter.previous_ranking_position = max(0, getattr(fighter, "previous_ranking_position", 0) or 0)
        fighter.ranking_reason = getattr(fighter, "ranking_reason", "") or ""
        if not fighter.career_goal:
            self.assign_career_goal(fighter)
        fighter.negotiation_persona = getattr(fighter, "negotiation_persona", "") or "Professional"
        fighter.agent_name = getattr(fighter, "agent_name", "") or "Independent"
        fighter.free_agent_months = max(0, getattr(fighter, "free_agent_months", 0) or 0)
        fighter.player_talent_alerted = bool(getattr(fighter, "player_talent_alerted", False))
        fighter.player_talent_window_until = max(0, getattr(fighter, "player_talent_window_until", 0) or 0)
        # Career timing is a permanent archetype, not a camp-changeable trait.
        if getattr(fighter, "career_arc_version", 0) < 2 and getattr(fighter, "legend_prime_age_version", 0) < 1:
            legacy_trait = getattr(fighter, "trait", "")
            if legacy_trait == "Late Prime":
                fighter.career_archetype = "Late Maturation"
                fighter.trait = "Technical Learner"
            elif legacy_trait == "Early Peak":
                fighter.career_archetype = "Early Maturation"
                fighter.trait = "Fast Starter"
            elif not getattr(fighter, "career_archetype", "") or fighter.career_archetype == "Standard Prime":
                if fighter.prime_end >= 36:
                    fighter.career_archetype = "Durable Career"
                elif fighter.prime_start <= 24:
                    fighter.career_archetype = "Early Maturation"
                else:
                    fighter.career_archetype = "Balanced Development"
            self.assign_career_arc(fighter)
            fighter.career_arc_version = 2

    def default_walk_weight(self, fighter):
        limit = WEIGHT_LIMITS.get(fighter.weight, 170)
        spread = 10 if limit <= 135 else 15 if limit <= 170 else 22 if limit <= 205 else 35
        if fighter.gender == "Female":
            spread = max(8, spread - 4)
        natural_size = self.ds(fighter, "natural_size", 50) if getattr(fighter, "detailed_skills", None) else 50
        size_adjust = round((natural_size - 50) / 8)
        return min(295, limit + max(4, random.randint(max(5, spread // 2), spread) + size_adjust))

    def refresh_game_menu(self):
        if not hasattr(self, "save_slot_list"):
            return
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        playable = [promo.name for promo in sorted(self.promotions, key=lambda promo: promo.name)
                    if promo.name != "Spectator" and not getattr(promo, "is_regional_feeder", False)
                    and "independent" not in promo.name.lower()]
        choices = ["Spectator Mode"] + list(dict.fromkeys([self.player_company_name] + playable))
        self.start_company_combo.configure(values=choices)
        if self.start_company_choice.get() not in choices:
            self.start_company_choice.set(self.player_company_name)
        current_save = self.save_slot_list.curselection()
        current_db = self.database_list.curselection()
        self.save_slot_list.delete(0, "end")
        self.save_slot_files = []
        for file in sorted(SAVE_DIR.glob("*.json")):
            if file.name == SAVE_FILE.name:
                label = f"{file.stem} | Quick Save"
            else:
                label = file.stem
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                meta = data.get("_save_meta", {}) if isinstance(data, dict) else {}
                if meta:
                    company = meta.get("company", "Unknown")
                    month = meta.get("month", "?")
                    week = meta.get("week", "?")
                    saved_at = str(meta.get("saved_at", ""))[:16].replace("T", " ")
                    universe = meta.get("active_universe", "")
                    universe_note = f" | {universe}" if universe else ""
                    label = f"{file.stem} | {company} | M{month} W{week} | {saved_at}{universe_note}"
            except Exception:
                pass
            self.save_slot_files.append(file)
            self.save_slot_list.insert("end", label)
        self.database_list.delete(0, "end")
        self.database_files = []
        if hasattr(self, "ensure_default_universe_database"):
            self.ensure_default_universe_database()
        for file in sorted(DATABASE_DIR.glob("*.universe.json")):
            self.database_files.append(file)
            active = ""
            try:
                active = " *ACTIVE*" if file.name == self.active_universe_database_path().name else ""
            except Exception:
                active = ""
            self.database_list.insert("end", f"[Universe] {file.stem.replace('.universe', '')}{active}")
        for file in sorted(path for path in DATABASE_DIR.glob("*.json") if not path.name.endswith(".universe.json")):
            self.database_files.append(file)
            self.database_list.insert("end", f"[Legacy/Section] {file.stem}")
        if current_save and self.save_slot_list.size():
            self.save_slot_list.selection_set(min(current_save[0], self.save_slot_list.size() - 1))
        if current_db and self.database_list.size():
            self.database_list.selection_set(min(current_db[0], self.database_list.size() - 1))

    def player_company_as_promotion(self):
        show_history = list(self.result_history[:12])
        if not show_history and self.event_log:
            show_history = list(self.event_log[:12])
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop, player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history)
        return Promotion(
            self.player_company_name,
            self.player_region,
            self.company_pop,
            self.cash,
            self.roster,
            reputation=self.player_reputation,
            reputation_score=self.company_pop,
            stability=self.company_stability,
            show_history=show_history,
            event_counter=max(1, len(self.result_history) + len(self.scheduled_events) + 1),
            belts=self.normalize_belts(self.belts),
            interim_belts=self.normalize_belts(self.interim_belts),
            belt_history=self.normalize_belt_history(self.belt_history),
            rules=dict(self.rules),
            broadcasters=[dict(item) for item in self.broadcasters],
            weight_classes=list(self.weight_classes),
            scheduled_events=list(self.scheduled_events),
            finance=json.loads(json.dumps(self.finance)),
            staff=[dict(item) for item in self.staff],
            scouting=list(self.scouting),
            inbox=[dict(item) for item in self.inbox],
            owner_goals=[dict(item) for item in self.owner_goals],
            post_show_bonuses=dict(self.post_show_bonuses),
            strategy=self.seed_promotion_strategy(self.player_company_name, "Balanced"),
            executive=self.seed_promotion_executive(self.player_company_name),
            era_history=[],
        )

    def enter_spectator_mode(self):
        """Turn the currently controlled promotion over to the AI and observe the full world."""
        if getattr(self, "spectator_mode", False):
            return
        former_company = self.player_company_as_promotion()
        # A human-controlled regional company can live on a lean cash reserve;
        # an unattended AI company needs enough runway to actually stage cards.
        # The existing player company begins with a regional operating budget,
        # but the AI requires a full-card reserve before it will book. Give the
        # handoff company a one-time operating runway rather than bypassing the
        # same affordability checks used by every other promotion.
        former_company.cash = max(former_company.cash, 2_000_000)
        former_company.show_personality = "Prospect Builder"
        former_company.strategy = self.seed_promotion_strategy(former_company.name, former_company.show_personality)
        former_company.executive = self.seed_promotion_executive(former_company.name)
        if not any(promo.name == former_company.name for promo in self.promotions):
            self.promotions.append(former_company)
        self.spectator_mode = True
        self.player_company_name = "Spectator"
        self.player_region = "Worldwide"
        self.player_reputation = "World Observer"
        self.cash = 0
        self.company_pop = 0
        self.company_stability = 100
        self.roster = []
        self.scheduled_events = []
        self.pending_rebookings = []
        self.booked = []
        self.result_history = []
        self.event_log = []
        self.news.insert(0, f"Spectator mode started. {former_company.name} is now AI-managed and the full MMA world will progress on its own.")
        if hasattr(self, "event_name"):
            self.event_name.set("Spectator Mode")
        self.refresh_all()
        self.write_log()

    def exit_spectator_mode(self):
        self.spectator_mode = False

    def take_control_selected_company(self):
        if not hasattr(self, "company_list") or not self.company_list.curselection():
            messagebox.showinfo("No company", "Select a company first.")
            return
        self.take_control_of_company(self.company_list.get(self.company_list.curselection()[0]))

    def take_control_of_company(self, company_name, keep_current=True):
        if company_name == self.player_company_name:
            messagebox.showinfo("Already active", f"You already control {company_name}.")
            return
        promo = next((item for item in self.promotions if item.name == company_name), None)
        if not promo:
            messagebox.showinfo("Company unavailable", "That company is not available to control.")
            return
        self.promotions.remove(promo)
        was_spectator = getattr(self, "spectator_mode", False)
        if keep_current and not was_spectator:
            self.promotions.append(self.player_company_as_promotion())
        self.exit_spectator_mode()
        self.player_company_name = promo.name
        self.player_region = promo.region
        self.player_reputation = promo.reputation
        self.cash = promo.cash
        self.company_pop = promo.reputation_score
        self.company_stability = promo.stability
        self.roster = promo.roster
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(self.roster, promo.belts or {}, promo.name, promo.region, promo.reputation_score, player_owned=True, interim_belts=promo.interim_belts or {}, belt_history=promo.belt_history or {})
        self.rules = promo.rules or {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200}
        self.ensure_rule_defaults()
        self.broadcasters = promo.broadcasters or [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]
        self.weight_classes = promo.weight_classes or list(WEIGHTS)
        self.scheduled_events = promo.scheduled_events or []
        self.finance = promo.finance or self.seed_finance()
        self.staff = promo.staff or self.seed_staff()
        self.staff_candidates = self.seed_staff_candidates()
        self.scouting = promo.scouting or []
        self.inbox = promo.inbox or []
        self.owner_goals = promo.owner_goals or self.seed_owner_goals()
        self.post_show_bonuses = promo.post_show_bonuses or {"fight": 5000, "ko": 5000, "sub": 5000}
        self.result_history = promo.show_history or []
        self.booked = []
        self.event_name.set(self.default_event_name())
        self.news.insert(0, f"You are now controlling {self.player_company_name}.")
        self.refresh_all()
        self.write_log()

    def safe_filename(self, value):
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in value).strip()
        return cleaned or "Game"

    def selected_database_path(self):
        selected = self.database_list.curselection() if hasattr(self, "database_list") else []
        files = getattr(self, "database_files", [])
        if selected and selected[0] < len(files):
            return files[selected[0]]
        name = self.safe_filename(self.database_name.get() if hasattr(self, "database_name") else "Default Universe")
        path = DATABASE_DIR / f"{name}.universe.json"
        return path if path.exists() else DATABASE_DIR / f"{name}.json"

    def use_selected_universe_database(self):
        path = self.selected_database_path()
        if not path.name.endswith(".universe.json"):
            messagebox.showinfo("Universe Database", "Select a [Universe] database pack first.")
            return
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        messagebox.showinfo("Universe Selected", f"New games will now use:\n{path.name}")

    def clone_selected_universe_database(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        source = self.selected_database_path()
        if not source.exists() or not source.name.endswith(".universe.json"):
            source = self.ensure_default_universe_database()
        name = self.safe_filename(self.database_name.get() if hasattr(self, "database_name") else "")
        if not name or name in ("Default Database", "Default Universe"):
            name = f"{source.stem.replace('.universe', '')} Copy"
        target = DATABASE_DIR / f"{name}.universe.json"
        counter = 2
        while target.exists():
            target = DATABASE_DIR / f"{name} {counter}.universe.json"
            counter += 1
        data = json.loads(source.read_text(encoding="utf-8"))
        data["database_name"] = target.stem.replace(".universe", "")
        data["cloned_from"] = source.name
        data["cloned_at"] = datetime.now().isoformat(timespec="seconds")
        atomic_write_json(target, data)
        self.active_universe_marker().write_text(target.name, encoding="utf-8")
        self.refresh_game_menu()
        messagebox.showinfo("Universe Cloned", f"Created and selected:\n{target.name}")

    def reset_default_universe_database(self):
        if not messagebox.askyesno("Reset Default Universe", "Rebuild the default real-life universe database from the game's built-in source data?\n\nYour cloned custom universes will not be changed."):
            return
        path = self.universe_database_path("Default Universe")
        if path.exists():
            backup = path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy2(path, backup)
        atomic_write_json(path, self.build_universe_database_pack("Default Universe"))
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        messagebox.showinfo("Default Restored", f"Default universe rebuilt and selected:\n{path.name}")

    def open_database_folder(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(DATABASE_DIR)
        except Exception:
            messagebox.showinfo("Database Folder", str(DATABASE_DIR))

    def active_universe_pack_with_path(self):
        path = self.active_universe_database_path()
        return path, self.load_universe_database_pack(path)

    def backup_universe_pack(self, path):
        backup = path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(path, backup)
        return backup

    def open_universe_section_editor(self):
        section = self.universe_section_choice.get() if hasattr(self, "universe_section_choice") else "fighters"
        path, pack = self.active_universe_pack_with_path()
        sections = pack.setdefault("sections", {})
        value = sections.get(section, {})
        window = tk.Toplevel(self.root)
        window.title(f"Universe Section Editor - {section}")
        window.geometry("980x720")
        window.minsize(780, 520)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"EDIT UNIVERSE SECTION: {section.upper()}", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text=f"Active pack: {path.name}. Save creates a backup first. This edits the database pack used by new games, not the current save.", style="Inset.TLabel").pack(fill="x", padx=10, pady=(0, 8))
        frame = ttk.Frame(window, style="Panel.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        text = tk.Text(frame, wrap="none", font=("Consolas", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text.insert("end", json.dumps(value, indent=2))
        buttons = ttk.Frame(window, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        def save_section():
            try:
                edited = json.loads(text.get("1.0", "end").strip() or "{}")
            except Exception as exc:
                messagebox.showerror("Invalid JSON", f"Section was not saved.\n\n{type(exc).__name__}: {exc}")
                return
            current_path, current_pack = self.active_universe_pack_with_path()
            self.backup_universe_pack(current_path)
            current_pack.setdefault("sections", {})[section] = edited
            current_pack["last_edited_at"] = datetime.now().isoformat(timespec="seconds")
            current_pack["last_edited_section"] = section
            atomic_write_json(current_path, current_pack)
            messagebox.showinfo("Section Saved", f"Saved {section} in {current_path.name}.")
            self.refresh_game_menu()

        def validate_section():
            try:
                edited = json.loads(text.get("1.0", "end").strip() or "{}")
            except Exception as exc:
                messagebox.showerror("Invalid JSON", f"{type(exc).__name__}: {exc}")
                return
            issues = self.validate_universe_section(section, edited)
            messagebox.showinfo("Section Validation", "\n".join(issues[:40]) if issues else f"{section} section looks valid.")

        ttk.Button(buttons, text="Validate Section", command=validate_section).pack(side="left")
        ttk.Button(buttons, text="Save Section", style="Accent.TButton", command=save_section).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

    def validate_universe_section(self, section, value):
        issues = []
        if section == "fighters":
            if not isinstance(value, dict):
                return ["fighters section must be an object."]
            for key in ("player_roster", "free_agents", "promotions"):
                if key not in value:
                    issues.append(f"Missing fighters.{key}")
            names = []
            for row in value.get("player_roster", []) + value.get("free_agents", []):
                if isinstance(row, list) and row:
                    names.append(row[0])
                elif isinstance(row, dict):
                    names.append(row.get("name", ""))
            for rows in value.get("promotions", {}).values():
                for row in rows:
                    if isinstance(row, list) and row:
                        names.append(row[0])
                    elif isinstance(row, dict):
                        names.append(row.get("name", ""))
            duplicates = [name for name, count in Counter(names).items() if name and count > 1]
            if duplicates:
                issues.append("Duplicate named fighters: " + ", ".join(duplicates[:12]))
        elif section == "combat_sports":
            rosters = value.get("rosters", value) if isinstance(value, dict) else {}
            for sport in ("Boxing", "Kickboxing", "Muay Thai", "Wrestling", "Brazilian Jiu-Jitsu"):
                if sport not in rosters:
                    issues.append(f"Missing combat sport roster: {sport}")
                elif len(rosters.get(sport, [])) < 12:
                    issues.append(f"{sport} roster is thin ({len(rosters.get(sport, []))})")
        elif section == "companies":
            if not isinstance(value, dict):
                return ["companies section must be an object."]
            if "player_company" not in value:
                issues.append("Missing companies.player_company")
            if not value.get("promotions"):
                issues.append("No AI promotions defined.")
            for promo in value.get("promotions", []):
                for key in ("name", "region", "size", "cash", "roster_key"):
                    if key not in promo:
                        issues.append(f"Promotion missing {key}: {promo.get('name', '<unnamed>')}")
        elif section == "media":
            if not isinstance(value, dict):
                return ["media section must be an object."]
            if not value.get("player_broadcasters"):
                issues.append("No player broadcasters defined.")
        elif section == "regions":
            if not isinstance(value, dict) or not value:
                issues.append("regions section must be a non-empty object.")
        return issues

    def validate_active_universe_database(self):
        path, pack = self.active_universe_pack_with_path()
        sections = pack.get("sections", {})
        issues = []
        for section in ("fighters", "companies", "combat_sports", "media", "regions"):
            issues.extend(f"{section}: {issue}" for issue in self.validate_universe_section(section, sections.get(section, {})))
        if not issues:
            messagebox.showinfo("Universe Validation", f"{path.name} passed the current validation checks.")
        else:
            messagebox.showwarning("Universe Validation", "\n".join(issues[:60]))

    def save_selected_slot(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.save_slot_name.get())
        path = SAVE_DIR / f"{name}.json"
        try:
            if path.exists():
                self.backup_save_file(path, "before_slot_save")
            data = self.serialize_world()
            data["_save_meta"] = self.save_metadata(name)
            atomic_write_json(path, data)
            self.prune_save_backups()
        except Exception as exc:
            LOGGER.exception("Save slot failed: %s", exc)
            messagebox.showerror("Save failed", f"The slot was not changed.\n\n{type(exc).__name__}: {exc}")
            return
        self.refresh_game_menu()
        messagebox.showinfo("Saved", f"Saved slot: {name}")

    def selected_save_path(self):
        selected = self.save_slot_list.curselection()
        files = getattr(self, "save_slot_files", [])
        if selected and selected[0] < len(files):
            return files[selected[0]]
        name = self.safe_filename(self.save_slot_name.get())
        return SAVE_DIR / f"{name}.json"

    def load_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            messagebox.showinfo("No save", "Select an existing save slot.")
            return
        try:
            self.backup_save_file(path, "before_slot_load")
            self.apply_world_data(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            LOGGER.exception("Save slot failed to load: %s", exc)
            messagebox.showerror("Load failed", f"That slot was left untouched.\n\n{type(exc).__name__}: {exc}")
            return
        self.booked.clear()
        self.refresh_all()
        self.write_log()
        messagebox.showinfo("Loaded", f"Loaded slot: {path.stem}")

    def delete_selected_slot(self):
        path = self.selected_save_path()
        if path.exists():
            if not messagebox.askyesno("Delete Save Slot", f"Delete {path.stem}? A backup will be kept."):
                return
            self.backup_save_file(path, "before_slot_delete")
            path.unlink()
            self.refresh_game_menu()

    def backup_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            messagebox.showinfo("No save", "Select an existing save slot first.")
            return
        backup = self.backup_save_file(path, "manual")
        self.prune_save_backups()
        messagebox.showinfo("Backup Created", f"Backed up {path.name}:\n{backup}")

    def open_saves_folder(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(SAVE_DIR)
        except Exception:
            messagebox.showinfo("Saves Folder", str(SAVE_DIR))

    def open_save_backup_manager(self):
        backup_dir = self.save_backup_dir()
        backups = sorted([item for item in backup_dir.glob("*.json") if not item.name.endswith(".manifest.json")], key=lambda item: item.stat().st_mtime, reverse=True)
        window = tk.Toplevel(self.root)
        window.title("Save Backup Manager")
        window.geometry("860x520")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="SAVE BACKUP MANAGER", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text="Restore creates a backup of the destination first. Backups live in Saves/Backups.", style="Inset.TLabel").pack(fill="x", padx=10, pady=(0, 8))
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        backup_list = tk.Listbox(body, font=("Consolas", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        backup_list.pack(side="left", fill="both", expand=True, padx=(0, 8))
        detail = tk.Text(body, width=38, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(side="left", fill="both")
        for item in backups:
            backup_list.insert("end", f"{item.name} | {datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

        def selected_backup():
            sel = backup_list.curselection()
            return backups[sel[0]] if sel else None

        def show_detail(_event=None):
            item = selected_backup()
            detail.config(state="normal")
            detail.delete("1.0", "end")
            if item:
                manifest = item.with_suffix(".manifest.json")
                text = f"Backup: {item.name}\nSize: {item.stat().st_size:,} bytes\nModified: {datetime.fromtimestamp(item.stat().st_mtime)}\n\n"
                if manifest.exists():
                    text += manifest.read_text(encoding="utf-8")
                detail.insert("end", text)
            detail.config(state="disabled")

        def restore_backup():
            item = selected_backup()
            if not item:
                messagebox.showinfo("Restore Backup", "Select a backup first.")
                return
            target_name = self.safe_filename(self.save_slot_name.get() or item.name.split("_before_")[0].split("_manual_")[0])
            target = SAVE_DIR / f"{target_name}.json"
            if not messagebox.askyesno("Restore Backup", f"Restore this backup to slot '{target.stem}'?\n\n{item.name}"):
                return
            if target.exists():
                self.backup_save_file(target, "before_restore")
            shutil.copy2(item, target)
            self.refresh_game_menu()
            messagebox.showinfo("Backup Restored", f"Restored to {target.name}.")

        backup_list.bind("<<ListboxSelect>>", show_detail)
        buttons = ttk.Frame(window, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Restore To Slot Name", style="Accent.TButton", command=restore_backup).pack(side="left")
        ttk.Button(buttons, text="Open Saves Folder", command=self.open_saves_folder).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        if backups:
            backup_list.selection_set(0)
            show_detail()

    def export_database(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.database_name.get())
        data = self.serialize_world()
        for key in ("cash", "month", "scheduled_events", "event_log", "result_history", "result_records", "ai_event_archive", "finance", "inbox"):
            data.pop(key, None)
        data["database_name"] = name
        path = DATABASE_DIR / f"{name}.json"
        atomic_write_json(path, data)
        self.refresh_game_menu()
        messagebox.showinfo("Database Exported", f"Exported database: {name}")

    def import_quick_save_as_database(self):
        if not SAVE_FILE.exists():
            messagebox.showinfo("No quick save", "No savegame.json exists to import.")
            return
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.database_name.get())
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        for key in ("cash", "month", "scheduled_events", "event_log", "result_history", "result_records", "ai_event_archive", "finance", "inbox"):
            data.pop(key, None)
        data["database_name"] = name
        atomic_write_json(DATABASE_DIR / f"{name}.json", data)
        self.refresh_game_menu()
        messagebox.showinfo("Database Imported", f"Imported quick save as database: {name}")

    def load_selected_database(self):
        path = self.selected_database_path()
        if not path.exists():
            messagebox.showinfo("No database", "Select a database to load.")
            return
        if path.name.endswith(".universe.json"):
            self.active_universe_marker().write_text(path.name, encoding="utf-8")
            self.new_game()
            messagebox.showinfo("Universe Loaded", f"Started a new game from universe pack: {path.stem.replace('.universe', '')}")
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("cash", 275_000)
        data.setdefault("month", 1)
        data.setdefault("scheduled_events", [])
        data.setdefault("event_log", [])
        data.setdefault("result_history", [])
        data.setdefault("finance", self.seed_finance())
        data.setdefault("inbox", [])
        self.apply_world_data(data)
        self.booked.clear()
        self.refresh_all()
        self.write_log()
        messagebox.showinfo("Database Loaded", f"Started game from database: {path.stem}")

    def new_game(self):
        choice = self.start_company_choice.get() if hasattr(self, "start_company_choice") else PLAYER_PROMOTION_NAME
        if choice == "Cage Empire":
            choice = PLAYER_PROMOTION_NAME
        company_section = self.universe_section("companies", {}) if hasattr(self, "universe_section") else {}
        player_spec = (company_section or {}).get("player_company", {})
        self.player_company_name = player_spec.get("name", PLAYER_PROMOTION_NAME)
        self.spectator_mode = False
        self.player_region = player_spec.get("region", "USA")
        self.player_reputation = player_spec.get("reputation", "Regional Player Company")
        self.cash = player_spec.get("cash", 275_000)
        self.company_pop = player_spec.get("popularity", 38)
        self.company_stability = player_spec.get("stability", 52)
        self.month = 1
        self.week = 1
        self.name_counts = {}
        self.roster = self.seed_roster()
        self.free_agents = self.seed_free_agents()
        self.promotions = self.seed_promotions()
        self.repair_core_promotions()
        self.regions = self.universe_section("regions", None) or self.seed_regions()
        self.result_history = []
        self.result_records = []
        self.ai_event_archive = []
        self.independent_showcase_counter = 1
        self.retired_fighters = []
        self.finance = self.seed_finance()
        self.engine_settings = self.seed_engine_settings()
        if hasattr(self, "engine_vars"):
            for key, var in self.engine_vars.items():
                var.set(self.engine_settings.get(key, 1.0))
        self.staff = self.seed_staff()
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        self.scouting = []
        self.scouting_reports = {}
        self.academy = self.academy_defaults() if hasattr(self, "academy_defaults") else {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True}
        self.inbox = []
        self.owner_goals = self.seed_owner_goals()
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.belt_history = self.blank_belt_history()
        self.rules = {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "allow_mixed_gender": False, "active_fighter_target": 1200, "auto_renew_enabled": False, "scouting_mode": False}
        media_section = self.universe_section("media", {}) if hasattr(self, "universe_section") else {}
        self.broadcasters = media_section.get("player_broadcasters", self.default_player_media() if hasattr(self, "default_player_media") else [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        self.weight_classes = list(WEIGHTS)
        self.post_show_bonuses = {"fight": 5000, "ko": 5000, "sub": 5000}
        self.news = ["A new game has started."]
        self.world_chronicle = []
        self.fanbase = {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}
        self.defunct_promotions = []
        self.booked = []
        self.scheduled_events = []
        self.event_log = []
        self.clean_numbered_fighter_names()
        self.sync_gym_membership()
        self.ensure_all_company_champions()
        if choice == "Spectator Mode":
            self.enter_spectator_mode()
            return
        if choice != self.player_company_name:
            self.take_control_of_company(choice, keep_current=False)
            self.news.insert(0, f"New game started as {self.player_company_name}.")
            return
        self.refresh_all()
        self.write_log()
