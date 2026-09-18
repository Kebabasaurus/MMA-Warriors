"""Reproducible, isolated checkpoints for long-run observer audits.

The playable world owns all simulation rules.  This module only describes the
small amount of evidence needed to pause and resume an *isolated* audit world:
source/configuration identity, encoded ``random`` state, serialized world
state, and bounded report progress.  It deliberately does not import the
application or install hooks on live classes.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
from copy import deepcopy
from pathlib import Path
from uuid import uuid4


AUDIT_CHECKPOINT_SCHEMA_VERSION = 1

# These are deliberately conservative qualification gates for the disposable
# observer world.  They are not gameplay rules: a live save can sit outside a
# warning band, while a long-run audit should stop when a system has clearly
# lost its ability to replenish fighters, award titles, or retain bounded
# history.  Keeping the thresholds in one catalogue makes the audit report
# auditable and lets balancing work change a measured limit without changing
# simulation mechanics.
AUDIT_BALANCE_LIMITS = {
    "title_starvation_years": 2,
    "max_average_cash": 2_000_000_000,
    "cash_growth_multiple": 100,
    "cash_growth_floor": 100_000_000,
    "max_history_entries": 250_000,
    "free_agent_warning_floor": 20,
}


class AuditCheckpointError(ValueError):
    """Raised when a checkpoint cannot be trusted for the requested audit."""


# Keep this inventory explicit.  It is intentionally source-bound rather than
# a recursive directory walk that could silently omit a newly added runtime
# module or include transient audit output.
DEFAULT_SOURCE_PATHS = (
    "constants.py",
    "models.py",
    "main.py",
    "admin.py",
    "ui.py",
    "world.py",
    "events.py",
    "awards.py",
    "media.py",
    # ``views.py`` owns the public readers and several explicit management
    # boundaries used by the observer loop.  Keep it in the identity so a
    # checkpoint cannot be presented as current after those paths change.
    "views.py",
    "drug_testing_catalogue.py",
    "staff_management.py",
    "feature_foundation.py",
    "booking_workbench.py",
    "contract_batch_workbench.py",
    "fighter_traits.py",
    "persistence.py",
    "seeding.py",
    "fight_release.py",
    "fight_moves/release_registry.py",
    "play_level_audit.py",
)


def _canonical(value):
    """Return JSON-safe, deterministic data for identity comparisons."""

    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _json_digest(value):
    encoded = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_inventory(root, paths=None):
    """Hash the explicit runtime source inventory without mutating anything.

    Frozen distributions may not carry source files.  Such entries are marked
    ``missing`` instead of being silently dropped; a checkpoint made in that
    environment can only resume when the same inventory is presented.
    """

    root = Path(root).resolve()
    selected = tuple(paths or DEFAULT_SOURCE_PATHS)
    inventory = {}
    for raw in selected:
        relative = str(raw).replace("\\", "/")
        path = root.joinpath(*relative.split("/"))
        if not path.is_file():
            inventory[relative] = {"missing": True, "sha256": None, "size": None}
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        inventory[relative] = {"missing": False, "sha256": digest, "size": path.stat().st_size}
    return inventory


def build_audit_identity(*, seed, target_weeks, configuration=None, source_root=None,
                         source_paths=None, native_profile="release"):
    """Build the source/configuration identity required by a checkpoint."""

    inventory = source_inventory(source_root, source_paths) if source_root is not None else {}
    identity = {
        "schema_version": AUDIT_CHECKPOINT_SCHEMA_VERSION,
        "seed": int(seed),
        "target_weeks": max(1, int(target_weeks)),
        "native_profile": str(native_profile or "release"),
        "configuration": _canonical(configuration or {}),
        "source_inventory": inventory,
    }
    identity["source_digest"] = _json_digest(inventory)
    identity["identity_digest"] = _json_digest(identity)
    return identity


def encode_rng_state(state):
    """Encode a ``random.getstate()`` tuple using JSON-safe data only."""

    return base64.b64encode(
        json.dumps(_canonical(state), separators=(",", ":")).encode("utf-8")
    ).decode("ascii")


def _tupleify(value):
    if isinstance(value, list):
        return tuple(_tupleify(item) for item in value)
    return value


def decode_rng_state(encoded):
    """Decode and validate an RNG state without changing the process RNG."""

    if not isinstance(encoded, str) or not encoded:
        raise AuditCheckpointError("Checkpoint is missing its RNG state.")
    try:
        raw = json.loads(base64.b64decode(encoded.encode("ascii"), validate=True).decode("utf-8"))
        state = _tupleify(raw)
        # ``random.Random`` validates the shape without touching the module's
        # global generator.
        import random
        random.Random().setstate(state)
    except Exception as exc:
        raise AuditCheckpointError("Checkpoint RNG state is invalid.") from exc
    return state


def make_checkpoint(*, identity, completed_weeks, target_weeks, rng_state,
                     world_state, methods=None, snapshots=None,
                     output_cursor=None, status="paused",
                     time_limit_seconds=None, stop_reason=None):
    """Create a defensive checkpoint payload suitable for atomic persistence."""

    if not isinstance(identity, dict):
        raise AuditCheckpointError("Checkpoint identity must be an object.")
    target = max(1, int(target_weeks))
    completed = max(0, min(target, int(completed_weeks)))
    if not isinstance(world_state, dict):
        raise AuditCheckpointError("Checkpoint world state must be an object.")
    # Validate before creating a payload, but never alter the caller's RNG.
    encoded_rng = encode_rng_state(rng_state)
    decode_rng_state(encoded_rng)
    checkpoint = {
        "schema_version": AUDIT_CHECKPOINT_SCHEMA_VERSION,
        "status": str(status or "paused"),
        "identity": deepcopy(identity),
        "completed_weeks": completed,
        "target_weeks": target,
        "rng_state": encoded_rng,
        "world_state": deepcopy(world_state),
        "methods": deepcopy(methods or {}),
        "snapshots": deepcopy(snapshots or []),
        "output_cursor": deepcopy(output_cursor or {}),
    }
    # These fields are additive evidence for bounded runs.  Omitting them on
    # legacy/ordinary checkpoints keeps the historical shape valid while a
    # time-limited checkpoint can explain why it is resumable.
    if time_limit_seconds is not None:
        try:
            checkpoint["time_limit_seconds"] = max(0, int(float(time_limit_seconds)))
        except (TypeError, ValueError, OverflowError):
            checkpoint["time_limit_seconds"] = 0
    if stop_reason:
        checkpoint["stop_reason"] = str(stop_reason)
    return checkpoint


def validate_checkpoint(checkpoint, expected_identity):
    """Validate an on-disk checkpoint against the current source/configuration."""

    if not isinstance(checkpoint, dict):
        raise AuditCheckpointError("Checkpoint is not an object.")
    try:
        schema_version = int(checkpoint.get("schema_version", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise AuditCheckpointError("Checkpoint schema is invalid.") from exc
    if schema_version != AUDIT_CHECKPOINT_SCHEMA_VERSION:
        raise AuditCheckpointError("Checkpoint schema is not supported.")
    identity = checkpoint.get("identity")
    if not isinstance(identity, dict) or not isinstance(expected_identity, dict):
        raise AuditCheckpointError("Checkpoint identity is missing.")
    if _canonical(identity) != _canonical(expected_identity):
        raise AuditCheckpointError("Checkpoint source/configuration identity does not match the requested audit.")
    try:
        target = int(checkpoint.get("target_weeks"))
        completed = int(checkpoint.get("completed_weeks"))
    except (TypeError, ValueError) as exc:
        raise AuditCheckpointError("Checkpoint progress is invalid.") from exc
    expected_target = int(expected_identity.get("target_weeks", target) or target)
    if target != expected_target or completed < 0 or completed > target:
        raise AuditCheckpointError("Checkpoint progress does not match the requested target.")
    decode_rng_state(checkpoint.get("rng_state"))
    if not isinstance(checkpoint.get("world_state"), dict):
        raise AuditCheckpointError("Checkpoint world state is missing.")
    if not isinstance(checkpoint.get("methods", {}), dict) or not isinstance(checkpoint.get("snapshots", []), list):
        raise AuditCheckpointError("Checkpoint report progress is invalid.")
    return deepcopy(checkpoint)


def write_checkpoint_atomic(path, checkpoint):
    """Write one checkpoint atomically and clean temporary output on failure."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        payload = json.dumps(checkpoint, indent=2, sort_keys=True, ensure_ascii=False)
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_checkpoint(path):
    """Read a checkpoint without changing any application state."""

    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AuditCheckpointError(f"Could not read audit checkpoint: {path.name}") from exc
    return validate_checkpoint_shape(payload)


