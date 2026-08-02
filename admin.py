import json
import random
import sys
import unicodedata
import traceback
from functools import lru_cache
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from constants import *
from models import Fighter, Gym, Promotion


class AdminMixin:
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
            self.engine_settings[key] = round(max(0.5, min(2.0, var.get())), 2)
        self.inbox.append({"subject": "Engine Settings Updated", "body": f"Simulation engine settings updated: {self.engine_settings}", "type": "Rules", "resolved": False})
        self.refresh_all()

    def reset_engine_settings(self):
        self.engine_settings = self.seed_engine_settings()
        for key, var in self.engine_vars.items():
            var.set(self.engine_settings[key])
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
        choices = [fighter.name for fighter in fighters]
        self.sim_combo_a.configure(values=choices)
        self.sim_combo_b.configure(values=choices)
        if choices and self.sim_fighter_a.get() not in choices:
            self.sim_fighter_a.set(choices[0])
        if len(choices) > 1 and self.sim_fighter_b.get() not in choices:
            self.sim_fighter_b.set(next((name for name in choices if name != self.sim_fighter_a.get()), choices[0]))
        if hasattr(self, "sim_tournament_list"):
            selected_names = {self.sim_tournament_list.get(index) for index in self.sim_tournament_list.curselection()}
            self.sim_tournament_list.delete(0, "end")
            for fighter in fighters:
                self.sim_tournament_list.insert("end", fighter.name)
            for index, fighter in enumerate(fighters):
                if fighter.name in selected_names:
                    self.sim_tournament_list.selection_set(index)
        self.update_sim_fighter_cards()

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
        company = next((name for name, candidate in self.all_database_fighters_with_companies() if candidate.name == fighter.name), "Unknown")
        return (
            f"{fighter.name}  |  OVR {fighter.overall}  |  ELO {fighter.elo_rating}\n"
            f"{fighter.gender} {fighter.weight}  |  {fighter.record}  |  Age {fighter.age}  |  {fighter.nationality}\n"
            f"{company}  |  {fighter.style} / {fighter.stance}  |  {fighter.trait}\n"
            f"Strike {fighter.striking}  Wrestle {fighter.wrestling}  Ground {fighter.grappling}  Cardio {fighter.cardio}  Chin {fighter.chin}\n"
            f"Power {fighter.power}  TD Def {fighter.takedown_defence}  Control {fighter.ground_control}  Subs {fighter.submissions}/{fighter.submission_defence}\n"
            f"Walk {fighter.walk_weight or self.default_walk_weight(fighter)} lb  Cut skill {self.ds(fighter, 'weight_cutting', fighter.cardio)}  Last cut penalty {fighter.weight_cut_penalty}\n"
            f"Pop {fighter.popularity}  Momentum {fighter.momentum:+d}  Morale {fighter.morale}  Camp {fighter.camp} (+{fighter.camp_boost})  Status {fighter.status}"
        )

    def update_sim_fighter_cards(self):
        if not hasattr(self, "sim_profile_a"):
            return
        self.sim_profile_a.config(text=self.sim_fighter_scout_text(self.find_fighter_anywhere(self.sim_fighter_a.get())))
        self.sim_profile_b.config(text=self.sim_fighter_scout_text(self.find_fighter_anywhere(self.sim_fighter_b.get())))

    def open_sim_fighter_profile(self, corner):
        name = self.sim_fighter_a.get() if corner == "red" else self.sim_fighter_b.get()
        fighter = self.find_fighter_anywhere(name)
        if fighter:
            self.open_fighter_profile_window(fighter)
        else:
            messagebox.showinfo("Simulator", "Select a fighter first.")

    def auto_seed_sim_tournament(self):
        if not hasattr(self, "sim_tournament_list"):
            return
        size = int(self.sim_tournament_size.get())
        fighters = self.sim_filtered_fighters()
        if len(fighters) < size:
            messagebox.showwarning("Tournament", f"This filter has only {len(fighters)} eligible fighters; {size} are needed.")
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
        selected_names = {fighter.name for fighter in seeded}
        self.sim_tournament_list.selection_clear(0, "end")
        for index in range(self.sim_tournament_list.size()):
            if self.sim_tournament_list.get(index) in selected_names:
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
        selected_names = [self.sim_tournament_list.get(index) for index in self.sim_tournament_list.curselection()]
        if len(selected_names) != size:
            messagebox.showinfo("Tournament", f"Select exactly {size} fighters, or use Auto-Seed Division.")
            return
        originals = [self.find_fighter_anywhere(name) for name in selected_names]
        if any(fighter is None for fighter in originals):
            messagebox.showwarning("Tournament", "A selected fighter is no longer in the database. Refresh the field and try again.")
            return
        genders = {fighter.gender for fighter in originals}
        weights = {fighter.weight for fighter in originals}
        if len(genders) != 1 or len(weights) != 1:
            messagebox.showwarning("Tournament", "Tournament entrants must all be in the same gender and weight division. Use the filters to build a valid field.")
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
            messagebox.showinfo("Tournament Night", "Run a tournament first, then its complete card can be watched like a fight night.")
            return
        def reveal_tournament():
            self.sim_tournament_bracket["revealed"] = True
            self.write_sim_tournament_report("\n".join(package["log"]))
            self.open_sim_tournament_bracket()
        self.open_live_fight_window(event, package, apply_results=False, on_complete=reveal_tournament)

    def open_sim_tournament_bracket(self):
        bracket = getattr(self, "sim_tournament_bracket", None)
        if not bracket:
            messagebox.showinfo("Tournament Bracket", "Run a tournament first to create its visual bracket.")
            return
        window = tk.Toplevel(self.root)
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
        a_name = self.sim_fighter_a.get()
        b_name = self.sim_fighter_b.get()
        if not a_name or not b_name or a_name == b_name:
            messagebox.showinfo("Simulator", "Pick two different fighters.")
            return
        original_a = self.find_fighter_anywhere(a_name)
        original_b = self.find_fighter_anywhere(b_name)
        if not original_a or not original_b:
            messagebox.showwarning("Simulator", "One of those fighters could not be found in the database.")
            return
        if original_a.gender != original_b.gender and not self.rules.get("allow_mixed_gender", False):
            messagebox.showwarning("Rules blocked", "Mixed-gender fights are not allowed under this promotion's current rules.")
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
            self.sim_result.config(text="Fight prepared. Watch it to reveal the result." if watch else lines[-1])
        if watch:
            event = {"name": "Quick Fight Simulator", "venue": "Simulation Lab", "region": self.player_region, "city": "Sandbox", "month": self.month, "week": self.week, "fights": [fight]}
            self.open_live_fight_window(event, package, apply_results=False, on_complete=lambda: self.sim_result.config(text=lines[-1]))

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
            gate = round(attendance * ticket_price * self.engine_settings.get("gate_multiplier", 1.0))
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

    def run_play_level_audit(self):
        """Run a fresh observer world for a long-run balance audit without touching this save."""
        years = max(1, min(100, self.play_audit_years.get()))
        weeks = years * 48
        if hasattr(self, "play_audit_progress"):
            self.play_audit_progress.configure(maximum=weeks, value=0)
            self.play_audit_status.config(text=f"{years}-year play audit: starting fresh observer world...")
        self.audit_text.config(state="normal")
        self.audit_text.delete("1.0", "end")
        self.audit_text.insert("end", f"Running fresh {years}-year observer audit...\nThis uses the full weekly world loop and may take a short while.")
        self.audit_text.config(state="disabled")
        self.root.update_idletasks()
        audit_root = tk.Tk()
        audit_root.withdraw()
        methods, snapshots = {}, []
        original_state = random.getstate()
        try:
            random.seed(260712)
            audit = self.__class__(audit_root)
            audit.enter_spectator_mode()
            audit.suppress_award_popups = True
            audit.suppress_autosaves = True
            real_simulate = audit.simulate_fight

            def count_fight(a, b, fight):
                winner, loser, method, round_no, lines = real_simulate(a, b, fight)
                methods[method] = methods.get(method, 0) + 1
                return winner, loser, method, round_no, lines

            audit.simulate_fight = count_fight
            for index in range(weeks):
                audit.advance_month()
                if (index + 1) % 4 == 0 or index + 1 == weeks:
                    if hasattr(self, "play_audit_progress"):
                        completed = index + 1
                        audit_year = 2026 + completed // 48
                        audit_week = completed % 48
                        self.play_audit_progress.configure(value=completed)
                        self.play_audit_status.config(text=f"{years}-year play audit: Year {audit_year} | week {audit_week or 48}/48 ({completed / weeks * 100:.1f}%)")
                    self.root.update_idletasks()
                if (index + 1) % 48 == 0:
                    active = [fighter for fighter in audit.all_fighter_objects() if not fighter.retired]
                    viable = [promo for promo in audit.promotions if promo.cash > 0 and promo.stability >= 20]
                    promo_cash = [promo.cash for promo in audit.promotions]
                    sport_events = sum(len(world.get("events", [])) for world in getattr(audit, "combat_sport_worlds", {}).values())
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
                    })
                if (index + 1) % 96 == 0:
                    self.root.update_idletasks()
            total = sum(methods.values())
            finish_count = sum(count for method, count in methods.items() if method not in ("Decision", "Draw"))
            last = snapshots[-1]
            active = [fighter for fighter in audit.all_fighter_objects() if not fighter.retired]
            by_gender, by_weight_gender = {}, {}
            for fighter in active:
                by_gender[fighter.gender] = by_gender.get(fighter.gender, 0) + 1
                key = (fighter.gender, fighter.weight)
                by_weight_gender[key] = by_weight_gender.get(key, 0) + 1
            promotion_rows = sorted(
                [(promo.name, promo.cash, promo.stability, promo.popularity, len(promo.roster), getattr(promo, "strategy", "")) for promo in audit.promotions],
                key=lambda row: row[1],
            )
            sport_rows = []
            for sport, world in getattr(audit, "combat_sport_worlds", {}).items():
                roster = world.get("roster", [])
                sport_rows.append((sport, len(roster), world.get("promotion", ""), world.get("champion", ""), len(world.get("events", [])), round(sum(a.overall for a in roster) / max(1, len(roster)), 1)))
            warnings = []
            if last["active"] < 350:
                warnings.append(f"Active fighter pool is thin late-era ({last['active']} active). Replenishment may need a boost.")
            if last["free_agents"] < 45:
                warnings.append(f"Free-agent pool is low ({last['free_agents']}). AI/player signings may feel starved.")
            if last["distressed"] >= max(2, last["promotions"] // 4):
                warnings.append(f"Promotion finance pressure is high ({last['distressed']} distressed companies).")
            if last["elite"] < 25:
                warnings.append(f"Elite population is low ({last['elite']} at 80+ OVR). Development/regen may be too stingy.")
            if methods.get("Decision", 0) / max(1, total) > 0.62:
                warnings.append("Decision rate is high for the full world. Check fight-engine/card matchmaking by tier.")
            if not warnings:
                warnings.append("No major red flags detected from headline balance metrics.")
            report = [
                f"{years}-YEAR PLAY-LEVEL AUDIT (fresh spectator world)",
                f"Weeks simulated: {weeks:,} | Fights: {total:,}",
                f"Finish rate: {finish_count / max(1, total) * 100:.1f}% | Decision rate: {methods.get('Decision', 0) / max(1, total) * 100:.1f}%",
                "",
                "BALANCE WARNINGS:",
            ]
            report.extend(f"- {warning}" for warning in warnings)
            report.extend(["", "METHOD DISTRIBUTION:"])
            report.extend(f"- {method}: {count:,} ({count / max(1, total) * 100:.1f}%)" for method, count in sorted(methods.items(), key=lambda item: -item[1]))
            report.extend(["", "YEARLY WORLD HEALTH:", "Year | Promotions | Viable | Distressed | Active | FAs | Retired | 80+ | Avg Cash | Min Cash | Sport Cards | Academy"])
            for row in snapshots:
                report.append(f"{row['year']} | {row['promotions']} | {row['viable']} | {row['distressed']} | {row['active']} | {row['free_agents']} | {row['retired']} | {row['elite']} | ${row['avg_cash']:,} | ${row['min_cash']:,} | {row['sport_events']} | {row['academy_size']}")
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
            report.extend(["", f"FINAL: {last['promotions']} promotions ({last['viable']} viable), {last['active']} active fighters, {last['free_agents']} free agents, {last['retired']} retired, {last['elite']} elite fighters."])
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
        if hasattr(self, "play_audit_progress"):
            if report and "PLAY-LEVEL AUDIT" in report[0]:
                self.play_audit_progress.configure(value=weeks)
                self.play_audit_status.config(text=f"{years}-year play audit: complete - results shown below")
                if hasattr(self, "view_play_audit_button"):
                    self.view_play_audit_button.configure(state="normal")
            else:
                self.play_audit_status.config(text=f"{years}-year play audit: failed - see report below")

    def open_play_level_audit_results(self):
        report = getattr(self, "play_audit_report", "")
        if not report:
            messagebox.showinfo("30-Year Play Audit", "Run the 30-year play audit first.")
            return
        window = tk.Toplevel(self.root)
        window.title("30-Year Play Audit Results")
        window.geometry("940x680")
        window.minsize(720, 480)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="30-YEAR PLAY AUDIT RESULTS", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
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

        def export_report():
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            path = LOG_DIR / f"play_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path.write_text(report, encoding="utf-8")
            messagebox.showinfo("Export Results", f"Exported audit report:\n{path}")

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
        for key, value in (belts or {}).items():
            if key in normalized:
                normalized[key] = value
            elif key in WEIGHTS:
                normalized[self.belt_key("Male", key)] = value
        return normalized

    def normalize_belt_history(self, history):
        normalized = self.blank_belt_history()
        for key, entries in (history or {}).items():
            if key in normalized:
                normalized[key] = list(entries or [])
            elif key in WEIGHTS:
                normalized[self.belt_key("Male", key)] = list(entries or [])
        return normalized

    def normalize_special_belts(self, belts):
        """Normalize player-created championships such as BMF without mixing them into divisions."""
        normalized = {}
        for key, value in (belts or {}).items():
            name = str((value or {}).get("name", key) if isinstance(value, dict) else key).strip()
            if not name:
                continue
            row = dict(value) if isinstance(value, dict) else {}
            row["name"] = name
            row["holder"] = str(row.get("holder", "") or "")
            row["defenses"] = max(0, int(row.get("defenses", 0) or 0))
            row["history"] = list(row.get("history", []) or [])[:80]
            normalized[name] = row
        return normalized

    def award_special_belt(self, belt_name, winner, loser, method):
        self.special_belts = self.normalize_special_belts(getattr(self, "special_belts", {}))
        belt = self.special_belts.get(belt_name)
        if not belt:
            return False
        previous = belt.get("holder", "")
        defense = previous == winner.name
        belt["holder"] = winner.name
        belt["defenses"] = belt.get("defenses", 0) + (1 if defense else 0)
        action = "Defense" if defense else "Champion Crowned"
        belt["history"].insert(0, {
            "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
            "action": action, "fighter": winner.name, "previous": previous,
            "note": f"Defeated {loser.name} by {method}.",
        })
        belt["history"] = belt["history"][:80]
        winner.special_titles = list(getattr(winner, "special_titles", None) or [])
        if belt_name not in winner.special_titles:
            winner.special_titles.append(belt_name)
        if previous and previous != winner.name:
            former = next((fighter for fighter in self.roster if fighter.name == previous), None)
            if former:
                former.special_titles = [name for name in (getattr(former, "special_titles", None) or []) if name != belt_name]
        return True

    def vacate_special_belts_held_by(self, fighter, reason):
        self.special_belts = self.normalize_special_belts(getattr(self, "special_belts", {}))
        for belt in self.special_belts.values():
            if belt.get("holder") != fighter.name:
                continue
            belt["holder"] = ""
            belt["history"].insert(0, {
                "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
                "action": "Vacated", "fighter": fighter.name, "previous": fighter.name, "note": reason,
            })
            belt["history"] = belt["history"][:80]
        fighter.special_titles = []

    def belt_history_entry(self, action, key, fighter_name="", note=""):
        entry = {
            "date": f"Month {getattr(self, 'month', 1)} Week {getattr(self, 'week', 1)}",
            "action": action,
            "division": key,
            "fighter": fighter_name,
            "note": note,
        }
        # A title change belongs to the day its card ran, so a lineage reads as
        # a sequence of dated events rather than a list of weeks. Fighter fight
        # histories deliberately stay week-level.
        day = getattr(self, "_active_card_day", None)
        if day is not None:
            entry["day"] = self.normalize_day(day)
        return entry

    def record_belt_history(self, history, key, action, fighter_name="", note=""):
        history = self.normalize_belt_history(history)
        history[key].insert(0, self.belt_history_entry(action, key, fighter_name, note))
        return history

    def set_primary_champion(self, roster, belts, belt_history, champion, note, defense=False, appointed=False):
        key = self.belt_key(champion.gender, champion.weight)
        belts = self.normalize_belts(belts)
        belt_history = self.normalize_belt_history(belt_history)
        previous = belts.get(key, "")
        for fighter in roster:
            if fighter.gender == champion.gender and fighter.weight == champion.weight:
                fighter.champion = fighter.name == champion.name
                if fighter.name == champion.name:
                    fighter.interim_champion = False
        belts[key] = champion.name
        if previous != champion.name:
            prior_lineage = bool(belt_history.get(key))
            action = "Champion Crowned" if previous or prior_lineage else ("Inaugural Champion Appointed" if appointed else "Inaugural Champion")
            belt_history = self.record_belt_history(belt_history, key, action, champion.name, note)
            if not appointed:
                champion.title_wins = getattr(champion, "title_wins", 0) + 1
        elif defense:
            champion.title_defenses = getattr(champion, "title_defenses", 0) + 1
            belt_history = self.record_belt_history(belt_history, key, "Title Defense", champion.name, note)
        return belts, belt_history

    def set_interim_champion(self, roster, interim_belts, belt_history, champion, note):
        key = self.belt_key(champion.gender, champion.weight)
        interim_belts = self.normalize_belts(interim_belts)
        belt_history = self.normalize_belt_history(belt_history)
        previous = interim_belts.get(key, "")
        for fighter in roster:
            if fighter.gender == champion.gender and fighter.weight == champion.weight:
                fighter.interim_champion = fighter.name == champion.name
        interim_belts[key] = champion.name
        if previous != champion.name:
            belt_history = self.record_belt_history(belt_history, key, "Interim Champion Crowned", champion.name, note)
            champion.interim_title_wins = getattr(champion, "interim_title_wins", 0) + 1
        else:
            champion.interim_title_defenses = getattr(champion, "interim_title_defenses", 0) + 1
            belt_history = self.record_belt_history(belt_history, key, "Interim Title Defense", champion.name, note)
        return interim_belts, belt_history

    def clear_interim_belt(self, roster, interim_belts, belt_history, key, note):
        interim_belts = self.normalize_belts(interim_belts)
        holder = interim_belts.get(key, "")
        if holder:
            for fighter in roster:
                if fighter.name == holder:
                    fighter.interim_champion = False
            interim_belts[key] = ""
            belt_history = self.record_belt_history(belt_history, key, "Interim Belt Cleared", holder, note)
        return interim_belts, belt_history

    def interim_title_participates(self, interim_belts, winner, loser):
        key = self.belt_key(winner.gender, winner.weight)
        holder = self.normalize_belts(interim_belts).get(key, "")
        return bool(holder and holder in {winner.name, loser.name})

    def vacate_fighter_belts(self, fighter, roster, belts, interim_belts, belt_history, reason):
        key = self.belt_key(fighter.gender, fighter.weight)
        belts = self.normalize_belts(belts)
        interim_belts = self.normalize_belts(interim_belts)
        belt_history = self.normalize_belt_history(belt_history)
        if belts.get(key) == fighter.name:
            belts[key] = ""
            fighter.champion = False
            belt_history = self.record_belt_history(belt_history, key, "Vacated", fighter.name, reason)
            if roster is getattr(self, "roster", None):
                self.queue_vacant_title_alert(key, f"{fighter.name}'s reign ended. Reason: {reason}", getattr(fighter, "fighter_id", ""))
        if interim_belts.get(key) == fighter.name:
            interim_belts[key] = ""
            fighter.interim_champion = False
            belt_history = self.record_belt_history(belt_history, key, "Interim Vacated", fighter.name, reason)
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
                current = next((fighter for fighter in division if fighter.name == belts.get(key)), None)
                # Player vacancies are always decided in the cage. AI companies
                # may receive inaugural holders during initial world seeding,
                # but once a lineage exists their later vacancies also stay open
                # until an AI-booked title fight crowns a champion.
                if not current and (player_owned or belt_history.get(key) or not allow_appointed):
                    belts[key] = ""
                    for fighter in division:
                        fighter.champion = False
                    champion = None
                else:
                    champion = current or max(division, key=self.champion_sort_value)
                    belts, belt_history = self.set_primary_champion(roster, belts, belt_history, champion, f"{company_name} title status normalized.", appointed=not current)
                primary_name = champion.name if champion else ""
                interim_holder = next((fighter for fighter in division if fighter.name == interim_belts.get(key) and fighter.name != primary_name), None)
                for fighter in division:
                    fighter.interim_champion = bool(interim_holder and fighter.name == interim_holder.name)
                if not interim_holder:
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
