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


class ViewMixin:
    def refresh_all(self):
        self.sync_gym_membership()
        if getattr(self, "spectator_mode", False):
            self.stat_cash.config(text="World Simulation")
            self.stat_pop.config(text=f"{len(self.promotions)} active promotions")
            self.stat_stability.config(text=f"{len(self.free_agents)} free agents")
        else:
            self.stat_cash.config(text=f"Cash: ${self.cash:,.0f}")
            self.stat_pop.config(text=f"{self.player_company_name} popularity: {self.company_pop}")
            self.stat_stability.config(text=f"Stability: {self.company_stability}")
        self.stat_month.config(text=f"Week {self.week}, Month {self.month} / 2026")
        self.refresh_game_menu()
        self.refresh_roster()
        self.refresh_contracts()
        self.refresh_available()
        self.refresh_card()
        self.refresh_upcoming()
        self.refresh_market()
        self.refresh_website()
        self.refresh_assistant()
        self.refresh_companies()
        self.refresh_regions()
        self.refresh_results()
        self.refresh_company_editor()
        self.refresh_inbox()
        self.refresh_staff()
        self.refresh_finance()
        self.refresh_world()
        self.refresh_rankings()
        self.refresh_sim_fighter_choices()
        self.refresh_database_editor()
        self.refresh_spectator_controls()

    def refresh_spectator_controls(self):
        if not hasattr(self, "spectator_sim_panel"):
            return
        if getattr(self, "spectator_mode", False):
            self.spectator_sim_panel.pack(fill="x", pady=(8, 0))
            if hasattr(self, "spectator_sim_status"):
                latest = self.ai_event_archive[0].get("event_name", "No events yet") if self.ai_event_archive else "No events hosted yet"
                self.spectator_sim_status.config(text=f"Observer mode: Month {self.month}, Week {self.week}. Latest world event: {latest}.")
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
        champ = 60 if fighter.champion else 0
        activity = max(0, 20 - fighter.fatigue // 4)
        elo = (getattr(fighter, "elo_rating", 1500) - 1500) / 5
        form = max(-45, min(45, fighter.momentum * 10))
        return round(champ + elo + fighter.record_w * 1.5 - fighter.record_l * 2.6 + fighter.overall * 1.25 + fighter.popularity * 0.38 + form + activity)

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
        return True

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

    def refresh_roster(self):
        self.roster_tree.delete(*self.roster_tree.get_children())
        selected = self.weight_filter.get()
        gender = self.roster_gender_filter.get() if hasattr(self, "roster_gender_filter") else "All"
        status = self.roster_status_filter.get() if hasattr(self, "roster_status_filter") else "All"
        query = self.roster_search.get().strip() if hasattr(self, "roster_search") else ""
        fighters = sorted(self.roster, key=lambda f: (f.weight, -(f.champion * 1000 + f.popularity + f.overall)))
        for fighter in fighters:
            if selected != "All" and fighter.weight != selected:
                continue
            if gender != "All" and fighter.gender != gender:
                continue
            if not self.fighter_matches_status_filter(fighter, status):
                continue
            if not self.fighter_matches_text_filter(fighter, query):
                continue
            name = self.fighter_display_name(fighter)
            if fighter.injured:
                row_tag = "injured"
            elif 0 < fighter.contract_months <= 3:
                row_tag = "expiring"
            elif fighter.champion:
                row_tag = "champ"
            else:
                row_tag = ""
            self.roster_tree.insert("", "end", iid=fighter.name, tags=(row_tag,) if row_tag else (), values=(name, fighter.gender[0], fighter.weight, fighter.record, fighter.age, fighter.overall, fighter.popularity, fighter.momentum, fighter.morale, fighter.contract_months, fighter.status))
        visible = self.roster_tree.get_children()
        if visible and not self.roster_tree.selection():
            self.roster_tree.selection_set(visible[0])
            self.update_fighter_detail()

    def refresh_contracts(self):
        if not hasattr(self, "contracts_tree"):
            return
        self.contracts_tree.delete(*self.contracts_tree.get_children())
        payroll = 0
        expiring = 0
        final_month = 0
        champs_expiring = []
        show_filter = self.contracts_filter.get() if hasattr(self, "contracts_filter") else "All"
        for fighter in sorted(self.roster, key=lambda f: (f.contract_months, -f.popularity, -f.overall)):
            payroll += fighter.purse
            months = fighter.contract_months
            if months <= 3:
                expiring += 1
                if fighter.champion:
                    champs_expiring.append(fighter.name)
            if months <= 1:
                final_month += 1
            exclusive = getattr(fighter, "exclusive", True)
            if show_filter == "Expiring (<=3 mo)" and months > 3:
                continue
            if show_filter == "Final month" and months > 1:
                continue
            if show_filter == "Non-Exclusive" and exclusive:
                continue
            if months <= 0:
                tag, status = "expired", "EXPIRED"
            elif months <= 1:
                tag, status = "final", "Final month"
            elif months <= 3:
                tag, status = "soon", ("Champion leverage" if fighter.champion else "Expiring soon")
            else:
                tag, status = "", ("Champion leverage" if fighter.champion else fighter.status)
            contract_type = getattr(fighter, "contract_type", "Exclusive" if exclusive else "Non-Exclusive")
            self.contracts_tree.insert("", "end", iid=fighter.name, tags=(tag,) if tag else (),
                                       values=(fighter.name, fighter.gender[0], fighter.weight, self.division_rank_label(fighter),
                                               fighter.popularity, fighter.overall, months, f"${fighter.purse:,}",
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
        self.contracts_summary.config(text=f"{expiring} expiring soon | {final_month} final month | est. show payroll ${payroll:,}")
        if hasattr(self, "auto_renew_button"):
            enabled = self.rules.get("auto_renew_enabled", False)
            self.auto_renew_button.config(text=f"Auto Renew: {'On' if enabled else 'Off'}")

    def selected_contract_fighter(self):
        selected = self.contracts_tree.selection() if hasattr(self, "contracts_tree") else []
        return self.get_fighter(selected[0]) if selected else None

    def renew_selected_contract(self):
        fighter = self.selected_contract_fighter()
        if not fighter:
            return
        self.open_contract_negotiation(fighter, existing=True)

    def toggle_auto_renew(self):
        self.rules["auto_renew_enabled"] = not self.rules.get("auto_renew_enabled", False)
        self.refresh_contracts()

    def view_contract_profile(self):
        fighter = self.selected_contract_fighter()
        if not fighter:
            return
        self.roster_tree.selection_set(fighter.name)
        self.select_tab("roster")
        self.update_fighter_detail()

    def update_fighter_detail(self, _event=None):
        selected = self.roster_tree.selection()
        if not selected:
            return
        fighter = self.get_fighter(selected[0])
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
                f"Recent Bio: {fighter.fight_history[0] if fighter.fight_history else 'No fight history yet'}\n"
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

    def portrait_badge_text(self, fighter):
        return f"{self.weight_abbreviation(fighter.weight)} | OVR {fighter.overall}"

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

    def fighter_profile_text(self, fighter):
        company = next((name for name, candidate in self.all_database_fighters_with_companies() if candidate.name == fighter.name), "Unknown")
        company_rank = self.rank_label_for_fighter(fighter, company, world=False)
        world_rank = self.rank_label_for_fighter(fighter, company, world=True)
        return (
            f"{fighter.name}\n"
            f"{fighter.gender} {fighter.weight} | {company}\n"
            f"Record: {fighter.record} | Age: {fighter.age} | Height: {fighter.height or '-'} | Nationality: {fighter.nationality}\n"
            f"Based In: {fighter.region}\n"
            f"Company Rank: {company_rank} | World Rank: {world_rank} | Elo: {fighter.elo_rating}\n"
            f"Title Status: {'Champion' if fighter.champion else ('Interim Champion' if getattr(fighter, 'interim_champion', False) else 'Contender')}\n\n"
            f"Style: {fighter.style} | Stance: {fighter.stance} | Behaviour: {fighter.behaviour}\n"
            f"Trait: {fighter.trait} | Camp: {fighter.camp} | Plan: {fighter.camp_focus} ({fighter.camp_intensity})\n"
            f"{self.rivalry_summary(fighter)}\n\n"
            f"Popularity: {fighter.popularity} | Momentum: {fighter.momentum} | Morale: {fighter.morale}\n"
            f"Star: {fighter.star_quality} | Charisma: {fighter.charisma} | Media: {fighter.media_presence} | Sponsor: {fighter.sponsor_appeal}\n"
            f"Contract: {fighter.contract_type} | {fighter.contract_months} months | ${fighter.purse:,}/fight | Trust: {fighter.relationship_trust}\n\n"
            f"Walk Weight: {fighter.walk_weight or self.default_walk_weight(fighter)} lb | Last Scale: {fighter.scale_weight or '-'} lb | Cut Penalty: {fighter.weight_cut_penalty}\n"
            f"Fatigue: {fighter.fatigue} | Injury: {fighter.injured or 'None'} | {self.fighter_return_label(fighter)} | Status: {fighter.status}\n"
            f"Camp Boost: +{fighter.camp_boost} ({fighter.camp_weeks} wk, Q{fighter.camp_quality})\n"
            f"Annual Peaks: {self.annual_overall_chart(fighter)}\n"
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
        rows.extend(("Retired", fighter) for fighter in self.retired_fighters)
        return rows

    def rank_label_for_fighter(self, fighter, company, world=False):
        rows = [(co, f) for co, f in self.unfiltered_ranked_fighter_rows() if f.gender == fighter.gender and f.weight == fighter.weight]
        if not world:
            rows = [(co, f) for co, f in rows if co == company]
        ordered = sorted(rows, key=lambda row: self.rank_value(row[1]), reverse=True)
        for index, (_company, candidate) in enumerate(ordered, 1):
            if candidate.name == fighter.name:
                return self.rank_label_for_position(candidate, index)
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
        return f"Career record (W-L-D): {fighter.record}\n\n" + "\n".join(f"- {entry}" for entry in history[:80])

    def profile_info_row(self, parent, label, value, row):
        tk.Label(parent, text=label.upper(), bg=self.colors["panel"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        tk.Label(parent, text=str(value), bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w").grid(row=row, column=1, sticky="ew", padx=8, pady=3)
        parent.grid_columnconfigure(1, weight=1)

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

    def open_fighter_profile_window(self, fighter):
        report = getattr(self, "scouting_reports", {}).get(fighter.name, {})
        if fighter in self.free_agents and self.rules.get("scouting_mode", False) and report.get("reveal", 0) < 100:
            self.open_limited_scout_profile(fighter, report)
            return
        self.ensure_detailed_skills(fighter)
        self.ensure_fighter_business_stats(fighter)
        company = next((name for name, candidate in self.all_database_fighters_with_companies() if candidate.name == fighter.name), "Unknown")
        company_rank = self.rank_label_for_fighter(fighter, company, world=False)
        world_rank = self.rank_label_for_fighter(fighter, company, world=True)
        window = tk.Toplevel(self.root)
        window.title(f"Fighter Profile - {fighter.name}")
        window.geometry("1120x720")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=fighter.name.upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        ttk.Label(header, text=f"{fighter.gender} {fighter.weight} | {company} | Company {company_rank} | World {world_rank}", style="ScreenTitle.TLabel").pack(side="right", padx=10, pady=5)
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body, style="Panel.TFrame")
        left.pack(side="left", fill="y", padx=(0, 8), ipadx=2)
        portrait = tk.Canvas(left, width=180, height=180, highlightthickness=1, highlightbackground=self.colors["line"], bg="#222222")
        portrait.pack(anchor="n", padx=10, pady=10)
        self.draw_profile_portrait(portrait, fighter)

        badge_row = tk.Frame(left, bg=self.colors["panel"])
        badge_row.pack(fill="x", padx=8, pady=(0, 6))
        self.profile_badge(badge_row, "OVR", fighter.overall)
        self.profile_badge(badge_row, "ELO", fighter.elo_rating)
        self.profile_badge(badge_row, "P4P", world_rank)

        identity = tk.Frame(left, bg=self.colors["panel"])
        identity.pack(fill="x", padx=8, pady=(0, 8))
        rows = [
            ("Record", fighter.record),
            ("Age", f"{fighter.age} ({self.fighter_career_stage(fighter)})"),
            ("Height", fighter.height or "-"),
            ("Nationality", fighter.nationality),
            ("Born", f"{getattr(fighter, 'birth_country', '') or fighter.region} - {getattr(fighter, 'hometown', '') or '-'}"),
            ("Based / Trains", f"{getattr(fighter, 'fighting_base', '') or fighter.region} / {getattr(fighter, 'training_location', '') or fighter.region}"),
            ("Style", fighter.style),
            ("Stance", fighter.stance),
            ("Behaviour", fighter.behaviour),
            ("Trait", fighter.trait),
            ("Camp", fighter.camp),
            ("Status", fighter.status),
            ("Major Injury", self.serious_injury_status(fighter)),
            ("Division Moves", len(getattr(fighter, "weight_class_history", []) or [])),
            ("Achievements", len(getattr(fighter, "career_achievements", []) or [])),
        ]
        for idx, (label, value) in enumerate(rows):
            self.profile_info_row(identity, label, value, idx)

        if fighter.injured or getattr(fighter, "serious_injury", ""):
            medical_alert = tk.Frame(left, bg="#5a2525", highlightthickness=1, highlightbackground="#d86b6b")
            medical_alert.pack(fill="x", padx=8, pady=(0, 8))
            injury_name = getattr(fighter, "serious_injury", "") or "Training / fight injury"
            decision = " — medical decision required" if getattr(fighter, "serious_injury_pending", False) else ""
            icon_path = APP_DIR / "assets" / "medical_cross.png"
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
        for idx, (label, value) in enumerate(core_stats):
            self.profile_meter(core, label, value, idx)

        self.profile_section_label(center, "Career & Camp")
        camp = tk.Frame(center, bg=self.colors["panel"])
        camp.pack(fill="x", padx=6, pady=(0, 8))
        for idx, (label, value) in enumerate([
            ("Popularity", fighter.popularity), ("Momentum", fighter.momentum), ("Morale", fighter.morale),
            ("Motivation", fighter.motivation), ("Upside", self.upside_assessment(fighter)), ("Fatigue", fighter.fatigue),
            ("Camp Boost", f"+{fighter.camp_boost} ({fighter.camp_weeks} wk, Q{fighter.camp_quality})"),
            ("Development Profile", fighter.career_archetype.replace("Standard Prime", "Balanced Development")),
            ("Career Stage", self.fighter_career_stage(fighter)),
            ("Annual Peaks", self.annual_overall_chart(fighter)),
        ]):
            self.profile_info_row(camp, label, value, idx)

        notebook = ttk.Notebook(body)
        notebook.pack(side="left", fill="both", expand=True)
        stand_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        grappling_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        business_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        history_frame = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(stand_frame, text="Striking")
        notebook.add(grappling_frame, text="Grappling")
        notebook.add(business_frame, text="Business")
        notebook.add(history_frame, text="Fight History")

        for frame, groups in ((stand_frame, ("Standing", "Muay Thai Clinch", "Physical")), (grappling_frame, ("Wrestling", "Ground", "Mental"))):
            tree = ttk.Treeview(frame, columns=("skill", "value", "grade"), show="headings", height=22)
            for col, text, width in (("skill", "Skill", 210), ("value", "Value", 80), ("grade", "Grade", 100)):
                tree.heading(col, text=text)
                tree.column(col, width=width, anchor="w")
            tree.pack(fill="both", expand=True, padx=8, pady=8)
            self.fill_profile_skill_tree(tree, fighter, groups)

        business = tk.Frame(business_frame, bg=self.colors["panel"])
        business.pack(fill="both", expand=True, padx=8, pady=8)
        self.profile_section_label(business, "Contract")
        contract = tk.Frame(business, bg=self.colors["panel"])
        contract.pack(fill="x", padx=4, pady=(0, 8))
        for idx, (label, value) in enumerate([
            ("Type", fighter.contract_type), ("Months", fighter.contract_months), ("Purse", f"${fighter.purse:,}/fight"),
            ("Star Quality", fighter.star_quality), ("Charisma", fighter.charisma), ("Media", fighter.media_presence),
            ("Sponsor", fighter.sponsor_appeal), ("Professionalism", fighter.professionalism), ("Injury Risk", fighter.injury_proneness),
            ("Major Injury", self.serious_injury_status(fighter)),
            ("Career Goal", f"{fighter.career_goal or 'Undeclared'} ({getattr(fighter, 'career_goal_progress', 0)}%)"),
            ("Walk Weight", f"{fighter.walk_weight or self.default_walk_weight(fighter)} lb"), ("Last Scale", f"{fighter.scale_weight or '-'} lb"), ("Cut Penalty", fighter.weight_cut_penalty),
        ]):
            self.profile_info_row(contract, label, value, idx)

        history_controls = ttk.Frame(history_frame, style="Inset.TFrame"); history_controls.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(history_controls, text=f"Career Record: {fighter.record}", style="Inset.TLabel").pack(side="left", padx=4)
        history_filter = tk.StringVar(value="All")
        ttk.Combobox(history_controls, textvariable=history_filter, values=("All", "Professional", "Amateur", "Wins", "Losses"), state="readonly", width=14).pack(side="right", padx=4)
        history_tree = ttk.Treeview(history_frame, columns=("result", "badge", "opponent", "event", "method", "weight"), show="headings", height=15)
        for col, label, width in (("result", "Result", 70), ("badge", "Level", 75), ("opponent", "Opponent", 145), ("event", "Event", 190), ("method", "Method", 100), ("weight", "Division", 115)):
            history_tree.heading(col, text=label); history_tree.column(col, width=width, anchor="w")
        history_tree.tag_configure("win", foreground="#9de6a0"); history_tree.tag_configure("loss", foreground="#ff9b9b"); history_tree.pack(fill="both", expand=True, padx=8, pady=6)
        history_detail = tk.Text(history_frame, wrap="word", font=("Tahoma", 9), height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], padx=10, pady=8); history_detail.pack(fill="x", padx=8, pady=(0, 8)); history_detail.config(state="disabled")
        entries = fighter.fight_history or []
        def parsed(entry):
            text = str(entry); amateur = "Amateur" if "Amateur" in text else "Professional"; result = "W" if (" def. " in text or "Amateur W" in text or "W over" in text) else "L" if ("Amateur L" in text or "L to" in text) else "-"
            opponent = text.split(" over ", 1)[-1].split(" to ", 1)[-1].split(" by ", 1)[0] if result != "-" else "-"; method = text.split(" by ", 1)[1] if " by " in text else "-"
            return result, amateur, opponent[:30], "Academy Showcase" if amateur == "Amateur" else "Career Record", method[:24], fighter.weight, text
        rows = [parsed(entry) for entry in entries[:100]]
        def render_history(*_):
            history_tree.delete(*history_tree.get_children())
            for index, row in enumerate(rows):
                mode = history_filter.get()
                if mode != "All" and mode not in (row[1], "Wins" if row[0] == "W" else "Losses" if row[0] == "L" else "") : continue
                history_tree.insert("", "end", iid=str(index), tags=("win" if row[0] == "W" else "loss" if row[0] == "L" else "",), values=row[:6])
        def show_history(_event=None):
            selected = history_tree.selection(); history_detail.config(state="normal"); history_detail.delete("1.0", "end"); history_detail.insert("end", rows[int(selected[0])][6] if selected else "Select a fight card to view its full recorded context."); history_detail.config(state="disabled")
        history_filter.trace_add("write", render_history); history_tree.bind("<<TreeviewSelect>>", show_history); render_history()

        if fighter.serious_injury_history:
            medical = tk.Text(history_frame, wrap="word", height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            medical.pack(fill="x", padx=8, pady=(0, 8))
            medical.insert("end", "MEDICAL HISTORY\n" + "\n".join(str(item) for item in fighter.serious_injury_history[-4:]))
            medical.config(state="disabled")
        if fighter.rivalry_history:
            rivalry_log = tk.Text(history_frame, wrap="word", height=4, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            rivalry_log.pack(fill="x", padx=8, pady=(0, 8))
            rivalry_log.insert("end", "RIVALRY TIMELINE\n" + "\n".join(str(item) for item in fighter.rivalry_history[-4:]))
            rivalry_log.config(state="disabled")
        if fighter.weight_class_history:
            division_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            division_log.pack(fill="x", padx=8, pady=(0, 8))
            division_log.insert("end", "DIVISION HISTORY\n" + "\n".join(str(item) for item in fighter.weight_class_history[-3:]))
            division_log.config(state="disabled")
        if fighter.career_achievements:
            achievement_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 9), padx=10, pady=8)
            achievement_log.pack(fill="x", padx=8, pady=(0, 8))
            achievement_log.insert("end", "CAREER ACHIEVEMENTS\n" + " • ".join(fighter.career_achievements[-6:]))
            achievement_log.config(state="disabled")
        if fighter.career_goal_history:
            goal_log = tk.Text(history_frame, wrap="word", height=3, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
            goal_log.pack(fill="x", padx=8, pady=(0, 8))
            goal_log.insert("end", "CAREER GOALS\nActive: " + (fighter.career_goal or "Undeclared") + f" ({getattr(fighter, 'career_goal_progress', 0)}%)\n" + "\n".join(fighter.career_goal_history[-2:]))
            goal_log.config(state="disabled")

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Market Identity", command=lambda: self.open_regional_identity_window(fighter)).pack(side="left", padx=4)
        if fighter in self.roster:
            ttk.Button(footer, text="Change Weight Class", command=lambda: self.open_weight_class_move_dialog(fighter, window)).pack(side="left", padx=4)
        elif fighter in self.free_agents and not fighter.retired:
            ttk.Button(footer, text="Negotiate Contract", style="Accent.TButton", command=lambda: self.open_contract_negotiation(fighter, existing=False)).pack(side="left", padx=4)
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
            ttk.Label(window, text="Recent market moments: " + " | ".join(f"M{item.get('month', '?')} {item.get('region', '')}: {item.get('note', '')}" for item in history[:3]), style="Inset.TLabel", wraplength=720).pack(fill="x", padx=10, pady=(0, 6))
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
        text.insert("end", "Findings:\n" + ("\n".join(f"- {note}" for note in report.get('notes', [])) or "- No verified findings yet.") + "\n\nA Full Scout report is required for detailed ratings and negotiations.")
        text.config(state="disabled"); ttk.Button(window, text="Close", command=window.destroy).pack(anchor="e", padx=10, pady=(0, 10))

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
        target = tk.StringVar(value=fighter.weight)
        combo = ttk.Combobox(row, textvariable=target, values=WEIGHTS, state="readonly", width=20)
        combo.pack(side="left")
        assessment = ttk.Label(body, text="Choose a target division to check body and cut suitability.", style="Inset.TLabel", wraplength=560, justify="left")
        assessment.pack(fill="x", padx=10, pady=(8, 4))

        def refresh_assessment(_event=None):
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

    def refresh_available(self):
        used = self.scheduled_fighter_names(include_booked=True)
        self.available_tree.delete(*self.available_tree.get_children())
        weight = self.available_weight_filter.get() if hasattr(self, "available_weight_filter") else "All"
        gender = self.available_gender_filter.get() if hasattr(self, "available_gender_filter") else "All"
        status = self.available_status_filter.get() if hasattr(self, "available_status_filter") else "Ready"
        query = self.available_search.get().strip() if hasattr(self, "available_search") else ""
        for fighter in sorted(self.roster, key=lambda f: (WEIGHTS.index(f.weight), self.division_rank_number(f) or 99, -f.overall, -f.popularity)):
            if fighter.name in used:
                continue
            if weight != "All" and fighter.weight != weight:
                continue
            if gender != "All" and fighter.gender != gender:
                continue
            if not self.fighter_matches_status_filter(fighter, status):
                continue
            if not self.fighter_matches_text_filter(fighter, query):
                continue
            name = self.fighter_display_name(fighter)
            self.available_tree.insert("", "end", iid=fighter.name, values=(name, fighter.gender, fighter.weight, self.division_rank_label(fighter), fighter.record, fighter.overall, fighter.popularity, self.fight_build_score(fighter), fighter.status))

    def scheduled_fighter_names(self, include_booked=False):
        names = set()
        if include_booked:
            for fight in self.booked:
                names.update(name for name in fight.get("fighters", []) if name != "TBA")
        for event in self.scheduled_events:
            if self.is_event_due(event) or (event.get("month", 1), event.get("week", 1)) >= (self.month, self.week):
                for fight in event.get("fights", []):
                    names.update(name for name in fight.get("fighters", []) if name != "TBA")
        return names

    def fighter_busy_message(self, names):
        busy = self.scheduled_fighter_names(include_booked=False)
        conflicts = [name for name in names if name in busy]
        if conflicts:
            messagebox.showwarning("Already scheduled", f"{', '.join(conflicts)} already has a future fight scheduled. A fighter cannot be booked again until that event has been completed.")
            return True
        return False

    def refresh_card(self):
        self.card_tree.delete(*self.card_tree.get_children())
        self.normalize_card_order()
        for index, fight in enumerate(self.booked, 1):
            if fight.get("main") and fight.get("interim"):
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
            if "TBA" in fight["fighters"]:
                known = self.get_fighter(next(name for name in fight["fighters"] if name != "TBA"))
                tba_label = f"TBA {fight.get('tba_gender', known.gender)} {fight.get('tba_weight', known.weight)}"
                self.card_tree.insert("", "end", iid=str(index - 1), values=(slot, f"{known.name} vs {tba_label}", known.weight, self.fight_build_score(known), "TBA"))
            else:
                a, b = [self.get_fighter(name) for name in fight["fighters"]]
                self.card_tree.insert("", "end", iid=str(index - 1), values=(slot, f"{a.name} vs {b.name}", a.weight, self.fight_hype(a, b, fight), self.match_build_score(a, b, fight)))
        if hasattr(self, "event_name") and self.booked and self.is_auto_event_name(self.event_name.get()):
            self.event_name.set(self.default_event_name())
        self.refresh_event_atmosphere_forecast()

    def event_date_label(self, event):
        return f"Month {event.get('month', self.month)} Week {event.get('week', 1)}"

    def next_player_event_number(self):
        return len(self.result_history) + len(self.scheduled_events) + 1

    def main_event_name_from_card(self, fights=None):
        fights = fights or self.booked
        if not fights:
            return "Main Event"
        self.normalize_card_order()
        main = next((fight for fight in fights if fight.get("main")), fights[0])
        names = main.get("fighters", [])
        if len(names) != 2:
            return "Main Event"
        return f"{names[0]} vs {names[1]}"

    def default_event_name(self, number=None, fights=None):
        number = number or self.next_player_event_number()
        return f"{self.player_company_name} {number}: {self.main_event_name_from_card(fights)}"

    def is_auto_event_name(self, value):
        value = (value or "").strip()
        if not value:
            return True
        if not value.startswith(f"{self.player_company_name} "):
            return False
        rest = value[len(self.player_company_name):].strip()
        first = rest.split(":", 1)[0].split(" ", 1)[0]
        return first.isdigit()

    def sorted_scheduled_events(self):
        return sorted(self.scheduled_events, key=lambda show: (show.get("month", 1), show.get("week", 1), show.get("name", "")))

    def is_event_due(self, event):
        return (event.get("month", 1), event.get("week", 1)) <= (self.month, self.week)

    def refresh_upcoming(self):
        if hasattr(self, "event_broadcaster_box"):
            names = ["No Coverage"] + [item["name"] for item in self.broadcasters]
            self.event_broadcaster_box.configure(values=names)
            if self.event_broadcaster.get() not in names:
                self.event_broadcaster.set("No Coverage")
            self.refresh_event_broadcaster_status()
            self.refresh_event_atmosphere_forecast()
        self.upcoming_tree.delete(*self.upcoming_tree.get_children())
        for index, event in enumerate(self.sorted_scheduled_events()):
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
        history.insert("end", "RECENT CROWD MEMORIES\n" + ("\n".join(f"Month {item.get('month', '?')}: {item.get('event', 'Event')} — {item.get('mood', 'Engaged')} {item.get('intensity', 50)}/100, attendance {item.get('attendance', 0):,}." for item in events[:5]) or "No player events have created fanbase memories yet."))
        history.config(state="disabled")

    def refresh_market(self):
        self.ensure_free_agent_depth()
        self.market_tree.delete(*self.market_tree.get_children())
        for fighter in sorted(self.free_agents, key=lambda f: (not self.is_blue_chip_prospect(f), -f.overall, -f.potential)):
            if self.market_weight_filter.get() != "All" and fighter.weight != self.market_weight_filter.get():
                continue
            if self.market_gender_filter.get() != "All" and fighter.gender != self.market_gender_filter.get():
                continue
            offer = ""
            if getattr(fighter, "ai_offer_company", ""):
                offer = f"{fighter.ai_offer_company}: ${fighter.ai_offer_purse:,}"
            report = getattr(self, "scouting_reports", {}).get(fighter.name, {})
            tag = "FULL" if report.get("reveal") == 100 else (f"SCOUT {report.get('reveal', 0)}%" if self.rules.get("scouting_mode", False) else ("BLUE CHIP" if self.is_blue_chip_prospect(fighter) else ""))
            reveal = report.get("reveal", 0) if self.rules.get("scouting_mode", False) else 100
            def known(value, threshold, estimate=False):
                if reveal >= threshold:
                    return value
                if estimate and reveal >= 25:
                    return f"~{max(1, int(value) + random.randint(-8, 8))}"
                return "?"
            self.market_tree.insert("", "end", iid=fighter.name, values=(fighter.name, tag, fighter.gender[0], fighter.weight, fighter.record, fighter.age, known(fighter.overall, 45, True), known(fighter.popularity, 35, True), known(fighter.star_quality, 60), known(fighter.media_presence, 60), known(fighter.professionalism, 55), known(fighter.style, 25), f"${fighter.purse:,}", offer))
        self.refresh_market_scout_panel()

    def market_scout_summary(self, fighter):
        report = getattr(self, "scouting_reports", {}).get(fighter.name, {})
        reveal = report.get("reveal", 0) if self.rules.get("scouting_mode", False) else 100
        confidence = f"{reveal}% confidence" if self.rules.get("scouting_mode", False) else "Full public info"
        if reveal < 35:
            grade = "Blind look"
            recommendation = "Run a basic scout before spending serious money."
        elif reveal < 65:
            grade = "Partial read"
            recommendation = "Negotiate carefully; upside and professionalism are still fuzzy."
        elif fighter.potential >= fighter.overall + 12 and fighter.age <= 27:
            grade = "Development target"
            recommendation = "Good academy/gym upside if the asking price is sane."
        elif fighter.popularity + fighter.star_quality >= 135:
            grade = "Marketable signing"
            recommendation = "Useful for ticket/media growth, especially on regional cards."
        elif fighter.overall >= 76:
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
            f"Record {fighter.record} | Style {fighter.style if reveal >= 25 or reveal == 100 else 'Unknown'}\n\n"
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
            fighter = next((row for row in self.free_agents if row.name == selected[0]), None)
            self.market_scout_text.insert("end", self.market_scout_summary(fighter) if fighter else "This fighter is no longer on the market.")
        self.market_scout_text.config(state="disabled")

    def toggle_scouting_mode(self):
        self.rules["scouting_mode"] = bool(self.scouting_mode_var.get())
        self.refresh_market()

    def start_selected_scout_report(self, kind):
        selected = self.market_tree.selection()
        if not selected:
            messagebox.showinfo("Scouting", "Select a free agent first.")
            return
        fighter = next((row for row in self.free_agents if row.name == selected[0]), None)
        if not fighter:
            return
        scout = max((staff for staff in self.staff if staff.get("role") == "Scout"), key=lambda staff: staff.get("fighter_judging", staff.get("skill", 0)), default={"skill": 45})
        home_bonus = 8 if fighter.region == self.player_region else 0
        judging = (scout.get("fighter_judging", scout.get("skill", 45)) + scout.get("potential_judging", scout.get("skill", 45)) + scout.get("reliability", 45) + scout.get("professionalism", 45)) / 4
        efficiency = scout.get("efficiency", scout.get("skill", 45))
        market_edge = (scout.get("regional_knowledge", 45) - 50) * 0.18 + (scout.get("networking", 45) - 50) * 0.12 + home_bonus
        reveal = 100 if kind == "full" else max(20, min(90, round(judging * 0.88 + market_edge + random.randint(-10, 10))))
        self.scouting_reports = getattr(self, "scouting_reports", {})
        weeks = 6 if kind == "full" else 2
        if efficiency >= 80: weeks = max(1, weeks - 1)
        notes = []
        if reveal >= 35:
            notes.append("Strong striking base" if fighter.striking >= fighter.wrestling else "Reliable wrestling base")
        if reveal >= 50:
            notes.append("High upside" if fighter.potential >= fighter.overall + 12 else "Limited upside")
        if reveal >= 65:
            notes.append("Durable and well-conditioned" if fighter.cardio + fighter.chin >= 145 else "Conditioning or durability concern")
        if reveal >= 80:
            notes.append("Professional preparation" if fighter.professionalism >= 70 else "Preparation consistency concern")
        self.scouting_reports[fighter.name] = {"kind": kind, "status": "In progress", "weeks_remaining": weeks, "reveal": reveal, "scout": scout.get("name", "Independent Scout"), "region": fighter.region, "notes": notes}
        self.scouting.append(f"{scout.get('name', 'Independent Scout')} began a {kind} report on {fighter.name}.")
        self.refresh_market()

    def ensure_free_agent_depth(self, minimum=None):
        if minimum is None:
            minimum = max(120, self.rules.get("active_fighter_target", 1200) - self.total_active_fighters(exclude_free_agents=True))
        created = 0
        existing_names = self.active_fighter_names()
        while len(self.free_agents) < minimum:
            fighter = self.create_generated_fighter(3, 38, 34, 78)
            self.avoid_name_collision(fighter, existing_names)
            self.free_agents.append(fighter)
            created += 1
        before = len(self.free_agents)
        self.ensure_free_agent_division_depth(self.free_agents, min_per_bucket=5)
        created += len(self.free_agents) - before
        if created:
            self.news.insert(0, f"{created} new free agents entered the market after scouting reports were updated.")

    def total_active_fighters(self, exclude_free_agents=False):
        total = len([f for f in self.roster if not f.retired])
        total += sum(len([f for f in promo.roster if not f.retired]) for promo in self.promotions)
        if not exclude_free_agents:
            total += len([f for f in self.free_agents if not f.retired])
        return total

    def ensure_world_fighter_target(self):
        target = self.rules.get("active_fighter_target", 1200)
        created = 0
        existing_names = {fighter.name for fighter in self.free_agents}
        year = 2026 + (self.month - 1) // 12
        active_total = self.total_active_fighters()
        late_target = target
        if year >= 2040:
            late_target = max(late_target, 1450)
        if year >= 2050:
            late_target = max(late_target, 1550)
        fill_target = target if active_total < target else active_total
        if year >= 2040 and active_total < late_target:
            fill_target = min(late_target, active_total + max(10, min(52, (late_target - active_total) // 4)))
        while self.total_active_fighters() < fill_target:
            gender, weight = self.thinnest_world_division()
            fighter = self.create_generated_fighter(4, 34, 36, 80, weight=weight, gender=gender)
            self.avoid_name_collision(fighter, existing_names)
            fighter.age = random.choices(range(18, 27), weights=[13, 15, 16, 15, 13, 10, 8, 6, 4], k=1)[0]
            fighter.purse = max(2500, min(fighter.purse, random.randint(4500, 18000)))
            fighter.contract_type = "Free Agent"
            fighter.free_agent_months = 0
            self.free_agents.append(fighter)
            existing_names.add(fighter.name)
            created += 1
        if created:
            if year >= 2040:
                self.news.insert(0, f"Next generation wave: {created} young fighters entered the market to replenish thinning divisions.")
                self.record_world_story("Next Generation", f"{created} young fighters enter the market.", "Late-era world health check filled thin gender/weight divisions through gyms, regional circuits, and independent scouting.", importance=2)
            else:
                self.news.insert(0, f"{created} new fighters entered the world to keep the active talent pool healthy.")

    def thinnest_world_division(self):
        active = [fighter for fighter in self.all_fighter_objects() if not getattr(fighter, "retired", False)]
        counts = {}
        for gender in ("Male", "Female"):
            for weight in WEIGHTS:
                counts[(gender, weight)] = sum(1 for fighter in active if fighter.gender == gender and fighter.weight == weight)
        return min(counts, key=lambda key: (counts[key], 0 if key[0] == "Female" else 1, random.random()))

    def refresh_world(self):
        self.promo_tree.delete(*self.promo_tree.get_children())
        player_row = (self.player_company_name, self.player_region, "Player", self.company_pop, self.company_pop, f"${self.cash:,}", "0", self.event_log[0] if self.event_log else "No shows yet")
        self.promo_tree.insert("", "end", values=player_row)
        for promo in sorted(self.promotions, key=lambda p: -p.reputation_score):
            if promo.show_history is None:
                promo.show_history = []
            last = promo.show_history[0] if promo.show_history else "No shows yet"
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
            for gym in sorted(getattr(self, "gyms", []), key=lambda g: (g.reputation, g.quality), reverse=True):
                self.gym_tree.insert("", "end", values=(gym.name, gym.region, gym.quality, gym.reputation, gym.morale, f"{gym.member_count}/{gym.capacity}", ", ".join(gym.specialties)))

    def show_selected_world_story(self, _event=None):
        if not hasattr(self, "world_news_detail"):
            return
        selected = self.world_news_list.curselection() if hasattr(self, "world_news_list") else []
        entry = self._world_news_entries[selected[0]] if selected and selected[0] < len(getattr(self, "_world_news_entries", [])) else None
        self.world_news_detail.config(state="normal")
        self.world_news_detail.delete("1.0", "end")
        if entry:
            self.world_news_detail.insert("end", f"{entry.get('detail', entry.get('headline', ''))}\n\nMonth {entry.get('month', self.month)} / Week {entry.get('week', self.week)}")
        self.world_news_detail.config(state="disabled")

    def open_selected_world_story_context(self):
        selected = self.world_news_list.curselection() if hasattr(self, "world_news_list") else []
        if not selected:
            return
        entry = self._world_news_entries[selected[0]]
        fighters = entry.get("fighters", [])
        fighter = next((self.find_fighter_anywhere(name) for name in fighters if self.find_fighter_anywhere(name)), None)
        if fighter:
            self.open_fighter_profile_window(fighter)
        elif entry.get("type") in ("Event", "Independent Showcase"):
            self.select_tab("results")
        elif entry.get("type") in ("Major Signing", "Regional Breakthrough"):
            self.select_tab("market")

    def open_combat_sports_window(self):
        window = tk.Toplevel(self.root)
        window.title("Combat Sports Universe")
        window.geometry("1120x680")
        window.minsize(920, 560)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="COMBAT SPORTS UNIVERSE", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 4))
        ttk.Label(window, text="Each sport has an AI flagship circuit. You can open one child division under your MMA business, sign specialists, run smart cards, and graduate academy prospects into it.", style="Inset.TLabel").pack(fill="x", padx=12, pady=(0, 8))
        tree = ttk.Treeview(window, columns=("sport", "promotion", "strategy", "roster", "player", "champion", "events", "latest"), show="headings")
        for column, label, width in (("sport", "Sport", 125), ("promotion", "AI Flagship", 210), ("strategy", "AI Strategy", 120), ("roster", "Roster", 60), ("player", "Your Division", 115), ("champion", "Champion", 160), ("events", "Cards", 60), ("latest", "Latest Media", 260)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        detail = tk.Text(window, height=7, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
        detail.config(state="disabled")

        def redraw():
            tree.delete(*tree.get_children())
            for sport, world in getattr(self, "combat_sport_worlds", {}).items():
                division = getattr(self, "player_combat_divisions", {}).get(sport, {})
                owned = f"Open ({len(division.get('roster', []))})" if division else "Not opened"
                tree.insert("", "end", iid=sport, values=(sport, world.get("promotion", ""), world.get("strategy", "Merit Ladder"), len(world.get("roster", [])), owned, world.get("champion", "Uncrowned") or "Uncrowned", world.get("events", 0), (world.get("media", []) or ["No major story yet."])[0]))
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
            lines = [
                f"{sport or 'Select a sport'}",
                f"AI flagship: {world.get('promotion', '-')}. Strategy: {world.get('strategy', 'Merit Ladder')}. Roster: {len(world.get('roster', []))}.",
                f"Your child division: {'opened' if division else 'not opened'}" + (f" | Strategy {division.get('strategy', 'Balanced')} | Athletes {len(division.get('roster', []))} | Net ${division.get('profit_total', 0):,}" if division else ""),
                "Top AI athletes: " + (", ".join(fighter.name for fighter in ranked) if ranked else "None"),
                "Latest: " + (latest[0] if latest else "No cards yet."),
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
        ttk.Button(actions, text="Open / Manage Your Division", style="Accent.TButton", command=manage).pack(side="left")
        ttk.Button(actions, text="Refresh", command=redraw).pack(side="left", padx=6)
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right")

    def open_player_combat_division_window(self, sport):
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
        if not division or not world:
            messagebox.showinfo("Combat Sports", "Open that player division first.")
            return
        window = tk.Toplevel(self.root)
        window.title(f"{self.player_company_name} - {sport} Division")
        window.geometry("1040x650")
        window.minsize(840, 520)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        title = ttk.Label(header, text=f"{sport.upper()} DIVISION", style="ScreenTitle.TLabel")
        title.pack(side="left", padx=10, pady=5)
        summary_var = tk.StringVar(value="")
        strategy_var = tk.StringVar(value=division.get("strategy", "Balanced"))
        ttk.Label(header, textvariable=summary_var, style="ScreenTitle.TLabel").pack(side="right", padx=10)
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        roster_tree = ttk.Treeview(body, columns=("rank", "name", "discipline", "record", "age", "ovr", "dev", "pop", "status"), show="headings", height=16)
        for column, label, width in (("rank", "#", 42), ("name", "Athlete", 170), ("discipline", "Discipline", 105), ("record", "Record", 75), ("age", "Age", 45), ("ovr", "OVR", 52), ("dev", "Dev", 52), ("pop", "Pop", 50), ("status", "Status", 95)):
            roster_tree.heading(column, text=label); roster_tree.column(column, width=width, anchor="w")
        roster_tree.pack(side="left", fill="both", expand=True, padx=(0, 8))
        side = ttk.Frame(body, style="Panel.TFrame")
        side.pack(side="left", fill="both", expand=True)
        finance_line = ttk.Label(side, text="", style="Inset.TLabel", wraplength=420)
        finance_line.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(side, text="LATEST EVENTS", style="Section.TLabel").pack(fill="x")
        events = tk.Listbox(side, height=12, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        events.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(side, text="SIGNABLE FLAGSHIP ATHLETES", style="Section.TLabel").pack(fill="x")
        sign_tree = ttk.Treeview(side, columns=("name", "record", "age", "ovr", "cost"), show="headings", height=9)
        for column, label, width in (("name", "Athlete", 170), ("record", "Record", 75), ("age", "Age", 42), ("ovr", "OVR", 48), ("cost", "Cost", 75)):
            sign_tree.heading(column, text=label); sign_tree.column(column, width=width, anchor="w")
        sign_tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def roster_members():
            names = set(division.get("roster", []))
            return [fighter for fighter in world.get("roster", []) if fighter.name in names and fighter.sport_employer == self.player_company_name and not fighter.retired]

        def redraw():
            division.setdefault("strategy", "Balanced")
            division.setdefault("revenue_total", 0)
            division.setdefault("cost_total", division.get("budget", 0))
            division.setdefault("profit_total", division.get("revenue_total", 0) - division.get("cost_total", 0))
            division.setdefault("last_card_summary", "No player card yet.")
            division.setdefault("title_name", f"{self.player_company_name} {sport} Championship")
            strategy_var.set(division.get("strategy", "Balanced"))
            members = sorted(roster_members(), key=lambda fighter: (self.combat_sport_rating(fighter, sport), fighter.record_w - fighter.record_l), reverse=True)
            division["roster"] = [fighter.name for fighter in members]
            division["rankings"] = [fighter.name for fighter in members[:10]]
            if division.get("champion") not in division["roster"]:
                division["champion"] = members[0].name if members else ""
            summary_var.set(f"{division.get('title_name', sport + ' Title')}: {division.get('champion', 'Uncrowned') or 'Uncrowned'} | Roster {len(members)} | Cash ${self.cash:,}")
            finance_line.config(text=f"Strategy: {division.get('strategy', 'Balanced')} | Lifetime revenue ${division.get('revenue_total', 0):,} | Costs ${division.get('cost_total', 0):,} | Net ${division.get('profit_total', 0):,} | Last: {division.get('last_card_summary', 'No player card yet.')}")
            roster_tree.delete(*roster_tree.get_children())
            for index, fighter in enumerate(members, 1):
                rank = "C" if fighter.name == division.get("champion") else index
                dev_gap = max(0, fighter.potential - fighter.overall)
                trend = ""
                if getattr(fighter, "annual_overalls", None):
                    years = sorted(fighter.annual_overalls)
                    if len(years) >= 2:
                        trend = fighter.annual_overalls[years[-1]] - fighter.annual_overalls[years[-2]]
                dev_text = f"+{dev_gap}" if not trend else f"+{dev_gap} ({trend:+})"
                roster_tree.insert("", "end", iid=fighter.name, values=(rank, fighter.name, fighter.primary_discipline, fighter.record, fighter.age, fighter.overall, dev_text, fighter.popularity, fighter.status))
            events.delete(0, "end")
            for event in division.get("events", [])[:25]:
                events.insert("end", event.get("recap") or event.get("headline", "Completed card"))
            if not division.get("events"):
                events.insert("end", "No player cards yet.")
            sign_tree.delete(*sign_tree.get_children())
            prospects = [fighter for fighter in self.combat_sport_ranked(sport, world.get("promotion", ""))[10:] if fighter.sport_employer == world.get("promotion", "") and not fighter.retired]
            for fighter in prospects[:40]:
                cost = max(8000, fighter.popularity * 450 + fighter.overall * 260)
                sign_tree.insert("", "end", iid=fighter.name, values=(fighter.name, fighter.record, fighter.age, fighter.overall, f"${cost:,}"))

        def run_card():
            if len(roster_members()) < 4:
                messagebox.showinfo("Combat Sports", "You need at least four active athletes to run a card.")
                return
            card = self.run_combat_sport_card(sport, world, self.player_company_name, player_owned=True, target_bouts=5)
            if not card:
                messagebox.showinfo("Combat Sports", "No suitable card could be built this month.")
            else:
                finance = card.get("finance", {})
                finance_text = f"\n\nRevenue ${finance.get('revenue', 0):,} | Cost ${finance.get('cost', 0):,} | Profit ${finance.get('profit', 0):,}" if finance else ""
                result_lines = "\n".join(item.get("result", "") for item in card.get("results", [])[:10])
                messagebox.showinfo(f"{sport} Card Recap", f"{card.get('recap', 'Card complete')}{finance_text}\n\n{result_lines}")
            redraw()
            self.refresh_all()

        def set_strategy():
            division["strategy"] = strategy_var.get() or "Balanced"
            self.news.insert(0, f"{self.player_company_name}'s {sport} division strategy set to {division['strategy']}.")
            redraw()

        def sign_selected():
            selected = sign_tree.selection()
            if not selected:
                messagebox.showinfo("Combat Sports", "Select an athlete to sign.")
                return
            fighter = next((candidate for candidate in world.get("roster", []) if candidate.name == selected[0]), None)
            if not fighter:
                return
            cost = max(8000, fighter.popularity * 450 + fighter.overall * 260)
            if self.cash < cost:
                messagebox.showwarning("Combat Sports", f"Need ${cost:,} to buy out/sign {fighter.name}.")
                return
            self.cash -= cost
            fighter.sport_employer = self.player_company_name
            division["roster"] = list(dict.fromkeys(division.get("roster", []) + [fighter.name]))
            fighter.fight_history = (fighter.fight_history or [])
            fighter.fight_history.insert(0, f"Month {self.month}: Signed with {self.player_company_name}'s {sport} division.")
            self.news.insert(0, f"{self.player_company_name} signed {fighter.name} to its {sport} division for ${cost:,}.")
            redraw()
            self.refresh_all()

        roster_tree.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(next((fighter for fighter in roster_members() if fighter.name == roster_tree.selection()[0]), None)) if roster_tree.selection() else None)
        controls = ttk.Frame(window, style="Chrome.TFrame")
        controls.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(controls, text="Strategy", style="Chrome.TLabel").pack(side="left", padx=(4, 2))
        ttk.Combobox(controls, values=("Balanced", "Prospect Builder", "Star Showcase", "Title Focus"), textvariable=strategy_var, state="readonly", width=17).pack(side="left", padx=3)
        ttk.Button(controls, text="Set Strategy", command=set_strategy).pack(side="left", padx=4)
        ttk.Button(controls, text="Run Smart Card", style="Accent.TButton", command=run_card).pack(side="left", padx=4)
        ttk.Button(controls, text="Sign Selected", command=sign_selected).pack(side="left", padx=4)
        ttk.Button(controls, text="Refresh", command=redraw).pack(side="left", padx=4)
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=4)
        redraw()

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
                if hasattr(self, "company_list"):
                    names = list(self.company_list.get(0, "end"))
                    if company in names:
                        self.company_list.selection_clear(0, "end")
                        self.company_list.selection_set(names.index(company))
                        self.open_selected_company_hub()
            elif entry.get("type") in ("Event", "Independent Showcase"):
                self.select_tab("results")

        def show_story(_event=None):
            selected = story_list.curselection()
            entry = rows[selected[0]] if selected and selected[0] < len(rows) else None
            detail.config(state="normal")
            detail.delete("1.0", "end")
            if entry:
                detail.insert("end", f"{entry.get('headline', '')}\n\n{entry.get('detail', '')}\n\nType: {entry.get('type', 'World')}\nDate: {entry.get('year', 2026)} / Month {entry.get('month', 1)} Week {entry.get('week', 1)}\nCompanies: {', '.join(entry.get('companies', [])) or '-'}\nFighters: {', '.join(entry.get('fighters', [])) or '-'}")
            detail.config(state="disabled")

        def render(*_):
            nonlocal rows
            rows = [entry for entry in getattr(self, "world_chronicle", []) if filter_var.get() == "All" or entry.get("type") == filter_var.get()]
            story_list.delete(0, "end")
            if not rows:
                story_list.insert("end", "No matching permanent stories yet.")
            for entry in rows:
                date = f"{entry.get('year', 2026)} | Month {entry.get('month', 1)}, Week {entry.get('week', 1)}"
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
        crowding = max(0, gym.member_count - gym.capacity)
        crowd_text = "Healthy room" if crowding == 0 else f"Over capacity by {crowding}; development gains are reduced"
        return (
            f"Head coach: {gym.head_coach}\n"
            f"Region: {gym.city}, {gym.region}\n"
            f"Quality: {gym.quality} | Facilities: {gym.facilities} | Reputation: {gym.reputation} | Room morale: {gym.morale}\n"
            f"Monthly fee: ${gym.monthly_fee:,} | Capacity: {gym.member_count}/{gym.capacity} | {crowd_text}\n"
            f"Specialties: {', '.join(gym.specialties)}\n\n"
            f"Tracked members: {len(members)} | Prospects: {prospects} | Elite fighters: {elites} | Average overall: {avg_overall}\n"
            f"Camp impact: Quality and facilities drive normal development. Specialties give extra boosts when they fit a fighter's style, "
            f"prospect gyms help younger fighters, conditioning gyms improve camp boosts, and overcrowded gyms slow progress.\n\n"
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
        window.geometry("980x650")
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

        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        info_panel, info = self.section(body, "GYM DOSSIER")
        info_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        info_text = tk.Text(info, wrap="word", font=("Tahoma", 10), bg="#141414", fg="#e8e3d6", insertbackground="#e8e3d6", padx=12, pady=12, relief="flat", height=12)
        info_text.pack(fill="both", expand=True)
        info_text.insert("end", self.gym_development_summary(gym, members))
        info_text.config(state="disabled")

        member_panel, member_inner = self.section(body, "FIGHTERS TRAINING HERE")
        member_panel.pack(side="left", fill="both", expand=True)
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
        for company, fighter in members:
            member_tree.insert("", "end", values=(fighter.name, company, fighter.gender[0], fighter.weight, fighter.age, fighter.overall, fighter.style, fighter.record, fighter.morale))
        member_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(member_tree, "name"))

        controls = ttk.Frame(window, style="Header.TFrame")
        controls.pack(fill="x")
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=8, pady=6)

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
                self.website_calendar.insert("end", f"> {promo.show_history[0]}\n")
        self.website_calendar.config(state="disabled")
        self.website_news.delete(0, "end")
        for index, item in enumerate(self.news[:40], 1):
            self.website_news.insert("end", f"{index}. {item}")

    def media_desk_fighter(self):
        name = self.media_fighter_choice.get() if hasattr(self, "media_fighter_choice") else ""
        return next((fighter for fighter in self.roster if fighter.name == name), None)

    def open_selected_story_context(self):
        if not hasattr(self, "website_news") or not self.website_news.curselection():
            return
        story = self.website_news.get(self.website_news.curselection()[0]).lower()
        fighter = next((candidate for _company, candidate in self.all_database_fighters_with_companies()
                        if candidate.name.lower() in story), None)
        if fighter:
            self.open_fighter_profile_window(fighter)
        elif any(word in story for word in ("signed", "contract", "free agent", "scouting")):
            self.select_tab("market")
        elif any(word in story for word in ("event", "def.", "title", "showcase")):
            self.select_tab("results")
        else:
            self.select_tab("world")

    def refresh_media_targets(self, _event=None):
        if not hasattr(self, "media_target_combo"):
            return
        speaker = self.media_desk_fighter()
        targets = [fighter.name for fighter in self.roster if speaker and fighter.name != speaker.name
                   and fighter.gender == speaker.gender and fighter.weight == speaker.weight]
        self.media_target_combo.configure(values=targets)
        if self.media_target_choice.get() not in targets:
            self.media_target_choice.set(targets[0] if targets else "")

    def media_desk_callout(self):
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

    def media_desk_interview(self):
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

    def media_desk_press_tour(self):
        fighter = self.media_desk_fighter()
        if not fighter:
            messagebox.showinfo("Media Desk", "Choose a spokesperson first.")
            return
        cost = 7_500 + max(0, fighter.popularity - 40) * 180
        if self.cash < cost:
            messagebox.showwarning("Media Desk", f"A press tour for {fighter.name} costs ${cost:,}.")
            return
        self.cash -= cost
        impact = max(2, round((fighter.media_presence + fighter.charisma + self.staff_skill("Marketing")) / 42))
        fighter.media_heat = min(100, fighter.media_heat + impact * 3)
        fighter.popularity = min(100, fighter.popularity + max(1, impact // 2))
        fighter.morale = min(100, fighter.morale + 2)
        headline = f"{fighter.name} begins a ${cost:,} press tour."
        self.news.insert(0, headline)
        self.record_world_story("Media", headline, f"Media heat +{impact * 3}; popularity +{max(1, impact // 2)}.", [self.player_company_name], [fighter.name], 2)
        self.refresh_all()

    def refresh_assistant(self):
        upcoming = self.sorted_scheduled_events()
        snapshot = (
            f"{self.player_company_name}\n"
            f"Size: {'High Level International' if self.company_pop > 65 else 'Regional'}\n"
            f"Current Finances: ${self.cash:,}\n"
            f"Credibility: {self.company_pop + 20 if self.company_pop < 80 else 96}%\n"
            f"Stability: {self.company_stability}%\n"
            f"Upcoming Shows: {len(upcoming)}"
        )
        self.assistant_snapshot.config(text=snapshot)
        self.assistant_messages.delete(*self.assistant_messages.get_children())
        messages = []
        for event in upcoming[:8]:
            fights = len(event["fights"])
            if fights < 6:
                messages.append(("!", f"{event['name']} only has {fights} fights; commercial and critical ratings may suffer.", "booking", "urgent"))
            if not any(f.get("main") for f in event["fights"]):
                messages.append(("!", f"{event['name']} does not have a declared main event.", "booking", "urgent"))
        for fighter in self.roster:
            if fighter.contract_months <= 3:
                messages.append(("!", f"{fighter.name}'s contract expires in {fighter.contract_months} months.", "contracts", "urgent"))
            if fighter.injured:
                messages.append(("!", f"{fighter.name} is injured for {fighter.injured} more month(s).", "roster", "urgent"))
            if fighter.fatigue >= 65:
                messages.append(("!", f"{fighter.name} is badly fatigued and should not be booked.", "roster", "urgent"))
        for weight in WEIGHTS:
            count = len([f for f in self.roster if f.weight == weight])
            if count < 4:
                messages.append(("•", f"The {weight} division only has {count} fighters in it.", "market", "normal"))
        if not messages:
            messages.append(("•", "No urgent issues. The company is ready for normal booking.", "booking", "normal"))
        self._assistant_messages = messages[:60]
        for index, (priority, message, action, tag) in enumerate(self._assistant_messages):
            self.assistant_messages.insert("", "end", iid=str(index), tags=(tag,), values=(priority, message, action.title()))

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
        for company, fighter in sorted(local, key=lambda row: -self.p4p_value(row[1])): fighter_tree.insert("", "end", iid=fighter.name, values=(fighter.name, company, fighter.weight, fighter.record, fighter.overall))
        fighter_tree.pack(fill="both", expand=True, padx=8, pady=8)
        fighter_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(fighter_tree, "name"))
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

    def open_academy_window(self):
        academy = self.academy
        if not academy.get("owned"):
            cost = 180000
            if messagebox.askyesno("Fighting Academy", f"Open a fighting academy for ${cost:,}? It begins with 8 places and $4,500 weekly costs. Youths must be scouted before they appear."):
                if self.cash < cost: messagebox.showwarning("Academy", "Not enough cash."); return
                self.cash -= cost; academy.update(self.academy_defaults()); academy.update({"owned": True, "level": 1, "capacity": 8, "weekly_cost": 4500, "last_scout_report": "Hire or use a Scout to establish a regional youth network."}); self.refresh_all()
            return
        self.repair_academy(academy)
        window = tk.Toplevel(self.root); window.title("MMA Warriors - Fighting Academy"); window.geometry("1120x720"); window.minsize(880, 560); window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="FIGHTING ACADEMY", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=8)
        status = ttk.Label(window, style="Inset.TLabel"); status.pack(fill="x", padx=10)
        report = ttk.Label(window, style="Inset.TLabel", wraplength=1060); report.pack(fill="x", padx=10, pady=(4, 0))
        network = ttk.Frame(window, style="Chrome.TFrame"); network.pack(fill="x", padx=10, pady=6)
        scout_names = [member.get("name", "") for member in self.staff if member.get("role") == "Scout"] or ["Staff Scout"]
        scout_var = tk.StringVar(value=academy.get("network_scout") or scout_names[0])
        region_var = tk.StringVar(value=academy.get("network_region") or self.player_region)
        ttk.Label(network, text="Scout", style="Chrome.TLabel").pack(side="left", padx=(4, 2))
        ttk.Combobox(network, values=scout_names, textvariable=scout_var, state="readonly", width=22).pack(side="left", padx=3)
        ttk.Label(network, text="Region", style="Chrome.TLabel").pack(side="left", padx=(12, 2))
        ttk.Combobox(network, values=REGIONS, textvariable=region_var, state="readonly", width=18).pack(side="left", padx=3)
        body = ttk.Panedwindow(window, orient="horizontal"); body.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(body, style="Panel.TFrame"); right = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=1); body.add(right, weight=2)
        ttk.Label(left, text="RECRUITMENT LEADS", style="Section.TLabel").pack(fill="x")
        talent = tk.Listbox(left, width=52, font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff"); talent.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Label(right, text="SIGNED PROSPECTS", style="Section.TLabel").pack(fill="x")
        prospects = tk.Listbox(right, width=78, font=("Tahoma", 10), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff"); prospects.pack(fill="both", expand=True, padx=8, pady=8)
        training_plans = ['Automatic', 'Balanced', 'Wrestling', 'Boxing', 'Muay Thai', 'BJJ', 'Judo', 'Sambo', 'Clinch', 'Cardio', 'Strength', 'Fight IQ']
        focus_var = tk.StringVar(value="Automatic")
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
            showcase = f"{academy.get('showcase_weeks', 2)}w" if academy.get("auto_showcases", True) else "Off"
            status.config(text=f"Level {academy['level']} | Capacity {len(academy['prospects'])}/{academy['capacity']} | Weekly cost ${academy['weekly_cost']:,} | Network {net} | Auto training {'On' if academy.get('auto_train', True) else 'Off'} | Next showcase {showcase}")
            report.config(text=academy.get("last_scout_report", "Scout youth prospects to build the shortlist."))
            talent.delete(0, 'end'); prospects.delete(0, 'end')
            for item in academy['talent_pool']:
                talent.insert('end', self.academy_recruitment_label(item))
            for item in academy['prospects']:
                self.repair_academy_prospect(item)
                injury = f" | INJ {item['injured']}w" if item.get("injured", 0) else ""
                prospects.insert('end', f"{item['name']} | age {item['age']} | {item['amateur_weight']} | {item['plan']} (rec {self.recommended_academy_focus(item)}) | {item['amateur_w']}-{item['amateur_l']}-{item.get('amateur_d', 0)} | {item['rating']}/{item['potential']} | Dev {item.get('development', 0)} | S{item['striking']} W{item['wrestling']} G{item['grappling']}{injury}")
        def sign():
            if not talent.curselection() or len(academy['prospects']) >= academy['capacity']: return
            item = academy['talent_pool'][talent.curselection()[0]]
            cost = item.get('signing_cost') or self.academy_signing_cost(item)
            if self.cash < cost: messagebox.showwarning('Academy', f'Signing {item["name"]} costs ${cost:,}.'); return
            self.cash -= cost
            item = academy['talent_pool'].pop(talent.curselection()[0]); item.update({'plan': 'Automatic', 'amateur_w': 0, 'amateur_l': 0, 'amateur_d': 0, 'amateur_history': [], 'weeks': 0, 'development': 0, 'weeks_to_sign': 0}); self.repair_academy_prospect(item); academy['prospects'].append(item); academy['last_scout_report'] = f"Signed {item['name']} into the academy for ${cost:,}."; redraw(); self.refresh_all()
        def pass_lead():
            if not talent.curselection(): return
            item = academy['talent_pool'].pop(talent.curselection()[0]); academy['last_scout_report'] = f"Passed on {item.get('name', 'a youth lead')} from the {item.get('region', 'regional')} youth list."; redraw()
        def set_training_focus():
            if not prospects.curselection(): return
            item = academy['prospects'][prospects.curselection()[0]]
            item['plan'] = focus_var.get() or 'Automatic'
            academy['last_scout_report'] = f"{item['name']} training focus set to {item['plan']}."
            redraw()
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
                f"Amateur record: {item['amateur_w']}-{item['amateur_l']}-{item.get('amateur_d', 0)}",
                "",
            ]
            for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
                lines.append(bar(key.title(), item.get(key, 40)))
            lines += ["", "AMATEUR HISTORY"] + (item.get("amateur_history", [])[:30] or ["No amateur bouts yet."])
            text.insert("end", "\n".join(lines)); text.config(state="disabled")
        def amateur_bout():
            results = self.run_academy_showcase_card(academy)
            if not results: messagebox.showinfo('Academy', 'Two eligible academy prospects of the same gender are needed.'); return
            academy['showcase_weeks'] = 2
            academy['last_scout_report'] = f"Manual academy showcase: {len(results)} bout(s). {results[0]}"
            redraw()
            messagebox.showinfo("Academy Card Recap", f"{len(results)} bout(s) completed.\n\n" + "\n".join(results[:10]))
        def promote():
            if not prospects.curselection(): return
            item = academy['prospects'][prospects.curselection()[0]]
            if item['age'] < 18: messagebox.showinfo('Academy', 'A prospect must be 18 to turn professional.'); return
            ok, note, fighter = self.promote_academy_prospect_to_sport(item, destination_var.get() or "MMA")
            if not ok: messagebox.showwarning("Academy", note); return
            academy['prospects'].remove(item)
            academy['last_scout_report'] = note
            self.news.insert(0, note)
            redraw(); self.refresh_all()
        controls = ttk.Frame(window, style='Inset.TFrame'); controls.pack(fill='x', padx=10, pady=(0, 8))
        def upgrade():
            if self.cash < 50000: messagebox.showwarning('Academy', 'Upgrade costs $50,000.'); return
            self.cash -= 50000; academy.update({'capacity': academy['capacity'] + 2, 'level': academy['level'] + 1, 'weekly_cost': academy['weekly_cost'] + 1800}); redraw()
        def start_network():
            ok, message = self.start_academy_network(region_var.get(), scout_var.get())
            if not ok: messagebox.showwarning("Academy", message)
            redraw(); self.refresh_all()
        def cancel_network():
            ok, message = self.cancel_academy_network()
            if not ok: messagebox.showinfo("Academy", message)
            redraw()
        ttk.Button(network, text="Set Up Network", style="Accent.TButton", command=start_network).pack(side="left", padx=6)
        ttk.Button(network, text="Cancel Network", command=cancel_network).pack(side="left", padx=3)
        ttk.Button(controls, text='Sign Selected Talent', command=sign).pack(side='left', padx=3); ttk.Button(controls, text='Pass Selected Lead', command=pass_lead).pack(side='left', padx=3); ttk.Label(controls, text='Focus', style='Inset.TLabel').pack(side='left', padx=(8, 2)); ttk.Combobox(controls, values=training_plans, textvariable=focus_var, state='readonly', width=12).pack(side='left', padx=2); ttk.Button(controls, text='Set Focus', command=set_training_focus).pack(side='left', padx=3); ttk.Button(controls, text='Profile/History', command=open_prospect_profile).pack(side='left', padx=3); ttk.Button(controls, text='Run Amateur Card', command=amateur_bout).pack(side='left', padx=3); ttk.Label(controls, text='Promote to', style='Inset.TLabel').pack(side='left', padx=(8, 2)); ttk.Combobox(controls, values=destinations, textvariable=destination_var, state='readonly', width=16).pack(side='left', padx=2); ttk.Button(controls, text='Promote', style='Accent.TButton', command=promote).pack(side='left', padx=4); ttk.Button(controls, text='Upgrade Capacity (+2)', command=upgrade).pack(side='right', padx=3)
        prospects.bind("<Double-1>", lambda _event: open_prospect_profile())
        redraw()

    def refresh_companies(self):
        current = self.company_list.curselection()
        self.company_list.delete(0, "end")
        self.company_list.insert("end", self.player_company_name)
        for promo in sorted(self.promotions, key=lambda p: p.name):
            self.company_list.insert("end", promo.name)
        if current:
            self.company_list.selection_set(min(current[0], self.company_list.size() - 1))
        elif self.company_list.size():
            self.company_list.selection_set(0)
        self.refresh_company_profile()

    def refresh_company_profile(self):
        if not hasattr(self, "company_list") or not self.company_list.curselection():
            return
        name = self.company_list.get(self.company_list.curselection()[0])
        if name == self.player_company_name:
            roster = self.roster
            upcoming = [f"{e['name']} ({self.event_date_label(e)})" for e in self.sorted_scheduled_events()[:5]]
            recent = self.result_history[:5]
            text = f"{self.player_company_name}\n{self.player_reputation}\nRanked: #{self.company_rank(self.player_company_name)}\nCredibility: {self.company_pop}%\nStability: {self.company_stability}%\nCurrent Finances: ${self.cash:,}\n\nCurrent Roster: {len(roster)} fighters\n"
        else:
            promo = next(p for p in self.promotions if p.name == name)
            roster = promo.roster
            upcoming = [f"{promo.name} {promo.event_counter + i}" for i in range(1, 6)]
            recent = promo.show_history[:5] if promo.show_history else []
            strategy = self.promotion_strategy(promo)
            executive = getattr(promo, "executive", {}) or {}
            prospect_count = sum(1 for fighter in roster if fighter.age <= 26 and fighter.potential - fighter.overall >= 7)
            star_count = sum(1 for fighter in roster if fighter.popularity >= 55 or fighter.overall >= 82)
            pressure = "High" if promo.cash < 150_000 or promo.stability < 35 else "Medium" if promo.cash < 500_000 or promo.stability < 55 else "Low"
            booking_why = f"Recent cards are likely driven by {strategy.get('current_mode', 'balanced booking').lower()}, cash pressure {pressure.lower()}, and a roster mix of {prospect_count} prospects / {star_count} stars."
            text = f"{promo.name}\n{promo.reputation}\nRanked: #{self.company_rank(promo.name)}\nRegion: {promo.region}\nCredibility: {promo.reputation_score}%\nStability: {promo.stability}%\nCurrent Finances: ${promo.cash:,}\n\nEXECUTIVE: {executive.get('name', 'Unknown')} ({executive.get('archetype', 'Operator')})\nBoard Security: {executive.get('job_security', 0)}% | Company Legacy: {getattr(promo, 'legacy_score', 0)}\nBoard mandate: {executive.get('board_mandate', 'None')} - {executive.get('mandate_progress', 0)}% (target {executive.get('mandate_target', 0):,}, deadline M{executive.get('mandate_deadline', 0)})\n\nAI STRATEGY READ\nIdentity: {strategy.get('identity', 'Balanced Growth')}\nDirection: {strategy.get('current_mode', 'Balanced')}\nMedia voice: {strategy.get('media_voice', 'Reliable fights')}\nFinancial pressure: {pressure}\nRoster tilt: {prospect_count} prospects / {star_count} stars\nWhy they book/sign this way: {booking_why}\n\nCurrent Roster: {len(roster)} fighters\n"
        by_weight = []
        for weight in WEIGHTS:
            names = [f.name for f in roster if f.weight == weight][:8]
            if names:
                by_weight.append(f"{weight}: {', '.join(names)}")
        text += "\nCURRENT ROSTER\n" + "\n".join(by_weight[:10])
        text += "\n\nUPCOMING EVENTS CALENDAR\n" + ("\n".join(f"> {item}" for item in upcoming) if upcoming else "> None")
        text += "\n\nRECENT EVENTS\n" + ("\n".join(f"> {item}" for item in recent) if recent else "> None")
        self.company_profile.config(state="normal")
        self.company_profile.delete("1.0", "end")
        self.company_profile.insert("end", text)
        self.company_profile.config(state="disabled")

    def company_rank(self, name):
        rows = [(self.player_company_name, self.company_power_score(self.player_company_name, self.roster, self.company_pop, self.company_stability, self.cash))]
        rows += [(p.name, self.company_power_score(p.name, p.roster, p.reputation_score, p.stability, p.cash)) for p in self.promotions]
        rows = sorted(rows, key=lambda item: -item[1])
        for index, row in enumerate(rows, 1):
            if row[0] == name:
                return index
        return len(rows)

    def selected_company_data(self):
        """Return a normalized read-only view of the company selected in the browser."""
        if not hasattr(self, "company_list") or not self.company_list.curselection():
            return None
        name = self.company_list.get(self.company_list.curselection()[0])
        if name == self.player_company_name:
            return {
                "name": name, "player": True, "roster": self.roster, "region": self.player_region,
                "reputation": self.player_reputation, "score": self.company_pop, "stability": self.company_stability,
                "cash": self.cash, "belts": self.belts, "interim_belts": self.interim_belts,
                "scheduled_events": self.sorted_scheduled_events(), "show_history": self.result_history,
                "finance": self.finance, "staff": self.staff, "strategy": {}, "executive": {},
            }
        promo = next((item for item in self.promotions if item.name == name), None)
        if not promo:
            return None
        return {
            "name": promo.name, "player": False, "roster": promo.roster, "region": promo.region,
            "reputation": promo.reputation, "score": promo.reputation_score, "stability": promo.stability,
            "cash": promo.cash, "belts": promo.belts or {}, "interim_belts": promo.interim_belts or {},
            "scheduled_events": promo.scheduled_events or [], "show_history": promo.show_history or [],
            "finance": promo.finance or {}, "staff": promo.staff or [],
            "strategy": self.promotion_strategy(promo), "executive": getattr(promo, "executive", {}) or {},
        }

    def open_selected_company_section(self, section):
        data = self.selected_company_data()
        if not data:
            messagebox.showinfo("No company", "Select a company first.")
            return
        if not data["player"]:
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
        ttk.Label(header, text=f"#{self.company_rank(data['name'])} | {data['region']} | credibility {data['score']}% | stability {data['stability']}%", style="ScreenTitle.TLabel").pack(side="right", padx=10)
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
        champs = [fighter.name for fighter in data["roster"] if fighter.champion]
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
            boardroom.insert("end", f"EXECUTIVE\n{executive.get('name', 'Unknown')} — {executive.get('archetype', 'Operator')}\n\nAggression: {executive.get('aggression', 50)} | Patience: {executive.get('patience', 50)} | Discipline: {executive.get('discipline', 50)}\nJob security: {executive.get('job_security', 0)}%\n\nACTIVE BOARD MANDATE\n{executive.get('board_mandate', 'None')}\nProgress: {executive.get('mandate_progress', 0)}% | Target: {executive.get('mandate_target', 0):,} | Deadline: Month {executive.get('mandate_deadline', 0)}\n\nMandates influence financial recovery, prospect development, and card frequency.\n\nRECENT BOARD NOTES\n" + ("\n".join(f"- {item.get('year', '')}: {item.get('note', '')}" for item in history[-8:]) or "- No completed or missed mandates recorded yet."))
        else:
            boardroom.insert("end", "The player promotion is governed through the Owner Goals panel in Inbox.")
        boardroom.config(state="disabled")

        roster_tree = ttk.Treeview(tabs["Roster"], columns=("name", "g", "division", "record", "ovr", "pop", "status"), show="headings")
        for column, label, width in (("name", "Fighter", 220), ("g", "G", 42), ("division", "Division", 120), ("record", "W-L-D", 86), ("ovr", "OVR", 60), ("pop", "Pop", 60), ("status", "Status", 130)):
            roster_tree.heading(column, text=label)
            roster_tree.column(column, width=width, anchor="center")
        roster_tree.column("name", anchor="w")
        self.make_tree_sortable(roster_tree)
        for fighter in sorted(data["roster"], key=lambda item: (-self.p4p_value(item), item.name)):
            roster_tree.insert("", "end", iid=fighter.name, values=(self.fighter_display_name(fighter), fighter.gender[0], fighter.weight, fighter.record, fighter.overall, fighter.popularity, fighter.status))
        roster_tree.pack(fill="both", expand=True, padx=8, pady=8)
        roster_tree.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(next((fighter for fighter in data["roster"] if fighter.name == (roster_tree.selection() or [""])[0]), None)) if roster_tree.selection() else None)

        rankings = ttk.Treeview(tabs["Rankings"], columns=("rank", "fighter", "division", "record", "ovr", "score"), show="headings")
        for column, label, width in (("rank", "Rank", 65), ("fighter", "Fighter", 220), ("division", "Division", 130), ("record", "W-L-D", 90), ("ovr", "OVR", 60), ("score", "Ranking", 85)):
            rankings.heading(column, text=label)
            rankings.column(column, width=width, anchor="center")
        rankings.column("fighter", anchor="w")
        self.make_tree_sortable(rankings)
        for rank, fighter in enumerate(sorted(data["roster"], key=self.rank_value, reverse=True), 1):
            rankings.insert("", "end", iid=fighter.name, values=("C" if fighter.champion else rank, self.fighter_display_name(fighter), fighter.weight, fighter.record, fighter.overall, self.rank_value(fighter)))
        rankings.pack(fill="both", expand=True, padx=8, pady=8)
        rankings.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(next((fighter for fighter in data["roster"] if fighter.name == (rankings.selection() or [""])[0]), None)) if rankings.selection() else None)

        belts = tk.Text(tabs["Belts"], wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], padx=12, pady=12)
        belts.pack(fill="both", expand=True, padx=8, pady=8)
        for gender in ("Male", "Female"):
            belts.insert("end", f"{gender.upper()} TITLES\n")
            for weight in WEIGHTS:
                key = self.belt_key(gender, weight)
                champion = next((fighter.name for fighter in data["roster"] if fighter.gender == gender and fighter.weight == weight and fighter.champion), data["belts"].get(key, "Vacant"))
                interim = next((fighter.name for fighter in data["roster"] if fighter.gender == gender and fighter.weight == weight and getattr(fighter, "interim_champion", False)), data["interim_belts"].get(key, ""))
                belts.insert("end", f"{weight:<16} {champion or 'Vacant'}" + (f"  | Interim: {interim}" if interim else "") + "\n")
            belts.insert("end", "\n")
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
        ttk.Button(controls, text="Read Latest Card", command=self.view_selected_company_card).pack(side="left", padx=4, pady=4)
        ttk.Button(controls, text="Watch Latest Card", command=self.watch_selected_company_card).pack(side="left", padx=4, pady=4)
        if not data["player"]:
            ttk.Button(controls, text="Take Control", command=self.take_control_selected_company).pack(side="left", padx=8, pady=4)
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=4, pady=4)
        if focus in tabs:
            notebook.select(tabs[focus])

    def company_power_score(self, name, roster, reputation, stability, cash):
        active = [f for f in roster if not f.retired]
        top = sorted(active, key=lambda f: self.p4p_value(f), reverse=True)[:12]
        top_strength = sum(self.p4p_value(f) for f in top) / max(1, len(top))
        champions = sum(1 for f in active if f.champion)
        star_power = sum(sorted((f.popularity + f.star_quality for f in active), reverse=True)[:8]) / max(1, min(8, len(active)))
        cash_score = min(55, max(-35, cash / 900_000))
        roster_depth = min(35, len(active) / 4)
        return round(reputation * 1.25 + stability * 0.55 + top_strength * 0.42 + star_power * 0.35 + champions * 5 + cash_score + roster_depth)

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
        if not self.company_list.curselection():
            return
        company = self.company_list.get(self.company_list.curselection()[0])
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
        if not self.company_list.curselection():
            return
        company = self.company_list.get(self.company_list.curselection()[0])
        if company == self.player_company_name:
            record = next((item for item in self.result_records if item.get("company") == company), None)
            if not record:
                messagebox.showinfo("No card", "This company has not completed a saved card yet.")
                return
            package = {"event_name": record.get("event", "Last Card"), "log": record.get("log", []), "fight_logs": record.get("fight_logs", [])}
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
        }.get(venue, "USA")

    def refresh_results(self):
        if not hasattr(self, "results_tree"):
            return
        query = self.result_search.get().lower() if hasattr(self, "result_search") else ""
        records = self.result_records or [
            {"date": "", "company": self.player_company_name, "event": item.split(":", 1)[0], "summary": item, "fights": "", "gate": "", "profit": "", "log": [item]}
            for item in self.result_history
        ]
        self.results_tree.delete(*self.results_tree.get_children())
        for index, record in enumerate(records):
            haystack = " ".join(str(record.get(key, "")) for key in ("date", "company", "event", "summary")).lower()
            haystack += " " + self.result_headline(record).lower()
            if query and query not in haystack:
                continue
            self.results_tree.insert("", "end", iid=str(index), values=(record.get("date", ""), record.get("company", ""), record.get("event", ""), self.result_headline(record), record.get("fights", ""), record.get("gate", ""), record.get("profit", "")))
        self.retired_tree.delete(*self.retired_tree.get_children())
        for index, fighter in enumerate(self.retired_fighters):
            self.retired_tree.insert("", "end", iid=str(index), values=(fighter.name, fighter.gender[0], fighter.weight, fighter.record, fighter.age, fighter.motivation))
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
        text = tk.Text(fighters_inner, wrap="none", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        text.pack(fill="both", expand=True)
        everyone = [fighter for _company, fighter in self.all_database_fighters_with_companies()]
        unique = {fighter.name: fighter for fighter in everyone}
        rows = sorted(unique.values(), key=lambda fighter: self.compute_legacy_score(fighter), reverse=True)[:60]
        text.insert("end", "Fighter                         Legacy   Record    Titles/Def    Awards\n")
        text.insert("end", "-" * 72 + "\n")
        for fighter in rows:
            score = self.compute_legacy_score(fighter)
            text.insert("end", f"{fighter.name[:30]:30} {score:>6}   {fighter.record:9} {fighter.title_wins:>2}/{fighter.title_defenses:<3} {fighter.award_count:>3}\n")
        text.config(state="disabled")
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

    def result_card_text(self, record):
        bout_lines = self.result_bout_lines(record)
        header = record.get("summary", "")
        parts = [header, "", "CARD RESULTS", "-" * 60]
        parts.extend(bout_lines if bout_lines else ["(No per-fight breakdown stored for this event.)"])
        return "\n".join(parts)

    def open_selected_result(self):
        selected = self.results_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        records = self.result_records or [
            {"summary": item, "log": [item]}
            for item in self.result_history
        ]
        if index >= len(records):
            return
        record = records[index]
        self.open_result_card_window(record)
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        card = self.result_card_text(record)
        full_log = "\n".join(record.get("log", [record.get("summary", "")]))
        self.results_text.insert("end", card + "\n\n\n" + "=" * 60 + "\nFULL PLAY-BY-PLAY\n" + "=" * 60 + "\n" + full_log)
        self.results_text.config(state="disabled")

    def result_fighter(self, name):
        return next((fighter for _company, fighter in self.all_database_fighters_with_companies()
                     if fighter.name == name), None)

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
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="right", padx=5, pady=5)
        selected_log = {"value": None}

        def open_profile(side):
            fight_log = selected_log["value"] or {}
            fighter = self.result_fighter(fight_log.get(side, ""))
            if fighter:
                self.open_fighter_profile_window(fighter)

        def negotiate_fighter(side):
            fight_log = selected_log["value"] or {}
            fighter = self.result_fighter(fight_log.get(side, ""))
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
            a = self.result_fighter(fight_log.get("a", ""))
            b = self.result_fighter(fight_log.get("b", ""))
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
            detail.insert("end", record.get("summary", "No bout logs recorded."))
            detail.config(state="disabled")

    def unretire_selected_fighter(self):
        selected = self.retired_tree.selection()
        if not selected:
            return
        fighter = self.retired_fighters.pop(int(selected[0]))
        fighter.retired = False
        fighter.retirement_reason = ""
        fighter.retirement_pending = False
        fighter.contract_months = max(10, random.randint(10, 24))
        fighter.motivation = max(55, fighter.motivation + random.randint(12, 28))
        fighter.morale = min(100, fighter.morale + 12)
        fighter.fatigue = 0
        fighter.injured = 0
        fighter.purse = round(fighter.purse * 1.35)
        self.roster.append(fighter)
        self.inbox.append({"subject": "Comeback Deal", "body": f"{fighter.name} accepted a comeback deal with at least 5 fights expected.", "type": "Contracts", "resolved": False})
        self.news.insert(0, f"{fighter.name} came out of retirement to join {self.player_company_name}.")
        self.refresh_all()

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
                active = "Yes" if weight in self.weight_classes else "No"
                self.company_belts_tree.insert("", "end", iid=key, values=(gender, weight, champion or "Vacant", interim or "-", active))
        self.refresh_belt_history_view()
        self.rules_text.config(state="normal")
        self.rules_text.delete("1.0", "end")
        broadcasters = "\n".join(f"- {b['name']} ({b['type']}): reach {b['reach']}, fee ${b['fee']:,}" for b in self.broadcasters)
        mixed = "Allowed" if self.rules.get("allow_mixed_gender", False) else "Not allowed"
        self.ensure_rule_defaults()
        self.rules_text.insert("end", f"Rounds: {self.rules['rounds']} regular / {self.rules['title_rounds']} title\nRound Length: {self.rules['round_length']} minutes\nDrug Testing: {self.rules['drug_testing']}\nJudging Randomness: {self.rules['judging_randomness']}\nMixed-Gender Fights: {mixed}\nActive Fighter Target: {self.rules['active_fighter_target']}\n\nBroadcasters:\n{broadcasters}")
        self.rules_text.config(state="disabled")

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

    def ensure_rule_defaults(self):
        self.rules.setdefault("rounds", 3)
        self.rules.setdefault("title_rounds", 5)
        self.rules.setdefault("round_length", 5)
        self.rules.setdefault("drug_testing", "Standard")
        self.rules.setdefault("judging_randomness", 2)
        self.rules.setdefault("allow_mixed_gender", False)
        self.rules.setdefault("active_fighter_target", 1200)
        # Migrate worlds created before the population floor was corrected.
        if self.rules["active_fighter_target"] < 800:
            self.rules["active_fighter_target"] = 1200

    def toggle_weight_class(self):
        selected = self.company_belts_tree.selection()
        if not selected:
            return
        weight = selected[0].replace("Male ", "").replace("Female ", "")
        if weight in self.weight_classes:
            self.weight_classes.remove(weight)
        else:
            self.weight_classes.append(weight)
        self.news.insert(0, f"{self.player_company_name} changed the {weight} division status.")
        self.refresh_all()

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
        candidate = options[min(len(self.broadcasters), len(options) - 1)]
        self.broadcasters.append(dict(candidate))
        self.inbox.append({"subject": "Broadcast Deal Signed", "body": f"{candidate['name']} has been added.", "type": "Business", "resolved": False})
        self.refresh_all()

    def refresh_inbox(self):
        if not hasattr(self, "inbox_tree"):
            return
        selected = self.inbox_tree.selection()
        self.inbox_tree.delete(*self.inbox_tree.get_children())
        status_filter = self.inbox_filter.get() if hasattr(self, "inbox_filter") else "Open"
        type_filter = self.inbox_type_filter.get() if hasattr(self, "inbox_type_filter") else "All"
        items = []
        for index, item in enumerate(self.inbox):
            resolved = item.get("resolved", False)
            seen = item.get("seen", False)
            if item.get("type", "Mail") in getattr(self, "inbox_hidden_types", set()):
                continue
            if status_filter == "Open" and resolved:
                continue
            if status_filter == "Read" and (resolved or not seen):
                continue
            if type_filter != "All" and item.get("type", "Mail") != type_filter:
                continue
            items.append((index, item))
        for index, item in items[:160]:
            urgent = any(token in item.get("subject", "").upper() for token in ("URGENT", "EXPIRING", "BROKEN PROMISE", "RETIREMENT"))
            tag = "urgent" if urgent else ("" if item.get("seen", False) else "unread")
            state = "!" if urgent else ("" if item.get("seen", False) else "*")
            self.inbox_tree.insert("", "end", iid=str(index), tags=(tag,) if tag else (), values=(state, item.get("type", "Mail"), item.get("subject", "Untitled")))
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
            self.goals_tree.insert("", "end", iid=str(index), tags=(tag,) if tag else (), values=(goal["goal"], progress, f"Month {goal['deadline']}", goal["status"]))

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
            self.inbox_detail.insert("end", f"{item.get('type', 'Mail').upper()}\n{item.get('subject', 'Untitled')}\n\n{item.get('body', '')}{context}\n\nStatus: {'Resolved' if item.get('resolved') else 'Open'}")
        self.inbox_detail.config(state="disabled")

    def mark_inbox_read(self):
        item = self.selected_inbox_item()
        if item:
            item["seen"] = True
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
            self.select_tab("market")
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
            messagebox.showinfo("Medical Decision", "Select a serious-injury medical decision from the inbox.")
            return
        fighter = self.inbox_related_fighter(item)
        if not fighter or not getattr(fighter, "serious_injury_pending", False):
            item["resolved"] = True
            self.refresh_all()
            return
        choice = messagebox.askyesnocancel("Medical Decision", f"{fighter.name}: {fighter.serious_injury}\n\nYes — surgical repair: longer recovery, lower future risk.\nNo — accelerated rehabilitation: sooner return, higher recurrence risk.\nCancel — retire the fighter.")
        if choice is None:
            if not messagebox.askyesno("Retirement Confirmation", f"Retire {fighter.name} because of this injury?"):
                return
            decision = "retire"
        else:
            decision = "surgery" if choice is True else "rehab"
        self.resolve_serious_injury(fighter, decision)
        item["resolved"] = True
        item["seen"] = True
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
        self.staff_text.insert("end", "Scouting Assignments:\n")
        if self.scouting:
            for assignment in self.scouting[-12:]:
                self.staff_text.insert("end", f"- {assignment}\n")
        else:
            self.staff_text.insert("end", "- No active scouting assignments.\n")
        self.staff_text.config(state="disabled")

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
        scout = max([s for s in self.staff if s["role"] == "Scout"], key=lambda s: s["skill"], default=None)
        region = random.choice(REGIONS)
        scout_quality = scout["skill"] if scout else 45
        found = self.create_generated_fighter(4, min(55, 18 + scout_quality // 2), max(36, scout_quality - 28), min(91, scout_quality + 18))
        found.region = region
        if scout and scout.get("specialty") == "Prospect eye":
            found.potential = min(98, max(found.potential, found.overall + random.randint(10, 22)))
        elif scout and scout.get("specialty") == "Women’s divisions":
            found.gender = "Female" if random.random() < 0.72 else found.gender
        self.free_agents.append(found)
        assignment = f"{scout['name'] if scout else 'Independent scout'} searched {region} and found {found.name} ({found.gender} {found.weight}, OVR {found.overall}, potential {found.potential})."
        self.scouting.append(assignment)
        self.inbox.append({"subject": "Scouting Report", "body": assignment, "type": "Scouting", "resolved": False})
        self.refresh_all()

    def run_drug_tests(self):
        tested = random.sample(self.roster, k=min(6, len(self.roster)))
        positives = []
        accuracy = {"None": 0, "Standard": 0.04, "Strict": 0.08, "Olympic": 0.12}[self.rules.get("drug_testing", "Standard")]
        cost = len(tested) * self.finance["drug_test_cost"]
        self.cash -= cost
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
        selected = self.finance_tree.selection()
        self.finance_tree.delete(*self.finance_tree.get_children())
        history = self.finance["weekly_history"][-48:]
        for index, row in enumerate(history):
            net = row.get("net", row.get("ending", 0) - row.get("opening", 0))
            tag = "positive" if net >= 0 else "negative"
            self.finance_tree.insert("", "end", iid=str(index), tags=(tag,), values=(
                f"M{row['month']} W{row['week']}", f"${row['opening']:,.0f}", f"${row['revenue']:,.0f}",
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
            self.finance_detail.insert("end", f"MONTH {row['month']} / WEEK {row['week']}\n\nOpening balance: ${row['opening']:,.0f}\nRevenue: ${row['revenue']:,.0f}\nCosts: ${row['costs']:,.0f}\nNet movement: ${row.get('net', row['ending'] - row['opening']):,.0f}\nClosing balance: ${row['ending']:,.0f}\n\nTRANSACTIONS\n")
            transactions = row.get("transactions", [])
            if transactions:
                for item in transactions:
                    self.finance_detail.insert("end", f"- {item['label']}: +${item['revenue']:,.0f} / -${item['costs']:,.0f}\n")
            else:
                self.finance_detail.insert("end", "- No player cash transactions recorded this week.\n")
        else:
            self.finance_detail.insert("end", "Advance time or run an event to begin building the 12-month cashflow history.")
        self.finance_detail.config(state="disabled")

    def ensure_finance_defaults(self):
        self.finance.setdefault("sponsor_deals", [])
        self.finance.setdefault("media_rights", {"name": "No rights package", "months": 0, "fee": 0, "reach": 0, "events_remaining": 0})
        self.finance["media_rights"].setdefault("events_remaining", 0)
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

    def pitch_sponsors(self):
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
        self.company_stability = min(100, self.company_stability + 1)
        self.finance["ledger"].insert(0, f"Month {self.month}: Signed sponsor {deal['name']} for ${deal['fee']:,}/event over {deal['months']} months.")
        self.inbox.append({"subject": "Sponsor Signed", "body": f"{deal['name']} signed for ${deal['fee']:,}/event.", "type": "Business", "resolved": False})
        self.refresh_all()

    def negotiate_media_rights(self):
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
        company_division_ranks, world_division_ranks = self.division_rank_maps()
        company_p4p_ranks, world_p4p_ranks = self.p4p_rank_maps()
        if mode == "Pound-for-Pound":
            ranked = sorted(rows, key=lambda row: self.p4p_value(row[1]), reverse=True)[:50]
            for _rank, (company, fighter) in enumerate(ranked, 1):
                label = self.fighter_display_name(fighter)
                self.rankings_tree.insert("", "end", values=(company_p4p_ranks.get((company, fighter.name), "-"), world_p4p_ranks.get(fighter.name, "-"), self.ranking_movement_label(fighter), label, fighter.gender[0], company, fighter.weight, fighter.record, fighter.overall, self.ranking_form_label(fighter), self.title_path_label(fighter), self.p4p_value(fighter), fighter.last_fight, fighter.status))
            return
        division = sorted(rows, key=lambda row: self.rank_value(row[1]), reverse=True)
        for company, fighter in division[:75]:
            label = self.fighter_display_name(fighter)
            self.rankings_tree.insert("", "end", values=(company_division_ranks.get((company, fighter.name), "-"), world_division_ranks.get(fighter.name, "-"), self.ranking_movement_label(fighter), label, fighter.gender[0], company, fighter.weight, fighter.record, fighter.overall, self.ranking_form_label(fighter), self.title_path_label(fighter), self.rank_value(fighter), fighter.last_fight, fighter.status))

    def ranking_movement_label(self, fighter):
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
            return "Defending champion"
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
            fighter = self.find_fighter_anywhere(self.clean_display_fighter_name(values[3])) if len(values) > 3 else None
            if fighter:
                self.ranking_detail.insert("end", f"{fighter.name}: rank is driven by ELO, record quality, overall ability, activity and current form. {self.title_path_label(fighter)}. Current rank #{fighter.ranking_position or '-'}; previous #{fighter.previous_ranking_position or '-'}; rationale: {fighter.ranking_reason or 'Merit ranking'}. Double-click to open profile.")
            else:
                self.ranking_detail.insert("end", "Company rankings combine roster strength, reputation, stability, and financial power.")
        else:
            self.ranking_detail.insert("end", "Select a contender to see the ranking rationale and title path.")
        self.ranking_detail.config(state="disabled")

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

    def division_rank_maps(self):
        company_ranks = {}
        world_ranks = {}
        rows = self.unfiltered_ranked_fighter_rows()
        company_groups = {}
        world_groups = {}
        for company, fighter in rows:
            key = (fighter.gender, fighter.weight)
            company_groups.setdefault((company, *key), []).append(fighter)
            world_groups.setdefault(key, []).append(fighter)
        for (company, _gender, _weight), fighters in company_groups.items():
            ordered = sorted(fighters, key=self.rank_value, reverse=True)
            for index, fighter in enumerate(ordered, 1):
                company_ranks[(company, fighter.name)] = self.rank_label_for_position(fighter, index)
        for fighters in world_groups.values():
            ordered = sorted(fighters, key=self.rank_value, reverse=True)
            for index, fighter in enumerate(ordered, 1):
                world_ranks[fighter.name] = self.rank_label_for_position(fighter, index)
        return company_ranks, world_ranks

    def p4p_rank_maps(self):
        company_ranks = {}
        world_ranks = {}
        rows = self.unfiltered_ranked_fighter_rows()
        company_groups = {}
        for company, fighter in rows:
            company_groups.setdefault(company, []).append(fighter)
        for company, fighters in company_groups.items():
            for index, fighter in enumerate(sorted(fighters, key=self.p4p_value, reverse=True), 1):
                company_ranks[(company, fighter.name)] = f"#{index}"
        for index, (_company, fighter) in enumerate(sorted(rows, key=lambda row: self.p4p_value(row[1]), reverse=True), 1):
            world_ranks[fighter.name] = f"#{index}"
        return company_ranks, world_ranks

    def get_fighter(self, name):
        return next(f for f in self.roster if f.name == name)

    def add_matchup(self):
        selection = self.available_tree.selection()
        if len(selection) != 2:
            messagebox.showinfo("Matchup needed", "Select exactly two available fighters.")
            return
        a, b = [self.get_fighter(name) for name in selection]
        if self.fighter_busy_message([a.name, b.name]):
            self.refresh_available()
            return
        if a.weight != b.weight:
            messagebox.showwarning("Weight mismatch", "Fighters must be in the same weight class.")
            return
        if a.gender != b.gender and not self.rules.get("allow_mixed_gender", False):
            messagebox.showwarning("Rules blocked", "Mixed-gender fights are not allowed under this promotion's current rules.")
            return
        if a.injured or b.injured:
            messagebox.showwarning("Unavailable", "Injured fighters cannot be booked.")
            return
        target_month = self.event_month.get() if hasattr(self, "event_month") else self.month
        target_week = self.event_week.get() if hasattr(self, "event_week") else self.week
        unavailable = [fighter for fighter in (a, b) if not self.fighter_available_for_date(fighter, target_month, target_week)]
        if unavailable:
            messagebox.showwarning("Recovery window", " | ".join(f"{fighter.name}: {self.fighter_return_label(fighter)}" for fighter in unavailable))
            return
        if a.fatigue >= 65 or b.fatigue >= 65:
            messagebox.showwarning("Too fatigued", "One of these fighters is carrying too much fatigue to be safely booked.")
            return
        interim = self.title_fight.get() and not (a.champion or b.champion)
        make_main = self.main_event.get() or len(self.booked) == 0
        if make_main:
            for fight in self.booked:
                fight["main"] = False
        fight = {"fighters": [a.name, b.name], "title": self.title_fight.get(), "interim": interim, "main": make_main, "tier": self.card_tier.get()}
        if make_main:
            self.booked.insert(0, fight)
        else:
            self.booked.append(fight)
        self.normalize_card_order()
        self.title_fight.set(False)
        self.main_event.set(False)
        self.refresh_available()
        self.refresh_card()

    def add_tba_matchup(self):
        selection = self.available_tree.selection()
        if len(selection) != 1:
            messagebox.showinfo("TBA matchup", "Select exactly one fighter to book against a TBA opponent.")
            return
        fighter = self.get_fighter(selection[0])
        if self.fighter_busy_message([fighter.name]):
            self.refresh_available()
            return
        if fighter.injured or fighter.fatigue >= 65:
            messagebox.showwarning("Unavailable", "That fighter is not available for a TBA booking.")
            return
        interim = self.title_fight.get() and not fighter.champion
        make_main = self.main_event.get() or len(self.booked) == 0
        if make_main:
            for fight in self.booked:
                fight["main"] = False
        fight = {"fighters": [fighter.name, "TBA"], "title": self.title_fight.get(), "interim": interim, "main": make_main, "tier": self.card_tier.get(), "tba_weight": fighter.weight, "tba_gender": fighter.gender}
        if make_main:
            self.booked.insert(0, fight)
        else:
            self.booked.append(fight)
        self.normalize_card_order()
        self.title_fight.set(False)
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
        if fight.get("title") and not (known.champion or replacement.champion):
            fight["interim"] = True
        self.news.insert(0, f"{replacement.name} has been confirmed as the TBA opponent for {known.name}.")
        self.refresh_available()
        self.refresh_market()
        self.refresh_card()

    def toggle_card_title(self):
        selected = self.card_tree.selection()
        if not selected:
            return
        fight = self.booked[int(selected[0])]
        names = [name for name in fight.get("fighters", []) if name != "TBA"]
        fighters = [self.get_fighter(name) for name in names]
        fight["title"] = not fight.get("title", False)
        fight["interim"] = bool(fight["title"] and not any(f.champion for f in fighters))
        if fight["title"] and fight["interim"]:
            self.news.insert(0, f"{' vs '.join(names)} has been marked as an interim title fight.")
        self.refresh_card()

    def assistant_pick_matchup(self):
        used = self.scheduled_fighter_names(include_booked=True)
        ready = [f for f in self.roster if f.name not in used and not f.injured and f.fatigue < 55]
        candidates = []
        for i, a in enumerate(ready):
            for b in ready[i + 1:]:
                if a.weight != b.weight:
                    continue
                score, reason = self.matchmaking_score(a, b)
                candidates.append((score, reason, a, b))
        if not candidates:
            messagebox.showinfo("Assistant", "No suitable matchups are available.")
            return
        score, reason, a, b = max(candidates, key=lambda item: item[0])
        if messagebox.askyesno("Assistant Recommendation", f"{a.name} vs {b.name}\n\n{reason}\n\nBook this fight?"):
            if self.main_event.get():
                for fight in self.booked:
                    fight["main"] = False
            should_title = self.title_fight.get() or a.champion or b.champion
            should_main = self.main_event.get() or len(self.booked) == 0 or should_title
            fight = {"fighters": [a.name, b.name], "title": should_title, "main": should_main, "tier": "Main Card" if should_main else self.card_tier.get()}
            if should_main:
                for existing in self.booked:
                    existing["main"] = False
                self.booked.insert(0, fight)
            else:
                self.booked.append(fight)
            self.normalize_card_order()
            self.title_fight.set(False)
            self.main_event.set(False)
            self.refresh_available()
            self.refresh_card()

    def normalize_card_order(self):
        if not self.booked:
            return
        for index, fight in enumerate(self.booked):
            fight["main"] = index == 0
            fight.setdefault("tier", "Main Card" if index == 0 else "Prelims")

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
        hype = self.fight_hype(a, b, {"title": False, "main": False})
        prospect_penalty = 0
        reason_bits = []
        if (a.record_l == 0 and a.age < 26 and b.overall - a.overall > 7) or (b.record_l == 0 and b.age < 26 and a.overall - b.overall > 7):
            prospect_penalty = 35
            reason_bits.append("protects prospects by avoiding a severe skill jump")
        if a.rival == b.name or b.rival == a.name:
            hype += 24
            reason_bits.append("existing rivalry")
        if a.champion or b.champion:
            contender = b if a.champion else a
            champ = a if a.champion else b
            hype += max(0, self.rank_value(contender) - self.rank_value(champ) // 2) / 12
            reason_bits.append("credible title-contender logic")
        style_gap = abs(a.overall - b.overall)
        score = hype - style_gap * 0.9 - prospect_penalty + abs(a.momentum - b.momentum) * 2
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

    def refresh_database_editor(self):
        if not hasattr(self, "editor_tree"):
            return
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
            messagebox.showwarning("Database Editor", "A fighter needs a name.")
            return
        target = self.editor_target_roster(owner)
        if target is None:
            messagebox.showwarning("Database Editor", "Choose a valid employer.")
            return
        fighter = self.editor_selected_fighter
        duplicates = [candidate for _owner, candidate in self.database_editor_rows() if candidate.name == name and candidate is not fighter]
        if duplicates:
            messagebox.showwarning("Database Editor", f"{name} already exists in the active database.")
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
        self.ensure_all_company_champions()
        self.news.insert(0, f"Database editor {'created' if is_new else 'updated'} {fighter.name} ({owner}).")
        self.refresh_all()
        self.load_selected_editor_fighter()

    def open_editor_selected_profile(self):
        fighter = getattr(self, "editor_selected_fighter", None)
        if fighter:
            self.open_fighter_profile_window(fighter)
        else:
            messagebox.showinfo("Database Editor", "Select a fighter first.")

    def retire_database_editor_fighter(self):
        fighter = getattr(self, "editor_selected_fighter", None)
        if not fighter:
            messagebox.showinfo("Database Editor", "Select a fighter first.")
            return
        if not messagebox.askyesno("Retire Fighter", f"Retire {fighter.name} from the active database?"):
            return
        self.remove_fighter_from_active_database(fighter)
        fighter.retired = True
        fighter.retirement_reason = "Database editor"
        fighter.champion = False
        fighter.interim_champion = False
        if fighter not in self.retired_fighters:
            self.retired_fighters.insert(0, fighter)
        self.editor_selected_fighter = None
        self.ensure_all_company_champions()
        self.news.insert(0, f"Database editor retired {fighter.name}.")
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