def validate_checkpoint_shape(payload):
    """Validate structural fields before a caller compares identity."""

    if not isinstance(payload, dict):
        raise AuditCheckpointError("Checkpoint is not an object.")
    try:
        schema_version = int(payload.get("schema_version", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise AuditCheckpointError("Checkpoint schema is invalid.") from exc
    if schema_version != AUDIT_CHECKPOINT_SCHEMA_VERSION:
        raise AuditCheckpointError("Checkpoint schema is not supported.")
    if not isinstance(payload.get("identity"), dict):
        raise AuditCheckpointError("Checkpoint identity is missing.")
    decode_rng_state(payload.get("rng_state"))
    if not isinstance(payload.get("world_state"), dict):
        raise AuditCheckpointError("Checkpoint world state is missing.")
    return deepcopy(payload)


def append_measurement(checkpoint, measurement, *, limit=200):
    """Append one bounded diagnostic row without retaining unbounded history."""

    result = validate_checkpoint_shape(checkpoint)
    rows = list(result.get("snapshots", []) or [])
    if isinstance(measurement, dict):
        rows.append(deepcopy(measurement))
    result["snapshots"] = rows[-max(1, int(limit)):]
    return result


def build_audit_measurement(world_state, *, year=None):
    """Build a read-only yearly measurement from one serialized audit world.

    The shape is deliberately descriptive rather than a balance verdict.  It
    keeps company/division cohorts visible, records operational backlogs and
    archive sizes, and leaves threshold decisions to the later qualification
    pass.  No model objects, RNG state or caller-owned dictionaries are
    changed.
    """

    state = world_state if isinstance(world_state, dict) else {}
    # Deadline evidence is projected from the serialized boundary only.  A
    # malformed or missing clock must not turn an old row into an invented
    # overdue commitment, and this reader never repairs the source envelope.
    def _boundary_number(value, *, minimum=0, maximum=10_000_000):
        if isinstance(value, bool) or value is None or value == "":
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError, OverflowError):
            return None
        return max(minimum, min(maximum, parsed))

    current_month = _boundary_number(state.get("month"), minimum=1)
    current_week = _boundary_number(state.get("week"), minimum=1, maximum=4)
    current_boundary = ((current_month - 1) * 4 + current_week) if current_month and current_week else None

    def _due_boundary(row, *, month_keys=("deadline_month",), week_keys=("deadline_week",), nested_keys=(), default_week=1):
        """Read one explicit month/week deadline without applying defaults."""
        if not isinstance(row, dict):
            return None
        candidate = row
        for key in nested_keys:
            value = candidate.get(key)
            if not isinstance(value, dict):
                return None
            candidate = value
        month = next((_boundary_number(candidate.get(key), minimum=1) for key in month_keys if key in candidate), None)
        if month is None:
            return None
        week = next((_boundary_number(candidate.get(key), minimum=1, maximum=4) for key in week_keys if key in candidate), default_week)
        if week is None:
            return None
        return (month - 1) * 4 + week

    def _is_active(row, terminal=()):
        if not isinstance(row, dict):
            return False
        status = str(row.get("status", "") or "").strip().casefold()
        return status not in {str(value).casefold() for value in terminal}

    overdue = {
        "super_event_offers": 0,
        "booking_proposals": 0,
        "locked_slot_proposals": 0,
        "medical_plans": 0,
        "media_plans": 0,
        "staff_briefs": 0,
        "owner_goals": 0,
        "career_promises": 0,
        "career_arcs": 0,
        "academy_promises": 0,
    }
    spectator_paused_owner_goals = 0

    def _record_overdue(bucket, row, *, month_keys=("deadline_month",), week_keys=("deadline_week",), nested_keys=(), terminal=(), default_week=1):
        if current_boundary is None or not _is_active(row, terminal=terminal):
            return
        due = _due_boundary(row, month_keys=month_keys, week_keys=week_keys, nested_keys=nested_keys, default_week=default_week)
        if due is not None and due < current_boundary:
            overdue[bucket] += 1

    # These rows are the saved commitment owners.  Keep the source-specific
    # buckets so a report can explain what is overdue instead of exposing only
    # one opaque total.
    top_offers = state.get("super_event_offers", []) if isinstance(state.get("super_event_offers"), list) else []
    for offer in top_offers:
        _record_overdue("super_event_offers", offer, terminal=("Completed", "Failed", "Cancelled", "Expired"), default_week=4)
    for raw in state.get("promotions", []) if isinstance(state.get("promotions"), list) else []:
        if not isinstance(raw, dict):
            continue
        for offer in raw.get("super_event_offers", []) if isinstance(raw.get("super_event_offers"), list) else []:
            _record_overdue("super_event_offers", offer, terminal=("Completed", "Failed", "Cancelled", "Expired"), default_week=4)

    booking = state.get("booking_workbench", {}) if isinstance(state.get("booking_workbench"), dict) else {}
    for proposal in booking.get("proposals", []) if isinstance(booking.get("proposals"), list) else []:
        _record_overdue("booking_proposals", proposal, month_keys=("target_month",), week_keys=("target_week",), terminal=("Committed", "Cancelled", "Completed", "Expired", "Rejected", "Replaced"))
    for proposal in booking.get("locked_slot_proposals", []) if isinstance(booking.get("locked_slot_proposals"), list) else []:
        _record_overdue("locked_slot_proposals", proposal, month_keys=("target_month",), week_keys=("target_week",), terminal=("Committed", "Cancelled", "Completed", "Expired", "Rejected", "Replaced"))
    for plan in booking.get("medical_plans", []) if isinstance(booking.get("medical_plans"), list) else []:
        _record_overdue("medical_plans", plan, month_keys=("target_month",), week_keys=("target_week",), terminal=("Committed", "Confirmed", "Cancelled", "Completed", "Expired", "Rejected", "Replaced"))

    media_plan = state.get("media_primary_plan")
    _record_overdue("media_plans", media_plan, month_keys=("month",), week_keys=("week",), nested_keys=("deadline",), terminal=("Completed", "Cancelled", "Replaced", "Expired"))

    staff_state_for_deadlines = state.get("staff_management") if isinstance(state.get("staff_management"), dict) else {}
    for brief in staff_state_for_deadlines.get("briefs", []) if isinstance(staff_state_for_deadlines.get("briefs"), list) else []:
        _record_overdue("staff_briefs", brief, month_keys=("month",), week_keys=("week",), nested_keys=("due",), terminal=("Completed", "Cancelled", "Expired", "Sealed"))

    for goal in state.get("owner_goals", []) if isinstance(state.get("owner_goals"), list) else []:
        # Spectator handoff intentionally stops player-owned objective work;
        # those rows remain retained legacy context, not overdue obligations
        # in the observer world. Keep a separate count so the audit remains
        # honest about what was paused without turning it into a failure.
        if bool(state.get("spectator_mode")):
            if _is_active(goal, terminal=("Complete", "Failed", "Cancelled", "Expired")):
                due = _due_boundary(goal, month_keys=("deadline",), week_keys=(), default_week=4)
                if current_boundary is not None and due is not None and due < current_boundary:
                    spectator_paused_owner_goals += 1
            continue
        # Owner objectives use a month-only deadline; an explicit deadline is
        # treated as the end of that month rather than inventing a week.
        _record_overdue("owner_goals", goal, month_keys=("deadline",), week_keys=(), terminal=("Complete", "Failed", "Cancelled", "Expired"), default_week=4)

    def _scan_fighter_commitments(fighter):
        if not isinstance(fighter, dict):
            return
        if fighter.get("main_event_promise") or fighter.get("top_opponent_promise"):
            _record_overdue("career_promises", fighter, month_keys=("promise_deadline_month",), week_keys=(), terminal=(), default_week=4)
        arc = fighter.get("career_arc")
        if isinstance(arc, dict):
            _record_overdue("career_arcs", arc, terminal=("completed", "failed", "cancelled", "expired"), default_week=4)

    for fighter in state.get("roster", []) if isinstance(state.get("roster"), list) else []:
        _scan_fighter_commitments(fighter)
    for raw in state.get("promotions", []) if isinstance(state.get("promotions"), list) else []:
        if not isinstance(raw, dict):
            continue
        for fighter in raw.get("roster", []) if isinstance(raw.get("roster"), list) else []:
            _scan_fighter_commitments(fighter)

    def _scan_academy(academy):
        if not isinstance(academy, dict):
            return
        prospects = academy.get("prospects", [])
        for prospect in prospects if isinstance(prospects, list) else []:
            promise = prospect.get("promise") if isinstance(prospect, dict) else None
            if not isinstance(promise, dict) or promise.get("fulfilled"):
                continue
            if current_boundary is None:
                continue
            due_week = _boundary_number(promise.get("deadline_week"), minimum=1)
            if due_week is not None and due_week < current_boundary:
                overdue["academy_promises"] += 1

    _scan_academy(state.get("academy"))
    for raw in state.get("promotions", []) if isinstance(state.get("promotions"), list) else []:
        if isinstance(raw, dict):
            _scan_academy(raw.get("academy"))
    overdue_total = min(1_000_000, sum(overdue.values()))
    companies = []
    division_counts = {}
    staff_total = 0
    staff_payroll_total = 0
    staff_salary_unknown = 0
    title_holders = 0
    title_history_entries = 0
    vacancy_count = 0
    vacancy_duration_total = 0
    vacancy_duration_max = 0
    expired_offer_count = 0
    eligible_title_challengers = 0
    cohort_measurements = {}
    event_counts = {
        "player_scheduled": 0,
        "ai_scheduled": 0,
        "owned_child_scheduled": 0,
        "owned_sport_scheduled": 0,
    }

    def _cohort_projection(label, roster, staff, scheduled):
        """Project active talent/division/event evidence for one cohort."""
        rows = roster if isinstance(roster, list) else []
        active_rows = [
            fighter for fighter in rows
            if isinstance(fighter, dict) and not fighter.get("retired")
        ]
        divisions = {}
        for fighter in active_rows:
            gender = str(fighter.get("gender", "Unknown") or "Unknown")
            weight = str(fighter.get("weight", "Unknown") or "Unknown")
            key = f"{gender}:{weight}"
            divisions[key] = divisions.get(key, 0) + 1
        staff_rows = staff if isinstance(staff, list) else []
        scheduled_rows = scheduled if isinstance(scheduled, list) else []
        return {
            "active_talent": len(active_rows),
            "roster_total": len(rows),
            "division_count": len(divisions),
            "division_counts": dict(sorted(divisions.items())),
            "staff": len(staff_rows),
            "scheduled_events": len(scheduled_rows),
        }

    def _identity_quality(rows, field):
        """Count missing/duplicate retained IDs without inventing identities."""
        values = []
        missing = 0
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                missing += 1
                continue
            value = str(row.get(field, "") or "").strip()
            if not value:
                missing += 1
                continue
            values.append(value)
        seen = set()
        duplicates = 0
        for value in values:
            if value in seen:
                duplicates += 1
            else:
                seen.add(value)
        return {"rows": len(rows) if isinstance(rows, list) else 0, "missing": missing, "duplicates": duplicates}

    def count_titles(mapping, history=None):
        """Count retained title lines without trusting their display labels."""
        nonlocal title_holders, title_history_entries, vacancy_count, vacancy_duration_total, vacancy_duration_max
        if isinstance(mapping, dict):
            title_holders += sum(1 for value in mapping.values() if str(value or "").strip())
        if isinstance(history, dict):
            title_history_entries += sum(
                len(entries) for entries in history.values() if isinstance(entries, list)
            )
            if isinstance(mapping, dict) and current_boundary is not None:
                for key, entries in history.items():
                    if str(mapping.get(key, "") or "").strip() or not isinstance(entries, list) or not entries:
                        continue
                    latest = entries[0] if isinstance(entries[0], dict) else {}
                    if str(latest.get("action", "") or "") not in {"Vacated", "Interim Vacated"}:
                        continue
                    month = _boundary_number(latest.get("month"), minimum=1)
                    week = _boundary_number(latest.get("week"), minimum=1, maximum=4)
                    if month is None or week is None:
                        match = re.search(r"Month\s+(\d+)\s+Week\s+(\d+)", str(latest.get("date", "") or ""))
                        if match:
                            month = _boundary_number(match.group(1), minimum=1)
                            week = _boundary_number(match.group(2), minimum=1, maximum=4)
                    if month is None or week is None:
                        continue
                    duration = max(0, current_boundary - ((month - 1) * 4 + week))
                    vacancy_count += 1
                    vacancy_duration_total = min(1_000_000, vacancy_duration_total + duration)
                    vacancy_duration_max = max(vacancy_duration_max, duration)

    def add_divisions(roster):
        for fighter in roster if isinstance(roster, list) else []:
            if not isinstance(fighter, dict) or fighter.get("retired"):
                continue
            gender = str(fighter.get("gender", "Unknown") or "Unknown")
            weight = str(fighter.get("weight", "Unknown") or "Unknown")
            key = f"{gender}:{weight}"
            division_counts[key] = division_counts.get(key, 0) + 1

    def division_projection(roster):
        result = {}
        for fighter in roster if isinstance(roster, list) else []:
            if not isinstance(fighter, dict) or fighter.get("retired"):
                continue
            gender = str(fighter.get("gender", "Unknown") or "Unknown")
            weight = str(fighter.get("weight", "Unknown") or "Unknown")
            key = f"{gender}:{weight}"
            result[key] = result.get(key, 0) + 1
        return dict(sorted(result.items()))

    def staff_payroll(rows):
        """Return bounded monthly Staff salary evidence without repairing rows."""
        nonlocal staff_salary_unknown
        total = 0
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                staff_salary_unknown += 1
                continue
            if "salary" not in row:
                staff_salary_unknown += 1
                continue
            raw_salary = row.get("salary")
            if isinstance(raw_salary, bool) or raw_salary is None or raw_salary == "":
                staff_salary_unknown += 1
                continue
            try:
                parsed = float(raw_salary)
            except (TypeError, ValueError, OverflowError):
                staff_salary_unknown += 1
                continue
            if not math.isfinite(parsed) or parsed < 0:
                staff_salary_unknown += 1
                continue
            total += min(1_000_000_000, max(0, int(parsed)))
        return min(1_000_000_000, total)

    def staff_salary_unknown_count(rows):
        count = 0
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                count += 1
                continue
            if "salary" not in row:
                count += 1
                continue
            raw_salary = row.get("salary")
            if isinstance(raw_salary, bool) or raw_salary is None or raw_salary == "":
                count += 1
                continue
            try:
                parsed = float(raw_salary)
            except (TypeError, ValueError, OverflowError):
                count += 1
                continue
            if not math.isfinite(parsed) or parsed < 0:
                count += 1
        return count

    def eligible_challenger_count(roster):
        """Apply the native record-based challenger gate to retained fighters."""
        count = 0
        for fighter in roster if isinstance(roster, list) else []:
            if not isinstance(fighter, dict) or fighter.get("retired") or fighter.get("champion"):
                continue
            try:
                wins = max(0, int(fighter.get("record_w", 0) or 0))
                losses = max(0, int(fighter.get("record_l", 0) or 0))
                streak = max(0, int(fighter.get("career_win_streak", 0) or 0))
            except (TypeError, ValueError, OverflowError):
                continue
            if wins >= 2 and (wins >= losses or streak >= 3):
                count += 1
        return count

    def count_challengers(roster):
        nonlocal eligible_title_challengers
        eligible_title_challengers += eligible_challenger_count(roster)

    def count_expired(rows):
        nonlocal expired_offer_count
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict) and str(row.get("status", "") or "").casefold() in {"expired", "expiry"}:
                expired_offer_count += 1

    player_roster = state.get("roster", []) if isinstance(state.get("roster"), list) else []
    player_staff = state.get("staff", []) if isinstance(state.get("staff"), list) else []
    player_scheduled = state.get("scheduled_events", []) if isinstance(state.get("scheduled_events"), list) else []
    cohort_measurements["player"] = _cohort_projection(
        "player", player_roster, player_staff, player_scheduled,
    )
    event_counts["player_scheduled"] = len(player_scheduled)
    staff_total += len(player_staff)
    staff_payroll_total += staff_payroll(player_staff)
    count_challengers(player_roster)
    count_expired(state.get("super_event_offers", []))
    count_expired(state.get("regional_invitations", []))
    for fighter in player_roster:
        add_divisions([fighter])
    ai_roster = []
    child_roster = []
    ai_staff = []
    child_staff = []
    ai_scheduled = []
    child_scheduled = []
    for raw in state.get("promotions", []) if isinstance(state.get("promotions"), list) else []:
        if not isinstance(raw, dict):
            continue
        roster = raw.get("roster", []) if isinstance(raw.get("roster"), list) else []
        staff = raw.get("staff", []) if isinstance(raw.get("staff"), list) else []
        scheduled_rows = raw.get("scheduled_events", []) if isinstance(raw.get("scheduled_events"), list) else []
        is_child = bool(raw.get("is_child_promotion"))
        if is_child:
            child_roster.extend(roster)
            child_staff.extend(staff)
            child_scheduled.extend(scheduled_rows)
        else:
            ai_roster.extend(roster)
            ai_staff.extend(staff)
            ai_scheduled.extend(scheduled_rows)
        staff_total += len(staff)
        company_staff_payroll = staff_payroll(staff)
        staff_payroll_total += company_staff_payroll
        add_divisions(roster)
        count_challengers(roster)
        finance = raw.get("finance", {}) if isinstance(raw.get("finance"), dict) else {}
        scheduled = raw.get("scheduled_events", []) if isinstance(raw.get("scheduled_events"), list) else []
        offers = raw.get("super_event_offers", []) if isinstance(raw.get("super_event_offers"), list) else []
        count_expired(offers)
        count_expired(raw.get("regional_invitations", []))
        companies.append({
            "promotion_id": str(raw.get("promotion_id", "") or ""),
            "name": str(raw.get("name", "") or ""),
            "active_roster": sum(1 for fighter in roster if isinstance(fighter, dict) and not fighter.get("retired")),
            "roster_total": len(roster),
            "division_counts": division_projection(roster),
            "eligible_title_challengers": eligible_challenger_count(roster),
            "cash": raw.get("cash", 0),
            "stability": raw.get("stability", 0),
            "staff": len(staff),
            "staff_payroll": company_staff_payroll,
            "staff_salary_unknown": staff_salary_unknown_count(staff),
            "scheduled_events": len(scheduled),
            "open_super_event_items": sum(1 for offer in offers if isinstance(offer, dict) and str(offer.get("status", "")) in {"Offered", "Planning", "Scheduled"}),
            "week_transactions": len(finance.get("week_transactions", []) or []) if isinstance(finance.get("week_transactions", []), list) else 0,
            "weekly_history": len(finance.get("weekly_history", []) or []) if isinstance(finance.get("weekly_history", []), list) else 0,
        })
        count_titles(raw.get("belts"), raw.get("belt_history"))
        count_titles(raw.get("interim_belts"))

    # The player promotion is represented at the top level, while child and AI
    # promotions are nested above.  Combat-sport circuits and player-owned
    # divisions use their own title maps, so include them in the same headline
    # count without attempting to resolve a fighter by name.
    count_titles(state.get("belts"), state.get("belt_history"))
    count_titles(state.get("interim_belts"))
    for sport, world in (state.get("combat_sport_worlds", {}) or {}).items() if isinstance(state.get("combat_sport_worlds"), dict) else []:
        if isinstance(world, dict):
            count_titles(world.get("titles"), world.get("title_history"))
    player_divisions = state.get("player_combat_divisions", {})
    if isinstance(player_divisions, dict):
        for sport_divisions in player_divisions.values():
            if not isinstance(sport_divisions, dict):
                continue
            for division in sport_divisions.values():
                if isinstance(division, dict):
                    count_titles(
                        division.get("titles", division.get("title_ids")),
                        division.get("title_history"),
                    )

    cohort_measurements["ai_promotions"] = _cohort_projection(
        "ai_promotions", ai_roster, ai_staff, ai_scheduled,
    )
    cohort_measurements["owned_child"] = _cohort_projection(
        "owned_child", child_roster, child_staff, child_scheduled,
    )
    event_counts["ai_scheduled"] = len(ai_scheduled)
    event_counts["owned_child_scheduled"] = len(child_scheduled)
    sport_scheduled = 0
    player_sport_divisions = state.get("player_combat_divisions", {})
    if isinstance(player_sport_divisions, dict):
        for sport_divisions in player_sport_divisions.values():
            if not isinstance(sport_divisions, dict):
                continue
            for division in sport_divisions.values():
                if isinstance(division, dict) and isinstance(division.get("scheduled_events"), list):
                    sport_scheduled += len(division.get("scheduled_events", []))
    event_counts["owned_sport_scheduled"] = min(1_000_000, sport_scheduled)

    fighter_identity_rows = []
    fighter_identity_rows.extend(player_roster)
    fighter_identity_rows.extend(state.get("free_agents", []) if isinstance(state.get("free_agents"), list) else [])
    fighter_identity_rows.extend(state.get("retired_fighters", []) if isinstance(state.get("retired_fighters"), list) else [])
    fighter_identity_rows.extend(ai_roster)
    fighter_identity_rows.extend(child_roster)
    promotion_rows = state.get("promotions", []) if isinstance(state.get("promotions"), list) else []
    event_identity_rows = list(player_scheduled) + list(ai_scheduled) + list(child_scheduled)
    for world in (state.get("combat_sport_worlds", {}) or {}).values() if isinstance(state.get("combat_sport_worlds"), dict) else []:
        if isinstance(world, dict) and isinstance(world.get("events"), list):
            event_identity_rows.extend(world.get("events", []))
    if isinstance(player_sport_divisions, dict):
        for sport_divisions in player_sport_divisions.values():
            if not isinstance(sport_divisions, dict):
                continue
            for division in sport_divisions.values():
                if isinstance(division, dict) and isinstance(division.get("scheduled_events"), list):
                    event_identity_rows.extend(division.get("scheduled_events", []))
    identity_quality = {
        "fighter_id": _identity_quality(fighter_identity_rows, "fighter_id"),
        "promotion_id": _identity_quality(promotion_rows, "promotion_id"),
        "event_id": _identity_quality(event_identity_rows, "event_id"),
    }

    foundation = state.get("foundation", {}) if isinstance(state.get("foundation"), dict) else {}
    historical = foundation.get("historical", {}) if isinstance(foundation.get("historical"), dict) else {}
    collections = historical.get("collections", {}) if isinstance(historical.get("collections"), dict) else {}
    membership = collections.get("membership", []) if isinstance(collections.get("membership"), list) else []
    booking = state.get("booking_workbench", {}) if isinstance(state.get("booking_workbench"), dict) else {}
    contract_batch = state.get("contract_batch_workbench", {}) if isinstance(state.get("contract_batch_workbench"), dict) else {}
    drug_testing = state.get("drug_testing_state", {}) if isinstance(state.get("drug_testing_state"), dict) else {}
    cases = drug_testing.get("cases", []) if isinstance(drug_testing.get("cases"), list) else []
    media_plans = state.get("media_primary_plan")
    # Staff management is a retained qualification ledger, not just a roster
    # count. Keep these metrics observational and bounded so the yearly audit
    # can qualify long-run evidence without repairing the saved state.
    staff_state = state.get("staff_management") if isinstance(state.get("staff_management"), dict) else {}
    raw_staff_work = staff_state.get("work_log", [])
    raw_staff_briefs = staff_state.get("briefs", [])
    raw_staff_exceptions = staff_state.get("exceptions", [])
    raw_staff_progression = staff_state.get("progression", {})
    staff_work_rows = raw_staff_work if isinstance(raw_staff_work, list) else []
    staff_brief_rows = raw_staff_briefs if isinstance(raw_staff_briefs, list) else []
    staff_exception_rows = raw_staff_exceptions if isinstance(raw_staff_exceptions, list) else []
    staff_progression_rows = raw_staff_progression if isinstance(raw_staff_progression, dict) else {}
    staff_malformed_evidence_rows = sum(
        1 for row in staff_work_rows + staff_brief_rows + staff_exception_rows
        if not isinstance(row, dict)
    )
    staff_malformed_evidence_rows += sum(
        1 for row in staff_progression_rows.values() if not isinstance(row, dict)
    )
    staff_malformed_evidence_rows += sum(
        1 for value in (raw_staff_work, raw_staff_briefs, raw_staff_exceptions)
        if not isinstance(value, list)
    )
    if not isinstance(raw_staff_progression, dict):
        staff_malformed_evidence_rows += 1
    staff_progression_credits = 0
    for row in staff_progression_rows.values():
        if isinstance(row, dict) and isinstance(row.get("credited_work_ids", []), list):
            staff_progression_credits += len(row.get("credited_work_ids", []))
    backlogs = {
        "scheduled_events": sum(item.get("scheduled_events", 0) for item in companies),
        "open_super_event_items": sum(item.get("open_super_event_items", 0) for item in companies),
        "booking_proposals": len(booking.get("proposals", []) or []) if isinstance(booking.get("proposals", []), list) else 0,
        "contract_batch_rows": len(contract_batch.get("rows", []) or []) if isinstance(contract_batch.get("rows", []), list) else 0,
        "testing_cases": len(cases),
        "membership_facts": len(membership),
        "media_plan_active": int(isinstance(media_plans, dict) and str(media_plans.get("status", "")) not in {"", "Cancelled", "Completed"}),
        "staff_work_log": len(staff_work_rows),
        "staff_briefs": len(staff_brief_rows),
        "staff_exceptions": len(staff_exception_rows),
        "staff_progression_rows": len(staff_progression_rows),
        "staff_progression_credits": staff_progression_credits,
        "staff_malformed_evidence_rows": staff_malformed_evidence_rows,
        "staff_payroll_total": staff_payroll_total,
        "staff_salary_unknown": staff_salary_unknown,
        "overdue_commitments": overdue_total,
        "overdue_commitment_breakdown": dict(overdue),
        "spectator_paused_owner_goals": spectator_paused_owner_goals,
    }
    archives = {
        "result_index": len(state.get("result_index", []) or []) if isinstance(state.get("result_index", []), list) else 0,
        "result_records": len(state.get("result_records", []) or []) if isinstance(state.get("result_records", []), list) else 0,
        "ai_event_archive": len(state.get("ai_event_archive", []) or []) if isinstance(state.get("ai_event_archive", []), list) else 0,
        "player_event_archive": len(state.get("player_event_archive", []) or []) if isinstance(state.get("player_event_archive", []), list) else 0,
        "event_log": len(state.get("event_log", []) or []) if isinstance(state.get("event_log", []), list) else 0,
    }
    regional_feeders = sum(
        1 for raw in state.get("promotions", [])
        if isinstance(raw, dict) and raw.get("is_regional_feeder")
    ) if isinstance(state.get("promotions"), list) else 0
    promotion_show_history = sum(
        len(raw.get("show_history", []) or [])
        for raw in state.get("promotions", [])
        if isinstance(raw, dict) and isinstance(raw.get("show_history", []), list)
    ) if isinstance(state.get("promotions"), list) else 0
    result_history = len(state.get("result_history", []) or []) if isinstance(state.get("result_history", []), list) else 0
    history_total = sum(archives.values()) + title_history_entries + promotion_show_history + result_history
    return {
        "measurement_year": None if year is None else int(year),
        "company_measurements": sorted(companies, key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("promotion_id", "")))),
        "cohort_measurements": deepcopy(cohort_measurements),
        "event_counts": dict(event_counts),
        "identity_quality": deepcopy(identity_quality),
        "division_counts": dict(sorted(division_counts.items())),
        "staff_total": staff_total,
        "title_holders": title_holders,
        "title_history_entries": title_history_entries,
        "free_agents": len(state.get("free_agents", []) or []) if isinstance(state.get("free_agents", []), list) else 0,
        "eligible_title_challengers": eligible_title_challengers,
        "title_vacancies": vacancy_count,
        "vacancy_duration_total_weeks": vacancy_duration_total,
        "vacancy_duration_max_weeks": vacancy_duration_max,
        "expired_offers": expired_offer_count,
        "regional_feeders": regional_feeders,
        "history_total": history_total,
        "backlogs": backlogs,
        "archive_sizes": archives,
    }


