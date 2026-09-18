"""Multi-event Grand Prix scheduling and state transitions.

The ordinary tournament card remains the execution engine.  This mixin owns
the small amount of durable planning state needed to let one bracket continue
across several ordinary event cards without creating a second fight, contract,
or finance system.
"""

from copy import deepcopy
from uuid import uuid4


class GrandPrixMixin:
    GRAND_PRIX_FIELD_SIZES = (4, 8, 16)
    GRAND_PRIX_MAX_EVENTS = 4
    GRAND_PRIX_DECIDER_MINUTES = 15

    @classmethod
    def grand_prix_round_count(cls, field_size):
        try:
            field_size = int(field_size)
        except (TypeError, ValueError):
            return 0
        if field_size not in cls.GRAND_PRIX_FIELD_SIZES:
            return 0
        return {4: 2, 8: 3, 16: 4}[field_size]

    @classmethod
    def grand_prix_event_count_options(cls, field_size):
        rounds = cls.grand_prix_round_count(field_size)
        return tuple(range(1, min(cls.GRAND_PRIX_MAX_EVENTS, rounds) + 1))

    @classmethod
    def grand_prix_stage_distribution(cls, field_size, event_count):
        rounds = cls.grand_prix_round_count(field_size)
        try:
            event_count = int(event_count)
        except (TypeError, ValueError):
            return ()
        if not rounds or event_count not in cls.grand_prix_event_count_options(field_size):
            return ()
        base, remainder = divmod(rounds, event_count)
        return tuple(base + (1 if index < remainder else 0) for index in range(event_count))

    def ensure_grand_prix_state(self):
        raw = getattr(self, "grand_prix_series", None)
        if not isinstance(raw, list):
            raw = []
        cleaned = []
        for row in raw:
            if not isinstance(row, dict):
                continue
            series = dict(row)
            series["series_id"] = str(series.get("series_id", "") or "")
            if not series["series_id"]:
                series["series_id"] = f"grand-prix:{uuid4().hex}"
            series.setdefault("status", "Scheduled")
            series.setdefault("history", [])
            series.setdefault("event_ids", [])
            series.setdefault("scheduled_dates", [])
            series.setdefault("advancing_ids", [])
            series.setdefault("original_entrant_ids", [])
            cleaned.append(series)
        self.grand_prix_series = cleaned
        return self.grand_prix_series

    def grand_prix_series_by_id(self, series_id):
        token = str(series_id or "")
        if not token:
            return None
        return next((row for row in self.ensure_grand_prix_state()
                     if str(row.get("series_id", "")) == token), None)

    def grand_prix_series_for_fight(self, fight):
        if not isinstance(fight, dict):
            return None
        metadata = fight.get("grand_prix") if isinstance(fight.get("grand_prix"), dict) else {}
        series_id = str(
            fight.get("grand_prix_series_id", "")
            or metadata.get("series_id", "")
            or fight.get("tournament_series_id", "")
            or ""
        )
        return self.grand_prix_series_by_id(series_id)

    def grand_prix_series_for_event(self, event):
        for fight in (event or {}).get("fights", []) if isinstance(event, dict) else []:
            series = self.grand_prix_series_for_fight(fight)
            if series:
                return series
        return None

    def _grand_prix_event_economics(self, event):
        keys = (
            "ticket_price", "marketing_budget", "production_tier", "broadcaster",
            "venue_capacity", "attendance_target",
        )
        return {key: deepcopy(event.get(key)) for key in keys if key in event}

    def _grand_prix_series_id(self):
        counter = getattr(self, "_grand_prix_series_counter", 0) + 1
        self._grand_prix_series_counter = counter
        if hasattr(self, "_foundation_next_id"):
            try:
                value = self._foundation_next_id("grand-prix")
                if value:
                    return str(value)
            except Exception:
                pass
        return f"grand-prix:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}:{counter}:{uuid4().hex[:8]}"

    def _grand_prix_fighter_ids(self, fight):
        entrants = list(fight.get("tournament_entrants", fight.get("fighters", [])) or [])
        fighter_ids = list(fight.get("fighter_ids", []) or [])
        if len(fighter_ids) == len(entrants) and all(str(value or "") for value in fighter_ids):
            return [str(value) for value in fighter_ids]
        resolved = []
        for name in entrants:
            fighter = self._resolve_event_fighter(name) if name != "TBA" else None
            resolved.append(str(getattr(fighter, "fighter_id", "") or ""))
        return resolved

    def _grand_prix_series_snapshot(self, event, fight, *, owner_kind="player"):
        entrants = list(fight.get("tournament_entrants", fight.get("fighters", [])) or [])
        fighter_ids = self._grand_prix_fighter_ids(fight)
        try:
            field_size = int(fight.get("tournament_size", len(entrants)) or len(entrants))
        except (TypeError, ValueError):
            field_size = len(entrants)
        try:
            event_count = int(fight.get("grand_prix_event_count", 1) or 1)
        except (TypeError, ValueError):
            event_count = 1
        distribution = self.grand_prix_stage_distribution(field_size, event_count)
        if not distribution or len(entrants) != field_size or len(fighter_ids) != field_size or not all(fighter_ids):
            return None
        series_id = str(fight.get("grand_prix_series_id", "") or self._grand_prix_series_id())
        title_flags = {
            "title": bool(fight.get("title")),
            "divisional_title": bool(fight.get("divisional_title")),
            "interim": bool(fight.get("interim")),
            "special_belt": str(fight.get("special_belt", "") or ""),
        }
        return {
            "schema_version": 1,
            "series_id": series_id,
            "name": str(fight.get("tournament_name", "MMA Grand Prix") or "MMA Grand Prix"),
            "owner_kind": str(owner_kind or "player"),
            "status": "Scheduled",
            "field_size": field_size,
            "event_count": event_count,
            "stage_count": len(distribution) + max(0, sum(distribution) - len(distribution)),
            "stage_distribution": list(distribution),
            "next_event_index": 0,
            "completed_event_count": 0,
            "completed_stage_count": 0,
            "original_entrant_ids": list(fighter_ids),
            "original_entrants": list(entrants),
            "advancing_ids": list(fighter_ids),
            "weight": str(fight.get("tournament_weight", "") or ""),
            "gender": str(fight.get("tournament_gender", "") or ""),
            "title_flags": title_flags,
            "event_ids": [str(event.get("event_id", "") or "")],
            "scheduled_dates": [],
            "history": [],
            "created_month": int(getattr(self, "month", 0) or 0),
            "created_week": int(getattr(self, "week", 0) or 0),
            "last_event_id": str(event.get("event_id", "") or ""),
        }

    def register_grand_prix_series_for_event(self, event, *, owner_kind="player"):
        """Attach durable series state to any Grand Prix fight on ``event``.

        Only the current event is scheduled.  The next stage is materialised
        after settlement, which keeps the normal booking conflict/readiness
        rules meaningful and lets an injury move the whole competition.
        """
        if not isinstance(event, dict):
            return []
        series_rows = self.ensure_grand_prix_state()
        registered = []
        for fight in event.get("fights", []) or []:
            if not isinstance(fight, dict) or not fight.get("tournament"):
                continue
            if self.grand_prix_series_for_fight(fight):
                registered.append(self.grand_prix_series_for_fight(fight))
                continue
            series = self._grand_prix_series_snapshot(event, fight, owner_kind=owner_kind)
            if series is None:
                continue
            series_rows.append(series)
            fight["grand_prix_series_id"] = series["series_id"]
            fight["grand_prix"] = {
                "series_id": series["series_id"],
                "field_size": series["field_size"],
                "event_count": series["event_count"],
                "stage_count": series["stage_count"],
                "owner_kind": series["owner_kind"],
            }
            fight["grand_prix_stage_start"] = 0
            fight["grand_prix_stage_end"] = int(series["stage_distribution"][0])
            fight["grand_prix_event_index"] = 0
            fight["grand_prix_decider_minutes"] = self.GRAND_PRIX_DECIDER_MINUTES
            registered.append(series)
        return registered

    def _grand_prix_date_index(self, month, week, day=None):
        if hasattr(self, "calendar_day_index"):
            try:
                return int(self.calendar_day_index(month, week, day))
            except (TypeError, ValueError, AttributeError):
                pass
        if hasattr(self, "calendar_week_index"):
            return int(self.calendar_week_index(month, week)) * 7
        return int(month or 1) * 28 + int(week or 1) * 7

    def grand_prix_next_best_date(self, series, *, after_event=None, fighters=None):
        """Find the next playable date without consuming RNG or creating work."""
        after_event = after_event if isinstance(after_event, dict) else {}
        start = self._grand_prix_date_index(
            after_event.get("month", getattr(self, "month", 1)),
            after_event.get("week", getattr(self, "week", 1)),
            after_event.get("day"),
        ) + 7
        fighters = list(fighters or [])
        for offset in range(0, 366 * 3):
            month, week, day = self.day_index_parts(start + offset) if hasattr(self, "day_index_parts") else (getattr(self, "month", 1), getattr(self, "week", 1), 1)
            if week not in range(1, 5):
                continue
            if fighters and all(
                self.fighter_available_for_date(fighter, month, week, day)
                for fighter in fighters if fighter is not None
            ):
                return month, week, day
        return (
            max(getattr(self, "month", 1), int(after_event.get("month", getattr(self, "month", 1)) or 1) + 1),
            1,
            1,
        )

    def _grand_prix_stage_event(self, series, *, source_event=None, date_override=None):
        advancing_ids = [str(value) for value in series.get("advancing_ids", []) if value]
        fighters = []
        for value in advancing_ids:
            if not hasattr(self, "resolve_fighter"):
                continue
            try:
                fighter = self.resolve_fighter(value)
            except (LookupError, TypeError, ValueError):
                fighter = None
            if fighter is not None:
                fighters.append(fighter)
        if len(fighters) != len(advancing_ids):
            return None
        event_index = int(series.get("next_event_index", 0) or 0)
        distribution = list(series.get("stage_distribution", []) or [])
        if event_index >= len(distribution):
            return None
        stage_start = sum(int(value or 0) for value in distribution[:event_index])
        stage_end = stage_start + int(distribution[event_index] or 0)
        source_event = source_event if isinstance(source_event, dict) else {}
        if date_override:
            month, week, day = date_override
        else:
            month, week, day = self.grand_prix_next_best_date(series, after_event=source_event, fighters=fighters)
        event_id = self._foundation_next_id("event") if hasattr(self, "_foundation_next_id") else f"event:{uuid4().hex}"
        base_name = str(series.get("name", "MMA Grand Prix") or "MMA Grand Prix")
        event_name = f"{base_name} — Stage {event_index + 1}/{len(distribution)}"
        names = [fighter.name for fighter in fighters]
        fight = {
            "fighters": [names[0], names[-1]],
            "fighter_ids": list(advancing_ids),
            "tournament": True,
            "tournament_size": int(series.get("field_size", len(fighters)) or len(fighters)),
            "tournament_entrants": names,
            "tournament_weight": str(series.get("weight", getattr(fighters[0], "weight", "")) or ""),
            "tournament_gender": str(series.get("gender", getattr(fighters[0], "gender", "")) or ""),
            "tournament_name": base_name,
            **deepcopy(series.get("title_flags", {})),
            "main": True,
            "tier": "Main Card",
            "grand_prix_series_id": str(series.get("series_id", "")),
            "grand_prix": {
                "series_id": str(series.get("series_id", "")),
                "field_size": int(series.get("field_size", len(fighters)) or len(fighters)),
                "event_count": len(distribution),
                "stage_count": int(series.get("stage_count", 0) or 0),
                "owner_kind": str(series.get("owner_kind", "player") or "player"),
            },
            "grand_prix_stage_start": stage_start,
            "grand_prix_stage_end": stage_end,
            "grand_prix_event_index": event_index,
            "grand_prix_decider_minutes": self.GRAND_PRIX_DECIDER_MINUTES,
        }
        event = {
            "event_id": str(event_id),
            "name": event_name,
            "auto_named": False,
            "venue": source_event.get("venue", "Regional Arena"),
            "region": source_event.get("region", getattr(self, "player_region", "USA")),
            "city": source_event.get("city", ""),
            "month": month,
            "week": week,
            "day": day,
            "broadcaster": source_event.get("broadcaster", ""),
            "fights": [fight],
            **self._grand_prix_event_economics(source_event),
            "grand_prix_series_id": str(series.get("series_id", "")),
            "grand_prix_event_index": event_index,
            "grand_prix_status": "Scheduled",
        }
        self.scheduled_events.append(event)
        series.setdefault("event_ids", []).append(str(event_id))
        series["last_event_id"] = str(event_id)
        series["next_event_index"] = event_index
        series["status"] = "Scheduled"
        self.assign_event_camps(event)
        return event

    def advance_grand_prix_after_event(self, event, package):
        """Record a completed stage and materialise the next stage if needed."""
        if not isinstance(package, dict):
            return []
        scheduled = []
        for bracket in package.get("tournament_brackets", []) or []:
            if not isinstance(bracket, dict):
                continue
            series_id = str(bracket.get("series_id", "") or "")
            series = self.grand_prix_series_by_id(series_id)
            if not series or str(series.get("status", "")) == "Completed":
                continue
            advancing = [str(value) for value in bracket.get("advancing_ids", []) if value]
            if not advancing:
                continue
            event_index = int(bracket.get("event_index", series.get("next_event_index", 0)) or 0)
            series["advancing_ids"] = advancing
            series["completed_event_count"] = event_index + 1
            series["completed_stage_count"] = int(bracket.get("stage_end", series.get("completed_stage_count", 0)) or 0)
            series["next_event_index"] = event_index + 1
            series.setdefault("history", []).append(deepcopy(bracket))
            if bracket.get("completed"):
                series["status"] = "Completed"
                series["champion_id"] = str(bracket.get("champion_id", "") or "")
                series["champion"] = str(bracket.get("champion", "") or "")
                continue
            next_event = self._grand_prix_stage_event(series, source_event=event)
            if next_event:
                scheduled.append(next_event)
                series.setdefault("scheduled_dates", []).append({
                    "event_index": int(series["next_event_index"]),
                    "month": next_event.get("month"), "week": next_event.get("week"), "day": next_event.get("day"),
                    "policy": "next_best",
                })
                note = f"{series.get('name', 'Grand Prix')} advances to Stage {series['next_event_index'] + 1}/{series.get('event_count', 1)} on {self.event_date_label(next_event)}."
                if hasattr(self, "news"):
                    self.news.insert(0, note)
                if hasattr(self, "inbox"):
                    self.inbox.insert(0, {
                        "subject": "Grand Prix stage scheduled", "body": note,
                        "type": "Tournament", "resolved": False,
                        "series_id": series_id, "event_id": next_event.get("event_id", ""),
                    })
        return scheduled

    def grand_prix_confirmed_drug_failure(self, fighter):
        fighter_id = str(getattr(fighter, "fighter_id", "") or "")
        if not fighter_id:
            return False
        raw_state = getattr(self, "drug_testing_state", {})
        cases = raw_state.get("cases", []) if isinstance(raw_state, dict) else []
        confirmed = {
            "confirmed", "confirmed_positive", "confirmed_violation", "final_positive",
            "sanctioned", "violation_confirmed",
        }
        for case in cases if isinstance(cases, list) else []:
            if not isinstance(case, dict) or str(case.get("fighter_id", "")) != fighter_id:
                continue
            confirmation = case.get("confirmation", {}) if isinstance(case.get("confirmation"), dict) else {}
            final_resolution = case.get("final_resolution", {}) if isinstance(case.get("final_resolution"), dict) else {}
            sanction = case.get("sanction", {}) if isinstance(case.get("sanction"), dict) else {}
            values = {
                str(confirmation.get("status", "") or "").casefold(),
                str(final_resolution.get("status", "") or "").casefold(),
                str(sanction.get("status", "") or "").casefold(),
            }
            if values & {item.casefold() for item in confirmed}:
                return True
        return False

    def _grand_prix_replacement_candidates(self, event, fight, injured, *, excluded=None):
        weight = str(fight.get("tournament_weight", getattr(injured, "weight", "")) or "")
        gender = str(fight.get("tournament_gender", getattr(injured, "gender", "")) or "")
        excluded = {str(value) for value in (excluded or []) if value}
        current = {str(value) for value in fight.get("fighter_ids", []) if value}
        current.update(str(value) for value in fight.get("tournament_entrants", []) if value and value != "TBA")
        busy = set()
        for other_event in getattr(self, "scheduled_events", []) or []:
            if other_event is event:
                continue
            for other_fight in other_event.get("fights", []) or []:
                busy.update(str(value) for value in self.event_fight_participant_references(other_fight) if value and value != "TBA")
        for other_fight in getattr(self, "booked", []) or []:
            busy.update(str(value) for value in self.event_fight_participant_references(other_fight) if value and value != "TBA")
        pool = list(getattr(self, "free_agents", []) or []) + list(getattr(self, "roster", []) or [])
        rows = []
        seen = set()
        for candidate in pool:
            candidate_id = str(getattr(candidate, "fighter_id", "") or "")
            key = candidate_id or f"{candidate.name}:{candidate.gender}:{candidate.weight}"
            if key in seen:
                continue
            seen.add(key)
            if candidate.weight != weight or candidate.gender != gender:
                continue
            if candidate_id in current or candidate.name in current or candidate_id in busy or candidate.name in busy or candidate_id in excluded:
                continue
            if getattr(candidate, "retired", False) or getattr(candidate, "retirement_pending", False):
                continue
            if getattr(candidate, "primary_discipline", "MMA") != "MMA":
                continue
            if getattr(candidate, "injured", 0) or getattr(candidate, "fatigue", 0) >= 62:
                continue
            if hasattr(self, "fighter_available_for_date") and not self.fighter_available_for_date(candidate, event.get("month"), event.get("week"), event.get("day")):
                continue
            if hasattr(self, "fighter_booking_status") and self.fighter_booking_status(candidate, event.get("month"), event.get("week")) != "Ready":
                continue
            rows.append(candidate)
        return sorted(rows, key=lambda item: (-getattr(item, "overall", 0), -getattr(item, "elo_rating", 0), item.name))

    def _grand_prix_postpone_event(self, event, reason, fighters):
        target = self.grand_prix_next_best_date(self.grand_prix_series_for_event(event), after_event=event, fighters=fighters)
        event["month"], event["week"], event["day"] = target
        event["grand_prix_status"] = "Postponed"
        event["grand_prix_postponed_count"] = int(event.get("grand_prix_postponed_count", 0) or 0) + 1
        event["grand_prix_postponement_reason"] = str(reason)
        series = self.grand_prix_series_for_event(event)
        if series:
            series["status"] = "Postponed"
        note = f"{event.get('name', 'Grand Prix')} moved to {self.event_date_label(event)}: {reason}"
        if hasattr(self, "news"):
            self.news.insert(0, note)
        if hasattr(self, "inbox"):
            self.inbox.insert(0, {"subject": "Grand Prix postponed", "body": note, "type": "Tournament", "resolved": False, "series_id": series.get("series_id", "") if series else "", "event_id": event.get("event_id", "")})
        return note

    def prepare_grand_prix_event(self, event):
        """Apply injury/confirmed-positive policy before press or weigh-ins."""
        notes = []
        for fight in event.get("fights", []) if isinstance(event, dict) else []:
            if not isinstance(fight, dict) or not fight.get("tournament") or not self.grand_prix_series_for_fight(fight):
                continue
            entrants = list(fight.get("tournament_entrants", []) or [])
            ids = list(fight.get("fighter_ids", []) or [])
            if len(ids) != len(entrants):
                ids = self._grand_prix_fighter_ids(fight)
            for index, reference in enumerate(list(ids)):
                fighter = self._resolve_event_fighter(reference or (entrants[index] if index < len(entrants) else "")) if reference or index < len(entrants) else None
                if fighter is None:
                    continue
                drug_failure = self.grand_prix_confirmed_drug_failure(fighter)
                unavailable = bool(getattr(fighter, "injured", 0)) or not self.fighter_available_for_date(fighter, event.get("month"), event.get("week"), event.get("day"))
                if not drug_failure and not unavailable:
                    continue
                reason = "confirmed drug failure" if drug_failure else "injury or medical unavailability"
                candidates = self._grand_prix_replacement_candidates(event, fight, fighter, excluded=ids)
                replacement = candidates[0] if candidates else None
                if replacement:
                    entrants[index] = replacement.name
                    ids[index] = replacement.fighter_id
                    notes.append(f"{fighter.name} was removed for {reason}; {replacement.name} entered the preserved tournament slot.")
                    continue
                note = self._grand_prix_postpone_event(event, f"{fighter.name} has {reason} and no eligible replacement was available.", [self._resolve_event_fighter(value) for value in ids if self._resolve_event_fighter(value)])
                return {"postponed": True, "reason": note, "notes": notes}
            fight["tournament_entrants"] = entrants
            fight["fighter_ids"] = ids
            if entrants:
                fight["fighters"] = [entrants[0], entrants[-1]]
            series = self.grand_prix_series_for_fight(fight)
            if series:
                series["advancing_ids"] = list(ids)
        return {"postponed": False, "notes": notes}

    def migrate_grand_prix_series(self):
        """Recover series rows from event metadata in older saves."""
        self.ensure_grand_prix_state()
        known = {str(row.get("series_id", "")) for row in self.grand_prix_series}
        for event in getattr(self, "scheduled_events", []) or []:
            for fight in event.get("fights", []) or []:
                if not isinstance(fight, dict) or not fight.get("tournament"):
                    continue
                series_id = str(fight.get("grand_prix_series_id", "") or "")
                if not series_id or series_id in known:
                    continue
                if fight.get("grand_prix_event_count", 1) in (None, 0, 1):
                    continue
                series = self._grand_prix_series_snapshot(event, fight)
                if series:
                    self.grand_prix_series.append(series)
                    known.add(series["series_id"])
                    fight["grand_prix_series_id"] = series["series_id"]
        return self.grand_prix_series
