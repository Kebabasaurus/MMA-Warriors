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


class EventMixin:
    def schedule_event(self):
        if len(self.booked) < 1:
            messagebox.showinfo("No fights", "Book at least one fight before scheduling a show.")
            return
        names = [name for fight in self.booked for name in fight.get("fighters", []) if name != "TBA"]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            messagebox.showwarning("Double booking", f"{', '.join(duplicates)} is booked in more than one fight on this card. A fighter can only appear once per event.")
            return
        if self.fighter_busy_message(names):
            self.refresh_available()
            return
        month = max(self.month, int(self.event_month.get()))
        week = max(1, min(4, int(self.event_week.get())))
        if month == self.month and week < self.week:
            week = self.week
        unavailable = []
        for name in names:
            fighter = self.get_fighter(name)
            if not self.fighter_available_for_date(fighter, month, week):
                unavailable.append(f"{fighter.name} ({self.fighter_return_label(fighter)})")
        if unavailable:
            messagebox.showwarning("Recovery window", "These fighters cannot be scheduled that soon:\n\n" + "\n".join(unavailable))
            return
        self.normalize_card_order()
        event_number = self.next_player_event_number()
        current_name = self.event_name.get().strip()
        event_name = self.default_event_name(event_number) if self.is_auto_event_name(current_name) else current_name
        event = {
            "name": event_name,
            "venue": self.venue.get(),
            "region": self.event_region.get(),
            "city": self.event_city.get(),
            "month": month,
            "week": week,
            "broadcaster": self.event_broadcaster.get(),
            "fights": [dict(fight) for fight in self.booked],
        }
        self.scheduled_events.append(event)
        self.assign_event_camps(event)
        self.news.insert(0, f"{event['name']} has been scheduled for {self.event_date_label(event)} at {event['venue']}.")
        self.booked.clear()
        self.event_name.set(self.default_event_name())
        self.event_month.set(month if week < 4 else month + 1)
        self.event_week.set(week + 1 if week < 4 else 1)
        self.event_broadcaster.set(self.broadcasters[0]["name"] if self.broadcasters else "No Coverage")
        self.refresh_all()

    def repair_booking_conflicts(self):
        """Guarantee no fighter is booked on two un-run events at once.

        Scans scheduled events in date order; the first booking wins, and any
        later slot for the same fighter is turned into a TBA so the card survives.
        Protects legacy saves and any edge case that slipped past the UI guards.
        """
        seen = set()
        conflicts = []
        for event in sorted(self.scheduled_events, key=lambda e: (e.get("month", 1), e.get("week", 1))):
            event_names = set()
            for fight in event.get("fights", []):
                fighters = fight.get("fighters", [])
                for index, name in enumerate(fighters):
                    if name == "TBA":
                        continue
                    if name in seen or name in event_names:
                        fighters[index] = "TBA"
                        fight["tba_weight"] = fight.get("tba_weight", self._safe_weight(name))
                        fight["tba_gender"] = fight.get("tba_gender", self._safe_gender(name))
                        conflicts.append(name)
                    else:
                        event_names.add(name)
            seen.update(event_names)
        for name in sorted(set(conflicts)):
            self.news.insert(0, f"Booking conflict resolved: {name} was double-booked and freed from the later event.")
        return conflicts

    def _safe_weight(self, name):
        fighter = self.get_fighter(name)
        return fighter.weight if fighter else "Lightweight"

    def _safe_gender(self, name):
        fighter = self.get_fighter(name)
        return fighter.gender if fighter else "Male"

    def assign_event_camps(self, event):
        weeks_out = max(1, (event["month"] - self.month) * 4 + (event.get("week", 1) - self.week))
        for fight in event["fights"]:
            for name in fight.get("fighters", []):
                if name == "TBA":
                    continue
                fighter = self.get_fighter(name)
                quality = self.gym_quality(fighter.camp)
                gym = self.gym_by_name(fighter.camp)
                professionalism = fighter.professionalism / 100
                motivation = fighter.motivation / 100
                specialty = self.gym_specialty_bonus(fighter, gym)
                focus_bonus = self.camp_focus_bonus(fighter, gym)
                intensity = getattr(fighter, "camp_intensity", "Standard")
                intensity_bonus = {"Light": -1, "Standard": 0, "Hard": 4}.get(intensity, 0)
                crowded = max(0, (gym.member_count - gym.capacity) / max(1, gym.capacity)) if gym and gym.capacity < 500 else 0
                base_boost = round(weeks_out * (quality + specialty + focus_bonus + intensity_bonus) / 112 * (0.55 + professionalism * 0.3 + motivation * 0.25) / (2.8 + crowded))
                camp_boost = min(12, max(0, base_boost + self.camp_form_variance(fighter, gym)))
                fighter.camp_quality = quality
                fighter.camp_weeks = weeks_out
                fighter.camp_boost = camp_boost
                fighter.morale = min(100, fighter.morale + max(0, camp_boost // 2))
                self.apply_gym_camp_micro_improvement(fighter, gym, weeks_out)
                self.apply_camp_focus_improvement(fighter, gym, weeks_out)
                self.evolve_trait_from_camp(fighter, quality, weeks_out)
                if intensity == "Hard" and random.random() < max(0.015, fighter.injury_proneness / 1600):
                    fighter.injured = max(fighter.injured, 1)
                    fighter.camp_boost = max(0, fighter.camp_boost - 3)
                    self.news.insert(0, f"Camp setback: {fighter.name} picked up a minor injury during a hard camp.")

    def camp_form_variance(self, fighter, gym=None):
        """Return a small, one-camp readiness swing without eclipsing preparation.

        Equal-length camps should vary, but the difference stays within two boost
        points. Professionalism, motivation, and gym morale only bias the roll;
        they never guarantee a great or poor camp.
        """
        gym = gym or self.gym_by_name(fighter.camp)
        reliability = (fighter.professionalism + fighter.motivation + (gym.morale if gym else 50)) / 3
        positive_bias = max(0, reliability - 55) / 10
        negative_bias = max(0, 55 - reliability) / 10
        return random.choices(
            (-2, -1, 0, 1, 2),
            weights=(6 + negative_bias, 21 + negative_bias / 2, 44, 21 + positive_bias / 2, 6 + positive_bias),
            k=1,
        )[0]

    def camp_focus_bonus(self, fighter, gym=None):
        focus = getattr(fighter, "camp_focus", "Balanced")
        specialty = {
            "Striking": "Boxing", "Wrestling": "Wrestling", "Grappling": "BJJ",
            "Conditioning": "Conditioning", "Game Plan": "Gameplanning", "Weight Management": "Conditioning",
        }.get(focus)
        if not specialty:
            return 0
        return 7 if gym and specialty in gym.specialties else 2

    def apply_camp_focus_improvement(self, fighter, gym, weeks_out):
        if weeks_out < 3 or random.random() > min(0.34, weeks_out * 0.032 + fighter.professionalism / 650):
            return
        self.ensure_detailed_skills(fighter)
        key_map = {
            "Striking": ("punch_technique", "hand_speed", "high_kick_technique", "low_kick_technique"),
            "Wrestling": ("takedowns", "takedown_setup", "chain_wrestling", "sprawl"),
            "Grappling": ("submission_attack", "guard_work", "transitions", "scrambles"),
            "Conditioning": ("conditioning", "resilience", "stun_recovery"),
            "Game Plan": ("composure", "adaptability", "confidence", "consistency"),
            "Weight Management": ("weight_cutting", "conditioning", "discipline"),
        }
        keys = key_map.get(getattr(fighter, "camp_focus", "Balanced"))
        if not keys:
            return
        key = random.choice(keys)
        fighter.detailed_skills[key] = min(99, fighter.detailed_skills.get(key, 50) + 1)
        self.sync_broad_skills_from_details(fighter)
        self.news.insert(0, f"Camp report: {fighter.name}'s {fighter.camp_focus.lower()} work improved {key.replace('_', ' ')}.")

    def selected_due_event(self):
        shows = self.sorted_scheduled_events()
        selected = self.upcoming_tree.selection()
        if selected:
            event = shows[int(selected[0])]
        else:
            due = [show for show in shows if self.is_event_due(show)]
            event = due[0] if due else None
        if not event:
            messagebox.showinfo("No due event", "There is no scheduled event due this week.")
            return None
        if not self.is_event_due(event):
            messagebox.showinfo("Not yet", f"{event['name']} is scheduled for {self.event_date_label(event)}.")
            return None
        return event

    def prompt_due_event(self):
        if self.root.state() == "withdrawn":
            return False
        due = [event for event in self.sorted_scheduled_events() if self.is_event_due(event)]
        if not due:
            return False
        event = due[0]
        choice = messagebox.askyesnocancel("Fight Day", f"{event['name']} is due in {self.event_date_label(event)}.\n\nYes = Watch live\nNo = Sim instantly\nCancel = stay on this week")
        if choice is True:
            package = self.prepare_event_result(event)
            self.open_live_fight_window(event, package)
            return True
        if choice is False:
            package = self.prepare_event_result(event)
            self.finish_event(event, package)
            self.select_tab("log")
            return True
        return True

    def evolve_trait_from_camp(self, fighter, quality, weeks_out):
        if weeks_out < 2:
            return
        gain_chance = (quality + fighter.professionalism + fighter.motivation) / 900
        lose_chance = max(0.01, (100 - fighter.professionalism + fighter.injury_proneness) / 1800)
        if random.random() < gain_chance:
            old = fighter.trait
            fighter.trait = random.choice([
                "Gym Rat", "Clutch", "Big Finisher", "Marketable", "Fan Favourite", "Cardio Machine",
                "Comeback Artist", "Submission Ace", "Knockout Artist", "Counter Specialist",
                "Coach Favourite", "Gym Leader", "Title Mentality", "Late Bloomer", "Technical Learner",
                "Warrior Spirit", "Fast Healer", "Adaptable", "Momentum Fighter", "Body Hunter",
                "Leg Kicker", "Cage Specialist", "Elbow Specialist", "Scramble Artist", "Fight Finisher",
            ])
            if fighter.trait != old:
                self.news.insert(0, f"Camp report: {fighter.name} developed the {fighter.trait} trait during camp.")
        elif random.random() < lose_chance and fighter.trait not in ("Fan Favourite", "Marketable"):
            old = fighter.trait
            fighter.trait = random.choice(["Slow Starter", "Erratic", "Fragile", "Bad Weight Cut", "Front Runner", "Slow Healer", "Gym Rat"])
            if fighter.trait != old:
                self.news.insert(0, f"Camp report: {fighter.name}'s traits shifted from {old} to {fighter.trait}.")

    def apply_gym_camp_micro_improvement(self, fighter, gym, weeks_out):
        if not gym or weeks_out < 2:
            return
        self.ensure_detailed_skills(fighter)
        chance = min(0.28, (gym.quality + gym.facilities + self.gym_specialty_bonus(fighter, gym)) / 900 * weeks_out)
        if random.random() > chance:
            return
        specialty = random.choice(gym.specialties or ["Gameplanning"])
        keys = [key for key in GYM_SPECIALTY_SKILLS.get(specialty, ()) if key in fighter.detailed_skills]
        if not keys:
            return
        key = random.choice(keys)
        amount = 2 if gym.quality >= 84 and fighter.age <= fighter.prime_end else 1
        fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills.get(key, 50) + amount))
        self.sync_broad_skills_from_details(fighter)
        if random.random() < 0.35:
            self.news.insert(0, f"Camp report: {fighter.name} sharpened {key.replace('_', ' ')} at {gym.name}.")

    def skip_due_event(self):
        event = self.selected_due_event()
        if not event:
            return
        package = self.prepare_event_result(event)
        self.finish_event(event, package)
        self.select_tab("log")

    def watch_due_event(self):
        event = self.selected_due_event()
        if not event:
            return
        package = self.prepare_event_result(event)
        self.open_live_fight_window(event, package)

    def open_event_replay_window(self, title, package):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("900x620")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=title.upper(), style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        fight_list = tk.Listbox(body, width=36, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        fight_list.pack(side="left", fill="y", padx=(0, 8))
        text = tk.Text(body, wrap="word", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        text.pack(side="left", fill="both", expand=True)
        logs = package.get("fight_logs", [])
        for index, fight_log in enumerate(logs, 1):
            heading = fight_log.get("heading", fight_log.get("fight", f"Bout {index}"))
            fight_list.insert("end", f"{index}. {heading[:40]}")
        def show_selected(_event=None):
            selected = fight_list.curselection()
            text.delete("1.0", "end")
            if selected and logs:
                text.insert("end", "\n".join(logs[selected[0]].get("lines", [])))
            else:
                text.insert("end", "\n".join(package.get("log", [])))
        fight_list.bind("<<ListboxSelect>>", show_selected)
        show_selected()

    def open_live_fight_window(self, event, package, apply_results=True, on_complete=None):
        window = tk.Toplevel(self.root)
        window.title(f"Live Fight - {event['name']}")
        self.root.update_idletasks()
        width, height = 1120, 740
        x = max(0, self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2)
        y = max(0, self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(1000, 640)
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        title_label = ttk.Label(header, text=f"LIVE FIGHT: {event['name']}", style="ScreenTitle.TLabel")
        title_label.pack(side="left", padx=10, pady=5)

        # Tale-of-the-tape scoreboard that updates as each bout begins.
        tote = tk.Frame(window, bg=self.colors["chrome"])
        tote.pack(fill="x", padx=8, pady=(6, 0))
        label_chip = tk.Label(tote, text="", font=("Tahoma", 9, "bold"), bg=self.colors["chrome"], fg=self.colors["gold"])
        label_chip.pack()
        matchup_row = tk.Frame(tote, bg=self.colors["chrome"])
        matchup_row.pack(fill="x")
        left_name = tk.Label(matchup_row, text="", font=("Tahoma", 13, "bold"), bg=self.colors["chrome"], fg=self.colors["text"], anchor="e", width=28)
        left_name.pack(side="left", expand=True, fill="x", padx=(6, 4))
        vs_label = tk.Label(matchup_row, text="", font=("Tahoma", 11, "bold"), bg=self.colors["chrome"], fg=self.colors["red"])
        vs_label.pack(side="left")
        right_name = tk.Label(matchup_row, text="", font=("Tahoma", 13, "bold"), bg=self.colors["chrome"], fg=self.colors["text"], anchor="w", width=28)
        right_name.pack(side="left", expand=True, fill="x", padx=(4, 6))
        score_label = tk.Label(window, text="", font=("Consolas", 10, "bold"), bg=self.colors["chrome"], fg=self.colors["gold"])
        score_label.pack(fill="x", padx=8, pady=(0, 2))
        fight_read_label = tk.Label(window, text="", font=("Tahoma", 9, "bold"), bg=self.colors["chrome"], fg=self.colors["text"])
        fight_read_label.pack(fill="x", padx=8, pady=(0, 4))

        # Pack the control bar at the bottom FIRST so it always reserves its
        # space; the play-by-play body then expands into whatever is left.
        controls_area = ttk.Frame(window, style="Chrome.TFrame")
        controls_area.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        controls = ttk.Frame(controls_area, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 2))
        controls2 = ttk.Frame(controls_area, style="Chrome.TFrame")
        controls2.pack(fill="x")

        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(side="top", fill="both", expand=True, padx=8, pady=8)
        fight_list = tk.Listbox(body, width=34, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        fight_list.pack(side="left", fill="y", padx=(0, 8))
        for index, fight_log in enumerate(package.get("fight_logs", []), 1):
            heading = fight_log.get("heading", fight_log.get("fight", f"Bout {index}"))
            fight_list.insert("end", f"{index}. {heading[:38]}")

        text = tk.Text(body, wrap="word", font=("Courier New", 11), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=14, pady=14, spacing1=3, spacing2=2, spacing3=8)
        text.pack(side="left", fill="both", expand=True)
        text.tag_configure("heading", font=("Courier New", 12, "bold"), foreground=self.colors["gold"])
        text.tag_configure("result", font=("Courier New", 12, "bold"), foreground=self.colors["red"])
        text.tag_configure("round", font=("Courier New", 11, "bold"))
        # Bright event-critical colors remain readable on the UFC theme's near-black canvas.
        text.tag_configure("knockdown", font=("Courier New", 11, "bold"), foreground="#ffb454")
        text.tag_configure("finish", font=("Courier New", 12, "bold"), foreground="#ff6b6b")
        text.tag_configure("cut", foreground="#ffb4a2")
        text.tag_configure("referee", font=("Courier New", 11, "bold"), foreground="#7dd3fc")
        text.config(state="disabled")

        state = {"fight": -1, "line": 0, "delay": max(120, min(3000, self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 2150)), "running": False, "finished": False}
        fight_logs = package.get("fight_logs", [{"heading": "Event Report", "lines": package["log"]}])

        def append_line(value):
            text.config(state="normal")
            tag = None
            lowered = value.lower()
            if value.startswith(("MAIN", "TITLE", "INTERIM", "BOUT")) or value.endswith(":"):
                tag = "heading"
            elif value.startswith("Result:"):
                tag = "result"
            elif (value.startswith("Round ") and "summary:" in value) or (value.startswith("R") and ":" in value[:5]):
                tag = "round"
            elif "referee" in lowered or "official" in lowered:
                tag = "referee"
            elif any(k in lowered for k in ("taps to", "and it's all over", "unconscious", "stops the fight", "by ko", "by tko", "by submission")):
                tag = "finish"
            elif any(k in lowered for k in ("drops", "hits the mat", "stumbles badly", "knocked down", "wobbl", "buckl", "rocked", "hurt")):
                tag = "knockdown"
            elif "cut" in lowered or "swelling" in lowered:
                tag = "cut"
            if tag:
                text.insert("end", value + "\n\n", tag)
            else:
                text.insert("end", value + "\n\n")
            text.see("end")
            text.config(state="disabled")
            # Keep the scoreboard live off the round summaries.
            if value.startswith("Round ") and "Live score" in value:
                fragment = value.split("Live score", 1)[1]
                score_label.config(text="Live score:  " + fragment.split(". Gas", 1)[0].strip())
                if "Gas" in value:
                    fight_read_label.config(text="Corner read: " + value.split("Gas", 1)[1].strip(" ."))
            elif value.startswith("R") and "Scores " in value:
                score_label.config(text="Live score:  " + value.split("Scores ", 1)[1].strip())
            elif value.startswith(("Corner read:", "Mat-side read:")):
                fight_read_label.config(text=value)
            elif value.startswith("Result:"):
                score_label.config(text=value.replace("Result: ", "").split(" | ")[0])
                fight_read_label.config(text=value.replace("Result: ", "").split(" | ")[-1])

        def finish_live_event():
            if state["finished"]:
                return
            state["finished"] = True
            if apply_results:
                self.finish_event(event, package)
                append_line("\n[Event processed. Results have been applied to the world.]")
            else:
                append_line("\n[Simulation complete. No world results were applied.]")
            if on_complete:
                on_complete()

        def mark_fight_done(index):
            log = fight_logs[index]
            result = log.get("result")
            if result and fight_list.size() > index:
                fight_list.delete(index)
                fight_list.insert(index, f"{index + 1}. Done - {result[:34]}")

        def update_scoreboard(log):
            label_chip.config(text=log.get("label", ""))
            a_name, b_name = log.get("a", ""), log.get("b", "")
            if a_name and b_name:
                left_name.config(text=f"{a_name}\n{log.get('a_record', '')}")
                vs_label.config(text="VS")
                right_name.config(text=f"{b_name}\n{log.get('b_record', '')}")
            else:
                left_name.config(text=log.get("heading", "")[:40])
                vs_label.config(text="")
                right_name.config(text="")
            score_label.config(text="")
            if a_name and b_name:
                fight_read_label.config(text=f"{log.get('weight', '')} | {log.get('label', 'Bout')} | Watch fatigue, damage, and round-by-round scoring.")
            else:
                fight_read_label.config(text="")

        def start_next_fight():
            if state["finished"]:
                return
            state["running"] = False
            if 0 <= state["fight"] < len(fight_logs):
                mark_fight_done(state["fight"])
            state["fight"] += 1
            state["line"] = 0
            if state["fight"] >= len(fight_logs):
                finish_live_event()
                return
            fight_list.selection_clear(0, "end")
            if fight_list.size():
                fight_list.selection_set(state["fight"])
                fight_list.see(state["fight"])
            log = fight_logs[state["fight"]]
            heading = log.get("heading", log.get("fight", "Bout"))
            title_label.config(text=f"LIVE FIGHT: {heading[:70]}")
            update_scoreboard(log)
            text.config(state="normal")
            text.delete("1.0", "end")
            text.config(state="disabled")
            append_line(log["heading"])
            append_line("-" * 72)

        def append_next():
            if state["finished"]:
                return
            if state["fight"] < 0:
                start_next_fight()
            lines = fight_logs[state["fight"]]["lines"]
            if state["line"] >= len(lines):
                if state.get("auto") and not state["finished"]:
                    def auto_continue():
                        if state["finished"]:
                            return
                        start_next_fight()
                        if not state["finished"]:
                            state["running"] = True
                            append_next()
                    window.after(max(600, state["delay"] * 2), auto_continue)
                    return
                state["running"] = False
                append_line("\n[Fight complete. Press Start Next Fight.]")
                return
            append_line(lines[state["line"]])
            state["line"] += 1
            if state["running"]:
                window.after(state["delay"], append_next)

        def start():
            if state["finished"]:
                return
            state["running"] = True
            append_next()

        def faster():
            state["delay"] = max(120, state["delay"] - 150)
            self.fight_timer_delay.set(state["delay"])
            speed_var.set(state["delay"])

        def slower():
            state["delay"] = min(3000, state["delay"] + 150)
            self.fight_timer_delay.set(state["delay"])
            speed_var.set(state["delay"])

        def apply_speed():
            state["delay"] = max(120, min(3000, int(speed_var.get())))
            self.fight_timer_delay.set(state["delay"])

        def pause_resume():
            if state["finished"]:
                return
            state["running"] = not state["running"]
            pause_button.config(text="Pause Timer" if state["running"] else "Resume Timer")
            if state["running"]:
                append_next()

        def next_round():
            if state["fight"] < 0:
                start_next_fight()
            state["running"] = False
            lines = fight_logs[state["fight"]]["lines"]
            while state["line"] < len(lines):
                line = lines[state["line"]]
                append_next()
                if "Round " in line and "summary:" in line:
                    break
                if "Result:" in line:
                    break

        def skip_current_fight():
            if state["finished"]:
                return
            if state["fight"] < 0:
                start_next_fight()
            state["running"] = False
            lines = fight_logs[state["fight"]]["lines"]
            while state["line"] < len(lines):
                append_line(lines[state["line"]])
                state["line"] += 1
            append_line("\n[Fight complete. Press Start Next Fight.]")

        def skip_to_end():
            state["running"] = False
            finish_live_event()

        ttk.Button(controls, text="Start Next Fight", style="Accent.TButton", command=start_next_fight).pack(side="left", padx=4)
        ttk.Button(controls, text="Play Fight", command=start).pack(side="left", padx=4)
        pause_button = ttk.Button(controls, text="Pause Timer", command=pause_resume)
        pause_button.pack(side="left", padx=4)
        auto_var = tk.BooleanVar(value=False)

        def toggle_auto():
            state["auto"] = bool(auto_var.get())
            if state["auto"] and not state["running"] and not state["finished"]:
                if state["fight"] < 0:
                    start_next_fight()
                state["running"] = True
                append_next()
        ttk.Checkbutton(controls, text="Auto-play card", variable=auto_var, command=toggle_auto).pack(side="left", padx=6)
        ttk.Button(controls, text="Next Round", command=next_round).pack(side="left", padx=4)
        ttk.Button(controls, text="Skip Fight", command=skip_current_fight).pack(side="left", padx=4)
        # Second row: speed and event controls.
        ttk.Button(controls2, text="Slower", command=slower).pack(side="left", padx=4)
        ttk.Button(controls2, text="Faster", command=faster).pack(side="left", padx=4)
        ttk.Label(controls2, text="Timer ms", style="Panel.TLabel").pack(side="left", padx=(12, 2))
        speed_var = tk.IntVar(value=state["delay"])
        ttk.Spinbox(controls2, from_=120, to=3000, increment=50, textvariable=speed_var, width=6, command=apply_speed).pack(side="left", padx=2)
        ttk.Button(controls2, text="Apply Speed", command=apply_speed).pack(side="left", padx=4)
        ttk.Button(controls2, text="Skip Event", command=skip_to_end).pack(side="left", padx=4)
        ttk.Button(controls2, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right", padx=4)

    def sign_fighter(self):
        selected = self.market_tree.selection()
        if not selected:
            return
        fighter = next(f for f in self.free_agents if f.name == selected[0])
        signing_bonus = fighter.purse * 2
        if self.cash < signing_bonus:
            messagebox.showwarning("Not enough cash", f"Signing {fighter.name} requires a ${signing_bonus:,} bonus.")
            return
        self.cash -= signing_bonus
        self.free_agents.remove(fighter)
        self.clear_ai_contract_offer(fighter)
        fighter.contract_months = random.randint(10, 24)
        fighter.morale = min(100, fighter.morale + 8)
        self.roster.append(fighter)
        self.event_log.append(f"Signed {fighter.name} to a {fighter.contract_months}-month ${fighter.purse:,}/fight contract.")
        self.news.insert(0, f"{self.player_company_name} signed {fighter.name}, a {fighter.style} {fighter.weight} with {fighter.trait.lower()} reputation.")
        self.refresh_all()
        self.write_log()

    def open_contract_negotiation(self, fighter, existing=False):
        report = getattr(self, "scouting_reports", {}).get(fighter.name, {})
        if not existing and self.rules.get("scouting_mode", False) and report.get("reveal", 0) < 100:
            messagebox.showinfo("Scouting required", f"Complete a Full Scout report on {fighter.name} before opening contract negotiations.")
            return
        window = tk.Toplevel(self.root)
        window.title(f"Negotiate - {fighter.name}")
        window.geometry("660x600")
        window.minsize(600, 560)
        window.configure(bg=self.colors["chrome"])
        active_offer_company = getattr(fighter, "ai_offer_company", "") if not existing else ""
        active_offer_purse = getattr(fighter, "ai_offer_purse", 0) if active_offer_company else 0
        rival = next((promo for promo in self.promotions if promo.name == active_offer_company), None) or random.choice([promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)])
        leverage = 1 + fighter.popularity / 140 + (0.35 if fighter.champion else 0) + max(0, fighter.momentum) * 0.05
        loyalty = 0.82 if existing else 1.0
        ask = max(4000, round(fighter.purse * leverage * loyalty), round(active_offer_purse * 1.05) if active_offer_purse else 0)
        purse_var = tk.IntVar(value=ask)
        term_var = tk.IntVar(value=max(8, min(30, fighter.contract_months if existing else 12)))
        fights_var = tk.IntVar(value=5 if existing else 3)
        bonus_var = tk.IntVar(value=15)
        signing_var = tk.IntVar(value=max(0, round(ask * 0.5 / 1000) * 1000))
        exclusive_var = tk.BooleanVar(value=True)
        win_bonus_var = tk.IntVar(value=getattr(fighter, "win_bonus", 0))
        ppv_var = tk.IntVar(value=getattr(fighter, "ppv_points", 0))
        champ_clause_var = tk.BooleanVar(value=getattr(fighter, "champions_clause", False))
        title_shot_var = tk.BooleanVar(value=getattr(fighter, "title_shot_clause", False))
        main_event_promise_var = tk.BooleanVar(value=getattr(fighter, "main_event_promise", False))
        top_opponent_promise_var = tk.BooleanVar(value=getattr(fighter, "top_opponent_promise", False))

        wants = []
        persona = getattr(fighter, "negotiation_persona", "Professional")
        career_goal = getattr(fighter, "career_goal", "")
        if persona == "Hard Bargainer":
            wants.extend(["star pay", "clear terms"])
        elif persona == "Loyalist" and existing:
            wants.append("respect and direction")
        elif persona == "Star Chaser":
            wants.extend(["a share of the money", "star pay"])
        elif persona == "Security First":
            wants.extend(["guaranteed fights", "clear terms"])
        elif persona == "Competitive":
            wants.append("guaranteed title shot")
        goal_need = {
            "Win a World Title": "a credible title path",
            "Build a Win Streak": "regular competitive fights",
            "Become a Star": "visible featured opportunities",
            "Secure a Payday": "a stronger purse",
            "Earn Contract Security": "a secure contract term",
            "Settle a Rivalry": "a chance to settle their feud",
        }.get(career_goal)
        if goal_need:
            wants.append(goal_need)
        if fighter.champion or fighter.popularity > 70:
            wants.append("star pay")
        if fighter.champion or fighter.popularity > 78:
            wants.append("a share of the money")
        if fighter.morale < 50:
            wants.append("respect and direction")
        if fighter.age > 34:
            wants.append("guaranteed fights")
        if fighter.professionalism > 72:
            wants.append("clear terms")
        if not wants:
            wants.append("fair money")
        relation_discount = self.staff_effect("Talent Relations", 2600)
        state = {"attempts": 3, "target": ask + fighter.popularity * 420 + fighter.professionalism * 180 - relation_discount,
                 "rival_bid": 0}

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"NEGOTIATION: {fighter.name}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        info = tk.Text(body, height=6, wrap="word", bg=self.colors["cream"], fg=self.colors["text"], padx=8, pady=8)
        info.pack(fill="x", padx=8, pady=(8, 4))
        rival_text = (f"Live rival offer: {rival.name} is offering ${active_offer_purse:,}/fight for {fighter.ai_offer_months} months; you can beat it before next month."
                      if active_offer_purse else ("Renewal talks start warmer because they already work here." if existing else f"{rival.name} may bid if talks drag."))
        info.insert("end", f"{fighter.name} ({fighter.gender}, {fighter.weight})\nAgent: {fighter.agent_name} | Negotiation style: {persona}\nRecord {fighter.record} | OVR {fighter.overall} | Pop {fighter.popularity} | Morale {fighter.morale}\nCareer goal: {career_goal or 'Undeclared'} ({getattr(fighter, 'career_goal_progress', 0)}%).\nCamp says they value: {', '.join(dict.fromkeys(wants))}.\nOpening ask: about ${ask:,}/fight. {rival_text}")
        info.config(state="disabled")

        def evaluate():
            purse, term, fights = purse_var.get(), term_var.get(), fights_var.get()
            bonus, signing, exclusive = bonus_var.get(), signing_var.get(), exclusive_var.get()
            win_bonus, ppv = win_bonus_var.get(), ppv_var.get()
            champ_clause, title_shot = champ_clause_var.get(), title_shot_var.get()
            main_event_promise, top_opponent_promise = main_event_promise_var.get(), top_opponent_promise_var.get()
            score = purse + term * 260 + fights * 2100 + bonus * 260 + signing * 0.35 + self.company_pop * 190 + self.company_stability * 95
            score += 9000 if exclusive else -3500
            score += 12000 if existing else 0
            score += win_bonus * 0.5 + ppv * 3600
            score += 14000 if champ_clause else 0
            score += 9000 if title_shot else 0
            score += 7500 if main_event_promise else 0
            score += 6500 if top_opponent_promise else 0
            unmet = []
            if "star pay" in wants and purse < ask * 1.15:
                score -= 16000; unmet.append("star-level pay")
            if "a share of the money" in wants and ppv < 1 and win_bonus < purse:
                score -= 12000; unmet.append("a cut of the revenue (PPV points or a win bonus)")
            if "guaranteed fights" in wants and fights < 4:
                score -= 12000; unmet.append("more guaranteed fights")
            if "clear terms" in wants and not exclusive:
                score -= 9000; unmet.append("a clean exclusive deal")
            if "guaranteed title shot" in wants and not title_shot:
                score -= 11000; unmet.append("a path to a title shot")
            if "respect and direction" in wants and bonus < 12 and term < 12:
                score -= 9000; unmet.append("a longer, incentivised deal")
            if persona == "Star Chaser" and not main_event_promise:
                score -= 8500; unmet.append("a main-event opportunity")
            if persona == "Competitive" and not top_opponent_promise and not title_shot:
                score -= 7500; unmet.append("a top opponent or title path")
            if career_goal == "Secure a Payday" and purse < fighter.career_goal_target:
                score -= 13000; unmet.append("their target payday")
            if career_goal == "Earn Contract Security" and term < fighter.career_goal_target:
                score -= 11000; unmet.append("their preferred contract security")
            if career_goal == "Win a World Title" and not (title_shot or top_opponent_promise):
                score -= 10500; unmet.append("a credible title route")
            if career_goal == "Become a Star" and not main_event_promise:
                score -= 8500; unmet.append("featured exposure")
            if career_goal == "Settle a Rivalry" and not top_opponent_promise:
                score -= 6500; unmet.append("a route to their rivalry fight")
            if "fair money" in wants and purse < ask:
                score -= 10000; unmet.append("fair money")
            target = state["target"] + state["rival_bid"]
            pct = max(2, min(98, round(50 + (score - target) / 900)))
            return score, target, pct, unmet

        grid = ttk.Frame(body, style="Panel.TFrame")
        grid.pack(fill="x", padx=8)
        for label, var, lo, hi, step in (("Purse / fight", purse_var, 1, 600000, 1000), ("Signing bonus", signing_var, 0, 400000, 1000),
                                         ("Contract months", term_var, 1, 60, 1), ("Guaranteed fights", fights_var, 1, 12, 1),
                                         ("Finish bonus %", bonus_var, 0, 60, 1), ("Win bonus $", win_bonus_var, 0, 300000, 1000),
                                         ("PPV points %", ppv_var, 0, 15, 1)):
            row = ttk.Frame(grid, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            ttk.Spinbox(row, from_=lo, to=hi, increment=step, textvariable=var, width=11).pack(side="left", padx=6)
        clause_row = ttk.Frame(grid, style="Panel.TFrame")
        clause_row.pack(fill="x", pady=2)
        ttk.Checkbutton(clause_row, text="Exclusive", variable=exclusive_var).pack(side="left", padx=4)
        ttk.Checkbutton(clause_row, text="Champion's clause", variable=champ_clause_var).pack(side="left", padx=4)
        ttk.Checkbutton(clause_row, text="Guaranteed title shot", variable=title_shot_var).pack(side="left", padx=4)
        ttk.Checkbutton(clause_row, text="Main-event promise", variable=main_event_promise_var).pack(side="left", padx=4)
        ttk.Checkbutton(clause_row, text="Top-opponent promise", variable=top_opponent_promise_var).pack(side="left", padx=4)

        meter_row = ttk.Frame(body, style="Panel.TFrame")
        meter_row.pack(fill="x", padx=12, pady=(6, 2))
        ttk.Label(meter_row, text="Estimated acceptance", style="Panel.TLabel").pack(side="left")
        accept_bar = ttk.Progressbar(meter_row, length=240, maximum=100)
        accept_bar.pack(side="left", padx=8)
        accept_label = tk.Label(meter_row, text="", font=("Tahoma", 10, "bold"), bg=self.colors["chrome"], fg=self.colors["text"])
        accept_label.pack(side="left")
        result_label = ttk.Label(body, text=f"Attempts left: {state['attempts']}", style="Panel.TLabel")
        result_label.pack(anchor="w", padx=12, pady=(2, 6))

        def refresh_meter(*_):
            try:
                _score, _target, pct, unmet = evaluate()
            except (tk.TclError, ValueError):
                return
            accept_bar["value"] = pct
            colour = "#5ac37a" if pct >= 66 else ("#e0a83a" if pct >= 40 else "#e86a5c")
            accept_label.config(text=f"{pct}%", fg=colour)
        for var in (purse_var, term_var, fights_var, bonus_var, signing_var, win_bonus_var, ppv_var):
            var.trace_add("write", refresh_meter)
        for var in (exclusive_var, champ_clause_var, title_shot_var, main_event_promise_var, top_opponent_promise_var):
            var.trace_add("write", refresh_meter)
        refresh_meter()

        def submit():
            purse, term, fights = purse_var.get(), term_var.get(), fights_var.get()
            bonus, signing, exclusive = bonus_var.get(), signing_var.get(), exclusive_var.get()
            score, target, _pct, unmet = evaluate()
            score += random.randint(-4500, 4500)
            if score >= target:
                signing_cost = purse * (2 if exclusive else 1) + signing
                if self.cash < signing_cost:
                    result_label.config(text=f"Not enough cash for ${signing_cost:,} up-front cost.")
                    return
                self.cash -= signing_cost
                if not existing and fighter in self.free_agents:
                    self.free_agents.remove(fighter)
                    self.roster.append(fighter)
                fighter.purse = purse
                fighter.contract_months = term
                fighter.exclusive = exclusive
                fighter.contract_type = "Exclusive" if exclusive else "Non-Exclusive"
                fighter.win_bonus = win_bonus_var.get()
                fighter.ppv_points = ppv_var.get()
                fighter.champions_clause = champ_clause_var.get()
                fighter.title_shot_clause = title_shot_var.get()
                fighter.main_event_promise = main_event_promise_var.get()
                fighter.top_opponent_promise = top_opponent_promise_var.get()
                fighter.promise_deadline_month = self.month + 6 if fighter.main_event_promise or fighter.top_opponent_promise else 0
                fighter.relationship_trust = min(100, fighter.relationship_trust + 4)
                self.clear_ai_contract_offer(fighter)
                fighter.morale = min(100, fighter.morale + 6)
                fighter.negotiation_heat = max(0, fighter.negotiation_heat - 10)
                fighter.fight_history = fighter.fight_history or []
                clause_notes = []
                if fighter.win_bonus:
                    clause_notes.append(f"${fighter.win_bonus:,} win bonus")
                if fighter.ppv_points:
                    clause_notes.append(f"{fighter.ppv_points}% PPV points")
                if fighter.champions_clause:
                    clause_notes.append("champion's clause")
                if fighter.title_shot_clause:
                    clause_notes.append("guaranteed title shot")
                if fighter.main_event_promise:
                    clause_notes.append("main-event promise")
                if fighter.top_opponent_promise:
                    clause_notes.append("top-opponent promise")
                clause_text = (" Clauses: " + ", ".join(clause_notes) + ".") if clause_notes else ""
                fighter.fight_history.insert(0, f"Signed contract: {term} months, {fights} guaranteed fights, ${purse:,}/fight, ${signing:,} signing bonus, {bonus}% finish bonus.{clause_text}")
                self.news.insert(0, f"{fighter.name} agreed terms with {self.player_company_name}.")
                self.refresh_all()
                window.destroy()
                return
            state["attempts"] -= 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + 10)
            # A rival can enter the bidding when talks drag, raising the bar.
            if not existing and not active_offer_purse and state["attempts"] == 1 and fighter.popularity > 45 and random.random() < 0.6:
                state["rival_bid"] = round(ask * random.uniform(0.15, 0.4))
                result_label.config(text=f"{rival.name} has entered the bidding! {fighter.name} now wants more to stay. Attempts left: {state['attempts']}")
                refresh_meter()
                return
            if state["attempts"] <= 0:
                if active_offer_purse:
                    result_label.config(text=f"Your talks ended. {rival.name}'s live offer remains in place until next month.")
                elif not existing and state["rival_bid"] and random.random() < 0.5:
                    result_label.config(text=f"{fighter.name} signed with {rival.name} instead.")
                else:
                    result_label.config(text=f"{fighter.name}'s camp walks away. They wanted a stronger package.")
                submit_button.config(state="disabled")
                return
            if unmet:
                feedback = f"They still want {unmet[0]}."
            elif score < target - 15000:
                feedback = "The overall package is well short."
            else:
                feedback = "Close, but they want better total security."
            result_label.config(text=f"{feedback} Attempts left: {state['attempts']}")

        button_row = ttk.Frame(body, style="Panel.TFrame")
        button_row.pack(fill="x", pady=8)
        submit_button = ttk.Button(button_row, text="Submit Offer", style="Accent.TButton", command=submit)
        submit_button.pack(side="left", padx=12)
        ttk.Button(button_row, text="Walk Away", command=window.destroy).pack(side="right", padx=12)

    def open_negotiation(self):
        selected = self.market_tree.selection()
        if not selected:
            messagebox.showinfo("Negotiations", "Select a free agent first.")
            return
        fighter = next(f for f in self.free_agents if f.name == selected[0])
        self.open_contract_negotiation(fighter, existing=False)
        return
        window = tk.Toplevel(self.root)
        window.title(f"Negotiate - {fighter.name}")
        window.geometry("520x360")
        window.configure(bg=self.colors["chrome"])

        rival = random.choice(self.promotions)
        rival_offer = round(fighter.purse * random.uniform(0.85, 1.45) + rival.reputation_score * 220)
        purse_var = tk.IntVar(value=max(fighter.purse, rival_offer - 2500))
        term_var = tk.IntVar(value=12)
        exclusive_var = tk.BooleanVar(value=True)

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"NEGOTIATION: {fighter.name}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        info = (
            f"{fighter.weight} | {fighter.record} | OVR {fighter.overall} | Pop {fighter.popularity}\n"
            f"Style: {fighter.style} / {fighter.behaviour} | Camp: {fighter.camp}\n"
            f"Star {fighter.star_quality} | Media {fighter.media_presence} | Sponsor {fighter.sponsor_appeal} | Pro {fighter.professionalism}\n"
            f"Rival bid: {rival.name} offers about ${rival_offer:,}/fight\n"
            f"Non-exclusive deals are cheaper but allow outside fights."
        )
        ttk.Label(body, text=info, justify="left", style="Panel.TLabel").pack(anchor="w", padx=12, pady=10)
        row = ttk.Frame(body, style="Panel.TFrame")
        row.pack(fill="x", padx=12, pady=4)
        ttk.Label(row, text="Purse", style="Panel.TLabel").pack(side="left")
        ttk.Spinbox(row, from_=1000, to=250000, increment=1000, textvariable=purse_var, width=10).pack(side="left", padx=8)
        ttk.Label(row, text="Months", style="Panel.TLabel").pack(side="left")
        ttk.Spinbox(row, from_=1, to=60, textvariable=term_var, width=6).pack(side="left", padx=8)
        ttk.Checkbutton(row, text="Exclusive", variable=exclusive_var).pack(side="left", padx=8)

        result_label = ttk.Label(body, text="", style="Panel.TLabel")
        result_label.pack(anchor="w", padx=12, pady=8)

        def submit_offer():
            purse = purse_var.get()
            term = term_var.get()
            exclusive = exclusive_var.get()
            offer_score = purse + term * (230 + fighter.professionalism) + (6500 if exclusive else -3500) + self.company_pop * 170 + self.company_stability * 120
            rival_score = rival_offer + rival.reputation_score * 210 + rival.stability * 95 + random.randint(-8000, 8000)
            if offer_score >= rival_score or random.random() < 0.12:
                signing_bonus = purse * (2 if exclusive else 1)
                if self.cash < signing_bonus:
                    result_label.config(text=f"Not enough cash for the ${signing_bonus:,} signing cost.")
                    return
                self.cash -= signing_bonus
                self.free_agents.remove(fighter)
                fighter.purse = purse
                fighter.contract_months = term
                fighter.exclusive = exclusive
                fighter.contract_type = "Exclusive" if exclusive else "Non-Exclusive"
                fighter.morale = min(100, fighter.morale + 8)
                self.roster.append(fighter)
                self.news.insert(0, f"{self.player_company_name} beat {rival.name} to sign {fighter.name} on a {fighter.contract_type.lower()} deal.")
                self.event_log.insert(0, f"Signed {fighter.name}: {term} months, ${purse:,}/fight, {fighter.contract_type}.")
                self.refresh_all()
                self.write_log()
                window.destroy()
            else:
                fighter.negotiation_heat = min(100, fighter.negotiation_heat + 14)
                result_label.config(text=f"{fighter.name} rejected the offer. {rival.name}'s bid is stronger.")

        ttk.Button(body, text="Submit Offer", style="Accent.TButton", command=submit_offer).pack(side="left", padx=12, pady=12)
        ttk.Button(body, text="Walk Away", command=window.destroy).pack(side="right", padx=12, pady=12)

    def fight_hype(self, a, b, fight):
        title = 12 if fight.get("title") else 0
        main = 8 if fight.get("main") else 0
        tier_factor = {"Main Card": 1.0, "Prelims": 0.72, "Early Prelims": 0.48}.get(fight.get("tier", "Main Card"), 1.0)
        rivalry = abs(a.momentum - b.momentum) + self.rivalry_heat_between(a, b) * 0.28
        media = self.match_build_score(a, b, fight) * 0.18
        rank_bonus = 0
        for fighter in (a, b):
            rank = self.division_rank_number(fighter)
            if fighter.champion:
                rank_bonus += 7
            elif rank and rank <= 5:
                rank_bonus += 5
            elif rank and rank <= 10:
                rank_bonus += 3
        marketing_lift = self.staff_effect("Marketing", 0.45)
        return max(1, round(((a.popularity + b.popularity) / 2 + title + main + rivalry / 2 + media + rank_bonus + marketing_lift) * tier_factor))

    def division_rank_number(self, fighter):
        division = sorted([f for f in self.roster if f.weight == fighter.weight and f.gender == fighter.gender], key=lambda item: self.rank_value(item), reverse=True)
        for index, item in enumerate(division, 1):
            if item.name == fighter.name:
                return index
        return None

    def division_rank_label(self, fighter):
        if fighter.champion:
            return "C"
        rank = self.division_rank_number(fighter)
        return f"#{rank}" if rank else "-"

    def fight_build_score(self, fighter):
        trait_bonus = {
            "Fan Favourite": 12,
            "Marketable": 14,
            "Media Natural": 13,
            "Showman": 12,
            "Trash Talker": 10,
            "Big Finisher": 8,
            "Knockout Artist": 9,
            "Submission Ace": 7,
            "Title Mentality": 6,
            "Clutch": 5,
            "Erratic": 4,
            "Slow Starter": -2,
            "Fragile": -4,
            "Injury Magnet": -5,
            "Bad Weight Cut": -5,
            "Gym Rat": 1,
            "Quiet Professional": -1,
            "Prospect Mindset": 3,
            "Short Notice Hero": 4,
        }.get(fighter.trait, 0)
        media = fighter.media_heat * 0.7 + fighter.media_presence * 0.35 + fighter.negotiation_heat * 0.15
        streak = max(-10, min(15, fighter.momentum * 3))
        rank = self.division_rank_number(fighter) or 25
        rank_bonus = 12 if fighter.champion else max(0, 12 - rank)
        finish_bonus = max(0, fighter.power + fighter.submissions - 130) * 0.12
        return max(1, min(99, round(fighter.popularity * 0.5 + fighter.star_quality * 0.22 + fighter.charisma * 0.12 + media + streak + rank_bonus + trait_bonus + finish_bonus)))

    def match_build_score(self, a, b, fight):
        style_clash = 6 if a.style != b.style else 1
        rivalry = 10 + self.rivalry_heat_between(a, b) * 0.22 if a.rival == b.name or b.rival == a.name else 0
        stakes = (10 if fight.get("title") else 0) + (6 if fight.get("main") else 0)
        competitiveness = max(0, 18 - abs(a.overall - b.overall))
        matchmaker_lift = self.staff_effect("Matchmaker", 0.28)
        return max(1, min(99, round((self.fight_build_score(a) + self.fight_build_score(b)) / 2 + style_clash + rivalry + stakes + competitiveness * 0.35 + matchmaker_lift)))

    def run_event(self):
        if len(self.booked) < 1:
            messagebox.showinfo("No fights", "Book at least one fight before running an event.")
            return
        self.normalize_card_order()
        current_name = self.event_name.get().strip()
        event_name = self.default_event_name(self.next_player_event_number()) if self.is_auto_event_name(current_name) else current_name
        event = {"name": event_name, "venue": self.venue.get(), "region": self.event_region.get(), "city": self.event_city.get(), "month": self.month, "week": self.week, "fights": [dict(fight) for fight in self.booked]}
        package = self.prepare_event_result(event)
        self.finish_event(None, package)
        self.booked.clear()
        self.event_name.set(self.default_event_name())
        self.refresh_all()
        self.select_tab("log")

    def run_press_conference(self, event):
        """Pre-fight press conference and weigh-in face-offs. Builds media heat and hype
        for the marquee fights, can spark rivalries, and feeds the gate/PPV take."""
        lines = ["", "PRESS CONFERENCE & FACE-OFFS"]
        hype_bonus = 0.0
        touched = False
        for fight in event.get("fights", []):
            if not (fight.get("main") or fight.get("title")):
                continue
            names = [n for n in fight.get("fighters", []) if n != "TBA"]
            fighters = [self.get_fighter(n) for n in names if any(r.name == n for r in self.roster)]
            if len(fighters) < 2:
                continue
            a, b = fighters[0], fighters[1]
            moment = self.press_faceoff_moment(a, b)
            lines.append(moment["line"])
            hype_bonus += moment["hype"]
            a.media_heat = min(100, a.media_heat + moment["heat"])
            b.media_heat = min(100, b.media_heat + moment["heat"])
            if moment["spark"] and not a.rival and not b.rival:
                self.establish_rivalry(a, b, "Press-conference confrontation", heat=random.randint(38, 58))
                lines.append(f"  A genuine grudge is born - {a.name} and {b.name} now have real history.")
            touched = True
        if not touched:
            lines.append("  A businesslike build; the fighters let their skills do the talking.")
        return lines, round(hype_bonus)

    def press_faceoff_moment(self, a, b):
        """Generate a face-off beat driven by charisma, media presence, traits and rivalry."""
        rivalry = a.rival == b.name or b.rival == a.name
        talkers = {"Trash Talker", "Showman", "Media Natural", "Fan Favourite", "Marketable"}
        quiet = {"Quiet Professional", "Coach Favourite"}
        charisma = (a.charisma + b.charisma) / 2 + (a.media_presence + b.media_presence) / 4
        a_loud = a.trait in talkers
        b_loud = b.trait in talkers
        heat = 4 + round(charisma / 22)
        hype = 3 + charisma / 20
        spark = False
        if rivalry:
            hype += 16
            heat += 8
            line = random.choice([
                f"  {a.name} and {b.name} have to be separated at the face-off - the arena is buzzing.",
                f"  Bad blood boils over: {a.name} and {b.name} go forehead-to-forehead and refuse to break.",
                f"  Security steps in as {a.name} and {b.name} trade words nose-to-nose.",
            ])
        elif a_loud and b_loud:
            hype += 11
            heat += 6
            spark = random.random() < 0.35
            line = f"  {a.name} and {b.name} light up the press conference with a genuine verbal war."
        elif a_loud or b_loud:
            loud = a if a_loud else b
            calm = b if a_loud else a
            hype += 6
            heat += 3
            spark = random.random() < 0.2
            line = f"  {loud.name} works the microphone hard while {calm.name} stays measured."
        elif a.trait in quiet and b.trait in quiet:
            hype += 1
            line = f"  {a.name} and {b.name} share a respectful, quiet face-off - all business."
        else:
            hype += 3
            line = f"  A composed face-off between {a.name} and {b.name}; the tension simmers under the surface."
        return {"line": line, "hype": hype, "heat": heat, "spark": spark}

    def prepare_event_result(self, event):
        log = [f"{event['name']} - {event['venue']} ({self.event_date_label(event)})", "=" * 72]
        press_log, press_hype = self.run_press_conference(event)
        log.extend(press_log)
        weigh_log, purse_penalty, cancelled_fights = self.run_weigh_ins(event)
        log.extend(weigh_log)
        total_hype = press_hype
        total_cost = -purse_penalty
        total_build = 0
        total_excitement = 0
        results = []
        award_pool = []
        fight_logs = []
        ordered = self.event_fight_order(event["fights"])
        for fight in ordered:
            if fight in cancelled_fights:
                fight_logs.append({"heading": "Cancelled bout", "lines": [f"{' vs '.join(fight.get('fighters', []))} was cancelled after weigh-ins."]})
                continue
            fight = dict(fight)
            # Player-event post-processing still needs both fighters for contract
            # clauses, awards, regional effects and the final recap.  Defer a
            # pending retirement until finish_event has completed those steps.
            fight["_defer_retirement"] = True
            fight.setdefault("region", event.get("region", self.venue_region(event["venue"])))
            fight.setdefault("city", event.get("city", ""))
            a, b = self.resolve_fight_fighters(fight)
            hype = self.fight_hype(a, b, fight)
            build = self.match_build_score(a, b, fight)
            total_hype += hype
            total_build += build
            total_cost += a.purse + b.purse
            winner, loser, method, round_no, commentary = self.simulate_fight(a, b, fight)
            excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, hype)
            total_excitement += excitement
            results.append((winner, loser, fight, method))
            award_pool.append({"winner": winner.name if method != "Draw" else "", "loser": loser.name if method != "Draw" else "", "fighters": [a.name, b.name], "method": method, "excitement": excitement, "round": round_no, "fight": f"{a.name} vs {b.name}"})
            label = "MAIN EVENT" if fight["main"] else ("TITLE FIGHT" if fight["title"] else "BOUT")
            if fight.get("interim"):
                label = "INTERIM " + label
            lines = [f"{label}: {a.name} vs {b.name} ({a.weight})", f"Odds: {self.matchup_odds(a, b)}"]
            red_form = f"{a.name}: camp {fight.get('red_camp', fight.get('camp_weeks', 8))}w, morale {a.morale}, fatigue {a.fatigue}, cut penalty {getattr(a, 'weight_cut_penalty', 0)}"
            blue_form = f"{b.name}: camp {fight.get('blue_camp', fight.get('camp_weeks', 8))}w, morale {b.morale}, fatigue {b.fatigue}, cut penalty {getattr(b, 'weight_cut_penalty', 0)}"
            lines.append(f"Corner read: {red_form} | {blue_form}")
            lines.extend(commentary)
            if method == "Draw":
                lines.append(f"Result: {a.name} vs {b.name} ends in a draw, R{round_no} | Fight excitement {excitement}")
                result_text = f"Draw (R{round_no})"
            else:
                lines.append(f"Result: {winner.name} def. {loser.name} by {method}, R{round_no} | Fight excitement {excitement}")
                result_text = f"{winner.name} - {method} R{round_no}"
            fight_logs.append({
                "heading": lines[0], "lines": lines,
                "a": a.name, "b": b.name, "a_record": a.record, "b_record": b.record,
                "weight": a.weight, "label": label, "result": result_text, "excitement": excitement,
            })
            log.append("\n" + lines[0])
            log.extend(f"  {line}" for line in lines[1:])

        completed = max(1, len(results))
        avg_hype = total_hype / completed
        avg_build = total_build / completed
        avg_excitement = total_excitement / completed
        regional_pull = self.regional_market_score(event.get("region", self.venue_region(event["venue"])))
        finance = self.calculate_event_finance(total_hype, total_cost, event, results, avg_excitement, avg_build, regional_pull)
        awards = self.choose_event_awards(award_pool)
        gate = finance["ticket_revenue"]
        profit = finance["profit"]
        mismatch_penalty = self.card_mismatch_penalty(results)
        projected_pop = min(100, max(1, self.company_pop + round((avg_hype - 50) / 11 + (avg_excitement - 52) / 14 + (regional_pull - 1) * 2.4)))
        projected_stability = min(100, max(1, self.company_stability + round(profit / 350000 + (avg_excitement - 42) / 24 + (finance["attendance"] / max(1, finance["venue_capacity"])) * 2.5 - 0.5 - mismatch_penalty * 0.35)))
        log.append("\n" + "=" * 72)
        log.append(f"Event hype {round(avg_hype)} | Fight build {round(avg_build)} | Fight excitement {round(avg_excitement)} | Regional pull x{regional_pull:.2f} | Media reach {finance['media_reach']}")
        atmosphere = finance.get("atmosphere", {})
        log.append(f"Crowd atmosphere: {atmosphere.get('mood', 'Engaged')} ({atmosphere.get('intensity', 50)}/100) — {atmosphere.get('identity', 'Local MMA community')}; preference: {atmosphere.get('preference', 'Competitive fights')}.")
        log.append(f"Attendance: {finance['attendance']:,} / {finance['venue_capacity']:,} | Ticket price ${finance['ticket_price']:,} | Mismatch penalty {mismatch_penalty}")
        log.append(f"Gate: ${finance['ticket_revenue']:,} | Broadcast: ${finance['broadcast_income']:,} | Sponsors: ${finance['sponsorship']:,} | Merch: ${finance['merchandise']:,}")
        log.append(f"Fighter pay: ${finance['fighter_pay']:,} | Bonuses: ${finance['bonuses']:,} | Production: ${finance['production']:,} | Medical: ${finance['medical']:,} | Marketing: ${finance['marketing']:,} | Tax: ${finance['tax']:,}")
        log.append(f"Total revenue: ${finance['total_revenue']:,} | Total expense: ${finance['total_expense']:,} | Profit: ${profit:,}")
        log.append(f"Company popularity will move from {self.company_pop} to {projected_pop}. Stability will move from {self.company_stability} to {projected_stability}.")
        summary = f"{event['name']} ({event['venue']}, {self.event_date_label(event)}): {len(event['fights'])} fights, excitement {round(avg_excitement)}, gate ${gate:,}, profit ${profit:,}, popularity {projected_pop}%, stability {projected_stability}%"
        return {
            "log": log,
            "results": results,
            "gate": gate,
            "profit": profit,
            "finance": finance,
            "projected_pop": projected_pop,
            "projected_stability": projected_stability,
            "average_excitement": avg_excitement,
            "awards": awards,
            "fight_count": len(results),
            "fight_logs": fight_logs,
            "award_pool": award_pool,
            "weigh_in_log": weigh_log,
            "event_name": event["name"],
            "venue": event["venue"],
            "region": event.get("region", self.venue_region(event["venue"])),
            "city": event.get("city", ""),
            "month": event["month"],
            "week": event.get("week", 1),
            "summary": summary,
        }

    def card_mismatch_penalty(self, results):
        penalty = 0
        for _winner, _loser, fight, _method in results:
            names = [name for name in fight.get("fighters", []) if name != "TBA"]
            if len(names) != 2:
                continue
            a, b = [self.get_fighter(name) for name in names]
            rank_a = self.division_rank_number(a) or 30
            rank_b = self.division_rank_number(b) or 30
            rank_gap = abs(rank_a - rank_b)
            skill_gap = abs(a.overall - b.overall)
            if rank_gap >= 12:
                penalty += 1
            if rank_gap >= 18 or skill_gap >= 14:
                penalty += 1
            if (fight.get("main") or fight.get("title")) and (rank_gap >= 12 or skill_gap >= 12):
                penalty += 1
        return min(8, penalty)

    def event_fight_order(self, fights):
        tier_order = {"Early Prelims": 0, "Prelims": 1, "Main Card": 2}
        return sorted(fights, key=lambda f: (tier_order.get(f.get("tier", "Main Card"), 2), f.get("main", False), f.get("title", False)))

    def weight_class_move_assessment(self, fighter, target_weight):
        """Return whether a division move is viable from the fighter's body, not a menu choice."""
        if target_weight not in WEIGHT_LIMITS:
            return False, "That division is not recognised."
        if target_weight == fighter.weight:
            return False, f"{fighter.name} already competes at {target_weight}."
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        cut_skill = self.ds(fighter, "weight_cutting", fighter.cardio)
        natural_size = self.ds(fighter, "natural_size", 50)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        current_limit = WEIGHT_LIMITS.get(fighter.weight, 170)
        target_limit = WEIGHT_LIMITS[target_weight]
        if target_limit < current_limit:
            required_cut = max(0, walk - target_limit)
            sustainable_cut = 9 + cut_skill * 0.16 + conditioning * 0.04 - max(0, natural_size - 55) * 0.12
            if required_cut > sustainable_cut + 2:
                return False, f"Unsafe cut: {walk} lb walk weight needs {required_cut:.0f} lb off; their frame and cutting skill support about {sustainable_cut:.0f} lb."
            risk = "manageable" if required_cut <= sustainable_cut - 3 else "demanding"
            return True, f"{risk.title()} cut: {walk} lb to the {target_limit} lb limit requires {required_cut:.0f} lb; sustainable estimate {sustainable_cut:.0f} lb."
        natural_floor = walk - (7 + cut_skill * 0.08)
        gain_needed = max(0, target_limit - walk)
        if target_limit > natural_floor + 42 or gain_needed > 35:
            return False, f"Unnatural jump: {walk} lb walk weight is too small for a credible move to {target_weight}."
        return True, f"Natural move up: {walk} lb frame can add toward the {target_limit} lb limit over a full camp."

    def complete_weight_class_move(self, fighter, target_weight, reason):
        """Apply a validated move; shared by the player UI and world simulation."""
        old_weight = fighter.weight
        fighter.weight = target_weight
        fighter.scale_weight = 0.0
        fighter.weight_cut_penalty = 0
        fighter.missed_weight = False
        fighter.camp_weeks = 0
        fighter.camp_boost = 0
        fighter.weight_move_last_month = self.month
        fighter.rank_score = self.rank_value(fighter)
        note = f"Month {self.month}: Moved from {old_weight} to {target_weight} — {reason}"
        fighter.weight_class_history = (fighter.weight_class_history or [])[-19:] + [note]
        fighter.fight_history = fighter.fight_history or []
        fighter.fight_history.insert(0, note)
        self.news.insert(0, f"{fighter.name} moved from {old_weight} to {target_weight}. {reason}")
        return True

    def move_fighter_weight_class(self, fighter, target_weight):
        allowed, reason = self.weight_class_move_assessment(fighter, target_weight)
        if not allowed:
            messagebox.showwarning("Division move declined", reason)
            return False
        if fighter.champion or fighter.interim_champion:
            messagebox.showwarning("Vacate title first", "A champion must vacate their belt before changing division.")
            return False
        if fighter.name in self.scheduled_fighter_names(include_booked=True):
            messagebox.showwarning("Future booking", "Complete or remove the fighter's booked bout before changing division.")
            return False
        self.complete_weight_class_move(fighter, target_weight, reason)
        self.refresh_all()
        return True

    def perform_weigh_in(self, fighter, title_fight=False, camp_weeks=None, persist=True):
        """Resolve a cut once for both real cards and sandbox simulations."""
        limit = WEIGHT_LIMITS.get(fighter.weight, 170) + (0 if title_fight else 1)
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        cut_amount = max(0, walk - limit)
        cut_skill = self.ds(fighter, "weight_cutting", fighter.cardio)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        natural_size = self.ds(fighter, "natural_size", 50)
        weeks = fighter.camp_weeks if camp_weeks is None else max(0, int(camp_weeks))
        camp_quality = fighter.camp_quality or self.gym_quality(fighter.camp)
        focus_bonus = 3.0 if getattr(fighter, "camp_focus", "") == "Weight Management" else 0.0
        preparation = min(9.0, weeks * 0.82) + fighter.camp_boost * 0.7 + camp_quality * 0.025 + focus_bonus
        sustainable_cut = 8 + cut_skill * 0.15 + conditioning * 0.045 + preparation - max(0, natural_size - 55) * 0.1
        variance = random.uniform(-3.0, 2.2)
        miss_by = max(0, round((cut_amount - sustainable_cut + variance) * 0.75, 1))
        scale_weight = round(limit + miss_by if miss_by else limit - random.uniform(0.1, 1.0), 1)
        penalty = max(0, min(22, round(max(0, cut_amount - sustainable_cut + 5) * 0.7 + miss_by * 3 + max(0, 3 - weeks) * 0.8)))
        result = {"limit": limit, "walk": walk, "cut_amount": cut_amount, "miss_by": miss_by, "scale_weight": scale_weight, "penalty": penalty, "made": miss_by <= 0}
        if persist:
            fighter.scale_weight = scale_weight
            fighter.missed_weight = miss_by > 0
            fighter.weight_cut_penalty = penalty
        return result

    def run_weigh_ins(self, event):
        lines = ["", "WEIGH-INS"]
        purse_penalty = 0
        cancelled = []
        for fight in event["fights"]:
            names = [name for name in fight.get("fighters", []) if name != "TBA"]
            fighters = [self.get_fighter(name) for name in names if any(r.name == name for r in self.roster)]
            if len(fighters) < 2:
                continue
            misses = []
            for fighter in fighters:
                outcome = self.perform_weigh_in(fighter, title_fight=fight.get("title", False), persist=True)
                miss_by = outcome["miss_by"]
                if fighter.missed_weight:
                    misses.append((fighter, miss_by))
                    fine = round(fighter.purse * (0.2 if miss_by <= 2 else 0.3))
                    purse_penalty += fine
                    fighter.morale = max(1, fighter.morale - 7)
                    fighter.popularity = max(1, fighter.popularity - 1)
                    lines.append(f"{fighter.name} missed {fighter.weight} by {miss_by} lb ({fighter.scale_weight} lb). Fine ${fine:,}; cut penalty {fighter.weight_cut_penalty}.")
                else:
                    lines.append(f"{fighter.name} made {fighter.weight} at {fighter.scale_weight} lb. Cut penalty {fighter.weight_cut_penalty}.")
            if len(misses) == 2 or any(miss_by > 7 for _fighter, miss_by in misses):
                made = next((fighter for fighter in fighters if not fighter.missed_weight), None)
                if made and len(misses) == 1:
                    replacement = self.find_tba_replacement(made.weight, made.gender, known=made, short_notice=True)
                    fight["fighters"] = [made.name, replacement.name]
                    fight["title"] = False; fight["interim"] = False; fight["catchweight"] = True
                    lines.append(f"{misses[0][0].name} was removed after a bad miss; {replacement.name} steps in on short notice against {made.name}.")
                else:
                    cancelled.append(fight)
                    self.queue_cancelled_bout_rebooking(event, fight, names)
                    lines.append(f"{' vs '.join(names)} was cancelled by the commission after a bad weigh-in and queued for rebooking.")
            elif misses:
                fight["catchweight"] = True
                fight["title"] = False
                fight["interim"] = False
                lines.append(f"{' vs '.join(names)} continues as a catchweight non-title bout.")
        return lines, purse_penalty, cancelled

    def queue_cancelled_bout_rebooking(self, event, fight, names):
        entry = {"fighters": list(names), "weight": fight.get("weight", ""), "tier": fight.get("tier", "Main Card"), "main": fight.get("main", False), "title": False, "interim": False, "source_event": event.get("name", "Event"), "target_month": self.month + 1, "status": "Awaiting rebooking"}
        self.pending_rebookings = getattr(self, "pending_rebookings", [])
        self.pending_rebookings.append(entry)
        self.inbox.append({"subject": f"Rebooking Required - {' vs '.join(names)}", "body": f"Cancelled from {entry['source_event']} after weigh-ins. Preserve {entry['tier']} placement when rebooking next month.", "type": "Roster", "resolved": False})

    def matchup_odds(self, a, b):
        a_score = a.overall * 1.7 + a.momentum * 5 + a.camp_boost * 4 - a.weight_cut_penalty * 3 + a.fight_iq * 0.25
        b_score = b.overall * 1.7 + b.momentum * 5 + b.camp_boost * 4 - b.weight_cut_penalty * 3 + b.fight_iq * 0.25
        diff = round(a_score - b_score)
        fav, dog, edge = (a, b, diff) if diff >= 0 else (b, a, -diff)
        fav_line = -110 - min(390, edge * 8)
        dog_line = 100 + min(500, edge * 7)
        return f"{fav.name} {fav_line} / {dog.name} +{dog_line}"

    def resolve_fight_fighters(self, fight):
        if "TBA" not in fight["fighters"]:
            return [self.get_fighter(name) for name in fight["fighters"]]
        known_name = next(name for name in fight["fighters"] if name != "TBA")
        known = self.get_fighter(known_name)
        replacement = self.find_tba_replacement(fight.get("tba_weight", known.weight), fight.get("tba_gender", known.gender), known=known, short_notice=True)
        fight["fighters"] = [known.name, replacement.name]
        fight["tba_filled"] = True
        fight["tba_note"] = f"{replacement.name} accepted a short-notice fight against {known.name}."
        self.news.insert(0, fight["tba_note"])
        return known, replacement

    def tba_replacement_score(self, fighter, known, short_notice):
        skill_fit = max(0, 28 - abs(fighter.overall - known.overall))
        business_fit = fighter.popularity * 0.42 + fighter.star_quality * 0.22 + fighter.media_presence * 0.12
        readiness = fighter.morale * 0.12 + fighter.professionalism * 0.12 - fighter.fatigue * 0.45
        cost_penalty = fighter.purse / (2800 if short_notice else 4200)
        age_penalty = max(0, fighter.age - 37) * 0.8
        short_notice_bonus = fighter.motivation * 0.08 + fighter.toughness * 0.06 if short_notice else fighter.camp_quality * 0.03
        return skill_fit + business_fit + readiness + short_notice_bonus - cost_penalty - age_penalty + random.uniform(-4, 4)

    def find_tba_replacement(self, weight, gender, known=None, event=None, short_notice=True):
        busy = self.scheduled_fighter_names(include_booked=True)
        candidates = [
            fighter for fighter in self.free_agents
            if fighter.weight == weight
            and fighter.gender == gender
            and fighter.name not in busy
            and not fighter.injured
            and fighter.fatigue < (62 if short_notice else 55)
        ]
        if candidates:
            if known:
                replacement = max(candidates, key=lambda fighter: self.tba_replacement_score(fighter, known, short_notice))
            else:
                replacement = max(candidates, key=lambda f: (f.morale + f.popularity + f.overall + f.motivation))
            self.free_agents.remove(replacement)
            source = "free agent"
        else:
            replacement = self.create_generated_fighter(5, 35, 38, 78, weight=weight, gender=gender)
            replacement.weight = weight
            replacement.gender = gender
            self.avoid_name_collision(replacement, self.active_fighter_names())
            source = "regional short-notice signing"
        multiplier = 1.35 if short_notice else 1.08
        if known:
            multiplier += max(0, known.popularity - replacement.popularity) / 220
        replacement.purse = max(replacement.purse, round(replacement.purse * multiplier / 500) * 500)
        replacement.contract_months = 1
        replacement.exclusive = False
        replacement.contract_type = "One-Fight Deal"
        replacement.camp_weeks = 0 if short_notice else max(1, self.event_week.get() - self.week if hasattr(self, "event_week") else 1)
        replacement.camp_boost = 0 if short_notice else min(3, replacement.professionalism // 30)
        replacement.morale = min(100, replacement.morale + (4 if short_notice else 7))
        replacement.media_heat = min(100, replacement.media_heat + (6 if short_notice else 3))
        self.roster.append(replacement)
        self.event_log.insert(0, f"TBA filled by {replacement.name} ({source}) at ${replacement.purse:,} for one fight.")
        return replacement

    def finish_event(self, event, package):
        self.cash += package["profit"]
        self.company_pop = package["projected_pop"]
        self.company_stability = package["projected_stability"]
        self.finance["last_event"] = package["finance"]
        self.finance["ledger"].insert(0, f"Month {self.month}: {package['event_name']} profit ${package['profit']:,}")

        award_pool = package.get("award_pool", [])
        clause_payout = 0
        finance = package.get("finance", {})
        ppv_pool = finance.get("ticket_revenue", 0) + finance.get("broadcast_income", 0)
        for index, (winner, loser, fight, method) in enumerate(package["results"]):
            if method == "Draw":
                self.apply_draw_result(winner, loser, fight)
            else:
                self.apply_result(winner, loser, fight, method)
                excitement = award_pool[index].get("excitement", 50) if index < len(award_pool) else 50
                round_no = award_pool[index].get("round", 1) if index < len(award_pool) else 1
                self.record_season_result(winner, loser, method, round_no, fight, excitement, self.player_company_name)
                if winner in self.roster and getattr(winner, "win_bonus", 0):
                    clause_payout += winner.win_bonus
            # PPV points are owed to booked fighters win or lose.
            for fighter in (winner, loser):
                if fighter in self.roster and getattr(fighter, "ppv_points", 0):
                    clause_payout += round(ppv_pool * fighter.ppv_points / 100)
        if clause_payout:
            self.cash -= clause_payout
            self.finance["ledger"].insert(0, f"Month {self.month}: Contract clause payouts (win bonuses + PPV points) ${clause_payout:,}.")
        self.record_finance_transaction(
            package["event_name"], revenue=finance.get("total_revenue", 0),
            costs=finance.get("total_expense", 0) + clause_payout,
        )
        for winner, loser, fight, _method in package["results"]:
            for fighter, opponent in ((winner, loser), (loser, winner)):
                if fighter not in self.roster:
                    continue
                fulfilled = []
                if fighter.main_event_promise and fight.get("main"):
                    fighter.main_event_promise = False
                    fulfilled.append("main-event")
                opponent_rank = self.division_rank_number(opponent)
                if fighter.top_opponent_promise and (opponent.champion or (opponent_rank and opponent_rank <= 10)):
                    fighter.top_opponent_promise = False
                    fulfilled.append("top-opponent")
                if fulfilled:
                    fighter.promise_deadline_month = 0 if not fighter.main_event_promise and not fighter.top_opponent_promise else fighter.promise_deadline_month
                    fighter.relationship_trust = min(100, fighter.relationship_trust + 12)
                    fighter.morale = min(100, fighter.morale + 5)
                    self.news.insert(0, f"Promise kept: {fighter.name}'s {' and '.join(fulfilled)} commitment was fulfilled.")

        if event and event in self.scheduled_events:
            self.scheduled_events.remove(event)
        self.apply_event_awards(package.get("awards", []))
        self.apply_regional_show_effects(package)
        # apply_result/apply_draw_result deliberately deferred these removals so
        # every event subsystem could still resolve the participants safely.
        for winner, loser, _fight, _method in package["results"]:
            self.retire_after_final_fight_if_due(winner, self.player_company_name)
            self.retire_after_final_fight_if_due(loser, self.player_company_name)
        self.result_history.insert(0, package["summary"])
        self.result_records.insert(0, {
            "date": f"Month {self.month} Week {self.week}",
            "company": self.player_company_name,
            "event": package["event_name"],
            "summary": package["summary"],
            "fights": package["fight_count"],
            "gate": f"${package['finance'].get('ticket_revenue', 0):,}",
            "profit": f"${package['profit']:,}",
            "log": package.get("log", []),
            "fight_logs": package.get("fight_logs", []),
            "finance": package.get("finance", {}),
        })
        self.result_records = self.result_records[:500]
        self.evaluate_promotion_achievements(self.player_company_name, package)
        self.refresh_historical_records()
        self.refresh_promotion_rankings()
        self.update_player_fanbase(package)
        region = package.get("region", self.venue_region(package["venue"]))
        if region in self.regions:
            self.regions[region]["last_major_show"] = package["summary"]
        self.event_log = package["log"] + [""] + self.event_log
        self.news.insert(0, f"{package['fight_count']}-fight show completed; {self.player_company_name} banked ${package['profit']:,}.")
        main = next((row for row in package.get("fight_logs", []) if "MAIN" in str(row.get("label", "")).upper()), None)
        headline = f"{self.player_company_name} completes {package['event_name']}."
        detail = main.get("result", "") if main else package["summary"]
        self.record_world_story("Event", headline, f"{detail} Profit: ${package['profit']:,}.", [self.player_company_name], importance=3)
        self.refresh_all()
        self.write_log()
        self.show_event_summary(package)

    def apply_regional_show_effects(self, package):
        region = package.get("region", self.player_region)
        city = package.get("city", "")
        data = self.regions.get(region, {})
        morale_bonus = data.get("promo_benefit", {}).get("morale", 1)
        for winner, loser, fight, method in package["results"]:
            for name in fight.get("fighters", []):
                # Prefer the exact objects stored in the result.  The fallback
                # also supports old result packages and already-retired fighters.
                fighter = winner if winner.name == name else loser if loser.name == name else self.find_fighter_anywhere(name)
                if not fighter:
                    continue
                connection = self.fighter_event_connection(fighter, region, city)
                if connection["strength"] <= 0:
                    continue
                is_winner = fighter is winner
                hometown_bonus = 2 if connection["level"] == "Hometown" else 1 if connection["strength"] >= 0.66 else 0
                fighter.morale = min(100, fighter.morale + max(1, round(morale_bonus * connection["strength"])) + hometown_bonus)
                fighter.motivation = min(99, fighter.motivation + 1 + hometown_bonus)
                market_delta = (3 if is_winner else 1) + hometown_bonus + (1 if method not in ("Decision", "Draw") and is_winner else 0)
                self.update_regional_popularity(fighter, region, market_delta, f"{connection['level']} appearance at {package.get('event_name', 'an event')}")
                if is_winner:
                    fighter.popularity = min(100, fighter.popularity + 1 + hometown_bonus)
                    fighter.media_heat = min(100, fighter.media_heat + 1 + hometown_bonus)

    def choose_event_awards(self, award_pool):
        if not award_pool:
            return []
        awards = []
        fight = max(award_pool, key=lambda row: row["excitement"])
        awards.append({"award": "Fight of the Night", "fighters": fight.get("fighters", [fight["winner"], fight["loser"]]), "note": fight["fight"], "bonus": self.post_show_bonuses["fight"]})
        kos = [row for row in award_pool if "KO" in row["method"] or "TKO" in row["method"]]
        subs = [row for row in award_pool if "Submission" in row["method"]]
        if kos:
            row = max(kos, key=lambda item: item["excitement"])
            awards.append({"award": "KO of the Night", "fighters": [row["winner"]], "note": row["method"], "bonus": self.post_show_bonuses["ko"]})
        if subs:
            row = max(subs, key=lambda item: item["excitement"])
            awards.append({"award": "Submission of the Night", "fighters": [row["winner"]], "note": row["method"], "bonus": self.post_show_bonuses["sub"]})
        return awards

    def apply_event_awards(self, awards):
        for award in awards:
            for name in award["fighters"]:
                fighter = self.find_fighter_anywhere(name)
                if not fighter:
                    continue
                fighter.morale = min(100, fighter.morale + 8)
                fighter.popularity = min(100, fighter.popularity + 1)
                self.finance["ledger"].insert(0, f"Month {self.month}: {fighter.name} earned {award['award']} bonus ${award['bonus']:,}.")

    def show_event_summary(self, package):
        if self.root.state() == "withdrawn":
            return
        window = tk.Toplevel(self.root)
        window.title("End of Event")
        window.geometry("560x430")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="END OF EVENT", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        canvas = tk.Canvas(window, bg=self.colors["cream"], highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=8, pady=8)
        canvas.create_text(24, 24, anchor="nw", fill=self.colors["text"], font=("Impact", 18), text=package["event_name"])
        canvas.create_text(24, 62, anchor="nw", fill=self.colors["text"], font=("Tahoma", 10, "bold"), text=f"Profit ${package['profit']:,} | Gate ${package['gate']:,} | Popularity {package['projected_pop']} | Stability {package['projected_stability']}")
        atmosphere = package.get("finance", {}).get("atmosphere", {})
        canvas.create_text(24, 84, anchor="nw", fill=self.colors["gold"], font=("Tahoma", 10, "bold"), text=f"Crowd: {atmosphere.get('mood', 'Engaged')} {atmosphere.get('intensity', 50)}/100 — {atmosphere.get('preference', 'Competitive fights')}")
        y = 128
        canvas.create_text(24, y, anchor="nw", fill=self.colors["gold"], font=("Impact", 14), text="BONUSES")
        y += 34
        if package.get("awards"):
            for award in package["awards"]:
                canvas.create_text(34, y, anchor="nw", fill=self.colors["text"], font=("Tahoma", 10, "bold"), text=f"{award['award']}: {', '.join(award['fighters'])}")
                y += 22
                canvas.create_text(52, y, anchor="nw", fill=self.colors["muted"], font=("Tahoma", 9), text=f"{award['note']} | ${award['bonus']:,} | morale +8")
                y += 30
        else:
            canvas.create_text(34, y, anchor="nw", fill=self.colors["muted"], font=("Tahoma", 10), text="No bonuses awarded.")
        ttk.Button(window, text="Close", command=window.destroy).pack(anchor="e", padx=8, pady=(0, 8))
