import json
import math
import random
import sys
import time
import unicodedata
import traceback
from functools import lru_cache
from datetime import datetime
from uuid import uuid4
import tkinter as tk
from dataclasses import asdict, dataclass
from copy import deepcopy
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from constants import *
from models import Fighter, Gym, Promotion
from play_level_audit import (
    AuditCheckpointError,
    audit_balance_findings,
    audit_hard_invariant_findings,
    audit_measurement_evidence_findings,
    build_audit_identity,
    build_calendar_timing_measurement,
    build_audit_measurement,
    build_audit_report_accounting,
    decode_rng_state,
    make_checkpoint,
    read_checkpoint,
    validate_checkpoint,
    write_checkpoint_atomic,
)


def _audit_collection_count(value):
    """Return a defensive count for audit-only collection/counter fields.

    Combat-sport world records use an integer event counter in the live save,
    while older fixtures and some read models retain an event list.  The
    play-audit report is observational and must accept both shapes (and fail
    closed for malformed values) instead of crashing at the first yearly
    boundary.
    """
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        try:
            return max(0, int(value))
        except (TypeError, ValueError, OverflowError):
            return 0
    if isinstance(value, (str, bytes)):
        return 0
    try:
        return max(0, len(value))
    except (TypeError, ValueError, OverflowError):
        return 0


# Play-level audits run the complete weekly world loop, so an accidental
# multi-day request should never monopolise the desktop.  The limit is a
# presentation/control value only; it does not change the simulated world or
# the deterministic seed.  A stopped run keeps a safe weekly checkpoint and
# can be resumed explicitly.
PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS = 300
PLAY_AUDIT_MIN_TIME_LIMIT_SECONDS = 30
PLAY_AUDIT_MAX_TIME_LIMIT_SECONDS = 1_800


