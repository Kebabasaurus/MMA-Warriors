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
from views import ViewMixin
from events import EventMixin
from fight_engine import FightEngineMixin
from world import WorldMixin
from persistence import PersistenceMixin, configure_runtime_logging, install_global_exception_handlers, register_crash_app, write_crash_report
from awards import AwardsMixin


class FightEmpireApp(
    UIMixin,
    AdminMixin,
    SeedMixin,
    ViewMixin,
    EventMixin,
    FightEngineMixin,
    WorldMixin,
    PersistenceMixin,
    AwardsMixin,
):
    def __init__(self, root):
        self.root = root
        self.root.report_callback_exception = self.handle_uncaught_exception
        register_crash_app(self)
        self.root.title(GAME_NAME)
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

        self.cash = 275_000
        self.company_pop = 38
        self.company_stability = 52
        self.theme_name = "UFC"
        self.player_company_name = PLAYER_PROMOTION_NAME
        self.spectator_mode = False
        self.player_region = "USA"
        self.player_reputation = "Regional Player Company"
        self.month = 1
        self.week = 1
        self.name_counts = {}
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.belt_history = self.blank_belt_history()
        self.roster = self.seed_roster()
        self.free_agents = self.seed_free_agents()
        self.promotions = self.seed_promotions()
        self.combat_sport_worlds = self.seed_combat_sport_worlds()
        self.player_combat_divisions = {}
        self.regions = self.seed_regions()
        self.gyms = self.seed_gyms()
        self.sync_gym_membership()
        self.result_history = []
        self.result_records = []
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
        self.academy = self.academy_defaults()
        self.inbox = []
        self.inbox_hidden_types = set()
        self.owner_goals = self.seed_owner_goals()
        self.rules = {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200, "auto_renew_enabled": False, "scouting_mode": False, "autosave_enabled": True, "autosave_weekly_keep": 12, "autosave_monthly_keep": 24, "save_backup_keep": 60}
        self.rules["allow_mixed_gender"] = False
        self.broadcasters = [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]
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

        self.event_name = tk.StringVar(value=self.default_event_name())
        self.venue = tk.StringVar(value="Regional Arena")
        self.event_region = tk.StringVar(value="USA")
        self.event_city = tk.StringVar(value="Las Vegas")
        self.event_broadcaster = tk.StringVar(value="No Coverage")
        self.card_tier = tk.StringVar(value="Main Card")
        self.event_month = tk.IntVar(value=1)
        self.event_week = tk.IntVar(value=1)
        self.title_fight = tk.BooleanVar(value=False)
        self.main_event = tk.BooleanVar(value=False)
        self.weight_filter = tk.StringVar(value="All")
        self.roster_gender_filter = tk.StringVar(value="All")
        self.roster_status_filter = tk.StringVar(value="All")
        self.roster_search = tk.StringVar(value="")
        self.available_weight_filter = tk.StringVar(value="All")
        self.available_gender_filter = tk.StringVar(value="All")
        self.available_status_filter = tk.StringVar(value="Ready")
        self.available_search = tk.StringVar(value="")
        self.market_weight_filter = tk.StringVar(value="All")
        self.market_gender_filter = tk.StringVar(value="All")
        self.ranking_gender_filter = tk.StringVar(value="All")
        self.ranking_weight_filter = tk.StringVar(value="All")
        self.result_search = tk.StringVar(value="")
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
        self.media_fighter_choice = tk.StringVar(value="")
        self.media_target_choice = tk.StringVar(value="")

        self.configure_style()
        self.build_layout()
        self.refresh_all()



if __name__ == "__main__":
    configure_runtime_logging()
    install_global_exception_handlers()
    try:
        root = tk.Tk()
        app = FightEmpireApp(root)
    except Exception as exc:
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