def build_calendar_timing_measurement(timings):
    """Summarise bounded native calendar-task timings without mutating them.

    The live calendar keeps only a small diagnostic ring.  Audit reporting
    projects that ring into stable per-task counts/totals/maxima and clamps
    malformed values so a timing row can never break a checkpoint or become a
    gameplay input.
    """

    by_task = {}
    count = 0
    total = 0.0
    maximum = 0.0
    rows = timings if isinstance(timings, (list, tuple)) else []
    for raw in rows[-200:]:
        if isinstance(raw, dict):
            label = str(raw.get("label", "") or "").strip()
            duration = raw.get("seconds", raw.get("duration", 0))
        elif isinstance(raw, (list, tuple)) and len(raw) >= 2:
            label = str(raw[0] or "").strip()
            duration = raw[1]
        else:
            continue
        if not label:
            label = "Unknown task"
        if isinstance(duration, bool):
            continue
        try:
            seconds = float(duration)
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(seconds) or seconds < 0:
            continue
        seconds = min(3_600.0, seconds)
        count += 1
        total = min(7_200.0, total + seconds)
        maximum = max(maximum, seconds)
        row = by_task.setdefault(label[:120], {"count": 0, "total_seconds": 0.0, "max_seconds": 0.0})
        row["count"] += 1
        row["total_seconds"] = min(7_200.0, row["total_seconds"] + seconds)
        row["max_seconds"] = max(row["max_seconds"], seconds)
    return {
        "count": count,
        "total_seconds": round(total, 6),
        "max_seconds": round(maximum, 6),
        "by_task": {
            label: {
                "count": int(row["count"]),
                "total_seconds": round(float(row["total_seconds"]), 6),
                "max_seconds": round(float(row["max_seconds"]), 6),
            }
            for label, row in sorted(by_task.items(), key=lambda item: item[0].casefold())
        },
    }


