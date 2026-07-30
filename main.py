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
from ui import UIMixin
from admin import AdminMixin
from seeding import SeedMixin
from media import MediaMixin
from views import ViewMixin
from events import EventMixin
from fight_engine import FightEngineMixin
from world import WorldMixin
from persistence import PersistenceMixin, configure_runtime_logging, install_global_exception_handlers, register_crash_app, write_crash_report
from awards import AwardsMixin
from audio import FightNightAudioMixin


class StartupSplash:
    """Small responsive startup window shown while the simulation is assembled."""

    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.configure(bg="#090909")
        width, height = 540, 210
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.attributes("-topmost", True)
        border = tk.Frame(self.window, bg="#d20a0a", padx=2, pady=2)
        border.pack(fill="both", expand=True)
        body = tk.Frame(border, bg="#111111")
        body.pack(fill="both", expand=True)
        tk.Label(
            body, text=GAME_NAME.upper(), bg="#111111", fg="#f3f3f3",
            font=("Arial", 23, "bold"), anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 2))
        tk.Label(
            body, text="PROMOTION MANAGEMENT SIM", bg="#111111", fg="#bdbdbd",
            font=("Arial", 9, "bold"), anchor="w",
        ).pack(fill="x", padx=25, pady=(0, 20))
        self.status = tk.StringVar(value="Starting...")
        tk.Label(
            body, textvariable=self.status, bg="#111111", fg="#f3f3f3",
            font=("Tahoma", 9), anchor="w",
        ).pack(fill="x", padx=25, pady=(0, 7))
        self.progress = ttk.Progressbar(body, mode="determinate", maximum=100, length=490)
        self.progress.pack(fill="x", padx=25, pady=(0, 7))
        self.percent = tk.StringVar(value="0%")
        tk.Label(
            body, textvariable=self.percent, bg="#111111", fg="#bdbdbd",
            font=("Tahoma", 8), anchor="e",
        ).pack(fill="x", padx=25)
        self.window.update_idletasks()
        self.window.update()

    def update(self, value, text):
        if not self.window.winfo_exists():
            return
        value = max(0, min(100, int(value)))
        self.progress["value"] = value
        self.status.set(text)
        self.percent.set(f"{value}%")
        self.window.update_idletasks()
        self.window.update()

    def close(self):
        if self.window.winfo_exists():
            self.window.destroy()