class AdminMixin:
    def _simulation_status_notice(self, message, *, warning=False, tournament=False):
        """Keep Simulation Lab guidance beside the tool that needs attention."""
        if tournament:
            report = getattr(self, "sim_tournament_report", None)
            if report is not None:
                self.write_sim_tournament_report(str(message))
                return True
        result = getattr(self, "sim_result", None)
        if result is not None:
            try:
                result.configure(text=str(message))
                return True
            except (tk.TclError, AttributeError):
                pass
        return False

    def update_sim_company_balance_display(self):
        """Keep the Sim Lab's controlled-company cash readout current."""
        if not hasattr(self, "sim_balance_label"):
            return
        if getattr(self, "spectator_mode", False):
            self.sim_balance_label.config(text="Spectator mode\nNo controlled company")
            if hasattr(self, "sim_balance_edit_button"):
                self.sim_balance_edit_button.config(state="disabled")
            return
        self.sim_balance_label.config(
            text=f"{self.player_company_name}\nCurrent balance: ${self.cash:,.0f}"
        )
        if hasattr(self, "sim_balance_edit_button"):
            self.sim_balance_edit_button.config(state="normal")

    def edit_sim_company_balance(self):
        """Set the controlled company's cash for a deliberate sandbox scenario."""
        if getattr(self, "spectator_mode", False):
            if not self._simulation_status_notice("Take control of a promotion before editing a company balance.", warning=True):
                messagebox.showinfo("Company Balance", "Take control of a promotion before editing a company balance.")
            return
        current_balance = max(0, round(self.cash))
        updated_balance = simpledialog.askinteger(
            "Edit Company Balance",
            f"Set the cash balance for {self.player_company_name}:\n\nCurrent balance: ${current_balance:,}",
            initialvalue=current_balance,
            minvalue=0,
            parent=self.root,
        )
        if updated_balance is None:
            return
        updated_balance = int(updated_balance)
        if updated_balance == current_balance:
            return

        change = updated_balance - current_balance
        self.cash = updated_balance
        self.ensure_finance_defaults()
        self.record_finance_transaction(
            "Simulation Lab balance adjustment",
            revenue=max(0, change),
            costs=max(0, -change),
        )
        self.finance["ledger"].insert(
            0,
            f"Month {self.month} Week {self.week}: Simulation Lab balance adjusted from ${current_balance:,} to ${updated_balance:,}.",
        )
        self.finance["ledger"] = self.finance["ledger"][:80]
        self.close_finance_week()
        self.news.insert(0, f"Simulation Lab: {self.player_company_name} balance adjusted to ${updated_balance:,}.")
        self.update_sim_company_balance_display()
        self.refresh_all()

    def apply_engine_settings(self):
        for key, var in self.engine_vars.items():
            minimum, maximum = FIGHT_ENGINE_SETTING_BOUNDS[key]
            self.engine_settings[key] = round(max(minimum, min(maximum, var.get())), 2)
        if hasattr(self, "gate_multiplier_var"):
            minimum, maximum = BUSINESS_SIMULATION_SETTING_BOUNDS["gate_multiplier"]
            self.business_settings["gate_multiplier"] = round(
                max(minimum, min(maximum, self.gate_multiplier_var.get())), 2
            )
        self.inbox.append({"subject": "Simulation Settings Updated", "body": f"Fight mechanics: {self.engine_settings}; business simulation: {self.business_settings}", "type": "Rules", "resolved": False})
        self.refresh_all()

    def reset_engine_settings(self):
        self.engine_settings = self.seed_engine_settings()
        self.business_settings = self.seed_business_settings()
        for key, var in self.engine_vars.items():
            var.set(self.engine_settings[key])
        if hasattr(self, "gate_multiplier_var"):
            self.gate_multiplier_var.set(self.business_settings["gate_multiplier"])
        self.refresh_all()

    @staticmethod
    def sim_generation_choice(value, minimum, maximum):
        value = str(value or "Random").strip()
        if value.lower() == "random":
            return None
        try:
            return max(minimum, min(maximum, int(value)))
        except (TypeError, ValueError):
            return None

    def set_generated_fighter_ability(self, fighter, target):
        """Move a generated profile to a requested OVR without flattening its style."""
        self.ensure_detailed_skills(fighter)
        for _ in range(5):
            adjustment = int(target) - fighter.overall
            if not adjustment:
                break
            fighter.detailed_skills = {
                key: max(1, min(99, value + adjustment))
                for key, value in fighter.detailed_skills.items()
            }
            self.sync_broad_skills_from_details(fighter)
        if fighter.overall != target:
            adjustment = 1 if fighter.overall < target else -1
            for key in fighter.detailed_skills:
                if fighter.overall == target:
                    break
                fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills[key] + adjustment))
                self.sync_broad_skills_from_details(fighter)

    def create_sim_lab_free_agents(self, count, age=None, ability=None, gender=None, weight=None):
        """Create emergency population directly in the current save's FA market."""
        count = max(1, min(2000, int(count)))
        age = None if age is None else max(16, min(60, int(age)))
        ability = None if ability is None else max(30, min(99, int(ability)))
        gender = gender if gender in ("Male", "Female") else None
        weight = weight if weight in WEIGHTS else None
        existing_names = self.active_fighter_names()
        created = []
        current_year = 2026 + (max(1, int(getattr(self, "month", 1))) - 1) // 12
        for _ in range(count):
            fighter = self.create_generated_fighter(
                2, 28,
                ability if ability is not None else 38,
                ability if ability is not None else 84,
                weight=weight,
                gender=gender,
                apply_entry_balance=ability is None,
                age_override=max(18, age) if age is not None else None,
                pre_universe=False,
            )
            self.avoid_name_collision(fighter, existing_names)
            if age is not None:
                fighter.age = age
            if ability is not None:
                self.set_generated_fighter_ability(fighter, ability)
            fighter.record_w = fighter.record_l = fighter.record_d = 0
            fighter.record_history_baseline_w = fighter.record_history_baseline_l = fighter.record_history_baseline_d = 0
            fighter.multi_sport_records = {"MMA": "0-0-0"}
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.free_agent_months = 0
            fighter.ai_offer_company = ""
            fighter.ai_offer_months = 0
            fighter.ai_offer_purse = 0
            fighter.ai_offer_signing_bonus = 0
            fighter.market_origin = "Simulation Lab population tool"
            fighter.available_week = self.calendar_week_index()
            fighter.retired = False
            fighter.retirement_pending = False
            fighter.fight_history = []
            fighter.bout_rating_history = []
            fighter.annual_overalls = {str(current_year): fighter.overall}
            fighter.potential = max(fighter.overall, min(99, fighter.potential))
            fighter.rank_score = self.rank_value(fighter)
            self.free_agents.append(fighter)
            created.append(fighter)
        return created

    def generate_sim_lab_free_agents(self):
        try:
            count = max(1, min(2000, int(self.sim_generate_count.get())))
        except (TypeError, ValueError, tk.TclError):
            count = 1
            self.sim_generate_count.set(count)
        age = self.sim_generation_choice(self.sim_generate_age.get(), 16, 60)
        ability = self.sim_generation_choice(self.sim_generate_ability.get(), 30, 99)
        gender = self.sim_generate_gender.get()
        weight = self.sim_generate_weight.get()
        created = self.create_sim_lab_free_agents(count, age, ability, gender, weight)
        male = sum(fighter.gender == "Male" for fighter in created)
        female = len(created) - male
        ability_range = f"OVR {min(f.overall for f in created)}-{max(f.overall for f in created)}"
        summary = f"Added {len(created)} free agents ({male} M / {female} F), {ability_range}. Market total: {len(self.free_agents)}."
        if hasattr(self, "sim_generate_status"):
            self.sim_generate_status.config(text=summary)
        self.news.insert(0, f"Simulation Lab population tool: {summary}")
        self.refresh_sim_fighter_choices()
        if getattr(self, "current_screen", "") == "market":
            self.refresh_market()

    def all_database_fighters(self, include_retired=False):
        fighters = {}
        for fighter in self.roster:
            fighters.setdefault(self.fighter_identity_key(fighter), fighter)
        for fighter in self.free_agents:
            fighters.setdefault(self.fighter_identity_key(fighter), fighter)
        for promo in self.promotions:
            for fighter in promo.roster:
                fighters.setdefault(self.fighter_identity_key(fighter), fighter)
        if include_retired:
            for fighter in self.retired_fighters:
                fighters.setdefault(self.fighter_identity_key(fighter), fighter)
        return sorted(fighters.values(), key=lambda fighter: (fighter.weight, fighter.gender, fighter.name))

    def refresh_sim_fighter_choices(self):
        self.update_sim_company_balance_display()
        if not hasattr(self, "sim_combo_a"):
            return
        fighters = self.sim_filtered_fighters()
        prior_a = self.selected_sim_fighter("a")
        prior_b = self.selected_sim_fighter("b")
        name_counts = {}
        for fighter in fighters:
            name_counts[fighter.name] = name_counts.get(fighter.name, 0) + 1
        choices = []
        self._sim_fighter_choice_rows = {}
        used_choice_labels = set()
        for fighter in fighters:
            label = fighter.name
            if name_counts.get(fighter.name, 0) > 1:
                identity = str(getattr(fighter, "fighter_id", "") or self.fighter_identity_key(fighter)).strip()
                label = f"{fighter.name} — {fighter.gender} {fighter.weight} ({identity})"
            suffix = 2
            base_label = label
            while label in used_choice_labels:
                label = f"{base_label} #{suffix}"
                suffix += 1
            used_choice_labels.add(label)
            choices.append(label)
            self._sim_fighter_choice_rows[label] = fighter
        self.sim_combo_a.configure(values=choices)
        self.sim_combo_b.configure(values=choices)
        def label_for(source, excluded=()):
            if source is not None:
                for label, candidate in self._sim_fighter_choice_rows.items():
                    if candidate is source and label not in excluded:
                        return label
                identity = self.fighter_identity_key(source)
                matches = [label for label, candidate in self._sim_fighter_choice_rows.items()
                           if self.fighter_identity_key(candidate) == identity and label not in excluded]
                if len(matches) == 1:
                    return matches[0]
            return next((label for label in choices if label not in excluded), choices[0] if choices else "")
        a_label = label_for(prior_a)
        b_label = label_for(prior_b, excluded=(a_label,))
        self.sim_fighter_a.set(a_label)
        self.sim_fighter_b.set(b_label)
        if hasattr(self, "sim_tournament_list"):
            prior_keys = getattr(self, "_sim_tournament_row_keys", []) or []
            prior_selected_keys = {
                prior_keys[int(index)] for index in self.sim_tournament_list.curselection()
                if str(index).isdigit() and 0 <= int(index) < len(prior_keys)
            }
            # Compatibility with a widget created by an older build: retain a
            # name-only selection only when that name is unique in the new
            # source list.  Duplicate names remain unselected until the player
            # makes an explicit choice.
            prior_names = {
                self.sim_tournament_list.get(index)
                for index in self.sim_tournament_list.curselection()
                if not prior_keys
            }
            self.sim_tournament_list.delete(0, "end")
            self._sim_tournament_row_keys = []
            self._sim_tournament_rows_by_key = {}
            used_keys = set()
            for fighter in fighters:
                base_key = f"sim:{self.fighter_identity_key(fighter)}"
                row_key = base_key
                suffix = 2
                while row_key in used_keys:
                    row_key = f"{base_key}#{suffix}"
                    suffix += 1
                used_keys.add(row_key)
                self._sim_tournament_row_keys.append(row_key)
                self._sim_tournament_rows_by_key[row_key] = fighter
                self.sim_tournament_list.insert("end", fighter.name)
            name_counts = {}
            for fighter in fighters:
                name_counts[fighter.name] = name_counts.get(fighter.name, 0) + 1
            for index, (row_key, fighter) in enumerate(zip(self._sim_tournament_row_keys, fighters)):
                if row_key in prior_selected_keys or (fighter.name in prior_names and name_counts.get(fighter.name) == 1):
                    self.sim_tournament_list.selection_set(index)
        self.update_sim_fighter_cards()

    def selected_sim_fighter(self, corner):
        """Resolve a simulator corner through the retained choice identity."""
        variable = self.sim_fighter_a if corner == "a" else self.sim_fighter_b
        value = str(variable.get() or "")
        fighter = (getattr(self, "_sim_fighter_choice_rows", {}) or {}).get(value)
        if fighter is not None:
            return fighter
        matches = [candidate for candidate in self.all_database_fighters(include_retired=True)
                   if getattr(candidate, "name", "") == value]
        return matches[0] if len(matches) == 1 else None

    def _simulation_tournament_source_key(self, fighter):
        """Resolve a current Simulation Lab fighter through its saved row key."""
        rows = getattr(self, "_sim_tournament_rows_by_key", {}) or {}
        for row_key, source in rows.items():
            if source is fighter:
                return row_key
        identity = self.fighter_identity_key(fighter)
        matches = [row_key for row_key, source in rows.items()
                   if self.fighter_identity_key(source) == identity]
        return matches[0] if len(matches) == 1 else None

    def sim_filtered_fighters(self):
        gender = getattr(self, "sim_gender_filter", tk.StringVar(value="All")).get()
        weight = getattr(self, "sim_weight_filter", tk.StringVar(value="All")).get()
        fighters = [
            fighter for fighter in self.all_database_fighters()
            if (gender == "All" or fighter.gender == gender)
            and (weight == "All" or fighter.weight == weight)
        ]
        return sorted(fighters, key=lambda fighter: (-fighter.overall, -fighter.elo_rating, fighter.name))

    def sim_fighter_scout_text(self, fighter):
        if not fighter:
            return "Select a fighter from the filtered database."
        self.ensure_detailed_skills(fighter)
        self.ensure_fighter_business_stats(fighter)
        company = next((name for name, candidate in self.all_database_fighters_with_companies()
                        if candidate is fighter or self.fighter_identity_key(candidate) == self.fighter_identity_key(fighter)), "Unknown")
        return (
            f"{fighter.name}  |  OVR {fighter.overall}  |  ELO {fighter.elo_rating}\n"
            f"{fighter.gender} {fighter.weight}  |  {fighter.record}  |  Age {fighter.age}  |  {fighter.nationality}\n"
            f"{company}  |  {fighter.style_label} / {fighter.stance}  |  {fighter.trait}\n"
            f"Strike {fighter.striking}  Wrestle {fighter.wrestling}  Ground {fighter.grappling}  Cardio {fighter.cardio}  Chin {fighter.chin}\n"
            f"Power {fighter.power}  TD Def {fighter.takedown_defence}  Control {fighter.ground_control}  Subs {fighter.submissions}/{fighter.submission_defence}\n"
            f"Walk {fighter.walk_weight or self.default_walk_weight(fighter)} lb  Cut skill {self.ds(fighter, 'weight_cutting', fighter.cardio)}  Last cut penalty {fighter.weight_cut_penalty}\n"
            f"Pop {fighter.popularity}  Momentum {fighter.momentum:+d}  Morale {fighter.morale}  Camp {fighter.camp} (+{fighter.camp_boost})  Status {fighter.status}"
        )

    def update_sim_fighter_cards(self):
        if not hasattr(self, "sim_profile_a"):
            return
        self.sim_profile_a.config(text=self.sim_fighter_scout_text(self.selected_sim_fighter("a")))
        self.sim_profile_b.config(text=self.sim_fighter_scout_text(self.selected_sim_fighter("b")))

    def open_sim_fighter_profile(self, corner):
        fighter = self.selected_sim_fighter("a" if corner == "red" else "b")
        if fighter:
            self.open_fighter_profile_window(fighter)
        else:
            if not self._simulation_status_notice("Select a fighter first.", warning=True):
                messagebox.showinfo("Simulator", "Select a fighter first.")

    def auto_seed_sim_tournament(self):
        if not hasattr(self, "sim_tournament_list"):
            return
        size = int(self.sim_tournament_size.get())
        fighters = self.sim_filtered_fighters()
        if len(fighters) < size:
            text = f"This filter has only {len(fighters)} eligible fighters; {size} are needed. Broaden the filters or use a smaller bracket."
            if not self._simulation_status_notice(text, warning=True, tournament=True):
                messagebox.showwarning("Tournament", text)
            return
        # This is intentionally a draw, not a deterministic top-N pick. Stronger
        # fighters remain more likely to enter, then the selected field is seeded by merit.
        remaining = list(fighters)
        drawn = []
        while remaining and len(drawn) < size:
            def draw_score(fighter):
                rank_signal = max(0, fighter.elo_rating - 1400) / 26
                record_signal = max(-8, min(16, fighter.record_w - fighter.record_l))
                star_signal = fighter.popularity * 0.08
                return fighter.overall * 0.65 + rank_signal + record_signal + star_signal + random.uniform(-22, 22)
            selected = max(remaining, key=draw_score)
            drawn.append(selected)
            remaining.remove(selected)
        seeded = sorted(drawn, key=lambda fighter: (-fighter.overall, -fighter.elo_rating, -(fighter.record_w - fighter.record_l), fighter.name))
        seeded_keys = {self._simulation_tournament_source_key(fighter) for fighter in seeded}
        seeded_keys.discard(None)
        self.sim_tournament_list.selection_clear(0, "end")
        row_keys = getattr(self, "_sim_tournament_row_keys", []) or []
        for index, row_key in enumerate(row_keys):
            if row_key in seeded_keys:
                self.sim_tournament_list.selection_set(index)
        self.write_sim_tournament_report(
            f"{size}-fighter field drawn from the current filter, then seeded on overall and Elo.\n"
            + "\n".join(f"#{index + 1} {fighter.name} (OVR {fighter.overall}, ELO {fighter.elo_rating}, {fighter.record})" for index, fighter in enumerate(seeded))
        )

    def write_sim_tournament_report(self, text):
        if not hasattr(self, "sim_tournament_report"):
            return
        self.sim_tournament_report.config(state="normal")
        self.sim_tournament_report.delete("1.0", "end")
        self.sim_tournament_report.insert("end", text)
        self.sim_tournament_report.config(state="disabled")

    def simulate_tournament_bout(self, a, b, round_label):
        fight = {"fighters": [a.name, b.name], "title": False, "interim": False, "main": False, "tier": "Main Card", "region": "Simulation Lab"}
        winner, loser, method, round_no, commentary = self.simulate_fight(a, b, fight)
        heading = f"{round_label}: {a.name} vs {b.name}"
        lines = [heading, f"Odds: {self.matchup_odds(a, b)}"] + commentary
        if method != "Draw":
            summary = f"{winner.name} def. {loser.name} by {method}, R{round_no}"
            lines.append(f"Result: {summary}")
            return winner, loser, summary, {
                "heading": heading, "lines": lines, "a": a.name, "b": b.name,
                "a_record": a.record, "b_record": b.record, "weight": a.weight,
                "label": round_label, "result": summary,
            }
        # A tournament needs an advancing fighter. Replaying a drawn sandbox bout keeps the fight engine in charge of the result.
        for replay in range(1, 4):
            lines.append(f"Initial bout ended in a draw. Tournament replay {replay} begins.")
            winner, loser, method, round_no, replay_commentary = self.simulate_fight(a, b, fight)
            if method != "Draw":
                summary = f"{winner.name} def. {loser.name} by {method}, R{round_no} (after drawn bout replay {replay})"
                lines.extend(replay_commentary)
                lines.append(f"Result: {summary}")
                return winner, loser, summary, {
                    "heading": heading, "lines": lines, "a": a.name, "b": b.name,
                    "a_record": a.record, "b_record": b.record, "weight": a.weight,
                    "label": round_label, "result": summary,
                }
        winner, loser = (a, b) if (a.elo_rating, a.overall, a.name) >= (b.elo_rating, b.overall, b.name) else (b, a)
        summary = f"{a.name} vs {b.name} remained drawn after replays; {winner.name} advances on tournament seeding"
        lines.append(f"Result: {summary}")
        return winner, loser, summary, {
            "heading": heading, "lines": lines, "a": a.name, "b": b.name,
            "a_record": a.record, "b_record": b.record, "weight": a.weight,
            "label": round_label, "result": summary,
        }

    def run_simulation_tournament(self):
        if not hasattr(self, "sim_tournament_list"):
            return
        size = int(self.sim_tournament_size.get())
        row_keys = getattr(self, "_sim_tournament_row_keys", []) or []
        rows = getattr(self, "_sim_tournament_rows_by_key", {}) or {}
        selected_keys = [row_keys[int(index)] for index in self.sim_tournament_list.curselection()
                         if str(index).isdigit() and 0 <= int(index) < len(row_keys)]
        originals = [rows.get(row_key) for row_key in selected_keys]
        if len(originals) != size or any(fighter is None for fighter in originals):
            text = f"Select exactly {size} fighters, or use Draw & Seed Field for an automatic {size}-fighter field."
            if not self._simulation_status_notice(text, warning=True, tournament=True):
                messagebox.showinfo("Tournament", text)
            return
        genders = {fighter.gender for fighter in originals}
        weights = {fighter.weight for fighter in originals}
        if len(genders) != 1 or len(weights) != 1:
            text = "Tournament entrants must all be in the same gender and weight division. Use the filters to build a valid field."
            if not self._simulation_status_notice(text, warning=True, tournament=True):
                messagebox.showwarning("Tournament", text)
            return
        entrants = sorted((self.clone_fighter_for_sim(fighter) for fighter in originals), key=lambda fighter: (-fighter.overall, -fighter.elo_rating, fighter.name))
        gender = next(iter(genders))
        weight = next(iter(weights))
        report = [f"{size}-FIGHTER {gender.upper()} {weight.upper()} TOURNAMENT", "Sandbox results only: careers, records, and saves are unchanged.", "", "Seeds:"]
        report.extend(f"#{index + 1} {fighter.name} | OVR {fighter.overall} | ELO {fighter.elo_rating} | {fighter.record}" for index, fighter in enumerate(entrants))
        current = entrants
        round_number = 1
        stages = []
        fight_logs = []
        while len(current) > 1:
            stage = {2: "FINAL", 4: "SEMIFINALS", 8: "QUARTERFINALS", 16: "ROUND OF 16"}.get(len(current), f"ROUND {round_number}")
            report.extend(["", stage])
            pairings = list(zip(current[:len(current) // 2], reversed(current[len(current) // 2:])))
            winners = []
            stage_matches = []
            for a, b in pairings:
                winner, _loser, summary, fight_log = self.simulate_tournament_bout(a, b, stage)
                winner.fatigue = min(70, winner.fatigue + 7)
                winners.append(winner)
                report.append(summary)
                fight_logs.append(fight_log)
                stage_matches.append({"a": a.name, "b": b.name, "winner": winner.name, "summary": summary})
            stages.append({"name": stage, "matches": stage_matches})
            current = winners
            round_number += 1
        champion = current[0]
        report.extend(["", f"CHAMPION: {champion.name} | OVR {champion.overall} | {champion.record}"])
        self.write_sim_tournament_report("\n".join(report[:3] + ["", "Seeds:"] + report[4:4 + len(entrants)] + ["", "Tournament results are hidden until you watch the card."]))
        tournament_name = f"Simulation Lab {size}-Fighter {gender} {weight} Tournament"
        self.sim_tournament_bracket = {"title": tournament_name, "champion": champion.name, "stages": stages, "revealed": False}
        self.sim_tournament_event = {"name": tournament_name, "venue": "Simulation Lab Arena", "region": self.player_region, "city": "Sandbox", "month": self.month, "week": self.week, "fights": []}
        self.sim_tournament_package = {
            "log": report, "fight_logs": fight_logs, "results": [],
            "summary": f"{champion.name} wins the {size}-fighter tournament.",
        }
        self.open_sim_tournament_bracket()

    def watch_simulation_tournament(self):
        package = getattr(self, "sim_tournament_package", None)
        event = getattr(self, "sim_tournament_event", None)
        if not package or not event:
            text = "Run a tournament first, then its complete card can be watched like a fight night."
            if not self._simulation_status_notice(text, warning=True, tournament=True):
                messagebox.showinfo("Tournament Night", text)
            return
        def reveal_tournament():
            self.sim_tournament_bracket["revealed"] = True
            self.write_sim_tournament_report("\n".join(package["log"]))
            self.open_sim_tournament_bracket()
        self.open_live_fight_window(event, package, apply_results=False, on_complete=reveal_tournament)

    def open_sim_tournament_bracket(self):
        bracket = getattr(self, "sim_tournament_bracket", None)
        if not bracket:
            text = "Run a tournament first to create its visual bracket."
            if not self._simulation_status_notice(text, warning=True, tournament=True):
                messagebox.showinfo("Tournament Bracket", text)
            return
        window = self.create_managed_window()
        window.title(f"Tournament Bracket - {bracket['title']}")
        window.geometry("1180x720")
        window.minsize(900, 560)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="TOURNAMENT BRACKET", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        revealed = bool(bracket.get("revealed", False))
        ttk.Label(header, text=f"CHAMPION: {bracket['champion']}" if revealed else "RESULTS HIDDEN UNTIL WATCHED", style="ScreenTitle.TLabel").pack(side="right", padx=10, pady=5)
        subtitle = tk.Label(window, text=bracket["title"], bg=self.colors["chrome"], fg=self.colors["gold"], font=("Tahoma", 10, "bold"))
        subtitle.pack(fill="x", padx=10, pady=7)
        canvas = tk.Canvas(window, bg=self.colors["tree"], highlightthickness=1, highlightbackground=self.colors["line"])
        canvas.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        def draw(_event=None):
            canvas.delete("all")
            width = max(850, canvas.winfo_width())
            height = max(480, canvas.winfo_height())
            stages = bracket["stages"]
            columns = max(1, len(stages))
            left_margin, right_margin, top_margin = 22, 22, 48
            column_width = (width - left_margin - right_margin) / columns
            card_width = max(150, min(235, column_width - 28))
            positions = []
            for column, stage in enumerate(stages):
                x = left_margin + column * column_width + 8
                canvas.create_text(x, 22, text=stage["name"], anchor="w", fill=self.colors["gold"], font=("Impact", 14))
                count = max(1, len(stage["matches"]))
                step = (height - top_margin - 20) / count
                column_positions = []
                for index, match in enumerate(stage["matches"]):
                    y = top_margin + index * step + max(0, (step - 46) / 2)
                    column_positions.append((x, y, step))
                positions.append(column_positions)
            for column in range(len(stages) - 1):
                for index, (x, y, _step) in enumerate(positions[column]):
                    nx, ny, _next_step = positions[column + 1][index // 2]
                    start_x, start_y = x + card_width, y + 23
                    mid_x = start_x + max(8, (nx - start_x) / 2)
                    canvas.create_line(start_x, start_y, mid_x, start_y, mid_x, ny + 23, nx, ny + 23, fill=self.colors["line"], width=2)
            for column, stage in enumerate(stages):
                for index, match in enumerate(stage["matches"]):
                    x, y, _step = positions[column][index]
                    canvas.create_rectangle(x, y, x + card_width, y + 46, fill=self.colors["panel"], outline=self.colors["gold"] if stage["name"] == "FINAL" else self.colors["line"], width=2 if stage["name"] == "FINAL" else 1)
                    a_color = self.colors["gold"] if revealed and match["winner"] == match["a"] else self.colors["text"]
                    b_color = self.colors["gold"] if revealed and match["winner"] == match["b"] else self.colors["text"]
                    canvas.create_text(x + 8, y + 12, text=match["a"], anchor="w", fill=a_color, font=("Tahoma", 8, "bold"))
                    canvas.create_text(x + 8, y + 32, text=match["b"], anchor="w", fill=b_color, font=("Tahoma", 8, "bold"))
                    if revealed:
                        canvas.create_text(x + card_width - 7, y + 23, text="W", anchor="e", fill=self.colors["muted"], font=("Tahoma", 7, "bold"))
        canvas.bind("<Configure>", draw)
        draw()
        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Watch Tournament Night", style="Accent.TButton", command=self.watch_simulation_tournament).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4)

    def find_fighter_anywhere(self, name):
        for fighter in self.all_database_fighters(include_retired=True):
            if fighter.name == name or getattr(fighter, "fighter_id", "") == name:
                return fighter
        return None

    def clone_fighter_for_sim(self, fighter):
        clone = Fighter(**asdict(fighter))
        self.ensure_detailed_skills(clone)
        self.ensure_fighter_business_stats(clone)
        clone.weight_cut_penalty = 0
        clone.camp_boost = getattr(fighter, "camp_boost", 0)
        return clone

    def prepare_sim_fighter(self, fighter, camp_weeks, title_fight=False):
        """Apply a sandbox camp and weigh-in to a disposable fighter clone."""
        fighter.camp_weeks = max(0, min(16, int(camp_weeks)))
        gym = self.gym_by_name(fighter.camp)
        quality = self.gym_quality(fighter.camp)
        specialty = self.gym_specialty_bonus(fighter, gym)
        fighter.camp_quality = quality
        base_boost = round(fighter.camp_weeks * (quality + specialty) / 135 * (0.65 + fighter.professionalism / 300))
        fighter.camp_boost = min(12, max(0, base_boost + self.camp_form_variance(fighter, gym)))
        outcome = self.perform_weigh_in(fighter, title_fight=title_fight, camp_weeks=fighter.camp_weeks, persist=True)
        return outcome

    def run_quick_fight_sim(self, watch=False):
        original_a = self.selected_sim_fighter("a")
        original_b = self.selected_sim_fighter("b")
        if not original_a or not original_b or original_a is original_b:
            if not self._simulation_status_notice("Pick two different fighters.", warning=True):
                messagebox.showinfo("Simulator", "Pick two different fighters.")
            return
        if self.fighter_identity_key(original_a) == self.fighter_identity_key(original_b):
            text = "Pick two different fighter identities. Duplicate display names are kept separate in the simulator."
            if not self._simulation_status_notice(text, warning=True):
                messagebox.showwarning("Simulator", text)
            return
        if original_a.gender != original_b.gender and not self.rules.get("allow_mixed_gender", False):
            text = "Mixed-gender fights are not allowed under this promotion's current rules."
            if not self._simulation_status_notice(text, warning=True):
                messagebox.showwarning("Rules blocked", text)
            return
        if original_a.weight != original_b.weight:
            if not messagebox.askyesno("Weight mismatch", "These fighters are in different weight classes. Run this as an openweight simulator bout?"):
                return
        a = self.clone_fighter_for_sim(original_a)
        b = self.clone_fighter_for_sim(original_b)
        a_weigh = self.prepare_sim_fighter(a, self.sim_camp_weeks_a.get(), self.sim_title_fight.get())
        b_weigh = self.prepare_sim_fighter(b, self.sim_camp_weeks_b.get(), self.sim_title_fight.get())
        fight = {"fighters": [a.name, b.name], "title": self.sim_title_fight.get(), "interim": False, "main": self.sim_main_event.get(), "tier": "Main Card"}
        winner, loser, method, round_no, commentary = self.simulate_fight(a, b, fight)
        hype = self.fight_hype(a, b, fight)
        excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, hype)
        label = "TITLE SIM" if fight["title"] else ("MAIN EVENT SIM" if fight["main"] else "SIM BOUT")
        a_weight_note = "made" if a_weigh["made"] else f"missed by {a_weigh['miss_by']}"
        b_weight_note = "made" if b_weigh["made"] else f"missed by {b_weigh['miss_by']}"
        lines = [
            f"{label}: {a.name} vs {b.name} ({a.weight})", f"Odds: {self.matchup_odds(a, b)}",
            f"Sandbox camps: {a.name} {a.camp_weeks} wk (+{a.camp_boost}) | {b.name} {b.camp_weeks} wk (+{b.camp_boost})",
            f"Sandbox weigh-ins: {a.name} {a_weigh['scale_weight']} lb ({a_weight_note}, cut penalty {a_weigh['penalty']}) | {b.name} {b_weigh['scale_weight']} lb ({b_weight_note}, cut penalty {b_weigh['penalty']})",
        ]
        lines.extend(commentary)
        result_metrics = getattr(getattr(self, "_last_fight_result", None), "metrics", {})
        move_metrics = result_metrics.get("exchanges", {})
        def family_line(slot, fighter):
            rows = move_metrics.get(slot, {}).get("move_families", {})
            leaders = sorted(rows.items(), key=lambda item: (-item[1].get("attempts", 0), item[0]))[:4]
            summary = ", ".join(f"{family} {row.get('effective', 0)}/{row.get('attempts', 0)}" for family, row in leaders)
            return f"{fighter.name}: {summary or 'no established family'}"
        move_line = "Move families (effective/used) - " + family_line("a", a) + " | " + family_line("b", b)
        analysis_lines = [move_line]

        def technique_line(slot, fighter):
            techniques = result_metrics.get("techniques", {}).get(slot, {})
            top_moves = techniques.get("top_moves", [])
            top = ", ".join(
                f"{row.get('move_id', '').replace('_', ' ')} x{row.get('attempts', 0)}"
                for row in top_moves[:3]
            ) or "none"
            mechanics = techniques.get("average_mechanics", {})
            stance = ", ".join(
                f"{name} {count}" for name, count in sorted(techniques.get("stance_matchups", {}).items())
            ) or "none"
            return (
                f"{fighter.name}: top {top}; sequences {techniques.get('completed_sequences', 0)}; "
                f"technique load E{mechanics.get('energy', 1.0):.2f}/M{mechanics.get('miss_risk', 1.0):.2f}/C{mechanics.get('counter_risk', 1.0):.2f}; "
                f"stance lanes {stance}"
            )

        def signature_line(slot, fighter):
            rows = result_metrics.get("signature_moves", {}).get(slot, {})
            attempts = sum(int(row.get("attempts", 0)) for row in rows.values())
            effective = sum(int(row.get("landed", 0)) for row in rows.values())
            return f"{fighter.name} {effective}/{attempts}"

        analysis_lines.extend([
            "Technique analysis - " + technique_line("a", a),
            "Technique analysis - " + technique_line("b", b),
            "Signature moves (effective/used) - " + signature_line("a", a) + " | " + signature_line("b", b),
            (
                f"Fight-plan evolution - {a.name}: {a.last_fight_stats.get('fight_plan', 'Balanced')} -> "
                f"{a.last_fight_stats.get('final_fight_plan', 'Balanced')} "
                f"({a.last_fight_stats.get('plan_adjustments', 0)} adjustments, "
                f"{a.last_fight_stats.get('plan_confidence', 0.5):.0%} confidence) | "
                f"{b.name}: {b.last_fight_stats.get('fight_plan', 'Balanced')} -> "
                f"{b.last_fight_stats.get('final_fight_plan', 'Balanced')} "
                f"({b.last_fight_stats.get('plan_adjustments', 0)} adjustments, "
                f"{b.last_fight_stats.get('plan_confidence', 0.5):.0%} confidence)"
            ),
        ])
        lines.extend(analysis_lines)
        if method == "Draw":
            lines.append(f"Result: {a.name} vs {b.name} ends in a draw, R{round_no} | Fight excitement {excitement}")
        else:
            lines.append(f"Result: {winner.name} def. {loser.name} by {method}, R{round_no} | Fight excitement {excitement}")
        package = {
            "log": [f"Quick Fight Simulator - {a.name} vs {b.name}", "=" * 72] + lines,
            "fight_logs": [{"heading": lines[0], "lines": lines}],
            "results": [],
            "summary": lines[-1],
        }
        if hasattr(self, "sim_result"):
            revealed = lines[-1] + "\n" + "\n".join(analysis_lines)
            self.sim_result.config(text="Fight prepared. Watch it to reveal the result." if watch else revealed)
        if watch:
            event = {"name": "Quick Fight Simulator", "venue": "Simulation Lab", "region": self.player_region, "city": "Sandbox", "month": self.month, "week": self.week, "fights": [fight]}
            self.open_live_fight_window(event, package, apply_results=False, on_complete=lambda: self.sim_result.config(text=revealed))

    def run_simulation_audit(self):
        """Audit competitive fight outcomes without mutating the active career.

        The old audit paired two fighters drawn from the full 42-92 skill span.
        That made severe mismatches common, inflated finishes, and then presented
        the mixed result as if it described normal matchmaking. Keep the useful
        synthetic business stress test, but build the fight sample inside named
        ability bands and prefer an opponent no more than six overall points away.
        """
        self.apply_engine_settings()
        runs = max(10, min(1000, self.audit_runs.get()))
        methods = {}
        tier_methods = {"Low": {}, "Mid": {}, "High": {}}
        matchup_gaps = []
        gates = []
        profits = []
        hypes = []
        builds = []
        upsets = 0
        original_state = random.getstate()
        original_name_counts = dict(getattr(self, "name_counts", {}))
        for index in range(runs):
            fights = []
            for _ in range(random.randint(7, 11)):
                tier, minimum, maximum = random.choice((
                    ("Low", 45, 62), ("Mid", 63, 76), ("High", 78, 92),
                ))
                a = self.create_generated_fighter(12, 80, minimum, maximum)
                # Choose the closest of several same-band candidates. This keeps
                # the audit representative of cards a competent matchmaker would
                # actually book while still retaining natural style variation.
                candidates = [
                    self.create_generated_fighter(
                        12, 80, minimum, maximum, weight=a.weight, gender=a.gender,
                    )
                    for _candidate in range(6)
                ]
                b = min(candidates, key=lambda fighter: abs(fighter.overall - a.overall))
                gap = abs(a.overall - b.overall)
                matchup_gaps.append(gap)
                fight = {"fighters": [a.name, b.name], "title": False, "main": False, "tier": random.choice(CARD_TIERS)}
                hype = self.fight_hype(a, b, fight)
                build = self.match_build_score(a, b, fight)
                winner, loser, method, _round, _lines = self.simulate_fight(a, b, fight)
                methods[method] = methods.get(method, 0) + 1
                tier_methods[tier][method] = tier_methods[tier].get(method, 0) + 1
                if loser.overall > winner.overall + 5:
                    upsets += 1
                fights.append((winner, loser, fight, method, hype, build))
            total_hype = sum(row[4] for row in fights)
            total_build = sum(row[5] for row in fights) / max(1, len(fights))
            total_pay = sum(row[0].purse + row[1].purse for row in fights)
            venue_capacity = random.choice([900, 4200, 7500, 14500])
            regional_pull = random.uniform(0.8, 1.35)
            attendance = min(venue_capacity, max(120, round(total_hype * random.uniform(8, 24) * regional_pull)))
            ticket_price = random.randint(32, 92)
            gate = round(attendance * ticket_price * self.business_settings.get("gate_multiplier", 1.0))
            rights = round(total_hype * random.randint(550, 1700) * (0.65 + total_build / 210))
            production = len(fights) * random.randint(19000, 45000) + venue_capacity * 16
            sponsorship = round(total_hype * random.randint(380, 1100) * (0.6 + total_build / 220))
            profit = gate + rights - total_pay - production
            profit += sponsorship
            gates.append(gate)
            profits.append(profit)
            hypes.append(total_hype / max(1, len(fights)))
            builds.append(total_build)
        random.setstate(original_state)
        self.name_counts = original_name_counts
        def avg(values):
            return round(sum(values) / max(1, len(values)))
        report = [
            f"Audit events: {runs}",
            f"Synthetic audit gate: ${avg(gates):,} (not the player event-finance model)",
            f"Synthetic audit profit: ${avg(profits):,} (not the player event-finance model)",
            f"Average matchup hype: {avg(hypes)}",
            f"Average fight build: {avg(builds)}",
            f"Competitive matchup coverage: {sum(gap <= 6 for gap in matchup_gaps)}/{len(matchup_gaps)} ({round(sum(gap <= 6 for gap in matchup_gaps) / max(1, len(matchup_gaps)) * 100, 1)}%) at OVR gap <= 6",
            f"Upsets: {upsets} ({round(upsets / max(1, sum(methods.values())) * 100, 1)}% of fights)",
            "",
            "Methods:",
        ]
        for method, count in sorted(methods.items(), key=lambda item: -item[1]):
            report.append(f"- {method}: {count} ({round(count / max(1, sum(methods.values())) * 100, 1)}%)")
        report.extend(["", "Competitive finish rate by generated tier:"])
        for tier in ("Low", "Mid", "High"):
            tier_total = sum(tier_methods[tier].values())
            decisions = tier_methods[tier].get("Decision", 0) + tier_methods[tier].get("Draw", 0)
            finish_rate = round((tier_total - decisions) / max(1, tier_total) * 100, 1)
            report.append(f"- {tier}: {finish_rate}% finishes across {tier_total} fights")
        self.audit_text.config(state="normal")
        self.audit_text.delete("1.0", "end")
        self.audit_text.insert("end", "\n".join(report))
        self.audit_text.config(state="disabled")

    def play_audit_seed_value(self, seed=None):
        """Return the bounded explicit seed used by a play-audit recipe."""
        raw = seed
        if raw is None:
            raw = getattr(self, "play_audit_seed", 260712)
            try:
                raw = raw.get() if hasattr(raw, "get") else raw
            except (tk.TclError, TypeError, ValueError):
                raw = 260712
        try:
            return max(1, min(2_147_483_647, int(raw)))
        except (TypeError, ValueError, OverflowError):
            return 260712

    def play_audit_time_limit_value(self, value=None):
        """Return a bounded wall-clock limit for one isolated play audit."""
        raw = value
        if raw is None:
            raw = getattr(
                self,
                "play_audit_time_limit_seconds",
                PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS,
            )
            try:
                raw = raw.get() if hasattr(raw, "get") else raw
            except (tk.TclError, TypeError, ValueError):
                raw = PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS
        try:
            parsed = int(float(raw))
        except (TypeError, ValueError, OverflowError):
            parsed = PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS
        return max(
            PLAY_AUDIT_MIN_TIME_LIMIT_SECONDS,
            min(PLAY_AUDIT_MAX_TIME_LIMIT_SECONDS, parsed),
        )

    def play_audit_time_limit_reached(self, started_at, limit_seconds, now=None):
        """Return whether a bounded audit may stop at the next safe boundary.

        The helper is deliberately pure apart from the default monotonic clock
        read. It clamps malformed limits through the same policy used by the
        Simulation Lab and treats a malformed start/clock value as not
        elapsed, leaving the caller free to retain its exact checkpoint rather
        than inventing progress.
        """
        try:
            started = float(started_at)
            current = time.monotonic() if now is None else float(now)
            if not math.isfinite(started) or not math.isfinite(current):
                return False
            elapsed = max(0.0, current - started)
        except (TypeError, ValueError, OverflowError):
            return False
        limit = self.play_audit_time_limit_value(limit_seconds)
        return elapsed >= limit

    def play_audit_identity(self, years, seed=None):
        """Return the source/configuration identity for an isolated play audit."""
        years = max(1, min(100, int(years)))
        seed = self.play_audit_seed_value(seed)
        configuration = {
            "engine_settings": deepcopy(getattr(self, "engine_settings", {}) or {}),
            "business_settings": deepcopy(getattr(self, "business_settings", {}) or {}),
            "rules": deepcopy(getattr(self, "rules", {}) or {}),
        }
        # The release profile is part of the audit identity.  It is read-only
        # metadata; no candidate registry or runtime hook is installed here.
        profile = str(getattr(self, "fight_engine_profile", "release") or "release")
        return build_audit_identity(
            seed=seed,
            target_weeks=years * 48,
            configuration=configuration,
            source_root=Path(__file__).resolve().parent,
            native_profile=profile,
        )

    def play_audit_checkpoint_path(self, years=None, seed=None):
        """Return the bounded latest checkpoint path for one audit recipe."""
        if years is None:
            years = max(1, min(100, int(self.play_audit_years.get())))
        years = max(1, min(100, int(years)))
        seed = self.play_audit_seed_value(seed)
        return LOG_DIR / "Play Audits" / f"play_audit_{seed}_{years}y.checkpoint.json"

    def play_audit_report_path(self, years=None, seed=None):
        """Return the durable raw-report path paired with one checkpoint."""
        if years is None:
            years = max(1, min(100, int(self.play_audit_years.get())))
        years = max(1, min(100, int(years)))
        seed = self.play_audit_seed_value(seed)
        return LOG_DIR / "Play Audits" / f"play_audit_{seed}_{years}y.report.txt"

    def write_play_audit_report(self, report, *, years=None, seed=None):
        """Persist a bounded raw audit report without touching the active save."""
        path = self.play_audit_report_path(years, seed=seed)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(str(report or ""), encoding="utf-8")
            temporary.replace(path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        return path

    def read_play_audit_report(self, *, years=None, seed=None):
        """Read the paired raw report without normalising or mutating it."""
        path = self.play_audit_report_path(years, seed=seed)
        try:
            if path.stat().st_size > 5_000_000:
                return ""
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return ""

    def play_audit_manifest_path(self):
        """Return the bounded index of retained isolated audit runs."""
        return LOG_DIR / "Play Audits" / "play_audit_manifest.json"

    def read_play_audit_manifest(self):
        """Read retained audit-run metadata without repairing the manifest."""
        path = self.play_audit_manifest_path()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            return []
        rows = payload.get("rows") if isinstance(payload, dict) else payload
        return [deepcopy(row) for row in rows[-200:] if isinstance(row, dict)] if isinstance(rows, list) else []

    def play_audit_manifest_summary(self):
        """Return a read-only qualification summary for retained audit rows."""
        rows = self.read_play_audit_manifest()
        complete = paused = time_limited = failed = current_source = reports = 0
        seeds = set()
        current_source_recipes = {}
        for row in rows:
            status = str(row.get("status", "unknown") or "unknown")
            try:
                target_weeks = max(0, int(row.get("target_weeks", 0) or 0))
                completed_weeks = max(0, int(row.get("completed_weeks", 0) or 0))
            except (TypeError, ValueError, OverflowError):
                target_weeks = completed_weeks = 0
            if status == "complete" and target_weeks and completed_weeks >= target_weeks:
                complete += 1
            elif status == "paused":
                paused += 1
            elif status == "time_limit":
                time_limited += 1
            elif status not in {"complete", "paused"}:
                failed += 1
            try:
                seed = self.play_audit_seed_value(row.get("seed"))
            except (TypeError, ValueError, OverflowError):
                seed = None
            if seed is not None:
                seeds.add(seed)
            report_path = Path(str(row.get("report_path", "") or ""))
            try:
                reports += int(report_path.is_file() and report_path.stat().st_size <= 5_000_000)
            except OSError:
                pass
            # Source comparison is intentionally observational.  A row with
            # a non-year target cannot be compared to the current recipe and
            # remains visible as unknown rather than being normalised.
            if target_weeks and target_weeks % 48 == 0 and seed is not None:
                try:
                    current = self.play_audit_identity(target_weeks // 48, seed=seed)
                    if str(row.get("source_digest", "") or "") == str(current.get("source_digest", "") or ""):
                        current_source += 1
                        if status == "complete" and target_weeks and completed_weeks >= target_weeks:
                            years = target_weeks // 48
                            recipe = current_source_recipes.setdefault(
                                years,
                                {"years": years, "complete_runs": 0, "seeds": set()},
                            )
                            recipe["complete_runs"] += 1
                            recipe["seeds"].add(seed)
                except (OSError, TypeError, ValueError, OverflowError):
                    pass
        recipe_summary = []
        for years, recipe in sorted(current_source_recipes.items()):
            recipe_summary.append({
                "years": years,
                "complete_runs": int(recipe.get("complete_runs", 0) or 0),
                "unique_seeds": len(recipe.get("seeds", set()) or set()),
                "seeds": sorted(recipe.get("seeds", set()) or set()),
            })
        return {
            "rows": len(rows),
            "complete": complete,
            "paused": paused,
            "time_limited": time_limited,
            "failed": failed,
            "unique_seeds": len(seeds),
            "current_source": current_source,
            "reports_available": reports,
            "threshold_policy": "Pending approval",
            "current_source_recipes": recipe_summary,
        }

    def open_play_audit_manifest(self):
        """Show retained isolated-audit runs without changing game state."""
        rows = self.read_play_audit_manifest()
        window = self.create_managed_window()
        window.title("Play Audit Evidence")
        window.geometry("930x520")
        window.minsize(760, 400)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(
            window,
            text="PLAY AUDIT EVIDENCE",
            style="ScreenTitle.TLabel",
        ).pack(anchor="w", padx=12, pady=(10, 2))
        summary = self.play_audit_manifest_summary()
        recipe_summary = summary.get("current_source_recipes", [])
        recipe_label = ", ".join(
            f"{row.get('years', 0)}y: {row.get('unique_seeds', 0)} seed(s)"
            for row in recipe_summary if isinstance(row, dict)
        ) or "none"
        ttk.Label(
            window,
            text=(
                f"{len(rows)} retained run(s) | {summary['complete']} complete | "
                f"{summary['paused']} paused | {summary.get('time_limited', 0)} time-limited | {summary['unique_seeds']} seed(s) | "
                f"{summary['current_source']} current-source match(es) | "
                f"{summary['reports_available']} report(s) available. "
                f"Complete current-source recipes: {recipe_label}. "
                f"Threshold policy: {summary['threshold_policy']}. This is a read-only index of isolated reports; "
                "opening a row never resumes, repairs or reruns an audit."
            ),
            style="Inset.TLabel",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 8))
        frame = ttk.Frame(window, style="Panel.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        table_frame = ttk.Frame(frame, style="Inset.TFrame")
        table_frame.pack(fill="both", expand=True, padx=6, pady=6)
        columns = ("status", "seed", "duration", "progress", "updated", "identity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "status": "Status", "seed": "Seed", "duration": "Target",
            "progress": "Progress", "updated": "Updated", "identity": "Source / Config",
        }
        widths = {"status": 125, "seed": 90, "duration": 75, "progress": 95, "updated": 150, "identity": 170}
        for column in columns:
            tree.heading(column, text=headings[column])
            tree.column(column, width=widths[column], anchor="w", stretch=column in ("updated", "identity"))
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row_by_iid = {}
        for index, row in enumerate(rows):
            iid = f"audit:{index}"
            row_by_iid[iid] = row
            try:
                target_weeks = max(1, int(row.get("target_weeks", 0) or 0))
            except (TypeError, ValueError, OverflowError):
                target_weeks = 0
            try:
                completed_weeks = max(0, int(row.get("completed_weeks", 0) or 0))
            except (TypeError, ValueError, OverflowError):
                completed_weeks = 0
            seed = row.get("seed", "—")
            target_label = f"{target_weeks // 48}y" if target_weeks and target_weeks % 48 == 0 else f"{target_weeks}w"
            progress = f"{completed_weeks}/{target_weeks}" if target_weeks else "—"
            identity = str(row.get("identity_digest", "") or "")[:16] or "—"
            tree.insert(
                "", "end", iid=iid,
                values=(
                    str(row.get("status", "unknown") or "unknown"), seed,
                    target_label, progress,
                    str(row.get("updated_at", "") or "—"), identity,
                ),
            )

        detail_var = tk.StringVar(value="Select a retained run to inspect its raw report.")
        ttk.Label(frame, textvariable=detail_var, style="Inset.TLabel", anchor="w", justify="left", wraplength=900).pack(fill="x", padx=8, pady=(0, 6))

        def open_selected_report():
            selected = tree.selection()
            if not selected:
                detail_var.set("Select a retained run first.")
                return
            row = row_by_iid.get(selected[0], {})
            report_path = Path(str(row.get("report_path", "") or ""))
            try:
                if not report_path.is_file() or report_path.stat().st_size > 5_000_000:
                    raise OSError("report is unavailable or exceeds the read limit")
                report = report_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                detail_var.set("The retained report is unavailable. The manifest row was not changed.")
                return
            report_window = self.create_managed_window()
            report_window.title("Play Audit Report")
            report_window.geometry("940x680")
            report_window.minsize(720, 480)
            report_window.configure(bg=self.colors["chrome"])
            ttk.Label(report_window, text="RETAINED PLAY AUDIT REPORT", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
            text = tk.Text(
                report_window, wrap="none", font=("Courier New", 10),
                bg=self.colors["cream"], fg=self.colors["text"], padx=12, pady=12,
            )
            text.pack(fill="both", expand=True, padx=10, pady=(0, 8))
            text.insert("1.0", report)
            text.config(state="disabled")
            ttk.Button(report_window, text="Close", style="Accent.TButton", command=report_window.destroy).pack(anchor="e", padx=10, pady=(0, 10))

        buttons = ttk.Frame(window, style="Panel.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Open Selected Report", style="Accent.TButton", command=open_selected_report).pack(side="left")
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

    def write_play_audit_manifest_row(self, *, identity, completed_weeks,
                                      status, report_path, checkpoint_path,
                                      time_limit_seconds=None):
        """Record one audit run without duplicating retries or touching saves."""
        identity = identity if isinstance(identity, dict) else {}
        try:
            target_weeks = max(1, int(identity.get("target_weeks", 1) or 1))
        except (TypeError, ValueError, OverflowError):
            target_weeks = 1
        try:
            completed = max(0, min(target_weeks, int(completed_weeks or 0)))
        except (TypeError, ValueError, OverflowError):
            completed = 0
        seed = self.play_audit_seed_value(identity.get("seed"))
        digest = str(identity.get("identity_digest", "") or "")
        run_key = f"{seed}:{target_weeks}:{digest}"
        row = {
            "schema_version": 1,
            "run_key": run_key,
            "seed": seed,
            "target_weeks": target_weeks,
            "completed_weeks": completed,
            "status": str(status or "unknown"),
            "identity_digest": digest,
            "source_digest": str(identity.get("source_digest", "") or ""),
            "report_path": str(report_path or ""),
            "checkpoint_path": str(checkpoint_path or ""),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        if time_limit_seconds is not None:
            row["time_limit_seconds"] = self.play_audit_time_limit_value(time_limit_seconds)
        rows = self.read_play_audit_manifest()
        replaced = False
        for index, prior in enumerate(rows):
            if str(prior.get("run_key", "") or "") == run_key:
                rows[index] = row
                replaced = True
                break
        if not replaced:
            rows.append(row)
        rows = rows[-200:]
        path = self.play_audit_manifest_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps({"schema_version": 1, "rows": rows}, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        return row

    def write_play_audit_checkpoint(self, *, audit, identity, completed_weeks,
                                    target_weeks, methods, snapshots,
                                    output_cursor=None, status="paused", world_state=None,
                                    time_limit_seconds=None, stop_reason=None):
        """Persist one isolated audit checkpoint; never touch the active save."""
        if world_state is None:
            world_state = audit.serialize_world()
        checkpoint = make_checkpoint(
            identity=identity,
            completed_weeks=completed_weeks,
            target_weeks=target_weeks,
            rng_state=random.getstate(),
            world_state=world_state,
            methods=methods,
            snapshots=snapshots,
            output_cursor=output_cursor or {"completed_weeks": completed_weeks},
            status=status,
            time_limit_seconds=time_limit_seconds,
            stop_reason=stop_reason,
        )
        path = self.play_audit_checkpoint_path(target_weeks // 48, seed=identity.get("seed"))
        write_checkpoint_atomic(path, checkpoint)
        return path

    def resume_play_level_audit(self):
        """Resume a compatible isolated audit from its latest yearly boundary."""
        return self.run_play_level_audit(resume=True)

    def run_100_year_play_audit(self):
        """Launch the canonical 100-year observer audit recipe explicitly."""
        if hasattr(self, "play_audit_years"):
            self.play_audit_years.set(100)
        return self.run_play_level_audit(resume=False)

    def run_play_level_audit(self, *, resume=False):
        """Run or resume an isolated observer-world audit without touching this save."""
        years = max(1, min(100, self.play_audit_years.get()))
        seed = self.play_audit_seed_value()
        time_limit_seconds = self.play_audit_time_limit_value()
        weeks = years * 48
        identity = self.play_audit_identity(years, seed=seed)
        checkpoint = None
        if resume:
            path = self.play_audit_checkpoint_path(years, seed=seed)
            try:
                checkpoint = validate_checkpoint(read_checkpoint(path), identity)
            except (AuditCheckpointError, OSError, ValueError) as exc:
                message = f"Cannot resume this audit safely: {exc}"
                if hasattr(self, "play_audit_status"):
                    self.play_audit_status.config(text="Resume refused - source/configuration mismatch")
                if hasattr(self, "audit_text"):
                    self.audit_text.config(state="normal")
                    self.audit_text.delete("1.0", "end")
                    self.audit_text.insert("end", message)
                    self.audit_text.config(state="disabled")
                return False
            if int(checkpoint.get("completed_weeks", 0) or 0) >= weeks:
                if hasattr(self, "play_audit_status"):
                    self.play_audit_status.config(text="Audit already complete - view the saved report")
                return False
            if str(checkpoint.get("status", "paused")) == "failed_invariant":
                if hasattr(self, "play_audit_status"):
                    self.play_audit_status.config(text="Resume refused - blocking finding requires review")
                if hasattr(self, "audit_text"):
                    self.audit_text.config(state="normal")
                    self.audit_text.delete("1.0", "end")
                    self.audit_text.insert("end", "This audit stopped on a blocking finding. Review the saved checkpoint before starting a fresh run.")
                    self.audit_text.config(state="disabled")
                return False
        start_completed = int(checkpoint.get("completed_weeks", 0) or 0) if checkpoint else 0
        if hasattr(self, "play_audit_progress"):
            self.play_audit_progress.configure(maximum=weeks, value=start_completed)
            phase = "resuming isolated observer world" if checkpoint else "starting fresh observer world"
            self.play_audit_status.config(text=f"{years}-year play audit: {phase}...")
        self.audit_text.config(state="normal")
        self.audit_text.delete("1.0", "end")
        phase = "resuming" if checkpoint else "fresh"
        self.audit_text.insert(
            "end",
            f"Running {phase} {years}-year observer audit...\n"
            f"The audit is bounded to {time_limit_seconds} seconds and can be resumed from its latest weekly checkpoint.",
        )
        self.audit_text.config(state="disabled")
        self.root.update_idletasks()
        audit_root = tk.Tk()
        audit_root.withdraw()
        methods = dict(checkpoint.get("methods", {}) or {}) if checkpoint else {}
        snapshots = deepcopy(checkpoint.get("snapshots", []) or []) if checkpoint else []
        checkpoint_notes = []
        completed_weeks = start_completed
        hard_invariant_findings = []
        balance_findings = []
        measurement_findings = []
        audit_stopped = False
        audit_stop_reason = ""
        latest_measurement = None
        boundary_timings = []
        original_state = random.getstate()
        audit_started = time.monotonic()
        try:
            if checkpoint:
                # Applying a saved audit world can run normal load-time
                # migration helpers. Restore the captured RNG only after those
                # helpers and spectator controls are installed.
                random.seed(seed)
                audit = self.__class__(audit_root)
                audit.apply_world_data(deepcopy(checkpoint["world_state"]))
            else:
                random.seed(seed)
                audit = self.__class__(audit_root)
            audit.enter_spectator_mode()
            audit.suppress_award_popups = True
            audit.suppress_autosaves = True
            if checkpoint:
                random.setstate(decode_rng_state(checkpoint["rng_state"]))
            real_simulate = audit.simulate_fight

            def count_fight(a, b, fight):
                winner, loser, method, round_no, lines = real_simulate(a, b, fight)
                methods[method] = methods.get(method, 0) + 1
                return winner, loser, method, round_no, lines

            audit.simulate_fight = count_fight
            for index in range(start_completed, weeks):
                audit.advance_month()
                # ``advance_month`` records each native calendar task in a
                # bounded diagnostic ring. Copy those rows into the current
                # yearly boundary and clear the ring so the checkpoint keeps
                # the complete boundary without retaining unbounded history.
                raw_timings = getattr(audit, "_advance_task_timings", None)
                if isinstance(raw_timings, list):
                    boundary_timings.extend(deepcopy(raw_timings))
                    raw_timings[:] = []
                completed_weeks = index + 1
                if (index + 1) % 4 == 0 or index + 1 == weeks:
                    if hasattr(self, "play_audit_progress"):
                        completed = index + 1
                        audit_year = 2026 + completed // 48
                        audit_week = completed % 48
                        elapsed_seconds = int(max(0.0, time.monotonic() - audit_started))
                        remaining_seconds = max(0, time_limit_seconds - elapsed_seconds)
                        self.play_audit_progress.configure(value=completed)
                        self.play_audit_status.config(
                            text=(
                                f"{years}-year play audit: Year {audit_year} | "
                                f"week {audit_week or 48}/48 ({completed / weeks * 100:.1f}%) | "
                                f"{elapsed_seconds}s elapsed / {remaining_seconds}s left"
                            )
                        )
                    self.root.update_idletasks()
                time_limit_reached = self.play_audit_time_limit_reached(
                    audit_started, time_limit_seconds,
                )
                # A timeout outside a yearly boundary is still safe: the
                # native weekly task has completed, so retain that exact world
                # and RNG state as a resumable checkpoint without inventing a
                # partial yearly snapshot.
                if time_limit_reached and (index + 1) % 48 != 0:
                    try:
                        world_state = audit.serialize_world()
                        latest_measurement = build_audit_measurement(
                            world_state, year=2026 + (index + 1) // 48,
                        )
                        # ``build_audit_measurement`` contains the detailed
                        # evidence fields; add the same bounded headline
                        # counters used by yearly rows so a timeout before
                        # week 48 still produces a useful report.
                        active_now = [
                            fighter for fighter in audit.all_fighter_objects()
                            if not fighter.retired
                        ]
                        cash_now = [promo.cash for promo in audit.promotions]
                        latest_measurement.update({
                            "year": 2026 + (index + 1) // 48,
                            "promotions": len(audit.promotions),
                            "viable": sum(1 for promo in audit.promotions if promo.cash > 0 and promo.stability >= 20),
                            "distressed": sum(1 for promo in audit.promotions if promo.cash < 0 or promo.stability < 20),
                            "active": len(active_now),
                            "free_agents": len(audit.free_agents),
                            "retired": len(audit.retired_fighters),
                            "elite": sum(1 for fighter in active_now if fighter.overall >= 80),
                            "avg_cash": round(sum(cash_now) / max(1, len(cash_now))),
                            "min_cash": min(cash_now) if cash_now else 0,
                            "sport_events": sum(
                                _audit_collection_count(world.get("events", 0))
                                for world in getattr(audit, "combat_sport_worlds", {}).values()
                                if isinstance(world, dict)
                            ),
                            "academy_size": len((getattr(audit, "academy", {}) or {}).get("prospects", [])),
                            "calendar_task_timings": build_calendar_timing_measurement(boundary_timings),
                        })
                        checkpoint_path = self.write_play_audit_checkpoint(
                            audit=audit, identity=identity,
                            completed_weeks=index + 1, target_weeks=weeks,
                            methods=methods, snapshots=snapshots,
                            output_cursor={"completed_weeks": index + 1},
                            status="time_limit", world_state=world_state,
                            time_limit_seconds=time_limit_seconds,
                            stop_reason="time_limit",
                        )
                        self.write_play_audit_manifest_row(
                            identity=identity,
                            completed_weeks=index + 1,
                            status="time_limit",
                            report_path=self.play_audit_report_path(years, seed=seed),
                            checkpoint_path=checkpoint_path,
                            time_limit_seconds=time_limit_seconds,
                        )
                    except Exception as exc:
                        checkpoint_notes.append(
                            f"Time-limit checkpoint unavailable at week {index + 1}: {type(exc).__name__}: {exc}"
                        )
                    audit_stopped = True
                    audit_stop_reason = "time_limit"
                    checkpoint_notes.append(
                        f"Stopped safely at week {index + 1} after the {time_limit_seconds}-second audit limit; resume from the retained weekly checkpoint."
                    )
                    break
                if (index + 1) % 48 == 0:
                    active = [fighter for fighter in audit.all_fighter_objects() if not fighter.retired]
                    viable = [promo for promo in audit.promotions if promo.cash > 0 and promo.stability >= 20]
                    promo_cash = [promo.cash for promo in audit.promotions]
                    sport_events = sum(
                        _audit_collection_count(world.get("events", 0))
                        for world in getattr(audit, "combat_sport_worlds", {}).values()
                        if isinstance(world, dict)
                    )
                    academy = getattr(audit, "academy", {}) or {}
                    snapshots.append({
                        "year": 2026 + (index + 1) // 48,
                        "promotions": len(audit.promotions),
                        "viable": len(viable),
                        "distressed": sum(1 for promo in audit.promotions if promo.cash < 0 or promo.stability < 20),
                        "active": len(active),
                        "free_agents": len(audit.free_agents),
                        "retired": len(audit.retired_fighters),
                        "elite": sum(1 for fighter in active if fighter.overall >= 80),
                        "avg_cash": round(sum(promo_cash) / max(1, len(promo_cash))),
                        "min_cash": min(promo_cash) if promo_cash else 0,
                        "sport_events": sport_events,
                        "academy_size": len(academy.get("prospects", [])),
                        "calendar_task_timings": build_calendar_timing_measurement(boundary_timings),
                    })
                    try:
                        # Serialize once for both the checkpoint and the
                        # descriptive measurement.  This keeps the audit
                        # evidence aligned with the exact saved boundary and
                        # avoids a second read/migration pass.
                        world_state = audit.serialize_world()
                        snapshots[-1].update(build_audit_measurement(
                            world_state, year=snapshots[-1].get("year"),
                        ))
                        latest_measurement = deepcopy(snapshots[-1])
                        hard_invariant_findings = audit_hard_invariant_findings(world_state)
                        balance_findings = audit_balance_findings(snapshots, target_years=years)
                        measurement_findings = audit_measurement_evidence_findings(snapshots)
                        blocking_balance_findings = [
                            finding for finding in balance_findings
                            if finding.get("severity") == "error"
                        ]
                        snapshots[-1]["hard_invariant_findings"] = deepcopy(hard_invariant_findings)
                        snapshots[-1]["balance_findings"] = deepcopy(balance_findings)
                        snapshots[-1]["measurement_findings"] = deepcopy(measurement_findings)
                        checkpoint_status = (
                            "failed_invariant" if hard_invariant_findings or blocking_balance_findings else
                            "time_limit" if time_limit_reached and index + 1 < weeks else
                            "complete" if index + 1 >= weeks else "paused"
                        )
                        checkpoint_path = self.write_play_audit_checkpoint(
                            audit=audit, identity=identity,
                            completed_weeks=index + 1, target_weeks=weeks,
                            methods=methods, snapshots=snapshots,
                            output_cursor={"completed_weeks": index + 1},
                            status=checkpoint_status,
                            world_state=world_state,
                            time_limit_seconds=time_limit_seconds if checkpoint_status == "time_limit" else None,
                            stop_reason="time_limit" if checkpoint_status == "time_limit" else None,
                        )
                        # Index every durable boundary, not only the eventual
                        # terminal report.  If a long audit is interrupted
                        # after a valid yearly checkpoint, the paused run
                        # remains discoverable and can be resumed explicitly.
                        try:
                            self.write_play_audit_manifest_row(
                                identity=identity,
                                completed_weeks=index + 1,
                                status=checkpoint_status,
                                report_path=self.play_audit_report_path(years, seed=seed),
                                checkpoint_path=checkpoint_path,
                                time_limit_seconds=time_limit_seconds if checkpoint_status == "time_limit" else None,
                            )
                        except (OSError, UnicodeError, ValueError, TypeError) as exc:
                            checkpoint_notes.append(
                                f"Audit manifest unavailable at week {index + 1}: {type(exc).__name__}: {exc}"
                            )
                        if hard_invariant_findings or blocking_balance_findings:
                            audit_stopped = True
                            audit_stop_reason = "failed_invariant"
                            checkpoint_notes.append(
                                f"Stopped safely at week {index + 1}: {len(hard_invariant_findings) + len(blocking_balance_findings)} blocking finding(s) retained in the checkpoint."
                            )
                            break
                        if time_limit_reached and index + 1 < weeks:
                            audit_stopped = True
                            audit_stop_reason = "time_limit"
                            checkpoint_notes.append(
                                f"Stopped safely at week {index + 1} after the {time_limit_seconds}-second audit limit; resume from the retained yearly checkpoint."
                            )
                            break
                    except Exception as exc:
                        # A checkpoint failure must not corrupt the active save
                        # or leave a partial file. Keep the audit result but
                        # make the missing resume guarantee explicit.
                        checkpoint_notes.append(f"Checkpoint unavailable at week {index + 1}: {type(exc).__name__}: {exc}")
                    boundary_timings = []
                if (index + 1) % 96 == 0:
                    self.root.update_idletasks()
            total = sum(methods.values())
            finish_count = sum(count for method, count in methods.items() if method not in ("Decision", "Draw"))
            # A time-limited run may stop before its first yearly boundary.
            # Use a current-world diagnostic projection for the report, while
            # keeping the durable yearly snapshot list unchanged and honest.
            if latest_measurement is None:
                try:
                    latest_measurement = build_audit_measurement(
                        audit.serialize_world(), year=2026 + completed_weeks // 48,
                    )
                except Exception:
                    latest_measurement = {}
            last = latest_measurement if isinstance(latest_measurement, dict) else (
                snapshots[-1] if snapshots else {}
            )
            if not isinstance(last, dict):
                last = {}
            balance_findings = audit_balance_findings(snapshots, target_years=years)
            measurement_findings = audit_measurement_evidence_findings(snapshots)
            accounting = build_audit_report_accounting(methods, snapshots, completed_weeks, weeks)
            active = [fighter for fighter in audit.all_fighter_objects() if not fighter.retired]
            by_gender, by_weight_gender = {}, {}
            for fighter in active:
                by_gender[fighter.gender] = by_gender.get(fighter.gender, 0) + 1
                key = (fighter.gender, fighter.weight)
                by_weight_gender[key] = by_weight_gender.get(key, 0) + 1
            promotion_rows = sorted(
                [(
                    promo.name,
                    promo.cash,
                    promo.stability,
                    getattr(promo, "popularity", getattr(promo, "reputation_score", 0)),
                    _audit_collection_count(getattr(promo, "roster", [])),
                    getattr(promo, "strategy", ""),
                ) for promo in audit.promotions],
                key=lambda row: row[1],
            )
            sport_rows = []
            for sport, world in getattr(audit, "combat_sport_worlds", {}).items():
                if not isinstance(world, dict):
                    continue
                roster = world.get("roster", [])
                if not isinstance(roster, (list, tuple)):
                    roster = []
                valid_roster = [fighter for fighter in roster if hasattr(fighter, "overall")]
                sport_rows.append((
                    sport,
                    len(valid_roster),
                    world.get("promotion", ""),
                    world.get("champion", ""),
                    _audit_collection_count(world.get("events", 0)),
                    round(sum(fighter.overall for fighter in valid_roster) / max(1, len(valid_roster)), 1),
                ))
            warnings = []
            if accounting.get("errors"):
                warnings.append("Report accounting is incomplete: " + "; ".join(accounting["errors"]))
            if audit_stopped:
                if audit_stop_reason == "time_limit":
                    warnings.append(
                        f"Audit stopped safely at the configured {time_limit_seconds}-second limit; no auto-repair was attempted."
                    )
                else:
                    warnings.append("Audit stopped safely after a blocking finding; no auto-repair was attempted.")
            for finding in balance_findings:
                if finding.get("severity") == "warning":
                    warnings.append(f"{finding.get('code')}: {finding.get('detail')}")
            for finding in measurement_findings:
                warnings.append(f"evidence {finding.get('code')}: {finding.get('detail')}")
            if last.get("active", 0) < 350:
                warnings.append(f"Active fighter pool is thin late-era ({last.get('active', 0)} active). Replenishment may need a boost.")
            if last.get("free_agents", 0) < 45:
                warnings.append(f"Free-agent pool is low ({last.get('free_agents', 0)}). AI/player signings may feel starved.")
            if last.get("distressed", 0) >= max(2, last.get("promotions", 0) // 4):
                warnings.append(f"Promotion finance pressure is high ({last.get('distressed', 0)} distressed companies).")
            if last.get("elite", 0) < 25:
                warnings.append(f"Elite population is low ({last.get('elite', 0)} at 80+ OVR). Development/regen may be too stingy.")
            if methods.get("Decision", 0) / max(1, total) > 0.62:
                warnings.append("Decision rate is high for the full world. Check fight-engine/card matchmaking by tier.")
            if not warnings:
                warnings.append("No major red flags detected from headline balance metrics.")
            report = [
                f"{years}-YEAR PLAY-LEVEL AUDIT ({'resumed' if checkpoint else 'fresh'} spectator world; "
                f"{('stopped at time limit' if audit_stop_reason == 'time_limit' else 'stopped on blocking finding') if audit_stopped else 'complete'})",
                f"Weeks simulated: {completed_weeks:,}/{weeks:,} | Fights: {total:,} | Seed: {seed}",
                f"Audit wall-clock limit: {time_limit_seconds:,} seconds",
                f"Source/configuration identity: {identity.get('identity_digest', '')[:16]}",
                f"Finish rate: {finish_count / max(1, total) * 100:.1f}% | Decision rate: {methods.get('Decision', 0) / max(1, total) * 100:.1f}%",
                f"Report accounting: {accounting.get('snapshot_count', 0)} yearly boundary row(s) / {accounting.get('expected_year_boundaries', 0)} expected; {len(accounting.get('errors', []))} error(s)",
                "",
                "BALANCE WARNINGS:",
            ]
            report.extend(f"- {warning}" for warning in warnings)
            report.extend(["", "METHOD DISTRIBUTION:"])
            report.extend(f"- {method}: {count:,} ({count / max(1, total) * 100:.1f}%)" for method, count in sorted(methods.items(), key=lambda item: -item[1]))
            report.extend(["", "YEARLY WORLD HEALTH:", "Year | Promotions | Viable | Distressed | Active | FAs | Retired | 80+ | Titles | History | Avg Cash | Min Cash | Sport Cards | Academy"])
            for row in snapshots:
                report.append(f"{row['year']} | {row['promotions']} | {row['viable']} | {row['distressed']} | {row['active']} | {row['free_agents']} | {row['retired']} | {row['elite']} | {row.get('title_holders', 0)} | {row.get('history_total', 0)} | ${row['avg_cash']:,} | ${row['min_cash']:,} | {row['sport_events']} | {row['academy_size']}")
            timing = last.get("calendar_task_timings", {}) if isinstance(last.get("calendar_task_timings"), dict) else {}
            def _audit_seconds(value):
                try:
                    parsed = float(value)
                except (TypeError, ValueError, OverflowError):
                    return 0.0
                return parsed if parsed >= 0 and parsed < 7_200 else 0.0
            def _audit_count(value):
                try:
                    return max(0, min(1_000_000, int(value or 0)))
                except (TypeError, ValueError, OverflowError):
                    return 0
            def _audit_money(value):
                try:
                    parsed = float(value)
                except (TypeError, ValueError, OverflowError):
                    return 0
                if not math.isfinite(parsed):
                    return 0
                return max(-1_000_000_000, min(1_000_000_000, int(parsed)))
            report.extend([
                "",
                "SUPPLY / COMMITMENT EVIDENCE:",
                f"Free agents: {last.get('free_agents', 0)} | Eligible non-champion challengers: {last.get('eligible_title_challengers', 0)} | "
                f"Vacant titles: {last.get('title_vacancies', 0)} | Vacancy duration: {last.get('vacancy_duration_total_weeks', 0)} total weeks / "
                f"{last.get('vacancy_duration_max_weeks', 0)} max weeks | Expired offers: {last.get('expired_offers', 0)}",
                f"Calendar task timing: {_audit_count(timing.get('count', 0))} samples | {_audit_seconds(timing.get('total_seconds', 0)):.3f}s total | {_audit_seconds(timing.get('max_seconds', 0)):.3f}s max",
            ])
            timing_rows = timing.get("by_task", {}) if isinstance(timing.get("by_task"), dict) else {}
            if timing_rows:
                report.append("Timing by task: " + ", ".join(
                    f"{label} {_audit_count(row.get('count', 0))}x/{_audit_seconds(row.get('total_seconds', 0)):.3f}s"
                    for label, row in list(timing_rows.items())[:24] if isinstance(row, dict)
                ))
            cohorts = last.get("cohort_measurements", {}) if isinstance(last.get("cohort_measurements"), dict) else {}
            report.extend(["", "COHORT / EVENT / IDENTITY EVIDENCE:"])
            for cohort_key, label in (
                ("player", "Player"),
                ("ai_promotions", "AI promotions"),
                ("owned_child", "Owned child promotions"),
            ):
                cohort = cohorts.get(cohort_key, {}) if isinstance(cohorts.get(cohort_key), dict) else {}
                report.append(
                    f"{label}: {_audit_count(cohort.get('active_talent', 0))} active talent | "
                    f"{_audit_count(cohort.get('division_count', 0))} divisions | "
                    f"{_audit_count(cohort.get('staff', 0))} staff | "
                    f"{_audit_count(cohort.get('scheduled_events', 0))} scheduled event(s)"
                )
            event_counts = last.get("event_counts", {}) if isinstance(last.get("event_counts"), dict) else {}
            report.append(
                "Event coverage: " + ", ".join(
                    f"{key}={_audit_count(event_counts.get(key, 0))}"
                    for key in ("player_scheduled", "ai_scheduled", "owned_child_scheduled", "owned_sport_scheduled")
                )
            )
            identity_quality = last.get("identity_quality", {}) if isinstance(last.get("identity_quality"), dict) else {}
            identity_parts = []
            for key in ("fighter_id", "promotion_id", "event_id"):
                evidence = identity_quality.get(key, {}) if isinstance(identity_quality.get(key), dict) else {}
                identity_parts.append(
                    f"{key} missing={_audit_count(evidence.get('missing', 0))}/duplicates={_audit_count(evidence.get('duplicates', 0))}"
                )
            report.append("Identity quality: " + "; ".join(identity_parts))
            report.extend(["", "ROSTER POPULATION BY GENDER:"])
            report.extend(f"- {gender}: {count}" for gender, count in sorted(by_gender.items()))
            report.extend(["", "ROSTER POPULATION BY WEIGHT/GENDER:"])
            for (gender, weight), count in sorted(by_weight_gender.items(), key=lambda item: (item[0][0], WEIGHTS.index(item[0][1]) if item[0][1] in WEIGHTS else 99)):
                report.append(f"- {gender} {weight}: {count}")
            report.extend(["", "COMPANY FINANCIAL HEALTH (poorest first):", "Company | Cash | Stability | Popularity | Roster | Strategy"])
            for row in promotion_rows[:18]:
                report.append(f"{row[0]} | ${row[1]:,} | {row[2]} | {row[3]} | {row[4]} | {row[5] or 'Balanced'}")
            report.extend(["", "COMBAT SPORT IMPACT:", "Sport | Roster | AI Promotion | Champion | Cards | Avg OVR"])
            report.extend(f"{sport} | {size} | {promotion} | {champion or 'Vacant'} | {events} | {avg_ovr}" for sport, size, promotion, champion, events, avg_ovr in sport_rows)
            report.extend(["", "LATEST DIAGNOSTIC DETAIL:", "Company | Active Roster | Divisions | Eligible Challengers | Cash | Stability | Staff | Scheduled | Open Projects | Week Transactions | History Weeks"])
            for row in (last.get("company_measurements", []) or [])[:40]:
                report.append(
                    f"{row.get('name', '')} | {_audit_count(row.get('active_roster', 0))} | {len(row.get('division_counts', {}) or {}) if isinstance(row.get('division_counts', {}), dict) else 0} | "
                    f"{_audit_count(row.get('eligible_title_challengers', 0))} | ${_audit_money(row.get('cash', 0)):,} | "
                    f"{row.get('stability', 0)} | {row.get('staff', 0)} | {row.get('scheduled_events', 0)} | "
                    f"{row.get('open_super_event_items', 0)} | {row.get('week_transactions', 0)} | {row.get('weekly_history', 0)}"
                )
            report.append("Division cohorts: " + ", ".join(
                f"{key}={value}" for key, value in (last.get("division_counts", {}) or {}).items()
            ) if last.get("division_counts") else "Division cohorts: no active fighters recorded")
            report.append("Backlogs: " + ", ".join(
                f"{key}={value}" for key, value in (last.get("backlogs", {}) or {}).items()
            ))
            report.append("Archive sizes: " + ", ".join(
                f"{key}={value}" for key, value in (last.get("archive_sizes", {}) or {}).items()
            ))
            if hard_invariant_findings:
                report.extend(["", "HARD INVARIANT FINDINGS:"])
                report.extend(
                    f"- {row.get('code')}: {row.get('path')} — {row.get('detail')}"
                    for row in hard_invariant_findings
                )
            if balance_findings:
                report.extend(["", "BALANCE FINDINGS (YEARLY EVIDENCE):"])
                report.extend(
                    f"- [{row.get('severity', 'warning').upper()}] {row.get('code')}: {row.get('path')} — {row.get('detail')}"
                    for row in balance_findings
                )
            if measurement_findings:
                report.extend(["", "MEASUREMENT EVIDENCE FINDINGS:"])
                report.extend(
                    f"- [{row.get('severity', 'warning').upper()}] {row.get('code')}: {row.get('path')} — {row.get('detail')}"
                    for row in measurement_findings
                )
            report.extend(["", f"FINAL: {last.get('promotions', 0)} promotions ({last.get('viable', 0)} viable), {last.get('active', 0)} active fighters, {last.get('free_agents', 0)} free agents, {last.get('retired', 0)} retired, {last.get('elite', 0)} elite fighters."])
            report.extend(["", "AUDIT CHECKPOINT:", f"Latest isolated checkpoint: {self.play_audit_checkpoint_path(years, seed=seed)}"])
            report.extend(f"- {note}" for note in checkpoint_notes)
        except Exception as exc:
            report = [f"{years}-year audit failed:", f"{type(exc).__name__}: {exc}", traceback.format_exc()]
        finally:
            random.setstate(original_state)
            audit_root.destroy()
        self.audit_text.config(state="normal")
        self.audit_text.delete("1.0", "end")
        self.audit_text.insert("end", "\n".join(report))
        self.audit_text.config(state="disabled")
        self.play_audit_report = "\n".join(report)
        report_path = self.play_audit_report_path(years, seed=seed)
        try:
            report_path = self.write_play_audit_report(self.play_audit_report, years=years, seed=seed)
        except (OSError, UnicodeError, ValueError) as exc:
            self.play_audit_report += f"\n\nRaw report persistence unavailable: {type(exc).__name__}: {exc}"
        audit_status = (
            "complete" if report and "PLAY-LEVEL AUDIT" in report[0] and not audit_stopped
            else "time_limit" if report and "PLAY-LEVEL AUDIT" in report[0] and audit_stop_reason == "time_limit"
            else "failed_invariant" if report and "PLAY-LEVEL AUDIT" in report[0]
            else "failed"
        )
        try:
            self.write_play_audit_manifest_row(
                identity=identity,
                completed_weeks=completed_weeks,
                status=audit_status,
                report_path=report_path,
                checkpoint_path=self.play_audit_checkpoint_path(years, seed=seed),
                time_limit_seconds=time_limit_seconds if audit_status == "time_limit" else None,
            )
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            self.play_audit_report += f"\n\nAudit manifest persistence unavailable: {type(exc).__name__}: {exc}"
        if hasattr(self, "play_audit_progress"):
            if report and "PLAY-LEVEL AUDIT" in report[0] and not audit_stopped:
                self.play_audit_progress.configure(value=weeks)
                self.play_audit_status.config(text=f"{years}-year play audit: complete - results shown below")
                if hasattr(self, "view_play_audit_button"):
                    self.view_play_audit_button.configure(state="normal")
            elif report and "PLAY-LEVEL AUDIT" in report[0]:
                self.play_audit_progress.configure(value=completed_weeks)
                status_text = (
                    f"{years}-year play audit: stopped at time limit - resume when ready"
                    if audit_stop_reason == "time_limit"
                    else f"{years}-year play audit: stopped on blocking finding - review results"
                )
                self.play_audit_status.config(text=status_text)
                if hasattr(self, "view_play_audit_button"):
                    self.view_play_audit_button.configure(state="normal")
            else:
                self.play_audit_status.config(text=f"{years}-year play audit: failed - see report below")

    def open_play_level_audit_results(self):
        report = getattr(self, "play_audit_report", "")
        if not report:
            try:
                years = max(1, min(100, int(self.play_audit_years.get()))) if hasattr(self, "play_audit_years") else 30
            except (TypeError, ValueError):
                years = 30
            report = self.read_play_audit_report(years=years, seed=self.play_audit_seed_value())
            if report:
                self.play_audit_report = report
                if hasattr(self, "audit_text"):
                    self.audit_text.config(state="normal")
                    self.audit_text.delete("1.0", "end")
                    self.audit_text.insert("end", report)
                    self.audit_text.config(state="disabled")
        if not report:
            if not self._simulation_status_notice("Run a play audit first; its results will appear here when complete.", warning=True):
                messagebox.showinfo("Play Audit", "Run a play audit first.")
            return
        window = self.create_managed_window()
        try:
            years = max(1, min(100, int(self.play_audit_years.get()))) if hasattr(self, "play_audit_years") else 30
        except (TypeError, ValueError):
            years = 30
        window.title(f"{years}-Year Play Audit Results")
        window.geometry("940x680")
        window.minsize(720, 480)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"{years}-YEAR PLAY AUDIT RESULTS", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
        frame = ttk.Frame(window, style="Panel.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        text = tk.Text(frame, wrap="none", font=("Courier New", 10), bg=self.colors["cream"], fg=self.colors["text"], padx=12, pady=12)
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text.insert("end", report)
        text.config(state="disabled")
        buttons = ttk.Frame(window, style="Panel.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        export_status_var = tk.StringVar(value="The report is read-only. Export a copy when you need to share the findings.")
        ttk.Label(window, textvariable=export_status_var, style="Inset.TLabel", anchor="w", justify="left", wraplength=900).pack(fill="x", padx=12, pady=(0, 5))

        def export_report():
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            path = LOG_DIR / f"play_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path.write_text(report, encoding="utf-8")
            export_status_var.set(f"Exported audit report to {path}. The active career and audit evidence were not changed.")

        ttk.Button(buttons, text="Export Results", command=export_report).pack(side="left")
        ttk.Button(buttons, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right")

    def unique_fighter_rows(self, rows):
        unique = []
        seen = set()
        for row in rows:
            if row[0] in seen:
                continue
            unique.append(row)
            seen.add(row[0])
        return unique

    def belt_key(self, gender, weight):
        return f"{gender} {weight}"

    def promotion_division_open(self, promo, gender, weight):
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        closed = self.company_closed_divisions(promo)
        return weight in weights and self.belt_key(gender, weight) not in closed

    def blank_belts(self):
        return {self.belt_key(gender, weight): "" for gender in ("Male", "Female") for weight in WEIGHTS}

    def blank_belt_history(self):
        return {self.belt_key(gender, weight): [] for gender in ("Male", "Female") for weight in WEIGHTS}

    def normalize_belts(self, belts):
        normalized = self.blank_belts()
        source = belts if isinstance(belts, dict) else {}
        for key, value in source.items():
            if key in normalized:
                normalized[key] = value
            elif key in WEIGHTS:
                normalized[self.belt_key("Male", key)] = value
        return normalized

    def normalize_belt_history(self, history):
        normalized = self.blank_belt_history()
        source = history if isinstance(history, dict) else {}
        for key, entries in source.items():
            entries = list(entries) if isinstance(entries, (list, tuple)) else []
            if key in normalized:
                normalized[key] = entries
            elif key in WEIGHTS:
                normalized[self.belt_key("Male", key)] = entries
        return normalized

    def normalize_special_belts(self, belts):
        """Normalize player-created championships such as BMF without mixing them into divisions."""
        normalized = {}
        source = belts if isinstance(belts, dict) else {}
        for key, value in source.items():
            name = str((value or {}).get("name", key) if isinstance(value, dict) else key).strip()
            if not name:
                continue
            row = dict(value) if isinstance(value, dict) else {}
            row["name"] = name
            row["holder"] = str(row.get("holder", "") or "")
            row["holder_id"] = str(row.get("holder_id", "") or "")
            try:
                row["defenses"] = max(0, int(row.get("defenses", 0) or 0))
            except (TypeError, ValueError):
                row["defenses"] = 0
            raw_history = row.get("history", [])
            row["history"] = list(raw_history)[:80] if isinstance(raw_history, (list, tuple)) else []
            normalized[name] = row
        return normalized

    def award_special_belt(self, belt_name, winner, loser, method):
        self.special_belts = self.normalize_special_belts(getattr(self, "special_belts", {}))
        belt = self.special_belts.get(belt_name)
        if not belt:
            return False
        previous = belt.get("holder", "")
        previous_id = str(belt.get("holder_id", "") or "")
        defense = previous_id == winner.fighter_id if previous_id else previous == winner.name
        belt["holder"] = winner.name
        belt["holder_id"] = winner.fighter_id
        belt["defenses"] = belt.get("defenses", 0) + (1 if defense else 0)
        action = "Defense" if defense else "Champion Crowned"
        belt["history"].insert(0, {
            "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
            "action": action, "fighter": winner.name, "fighter_id": winner.fighter_id, "previous": previous, "previous_id": previous_id,
            "note": f"Defeated {loser.name} by {method}.",
        })
        belt["history"] = belt["history"][:80]
        winner.special_titles = list(getattr(winner, "special_titles", None) or [])
        if belt_name not in winner.special_titles:
            winner.special_titles.append(belt_name)
        if previous and not defense:
            former = next((fighter for fighter in self.roster if fighter.fighter_id == previous_id), None) if previous_id else None
            if former is None:
                matches = [fighter for fighter in self.roster if fighter.name == previous]
                former = matches[0] if len(matches) == 1 else None
            if former:
                former.special_titles = [name for name in (getattr(former, "special_titles", None) or []) if name != belt_name]
        return True

    def vacate_special_belts_held_by(self, fighter, reason, *, owner=None):
        """Vacate every named belt held by ``fighter`` on one promotion.

        ``self`` is normally the owning player company, but child-promotion
        departures must pass that promotion explicitly.  Keeping the owner
        boundary here prevents a child exit from accidentally mutating the
        player's special-belt catalogue.  Only titles actually found in the
        owner's catalogue are removed from ``fighter.special_titles`` so a
        fighter holding different named belts for another promotion keeps
        those historical/current associations intact.
        """
        title_owner = owner if owner is not None else self
        normalized = self.normalize_special_belts(getattr(title_owner, "special_belts", {}))
        title_owner.special_belts = normalized
        vacated_names = set()
        fighter_id = str(getattr(fighter, "fighter_id", "") or "")
        fighter_name = str(getattr(fighter, "name", "") or "")
        for belt_name, belt in normalized.items():
            holder_id = str(belt.get("holder_id", "") or "")
            if (holder_id and holder_id != fighter_id) or (not holder_id and belt.get("holder") != fighter_name):
                continue
            belt["holder"] = ""
            belt["holder_id"] = ""
            vacated_names.add(belt_name)
            belt["history"].insert(0, {
                "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
                "action": "Vacated", "fighter": fighter_name, "fighter_id": fighter_id,
                "previous": fighter_name, "previous_id": fighter_id, "note": reason,
            })
            belt["history"] = belt["history"][:80]
        if vacated_names:
            fighter.special_titles = [
                name for name in (getattr(fighter, "special_titles", None) or [])
                if name not in vacated_names
            ]

    def belt_history_entry(self, action, key, fighter_name="", note="", fighter_id=""):
        entry = {
            "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
            "action": action,
            "division": key,
            "fighter": fighter_name,
            "fighter_id": str(fighter_id or ""),
            "note": note,
        }
        # A title change belongs to the day its card ran, so a lineage reads as
        # a sequence of dated events rather than a list of weeks. Fighter fight
        # histories deliberately stay week-level.
        day = getattr(self, "_active_card_day", None)
        if day is not None:
            entry["day"] = self.normalize_day(day)
        return entry

    def record_belt_history(self, history, key, action, fighter_name="", note="", fighter_id=""):
        history = self.normalize_belt_history(history)
        history[key].insert(0, self.belt_history_entry(action, key, fighter_name, note, fighter_id))
        return history

    def set_primary_champion(self, roster, belts, belt_history, champion, note, defense=False, appointed=False):
        key = self.belt_key(champion.gender, champion.weight)
        belts = self.normalize_belts(belts)
        belt_history = self.normalize_belt_history(belt_history)
        previous = belts.get(key, "")
        for fighter in roster:
            if fighter.gender == champion.gender and fighter.weight == champion.weight:
                is_champion = fighter is champion or self.fighter_identity_key(fighter) == self.fighter_identity_key(champion)
                fighter.champion = is_champion
                if is_champion:
                    fighter.interim_champion = False
        belts[key] = champion.name
        if previous != champion.name:
            prior_lineage = bool(belt_history.get(key))
            action = "Champion Crowned" if previous or prior_lineage else ("Inaugural Champion Appointed" if appointed else "Inaugural Champion")
            belt_history = self.record_belt_history(belt_history, key, action, champion.name, note, champion.fighter_id)
            if not appointed:
                champion.title_wins = getattr(champion, "title_wins", 0) + 1
        elif defense:
            champion.title_defenses = getattr(champion, "title_defenses", 0) + 1
            belt_history = self.record_belt_history(belt_history, key, "Title Defense", champion.name, note, champion.fighter_id)
        return belts, belt_history

    def set_interim_champion(self, roster, interim_belts, belt_history, champion, note):
        key = self.belt_key(champion.gender, champion.weight)
        interim_belts = self.normalize_belts(interim_belts)
        belt_history = self.normalize_belt_history(belt_history)
        previous = interim_belts.get(key, "")
        for fighter in roster:
            if fighter.gender == champion.gender and fighter.weight == champion.weight:
                fighter.interim_champion = fighter is champion or self.fighter_identity_key(fighter) == self.fighter_identity_key(champion)
        interim_belts[key] = champion.name
        if previous != champion.name:
            belt_history = self.record_belt_history(belt_history, key, "Interim Champion Crowned", champion.name, note, champion.fighter_id)
            champion.interim_title_wins = getattr(champion, "interim_title_wins", 0) + 1
        else:
            champion.interim_title_defenses = getattr(champion, "interim_title_defenses", 0) + 1
            belt_history = self.record_belt_history(belt_history, key, "Interim Title Defense", champion.name, note, champion.fighter_id)
        return interim_belts, belt_history

    def clear_interim_belt(self, roster, interim_belts, belt_history, key, note):
        interim_belts = self.normalize_belts(interim_belts)
        holder = interim_belts.get(key, "")
        if holder:
            matches = [fighter for fighter in (roster or []) if fighter.name == holder]
            # Legacy interim maps store only a display name.  With duplicate
            # names, clear the flag only for the explicitly marked holder and
            # fail closed when no identity-safe flag can disambiguate them.
            marked = [fighter for fighter in matches if getattr(fighter, "interim_champion", False)]
            if len(matches) == 1 or len(marked) == 1:
                target = matches[0] if len(matches) == 1 else marked[0]
                target.interim_champion = False
                interim_belts[key] = ""
                belt_history = self.record_belt_history(
                    belt_history, key, "Interim Belt Cleared", holder, note,
                    getattr(target, "fighter_id", ""),
                )
        return interim_belts, belt_history

    def record_orphaned_title_vacancy(self, belt_history, key, holder, reason, *, interim=False):
        """Retain a name-only vacancy when a saved holder is no longer present.

        Reconciliation can encounter a belt map whose fighter has already
        disappeared from the source roster.  There is no safe identity to
        attach in that situation, so keep the display name and an explicit
        incomplete-coverage note rather than guessing a same-name fighter.
        The belt map is cleared by the caller after this fact is recorded.
        """
        history = self.normalize_belt_history(belt_history)
        holder = str(holder or "")
        if not holder:
            return history
        action = "Interim Vacated" if interim else "Vacated"
        note = (
            f"{reason} No matching roster identity was available; retained as a "
            "name-only vacancy for manual review."
        )
        if not any(
            isinstance(entry, dict)
            and entry.get("action") == action
            and str(entry.get("fighter", "") or "") == holder
            and str(entry.get("note", "") or "") == note
            for entry in history.get(key, [])
        ):
            history = self.record_belt_history(history, key, action, holder, note, "")
        return history

    def interim_title_participates(self, interim_belts, winner, loser):
        key = self.belt_key(winner.gender, winner.weight)
        holder = self.normalize_belts(interim_belts).get(key, "")
        return bool(holder and holder in {winner.name, loser.name})

    def vacate_fighter_belts(self, fighter, roster, belts, interim_belts, belt_history, reason):
        key = self.belt_key(fighter.gender, fighter.weight)
        belts = self.normalize_belts(belts)
        interim_belts = self.normalize_belts(interim_belts)
        belt_history = self.normalize_belt_history(belt_history)
        # Legacy belt maps retain the holder's display name, but duplicate
        # names are valid.  A departing non-holder must not vacate the actual
        # champion's belt merely because their label matches; use the live
        # champion flag when available and only fall back to name equality for
        # an unambiguous legacy roster.
        same_name = [
            item for item in (roster or [])
            if str(getattr(item, "name", "") or "") == str(getattr(fighter, "name", "") or "")
        ]
        is_named_holder = bool(getattr(fighter, "champion", False)) or len(same_name) <= 1
        if belts.get(key) == fighter.name and is_named_holder:
            belts[key] = ""
            fighter.champion = False
            belt_history = self.record_belt_history(belt_history, key, "Vacated", fighter.name, reason, fighter.fighter_id)
            if roster is getattr(self, "roster", None):
                self.queue_vacant_title_alert(key, f"{fighter.name}'s reign ended. Reason: {reason}", getattr(fighter, "fighter_id", ""))
        is_named_interim_holder = bool(getattr(fighter, "interim_champion", False)) or len(same_name) <= 1
        if interim_belts.get(key) == fighter.name and is_named_interim_holder:
            interim_belts[key] = ""
            fighter.interim_champion = False
            belt_history = self.record_belt_history(belt_history, key, "Interim Vacated", fighter.name, reason, fighter.fighter_id)
        return belts, interim_belts, belt_history

    def queue_vacant_title_alert(self, key, reason="No champion is currently recognized.", fighter_id=""):
        """Create one actionable player alert per unresolved vacant title."""
        if not hasattr(self, "inbox"):
            return
        subject = f"Vacant Championship - {key}"
        if any(message.get("subject") == subject and not message.get("resolved", False) for message in self.inbox):
            return
        self.inbox.append({
            "subject": subject,
            "body": f"The {key} championship is vacant. {reason} Book a title fight to crown the next champion; no replacement will be appointed automatically.",
            "type": "Roster",
            "resolved": False,
            "fighter_id": fighter_id,
            "action": "booking",
        })

    def sync_player_vacant_title_alerts(self):
        """Alert on valid vacancies and retire the warning once a belt is filled."""
        if getattr(self, "spectator_mode", False) or not hasattr(self, "inbox"):
            return
        belts = self.normalize_belts(getattr(self, "belts", {}))
        closed = set(getattr(self, "closed_divisions", set()))
        active_vacancies = set()
        for weight in WEIGHTS:
            for gender in ("Male", "Female"):
                key = self.belt_key(gender, weight)
                depth = sum(not fighter.retired and fighter.gender == gender and fighter.weight == weight for fighter in self.roster)
                if key not in closed and depth >= 2 and not belts.get(key):
                    active_vacancies.add(key)
                    self.queue_vacant_title_alert(key)
        for message in self.inbox:
            subject = str(message.get("subject", ""))
            if subject.startswith("Vacant Championship - ") and subject.removeprefix("Vacant Championship - ") not in active_vacancies:
                message["resolved"] = True

    def champion_sort_value(self, fighter):
        return fighter.overall * 1.35 + fighter.popularity * 0.62 + fighter.momentum * 8 + fighter.record_w * 1.4 - fighter.record_l * 2

    def repair_appointed_title_credits(self):
        """Appointments establish a belt holder but are not championship wins."""
        if int(getattr(self, "rules", {}).get("appointment_title_credit_version", 0) or 0) >= 1:
            return
        fighter_lookup = {fighter.name: fighter for fighter in list(self.roster) + list(self.free_agents) + list(self.retired_fighters)}
        for entries in self.normalize_belt_history(getattr(self, "belt_history", {})).values():
            for entry in entries:
                action = str(entry.get("action", ""))
                note = str(entry.get("note", "")).lower()
                if "appointed" not in action.lower() and not (action == "Inaugural Champion" and "status normalized" in note):
                    continue
                fighter = fighter_lookup.get(entry.get("fighter", ""))
                if fighter and getattr(fighter, "title_wins", 0) > 0:
                    fighter.title_wins -= 1
        self.rules["appointment_title_credit_version"] = 1

    def review_player_champion_credibility(self):
        """Stop appointed player champions retaining belts through prolonged non-title failure."""
        self.repair_appointed_title_credits()
        if getattr(self, "spectator_mode", False) or getattr(self, "month", 1) < 6:
            return
        self.belts = self.normalize_belts(getattr(self, "belts", {}))
        self.interim_belts = self.normalize_belts(getattr(self, "interim_belts", {}))
        self.belt_history = self.normalize_belt_history(getattr(self, "belt_history", {}))
        for key, holder in list(self.belts.items()):
            if not holder:
                continue
            champion = next((fighter for fighter in self.roster if fighter.name == holder), None)
            if not champion:
                continue
            reign_entry = next((entry for entry in self.belt_history.get(key, []) if entry.get("fighter") == holder and entry.get("action") in ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed")), None)
            if not reign_entry:
                continue
            date_parts = str(reign_entry.get("date", "Month 1 Week 1")).split()
            try:
                reign_month = int(date_parts[1]) if date_parts and date_parts[0] == "Month" else 1
            except (ValueError, IndexError):
                reign_month = 1
            reign_bouts = []
            for bout in list(getattr(champion, "bout_rating_history", None) or []):
                parts = str(bout.get("date", "")).split()
                try:
                    bout_month = int(parts[1]) if parts and parts[0] == "Month" else 0
                except (ValueError, IndexError):
                    bout_month = 0
                if bout_month >= reign_month:
                    reign_bouts.append(bout)
            title_bouts = [bout for bout in reign_bouts if bout.get("title") or bout.get("divisional_title")]
            non_title_losses = [bout for bout in reign_bouts if bout.get("result") == "L" and not (bout.get("title") or bout.get("divisional_title"))]
            months_held = max(0, self.month - reign_month)
            appointed = "appointed" in str(reign_entry.get("action", "")).lower() or "status normalized" in str(reign_entry.get("note", "")).lower()
            reason = ""
            if len(non_title_losses) >= 2:
                reason = f"Championship credibility review: {len(non_title_losses)} non-title losses during the reign."
            elif appointed and not title_bouts:
                reason = "Championship governance review: an appointed holder must earn the vacant title in a championship fight."
            if not reason:
                continue
            self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(champion, self.roster, self.belts, self.interim_belts, self.belt_history, reason)
            self.news.insert(0, f"{key} title vacated: {champion.name} failed the championship credibility review.")

    def ensure_company_champions(self, roster, belts, company_name, region, size, player_owned=False, min_per_division=3, interim_belts=None, belt_history=None, closed_divisions=None, allow_appointed=True, existing_names=None):
        belts = self.normalize_belts(belts)
        interim_belts = self.normalize_belts(interim_belts)
        belt_history = self.normalize_belt_history(belt_history)
        existing_names = existing_names if isinstance(existing_names, set) else (set(existing_names) if existing_names is not None else self.active_fighter_names())
        existing_names.update(fighter.name for fighter in roster)
        closed = set(closed_divisions or ())
        for weight in WEIGHTS:
            for gender in ("Male", "Female"):
                key = self.belt_key(gender, weight)
                # A player can deliberately shut down an unviable division. Do
                # not silently regenerate a roster and champion during a save
                # or monthly world repair.
                if key in closed or (player_owned and key in (set(getattr(self, "closed_divisions", set())) | set(getattr(self, "player_managed_divisions", set())))):
                    belts[key] = ""
                    interim_belts[key] = ""
                    continue
                division = [fighter for fighter in roster if fighter.weight == weight and fighter.gender == gender]
                while len(division) < min_per_division:
                    fighter = self.create_generated_fighter(8, min(72, max(32, size)), 42, min(90, 50 + max(20, size) // 2), weight=weight, gender=gender)
                    self.avoid_name_collision(fighter, existing_names)
                    roster.append(self.prepare_company_generated_fighter(fighter, region, company_name, player_owned=player_owned))
                    division.append(fighter)
                holder_name = str(belts.get(key, "") or "")
                named_matches = [fighter for fighter in division if fighter.name == holder_name] if holder_name else []
                marked_matches = [fighter for fighter in named_matches if getattr(fighter, "champion", False)]
                # A name-only legacy belt is ambiguous when duplicate fighters
                # share the label.  A single explicit champion marker is the
                # only safe disambiguator; otherwise leave the saved belt and
                # flags untouched for manual review.
                if len(named_matches) > 1 and len(marked_matches) != 1:
                    continue
                current = named_matches[0] if len(named_matches) == 1 else (marked_matches[0] if len(marked_matches) == 1 else None)
                # Player vacancies are always decided in the cage. AI companies
                # may receive inaugural holders during initial world seeding,
                # but once a lineage exists their later vacancies also stay open
                # until an AI-booked title fight crowns a champion.
                if not current and (player_owned or belt_history.get(key) or not allow_appointed):
                    if holder_name:
                        belt_history = self.record_orphaned_title_vacancy(
                            belt_history, key, holder_name,
                            f"{company_name} title holder was not present during state reconciliation.",
                        )
                    belts[key] = ""
                    for fighter in division:
                        fighter.champion = False
                    champion = None
                else:
                    champion = current or max(division, key=self.champion_sort_value)
                    belts, belt_history = self.set_primary_champion(roster, belts, belt_history, champion, f"{company_name} title status normalized.", appointed=not current)
                primary_name = champion.name if champion else ""
                interim_name = str(interim_belts.get(key, "") or "")
                interim_matches = [fighter for fighter in division if fighter.name == interim_name and fighter is not champion] if interim_name else []
                interim_marked = [fighter for fighter in interim_matches if getattr(fighter, "interim_champion", False)]
                ambiguous_interim = bool(interim_name and len(interim_matches) > 1 and len(interim_marked) != 1)
                interim_holder = None if ambiguous_interim else (interim_matches[0] if len(interim_matches) == 1 else (interim_marked[0] if len(interim_marked) == 1 else None))
                if not ambiguous_interim:
                    for fighter in division:
                        fighter.interim_champion = bool(interim_holder and fighter is interim_holder)
                    if not interim_holder:
                        if interim_name:
                            belt_history = self.record_orphaned_title_vacancy(
                                belt_history, key, interim_name,
                                f"{company_name} interim holder was not present during state reconciliation.",
                                interim=True,
                            )
                        interim_belts[key] = ""
        return belts, interim_belts, belt_history

    def promotion_male_only(self, promo):
        return bool(promo is not None and getattr(promo, "name", "") == EURASIAN_FIGHT_CIRCUIT_NAME)

    def company_closed_divisions(self, promo):
        """Divisions a promotion must never staff, crown, or book.

        Every caller of ensure_company_champions has to agree on this, or a
        single-gender circuit quietly gets a women's roster generated into it
        by whichever call site forgot the rule.
        """
        closed = set(getattr(promo, "closed_divisions", None) or ())
        if self.promotion_male_only(promo):
            closed.update(self.belt_key("Female", weight) for weight in WEIGHTS)
        return closed

    def ensure_all_company_champions(self):
        existing_names = self.active_fighter_names()
        if not getattr(self, "spectator_mode", False):
            self.review_player_champion_credibility()
            self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(
                self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop,
                player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history,
                closed_divisions=self.closed_divisions, existing_names=existing_names,
            )
            self.sync_player_vacant_title_alerts()
        for promo in self.promotions:
            closed = self.company_closed_divisions(promo)
            promo.belts, promo.interim_belts, promo.belt_history = self.ensure_company_champions(
                promo.roster, promo.belts or {}, promo.name, promo.region, promo.reputation_score,
                player_owned=False, interim_belts=promo.interim_belts or {}, belt_history=promo.belt_history or {},
                closed_divisions=closed, allow_appointed=not getattr(promo, "is_regional_feeder", False),
                existing_names=existing_names,
            )

    @staticmethod
    @lru_cache(maxsize=200000)
    def fighter_name_key(name):
        """Identity of a fighter name, ignoring case and accents.

        Curated rosters spell names without diacritics while the generated
        name banks keep them, so "Diego Sanchez" and "Diego Sánchez" are not
        equal as strings and both could appear in one world. The key is always
        lower case, so it can never collide with a real Title Case name held in
        the same set.
        """
        folded = unicodedata.normalize("NFKD", str(name))
        return "".join(char for char in folded if not unicodedata.combining(char)).casefold()

    def avoid_name_collision(self, fighter, existing_names):
        parts = fighter.name.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            fighter.name = parts[0]
        if fighter.name in existing_names or self.fighter_name_key(fighter.name) in existing_names:
            fighter.name = self.generate_clean_unique_name(fighter.gender, existing_names)
        existing_names.add(fighter.name)
        existing_names.add(self.fighter_name_key(fighter.name))
        return fighter

    def generate_clean_unique_name(self, gender="Male", existing_names=None):
        existing_names = existing_names or set()
        first_names = FEMALE_FIRST_NAMES if gender == "Female" else FIRST_NAMES
        for _ in range(200):
            name = f"{random.choice(first_names)} {random.choice(LAST_NAMES)}"
            if (name not in existing_names and self.fighter_name_key(name) not in existing_names
                    and name not in self.name_counts and self.fighter_name_key(name) not in self.name_counts):
                self.name_counts[name] = 1
                self.name_counts[self.fighter_name_key(name)] = 1
                return name
        middle_names = ["Kai", "Lee", "Ray", "Jae", "Noel", "Rio", "Taj", "Vale", "Sage", "Dean"]
        for middle in middle_names:
            for _ in range(40):
                name = f"{random.choice(first_names)} {middle} {random.choice(LAST_NAMES)}"
                if (name not in existing_names and self.fighter_name_key(name) not in existing_names
                        and name not in self.name_counts and self.fighter_name_key(name) not in self.name_counts):
                    self.name_counts[name] = 1
                    self.name_counts[self.fighter_name_key(name)] = 1
                    return name
        name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(LAST_NAMES)}"
        self.name_counts[name] = self.name_counts.get(name, 0) + 1
        return name

    def active_fighter_names(self):
        names = {fighter.name for fighter in getattr(self, "roster", [])}
        names.update(fighter.name for fighter in getattr(self, "free_agents", []))
        for promo in getattr(self, "promotions", []):
            names.update(fighter.name for fighter in promo.roster)
        names.update(fighter.name for fighter in getattr(self, "retired_fighters", []))
        # Carry each name's accent- and case-folded identity alongside it so a
        # generated "Alex Pérez" cannot slip past a rostered "Alex Perez".
        names.update({self.fighter_name_key(name) for name in list(names)})
        return names

    def all_fighter_objects(self):
        fighters = []
        fighters.extend(getattr(self, "roster", []))
        fighters.extend(getattr(self, "free_agents", []))
        for promo in getattr(self, "promotions", []):
            fighters.extend(promo.roster)
        fighters.extend(getattr(self, "retired_fighters", []))
        return fighters

    def clean_numbered_fighter_names(self):
        existing = set()
        renames = {}
        self.name_counts = {}
        for fighter in self.all_fighter_objects():
            old_name = fighter.name
            parts = fighter.name.rsplit(" ", 1)
            preferred = parts[0] if len(parts) == 2 and parts[1].isdigit() else fighter.name
            if preferred in existing:
                # Curated universe data can intentionally include a younger or
                # alternate-era version of a real fighter on another roster.
                # They retain separate fighter_id values, so do not turn them
                # into ugly "Name 2" entries or silently remove one at seed.
                if not getattr(fighter, "generated", False):
                    fighter.name = preferred
                else:
                    fighter.name = self.generate_clean_unique_name(fighter.gender, existing)
            else:
                fighter.name = preferred
                self.name_counts[fighter.name] = 1
            existing.add(fighter.name)
            if old_name != fighter.name:
                renames[old_name] = fighter.name
        if renames:
            self.apply_fighter_renames(renames)

    def apply_fighter_renames(self, renames):
        for fight in getattr(self, "booked", []):
            fight["fighters"] = [renames.get(name, name) for name in fight.get("fighters", [])]
        for event in getattr(self, "scheduled_events", []):
            for fight in event.get("fights", []):
                fight["fighters"] = [renames.get(name, name) for name in fight.get("fighters", [])]
        for weight, champion in list(getattr(self, "belts", {}).items()):
            self.belts[weight] = renames.get(champion, champion)
        self.interim_belts = {key: renames.get(champion, champion) for key, champion in self.normalize_belts(getattr(self, "interim_belts", {})).items()}
        self.belt_history = self.rename_belt_history(getattr(self, "belt_history", {}), renames)
        for promo in getattr(self, "promotions", []):
            promo.belts = {key: renames.get(champion, champion) for key, champion in self.normalize_belts(promo.belts).items()}
            promo.interim_belts = {key: renames.get(champion, champion) for key, champion in self.normalize_belts(promo.interim_belts).items()}
            promo.belt_history = self.rename_belt_history(promo.belt_history, renames)
        for fighter in self.all_fighter_objects():
            if fighter.rival in renames:
                fighter.rival = renames[fighter.rival]
            if fighter.friend in renames:
                fighter.friend = renames[fighter.friend]

    def rename_belt_history(self, history, renames):
        history = self.normalize_belt_history(history)
        for entries in history.values():
            for entry in entries:
                if entry.get("fighter") in renames:
                    entry["fighter"] = renames[entry["fighter"]]
        return history
