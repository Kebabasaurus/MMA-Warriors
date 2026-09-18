import hashlib
import json
import math
from fighter_traits import effective_injury_tendency, progress_camp_trait
from fight_night_layout import build_fight_night_layout
from fight_night_presentation import configure_fight_timeline, insert_fight_timeline_line
from fight_night_archive import build_event_archive
import random
import re
import sys
import threading
import traceback
from collections import Counter
from copy import deepcopy
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4
from tkinter import messagebox, ttk

from constants import *
from fighter_portraits import render_portrait
from fight_moves.release_registry import RELEASE_MOVE_REGISTRY as MOVE_REGISTRY
from models import Fighter, Gym, Promotion


class EventMixin:
    TITLE_MISS_ACTIONS = ("remove_belt", "rebook", "keep_belt", "cancel", "replacement")

    @staticmethod
    def event_transaction_runtime_value(value, seen=None):
        """Identify UI/callback objects that must remain outside event rollback."""
        if (callable(value) or isinstance(value, (tk.Misc, tk.Variable, threading.Thread,
                                                   threading.Event, type(threading.Lock()),
                                                   type(threading.RLock()), random.SystemRandom))
                or hasattr(value, "tk")):
            return True
        seen = seen if seen is not None else set()
        marker = id(value)
        if marker in seen:
            return False
        seen.add(marker)
        if isinstance(value, dict):
            return any(EventMixin.event_transaction_runtime_value(item, seen) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(EventMixin.event_transaction_runtime_value(item, seen) for item in value)
        return False

    def normalized_contract_months(self, months):
        """Keep player-negotiated contract terms inside the supported range."""
        return max(1, min(60, int(months)))

    def validated_contract_terms(self, purse, months, guaranteed_fights, signing_bonus=0,
                                 finish_bonus_pct=0, win_bonus=0, ppv_points=0):
        """Return safe player contract terms or reject an invalid financial package.

        Spinbox limits are presentation hints rather than a security boundary: a
        player can type arbitrary text into them and tests or future callers can
        invoke the domain path directly.  Validate before calculating acceptance
        or touching cash so negative money can never become a credit.
        """
        try:
            terms = {
                "purse": int(purse),
                "months": self.normalized_contract_months(months),
                "guaranteed_fights": int(guaranteed_fights),
                "signing_bonus": int(signing_bonus),
                "finish_bonus_pct": int(finish_bonus_pct),
                "win_bonus": int(win_bonus),
                "ppv_points": int(ppv_points),
            }
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Contract terms must be whole numbers.") from exc

        limits = {
            "purse": (1, 600_000, "Purse per fight"),
            "guaranteed_fights": (1, 12, "Guaranteed fights"),
            "signing_bonus": (0, 400_000, "Signing bonus"),
            "finish_bonus_pct": (0, 60, "Finish bonus"),
            "win_bonus": (0, 300_000, "Win bonus"),
            "ppv_points": (0, 15, "PPV points"),
        }
        for key, (minimum, maximum, label) in limits.items():
            if not minimum <= terms[key] <= maximum:
                suffix = "%" if key in ("finish_bonus_pct", "ppv_points") else ""
                raise ValueError(f"{label} must be between {minimum}{suffix} and {maximum}{suffix}.")
        return terms

    def contract_duration_offer_score(self, months, purse, ask, signing_bonus=0, win_bonus=0,
                                      finish_bonus_pct=0):
        """Value contract security without letting raw duration replace fair pay.

        Fighters are paid per fight, so the compensation gate uses a three-fight
        annual earnings proxy.  Base purse remains the largest component; win,
        finish, and signing bonuses provide secondary support.  Security has
        diminishing returns through 48 months and no extra value after that.
        """
        term = self.normalized_contract_months(months)
        security_months = min(term, 48)
        duration_value = min(security_months, 12) * 260
        duration_value += max(0, min(security_months, 24) - 12) * 130
        duration_value += max(0, min(security_months, 36) - 24) * 60
        duration_value += max(0, security_months - 36) * 20

        market_purse = max(1, int(ask))
        offered_purse = max(0, int(purse))
        security_rate = min(security_months, 12) / 12 * 0.08
        security_rate += max(0, min(security_months, 24) - 12) / 12 * 0.04
        security_rate += max(0, min(security_months, 36) - 24) / 12 * 0.02
        security_rate += max(0, security_months - 36) / 12 * 0.01
        # Duration stays secondary to a three-fight year of market-rate pay,
        # including for inexpensive prospects where fixed points loom largest.
        duration_value = min(duration_value, market_purse * 3 * security_rate)
        base_pay_ratio = offered_purse / market_purse
        # An agent will not trade badly under-market base pay for years of control.
        salary_gate = max(0.0, min(1.0, (base_pay_ratio - 0.60) / 0.40))

        expected_annual_pay = offered_purse * 3
        expected_annual_pay += max(0, int(win_bonus)) * 1.25
        expected_annual_pay += offered_purse * max(0, int(finish_bonus_pct)) / 100 * 0.75
        # A signing bonus is worth less per year when spread across a long deal.
        expected_annual_pay += max(0, int(signing_bonus)) * 12 / term
        annual_pay_ratio = expected_annual_pay / (market_purse * 3)
        compensation_gate = min(1.15, annual_pay_ratio) * salary_gate
        return round(duration_value * compensation_gate)

    def event_fight_participants(self, fight):
        """Return every booked athlete, including a tournament's complete field."""
        return list(fight.get("tournament_entrants", fight.get("fighters", [])))

    def event_fight_participant_references(self, fight):
        """Return stable participant references, preferring fighter IDs.

        Names remain in event data for presentation and legacy saves, but they
        are not unique.  A complete aligned ``fighter_ids`` list is therefore
        authoritative for availability, conflict checks and result resolution.
        """
        participants = self.event_fight_participants(fight)
        fighter_ids = list(fight.get("fighter_ids", []))
        if len(fighter_ids) == len(participants):
            return [fighter_id if fighter_id else name for name, fighter_id in zip(participants, fighter_ids)]
        return participants

    def event_fight_fighters(self, fight):
        fighters = []
        for reference in self.event_fight_participant_references(fight):
            if reference == "TBA":
                continue
            fighter = self._resolve_event_fighter(reference)
            if fighter is not None:
                fighters.append(fighter)
        return fighters

    def duplicate_event_participant_references(self, fights):
        references = [
            reference for fight in fights
            for reference in self.event_fight_participant_references(fight)
            if reference != "TBA"
        ]
        return {reference for reference, count in Counter(references).items() if count > 1}

    def contract_rival_candidate(self, active_offer_company=""):
        candidates = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)]
        matched = next((promo for promo in candidates if promo.name == active_offer_company), None)
        if active_offer_company:
            return matched
        return random.choice(candidates) if candidates else None

    def schedule_event(self):
        if len(self.booked) < 1:
            self.set_schedule_status("SCHEDULING BLOCKED: Book at least one fight before scheduling the show.", "error")
            return
        references = [reference for fight in self.booked for reference in self.event_fight_participant_references(fight) if reference != "TBA"]
        duplicate_refs = self.duplicate_event_participant_references(self.booked)
        duplicates = sorted({getattr(self._resolve_event_fighter(reference), "name", str(reference)) for reference in duplicate_refs})
        if duplicate_refs:
            self.set_schedule_status("SCHEDULING BLOCKED: A fighter appears more than once on this card.", "error")
            self.set_schedule_status(
                f"SCHEDULING BLOCKED: {', '.join(duplicates)} is booked more than once. A fighter can only appear once per event.",
                "error",
            )
            return
        scheduled_refs = {
            reference for event in self.scheduled_events
            for fight in event.get("fights", [])
            for reference in self.event_fight_participant_references(fight) if reference != "TBA"
        }
        conflict_refs = [reference for reference in references if reference in scheduled_refs]
        if conflict_refs:
            conflicts = sorted({getattr(self._resolve_event_fighter(reference), "name", str(reference)) for reference in conflict_refs})
            self.set_schedule_status(
                f"SCHEDULING BLOCKED: {', '.join(conflicts)} already has a future fight scheduled. "
                "A fighter cannot be booked again until that event has been completed.",
                "error",
            )
            self.refresh_available()
            return
        target_date = self.selected_booking_date(reject_past=True)
        if target_date is None:
            return
        month, week = target_date
        unavailable = []
        for reference in references:
            fighter = self._resolve_event_fighter(reference)
            if fighter is None:
                unavailable.append(f"{reference} (identity unavailable)")
                continue
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
            project_status = str(super_project.get("status", "") or "").strip()
            # Only an accepted Planning project may enter the scheduled
            # pipeline. An Offered/terminal/stale object must not bypass the
            # approval deposit and terms snapshot by being left in the editor.
            if project_status and project_status != "Planning":
                message = f"This super-event project is {project_status.lower()} and cannot be scheduled from the current editor state. Review the project before trying again."
                self.set_schedule_status("SCHEDULING BLOCKED: " + message, "error")
                return
            if month < int(super_project.get("earliest_month", month)) or month > int(super_project.get("deadline_month", month)):
                message = f"This project must be scheduled between {self.format_game_date(super_project.get('earliest_month', month), 1)} and {self.format_game_date(super_project.get('deadline_month', month), 4)}."
                self.set_schedule_status("SCHEDULING BLOCKED: " + message, "error")
                return
            missing = self.validate_super_event_card(super_project, self.booked)
            if missing:
                message = "Super-event card approval still requires: " + ", ".join(missing) + "."
                self.set_schedule_status("SCHEDULING BLOCKED: " + message, "error")
                return
        event_number = self.next_player_event_number()
        current_name = self.event_name.get().strip()
        auto_named = self.is_auto_event_name(current_name)
        event_name = self.default_event_name(event_number) if auto_named else current_name
        scheduled_fights = []
        for booked_fight in self.booked:
            snapshot = dict(booked_fight)
            snapshot["fighter_ids"] = [
                getattr(self._resolve_event_fighter(reference), "fighter_id", "") if reference != "TBA" else ""
                for reference in self.event_fight_participant_references(snapshot)
            ]
            scheduled_fights.append(snapshot)
        event = {
            "event_id": self._foundation_next_id("event") if hasattr(self, "_foundation_next_id") else "",
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
            **self.selected_event_economics(),
        }
        # An accepted regional host offer is an entitlement on one ordinary
        # event, not a second scheduling system.  Binding is exact-date and
        # region based; unmatched cards remain ordinary events.
        if hasattr(self, "bind_regional_invitation_to_event"):
            self.bind_regional_invitation_to_event(event)
        if super_project:
            project = dict(super_project)
            project["status"] = "Scheduled"
            project["scheduled_month"] = month
            project["project_revision"] = max(1, int(project.get("project_revision", 1) or 1) + 1)
            event["super_event"] = project
            self.super_event_project = None
            for offer in self.super_event_offers:
                if offer.get("id") == project.get("id"):
                    offer.update(project)
        self.scheduled_events.append(event)
        if hasattr(self, "register_grand_prix_series_for_event"):
            self.register_grand_prix_series_for_event(event)
        self.record_homecoming_booking(event, self.player_company_name)
        self.assign_event_camps(event)
        prefix = "SUPER EVENT SCHEDULED: " if event.get("super_event") else ""
        self.news.insert(0, f"{prefix}{event['name']} has been scheduled for {self.event_date_label(event)} at {event['venue']}.")
        self.set_schedule_status(f"SCHEDULED: {event['name']} | {self.event_date_label(event)} | {len(event['fights'])} fights.", "success")
        self.booked.clear()
        self._event_price_user_set = False
        self.event_name.set(self.default_event_name())
        self.set_booking_date(month if week < 4 else month + 1, week + 1 if week < 4 else 1)
        self.event_broadcaster.set(self.broadcasters[0]["name"] if self.broadcasters else "No Coverage")
        if hasattr(self, "event_venue_box"):
            self.event_venue_box.configure(values=self.available_event_venues())
        self.refresh_all()

    def fight_has_title_stakes(self, fight):
        """True when a belt is genuinely on the line in this booking."""
        if not isinstance(fight, dict):
            return False
        return bool(
            fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))
            or fight.get("special_belt")
        )

    def strip_fight_title_stakes(self, fight, reason):
        """Take a belt off the line once the bout can no longer legitimately carry it."""
        if not self.fight_has_title_stakes(fight):
            return False
        fight["title"] = False
        fight["divisional_title"] = False
        fight["interim"] = False
        fight["special_belt"] = ""
        fight["title_stripped_reason"] = reason
        return True

    def repair_booking_conflicts(self):
        """Guarantee no fighter is booked on two un-run events at once.

        Championship bouts claim their fighters first, whatever the date. This
        used to be a plain date-ordered pass where the earliest booking always
        won, which silently pulled a champion out of their own title defence to
        honour an ordinary undercard booking made a week earlier -- the belt
        stayed on the line, a free agent was signed into the empty corner on
        fight night, and the champion's record showed the other, non-title bout
        instead. A belt match is also the harder booking to remake.

        Any bout that still loses a fighter has its stakes removed rather than
        left advertising a belt nobody present can win, and interim status is
        recomputed for the title fights that survive.

        Runs on load, so it also protects legacy saves and anything that slipped
        past the UI guards.
        """
        seen = set()
        conflicts = []
        downgraded = []
        events = sorted(self.scheduled_events, key=lambda e: (e.get("month", 1), e.get("week", 1)))
        claimed_per_event = {}
        title_bouts = [(event, fight) for event in events for fight in event.get("fights", [])
                       if self.fight_has_title_stakes(fight)]
        other_bouts = [(event, fight) for event in events for fight in event.get("fights", [])
                       if not self.fight_has_title_stakes(fight)]
        for event, fight in title_bouts + other_bouts:
            event_names = claimed_per_event.setdefault(id(event), set())
            participants = self.event_fight_participants(fight)
            references = self.event_fight_participant_references(fight)
            for index, (name, reference) in enumerate(zip(participants, references)):
                if name == "TBA":
                    continue
                if reference in seen or reference in event_names:
                    if fight.get("tournament"):
                        fight.setdefault("tournament_entrants", participants)[index] = "TBA"
                        fight["fighters"] = list(fight["tournament_entrants"][:1] + fight["tournament_entrants"][-1:])
                    else:
                        fight.setdefault("fighters", participants)[index] = "TBA"
                    fighter = self._resolve_event_fighter(reference)
                    fight["tba_weight"] = fight.get("tba_weight", fighter.weight if fighter else self._safe_weight(name))
                    fight["tba_gender"] = fight.get("tba_gender", fighter.gender if fighter else self._safe_gender(name))
                    if len(fight.get("fighter_ids", [])) == len(participants):
                        fight["fighter_ids"][index] = ""
                    conflicts.append(name)
                    if self.strip_fight_title_stakes(fight, f"{name} was double-booked and freed from this card"):
                        downgraded.append((event.get("name", "a scheduled card"), name))
                else:
                    event_names.add(reference)
                    seen.add(reference)
        # A title bout that kept both corners may still have changed shape, so
        # its interim status is settled against the belts as they stand now.
        for _event, fight in title_bouts:
            if not self.fight_has_title_stakes(fight):
                continue
            named = self.event_fight_fighters(fight)
            divisional = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            fight["interim"] = self.divisional_title_is_interim([f for f in named if f], divisional)
        for name in sorted(set(conflicts)):
            self.news.insert(0, f"Booking conflict resolved: {name} was double-booked and freed from the lower-priority card.")
        for event_name, name in downgraded:
            note = (f"{event_name} lost its championship sanction: {name} was double-booked and could not "
                    f"appear, so the bout goes ahead without the belt.")
            self.news.insert(0, note)
            self.inbox.append({"subject": "Title Fight Downgraded", "body": note, "type": "Booking", "resolved": False})
        return conflicts

    def _safe_weight(self, name):
        fighter = self._resolve_event_fighter(name)
        return fighter.weight if fighter else "Lightweight"

    def _safe_gender(self, name):
        fighter = self._resolve_event_fighter(name)
        return fighter.gender if fighter else "Male"

    def _resolve_event_fighter(self, reference):
        """Resolve an event corner by stable ID, with a safe legacy fallback."""
        resolver = getattr(self, "resolve_fighter", None)
        if callable(resolver):
            try:
                return resolver(reference)
            except (LookupError, TypeError, ValueError):
                return None
        getter = getattr(self, "get_fighter", None)
        if callable(getter):
            try:
                return getter(reference)
            except (LookupError, TypeError, ValueError):
                return None
        return None

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
            for fighter in self.event_fight_fighters(fight):
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
                self.develop_fighter_move_mastery(fighter, weeks_out, getattr(fighter, "camp_focus", "Balanced"))
                self.evolve_trait_from_camp(fighter, quality, weeks_out)
                if intensity == "Hard" and random.random() < max(0.015, effective_injury_tendency(fighter) / 1600):
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
        selected = self.upcoming_tree.selection()
        if selected:
            event = getattr(self, "upcoming_event_rows", {}).get(selected[0])
            if event is None:
                self.set_schedule_status("CARD UNAVAILABLE: The selected card could not be resolved by its saved identity. Refresh the list and try again.", "error")
                return None
        else:
            shows = self.sorted_scheduled_events()
            due = [show for show in shows if self.is_event_due(show)]
            event = due[0] if due else None
        if not event:
            self.set_schedule_status("NO FIGHT DAY: There is no scheduled event due this week.", "info")
            return None
        if not self.is_event_due(event):
            self.set_schedule_status(f"NOT YET: {event['name']} is scheduled for {self.event_date_label(event)}.", "info")
            return None
        return event

    def selected_scheduled_event_for_edit(self):
        """Resolve the exact future event selected in the upcoming-events list."""
        if not hasattr(self, "upcoming_tree"):
            return None
        selected = self.upcoming_tree.selection()
        if not selected:
            self.set_schedule_status("EDIT BLOCKED: Select an upcoming event first.", "info")
            return None
        event = getattr(self, "upcoming_event_rows", {}).get(selected[0])
        if event is None:
            self.set_schedule_status("EDIT BLOCKED: The selected event could not be found. Refresh the list and try again.", "error")
        return event

    def edit_selected_scheduled_event(self):
        event = self.selected_scheduled_event_for_edit()
        if not event:
            return
        if self.is_event_due(event):
            self.set_schedule_status("FIGHT DAY: Watch or simulate this event before making further card changes.", "info")
            return
        self.open_scheduled_card_editor(event)

    def review_selected_title_miss_decision(self):
        """Open a read-only review of retained title-miss decisions.

        Upcoming Cards already marks a card that is waiting at the weigh-in
        boundary. This companion surface lets the player inspect the exact
        saved corners, available actions and evidence before choosing Watch,
        Simulate or an explicit title action. Opening it never reruns
        weigh-ins, resolves rankings or mutates the scheduled event.
        """
        event = self.selected_scheduled_event_for_edit()
        if not event:
            return []
        rows = self.title_miss_decision_read_model(event)
        if not rows:
            self.set_schedule_status(
                "NO TITLE DECISION: The selected card has no retained title-miss decision to review.",
                "info",
            )
            return []
        # Keep headless/legacy callers useful without trying to construct a Tk
        # window. The pure rows are also convenient for regression coverage.
        if not hasattr(self, "create_managed_window") or not hasattr(self, "root"):
            return rows
        try:
            event_identity = self.fight_night_event_key(event)
        except Exception:
            event_identity = event.get("event_id") or event.get("name") or "upcoming"
        review_key = f"title-decision-review:{event_identity!r}"
        existing = self.focus_managed_window(review_key) if hasattr(self, "focus_managed_window") else None
        if existing is not None:
            return rows
        window = self.create_managed_window(review_key, parent=self.root)
        window.title(f"Title Decision Review - {event.get('name', 'Upcoming Event')}")
        window.geometry("980x520")
        window.minsize(760, 420)
        window.configure(bg=getattr(self, "colors", {}).get("chrome", "#1f2830"))

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="TITLE DECISION REVIEW", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(
            header,
            text=f"{event.get('name', 'Upcoming Event')} | {self.event_date_label(event)}",
            style="Panel.TLabel",
        ).pack(side="right", padx=10)
        ttk.Label(
            window,
            text=(
                "This is the saved weigh-in evidence for the selected card. "
                "Review it before committing a title action; nothing on this screen changes the card."
            ),
            style="Inset.TLabel", anchor="w", justify="left", wraplength=920,
        ).pack(fill="x", padx=16, pady=(8, 6))

        body = ttk.Frame(window, style="Inset.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        columns = ("bout", "status", "action", "corners", "title", "replacement")
        tree = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse", height=7)
        labels = {
            "bout": "Bout", "status": "Status", "action": "Action",
            "corners": "Recorded corners", "title": "Title state", "replacement": "Replacement",
        }
        widths = {"bout": 58, "status": 125, "action": 120, "corners": 280, "title": 130, "replacement": 150}
        for column in columns:
            tree.heading(column, text=labels[column])
            tree.column(column, width=widths[column], anchor="center")
        tree.column("corners", anchor="w")
        tree.column("replacement", anchor="w")
        scroll = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        status_labels = {"awaiting_player": "Decision required", "needs_review": "Review required"}
        action_labels = {
            "remove_belt": "Remove Belt", "rebook": "Rebook Fight", "keep_belt": "Keep Belt",
            "cancel": "Cancel Fight", "replacement": "Last-minute replacement",
        }

        def missed_text(row):
            entries = []
            for corner in row.get("missed_corners", []) if isinstance(row.get("missed_corners"), list) else []:
                if not isinstance(corner, dict):
                    continue
                name = str(corner.get("fighter", corner.get("name", "Recorded corner")) or "Recorded corner")
                try:
                    miss_by = float(corner.get("miss_by", 0) or 0)
                except (TypeError, ValueError, OverflowError):
                    miss_by = 0
                entries.append(f"{name} ({miss_by:g} lb)" if miss_by else name)
            return ", ".join(entries) or "No miss detail recorded"

        for row_index, row in enumerate(rows, 1):
            refs = " vs ".join(row.get("fighter_references", [])) or "Recorded corners unavailable"
            if row.get("status") == "awaiting_player" and row.get("scheduled_title"):
                title_state = "Pending — scheduled title"
            else:
                title_state = "On the line" if row.get("on_line") else "Removed / not on line"
            title_scope = str(row.get("belt_id") or row.get("title_key") or "")
            if title_scope.startswith("division:"):
                _prefix, scope_gender, scope_weight = (title_scope.split(":", 2) + ["", ""])[:3]
                title_scope = f"{scope_gender} {scope_weight} belt".strip()
            elif title_scope.startswith("special:"):
                title_scope = f"Special belt: {title_scope.split(':', 1)[1]}"
            if title_scope:
                title_state += f" • {title_scope}"
            if row.get("vacated_before_bout"):
                title_state += " • vacated"
            replacement = row.get("replacement_id") or "—"
            tree.insert(
                "", "end", iid=f"decision:{row_index}",
                values=(
                    row.get("fight_ordinal", row_index),
                    status_labels.get(row.get("status"), row.get("status") or "Recorded"),
                    action_labels.get(row.get("action"), row.get("action") or "Uncommitted"),
                    refs, title_state, replacement,
                ),
            )

        detail_var = tk.StringVar(value="Select a bout to view its recorded miss, reason and permitted choices.")
        detail = ttk.Label(window, textvariable=detail_var, style="Inset.TLabel", anchor="w", justify="left", wraplength=920)
        detail.pack(fill="x", padx=16, pady=(0, 8))

        def show_detail(_event=None):
            selected = tree.selection()
            if not selected:
                return
            try:
                index = int(selected[0].split(":", 1)[1]) - 1
            except (ValueError, IndexError):
                return
            if index < 0 or index >= len(rows):
                return
            row = rows[index]
            choices = ", ".join(action_labels.get(choice, choice) for choice in row.get("choices", [])) or "No choices recorded"
            reason = row.get("reason") or "No reason recorded."
            legacy = " Legacy reference; no durable fight ID was saved." if row.get("legacy_reference") else ""
            replacement_note = f" Replacement: {row.get('replacement_id')}." if row.get("replacement_id") else ""
            eligibility_notes = []
            for corner in row.get("corner_eligibility", []) if isinstance(row.get("corner_eligibility"), list) else []:
                if not isinstance(corner, dict):
                    continue
                name = str(corner.get("fighter", "Recorded corner") or "Recorded corner")
                win = "yes" if corner.get("eligible_to_win") is True else "no" if corner.get("eligible_to_win") is False else "unknown"
                retain = "yes" if corner.get("eligible_to_retain") is True else "no" if corner.get("eligible_to_retain") is False else "unknown"
                holder = "named-belt holder" if corner.get("special_belt_holder") is True else ""
                eligibility_notes.append(f"{name}: {holder + '; ' if holder else ''}win {win}, retain {retain}")
            eligibility_note = (
                " Eligibility: " + "; ".join(eligibility_notes) + "."
                if eligibility_notes else ""
            )
            settlement = row.get("settlement") if isinstance(row.get("settlement"), dict) else {}
            settlement_note = ""
            if settlement:
                outcome = str(settlement.get("outcome", "Recorded") or "Recorded").replace("_", " ").title()
                settlement_note = f" Settlement: {outcome} after {settlement.get('method', 'the official result')}: {settlement.get('reason', 'No reason recorded.')}"
            detail_var.set(f"{missed_text(row)}  •  {reason}  •  Choices: {choices}.{replacement_note}{eligibility_note}{settlement_note}{legacy}")

        tree.bind("<<TreeviewSelect>>", show_detail)
        if rows:
            first = tree.get_children()[0]
            tree.selection_set(first)
            tree.focus(first)
            show_detail()
        actions = ttk.Frame(window, style="Chrome.TFrame")
        actions.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right", padx=4)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        return rows

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
        event = getattr(self, "upcoming_event_rows", {}).get(selected[0])
        if event is None:
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
        cancelled_references = {
            reference for fight in event.get("fights", [])
            for reference in self.event_fight_participant_references(fight) if reference != "TBA"
        }
        super_event = event.get("super_event")
        if isinstance(super_event, dict) and hasattr(self, "close_super_event_project"):
            close_result = self.close_super_event_project(
                super_event, outcome="Cancelled",
                reason="The scheduled card was cancelled before execution.",
                event_name=event.get("name", ""),
            )
            if isinstance(close_result, dict) and close_result.get("needs_review"):
                self.reset_cancel_card_confirmation()
                self.set_matchmaking_notice(
                    "Cancellation paused: the linked super-event project changed. "
                    "Refresh the project and review its current terms before trying again."
                )
                return
        if hasattr(self, "cancel_regional_invitation_for_event"):
            self.cancel_regional_invitation_for_event(
                event, reason="The linked regional-host card was cancelled before execution.",
            )
        self.scheduled_events.remove(event)
        still_booked = {
            reference for other in self.scheduled_events for fight in other.get("fights", [])
            for reference in self.event_fight_participant_references(fight) if reference != "TBA"
        }
        for reference in cancelled_references - still_booked:
            fighter = self._resolve_event_fighter(reference)
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
            for fighter in self.event_fight_fighters(fight):
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
        unavailable = []
        for fight in self.booked:
            for name in self.event_fight_participants(fight):
                if name == "TBA":
                    continue
                fighter = self._resolve_event_fighter(name)
                if fighter is None:
                    unavailable.append(name)
                elif fighter.injured:
                    injured.append(name)
        if unavailable:
            self.set_schedule_status(
                "DATE NOT CHANGED: Fighter identity is unavailable or ambiguous: " + ", ".join(sorted(set(unavailable))),
                "error",
            )
            return
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
        window = self.create_managed_window()
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

        # Keep routine editor validation and replacement feedback in the
        # managed card surface. Explicit scheduling/cancellation confirmations
        # remain separate, but a missing selection or stale fighter should not
        # interrupt the player with a stack of transient dialogs.
        editor_status_var = tk.StringVar(value="Select fighters or a booked bout to review the next card action.")
        editor_status = tk.Label(
            window, textvariable=editor_status_var, anchor="w", justify="left",
            bg=self.colors["chrome"], fg=self.colors.get("gold", "#e0b85c"),
            font=("Tahoma", 9, "bold"), padx=8, pady=4,
        )
        editor_status.pack(fill="x", padx=8, pady=(4, 0))
        editor_status.bind("<Configure>", lambda event: editor_status.configure(wraplength=max(320, event.width - 18)))

        def set_editor_status(message, warning=False):
            editor_status_var.set(str(message))
            editor_status.configure(fg="#ffb08a" if warning else self.colors.get("gold", "#e0b85c"))

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
        red_plan_var = tk.StringVar(value="Balanced")
        blue_plan_var = tk.StringVar(value="Balanced")
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

        plan_controls = ttk.Frame(available, style="Inset.TFrame")
        plan_controls.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(plan_controls, text="Corner A plan", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        red_plan_box = ttk.Combobox(
            plan_controls, values=FIGHT_PLANS, textvariable=red_plan_var,
            state="readonly", width=19,
        )
        red_plan_box.pack(side="left", padx=(0, 7))
        ttk.Label(plan_controls, text="Corner B plan", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        blue_plan_box = ttk.Combobox(
            plan_controls, values=FIGHT_PLANS, textvariable=blue_plan_var,
            state="readonly", width=19,
        )
        blue_plan_box.pack(side="left", padx=(0, 3))
        self.attach_tooltip(red_plan_box, "Plan for the first selected fighter, or the known fighter in a TBA bout.")
        self.attach_tooltip(blue_plan_box, "Plan for the second selected fighter. A future TBA replacement begins Balanced.")

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

        # Explicit last-minute replacement controls. The dropdown is fed by a
        # read-only same-division readiness adapter and includes both company
        # and world rank so the player can make an informed short-notice choice.
        replacement_corner_var = tk.StringVar(value="")
        replacement_var = tk.StringVar(value="")
        replacement_choices = {}
        replacement_corner_choices = {}
        replacement_controls = ttk.Frame(card, style="Inset.TFrame")
        replacement_controls.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(replacement_controls, text="LAST-MINUTE REPLACEMENT", style="Inset.TLabel").pack(side="left", padx=(4, 6), pady=5)
        ttk.Label(replacement_controls, text="Corner", style="Inset.TLabel").pack(side="left", padx=(0, 2), pady=5)
        replacement_corner_box = ttk.Combobox(replacement_controls, textvariable=replacement_corner_var, state="readonly", width=18)
        replacement_corner_box.pack(side="left", padx=(0, 6), pady=5)
        ttk.Label(replacement_controls, text="Ready fighter", style="Inset.TLabel").pack(side="left", padx=(0, 2), pady=5)
        replacement_box = ttk.Combobox(replacement_controls, textvariable=replacement_var, state="readonly", width=48)
        replacement_box.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        replacement_button = ttk.Button(replacement_controls, text="Offer Replacement", style="Accent.TButton")
        replacement_button.pack(side="right", padx=(0, 3), pady=5)
        replacement_hint_var = tk.StringVar(value="Select a booked bout to review ready same-division options.")
        ttk.Label(card, textvariable=replacement_hint_var, style="Inset.TLabel", anchor="w").pack(fill="x", padx=10, pady=(0, 5))

        def normalize_event_order():
            self.normalize_card_order(event.get("fights", []))
            self.refresh_scheduled_event_auto_name(event)
            event_name_var.set(event.get("name", ""))
            update_header()

        def current_names():
            return {
                reference for fight in event.get("fights", [])
                for reference in self.event_fight_participant_references(fight) if reference != "TBA"
            }

        def other_booked_names():
            return {
                reference for other in self.scheduled_events if other is not event
                for fight in other.get("fights", [])
                for reference in self.event_fight_participant_references(fight) if reference != "TBA"
            }

        def refresh_available_editor(*_args):
            available_tree.delete(*available_tree.get_children())
            booked_here = current_names()
            booked_elsewhere = other_booked_names()
            division_ranks = self.player_division_rank_map()
            closed = set(getattr(self, "closed_divisions", set()))
            for fighter in sorted(self.roster, key=lambda item: (item.weight, item.gender, -item.overall, item.name)):
                if fighter.fighter_id in booked_here or fighter.fighter_id in booked_elsewhere:
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

        card_tree_fights = {}

        def fight_editor_ui_identity(fight, *, used_ids=None):
            """Return a stable presentation key for an editor bout row."""
            fight = fight if isinstance(fight, dict) else {}
            source_id = ""
            for field in ("fight_id", "bout_id", "booking_id", "match_id"):
                source_id = str(fight.get(field, "") or "").strip()
                if source_id:
                    break
            if source_id:
                base = f"fight:{source_id}"
            else:
                basis = {
                    "fighter_ids": fight.get("fighter_ids", []),
                    "fighters": fight.get("fighters", []),
                    "tier": fight.get("tier", ""),
                    "title": bool(fight.get("title", False)),
                    "divisional_title": bool(fight.get("divisional_title", False)),
                    "interim": bool(fight.get("interim", False)),
                    "special_belt": fight.get("special_belt", ""),
                    "tournament": bool(fight.get("tournament", False)),
                }
                encoded = json.dumps(basis, sort_keys=True, separators=(",", ":"), default=str)
                base = "legacy-fight:" + hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:20]
            if used_ids is None:
                return base
            candidate = base
            suffix = 2
            while candidate in used_ids:
                candidate = f"{base}#{suffix}"
                suffix += 1
            used_ids.add(candidate)
            return candidate

        def refresh_card_editor(select_index=None):
            normalize_event_order()
            prior_selection = card_tree.selection()
            prior_fight = card_tree_fights.get(prior_selection[0]) if prior_selection else None
            card_tree.delete(*card_tree.get_children())
            card_tree_fights.clear()
            used_fight_ids = set()
            tier_counts = {}
            for index, fight in enumerate(event.get("fights", [])):
                names = fight.get("fighters", [])
                matchup = " vs ".join(names) if names else "Tournament"
                named = self.event_fight_fighters(fight)
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
                row_id = fight_editor_ui_identity(fight, used_ids=used_fight_ids)
                card_tree_fights[row_id] = fight
                card_tree.insert("", "end", iid=row_id, values=(slot, matchup, fight.get("tier", "Main Card"), stakes, weight, build, fatigue, recovery))
            selected_fight = None
            if select_index is not None and 0 <= select_index < len(event.get("fights", [])):
                selected_fight = event["fights"][select_index]
            elif prior_fight is not None:
                selected_fight = prior_fight
            if selected_fight is not None:
                selected_row = next((row_id for row_id, row_fight in card_tree_fights.items() if row_fight is selected_fight), None)
                if selected_row:
                    card_tree.selection_set(selected_row)
                    card_tree.focus(selected_row)
            refresh_available_editor()
            refresh_replacement_controls()
            self.refresh_upcoming()

        def selected_card_index():
            selected = card_tree.selection()
            fight = card_tree_fights.get(selected[0]) if selected else None
            if fight is None:
                return None
            return next((index for index, item in enumerate(event.get("fights", [])) if item is fight), None)

        def add_fight(tba=False):
            selected = available_tree.selection()
            needed = 1 if tba else 2
            if len(selected) != needed:
                set_editor_status(f"BOOKING BLOCKED: Select exactly {needed} eligible fighter{'s' if needed > 1 else ''}.", warning=True)
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
                set_editor_status(f"BOOKING BLOCKED: {details}", warning=True)
                return
            if not tba and (fighters[0].gender != fighters[1].gender or fighters[0].weight != fighters[1].weight):
                set_editor_status("BOOKING BLOCKED: Booked opponents must share a gender and weight class.", warning=True)
                return
            names = [fighters[0].name, "TBA"] if tba else [fighter.name for fighter in fighters]
            title = bool(title_var.get())
            interim = self.divisional_title_is_interim(fighters, title)
            fight = {
                "fighters": names,
                "fighter_ids": [fighters[0].fighter_id, ""] if tba else [fighter.fighter_id for fighter in fighters],
                "title": title,
                "divisional_title": title,
                "interim": interim,
                "main": not event.get("fights"),
                "tier": tier_var.get(),
                "fight_plans": {
                    fighters[0].fighter_id: self.normalize_fight_plan(red_plan_var.get()),
                    **({} if tba else {
                        fighters[1].fighter_id: self.normalize_fight_plan(blue_plan_var.get()),
                    }),
                },
            }
            if tba:
                fight.update({"tba_weight": fighters[0].weight, "tba_gender": fighters[0].gender})
            event.setdefault("fights", []).append(fight)
            # Only the newly added athletes receive a new camp assignment.
            self.assign_event_camps({"month": event["month"], "week": event.get("week", 1), "fights": [fight]})
            refresh_card_editor(len(event["fights"]) - 1)
            set_editor_status(f"ADDED: {fighters[0].name} is now on the card" + (" with a TBA opponent." if tba else f" opposite {fighters[1].name}."))
            red_plan_var.set("Balanced")
            blue_plan_var.set("Balanced")

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
            named = self.event_fight_fighters(fight)
            current_divisional = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            fight["divisional_title"] = not current_divisional
            fight["title"] = bool(fight["divisional_title"] or fight.get("special_belt"))
            fight["interim"] = self.divisional_title_is_interim(named, fight["divisional_title"])
            refresh_card_editor(index)

        def replace_selected_tba():
            index = selected_card_index()
            selected = available_tree.selection()
            if index is None or len(selected) != 1:
                set_editor_status("REPLACEMENT BLOCKED: Select the TBA fight, then select one eligible replacement fighter.", warning=True)
                return
            fight = event["fights"][index]
            if fight.get("tournament") or "TBA" not in fight.get("fighters", []):
                set_editor_status("REPLACEMENT BLOCKED: The selected booking does not have a replaceable TBA slot.", warning=True)
                return
            replacement = next((fighter for fighter in self.roster if fighter.fighter_id == selected[0]), None)
            if not replacement:
                return
            replacement_status = self.fighter_booking_status(replacement, event["month"], event.get("week", 1))
            if replacement_status != "Ready":
                set_editor_status(f"REPLACEMENT BLOCKED: {replacement.name}: {replacement_status}", warning=True)
                return
            booked_fighters = self.event_fight_fighters(fight)
            tba_weight = fight.get("tba_weight") or next((fighter.weight for fighter in booked_fighters), "")
            tba_gender = fight.get("tba_gender") or next((fighter.gender for fighter in booked_fighters), "")
            if replacement.weight != tba_weight or replacement.gender != tba_gender:
                set_editor_status(f"REPLACEMENT BLOCKED: The replacement must be a {tba_gender} {tba_weight}.", warning=True)
                return
            fight["fighters"] = [replacement.name if name == "TBA" else name for name in fight["fighters"]]
            fighter_ids = list(fight.get("fighter_ids", []))
            if len(fighter_ids) != len(fight["fighters"]):
                fighter_ids = [getattr(self._resolve_event_fighter(name), "fighter_id", "") if name != "TBA" else "" for name in fight["fighters"]]
            fight["fighter_ids"] = [replacement.fighter_id if not fighter_id else fighter_id for fighter_id in fighter_ids]
            fight.setdefault("fight_plans", {})[replacement.fighter_id] = "Balanced"
            fight["tba_filled"] = True
            fight["tba_note"] = f"{replacement.name} was confirmed through the booked-card editor."
            named = self.event_fight_fighters(fight)
            divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
            fight["divisional_title"] = divisional_title
            fight["title"] = bool(divisional_title or fight.get("special_belt"))
            fight["interim"] = self.divisional_title_is_interim(named, divisional_title)
            # Camp only the incoming replacement; the original fighter's camp
            # has already been prepared for this scheduled event.
            self.assign_event_camps({"month": event["month"], "week": event.get("week", 1), "fights": [{"fighters": [replacement.name], "fighter_ids": [replacement.fighter_id]}]})
            self.news.insert(0, f"{replacement.name} replaces TBA on {event.get('name', 'an upcoming event')}." )
            refresh_card_editor(index)
            set_editor_status(f"REPLACEMENT STAGED: {replacement.name} now fills the TBA slot. Review the card before closing.")

        def refresh_replacement_controls():
            replacement_choices.clear()
            replacement_corner_choices.clear()
            index = selected_card_index()
            if index is None or index >= len(event.get("fights", [])):
                replacement_corner_box.configure(values=[])
                replacement_box.configure(values=[])
                replacement_corner_var.set("")
                replacement_var.set("")
                replacement_button.configure(state="disabled")
                replacement_hint_var.set("Select a booked bout to review ready same-division options.")
                return
            fight = event["fights"][index]
            if fight.get("tournament"):
                replacement_corner_box.configure(values=[])
                replacement_box.configure(values=[])
                replacement_corner_var.set("")
                replacement_var.set("")
                replacement_button.configure(state="disabled")
                replacement_hint_var.set("Tournament alternates use the tournament field flow.")
                return
            names = list(fight.get("fighters", []) or [])
            while len(names) < 2:
                names.append("TBA")
            corner_values = []
            for corner in (0, 1):
                label = f"{chr(65 + corner)}: {names[corner] or 'TBA'}"
                replacement_corner_choices[label] = corner
                corner_values.append(label)
            replacement_corner_box.configure(values=corner_values)
            current_corner = replacement_corner_var.get()
            if current_corner not in corner_values:
                current_corner = next((label for label in corner_values if label.endswith(": TBA")), corner_values[0])
                replacement_corner_var.set(current_corner)
            corner_index = replacement_corner_choices.get(current_corner, 0)
            rows = self.last_minute_replacement_candidates(event, fight, corner_index)
            values = []
            for row in rows:
                display = (
                    f"{row['name']} | Company {row['company_rank']} | World {row['world_rank']} | "
                    f"{row['record']} | {row['readiness']}"
                )
                replacement_choices[display] = row["fighter_id"]
                values.append(display)
            replacement_box.configure(values=values)
            if values:
                if replacement_var.get() not in values:
                    replacement_var.set(values[0])
                replacement_button.configure(state="normal")
                named = self.event_fight_fighters(fight)
                division = fight.get("tba_weight") or (named[0].weight if named else "the selected division")
                replacement_hint_var.set(
                    f"{len(values)} ready {division} options. Ranks are current snapshots; choosing one does not commit until Offer Replacement."
                )
            else:
                replacement_var.set("")
                replacement_button.configure(state="disabled")
                replacement_hint_var.set("No ready same-division fighter is available for this corner on the event date.")

        def commit_selected_replacement():
            index = selected_card_index()
            replacement_id = replacement_choices.get(replacement_var.get())
            corner = replacement_corner_choices.get(replacement_corner_var.get())
            if index is None or not replacement_id or corner is None:
                set_editor_status("REPLACEMENT BLOCKED: Select a booked bout, corner and ready fighter first.", warning=True)
                return
            fight = event["fights"][index]
            ok, note = self.commit_last_minute_replacement(event, fight, replacement_id, corner)
            if not ok:
                set_editor_status(f"REPLACEMENT BLOCKED: {note}", warning=True)
                refresh_replacement_controls()
                return
            set_editor_status(note + " Existing opponent and prior booking evidence remain unchanged.")
            refresh_card_editor(index)

        def set_selected_tier():
            index = selected_card_index()
            if index is None:
                return
            event["fights"][index]["tier"] = tier_var.get()
            refresh_card_editor(index)

        def load_selected_plans(_event=None):
            index = selected_card_index()
            if index is None:
                return
            fight = event["fights"][index]
            fighter_ids = list(fight.get("fighter_ids", []))
            plans = fight.get("fight_plans", {}) if isinstance(fight.get("fight_plans", {}), dict) else {}
            red_plan_var.set(self.normalize_fight_plan(plans.get(fighter_ids[0], "Balanced")) if fighter_ids else "Balanced")
            blue_plan_var.set(self.normalize_fight_plan(plans.get(fighter_ids[1], "Balanced")) if len(fighter_ids) > 1 and fighter_ids[1] else "Balanced")

        def apply_selected_plans():
            index = selected_card_index()
            if index is None:
                return
            fight = event["fights"][index]
            fighter_ids = list(fight.get("fighter_ids", []))
            plans = {}
            if fighter_ids and fighter_ids[0]:
                plans[fighter_ids[0]] = self.normalize_fight_plan(red_plan_var.get())
            if len(fighter_ids) > 1 and fighter_ids[1]:
                plans[fighter_ids[1]] = self.normalize_fight_plan(blue_plan_var.get())
            fight["fight_plans"] = plans
            refresh_card_editor(index)

        ttk.Button(card_controls, text="Remove", command=remove_selected).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Replace TBA (legacy)", command=replace_selected_tba).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Title / Interim", command=toggle_selected_title).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Move Up", command=lambda: move_selected(-1)).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Move Down", command=lambda: move_selected(1)).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Set Tier", command=set_selected_tier).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Apply Plans", command=apply_selected_plans).pack(side="left", padx=3, pady=4)
        ttk.Button(card_controls, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right", padx=3, pady=4)
        replacement_button.configure(command=commit_selected_replacement)

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
        card_tree.bind("<<TreeviewSelect>>", load_selected_plans, add="+")
        replacement_corner_box.bind("<<ComboboxSelected>>", lambda _event: refresh_replacement_controls())
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
        event_key = self.fight_night_event_key(event)
        decision_key = "decision:due-event:" + hashlib.sha1(repr(event_key).encode("utf-8")).hexdigest()[:16]
        existing = self.focus_managed_window(decision_key) if hasattr(self, "focus_managed_window") else None
        if existing is not None:
            return True
        if not hasattr(self, "create_managed_window"):
            # Headless/legacy callers do not have the themed window registry;
            # retain their explicit three-way choice without affecting normal
            # application behaviour.
            choice = messagebox.askyesnocancel("Fight Day", f"{event['name']} is due in {self.event_date_label(event)}.{retirement_warning}{comeback_warning}\n\nYes = Watch live\nNo = Sim instantly\nCancel = stay on this week")
            if choice is True:
                if self.focus_active_live_fight_window():
                    return True
                package = self.prepare_event_result(event)
                self.open_live_fight_window(event, package)
                return True
            if choice is False:
                package = self.prepare_event_result(event)
                self.finish_event(event, package)
                self.select_tab("log")
                return True
            return True

        # Fight day is a routine, repeatable choice rather than a destructive
        # confirmation.  Keep it on the same themed surface as the rest of the
        # game so the consequence and the safe stay-on-this-week path are clear.
        window = self.create_managed_window(decision_key)
        window.title("Fight Day Decision")
        window.geometry("600x360")
        window.minsize(520, 300)
        window.configure(bg=self.colors.get("chrome", "#1f2830"))
        ttk.Label(window, text="FIGHT DAY", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(12, 2))
        ttk.Label(window, text=f"{event['name']} • {self.event_date_label(event)}", style="Section.TLabel").pack(anchor="w", padx=14, pady=(0, 10))
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        copy = (
            "The card is due now. Choose how to resolve it; nothing is prepared or settled until you choose.\n\n"
            "WATCH LIVE opens the broadcast viewer. SIMULATE NOW seals the result immediately. "
            "STAY ON THIS WEEK closes this panel and leaves the card unresolved."
        )
        if retirement_warning or comeback_warning:
            copy += retirement_warning + comeback_warning
        ttk.Label(body, text=copy, style="Inset.TLabel", anchor="w", justify="left", wraplength=540).pack(fill="x", padx=12, pady=14)
        actions = ttk.Frame(body, style="Inset.TFrame")
        actions.pack(fill="x", side="bottom", padx=8, pady=10)

        def close():
            try:
                window.destroy()
            except tk.TclError:
                pass

        def resolve(mode):
            current = next((item for item in self.sorted_scheduled_events() if self.fight_night_event_key(item) == event_key), None)
            if current is None or not self.is_event_due(current):
                close()
                return
            close()
            if mode == "watch":
                if self.focus_active_live_fight_window():
                    return
                package = self.prepare_event_result(current)
                self.open_live_fight_window(current, package)
            elif mode == "simulate":
                package = self.prepare_event_result(current)
                self.finish_event(current, package)
                self.select_tab("log")

        ttk.Button(actions, text="Watch Live", style="Accent.TButton", command=lambda: resolve("watch")).pack(side="left", padx=4, ipadx=9, ipady=4)
        ttk.Button(actions, text="Simulate Now", command=lambda: resolve("simulate")).pack(side="left", padx=4, ipadx=9, ipady=4)
        ttk.Button(actions, text="Stay on This Week", command=close).pack(side="right", padx=4, ipadx=9, ipady=4)
        window.protocol("WM_DELETE_WINDOW", close)
        return True

    def evolve_trait_from_camp(self, fighter, quality, weeks_out):
        change = progress_camp_trait(fighter, quality, weeks_out, self.month)
        if change:
            self.news.insert(0, f"Camp report: {fighter.name} developed from {change['from']} to {change['to']} after sustained preparation.")

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

    def title_miss_decision_read_model(self, event):
        """Project retained title-miss decisions for readers and archives.

        The projection is deliberately source-bound and read-only.  It keeps
        the saved participant references, choices and sanction snapshot
        together so Results, Upcoming Cards and future decision handlers do
        not each invent a different interpretation of the same weigh-in.
        A missing fight ID is reported as a legacy reference and is never
        promoted to a durable action key.
        """
        event = event if isinstance(event, dict) else {}
        fights = event.get("fights", []) if isinstance(event.get("fights", []), list) else []
        rows = []
        reference_helper = getattr(self, "event_fight_participant_references", None)
        for ordinal, fight in enumerate(fights, 1):
            if not isinstance(fight, dict):
                continue
            state = fight.get("title_miss_decision_state") if isinstance(fight.get("title_miss_decision_state"), dict) else {}
            sanction = fight.get("title_sanction_snapshot") if isinstance(fight.get("title_sanction_snapshot"), dict) else {}
            settlement = sanction.get("settlement") if isinstance(sanction.get("settlement"), dict) else state.get("settlement", {})
            if not state and not sanction:
                continue
            try:
                raw_refs = reference_helper(fight) if callable(reference_helper) else fight.get("fighters", [])
            except (TypeError, ValueError, AttributeError):
                raw_refs = fight.get("fighters", [])
            references = [str(value) for value in raw_refs if value and str(value) != "TBA"] if isinstance(raw_refs, (list, tuple)) else []
            raw_choices = state.get("choices") if isinstance(state.get("choices"), list) else []
            choices = [str(value) for value in raw_choices if str(value) in self.TITLE_MISS_ACTIONS]
            if not choices:
                choices = list(self.TITLE_MISS_ACTIONS)
            missed = sanction.get("missed_corners") if isinstance(sanction.get("missed_corners"), list) else state.get("corners", [])
            corner_eligibility = []
            if isinstance(missed, list):
                for corner in missed:
                    if not isinstance(corner, dict):
                        continue
                    # New snapshots carry explicit booleans.  Legacy rows do
                    # not: keep those values unknown rather than deriving a
                    # current eligibility from mutable roster/ranking state.
                    def stored_bool(key):
                        if key not in corner:
                            return None
                        value = corner.get(key)
                        return value if isinstance(value, bool) else None

                    corner_eligibility.append({
                        "corner": corner.get("corner", len(corner_eligibility)),
                        "fighter_id": str(corner.get("fighter_id", "") or ""),
                        "fighter": str(corner.get("fighter", corner.get("name", "")) or ""),
                        "special_belt_holder": stored_bool("special_belt_holder"),
                        "eligible_to_win": stored_bool("eligible_to_win"),
                        "eligible_to_retain": stored_bool("eligible_to_retain"),
                    })
            explicit_belt_id = str(
                state.get("belt_id", sanction.get("belt_id", fight.get("belt_id", fight.get("title_id", "")))) or ""
            )
            title_key = str(state.get("title_key", sanction.get("title_key", "")) or "")
            if not title_key:
                special_belt = str(fight.get("special_belt", "") or "")
                if special_belt:
                    title_key = f"special:{special_belt}"
                elif fight.get("gender") and fight.get("weight"):
                    # Only use scope facts explicitly retained on a legacy
                    # fight. Never infer an at-the-time belt from a fighter's
                    # current mutable division after a later move/rename.
                    title_key = f"division:{fight.get('gender')}:{fight.get('weight')}"
            rows.append({
                "fight_id": str(fight.get("fight_id", "") or fight.get("bout_id", "") or ""),
                "fight_ordinal": ordinal,
                "legacy_reference": not bool(str(fight.get("fight_id", "") or fight.get("bout_id", "") or "").strip()),
                "fighter_references": references,
                "belt_id": explicit_belt_id,
                "title_key": title_key,
                # A legacy or partially migrated row may retain only the
                # sanction envelope. An explicit review flag still means the
                # card is blocked; surface that state instead of making the
                # player rediscover it by opening Watch or Simulate.
                "status": str(
                    state.get("status", "")
                    or ("needs_review" if sanction.get("review_required") else "")
                ),
                "action": str(state.get("action", sanction.get("decision", "")) or ""),
                "reason": str(state.get("reason", "") or ""),
                "choices": choices,
                "replacement_id": str(state.get("replacement_id", sanction.get("replacement_id", "")) or ""),
                "scheduled_title": bool(
                    state.get(
                        "title_stakes_before",
                        fight.get("title") or fight.get("divisional_title") or fight.get("special_belt"),
                    )
                ),
                "on_line": bool(sanction.get("on_line", False)),
                "vacated_before_bout": bool(sanction.get("vacated_before_bout", False)),
                "champion_miss_waived": bool(sanction.get("champion_miss_waived", False)),
                "missed_corners": deepcopy(missed) if isinstance(missed, list) else [],
                "corner_eligibility": corner_eligibility,
                "settlement": deepcopy(settlement) if isinstance(settlement, dict) else {},
            })
        return rows

    def title_sanction_settlement_evidence(self, fight, winner=None, loser=None, method=""):
        """Return observed post-settlement evidence for a recorded title miss.

        This is an evidence writer called only from the existing settlement
        transaction.  It does not decide eligibility, create a sanction or
        rerun rankings; it records the result that the ordinary title/belt
        owners already applied.  Missing legacy role fields remain unknown.
        """
        if not isinstance(fight, dict):
            return {}
        sanction = fight.get("title_sanction_snapshot") if isinstance(fight.get("title_sanction_snapshot"), dict) else {}
        state = fight.get("title_miss_decision_state") if isinstance(fight.get("title_miss_decision_state"), dict) else {}
        scheduled_title = bool(
            sanction.get("scheduled_title", state.get("title_stakes_before", False))
            or fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
        )
        if not scheduled_title and not sanction and not state:
            return {}
        on_line = bool(
            sanction.get("on_line", False)
            if "on_line" in sanction
            else state.get("on_line", scheduled_title)
        )
        method = str(method or "").strip() or "Unknown"
        winner_id = str(getattr(winner, "fighter_id", "") or "")
        loser_id = str(getattr(loser, "fighter_id", "") or "")
        corners = sanction.get("missed_corners") if isinstance(sanction.get("missed_corners"), list) else state.get("corners", [])

        def role_before(fighter, *keys):
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            for corner in corners if isinstance(corners, list) else []:
                if not isinstance(corner, dict):
                    continue
                saved_id = str(corner.get("fighter_id", "") or "")
                if fighter_id and saved_id and saved_id == fighter_id:
                    observed = []
                    for key in keys:
                        if key in corner and isinstance(corner.get(key), bool):
                            observed.append(bool(corner[key]))
                    if not observed:
                        return None
                    # Older snapshots may contain explicit false generic
                    # champion flags even when the corner held a named belt.
                    # Preserve the additive retain-eligibility evidence as a
                    # truthful fallback instead of mislabelling a defence as
                    # a new title win.
                    if not any(observed) and corner.get("eligible_to_retain") is True:
                        return True
                    return any(observed)
            return None

        winner_was_holder = role_before(winner, "champion", "interim_champion", "special_belt_holder")
        if winner_was_holder is None:
            winner_was_holder = role_before(winner, "eligible_to_retain")
        loser_was_holder = role_before(loser, "champion", "interim_champion", "special_belt_holder")
        if loser_was_holder is None:
            loser_was_holder = role_before(loser, "eligible_to_retain")
        winner_is_holder = bool(
            getattr(winner, "champion", False) or getattr(winner, "interim_champion", False)
        ) if winner is not None else False
        loser_is_holder = bool(
            getattr(loser, "champion", False) or getattr(loser, "interim_champion", False)
        ) if loser is not None else False
        special_name = str(fight.get("special_belt", "") or "")
        if special_name:
            belt = getattr(self, "special_belts", {})
            belt = belt.get(special_name) if isinstance(belt, dict) else None
            holder_id = str(belt.get("holder_id", "") or "") if isinstance(belt, dict) else ""
            holder_name = str(belt.get("holder", "") or "") if isinstance(belt, dict) else ""
            winner_is_holder = bool(
                winner is not None and (
                    (holder_id and holder_id == winner_id)
                    or (not holder_id and holder_name and holder_name == getattr(winner, "name", ""))
                )
            )
            loser_is_holder = bool(
                loser is not None and (
                    (holder_id and holder_id == loser_id)
                    or (not holder_id and holder_name and holder_name == getattr(loser, "name", ""))
                )
            )
        if not on_line:
            outcome = "not_contested"
            reason = "The saved sanction kept the title off the line; the official result made no title change."
        elif method in {"Draw", "No Contest"}:
            outcome = "unchanged"
            reason = f"The official result was {method}; the recorded holder/title state remained unchanged."
        elif winner_is_holder:
            outcome = (
                "retained" if winner_was_holder is True
                else "won" if winner_was_holder is False
                else "holder_after"
            )
            reason = (
                "The official winner retained the recorded title."
                if outcome == "retained" else
                "The official winner became the recorded title holder."
                if outcome == "won" else
                "The official winner is the recorded title holder; the pre-bout holder role was not retained."
            )
        elif loser_is_holder and winner is not None:
            outcome = "transferred"
            reason = "The official result transferred the recorded title away from the prior holder."
        else:
            outcome = "unchanged"
            reason = "The official result completed without a recorded title-holder change."
        return {
            "schema_version": 1,
            "method": method,
            "winner_id": winner_id,
            "loser_id": loser_id,
            "title_on_line": on_line,
            "outcome": outcome,
            "reason": reason,
            "winner_was_holder": winner_was_holder,
            "loser_was_holder": loser_was_holder,
            "winner_is_holder_after": winner_is_holder,
            "loser_is_holder_after": loser_is_holder,
        }

    def event_preparation_timeline(self, event, press_log=None, weigh_log=None, cancelled_fights=None):
        """Build a display-safe preparation timeline from recorded outcomes.

        This is deliberately a presentation/read-model boundary.  It does not
        resolve press, weigh-ins, readiness, or fights; callers pass the logs
        that the existing event resolver already produced.  The resulting
        dictionary is stored with the normal event package so the same cards are
        available from the archive after settlement.
        """
        event = event if isinstance(event, dict) else {}
        press = [str(value) for value in (press_log or [])]
        weigh = [str(value) for value in (weigh_log or [])]
        cancelled = list(cancelled_fights or [])
        fighter_ids = []
        reference_helper = getattr(self, "event_fight_participant_references", None)
        if callable(reference_helper):
            for fight in event.get("fights", []) if isinstance(event.get("fights", []), list) else []:
                try:
                    refs = reference_helper(fight) or []
                except Exception:
                    refs = []
                fighter_ids.extend(str(value) for value in refs if value and str(value) != "TBA")
        fighter_ids = list(dict.fromkeys(fighter_ids))
        event_id = str(event.get("event_id", "") or event.get("id", "") or event.get("name", ""))
        campaign_evidence = []
        finance = getattr(self, "finance", {})
        plan = finance.get("media_primary_plan") if isinstance(finance, dict) else None
        if isinstance(plan, dict) and str(plan.get("target_id", "")) == event_id:
            for receipt in plan.get("action_receipts", []) if isinstance(plan.get("action_receipts", []), list) else []:
                if not isinstance(receipt, dict):
                    continue
                evidence = str(receipt.get("evidence_key", "") or "")
                if evidence:
                    campaign_evidence.append({
                        "plan_id": str(plan.get("plan_id", "") or ""),
                        "objective": str(plan.get("objective", "") or ""),
                        "action": str(receipt.get("action", "") or ""),
                        "evidence_key": evidence,
                    })
        cancelled_count = len(cancelled)
        # Title-miss decisions are part of the preparation evidence, not a
        # second settlement record.  Keep a compact, plain-data projection in
        # the timeline so the archive can explain why a bout stayed on the card,
        # was rebooked/cancelled, or lost its sanction without reopening the
        # original prompt or recomputing rankings.
        title_miss_decisions = self.title_miss_decision_read_model(event)
        if cancelled_count:
            readiness = f"Ready with {cancelled_count} cancelled bout(s)"
        elif weigh:
            readiness = "Ready for the recorded card"
        else:
            readiness = "No weigh-in outcome recorded"
        stages = [
            {
                "stage_id": "campaign", "label": "Campaign / media", "status": "Evidence recorded" if campaign_evidence else "No linked campaign evidence",
                "detail": (f"{len(campaign_evidence)} linked campaign action(s)" if campaign_evidence else "No active event-targeted campaign receipt was recorded."),
            },
            {
                "stage_id": "press", "label": "Press conference", "status": "Recorded" if press else "No recorded outcome",
                "detail": f"{len(press)} stored line(s); opening this card does not rerun the resolver.",
            },
            {
                "stage_id": "weigh_in", "label": "Weigh-ins", "status": "Recorded" if weigh else "No recorded outcome",
                "detail": (
                    f"{len(weigh)} stored line(s); {cancelled_count} bout(s) cancelled at this boundary. "
                    f"{len(title_miss_decisions)} title-miss decision(s) retained."
                    if weigh else "No weigh-in output was supplied."
                ),
            },
            {
                "stage_id": "readiness", "label": "Final readiness", "status": readiness,
                "detail": f"{len(fighter_ids)} linked fighter identity/identities retained for this event.",
            },
        ]
        completion_keys = {
            state["stage_id"]: f"event-preparation:{event_id}:{state['stage_id']}:r1"
            for state in stages
            if state.get("status") not in ("No linked campaign evidence", "No recorded outcome", "No weigh-in outcome recorded")
        }
        return {
            "schema_version": 1,
            "event_id": event_id,
            "preparation_revision": 1,
            "stage_states": stages,
            "completion_keys": completion_keys,
            "press_outcomes": press,
            "weigh_in_outcomes": weigh,
            "cancelled_bout_count": cancelled_count,
            "title_miss_decisions": title_miss_decisions,
            "fighter_ids": fighter_ids,
            "campaign_evidence": campaign_evidence,
            "final_readiness": readiness,
        }

    def watch_due_event(self):
        event = self.selected_due_event()
        if not event:
            return
        if self.focus_active_live_fight_window():
            return
        package = self.prepare_event_result(event)
        self.open_live_fight_window(event, package)

    @staticmethod
    def fight_night_event_key(event):
        """Return a stable presentation key without mutating the scheduled card."""
        if not isinstance(event, dict):
            return ()
        return (
            str(event.get("event_id", "") or ""),
            str(event.get("name", "") or ""),
            int(event.get("month", 0) or 0),
            int(event.get("week", 0) or 0),
        )

    @staticmethod
    def fight_night_commentary_rows(lines, mode="Broadcast"):
        """Return ``(source index, text)`` rows for a viewer-only transcript.

        Detailed mode is the complete stored transcript. Broadcast mode removes
        legacy technical suffixes, limits repeated low-value calls within each
        round, and keeps every structural, evidential, scoring, and result line.
        Source indexes let the live viewer change density without revealing
        future commentary or modifying the archived transcript.
        """
        source = list(lines or [])
        normalized_mode = str(mode or "Broadcast").strip().title()
        if normalized_mode == "Detailed":
            return list(enumerate(source))

        suffix_pattern = re.compile(
            r"\s+\[(?=(?:target|defense|next)\b)[^\]]+\]\s*$",
            re.IGNORECASE,
        )
        clock_pattern = re.compile(r"^\s*\[(\d{1,2}:\d{2})\]\s*(.*)$")
        critical_terms = (
            "knockdown", "drops ", "is down", "submission", "tap", "choke", "armbar",
            "cut ", "opens a cut", "swelling", "foul", "point deduct", "referee",
            "bruising", "reddening", "welt", "visible limp", "laboured breathing",
            "guarding the midsection", "protecting the midsection", "shifts weight",
            "shift weight", "weight shifts",
            "facial damage", "head damage", "body damage", "damaged midsection",
            "leg damage", "damaged leg",
            "doctor", "injury", "unconscious", "cannot continue", "stops the fight",
            "finishes the fight", "official result", "technical fall", "secures the pin",
            "position change", "takes the back", "mount", "stance switch", "switches stance",
        )
        ground_positions = (
            "guard", "half guard", "side control", "mount", "back control", "turtle",
            "failed shot", "front headlock", "standing back control", "leg entanglement",
        )
        ground_strike_moves = tuple(
            str(definition.name or "").casefold()
            for definition in MOVE_REGISTRY.values()
            if definition.parent_action == "ground_strikes" and definition.name
        )
        standing_strike_moves = tuple(
            str(definition.name or "").casefold()
            for definition in MOVE_REGISTRY.values()
            if definition.parent_action in {"jab", "power_punch", "kick", "dirty_boxing"}
            and definition.name
        )
        positive_attack_terms = (
            " lands ", " lands the ", " gets through ", " finds ", " scores with ",
            " answers immediately with ",
        )
        denied_terms = (
            " denies ", " stops ", " turned away", " misses ", " does not advance",
            "attempts the ", "tries the ",
        )

        def strip_suffix(value):
            return suffix_pattern.sub("", str(value)).rstrip()

        def repeat_key(value):
            match = clock_pattern.match(value)
            body = match.group(2) if match else value
            body = re.sub(r"\b\d+(?::\d+)?\b", "#", body.casefold())
            return re.sub(r"\s+", " ", body).strip()

        def is_landed_ground_strike(value):
            lowered = f" {value.casefold()} "
            named_ground_strike = any(move in lowered for move in ground_strike_moves)
            legacy_ground_strike = any(term in lowered for term in (
                "ground-and-pound", "short punches from top", "elbows from top control",
                "heavy shots on the mat",
            ))
            return (
                (named_ground_strike or legacy_ground_strike)
                and any(term in lowered for term in positive_attack_terms)
                and not any(term in lowered for term in denied_terms)
            )

        def is_completed_attack(value):
            """Protect successful offense in every range, not one preferred phase."""
            lowered = f" {value.casefold()} "
            return (
                any(term in lowered for term in positive_attack_terms)
                and not any(term in lowered for term in denied_terms)
            )

        def is_meaningful_ground_exchange(value):
            """Protect completed ground progress while leaving failed/routine work compactable."""
            lowered = f" {value.casefold()} "
            if is_landed_ground_strike(value):
                return True
            if any(term in lowered for term in denied_terms):
                return False
            transition_phrases = (
                " move the fight from ", " carries ", " completes the ", " completes it into ",
                " takes the fight to ", " settling in ", " escape from ", " out of ",
                " clears the control ", " reaching ",
            )
            settled_position = any(
                f" to {position}" in lowered
                or f" into {position}" in lowered
                or f" in {position}" in lowered
                for position in (*ground_positions, "range", "pocket", "clinch", "cage")
            )
            return any(term in lowered for term in transition_phrases) and settled_position

        def suppressed_lane(value):
            """Describe omitted evidence without claiming an unrecorded outcome."""
            lowered = value.casefold()
            if any(move in lowered for move in ground_strike_moves) or any(term in lowered for term in (
                    "ground-and-pound", "short punches from top", "elbows from top control",
                    "heavy shots on the mat")):
                return "ground-striking exchange"
            if any(term in lowered for term in (
                    "takedown", "single leg", "single-leg", "double leg", "double-leg",
                    "level change", "shot", "sprawl", "throw", "trip", "mat return", "mat-return")):
                return "takedown exchange"
            if any(position in lowered for position in ground_positions) or any(term in lowered for term in (
                    "on the mat", "from the top", "top control", "ground control", "sweep",
                    "wall-walk", "stand-up", "back to the feet", "back to standing")):
                return "ground-control exchange"
            if any(move in lowered for move in standing_strike_moves) or any(term in lowered for term in (
                    "punch", "kick", "knee", "elbow", "uppercut", "hook", "cross", "jab")):
                return "standing-striking exchange"
            return "standing exchange"

        def summary_copy(suppressed):
            lanes = Counter(suppressed_lane(value) for _index, value in suppressed)
            parts = [
                f"{count} {lane if count == 1 else lane + 's'}"
                for lane, count in (
                    ("ground-striking exchange", lanes["ground-striking exchange"]),
                    ("takedown exchange", lanes["takedown exchange"]),
                    ("ground-control exchange", lanes["ground-control exchange"]),
                    ("standing-striking exchange", lanes["standing-striking exchange"]),
                    ("standing exchange", lanes["standing exchange"]),
                )
                if count
            ]
            if len(parts) > 1:
                detail = ", ".join(parts[:-1]) + f", and {parts[-1]}"
            else:
                detail = parts[0]
            return f"{len(suppressed)} quieter exchanges summarised by factual lane: {detail}."

        def compact_timestamped(group, repeat_memory):
            if not group:
                return []
            retained = []
            suppressed = []
            for original_index, value in group:
                cleaned = strip_suffix(value)
                lowered = cleaned.casefold()
                base_critical = any(term in lowered for term in critical_terms)
                added_evidence = (
                    is_meaningful_ground_exchange(cleaned)
                    or is_completed_attack(cleaned)
                )
                critical = base_critical or added_evidence
                key = repeat_key(cleaned)
                # Evidence priority controls the line budget, not duplicate
                # wording. Even critical facts remain present twice per round,
                # while a third identical call is compacted into the factual
                # lane summary instead of making the broadcast sound stuck.
                if repeat_memory[key] >= 2:
                    suppressed.append((original_index, cleaned))
                    continue
                repeat_memory[key] += 1
                retained.append((original_index, cleaned, critical))

            critical_rows = [row for row in retained if row[2]]
            ordinary_rows = [row for row in retained if not row[2]]
            available = max(0, FIGHT_COMMENTARY_ROUND_LINE_LIMIT - len(critical_rows))
            if len(ordinary_rows) > available:
                if available:
                    # Even coverage keeps the round's opening and closing shape
                    # without using any simulation or presentation RNG.
                    if available == 1:
                        chosen = {0}
                    else:
                        chosen = {
                            round(index * (len(ordinary_rows) - 1) / (available - 1))
                            for index in range(available)
                        }
                    kept_ordinary = [row for index, row in enumerate(ordinary_rows) if index in chosen]
                    dropped_ordinary = [row for index, row in enumerate(ordinary_rows) if index not in chosen]
                else:
                    kept_ordinary, dropped_ordinary = [], ordinary_rows
                retained = critical_rows + kept_ordinary
                suppressed.extend((row[0], row[1]) for row in dropped_ordinary)

            output = [(index, value) for index, value, _critical in retained]
            if suppressed:
                first_index, first_line = min(suppressed, key=lambda row: row[0])
                clock = clock_pattern.match(first_line)
                clock_copy = f"  [{clock.group(1)}] " if clock else ""
                summary = f"{clock_copy}Broadcast note: {summary_copy(suppressed)}"
                output.append((first_index, summary))
            return sorted(output, key=lambda row: row[0])

        rendered = []
        timestamped = []
        repeat_memory = Counter()
        for index, value in enumerate(source):
            cleaned = strip_suffix(value)
            if clock_pattern.match(cleaned):
                timestamped.append((index, value))
                continue
            rendered.extend(compact_timestamped(timestamped, repeat_memory))
            timestamped = []
            rendered.append((index, cleaned))
            upper = cleaned.strip().upper()
            if (
                re.match(r"^(?:ROUND|PERIOD)\s+\d+", upper)
                or upper.startswith("MATCH CLOCK")
                or " SUMMARY:" in upper
                or upper.startswith(("RESULT:", "OFFICIAL RESULT"))
            ):
                repeat_memory.clear()
        rendered.extend(compact_timestamped(timestamped, repeat_memory))
        return rendered

    @classmethod
    def fight_night_commentary_lines(cls, lines, mode="Broadcast"):
        """Return the text portion of a non-mutating viewer transcript."""
        return [value for _source_index, value in cls.fight_night_commentary_rows(lines, mode)]

    @classmethod
    def fight_night_presentation_logs(cls, fight_logs, mode="Broadcast"):
        """Clone logs for one viewer while retaining their complete transcript."""
        presented = []
        for raw in fight_logs or []:
            row = dict(raw)
            detailed = list(raw.get("detailed_lines", raw.get("lines", [])) or [])
            commentary_rows = cls.fight_night_commentary_rows(detailed, mode=mode)
            row["detailed_lines"] = detailed
            row["lines"] = [value for _source_index, value in commentary_rows]
            row["_line_source_indices"] = [source_index for source_index, _value in commentary_rows]
            presented.append(row)
        return presented

    @staticmethod
    def fight_night_source_cutoff(presented_log, displayed_count):
        """Map visible progress back to the complete archived line stream."""
        detailed = list(presented_log.get("detailed_lines", presented_log.get("lines", [])) or [])
        indexes = list(presented_log.get("_line_source_indices", range(len(presented_log.get("lines", [])))) or [])
        count = max(0, min(int(displayed_count or 0), len(indexes)))
        if count <= 0:
            return 0
        return min(len(detailed), max(indexes[:count]) + 1)

    @classmethod
    def fight_night_presentation_progress(cls, raw_log, mode, source_cutoff):
        """Build one density view and locate the same sealed playback frontier."""
        presented = cls.fight_night_presentation_logs([raw_log], mode=mode)[0]
        cutoff = max(0, min(int(source_cutoff or 0), len(presented["detailed_lines"])))
        displayed = sum(index < cutoff for index in presented.get("_line_source_indices", []))
        return presented, displayed

    def focus_active_live_fight_window(self, event=None):
        """Focus the matching live broadcast instead of preparing it twice."""
        window = getattr(self, "_active_live_fight_window", None)
        if window is None:
            return False
        try:
            if not window.winfo_exists():
                raise tk.TclError
            expected = self.fight_night_event_key(event) if event is not None else None
            if expected is not None and expected != getattr(self, "_active_live_fight_event_key", None):
                return False
            window.deiconify()
            window.lift()
            window.focus_force()
            return True
        except tk.TclError:
            self._active_live_fight_window = None
            self._active_live_fight_event_key = None
            return False

    @staticmethod
    def fight_night_bout_complete(state, fight_logs, index=None):
        """Say whether a bout's complete commentary has been presented."""
        if not fight_logs:
            return True
        current = int(state.get("fight", -1))
        target = current if index is None else int(index)
        if target < 0 or target >= len(fight_logs):
            return False
        if target < current or bool(state.get("finished")):
            return True
        if target > current:
            return False
        return int(state.get("line", 0)) >= len(fight_logs[target].get("lines", []))

    @classmethod
    def fight_night_can_review(cls, state, fight_logs, index):
        """Keep future commentary locked while preserving every completed review."""
        if bool(state.get("finished")):
            return 0 <= int(index) < len(fight_logs)
        return cls.fight_night_bout_complete(state, fight_logs, index)

    def commit_live_fight_package(self, event, package, apply_results=True):
        """Attempt settlement without making a failed presentation look complete."""
        if not apply_results:
            return True, ""
        try:
            self.finish_event(event, package)
        except Exception as exc:
            return False, str(exc) or exc.__class__.__name__
        return True, ""

    def open_event_replay_window(self, title, package):
        return build_event_archive(self, title, package)

    @staticmethod
    def format_round_analysis(row, log=None):
        log = log or {}
        names = {"a": log.get("a", "Red corner"), "b": log.get("b", "Blue corner")}
        lines = [f"ROUND {row.get('round', '?')} ANALYSIS", "=" * 56]
        for key in ("a", "b"):
            corner = row.get("corners", {}).get(key, {})
            moves = sorted(corner.get("moves", {}).items(), key=lambda item: (-item[1], item[0]))[:5]
            defenses = sorted(corner.get("defenses", {}).items(), key=lambda item: (-item[1], item[0]))[:4]
            lines.extend([
                f"\n{names[key]}",
                f"Effectiveness: {corner.get('effective', 0)}/{corner.get('attempts', 0)}",
                "Top moves: " + (", ".join(f"{move.replace('_', ' ')} x{count}" for move, count in moves) or "none"),
                "Defenses: " + (", ".join(f"{move.replace('_', ' ')} x{count}" for move, count in defenses) or "none"),
                "Sequences: " + (", ".join(f"{item.get('source', '').replace('_', ' ')} -> {item.get('move', '').replace('_', ' ')} ({item.get('branch', 'primary')})" for item in corner.get("sequences", [])[:5]) or "none"),
                "Visible damage: " + (
                    ", ".join(
                        f"{item.get('label', item.get('damage_id', 'damage')).replace('_', ' ')} "
                        f"({item.get('channel', 'general')} {item.get('total', 0)})"
                        for item in corner.get("damage_events", [])
                    ) or "none"
                ),
            ])
        switches = row.get("stance_switches", [])
        changes = row.get("plan_changes", [])
        lines.append("\nStance changes: " + (", ".join(f"{names.get(item.get('corner'), item.get('corner'))} {item.get('from')} -> {item.get('to')}" for item in switches) or "none"))
        lines.append("Plan changes: " + (", ".join(f"{names.get(item.get('corner'), item.get('corner'))} -> {item.get('plan')} ({item.get('reason')})" for item in changes) or "none"))
        return "\n".join(lines)

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

    def live_fight_corner_outcome(self, log, side):
        """Return one corner's result without conflating duplicate display names."""
        draw, winner_name = self.live_fight_official_outcome(log)
        if draw:
            return "draw"
        winner_id = str(log.get("winner_id", "") or "")
        corner_id = str(log.get(f"{side}_id", "") or "")
        if winner_id and corner_id:
            return "win" if winner_id == corner_id else "loss"
        other_side = "b" if side == "a" else "a"
        corner_name = str(log.get(side, "") or "")
        other_name = str(log.get(other_side, "") or "")
        if winner_name and corner_name and corner_name != other_name:
            return "win" if corner_name == winner_name else "loss"
        return "unknown"

    def open_live_fight_window(self, event, package, apply_results=True, on_complete=None):
        # Preparation can pause at a title-miss decision before any fight is
        # simulated.  Keep the due card and its recorded weigh-in evidence
        # intact; opening the broadcast or applying results here would turn a
        # dismissed prompt into an accidental settlement.
        if isinstance(package, dict) and package.get("preparation_pending"):
            notice = getattr(self, "_results_status_notice", None)
            if callable(notice):
                notice(
                    str(package.get(
                        "pending_reason",
                        "Choose the pending title-miss action before opening the broadcast.",
                    )),
                    warning=True,
                )
            return package
        # Matchmaking displays the headline at the top of the bill, but a live
        # broadcast runs from the undercard upward. Copy the package so archived
        # records are not mutated merely by opening a replay.
        # Only one live broadcast may own the pre-simulated presentation at a
        # time. A replay or another event must not destroy an unresolved card.
        if self.focus_active_live_fight_window():
            return getattr(self, "_active_live_fight_window", None)
        package = dict(package)
        package["fight_logs"] = self.fight_night_log_order(package.get("fight_logs", []))
        window = self.create_managed_window()
        self._active_live_fight_window = window
        self._active_live_fight_event_key = self.fight_night_event_key(event)
        window.title(f"{'Live Fight' if apply_results else 'Event Replay'} - {event['name']}")
        self.root.update_idletasks()
        screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
        width = min(1360, max(640, screen_w - 60), screen_w)
        height = min(900, max(480, screen_h - 90), screen_h)
        x = max(0, min(screen_w - width, self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2))
        y = max(0, min(screen_h - height - 40, self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2))
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(min(820, width), min(540, height))
        window.configure(bg=self.colors["chrome"])
        canvas_hex = self.colors["cream"].lstrip("#")
        canvas_rgb = tuple(int(canvas_hex[index:index + 2], 16) for index in (0, 2, 4)) if len(canvas_hex) == 6 else (32, 32, 32)
        light_canvas = sum(canvas_rgb) > 430
        heading_color = "#6b4b00" if light_canvas else self.colors["gold"]
        round_color = "#005a78" if light_canvas else "#7dd3fc"
        result_color = "#8b1010" if light_canvas else "#ff8a8a"

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        title_label = ttk.Label(header, text=f"{'LIVE FIGHT' if apply_results else 'REPLAY'}: {event['name']}", style="ScreenTitle.TLabel")
        title_label.pack(side="left", padx=10, pady=5)
        event_progress_label = ttk.Label(header, text="Card ready", style="Panel.TLabel")
        event_progress_label.pack(side="right", padx=10, pady=5)
        event_progress = ttk.Progressbar(window, maximum=max(1, len(package.get("fight_logs", []))), value=0)
        event_progress.pack(fill="x", padx=8, pady=(4, 0))

        dashboard = build_fight_night_layout(self, window, width, height)
        controls_area = dashboard.controls_area
        controls = dashboard.controls
        controls2 = dashboard.controls2
        controls3 = dashboard.controls3
        reading_controls = dashboard.reading_controls
        audio_controls = dashboard.audio_controls
        left_name = dashboard.left_name
        left_ovr = dashboard.left_ovr
        left_portrait = dashboard.left_portrait
        left_title_status = dashboard.left_title_status
        left_condition = dashboard.left_condition
        left_gas = dashboard.left_gas
        right_name = dashboard.right_name
        right_ovr = dashboard.right_ovr
        right_portrait = dashboard.right_portrait
        right_title_status = dashboard.right_title_status
        right_condition = dashboard.right_condition
        right_gas = dashboard.right_gas
        label_chip = dashboard.label_chip
        phase_label = dashboard.phase_label
        clock_label = dashboard.clock_label
        vs_label = dashboard.vs_label
        score_label = dashboard.score_label
        fight_read_label = dashboard.fight_read_label
        round_read_label = dashboard.round_read_label
        intro_label = dashboard.intro_label
        bout_brief_label = dashboard.bout_brief_label
        current_moment_label = dashboard.current_moment_label
        momentum_canvas = dashboard.momentum_canvas
        momentum_text = dashboard.momentum_text
        live_stats = dashboard.live_stats
        result_ribbon = dashboard.result_ribbon
        result_winner_label = dashboard.result_winner_label
        result_detail_label = dashboard.result_detail_label
        text = dashboard.text
        text_scroll = dashboard.text_scroll
        fight_list = dashboard.fight_list
        configure_fight_timeline(text, self.colors)
        for index, fight_log in enumerate(package.get('fight_logs', []), 1):
            heading = fight_log.get('heading', fight_log.get('fight', f'Bout {index}'))
            fight_list.insert('end', f'{index}. PENDING — {heading}')

        selected_commentary_mode = str(self.rules.get("fight_commentary_mode", "Broadcast"))
        if selected_commentary_mode not in FIGHT_COMMENTARY_MODES:
            selected_commentary_mode = "Broadcast"
        state = {
            "fight": -1, "line": 0,
            "delay": max(300, min(3000, self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 1600)),
            "running": False, "finished": False, "after_id": None, "phase": "", "result_shown": False,
            "metrics_rows_remaining": 0, "scorecard_buffer": [], "holding_scorecards": False,
            "momentum": "", "close_armed": False, "walkout_played": False,
            "skip_armed": False, "commit_error": "",
            "auto": bool(self.rules.get("live_auto_play_card", False)),
            "commentary_mode": selected_commentary_mode,
            "rerendering": False,
        }
        window._fight_night_state = state
        raw_fight_logs = package.get("fight_logs", [{"heading": "Event Report", "lines": package["log"]}])
        fight_logs = self.fight_night_presentation_logs(
            raw_fight_logs, state["commentary_mode"],
        )
        commentary_mode_var = tk.StringVar(value=state["commentary_mode"])
        commentary_personality_var = tk.StringVar(
            value=f"Voice: {self.rules.get('fight_commentary_personality', 'Balanced')}"
        )
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
            left_marker = "  MOMENTUM" if state.get("momentum") == "a" else ""
            right_marker = "MOMENTUM  " if state.get("momentum") == "b" else ""
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
            a_row, b_row = values.get("a", {}), values.get("b", {})
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
                canvas.create_text(7, canvas_h // 2, text="RED" if canvas_w < 400 else a_name[:18], anchor="w", fill="#ffffff", font=("Tahoma", 8, "bold"))
            if b_name:
                canvas.create_text(canvas_w - 7, canvas_h // 2, text="BLUE" if canvas_w < 400 else b_name[:18], anchor="e", fill="#ffffff", font=("Tahoma", 8, "bold"))
            if total > 0:
                if canvas_w >= 400:
                    canvas.create_text(canvas_w // 2, canvas_h // 2, text=f"{round(lean_a * 100)}—{round((1 - lean_a) * 100)}", anchor="center", fill="#ffffff", font=("Consolas", 8, "bold"))
            if total <= 0:
                momentum_text.config(text="Momentum: even")
            elif lean_a >= 0.55:
                momentum_text.config(text=f"Momentum: {self.display_fighter_name_value(a_name)} leads {round(lean_a * 100)}–{round((1 - lean_a) * 100)}")
            elif lean_a <= 0.45:
                momentum_text.config(text=f"Momentum: {self.display_fighter_name_value(b_name)} leads {round((1 - lean_a) * 100)}–{round(lean_a * 100)}")
            else:
                momentum_text.config(text=f"Momentum: even {round(lean_a * 100)}–{round((1 - lean_a) * 100)}")

        momentum_canvas.bind("<Configure>", lambda _event: draw_momentum_bar())

        def refresh_live_stats(round_values=None):
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            names = (current_log.get("a", "Red corner"), current_log.get("b", "Blue corner"))
            gas = state.get("gas", (100, 100))
            values = round_values or state.get("round_values", {})
            for item in live_stats.get_children():
                live_stats.delete(item)
            for index, name in enumerate(names):
                side = "a" if index == 0 else "b"
                row = values.get(side, {})
                leads = state.get("momentum") == side
                marker = "EDGE" if leads else "-"
                live_stats.insert("", "end", tags=("edge",) if leads else (), values=(
                    name,
                    int(round(float(row.get("impact", 0) or 0))),
                    int(round(float(row.get("control", 0) or 0))),
                    int(round(float(row.get("danger", 0) or 0))),
                    int(gas[index]), marker,
                ))
            draw_momentum_bar()
            dashboard.update_round_read(values, names)

        def round_summary_presentation(value):
            """Update live telemetry without replacing the stored commentary.

            Exact judge cards stay sealed until the official result, but every
            stored round-summary line remains visible in the commentary stream.
            """
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            if not (a_name and b_name and " summary:" in value.lower() and "Metrics -" in value):
                return value
            pattern = (
                rf"^(Round\s+\d+)\s+summary:.*?Metrics\s+-\s+{re.escape(a_name)}:\s*impact\s+([\d.]+),\s*control\s+([\d.]+),\s*danger\s+([\d.]+);\s*"
                rf"{re.escape(b_name)}:\s*impact\s+([\d.]+),\s*control\s+([\d.]+),\s*danger\s+([\d.]+)\.\s*"
                rf"Gas:\s*{re.escape(a_name)}\s+([\d.]+),\s*{re.escape(b_name)}\s+([\d.]+)\.\s*Momentum:\s*(.+?)\.?$"
            )
            match = re.match(pattern, value, re.IGNORECASE)
            if not match:
                return value
            phase = match.group(1).title()
            numbers = [int(round(float(number))) for number in match.groups()[1:9]]
            a_impact, a_control, a_danger, b_impact, b_control, b_danger, gas_a, gas_b = numbers
            a_strength = a_impact + a_control + a_danger
            b_strength = b_impact + b_control + b_danger
            state["momentum"] = "a" if a_strength > b_strength else "b" if b_strength > a_strength else ""
            state["round_values"] = {
                "a": {"impact": a_impact, "control": a_control, "danger": a_danger},
                "b": {"impact": b_impact, "control": b_control, "danger": b_danger},
            }
            set_condition(gas_a, gas_b)
            refresh_live_stats(state["round_values"])
            score_label.config(text="Unofficial round telemetry updated  |  Official judges sealed")
            display_value = self.display_fighter_names_in_text(value, current_log)
            round_read_label.config(text=display_value + " Exact cards remain private.")
            current_moment_label.config(text=f"{phase} complete. Full summary remains in the action timeline.")
            return value

        def play_crowd(cue):
            profile = state.get("crowd_profile", {}) or {}
            return self.play_fight_night_sound(cue, profile.get("gain", 1.0))

        def append_line(value):
            value = str(value or "").strip("\n")
            if not value:
                return
            raw_value = value
            current_log = fight_logs[state["fight"]] if 0 <= state["fight"] < len(fight_logs) else {}
            value = round_summary_presentation(value)
            value = self.display_fighter_names_in_text(value, current_log)
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
            elif any(k in lowered for k in ("taps to", "has to tap", "gets the tap", "and it's all over", "unconscious", "stops the fight", "by ko", "by tko", "by submission", "technical fall", "secures the pin", "referee has seen enough", "stoppage comes")):
                tag = "finish"
            elif "referee" in lowered or "official" in lowered:
                tag = "referee"
            elif any(k in lowered for k in ("drops", "hits the mat", "stumbles badly", "knocked down", "wobbl", "buckl", "rocked", "hurt")):
                tag = "knockdown"
            elif any(term in lowered for term in (
                    "cut", "swelling", "bruising", "reddening", "welt", "visible limp",
                    "laboured breathing", "guarding the midsection", "shifts weight")):
                tag = "cut"
            elif value and set(value) <= {"-", "=", " "}:
                tag = "separator"
            # Keep the complete displayed source, using layout rather than more
            # punctuation or repeated banners to distinguish each exchange.
            # Keyword guesses still serve legacy audio cues, but do not paint
            # ordinary/negated mentions of "hurt" or "cut" as verified events.
            # Structural tags are authoritative. Event accents are derived again
            # from positive recorded wording so incidental/negated mentions do
            # not become visual evidence merely because legacy audio matched.
            visual_tag = tag if tag in {'heading', 'round', 'result', 'metrics', 'analysis', 'separator'} else None
            if " summary:" in lowered:
                visual_tag = 'analysis'
            insert_fight_timeline_line(text, value, tag=visual_tag)
            if clock_match:
                current_moment_label.config(text=clock_match.group(2))
                clock_label.config(text=clock_match.group(1).strip("[]"))
                if state.get("phase"):
                    phase_label.config(text=state["phase"])
            if follow_var.get():
                text.see("end")
            text.config(state="disabled")
            # Cues mirror clearly observable broadcast moments. They never
            # affect fight simulation or event timing, and can be disabled in
            # Game Settings.
            emit_audio = not state.get("rerendering", False)
            if emit_audio and is_phase_start:
                phase = str(phase_match.group(1)).upper()
                play_crowd(
                    "opening" if phase in ("ROUND 1", "PERIOD 1", "MATCH CLOCK") else "round_start"
                )
            elif emit_audio and tag == "finish":
                play_crowd("finish")
            elif emit_audio and tag == "knockdown":
                play_crowd("knockdown")
            elif emit_audio and tag == "round" and " summary:" in lowered:
                play_crowd("round_end")
            elif emit_audio and clock_match and any(phrase in lowered for phrase in (
                "deep submission", "submission threat", "choke threat", "armbar threat",
                "triangle threat", "locks the choke", "locks on", "nearly taps",
            )):
                play_crowd("submission")
            elif emit_audio and clock_match and any(phrase in lowered for phrase in (
                "stalls", "inactive", "inactivity", "stand-up", "restarts them at range",
                "little action", "crowd grows restless",
            )):
                play_crowd("inactivity")
            elif emit_audio and clock_match and any(word in lowered for word in ("lands", "connects", "drives", "slams", "elbow")):
                play_crowd("impact")
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
            a_name, b_name = current_log.get("a", ""), current_log.get("b", "")
            if a_name and b_name:
                condition_match = re.search(
                    rf"(?:Gas|Stamina):\s*{re.escape(a_name)}\s+([\d.]+),\s*{re.escape(b_name)}\s+([\d.]+)", raw_value, re.IGNORECASE,
                )
                if not condition_match and value.startswith(("Corner read:", "Mat-side read:")):
                    condition_match = re.search(
                        rf"{re.escape(a_name)}\s+stamina\s+([\d.]+).*?{re.escape(b_name)}\s+stamina\s+([\d.]+)", raw_value, re.IGNORECASE,
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
            play_crowd(self.fight_night_decision_reaction(buffered))
            for card_line in buffered[1:]:
                append_line(card_line)

        def present_fight_line(line):
            """Render one stored line while preserving result suspense."""
            stripped = str(line or "").strip()
            if stripped == "Official scorecards:":
                state["holding_scorecards"] = True
                state["scorecard_buffer"] = [stripped]
                play_crowd("decision_pending")
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
                return True
            cancel_timer()
            committed, commit_error = self.commit_live_fight_package(event, package, apply_results)
            if not committed:
                state["commit_error"] = commit_error
                state["running"] = False
                state["skip_armed"] = False
                phase_label.config(text="COMMIT FAILED")
                status_label.config(
                    text=f"Event settlement failed: {state['commit_error']}. The broadcast remains open; retry End Event after resolving the error.",
                    fg=result_color,
                )
                skip_event_button.config(text="Retry End Event")
                update_control_state()
                return False
            if apply_results:
                state["commit_error"] = ""
                append_line("\n[Event processed. Results have been applied to the world.]")
            else:
                append_line("\n[Simulation complete. No world results were applied.]")
            state["finished"] = True
            self.play_fight_night_sound("card_complete")
            event_progress["value"] = max(1, len(fight_logs))
            event_progress_label.config(text=f"Card complete - {len(fight_logs)} fights")
            phase_label.config(text="EVENT COMPLETE")
            profit = int(round(float(package.get("profit", 0) or 0)))
            excitement = int(round(float(package.get("average_excitement", 0) or 0)))
            current_moment_label.config(text=f"{event.get('name', 'Event')} complete  •  Profit ${profit:,}  •  Average excitement {excitement}")
            round_read_label.config(text="Results, bonuses, attendance, finances, and company effects are available in the end-of-event report.")
            update_control_state()
            if on_complete:
                on_complete()
            return True

        def mark_fight_done(index):
            log = fight_logs[index]
            result = log.get("result") or ("CANCELLED" if log.get("cancelled") else "")
            if result and fight_list.size() > index:
                result = self.display_fighter_names_in_text(result, log)
                fight_list.delete(index)
                fight_list.insert(index, f"{index + 1}. DONE - {result}")
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
            return self.fight_night_bout_complete(state, fight_logs)

        def update_event_button_label():
            try:
                skip_event_button.config(text=("End Event" if all_presented_fights_complete() else "Skip Event") if apply_results else "Close Replay")
            except (NameError, tk.TclError):
                pass

        def update_control_state():
            """Keep destructive/advancing actions aligned with presentation state."""
            try:
                current_complete = state["fight"] < 0 or self.fight_night_bout_complete(state, fight_logs)
                active_incomplete = 0 <= state["fight"] < len(fight_logs) and not current_complete and not state["finished"]
                can_advance = (current_complete and not state["finished"]) if apply_results else state["fight"] + 1 < len(fight_logs)
                next_fight_button.config(state="normal" if can_advance else "disabled")
                play_button.config(state="normal" if (state["fight"] < 0 or active_incomplete) and not state["finished"] else "disabled")
                pause_button.config(state="normal" if active_incomplete else "disabled")
                quick_navigation = (state["fight"] < 0 or active_incomplete) and not state["finished"]
                next_round_button.config(state="normal" if quick_navigation else "disabled")
                skip_fight_button.config(state="normal" if quick_navigation else "disabled")
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
            width, height = int(canvas.cget("width")), int(canvas.cget("height"))
            render_portrait(canvas, fighter, size=min(width, height), ratings_visible=True)

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
            story_copy = self.fight_story_summary(a, b, log) if hasattr(self, "fight_story_summary") else ""
            story_copy = f" Why this fight matters: {story_copy}" if story_copy else ""
            local_copy = str((state.get("crowd_profile", {}) or {}).get("summary", "") or "")
            local_copy = f" {local_copy}" if local_copy else ""
            return (f"{stakes}: {a.style} from {a.camp or 'independent camp'} meets {b.style} from {b.camp or 'independent camp'}. "
                    f"Recent form {self.fighter_display_name(a)}: {form_text(a)} | {self.fighter_display_name(b)}: {form_text(b)}. Odds {self.matchup_odds(a, b)}.{rivalry_copy}{story_copy}{local_copy}")

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
            return self.display_fighter_names_in_text(lead + (" This is the final fight of the broadcast." if not remaining else f" {remaining} bout{'s' if remaining != 1 else ''} remain on the card."), log)

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
                return f"OVERALL  {value}" if value else ""

            label_chip.config(text=log.get("label", ""))
            a_name, b_name = log.get("a", ""), log.get("b", "")
            if a_name and b_name:
                a = self.result_fighter(a_name, log.get("a_id", ""), log.get("sport", ""), log.get("weight", ""))
                b = self.result_fighter(b_name, log.get("b_id", ""), log.get("sport", ""), log.get("weight", ""))
                left_name.config(text=f"{self.fighter_display_name(a) if a else self.display_fighter_name_value(a_name)}\n{log.get('a_record', '')}")
                left_ovr.config(text=rating_text(log.get("a_rating", {})))
                vs_label.config(text="VS")
                right_name.config(text=f"{self.fighter_display_name(b) if b else self.display_fighter_name_value(b_name)}\n{log.get('b_record', '')}")
                right_ovr.config(text=rating_text(log.get("b_rating", {})))
                left_title_status.config(text=log.get("a_title_status", ""))
                right_title_status.config(text=log.get("b_title_status", ""))
            else:
                left_name.config(text=log.get("heading", ""))
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
                if a:
                    draw_intro_portrait(left_portrait, a, "red")
                if b:
                    draw_intro_portrait(right_portrait, b, "blue")
                set_condition(log.get("a_start_gas", 100), log.get("b_start_gas", 100))
                refresh_live_stats()
                current_moment_label.config(text=pre_fight_copy(log))
                bout_brief_label.config(text=pre_fight_copy(log))
                round_read_label.config(text="Walkouts complete. Tale of the tape, camp form, odds, and stakes are live; official scoring stays sealed until the result.")
                fight_read_label.config(text=f"{log.get('weight', '')} | {log.get('label', 'Bout')} | Condition, momentum, threat, and control update between rounds.")
                intro_label.config(text=f"{log.get('weight', '').upper()} | {log.get('label', 'BOUT')}\n{log.get('a_record', '')}  vs  {log.get('b_record', '')}")
            else:
                set_condition(100, 100)
                refresh_live_stats()
                fight_read_label.config(text="")
                intro_label.config(text="EVENT PRESENTATION")

        def start_next_fight(replay_index=None):
            if replay_index is not None and (apply_results or not 0 <= replay_index < len(fight_logs)):
                return
            if state["finished"] and replay_index is None:
                return
            if apply_results and 0 <= state["fight"] < len(fight_logs) and not self.fight_night_bout_complete(state, fight_logs):
                status_label.config(text="Finish or skip the active bout before starting the next fight.", fg=result_color)
                update_control_state()
                return
            cancel_timer()
            state["running"] = False
            if 0 <= state["fight"] < len(fight_logs):
                if self.fight_night_bout_complete(state, fight_logs):
                    mark_fight_done(state["fight"])
                elif not apply_results:
                    previous = state["fight"]
                    fight_list.delete(previous)
                    fight_list.insert(previous, f"{previous + 1}. {fight_logs[previous].get('heading', 'Bout')}")
            target = state["fight"] + 1 if replay_index is None else replay_index
            if target >= len(fight_logs):
                finish_live_event()
                return
            state["fight"] = target
            state["finished"] = False
            state["line"] = 0
            state["phase"] = ""
            state["result_shown"] = False
            state["close_armed"] = False
            state["walkout_played"] = False
            state["skip_armed"] = False
            state["metrics_rows_remaining"] = 0
            pause_button.config(text="Pause")
            close_button.config(text="Close")
            fight_list.selection_clear(0, "end")
            if fight_list.size():
                fight_list.delete(state["fight"])
                fight_list.insert(state["fight"], f"{state['fight'] + 1}. {'LIVE' if apply_results else 'REPLAY'} - {fight_logs[state['fight']].get('heading', 'Bout')[:31]}")
                fight_list.selection_set(state["fight"])
                fight_list.see(state["fight"])
            log = fight_logs[state["fight"]]
            personality = str(
                log.get("commentary_personality")
                or self.rules.get("fight_commentary_personality", "Balanced")
            )
            if personality not in FIGHT_COMMENTARY_PERSONALITIES:
                personality = "Balanced"
            commentary_personality_var.set(f"Voice: {personality}")
            a_fighter = self.result_fighter(log.get("a", ""), log.get("a_id", ""), log.get("sport", ""), log.get("weight", ""))
            b_fighter = self.result_fighter(log.get("b", ""), log.get("b_id", ""), log.get("sport", ""), log.get("weight", ""))
            state["crowd_profile"] = self.fight_night_local_crowd_profile(
                (a_fighter, b_fighter), package.get("region", ""), package.get("city", "")
            )
            # One neutral arena bed persists across the whole card. Fighter-
            # specific hometown gain remains on reactions and walkouts so a
            # preliminary bout cannot set the ambience level for the main event.
            self.start_fight_night_audio_session()
            if state.get("auto"):
                state["walkout_played"] = True
                play_crowd("walkout")
            heading = log.get("heading", log.get("fight", "Bout"))
            title_label.config(text=f"{'FIGHT NIGHT' if apply_results else 'REPLAY'}: {event['name']}")
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
            update_event_button_label()
            update_control_state()

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
            winner_id = str(log.get("winner_id", "") or "")
            winner_fighter = self.result_fighter(winner_name, winner_id, log.get("sport", ""), log.get("weight", "")) if winner_name or winner_id else None
            display_result = self.display_fighter_names_in_text(result or "Official result", log)
            display_winner = self.fighter_display_name(winner_fighter) if winner_fighter else winner_name
            a_outcome = self.live_fight_corner_outcome(log, "a")
            b_outcome = self.live_fight_corner_outcome(log, "b")
            scorecards = log.get("scorecards", "") or "No scorecards required"
            excitement = int(round(float(log.get("excitement", 0) or 0)))
            # Per-fight scores spread far wider than card averages (roughly
            # 11-84), so this reads the individual-bout range, not the event one.
            contender = "Bonus contender" if excitement >= 58 else "Solid performance" if excitement >= 44 else "Low bonus contention"
            result_winner_label.config(text="OFFICIAL DRAW" if draw else f"WINNER: {display_winner}" if winner_name else "OFFICIAL RESULT")
            result_detail_label.config(text=(f"{display_result}  |  Time: {finish_time}\n"
                f"Records: {self.fighter_display_name(self.result_fighter(log.get('a', ''), log.get('a_id', ''), log.get('sport', ''), log.get('weight', ''))) if self.result_fighter(log.get('a', ''), log.get('a_id', ''), log.get('sport', ''), log.get('weight', '')) else log.get('a', 'Red')} {a_record} -> {next_record(a_record, a_outcome)}   |   "
                f"{self.fighter_display_name(self.result_fighter(log.get('b', ''), log.get('b_id', ''), log.get('sport', ''), log.get('weight', ''))) if self.result_fighter(log.get('b', ''), log.get('b_id', ''), log.get('sport', ''), log.get('weight', '')) else log.get('b', 'Blue')} {b_record} -> {next_record(b_record, b_outcome)}\n"
                f"{scorecards}  |  {contender} (excitement {excitement})\n"
                "Medical clearance, morale, popularity, and any suspension are applied after the card and explained in End of Event."))
            result_ribbon.pack(fill="x", padx=6, pady=(4, 5), before=intro_label)
            if not state.get("rerendering"):
                dashboard.sidebar.select(dashboard.brief_page)
            status_label.config(text="Bout complete. Review the official result, scorecards, and metrics, then start the next fight.", fg=self.colors["muted"])
            append_line("\n[Fight complete. Press Start Next Fight.]")
            if state["fight"] + 1 < len(fight_logs):
                next_log = fight_logs[state["fight"] + 1]
                append_line(f"Broadcast desk: next up, {next_log.get('heading', 'the next bout')}. The card moves on after the official result.")
            update_event_button_label()
            update_control_state()

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
            if not state.get("walkout_played"):
                state["walkout_played"] = True
                play_crowd("walkout")
            state["running"] = True
            state["close_armed"] = False
            state["skip_armed"] = False
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
            state["skip_armed"] = False
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
            if not fight_logs:
                return
            if state["fight"] < 0:
                start_next_fight()
            if not apply_results:
                target = state["fight"] + 1
                if target < len(fight_logs):
                    watch_replay_bout(target)
                else:
                    close_window()
                return
            was_running = bool(state["running"])
            state["running"] = False
            state["skip_armed"] = False
            cancel_timer()
            lines = fight_logs[state["fight"]]["lines"]
            # Skipping changes the presentation frontier only. Official results
            # and full commentary already exist in the prepared package.
            state["line"] = len(lines)
            state["metrics_rows_remaining"] = 0
            state["scorecard_buffer"] = []
            state["holding_scorecards"] = False
            show_result_if_needed()
            show_fight_complete_status()
            if state["fight"] + 1 < len(fight_logs):
                start_next_fight()
                if was_running or state.get("auto"):
                    start()
            elif state.get("auto"):
                finish_live_event()

        def skip_to_end():
            if not apply_results:
                close_window()
                return
            if state["finished"]:
                return
            state["running"] = False
            cancel_timer()
            if not all_presented_fights_complete() and not state.get("skip_armed"):
                state["skip_armed"] = True
                skip_event_button.config(text="Confirm Skip Event")
                status_label.config(text="Skipping ends the live presentation and applies the complete event. Press Confirm Skip Event to continue.", fg=result_color)
                return
            for index in range(fight_list.size()):
                mark_fight_done(index)
            finish_live_event()

        def clear_active_live_window(_event=None):
            if getattr(self, "_active_live_fight_window", None) is window:
                self.stop_fight_night_audio_session()
                self._active_live_fight_window = None
                self._active_live_fight_event_key = None

        def close_window():
            cancel_timer()
            if not apply_results:
                state["running"] = False
                state["finished"] = True
                clear_active_live_window()
                window.destroy()
                return
            if not state["finished"]:
                if not state.get("close_armed"):
                    state["running"] = False
                    state["close_armed"] = True
                    pause_button.config(text="Resume")
                    close_button.config(text="Confirm Close")
                    action = "apply the completed event package" if apply_results else "discard this presentation"
                    status_label.config(text=f"Fight Night is still in progress. Press Confirm Close to {action}, or Resume to continue.", fg=result_color)
                    return
                if not finish_live_event():
                    return
            clear_active_live_window()
            window.destroy()

        def review_selected_bout(_event=None):
            selected = fight_list.curselection()
            if not selected:
                status_label.config(text="Select a completed bout on the left to review its commentary.", fg=heading_color)
                return
            index = selected[0]
            if apply_results and not self.fight_night_can_review(state, fight_logs, index):
                status_label.config(text="That bout has not finished. Future commentary remains locked.", fg=result_color)
                return
            log = fight_logs[index]
            review = self.create_managed_window(parent=window)
            left_copy = self.display_fighter_name_value(log.get("a", "Red corner"))
            right_copy = self.display_fighter_name_value(log.get("b", "Blue corner"))
            review.title(f"Fight Review - {left_copy} vs {right_copy}")
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
            left_role = log.get("a_title_status", "")
            right_role = log.get("b_title_status", "")
            tk.Label(matchup, text=f"{left_copy}\n{left_role}", bg=self.colors["panel_dark"], fg=self.colors["gold"] if left_role else self.colors["text"], font=("Tahoma", 11, "bold"), justify="right").pack(side="left", fill="x", expand=True, padx=12, pady=9)
            tk.Label(matchup, text="VS", bg=self.colors["panel_dark"], fg=self.colors["red"], font=("Tahoma", 10, "bold")).pack(side="left", padx=10)
            tk.Label(matchup, text=f"{right_copy}\n{right_role}", bg=self.colors["panel_dark"], fg=self.colors["gold"] if right_role else self.colors["text"], font=("Tahoma", 11, "bold"), justify="left").pack(side="left", fill="x", expand=True, padx=12, pady=9)
            review_body = ttk.Frame(review, style="Chrome.TFrame")
            review_body.pack(fill="both", expand=True, padx=8)
            review_text = tk.Text(review_body, wrap="word", bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], font=("Tahoma", 11), padx=14, pady=12, spacing3=3)
            configure_fight_timeline(review_text, self.colors)
            review_scroll = ttk.Scrollbar(review_body, orient="vertical", command=review_text.yview)
            review_text.configure(yscrollcommand=review_scroll.set)
            review_scroll.pack(side="right", fill="y")
            review_text.pack(side="left", fill="both", expand=True)
            review_lines = self.fight_night_commentary_lines(
                log.get("detailed_lines", log.get("lines", [])), commentary_mode_var.get(),
            )
            for line in review_lines:
                insert_fight_timeline_line(review_text, self.display_fighter_names_in_text(str(line), log))
            review_text.config(state="disabled")
            review_actions = ttk.Frame(review, style="Chrome.TFrame")
            review_actions.pack(fill="x", padx=8, pady=8)
            ttk.Label(
                review_actions,
                text=f"{commentary_mode_var.get()} commentary and official scorecards from this completed bout",
                style="Panel.TLabel",
            ).pack(side="left", padx=4)
            ttk.Button(review_actions, text="Close Review", style="Accent.TButton", command=review.destroy).pack(side="right", padx=4)

        def switch_commentary_mode(_event=None):
            """Rebuild the visible bout at the same sealed playback frontier."""
            nonlocal fight_logs
            requested = str(commentary_mode_var.get() or "Broadcast")
            if requested not in FIGHT_COMMENTARY_MODES:
                requested = "Broadcast"
                commentary_mode_var.set(requested)
            if requested == state.get("commentary_mode"):
                return

            was_running = bool(state.get("running"))
            cancel_timer()
            state["running"] = False
            self.rules["fight_commentary_mode"] = requested
            state["commentary_mode"] = requested
            if state["fight"] < 0:
                fight_logs = self.fight_night_presentation_logs(raw_fight_logs, requested)
                status_label.config(text=f"{requested} commentary selected for the next bout.", fg=self.colors["muted"])
                return

            index = state["fight"]
            source_cutoff = self.fight_night_source_cutoff(fight_logs[index], state["line"])
            refreshed_logs = self.fight_night_presentation_logs(raw_fight_logs, requested)
            refreshed_log, displayed_count = self.fight_night_presentation_progress(
                raw_fight_logs[index], requested, source_cutoff,
            )
            refreshed_logs[index] = refreshed_log
            fight_logs = refreshed_logs
            state["line"] = displayed_count
            state["phase"] = ""
            state["result_shown"] = False
            state["metrics_rows_remaining"] = 0
            state["scorecard_buffer"] = []
            state["holding_scorecards"] = False

            log = fight_logs[index]
            heading = log.get("heading", log.get("fight", "Bout"))
            state["rerendering"] = True
            try:
                if not state.get("finished"):
                    update_scoreboard(log)
                text.config(state="normal")
                text.delete("1.0", "end")
                text.config(state="disabled")
                append_line(heading)
                append_line("-" * 72)
                append_line(broadcast_rundown(index, log))
                first_line = 1 if log.get("lines") and str(log["lines"][0]).strip() == str(heading).strip() else 0
                for line in log.get("lines", [])[first_line:displayed_count]:
                    present_fight_line(line)
            finally:
                state["rerendering"] = False

            complete = state["line"] >= len(log.get("lines", []))
            if complete and state.get("finished"):
                phase_label.config(text="EVENT COMPLETE")
                profit = int(round(float(package.get("profit", 0) or 0)))
                excitement = int(round(float(package.get("average_excitement", 0) or 0)))
                current_moment_label.config(
                    text=f"{event.get('name', 'Event')} complete  •  Profit ${profit:,}  •  Average excitement {excitement}"
                )
                round_read_label.config(text="Results, bonuses, attendance, finances, and company effects are available in the end-of-event report.")
                status_label.config(text=f"Event complete — {requested} commentary view", fg=self.colors["muted"])
            elif complete:
                show_result_if_needed()
                show_fight_complete_status()
            elif was_running and not state.get("finished"):
                state["running"] = True
                status_label.config(text=f"Live playback running — {requested} commentary", fg=self.colors["muted"])
                schedule_next()
            else:
                status_label.config(text=f"{requested} commentary applied at the current fight position.", fg=self.colors["muted"])
            update_control_state()

        def watch_replay_bout(index):
            if apply_results or not 0 <= index < len(fight_logs):
                return
            start_next_fight(replay_index=index)
            start()

        def watch_selected_bout(_event=None):
            selected = fight_list.curselection()
            if selected:
                watch_replay_bout(selected[0])
            else:
                status_label.config(text="Select any archived bout on the left to play it immediately.", fg=heading_color)
            return "break"

        def watch_main_event():
            if not fight_logs:
                return
            index = next((index for index, log in enumerate(fight_logs)
                          if "MAIN" in str(log.get("label", "")).upper()
                          and "CO" not in str(log.get("label", "")).upper()), len(fight_logs) - 1)
            watch_replay_bout(index)

        def next_fight():
            if apply_results:
                start_next_fight()
            else:
                watch_replay_bout(state["fight"] + 1)

        next_fight_button = ttk.Button(controls, text="Start Next Fight" if apply_results else "Next Fight", style="Accent.TButton", command=next_fight)
        next_fight_button.pack(side="left", padx=4)
        play_button = ttk.Button(controls, text="Play Fight", command=start)
        play_button.pack(side="left", padx=4)
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
        next_round_button = ttk.Button(controls, text="Next Round", command=next_round)
        next_round_button.pack(side="left", padx=4)
        skip_fight_button = ttk.Button(controls, text="Skip Fight", command=skip_current_fight)
        skip_fight_button.pack(side="left", padx=4)
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
            configure_fight_timeline(text, self.colors, size)

        ttk.Button(reading_controls, text="Text -", command=lambda: change_font(-1)).pack(side="left", padx=(12, 2))
        ttk.Button(reading_controls, text="Text +", command=lambda: change_font(1)).pack(side="left", padx=2)
        def toggle_follow():
            self.rules["live_follow_commentary"] = bool(follow_var.get())
            if follow_var.get():
                text.see("end")

        ttk.Checkbutton(reading_controls, text="Follow live", variable=follow_var, command=toggle_follow).pack(side="left", padx=8)
        ttk.Label(reading_controls, text="Commentary", style="Panel.TLabel").pack(side="left", padx=(8, 3))
        commentary_mode_box = ttk.Combobox(
            reading_controls, state="readonly", values=FIGHT_COMMENTARY_MODES,
            textvariable=commentary_mode_var, width=10,
        )
        commentary_mode_box.pack(side="left", padx=(0, 8))
        commentary_mode_box.bind("<<ComboboxSelected>>", switch_commentary_mode)
        ttk.Label(
            reading_controls, textvariable=commentary_personality_var,
            style="Panel.TLabel", anchor="e",
        ).pack(side="right", padx=(8, 4))

        skip_event_button = ttk.Button(controls3, text="Skip Event", command=skip_to_end)
        skip_event_button.pack(side="left", padx=4)
        update_event_button_label()
        ttk.Button(controls3, text="Review Selected Bout", command=review_selected_bout).pack(side="left", padx=4)
        if apply_results:
            fight_list.bind("<Double-1>", review_selected_bout)
        else:
            replay_controls = ttk.Frame(audio_controls.master, style="Panel.TFrame")
            replay_controls.pack(fill="x", before=audio_controls, pady=(2, 4))
            ttk.Button(replay_controls, text="Watch Selected", style="Accent.TButton", command=watch_selected_bout).pack(side="left", padx=4)
            ttk.Button(replay_controls, text="Main Event", command=watch_main_event).pack(side="left", padx=4)
            ttk.Label(replay_controls, text="Double-click any bout to replay it. No results are reapplied.", style="Chrome.TLabel").pack(side="left", padx=10)
            fight_list.bind("<Double-1>", watch_selected_bout)
            fight_list.bind("<Return>", watch_selected_bout)
        if package.get("tournament_brackets"):
            ttk.Button(controls3, text="View Bracket", command=lambda: self.open_event_tournament_bracket(package, window)).pack(side="left", padx=4)
        self.ensure_audio_defaults()
        live_audio_volume_var = tk.DoubleVar(value=self.fight_night_audio_volume())
        live_audio_volume_label = tk.StringVar(value=f"{self.fight_night_audio_volume()}%")

        def apply_live_audio_volume(value=None):
            volume = self.set_fight_night_audio_volume(
                live_audio_volume_var.get() if value is None else value
            )
            live_audio_volume_label.set(f"{volume}%")

        ttk.Label(audio_controls, text="Audio", style="Panel.TLabel").pack(side="left", padx=(12, 3))
        ttk.Scale(
            audio_controls, from_=0, to=100, variable=live_audio_volume_var,
            orient="horizontal", length=120, command=apply_live_audio_volume,
        ).pack(side="left", padx=2)
        ttk.Label(
            audio_controls, textvariable=live_audio_volume_label,
            style="Panel.TLabel", width=4, anchor="e",
        ).pack(side="left", padx=(2, 4))
        status_label = tk.Label(controls_area, text="Ready", bg=self.colors["chrome"], fg=self.colors["muted"], font=("Tahoma", 9), anchor="w", justify="left", wraplength=width-40)
        status_label.pack(fill="x", padx=6, pady=(3, 0))
        status_label.bind('<Configure>', lambda event: status_label.configure(wraplength=max(100, event.width-12)))
        close_button = ttk.Button(controls3, text="Close", style="Accent.TButton", command=close_window)
        close_button.pack(side="right", padx=4)
        window.protocol("WM_DELETE_WINDOW", close_window)
        window.bind("<Destroy>", lambda event: clear_active_live_window(event) if event.widget is window else None, add="+")

        def keyboard_action(action):
            focused = window.focus_get()
            if focused is not None and focused.winfo_class() in {"Entry", "TEntry", "Spinbox", "TSpinbox", "Text"}:
                return
            action()
            return "break"

        window.bind("<space>", lambda _event: keyboard_action(pause_resume if state["running"] else start))
        window.bind("<Return>", lambda _event: keyboard_action(start))
        window.bind("<Control-n>", lambda _event: keyboard_action(next_fight))
        window.bind("<Control-r>", lambda _event: keyboard_action(next_round))
        window.bind("<Control-f>", lambda _event: keyboard_action(skip_current_fight))
        window.bind("<Escape>", lambda _event: keyboard_action(close_window))
        for profile_label, side in ((left_name, "a"), (right_name, "b")):
            profile_label.configure(takefocus=True)
            profile_label.bind("<Return>", lambda _event, selected_side=side: open_header_profile(selected_side))
            profile_label.bind("<space>", lambda _event, selected_side=side: open_header_profile(selected_side))
        def resize_fight_dashboard(event):
            if event.widget is not window:
                return
            compact = event.height < 700
            portrait_size = 104 if compact else 136
            for inner in dashboard.corner_inners:
                inner.pack_configure(pady=4 if compact else 8)
            for portrait, side in ((left_portrait, 'a'), (right_portrait, 'b')):
                if int(portrait.cget('width')) != portrait_size:
                    portrait.configure(width=portrait_size, height=portrait_size)
                    if 0 <= state['fight'] < len(fight_logs):
                        log = fight_logs[state['fight']]
                        fighter = self.result_fighter(log.get(side, ''), log.get(f'{side}_id', ''), log.get('sport', ''), log.get('weight', ''))
                        if fighter:
                            draw_intro_portrait(portrait, fighter, side)
        window.bind('<Configure>', resize_fight_dashboard, add='+')
        update_control_state()
        next_fight_button.focus_set()
        if state["auto"]:
            window.after_idle(start)
        return window

    def sign_fighter(self):
        selected = self.market_tree.selection()
        if not selected:
            return
        fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
        if fighter not in self.free_agents:
            self.refresh_market()
            return
        if int(getattr(fighter, "purse", 0) or 0) < 0:
            if hasattr(self, "_market_status_notice"):
                self._market_status_notice("This fighter has an invalid negative purse. Repair the fighter record before signing.", warning=True)
            else:
                messagebox.showwarning("Invalid contract", "This fighter has an invalid negative purse. Repair the fighter record before signing.")
            return
        signing_bonus = fighter.purse * 2
        if self.cash < signing_bonus:
            if hasattr(self, "_market_status_notice"):
                self._market_status_notice(f"Signing {self.fighter_display_name(fighter)} requires a ${signing_bonus:,} bonus.", warning=True)
            else:
                messagebox.showwarning("Not enough cash", f"Signing {self.fighter_display_name(fighter)} requires a ${signing_bonus:,} bonus.")
            return
        # Append the incoming company fact before moving the fighter out of
        # the free-agent collection.  The post-move narrative hook below is
        # deliberately membership-free so retries cannot create a second row.
        membership_recorded = False
        membership = getattr(self, "record_membership_event", None)
        if callable(membership):
            membership(
                fighter, "join", company_name=self.player_company_name,
                reason="Free-agent market signing",
                source_transaction=f"market-signing:{getattr(fighter, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
            )
            membership_recorded = True
        self.cash -= signing_bonus
        self.record_finance_transaction(f"Signing bonus: {self.fighter_display_name(fighter)}", costs=signing_bonus)
        self.free_agents.remove(fighter)
        self.clear_ai_contract_offer(fighter)
        # AI roster caps prevent market hoarding; player-controlled promotions
        # are deliberately uncapped, including after a company takeover.
        fighter.contract_months = random.randint(10, 24)
        fighter.morale = min(100, fighter.morale + 8)
        self.roster.append(fighter)
        # Record the roster boundary alongside the contract mutation so a
        # market signing appears in the same ID-linked membership timeline as
        # negotiated and AI signings.
        if hasattr(self, "record_contract_signing"):
            self.record_contract_signing(
                fighter, self.player_company_name,
                source="Free-agent market signing",
                record_membership=not membership_recorded,
            )
        elif not membership_recorded:
            membership = getattr(self, "record_membership_event", None)
            if callable(membership):
                membership(
                    fighter, "join", company_name=self.player_company_name,
                    reason="Free-agent market signing",
                    source_transaction=f"market-signing:{getattr(fighter, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                )
        self.event_log.append(f"Signed {self.fighter_display_name(fighter)} to a {fighter.contract_months}-month ${fighter.purse:,}/fight contract.")
        self.news.insert(0, f"{self.player_company_name} signed {self.fighter_display_name(fighter)}, a {fighter.style_label} {fighter.weight} with {fighter.trait.lower()} reputation.")
        if hasattr(self, "_market_status_notice"):
            self._market_status_notice(f"SIGNED: {self.fighter_display_name(fighter)} joined the roster on a {fighter.contract_months}-month contract.")
        self.refresh_all()
        self.write_log()

    # Signed adjustment motivation makes to a comeback asking price, as agreed
    # anchor points. Positive is a discount, negative a surcharge, neutral at
    # 65. Interpolated linearly between anchors, so the curve stays gentle
    # through the reluctant range and steepens once a fighter genuinely wants
    # back in.
    COMEBACK_MOTIVATION_CURVE = (
        (0, -0.06), (30, -0.04), (50, -0.02), (65, 0.0), (75, 0.045), (85, 0.075), (100, 0.12),
    )

    def comeback_motivation_discount(self, fighter):
        """Fraction motivation adds to or takes off a comeback asking price.

        A fighter who badly wants to compete again gives up to 12% back; one
        who has to be talked into it charges up to 6% more for the
        inconvenience. Deliberately small both ways: a comeback should stay a
        real financial commitment rather than becoming a bargain or a wall.
        """
        motivation = max(0, min(100, int(getattr(fighter, "motivation", 65) or 0)))
        curve = self.COMEBACK_MOTIVATION_CURVE
        for (low, low_value), (high, high_value) in zip(curve, curve[1:]):
            if motivation <= high:
                span = high - low
                weight = (motivation - low) / span if span else 0.0
                return round(low_value + (high_value - low_value) * weight, 4)
        return round(curve[-1][1], 4)

    def contract_negotiation_target_is_current(self, fighter, existing=False, comeback=False, source_promotion=None, transfer_deal=None):
        """Revalidate a potentially stale Profile action before any contract mutation."""
        if getattr(self, "spectator_mode", False):
            return False, "Contracts cannot be negotiated in Spectator Mode."
        if existing:
            return (True, "") if self.player_owns_fighter(fighter) else (False, "That fighter is no longer on your roster.")
        if comeback:
            available = getattr(fighter, "retired", False) and fighter in getattr(self, "retired_fighters", [])
            if not available:
                return False, "That fighter is no longer available for a comeback deal."
            active_coaching = getattr(self, "academy_coach_link_for_fighter", lambda _fighter: None)(fighter)
            if active_coaching:
                return False, (
                    f"{getattr(fighter, 'name', 'This fighter')} is actively supervising an Academy development block "
                    f"as {active_coaching.get('coach_name', 'an Academy Coach')}. End that coaching assignment "
                    "from the Academy page before starting a comeback negotiation."
                )
            return True, ""
        if source_promotion is not None:
            available = fighter in getattr(source_promotion, "roster", [])
            return (True, "") if available else (False, f"That fighter has already left {source_promotion.name}.")
        if transfer_deal is not None:
            owner = self.promotion_owning_fighter(fighter) if hasattr(self, "promotion_owning_fighter") else None
            expected_owner = transfer_deal.get("source") if isinstance(transfer_deal, dict) else None
            return (True, "") if owner is expected_owner and owner is not None else (False, "That fighter is no longer owned by the promotion in this transfer.")
        available = (
            fighter in getattr(self, "free_agents", [])
            and not self.player_owns_fighter(fighter)
            and self.promotion_owning_fighter(fighter) is None
        )
        return (True, "") if available else (False, "That fighter is no longer a free agent.")

    def open_contract_negotiation(self, fighter, existing=False, comeback=False, farewell=False, source_promotion=None, transfer_deal=None):
        # A farewell deal is a comeback that resolves in a single retirement bout
        # rather than a multi-fight commitment.
        if farewell:
            comeback = True
        proposal_id = str((transfer_deal or {}).get("proposal_id", "") or "")

        def proposal_update(status, *, outcome="", error="", terms=None):
            if proposal_id and callable(getattr(self, "update_company_proposal", None)):
                self.update_company_proposal(proposal_id, status, outcome=outcome, error=error, terms=terms)

        available, unavailable_reason = self.contract_negotiation_target_is_current(
            fighter, existing, comeback, source_promotion, transfer_deal,
        )
        if not available:
            proposal_update("needs_review", outcome="Fighter contract talks could not start.", error=unavailable_reason)
            if hasattr(self, "_market_status_notice"):
                self._market_status_notice(unavailable_reason, warning=True)
            else:
                messagebox.showinfo("Contract unavailable", unavailable_reason)
            return None
        prior_comeback_guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        prior_comeback_completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
        report = self.scouting_report_for(fighter)
        ratings_known = existing or not self.rules.get("scouting_mode", False) or self.scouting_report_is_current_full(report)
        window = self.create_managed_window()
        window.title(f"Negotiate - {self.fighter_display_name(fighter)}")
        window.geometry("660x600")
        window.minsize(600, 560)
        window.configure(bg=self.colors["chrome"])
        active_offer_company = getattr(fighter, "ai_offer_company", "") if not existing and not comeback else ""
        active_offer_purse = getattr(fighter, "ai_offer_purse", 0) if active_offer_company else 0
        rival = self.contract_rival_candidate(active_offer_company)
        if active_offer_company and rival is None:
            active_offer_purse = 0
        rival_name = getattr(rival, "name", active_offer_company or "No rival promotion")
        leverage = 1 + fighter.popularity / 140 + (0.35 if fighter.champion else 0) + max(0, fighter.momentum) * 0.05
        comeback_motivation_discount = 0.0
        if comeback:
            leverage += 0.28
            # A retired fighter who genuinely wants back in will shave their
            # asking price. Small enough that a comeback stays expensive,
            # visible enough that motivation is worth checking before talks.
            comeback_motivation_discount = self.comeback_motivation_discount(fighter)
        loyalty = 0.82 if existing else 1.0
        ask = max(4000, round(fighter.purse * leverage * loyalty * (1 - comeback_motivation_discount)),
                  round(active_offer_purse * 1.05) if active_offer_purse else 0)
        purse_var = tk.IntVar(value=ask)
        term_var = tk.IntVar(value=max(8, min(30, fighter.contract_months if existing else 12)))
        fights_var = tk.IntVar(value=5 if (existing or comeback) else 3)
        signing_var = tk.IntVar(value=max(0, round(ask * (0.75 if comeback else 0.5) / 1000) * 1000))
        exclusive_var = tk.BooleanVar(value=True)
        win_bonus_var = tk.IntVar(value=getattr(fighter, "win_bonus", 0))
        bonus_var = tk.IntVar(value=getattr(fighter, "finish_bonus_pct", 0) if existing else 15)
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
        relation_discount = self.staff_negotiation_discount("Talent Relations", 2600)
        relation_admin_saving = self.staff_negotiation_administration_saving(2600) if hasattr(self, "staff_negotiation_administration_saving") else 0
        comeback_premium = round(12000 * (1 - comeback_motivation_discount)) if comeback else 0
        state = {"attempts": 3, "target": ask + fighter.popularity * 420 + fighter.professionalism * 180 - relation_discount - relation_admin_saving + comeback_premium,
                 "rival_bid": 0}

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"NEGOTIATION: {self.fighter_display_name(fighter)}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        comeback_text = "A comeback requires a convincing financial and career package; the fighter stays retired if talks fail."
        if comeback:
            motivation_value = int(getattr(fighter, "motivation", 65) or 0)
            if comeback_motivation_discount > 0:
                comeback_text += (
                    f" They are motivated to fight again ({motivation_value} motivation) and have shaved "
                    f"{comeback_motivation_discount:.0%} off their asking price."
                )
            elif comeback_motivation_discount < 0:
                comeback_text += (
                    f" They are lukewarm about returning ({motivation_value} motivation) and have added "
                    f"{abs(comeback_motivation_discount):.0%} to their asking price."
                )
            else:
                comeback_text += " Their motivation to return is average, so their asking price is unadjusted."
        rival_text = (comeback_text
                      if comeback else f"Live rival offer: {rival_name} is offering ${active_offer_purse:,}/fight for {fighter.ai_offer_months} months; you can beat it before next month."
                      if active_offer_purse else ("Renewal talks start warmer because they already work here." if existing
                                                  else f"{rival_name} may bid if talks drag." if rival
                                                  else "No rival promotion is currently able to bid; the fighter will judge your offer on its own merits."))
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
        render_portrait(portrait, fighter, size=98, ratings_visible=True)

        summary = tk.Frame(profile, bg=self.colors["panel_dark"])
        summary.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        name_row = tk.Frame(summary, bg=self.colors["panel_dark"])
        name_row.pack(fill="x")
        tk.Label(name_row, text=self.fighter_display_name(fighter).upper(), bg=self.colors["panel_dark"], fg=self.colors["gold"],
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
        if relation_admin_saving:
            chip(chips, "Staff admin saving", f"${relation_admin_saving:,}", "#1f4a3a")

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
            terms = self.validated_contract_terms(
                purse_var.get(), term_var.get(), fights_var.get(), signing_var.get(),
                bonus_var.get(), win_bonus_var.get(), ppv_var.get(),
            )
            purse, term, fights = terms["purse"], terms["months"], terms["guaranteed_fights"]
            bonus, signing, exclusive = terms["finish_bonus_pct"], terms["signing_bonus"], exclusive_var.get()
            win_bonus, ppv = terms["win_bonus"], terms["ppv_points"]
            champ_clause, title_shot = champ_clause_var.get(), title_shot_var.get()
            main_event_promise, top_opponent_promise = main_event_promise_var.get(), top_opponent_promise_var.get()
            term = self.normalized_contract_months(term)
            duration_score = self.contract_duration_offer_score(
                term, purse, ask, signing_bonus=signing, win_bonus=win_bonus,
                finish_bonus_pct=bonus,
            )
            score = purse + duration_score + fights * 2100 + bonus * 260 + signing * 0.35 + self.company_pop * 190 + self.company_stability * 95
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
                popup = self.create_managed_window(parent=window)
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
            available, unavailable_reason = self.contract_negotiation_target_is_current(
                fighter, existing, comeback, source_promotion, transfer_deal,
            )
            if not available:
                proposal_update("needs_review", outcome="Fighter contract talks became stale before commitment.", error=unavailable_reason)
                result_label.config(text=unavailable_reason + " No money was charged.")
                submit_button.config(state="disabled")
                return
            if source_promotion is not None and fighter not in source_promotion.roster:
                proposal_update("needs_review", outcome="The source roster changed before contract commitment.", error=f"{self.fighter_display_name(fighter)} has already left {source_promotion.name}.")
                result_label.config(text=f"{self.fighter_display_name(fighter)} has already left {source_promotion.name}. No money was charged.")
                submit_button.config(state="disabled")
                if hasattr(self, "refresh_regional_prospects"):
                    self.refresh_regional_prospects()
                return
            if source_promotion is not None:
                assessment = self.regional_candidate_assessment(fighter, source_promotion)
                if not assessment["eligible"]:
                    result_label.config(text=f"{self.fighter_display_name(fighter)} is not eligible to sign yet: {assessment['explanation']}.")
                    submit_button.config(state="disabled")
                    if hasattr(self, "refresh_regional_prospects"):
                        self.refresh_regional_prospects()
                    return
            try:
                terms = self.validated_contract_terms(
                    purse_var.get(), term_var.get(), fights_var.get(), signing_var.get(),
                    bonus_var.get(), win_bonus_var.get(), ppv_var.get(),
                )
            except (tk.TclError, ValueError) as exc:
                result_label.config(text=f"Invalid contract: {exc}")
                return
            purse, term, fights = terms["purse"], terms["months"], terms["guaranteed_fights"]
            if term != term_var.get():
                term_var.set(term)
            bonus, signing, exclusive = terms["finish_bonus_pct"], terms["signing_bonus"], exclusive_var.get()
            score, target, _pct, unmet = evaluate()
            score += random.randint(-4500, 4500)
            if score >= target:
                signing_cost = purse * (2 if exclusive else 1) + signing
                transfer_cash = int((transfer_deal or {}).get("cash", 0) or 0)
                if self.cash < signing_cost + transfer_cash:
                    proposal_update("needs_review", outcome="The accepted package could not be funded at commitment.", error=f"Not enough cash for ${signing_cost + transfer_cash:,} up-front cost.")
                    result_label.config(text=f"Not enough cash for ${signing_cost + transfer_cash:,} up-front cost.")
                    return
                if transfer_deal is not None:
                    committed, detail = self.commit_player_transfer_deal(transfer_deal, fighter)
                    if not committed:
                        result_label.config(text=detail)
                        submit_button.config(state="disabled")
                        return
                    # The swap commit already records both sides' membership
                    # facts before moving either roster entry.
                    membership_recorded = True
                else:
                    membership_recorded = False
                if source_promotion is not None:
                    # The transfer and payment are one decision. If the feeder
                    # no longer owns the fighter, stop before touching cash.
                    if fighter not in source_promotion.roster:
                        result_label.config(text=f"{self.fighter_display_name(fighter)} is no longer available from {source_promotion.name}. No money was charged.")
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
                    self.vacate_special_belts_held_by(
                        fighter,
                        f"Signed by {self.player_company_name} from the regional circuit.",
                        owner=source_promotion,
                    )
                    membership = getattr(self, "record_membership_event", None)
                    if callable(membership):
                        membership(
                            fighter, "leave", promotion=source_promotion,
                            reason="Signed by the player promotion from the regional circuit.",
                            source_transaction=f"regional-signing:{fighter.fighter_id}:{source_promotion.name}:{self.month}:{self.week}",
                        )
                        membership(
                            fighter, "join", company_name=self.player_company_name,
                            reason="Signed by the player promotion from the regional circuit.",
                            source_transaction=f"regional-signing:{fighter.fighter_id}:{source_promotion.name}:{self.month}:{self.week}",
                        )
                        membership_recorded = True
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
                    # A retired fighter is leaving ``retired_fighters`` and
                    # re-entering the player roster at this boundary.  Record
                    # the return before either collection changes so the
                    # append-only Company Timeline cannot show a roster
                    # presence without its transition fact.  The stable key
                    # makes a retried comeback idempotent.
                    membership = getattr(self, "record_membership_event", None)
                    if callable(membership):
                        membership(
                            fighter, "return", company_name=self.player_company_name,
                            reason="Returned for a comeback contract.",
                            source_transaction=f"comeback-signing:{getattr(fighter, 'fighter_id', '')}:{self.player_company_name}:{self.month}:{self.week}",
                        )
                        membership_recorded = True
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
                        membership = getattr(self, "record_membership_event", None)
                        if callable(membership):
                            membership(
                                fighter, "join", company_name=self.player_company_name,
                                reason="Direct contract negotiation",
                                source_transaction=f"contract-signing:{getattr(fighter, 'fighter_id', '')}:{self.player_company_name}:{self.month}:{self.week}",
                            )
                            membership_recorded = True
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
                    if not comeback:
                        fighter.guaranteed_fights = fights
                        fighter.contract_fights_completed = 0
                fighter.exclusive = exclusive
                fighter.contract_type = "Exclusive" if exclusive else "Non-Exclusive"
                fighter.win_bonus = terms["win_bonus"]
                fighter.finish_bonus_pct = bonus
                fighter.ppv_points = terms["ppv_points"]
                fighter.champions_clause = champ_clause_var.get()
                fighter.title_shot_clause = title_shot_var.get()
                fighter.main_event_promise = main_event_promise_var.get()
                fighter.top_opponent_promise = top_opponent_promise_var.get()
                fighter.promise_deadline_month = self.month + 6 if fighter.main_event_promise or fighter.top_opponent_promise else 0
                promised_opportunities = []
                if fighter.main_event_promise:
                    promised_opportunities.append("main-event")
                if fighter.top_opponent_promise:
                    promised_opportunities.append("top-opponent")
                self.record_contract_promise_story(fighter, promised_opportunities, self.player_company_name)
                if existing:
                    self.record_contract_renewal(
                        fighter, self.player_company_name, term,
                        source="Direct contract negotiation",
                    )
                elif not comeback:
                    self.record_contract_signing(
                        fighter, self.player_company_name,
                        source="Direct contract negotiation",
                        record_membership=not membership_recorded,
                    )
                competing_company = (
                    active_offer_company
                    or (rival.name if rival is not None and state["rival_bid"] else "")
                )
                if competing_company and not existing and not comeback:
                    self.record_promotion_war_event(
                        self.player_company_name, competing_company, "talent_signing",
                        f"{self.player_company_name} beat {competing_company} to the signing of {fighter.name}.",
                        fighters=[fighter], importance=3,
                        event_ref=f"contract-battle:{fighter.fighter_id}:{self.month}:{self.week}:{self.story_company_key(self.player_company_name)}",
                    )
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
                if comeback:
                    self.record_comeback_contract_story(
                        fighter, farewell=farewell, fights=1 if farewell else fights,
                        company=self.player_company_name,
                    )
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
            if rival is not None and not existing and not comeback and not active_offer_purse and state["attempts"] == 1 and fighter.popularity > 45 and random.random() < 0.6:
                state["rival_bid"] = round(ask * random.uniform(0.15, 0.4))
                result_label.config(text=f"{rival.name} has entered the bidding! {self.fighter_display_name(fighter)} now wants more to stay. Attempts left: {state['attempts']}")
                refresh_meter()
                return
            if state["attempts"] <= 0:
                proposal_update(
                    "rejected",
                    outcome="The fighter's camp rejected the transfer contract package.",
                    error="No contract was completed after the available negotiation attempts.",
                )
                if existing and self.active_contract_saga(fighter):
                    self.record_contract_saga(
                        fighter, self.player_company_name, phase="talks_broken_down",
                        summary=f"Renewal talks between {fighter.name} and {self.player_company_name} broke down.",
                        importance=4,
                        beat_ref=f"contract-talks-broken:{fighter.fighter_id}:{self.month}:{self.week}",
                        former_company=self.player_company_name,
                    )
                if active_offer_purse:
                    result_label.config(text=f"Your talks ended. {rival_name}'s live offer remains in place until next month.")
                elif rival is not None and not existing and not comeback and source_promotion is None and state["rival_bid"] and random.random() < 0.5:
                    rival_purse = max(round(ask * 1.08 / 500) * 500, fighter.purse)
                    rival_term = random.randint(10, 22)
                    rival_bonus = max(rival_purse, round(rival_purse * random.uniform(0.8, 1.5) / 500) * 500)
                    signed, detail = self.complete_ai_free_agent_signing(
                        fighter, rival, rival_purse, rival_term, rival_bonus,
                        source="Won the bidding after player negotiations broke down",
                        rival_company=self.player_company_name,
                    )
                    result_label.config(text=(f"{self.fighter_display_name(fighter)} signed with {rival.name} instead." if signed else f"{rival.name}'s bid collapsed: {detail}"))
                else:
                    result_label.config(text=(f"{self.fighter_display_name(fighter)} stays retired. The comeback package was not convincing enough." if comeback else f"{self.fighter_display_name(fighter)}'s camp walks away. They wanted a stronger package."))
                submit_button.config(state="disabled")
                return
            if unmet:
                feedback = f"They still want {unmet[0]}."
            elif score < target - 15000:
                feedback = "The overall package is well short."
            else:
                feedback = "Close, but they want better total security."
            result_label.config(text=f"{feedback} Attempts left: {state['attempts']}")

        def close_transfer_talks():
            current = self.company_proposal_read_model(proposal_id=proposal_id, limit=1) if proposal_id and callable(getattr(self, "company_proposal_read_model", None)) else []
            status = str(current[0].get("status", "") or "") if current else ""
            if proposal_id and status not in {"needs_review", "rejected", "committed", "withdrawn", "expired"}:
                proposal_update("withdrawn", outcome="Player closed the fighter contract window before commitment.")
            window.destroy()

        button_row = ttk.Frame(body, style="Panel.TFrame")
        button_row.pack(fill="x", pady=8)
        submit_button = ttk.Button(button_row, text="Submit Offer", style="Accent.TButton", command=submit)
        submit_button.pack(side="left", padx=12)
        ttk.Button(button_row, text="Walk Away", command=close_transfer_talks).pack(side="right", padx=12)
        if proposal_id:
            window.protocol("WM_DELETE_WINDOW", close_transfer_talks)

    def open_negotiation(self):
        selected = self.market_tree.selection()
        if not selected:
            if hasattr(self, "_market_status_notice"):
                self._market_status_notice("Select a free agent first.")
            else:
                messagebox.showinfo("Negotiations", "Select a free agent first.")
            return
        fighter = getattr(self, "market_tree_fighters", {}).get(selected[0])
        if fighter not in self.free_agents:
            self.refresh_market()
            if hasattr(self, "_market_status_notice"):
                self._market_status_notice("That fighter is no longer available. Refresh the market and choose another fighter.", warning=True)
            else:
                messagebox.showinfo("Negotiations", "That fighter is no longer available.")
            return
        self.open_contract_negotiation(fighter, existing=False)
        return
        window = self.create_managed_window()
        window.title(f"Negotiate - {self.fighter_display_name(fighter)}")
        window.geometry("520x360")
        window.configure(bg=self.colors["chrome"])

        rival = random.choice(self.promotions)
        rival_offer = round(fighter.purse * random.uniform(0.85, 1.45) + rival.reputation_score * 220)
        purse_var = tk.IntVar(value=max(fighter.purse, rival_offer - 2500))
        term_var = tk.IntVar(value=12)
        exclusive_var = tk.BooleanVar(value=True)

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"NEGOTIATION: {self.fighter_display_name(fighter)}", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        body = ttk.Frame(window, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        info = (
            f"{fighter.weight} | {fighter.record} | OVR {fighter.overall} | Pop {fighter.popularity}\n"
            f"Style: {fighter.style_label} / {fighter.behaviour} | Camp: {fighter.camp}\n"
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
                result_label.config(text=f"{self.fighter_display_name(fighter)} rejected the offer. {rival.name}'s bid is stronger.")

        ttk.Button(body, text="Submit Offer", style="Accent.TButton", command=submit_offer).pack(side="left", padx=12, pady=12)
        ttk.Button(body, text="Walk Away", command=window.destroy).pack(side="right", padx=12, pady=12)

    def selected_event_economics(self, *, repair=True):
        """Read the booking screen's per-event economic levers.

        Explicit booking/commit callers keep the legacy repair boundary.  A
        page forecast can pass ``repair=False`` so opening or repainting the
        Upcoming/Matchmaking reader does not normalize a malformed finance
        envelope merely to display a quote.
        """
        if repair:
            self.ensure_finance_defaults()
        finance = getattr(self, "finance", {})
        if not isinstance(finance, dict):
            finance = {}
        ticket_default = finance.get("ticket_price", 55)
        marketing_default = finance.get("marketing_budget", 18_000)

        def read(variable, fallback):
            try:
                return int(variable.get())
            except Exception:
                try:
                    return int(fallback)
                except (TypeError, ValueError):
                    return 55 if fallback is ticket_default else 18_000

        tier = self.event_production_tier.get() if hasattr(self, "event_production_tier") else DEFAULT_EVENT_PRODUCTION_TIER
        return {
            "ticket_price": max(EVENT_TICKET_PRICE_MIN, min(EVENT_TICKET_PRICE_MAX, read(
                getattr(self, "event_ticket_price", None) or tk.IntVar(value=ticket_default),
                ticket_default))),
            "marketing_budget": max(0, min(EVENT_MARKETING_BUDGET_MAX, read(
                getattr(self, "event_marketing_budget", None) or tk.IntVar(value=marketing_default),
                marketing_default))),
            "production_tier": tier if tier in EVENT_PRODUCTION_TIERS else DEFAULT_EVENT_PRODUCTION_TIER,
        }

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
        base = (a.popularity + b.popularity) / 2 + title + main + rivalry / 2 + media + rank_bonus + marketing_lift
        # A booked grudge match is worth more than the sum of its fighters.
        grudge = self.grudge_match_state(a, b)
        if grudge["grudge"]:
            lift = (grudge["heat"] / 100.0) * GRUDGE_MATCH_MAX_HYPE_BONUS
            if grudge["rematch_due"]:
                lift *= 1.2
            base *= 1 + min(GRUDGE_MATCH_MAX_HYPE_BONUS, lift)
        return max(1, round(base * tier_factor))

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
        rivalry_heat = self.rivalry_heat_between(a, b)
        rivalry = 10 + rivalry_heat * 0.22 if rivalry_heat else 0
        stakes = (10 if fight.get("title") else 0) + (6 if fight.get("main") else 0)
        competitiveness = max(0, 18 - abs(a.overall - b.overall))
        matchmaker_lift = self.staff_effect("Matchmaker", 0.28)
        rank_a = rank_map.get(self.fighter_identity_key(a)) if rank_map is not None else None
        rank_b = rank_map.get(self.fighter_identity_key(b)) if rank_map is not None else None
        return max(1, min(99, round((self.fight_build_score(a, rank_a) + self.fight_build_score(b, rank_b)) / 2 + style_clash + rivalry + stakes + competitiveness * 0.35 + matchmaker_lift)))

    def run_event(self):
        if len(self.booked) < 1:
            setter = getattr(self, "set_schedule_status", None)
            if callable(setter):
                setter("RUN BLOCKED: Book at least one fight before running an event.", "error")
            else:
                messagebox.showinfo("No fights", "Book at least one fight before running an event.")
            return
        self.normalize_card_order()
        current_name = self.event_name.get().strip()
        event_name = self.default_event_name(self.next_player_event_number()) if self.is_auto_event_name(current_name) else current_name
        immediate_fights = []
        for booked_fight in self.booked:
            snapshot = dict(booked_fight)
            snapshot["fighter_ids"] = [
                getattr(self._resolve_event_fighter(reference), "fighter_id", "") if reference != "TBA" else ""
                for reference in self.event_fight_participant_references(snapshot)
            ]
            immediate_fights.append(snapshot)
        event = {"event_id": self._foundation_next_id("event") if hasattr(self, "_foundation_next_id") else "", "name": event_name, "venue": self.venue.get(), "region": self.event_region.get(), "city": self.event_city.get(), "month": self.month, "week": self.week, "fights": immediate_fights, **self.selected_event_economics()}
        if hasattr(self, "register_grand_prix_series_for_event"):
            self.register_grand_prix_series_for_event(event)
        self.record_homecoming_booking(event, self.player_company_name)
        package = self.prepare_event_result(event)
        self.finish_event(event, package)
        self.booked.clear()
        self._event_price_user_set = False
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
            fighters = [fighter for fighter in self.event_fight_fighters(fight) if fighter in self.roster]
            if fight.get("tournament") and len(fighters) > 2:
                fighters = [fighters[0], fighters[-1]]
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
        rivalry = bool(self.rivalry_heat_between(a, b))
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
        """Honor the negotiated purse regardless of card placement.

        Card tier controls presentation and commercial draw, not whether the
        promotion may silently withhold part of a signed fighter's pay.
        """
        return 1.0

    def player_bout_purse_cost(self, fight, a, b):
        return round((a.purse + b.purse) * self.player_bout_purse_factor(fight))

    def event_contract_clause_payouts(self, results, finance):
        """Calculate every fight-night clause from the completed card once."""
        ppv_pool = max(0, int(finance.get("ticket_revenue", 0) or 0)) + max(0, int(finance.get("broadcast_income", 0) or 0))
        win_bonuses = 0
        finish_bonuses = 0
        ppv_points = 0
        ppv_fighters = set()
        for winner, loser, _fight, method in results:
            if method not in ("Draw", "No Contest") and winner in self.roster:
                win_bonuses += max(0, int(getattr(winner, "win_bonus", 0) or 0))
                if method in FINISH_METHODS:
                    finish_pct = max(0, int(getattr(winner, "finish_bonus_pct", 0) or 0))
                    finish_bonuses += round(max(0, int(getattr(winner, "purse", 0) or 0)) * finish_pct / 100)
            # PPV is an event-level revenue share. Tournament entrants who fight
            # more than once are still paid their points only once for the card.
            for fighter in (winner, loser):
                fighter_key = getattr(fighter, "fighter_id", "") or id(fighter)
                if fighter not in self.roster or fighter_key in ppv_fighters:
                    continue
                ppv_fighters.add(fighter_key)
                ppv_points += round(ppv_pool * max(0, int(getattr(fighter, "ppv_points", 0) or 0)) / 100)
        return {
            "win_bonuses": win_bonuses,
            "finish_bonuses": finish_bonuses,
            "ppv_points": ppv_points,
            "total": win_bonuses + finish_bonuses + ppv_points,
        }

    def finalize_event_fight_pay(self, finance, results, awards):
        """Reconcile awards and clauses into the canonical event profit."""
        old_tax = max(0, int(finance.get("tax", 0) or 0))
        old_awards = max(0, int(finance.get("bonuses", 0) or 0))
        pre_tax_expense = max(0, int(finance.get("total_expense", 0) or 0) - old_tax - old_awards)
        award_payout = sum(
            max(0, int(award.get("bonus", 0) or 0)) * len(award.get("fighters", []))
            for award in awards
        )
        clauses = self.event_contract_clause_payouts(results, finance)
        pre_tax_expense += award_payout + clauses["total"]
        tax_rate = max(0.0, float(self.finance.get("tax_rate", 0) or 0))
        total_revenue = max(0, int(finance.get("total_revenue", 0) or 0))
        tax = round(max(0, total_revenue - pre_tax_expense) * tax_rate)
        total_expense = pre_tax_expense + tax
        finance.update({
            "bonuses": award_payout,
            "contract_clauses": clauses["total"],
            "win_bonuses": clauses["win_bonuses"],
            "finish_bonuses": clauses["finish_bonuses"],
            "ppv_points_payout": clauses["ppv_points"],
            "contract_clauses_included": True,
            "tax": tax,
            "total_expense": total_expense,
            "profit": total_revenue - total_expense,
        })
        return finance

    def record_standard_guaranteed_fight(self, fighter):
        """Count a completed official bout against an ordinary player guarantee."""
        if fighter not in self.roster or getattr(fighter, "comeback_contract", False):
            return 0
        guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
        if guaranteed <= 0 or completed >= guaranteed:
            return 0
        fighter.contract_fights_completed = min(guaranteed, completed + 1)
        remaining = guaranteed - fighter.contract_fights_completed
        fighter.fight_history = fighter.fight_history or []
        fighter.fight_history.insert(0, f"Contract guarantee: {fighter.contract_fights_completed}/{guaranteed} fights completed.")
        if remaining == 0:
            fighter.relationship_trust = min(100, int(getattr(fighter, "relationship_trust", 55) or 55) + 6)
            fighter.morale = min(100, fighter.morale + 3)
            self.inbox.append({
                "subject": f"Fight Guarantee Fulfilled - {fighter.name}",
                "body": f"{fighter.name} has received all {guaranteed} guaranteed fights in their contract. Trust and morale improved.",
                "type": "Contracts", "resolved": True, "seen": False,
            })
        return remaining

    def prepare_event_result(self, event):
        # A player-arranged card is not re-sorted on fight night. The top row
        # is the main event, and therefore the name and watch order source.
        # Title changes decided tonight are dated to the day this card runs.
        self._active_card_day = self.event_day(event)
        self.normalize_card_order(event.get("fights", []))
        self.refresh_scheduled_event_auto_name(event)
        log = [f"{event['name']} - {event['venue']} ({self.event_date_label(event)})", "=" * 72]
        grand_prix_preflight = (
            self.prepare_grand_prix_event(event)
            if hasattr(self, "prepare_grand_prix_event") else {"postponed": False, "notes": []}
        )
        preflight_notes = list(grand_prix_preflight.get("notes", []) or []) if isinstance(grand_prix_preflight, dict) else []
        if isinstance(grand_prix_preflight, dict) and grand_prix_preflight.get("postponed"):
            reason = str(grand_prix_preflight.get("reason", "The Grand Prix was postponed before preparation.") or "The Grand Prix was postponed before preparation.")
            log.append("GRAND PRIX POSTPONED: " + reason)
            self._active_card_day = None
            return {
                "preparation_pending": True,
                "grand_prix_postponed": True,
                "pending_reason": reason,
                "event_id": str(event.get("event_id", "") or ""),
                "event_name": event.get("name", ""),
                "venue": event.get("venue", ""),
                "region": event.get("region", self.venue_region(event.get("venue", ""))),
                "city": event.get("city", ""),
                "month": event.get("month", self.month),
                "week": event.get("week", 1),
                "day": self.event_day(event),
                "log": log,
                "fight_logs": [],
                "results": [],
                "preparation_timeline": self.event_preparation_timeline(event, press_log=[], weigh_log=[], cancelled_fights=[]),
            }
        if preflight_notes:
            log.extend(["", "GRAND PRIX FIELD UPDATE"])
            log.extend(f"  {note}" for note in preflight_notes)
        # A title-miss prompt can interrupt preparation after press has already
        # been resolved.  Reuse that retained read model on retry so reopening
        # the decision does not roll another face-off, heat change or rivalry.
        stored_preparation = event.get("preparation_timeline") if isinstance(event, dict) else None
        if isinstance(stored_preparation, dict) and "press_outcomes" in stored_preparation:
            raw_press = stored_preparation.get("press_outcomes")
            press_log = [str(value) for value in raw_press] if isinstance(raw_press, list) else []
            try:
                press_hype = float(stored_preparation.get("press_hype", 0) or 0)
                if not math.isfinite(press_hype):
                    press_hype = 0.0
            except (TypeError, ValueError, OverflowError):
                press_hype = 0.0
        else:
            press_log, press_hype = self.run_press_conference(event)
        event["preparation_timeline"] = self.event_preparation_timeline(
            event, press_log=press_log, weigh_log=[], cancelled_fights=[],
        )
        event["preparation_timeline"]["press_hype"] = press_hype
        log.extend(press_log)
        weigh_log, purse_penalty, cancelled_fights = self.run_weigh_ins(event)
        log.extend(weigh_log)
        pending_fights = [
            fight for fight in cancelled_fights
            if isinstance(fight, dict)
            and str((fight.get("title_miss_decision_state") or {}).get("status", "") or "") == "awaiting_player"
        ]
        if pending_fights:
            pending_ids = [
                str(fight.get("fight_id", "") or "")
                for fight in pending_fights
            ]
            pending_reason = (
                "The card is paused at the recorded weigh-in boundary. "
                "Choose a title-miss action before any bout is executed or settled."
            )
            timeline = self.event_preparation_timeline(
                event, press_log=press_log, weigh_log=weigh_log,
                cancelled_fights=[],
            )
            timeline.update({
                "status": "awaiting_player",
                "pending_reason": pending_reason,
                "pending_fight_ids": pending_ids,
                "press_hype": press_hype,
                "final_readiness": "Awaiting player title-miss decision",
            })
            for stage in timeline.get("stage_states", []):
                if isinstance(stage, dict) and stage.get("stage_id") == "readiness":
                    stage["status"] = "Awaiting player"
                    stage["detail"] = pending_reason
            event["preparation_timeline"] = timeline
            self._active_card_day = None
            return {
                "preparation_pending": True,
                "pending_reason": pending_reason,
                "pending_fight_ids": pending_ids,
                "event_id": str(event.get("event_id", "") or ""),
                "event_name": event.get("name", ""),
                "venue": event.get("venue", ""),
                "region": event.get("region", self.venue_region(event.get("venue", ""))),
                "city": event.get("city", ""),
                "month": event.get("month", self.month),
                "week": event.get("week", 1),
                "day": self.event_day(event),
                "log": log,
                "press_log": press_log,
                "weigh_in_log": weigh_log,
                "fight_logs": [],
                "results": [],
                "preparation_timeline": timeline,
            }
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
                references = self.event_fight_participant_references(fight)
                a = self.resolve_fighter(references[0]) if references and references[0] != "TBA" else None
                b = self.resolve_fighter(references[1]) if len(references) > 1 and references[1] != "TBA" else None
                a_status, b_status = self.fight_corner_title_statuses(fight, a, b) if a and b else ("", "")
                fight_logs.append({
                    "heading": lines[0], "lines": lines, "cancelled": True,
                    "a": names[0] if names else "", "b": names[1] if len(names) > 1 else "",
                    "a_id": getattr(a, "fighter_id", ""), "b_id": getattr(b, "fighter_id", ""),
                    "a_record": getattr(a, "record", ""), "b_record": getattr(b, "record", ""),
                    "a_rating": self.bout_rating_snapshot(a) if a else {}, "b_rating": self.bout_rating_snapshot(b) if b else {},
                    "weight": getattr(a, "weight", fight.get("tba_weight", "")), "label": "CANCELLED BOUT",
                    "a_title_status": a_status, "b_title_status": b_status,
                    # Preserve the pre-fight title-miss decision evidence in the
                    # read-only event archive.  The fight dict is the source of
                    # truth during weigh-ins, but the archive is what profile,
                    # replay and audit views actually receive after settlement.
                    "title_miss_decision_state": deepcopy(fight.get("title_miss_decision_state", {})),
                    "title_sanction_snapshot": deepcopy(fight.get("title_sanction_snapshot", {})),
                    "result": "Cancelled - no contest took place",
                })
                continue
            if fight.get("tournament"):
                tournament = self.simulate_event_tournament(event, fight)
                results.extend(tournament["results"])
                award_pool.extend(tournament["award_pool"])
                fight_logs.extend(tournament["fight_logs"])
                bracket = tournament["bracket"]
                edition_number = len(tournament_brackets) + 1
                event_identity = str(event.get("event_id", "") or event.get("name", "event")).strip()
                bracket.setdefault("event_id", event_identity)
                bracket.setdefault("edition_id", f"{event_identity}:tournament:{edition_number}")
                match_count = sum(len(stage.get("matches", []) or []) for stage in bracket.get("stages", []) if isinstance(stage, dict))
                bracket.setdefault(
                    "result_refs",
                    [f"{event_identity}:tournament:{edition_number}:match:{match_number}" for match_number in range(1, match_count + 1)],
                )
                tournament_brackets.append(bracket)
                total_hype += tournament["hype"]
                total_build += tournament["build"]
                total_excitement += tournament["excitement"]
                total_cost += tournament["cost"]
                total_contract_cost += tournament.get("contracted_cost", tournament["cost"])
                log.extend(["", bracket["title"].upper(), "-" * 72])
                for stage in bracket["stages"]:
                    log.append(stage["name"])
                    log.extend(f"  {match['summary']}" for match in stage["matches"])
                log.append(f"  GRAND PRIX CHAMPION: {bracket['champion']}")
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
            official_winner = method not in ("Draw", "No Contest")
            award_pool.append({"winner": winner.name if official_winner else "", "winner_id": winner.fighter_id if official_winner else "", "loser": loser.name if official_winner else "", "fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id], "method": method, "excitement": excitement, "round": round_no, "fight": f"{a.name} vs {b.name}"})
            label = f"{fight['special_belt'].upper()} TITLE FIGHT" if fight.get("special_belt") else ("MAIN EVENT" if fight["main"] else ("TITLE FIGHT" if fight["title"] else "BOUT"))
            if fight.get("special_belt") and fight.get("divisional_title"):
                label += " + " + ("INTERIM TITLE" if fight.get("interim") else "DIVISIONAL TITLE")
            if fight.get("interim") and not fight.get("special_belt"):
                label = "INTERIM " + label
            lines = [f"{label}: {a.name} vs {b.name} ({a.weight})", f"Odds: {self.matchup_odds(a, b)}"]
            # Camp length lives on the fighter, not the booking. These read
            # 'red_camp'/'blue_camp'/'camp_weeks' off the fight dict, which
            # nothing has ever written, so every corner read fell through to the
            # hardcoded default and reported an 8-week camp for everyone --
            # including short-notice replacements who had no camp at all.
            red_form = f"{a.name}: camp {getattr(a, 'camp_weeks', 0)}w, morale {a.morale}, fatigue {a.fatigue}, cut penalty {getattr(a, 'weight_cut_penalty', 0)}"
            blue_form = f"{b.name}: camp {getattr(b, 'camp_weeks', 0)}w, morale {b.morale}, fatigue {b.fatigue}, cut penalty {getattr(b, 'weight_cut_penalty', 0)}"
            lines.append(f"Corner read: {red_form} | {blue_form}")
            lines.extend(commentary)
            if method == "Draw":
                lines.append(f"Result: {a.name} vs {b.name} ends in a draw, R{round_no} | Fight excitement {excitement}")
                result_text = f"Draw (R{round_no})"
            elif method == "No Contest":
                lines.append(f"Result: {a.name} vs {b.name} is ruled a No Contest, R{round_no} | Fight excitement {excitement}")
                result_text = f"No Contest (R{round_no})"
            else:
                lines.append(f"Result: {winner.name} def. {loser.name} by {method}, R{round_no} | Fight excitement {excitement}")
                result_text = f"{winner.name} - {method} R{round_no}"
            fight_logs.append({
                "heading": lines[0], "lines": lines,
                "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                "winner": winner.name if official_winner else "", "winner_id": winner.fighter_id if official_winner else "", "draw": method == "Draw", "no_contest": method == "No Contest",
                "a_record": a.record, "b_record": b.record,
                "a_rating": a_rating, "b_rating": b_rating,
                "weight": a.weight, "label": label, "title": bool(fight.get("title", False)), "divisional_title": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))), "interim": bool(fight.get("interim", False)), "special_belt": str(fight.get("special_belt", "") or ""), "result": result_text, "excitement": excitement,
                "a_title_status": a_title_status, "b_title_status": b_title_status,
                "a_start_gas": a_start_gas, "b_start_gas": b_start_gas, "scorecards": fight["_scorecards"],
                # Keep the exact corner choices and sanction state alongside
                # the fight log so a saved event never loses why a title was
                # removed, waived, rebooked or replaced at the scale.
                "title_miss_decision_state": deepcopy(fight.get("title_miss_decision_state", {})),
                "title_sanction_snapshot": deepcopy(fight.get("title_sanction_snapshot", {})),
                "commentary_personality": self.commentary_personality(),
                "round_analysis": deepcopy(getattr(self, "_last_fight_result", None).metrics.get("round_analysis", []) if getattr(self, "_last_fight_result", None) else []),
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
        self.finalize_event_fight_pay(finance, results, awards)
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
        log.append(f"Contract clauses: ${finance.get('contract_clauses', 0):,} (win ${finance.get('win_bonuses', 0):,}, finish ${finance.get('finish_bonuses', 0):,}, PPV ${finance.get('ppv_points_payout', 0):,})")
        log.append(f"Total revenue: ${finance['total_revenue']:,} | Total expense: ${finance['total_expense']:,} | Profit: ${profit:,}")
        log.append(f"Company popularity will move from {self.company_pop} to {projected_pop}. Stability will move from {self.company_stability} to {projected_stability}.")
        tournament_note = f", {len(tournament_brackets)} tournament(s)" if tournament_brackets else ""
        summary = f"{event['name']} ({event['venue']}, {self.event_date_label(event)}): {len(results)} fights{tournament_note}, excitement {round(avg_excitement)}, gate ${gate:,}, profit ${profit:,}, popularity {projected_pop}%, stability {projected_stability}%"
        package = {
            "event_id": str(event.get("event_id", "") or ""),
            "regional_invitation_id": str(event.get("regional_invitation_id", "") or ""),
            "regional_invitation_entitlement_key": str(event.get("regional_invitation_entitlement_key", "") or ""),
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
            "preparation_timeline": self.event_preparation_timeline(
                event, press_log=press_log, weigh_log=weigh_log, cancelled_fights=cancelled_fights,
            ),
        }
        self._active_card_day = None
        return package

    def card_mismatch_penalty(self, results):
        penalty = 0
        for a, b, fight, _method in results:
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
        # Moving up still has to be a weight the fighter can actually make. This
        # branch used to measure frame fit only, so a 227lb featherweight was
        # waved into lightweight as an "undersized" move: he cannot make 155
        # either, and moving up one class does not fix a frame that belongs
        # three classes higher.
        required_cut = max(0, walk - target_limit)
        sustainable_cut = 9 + cut_skill * 0.16 + conditioning * 0.04 - max(0, natural_size - 55) * 0.12
        if required_cut > sustainable_cut + 2:
            return False, (
                f"Still overweight for {target_weight}: {walk} lb walk weight needs {required_cut:.0f} lb off to make "
                f"{target_limit} lb, and their frame and cutting skill support about {sustainable_cut:.0f} lb. "
                f"This fighter needs a heavier division, not this one."
            )
        parts = self.division_size_penalty_parts(fighter, target_weight)
        penalty = parts["penalty"]
        if penalty <= 1:
            return True, f"Natural move up: {walk} lb frame can add toward the {target_limit} lb limit over a full camp."
        severity = "manageable" if penalty <= 4 else "clear" if penalty <= 8 else "major"
        return True, (f"Undersized move accepted: {self.division_fit_reason(parts, target_weight)}. "
                      f"This creates a {severity} division-fit disadvantage ({penalty}/14) in physical exchanges, "
                      f"initiative, starting condition, and odds; it eases as they grow into the division.")

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

    def plausible_walk_weight_band(self, fighter, weight):
        """The believable walk-weight range for a division.

        Built from the same limit and spread constants as default_walk_weight so
        the generator and the validator cannot drift apart. This exists to catch
        frames that belong to a different division entirely -- a 295lb flyweight
        -- without touching the ordinary big-for-the-class fighter, who is a
        legitimate and interesting part of the game.
        """
        if weight not in WEIGHT_LIMITS:
            return 0, 999
        limit = WEIGHT_LIMITS[weight]
        if weight == "Heavyweight":
            # There is no weight to make at heavyweight, so the only question is
            # whether the frame is too small to belong there at all.
            return limit - 45, 295
        spread = 10 if limit <= 135 else 15 if limit <= 170 else 22 if limit <= 205 else 35
        if getattr(fighter, "gender", "Male") == "Female":
            spread = max(8, spread - 4)
        # The generator's own ceiling is limit + spread + 6 (the largest natural
        # size adjustment). Allow headroom above it for fighters who have grown
        # into the class, and room underneath for the genuinely undersized.
        return limit - 12, limit + spread + 12

    def assign_fighter_division(self, fighter, weight, *, reset_walk_weight=False):
        """Set a fighter's division and keep their frame honest. The only
        supported way to write fighter.weight.

        Walk weight used to be derived inside the generator from a randomly
        rolled division and then left behind when the caller overwrote .weight,
        which is how a fighter built as a heavyweight ended up defending a
        flyweight belt on a 295lb frame. Routing every division change through
        one place means the frame and the class cannot silently disagree again.
        """
        weight = self.game_weight_class(weight)
        if weight not in WEIGHT_LIMITS:
            return getattr(fighter, "weight", "")
        fighter.weight = weight
        if reset_walk_weight:
            fighter.walk_weight = self.default_walk_weight(fighter)
        else:
            self.repair_walk_weight_for_division(fighter)
        return weight

    def repair_walk_weight_for_division(self, fighter, force=False):
        """Pull an impossible frame back into its division's believable band.

        Returns how many pounds the frame was out by, or zero when it was
        already credible for the class.
        """
        weight = getattr(fighter, "weight", "")
        if weight not in WEIGHT_LIMITS:
            return 0
        walk = int(getattr(fighter, "walk_weight", 0) or 0)
        if not walk:
            fighter.walk_weight = self.default_walk_weight(fighter)
            return 0
        low, high = self.plausible_walk_weight_band(fighter, weight)
        if not force and low <= walk <= high:
            return 0
        gap = (low - walk) if walk < low else max(0, walk - high)
        fighter.walk_weight = self.default_walk_weight(fighter)
        return gap

    def division_size_penalty_parts(self, fighter, target_weight):
        """Break the division-fit penalty into its two independent causes.

        The penalty is the sum of a frame that is light for the class and a
        naturally small build. Reporting only the total produced messages that
        blamed the wrong one: a 227lb lightweight was told his walk weight was
        "light for Lightweight" when every point of it came from his build.
        """
        empty = {"penalty": 0, "size": 0.0, "frame": 0.0, "walk": 0, "expected": 0, "cause": "none"}
        if fighter.weight not in WEIGHT_LIMITS or target_weight not in WEIGHT_LIMITS:
            return empty
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        natural_size = self.ds(fighter, "natural_size", 50)
        # Measured against the division being entered rather than the direction
        # of travel. A fighter who drops down from heavyweight carrying a
        # lightweight's frame is exactly as undersized as one who climbed up to
        # it, and previously came away with no penalty at all.
        expected_walk = self.natural_walk_weight_for(fighter, target_weight)
        size_term = max(0, expected_walk - walk) / 4.5
        frame_term = max(0, 55 - natural_size) / 16
        penalty = max(0, min(14, round(size_term + frame_term)))
        if not penalty:
            cause = "none"
        elif size_term >= frame_term * 2:
            cause = "weight"
        elif frame_term >= size_term * 2:
            cause = "build"
        else:
            cause = "both"
        return {"penalty": penalty, "size": size_term, "frame": frame_term,
                "walk": int(walk), "expected": int(expected_walk), "cause": cause}

    def division_fit_reason(self, parts, target_weight):
        """Name the cause of a division-fit penalty rather than assuming weight."""
        if parts["cause"] == "weight":
            return (f"{parts['walk']} lb walk weight is light for {target_weight}, "
                    f"which wants about {parts['expected']} lb")
        if parts["cause"] == "build":
            return (f"a naturally small build for {target_weight}, "
                    f"even carrying a {parts['walk']} lb walk weight")
        return (f"a {parts['walk']} lb walk weight and a naturally small build "
                f"for {target_weight}")

    def division_size_penalty_for(self, fighter, target_weight):
        """Return the durable cost of competing below the division's natural size."""
        return self.division_size_penalty_parts(fighter, target_weight)["penalty"]

    def record_division_fit_step(self, fighter, weight, direction, moved, walk, penalty):
        """Keep a readable trail of how a frame settled into its division."""
        if direction == "up":
            detail = f"filled out {moved} lb to {walk} lb"
        elif direction == "down":
            detail = f"trimmed {moved} lb to {walk} lb"
        else:
            detail = f"settled at {walk} lb"
        entry = {
            "month": int(getattr(self, "month", 0)),
            "date": self.format_game_date(),
            "weight": weight,
            "walk": int(walk),
            "penalty": int(penalty),
            "direction": direction or "hold",
            "note": f"{weight}: {detail}, division fit {int(penalty)}/14",
        }
        log = list(getattr(fighter, "division_fit_log", None) or [])
        log.append(entry)
        fighter.division_fit_log = log[-24:]

    def acclimatize_division_fit(self, fighter):
        """Let a frame settle into the division the fighter actually competes in.

        Growing up is the common path and stays deliberately loose: a fighter
        competing above their natural size fills out toward the class over
        months of training and eating for it, and the division-fit penalty eases
        as they do.

        Coming down is the rare path and has to be earned by the body. A fighter
        carrying more than their division wants can recompose toward it, but
        only with the cutting skill, conditioning and build to support it, at
        roughly half the speed and a third of the frequency. Most oversized
        fighters never fully arrive, which is intended -- they should be moving
        up instead, and the annual division review will suggest exactly that.

        Called once per month from roster development.
        """
        if getattr(fighter, "retired", False):
            return
        weight = getattr(fighter, "weight", "")
        if weight not in WEIGHT_LIMITS:
            return
        penalty = int(getattr(fighter, "division_size_penalty", 0) or 0)
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        expected_walk = self.natural_walk_weight_for(fighter, weight)
        _low, ceiling = self.plausible_walk_weight_band(fighter, weight)
        # Nothing to grow into and nothing to trim: leave the fighter alone.
        if penalty <= 0 and walk <= ceiling:
            return
        natural_size = self.ds(fighter, "natural_size", 50)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        cut_skill = self.ds(fighter, "weight_cutting", fighter.cardio)
        moved = 0
        direction = ""
        if walk < expected_walk:
            # Younger fighters with growing frames adapt faster; veterans barely.
            chance = 0.16 + max(0, 30 - fighter.age) * 0.012
            if fighter.age >= 34:
                chance *= 0.45
            chance += (natural_size - 50) * 0.002 + max(0, conditioning - 55) * 0.001
            if random.random() > max(0.03, min(0.5, chance)):
                return
            moved = min(expected_walk - walk, random.randint(2, 5))
            walk += moved
            fighter.walk_weight = walk
            direction = "up"
        elif walk > ceiling:
            # Recomposition is real but slow, and a naturally large frame will
            # not hold a smaller division no matter how disciplined the athlete.
            chance = 0.05 + max(0, cut_skill - 55) * 0.0022 + max(0, conditioning - 55) * 0.0018
            chance += max(0, 50 - natural_size) * 0.0025
            chance -= max(0, fighter.age - 31) * 0.006
            if random.random() > max(0.01, min(0.22, chance)):
                return
            moved = min(walk - ceiling, random.randint(1, 3))
            walk -= moved
            fighter.walk_weight = walk
            direction = "down"
        else:
            return
        # Recompute the durable penalty from the frame as it now stands, and only
        # ever let it ease downward — at least one point per successful month.
        floor = self.division_size_penalty_for(fighter, weight)
        new_penalty = min(penalty, max(floor, penalty - 1)) if penalty else floor
        eased = new_penalty < penalty
        if eased:
            fighter.division_size_penalty = new_penalty
            fighter.division_size_note = (
                f"Fully adapted to {weight}: natural division fit." if new_penalty == 0
                else f"Adapting to {weight}: division-fit penalty eased to {new_penalty}/14."
            )
        elif direction == "down":
            fighter.division_size_note = (
                f"Recomposing toward {weight}: walk weight down to {walk} lb."
            )
        if moved or eased:
            self.record_division_fit_step(fighter, weight, direction, moved, walk, new_penalty)
        if eased and new_penalty == 0 and fighter in getattr(self, "roster", []):
            self.inbox.append({
                "subject": f"Division Fit — {fighter.name}",
                "body": f"{fighter.name} has fully grown into {weight}; the size disadvantage from the move up is gone.",
                "type": "Roster", "fighter": fighter.name, "resolved": False,
            })

    def complete_weight_class_move(self, fighter, target_weight, reason):
        """Apply a validated move; shared by the player UI and world simulation."""
        old_weight = fighter.weight
        # A real move keeps the frame the fighter actually has -- that is the
        # whole point of moving -- so the walk weight is carried across intact
        # and only repaired if it was never credible for either division.
        fighter.weight = target_weight
        self.repair_walk_weight_for_division(fighter)
        fighter.scale_weight = 0.0
        fighter.weight_cut_penalty = 0
        parts = self.division_size_penalty_parts(fighter, target_weight)
        fighter.division_size_penalty = parts["penalty"]
        fighter.division_size_note = (
            f"Moved to {target_weight} with {self.division_fit_reason(parts, target_weight)}: "
            f"division-fit penalty {parts['penalty']}/14."
            if parts["penalty"] else "Natural division fit."
        )
        self.record_division_fit_step(
            fighter, target_weight, "", 0,
            fighter.walk_weight or self.default_walk_weight(fighter), parts["penalty"],
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
        summary = f"{fighter.name} moved from {old_weight} to {target_weight}. {reason}"
        self.record_weight_journey_story(
            fighter, phase="division_reinvention", status="resolved", importance=4,
            summary=summary, resolution=summary,
        )
        self.record_crossroads_reinvention(
            fighter, self.fighter_company_name(fighter) or self.player_company_name,
            old_weight, target_weight,
        )
        return True

    def move_fighter_weight_class(self, fighter, target_weight):
        if getattr(self, "spectator_mode", False) or not self.player_owns_fighter(fighter):
            notice = getattr(self, "_roster_status_notice", None)
            if callable(notice):
                notice("Only a fighter currently on your roster can change division here.", warning=True)
            else:
                messagebox.showwarning("Division move unavailable", "Only a fighter currently on your roster can change division here.")
            return False
        if (
            self.player_owns_fighter(fighter)
            and self.belt_key(fighter.gender, target_weight) in set(getattr(self, "closed_divisions", set()))
        ):
            text = (f"{fighter.gender} {target_weight} is not operated by your promotion. "
                    "Reopen it or choose an active division.")
            notice = getattr(self, "_roster_status_notice", None)
            if callable(notice):
                notice(text, warning=True)
            else:
                messagebox.showwarning("Division closed", text)
            return False
        allowed, reason = self.weight_class_move_assessment(fighter, target_weight)
        if not allowed:
            notice = getattr(self, "_roster_status_notice", None)
            if callable(notice):
                notice(reason, warning=True)
            else:
                messagebox.showwarning("Division move declined", reason)
            return False
        if fighter.champion or fighter.interim_champion:
            text = "A champion must vacate their belt before changing division."
            notice = getattr(self, "_roster_status_notice", None)
            if callable(notice):
                notice(text, warning=True)
            else:
                messagebox.showwarning("Vacate title first", text)
            return False
        if fighter.name in self.scheduled_fighter_names(include_booked=True):
            text = "Complete or remove the fighter's booked bout before changing division."
            notice = getattr(self, "_roster_status_notice", None)
            if callable(notice):
                notice(text, warning=True)
            else:
                messagebox.showwarning("Future booking", text)
            return False
        self.complete_weight_class_move(fighter, target_weight, reason)
        notice = getattr(self, "_roster_status_notice", None)
        if callable(notice):
            notice(f"{fighter.name} moved to {target_weight}. {reason}")
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

    def prompt_title_weight_miss_decision(self, event, fight, misses):
        """Ask the player how to handle a title bout weight miss.

        The provider hook keeps the decision deterministic in regressions and
        lets spectator/AI flows retain their existing non-interactive policy
        until the full resumable title-decision slice is enabled.
        """
        provider = getattr(self, "_title_miss_decision_provider", None)
        if callable(provider):
            response = provider(event, fight, list(misses))
            # A dismissed/invalid provider response is not a sporting choice.
            # Keep the recorded decision pending so a caller cannot silently
            # turn a closed prompt into Keep Belt.
            return response if isinstance(response, dict) else {"action": "awaiting_player"}
        if getattr(self, "spectator_mode", False) or not hasattr(self, "root"):
            return {"action": "awaiting_player"}
        parent = self.root
        # Route the decision dialog through the shared registry so title-miss
        # prompts cannot leave an unmanaged window behind on close/reload.
        dialog = self.create_managed_window(parent=parent)
        dialog.title("Title decision required")
        dialog.geometry("760x480")
        dialog.minsize(680, 420)
        dialog.transient(parent)
        dialog.grab_set()
        result = {"action": "awaiting_player"}
        ttk.Label(dialog, text="TITLE WEIGHT MISS", style="ScreenTitle.TLabel").pack(fill="x", padx=12, pady=(12, 4))
        names = ", ".join(f"{fighter.name} ({miss_by:g} lb)" for fighter, miss_by in misses)
        ttk.Label(dialog, text=f"{names} missed the limit. Choose what happens to this title bout.", style="Panel.TLabel", wraplength=700).pack(fill="x", padx=14, pady=4)
        ttk.Label(dialog, text="Keep Belt keeps the title on the line. Remove Belt vacates it before the bout. Rebook and Cancel stop this bout.", style="Inset.TLabel", wraplength=700).pack(fill="x", padx=14, pady=(0, 10))
        consequence = tk.StringVar()
        ttk.Label(
            dialog, textvariable=consequence, style="Panel.TLabel", wraplength=700,
            anchor="w", justify="left",
        ).pack(fill="x", padx=14, pady=(0, 8))
        ttk.Label(dialog, text="LAST-MINUTE REPLACEMENT", style="Section.TLabel").pack(
            fill="x", padx=14, pady=(2, 0), anchor="w"
        )
        ttk.Label(
            dialog,
            text="Optional approved choice: select a ready same-division fighter, review the company/world ranks, then commit the replacement.",
            style="Inset.TLabel",
            wraplength=700,
            justify="left",
        ).pack(fill="x", padx=14, pady=(0, 4), anchor="w")
        replacement_frame = ttk.Frame(dialog, style="Inset.TFrame")
        replacement_frame.pack(fill="both", expand=True, padx=14, pady=6)
        replacement_frame.columnconfigure(1, weight=1)
        ttk.Label(replacement_frame, text="Missed corner", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=8, pady=(10, 4))
        corner_var = tk.StringVar()
        # Use a stable corner label rather than a bare name.  Two fighters can
        # legitimately share a display name, and the merit explanation must
        # follow the saved corner identity rather than whichever duplicate is
        # found first.
        corner_lookup = {}
        for miss_ordinal, (fighter, _miss_by) in enumerate(misses):
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            ids = list(fight.get("fighter_ids", []) or [])
            corner_index = ids.index(fighter_id) if fighter_id and fighter_id in ids else miss_ordinal
            label = f"{fighter.name} | Corner {corner_index + 1}"
            if label in corner_lookup:
                label = f"{label} ({miss_ordinal + 1})"
            corner_lookup[label] = corner_index
        corner_values = list(corner_lookup)
        corner_box = ttk.Combobox(replacement_frame, textvariable=corner_var, values=corner_values, state="readonly", width=28)
        corner_box.grid(row=0, column=1, sticky="ew", padx=8, pady=(10, 4))
        corner_var.set(corner_values[0] if corner_values else "")
        ttk.Label(replacement_frame, text="Ready same-division fighter", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        fighter_var = tk.StringVar()
        fighter_box = ttk.Combobox(replacement_frame, textvariable=fighter_var, state="readonly", width=68)
        fighter_box.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        replacement_rows = {}

        def miss_corner_index(selected_name):
            if selected_name in corner_lookup:
                return int(corner_lookup[selected_name])
            fighter = next((item for item, _miss in misses if item.name == selected_name), None)
            if fighter is None:
                return 0
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            ids = list(fight.get("fighter_ids", []) or [])
            if fighter_id and fighter_id in ids:
                return ids.index(fighter_id)
            names_in_fight = list(fight.get("fighters", []) or [])
            return names_in_fight.index(fighter.name) if fighter.name in names_in_fight else 0

        def missed_fighter_for_corner(corner_index):
            ids = list(fight.get("fighter_ids", []) or [])
            wanted_id = str(ids[corner_index] or "") if 0 <= corner_index < len(ids) else ""
            if wanted_id:
                fighter = next(
                    (item for item, _miss in misses if str(getattr(item, "fighter_id", "") or "") == wanted_id),
                    None,
                )
                if fighter is not None:
                    return fighter
            names_in_fight = list(fight.get("fighters", []) or [])
            wanted_name = names_in_fight[corner_index] if 0 <= corner_index < len(names_in_fight) else ""
            return next((item for item, _miss in misses if item.name == wanted_name), None)

        def refresh_replacement_choices(*_args):
            replacement_rows.clear()
            corner_index = miss_corner_index(corner_var.get())
            rows = self.last_minute_replacement_candidates(event, fight, corner_index)
            selected_miss = missed_fighter_for_corner(corner_index)
            title_merit_required = bool(fight.get("title")) and not bool(
                getattr(selected_miss, "is_champion", False)
                or getattr(selected_miss, "champion", False)
                or getattr(selected_miss, "interim_champion", False)
            )
            values = []
            for row in rows:
                title_note = " | Title eligible" if title_merit_required and row.get("title_eligible") else ""
                display = f"{row['name']} | Company {row['company_rank']} | World {row['world_rank']} | {row['record']} | {row['readiness']}{title_note}"
                replacement_rows[display] = row.get("candidate_key") or row.get("fighter_id", "")
                values.append(display)
            fighter_box.configure(values=values)
            fighter_var.set(values[0] if values else "")
            replacement_button.configure(state="normal" if values else "disabled")
            if title_merit_required:
                status = "title-eligible challenger option(s)"
            elif bool(fight.get("title")):
                status = "title replacement option(s)"
            else:
                status = "ready option(s)"
            replacement_status.set(
                f"{len(values)} {status} in the same division." if values else (
                    "No title-eligible same-division replacement is available."
                    if title_merit_required else "No ready same-division replacement is available."
                )
            )

        replacement_status = tk.StringVar(value="Choose a corner to see ready options.")
        ttk.Label(replacement_frame, textvariable=replacement_status, style="Inset.TLabel", wraplength=650).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 8))
        corner_box.bind("<<ComboboxSelected>>", refresh_replacement_choices)
        replacement_button = ttk.Button(replacement_frame, text="Last-Minute Replacement", state="disabled")
        replacement_button.grid(row=3, column=1, sticky="e", padx=8, pady=(4, 10))
        buttons = ttk.Frame(dialog, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=14, pady=(4, 14))

        def choose(action):
            result["action"] = action
            dialog.destroy()

        def choose_replacement():
            selected_id = replacement_rows.get(fighter_var.get())
            if not selected_id:
                return
            corner_index = miss_corner_index(corner_var.get())
            result.update({"action": "replacement", "fighter_id": selected_id, "corner_index": corner_index})
            dialog.destroy()

        replacement_button.configure(command=choose_replacement)
        action_buttons = []
        for label, action in (("Remove Belt", "remove_belt"), ("Rebook Fight", "rebook"), ("Keep Belt", "keep_belt"), ("Cancel Fight", "cancel")):
            button = ttk.Button(buttons, text=label, command=lambda action=action: choose(action))
            button.pack(side="left", padx=3)
            action_buttons.append((button, action))
        for button, action in action_buttons:
            button.bind("<Enter>", lambda _event, action=action: consequence.set(self.title_miss_action_consequence(action, fight, misses)))
            button.bind("<FocusIn>", lambda _event, action=action: consequence.set(self.title_miss_action_consequence(action, fight, misses)))
        replacement_button.bind("<Enter>", lambda _event: consequence.set(self.title_miss_action_consequence("replacement", fight, misses)))
        replacement_button.bind("<FocusIn>", lambda _event: consequence.set(self.title_miss_action_consequence("replacement", fight, misses)))
        ttk.Button(buttons, text="Leave unresolved", command=lambda: choose("awaiting_player")).pack(side="right", padx=3)
        consequence.set("No decision committed. The card stays at the recorded weigh-in boundary until you choose an action.")
        refresh_replacement_choices()
        parent.wait_window(dialog)
        return result

    def title_miss_action_consequence(self, action, fight, misses):
        """Return the honest, pre-commit explanation for an approved choice.

        This helper is deliberately pure presentation data.  It does not
        vacate a belt, queue a booking, inspect today's rankings or consume an
        RNG draw; the existing weigh-in branch remains the only owner of those
        mutations after the player commits a choice.
        """
        action = str(action or "keep_belt")
        names = ", ".join(str(getattr(fighter, "name", "The affected fighter")) for fighter, _miss in (misses or []))
        if action == "remove_belt":
            return (
                f"Remove Belt: record {names or 'the champion'} as vacating before the bout. "
                "The fight can proceed as a title contest; the exact vacant-belt winner/defence outcome is settled by the approved title rules."
            )
        if action == "rebook":
            return (
                "Rebook Fight: stop this bout with no result or defence credit and place the same matchup into the existing rescheduling review. "
                "No new date or payment is invented here; belt handling remains visible for the later booking decision."
            )
        if action == "cancel":
            return (
                "Cancel Fight: close only this bout and its unperformed work. No result, defence credit or replacement booking is created, "
                "and a belt is not stripped unless Remove Belt is chosen."
            )
        if action == "replacement":
            return (
                "Last-Minute Replacement: choose a ready same-division candidate with company/world ranks, then recheck medical, schedule and title eligibility. "
                "Replacing a champion never silently grants or removes the belt; the resulting title status stays explicit."
            )
        return (
            "Keep Belt: keep the title on the line despite the recorded miss. A champion win retains it and an eligible challenger win transfers it; "
            "draw/no-contest follows the existing title-retention rules."
        )

    def build_title_miss_decision_snapshot(self, event, fight, misses):
        """Capture the pre-resolution title decision facts on the fight record.

        This is deliberately a plain-data snapshot.  It gives a saved event,
        replay and later audit the exact corners, miss amounts, title roles and
        available choices that the player saw without serialising a dialog or
        recomputing today's rankings after the fact.
        """
        misses = list(misses or [])
        miss_by_id = {
            str(getattr(fighter, "fighter_id", "") or fighter.name): float(miss_by)
            for fighter, miss_by in misses if fighter is not None
        }
        fighters = list(self.event_fight_fighters(fight))
        while len(fighters) < 2:
            fighters.append(None)
        corners = []
        miss_fine_total = 0
        for index, fighter in enumerate(fighters[:2]):
            if fighter is None:
                corners.append({"corner": index, "fighter_id": "", "fighter": "", "miss_by": 0, "miss_fine": 0, "champion": False, "interim_champion": False, "title_eligible": False})
                continue
            fighter_id = str(getattr(fighter, "fighter_id", "") or fighter.name)
            special_belt_holder = bool(
                str(fight.get("special_belt", "") or "")
                and callable(getattr(self, "fighter_holds_scheduled_title", None))
                and self.fighter_holds_scheduled_title(fighter, fight)
            )
            title_holder = bool(
                getattr(fighter, "champion", False)
                or getattr(fighter, "interim_champion", False)
                or special_belt_holder
            )
            title_eligible = True
            if not title_holder and callable(getattr(self, "ai_title_challenger_is_eligible", None)):
                try:
                    title_eligible = bool(self.ai_title_challenger_is_eligible(fighter))
                except Exception:
                    title_eligible = False
            miss_by = miss_by_id.get(fighter_id, 0)
            miss_fine = round(fighter.purse * (0.2 if miss_by <= 2 else 0.3)) if miss_by > 0 else 0
            miss_fine_total += miss_fine
            corners.append({
                "corner": index,
                "fighter_id": fighter_id,
                "fighter": str(getattr(fighter, "name", "")),
                "gender": str(getattr(fighter, "gender", "")),
                "weight": str(getattr(fighter, "weight", "")),
                "miss_by": miss_by,
                "miss_fine": miss_fine,
                "champion": bool(getattr(fighter, "champion", False)),
                "interim_champion": bool(getattr(fighter, "interim_champion", False)),
                "title_eligible": title_eligible,
                "special_belt_holder": special_belt_holder,
                # Preserve the two distinct pre-decision questions used by
                # the sanction record.  A champion/interim holder may retain
                # a belt; a challenger may win it only when the existing merit
                # check says so.  These are evidence fields, not a new rule.
                "eligible_to_win": bool(title_eligible),
                "eligible_to_retain": title_holder,
            })
        references = list(self.event_fight_participant_references(fight))
        special_belt = str(fight.get("special_belt", "") or "")
        first_fighter = next((item for item in fighters if item is not None), None)
        title_key = (
            f"special:{special_belt}" if special_belt else
            f"division:{getattr(first_fighter, 'gender', '')}:{getattr(first_fighter, 'weight', '')}"
            if first_fighter is not None else ""
        )
        return {
            "schema_version": 1,
            "status": "awaiting_player",
            "event_id": str(event.get("event_id", "") or ""),
            "event_name": str(event.get("name", "") or ""),
            "event_month": int(event.get("month", self.month) or self.month),
            "event_week": int(event.get("week", self.week) or self.week),
            "fighter_references": references,
            "belt_id": str(fight.get("belt_id", fight.get("title_id", "")) or ""),
            "title_key": title_key,
            "corners": corners,
            "choices": list(self.TITLE_MISS_ACTIONS),
            "title_stakes_before": bool(
                fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
            ),
            "divisional_title_before": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))),
            "special_belt_before": str(fight.get("special_belt", "") or ""),
            "miss_fine_total": miss_fine_total,
            "miss_fine_applied": False,
        }

    @staticmethod
    def record_title_miss_decision(fight, action, *, status="resolved", reason="", replacement_id=""):
        """Seal the selected title-miss action without losing the original facts."""
        state = fight.setdefault("title_miss_decision_state", {})
        state.update({
            "status": str(status),
            "action": str(action),
            "reason": str(reason or ""),
            "replacement_id": str(replacement_id or ""),
        })
        return state

    @staticmethod
    def update_title_sanction_snapshot(fight, **updates):
        """Merge a decision update without dropping the original belt scope.

        The weigh-in snapshot is the historical source for belt ID, title
        scope and per-corner eligibility.  Decision branches may add their
        outcome fields, but must not replace that evidence with a narrower
        envelope.
        """
        previous = fight.get("title_sanction_snapshot") if isinstance(fight, dict) else {}
        snapshot = deepcopy(previous) if isinstance(previous, dict) else {}
        snapshot.setdefault("schema_version", 1)
        state = fight.get("title_miss_decision_state") if isinstance(fight, dict) and isinstance(fight.get("title_miss_decision_state"), dict) else {}
        snapshot.setdefault(
            "scheduled_title",
            bool(
                state.get("title_stakes_before", False)
                or fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
            ) if isinstance(fight, dict) else False,
        )
        snapshot.setdefault(
            "belt_id",
            str(
                state.get("belt_id", "")
                or (fight.get("belt_id", fight.get("title_id", "")) if isinstance(fight, dict) else "")
                or ""
            ),
        )
        if not snapshot.get("title_key"):
            saved_title_key = str(state.get("title_key", "") or "")
            if saved_title_key:
                snapshot["title_key"] = saved_title_key
        snapshot.update(updates)
        if isinstance(fight, dict):
            fight["title_sanction_snapshot"] = snapshot
        return snapshot

    def _stored_title_miss_context(self, fight):
        """Read a saved title-miss snapshot without rerunning the weigh-in roll.

        A save can be taken after the official scale evidence is written but
        before the player's modal decision returns.  On reload the snapshot is
        the authority: the pending prompt must use the recorded miss amounts,
        not a fresh random cut.  Terminal states are also recognised so a
        crash after the choice cannot charge or mutate the same corner twice.
        """
        state = fight.get("title_miss_decision_state") if isinstance(fight, dict) else None
        if not isinstance(state, dict):
            return None
        status = str(state.get("status", "") or "")
        if status not in {"awaiting_player", "resolved", "rebooked", "cancelled", "needs_review"}:
            return None
        corners = state.get("corners")
        if not isinstance(corners, list):
            return None
        misses = []
        for corner in corners:
            if not isinstance(corner, dict):
                # A pending decision must be rebuilt from its recorded
                # corners, not from whatever names happen to be on the live
                # fight after a reload.  Malformed corner data therefore
                # fails closed instead of silently substituting a fighter.
                return None
            fighter_id = str(corner.get("fighter_id", "") or "")
            try:
                fighter = self.resolve_fighter(fighter_id) if fighter_id and hasattr(self, "resolve_fighter") else None
            except (LookupError, TypeError, ValueError):
                fighter = None
            if fighter is None and fighter_id and hasattr(self, "get_fighter"):
                try:
                    fighter = self.get_fighter(fighter_id)
                except (LookupError, TypeError, ValueError):
                    fighter = None
            if fighter_id and fighter is None:
                # Validate every recorded identity, including a corner that
                # made weight.  Resolving only missed corners would allow a
                # same-name/current-roster fallback to replace the other
                # participant and change the meaning of the saved decision.
                return None
            try:
                miss_by = float(corner.get("miss_by", 0) or 0)
                if not math.isfinite(miss_by):
                    return None
                miss_by = max(0.0, miss_by)
            except (TypeError, ValueError, OverflowError):
                return None
            if miss_by <= 0:
                continue
            if fighter is None:
                # A pending decision with an unresolvable corner cannot safely
                # continue; callers fail closed and retain the evidence.
                return None
            misses.append((fighter, miss_by))
        if not misses:
            return None
        return deepcopy(state), misses

    def run_weigh_ins(self, event):
        lines = ["", "WEIGH-INS"]
        purse_penalty = 0
        cancelled = []

        def safe_nonnegative_int(value, fallback=0):
            try:
                numeric = float(value)
                if not math.isfinite(numeric):
                    return fallback
                return max(0, int(value or fallback))
            except (TypeError, ValueError, OverflowError):
                return fallback

        for fight in event["fights"]:
            if fight.get("tournament") and "TBA" in fight.get("tournament_entrants", []):
                entrants = list(fight.get("tournament_entrants", []))
                fighter_ids = list(fight.get("fighter_ids", []))
                if len(fighter_ids) != len(entrants):
                    fighter_ids = [
                        getattr(self._resolve_event_fighter(name), "fighter_id", "")
                        if name != "TBA" else ""
                        for name in entrants
                    ]
                known = next(iter(self.event_fight_fighters(fight)), None)
                for index, name in enumerate(entrants):
                    if name != "TBA":
                        continue
                    replacement = self.find_tba_replacement(fight.get("tournament_weight", known.weight), fight.get("tournament_gender", known.gender), known=known, short_notice=True)
                    entrants[index] = replacement.name
                    fighter_ids[index] = replacement.fighter_id
                    lines.append(f"Tournament alternate {replacement.name} entered the field on short notice.")
                fight["tournament_entrants"] = entrants
                fight["fighter_ids"] = fighter_ids
                fight["fighters"] = [entrants[0], entrants[-1]]
            # Fill an outstanding TBA before the scale rather than after it.
            # Weigh-ins ran before the opponent existed, so any bout still
            # holding a TBA slot fell through the len(fighters) < 2 guard below
            # and skipped the scale completely: no weight was recorded for
            # either corner, a miss could not be detected, and a blown cut could
            # never downgrade a title bout to catchweight. resolve_fight_fighters
            # is a no-op once both corners are named, so the later call in
            # prepare_event_result still returns the same pair.
            if not fight.get("tournament") and "TBA" in fight.get("fighters", []):
                if any(name != "TBA" for name in fight.get("fighters", [])):
                    self.resolve_fight_fighters(fight)
            names = [name for name in self.event_fight_participants(fight) if name != "TBA"]
            raw_state = fight.get("title_miss_decision_state") if isinstance(fight.get("title_miss_decision_state"), dict) else None
            raw_status = str((raw_state or {}).get("status", "") or "")
            saved_context = self._stored_title_miss_context(fight)
            saved_state = saved_context[0] if saved_context else None
            saved_status = str((saved_state or raw_state or {}).get("status", "") or "")
            if saved_state is None and raw_state is not None and raw_status in {"resolved", "rebooked", "cancelled", "needs_review"} and fight.get("_weight_miss_decision_applied"):
                # Terminal states do not need a live original corner to be
                # idempotent.  Preserve their evidence and fail closed rather
                # than attempting a new scale for an unresolvable fighter.
                saved_state = deepcopy(raw_state)
            # A choice may have been sealed immediately before a save or
            # process interruption.  Do not run the scale again: the saved
            # sanction and decision already contain the official evidence.
            if saved_state is not None and saved_status in {"resolved", "rebooked", "cancelled", "needs_review"} and fight.get("_weight_miss_decision_applied"):
                for corner in saved_state.get("corners", []):
                    if not isinstance(corner, dict):
                        continue
                    name = str(corner.get("fighter", "The affected fighter") or "The affected fighter")
                    try:
                        miss_by = max(0.0, float(corner.get("miss_by", 0) or 0))
                    except (TypeError, ValueError, OverflowError):
                        miss_by = 0.0
                    result_text = f"missed by {miss_by:g} lb" if miss_by else "made weight"
                    lines.append(f"Recorded weigh-in: {name} {result_text}; no new scale roll.")
                if saved_status in {"rebooked", "cancelled", "needs_review"}:
                    if not isinstance(fight.get("_cancellation"), dict):
                        action = str((saved_state or {}).get("action", "cancel") or "cancel")
                        fight["_cancellation"] = {
                            "reason": "The saved title-miss decision stopped this bout before execution.",
                            "weigh_in": "Recorded title-miss evidence retained.",
                            "resolution": "Return to the saved title-decision/rebooking review." if action == "rebook" else "No replacement booking was created.",
                            "title_decision": action,
                        }
                    cancelled.append(fight)
                continue

            pending_decision = raw_status == "awaiting_player"
            if pending_decision and saved_context is None:
                reason = "The saved title-miss decision could not resolve its recorded corner; the bout was held for review."
                recorded_fine = (raw_state or {}).get("miss_fine_total", 0)
                purse_penalty += safe_nonnegative_int(recorded_fine)
                if isinstance(raw_state, dict):
                    raw_state["miss_fine_applied"] = True
                self.record_title_miss_decision(fight, "needs_review", status="needs_review", reason=reason)
                fight["_weight_miss_decision_applied"] = True
                fight["_cancellation"] = {"reason": reason, "weigh_in": "Recorded title-miss evidence retained.", "resolution": "Review the saved event before resuming."}
                cancelled.append(fight)
                continue
            fighters = [fighter for fighter in self.event_fight_fighters(fight) if fighter in self.roster]
            if len(fighters) < 2:
                if pending_decision:
                    reason = "The saved title-miss decision could not resolve both original corners; the bout was held for review."
                    review_state = saved_state or raw_state
                    if isinstance(review_state, dict) and not bool(review_state.get("miss_fine_applied", False)):
                        recorded_fine = review_state.get("miss_fine_total")
                        if recorded_fine is None:
                            recorded_fine = sum(
                                safe_nonnegative_int(corner.get("miss_fine", 0))
                                for corner in review_state.get("corners", [])
                                if isinstance(corner, dict)
                            )
                        if not recorded_fine and saved_context:
                            recorded_fine = sum(
                                round(getattr(fighter, "purse", 0) * (0.2 if miss_by <= 2 else 0.3))
                                for fighter, miss_by in saved_context[1]
                            )
                        purse_penalty += safe_nonnegative_int(recorded_fine)
                        review_state["miss_fine_applied"] = True
                    self.record_title_miss_decision(fight, "needs_review", status="needs_review", reason=reason)
                    fight["_weight_miss_decision_applied"] = True
                    fight["_cancellation"] = {"reason": reason, "weigh_in": "Recorded title-miss evidence retained.", "resolution": "Review the saved event before resuming."}
                    cancelled.append(fight)
                continue
            # All persisted title-stakes forms share the same player decision
            # boundary.  Older bookings may carry only ``divisional_title``
            # or a named ``special_belt`` rather than the broad ``title``
            # flag; treating those as ordinary bouts would silently skip the
            # recorded title-miss choice even though the snapshot/read model
            # correctly identifies them as title stakes.
            title_stakes = bool(
                fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
            )
            if pending_decision and saved_context:
                decision_snapshot, misses = saved_context
                # The first invocation's purse total is local until event
                # settlement.  If a save/reload interrupted the prompt, carry
                # the recorded one-time fine forward exactly once.
                if not bool(decision_snapshot.get("miss_fine_applied", False)):
                    recorded_fine = decision_snapshot.get("miss_fine_total")
                    if recorded_fine is None:
                        recorded_fine = sum(
                            safe_nonnegative_int(corner.get("miss_fine", 0))
                            for corner in decision_snapshot.get("corners", [])
                            if isinstance(corner, dict)
                        )
                    if not recorded_fine:
                        # Legacy pending snapshots predate the fine fields;
                        # rebuild the same existing purse rule from the
                        # identity-linked missed corners, never from a fresh
                        # scale roll.
                        recorded_fine = sum(
                            round(getattr(fighter, "purse", 0) * (0.2 if miss_by <= 2 else 0.3))
                            for fighter, miss_by in misses
                        )
                    purse_penalty += safe_nonnegative_int(recorded_fine)
                    decision_snapshot["miss_fine_applied"] = True
                for missed, miss_by in misses:
                    lines.append(f"Recorded weigh-in: {missed.name} missed {missed.weight} by {miss_by:g} lb; no new scale roll or duplicate fine.")
            else:
                decision_snapshot = None
                misses = []
                for fighter in fighters:
                    outcome = self.perform_weigh_in(fighter, title_fight=title_stakes, persist=True)
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
                    fighter_ids = list(fight.get("fighter_ids", []))
                    entrant_index = (
                        fighter_ids.index(missed.fighter_id)
                        if len(fighter_ids) == len(entrants) and missed.fighter_id in fighter_ids
                        else entrants.index(missed.name)
                    )
                    entrants[entrant_index] = replacement.name
                    if len(fighter_ids) == len(entrants):
                        fighter_ids[entrant_index] = replacement.fighter_id
                        fight["fighter_ids"] = fighter_ids
                    outcome = self.perform_weigh_in(replacement, title_fight=False, camp_weeks=0, persist=True)
                    lines.append(f"Commission removed {missed.name} after a {miss_by} lb miss; alternate {replacement.name} weighed {outcome['scale_weight']} lb and joined the bracket.")
                entrants = fight.get("tournament_entrants", [])
                fight["fighters"] = [entrants[0], entrants[-1]]
                continue
            double_miss = len(misses) == 2
            # Player title bouts pause for an explicit decision. If a saved
            # snapshot is already awaiting the player, use its recorded miss
            # amounts and do not roll the scale again.
            if misses and title_stakes and not getattr(self, "spectator_mode", False):
                if not pending_decision:
                    decision_snapshot = self.build_title_miss_decision_snapshot(event, fight, misses)
                    fight["title_miss_decision_state"] = decision_snapshot
                decision = self.prompt_title_weight_miss_decision(event, fight, misses) or {"action": "awaiting_player"}
                action = str(decision.get("action", "awaiting_player"))
                if action not in self.TITLE_MISS_ACTIONS:
                    # Closing the prompt, returning an invalid action, or
                    # losing a response must never answer the sporting choice
                    # on the player's behalf.  Keep the recorded weigh-in and
                    # one-time fine, then stop preparation at this persisted
                    # boundary so the prompt can be reopened after reload.
                    reason = (
                        "No title-miss decision was committed; the bout remains "
                        "pending for an explicit player choice."
                    )
                    self.record_title_miss_decision(
                        fight, "awaiting_player", status="awaiting_player", reason=reason,
                    )
                    self.update_title_sanction_snapshot(
                        fight,
                        on_line=False,
                        decision="awaiting_player",
                        review_required=True,
                        missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                    )
                    fight["_title_miss_decision_pending"] = True
                    cancelled.append(fight)
                    lines.append("Title decision remains unresolved; preparation stopped before the bout.")
                    continue
                if action == "remove_belt":
                    missed_champions = [
                        missed for missed, _miss_by in misses
                        if getattr(missed, "champion", False)
                        or getattr(missed, "interim_champion", False)
                        or self.fighter_holds_scheduled_title(missed, fight)
                    ]
                    # Remove Belt has a defined meaning only when a recorded
                    # champion actually missed.  A challenger-only miss has
                    # unresolved sporting consequences in the approved J5
                    # policy; do not silently treat it as a vacancy or let
                    # the title settlement guess which corner should be
                    # stripped.  Preserve the scale/fine evidence and hold
                    # the bout for explicit review instead.
                    if not missed_champions:
                        reason = (
                            "Remove Belt was selected, but no recorded champion missed weight; "
                            "the challenger-only title case needs an approved rule before the bout can proceed."
                        )
                        self.record_title_miss_decision(
                            fight, action, status="needs_review", reason=reason,
                        )
                        self.update_title_sanction_snapshot(
                            fight,
                            on_line=False,
                            decision=action,
                            review_required=True,
                            missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                        )
                        fight["_cancellation"] = {
                            "reason": reason,
                            "weigh_in": "; ".join(
                                f"{missed.name} missed by {miss_by:g} lb"
                                for missed, miss_by in misses
                            ),
                            "resolution": "Review the challenger-only title-miss policy before resuming.",
                            "title_decision": action,
                        }
                        fight["_weight_miss_decision_applied"] = True
                        if isinstance(fight.get("title_miss_decision_state"), dict):
                            fight["title_miss_decision_state"]["miss_fine_applied"] = True
                        cancelled.append(fight)
                        lines.append("Player decision held for review: Remove Belt requires a recorded champion miss.")
                        continue
                    for missed, _miss_by in misses:
                        if self.fighter_holds_scheduled_title(missed, fight) and hasattr(self, "vacate_fighter_belts"):
                            self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
                                missed, self.roster, self.belts, self.interim_belts, self.belt_history,
                                "Player decision after missing weight.",
                            )
                            if fight.get("special_belt"):
                                self.vacate_special_belts_held_by(
                                    missed, "Player decision after missing weight."
                                )
                    fight["title_decision"] = "remove_belt"
                    self.record_title_miss_decision(fight, action, reason="Player chose to vacate the belt before the bout.")
                    self.update_title_sanction_snapshot(
                        fight,
                        on_line=True,
                        vacated_before_bout=True,
                        decision=action,
                        missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                    )
                    lines.append("Player decision: belt removed before the bout; the fight may crown a new champion.")
                    misses = []
                elif action in ("rebook", "cancel"):
                    cancelled.append(fight)
                    weigh_in = "; ".join(f"{fighter.name} missed by {miss_by:g} lb" for fighter, miss_by in misses)
                    resolution = self.queue_cancelled_bout_rebooking(event, fight, names) if action == "rebook" else "No replacement booking was created."
                    self.record_title_miss_decision(fight, action, status="rebooked" if action == "rebook" else "cancelled", reason=resolution)
                    self.update_title_sanction_snapshot(
                        fight,
                        on_line=False,
                        decision=action,
                        missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                    )
                    fight["_cancellation"] = {
                        "reason": "The player stopped the title bout after a weight miss.",
                        "weigh_in": weigh_in,
                        "resolution": resolution,
                        "title_decision": action,
                    }
                    # Seal the decision before leaving this branch.  Rebook
                    # and Cancel are terminal for this scheduled slot; without
                    # the marker a save/reload would fall through to a fresh
                    # weigh-in and could duplicate fines or cancellation work.
                    fight["_weight_miss_decision_applied"] = True
                    lines.append(f"Player decision: {'bout rebooked' if action == 'rebook' else 'bout cancelled'} after the weight miss.")
                    continue
                elif action == "replacement":
                    replaced_corner = int(decision.get("corner_index", 0) or 0)
                    original_replaced_id = str((fight.get("fighter_ids", []) or ["", ""])[replaced_corner] or "")
                    original_replaced_fighter = next(
                        (item[0] for item in misses if str(getattr(item[0], "fighter_id", "") or "") == original_replaced_id),
                        None,
                    )
                    ok, note = self.commit_last_minute_replacement(
                        event, fight, decision.get("fighter_id", ""), replaced_corner,
                    )
                    if ok:
                        replaced_fighter = original_replaced_fighter
                        replacement_ids = list(fight.get("fighter_ids", []) or [])
                        replacement_names = list(fight.get("fighters", []) or [])
                        replacement_reference = (
                            replacement_ids[replaced_corner]
                            if replaced_corner < len(replacement_ids) and replacement_ids[replaced_corner]
                            else replacement_names[replaced_corner]
                            if replaced_corner < len(replacement_names)
                            else ""
                        )
                        # Modern rows resolve by fighter_id.  ID-less legacy
                        # rows retain their name in the event and may use a
                        # unique name-only compatibility fallback; the shared
                        # resolver rejects duplicate names rather than
                        # silently selecting another career.
                        replacement = self._resolve_event_fighter(replacement_reference)
                        if replacement:
                            replacement_outcome = self.perform_weigh_in(replacement, title_fight=True, camp_weeks=0, persist=True)
                            remaining_misses = [item for item in misses if item[0] is not replaced_fighter]
                            if replacement_outcome["made"]:
                                misses = remaining_misses
                            else:
                                replacement_miss = replacement_outcome["miss_by"]
                                replacement_fine = round(replacement.purse * (0.2 if replacement_miss <= 2 else 0.3))
                                purse_penalty += replacement_fine
                                replacement.morale = max(1, replacement.morale - 7)
                                replacement.popularity = max(1, replacement.popularity - 1)
                                lines.append(
                                    f"Replacement {replacement.name} also missed by {replacement_miss} lb; "
                                    f"fine ${replacement_fine:,}; the bout was stopped for review."
                                )
                                misses = remaining_misses + [(replacement, replacement_outcome["miss_by"])]
                            lines.append(f"Player decision: {note} The replacement's title eligibility and weigh-in were checked.")
                            replacement_on_line = bool(title_stakes)
                            if replaced_fighter and self.fighter_holds_scheduled_title(replaced_fighter, fight):
                                fight["title"] = False
                                fight["divisional_title"] = False
                                fight["interim"] = False
                                fight["special_belt"] = ""
                                replacement_on_line = False
                                lines.append("The champion's corner was replaced, so the belt is retained by the absent holder and is not contested tonight.")
                            self.record_title_miss_decision(
                                fight, action, reason=note,
                                replacement_id=decision.get("fighter_id", ""),
                            )
                            self.update_title_sanction_snapshot(
                                fight,
                                on_line=replacement_on_line,
                                decision=action,
                                replacement_id=str(decision.get("fighter_id", "") or ""),
                                missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                            )
                            if not replacement_outcome["made"]:
                                review_reason = (
                                    f"The selected replacement {replacement.name} also missed weight; "
                                    "the bout was held for review rather than downgraded automatically."
                                )
                                cancelled.append(fight)
                                self.record_title_miss_decision(
                                    fight, action, status="needs_review", reason=review_reason,
                                    replacement_id=decision.get("fighter_id", ""),
                                )
                                self.update_title_sanction_snapshot(
                                    fight,
                                    on_line=False,
                                    decision=action,
                                    replacement_id=str(decision.get("fighter_id", "") or ""),
                                    missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                                    replacement_miss_by=replacement_outcome["miss_by"],
                                )
                                fight["_cancellation"] = {
                                    "reason": review_reason,
                                    "weigh_in": f"Replacement {replacement.name} missed by {replacement_outcome['miss_by']} lb.",
                                    "resolution": "Review the saved replacement decision before resuming.",
                                    "title_decision": action,
                                }
                                fight["_weight_miss_decision_applied"] = True
                                if isinstance(fight.get("title_miss_decision_state"), dict):
                                    fight["title_miss_decision_state"]["miss_fine_applied"] = True
                                continue
                        else:
                            note = "The selected replacement could not be resolved; the bout was held for review."
                            lines.append(note)
                            cancelled.append(fight)
                            self.record_title_miss_decision(
                                fight, action, status="needs_review", reason=note,
                                replacement_id=decision.get("fighter_id", ""),
                            )
                            self.update_title_sanction_snapshot(
                                fight,
                                on_line=False,
                                decision=action,
                                replacement_id=str(decision.get("fighter_id", "") or ""),
                                missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                            )
                            fight["_cancellation"] = {
                                "reason": note,
                                "weigh_in": "Recorded title-miss evidence retained.",
                                "resolution": "Review the saved replacement decision before resuming.",
                                "title_decision": action,
                            }
                            fight["_weight_miss_decision_applied"] = True
                            if isinstance(fight.get("title_miss_decision_state"), dict):
                                fight["title_miss_decision_state"]["miss_fine_applied"] = True
                            continue
                    else:
                        note = f"Replacement decision could not be completed: {note} The bout was held for review."
                        lines.append(note)
                        cancelled.append(fight)
                        self.record_title_miss_decision(
                            fight, action, status="needs_review", reason=note,
                            replacement_id=decision.get("fighter_id", ""),
                        )
                        self.update_title_sanction_snapshot(
                            fight,
                            on_line=False,
                            decision=action,
                            replacement_id=str(decision.get("fighter_id", "") or ""),
                            missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                        )
                        fight["_cancellation"] = {
                            "reason": note,
                            "weigh_in": "Recorded title-miss evidence retained.",
                            "resolution": "Review the saved replacement decision before resuming.",
                            "title_decision": action,
                        }
                        fight["_weight_miss_decision_applied"] = True
                        if isinstance(fight.get("title_miss_decision_state"), dict):
                            fight["title_miss_decision_state"]["miss_fine_applied"] = True
                        continue
                else:
                    fight["title_decision"] = "keep_belt"
                    self.record_title_miss_decision(fight, action, reason="Player kept the title on the line despite the recorded miss.")
                    self.update_title_sanction_snapshot(
                        fight,
                        on_line=True,
                        decision=action,
                        champion_miss_waived=True,
                        missed_corners=deepcopy(decision_snapshot.get("corners", [])),
                    )
                    lines.append("Player decision: keep belt; the title remains on the line despite the recorded weight miss.")
                if isinstance(fight.get("title_miss_decision_state"), dict):
                    # Fresh preparation already included the fine in this
                    # invocation's local total; resumed preparation marked it
                    # above. Persist the same fact for idempotent retries.
                    fight["title_miss_decision_state"]["miss_fine_applied"] = True
                fight["_weight_miss_decision_applied"] = True
            double_miss = len(misses) == 2
            severe_double_miss = double_miss and (
                sum(miss_by for _fighter, miss_by in misses) > 8
                or max(miss_by for _fighter, miss_by in misses) > 5
            )
            explicit_keep = fight.get("title_decision") == "keep_belt" and fight.get("_weight_miss_decision_applied")
            # An explicit Keep Belt decision owns the title treatment.  Do not
            # even draw the old commission-cancellation roll in that path: it
            # cannot change the outcome and would make a player choice consume
            # simulation RNG for no mechanical purpose.
            commission_cancels = False if explicit_keep else severe_double_miss and random.random() < 0.35
            if (commission_cancels or any(miss_by > 9 for _fighter, miss_by in misses)) and not explicit_keep:
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
            elif misses and not explicit_keep:
                fight["catchweight"] = True
                fight["title"] = False
                fight["divisional_title"] = False
                fight["interim"] = False
                fight["special_belt"] = ""
                lines.append(f"{' vs '.join(names)} continues as a catchweight non-title bout.")
        return lines, purse_penalty, cancelled

    def simulate_event_tournament(self, event, tournament):
        """Simulate a tournament stage while preserving the normal result pipeline.

        A legacy tournament has no Grand Prix metadata and therefore runs every
        bracket round in one card.  A multi-event Grand Prix supplies a stage
        window and carries only its advancing identities into the next card.
        """
        entrants = self.event_fight_fighters(tournament)
        entrants = sorted(entrants, key=lambda fighter: (self.division_rank_number(fighter) or 99, -fighter.elo_rating, -fighter.overall, fighter.name))
        # Tournament preparation is private in-memory state. Object identity
        # keeps duplicate display names from sharing one fatigue snapshot.
        starting_fatigue = {id(fighter): fighter.fatigue for fighter in entrants}
        current = entrants
        grand_prix = tournament.get("grand_prix") if isinstance(tournament.get("grand_prix"), dict) else {}
        is_grand_prix = bool(grand_prix or tournament.get("grand_prix_series_id"))
        stage_start = int(tournament.get("grand_prix_stage_start", 0) or 0)
        stage_end = tournament.get("grand_prix_stage_end")
        if stage_end is None:
            stage_end = self.grand_prix_round_count(len(entrants)) if is_grand_prix and hasattr(self, "grand_prix_round_count") else 0
        stage_end = int(stage_end or 0)
        rounds_to_run = max(1, stage_end - stage_start) if is_grand_prix else None
        rounds_run = 0
        total_stage_count = int(grand_prix.get("stage_count", self.grand_prix_round_count(len(entrants)) if hasattr(self, "grand_prix_round_count") else 0) or 0)
        stages = []
        results = []
        award_pool = []
        fight_logs = []
        total_hype = total_build = total_excitement = total_cost = total_contract_cost = 0
        while len(current) > 1 and (rounds_to_run is None or rounds_run < rounds_to_run):
            stage = {8: "QUARTERFINALS", 4: "SEMIFINALS", 2: "FINAL"}.get(len(current), f"ROUND OF {len(current)}")
            stage_number = stage_start + rounds_run + 1
            pairings = list(zip(current[:len(current) // 2], reversed(current[len(current) // 2:])))
            winners = []
            stage_matches = []
            for a, b in pairings:
                is_final = len(current) == 2
                series_final = not is_grand_prix or (total_stage_count and stage_number >= total_stage_count)
                fight = {
                    "fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id], "title": bool(is_final and series_final and tournament.get("title")),
                    "divisional_title": bool(is_final and series_final and tournament.get("divisional_title", tournament.get("title") and not tournament.get("special_belt"))),
                    "interim": bool(is_final and series_final and tournament.get("interim")), "main": bool(is_final and series_final and tournament.get("main")),
                    "special_belt": tournament.get("special_belt", "") if is_final and series_final else "",
                    "tier": tournament.get("tier", "Main Card"), "tournament": True,
                    "tournament_stage": stage, "tournament_stage_number": stage_number, "tournament_name": tournament.get("tournament_name", "MMA Grand Prix"),
                    "grand_prix_series_id": tournament.get("grand_prix_series_id", grand_prix.get("series_id", "")),
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
                decider = False
                if method == "Draw":
                    # Tournament draws are not allowed to eliminate a seed.
                    # The decider is one extra 15-minute round and is scoped to
                    # tournament execution so ordinary fights retain normal
                    # draw rules.
                    decider_fight = dict(fight)
                    decider_fight["tournament_decider"] = True
                    decider_fight["tournament_decider_minutes"] = self.GRAND_PRIX_DECIDER_MINUTES if hasattr(self, "GRAND_PRIX_DECIDER_MINUTES") else 15
                    winner, loser, method, round_no, decider_commentary = self.simulate_fight(a, b, decider_fight)
                    commentary = list(commentary) + ["Tournament draw detected; a 15-minute decider round was ordered."] + list(decider_commentary)
                    decider = True
                    if method == "Draw":
                        # The decider engine's scoped judge rule should always
                        # produce a winner. Keep a deterministic fail-closed
                        # guard for legacy/custom engines that still return a
                        # draw after the decider.
                        winner = max((a, b), key=lambda fighter: (fighter.overall, fighter.fight_iq, fighter.cardio, fighter.fighter_id))
                        loser = b if winner is a else a
                        method = "Decision"
                        round_no = 1
                        commentary.append(f"Decider judges selected {winner.name} after the full 15 minutes.")
                if decider:
                    fight["tournament_decider"] = {
                        "minutes": 15,
                        "method": method,
                        "winner_id": getattr(winner, "fighter_id", "") if winner else "",
                        "judges_decided": method == "Decision",
                    }
                official_winner = method not in ("Draw", "No Contest")
                advancing = winner if official_winner else max((a, b), key=lambda fighter: (fighter.elo_rating, fighter.overall, fighter.fight_iq))
                if not official_winner:
                    winner, loser = a, b
                    commentary.append(f"The official result remains {method}. Tournament tiebreak criteria advance {advancing.name}; no fight win or loss is awarded.")
                fight["advancing_id"] = advancing.fighter_id
                fight["_scorecards"] = self.scorecard_summary_from_lines(commentary)
                # A finalist can fight several times before finish_event commits
                # the career results. Preserve each bout's own box score so a
                # later round cannot overwrite the earlier career telemetry.
                fight["_fighter_stats"] = {
                    getattr(a, "fighter_id", "") or a.name: dict(getattr(a, "last_fight_stats", {}) or {}),
                    getattr(b, "fighter_id", "") or b.name: dict(getattr(b, "last_fight_stats", {}) or {}),
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
                result_text = (f"{winner.name} def. {loser.name} by {method}, R{round_no}" if official_winner
                               else f"{a.name} vs {b.name}: {method}, R{round_no}")
                lines.append(f"Result: {result_text} | Fight excitement {excitement} | {advancing.name} advances")
                results.append((winner, loser, fight, method))
                award_pool.append({"winner": winner.name if official_winner else "", "winner_id": winner.fighter_id if official_winner else "", "loser": loser.name if official_winner else "", "fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id], "method": method, "excitement": excitement, "round": round_no, "fight": f"{a.name} vs {b.name}"})
                fight_logs.append({
                    "heading": lines[0], "lines": lines, "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                    "winner": winner.name if official_winner else "", "winner_id": winner.fighter_id if official_winner else "", "draw": method == "Draw", "no_contest": method == "No Contest",
                    "advancing": advancing.name, "advancing_id": advancing.fighter_id,
                    "a_record": a.record, "b_record": b.record, "a_rating": a_rating, "b_rating": b_rating, "weight": a.weight,
                    "label": label, "title": bool(fight.get("title", False)), "divisional_title": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))), "interim": bool(fight.get("interim", False)), "special_belt": str(fight.get("special_belt", "") or ""), "result": result_text, "excitement": excitement,
                    "a_title_status": a_title_status, "b_title_status": b_title_status,
                    "tournament_stage": stage, "tournament_stage_number": stage_number, "tournament_name": tournament.get("tournament_name", "MMA Grand Prix"),
                    "tournament_decider": deepcopy(fight.get("tournament_decider", {})),
                    "a_start_gas": a_start_gas, "b_start_gas": b_start_gas,
                    "scorecards": fight["_scorecards"],
                    "commentary_personality": self.commentary_personality(),
                    "round_analysis": deepcopy(getattr(self, "_last_fight_result", None).metrics.get("round_analysis", []) if getattr(self, "_last_fight_result", None) else []),
                })
                stage_matches.append({"a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                                      "winner": winner.name if official_winner else "", "winner_id": winner.fighter_id if official_winner else "",
                                      "advancing": advancing.name, "advancing_id": advancing.fighter_id,
                                      "method": method, "round": round_no, "summary": result_text})
                winners.append(advancing)
                total_hype += hype
                total_build += build
                total_excitement += excitement
                total_contract_cost += a.purse + b.purse
                total_cost += self.player_bout_purse_cost(fight, a, b)
            stages.append({"name": stage, "matches": stage_matches})
            current = winners
            rounds_run += 1
        completed = len(current) == 1 and (rounds_to_run is None or rounds_run >= rounds_to_run)
        champion = current[0] if completed and current else None
        bracket = {
            "title": tournament.get("tournament_name", "MMA Grand Prix"),
            # Keep the original display list for legacy readers, but also
            # retain the identity-safe seed order.  The tournament hub uses
            # these IDs when a name is duplicated or a fighter later changes
            # companies; no current roster lookup is required to read an old
            # edition.
            "entrants": [fighter.name for fighter in entrants],
            "entrant_ids": [getattr(fighter, "fighter_id", "") for fighter in entrants],
            "seeds": [
                {
                    "seed": index,
                    "fighter_id": getattr(fighter, "fighter_id", ""),
                    "name": fighter.name,
                    "rank": self.division_rank_number(fighter),
                }
                for index, fighter in enumerate(entrants, 1)
            ],
            "weight": getattr(entrants[0], "weight", "") if entrants else tournament.get("weight", ""),
            "gender": getattr(entrants[0], "gender", "") if entrants else tournament.get("gender", ""),
            "series_id": str(tournament.get("grand_prix_series_id", tournament.get("tournament_series_id", tournament.get("series_id", grand_prix.get("series_id", "")))) or ""),
            "stages": stages, "champion": champion.name if champion else "", "champion_id": champion.fighter_id if champion else "",
            "advancing_ids": [fighter.fighter_id for fighter in current],
            "stage_start": stage_start, "stage_end": stage_start + rounds_run,
            "stage_number": stage_start + rounds_run, "event_index": int(tournament.get("grand_prix_event_index", 0) or 0),
            "event_count": int(grand_prix.get("event_count", 1) or 1), "completed": bool(completed),
            "title_fight": bool(tournament.get("title")) if completed else False, "final_decisive": bool(completed),
        }
        # Later rounds need real cumulative fatigue while being simulated, but
        # preparation happens before the viewer is completed. Restore the live
        # world here; finish_event applies every bout in order exactly once.
        for fighter in entrants:
            fighter.fatigue = starting_fatigue[id(fighter)]
        return {
            "results": results, "award_pool": award_pool, "fight_logs": fight_logs,
            "hype": total_hype, "build": total_build, "excitement": total_excitement,
            "cost": total_cost, "contracted_cost": total_contract_cost, "bracket": bracket,
        }

    def open_event_tournament_bracket(self, package, parent=None):
        """Open a compact, readable bracket for a live or completed event."""
        brackets = package.get("tournament_brackets", []) if isinstance(package, dict) else []
        if not brackets:
            notice = getattr(self, "_results_status_notice", None)
            if callable(notice):
                notice("This event has no retained tournament bracket to open.", warning=True)
            else:
                messagebox.showinfo("Tournament Bracket", "This event has no tournament bracket.", parent=parent or self.root)
            return
        window = self.create_managed_window(parent=parent or self.root)
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
            ttk.Label(tab, text=f"Field: {len(bracket.get('entrants', []))} fighters" + (" | Title bout in the final" if bracket.get("title_fight") else "") + (" | Bracket decided by advancement; final had no winner" if bracket.get("final_decisive") is False else ""), style="Panel.TLabel", anchor="center").pack(fill="x", pady=(0, 8))
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
                    tree.insert("", "end", values=(stage.get("name", "ROUND"), bout_no, matchup, match.get("advancing", match.get("winner", "TBD")), result))
            entrants = "Seeded field: " + "  |  ".join(bracket.get("entrants", []))
            ttk.Label(tab, text=entrants, style="Panel.TLabel", wraplength=830, justify="left").pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=8, pady=(0, 8))

    def queue_cancelled_bout_rebooking(self, event, fight, names):
        """Queue a cancelled bout without discarding its booking contract.

        Older callers pass only display names and a small fight dictionary.  A
        title-miss decision, however, has stable participant IDs and sanction
        terms that must survive the move to a future card.  Capture those facts
        once at the cancellation boundary; the calendar worker can then resolve
        the same fighters by ID and restore the title flags when a suitable
        existing card is found.  The payload is plain data so it is safe to
        persist and retry after a save/reload.
        """
        self.pending_rebookings = getattr(self, "pending_rebookings", [])
        event = event if isinstance(event, dict) else {}
        fight = fight if isinstance(fight, dict) else {}
        display_names = list(names or fight.get("fighters", []) or [])
        references = []
        try:
            references = list(self.event_fight_participant_references(fight))
        except Exception:
            references = list(fight.get("fighter_ids", []) or [])
        if len(references) != len(display_names):
            references = list(display_names)
        source_event = str(event.get("event_id", "") or event.get("name", "Event"))
        source_fight = str(
            fight.get("fight_id", "") or fight.get("bout_id", "")
            or fight.get("booking_id", "") or ""
        )
        identity_payload = {
            "event": source_event,
            "fight": source_fight,
            "fighters": references,
            "names": display_names,
            "tier": str(fight.get("tier", "Main Card") or "Main Card"),
            "title": bool(fight.get("title", False)),
            "special_belt": str(fight.get("special_belt", "") or ""),
        }
        rebooking_id = str(fight.get("rebooking_id", "") or "").strip()
        if not rebooking_id:
            digest = hashlib.sha1(
                json.dumps(identity_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()[:16]
            rebooking_id = f"rebook:{digest}"
        existing = next(
            (row for row in self.pending_rebookings
             if isinstance(row, dict) and str(row.get("rebooking_id", "")) == rebooking_id),
            None,
        )
        if existing is None:
            # Keep the sanction contract and presentation metadata, but never
            # carry the old title-miss decision into the new event: the
            # rescheduled card receives a fresh official weigh-in and, if
            # needed, a fresh player decision.  The original evidence remains
            # on the cancelled event/archive.
            snapshot_keys = (
                "title", "divisional_title", "interim", "special_belt", "main",
                "tier", "region", "city", "weight", "gender", "catchweight",
                "tournament", "tournament_name", "fight_plans", "championship",
            )
            fight_snapshot = {}
            for key in snapshot_keys:
                if key not in fight:
                    continue
                value = fight.get(key)
                if key == "fight_plans" and isinstance(value, dict):
                    value = deepcopy(value)
                fight_snapshot[key] = value
            existing = {
                "rebooking_id": rebooking_id,
                "fighters": list(display_names),
                "fighter_ids": list(references),
                "tier": fight_snapshot.get("tier", "Main Card"),
                "source_event": str(event.get("name", "Event") or "Event"),
                "source_event_id": str(event.get("event_id", "") or ""),
                "source_fight_id": source_fight,
                "queued_month": int(getattr(self, "month", 0) or 0),
                "queued_week": int(getattr(self, "week", 0) or 0),
                "fight_snapshot": fight_snapshot,
                "source_title_miss": deepcopy(fight.get("title_miss_decision_state", {})),
                "status": "queued",
            }
            self.pending_rebookings.append(existing)
        outcomes = self.process_pending_rebookings()
        if outcomes:
            return outcomes[0]
        if existing.get("status") == "queued":
            return "The promotion will review the matchup after the event."
        return str(existing.get("outcome", "The promotion will review the matchup after the event."))

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
            fighters = [self._resolve_event_fighter(reference) for reference in references]
            if len(fighters) != 2 or any(fighter is None for fighter in fighters):
                raise LookupError("Fight corner identity could not be resolved unambiguously")
            return fighters
        known_index = next(index for index, name in enumerate(fight["fighters"]) if name != "TBA")
        fighter_ids = list(fight.get("fighter_ids", []))
        known_reference = fighter_ids[known_index] if len(fighter_ids) > known_index and fighter_ids[known_index] else fight["fighters"][known_index]
        known = self._resolve_event_fighter(known_reference)
        if known is None:
            raise LookupError("Known fight corner identity could not be resolved unambiguously")
        replacement = self.find_tba_replacement(fight.get("tba_weight", known.weight), fight.get("tba_gender", known.gender), known=known, short_notice=True)
        fight["fighters"] = [known.name, replacement.name]
        fight["fighter_ids"] = [getattr(known, "fighter_id", ""), getattr(replacement, "fighter_id", "")]
        fight.setdefault("fight_plans", {})[getattr(replacement, "fighter_id", "")] = "Balanced"
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
            source = "free agent"
        else:
            replacement = self.create_generated_fighter(5, 35, 38, 78, weight=weight, gender=gender)
            replacement.weight = weight
            replacement.gender = gender
            self.avoid_name_collision(replacement, self.active_fighter_names())
            source = "regional short-notice signing"
        # Capture the company entry before the free-agent/temporary-fighter
        # roster move.  This is the durable boundary used by the profile
        # timeline; the narrative hook below must not append it again.
        membership_recorded = False
        membership = getattr(self, "record_membership_event", None)
        if callable(membership):
            membership(
                replacement, "join", company_name=self.player_company_name,
                reason="Automatic TBA replacement",
                source_transaction=f"automatic-tba-replacement:{getattr(replacement, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
            )
            membership_recorded = True
        if source == "free agent":
            self.free_agents.remove(replacement)
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
        # Automatic TBA fills use the same durable membership boundary as the
        # explicit replacement picker; this keeps short-notice entrants
        # visible in company history and ensures their later one-fight exit
        # closes a real interval.
        if hasattr(self, "record_contract_signing"):
            self.record_contract_signing(
                replacement, self.player_company_name,
                source="Automatic TBA replacement",
                record_membership=not membership_recorded,
            )
        elif not membership_recorded:
            membership = getattr(self, "record_membership_event", None)
            if callable(membership):
                membership(
                    replacement, "join", company_name=self.player_company_name,
                    reason="Automatic TBA replacement",
                    source_transaction=f"automatic-tba-replacement:{getattr(replacement, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                )
        self.event_log.insert(0, f"TBA filled by {replacement.name} ({source}) at ${replacement.purse:,} for one fight.")
        return replacement

    def tournament_alternate_candidates(self, event, fight):
        """Return a read-only ranked pool for tournament alternate review."""
        event = event or {}
        fight = fight or {}
        weight = str(fight.get("tournament_weight", fight.get("weight", "")) or "")
        gender = str(fight.get("tournament_gender", fight.get("gender", "")) or "")
        if not weight or not gender:
            return []
        current_ids = {str(value) for value in fight.get("fighter_ids", []) or [] if value and value != "TBA"}
        current_names = {str(value) for value in fight.get("tournament_entrants", fight.get("fighters", [])) or [] if value and value != "TBA"}
        busy_ids, busy_names = set(), set()
        for other_event in getattr(self, "scheduled_events", []) or []:
            for other_fight in other_event.get("fights", []) or []:
                if other_event is event and other_fight is fight:
                    continue
                busy_ids.update(str(value) for value in other_fight.get("fighter_ids", []) or [] if value and value != "TBA")
                busy_names.update(str(value) for value in self.event_fight_participant_references(other_fight) if value and value != "TBA")
        for other_fight in getattr(self, "booked", []) or []:
            if other_fight is fight:
                continue
            busy_ids.update(str(value) for value in other_fight.get("fighter_ids", []) or [] if value)
            busy_names.update(str(value) for value in self.event_fight_participant_references(other_fight) if value and value != "TBA")
        pool = list(getattr(self, "free_agents", []) or []) + list(getattr(self, "roster", []) or [])
        seen, eligible = set(), []
        target_month = event.get("month", getattr(self, "month", 1))
        target_week = event.get("week", getattr(self, "week", 1))
        for fighter in pool:
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            identity = fighter_id or f"legacy:{getattr(fighter, 'name', '')}:{getattr(fighter, 'gender', '')}:{getattr(fighter, 'weight', '')}"
            if identity in seen:
                continue
            seen.add(identity)
            if fighter.weight != weight or fighter.gender != gender:
                continue
            if fighter_id in current_ids or fighter.name in current_names or fighter_id in busy_ids or fighter.name in busy_names:
                continue
            status_fn = getattr(self, "fighter_booking_status", None)
            status = status_fn(fighter, target_month, target_week) if callable(status_fn) else ("Unavailable" if getattr(fighter, "injured", False) else "Ready")
            if status == "Ready":
                company = self.fighter_company_for_profile(fighter) if hasattr(self, "fighter_company_for_profile") else ("Free Agent" if fighter in getattr(self, "free_agents", []) else getattr(self, "player_company_name", "Player Company"))
                eligible.append((fighter, company))
        divisions = []
        divisions.extend(("Free Agent", fighter) for fighter in getattr(self, "free_agents", []) or [])
        divisions.extend((getattr(self, "player_company_name", "Player Company"), fighter) for fighter in getattr(self, "roster", []) or [])
        for promotion in getattr(self, "promotions", []) or []:
            divisions.extend((promotion.name, fighter) for fighter in getattr(promotion, "roster", []) or [])
        division_rows = [(company, fighter) for company, fighter in divisions if fighter.gender == gender and fighter.weight == weight]

        official_rank_value = getattr(self, "rank_value", None)

        def rank_value(fighter):
            if callable(official_rank_value):
                try:
                    return official_rank_value(fighter)
                except Exception:
                    pass
            try:
                return float(getattr(fighter, "elo_rating", 0) or 0) * 0.65 + float(getattr(fighter, "overall", 0) or 0) * 0.35
            except (TypeError, ValueError):
                return 0.0

        ordered_world = sorted((fighter for _company, fighter in division_rows), key=rank_value, reverse=True)
        rows = []
        for fighter, company in eligible:
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            company_rows = sorted((item for owner, item in division_rows if owner == company), key=rank_value, reverse=True)
            company_position = next((index for index, item in enumerate(company_rows, 1) if item is fighter or getattr(item, "fighter_id", "") == getattr(fighter, "fighter_id", "")), None)
            world_position = next((index for index, item in enumerate(ordered_world, 1) if item is fighter or getattr(item, "fighter_id", "") == getattr(fighter, "fighter_id", "")), None)
            rows.append({
                "fighter": fighter, "fighter_id": fighter_id, "name": fighter.name,
                "company": company, "company_rank": "C" if getattr(fighter, "champion", False) else (f"#{company_position}" if company_position else "-"),
                "world_rank": "C" if getattr(fighter, "champion", False) else (f"#{world_position}" if world_position else "-"),
                "weight": fighter.weight, "gender": fighter.gender, "record": fighter.record,
                "readiness": "Ready", "status": "Ready",
            })

        def rank_number(value):
            if value == "C":
                return 0
            try:
                return int(str(value).lstrip("#"))
            except (TypeError, ValueError):
                return 999

        rows.sort(key=lambda row: (rank_number(row["company_rank"]), rank_number(row["world_rank"]), row["name"].casefold(), row["fighter_id"]))
        return rows

    def fighter_holds_scheduled_title(self, fighter, fight):
        """Return whether a saved corner is the holder whose belt is protected.

        Standard and interim titles expose holder flags on the fighter. Named
        special belts instead use the belt envelope, so resolve that holder by
        stable ID first and use a unique-name fallback only for legacy rows.
        """
        if fighter is None or not isinstance(fight, dict):
            return False
        if getattr(fighter, "champion", False) or getattr(fighter, "interim_champion", False):
            return True
        special_name = str(fight.get("special_belt", "") or "")
        if not special_name:
            return False
        belts = getattr(self, "special_belts", {})
        belt = belts.get(special_name) if isinstance(belts, dict) else None
        if not isinstance(belt, dict):
            return False
        holder_id = str(belt.get("holder_id", "") or "")
        fighter_id = str(getattr(fighter, "fighter_id", "") or "")
        if holder_id:
            return bool(fighter_id and fighter_id == holder_id)
        holder_name = str(belt.get("holder", "") or "")
        fighter_name = str(getattr(fighter, "name", "") or "")
        if not holder_name or holder_name != fighter_name:
            return False
        all_fighters = getattr(self, "all_fighter_objects", None)
        try:
            population = list(all_fighters()) if callable(all_fighters) else list(getattr(self, "roster", []) or [])
        except (TypeError, ValueError, AttributeError):
            population = list(getattr(self, "roster", []) or [])
        matches = [row for row in population if str(getattr(row, "name", "") or "") == holder_name]
        return len(matches) == 1 and matches[0] is fighter

    def last_minute_replacement_candidates(self, event, fight, corner_index=0):
        """Return ready, same-division candidates for an explicit replacement.

        This is a read-only adapter for the booked-card editor.  It deliberately
        considers both free agents and the player's unbooked roster, while
        excluding fighters committed to another card.  Ranking labels are
        snapshots for presentation only; choosing a row never changes rankings.
        """
        event = event or {}
        fight = fight or {}
        named = self.event_fight_fighters(fight)
        anchor = named[0] if named else None
        weight = fight.get("tba_weight") or getattr(anchor, "weight", "")
        gender = fight.get("tba_gender") or getattr(anchor, "gender", "")
        if not weight or not gender:
            return []
        try:
            corner_index = int(corner_index)
        except (TypeError, ValueError):
            corner_index = 0
        replacing = named[corner_index] if 0 <= corner_index < len(named) else None
        # A title replacement for a non-champion corner must meet the same
        # sporting merit rule as any other challenger.  Replacing a champion
        # removes that corner from the title contest later in the existing
        # weigh-in owner, so challenger merit is not silently applied to a
        # non-title bout.  If the live title-eligibility owner is unavailable,
        # fail closed instead of presenting an unqualified candidate as Ready.
        title_stakes = bool(
            fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
        )
        title_requires_merit = title_stakes and not bool(
            getattr(replacing, "champion", False) or getattr(replacing, "interim_champion", False)
        )
        title_eligibility_fn = getattr(self, "ai_title_challenger_is_eligible", None)
        if title_requires_merit and not callable(title_eligibility_fn):
            return []
        current_ids = {
            str(value) for value in fight.get("fighter_ids", []) if value and value != "TBA"
        }
        current_names = {
            str(value) for value in fight.get("fighters", []) if value and value != "TBA"
        }
        busy_ids, busy_names = set(), set()
        for other_event in getattr(self, "scheduled_events", []) or []:
            for other_fight in other_event.get("fights", []) or []:
                if other_event is event and other_fight is fight:
                    continue
                for value in other_fight.get("fighter_ids", []) or []:
                    if value and value != "TBA":
                        busy_ids.add(str(value))
                for value in self.event_fight_participant_references(other_fight):
                    if value and value != "TBA":
                        busy_names.add(str(value))
        for other_fight in getattr(self, "booked", []) or []:
            if other_fight is fight:
                continue
            for value in other_fight.get("fighter_ids", []) or []:
                if value:
                    busy_ids.add(str(value))
            for value in self.event_fight_participant_references(other_fight):
                if value and value != "TBA":
                    busy_names.add(str(value))
        pool = list(getattr(self, "free_agents", []) or []) + list(getattr(self, "roster", []) or [])
        identity_counts = {}
        rows = []
        for fighter in pool:
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            if fighter_id:
                base_identity = f"id:{fighter_id}"
            else:
                # Imported legacy fighters can lack a durable ID.  Keep every
                # qualifying row visible using a deterministic fingerprint of
                # retained facts, then suffix exact duplicate fingerprints in
                # source order.  Object identity is intentionally excluded so
                # refresh/reload cannot retarget a different career.
                legacy_payload = {
                    "name": str(getattr(fighter, "name", "") or ""),
                    "gender": str(getattr(fighter, "gender", "") or ""),
                    "weight": str(getattr(fighter, "weight", "") or ""),
                    "age": str(getattr(fighter, "age", "") or ""),
                    "record_w": str(getattr(fighter, "record_w", "") or ""),
                    "record_l": str(getattr(fighter, "record_l", "") or ""),
                    "record_d": str(getattr(fighter, "record_d", "") or ""),
                    "overall": str(getattr(fighter, "overall", "") or ""),
                    "popularity": str(getattr(fighter, "popularity", "") or ""),
                }
                fingerprint = hashlib.sha1(
                    json.dumps(legacy_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
                ).hexdigest()[:20]
                base_identity = f"legacy:{fingerprint}"
            identity_counts[base_identity] = identity_counts.get(base_identity, 0) + 1
            occurrence = identity_counts[base_identity]
            identity = base_identity if occurrence == 1 else f"{base_identity}#{occurrence}"
            if fighter.weight != weight or fighter.gender != gender:
                continue
            if fighter_id in current_ids or fighter.name in current_names:
                continue
            if fighter_id in busy_ids or fighter.name in busy_names:
                continue
            if self.fighter_booking_status(fighter, event.get("month", self.month), event.get("week", self.week)) != "Ready":
                continue
            title_eligible = True
            if title_requires_merit:
                try:
                    title_eligible = bool(title_eligibility_fn(fighter))
                except Exception:
                    title_eligible = False
                if not title_eligible:
                    continue
            company = self.fighter_company_for_profile(fighter) if hasattr(self, "fighter_company_for_profile") else "Free Agent"
            # Do not reuse the Rankings page's active UI filters here: a
            # player looking at (for example) Women's rankings must still see
            # a male replacement's actual company/world position.
            rank_rows = []
            rank_rows.extend((getattr(self, "player_company_name", "Player Company"), item) for item in getattr(self, "roster", []) or [])
            rank_rows.extend(("Free Agent", item) for item in getattr(self, "free_agents", []) or [])
            for promotion in getattr(self, "promotions", []) or []:
                rank_rows.extend((promotion.name, item) for item in getattr(promotion, "roster", []) or [])
            division_rows = [(employer, item) for employer, item in rank_rows if item.gender == gender and item.weight == weight]
            company_rows = [item for employer, item in division_rows if employer == company]
            # A free agent has no rank inside the player's promotion. Never
            # turn the free-agent pool into a fictional company leaderboard;
            # the world rank remains useful while the company rank is
            # explicitly unranked until the contract is signed.
            if company == "Free Agent":
                company_rank = "-"
            elif getattr(fighter, "champion", False):
                company_rank = "C"
            else:
                ordered_company = sorted((item for item in company_rows if not item.champion), key=self.rank_value, reverse=True) if hasattr(self, "rank_value") else []
                company_rank = next((f"#{position}" for position, item in enumerate(ordered_company, 1) if item is fighter or getattr(item, "fighter_id", "") == fighter_id), "-")
            ordered_world = sorted((item for _employer, item in division_rows), key=self.rank_value, reverse=True) if hasattr(self, "rank_value") else []
            world_rank = next((f"#{position}" for position, item in enumerate(ordered_world, 1) if item is fighter or getattr(item, "fighter_id", "") == fighter_id), "-")
            if not hasattr(self, "rank_value") and hasattr(self, "rank_label_for_fighter"):
                company_rank = (
                    self.rank_label_for_fighter(fighter, company, world=False)
                    if company != "Free Agent" else "-"
                )
                world_rank = self.rank_label_for_fighter(fighter, company, world=True)
            rows.append({
                "fighter": fighter,
                "fighter_id": fighter_id,
                "candidate_key": identity,
                "name": fighter.name,
                "weight": fighter.weight,
                "gender": fighter.gender,
                "company": company,
                "company_rank": company_rank,
                "world_rank": world_rank,
                "record": fighter.record,
                "readiness": self.fighter_fatigue_label(fighter) if hasattr(self, "fighter_fatigue_label") else "Ready",
                "title_eligible": title_eligible,
                "status": "Ready",
            })

        def rank_number(value):
            if value == "C":
                return 0
            try:
                return int(str(value).lstrip("#"))
            except (TypeError, ValueError):
                return 999

        rows.sort(key=lambda row: (rank_number(row["company_rank"]), rank_number(row["world_rank"]), row["name"].casefold(), row["fighter_id"]))
        return rows

    def commit_last_minute_replacement(self, event, fight, replacement_id, corner_index=0):
        """Commit one explicit short-notice replacement on an unresolved card.

        The affected slot is the only part of the booking changed.  The removed
        fighter and pre-replacement ranking evidence are retained on the fight
        for history; the unaffected corner's preparation is not rerun.
        """
        if not isinstance(fight, dict) or fight.get("tournament"):
            return False, "Tournament entrants use their existing alternate flow."
        if hasattr(self, "ensure_foundation_ids"):
            self.ensure_foundation_ids()
        try:
            corner_index = int(corner_index)
        except (TypeError, ValueError):
            return False, "Choose a valid corner."
        if corner_index not in (0, 1):
            return False, "Choose a valid corner."
        candidates = self.last_minute_replacement_candidates(event, fight, corner_index)
        replacement_key = str(replacement_id or "")
        candidate = next(
            (row["fighter"] for row in candidates
             if str(row.get("fighter_id", "") or "") == replacement_key
             or str(row.get("candidate_key", "") or "") == replacement_key),
            None,
        )
        if candidate is None:
            return False, "That fighter is no longer available for this card. Refresh the replacement list."
        candidate_row = next(
            (row for row in candidates if row.get("fighter") is candidate),
            {},
        )
        # ``candidate_key`` is durable for the lifetime of an ID-less legacy
        # row (and is disambiguated with a deterministic suffix for exact
        # duplicates).  Keep it alongside the modern fighter_id so replacement
        # history and retry receipts do not lose which legacy career was
        # selected after the UI row is rebuilt.
        candidate_reference = str(
            candidate_row.get("candidate_key", "")
            or replacement_key
            or getattr(candidate, "fighter_id", "")
            or candidate.name
        )
        fighter_ids = list(fight.get("fighter_ids", []) or [])
        names = list(fight.get("fighters", []) or [])
        while len(names) < 2:
            names.append("TBA")
        while len(fighter_ids) < 2:
            fighter_ids.append("")
        old_id = str(fighter_ids[corner_index] or "")
        old_name = str(names[corner_index] or "TBA")
        replaced = self.resolve_fighter(old_id or old_name) if old_name != "TBA" else None
        old_reference = old_id
        if not old_reference and replaced is not None:
            old_reference = str(getattr(replaced, "fighter_id", "") or "")
        if not old_reference:
            old_reference = old_name
        title_eligibility_fn = getattr(self, "ai_title_challenger_is_eligible", None)
        title_stakes = bool(
            fight.get("title") or fight.get("divisional_title") or fight.get("special_belt")
        )
        if (title_stakes and not bool(getattr(replaced, "champion", False) or getattr(replaced, "interim_champion", False))
                and callable(title_eligibility_fn)
                and not title_eligibility_fn(candidate)):
            return False, f"{candidate.name} does not meet the current title-challenger merit rule."
        candidate_identity = candidate_reference
        operation_key = f"replacement:{event.get('event_id', 'unassigned-event')}:{old_reference}:{corner_index}:{candidate_identity}"
        if hasattr(self, "foundation_get_receipt"):
            prior = self.foundation_get_receipt(operation_key)
            if prior and prior.get("status") == "committed":
                return True, f"{candidate.name} was already staged for this replacement slot."
        # Free agents become one-fight contracted roster members exactly once;
        # an existing roster fighter remains in place and keeps their identity.
        if candidate in getattr(self, "free_agents", []):
            membership_recorded = False
            membership = getattr(self, "record_membership_event", None)
            if callable(membership):
                membership(
                    candidate, "join", company_name=self.player_company_name,
                    reason="Last-minute replacement",
                    source_transaction=f"last-minute-replacement:{getattr(candidate, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                )
                membership_recorded = True
            self.free_agents.remove(candidate)
            candidate.purse = max(int(getattr(candidate, "purse", 0) or 0), round(max(1, int(getattr(candidate, "purse", 0) or 0) * 1.35) / 500) * 500)
            candidate.contract_months = 1
            candidate.exclusive = False
            candidate.contract_type = "One-Fight Deal"
            candidate.camp_weeks = 0
            candidate.camp_boost = 0
            candidate.morale = min(100, int(getattr(candidate, "morale", 50) or 50) + 4)
            candidate.media_heat = min(100, int(getattr(candidate, "media_heat", 0) or 0) + 6)
            self.roster.append(candidate)
            if hasattr(self, "record_contract_signing"):
                self.record_contract_signing(
                    candidate, self.player_company_name,
                    source="Last-minute replacement",
                    record_membership=not membership_recorded,
                )
            elif not membership_recorded:
                membership = getattr(self, "record_membership_event", None)
                if callable(membership):
                    membership(
                        candidate, "join", company_name=self.player_company_name,
                        reason="Last-minute replacement",
                        source_transaction=f"last-minute-replacement:{getattr(candidate, 'fighter_id', '')}:{self.player_company_name}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                    )
            source = "free agent"
        else:
            source = "player roster"
        if hasattr(self, "ensure_foundation_ids"):
            self.ensure_foundation_ids()
        capture_date = (
            self.format_game_date(event.get("month", self.month), event.get("week", self.week))
            if hasattr(self, "format_game_date") else ""
        )

        def rank_snapshot(fighter, *, fallback_company=""):
            if fighter is None:
                return {
                    "fighter_id": "", "fighter": "", "company": str(fallback_company or ""),
                    "company_rank": "-", "world_rank": "-", "captured_date": capture_date,
                }
            try:
                company_name = (
                    self.fighter_company_for_profile(fighter)
                    if hasattr(self, "fighter_company_for_profile") else fallback_company
                ) or fallback_company or "Unknown"
            except (TypeError, ValueError, AttributeError):
                company_name = fallback_company or "Unknown"
            company_rank, world_rank = "-", "-"
            rank_fn = getattr(self, "rank_label_for_fighter", None)
            if callable(rank_fn):
                if company_name != "Free Agent":
                    try:
                        company_rank = str(rank_fn(fighter, company_name, world=False) or "-")
                    except (TypeError, ValueError, AttributeError):
                        company_rank = "-"
                try:
                    world_rank = str(rank_fn(fighter, company_name, world=True) or "-")
                except (TypeError, ValueError, AttributeError):
                    world_rank = "-"
            return {
                "fighter_id": str(getattr(fighter, "fighter_id", "") or ""),
                "fighter": str(getattr(fighter, "name", "") or ""),
                "company": str(company_name),
                "company_rank": company_rank,
                "world_rank": world_rank,
                "captured_date": capture_date,
            }

        # Capture every relevant identity before mutating the slot. The
        # removed corner may be TBA in a legacy booking, so the retained
        # opponent is resolved independently rather than assumed from a name.
        current_fighters = []
        try:
            current_fighters = list(self.event_fight_fighters(fight))
        except (TypeError, ValueError, AttributeError):
            current_fighters = []
        retained_opponent = next(
            (
                item for item in current_fighters
                if item is not replaced
                and str(getattr(item, "fighter_id", "") or "") != old_id
                and str(getattr(item, "name", "") or "") != old_name
            ),
            None,
        )
        removed_snapshot = rank_snapshot(replaced, fallback_company="Unknown")
        replacement_snapshot = rank_snapshot(candidate, fallback_company=source)
        opponent_snapshot = rank_snapshot(retained_opponent, fallback_company="Unknown")
        replacement_row = {
            "date": capture_date,
            "corner": corner_index,
            "removed_id": old_id,
            "removed_reference": old_reference,
            "removed_name": old_name,
            "replacement_id": str(getattr(candidate, "fighter_id", "") or ""),
            "replacement_reference": candidate_reference,
            "replacement_name": candidate.name,
            "source": source,
            "company_rank": next((row["company_rank"] for row in candidates if row["fighter"] is candidate), "-"),
            "world_rank": next((row["world_rank"] for row in candidates if row["fighter"] is candidate), "-"),
            "pre_bout_rankings": {
                "captured_date": capture_date,
                "removed": removed_snapshot,
                "replacement": replacement_snapshot,
                "retained_opponent": opponent_snapshot,
            },
        }
        fight.setdefault("replacement_history", []).append(replacement_row)
        names[corner_index] = candidate.name
        fighter_ids[corner_index] = str(getattr(candidate, "fighter_id", "") or "")
        fight["fighters"], fight["fighter_ids"] = names, fighter_ids
        fight.setdefault("fight_plans", {})[fighter_ids[corner_index]] = "Balanced"
        fight["last_minute_replacement"] = dict(replacement_row)
        fight["replacement_title_review_required"] = title_stakes
        if hasattr(self, "assign_event_camps"):
            self.assign_event_camps({"month": event.get("month", self.month), "week": event.get("week", self.week), "fights": [{"fighters": [candidate.name], "fighter_ids": [fighter_ids[corner_index]]}]})
        if hasattr(self, "foundation_record_work"):
            self.foundation_record_work(
                operation_key, domain="booking", action="last_minute_replacement",
                target_id=str(event.get("event_id", "")), status="committed", result=dict(replacement_row),
            )
        self.news.insert(0, f"{candidate.name} accepted a last-minute replacement bout ({candidate.weight}); company {replacement_row['company_rank']}, world {replacement_row['world_rank']}.")
        return True, f"{candidate.name} is now booked on short notice."

    def capture_event_transaction_state(self, memo=None):
        """Copy persistent state before committing a completed player card.

        UI handles stay live; the domain state is restored in full if any late
        award, archive, finance, or presentation-adjacent hook fails.
        """
        snapshot = {}
        memo = {} if memo is None else memo
        for key, value in self.__dict__.items():
            if self.event_transaction_runtime_value(value):
                continue
            try:
                snapshot[key] = deepcopy(value, memo)
            except Exception as exc:
                raise RuntimeError(f"Could not stage event state attribute {key!r}.") from exc
        return snapshot

    def restore_event_transaction_state(self, snapshot):
        """Restore the domain attributes captured for a failed event commit."""
        live_keys = {
            key for key, value in self.__dict__.items()
            if self.event_transaction_runtime_value(value)
        }
        for key in list(self.__dict__):
            if key not in live_keys and key not in snapshot:
                del self.__dict__[key]
        for key, value in snapshot.items():
            self.__dict__[key] = value

    def finish_event(self, event, package):
        """Commit an event atomically before refreshing the live UI."""
        # A title-miss prompt may deliberately leave preparation unresolved.
        # This is a resumable read/decision boundary, not a completed event;
        # never assign a settlement id, archive cancellations, charge finance,
        # or advance the calendar until the player commits an action.
        if isinstance(package, dict) and package.get("preparation_pending"):
            notice = getattr(self, "_results_status_notice", None)
            if callable(notice):
                notice(
                    str(package.get(
                        "pending_reason",
                        "Choose the pending title-miss action before settling this event.",
                    )),
                    warning=True,
                )
            return package
        settlement_id = package.get("record_id") or (event or {}).get("_settlement_id") or f"event-{uuid4().hex}"
        package["record_id"] = settlement_id
        if event is not None:
            event["_settlement_id"] = settlement_id
        if package.get("_settlement_committed") or any(
            row.get("record_id") == settlement_id
            for row in list(getattr(self, "result_index", [])) + list(getattr(self, "result_records", []))
        ):
            return package
        # A previous rollback may have replaced roster objects. The live viewer
        # owns its package, so resolve every result participant against this world.
        rebound = []
        for winner, loser, fight, method in package.get("results", []):
            resolved = []
            for fighter in (winner, loser):
                reference = str(getattr(fighter, "fighter_id", "") or "")
                current = self.resolve_fighter(reference) if reference else None
                if current is None:
                    raise RuntimeError("Event participant could not be resolved by fighter ID; settlement was not applied.")
                resolved.append(current)
            rebound.append((resolved[0], resolved[1], fight, method))
        package["results"] = rebound
        memo = {}
        transaction_state = self.capture_event_transaction_state(memo)
        package_state = deepcopy(package, memo)
        event_state = deepcopy(event, memo) if event is not None else None
        rng_state = random.getstate()
        try:
            completed_package = self._finish_event_unchecked(event, package)
            completed_package["_settlement_committed"] = True
        except Exception:
            self.restore_event_transaction_state(transaction_state)
            package.clear()
            package.update(package_state)
            if event is not None:
                event.clear()
                event.update(event_state)
            random.setstate(rng_state)
            raise
        # Presentation errors must never turn a committed card into a retryable
        # domain failure. The archived results remain the authority.
        try:
            self.refresh_all()
            self.write_log()
            self.show_event_summary(completed_package)
        except Exception as exc:
            completed_package["_presentation_error"] = str(exc)
            notice = getattr(self, "_results_status_notice", None)
            if callable(notice):
                notice("Results saved successfully, but the display could not refresh. Open Results to review the card. " + str(exc), warning=True)
            else:
                try:
                    messagebox.showwarning("Results saved", "The event was settled successfully, but its display could not refresh. Open Results to review the card.\n\n" + str(exc))
                except Exception:
                    pass
        return completed_package

    def _finish_event_unchecked(self, event, package):
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
            for fighter in self.event_fight_fighters(fight):
                if fighter and fighter not in featured:
                    featured.append(fighter)
        if package.get("media_outcome"):
            self.record_media_event_outcome(event, package["media_outcome"], featured_fighters=featured)

        award_pool = package.get("award_pool", [])
        finance = package.get("finance", {})
        clause_breakdown = self.event_contract_clause_payouts(package.get("results", []), finance)
        clause_payout = int(finance.get("contract_clauses", clause_breakdown["total"]) or 0)
        clauses_included = bool(finance.get("contract_clauses_included", False))
        for index, (winner, loser, fight, method) in enumerate(package["results"]):
            stats = fight.get("_fighter_stats", {})
            if stats:
                winner.last_fight_stats = dict(stats.get(getattr(winner, "fighter_id", "") or winner.name, stats.get(winner.name, {})) or {}) or None
                loser.last_fight_stats = dict(stats.get(getattr(loser, "fighter_id", "") or loser.name, stats.get(loser.name, {})) or {}) or None
            excitement = award_pool[index].get("excitement", 50) if index < len(award_pool) else 50
            round_no = award_pool[index].get("round", 1) if index < len(award_pool) else 1
            if method != "No Contest":
                self.record_season_result(winner, loser, method, round_no, fight, excitement, self.player_company_name)
            if method == "Draw":
                self.apply_draw_result(winner, loser, fight)
            elif method == "No Contest":
                self.apply_no_contest_result(winner, loser, fight)
            else:
                self.apply_result(winner, loser, fight, method)
            settlement_evidence = self.title_sanction_settlement_evidence(
                fight, winner, loser, method,
            )
            if settlement_evidence:
                # Keep the observed outcome with both the settled fight copy
                # and the archived/read-only fight log. Matching is
                # ID-first; a legacy row without durable IDs is not guessed
                # into another bout by display name or list position.
                raw_sanction = fight.get("title_sanction_snapshot")
                if isinstance(raw_sanction, dict):
                    raw_sanction["settlement"] = deepcopy(settlement_evidence)
                fight["title_settlement_evidence"] = deepcopy(settlement_evidence)
                fight_id = str(fight.get("fight_id", "") or fight.get("bout_id", "") or "")
                fighter_ids = {
                    str(getattr(item, "fighter_id", "") or "")
                    for item in (winner, loser)
                    if str(getattr(item, "fighter_id", "") or "")
                }
                for fight_log in package.get("fight_logs", []):
                    if not isinstance(fight_log, dict):
                        continue
                    log_id = str(fight_log.get("fight_id", "") or fight_log.get("bout_id", "") or "")
                    log_ids = {
                        str(fight_log.get("a_id", "") or ""),
                        str(fight_log.get("b_id", "") or ""),
                    } - {""}
                    same_bout = bool(fight_id and log_id and fight_id == log_id)
                    if not same_bout and fighter_ids and log_ids:
                        same_bout = fighter_ids == log_ids
                    if not same_bout:
                        continue
                    fight_log["title_settlement_evidence"] = deepcopy(settlement_evidence)
                    log_snapshot = fight_log.get("title_sanction_snapshot")
                    if isinstance(log_snapshot, dict):
                        log_snapshot["settlement"] = deepcopy(settlement_evidence)
                    break
                preparation = package.get("preparation_timeline")
                if isinstance(preparation, dict):
                    for decision in preparation.get("title_miss_decisions", []) if isinstance(preparation.get("title_miss_decisions"), list) else []:
                        if not isinstance(decision, dict):
                            continue
                        if fight_id and str(decision.get("fight_id", "") or "") == fight_id:
                            decision["settlement"] = deepcopy(settlement_evidence)
                            break
            self.record_standard_guaranteed_fight(winner)
            self.record_standard_guaranteed_fight(loser)
        if clause_payout:
            # New event packages already include clauses in profit. Keep the
            # fallback for an in-memory package prepared by an older build.
            if not clauses_included:
                self.cash -= clause_payout
            self.finance["ledger"].insert(0, f"Month {self.month}: Contract clause payouts (win + finish + PPV) ${clause_payout:,}.")
        self.record_finance_transaction(
            package["event_name"], revenue=finance.get("total_revenue", 0),
            costs=finance.get("total_expense", 0) + (0 if clauses_included else clause_payout),
            category="Event", source="Promoted event", event=package["event_name"],
        )
        if hasattr(self, "settle_regional_invitation"):
            # The host guarantee is paid only after the ordinary event result
            # is known and is keyed to the saved entitlement, so retries cannot
            # create a second payment.
            self.settle_regional_invitation(event, package)
        for bracket in package.get("tournament_brackets", []):
            champion = self.resolve_award_fighter(bracket.get("champion", ""), bracket.get("champion_id", ""))
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
                    story = self.resolve_contract_promise_story(
                        fighter, fulfilled, kept=True, company=self.player_company_name,
                    )
                    if story and story.get("status") == "resolved":
                        self.record_world_story(
                            "Promise Kept", f"{self.player_company_name} keeps its commitment to {fighter.name}.",
                            story.get("resolution", ""), [self.player_company_name], [fighter.name], 3,
                            fighter_ids=[fighter.fighter_id], story_id=story.get("story_id", ""),
                        )
                        self.record_staff_contribution(
                            "Talent Relations", "fighter_promise_fulfilled",
                            f"The talent-relations team helped fulfil {fighter.name}'s {' and '.join(fulfilled)} commitment.",
                            event_ref=f"staff-promise-fulfilled:{fighter.fighter_id}:{self.month}:{self.week}",
                            importance=3,
                        )

        if event and event in self.scheduled_events:
            self.scheduled_events.remove(event)
        if event and package.get("tournament_brackets") and hasattr(self, "advance_grand_prix_after_event"):
            package["grand_prix_next_events"] = [
                dict(next_event) for next_event in self.advance_grand_prix_after_event(event, package)
            ]
        package["date"] = f"Month {self.month} Week {self.week}"
        package["company"] = self.player_company_name
        self.apply_event_awards(package.get("awards", []))
        self.apply_regional_show_effects(package)
        self.record_event_staff_milestones(package)
        # apply_result/apply_draw_result deliberately deferred these removals so
        # every event subsystem could still resolve the participants safely.
        for winner, loser, _fight, _method in package["results"]:
            self.retire_after_final_fight_if_due(winner, self.player_company_name)
            self.retire_after_final_fight_if_due(loser, self.player_company_name)
        self.result_history.insert(0, package["summary"])
        self.result_history = self.result_history[:RESULT_HISTORY_LIMIT]
        self.player_event_archive = [package] + list(getattr(self, "player_event_archive", []))
        self.player_event_archive = self.player_event_archive[:150]
        self.archive_result_record({
            "record_id": package["record_id"],
            "event_id": package.get("event_id", ""),
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
            "preparation_timeline": package.get("preparation_timeline", {}),
            "regional_invitation_id": package.get("regional_invitation_id", ""),
            "regional_invitation_outcome": package.get("regional_invitation_outcome", ""),
            "regional_host_guarantee": package.get("regional_host_guarantee", 0),
        })
        self.evaluate_promotion_achievements(self.player_company_name, package)
        self.complete_super_event(event, package)
        self.refresh_historical_records()
        self.refresh_promotion_rankings()
        self.update_player_fanbase(package)
        finance = package.get("finance", {})
        event_reason = (
            f"{package.get('fight_count', 0)} fights; excitement {round(package.get('average_excitement', 0) or 0)}; "
            f"${finance.get('total_revenue', 0):,} revenue against "
            f"${finance.get('total_expense', 0) + (0 if clauses_included else clause_payout):,} costs"
        )
        self.record_snapshot_changes(change_snapshot, event_reason, include_finance=False)
        package["attributed_changes"] = [entry for entry in getattr(self, "change_journal", []) if id(entry) not in prior_change_ids]
        region = package.get("region", self.venue_region(package["venue"]))
        if region in self.regions:
            self.regions[region]["last_major_show"] = package["summary"]
        self.event_log = (package["log"] + [""] + self.event_log)[:EVENT_LOG_LIMIT]
        self.news.insert(0, f"{package['fight_count']}-fight show completed; {self.player_company_name} banked ${package['profit']:,}.")
        main = next((row for row in package.get("fight_logs", []) if "MAIN" in str(row.get("label", "")).upper()), None)
        headline = f"{self.player_company_name} completes {package['event_name']}."
        detail = main.get("result", "") if main else package["summary"]
        self.record_world_story("Event", headline, f"{detail} Profit: ${package['profit']:,}.", [self.player_company_name], importance=3)
        return package

    def apply_regional_show_effects(self, package):
        region = package.get("region", self.player_region)
        city = package.get("city", "")
        data = self.regions.get(region, {})
        morale_bonus = data.get("promo_benefit", {}).get("morale", 1)
        for winner, loser, fight, method in package["results"]:
            for fighter in (winner, loser):
                if not fighter:
                    continue
                connection = self.fighter_event_connection(fighter, region, city)
                if connection["strength"] <= 0:
                    continue
                is_winner = fighter is winner and method not in ("Draw", "No Contest")
                hometown_bonus = 2 if connection["level"] == "Hometown" else 1 if connection["strength"] >= 0.66 else 0
                fighter.morale = min(100, fighter.morale + max(1, round(morale_bonus * connection["strength"])) + hometown_bonus)
                fighter.motivation = min(99, fighter.motivation + 1 + hometown_bonus)
                market_delta = (3 if is_winner else 1) + hometown_bonus + (1 if method not in ("Decision", "Technical Decision", "Draw", "No Contest") and is_winner else 0)
                self.update_regional_popularity(fighter, region, market_delta, f"{connection['level']} appearance at {package.get('event_name', 'an event')}")
                opponent = loser if fighter is winner else winner
                home_fight = dict(fight or {}, region=region, city=city)
                self.record_hometown_fight_story(
                    fighter, opponent, home_fight, method, is_winner,
                    event_name=package.get("event_name", "an event"),
                    company=self.player_company_name,
                )
                if is_winner:
                    fighter.popularity = min(100, fighter.popularity + 1 + hometown_bonus)
                    fighter.media_heat = min(100, fighter.media_heat + 1 + hometown_bonus)

    def choose_event_awards(self, award_pool):
        if not award_pool:
            return []
        awards = []
        fight = max(award_pool, key=lambda row: row["excitement"])
        awards.append({"award": "Fight of the Night", "fighters": fight.get("fighters", [fight["winner"], fight["loser"]]), "fighter_ids": fight.get("fighter_ids", []), "note": fight["fight"], "bonus": self.post_show_bonuses["fight"]})
        kos = [row for row in award_pool if "KO" in row["method"] or "TKO" in row["method"]]
        subs = [row for row in award_pool if "Submission" in row["method"]]
        if kos:
            row = max(kos, key=lambda item: item["excitement"])
            awards.append({"award": "KO of the Night", "fighters": [row["winner"]], "fighter_ids": [row.get("winner_id", "")], "note": row["method"], "bonus": self.post_show_bonuses["ko"]})
        if subs:
            row = max(subs, key=lambda item: item["excitement"])
            awards.append({"award": "Submission of the Night", "fighters": [row["winner"]], "fighter_ids": [row.get("winner_id", "")], "note": row["method"], "bonus": self.post_show_bonuses["sub"]})
        return awards

    def apply_event_awards(self, awards):
        for award in awards:
            identities = award.get("fighter_ids", [])
            for index, name in enumerate(award["fighters"]):
                fighter = self.resolve_award_fighter(name, identities[index] if index < len(identities) else "")
                if not fighter:
                    continue
                fighter.morale = min(100, fighter.morale + 8)
                fighter.popularity = min(100, fighter.popularity + 1)
                self.finance["ledger"].insert(0, f"Month {self.month}: {fighter.name} earned {award['award']} bonus ${award['bonus']:,}.")

    def show_event_summary(self, package):
        if self.root.state() == "withdrawn":
            return
        window = self.create_managed_window()
        window.title("End of Event")
        window.update_idletasks()
        screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
        summary_width = min(1040, max(760, screen_w - 100))
        summary_height = min(760, max(520, screen_h - 140))
        window.geometry(f"{summary_width}x{summary_height}")
        window.minsize(min(760, summary_width), min(520, summary_height))
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="END OF EVENT", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        summary_controls = ttk.Frame(window, style="Chrome.TFrame")
        summary_controls.pack(side="bottom", fill="x", padx=8, pady=(4, 8))
        if package.get("tournament_brackets"):
            ttk.Button(summary_controls, text="View Tournament Bracket", style="Accent.TButton", command=lambda: self.open_event_tournament_bracket(package, window)).pack(side="left")
        close_summary_button = ttk.Button(summary_controls, text="Close", command=window.destroy)
        close_summary_button.pack(side="right")

        summary_body = ttk.Frame(window, style="Chrome.TFrame")
        summary_body.pack(fill="both", expand=True, padx=8, pady=4)
        summary_canvas = tk.Canvas(summary_body, bg=self.colors["chrome"], highlightthickness=0)
        summary_scroll = ttk.Scrollbar(summary_body, orient="vertical", command=summary_canvas.yview)
        summary_canvas.configure(yscrollcommand=summary_scroll.set)
        summary_scroll.pack(side="right", fill="y")
        summary_canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(summary_canvas, style="Chrome.TFrame")
        content_id = summary_canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda _event: summary_canvas.configure(scrollregion=summary_canvas.bbox("all")))
        summary_canvas.bind("<Configure>", lambda event: summary_canvas.itemconfigure(content_id, width=event.width))
        summary_canvas.bind("<MouseWheel>", lambda event: summary_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"))

        overview = ttk.Frame(content, style="Panel.TFrame")
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
        # Calibrated to the range a real card actually produces. Averaging a
        # whole card pulls hard toward the middle, so event scores land roughly
        # 33-59 with a median near 47. The old A/B cutoffs of 78 and 64 sat
        # above the maximum a card could reach and were literally unobtainable,
        # while the F cutoff caught the median show.
        grade = "A" if excitement >= 53 else "B" if excitement >= 49 else "C" if excitement >= 44 else "D" if excitement >= 40 else "F"

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

        # Preparation is presented as a compact timeline so the player can
        # follow the build to the card without parsing the raw event log.  It
        # is intentionally read-only: the resolver has already produced these
        # outcomes and opening the summary must never reroll a press or scale.
        preparation = package.get("preparation_timeline", {})
        stage_states = preparation.get("stage_states", []) if isinstance(preparation, dict) else []
        if stage_states:
            prep_panel = ttk.Frame(content, style="Panel.TFrame")
            prep_panel.pack(fill="x", padx=8, pady=4)
            ttk.Label(prep_panel, text="EVENT PREPARATION", style="Section.TLabel", anchor="center").pack(fill="x", ipady=3)
            ttk.Label(
                prep_panel,
                text="Recorded campaign, press and weigh-in outcomes — no stage is rerun from this view.",
                style="Panel.TLabel", anchor="w", justify="left", wraplength=900,
            ).pack(fill="x", padx=12, pady=(0, 5))
            prep_cards = tk.Frame(prep_panel, bg=self.colors["panel"])
            prep_cards.pack(fill="x", padx=8, pady=(0, 8))
            status_colors = {
                "Recorded": self.colors.get("green", "#6dd58c"),
                "Evidence recorded": self.colors.get("green", "#6dd58c"),
                "Ready for the recorded card": self.colors.get("green", "#6dd58c"),
            }
            for state in stage_states:
                if not isinstance(state, dict):
                    continue
                status = str(state.get("status", "Not recorded"))
                accent = status_colors.get(status, self.colors.get("gold", "#e4b45f"))
                card = tk.Frame(
                    prep_cards, bg=self.colors["tree"], highlightthickness=1,
                    highlightbackground=accent,
                )
                card.pack(side="left", fill="both", expand=True, padx=3)
                tk.Label(
                    card, text=str(state.get("label", "Preparation stage")).upper(),
                    bg=self.colors["tree"], fg=self.colors["muted"],
                    font=("Tahoma", 8, "bold"), anchor="w",
                ).pack(fill="x", padx=8, pady=(6, 1))
                tk.Label(
                    card, text=status, bg=self.colors["tree"], fg=accent,
                    font=("Tahoma", 10, "bold"), anchor="w",
                ).pack(fill="x", padx=8)
                tk.Label(
                    card, text=str(state.get("detail", "")), bg=self.colors["tree"],
                    fg=self.colors["text"], font=("Tahoma", 8), anchor="w",
                    justify="left", wraplength=205,
                ).pack(fill="x", padx=8, pady=(1, 7))

        result_panel = ttk.Frame(content, style="Panel.TFrame")
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
            matchup = (
                f"{self.display_fighter_name_value(log.get('a', ''))} vs {self.display_fighter_name_value(log.get('b', ''))}"
                if log.get("a") else log.get("heading", "Bout")
            )
            stage = log.get("tournament_stage") or log.get("label", "BOUT")
            tags = ("headline",) if "MAIN" in str(stage).upper() else ("title",) if log.get("title") else ()
            tree.insert("", "end", values=(index, stage, matchup, self.display_fighter_names_in_text(log.get("result", "Cancelled"), log), log.get("excitement", "-")), tags=tags)

        bonus_panel = ttk.Frame(content, style="Panel.TFrame")
        bonus_panel.pack(fill="x", padx=8, pady=4)
        ttk.Label(bonus_panel, text="POST-FIGHT BONUSES", style="Section.TLabel", anchor="center").pack(fill="x", ipady=3)
        if package.get("awards"):
            for award in package["awards"]:
                fighter_names = ", ".join(self.display_fighter_name_value(name) for name in award["fighters"])
                ttk.Label(bonus_panel, text=f"{award['award']}: {fighter_names}  |  {award['note']}  |  ${award['bonus']:,}", style="Panel.TLabel").pack(anchor="w", padx=12, pady=2)
        else:
            ttk.Label(bonus_panel, text="No bonuses awarded.", style="Panel.TLabel").pack(anchor="w", padx=12, pady=4)
        close_summary_button.focus_set()
