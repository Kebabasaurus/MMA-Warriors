import json
import random
import re
import sys
import traceback
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion


class ViewMixin:
    def refresh_header(self):
        self.sync_gym_membership()
        if getattr(self, "spectator_mode", False):
            self.stat_cash.config(text="World Simulation")
            self.stat_pop.config(text=f"{len(self.promotions)} active promotions")
            self.stat_stability.config(text=f"{len(self.free_agents)} free agents")
        else:
            self.stat_cash.config(text=f"Cash: ${self.cash:,.0f}")
            self.stat_pop.config(text=f"{self.player_company_name} popularity: {self.company_pop}")
            self.stat_stability.config(text=f"Stability: {self.company_stability}")
        self.stat_month.config(text=self.format_game_date())

    def refresh_current_screen(self, name=None):
        """Refresh only the visible page; hidden Tk tables are rebuilt on entry."""
        name = name or getattr(self, "current_tab_name", "game_menu")
        if hasattr(self, "ensure_screen_built"):
            self.ensure_screen_built(name)
        refreshers = {
            "game_menu": (self.refresh_game_menu,),
            "website": (self.refresh_website,),
            "assistant": (self.refresh_assistant,),
            "roster": (self.refresh_roster,),
            "contracts": (self.refresh_contracts,),
            "companies": (self.refresh_companies,),
            "regions": (self.refresh_regions,),
            "results": (self.refresh_results,),
            "company_editor": (self.refresh_company_editor,),
            "inbox": (self.refresh_inbox,),
            "staff": (self.refresh_staff,),
            "scouting": (self.refresh_scouting_center,),
            "finance": (self.refresh_finance,),
            "booking": (self.refresh_available, self.refresh_card, self.refresh_upcoming),
            "market": (self.refresh_market,),
            "world": (self.refresh_world,),
            "regional_prospects": (self.refresh_regional_prospects,),
            "fighter_search": (self.refresh_world_fighter_search,),
            "rankings": (self.refresh_rankings,),
            "editor": (self.refresh_database_editor,),
            "sim_lab": (self.refresh_sim_fighter_choices,),
            "log": (self.write_log,),
        }
        for refresher in refreshers.get(name, ()):
            refresher()

    def refresh_all(self, full=False):
        """Refresh game chrome and either the visible page or every page.

        A full refresh remains available for startup and validation. Routine
        gameplay uses lazy page refreshes, avoiding thousands of invisible Tk
        row insertions after every simulation step.
        """
        self.refresh_header()
        if full:
            for name in (
                "game_menu", "roster", "contracts", "booking", "market",
                "website", "assistant", "companies", "regions", "results",
                "company_editor", "inbox", "staff", "scouting", "finance", "world", "regional_prospects", "fighter_search",
                "rankings", "sim_lab", "editor",
            ):
                self.refresh_current_screen(name)
        else:
            self.refresh_current_screen()
        self.refresh_spectator_controls()
        academy_refresh = getattr(self, "_academy_window_refresh", None)
        if callable(academy_refresh):
            try:
                academy_refresh()
            except tk.TclError:
                self._academy_window_refresh = None

    def refresh_spectator_controls(self):
        if hasattr(self, "advance_button"):
            if getattr(self, "spectator_mode", False):
                self.advance_button.pack_forget()
            elif not self.advance_button.winfo_manager():
                self.advance_button.pack(side="right", padx=(6, 0), ipady=2)
        if not hasattr(self, "spectator_sim_panel"):
            return
        if getattr(self, "spectator_mode", False):
            self.spectator_sim_panel.pack(fill="x", pady=(8, 0))
            if hasattr(self, "spectator_sim_status"):
                latest = self.ai_event_archive[0].get("event_name", "No events yet") if self.ai_event_archive else "No events hosted yet"
                self.spectator_sim_status.config(text=f"Observer mode: {self.format_game_date()}. Latest world event: {latest}.")
        else:
            self.spectator_sim_panel.pack_forget()

    def open_guided_first_week(self):
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - First Week")
        window.geometry("720x540")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="YOUR FIRST WEEK", style="ScreenTitle.TLabel").pack(fill="x", padx=10, pady=(10, 4))
        text = tk.Text(window, wrap="word", font=("Tahoma", 10), bg=self.colors["cream"], fg=self.colors["text"], padx=14, pady=14)
        text.pack(fill="both", expand=True, padx=10, pady=8)
        text.insert("end", "1. Read the Inbox and Personal Assistant for contract, injury, and owner-goal pressure.\n\n")
        text.insert("end", "2. Inspect the Roster. Double-click a fighter for their style, detailed skills, history, career arc, camp, and market value.\n\n")
        text.insert("end", "3. Build an event in Matchmaking. The first fight is the main event; use title/interim controls only when the division calls for it.\n\n")
        text.insert("end", "4. Choose camp focuses before scheduling. Longer camps, gym fit, morale, recovery, and weight management all matter.\n\n")
        text.insert("end", "5. Schedule by Month and Week, then advance. When a due show is ready, choose to watch it round by round or simulate it.\n\n")
        text.insert("end", "6. Use World and Companies to scout rival strategies. Their events, signings, title changes, retirements, and pivots are recorded in the World Chronicle.\n\n")
        text.insert("end", "There is no single correct card. A smart promotion balances sporting credibility, developing talent, fighter morale, regional interest, and finances.")
        text.config(state="disabled")
        ttk.Button(window, text="Open Inbox", command=lambda: (window.destroy(), self.select_tab("inbox"))).pack(pady=(0, 10))

    def rank_value(self, fighter):
        """Rank fighters by competitive achievement first, with ability as a tiebreaker."""
        champ = 75 if fighter.champion else 0
        bouts = fighter.record_w + fighter.record_l + fighter.record_d
        win_rate = (fighter.record_w + fighter.record_d * 0.5) / max(1, bouts)
        record_merit = (
            (fighter.record_w - fighter.record_l) * 1.15
            + (win_rate - 0.5) * 32
            + min(18, bouts * 0.18)
        )
        elo = (getattr(fighter, "elo_rating", 1500) - 1500) / 6
        form = max(-36, min(36, fighter.momentum * 6))
        streak = min(20, max(0, getattr(fighter, "career_win_streak", 0)) * 3)
        activity = max(0, 14 - fighter.fatigue // 5)
        return round(
            champ + elo + record_merit + fighter.overall * 0.55
            + fighter.popularity * 0.18 + form + streak + activity
        )

    def fighter_activity_rating(self, fighter):
        """Recent competitive activity, not availability or current fight form."""
        last_month = max(0, int(getattr(fighter, "last_fight_month", 0) or 0))
        if not last_month:
            for entry in getattr(fighter, "bout_rating_history", None) or []:
                match = re.search(r"Month\s+(\d+)", str(entry.get("date", "")) if isinstance(entry, dict) else "")
                if match:
                    last_month = max(last_month, int(match.group(1)))
        if not last_month:
            return 35 if (fighter.record_w + fighter.record_l + fighter.record_d) else 20
        months_out = max(0, int(self.month) - last_month)
        if months_out <= 1:
            return 100
        if months_out <= 3:
            return 88
        if months_out <= 6:
            return 72
        if months_out <= 9:
            return 58
        if months_out <= 12:
            return 45
        if months_out <= 18:
            return 30
        return 15

    def fighter_competitiveness_rating(self, fighter):
        """Rates recent opposition and results without changing fight-engine odds."""
        bouts = [entry for entry in (getattr(fighter, "bout_rating_history", None) or []) if isinstance(entry, dict)]
        if not bouts:
            total = fighter.record_w + fighter.record_l + fighter.record_d
            win_rate = fighter.record_w / max(1, total)
            return max(20, min(95, round(30 + (fighter.overall - 50) * 0.8 + min(12, total) * 1.2 + (win_rate - 0.5) * 24)))
        weighted_score = weight_total = 0.0
        for index, entry in enumerate(bouts[:8]):
            weight = max(0.35, 1 - index * 0.1)
            opponent_overall = int(entry.get("opponent_overall", 65) or 65)
            opponent_elo = int(entry.get("opponent_elo", 1500) or 1500)
            opposition = max(0, min(100, 20 + (opponent_overall - 50) * 1.2 + (opponent_elo - 1400) * 0.1))
            result_bonus = {"W": 18, "D": 11, "L": 6}.get(str(entry.get("result", "")).upper(), 5)
            weighted_score += (opposition * 0.82 + result_bonus) * weight
            weight_total += weight
        return max(0, min(100, round(weighted_score / max(1, weight_total))))

    def p4p_value(self, fighter):
        champ = 85 if fighter.champion else 0
        record_quality = fighter.record_w * 2.6 - fighter.record_l * 5
        prime = 10 if fighter.prime_start <= fighter.age <= fighter.prime_end else -max(0, fighter.age - fighter.prime_end) * 1.3
        activity = max(0, 18 - fighter.fatigue // 5)
        elo = (getattr(fighter, "elo_rating", 1500) - 1500) / 3.2
        return round(champ + elo + fighter.overall * 1.8 + record_quality + fighter.momentum * 8 + fighter.popularity * 0.18 + activity + prime)

    def fighter_career_stage(self, fighter):
        if fighter.age < fighter.prime_start:
            return "Developing"
        if fighter.age <= fighter.prime_end:
            return "Established"
        if fighter.age <= fighter.prime_end + 3:
            return "Veteran"
        return "Late Career"

    def upside_assessment(self, fighter):
        gap = max(0, fighter.potential - fighter.overall)
        if gap >= 18:
            return "Elite upside"
        if gap >= 10:
            return "High upside"
        if gap >= 4:
            return "Some upside"
        return "Near ceiling"

    def fighter_matches_status_filter(self, fighter, selected):
        if selected == "All":
            return True
        if selected == "Ready":
            return not fighter.injured and fighter.fatigue < 45
        if selected == "Champion":
            return fighter.champion
        if selected == "Injured":
            return bool(fighter.injured)
        if selected == "Tired":
            return fighter.fatigue >= 45
        if selected == "Expiring":
            return fighter.contract_months <= 3
        if selected == "Unhappy":
            return fighter.morale < 45
        if selected == "Closed Division":
            return self.fighter_in_closed_player_division(fighter)
        return True

    def fighter_current_roster_status(self, fighter):
        """Describe whether a fighter can actually be booked from the current week."""
        if getattr(fighter, "retired", False):
            return "Retired"
        if fighter.injured:
            return fighter.status
        for fight in getattr(self, "booked", []):
            if fighter.name in self.event_fight_participants(fight):
                return "On draft card"
        for event in getattr(self, "scheduled_events", []):
            if any(fighter.name in self.event_fight_participants(fight) for fight in event.get("fights", [])):
                return f"Booked {self.event_date_label(event)}"
        if not self.fighter_available_for_date(fighter, self.month, self.week):
            return self.fighter_return_label(fighter)
        if getattr(fighter, "retirement_pending", False):
            return "Retirement bout due"
        if fighter.fatigue >= 45:
            return f"Needs rest {fighter.fatigue}"
        return "Ready"

    def fighter_matches_text_filter(self, fighter, query):
        if not query:
            return True
        text = " ".join([
            fighter.name,
            fighter.weight,
            fighter.gender,
            fighter.nationality,
            fighter.record,
            fighter.region,
            fighter.style,
            fighter.behaviour,
            fighter.trait,
            fighter.camp,
            fighter.status,
        ]).lower()
        return query.lower() in text

    def fighter_display_name(self, fighter):
        if fighter.champion:
            return f"{fighter.name} (C)"
        if getattr(fighter, "interim_champion", False):
            return f"{fighter.name} (IC)"
        return fighter.name

    def active_player_division_weights(self, gender="All"):
        """Return only divisions the player has not explicitly closed."""
        closed = set(getattr(self, "closed_divisions", set()))
        genders = ("Male", "Female") if gender == "All" else (gender,)
        return [weight for weight in WEIGHTS if any(self.belt_key(candidate_gender, weight) not in closed for candidate_gender in genders)]

    def player_roster_filter_weights(self, gender="All"):
        """Roster filters include occupied closed divisions so contracted fighters never disappear."""
        active = set(self.active_player_division_weights(gender))
        occupied = {
            fighter.weight for fighter in self.roster
            if gender == "All" or fighter.gender == gender
        }
        return [weight for weight in WEIGHTS if weight in active or weight in occupied]

    def player_owns_fighter(self, fighter):
        fighter_key = self.fighter_identity_key(fighter)
        return any(candidate is fighter or self.fighter_identity_key(candidate) == fighter_key for candidate in self.roster)

    def promotion_owning_fighter(self, fighter):
        """Return the AI MMA promotion that currently owns this fighter, if any."""
        for promo in getattr(self, "promotions", []):
            if fighter in getattr(promo, "roster", []):
                return promo
        return None

    def fighter_in_closed_player_division(self, fighter):
        return self.player_owns_fighter(fighter) and self.belt_key(fighter.gender, fighter.weight) in set(getattr(self, "closed_divisions", set()))

    def cut_player_fighter(self, fighter, parent=None):
        """Release a rostered fighter stranded in a closed division.

        Closing a division releases everyone in it, but a fighter can still end up
        in a shut class afterwards (a weight move, or a signing). Without this they
        are unbookable and stuck on the payroll, so give them a clean paid exit."""
        if not self.player_owns_fighter(fighter):
            messagebox.showinfo("Cut fighter", "That fighter is not on your roster.", parent=parent)
            return False
        if not self.fighter_in_closed_player_division(fighter):
            messagebox.showinfo(
                "Cut fighter",
                f"{fighter.name} competes in an active division. Move them to another class, close the division, or let the contract expire.",
                parent=parent,
            )
            return False
        if fighter.name in self.scheduled_fighter_names(include_booked=True):
            messagebox.showwarning(
                "Cut fighter",
                f"{fighter.name} is booked on an upcoming card. Remove that bout before releasing them.",
                parent=parent,
            )
            return False
        remaining = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0) - int(getattr(fighter, "contract_fights_completed", 0) or 0))
        severance = max(0, int(getattr(fighter, "purse", 0) or 0)) * max(1, remaining)
        detail = f"{remaining} guaranteed fight(s) remaining" if remaining else "one fight purse"
        if not messagebox.askyesno(
            "Cut fighter",
            f"Release {fighter.name} ({fighter.gender} {fighter.weight}) to free agency?\n\n"
            f"Severance: ${severance:,} ({detail})\n"
            f"Cash after release: ${self.cash - severance:,}\n\n"
            "This cannot be undone, and rival promotions can sign them immediately.",
            parent=parent,
        ):
            return False
        self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
            fighter, self.roster, self.belts, self.interim_belts, self.belt_history, "Released by the promotion."
        )
        self.vacate_special_belts_held_by(fighter, "Released by the promotion.")
        if severance:
            self.cash -= severance
            self.record_finance_transaction(f"Contract severance: {fighter.name}", costs=severance)
        fighter.champion = False
        fighter.interim_champion = False
        fighter.contract_months = 0
        fighter.exclusive = False
        fighter.contract_type = "Free Agent"
        fighter.guaranteed_fights = 0
        fighter.contract_fights_completed = 0
        fighter.comeback_contract = False
        fighter.ai_offer_company = ""
        fighter.ai_offer_purse = fighter.ai_offer_months = fighter.ai_offer_signing_bonus = 0
        fighter.free_agent_months = 0
        fighter.fight_history = ([f"Month {self.month}: Released by {self.player_company_name} after the {fighter.weight} division closed."] + (fighter.fight_history or []))[:60]
        if fighter in self.roster:
            self.roster.remove(fighter)
        if fighter not in self.free_agents:
            self.free_agents.append(fighter)
        note = f"{self.player_company_name} released {fighter.name} from its closed {fighter.gender} {fighter.weight} division."
        self.news.insert(0, note)
        self.inbox.append({
            "subject": f"Fighter Released - {fighter.name}",
            "body": f"{note} Severance paid: ${severance:,}.",
            "type": "Roster", "resolved": True, "seen": True,
        })
        self.record_change("Roster", fighter.name, "Released", "Cut from a closed division", 2)
        if parent is not None and parent.winfo_exists():
            parent.destroy()
        self.refresh_all()
        messagebox.showinfo("Fighter released", f"{fighter.name} is now a free agent. Severance of ${severance:,} was paid.")
        return True

    def player_weight_move_targets(self, fighter):
        """Only player-operated destinations are offered; body suitability is assessed separately."""
        closed = set(getattr(self, "closed_divisions", set()))
        return [weight for weight in WEIGHTS if self.belt_key(fighter.gender, weight) not in closed]

    def refresh_player_division_filter_options(self, target=None):
        """Keep roster/matchmaking selectors aligned with the division manager."""
        targets = (target,) if target else ("roster", "matchmaking")
        mapping = {
            "roster": ("roster_gender_filter", "weight_filter", "roster_weight_combo"),
            "matchmaking": ("available_gender_filter", "available_weight_filter", "available_weight_combo"),
        }
        for key in targets:
            gender_attr, weight_attr, combo_attr = mapping.get(key, (None, None, None))
            if not gender_attr or not hasattr(self, gender_attr):
                continue
            gender = getattr(self, gender_attr).get()
            weights = self.player_roster_filter_weights(gender) if key == "roster" else self.active_player_division_weights(gender)
            values = ["All"] + weights
            combo = getattr(self, combo_attr, None)
            if combo:
                combo.configure(values=values)
            weight_var = getattr(self, weight_attr)
            if weight_var.get() not in values:
                weight_var.set("All")

    def refresh_roster(self):
        self.refresh_player_division_filter_options("roster")
        self.roster_tree.delete(*self.roster_tree.get_children())
        self.roster_tree_fighters = {}
        selected = self.weight_filter.get()
        gender = self.roster_gender_filter.get() if hasattr(self, "roster_gender_filter") else "All"
        status = self.roster_status_filter.get() if hasattr(self, "roster_status_filter") else "All"
        query = self.roster_search.get().strip() if hasattr(self, "roster_search") else ""
        age_min, age_max = self.filter_range("roster_age_min", "roster_age_max", 16, 60)
        ovr_min, ovr_max = self.filter_range("roster_ovr_min", "roster_ovr_max", 0, 100)
        pop_min = self.filter_value("roster_pop_min", 0, 0, 100)
        fighters = sorted(self.roster, key=lambda f: (f.weight, -(f.champion * 1000 + f.popularity + f.overall)))
        for row_index, fighter in enumerate(fighters):
            if selected != "All" and fighter.weight != selected:
                continue
            if gender != "All" and fighter.gender != gender:
                continue
            closed_division = self.fighter_in_closed_player_division(fighter)
            current_status = "DIVISION CLOSED - MOVE REQUIRED" if closed_division else self.fighter_current_roster_status(fighter)
            if status == "Ready" and current_status != "Ready":
                continue
            if status != "Ready" and not self.fighter_matches_status_filter(fighter, status):
                continue
            if not self.fighter_matches_text_filter(fighter, query):
                continue
            if not (age_min <= fighter.age <= age_max and ovr_min <= fighter.overall <= ovr_max and fighter.popularity >= pop_min):
                continue
            name = self.fighter_display_name(fighter)
            if closed_division:
                row_tag = "closed_division"
            elif fighter.injured:
                row_tag = "injured"
            elif 0 < fighter.contract_months <= 3:
                row_tag = "expiring"
            elif fighter.champion:
                row_tag = "champ"
            else:
                row_tag = ""
            row_id = self.fighter_tree_row_id("roster", fighter, row_index)
            self.roster_tree_fighters[row_id] = fighter
            self.roster_tree.insert("", "end", iid=row_id, tags=(row_tag,) if row_tag else (), values=(name, fighter.gender[0], fighter.weight, fighter.record, fighter.age, fighter.overall, fighter.popularity, fighter.momentum, fighter.morale, fighter.contract_months, current_status))
        visible = self.roster_tree.get_children()
        if visible and not self.roster_tree.selection():
            self.roster_tree.selection_set(visible[0])
            self.update_fighter_detail()

    def filter_value(self, attribute, default, minimum, maximum):
        """Read a numeric filter without a half-typed field breaking a table refresh."""
        try:
            value = int(getattr(self, attribute).get())
        except (AttributeError, ValueError, tk.TclError):
            value = default
        return max(minimum, min(maximum, value))

    def filter_range(self, minimum_attribute, maximum_attribute, lower, upper):
        minimum = self.filter_value(minimum_attribute, lower, lower, upper)
        maximum = self.filter_value(maximum_attribute, upper, lower, upper)
        return min(minimum, maximum), max(minimum, maximum)

    def reset_roster_filters(self):
        self.roster_search.set("")
        self.weight_filter.set("All")
        self.roster_gender_filter.set("All")
        self.roster_status_filter.set("All")
        self.roster_age_min.set(16)
        self.roster_age_max.set(60)
        self.roster_ovr_min.set(0)
        self.roster_ovr_max.set(100)
        self.roster_pop_min.set(0)
        self.refresh_roster()

    def open_division_management_window(self):
        """Open an explicit division manager; roster list filters never control this action."""
        window = tk.Toplevel(self.root)
        window.title("Manage Divisions")
        window.geometry("510x330")
        window.minsize(470, 300)
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        window.grab_set()

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="DIVISION MANAGEMENT", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=7)

        panel, body = self.section(window, "CLOSE OR REOPEN A PLAYER DIVISION")
        panel.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(body, text="Choose the division to manage. This is separate from the roster filters.", style="Inset.TLabel").pack(anchor="w", padx=10, pady=(10, 6))
        controls = ttk.Frame(body, style="Inset.TFrame")
        controls.pack(fill="x", padx=10, pady=4)
        gender_var = tk.StringVar(value="Male")
        weight_var = tk.StringVar(value=WEIGHTS[0])
        ttk.Label(controls, text="Gender", style="Inset.TLabel").pack(side="left", padx=(8, 4), pady=8)
        gender_combo = ttk.Combobox(controls, textvariable=gender_var, values=("Male", "Female"), state="readonly", width=12)
        gender_combo.pack(side="left", padx=(0, 14), pady=8)
        ttk.Label(controls, text="Weight class", style="Inset.TLabel").pack(side="left", padx=(0, 4), pady=8)
        weight_combo = ttk.Combobox(controls, textvariable=weight_var, values=WEIGHTS, state="readonly", width=20)
        weight_combo.pack(side="left", padx=(0, 8), pady=8)

        status_var = tk.StringVar()
        info_var = tk.StringVar()
        ttk.Label(body, textvariable=status_var, style="Subtle.TLabel").pack(anchor="w", padx=10, pady=(12, 3))
        ttk.Label(body, textvariable=info_var, style="Inset.TLabel", wraplength=455, justify="left").pack(anchor="w", padx=10)
        actions = ttk.Frame(body, style="Inset.TFrame")
        actions.pack(fill="x", padx=10, pady=(16, 10))
        action_button = ttk.Button(actions, style="Accent.TButton")
        action_button.pack(side="left")
        ttk.Button(actions, text="Done", command=window.destroy).pack(side="right")

        def update_details(_event=None):
            gender, weight = gender_var.get(), weight_var.get()
            key = self.belt_key(gender, weight)
            fighters = [fighter for fighter in self.roster if fighter.gender == gender and fighter.weight == weight]
            if key in set(getattr(self, "closed_divisions", set())):
                status_var.set(f"Status: CLOSED — {gender} {weight}")
                info_var.set("Reopening is free. The title remains vacant and you rebuild by signing fighters, then booking cards.")
                action_button.config(text="Reopen Division", command=lambda: perform_action(False))
            else:
                payroll = sum(max(0, getattr(fighter, "purse", 0)) for fighter in fighters)
                status_var.set(f"Status: OPEN — {gender} {weight} ({len(fighters)} contracted fighter(s))")
                info_var.set(f"Closing releases the contracted fighters, vacates titles and removes booked bouts. Estimated show payroll removed: ${payroll:,}.")
                action_button.config(text="Close Division", command=lambda: perform_action(True))

        def perform_action(closing):
            completed = self.close_selected_division(gender_var.get(), weight_var.get()) if closing else self.reopen_selected_division(gender_var.get(), weight_var.get())
            if completed:
                update_details()

        gender_combo.bind("<<ComboboxSelected>>", update_details)
        weight_combo.bind("<<ComboboxSelected>>", update_details)
        update_details()
        window.protocol("WM_DELETE_WINDOW", window.destroy)

    def close_selected_division(self, gender=None, weight=None):
        """Release one player-owned gender/weight division and permanently vacate its titles."""
        gender = gender or (self.roster_gender_filter.get() if hasattr(self, "roster_gender_filter") else "All")
        weight = weight or (self.weight_filter.get() if hasattr(self, "weight_filter") else "All")
        if gender == "All" or weight == "All":
            messagebox.showinfo("Choose a division", "Choose one gender and one weight class in the roster filters before closing a division.")
            return False
        key = self.belt_key(gender, weight)
        fighters = [fighter for fighter in self.roster if fighter.gender == gender and fighter.weight == weight]
        if not fighters:
            messagebox.showinfo("Division already empty", f"{gender} {weight} has no fighters under contract.")
            return False
        estimated_show_payroll = sum(max(0, getattr(fighter, "purse", 0)) for fighter in fighters)
        booked_names = {fighter.name for fighter in fighters}
        booked_purse_exposure = 0
        future_bouts = 0
        for fight in list(getattr(self, "booked", [])):
            if set(self.event_fight_participants(fight)) & booked_names:
                future_bouts += 1
                for name in self.event_fight_participants(fight):
                    fighter = self.get_fighter(name)
                    if fighter:
                        booked_purse_exposure += max(0, getattr(fighter, "purse", 0))
        for event in list(getattr(self, "scheduled_events", [])):
            for fight in event.get("fights", []):
                if set(self.event_fight_participants(fight)) & booked_names:
                    future_bouts += 1
                    for name in self.event_fight_participants(fight):
                        fighter = self.get_fighter(name)
                        if fighter:
                            booked_purse_exposure += max(0, getattr(fighter, "purse", 0))
        warning = (f"Close {gender} {weight}?\n\nThis releases {len(fighters)} contracted fighter(s) to free agency, "
                   "vacates its titles, and removes their future bouts from your cards.\n\n"
                   f"Estimated show payroll removed: ${estimated_show_payroll:,}\n"
                   f"Future booked purse exposure removed: ${booked_purse_exposure:,} across {future_bouts} bout(s).\n\n"
                   "No closure fee is charged. You can reopen it later from this screen, but rebuilding the division will require new signings.")
        if not messagebox.askyesno("Close division", warning, icon="warning"):
            return False
        self.booked = [fight for fight in self.booked if not (set(self.event_fight_participants(fight)) & booked_names)]
        removed_bouts = 0
        for event in self.scheduled_events:
            original = list(event.get("fights", []))
            event["fights"] = [fight for fight in original if not (set(self.event_fight_participants(fight)) & booked_names)]
            removed_bouts += len(original) - len(event["fights"])
        self.scheduled_events = [event for event in self.scheduled_events if event.get("fights")]
        self.belts = self.normalize_belts(self.belts)
        self.interim_belts = self.normalize_belts(self.interim_belts)
        self.belt_history = self.normalize_belt_history(self.belt_history)
        primary_holder, interim_holder = self.belts.get(key, ""), self.interim_belts.get(key, "")
        self.belts[key], self.interim_belts[key] = "", ""
        if primary_holder:
            self.belt_history = self.record_belt_history(self.belt_history, key, "Division Closed", primary_holder, "Player closed the division.")
        if interim_holder:
            self.belt_history = self.record_belt_history(self.belt_history, key, "Division Closed", interim_holder, "Player closed the division.")
        for fighter in fighters:
            fighter.champion = False
            fighter.interim_champion = False
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.ai_offer_company = ""
            fighter.ai_offer_purse = fighter.ai_offer_months = fighter.ai_offer_signing_bonus = 0
            self.free_agents.append(fighter)
        self.roster = [fighter for fighter in self.roster if fighter not in fighters]
        self.closed_divisions = set(getattr(self, "closed_divisions", set()))
        self.closed_divisions.add(key)
        self.player_managed_divisions = set(getattr(self, "player_managed_divisions", set()))
        self.player_managed_divisions.add(key)
        story = f"{self.player_company_name} closed its {gender} {weight} division, releasing {len(fighters)} fighter(s) to free agency."
        self.news.insert(0, story)
        finance_detail = f"Estimated show payroll removed ${estimated_show_payroll:,}; future booked purse exposure removed ${booked_purse_exposure:,}."
        self.world_chronicle.insert(0, {"month": self.month, "week": self.week, "category": "Company", "headline": story, "details": f"{removed_bouts} future bout(s) were removed and the title was vacated. {finance_detail}"})
        if hasattr(self, "record_finance_transaction"):
            self.record_finance_transaction(f"Closed {gender} {weight} division - purse exposure removed ${booked_purse_exposure:,}")
        if hasattr(self, "ensure_finance_defaults"):
            self.ensure_finance_defaults()
            self.finance["ledger"].insert(0, f"Month {self.month}: Closed {gender} {weight}; estimated show payroll removed ${estimated_show_payroll:,}, future booked purse exposure removed ${booked_purse_exposure:,}.")
            self.finance["ledger"] = self.finance["ledger"][:80]
        self.refresh_card()
        self.refresh_all(full=False)
        messagebox.showinfo("Division closed", f"Released {len(fighters)} fighter(s) to free agency. Removed {removed_bouts} future bout(s).\n\nEstimated show payroll removed: ${estimated_show_payroll:,}\nFuture booked purse exposure removed: ${booked_purse_exposure:,}")
        return True

    def reopen_selected_division(self, gender=None, weight=None):
        """Make a previously closed division available for player-led rebuilding."""
        gender = gender or (self.roster_gender_filter.get() if hasattr(self, "roster_gender_filter") else "All")
        weight = weight or (self.weight_filter.get() if hasattr(self, "weight_filter") else "All")
        if gender == "All" or weight == "All":
            messagebox.showinfo("Choose a division", "Choose one gender and one weight class in the roster filters before reopening a division.")
            return False
        key = self.belt_key(gender, weight)
        self.closed_divisions = set(getattr(self, "closed_divisions", set()))
        if key not in self.closed_divisions:
            messagebox.showinfo("Division open", f"{gender} {weight} is already open.")
            return False
        self.closed_divisions.remove(key)
        self.player_managed_divisions = set(getattr(self, "player_managed_divisions", set()))
        self.player_managed_divisions.discard(key)
        if weight not in self.weight_classes:
            self.weight_classes.append(weight)
        story = f"{self.player_company_name} reopened its {gender} {weight} division and can now rebuild it through free agency."
        self.news.insert(0, story)
        self.world_chronicle.insert(0, {"month": self.month, "week": self.week, "category": "Company", "headline": story, "details": "Reopening is free. The title remains vacant until the player builds the division, and future costs come from signing fighters and booking cards."})
        if hasattr(self, "ensure_finance_defaults"):
            self.ensure_finance_defaults()
            self.finance["ledger"].insert(0, f"Month {self.month}: Reopened {gender} {weight}; no fee charged, rebuild costs depend on signings and booked cards.")
            self.finance["ledger"] = self.finance["ledger"][:80]
        self.refresh_all(full=False)
        messagebox.showinfo("Division reopened", "The division is open and remains empty until you sign fighters. Reopening is free; the title stays vacant until you build it.")
        return True

    def refresh_contracts(self):
        if not hasattr(self, "contracts_tree"):
            return
        self.contracts_tree.delete(*self.contracts_tree.get_children())
        self.contracts_tree_fighters = {}
        payroll = 0
        expiring = 0
        final_month = 0
        fight_counted = 0
        champs_expiring = []
        show_filter = self.contracts_filter.get() if hasattr(self, "contracts_filter") else "All"
        division_ranks = self.player_division_rank_map()
        for row_index, fighter in enumerate(sorted(self.roster, key=lambda f: (not getattr(f, "comeback_contract", False), f.contract_months, -f.popularity, -f.overall))):
            payroll += fighter.purse
            months = fighter.contract_months
            is_comeback = bool(getattr(fighter, "comeback_contract", False))
            final_retirement_bout = bool(getattr(fighter, "retirement_pending", False))
            if is_comeback:
                fight_counted += 1
                remaining_fights = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0) - int(getattr(fighter, "contract_fights_completed", 0) or 0))
            elif months <= 3 and not final_retirement_bout:
                expiring += 1
                if fighter.champion:
                    champs_expiring.append(fighter.name)
            if months <= 1 and not is_comeback and not final_retirement_bout:
                final_month += 1
            exclusive = getattr(fighter, "exclusive", True)
            if show_filter == "Expiring (<=3 mo)" and (is_comeback or final_retirement_bout or months > 3):
                continue
            if show_filter == "Final month" and (is_comeback or final_retirement_bout or months > 1):
                continue
            if show_filter == "Non-Exclusive" and exclusive:
                continue
            if is_comeback:
                tag, status = "", f"Comeback: {remaining_fights} fight{'s' if remaining_fights != 1 else ''} left"
                remaining_label, expiry_label = f"{remaining_fights} fight{'s' if remaining_fights != 1 else ''}", "Fight-counted"
            elif final_retirement_bout:
                tag, status = "", "Retirement bout due"
                remaining_label, expiry_label = "Final bout", "Fight-counted"
            elif months <= 0:
                tag, status = "expired", "EXPIRED"
                remaining_label, expiry_label = self.contract_time_remaining_label(months), self.contract_expiry_date_label(months)
            elif months <= 1:
                tag, status = "final", "Final month"
                remaining_label, expiry_label = self.contract_time_remaining_label(months), self.contract_expiry_date_label(months)
            elif months <= 3:
                tag, status = "soon", ("Champion leverage" if fighter.champion else "Expiring soon")
                remaining_label, expiry_label = self.contract_time_remaining_label(months), self.contract_expiry_date_label(months)
            else:
                tag, status = "", ("Champion leverage" if fighter.champion else fighter.status)
                remaining_label, expiry_label = self.contract_time_remaining_label(months), self.contract_expiry_date_label(months)
            contract_type = getattr(fighter, "contract_type", "Exclusive" if exclusive else "Non-Exclusive")
            rank = division_ranks.get(self.fighter_identity_key(fighter))
            rank_label = "C" if fighter.champion else f"#{rank}" if rank else "-"
            row_id = self.fighter_tree_row_id("contract", fighter, row_index)
            self.contracts_tree_fighters[row_id] = fighter
            self.contracts_tree.insert("", "end", iid=row_id, tags=(tag,) if tag else (),
                                       values=(fighter.name, fighter.gender[0], fighter.weight, rank_label,
                                               fighter.popularity, fighter.overall,
                                               remaining_label, expiry_label, f"${fighter.purse:,}",
                                               contract_type, fighter.morale, status))
        if hasattr(self, "contracts_alert"):
            if champs_expiring:
                self.contracts_alert.config(text=f"⚠ {expiring} deal(s) expiring soon, including CHAMPION(S): {', '.join(champs_expiring)}. Renew now.", fg="#e86a5c")
            elif final_month:
                self.contracts_alert.config(text=f"⚠ {final_month} fighter(s) in their FINAL month. Renew before they leave.", fg="#e0a83a")
            elif expiring:
                self.contracts_alert.config(text=f"{expiring} fighter(s) expiring within 3 months.", fg=self.colors["gold"])
            else:
                self.contracts_alert.config(text="No contracts expiring soon.", fg=self.colors["text"])
        self.contracts_summary.config(text=f"{expiring} expiring soon | {final_month} final month | {fight_counted} fight-counted comeback deal(s) | est. show payroll ${payroll:,}")
        if hasattr(self, "auto_renew_button"):
            enabled = self.rules.get("auto_renew_enabled", False)
            self.auto_renew_button.config(text=f"Auto Renew: {'On' if enabled else 'Off'}")

    def contract_time_remaining_label(self, months):
        months = max(0, int(months or 0))
        if months <= 0:
            return "Expired"
        years, remainder = divmod(months, 12)
        if years and remainder:
            return f"{years}y {remainder}mo"
        if years:
            return f"{years}y"
        return f"{months} mo"

    def contract_expiry_date_label(self, months):
        """Contracts lapse at the first monthly processing boundary after their remaining term."""
        months = int(months or 0)
        if months <= 0:
            return "Expired"
        return self.format_game_date(self.month + months, 1)

    def selected_contract_fighter(self):
        selected = self.contracts_tree.selection() if hasattr(self, "contracts_tree") else []
        return getattr(self, "contracts_tree_fighters", {}).get(selected[0]) if selected else None

    def renew_selected_contract(self):
        fighter = self.selected_contract_fighter()
        if not fighter:
            return
        self.open_contract_negotiation(fighter, existing=True)

    def auto_negotiate_selected_contracts(self):
        selected = self.contracts_tree.selection() if hasattr(self, "contracts_tree") else []
        mapping = getattr(self, "contracts_tree_fighters", {})
        fighters = [mapping.get(row_id) for row_id in selected]
        fighters = [fighter for fighter in fighters if fighter]
        if not fighters:
            messagebox.showinfo("Auto Negotiate", "Select one or more fighters in Contracts first.")
            return
        report = self.auto_negotiate_player_contracts(fighters)
        lines = []
        for row in report["results"]:
            if row["status"] == "renewed":
                lines.append(f"RENEWED: {row['name']} - {row['months']} months, ${row['purse']:,}/fight")
            else:
                lines.append(f"NOT RENEWED: {row['name']} - {row['reason']}")
        heading = (f"{report['renewed']} renewed | {report['failed']} talks failed | "
                   f"{report['unaffordable']} deferred for cash | Cost ${report['cost']:,}")
        messagebox.showinfo("Auto Negotiation Results", heading + "\n\n" + "\n".join(lines[:40]))
        self.refresh_all(full=False)

    def toggle_auto_renew(self):
        self.rules["auto_renew_enabled"] = not self.rules.get("auto_renew_enabled", False)
        self.refresh_contracts()

    def view_contract_profile(self):
        fighter = self.selected_contract_fighter()
        if not fighter:
            return
        self.select_tab("roster")
        row_id = next((row_id for row_id, row_fighter in getattr(self, "roster_tree_fighters", {}).items() if row_fighter is fighter), None)
        if row_id:
            self.roster_tree.selection_set(row_id)
            self.roster_tree.see(row_id)
        self.update_fighter_detail()

    def update_fighter_detail(self, _event=None):
        selected = self.roster_tree.selection()
        if not selected:
            return
        fighter = getattr(self, "roster_tree_fighters", {}).get(selected[0])
        if fighter not in self.roster:
            self.roster_tree.selection_remove(*selected)
            return
        crown = " - Champion" if fighter.champion else (" - Interim Champion" if getattr(fighter, "interim_champion", False) else "")
        self.detail_name.config(text=f"{fighter.name}{crown}")
        self.draw_fighter_portrait(fighter)
        self.detail_lines.config(
            text=(
                f"{fighter.weight}\n"
                f"Record: {fighter.record}     Age: {fighter.age}     Height: {fighter.height or '-'}     Nationality: {fighter.nationality}\n"
                f"Based In: {fighter.region}\n"
                f"Style: {fighter.style}     Stance: {fighter.stance}     Behaviour: {fighter.behaviour}\n"
                f"Trait: {fighter.trait}     Camp: {fighter.camp}\n"
                f"Camp Focus: {fighter.camp_focus} ({fighter.camp_intensity})\n"
                f"Walk Weight: {fighter.walk_weight or self.default_walk_weight(fighter)} lb     Last Scale: {fighter.scale_weight or '-'} lb     Cut Penalty: {fighter.weight_cut_penalty}\n"
                f"Rival: {fighter.rival or 'None'}     Friend: {fighter.friend or 'None'}\n"
                f"Deal: {fighter.contract_type} / {fighter.contract_months} mo\n"
                f"Popularity: {fighter.popularity}     Momentum: {fighter.momentum}\n"
                f"Morale: {fighter.morale}     Purse: ${fighter.purse:,}\n"
                f"Star: {fighter.star_quality}     Media: {fighter.media_presence}     Sponsor: {fighter.sponsor_appeal}\n"
                f"Charisma: {fighter.charisma}     Pro: {fighter.professionalism}     Injury Risk: {fighter.injury_proneness}\n"
                f"Motivation: {fighter.motivation}     Camp: +{fighter.camp_boost} ({fighter.camp_weeks} wk, Q{fighter.camp_quality})\n"
                f"Annual Peaks: {self.annual_overall_chart(fighter)}\n"
                f"Recent Bio: {self.format_game_date_text(fighter.fight_history[0]) if fighter.fight_history else 'No fight history yet'}\n"
                f"Contract: {fighter.contract_months} mo     Fatigue: {fighter.fatigue}\n"
                f"Potential: {fighter.potential}     Ranking Score: {self.rank_value(fighter)}\n"
                f"Status: {fighter.status}"
            )
        )
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "takedown_defence", "ground_control", "submissions", "submission_defence", "recovery", "toughness", "fight_iq", "finishing_instinct", "star_quality", "charisma", "professionalism"):
            bar, value = self.skill_rows[key]
            score = getattr(fighter, key)
            bar.configure(value=score)
            value.configure(text=str(score))

    def clean_display_fighter_name(self, value):
        return str(value).replace(" (C)", "").replace(" (IC)", "").strip()

    def open_tree_fighter_profile(self, tree, name_column="name"):
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]
        name = item_id if self.find_fighter_anywhere(item_id) else ""
        if not name:
            values = tree.item(item_id, "values")
            try:
                columns = list(tree["columns"])
                index = columns.index(name_column)
                name = values[index]
            except (ValueError, IndexError):
                return
        fighter = self.find_fighter_anywhere(self.clean_display_fighter_name(name))
        if fighter:
            self.open_fighter_profile_window(fighter)

    def weight_abbreviation(self, weight):
        return {
            "Flyweight": "FLW",
            "Bantamweight": "BW",
            "Featherweight": "FTW",
            "Lightweight": "LW",
            "Welterweight": "WW",
            "Middleweight": "MW",
            "Light Heavyweight": "LHW",
            "Heavyweight": "HW",
        }.get(weight, weight[:3].upper())

    def fighter_display_division(self, fighter):
        if getattr(fighter, "sport_employer", "") and getattr(fighter, "primary_discipline", "MMA") != "MMA":
            return getattr(fighter, "sport_weight_class", "") or fighter.weight
        return fighter.weight

    def portrait_badge_text(self, fighter):
        sport = self.combat_sport_for_fighter(fighter) if getattr(fighter, "sport_employer", "") else ""
        if sport:
            label = {"Brazilian Jiu-Jitsu": "BJJ", "Kickboxing": "KB", "Muay Thai": "MT", "Wrestling": "WRE", "Boxing": "BOX"}.get(sport, sport[:3].upper())
            return f"{label} | RTG {round(self.combat_sport_display_rating(fighter, sport))}"
        origin = "GEN" if getattr(fighter, "generated", False) else "REAL"
        return f"{origin} | {self.weight_abbreviation(self.fighter_display_division(fighter))} | OVR {fighter.overall}"

    def fit_canvas_text(self, canvas, x, y, text, fill, max_width, base_size=9, weight="bold"):
        size = base_size
        item = None
        while size >= 6:
            if item:
                canvas.delete(item)
            item = canvas.create_text(x, y, text=text, fill=fill, font=("Tahoma", size, weight))
            bbox = canvas.bbox(item)
            if not bbox or bbox[2] - bbox[0] <= max_width:
                return item
            size -= 1
        return item

    def draw_profile_portrait(self, canvas, fighter):
        bg = fighter.portrait_bg or "#222222"
        accent = fighter.portrait_accent or "#c3a45d"
        canvas.delete("all")
        canvas.configure(bg=bg)
        # The canvas is 180px wide; draw around its actual centre so generated
        # profile cards never sit in the top-left or overlap their badge.
        canvas.create_rectangle(12, 10, 168, 170, fill=bg, outline=accent, width=3)
        canvas.create_oval(62, 28, 118, 84, fill=accent, outline="")
        canvas.create_polygon(35, 150, 55, 96, 125, 96, 145, 150, fill="#d7d7d7", outline="")
        canvas.create_rectangle(28, 148, 152, 166, fill=accent, outline="")
        initials = "".join(part[0] for part in fighter.name.replace("'", "").split()[:2]).upper()
        canvas.create_text(90, 58, text=initials, fill=bg, font=("Impact", 24))
        self.fit_canvas_text(canvas, 90, 157, self.portrait_badge_text(fighter), bg, 116, base_size=8)
        self.draw_portrait_status_markers(canvas, fighter, large=True)

    def draw_portrait_status_markers(self, canvas, fighter, large=False):
        """Overlay durable visual status badges on generated portrait cards."""
        size = 28 if large else 21
        right = 168 if large else 96
        top = 12 if large else 6
        if getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", ""):
            cx = right - size // 2
            cy = top + size // 2
            canvas.create_oval(cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2,
                               fill="#8d2029", outline="#ffd2d7", width=1)
            cross = max(3, size // 6)
            arm = max(7, size // 3)
            canvas.create_rectangle(cx - cross, cy - arm, cx + cross, cy + arm, fill="#ffffff", outline="")
            canvas.create_rectangle(cx - arm, cy - cross, cx + arm, cy + cross, fill="#ffffff", outline="")
        if getattr(fighter, "retired", False):
            cx = right - size // 2
            cy = top + size + 5 + size // 2 if (getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", "")) else top + size // 2
            canvas.create_oval(cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2,
                               fill="#315a70", outline="#bfe6f2", width=1)
            canvas.create_text(cx, cy + 1, text="RTD", fill="#ffffff", font=("Impact", max(7, size - 17)))
        elif getattr(fighter, "retirement_pending", False):
            cx = right - size // 2
            cy = top + size + 5 + size // 2 if (getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", "")) else top + size // 2
            canvas.create_oval(cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2,
                               fill="#b88717", outline="#fff0bd", width=1)
            canvas.create_text(cx, cy + 1, text="R", fill="#1b1710", font=("Impact", max(11, size - 8)))

    def fighter_title_reign_origin(self, fighter, company=""):
        if not getattr(fighter, "champion", False):
            return ""
        history = getattr(self, "belt_history", {})
        if company and company != self.player_company_name:
            promo = next((item for item in self.promotions if item.name == company), None)
            if promo:
                history = promo.belt_history or {}
        key = self.belt_key(fighter.gender, fighter.weight)
        entries = self.normalize_belt_history(history).get(key, [])
        entry = next((item for item in entries if item.get("fighter") == fighter.name and item.get("action") in ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed")), None)
        if not entry:
            return "Championship origin unavailable"
        appointed = "appointed" in str(entry.get("action", "")).lower() or "status normalized" in str(entry.get("note", "")).lower()
        origin = "Appointed inaugural champion" if appointed else "Won championship"
        return f"{origin} - {self.format_game_date_text(entry.get('date', ''))}"

    def fighter_profile_text(self, fighter):
        company = fighter.sport_employer if getattr(fighter, "sport_employer", "") else next((name for name, candidate in self.all_database_fighters_with_companies() if candidate.name == fighter.name), "Unknown")
        company_rank = self.rank_label_for_fighter(fighter, company, world=False)
        world_rank = self.rank_label_for_fighter(fighter, company, world=True)
        company_rank_text = self.profile_rank_text(fighter, company_rank, "Company")
        world_rank_text = self.profile_rank_text(fighter, world_rank, "World")
        sport = self.combat_sport_for_fighter(fighter) if getattr(fighter, "sport_employer", "") else ""
        sport_block = ""
        if sport:
            rating = self.combat_sport_display_rating(fighter, sport)
            gap = max(0, round(min(99, fighter.potential) - rating, 1))
            trend = self.combat_sport_rating_trend(fighter, sport, 12)
            stage = self.combat_sport_development_stage(fighter, sport)
            recent = (getattr(fighter, "sport_development_log", None) or [{}])[0]
            latest = "No recorded development change yet."
            if recent:
                skills = ", ".join(str(key).replace("_", " ").title() for key in recent.get("skills", [])[:3]) or "native skills"
                latest = f"{recent.get('reason', 'Training')}: {recent.get('change', 0):+} ({skills})"
            sport_block = (
                f"\n{sport} Development: Rating {rating:.1f} | Potential {fighter.potential} | Runway +{gap:.1f}\n"
                f"Career Stage: {stage} | 12-month trend {trend:+.1f} | Latest: {latest}\n"
            )
        peaks_line = "" if sport else f"Annual Peaks: {self.annual_overall_chart(fighter)}\n"
        title_status = "Champion" if fighter.champion else ("Interim Champion" if getattr(fighter, "interim_champion", False) else "Contender")
        special_titles = list(getattr(fighter, "special_titles", None) or [])
        if special_titles:
            title_status += " | " + ", ".join(f"{name} Champion" for name in special_titles)
        title_origin = self.fighter_title_reign_origin(fighter, company)
        title_origin_line = f"Championship Reign: {title_origin}\n" if title_origin else ""
        return (
            f"{fighter.name}\n"
            f"{fighter.gender} {self.fighter_display_division(fighter)} | {company}\n"
            f"Record: {fighter.record} | Age: {fighter.age} | Height: {fighter.height or '-'} | Nationality: {fighter.nationality}\n"
            f"Based In: {fighter.region}\n"
            f"{company_rank_text} | {world_rank_text} | Elo: {fighter.elo_rating}\n"
            f"Title Status: {title_status}\n"
            f"{title_origin_line}"
            f"Title Record: Primary {fighter.title_wins} wins / {fighter.title_defenses} defenses | "
            f"Interim {getattr(fighter, 'interim_title_wins', 0)} wins / {getattr(fighter, 'interim_title_defenses', 0)} defenses\n\n"
            f"Style: {fighter.style} | Stance: {fighter.stance} | Behaviour: {fighter.behaviour}\n"
            f"Trait: {fighter.trait} | Camp: {fighter.camp} | Plan: {fighter.camp_focus} ({fighter.camp_intensity})\n"
            f"{self.rivalry_summary(fighter)}\n\n"
            f"Popularity: {fighter.popularity} | Momentum: {fighter.momentum} | Morale: {fighter.morale}\n"
            f"Star: {fighter.star_quality} | Charisma: {fighter.charisma} | Media: {fighter.media_presence} | Sponsor: {fighter.sponsor_appeal}\n"
            f"Contract: {fighter.contract_type} | {fighter.contract_months} months | ${fighter.purse:,}/fight | Trust: {fighter.relationship_trust}\n\n"
            f"Walk Weight: {fighter.walk_weight or self.default_walk_weight(fighter)} lb | Last Scale: {fighter.scale_weight or '-'} lb | Cut Penalty: {fighter.weight_cut_penalty}\n"
            f"Fatigue: {fighter.fatigue} | Injury: {fighter.injured or 'None'} | {self.fighter_return_label(fighter)} | Status: {fighter.status}\n"
            f"Camp Boost: +{fighter.camp_boost} ({fighter.camp_weeks} wk, Q{fighter.camp_quality})\n"
            f"{sport_block}"
            f"{peaks_line}"
        )

    def rivalry_summary(self, fighter):
        """Readable rivalry / ally / media-heat line for the profile."""
        heat = getattr(fighter, "media_heat", 0)
        band = "cold" if heat < 20 else ("simmering" if heat < 45 else ("hot" if heat < 70 else "white-hot"))
        if fighter.rival:
            opponent = self.find_fighter_anywhere(fighter.rival) if hasattr(self, "find_fighter_anywhere") else None
            mutual = bool(opponent and getattr(opponent, "rival", "") == fighter.name)
            feud = "bitter mutual feud" if mutual else "has called them out"
            rivalry_heat = getattr(fighter, "rivalry_heat", 0)
            rematch = " | rematch demanded" if getattr(fighter, "rivalry_rematch_due", False) else ""
            rival_text = f"Rival: {fighter.rival} ({feud}; heat {rivalry_heat}/100{rematch})"
        else:
            rival_text = "Rival: None"
        origin = f" | Origin: {fighter.rivalry_origin}" if getattr(fighter, "rivalry_origin", "") else ""
        return f"{rival_text}{origin}\nAlly: {fighter.friend or 'None'} | Media Heat: {heat} ({band})"

    def all_database_fighters_with_companies(self):
        rows = [(self.player_company_name, fighter) for fighter in self.roster]
        rows.extend(("Free Agent", fighter) for fighter in self.free_agents)
        for promo in self.promotions:
            rows.extend((promo.name, fighter) for fighter in promo.roster)
        known_fighters = {self.fighter_identity_key(fighter) for _company, fighter in rows}
        for sport, world in getattr(self, "combat_sport_worlds", {}).items():
            for fighter in world.get("roster", []):
                fighter_key = self.fighter_identity_key(fighter)
                if fighter_key in known_fighters:
                    continue
                employer = fighter.sport_employer or world.get("promotion", sport)
                rows.append((employer, fighter))
                known_fighters.add(fighter_key)
        rows.extend(("Retired", fighter) for fighter in self.retired_fighters)
        return rows

    def fighter_instances_with_companies(self, include_retired=True):
        """Return every stored fighter instance, including intentional same-name athletes.

        Most roster lists keep names unique for compact display. Archived cards cannot
        make that assumption: a generated athlete can share a real athlete's name in
        another combat sport. Result/profile resolution uses this identity-preserving
        view together with sport and division metadata.
        """
        rows = [(self.player_company_name, fighter) for fighter in self.roster]
        rows.extend(("Free Agent", fighter) for fighter in self.free_agents)
        for promo in self.promotions:
            rows.extend((promo.name, fighter) for fighter in promo.roster)
        for sport, world in getattr(self, "combat_sport_worlds", {}).items():
            for fighter in world.get("roster", []):
                rows.append((fighter.sport_employer or world.get("promotion", sport), fighter))
        if include_retired:
            rows.extend(("Retired", fighter) for fighter in self.retired_fighters)
        return rows

    def rank_label_for_fighter(self, fighter, company, world=False):
        if getattr(fighter, "sport_employer", "") and getattr(fighter, "primary_discipline", "MMA") != "MMA":
            for sport, sport_world in getattr(self, "combat_sport_worlds", {}).items():
                if fighter not in sport_world.get("roster", []):
                    continue
                player_owned = fighter.sport_employer == self.player_company_name
                employer = fighter.sport_employer or sport_world.get("promotion", "")
                state = self.ensure_combat_sport_circuit_state(sport, sport_world, employer, player_owned)
                key = self.combat_sport_division_key(fighter, sport)
                if state.get("titles", {}).get(key) == fighter.name:
                    return "C"
                names = state.get("rankings_by_division", {}).get(key, [])
                return f"#{names.index(fighter.name) + 1}" if fighter.name in names else "-"
        rows = [(co, f) for co, f in self.unfiltered_ranked_fighter_rows() if f.gender == fighter.gender and f.weight == fighter.weight]
        if world:
            ordered = sorted(rows, key=lambda row: self.rank_value(row[1]), reverse=True)
        else:
            rows = [(co, f) for co, f in rows if co == company]
            if fighter.champion:
                return "C"
            rows = [(co, candidate) for co, candidate in rows if not candidate.champion]
            ordered = sorted(rows, key=lambda row: self.rank_value(row[1]), reverse=True)
        for index, (_company, candidate) in enumerate(ordered, 1):
            if candidate is fighter or self.fighter_identity_key(candidate) == self.fighter_identity_key(fighter):
                return f"#{index}" if world or not candidate.interim_champion else "IC"
        return "-"

    def fighter_stats_text(self, fighter):
        bouts = fighter.record_w + fighter.record_l + fighter.record_d
        stat_rounds = max(1, getattr(fighter, "career_stat_rounds", 0))
        control = getattr(fighter, "career_control_secs", 0)
        cm, cs = divmod(control, 60)
        lines = [
            "Core",
            f"  Overall {fighter.overall} | Standing {fighter.striking} | Wrestling {fighter.wrestling} | Ground {fighter.grappling} | Cardio {fighter.cardio} | Chin {fighter.chin}",
            f"  Power {fighter.power} | TD Defence {fighter.takedown_defence} | Ground Control {fighter.ground_control} | Submissions {fighter.submissions} | Sub Defence {fighter.submission_defence}",
            f"  Recovery {fighter.recovery} | Toughness {fighter.toughness} | Fight IQ {fighter.fight_iq} | Finishing {fighter.finishing_instinct}",
            "",
            "Career Statistics",
            f"  Recorded rounds: {getattr(fighter, 'career_stat_rounds', 0)} | Tracked fights: {getattr(fighter, 'career_stat_fights', 0)}",
            f"  Sig. strikes: {getattr(fighter, 'career_sig_strikes', 0)} | {round(getattr(fighter, 'career_sig_strikes', 0) / stat_rounds, 1)} per round",
            f"  Takedowns: {getattr(fighter, 'career_takedowns', 0)} | {round(getattr(fighter, 'career_takedowns', 0) / stat_rounds, 2)} per round",
            f"  Submissions: {getattr(fighter, 'career_submissions', 0)} successful | {getattr(fighter, 'career_sub_attempts', 0)} attempts | {round(getattr(fighter, 'career_sub_attempts', 0) / stat_rounds, 2)} attempts/round",
            f"  Knockdowns: {getattr(fighter, 'career_knockdowns', 0)} | {round(getattr(fighter, 'career_knockdowns', 0) / stat_rounds, 2)} per round | Control: {cm}:{cs:02d}",
            "",
        ]
        self.ensure_detailed_skills(fighter)
        for group, keys in DETAILED_SKILL_GROUPS.items():
            lines.append(group)
            for key in keys:
                lines.append(f"  {key.replace('_', ' ').title()}: {fighter.detailed_skills.get(key, 50)}")
            lines.append("")
        return "\n".join(lines)

    def fighter_history_text(self, fighter):
        history = fighter.fight_history or []
        if not history:
            return f"Career record (W-L-D): {fighter.record}\n\nNo prior fight history recorded yet."
        return f"Career record (W-L-D): {fighter.record}\n\n" + "\n".join(f"- {self.format_game_date_text(entry)}" for entry in history[:80])

    def fighter_history_opponent_name(self, fighter, entry):
        """Extract an opponent before resolving same-date bouts from a card archive."""
        text = str(entry or "")
        result = text.split(": ", 1)[1] if ": " in text else text
        name = re.escape(fighter.name)
        patterns = (
            rf"^{name}\s+def\.\s+(.+?)\s+by\s+",
            rf"^(.+?)\s+def\.\s+{name}\s+by\s+",
            rf"^{name}\s+and\s+(.+?)\s+fought to a draw",
            rf"^(.+?)\s+and\s+{name}\s+fought to a draw",
            rf"^{name}\s+W over\s+(.+?)(?:\s+by\s+|$)",
            rf"^{name}\s+L to\s+(.+?)(?:\s+by\s+|$)",
        )
        for pattern in patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def fight_stakes_label(self, fight):
        """Keep divisional, interim, and special championships distinct in every history view."""
        fight = fight or {}
        stakes = []
        if fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")):
            stakes.append("INTERIM TITLE" if fight.get("interim") else "DIVISIONAL TITLE")
        if fight.get("special_belt"):
            stakes.append(f"{fight['special_belt']} TITLE")
        return " + ".join(stakes) or "-"

    def fighter_history_card_context(self, fighter, entry, opponent=None):
        """Resolve a legacy history line to its archived event and bout metadata."""
        text = str(entry)
        date_match = re.search(r"Month\s+\d+\s+Week\s+\d+", text, re.IGNORECASE)
        entry_date = date_match.group(0) if date_match else ""
        entry_event = text.split(" at ", 1)[1].strip() if " at " in text else ""
        if " def. " not in text and "fought to a draw" not in text and "Amateur " not in text:
            return {
                "date": entry_date or "-", "event": entry_event or "Archive unavailable", "weight": fighter.weight,
                "opponent_name": "-", "opponent_id": "", "opponent_record": "-",
                "scorecard": "-", "sport": "", "title": False, "divisional_title": False, "interim": False, "special_belt": "", "source": "Legacy history entry", "fighter_rating": {}, "opponent_rating": {}, "record": None,
            }
        records, seen = [], set()
        for record in list(getattr(self, "result_records", []) or []) + list(getattr(self, "ai_event_archive", []) or []):
            event_name = str(record.get("event") or record.get("event_name") or "")
            key = (str(record.get("date", "")), event_name, str(record.get("company", "")))
            if key not in seen:
                seen.add(key)
                records.append(record)
        candidates = []
        fighter_id = str(getattr(fighter, "fighter_id", "") or "")
        fighter_sport = str(getattr(fighter, "primary_discipline", "MMA") or "MMA")
        fighter_division = str(getattr(fighter, "sport_weight_class", "") or getattr(fighter, "weight", ""))
        opponent_name = opponent if isinstance(opponent, str) else getattr(opponent, "name", "")
        opponent_id = "" if isinstance(opponent, str) else str(getattr(opponent, "fighter_id", "") or "")
        for record in records:
            event_name = str(record.get("event") or record.get("event_name") or "")
            record_date = str(record.get("date", ""))
            for fight_log in record.get("fight_logs", []) or []:
                a_name, b_name = str(fight_log.get("a", "")), str(fight_log.get("b", ""))
                a_id, b_id = str(fight_log.get("a_id", "") or ""), str(fight_log.get("b_id", "") or "")
                identified_bout = bool(a_id or b_id)
                if identified_bout:
                    if not fighter_id or fighter_id not in (a_id, b_id):
                        continue
                    if opponent_id and opponent_id not in (a_id, b_id):
                        continue
                    if opponent_name and opponent_name not in (a_name, b_name):
                        continue
                elif fighter.name not in (a_name, b_name) or (opponent_name and opponent_name not in (a_name, b_name)):
                    continue
                log_sport = str(fight_log.get("sport", ""))
                log_division = str(fight_log.get("weight", ""))
                # Sports cards retain their sport and competition class. These checks
                # stop a same-name boxer, kickboxer or generated athlete stealing a
                # profile's history entry from an unrelated division.
                if log_sport and fighter_sport not in ("", "MMA") and log_sport != fighter_sport:
                    continue
                if log_sport and fighter_division and log_division and fighter_division != log_division:
                    continue
                log_result = str(fight_log.get("result", ""))
                exact_result = bool(text.strip()) and text.strip().lower() == log_result.strip().lower()
                matching_date = bool(entry_date and entry_date == record_date)
                matching_event = bool(entry_event and entry_event.lower() == event_name.lower())
                # A card archive is deliberately bounded. Never attach an old plain
                # history line to an unrelated surviving replay just because the
                # fighter name happens to match.
                if (entry_date or entry_event or " by " in text) and not (exact_result or matching_date or matching_event):
                    continue
                score = 1
                if matching_date:
                    score += 100
                if matching_event:
                    score += 60
                if exact_result:
                    score += 300
                elif " by " in text and " by " in log_result:
                    score += 4
                candidates.append((score, record, fight_log))
        if not candidates:
            historical = next((
                item for item in (getattr(fighter, "bout_rating_history", None) or [])
                if isinstance(item, dict) and (not entry_date or item.get("date") == entry_date)
                and (not opponent or item.get("opponent_id") == str(getattr(opponent, "fighter_id", "") or "") or item.get("opponent_name") == getattr(opponent, "name", opponent))
            ), {})
            return {
                "date": entry_date or "-", "event": entry_event or "Archive unavailable", "weight": historical.get("weight") or fighter.weight,
                "opponent_name": historical.get("opponent_name") or (opponent_name or "-"),
                "opponent_id": historical.get("opponent_id", "") or opponent_id,
                "opponent_record": historical.get("opponent_record") or (getattr(opponent, "record", "") or "-"),
                "scorecard": historical.get("scorecard", "-"), "sport": "", "title": bool(historical.get("title", False)), "divisional_title": bool(historical.get("divisional_title", historical.get("title") and not historical.get("special_belt"))), "interim": bool(historical.get("interim", False)), "special_belt": str(historical.get("special_belt", "") or ""),
                "source": "Recorded result; card replay has expired" if historical else "Legacy history entry; card replay unavailable",
                "fighter_rating": {"overall": historical.get("self_overall"), "elo": historical.get("self_elo")},
                "opponent_rating": {"overall": historical.get("opponent_overall"), "elo": historical.get("opponent_elo")},
                "record": None,
            }
        _score, record, fight_log = max(candidates, key=lambda item: item[0])
        lines = list(fight_log.get("lines", []) or [])
        scorecards = []
        collecting = False
        for raw in lines:
            line = str(raw).strip()
            if line == "Official scorecards:":
                collecting = True
                continue
            if collecting and line.startswith("Judges' vote:"):
                break
            if collecting and line:
                card = re.search(r":.*?(\d{2}).*?,.*?(\d{2})", line)
                if card:
                    scorecards.append(f"{card.group(1)}-{card.group(2)}")
        fighter_is_a = fight_log.get("a_id") == fighter_id if fighter_id and fight_log.get("a_id") else fight_log.get("a") == fighter.name
        opponent_name = fight_log.get("b", "-") if fighter_is_a else fight_log.get("a", "-")
        opponent_id = fight_log.get("b_id", "") if fighter_is_a else fight_log.get("a_id", "")
        opponent_record = fight_log.get("b_record", "-") if fighter_is_a else fight_log.get("a_record", "-")
        fighter_rating = fight_log.get("a_rating", {}) if fighter_is_a else fight_log.get("b_rating", {})
        opponent_rating = fight_log.get("b_rating", {}) if fighter_is_a else fight_log.get("a_rating", {})
        # Compact regional cards from older builds retained results but not the
        # rating columns. Use the permanent pre-bout snapshot rather than
        # showing a misleading blank profile row.
        selected_date = str(record.get("date") or entry_date or "")
        historical = next((
            item for item in (getattr(fighter, "bout_rating_history", None) or [])
            if isinstance(item, dict) and (not selected_date or item.get("date") == selected_date)
            and (not opponent_id or item.get("opponent_id") == str(opponent_id))
        ), {})
        if not opponent_record or opponent_record == "-":
            opponent_record = historical.get("opponent_record", opponent_record)
        if not fighter_rating:
            fighter_rating = {"overall": historical.get("self_overall"), "elo": historical.get("self_elo")}
        if not opponent_rating:
            opponent_rating = {"overall": historical.get("opponent_overall"), "elo": historical.get("opponent_elo")}
        if not scorecards and historical.get("scorecard"):
            scorecards = [historical["scorecard"]]
        event_name = str(record.get("event") or record.get("event_name") or "-")
        card_record = dict(record)
        card_record.setdefault("event", event_name)
        return {
            "date": str(record.get("date") or entry_date or "-"), "event": event_name,
            "weight": fight_log.get("weight", fighter.weight), "opponent_name": opponent_name or "-",
            "opponent_id": opponent_id or "", "opponent_record": opponent_record or "-", "scorecard": " / ".join(scorecards) if scorecards else "-",
            "sport": str(fight_log.get("sport", "")), "title": bool(fight_log.get("title", False)), "divisional_title": bool(fight_log.get("divisional_title", fight_log.get("title") and not fight_log.get("special_belt"))), "interim": bool(fight_log.get("interim", False)), "special_belt": str(fight_log.get("special_belt", "") or ""), "source": "Archived event replay", "fighter_rating": fighter_rating or {}, "opponent_rating": opponent_rating or {}, "record": card_record,
        }

    def profile_info_row(self, parent, label, value, row):
        tk.Label(parent, text=label.upper(), bg=self.colors["panel"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        tk.Label(parent, text=str(value), bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w").grid(row=row, column=1, sticky="ew", padx=8, pady=3)
        parent.grid_columnconfigure(1, weight=1)

    def country_flag_path_for_fighter(self, fighter):
        """Find the bundled national flag, preferring a fighter's recorded birthplace."""
        flag_dir = BUNDLE_DIR / "country_flags"
        aliases = {
            "usa": "united_states", "us": "united_states", "u.s.a.": "united_states",
            "united states of america": "united_states", "american": "united_states",
            "uk": "united_kingdom", "u.k.": "united_kingdom", "british": "united_kingdom",
            "england": "united_kingdom", "scotland": "united_kingdom", "wales": "united_kingdom",
            "northern ireland": "united_kingdom", "northern irish": "united_kingdom",
            "czech republic": "czechia", "czech": "czechia",
            "south korean": "south_korea", "korean": "south_korea",
            "people's republic of china": "china", "the bahamas": "bahamas",
            "republic of ireland": "ireland", "turkey": "turkiye", "turkish": "turkiye",
            "new zealander": "new_zealand", "emirati": "united_arab_emirates",
        }
        candidates = [
            getattr(fighter, "birth_country", ""),
            getattr(fighter, "nationality", ""),
            getattr(fighter, "region", ""),
        ]
        nationality = str(getattr(fighter, "nationality", "") or "").strip()
        candidates.extend(country for country, value in COUNTRY_NATIONALITIES.items() if value == nationality)
        region = str(getattr(fighter, "region", "") or "").strip()
        if region in REGION_COUNTRIES:
            candidates.append(REGION_COUNTRIES[region])

        for candidate in candidates:
            candidate = str(candidate or "").strip()
            if not candidate:
                continue
            key = candidate.lower()
            slug = aliases.get(key, re.sub(r"[^a-z0-9]+", "_", key).strip("_"))
            path = flag_dir / f"{slug}.png"
            if path.exists():
                return path
        return None

    def profile_country_flag_badge(self, parent, fighter):
        path = self.country_flag_path_for_fighter(fighter)
        if not path:
            return None
        try:
            flag = tk.PhotoImage(file=str(path))
        except tk.TclError:
            return None
        scale = max(1, (flag.width() + 43 - 1) // 43, (flag.height() + 29 - 1) // 29)
        if scale > 1:
            flag = flag.subsample(scale, scale)
        frame = tk.Frame(parent, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        frame.pack(side="left", padx=4, pady=4)
        tk.Label(frame, text="FLAG", bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).pack(padx=8, pady=(5, 1))
        label = tk.Label(frame, image=flag, bg=self.colors["panel_dark"], bd=0)
        label.image = flag  # Keep the Tk image alive for the lifetime of the profile.
        label.pack(padx=8, pady=(0, 5))
        return frame

    def profile_badge(self, parent, text, value=None):
        frame = tk.Frame(parent, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        frame.pack(side="left", padx=4, pady=4)
        tk.Label(frame, text=text.upper(), bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).pack(padx=8, pady=(5, 0))
        if value is not None:
            tk.Label(frame, text=str(value), bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Impact", 15)).pack(padx=8, pady=(0, 5))
        return frame

    def profile_meter(self, parent, label, value, row):
        value = max(0, min(100, int(value)))
        tk.Label(parent, text=label, bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 8, "bold")).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        canvas = tk.Canvas(parent, width=182, height=16, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        canvas.grid(row=row, column=1, sticky="ew", padx=8, pady=3)
        color = self.colors["gold"] if value >= 80 else self.colors["red"] if value >= 60 else self.colors["muted"]
        # Reserve a dark value gutter so a full bar can never hide white text.
        track_width, total_width = 142, 182
        canvas.create_rectangle(0, 0, track_width, 16, fill="#171b22", outline="")
        canvas.create_rectangle(0, 0, max(3, int(track_width * value / 100)), 16, fill=color, outline="")
        canvas.create_rectangle(track_width, 0, total_width, 16, fill="#0d1015", outline="")
        canvas.create_text(total_width - 5, 8, anchor="e", text=str(value), fill="#ffffff", font=("Tahoma", 8, "bold"))
        parent.grid_columnconfigure(1, weight=1)

    def profile_section_label(self, parent, text):
        tk.Label(parent, text=text.upper(), bg=self.colors["red"], fg="#ffffff", font=("Impact", 11), anchor="w").pack(fill="x", pady=(8, 4))

    def fill_profile_skill_tree(self, tree, fighter, groups):
        tree.delete(*tree.get_children())
        self.ensure_detailed_skills(fighter)
        for group in groups:
            group_id = tree.insert("", "end", values=(group, "", ""), open=True)
            for key in DETAILED_SKILL_GROUPS[group]:
                value = fighter.detailed_skills.get(key, 50)
                grade = "Elite" if value >= 88 else "Excellent" if value >= 78 else "Good" if value >= 65 else "Raw" if value >= 50 else "Weak"
                tree.insert(group_id, "end", values=(key.replace("_", " ").title(), value, grade))

    def fighter_profile_stats_visible(self, fighter, company=""):
        """Public profiles stay accessible; scouting controls only the private ratings within them."""
        if not self.rules.get("scouting_mode", False) or self.player_owns_fighter(fighter) or getattr(fighter, "retired", False):
            return True
        if company and company == self.player_company_name:
            return True
        report = self.scouting_report_for(fighter)
        return self.scouting_report_is_current_full(report)

    def fighter_current_championships(self, fighter):
        titles = []
        name = getattr(fighter, "name", "")

        def add(company, division, kind="Champion"):
            label = f"{company} {division} {kind}".strip()
            if label and label not in titles:
                titles.append(label)

        for key, holder in self.normalize_belts(getattr(self, "belts", {})).items():
            if holder == name:
                add(self.player_company_name, key)
        for key, holder in self.normalize_belts(getattr(self, "interim_belts", {})).items():
            if holder == name:
                add(self.player_company_name, key, "Interim Champion")
        for title, belt in self.normalize_special_belts(getattr(self, "special_belts", {})).items():
            if belt.get("holder") == name or title in (getattr(fighter, "special_titles", None) or []):
                add(self.player_company_name, title)
        for promo in getattr(self, "promotions", []):
            for key, holder in self.normalize_belts(getattr(promo, "belts", {})).items():
                if holder == name:
                    add(promo.name, key)
            for key, holder in self.normalize_belts(getattr(promo, "interim_belts", {})).items():
                if holder == name:
                    add(promo.name, key, "Interim Champion")
        for sport, world in getattr(self, "combat_sport_worlds", {}).items():
            state = self.ensure_combat_sport_circuit_state(sport, world, getattr(fighter, "sport_employer", "") or world.get("promotion", sport), getattr(fighter, "sport_employer", "") == self.player_company_name)
            for key, holder in state.get("titles", {}).items():
                if holder == name:
                    add(state.get("promotion", world.get("promotion", sport)), self.combat_sport_division_label(key))
        if getattr(fighter, "champion", False) and not titles:
            add("", self.fighter_display_division(fighter))
        if getattr(fighter, "interim_champion", False) and not any("Interim" in item for item in titles):
            add("", self.fighter_display_division(fighter), "Interim Champion")
        return titles

    def championship_profile_badge(self, parent, titles):
        panel = tk.Frame(parent, bg="#4b3512", highlightthickness=1, highlightbackground="#d9ad45")
        panel.pack(fill="x", padx=8, pady=(0, 8))
        canvas = tk.Canvas(panel, width=44, height=34, bg="#4b3512", highlightthickness=0)
        canvas.pack(side="left", padx=(7, 4), pady=6)
        canvas.create_polygon(4, 14, 15, 7, 29, 7, 40, 14, 34, 27, 10, 27, fill="#d9ad45", outline="#fff0a5")
        canvas.create_oval(16, 10, 28, 24, fill="#2a2211", outline="#fff0a5")
        canvas.create_text(22, 17, text="C", fill="#fff0a5", font=("Impact", 10))
        copy = tk.Frame(panel, bg="#4b3512")
        copy.pack(side="left", fill="x", expand=True, pady=4)
        tk.Label(copy, text="CURRENT CHAMPION", bg="#4b3512", fg="#ffe08a", font=("Impact", 10), anchor="w").pack(fill="x")
        tk.Label(copy, text=" | ".join(titles[:3]), bg="#4b3512", fg="#ffffff", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=118).pack(fill="x", pady=(1, 2))

    def fighter_trade_asset_value(self, fighter):
        age_drag = max(0, fighter.age - min(fighter.prime_end, 33)) * 3.0
        prospect_bonus = max(0, min(24, fighter.potential - fighter.overall)) * max(0.35, (31 - min(fighter.age, 31)) / 12)
        ceiling = fighter.overall * 1.9 + fighter.potential * 1.25 + prospect_bonus * 4.5 - age_drag
        market = fighter.popularity * 1.15 + max(-6, fighter.momentum) * 3 + fighter.star_quality * 0.45
        contract = max(0, fighter.contract_months) * 1.8
        champion = 55 if fighter.champion else 28 if getattr(fighter, "interim_champion", False) else 0
        return max(8, ceiling + market + contract + champion)

    def transfer_cash_valuation(self, target, outgoing, source_promotion):
        target_value = self.fighter_trade_asset_value(target)
        outgoing_value = self.fighter_trade_asset_value(outgoing)
        skill_gap = target.overall - outgoing.overall
        ceiling_gap = max(0, target.potential - outgoing.potential)
        age_gap = max(0, outgoing.age - target.age)
        star_gap = max(0, target.popularity + target.star_quality - outgoing.popularity - outgoing.star_quality)
        resistance = source_promotion.reputation_score * 1700 + max(0, target.contract_months) * 1300
        if target.champion:
            resistance += 180000
        if len([f for f in source_promotion.roster if f.gender == target.gender and f.weight == target.weight]) <= 6:
            resistance += 95000
        base = (target_value - outgoing_value) * 2150 + max(0, skill_gap) * 15500 + ceiling_gap * 6800 + age_gap * 7200 + star_gap * 1150
        if skill_gap < -4:
            base -= abs(skill_gap) * 9000
        return max(0, round((base + resistance) * 1.2 / 5000) * 5000)

    def transfer_fighter_is_booked(self, fighter, promotion=None):
        names = {fighter.name}
        if fighter.name in self.scheduled_fighter_names(include_booked=True):
            return True
        events = getattr(promotion, "scheduled_events", []) if promotion is not None else []
        for event in events or []:
            for fight in event.get("fights", []):
                if names & set(self.event_fight_participants(fight)):
                    return True
        return False

    def transfer_reasoning(self, target, outgoing, source_promotion, cash_offer, ask):
        reasons = []
        skill_gap = target.overall - outgoing.overall
        potential_gap = target.potential - outgoing.potential
        if skill_gap >= 8:
            reasons.append("major ability gap")
        elif skill_gap >= 3:
            reasons.append("clear ability upgrade")
        elif skill_gap <= -5:
            reasons.append("incoming athlete is a useful sporting replacement")
        if potential_gap >= 8 and target.age <= 30:
            reasons.append("younger ceiling")
        if outgoing.age > target.age + 4:
            reasons.append("your makeweight has less long-term runway")
        if target.champion:
            reasons.append("champion premium")
        if len([f for f in source_promotion.roster if f.gender == target.gender and f.weight == target.weight]) <= 6:
            reasons.append("thin source division")
        if cash_offer < ask:
            reasons.append(f"cash is ${ask - cash_offer:,} light")
        return ", ".join(reasons[:4]) or "balanced sporting value"

    def open_transfer_negotiation(self, target, source_promotion=None, parent=None):
        source_promotion = source_promotion or self.promotion_owning_fighter(target)
        if not source_promotion or getattr(source_promotion, "is_regional_feeder", False):
            messagebox.showinfo("Transfer offer", "Transfers are only available for fighters contracted to rival MMA promotions.", parent=parent)
            return
        if getattr(self, "spectator_mode", False):
            messagebox.showinfo("Transfer offer", "Transfers require control of a promotion.", parent=parent)
            return
        if self.belt_key(target.gender, target.weight) in set(getattr(self, "closed_divisions", set())):
            messagebox.showinfo("Transfer offer", f"Your {target.gender} {target.weight} division is closed. Reopen it before buying a contracted fighter for that class.", parent=parent)
            return
        if target.champion or getattr(target, "interim_champion", False) or self.fighter_current_championships(target):
            messagebox.showinfo("Transfer offer", f"{target.name} currently holds a championship. Champions are not available for transfer deals.", parent=parent)
            return
        if self.transfer_fighter_is_booked(target, source_promotion):
            messagebox.showinfo("Transfer offer", f"{target.name} is booked on an upcoming card. Try again after that fight.", parent=parent)
            return
        player_candidates = [
            fighter for fighter in self.roster
            if fighter is not target and not getattr(fighter, "retired", False)
            and fighter.gender == target.gender and fighter.weight == target.weight
            and not fighter.champion and not getattr(fighter, "interim_champion", False) and not self.fighter_current_championships(fighter)
            and not self.fighter_in_closed_player_division(fighter)
            and not self.transfer_fighter_is_booked(fighter)
        ]
        if not player_candidates:
            messagebox.showinfo("Transfer offer", f"You need an unbooked, non-champion {target.gender} {target.weight} fighter to include in this swap deal.", parent=parent)
            return

        player_candidates.sort(key=lambda fighter: (abs(fighter.overall - target.overall), -fighter.age, fighter.name))
        label_to_fighter = {
            f"{fighter.name} | {fighter.gender[0]} {fighter.weight} | OVR {fighter.overall} POT {fighter.potential} | Age {fighter.age}": fighter
            for fighter in player_candidates
        }
        initial_outgoing = player_candidates[0]
        initial_ask = self.transfer_cash_valuation(target, initial_outgoing, source_promotion)

        window = tk.Toplevel(self.root)
        window.title(f"Transfer Offer - {target.name}")
        window.geometry("780x610")
        window.minsize(700, 560)
        window.configure(bg=self.colors["chrome"])
        if parent is not None:
            window.transient(parent)

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"TRANSFER: {target.name.upper()}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text=f"{source_promotion.name}", style="Chrome.TLabel").pack(side="right", padx=10)

        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        summary = tk.Frame(body, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        summary.pack(fill="x", padx=8, pady=(8, 8))
        summary_vars = {}
        for title, fighter, column in (("TARGET", target, 0), ("FIGHTER OFFERED", initial_outgoing, 1)):
            card = tk.Frame(summary, bg=self.colors["panel_dark"])
            card.grid(row=0, column=column, sticky="nsew", padx=10, pady=8)
            name_var = tk.StringVar(value=fighter.name)
            detail_var = tk.StringVar(value=f"{fighter.gender} {fighter.weight} | Age {fighter.age} | OVR {fighter.overall} / POT {fighter.potential}\nRecord {fighter.record} | Pop {fighter.popularity} | ${fighter.purse:,}/fight")
            summary_vars[title] = (name_var, detail_var)
            tk.Label(card, text=title, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 8, "bold"), anchor="w").pack(fill="x")
            tk.Label(card, textvariable=name_var, bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Impact", 16), anchor="w").pack(fill="x")
            tk.Label(card, textvariable=detail_var, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), justify="left", anchor="w").pack(fill="x")
        summary.grid_columnconfigure(0, weight=1)
        summary.grid_columnconfigure(1, weight=1)

        controls = tk.Frame(body, bg=self.colors["panel"])
        controls.pack(fill="x", padx=8, pady=(0, 8))
        selected_label = tk.StringVar(value=next(label for label, fighter in label_to_fighter.items() if fighter is initial_outgoing))
        cash_var = tk.IntVar(value=max(0, round(initial_ask * 0.72 / 5000) * 5000))
        ttk.Label(controls, text="Fighter offered", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=8, pady=(9, 4))
        fighter_combo = ttk.Combobox(controls, textvariable=selected_label, values=list(label_to_fighter.keys()), state="readonly", width=78)
        fighter_combo.grid(row=0, column=1, sticky="ew", padx=8, pady=(9, 4))
        ttk.Label(controls, text="Cash", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        cash_spin = ttk.Spinbox(controls, from_=0, to=max(2000000, self.cash), increment=5000, textvariable=cash_var, width=14)
        cash_spin.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        controls.grid_columnconfigure(1, weight=1)

        readout = tk.Frame(body, bg=self.colors["chrome"], highlightthickness=1, highlightbackground=self.colors["line"])
        readout.pack(fill="x", padx=8, pady=(0, 8))
        stance_var = tk.StringVar()
        details_var = tk.StringVar()
        tk.Label(readout, textvariable=stance_var, bg=self.colors["chrome"], fg=self.colors["gold"], font=("Impact", 12), anchor="w").pack(fill="x", padx=8, pady=(7, 1))
        tk.Label(readout, textvariable=details_var, bg=self.colors["chrome"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), justify="left", anchor="w", wraplength=730).pack(fill="x", padx=8, pady=(0, 7))
        accept_bar = ttk.Progressbar(body, maximum=100)
        accept_bar.pack(fill="x", padx=12, pady=(0, 4))
        result_label = ttk.Label(body, text="Shape the bid, then submit. A transfer agreement still requires the fighter to accept your contract.", style="Panel.TLabel")
        result_label.pack(anchor="w", padx=12, pady=(0, 8))

        state = {"attempts": 4, "softened": 0}

        def selected_outgoing():
            return label_to_fighter[selected_label.get()]

        def assessment():
            outgoing = selected_outgoing()
            ask = max(0, self.transfer_cash_valuation(target, outgoing, source_promotion) - state["softened"])
            offered = cash_var.get()
            strategic_fit = 9000
            relationship = self.staff_effect("Talent Relations", 4200)
            score = offered - ask + strategic_fit + relationship
            chance = max(3, min(94, round(48 + score / 10500)))
            return outgoing, ask, offered, chance

        def refresh_details(*_):
            try:
                outgoing, ask, offered, chance = assessment()
            except (ValueError, tk.TclError, KeyError):
                return
            accept_bar["value"] = chance
            offered_name_var, offered_detail_var = summary_vars["FIGHTER OFFERED"]
            offered_name_var.set(outgoing.name)
            offered_detail_var.set(f"{outgoing.gender} {outgoing.weight} | Age {outgoing.age} | OVR {outgoing.overall} / POT {outgoing.potential}\nRecord {outgoing.record} | Pop {outgoing.popularity} | ${outgoing.purse:,}/fight")
            if offered >= ask:
                stance = "Their board can sell this internally"
            elif offered >= ask * 0.75:
                stance = "There is a deal here, but they want the gap closed"
            else:
                stance = "They see this as a talent raid"
            stance_var.set(f"{stance} | Estimated acceptance {chance}%")
            reason = self.transfer_reasoning(target, outgoing, source_promotion, offered, ask)
            details_var.set(
                f"Expected make-good: ${ask:,}. Offered cash: ${offered:,}. Cash after transfer fee only: ${self.cash - offered:,}.\n"
                f"Read: {reason}. Older athletes carry less ceiling; bigger skill and potential gaps push the cash demand up."
            )

        def submit_offer():
            outgoing, ask, offered, chance = assessment()
            if offered > self.cash:
                result_label.config(text=f"You only have ${self.cash:,} available.")
                return
            if outgoing not in self.roster or target not in source_promotion.roster:
                result_label.config(text="One side of the deal is no longer available.")
                submit_button.config(state="disabled")
                return
            if self.transfer_fighter_is_booked(outgoing) or self.transfer_fighter_is_booked(target, source_promotion):
                result_label.config(text="A fighter in this deal has been booked. Remove the booking or try later.")
                submit_button.config(state="disabled")
                return
            roll = random.randint(1, 100)
            if roll <= chance:
                deal = {"source": source_promotion, "target": target, "outgoing": outgoing, "cash": offered}
                result_label.config(text=f"{source_promotion.name} accepts the transfer terms. Now convince {target.name}'s camp.")
                submit_button.config(state="disabled")
                self.open_contract_negotiation(target, existing=False, transfer_deal=deal)
                return
            state["attempts"] -= 1
            state["softened"] += max(5000, round(min(ask * 0.08, 45000) / 5000) * 5000)
            if state["attempts"] <= 0:
                result_label.config(text=f"{source_promotion.name} ends talks. They will not move {target.name} for this package.")
                submit_button.config(state="disabled")
                return
            counter = max(offered + 10000, round((ask - state["softened"] * 0.35) / 5000) * 5000)
            result_label.config(text=f"No agreement. Counter signal: add cash near ${counter:,} or offer a closer sporting replacement. Attempts left: {state['attempts']}.")
            refresh_details()

        for variable in (selected_label, cash_var):
            variable.trace_add("write", refresh_details)
        fighter_combo.bind("<<ComboboxSelected>>", refresh_details)
        refresh_details()

        buttons = ttk.Frame(body, style="Panel.TFrame")
        buttons.pack(fill="x", padx=8, pady=(2, 8))
        ttk.Button(buttons, text="Target Profile", command=lambda: self.open_fighter_profile_window(target)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Offered Fighter Profile", command=lambda: self.open_fighter_profile_window(selected_outgoing())).pack(side="left", padx=4)
        submit_button = ttk.Button(buttons, text="Submit Transfer Offer", style="Accent.TButton", command=submit_offer)
        submit_button.pack(side="left", padx=10)
        ttk.Button(buttons, text="Walk Away", command=window.destroy).pack(side="right", padx=4)

    def commit_player_transfer_deal(self, deal, target):
        source = deal.get("source")
        outgoing = deal.get("outgoing")
        transfer_cash = int(deal.get("cash", 0) or 0)
        if not source or source not in getattr(self, "promotions", []):
            return False, "The source promotion is no longer active. Transfer cancelled."
        if target not in source.roster:
            return False, f"{target.name} is no longer contracted to {source.name}. Transfer cancelled."
        if outgoing not in self.roster:
            return False, f"{getattr(outgoing, 'name', 'Your offered fighter')} is no longer on your roster. Transfer cancelled."
        if target.champion or getattr(target, "interim_champion", False) or self.fighter_current_championships(target):
            return False, f"{target.name} now holds a championship. Transfer cancelled."
        if outgoing.champion or getattr(outgoing, "interim_champion", False) or self.fighter_current_championships(outgoing):
            return False, f"{outgoing.name} now holds a championship. Transfer cancelled."
        if self.transfer_fighter_is_booked(target, source) or self.transfer_fighter_is_booked(outgoing):
            return False, "A fighter in the agreed transfer is now booked. Transfer cancelled."
        if self.cash < transfer_cash:
            return False, f"Not enough cash for the ${transfer_cash:,} transfer fee."

        self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
            outgoing, self.roster, self.belts, self.interim_belts, self.belt_history,
            f"Transferred to {source.name} in a swap deal for {target.name}.",
        )
        source.belts, source.interim_belts, source.belt_history = self.vacate_fighter_belts(
            target, source.roster, source.belts or {}, source.interim_belts or {}, source.belt_history or {},
            f"Transferred to {self.player_company_name} in a swap deal for {outgoing.name}.",
        )
        self.roster.remove(outgoing)
        source.roster.remove(target)
        outgoing.champion = False
        outgoing.interim_champion = False
        target.champion = False
        target.interim_champion = False
        if outgoing not in source.roster:
            source.roster.append(outgoing)
        if target not in self.roster:
            self.roster.append(target)

        self.cash -= transfer_cash
        source.cash += transfer_cash
        self.record_finance_transaction(f"Transfer fee: {target.name} from {source.name}", costs=transfer_cash)
        outgoing.morale = max(35, min(100, outgoing.morale - 4 + random.randint(-2, 4)))
        target.morale = min(100, target.morale + 3)
        outgoing.contract_type = "Exclusive"
        outgoing.exclusive = True
        outgoing.fight_history = ([f"Month {self.month}: Transferred from {self.player_company_name} to {source.name} in swap for {target.name}."] + (outgoing.fight_history or []))[:60]
        target.fight_history = ([f"Month {self.month}: Transfer agreed from {source.name} to {self.player_company_name}; contract talks completed the deal."] + (target.fight_history or []))[:60]
        headline = f"{self.player_company_name} completed a transfer for {target.name}; {outgoing.name} and ${transfer_cash:,} went to {source.name}."
        self.news.insert(0, headline)
        self.record_world_story("Transfer", headline, "The transfer only completed after the incoming fighter agreed personal contract terms.", [self.player_company_name, source.name], [target.name, outgoing.name], importance=3)
        self.record_change("Roster", target.name, "Transfer In", f"Swap with {source.name}: {outgoing.name} plus ${transfer_cash:,}", 3)
        self.refresh_promotion_rankings(company=source.name, roster=source.roster)
        return True, "Transfer completed."

    def open_fighter_profile_window(self, fighter):
        report = self.scouting_report_for(fighter)
        self.ensure_detailed_skills(fighter)
        self.ensure_fighter_business_stats(fighter)
        # Old saves may still have academy bouts mixed into the professional
        # text ledger. Repair before calculating the visible record.
        self.migrate_academy_amateur_history(fighter)
        baseline_record = self.ensure_fighter_history_baseline(fighter)
        company = fighter.sport_employer if getattr(fighter, "sport_employer", "") else next((name for name, candidate in self.all_database_fighters_with_companies() if candidate.name == fighter.name), "Unknown")
        sport = self.combat_sport_for_fighter(fighter) if getattr(fighter, "sport_employer", "") else ""
        stats_visible = self.fighter_profile_stats_visible(fighter, company)
        private_development_visible = (not self.rules.get("scouting_mode", False) or self.player_owns_fighter(fighter) or getattr(fighter, "retired", False) or company == self.player_company_name)
        sport_rating = self.combat_sport_display_rating(fighter, sport) if sport else None
        company_rank = self.rank_label_for_fighter(fighter, company, world=False)
        world_rank = self.rank_label_for_fighter(fighter, company, world=True)
        company_rank_text = self.profile_rank_text(fighter, company_rank, "Company")
        world_rank_text = self.profile_rank_text(fighter, world_rank, "World")
        window = tk.Toplevel(self.root)
        window.title(f"Fighter Profile - {fighter.name}")
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        profile_width = min(1500, max(1220, screen_width - 120))
        profile_height = min(900, max(760, screen_height - 130))
        window.geometry(f"{profile_width}x{profile_height}+{max(0, (screen_width - profile_width) // 2)}+{max(0, (screen_height - profile_height) // 3)}")
        window.minsize(1100, 680)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=fighter.name.upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        origin = "GENERATED" if getattr(fighter, "generated", False) else "REAL"
        ttk.Label(header, text=origin, style="Header.TLabel").pack(side="left", padx=(0, 8), pady=5)
        ttk.Label(header, text=f"{fighter.gender} {self.fighter_display_division(fighter)} | {company} | {company_rank_text} | {world_rank_text}", style="ScreenTitle.TLabel").pack(side="right", padx=10, pady=5)
        body_shell, body = self.create_scrollable_frame(window, style="Chrome.TFrame")
        body_shell.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body, style="Panel.TFrame")
        left.pack(side="left", fill="y", padx=(0, 8), ipadx=2)
        portrait = tk.Canvas(left, width=180, height=180, highlightthickness=1, highlightbackground=self.colors["line"], bg="#222222")
        portrait.pack(anchor="n", padx=10, pady=10)
        self.draw_profile_portrait(portrait, fighter)

        badge_row = tk.Frame(left, bg=self.colors["panel"])
        badge_row.pack(fill="x", padx=8, pady=(0, 6))
        overall_badge = f"{sport_rating:.1f}" if sport else fighter.overall
        self.profile_badge(badge_row, "SPORT RTG" if sport else "OVR", overall_badge if stats_visible else "SCOUT")
        self.profile_badge(badge_row, "ELO", fighter.elo_rating if stats_visible else "SCOUT")
        self.profile_badge(badge_row, "P4P", world_rank)
        self.profile_country_flag_badge(badge_row, fighter)
        current_titles = self.fighter_current_championships(fighter)
        if current_titles:
            self.championship_profile_badge(left, current_titles)

        identity = tk.Frame(left, bg=self.colors["panel"])
        identity.pack(fill="x", padx=8, pady=(0, 8))
        rows = [
            ("Record", fighter.record),
            ("Age", f"{fighter.age} ({self.combat_sport_development_stage(fighter, sport) if sport else self.fighter_career_stage(fighter)})"),
            ("Height", fighter.height or "-"),
            ("Nationality", fighter.nationality),
            ("Born", f"{getattr(fighter, 'birth_country', '') or fighter.region} - {getattr(fighter, 'hometown', '') or '-'}"),
            ("Based / Trains", f"{getattr(fighter, 'fighting_base', '') or fighter.region} / {getattr(fighter, 'training_location', '') or fighter.region}"),
            ("Style", fighter.style),
            ("Stance", fighter.stance),
            ("Behaviour", fighter.behaviour),
            ("Trait", fighter.trait),
            ("Camp", fighter.camp),
            ("Competition Class", self.fighter_display_division(fighter)),
            ("Status", fighter.status),
            ("Major Injury", self.serious_injury_status(fighter)),
            ("Division Moves", len(getattr(fighter, "weight_class_history", []) or [])),
            ("Achievements", len(getattr(fighter, "career_achievements", []) or [])),
        ]
        for idx, (label, value) in enumerate(rows):
            self.profile_info_row(identity, label, value, idx)

        owned_closed_division = self.fighter_in_closed_player_division(fighter)
        if owned_closed_division:
            division_alert = tk.Frame(left, bg="#5a3516", highlightthickness=1, highlightbackground="#e2a442")
            division_alert.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(division_alert, text="!", bg="#d88a22", fg="#18120b", font=("Impact", 13), width=2).pack(side="left", padx=(6, 5), pady=6)
            alert_copy = tk.Frame(division_alert, bg="#5a3516")
            alert_copy.pack(side="left", fill="x", expand=True, pady=4)
            tk.Label(alert_copy, text="DIVISION CLOSED", bg="#5a3516", fg="#ffd27a", font=("Impact", 10), anchor="w").pack(fill="x")
            tk.Label(alert_copy, text="Still under contract. Move to an active division before booking.", bg="#5a3516", fg="#ffffff", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=115).pack(fill="x", pady=(1, 2))

        if fighter.injured or getattr(fighter, "serious_injury", ""):
            medical_alert = tk.Frame(left, bg="#5a2525", highlightthickness=1, highlightbackground="#d86b6b")
            medical_alert.pack(fill="x", padx=8, pady=(0, 8))
            injury_name = getattr(fighter, "serious_injury", "") or "Training / fight injury"
            decision = " — medical decision required" if getattr(fighter, "serious_injury_pending", False) else ""
            icon_path = ASSET_DIR / "medical_cross.png"
            try:
                cross_icon = tk.PhotoImage(file=str(icon_path)).subsample(16, 16)
                icon_label = tk.Label(medical_alert, image=cross_icon, bg="#5a2525")
                icon_label.image = cross_icon  # keep the Tk image alive with its profile panel
                icon_label.pack(side="left", padx=(7, 5), pady=6)
            except tk.TclError:
                pass  # A source-only or older portable build still keeps the text alert.
            medical_copy = tk.Frame(medical_alert, bg="#5a2525")
            medical_copy.pack(side="left", fill="x", expand=True, pady=4)
            tk.Label(medical_copy, text="MEDICAL STATUS", bg="#5a2525", fg="#ffd1d1", font=("Impact", 10), anchor="w").pack(fill="x")
            tk.Label(medical_copy, text=f"{injury_name}\nOut approximately {fighter.injured} month(s){decision}", bg="#5a2525", fg="#ffffff", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=105).pack(fill="x", pady=(1, 2))

        if getattr(fighter, "retirement_pending", False):
            retirement_alert = tk.Frame(left, bg="#4d3b18", highlightthickness=1, highlightbackground="#d9b34c")
            retirement_alert.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(retirement_alert, text="R", bg="#b88717", fg="#1b1710", font=("Impact", 13), width=2).pack(side="left", padx=(6, 5), pady=6)
            retirement_reason = getattr(fighter, "retirement_reason", "") or "Final bout requested"
            tk.Label(retirement_alert, text=f"RETIREMENT FIGHT PENDING\n{retirement_reason}", bg="#4d3b18", fg="#fff0bd", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=115).pack(side="left", fill="x", expand=True, pady=5)

        if getattr(fighter, "retired", False):
            retired_alert = tk.Frame(left, bg="#243f4d", highlightthickness=1, highlightbackground="#6fa4b8")
            retired_alert.pack(fill="x", padx=8, pady=(0, 8))
            tk.Label(retired_alert, text="RTD", bg="#315a70", fg="#ffffff", font=("Impact", 10), width=3).pack(side="left", padx=(6, 5), pady=6)
            tk.Label(retired_alert, text="CAREER RETIRED\nHistorical profile and record", bg="#243f4d", fg="#d8f2fa", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=115).pack(side="left", fill="x", expand=True, pady=5)

        relation = tk.Frame(left, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        relation.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(relation, text="RELATIONSHIPS", bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Impact", 10), anchor="w").pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(relation, text=f"Rival: {fighter.rival or 'None'}", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8, "bold"), anchor="w").pack(fill="x", padx=8, pady=1)
        tk.Label(relation, text=f"Friend: {fighter.friend or 'None'}", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8, "bold"), anchor="w").pack(fill="x", padx=8, pady=(1, 6))
        if fighter.rival:
            rematch = " REMATCH DEMANDED" if getattr(fighter, "rivalry_rematch_due", False) else ""
            tk.Label(relation, text=f"FEUD HEAT {getattr(fighter, 'rivalry_heat', 0)}/100{rematch}", bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 8, "bold"), anchor="w", wraplength=160).pack(fill="x", padx=8, pady=(0, 2))
            if getattr(fighter, "rivalry_origin", ""):
                tk.Label(relation, text=fighter.rivalry_origin, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 8), anchor="w", wraplength=160).pack(fill="x", padx=8, pady=(0, 6))

        if not stats_visible:
            scout_panel = tk.Frame(left, bg="#233b52", highlightthickness=1, highlightbackground="#4f83b5")
            scout_panel.pack(fill="x", padx=8, pady=(0, 8))
            reveal = self.scouting_effective_confidence(report) if report else 0
            status = report.get("status", "Unscouted")
            age_note = ""
            if report.get("status") == "Complete" and reveal < int(report.get("confidence", reveal) or reveal):
                age_note = " | Intel ageing"
            tk.Label(scout_panel, text="SCOUTING INTEL", bg="#233b52", fg="#b8dcff", font=("Impact", 10), anchor="w").pack(fill="x", padx=8, pady=(6, 2))
            ability = self.scouting_estimate(fighter, "overall", {}) if report.get("status") == "Complete" else {}
            ability_text = f"\nProjected OVR {ability.get('low')}-{ability.get('high')}" if ability else ""
            tk.Label(scout_panel, text=f"{status} | Confidence {reveal}%{age_note}{ability_text}\nA full evaluation reveals current ratings; potential remains projected.", bg="#233b52", fg="#ffffff", font=("Tahoma", 8, "bold"), justify="left", anchor="w", wraplength=155).pack(fill="x", padx=8, pady=(0, 6))

        center = ttk.Frame(body, style="Panel.TFrame")
        center.pack(side="left", fill="both", padx=(0, 8), ipadx=2)
        self.profile_section_label(center, "Core Ratings")
        core = tk.Frame(center, bg=self.colors["panel"])
        core.pack(fill="x", padx=6, pady=(0, 8))
        core_stats = [
            ("Striking", fighter.striking), ("Wrestling", fighter.wrestling), ("Grappling", fighter.grappling),
            ("Cardio", fighter.cardio), ("Chin", fighter.chin), ("Power", fighter.power),
            ("TD Defence", fighter.takedown_defence), ("Ground Ctrl", fighter.ground_control),
            ("Submissions", fighter.submissions), ("Sub Defence", fighter.submission_defence),
            ("Recovery", fighter.recovery), ("Toughness", fighter.toughness),
            ("Fight IQ", fighter.fight_iq), ("Finishing", fighter.finishing_instinct),
        ]
        if stats_visible:
            for idx, (label, value) in enumerate(core_stats):
                self.profile_meter(core, label, value, idx)
        else:
            overall_range = self.scouting_estimate(fighter, "overall", {}) if report.get("status") == "Complete" else {}
            potential_range = self.scouting_estimate(fighter, "potential", {}) if report.get("status") == "Complete" else {}
            summary = "Private fighting attributes are hidden while scouting is enabled."
            if overall_range:
                summary += f"\n\nProjected OVR: {overall_range.get('low')}-{overall_range.get('high')}"
            if potential_range:
                summary += f"\nProjected ceiling: {potential_range.get('low')}-{potential_range.get('high')}"
            if report.get("notes"):
                summary += "\n\n" + "\n".join(f"- {note}" for note in report.get("notes", []))
            tk.Label(core, text=summary, bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), justify="left", anchor="w", wraplength=330).pack(fill="x", padx=12, pady=(10, 8))
            tk.Label(core, text="Basic and observation reports provide stable ranges. A Full Evaluation reveals exact current ratings.", bg=self.colors["panel"], fg=self.colors["muted"], font=("Tahoma", 9), anchor="w", wraplength=330).pack(fill="x", padx=12, pady=(0, 12))

        self.profile_section_label(center, "Career & Camp")
        camp = tk.Frame(center, bg=self.colors["panel"])
        camp.pack(fill="x", padx=6, pady=(0, 8))
        career_rows = [
            ("Popularity", fighter.popularity), ("Momentum", fighter.momentum), ("Morale", fighter.morale),
            ("Motivation", fighter.motivation), ("Fatigue", fighter.fatigue),
            ("Camp Boost", f"+{fighter.camp_boost} ({fighter.camp_weeks} wk, Q{fighter.camp_quality})"),
            ("Development Profile", fighter.career_archetype.replace("Standard Prime", "Balanced Development")),
        ] if stats_visible else [
            ("Scout Status", f"{report.get('status', 'Unscouted')} ({self.scouting_effective_confidence(report) if report else 0}% confidence)"),
            ("Observed Style", fighter.style if self.scouting_effective_confidence(report) >= 25 else "Unknown"),
            ("Known Record", fighter.record),
        ]
        if sport and stats_visible:
            recent = (getattr(fighter, "sport_development_log", None) or [{}])[0]
            latest = "No recorded change yet"
            if recent:
                latest = f"{recent.get('change', 0):+} - {recent.get('reason', 'Training')}"
            career_rows.extend([
                ("Sport Rating", f"{sport_rating:.1f} / Potential {fighter.potential} (+{max(0, min(99, fighter.potential) - sport_rating):.1f})"),
                ("Career Stage", f"{self.combat_sport_development_stage(fighter, sport)} | 12m {self.combat_sport_rating_trend(fighter, sport, 12):+.1f}"),
                ("Latest Development", latest),
            ])
        elif not sport and stats_visible:
            if private_development_visible:
                career_rows.extend([
                    ("Upside", self.upside_assessment(fighter)),
                    ("Career Stage", self.fighter_career_stage(fighter)),
                    ("Annual Peaks", self.annual_overall_chart(fighter)),
                ])
            else:
                potential = (report.get("estimates", {}).get("potential", {}) or {})
                career_rows.extend([
                    ("Projected Ceiling", f"{potential.get('low', '?')}-{potential.get('high', '?')}"),
                    ("Career Stage", self.fighter_career_stage(fighter)),
                    ("Development Detail", "Private; potential remains a scout projection"),
                ])
        for idx, (label, value) in enumerate(career_rows):
            self.profile_info_row(camp, label, value, idx)

        notebook = ttk.Notebook(body)
        notebook.pack(side="left", fill="both", expand=True)
        stand_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        grappling_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        business_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        history_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        development_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(stand_frame, text="Striking")
        notebook.add(grappling_frame, text="Grappling")
        notebook.add(business_frame, text="Business")
        if not sport and stats_visible and private_development_visible:
            notebook.add(development_frame, text="Development")
        notebook.add(history_frame, text="Fight History")

        for frame, groups in ((stand_frame, ("Standing", "Muay Thai Clinch", "Physical")), (grappling_frame, ("Wrestling", "Ground", "Mental"))):
            tree = ttk.Treeview(frame, columns=("skill", "value", "grade"), show="headings", height=22)
            for col, text, width in (("skill", "Skill", 210), ("value", "Value", 80), ("grade", "Grade", 100)):
                tree.heading(col, text=text)
                tree.column(col, width=width, anchor="w")
            tree.pack(fill="both", expand=True, padx=8, pady=8)
            if stats_visible:
                self.fill_profile_skill_tree(tree, fighter, groups)
            else:
                tree.insert("", "end", values=("Scouting required", "Hidden", "Full report needed"))

        business = tk.Frame(business_frame, bg=self.colors["panel"])
        business.pack(fill="both", expand=True, padx=8, pady=8)
        self.profile_section_label(business, "Contract")
        contract = tk.Frame(business, bg=self.colors["panel"])
        contract.pack(fill="x", padx=4, pady=(0, 8))
        contract_rows = [("Type", fighter.contract_type), ("Purse", f"${fighter.purse:,}/fight")]
        if getattr(fighter, "comeback_contract", False):
            contract_rows.append(("Comeback Commitment", f"{getattr(fighter, 'contract_fights_completed', 0)}/{getattr(fighter, 'guaranteed_fights', 0)} fights"))
        elif getattr(fighter, "retirement_pending", False):
            contract_rows.append(("Retirement Status", "One final bout due - or renew comeback"))
        else:
            contract_rows.append(("Months", fighter.contract_months))
        business_rows = contract_rows + [
            ("Star Quality", fighter.star_quality), ("Charisma", fighter.charisma), ("Media", fighter.media_presence),
            ("Sponsor", fighter.sponsor_appeal), ("Professionalism", fighter.professionalism), ("Injury Risk", fighter.injury_proneness),
            ("Major Injury", self.serious_injury_status(fighter)),
            ("Career Goal", f"{fighter.career_goal or 'Undeclared'} ({getattr(fighter, 'career_goal_progress', 0)}%)"),
            ("Walk Weight", f"{fighter.walk_weight or self.default_walk_weight(fighter)} lb"), ("Last Scale", f"{fighter.scale_weight or '-'} lb"), ("Cut Penalty", fighter.weight_cut_penalty),
            ("Division Fit", getattr(fighter, "division_size_note", "") or (f"Undersized penalty {getattr(fighter, 'division_size_penalty', 0)}/14" if getattr(fighter, "division_size_penalty", 0) else "Natural division fit")),
        ] if stats_visible else [
            ("Contract", "Terms private"), ("Market Access", "Under contract with another promotion"),
            ("Scouting", f"{report.get('status', 'Unscouted')} - {report.get('reveal', 0)}% confidence"),
        ]
        for idx, (label, value) in enumerate(business_rows):
            self.profile_info_row(contract, label, value, idx)

        if not sport and stats_visible and private_development_visible:
            development = self.fighter_development_explanation(fighter)
            dev_header = tk.Frame(development_frame, bg=self.colors["panel"])
            dev_header.pack(fill="x", padx=8, pady=(8, 4))
            tk.Label(dev_header, text=development["outlook"], bg=self.colors["panel"], fg=self.colors["gold"], font=("Impact", 13), anchor="w").pack(fill="x", padx=8, pady=(6, 1))
            tk.Label(
                dev_header,
                text=(f"Monthly development score {development['score']:.1f} | Current OVR {fighter.overall} | "
                      f"Potential {fighter.potential} | Prime {fighter.prime_start}-{fighter.prime_end}"),
                bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w",
            ).pack(fill="x", padx=8, pady=(0, 6))
            factor_tree = ttk.Treeview(development_frame, columns=("factor", "effect", "meaning"), show="headings", height=12)
            for col, label, width in (("factor", "Development Factor", 260), ("effect", "Monthly Effect", 110), ("meaning", "What It Means", 390)):
                factor_tree.heading(col, text=label); factor_tree.column(col, width=width, anchor="w")
            meanings = {
                "Gym quality": "The quality of the room and daily training partners.", "Gym facilities": "Recovery, equipment and training infrastructure.",
                "Coaching": "How well the coaches and gym specialty fit this fighter.", "Dedication": "Training habits and professionalism.",
                "Age": "Learning runway before and through the fighter's prime.", "Potential": "Remaining ceiling; development slows as the gap closes.",
                "Recent victories": "Momentum and strong regional results reinforce progress.", "Motivation": "Morale and willingness to train.",
                "Active competition": "Recent bouts and a structured developmental pathway.", "Learning traits": "Traits that improve learning speed.",
                "Fatigue": "Injury and accumulated fatigue reduce useful training.", "Gym crowding": "Over-capacity rooms reduce individual coaching attention.",
            }
            for label, value in self.fighter_development_factors(fighter):
                meaning = next((text for key, text in meanings.items() if label.startswith(key)), "Calculated from the fighter's current career state.")
                factor_tree.insert("", "end", values=(label, f"{value:+.1f}", meaning), tags=("negative" if value < 0 else "positive",))
            factor_tree.tag_configure("positive", foreground="#9de6a0"); factor_tree.tag_configure("negative", foreground="#ff9b9b")
            factor_tree.pack(fill="both", expand=True, padx=8, pady=4)
            dev_log = tk.Text(development_frame, wrap="word", height=7, bg=self.colors["panel_dark"], fg=self.colors["text"], padx=10, pady=8)
            dev_log.pack(fill="x", padx=8, pady=(4, 8))
            history = getattr(fighter, "development_log", None) or []
            if history:
                for entry in history:
                    dev_log.insert("end", f"{entry.get('date', '')}  |  OVR {entry.get('before', '?')} -> {entry.get('after', '?')}  |  {entry.get('type', 'Development')}\n{entry.get('reason', '')}\n\n")
            else:
                dev_log.insert("end", "No recorded overall change yet. The factors above are the exact inputs to the next monthly development opportunity.")
            dev_log.config(state="disabled")

        history_controls = ttk.Frame(history_frame, style="Inset.TFrame"); history_controls.pack(fill="x", padx=8, pady=(8, 0))
        in_universe_record = (
            max(0, fighter.record_w - baseline_record[0]),
            max(0, fighter.record_l - baseline_record[1]),
            max(0, fighter.record_d - baseline_record[2]),
        )
        baseline_text = "-".join(map(str, baseline_record))
        universe_text = "-".join(map(str, in_universe_record))
        pre_universe_note = f"   |   Pre-universe: {baseline_text}" if any(baseline_record) else ""
        amateur_record = (
            int(getattr(fighter, "amateur_w", 0) or 0),
            int(getattr(fighter, "amateur_l", 0) or 0),
            int(getattr(fighter, "amateur_d", 0) or 0),
        )
        amateur_note = f"   |   Academy Amateur: {'-'.join(map(str, amateur_record))}" if any(amateur_record) else ""
        ttk.Label(
            history_controls,
            text=(
                f"Pro Record: {fighter.record}   |   In-universe: {universe_text}{pre_universe_note}{amateur_note}"
                f"   |   Activity: {self.fighter_activity_rating(fighter)}/100"
                f"   |   Competitiveness: {self.fighter_competitiveness_rating(fighter)}/100"
            ),
            style="Inset.TLabel",
        ).pack(side="left", padx=4)
        history_opponent_button = ttk.Button(history_controls, text="View Opponent", state="disabled")
        history_opponent_button.pack(side="left", padx=(8, 4))
        history_card_button = ttk.Button(history_controls, text="View Card", state="disabled")
        history_card_button.pack(side="left", padx=4)
        history_filter = tk.StringVar(value="All")
        ttk.Combobox(history_controls, textvariable=history_filter, values=("All", "Professional", "Amateur", "Wins", "Losses"), state="readonly", width=14).pack(side="right", padx=4)
        history_tree_shell = ttk.Frame(history_frame, style="Chrome.TFrame")
        history_tree_shell.pack(fill="both", expand=True, padx=8, pady=6)
        history_tree = ttk.Treeview(history_tree_shell, columns=("date", "result", "stakes", "opponent", "opponent_record", "fighter_rating", "opponent_rating", "event", "method", "scorecard", "weight"), show="headings", height=15)
        for col, label, width in (("date", "Date", 108), ("result", "Result", 58), ("stakes", "Stakes", 95), ("opponent", "Opponent", 138), ("opponent_record", "Opp. Record", 88), ("fighter_rating", "Your Rating", 112), ("opponent_rating", "Opp. Rating", 112), ("event", "Event", 185), ("method", "Method", 105), ("scorecard", "Scorecards", 120), ("weight", "Division", 105)):
            history_tree.heading(col, text=label); history_tree.column(col, width=width, anchor="w")
        history_tree.tag_configure("win", foreground="#9de6a0"); history_tree.tag_configure("loss", foreground="#ff9b9b"); history_tree.pack(side="left", fill="both", expand=True)
        history_yscroll = ttk.Scrollbar(history_tree_shell, orient="vertical", command=history_tree.yview)
        history_yscroll.pack(side="right", fill="y")
        history_tree.configure(yscrollcommand=history_yscroll.set)
        history_xscroll = ttk.Scrollbar(history_frame, orient="horizontal", command=history_tree.xview)
        history_xscroll.pack(fill="x", padx=8, pady=(0, 4)); history_tree.configure(xscrollcommand=history_xscroll.set)
        history_detail = tk.Text(history_frame, wrap="word", font=("Tahoma", 9), height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], padx=10, pady=8); history_detail.pack(fill="x", padx=8, pady=(0, 8)); history_detail.config(state="disabled")
        entries = fighter.fight_history or []

        def history_opponent(entry, context=None):
            """Find the real opponent even when old save history is plain text."""
            text = str(entry)
            opponent_name = str((context or {}).get("opponent_name", "") or "")
            opponent_id = str((context or {}).get("opponent_id", "") or "")
            sport = str((context or {}).get("sport", "") or "")
            division = str((context or {}).get("weight", "") or "")
            candidates = [
                candidate for _company, candidate in self.fighter_instances_with_companies(include_retired=True)
                if candidate is not fighter and candidate.name != fighter.name
                and (candidate.fighter_id == opponent_id if opponent_id else (candidate.name.casefold() == opponent_name.casefold() if opponent_name else False))
            ]
            if sport:
                sport_matches = [candidate for candidate in candidates if str(getattr(candidate, "primary_discipline", "") or "") == sport]
                if sport_matches:
                    candidates = sport_matches
            if division:
                division_matches = [candidate for candidate in candidates if str(getattr(candidate, "sport_weight_class", "") or candidate.weight) == division]
                if division_matches:
                    candidates = division_matches
            return max(candidates, key=lambda candidate: (len(candidate.name), candidate.record_w + candidate.record_l + candidate.record_d), default=None)

        def parsed(entry):
            text = str(entry)
            amateur = "Amateur" if "Amateur" in text else "Professional"
            opponent_name = self.fighter_history_opponent_name(fighter, text)
            opponent_fighter = history_opponent(text, {"opponent_name": opponent_name}) if opponent_name else None
            if f"{fighter.name} def. " in text or "Amateur W" in text or "W over" in text or f"{fighter.name} won an outside fight" in text:
                result = "W"
            elif "fought to a draw" in text or "Amateur D" in text or f"{fighter.name} drew an outside fight" in text:
                result = "D"
            elif (" def. " in text and fighter.name in text) or "Amateur L" in text or "L to" in text or f"{fighter.name} lost an outside fight" in text:
                result = "L"
            else:
                result = "-"
            method = text.split(" by ", 1)[1].split(" at ", 1)[0] if " by " in text else "Draw" if result == "D" else "-"
            context = self.fighter_history_card_context(fighter, text, opponent_fighter or opponent_name)
            opponent = context.get("opponent_name", "-") or (opponent_fighter.name if opponent_fighter else "-")
            opponent_fighter = history_opponent(text, context) if opponent != "-" else opponent_fighter
            log_result = ""
            for fight_log in (context.get("record", {}) or {}).get("fight_logs", []):
                names = (str(fight_log.get("a", "")), str(fight_log.get("b", "")))
                if fighter.name in names and (opponent == "-" or opponent in names):
                    log_result = str(fight_log.get("result", ""))
                    break
            if " by " in log_result:
                method = log_result.split(" by ", 1)[1].rsplit(" (R", 1)[0]
            fighter_rating = context.get("fighter_rating", {}) or {}
            opponent_rating = context.get("opponent_rating", {}) or {}
            def format_rating(snapshot):
                overall, elo = snapshot.get("overall"), snapshot.get("elo")
                if overall in (None, "") and elo in (None, ""):
                    return "-"
                parts = []
                if overall not in (None, ""):
                    parts.append(f"OVR {overall}")
                if elo not in (None, ""):
                    parts.append(f"ELO {elo}")
                return " | ".join(parts)
            fighter_rating_text = format_rating(fighter_rating)
            opponent_rating_text = format_rating(opponent_rating)
            if not stats_visible:
                fighter_rating_text = "Hidden"
                opponent_rating_text = "Hidden"
            stakes = self.fight_stakes_label(context)
            detail = self.format_game_date_text(text)
            detail += f"\n\nDate: {self.format_game_date_text(context['date'])}\nEvent: {context['event']}\nStakes: {stakes}\nRecord source: {context.get('source', 'Legacy history entry')}\nOpponent record: {context['opponent_record']}\nYour rating at fight time: {fighter_rating_text}\nOpponent rating at fight time: {opponent_rating_text}\nScorecards: {context['scorecard']}"
            return {
                "result": result, "level": amateur, "opponent": opponent, "opponent_fighter": opponent_fighter,
                "date": self.format_game_date_text(context["date"]), "stakes": stakes, "opponent_record": context["opponent_record"], "event": context["event"],
                "fighter_rating": fighter_rating_text, "opponent_rating": opponent_rating_text,
                "method": method, "scorecard": context["scorecard"], "weight": context["weight"],
                "detail": detail, "card": context["record"],
            }
        rows = []
        resolved_bouts = set()
        for entry in entries[:100]:
            row = parsed(entry)
            if row["result"] not in ("W", "L", "D"):
                continue
            # Legacy saves can retain the same string twice. Only suppress a row when
            # it resolves to the exact same archived bout, never merely on a matching
            # name or date.
            key = (row["date"], row["event"], row["opponent"], row["method"], row["weight"])
            if row["card"] and key in resolved_bouts:
                continue
            if row["card"]:
                resolved_bouts.add(key)
            rows.append(row)
        # Academy background is intentionally rendered as its own ledger. It
        # can identify the opponent and result, but it is never treated as a
        # professional card or replay archive.
        for record in list(getattr(fighter, "amateur_bout_history", None) or [])[:100]:
            if not isinstance(record, dict):
                continue
            opponent_name = str(record.get("opponent", "Unknown opponent") or "Unknown opponent")
            opponent_fighter = history_opponent("", {"opponent_name": opponent_name})
            result = str(record.get("result", "-") or "-")[:1]
            month = int(record.get("month", 0) or 0)
            week = int(record.get("week", 1) or 1)
            raw_date = f"Month {month} Week {week}" if month else "Academy period"
            event = str(record.get("event", "Academy Showcase") or "Academy Showcase")
            method = str(record.get("method", "-") or "-")
            round_no = record.get("round", "?")
            detail = (
                f"Date: {self.format_game_date_text(raw_date)}\nEvent: {event}\n"
                f"Level: Amateur academy bout\nOpponent: {opponent_name}\n"
                f"Method: {method} (R{round_no})\n"
                "This amateur result is separate from the professional record and has no retained event replay."
            )
            rows.append({
                "result": result, "level": "Amateur", "opponent": opponent_name, "opponent_fighter": opponent_fighter,
                "date": self.format_game_date_text(raw_date), "stakes": "AMATEUR", "opponent_record": "-", "event": event,
                "fighter_rating": "-", "opponent_rating": "-", "method": method, "scorecard": "-",
                "weight": str(record.get("weight", "Youth Openweight") or "Youth Openweight"), "detail": detail, "card": None,
            })
        history_rows_by_id = {}
        def render_history(*_):
            history_tree.delete(*history_tree.get_children())
            history_rows_by_id.clear()
            history_opponent_button.configure(state="disabled")
            history_card_button.configure(state="disabled")
            for index, row in enumerate(rows):
                mode = history_filter.get()
                if mode != "All" and mode not in (row["level"], "Wins" if row["result"] == "W" else "Losses" if row["result"] == "L" else ""):
                    continue
                row_id = str(index)
                history_rows_by_id[row_id] = row
                tag = "win" if row["result"] == "W" else "loss" if row["result"] == "L" else ""
                history_tree.insert("", "end", iid=row_id, tags=(tag,), values=(row["date"], row["result"], row["stakes"], row["opponent"], row["opponent_record"], row["fighter_rating"], row["opponent_rating"], row["event"], row["method"], row["scorecard"], row["weight"]))
        def show_history(_event=None):
            selected = history_tree.selection()
            row = history_rows_by_id.get(selected[0]) if selected else None
            history_detail.config(state="normal")
            history_detail.delete("1.0", "end")
            history_detail.insert("end", row["detail"] if row else "Select an in-universe fight to see its recorded context. Only bouts still present in the replay archive can open a saved card.")
            history_detail.config(state="disabled")
            history_opponent_button.configure(state="normal" if row and row["opponent_fighter"] else "disabled")
            history_card_button.configure(state="normal" if row and row["card"] else "disabled")

        def open_history_opponent(_event=None):
            selected = history_tree.selection()
            row = history_rows_by_id.get(selected[0]) if selected else None
            opponent = row["opponent_fighter"] if row else None
            if opponent:
                self.open_fighter_profile_window(opponent)

        def open_history_card(_event=None):
            selected = history_tree.selection()
            row = history_rows_by_id.get(selected[0]) if selected else None
            if row and row["card"]:
                self.open_result_card_window(row["card"])

        history_opponent_button.configure(command=open_history_opponent)
        history_card_button.configure(command=open_history_card)
        history_filter.trace_add("write", render_history)
        history_tree.bind("<<TreeviewSelect>>", show_history)
        history_tree.bind("<Double-1>", open_history_card)
        render_history()

        if fighter.serious_injury_history:
            medical = tk.Text(history_frame, wrap="word", height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            medical.pack(fill="x", padx=8, pady=(0, 8))
            medical.insert("end", "MEDICAL HISTORY\n" + "\n".join(self.format_game_date_text(item) for item in fighter.serious_injury_history[-4:]))
            medical.config(state="disabled")
        if fighter.rivalry_history:
            rivalry_log = tk.Text(history_frame, wrap="word", height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            rivalry_log.pack(fill="x", padx=8, pady=(0, 8))
            rivalry_log.insert("end", "RIVALRY TIMELINE\n" + "\n".join(self.format_game_date_text(item) for item in fighter.rivalry_history[-4:]))
            rivalry_log.config(state="disabled")
        if fighter.weight_class_history:
            division_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            division_log.pack(fill="x", padx=8, pady=(0, 8))
            division_log.insert("end", "DIVISION HISTORY\n" + "\n".join(self.format_game_date_text(item) for item in fighter.weight_class_history[-3:]))
            division_log.config(state="disabled")
        if fighter.career_achievements:
            achievement_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 9), padx=10, pady=8)
            achievement_log.pack(fill="x", padx=8, pady=(0, 8))
            achievement_log.insert("end", "CAREER ACHIEVEMENTS\n" + " • ".join(fighter.career_achievements[-6:]))
            achievement_log.config(state="disabled")
        if fighter.career_goal_history:
            goal_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            goal_log.pack(fill="x", padx=8, pady=(0, 8))
            goal_log.insert("end", "CAREER GOALS\nActive: " + (fighter.career_goal or "Undeclared") + f" ({getattr(fighter, 'career_goal_progress', 0)}%)\n" + "\n".join(self.format_game_date_text(item) for item in fighter.career_goal_history[-2:]))
            goal_log.config(state="disabled")

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Market Identity", command=lambda: self.open_regional_identity_window(fighter)).pack(side="left", padx=4)
        if getattr(fighter, "retired", False):
            ttk.Button(
                footer, text="Offer Comeback Deal", style="Accent.TButton",
                command=lambda: self.offer_comeback_deal(fighter, window),
            ).pack(side="left", padx=4)
        elif (self.player_owns_fighter(fighter)
              and getattr(fighter, "retirement_pending", False)
              and getattr(fighter, "retirement_fight_due_after_month", 0) > 0):
            ttk.Button(
                footer, text="Renew Comeback Deal", style="Accent.TButton",
                command=lambda: self.open_contract_negotiation(fighter, existing=True, comeback=True),
            ).pack(side="left", padx=4)
        elif self.player_owns_fighter(fighter):
            ttk.Button(
                footer,
                text="Move To Active Division" if owned_closed_division else "Change Weight Class",
                style="Accent.TButton" if owned_closed_division else "TButton",
                command=lambda: self.open_weight_class_move_dialog(fighter, window),
            ).pack(side="left", padx=4)
            if owned_closed_division:
                # Stranded in a shut division: offer a paid release as the alternative to moving.
                ttk.Button(footer, text="Cut From Roster", command=lambda: self.cut_player_fighter(fighter, window)).pack(side="left", padx=4)
        elif not fighter.retired:
            if self.rules.get("scouting_mode", False) and not stats_visible:
                ttk.Button(footer, text="Basic Dossier", command=lambda: self.start_scout_report_for_fighter(fighter, "basic")).pack(side="left", padx=4)
                ttk.Button(footer, text="Full Evaluation", style="Accent.TButton", command=lambda: self.start_scout_report_for_fighter(fighter, "full")).pack(side="left", padx=4)
                ttk.Button(footer, text="Observe Next Fight", command=lambda: self.start_scout_report_for_fighter(fighter, "observation")).pack(side="left", padx=4)
            if fighter in self.free_agents:
                ttk.Button(footer, text="Negotiate Contract", style="Accent.TButton", command=lambda: self.open_contract_negotiation(fighter, existing=False)).pack(side="left", padx=4)
            source_promotion = self.promotion_owning_fighter(fighter)
            if (source_promotion and not getattr(source_promotion, "is_regional_feeder", False) and not sport
                    and not fighter.champion and not getattr(fighter, "interim_champion", False)
                    and not self.fighter_current_championships(fighter)):
                ttk.Button(
                    footer,
                    text="Transfer Offer",
                    style="Accent.TButton",
                    command=lambda promo=source_promotion: self.open_transfer_negotiation(fighter, promo, window),
                ).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4)

    def open_regional_identity_window(self, fighter):
        window = tk.Toplevel(self.root)
        window.title(f"Market Identity - {fighter.name}")
        window.geometry("760x560")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"MARKET IDENTITY: {fighter.name.upper()}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text="Origin, adopted homes, and local drawing power", style="Chrome.TLabel").pack(side="right", padx=10)
        summary = tk.Text(window, height=7, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 10), padx=12, pady=10)
        summary.pack(fill="x", padx=8, pady=8)
        connections = ", ".join(getattr(fighter, "cultural_connections", None) or []) or "No documented connections"
        summary.insert("end", f"Nationality: {fighter.nationality}\nBorn: {getattr(fighter, 'hometown', '-')}, {getattr(fighter, 'birth_country', fighter.region)} ({getattr(fighter, 'birth_region', fighter.region)})\nResidence / fighting base: {getattr(fighter, 'residence', fighter.region)}\nTraining location: {getattr(fighter, 'training_location', fighter.region)}\nCultural connections: {connections}\n\nHome events create stronger morale, media, merchandise, and regional-popularity gains. A hometown appearance is the strongest connection.")
        summary.config(state="disabled")
        tree = ttk.Treeview(window, columns=("market", "popularity", "connection", "forecast"), show="headings")
        for column, label, width in (("market", "Market", 130), ("popularity", "Regional Popularity", 150), ("connection", "Connection", 180), ("forecast", "Home-Event Effect", 250)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        markets = getattr(fighter, "regional_popularity", {}) or {}
        for region in sorted(REGIONS, key=lambda region: markets.get(region, 0), reverse=True):
            connection = self.fighter_event_connection(fighter, region, "")
            effect = "Strong local draw" if connection["strength"] >= 0.66 else "Recognised market" if connection["strength"] >= 0.36 else "Neutral market"
            tree.insert("", "end", values=(region, f"{markets.get(region, 0)}/100", connection["level"], effect))
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        history = getattr(fighter, "home_event_history", None) or []
        if history:
            ttk.Label(window, text="Recent market moments: " + " | ".join(f"{self.format_game_date(item.get('month', self.month), 1, include_week=False)} {item.get('region', '')}: {item.get('note', '')}" for item in history[:3]), style="Inset.TLabel", wraplength=720).pack(fill="x", padx=10, pady=(0, 6))
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=10, pady=(0, 10))

    def open_career_goals_window(self):
        window = tk.Toplevel(self.root)
        window.title("Fighter Career Goals")
        window.geometry("900x560")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="FIGHTER CAREER GOALS", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text="Ambitions influence morale, motivation, and retention", style="Chrome.TLabel").pack(side="right", padx=10)
        tree = ttk.Treeview(window, columns=("fighter", "division", "persona", "goal", "progress", "trust", "morale"), show="headings")
        for column, label, width in (("fighter", "Fighter", 165), ("division", "Division", 115), ("persona", "Persona", 115), ("goal", "Career Goal", 220), ("progress", "Progress", 90), ("trust", "Trust", 65), ("morale", "Morale", 65)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        detail = tk.Text(window, height=6, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(fill="x", padx=8, pady=(0, 8)); detail.config(state="disabled")
        rows = sorted(self.roster, key=lambda fighter: (getattr(fighter, "career_goal_progress", 0), fighter.name))
        for index, fighter in enumerate(rows):
            tree.insert("", "end", iid=str(index), values=(fighter.name, fighter.weight, fighter.negotiation_persona, fighter.career_goal or "Undeclared", f"{fighter.career_goal_progress}%", fighter.relationship_trust, fighter.morale))
        def select(_event=None):
            selected = tree.selection(); detail.config(state="normal"); detail.delete("1.0", "end")
            if selected:
                fighter = rows[int(selected[0])]
                history = "\n".join(fighter.career_goal_history[-4:]) if fighter.career_goal_history else "No completed career goals yet."
                detail.insert("end", f"{fighter.name}\nGoal: {fighter.career_goal or 'Undeclared'} | Progress: {fighter.career_goal_progress}% | Target: {fighter.career_goal_target}\nPersona: {fighter.negotiation_persona} | Agent: {fighter.agent_name}\n\nGoal history:\n{history}")
            detail.config(state="disabled")
        def open_profile(_event=None):
            selected = tree.selection()
            if selected:
                self.open_fighter_profile_window(rows[int(selected[0])])
        tree.bind("<<TreeviewSelect>>", select); tree.bind("<Double-1>", open_profile)

    def open_limited_scout_profile(self, fighter, report):
        window = tk.Toplevel(self.root); window.title(f"Scout Report - {fighter.name}"); window.geometry("520x360"); window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"SCOUT REPORT: {fighter.name.upper()}", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=10)
        text = tk.Text(window, wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        text.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        reveal = report.get("reveal", 0)
        text.insert("end", f"{fighter.gender} | {fighter.weight} | Age {fighter.age} | {fighter.region}\nStyle: {fighter.style if reveal >= 25 else 'Unknown'}\n\nReport status: {report.get('status', 'Unscouted')}\nConfidence: {reveal}%\nScout: {report.get('scout', 'No assigned scout')}\n\n")
        text.insert("end", "Findings:\n" + ("\n".join(f"- {note}" for note in report.get('notes', [])) or "- No verified findings yet.") + "\n\nYou can negotiate immediately. A Full Scout report is only required to reveal exact ratings and reduce recruitment risk.")
        text.config(state="disabled")
        actions = ttk.Frame(window, style="Chrome.TFrame"); actions.pack(fill="x", padx=10, pady=(0, 10))
        if fighter in self.free_agents:
            ttk.Button(actions, text="Negotiate Without Full Scout", style="Accent.TButton", command=lambda: self.open_contract_negotiation(fighter)).pack(side="left")
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right")

    def open_weight_class_move_dialog(self, fighter, profile_window=None):
        window = tk.Toplevel(self.root)
        window.title(f"Weight Class Move - {fighter.name}")
        window.geometry("620x260")
        window.resizable(False, False)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"CHANGE DIVISION: {fighter.name.upper()}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(body, text=f"Current: {fighter.gender} {fighter.weight} | Walk weight: {fighter.walk_weight or self.default_walk_weight(fighter)} lb", style="Panel.TLabel").pack(anchor="w", padx=10, pady=(10, 6))
        row = ttk.Frame(body, style="Inset.TFrame")
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text="Target division", style="Inset.TLabel").pack(side="left", padx=(6, 4))
        target_weights = self.player_weight_move_targets(fighter)
        default_target = fighter.weight if fighter.weight in target_weights else (target_weights[0] if target_weights else "")
        target = tk.StringVar(value=default_target)
        combo = ttk.Combobox(row, textvariable=target, values=target_weights, state="readonly", width=20)
        combo.pack(side="left")
        assessment = ttk.Label(body, text="Choose a target division to check body and cut suitability.", style="Inset.TLabel", wraplength=560, justify="left")
        assessment.pack(fill="x", padx=10, pady=(8, 4))

        def refresh_assessment(_event=None):
            if not target.get():
                assessment.config(text="No active destination exists for this fighter's gender. Reopen a division first.")
                return
            _allowed, message = self.weight_class_move_assessment(fighter, target.get())
            assessment.config(text=message)

        def confirm_move():
            if self.move_fighter_weight_class(fighter, target.get()):
                window.destroy()
                if profile_window and profile_window.winfo_exists():
                    profile_window.destroy()

        combo.bind("<<ComboboxSelected>>", refresh_assessment)
        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Confirm Move", style="Accent.TButton", command=confirm_move).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4)
        refresh_assessment()

    def annual_overall_chart(self, fighter):
        peaks = fighter.annual_overalls or {}
        if not peaks:
            return "None"
        return " | ".join(f"{year}:{score}" for year, score in sorted(peaks.items())[-5:])

    def generate_portrait_palette(self, name):
        palettes = [
            ("#1f2937", "#f59e0b"), ("#172554", "#38bdf8"), ("#3b0a0a", "#ef4444"),
            ("#1b4332", "#74c69d"), ("#2e1065", "#c084fc"), ("#3f2f1d", "#facc15"),
            ("#111827", "#e5e7eb"), ("#4a1d1f", "#fb7185"), ("#0f172a", "#22d3ee"),
        ]
        return palettes[sum(ord(ch) for ch in name) % len(palettes)]

    def draw_fighter_portrait(self, fighter):
        if not hasattr(self, "portrait_canvas"):
            return
        canvas = self.portrait_canvas
        canvas.delete("all")
        bg = fighter.portrait_bg or "#222222"
        accent = fighter.portrait_accent or "#c3a45d"
        canvas.configure(bg=bg)
        canvas.create_rectangle(0, 0, 104, 104, fill=bg, outline=accent, width=3)
        canvas.create_oval(32, 14, 72, 54, fill=accent, outline="")
        canvas.create_polygon(18, 96, 32, 62, 72, 62, 88, 96, fill="#d7d7d7", outline="")
        canvas.create_rectangle(18, 86, 88, 104, fill=accent, outline="")
        initials = "".join(part[0] for part in fighter.name.replace("'", "").split()[:2]).upper()
        canvas.create_text(52, 35, text=initials, fill=bg, font=("Impact", 18))
        self.fit_canvas_text(canvas, 52, 94, f"{self.weight_abbreviation(fighter.weight)} {fighter.overall}", bg, 70, base_size=8)
        self.draw_portrait_status_markers(canvas, fighter, large=False)

    def matchmaking_title_path_label(self, fighter):
        """Compact title-path read for the matchmaking table (space-conscious)."""
        if getattr(fighter, "champion", False):
            origin = self.fighter_title_reign_origin(fighter, self.player_company_name)
            return "Champion (appointed)" if origin.startswith("Appointed") else "Champion"
        if getattr(fighter, "owed_title_shot", False):
            return "Owed shot"
        rank = getattr(fighter, "ranking_position", 0)
        if rank == 1:
            return "#1 contender"
        if rank and rank <= 5:
            return "Top 5"
        if rank and rank <= 10:
            return "Top 10"
        return "Merit"

    def matchmaking_form_label(self, fighter):
        """Compact momentum read matching the rankings tab's Form column."""
        if getattr(fighter, "champion", False):
            return "Champ"
        streak = getattr(fighter, "career_win_streak", 0)
        if streak >= 3:
            return f"W{streak}"
        momentum = getattr(fighter, "momentum", 0)
        if momentum >= 3:
            return "Rising"
        if momentum <= -3:
            return "Sliding"
        return "Steady"

    def available_row_tags(self, fighter, booking_status):
        """Row tags for the available-fighters table: unavailable fighters stay
        flagged; available ones are tinted green/red by their win-loss record.
        (ttk colours a whole row, not a single cell.)"""
        if booking_status != "Ready":
            return ("not_ready",)
        wins = getattr(fighter, "record_w", 0)
        losses = getattr(fighter, "record_l", 0)
        if wins > losses:
            return ("rec_win",)
        if losses > wins:
            return ("rec_loss",)
        return ()

    def refresh_available(self):
        self.ensure_player_event_name()
        self.refresh_player_division_filter_options("matchmaking")
        self.available_tree.delete(*self.available_tree.get_children())
        self.available_tree_fighters = {}
        weight = self.available_weight_filter.get() if hasattr(self, "available_weight_filter") else "All"
        gender = self.available_gender_filter.get() if hasattr(self, "available_gender_filter") else "All"
        status = self.available_status_filter.get() if hasattr(self, "available_status_filter") else "All"
        query = self.available_search.get().strip() if hasattr(self, "available_search") else ""
        target_date = self.selected_booking_date(reject_past=False)
        target_month, target_week = target_date if target_date else (self.month, self.week)
        division_ranks = self.player_division_rank_map()
        for row_index, fighter in enumerate(sorted(self.roster, key=lambda f: (WEIGHTS.index(f.weight), division_ranks.get(self.fighter_identity_key(f), 99), -f.overall, -f.popularity))):
            if self.belt_key(fighter.gender, fighter.weight) in set(getattr(self, "closed_divisions", set())):
                continue
            if weight != "All" and fighter.weight != weight:
                continue
            if gender != "All" and fighter.gender != gender:
                continue
            booking_status = self.fighter_matchmaking_status(fighter, target_month, target_week)
            if status == "Ready":
                if booking_status != "Ready":
                    continue
            elif not self.fighter_matches_status_filter(fighter, status):
                continue
            if not self.fighter_matches_text_filter(fighter, query):
                continue
            name = self.fighter_display_name(fighter)
            rank = division_ranks.get(self.fighter_identity_key(fighter))
            rank_label = "C" if fighter.champion else f"#{rank}" if rank else "-"
            row_id = self.fighter_tree_row_id("available", fighter, row_index)
            self.available_tree_fighters[row_id] = fighter
            self.available_tree.insert(
                "", "end", iid=row_id,
                tags=self.available_row_tags(fighter, booking_status),
                values=(
                    name, fighter.gender[0], fighter.weight, rank_label,
                    self.matchmaking_title_path_label(fighter), fighter.record, fighter.age,
                    fighter.overall, fighter.elo_rating, fighter.popularity,
                    self.fight_build_score(fighter, rank=rank), self.fighter_last_fight_date_label(fighter),
                    self.world_fighter_last_five(fighter), self.matchmaking_form_label(fighter),
                    self.fighter_activity_rating(fighter), self.fighter_fatigue_label(fighter),
                    self.fighter_recovery_date_label(fighter), "-", "-", booking_status,
                 ),
             )
        self.refresh_matchmaking_history_indicators()

    def fighter_last_fight_date_label(self, fighter):
        for entry in getattr(fighter, "bout_rating_history", None) or []:
            if isinstance(entry, dict) and entry.get("date"):
                return self.format_game_date_text(entry["date"])
        month = int(getattr(fighter, "last_fight_month", 0) or 0)
        return self.format_game_date(month, 1, include_week=False) if month else "Never"

    def matchmaking_fit_score(self, a, b):
        if not a or not b or a is b or a.gender != b.gender or a.weight != b.weight:
            return None
        score, _reason = self.matchmaking_score(a, b)
        # The assistant's raw score can exceed 100 because hype, rivalry and
        # title logic stack. Compress it into a readable scouting scale while
        # preserving the order of candidates.
        return max(1, min(99, round(20 + score * 0.65)))

    def suggested_matchmaking_opponent(self, fighter, target_month, target_week):
        busy = self.scheduled_fighter_names(include_booked=True)
        if fighter.name in busy or fighter.injured or fighter.fatigue >= 65 or not self.fighter_available_for_date(fighter, target_month, target_week, self.selected_booking_day()):
            return None
        candidates = []
        for opponent in self.roster:
            if opponent is fighter or opponent.gender != fighter.gender or opponent.weight != fighter.weight:
                continue
            if opponent.name in busy or opponent.injured or opponent.fatigue >= 65:
                continue
            if not self.fighter_available_for_date(opponent, target_month, target_week):
                continue
            fit = self.matchmaking_fit_score(fighter, opponent)
            if fit is None:
                continue
            _score, reason = self.matchmaking_score(fighter, opponent)
            candidates.append((fit, self.match_build_score(fighter, opponent, {"title": False, "main": False}), reason, opponent))
        return max(candidates, key=lambda item: (item[0], item[1], item[3].overall), default=None)

    def matchmaking_fighter_brief(self, fighter, suggestion=None):
        rank = self.division_rank_label(fighter)
        last_fight = str(getattr(fighter, "last_fight", "None") or "None")
        if len(last_fight) > 90:
            last_fight = last_fight[:87] + "..."
        camp = f"{fighter.camp} | {fighter.camp_weeks} wk | boost {fighter.camp_boost:+d}"
        line_one = (
            f"{fighter.name.upper()} | {rank} | Record {fighter.record} | OVR {fighter.overall} | ELO {fighter.elo_rating} | "
            f"Form {self.world_fighter_last_five(fighter)} | Activity {self.fighter_activity_rating(fighter)}/100 | Momentum {fighter.momentum:+d}"
        )
        line_two = (
            f"Last fight: {self.fighter_last_fight_date_label(fighter)} - {last_fight} | "
            f"Camp: {camp} | Fatigue {self.fighter_fatigue_label(fighter)} | "
            f"Medical return {self.fighter_recovery_date_label(fighter)} | Morale {fighter.morale} | Motivation {fighter.motivation} | "
            f"Contract {fighter.contract_months} mo | {self.title_path_label(fighter)}"
        )
        if suggestion:
            fit, build, reason, opponent = suggestion
            line_two += f"\nSUGGESTED NEXT: {opponent.name} ({self.division_rank_label(opponent)}, {opponent.record}, OVR {opponent.overall}) | Fit {fit} | Build {build} | {reason}."
        return line_one + "\n" + line_two

    def fighter_matchmaking_status(self, fighter, target_month, target_week):
        """Keep the complete roster visible while explaining why a row cannot be booked."""
        for fight in getattr(self, "booked", []):
            if fighter.name in self.event_fight_participants(fight):
                return "On draft card"
        for event in getattr(self, "scheduled_events", []):
            if any(fighter.name in self.event_fight_participants(fight) for fight in event.get("fights", [])):
                return f"Booked {self.event_date_label(event)}"
        return self.fighter_booking_status(fighter, target_month, target_week)

    def matchup_history_indicator(self, a, b):
        if not a or not b or a is b:
            return "-"
        meetings, _latest_month = self.matchup_history_summary(a, b)
        return "First meeting" if meetings == 0 else f"{meetings} prior"

    def refresh_matchmaking_history_indicators(self, _event=None):
        """Compare available opponents with the selected matchmaking anchor."""
        tree = getattr(self, "available_tree", None)
        mapping = getattr(self, "available_tree_fighters", {})
        if tree is None:
            return
        selected_ids = list(tree.selection())
        selected = [mapping[row_id] for row_id in selected_ids if row_id in mapping]
        if hasattr(self, "matchmaking_title_warning_var"):
            self.matchmaking_title_warning_var.set(self.champion_non_title_warning_text(selected))
        for row_id in tree.get_children():
            tree.set(row_id, "history", "-")
            tree.set(row_id, "fit", "-")
            status = tree.set(row_id, "status")
            fighter = mapping.get(row_id)
            if fighter is not None:
                tree.item(row_id, tags=self.available_row_tags(fighter, status))
            else:
                tree.item(row_id, tags=(() if status == "Ready" else ("not_ready",)))
        if not selected:
            if hasattr(self, "matchmaking_history_var"):
                self.matchmaking_history_var.set("Select one fighter to compare prior meetings with every possible opponent.")
            if hasattr(self, "matchmaking_brief_var"):
                self.matchmaking_brief_var.set("Select a fighter for a divisional recommendation and detailed booking context.")
            return
        if len(selected) == 1:
            anchor = selected[0]
            for row_id, opponent in mapping.items():
                tree.set(row_id, "history", self.matchup_history_indicator(anchor, opponent))
                fit = self.matchmaking_fit_score(anchor, opponent)
                if fit is not None:
                    tree.set(row_id, "fit", str(fit))
            target_date = self.selected_booking_date(reject_past=False)
            target_month, target_week = target_date if target_date else (self.month, self.week)
            suggestion = self.suggested_matchmaking_opponent(anchor, target_month, target_week)
            if suggestion:
                suggested = suggestion[3]
                suggested_row = next((row_id for row_id, fighter in mapping.items() if fighter is suggested), None)
                if suggested_row:
                    tree.set(suggested_row, "fit", f"BEST {suggestion[0]}")
                    tree.item(suggested_row, tags=("recommended",))
            self.matchmaking_history_var.set(f"OPPONENT CHECK: history is compared with {anchor.name}. First meeting means they have never fought.")
            self.matchmaking_brief_var.set(self.matchmaking_fighter_brief(anchor, suggestion))
            return
        a, b = selected[:2]
        meetings, latest_month = self.matchup_history_summary(a, b)
        indicator = self.matchup_history_indicator(a, b)
        fit = self.matchmaking_fit_score(a, b)
        for row_id in selected_ids[:2]:
            tree.set(row_id, "history", indicator)
            tree.set(row_id, "fit", str(fit or "-"))
        build = self.match_build_score(a, b, {"title": self.title_fight.get(), "main": self.main_event.get()})
        hype = self.fight_hype(a, b, {"title": self.title_fight.get(), "main": self.main_event.get(), "tier": self.card_tier.get()})
        pair_note = (
            f"MATCHUP | Fit {fit or '-'} | Build {build} | Projected hype {hype} | OVR gap {abs(a.overall - b.overall)} | "
            f"ELO gap {abs(a.elo_rating - b.elo_rating)} | {self.matchmaking_score(a, b)[1]}."
        )
        self.matchmaking_brief_var.set(self.matchmaking_fighter_brief(a) + "\n" + self.matchmaking_fighter_brief(b) + "\n" + pair_note)
        if meetings:
            last_met = f"; last met {self.format_game_date(latest_month, 1)}" if latest_month else ""
            next_meeting = self.matchup_display_name(a, b).rsplit(" ", 1)[-1]
            self.matchmaking_history_var.set(f"REMATCH {next_meeting}: {a.name} and {b.name} have {meetings} prior meeting{'s' if meetings != 1 else ''}{last_met}.")
        else:
            self.matchmaking_history_var.set(f"FIRST MEETING: {a.name} vs {b.name}.")

    def champion_non_title_warning_text(self, fighters, title_selected=None, special_belt_selected=None):
        """Explain when a belt holder is being booked without defending their championship."""
        if title_selected is None:
            title_selected = bool(self.title_fight.get()) if hasattr(self, "title_fight") else False
        divisional_holders = []
        for fighter in fighters or []:
            if not fighter:
                continue
            if getattr(fighter, "champion", False):
                divisional_holders.append(f"{fighter.name} (champion)")
            elif getattr(fighter, "interim_champion", False):
                divisional_holders.append(f"{fighter.name} (interim champion)")
        special_choice = special_belt_selected
        if special_choice is None:
            special_choice = self.special_belt_choice.get() if hasattr(self, "special_belt_choice") else "None"
        fighter_names = {fighter.name for fighter in (fighters or []) if fighter}
        undefended_special = [
            name for name, belt in self.normalize_special_belts(getattr(self, "special_belts", {})).items()
            if belt.get("holder") in fighter_names and special_choice != name
        ]
        warnings = []
        if divisional_holders and not title_selected:
            warnings.append(", ".join(divisional_holders) + " selected, but divisional Title is off; that belt will not be defended.")
        if undefended_special:
            warnings.append("Special title not selected: " + ", ".join(undefended_special) + ".")
        return "TITLE WARNING: " + " ".join(warnings) if warnings else ""

    def selected_special_belt_name(self):
        name = self.special_belt_choice.get().strip() if hasattr(self, "special_belt_choice") else ""
        return name if name and name != "None" and name in getattr(self, "special_belts", {}) else ""

    def special_belt_booking_error(self, belt_name, fighters):
        """A held special championship can only be defended by its current holder."""
        if not belt_name:
            return ""
        belt = self.normalize_special_belts(getattr(self, "special_belts", {})).get(belt_name, {})
        holder = str(belt.get("holder", "") or "")
        names = {fighter.name for fighter in (fighters or []) if fighter}
        if holder and holder not in names:
            return f"{belt_name} is held by {holder}. The holder must be included when that belt is at stake."
        return ""

    def toggle_divisional_title_booking(self):
        self.refresh_matchmaking_history_indicators()

    def select_special_belt_booking(self, _event=None):
        self.refresh_matchmaking_history_indicators()

    def refresh_special_belt_choices(self):
        if not hasattr(self, "special_belt_box"):
            return
        names = sorted(self.normalize_special_belts(getattr(self, "special_belts", {})))
        values = ["None"] + names
        self.special_belt_box.configure(values=values)
        if self.special_belt_choice.get() not in values:
            self.special_belt_choice.set("None")

    def divisional_title_is_interim(self, fighters, title_selected):
        """An interim title exists only while the primary champion is absent from the title bout."""
        fighters = [fighter for fighter in fighters if fighter]
        if not title_selected or not fighters:
            return False
        key = self.belt_key(fighters[0].gender, fighters[0].weight)
        primary_holder = self.normalize_belts(self.belts).get(key, "")
        participant_names = {fighter.name for fighter in fighters}
        return bool(primary_holder and primary_holder not in participant_names)

    def set_matchmaking_notice(self, message=""):
        if hasattr(self, "matchmaking_notice_var"):
            self.matchmaking_notice_var.set(str(message))

    def scheduled_fighter_names(self, include_booked=False):
        names = set()
        if include_booked:
            for fight in self.booked:
                names.update(name for name in self.event_fight_participants(fight) if name != "TBA")
        for event in self.scheduled_events:
            if self.is_event_due(event) or (event.get("month", 1), event.get("week", 1)) >= (self.month, self.week):
                for fight in event.get("fights", []):
                    names.update(name for name in self.event_fight_participants(fight) if name != "TBA")
        return names

    def fighter_busy_message(self, names, include_draft=False):
        busy = self.scheduled_fighter_names(include_booked=include_draft)
        conflicts = [name for name in names if name in busy]
        if conflicts:
            messagebox.showwarning("Already scheduled", f"{', '.join(conflicts)} already has a future fight scheduled. A fighter cannot be booked again until that event has been completed.")
            return True
        return False

    def refresh_card(self):
        self.refresh_special_belt_choices()
        self.card_tree.delete(*self.card_tree.get_children())
        self.normalize_card_order()
        for index, fight in enumerate(self.booked, 1):
            if fight.get("tournament"):
                entrants = fight.get("tournament_entrants", [])
                tournament_fighters = [self.get_fighter(name) for name in entrants if name != "TBA"]
                divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
                non_title_warning = self.champion_non_title_warning_text(tournament_fighters, divisional_title, fight.get("special_belt", ""))
                slot = "Main Tournament" if fight.get("main") else "Tournament"
                if fight.get("special_belt"):
                    slot = f"{fight['special_belt']} Tournament"
                    if divisional_title:
                        slot += " + Interim" if fight.get("interim") else " + Div Title"
                elif fight.get("title"):
                    slot = "Title " + slot
                elif non_title_warning:
                    slot = "NON-TITLE CHAMP"
                if non_title_warning and fight.get("special_belt"):
                    slot += " / DIV TITLE OFF"
                field = ", ".join(entrants[:3]) + (f" +{len(entrants) - 3}" if len(entrants) > 3 else "")
                avg_hype = round(sum(self.fight_build_score(self.get_fighter(name)) for name in entrants if name != "TBA") / max(1, len([name for name in entrants if name != "TBA"])))
                avg_fatigue = round(sum(fighter.fatigue for fighter in tournament_fighters) / max(1, len(tournament_fighters)))
                recovery = "All clear" if all(self.fighter_recovery_date_label(fighter) == "Now" for fighter in tournament_fighters) else "Mixed"
                tags = ("non_title_champion",) if non_title_warning else ()
                self.card_tree.insert("", "end", iid=str(index - 1), tags=tags, values=(slot, f"{fight.get('tournament_name', 'MMA Grand Prix')} [{field}]", fight.get("tournament_weight", ""), avg_hype, "Bracket", f"Avg {avg_fatigue}", recovery))
                continue
            if fight.get("special_belt"):
                slot = f"{fight['special_belt']} Title"
                if fight.get("divisional_title", False):
                    slot += " + Interim" if fight.get("interim") else " + Div Title"
            elif fight.get("main") and fight.get("interim"):
                slot = "Main Interim"
            elif fight.get("main") and fight.get("title"):
                slot = "Main Title"
            elif fight.get("main"):
                slot = "Main"
            elif fight.get("interim"):
                slot = "Interim"
            elif fight.get("title"):
                slot = "Title"
            else:
                slot = fight.get("tier", f"Fight {index}")
            named_fighters = [self.get_fighter(name) for name in fight.get("fighters", []) if name != "TBA"]
            divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            non_title_warning = self.champion_non_title_warning_text(named_fighters, divisional_title, fight.get("special_belt", ""))
            if non_title_warning:
                slot = f"{slot} / DIV TITLE OFF" if fight.get("special_belt") else "NON-TITLE CHAMP"
            if "TBA" in fight["fighters"]:
                known = self.get_fighter(next(name for name in fight["fighters"] if name != "TBA"))
                tba_label = f"TBA {fight.get('tba_gender', known.gender)} {fight.get('tba_weight', known.weight)}"
                self.card_tree.insert("", "end", iid=str(index - 1), tags=(("non_title_champion",) if non_title_warning else ()), values=(slot, f"{known.name} vs {tba_label}", known.weight, self.fight_build_score(known), "TBA", f"{known.fatigue} / -", f"{self.fighter_recovery_date_label(known)} / -"))
            else:
                a, b = [self.get_fighter(name) for name in fight["fighters"]]
                self.card_tree.insert("", "end", iid=str(index - 1), tags=(("non_title_champion",) if non_title_warning else ()), values=(slot, f"{a.name} vs {b.name}", a.weight, self.fight_hype(a, b, fight), self.match_build_score(a, b, fight), f"{a.fatigue} / {b.fatigue}", f"{self.fighter_recovery_date_label(a)} / {self.fighter_recovery_date_label(b)}"))
        if hasattr(self, "event_name") and not getattr(self, "spectator_mode", False):
            current = self.event_name.get()
            prefix, number = self.event_name_parts(current)
            foreign_auto = number is not None and prefix in self.known_promotion_names() and prefix != self.player_company_name
            if foreign_auto or (self.booked and self.is_auto_event_name(current)):
                self.event_name.set(self.default_event_name())
        self.refresh_event_atmosphere_forecast()

    def event_date_label(self, event):
        # Cards booked before bookings carried a weekday show the date they
        # were always shown with, rather than a day nobody picked.
        day = self.event_day(event) if isinstance(event, dict) and event.get("day") is not None else None
        return self.format_game_date(event.get("month", self.month), event.get("week", 1), day=day)

    def sync_booking_internal_date(self):
        """Translate the calendar controls into the save-stable month index."""
        if not hasattr(self, "event_calendar_month") or not hasattr(self, "event_year"):
            return
        try:
            calendar_month = CALENDAR_MONTH_ABBREVIATIONS.index(self.event_calendar_month.get()) + 1
            self.event_month.set(self.calendar_month_index(int(self.event_year.get()), calendar_month))
        except (ValueError, tk.TclError):
            return

    def set_booking_date(self, month, week):
        """Update both the visible calendar controls and internal event date."""
        month = max(1, int(month))
        week = max(1, min(4, int(week)))
        self.event_month.set(month)
        self.event_week.set(week)
        if hasattr(self, "event_calendar_month") and hasattr(self, "event_year"):
            year, calendar_month, _week = self.calendar_parts(month, week)
            self.event_calendar_month.set(CALENDAR_MONTH_ABBREVIATIONS[calendar_month - 1])
            self.event_year.set(year)

    def selected_booking_day(self):
        """The weekday chosen for the card, defaulting to the weekend."""
        if not hasattr(self, "event_day_choice"):
            return DEFAULT_EVENT_DAY
        try:
            return CALENDAR_DAYS.index(self.event_day_choice.get()) + 1
        except (ValueError, tk.TclError):
            return DEFAULT_EVENT_DAY

    def selected_booking_date(self, reject_past=False):
        """Return the chosen date, rejecting a past calendar selection when asked."""
        self.sync_booking_internal_date()
        month = int(self.event_month.get()) if hasattr(self, "event_month") else self.month
        week = max(1, min(4, int(self.event_week.get()))) if hasattr(self, "event_week") else self.week
        if reject_past and (month, week) < (self.month, self.week):
            messagebox.showwarning("Past date", f"Choose {self.format_game_date(self.month, self.week)} or a later date. Events cannot be scheduled in the past.")
            return None
        return month, week

    def next_player_event_number(self):
        """Continue the promotion's public card sequence without duplicates."""
        pattern = re.compile(rf"^{re.escape(self.player_company_name)}\s+(\d+)(?::|\s|$)")
        labels = [event.get("name", "") for event in self.scheduled_events]
        labels.extend(str(item) for item in self.result_history)
        labels.extend(
            record.get("event", "")
            for record in getattr(self, "result_records", [])
            if record.get("company") == self.player_company_name
        )
        labels.extend(
            package.get("event_name", package.get("name", ""))
            for package in getattr(self, "player_event_archive", [])
            if package.get("company", self.player_company_name) == self.player_company_name
        )
        used = [int(match.group(1)) for label in labels if (match := pattern.match(str(label).strip()))]
        return max(used, default=0) + 1

    def main_event_name_from_card(self, fights=None):
        fights = self.booked if fights is None else fights
        if not fights:
            return "Main Event"
        self.normalize_card_order(fights)
        # Card order is intentional: the first row is the advertised main event.
        main = fights[0]
        if main.get("tournament"):
            return main.get("tournament_name", "MMA Grand Prix")
        names = main.get("fighters", [])
        if len(names) != 2:
            return "Main Event"
        if "TBA" in names:
            return f"{names[0]} vs {names[1]}"
        a, b = (self.get_fighter(name) for name in names)
        return self.matchup_display_name(a, b) if a and b else f"{names[0]} vs {names[1]}"

    def default_event_name(self, number=None, fights=None):
        number = number or self.next_player_event_number()
        return f"{self.player_company_name} {number}: {self.main_event_name_from_card(fights)}"

    def ensure_player_event_name(self):
        """Keep the matchmaking event-name field pointed at the player's promotion.

        The field is a transient StringVar that is not saved, so after loading a
        game or switching promotions it can still show a stale auto-name from
        another company (for example "BAMMA 1" while the player runs Kebab
        Fighting Championship). Regenerate it whenever it is blank or holds an
        auto-name, but never overwrite a name the player typed themselves or the
        spectator placeholder."""
        if not hasattr(self, "event_name"):
            return
        if getattr(self, "spectator_mode", False):
            return
        current = self.event_name.get().strip()
        if not current or self.is_auto_event_name(current):
            self.event_name.set(self.default_event_name())

    def event_name_parts(self, value):
        """Return the promotion prefix and sequence number for a numbered show name."""
        match = re.match(r"^(.+?)\s+(\d+)(?::|\s|$)", str(value or "").strip())
        return (match.group(1).strip(), int(match.group(2))) if match else (None, None)

    def event_name_number(self, value):
        return self.event_name_parts(value)[1]

    def known_promotion_names(self):
        names = {self.player_company_name}
        names.update(getattr(promotion, "name", "") for promotion in getattr(self, "promotions", []))
        return {name for name in names if name}

    def is_auto_event_name(self, value):
        value = (value or "").strip()
        if not value:
            return True
        prefix, number = self.event_name_parts(value)
        return number is not None and prefix in self.known_promotion_names()

    def refresh_scheduled_event_auto_name(self, event):
        """Keep a generated event name attached to the card's first/main bout."""
        fights = event.get("fights", [])
        self.normalize_card_order(fights)
        current = str(event.get("name", "")).strip()
        prefix, number = self.event_name_parts(current)
        auto_named = event.get("auto_named")
        if not fights or auto_named is False:
            return
        if auto_named is True or (number is not None and prefix in self.known_promotion_names()):
            event["auto_named"] = True
            event["name"] = self.default_event_name(number or self.next_player_event_number(), fights)

    def repair_scheduled_event_names(self):
        """Migrate generated card names after a player changes or creates a promotion."""
        for event in self.scheduled_events:
            self.refresh_scheduled_event_auto_name(event)

    def sorted_scheduled_events(self):
        return sorted(self.scheduled_events, key=lambda show: (show.get("month", 1), show.get("week", 1), show.get("name", "")))

    def is_event_due(self, event):
        return (event.get("month", 1), event.get("week", 1)) <= (self.month, self.week)

    def refresh_upcoming(self):
        self.repair_scheduled_event_names()
        # Do not leave the matchmaker pointed at an already-passed calendar
        # date after the player advances the world. Future selections remain
        # untouched, but stale ones reset to the current playable week.
        if hasattr(self, "event_month"):
            selected = self.selected_booking_date(reject_past=False)
            if selected and selected < (self.month, self.week):
                self.set_booking_date(self.month, self.week)
        if hasattr(self, "event_broadcaster_box"):
            names = ["No Coverage"] + [item["name"] for item in self.broadcasters]
            self.event_broadcaster_box.configure(values=names)
            if self.event_broadcaster.get() not in names:
                self.event_broadcaster.set("No Coverage")
            self.refresh_event_broadcaster_status()
            self.refresh_event_atmosphere_forecast()
        self.upcoming_tree.delete(*self.upcoming_tree.get_children())
        for index, event in enumerate(self.sorted_scheduled_events()):
            self.refresh_scheduled_event_auto_name(event)
            status = "Due" if self.is_event_due(event) else "Scheduled"
            place = f"{event.get('city','')}, {event.get('region', self.venue_region(event['venue']))}".strip(", ")
            self.upcoming_tree.insert("", "end", iid=str(index), values=(self.event_date_label(event), event["name"], event["venue"], place, len(event["fights"]), status))

    def refresh_event_broadcaster_status(self, _event=None):
        if not hasattr(self, "event_broadcaster_status"):
            return
        name = self.event_broadcaster.get() if hasattr(self, "event_broadcaster") else "No Coverage"
        provider = next((item for item in self.broadcasters if item["name"] == name), None)
        rights = self.finance.get("media_rights", {})
        rights_events = rights.get("events_remaining", 0)
        if provider:
            text = f"Provider: {provider['name']} ({provider.get('type', 'Broadcast')}) | Reach {provider['reach']} | Production fee ${provider['fee']:,}."
        else:
            text = "No event provider selected: exposure and broadcast income will be sharply reduced."
        if rights.get("reach", 0) and rights_events != 0:
            text += f" Active rights: {rights['name']} (+{rights['reach']} reach, {rights_events if rights_events > 0 else 'unlimited'} event(s) remaining)."
        self.event_broadcaster_status.config(text=text)

    def refresh_event_atmosphere_forecast(self, _event=None):
        if not hasattr(self, "event_atmosphere_status"):
            return
        region = self.event_region.get() if hasattr(self, "event_region") else self.player_region
        forecast = self.event_atmosphere({"region": region, "fights": list(getattr(self, "booked", []))})
        self.event_atmosphere_status.config(text=f"Atmosphere forecast: {forecast['mood']} {forecast['intensity']}/100 | {forecast['identity']} | Crowd wants {forecast['preference']}. Home connections: {forecast['local_fighters']} ({forecast.get('hometown_fighters', 0)} hometown), pull {forecast.get('home_pull', 0):.1f}.")

    def open_fanbase_window(self):
        fanbase = getattr(self, "fanbase", {}) or {}
        window = tk.Toplevel(self.root)
        window.title("Fanbase & Atmosphere")
        window.geometry("860x560")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="FANBASE & ATMOSPHERE", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text=f"Identity: {fanbase.get('identity', 'Regional Fight Community')}", style="Chrome.TLabel").pack(side="right", padx=10)
        summary = tk.Frame(window, bg=self.colors["panel"]); summary.pack(fill="x", padx=8, pady=8)
        for index, (label, value) in enumerate((("Core Support", fanbase.get("core_support", 42)), ("Casual Reach", fanbase.get("casual_reach", 30)), ("Home Region", fanbase.get("home_region", self.player_region)), ("Recent Events", len(fanbase.get("event_history", []))))):
            self.profile_info_row(summary, label, value, index)
        tree = ttk.Treeview(window, columns=("region", "identity", "preference", "love", "forecast"), show="headings")
        for column, label, width in (("region", "Region", 90), ("identity", "Crowd Identity", 185), ("preference", "Crowd Preference", 190), ("love", "MMA Love", 80), ("forecast", "Current Forecast", 150)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        for region in REGIONS:
            data = self.regions.get(region, {})
            forecast = self.event_atmosphere({"region": region, "fights": []})
            tree.insert("", "end", iid=region, values=(region, data.get("fan_identity", "Local MMA community"), data.get("crowd_preference", "Competitive fights"), f"{data.get('mma_love', 50)}%", f"{forecast['mood']} {forecast['intensity']}/100"))
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        history = tk.Text(window, height=5, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        history.pack(fill="x", padx=8, pady=(0, 8))
        events = fanbase.get("event_history", [])
        history.insert("end", "RECENT CROWD MEMORIES\n" + ("\n".join(f"{self.format_game_date(item.get('month', self.month), item.get('week', 1), include_week=False)}: {item.get('event', 'Event')} — {item.get('mood', 'Engaged')} {item.get('intensity', 50)}/100, attendance {item.get('attendance', 0):,}." for item in events[:5]) or "No player events have created fanbase memories yet."))
        history.config(state="disabled")

    def refresh_market(self):
        self.ensure_free_agent_depth()
        self.market_tree.delete(*self.market_tree.get_children())
        self.market_tree_fighters = {}
        age_min, age_max = self.filter_range("market_age_min", "market_age_max", 16, 60)
        ovr_min, ovr_max = self.filter_range("market_ovr_min", "market_ovr_max", 0, 100)
        pop_min = self.filter_value("market_pop_min", 0, 0, 100)
        potential_min = self.filter_value("market_potential_min", 0, 0, 100)
        market_status = self.market_status_filter.get() if hasattr(self, "market_status_filter") else "All"
        query = self.market_search.get().strip() if hasattr(self, "market_search") else ""
        scouting_on = bool(self.rules.get("scouting_mode", False))

        def report_value(fighter, field):
            if not scouting_on:
                return int(getattr(fighter, field))
            estimate = self.scouting_estimate(fighter, field)
            return int(estimate.get("mid")) if isinstance(estimate, dict) and estimate.get("mid") is not None else None

        def market_sort_key(fighter):
            projected = report_value(fighter, "overall")
            potential = report_value(fighter, "potential")
            fights = max(1, fighter.record_w + fighter.record_l + fighter.record_d)
            public_merit = (fighter.record_w - fighter.record_l) / fights
            return (projected is None, -(projected or 0), -(potential or 0), -public_merit, fighter.age, fighter.name)

        for row_index, fighter in enumerate(sorted(self.free_agents, key=market_sort_key)):
            if self.market_weight_filter.get() != "All" and fighter.weight != self.market_weight_filter.get():
                continue
            if self.market_gender_filter.get() != "All" and fighter.gender != self.market_gender_filter.get():
                continue
            if query and not self.fighter_matches_text_filter(fighter, query):
                continue
            has_offer = bool(getattr(fighter, "ai_offer_company", ""))
            if market_status == "Available" and (has_offer or getattr(fighter, "retirement_pending", False)):
                continue
            if market_status == "Rival Offer" and not has_offer:
                continue
            if market_status == "Retiring" and not getattr(fighter, "retirement_pending", False):
                continue
            if not age_min <= fighter.age <= age_max:
                continue
            projected_ovr = report_value(fighter, "overall")
            projected_pop = report_value(fighter, "popularity")
            projected_potential = report_value(fighter, "potential")
            active_private_filter = (ovr_min > 0 or ovr_max < 100 or pop_min > 0 or potential_min > 0)
            if active_private_filter and scouting_on and None in (projected_ovr, projected_pop, projected_potential):
                continue
            if projected_ovr is not None and not ovr_min <= projected_ovr <= ovr_max:
                continue
            if projected_pop is not None and projected_pop < pop_min:
                continue
            if projected_potential is not None and projected_potential < potential_min:
                continue
            offer = ""
            if getattr(fighter, "ai_offer_company", ""):
                offer = f"{fighter.ai_offer_company}: ${fighter.ai_offer_purse:,}"
            report = self.scouting_report_for(fighter)
            in_closed_division = self.belt_key(fighter.gender, fighter.weight) in set(getattr(self, "closed_divisions", set()))
            reveal = self.scouting_effective_confidence(report) if scouting_on and report else (0 if scouting_on else 100)
            if in_closed_division:
                tag = "DIVISION CLOSED"
            elif not scouting_on:
                tag = "BLUE CHIP" if self.is_blue_chip_prospect(fighter) else ""
            elif report.get("status") == "In progress":
                tag = f"{report.get('kind', 'report').upper()} {report.get('weeks_remaining', 0)}W"
            elif report.get("reveal", 0) >= 100:
                tag = "FULL" if self.scouting_report_is_current_full(report) else "STALE"
            elif report:
                tag = f"SCOUT {reveal}%"
            else:
                tag = "UNSCOUTED"

            def known(field, threshold, public_value=None):
                if not scouting_on:
                    return getattr(fighter, field) if public_value is None else public_value
                if report.get("status") != "Complete" or reveal < threshold:
                    return "?"
                estimate = self.scouting_estimate(fighter, field)
                if not isinstance(estimate, dict):
                    return public_value if public_value is not None else "?"
                return estimate.get("mid") if estimate.get("low") == estimate.get("high") else f"{estimate.get('low')}-{estimate.get('high')}"
            row_id = self.fighter_tree_row_id("market", fighter, row_index)
            self.market_tree_fighters[row_id] = fighter
            style = fighter.style if (not scouting_on or (report.get("status") == "Complete" and reveal >= 25)) else "?"
            self.market_tree.insert("", "end", iid=row_id, tags=("closed_division",) if in_closed_division else (), values=(fighter.name, tag, fighter.gender[0], fighter.weight, fighter.record, fighter.age, known("overall", 35), known("popularity", 35), known("star_quality", 55), known("media_presence", 55), known("professionalism", 50), style, f"${fighter.purse:,}", offer))
        self.refresh_market_scout_panel()

    def reset_market_filters(self):
        self.market_search.set("")
        self.market_weight_filter.set("All")
        self.market_gender_filter.set("All")
        self.market_status_filter.set("All")
        self.market_age_min.set(16)
        self.market_age_max.set(60)
        self.market_ovr_min.set(0)
        self.market_ovr_max.set(100)
        self.market_pop_min.set(0)
        self.market_potential_min.set(0)
        self.refresh_market()

    def market_scout_summary(self, fighter):
        report = self.scouting_report_for(fighter)
        scouting_on = bool(self.rules.get("scouting_mode", False))
        reveal = self.scouting_effective_confidence(report) if scouting_on and report else (0 if scouting_on else 100)
        confidence = f"{reveal}% confidence" if self.rules.get("scouting_mode", False) else "Full public info"
        division_closed = self.belt_key(fighter.gender, fighter.weight) in set(getattr(self, "closed_divisions", set()))
        eligibility = "Eligible to sign into an active division."
        if division_closed:
            eligibility = (
                f"DIVISION CLOSED: Your promotion does not currently operate {fighter.gender} "
                f"{fighter.weight}. You may still sign them; they will remain visible on your roster, "
                "but must move to an active division or have this division reopened before being booked."
            )
        projected_ovr = (self.scouting_estimate(fighter, "overall", {}) or {}).get("mid")
        projected_potential = (self.scouting_estimate(fighter, "potential", {}) or {}).get("mid")
        projected_pop = (self.scouting_estimate(fighter, "popularity", {}) or {}).get("mid")
        projected_star = (self.scouting_estimate(fighter, "star_quality", {}) or {}).get("mid")
        if not scouting_on:
            projected_ovr, projected_potential = fighter.overall, fighter.potential
            projected_pop, projected_star = fighter.popularity, fighter.star_quality
        if reveal < 35:
            grade = "Blind look"
            recommendation = "Run a basic dossier before spending serious money."
        elif projected_ovr is None:
            grade = "Incomplete report"
            recommendation = "Wait for the assigned scout to complete the report."
        elif projected_potential is not None and projected_potential >= projected_ovr + 12 and fighter.age <= 27:
            grade = "Development target"
            recommendation = "Good academy/gym upside if the asking price is sane."
        elif projected_pop is not None and projected_star is not None and projected_pop + projected_star >= 135:
            grade = "Marketable signing"
            recommendation = "Useful for ticket/media growth, especially on regional cards."
        elif projected_ovr >= 76:
            grade = "Competitive signing"
            recommendation = "Can help main cards now; watch purse pressure."
        else:
            grade = "Depth option"
            recommendation = "Use only if the division needs bodies or a cheap local draw."
        offer = "No known rival offer."
        if getattr(fighter, "ai_offer_company", ""):
            offer = f"Rival offer: {fighter.ai_offer_company} at ${fighter.ai_offer_purse:,}. Move quickly or raise your terms."
        notes = list(report.get("notes", []))
        if not notes and reveal < 35:
            notes = ["Not enough reliable information yet."]
        elif not notes:
            notes = ["Public data only; scout report can sharpen the read."]
        hidden = ""
        if self.rules.get("scouting_mode", False) and reveal < 100:
            hidden = "\nHidden: exact OVR/popularity/star/media/professionalism may still be off."
        return (
            f"{fighter.name}\n"
            f"{fighter.gender} {fighter.weight} | Age {fighter.age} | {fighter.region}\n"
            f"Record {fighter.record} | Style {fighter.style if reveal >= 25 or reveal == 100 else 'Unknown'}\n"
            f"Eligibility: {eligibility}\n\n"
            f"Report: {report.get('kind', 'none').title() if report else 'None'} | {confidence}\n"
            f"Scout: {report.get('scout', 'No assigned scout')}\n"
            f"Read: {grade}\n"
            f"Asking: ${fighter.purse:,} | {offer}\n\n"
            f"Notes:\n- " + "\n- ".join(notes) +
            f"\n\nRecommendation: {recommendation}{hidden}"
        )

    def refresh_market_scout_panel(self):
        if not hasattr(self, "market_scout_text"):
            return
        selected = self.market_tree.selection() if hasattr(self, "market_tree") else []
        self.market_scout_text.config(state="normal")
        self.market_scout_text.delete("1.0", "end")
        if not selected:
            self.market_scout_text.insert("end", "Select a free agent to see scouting confidence, risk, and action advice.")
        else:
            fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
            self.market_scout_text.insert("end", self.market_scout_summary(fighter) if fighter else "This fighter is no longer on the market.")
        self.market_scout_text.config(state="disabled")

    def open_game_settings_window(self):
        """Persistent gameplay settings for player information and AI market pace."""
        window = tk.Toplevel(self.root)
        window.title("Game Settings")
        window.geometry("620x650")
        window.minsize(550, 560)
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="GAME SETTINGS", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=7)
        panel, body = self.section(window, "MARKET INFORMATION")
        panel.pack(fill="both", expand=True, padx=8, pady=8)
        scouting_var = tk.BooleanVar(value=bool(self.rules.get("scouting_mode", True)))
        ttk.Checkbutton(body, text="Require scouting reports for free-agent ratings", variable=scouting_var).pack(anchor="w", padx=12, pady=(14, 8))
        explanation = (
            "On: the Free Agents list hides exact OVR, popularity, style and business traits until your scout reports on the fighter. "
            "Off: those details are treated as public information.\n\n"
            "This is saved with the game and stays in effect after reload."
        )
        ttk.Label(body, text=explanation, style="Inset.TLabel", wraplength=510, justify="left").pack(anchor="w", padx=12, pady=4)
        market_row = ttk.Frame(body, style="Inset.TFrame")
        market_row.pack(fill="x", padx=12, pady=(12, 2))
        ttk.Label(market_row, text="AI market offer target", style="Inset.TLabel").pack(side="left", padx=(8, 6), pady=6)
        offer_target_var = tk.IntVar(value=int(self.rules.get("ai_offer_market_target", 100)))
        ttk.Spinbox(market_row, from_=20, to=180, increment=5, textvariable=offer_target_var, width=7).pack(side="left", pady=6)
        ttk.Label(market_row, text="offers per month", style="Inset.TLabel").pack(side="left", padx=6, pady=6)
        market_explanation = (
            "This sets the AI's market pace across every promotion. Higher values create more competing contract offers and faster roster repair; "
            "lower values create a quieter market. Cash reserves, roster caps, division needs, fighter choices, and monthly volatility still apply."
        )
        ttk.Label(body, text=market_explanation, style="Inset.TLabel", wraplength=510, justify="left").pack(anchor="w", padx=12, pady=(2, 4))
        replay_row = ttk.Frame(body, style="Inset.TFrame")
        replay_row.pack(fill="x", padx=12, pady=(10, 2))
        ttk.Label(replay_row, text="Global full replay limit", style="Inset.TLabel").pack(side="left", padx=(8, 6), pady=6)
        replay_limit_var = tk.IntVar(value=int(self.rules.get("global_result_replay_limit", GLOBAL_RESULT_REPLAY_LIMIT)))
        ttk.Entry(replay_row, textvariable=replay_limit_var, width=10).pack(side="left", pady=6)
        ttk.Label(replay_row, text="cards", style="Inset.TLabel").pack(side="left", padx=6, pady=6)
        ttk.Label(body, text="Older cards still keep compact results and scorecards permanently; this only controls how many global cards keep full watchable play-by-play. Use 0 for compact history only.", style="Inset.TLabel", wraplength=510, justify="left").pack(anchor="w", padx=12, pady=(2, 4))
        audio_separator = ttk.Separator(body, orient="horizontal")
        audio_separator.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(body, text="FIGHT NIGHT AUDIO", style="Section.TLabel").pack(anchor="w", padx=12, pady=(2, 4))
        self.ensure_audio_defaults()
        audio_enabled_var = tk.BooleanVar(value=bool(self.rules.get("fight_night_audio_enabled", True)))
        ttk.Checkbutton(body, text="Play fight-night sound cues", variable=audio_enabled_var).pack(anchor="w", padx=12, pady=(3, 6))
        audio_labels = [self.AUDIO_DEFAULT]
        selected_output = str(self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT))
        if selected_output not in audio_labels:
            selected_output = self.AUDIO_DEFAULT
        audio_output_var = tk.StringVar(value=selected_output)
        audio_volume_var = tk.IntVar(value=int(self.rules.get("fight_night_audio_volume", 55)))
        audio_row = ttk.Frame(body, style="Inset.TFrame")
        audio_row.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Label(audio_row, text="Output", style="Inset.TLabel").pack(side="left", padx=(8, 6), pady=6)
        audio_output_box = ttk.Combobox(audio_row, state="readonly", values=audio_labels, textvariable=audio_output_var, width=37)
        audio_output_box.pack(side="left", fill="x", expand=True, pady=6)

        def refresh_audio_outputs(_event=None):
            labels = [label for label, _index in self.available_fight_night_outputs()]
            audio_output_box.configure(values=labels)
            if audio_output_var.get() not in labels:
                audio_output_var.set(self.AUDIO_DEFAULT)

        audio_output_box.bind("<Button-1>", refresh_audio_outputs)
        volume_row = ttk.Frame(body, style="Inset.TFrame")
        volume_row.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Label(volume_row, text="Cue volume", style="Inset.TLabel").pack(side="left", padx=(8, 6), pady=6)
        ttk.Scale(volume_row, from_=0, to=100, variable=audio_volume_var, orient="horizontal").pack(side="left", fill="x", expand=True, pady=6)
        ttk.Label(volume_row, textvariable=audio_volume_var, style="Inset.TLabel", width=4).pack(side="left", padx=(6, 8))
        audio_note = "Bell, impact, knockdown, finish, decision, and card-complete cues play only while watching a live card. Audio uses the selected Windows output and never slows the simulation."
        ttk.Label(body, text=audio_note, style="Inset.TLabel", wraplength=540, justify="left").pack(anchor="w", padx=12, pady=(0, 4))

        def preview_audio():
            self.rules["fight_night_audio_enabled"] = bool(audio_enabled_var.get())
            self.rules["fight_night_audio_output"] = audio_output_var.get()
            self.rules["fight_night_audio_volume"] = max(0, min(100, int(audio_volume_var.get())))
            self.play_fight_night_sound("preview")

        ttk.Button(body, text="Test Selected Output", command=preview_audio).pack(anchor="w", padx=12, pady=(0, 4))
        footer = ttk.Frame(body, style="Inset.TFrame")
        footer.pack(fill="x", padx=12, pady=(12, 10))
        def apply():
            self.toggle_scouting_mode(scouting_var.get())
            try:
                target = int(offer_target_var.get())
            except (tk.TclError, ValueError):
                target = 100
            self.rules["ai_offer_market_target"] = max(20, min(180, target))
            try:
                replay_limit = int(replay_limit_var.get())
            except (tk.TclError, ValueError):
                replay_limit = GLOBAL_RESULT_REPLAY_LIMIT
            self.rules["global_result_replay_limit"] = max(0, replay_limit)
            self.rules["fight_night_audio_enabled"] = bool(audio_enabled_var.get())
            self.rules["fight_night_audio_output"] = audio_output_var.get()
            self.rules["fight_night_audio_volume"] = max(0, min(100, int(audio_volume_var.get())))
            window.destroy()
        ttk.Button(footer, text="Apply", style="Accent.TButton", command=apply).pack(side="left")
        ttk.Button(footer, text="Cancel", command=window.destroy).pack(side="right")

    def toggle_scouting_mode(self, enabled=None):
        self.rules["scouting_mode"] = bool(self.scouting_mode_var.get()) if enabled is None and hasattr(self, "scouting_mode_var") else bool(enabled)
        self.refresh_market()

    def start_selected_scout_report(self, kind):
        selected = self.market_tree.selection()
        if not selected:
            messagebox.showinfo("Scouting", "Select a free agent first.")
            return
        fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
        if not fighter:
            return
        self.start_scout_report_for_fighter(fighter, kind)

    def start_scout_report_for_fighter(self, fighter, kind, scout_name=None, automatic=False):
        """Assign a real scout (or paid contractor) to a stable fighter report."""
        if getattr(fighter, "retired", False):
            messagebox.showinfo("Scouting", "Retired fighters do not need a live scouting report.")
            return False
        self.migrate_scouting_state()
        existing = self.scouting_report_for(fighter)
        if existing.get("reveal", 0) >= 100 and self.scouting_report_is_current_full(existing):
            messagebox.showinfo("Scouting", f"A full report on {fighter.name} is already available.")
            return False
        if existing.get("status") == "In progress":
            messagebox.showinfo("Scouting", f"{existing.get('kind', 'A')} report on {fighter.name} is already in progress.")
            return False
        scouts = [staff for staff in self.staff if staff.get("role") == "Scout"]
        if scout_name:
            scout = next((staff for staff in scouts if staff.get("name") == scout_name), None)
            if not scout:
                messagebox.showinfo("Scouting", "That scout is no longer employed.")
                return False
        else:
            available = [staff for staff in scouts if self.scout_workload(staff.get("name")) < self.scout_capacity(staff)]
            scout = max(
                available,
                key=lambda staff: (
                    staff.get("fighter_judging", staff.get("skill", 45)) * 0.46
                    + staff.get("potential_judging", staff.get("skill", 45)) * 0.24
                    + staff.get("efficiency", staff.get("skill", 45)) * 0.15
                    + staff.get("reliability", staff.get("skill", 45)) * 0.15
                    + (8 if fighter.region == self.player_region else 0)
                    + (7 if staff.get("specialty") == "Prospect eye" and fighter.age <= 27 else 0)
                    + (7 if staff.get("specialty") == "Women’s divisions" and fighter.gender == "Female" else 0)
                    + (6 if staff.get("specialty") == "International network" and fighter.region != self.player_region else 0)
                ),
                default=None,
            )
        independent = scout is None
        if independent:
            if any(report.get("status") == "In progress" and report.get("scout") == "Independent Contractor" for report in self.scouting_reports.values()):
                messagebox.showinfo("Scouting", "Your independent contractor is already handling another report. Hire a Scout for more capacity.")
                return False
            scout = {"name": "Independent Contractor", "skill": 42, "fighter_judging": 42, "potential_judging": 38, "efficiency": 35, "regional_knowledge": 35, "networking": 35, "reliability": 40, "professionalism": 50}
        elif self.scout_workload(scout.get("name")) >= self.scout_capacity(scout):
            messagebox.showinfo("Scouting", f"{scout.get('name')} has no free assignment slots.")
            return False
        home_bonus = 8 if fighter.region == self.player_region else 0
        judging = (scout.get("fighter_judging", scout.get("skill", 45)) + scout.get("potential_judging", scout.get("skill", 45)) + scout.get("reliability", 45) + scout.get("professionalism", 45)) / 4
        efficiency = scout.get("efficiency", scout.get("skill", 45))
        market_edge = (scout.get("regional_knowledge", 45) - 50) * 0.18 + (scout.get("networking", 45) - 50) * 0.12 + home_bonus
        confidence = max(30, min(94, round(judging * 0.88 + market_edge + random.randint(-7, 7))))
        if scout.get("specialty") == "Prospect eye" and fighter.age <= 27:
            confidence = min(96, confidence + 5)
        elif scout.get("specialty") == "Women’s divisions" and fighter.gender == "Female":
            confidence = min(96, confidence + 6)
        elif scout.get("specialty") == "International network" and fighter.region != self.player_region:
            confidence = min(96, confidence + 4)
        self.scouting_reports = getattr(self, "scouting_reports", {})
        base_weeks = {"basic": 2, "full": 6, "observation": 26}.get(kind, 2)
        weeks = base_weeks if kind == "observation" else max(1, base_weeks - int(efficiency >= 80))
        cost = 0 if automatic else {"basic": 2500, "full": 7500, "observation": 4000}.get(kind, 2500)
        if fighter.region != self.player_region:
            cost = round(cost * 1.35)
        if independent:
            cost = round(cost * 1.5)
            if kind != "observation":
                weeks += 1
        if self.cash < cost:
            messagebox.showinfo("Scouting", f"This assignment needs ${cost:,}.")
            return False
        notes = []
        if automatic:
            notes.append("Proactively selected by an idle staff scout from public market information.")
        if confidence >= 35:
            notes.append("Strong striking base" if fighter.striking >= fighter.wrestling else "Reliable wrestling base")
        if confidence >= 50:
            notes.append("High upside" if fighter.potential >= fighter.overall + 12 else "Limited upside")
        if confidence >= 65:
            notes.append("Durable and well-conditioned" if fighter.cardio + fighter.chin >= 145 else "Conditioning or durability concern")
        if confidence >= 80:
            notes.append("Professional preparation" if fighter.professionalism >= 70 else "Preparation consistency concern")
        key = self.scouting_report_key(fighter)
        self.scouting_reports[key] = {"schema_version": 2, "fighter_id": key, "fighter_name": fighter.name, "kind": kind, "status": "In progress", "started_week": self.calendar_week_index(), "weeks_remaining": weeks, "confidence": confidence, "reveal": 0, "scout": scout.get("name"), "region": fighter.region, "notes": notes, "cost": cost, "automatic": bool(automatic), "estimates": self.build_scouting_estimates(fighter, scout, kind, confidence), "prior_kind": existing.get("kind", ""), "prior_confidence": self.scouting_effective_confidence(existing) if existing else 0, "prior_notes": list(existing.get("notes", [])) if existing else []}
        if cost:
            self.cash -= cost
            self.record_finance_transaction(f"Scouting: {fighter.name} ({kind})", costs=cost)
        cost_text = f" Cost ${cost:,}." if cost else " Routine staff assignment; no additional fee."
        assignment_text = f"{scout.get('name')} began {'an observation assignment' if kind == 'observation' else f'a {kind} report'} on {fighter.name}.{cost_text}"
        self.scouting.append(assignment_text)
        if not automatic:
            self.inbox.append({"subject": f"Scouting Assignment - {fighter.name}", "body": assignment_text + (" The report completes after their next fight." if kind == "observation" else f" Due in {weeks} week(s)."), "type": "Scouting", "resolved": True, "fighter_id": key})
            self.refresh_market()
            self.refresh_world_fighter_search()
            self.refresh_staff()
        return True

    def ensure_free_agent_depth(self, minimum=None, emergency=False):
        active_free_agents = lambda: sum(not fighter.retired for fighter in self.free_agents)
        regional_additions = 0
        if minimum is None:
            # Opening depth is seeded once. Afterwards the regional pathway is
            # the main source; direct entrants only prevent a genuine collapse.
            if self.month <= 1:
                minimum = 260
            elif emergency:
                # A hard safety floor prevents a mature universe from running
                # out of negotiable talent. It is deliberately dormant at 160+
                # so the normal regional, release and retirement flows remain
                # in charge during healthy saves.
                if active_free_agents() >= 160:
                    return 0
                minimum = 200
                emergency_need = minimum - active_free_agents()
                regional_additions = self.promote_regional_emergency_talent(emergency_need)
            else:
                return 0
        created = 0
        existing_names = self.active_fighter_names()
        while active_free_agents() < minimum:
            fighter = self.create_generated_fighter(3, 38, 34, 78)
            self.avoid_name_collision(fighter, existing_names)
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.free_agent_months = 0
            fighter.ai_offer_company = ""
            fighter.ai_offer_months = 0
            fighter.ai_offer_purse = 0
            fighter.ai_offer_signing_bonus = 0
            fighter.market_origin = "Emergency free-agent replenishment"
            self.free_agents.append(fighter)
            created += 1
        if self.month <= 1:
            before = len(self.free_agents)
            self.ensure_free_agent_division_depth(self.free_agents, min_per_bucket=4)
            created += len(self.free_agents) - before
        if created:
            self.news.insert(0, f"{created} emergency free-agent prospects entered the market after the regional pathway could not meet demand.")
        return regional_additions + created

    def total_active_fighters(self, exclude_free_agents=False):
        total = len([f for f in self.roster if not f.retired])
        total += sum(len([f for f in promo.roster if not f.retired]) for promo in self.promotions)
        if not exclude_free_agents:
            total += len([f for f in self.free_agents if not f.retired])
        return total

    def ensure_world_fighter_target(self):
        # Company capacity is not a population target. Vacant major-promotion
        # places are filled only when somebody signs a real market fighter.
        # Regional circuits create and develop the next generation in-house.
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            vacancies = max(0, 70 - len([fighter for fighter in promo.roster if not fighter.retired]))
            if vacancies:
                # Feeders are fixed-capacity development systems. Replace every
                # active vacancy now so retirement and graduation never leave a
                # circuit shrinking for several months.
                self.regional_recruit_fighter(promo, slots=vacancies)
        return self.ensure_free_agent_depth(emergency=True)

    def thinnest_world_division(self):
        active = [fighter for fighter in self.all_fighter_objects() if not getattr(fighter, "retired", False)]
        counts = {}
        for gender in ("Male", "Female"):
            for weight in WEIGHTS:
                counts[(gender, weight)] = sum(1 for fighter in active if fighter.gender == gender and fighter.weight == weight)
        return min(counts, key=lambda key: (counts[key], 0 if key[0] == "Female" else 1, random.random()))

    def refresh_world(self):
        self.promo_tree.delete(*self.promo_tree.get_children())
        player_row = (self.player_company_name, self.player_region, "Player", self.company_pop, self.company_pop, f"${self.cash:,}", "0", self.format_game_date_text(self.event_log[0]) if self.event_log else "No shows yet")
        self.promo_tree.insert("", "end", values=player_row)
        for promo in sorted(self.promotions, key=lambda p: -p.reputation_score):
            if promo.show_history is None:
                promo.show_history = []
            last = self.format_game_date_text(promo.show_history[0]) if promo.show_history else "No shows yet"
            self.promo_tree.insert("", "end", values=(promo.name, promo.region, promo.reputation, promo.reputation_score, promo.size, f"${promo.cash:,}", promo.momentum, last))
        if hasattr(self, "world_news_list"):
            self.world_news_list.delete(0, "end")
            entries = list(getattr(self, "world_chronicle", []))[:60]
            self._world_news_entries = entries or [{"type": "News", "headline": item, "detail": item} for item in self.news[:60]]
            for entry in self._world_news_entries:
                self.world_news_list.insert("end", f"[{entry.get('type', 'News')}] {entry.get('headline', '')}")
            if self._world_news_entries:
                self.world_news_list.selection_set(0)
            self.show_selected_world_story()
        if hasattr(self, "gym_tree"):
            self.sync_gym_membership()
            self.gym_tree.delete(*self.gym_tree.get_children())
            for gym in sorted(getattr(self, "gyms", []), key=lambda g: (self.gym_effective_training(g), g.reputation), reverse=True):
                load = round(gym.member_count / max(1, gym.capacity) * 100)
                trend = f"{gym.momentum:+d}"
                self.gym_tree.insert("", "end", values=(gym.name, gym.region, self.gym_tier(gym), self.gym_effective_training(gym), gym.morale, f"{gym.member_count}/{gym.capacity} ({load}%)", trend, ", ".join(gym.specialties)))

    def clear_regional_prospect_filters(self):
        self.regional_prospect_search.set("")
        self.regional_prospect_status_filter.set("Eligible + Nearly")
        self.regional_prospect_company_filter.set("All")
        self.regional_prospect_gender_filter.set("All")
        self.regional_prospect_weight_filter.set("All")
        self.refresh_regional_prospects()

    def regional_prospect_rows(self):
        rows = []
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            for fighter in promo.roster:
                if getattr(fighter, "retired", False):
                    continue
                rows.append((promo, fighter, self.regional_candidate_assessment(fighter, promo)))
        return rows

    def refresh_regional_prospects(self):
        if not hasattr(self, "regional_prospect_tree"):
            return
        rows = self.regional_prospect_rows()
        companies = ["All"] + sorted({promo.name for promo, _fighter, _assessment in rows})
        self.regional_prospect_company_combo.configure(values=companies)
        if self.regional_prospect_company_filter.get() not in companies:
            self.regional_prospect_company_filter.set("All")
        query = self.regional_prospect_search.get().strip().lower()
        status_filter = self.regional_prospect_status_filter.get()
        company_filter = self.regional_prospect_company_filter.get()
        gender_filter = self.regional_prospect_gender_filter.get()
        weight_filter = self.regional_prospect_weight_filter.get()
        filtered = []
        for promo, fighter, assessment in rows:
            if query and query not in f"{fighter.name} {promo.name} {promo.region} {fighter.weight} {assessment['explanation']}".lower():
                continue
            if company_filter != "All" and promo.name != company_filter:
                continue
            if gender_filter != "All" and fighter.gender != gender_filter:
                continue
            if weight_filter != "All" and fighter.weight != weight_filter:
                continue
            status = assessment["status"]
            if status_filter == "Eligible + Nearly" and status not in ("Eligible Now", "Nearly Eligible", "Medical Hold"):
                continue
            if status_filter not in ("Eligible + Nearly", "All Regional") and status != status_filter:
                continue
            filtered.append((promo, fighter, assessment))
        order = {"Eligible Now": 0, "Medical Hold": 1, "Nearly Eligible": 2, "Developing": 3, "Blocked": 4}
        filtered.sort(key=lambda row: (
            order.get(row[2]["status"], 9), -row[1].overall, -row[1].potential,
            -row[1].record_w, row[1].name.lower(),
        ))
        tree = self.regional_prospect_tree
        tree.delete(*tree.get_children())
        self._regional_prospect_rows = {}
        for index, (promo, fighter, assessment) in enumerate(filtered):
            row_id = f"regional:{fighter.fighter_id}:{index}"
            self._regional_prospect_rows[row_id] = (promo, fighter, assessment)
            visible = self.world_fighter_search_stat_visible(fighter, promo.name)
            status = assessment["status"]
            tag = "eligible" if status == "Eligible Now" else "medical" if status in ("Medical Hold", "Blocked") else "nearly" if status == "Nearly Eligible" else "developing"
            tree.insert("", "end", iid=row_id, tags=(tag,), values=(
                fighter.name, status, promo.name, promo.region, fighter.gender[:1], fighter.weight,
                fighter.age, fighter.record, f"{assessment['win_rate']:.0%}",
                fighter.overall if visible else "Hidden", fighter.potential if visible else "Hidden",
                f"{fighter.momentum:+d}", fighter.popularity, self.fighter_last_fight_date_label(fighter),
                assessment["explanation"],
            ))
        throughput = self.regional_market_throughput()
        eligible_count = sum(assessment["eligible"] for _promo, _fighter, assessment in rows)
        near_count = sum(assessment["status"] == "Nearly Eligible" for _promo, _fighter, assessment in rows)
        mode = "Ratings respect Scouting Mode." if self.rules.get("scouting_mode", False) else "Full ratings visible."
        self.regional_prospect_count.config(
            text=(
                f"{len(filtered):,} shown | {eligible_count:,} eligible worldwide | {near_count:,} nearly eligible | "
                f"{throughput['graduation_slots']} circuit graduation slot(s) this month | {mode}"
            )
        )
        self.regional_prospect_detail_var.set(
            "Select a prospect to see exactly why they qualify or what remains. Green = eligible, gold = nearly eligible, red = medical/administrative hold."
        )
        if hasattr(self, "regional_prospect_negotiate_button"):
            self.regional_prospect_negotiate_button.config(state="disabled")

    def selected_regional_prospect(self):
        selected = self.regional_prospect_tree.selection() if hasattr(self, "regional_prospect_tree") else ()
        return self._regional_prospect_rows.get(selected[0]) if selected else None

    def show_selected_regional_prospect(self, _event=None):
        selected = self.selected_regional_prospect()
        if not selected:
            if hasattr(self, "regional_prospect_negotiate_button"):
                self.regional_prospect_negotiate_button.config(state="disabled")
            return
        promo, fighter, assessment = selected
        report = self.scouting_report_for(fighter)
        intel = self.scouting_intel_label(fighter, report)
        selected_circuits = set(self.rules.get("regional_graduation_promotions", []) or [])
        rotation = (
            "This circuit currently holds a world graduation slot."
            if promo.name in selected_circuits else
            "This circuit was not selected for a world graduation slot this month."
        )
        self.regional_prospect_detail_var.set(
            f"{fighter.name} | {promo.name} | {assessment['status']} | {assessment['explanation']}. "
            f"Record {fighter.record}; {assessment['bouts']} bouts; win rate {assessment['win_rate']:.0%}; "
            f"momentum {fighter.momentum:+d}; popularity {fighter.popularity}; scouting intel: {intel}. {rotation}"
        )
        if hasattr(self, "regional_prospect_negotiate_button"):
            self.regional_prospect_negotiate_button.config(state="normal" if assessment["eligible"] else "disabled")

    def open_selected_regional_prospect(self):
        selected = self.selected_regional_prospect()
        if selected:
            self.open_fighter_profile_window(selected[1])
        else:
            self.regional_prospect_detail_var.set("Select a regional fighter first.")

    def scout_selected_regional_prospect(self, kind):
        selected = self.selected_regional_prospect()
        if not selected:
            self.regional_prospect_detail_var.set("Select a regional fighter to scout.")
            return
        _promo, fighter, _assessment = selected
        if self.start_scout_report_for_fighter(fighter, kind):
            self.regional_prospect_detail_var.set(f"{kind.title()} scouting assignment started for {fighter.name}.")
            self.refresh_regional_prospects()

    def negotiate_selected_regional_prospect(self):
        selected = self.selected_regional_prospect()
        if not selected:
            self.regional_prospect_detail_var.set("Select a regional fighter to approach.")
            return
        promo, fighter, assessment = selected
        if getattr(self, "spectator_mode", False):
            self.regional_prospect_detail_var.set("Take control of a promotion before negotiating with fighters.")
            return
        if not assessment["eligible"]:
            self.regional_prospect_detail_var.set(f"{fighter.name} is not eligible to sign yet: {assessment['explanation']}.")
            return
        if fighter not in promo.roster:
            self.regional_prospect_detail_var.set(f"{fighter.name} has already left {promo.name}. The list has been refreshed.")
            self.refresh_regional_prospects()
            return
        self.open_contract_negotiation(fighter, existing=False, source_promotion=promo)

    def clear_world_fighter_filters(self):
        self.world_fighter_search.set("")
        self.world_fighter_company_filter.set("All")
        self.world_fighter_gender_filter.set("All")
        self.world_fighter_weight_filter.set("All")
        self.world_fighter_sport_filter.set("All")
        self.world_fighter_status_filter.set("Active")
        self.refresh_world_fighter_search()

    def world_fighter_search_stat_visible(self, fighter, company):
        return self.fighter_profile_stats_visible(fighter, company)

    def world_fighter_universe_record(self, fighter):
        baseline = self.ensure_fighter_history_baseline(fighter)
        return "-".join(str(max(0, value - baseline[index])) for index, value in enumerate((fighter.record_w, fighter.record_l, fighter.record_d)))

    def world_fighter_last_five(self, fighter):
        # bout_rating_history is newest-first; take the five most recent then
        # reverse so the sequence reads oldest -> newest (latest result last).
        results = [str(entry.get("result", ""))[:1] for entry in (getattr(fighter, "bout_rating_history", None) or []) if isinstance(entry, dict) and str(entry.get("result", ""))[:1] in ("W", "L", "D")]
        if not results:
            return "-"
        return "".join(reversed(results[:5]))

    def refresh_world_fighter_search(self):
        if not hasattr(self, "world_fighter_tree"):
            return
        rows = self.all_database_fighters_with_companies()
        companies = ["All"] + sorted({company for company, _fighter in rows})
        sports = ["All"] + sorted({getattr(fighter, "primary_discipline", "MMA") or "MMA" for _company, fighter in rows})
        self.world_fighter_company_combo.configure(values=companies)
        self.world_fighter_sport_combo.configure(values=sports)
        if self.world_fighter_company_filter.get() not in companies:
            self.world_fighter_company_filter.set("All")
        if self.world_fighter_sport_filter.get() not in sports:
            self.world_fighter_sport_filter.set("All")
        search = self.world_fighter_search.get().strip().lower()
        company_filter = self.world_fighter_company_filter.get()
        gender_filter = self.world_fighter_gender_filter.get()
        weight_filter = self.world_fighter_weight_filter.get()
        sport_filter = self.world_fighter_sport_filter.get()
        status_filter = self.world_fighter_status_filter.get()
        filtered = []
        for company, fighter in rows:
            retired = bool(getattr(fighter, "retired", False) or company == "Retired")
            free_agent = company == "Free Agent"
            sport = getattr(fighter, "primary_discipline", "MMA") or "MMA"
            if search and search not in f"{fighter.name} {company} {sport} {fighter.region} {fighter.nationality}".lower():
                continue
            if company_filter != "All" and company != company_filter:
                continue
            if gender_filter != "All" and fighter.gender != gender_filter:
                continue
            if weight_filter != "All" and fighter.weight != weight_filter:
                continue
            if sport_filter != "All" and sport != sport_filter:
                continue
            if status_filter == "Active" and retired:
                continue
            if status_filter == "Free Agents" and not free_agent:
                continue
            if status_filter == "Retired" and not retired:
                continue
            filtered.append((company, fighter, sport))
        filtered.sort(key=lambda row: (row[0] != self.player_company_name, row[0], row[1].name.lower()))
        self.world_fighter_tree.delete(*self.world_fighter_tree.get_children())
        self._world_fighter_search_rows = {}
        for index, (company, fighter, sport) in enumerate(filtered):
            item_id = str(index)
            visible = self.world_fighter_search_stat_visible(fighter, company)
            self._world_fighter_search_rows[item_id] = (company, fighter)
            self.world_fighter_tree.insert("", "end", iid=item_id, values=(
                fighter.name, company, sport, fighter.gender[:1], self.fighter_display_division(fighter), fighter.age,
                self.world_fighter_universe_record(fighter), fighter.record, self.world_fighter_last_five(fighter),
                fighter.last_fight or "No recorded fight", fighter.overall if visible else "Hidden",
                getattr(fighter, "elo_rating", 1500) if visible else "Hidden",
            ))
        mode = "Scouting Mode: unscouted rival ratings are hidden." if self.rules.get("scouting_mode", False) else "Full public ratings are visible."
        self.world_fighter_search_count.config(text=f"{len(filtered):,} fighters found. {mode}")

    def open_selected_world_fighter_profile(self):
        selected = self.world_fighter_tree.selection() if hasattr(self, "world_fighter_tree") else ()
        if not selected:
            messagebox.showinfo("Fighter Search", "Select a fighter first.")
            return
        company, fighter = self._world_fighter_search_rows.get(selected[0], ("", None))
        if not fighter:
            return
        self.open_fighter_profile_window(fighter)

    def compare_selected_world_fighters(self):
        selected = list(self.world_fighter_tree.selection()) if hasattr(self, "world_fighter_tree") else []
        fighters = []
        seen = set()
        for row_id in selected:
            company, fighter = self._world_fighter_search_rows.get(row_id, ("", None))
            if not fighter or id(fighter) in seen:
                continue
            fighters.append((company, fighter))
            seen.add(id(fighter))
            if len(fighters) == 2:
                break
        if len(fighters) < 2:
            messagebox.showinfo("Compare Fighters", "Select two fighters in Fighter Search, then choose Compare Selected.")
            return
        self.open_compare_fighters_window(fighters[0], fighters[1])

    def open_compare_fighters_window(self, left_pick, right_pick):
        left_company, left_fighter = left_pick
        right_company, right_fighter = right_pick
        window = tk.Toplevel(self.root)
        window.title(f"Compare Fighters - {left_fighter.name} vs {right_fighter.name}")
        width = min(1180, max(980, window.winfo_screenwidth() - 180))
        height = min(760, max(620, window.winfo_screenheight() - 180))
        window.geometry(f"{width}x{height}+{max(0, (window.winfo_screenwidth() - width) // 2)}+{max(0, (window.winfo_screenheight() - height) // 3)}")
        window.configure(bg=self.colors["chrome"])
        self.screen_header(window, "COMPARE FIGHTERS", f"{left_fighter.name} vs {right_fighter.name}")

        header = ttk.Frame(window, style="Chrome.TFrame")
        header.pack(fill="x", padx=10, pady=(0, 6))
        for company, fighter, side in ((left_company, left_fighter, "left"), (right_company, right_fighter, "right")):
            frame = ttk.Frame(header, style="Panel.TFrame")
            frame.pack(side=side, fill="both", expand=True, padx=(0, 5) if side == "left" else (5, 0))
            tk.Label(frame, text=fighter.name.upper(), bg=self.colors["panel"], fg=self.colors["gold"], font=("Impact", 18), anchor="w").pack(fill="x", padx=10, pady=(8, 1))
            titles = self.fighter_current_championships(fighter)
            title_line = f" | {titles[0]}" if titles else ""
            rank_line = f"{company} | {fighter.gender} {self.fighter_display_division(fighter)} | {self.profile_rank_text(fighter, self.rank_label_for_fighter(fighter, company), 'Company')} | {self.profile_rank_text(fighter, self.rank_label_for_fighter(fighter, company, world=True), 'World')}{title_line}"
            tk.Label(frame, text=rank_line, bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w", wraplength=520).pack(fill="x", padx=10, pady=(0, 8))

        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        columns = ("category", "left", "edge", "right")
        tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        for column, label, width_col, anchor in (
            ("category", "Measure", 205, "w"),
            ("left", left_fighter.name, 250, "center"),
            ("edge", "Edge", 110, "center"),
            ("right", right_fighter.name, 250, "center"),
        ):
            tree.heading(column, text=label)
            tree.column(column, width=width_col, anchor=anchor)
        tree.tag_configure("left_edge", foreground="#a8f0bd")
        tree.tag_configure("right_edge", foreground="#ffd18a")
        tree.tag_configure("even", foreground=self.colors["muted"])
        tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        def visible_rating(fighter, company):
            return self.world_fighter_search_stat_visible(fighter, company)

        def safe_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        left_visible = visible_rating(left_fighter, left_company)
        right_visible = visible_rating(right_fighter, right_company)
        rows = [
            ("Record", left_fighter.record, None, right_fighter.record),
            ("Universe Record", self.world_fighter_universe_record(left_fighter), None, self.world_fighter_universe_record(right_fighter)),
            ("Last 5", self.world_fighter_last_five(left_fighter), None, self.world_fighter_last_five(right_fighter)),
            ("Age", left_fighter.age, "lower", right_fighter.age),
            ("Overall", left_fighter.overall if left_visible else "Hidden", "higher" if left_visible and right_visible else None, right_fighter.overall if right_visible else "Hidden"),
            ("Potential", left_fighter.potential if left_visible else "Hidden", "higher" if left_visible and right_visible else None, right_fighter.potential if right_visible else "Hidden"),
            ("ELO", getattr(left_fighter, "elo_rating", 1500) if left_visible else "Hidden", "higher" if left_visible and right_visible else None, getattr(right_fighter, "elo_rating", 1500) if right_visible else "Hidden"),
            ("Momentum", f"{left_fighter.momentum:+d}", "higher", f"{right_fighter.momentum:+d}"),
            ("Popularity", left_fighter.popularity, "higher", right_fighter.popularity),
            ("Star Quality", left_fighter.star_quality, "higher", right_fighter.star_quality),
            ("Morale", left_fighter.morale, "higher", right_fighter.morale),
            ("Fatigue", left_fighter.fatigue, "lower", right_fighter.fatigue),
            ("Title Wins", left_fighter.title_wins, "higher", right_fighter.title_wins),
            ("Title Defenses", left_fighter.title_defenses, "higher", right_fighter.title_defenses),
            ("Style", left_fighter.style, None, right_fighter.style),
            ("Stance", left_fighter.stance, None, right_fighter.stance),
            ("Trait", left_fighter.trait, None, right_fighter.trait),
            ("Camp", left_fighter.camp, None, right_fighter.camp),
            ("Last Fight", left_fighter.last_fight or "No recorded fight", None, right_fighter.last_fight or "No recorded fight"),
        ]
        for label, left_value, compare, right_value in rows:
            edge = "-"
            tag = "even"
            if compare:
                left_score = safe_int(str(left_value).replace("+", ""))
                right_score = safe_int(str(right_value).replace("+", ""))
                if left_score != right_score:
                    left_wins = left_score > right_score if compare == "higher" else left_score < right_score
                    edge = left_fighter.name if left_wins else right_fighter.name
                    tag = "left_edge" if left_wins else "right_edge"
            tree.insert("", "end", values=(label, left_value, edge, right_value), tags=(tag,))

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(footer, text="Open Left Profile", command=lambda: self.open_fighter_profile_window(left_fighter)).pack(side="left", padx=4)
        ttk.Button(footer, text="Open Right Profile", command=lambda: self.open_fighter_profile_window(right_fighter)).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right", padx=4)

    def show_selected_world_story(self, _event=None):
        if not hasattr(self, "world_news_detail"):
            return
        selected = self.world_news_list.curselection() if hasattr(self, "world_news_list") else []
        entry = self._world_news_entries[selected[0]] if selected and selected[0] < len(getattr(self, "_world_news_entries", [])) else None
        self.world_news_detail.config(state="normal")
        self.world_news_detail.delete("1.0", "end")
        if entry:
            self.world_news_detail.insert("end", f"{self.format_game_date_text(entry.get('detail', entry.get('headline', '')))}\n\n{self.format_game_date(entry.get('month', self.month), entry.get('week', self.week))}")
        self.world_news_detail.config(state="disabled")

    def open_selected_world_story_context(self):
        selected = self.world_news_list.curselection() if hasattr(self, "world_news_list") else []
        if not selected:
            return
        entry = self._world_news_entries[selected[0]]
        self.open_story_entry_context(entry)

    def open_selected_world_story_reader(self):
        selected = self.world_news_list.curselection() if hasattr(self, "world_news_list") else []
        if not selected or selected[0] >= len(getattr(self, "_world_news_entries", [])):
            messagebox.showinfo("World News", "Select a story first.")
            return
        self.open_story_reader(self._world_news_entries[selected[0]])

    def open_superfight_night_window(self):
        """Build and run a crossover Superfight Night: negotiated champion-vs-champion
        bouts from rival promotions (non-title) plus optional prelims from your roster."""
        if getattr(self, "spectator_mode", False):
            messagebox.showinfo("Superfight Night", "Take control of a promotion to promote a superfight night.")
            return
        # Exclude fighters already committed to a booked/scheduled show so a
        # superfight can never double-book a fighter across events.
        committed = self.scheduled_fighter_names(include_booked=True)
        your_champions = [
            f for f in self.roster
            if getattr(f, "champion", False) and not getattr(f, "retired", False)
            and not getattr(f, "injured", 0) and f.name not in committed
        ]
        window = tk.Toplevel(self.root)
        window.title("Crossover Superfight Night")
        window.geometry("1080x720"); window.minsize(900, 600)
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        ttk.Label(window, text="CROSSOVER SUPERFIGHT NIGHT", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Label(window, text="Pay rival promotions to sanction champion-vs-champion superfights. Non-title: no belt ever changes hands. Add prelims from your own roster.", style="Inset.TLabel", wraplength=1040, justify="left").pack(fill="x", padx=12, pady=(0, 6))

        header = ttk.Frame(window, style="Inset.TFrame"); header.pack(fill="x", padx=12, pady=(0, 6))
        name_var = tk.StringVar(value=f"{self.player_company_name} Superfight Night")
        venue_var = tk.StringVar(value="National Sports Hall")
        ttk.Label(header, text="Event", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        ttk.Entry(header, textvariable=name_var, width=34).pack(side="left", padx=(0, 10))
        ttk.Label(header, text="Venue", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        ttk.Combobox(header, textvariable=venue_var, values=["Casino Ballroom", "National Sports Hall", "Regional Arena"], state="readonly", width=22).pack(side="left", padx=(0, 8))

        card = []  # ordered list of {"a", "b", "crossover"}

        body = ttk.Panedwindow(window, orient="horizontal"); body.pack(fill="both", expand=True, padx=12, pady=6)
        builder = ttk.Notebook(body); card_side = ttk.Frame(body, style="Panel.TFrame")
        body.add(builder, weight=3); body.add(card_side, weight=2)
        crossover_tab = ttk.Frame(builder, style="Panel.TFrame")
        prelim_tab = ttk.Frame(builder, style="Panel.TFrame")
        builder.add(crossover_tab, text="Crossover Superfight")
        builder.add(prelim_tab, text="Prelim Bout")

        # --- Crossover builder ---
        cx_panel, cx = self.section(crossover_tab, "CROSSOVER SUPERFIGHT"); cx_panel.pack(fill="both", expand=True, pady=(0, 4))
        row = ttk.Frame(cx, style="Inset.TFrame"); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Your champion", style="Inset.TLabel").pack(side="left", padx=(2, 3))
        your_champ_var = tk.StringVar()
        your_champ_box = ttk.Combobox(row, textvariable=your_champ_var, state="readonly", width=26,
                                      values=[f"{f.name} ({f.weight})" for f in your_champions])
        your_champ_box.pack(side="left", padx=(0, 8))
        ttk.Label(row, text="Offer", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        offer_var = tk.StringVar(value="Standard")
        ttk.Combobox(row, textvariable=offer_var, values=["Standard", "Generous (+50%)", "Blank cheque (+100%)"], state="readonly", width=18).pack(side="left")
        rival_tree = ttk.Treeview(cx, columns=("name", "promo", "division", "ovr", "pop", "fee", "odds"), show="headings", height=12, selectmode="browse")
        for col, text, w in (("name", "Rival Champion", 150), ("promo", "Promotion", 140), ("division", "Division", 150), ("ovr", "OVR", 46), ("pop", "Pop", 44), ("fee", "Sanction Fee", 100), ("odds", "Accept", 64)):
            rival_tree.heading(col, text=text); rival_tree.column(col, width=w, anchor="center")
        rival_tree.column("name", anchor="w"); rival_tree.column("promo", anchor="w")
        rival_tree.pack(fill="both", expand=True, pady=4)
        cx_status = ttk.Label(cx, text="Select your champion, then a rival champion to sanction.", style="Inset.TLabel", wraplength=560, justify="left")
        cx_status.pack(fill="x", padx=2, pady=(0, 2))
        cx_actions = ttk.Frame(cx, style="Inset.TFrame"); cx_actions.pack(fill="x", pady=(0, 2))

        def offer_multiplier():
            return {"Standard": 1.0, "Generous (+50%)": 1.5, "Blank cheque (+100%)": 2.0}.get(offer_var.get(), 1.0)

        def selected_your_champ():
            index = your_champ_box.current()
            return your_champions[index] if 0 <= index < len(your_champions) else None

        rival_rows = {}
        def refresh_rivals(*_):
            rival_tree.delete(*rival_tree.get_children())
            rival_rows.clear()
            champ = selected_your_champ()
            if not champ:
                cx_status.config(text="Select one of your champions to see eligible rival champions in the same (or one adjacent, catchweight) division.")
                return
            eligible = self.eligible_crossover_champions(gender=champ.gender, weight=champ.weight, max_class_gap=1)
            for rival, promo in eligible:
                fee = round(self.crossover_sanctioning_fee(rival) * offer_multiplier())
                odds = round(self.crossover_acceptance_chance(rival, offer=fee) * 100)
                catch = " (catchweight)" if rival.weight != champ.weight else ""
                iid = getattr(rival, "fighter_id", "") or rival.name
                rival_rows[iid] = (rival, promo)
                rival_tree.insert("", "end", iid=iid, values=(rival.name, promo.name, rival.weight + catch, rival.overall, rival.popularity, f"${fee:,}", f"{odds}%"))
            if not eligible:
                cx_status.config(text=f"No rival champion is available at {champ.weight} or an adjacent division right now.")
            else:
                cx_status.config(text=f"{len(eligible)} eligible {champ.gender.lower()} champion(s) within one division of {champ.name} ({champ.weight}). '(catchweight)' = one class apart.")
        your_champ_box.bind("<<ComboboxSelected>>", refresh_rivals)
        for widget in (window,):
            pass
        offer_var.trace_add("write", lambda *_: refresh_rivals())

        def propose():
            champ = selected_your_champ()
            if not champ:
                cx_status.config(text="Pick one of your champions first."); return
            selected = rival_tree.selection()
            if not selected:
                cx_status.config(text="Select a rival champion to negotiate."); return
            rival, promo = rival_rows[selected[0]]
            booked_fighters = {bout["a"] for bout in card} | {bout["b"] for bout in card}
            if champ in booked_fighters or rival in booked_fighters:
                cx_status.config(text=f"{champ.name} or {rival.name} is already booked on this card."); return
            fee = round(self.crossover_sanctioning_fee(rival) * offer_multiplier())
            if self.cash < fee:
                cx_status.config(text=f"You need ${fee:,} to sanction {rival.name}."); return
            chance = self.crossover_acceptance_chance(rival, offer=fee)
            if random.random() < chance:
                self.cash -= fee
                self.record_finance_transaction(f"Superfight sanction: {rival.name} ({promo.name})", costs=fee)
                card.append({"a": champ, "b": rival, "crossover": True})
                cx_status.config(text=f"{promo.name} agreed! {champ.name} vs {rival.name} added for ${fee:,}. Cash: ${self.cash:,}.")
                refresh_card()
            else:
                cx_status.config(text=f"{promo.name} declined this time. Try a more generous offer or grow your prestige.")
        ttk.Button(cx_actions, text="Propose & Add Superfight", style="Accent.TButton", command=propose).pack(side="left", padx=2)

        # --- Prelim builder (full matchmaker-style table) ---
        pr_panel, pr = self.section(prelim_tab, "PRELIM BOUT (YOUR ROSTER)"); pr_panel.pack(fill="both", expand=True)
        pr_filters = ttk.Frame(pr, style="Inset.TFrame"); pr_filters.pack(fill="x", padx=4, pady=(4, 2))
        pr_search = tk.StringVar(); pr_weight = tk.StringVar(value="All"); pr_gender = tk.StringVar(value="All")
        ttk.Label(pr_filters, text="Search", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        pr_search_entry = ttk.Entry(pr_filters, textvariable=pr_search, width=16); pr_search_entry.pack(side="left", padx=(0, 8))
        ttk.Label(pr_filters, text="Weight", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        pr_weight_box = ttk.Combobox(pr_filters, values=["All", *WEIGHTS], textvariable=pr_weight, state="readonly", width=14); pr_weight_box.pack(side="left", padx=(0, 8))
        ttk.Label(pr_filters, text="Gender", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        pr_gender_box = ttk.Combobox(pr_filters, values=["All", "Male", "Female"], textvariable=pr_gender, state="readonly", width=8); pr_gender_box.pack(side="left")
        pr_legend = tk.Frame(pr, bg=self.colors["panel_dark"]); pr_legend.pack(fill="x", padx=4, pady=(0, 2))
        for swatch_color, swatch_text in (("#7fd694", "winning record"), ("#e8837a", "losing record"), ("#9298a1", "unavailable this date")):
            tk.Label(pr_legend, text="■", bg=self.colors["panel_dark"], fg=swatch_color, font=("Tahoma", 9)).pack(side="left", padx=(6, 1))
            tk.Label(pr_legend, text=swatch_text, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left")
        pr_hist_var = tk.StringVar(value="Select two same-division fighters, then Add Prelim.")
        ttk.Label(pr, textvariable=pr_hist_var, style="Inset.TLabel", anchor="w", wraplength=560, justify="left").pack(fill="x", padx=4)
        prelim_tree = ttk.Treeview(pr, columns=("name", "gender", "weight", "rank", "titlepath", "record", "age", "overall", "elo", "pop", "build", "last", "form", "trend", "activity", "fit", "history", "status"), show="headings", selectmode="extended", height=13)
        for key, label, size in (("name", "Name", 148), ("gender", "G", 34), ("weight", "Class", 90), ("rank", "Rank", 44), ("titlepath", "Title Path", 104), ("record", "Record", 66), ("age", "Age", 40), ("overall", "OVR", 44), ("elo", "ELO", 54), ("pop", "Pop", 42), ("build", "Build", 48), ("last", "Last Fight", 84), ("form", "Last 5 (→latest)", 82), ("trend", "Form", 56), ("activity", "Active", 50), ("fit", "Match Fit", 66), ("history", "History", 74), ("status", "Event Availability", 132)):
            prelim_tree.heading(key, text=label); prelim_tree.column(key, width=size, anchor="center")
        prelim_tree.column("name", anchor="w"); prelim_tree.column("titlepath", anchor="w")
        prelim_tree.tag_configure("not_ready", foreground="#9298a1")
        prelim_tree.tag_configure("rec_win", foreground="#7fd694")
        prelim_tree.tag_configure("rec_loss", foreground="#e8837a")
        self.make_tree_sortable(prelim_tree)
        self.attach_tree_heading_tooltips(prelim_tree, {
            "rank": "Divisional rank. C = champion, #n = ranked contender, - = unranked.",
            "titlepath": "Where this fighter sits on the road to a belt.",
            "record": "Career wins-losses-draws. Row colour: green = winning, red = losing, grey = unavailable.",
            "build": "Match build - how compelling this fighter is to book right now.",
            "form": "Wins-losses over the last five bouts, oldest to newest (latest last).",
            "trend": "Momentum: win streak, rising, sliding, or steady.",
            "fit": "Match fitness vs the selected anchor.",
            "history": "Prior meetings with the other selected fighter.",
            "status": "Whether this fighter can be booked on this event.",
        })
        pr_scroll_x = ttk.Scrollbar(pr, orient="horizontal", command=prelim_tree.xview)
        prelim_tree.configure(xscrollcommand=pr_scroll_x.set)
        pr_scroll_x.pack(side="bottom", fill="x")
        prelim_tree.pack(fill="both", expand=True, padx=4, pady=(2, 2))
        pr_actions = ttk.Frame(pr, style="Inset.TFrame"); pr_actions.pack(fill="x", padx=4, pady=(0, 2))
        pr_status = ttk.Label(pr_actions, text="", style="Inset.TLabel", wraplength=440, justify="left")

        def prelim_pool():
            on_card = {bout["a"] for bout in card} | {bout["b"] for bout in card}
            return [f for f in self.roster if not getattr(f, "retired", False) and not getattr(f, "injured", 0) and f.name not in committed and f not in on_card]

        def refresh_prelim(*_):
            prelim_tree.delete(*prelim_tree.get_children())
            division_ranks = self.player_division_rank_map()
            search = pr_search.get().strip().lower()
            for fighter in sorted(prelim_pool(), key=lambda item: (item.weight, item.gender, -item.overall, item.name)):
                if pr_weight.get() != "All" and fighter.weight != pr_weight.get():
                    continue
                if pr_gender.get() != "All" and fighter.gender != pr_gender.get():
                    continue
                if search and search not in fighter.name.lower():
                    continue
                rank = division_ranks.get(self.fighter_identity_key(fighter))
                rank_label = "C" if fighter.champion else f"#{rank}" if rank else "-"
                status = self.fighter_booking_status(fighter, self.month, self.week)
                prelim_tree.insert(
                    "", "end", iid=fighter.fighter_id, tags=self.available_row_tags(fighter, status),
                    values=(
                        fighter.name, fighter.gender[0], fighter.weight, rank_label,
                        self.matchmaking_title_path_label(fighter), fighter.record, fighter.age,
                        fighter.overall, fighter.elo_rating, fighter.popularity,
                        self.fight_build_score(fighter, rank=rank), self.fighter_last_fight_date_label(fighter),
                        self.world_fighter_last_five(fighter), self.matchmaking_form_label(fighter),
                        self.fighter_activity_rating(fighter), "-", "-", status,
                    ),
                )
            refresh_prelim_history()

        def refresh_prelim_history(_event=None):
            selected_ids = list(prelim_tree.selection())
            fighters = [next((f for f in self.roster if f.fighter_id == fid), None) for fid in selected_ids]
            fighters = [f for f in fighters if f]
            for row_id in prelim_tree.get_children():
                prelim_tree.set(row_id, "history", "-"); prelim_tree.set(row_id, "fit", "-")
            if not fighters:
                pr_hist_var.set("Select two same-division fighters, then Add Prelim."); return
            if len(fighters) == 1:
                anchor = fighters[0]
                for row_id in prelim_tree.get_children():
                    opponent = next((f for f in self.roster if f.fighter_id == row_id), None)
                    prelim_tree.set(row_id, "history", self.matchup_history_indicator(anchor, opponent))
                    fit = self.matchmaking_fit_score(anchor, opponent)
                    if fit is not None:
                        prelim_tree.set(row_id, "fit", str(fit))
                pr_hist_var.set(f"OPPONENT CHECK: comparing every fighter with {anchor.name}.")
                return
            a, b = fighters[:2]
            indicator = self.matchup_history_indicator(a, b); fit = self.matchmaking_fit_score(a, b)
            for row_id in selected_ids[:2]:
                prelim_tree.set(row_id, "history", indicator); prelim_tree.set(row_id, "fit", str(fit or "-"))
            if a.gender != b.gender or a.weight != b.weight:
                pr_hist_var.set(f"{a.name} and {b.name} are not the same division - pick a same-gender, same-weight pairing.")
            else:
                pr_hist_var.set(f"{a.name} vs {b.name}: {indicator}. Ready to add as a prelim.")

        def add_prelim():
            selected = prelim_tree.selection()
            if len(selected) != 2:
                pr_status.config(text="Select exactly two fighters for a prelim."); pr_status.pack(side="left", padx=4); return
            fighters = [next((f for f in self.roster if f.fighter_id == fid), None) for fid in selected]
            if any(f is None for f in fighters):
                return
            a, b = fighters
            if a.gender != b.gender or a.weight != b.weight:
                pr_status.config(text="Prelim opponents must share a gender and weight class."); pr_status.pack(side="left", padx=4); return
            if any(a in (bout["a"], bout["b"]) or b in (bout["a"], bout["b"]) for bout in card):
                pr_status.config(text="One of those fighters is already on the card."); pr_status.pack(side="left", padx=4); return
            card.append({"a": a, "b": b, "crossover": False})
            pr_status.config(text=f"Added prelim {a.name} vs {b.name}."); pr_status.pack(side="left", padx=4)
            refresh_card(); refresh_prelim()

        ttk.Button(pr_actions, text="Add Prelim (select 2)", style="Accent.TButton", command=add_prelim).pack(side="left", padx=2)
        pr_status.pack(side="left", padx=4)
        pr_search_entry.bind("<KeyRelease>", lambda _e: refresh_prelim())
        pr_weight_box.bind("<<ComboboxSelected>>", lambda _e: refresh_prelim())
        pr_gender_box.bind("<<ComboboxSelected>>", lambda _e: refresh_prelim())
        prelim_tree.bind("<<TreeviewSelect>>", refresh_prelim_history, add="+")
        prelim_tree.bind("<Double-1>", lambda _e: (prelim_tree.selection() and self.open_fighter_profile_window(next((f for f in self.roster if f.fighter_id == prelim_tree.selection()[0]), None))))

        # --- Card side ---
        card_panel, card_inner = self.section(card_side, "SUPERFIGHT NIGHT CARD (top = main event)"); card_panel.pack(fill="both", expand=True)
        card_tree = ttk.Treeview(card_inner, columns=("slot", "matchup", "type"), show="headings", height=14, selectmode="browse")
        for col, text, w in (("slot", "Slot", 90), ("matchup", "Matchup", 300), ("type", "Type", 130)):
            card_tree.heading(col, text=text); card_tree.column(col, width=w, anchor="w")
        card_tree.tag_configure("crossover", foreground="#e6c15a")
        card_tree.pack(fill="both", expand=True, pady=4)
        card_status = ttk.Label(card_inner, text="", style="Inset.TLabel", wraplength=380, justify="left"); card_status.pack(fill="x", pady=(0, 2))
        card_buttons = ttk.Frame(card_inner, style="Inset.TFrame"); card_buttons.pack(fill="x")

        def refresh_card():
            card_tree.delete(*card_tree.get_children())
            for index, bout in enumerate(card):
                slot = "MAIN EVENT" if index == 0 else f"Bout {len(card) - index}"
                kind = "Crossover Superfight" if bout["crossover"] else "Prelim"
                card_tree.insert("", "end", iid=str(index), tags=("crossover",) if bout["crossover"] else (),
                                 values=(slot, f"{bout['a'].name} vs {bout['b'].name}", kind))
            fees_note = f"{sum(1 for b in card if b['crossover'])} superfight(s), {sum(1 for b in card if not b['crossover'])} prelim(s)."
            card_status.config(text=f"{fees_note}  Cash: ${self.cash:,}. Sanction fees are already paid; purses are settled on the night.")
            refresh_prelim()
        def remove_bout():
            sel = card_tree.selection()
            if sel:
                del card[int(sel[0])]; refresh_card()
        def move_up():
            sel = card_tree.selection()
            if sel and int(sel[0]) > 0:
                i = int(sel[0]); card[i - 1], card[i] = card[i], card[i - 1]; refresh_card(); card_tree.selection_set(str(i - 1))
        ttk.Button(card_buttons, text="Remove", command=remove_bout).pack(side="left", padx=2, pady=3)
        ttk.Button(card_buttons, text="Move Up", command=move_up).pack(side="left", padx=2, pady=3)

        def run_night():
            if not card:
                card_status.config(text="Add at least one bout before running the night."); return
            if not any(bout["crossover"] for bout in card):
                if not messagebox.askyesno("No superfights", "This card has no crossover superfights. Run it anyway?"):
                    return
            name = name_var.get().strip() or f"{self.player_company_name} Superfight Night"
            region = self.player_region
            bouts = [dict(bout) for bout in card]
            package = self.run_superfight_night(name, venue_var.get(), region, bouts)
            window.destroy()
            self.refresh_all()
            self.open_live_fight_window({"name": name}, package, apply_results=False)
        run_bar = ttk.Frame(window, style="Inset.TFrame"); run_bar.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(run_bar, text="Run Superfight Night", style="Accent.TButton", command=run_night).pack(side="right", padx=4)
        ttk.Button(run_bar, text="Close", command=window.destroy).pack(side="right", padx=4)

        if not your_champions:
            roster_champs = [f for f in self.roster if getattr(f, "champion", False) and not getattr(f, "retired", False)]
            if roster_champs:
                cx_status.config(text="Your champions are all injured or already committed to a scheduled show, so none can headline right now. You can still book prelims.")
            else:
                cx_status.config(text="You have no champions yet. Win a title first to headline a crossover superfight (you can still book prelims).")
        else:
            your_champ_box.current(0); refresh_rivals()
        refresh_card()

    def open_combat_sports_window(self):
        window = tk.Toplevel(self.root)
        window.title("Combat Sports Universe")
        window.geometry("1120x680")
        window.minsize(920, 560)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="COMBAT SPORTS UNIVERSE", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Label(window, text="Each sport has an AI flagship. Open your own child promotion (for example UFC BJJ), sign its athletes, book its matchups, then run and watch its cards. Academy prospects can graduate into an open child promotion.", style="Inset.TLabel").pack(fill="x", padx=12, pady=(0, 8))
        tree = ttk.Treeview(window, columns=("sport", "promotion", "strategy", "roster", "titles", "cash", "rep", "player", "events"), show="headings")
        for column, label, width in (("sport", "Sport", 120), ("promotion", "AI Flagship", 195), ("strategy", "AI Strategy", 120), ("roster", "Active", 55), ("titles", "Titles", 50), ("cash", "Circuit Cash", 95), ("rep", "Rep", 45), ("player", "Your Division", 105), ("events", "Cards", 50)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        detail = tk.Text(window, height=7, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
        detail.config(state="disabled")

        def redraw():
            tree.delete(*tree.get_children())
            for sport, world in getattr(self, "combat_sport_worlds", {}).items():
                state = self.ensure_combat_sport_circuit_state(sport, world, world.get("promotion", ""), False)
                division = getattr(self, "player_combat_divisions", {}).get(sport, {})
                owned = f"{division.get('promotion_name', self.player_company_name)} ({len(division.get('roster', []))})" if division else "Not opened"
                active = len(self.combat_sport_roster(sport, world.get("promotion", "")))
                titles = sum(1 for champion in state.get("titles", {}).values() if champion)
                tree.insert("", "end", iid=sport, values=(sport, world.get("promotion", ""), world.get("strategy", "Merit Ladder"), active, titles, f"${world.get('cash', 0):,}", world.get("reputation", 0), owned, world.get("events", 0)))
            if not tree.selection() and tree.get_children():
                tree.selection_set(tree.get_children()[0])
            show_detail()

        def show_detail(_event=None):
            selected = tree.selection()
            sport = selected[0] if selected else ""
            world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
            division = getattr(self, "player_combat_divisions", {}).get(sport, {})
            ranked = self.combat_sport_ranked(sport, world.get("promotion", ""))[:5] if sport else []
            latest = world.get("event_history", [])[:3]
            titles = world.get("titles", {})
            title_text = "; ".join(f"{self.combat_sport_division_label(key)} — {champion or 'Vacant'}" for key, champion in list(titles.items())[:5]) or "No established titles"
            latest_award = (world.get("awards", []) or [{}])[0]
            award_text = latest_award.get("summary", latest_award) if isinstance(latest_award, dict) else str(latest_award)
            lines = [
                f"{sport or 'Select a sport'}",
                f"AI flagship: {world.get('promotion', '-')}. Strategy: {world.get('strategy', 'Merit Ladder')}. Cash ${world.get('cash', 0):,} | Reputation {world.get('reputation', 0)} | Stability {world.get('stability', 0)}.",
                f"Your child promotion: {'opened' if division else 'not opened'}" + (f" — {division.get('promotion_name', self.player_company_name)} | Strategy {division.get('strategy', 'Balanced')} | Athletes {len(division.get('roster', []))} | Net ${division.get('profit_total', 0):,}" if division else ""),
                "Championships: " + title_text,
                "Top AI athletes: " + (", ".join(f"{fighter.name} ({self.combat_sport_competition_class(sport, fighter)})" for fighter in ranked) if ranked else "None"),
                "Latest: " + (latest[0] if latest else "No cards yet.") + (f" | Awards: {award_text}" if award_text else ""),
            ]
            detail.config(state="normal")
            detail.delete("1.0", "end")
            detail.insert("end", "\n".join(lines))
            detail.config(state="disabled")

        redraw()
        tree.bind("<<TreeviewSelect>>", show_detail)
        tree.pack(fill="both", expand=True, padx=10, pady=8)
        actions = ttk.Frame(window, style="Chrome.TFrame"); actions.pack(fill="x", padx=10, pady=(0, 10))
        def launch():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Combat Sports", "Select a sport first."); return
            ok, result = self.open_player_combat_division(selected[0])
            if ok:
                redraw()
                self.open_player_combat_division_window(selected[0])
            else: messagebox.showwarning("Division Unavailable", result)
        def manage():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Combat Sports", "Select a sport first."); return
            sport = selected[0]
            if sport not in getattr(self, "player_combat_divisions", {}):
                launch()
            else:
                self.open_player_combat_division_window(sport)
        ttk.Button(actions, text="Open / Manage Child Promotion", style="Accent.TButton", command=manage).pack(side="left")
        ttk.Button(actions, text="Circuit Records & History", command=lambda: self.open_combat_sport_history_window(tree.selection()[0]) if tree.selection() else None).pack(side="left", padx=6)
        ttk.Button(actions, text="Refresh", command=redraw).pack(side="left", padx=6)
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right")

    def open_combat_sport_history_window(self, sport, player_owned=False):
        world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
        division = (getattr(self, "player_combat_divisions", {}) or {}).get(sport, {}) if player_owned else {}
        employer = division.get("promotion_name", self.player_company_name) if player_owned else world.get("promotion", "")
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        self.combat_sport_record_book(sport, world, employer, player_owned)
        window = tk.Toplevel(self.root)
        circuit_name = employer if player_owned else world.get("promotion", sport)
        window.title(f"{sport} - Records and History")
        window.geometry("980x650")
        window.minsize(760, 500)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"{sport.upper()} — {circuit_name.upper()}", style="ScreenTitle.TLabel").pack(fill="x", padx=10, pady=(10, 5))
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=6)

        rankings_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(rankings_tab, text="Championships & Rankings")
        ranking_tree = ttk.Treeview(rankings_tab, columns=("division", "champion", "top"), show="headings")
        for column, label, width in (("division", "Division", 180), ("champion", "Champion", 210), ("top", "Ranked Contenders", 500)):
            ranking_tree.heading(column, text=label); ranking_tree.column(column, width=width, anchor="w")
        ranking_tree.pack(fill="both", expand=True, padx=6, pady=6)
        for key, names in sorted(state.get("rankings_by_division", {}).items()):
            ranking_tree.insert("", "end", iid=key, values=(self.combat_sport_division_label(key), state.get("titles", {}).get(key, "") or "Vacant", ", ".join(names[:6])))

        def open_ranked_athlete(_event=None):
            selected = ranking_tree.selection()
            if not selected:
                return
            key = selected[0]
            name = state.get("titles", {}).get(key, "") or next(iter(state.get("rankings_by_division", {}).get(key, [])), "")
            source_roster = self.combat_sport_roster(sport, employer) if player_owned else world.get("roster", [])
            fighter = next((candidate for candidate in source_roster if candidate.name == name), None)
            if fighter:
                self.open_fighter_profile_window(fighter)
        ranking_tree.bind("<Double-1>", open_ranked_athlete)

        def add_text_tab(label, lines):
            frame = ttk.Frame(notebook, style="Chrome.TFrame")
            notebook.add(frame, text=label)
            text = tk.Text(frame, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 10), padx=12, pady=10)
            scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            text.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            text.insert("end", "\n\n".join(str(line) for line in lines if str(line).strip()) or "No history recorded yet.")
            text.config(state="disabled")

        title_lines = []
        for key, history in sorted(state.get("title_history", {}).items()):
            title_lines.append(self.combat_sport_division_label(key).upper())
            title_lines.extend(f"{self.format_game_date(entry.get('month', 1), entry.get('week', 1), include_week=False)}: {entry.get('winner', 'Vacant')} over {entry.get('loser', '')} — {entry.get('method', '')}" for entry in history[:30])
        add_text_tab("Title Lineage", title_lines)
        add_text_tab("Record Book", [f"{label}: {value}" for label, value in state.get("record_book", {}).items()])
        add_text_tab("Awards", [entry.get("summary", entry) if isinstance(entry, dict) else entry for entry in state.get("awards", [])])
        add_text_tab("Hall of Fame", [entry.get("summary", entry) if isinstance(entry, dict) else entry for entry in state.get("hall_of_fame", [])])
        finance_lines = [f"{self.format_game_date(entry.get('month', 1), entry.get('week', 1), include_week=False)}: Revenue ${entry.get('revenue', 0):,} | Costs ${entry.get('cost', 0):,} | Profit ${entry.get('profit', 0):,} | Cash ${entry.get('cash', 0):,}" for entry in state.get("finance_history", [])]
        add_text_tab("Finances", [f"Current cash: ${state.get('cash', self.cash if player_owned else 0):,} | Reputation {state.get('reputation', 0)} | Stability {state.get('stability', 0)}"] + finance_lines)
        event_lines = ([event.get("headline", event.get("recap", "Completed card")) for event in state.get("events", [])] if player_owned else world.get("event_history", []))
        add_text_tab("Event Archive", event_lines)
        footer = ttk.Frame(window, style="Chrome.TFrame"); footer.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(footer, text="Open Selected Athlete", command=open_ranked_athlete).pack(side="left")
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right")

    def open_player_combat_division_window(self, sport):
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
        if not division or not world:
            messagebox.showinfo("Combat Sports", "Open that player division first.")
            return
        window = tk.Toplevel(self.root)
        promotion_name = division.get("promotion_name", f"{self.player_company_name} {'BJJ' if sport == 'Brazilian Jiu-Jitsu' else sport}")
        division.setdefault("promotion_name", promotion_name)
        division.setdefault("booked_bouts", [])
        window.title(f"{promotion_name} - {sport}")
        window.geometry("1280x760")
        window.minsize(1020, 640)
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"{promotion_name.upper()} — {sport.upper()}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        summary_var = tk.StringVar(value="")
        ttk.Label(header, textvariable=summary_var, style="ScreenTitle.TLabel").pack(side="right", padx=10)

        decision_var = tk.StringVar(value="Select an athlete to start building a card.")
        decision_bar = tk.Label(
            window, textvariable=decision_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg=self.colors["text"],
            font=("Tahoma", 9, "bold"), padx=10, pady=6,
        )
        decision_bar.pack(fill="x", padx=8, pady=(6, 0))

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        roster_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        matchmaking_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        market_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        events_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(roster_tab, text="Roster")
        notebook.add(matchmaking_tab, text="Matchmaking")
        notebook.add(market_tab, text="Market")
        notebook.add(events_tab, text="Events & Finance")

        strategy_var = tk.StringVar(value=division.get("strategy", "Balanced"))
        auto_cards_var = tk.BooleanVar(value=bool(division.get("auto_cards", False)))
        auto_card_minimum = tk.IntVar(value=max(1, min(14, int(division.get("auto_card_min_bouts", 5) or 5))))
        target_bouts_var = tk.IntVar(value=max(1, min(14, int(division.get("card_target_bouts", 6) or 6))))
        event_name_var = tk.StringVar(value=division.get("next_event_name", f"{promotion_name} {sport} Night"))
        title_var = tk.BooleanVar(value=False)

        roster_search_var = tk.StringVar(value="")
        roster_division_var = tk.StringVar(value="All")
        roster_ready_var = tk.StringVar(value="All")
        roster_filters = ttk.Frame(roster_tab, style="Inset.TFrame")
        roster_filters.pack(fill="x", padx=6, pady=6)
        ttk.Label(roster_filters, text="Search", style="Inset.TLabel").pack(side="left", padx=(6, 3), pady=4)
        roster_search = ttk.Entry(roster_filters, textvariable=roster_search_var, width=20)
        roster_search.pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(roster_filters, text="Division", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        roster_division_box = ttk.Combobox(roster_filters, textvariable=roster_division_var, values=("All",), state="readonly", width=18)
        roster_division_box.pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(roster_filters, text="Readiness", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        roster_ready_box = ttk.Combobox(roster_filters, textvariable=roster_ready_var, values=("All", "Ready", "Unavailable", "Booked"), state="readonly", width=13)
        roster_ready_box.pack(side="left", padx=(0, 10), pady=4)
        roster_count_var = tk.StringVar(value="")
        ttk.Label(roster_filters, textvariable=roster_count_var, style="Inset.TLabel").pack(side="right", padx=6, pady=4)

        roster_tree = ttk.Treeview(
            roster_tab,
            columns=("rank", "name", "gender", "division", "record", "age", "rating", "trend", "pop", "fatigue", "ready"),
            show="headings", selectmode="extended",
        )
        for column, label, width in (
            ("rank", "#", 42), ("name", "Athlete", 190), ("gender", "G", 34), ("division", "Division", 130),
            ("record", "Record", 78), ("age", "Age", 48), ("rating", "Sport RTG", 76),
            ("trend", "12m / Ceiling", 112), ("pop", "Pop", 52), ("fatigue", "Fatigue", 62), ("ready", "Availability", 145),
        ):
            roster_tree.heading(column, text=label)
            roster_tree.column(column, width=width, anchor="center")
        roster_tree.column("name", anchor="w")
        roster_tree.column("division", anchor="w")
        roster_tree.tag_configure("unavailable", foreground="#9298a1")
        roster_tree.tag_configure("booked", foreground="#d6b25e")
        self.make_tree_sortable(roster_tree)
        roster_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        roster_detail_var = tk.StringVar(value="Select an athlete for contract, development, and readiness detail.")
        roster_detail = ttk.Label(roster_tab, textvariable=roster_detail_var, style="Inset.TLabel", justify="left")
        roster_detail.pack(fill="x", padx=8, pady=(0, 5))
        roster_actions = ttk.Frame(roster_tab, style="Chrome.TFrame")
        roster_actions.pack(fill="x", padx=6, pady=(0, 6))

        matchmaking_setup = ttk.Frame(matchmaking_tab, style="Inset.TFrame")
        matchmaking_setup.pack(fill="x", padx=6, pady=6)
        ttk.Label(matchmaking_setup, text="Show", style="Inset.TLabel").pack(side="left", padx=(6, 3), pady=4)
        ttk.Entry(matchmaking_setup, textvariable=event_name_var, width=34).pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(matchmaking_setup, text="Target", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        target_spin = ttk.Spinbox(matchmaking_setup, from_=1, to=14, textvariable=target_bouts_var, width=4)
        target_spin.pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(matchmaking_setup, text="Strategy", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        strategy_box = ttk.Combobox(
            matchmaking_setup, values=("Balanced", "Prospect Builder", "Star Showcase", "Title Focus"),
            textvariable=strategy_var, state="readonly", width=17,
        )
        strategy_box.pack(side="left", padx=(0, 8), pady=4)
        ttk.Checkbutton(matchmaking_setup, text="Championship bout", variable=title_var).pack(side="left", padx=6, pady=4)

        matchup_panes = ttk.Panedwindow(matchmaking_tab, orient="horizontal")
        matchup_panes.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        athlete_panel, athlete_inner = self.section(matchup_panes, "1. CHOOSE ATHLETE")
        opponent_panel, opponent_inner = self.section(matchup_panes, "2. CHOOSE OPPONENT")
        card_panel, card_inner = self.section(matchup_panes, "3. RUNNING ORDER")
        matchup_panes.add(athlete_panel, weight=4)
        matchup_panes.add(opponent_panel, weight=3)
        matchup_panes.add(card_panel, weight=5)

        athlete_tree = ttk.Treeview(
            athlete_inner, columns=("name", "division", "record", "rating", "ready"),
            show="headings", selectmode="browse", height=15,
        )
        opponent_tree = ttk.Treeview(
            opponent_inner, columns=("name", "record", "rating", "gap", "quality"),
            show="headings", selectmode="browse", height=15,
        )
        card_tree = ttk.Treeview(
            card_inner, columns=("slot", "bout", "division", "stakes", "quality"),
            show="headings", selectmode="browse", height=15,
        )
        for tree, columns in (
            (athlete_tree, (("name", "Athlete", 135), ("division", "Division", 92), ("record", "Record", 55), ("rating", "RTG", 44), ("ready", "Status", 74))),
            (opponent_tree, (("name", "Opponent", 125), ("record", "Record", 55), ("rating", "RTG", 44), ("gap", "Gap", 38), ("quality", "Match", 66))),
            (card_tree, (("slot", "#", 34), ("bout", "Bout", 220), ("division", "Division", 92), ("stakes", "Stakes", 60), ("quality", "Match", 68))),
        ):
            for column, label, width in columns:
                tree.heading(column, text=label)
                tree.column(column, width=width, anchor="center")
            tree.column("name" if "name" in tree["columns"] else "bout", anchor="w")
            if tree is not card_tree:
                self.make_tree_sortable(tree)
            tree.pack(fill="both", expand=True)

        athlete_tree.tag_configure("unavailable", foreground="#9298a1")
        matchup_context_var = tk.StringVar(value="Choose an athlete. Compatible opponents will appear here.")
        ttk.Label(opponent_inner, textvariable=matchup_context_var, style="Inset.TLabel", wraplength=330, justify="left").pack(fill="x", pady=(5, 0))
        card_summary_var = tk.StringVar(value="")
        ttk.Label(card_inner, textvariable=card_summary_var, style="Inset.TLabel", wraplength=400, justify="left").pack(fill="x", pady=(5, 0))

        matchup_actions = ttk.Frame(matchmaking_tab, style="Chrome.TFrame")
        matchup_actions.pack(fill="x", padx=6, pady=(0, 6))

        market_search_var = tk.StringVar(value="")
        market_division_var = tk.StringVar(value="All")
        market_source_var = tk.StringVar(value="All")
        market_filters = ttk.Frame(market_tab, style="Inset.TFrame")
        market_filters.pack(fill="x", padx=6, pady=6)
        ttk.Label(market_filters, text="Search", style="Inset.TLabel").pack(side="left", padx=(6, 3), pady=4)
        market_search = ttk.Entry(market_filters, textvariable=market_search_var, width=22)
        market_search.pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(market_filters, text="Division", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        market_division_box = ttk.Combobox(market_filters, textvariable=market_division_var, values=("All",), state="readonly", width=18)
        market_division_box.pack(side="left", padx=(0, 10), pady=4)
        ttk.Label(market_filters, text="Source", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=4)
        market_source_box = ttk.Combobox(market_filters, textvariable=market_source_var, values=("All", "Youth & Free Agents", "Flagship Prospects"), state="readonly", width=19)
        market_source_box.pack(side="left", padx=(0, 10), pady=4)
        market_count_var = tk.StringVar(value="")
        ttk.Label(market_filters, textvariable=market_count_var, style="Inset.TLabel").pack(side="right", padx=6, pady=4)

        market_tree = ttk.Treeview(
            market_tab,
            columns=("name", "source", "gender", "division", "record", "age", "rating", "potential", "pop", "cost"),
            show="headings", selectmode="browse",
        )
        for column, label, width in (
            ("name", "Athlete", 185), ("source", "Source", 130), ("gender", "G", 34), ("division", "Division", 130),
            ("record", "Record", 72), ("age", "Age", 44), ("rating", "Sport RTG", 72),
            ("potential", "Potential", 68), ("pop", "Pop", 48), ("cost", "Signing Cost", 96),
        ):
            market_tree.heading(column, text=label)
            market_tree.column(column, width=width, anchor="center")
        market_tree.column("name", anchor="w")
        market_tree.column("source", anchor="w")
        market_tree.column("division", anchor="w")
        self.make_tree_sortable(market_tree)
        market_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        market_detail_var = tk.StringVar(value="Select an athlete to review their fit and signing cost.")
        ttk.Label(market_tab, textvariable=market_detail_var, style="Inset.TLabel", justify="left").pack(fill="x", padx=8, pady=(0, 5))
        market_actions = ttk.Frame(market_tab, style="Chrome.TFrame")
        market_actions.pack(fill="x", padx=6, pady=(0, 6))

        finance_var = tk.StringVar(value="")
        ttk.Label(events_tab, textvariable=finance_var, style="Inset.TLabel", justify="left").pack(fill="x", padx=8, pady=(8, 5))
        events_body = ttk.Panedwindow(events_tab, orient="horizontal")
        events_body.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        events_panel, events_inner = self.section(events_body, "COMPLETED CARDS")
        titles_panel, titles_inner = self.section(events_body, "CHAMPIONSHIPS")
        events_body.add(events_panel, weight=3)
        events_body.add(titles_panel, weight=2)
        events_tree = ttk.Treeview(
            events_inner, columns=("date", "show", "bouts", "profit", "summary"),
            show="headings", selectmode="browse",
        )
        for column, label, width in (
            ("date", "Date", 90), ("show", "Show", 210), ("bouts", "Bouts", 52),
            ("profit", "Profit", 90), ("summary", "Summary", 330),
        ):
            events_tree.heading(column, text=label)
            events_tree.column(column, width=width, anchor="center")
        events_tree.column("show", anchor="w")
        events_tree.column("summary", anchor="w")
        self.make_tree_sortable(events_tree)
        events_tree.pack(fill="both", expand=True)
        titles_tree = ttk.Treeview(titles_inner, columns=("division", "champion", "contenders"), show="headings")
        for column, label, width in (("division", "Division", 150), ("champion", "Champion", 170), ("contenders", "Leading Contenders", 250)):
            titles_tree.heading(column, text=label)
            titles_tree.column(column, width=width, anchor="w")
        titles_tree.pack(fill="both", expand=True)

        events_controls = ttk.Frame(events_tab, style="Chrome.TFrame")
        events_controls.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(events_controls, text="Automation", style="Chrome.TLabel").pack(side="left", padx=(4, 4))
        auto_cards = ttk.Checkbutton(events_controls, text="Auto Cards", variable=auto_cards_var)
        auto_cards.pack(side="left", padx=3)
        ttk.Label(events_controls, text="Minimum bouts", style="Chrome.TLabel").pack(side="left", padx=(8, 3))
        auto_card_spin = ttk.Spinbox(events_controls, from_=1, to=14, width=4, textvariable=auto_card_minimum)
        auto_card_spin.pack(side="left", padx=(0, 8))

        def roster_members():
            names = set(division.get("roster", []))
            return [fighter for fighter in world.get("roster", []) if fighter.name in names and fighter.sport_employer == self.player_company_name and not fighter.retired]

        roster_row_fighters = {}
        athlete_row_fighters = {}
        opponent_row_fighters = {}
        market_row_fighters = {}
        event_rows = {}

        def set_status(text, tone="normal"):
            colors = {
                "normal": self.colors["text"],
                "good": "#7fd694",
                "warn": "#e2bd62",
                "bad": "#ff766d",
            }
            decision_var.set(text)
            decision_bar.config(fg=colors.get(tone, self.colors["text"]))

        def used_names():
            return {
                name
                for bout in division.get("booked_bouts", [])
                for name in (bout.get("a"), bout.get("b"))
                if name
            }

        def athlete_readiness(fighter):
            if fighter.name in used_names():
                return "Booked"
            if fighter.injured:
                return f"Injured {fighter.injured} mo"
            if fighter.fatigue >= 55:
                return f"Fatigue {fighter.fatigue}"
            wait = max(0, int(getattr(fighter, "available_week", 0) or 0) - self.calendar_week_index())
            if wait:
                return f"Available in {wait}w"
            return "Ready"

        def matchup_quality(a, b):
            gap = abs(self.combat_sport_display_rating(a, sport) - self.combat_sport_display_rating(b, sport))
            record_gap = abs((a.record_w - a.record_l) - (b.record_w - b.record_l))
            score = max(0, 100 - gap * 3.2 - min(20, record_gap * 1.4))
            if score >= 82:
                return "Excellent", round(score)
            if score >= 68:
                return "Good", round(score)
            if score >= 52:
                return "Fair", round(score)
            return "Mismatch", round(score)

        def selected_roster_fighters():
            return [roster_row_fighters[row_id] for row_id in roster_tree.selection() if row_id in roster_row_fighters]

        def selected_market_fighter():
            selected = market_tree.selection()
            return market_row_fighters.get(selected[0]) if selected else None

        def selected_matchup_fighters():
            athlete_selected = athlete_tree.selection()
            opponent_selected = opponent_tree.selection()
            a = athlete_row_fighters.get(athlete_selected[0]) if athlete_selected else None
            b = opponent_row_fighters.get(opponent_selected[0]) if opponent_selected else None
            return a, b

        def normalize_settings():
            division.setdefault("strategy", "Balanced")
            division.setdefault("revenue_total", 0)
            division.setdefault("cost_total", division.get("budget", 0))
            division.setdefault("profit_total", division.get("revenue_total", 0) - division.get("cost_total", 0))
            division.setdefault("last_card_summary", "No player card yet.")
            division.setdefault("title_name", f"{self.player_company_name} {sport} Championship")
            division.setdefault("auto_cards", False)
            division["auto_card_min_bouts"] = max(1, min(14, int(division.get("auto_card_min_bouts", 5) or 5)))
            division["card_target_bouts"] = max(1, min(14, int(division.get("card_target_bouts", 6) or 6)))
            division.setdefault("auto_card_status", "Off - manual cards only.")
            if "last_card_month" not in division:
                division["last_card_month"] = max((int(card.get("month", 0) or 0) for card in division.get("events", [])), default=0)

        def redraw():
            normalize_settings()
            auto_cards_var.set(bool(division.get("auto_cards", False)))
            auto_card_minimum.set(division["auto_card_min_bouts"])
            strategy_var.set(division.get("strategy", "Balanced"))
            target_bouts_var.set(division["card_target_bouts"])
            members = sorted(roster_members(), key=lambda fighter: (self.combat_sport_rating(fighter, sport), fighter.record_w - fighter.record_l), reverse=True)
            division["roster"] = [fighter.name for fighter in members]
            self.refresh_combat_sport_rankings(sport, world, employer=self.player_company_name, division=division)
            self.combat_sport_record_book(sport, world, self.player_company_name, True)
            champions = {name for name in division.get("titles", {}).values() if name}
            ready_count = sum(athlete_readiness(fighter) == "Ready" for fighter in members)
            summary_var.set(f"Roster {len(members)} | Ready {ready_count} | Champions {len(champions)} | Cash ${self.cash:,}")

            divisions = sorted({self.combat_sport_competition_class(sport, fighter) for fighter in members})
            roster_division_box["values"] = ["All"] + divisions
            market_division_box["values"] = ["All"] + sorted({
                label for gender in ("Male", "Female") for label, _limit in self.combat_sport_weight_ladder(sport, gender)
            })
            if roster_division_var.get() not in roster_division_box["values"]:
                roster_division_var.set("All")
            if market_division_var.get() not in market_division_box["values"]:
                market_division_var.set("All")

            current_roster_selection = roster_tree.selection()
            roster_tree.delete(*roster_tree.get_children())
            roster_row_fighters.clear()
            roster_search_text = roster_search_var.get().strip().lower()
            filtered_members = [
                fighter for fighter in members
                if (not roster_search_text or roster_search_text in fighter.name.lower())
                and (roster_division_var.get() == "All" or self.combat_sport_competition_class(sport, fighter) == roster_division_var.get())
                and (
                    roster_ready_var.get() == "All"
                    or (roster_ready_var.get() == "Ready" and athlete_readiness(fighter) == "Ready")
                    or (roster_ready_var.get() == "Booked" and athlete_readiness(fighter) == "Booked")
                    or (roster_ready_var.get() == "Unavailable" and athlete_readiness(fighter) not in ("Ready", "Booked"))
                )
            ]
            for index, fighter in enumerate(filtered_members, 1):
                rank = "C" if fighter.name in champions else index
                sport_rating = self.combat_sport_display_rating(fighter, sport)
                dev_gap = max(0, min(99, fighter.potential) - sport_rating)
                trend = self.combat_sport_rating_trend(fighter, sport, 12)
                readiness = athlete_readiness(fighter)
                row_id = f"roster:{fighter.fighter_id}"
                roster_row_fighters[row_id] = fighter
                tag = "booked" if readiness == "Booked" else ("unavailable" if readiness != "Ready" else "")
                roster_tree.insert(
                    "", "end", iid=row_id,
                    values=(rank, fighter.name, fighter.gender[:1], self.combat_sport_competition_class(sport, fighter), fighter.record, fighter.age, f"{sport_rating:.1f}", f"{trend:+.1f} / +{dev_gap:.1f}", fighter.popularity, fighter.fatigue, readiness),
                    tags=(tag,) if tag else (),
                )
            roster_count_var.set(f"Showing {len(filtered_members)} of {len(members)}")
            for row_id in current_roster_selection:
                if roster_tree.exists(row_id):
                    roster_tree.selection_add(row_id)

            member_names = {fighter.name for fighter in members}
            division["booked_bouts"] = [bout for bout in division.get("booked_bouts", []) if bout.get("a") in member_names and bout.get("b") in member_names]

            current_athlete = athlete_tree.selection()
            athlete_tree.delete(*athlete_tree.get_children())
            athlete_row_fighters.clear()
            for fighter in members:
                readiness = athlete_readiness(fighter)
                row_id = f"match:{fighter.fighter_id}"
                athlete_row_fighters[row_id] = fighter
                athlete_tree.insert(
                    "", "end", iid=row_id,
                    values=(fighter.name, self.combat_sport_competition_class(sport, fighter), fighter.record, f"{self.combat_sport_display_rating(fighter, sport):.1f}", readiness),
                    tags=("unavailable",) if readiness != "Ready" else (),
                )
            if current_athlete and athlete_tree.exists(current_athlete[0]):
                athlete_tree.selection_set(current_athlete[0])
            else:
                opponent_tree.delete(*opponent_tree.get_children())
                opponent_row_fighters.clear()

            card_tree.delete(*card_tree.get_children())
            by_name = {fighter.name: fighter for fighter in members}
            projected_draw = 0
            for index, bout in enumerate(division["booked_bouts"], 1):
                a, b = by_name.get(bout.get("a")), by_name.get(bout.get("b"))
                if not a or not b:
                    continue
                quality, score = matchup_quality(a, b)
                projected_draw += a.popularity + b.popularity
                card_tree.insert(
                    "", "end", iid=f"bout:{index - 1}",
                    values=(
                        "MAIN" if index == 1 else index,
                        f"{a.name} vs {b.name}",
                        self.combat_sport_competition_class(sport, a),
                        "TITLE" if bout.get("title") else "Bout",
                        f"{quality} {score}",
                    ),
                )
            card_summary_var.set(
                f"{len(division['booked_bouts'])}/{division.get('card_target_bouts', 6)} bouts | "
                f"{sum(1 for bout in division['booked_bouts'] if bout.get('title'))} title | "
                f"Projected draw {projected_draw}"
            )

            market_tree.delete(*market_tree.get_children())
            market_row_fighters.clear()
            youth = self.player_combat_signable_youth(sport)
            youth.sort(key=lambda fighter: (self.combat_sport_competition_class(sport, fighter), fighter.gender, -self.combat_sport_display_rating(fighter, sport)))
            prospects = [fighter for fighter in self.combat_sport_ranked(sport, world.get("promotion", ""))[10:] if fighter.sport_employer == world.get("promotion", "") and not fighter.retired]
            prospects.sort(key=lambda fighter: (fighter.age >= 20, self.combat_sport_competition_class(sport, fighter), -self.combat_sport_display_rating(fighter, sport), fighter.age))
            market_rows = [(fighter, "Youth & Free Agents", "youth") for fighter in youth]
            market_rows.extend((fighter, "Flagship Prospects", "flagship") for fighter in prospects[:max(0, 80 - len(youth))])
            market_search_text = market_search_var.get().strip().lower()
            visible_market = 0
            for fighter, source_label, source_key in market_rows:
                fighter_division = self.combat_sport_competition_class(sport, fighter)
                if market_search_text and market_search_text not in fighter.name.lower():
                    continue
                if market_division_var.get() != "All" and fighter_division != market_division_var.get():
                    continue
                if market_source_var.get() != "All" and source_label != market_source_var.get():
                    continue
                sport_rating = self.combat_sport_display_rating(fighter, sport)
                cost = max(8000, fighter.popularity * 450 + round(sport_rating) * 260)
                row_id = f"{source_key}:{fighter.fighter_id}"
                market_row_fighters[row_id] = fighter
                market_tree.insert("", "end", iid=row_id, values=(fighter.name, source_label, fighter.gender[:1], fighter_division, fighter.record, fighter.age, f"{sport_rating:.1f}", fighter.potential, fighter.popularity, f"${cost:,}"))
                visible_market += 1
            market_count_var.set(f"{visible_market} available")

            events_tree.delete(*events_tree.get_children())
            event_rows.clear()
            for index, event in enumerate(division.get("events", [])[:50]):
                finance = event.get("finance", {})
                event_rows[f"event:{index}"] = event
                events_tree.insert(
                    "", "end", iid=f"event:{index}",
                    values=(
                        self.format_game_date(event.get("month", self.month), event.get("week", 1), include_week=True),
                        event.get("event_name", f"{promotion_name} {sport} Card"),
                        len(event.get("results", [])),
                        f"${finance.get('profit', 0):,}",
                        event.get("recap", "Completed card"),
                    ),
                )
            titles_tree.delete(*titles_tree.get_children())
            for key, names in sorted(division.get("rankings_by_division", {}).items()):
                titles_tree.insert(
                    "", "end", iid=f"title:{key}",
                    values=(self.combat_sport_division_label(key), division.get("titles", {}).get(key, "") or "Vacant", ", ".join(names[:4])),
                )
            finance_var.set(
                f"Reputation {division.get('reputation', 0)} | Stability {division.get('stability', 0)} | "
                f"Lifetime revenue ${division.get('revenue_total', 0):,} | Costs ${division.get('cost_total', 0):,} | "
                f"Net ${division.get('profit_total', 0):,} | {division.get('auto_card_status', 'Auto cards off.')}"
            )

        def add_selected_matchup():
            a, b = selected_matchup_fighters()
            if not a or not b:
                set_status("Choose one athlete and one compatible opponent first.", "warn")
                return
            if athlete_readiness(a) != "Ready" or athlete_readiness(b) != "Ready":
                set_status("Both athletes must be ready and unbooked before this matchup can be added.", "bad")
                return
            key = self.combat_sport_division_key(a, sport)
            title = bool(title_var.get())
            if title and any(bout.get("title") and bout.get("title_key") == key for bout in division.get("booked_bouts", [])):
                set_status(f"A {self.combat_sport_division_label(key)} title bout is already on this card.", "bad")
                return
            champion = division.get("titles", {}).get(key, "")
            ranked = division.get("rankings_by_division", {}).get(key, [])
            if title and champion and champion not in (a.name, b.name):
                set_status(f"{champion} holds this title and must be in the championship bout.", "bad")
                return
            if title and not champion and (a.name not in ranked[:4] or b.name not in ranked[:4]):
                set_status("A vacant championship needs two of the top four ranked available athletes.", "bad")
                return
            quality, score = matchup_quality(a, b)
            division.setdefault("booked_bouts", []).append({
                "a": a.name, "b": b.name, "title": title, "title_key": key,
                "booking_reason": f"Player booked {quality.lower()} matchup ({score})",
            })
            set_status(f"Added {a.name} vs {b.name}. {quality} competitive fit ({score}/100).", "good")
            redraw()
            select_first_ready_athlete()

        def remove_booked_matchup():
            selected = card_tree.selection()
            if not selected:
                set_status("Select a bout from the running order first.", "warn")
                return
            index = int(selected[0].split(":", 1)[1])
            removed = division["booked_bouts"].pop(index)
            set_status(f"Removed {removed.get('a')} vs {removed.get('b')} from the card.")
            redraw()

        def move_booked_matchup(amount):
            selected = card_tree.selection()
            if not selected:
                set_status("Select a bout to move in the running order.", "warn")
                return
            index = int(selected[0].split(":", 1)[1])
            new_index = max(0, min(len(division["booked_bouts"]) - 1, index + amount))
            if new_index == index:
                return
            bout = division["booked_bouts"].pop(index)
            division["booked_bouts"].insert(new_index, bout)
            redraw()
            card_tree.selection_set(f"bout:{new_index}")

        def clear_card():
            if not division.get("booked_bouts"):
                set_status("The card is already empty.")
                return
            division["booked_bouts"] = []
            set_status("Card cleared. All athletes are available for matchmaking again.")
            redraw()

        def auto_fill_card():
            set_strategy()
            try:
                target = max(1, min(14, int(target_bouts_var.get())))
            except (TypeError, ValueError, tk.TclError):
                target = 6
            division["card_target_bouts"] = target
            existing = list(division.get("booked_bouts", []))
            existing_names = used_names()
            proposed = self.build_combat_sport_card(
                sport, world, self.player_company_name, player_owned=True, target_bouts=target + len(existing),
            )
            member_names = {fighter.name for fighter in roster_members()}
            added = 0
            for bout in proposed:
                if len(existing) >= target:
                    break
                a, b = bout["a"], bout["b"]
                if a.name not in member_names or b.name not in member_names:
                    continue
                if a.name in existing_names or b.name in existing_names:
                    continue
                if athlete_readiness(a) != "Ready" or athlete_readiness(b) != "Ready":
                    continue
                existing.append({
                    "a": a.name, "b": b.name, "title": bool(bout.get("title")),
                    "title_key": bout.get("title_key", self.combat_sport_division_key(a, sport)),
                    "booking_reason": bout.get("booking_reason", "Smart matchmaking"),
                })
                existing_names.update((a.name, b.name))
                added += 1
            division["booked_bouts"] = existing
            if added:
                set_status(f"Matchmaker added {added} bout(s). Review the running order, title stakes, and matchup quality before running the show.", "good")
            else:
                set_status("No additional same-division roster matchups are currently viable. Check readiness or sign more depth.", "warn")
            redraw()

        def run_booked_card():
            planned = division.get("booked_bouts", [])
            if not planned:
                set_status("Build at least one matchup before running the show.", "warn")
                return
            members = {fighter.name: fighter for fighter in roster_members()}
            bouts = []
            for bout in planned:
                a, b = members.get(bout.get("a")), members.get(bout.get("b"))
                if not a or not b:
                    set_status("A booked athlete is no longer on this roster. Remove that matchup and rebuild the card.", "bad")
                    return
                if athlete_readiness(a) not in ("Ready", "Booked") or athlete_readiness(b) not in ("Ready", "Booked"):
                    set_status(f"{a.name} vs {b.name} cannot run because an athlete is no longer ready.", "bad")
                    return
                bouts.append({
                    "a": a, "b": b, "title": bool(bout.get("title")),
                    "title_key": bout.get("title_key", self.combat_sport_division_key(a, sport)),
                    "main": not bouts, "booking_reason": bout.get("booking_reason", "Player booked matchup"),
                })
            name = event_name_var.get().strip() or f"{promotion_name} {sport} Night"
            division["next_event_name"] = name
            card = self.run_combat_sport_card(
                sport, world, self.player_company_name, player_owned=True, bouts=bouts, event_name=name,
            )
            if not card:
                set_status("The card could not be completed. The running order has been preserved for review.", "bad")
                return
            division["booked_bouts"] = []
            redraw()
            self.refresh_all()
            notebook.select(events_tab)
            finance = card.get("finance", {})
            set_status(f"{name} completed: {len(card.get('results', []))} bouts, profit ${finance.get('profit', 0):,}. Select it below to watch the replay.", "good")

        def watch_selected_card(_event=None):
            selected = events_tree.selection()
            card = event_rows.get(selected[0]) if selected else None
            if not card:
                set_status("Select a completed card first.", "warn")
                return
            package = {"event_name": card.get("event_name", f"{sport} Card"), "log": [card.get("headline", ""), card.get("recap", "")], "fight_logs": card.get("fight_logs", [])}
            if not package["fight_logs"]:
                set_status("That older card predates saved play-by-play replays.", "warn")
                return
            self.open_live_fight_window({"name": package["event_name"]}, package, apply_results=False)

        def set_strategy():
            division["strategy"] = strategy_var.get() or "Balanced"
            division["card_target_bouts"] = max(1, min(14, int(target_bouts_var.get() or 6)))

        def toggle_auto_cards():
            division["auto_cards"] = bool(auto_cards_var.get())
            division["auto_card_status"] = (
                f"On - waiting for at least {division.get('auto_card_min_bouts', 5)} viable bouts."
                if division["auto_cards"] else "Off - manual cards only."
            )
            set_status(division["auto_card_status"], "good" if division["auto_cards"] else "normal")
            redraw()

        def set_auto_card_minimum(*_args):
            try:
                required = max(1, min(14, int(auto_card_minimum.get())))
            except (TypeError, ValueError, tk.TclError):
                required = 5
            division["auto_card_min_bouts"] = required
            auto_card_minimum.set(required)
            if division.get("auto_cards", False):
                division["auto_card_status"] = f"On - waiting for at least {required} viable bouts."
            set_status(f"Automatic cards now require at least {required} viable bouts.")
            redraw()

        def sign_selected():
            selected = market_tree.selection()
            if not selected:
                set_status("Select an athlete from the market first.", "warn")
                return
            source, _, fighter_id = selected[0].partition(":")
            if source == "youth":
                ok, note, _fighter = self.sign_player_combat_youth(sport, fighter_id)
                if not ok:
                    set_status(note, "bad")
                    return
                set_status(note, "good")
                redraw()
                self.refresh_all()
                return
            fighter = next((candidate for candidate in world.get("roster", []) if candidate.fighter_id == fighter_id), None)
            if not fighter:
                return
            cost = max(8000, fighter.popularity * 450 + round(self.combat_sport_display_rating(fighter, sport)) * 260)
            if self.cash < cost:
                set_status(f"Need ${cost:,} to buy out and sign {fighter.name}.", "bad")
                return
            self.cash -= cost
            self.record_finance_transaction(f"Combat-sport signing: {fighter.name}", costs=cost)
            fighter.sport_employer = self.player_company_name
            division["roster"] = list(dict.fromkeys(division.get("roster", []) + [fighter.name]))
            fighter.fight_history = (fighter.fight_history or [])
            fighter.fight_history.insert(0, f"Month {self.month}: Signed with {self.player_company_name}'s {sport} division.")
            self.news.insert(0, f"{self.player_company_name} signed {fighter.name} to its {sport} division for ${cost:,}.")
            set_status(f"Signed {fighter.name} for ${cost:,}. They are now available in the Roster and Matchmaking workspaces.", "good")
            redraw()
            self.refresh_all()

        def show_roster_detail(_event=None):
            fighters = selected_roster_fighters()
            if not fighters:
                roster_detail_var.set("Select an athlete for contract, development, and readiness detail.")
                return
            if len(fighters) > 1:
                roster_detail_var.set(f"{len(fighters)} athletes selected. Release supports multiple selections; other actions use the first athlete.")
                return
            fighter = fighters[0]
            rating = self.combat_sport_display_rating(fighter, sport)
            stage = self.combat_sport_development_stage(fighter, sport)
            trend = self.combat_sport_rating_trend(fighter, sport, 12)
            roster_detail_var.set(
                f"{fighter.name} | {self.combat_sport_competition_class(sport, fighter)} | {stage} | "
                f"Rating {rating:.1f}, 12m {trend:+.1f}, potential {fighter.potential} | "
                f"{athlete_readiness(fighter)} | Camp: {fighter.camp_focus or 'Balanced'}"
            )

        def show_market_detail(_event=None):
            fighter = selected_market_fighter()
            if not fighter:
                market_detail_var.set("Select an athlete to review their fit and signing cost.")
                return
            rating = self.combat_sport_display_rating(fighter, sport)
            cost = max(8000, fighter.popularity * 450 + round(rating) * 260)
            runway = max(0, fighter.potential - rating)
            market_detail_var.set(
                f"{fighter.name} | {self.combat_sport_competition_class(sport, fighter)} | "
                f"Rating {rating:.1f}, potential {fighter.potential} (+{runway:.1f}), age {fighter.age}, popularity {fighter.popularity} | "
                f"Cost ${cost:,} | Cash after signing ${self.cash - cost:,}"
            )

        def refresh_opponents(_event=None):
            opponent_tree.delete(*opponent_tree.get_children())
            opponent_row_fighters.clear()
            selected = athlete_tree.selection()
            fighter = athlete_row_fighters.get(selected[0]) if selected else None
            if not fighter:
                matchup_context_var.set("Choose an athlete. Compatible opponents will appear here.")
                return
            readiness = athlete_readiness(fighter)
            key = self.combat_sport_division_key(fighter, sport)
            champion = division.get("titles", {}).get(key, "") or "Vacant"
            if readiness != "Ready":
                matchup_context_var.set(f"{fighter.name} is {readiness.lower()} and cannot be booked again on this card.")
                return
            opponents = [
                other for other in roster_members()
                if other is not fighter
                and other.gender == fighter.gender
                and self.combat_sport_competition_class(sport, other) == self.combat_sport_competition_class(sport, fighter)
                and athlete_readiness(other) == "Ready"
            ]
            opponents.sort(key=lambda other: abs(self.combat_sport_display_rating(other, sport) - self.combat_sport_display_rating(fighter, sport)))
            for other in opponents:
                quality, _score = matchup_quality(fighter, other)
                gap = abs(self.combat_sport_display_rating(other, sport) - self.combat_sport_display_rating(fighter, sport))
                row_id = f"opponent:{other.fighter_id}"
                opponent_row_fighters[row_id] = other
                opponent_tree.insert("", "end", iid=row_id, values=(other.name, other.record, f"{self.combat_sport_display_rating(other, sport):.1f}", f"{gap:.1f}", quality))
            matchup_context_var.set(
                f"{fighter.name} | {self.combat_sport_competition_class(sport, fighter)} | "
                f"Champion: {champion} | {len(opponents)} compatible ready opponent(s)"
            )
            if opponents:
                opponent_tree.selection_set(f"opponent:{opponents[0].fighter_id}")

        def select_first_ready_athlete():
            for row_id, fighter in athlete_row_fighters.items():
                if athlete_readiness(fighter) == "Ready":
                    athlete_tree.selection_set(row_id)
                    athlete_tree.see(row_id)
                    refresh_opponents()
                    return

        def set_selected_camp():
            fighters = selected_roster_fighters()
            if not fighters:
                set_status("Select an athlete from your roster first.", "warn")
                return
            self.open_fighter_camp_plan(fighters[0], on_save=redraw)

        def open_selected_roster_profile():
            fighters = selected_roster_fighters()
            if fighters:
                self.open_fighter_profile_window(fighters[0])
            else:
                set_status("Select an athlete from your roster first.", "warn")

        def open_selected_market_profile():
            fighter = selected_market_fighter()
            if fighter:
                self.open_fighter_profile_window(fighter)
            else:
                set_status("Select an athlete from the market first.", "warn")

        def move_selected_to_mma():
            fighters = selected_roster_fighters()
            if len(fighters) != 1:
                set_status("Select exactly one athlete to move into MMA.", "warn")
                return
            fighter = fighters[0]
            ok, note = self.move_player_combat_athlete_to_mma(sport, fighter)
            if not ok:
                set_status(note, "bad")
                return
            set_status(note, "good")
            redraw()
            self.refresh_all()

        def release_selected():
            fighters = selected_roster_fighters()
            if not fighters:
                set_status("Select one or more contracted athletes to release.", "warn")
                return
            champions = [fighter.name for fighter in fighters if fighter.name in set(division.get("titles", {}).values())]
            booked = [fighter.name for fighter in fighters if any(fighter.name in (bout.get("a"), bout.get("b")) for bout in division.get("booked_bouts", []))]
            warning = f"Release {len(fighters)} athlete(s) from your {sport} division?"
            if champions:
                warning += f"\n\nTitles will be vacated: {', '.join(champions)}."
            if booked:
                warning += f"\n\nTheir booked matchups will be removed: {', '.join(booked)}."
            if not messagebox.askyesno("Release Athletes", warning):
                return
            notes = []
            for fighter in fighters:
                ok, note = self.release_player_combat_athlete(sport, fighter)
                if ok:
                    notes.append(note)
            set_status(f"Released {len(notes)} athlete(s). " + (notes[-1] if notes else "No contracts changed."), "good" if notes else "warn")
            redraw()
            self.refresh_all()

        roster_search.bind("<KeyRelease>", lambda _event: redraw())
        roster_division_box.bind("<<ComboboxSelected>>", lambda _event: redraw())
        roster_ready_box.bind("<<ComboboxSelected>>", lambda _event: redraw())
        roster_tree.bind("<<TreeviewSelect>>", show_roster_detail)
        roster_tree.bind("<Double-1>", lambda _event: open_selected_roster_profile())
        ttk.Button(roster_actions, text="Open Profile", style="Accent.TButton", command=open_selected_roster_profile).pack(side="left", padx=4)
        ttk.Button(roster_actions, text="Set Camp Plan", command=set_selected_camp).pack(side="left", padx=4)
        ttk.Button(roster_actions, text="Move to MMA", command=move_selected_to_mma).pack(side="left", padx=4)
        ttk.Button(roster_actions, text="Release Selected", command=release_selected).pack(side="left", padx=4)

        athlete_tree.bind("<<TreeviewSelect>>", refresh_opponents)
        opponent_tree.bind("<Double-1>", lambda _event: add_selected_matchup())
        strategy_box.bind("<<ComboboxSelected>>", lambda _event: set_strategy())
        ttk.Button(matchup_actions, text="Add Selected Bout", style="Accent.TButton", command=add_selected_matchup).pack(side="left", padx=4)
        ttk.Button(matchup_actions, text="Auto-Fill Card", command=auto_fill_card).pack(side="left", padx=4)
        ttk.Button(matchup_actions, text="Move Up", command=lambda: move_booked_matchup(-1)).pack(side="left", padx=(14, 4))
        ttk.Button(matchup_actions, text="Move Down", command=lambda: move_booked_matchup(1)).pack(side="left", padx=4)
        ttk.Button(matchup_actions, text="Remove", command=remove_booked_matchup).pack(side="left", padx=4)
        ttk.Button(matchup_actions, text="Clear Card", command=clear_card).pack(side="left", padx=4)
        ttk.Button(matchup_actions, text="Run Show Now", style="Accent.TButton", command=run_booked_card).pack(side="right", padx=4)

        market_search.bind("<KeyRelease>", lambda _event: redraw())
        market_division_box.bind("<<ComboboxSelected>>", lambda _event: redraw())
        market_source_box.bind("<<ComboboxSelected>>", lambda _event: redraw())
        market_tree.bind("<<TreeviewSelect>>", show_market_detail)
        market_tree.bind("<Double-1>", lambda _event: open_selected_market_profile())
        ttk.Button(market_actions, text="Sign Selected", style="Accent.TButton", command=sign_selected).pack(side="left", padx=4)
        ttk.Button(market_actions, text="Open Profile", command=open_selected_market_profile).pack(side="left", padx=4)
        ttk.Button(market_actions, text="Refresh Market", command=redraw).pack(side="left", padx=4)

        auto_cards.config(command=toggle_auto_cards)
        auto_card_spin.config(command=set_auto_card_minimum)
        auto_card_spin.bind("<FocusOut>", set_auto_card_minimum)
        auto_card_spin.bind("<Return>", set_auto_card_minimum)
        self.attach_tooltip(auto_cards, "When enabled, this child promotion attempts one smart card per month. It waits if your minimum bout requirement cannot be met or a manual card is being built.")
        self.attach_tooltip(auto_card_spin, "The automatic show is cancelled unless matchmaking can build at least this many valid bouts. The setting is saved separately for each sport.")
        events_tree.bind("<Double-1>", watch_selected_card)
        ttk.Button(events_controls, text="Watch Selected Card", style="Accent.TButton", command=watch_selected_card).pack(side="left", padx=4)
        ttk.Button(events_controls, text="Records & History", command=lambda: self.open_combat_sport_history_window(sport, player_owned=True)).pack(side="left", padx=4)
        ttk.Button(events_controls, text="Refresh", command=redraw).pack(side="left", padx=4)

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4)
        redraw()
        select_first_ready_athlete()

    def open_world_chronicle(self):
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - World Chronicle")
        window.geometry("920x620")
        window.minsize(760, 500)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="WORLD CHRONICLE", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        kinds = ["All"] + sorted({entry.get("type", "World") for entry in getattr(self, "world_chronicle", [])})
        filter_var = tk.StringVar(value="All")
        controls = ttk.Frame(body, style="Panel.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        ttk.Label(controls, text="Story type", style="Panel.TLabel").pack(side="left", padx=(6, 4))
        chooser = ttk.Combobox(controls, values=kinds, textvariable=filter_var, state="readonly", width=24)
        chooser.pack(side="left")
        content = ttk.Frame(body, style="Chrome.TFrame")
        content.pack(fill="both", expand=True)
        story_list = tk.Listbox(content, width=42, font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        story_list.pack(side="left", fill="both", expand=True, padx=(0, 6))
        detail = tk.Text(content, wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        detail.pack(side="left", fill="both", expand=True)
        rows = []

        def open_context():
            selected = story_list.curselection()
            if not selected or selected[0] >= len(rows):
                return
            entry = rows[selected[0]]
            fighter = next((self.find_fighter_anywhere(name) for name in entry.get("fighters", []) if self.find_fighter_anywhere(name)), None)
            if fighter:
                self.open_fighter_profile_window(fighter)
            elif entry.get("companies"):
                company = entry["companies"][0]
                if self.select_company_by_name(company):
                    self.open_selected_company_hub()
            elif entry.get("type") in ("Event", "Independent Showcase"):
                self.select_tab("results")

        def show_story(_event=None):
            selected = story_list.curselection()
            entry = rows[selected[0]] if selected and selected[0] < len(rows) else None
            detail.config(state="normal")
            detail.delete("1.0", "end")
            if entry:
                detail.insert("end", f"{entry.get('headline', '')}\n\n{self.format_game_date_text(entry.get('detail', ''))}\n\nType: {entry.get('type', 'World')}\nDate: {self.format_game_date(entry.get('month', 1), entry.get('week', 1))}\nCompanies: {', '.join(entry.get('companies', [])) or '-'}\nFighters: {', '.join(entry.get('fighters', [])) or '-'}")
            detail.config(state="disabled")

        def render(*_):
            nonlocal rows
            rows = [entry for entry in getattr(self, "world_chronicle", []) if filter_var.get() == "All" or entry.get("type") == filter_var.get()]
            story_list.delete(0, "end")
            if not rows:
                story_list.insert("end", "No matching permanent stories yet.")
            for entry in rows:
                date = self.format_game_date(entry.get('month', 1), entry.get('week', 1))
                story_list.insert("end", f"[{entry.get('type', 'World')}] {date}\n{entry.get('headline', '')}")
            if rows:
                story_list.selection_set(0)
            show_story()
        chooser.bind("<<ComboboxSelected>>", render)
        story_list.bind("<<ListboxSelect>>", show_story)
        story_list.bind("<Double-1>", lambda _event: open_context())
        ttk.Button(body, text="Open Story Context", style="Accent.TButton", command=open_context).pack(anchor="e", pady=(6, 0))
        render()

    def selected_gym_from_tree(self):
        if not hasattr(self, "gym_tree") or not self.gym_tree.selection():
            return None
        values = self.gym_tree.item(self.gym_tree.selection()[0], "values")
        return self.gym_by_name(values[0]) if values else None

    def gym_members_with_companies(self, gym):
        members = []
        for company, fighter in self.all_database_fighters_with_companies():
            if fighter.camp == gym.name and company != "Retired":
                members.append((company, fighter))
        return sorted(members, key=lambda row: (row[1].weight, row[1].gender, -row[1].overall, row[1].name))

    def gym_development_summary(self, gym, members):
        avg_overall = round(sum(f.overall for _co, f in members) / max(1, len(members)), 1)
        prospects = sum(1 for _co, f in members if f.age < f.prime_start)
        elites = sum(1 for _co, f in members if f.overall >= 82)
        load = gym.member_count / max(1, gym.capacity)
        attention = round(self.gym_attention_multiplier(gym) * 100)
        crowd_text = "Excellent coaching access" if load < 0.7 else "Healthy coaching access" if load <= 1 else "Busy room; individual attention is reduced"
        return (
            f"Head coach: {gym.head_coach}\n"
            f"Region: {gym.city}, {gym.region}\n"
            f"Tier: {self.gym_tier(gym)} | Effective training: {self.gym_effective_training(gym)}/99 | Coaching attention: {attention}%\n"
            f"Quality: {gym.quality} | Facilities: {gym.facilities} | Reputation: {gym.reputation} | Development record: {gym.development_reputation}\n"
            f"Monthly fee: ${gym.monthly_fee:,} | Capacity: {gym.member_count}/{gym.capacity} | {crowd_text}\n"
            f"Room morale: {gym.morale} | Gym momentum: {gym.momentum:+d} | Lifetime capacity growth: +{gym.capacity_growth}\n"
            f"Specialties: {', '.join(gym.specialties)}\n\n"
            f"Tracked members: {len(members)} | Prospects: {prospects} | Elite fighters: {elites} | Average overall: {avg_overall}\n"
            f"Effective training combines coaching quality, facilities, morale, development history and available attention. Style fit then adds a fighter-specific edge.\n\n"
            f"{gym.notes}"
        )

    def open_selected_gym_viewer(self):
        gym = self.selected_gym_from_tree()
        if not gym:
            messagebox.showinfo("Gym Viewer", "Select a gym first.")
            return
        self.open_gym_viewer(gym)

    def open_gym_viewer(self, gym):
        self.sync_gym_membership()
        members = self.gym_members_with_companies(gym)
        window = tk.Toplevel(self.root)
        window.title(f"Gym Viewer - {gym.name}")
        window.geometry("1180x760")
        window.minsize(940, 620)
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=gym.name.upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text=f"{gym.city}, {gym.region}", style="ScreenTitle.TLabel", font=("Tahoma", 8)).pack(side="right", padx=10)

        badge_row = tk.Frame(window, bg=self.colors["chrome"])
        badge_row.pack(fill="x", padx=10, pady=8)
        self.profile_badge(badge_row, "Quality", gym.quality)
        self.profile_badge(badge_row, "Rep", gym.reputation)
        self.profile_badge(badge_row, "Room", gym.morale)
        self.profile_badge(badge_row, "Scout", gym.scouting)
        self.profile_badge(badge_row, "Members", f"{gym.member_count}/{gym.capacity}")

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        overview_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        roster_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        development_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        history_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(overview_tab, text="Overview")
        notebook.add(roster_tab, text="Roster")
        notebook.add(development_tab, text="Development")
        notebook.add(history_tab, text="History")

        info_panel, info = self.section(overview_tab, "GYM IDENTITY AND OPERATIONS")
        info_panel.pack(fill="both", expand=True)
        info_text = tk.Text(info, wrap="word", font=("Tahoma", 10), bg="#141414", fg="#e8e3d6", insertbackground="#e8e3d6", padx=12, pady=12, relief="flat", height=12)
        info_text.pack(fill="both", expand=True)
        info_text.insert("end", self.gym_development_summary(gym, members))
        info_text.config(state="disabled")

        filters = ttk.Frame(roster_tab, style="Chrome.TFrame")
        filters.pack(fill="x", pady=(0, 6))
        search_var = tk.StringVar(value="")
        gender_var = tk.StringVar(value="All")
        division_var = tk.StringVar(value="All")
        ttk.Label(filters, text="Search").pack(side="left", padx=(4, 3))
        search_entry = ttk.Entry(filters, textvariable=search_var, width=24)
        search_entry.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Gender").pack(side="left", padx=(0, 3))
        ttk.Combobox(filters, textvariable=gender_var, values=("All", "Male", "Female"), state="readonly", width=9).pack(side="left", padx=(0, 10))
        divisions = ["All"] + sorted({fighter.weight for _company, fighter in members})
        ttk.Label(filters, text="Division").pack(side="left", padx=(0, 3))
        ttk.Combobox(filters, textvariable=division_var, values=divisions, state="readonly", width=16).pack(side="left")

        member_panel, member_inner = self.section(roster_tab, "FIGHTERS TRAINING HERE")
        member_panel.pack(fill="both", expand=True)
        columns = ("name", "company", "gender", "weight", "age", "overall", "style", "record", "morale")
        member_tree = ttk.Treeview(member_inner, columns=columns, show="headings", height=18)
        for col, text, width in (
            ("name", "Fighter", 150), ("company", "Company", 135), ("gender", "G", 35), ("weight", "Division", 95),
            ("age", "Age", 42), ("overall", "OVR", 48), ("style", "Style", 95), ("record", "Record", 70), ("morale", "Morale", 55),
        ):
            member_tree.heading(col, text=text)
            member_tree.column(col, width=width, anchor="center")
        member_tree.column("name", anchor="w")
        member_tree.column("company", anchor="w")
        member_tree.column("style", anchor="w")
        self.make_tree_sortable(member_tree)
        member_tree.pack(fill="both", expand=True)
        def render_members(*_args):
            member_tree.delete(*member_tree.get_children())
            query = search_var.get().strip().lower()
            for company, fighter in members:
                if query and query not in fighter.name.lower() and query not in company.lower():
                    continue
                if gender_var.get() != "All" and fighter.gender != gender_var.get():
                    continue
                if division_var.get() != "All" and fighter.weight != division_var.get():
                    continue
                member_tree.insert("", "end", values=(fighter.name, company, fighter.gender[0], fighter.weight, fighter.age, fighter.overall, fighter.style, fighter.record, fighter.morale))
        render_members()
        search_var.trace_add("write", render_members)
        gender_var.trace_add("write", render_members)
        division_var.trace_add("write", render_members)
        member_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(member_tree, "name"))

        development_panel, development_inner = self.section(development_tab, "PIPELINE AND RESULTS")
        development_panel.pack(fill="both", expand=True)
        development_tree = ttk.Treeview(development_inner, columns=("name", "age", "ovr", "potential", "growth", "company", "fit"), show="headings")
        for col, label, width in (("name", "Fighter", 190), ("age", "Age", 55), ("ovr", "OVR", 60), ("potential", "Potential", 70), ("growth", "12m Growth", 85), ("company", "Company", 190), ("fit", "Gym Fit", 70)):
            development_tree.heading(col, text=label)
            development_tree.column(col, width=width, anchor="center")
        development_tree.column("name", anchor="w")
        development_tree.column("company", anchor="w")
        development_tree.pack(fill="both", expand=True)
        year = str(2026 + max(0, self.month - 1) // 12)
        prior_year = str(int(year) - 1)
        for company, fighter in sorted(members, key=lambda row: (row[1].age >= row[1].prime_start, -(row[1].potential - row[1].overall), -row[1].overall)):
            prior = (fighter.annual_overalls or {}).get(prior_year, fighter.overall)
            growth = fighter.overall - prior
            development_tree.insert("", "end", values=(fighter.name, fighter.age, fighter.overall, fighter.potential, f"{growth:+d}", company, self.gym_effective_training(gym, fighter)))
        development_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(development_tree, "name"))

        history_panel, history_inner = self.section(history_tab, "GYM TIMELINE")
        history_panel.pack(fill="both", expand=True)
        history_tree = ttk.Treeview(history_inner, columns=("date", "event", "members", "capacity", "effective", "morale", "trend"), show="headings")
        for col, label, width in (("date", "Date", 100), ("event", "Event", 360), ("members", "Members", 70), ("capacity", "Capacity", 70), ("effective", "Effective", 70), ("morale", "Morale", 65), ("trend", "Form", 60)):
            history_tree.heading(col, text=label)
            history_tree.column(col, width=width, anchor="center")
        history_tree.column("event", anchor="w")
        history_tree.pack(fill="both", expand=True)
        for entry in reversed(gym.history or []):
            history_tree.insert("", "end", values=(self.format_game_date(entry.get("month", 1), 1), entry.get("event", "Room review"), entry.get("members", "-"), entry.get("capacity", "-"), entry.get("effective", "-"), entry.get("morale", "-"), entry.get("momentum", "-")))

        controls = ttk.Frame(window, style="Header.TFrame")
        controls.pack(fill="x")
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=8, pady=6)

    def infer_news_story_type(self, headline):
        text = str(headline).lower()
        rules = (
            (("injury", "medical", "concussion"), "Medical"),
            (("signed", "contract", "free agent", "scouting", "rejected"), "Roster Market"),
            (("champion", "title", "def.", "fight", "event", "showcase", "grand prix"), "Fight News"),
            (("academy", "graduate", "amateur"), "Academy"),
            (("retire", "farewell"), "Retirement"),
            (("media", "called out", "viral", "press"), "Media"),
            (("cash", "financial", "buyout", "investor", "sponsor"), "Business"),
        )
        return next((label for words, label in rules if any(word in text for word in words)), "World News")

    def media_story_entries(self):
        """Merge rich Chronicle reports with legacy headlines without losing either.

        Older builds treated ``self.news`` as the index and only enriched an
        exact headline match.  That made detailed Chronicle-only media stories
        invisible on the Media Desk.  The Chronicle is now authoritative and
        the legacy feed is appended/deduplicated for save compatibility.
        """
        chronicle = list(getattr(self, "world_chronicle", []) or [])[:240]
        rows = []
        seen = set()

        def story_key(headline):
            return " ".join(str(headline).strip().lower().split())

        for entry in chronicle:
            row = dict(entry)
            headline = str(row.get("headline", "")).strip()
            key = story_key(headline)
            if not headline or key in seen:
                continue
            row.setdefault("type", self.infer_news_story_type(headline))
            row.setdefault("detail", headline)
            row.setdefault("companies", [])
            row.setdefault("fighters", [])
            row.setdefault("importance", 1)
            rows.append(row)
            seen.add(key)

        for headline in list(getattr(self, "news", []) or [])[:160]:
            text = str(headline).strip()
            key = story_key(text)
            if not text or key in seen:
                continue
            rows.append({
                "type": self.infer_news_story_type(text), "headline": text, "detail": text,
                "companies": [], "fighters": [], "importance": 1, "date_label": "Recent update",
            })
            seen.add(key)
        return rows[:240]

    def selected_media_story_entry(self):
        if not hasattr(self, "website_news"):
            return None
        selected = self.website_news.selection()
        if not selected:
            return None
        try:
            index = int(selected[0].split(":", 1)[1])
        except (IndexError, ValueError):
            return None
        entries = getattr(self, "_website_news_entries", [])
        return entries[index] if 0 <= index < len(entries) else None

    def story_related_entities(self, entry):
        headline = str(entry.get("headline", ""))
        fighters = list(dict.fromkeys(entry.get("fighters", []) or []))
        companies = list(dict.fromkeys(entry.get("companies", []) or []))
        if not fighters:
            lowered = f"{headline} {entry.get('detail', '')}".lower()
            fighters = [fighter.name for _company, fighter in self.all_database_fighters_with_companies()
                        if fighter.name.lower() in lowered][:8]
        if not companies:
            lowered = headline.lower()
            company_names = [self.player_company_name] + [promo.name for promo in self.promotions]
            companies = [name for name in company_names if name and name.lower() in lowered][:6]
        return fighters, companies

    def media_story_date(self, entry):
        if entry.get("date_label"):
            return entry["date_label"]
        if entry.get("month") is None:
            return "Recent update"
        return self.format_game_date(entry.get("month", 1), entry.get("week", 1))

    def show_selected_media_story(self, _event=None):
        if not hasattr(self, "website_news_preview"):
            return
        entry = self.selected_media_story_entry()
        self.website_news_preview.config(state="normal")
        self.website_news_preview.delete("1.0", "end")
        if entry:
            detail = entry.get("detail") or entry.get("headline", "")
            self.website_news_preview.insert("end", f"{entry.get('headline', '')}\n\n{detail}\n\n{self.media_story_date(entry)}")
        else:
            self.website_news_preview.insert("end", "Select a headline to preview it. Double-click or use Read Selected Story for the full report.")
        self.website_news_preview.config(state="disabled")

    def open_story_entry_context(self, entry, fighter_name="", company_name=""):
        if not entry:
            return
        fighters, companies = self.story_related_entities(entry)
        if not fighter_name and not company_name:
            related_fighters = [self.find_fighter_anywhere(name) for name in fighters]
            related_fighters = [fighter for fighter in related_fighters if fighter]
            # A fight, rivalry, or negotiation story is usually about a pair.
            # Open both profiles so the player can compare the people involved.
            if len(related_fighters) == 2:
                for related_fighter in related_fighters:
                    self.open_fighter_profile_window(related_fighter)
                return
        fighter_name = fighter_name or ((fighters[0] if fighters else "") if not company_name else "")
        company_name = company_name or (companies[0] if companies else "")
        fighter = self.find_fighter_anywhere(fighter_name) if fighter_name else None
        if fighter:
            self.open_fighter_profile_window(fighter)
            return
        if company_name and self.select_company_by_name(company_name):
            self.open_selected_company_hub()
            return
        story_type = entry.get("type", "")
        text = f"{entry.get('headline', '')} {entry.get('detail', '')}".lower()
        if story_type in ("Event", "Independent Showcase", "Title Change", "Fight News") or any(word in text for word in ("event", "def.", "title fight", "showcase")):
            self.select_tab("results")
        elif story_type in ("Major Signing", "Regional Breakthrough", "Roster Market") or any(word in text for word in ("signed", "contract", "free agent", "scouting")):
            self.select_tab("market")
        else:
            self.select_tab("world")

    def open_story_reader(self, entry=None, entry_index=None):
        entries = getattr(self, "_website_news_entries", [])
        if entry is None:
            entry = self.selected_media_story_entry()
        if not entry:
            messagebox.showinfo("Media Desk", "Select a news story first.")
            return
        if entry not in entries:
            # World Hub and Chronicle can reuse the reader without incorrectly
            # navigating into the separate Media Desk headline list.
            entries = []
        if entry_index is None:
            try:
                entry_index = entries.index(entry)
            except ValueError:
                entry_index = 0
        existing = getattr(self, "_news_reader_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.destroy()
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        self._news_reader_window = window
        window.title("MMA Warriors - News Story")
        screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
        width = min(860, max(650, screen_w - 100)); height = min(620, max(470, screen_h - 150))
        window.geometry(f"{width}x{height}+{max(0, (screen_w-width)//2)}+{max(0, (screen_h-height)//3)}")
        window.minsize(min(650, width), min(470, height)); window.configure(bg=self.colors["chrome"])
        state = {"index": max(0, min(len(entries) - 1, entry_index)) if entries else 0, "entry": entry}
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 4))
        type_label = ttk.Label(header, style="ScreenTitle.TLabel"); type_label.pack(side="left", padx=10, pady=5)
        date_label = ttk.Label(header, style="ScreenTitle.TLabel"); date_label.pack(side="right", padx=10, pady=5)
        headline_label = ttk.Label(window, style="Section.TLabel", justify="left", anchor="w", wraplength=max(560, width - 45))
        headline_label.pack(fill="x", padx=8, pady=(0, 4))
        body_frame = ttk.Frame(window, style="Panel.TFrame"); body_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        body = tk.Text(body_frame, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], font=("Tahoma", 10), padx=14, pady=12)
        body_scroll = ttk.Scrollbar(body_frame, orient="vertical", command=body.yview); body.configure(yscrollcommand=body_scroll.set)
        body.pack(side="left", fill="both", expand=True); body_scroll.pack(side="right", fill="y")
        related = ttk.Frame(window, style="Inset.TFrame"); related.pack(fill="x", padx=8, pady=(0, 5))
        related.columnconfigure(1, weight=1); related.columnconfigure(4, weight=1)
        fighter_var = tk.StringVar(); company_var = tk.StringVar()
        ttk.Label(related, text="Fighter", style="Inset.TLabel").grid(row=0, column=0, padx=(5, 3), pady=4)
        fighter_combo = ttk.Combobox(related, textvariable=fighter_var, state="readonly")
        fighter_combo.grid(row=0, column=1, sticky="ew", padx=3, pady=4)
        fighter_button = ttk.Button(related, text="Open Fighter")
        fighter_button.grid(row=0, column=2, padx=3, pady=4)
        ttk.Label(related, text="Company", style="Inset.TLabel").grid(row=0, column=3, padx=(10, 3), pady=4)
        company_combo = ttk.Combobox(related, textvariable=company_var, state="readonly")
        company_combo.grid(row=0, column=4, sticky="ew", padx=3, pady=4)
        company_button = ttk.Button(related, text="Open Company")
        company_button.grid(row=0, column=5, padx=3, pady=4)
        footer = ttk.Frame(window, style="Chrome.TFrame"); footer.pack(fill="x", padx=8, pady=(0, 8))
        previous_button = ttk.Button(footer, text="Previous Story")
        previous_button.pack(side="left", padx=3)
        next_button = ttk.Button(footer, text="Next Story")
        next_button.pack(side="left", padx=3)
        context_button = ttk.Button(footer, text="Open Best Context", style="Accent.TButton")
        context_button.pack(side="left", padx=8)
        ttk.Button(footer, text="World Chronicle", command=self.open_world_chronicle).pack(side="right", padx=3)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=3)

        def render():
            current = state["entry"]
            type_label.config(text=str(current.get("type", "World News")).upper())
            date_label.config(text=self.media_story_date(current))
            headline_label.config(text=current.get("headline", "Untitled story"), wraplength=max(560, window.winfo_width() - 45))
            detail = str(current.get("detail") or "").strip()
            headline = str(current.get("headline", "")).strip()
            body.config(state="normal"); body.delete("1.0", "end")
            if detail and detail != headline:
                body.insert("end", detail)
            else:
                body.insert("end", headline + "\n\nThis is a live world news brief. Use the related links below to inspect the people, company, market, or results behind it.")
            fighters, companies = self.story_related_entities(current)
            if fighters or companies:
                body.insert("end", f"\n\nRELATED\nFighters: {', '.join(fighters) or '-'}\nCompanies: {', '.join(companies) or '-'}")
            body.config(state="disabled"); body.yview_moveto(0)
            fighter_combo["values"] = fighters; fighter_var.set(fighters[0] if fighters else "")
            company_combo["values"] = companies; company_var.set(companies[0] if companies else "")
            fighter_button.state(["!disabled"] if fighters else ["disabled"])
            company_button.state(["!disabled"] if companies else ["disabled"])
            context_button.config(text="Open Both Fighters" if len(fighters) == 2 else "Open Best Context")
            previous_button.state(["!disabled"] if entries and state["index"] > 0 else ["disabled"])
            next_button.state(["!disabled"] if entries and state["index"] < len(entries) - 1 else ["disabled"])

        def move(amount):
            if not entries:
                return
            state["index"] = max(0, min(len(entries) - 1, state["index"] + amount))
            state["entry"] = entries[state["index"]]
            iid = f"story:{state['index']}"
            if hasattr(self, "website_news") and self.website_news.exists(iid):
                self.website_news.selection_set(iid); self.website_news.see(iid); self.show_selected_media_story()
            render()

        previous_button.config(command=lambda: move(-1)); next_button.config(command=lambda: move(1))
        fighter_button.config(command=lambda: self.open_story_entry_context(state["entry"], fighter_name=fighter_var.get()))
        company_button.config(command=lambda: self.open_story_entry_context(state["entry"], company_name=company_var.get()))
        context_button.config(command=lambda: self.open_story_entry_context(state["entry"]))
        window.bind("<Left>", lambda _event: move(-1)); window.bind("<Right>", lambda _event: move(1))
        window.protocol("WM_DELETE_WINDOW", lambda: (setattr(self, "_news_reader_window", None), window.destroy()))
        window.after_idle(render)

    def open_selected_news_story(self):
        entry = self.selected_media_story_entry()
        selected = self.website_news.selection() if hasattr(self, "website_news") else ()
        index = int(selected[0].split(":", 1)[1]) if selected else 0
        self.open_story_reader(entry, index)

    def refresh_website(self):
        names = [fighter.name for fighter in sorted(self.roster, key=lambda fighter: (fighter.media_presence, fighter.popularity), reverse=True)]
        if hasattr(self, "media_fighter_combo"):
            self.media_fighter_combo.configure(values=names)
            if self.media_fighter_choice.get() not in names and names:
                self.media_fighter_choice.set(names[0])
            self.refresh_media_targets()
        featured = self.news[0] if self.news else "No major stories today."
        upcoming = self.sorted_scheduled_events()
        for promo in self.promotions:
            if promo.show_history:
                pass
        self.website_story.config(state="normal")
        self.website_story.delete("1.0", "end")
        top_p4p = sorted(self.roster, key=lambda f: self.p4p_value(f), reverse=True)[:5]
        champions = [f"{f.gender} {f.weight}: {f.name}" for f in self.roster if f.champion]
        self.website_story.insert("end", f"Result: {featured}\n\nPound-for-pound leaders: {', '.join(f.name for f in top_p4p)}.\n\nCurrent champions: {', '.join(champions) if champions else 'No champions crowned'}.\n\nThe MMA world is active across {len(self.promotions)} major companies, {len(self.free_agents)} ranked free agents, and {sum(len(p.roster) for p in self.promotions)} contracted rival fighters.")
        self.website_story.config(state="disabled")
        self.website_calendar.config(state="normal")
        self.website_calendar.delete("1.0", "end")
        if upcoming:
            for event in upcoming[:12]:
                self.website_calendar.insert("end", f"> {event['name']} ({event['venue']}, {self.event_date_label(event)})\n")
        else:
            self.website_calendar.insert("end", f"> No {self.player_company_name} events scheduled.\n")
        for promo in sorted(self.promotions, key=lambda p: -p.reputation_score)[:6]:
            if promo.show_history:
                self.website_calendar.insert("end", f"> {self.format_game_date_text(promo.show_history[0])}\n")
        self.website_calendar.config(state="disabled")
        selected_headline = ""
        if self.website_news.selection():
            values = self.website_news.item(self.website_news.selection()[0], "values")
            selected_headline = values[1] if len(values) > 1 else ""
        self.website_news.delete(*self.website_news.get_children())
        self._website_news_entries = self.media_story_entries()
        for index, entry in enumerate(self._website_news_entries):
            iid = f"story:{index}"
            date = self.media_story_date(entry)
            if date.startswith(str(entry.get("year", ""))) and entry.get("month") is not None:
                date = self.format_game_date(entry.get("month"), entry.get("week"))
            self.website_news.insert("", "end", iid=iid, values=(entry.get("type", "World News"), entry.get("headline", ""), date))
            if entry.get("headline") == selected_headline:
                self.website_news.selection_set(iid)
        if self._website_news_entries and not self.website_news.selection():
            self.website_news.selection_set("story:0")
        self.show_selected_media_story()
        if hasattr(self, "refresh_media_dashboard"):
            self.refresh_media_dashboard()

    def media_desk_fighter(self):
        name = self.media_fighter_choice.get() if hasattr(self, "media_fighter_choice") else ""
        return next((fighter for fighter in self.roster if fighter.name == name), None)

    def open_selected_story_context(self):
        self.open_story_entry_context(self.selected_media_story_entry())

    def refresh_media_targets(self, _event=None):
        if not hasattr(self, "media_target_combo"):
            return
        speaker = self.media_desk_fighter()
        targets = [fighter.name for fighter in self.roster if speaker and fighter.name != speaker.name
                   and fighter.gender == speaker.gender and fighter.weight == speaker.weight]
        self.media_target_combo.configure(values=targets)
        if self.media_target_choice.get() not in targets:
            self.media_target_choice.set(targets[0] if targets else "")

    def legacy_media_desk_callout(self):
        fighter = self.media_desk_fighter()
        target = self.get_fighter(self.media_target_choice.get()) if hasattr(self, "media_target_choice") and self.media_target_choice.get() else None
        if not fighter or not target or fighter.gender != target.gender or fighter.weight != target.weight:
            messagebox.showinfo("Media Desk", "Choose a spokesperson and a same-division target.")
            return
        fighter.rival, target.rival = target.name, fighter.name
        heat = 10 + round(self.staff_effect("Marketing", 0.7))
        fighter.media_heat = min(100, fighter.media_heat + heat)
        target.media_heat = min(100, target.media_heat + max(6, heat - 3))
        fighter.popularity = min(100, fighter.popularity + 1)
        headline = f"{fighter.name} calls out {target.name}."
        self.news.insert(0, headline)
        self.record_world_story("Media", headline, f"The {fighter.weight} rivalry is now active.", [self.player_company_name], [fighter.name, target.name], 2)
        self.refresh_all()

    def legacy_media_desk_interview(self):
        fighter = self.media_desk_fighter()
        if not fighter:
            messagebox.showinfo("Media Desk", "Choose a spokesperson first.")
            return
        upside = fighter.media_presence + fighter.charisma + self.staff_effect("Marketing", 1.2) * 4 + random.randint(-28, 24)
        if upside >= 110:
            fighter.media_heat = min(100, fighter.media_heat + random.randint(7, 14))
            fighter.popularity = min(100, fighter.popularity + random.randint(1, 3))
            text = f"{fighter.name}'s interview lands well and builds their profile."
        else:
            fighter.media_heat = max(0, fighter.media_heat - 3)
            text = f"{fighter.name}'s interview fails to generate much attention."
        self.news.insert(0, text)
        self.refresh_all()

    def legacy_media_desk_press_tour(self):
        fighter = self.media_desk_fighter()
        if not fighter:
            messagebox.showinfo("Media Desk", "Choose a spokesperson first.")
            return
        cost = 7_500 + max(0, fighter.popularity - 40) * 180
        if self.cash < cost:
            messagebox.showwarning("Media Desk", f"A press tour for {fighter.name} costs ${cost:,}.")
            return
        self.cash -= cost
        self.record_finance_transaction(f"Press tour: {fighter.name}", costs=cost)
        impact = max(2, round((fighter.media_presence + fighter.charisma + self.staff_skill("Marketing")) / 42))
        old_popularity, old_morale = fighter.popularity, fighter.morale
        fighter.media_heat = min(100, fighter.media_heat + impact * 3)
        fighter.popularity = min(100, fighter.popularity + max(1, impact // 2))
        fighter.morale = min(100, fighter.morale + 2)
        if fighter.popularity != old_popularity:
            self.record_change("Popularity", fighter.name, fighter.popularity - old_popularity, "Press-tour exposure and media performance")
        if fighter.morale != old_morale:
            self.record_change("Morale", fighter.name, fighter.morale - old_morale, "Featured role on the company press tour")
        headline = f"{fighter.name} begins a ${cost:,} press tour."
        self.news.insert(0, headline)
        self.record_world_story("Media", headline, f"Media heat +{impact * 3}; popularity +{max(1, impact // 2)}.", [self.player_company_name], [fighter.name], 2)
        self.refresh_all()

    def refresh_assistant(self):
        upcoming = self.sorted_scheduled_events()
        self.assistant_messages.delete(*self.assistant_messages.get_children())
        if hasattr(self, "assistant_changes"):
            self.assistant_changes.delete(*self.assistant_changes.get_children())
        messages = []
        if getattr(self, "spectator_mode", False):
            active_promos = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)]
            distressed = [promo for promo in active_promos if promo.cash < 0 or promo.stability < 28]
            latest = (getattr(self, "result_records", []) or [{}])[0]
            latest_text = latest.get("event", "No world event has been recorded yet")
            snapshot = (
                f"{self.format_game_date()}  |  WORLD SIMULATION\n"
                f"Promotions {len(active_promos)}  |  Free agents {len([f for f in self.free_agents if not f.retired])}  |  "
                f"Financial distress {len(distressed)}  |  Latest result: {latest_text}"
            )
            if distressed:
                messages.append(("!", f"{len(distressed)} promotion(s) are financially unstable; inspect company health and roster cuts.", "companies", "urgent"))
            messages.append(("•", "Review the latest cards, rankings and movement across the simulated world.", "results", "normal"))
            stories = list(getattr(self, "world_chronicle", []))[-4:]
            for story in reversed(stories):
                headline = story.get("headline", "World development") if isinstance(story, dict) else str(story)
                messages.append(("•", headline, "world", "normal"))
        else:
            expiring = [fighter for fighter in self.roster if fighter.contract_months <= 3]
            unavailable = [
                fighter for fighter in self.roster
                if fighter.injured or fighter.fatigue >= 65 or not self.fighter_available_for_date(fighter, self.month, self.week)
            ]
            medical_decisions = [fighter for fighter in self.roster if getattr(fighter, "serious_injury_pending", False)]
            completed_scouting = [
                (report.get("fighter_name", fighter_id), report) for fighter_id, report in getattr(self, "scouting_reports", {}).items()
                if report.get("status") == "Complete" or report.get("reveal", 0) >= 100
            ]
            active_scouting = [report for report in getattr(self, "scouting_reports", {}).values() if report.get("status") == "In progress"]
            active_scouting += [search for search in getattr(self, "scouting_searches", []) if search.get("status") == "In progress"]
            payroll = sum(member.get("salary", 0) for member in self.staff)
            monthly_burn = max(1, self.finance.get("monthly_office", 0) + payroll + (self.academy.get("weekly_cost", 0) * 4 if self.academy.get("owned") else 0))
            runway = self.cash / monthly_burn
            next_event = upcoming[0] if upcoming else None
            if next_event:
                fights = next_event.get("fights", [])
                tba = sum("TBA" in self.event_fight_participants(fight) for fight in fights)
                main_ready = any(fight.get("main") for fight in fights)
                event_line = f"Next: {next_event['name']} - {self.event_date_label(next_event)} - {len(fights)} fights - {tba} TBA"
                if len(fights) < 6:
                    messages.append(("!", f"{next_event['name']} only has {len(fights)} fights; depth will hurt its commercial and critical ceiling.", "booking", "urgent"))
                if not main_ready:
                    messages.append(("!", f"{next_event['name']} has no declared main event.", "booking", "urgent"))
                if tba:
                    messages.append(("!", f"{next_event['name']} has {tba} unresolved TBA position(s).", "booking", "urgent"))
            else:
                event_line = "Next: no event scheduled"
                messages.append(("!", "No future event is scheduled; revenue and audience momentum will stall.", "booking", "urgent"))
            snapshot = (
                f"{self.format_game_date()}  |  {self.player_company_name}\n"
                f"{event_line}\n"
                f"Cash ${self.cash:,}  |  Fixed-cost runway {runway:.1f} months  |  Popularity {self.company_pop}  |  Stability {self.company_stability}  |  "
                f"Urgent contracts {len(expiring)}  |  Unavailable fighters {len(unavailable)}"
            )
            for fighter in sorted(expiring, key=lambda row: row.contract_months)[:6]:
                champion = " Champion." if fighter.champion else ""
                messages.append(("!", f"{fighter.name}'s contract expires in {fighter.contract_months} month(s).{champion}", "contracts", "urgent"))
            for fighter in unavailable[:5]:
                if fighter.injured:
                    problem = f"injured for {fighter.injured} month(s)"
                elif not self.fighter_available_for_date(fighter, self.month, self.week):
                    problem = self.fighter_return_label(fighter).lower()
                else:
                    problem = f"fatigue {fighter.fatigue}"
                messages.append(("!", f"{fighter.name} is unavailable: {problem}.", "roster", "urgent"))
            division_counts = {}
            for fighter in self.roster:
                if not fighter.retired:
                    division_counts[(fighter.gender, fighter.weight)] = division_counts.get((fighter.gender, fighter.weight), 0) + 1
            active_genders = sorted({fighter.gender for fighter in self.roster if not fighter.retired}) or ["Male"]
            for gender in active_genders:
                for weight in self.weight_classes:
                    if self.belt_key(gender, weight) in set(getattr(self, "closed_divisions", set())):
                        continue
                    division_counts.setdefault((gender, weight), 0)
            thin = sorted((
                (count, gender, weight) for (gender, weight), count in division_counts.items()
                if count < 6 and self.belt_key(gender, weight) not in set(getattr(self, "closed_divisions", set()))
            ))
            for count, gender, weight in thin[:5]:
                messages.append(("•", f"{gender} {weight} has only {count} active fighters; matchmaking depth is fragile.", "market", "normal"))
            current_belts = self.normalize_belts(getattr(self, "belts", {}))
            vacant_titles = [
                (gender, weight) for (gender, weight), count in division_counts.items()
                if count >= 2
                and self.belt_key(gender, weight) not in set(getattr(self, "closed_divisions", set()))
                and not current_belts.get(self.belt_key(gender, weight), "")
            ]
            for gender, weight in vacant_titles[:6]:
                messages.append(("!", f"The {gender} {weight} championship is vacant. Book a title fight to crown a champion.", "booking", "urgent"))
            for name, report in completed_scouting[:4]:
                notes = "; ".join(report.get("notes", [])) or "A report is ready for review."
                messages.append(("•", f"Scouting complete: {name}. {notes}", "scouting", "normal"))
            for report in sorted(active_scouting, key=lambda item: item.get("weeks_remaining", 99))[:3]:
                if report.get("weeks_remaining", 99) <= 1:
                    target = report.get("fighter_name") or report.get("region", "regional search")
                    messages.append(("•", f"Scouting update due this week: {target} via {report.get('scout', 'staff')}.", "scouting", "normal"))
            idle_scouts = [member for member in self.staff if member.get("role") == "Scout" and self.scout_workload(member.get("name")) == 0]
            if idle_scouts:
                messages.append(("•", f"{len(idle_scouts)} scout(s) have no active assignment.", "scouting", "normal"))
            for fighter in medical_decisions[:3]:
                messages.append(("!", f"Medical decision required for {fighter.name}: {self.serious_injury_status(fighter)}.", "inbox", "urgent"))
            if runway < 4:
                messages.append(("!", f"Only {runway:.1f} months of fixed-cost runway remain at the present balance.", "finance", "urgent"))
            if hasattr(self, "assistant_kpis"):
                show_value = self.event_date_label(next_event) if next_event else "NOT SCHEDULED"
                card_value = f"{len(next_event.get('fights', []))} bouts / {tba} TBA" if next_event else "ACTION REQUIRED"
                values = {
                    "show": show_value,
                    "card": card_value,
                    "contracts": f"{len(expiring)} urgent",
                    "divisions": f"{len(thin)} thin",
                    "runway": f"{runway:.1f} months",
                    "medical": f"{len(unavailable)} unavailable",
                }
                warnings = {
                    "contracts": bool(expiring), "divisions": bool(thin), "medical": bool(unavailable),
                    "runway": runway < 4, "card": bool(next_event and (tba or len(next_event.get("fights", [])) < 6)),
                    "show": next_event is None,
                }
                for key, value in values.items():
                    self.assistant_kpis[key].config(text=value, fg="#ff9b9b" if warnings.get(key) else self.colors["text"])
        if getattr(self, "spectator_mode", False) and hasattr(self, "assistant_kpis"):
            latest = (getattr(self, "result_records", []) or [{}])[0]
            spectator_values = {
                "show": "WORLD SIM", "card": latest.get("fight_count", "-") and f"{latest.get('fight_count', '-')} latest bouts",
                "contracts": "N/A", "divisions": "WORLDWIDE", "runway": "N/A", "medical": "WORLD FEED",
            }
            for key, value in spectator_values.items():
                self.assistant_kpis[key].config(text=value, fg=self.colors["text"])
        self.assistant_snapshot.config(text=snapshot)
        if not messages:
            messages.append(("•", "No urgent issues. The company is ready for normal booking.", "booking", "normal"))
        self._assistant_messages = messages[:20]
        for index, (priority, message, action, tag) in enumerate(self._assistant_messages):
            self.assistant_messages.insert("", "end", iid=str(index), tags=(tag,), values=(priority, message, action.title()))

        if hasattr(self, "assistant_changes"):
            journal = getattr(self, "change_journal", [])
            changes = [entry for entry in reversed(journal) if entry.get("month") == self.month and entry.get("week") == self.week]
            if not changes:
                changes = list(reversed(journal[-20:]))
            if getattr(self, "spectator_mode", False):
                changes = []
                for record in (getattr(self, "result_records", []) or [])[:12]:
                    changes.append({"date": self.format_game_date_text(record.get("date", "")), "category": "Event", "subject": record.get("company", "World"), "delta": "Card", "reason": record.get("event", record.get("summary", "World event completed"))})
            if not changes:
                self.assistant_changes.insert("", "end", values=(self.format_game_date(), "No recorded changes", "Advance the world or complete an event to begin the attributed report."))
            for entry in changes[:16]:
                delta = entry.get("delta", 0)
                if entry.get("category") == "Finance" and isinstance(delta, (int, float)):
                    delta_text = f"{delta:+,.0f} cash"
                elif isinstance(delta, (int, float)):
                    delta_text = f"{delta:+g} {entry.get('category', 'Change').lower()}"
                else:
                    delta_text = f"{entry.get('category', 'Change')}: {delta}"
                change_text = f"{entry.get('subject', '')}: {delta_text}"
                self.assistant_changes.insert("", "end", values=(self.format_game_date_text(entry.get("date", "")), change_text, self.format_game_date_text(entry.get("reason", ""))))

    def open_selected_assistant_notice(self):
        selected = self.assistant_messages.selection() if hasattr(self, "assistant_messages") else []
        if not selected:
            return
        try:
            _priority, _message, action, _tag = self._assistant_messages[int(selected[0])]
        except (AttributeError, IndexError, ValueError):
            return
        self.select_tab(action)

    def open_selected_region_hub(self, focus="Overview"):
        if not hasattr(self, "region_list") or not self.region_list.curselection():
            return
        region = self.region_list.get(self.region_list.curselection()[0])
        data = self.regions[region]
        window = tk.Toplevel(self.root)
        window.title(f"MMA Warriors - {region} Region Hub")
        window.geometry("980x620")
        window.configure(bg=self.colors["chrome"])
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        tabs = {name: ttk.Frame(notebook, style="Chrome.TFrame") for name in ("Overview", "Fighters", "Gyms", "Events", "Market")}
        for name, tab in tabs.items(): notebook.add(tab, text=name)
        overview = tk.Text(tabs["Overview"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        overview.pack(fill="both", expand=True)
        benefit = data.get("promo_benefit", {})
        overview.insert("end", f"{region}\n\nAreas: {', '.join(data['areas'])}\nEconomy: {data['economy']}\nMMA legality: {data['legality']}\nDrug-testing accuracy: {data['drug_accuracy']}%\nMMA interest: {data.get('mma_love', 50)}%\nFan identity: {data.get('fan_identity', 'Local MMA community')}\nCrowd preference: {data.get('crowd_preference', 'Competitive fights')}\n\nPromotion effects: media x{benefit.get('media', 1.0)}, gate x{benefit.get('gate', 1.0)}, morale {benefit.get('morale', 0):+}.\n\nTeams: {', '.join(data['teams'])}\nLast major show: {data['last_major_show']}")
        overview.config(state="disabled")
        local = [(company, fighter) for company, fighter in self.all_database_fighters_with_companies() if fighter.region == region]
        fighter_tree = ttk.Treeview(tabs["Fighters"], columns=("name", "company", "division", "record", "ovr"), show="headings")
        for col, label, width in (("name", "Fighter", 210), ("company", "Company", 190), ("division", "Division", 130), ("record", "W-L-D", 90), ("ovr", "OVR", 60)):
            fighter_tree.heading(col, text=label); fighter_tree.column(col, width=width, anchor="center")
        fighter_tree.column("name", anchor="w")
        region_fighter_rows = {}
        for row_index, (company, fighter) in enumerate(sorted(local, key=lambda row: -self.p4p_value(row[1]))):
            row_id = self.fighter_tree_row_id("region", fighter, row_index)
            region_fighter_rows[row_id] = fighter
            fighter_tree.insert("", "end", iid=row_id, values=(fighter.name, company, fighter.weight, fighter.record, fighter.overall))
        fighter_tree.pack(fill="both", expand=True, padx=8, pady=8)
        fighter_tree.bind("<Double-1>", lambda _e: self.open_fighter_profile_window(region_fighter_rows.get(fighter_tree.selection()[0])) if fighter_tree.selection() else None)
        gym_list = tk.Listbox(tabs["Gyms"], font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        gyms = [gym for gym in self.gyms if gym.region == region]
        for gym in gyms: gym_list.insert("end", f"{gym.name} — {gym.city} | Q{gym.quality} | {', '.join(gym.specialties)}")
        gym_list.pack(fill="both", expand=True, padx=8, pady=8)
        gym_list.bind("<Double-1>", lambda _e: self.open_gym_viewer(gyms[gym_list.curselection()[0]]) if gym_list.curselection() else None)
        event_list = tk.Listbox(tabs["Events"], font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"])
        events = [event for event in self.scheduled_events if self.venue_region(event.get("venue", "")) == region]
        for event in events: event_list.insert("end", f"{event['name']} — {self.event_date_label(event)} — {event.get('venue', '')}")
        event_list.insert("end", "No player events scheduled here." if not events else "")
        event_list.pack(fill="both", expand=True, padx=8, pady=8)
        market = tk.Text(tabs["Market"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        market.pack(fill="both", expand=True, padx=8, pady=8)
        local_promos = [promo.name for promo in self.promotions if promo.region == region]
        market.insert("end", f"Local promotions: {', '.join(local_promos) if local_promos else 'No rival promotion headquartered here.'}\n\nFree agents based here: {len([fighter for fighter in self.free_agents if fighter.region == region])}\nRegional gyms: {len(gyms)}\n\nUse the Fighters and Gyms tabs to inspect the local talent pathway.")
        market.config(state="disabled")
        notebook.select(tabs.get(focus, tabs["Overview"]))

    def open_selected_staff_profile(self, candidate=False):
        tree = self.staff_candidate_tree if candidate else self.staff_tree
        selected = tree.selection() if hasattr(tree, "selection") else []
        if not selected:
            return
        pool = self.staff_candidates if candidate else self.staff
        try: member = pool[int(selected[0])]
        except (IndexError, ValueError): return
        scout_detail = ""
        if member.get("role") == "Scout":
            scout_detail = "\n\nSCOUTING\n" + "\n".join(f"{label}: {member.get(key, member['skill'])}" for key, label in (("fighter_judging", "Fighter judging"), ("potential_judging", "Potential judging"), ("efficiency", "Efficiency"), ("regional_knowledge", "Regional knowledge"), ("networking", "Networking"), ("reliability", "Reliability"), ("negotiation", "Negotiation"), ("professionalism", "Professionalism")))
        messagebox.showinfo("Staff Profile", f"{member['name']}\n\nRole: {member['role']}\nSkill: {member['skill']}\nMorale: {member['morale']}\nSalary: ${member['salary']:,}/month\nSpecialty: {member.get('specialty', 'Operations')}\nReputation: {member.get('reputation', 50)}" + scout_detail)

    def _open_academy_window_legacy(self):
        academy = self.academy
        if not academy.get("owned"):
            cost = 180000
            if messagebox.askyesno("Fighting Academy", f"Open a fighting academy for ${cost:,}? It begins with 8 places and $4,500 weekly costs. Youths must be scouted before they appear."):
                if self.cash < cost: messagebox.showwarning("Academy", "Not enough cash."); return
                self.cash -= cost; academy.update(self.academy_defaults()); academy.update({"owned": True, "level": 1, "capacity": 8, "weekly_cost": 4500, "build_spend": cost, "last_scout_report": "Hire or use a Scout to establish a regional youth network."}); self.record_finance_transaction("Build Fighting Academy", costs=cost); self.refresh_all()
            return
        self.repair_academy(academy)
        window = tk.Toplevel(self.root); window.title("MMA Warriors - Fighting Academy"); window.geometry("1240x760"); window.minsize(960, 600); window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="FIGHTING ACADEMY", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=8)
        status = ttk.Label(window, style="Inset.TLabel"); status.pack(fill="x", padx=10)
        report = ttk.Label(window, style="Inset.TLabel", wraplength=1060); report.pack(fill="x", padx=10, pady=(4, 0))
        network = ttk.Frame(window, style="Chrome.TFrame"); network.pack(fill="x", padx=10, pady=6)
        scout_names = [member.get("name", "") for member in self.staff if member.get("role") == "Scout"] or ["Staff Scout"]
        scout_var = tk.StringVar(value=academy.get("network_scout") or scout_names[0])
        region_var = tk.StringVar(value=academy.get("network_region") or self.player_region)
        philosophy_var = tk.StringVar(value=academy.get("philosophy", "Balanced MMA"))
        ttk.Label(network, text="Scout", style="Chrome.TLabel").pack(side="left", padx=(4, 2))
        ttk.Combobox(network, values=scout_names, textvariable=scout_var, state="readonly", width=22).pack(side="left", padx=3)
        ttk.Label(network, text="Region", style="Chrome.TLabel").pack(side="left", padx=(12, 2))
        ttk.Combobox(network, values=REGIONS, textvariable=region_var, state="readonly", width=18).pack(side="left", padx=3)
        ttk.Label(network, text="Philosophy", style="Chrome.TLabel").pack(side="left", padx=(12, 2))
        ttk.Combobox(network, values=("Balanced MMA", "Striking Academy", "Wrestling Pipeline", "Submission School", "Athletic Development", "Multi-Sport Pathway"), textvariable=philosophy_var, state="readonly", width=21).pack(side="left", padx=3)
        network_actions = ttk.Frame(window, style="Chrome.TFrame"); network_actions.pack(fill="x", padx=10, pady=(0, 3))
        body = ttk.Panedwindow(window, orient="horizontal"); body.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(body, style="Panel.TFrame"); right = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=1); body.add(right, weight=2)
        ttk.Label(left, text="RECRUITMENT LEADS", style="Section.TLabel").pack(fill="x")
        talent_frame = ttk.Frame(left, style="Panel.TFrame"); talent_frame.pack(fill="both", expand=True, padx=8, pady=8)
        talent = tk.Listbox(talent_frame, width=52, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        talent_x = ttk.Scrollbar(talent_frame, orient="horizontal", command=talent.xview); talent.configure(xscrollcommand=talent_x.set)
        talent.pack(fill="both", expand=True); talent_x.pack(fill="x")
        ttk.Label(right, text="SIGNED PROSPECTS", style="Section.TLabel").pack(fill="x")
        prospect_frame = ttk.Frame(right, style="Panel.TFrame"); prospect_frame.pack(fill="both", expand=True, padx=8, pady=8)
        prospects = tk.Listbox(prospect_frame, width=78, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        prospect_x = ttk.Scrollbar(prospect_frame, orient="horizontal", command=prospects.xview); prospects.configure(xscrollcommand=prospect_x.set)
        prospects.pack(fill="both", expand=True); prospect_x.pack(fill="x")
        training_plans = ['Automatic', 'Balanced', 'Wrestling', 'Boxing', 'Muay Thai', 'BJJ', 'Judo', 'Sambo', 'Clinch', 'Cardio', 'Strength', 'Fight IQ']
        focus_var = tk.StringVar(value="Automatic")
        intensity_var = tk.StringVar(value="Standard")
        destinations = ["MMA"] + sorted(getattr(self, "player_combat_divisions", {}).keys())
        destination_var = tk.StringVar(value=destinations[0])
        def redraw():
            self.repair_academy(academy)
            if academy.get("network_weeks", 0) > 0:
                net = f"building {academy.get('network_region', '')} ({academy.get('network_weeks')}w left)"
            elif academy.get("network_active"):
                net = f"active {academy.get('network_region', '')} via {academy.get('network_scout', 'Scout')}"
            else:
                net = "none"
            showcase = f"{academy.get('showcase_weeks', 8)}w" if academy.get("auto_showcases", True) else "Off"
            total_invested = sum(academy.get(key, 0) for key in ("build_spend", "operating_spend", "signing_spend", "upgrade_spend", "network_spend"))
            status.config(text=f"Level {academy['level']} | Reputation {academy.get('reputation', 10)}/100 | {academy.get('philosophy', 'Balanced MMA')} | Capacity {len(academy['prospects'])}/{academy['capacity']} | Weekly ${academy['weekly_cost']:,} | Invested ${total_invested:,} | Network {net} | Training {'Auto' if academy.get('auto_train', True) else 'Paused'} | Showcase {showcase}")
            report.config(text=academy.get("last_scout_report", "Scout youth prospects to build the shortlist."))
            talent.delete(0, 'end'); prospects.delete(0, 'end')
            for item in academy['talent_pool']:
                talent.insert('end', self.academy_recruitment_label(item))
            for item in academy['prospects']:
                self.repair_academy_prospect(item)
                injury = f" | INJ {item['injured']}w" if item.get("injured", 0) else ""
                trend = self.academy_prospect_trend(item)
                ready = self.academy_graduation_readiness(item)
                gender = str(item.get('gender', '')).strip()[:1].upper() or '?'
                prospects.insert('end', f"{item['name']} | {gender} | age {item['age']} | {item['amateur_weight']} | {item['plan']}/{item.get('training_intensity', 'Standard')} (rec {self.recommended_academy_focus(item)}) | {item['amateur_w']}-{item['amateur_l']}-{item.get('amateur_d', 0)} | {item['rating']}/{item['potential']} ({trend:+}) | Ready {ready}% | S{item['striking']} W{item['wrestling']} G{item['grappling']}{injury}")
        def sign():
            if not talent.curselection() or len(academy['prospects']) >= academy['capacity']: return
            item = academy['talent_pool'][talent.curselection()[0]]
            cost = item.get('signing_cost') or self.academy_signing_cost(item)
            if self.cash < cost: messagebox.showwarning('Academy', f'Signing {item["name"]} costs ${cost:,}.'); return
            self.cash -= cost
            item = academy['talent_pool'].pop(talent.curselection()[0]); item.update({'plan': 'Automatic', 'training_intensity': 'Standard', 'amateur_w': 0, 'amateur_l': 0, 'amateur_d': 0, 'amateur_history': [], 'weeks': 0, 'development': 0, 'weeks_to_sign': 0, 'academy_member': True, 'joined_month': self.month, 'baseline_rating': item.get('rating', 40)}); self.repair_academy_prospect(item); academy['prospects'].append(item); academy['signing_spend'] = academy.get('signing_spend', 0) + cost; self.record_finance_transaction(f"Academy signing: {item['name']}", costs=cost); academy['last_scout_report'] = f"Signed {item['name']} into the academy for ${cost:,}."; redraw(); self.refresh_all()
        def pass_lead():
            if not talent.curselection(): return
            item = academy['talent_pool'].pop(talent.curselection()[0]); academy['last_scout_report'] = f"Passed on {item.get('name', 'a youth lead')} from the {item.get('region', 'regional')} youth list."; redraw()
        def set_training_focus():
            if not prospects.curselection(): return
            item = academy['prospects'][prospects.curselection()[0]]
            item['plan'] = focus_var.get() or 'Automatic'
            item['training_intensity'] = intensity_var.get() or 'Standard'
            academy['last_scout_report'] = f"{item['name']} training focus set to {item['plan']}."
            redraw()
        def selected_prospect(_event=None):
            if not prospects.curselection(): return None
            item = academy['prospects'][prospects.curselection()[0]]
            focus_var.set(item.get('plan', 'Automatic')); intensity_var.set(item.get('training_intensity', 'Standard'))
            return item
        def open_lead_report():
            if not talent.curselection(): return
            item = academy['talent_pool'][talent.curselection()[0]]
            messagebox.showinfo(f"Scout Report - {item['name']}", self.academy_lead_report(item))
        def open_prospect_profile():
            if not prospects.curselection(): return
            item = academy['prospects'][prospects.curselection()[0]]
            self.repair_academy_prospect(item)
            profile = tk.Toplevel(window); profile.title(f"Academy Prospect - {item['name']}"); profile.geometry("720x560"); profile.minsize(620, 460); profile.configure(bg=self.colors["chrome"])
            ttk.Label(profile, text=item['name'].upper(), style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=8)
            text = tk.Text(profile, wrap="word", font=("Courier New", 10), bg=self.colors["cream"], fg=self.colors["text"], padx=12, pady=12)
            text.pack(fill="both", expand=True, padx=10, pady=(0, 8))
            def bar(label, value):
                blocks = max(1, min(20, round(value / 5)))
                return f"{label:<12} [{'█' * blocks}{'.' * (20 - blocks)}] {value}"
            lines = [
                f"{item['gender']} | Age {item['age']} | {item['region']} | {item['amateur_weight']} -> {item['weight']}",
                f"Current/Potential: {item['rating']}/{item['potential']} | Development {item.get('development', 0)} | Fatigue {item.get('fatigue', 0)} | Injury {item.get('injured', 0)}w",
                f"Training focus: {item.get('plan', 'Automatic')} | Recommended: {self.recommended_academy_focus(item)}",
                f"Intensity: {item.get('training_intensity', 'Standard')} | Preferred pathway: {self.academy_preferred_sport(item)} | Graduation readiness: {self.academy_graduation_readiness(item)}%",
                f"Dedication: {item.get('dedication', 50)} | Coachability: {item.get('coachability', 50)} | Confidence: {item.get('confidence', 50)} | Trend: {self.academy_prospect_trend(item):+}",
                f"Amateur record: {item['amateur_w']}-{item['amateur_l']}-{item.get('amateur_d', 0)}",
                "",
            ]
            for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
                lines.append(bar(key.title(), item.get(key, 40)))
            lines += ["", "MILESTONES"] + ([self.format_game_date_text(entry) for entry in item.get("milestones", [])[:12]] or ["No milestones yet."])
            lines += ["", "RECENT TRAINING"] + ([self.format_game_date_text(entry) for entry in item.get("training_log", [])[:12]] or ["No recorded training gains yet."])
            lines += ["", "AMATEUR HISTORY"] + ([self.format_game_date_text(entry) for entry in item.get("amateur_history", [])[:30]] or ["No amateur bouts yet."])
            text.insert("end", "\n".join(lines)); text.config(state="disabled")
        def amateur_bout():
            results = self.run_academy_showcase_card(academy)
            if not results: messagebox.showinfo('Academy', 'Two eligible academy prospects of the same gender are needed.'); return
            academy['showcase_weeks'] = 8
            academy['last_scout_report'] = f"Manual academy showcase: {len(results)} bout(s). {results[0]}"
            redraw()
            messagebox.showinfo("Academy Card Recap", f"{len(results)} bout(s) completed.\n\n" + "\n".join(results[:10]))
        def promote():
            if not prospects.curselection(): return
            item = academy['prospects'][prospects.curselection()[0]]
            if item['age'] < 16: messagebox.showinfo('Academy', 'A prospect must be at least 16 to turn professional.'); return
            if item['age'] < 18 and not messagebox.askyesno('Early Professional Debut', f"{item['name']} is only {item['age']}. Promote early, before the normal age-18 pathway?"): return
            ok, note, fighter = self.promote_academy_prospect_to_sport(item, destination_var.get() or "MMA")
            if not ok: messagebox.showwarning("Academy", note); return
            academy['prospects'].remove(item)
            academy['last_scout_report'] = note
            self.news.insert(0, note)
            redraw(); self.refresh_all()
        def release_prospect():
            item = selected_prospect()
            if not item: return
            if not messagebox.askyesno("Release Academy Prospect", f"Release {item['name']} from the academy? This cannot be undone."): return
            academy['prospects'].remove(item)
            academy['last_scout_report'] = f"Released {item['name']} from the academy."
            redraw()
        def watch_last_card():
            cards = academy.get('card_history', [])
            if not cards: messagebox.showinfo("Academy Cards", "No academy showcase has been completed yet."); return
            card = cards[0]
            package = {'event_name': card.get('event_name', 'Academy Showcase'), 'log': [card.get('recap', '')] + card.get('results', []), 'fight_logs': card.get('fight_logs', [])}
            self.open_live_fight_window({'name': package['event_name']}, package, apply_results=False)
        def show_alumni():
            alumni = academy.get('alumni', [])
            if not alumni: messagebox.showinfo("Academy Alumni", "No academy graduates yet."); return
            lines = [f"{row.get('name')} | {row.get('destination')} | Amateur {row.get('amateur_record')} | Pro {row.get('professional_record')} | OVR {row.get('current_rating')} | Titles {row.get('title_wins', 0)}" for row in alumni[:40]]
            messagebox.showinfo("Academy Alumni", "ACADEMY GRADUATES\n\n" + "\n".join(lines))
        controls = ttk.Frame(window, style='Inset.TFrame'); controls.pack(fill='x', padx=10, pady=(0, 8))
        def upgrade():
            cost = 50000 + max(0, academy.get('level', 1) - 1) * 35000
            if self.cash < cost: messagebox.showwarning('Academy', f'Upgrade costs ${cost:,}.'); return
            self.cash -= cost; academy.update({'capacity': academy['capacity'] + 2, 'level': academy['level'] + 1, 'weekly_cost': academy['weekly_cost'] + 1800}); academy['upgrade_spend'] = academy.get('upgrade_spend', 0) + cost; academy['reputation'] = min(100, academy.get('reputation', 10) + 2); self.record_finance_transaction('Academy facilities upgrade', costs=cost); redraw()
        def start_network():
            ok, message = self.start_academy_network(region_var.get(), scout_var.get())
            if not ok: messagebox.showwarning("Academy", message)
            redraw(); self.refresh_all()
        def cancel_network():
            ok, message = self.cancel_academy_network()
            if not ok: messagebox.showinfo("Academy", message)
            redraw()
        def set_philosophy():
            academy['philosophy'] = philosophy_var.get() or 'Balanced MMA'
            academy['last_scout_report'] = f"Academy philosophy set to {academy['philosophy']}. Training will now favour those attributes."
            redraw()
        def toggle_training():
            academy['auto_train'] = not academy.get('auto_train', True); redraw()
        def toggle_showcases():
            academy['auto_showcases'] = not academy.get('auto_showcases', True); redraw()
        ttk.Button(network_actions, text="Set Up Network", style="Accent.TButton", command=start_network).pack(side="left", padx=4)
        ttk.Button(network_actions, text="Cancel Network", command=cancel_network).pack(side="left", padx=3)
        ttk.Button(network_actions, text="Set Philosophy", command=set_philosophy).pack(side="left", padx=3)
        recruit_row = ttk.Frame(controls, style='Inset.TFrame'); recruit_row.pack(fill='x', pady=2)
        ttk.Button(recruit_row, text='Sign Selected Talent', command=sign).grid(row=0, column=0, sticky='ew', padx=3, pady=2)
        ttk.Button(recruit_row, text='Pass Selected Lead', command=pass_lead).grid(row=0, column=1, sticky='ew', padx=3, pady=2)
        ttk.Button(recruit_row, text='Profile / History', command=open_prospect_profile).grid(row=0, column=2, sticky='ew', padx=3, pady=2)
        ttk.Button(recruit_row, text='Run Amateur Card', command=amateur_bout).grid(row=0, column=3, sticky='ew', padx=3, pady=2)
        ttk.Button(recruit_row, text='Scout Report', command=open_lead_report).grid(row=0, column=4, sticky='ew', padx=3, pady=2)
        train_row = ttk.Frame(controls, style='Inset.TFrame'); train_row.pack(fill='x', pady=2)
        ttk.Label(train_row, text='Focus', style='Inset.TLabel').grid(row=0, column=0, sticky='w', padx=(4, 2))
        ttk.Combobox(train_row, values=training_plans, textvariable=focus_var, state='readonly', width=12).grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Label(train_row, text='Intensity', style='Inset.TLabel').grid(row=0, column=2, sticky='w', padx=(6, 2))
        ttk.Combobox(train_row, values=('Light', 'Standard', 'Intensive', 'Recovery'), textvariable=intensity_var, state='readonly', width=10).grid(row=0, column=3, sticky='ew', padx=2)
        ttk.Button(train_row, text='Set Plan', command=set_training_focus).grid(row=0, column=4, sticky='ew', padx=3, pady=2)
        ttk.Label(train_row, text='Promote to', style='Inset.TLabel').grid(row=0, column=5, sticky='w', padx=(8, 2))
        ttk.Combobox(train_row, values=destinations, textvariable=destination_var, state='readonly', width=16).grid(row=0, column=6, sticky='ew', padx=2)
        ttk.Button(train_row, text='Promote', style='Accent.TButton', command=promote).grid(row=0, column=7, sticky='ew', padx=3, pady=2)
        upgrade_row = ttk.Frame(controls, style='Inset.TFrame'); upgrade_row.pack(fill='x', pady=2)
        for col in range(3): upgrade_row.columnconfigure(col, weight=1)
        ttk.Button(upgrade_row, text='Upgrade Facilities / Capacity (+2)', command=upgrade).grid(row=0, column=0, sticky='ew', padx=3, pady=2)
        ttk.Button(upgrade_row, text='Release Selected', command=release_prospect).grid(row=0, column=1, sticky='ew', padx=3, pady=2)
        ttk.Button(upgrade_row, text='Watch Last Card', command=watch_last_card).grid(row=0, column=2, sticky='ew', padx=3, pady=2)
        ttk.Button(upgrade_row, text='Academy Alumni', command=show_alumni).grid(row=1, column=0, sticky='ew', padx=3, pady=2)
        ttk.Button(upgrade_row, text='Toggle Training', command=toggle_training).grid(row=1, column=1, sticky='ew', padx=3, pady=2)
        ttk.Button(upgrade_row, text='Toggle Auto Cards', command=toggle_showcases).grid(row=1, column=2, sticky='ew', padx=3, pady=2)
        for row_frame, cols in ((recruit_row, 5), (train_row, 8)):
            for col in range(cols):
                row_frame.columnconfigure(col, weight=1)
        prospects.bind("<Double-1>", lambda _event: open_prospect_profile())
        prospects.bind("<<ListboxSelect>>", selected_prospect)
        talent.bind("<Double-1>", lambda _event: open_lead_report())
        redraw()

    def open_academy_window(self):
        """Open the responsive, live-refreshing academy management workspace."""
        academy = self.academy
        if not academy.get("owned"):
            cost = 180000
            setup = tk.Toplevel(self.root)
            setup.title("MMA Warriors - Build Fighting Academy")
            setup.geometry("720x330")
            setup.minsize(620, 300)
            setup.configure(bg=self.colors["chrome"])
            setup.transient(self.root)
            ttk.Label(setup, text="BUILD A FIGHTING ACADEMY", style="ScreenTitle.TLabel").pack(fill="x", padx=10, pady=(10, 6), ipady=5)
            body = ttk.Frame(setup, style="Panel.TFrame")
            body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
            ttk.Label(
                body,
                text=(f"INVESTMENT  ${cost:,}\nWEEKLY OPERATING COST  $4,500\nSTARTING CAPACITY  8 PROSPECTS\n\n"
                      "Hire a Scout, establish a regional youth network, evaluate live leads, and develop prospects through training and amateur cards."),
                style="Panel.TLabel", justify="left", anchor="nw",
            ).pack(fill="both", expand=True, padx=18, pady=18)
            setup_status = ttk.Label(setup, text=f"Available company cash: ${self.cash:,}", style="Inset.TLabel", anchor="w")
            setup_status.pack(fill="x", padx=10, pady=(0, 6), ipady=4)
            setup_actions = ttk.Frame(setup, style="Inset.TFrame")
            setup_actions.pack(fill="x", padx=10, pady=(0, 10))

            def complete_academy_build():
                if self.cash < cost:
                    setup_status.config(text=f"Build blocked: ${cost:,} required; company cash is ${self.cash:,}.")
                    return
                self.cash -= cost
                academy.update(self.academy_defaults())
                academy.update({
                    "owned": True, "level": 1, "capacity": 8, "weekly_cost": 4500,
                    "build_spend": cost,
                    "last_scout_report": "Hire a Scout to establish a regional youth network.",
                })
                self.record_finance_transaction("Build Fighting Academy", costs=cost)
                self.refresh_all()
                setup.destroy()
                self.open_academy_window()

            build_button = ttk.Button(setup_actions, text=f"Build Academy  ${cost:,}", style="Accent.TButton", command=complete_academy_build)
            build_button.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            ttk.Button(setup_actions, text="Not Now", command=setup.destroy).pack(side="right", padx=4, pady=4)
            if self.cash < cost:
                build_button.state(["disabled"])
            return

        existing = getattr(self, "_academy_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    refresh = getattr(self, "_academy_window_refresh", None)
                    if callable(refresh):
                        refresh()
                    return
            except tk.TclError:
                pass

        self.repair_academy(academy)
        window = tk.Toplevel(self.root)
        self._academy_window = window
        window.title("MMA Warriors - Fighting Academy")
        screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
        width = min(1180, max(900, screen_w - 70))
        height = min(720, max(540, screen_h - 130))
        window.geometry(f"{width}x{height}+{max(0, (screen_w-width)//2)}+{max(0, (screen_h-height)//3)}")
        window.minsize(min(900, width), min(540, height))
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(header, text="FIGHTING ACADEMY", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=4)
        summary = ttk.Label(header, text="", style="ScreenTitle.TLabel", anchor="e", justify="right")
        summary.pack(side="right", fill="x", expand=True, padx=10, pady=4)

        decision_bar = ttk.Frame(window, style="Inset.TFrame")
        decision_bar.pack(fill="x", padx=8, pady=(0, 4))
        decision_text = ttk.Label(
            decision_bar, text="Academy operations ready.", style="Inset.TLabel",
            anchor="w", justify="left",
        )
        decision_text.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        decision_confirm = ttk.Button(decision_bar, text="Confirm", style="Accent.TButton")
        decision_cancel = ttk.Button(decision_bar, text="Cancel")

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        overview = ttk.Frame(notebook, style="Chrome.TFrame")
        recruitment = ttk.Frame(notebook, style="Chrome.TFrame")
        squad = ttk.Frame(notebook, style="Chrome.TFrame")
        facilities = ttk.Frame(notebook, style="Chrome.TFrame")
        legacy = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(overview, text="Overview / Network")
        notebook.add(recruitment, text="Recruitment")
        notebook.add(squad, text="Squad / Training")
        notebook.add(facilities, text="Facilities")
        notebook.add(legacy, text="Cards & Alumni")

        def add_tree(parent, columns, height=12):
            shell = ttk.Frame(parent, style="Panel.TFrame")
            tree = ttk.Treeview(shell, columns=tuple(col[0] for col in columns), show="headings", height=height)
            ybar = ttk.Scrollbar(shell, orient="vertical", command=tree.yview)
            xbar = ttk.Scrollbar(shell, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
            for key, label, col_width, anchor in columns:
                tree.heading(key, text=label)
                tree.column(key, width=col_width, minwidth=45, anchor=anchor, stretch=True)
            shell.rowconfigure(0, weight=1)
            shell.columnconfigure(0, weight=1)
            tree.grid(row=0, column=0, sticky="nsew")
            ybar.grid(row=0, column=1, sticky="ns")
            xbar.grid(row=1, column=0, sticky="ew")
            return shell, tree

        # Overview and network controls.
        overview.columnconfigure(0, weight=1)
        overview.rowconfigure(3, weight=1)
        overview_status = ttk.Label(overview, text="", style="Inset.TLabel", justify="left", anchor="w")
        overview_status.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        report_box = tk.Text(overview, height=4, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8, bd=0)
        report_box.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        report_box.config(state="disabled")
        network_panel, network = self.section(overview, "SCOUTING NETWORK")
        network_panel.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        for col in range(4):
            network.columnconfigure(col, weight=1)
        scout_var = tk.StringVar()
        region_var = tk.StringVar(value=academy.get("network_region") or self.player_region)
        philosophy_var = tk.StringVar(value=academy.get("philosophy", "Balanced MMA"))
        ttk.Label(network, text="Scout", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))
        scout_combo = ttk.Combobox(network, textvariable=scout_var, state="readonly")
        scout_combo.grid(row=1, column=0, sticky="ew", padx=4, pady=3)
        ttk.Label(network, text="Region", style="Inset.TLabel").grid(row=0, column=1, sticky="w", padx=4, pady=(4, 0))
        region_combo = ttk.Combobox(network, values=REGIONS, textvariable=region_var, state="readonly")
        region_combo.grid(row=1, column=1, sticky="ew", padx=4, pady=3)
        ttk.Label(network, text="Philosophy", style="Inset.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=(4, 0))
        philosophy_combo = ttk.Combobox(
            network, textvariable=philosophy_var, state="readonly",
            values=("Balanced MMA", "Striking Academy", "Wrestling Pipeline", "Submission School", "Athletic Development", "Multi-Sport Pathway"),
        )
        philosophy_combo.grid(row=1, column=2, sticky="ew", padx=4, pady=3)
        preview = ttk.Label(network, text="", style="Inset.TLabel", justify="left", anchor="w")
        preview.grid(row=2, column=0, columnspan=4, sticky="ew", padx=4, pady=3)
        network_progress = ttk.Progressbar(network, maximum=8, mode="determinate")
        network_progress.grid(row=3, column=0, columnspan=3, sticky="ew", padx=4, pady=4)
        network_progress_text = ttk.Label(network, text="", style="Inset.TLabel", anchor="e")
        network_progress_text.grid(row=3, column=3, sticky="ew", padx=4, pady=4)
        network_actions = ttk.Frame(network, style="Inset.TFrame")
        network_actions.grid(row=4, column=0, columnspan=4, sticky="ew", padx=2, pady=(2, 5))
        for col in range(6):
            network_actions.columnconfigure(col, weight=1)

        # Recruitment table and actions.
        recruitment.rowconfigure(0, weight=3)
        recruitment.rowconfigure(2, weight=1)
        recruitment.columnconfigure(0, weight=1)
        lead_shell, lead_tree = add_tree(recruitment, (
            ("name", "Prospect", 165, "w"), ("gender", "G", 34, "center"), ("age", "Age", 45, "center"), ("region", "Region", 85, "w"),
            ("weight", "Youth Class", 110, "w"), ("current", "Current", 75, "center"), ("potential", "Potential", 75, "center"),
            ("confidence", "Confidence", 75, "center"), ("cost", "Sign Cost", 90, "e"), ("window", "Decision", 65, "center"),
        ), 15)
        lead_shell.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        lead_tree.tag_configure("urgent", foreground="#ffb0a8")
        lead_tree.tag_configure("strong", foreground="#9de6a0")
        lead_actions = ttk.Frame(recruitment, style="Inset.TFrame")
        lead_actions.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        for col in range(4): lead_actions.columnconfigure(col, weight=1)
        lead_report_panel, lead_report_body = self.section(recruitment, "SCOUT REPORT")
        lead_report_panel.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        lead_report_body.rowconfigure(0, weight=1)
        lead_report_body.columnconfigure(0, weight=1)
        lead_feedback = tk.Text(
            lead_report_body, height=7, wrap="word", bg=self.colors["panel_dark"],
            fg=self.colors["text"], insertbackground=self.colors["text"],
            font=("Tahoma", 9), padx=10, pady=8, bd=0,
        )
        lead_feedback.grid(row=0, column=0, sticky="nsew")
        lead_feedback.config(state="disabled")

        # Signed squad table and controls.
        squad.rowconfigure(0, weight=1)
        squad.columnconfigure(0, weight=1)
        prospect_shell, prospect_tree = add_tree(squad, (
            ("name", "Prospect", 150, "w"), ("gender", "G", 34, "center"), ("age", "Age", 42, "center"), ("weight", "Class", 100, "w"),
            ("focus", "Focus / Intensity", 130, "w"), ("record", "Amateur", 65, "center"), ("ability", "Current / Pot", 85, "center"),
            ("trend", "Trend", 55, "center"), ("ready", "Ready", 55, "center"), ("grad", "Graduation", 118, "center"), ("fatigue", "Fatigue", 55, "center"), ("status", "Status", 75, "center"),
        ), 14)
        prospect_shell.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        prospect_tree.tag_configure("injured", foreground="#ff9b9b")
        prospect_tree.tag_configure("ready", foreground="#9de6a0")
        self.attach_tree_heading_tooltips(prospect_tree, {
            "ready": "Graduation readiness (age, ability, amateur experience, mentality, minus injury/fatigue).",
            "grad": "Scout's call: GRADUATE NOW (turn pro), ALMOST READY, KEEP DEVELOPING, NEEDS BOUTS, or TOO YOUNG.",
            "trend": "Recent rating movement.",
            "ability": "Current rating / projected ceiling.",
        })
        plan_row = ttk.Frame(squad, style="Inset.TFrame")
        plan_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 3))
        for col in range(8): plan_row.columnconfigure(col, weight=1)
        focus_var = tk.StringVar(value="Automatic")
        intensity_var = tk.StringVar(value="Standard")
        destination_var = tk.StringVar(value="MMA")
        ttk.Label(plan_row, text="Focus", style="Inset.TLabel").grid(row=0, column=0, padx=3, sticky="w")
        ttk.Combobox(plan_row, textvariable=focus_var, state="readonly", values=("Automatic", "Balanced", "Wrestling", "Boxing", "Muay Thai", "BJJ", "Judo", "Sambo", "Clinch", "Cardio", "Strength", "Fight IQ")).grid(row=0, column=1, padx=3, sticky="ew")
        ttk.Label(plan_row, text="Intensity", style="Inset.TLabel").grid(row=0, column=2, padx=3, sticky="w")
        ttk.Combobox(plan_row, textvariable=intensity_var, state="readonly", values=("Light", "Standard", "Intensive", "Recovery")).grid(row=0, column=3, padx=3, sticky="ew")
        plan_hint = ttk.Label(plan_row, text="Select a prospect to see coaching advice.", style="Inset.TLabel", anchor="w")
        plan_hint.grid(row=1, column=0, columnspan=8, padx=3, pady=(3, 0), sticky="ew")
        squad_actions = ttk.Frame(squad, style="Inset.TFrame")
        squad_actions.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        for col in range(7): squad_actions.columnconfigure(col, weight=1)

        # Cards and alumni tables.
        legacy.rowconfigure(0, weight=1)
        legacy.columnconfigure(0, weight=1)
        legacy_panes = ttk.Panedwindow(legacy, orient="vertical")
        legacy_panes.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        cards_panel = ttk.Frame(legacy_panes, style="Panel.TFrame")
        alumni_panel = ttk.Frame(legacy_panes, style="Panel.TFrame")
        legacy_panes.add(cards_panel, weight=1)
        legacy_panes.add(alumni_panel, weight=1)
        cards_panel.rowconfigure(1, weight=1); cards_panel.columnconfigure(0, weight=1)
        ttk.Label(cards_panel, text="ACADEMY CARD HISTORY", style="Section.TLabel").grid(row=0, column=0, sticky="ew")
        card_shell, card_tree = add_tree(cards_panel, (
            ("event", "Event", 230, "w"), ("date", "Date", 110, "center"), ("bouts", "Bouts", 55, "center"), ("recap", "Recap", 340, "w"),
        ), 6)
        card_shell.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        card_detail = ttk.Label(cards_panel, text="Select a card to inspect or replay it.", style="Panel.TLabel", anchor="w", justify="left")
        card_detail.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 4))
        card_controls = ttk.Frame(cards_panel, style="Inset.TFrame"); card_controls.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 6))
        alumni_panel.rowconfigure(1, weight=1); alumni_panel.columnconfigure(0, weight=1)
        ttk.Label(alumni_panel, text="ACADEMY ALUMNI", style="Section.TLabel").grid(row=0, column=0, sticky="ew")
        alumni_shell, alumni_tree = add_tree(alumni_panel, (
            ("name", "Graduate", 180, "w"), ("destination", "Destination", 115, "w"), ("amateur", "Amateur", 70, "center"),
            ("pro", "Professional", 75, "center"), ("rating", "OVR", 50, "center"), ("titles", "Titles", 50, "center"), ("status", "Status", 65, "center"),
        ), 6)
        alumni_shell.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        alumni_controls = ttk.Frame(alumni_panel, style="Inset.TFrame"); alumni_controls.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))

        # Facilities tab: purchasable, permanent upgrades that boost development.
        facilities.rowconfigure(1, weight=1)
        facilities.columnconfigure(0, weight=1)
        ttk.Label(facilities, text="Permanent facility upgrades speed up and protect prospect development. Each is a one-off cost.", style="Inset.TLabel", anchor="w").grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        facility_shell, facility_tree = add_tree(facilities, (
            ("name", "Facility", 220, "w"), ("effect", "Effect", 430, "w"), ("cost", "Cost", 100, "e"), ("status", "Status", 100, "center"),
        ), 8)
        facility_shell.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        facility_tree.tag_configure("owned", foreground="#7fd694")
        facility_controls = ttk.Frame(facilities, style="Inset.TFrame")
        facility_controls.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        facility_hint = ttk.Label(facility_controls, text="Select a facility to install.", style="Inset.TLabel", anchor="w")
        facility_hint.pack(side="left", fill="x", expand=True, padx=4)

        def buy_facility():
            selected = facility_tree.selection()
            if not selected:
                facility_hint.config(text="Select a facility to install."); return
            upgrade_id = selected[0].split(":", 1)[1]
            ok, message = self.purchase_academy_upgrade(academy, upgrade_id)
            facility_hint.config(text=message)
            if ok:
                self.refresh_all()
            refresh_window()

        buy_button = ttk.Button(facility_controls, text="Install Selected", style="Accent.TButton", command=buy_facility)
        buy_button.pack(side="right", padx=4)

        def selected_index(tree, prefix, pool):
            selected = tree.selection()
            if not selected:
                return None
            try:
                index = int(selected[0].split(":", 1)[1])
            except (IndexError, ValueError):
                return None
            return index if 0 <= index < len(pool) else None

        def set_enabled(button, enabled):
            button.state(["!disabled"] if enabled else ["disabled"])

        def selected_lead():
            index = selected_index(lead_tree, "lead", academy.get("talent_pool", []))
            return academy["talent_pool"][index] if index is not None else None

        def selected_prospect():
            index = selected_index(prospect_tree, "prospect", academy.get("prospects", []))
            return academy["prospects"][index] if index is not None else None

        def selected_card():
            index = selected_index(card_tree, "card", academy.get("card_history", []))
            return academy["card_history"][index] if index is not None else None

        def selected_alumnus():
            index = selected_index(alumni_tree, "alumnus", academy.get("alumni", []))
            return academy["alumni"][index] if index is not None else None

        pending_decision = {"callback": None}

        def set_readonly_text(widget, text):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.insert("end", text)
            widget.config(state="disabled")

        def clear_decision(message="Academy operations ready."):
            pending_decision["callback"] = None
            decision_text.config(text=message)
            decision_confirm.pack_forget()
            decision_cancel.pack_forget()

        def show_academy_notice(message, tab=None, report=None):
            academy["last_scout_report"] = message
            clear_decision(message)
            if tab is not None:
                notebook.select(tab)
            set_readonly_text(report_box, message)
            if report is not None:
                set_readonly_text(lead_feedback, report)

        def request_academy_decision(prompt, callback, tab=None):
            pending_decision["callback"] = callback
            decision_text.config(text=prompt)
            decision_cancel.pack(side="right", padx=(3, 8), pady=4)
            decision_confirm.pack(side="right", padx=3, pady=4)
            if tab is not None:
                notebook.select(tab)

        def confirm_academy_decision():
            callback = pending_decision.get("callback")
            clear_decision()
            if callable(callback):
                callback()

        decision_confirm.config(command=confirm_academy_decision)
        decision_cancel.config(command=lambda: clear_decision("Action cancelled."))

        def open_fight_log(event_name, fight_logs, recap=""):
            package = {"event_name": event_name, "log": [recap] if recap else [], "fight_logs": list(fight_logs or [])}
            self.open_live_fight_window({"name": event_name}, package, apply_results=False)

        def open_lead_report():
            item = selected_lead()
            if item:
                report = self.academy_lead_report(item)
                show_academy_notice(f"Reviewing the live report for {item['name']}.", recruitment, report)

        def open_prospect_profile():
            item = selected_prospect()
            if not item:
                return
            self.repair_academy_prospect(item)
            profile = tk.Toplevel(window)
            profile.title(f"Academy Prospect - {item['name']}")
            pw = min(880, max(700, profile.winfo_screenwidth() - 100))
            ph = min(650, max(520, profile.winfo_screenheight() - 150))
            profile.geometry(f"{pw}x{ph}")
            profile.minsize(min(700, pw), min(500, ph))
            profile.configure(bg=self.colors["chrome"])
            ttk.Label(profile, text=item["name"].upper(), style="ScreenTitle.TLabel").pack(fill="x", padx=10, pady=8)
            profile_tabs = ttk.Notebook(profile); profile_tabs.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            summary_tab = ttk.Frame(profile_tabs, style="Chrome.TFrame")
            progress_tab = ttk.Frame(profile_tabs, style="Chrome.TFrame")
            history_tab = ttk.Frame(profile_tabs, style="Chrome.TFrame")
            training_tab = ttk.Frame(profile_tabs, style="Chrome.TFrame")
            for tab, label in ((summary_tab, "Summary"), (progress_tab, "Progression"), (history_tab, "Amateur History"), (training_tab, "Training & Milestones")):
                profile_tabs.add(tab, text=label)
            identity = ttk.Label(
                summary_tab,
                text=(f"{item['gender']} | Age {item['age']} | {item['region']} | {item['amateur_weight']} -> {item['weight']}\n"
                      f"Current/Potential {item['rating']}/{item['potential']} | Amateur {item['amateur_w']}-{item['amateur_l']}-{item.get('amateur_d', 0)} | "
                      f"Readiness {self.academy_graduation_readiness(item)}%\n"
                      f"Focus {item.get('plan', 'Automatic')} ({item.get('training_intensity', 'Standard')}) | Recommended {self.recommended_academy_focus(item)} | "
                      f"Preferred path {self.academy_preferred_sport(item)} | Fatigue {item.get('fatigue', 0)} | Injury {item.get('injured', 0)}w"),
                style="Inset.TLabel", justify="left", anchor="w",
            )
            identity.pack(fill="x", padx=8, pady=8)
            stat_tree = ttk.Treeview(summary_tab, columns=("area", "value", "assessment"), show="headings", height=11)
            for key, label, col_width in (("area", "Attribute", 210), ("value", "Rating", 90), ("assessment", "Assessment", 180)):
                stat_tree.heading(key, text=label); stat_tree.column(key, width=col_width, anchor="w")
            for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
                value = item.get(key, 40)
                grade = "Elite" if value >= 80 else "Strong" if value >= 65 else "Developing" if value >= 50 else "Raw"
                stat_tree.insert("", "end", values=(key.replace("_", " ").title(), value, grade))
            stat_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            mentality = ttk.Label(summary_tab, text=f"Dedication {item.get('dedication', 50)} | Coachability {item.get('coachability', 50)} | Confidence {item.get('confidence', 50)}", style="Inset.TLabel")
            mentality.pack(fill="x", padx=8, pady=(0, 8))

            progress_tab.rowconfigure(0, weight=1); progress_tab.columnconfigure(0, weight=2); progress_tab.columnconfigure(1, weight=1)
            chart = tk.Canvas(progress_tab, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            chart.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            progress_tree = ttk.Treeview(progress_tab, columns=("date", "rating", "change"), show="headings", height=16)
            for key, label, col_width in (("date", "Recorded", 100), ("rating", "Rating", 70), ("change", "Change", 70)):
                progress_tree.heading(key, text=label); progress_tree.column(key, width=col_width, anchor="center")
            history = list(item.get("rating_history", []))
            prior = item.get("baseline_rating", item.get("rating", 40))
            if not history:
                history = [{"month": item.get("joined_month", self.month), "week": 1, "rating": prior}]
            if history[-1].get("rating") != item.get("rating"):
                history.append({"month": self.month, "week": self.week, "rating": item.get("rating", 40)})
            for row in history:
                rating = row.get("rating", 40)
                progress_tree.insert("", "end", values=(self.format_game_date(row.get("month", self.month), row.get("week", 1)), rating, f"{rating-prior:+}"))
                prior = rating
            progress_tree.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
            def draw_chart(_event=None):
                chart.delete("all")
                cw, ch = max(260, chart.winfo_width()), max(180, chart.winfo_height())
                values = [row.get("rating", 40) for row in history]
                low, high = max(1, min(values) - 3), min(99, max(values) + 3)
                span = max(1, high - low)
                points = []
                for index, value in enumerate(values):
                    x = 35 + index * (cw - 60) / max(1, len(values) - 1)
                    y = ch - 28 - (value - low) * (ch - 55) / span
                    points.extend((x, y))
                chart.create_text(8, 12, anchor="w", text=f"Rating progression ({values[0]} -> {values[-1]})", fill=self.colors["text"], font=("Tahoma", 9, "bold"))
                chart.create_line(30, 24, 30, ch - 24, fill=self.colors["line"])
                chart.create_line(30, ch - 24, cw - 15, ch - 24, fill=self.colors["line"])
                if len(points) >= 4: chart.create_line(*points, fill=self.colors["gold"], width=3, smooth=True)
                for index in range(0, len(points), 2): chart.create_oval(points[index]-3, points[index+1]-3, points[index]+3, points[index+1]+3, fill=self.colors["red"], outline="")
                chart.create_text(26, 30, anchor="e", text=str(high), fill=self.colors["muted"])
                chart.create_text(26, ch-26, anchor="e", text=str(low), fill=self.colors["muted"])
            chart.bind("<Configure>", draw_chart); profile.after_idle(draw_chart)

            history_tab.rowconfigure(0, weight=1); history_tab.columnconfigure(0, weight=1)
            amateur_tree = ttk.Treeview(history_tab, columns=("date", "result", "opponent", "method", "detail"), show="headings", height=16)
            for key, label, col_width in (("date", "Date", 95), ("result", "Result", 60), ("opponent", "Opponent", 150), ("method", "Method", 130), ("detail", "Recorded bout", 360)):
                amateur_tree.heading(key, text=label); amateur_tree.column(key, width=col_width, anchor="w")
            amateur_tree.tag_configure("win", foreground="#9de6a0"); amateur_tree.tag_configure("loss", foreground="#ff9b9b")
            bout_records = list(item.get("amateur_bout_records", []))[:100]
            if bout_records:
                for index, record in enumerate(bout_records):
                    result = record.get("result", "-")
                    date = self.format_game_date(record.get("month", self.month), record.get("week", 1))
                    detail = f"{record.get('event', 'Academy Showcase')} | R{record.get('round', '?')} | {record.get('weight', item.get('amateur_weight', 'Youth'))}"
                    amateur_tree.insert("", "end", iid=f"history:{index}", tags=("win" if result == "W" else "loss" if result == "L" else "",), values=(date, result, record.get("opponent", "Unknown"), record.get("method", "-"), detail))
            else:
                for index, entry in enumerate(item.get("amateur_history", [])[:100]):
                    text = str(entry)
                    date = text.split(":", 1)[0]
                    if " ended in a draw " in text:
                        result, opponent, method = "D", text.split(":", 1)[-1].split(" vs ", 1)[-1].split(" ended", 1)[0], "Draw"
                    elif f"{item['name']} def. " in text:
                        result, opponent = "W", text.split(" def. ", 1)[1].split(" by ", 1)[0]
                        method = text.split(" by ", 1)[1].split(" (", 1)[0] if " by " in text else "-"
                    else:
                        result = "L"
                        opponent = text.split(":", 1)[-1].split(" def. ", 1)[0].strip()
                        method = text.split(" by ", 1)[1].split(" (", 1)[0] if " by " in text else "-"
                    amateur_tree.insert("", "end", iid=f"history:{index}", tags=("win" if result == "W" else "loss" if result == "L" else "",), values=(self.format_game_date_text(date), result, opponent, method, self.format_game_date_text(text)))
            amateur_y = ttk.Scrollbar(history_tab, orient="vertical", command=amateur_tree.yview); amateur_x = ttk.Scrollbar(history_tab, orient="horizontal", command=amateur_tree.xview)
            amateur_tree.configure(yscrollcommand=amateur_y.set, xscrollcommand=amateur_x.set)
            amateur_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0)); amateur_y.grid(row=0, column=1, sticky="ns", pady=(8, 0)); amateur_x.grid(row=1, column=0, sticky="ew", padx=(8, 0))
            history_buttons = ttk.Frame(history_tab, style="Inset.TFrame"); history_buttons.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
            def watch_last_bout():
                bout = item.get("last_amateur_bout", {})
                if not bout or not bout.get("lines"):
                    show_academy_notice(f"No replayable amateur bout has been stored for {item['name']} yet.", squad)
                    return
                open_fight_log(bout.get("heading", "Academy Amateur Bout"), [bout], bout.get("result", ""))
            ttk.Button(history_buttons, text="Watch Last Bout", style="Accent.TButton", command=watch_last_bout).pack(side="left", padx=4, pady=4)

            training_text = tk.Text(training_tab, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=12, pady=10)
            training_scroll = ttk.Scrollbar(training_tab, orient="vertical", command=training_text.yview); training_text.configure(yscrollcommand=training_scroll.set)
            training_scroll.pack(side="right", fill="y", padx=(0, 8), pady=8); training_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
            milestones = [self.format_game_date_text(entry) for entry in item.get("milestones", [])[:30]] or ["No milestones yet."]
            training = [self.format_game_date_text(entry) for entry in item.get("training_log", [])[:60]] or ["No recorded training gains yet."]
            training_text.insert("end", "MILESTONES\n" + "\n".join(milestones))
            training_text.insert("end", "\n\nRECENT TRAINING\n" + "\n".join(training))
            training_text.config(state="disabled")

        def replay_selected_card():
            card = selected_card()
            if not card:
                return
            open_fight_log(card.get("event_name", "Academy Showcase"), card.get("fight_logs", []), card.get("recap", ""))

        def open_alumnus_profile():
            row = selected_alumnus()
            fighter = self.academy_alumnus_fighter(row.get("name", "")) if row else None
            if fighter:
                self.open_fighter_profile_window(fighter)
            elif row:
                show_academy_notice(f"{row.get('name')} is no longer available in the active fighter database.", legacy)

        def sign_lead():
            item = selected_lead()
            if not item:
                return
            if len(academy.get("prospects", [])) >= academy.get("capacity", 0):
                academy["last_scout_report"] = "Signing blocked: the academy is at capacity."
                refresh_window()
                return
            cost = item.get("signing_cost") or self.academy_signing_cost(item)
            if self.cash < cost:
                academy["last_scout_report"] = f"Signing blocked: {item['name']} costs ${cost:,}."
                refresh_window()
                return
            self.cash -= cost
            academy["talent_pool"].remove(item)
            item.update({"plan": "Automatic", "training_intensity": "Standard", "amateur_w": 0, "amateur_l": 0, "amateur_d": 0,
                         "amateur_history": [], "amateur_bout_records": [], "weeks": 0, "development": 0,
                         "weeks_to_sign": 0, "academy_member": True, "joined_month": self.month,
                         "baseline_rating": item.get("rating", 40), "signed_cost": cost})
            self.repair_academy_prospect(item); academy["prospects"].append(item)
            academy["signing_spend"] = academy.get("signing_spend", 0) + cost
            self.record_finance_transaction(f"Academy signing: {item['name']}", costs=cost)
            academy["last_scout_report"] = f"Signed {item['name']} into the academy for ${cost:,}."
            refresh_window()
            self.refresh_all()

        def pass_lead():
            item = selected_lead()
            if item:
                academy["talent_pool"].remove(item)
                academy["last_scout_report"] = f"Passed on {item['name']} from the {item.get('region', 'regional')} youth list."
                refresh_window()

        def set_plan():
            item = selected_prospect()
            if not item:
                return
            item["plan"] = focus_var.get() or "Automatic"
            item["training_intensity"] = intensity_var.get() or "Standard"
            academy["last_scout_report"] = f"{item['name']} training set to {item['plan']} / {item['training_intensity']}."
            refresh_window(preserve_prospect=item["name"])

        def promote():
            item = selected_prospect()
            if not item:
                return
            if item["age"] < 16:
                show_academy_notice("A prospect must be at least 16 to turn professional.", squad)
                return
            readiness = self.academy_graduation_readiness(item)
            destination = destination_var.get() or "MMA"

            def complete_promotion():
                ok, note, _fighter = self.promote_academy_prospect_to_sport(item, destination)
                if not ok:
                    show_academy_notice(note, squad)
                    return
                if item in academy.get("prospects", []):
                    academy["prospects"].remove(item)
                academy["last_scout_report"] = note
                self.news.insert(0, note)
                self.refresh_all()

            warnings = []
            if item["age"] < 18:
                warnings.append(f"age {item['age']} is before the normal age-18 pathway")
            if readiness < 55:
                warnings.append(f"graduation readiness is only {readiness}%")
            if warnings:
                request_academy_decision(
                    f"Promote {item['name']} to {destination}? " + "; ".join(warnings).capitalize() + ".",
                    complete_promotion, squad,
                )
            else:
                complete_promotion()

        def release_prospect():
            item = selected_prospect()
            if not item:
                return

            def complete_release():
                if item in academy.get("prospects", []):
                    academy["prospects"].remove(item)
                academy["last_scout_report"] = f"Released {item['name']} from the academy."
                refresh_window()

            request_academy_decision(
                f"Release {item['name']} from the academy? This cannot be undone.",
                complete_release, squad,
            )

        def run_card():
            results = self.run_academy_showcase_card(academy)
            if not results:
                show_academy_notice("No healthy academy prospect is currently eligible for a showcase bout.", squad)
                return
            academy["showcase_weeks"] = 8
            academy["last_scout_report"] = f"Manual academy showcase: {len(results)} bout(s). {results[0]}"
            refresh_window()
            show_academy_notice(
                f"Academy showcase complete: {len(results)} bout(s). The full card is available below.",
                legacy,
            )
            card_detail.config(text="\n".join(results[:10]))

        def start_network():
            scouts = [member for member in self.staff if member.get("role") == "Scout"]
            scout = next((member for member in scouts if member.get("name") == scout_var.get()), None)
            if not scout:
                show_academy_notice("Hire a Scout on the Staff screen before establishing a youth network.", overview)
                return
            cost = self.academy_scouting_network_cost(region_var.get())

            def complete_network_setup():
                ok, note = self.start_academy_network(region_var.get(), scout_var.get())
                if not ok:
                    show_academy_notice(note, overview)
                    return
                show_academy_notice(note, overview)
                self.refresh_all()

            request_academy_decision(
                f"Invest ${cost:,} to establish a youth network in {region_var.get()}? Setup takes 8 weeks.",
                complete_network_setup, overview,
            )

        def cancel_network():
            if not academy.get("network_active") and academy.get("network_weeks", 0) <= 0:
                show_academy_notice("There is no youth network to cancel.", overview)
                return

            def complete_network_cancel():
                _ok, note = self.cancel_academy_network()
                academy["last_scout_report"] = note
                refresh_window()

            request_academy_decision(
                "Cancel the current network? Every unsigned live lead will be lost.",
                complete_network_cancel, overview,
            )

        def set_philosophy():
            academy["philosophy"] = philosophy_var.get() or "Balanced MMA"
            fields = ", ".join(key.replace("_", " ").title() for key in self.academy_philosophy_fields(academy))
            academy["last_scout_report"] = f"Academy philosophy set to {academy['philosophy']}. It favours {fields}."
            refresh_window()

        def upgrade():
            cost = 50000 + max(0, academy.get("level", 1) - 1) * 35000
            if self.cash < cost:
                show_academy_notice(f"Upgrade blocked: it costs ${cost:,}.", overview)
                return

            def complete_upgrade():
                self.cash -= cost
                academy.update({"capacity": academy["capacity"] + 2, "level": academy["level"] + 1, "weekly_cost": academy["weekly_cost"] + 1800})
                academy["upgrade_spend"] = academy.get("upgrade_spend", 0) + cost
                academy["reputation"] = min(100, academy.get("reputation", 10) + 2)
                self.record_finance_transaction("Academy facilities upgrade", costs=cost)
                academy["last_scout_report"] = f"Academy upgraded to Level {academy['level']}; capacity is now {academy['capacity']}."
                self.refresh_all()

            request_academy_decision(
                f"Spend ${cost:,} to add two places and improve facilities?",
                complete_upgrade, overview,
            )

        def toggle_training():
            academy["auto_train"] = not academy.get("auto_train", True); refresh_window()

        def toggle_cards():
            academy["auto_showcases"] = not academy.get("auto_showcases", True); refresh_window()

        def toggle_graduate():
            academy["auto_graduate"] = not academy.get("auto_graduate", False); refresh_window()

        def set_auto_card_minimum(*_args):
            try:
                academy["auto_card_min_bouts"] = max(1, min(12, int(auto_card_minimum.get())))
            except (TypeError, ValueError, tk.TclError):
                academy["auto_card_min_bouts"] = 2
                auto_card_minimum.set(2)

        setup_button = ttk.Button(network_actions, text="Set Up Network", style="Accent.TButton", command=start_network)
        cancel_button = ttk.Button(network_actions, text="Cancel Network", command=cancel_network)
        philosophy_button = ttk.Button(network_actions, text="Apply Philosophy", command=set_philosophy)
        upgrade_button = ttk.Button(network_actions, text="Upgrade Academy", command=upgrade)
        training_toggle = ttk.Button(network_actions, text="Weekly Training", command=toggle_training)
        cards_toggle = ttk.Button(network_actions, text="Auto Cards", command=toggle_cards)
        graduate_toggle = ttk.Button(network_actions, text="Auto Graduate", command=toggle_graduate)
        for col, button in enumerate((setup_button, cancel_button, philosophy_button, upgrade_button, training_toggle, cards_toggle)):
            button.grid(row=0, column=col, sticky="ew", padx=3, pady=2)
        graduate_toggle.grid(row=1, column=0, columnspan=2, sticky="ew", padx=3, pady=2)
        ttk.Label(network_actions, text="Required fights", style="Inset.TLabel").grid(row=1, column=4, sticky="e", padx=3, pady=2)
        auto_card_minimum = tk.IntVar(value=academy.get("auto_card_min_bouts", 2))
        auto_card_spin = ttk.Spinbox(network_actions, from_=1, to=12, width=5, textvariable=auto_card_minimum, command=set_auto_card_minimum)
        auto_card_spin.grid(row=1, column=5, sticky="w", padx=3, pady=2)
        auto_card_spin.bind("<FocusOut>", set_auto_card_minimum)
        auto_card_spin.bind("<Return>", set_auto_card_minimum)

        sign_button = ttk.Button(lead_actions, text="Sign Selected", style="Accent.TButton", command=sign_lead)
        pass_button = ttk.Button(lead_actions, text="Pass On Lead", command=pass_lead)
        report_button = ttk.Button(lead_actions, text="Open Scout Report", command=open_lead_report)
        for col, button in enumerate((sign_button, pass_button, report_button)):
            button.grid(row=0, column=col, sticky="ew", padx=3, pady=3)

        plan_button = ttk.Button(squad_actions, text="Apply Training Plan", command=set_plan)
        profile_button = ttk.Button(squad_actions, text="Profile / Progress", command=open_prospect_profile)
        card_button = ttk.Button(squad_actions, text="Run Amateur Card", command=run_card)
        ttk.Label(squad_actions, text="Promote to", style="Inset.TLabel").grid(row=0, column=3, padx=3, sticky="e")
        destination_combo = ttk.Combobox(squad_actions, textvariable=destination_var, state="readonly")
        destination_combo.grid(row=0, column=4, sticky="ew", padx=3)
        promote_button = ttk.Button(squad_actions, text="Promote", style="Accent.TButton", command=promote)
        release_button = ttk.Button(squad_actions, text="Release", command=release_prospect)
        for col, button in ((0, plan_button), (1, profile_button), (2, card_button), (5, promote_button), (6, release_button)):
            button.grid(row=0, column=col, sticky="ew", padx=3, pady=3)

        replay_button = ttk.Button(card_controls, text="Replay Selected Card", style="Accent.TButton", command=replay_selected_card)
        replay_button.pack(side="left", padx=4, pady=3)
        alumni_profile_button = ttk.Button(alumni_controls, text="Open Graduate Fighter Profile", style="Accent.TButton", command=open_alumnus_profile)
        alumni_profile_button.pack(side="left", padx=4, pady=3)

        def update_network_preview(*_args):
            scouts = [member for member in self.staff if member.get("role") == "Scout"]
            names = [member.get("name", "") for member in scouts]
            scout_combo["values"] = names
            if scout_var.get() not in names:
                scout_var.set(academy.get("network_scout") if academy.get("network_scout") in names else (names[0] if names else ""))
            scout = next((member for member in scouts if member.get("name") == scout_var.get()), None)
            cost = self.academy_scouting_network_cost(region_var.get())
            distance = self.academy_region_distance(region_var.get())
            if scout:
                judging = scout.get("fighter_judging", scout.get("skill", 45))
                potential = scout.get("potential_judging", scout.get("skill", 45))
                regional = scout.get("regional_knowledge", 45)
                reliability = scout.get("reliability", 45)
                scout_score = (judging + potential) / 2
                expected = max(30, min(94, round(scout_score + academy.get("reputation", 10) * .08)))
                networking = scout.get("networking", scout.get("skill", 45))
                lead_chance = max(.20, min(.80, .20 + networking / 210 + reliability / 500))
                preview.config(text=f"{scout.get('name')} | Fighter judgement {judging} | Potential {potential} | Regional knowledge {regional} | Reliability {reliability}\nEstimated setup ${cost:,} | Distance tier {distance} | First-report confidence around {expected}% | Weekly lead chance about {lead_chance:.0%}; reports narrow weekly.")
            else:
                preview.config(text=f"No Scout hired. Hire one on Staff before setup. Selected-region setup would cost ${cost:,} (distance tier {distance}).")
            setup_button.config(text=f"Set Up Network (${cost:,})")
            set_enabled(setup_button, bool(scout) and not academy.get("network_active") and academy.get("network_weeks", 0) <= 0 and self.cash >= cost)

        def update_context_actions(_event=None):
            lead = selected_lead()
            prospect = selected_prospect()
            card = selected_card()
            alumnus = selected_alumnus()
            set_enabled(sign_button, bool(lead) and len(academy.get("prospects", [])) < academy.get("capacity", 0) and self.cash >= (lead.get("signing_cost", 0) if lead else 0))
            set_enabled(pass_button, bool(lead)); set_enabled(report_button, bool(lead))
            if lead:
                set_readonly_text(lead_feedback, self.academy_lead_report(lead))
            else:
                set_readonly_text(lead_feedback, "Select a live lead to inspect the full scouting report here. Reports become more accurate while the lead remains available.")
            for button in (plan_button, profile_button, promote_button, release_button): set_enabled(button, bool(prospect))
            set_enabled(replay_button, bool(card and card.get("fight_logs")))
            fighter = self.academy_alumnus_fighter(alumnus.get("name", "")) if alumnus else None
            set_enabled(alumni_profile_button, bool(fighter))
            if prospect:
                focus_var.set(prospect.get("plan", "Automatic")); intensity_var.set(prospect.get("training_intensity", "Standard"))
                recommendation, reason, recommended_fields = self.academy_focus_recommendation(prospect)
                fields = ", ".join(key.replace("_", " ").title() for key in recommended_fields)
                risk = {"Light": "low fatigue / low injury risk", "Standard": "balanced workload", "Intensive": "high gain chance / higher fatigue and injury risk", "Recovery": "recovery only"}.get(intensity_var.get(), "balanced workload")
                plan_hint.config(text=f"Recommended {recommendation}: targets {fields}. {reason} Current intensity: {risk}.")
            else:
                plan_hint.config(text="Select a prospect to see recommended focus, affected attributes and workload risk.")
            if card:
                card_detail.config(text=f"{card.get('event_name')} | {card.get('date')} | {card.get('recap')}\n" + " | ".join(card.get("results", [])[:2]))
            else:
                card_detail.config(text="Select a card to inspect or replay it.")

        def refresh_window(preserve_prospect=None):
            try:
                if not window.winfo_exists():
                    return
            except tk.TclError:
                return
            self.repair_academy(academy)
            selected_lead_name = lead_tree.item(lead_tree.selection()[0], "values")[0] if lead_tree.selection() else None
            selected_prospect_name = preserve_prospect or (prospect_tree.item(prospect_tree.selection()[0], "values")[0] if prospect_tree.selection() else None)
            selected_card_name = card_tree.item(card_tree.selection()[0], "values")[0] if card_tree.selection() else None
            selected_alumnus_name = alumni_tree.item(alumni_tree.selection()[0], "values")[0] if alumni_tree.selection() else None
            net = f"Building {academy.get('network_region', '')}: {academy.get('network_weeks', 0)} weeks left" if academy.get("network_weeks", 0) > 0 else f"Active in {academy.get('network_region', '')} via {academy.get('network_scout', 'Scout')}" if academy.get("network_active") else "No active network"
            next_card = f"{academy.get('showcase_weeks', 8)} week(s)" if academy.get("auto_showcases", True) else "Automatic cards off"
            summary.config(text=f"Level {academy.get('level', 0)} | Reputation {academy.get('reputation', 10)}/100 | Squad {len(academy.get('prospects', []))}/{academy.get('capacity', 0)} | Weekly ${academy.get('weekly_cost', 0):,}")
            total_invested = sum(academy.get(key, 0) for key in ("build_spend", "operating_spend", "signing_spend", "upgrade_spend", "network_spend"))
            runway = self.cash // max(1, academy.get("weekly_cost", 0))
            overview_status.config(text=f"{academy.get('philosophy', 'Balanced MMA')} | {net}\nWeekly training {'ON' if academy.get('auto_train', True) else 'PAUSED'} | Next showcase: {next_card} | Academy-only cash runway {runway}w | Total invested ${total_invested:,} | Cards {academy.get('total_cards', 0)} | Graduates {academy.get('total_graduates', 0)}")
            report_box.config(state="normal"); report_box.delete("1.0", "end"); report_box.insert("end", academy.get("last_scout_report") or "Hire a Scout and establish a regional network to discover youth prospects."); report_box.config(state="disabled")
            set_readonly_text(lead_feedback, "Select a live lead to inspect the full scouting report here. Reports become more accurate while the lead remains available.")
            philosophy_var.set(academy.get("philosophy", "Balanced MMA"))
            weeks = academy.get("network_weeks", 0)
            network_progress["value"] = 8 if academy.get("network_active") else max(0, 8 - weeks)
            network_progress_text.config(text="Network active" if academy.get("network_active") else f"{weeks} week(s) left" if weeks else "Not established")
            cancel_enabled = academy.get("network_active") or weeks > 0
            set_enabled(cancel_button, cancel_enabled)
            upgrade_cost = 50000 + max(0, academy.get("level", 1) - 1) * 35000
            upgrade_button.config(text=f"Upgrade (+2) ${upgrade_cost:,}")
            set_enabled(upgrade_button, self.cash >= upgrade_cost)
            training_toggle.config(text=f"Weekly Training: {'ON' if academy.get('auto_train', True) else 'PAUSED'}")
            cards_toggle.config(text=f"Auto Cards: {'ON' if academy.get('auto_showcases', True) else 'OFF'}")
            graduate_toggle.config(text=f"Auto Graduate: {'ON' if academy.get('auto_graduate', False) else 'OFF'}")
            destinations = ["MMA"] + sorted(getattr(self, "player_combat_divisions", {}).keys())
            destination_combo["values"] = destinations
            if destination_var.get() not in destinations: destination_var.set("MMA")

            lead_tree.delete(*lead_tree.get_children())
            for index, item in enumerate(academy.get("talent_pool", [])):
                self.repair_academy_prospect(item)
                current = item.get("current_range", (item.get("rating", 40), item.get("rating", 40)))
                potential = item.get("potential_range", (item.get("potential", 70), item.get("potential", 70)))
                tag = "urgent" if item.get("weeks_to_sign", 0) <= 1 else "strong" if potential[1] >= 90 else ""
                iid = f"lead:{index}"
                gender = str(item.get("gender", "")).strip()[:1].upper() or "?"
                lead_tree.insert("", "end", iid=iid, tags=(tag,), values=(item.get("name"), gender, item.get("age"), item.get("region"), item.get("amateur_weight"), f"{current[0]}-{current[1]}", f"{potential[0]}-{potential[1]}", f"{item.get('scout_confidence', 0)}%", f"${item.get('signing_cost', 0):,}", f"{item.get('weeks_to_sign', 0)}w"))
                if item.get("name") == selected_lead_name: lead_tree.selection_set(iid); lead_tree.see(iid)

            prospect_tree.delete(*prospect_tree.get_children())
            for index, item in enumerate(academy.get("prospects", [])):
                self.repair_academy_prospect(item)
                ready = self.academy_graduation_readiness(item); trend = self.academy_prospect_trend(item)
                grad_label, _grad_reason = self.academy_graduation_recommendation(item)
                status = f"INJ {item.get('injured')}w" if item.get("injured", 0) else "Ready" if ready >= 75 else "Training"
                tag = "injured" if item.get("injured", 0) else "ready" if grad_label == "GRADUATE NOW" else ""
                iid = f"prospect:{index}"
                gender = str(item.get("gender", "")).strip()[:1].upper() or "?"
                prospect_tree.insert("", "end", iid=iid, tags=(tag,), values=(item.get("name"), gender, item.get("age"), item.get("amateur_weight"), f"{item.get('plan', 'Automatic')} / {item.get('training_intensity', 'Standard')}", f"{item.get('amateur_w', 0)}-{item.get('amateur_l', 0)}-{item.get('amateur_d', 0)}", f"{item.get('rating')}/{item.get('potential')}", f"{trend:+}", f"{ready}%", grad_label, item.get("fatigue", 0), status))
                if item.get("name") == selected_prospect_name: prospect_tree.selection_set(iid); prospect_tree.see(iid)

            card_tree.delete(*card_tree.get_children())
            for index, card in enumerate(academy.get("card_history", [])):
                iid = f"card:{index}"; card_tree.insert("", "end", iid=iid, values=(card.get("event_name"), card.get("date"), len(card.get("results", [])), card.get("recap", "")))
                if card.get("event_name") == selected_card_name: card_tree.selection_set(iid); card_tree.see(iid)
            alumni_tree.delete(*alumni_tree.get_children())
            for index, row in enumerate(academy.get("alumni", [])):
                iid = f"alumnus:{index}"; alumni_tree.insert("", "end", iid=iid, values=(row.get("name"), row.get("destination"), row.get("amateur_record"), row.get("professional_record"), row.get("current_rating"), row.get("title_wins", 0), "Active" if row.get("active", True) else "Retired"))
                if row.get("name") == selected_alumnus_name: alumni_tree.selection_set(iid); alumni_tree.see(iid)
            selected_facility = facility_tree.selection()[0] if facility_tree.selection() else None
            facility_tree.delete(*facility_tree.get_children())
            owned = set(academy.get("upgrades", []) or [])
            for upgrade in self.academy_upgrade_catalog():
                installed = upgrade["id"] in owned
                iid = f"facility:{upgrade['id']}"
                facility_tree.insert("", "end", iid=iid, tags=("owned",) if installed else (), values=(upgrade["name"], upgrade["effect"], f"${upgrade['cost']:,}", "Installed" if installed else "Available"))
            if selected_facility and facility_tree.exists(selected_facility):
                facility_tree.selection_set(selected_facility)
            installed_count = len(owned)
            set_enabled(buy_button, installed_count < len(self.academy_upgrade_catalog()))
            update_network_preview(); update_context_actions()

        def close_window():
            self._academy_window_refresh = None
            self._academy_window = None
            window.destroy()

        for variable in (region_var, scout_var): variable.trace_add("write", update_network_preview)
        lead_tree.bind("<<TreeviewSelect>>", update_context_actions); lead_tree.bind("<Double-1>", lambda _event: open_lead_report())
        prospect_tree.bind("<<TreeviewSelect>>", update_context_actions); prospect_tree.bind("<Double-1>", lambda _event: open_prospect_profile())
        card_tree.bind("<<TreeviewSelect>>", update_context_actions); card_tree.bind("<Double-1>", lambda _event: replay_selected_card())
        alumni_tree.bind("<<TreeviewSelect>>", update_context_actions); alumni_tree.bind("<Double-1>", lambda _event: open_alumnus_profile())
        window.protocol("WM_DELETE_WINDOW", close_window)
        self._academy_window_refresh = refresh_window
        refresh_window()

    def company_selected_name(self):
        """Name of the company selected in the standings table (or None)."""
        tree = getattr(self, "company_list", None)
        if tree is None:
            return None
        try:
            selection = tree.selection()
        except Exception:
            return None
        if not selection:
            return None
        return tree.set(selection[0], "name") or None

    def company_selected_identity(self):
        tree = getattr(self, "company_list", None)
        if tree is None:
            return None, None
        selection = tree.selection()
        if not selection:
            return None, None
        return tree.set(selection[0], "name") or None, tree.set(selection[0], "sport") or "MMA"

    def select_company_by_name(self, name, sport=None):
        tree = getattr(self, "company_list", None)
        if tree is None or not name:
            return False
        for iid in tree.get_children(""):
            if tree.set(iid, "name") == name and (sport is None or tree.set(iid, "sport") == sport):
                tree.selection_set(iid)
                tree.see(iid)
                return True
        return False

    _COMPANY_SORT_KEYS = {
        "Power ranking": "power", "Richest": "cash", "Most stable": "stability",
        "Best reputation": "reputation", "Deepest roster": "roster_count", "Most champions": "champs",
    }

    def refresh_companies(self):
        tree = getattr(self, "company_list", None)
        if tree is None:
            return
        previous = self.company_selected_name()
        rows = self.industry_standings_rows()
        self._standings_rows_by_key = {
            self.standings_history_key(row["sport"], row["name"]): row for row in rows
        }

        # Populate filter option lists once we know the live sports and regions.
        sports = ["All Sports"] + sorted({row["sport"] for row in rows})
        regions = ["All Regions"] + sorted({row["region"] for row in rows})
        if hasattr(self, "company_sport_combo"):
            self.company_sport_combo.configure(values=sports)
            if self.company_sport_filter.get() not in sports:
                self.company_sport_filter.set("All Sports")
        if hasattr(self, "company_region_combo"):
            self.company_region_combo.configure(values=regions)
            if self.company_region_filter.get() not in regions:
                self.company_region_filter.set("All Regions")

        sport_choice = self.company_sport_filter.get()
        region_choice = self.company_region_filter.get()
        visible = [
            row for row in rows
            if (sport_choice in ("All Sports", row["sport"]))
            and (region_choice in ("All Regions", row["region"]))
        ]
        sort_key = self._COMPANY_SORT_KEYS.get(self.company_sort_by.get(), "power")
        visible.sort(key=lambda row: -row[sort_key])

        tree.delete(*tree.get_children())
        for row in visible:
            move = self.standings_move(row["sport"], row["name"])
            move_text = f"▲{move}" if move > 0 else f"▼{abs(move)}" if move < 0 else "—"
            tags = [f"tier_{row['tier'].lower()}"]
            if row["player"]:
                tags.append("player")
            iid = self.standings_history_key(row["sport"], row["name"])
            tree.insert("", "end", iid=iid, tags=tuple(tags), values=(
                row["rank"], move_text, row["name"], row["sport"], row["region"], row["tier"],
                row["power"], f"{row['reputation']}%", f"{row['stability']}%", f"${row['cash']:,}",
                row["roster_count"], row["champs"], row["stars"],
            ))
        if not self.select_company_by_name(previous):
            children = tree.get_children("")
            if children:
                tree.selection_set(children[0])
        if hasattr(self, "company_standings_summary"):
            self.company_standings_summary.config(text=f"{len(visible)} shown / {len(rows)} tracked")
        if hasattr(self, "return_to_spectator_button"):
            self.return_to_spectator_button.configure(state="disabled" if getattr(self, "spectator_mode", False) else "normal")
        self.refresh_company_profile()

    def _write_company_profile(self, text):
        box = getattr(self, "company_profile", None)
        if box is None:
            return
        box.config(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.config(state="disabled")

    def refresh_company_profile(self):
        tree = getattr(self, "company_list", None)
        if tree is None:
            return
        selection = tree.selection()
        if not selection:
            self._write_company_profile("Select a company to view its profile.")
            self._render_company_breakdown(None)
            return
        iid = selection[0]
        name = tree.set(iid, "name")
        sport = tree.set(iid, "sport")
        row = (getattr(self, "_standings_rows_by_key", {}) or {}).get(self.standings_history_key(sport, name))
        total = len(getattr(self, "_standings_rows_by_key", {}) or {})
        header = ""
        if row:
            header = (
                f"{name}\n{row['tier']} tier | Rank #{row['rank']} of {total} | Power {row['power']}\n"
                f"Sport: {sport} | Region: {row['region']}\n"
                f"Credibility: {row['reputation']}% | Stability: {row['stability']}% | Cash: ${row['cash']:,}\n"
                f"Roster: {row['roster_count']} | Champions: {row['champs']} | Stars: {row['stars']}\n"
            )

        is_player_mma = (name == self.player_company_name and sport == "MMA")
        promo = next((p for p in self.promotions if p.name == name), None) if sport == "MMA" else None

        if is_player_mma:
            roster = self.roster
            upcoming = [f"{e['name']} ({self.event_date_label(e)})" for e in self.sorted_scheduled_events()[:5]]
            recent = self.result_history[:5]
            text = header + f"\n{self.player_reputation}\n"
        elif promo is not None:
            roster = promo.roster
            upcoming = [f"{promo.name} {promo.event_counter + i}" for i in range(1, 6)]
            recent = promo.show_history[:5] if promo.show_history else []
            strategy = self.promotion_strategy(promo)
            executive = getattr(promo, "executive", {}) or {}
            prospect_count = sum(1 for fighter in roster if fighter.age <= 26 and fighter.potential - fighter.overall >= 7)
            star_count = sum(1 for fighter in roster if fighter.popularity >= 55 or fighter.overall >= 82)
            pressure = "High" if promo.cash < 150_000 or promo.stability < 35 else "Medium" if promo.cash < 500_000 or promo.stability < 55 else "Low"
            booking_why = f"Recent cards are likely driven by {strategy.get('current_mode', 'balanced booking').lower()}, cash pressure {pressure.lower()}, and a roster mix of {prospect_count} prospects / {star_count} stars."
            text = header + (
                f"\n{promo.reputation}\n\nEXECUTIVE: {executive.get('name', 'Unknown')} ({executive.get('archetype', 'Operator')})\n"
                f"Board Security: {executive.get('job_security', 0)}% | Company Legacy: {getattr(promo, 'legacy_score', 0)}\n"
                f"Board mandate: {executive.get('board_mandate', 'None')} - {executive.get('mandate_progress', 0)}% (target {executive.get('mandate_target', 0):,}, deadline {self.format_game_date(executive.get('mandate_deadline', self.month), 1, include_week=False)})\n\n"
                f"AI STRATEGY READ\nIdentity: {strategy.get('identity', 'Balanced Growth')}\nDirection: {strategy.get('current_mode', 'Balanced')}\n"
                f"Media voice: {strategy.get('media_voice', 'Reliable fights')}\nFinancial pressure: {pressure}\n"
                f"Roster tilt: {prospect_count} prospects / {star_count} stars\nWhy they book/sign this way: {booking_why}\n"
            )
        else:
            world = (getattr(self, "combat_sport_worlds", {}) or {}).get(sport, {})
            roster = row["roster_ref"] if row else []
            upcoming = []
            recent = (world.get("event_history", []) or [])[:5]
            owner = "your child promotion" if (row and row["player"]) else "AI flagship circuit"
            text = header + f"\n{sport} circuit ({owner})\nCircuit strategy: {world.get('strategy', 'Merit Ladder')}\n"

        by_weight = []
        for weight in WEIGHTS:
            names = [f.name for f in roster if f.weight == weight][:8]
            if names:
                by_weight.append(f"{weight}: {', '.join(names)}")
        text += "\nCURRENT ROSTER\n" + ("\n".join(by_weight[:10]) or "> None")
        text += "\n\nUPCOMING EVENTS CALENDAR\n" + ("\n".join(f"> {item}" for item in upcoming) if upcoming else "> None")
        text += "\n\nRECENT EVENTS\n" + ("\n".join(f"> {item}" for item in recent) if recent else "> None")
        self._write_company_profile(text)
        self._render_company_breakdown(row)
        if hasattr(self, "take_control_company_button"):
            can_take_over = bool(row and row["sport"] == "MMA" and not row["player"] and not (promo is not None and getattr(promo, "is_regional_feeder", False)))
            self.take_control_company_button.configure(state="normal" if can_take_over else "disabled")

    def _closest_rivals(self, sport, name, span=2):
        rows = sorted((getattr(self, "_standings_rows_by_key", {}) or {}).values(), key=lambda r: r["rank"])
        index = next((i for i, row in enumerate(rows) if row["name"] == name and row["sport"] == sport), None)
        if index is None:
            return []
        return rows[max(0, index - span):index + span + 1]

    def _render_company_breakdown(self, row):
        box = getattr(self, "company_breakdown", None)
        if box is not None:
            box.config(state="normal")
            box.delete("1.0", "end")
            if not row:
                box.insert("end", "Select a company to see its power breakdown.")
            else:
                components = row["components"]
                lines = [f"POWER {row['power']}   ({row['tier']} tier)", ""]
                for label, value in components:
                    lines.append(f"  {label:<16}{round(value):>5}")
                lines.append("")
                lines.append("CLOSEST RIVALS")
                for rival in self._closest_rivals(row["sport"], row["name"]):
                    marker = ">" if rival["name"] == row["name"] and rival["sport"] == row["sport"] else " "
                    lines.append(f"{marker}#{rival['rank']:<3}{rival['name'][:19]:<20}{rival['power']}")
                box.insert("end", "\n".join(lines))
            box.config(state="disabled")
        self.draw_company_sparkline(row)

    def draw_company_sparkline(self, row):
        canvas = getattr(self, "company_sparkline", None)
        if canvas is None:
            return
        canvas.delete("all")
        width = int(canvas.winfo_width() or 0) or 240
        height = int(canvas.winfo_height() or 0) or 38
        series = self.standings_power_series(row["sport"], row["name"]) if row else []
        if len(series) < 2:
            canvas.create_text(width // 2, height // 2, text="Trend builds as months pass", fill="#8a8f97", font=("Tahoma", 8))
            return
        low, high = min(series), max(series)
        span = max(1, high - low)
        pad = 4
        points = []
        for index, value in enumerate(series):
            x = pad + (width - 2 * pad) * index / (len(series) - 1)
            y = height - pad - (height - 2 * pad) * (value - low) / span
            points.extend((x, y))
        color = "#3f9d5a" if series[-1] >= series[0] else "#c0533f"
        canvas.create_line(*points, fill=color, width=2, smooth=True)

    def company_rank(self, name):
        rows = [(self.player_company_name, self.company_power_score(self.player_company_name, self.roster, self.company_pop, self.company_stability, self.cash))]
        rows += [(p.name, self.company_power_score(p.name, p.roster, p.reputation_score, p.stability, p.cash)) for p in self.promotions]
        rows = sorted(rows, key=lambda item: -item[1])
        for index, row in enumerate(rows, 1):
            if row[0] == name:
                return index
        return len(rows)

    def _standings_entity(self, name, sport, region, roster, reputation, stability, cash, player, champion_count=None):
        """Normalise one fight-business entity into a ranked-standings row."""
        active = [f for f in roster if not getattr(f, "retired", False)]
        if champion_count is None:
            champion_count = sum(1 for fighter in active if getattr(fighter, "champion", False))
        components = self.company_power_components(roster, reputation, stability, cash, champion_count)
        power = round(sum(value for _label, value in components))
        tier, tier_color = self.company_tier(power)
        champs = int(champion_count)
        stars = sum(1 for f in active if getattr(f, "popularity", 0) >= 55 or getattr(f, "overall", 0) >= 82)
        return {
            "name": name, "sport": sport, "region": region or "Worldwide", "player": bool(player),
            "reputation": int(reputation), "stability": int(stability), "cash": int(cash),
            "roster_count": len(active), "power": power, "tier": tier, "tier_color": tier_color,
            "champs": champs, "stars": stars, "roster_ref": roster, "components": components,
        }

    def industry_standings_rows(self):
        """Every promotion and combat-sport circuit, scored and ranked together."""
        rows = [self._standings_entity(
            self.player_company_name, "MMA", self.player_region, self.roster,
            self.company_pop, self.company_stability, self.cash, True,
        )]
        for promo in self.promotions:
            rows.append(self._standings_entity(
                promo.name, "MMA", promo.region, promo.roster,
                promo.reputation_score, promo.stability, promo.cash, False,
            ))
        for sport, world in (getattr(self, "combat_sport_worlds", {}) or {}).items():
            flagship = world.get("promotion", sport)
            flagship_state = self.ensure_combat_sport_circuit_state(sport, world, flagship, False)
            rows.append(self._standings_entity(
                flagship, sport, world.get("region", "Worldwide"),
                self.combat_sport_roster(sport, flagship),
                flagship_state.get("reputation", world.get("reputation", 50)),
                flagship_state.get("stability", world.get("stability", 60)),
                flagship_state.get("cash", world.get("cash", 0)), False,
                sum(1 for holder in flagship_state.get("titles", {}).values() if holder),
            ))
            division = (getattr(self, "player_combat_divisions", {}) or {}).get(sport)
            if division:
                player_state = self.ensure_combat_sport_circuit_state(
                    sport, world, division.get("promotion_name", self.player_company_name), True
                )
                rows.append(self._standings_entity(
                    division.get("promotion_name", self.player_company_name), sport, self.player_region,
                    self.combat_sport_roster(sport, division.get("promotion_name", self.player_company_name)),
                    player_state.get("reputation", self.company_pop),
                    player_state.get("stability", self.company_stability),
                    player_state.get("cash", division.get("profit_total", 0)), True,
                    sum(1 for holder in player_state.get("titles", {}).values() if holder),
                ))
        rows.sort(key=lambda row: -row["power"])
        for index, row in enumerate(rows, 1):
            row["rank"] = index
        return rows

    @staticmethod
    def standings_history_key(sport, name):
        return f"{sport}|{name}"

    def snapshot_industry_standings(self, max_points=24):
        """Record each entity's monthly rank and power for move arrows and sparklines."""
        history = getattr(self, "standings_history", None)
        if not isinstance(history, dict):
            history = self.standings_history = {}
        rows = self.industry_standings_rows()
        live = set()
        for row in rows:
            key = self.standings_history_key(row["sport"], row["name"])
            live.add(key)
            entry = history.setdefault(key, {"rank": [], "power": []})
            entry["rank"] = (entry.get("rank", []) + [row["rank"]])[-max_points:]
            entry["power"] = (entry.get("power", []) + [row["power"]])[-max_points:]
        for key in [key for key in history if key not in live]:
            del history[key]
        return history

    def standings_move(self, sport, name):
        """Rank change since last snapshot: (+n climbed, -n dropped, 0 unknown/new)."""
        entry = (getattr(self, "standings_history", {}) or {}).get(self.standings_history_key(sport, name), {})
        ranks = entry.get("rank", [])
        if len(ranks) < 2:
            return 0
        return ranks[-2] - ranks[-1]

    def standings_power_series(self, sport, name):
        entry = (getattr(self, "standings_history", {}) or {}).get(self.standings_history_key(sport, name), {})
        return list(entry.get("power", []))

    def selected_company_data(self):
        """Return a normalized read-only view of the company selected in the browser."""
        name, sport = self.company_selected_identity()
        if not name:
            return None
        row = (getattr(self, "_standings_rows_by_key", {}) or {}).get(self.standings_history_key(sport, name), {})
        if sport != "MMA":
            world = (getattr(self, "combat_sport_worlds", {}) or {}).get(sport, {})
            division = (getattr(self, "player_combat_divisions", {}) or {}).get(sport, {})
            player_owned = bool(division and division.get("promotion_name") == name)
            state = self.ensure_combat_sport_circuit_state(sport, world, name, player_owned)
            roster = self.combat_sport_roster(sport, name)
            events = list(state.get("events", [])) if player_owned else []
            history = list(state.get("events", [])) if player_owned else list(world.get("event_history", []))
            return {
                "name": name, "sport": sport, "combat_sport": True, "player": player_owned,
                "rank": row.get("rank", "-"), "roster": roster, "region": row.get("region", world.get("region", "Worldwide")),
                "reputation": f"{sport} combat-sport circuit", "score": int(state.get("reputation", row.get("reputation", 50))),
                "stability": int(state.get("stability", row.get("stability", 60))), "cash": int(state.get("cash", row.get("cash", 0))),
                "belts": dict(state.get("titles", {})), "interim_belts": {}, "special_belts": {},
                "scheduled_events": events, "show_history": history, "finance": {"history": state.get("finance_history", [])},
                "staff": [], "strategy": {"identity": state.get("strategy", world.get("strategy", "Merit Ladder"))}, "executive": {},
            }
        if name == self.player_company_name:
            return {
                "name": name, "sport": "MMA", "combat_sport": False, "player": True, "rank": row.get("rank", self.company_rank(name)), "roster": self.roster, "region": self.player_region,
                "reputation": self.player_reputation, "score": self.company_pop, "stability": self.company_stability,
                "cash": self.cash, "belts": self.belts, "interim_belts": self.interim_belts, "special_belts": self.special_belts,
                "scheduled_events": self.sorted_scheduled_events(), "show_history": self.result_history,
                "finance": self.finance, "staff": self.staff, "strategy": {}, "executive": {},
            }
        promo = next((item for item in self.promotions if item.name == name), None)
        if not promo:
            return None
        return {
            "name": promo.name, "sport": "MMA", "combat_sport": False, "player": False, "rank": row.get("rank", self.company_rank(name)), "roster": promo.roster, "region": promo.region,
            "reputation": promo.reputation, "score": promo.reputation_score, "stability": promo.stability,
            "cash": promo.cash, "belts": promo.belts or {}, "interim_belts": promo.interim_belts or {}, "special_belts": promo.special_belts or {},
            "scheduled_events": promo.scheduled_events or [], "show_history": promo.show_history or [],
            "finance": promo.finance or {}, "staff": promo.staff or [],
            "strategy": self.promotion_strategy(promo), "executive": getattr(promo, "executive", {}) or {},
        }

    def open_selected_company_section(self, section):
        data = self.selected_company_data()
        if not data:
            messagebox.showinfo("No company", "Select a company first.")
            return
        if data.get("combat_sport") or not data["player"]:
            self.open_selected_company_hub(section)
            return
        if section == "Roster":
            self.select_tab("roster")
        elif section == "Rankings":
            self.ranking_scope.set(self.player_company_name)
            self.refresh_rankings()
            self.select_tab("rankings")
        elif section == "Belts":
            self.select_tab("company_editor")
        elif section == "Events":
            self.select_tab("booking")
        elif section == "Results":
            self.result_search.set(self.player_company_name)
            self.refresh_results()
            self.select_tab("results")
        elif section == "Finance":
            self.select_tab("finance")
        elif section == "Staff":
            self.select_tab("staff")

    def open_selected_company_hub(self, focus="Overview"):
        data = self.selected_company_data()
        if not data:
            messagebox.showinfo("No company", "Select a company first.")
            return
        window = tk.Toplevel(self.root)
        window.title(f"MMA Warriors - {data['name']}")
        window.geometry("1040x680")
        window.minsize(850, 540)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=data["name"].upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text=f"#{data.get('rank', '-')} | {data.get('sport', 'MMA')} | {data['region']} | credibility {data['score']}% | stability {data['stability']}%", style="ScreenTitle.TLabel").pack(side="right", padx=10)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        tabs = {}
        for title in ("Overview", "Boardroom", "Roster", "Rankings", "Belts", "Events", "Results", "Finance", "Staff"):
            tab = ttk.Frame(notebook, style="Chrome.TFrame")
            notebook.add(tab, text=title)
            tabs[title] = tab

        overview = tk.Text(tabs["Overview"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=14, pady=14)
        overview.pack(fill="both", expand=True)
        strategy, executive = data["strategy"], data["executive"]
        champs = list(data["belts"].values()) if data.get("combat_sport") else [fighter.name for fighter in data["roster"] if fighter.champion]
        champs = [name for name in champs if name]
        top = sorted(data["roster"], key=self.p4p_value, reverse=True)[:5]
        overview.insert("end", f"{data['reputation']}\n\nRegion: {data['region']}\nCash reserve: ${data['cash']:,}\nRoster: {len(data['roster'])} fighters\nChampions: {', '.join(champs) if champs else 'None'}\n\n")
        if strategy:
            overview.insert("end", f"Identity: {strategy.get('identity', 'Balanced Growth')}\nCurrent direction: {strategy.get('current_mode', 'Balanced')}\nMedia voice: {strategy.get('media_voice', 'Reliable fights')}\n\n")
        if executive:
            overview.insert("end", f"Executive: {executive.get('name', 'Unknown')} ({executive.get('archetype', 'Operator')})\nBoard security: {executive.get('job_security', 0)}%\n\n")
        overview.insert("end", "TOP FIGHTERS\n" + "\n".join(f"- {fighter.name} | {fighter.weight} | {fighter.record} | OVR {fighter.overall}" for fighter in top))
        overview.config(state="disabled")

        boardroom = tk.Text(tabs["Boardroom"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=14, pady=14)
        boardroom.pack(fill="both", expand=True)
        if executive:
            history = executive.get("mandate_history", []) or []
            deadline = self.format_game_date(executive.get("mandate_deadline", self.month), 4, include_week=False)
            notes = "\n".join(f"- {item.get('year', '')}: {self.format_game_date_text(item.get('note', ''))}" for item in history[-8:]) or "- No completed or missed mandates recorded yet."
            boardroom.insert("end", f"EXECUTIVE\n{executive.get('name', 'Unknown')} — {executive.get('archetype', 'Operator')}\n\nAggression: {executive.get('aggression', 50)} | Patience: {executive.get('patience', 50)} | Discipline: {executive.get('discipline', 50)}\nJob security: {executive.get('job_security', 0)}%\n\nACTIVE BOARD MANDATE\n{executive.get('board_mandate', 'None')}\nProgress: {executive.get('mandate_progress', 0)}% | Target: {executive.get('mandate_target', 0):,} | Deadline: {deadline}\n\nMandates influence financial recovery, prospect development, and card frequency.\n\nRECENT BOARD NOTES\n{notes}")
        else:
            boardroom.insert("end", "The player promotion is governed through the Owner Goals panel in Inbox.")
        boardroom.config(state="disabled")

        roster_filters = ttk.Frame(tabs["Roster"], style="Inset.TFrame")
        roster_filters.pack(fill="x", padx=8, pady=(8, 0))
        hub_roster_gender = tk.StringVar(value="All")
        hub_roster_division = tk.StringVar(value="All")
        ttk.Label(roster_filters, text="Gender", style="Inset.TLabel").pack(side="left", padx=(6, 3), pady=5)
        gender_combo = ttk.Combobox(
            roster_filters,
            textvariable=hub_roster_gender,
            values=("All", "Male", "Female"),
            width=10,
            state="readonly",
        )
        gender_combo.pack(side="left", padx=(0, 10), pady=5)
        ttk.Label(roster_filters, text="Division", style="Inset.TLabel").pack(side="left", padx=(0, 3), pady=5)
        division_combo = ttk.Combobox(
            roster_filters,
            textvariable=hub_roster_division,
            values=["All"] + [weight for weight in WEIGHTS if any(fighter.weight == weight for fighter in data["roster"])],
            width=18,
            state="readonly",
        )
        division_combo.pack(side="left", padx=(0, 10), pady=5)
        roster_filter_count = ttk.Label(roster_filters, text="", style="Inset.TLabel")
        roster_filter_count.pack(side="right", padx=6, pady=5)

        roster_tree = ttk.Treeview(tabs["Roster"], columns=("name", "g", "division", "record", "ovr", "pop", "status"), show="headings")
        for column, label, width in (("name", "Fighter", 220), ("g", "G", 42), ("division", "Division", 120), ("record", "W-L-D", 86), ("ovr", "OVR", 60), ("pop", "Pop", 60), ("status", "Status", 130)):
            roster_tree.heading(column, text=label)
            roster_tree.column(column, width=width, anchor="center")
        roster_tree.column("name", anchor="w")
        self.make_tree_sortable(roster_tree)
        hub_roster_rows = {}

        def populate_hub_roster(*_event):
            selected = roster_tree.selection()
            filtered = [
                fighter for fighter in data["roster"]
                if (hub_roster_gender.get() == "All" or fighter.gender == hub_roster_gender.get())
                and (hub_roster_division.get() == "All" or fighter.weight == hub_roster_division.get())
            ]
            roster_tree.delete(*roster_tree.get_children())
            hub_roster_rows.clear()
            for row_index, fighter in enumerate(sorted(filtered, key=lambda item: (-self.p4p_value(item), item.name))):
                row_id = self.fighter_tree_row_id("company-roster", fighter, row_index)
                hub_roster_rows[row_id] = fighter
                stats_visible = self.fighter_profile_stats_visible(fighter, data["name"])
                roster_tree.insert("", "end", iid=row_id, values=(self.fighter_display_name(fighter), fighter.gender[0], fighter.weight, fighter.record, fighter.overall if stats_visible else "Scout", fighter.popularity if stats_visible else "Scout", fighter.status))
            roster_filter_count.config(text=f"Showing {len(filtered)} of {len(data['roster'])} fighters")
            if selected and selected[0] in roster_tree.get_children():
                roster_tree.selection_set(selected[0])

        gender_combo.bind("<<ComboboxSelected>>", populate_hub_roster)
        division_combo.bind("<<ComboboxSelected>>", populate_hub_roster)
        roster_tree.pack(fill="both", expand=True, padx=8, pady=8)
        populate_hub_roster()
        roster_tree.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(hub_roster_rows.get(roster_tree.selection()[0])) if roster_tree.selection() else None)

        rankings = ttk.Treeview(tabs["Rankings"], columns=("rank", "fighter", "division", "record", "ovr", "score"), show="headings")
        for column, label, width in (("rank", "Rank", 65), ("fighter", "Fighter", 220), ("division", "Division", 130), ("record", "W-L-D", 90), ("ovr", "OVR", 60), ("score", "Ranking", 85)):
            rankings.heading(column, text=label)
            rankings.column(column, width=width, anchor="center")
        rankings.column("fighter", anchor="w")
        self.make_tree_sortable(rankings)
        hub_ranking_rows = {}
        ranking_value = (lambda fighter: self.combat_sport_display_rating(fighter, data["sport"])) if data.get("combat_sport") else self.rank_value
        for rank, fighter in enumerate(sorted(data["roster"], key=ranking_value, reverse=True), 1):
            row_id = self.fighter_tree_row_id("company-rank", fighter, rank)
            hub_ranking_rows[row_id] = fighter
            is_champion = fighter.name in set(data["belts"].values()) if data.get("combat_sport") else fighter.champion
            stats_visible = self.fighter_profile_stats_visible(fighter, data["name"])
            rankings.insert("", "end", iid=row_id, values=("C" if is_champion else rank, self.fighter_display_name(fighter), fighter.weight, fighter.record, fighter.overall if stats_visible else "Scout", round(ranking_value(fighter), 1) if stats_visible else "Scout"))
        rankings.pack(fill="both", expand=True, padx=8, pady=8)
        rankings.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(hub_ranking_rows.get(rankings.selection()[0])) if rankings.selection() else None)

        belts = tk.Text(tabs["Belts"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        belts.pack(fill="both", expand=True, padx=8, pady=8)
        if data.get("combat_sport"):
            for key, champion in sorted(data["belts"].items()):
                belts.insert("end", f"{self.combat_sport_division_label(key):<28} {champion or 'Vacant'}\n")
        else:
            for gender in ("Male", "Female"):
                belts.insert("end", f"{gender.upper()} TITLES\n")
                for weight in WEIGHTS:
                    key = self.belt_key(gender, weight)
                    champion = next((fighter.name for fighter in data["roster"] if fighter.gender == gender and fighter.weight == weight and fighter.champion), data["belts"].get(key, "Vacant"))
                    interim = next((fighter.name for fighter in data["roster"] if fighter.gender == gender and fighter.weight == weight and getattr(fighter, "interim_champion", False)), data["interim_belts"].get(key, ""))
                    belts.insert("end", f"{weight:<16} {champion or 'Vacant'}" + (f"  | Interim: {interim}" if interim else "") + "\n")
                belts.insert("end", "\n")
        special_belts = self.normalize_special_belts(data.get("special_belts", {})) if not data.get("combat_sport") else {}
        if special_belts:
            belts.insert("end", "SPECIAL TITLES\n")
            for belt in special_belts.values():
                belts.insert("end", f"{belt['name']:<20} {belt.get('holder') or 'Vacant'} | Defenses: {belt.get('defenses', 0)}\n")
        belts.config(state="disabled")

        event_list = tk.Listbox(tabs["Events"], font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        event_list.pack(fill="both", expand=True, padx=8, pady=8)
        events = data["scheduled_events"]
        for event in events:
            event_list.insert("end", f"{event.get('name', data['name'])} — {self.event_date_label(event) if event.get('month') else 'Upcoming'} — {event.get('venue', event.get('region', data['region']))}")
        if not events:
            event_list.insert("end", "No confirmed upcoming events are currently stored.")

        result_list = tk.Listbox(tabs["Results"], font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        result_list.pack(fill="both", expand=True, padx=8, pady=8)
        history = data["show_history"]
        for item in history[:30]:
            result_list.insert("end", str(item))
        if not history:
            result_list.insert("end", "No completed event history is currently stored.")

        finance = tk.Text(tabs["Finance"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        finance.pack(fill="both", expand=True, padx=8, pady=8)
        finance_data = data["finance"]
        finance.insert("end", f"Cash reserve: ${data['cash']:,}\n\n")
        if finance_data:
            media = finance_data.get("media_rights", {})
            finance.insert("end", f"Monthly office: ${finance_data.get('monthly_office', 0):,}\nMarketing per event: ${finance_data.get('marketing_budget', 0):,}\nMedia: {media.get('name', 'No rights package')} (${media.get('fee', 0):,}/event)\n")
        else:
            finance.insert("end", "Detailed financial data is not available for this company.")
        finance.config(state="disabled")

        staff = tk.Text(tabs["Staff"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        staff.pack(fill="both", expand=True, padx=8, pady=8)
        if data["staff"]:
            for member in data["staff"]:
                staff.insert("end", f"{member.get('name', 'Staff')} — {member.get('role', 'Operations')} | skill {member.get('skill', 0)} | ${member.get('salary', 0):,}/month\n")
        else:
            staff.insert("end", "Detailed staff data is not available for this company.")
        staff.config(state="disabled")

        controls = ttk.Frame(window, style="Inset.TFrame")
        controls.pack(fill="x", padx=8, pady=(0, 8))
        if data.get("combat_sport"):
            ttk.Button(controls, text="Circuit Records & History", style="Accent.TButton", command=lambda: self.open_combat_sport_history_window(data["sport"], data["player"])).pack(side="left", padx=4, pady=4)
            if data["player"]:
                ttk.Button(controls, text="Manage Child Promotion", command=lambda: self.open_player_combat_division_window(data["sport"])).pack(side="left", padx=4, pady=4)
        else:
            ttk.Button(controls, text="Read Latest Card", command=self.view_selected_company_card).pack(side="left", padx=4, pady=4)
            ttk.Button(controls, text="Watch Latest Card", command=self.watch_selected_company_card).pack(side="left", padx=4, pady=4)
        if not data["player"] and not data.get("combat_sport"):
            ttk.Button(controls, text="Take Control", command=self.take_control_selected_company).pack(side="left", padx=8, pady=4)
        elif data["player"] and not data.get("combat_sport"):
            ttk.Button(controls, text="Return to Spectator", command=self.return_to_spectator_mode).pack(side="left", padx=8, pady=4)
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=4, pady=4)
        if focus in tabs:
            notebook.select(tabs[focus])

    def company_power_components(self, roster, reputation, stability, cash, champion_count=None):
        """Break the company power score into labelled contributions.

        Returned as an ordered list of (label, points) so the rankings screen can
        show players *why* a promotion sits where it does — and how to climb.
        """
        active = [f for f in roster if not f.retired]
        top = sorted(active, key=lambda fighter: (fighter.overall, fighter.elo_rating), reverse=True)[:12]
        top_average = sum(fighter.overall for fighter in top) / max(1, len(top))
        champions = sum(1 for fighter in active if fighter.champion) if champion_count is None else int(champion_count)
        star_average = sum(sorted(((fighter.popularity + fighter.star_quality) / 2 for fighter in active), reverse=True)[:8]) / max(1, min(8, len(active)))
        cash_score = min(30, (max(0, cash) / 5_000_000) ** 0.5 * 10) if cash >= 0 else max(-20, cash / 250_000)
        roster_depth = min(30, len(active) / 8)
        return [
            ("Reputation", reputation * 0.75),
            ("Stability", stability * 0.45),
            ("Roster strength", max(0, (top_average - 50) * 1.2)),
            ("Star power", star_average * 0.45),
            ("Champions", min(12, champions) * 3),
            ("Cash", cash_score),
            ("Roster depth", roster_depth),
        ]

    def company_power_score(self, name, roster, reputation, stability, cash):
        return round(sum(value for _label, value in self.company_power_components(roster, reputation, stability, cash)))

    def company_tier(self, score):
        """Bucket a power score into an industry tier plus its accent colour.

        Thresholds are calibrated to the bounded component scale: elite global
        groups approach 300, national operators sit near 190-279, regional groups
        begin at 100, and startups or failing local shows fall below that.
        """
        for threshold, label, color in (
            (280, "Global", "#c9a13a"),
            (190, "National", "#3f7bd6"),
            (100, "Regional", "#3f9d5a"),
            (0, "Local", "#8a8f97"),
        ):
            if score >= threshold:
                return label, color
        return "Local", "#8a8f97"

    def refresh_regions(self):
        current = self.region_list.curselection()
        self.region_list.delete(0, "end")
        for region in self.regions:
            self.region_list.insert("end", region)
        if current:
            self.region_list.selection_set(min(current[0], self.region_list.size() - 1))
        elif self.region_list.size():
            self.region_list.selection_set(0)
        self.refresh_region_profile()

    def refresh_region_profile(self):
        if not hasattr(self, "region_list") or not self.region_list.curselection():
            return
        region = self.region_list.get(self.region_list.curselection()[0])
        data = self.regions[region]
        local_promos = [p.name for p in self.promotions if p.region == region]
        local_events = [e["name"] for e in self.scheduled_events if self.venue_region(e["venue"]) == region]
        local_gyms = [g for g in getattr(self, "gyms", []) if g.region == region]
        gym_lines = [
            f"> {g.name} ({g.city}) Q{g.quality} Rep{g.reputation} - {', '.join(g.specialties)} - {g.member_count}/{g.capacity} fighters"
            for g in sorted(local_gyms, key=lambda gym: (gym.reputation, gym.quality), reverse=True)[:8]
        ]
        text = (
            f"{region}\n\n"
            f"{region} contains {len(data['areas'])} tracked regions: {', '.join(data['areas'])}.\n\n"
            f"The economy is currently {data['economy']}. MMA is {data['legality']} here. "
            f"Drug testing accuracy is estimated at {data['drug_accuracy']}%. Regional MMA love is {data.get('mma_love', 50)}%.\n\n"
            f"There are {len(data['teams'])} notable fight teams based in this region. The top teams are {', '.join(data['teams'])}.\n\n"
            f"Known gyms:\n{chr(10).join(gym_lines) if gym_lines else 'No tracked gyms yet.'}\n\n"
            f"Major companies based here: {', '.join(local_promos) if local_promos else 'None'}.\n"
            f"Scheduled {self.player_company_name} shows here: {', '.join(local_events) if local_events else 'None'}.\n"
            f"Last major show: {data['last_major_show']}."
        )
        self.region_profile.config(state="normal")
        self.region_profile.delete("1.0", "end")
        self.region_profile.insert("end", text)
        self.region_profile.config(state="disabled")

    def view_selected_company_card(self):
        company, sport = self.company_selected_identity()
        if not company:
            return
        if sport != "MMA":
            data = self.selected_company_data()
            self.open_combat_sport_history_window(sport, bool(data and data.get("player")))
            return
        if company == self.player_company_name:
            record = next((item for item in self.result_records if item.get("company") == company), None)
            if not record:
                messagebox.showinfo("No card", "This company has not completed a saved card yet.")
                return
            package = {"log": record.get("log", []), "fight_logs": record.get("fight_logs", [])}
            self.open_event_replay_window(f"{company}: {record.get('event', 'Last Card')}", package)
            return
        package = next((item for item in self.ai_event_archive if item.get("company") == company), None)
        if not package:
            messagebox.showinfo("No card", "That promotion has not run an archived AI card yet.")
            return
        self.open_event_replay_window(f"{company}: {package.get('event_name', 'Last Card')}", package)

    def watch_selected_company_card(self):
        company, sport = self.company_selected_identity()
        if not company:
            return
        if sport != "MMA":
            data = self.selected_company_data()
            if data and data.get("player"):
                self.open_player_combat_division_window(sport)
            else:
                self.open_combat_sport_history_window(sport, False)
            return
        if company == self.player_company_name:
            package = next((item for item in getattr(self, "player_event_archive", []) if item.get("company") == company), None)
            if not package:
                record = next((item for item in self.result_records if item.get("company") == company), None)
                package = {"event_name": record.get("event", "Last Card"), "log": record.get("log", []), "fight_logs": record.get("fight_logs", [])} if record else None
            if not package:
                messagebox.showinfo("No card", "This company has not completed a saved card yet.")
                return
        else:
            package = next((item for item in self.ai_event_archive if item.get("company") == company), None)
            if not package:
                messagebox.showinfo("No card", "That promotion has not run an archived card yet.")
                return
        self.open_live_fight_window({"name": package.get("event_name", "Archived Event")}, package, apply_results=False)

    def venue_region(self, venue):
        return {
            "Local Gym": "USA",
            "Regional Arena": "USA",
            "Casino Ballroom": "USA",
            "National Sports Hall": "UK",
            "National Stadium": "USA",
            "Mega Stadium": "USA",
            "Historic Amphitheatre": "Europe",
            "Ceremonial Capital Grounds": "USA",
            "White House South Lawn": "USA",
        }.get(venue, "USA")

    def refresh_results(self):
        if not hasattr(self, "results_tree"):
            return
        query = self.result_search.get().lower() if hasattr(self, "result_search") else ""
        records = getattr(self, "result_index", []) or self.result_records or [
            {"date": "", "company": self.player_company_name, "event": item.split(":", 1)[0], "summary": item, "fights": "", "gate": "", "profit": "", "log": [item]}
            for item in self.result_history
        ]
        companies = sorted({str(record.get("company", "")).strip() for record in records if str(record.get("company", "")).strip()})
        companies.extend(name for name in [self.player_company_name] + [promo.name for promo in self.promotions] if name and name not in companies)
        companies = ["All"] + companies
        if hasattr(self, "result_company_combo"):
            self.result_company_combo.configure(values=companies)
        company_filter = self.result_company_filter.get() if hasattr(self, "result_company_filter") else "All"
        if company_filter not in companies:
            company_filter = "All"
            if hasattr(self, "result_company_filter"):
                self.result_company_filter.set(company_filter)
        self.results_tree.delete(*self.results_tree.get_children())
        self._visible_result_records = {}
        for index, record in enumerate(records):
            haystack = " ".join(str(record.get(key, "")) for key in ("date", "company", "event", "summary")).lower()
            haystack += " " + self.result_headline(record).lower()
            if query and query not in haystack:
                continue
            if company_filter != "All" and record.get("company", "") != company_filter:
                continue
            iid = f"result-{index}"
            self._visible_result_records[iid] = record
            self.results_tree.insert("", "end", iid=iid, values=(self.format_game_date_text(record.get("date", "")), record.get("company", ""), record.get("event", ""), record.get("headline") or self.result_headline(record), record.get("fights", ""), record.get("gate", ""), record.get("profit", "")))
        self.retired_tree.delete(*self.retired_tree.get_children())
        retired_query = self.retired_search.get().strip().lower() if hasattr(self, "retired_search") else ""
        retired_gender = self.retired_gender_filter.get() if hasattr(self, "retired_gender_filter") else "All"
        retired_weight = self.retired_weight_filter.get() if hasattr(self, "retired_weight_filter") else "All"
        retired_legacy = self.retired_legacy_filter.get() if hasattr(self, "retired_legacy_filter") else "All"
        for index, fighter in enumerate(self.retired_fighters):
            if retired_gender != "All" and fighter.gender != retired_gender:
                continue
            if retired_weight != "All" and fighter.weight != retired_weight:
                continue
            bouts = fighter.record_w + fighter.record_l + fighter.record_d
            former_champion = bool(getattr(fighter, "champion", False) or getattr(fighter, "interim_champion", False)
                                  or getattr(fighter, "title_wins", 0) or getattr(fighter, "title_defenses", 0))
            if retired_legacy == "Former Champions" and not former_champion:
                continue
            if retired_legacy == "20+ Bouts" and bouts < 20:
                continue
            if retired_legacy == "30+ Bouts" and bouts < 30:
                continue
            haystack = " ".join((fighter.name, fighter.gender, fighter.weight, fighter.nationality,
                                  fighter.region, fighter.style, fighter.trait, fighter.record)).lower()
            if retired_query and retired_query not in haystack:
                continue
            peaks = [int(value) for value in (fighter.annual_overalls or {}).values() if str(value).lstrip("-").isdigit()]
            peak_overall = max(peaks + [fighter.overall])
            self.retired_tree.insert("", "end", iid=str(index), values=(fighter.name, fighter.gender[0], fighter.weight, fighter.record, fighter.age, peak_overall, fighter.motivation))
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        if records:
            self.results_text.insert("end", self.result_card_text(records[0]))
        else:
            self.results_text.insert("end", "No completed events yet.")
        self.results_text.config(state="disabled")

    def open_legacy_ledger(self):
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - Legacy Ledger")
        window.geometry("920x620")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="LEGACY LEDGER", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=8)
        fighters_panel, fighters_inner = self.section(body, "ALL-TIME FIGHTER LEGACY")
        fighters_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        legacy_controls = ttk.Frame(fighters_inner, style="Inset.TFrame")
        legacy_controls.pack(fill="x", pady=(0, 4))
        ttk.Label(legacy_controls, text="Sport", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        legacy_sport = tk.StringVar(value="MMA")
        all_legacy_fighters = [fighter for _company, fighter in self.all_database_fighters_with_companies()]
        legacy_sports = ["All Sports"] + sorted({self.fighter_career_sport(fighter) for fighter in all_legacy_fighters})
        ttk.Combobox(legacy_controls, textvariable=legacy_sport, values=legacy_sports, state="readonly", width=18).pack(side="left")
        text = tk.Text(fighters_inner, wrap="none", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        text.pack(fill="both", expand=True)

        def refresh_legacy_fighters(*_args):
            selected_sport = legacy_sport.get()
            unique = {self.fighter_identity_key(fighter): fighter for fighter in all_legacy_fighters}
            rows = [fighter for fighter in unique.values() if selected_sport == "All Sports" or self.fighter_career_sport(fighter) == selected_sport]
            rows.sort(key=lambda fighter: self.compute_legacy_score(fighter), reverse=True)
            text.config(state="normal")
            text.delete("1.0", "end")
            text.insert("end", "Fighter                         Legacy   Record    Titles/Def    Awards\n")
            text.insert("end", "-" * 72 + "\n")
            for fighter in rows[:60]:
                score = self.compute_legacy_score(fighter)
                text.insert("end", f"{fighter.name[:30]:30} {score:>6}   {fighter.record:9} {fighter.title_wins:>2}/{fighter.title_defenses:<3} {fighter.award_count:>3}\n")
            text.config(state="disabled")

        legacy_sport.trace_add("write", refresh_legacy_fighters)
        refresh_legacy_fighters()
        companies_panel, companies_inner = self.section(body, "COMPANY ERAS")
        companies_panel.pack(side="left", fill="both", expand=True)
        company_text = tk.Text(companies_inner, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        company_text.pack(fill="both", expand=True)
        for promo in sorted(self.promotions, key=lambda item: getattr(item, "legacy_score", item.reputation_score), reverse=True):
            executive = getattr(promo, "executive", {}) or {}
            company_text.insert("end", f"{promo.name}\n")
            company_text.insert("end", f"Legacy {getattr(promo, 'legacy_score', 0)} | Executive: {executive.get('name', 'Unknown')} ({executive.get('archetype', 'Operator')})\n")
            for era in (getattr(promo, "era_history", []) or [])[:3]:
                company_text.insert("end", f"  {era.get('year', '')}: {era.get('note', '')}\n")
            company_text.insert("end", "\n")
        company_text.config(state="disabled")

    def result_headline(self, record):
        """One-line 'A vs B' for the main event, so the list shows who fought."""
        for fight_log in record.get("fight_logs", []) or []:
            if "MAIN" in str(fight_log.get("label", "")).upper():
                if fight_log.get("a"):
                    return f"{fight_log['a']} vs {fight_log['b']}"
                return str(fight_log.get("heading", ""))[:60]
        fight_logs = record.get("fight_logs", []) or []
        if fight_logs:
            last = fight_logs[-1]
            if last.get("a"):
                return f"{last['a']} vs {last['b']}"
            return str(last.get("heading", ""))[:60]
        return ""

    def result_bout_lines(self, record):
        """Readable one-line result for every bout on the card."""
        lines = []
        for fight_log in record.get("fight_logs", []) or []:
            label = str(fight_log.get("label", "")).strip()
            prefix = f"[{label}] " if label and label != "BOUT" else ""
            if fight_log.get("a") and fight_log.get("result"):
                weight = f" ({fight_log.get('weight', '')})" if fight_log.get("weight") else ""
                lines.append(f"{prefix}{fight_log['a']} vs {fight_log['b']}{weight}  ->  {fight_log['result']}")
            else:
                heading = str(fight_log.get("heading", "")).strip()
                result = ""
                for raw in fight_log.get("lines", []):
                    text = str(raw)
                    if text.startswith("Result:"):
                        result = text.replace("Result: ", "").split(" | ")[0].strip()
                    elif " def. " in text and not result:
                        result = text.strip()
                lines.append(f"{heading}" + (f"  ->  {result}" if result else ""))
        return lines

    def result_record_with_compact_bouts(self, record):
        """Turn the permanent results index back into a browseable card view."""
        if record.get("fight_logs"):
            return record
        compact = record.get("bout_results", []) or []
        if not compact:
            return record
        display = dict(record)
        display["fight_logs"] = [
            {
                **bout,
                "heading": f"{bout.get('a', '')} vs {bout.get('b', '')}".strip(" vs"),
                "lines": [bout.get("result", "Result unavailable")] + ([f"Official scorecards: {bout['scorecards']}"] if bout.get("scorecards") else []),
            }
            for bout in compact
        ]
        return display

    def detailed_result_record(self, record):
        """Resolve a card's replay from the global shelf or its owner archive."""
        key = record.get("detail_key", self.result_archive_key(record))
        detailed = next((item for item in self.result_records if self.result_archive_key(item) == key), None)
        if detailed:
            return detailed
        for package in list(getattr(self, "player_event_archive", [])) + list(getattr(self, "ai_event_archive", [])):
            package_key = "|".join(str(package.get(field, "")).strip() for field in ("date", "company"))
            package_key += "|" + str(package.get("event_name", "")).strip()
            if package_key != key:
                continue
            detailed = dict(package)
            detailed["event"] = package.get("event_name", "Archived Event")
            detailed["fights"] = package.get("fight_count", "")
            detailed["gate"] = record.get("gate", "")
            detailed["profit"] = record.get("profit", "")
            return detailed
        return None

    def result_card_text(self, record):
        record = self.result_record_with_compact_bouts(record)
        bout_lines = self.result_bout_lines(record)
        header = self.format_game_date_text(record.get("summary", ""))
        parts = [header, "", "CARD RESULTS", "-" * 60]
        parts.extend([self.format_game_date_text(line) for line in bout_lines] if bout_lines else ["(No per-fight breakdown stored for this event.)"])
        return "\n".join(parts)

    def open_selected_result(self):
        selected = self.results_tree.selection()
        if not selected:
            return
        record = getattr(self, "_visible_result_records", {}).get(selected[0])
        if not record:
            return
        detailed = self.detailed_result_record(record)
        display_record = detailed or self.result_record_with_compact_bouts(record)
        self.open_result_card_window(display_record)
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        card = self.result_card_text(display_record)
        full_log = self.format_game_date_text("\n".join(display_record.get("log", [display_record.get("summary", "")])))
        self.results_text.insert("end", card + "\n\n\n" + "=" * 60 + "\nFULL PLAY-BY-PLAY\n" + "=" * 60 + "\n" + full_log)
        self.results_text.config(state="disabled")

    def watch_selected_result(self):
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showinfo("Results Database", "Select an event to watch first.")
            return
        record = getattr(self, "_visible_result_records", {}).get(selected[0])
        if not record:
            return
        if not record.get("has_replay", bool(record.get("log") or record.get("fight_logs"))):
            messagebox.showinfo("Replay Unavailable", "This historic card has a permanent result summary, but its full watchable replay is no longer retained.")
            return
        detailed = self.detailed_result_record(record)
        if not detailed:
            messagebox.showinfo("Replay Unavailable", "This card's replay detail has aged out of the archive.")
            return
        self.watch_result_card(detailed)

    def watch_result_card(self, record):
        """Replay a completed card without applying its already-recorded result twice."""
        logs = list(record.get("fight_logs", []) or [])
        event_name = record.get("event") or record.get("event_name") or "Archived Event"
        package = {
            "event_name": event_name,
            "log": list(record.get("log", []) or [record.get("summary", "No saved play-by-play.")]),
        }
        if logs:
            package["fight_logs"] = logs
        else:
            package["fight_logs"] = [{"heading": "Event Report", "lines": package["log"]}]
        if record.get("tournament_brackets"):
            package["tournament_brackets"] = record["tournament_brackets"]
        self.open_live_fight_window({"name": event_name}, package, apply_results=False)

    def result_fighter(self, name, fighter_id="", sport="", division=""):
        """Resolve a result-card fighter by permanent ID, with legacy metadata fallback."""
        rows = self.fighter_instances_with_companies(include_retired=True)
        if fighter_id:
            return next((fighter for _company, fighter in rows if fighter.fighter_id == fighter_id), None)
        candidates = [fighter for _company, fighter in rows if fighter.name == name]
        if sport:
            matches = [fighter for fighter in candidates if str(getattr(fighter, "primary_discipline", "") or "") == sport]
            if matches:
                candidates = matches
        if division:
            matches = [fighter for fighter in candidates if str(getattr(fighter, "sport_weight_class", "") or fighter.weight) == division]
            if matches:
                candidates = matches
        return max(candidates, key=lambda fighter: fighter.record_w + fighter.record_l + fighter.record_d, default=None)

    def open_result_card_window(self, record):
        title = f"{record.get('company', 'MMA')} - {record.get('event', 'Event Results')}"
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("980x640")
        window.minsize(820, 520)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=title.upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        ttk.Label(header, text=record.get("date", ""), style="ScreenTitle.TLabel").pack(side="right", padx=10, pady=5)
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        bouts = tk.Listbox(body, width=44, font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"],
                           selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        bouts.pack(side="left", fill="y", padx=(0, 8))
        logs = record.get("fight_logs", []) or []
        for number, fight_log in enumerate(logs, 1):
            bouts.insert("end", f"{number}. {fight_log.get('heading', 'Bout')[:52]}")
        detail = tk.Text(body, wrap="word", font=("Courier New", 10), bg=self.colors["panel_dark"], fg=self.colors["text"],
                         insertbackground=self.colors["text"], padx=12, pady=12)
        detail.pack(side="left", fill="both", expand=True)
        controls = ttk.Frame(window, style="Inset.TFrame")
        controls.pack(fill="x", padx=8, pady=(0, 8))
        fighter_a_button = ttk.Button(controls, text="View Fighter A", state="disabled")
        fighter_b_button = ttk.Button(controls, text="View Fighter B", state="disabled")
        negotiate_a_button = ttk.Button(controls, text="Negotiate Fighter A", state="disabled")
        negotiate_b_button = ttk.Button(controls, text="Negotiate Fighter B", state="disabled")
        fighter_a_button.pack(side="left", padx=5, pady=5)
        fighter_b_button.pack(side="left", padx=5, pady=5)
        negotiate_a_button.pack(side="left", padx=5, pady=5)
        negotiate_b_button.pack(side="left", padx=5, pady=5)
        replay_available = record.get("replay_available", bool(record.get("log") and record.get("fight_logs")))
        ttk.Button(
            controls, text="Watch Card" if replay_available else "Replay Not Retained",
            style="Accent.TButton", command=lambda: self.watch_result_card(record),
            state="normal" if replay_available else "disabled",
        ).pack(side="right", padx=5, pady=5)
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=5, pady=5)
        selected_log = {"value": None}

        def open_profile(side):
            fight_log = selected_log["value"] or {}
            fighter = self.result_fighter(fight_log.get(side, ""), fight_log.get(f"{side}_id", ""), fight_log.get("sport", ""), fight_log.get("weight", ""))
            if fighter:
                self.open_fighter_profile_window(fighter)

        def negotiate_fighter(side):
            fight_log = selected_log["value"] or {}
            fighter = self.result_fighter(fight_log.get(side, ""), fight_log.get(f"{side}_id", ""), fight_log.get("sport", ""), fight_log.get("weight", ""))
            if fighter and fighter in self.free_agents:
                self.open_contract_negotiation(fighter, existing=False)

        fighter_a_button.configure(command=lambda: open_profile("a"))
        fighter_b_button.configure(command=lambda: open_profile("b"))
        negotiate_a_button.configure(command=lambda: negotiate_fighter("a"))
        negotiate_b_button.configure(command=lambda: negotiate_fighter("b"))

        def show_bout(_event=None):
            selected = bouts.curselection()
            if not selected or selected[0] >= len(logs):
                return
            fight_log = logs[selected[0]]
            selected_log["value"] = fight_log
            detail.config(state="normal")
            detail.delete("1.0", "end")
            detail.insert("end", "\n".join(fight_log.get("lines", [])))
            detail.config(state="disabled")
            a = self.result_fighter(fight_log.get("a", ""), fight_log.get("a_id", ""), fight_log.get("sport", ""), fight_log.get("weight", ""))
            b = self.result_fighter(fight_log.get("b", ""), fight_log.get("b_id", ""), fight_log.get("sport", ""), fight_log.get("weight", ""))
            fighter_a_button.configure(state="normal" if a else "disabled", text=f"View {fight_log.get('a', 'Fighter A')[:22]}")
            fighter_b_button.configure(state="normal" if b else "disabled", text=f"View {fight_log.get('b', 'Fighter B')[:22]}")
            negotiate_a_button.configure(state="normal" if a in self.free_agents else "disabled",
                                         text=f"Negotiate {a.name[:20]}" if a in self.free_agents else "A Not Available")
            negotiate_b_button.configure(state="normal" if b in self.free_agents else "disabled",
                                         text=f"Negotiate {b.name[:20]}" if b in self.free_agents else "B Not Available")

        bouts.bind("<<ListboxSelect>>", show_bout)
        bouts.bind("<Double-1>", lambda _event: open_profile("a"))
        if logs:
            bouts.selection_set(0)
            show_bout()
        else:
            detail.insert("end", record.get("summary", "No bout logs recorded.") + "\n\nNo bout-by-bout detail was retained for this historic card.")
            detail.config(state="disabled")

    def offer_comeback_deal(self, fighter, profile_window=None):
        """Warn before signing a retired fighter, then let the player choose a full
        comeback (guaranteed fights) or a single farewell retirement bout."""
        if not getattr(fighter, "retired", False):
            return False
        if profile_window and profile_window.winfo_exists():
            profile_window.destroy()

        guaranteed = int(getattr(fighter, "guaranteed_fights", 0) or 0)
        completed = int(getattr(fighter, "contract_fights_completed", 0) or 0)
        has_clause = guaranteed > 0 or getattr(fighter, "comeback_contract", False)
        outstanding_clause = getattr(fighter, "comeback_contract", False) or completed < guaranteed

        window = tk.Toplevel(self.root)
        window.title(f"Bring {fighter.name} Out of Retirement?")
        window.geometry("560x360")
        window.minsize(520, 320)
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        ttk.Label(window, text=f"COMEBACK REVIEW: {fighter.name}", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 4))

        info = tk.Text(window, height=8, wrap="word", bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=8)
        info.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        lines = [
            f"{fighter.name} ({fighter.gender}, {fighter.weight}) — age {fighter.age}, record {fighter.record}.",
            f"Retirement reason: {getattr(fighter, 'retirement_reason', '') or 'Career review.'}",
            "",
        ]
        if has_clause:
            if outstanding_clause:
                lines.append(
                    f"WARNING: {fighter.name} still carries a committed-fight clause "
                    f"({completed}/{guaranteed} guaranteed comeback fights completed). Re-signing them "
                    "for a full comeback adds the new guaranteed fights to that career total — retirement "
                    "stays deferred until every remaining fight is complete."
                )
            else:
                lines.append(
                    f"PREVIOUS COMEBACK COMPLETE: {fighter.name} completed {completed}/{guaranteed} guaranteed fights. "
                    "A new full-comeback contract starts a fresh fight-counted commitment."
                )
            lines.append("")
        lines.append("FULL COMEBACK: negotiate a multi-fight deal with guaranteed fights; they return as an active roster fighter.")
        lines.append("ONE FINAL RETIREMENT BOUT: sign a single farewell fight; they retire immediately after it.")
        info.insert("end", "\n".join(lines))
        if has_clause:
            info.tag_add("warn", "4.0", "4.end")
            info.tag_configure("warn", foreground="#c0392b" if outstanding_clause else self.colors["gold"], font=("Tahoma", 9, "bold"))
        info.config(state="disabled")

        buttons = ttk.Frame(window, style="Inset.TFrame")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        def choose(farewell):
            window.destroy()
            self.open_contract_negotiation(fighter, existing=False, comeback=True, farewell=farewell)

        ttk.Button(buttons, text="Full Comeback", style="Accent.TButton", command=lambda: choose(False)).pack(side="left", padx=4)
        ttk.Button(buttons, text="One Final Retirement Bout", command=lambda: choose(True)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="right", padx=4)
        return True

    def prompt_comeback_completion(self, fighter):
        """Offer the next decision once a player-managed comeback is fulfilled."""
        if (fighter not in self.roster or getattr(fighter, "retired", False)
                or not getattr(fighter, "retirement_pending", False)
                or getattr(fighter, "comeback_completion_prompted", False)):
            return False
        fighter.comeback_completion_prompted = True
        window = tk.Toplevel(self.root)
        window.title("Comeback Commitment Complete")
        window.geometry("560x250")
        window.minsize(500, 230)
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        ttk.Label(window, text="COMEBACK COMMITMENT COMPLETE", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 5))
        ttk.Label(
            window,
            text=(f"{fighter.name} has completed their agreed comeback fights.\n\n"
                  "Negotiate another fight-counted comeback deal, or leave them in final retirement-bout mode. "
                  "The renewal option remains on their profile if you decide later."),
            style="Panel.TLabel", justify="left", wraplength=510,
        ).pack(fill="x", padx=14, pady=(0, 12))
        buttons = ttk.Frame(window, style="Inset.TFrame")
        buttons.pack(fill="x", padx=14, pady=(0, 14))

        def renew():
            window.destroy()
            self.open_contract_negotiation(fighter, existing=True, comeback=True)

        ttk.Button(buttons, text="Renew Comeback Deal", style="Accent.TButton", command=renew).pack(side="left", padx=4)
        ttk.Button(buttons, text="Final Retirement Bout", command=window.destroy).pack(side="left", padx=4)
        ttk.Button(buttons, text="Decide Later", command=window.destroy).pack(side="right", padx=4)
        return True

    def unretire_selected_fighter(self):
        selected = self.retired_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        if 0 <= index < len(self.retired_fighters):
            self.offer_comeback_deal(self.retired_fighters[index])

    def refresh_company_editor(self):
        self.company_belts_tree.delete(*self.company_belts_tree.get_children())
        self.belts = self.normalize_belts(self.belts)
        self.interim_belts = self.normalize_belts(getattr(self, "interim_belts", {}))
        self.belt_history = self.normalize_belt_history(getattr(self, "belt_history", {}))
        for gender in ("Male", "Female"):
            for weight in WEIGHTS:
                key = self.belt_key(gender, weight)
                champion = next((f.name for f in self.roster if f.weight == weight and f.gender == gender and f.champion), self.belts.get(key, "Vacant"))
                interim = next((f.name for f in self.roster if f.weight == weight and f.gender == gender and getattr(f, "interim_champion", False)), self.interim_belts.get(key, ""))
                active = "Closed" if key in set(getattr(self, "closed_divisions", set())) else "Open"
                self.company_belts_tree.insert("", "end", iid=key, values=(gender, weight, champion or "Vacant", interim or "-", active))
        self.special_belts = self.normalize_special_belts(getattr(self, "special_belts", {}))
        if hasattr(self, "special_belts_tree"):
            self.special_belts_tree.delete(*self.special_belts_tree.get_children())
            for name, belt in sorted(self.special_belts.items()):
                self.special_belts_tree.insert("", "end", iid=name, values=(name, belt.get("holder") or "Vacant", belt.get("defenses", 0)))
        self.refresh_special_belt_choices()
        self.refresh_belt_history_view()
        self.refresh_company_division_toggle_button()
        self.rules_text.config(state="normal")
        self.rules_text.delete("1.0", "end")
        self.ensure_rule_defaults()
        broadcasters = "\n".join(
            f"- {b['name']} ({b['type']}): reach {b['reach']}, production fee ${b['fee']:,}"
            for b in sorted(self.broadcasters, key=lambda item: (item.get("fee", 0), item.get("name", "")))
        ) or "- No production providers configured"
        mixed = "Allowed" if self.rules.get("allow_mixed_gender", False) else "Not allowed"
        closed = set(getattr(self, "closed_divisions", set()))
        open_divisions = (len(WEIGHTS) * 2) - len(closed)
        vacant_titles = sum(1 for holder in self.normalize_belts(getattr(self, "belts", {})).values() if not holder)
        interim_titles = sum(1 for holder in self.normalize_belts(getattr(self, "interim_belts", {})).values() if holder)
        managed = len(set(getattr(self, "player_managed_divisions", set()) or []))
        policy_lines = [
            "FIGHT FORMAT",
            f"- Regular bouts: {self.rules['rounds']} rounds x {self.rules['round_length']} minutes",
            f"- Title/main-event bouts: {self.rules['title_rounds']} rounds x {self.rules['round_length']} minutes",
            f"- Judging randomness: {self.rules['judging_randomness']} (lower is cleaner scoring, higher creates more volatility)",
            "",
            "REGULATORY POLICY",
            f"- Drug testing: {self.rules['drug_testing']}",
            f"- Mixed-gender fights: {mixed}",
            f"- Scouting mode: {'On' if self.rules.get('scouting_mode', False) else 'Off'}",
            f"- Autosave: {'On' if self.rules.get('autosave_enabled', True) else 'Off'} every {self.rules.get('autosave_interval_months', 2)} month(s)",
            "",
            "TITLE GOVERNANCE",
            f"- Open divisions: {open_divisions} / {len(WEIGHTS) * 2}",
            f"- Player-managed closed divisions: {managed}",
            f"- Vacant primary titles: {vacant_titles}",
            f"- Active interim champions: {interim_titles}",
            "- Vacant player championships must be decided by title fights; AI/regional vacancies stay vacant after a lineage exists.",
            "",
            "WORLD / MARKET",
            f"- Active fighter target: {self.rules['active_fighter_target']}",
            f"- AI offer-market target: {self.rules.get('ai_offer_market_target', 100)} free agents",
            f"- Result replay retention: {self.rules.get('global_result_replay_limit', GLOBAL_RESULT_REPLAY_LIMIT)} detailed cards",
            "",
            "EVENT PRODUCTION PROVIDERS",
            broadcasters,
        ]
        self.rules_text.insert("end", "\n".join(policy_lines))
        self.rules_text.config(state="disabled")

    def create_special_belt(self):
        name = " ".join(self.special_belt_name_var.get().strip().split()) if hasattr(self, "special_belt_name_var") else ""
        if not name:
            self.special_belt_status_var.set("Enter a belt name first.")
            return
        if len(name) > 40:
            self.special_belt_status_var.set("Belt names must be 40 characters or fewer.")
            return
        self.special_belts = self.normalize_special_belts(getattr(self, "special_belts", {}))
        if any(existing.casefold() == name.casefold() for existing in self.special_belts):
            self.special_belt_status_var.set(f"{name} already exists.")
            return
        self.special_belts[name] = {"name": name, "holder": "", "defenses": 0, "history": []}
        self.special_belt_name_var.set("")
        self.special_belt_status_var.set(f"Created {name}. It is now available in Matchmaking.")
        self.refresh_company_editor()

    def selected_special_belt_editor_name(self):
        selected = self.special_belts_tree.selection() if hasattr(self, "special_belts_tree") else ()
        return selected[0] if selected else ""

    def vacate_selected_special_belt(self):
        name = self.selected_special_belt_editor_name()
        belt = getattr(self, "special_belts", {}).get(name)
        if not belt:
            self.special_belt_status_var.set("Select a special belt first.")
            return
        holder = belt.get("holder", "")
        if holder:
            fighter = next((item for item in self.roster if item.name == holder), None)
            if fighter:
                fighter.special_titles = [title for title in (fighter.special_titles or []) if title != name]
            belt["history"].insert(0, {"date": f"Month {self.month} Week {self.week}", "action": "Vacated", "fighter": holder, "previous": holder, "note": "Player vacated the championship."})
        belt["holder"] = ""
        self.special_belt_status_var.set(f"{name} is now vacant.")
        self.refresh_company_editor()

    def delete_selected_special_belt(self):
        name = self.selected_special_belt_editor_name()
        if not name or name not in getattr(self, "special_belts", {}):
            self.special_belt_status_var.set("Select a special belt first.")
            return
        holder = self.special_belts[name].get("holder", "")
        if holder:
            fighter = next((item for item in self.roster if item.name == holder), None)
            if fighter:
                fighter.special_titles = [title for title in (fighter.special_titles or []) if title != name]
        del self.special_belts[name]
        for event in [{"fights": self.booked}] + list(self.scheduled_events):
            for fight in event.get("fights", []):
                if fight.get("special_belt") == name:
                    fight["special_belt"] = ""
                    fight["title"] = bool(fight.get("divisional_title", False))
                    named = [self.get_fighter(fighter_name) for fighter_name in fight.get("fighters", []) if fighter_name != "TBA"]
                    fight["interim"] = self.divisional_title_is_interim(named, fight.get("divisional_title", False))
        self.special_belt_status_var.set(f"Deleted {name}; any future booking for it was changed to non-title.")
        self.refresh_company_editor()
        self.refresh_card()

    def refresh_belt_history_view(self):
        if not hasattr(self, "belt_history_text"):
            return
        selected = self.company_belts_tree.selection() if hasattr(self, "company_belts_tree") else []
        key = selected[0] if selected else self.belt_key("Male", WEIGHTS[0])
        entries = self.normalize_belt_history(getattr(self, "belt_history", {})).get(key, [])
        self.belt_history_text.config(state="normal")
        self.belt_history_text.delete("1.0", "end")
        self.belt_history_text.insert("end", f"{key} Belt History\n")
        if entries:
            for entry in entries[:8]:
                fighter = f" - {entry.get('fighter')}" if entry.get("fighter") else ""
                note = f" ({entry.get('note')})" if entry.get("note") else ""
                self.belt_history_text.insert("end", f"{entry.get('date', '')}: {entry.get('action', '')}{fighter}{note}\n")
        else:
            self.belt_history_text.insert("end", "No belt history recorded yet.")
        self.belt_history_text.config(state="disabled")
        self.refresh_company_division_toggle_button()

    def ensure_rule_defaults(self):
        self.rules.setdefault("rounds", 3)
        self.rules.setdefault("title_rounds", 5)
        self.rules.setdefault("round_length", 5)
        self.rules.setdefault("drug_testing", "Standard")
        self.rules.setdefault("judging_randomness", 2)
        self.rules.setdefault("allow_mixed_gender", False)
        self.rules.setdefault("active_fighter_target", 1200)
        self.rules.setdefault("ai_offer_market_target", 100)
        self.rules.setdefault("global_result_replay_limit", GLOBAL_RESULT_REPLAY_LIMIT)
        self.rules.setdefault("live_follow_commentary", True)
        self.rules.setdefault("live_auto_play_card", False)
        self.rules.setdefault("fight_night_audio_enabled", True)
        self.rules.setdefault("fight_night_audio_output", "System default")
        self.rules.setdefault("fight_night_audio_volume", 55)
        self.rules["fight_night_audio_volume"] = max(0, min(100, int(self.rules.get("fight_night_audio_volume", 55))))
        self.rules.setdefault("opening_division_depth_seeded", False)
        # Absent marker means the save predates the academy price rise, so it
        # keeps the costs it was started under.
        self.rules.setdefault("academy_upgrade_pricing_version", 1)
        self.rules.setdefault("autosave_enabled", True)
        self.rules.setdefault("autosave_interval_months", 2)
        # Version 1 shipped very large defaults (12/24/60). A mature world can
        # exceed 13 MB per JSON file, so that policy could quietly consume more
        # than a gigabyte.
        retention_version = int(self.rules.get("save_retention_version", 1))
        if retention_version < 2:
            if (int(self.rules.get("autosave_weekly_keep", 12)), int(self.rules.get("autosave_monthly_keep", 24)), int(self.rules.get("save_backup_keep", 60))) == (12, 24, 60):
                self.rules.update({"autosave_weekly_keep": 8, "autosave_monthly_keep": 6, "save_backup_keep": 12})
        if retention_version < 3:
            # Existing saves adopt the new lower-I/O two-month cadence.
            self.rules["autosave_interval_months"] = 2
        if retention_version < 4:
            # Every category now uses two fixed files that overwrite the oldest
            # slot. This avoids silent save-folder growth across long careers.
            self.rules.update({"autosave_weekly_keep": ROLLING_SAVE_SLOT_COUNT, "autosave_monthly_keep": ROLLING_SAVE_SLOT_COUNT, "save_backup_keep": ROLLING_SAVE_SLOT_COUNT})
        self.rules["save_retention_version"] = 4
        self.rules["autosave_weekly_keep"] = ROLLING_SAVE_SLOT_COUNT
        self.rules["autosave_monthly_keep"] = ROLLING_SAVE_SLOT_COUNT
        self.rules["save_backup_keep"] = ROLLING_SAVE_SLOT_COUNT
        self.rules["autosave_interval_months"] = max(1, min(12, int(self.rules.get("autosave_interval_months", 2))))
        # Migrate worlds created before the population floor was corrected.
        if self.rules["active_fighter_target"] < 800:
            self.rules["active_fighter_target"] = 1200
        self.rules["ai_offer_market_target"] = max(20, min(180, int(self.rules.get("ai_offer_market_target", 100))))
        self.rules["global_result_replay_limit"] = max(0, int(self.rules.get("global_result_replay_limit", GLOBAL_RESULT_REPLAY_LIMIT)))

    def refresh_company_division_toggle_button(self):
        button = getattr(self, "company_division_toggle_button", None)
        if not button:
            return
        selected = self.company_belts_tree.selection() if hasattr(self, "company_belts_tree") else ()
        if not selected:
            button.config(text="Open / Close Selected Division", state="disabled")
            return
        key = selected[0]
        closed = key in set(getattr(self, "closed_divisions", set()))
        button.config(text="Reopen Selected Division" if closed else "Close Selected Division", state="normal")

    def toggle_selected_company_division(self):
        """Use the same gender-specific division state as roster and matchmaking."""
        selected = self.company_belts_tree.selection()
        if not selected:
            messagebox.showinfo("Choose a division", "Select one gender and weight-class row first.")
            return False
        key = selected[0]
        values = self.company_belts_tree.item(key, "values")
        if len(values) < 2:
            return False
        gender, weight = str(values[0]), str(values[1])
        if key in set(getattr(self, "closed_divisions", set())):
            changed = self.reopen_selected_division(gender, weight)
        else:
            changed = self.close_selected_division(gender, weight)
        if changed:
            self.refresh_company_editor()
        return changed

    def toggle_weight_class(self):
        """Compatibility alias for older UI bindings and automation."""
        return self.toggle_selected_company_division()

    def cycle_drug_testing(self):
        values = ["None", "Standard", "Strict", "Olympic"]
        current = values.index(self.rules.get("drug_testing", "Standard"))
        self.rules["drug_testing"] = values[(current + 1) % len(values)]
        self.inbox.append({"subject": "Drug Testing Policy Updated", "body": f"Policy is now {self.rules['drug_testing']}.", "type": "Info", "resolved": False})
        self.refresh_all()

    def toggle_mixed_gender_rule(self):
        self.rules["allow_mixed_gender"] = not self.rules.get("allow_mixed_gender", False)
        status = "allowed" if self.rules["allow_mixed_gender"] else "not allowed"
        self.inbox.append({"subject": "Rules Updated", "body": f"Mixed-gender fights are now {status}.", "type": "Rules", "resolved": False})
        self.refresh_all()

    def adjust_round_length(self, amount):
        self.ensure_rule_defaults()
        self.rules["round_length"] = max(3, min(10, self.rules["round_length"] + amount))
        self.inbox.append({"subject": "Rules Updated", "body": f"Round length is now {self.rules['round_length']} minutes.", "type": "Rules", "resolved": False})
        self.refresh_all()

    def adjust_regular_rounds(self, amount):
        self.ensure_rule_defaults()
        self.rules["rounds"] = max(1, min(5, self.rules["rounds"] + amount))
        self.rules["title_rounds"] = max(self.rules["rounds"], self.rules["title_rounds"])
        self.inbox.append({"subject": "Rules Updated", "body": f"Regular fights are now {self.rules['rounds']} rounds.", "type": "Rules", "resolved": False})
        self.refresh_all()

    def adjust_title_rounds(self, amount):
        self.ensure_rule_defaults()
        minimum = max(1, self.rules["rounds"])
        self.rules["title_rounds"] = max(minimum, min(7, self.rules["title_rounds"] + amount))
        self.inbox.append({"subject": "Rules Updated", "body": f"Title/main event fights are now {self.rules['title_rounds']} rounds.", "type": "Rules", "resolved": False})
        self.refresh_all()

    def adjust_active_fighter_target(self, amount):
        self.ensure_rule_defaults()
        self.rules["active_fighter_target"] = max(800, min(3000, self.rules["active_fighter_target"] + amount))
        self.ensure_world_fighter_target()
        self.inbox.append({"subject": "World Size Updated", "body": f"Active fighter target is now {self.rules['active_fighter_target']}.", "type": "Rules", "resolved": False})
        self.refresh_all()

    def add_broadcaster(self):
        options = [
            {"name": "FightPass Local", "reach": 34, "fee": 22000, "type": "Streaming"},
            {"name": "Combat Cable", "reach": 48, "fee": 42000, "type": "Cable"},
            {"name": "Global Sports Net", "reach": 72, "fee": 95000, "type": "TV"},
        ]
        existing = {item.get("name") for item in self.broadcasters}
        candidate = next((item for item in options if item["name"] not in existing), None)
        if candidate is None:
            messagebox.showinfo("Production Providers", "Every production provider is already available. Media-rights partners are negotiated from the Media Desk.")
            return
        setup_cost = max(10_000, candidate["fee"])
        if self.cash < setup_cost:
            messagebox.showwarning("Production Providers", f"Adding {candidate['name']} requires a ${setup_cost:,} production setup payment.")
            return
        self.cash -= setup_cost
        self.record_finance_transaction(f"Production provider: {candidate['name']}", costs=setup_cost)
        self.broadcasters.append(dict(candidate))
        self.finance.setdefault("ledger", []).insert(0, f"Month {self.month}: Added event production provider {candidate['name']} for ${setup_cost:,}.")
        self.news.insert(0, f"{self.player_company_name} added {candidate['name']} as an event production provider.")
        self.inbox.append({"subject": "Production Provider Added", "body": f"{candidate['name']} is now available for event production. Its ${candidate['fee']:,} fee is an event cost, not media-rights income.", "type": "Business", "resolved": False})
        self.refresh_all()

    def refresh_inbox(self):
        if not hasattr(self, "inbox_tree"):
            return
        self.normalize_inbox_messages()
        selected = self.inbox_tree.selection()
        self.inbox_tree.delete(*self.inbox_tree.get_children())
        status_filter = self.inbox_filter.get() if hasattr(self, "inbox_filter") else "Open"
        type_filter = self.inbox_type_filter.get() if hasattr(self, "inbox_type_filter") else "All"
        search = self.inbox_search.get().strip().lower() if hasattr(self, "inbox_search") else ""
        available_types = sorted({item.get("type", "Mail") for item in self.inbox})
        if hasattr(self, "inbox_type_box"):
            self.inbox_type_box.configure(values=("All", *available_types))
        if type_filter != "All" and type_filter not in available_types:
            type_filter = "All"
            self.inbox_type_filter.set("All")
        items = []
        for index, item in enumerate(self.inbox):
            resolved = item.get("resolved", False)
            seen = item.get("seen", False)
            if item.get("type", "Mail") in getattr(self, "inbox_hidden_types", set()):
                continue
            if status_filter == "Open" and resolved:
                continue
            if status_filter == "Needs Action" and not self.inbox_item_needs_action(item):
                continue
            if status_filter == "Unread" and (resolved or seen):
                continue
            if status_filter == "Read" and (resolved or not seen):
                continue
            if status_filter == "Archived" and not resolved:
                continue
            if type_filter != "All" and item.get("type", "Mail") != type_filter:
                continue
            haystack = " ".join(str(item.get(key, "") or "") for key in ("subject", "body", "type", "fighter", "fighter_id")).lower()
            if search and search not in haystack:
                continue
            items.append((index, item))
        sort_mode = self.inbox_sort.get() if hasattr(self, "inbox_sort") else "Newest"
        date_key = lambda row: (int(row[1].get("created_month", 0) or 0), int(row[1].get("created_week", 0) or 0), row[0])
        if sort_mode == "Oldest":
            items.sort(key=date_key)
        elif sort_mode == "Priority":
            items.sort(key=lambda row: (not self.inbox_item_needs_action(row[1]), row[1].get("resolved", False), -date_key(row)[0], -date_key(row)[1], -row[0]))
        elif sort_mode == "Type":
            items.sort(key=lambda row: (str(row[1].get("type", "Mail")), -date_key(row)[0], -date_key(row)[1], -row[0]))
        else:
            items.sort(key=date_key, reverse=True)
        for index, item in items[:160]:
            urgent = self.inbox_item_needs_action(item)
            tag = "urgent" if urgent else ("" if item.get("seen", False) else "unread")
            state = "!" if urgent else ("" if item.get("seen", False) else "*")
            received = self.format_game_date(item.get("created_month", self.month), item.get("created_week", 1))
            self.inbox_tree.insert("", "end", iid=str(index), tags=(tag,) if tag else (), values=(state, received, item.get("type", "Mail"), item.get("subject", "Untitled")))
        if hasattr(self, "inbox_summary"):
            actions = sum(self.inbox_item_needs_action(item) for item in self.inbox)
            unread = sum(not item.get("seen", False) and not item.get("resolved", False) for item in self.inbox)
            shown = min(160, len(items))
            suffix = " (first 160)" if len(items) > 160 else ""
            self.inbox_summary.configure(text=f"{shown} shown{suffix} | {len(self.inbox)} stored | {unread} unread | {actions} need action")
        if selected and selected[0] in self.inbox_tree.get_children():
            self.inbox_tree.selection_set(selected[0])
        elif self.inbox_tree.get_children():
            self.inbox_tree.selection_set(self.inbox_tree.get_children()[0])
        self.refresh_owner_goals()
        self.show_selected_inbox_message()

    def refresh_owner_goals(self):
        if not hasattr(self, "goals_tree"):
            return
        self.goals_tree.delete(*self.goals_tree.get_children())
        shows = len(self.result_history)
        for index, goal in enumerate(self.owner_goals):
            if goal["metric"] == "cash":
                current = self.cash
            elif goal["metric"] == "popularity":
                current = self.company_pop
            else:
                current = shows
            goal["status"] = "Complete" if current >= goal["target"] else ("Failed" if self.month > goal["deadline"] else "Active")
            progress = f"{current:,} / {goal['target']:,}" if goal["metric"] == "cash" else f"{current} / {goal['target']}"
            tag = "complete" if goal["status"] == "Complete" else "failed" if goal["status"] == "Failed" else ""
            self.goals_tree.insert("", "end", iid=str(index), tags=(tag,) if tag else (), values=(goal["goal"], progress, self.format_game_date(goal["deadline"], 4, include_week=False), goal["status"]))

    def open_selected_owner_goal(self):
        if not hasattr(self, "goals_tree") or not self.goals_tree.selection():
            return
        try:
            goal = self.owner_goals[int(self.goals_tree.selection()[0])]
        except (IndexError, ValueError):
            return
        self.select_tab({"cash": "finance", "popularity": "website"}.get(goal.get("metric"), "booking"))

    def selected_inbox_item(self):
        if not hasattr(self, "inbox_tree"):
            return None
        selected = self.inbox_tree.selection()
        if not selected:
            return None
        try:
            return self.inbox[int(selected[0])]
        except (IndexError, ValueError):
            return None

    def inbox_related_fighter(self, item):
        fighter_id = str(item.get("fighter_id", "") or "")
        if fighter_id:
            exact = next((fighter for fighter in self.all_scoutable_fighters() if self.scouting_report_key(fighter) == fighter_id), None)
            if exact:
                return exact
        text = f"{item.get('subject', '')} {item.get('body', '')}".lower()
        fighters = sorted((fighter for _company, fighter in self.all_database_fighters_with_companies()), key=lambda fighter: len(fighter.name), reverse=True)
        return next((fighter for fighter in fighters if fighter.name.lower() in text), None)

    def show_selected_inbox_message(self, _event=None):
        if not hasattr(self, "inbox_detail"):
            return
        item = self.selected_inbox_item()
        self.inbox_detail.config(state="normal")
        self.inbox_detail.delete("1.0", "end")
        if not item:
            self.inbox_detail.insert("end", "No message selected.")
        else:
            item["seen"] = True
            fighter = self.inbox_related_fighter(item)
            context = f"\n\nRelated fighter: {fighter.name} ({fighter.gender} {fighter.weight})" if fighter else ""
            received = self.format_game_date(item.get("created_month", self.month), item.get("created_week", 1))
            action_status = "Needs action" if self.inbox_item_needs_action(item) else ("Archived" if item.get("resolved") else "For information")
            self.inbox_detail.insert("end", f"{item.get('type', 'Mail').upper()} | RECEIVED {received}\n{item.get('subject', 'Untitled')}\n\n{item.get('body', '')}{context}\n\nStatus: {action_status}")
        self.inbox_detail.config(state="disabled")
        if hasattr(self, "medical_decision_bar"):
            show_medical = bool(item and item.get("action") == "serious_injury" and not item.get("resolved"))
            if show_medical:
                self.medical_decision_bar.pack(fill="x", before=self.inbox_detail)
            else:
                self.medical_decision_bar.pack_forget()

    def mark_inbox_read(self):
        item = self.selected_inbox_item()
        if item:
            item["seen"] = True
            self.refresh_inbox()

    def visible_inbox_items(self):
        rows = []
        for iid in self.inbox_tree.get_children() if hasattr(self, "inbox_tree") else ():
            try:
                rows.append(self.inbox[int(iid)])
            except (IndexError, ValueError):
                continue
        return rows

    def mark_visible_inbox_read(self):
        rows = self.visible_inbox_items()
        for item in rows:
            item["seen"] = True
        if hasattr(self, "inbox_notice"):
            self.inbox_notice.configure(text=f"Marked {len(rows)} visible message(s) as read.")
        self.refresh_inbox()

    def clear_old_inbox(self):
        result = self.maintain_inbox(manual=True)
        if hasattr(self, "inbox_notice"):
            self.inbox_notice.configure(text=f"Cleared {result['removed']} old or no-longer-relevant message(s). {result['remaining']} remain.")
        self.refresh_inbox()

    def hide_selected_inbox_type(self):
        item = self.selected_inbox_item()
        if item:
            self.inbox_hidden_types.add(item.get("type", "Mail"))
            self.refresh_inbox()

    def show_all_inbox_types(self):
        self.inbox_hidden_types.clear()
        self.refresh_inbox()

    def open_inbox_context(self):
        item = self.selected_inbox_item()
        if not item:
            return
        item["seen"] = True
        subject = item.get("subject", "").lower()
        message_type = item.get("type", "")
        fighter = self.inbox_related_fighter(item)
        if item.get("action") == "serious_injury" and fighter:
            self.resolve_serious_injury_inbox()
            return
        if "title shot" in subject:
            self.select_tab("booking")
        elif message_type == "Contract":
            self.select_tab("contracts")
        elif message_type == "Scouting":
            self.select_tab("scouting")
            if fighter:
                self.open_fighter_profile_window(fighter)
        elif message_type in ("Medical", "Roster", "Talent Relations"):
            self.select_tab("roster")
            if fighter:
                self.open_fighter_profile_window(fighter)
        elif message_type == "Staff":
            self.select_tab("staff")
        elif message_type in ("Business", "Media"):
            self.select_tab("finance" if message_type == "Business" else "website")
        elif message_type == "Rules":
            self.select_tab("company_editor")
        elif fighter:
            self.open_fighter_profile_window(fighter)
        self.refresh_inbox()

    def resolve_inbox_item(self):
        item = self.selected_inbox_item()
        if item:
            item["resolved"] = True
            item["seen"] = True
            self.refresh_all()

    def resolve_serious_injury_inbox(self):
        item = self.selected_inbox_item()
        if not item or item.get("action") != "serious_injury":
            self.select_tab("inbox")
            return
        fighter = self.inbox_related_fighter(item)
        if not fighter or not getattr(fighter, "serious_injury_pending", False):
            item["resolved"] = True
            self.refresh_all()
            return
        self.show_selected_inbox_message()

    def apply_inbox_medical_decision(self, decision):
        item = self.selected_inbox_item()
        if not item or item.get("action") != "serious_injury":
            return
        fighter = self.inbox_related_fighter(item)
        if not fighter or not getattr(fighter, "serious_injury_pending", False):
            item["resolved"] = True
            self.refresh_all()
            return
        self.resolve_serious_injury(fighter, decision)
        item["resolved"] = True
        item["seen"] = True
        self.record_change("Medical", fighter.name, decision.title(), f"Medical decision following {fighter.serious_injury or 'serious injury'}", 2)
        self.refresh_all()

    def refresh_staff(self):
        self.staff_tree.delete(*self.staff_tree.get_children())
        for index, member in enumerate(self.staff):
            self.staff_tree.insert("", "end", iid=str(index), values=(member["name"], member["role"], member["skill"], f"${member['salary']:,}", member["morale"]))
        if hasattr(self, "staff_candidate_tree"):
            self.staff_candidate_tree.delete(*self.staff_candidate_tree.get_children())
            for index, member in enumerate(self.staff_candidates):
                self.staff_candidate_tree.insert("", "end", iid=str(index), values=(member["name"], member["role"], member["skill"], f"${member['salary']:,}", member["morale"]))
        self.staff_text.config(state="normal")
        self.staff_text.delete("1.0", "end")
        self.staff_text.insert("end", f"Post-show bonuses: Fight ${self.post_show_bonuses['fight']:,}, KO ${self.post_show_bonuses['ko']:,}, Sub ${self.post_show_bonuses['sub']:,}\n\n")
        self.staff_text.insert("end", "Staff Effects\n")
        for role in ("Matchmaker", "Marketing", "Scout", "Talent Relations", "Doctor"):
            members = [member for member in self.staff if member.get("role") == role]
            if members:
                lead = max(members, key=lambda member: member.get("skill", 0))
                self.staff_text.insert("end", f"- {role}: {lead['name']} ({lead.get('specialty', 'Operations')}) | skill {lead['skill']} | rep {lead.get('reputation', 50)}\n")
        self.staff_text.insert("end", "\n")
        self.staff_text.insert("end", "Recent Scouting Activity (manage assignments on the Scouting screen):\n")
        if self.scouting:
            for assignment in self.scouting[-12:]:
                self.staff_text.insert("end", f"- {assignment}\n")
        else:
            self.staff_text.insert("end", "- No active scouting assignments.\n")
        self.staff_text.config(state="disabled")
        if hasattr(self, "scouting_assignment_tree"):
            self.refresh_scouting_center()

    def scout_signing_recommendation(self, fighter, report):
        if not fighter or report.get("status") != "Complete":
            return "PENDING", "The scout has not completed enough work to make a recruitment recommendation."

        def estimate(key, fallback=50):
            return self.scouting_estimate(fighter, key, {}) or {"low": fallback, "mid": fallback, "high": fallback}

        overall_est, potential_est = estimate("overall"), estimate("potential")
        popularity_est, star_est = estimate("popularity"), estimate("star_quality")
        overall, potential = int(overall_est.get("mid", 50)), int(potential_est.get("mid", 50))
        popularity, star = int(popularity_est.get("mid", 50)), int(star_est.get("mid", 50))

        division_key = self.belt_key(fighter.gender, fighter.weight)
        division_closed = division_key in set(getattr(self, "closed_divisions", set()))
        division_count = sum(candidate.gender == fighter.gender and candidate.weight == fighter.weight for candidate in self.roster)
        need = 0 if division_closed else max(0, 10 - division_count)

        # A flat weight on "potential" treats a 38-year-old at his ceiling the
        # same as a 22-year-old with real development room. Give the gap real
        # upside only while there's runway left to close it, and let age past
        # the prime years erode value instead of just diluting the bonus.
        runway_gap = max(0, potential - overall)
        if fighter.age <= 26:
            runway_bonus = runway_gap * 0.12 + max(0, 26 - fighter.age) * 0.4
        elif fighter.age <= 33:
            runway_bonus = runway_gap * 0.05
        else:
            runway_bonus = -max(0, fighter.age - 33) * 1.1

        # A wide low/high spread means the scout isn't confident in the read;
        # a stale or basic report shouldn't carry the same weight as a fresh
        # full workup when it lands on the same midpoint.
        spread = (overall_est.get("high", overall) - overall_est.get("low", overall)) + \
            (potential_est.get("high", potential) - potential_est.get("low", potential))
        confidence_penalty = max(0, (spread - 10) * 0.25)

        projected_value = overall * 0.48 + potential * 0.10 + popularity * 0.12 + star * 0.08 + need * 1.7 + runway_bonus
        affordability = max(-12, min(8, (self.cash / max(1, fighter.purse * 20) - 1) * 3))
        score = projected_value + affordability - confidence_penalty

        context = (
            f"Projected OVR {overall}, ceiling {potential}, market pull {round((popularity + star) / 2)}, "
            f"division depth {division_count}, asking ${fighter.purse:,}."
        )

        red_flags = []
        if getattr(fighter, "injured", 0):
            red_flags.append("currently injured")
        if getattr(fighter, "retirement_pending", False):
            red_flags.append("weighing retirement")
        if division_closed:
            red_flags.append("division closed to new signings")
        streak = self.in_universe_loss_streak(fighter)
        if streak >= 3:
            red_flags.append(f"on a {streak}-fight losing streak")
        if red_flags:
            return "PASS", context + " Red flag: " + "; ".join(red_flags) + "."

        if confidence_penalty >= 4:
            context += " Report confidence is low; a fresher scouting pass would sharpen this read."

        if score >= 60 or (need >= 5 and score >= 56):
            return "RECOMMEND SIGNING", context + " This report sees a strong sporting or roster-fit case, subject to negotiation."
        if score >= 52:
            return "MONITOR", context + " Useful target, but price, uncertainty, or divisional need does not justify immediate pursuit."
        return "PASS", context + " The projected contribution does not currently justify the roster and salary commitment."

    def scouting_target_company_for(self, fighter):
        key = self.scouting_report_key(fighter)
        if any(self.scouting_report_key(candidate) == key for candidate in self.free_agents):
            return "Free Agent"
        for promo in self.promotions:
            if any(self.scouting_report_key(candidate) == key for candidate in promo.roster):
                return promo.name
        return "Independent"

    def scouting_intel_label(self, fighter, report):
        if not self.rules.get("scouting_mode", True):
            return "Open Database"
        if not report:
            return "Unscouted"
        status = report.get("status", "")
        if status == "In progress":
            return "In Progress"
        if status != "Complete":
            return status or "Unscouted"
        completed = int(report.get("completed_week", self.calendar_week_index()) or self.calendar_week_index())
        if self.calendar_week_index() - completed > 52:
            return "Stale"
        return {"basic": "Basic", "full": "Full", "observation": "Observed"}.get(report.get("kind"), "Scouted")

    def reset_scouting_target_page(self):
        self.scouting_target_page = 0
        self.refresh_scouting_targets()

    def change_scouting_target_page(self, direction):
        self.scouting_target_page = max(0, int(getattr(self, "scouting_target_page", 0)) + int(direction))
        self.refresh_scouting_targets()

    def refresh_scouting_targets(self):
        if not hasattr(self, "scouting_target_tree"):
            return
        self.migrate_scouting_state()
        shortlist = set(str(key) for key in getattr(self, "scouting_shortlist", []))
        player_ids = {self.scouting_report_key(fighter) for fighter in self.roster}
        candidates = []
        seen = set()

        def add_candidates(company, roster):
            for fighter in roster:
                key = self.scouting_report_key(fighter)
                if key in seen or key in player_ids or getattr(fighter, "retired", False):
                    continue
                if getattr(fighter, "sport_employer", "") and getattr(fighter, "primary_discipline", "MMA") != "MMA":
                    continue
                seen.add(key)
                candidates.append((key, company, fighter))

        add_candidates("Free Agent", self.free_agents)
        for promo in self.promotions:
            add_candidates(promo.name, promo.roster)
        for fighter in self.all_scoutable_fighters():
            key = self.scouting_report_key(fighter)
            if key not in seen and key not in player_ids and not getattr(fighter, "retired", False):
                add_candidates("Independent", (fighter,))
        companies = ["All"] + sorted({company for _key, company, _fighter in candidates})
        self.scouting_target_company_box.configure(values=companies)
        if self.scouting_target_company.get() not in companies:
            self.scouting_target_company.set("All")
        search = self.scouting_target_search.get().strip().lower()
        company_filter = self.scouting_target_company.get()
        gender_filter = self.scouting_target_gender.get()
        weight_filter = self.scouting_target_weight.get()
        intel_filter = self.scouting_target_status.get()
        filtered = []
        for key, company, fighter in candidates:
            report = self.scouting_report_for(fighter)
            intel = self.scouting_intel_label(fighter, report)
            advice = self.scout_signing_recommendation(fighter, report)[0] if report.get("status") == "Complete" else "-"
            watched = key in shortlist
            if search and search not in fighter.name.lower() and search not in company.lower():
                continue
            if company_filter != "All" and company != company_filter:
                continue
            if gender_filter != "All" and fighter.gender != gender_filter:
                continue
            if weight_filter != "All" and fighter.weight != weight_filter:
                continue
            if intel_filter == "Shortlisted" and not watched:
                continue
            if intel_filter == "Unscouted" and report:
                continue
            if intel_filter == "In Progress" and report.get("status") != "In progress":
                continue
            if intel_filter == "Scouted" and report.get("status") != "Complete":
                continue
            if intel_filter == "Stale" and intel != "Stale":
                continue
            if intel_filter == "Free Agents" and company != "Free Agent":
                continue
            if intel_filter == "Rival Rosters" and company in ("Free Agent", "Independent"):
                continue
            if intel_filter == "Recommended Signings" and advice != "RECOMMEND SIGNING":
                continue
            if intel_filter == "Monitor" and advice != "MONITOR":
                continue
            if intel_filter == "Pass" and advice != "PASS":
                continue
            report_rank = {"Full": 4, "Observed": 3, "Basic": 2, "Stale": 1, "In Progress": 0}.get(intel, 0)
            advice_rank = {"RECOMMEND SIGNING": 3, "MONITOR": 2, "PASS": 1}.get(advice, 0)
            public_merit = fighter.record_w * 2 - fighter.record_l + fighter.record_d * 0.25
            filtered.append((not watched, -advice_rank, -report_rank, -public_merit, fighter.name.lower(), key, company, fighter, report, intel, advice))
        filtered.sort(key=lambda row: row[:5])
        total_matches = len(filtered)
        page_size = max(100, int(getattr(self, "scouting_target_page_size", 400)))
        max_page = max(0, (total_matches - 1) // page_size)
        page = min(max_page, max(0, int(getattr(self, "scouting_target_page", 0))))
        self.scouting_target_page = page
        start = page * page_size
        end = min(total_matches, start + page_size)
        visible = filtered[start:end]
        if hasattr(self, "scouting_target_count_var"):
            if total_matches:
                self.scouting_target_count_var.set(f"Showing {start + 1:,}-{end:,} of {total_matches:,} | Page {page + 1} of {max_page + 1}")
            else:
                self.scouting_target_count_var.set("No fighters match these filters")
        self.scouting_target_tree.delete(*self.scouting_target_tree.get_children())
        self._scouting_target_rows = {}
        open_database = not self.rules.get("scouting_mode", True)
        for _watch_sort, _advice_sort, _report_sort, _merit, _name, key, company, fighter, report, intel, advice in visible:
            overall = str(fighter.overall) if open_database else self.format_scouting_estimate(self.scouting_estimate(fighter, "overall", {}))
            potential = str(fighter.potential) if open_database else self.format_scouting_estimate(self.scouting_estimate(fighter, "potential", {}))
            row_id = f"target:{key}"
            self._scouting_target_rows[row_id] = (company, fighter)
            if key in shortlist:
                tags = ("shortlisted",)
            elif intel == "Stale":
                tags = ("stale",)
            else:
                advice_tag = self._scouting_advice_tag(advice)
                tags = (advice_tag,) if advice_tag else ()
            self.scouting_target_tree.insert("", "end", iid=row_id, values=("WATCH" if key in shortlist else "", fighter.name, company, fighter.gender[:1], fighter.weight, fighter.record, fighter.age, intel, advice, overall, potential, self.fighter_last_fight_date_label(fighter)), tags=tags)
        if hasattr(self, "scouting_board_summary_var"):
            recommend = sum(1 for row in filtered if row[10] == "RECOMMEND SIGNING")
            watched = sum(1 for row in filtered if not row[0])  # row[0] is `not watched`
            in_progress = sum(1 for report in self.scouting_reports.values() if report.get("status") == "In progress")
            scouts = [member for member in self.staff if member.get("role") == "Scout"]
            idle_slots = sum(max(0, self.scout_capacity(member) - self.scout_workload(member.get("name"))) for member in scouts)
            self.scouting_board_summary_var.set(
                f"{recommend} recommended · {watched} shortlisted · {in_progress} report(s) in progress · {idle_slots} free scout slot(s)"
            )

    @staticmethod
    def _scouting_advice_tag(advice):
        return {
            "RECOMMEND SIGNING": "advice_sign",
            "MONITOR": "advice_monitor",
            "PASS": "advice_pass",
        }.get(advice, "")

    def format_scouting_estimate(self, estimate):
        if not estimate:
            return "?"
        low, high = estimate.get("low"), estimate.get("high")
        if low is None or high is None:
            return "?"
        return str(low) if low == high else f"{low}-{high}"

    def selected_recruitment_target(self):
        selected = self.scouting_target_tree.selection() if hasattr(self, "scouting_target_tree") else ()
        return self._scouting_target_rows.get(selected[0]) if selected else None

    def show_selected_recruitment_target_summary(self):
        """Explain the selected fighter's intel state and recruitment advice."""
        selected = self.selected_recruitment_target()
        if not selected or not hasattr(self, "scouting_target_status_var"):
            return
        company, fighter = selected
        report = self.scouting_report_for(fighter)
        intel = self.scouting_intel_label(fighter, report)
        if intel == "Stale":
            self.scouting_target_status_var.set(f"{fighter.name} | Stale intel: this report is over one year old. Commission a new dossier before relying on its ranges or advice.")
            return
        if report.get("status") == "Complete":
            recommendation, reason = self.scout_signing_recommendation(fighter, report)
            self.scouting_target_status_var.set(f"{fighter.name} | {company} | {intel} intel | {recommendation}: {reason}")
            return
        if report.get("status") == "In progress":
            kind = str(report.get("kind", "basic")).replace("_", " ").title()
            due = "their next fight" if report.get("kind") == "observation" else f"{report.get('weeks_remaining', 0)} week(s)"
            self.scouting_target_status_var.set(f"{fighter.name} | {kind} in progress with {report.get('scout', 'assigned staff')} | Due: {due}. No signing recommendation is available yet.")
            return
        self.scouting_target_status_var.set(f"{fighter.name} | Unscouted. Public record and career information are visible, but ability, ceiling, and recruitment value remain uncertain.")

    def start_selected_recruitment_report(self, kind):
        selected = self.selected_recruitment_target()
        if not selected:
            self.scouting_target_status_var.set("Select a recruitment target first.")
            return
        _company, fighter = selected
        selected_scout = self.scouting_scout_var.get()
        scout_name = None if selected_scout in ("", "Auto Assign") else selected_scout
        if self.start_scout_report_for_fighter(fighter, kind, scout_name=scout_name):
            self.scouting_target_status_var.set(f"{kind.title()} assignment started for {fighter.name}.")
            self.refresh_scouting_center()

    def toggle_selected_scouting_shortlist(self):
        selected = self.selected_recruitment_target()
        if not selected:
            self.scouting_target_status_var.set("Select a fighter to add to the shortlist.")
            return
        _company, fighter = selected
        key = self.scouting_report_key(fighter)
        shortlist = list(dict.fromkeys(str(value) for value in getattr(self, "scouting_shortlist", [])))
        if key in shortlist:
            shortlist.remove(key)
            action = "Removed"
        else:
            shortlist.append(key)
            action = "Added"
        self.scouting_shortlist = shortlist
        self.scouting_target_status_var.set(f"{action} {fighter.name} {'from' if action == 'Removed' else 'to'} the recruitment shortlist.")
        self.refresh_scouting_targets()
        row_id = f"target:{key}"
        if self.scouting_target_tree.exists(row_id):
            self.scouting_target_tree.selection_set(row_id)
            self.scouting_target_tree.see(row_id)

    def open_selected_recruitment_target(self):
        selected = self.selected_recruitment_target()
        if selected:
            self.open_fighter_profile_window(selected[1])
        else:
            self.scouting_target_status_var.set("Select a fighter to open their profile.")

    def negotiate_selected_recruitment_target(self):
        selected = self.selected_recruitment_target()
        if not selected:
            self.scouting_target_status_var.set("Select a fighter to approach.")
            return
        company, fighter = selected
        if company != "Free Agent":
            self.scouting_target_status_var.set(f"{fighter.name} is contracted to {company}; they cannot enter free-agent negotiations yet.")
            return
        self.open_contract_negotiation(fighter, existing=False)

    def refresh_scouting_center(self):
        if not hasattr(self, "scouting_assignment_tree"):
            return
        self.migrate_scouting_state()
        scouts = [member for member in self.staff if member.get("role") == "Scout"]
        names = [member.get("name") for member in scouts]
        scout_choices = ["Auto Assign", *names]
        self.scouting_scout_box.configure(values=scout_choices)
        if hasattr(self, "scouting_target_scout_box"):
            self.scouting_target_scout_box.configure(values=scout_choices)
        if self.scouting_scout_var.get() not in scout_choices:
            self.scouting_scout_var.set("Auto Assign")
        self.scouting_assignment_tree.delete(*self.scouting_assignment_tree.get_children())
        self.scouting_assignment_rows = {}
        fighters = {self.scouting_report_key(fighter): fighter for fighter in self.all_scoutable_fighters()}
        for fighter_id, report in sorted(self.scouting_reports.items(), key=lambda item: (item[1].get("status") != "In progress", -int(item[1].get("started_week", 0)))):
            fighter = fighters.get(fighter_id)
            kind = str(report.get("kind", "basic")).replace("_", " ").title()
            if report.get("automatic"):
                kind = f"Auto {kind}"
            due = "Next fight" if report.get("kind") == "observation" and report.get("status") == "In progress" else (f"{report.get('weeks_remaining', 0)} wk" if report.get("status") == "In progress" else self.format_game_date(self.month, self.week, include_week=False))
            confidence = self.scouting_effective_confidence(report) if report.get("status") == "Complete" else "-"
            advice = self.scout_signing_recommendation(fighter, report)[0] if fighter else "-"
            row_id = f"report:{fighter_id}"
            self.scouting_assignment_rows[row_id] = {"type": "report", "fighter": fighter, "report": report}
            if report.get("status") == "In progress":
                report_tags = ("assignment_pending",)
            else:
                advice_tag = self._scouting_advice_tag(advice)
                report_tags = (advice_tag,) if advice_tag else ()
            self.scouting_assignment_tree.insert("", "end", iid=row_id, values=(kind, report.get("fighter_name", getattr(fighter, "name", fighter_id)), report.get("scout", "-"), report.get("status", "-"), due, f"{confidence}%" if isinstance(confidence, int) else confidence, advice, f"${int(report.get('cost', 0)):,}"), tags=report_tags)
        for index, search in enumerate(getattr(self, "scouting_searches", [])):
            row_id = f"search:{index}"
            self.scouting_assignment_rows[row_id] = {"type": "search", "search": search}
            due = f"{search.get('weeks_remaining', 0)} wk" if search.get("status") == "In progress" else "Complete"
            self.scouting_assignment_tree.insert("", "end", iid=row_id, values=("Talent Search", f"{search.get('region')} | {search.get('gender')} {search.get('weight')}", search.get("scout", "-"), search.get("status", "-"), due, "-", search.get("result_name", "-") if search.get("status") == "Complete" else "Searching", f"${int(search.get('cost', 0)):,}"))
        academy = getattr(self, "academy", {}) or {}
        if academy.get("network_scout") and (academy.get("network_active") or academy.get("network_weeks", 0) > 0):
            self.scouting_assignment_rows["academy"] = {"type": "academy"}
            status = "Active" if academy.get("network_active") else "Building"
            self.scouting_assignment_tree.insert("", "end", iid="academy", values=("Academy Network", academy.get("network_region", "-"), academy.get("network_scout"), status, f"{academy.get('network_weeks', 0)} wk" if not academy.get("network_active") else "Ongoing", "-", "Youth leads", "Ongoing"))
        capacity = " | ".join(f"{member['name']} {self.scout_workload(member['name'])}/{self.scout_capacity(member)} slots" for member in scouts) or "No hired scouts; fighter profiles can commission one independent report at a time."
        if not self.scouting_status_var.get().startswith(("Search started", "Cancelled", "Cannot")):
            self.scouting_status_var.set(capacity)
        self.show_selected_scouting_assignment()
        self.refresh_scouting_targets()

    def show_selected_scouting_assignment(self):
        if not hasattr(self, "scouting_detail_text"):
            return
        selected = self.scouting_assignment_tree.selection()
        row = self.scouting_assignment_rows.get(selected[0]) if selected else None
        text = "Select an assignment. Completed fighter reports include a scout recommendation based on projected ability, upside, market value, division need, and asking price."
        if row and row.get("type") == "report":
            fighter, report = row.get("fighter"), row.get("report", {})
            recommendation, reason = self.scout_signing_recommendation(fighter, report)
            ranges = []
            for key, label in (("overall", "OVR"), ("potential", "Potential"), ("popularity", "Popularity"), ("professionalism", "Professionalism")):
                estimate = self.scouting_estimate(fighter, key, {}) if fighter else {}
                if estimate:
                    ranges.append(f"{label}: {estimate.get('low')}-{estimate.get('high')}")
            text = f"{report.get('fighter_name')} | {report.get('kind', 'basic').title()} | {report.get('status')}\nScout: {report.get('scout')} | Confidence: {self.scouting_effective_confidence(report)}%\n" + (" | ".join(ranges) or "Report work is still in progress.") + f"\n\n{recommendation}\n{reason}\n\n" + "\n".join(f"- {note}" for note in report.get("notes", []))
        elif row and row.get("type") == "search":
            search = row.get("search", {})
            text = f"Talent Search | {search.get('region')}\nScout: {search.get('scout')} | Status: {search.get('status')} | Brief: {search.get('gender')} {search.get('weight')}\nResult: {search.get('result_name', 'Search in progress')}"
        elif row and row.get("type") == "academy":
            text = "The academy youth network uses one assignment slot from its named scout. Manage its region, leads, and cancellation from Fight Academy."
        self.scouting_detail_text.config(state="normal")
        self.scouting_detail_text.delete("1.0", "end")
        self.scouting_detail_text.insert("end", text)
        self.scouting_detail_text.config(state="disabled")

    def cancel_selected_scouting_assignment(self):
        selected = self.scouting_assignment_tree.selection() if hasattr(self, "scouting_assignment_tree") else ()
        row = self.scouting_assignment_rows.get(selected[0]) if selected else None
        if not row:
            self.scouting_status_var.set("Select an active report or talent search to cancel.")
            return
        target = row.get("report") if row.get("type") == "report" else row.get("search") if row.get("type") == "search" else None
        if not target or target.get("status") != "In progress":
            self.scouting_status_var.set("Only an active fighter report or talent search can be cancelled here.")
            return
        target["status"] = "Cancelled"
        target["weeks_remaining"] = 0
        self.scouting_status_var.set("Cancelled assignment. Spent scouting costs are not refunded.")
        self.refresh_scouting_center()

    def open_selected_scouting_target(self):
        selected = self.scouting_assignment_tree.selection() if hasattr(self, "scouting_assignment_tree") else ()
        row = self.scouting_assignment_rows.get(selected[0]) if selected else None
        fighter = row.get("fighter") if row else None
        if fighter:
            self.open_fighter_profile_window(fighter)
        elif hasattr(self, "scouting_status_var"):
            self.scouting_status_var.set("This assignment is not attached to an individual fighter profile.")

    def hire_staff(self):
        selected = self.staff_candidate_tree.selection() if hasattr(self, "staff_candidate_tree") else []
        if not selected:
            messagebox.showinfo("Staff Market", "Select a staff candidate to hire.")
            return
        member = self.staff_candidates.pop(int(selected[0]))
        signing_cost = member["salary"] * 2
        if self.cash < signing_cost:
            self.staff_candidates.insert(int(selected[0]), member)
            messagebox.showwarning("Not enough cash", f"Hiring {member['name']} needs a ${signing_cost:,} signing budget.")
            return
        self.cash -= signing_cost
        self.record_finance_transaction(f"Staff signing: {member['name']}", costs=signing_cost)
        self.staff.append(member)
        self.staff_candidates.append(self.create_staff_candidate())
        self.inbox.append({"subject": "Staff Hire", "body": f"Hired {member['name']} as {member['role']} for ${member['salary']:,}/month.", "type": "Staff", "resolved": False})
        self.refresh_all()

    def simulate_ai_staff_market(self):
        if not hasattr(self, "staff_candidates"):
            self.staff_candidates = self.seed_staff_candidates()
        if random.random() < 0.18 and self.staff_candidates:
            candidate = self.staff_candidates.pop(random.randrange(len(self.staff_candidates)))
            promo = random.choice(self.promotions)
            if promo.cash > candidate["salary"] * 6:
                promo.cash -= candidate["salary"] * 2
                self.news.insert(0, f"Week {self.week}: {promo.name} hired {candidate['name']} as {candidate['role']}.")
        if len(self.staff_candidates) < 14 or random.random() < 0.22:
            self.staff_candidates.append(self.create_staff_candidate())
        self.staff_candidates = sorted(self.staff_candidates, key=lambda c: c["skill"], reverse=True)[:18]

    def assign_scouting(self):
        if not hasattr(self, "scouting_scout_var"):
            self.select_tab("scouting")
            return
        scout_name = self.scouting_scout_var.get()
        if scout_name in ("", "Auto Assign"):
            available = [
                scout for scout in self.staff
                if scout.get("role") == "Scout" and self.scout_workload(scout.get("name")) < self.scout_capacity(scout)
            ]
            region = self.scouting_region_var.get()
            scout = max(
                available,
                key=lambda member: (
                    member.get("networking", member.get("skill", 45)) * 0.38
                    + member.get("regional_knowledge", member.get("skill", 45)) * 0.30
                    + member.get("efficiency", member.get("skill", 45)) * 0.20
                    + member.get("reliability", member.get("skill", 45)) * 0.12
                    + (8 if member.get("region") == region else 0)
                ),
                default=None,
            )
            scout_name = scout.get("name") if scout else ""
        ok, message = self.start_talent_search(scout_name, self.scouting_region_var.get(), self.scouting_gender_var.get(), self.scouting_weight_var.get())
        self.scouting_status_var.set(("Search started: " if ok else "Cannot start search: ") + message)
        self.refresh_scouting_center()
        self.refresh_header()

    def run_drug_tests(self):
        tested = random.sample(self.roster, k=min(6, len(self.roster)))
        positives = []
        accuracy = {"None": 0, "Standard": 0.04, "Strict": 0.08, "Olympic": 0.12}[self.rules.get("drug_testing", "Standard")]
        cost = len(tested) * self.finance["drug_test_cost"]
        self.cash -= cost
        self.record_finance_transaction("Drug testing", costs=cost)
        self.finance["ledger"].insert(0, f"Month {self.month}: Drug testing cost ${cost:,}")
        for fighter in tested:
            if random.random() < accuracy:
                fighter.injured = max(fighter.injured, 2)
                positives.append(fighter.name)
        body = f"Tested {len(tested)} fighters. Positives: {', '.join(positives) if positives else 'None'}."
        self.inbox.append({"subject": "Drug Testing Results", "body": body, "type": "Medical", "resolved": False})
        self.refresh_all()

    def refresh_finance(self):
        if not hasattr(self, "finance_tree"):
            return
        payroll = sum(s["salary"] for s in self.staff)
        self.finance["staff_payroll"] = payroll
        self.ensure_finance_defaults()
        self.finance.setdefault("sponsor_offers", [])
        self.finance.setdefault("sponsor_offer_history", [])
        media = self.finance["media_rights"]
        sponsor_total = self.finance["sponsor_income"] + sum(deal["fee"] for deal in self.finance["sponsor_deals"])
        academy = getattr(self, "academy", {}) or {}
        academy_monthly = academy.get("weekly_cost", 0) * 4 if academy.get("owned") else 0
        booked_purses = sum((fight.get("red").purse + fight.get("blue").purse) for event in getattr(self, "scheduled_events", []) for fight in event.get("fights", []) if fight.get("red") and fight.get("blue"))
        active_injuries = [fighter for fighter in self.all_fighter_objects() if getattr(fighter, "injured", 0)]
        medical_base = self.finance.get("medical_base", 6500)
        medical_expected = medical_base + len(active_injuries) * 1400
        sport_divisions = getattr(self, "player_combat_divisions", {}) or {}
        sport_costs = sum(max(0, division.get("cost_total", 0) - division.get("revenue_total", 0)) for division in sport_divisions.values())
        sport_net = sum(division.get("profit_total", 0) for division in sport_divisions.values())
        monthly_fixed = self.finance["monthly_office"] + payroll + academy_monthly + medical_expected
        income_per_event = media.get("fee", 0) + sponsor_total
        self.finance_summary.config(text=(
            f"Cash ${self.cash:,.0f}     Ticket ${self.finance['ticket_price']}     Sponsor/Event ${sponsor_total:,.0f}     "
            f"Office + Payroll ${self.finance['monthly_office'] + payroll:,.0f}/month\n"
            f"Media: {media['name']} ({media['months']} mo, {media.get('events_remaining', 0)} event(s), ${media['fee']:,.0f}/event, reach +{media['reach']})     "
            f"Marketing ${self.finance['marketing_budget']:,.0f}/event     Tax {round(self.finance['tax_rate'] * 100)}%\n"
            f"Forecast: fixed monthly burn ${monthly_fixed:,.0f} (office/payroll ${self.finance['monthly_office'] + payroll:,.0f}, academy ${academy_monthly:,.0f}, medical ${medical_expected:,.0f})     "
            f"Upcoming booked purses ${booked_purses:,.0f}     Expected media+sponsor income/event ${income_per_event:,.0f}\n"
            f"Child sport divisions: {len(sport_divisions)} open | lifetime net ${sport_net:,.0f} | unrecovered setup/card costs ${sport_costs:,.0f}"
        ))
        if hasattr(self, "sponsor_market_tree"):
            self.finance["sponsor_offers"] = [offer for offer in self.finance.get("sponsor_offers", []) if int(offer.get("expires_month", self.month + 1)) >= self.month]
            selected_sponsor = self.sponsor_market_tree.selection()
            self.sponsor_market_tree.delete(*self.sponsor_market_tree.get_children())
            for index, deal in enumerate(self.finance.get("sponsor_deals", [])):
                requirement = deal.get("activation_requirement", "Event brand placement")
                self.sponsor_market_tree.insert("", "end", iid=f"active-{index}", tags=("active",), values=("ACTIVE", deal.get("name", "Sponsor"), deal.get("category", "Partner"), f"${deal.get('fee', 0):,}", f"{deal.get('months', 0)} mo", deal.get("fit", "-"), requirement))
            for offer in self.finance.get("sponsor_offers", []):
                self.sponsor_market_tree.insert("", "end", iid=offer["id"], tags=("offer",), values=("OFFER", offer["name"], offer["category"], f"${offer['fee']:,}", f"{offer['months']} mo", offer["fit"], offer["activation_requirement"]))
            if selected_sponsor and selected_sponsor[0] in self.sponsor_market_tree.get_children():
                self.sponsor_market_tree.selection_set(selected_sponsor[0])
            self.sponsor_market_note.config(text=self.finance.get("sponsor_market_note", "Pitch the market once per month, compare terms, then choose which category partners fit the promotion."))
        selected = self.finance_tree.selection()
        self.finance_tree.delete(*self.finance_tree.get_children())
        history = self.finance["weekly_history"][-48:]
        for index, row in enumerate(history):
            net = row.get("net", row.get("ending", 0) - row.get("opening", 0))
            tag = "positive" if net >= 0 else "negative"
            self.finance_tree.insert("", "end", iid=str(index), tags=(tag,), values=(
                self.format_game_date(row['month'], row['week']), f"${row['opening']:,.0f}", f"${row['revenue']:,.0f}",
                f"${row['costs']:,.0f}", f"${net:,.0f}", f"${row['ending']:,.0f}",
            ))
        if selected and selected[0] in self.finance_tree.get_children():
            self.finance_tree.selection_set(selected[0])
        elif self.finance_tree.get_children():
            self.finance_tree.selection_set(self.finance_tree.get_children()[-1])
        self.show_selected_finance_week()

    def show_selected_finance_week(self, _event=None):
        if not hasattr(self, "finance_detail"):
            return
        selected = self.finance_tree.selection()
        history = self.finance.get("weekly_history", [])[-48:]
        row = history[int(selected[0])] if selected and int(selected[0]) < len(history) else None
        self.finance_detail.config(state="normal")
        self.finance_detail.delete("1.0", "end")
        if row:
            self.finance_detail.insert("end", f"{self.format_game_date(row['month'], row['week']).upper()}\n\nOpening balance: ${row['opening']:,.0f}\nRevenue: ${row['revenue']:,.0f}\nCosts: ${row['costs']:,.0f}\nNet movement: ${row.get('net', row['ending'] - row['opening']):,.0f}\nClosing balance: ${row['ending']:,.0f}\n\nTRANSACTIONS\n")
            transactions = row.get("transactions", [])
            if transactions:
                for item in transactions:
                    self.finance_detail.insert("end", f"- {self.format_game_date_text(item['label'])}: +${item['revenue']:,.0f} / -${item['costs']:,.0f}\n")
            else:
                self.finance_detail.insert("end", "- No player cash transactions recorded this week.\n")
        else:
            self.finance_detail.insert("end", "Advance time or run an event to begin building the 12-month cashflow history.")
        self.finance_detail.config(state="disabled")

    def ensure_finance_defaults(self):
        # AI promotions created by older saves may have an empty/minimal
        # finance dictionary.  A player can take control of any of them, so
        # repair the full player-finance shape before a screen reads a key.
        if not isinstance(getattr(self, "finance", None), dict):
            self.finance = {}
        for key, value in self.seed_finance().items():
            self.finance.setdefault(key, value)
        self.finance.setdefault("sponsor_deals", [])
        self.finance.setdefault("media_rights", {"name": "No rights package", "months": 0, "fee": 0, "reach": 0, "events_remaining": 0})
        rights = self.finance["media_rights"]
        if "events_remaining" not in rights:
            # Pre-media-market saves used only a term in months.  Preserve an
            # active deal rather than repairing it into a zero-event contract.
            rights["events_remaining"] = max(1, min(24, int(rights.get("months", 0)))) if rights.get("months", 0) > 0 and rights.get("name") not in ("", "No rights package") else 0
        self.finance.setdefault("commentators", [
            {"name": "Mike Lane", "role": "Play-by-play", "quality": 62, "salary": 3500, "chemistry": 58},
            {"name": "Laura Nash", "role": "Analyst", "quality": 66, "salary": 4200, "chemistry": 64},
        ])
        self.finance.setdefault("ledger", [])
        self.finance.setdefault("weekly_history", [])
        self.finance.setdefault("week_transactions", [])

    def adjust_ticket_price(self, amount):
        self.finance["ticket_price"] = max(15, min(250, self.finance["ticket_price"] + amount))
        self.finance["ledger"].insert(0, f"Month {self.month}: Ticket price adjusted to ${self.finance['ticket_price']}.")
        self.refresh_all()

    def legacy_pitch_sponsors(self):
        self.ensure_finance_defaults()
        top_appeal = sum(sorted((f.sponsor_appeal for f in self.roster), reverse=True)[:8])
        company_score = self.company_pop * 1.6 + self.company_stability + top_appeal / 8
        success = company_score + random.randint(-35, 35)
        if success < 135:
            self.finance["ledger"].insert(0, f"Month {self.month}: Sponsor pitch failed; brands wanted more stability and star power.")
            self.inbox.append({"subject": "Sponsor Pitch Failed", "body": "Brands passed after reviewing popularity, stability, and roster sponsor appeal.", "type": "Business", "resolved": False})
            self.refresh_all()
            return
        names = ["Prime Hydration", "Venum Fight Gear", "Manscaped", "Monster Energy", "DraftKings", "Modelo", "Hayabusa"]
        fee = round((company_score * random.randint(120, 260)) / 10) * 10
        deal = {"name": random.choice(names), "fee": max(4500, fee), "months": random.randint(6, 18), "fit": round(min(99, company_score / 2))}
        self.finance["sponsor_deals"].insert(0, deal)
        self.finance["sponsor_deals"] = self.finance["sponsor_deals"][:6]
        old_stability = self.company_stability
        self.company_stability = min(100, self.company_stability + 1)
        if self.company_stability != old_stability:
            self.record_change("Stability", self.player_company_name, self.company_stability - old_stability, f"Sponsor agreement with {deal['name']}")
        self.finance["ledger"].insert(0, f"Month {self.month}: Signed sponsor {deal['name']} for ${deal['fee']:,}/event over {deal['months']} months.")
        self.inbox.append({"subject": "Sponsor Signed", "body": f"{deal['name']} signed for ${deal['fee']:,}/event.", "type": "Business", "resolved": False})
        self.refresh_all()

    def legacy_negotiate_media_rights(self):
        self.ensure_finance_defaults()
        show_base = min(18, len(self.result_history) * 2)
        champion_value = sum(f.popularity + f.star_quality for f in self.roster if f.champion) / max(1, len([f for f in self.roster if f.champion]))
        score = self.company_pop * 1.7 + self.company_stability * 0.8 + champion_value * 0.35 + show_base + random.randint(-25, 35)
        packages = [
            ("Regional Webstream Bundle", 20, 12000),
            ("Combat Cable Package", 38, 46000),
            ("Premium Fight Network", 60, 125000),
            ("Global Sports Plus", 82, 310000),
        ]
        eligible = [package for package in packages if score >= package[1] + 45]
        if not eligible:
            self.finance["ledger"].insert(0, f"Month {self.month}: Media rights talks stalled; networks wanted stronger ratings.")
            self.inbox.append({"subject": "Media Talks Stalled", "body": "No network made a worthwhile offer.", "type": "Business", "resolved": False})
            self.refresh_all()
            return
        name, reach, base_fee = eligible[-1]
        fee = round(base_fee * (0.85 + min(0.75, self.company_pop / 140)))
        events = random.randint(5, 18)
        self.finance["media_rights"] = {"name": name, "months": random.randint(8, 24), "fee": fee, "reach": reach, "events_remaining": events}
        self.finance["ledger"].insert(0, f"Month {self.month}: Agreed media rights with {name}: ${fee:,}/event, reach +{reach}, {events} contracted events.")
        self.inbox.append({"subject": "Media Rights Deal", "body": f"{name} adds ${fee:,}/event and reach +{reach}.", "type": "Business", "resolved": False})
        self.refresh_all()

    def hire_commentator(self):
        self.ensure_finance_defaults()
        roles = ["Play-by-play", "Analyst", "Rules Expert", "Desk Host"]
        candidate = {
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "role": random.choice(roles),
            "quality": random.randint(48, 88),
            "salary": random.randint(2500, 16000),
            "chemistry": random.randint(40, 90),
        }
        signing_cost = candidate["salary"] * 2
        if self.cash < signing_cost:
            messagebox.showwarning("Not enough cash", f"Hiring {candidate['name']} requires ${signing_cost:,}.")
            return
        self.cash -= signing_cost
        self.record_finance_transaction(f"Commentator signing: {candidate['name']}", costs=signing_cost)
        self.finance["commentators"].append(candidate)
        self.finance["commentators"] = sorted(self.finance["commentators"], key=lambda c: c["quality"] + c["chemistry"], reverse=True)[:4]
        self.finance["ledger"].insert(0, f"Month {self.month} Week {self.week}: Hired commentator {candidate['name']} for ${candidate['salary']:,}/event.")
        self.inbox.append({"subject": "Commentator Hired", "body": f"{candidate['name']} joins as {candidate['role']}.", "type": "Media", "resolved": False})
        self.refresh_all()

    def refresh_rankings(self):
        self.refresh_promotion_rankings(track=False)
        if hasattr(self, "ranking_scope_box"):
            scopes = ["Worldwide", self.player_company_name] + [promo.name for promo in sorted(self.promotions, key=lambda p: p.name)] + ["Free Agents"]
            self.ranking_scope_box.configure(values=scopes)
            if self.ranking_scope.get() not in scopes:
                self.ranking_scope.set("Worldwide")
        self.rankings_tree.delete(*self.rankings_tree.get_children())
        self.ranking_tree_fighters = {}
        mode = self.ranking_filter.get() if hasattr(self, "ranking_filter") else "Pound-for-Pound"
        if mode in WEIGHTS:
            self.ranking_weight_filter.set(mode)
            self.ranking_filter.set("Division Rankings")
            mode = "Division Rankings"
        scope = self.ranking_scope.get() if hasattr(self, "ranking_scope") else "Worldwide"
        if mode == "Company Rankings":
            companies = [(self.player_company_name, self.player_region, self.player_reputation, self.company_pop, self.company_stability, self.cash, len(self.roster))]
            companies += [(p.name, p.region, p.reputation, p.reputation_score, p.stability, p.cash, len(p.roster)) for p in self.promotions]
            companies = sorted(companies, key=lambda row: self.company_power_score(row[0], self.roster if row[0] == self.player_company_name else next(p.roster for p in self.promotions if p.name == row[0]), row[3], row[4], row[5]), reverse=True)
            for rank, (name, region, rep, score, stability, cash, roster_size) in enumerate(companies, 1):
                roster = self.roster if name == self.player_company_name else next(p.roster for p in self.promotions if p.name == name)
                combined = self.company_power_score(name, roster, score, stability, cash)
                self.rankings_tree.insert("", "end", values=(rank, "-", "-", name, "-", region, rep, f"{roster_size} fighters", "-", "Company", "Promotion strength", combined, f"${cash:,}", "Active"))
            return
        rows = self.ranked_fighter_rows(scope)
        if mode == "Pound-for-Pound":
            all_rows = self.unfiltered_ranked_fighter_rows()
            p4p_scores = {id(fighter): self.p4p_value(fighter) for _company, fighter in all_rows}
            company_p4p_ranks, world_p4p_ranks = self.p4p_rank_maps(all_rows, p4p_scores)
            ranked = sorted(rows, key=lambda row: p4p_scores[id(row[1])], reverse=True)[:50]
            for _rank, (company, fighter) in enumerate(ranked, 1):
                label = self.fighter_display_name(fighter)
                fighter_key = self.fighter_identity_key(fighter)
                item_id = self.rankings_tree.insert("", "end", values=(company_p4p_ranks.get((company, fighter_key), "-"), world_p4p_ranks.get(fighter_key, "-"), self.ranking_movement_label(fighter), label, fighter.gender[0], company, fighter.weight, fighter.record, fighter.overall, self.ranking_form_label(fighter), self.title_path_label(fighter), p4p_scores[id(fighter)], fighter.last_fight, fighter.status))
                self.ranking_tree_fighters[item_id] = fighter
            return
        all_rows = self.unfiltered_ranked_fighter_rows()
        rank_scores = {id(fighter): self.rank_value(fighter) for _company, fighter in all_rows}
        company_division_ranks, world_division_ranks = self.division_rank_maps(all_rows, rank_scores)
        # A champion is the division's standing #1 and appears above every
        # numbered contender; `C` remains clearer than assigning them `#1`.
        division = sorted(
            rows,
            key=lambda row: (not row[1].champion, -rank_scores[id(row[1])]),
        )
        for company, fighter in division[:75]:
            label = self.fighter_display_name(fighter)
            fighter_key = self.fighter_identity_key(fighter)
            item_id = self.rankings_tree.insert("", "end", values=(company_division_ranks.get((company, fighter_key), "-"), world_division_ranks.get(fighter_key, "-"), self.ranking_movement_label(fighter), label, fighter.gender[0], company, fighter.weight, fighter.record, fighter.overall, self.ranking_form_label(fighter), self.title_path_label(fighter), rank_scores[id(fighter)], fighter.last_fight, fighter.status))
            self.ranking_tree_fighters[item_id] = fighter

    def ranking_movement_label(self, fighter):
        if fighter.champion:
            return "—"
        current, previous = getattr(fighter, "ranking_position", 0), getattr(fighter, "previous_ranking_position", 0)
        if not current or not previous:
            return "NEW"
        delta = previous - current
        return f"▲{delta}" if delta > 0 else f"▼{abs(delta)}" if delta < 0 else "—"

    def ranking_form_label(self, fighter):
        streak = getattr(fighter, "career_win_streak", 0)
        if fighter.champion:
            return "Champion"
        if streak >= 3:
            return f"W{streak} streak"
        if fighter.momentum >= 3:
            return "Rising"
        if fighter.momentum <= -3:
            return "Sliding"
        return "Steady"

    def title_path_label(self, fighter):
        if fighter.champion:
            origin = self.fighter_title_reign_origin(fighter, self.fighter_company_name(fighter))
            return "Appointed champion" if origin.startswith("Appointed") else "Defending champion"
        if getattr(fighter, "owed_title_shot", False):
            return "Title shot owed"
        rank = getattr(fighter, "ranking_position", 0)
        if rank == 1:
            return "Next contender"
        if rank and rank <= 5:
            return "Top-five contender"
        return getattr(fighter, "ranking_reason", "Merit ranking")

    def show_ranking_detail(self, _event=None):
        if not hasattr(self, "ranking_detail"):
            return
        selected = self.rankings_tree.selection()
        self.ranking_detail.config(state="normal"); self.ranking_detail.delete("1.0", "end")
        if selected:
            values = self.rankings_tree.item(selected[0], "values")
            fighter = getattr(self, "ranking_tree_fighters", {}).get(selected[0])
            if fighter is None and len(values) > 3:
                fighter = self.find_fighter_anywhere(self.clean_display_fighter_name(values[3]))
            if fighter:
                current = "Champion" if fighter.champion else f"#{fighter.ranking_position or '-'}"
                previous = "-" if fighter.champion else f"#{fighter.previous_ranking_position or '-'}"
                self.ranking_detail.insert("end", f"{fighter.name}: rank is driven by ELO, record quality, overall ability, activity and current form. {self.title_path_label(fighter)}. Current: {current}; previous: {previous}; rationale: {fighter.ranking_reason or 'Merit ranking'}. Double-click to open profile.")
            else:
                self.ranking_detail.insert("end", "Company rankings combine roster strength, reputation, stability, and financial power.")
        else:
            self.ranking_detail.insert("end", "Select a contender to see the ranking rationale and title path.")
        self.ranking_detail.config(state="disabled")

    def open_selected_ranking_profile(self, _event=None):
        """Open the exact fighter behind a ranking row, including duplicate names."""
        selected = self.rankings_tree.selection() if hasattr(self, "rankings_tree") else ()
        if not selected:
            return
        fighter = getattr(self, "ranking_tree_fighters", {}).get(selected[0])
        if fighter is None:
            self.open_tree_fighter_profile(self.rankings_tree, "name")
            return
        self.open_fighter_profile_window(fighter)

    def ranked_fighter_rows(self, scope):
        rows = []
        if scope in ("Worldwide", self.player_company_name):
            rows.extend((self.player_company_name, fighter) for fighter in self.roster)
        if scope in ("Worldwide", "Free Agents"):
            rows.extend(("Free Agent", fighter) for fighter in self.free_agents)
        for promo in self.promotions:
            if scope in ("Worldwide", promo.name):
                rows.extend((promo.name, fighter) for fighter in promo.roster)
        gender = self.ranking_gender_filter.get() if hasattr(self, "ranking_gender_filter") else "All"
        if gender != "All":
            rows = [(company, fighter) for company, fighter in rows if fighter.gender == gender]
        weight = self.ranking_weight_filter.get() if hasattr(self, "ranking_weight_filter") else "All"
        if weight != "All":
            rows = [(company, fighter) for company, fighter in rows if fighter.weight == weight]
        return rows

    def unfiltered_ranked_fighter_rows(self):
        rows = [(self.player_company_name, fighter) for fighter in self.roster]
        rows.extend(("Free Agent", fighter) for fighter in self.free_agents)
        for promo in self.promotions:
            rows.extend((promo.name, fighter) for fighter in promo.roster)
        gender = self.ranking_gender_filter.get() if hasattr(self, "ranking_gender_filter") else "All"
        if gender != "All":
            rows = [(company, fighter) for company, fighter in rows if fighter.gender == gender]
        weight = self.ranking_weight_filter.get() if hasattr(self, "ranking_weight_filter") else "All"
        if weight != "All":
            rows = [(company, fighter) for company, fighter in rows if fighter.weight == weight]
        return rows

    def rank_label_for_position(self, fighter, position):
        return "C" if fighter.champion else f"#{position}"

    def profile_rank_text(self, fighter, rank, scope):
        """Expand compact ranking codes into readable profile language."""
        if rank == "C":
            return f"{scope} Champion"
        if rank == "IC":
            return f"Interim {scope} Champion"
        return f"{scope} Rank {rank}"

    def division_rank_maps(self, rows=None, rank_scores=None):
        company_ranks = {}
        world_ranks = {}
        rows = rows if rows is not None else self.unfiltered_ranked_fighter_rows()
        rank_scores = rank_scores or {id(fighter): self.rank_value(fighter) for _company, fighter in rows}
        company_groups = {}
        world_groups = {}
        for company, fighter in rows:
            key = (fighter.gender, fighter.weight)
            company_groups.setdefault((company, *key), []).append(fighter)
            world_groups.setdefault(key, []).append(fighter)
        for (company, _gender, _weight), fighters in company_groups.items():
            champions = [fighter for fighter in fighters if fighter.champion]
            for fighter in champions:
                company_ranks[(company, self.fighter_identity_key(fighter))] = "C"
            contenders = sorted((fighter for fighter in fighters if not fighter.champion), key=lambda fighter: rank_scores[id(fighter)], reverse=True)
            for index, fighter in enumerate(contenders, 1):
                company_ranks[(company, self.fighter_identity_key(fighter))] = "IC" if fighter.interim_champion else f"#{index}"
        for fighters in world_groups.values():
            ordered = sorted(fighters, key=lambda fighter: rank_scores[id(fighter)], reverse=True)
            for index, fighter in enumerate(ordered, 1):
                world_ranks[self.fighter_identity_key(fighter)] = f"#{index}"
        return company_ranks, world_ranks

    def p4p_rank_maps(self, rows=None, p4p_scores=None):
        company_ranks = {}
        world_ranks = {}
        rows = rows if rows is not None else self.unfiltered_ranked_fighter_rows()
        p4p_scores = p4p_scores or {id(fighter): self.p4p_value(fighter) for _company, fighter in rows}
        company_groups = {}
        for company, fighter in rows:
            company_groups.setdefault(company, []).append(fighter)
        for company, fighters in company_groups.items():
            for index, fighter in enumerate(sorted(fighters, key=lambda fighter: p4p_scores[id(fighter)], reverse=True), 1):
                company_ranks[(company, self.fighter_identity_key(fighter))] = f"#{index}"
        for index, (_company, fighter) in enumerate(sorted(rows, key=lambda row: p4p_scores[id(row[1])], reverse=True), 1):
            world_ranks[self.fighter_identity_key(fighter)] = f"#{index}"
        return company_ranks, world_ranks

    def fighter_identity_key(self, fighter):
        return getattr(fighter, "fighter_id", "") or f"legacy-{id(fighter)}"

    def fighter_tree_row_id(self, scope, fighter, row_index=0):
        """Tree rows use durable fighter identity; display names are not unique keys."""
        identity = self.fighter_identity_key(fighter)
        return f"{scope}:{identity}:{row_index}"

    def get_fighter(self, name):
        for mapping_name in ("roster_tree_fighters", "contracts_tree_fighters", "available_tree_fighters"):
            fighter = getattr(self, mapping_name, {}).get(name)
            if fighter in self.roster:
                return fighter
        fighter = next((f for f in self.roster if f.name == name or getattr(f, "fighter_id", "") == name), None)
        if fighter:
            return fighter
        # Legacy cards stored names only. If a retirement or contract transition
        # moved an already-booked athlete out of the live roster, honour that
        # outstanding event commitment instead of crashing the card loader.
        scheduled_refs = set()
        for event in getattr(self, "scheduled_events", []):
            for fight in event.get("fights", []):
                scheduled_refs.update(self.event_fight_participants(fight))
                scheduled_refs.update(ref for ref in fight.get("fighter_ids", []) if ref)
        if name in scheduled_refs:
            retired = next((f for f in self.retired_fighters if f.name == name or getattr(f, "fighter_id", "") == name), None)
            if retired:
                self.retired_fighters.remove(retired)
                retired.retired = False
                retired.retirement_pending = True
                retired.retirement_fight_completed = False
                retired.retirement_reason = "Retirement deferred to honour an existing booked fight."
                self.roster.append(retired)
                self.inbox.append({"subject": f"Booked Fight Restored - {retired.name}", "body": f"{retired.name} was prematurely retired while still booked. They have been restored for the outstanding bout and will retire after their final scheduled commitment.", "type": "Roster", "resolved": False, "fighter_id": getattr(retired, "fighter_id", "")})
                return retired
            free_agent = next((f for f in self.free_agents if f.name == name or getattr(f, "fighter_id", "") == name), None)
            if free_agent:
                self.free_agents.remove(free_agent)
                free_agent.contract_months = max(1, int(getattr(free_agent, "contract_months", 0) or 0))
                self.roster.append(free_agent)
                self.inbox.append({"subject": f"Booked Contract Restored - {free_agent.name}", "body": f"{free_agent.name}'s existing event commitment was restored after an early roster transition.", "type": "Contracts", "resolved": False, "fighter_id": getattr(free_agent, "fighter_id", "")})
                return free_agent
        raise LookupError(f"Booked fighter reference could not be resolved: {name}")

    def add_matchup(self):
        self.set_matchmaking_notice()
        selection = self.available_tree.selection()
        if len(selection) != 2:
            messagebox.showinfo("Matchup needed", "Select exactly two available fighters.")
            return
        mapping = getattr(self, "available_tree_fighters", {})
        a, b = [mapping.get(row_id) for row_id in selection]
        if not a or not b:
            self.refresh_available()
            return
        if self.fighter_busy_message([a.name, b.name], include_draft=True):
            self.refresh_available()
            return
        if a.weight != b.weight:
            messagebox.showwarning("Weight mismatch", "Fighters must be in the same weight class.")
            return
        if self.belt_key(a.gender, a.weight) in set(getattr(self, "closed_divisions", set())):
            messagebox.showwarning("Division closed", f"{a.gender} {a.weight} is closed. Reopen it through Manage Divisions before booking fights.")
            return
        if a.gender != b.gender and not self.rules.get("allow_mixed_gender", False):
            messagebox.showwarning("Rules blocked", "Mixed-gender fights are not allowed under this promotion's current rules.")
            return
        if a.injured or b.injured:
            messagebox.showwarning("Unavailable", "Injured fighters cannot be booked.")
            return
        target_date = self.selected_booking_date(reject_past=True)
        if target_date is None:
            return
        target_month, target_week = target_date
        unavailable = [fighter for fighter in (a, b) if not self.fighter_available_for_date(fighter, target_month, target_week)]
        if unavailable:
            self.set_matchmaking_notice("Cannot add matchup: " + " | ".join(f"{fighter.name}: {self.fighter_return_label(fighter)}" for fighter in unavailable))
            self.refresh_available()
            return
        if a.fatigue >= 65 or b.fatigue >= 65:
            messagebox.showwarning("Too fatigued", "One of these fighters is carrying too much fatigue to be safely booked.")
            return
        divisional_title = bool(self.title_fight.get())
        special_belt = self.selected_special_belt_name()
        belt_error = self.special_belt_booking_error(special_belt, (a, b))
        if belt_error:
            self.set_matchmaking_notice("TITLE BOOKING BLOCKED: " + belt_error)
            return
        title = bool(divisional_title or special_belt)
        interim = self.divisional_title_is_interim((a, b), divisional_title)
        make_main = self.main_event.get() or len(self.booked) == 0
        if make_main:
            for fight in self.booked:
                fight["main"] = False
        fight = {"fighters": [a.name, b.name], "title": title, "divisional_title": divisional_title, "interim": interim, "special_belt": special_belt, "main": make_main, "tier": self.card_tier.get()}
        if make_main:
            self.booked.insert(0, fight)
        else:
            self.booked.append(fight)
        self.normalize_card_order()
        self.title_fight.set(False)
        self.special_belt_choice.set("None")
        self.main_event.set(False)
        self.refresh_available()
        self.refresh_card()

    def add_tournament_to_card(self):
        """Book a seeded, career-affecting four- or eight-fighter MMA tournament."""
        selection = list(self.available_tree.selection())
        if len(selection) not in (4, 8):
            messagebox.showinfo("MMA Tournament", "Select exactly 4 or 8 available fighters from one gender and weight division.")
            return
        mapping = getattr(self, "available_tree_fighters", {})
        fighters = [mapping.get(row_id) for row_id in selection]
        if any(fighter is None for fighter in fighters):
            self.refresh_available()
            return
        if len({fighter.weight for fighter in fighters}) != 1 or len({fighter.gender for fighter in fighters}) != 1:
            messagebox.showwarning("Invalid Tournament", "Every entrant must be in the same gender and weight division.")
            return
        if self.fighter_busy_message([fighter.name for fighter in fighters], include_draft=True):
            self.refresh_available()
            return
        target_date = self.selected_booking_date(reject_past=True)
        if target_date is None:
            return
        target_month, target_week = target_date
        blocked = [fighter for fighter in fighters if fighter.injured or fighter.fatigue >= 55 or not self.fighter_available_for_date(fighter, target_month, target_week)]
        if blocked:
            messagebox.showwarning("Entrants Unavailable", "These fighters are not tournament-ready:\n\n" + "\n".join(f"{fighter.name}: {fighter.status} / {self.fighter_return_label(fighter)}" for fighter in blocked))
            return
        seeded = sorted(fighters, key=lambda fighter: (self.division_rank_number(fighter) or 99, -fighter.elo_rating, -fighter.overall, fighter.name))
        weight, gender = seeded[0].weight, seeded[0].gender
        divisional_title = bool(self.title_fight.get())
        special_belt = self.selected_special_belt_name()
        belt_error = self.special_belt_booking_error(special_belt, seeded)
        if belt_error:
            self.set_matchmaking_notice("TITLE BOOKING BLOCKED: " + belt_error)
            return
        title = bool(divisional_title or special_belt)
        interim = self.divisional_title_is_interim(seeded, divisional_title)
        make_main = bool(self.main_event.get() or not self.booked or title)
        if make_main:
            for existing in self.booked:
                existing["main"] = False
        tournament = {
            "fighters": [seeded[0].name, seeded[-1].name], "tournament": True,
            "tournament_size": len(seeded), "tournament_entrants": [fighter.name for fighter in seeded],
            "tournament_weight": weight, "tournament_gender": gender,
            "tournament_name": f"{gender} {weight} {len(seeded)}-Fighter Grand Prix",
            "title": title, "divisional_title": divisional_title, "interim": interim, "special_belt": special_belt, "main": make_main,
            "tier": "Main Card" if make_main else self.card_tier.get(),
        }
        if make_main:
            self.booked.insert(0, tournament)
        else:
            self.booked.append(tournament)
        self.normalize_card_order()
        self.title_fight.set(False)
        self.special_belt_choice.set("None")
        self.main_event.set(False)
        self.refresh_available()
        self.refresh_card()

    def add_tba_matchup(self):
        selection = self.available_tree.selection()
        if len(selection) != 1:
            messagebox.showinfo("TBA matchup", "Select exactly one fighter to book against a TBA opponent.")
            return
        fighter = getattr(self, "available_tree_fighters", {}).get(selection[0])
        if not fighter:
            self.refresh_available()
            return
        if self.fighter_busy_message([fighter.name], include_draft=True):
            self.refresh_available()
            return
        target_date = self.selected_booking_date(reject_past=True)
        if target_date is None:
            return
        target_month, target_week = target_date
        if fighter.injured or fighter.fatigue >= 65 or not self.fighter_available_for_date(fighter, target_month, target_week):
            messagebox.showwarning("Unavailable", "That fighter is not available for a TBA booking.")
            return
        divisional_title = bool(self.title_fight.get())
        special_belt = self.selected_special_belt_name()
        belt_error = self.special_belt_booking_error(special_belt, (fighter,))
        if belt_error:
            self.set_matchmaking_notice("TITLE BOOKING BLOCKED: " + belt_error)
            return
        title = bool(divisional_title or special_belt)
        interim = self.divisional_title_is_interim((fighter,), divisional_title)
        make_main = self.main_event.get() or len(self.booked) == 0
        if make_main:
            for fight in self.booked:
                fight["main"] = False
        fight = {"fighters": [fighter.name, "TBA"], "title": title, "divisional_title": divisional_title, "interim": interim, "special_belt": special_belt, "main": make_main, "tier": self.card_tier.get(), "tba_weight": fighter.weight, "tba_gender": fighter.gender}
        if make_main:
            self.booked.insert(0, fight)
        else:
            self.booked.append(fight)
        self.normalize_card_order()
        self.title_fight.set(False)
        self.special_belt_choice.set("None")
        self.main_event.set(False)
        self.refresh_available()
        self.refresh_card()

    def remove_matchup(self):
        selected = self.card_tree.selection()
        if selected:
            self.booked.pop(int(selected[0]))
            self.normalize_card_order()
            self.refresh_available()
            self.refresh_card()

    def compare_selected_card_matchup(self):
        selected = self.card_tree.selection() if hasattr(self, "card_tree") else ()
        if not selected:
            return
        try:
            fight = self.booked[int(selected[0])]
        except (IndexError, ValueError):
            return
        if fight.get("tournament"):
            messagebox.showinfo("Compare Matchup", "Tournament rows do not have one fixed matchup yet.")
            return
        names = [name for name in fight.get("fighters", []) if name != "TBA"]
        if len(names) != 2:
            messagebox.showinfo("Compare Matchup", "Fill the TBA opponent before comparing this matchup.")
            return
        fighters = [self.get_fighter(name) for name in names]
        if any(fighter is None for fighter in fighters):
            messagebox.showinfo("Compare Matchup", "One of the fighters could not be found.")
            return
        if hasattr(self, "open_compare_fighters_window"):
            self.open_compare_fighters_window((self.player_company_name, fighters[0]), (self.player_company_name, fighters[1]))
        else:
            self.open_fighter_profile_window(fighters[0])

    def clear_card(self):
        self.booked.clear()
        self.refresh_available()
        self.refresh_card()

    def fill_selected_tba_matchup(self):
        selected = self.card_tree.selection()
        if not selected:
            messagebox.showinfo("Fill TBA", "Select a fight with a TBA opponent.")
            return
        fight = self.booked[int(selected[0])]
        if fight.get("tournament"):
            messagebox.showinfo("Tournament Field", "Tournament alternates are resolved automatically at weigh-ins.")
            return
        if "TBA" not in fight.get("fighters", []):
            messagebox.showinfo("Fill TBA", "That fight already has two named fighters.")
            return
        known = self.get_fighter(next(name for name in fight["fighters"] if name != "TBA"))
        replacement = self.find_tba_replacement(known.weight, known.gender, known=known, event=None, short_notice=False)
        if known.gender != replacement.gender and not self.rules.get("allow_mixed_gender", False):
            messagebox.showwarning("Rules blocked", "Mixed-gender fights are not allowed under this promotion's current rules.")
            return
        fight["fighters"] = [known.name, replacement.name]
        fight["tba_filled"] = True
        fight["tba_note"] = f"{replacement.name} was signed as the replacement opponent."
        divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
        fight["divisional_title"] = divisional_title
        fight["title"] = bool(divisional_title or fight.get("special_belt"))
        fight["interim"] = self.divisional_title_is_interim((known, replacement), divisional_title)
        self.news.insert(0, f"{replacement.name} has been confirmed as the TBA opponent for {known.name}.")
        self.refresh_available()
        self.refresh_market()
        self.refresh_card()

    def toggle_card_title(self):
        selected = self.card_tree.selection()
        if not selected:
            return
        fight = self.booked[int(selected[0])]
        names = [name for name in self.event_fight_participants(fight) if name != "TBA"]
        fighters = [self.get_fighter(name) for name in names]
        current_divisional = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
        fight["divisional_title"] = not current_divisional
        fight["title"] = bool(fight["divisional_title"] or fight.get("special_belt"))
        fight["interim"] = self.divisional_title_is_interim(fighters, fight["divisional_title"])
        if fight["divisional_title"] and fight["interim"]:
            self.news.insert(0, f"{' vs '.join(names)} has been marked as an interim title fight.")
        self.refresh_card()

    def assistant_pick_matchup(self):
        target_date = self.selected_booking_date(reject_past=False)
        target_month, target_week = target_date if target_date else (self.month, self.week)
        candidates = self.assistant_matchmaking_candidates(target_month, target_week)
        if not candidates:
            self.set_matchmaking_notice("ASSISTANT: No eligible matchup fits the selected date and division filters.")
            return
        score, reason, a, b, should_title = candidates[0]
        self.available_search.set("")
        self.refresh_available()
        mapping = getattr(self, "available_tree_fighters", {})
        rows = [row_id for row_id, fighter in mapping.items() if fighter is a or fighter is b]
        if len(rows) != 2:
            self.available_weight_filter.set(a.weight)
            self.available_gender_filter.set(a.gender)
            self.refresh_available()
            mapping = getattr(self, "available_tree_fighters", {})
            rows = [row_id for row_id, fighter in mapping.items() if fighter is a or fighter is b]
        if len(rows) != 2:
            self.set_matchmaking_notice("ASSISTANT: Recommendation calculated, but the current filters could not display both fighters.")
            return
        self.available_tree.selection_set(rows)
        self.available_tree.focus(rows[0])
        for row_id in rows:
            self.available_tree.see(row_id)
        self.title_fight.set(should_title)
        self.main_event.set(bool(should_title or not self.booked))
        if self.main_event.get():
            self.card_tier.set("Main Card")
        self.refresh_matchmaking_history_indicators()
        stakes = "TITLE FIGHT" if should_title else ("MAIN EVENT" if self.main_event.get() else self.card_tier.get().upper())
        self.set_matchmaking_notice(
            f"ASSISTANT PICK [{stakes}] | {a.name} vs {b.name} | Recommendation {self.assistant_recommendation_display_score(score)}/99. "
            f"{reason}. Review the comparison, then press Add Matchup to confirm."
        )

    def assistant_matchmaking_candidates(self, target_month, target_week):
        used = self.scheduled_fighter_names(include_booked=True)
        weight_filter = self.available_weight_filter.get() if hasattr(self, "available_weight_filter") else "All"
        gender_filter = self.available_gender_filter.get() if hasattr(self, "available_gender_filter") else "All"
        closed = set(getattr(self, "closed_divisions", set()))
        ready = [
            fighter for fighter in self.roster
            if fighter.name not in used
            and not fighter.retired and not getattr(fighter, "retirement_pending", False)
            and not fighter.injured and fighter.fatigue < 65
            and self.fighter_available_for_date(fighter, target_month, target_week)
            and self.belt_key(fighter.gender, fighter.weight) not in closed
            and (weight_filter == "All" or fighter.weight == weight_filter)
            and (gender_filter == "All" or fighter.gender == gender_filter)
        ]
        booked_divisions = {}
        for fight in self.booked:
            named = [self.get_fighter(name) for name in self.event_fight_participants(fight) if name != "TBA"]
            if named:
                key = (named[0].gender, named[0].weight)
                booked_divisions[key] = booked_divisions.get(key, 0) + 1
        candidates = []
        for index, a in enumerate(ready):
            for b in ready[index + 1:]:
                if a.gender != b.gender or a.weight != b.weight:
                    continue
                raw, reason = self.matchmaking_score(a, b)
                build = self.match_build_score(a, b, {"title": False, "main": False})
                division_uses = booked_divisions.get((a.gender, a.weight), 0)
                variety = 9 if division_uses == 0 else -min(24, division_uses * 8)
                activity_need = max(0, 72 - min(self.fighter_activity_rating(a), self.fighter_activity_rating(b))) * 0.12
                should_title = self.assistant_title_recommendation(a, b)
                score = raw + build * 0.22 + variety + activity_need + (16 if should_title else 0)
                context = [reason, "adds card variety" if variety > 0 else f"division already has {division_uses} booked bout(s)"]
                if activity_need >= 4:
                    context.append("addresses inactivity")
                if should_title:
                    context.append("deserving championship matchup")
                candidates.append((score, ", ".join(context), a, b, should_title))
        return sorted(candidates, key=lambda item: (item[0], item[2].popularity + item[3].popularity, item[2].overall + item[3].overall), reverse=True)

    def assistant_recommendation_display_score(self, raw_score):
        return max(1, min(99, round(10 + raw_score * 0.45)))

    def assistant_title_recommendation(self, a, b):
        if not (a.champion or b.champion):
            return False
        champion = a if a.champion else b
        contender = b if champion is a else a
        rank = self.division_rank_number(contender) or 99
        return bool(rank <= 5 or contender.owed_title_shot or contender.title_shot_clause)

    def normalize_card_order(self, fights=None):
        """Preserve visual card order: row one is always the advertised main event."""
        card = self.booked if fights is None else fights
        if not card:
            return card
        for index, fight in enumerate(card):
            fight["main"] = index == 0
            if index == 0:
                fight["tier"] = "Main Card"
                fight["card_position"] = "Main Event"
            elif index == 1 and fight.get("tier") == "Main Card":
                fight["card_position"] = "Co-Main Event"
            else:
                fight.setdefault("tier", "Prelims")
                fight.setdefault("card_position", fight["tier"])
        return card

    def move_fight_up(self):
        selected = self.card_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        if index <= 0:
            return
        self.booked[index - 1], self.booked[index] = self.booked[index], self.booked[index - 1]
        self.normalize_card_order()
        self.refresh_card()
        self.card_tree.selection_set(str(index - 1))

    def move_fight_down(self):
        selected = self.card_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        if index >= len(self.booked) - 1:
            return
        self.booked[index + 1], self.booked[index] = self.booked[index], self.booked[index + 1]
        self.normalize_card_order()
        self.refresh_card()
        self.card_tree.selection_set(str(index + 1))

    def matchmaking_score(self, a, b):
        if a is b or a.gender != b.gender or a.weight != b.weight:
            return -999, "invalid divisional pairing"
        hype = self.fight_hype(a, b, {"title": False, "main": False})
        prospect_penalty = 0
        reason_bits = []
        if (a.record_l == 0 and a.age < 26 and b.overall - a.overall > 7) or (b.record_l == 0 and b.age < 26 and a.overall - b.overall > 7):
            prospect_penalty = 35
            reason_bits.append("major prospect-risk penalty")
        if a.rival == b.name or b.rival == a.name:
            hype += 24
            reason_bits.append("existing rivalry")
        if a.champion or b.champion:
            contender = b if a.champion else a
            contender_rank = self.division_rank_number(contender) or 99
            if contender_rank <= 5:
                hype += 24 - contender_rank * 2
                reason_bits.append(f"credible #{contender_rank} title contender")
            elif contender_rank <= 10:
                hype -= 8
                reason_bits.append(f"#{contender_rank} contender needs a stronger case")
            else:
                hype -= 28
                reason_bits.append("weak championship claim")
        style_gap = abs(a.overall - b.overall)
        rank_a, rank_b = self.division_rank_number(a), self.division_rank_number(b)
        rank_alignment = max(0, 10 - abs((rank_a or 12) - (rank_b or 12)) * 1.4)
        form_alignment = max(0, 7 - abs(a.momentum - b.momentum)) * 1.5
        repeat_penalty = self.matchup_history_penalty(a, b)
        if repeat_penalty:
            reason_bits.append("repeat-pairing penalty")
        score = hype - style_gap * 1.15 - prospect_penalty + rank_alignment + form_alignment - repeat_penalty
        if not reason_bits:
            reason_bits.append("balanced divisional matchup with workable hype")
        return score, ", ".join(reason_bits)

    def media_callout_selected(self):
        selected = self.roster_tree.selection()
        if not selected:
            return
        fighter = self.get_fighter(selected[0])
        rivals = [f for f in self.roster if f.gender == fighter.gender and f.weight == fighter.weight and f.name != fighter.name]
        if not rivals:
            return
        target = max(rivals, key=lambda f: self.rank_value(f) + f.popularity)
        fighter.rival = target.name
        target.rival = fighter.name
        fighter.media_heat = min(100, fighter.media_heat + 18)
        target.media_heat = min(100, target.media_heat + 12)
        self.news.insert(0, f"{fighter.name} called out {target.name}, heating up the {fighter.weight} division.")
        messagebox.showinfo("Media Callout", f"{fighter.name} called out {target.name}.")
        self.refresh_all()

    def open_detailed_skills_selected(self):
        selected = self.roster_tree.selection()
        if not selected:
            return
        self.open_detailed_skills(self.get_fighter(selected[0]))

    def choose_camp_focus_selected(self):
        selected = self.roster_tree.selection()
        if not selected:
            messagebox.showinfo("Camp Plan", "Select a fighter first.")
            return
        fighter = self.get_fighter(selected[0])
        self.open_fighter_camp_plan(fighter)

    def open_fighter_camp_plan(self, fighter, on_save=None):
        window = tk.Toplevel(self.root)
        window.title(f"Camp Plan - {fighter.name}")
        window.geometry("460x410")
        window.resizable(False, False)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"CAMP PLAN: {fighter.name.upper()}", style="ScreenTitle.TLabel").pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(window, text="Choose the gym, focus, and workload for the next scheduled camp. Hard camps improve preparation but add injury and fatigue risk.", wraplength=420, style="Chrome.TLabel").pack(fill="x", padx=14, pady=(0, 8))
        choice = tk.StringVar(value=getattr(fighter, "camp_focus", "Balanced"))
        gym_choice = tk.StringVar(value=fighter.camp)
        intensity_choice = tk.StringVar(value=getattr(fighter, "camp_intensity", "Standard"))
        controls = ttk.Frame(window, style="Panel.TFrame")
        controls.pack(fill="x", padx=10, pady=4)
        ttk.Label(controls, text="Gym", style="Panel.TLabel").pack(side="left", padx=(8, 4))
        ttk.Combobox(controls, textvariable=gym_choice, values=[gym.name for gym in self.gyms], state="readonly", width=27).pack(side="left", padx=4)
        intensity_row = ttk.Frame(window, style="Panel.TFrame")
        intensity_row.pack(fill="x", padx=10, pady=2)
        ttk.Label(intensity_row, text="Workload", style="Panel.TLabel").pack(side="left", padx=(8, 8))
        for intensity in ("Light", "Standard", "Hard"):
            ttk.Radiobutton(intensity_row, text=intensity, value=intensity, variable=intensity_choice).pack(side="left", padx=5)
        options = ["Balanced", "Striking", "Wrestling", "Grappling", "Conditioning", "Game Plan", "Weight Management"]
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=4)
        for option in options:
            ttk.Radiobutton(body, text=option, value=option, variable=choice).pack(anchor="w", padx=12, pady=3)
        def save():
            fighter.camp_focus = choice.get()
            fighter.camp = gym_choice.get()
            fighter.camp_intensity = intensity_choice.get()
            self.news.insert(0, f"Camp plan: {fighter.name} joins {fighter.camp} for a {fighter.camp_intensity.lower()} {fighter.camp_focus.lower()} camp.")
            self.refresh_all()
            if on_save:
                on_save()
            window.destroy()
        ttk.Button(window, text="Set Camp Focus", style="Accent.TButton", command=save).pack(pady=10)

    def open_detailed_skills(self, fighter):
        self.ensure_detailed_skills(fighter)
        window = tk.Toplevel(self.root)
        window.title(f"Detailed Skills - {fighter.name}")
        window.geometry("760x620")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"{fighter.name.upper()} - DETAILED SKILLS", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        for group, keys in DETAILED_SKILL_GROUPS.items():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=group)
            canvas = tk.Canvas(tab, bg=self.colors["cream"], highlightthickness=0)
            scroll = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            inner = ttk.Frame(canvas, style="Inset.TFrame")
            inner.bind("<Configure>", lambda _e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scroll.set)
            canvas.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            for key in keys:
                row = ttk.Frame(inner, style="Inset.TFrame")
                row.pack(fill="x", padx=18, pady=4)
                label = key.replace("_", " ").title()
                value = fighter.detailed_skills.get(key, 50)
                ttk.Label(row, text=label, width=24, style="Inset.TLabel").pack(side="left")
                bar = ttk.Progressbar(row, maximum=100, length=300)
                bar.configure(value=value)
                bar.pack(side="left", padx=8)
                ttk.Label(row, text=f"{value:.1f}%", width=8, style="Inset.TLabel").pack(side="left")
        ttk.Button(window, text="Close", command=window.destroy).pack(anchor="e", padx=8, pady=(0, 8))

    def ensure_detailed_skills(self, fighter):
        if not fighter.detailed_skills:
            self.generate_detailed_skills(fighter)
            self.sync_broad_skills_from_details(fighter)

    def build_editor_form(self, parent, fields):
        for index, (label, key, kind) in enumerate(fields):
            row, column = divmod(index, 3)
            base_column = column * 2
            ttk.Label(parent, text=label, style="Inset.TLabel").grid(row=row, column=base_column, sticky="w", padx=(10, 3), pady=7)
            variable = self.editor_vars[key]
            if kind == "entry":
                widget = ttk.Entry(parent, textvariable=variable, width=19)
            elif kind == "owner":
                widget = ttk.Combobox(parent, textvariable=variable, width=24, state="readonly")
                self.editor_owner_box = widget
            elif kind.startswith("combo:"):
                widget = ttk.Combobox(parent, textvariable=variable, values=kind.split(":", 1)[1].split("|"), width=18, state="readonly")
            elif kind.startswith("spin:"):
                low, high = kind.split(":", 1)[1].split(":")
                widget = ttk.Spinbox(parent, from_=int(low), to=int(high), textvariable=variable, width=10)
            else:
                widget = ttk.Entry(parent, textvariable=variable, width=18)
            widget.grid(row=row, column=base_column + 1, sticky="ew", padx=(0, 10), pady=7)
            parent.grid_columnconfigure(base_column + 1, weight=1)

    def database_editor_owner_names(self):
        return ["Free Agent", self.player_company_name] + [promo.name for promo in sorted(self.promotions, key=lambda item: item.name)]

    def database_editor_rows(self):
        rows = [(self.player_company_name, fighter) for fighter in self.roster]
        rows.extend(("Free Agent", fighter) for fighter in self.free_agents)
        for promotion in self.promotions:
            rows.extend((promotion.name, fighter) for fighter in promotion.roster)
        return rows

    def schedule_database_editor_refresh(self, delay=150):
        """Debounce dense editor filters and ignore changes while the page is hidden."""
        pending = getattr(self, "_editor_refresh_after", None)
        if pending:
            try:
                self.root.after_cancel(pending)
            except tk.TclError:
                pass
        self._editor_refresh_after = None
        if getattr(self, "current_tab_name", "") != "editor":
            return

        def run():
            self._editor_refresh_after = None
            self.refresh_database_editor()

        self._editor_refresh_after = self.root.after(max(1, int(delay)), run)

    def refresh_database_editor(self):
        if getattr(self, "_refreshing_database_editor", False):
            return
        self._refreshing_database_editor = True
        try:
            self._refresh_database_editor_now()
        finally:
            self._refreshing_database_editor = False

    def refresh_editor_scope_banner(self):
        if hasattr(self, "editor_career_target_var"):
            company = getattr(self, "player_company_name", "No company")
            slot = getattr(self, "active_save_name", "Unsaved Session")
            self.editor_career_target_var.set(f"Career: {slot} | {company}")
        if hasattr(self, "editor_database_target_var"):
            try:
                pack = self.active_universe_database_path().name
            except Exception:
                pack = "No starting pack selected"
            self.editor_database_target_var.set(f"Pack: {pack}")
        if hasattr(self, "editor_edit_state_var"):
            state = "Editor changes pending career save" if getattr(self, "editor_current_dirty", False) else "No pending editor changes"
            self.editor_edit_state_var.set(state)

    def save_editor_career_now(self):
        if self.save_game():
            self.editor_current_dirty = False
            self.refresh_editor_scope_banner()

    def _refresh_database_editor_now(self):
        if not hasattr(self, "editor_tree"):
            return
        self.refresh_editor_scope_banner()
        owners = self.database_editor_owner_names()
        if hasattr(self, "editor_company_combo"):
            self.editor_company_combo.configure(values=["All"] + owners)
        if hasattr(self, "editor_owner_box"):
            self.editor_owner_box.configure(values=owners)
        if self.editor_company_filter.get() not in (["All"] + owners):
            self.editor_company_filter.set("All")
        selected_fighter = getattr(self, "editor_selected_fighter", None)
        search = self.editor_search.get().strip().lower()
        owner_filter = self.editor_company_filter.get()
        weight_filter = self.editor_weight_filter.get()
        gender_filter = self.editor_gender_filter.get()
        self.editor_tree.delete(*self.editor_tree.get_children())
        self.editor_row_map = {}
        rows = []
        for owner, fighter in self.database_editor_rows():
            if owner_filter != "All" and owner != owner_filter:
                continue
            if weight_filter != "All" and fighter.weight != weight_filter:
                continue
            if gender_filter != "All" and fighter.gender != gender_filter:
                continue
            haystack = f"{fighter.name} {owner} {fighter.nationality} {fighter.style} {fighter.trait}".lower()
            if search and search not in haystack:
                continue
            rows.append((owner, fighter))
        for index, (owner, fighter) in enumerate(sorted(rows, key=lambda item: (item[0], item[1].weight, item[1].gender, item[1].name))):
            item_id = f"editor:{index}:{fighter.name}"
            self.editor_row_map[item_id] = (owner, fighter)
            self.editor_tree.insert("", "end", iid=item_id, values=(owner, fighter.name, fighter.gender[:1], fighter.weight, fighter.age, fighter.overall, fighter.potential, fighter.popularity, fighter.record, fighter.status))
            if fighter is selected_fighter:
                self.editor_tree.selection_set(item_id)
                self.editor_tree.see(item_id)

    def load_selected_editor_fighter(self):
        selected = self.editor_tree.selection() if hasattr(self, "editor_tree") else ()
        if not selected:
            return
        owner, fighter = self.editor_row_map.get(selected[0], (None, None))
        if not fighter:
            return
        self.editor_selected_fighter = fighter
        self.editor_selected_owner = owner
        self.ensure_detailed_skills(fighter)
        values = {
            "name": fighter.name, "gender": fighter.gender, "weight": fighter.weight, "region": fighter.region,
            "nationality": fighter.nationality, "style": fighter.style, "stance": fighter.stance, "trait": fighter.trait,
            "behaviour": fighter.behaviour, "camp": fighter.camp, "age": fighter.age, "record_w": fighter.record_w,
            "record_l": fighter.record_l, "record_d": fighter.record_d, "striking": fighter.striking,
            "wrestling": fighter.wrestling, "grappling": fighter.grappling, "cardio": fighter.cardio, "chin": fighter.chin,
            "power": fighter.power, "takedown_defence": fighter.takedown_defence, "ground_control": fighter.ground_control,
            "submissions": fighter.submissions, "submission_defence": fighter.submission_defence, "recovery": fighter.recovery,
            "toughness": fighter.toughness, "fight_iq": fighter.fight_iq, "potential": fighter.potential,
            "popularity": fighter.popularity, "momentum": fighter.momentum, "morale": fighter.morale, "purse": fighter.purse,
            "contract_months": fighter.contract_months, "fatigue": fighter.fatigue, "injured": fighter.injured,
            "motivation": fighter.motivation, "professionalism": fighter.professionalism, "media_presence": fighter.media_presence, "star_quality": fighter.star_quality,
            "height": fighter.height, "rival": fighter.rival, "friend": fighter.friend, "career_archetype": fighter.career_archetype, "prime_start": fighter.prime_start, "prime_end": fighter.prime_end, "walk_weight": fighter.walk_weight, "weight_cut_penalty": fighter.weight_cut_penalty, "injury_proneness": fighter.injury_proneness, "finishing_instinct": fighter.finishing_instinct, "charisma": fighter.charisma, "sponsor_appeal": fighter.sponsor_appeal, "media_heat": fighter.media_heat, "elo_rating": fighter.elo_rating, "rank_score": fighter.rank_score, "title_wins": fighter.title_wins, "title_defenses": fighter.title_defenses, "award_count": fighter.award_count, "win_bonus": fighter.win_bonus, "ppv_points": fighter.ppv_points, "relationship_trust": fighter.relationship_trust, "champions_clause": fighter.champions_clause, "title_shot_clause": fighter.title_shot_clause, "main_event_promise": fighter.main_event_promise, "top_opponent_promise": fighter.top_opponent_promise,
            "owner": owner, "contract_type": fighter.contract_type, "exclusive": fighter.exclusive,
            "champion": fighter.champion, "interim_champion": fighter.interim_champion,
        }
        for key, value in values.items():
            self.editor_vars[key].set(value)

    def new_database_editor_fighter(self):
        self.editor_selected_fighter = None
        self.editor_selected_owner = ""
        defaults = {
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}", "gender": "Male", "weight": "Lightweight",
            "region": "USA", "nationality": "American", "style": "Well-Rounded", "stance": "Orthodox",
            "trait": "Gym Rat", "behaviour": "Dynamic Attacker", "camp": "Independent", "age": 24,
            "record_w": 0, "record_l": 0, "record_d": 0, "striking": 65, "wrestling": 65, "grappling": 65,
            "cardio": 65, "chin": 65, "power": 65, "takedown_defence": 65, "ground_control": 65,
            "submissions": 65, "submission_defence": 65, "recovery": 65, "toughness": 65, "fight_iq": 65,
            "potential": 70, "popularity": 15, "momentum": 0, "morale": 70, "purse": 8000,
            "contract_months": 0, "fatigue": 0, "injured": 0, "owner": "Free Agent", "contract_type": "Non-Exclusive",
            "exclusive": False, "champion": False, "interim_champion": False, "height": "", "rival": "", "friend": "", "career_archetype": "Balanced Development", "prime_start": 25, "prime_end": 33, "walk_weight": 0, "weight_cut_penalty": 0, "injury_proneness": 20, "finishing_instinct": 50, "charisma": 50, "sponsor_appeal": 50, "media_heat": 0, "elo_rating": 1500, "rank_score": 0, "title_wins": 0, "title_defenses": 0, "award_count": 0, "win_bonus": 0, "ppv_points": 0, "relationship_trust": 55, "champions_clause": False, "title_shot_clause": False, "main_event_promise": False, "top_opponent_promise": False,
        }
        for key, value in defaults.items():
            self.editor_vars[key].set(value)
        if hasattr(self, "editor_tree"):
            selected = self.editor_tree.selection()
            if selected:
                self.editor_tree.selection_remove(*selected)

    def editor_target_roster(self, owner):
        if owner == "Free Agent":
            return self.free_agents
        if owner == self.player_company_name:
            return self.roster
        promotion = next((item for item in self.promotions if item.name == owner), None)
        return promotion.roster if promotion else None

    def remove_fighter_from_active_database(self, fighter):
        for roster in [self.roster, self.free_agents] + [promotion.roster for promotion in self.promotions]:
            if fighter in roster:
                roster.remove(fighter)

    def editor_shift_detailed_rating(self, fighter, keys, target):
        if not keys:
            return
        current = round(sum(fighter.detailed_skills.get(key, 50) for key in keys) / len(keys))
        adjustment = int(target) - current
        for key in keys:
            fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills.get(key, 50) + adjustment))

    def apply_editor_combat_ratings(self, fighter):
        self.ensure_detailed_skills(fighter)
        mapping = [
            (STANDING_SKILLS, "striking"), (WRESTLING_SKILLS, "wrestling"), (GROUND_SKILLS, "grappling"),
            (("conditioning", "resilience", "dedication"), "cardio"),
            (("chin_strength", "stun_recovery", "resilience"), "chin"),
            (("punch_power", "high_kick_power", "strength"), "power"),
            (("takedown_defence_detail", "sprawl", "get_ups"), "takedown_defence"),
            (("top_control", "positional_ability", "ride_control"), "ground_control"),
            (("submission_attack", "leg_locks", "back_control"), "submissions"),
            (("submission_defence_detail", "guard_work"), "submission_defence"),
            (("stun_recovery", "composure"), "recovery"), (("resilience", "chin_strength"), "toughness"),
            (("adaptability", "composure", "discipline"), "fight_iq"),
        ]
        for keys, variable in mapping:
            self.editor_shift_detailed_rating(fighter, keys, self.editor_vars[variable].get())
        self.sync_broad_skills_from_details(fighter)

    def editor_replace_name_references(self, old_name, new_name):
        if old_name == new_name:
            return
        all_fighters = [fighter for _owner, fighter in self.database_editor_rows()] + list(self.retired_fighters)
        for fighter in all_fighters:
            if fighter.rival == old_name:
                fighter.rival = new_name
            if fighter.friend == old_name:
                fighter.friend = new_name
        for fight in self.booked:
            fight["fighters"] = [new_name if name == old_name else name for name in fight.get("fighters", [])]
        for event in self.scheduled_events:
            for fight in event.get("fights", []):
                fight["fighters"] = [new_name if name == old_name else name for name in fight.get("fighters", [])]
        for belts in (self.belts, self.interim_belts):
            for key, holder in belts.items():
                if holder == old_name:
                    belts[key] = new_name
        for promotion in self.promotions:
            for belts in (promotion.belts or {}, promotion.interim_belts or {}):
                for key, holder in belts.items():
                    if holder == old_name:
                        belts[key] = new_name

    def save_database_editor_fighter(self):
        name = self.editor_vars["name"].get().strip()
        owner = self.editor_vars["owner"].get()
        if not name:
            messagebox.showwarning("Current Career Editor", "A fighter needs a name.")
            return
        target = self.editor_target_roster(owner)
        if target is None:
            messagebox.showwarning("Current Career Editor", "Choose a valid employer.")
            return
        fighter = self.editor_selected_fighter
        duplicates = [candidate for _owner, candidate in self.database_editor_rows() if candidate.name == name and candidate is not fighter]
        if duplicates:
            messagebox.showwarning("Current Career Editor", f"{name} already exists in this career.")
            return
        is_new = fighter is None
        if is_new:
            fighter = Fighter(name=name, weight=self.editor_vars["weight"].get(), age=self.editor_vars["age"].get(), record_w=0, record_l=0, striking=65, wrestling=65, grappling=65, cardio=65, chin=65, popularity=15, momentum=0, morale=70, purse=8000)
            self.enrich_fighter(fighter, player_owned=owner == self.player_company_name)
        old_name = fighter.name
        for key in ("name", "gender", "weight", "region", "nationality", "style", "stance", "trait", "behaviour", "camp", "age", "record_w", "record_l", "record_d", "popularity", "momentum", "morale", "potential", "purse", "contract_months", "fatigue", "injured", "contract_type", "exclusive", "champion", "interim_champion", "motivation", "professionalism", "media_presence", "star_quality", "height", "rival", "friend", "career_archetype", "prime_start", "prime_end", "walk_weight", "weight_cut_penalty", "injury_proneness", "finishing_instinct", "charisma", "sponsor_appeal", "media_heat", "elo_rating", "rank_score", "title_wins", "title_defenses", "award_count", "win_bonus", "ppv_points", "relationship_trust", "champions_clause", "title_shot_clause", "main_event_promise", "top_opponent_promise"):
            value = self.editor_vars[key].get()
            setattr(fighter, key, value)
        self.apply_editor_combat_ratings(fighter)
        fighter.rank_score = self.rank_value(fighter)
        if is_new:
            target.append(fighter)
        elif fighter not in target:
            self.remove_fighter_from_active_database(fighter)
            target.append(fighter)
        self.editor_replace_name_references(old_name, fighter.name)
        self.editor_selected_fighter = fighter
        self.editor_selected_owner = owner
        self.editor_current_dirty = True
        self.refresh_editor_scope_banner()
        self.ensure_all_company_champions()
        self.news.insert(0, f"World editor {'created' if is_new else 'updated'} {fighter.name} in the current career ({owner}).")
        self.refresh_all()
        self.load_selected_editor_fighter()

    def open_editor_selected_profile(self):
        fighter = getattr(self, "editor_selected_fighter", None)
        if fighter:
            self.open_fighter_profile_window(fighter)
        else:
            messagebox.showinfo("Current Career Editor", "Select a fighter first.")

    def retire_database_editor_fighter(self):
        fighter = getattr(self, "editor_selected_fighter", None)
        if not fighter:
            messagebox.showinfo("Current Career Editor", "Select a fighter first.")
            return
        if not messagebox.askyesno("Retire Fighter", f"Retire {fighter.name} in the current career?"):
            return
        self.remove_fighter_from_active_database(fighter)
        fighter.retired = True
        fighter.retirement_reason = "World editor"
        fighter.champion = False
        fighter.interim_champion = False
        if fighter not in self.retired_fighters:
            self.retired_fighters.insert(0, fighter)
        self.editor_selected_fighter = None
        self.editor_current_dirty = True
        self.refresh_editor_scope_banner()
        self.ensure_all_company_champions()
        self.news.insert(0, f"World editor retired {fighter.name} in the current career.")
        self.refresh_all()

    def open_detailed_skill_editor(self):
        fighter = getattr(self, "editor_selected_fighter", None)
        if not fighter:
            messagebox.showinfo("Detailed Skill Editor", "Select a fighter first.")
            return
        self.ensure_detailed_skills(fighter)
        window = tk.Toplevel(self.root)
        window.title(f"Detailed Skill Editor - {fighter.name}")
        window.geometry("760x650")
        window.minsize(680, 520)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"{fighter.name.upper()} - FIGHT ATTRIBUTES", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        skill_vars = {key: tk.IntVar(value=round(fighter.detailed_skills.get(key, 50))) for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
        for group, keys in DETAILED_SKILL_GROUPS.items():
            tab = ttk.Frame(notebook, style="Inset.TFrame")
            notebook.add(tab, text=group)
            for index, key in enumerate(keys):
                row, column = divmod(index, 2)
                ttk.Label(tab, text=key.replace("_", " ").title(), style="Inset.TLabel").grid(row=row, column=column * 2, sticky="w", padx=(12, 4), pady=7)
                ttk.Spinbox(tab, from_=1, to=99, textvariable=skill_vars[key], width=7).grid(row=row, column=column * 2 + 1, sticky="w", padx=(0, 12), pady=7)
        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        def save_details():
            fighter.detailed_skills = {key: max(1, min(99, variable.get())) for key, variable in skill_vars.items()}
            self.sync_broad_skills_from_details(fighter)
            fighter.rank_score = self.rank_value(fighter)
            self.editor_current_dirty = True
            self.refresh_editor_scope_banner()
            self.refresh_all()
            window.destroy()
        ttk.Button(footer, text="Save Detailed Ratings", style="Accent.TButton", command=save_details).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4)

    def randomize_editor_fighter(self):
        self.new_database_editor_fighter()
        base = random.randint(42, 86)
        self.editor_vars["name"].set(f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}")
        self.editor_vars["weight"].set(random.choice(WEIGHTS))
        self.editor_vars["region"].set(random.choice(REGIONS))
        self.editor_vars["style"].set(random.choice(STYLES))
        self.editor_vars["trait"].set(random.choice(TRAITS))
        self.editor_vars["camp"].set(random.choice(CAMPS))
        self.editor_vars["age"].set(random.randint(19, 38))
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "takedown_defence", "ground_control", "submissions", "submission_defence", "recovery", "toughness", "fight_iq"):
            self.editor_vars[key].set(max(25, min(99, base + random.randint(-8, 8))))
        self.editor_vars["popularity"].set(random.randint(4, 55))
        self.editor_vars["purse"].set(random.randint(4000, 45000))

    def create_custom_fighter(self, add_to_roster):
        self.new_database_editor_fighter()
        self.editor_vars["owner"].set(self.player_company_name if add_to_roster else "Free Agent")
        self.editor_vars["exclusive"].set(add_to_roster)
        self.editor_vars["contract_type"].set("Exclusive" if add_to_roster else "Non-Exclusive")
        self.editor_vars["contract_months"].set(12 if add_to_roster else 0)
        self.save_database_editor_fighter()
