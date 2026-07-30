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


class EventMixin:
    def event_fight_participants(self, fight):
        """Return every booked athlete, including a tournament's complete field."""
        return list(fight.get("tournament_entrants", fight.get("fighters", [])))

    def schedule_event(self):
        if len(self.booked) < 1:
            self.set_schedule_status("SCHEDULING BLOCKED: Book at least one fight before scheduling the show.", "error")
            messagebox.showinfo("No fights", "Book at least one fight before scheduling a show.")
            return
        names = [name for fight in self.booked for name in self.event_fight_participants(fight) if name != "TBA"]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            self.set_schedule_status("SCHEDULING BLOCKED: A fighter appears more than once on this card.", "error")
            messagebox.showwarning("Double booking", f"{', '.join(duplicates)} is booked in more than one fight on this card. A fighter can only appear once per event.")
            return
        if self.fighter_busy_message(names):
            self.refresh_available()
            return
        target_date = self.selected_booking_date(reject_past=True)
        if target_date is None:
            return
        month, week = target_date
        unavailable = []
        for name in names:
            fighter = self.get_fighter(name)
            if not self.fighter_available_for_date(fighter, month, week, self.selected_booking_day()):
                unavailable.append(f"{fighter.name} ({self.fighter_return_label(fighter)})")
        if unavailable:
            earliest_month, earliest_week, earliest_day = self.earliest_booked_card_day()
            target_label = self.format_game_date(month, week, day=self.selected_booking_day())
            earliest_label = self.format_game_date(earliest_month, earliest_week, day=earliest_day)
            sample = ", ".join(unavailable[:4])
            remainder = f" and {len(unavailable) - 4} more" if len(unavailable) > 4 else ""
            message = (
                f"SCHEDULING BLOCKED: {len(unavailable)} booked fighter{'s are' if len(unavailable) != 1 else ' is'} "
                f"unavailable on {target_label}. Earliest complete-card date: {earliest_label}. "
                f"{sample}{remainder}. Use Earliest Valid Date or edit the card."
            )
            self.set_schedule_status(message, "error")
            self.set_matchmaking_notice(message)
            self.refresh_available()
            return
        self.normalize_card_order()
        super_project = getattr(self, "super_event_project", None)
        if super_project:
            if month < int(super_project.get("earliest_month", month)) or month > int(super_project.get("deadline_month", month)):
                message = f"This project must be scheduled between {self.format_game_date(super_project.get('earliest_month', month), 1)} and {self.format_game_date(super_project.get('deadline_month', month), 4)}."
                self.set_schedule_status("SCHEDULING BLOCKED: " + message, "error")
                messagebox.showwarning("Super-event date", message)
                return
            missing = self.validate_super_event_card(super_project, self.booked)
            if missing:
                message = "Super-event card approval still requires: " + ", ".join(missing) + "."
                self.set_schedule_status("SCHEDULING BLOCKED: " + message, "error")
                messagebox.showwarning("Super-event card approval", message)
                return
        event_number = self.next_player_event_number()
        current_name = self.event_name.get().strip()
        auto_named = self.is_auto_event_name(current_name)
        event_name = self.default_event_name(event_number) if auto_named else current_name
        scheduled_fights = []
        for booked_fight in self.booked:
            snapshot = dict(booked_fight)
            snapshot["fighter_ids"] = [
                getattr(self.get_fighter(reference), "fighter_id", "") if reference != "TBA" else ""
                for reference in self.event_fight_participants(snapshot)
            ]
            scheduled_fights.append(snapshot)
        event = {
            "name": event_name,
            "auto_named": auto_named,
            "venue": self.venue.get(),
            "region": self.event_region.get(),
            "city": self.event_city.get(),
            "month": month,
            "week": week,
            "day": self.selected_booking_day(),
            "broadcaster": self.event_broadcaster.get(),
            "fights": scheduled_fights,
        }
        if super_project:
            project = dict(super_project)
            project["status"] = "Scheduled"
            project["scheduled_month"] = month
            event["super_event"] = project
            self.super_event_project = None
            for offer in self.super_event_offers:
                if offer.get("id") == project.get("id"):
                    offer.update(project)
        self.scheduled_events.append(event)
        self.assign_event_camps(event)
        prefix = "SUPER EVENT SCHEDULED: " if event.get("super_event") else ""
        self.news.insert(0, f"{prefix}{event['name']} has been scheduled for {self.event_date_label(event)} at {event['venue']}.")
        self.set_schedule_status(f"SCHEDULED: {event['name']} | {self.event_date_label(event)} | {len(event['fights'])} fights.", "success")
        self.booked.clear()
        self.event_name.set(self.default_event_name())
        self.set_booking_date(month if week < 4 else month + 1, week + 1 if week < 4 else 1)
        self.event_broadcaster.set(self.broadcasters[0]["name"] if self.broadcasters else "No Coverage")
        if hasattr(self, "event_venue_box"):
            self.event_venue_box.configure(values=self.available_event_venues())
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
                participants = self.event_fight_participants(fight)
                for index, name in enumerate(participants):
                    if name == "TBA":
                        continue
                    if name in seen or name in event_names:
                        if fight.get("tournament"):
                            fight.setdefault("tournament_entrants", participants)[index] = "TBA"
                            fight["fighters"] = list(fight["tournament_entrants"][:1] + fight["tournament_entrants"][-1:])
                        else:
                            fight.setdefault("fighters", participants)[index] = "TBA"
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

    def event_camp_days(self, event):
        """Days from now until a card runs, which is the real length of its camp."""
        days = self.calendar_day_index(
            event.get("month", self.month), event.get("week", 1), self.event_day(event)
        ) - self.current_day_index()
        return max(1, days)

    def assign_event_camps(self, event):
        # Camp is measured in days, so a card booked on the Saturday of a week
        # is nearly a full extra week of preparation over the same card on the
        # Monday. The fractional length drives the boost; camp_weeks stays a
        # whole number because it is a display value.
        camp_days = self.event_camp_days(event)
        camp_length_weeks = camp_days / DAYS_PER_WEEK
        weeks_out = max(1, round(camp_length_weeks))
        for fight in event["fights"]:
            for name in self.event_fight_participants(fight):
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
                attention = self.gym_attention_multiplier(gym)
                base_boost = round(camp_length_weeks * (quality + specialty + focus_bonus + intensity_bonus) / 112 * (0.55 + professionalism * 0.3 + motivation * 0.25) / 2.8 * attention)
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
        sport = self.combat_sport_for_fighter(fighter) if hasattr(self, "combat_sport_for_fighter") else ""
        if sport:
            stage = self.combat_sport_development_stage(fighter, sport)
            if stage not in ("Pre-prime", "Prime") or (stage == "Prime" and random.random() > 0.48):
                return
            native_keys = set(self.combat_sport_development_profile(sport)["growth"])
            compatible = tuple(key for key in keys if key in native_keys)
            if not compatible:
                return
            keys = compatible
        key = random.choice(keys)
        if sport:
            if not self.adjust_combat_sport_training_key(fighter, sport, key, 1, f"{fighter.camp_focus} camp focus"):
                return
        else:
            if not self.improve_detailed_skill(fighter, key, 1):
                return
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

    def selected_scheduled_event_for_edit(self):
        """Resolve the exact future event selected in the upcoming-events list."""
        if not hasattr(self, "upcoming_tree"):
            return None
        selected = self.upcoming_tree.selection()
        if not selected:
            messagebox.showinfo("Edit booked card", "Select an upcoming event first.")
            return None
        shows = self.sorted_scheduled_events()
        try:
            return shows[int(selected[0])]
        except (IndexError, TypeError, ValueError):
            messagebox.showinfo("Edit booked card", "The selected event could not be found. Refresh the list and try again.")
            return None

    def edit_selected_scheduled_event(self):
        event = self.selected_scheduled_event_for_edit()
        if not event:
            return
        if self.is_event_due(event):
            messagebox.showinfo("Fight day", "This event is due now. Watch or simulate it before making any further card changes.")
            return
        self.open_scheduled_card_editor(event)

    def reset_cancel_card_confirmation(self, _event=None):
        self._cancel_card_confirmation = None
        if hasattr(self, "cancel_card_button"):
            self.cancel_card_button.config(text="Cancel Selected Card")

    def cancel_selected_scheduled_event(self):
        """Two-step inline cancellation for a player-scheduled event."""
        selected = self.upcoming_tree.selection() if hasattr(self, "upcoming_tree") else ()
        if not selected:
            self.set_matchmaking_notice("Select an upcoming card before cancelling it.")
            return
        shows = self.sorted_scheduled_events()
        try:
            event = shows[int(selected[0])]
        except (IndexError, TypeError, ValueError):
            self.set_matchmaking_notice("That scheduled card could not be found. Refresh and try again.")
            return
        token = id(event)
        if getattr(self, "_cancel_card_confirmation", None) != token:
            self._cancel_card_confirmation = token
            if hasattr(self, "cancel_card_button"):
                self.cancel_card_button.config(text="Confirm Cancel Card")
            self.set_matchmaking_notice(
                f"Cancel {event.get('name', 'this card')}? Click Confirm Cancel Card to remove the entire event."
            )
            return
        cancelled_names = {
            name for fight in event.get("fights", [])
            for name in self.event_fight_participants(fight) if name != "TBA"
        }
        self.scheduled_events.remove(event)
        still_booked = {
            name for other in self.scheduled_events for fight in other.get("fights", [])
            for name in self.event_fight_participants(fight) if name != "TBA"
        }
        for name in cancelled_names - still_booked:
            fighter = self.get_fighter(name)
            if fighter:
                fighter.camp_weeks = 0
                fighter.camp_boost = 0
        note = f"{event.get('name', 'Scheduled event')} was cancelled by the promoter."
        self.news.insert(0, note)
        self.inbox.append({"subject": "Event Cancelled", "body": note, "type": "Business", "resolved": True, "seen": True})
        self.record_change("Schedule", event.get("name", "Event"), "Cancelled", "Promoter cancelled the scheduled card", 2)
        self.reset_cancel_card_confirmation()
        self.set_matchmaking_notice(note)
        self.refresh_all()

    def set_schedule_status(self, message, level="info"):
        if hasattr(self, "schedule_status_var"):
            self.schedule_status_var.set(str(message))
        label = getattr(self, "schedule_status", None)
        if label:
            palette = {
                "error": ("#4a1717", "#ffb4a2"),
                "success": ("#173d29", "#b7f7ce"),
                "info": ("#252525", self.colors.get("text", "#ffffff")),
            }
            background, foreground = palette.get(level, palette["info"])
            label.configure(bg=background, fg=foreground)

    def earliest_booked_card_day(self):
        """First date every booked participant is out of recovery, to the day.

        Recovery now ends on a weekday, so the earliest legal card can sit part
        way through a week. Returning only the week would offer a date that the
        scheduler then rejects because the chosen day falls before a fighter's
        return.
        """
        earliest = self.current_day_index()
        for fight in getattr(self, "booked", []):
            for name in self.event_fight_participants(fight):
                if name == "TBA":
                    continue
                fighter = self.get_fighter(name)
                earliest = max(earliest, self.fighter_available_day_index(fighter))
        return self.day_index_parts(earliest)

    def earliest_booked_card_date(self):
        """Return the first week where every booked participant is out of recovery."""
        month, week, _day = self.earliest_booked_card_day()
        return month, week

    def move_booking_to_earliest_card_date(self):
        if not self.booked:
            self.set_schedule_status("Book at least one fight before calculating the earliest valid date.", "error")
            return
        injured = []
        for fight in self.booked:
            for name in self.event_fight_participants(fight):
                if name != "TBA" and self.get_fighter(name).injured:
                    injured.append(name)
        if injured:
            self.set_schedule_status(
                "DATE NOT CHANGED: Injured fighters must recover or be removed first: " + ", ".join(sorted(set(injured))),
                "error",
            )
            return
        month, week, day = self.earliest_booked_card_day()
        # Keep the player's chosen weekday when it is already late enough in
        # the week; only move it forward when recovery demands it.
        day = max(day, self.selected_booking_day())
        self.set_booking_date(month, week, day)
        self.refresh_available()
        self.set_schedule_status(
            f"DATE UPDATED: The full card can be scheduled from {self.format_game_date(month, week, day=day)}.",
            "success",
        )

    def open_scheduled_card_editor(self, event):
        """Edit a future card directly without sending it back through the new-show form."""
        window = tk.Toplevel(self.root)
        window.title(f"Edit Card - {event.get('name', 'Upcoming Event')}")
        window.geometry("1120x680")
        window.minsize(900, 540)
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="EDIT BOOKED CARD", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        header_info = ttk.Label(header, text=f"{event.get('name', 'Event')} | {self.event_date_label(event)} | {event.get('venue', '')}", style="Panel.TLabel")
        header_info.pack(side="right", padx=10)

        name_bar = ttk.Frame(window, style="Inset.TFrame")
        name_bar.pack(fill="x", padx=8, pady=(6, 0))
        event_name_var = tk.StringVar(value=event.get("name", ""))
        ttk.Label(name_bar, text="Event Name", style="Inset.TLabel").pack(side="left", padx=(8, 4), pady=5)
        event_name_entry = ttk.Entry(name_bar, textvariable=event_name_var)
        event_name_entry.pack(side="left", fill="x", expand=True, padx=4, pady=5)

        def update_header():
            header_info.config(text=f"{event.get('name', 'Event')} | {self.event_date_label(event)} | {event.get('venue', '')}")
            window.title(f"Edit Card - {event.get('name', 'Upcoming Event')}")

        def apply_manual_event_name():
            name = event_name_var.get().strip()
            if not name:
                return
            event["name"] = name
            event["auto_named"] = False
            update_header()
            self.refresh_upcoming()

        def apply_auto_event_name():
            number = self.event_name_number(event.get("name")) or self.next_player_event_number()
            event["auto_named"] = True
            event["name"] = self.default_event_name(number, event.get("fights", []))
            event_name_var.set(event["name"])
            update_header()
            self.refresh_upcoming()

        ttk.Button(name_bar, text="Apply Name", command=apply_manual_event_name).pack(side="left", padx=3, pady=5)
        ttk.Button(name_bar, text="Use Auto Name", style="Accent.TButton", command=apply_auto_event_name).pack(side="left", padx=(3, 8), pady=5)

        body = ttk.Panedwindow(window, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        available_panel, available = self.section(body, "ADD ELIGIBLE FIGHTERS")
        card_panel, card = self.section(body, "CURRENT BOOKED CARD")
        body.add(available_panel, weight=1)
        body.add(card_panel, weight=1)

        filters = ttk.Frame(available, style="Inset.TFrame")
        filters.pack(fill="x", padx=6, pady=(6, 2))
        weight_var = tk.StringVar(value="All")
        gender_var = tk.StringVar(value="All")
        title_var = tk.BooleanVar(value=False)
        tier_var = tk.StringVar(value="Main Card")
        ttk.Label(filters, text="Weight", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        weight_box = ttk.Combobox(filters, values=["All"] + self.active_player_division_weights("All"), textvariable=weight_var, state="readonly", width=14)
        weight_box.pack(side="left", padx=(0, 7))
        ttk.Label(filters, text="Gender", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        gender_box = ttk.Combobox(filters, values=["All", "Male", "Female"], textvariable=gender_var, state="readonly", width=8)
        gender_box.pack(side="left", padx=(0, 5))

        def sync_editor_divisions(*_args):
            """Only offer weight classes this promotion actually operates."""
            options = ["All"] + self.active_player_division_weights(gender_var.get())
            weight_box.configure(values=options)
            if weight_var.get() not in options:
                weight_var.set("All")

        legend = tk.Frame(available, bg=self.colors["panel_dark"])
        legend.pack(fill="x", padx=6, pady=(2, 0))
        for swatch_color, swatch_text in (("#7fd694", "winning record"), ("#e8837a", "losing record"), ("#9298a1", "unavailable this date")):
            tk.Label(legend, text="■", bg=self.colors["panel_dark"], fg=swatch_color, font=("Tahoma", 9)).pack(side="left", padx=(6, 1))
            tk.Label(legend, text=swatch_text, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left")

        history_var = tk.StringVar(value="Select one fighter to compare prior meetings.")
        history_label = ttk.Label(available, textvariable=history_var, style="Inset.TLabel", anchor="w")
        history_label.pack(fill="x", padx=6, pady=(2, 0))

        available_tree = ttk.Treeview(available, columns=("name", "gender", "weight", "rank", "titlepath", "record", "age", "overall", "elo", "pop", "build", "last", "form", "trend", "activity", "fatigue", "recovery", "fit", "history", "status"), show="headings", selectmode="extended", height=18)
        for key, label, size in (("name", "Name", 148), ("gender", "G", 34), ("weight", "Class", 90), ("rank", "Rank", 44), ("titlepath", "Title Path", 104), ("record", "Record", 66), ("age", "Age", 40), ("overall", "OVR", 44), ("elo", "ELO", 54), ("pop", "Pop", 42), ("build", "Build", 48), ("last", "Last Fight", 84), ("form", "Last 5 (→latest)", 82), ("trend", "Form", 56), ("activity", "Active", 50), ("fatigue", "Fatigue", 88), ("recovery", "Medical Return", 104), ("fit", "Match Fit", 66), ("history", "History", 74), ("status", "Event Availability", 132)):
            available_tree.heading(key, text=label)
            available_tree.column(key, width=size, anchor="center")
        available_tree.column("name", anchor="w")
        available_tree.column("titlepath", anchor="w")
        available_tree.tag_configure("not_ready", foreground="#9298a1")
        available_tree.tag_configure("rec_win", foreground="#7fd694")
        available_tree.tag_configure("rec_loss", foreground="#e8837a")
        self.make_tree_sortable(available_tree)
        self.attach_tree_heading_tooltips(available_tree, {
            "rank": "Divisional rank. C = champion, #n = ranked contender, - = unranked.",
            "titlepath": "Where this fighter sits on the road to a belt (champion, owed a title shot, #1 or top-five contender, or building merit).",
            "record": "Career wins-losses-draws. Row colour: green = winning record, red = losing record, grey = unavailable on this date.",
            "overall": "Overall ability (OVR). A large OVR gap usually means a lopsided mismatch.",
            "elo": "Rating earned from actual results. Close ELOs make the most competitive bout.",
            "pop": "Fighter popularity. Popular names high on the card lift the gate, hype, and media rating.",
            "build": "Match build - how compelling this fighter is to book right now.",
            "last": "Date of their last fight.",
            "form": "Wins-losses over the last five bouts, oldest to newest (latest result last).",
            "trend": "Momentum read from the rankings: a win streak, rising, sliding, or steady.",
            "activity": "How recently they competed. Long layoffs risk ring rust; too-frequent bouts risk fatigue.",
            "fatigue": "Current fatigue, 0-100. 0-19 Fresh; 20-39 Manageable; 40-54 Elevated; 55-64 Tired; 65+ Unfit and cannot be booked.",
            "recovery": "Earliest medical return date after the previous bout or injury. This is separate from accumulated fatigue.",
            "fit": "Match fitness vs the selected anchor: fatigue, injury, and camp readiness.",
            "history": "Prior meetings with the other selected fighter.",
            "status": "Whether this fighter can be booked on this event's date.",
        })
        available_scroll = ttk.Scrollbar(available, orient="vertical", command=available_tree.yview)
        available_scroll_x = ttk.Scrollbar(available, orient="horizontal", command=available_tree.xview)
        available_tree.configure(yscrollcommand=available_scroll.set, xscrollcommand=available_scroll_x.set)
        available_scroll_x.pack(side="bottom", fill="x")
        available_scroll.pack(side="right", fill="y", pady=5)
        available_tree.pack(fill="both", expand=True, padx=6, pady=5)

        add_controls = ttk.Frame(available, style="Inset.TFrame")
        add_controls.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(add_controls, text="Add Bout", style="Accent.TButton", command=lambda: add_fight(False)).pack(side="left", padx=3, pady=4)
        ttk.Button(add_controls, text="Add TBA", command=lambda: add_fight(True)).pack(side="left", padx=3, pady=4)
        ttk.Checkbutton(add_controls, text="Title", variable=title_var).pack(side="left", padx=(10, 3))
        ttk.Label(add_controls, text="Tier", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        ttk.Combobox(add_controls, values=CARD_TIERS, textvariable=tier_var, state="readonly", width=12).pack(side="left", padx=(0, 3))

        card_tree = ttk.Treeview(card, columns=("slot", "fight", "tier", "title", "weight", "build", "fatigue", "recovery"), show="headings", height=18)
        for key, label, size in (("slot", "Slot", 90), ("fight", "Fight", 240), ("tier", "Tier", 92), ("title", "Stakes", 92), ("weight", "Class", 100), ("build", "Build", 52), ("fatigue", "Fatigue A/B", 92), ("recovery", "Medical Return A/B", 150)):
            card_tree.heading(key, text=label)
            card_tree.column(key, width=size, anchor="center")
        card_tree.column("fight", anchor="w")
        self.attach_tree_heading_tooltips(card_tree, {
            "fatigue": "Current fatigue for each fighter in the same order as the matchup. 65 or higher is unfit.",
            "recovery": "Earliest medical return for each fighter in matchup order. Now means medically cleared today.",
        })
        card_tree.pack(fill="both", expand=True, padx=6, pady=5)

        card_controls = ttk.Frame(card, style="Inset.TFrame")
        card_controls.pack(fill="x", padx=6, pady=(0, 6))

        def normalize_event_order():
            self.normalize_card_order(event.get("fights", []))
            self.refresh_scheduled_event_auto_name(event)
            event_name_var.set(event.get("name", ""))
            update_header()

        def current_names():
            return {
                name for fight in event.get("fights", [])
                for name in self.event_fight_participants(fight) if name != "TBA"
            }

        def other_booked_names():
            return {
                name for other in self.scheduled_events if other is not event
                for fight in other.get("fights", [])
                for name in self.event_fight_participants(fight) if name != "TBA"
            }

        def refresh_available_editor(*_args):
            available_tree.delete(*available_tree.get_children())
            booked_here = current_names()
            booked_elsewhere = other_booked_names()
            division_ranks = self.player_division_rank_map()
            closed = set(getattr(self, "closed_divisions", set()))
            for fighter in sorted(self.roster, key=lambda item: (item.weight, item.gender, -item.overall, item.name)):
                if fighter.name in booked_here or fighter.name in booked_elsewhere:
                    continue
                # Never offer fighters from a division the promotion has closed.
                if self.belt_key(fighter.gender, fighter.weight) in closed:
                    continue
                if weight_var.get() != "All" and fighter.weight != weight_var.get():
                    continue
                if gender_var.get() != "All" and fighter.gender != gender_var.get():
                    continue
                rank = division_ranks.get(self.fighter_identity_key(fighter))
                rank_label = "C" if fighter.champion else f"#{rank}" if rank else "-"
                status = self.fighter_booking_status(fighter, event["month"], event.get("week", 1))
                available_tree.insert(
                    "", "end", iid=fighter.fighter_id, tags=self.available_row_tags(fighter, status),
                    values=(
                        fighter.name, fighter.gender[0], fighter.weight, rank_label,
                        self.matchmaking_title_path_label(fighter), fighter.record, fighter.age,
                        fighter.overall, fighter.elo_rating, fighter.popularity,
                        self.fight_build_score(fighter, rank=rank), self.fighter_last_fight_date_label(fighter),
                        self.world_fighter_last_five(fighter), self.matchmaking_form_label(fighter),
                        self.fighter_activity_rating(fighter), self.fighter_fatigue_label(fighter),
                        self.fighter_recovery_date_label(fighter), "-", "-", status,
                    ),
                )
            refresh_history_editor()

        def refresh_history_editor(_event=None):
            selected_ids = list(available_tree.selection())
            fighters = [next((item for item in self.roster if item.fighter_id == fighter_id), None) for fighter_id in selected_ids]
            fighters = [fighter for fighter in fighters if fighter]
            for row_id in available_tree.get_children():
                available_tree.set(row_id, "history", "-")
                available_tree.set(row_id, "fit", "-")
            if not fighters:
                history_var.set("Select one fighter to compare prior meetings.")
                return
            if len(fighters) == 1:
                anchor = fighters[0]
                for row_id in available_tree.get_children():
                    opponent = next((item for item in self.roster if item.fighter_id == row_id), None)
                    available_tree.set(row_id, "history", self.matchup_history_indicator(anchor, opponent))
                    fit = self.matchmaking_fit_score(anchor, opponent)
                    if fit is not None:
                        available_tree.set(row_id, "fit", str(fit))
                history_var.set(f"OPPONENT CHECK: comparing every fighter with {anchor.name}.")
                return
            a, b = fighters[:2]
            meetings, latest_month = self.matchup_history_summary(a, b)
            indicator = self.matchup_history_indicator(a, b)
            fit = self.matchmaking_fit_score(a, b)
            for row_id in selected_ids[:2]:
                available_tree.set(row_id, "history", indicator)
                available_tree.set(row_id, "fit", str(fit or "-"))
            if meetings:
                last_met = f"; last met {self.format_game_date(latest_month, 1)}" if latest_month else ""
                history_var.set(f"REMATCH: {a.name} and {b.name} have {meetings} prior meeting{'s' if meetings != 1 else ''}{last_met}.")
            else:
                history_var.set(f"FIRST MEETING: {a.name} vs {b.name}.")

        def refresh_card_editor(select_index=None):
            normalize_event_order()
            card_tree.delete(*card_tree.get_children())
            tier_counts = {}
            for index, fight in enumerate(event.get("fights", [])):
                names = fight.get("fighters", [])
                matchup = " vs ".join(names) if names else "Tournament"
                named = [self.get_fighter(name) for name in names if name != "TBA"]
                build = round(self.match_build_score(*named, fight)) if len(named) == 2 else "-"
                # Make the segment of the card explicit, not just a running number.
                tier_name = fight.get("tier", "Main Card")
                tier_counts[tier_name] = tier_counts.get(tier_name, 0) + 1
                slot = "MAIN EVENT" if fight.get("main") else f"{tier_name} {tier_counts[tier_name]}"
                stake_parts = []
                if fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")):
                    stake_parts.append("Interim Title" if fight.get("interim") else "Divisional Title")
                if fight.get("special_belt"):
                    stake_parts.append(f"{fight['special_belt']} Title")
                stakes = " + ".join(stake_parts) or "-"
                weight = named[0].weight if named else fight.get("tba_weight", "-")
                fatigue = " / ".join(str(fighter.fatigue) for fighter in named) or "-"
                recovery = " / ".join(self.fighter_recovery_date_label(fighter) for fighter in named) or "-"
                card_tree.insert("", "end", iid=str(index), values=(slot, matchup, fight.get("tier", "Main Card"), stakes, weight, build, fatigue, recovery))
            if select_index is not None and str(select_index) in card_tree.get_children():
                card_tree.selection_set(str(select_index))
                card_tree.focus(str(select_index))
            refresh_available_editor()
            self.refresh_upcoming()

        def selected_card_index():
            selected = card_tree.selection()
            return int(selected[0]) if selected else None

        def add_fight(tba=False):
            selected = available_tree.selection()
            needed = 1 if tba else 2
            if len(selected) != needed:
                messagebox.showinfo("Book fight", f"Select exactly {needed} eligible fighter{'s' if needed > 1 else ''}.", parent=window)
                return
            fighters = [next((fighter for fighter in self.roster if fighter.fighter_id == fighter_id), None) for fighter_id in selected]
            if any(fighter is None for fighter in fighters):
                return
            unavailable = [
                fighter for fighter in fighters
                if self.fighter_booking_status(fighter, event["month"], event.get("week", 1)) != "Ready"
            ]
            if unavailable:
                details = ", ".join(
                    f"{fighter.name}: {self.fighter_booking_status(fighter, event['month'], event.get('week', 1))}"
                    for fighter in unavailable
                )
                messagebox.showwarning("Fighter unavailable", details, parent=window)
                return
            if not tba and (fighters[0].gender != fighters[1].gender or fighters[0].weight != fighters[1].weight):
                messagebox.showwarning("Division mismatch", "Booked opponents must share a gender and weight class.", parent=window)
                return
            names = [fighters[0].name, "TBA"] if tba else [fighter.name for fighter in fighters]
            title = bool(title_var.get())
            interim = self.divisional_title_is_interim(fighters, title)
            fight = {
                "fighters": names,
                "title": title,
                "divisional_title": title,
                "interim": interim,
                "main": not event.get("fights"),
                "tier": tier_var.get(),
            }
            if tba:
                fight.update({"tba_weight": fighters[0].weight, "tba_gender": fighters[0].gender})
            event.setdefault("fights", []).append(fight)
            # Only the newly added athletes receive a new camp assignment.
            self.assign_event_camps({"month": event["month"], "week": event.get("week", 1), "fights": [fight]})
            refresh_card_editor(len(event["fights"]) - 1)

        def remove_selected():
            index = selected_card_index()
            if index is None:
                return
            event["fights"].pop(index)
            refresh_card_editor(max(0, index - 1))

        def move_selected(delta):
            index = selected_card_index()
            target = None if index is None else index + delta
            if target is None or target < 0 or target >= len(event.get("fights", [])):
                return
            event["fights"][index], event["fights"][target] = event["fights"][target], event["fights"][index]
            refresh_card_editor(target)

        def toggle_selected_title():
            index = selected_card_index()
            if index is None:
                return
            fight = event["fights"][index]
            named = [self.get_fighter(name) for name in fight.get("fighters", []) if name != "TBA"]
            current_divisional = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            fight["divisional_title"] = not current_divisional
            fight["title"] = bool(fight["divisional_title"] or fight.get("special_belt"))
            fight["interim"] = self.divisional_title_is_interim(named, fight["divisional_title"])
            refresh_card_editor(index)

        def replace_selected_tba():
            index = selected_card_index()
            selected = available_tree.selection()
            if index is None or len(selected) != 1:
                messagebox.showinfo("Replace TBA", "Select the TBA fight, then select one eligible replacement fighter.", parent=window)
                return
            fight = event["fights"][index]
            if fight.get("tournament") or "TBA" not in fight.get("fighters", []):
                messagebox.showinfo("Replace TBA", "The selected booking does not have a replaceable TBA slot.", parent=window)
                return
            replacement = next((fighter for fighter in self.roster if fighter.fighter_id == selected[0]), None)
            if not replacement:
                return
            replacement_status = self.fighter_booking_status(replacement, event["month"], event.get("week", 1))
            if replacement_status != "Ready":
                messagebox.showwarning("Fighter unavailable", f"{replacement.name}: {replacement_status}", parent=window)
                return
            tba_weight = fight.get("tba_weight") or next((self.get_fighter(name).weight for name in fight.get("fighters", []) if name != "TBA" and self.get_fighter(name)), "")
            tba_gender = fight.get("tba_gender") or next((self.get_fighter(name).gender for name in fight.get("fighters", []) if name != "TBA" and self.get_fighter(name)), "")
            if replacement.weight != tba_weight or replacement.gender != tba_gender:
                messagebox.showwarning("Division mismatch", f"The replacement must be a {tba_gender} {tba_weight}.", parent=window)
                return
            fight["fighters"] = [replacement.name if name == "TBA" else name for name in fight["fighters"]]
            fight["tba_filled"] = True
            fight["tba_note"] = f"{replacement.name} was confirmed through the booked-card editor."
            named = [self.get_fighter(name) for name in fight["fighters"]]
            divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            fight["divisional_title"] = divisional_title
            fight["title"] = bool(divisional_title or fight.get("special_belt"))
            fight["interim"] = self.divisional_title_is_interim(named, divisional_title)
            # Camp only the incoming replacement; the original fighter's camp
            # has already been prepared for this scheduled event.
            self.assign_event_camps({"month": event["month"], "week": event.get("week", 1), "fights": [{"fighters": [replacement.name]}]})
            self.news.insert(0, f"{replacement.name} replaces TBA on {event.get('name', 'an upcoming event')}." )
            refresh_card_editor(index)

        def set_selected_tier():
            index = selected_card_index()
            if index is None:
                return
            event["fights"][index]["tier"] = tier_var.get()
            refresh_card_editor(index)

        ttk.Button(card_controls, text="Remove", command=remove_selected).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Replace TBA", style="Accent.TButton", command=replace_selected_tba).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Title / Interim", command=toggle_selected_title).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Move Up", command=lambda: move_selected(-1)).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Move Down", command=lambda: move_selected(1)).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Set Tier", command=set_selected_tier).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right", padx=3, pady=4)

        def show_selected_profile(_event=None):
            selected = available_tree.selection()
            if not selected:
                return
            fighter = next((item for item in self.roster if item.fighter_id == selected[0]), None)
            if fighter:
                self.open_fighter_profile_window(fighter)

        weight_box.bind("<<ComboboxSelected>>", refresh_available_editor)
        gender_box.bind("<<ComboboxSelected>>", lambda _event: (sync_editor_divisions(), refresh_available_editor()))
        sync_editor_divisions()
        available_tree.bind("<Double-1>", show_selected_profile)
        available_tree.bind("<<TreeviewSelect>>", refresh_history_editor, add="+")
        refresh_card_editor()

    def prompt_due_event(self):
        if self.root.state() == "withdrawn":
            return False
        due = [event for event in self.sorted_scheduled_events() if self.is_event_due(event)]
        if not due:
            return False
        event = due[0]
        references = set()
        for fight in event.get("fights", []):
            references.update(self.event_fight_participants(fight))
            references.update(ref for ref in fight.get("fighter_ids", []) if ref)
        retirement_names = []
        final_comeback_names = []
        for fighter in list(self.roster) + list(self.retired_fighters):
            if fighter.name not in references and getattr(fighter, "fighter_id", "") not in references:
                continue
            if getattr(fighter, "retirement_pending", False) or getattr(fighter, "retired", False):
                retirement_names.append(fighter.name)
            guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
            completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
            if getattr(fighter, "comeback_contract", False) and guaranteed - completed == 1:
                final_comeback_names.append(fighter.name)
        retirement_warning = ""
        if retirement_names:
            retirement_warning = "\n\nRETIREMENT NOTICE: " + ", ".join(sorted(set(retirement_names))) + " has announced retirement and will leave after completing their final scheduled commitment."
        comeback_warning = ""
        if final_comeback_names:
            comeback_warning = ("\n\nCOMEBACK COMMITMENT: " + ", ".join(sorted(set(final_comeback_names)))
                                + " will complete their guaranteed comeback commitment in this bout. Normal retirement review can resume afterward.")
        choice = messagebox.askyesnocancel("Fight Day", f"{event['name']} is due in {self.event_date_label(event)}.{retirement_warning}{comeback_warning}\n\nYes = Watch live\nNo = Sim instantly\nCancel = stay on this week")
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
            sport = self.combat_sport_for_fighter(fighter) if hasattr(self, "combat_sport_for_fighter") else ""
            sport_traits = {
                "Boxing": ["Technical Learner", "Body Hunter", "Counter Specialist", "Knockout Artist", "Cardio Machine", "Title Mentality", "Adaptable"],
                "Kickboxing": ["Technical Learner", "Leg Kicker", "Counter Specialist", "Knockout Artist", "Cardio Machine", "Fight Finisher", "Adaptable"],
                "Muay Thai": ["Technical Learner", "Leg Kicker", "Elbow Specialist", "Iron Chin", "Warrior Spirit", "Counter Specialist", "Fight Finisher"],
                "Wrestling": ["Technical Learner", "Cardio Machine", "Scramble Artist", "Title Mentality", "Pressure Fighter", "Adaptable", "Gym Rat"],
                "Brazilian Jiu-Jitsu": ["Submission Ace", "Scramble Artist", "Technical Learner", "Title Mentality", "Pressure Fighter", "Fight Finisher", "Adaptable"],
            }
            fighter.trait = random.choice(sport_traits.get(sport, [
                "Gym Rat", "Clutch", "Big Finisher", "Marketable", "Fan Favourite", "Cardio Machine",
                "Comeback Artist", "Submission Ace", "Knockout Artist", "Counter Specialist",
                "Coach Favourite", "Gym Leader", "Title Mentality", "Late Bloomer", "Technical Learner",
                "Warrior Spirit", "Fast Healer", "Adaptable", "Momentum Fighter", "Body Hunter",
                "Leg Kicker", "Cage Specialist", "Elbow Specialist", "Scramble Artist", "Fight Finisher",
            ]))
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
        chance *= self.gym_attention_multiplier(gym) * (0.82 + gym.morale / 360)
        if random.random() > chance:
            return
        specialty = random.choice(gym.specialties or ["Gameplanning"])
        keys = [key for key in GYM_SPECIALTY_SKILLS.get(specialty, ()) if key in fighter.detailed_skills]
        if not keys:
            return
        key = random.choice(keys)
        amount = 2 if gym.quality >= 84 and fighter.age <= fighter.prime_end else 1
        sport = self.combat_sport_for_fighter(fighter) if hasattr(self, "combat_sport_for_fighter") else ""
        if sport:
            stage = self.combat_sport_development_stage(fighter, sport)
            if stage not in ("Pre-prime", "Prime") or (stage == "Prime" and random.random() > 0.48):
                return
            native_keys = set(self.combat_sport_development_profile(sport)["growth"])
            if key not in native_keys or not self.adjust_combat_sport_training_key(fighter, sport, key, amount, f"{gym.name} camp development"):
                return
        else:
            if not self.improve_detailed_skill(fighter, key, amount):
                return
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
        package = dict(package)
        package["fight_logs"] = self.fight_night_log_order(package.get("fight_logs", []))
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
        replay_controls = ttk.Frame(window, style="Chrome.TFrame")
        replay_controls.pack(fill="x", padx=8, pady=(0, 8))
        if package.get("tournament_brackets"):
            ttk.Button(replay_controls, text="View Tournament Bracket", style="Accent.TButton", command=lambda: self.open_event_tournament_bracket(package, window)).pack(side="left")
        ttk.Button(replay_controls, text="Close", command=window.destroy).pack(side="right")

    def live_fight_official_outcome(self, log):
        """Return (is_draw, winner_name) for current and legacy fight logs."""
        result = str(log.get("result", "") or "")
        method = str(log.get("method", "") or "")
        a_name = str(log.get("a", "") or "")
        b_name = str(log.get("b", "") or "")
        structured_winner = str(log.get("winner", "") or "").strip()
        draw = (
            bool(log.get("draw"))
            or structured_winner.casefold() == "draw"
            or method.casefold() == "draw"
            or bool(re.search(r"\b(?:draw|fought to a draw)\b", result, re.IGNORECASE))
        )
        if draw:
            return True, ""
        if structured_winner in (a_name, b_name):
            return False, structured_winner
        if " - " in result:
            legacy_winner = result.split(" - ", 1)[0].strip()
            if legacy_winner in (a_name, b_name):
                return False, legacy_winner
        for name in (a_name, b_name):
            if name and re.search(rf"{re.escape(name)}\s+(?:def\.|defeats\b|beat\b|wins\b)", result, re.IGNORECASE):
                return False, name
        return False, ""

    def open_live_fight_window(self, event, package, apply_results=True, on_complete=None):
        # Matchmaking displays the headline at the top of the bill, but a live
        # broadcast runs from the undercard upward. Copy the package so archived
        # records are not mutated merely by opening a replay.
        package = dict(package)
        package["fight_logs"] = self.fight_night_log_order(package.get("fight_logs", []))
        window = tk.Toplevel(self.root)
        window.title(f"Live Fight - {event['name']}")
        self.root.update_idletasks()
        screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
        width = min(1180, max(820, screen_w - 80))
        height = min(800, max(560, screen_h - 120))
        x = max(0, min(screen_w - width, self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2))
        y = max(0, min(screen_h - height - 40, self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2))
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(min(820, width), min(560, height))
        window.configure(bg=self.colors["chrome"])
        canvas_hex = self.colors["cream"].lstrip("#")
        canvas_rgb = tuple(int(canvas_hex[index:index + 2], 16) for index in (0, 2, 4)) if len(canvas_hex) == 6 else (32, 32, 32)
        light_canvas = sum(canvas_rgb) > 430
        heading_color = "#6b4b00" if light_canvas else self.colors["gold"]
        round_color = "#005a78" if light_canvas else "#7dd3fc"
        result_color = "#8b1010" if light_canvas else "#ff8a8a"
        impact_color = "#8a4500" if light_canvas else "#ffb454"
        cut_color = "#8a2d1a" if light_canvas else "#ffb4a2"

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        title_label = ttk.Label(header, text=f"LIVE FIGHT: {event['name']}", style="ScreenTitle.TLabel")
        title_label.pack(side="left", padx=10, pady=5)
        event_progress_label = ttk.Label(header, text="Card ready", style="Panel.TLabel")
        event_progress_label.pack(side="right", padx=10, pady=5)
        event_progress = ttk.Progressbar(window, maximum=max(1, len(package.get("fight_logs", []))), value=0)
        event_progress.pack(fill="x", padx=8, pady=(4, 0))

        # Tale-of-the-tape scoreboard that updates as each bout begins.
        tote = tk.Frame(window, bg=self.colors["chrome"])
        tote.pack(fill="x", padx=8, pady=(6, 0))
        label_chip = tk.Label(tote, text="", font=("Tahoma", 9, "bold"), bg=self.colors["chrome"], fg=heading_color)
        label_chip.pack()
        broadcast_status = tk.Frame(tote, bg=self.colors["chrome"])
        broadcast_status.pack(pady=(1, 0))
        phase_label = tk.Label(broadcast_status, text="CARD READY", font=("Tahoma", 12, "bold"), bg=self.colors["chrome"], fg=round_color)
        phase_label.pack(side="left", padx=(0, 16))
        clock_label = tk.Label(broadcast_status, text="--:--", font=("Consolas", 18, "bold"), bg=self.colors["chrome"], fg=self.colors["gold"], width=5)
        clock_label.pack(side="left")
        matchup_row = tk.Frame(tote, bg=self.colors["chrome"])
        matchup_row.pack(fill="x")
        left_ovr = tk.Label(matchup_row, text="", font=("Tahoma", 22, "bold"), bg=self.colors["chrome"], fg=self.colors["gold"], anchor="e", width=5)
        left_ovr.pack(side="left", padx=(4, 2))
        left_name = tk.Label(matchup_row, text="", font=("Tahoma", 14, "bold underline"), bg=self.colors["chrome"], fg=self.colors["text"], anchor="e", width=25, cursor="hand2")
        left_name.pack(side="left", expand=True, fill="x", padx=(6, 4))
        vs_label = tk.Label(matchup_row, text="", font=("Tahoma", 11, "bold"), bg=self.colors["chrome"], fg=self.colors["red"])
        vs_label.pack(side="left")
        right_name = tk.Label(matchup_row, text="", font=("Tahoma", 14, "bold underline"), bg=self.colors["chrome"], fg=self.colors["text"], anchor="w", width=25, cursor="hand2")
        right_name.pack(side="left", expand=True, fill="x", padx=(4, 6))
        right_ovr = tk.Label(matchup_row, text="", font=("Tahoma", 22, "bold"), bg=self.colors["chrome"], fg=self.colors["gold"], anchor="w", width=5)
        right_ovr.pack(side="left", padx=(2, 4))
        # Keep the portraits attached to the matchup instead of pinning them to
        # the edges of a wide monitor.
        portrait_row = tk.Frame(tote, bg=self.colors["chrome"])
        portrait_row.pack(pady=(2, 3))
        left_portrait = tk.Canvas(portrait_row, width=112, height=100, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        left_portrait.pack(side="left")
        intro_label = tk.Label(portrait_row, text="TALE OF THE TAPE\nPress Play Fight to begin", font=("Tahoma", 9, "bold"), bg=self.colors["chrome"], fg=self.colors["muted"], justify="center", width=42)
        intro_label.pack(side="left", padx=16)
        right_portrait = tk.Canvas(portrait_row, width=112, height=100, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        right_portrait.pack(side="right")
        title_status_row = tk.Frame(tote, bg=self.colors["chrome"])
        title_status_row.pack(fill="x", padx=72)
        left_title_status = tk.Label(title_status_row, text="", bg=self.colors["chrome"], fg=self.colors["gold"], font=("Tahoma", 9, "bold"), anchor="e")
        left_title_status.pack(side="left", fill="x", expand=True, padx=(0, 28))
        right_title_status = tk.Label(title_status_row, text="", bg=self.colors["chrome"], fg=self.colors["gold"], font=("Tahoma", 9, "bold"), anchor="w")
        right_title_status.pack(side="left", fill="x", expand=True, padx=(28, 0))
        score_label = tk.Label(window, text="", font=("Consolas", 10, "bold"), bg=self.colors["chrome"], fg=heading_color)
        score_label.pack(fill="x", padx=8, pady=(0, 2))
        fight_read_label = tk.Label(window, text="", font=("Tahoma", 9, "bold"), bg=self.colors["chrome"], fg=self.colors["text"], wraplength=max(600, width - 80), justify="center")
        fight_read_label.pack(fill="x", padx=8, pady=(0, 4))
        condition_row = tk.Frame(window, bg=self.colors["chrome"])
        condition_row.pack(fill="x", padx=28, pady=(0, 5))
        left_condition = tk.Label(condition_row, text="RED CORNER READY", width=24, anchor="e", bg=self.colors["chrome"], fg=self.colors["muted"], font=("Tahoma", 8, "bold"))
        left_condition.pack(side="left", padx=(0, 5))
        left_gas = ttk.Progressbar(condition_row, maximum=100, value=100, length=220)
        left_gas.pack(side="left", fill="x", expand=True, padx=(0, 12))
        right_gas = ttk.Progressbar(condition_row, maximum=100, value=100, length=220)
        right_gas.pack(side="left", fill="x", expand=True, padx=(12, 0))
        right_condition = tk.Label(condition_row, text="BLUE CORNER READY", width=24, anchor="w", bg=self.colors["chrome"], fg=self.colors["muted"], font=("Tahoma", 8, "bold"))
        right_condition.pack(side="left", padx=(5, 0))

        # Broadcast-style tug-of-war momentum meter: who is winning the exchanges.
        momentum_frame = tk.Frame(window, bg=self.colors["chrome"])
        momentum_frame.pack(fill="x", padx=28, pady=(0, 4))
        tk.Label(momentum_frame, text="ROUND MOMENTUM", font=("Tahoma", 8, "bold"), bg=self.colors["chrome"], fg=self.colors["muted"]).pack(anchor="center")
        momentum_canvas = tk.Canvas(momentum_frame, height=22, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        momentum_canvas.pack(fill="x", padx=4)

        moment_panel = tk.Frame(window, bg=self.colors["tree"], highlightthickness=1, highlightbackground=self.colors["line"])
        moment_panel.pack(fill="x", padx=8, pady=(0, 5))
        current_moment_label = tk.Label(
            moment_panel, text="Select Start Next Fight when you are ready.", height=2,
            bg=self.colors["tree"], fg=self.colors["text"], font=("Tahoma", 12, "bold"),
            anchor="center", justify="center", wraplength=max(600, width - 90), padx=12, pady=5,
        )
        current_moment_label.pack(fill="x")
        round_read_label = tk.Label(
            moment_panel, text="Official scorecards remain sealed until the result.",
            bg=self.colors["chrome"], fg=self.colors["muted"], font=("Tahoma", 9, "bold"),
            anchor="center", justify="center", wraplength=max(600, width - 90), padx=10, pady=4,
        )
        round_read_label.pack(fill="x")
        result_ribbon = tk.Frame(moment_panel, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["gold"])
        result_winner_label = tk.Label(result_ribbon, text="", bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 15, "bold"), anchor="center")
        result_winner_label.pack(fill="x", padx=8, pady=(5, 0))
        result_detail_label = tk.Label(result_ribbon, text="", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="center", justify="center", wraplength=max(600, width - 100))
        result_detail_label.pack(fill="x", padx=10, pady=(1, 5))

        # Pack the control bar at the bottom FIRST so it always reserves its
        # space; the play-by-play body then expands into whatever is left.
        controls_area = ttk.Frame(window, style="Chrome.TFrame")
        controls_area.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        controls = ttk.Frame(controls_area, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 2))
        controls2 = ttk.Frame(controls_area, style="Chrome.TFrame")
        controls2.pack(fill="x", pady=(0, 2))
        controls3 = ttk.Frame(controls_area, style="Chrome.TFrame")
        controls3.pack(fill="x")

        body = tk.PanedWindow(
            window, orient="horizontal", bg=self.colors["line"], bd=0,
            sashwidth=8, sashrelief="raised", showhandle=True, handlesize=10,
        )
        body.pack(side="top", fill="both", expand=True, padx=8, pady=8)
        list_frame = ttk.Frame(body, style="Chrome.TFrame")
        fight_list = tk.Listbox(list_frame, width=29, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        fight_list.pack(side="left", fill="both", expand=True)
        fight_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=fight_list.yview)
        fight_scroll.pack(side="right", fill="y")
        fight_list.configure(yscrollcommand=fight_scroll.set)
        for index, fight_log in enumerate(package.get("fight_logs", []), 1):
            heading = fight_log.get("heading", fight_log.get("fight", f"Bout {index}"))
            fight_list.insert("end", f"{index}. PENDING - {heading[:28]}")

        text_frame = ttk.Frame(body, style="Chrome.TFrame")
        body.add(list_frame, minsize=170, width=270, stretch="never")
        body.add(text_frame, minsize=420, stretch="always")
        stats_panel = ttk.Frame(text_frame, style="Panel.TFrame")
        stats_panel.pack(side="bottom", fill="x", pady=(5, 0))
        ttk.Label(stats_panel, text="LIVE ROUND READ", style="Section.TLabel", anchor="center").pack(fill="x")
        stat_columns = ("fighter", "impact", "control", "threat", "gas", "momentum")
        live_stats = ttk.Treeview(stats_panel, columns=stat_columns, show="headings", height=2, selectmode="none")
        stat_defs = (
            ("fighter", "Fighter", 210, "w"), ("impact", "Impact", 65, "center"),
            ("control", "Control", 65, "center"), ("threat", "Threat", 65, "center"),
            ("gas", "Gas", 58, "center"), ("momentum", "Momentum", 100, "center"),
        )
        for column, heading, column_width, anchor in stat_defs:
            live_stats.heading(column, text=heading)
            live_stats.column(column, width=column_width, minwidth=48, anchor=anchor, stretch=column == "fighter")
        live_stats.pack(fill="x")
        text = tk.Text(text_frame, wrap="word", font=("Tahoma", 11), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=16, pady=12, spacing1=2, spacing2=1, spacing3=3)
        text.pack(side="left", fill="both", expand=True)
        text_scroll = ttk.Scrollbar(text_frame, orient="vertical")
        text_scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=text_scroll.set)
        text.tag_configure("heading", font=("Tahoma", 12, "bold"), foreground=heading_color, spacing1=7, spacing3=5)
        text.tag_configure("result", font=("Tahoma", 12, "bold"), foreground=result_color, spacing1=10, spacing3=8)
        text.tag_configure("round", font=("Tahoma", 11, "bold"), foreground=round_color, spacing1=8, spacing3=5)
        text.tag_configure("clock", font=("Consolas", 10, "bold"), foreground=heading_color)
        text.tag_configure("analysis", font=("Tahoma", 10, "italic"), foreground=self.colors["muted"], lmargin1=12, lmargin2=12, spacing1=5, spacing3=5)
        text.tag_configure("separator", font=("Consolas", 9), foreground=self.colors["muted"])
        text.tag_configure("metrics", font=("Consolas", 10), foreground=self.colors["text"], lmargin1=8, lmargin2=8)
        # Bright event-critical colors remain readable on the UFC theme's near-black canvas.
        text.tag_configure("knockdown", font=("Tahoma", 11, "bold"), foreground=impact_color)
        text.tag_configure("finish", font=("Tahoma", 12, "bold"), foreground=result_color, spacing1=7, spacing3=6)
        text.tag_configure("cut", foreground=cut_color)
        text.tag_configure("referee", font=("Tahoma", 11, "bold"), foreground=round_color)
        text.config(state="disabled")

        state = {
            "fight": -1, "line": 0,
            "delay": max(300, min(3000, self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 1600)),
            "running": False, "finished": False, "after_id": None, "phase": "", "result_shown": False,
            "metrics_rows_remaining": 0, "scorecard_buffer": [], "holding_scorecards": False,
            "momentum": "", "close_armed": False,
            "auto": bool(self.rules.get("live_auto_play_card", False)),
        }
        fight_logs = package.get("fight_logs", [{"heading": "Event Report", "lines": package["log"]}])
        follow_var = tk.BooleanVar(value=bool(self.rules.get("live_follow_commentary", True)))
        font_size = tk.IntVar(value=11)

        def scroll_text(*args):
            follow_var.set(False)
            self.rules["live_follow_commentary"] = False
            text.yview(*args)

        text_scroll.configure(command=scroll_text)
        text.bind("<MouseWheel>", lambda _event: (follow_var.set(False), self.rules.__setitem__("live_follow_commentary", False)), add="+")

        def condition_word(gas):
            if gas >= 70:
                return "FRESH"
            if gas >= 45:
                return "WORKING"
            if gas >= 25:
                return "FADING"
            return "EXHAUSTED"

        def set_condition(gas_a, gas_b):
            gas_a = max(0, min(100, int(gas_a)))
            gas_b = max(0, min(100, int(gas_b)))
            state["gas"] = (gas_a, gas_b)
            left_gas["value"] = gas_a
            right_gas["value"] = gas_b
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            left_marker = "  MOMENTUM" if state.get("momentum") == a_name else ""
            right_marker = "MOMENTUM  " if state.get("momentum") == b_name else ""
            left_condition.config(text=f"RED {condition_word(gas_a)}  {gas_a}%{left_marker}")
            right_condition.config(text=f"{right_marker}{gas_b}%  {condition_word(gas_b)} BLUE")

        live_stats.tag_configure("edge", foreground="#7fd694")

        def draw_momentum_bar():
            canvas = momentum_canvas
            canvas.delete("all")
            canvas_w = int(canvas.winfo_width() or 0) or 600
            canvas_h = int(canvas.winfo_height() or 0) or 22
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            values = state.get("round_values", {})
            a_row, b_row = values.get(a_name, {}), values.get(b_name, {})
            strength_a = sum(float(a_row.get(key, 0) or 0) for key in ("impact", "control", "danger"))
            strength_b = sum(float(b_row.get(key, 0) or 0) for key in ("impact", "control", "danger"))
            total = strength_a + strength_b
            lean_a = 0.5 if total <= 0 else max(0.06, min(0.94, strength_a / total))
            split = int(canvas_w * lean_a)
            red = self.colors.get("red", "#c0392b")
            blue = "#3f7bd6"
            canvas.create_rectangle(0, 0, split, canvas_h, fill=red, width=0)
            canvas.create_rectangle(split, 0, canvas_w, canvas_h, fill=blue, width=0)
            canvas.create_line(canvas_w // 2, 0, canvas_w // 2, canvas_h, fill="#ffffff", width=1, dash=(2, 2))
            canvas.create_line(split, 0, split, canvas_h, fill=self.colors.get("gold", "#c9a13a"), width=3)
            if a_name:
                canvas.create_text(7, canvas_h // 2, text=a_name[:18], anchor="w", fill="#ffffff", font=("Tahoma", 8, "bold"))
            if b_name:
                canvas.create_text(canvas_w - 7, canvas_h // 2, text=b_name[:18], anchor="e", fill="#ffffff", font=("Tahoma", 8, "bold"))
            if total > 0:
                canvas.create_text(canvas_w // 2, canvas_h // 2, text=f"{round(lean_a * 100)}—{round((1 - lean_a) * 100)}", anchor="center", fill="#ffffff", font=("Consolas", 8, "bold"))

        momentum_canvas.bind("<Configure>", lambda _event: draw_momentum_bar())

        def refresh_live_stats(round_values=None):
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            names = (current_log.get("a", "Red corner"), current_log.get("b", "Blue corner"))
            gas = state.get("gas", (100, 100))
            values = round_values or state.get("round_values", {})
            for item in live_stats.get_children():
                live_stats.delete(item)
            for index, name in enumerate(names):
                row = values.get(name, {})
                leads = state.get("momentum") == name
                marker = "EDGE" if leads else "-"
                live_stats.insert("", "end", tags=("edge",) if leads else (), values=(
                    name,
                    int(round(float(row.get("impact", 0) or 0))),
                    int(round(float(row.get("control", 0) or 0))),
                    int(round(float(row.get("danger", 0) or 0))),
                    int(gas[index]), marker,
                ))
            draw_momentum_bar()

        def round_summary_presentation(value):
            """Turn engine telemetry into a readable broadcast summary.

            Exact judge cards stay in the underlying log.  The live viewer only
            presents a bounded broadcast lean until the official result exists.
            """
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            if not (a_name and b_name and " summary:" in value.lower() and "Metrics -" in value):
                return value
            pattern = (
                rf"^(Round\s+\d+)\s+summary:.*?Metrics\s+-\s+{re.escape(a_name)}:\s*impact\s+([\d.]+),\s*control\s+([\d.]+),\s*danger\s+([\d.]+);\s*"
                rf"{re.escape(b_name)}:\s*impact\s+([\d.]+),\s*control\s+([\d.]+),\s*danger\s+([\d.]+)\.\s*"
                rf"Live score\s+{re.escape(a_name)}\s+([\d.]+),\s*{re.escape(b_name)}\s+([\d.]+)\.\s*"
                rf"Gas:\s*{re.escape(a_name)}\s+([\d.]+),\s*{re.escape(b_name)}\s+([\d.]+)\.\s*Momentum:\s*(.+?)\.?$"
            )
            match = re.match(pattern, value, re.IGNORECASE)
            if not match:
                # Never leak the three exact round cards if an older/newer log
                # format cannot be fully parsed.
                value = re.sub(r"judge cards\s+.*?\.\s*Metrics", "judges' cards sealed. Metrics", value, flags=re.IGNORECASE)
                return re.sub(r"Live score\s+.*?(?=(?:Gas|Stamina):|$)", "Unofficial broadcast lean updated. ", value, flags=re.IGNORECASE)
            phase = match.group(1).title()
            numbers = [int(round(float(number))) for number in match.groups()[1:11]]
            a_impact, a_control, a_danger, b_impact, b_control, b_danger, a_score, b_score, gas_a, gas_b = numbers
            momentum = match.group(12).strip().rstrip(".")
            state["momentum"] = momentum
            state["round_values"] = {
                a_name: {"impact": a_impact, "control": a_control, "danger": a_danger},
                b_name: {"impact": b_impact, "control": b_control, "danger": b_danger},
            }
            set_condition(gas_a, gas_b)
            refresh_live_stats(state["round_values"])
            margin = a_score - b_score
            if abs(margin) <= 1:
                lean = "TOO CLOSE TO CALL"
            elif abs(margin) <= 3:
                lean = f"SLIGHT LEAN: {a_name if margin > 0 else b_name}"
            else:
                lean = f"LEAN: {a_name if margin > 0 else b_name}"
            score_label.config(text=f"Unofficial broadcast read: {lean}  |  Official judges sealed")
            summary = (
                f"{phase}: {a_name} impact {a_impact}, control {a_control}, threat {a_danger}; "
                f"{b_name} impact {b_impact}, control {b_control}, threat {b_danger}. "
                f"Momentum: {momentum}. {lean}."
            )
            round_read_label.config(text=summary + " Official cards remain private.")
            current_moment_label.config(text=summary)
            return summary

        def append_line(value):
            value = str(value or "").strip("\n")
            if not value:
                return
            value = round_summary_presentation(value)
            if not state.get("result_shown") and "Live score" in value:
                value = re.sub(r"Live score\s+.*?(?=(?:Gas|Stamina):|$)", "Unofficial broadcast lean updated. ", value, flags=re.IGNORECASE)
            if not state.get("result_shown") and value.startswith("R") and "Scores " in value:
                value = re.sub(r"Scores\s+.*?(?=\.|$)", "Judges' round read sealed", value)
            # Old archived commentary can contain float-valued metric fields.
            # Fight telemetry is count/time data, so the presentation is always
            # normalized to whole numbers in the end-of-bout box score.
            is_metrics_row = state.get("metrics_rows_remaining", 0) > 0
            if is_metrics_row:
                value = re.sub(r"\b\d+\.\d+\b", lambda match: str(round(float(match.group(0)))), value)
                state["metrics_rows_remaining"] -= 1
            text.config(state="normal")
            tag = None
            lowered = value.lower()
            upper = value.upper()
            clock_match = re.match(r"^\s*(\[\d{1,2}:\d{2}\])\s*(.*)$", value)
            phase_match = re.match(r"^(ROUND\s+\d+|PERIOD\s+\d+|MATCH CLOCK)", upper)
            is_phase_start = bool(phase_match) and ("—" in value or ":" in value[:20])
            if value.startswith(("MAIN", "TITLE", "INTERIM", "BOUT")) or value.endswith(":"):
                tag = "heading"
            if upper == "FIGHT METRICS":
                state["metrics_rows_remaining"] = 4
            elif is_metrics_row:
                tag = "metrics"
            elif value.startswith("Result:"):
                tag = "result"
                state["result_shown"] = True
                phase_label.config(text="OFFICIAL RESULT")
            elif is_phase_start or " summary:" in lowered or (value.startswith("R") and ":" in value[:5]) or value.startswith("Match:"):
                tag = "round"
                if is_phase_start:
                    state["phase"] = phase_match.group(1)
                    phase_label.config(text=state["phase"])
                    clock_label.config(text=f"{int(self.rules.get('round_length', 5))}:00")
            elif value.startswith(("Corner read:", "Mat-side read:", "Broadcast read:", "Fight-night readiness:")):
                tag = "analysis"
            elif "referee" in lowered or "official" in lowered:
                tag = "referee"
            elif any(k in lowered for k in ("taps to", "has to tap", "gets the tap", "and it's all over", "unconscious", "stops the fight", "by ko", "by tko", "by submission", "technical fall", "secures the pin", "referee has seen enough", "stoppage comes")):
                tag = "finish"
            elif any(k in lowered for k in ("drops", "hits the mat", "stumbles badly", "knocked down", "wobbl", "buckl", "rocked", "hurt")):
                tag = "knockdown"
            elif "cut" in lowered or "swelling" in lowered:
                tag = "cut"
            elif value and set(value) <= {"-", "=", " "}:
                tag = "separator"
            if clock_match:
                text.insert("end", clock_match.group(1) + "  ", "clock")
                text.insert("end", clock_match.group(2) + "\n", tag or ())
                current_moment_label.config(text=clock_match.group(2))
                clock_label.config(text=clock_match.group(1).strip("[]"))
                if state.get("phase"):
                    phase_label.config(text=state["phase"])
            elif tag:
                text.insert("end", value + ("\n\n" if tag in ("heading", "round", "result", "finish") else "\n"), tag)
            else:
                text.insert("end", value + "\n")
            if follow_var.get():
                text.see("end")
            text.config(state="disabled")
            # Cues mirror clearly observable broadcast moments. They never
            # affect fight simulation or event timing, and can be disabled in
            # Game Settings.
            if is_phase_start:
                self.play_fight_night_sound("round_start")
            elif tag == "finish":
                self.play_fight_night_sound("finish")
            elif tag == "knockdown":
                self.play_fight_night_sound("knockdown")
            elif clock_match and any(word in lowered for word in ("lands", "connects", "drives", "slams", "elbow")):
                self.play_fight_night_sound("impact")
            # Keep the shared scoreboard live for MMA rounds, boxing/kickboxing/
            # Thai rounds, wrestling periods and BJJ matches.
            if value.startswith("R") and "Scores " in value:
                score_label.config(text="Unofficial broadcast read updated  |  Official judges sealed")
            if value.startswith(("Corner read:", "Mat-side read:", "Broadcast read:")):
                fight_read_label.config(text=value)
            if value.startswith("Result:"):
                score_label.config(text=value.replace("Result: ", "").split(" | ")[0])
                fight_read_label.config(text=value.replace("Result: ", "").split(" | ")[-1])
                current_moment_label.config(text=value.replace("Result: ", ""))
                round_read_label.config(text="Official result confirmed. Full scorecards and fight metrics are shown below.")
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            if a_name and b_name:
                condition_match = re.search(
                    rf"(?:Gas|Stamina):\s*{re.escape(a_name)}\s+([\d.]+),\s*{re.escape(b_name)}\s+([\d.]+)", value, re.IGNORECASE,
                )
                if not condition_match and value.startswith(("Corner read:", "Mat-side read:")):
                    condition_match = re.search(
                        rf"{re.escape(a_name)}\s+stamina\s+([\d.]+).*?{re.escape(b_name)}\s+stamina\s+([\d.]+)", value, re.IGNORECASE,
                    )
                if condition_match:
                    set_condition(float(condition_match.group(1)), float(condition_match.group(2)))
                    refresh_live_stats()

        def reveal_scorecards():
            buffered = list(state.get("scorecard_buffer", []))
            state["scorecard_buffer"] = []
            state["holding_scorecards"] = False
            if not buffered:
                return
            append_line("OFFICIAL SCORECARDS - RESULT CONFIRMED")
            self.play_fight_night_sound("decision")
            for card_line in buffered[1:]:
                append_line(card_line)

        def present_fight_line(line):
            """Render one stored line while preserving result suspense."""
            stripped = str(line or "").strip()
            if stripped == "Official scorecards:":
                state["holding_scorecards"] = True
                state["scorecard_buffer"] = [stripped]
                phase_label.config(text="DECISION PENDING")
                current_moment_label.config(text="The judges are finalising their cards...")
                round_read_label.config(text="Exact totals remain sealed until the official decision is announced.")
                return False
            if state.get("holding_scorecards"):
                if stripped.startswith("Judges' vote:") or re.match(r"^.+?\s+\[.+?\]:", stripped):
                    state["scorecard_buffer"].append(stripped)
                    return False
                append_line(line)
                reveal_scorecards()
                return True
            append_line(line)
            return True

        def finish_live_event():
            if state["finished"]:
                return
            cancel_timer()
            state["finished"] = True
            self.play_fight_night_sound("card_complete")
            event_progress["value"] = max(1, len(fight_logs))
            event_progress_label.config(text=f"Card complete - {len(fight_logs)} fights")
            phase_label.config(text="EVENT COMPLETE")
            profit = int(round(float(package.get("profit", 0) or 0)))
            excitement = int(round(float(package.get("average_excitement", 0) or 0)))
            current_moment_label.config(text=f"{event.get('name', 'Event')} complete  •  Profit ${profit:,}  •  Average excitement {excitement}")
            round_read_label.config(text="Results, bonuses, attendance, finances, and company effects are available in the end-of-event report.")
            if apply_results:
                self.finish_event(event, package)
                append_line("\n[Event processed. Results have been applied to the world.]")
            else:
                append_line("\n[Simulation complete. No world results were applied.]")
            if on_complete:
                on_complete()

        def mark_fight_done(index):
            log = fight_logs[index]
            result = log.get("result") or ("CANCELLED" if log.get("cancelled") else "")
            if result and fight_list.size() > index:
                fight_list.delete(index)
                fight_list.insert(index, f"{index + 1}. DONE - {result[:31]}")
            event_progress["value"] = index + 1
            update_event_button_label()

        def all_presented_fights_complete():
            if not fight_logs:
                return True
            if state["finished"]:
                return True
            if state["fight"] < len(fight_logs) - 1:
                return False
            if state["fight"] < 0:
                return False
            return state["line"] >= len(fight_logs[state["fight"]].get("lines", []))

        def update_event_button_label():
            try:
                skip_event_button.config(text="End Event" if all_presented_fights_complete() else "Skip Event")
            except (NameError, tk.TclError):
                pass

        def open_header_profile(side):
            if not (0 <= state["fight"] < len(fight_logs)):
                return
            log = fight_logs[state["fight"]]
            fighter = self.result_fighter(log.get(side, ""), log.get(f"{side}_id", ""), log.get("sport", ""), log.get("weight", ""))
            if fighter:
                self.open_fighter_profile_window(fighter)

        left_name.bind("<Button-1>", lambda _event: open_header_profile("a"))
        right_name.bind("<Button-1>", lambda _event: open_header_profile("b"))

        def draw_intro_portrait(canvas, fighter, corner):
            canvas.delete("all")
            bg = getattr(fighter, "portrait_bg", "") or self.colors["panel_dark"]
            accent = getattr(fighter, "portrait_accent", "") or (self.colors["red"] if corner == "red" else "#3b9edb")
            canvas.configure(bg=bg)
            width, height = int(canvas.cget("width")), int(canvas.cget("height"))
            canvas.create_rectangle(5, 5, width - 5, height - 7, fill=bg, outline=accent, width=2)
            canvas.create_oval(width * 0.32, height * 0.16, width * 0.68, height * 0.52, fill=accent, outline="")
            canvas.create_polygon(width * 0.18, height * 0.84, width * 0.32, height * 0.54, width * 0.68, height * 0.54, width * 0.82, height * 0.84, fill="#d7d7d7", outline="")
            initials = "".join(part[0] for part in fighter.name.replace("'", "").split()[:2]).upper()
            canvas.create_text(width / 2, height * 0.34, text=initials, fill=bg, font=("Impact", 18))
            canvas.create_rectangle(8, height - 24, width - 8, height - 9, fill=accent, outline="")
            canvas.create_text(width / 2, height - 16, text=f"OVR {fighter.overall}", fill=bg, font=("Tahoma", 8, "bold"))

        def form_text(fighter):
            history = list(getattr(fighter, "bout_rating_history", []) or [])[:5]
            form = "".join(str(row.get("result", "-"))[:1] for row in history if isinstance(row, dict))
            return form or "No recent result"

        def pre_fight_copy(log):
            a = self.result_fighter(log.get("a", ""), log.get("a_id", ""), log.get("sport", ""), log.get("weight", ""))
            b = self.result_fighter(log.get("b", ""), log.get("b_id", ""), log.get("sport", ""), log.get("weight", ""))
            if not (a and b):
                return "Fighters are ready for the next bout."
            stakes = log.get("special_belt") or ("Interim championship" if log.get("interim") else "Championship" if log.get("divisional_title") or log.get("title") else "Featured bout")
            rivalry = self.rivalry_heat_between(a, b) if hasattr(self, "rivalry_heat_between") else 0
            rivalry_copy = f" Rivalry heat {rivalry}/100." if rivalry else ""
            return (f"{stakes}: {a.style} from {a.camp or 'independent camp'} meets {b.style} from {b.camp or 'independent camp'}. "
                    f"Recent form {a.name}: {form_text(a)} | {b.name}: {form_text(b)}. Odds {self.matchup_odds(a, b)}.{rivalry_copy}")

        def broadcast_rundown(index, log):
            """Give each bout a concise place in the event broadcast."""
            remaining = max(0, len(fight_logs) - index - 1)
            position = str(log.get("card_position") or log.get("tier") or "Fight Night")
            a_name, b_name = log.get("a", "Red corner"), log.get("b", "Blue corner")
            stakes = "a championship" if log.get("divisional_title") or log.get("title") else "a featured contest"
            if "Main Event" in position:
                lead = f"Broadcast desk: the main event is here. {a_name} and {b_name} close the card with {stakes} at stake."
            elif "Co-Main" in position:
                lead = f"Broadcast desk: co-main time. {a_name} and {b_name} set the stage for the headline bout."
            elif index == 0:
                lead = f"Broadcast desk: the card is underway. {a_name} and {b_name} set the first impression for the arena."
            else:
                lead = f"Broadcast desk: {position}. {a_name} and {b_name} take over with {stakes} at stake."
            return lead + (" This is the final fight of the broadcast." if not remaining else f" {remaining} bout{'s' if remaining != 1 else ''} remain on the card.")

        def reset_result_ribbon():
            result_winner_label.config(text="")
            result_detail_label.config(text="")
            result_ribbon.pack_forget()

        def update_scoreboard(log):
            def rating_text(snapshot):
                if isinstance(snapshot, dict):
                    value = snapshot.get("overall", 0)
                else:
                    value = snapshot
                try:
                    value = int(round(float(value or 0)))
                except (TypeError, ValueError):
                    value = 0
                return f"OVR\n{value}" if value else ""

            label_chip.config(text=log.get("label", ""))
            a_name, b_name = log.get("a", ""), log.get("b", "")
            if a_name and b_name:
                left_name.config(text=f"{a_name}\n{log.get('a_record', '')}")
                left_ovr.config(text=rating_text(log.get("a_rating", {})))
                vs_label.config(text="VS")
                right_name.config(text=f"{b_name}\n{log.get('b_record', '')}")
                right_ovr.config(text=rating_text(log.get("b_rating", {})))
                left_title_status.config(text=log.get("a_title_status", ""))
                right_title_status.config(text=log.get("b_title_status", ""))
            else:
                left_name.config(text=log.get("heading", "")[:40])
                left_ovr.config(text="")
                vs_label.config(text="")
                right_name.config(text="")
                right_ovr.config(text="")
                left_title_status.config(text="")
                right_title_status.config(text="")
            score_label.config(text="")
            state["momentum"] = ""
            state["round_values"] = {}
            state["scorecard_buffer"] = []
            state["holding_scorecards"] = False
            reset_result_ribbon()
            clock_label.config(text=f"{int(self.rules.get('round_length', 5))}:00")
            if a_name and b_name:
                a = self.result_fighter(a_name, log.get("a_id", ""), log.get("sport", ""), log.get("weight", ""))
                b = self.result_fighter(b_name, log.get("b_id", ""), log.get("sport", ""), log.get("weight", ""))
                if a:
                    draw_intro_portrait(left_portrait, a, "red")
                if b:
                    draw_intro_portrait(right_portrait, b, "blue")
                set_condition(log.get("a_start_gas", 100), log.get("b_start_gas", 100))
                refresh_live_stats()
                current_moment_label.config(text=pre_fight_copy(log))
                round_read_label.config(text="Walkouts complete. Tale of the tape, camp form, odds, and stakes are live; official scoring stays sealed until the result.")
                fight_read_label.config(text=f"{log.get('weight', '')} | {log.get('label', 'Bout')} | Condition, momentum, threat, and control update between rounds.")
                intro_label.config(text=f"{log.get('weight', '').upper()} | {log.get('label', 'BOUT')}\n{log.get('a_record', '')}  vs  {log.get('b_record', '')}")
            else:
                set_condition(100, 100)
                refresh_live_stats()
                fight_read_label.config(text="")
                intro_label.config(text="EVENT PRESENTATION")

        def start_next_fight():
            if state["finished"]:
                return
            cancel_timer()
            state["running"] = False
            if 0 <= state["fight"] < len(fight_logs):
                mark_fight_done(state["fight"])
            state["fight"] += 1
            state["line"] = 0
            state["phase"] = ""
            state["result_shown"] = False
            state["close_armed"] = False
            if state["fight"] >= len(fight_logs):
                finish_live_event()
                return
            fight_list.selection_clear(0, "end")
            if fight_list.size():
                fight_list.delete(state["fight"])
                fight_list.insert(state["fight"], f"{state['fight'] + 1}. LIVE - {fight_logs[state['fight']].get('heading', 'Bout')[:31]}")
                fight_list.selection_set(state["fight"])
                fight_list.see(state["fight"])
            log = fight_logs[state["fight"]]
            self.play_fight_night_sound("bout_start")
            heading = log.get("heading", log.get("fight", "Bout"))
            title_label.config(text=f"LIVE FIGHT: {heading[:70]}")
            stage = f" - {log.get('tournament_stage')}" if log.get("tournament_stage") else ""
            event_progress_label.config(text=f"Fight {state['fight'] + 1} of {len(fight_logs)}{stage}")
            update_scoreboard(log)
            text.config(state="normal")
            text.delete("1.0", "end")
            text.config(state="disabled")
            append_line(log["heading"])
            append_line("-" * 72)
            append_line(broadcast_rundown(state["fight"], log))
            lines = log.get("lines", [])
            if lines and str(lines[0]).strip() == str(heading).strip():
                state["line"] = 1

        def cancel_timer():
            after_id = state.get("after_id")
            state["after_id"] = None
            if after_id:
                try:
                    window.after_cancel(after_id)
                except tk.TclError:
                    pass

        def schedule_next(delay=None):
            cancel_timer()
            if not state["running"] or state["finished"]:
                return
            def callback():
                state["after_id"] = None
                if state["running"] and not state["finished"] and window.winfo_exists():
                    append_next()
            state["after_id"] = window.after(max(100, int(delay if delay is not None else state["delay"])), callback)

        def show_result_if_needed():
            if state["result_shown"] or not (0 <= state["fight"] < len(fight_logs)):
                return
            result = fight_logs[state["fight"]].get("result", "")
            if result:
                append_line(f"Result: {result}")
                reveal_scorecards()

        def show_fight_complete_status():
            state["running"] = False
            log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            result = log.get("result", "")
            phase_label.config(text="BOUT COMPLETE")
            current_moment_label.config(text=result or "Bout complete")
            lines = log.get("lines", [])
            clocks = re.findall(r"\[(\d{1,2}:\d{2})\]", "\n".join(str(line) for line in lines))
            finish_time = clocks[-1] if clocks else (f"{int(self.rules.get('round_length', 5))}:00" if "Decision" in result or "Draw" in result else "Official time pending")
            clock_label.config(text=finish_time if finish_time != "Official time pending" else "--:--")
            a_record = log.get("a_record", "-")
            b_record = log.get("b_record", "-")
            def next_record(record, outcome):
                try:
                    w, l, d = (int(part) for part in str(record).split("-")[:3])
                    if outcome == "win": w += 1
                    elif outcome == "loss": l += 1
                    elif outcome == "draw": d += 1
                    else: return record or "-"
                    return f"{w}-{l}-{d}"
                except (TypeError, ValueError):
                    return record or "-"
            draw, winner_name = self.live_fight_official_outcome(log)
            a_outcome = "draw" if draw else "win" if log.get("a") == winner_name else "loss" if winner_name else "unknown"
            b_outcome = "draw" if draw else "win" if log.get("b") == winner_name else "loss" if winner_name else "unknown"
            scorecards = log.get("scorecards", "") or "No scorecards required"
            excitement = int(round(float(log.get("excitement", 0) or 0)))
            contender = "Bonus contender" if excitement >= 62 else "Solid performance" if excitement >= 45 else "Low bonus contention"
            result_winner_label.config(text="OFFICIAL DRAW" if draw else f"WINNER: {winner_name}" if winner_name else "OFFICIAL RESULT")
            result_detail_label.config(text=(f"{result or 'Official result'}  |  Time: {finish_time}\n"
                f"Records: {log.get('a', 'Red')} {a_record} -> {next_record(a_record, a_outcome)}   |   "
                f"{log.get('b', 'Blue')} {b_record} -> {next_record(b_record, b_outcome)}\n"
                f"{scorecards}  |  {contender} (excitement {excitement})\n"
                "Medical clearance, morale, popularity, and any suspension are applied after the card and explained in End of Event."))
            result_ribbon.pack(fill="x", padx=6, pady=(4, 5))
            status_label.config(text="Bout complete. Review the official result, scorecards, and metrics, then start the next fight.", fg=self.colors["muted"])
            append_line("\n[Fight complete. Press Start Next Fight.]")
            if state["fight"] + 1 < len(fight_logs):
                next_log = fight_logs[state["fight"] + 1]
                append_line(f"Broadcast desk: next up, {next_log.get('heading', 'the next bout')}. The card moves on after the official result.")
            update_event_button_label()

        def is_round_boundary(line):
            lowered = str(line).lower()
            return (
                " summary:" in lowered
                or str(line).startswith(("Match:", "Result:"))
                or (str(line).startswith("R") and ":" in str(line)[:5])
            )

        def append_next():
            if state["finished"]:
                return
            if state["fight"] < 0:
                start_next_fight()
            lines = fight_logs[state["fight"]]["lines"]
            if state["line"] >= len(lines):
                show_result_if_needed()
                if state.get("auto") and not state["finished"]:
                    def continue_card():
                        state["after_id"] = None
                        if state["finished"] or not window.winfo_exists():
                            return
                        start_next_fight()
                        if not state["finished"]:
                            state["running"] = True
                            append_next()
                    cancel_timer()
                    state["after_id"] = window.after(max(600, state["delay"] * 2), continue_card)
                    return
                show_fight_complete_status()
                return
            line = lines[state["line"]]
            rendered = present_fight_line(line)
            state["line"] += 1
            if state["running"]:
                lowered = str(line).lower()
                hold = state["delay"]
                if not rendered:
                    hold = 90
                elif str(line).upper().startswith(("ROUND ", "PERIOD ", "MATCH CLOCK")):
                    hold = round(hold * 1.35)
                elif " summary:" in lowered:
                    hold = round(hold * 1.85)
                elif str(line).startswith(("Result:", "Corner read:", "Mat-side read:", "Broadcast read:")):
                    hold = round(hold * 1.45)
                elif any(word in lowered for word in ("drops", "knocked down", "wobbles", "rocked", "stops the fight", "submission", "technical fall", "secures the pin", "ko/tko")):
                    hold = round(hold * 1.75)
                elif str(line).strip().startswith("["):
                    hold = round(hold * 0.92)
                schedule_next(hold)

        def start():
            if state["finished"]:
                return
            if state["running"]:
                return
            if state["fight"] < 0:
                start_next_fight()
            if state["finished"]:
                return
            state["running"] = True
            state["close_armed"] = False
            status_label.config(text="Live playback running", fg=self.colors["muted"])
            close_button.config(text="Close")
            pause_button.config(text="Pause")
            append_next()

        def faster():
            state["delay"] = max(300, state["delay"] - 200)
            self.fight_timer_delay.set(state["delay"])
            speed_var.set(state["delay"])

        def slower():
            state["delay"] = min(3000, state["delay"] + 150)
            self.fight_timer_delay.set(state["delay"])
            speed_var.set(state["delay"])

        def apply_speed():
            state["delay"] = max(300, min(3000, int(speed_var.get())))
            self.fight_timer_delay.set(state["delay"])

        def pause_resume():
            if state["finished"]:
                return
            state["running"] = not state["running"]
            state["close_armed"] = False
            close_button.config(text="Close")
            pause_button.config(text="Pause" if state["running"] else "Resume")
            if state["running"]:
                status_label.config(text="Live playback running", fg=self.colors["muted"])
                append_next()
            else:
                cancel_timer()
                status_label.config(text="Paused", fg=heading_color)

        def next_round():
            if state["fight"] < 0:
                start_next_fight()
            state["running"] = False
            cancel_timer()
            lines = fight_logs[state["fight"]]["lines"]
            while state["line"] < len(lines):
                line = lines[state["line"]]
                append_next()
                if is_round_boundary(line):
                    break

        def skip_current_fight():
            if state["finished"]:
                return
            if state["fight"] < 0:
                start_next_fight()
            state["running"] = False
            cancel_timer()
            lines = fight_logs[state["fight"]]["lines"]
            while state["line"] < len(lines):
                present_fight_line(lines[state["line"]])
                state["line"] += 1
            show_result_if_needed()
            show_fight_complete_status()
            if state.get("auto") and not state["finished"]:
                status_label.config(text="Fight skipped. Auto-play is starting the next bout...", fg=self.colors["muted"])

                def continue_auto_card():
                    state["after_id"] = None
                    if state["finished"] or not window.winfo_exists():
                        return
                    start_next_fight()
                    if not state["finished"]:
                        state["running"] = True
                        append_next()

                cancel_timer()
                state["after_id"] = window.after(max(450, state["delay"]), continue_auto_card)

        def skip_to_end():
            state["running"] = False
            cancel_timer()
            for index in range(fight_list.size()):
                mark_fight_done(index)
            finish_live_event()

        def close_window():
            cancel_timer()
            if not state["finished"]:
                if not state.get("close_armed"):
                    state["running"] = False
                    state["close_armed"] = True
                    pause_button.config(text="Resume")
                    close_button.config(text="Confirm Close")
                    action = "apply the completed event package" if apply_results else "discard this presentation"
                    status_label.config(text=f"Fight Night is still in progress. Press Confirm Close to {action}, or Resume to continue.", fg=result_color)
                    return
                finish_live_event()
            window.destroy()

        def review_selected_bout(_event=None):
            selected = fight_list.curselection()
            if not selected:
                status_label.config(text="Select a completed bout on the left to review its commentary.", fg=heading_color)
                return
            index = selected[0]
            current_complete = (
                index == state["fight"]
                and 0 <= index < len(fight_logs)
                and state["line"] >= len(fight_logs[index].get("lines", []))
            )
            if index > state["fight"] or (index == state["fight"] and not current_complete and not state["finished"]):
                status_label.config(text="That bout has not finished. Future commentary remains locked.", fg=result_color)
                return
            log = fight_logs[index]
            review = tk.Toplevel(window)
            review.title(f"Fight Review - {log.get('a', '')} vs {log.get('b', '')}")
            review.geometry(f"{min(920, width - 80)}x{min(680, height - 80)}")
            review.minsize(700, 480)
            review.configure(bg=self.colors["chrome"])
            review.transient(window)
            review_header = ttk.Frame(review, style="Header.TFrame")
            review_header.pack(fill="x", padx=8, pady=(8, 0))
            ttk.Label(review_header, text=f"COMPLETED BOUT {index + 1}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
            ttk.Label(review_header, text=log.get("label", "BOUT"), style="ScreenTitle.TLabel").pack(side="right", padx=10)
            matchup = tk.Frame(review, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            matchup.pack(fill="x", padx=8, pady=8)
            left_copy = log.get("a", "Red corner")
            right_copy = log.get("b", "Blue corner")
            left_role = log.get("a_title_status", "")
            right_role = log.get("b_title_status", "")
            tk.Label(matchup, text=f"{left_copy}\n{left_role}", bg=self.colors["panel_dark"], fg=self.colors["gold"] if left_role else self.colors["text"], font=("Tahoma", 11, "bold"), justify="right").pack(side="left", fill="x", expand=True, padx=12, pady=9)
            tk.Label(matchup, text="VS", bg=self.colors["panel_dark"], fg=self.colors["red"], font=("Tahoma", 10, "bold")).pack(side="left", padx=10)
            tk.Label(matchup, text=f"{right_copy}\n{right_role}", bg=self.colors["panel_dark"], fg=self.colors["gold"] if right_role else self.colors["text"], font=("Tahoma", 11, "bold"), justify="left").pack(side="left", fill="x", expand=True, padx=12, pady=9)
            review_body = ttk.Frame(review, style="Chrome.TFrame")
            review_body.pack(fill="both", expand=True, padx=8)
            review_text = tk.Text(review_body, wrap="word", bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], font=("Tahoma", 11), padx=14, pady=12, spacing3=3)
            review_scroll = ttk.Scrollbar(review_body, orient="vertical", command=review_text.yview)
            review_text.configure(yscrollcommand=review_scroll.set)
            review_scroll.pack(side="right", fill="y")
            review_text.pack(side="left", fill="both", expand=True)
            review_text.insert("end", "\n".join(str(line) for line in log.get("lines", [])))
            review_text.config(state="disabled")
            review_actions = ttk.Frame(review, style="Chrome.TFrame")
            review_actions.pack(fill="x", padx=8, pady=8)
            ttk.Label(review_actions, text="Stored commentary and official scorecards from this completed bout", style="Panel.TLabel").pack(side="left", padx=4)
            ttk.Button(review_actions, text="Close Review", style="Accent.TButton", command=review.destroy).pack(side="right", padx=4)

        ttk.Button(controls, text="Start Next Fight", style="Accent.TButton", command=start_next_fight).pack(side="left", padx=4)
        ttk.Button(controls, text="Play Fight", command=start).pack(side="left", padx=4)
        pause_button = ttk.Button(controls, text="Pause", command=pause_resume)
        pause_button.pack(side="left", padx=4)
        auto_var = tk.BooleanVar(value=bool(self.rules.get("live_auto_play_card", False)))

        def toggle_auto():
            state["auto"] = bool(auto_var.get())
            self.rules["live_auto_play_card"] = state["auto"]
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
        ttk.Label(controls2, text="Beat pace (ms)", style="Panel.TLabel").pack(side="left", padx=(12, 2))
        speed_var = tk.IntVar(value=state["delay"])
        ttk.Spinbox(controls2, from_=300, to=3000, increment=100, textvariable=speed_var, width=6, command=apply_speed).pack(side="left", padx=2)
        ttk.Button(controls2, text="Apply", command=apply_speed).pack(side="left", padx=4)

        def change_font(delta):
            size = max(9, min(16, font_size.get() + delta))
            font_size.set(size)
            text.configure(font=("Tahoma", size))
            text.tag_configure("heading", font=("Tahoma", size + 1, "bold"))
            text.tag_configure("result", font=("Tahoma", size + 1, "bold"))
            text.tag_configure("round", font=("Tahoma", size, "bold"))
            text.tag_configure("analysis", font=("Tahoma", max(9, size - 1), "italic"))
            text.tag_configure("knockdown", font=("Tahoma", size, "bold"))
            text.tag_configure("finish", font=("Tahoma", size + 1, "bold"))
            text.tag_configure("referee", font=("Tahoma", size, "bold"))

        ttk.Button(controls2, text="Text -", command=lambda: change_font(-1)).pack(side="left", padx=(12, 2))
        ttk.Button(controls2, text="Text +", command=lambda: change_font(1)).pack(side="left", padx=2)
        def toggle_follow():
            self.rules["live_follow_commentary"] = bool(follow_var.get())
            if follow_var.get():
                text.see("end")

        ttk.Checkbutton(controls2, text="Follow live", variable=follow_var, command=toggle_follow).pack(side="left", padx=8)

        skip_event_button = ttk.Button(controls3, text="Skip Event", command=skip_to_end)
        skip_event_button.pack(side="left", padx=4)
        update_event_button_label()
        ttk.Button(controls3, text="Review Selected Bout", command=review_selected_bout).pack(side="left", padx=4)
        fight_list.bind("<Double-1>", review_selected_bout)
        if package.get("tournament_brackets"):
            ttk.Button(controls3, text="View Bracket", command=lambda: self.open_event_tournament_bracket(package, window)).pack(side="left", padx=4)
        status_label = tk.Label(controls3, text="Ready", bg=self.colors["chrome"], fg=self.colors["muted"], font=("Tahoma", 9, "bold"), anchor="w")
        status_label.pack(side="left", fill="x", expand=True, padx=12)
        close_button = ttk.Button(controls3, text="Close", style="Accent.TButton", command=close_window)
        close_button.pack(side="right", padx=4)
        window.protocol("WM_DELETE_WINDOW", close_window)

    def sign_fighter(self):
        selected = self.market_tree.selection()
        if not selected:
            return
        fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
        if fighter not in self.free_agents:
            self.refresh_market()
            return
        signing_bonus = fighter.purse * 2
        if self.cash < signing_bonus:
            messagebox.showwarning("Not enough cash", f"Signing {fighter.name} requires a ${signing_bonus:,} bonus.")
            return
        self.cash -= signing_bonus
        self.record_finance_transaction(f"Signing bonus: {fighter.name}", costs=signing_bonus)
        self.free_agents.remove(fighter)
        self.clear_ai_contract_offer(fighter)
        # AI roster caps prevent market hoarding; player-controlled promotions
        # are deliberately uncapped, including after a company takeover.
        fighter.contract_months = random.randint(10, 24)
        fighter.morale = min(100, fighter.morale + 8)
        self.roster.append(fighter)
        self.event_log.append(f"Signed {fighter.name} to a {fighter.contract_months}-month ${fighter.purse:,}/fight contract.")
        self.news.insert(0, f"{self.player_company_name} signed {fighter.name}, a {fighter.style} {fighter.weight} with {fighter.trait.lower()} reputation.")
        self.refresh_all()
        self.write_log()

    def open_contract_negotiation(self, fighter, existing=False, comeback=False, farewell=False, source_promotion=None, transfer_deal=None):
        # A farewell deal is a comeback that resolves in a single retirement bout
        # rather than a multi-fight commitment.
        if farewell:
            comeback = True
        prior_comeback_guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        prior_comeback_completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
        report = self.scouting_report_for(fighter)
        ratings_known = existing or not self.rules.get("scouting_mode", False) or report.get("reveal", 0) >= 100
        window = tk.Toplevel(self.root)
        window.title(f"Negotiate - {fighter.name}")
        window.geometry("660x600")
        window.minsize(600, 560)
        window.configure(bg=self.colors["chrome"])
        active_offer_company = getattr(fighter, "ai_offer_company", "") if not existing and not comeback else ""
        active_offer_purse = getattr(fighter, "ai_offer_purse", 0) if active_offer_company else 0
        rival = next((promo for promo in self.promotions if promo.name == active_offer_company), None) or random.choice([promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)])
        leverage = 1 + fighter.popularity / 140 + (0.35 if fighter.champion else 0) + max(0, fighter.momentum) * 0.05
        if comeback:
            leverage += 0.28
        loyalty = 0.82 if existing else 1.0
        ask = max(4000, round(fighter.purse * leverage * loyalty), round(active_offer_purse * 1.05) if active_offer_purse else 0)
        purse_var = tk.IntVar(value=ask)
        term_var = tk.IntVar(value=max(8, min(30, fighter.contract_months if existing else 12)))
        fights_var = tk.IntVar(value=5 if (existing or comeback) else 3)
        bonus_var = tk.IntVar(value=15)
        signing_var = tk.IntVar(value=max(0, round(ask * (0.75 if comeback else 0.5) / 1000) * 1000))
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
        if fighter.age > 34 or comeback:
            wants.append("guaranteed fights")
        if fighter.professionalism > 72:
            wants.append("clear terms")
        if not wants:
            wants.append("fair money")
        relation_discount = self.staff_effect("Talent Relations", 2600)
        state = {"attempts": 3, "target": ask + fighter.popularity * 420 + fighter.professionalism * 180 - relation_discount + (12000 if comeback else 0),
                 "rival_bid": 0}

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"NEGOTIATION: {fighter.name}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        rival_text = ("A comeback requires a convincing financial and career package; the fighter stays retired if talks fail."
                      if comeback else f"Live rival offer: {rival.name} is offering ${active_offer_purse:,}/fight for {fighter.ai_offer_months} months; you can beat it before next month."
                      if active_offer_purse else ("Renewal talks start warmer because they already work here." if existing else f"{rival.name} may bid if talks drag."))
        rating_line = (
            f"OVR {fighter.overall} | Pop {fighter.popularity} | Morale {fighter.morale}"
            if ratings_known else
            f"Ability and business ratings hidden | Scout confidence {report.get('reveal', 0)}%"
        )
        scout_warning = "" if ratings_known else "\nYou may negotiate now, but you are pricing risk without a full scouting report."
        status_line = ("Retired athlete signing for one final farewell bout" if farewell
                       else "Retired athlete considering a comeback" if comeback
                       else f"Transfer agreement in place with {transfer_deal['source'].name}" if transfer_deal
                       else f"Regional prospect under developmental terms with {source_promotion.name}" if source_promotion
                       else "Active contract discussion")

        profile = tk.Frame(body, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        profile.pack(fill="x", padx=8, pady=(8, 8))
        portrait = tk.Canvas(profile, width=98, height=98, highlightthickness=1, highlightbackground=self.colors["line"], bg="#222222")
        portrait.pack(side="left", padx=10, pady=10)
        bg = fighter.portrait_bg or "#222222"
        accent = fighter.portrait_accent or self.colors["gold"]
        portrait.configure(bg=bg)
        portrait.create_rectangle(8, 8, 90, 90, fill=bg, outline=accent, width=2)
        portrait.create_oval(33, 16, 65, 48, fill=accent, outline="")
        portrait.create_polygon(18, 84, 30, 54, 68, 54, 80, 84, fill="#d7d7d7", outline="")
        portrait.create_rectangle(16, 82, 82, 91, fill=accent, outline="")
        initials = "".join(part[0] for part in fighter.name.replace("'", "").split()[:2]).upper()
        portrait.create_text(49, 33, text=initials, fill=bg, font=("Impact", 14))
        if hasattr(self, "fit_canvas_text"):
            self.fit_canvas_text(portrait, 49, 87, self.portrait_badge_text(fighter), bg, 58, base_size=6)
        if hasattr(self, "draw_portrait_status_markers"):
            self.draw_portrait_status_markers(portrait, fighter, large=False)

        summary = tk.Frame(profile, bg=self.colors["panel_dark"])
        summary.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        name_row = tk.Frame(summary, bg=self.colors["panel_dark"])
        name_row.pack(fill="x")
        tk.Label(name_row, text=fighter.name.upper(), bg=self.colors["panel_dark"], fg=self.colors["gold"],
                 font=("Impact", 18), anchor="w").pack(side="left")
        tk.Label(name_row, text=f"Age {fighter.age} | {fighter.gender} {fighter.weight}", bg=self.colors["panel_dark"], fg=self.colors["muted"],
                 font=("Tahoma", 9, "bold"), anchor="e").pack(side="right", padx=(8, 0))
        tk.Label(summary, text=status_line, bg=self.colors["panel_dark"], fg=self.colors["text"],
                 font=("Tahoma", 9, "bold"), anchor="w").pack(fill="x", pady=(1, 6))

        def chip(parent, label, value, accent=None):
            frame = tk.Frame(parent, bg=accent or self.colors["chrome"], highlightthickness=1, highlightbackground=self.colors["line"])
            frame.pack(side="left", padx=(0, 5), pady=2)
            tk.Label(frame, text=label.upper(), bg=frame["bg"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).pack(side="left", padx=(6, 3), pady=3)
            tk.Label(frame, text=str(value), bg=frame["bg"], fg=self.colors["text"], font=("Tahoma", 8, "bold")).pack(side="left", padx=(0, 6), pady=3)

        chips = tk.Frame(summary, bg=self.colors["panel_dark"])
        chips.pack(fill="x")
        chip(chips, "Record", fighter.record)
        if ratings_known:
            chip(chips, "OVR", fighter.overall)
            chip(chips, "Pop", fighter.popularity)
            chip(chips, "Morale", fighter.morale)
        else:
            chip(chips, "Intel", f"{report.get('reveal', 0)}% scout")
            chip(chips, "Ratings", "Hidden")
        if hasattr(self, "fighter_current_championships"):
            titles = self.fighter_current_championships(fighter)
            if titles:
                chip(chips, "Champion", titles[0].replace(" Champion", ""), "#4b3512")
        chip(chips, "Ask", f"${ask:,}/fight", "#25384a")

        meta = tk.Frame(summary, bg=self.colors["panel_dark"])
        meta.pack(fill="x", pady=(7, 0))
        goal_text = f"{career_goal or 'Undeclared'} ({getattr(fighter, 'career_goal_progress', 0)}%)"
        tk.Label(meta, text=f"Agent: {fighter.agent_name}", bg=self.colors["panel_dark"], fg=self.colors["text"],
                 font=("Tahoma", 8, "bold"), anchor="w").pack(side="left", padx=(0, 12))
        tk.Label(meta, text=f"Style: {persona}", bg=self.colors["panel_dark"], fg=self.colors["text"],
                 font=("Tahoma", 8, "bold"), anchor="w").pack(side="left", padx=(0, 12))
        tk.Label(meta, text=f"Goal: {goal_text}", bg=self.colors["panel_dark"], fg=self.colors["text"],
                 font=("Tahoma", 8, "bold"), anchor="w").pack(side="left")

        priorities = tk.Frame(body, bg=self.colors["chrome"])
        priorities.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(priorities, text="CAMP PRIORITIES", bg=self.colors["chrome"], fg=self.colors["muted"],
                 font=("Tahoma", 8, "bold")).grid(row=0, column=0, sticky="nw", padx=(2, 8), pady=2)
        priority_wrap = tk.Frame(priorities, bg=self.colors["chrome"])
        priority_wrap.grid(row=0, column=1, sticky="ew")
        priorities.grid_columnconfigure(1, weight=1)
        for index, want in enumerate(dict.fromkeys(wants)):
            tk.Label(priority_wrap, text=want, bg="#2b333d", fg=self.colors["text"], font=("Tahoma", 8, "bold"),
                     padx=7, pady=3).grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 5), pady=2)

        context = tk.Frame(body, bg="#243140" if ratings_known else "#4a311d", highlightthickness=1, highlightbackground=self.colors["line"])
        context.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(context, text=f"{rival_text}{scout_warning}", bg=context["bg"], fg=self.colors["text"],
                 font=("Tahoma", 8, "bold"), anchor="w", justify="left", wraplength=610, padx=8, pady=6).pack(fill="x")

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

        grid = tk.Frame(body, bg=self.colors["panel"])
        grid.pack(fill="x", padx=8)
        terms_panel = tk.Frame(grid, bg=self.colors["panel"])
        terms_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        upside_panel = tk.Frame(grid, bg=self.colors["panel"])
        upside_panel.pack(side="left", fill="both", expand=True)
        tk.Label(terms_panel, text="BASE PACKAGE", bg=self.colors["panel"], fg=self.colors["gold"], font=("Impact", 10), anchor="w").pack(fill="x", pady=(0, 3))
        tk.Label(upside_panel, text="UPSIDE / PROMISES", bg=self.colors["panel"], fg=self.colors["gold"], font=("Impact", 10), anchor="w").pack(fill="x", pady=(0, 3))

        def attach_tooltip(widget, tip_text):
            """Small themed hover help for dense negotiation controls."""
            holder = {"window": None}
            def show(_event=None):
                if holder["window"] or not widget.winfo_exists():
                    return
                popup = tk.Toplevel(window)
                popup.overrideredirect(True)
                popup.configure(bg=self.colors["panel_dark"])
                popup.attributes("-topmost", True)
                x = widget.winfo_rootx() + 12
                y = widget.winfo_rooty() + widget.winfo_height() + 6
                popup.geometry(f"+{x}+{y}")
                tk.Label(popup, text=tip_text, bg=self.colors["panel_dark"], fg=self.colors["text"],
                         font=("Tahoma", 8, "bold"), justify="left", wraplength=310,
                         padx=8, pady=6, highlightthickness=1, highlightbackground=self.colors["gold"]).pack()
                holder["window"] = popup
            def hide(_event=None):
                popup = holder.get("window")
                holder["window"] = None
                if popup and popup.winfo_exists():
                    popup.destroy()
            widget.bind("<Enter>", show, add="+")
            widget.bind("<Leave>", hide, add="+")
            widget.bind("<ButtonPress>", hide, add="+")

        for label, var, lo, hi, step, parent in (
                ("Purse / fight", purse_var, 1, 600000, 1000, terms_panel),
                ("Signing bonus", signing_var, 0, 400000, 1000, terms_panel),
                *(([]) if comeback else [("Contract months", term_var, 1, 60, 1, terms_panel)]),
                ("Guaranteed fights", fights_var, 1, 12, 1, terms_panel),
                ("Finish bonus %", bonus_var, 0, 60, 1, upside_panel),
                ("Win bonus $", win_bonus_var, 0, 300000, 1000, upside_panel),
                ("PPV points %", ppv_var, 0, 15, 1, upside_panel)):
            row = tk.Frame(parent, bg=self.colors["panel"])
            row.pack(fill="x", pady=2)
            label_widget = tk.Label(row, text=label, width=16, bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 8, "bold"), anchor="w")
            label_widget.pack(side="left")
            input_widget = ttk.Spinbox(row, from_=lo, to=hi, increment=step, textvariable=var, width=11)
            input_widget.pack(side="right", padx=2)
            if label == "Guaranteed fights" and comeback:
                tip = ("Comeback commitment: this is the number of official fights in this new deal. "
                       "After the final fight, choose another comeback deal from the profile or book one farewell bout.")
                attach_tooltip(label_widget, tip)
                attach_tooltip(input_widget, tip)
        clause_row = tk.Frame(body, bg=self.colors["panel"])
        clause_row.pack(fill="x", padx=8, pady=(7, 2))
        for text, var in (
                ("Exclusive", exclusive_var),
                ("Champion's clause", champ_clause_var),
                ("Guaranteed title shot", title_shot_var),
                ("Main-event promise", main_event_promise_var),
                ("Top-opponent promise", top_opponent_promise_var)):
            ttk.Checkbutton(clause_row, text=text, variable=var).pack(side="left", padx=(0, 8))

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
            if source_promotion is not None and fighter not in source_promotion.roster:
                result_label.config(text=f"{fighter.name} has already left {source_promotion.name}. No money was charged.")
                submit_button.config(state="disabled")
                if hasattr(self, "refresh_regional_prospects"):
                    self.refresh_regional_prospects()
                return
            if source_promotion is not None:
                assessment = self.regional_candidate_assessment(fighter, source_promotion)
                if not assessment["eligible"]:
                    result_label.config(text=f"{fighter.name} is not eligible to sign yet: {assessment['explanation']}.")
                    submit_button.config(state="disabled")
                    if hasattr(self, "refresh_regional_prospects"):
                        self.refresh_regional_prospects()
                    return
            purse, term, fights = purse_var.get(), term_var.get(), fights_var.get()
            bonus, signing, exclusive = bonus_var.get(), signing_var.get(), exclusive_var.get()
            score, target, _pct, unmet = evaluate()
            score += random.randint(-4500, 4500)
            if score >= target:
                signing_cost = purse * (2 if exclusive else 1) + signing
                transfer_cash = int((transfer_deal or {}).get("cash", 0) or 0)
                if self.cash < signing_cost + transfer_cash:
                    result_label.config(text=f"Not enough cash for ${signing_cost + transfer_cash:,} up-front cost.")
                    return
                if transfer_deal is not None:
                    committed, detail = self.commit_player_transfer_deal(transfer_deal, fighter)
                    if not committed:
                        result_label.config(text=detail)
                        submit_button.config(state="disabled")
                        return
                if source_promotion is not None:
                    # The transfer and payment are one decision. If the feeder
                    # no longer owns the fighter, stop before touching cash.
                    if fighter not in source_promotion.roster:
                        result_label.config(text=f"{fighter.name} is no longer available from {source_promotion.name}. No money was charged.")
                        submit_button.config(state="disabled")
                        return
                    self.capture_regional_record(fighter)
                    source_promotion.belts, source_promotion.interim_belts, source_promotion.belt_history = self.vacate_fighter_belts(
                        fighter,
                        source_promotion.roster,
                        source_promotion.belts or {},
                        source_promotion.interim_belts or {},
                        source_promotion.belt_history or {},
                        f"Signed by {self.player_company_name} from the regional circuit.",
                    )
                    source_promotion.roster.remove(fighter)
                    fighter.champion = False
                    fighter.interim_champion = False
                    fighter.last_regional_promotion = source_promotion.name
                    fighter.regional_departure_month = self.month
                    fighter.market_origin = "Player regional signing"
                    if fighter not in self.roster:
                        self.roster.append(fighter)
                self.cash -= signing_cost
                self.record_finance_transaction(f"Contract agreement: {fighter.name}", costs=signing_cost)
                if comeback:
                    if fighter in self.retired_fighters:
                        self.retired_fighters.remove(fighter)
                    fighter.retired = False
                    fighter.retirement_reason = ""
                    fighter.retirement_pending = False
                    fighter.fatigue = 0
                    fighter.injured = 0
                    if fighter not in self.roster:
                        self.roster.append(fighter)
                elif not existing:
                    if source_promotion is None and fighter in self.free_agents:
                        self.free_agents.remove(fighter)
                    if fighter not in self.roster:
                        self.roster.append(fighter)
                fighter.purse = purse
                fighter.contract_months = 0 if comeback else term
                if farewell:
                    # One final retirement bout: no ongoing commitment; the fighter
                    # retires immediately after their next completed fight.
                    fighter.guaranteed_fights = 0
                    fighter.contract_fights_completed = 0
                    fighter.comeback_contract = False
                    fighter.retirement_pending = True
                    fighter.retirement_fight_completed = False
                    fighter.retirement_fight_due_after_month = 0
                    fighter.retirement_requested_month = self.month
                    fighter.retirement_reason = "Signed for one final retirement bout."
                else:
                    comeback_extension = self.extend_comeback_commitment(fighter, fights) if comeback else None
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
                contract_note = (" Farewell bout: they retire immediately after their next fight." if farewell
                                 else " Comeback commitment: retirement is deferred until the guaranteed fights are complete." if comeback else "")
                if comeback and not farewell and comeback_extension:
                    fights_note = f"{comeback_extension['total']} guaranteed comeback fights"
                else:
                    fights_note = "1 farewell bout" if farewell else f"{fights} guaranteed fights"
                duration_note = "fight-counted comeback deal" if comeback else f"{term} months"
                fighter.fight_history.insert(0, f"Signed contract: {duration_note}, {fights_note}, ${purse:,}/fight, ${signing:,} signing bonus, {bonus}% finish bonus.{clause_text}{contract_note}")
                if source_promotion is not None:
                    fighter.fight_history.insert(1, f"Left {source_promotion.name} after a regional record of {fighter.regional_record_w}-{fighter.regional_record_l}-{fighter.regional_record_d}.")
                    self.regional_recruit_fighter(source_promotion, slots=1)
                self.news.insert(0, (f"{fighter.name} signed a one-fight farewell deal with {self.player_company_name} before retiring." if farewell
                                     else f"{fighter.name} came out of retirement to join {self.player_company_name}." if comeback
                                     else f"{fighter.name} left {source_promotion.name} to join {self.player_company_name}." if source_promotion
                                     else f"{fighter.name} agreed terms with {self.player_company_name}."))
                self.refresh_all()
                window.destroy()
                return
            state["attempts"] -= 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + 10)
            # A rival can enter the bidding when talks drag, raising the bar.
            if not existing and not comeback and not active_offer_purse and state["attempts"] == 1 and fighter.popularity > 45 and random.random() < 0.6:
                state["rival_bid"] = round(ask * random.uniform(0.15, 0.4))
                result_label.config(text=f"{rival.name} has entered the bidding! {fighter.name} now wants more to stay. Attempts left: {state['attempts']}")
                refresh_meter()
                return
            if state["attempts"] <= 0:
                if active_offer_purse:
                    result_label.config(text=f"Your talks ended. {rival.name}'s live offer remains in place until next month.")
                elif not existing and not comeback and source_promotion is None and state["rival_bid"] and random.random() < 0.5:
                    rival_purse = max(round(ask * 1.08 / 500) * 500, fighter.purse)
                    rival_term = random.randint(10, 22)
                    rival_bonus = max(rival_purse, round(rival_purse * random.uniform(0.8, 1.5) / 500) * 500)
                    signed, detail = self.complete_ai_free_agent_signing(
                        fighter, rival, rival_purse, rival_term, rival_bonus,
                        source="Won the bidding after player negotiations broke down",
                    )
                    result_label.config(text=(f"{fighter.name} signed with {rival.name} instead." if signed else f"{rival.name}'s bid collapsed: {detail}"))
                else:
                    result_label.config(text=(f"{fighter.name} stays retired. The comeback package was not convincing enough." if comeback else f"{fighter.name}'s camp walks away. They wanted a stronger package."))
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
        fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
        if fighter not in self.free_agents:
            self.refresh_market()
            messagebox.showinfo("Negotiations", "That fighter is no longer available.")
            return
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
                self.record_finance_transaction(f"Negotiated signing: {fighter.name}", costs=signing_bonus)
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

    def fight_hype(self, a, b, fight, rank_map=None):
        title = 12 if fight.get("title") else 0
        main = 8 if fight.get("main") else 0
        tier_factor = {"Main Card": 1.0, "Prelims": 0.72, "Early Prelims": 0.48}.get(fight.get("tier", "Main Card"), 1.0)
        rivalry = abs(a.momentum - b.momentum) + self.rivalry_heat_between(a, b) * 0.28
        media = self.match_build_score(a, b, fight, rank_map=rank_map) * 0.18
        rank_bonus = 0
        for fighter in (a, b):
            rank = rank_map.get(self.fighter_identity_key(fighter)) if rank_map is not None else None
            rank = rank if rank is not None else self.division_rank_number(fighter)
            if fighter.champion:
                rank_bonus += 7
            elif rank and rank <= 5:
                rank_bonus += 5
            elif rank and rank <= 10:
                rank_bonus += 3
        marketing_lift = self.staff_effect("Marketing", 0.45)
        return max(1, round(((a.popularity + b.popularity) / 2 + title + main + rivalry / 2 + media + rank_bonus + marketing_lift) * tier_factor))

    def division_rank_number(self, fighter):
        if fighter.champion:
            return 0
        division = sorted(
            [f for f in self.roster if f.weight == fighter.weight and f.gender == fighter.gender and not f.champion],
            key=lambda item: self.rank_value(item), reverse=True,
        )
        for index, item in enumerate(division, 1):
            if item is fighter or self.fighter_identity_key(item) == self.fighter_identity_key(fighter):
                return index
        return None

    def player_division_rank_map(self):
        """Build all player-roster division ranks in one pass for dense tables."""
        groups = {}
        for fighter in self.roster:
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        ranks = {}
        for fighters in groups.values():
            for fighter in fighters:
                if fighter.champion:
                    ranks[self.fighter_identity_key(fighter)] = 0
            contenders = sorted((fighter for fighter in fighters if not fighter.champion), key=self.rank_value, reverse=True)
            for index, fighter in enumerate(contenders, 1):
                ranks[self.fighter_identity_key(fighter)] = index
        return ranks

    def division_rank_label(self, fighter):
        if fighter.champion:
            return "C"
        rank = self.division_rank_number(fighter)
        return f"#{rank}" if rank else "-"

    def fight_build_score(self, fighter, rank=None):
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
        rank = rank or self.division_rank_number(fighter) or 25
        rank_bonus = 12 if fighter.champion else max(0, 12 - rank)
        finish_bonus = max(0, fighter.power + fighter.submissions - 130) * 0.12
        return max(1, min(99, round(fighter.popularity * 0.5 + fighter.star_quality * 0.22 + fighter.charisma * 0.12 + media + streak + rank_bonus + trait_bonus + finish_bonus)))

    def match_build_score(self, a, b, fight, rank_map=None):
        style_clash = 6 if a.style != b.style else 1
        rivalry = 10 + self.rivalry_heat_between(a, b) * 0.22 if a.rival == b.name or b.rival == a.name else 0
        stakes = (10 if fight.get("title") else 0) + (6 if fight.get("main") else 0)
        competitiveness = max(0, 18 - abs(a.overall - b.overall))
        matchmaker_lift = self.staff_effect("Matchmaker", 0.28)
        rank_a = rank_map.get(self.fighter_identity_key(a)) if rank_map is not None else None
        rank_b = rank_map.get(self.fighter_identity_key(b)) if rank_map is not None else None
        return max(1, min(99, round((self.fight_build_score(a, rank_a) + self.fight_build_score(b, rank_b)) / 2 + style_clash + rivalry + stakes + competitiveness * 0.35 + matchmaker_lift)))

    def run_event(self):
        if len(self.booked) < 1:
            messagebox.showinfo("No fights", "Book at least one fight before running an event.")
            return
        self.normalize_card_order()
        current_name = self.event_name.get().strip()
        event_name = self.default_event_name(self.next_player_event_number()) if self.is_auto_event_name(current_name) else current_name
        immediate_fights = []
        for booked_fight in self.booked:
            snapshot = dict(booked_fight)
            snapshot["fighter_ids"] = [
                getattr(self.get_fighter(reference), "fighter_id", "") if reference != "TBA" else ""
                for reference in self.event_fight_participants(snapshot)
            ]
            immediate_fights.append(snapshot)
        event = {"name": event_name, "venue": self.venue.get(), "region": self.event_region.get(), "city": self.event_city.get(), "month": self.month, "week": self.week, "fights": immediate_fights}
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

    def fight_corner_title_statuses(self, fight, a, b):
        """Snapshot each corner's championship role before the result changes any belts."""
        special_name = str(fight.get("special_belt", "") or "")
        special_holder = ""
        if special_name:
            belt = self.normalize_special_belts(getattr(self, "special_belts", {})).get(special_name, {})
            special_holder = str(belt.get("holder", "") or "")
        divisional_stakes = bool(fight.get("divisional_title", fight.get("title") and not special_name))
        interim_stakes = bool(fight.get("interim"))

        def status(fighter):
            labels = []
            if getattr(fighter, "retirement_pending", False):
                labels.append("RETIREMENT FIGHT")
            if special_name and fighter.name == special_holder:
                labels.append(f"{special_name.upper()} CHAMPION")
            if divisional_stakes:
                if interim_stakes and fighter.interim_champion:
                    labels.append("INTERIM CHAMPION")
                elif interim_stakes and fighter.champion:
                    labels.append("UNDISPUTED CHAMPION")
                elif interim_stakes:
                    labels.append("INTERIM TITLE CHALLENGER")
                elif fighter.champion:
                    labels.append("UNDISPUTED CHAMPION")
                elif fighter.interim_champion:
                    labels.append("INTERIM CHAMPION")
                else:
                    labels.append("TITLE CHALLENGER")
            elif interim_stakes:
                labels.append("INTERIM CHAMPION" if fighter.interim_champion else "INTERIM TITLE CHALLENGER")
            elif fighter.champion:
                labels.append("CHAMPION - NON-TITLE BOUT")
            elif fighter.interim_champion:
                labels.append("INTERIM CHAMPION - NON-TITLE BOUT")
            if special_name and fighter.name != special_holder:
                labels.append(f"{special_name.upper()} CHALLENGER")
            return "  |  ".join(dict.fromkeys(labels))

        return status(a), status(b)

    def player_bout_purse_factor(self, fight):
        """Player cards pay less for lower-card placement; AI finance has its own model."""
        return {"Prelims": 0.75, "Early Prelims": 0.55}.get(str(fight.get("tier", "Main Card") or "Main Card"), 1.0)

    def player_bout_purse_cost(self, fight, a, b):
        return round((a.purse + b.purse) * self.player_bout_purse_factor(fight))

    def prepare_event_result(self, event):
        # A player-arranged card is not re-sorted on fight night. The top row
        # is the main event, and therefore the name and watch order source.
        # Title changes decided tonight are dated to the day this card runs.
        self._active_card_day = self.event_day(event)
        self.normalize_card_order(event.get("fights", []))
        self.refresh_scheduled_event_auto_name(event)
        log = [f"{event['name']} - {event['venue']} ({self.event_date_label(event)})", "=" * 72]
        press_log, press_hype = self.run_press_conference(event)
        log.extend(press_log)
        weigh_log, purse_penalty, cancelled_fights = self.run_weigh_ins(event)
        log.extend(weigh_log)
        total_hype = press_hype
        total_cost = -purse_penalty
        total_contract_cost = -purse_penalty
        total_build = 0
        total_excitement = 0
        results = []
        award_pool = []
        fight_logs = []
        tournament_brackets = []
        ordered = self.event_fight_order(event["fights"])
        for fight in ordered:
            if fight in cancelled_fights:
                cancellation = dict(fight.get("_cancellation", {}) or {})
                names = list(fight.get("fighters", []))
                lines = [
                    f"CANCELLED BOUT: {' vs '.join(names)}",
                    cancellation.get("reason", "The commission cancelled the bout after weigh-ins."),
                ]
                if cancellation.get("weigh_in"):
                    lines.append(f"Weigh-in: {cancellation['weigh_in']}")
                if cancellation.get("resolution"):
                    lines.append(f"Next step: {cancellation['resolution']}")
                a = self.get_fighter(names[0]) if names else None
                b = self.get_fighter(names[1]) if len(names) > 1 else None
                a_status, b_status = self.fight_corner_title_statuses(fight, a, b) if a and b else ("", "")
                fight_logs.append({
                    "heading": lines[0], "lines": lines, "cancelled": True,
                    "a": names[0] if names else "", "b": names[1] if len(names) > 1 else "",
                    "a_id": getattr(a, "fighter_id", ""), "b_id": getattr(b, "fighter_id", ""),
                    "a_record": getattr(a, "record", ""), "b_record": getattr(b, "record", ""),
                    "a_rating": self.bout_rating_snapshot(a) if a else {}, "b_rating": self.bout_rating_snapshot(b) if b else {},
                    "weight": getattr(a, "weight", fight.get("tba_weight", "")), "label": "CANCELLED BOUT",
                    "a_title_status": a_status, "b_title_status": b_status,
                    "result": "Cancelled - no contest took place",
                })
                continue
            if fight.get("tournament"):
                tournament = self.simulate_event_tournament(event, fight)
                results.extend(tournament["results"])
                award_pool.extend(tournament["award_pool"])
                fight_logs.extend(tournament["fight_logs"])
                tournament_brackets.append(tournament["bracket"])
                total_hype += tournament["hype"]
                total_build += tournament["build"]
                total_excitement += tournament["excitement"]
                total_cost += tournament["cost"]
                total_contract_cost += tournament.get("contracted_cost", tournament["cost"])
                log.extend(["", tournament["bracket"]["title"].upper(), "-" * 72])
                for stage in tournament["bracket"]["stages"]:
                    log.append(stage["name"])
                    log.extend(f"  {match['summary']}" for match in stage["matches"])
                log.append(f"  GRAND PRIX CHAMPION: {tournament['bracket']['champion']}")
                continue
            fight = dict(fight)
            # Player-event post-processing still needs both fighters for contract
            # clauses, awards, regional effects and the final recap.  Defer a
            # pending retirement until finish_event has completed those steps.
            fight["_defer_retirement"] = True
            fight.setdefault("region", event.get("region", self.venue_region(event["venue"])))
            fight.setdefault("city", event.get("city", ""))
            a, b = self.resolve_fight_fighters(fight)
            a_title_status, b_title_status = self.fight_corner_title_statuses(fight, a, b)
            a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
            hype = self.fight_hype(a, b, fight)
            build = self.match_build_score(a, b, fight)
            total_hype += hype
            total_build += build
            total_contract_cost += a.purse + b.purse
            total_cost += self.player_bout_purse_cost(fight, a, b)
            a_start_gas = round(self.starting_fight_gas(a))
            b_start_gas = round(self.starting_fight_gas(b))
            winner, loser, method, round_no, commentary = self.simulate_fight(a, b, fight)
            fight["_scorecards"] = self.scorecard_summary_from_lines(commentary)
            excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, hype)
            total_excitement += excitement
            results.append((winner, loser, fight, method))
            award_pool.append({"winner": winner.name if method != "Draw" else "", "loser": loser.name if method != "Draw" else "", "fighters": [a.name, b.name], "method": method, "excitement": excitement, "round": round_no, "fight": f"{a.name} vs {b.name}"})
            label = f"{fight['special_belt'].upper()} TITLE FIGHT" if fight.get("special_belt") else ("MAIN EVENT" if fight["main"] else ("TITLE FIGHT" if fight["title"] else "BOUT"))
            if fight.get("special_belt") and fight.get("divisional_title"):
                label += " + " + ("INTERIM TITLE" if fight.get("interim") else "DIVISIONAL TITLE")
            if fight.get("interim") and not fight.get("special_belt"):
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
                "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id, "a_record": a.record, "b_record": b.record,
                "a_rating": a_rating, "b_rating": b_rating,
                "weight": a.weight, "label": label, "title": bool(fight.get("title", False)), "divisional_title": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))), "interim": bool(fight.get("interim", False)), "special_belt": str(fight.get("special_belt", "") or ""), "result": result_text, "excitement": excitement,
                "a_title_status": a_title_status, "b_title_status": b_title_status,
                "a_start_gas": a_start_gas, "b_start_gas": b_start_gas, "scorecards": fight["_scorecards"],
            })
            log.append("\n" + lines[0])
            log.extend(f"  {line}" for line in lines[1:])

        completed = max(1, len(results))
        avg_hype = total_hype / completed
        avg_build = total_build / completed
        avg_excitement = total_excitement / completed
        regional_pull = self.regional_market_score(event.get("region", self.venue_region(event["venue"])))
        finance = self.calculate_event_finance(
            total_hype, total_cost, event, results, avg_excitement, avg_build, regional_pull,
            contracted_fighter_pay=total_contract_cost,
        )
        media_outcome = self.calculate_event_media_outcome(event, {
            "finance": finance, "fight_count": len(results),
            "average_excitement": avg_excitement, "average_build": avg_build,
        })
        performance_bonus = int(media_outcome.get("performance_bonus", 0))
        if performance_bonus:
            finance["broadcast_income"] += performance_bonus
            finance["total_revenue"] += performance_bonus
            finance["profit"] += performance_bonus
        finance["media_outcome"] = dict(media_outcome)
        awards = self.choose_event_awards(award_pool)
        gate = finance["ticket_revenue"]
        profit = finance["profit"]
        mismatch_penalty = self.card_mismatch_penalty(results)
        attendance_ratio = finance["attendance"] / max(1, finance["venue_capacity"])
        # Credibility growth for a completed show. The old model measured hype and
        # excitement against global-average baselines a small promotion can never
        # reach — and because hype is itself depressed by low popularity, a healthy
        # regional promotion bled down to 1% no matter how well it ran. Reward the
        # things a small show can actually control (a strong local draw, a full
        # house, an entertaining, profitable card) with size-appropriate baselines,
        # and give a fading head-start so a promotion can climb out of the basement.
        pop_delta = ((avg_hype - 43) / 15
                     + (avg_excitement - 44) / 16
                     + (regional_pull - 1) * 1.6
                     + attendance_ratio * 1.8
                     + (0.4 if profit > 0 else -0.7))
        if self.company_pop < 40:
            pop_delta += 0.6 * (1 - self.company_pop / 40)
        projected_pop = min(100, max(1, self.company_pop + round(pop_delta)))
        stability_delta = (profit / 300000
                           + (avg_excitement - 40) / 24
                           + attendance_ratio * 2.2
                           - 0.3
                           - mismatch_penalty * 0.28)
        projected_stability = min(100, max(1, self.company_stability + round(stability_delta)))
        log.append("\n" + "=" * 72)
        log.append(f"Event hype {round(avg_hype)} | Fight build {round(avg_build)} | Fight excitement {round(avg_excitement)} | Regional pull x{regional_pull:.2f} | Media reach {finance['media_reach']}")
        log.append(f"Media report: {media_outcome['outlet']} | rating {media_outcome['rating']} | estimated viewers {media_outcome['viewers']:,} | contract {'delivered' if media_outcome['delivered'] else media_outcome['reason']} | relationship {media_outcome['relationship_delta']:+}")
        atmosphere = finance.get("atmosphere", {})
        log.append(f"Crowd atmosphere: {atmosphere.get('mood', 'Engaged')} ({atmosphere.get('intensity', 50)}/100) — {atmosphere.get('identity', 'Local MMA community')}; preference: {atmosphere.get('preference', 'Competitive fights')}.")
        log.append(f"Attendance: {finance['attendance']:,} / {finance['venue_capacity']:,} | Ticket price ${finance['ticket_price']:,} | Mismatch penalty {mismatch_penalty}")
        log.append(f"Gate: ${finance['ticket_revenue']:,} | Broadcast: ${finance['broadcast_income']:,} | Sponsors: ${finance['sponsorship']:,} | Merch: ${finance['merchandise']:,}")
        log.append(f"Fighter pay: ${finance['fighter_pay']:,} | Lower-card savings: ${finance.get('tier_purse_savings', 0):,} | Bonuses: ${finance['bonuses']:,} | Production: ${finance['production']:,} | Medical: ${finance['medical']:,} | Marketing: ${finance['marketing']:,} | Tax: ${finance['tax']:,}")
        log.append(f"Total revenue: ${finance['total_revenue']:,} | Total expense: ${finance['total_expense']:,} | Profit: ${profit:,}")
        log.append(f"Company popularity will move from {self.company_pop} to {projected_pop}. Stability will move from {self.company_stability} to {projected_stability}.")
        tournament_note = f", {len(tournament_brackets)} tournament(s)" if tournament_brackets else ""
        summary = f"{event['name']} ({event['venue']}, {self.event_date_label(event)}): {len(results)} fights{tournament_note}, excitement {round(avg_excitement)}, gate ${gate:,}, profit ${profit:,}, popularity {projected_pop}%, stability {projected_stability}%"
        package = {
            "log": log,
            "results": results,
            "gate": gate,
            "profit": profit,
            "finance": finance,
            "projected_pop": projected_pop,
            "projected_stability": projected_stability,
            "starting_pop": self.company_pop,
            "starting_stability": self.company_stability,
            "starting_cash": self.cash,
            "average_excitement": avg_excitement,
            "awards": awards,
            "fight_count": len(results),
            "fight_logs": fight_logs,
            "tournament_brackets": tournament_brackets,
            "award_pool": award_pool,
            "weigh_in_log": weigh_log,
            "event_name": event["name"],
            "venue": event["venue"],
            "region": event.get("region", self.venue_region(event["venue"])),
            "city": event.get("city", ""),
            "month": event["month"],
            "week": event.get("week", 1),
            "day": self.event_day(event),
            "summary": summary,
            "media_outcome": media_outcome,
        }
        self._active_card_day = None
        return package

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
        # Booking order is headline-first for quick card management. Fight-night
        # order is the inverse: early prelims open and the main event closes.
        return list(reversed(fights))

    def fight_night_log_order(self, fight_logs):
        """Return a watch queue with the declared main event in the final slot."""
        logs = list(fight_logs or [])
        if len(logs) < 2:
            return logs
        main_indices = [
            index for index, row in enumerate(logs)
            if "MAIN EVENT" in str(row.get("label", "")).upper()
            and "CO-MAIN" not in str(row.get("label", "")).upper()
        ]
        if not main_indices or main_indices[-1] == len(logs) - 1:
            return logs
        # Current and legacy cards normally store the whole bill headline-first,
        # so reversing also restores co-main/main-card/prelim progression. For a
        # malformed mixed-order archive, preserve every non-main bout and move
        # only the declared headline to the end.
        if main_indices == [0]:
            return list(reversed(logs))
        mains = [row for index, row in enumerate(logs) if index in main_indices]
        undercard = [row for index, row in enumerate(logs) if index not in main_indices]
        return undercard + mains

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
        penalty = self.division_size_penalty_for(fighter, target_weight)
        if penalty <= 1:
            return True, f"Natural move up: {walk} lb frame can add toward the {target_limit} lb limit over a full camp."
        severity = "manageable" if penalty <= 4 else "clear" if penalty <= 8 else "major"
        return True, (f"Undersized move accepted: {walk} lb walk weight is light for {target_weight}. "
                      f"This creates a {severity} permanent division-fit disadvantage ({penalty}/14) in physical exchanges, initiative, starting condition, and odds.")

    def natural_walk_weight_for(self, fighter, weight):
        """The frame a fighter needs to be a natural fit in a division.

        Has to agree with default_walk_weight, which builds fighters at their
        limit plus four pounds or more: a fighter walks above their class and
        cuts down to it. These two had drifted about twenty-five pounds apart --
        the fit model believed a natural welterweight walked 154lb while the
        generator was making them 174-185lb. Nothing was ever measured as
        undersized as a result, and a fighter "growing into" a division stopped
        growing sixteen pounds below its limit. Kept in one place so the two
        cannot separate again.
        """
        limit = WEIGHT_LIMITS.get(weight, 170)
        if weight == "Heavyweight":
            # The heavyweight limit is a cap rather than a target: nobody cuts
            # to 265, so a natural heavyweight sits well under it.
            return limit - 25
        spread = 10 if limit <= 135 else 15 if limit <= 170 else 22
        if getattr(fighter, "gender", "Male") == "Female":
            spread = max(8, spread - 4)
        return limit + max(4, spread // 3)

    def division_size_penalty_for(self, fighter, target_weight):
        """Return the durable cost of competing below the division's natural size."""
        if fighter.weight not in WEIGHT_LIMITS or target_weight not in WEIGHT_LIMITS:
            return 0
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        natural_size = self.ds(fighter, "natural_size", 50)
        # Measured against the division being entered rather than the direction
        # of travel. A fighter who drops down from heavyweight carrying a
        # lightweight's frame is exactly as undersized as one who climbed up to
        # it, and previously came away with no penalty at all.
        expected_walk = self.natural_walk_weight_for(fighter, target_weight)
        size_gap = max(0, expected_walk - walk)
        frame_gap = max(0, 55 - natural_size)
        return max(0, min(14, round(size_gap / 4.5 + frame_gap / 16)))

    def acclimatize_division_fit(self, fighter):
        """A fighter competing above their natural size slowly grows into the
        division. Their frame fills out (walk weight creeps up toward the class)
        and the durable division-fit penalty eases over months of competing and
        training there, until only a small residual remains for genuinely small
        frames. Called once per month from roster development."""
        penalty = int(getattr(fighter, "division_size_penalty", 0) or 0)
        if penalty <= 0 or getattr(fighter, "retired", False):
            return
        weight = getattr(fighter, "weight", "")
        if weight not in WEIGHT_LIMITS:
            return
        natural_size = self.ds(fighter, "natural_size", 50)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        # Younger fighters with growing frames adapt faster; veterans barely.
        chance = 0.16 + max(0, 30 - fighter.age) * 0.012
        if fighter.age >= 34:
            chance *= 0.45
        chance += (natural_size - 50) * 0.002 + max(0, conditioning - 55) * 0.001
        if random.random() > max(0.03, min(0.5, chance)):
            return
        expected_walk = self.natural_walk_weight_for(fighter, weight)
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        if walk < expected_walk:
            walk = min(expected_walk, walk + random.randint(2, 5))
            fighter.walk_weight = walk
        # Recompute the durable penalty from the (now larger) frame, and only ever
        # let it ease downward — at least one point per successful month of growth.
        size_gap = max(0, expected_walk - walk)
        frame_gap = max(0, 55 - natural_size)
        floor = max(0, min(14, round(size_gap / 4.5 + frame_gap / 16)))
        new_penalty = max(floor, penalty - 1)
        if new_penalty >= penalty:
            return
        fighter.division_size_penalty = new_penalty
        fighter.division_size_note = (
            f"Fully adapted to {weight}: natural division fit." if new_penalty == 0
            else f"Adapting to {weight}: division-fit penalty eased to {new_penalty}/14."
        )
        if new_penalty == 0 and fighter in getattr(self, "roster", []):
            self.inbox.append({
                "subject": f"Division Fit — {fighter.name}",
                "body": f"{fighter.name} has fully grown into {weight}; the size disadvantage from the move up is gone.",
                "type": "Roster", "fighter": fighter.name, "resolved": False,
            })

    def complete_weight_class_move(self, fighter, target_weight, reason):
        """Apply a validated move; shared by the player UI and world simulation."""
        old_weight = fighter.weight
        fighter.weight = target_weight
        fighter.scale_weight = 0.0
        fighter.weight_cut_penalty = 0
        fighter.division_size_penalty = self.division_size_penalty_for(fighter, target_weight)
        fighter.division_size_note = (
            f"Undersized for {target_weight}: division-fit penalty {fighter.division_size_penalty}/14."
            if fighter.division_size_penalty else "Natural division fit."
        )
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
        if (
            self.player_owns_fighter(fighter)
            and self.belt_key(fighter.gender, target_weight) in set(getattr(self, "closed_divisions", set()))
        ):
            messagebox.showwarning(
                "Division closed",
                f"{fighter.gender} {target_weight} is not operated by your promotion. "
                "Reopen it or choose an active division.",
            )
            return False
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
            if fight.get("tournament") and "TBA" in fight.get("tournament_entrants", []):
                entrants = list(fight.get("tournament_entrants", []))
                known = next((self.get_fighter(name) for name in entrants if name != "TBA"), None)
                for index, name in enumerate(entrants):
                    if name != "TBA":
                        continue
                    replacement = self.find_tba_replacement(fight.get("tournament_weight", known.weight), fight.get("tournament_gender", known.gender), known=known, short_notice=True)
                    entrants[index] = replacement.name
                    lines.append(f"Tournament alternate {replacement.name} entered the field on short notice.")
                fight["tournament_entrants"] = entrants
                fight["fighters"] = [entrants[0], entrants[-1]]
            names = [name for name in self.event_fight_participants(fight) if name != "TBA"]
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
            if fight.get("tournament"):
                if misses:
                    fight["catchweight"] = True
                    fight["title"] = False
                    fight["divisional_title"] = False
                    fight["interim"] = False
                    fight["special_belt"] = ""
                    lines.append(f"{fight.get('tournament_name', 'The tournament')} continues, but the championship sanction was removed after {len(misses)} weight miss(es).")
                severe = [(fighter, miss_by) for fighter, miss_by in misses if miss_by > 2]
                for missed, miss_by in severe:
                    replacement = self.find_tba_replacement(missed.weight, missed.gender, known=missed, short_notice=True)
                    entrants = fight.get("tournament_entrants", [])
                    entrants[entrants.index(missed.name)] = replacement.name
                    outcome = self.perform_weigh_in(replacement, title_fight=False, camp_weeks=0, persist=True)
                    lines.append(f"Commission removed {missed.name} after a {miss_by} lb miss; alternate {replacement.name} weighed {outcome['scale_weight']} lb and joined the bracket.")
                entrants = fight.get("tournament_entrants", [])
                fight["fighters"] = [entrants[0], entrants[-1]]
                continue
            double_miss = len(misses) == 2
            severe_double_miss = double_miss and (
                sum(miss_by for _fighter, miss_by in misses) > 8
                or max(miss_by for _fighter, miss_by in misses) > 5
            )
            commission_cancels = severe_double_miss and random.random() < 0.35
            if commission_cancels or any(miss_by > 9 for _fighter, miss_by in misses):
                made = next((fighter for fighter in fighters if not fighter.missed_weight), None)
                if made and len(misses) == 1:
                    replacement = self.find_tba_replacement(made.weight, made.gender, known=made, short_notice=True)
                    fight["fighters"] = [made.name, replacement.name]
                    fight["title"] = False
                    fight["divisional_title"] = False
                    fight["interim"] = False
                    fight["special_belt"] = ""
                    fight["catchweight"] = True
                    lines.append(f"{misses[0][0].name} was removed after a bad miss; {replacement.name} steps in on short notice against {made.name}.")
                else:
                    cancelled.append(fight)
                    weigh_in = "; ".join(f"{fighter.name} missed by {miss_by:g} lb" for fighter, miss_by in misses)
                    reason = f"The commission cancelled the bout after a severe weigh-in failure ({weigh_in})."
                    resolution = self.queue_cancelled_bout_rebooking(event, fight, names)
                    fight["_cancellation"] = {"reason": reason, "weigh_in": weigh_in, "resolution": resolution}
                    lines.append(f"{' vs '.join(names)} was cancelled by the commission after a severe weigh-in failure. {resolution}")
            elif misses:
                fight["catchweight"] = True
                fight["title"] = False
                fight["divisional_title"] = False
                fight["interim"] = False
                fight["special_belt"] = ""
                lines.append(f"{' vs '.join(names)} continues as a catchweight non-title bout.")
        return lines, purse_penalty, cancelled

    def simulate_event_tournament(self, event, tournament):
        """Simulate a one-night MMA bracket while preserving the normal career result pipeline."""
        entrants = [self.get_fighter(name) for name in tournament.get("tournament_entrants", [])]
        entrants = sorted(entrants, key=lambda fighter: (self.division_rank_number(fighter) or 99, -fighter.elo_rating, -fighter.overall, fighter.name))
        starting_fatigue = {fighter.name: fighter.fatigue for fighter in entrants}
        current = entrants
        stages = []
        results = []
        award_pool = []
        fight_logs = []
        total_hype = total_build = total_excitement = total_cost = total_contract_cost = 0
        while len(current) > 1:
            stage = {8: "QUARTERFINALS", 4: "SEMIFINALS", 2: "FINAL"}.get(len(current), f"ROUND OF {len(current)}")
            pairings = list(zip(current[:len(current) // 2], reversed(current[len(current) // 2:])))
            winners = []
            stage_matches = []
            for a, b in pairings:
                is_final = len(current) == 2
                fight = {
                    "fighters": [a.name, b.name], "title": bool(is_final and tournament.get("title")),
                    "divisional_title": bool(is_final and tournament.get("divisional_title", tournament.get("title") and not tournament.get("special_belt"))),
                    "interim": bool(is_final and tournament.get("interim")), "main": bool(is_final and tournament.get("main")),
                    "special_belt": tournament.get("special_belt", "") if is_final else "",
                    "tier": tournament.get("tier", "Main Card"), "tournament": True,
                    "tournament_stage": stage, "tournament_name": tournament.get("tournament_name", "MMA Grand Prix"),
                    "_defer_retirement": True, "region": event.get("region", self.venue_region(event["venue"])),
                    "city": event.get("city", ""),
                }
                hype = self.fight_hype(a, b, fight) + (8 if is_final else 3)
                build = self.match_build_score(a, b, fight) + (8 if is_final else 4)
                a_start_gas = round(self.starting_fight_gas(a))
                b_start_gas = round(self.starting_fight_gas(b))
                a_title_status, b_title_status = self.fight_corner_title_statuses(fight, a, b)
                a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
                winner, loser, method, round_no, commentary = self.simulate_fight(a, b, fight)
                replay = 0
                while method == "Draw" and replay < 8:
                    replay += 1
                    commentary.append(f"Tournament rules require an advancing fighter. Sudden-death replay {replay} begins after the drawn bout.")
                    winner, loser, method, round_no, replay_lines = self.simulate_fight(a, b, fight)
                    commentary.extend(replay_lines)
                if method == "Draw":
                    winner, loser = ((a, b) if (a.elo_rating, a.overall, a.fight_iq) >= (b.elo_rating, b.overall, b.fight_iq) else (b, a))
                    method = "Decision"
                    commentary.append(f"After repeated level scorecards, the tournament commission's mandatory tiebreak criteria advances {winner.name}.")
                fight["_scorecards"] = self.scorecard_summary_from_lines(commentary)
                # A finalist can fight several times before finish_event commits
                # the career results. Preserve each bout's own box score so a
                # later round cannot overwrite the earlier career telemetry.
                fight["_fighter_stats"] = {
                    a.name: dict(getattr(a, "last_fight_stats", {}) or {}),
                    b.name: dict(getattr(b, "last_fight_stats", {}) or {}),
                }
                excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, hype)
                carry = max(4, round_no * 2 + (2 if method in ("Decision", "Majority Decision") else 0))
                winner.fatigue = min(88, winner.fatigue + carry)
                loser.fatigue = min(95, loser.fatigue + carry + 2)
                label = f"TOURNAMENT {stage[:-1] if stage.endswith('S') else stage}"
                if is_final:
                    label = "TOURNAMENT FINAL" + (" — TITLE FIGHT" if fight.get("title") else "")
                    if fight.get("special_belt"):
                        label = f"TOURNAMENT FINAL — {fight['special_belt'].upper()} TITLE" + (" + INTERIM TITLE" if fight.get("interim") else " + DIVISIONAL TITLE" if fight.get("divisional_title") else "")
                lines = [
                    f"{label}: {a.name} vs {b.name} ({a.weight})",
                    f"Bracket: {tournament.get('tournament_name', 'MMA Grand Prix')} | Cumulative fatigue {a.name} {a.fatigue}, {b.name} {b.fatigue}",
                    f"Odds: {self.matchup_odds(a, b)}",
                    f"Corner read: {a.name} camp {a.camp_weeks}w, morale {a.morale}, cut penalty {a.weight_cut_penalty} | {b.name} camp {b.camp_weeks}w, morale {b.morale}, cut penalty {b.weight_cut_penalty}",
                ] + commentary
                result_text = f"{winner.name} def. {loser.name} by {method}, R{round_no}"
                lines.append(f"Result: {result_text} | Fight excitement {excitement} | {winner.name} advances")
                results.append((winner, loser, fight, method))
                award_pool.append({"winner": winner.name, "loser": loser.name, "fighters": [a.name, b.name], "method": method, "excitement": excitement, "round": round_no, "fight": f"{a.name} vs {b.name}"})
                fight_logs.append({
                    "heading": lines[0], "lines": lines, "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                    "a_record": a.record, "b_record": b.record, "a_rating": a_rating, "b_rating": b_rating, "weight": a.weight,
                    "label": label, "title": bool(fight.get("title", False)), "divisional_title": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))), "interim": bool(fight.get("interim", False)), "special_belt": str(fight.get("special_belt", "") or ""), "result": result_text, "excitement": excitement,
                    "a_title_status": a_title_status, "b_title_status": b_title_status,
                    "tournament_stage": stage, "tournament_name": tournament.get("tournament_name", "MMA Grand Prix"),
                    "a_start_gas": a_start_gas, "b_start_gas": b_start_gas,
                    "scorecards": fight["_scorecards"],
                })
                stage_matches.append({"a": a.name, "b": b.name, "winner": winner.name, "method": method, "round": round_no, "summary": result_text})
                winners.append(winner)
                total_hype += hype
                total_build += build
                total_excitement += excitement
                total_contract_cost += a.purse + b.purse
                total_cost += self.player_bout_purse_cost(fight, a, b)
            stages.append({"name": stage, "matches": stage_matches})
            current = winners
        champion = current[0]
        bracket = {
            "title": tournament.get("tournament_name", "MMA Grand Prix"), "entrants": [fighter.name for fighter in entrants],
            "stages": stages, "champion": champion.name, "title_fight": bool(tournament.get("title")),
        }
        # Later rounds need real cumulative fatigue while being simulated, but
        # preparation happens before the viewer is completed. Restore the live
        # world here; finish_event applies every bout in order exactly once.
        for fighter in entrants:
            fighter.fatigue = starting_fatigue[fighter.name]
        return {
            "results": results, "award_pool": award_pool, "fight_logs": fight_logs,
            "hype": total_hype, "build": total_build, "excitement": total_excitement,
            "cost": total_cost, "contracted_cost": total_contract_cost, "bracket": bracket,
        }

    def open_event_tournament_bracket(self, package, parent=None):
        """Open a compact, readable bracket for a live or completed event."""
        brackets = package.get("tournament_brackets", []) if isinstance(package, dict) else []
        if not brackets:
            messagebox.showinfo("Tournament Bracket", "This event has no tournament bracket.", parent=parent or self.root)
            return
        window = tk.Toplevel(parent or self.root)
        window.title("Tournament Bracket")
        window.geometry("900x620")
        window.minsize(720, 480)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="TOURNAMENT BRACKET", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        for bracket in brackets:
            tab = ttk.Frame(notebook, style="Chrome.TFrame")
            notebook.add(tab, text=str(bracket.get("title", "Grand Prix"))[:32])
            champion = bracket.get("champion", "TBD")
            ttk.Label(tab, text=f"CHAMPION: {champion}", style="Section.TLabel", anchor="center").pack(fill="x", pady=(8, 4))
            ttk.Label(tab, text=f"Field: {len(bracket.get('entrants', []))} fighters" + (" | Championship awarded in the final" if bracket.get("title_fight") else ""), style="Panel.TLabel", anchor="center").pack(fill="x", pady=(0, 8))
            table_frame = ttk.Frame(tab, style="Chrome.TFrame")
            table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            columns = ("stage", "bout", "matchup", "winner", "result")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings")
            widths = {"stage": 120, "bout": 50, "matchup": 260, "winner": 180, "result": 220}
            labels = {"stage": "Stage", "bout": "Bout", "matchup": "Matchup", "winner": "Advances", "result": "Result"}
            for column in columns:
                tree.heading(column, text=labels[column])
                tree.column(column, width=widths[column], minwidth=45, anchor="w", stretch=column in ("matchup", "result"))
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for stage in bracket.get("stages", []):
                for bout_no, match in enumerate(stage.get("matches", []), 1):
                    matchup = f"{match.get('a', 'TBD')} vs {match.get('b', 'TBD')}"
                    result = f"{match.get('method', '')} R{match.get('round', '')}".strip()
                    tree.insert("", "end", values=(stage.get("name", "ROUND"), bout_no, matchup, match.get("winner", "TBD"), result))
            entrants = "Seeded field: " + "  |  ".join(bracket.get("entrants", []))
            ttk.Label(tab, text=entrants, style="Panel.TLabel", wraplength=830, justify="left").pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=8, pady=(0, 8))

    def queue_cancelled_bout_rebooking(self, event, fight, names):
        self.pending_rebookings = getattr(self, "pending_rebookings", [])
        self.pending_rebookings.append({
            "fighters": list(names), "tier": fight.get("tier", "Main Card"),
            "source_event": event.get("name", "Event"),
        })
        outcomes = self.process_pending_rebookings()
        return outcomes[0] if outcomes else "The promotion will review the matchup after the event."

    def matchup_odds(self, a, b):
        a_score = a.overall * 1.7 + a.momentum * 5 + a.camp_boost * 4 - a.weight_cut_penalty * 3 - getattr(a, "division_size_penalty", 0) * 2.4 + a.fight_iq * 0.25
        b_score = b.overall * 1.7 + b.momentum * 5 + b.camp_boost * 4 - b.weight_cut_penalty * 3 - getattr(b, "division_size_penalty", 0) * 2.4 + b.fight_iq * 0.25
        diff = round(a_score - b_score)
        fav, dog, edge = (a, b, diff) if diff >= 0 else (b, a, -diff)
        fav_line = -110 - min(390, edge * 8)
        dog_line = 100 + min(500, edge * 7)
        return f"{fav.name} {fav_line} / {dog.name} +{dog_line}"

    def resolve_fight_fighters(self, fight):
        if "TBA" not in fight["fighters"]:
            fighter_ids = list(fight.get("fighter_ids", []))
            references = fighter_ids if len(fighter_ids) == len(fight["fighters"]) and all(fighter_ids) else fight["fighters"]
            return [self.get_fighter(reference) for reference in references]
        known_index = next(index for index, name in enumerate(fight["fighters"]) if name != "TBA")
        fighter_ids = list(fight.get("fighter_ids", []))
        known_reference = fighter_ids[known_index] if len(fighter_ids) > known_index and fighter_ids[known_index] else fight["fighters"][known_index]
        known = self.get_fighter(known_reference)
        replacement = self.find_tba_replacement(fight.get("tba_weight", known.weight), fight.get("tba_gender", known.gender), known=known, short_notice=True)
        fight["fighters"] = [known.name, replacement.name]
        fight["fighter_ids"] = [getattr(known, "fighter_id", ""), getattr(replacement, "fighter_id", "")]
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
        change_snapshot = self.capture_player_change_snapshot()
        prior_change_ids = {id(entry) for entry in getattr(self, "change_journal", [])}
        self.cash += package["profit"]
        self.company_pop = package["projected_pop"]
        self.company_stability = package["projected_stability"]
        self.finance["last_event"] = package["finance"]
        self.finance["ledger"].insert(0, f"Month {self.month}: {package['event_name']} profit ${package['profit']:,}")
        featured = []
        for _winner, _loser, fight, _method in package.get("results", []):
            if not (fight.get("main") or fight.get("title")):
                continue
            for name in fight.get("fighters", []):
                fighter = self.find_fighter_anywhere(name)
                if fighter and fighter not in featured:
                    featured.append(fighter)
        if package.get("media_outcome"):
            self.record_media_event_outcome(event, package["media_outcome"], featured_fighters=featured)

        award_pool = package.get("award_pool", [])
        clause_payout = 0
        finance = package.get("finance", {})
        ppv_pool = finance.get("ticket_revenue", 0) + finance.get("broadcast_income", 0)
        for index, (winner, loser, fight, method) in enumerate(package["results"]):
            stats = fight.get("_fighter_stats", {})
            if stats:
                winner.last_fight_stats = dict(stats.get(winner.name, {}) or {}) or None
                loser.last_fight_stats = dict(stats.get(loser.name, {}) or {}) or None
            excitement = award_pool[index].get("excitement", 50) if index < len(award_pool) else 50
            round_no = award_pool[index].get("round", 1) if index < len(award_pool) else 1
            self.record_season_result(winner, loser, method, round_no, fight, excitement, self.player_company_name)
            if method == "Draw":
                self.apply_draw_result(winner, loser, fight)
            else:
                self.apply_result(winner, loser, fight, method)
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
        for bracket in package.get("tournament_brackets", []):
            champion = self.find_fighter_anywhere(bracket.get("champion", ""))
            if not champion:
                continue
            honour = f"Won {bracket.get('title', 'MMA Grand Prix')} in Month {self.month}"
            champion.career_achievements = list(champion.career_achievements or [])
            if honour not in champion.career_achievements:
                champion.career_achievements.append(honour)
            champion.popularity = min(100, champion.popularity + 4)
            champion.morale = min(100, champion.morale + 8)
            champion.legacy_score += 14 + len(bracket.get("entrants", []))
            self.news.insert(0, f"GRAND PRIX WINNER: {champion.name} won the {bracket.get('title', 'MMA Grand Prix')}.")
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
        package["date"] = f"Month {self.month} Week {self.week}"
        package["company"] = self.player_company_name
        self.apply_event_awards(package.get("awards", []))
        self.apply_regional_show_effects(package)
        # apply_result/apply_draw_result deliberately deferred these removals so
        # every event subsystem could still resolve the participants safely.
        for winner, loser, _fight, _method in package["results"]:
            self.retire_after_final_fight_if_due(winner, self.player_company_name)
            self.retire_after_final_fight_if_due(loser, self.player_company_name)
        self.result_history.insert(0, package["summary"])
        self.player_event_archive = [package] + list(getattr(self, "player_event_archive", []))
        self.player_event_archive = self.player_event_archive[:150]
        self.archive_result_record({
            "date": f"Month {self.month} Week {self.week}",
            "company": self.player_company_name,
            "event": package["event_name"],
            "summary": package["summary"],
            "fights": package["fight_count"],
            "gate": f"${package['finance'].get('ticket_revenue', 0):,}",
            "profit": f"${package['profit']:,}",
            "log": package.get("log", []),
            "fight_logs": package.get("fight_logs", []),
            "tournament_brackets": package.get("tournament_brackets", []),
            "finance": package.get("finance", {}),
        })
        self.evaluate_promotion_achievements(self.player_company_name, package)
        self.complete_super_event(event, package)
        self.refresh_historical_records()
        self.refresh_promotion_rankings()
        self.update_player_fanbase(package)
        finance = package.get("finance", {})
        event_reason = (
            f"{package.get('fight_count', 0)} fights; excitement {round(package.get('average_excitement', 0) or 0)}; "
            f"${finance.get('total_revenue', 0):,} revenue against ${finance.get('total_expense', 0) + clause_payout:,} costs"
        )
        self.record_snapshot_changes(change_snapshot, event_reason, include_finance=False)
        package["attributed_changes"] = [entry for entry in getattr(self, "change_journal", []) if id(entry) not in prior_change_ids]
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
        window.geometry("1040x760")
        window.minsize(820, 600)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="END OF EVENT", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        overview = ttk.Frame(window, style="Panel.TFrame")
        overview.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(overview, text=package["event_name"], style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(8, 2))
        finance = package.get("finance", {})
        excitement = int(round(float(package.get("average_excitement", 0) or 0)))
        attendance = int(round(float(finance.get("attendance", 0) or 0)))
        capacity = max(1, int(round(float(finance.get("venue_capacity", 1) or 1))))
        sell_through = min(100, round(attendance * 100 / capacity))
        pop_before = int(package.get("starting_pop", package.get("projected_pop", 0)))
        stability_before = int(package.get("starting_stability", package.get("projected_stability", 0)))
        pop_after = int(package.get("projected_pop", pop_before))
        stability_after = int(package.get("projected_stability", stability_before))
        grade = "A" if excitement >= 78 else "B" if excitement >= 64 else "C" if excitement >= 50 else "D" if excitement >= 38 else "F"

        metrics = tk.Frame(overview, bg=self.colors["panel"])
        metrics.pack(fill="x", padx=12, pady=(4, 6))
        metric_data = (
            ("EVENT GRADE", grade, f"Excitement {excitement}"),
            ("PROFIT", f"${int(package.get('profit', 0)):,}", f"Revenue ${int(finance.get('total_revenue', 0)):,}"),
            ("ATTENDANCE", f"{attendance:,}", f"{sell_through}% of {capacity:,}"),
            ("POPULARITY", f"{pop_after}", f"{pop_before}  →  {pop_after} ({pop_after - pop_before:+d})"),
            ("STABILITY", f"{stability_after}", f"{stability_before}  →  {stability_after} ({stability_after - stability_before:+d})"),
        )
        for heading, value, detail in metric_data:
            tile = tk.Frame(metrics, bg=self.colors["tree"], highlightthickness=1, highlightbackground=self.colors["line"])
            tile.pack(side="left", fill="x", expand=True, padx=3)
            tk.Label(tile, text=heading, bg=self.colors["tree"], fg=self.colors["muted"], font=("Tahoma", 8, "bold")).pack(pady=(5, 0))
            tk.Label(tile, text=value, bg=self.colors["tree"], fg=self.colors["gold"], font=("Tahoma", 15, "bold")).pack()
            tk.Label(tile, text=detail, bg=self.colors["tree"], fg=self.colors["text"], font=("Tahoma", 8)).pack(pady=(0, 5))
        atmosphere = package.get("finance", {}).get("atmosphere", {})
        media = package.get("media_outcome", {})
        ttk.Label(
            overview,
            text=(f"Crowd: {atmosphere.get('mood', 'Engaged')} {atmosphere.get('intensity', 50)}/100 - {atmosphere.get('preference', 'Competitive fights')}  |  "
                  f"Media: {media.get('outlet', 'No broadcaster')} - {int(media.get('viewers', 0) or 0):,} viewers"),
            style="Panel.TLabel",
        ).pack(anchor="w", padx=12, pady=(0, 8))
        changes = package.get("attributed_changes", [])
        if changes:
            ttk.Label(overview, text="WHY VALUES CHANGED", style="Section.TLabel", anchor="w").pack(fill="x", padx=8, pady=(0, 3))
            for entry in changes[:5]:
                delta = entry.get("delta", 0)
                if entry.get("category") == "Finance" and isinstance(delta, (int, float)):
                    delta_text = f"${delta:+,.0f}"
                elif isinstance(delta, (int, float)):
                    delta_text = f"{delta:+g}"
                else:
                    delta_text = str(delta)
                ttk.Label(
                    overview,
                    text=f"{entry.get('subject', '')}: {entry.get('category', 'Change')} {delta_text} - {entry.get('reason', '')}",
                    style="Panel.TLabel", anchor="w", justify="left", wraplength=880,
                ).pack(fill="x", padx=12, pady=1)
        if package.get("tournament_brackets"):
            champions = "  |  ".join(f"{bracket.get('title', 'Grand Prix')}: {bracket.get('champion', 'TBD')}" for bracket in package["tournament_brackets"])
            ttk.Label(overview, text=f"TOURNAMENT CHAMPION - {champions}", style="Section.TLabel", anchor="center").pack(fill="x", padx=8, pady=(0, 8))

        result_panel = ttk.Frame(window, style="Panel.TFrame")
        result_panel.pack(fill="both", expand=True, padx=8, pady=4)
        ttk.Label(result_panel, text="CARD RESULTS", style="Section.TLabel", anchor="center").pack(fill="x", ipady=3)
        table_frame = ttk.Frame(result_panel, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)
        columns = ("bout", "stage", "matchup", "result", "excitement")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        definitions = (
            ("bout", "#", 42, "center"), ("stage", "Stage", 125, "center"),
            ("matchup", "Matchup", 250, "w"), ("result", "Result", 260, "w"),
            ("excitement", "Exc.", 58, "center"),
        )
        for column, heading, width, anchor in definitions:
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=40, anchor=anchor, stretch=column in ("matchup", "result"))
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.tag_configure("headline", background=self.colors["panel_dark"], foreground=self.colors["text"])
        tree.tag_configure("title", foreground=self.colors["gold"])
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for index, log in enumerate(package.get("fight_logs", []), 1):
            matchup = f"{log.get('a', '')} vs {log.get('b', '')}" if log.get("a") else log.get("heading", "Bout")
            stage = log.get("tournament_stage") or log.get("label", "BOUT")
            tags = ("headline",) if "MAIN" in str(stage).upper() else ("title",) if log.get("title") else ()
            tree.insert("", "end", values=(index, stage, matchup, log.get("result", "Cancelled"), log.get("excitement", "-")), tags=tags)

        bonus_panel = ttk.Frame(window, style="Panel.TFrame")
        bonus_panel.pack(fill="x", padx=8, pady=4)
        ttk.Label(bonus_panel, text="POST-FIGHT BONUSES", style="Section.TLabel", anchor="center").pack(fill="x", ipady=3)
        if package.get("awards"):
            for award in package["awards"]:
                ttk.Label(bonus_panel, text=f"{award['award']}: {', '.join(award['fighters'])}  |  {award['note']}  |  ${award['bonus']:,}", style="Panel.TLabel").pack(anchor="w", padx=12, pady=2)
        else:
            ttk.Label(bonus_panel, text="No bonuses awarded.", style="Panel.TLabel").pack(anchor="w", padx=12, pady=4)
        summary_controls = ttk.Frame(window, style="Chrome.TFrame")
        summary_controls.pack(fill="x", padx=8, pady=(0, 8))
        if package.get("tournament_brackets"):
            ttk.Button(summary_controls, text="View Tournament Bracket", style="Accent.TButton", command=lambda: self.open_event_tournament_bracket(package, window)).pack(side="left")
        ttk.Button(summary_controls, text="Close", command=window.destroy).pack(side="right")