def audit_balance_findings(snapshots, *, target_years=None):
    """Return deterministic long-run balance findings from yearly snapshots.

    The function is a pure qualification pass over already-recorded evidence.
    It does not inspect model objects, repair a checkpoint, consume RNG, or
    infer a title/fighter from a display name.  ``severity=error`` findings are
    safe stopping conditions for the isolated audit; warnings remain visible in
    the report but do not interrupt a run.
    """

    rows = [row for row in snapshots if isinstance(row, dict)] if isinstance(snapshots, list) else []
    findings = []

    def add(code, severity, path, detail):
        findings.append({
            "code": str(code),
            "severity": str(severity),
            "path": str(path),
            "detail": str(detail),
        })

    def number(row, key, default=0.0):
        raw = row.get(key, default) if isinstance(row, dict) else default
        if isinstance(raw, bool):
            return float(default)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return float(default)

    if not rows:
        add("no_yearly_measurements", "error", "snapshots", "The audit produced no yearly boundary evidence.")
        return findings
    if target_years is not None:
        try:
            expected = max(1, int(target_years))
        except (TypeError, ValueError):
            expected = None
        if expected is not None and len(rows) < expected:
            add("incomplete_yearly_coverage", "warning", "snapshots", f"Recorded {len(rows)} yearly row(s); {expected} expected.")

    for index, row in enumerate(rows):
        path = f"snapshots[{index}]"
        active = number(row, "active")
        if active <= 0:
            add("roster_extinction", "error", f"{path}.active", "No active fighters remain in the observer world.")
        if number(row, "viable") <= 0:
            add("promotion_extinction", "error", f"{path}.viable", "No promotion remains both solvent and operational.")

    # A single titleless boundary can be a normal transition.  Two consecutive
    # titleless years indicate that the sporting ecosystem has stopped creating
    # or restoring championship lines.
    title_gap = 0
    title_start = None
    required_gap = int(AUDIT_BALANCE_LIMITS["title_starvation_years"])
    for index, row in enumerate(rows):
        if number(row, "title_holders") <= 0:
            title_gap += 1
            title_start = index if title_start is None else title_start
        else:
            title_gap = 0
            title_start = None
        if title_gap >= required_gap:
            add(
                "title_starvation", "error", f"snapshots[{title_start}:{index + 1}].title_holders",
                f"No active title holder was recorded for {title_gap} consecutive yearly boundaries.",
            )
            break

    initial_cash = max(0.0, number(rows[0], "avg_cash"))
    for index, row in enumerate(rows):
        average_cash = number(row, "avg_cash")
        runaway_by_cap = average_cash > float(AUDIT_BALANCE_LIMITS["max_average_cash"])
        runaway_by_growth = (
            initial_cash > 0
            and average_cash > initial_cash * float(AUDIT_BALANCE_LIMITS["cash_growth_multiple"])
            and average_cash > float(AUDIT_BALANCE_LIMITS["cash_growth_floor"])
        )
        if runaway_by_cap or runaway_by_growth:
            add("runaway_cash", "error", f"snapshots[{index}].avg_cash", f"Average promotion cash reached ${average_cash:,.0f} without a bounded equilibrium.")
            break

    for index, row in enumerate(rows):
        history_total = number(row, "history_total")
        if history_total > float(AUDIT_BALANCE_LIMITS["max_history_entries"]):
            add("unbounded_history_growth", "error", f"snapshots[{index}].history_total", f"Retained history reached {int(history_total):,} entries, above the {AUDIT_BALANCE_LIMITS['max_history_entries']:,} audit limit.")
            break

    final = rows[-1]
    if number(final, "free_agents") < float(AUDIT_BALANCE_LIMITS["free_agent_warning_floor"]):
        add("free_agent_starvation", "warning", "snapshots[-1].free_agents", f"Only {int(number(final, 'free_agents'))} free agents remain at the final boundary.")
    if number(final, "regional_feeders") <= 0:
        add("regional_feeder_shortage", "warning", "snapshots[-1].regional_feeders", "No regional feeder promotion remains in the final boundary.")
    return sorted(findings, key=lambda row: (row["severity"], row["code"], row["path"]))


