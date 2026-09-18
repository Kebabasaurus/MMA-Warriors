"""Shared identity, work-envelope and historical-state contracts.

The management features are intentionally implemented on top of this small
foundation.  It keeps identifiers independent from display names/list order,
and makes retries safe when a save or a long-running workflow is interrupted.
The mixin is deliberately UI-free so it is safe to use from staging loads and
headless regression tests.
"""

from copy import deepcopy
import hashlib
import json
import re
from datetime import datetime, timezone


class FoundationMixin:
    FOUNDATION_SCHEMA_VERSION = 1
    _FOUNDATION_PREFIXES = {
        "promotion": "promo",
        "event": "event",
        "work": "work",
    }

    @staticmethod
    def _foundation_default_state():
        return {
            "schema_version": 1,
            "counters": {"promotion": 1, "event": 1, "work": 1},
            "player_promotion_id": "",
            "legacy_reference_map": {},
            "operations": {},
            "historical": {
                "schema_version": 1,
                "collections": {},
            },
        }

    def ensure_foundation_state(self, supplied=None):
        """Return a repaired, save-owned foundation state.

        Unknown future fields are retained.  Malformed mutable sections are
        replaced with empty compatible structures, which lets old saves load
        without making an unsafe assumption about their provenance.
        """
        state = supplied if supplied is not None else getattr(self, "_foundation_state", None)
        if not isinstance(state, dict):
            state = self._foundation_default_state()
        state.setdefault("schema_version", self.FOUNDATION_SCHEMA_VERSION)
        counters = state.get("counters")
        if not isinstance(counters, dict):
            counters = {}
            state["counters"] = counters
        for kind in self._FOUNDATION_PREFIXES:
            try:
                counters[kind] = max(1, int(counters.get(kind, 1) or 1))
            except (TypeError, ValueError):
                counters[kind] = 1
        if not isinstance(state.get("legacy_reference_map"), dict):
            state["legacy_reference_map"] = {}
        if not isinstance(state.get("operations"), dict):
            state["operations"] = {}
        historical = state.get("historical")
        if not isinstance(historical, dict):
            historical = {}
            state["historical"] = historical
        historical.setdefault("schema_version", 1)
        if not isinstance(historical.get("collections"), dict):
            historical["collections"] = {}
        self._foundation_state = state
        return state

    def _foundation_existing_ids(self, kind):
        prefix = self._FOUNDATION_PREFIXES[kind]
        pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
        values = set()
        if kind == "promotion":
            rows = getattr(self, "promotions", []) or []
            values.update(str(getattr(row, "promotion_id", "") or "") for row in rows)
            values.add(str(self.ensure_foundation_state().get("player_promotion_id", "") or ""))
        elif kind == "event":
            for row in self._foundation_event_rows():
                values.add(str(row.get("event_id", "") or ""))
        else:
            values.update(
                str(receipt.get("operation_id", ""))
                for receipt in self.ensure_foundation_state().get("operations", {}).values()
                if isinstance(receipt, dict)
            )
        return {value for value in values if pattern.match(value)}

    def _foundation_next_id(self, kind):
        state = self.ensure_foundation_state()
        prefix = self._FOUNDATION_PREFIXES[kind]
        counter = int(state["counters"].get(kind, 1) or 1)
        existing = self._foundation_existing_ids(kind)
        while f"{prefix}-{counter:06d}" in existing:
            counter += 1
        value = f"{prefix}-{counter:06d}"
        state["counters"][kind] = counter + 1
        return value

    def _foundation_company_reference(self, promotion=None, company_name=None):
        """Resolve a promotion name and durable ID without creating objects."""
        if promotion is not None and not isinstance(promotion, str):
            name = str(getattr(promotion, "name", "") or company_name or "")
            promotion_id = str(getattr(promotion, "promotion_id", "") or "")
            if name and not promotion_id:
                for row in getattr(self, "promotions", []) or []:
                    if getattr(row, "name", "") == name:
                        promotion_id = str(getattr(row, "promotion_id", "") or "")
                        break
            return name, promotion_id
        name = str(company_name or (promotion if isinstance(promotion, str) else "") or "")
        state = self.ensure_foundation_state()
        if name == str(getattr(self, "player_company_name", "") or ""):
            return name, str(state.get("player_promotion_id", "") or "")
        for row in getattr(self, "promotions", []) or []:
            if getattr(row, "name", "") == name:
                return name, str(getattr(row, "promotion_id", "") or "")
        return name, ""

    def record_membership_event(self, fighter, action, *, promotion=None, company_name=None,
                                event_id="", effective_month=None, effective_week=None,
                                precision="week", reason="", source_transaction=""):
        """Append one ID-linked company-membership fact to the history collection.

        This is an append-only historical adapter.  It never infers an old join
        date, mutates rosters, consumes RNG or allocates a Foundation counter.
        Repeated hooks for the same transition key return the original fact.
        """
        if fighter is None:
            return None
        ensure_ids = getattr(self, "ensure_foundation_ids", None)
        if callable(ensure_ids):
            ensure_ids()
        fighter_id = str(getattr(fighter, "fighter_id", "") or "").strip()
        if not fighter_id:
            return None
        action = str(action or "other").strip().lower() or "other"
        migration_precision = str(precision or "week").strip().lower() == "migration"
        if migration_precision and effective_month is None and effective_week is None:
            # A current roster can be known at the migration boundary without
            # inventing a historical join date.  Null dates plus the explicit
            # precision are consumed by future as-of readers as a coverage
            # boundary, not as a real contract start.
            month = week = None
        else:
            month = int(effective_month if effective_month is not None else getattr(self, "month", 0) or 0)
            week = int(effective_week if effective_week is not None else getattr(self, "week", 0) or 0)
        company, company_id = self._foundation_company_reference(promotion, company_name)
        event_id = str(event_id or "")
        source_transaction = str(source_transaction or "")
        identity_basis = {
            "fighter_id": fighter_id, "company_id": company_id,
            "company": company, "action": action, "event_id": event_id,
            "month": month, "week": week, "source_transaction": source_transaction,
        }
        digest = hashlib.sha256(json.dumps(identity_basis, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
        membership_id = f"membership-{digest}"
        state = self.ensure_foundation_state()
        rows = state["historical"]["collections"].setdefault("membership", [])
        if not isinstance(rows, list):
            rows = []
            state["historical"]["collections"]["membership"] = rows
        existing = next((row for row in rows if isinstance(row, dict) and row.get("membership_id") == membership_id), None)
        if existing is not None:
            return deepcopy(existing)
        normalized_week = None if week is None else max(0, min(4, week))
        fact = {
            "membership_id": membership_id,
            "event_id": event_id,
            "promotion_id": company_id,
            "promotion_name": company,
            "fighter_id": fighter_id,
            "fighter_name": str(getattr(fighter, "name", "") or ""),
            "action": action,
            "effective_month": max(0, month) if month is not None else None,
            "effective_week": normalized_week,
            "date_precision": str(precision or "week"),
            "reason": str(reason or ""),
            "source_transaction": source_transaction,
        }
        rows.append(fact)
        # Membership facts are the authoritative company-history ledger.  Keep
        # them append-only here; the 10,000-row value is a measured review
        # threshold, not permission to silently discard a fighter's past.
        # Any future compaction/sidecar policy must be explicit, recoverable
        # and separately versioned.
        state["historical"]["collections"]["membership"] = rows
        return deepcopy(fact)

    def migrate_current_membership_presence(self):
        """Record current roster presence without fabricating a join date.

        This one-time additive migration is intentionally conservative.  It
        captures only the rosters visible at the migration boundary, marks the
        date precision as ``migration`` and leaves both effective date fields
        null.  A later as-of index can therefore show a known-present boundary
        while refusing to claim when the fighter actually joined.
        """
        state = self.ensure_foundation_state()
        historical = state.setdefault("historical", {})
        migration = historical.setdefault("membership_migration", {})
        if int(migration.get("version", 0) or 0) >= 1:
            return 0
        ensure_ids = getattr(self, "ensure_foundation_ids", None)
        if callable(ensure_ids):
            ensure_ids()
        captured = 0

        def capture(roster, *, promotion=None, company_name=None, scope=""):
            nonlocal captured
            if not isinstance(roster, list):
                return
            for fighter in roster:
                fighter_id = str(getattr(fighter, "fighter_id", "") or "").strip()
                if not fighter_id:
                    continue
                source = f"migration:known-present:v1:{scope}:{fighter_id}"
                fact = self.record_membership_event(
                    fighter, "join", promotion=promotion, company_name=company_name,
                    precision="migration",
                    reason="Known present at migration; original join date is not recorded.",
                    source_transaction=source,
                )
                if fact:
                    captured += 1

        player_name = str(getattr(self, "player_company_name", "") or "").strip()
        if player_name and player_name.lower() != "spectator":
            capture(getattr(self, "roster", []), company_name=player_name, scope="player")
        for index, promotion in enumerate(getattr(self, "promotions", []) or [], 1):
            promotion_id = str(getattr(promotion, "promotion_id", "") or "").strip()
            scope = f"promotion:{promotion_id or getattr(promotion, 'name', '') or index}"
            capture(getattr(promotion, "roster", []), promotion=promotion, scope=scope)
        migration.update({"version": 1, "captured": captured})
        return captured

    def foundation_membership_events(self, *, promotion_id="", fighter_id="", action="",
                                     offset=0, limit=100):
        """Read membership facts by durable identity, preserving append order.

        This reader deliberately uses the raw saved envelope.  A page refresh
        must not normalise or replace a malformed historical section; callers
        receive an empty page and the retention diagnostic can explain the
        limitation without changing the save.
        """
        state = getattr(self, "_foundation_state", {})
        historical = state.get("historical", {}) if isinstance(state, dict) else {}
        collections = historical.get("collections", {}) if isinstance(historical, dict) else {}
        rows = collections.get("membership", []) if isinstance(collections, dict) else []
        if not isinstance(rows, list):
            return []
        wanted_promotion = str(promotion_id or "")
        wanted_fighter = str(fighter_id or "")
        wanted_action = str(action or "").lower()
        filtered = [row for row in rows if isinstance(row, dict)
                    and (not wanted_promotion or str(row.get("promotion_id", "")) == wanted_promotion)
                    and (not wanted_fighter or str(row.get("fighter_id", "")) == wanted_fighter)
                    and (not wanted_action or str(row.get("action", "")).lower() == wanted_action)]
        # Reader arguments are presentation inputs, not a repair boundary.
        # Malformed values must fail closed rather than turning a profile
        # refresh into an exception (or an unbounded slice).
        def bounded_int(value, fallback, low, high):
            if value is None or isinstance(value, bool):
                return fallback
            try:
                parsed = int(value)
            except (TypeError, ValueError, OverflowError):
                return fallback
            return max(low, min(high, parsed))

        start = bounded_int(offset, 0, 0, 10_000_000)
        size = bounded_int(limit, 100, 1, 1000)
        return deepcopy(filtered[start:start + size])

    def foundation_membership_event_count(self, *, promotion_id="", fighter_id="", action=""):
        """Count all retained membership facts without changing the envelope.

        The paged reader intentionally limits each response for UI
        responsiveness.  Summary cards that show a total must walk those
        pages instead of treating the first page as the complete count.
        """
        total = 0
        offset = 0
        while True:
            page = self.foundation_membership_events(
                promotion_id=promotion_id, fighter_id=fighter_id, action=action,
                offset=offset, limit=1000,
            )
            total += len(page)
            if len(page) < 1000:
                break
            offset += len(page)
        return total

    def foundation_membership_retention_summary(self):
        """Describe retained membership coverage without repairing the save.

        This is intentionally a diagnostic/read model for the J4 retention
        decision.  It reports the bounded in-save collection, migration-date
        gaps and duplicate IDs instead of silently trimming or inventing old
        facts.  A future sidecar/retention policy must use this evidence before
        changing the portable save contract.
        """
        raw = getattr(self, "_foundation_state", {})
        historical_raw = raw.get("historical") if isinstance(raw, dict) else None
        historical_available = isinstance(historical_raw, dict)
        collections = historical_raw.get("collections") if historical_available else None
        collection_available = historical_available and isinstance(collections, dict)
        membership_value = collections.get("membership", []) if collection_available else None
        membership_available = isinstance(membership_value, list)
        rows = membership_value if membership_available else []
        malformed_rows = sum(1 for row in rows if not isinstance(row, dict))
        ids = [str(row.get("membership_id", "") or "") for row in rows if isinstance(row, dict)]
        nonempty_ids = [item for item in ids if item]
        idless_rows = sum(1 for item in ids if not item)
        def valid_month(value):
            if value is None or isinstance(value, bool):
                return False
            return str(value).strip().lstrip("-").isdigit()

        # A non-null field is not automatically a valid date. Keep malformed
        # legacy values in the retained envelope, but classify them as
        # date-unknown so the diagnostic cannot imply trustworthy chronology.
        known_dates = [row for row in rows if isinstance(row, dict) and valid_month(row.get("effective_month"))]
        migration_rows = [row for row in rows if isinstance(row, dict) and str(row.get("date_precision", "")).lower() == "migration"]
        # Blank legacy identities are a coverage gap, not duplicate IDs. Only
        # repeated non-empty durable IDs are reported as an identity collision;
        # counting empty strings as duplicates would inflate this diagnostic
        # whenever an old row predates the membership ID field.
        duplicate_ids = len(nonempty_ids) - len(set(nonempty_ids))
        months = [int(row.get("effective_month")) for row in known_dates]
        within_limit = len(rows) <= 10000
        available = bool(collection_available and membership_available)
        coverage = "complete" if available else "unavailable"
        if not available:
            threshold_notice = (
                "Membership archive unavailable: the retained historical envelope "
                "is malformed; repair is limited to the load/migration boundary."
            )
        elif not within_limit:
            threshold_notice = "Review threshold exceeded; all membership facts are retained and can be paged."
        else:
            threshold_notice = ""
        return {
            "collection": "membership",
            "available": available,
            "coverage": coverage,
            "retained_rows": len(rows),
            "valid_rows": max(0, len(rows) - malformed_rows),
            "malformed_rows": malformed_rows,
            "retention_limit": 10000,
            "within_limit": within_limit,
            "threshold_notice": threshold_notice,
            "unique_membership_ids": len(set(nonempty_ids)),
            "duplicate_membership_ids": max(0, duplicate_ids),
            "idless_rows": idless_rows,
            "fighter_count": len({str(row.get("fighter_id", "") or "") for row in rows if isinstance(row, dict) and row.get("fighter_id")}),
            "company_count": len({str(row.get("promotion_id") or row.get("promotion_name") or "") for row in rows if isinstance(row, dict) and (row.get("promotion_id") or row.get("promotion_name"))}),
            "known_date_rows": len(known_dates),
            "unknown_date_rows": max(0, len(rows) - len(known_dates)),
            "migration_rows": len(migration_rows),
            "oldest_known_month": min(months) if months else None,
            "newest_known_month": max(months) if months else None,
        }

    def foundation_membership_intervals(self, *, fighter_id="", as_of_month=None,
                                        as_of_week=None, limit=100):
        """Derive bounded company intervals from recorded membership facts.

        Dates are compared only when both sides are known.  Migration presence
        rows therefore remain explicitly incomplete instead of being treated as
        a fabricated join date.  The method is a read model: it never repairs,
        sorts or mutates the underlying append-only facts.
        """
        # Read all pages so an archive beyond the review threshold still
        # produces a complete interval projection.  The public reader remains
        # bounded per page for UI responsiveness; this loop does not mutate or
        # reorder the save-owned collection.
        rows = []
        offset = 0
        while True:
            page = self.foundation_membership_events(fighter_id=fighter_id, offset=offset, limit=1000)
            rows.extend(page)
            if len(page) < 1000:
                break
            offset += len(page)
        open_intervals = {}
        intervals = []

        def stamp(row, prefix):
            return {
                f"{prefix}_month": row.get("effective_month"),
                f"{prefix}_week": row.get("effective_week"),
                f"{prefix}_precision": row.get("date_precision", "week"),
                # Keep the source facts attached to a derived interval.  The
                # interval is still a read model, but a profile reader can
                # now retain the authoritative membership/event identity
                # instead of falling back to a display-text fingerprint.
                f"{prefix}_membership_id": row.get("membership_id", ""),
                f"{prefix}_event_id": row.get("event_id", ""),
            }

        def key_for(row):
            return str(row.get("promotion_id") or row.get("promotion_name") or "")

        def date_stamp(month, week):
            if month is None or isinstance(month, bool):
                return None
            try:
                if isinstance(month, int):
                    parsed_month = month
                elif isinstance(month, str) and month.strip().lstrip("-").isdigit():
                    parsed_month = int(month.strip())
                else:
                    return None
                if week is None or isinstance(week, bool):
                    parsed_week = 0 if week is None else None
                elif isinstance(week, int):
                    parsed_week = week
                elif isinstance(week, str) and week.strip().lstrip("-").isdigit():
                    parsed_week = int(week.strip())
                else:
                    parsed_week = None
                if parsed_week is None:
                    return None
                return parsed_month, parsed_week
            except (TypeError, ValueError):
                return None

        def finish(key, row, *, inferred=False):
            interval = open_intervals.pop(key, None)
            if interval is None:
                interval = {
                    "promotion_id": row.get("promotion_id", ""),
                    "promotion_name": row.get("promotion_name", ""),
                    "fighter_id": row.get("fighter_id", ""),
                    "fighter_name": row.get("fighter_name", ""),
                    "start_month": None, "start_week": None,
                    "start_precision": "unknown",
                    "coverage": "incomplete",
                    "start_source": "",
                }
            interval.update(stamp(row, "end"))
            interval["end_source"] = row.get("source_transaction", "")
            if inferred:
                interval["coverage"] = "incomplete"
            start_month = interval.get("start_month")
            end_month = interval.get("end_month")
            start_stamp = date_stamp(start_month, interval.get("start_week"))
            end_stamp = date_stamp(end_month, interval.get("end_week"))
            if start_month is not None and end_month is not None and start_stamp and end_stamp:
                if end_stamp < start_stamp:
                    # Retained facts are authoritative, but a late import or
                    # malformed legacy row can put the recorded end before
                    # the recorded start. Keep both facts and make the
                    # contradiction explicit instead of displaying a normal
                    # interval or silently sorting the append-only ledger.
                    interval["coverage"] = "incomplete"
                    interval["temporal_order"] = "conflict"
                    interval["coverage_note"] = (
                        "Recorded end precedes recorded start; source facts "
                        "were retained without reordering."
                    )
                else:
                    interval["temporal_order"] = "ordered"
            elif (start_month is not None and not start_stamp) or (end_month is not None and not end_stamp):
                interval["coverage"] = "incomplete"
                interval["temporal_order"] = "unknown"
                interval["coverage_note"] = "A retained membership date is malformed; the source fact remains available for audit."
            elif interval.get("start_month") is None or interval.get("end_month") is None:
                interval["temporal_order"] = "unknown"
            intervals.append(interval)

        for row in rows:
            action = str(row.get("action", "") or "").lower()
            key = key_for(row)
            if not key:
                continue
            if action in {"leave", "loan"}:
                finish(key, row, inferred=key not in open_intervals)
                continue
            if action not in {"join", "return"}:
                continue
            if key in open_intervals:
                # A repeated open state has no new interval boundary; retain
                # the first fact and let the source transaction explain it.
                continue
            interval = {
                "promotion_id": row.get("promotion_id", ""),
                "promotion_name": row.get("promotion_name", ""),
                "fighter_id": row.get("fighter_id", ""),
                "fighter_name": row.get("fighter_name", ""),
                "coverage": "incomplete" if row.get("date_precision") == "migration" else "complete",
                "start_source": row.get("source_transaction", ""),
                "temporal_order": "unknown" if row.get("effective_month") is None else "open",
            }
            interval.update(stamp(row, "start"))
            open_intervals[key] = interval
        intervals.extend(
            dict(interval, end_month=None, end_week=None, end_precision="open", end_source="")
            for interval in open_intervals.values()
        )

        if as_of_month is not None:
            def bounded_int(value, fallback, low, high):
                if value is None or isinstance(value, bool):
                    return fallback
                try:
                    parsed = int(value)
                except (TypeError, ValueError, OverflowError):
                    return fallback
                return max(low, min(high, parsed))

            target_month = bounded_int(as_of_month, 0, 0, 1_000_000)
            target_week = bounded_int(as_of_week, 0, 0, 4)

            def at_or_before(month, week):
                if month is None:
                    return True
                stamp = date_stamp(month, week)
                return stamp is None or stamp <= (target_month, target_week)

            def on_or_before(month, week):
                if month is None:
                    return False
                stamp = date_stamp(month, week)
                return stamp is not None and stamp <= (target_month, target_week)

            intervals = [
                interval for interval in intervals
                if interval.get("temporal_order") == "conflict"
                or (
                    at_or_before(interval.get("start_month"), interval.get("start_week"))
                    and not on_or_before(interval.get("end_month"), interval.get("end_week"))
                )
            ]
        # Keep a generous safety cap while allowing the caller to inspect a
        # complete long-career projection.  Normal UI callers request a small
        # page; this cap is not a retention policy and never drops stored facts.
        result_limit = 100
        if limit is not None and not isinstance(limit, bool):
            try:
                result_limit = int(limit)
            except (TypeError, ValueError, OverflowError):
                result_limit = 100
        result_limit = max(1, min(100000, result_limit))
        return deepcopy(intervals[:result_limit])

    def _foundation_event_rows(self):
        """Yield each persisted event dictionary once, preserving save order."""
        rows = []
        seen = set()

        def add(values):
            if not isinstance(values, list):
                return
            for value in values:
                if isinstance(value, dict) and id(value) not in seen:
                    seen.add(id(value))
                    rows.append(value)

        add(getattr(self, "scheduled_events", []))
        for promotion in getattr(self, "promotions", []) or []:
            add(getattr(promotion, "scheduled_events", []))
        for division in (getattr(self, "player_combat_divisions", {}) or {}).values():
            if isinstance(division, dict):
                add(division.get("scheduled_events", []))
                add(division.get("events", []))
        for world in (getattr(self, "combat_sport_worlds", {}) or {}).values():
            if isinstance(world, dict):
                add(world.get("scheduled_events", []))
                add(world.get("events", []))
        return rows

    def ensure_foundation_ids(self):
        """Migrate missing promotion/event identities exactly once per row.

        A legacy reference key is based on its explicit collection path and
        ordinal.  It is only a migration aid; all runtime references use the
        generated ID after this function runs. Existing non-empty IDs are
        preserved, and duplicate generated IDs are repaired deterministically.
        """
        state = self.ensure_foundation_state()
        mapping = state["legacy_reference_map"]
        assigned = {"promotion": 0, "event": 0}

        promotions = getattr(self, "promotions", []) or []
        used_promotions = set()
        for index, promotion in enumerate(promotions, 1):
            current = str(getattr(promotion, "promotion_id", "") or "")
            key = f"promotions[{index}]"
            if not current or current in used_promotions:
                current = str(mapping.get(key, "") or "")
                if not current or current in used_promotions:
                    current = self._foundation_next_id("promotion")
                    mapping[key] = current
                    assigned["promotion"] += 1
                promotion.promotion_id = current
            used_promotions.add(current)

        # The player company is represented by top-level fields rather than a
        # Promotion instance in the live app. Give it the same durable identity
        # without manufacturing a second roster object.
        if hasattr(self, "player_company_name"):
            player_id = str(state.get("player_promotion_id", "") or "")
            if not player_id or player_id in used_promotions:
                player_id = self._foundation_next_id("promotion")
                state["player_promotion_id"] = player_id

        used_events = set()
        for ordinal, event in enumerate(self._foundation_event_rows(), 1):
            current = str(event.get("event_id", "") or "")
            key = f"events[{ordinal}]"
            if not current or current in used_events:
                current = str(mapping.get(key, "") or "")
                if not current or current in used_events:
                    current = self._foundation_next_id("event")
                    mapping[key] = current
                    assigned["event"] += 1
                event["event_id"] = current
            used_events.add(current)

        # Fights inside an event are a separate identity layer from the event
        # itself.  Older saves often have only list positions, which is enough
        # for a read-only display but unsafe for an editable workbench.  Assign
        # deterministic IDs from the already-stable event ID and ordinal; never
        # draw randomness or use a Python object/list index as a durable key.
        self.ensure_booking_ids()

        if assigned["promotion"] or assigned["event"]:
            state.setdefault("migration", {})["last_assignment"] = {
                "promotions": assigned["promotion"],
                "events": assigned["event"],
            }
        return assigned

    def ensure_booking_ids(self):
        """Assign stable IDs to draft/scheduled fight rows in a save-owned graph.

        Existing IDs are retained, including IDs authored by a newer build.
        Legacy rows receive an event-scoped identity (or a clearly labelled
        draft identity) and duplicate IDs are repaired deterministically. The
        method is intentionally separate from the foundation counter contract:
        booking IDs are namespaced by their owning event and therefore do not
        consume a global counter or alter the historical promotion/event/work
        counter shape.
        """
        assigned = 0
        seen_fights = set()
        used_ids = set()

        def assign_fight(fight, owner, ordinal):
            nonlocal assigned
            if not isinstance(fight, dict) or id(fight) in seen_fights:
                return
            seen_fights.add(id(fight))
            current = str(fight.get("booking_id", "") or "").strip()
            if not current or current in used_ids:
                current = f"booking:{owner}:{ordinal}"
                suffix = 2
                candidate = current
                while candidate in used_ids:
                    candidate = f"{current}:{suffix}"
                    suffix += 1
                current = candidate
                fight["booking_id"] = current
                assigned += 1
            used_ids.add(current)

        # Player draft card has no event owner until it is scheduled.
        for ordinal, fight in enumerate(getattr(self, "booked", []) or [], 1):
            assign_fight(fight, "draft", ordinal)

        for event_ordinal, event in enumerate(self._foundation_event_rows(), 1):
            event_id = str(event.get("event_id", "") or f"legacy-event-{event_ordinal}")
            fights = event.get("fights", [])
            if not isinstance(fights, list):
                continue
            for ordinal, fight in enumerate(fights, 1):
                assign_fight(fight, event_id, ordinal)
        return assigned

    def foundation_quote(self, domain, action, target_id, *, amount=0, currency="USD", details=None):
        """Create an observational quote; this function never mutates state."""
        return {
            "domain": str(domain),
            "action": str(action),
            "target_id": str(target_id),
            "amount": int(amount or 0),
            "currency": str(currency),
            "details": dict(details or {}),
            "quoted_at": datetime.now(timezone.utc).isoformat(),
        }

    def foundation_get_receipt(self, operation_key):
        state = self.ensure_foundation_state()
        receipt = state["operations"].get(str(operation_key))
        return deepcopy(receipt) if isinstance(receipt, dict) else None

    def foundation_record_work(self, operation_key, *, domain, action, target_id="", status="committed", result=None, error="", quote=None):
        """Record one durable work receipt and return a copy.

        Reusing an operation key returns the original receipt. This is the
        idempotency boundary used by UI retries and save/load recovery.
        """
        state = self.ensure_foundation_state()
        key = str(operation_key or "").strip()
        if not key:
            raise ValueError("operation_key is required")
        existing = state["operations"].get(key)
        if isinstance(existing, dict) and existing.get("status") != "failed":
            return deepcopy(existing)
        previous_attempt = int(existing.get("attempt", 0) or 0) if isinstance(existing, dict) else 0
        receipt = {
            "operation_id": self._foundation_next_id("work"),
            "operation_key": key,
            "domain": str(domain),
            "action": str(action),
            "target_id": str(target_id or ""),
            "status": str(status),
            "result": deepcopy(result),
            "error": str(error or ""),
            "quote": deepcopy(quote) if isinstance(quote, dict) else None,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "attempt": previous_attempt + 1,
        }
        state["operations"][key] = receipt
        return deepcopy(receipt)

    def foundation_commit(self, operation_key, *, domain, action, target_id="", quote=None,
                          validate=None, apply=None, expected_revision=None,
                          current_revision=None, snapshot=None, restore=None):
        """Validate and apply one operation with an idempotent receipt.

        ``validate`` and ``apply`` are domain-owned callbacks. Callers that
        mutate more than the foundation state may provide ``snapshot`` and
        ``restore`` callbacks; a failed apply then restores the complete domain
        transaction. No RNG is touched by this coordinator.
        """
        key = str(operation_key or "").strip()
        if not key:
            raise ValueError("operation_key is required")
        prior = self.foundation_get_receipt(key)
        if prior is not None and prior.get("status") != "failed":
            return prior
        if expected_revision is not None and current_revision is not None and expected_revision != current_revision:
            return self.foundation_record_work(
                key, domain=domain, action=action, target_id=target_id,
                status="stale", error="Target changed since the quote was read.", quote=quote,
            )
        snapshot_value = None
        try:
            if callable(validate):
                verdict = validate()
                if verdict is False:
                    return self.foundation_record_work(
                        key, domain=domain, action=action, target_id=target_id,
                        status="rejected", error="Validation rejected the operation.", quote=quote,
                    )
                if isinstance(verdict, tuple) and verdict and verdict[0] is False:
                    return self.foundation_record_work(
                        key, domain=domain, action=action, target_id=target_id,
                        status="rejected", error=str(verdict[1] if len(verdict) > 1 else "Validation rejected the operation."), quote=quote,
                    )
            snapshot_value = snapshot() if callable(snapshot) else None
            result = apply() if callable(apply) else None
            return self.foundation_record_work(
                key, domain=domain, action=action, target_id=target_id,
                status="committed", result=result, quote=quote,
            )
        except Exception as exc:
            if snapshot_value is not None and callable(restore):
                restore(snapshot_value)
            return self.foundation_record_work(
                key, domain=domain, action=action, target_id=target_id,
                status="failed", error=f"{type(exc).__name__}: {exc}", quote=quote,
            )

    def foundation_commit_rows(self, operation_key, rows, *, domain, action, row_id=None,
                               quote=None, validate=None, apply=None):
        """Commit independent rows, retaining successes and retrying only gaps."""
        receipts = []
        for index, row in enumerate(rows or [], 1):
            identifier = row_id(row, index) if callable(row_id) else index
            child_key = f"{operation_key}:{identifier}"
            row_quote = quote(row, index) if callable(quote) else quote
            row_validate = (lambda row=row, index=index: validate(row, index)) if callable(validate) else None
            row_apply = (lambda row=row, index=index: apply(row, index)) if callable(apply) else None
            receipts.append(self.foundation_commit(
                child_key, domain=domain, action=action, target_id=str(identifier),
                quote=row_quote, validate=row_validate, apply=row_apply,
            ))
        return receipts

    def foundation_append_historical(self, collection, fact, *, max_items=10000):
        """Append a bounded historical fact to the save-owned archive."""
        state = self.ensure_foundation_state()
        name = str(collection or "history")
        collections = state["historical"]["collections"]
        rows = collections.setdefault(name, [])
        if not isinstance(rows, list):
            rows = []
            collections[name] = rows
        rows.append(deepcopy(fact))
        collections[name] = rows[-max(1, int(max_items or 1)):]
        return deepcopy(collections[name][-1])

    def foundation_historical_page(self, collection, *, offset=0, limit=100):
        state = self.ensure_foundation_state()
        rows = state["historical"]["collections"].get(str(collection or ""), [])
        if not isinstance(rows, list):
            return []
        start = max(0, int(offset or 0))
        size = max(1, min(1000, int(limit or 100)))
        return deepcopy(rows[start:start + size])

    # Company proposals deliberately live beside (rather than inside) the
    # transfer/loan domain objects.  A proposal is a reviewable decision
    # record; it is not a second ownership model.  Each status transition is
    # append-only, so a reload can show the original terms and the terminal
    # outcome without rerunning a negotiation or reconstructing a stale deal
    # from today's rosters.
    def create_company_proposal(self, kind, *, source_company="", source_company_id="",
                                target_company="", target_company_id="",
                                fighters=None, costs=None, expiry=None,
                                warnings=None, terms=None, reason=""):
        """Create one stable, identity-linked company proposal snapshot.

        This method is called only from an explicit player action.  It never
        mutates rosters, belts, contracts, finance or RNG.  Repeating the
        same proposal inputs at the same calendar boundary returns the same
        durable proposal ID and does not append another draft transition.
        """
        fighters = [dict(item) for item in (fighters or []) if isinstance(item, dict)]
        costs = dict(costs or {})
        expiry = dict(expiry or {})
        warnings = [str(item) for item in (warnings or []) if str(item)]
        terms = dict(terms or {})
        basis = {
            "kind": str(kind or "company_transfer"),
            "source_company": str(source_company or ""),
            "source_company_id": str(source_company_id or ""),
            "target_company": str(target_company or ""),
            "target_company_id": str(target_company_id or ""),
            "fighters": fighters,
            "costs": costs,
            "expiry": expiry,
            "terms": terms,
            "month": int(getattr(self, "month", 0) or 0),
            "week": int(getattr(self, "week", 0) or 0),
        }
        digest = hashlib.sha256(json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
        proposal_id = f"proposal-{digest}"
        state = self.ensure_foundation_state()
        rows = state["historical"]["collections"].setdefault("company_proposals", [])
        if not isinstance(rows, list):
            rows = []
            state["historical"]["collections"]["company_proposals"] = rows
        existing = next((row for row in reversed(rows)
                         if isinstance(row, dict) and row.get("proposal_id") == proposal_id), None)
        if existing is not None:
            return deepcopy(existing)
        record = {
            "proposal_id": proposal_id,
            "proposal_revision": 1,
            "kind": str(kind or "company_transfer"),
            "status": "draft",
            "source_company": str(source_company or ""),
            "source_company_id": str(source_company_id or ""),
            "target_company": str(target_company or ""),
            "target_company_id": str(target_company_id or ""),
            "fighters": deepcopy(fighters),
            "costs": deepcopy(costs),
            "expiry": deepcopy(expiry),
            "warnings": list(warnings),
            "terms": deepcopy(terms),
            "reason": str(reason or ""),
            "outcome": "",
            "error": "",
            "created_month": int(getattr(self, "month", 0) or 0),
            "created_week": int(getattr(self, "week", 0) or 0),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        rows.append(record)
        state["historical"]["collections"]["company_proposals"] = rows[-10000:]
        return deepcopy(record)

    def update_company_proposal(self, proposal_id, status, *, outcome="", error="",
                                terms=None, warnings=None, reason=""):
        """Append a proposal status transition without changing its snapshot."""
        proposal_id = str(proposal_id or "").strip()
        if not proposal_id:
            return None
        state = self.ensure_foundation_state()
        rows = state["historical"]["collections"].setdefault("company_proposals", [])
        if not isinstance(rows, list):
            rows = []
            state["historical"]["collections"]["company_proposals"] = rows
        current = next((row for row in reversed(rows)
                        if isinstance(row, dict) and row.get("proposal_id") == proposal_id), None)
        if current is None:
            return None
        next_status = str(status or current.get("status", "draft"))
        # Terminal proposal evidence is append-only and immutable.  A second
        # click may arrive with a different UI message or stale terms; it must
        # return the original terminal row rather than manufacture a new
        # outcome.  ``needs_review`` is intentionally recoverable so an
        # explicit player correction can still move a proposal forward.
        terminal_statuses = {"committed", "rejected", "withdrawn", "expired", "failed", "cancelled"}
        if str(current.get("status", "") or "").strip().lower() in terminal_statuses:
            return deepcopy(current)
        next_terms = deepcopy(current.get("terms", {})) if isinstance(current.get("terms"), dict) else {}
        if isinstance(terms, dict):
            next_terms.update(deepcopy(terms))
        next_warnings = list(current.get("warnings", [])) if isinstance(current.get("warnings"), list) else []
        if warnings:
            next_warnings.extend(str(item) for item in warnings if str(item))
            next_warnings = list(dict.fromkeys(next_warnings))
        revision = max(1, int(current.get("proposal_revision", 1) or 1)) + 1
        transition = deepcopy(current)
        transition.update({
            "proposal_revision": revision,
            "status": next_status,
            "terms": next_terms,
            "warnings": next_warnings,
            "outcome": str(outcome or current.get("outcome", "")),
            "error": str(error or ""),
            "reason": str(reason or current.get("reason", "")),
            "updated_month": int(getattr(self, "month", 0) or 0),
            "updated_week": int(getattr(self, "week", 0) or 0),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })
        # Reusing the same terminal status/reason is an idempotent retry, not
        # a new transition.  Preserve the first terminal evidence exactly.
        if (str(current.get("status", "")) == next_status
                and str(current.get("outcome", "")) == str(outcome or current.get("outcome", ""))
                and str(current.get("error", "")) == str(error or "")):
            return deepcopy(current)
        rows.append(transition)
        state["historical"]["collections"]["company_proposals"] = rows[-10000:]
        return deepcopy(transition)

    def company_proposal_read_model(self, *, proposal_id="", statuses=None, limit=100):
        """Return latest proposal snapshots as defensive, UI-safe cards."""
        # This is a reader over an append-only review ledger.  Do not invoke
        # ``ensure_foundation_state`` here: opening/refreshing the proposal
        # window must leave malformed legacy history untouched for the
        # sanctioned load/migration boundary.
        raw_state = getattr(self, "_foundation_state", {})
        historical = raw_state.get("historical", {}) if isinstance(raw_state, dict) else {}
        collections = historical.get("collections", {}) if isinstance(historical, dict) else {}
        rows = collections.get("company_proposals", []) if isinstance(collections, dict) else []
        if not isinstance(rows, list):
            return []
        latest = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = str(row.get("proposal_id", "") or "")
            if key:
                latest[key] = row
        wanted_id = str(proposal_id or "")
        wanted_statuses = {str(item).lower() for item in (statuses or ())}
        cards = []
        for row in latest.values():
            if wanted_id and str(row.get("proposal_id", "")) != wanted_id:
                continue
            status = str(row.get("status", "draft") or "draft").lower()
            if wanted_statuses and status not in wanted_statuses:
                continue
            card = deepcopy(row)
            card["status_label"] = {
                "draft": "Draft", "submitted": "Submitted", "countered": "Countered",
                "accepted_pending_terms": "Awaiting fighter terms", "committed": "Completed",
                "rejected": "Rejected", "withdrawn": "Withdrawn", "expired": "Expired",
                "needs_review": "Needs review", "failed": "Failed",
            }.get(status, status.replace("_", " ").title())
            cards.append(card)
        cards.sort(key=lambda row: (str(row.get("recorded_at", "")), str(row.get("proposal_id", ""))), reverse=True)
        return deepcopy(cards[:max(1, min(1000, int(limit or 100)))])

    @staticmethod
    def foundation_work_read_model(receipt):
        """Return a display-safe work card without exposing mutable state."""
        receipt = receipt if isinstance(receipt, dict) else {}
        status = str(receipt.get("status", "unknown") or "unknown").lower()
        labels = {
            "committed": "Completed", "rejected": "Needs attention", "stale": "Needs review",
            "failed": "Failed", "in_progress": "In progress", "draft": "Draft",
        }
        result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
        quote = receipt.get("quote") if isinstance(receipt.get("quote"), dict) else {}

        def nonnegative_int(value):
            try:
                if isinstance(value, bool) or value is None or value == "":
                    raise ValueError
                return max(0, int(value)), True
            except (TypeError, ValueError):
                return 0, False

        attempt, attempt_known = nonnegative_int(receipt.get("attempt", 0))
        amount, amount_known = nonnegative_int(quote.get("amount", 0))
        actual_spend, actual_known = nonnegative_int(result.get("spend", result.get("cost", 0)))
        diagnostics = []
        if "attempt" in receipt and not attempt_known:
            diagnostics.append("attempt is malformed")
        if "amount" in quote and not amount_known:
            diagnostics.append("quoted amount is malformed")
        if "spend" in result and not actual_known:
            diagnostics.append("actual spend is malformed")
        if "cost" in result and "spend" not in result and not actual_known:
            diagnostics.append("actual cost is malformed")

        return {
            "operation_id": str(receipt.get("operation_id", "") or ""),
            "operation_key": str(receipt.get("operation_key", "") or ""),
            "domain": str(receipt.get("domain", "") or ""),
            "action": str(receipt.get("action", "") or ""),
            "target_id": str(receipt.get("target_id", "") or ""),
            "status": status,
            "status_label": labels.get(status, status.replace("_", " ").title()),
            # Numeric fields stay bounded for existing callers, while the
            # companion state/diagnostic fields make a coerced zero visibly
            # different from a genuine zero in long-run readers.
            "attempt": attempt,
            "attempt_state": "Recorded" if attempt_known else "Unknown",
            "amount": amount,
            "amount_state": "Recorded" if amount_known else "Unknown",
            "actual_spend": actual_spend,
            "actual_spend_state": "Recorded" if actual_known else "Unknown",
            "diagnostics": diagnostics,
            "error": str(receipt.get("error", "") or ""),
            "evidence_key": str(result.get("evidence_key", "") or ""),
            "recorded_at": str(receipt.get("recorded_at", "") or ""),
        }

    def foundation_work_cards(self, *, domain=None, statuses=None, limit=100):
        """Read operation receipts as stable cards; never repair or mutate state."""
        raw = getattr(self, "_foundation_state", {})
        operations = raw.get("operations", {}) if isinstance(raw, dict) else {}
        wanted_domain = str(domain or "")
        wanted_statuses = {str(value).lower() for value in (statuses or ())}
        rows = []
        for receipt in operations.values() if isinstance(operations, dict) else ():
            card = self.foundation_work_read_model(receipt)
            if wanted_domain and card["domain"] != wanted_domain:
                continue
            if wanted_statuses and card["status"] not in wanted_statuses:
                continue
            rows.append(card)
        rows.sort(key=lambda row: (row.get("recorded_at", ""), row.get("operation_id", "")), reverse=True)
        return deepcopy(rows[:max(1, min(1000, int(limit or 100)))])

    def foundation_work_summary(self, *, domain=None):
        cards = self.foundation_work_cards(domain=domain, limit=1000)
        counts = {}
        for card in cards:
            counts[card["status"]] = counts.get(card["status"], 0) + 1
        return {"total": len(cards), "counts": counts}