class FightEmpireApp(
    FightNightAudioMixin,
    UIMixin,
    AdminMixin,
    SeedMixin,
    MediaMixin,
    ViewMixin,
    EventMixin,
    FightEngineMixin,
    WorldMixin,
    PersistenceMixin,
    AwardsMixin,
):
    def __init__(self, root, startup_progress=None):
        self.root = root
        self._startup_progress_callback = startup_progress
        self.report_startup_progress(5, "Preparing the application...")
        self.root.report_callback_exception = self.handle_uncaught_exception
        register_crash_app(self)
        self.root.title(GAME_NAME)
        self.app_icon_image = None
        try:
            if APP_ICON_ICO.exists():
                self.root.iconbitmap(default=str(APP_ICON_ICO))
            if APP_ICON_PNG.exists():
                self.app_icon_image = tk.PhotoImage(file=str(APP_ICON_PNG))
                self.root.iconphoto(True, self.app_icon_image)
        except tk.TclError:
            pass
        # Keep the dense desktop layout usable on 13-inch/768px laptops.  The
        # old fixed 1280x760 launch size could extend underneath the taskbar or
        # beyond a smaller screen before the player had a chance to resize it.
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        available_width = max(640, screen_width - 32)
        available_height = max(520, screen_height - 92)
        launch_width = min(1280, available_width)
        launch_height = min(760, available_height)
        self.root.geometry(f"{launch_width}x{launch_height}+{max(0, (screen_width - launch_width) // 2)}+{max(0, (screen_height - launch_height) // 3)}")
        self.root.minsize(min(960, launch_width), min(620, launch_height))
        self.report_startup_progress(10, "Reading promotion settings...")

        self.cash = 275_000
        self.company_pop = 38
        self.company_stability = 52
        self.company_safety = 60
        self.company_milestone_progress = {}
        self.super_event_offers = []
        self.super_event_history = []
        self.super_event_project = None
        self.theme_name = "UFC"
        self.player_company_name = PLAYER_PROMOTION_NAME
        self.spectator_mode = False
        # Save files are isolated by game slot.  Persistence keeps legacy flat
        # saves readable, but all newly written data lives under Saves/<slot>/.
        self.active_save_name = "Game 1"
        self.active_save_group = "Main"
        self.last_spectator_snapshot_year = 0
        self.player_region = "USA"
        self.player_reputation = "Regional Player Company"
        self.month = 1
        self.week = 1
        self._advance_in_progress = False
        self._advance_job = None
        self.name_counts = {}
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.special_belts = {}
        self.belt_history = self.blank_belt_history()
        self.closed_divisions = set()
        self.player_managed_divisions = set()
        self._seeding_universe = True
        try:
            self.report_startup_progress(18, "Loading your promotion roster...")
            self.roster = self.seed_roster()
            self.report_startup_progress(28, "Loading the fighter market...")
            self.free_agents = self.seed_free_agents()
            self.report_startup_progress(39, "Building the MMA world...")
            self.promotions = self.seed_promotions()
            self.report_startup_progress(57, "Building boxing and combat-sport circuits...")
            self.combat_sport_worlds = self.seed_combat_sport_worlds()
        finally:
            self._seeding_universe = False
        self.player_combat_divisions = {}
        self.standings_history = {}
        self.regions = self.seed_regions()
        self.gyms = self.seed_gyms()
        self.report_startup_progress(67, "Connecting gyms, regions, and athletes...")
        self.normalize_gym_assignments()
        self.sync_gym_membership()
        self.result_history = []
        self.result_records = []
        self.change_journal = []
        self.ai_event_archive = []
        self.independent_showcase_counter = 1
        self.retired_fighters = []
        self.finance = self.seed_finance()
        self.engine_settings = self.seed_engine_settings()
        self.staff = self.seed_staff()
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        self.scouting = []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self._scouting_state_migrated = True
        self.academy = self.academy_defaults()
        self.inbox = []
        self.inbox_hidden_types = set()
        self.owner_goals = self.seed_owner_goals()
        self.rules = {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200, "ai_offer_market_target": 100, "global_result_replay_limit": 2000, "auto_renew_enabled": False, "scouting_mode": True, "fight_night_audio_enabled": True, "fight_night_audio_output": "System default", "fight_night_audio_volume": 55, "autosave_enabled": True, "autosave_interval_months": 2, "autosave_weekly_keep": 2, "autosave_monthly_keep": 2, "save_backup_keep": 2, "save_retention_version": 4, "detailed_skill_balance_version": 1}
        self.rules["allow_mixed_gender"] = False
        self.broadcasters = [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]
        self.media_companies = []
        self.media_market_history = []
        self.media_market_last_month = 0
        self.ensure_media_system()
        self.weight_classes = list(WEIGHTS)
        self.post_show_bonuses = {"fight": 5000, "ko": 5000, "sub": 5000}
        self.news = [
            "The new season begins with regional promoters competing for attention.",
            "Managers are watching prospect development, contract expiry, and divisional depth closely.",
        ]
        self.world_chronicle = []
        self.defunct_promotions = []
        self.booked = []
        self.scheduled_events = []
        self.pending_rebookings = []
        self.event_log = []
        self.season_stats = {}
        self.awards_history = []
        self.achievement_log = []
        self.historical_records = {}
        self.fanbase = {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}
        if hasattr(self, "event_name"):
            self.event_name.set(self.default_event_name())
        self.clean_numbered_fighter_names()
        self.refresh_promotion_rankings(track=False)
        self.report_startup_progress(74, "Preparing contracts, finance, and staff...")

        self.event_name = tk.StringVar(value=self.default_event_name())
        self.venue = tk.StringVar(value="Regional Arena")
        self.event_region = tk.StringVar(value="USA")
        self.event_city = tk.StringVar(value="Las Vegas")
        self.event_broadcaster = tk.StringVar(value="Regional Webcast")
        self.card_tier = tk.StringVar(value="Main Card")
        self.event_month = tk.IntVar(value=1)
        self.event_week = tk.IntVar(value=1)
        self.event_day_choice = tk.StringVar(value=CALENDAR_DAYS[DEFAULT_EVENT_DAY - 1])
        self.event_calendar_month = tk.StringVar(value=CALENDAR_MONTH_ABBREVIATIONS[0])
        self.event_year = tk.IntVar(value=GAME_START_YEAR)
        self.title_fight = tk.BooleanVar(value=False)
        self.main_event = tk.BooleanVar(value=False)
        self.weight_filter = tk.StringVar(value="All")
        self.roster_gender_filter = tk.StringVar(value="All")
        self.roster_status_filter = tk.StringVar(value="All")
        self.roster_search = tk.StringVar(value="")
        self.roster_age_min = tk.IntVar(value=16)
        self.roster_age_max = tk.IntVar(value=60)
        self.roster_ovr_min = tk.IntVar(value=0)
        self.roster_ovr_max = tk.IntVar(value=100)
        self.roster_pop_min = tk.IntVar(value=0)
        self.available_weight_filter = tk.StringVar(value="All")
        self.available_gender_filter = tk.StringVar(value="All")
        self.available_status_filter = tk.StringVar(value="All")
        self.available_search = tk.StringVar(value="")
        self.market_weight_filter = tk.StringVar(value="All")
        self.market_gender_filter = tk.StringVar(value="All")
        self.market_search = tk.StringVar(value="")
        self.market_status_filter = tk.StringVar(value="All")
        self.market_age_min = tk.IntVar(value=16)
        self.market_age_max = tk.IntVar(value=60)
        self.market_ovr_min = tk.IntVar(value=0)
        self.market_ovr_max = tk.IntVar(value=100)
        self.market_pop_min = tk.IntVar(value=0)
        self.market_potential_min = tk.IntVar(value=0)
        self.ranking_gender_filter = tk.StringVar(value="All")
        self.ranking_weight_filter = tk.StringVar(value="All")
        self.result_search = tk.StringVar(value="")
        self.result_company_filter = tk.StringVar(value="All")
        self.retired_search = tk.StringVar(value="")
        self.retired_gender_filter = tk.StringVar(value="All")
        self.retired_weight_filter = tk.StringVar(value="All")
        self.retired_legacy_filter = tk.StringVar(value="All")
        self.audit_runs = tk.IntVar(value=250)
        self.play_audit_years = tk.IntVar(value=30)
        self.fight_timer_delay = tk.IntVar(value=2150)
        self.sim_fighter_a = tk.StringVar(value="")
        self.sim_fighter_b = tk.StringVar(value="")
        self.sim_gender_filter = tk.StringVar(value="All")
        self.sim_weight_filter = tk.StringVar(value="All")
        self.sim_title_fight = tk.BooleanVar(value=False)
        self.sim_main_event = tk.BooleanVar(value=True)
        self.sim_camp_weeks_a = tk.IntVar(value=8)
        self.sim_camp_weeks_b = tk.IntVar(value=8)
        self.sim_tournament_size = tk.IntVar(value=8)
        self.sim_generate_count = tk.IntVar(value=25)
        self.sim_generate_age = tk.StringVar(value="Random")
        self.sim_generate_ability = tk.StringVar(value="Random")
        self.sim_generate_gender = tk.StringVar(value="Random")
        self.sim_generate_weight = tk.StringVar(value="Random")
        self.media_fighter_choice = tk.StringVar(value="")
        self.media_target_choice = tk.StringVar(value="")

        self.configure_style()
        self.build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit_application)
        self.root.bind_all("<space>", self.handle_spectator_space_stop, add="+")
        self.report_startup_progress(97, "Opening the promoter dashboard...")
        self.refresh_all(full=False)
        self.report_startup_progress(100, "Ready.")

    def report_startup_progress(self, value, text):
        callback = getattr(self, "_startup_progress_callback", None)
        if callable(callback):
            callback(value, text)

    def confirm_exit_application(self):
        if messagebox.askyesno(
            "Exit MMA Warriors?",
            "Are you sure you want to close MMA Warriors?\n\nRemember to save your game before exiting.",
            parent=self.root,
        ):
            self.root.destroy()

    def handle_spectator_space_stop(self, _event=None):
        """Space is an immediate, keyboard-friendly stop control for observer fast-forward."""
        if self.request_spectator_sim_stop():
            return "break"
        return None



if __name__ == "__main__":
    configure_runtime_logging()
    install_global_exception_handlers()
    root = None
    splash = None
    try:
        root = tk.Tk()
        root.withdraw()
        splash = StartupSplash(root)
        app = FightEmpireApp(root, startup_progress=splash.update)
        splash.close()
        splash = None
        root.deiconify()
        root.lift()
        root.focus_force()
    except Exception as exc:
        if splash is not None:
            splash.close()
        if root is not None:
            root.deiconify()
        report_path, _ = write_crash_report(type(exc), exc, exc.__traceback__, "Application startup")
        error_message = "MMA Warriors could not start. Your saves were not changed."
        if report_path:
            error_message += f"\n\nCrash report: {report_path}"
        messagebox.showerror(
            "MMA Warriors failed to start",
            error_message,
        )
        # The startup failure was already written above; avoid a duplicate report on re-raise.
        sys.excepthook = sys.__excepthook__
        raise
    root.mainloop()