def audit_measurement_evidence_findings(snapshots):
    """Validate that yearly rows carry the required diagnostic evidence.

    This is deliberately separate from balance policy.  Missing or malformed
    measurements are evidence-quality warnings, never reasons to mutate or
    auto-repair the isolated world.
    """

    rows = [row for row in snapshots if isinstance(row, dict)] if isinstance(snapshots, list) else []
    findings = []
    required_numeric = (
        "free_agents", "eligible_title_challengers", "title_vacancies",
        "vacancy_duration_total_weeks", "vacancy_duration_max_weeks", "expired_offers",
    )
    required_cohorts = ("player", "ai_promotions", "owned_child")
    required_cohort_numeric = (
        "active_talent", "roster_total", "division_count", "staff", "scheduled_events",
    )
    required_event_sources = (
        "player_scheduled", "ai_scheduled", "owned_child_scheduled", "owned_sport_scheduled",
    )
    required_identity_sources = ("fighter_id", "promotion_id", "event_id")

    def add(code, path, detail):
        findings.append({"code": str(code), "severity": "warning", "path": str(path), "detail": str(detail)})

    def nonnegative_number(value):
        if isinstance(value, bool) or value is None:
            return None
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            return None
        return value if math.isfinite(value) and value >= 0 else None

    for index, row in enumerate(rows):
        path = f"snapshots[{index}]"
        for key in required_numeric:
            if key not in row:
                add("missing_yearly_measurement", f"{path}.{key}", "Required L0 supply/title evidence is absent")
            elif nonnegative_number(row.get(key)) is None:
                add("invalid_yearly_measurement", f"{path}.{key}", "Required L0 supply/title evidence is not a finite non-negative number")
        total = nonnegative_number(row.get("vacancy_duration_total_weeks"))
        maximum = nonnegative_number(row.get("vacancy_duration_max_weeks"))
        if total is not None and maximum is not None and maximum > total:
            add("invalid_vacancy_duration", f"{path}.vacancy_duration_max_weeks", "Maximum vacancy duration exceeds the retained total")

        cohorts = row.get("cohort_measurements")
        if not isinstance(cohorts, dict):
            add("missing_cohort_measurements", f"{path}.cohort_measurements", "Yearly row has no player/AI/child cohort evidence")
        else:
            for cohort_key in required_cohorts:
                cohort_path = f"{path}.cohort_measurements.{cohort_key}"
                cohort = cohorts.get(cohort_key)
                if not isinstance(cohort, dict):
                    add("missing_cohort_measurements", cohort_path, "Cohort evidence is missing or not a mapping")
                    continue
                for key in required_cohort_numeric:
                    value = nonnegative_number(cohort.get(key))
                    if value is None:
                        add("invalid_cohort_measurement", f"{cohort_path}.{key}", "Cohort evidence is not a finite non-negative number")

        event_sources = row.get("event_counts")
        if not isinstance(event_sources, dict):
            add("missing_event_counts", f"{path}.event_counts", "Yearly row has no source-specific event coverage")
        else:
            for key in required_event_sources:
                if nonnegative_number(event_sources.get(key)) is None:
                    add("invalid_event_counts", f"{path}.event_counts.{key}", "Event coverage is not a finite non-negative number")

        identity_sources = row.get("identity_quality")
        if not isinstance(identity_sources, dict):
            add("missing_identity_quality", f"{path}.identity_quality", "Yearly row has no identity-quality evidence")
        else:
            for key in required_identity_sources:
                identity_path = f"{path}.identity_quality.{key}"
                evidence = identity_sources.get(key)
                if not isinstance(evidence, dict):
                    add("invalid_identity_quality", identity_path, "Identity-quality evidence is missing or not a mapping")
                    continue
                for metric in ("rows", "missing", "duplicates"):
                    if nonnegative_number(evidence.get(metric)) is None:
                        add("invalid_identity_quality", f"{identity_path}.{metric}", "Identity-quality count is not a finite non-negative number")

        timing = row.get("calendar_task_timings")
        if not isinstance(timing, dict):
            add("missing_calendar_task_timings", f"{path}.calendar_task_timings", "Yearly row has no bounded calendar timing summary")
            continue
        count = nonnegative_number(timing.get("count"))
        timing_total = nonnegative_number(timing.get("total_seconds"))
        timing_max = nonnegative_number(timing.get("max_seconds"))
        if count is None or timing_total is None or timing_max is None:
            add("invalid_calendar_task_timings", f"{path}.calendar_task_timings", "Timing summary contains malformed or non-finite values")
        elif timing_max > timing_total:
            add("invalid_calendar_task_timings", f"{path}.calendar_task_timings.max_seconds", "Maximum task duration exceeds the total")
        by_task = timing.get("by_task")
        if not isinstance(by_task, dict):
            add("invalid_calendar_task_timings", f"{path}.calendar_task_timings.by_task", "Per-task timing evidence is not a mapping")
    return sorted(findings, key=lambda row: (row["code"], row["path"], row["detail"]))


def audit_hard_invariant_findings(world_state):
    """Return deterministic, read-only hard-invariant findings for one boundary.

    This deliberately checks only evidence that is unambiguous in the saved
    package.  Balance observations (thin divisions, low cash, high decision
    rates) stay measurements and are never promoted to failures here.  Each
    finding includes a stable code/path so a stopped long-run audit can be
    investigated without mutating or auto-repairing its disposable world.
    """

    state = world_state if isinstance(world_state, dict) else {}
    findings = []

    def add(code, path, detail):
        findings.append({"code": str(code), "path": str(path), "detail": str(detail)})

    def rows_at(value):
        return value if isinstance(value, list) else []

    def first_identifier(row, keys):
        if not isinstance(row, dict):
            return ""
        for key in keys:
            value = str(row.get(key, "") or "").strip()
            if value:
                return value
        return ""

    def duplicate_rows(rows, path, keys, code):
        seen = {}
        for index, row in enumerate(rows_at(rows)):
            identifier = first_identifier(row, keys)
            if not identifier:
                continue
            prior = seen.get(identifier)
            if prior is not None:
                add(code, f"{path}[{index}]", f"{identifier!r} also occurs at {path}[{prior}]")
            else:
                seen[identifier] = index

    # Fighter ownership pools are the authoritative identity surfaces.  Empty
    # IDs remain legacy/unknown and are not guessed from mutable names.
    fighter_locations = []
    for field in ("roster", "free_agents", "retired_fighters"):
        fighter_locations.append((field, rows_at(state.get(field))))
    for promo_index, promotion in enumerate(rows_at(state.get("promotions"))):
        if isinstance(promotion, dict):
            fighter_locations.append((f"promotions[{promo_index}].roster", rows_at(promotion.get("roster"))))
    combat_worlds = state.get("combat_sport_worlds", {})
    if isinstance(combat_worlds, dict):
        for sport in sorted(combat_worlds, key=str):
            world = combat_worlds.get(sport)
            if isinstance(world, dict):
                fighter_locations.append((f"combat_sport_worlds[{sport!r}].roster", rows_at(world.get("roster"))))
    known_fighters = {}
    for path, rows in fighter_locations:
        for index, row in enumerate(rows):
            fighter_id = first_identifier(row, ("fighter_id",))
            if not fighter_id:
                continue
            prior = known_fighters.get(fighter_id)
            if prior is not None:
                add("duplicate_fighter_identity", f"{path}[{index}]", f"{fighter_id!r} also occurs at {prior}")
            else:
                known_fighters[fighter_id] = f"{path}[{index}]"

    # A transaction ID is unique within one ledger, while separate company
    # ledgers may legitimately start their local sequence at the same value.
    finance_sources = [("finance", state.get("finance"))]
    for promo_index, promotion in enumerate(rows_at(state.get("promotions"))):
        if isinstance(promotion, dict):
            finance_sources.append((f"promotions[{promo_index}].finance", promotion.get("finance")))
    for path, finance in finance_sources:
        if not isinstance(finance, dict):
            continue
        duplicate_rows(
            finance.get("week_transactions"), f"{path}.week_transactions",
            ("transaction_id", "id"), "duplicate_settlement_transaction",
        )

    duplicate_rows(state.get("result_index"), "result_index", ("key", "record_id", "event_id"), "duplicate_result_index")
    duplicate_rows(state.get("result_records"), "result_records", ("record_id",), "duplicate_result_record")

    foundation = state.get("foundation", {}) if isinstance(state.get("foundation"), dict) else {}
    historical = foundation.get("historical", {}) if isinstance(foundation.get("historical"), dict) else {}
    collections = historical.get("collections", {}) if isinstance(historical.get("collections"), dict) else {}
    duplicate_rows(collections.get("membership"), "foundation.historical.collections.membership", ("membership_id",), "duplicate_membership_fact")

    # Staff employment is an identity/obligation surface, not a balance
    # preference.  A long-run checkpoint must expose a missing or duplicated
    # employee instead of allowing a later expiry/market transfer to attach to
    # the wrong person.  Legacy rows without an ID are reported as unknown
    # evidence; this scan deliberately does not call a repair helper.
    staff_locations = []
    # Spectator handoff retains the former player roster in the top-level
    # ``staff`` field while also projecting the same employment rows into the
    # newly AI-managed promotion.  Those are two views of one employment
    # record, not two employees; scan the promotion-owned copy as canonical.
    # Active player saves do not have this projection and retain the ordinary
    # top-level scan.
    if not bool(state.get("spectator_mode")):
        staff_locations.append(("staff", rows_at(state.get("staff"))))
    staff_locations.append(("staff_candidates", rows_at(state.get("staff_candidates"))))
    for promo_index, promotion in enumerate(rows_at(state.get("promotions"))):
        if isinstance(promotion, dict):
            staff_locations.append((f"promotions[{promo_index}].staff", rows_at(promotion.get("staff"))))
    staff_ids = {}
    for path, staff_rows in staff_locations:
        for index, member in enumerate(staff_rows):
            member_path = f"{path}[{index}]"
            if not isinstance(member, dict):
                add("invalid_staff_record", member_path, "staff entry is not an object")
                continue
            staff_id = first_identifier(member, ("staff_id", "id"))
            if not staff_id:
                add("staff_missing_identity", member_path, "staff entry has no stable staff_id")
            else:
                prior = staff_ids.get(staff_id)
                if prior is not None:
                    add("duplicate_staff_identity", member_path, f"{staff_id!r} also occurs at {prior}")
                else:
                    staff_ids[staff_id] = member_path
            role = str(member.get("role", "") or "").strip()
            if not role:
                add("staff_missing_role", member_path, "staff entry has no role")
            for field in ("salary", "contract_months"):
                raw_value = member.get(field)
                if isinstance(raw_value, bool):
                    add("invalid_staff_term", f"{member_path}.{field}", f"{field} is boolean, not a numeric term")
                    continue
                try:
                    numeric = float(raw_value or 0)
                except (TypeError, ValueError):
                    add("invalid_staff_term", f"{member_path}.{field}", f"{field} is not numeric")
                    continue
                if numeric < 0:
                    add("negative_staff_term", f"{member_path}.{field}", f"{field} is below zero")

    # Staff work is an exactly-once evidence surface. A duplicate work or
    # operation identity can cause a retry to be charged twice, while a
    # progression credit with no retained work record cannot be audited. The
    # long-run scan reports these conditions without normalising the ledger or
    # invoking a Staff handler.
    staff_management = state.get("staff_management")
    if isinstance(staff_management, dict):
        raw_work_log = staff_management.get("work_log", [])
        work_rows = raw_work_log if isinstance(raw_work_log, list) else []
        if not isinstance(raw_work_log, list):
            add("invalid_staff_work_collection", "staff_management.work_log", "Staff work log is not a retained list")
        else:
            duplicate_rows(
                raw_work_log, "staff_management.work_log", ("work_id",),
                "duplicate_staff_work_id",
            )
            duplicate_rows(
                raw_work_log, "staff_management.work_log", ("operation_id",),
                "duplicate_staff_operation_id",
            )
            for index, row in enumerate(raw_work_log):
                path = f"staff_management.work_log[{index}]"
                if not isinstance(row, dict):
                    add("invalid_staff_work_record", path, "Staff work entry is not an object")
                    continue
                status = str(row.get("status", "") or "")
                if status in {"Executed", "Recommendation"}:
                    if not str(row.get("work_id", "") or "").strip():
                        add("staff_missing_work_id", f"{path}.work_id", "Completed Staff evidence has no durable work ID")
                    if not str(row.get("operation_id", "") or "").strip():
                        add("staff_missing_operation_id", f"{path}.operation_id", "Completed Staff evidence has no durable operation ID")
        raw_progression = staff_management.get("progression", {})
        progression = raw_progression if isinstance(raw_progression, dict) else {}
        if not isinstance(raw_progression, dict):
            add("invalid_staff_progression_collection", "staff_management.progression", "Staff progression ledger is not a mapping")
        known_work_ids = {
            str(row.get("work_id", "") or "").strip()
            for row in work_rows
            if isinstance(row, dict) and str(row.get("work_id", "") or "").strip()
        }
        for staff_id, row in progression.items():
            path = f"staff_management.progression[{staff_id!r}]"
            if not isinstance(row, dict):
                add("invalid_staff_progression_record", path, "Staff progression entry is not an object")
                continue
            credited = row.get("credited_work_ids", [])
            if not isinstance(credited, list):
                add("invalid_staff_progression_credits", f"{path}.credited_work_ids", "Credited work IDs are not a list")
                continue
            for index, work_id in enumerate(credited):
                work_id = str(work_id or "").strip()
                if work_id and work_id not in known_work_ids:
                    add(
                        "orphan_staff_progression_credit",
                        f"{path}.credited_work_ids[{index}]",
                        f"Progression references missing Staff work ID {work_id!r}",
                    )

    # Explicit remaining-* obligations are required to stay non-negative.  We
    # do not treat negative cash or other signed balances as an invariant.
    def walk_remaining(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if str(key).casefold().startswith("remaining_") and isinstance(child, (int, float)) and not isinstance(child, bool) and child < 0:
                    add("negative_remaining_obligation", child_path, f"remaining value {child} is below zero")
                walk_remaining(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk_remaining(child, f"{path}[{index}]")
    walk_remaining(state, "")

    # Keep scheduled references resolvable when a stable ID is present.  Legacy
    # name-only cards remain valid and are intentionally not fabricated here.
    scheduled_sources = [("scheduled_events", rows_at(state.get("scheduled_events")))]
    for promo_index, promotion in enumerate(rows_at(state.get("promotions"))):
        if isinstance(promotion, dict):
            scheduled_sources.append((f"promotions[{promo_index}].scheduled_events", rows_at(promotion.get("scheduled_events"))))
    divisions = state.get("player_combat_divisions", {})
    if isinstance(divisions, dict):
        for sport in sorted(divisions, key=str):
            sport_divisions = divisions.get(sport)
            if not isinstance(sport_divisions, dict):
                continue
            for division_key in sorted(sport_divisions, key=str):
                division = sport_divisions.get(division_key)
                if isinstance(division, dict):
                    scheduled_sources.append((f"player_combat_divisions[{sport!r}][{division_key!r}].scheduled_events", rows_at(division.get("scheduled_events"))))
    for sport in sorted(combat_worlds, key=str) if isinstance(combat_worlds, dict) else []:
        world = combat_worlds.get(sport)
        if isinstance(world, dict):
            scheduled_sources.append((f"combat_sport_worlds[{sport!r}].scheduled_events", rows_at(world.get("scheduled_events"))))

    event_ids = {}
    for path, events in scheduled_sources:
        for event_index, event in enumerate(events):
            if not isinstance(event, dict):
                continue
            event_id = first_identifier(event, ("event_id", "id"))
            if event_id:
                prior = event_ids.get(event_id)
                if prior is not None:
                    add("duplicate_scheduled_event", f"{path}[{event_index}]", f"{event_id!r} also occurs at {prior}")
                else:
                    event_ids[event_id] = f"{path}[{event_index}]"
            fights = rows_at(event.get("fights"))
            for fight_index, fight in enumerate(fights):
                if not isinstance(fight, dict):
                    continue
                references = []
                for key in ("a_id", "b_id", "fighter_id"):
                    value = str(fight.get(key, "") or "").strip()
                    if value:
                        references.append((key, value))
                for value in fight.get("fighter_ids", []) if isinstance(fight.get("fighter_ids"), list) else []:
                    value = str(value or "").strip()
                    if value:
                        references.append(("fighter_ids", value))
                for key, fighter_id in references:
                    if fighter_id not in known_fighters:
                        add("orphan_scheduled_fighter", f"{path}[{event_index}].fights[{fight_index}].{key}", f"fighter ID {fighter_id!r} is not present in a retained identity pool")

    # Child-loan lists are explicit ownership references and are safe to check
    # without guessing legacy name-only relationships.
    for promo_index, promotion in enumerate(rows_at(state.get("promotions"))):
        if not isinstance(promotion, dict):
            continue
        roster_ids = {first_identifier(row, ("fighter_id",)) for row in rows_at(promotion.get("roster"))}
        for index, fighter_id in enumerate(promotion.get("loaned_fighter_ids", []) if isinstance(promotion.get("loaned_fighter_ids"), list) else []):
            fighter_id = str(fighter_id or "").strip()
            if fighter_id and fighter_id not in roster_ids:
                add("orphan_loan_reference", f"promotions[{promo_index}].loaned_fighter_ids[{index}]", f"fighter ID {fighter_id!r} is not on that promotion's retained roster")

    return sorted(findings, key=lambda row: (row["code"], row["path"], row["detail"]))


def build_audit_report_accounting(methods, snapshots, completed_weeks, target_weeks):
    """Summarize report coverage and expose gaps before a qualification claim."""

    target = max(1, int(target_weeks))
    completed = max(0, int(completed_weeks))
    normalized_methods = {}
    errors = []
    for method, raw_count in (methods.items() if isinstance(methods, dict) else []):
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            errors.append(f"method {method!r} has a non-numeric count")
            continue
        if count < 0:
            errors.append(f"method {method!r} has a negative count")
            continue
        normalized_methods[str(method)] = count
    rows = [row for row in (snapshots if isinstance(snapshots, list) else []) if isinstance(row, dict)]
    expected_boundaries = completed // 48
    recorded_years = [row.get("year") for row in rows if row.get("year") is not None]
    if len(rows) != expected_boundaries:
        errors.append(f"expected {expected_boundaries} completed yearly boundary row(s), found {len(rows)}")
    if completed >= target and completed != target:
        errors.append(f"completed weeks {completed} exceed target {target}")
    total_fights = sum(normalized_methods.values())
    return {
        "completed_weeks": completed,
        "target_weeks": target,
        "complete": completed >= target and not errors,
        "method_fights": normalized_methods,
        "fights_total": total_fights,
        "snapshot_count": len(rows),
        "expected_year_boundaries": expected_boundaries,
        "recorded_years": recorded_years,
        "errors": errors,
    }
