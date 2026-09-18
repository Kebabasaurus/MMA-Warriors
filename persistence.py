import json
import gzip
import logging
import math
import os
import platform
import random
import re
import shutil
import stat
import sys
import threading
import traceback
from collections import Counter
from copy import deepcopy
from datetime import datetime
from logging.handlers import RotatingFileHandler
from uuid import uuid4
import tkinter as tk
from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion
from fight_moves.release_registry import (
    normalize_release_move_mastery as normalize_move_mastery,
    normalize_release_signature_moves as normalize_signature_moves,
)
from fighter_portraits.identity import ensure_portrait_identity
from replay_storage import ReplayLines, defer_replay_rows, pinned_replay_roots, split_replay_rows
from universe_validation import validate_universe_section as shared_validate_universe_section


LOGGER = logging.getLogger("mma_warriors")
_CRASH_APP = None

FIGHTER_SAVE_FIELDS = tuple(field.name for field in fields(Fighter))
GYM_SAVE_FIELDS = tuple(field.name for field in fields(Gym))
PROMOTION_SAVE_FIELDS = tuple(field.name for field in fields(Promotion))

# Career arcs were renamed after the first public builds.  Keep the mapping
# deliberately explicit: ordinary loading still leaves a healthy save alone,
# while the Game & Saves migration action can opt in to a one-time, backed-up
# rewrite.  Case-folded aliases make hand-edited legacy files safe without
# changing unknown authored values.
CAREER_ARCHETYPE_MIGRATION_VERSION = 1
CAREER_ARCHETYPE_ALIASES = {
    "standard prime": "Balanced Development",
    "early peak": "Early Maturation",
    "late developer": "Late Maturation",
    "late maturation": "Late Maturation",
    "long prime": "Durable Career",
    "durable career": "Durable Career",
    "early maturation": "Early Maturation",
    "balanced development": "Balanced Development",
}


def migrate_serialized_career_archetypes(data):
    """Return a copied save payload with known legacy arc labels normalised.

    This is intentionally a pure, identity-preserving transformation.  It
    walks every retained fighter row (including promotion and child-sport
    rosters), records exact source paths for the audit entry, and leaves
    unknown values untouched.  The live loader does not call it; the explicit
    Game & Saves action owns the backed-up migration boundary.
    """
    if not isinstance(data, dict):
        raise ValueError("Career-archetype migration requires a save object.")
    migrated = deepcopy(data)
    changes = []

    def walk(value, path):
        if isinstance(value, dict):
            if "career_archetype" in value:
                old = value.get("career_archetype")
                token = str(old or "").strip()
                replacement = CAREER_ARCHETYPE_ALIASES.get(token.casefold(), old)
                if replacement != old:
                    value["career_archetype"] = replacement
                    changes.append({
                        "path": f"{path}.career_archetype" if path else "career_archetype",
                        "from": old,
                        "to": replacement,
                    })
            for key, nested in list(value.items()):
                walk(nested, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(migrated, "")
    return migrated, changes


def load_model_row(row, model_type, field_names, context):
    """Create one save model with an actionable compatibility error.

    Saves from newer builds may carry fields this executable does not yet know.
    Those fields are ignored rather than crashing load; malformed required data
    remains a clear transactional load failure.
    """
    if not isinstance(row, dict):
        raise ValueError(f"{context} must be an object, not {type(row).__name__}.")
    allowed = set(field_names)
    unknown = sorted(set(row) - allowed)
    if unknown:
        LOGGER.warning("Ignoring forward-compatible fields in %s: %s", context, ", ".join(unknown[:8]))
    filtered = {name: value for name, value in row.items() if name in allowed}
    required = [field.name for field in fields(model_type) if field.default is MISSING and field.default_factory is MISSING]
    missing = [name for name in required if name not in filtered]
    if missing:
        raise ValueError(f"{context} is missing required field(s): {', '.join(missing)}.")
    try:
        value = model_type(**filtered)
        if model_type is Fighter:
            value.style = normalize_mma_style(getattr(value, "style", ""))
            value.secondary_style = normalize_secondary_style(
                getattr(value, "secondary_style", ""), value.style,
            )
            value.signature_moves = normalize_signature_moves(getattr(value, "signature_moves", []))
            value.move_mastery = normalize_move_mastery(getattr(value, "move_mastery", {}))
            value.move_mastery_last_month = max(0, int(getattr(value, "move_mastery_last_month", 0) or 0))
            if not isinstance(getattr(value, "career_signature_stats", None), dict):
                value.career_signature_stats = {}
            if not isinstance(getattr(value, "career_move_family_stats", None), dict):
                value.career_move_family_stats = {}
            if value.trait not in TRAITS:
                value.trait = "Gym Rat"
            if value.trait_injury_baseline is None:
                value.trait_injury_baseline = value.trait
            if not isinstance(value.trait_progress, dict):
                value.trait_progress = {}
            if not isinstance(value.trait_history, list):
                value.trait_history = []
            if value.behaviour not in BEHAVIOURS:
                value.behaviour = "Dynamic Attacker"
            if value.stance not in ("Orthodox", "Southpaw", "Switch"):
                value.stance = "Orthodox"
        return value
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} could not be loaded: {exc}") from exc


def model_field_dict(value, field_names):
    """Serialize declared dataclass fields without asdict's expensive deep copy."""
    source = getattr(value, "__dict__", {})
    return {name: source[name] if name in source else getattr(value, name) for name in field_names}


def serialize_fighter_model(fighter):
    return model_field_dict(fighter, FIGHTER_SAVE_FIELDS)


def serialize_gym_model(gym):
    return model_field_dict(gym, GYM_SAVE_FIELDS)


def serialize_promotion_model(promotion):
    data = model_field_dict(promotion, PROMOTION_SAVE_FIELDS)
    data["roster"] = [serialize_fighter_model(fighter) for fighter in getattr(promotion, "roster", [])]
    return data


def _crash_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def atomic_write_text(path, contents):
    """Write a file without leaving partial JSON after a power loss or crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(contents, encoding="utf-8")
    os.replace(temporary, path)


def atomic_write_json(path, data):
    atomic_write_text(path, json.dumps(data, indent=2))


def atomic_write_json_compact(path, data):
    """Atomic compact JSON for runtime saves; editable databases stay indented."""
    atomic_write_text(path, json.dumps(data, separators=(",", ":")))


def atomic_write_json_gzip(path, data, compresslevel=6):
    """Atomically write a compressed JSON backup/autosave."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        # Use the accelerated encoder once, but bound encoded byte buffers.
        # Token-by-token json.dump is substantially slower for career archives.
        payload = json.dumps(data, separators=(",", ":"))
        with temporary.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=max(1, min(9, int(compresslevel)))) as compressed:
                for offset in range(0, len(payload), 1_048_576):
                    compressed.write(payload[offset:offset + 1_048_576].encode("utf-8"))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _make_path_writable(path):
    """Clear Windows read-only attributes before removing user save folders."""
    try:
        path = Path(path)
        path.chmod(path.stat().st_mode | stat.S_IWRITE)
    except OSError:
        pass


def _remove_readonly_path(func, path, _exc_info):
    """Retry a failed rmtree operation after making the affected path writable."""
    _make_path_writable(path)
    func(path)


def remove_save_folder(path):
    """Remove a save slot even when an autosave folder was marked read-only."""
    path = Path(path)
    if not path.exists():
        return
    for item in sorted(path.rglob("*"), key=lambda candidate: len(candidate.parts), reverse=True):
        _make_path_writable(item)
    _make_path_writable(path)
    shutil.rmtree(path, onerror=_remove_readonly_path)


def read_json_text(path):
    path = Path(path)
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


EXTERNAL_SAVE_BLOCK_KEYS = (
    "roster", "free_agents", "promotions", "combat_sport_worlds",
    "result_index", "result_records", "ai_event_archive", "player_event_archive",
    "season_stats", "event_log",
)


def hydrate_external_save_blocks(path, data):
    """Load gzip sidecar blocks back into the normal save payload shape."""
    path = Path(path)
    blocks = data.pop("_external_blocks", {}) or {}
    if not isinstance(blocks, dict):
        return data
    block_root = (path.parent / "DataBlocks").resolve()
    for key, relative in blocks.items():
        if key not in EXTERNAL_SAVE_BLOCK_KEYS:
            continue
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError(f"External save block {key!r} has no valid relative path.")
        relative_path = Path(relative)
        if relative_path.is_absolute() or any(part == ".." for part in relative_path.parts):
            raise ValueError(f"External save block {key!r} uses an unsafe path.")
        block_path = (path.parent / relative_path).resolve()
        try:
            block_path.relative_to(block_root)
        except ValueError as exc:
            raise ValueError(f"External save block {key!r} escapes the save DataBlocks folder.") from exc
        if block_path.name != f"{key}.json.gz" or block_path.parent.parent != block_root:
            raise ValueError(f"External save block {key!r} has an invalid generated filename.")
        data[key] = json.loads(read_json_text(block_path))
        if key in ("result_records", "ai_event_archive", "player_event_archive"):
            data[key] = defer_replay_rows(data[key], block_path.parent)
    return data


def load_save_payload(path):
    """Read either a legacy single-file save or the split primary+blocks format."""
    path = Path(path)
    payload = json.loads(read_json_text(path))
    if not isinstance(payload, dict):
        raise ValueError("Save payload is not a valid JSON object.")
    return hydrate_external_save_blocks(path, payload)


# Career conversion deliberately has a narrower contract than a normal save.
# The destination is a new-start database: identity, ratings, records, roster
# ownership and current supported contracts remain playable, while live time,
# money, scheduled work and narrative archives are reset or moved to a labelled
# companion manifest.  Keep this list explicit so a newly-added save field
# cannot disappear silently during conversion.
CAREER_CONVERSION_SUPPORTED_FIELDS = frozenset({
    "player_company_name", "spectator_mode", "active_save_name", "active_save_group",
    "last_spectator_snapshot_year", "player_region", "player_reputation",
    "company_show_personality", "theme_name", "company_pop", "company_stability",
    "company_safety", "company_milestone_progress", "super_event_offers",
    "super_event_history", "super_event_project", "regional_invitations",
    "regional_invitation_history", "roster", "free_agents",
    "promotions", "combat_sport_worlds", "player_combat_divisions",
    "standings_history", "regions", "gyms", "change_journal", "result_index",
    "independent_showcase_counter", "retired_fighters", "media_companies",
    "media_market_history", "media_market_last_month", "engine_settings",
    "business_settings", "staff", "staff_candidates", "staff_management",
    "booking_workbench", "contract_batch_workbench", "scouting", "scouting_reports",
    "scouting_searches", "scouting_shortlist", "scouting_watchlists",
    "scouting_decision_packs", "scouting_history", "scouting_knowledge",
    "scouting_alert_state", "scouting_quarantined_reports", "achievement_log",
    "historical_records", "fanbase", "academy", "inbox_hidden_types", "owner_goals",
    "belts", "interim_belts", "special_belts", "belt_history", "closed_divisions",
    "player_managed_divisions", "rules", "broadcasters", "weight_classes",
    "post_show_bonuses", "news", "world_chronicle", "story_threads",
    "story_subscriptions", "relationship_cases", "defunct_promotions", "season_stats",
    "awards_history", "fight_timer_delay", "foundation", "grand_prix_series",
})

# Values in these fields are useful evidence, but must never be treated as
# already-completed work in a fresh playable world.
CAREER_CONVERSION_HISTORY_FIELDS = (
    "result_history", "result_records", "ai_event_archive", "player_event_archive",
    "result_index", "event_log", "change_journal", "world_chronicle", "story_threads",
    "story_subscriptions", "relationship_cases", "news", "season_stats", "awards_history",
    "historical_records", "belt_history", "scouting_history",
    "regional_invitation_history",
)

# These are live obligations or mutable progress and make the conversion
# explicitly incomplete when populated.  Their exact values are copied into
# the companion manifest for audit/recovery rather than silently dropped.
CAREER_CONVERSION_ONGOING_FIELDS = (
    "scheduled_events", "pending_rebookings", "booking_workbench",
    "contract_batch_workbench", "super_event_project", "super_event_offers",
    "regional_invitations",
    "grand_prix_series",
    "scouting_searches", "inbox", "owner_goals",
)


def _conversion_value_count(value):
    if value is None or value is False or value == "" or value == 0:
        return 0
    if isinstance(value, (dict, list, tuple, set)):
        return len(value)
    return 1


def _conversion_json_safe(value):
    """Flatten deferred replay rows and model-like values for manifests."""
    if isinstance(value, ReplayLines):
        return list(value)
    if isinstance(value, dict):
        return {str(key): _conversion_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_conversion_json_safe(item) for item in value]
    if hasattr(value, "__dict__") and value.__class__.__name__ in {"Fighter", "Gym", "Promotion"}:
        return _conversion_json_safe(vars(value))
    return value


def _conversion_fighter_rows(data):
    """Yield (scope, row) pairs without treating cross-view aliases as errors."""
    for key in ("roster", "free_agents", "retired_fighters"):
        for index, row in enumerate(data.get(key, []) or [], 1):
            if isinstance(row, dict):
                yield f"{key}[{index}]", row
    for index, promotion in enumerate(data.get("promotions", []) or [], 1):
        if not isinstance(promotion, dict):
            continue
        for fighter_index, row in enumerate(promotion.get("roster", []) or [], 1):
            if isinstance(row, dict):
                yield f"promotions[{index}].roster[{fighter_index}]", row
    for sport, sport_world in (data.get("combat_sport_worlds", {}) or {}).items():
        if not isinstance(sport_world, dict):
            continue
        for index, row in enumerate(sport_world.get("roster", []) or [], 1):
            if isinstance(row, dict):
                yield f"combat_sport_worlds.{sport}.roster[{index}]", row


def career_conversion_preflight(data):
    """Return structured, read-only conversion issues for one serialized world.

    The helper intentionally accepts a plain mapping so tests and editor tools
    can validate a staged payload without a Tk app or any RNG/state mutation.
    """
    if not isinstance(data, dict):
        return [{
            "severity": "error", "entity": "world", "field": "payload",
            "evidence": f"expected an object, received {type(data).__name__}",
            "remedy": "Load a valid career save before converting.",
        }]
    issues = []
    unknown = sorted(set(data) - CAREER_CONVERSION_SUPPORTED_FIELDS - {
        "cash", "month", "week", "finance", "inbox", "scheduled_events",
        "pending_rebookings", "result_history", "result_records", "ai_event_archive",
        "player_event_archive", "event_log", "database_name", "_save_meta",
    })
    for field in unknown:
        issues.append({
            "severity": "error", "entity": "world", "field": field,
            "evidence": "field is not in the conversion schema and would be excluded",
            "remedy": "Add a versioned field policy before converting this save.",
        })

    promotions = [row for row in data.get("promotions", []) or [] if isinstance(row, dict)]
    promotion_names = {str(row.get("name", "")).strip() for row in promotions if row.get("name")}
    player_company = str(data.get("player_company_name", "")).strip()
    if player_company:
        # The player-owned promotion is represented by top-level world fields,
        # not by a duplicate Promotion row, but child promotions may still
        # legitimately name it as their parent.
        promotion_names.add(player_company)
    fighter_names = {
        str(row.get("name", "")).strip()
        for _scope, row in _conversion_fighter_rows(data)
        if str(row.get("name", "")).strip()
    }
    for scope, row in _conversion_fighter_rows(data):
        fighter_id = str(row.get("fighter_id", "") or "").strip()
        if not fighter_id:
            issues.append({
                "severity": "error", "entity": scope, "field": "fighter_id",
                "evidence": "fighter has no stable identity", "remedy": "Repair IDs in the source save first.",
            })
        weight = str(row.get("weight", "") or "")
        sport_weight = str(row.get("sport_weight_class", "") or "")
        invalid = [value for value in (weight, sport_weight) if value and value not in WEIGHTS]
        if invalid:
            issues.append({
                "severity": "error", "entity": scope, "field": "weight",
                "evidence": f"unsupported division value(s): {', '.join(invalid)}",
                "remedy": "Map the fighter to a supported division before conversion.",
            })

    for collection in ("roster", "free_agents", "retired_fighters"):
        rows = [row for row in data.get(collection, []) or [] if isinstance(row, dict)]
        ids = [str(row.get("fighter_id", "") or "") for row in rows if row.get("fighter_id")]
        duplicates = sorted({fighter_id for fighter_id in ids if ids.count(fighter_id) > 1})
        if duplicates:
            issues.append({
                "severity": "error", "entity": collection, "field": "fighter_id",
                "evidence": f"duplicate stable ID(s): {', '.join(duplicates[:8])}",
                "remedy": "Keep one authoritative row per top-level collection or repair the IDs.",
            })

    for index, promotion in enumerate(promotions, 1):
        name = str(promotion.get("name", "")).strip()
        if not name:
            issues.append({
                "severity": "error", "entity": f"promotions[{index}]", "field": "name",
                "evidence": "promotion has no owner name", "remedy": "Repair the promotion identity first.",
            })
        parent = str(promotion.get("parent_company", "") or "").strip()
        if parent and parent not in promotion_names and parent != "Independent":
            issues.append({
                "severity": "error", "entity": f"promotions[{index}]", "field": "parent_company",
                "evidence": f"owner '{parent}' is not present in the promotion set",
                "remedy": "Restore the owner or clear the stale parent reference.",
            })

    # Current belt holders are name snapshots in the legacy schema. Validate
    # them against the preserved fighter graph, while leaving excluded history
    # free to mention retired/departed names in the provenance manifest.
    title_sources = [("belts", data.get("belts", {})), ("interim_belts", data.get("interim_belts", {}))]
    for index, promotion in enumerate(promotions, 1):
        title_sources.extend([
            (f"promotions[{index}].belts", promotion.get("belts", {})),
            (f"promotions[{index}].interim_belts", promotion.get("interim_belts", {})),
        ])
    for field, titles in title_sources:
        if not isinstance(titles, dict):
            continue
        for title, holder in titles.items():
            holder_name = str(holder or "").strip()
            if holder_name and holder_name not in fighter_names:
                issues.append({
                    "severity": "error", "entity": field, "field": str(title),
                    "evidence": f"title holder '{holder_name}' is not present in the preserved fighter graph",
                    "remedy": "Restore the holder or vacate the title before conversion.",
                })

    return issues


def build_career_database_package(data, database_name, *, source_save="", created_at=""):
    """Build a new-start database plus an explicit conversion manifest.

    No input mapping is mutated. The returned ``package`` is directly playable
    by ``load_selected_database``; ``manifest`` is written beside it and holds
    excluded history/obligation evidence and the exact acceptance surface.
    """
    if not isinstance(data, dict):
        raise ValueError("Career conversion requires a serialized world object.")
    name = str(database_name or "Career Start").strip() or "Career Start"
    staged = deepcopy(data)
    issues = career_conversion_preflight(staged)
    errors = [row for row in issues if row.get("severity") == "error"]
    if errors:
        # Keep the pure helper useful to callers: structural issues are returned
        # in the manifest and the UI can refuse the write with a clear report.
        pass

    manifest = {
        "schema": 1,
        "type": "career_to_database_conversion",
        "database_name": name,
        "source_save": str(source_save or ""),
        "created_at": str(created_at or ""),
        "complete": not errors,
        "issues": issues,
        "preserved_fields": [],
        "reset_fields": [],
        "excluded_fields": [],
        "provenance": {},
    }
    # Fields with no playable value in a fresh start are reset by omission;
    # ``load_selected_database`` supplies safe defaults for the core counters.
    reset_fields = ("cash", "month", "week", "finance", "inbox", "active_save_name", "active_save_group")
    for field in reset_fields:
        if field in staged:
            manifest["reset_fields"].append({"field": field, "count": _conversion_value_count(staged[field])})
        staged.pop(field, None)

    for field in CAREER_CONVERSION_HISTORY_FIELDS:
        if field not in staged:
            continue
        value = _conversion_json_safe(staged.pop(field))
        count = _conversion_value_count(value)
        manifest["excluded_fields"].append({
            "field": field, "kind": "history", "count": count,
            "reason": "retained in the companion provenance manifest, not imported as playable history",
        })
        manifest["provenance"][field] = value

    for field in CAREER_CONVERSION_ONGOING_FIELDS:
        if field not in staged:
            continue
        value = _conversion_json_safe(staged.pop(field))
        count = _conversion_value_count(value)
        if count:
            manifest["excluded_fields"].append({
                "field": field, "kind": "ongoing", "count": count,
                "reason": "active work cannot be carried into a new-start database",
            })
            manifest["provenance"].setdefault("ongoing", {})[field] = value
        else:
            manifest["reset_fields"].append({"field": field, "count": 0})

    # Promotion and cross-sport rows carry their own event ledgers.  Strip only
    # the live/history members of those nested records; rosters, rankings,
    # titles and staff remain part of the world that a new game can start from.
    nested_paths = []
    for index, promotion in enumerate(staged.get("promotions", []) or [], 1):
        if not isinstance(promotion, dict):
            continue
        for field in ("scheduled_events", "finance", "inbox", "owner_goals"):
            if field not in promotion:
                continue
            value = _conversion_json_safe(promotion.pop(field))
            count = _conversion_value_count(value)
            if count:
                nested_paths.append((f"promotions[{index}].{field}", value, "ongoing" if field == "scheduled_events" else "history"))
    for sport, sport_world in (staged.get("combat_sport_worlds", {}) or {}).items():
        if not isinstance(sport_world, dict):
            continue
        for field in ("events", "scheduled_events", "booked_bouts", "finance_history"):
            if field not in sport_world:
                continue
            value = _conversion_json_safe(sport_world.pop(field))
            count = _conversion_value_count(value)
            if count:
                nested_paths.append((f"combat_sport_worlds.{sport}.{field}", value, "ongoing" if field in {"scheduled_events", "booked_bouts"} else "history"))
    for sport, division_map in (staged.get("player_combat_divisions", {}) or {}).items():
        if not isinstance(division_map, dict):
            continue
        for division, row in division_map.items():
            if not isinstance(row, dict):
                continue
            for field in ("events", "scheduled_events", "booked_bouts", "finance_history"):
                if field not in row:
                    continue
                value = _conversion_json_safe(row.pop(field))
                count = _conversion_value_count(value)
                if count:
                    nested_paths.append((f"player_combat_divisions.{sport}.{division}.{field}", value, "ongoing" if field in {"scheduled_events", "booked_bouts"} else "history"))
    for path, value, kind in nested_paths:
        manifest["excluded_fields"].append({
            "field": path, "kind": kind, "count": _conversion_value_count(value),
            "reason": "nested event/finance state is not imported into a new-start database",
        })
        manifest["provenance"].setdefault("nested", {})[path] = value

    # Pause policies are saved configuration, but their target boundary is a
    # live-career commitment. Do not carry an old stop target into a fresh
    # start; retain the exact policy in provenance for the audit trail.
    rules = staged.get("rules")
    if isinstance(rules, dict) and "simulation_pause_policy" in rules:
        value = _conversion_json_safe(rules.pop("simulation_pause_policy"))
        if _conversion_value_count(value):
            manifest["excluded_fields"].append({
                "field": "rules.simulation_pause_policy", "kind": "ongoing",
                "count": _conversion_value_count(value),
                "reason": "a live-career stop target cannot resume in a new-start database",
            })
            manifest["provenance"].setdefault("ongoing", {})["rules.simulation_pause_policy"] = value

    unknown = sorted(set(staged) - CAREER_CONVERSION_SUPPORTED_FIELDS - {"database_name", "_save_meta"})
    for field in unknown:
        value = _conversion_json_safe(staged.pop(field))
        manifest["excluded_fields"].append({
            "field": field, "kind": "unsupported", "count": _conversion_value_count(value),
            "reason": "no versioned playable mapping exists",
        })
        manifest["provenance"].setdefault("unsupported", {})[field] = value

    for field in sorted(staged):
        if field not in {"database_name", "_save_meta"}:
            manifest["preserved_fields"].append(field)
    staged.pop("_save_meta", None)
    staged["database_name"] = name
    staged["conversion_schema"] = 1
    staged["conversion_source_save"] = str(source_save or "")
    staged["active_save_name"] = f"{name} Start"
    staged["active_save_group"] = "Main"
    # A new-start database must not inherit an active spectator snapshot cursor.
    staged["last_spectator_snapshot_year"] = 0
    manifest["complete"] = not errors and not any(item.get("kind") == "ongoing" for item in manifest["excluded_fields"])
    return staged, manifest


def prune_external_save_blocks(path, active_relatives):
    """Keep only the sidecar block folder referenced by the current primary save."""
    path = Path(path)
    block_root = path.parent / "DataBlocks"
    if not block_root.exists():
        return
    active_roots = set()
    active_roots.update(pinned_replay_roots())
    for relative in active_relatives:
        parts = Path(str(relative)).parts
        if len(parts) >= 2 and parts[0] == "DataBlocks":
            active_roots.add(block_root / parts[1])
    for child in block_root.iterdir():
        if child.resolve() in {root.resolve() for root in active_roots}:
            continue
        if child.is_symlink():
            LOGGER.warning("Skipping symlinked save block entry during prune: %s", child)
            continue
        try:
            if child.is_dir():
                shutil.rmtree(child, onerror=_remove_readonly_path)
            else:
                child.unlink()
        except OSError:
            LOGGER.exception("Could not prune stale save data block %s", child)


def atomic_write_split_save(path, data):
    """Write primary save metadata plus compressed heavy record blocks."""
    path = Path(path)
    payload = dict(data)
    block_refs = {}
    stamp = _crash_stamp()
    block_dir = path.parent / "DataBlocks" / f"{path.stem}_{stamp}"
    for key in EXTERNAL_SAVE_BLOCK_KEYS:
        if key not in payload:
            continue
        block_path = block_dir / f"{key}.json.gz"
        block_data = payload.pop(key)
        if key in ("result_records", "ai_event_archive", "player_event_archive"):
            block_data = split_replay_rows(block_data, block_dir, atomic_write_json_gzip)
        atomic_write_json_gzip(block_path, block_data, compresslevel=3)
        block_refs[key] = str(Path("DataBlocks") / block_dir.name / block_path.name).replace("\\", "/")
    if block_refs:
        payload["_external_blocks"] = block_refs
    else:
        payload.pop("_external_blocks", None)
    atomic_write_json_compact(path, payload)
    prune_external_save_blocks(path, block_refs.values())


def configure_runtime_logging():
    """Create durable, size-limited logs for both source and packaged builds."""
    if getattr(configure_runtime_logging, "configured", False):
        return
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False
        handler = RotatingFileHandler(
            LOG_DIR / "mma_warriors.log",
            maxBytes=1_500_000,
            backupCount=4,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        ))
        LOGGER.addHandler(handler)
        configure_runtime_logging.configured = True
        LOGGER.info("Logging started | Python %s | frozen=%s | app_dir=%s | data_dir=%s", sys.version.split()[0], getattr(sys, "frozen", False), APP_DIR, DATA_DIR)
    except Exception:
        # Logging must never prevent the game starting.
        pass


def register_crash_app(app):
    global _CRASH_APP
    _CRASH_APP = app


def _crash_context(app=None):
    app = app or _CRASH_APP
    lines = [
        f"Timestamp: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Game: {GAME_NAME}",
        f"Python: {sys.version}",
        f"Platform: {platform.platform()}",
        f"Executable: {sys.executable}",
        f"Working directory: {os.getcwd()}",
    ]
    if app:
        lines.extend([
            f"Calendar: Month {getattr(app, 'month', '?')}, Week {getattr(app, 'week', '?')}",
            f"Player company: {getattr(app, 'player_company_name', '?')}",
            f"Theme: {getattr(app, 'theme_name', '?')}",
            f"Roster/free agents: {len(getattr(app, 'roster', []))}/{len(getattr(app, 'free_agents', []))}",
            f"Scheduled events: {len(getattr(app, 'scheduled_events', []))}",
        ])
    return "\n".join(lines)


def write_crash_report(exc_type, exc_value, exc_tb, source="Unhandled exception", app=None):
    """Persist a standalone report and append a concise entry to the runtime log."""
    configure_runtime_logging()
    trace = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    report = f"{_crash_context(app)}\nSource: {source}\n\nTraceback:\n{trace}"
    report_path = None
    try:
        CRASH_DIR.mkdir(parents=True, exist_ok=True)
        report_path = CRASH_DIR / f"crash_{_crash_stamp()}.txt"
        atomic_write_text(report_path, report)
    except Exception:
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            report_path = SAVE_DIR / "crash_log.txt"
            with report_path.open("a", encoding="utf-8") as handle:
                handle.write(f"\n{'=' * 72}\n{report}\n")
        except Exception:
            report_path = None
    try:
        LOGGER.error("%s: %s: %s | report=%s", source, exc_type.__name__, exc_value, report_path, exc_info=(exc_type, exc_value, exc_tb))
    except Exception:
        pass
    return report_path, trace


def install_global_exception_handlers():
    """Catch failures outside Tk callbacks, including worker-thread failures."""
    def handle_main_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        write_crash_report(exc_type, exc_value, exc_tb, "Python main-thread exception")

    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
        write_crash_report(args.exc_type, args.exc_value, args.exc_traceback, f"Background thread exception ({args.thread.name})")

    sys.excepthook = handle_main_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = handle_thread_exception


class PersistenceMixin:
    def save_metadata_sidecar_path(self, path):
        path = Path(path)
        return path.with_name(path.name + ".metadata")

    def write_save_metadata_sidecar(self, path, metadata):
        """Persist tiny save-list metadata without opening the full world file."""
        if not isinstance(metadata, dict) or not metadata:
            return False
        try:
            atomic_write_json_compact(self.save_metadata_sidecar_path(path), metadata)
            return True
        except Exception:
            LOGGER.exception("Could not write save metadata sidecar for %s", path)
            # The sidecar is only a save-manager acceleration cache.  The
            # primary save has already been written successfully and remains
            # authoritative, so a cache failure must not become a false
            # whole-save failure.
            return False

    def save_metadata_file_signature(self, path):
        path = Path(path)
        stat = path.stat()
        sidecar = self.save_metadata_sidecar_path(path)
        if sidecar.exists():
            sidecar_stat = sidecar.stat()
            return (stat.st_mtime_ns, stat.st_size, sidecar_stat.st_mtime_ns, sidecar_stat.st_size)
        return (stat.st_mtime_ns, stat.st_size, 0, 0)

    def read_save_metadata_fast(self, path):
        """Read sidecar metadata, or recover it from a bounded legacy JSON tail."""
        path = Path(path)
        sidecar = self.save_metadata_sidecar_path(path)
        if sidecar.exists():
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except Exception:
                LOGGER.exception("Could not read save metadata sidecar: %s", sidecar)
        if path.suffix.lower() == ".gz":
            return {}
        try:
            with path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(max(0, size - 262_144))
                tail = handle.read().decode("utf-8", errors="ignore")
            marker = '"_save_meta"'
            marker_at = tail.rfind(marker)
            if marker_at < 0:
                return {}
            value_at = tail.find(":", marker_at + len(marker))
            if value_at < 0:
                return {}
            metadata, _end = json.JSONDecoder().raw_decode(tail[value_at + 1:].lstrip())
            if isinstance(metadata, dict):
                self.write_save_metadata_sidecar(path, metadata)
                return metadata
        except Exception:
            LOGGER.exception("Could not recover bounded save metadata from %s", path)
        return {}

    def handle_uncaught_exception(self, exc_type, exc_value, exc_tb):
        """Global guard so a stray error never silently kills a windowed build.

        Logs the traceback, tries an emergency autosave to a separate file so a
        good quick-save is never clobbered, then tells the player what happened.
        """
        report_path, message = write_crash_report(exc_type, exc_value, exc_tb, "Tkinter callback", self)
        crash_note = f"\nCrash report: {report_path}." if report_path else "\nA crash report could not be written."
        try:
            data = self.serialize_world()
            crash_folder = self.save_slot_dir() / "Crash Recovery"
            crash_folder.mkdir(parents=True, exist_ok=True)
            autosave_path = crash_folder / f"crash_autosave_{_crash_stamp()}.json.gz"
            data["_save_meta"] = self.save_metadata("Crash Recovery")
            atomic_write_json_gzip(autosave_path, data, compresslevel=3)
            self.write_save_metadata_sidecar(autosave_path, data["_save_meta"])
            crash_note += f"\nAn emergency autosave was written to {autosave_path}."
        except Exception as autosave_error:
            LOGGER.exception("Emergency crash autosave failed: %s", autosave_error)
            crash_note += "\nEmergency autosave could not be written."
        try:
            messagebox.showerror(
                "Something went wrong",
                "MMA Warriors hit an unexpected error and recovered instead of closing."
                f"\n\n{exc_type.__name__}: {exc_value}{crash_note}",
            )
        except Exception:
            print(message, file=sys.stderr)

    def save_game(self):
        path = self.active_save_path()
        data = self.serialize_world()
        data["_save_meta"] = self.save_metadata(self.active_save_name)
        try:
            if path.exists():
                try:
                    self.backup_save_file(path, "before_quick_save")
                except Exception:
                    LOGGER.exception("Quick save backup failed; continuing with direct write: %s", path)
            atomic_write_split_save(path, data)
            self.write_save_metadata_sidecar(path, data["_save_meta"])
            self.prune_save_backups()
        except Exception as exc:
            LOGGER.exception("Quick save failed: %s", exc)
            messagebox.showerror("Save failed", f"The existing save was left untouched.\n\n{type(exc).__name__}: {exc}")
            return False
        notice = (
            f"Quick saved to {path.resolve()}. Two rolling recovery backups are kept in this game's Backups folder."
        )
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Saved", notice)
        if hasattr(self, "editor_current_dirty"):
            self.editor_current_dirty = False
            if hasattr(self, "refresh_editor_scope_banner"):
                self.refresh_editor_scope_banner()
        return True

    def normalized_save_name(self, name=None):
        raw = str(name or getattr(self, "active_save_name", "") or "Game 1").strip()
        return self.safe_filename(raw) if hasattr(self, "safe_filename") else raw

    def normalized_save_group(self, group=None):
        raw = str(group if group is not None else getattr(self, "active_save_group", "Main") or "Main").strip()
        if raw in ("", "All Saves"):
            return "Main"
        cleaned = self.safe_filename(raw) if hasattr(self, "safe_filename") else raw
        return cleaned if cleaned.lower() not in {"main", "folders", "deleted saves", "autosaves", "backups"} else "Main"

    def save_group_root(self, group=None, create=True):
        normalized = self.normalized_save_group(group)
        path = SAVE_DIR if normalized == "Main" else SAVE_DIR / "Folders" / normalized
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def save_slot_dir(self, name=None, create=True, group=None):
        path = self.save_group_root(group, create=create) / self.normalized_save_name(name)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def active_save_path(self):
        return self.save_slot_dir() / "savegame.json"

    def save_slot_name_from_path(self, path):
        """Find the owning game folder for a new-format primary or snapshot."""
        path = Path(path)
        try:
            relative = path.resolve().relative_to(SAVE_DIR.resolve())
        except Exception:
            return self.normalized_save_name()
        parts = relative.parts
        if len(parts) >= 4 and parts[0] == "Folders":
            return parts[2]
        if len(parts) >= 2 and parts[0] not in {"Backups", "Autosaves", "Deleted Saves", "Folders"}:
            return parts[0]
        return self.normalized_save_name()

    def save_slot_group_from_path(self, path):
        try:
            parts = Path(path).resolve().relative_to(SAVE_DIR.resolve()).parts
        except Exception:
            return "Main"
        return parts[1] if len(parts) >= 4 and parts[0] == "Folders" else "Main"

    @staticmethod
    def save_entry_identity(path):
        """Return a stable read-model key for a save or spectator snapshot.

        Display names are intentionally not used: two folders may contain the
        same slot name, and a snapshot's label is derived from its timestamp.
        The normalized absolute path is only a UI identity; it is never used
        as a permission or mutation shortcut.
        """
        try:
            return f"save-entry:{Path(path).resolve().as_posix().casefold()}"
        except (OSError, ValueError, TypeError):
            return f"save-entry:{Path(path)}"

    @staticmethod
    def save_entry_index(view_keys, identity):
        """Resolve a prior save identity to its current listbox position."""
        if not identity:
            return None
        try:
            return list(view_keys).index(identity)
        except ValueError:
            return None

    @staticmethod
    def database_entry_identity(path):
        """Return an identity for a database row without relying on its label."""
        try:
            return f"database-entry:{Path(path).resolve().as_posix().casefold()}"
        except (OSError, ValueError, TypeError):
            return f"database-entry:{Path(path)}"

    def save_slot_root_from_path(self, path):
        path = Path(path)
        if path.name == "savegame.json":
            return path.parent
        for parent in path.parents:
            if (parent / "savegame.json").exists():
                return parent
        return path.parent

    def set_active_save_name(self, name):
        self.active_save_name = self.normalized_save_name(name)

    def set_active_save_location(self, name, group="Main"):
        self.active_save_group = self.normalized_save_group(group)
        self.set_active_save_name(name)
        if hasattr(self, "save_folder_target"):
            self.save_folder_target.set(self.active_save_group)

    def primary_save_paths(self, *, create=True):
        """Return folder-based saves first, then legacy flat saves for migration.

        The Game & Saves page uses ``create=False`` because refreshing a
        library must not create a save directory as a side effect.  Explicit
        save/new-game owners retain the historical create-on-demand default.
        """
        if create:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
        elif not SAVE_DIR.exists() or not SAVE_DIR.is_dir():
            return []
        paths = [folder / "savegame.json" for folder in SAVE_DIR.iterdir()
                 if folder.is_dir() and folder.name != "Folders" and (folder / "savegame.json").exists()]
        folders_root = SAVE_DIR / "Folders"
        if folders_root.exists():
            paths.extend(
                slot / "savegame.json"
                for group in folders_root.iterdir() if group.is_dir()
                for slot in group.iterdir() if slot.is_dir() and (slot / "savegame.json").exists()
            )
        legacy = [path for path in SAVE_DIR.glob("*.json") if path.name != SAVE_FILE.name]
        if SAVE_FILE.exists():
            legacy.append(SAVE_FILE)
        return sorted(paths, key=lambda item: (self.save_slot_group_from_path(item).lower(), item.parent.name.lower())) + sorted(legacy, key=lambda item: item.name.lower())

    def spectator_snapshot_dir(self, name=None):
        path = self.save_slot_dir(name) / "Snapshots"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def pinned_checkpoint_dir(self, name=None, create=True):
        """Return the explicit, manual checkpoint folder for one save slot."""
        path = self.save_slot_dir(name, create=create) / "Pinned Checkpoints"
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def pinned_checkpoint_files(self, name=None):
        folder = self.pinned_checkpoint_dir(name, create=False)
        if not folder.exists():
            return []
        return sorted(
            (item for item in folder.glob("*.json.gz") if item.is_file()),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )

    def pin_current_checkpoint(self, label=None):
        """Write one immutable, user-requested checkpoint atomically.

        This never replaces the primary save or rolling recovery slots. A
        bounded manual count keeps an accidental button loop from consuming
        unbounded disk space; deletion is always explicit in the manager.
        """
        folder = self.pinned_checkpoint_dir()
        existing = self.pinned_checkpoint_files()
        if len(existing) >= 12:
            self.set_save_manager_status("Checkpoint limit reached (12). Delete an old pinned checkpoint before adding another.")
            return None
        raw_label = str(label or "").strip()
        if not raw_label:
            raw_label = f"Checkpoint {self.format_game_date().replace(' ', '_')}"
        base = self.safe_filename(raw_label)
        path = folder / f"{base}.json.gz"
        suffix = 2
        while path.exists():
            path = folder / f"{base} {suffix}.json.gz"
            suffix += 1
        data = self.serialize_world()
        metadata = self.save_metadata(path.stem)
        metadata.update({
            "checkpoint_type": "pinned",
            "verification_status": "Verified: atomic save completed",
            "source_save": self.active_save_name,
            "source_group": getattr(self, "active_save_group", "Main"),
            "checkpoint_date": self.format_game_date(),
        })
        data["_save_meta"] = metadata
        try:
            atomic_write_json_gzip(path, data, compresslevel=3)
            self.write_save_metadata_sidecar(path, metadata)
        except Exception as exc:
            LOGGER.exception("Pinned checkpoint failed: %s", exc)
            self.set_save_manager_status(f"Checkpoint failed: {type(exc).__name__}: {exc}")
            return None
        self.event_log.insert(0, f"Save system: pinned checkpoint {path.name} at {self.format_game_date()}.")
        self.set_save_manager_status(f"Pinned checkpoint created: {path.name} ({path.stat().st_size:,} bytes).")
        return path

    def delete_pinned_checkpoint(self, path):
        """Delete only a selected pinned checkpoint inside this save slot."""
        path = Path(path)
        folder = self.pinned_checkpoint_dir(create=False)
        try:
            allowed = path.resolve().is_relative_to(folder.resolve())
        except (OSError, ValueError, AttributeError):
            allowed = False
        if not allowed or path.suffix.lower() != ".gz" or not path.exists():
            return False
        path.unlink()
        sidecar = self.save_metadata_sidecar_path(path)
        if sidecar.exists():
            sidecar.unlink()
        self.set_save_manager_status(f"Deleted pinned checkpoint: {path.name}.")
        return True

    def write_spectator_decade_snapshot(self):
        """Archive a spectator universe at each completed decade, once only."""
        if not getattr(self, "spectator_mode", False):
            return None
        years = max(0, (int(getattr(self, "month", 1)) - 1) // 12)
        if years < 10 or years % 10 or years <= int(getattr(self, "last_spectator_snapshot_year", 0)):
            return None
        name = self.normalized_save_name()
        path = self.spectator_snapshot_dir(name) / f"{name} - {years} Years.json.gz"
        data = self.serialize_world()
        # Store the completed decade in the archive itself. Loading a 10-year
        # archive should continue toward year 20, not rewrite year 10 next month.
        data["last_spectator_snapshot_year"] = years
        data["_save_meta"] = self.save_metadata(f"{name} - {years} Years")
        data["_save_meta"].update({"snapshot_type": "spectator_decade", "years_elapsed": years})
        try:
            atomic_write_json_gzip(path, data, compresslevel=3)
            self.write_save_metadata_sidecar(path, data["_save_meta"])
            self.last_spectator_snapshot_year = years
            self.event_log.insert(0, f"Save system: created spectator decade snapshot {path.name}.")
            return path
        except Exception as exc:
            LOGGER.exception("Spectator decade snapshot failed: %s", exc)
            return None

    def save_metadata(self, slot_name=""):
        company_label = "Spectator Mode" if getattr(self, "spectator_mode", False) else getattr(self, "player_company_name", PLAYER_PROMOTION_NAME)
        return {
            "schema": 1,
            "slot_name": slot_name,
            "folder": getattr(self, "active_save_group", "Main"),
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "company": company_label,
            "spectator_mode": bool(getattr(self, "spectator_mode", False)),
            "month": getattr(self, "month", 1),
            "week": getattr(self, "week", 1),
            "cash": getattr(self, "cash", 0),
            "active_universe": self.active_universe_database_path().name if hasattr(self, "active_universe_database_path") else "",
        }

    def save_backup_dir(self, source_path=None, *, create=True):
        # ``create=False`` is used by library readers.  Do not call
        # ``active_save_path()`` there because its normal compatibility path
        # creates the active slot folder as a write-side effect.
        if source_path:
            source = Path(source_path)
        elif create:
            source = self.active_save_path()
        else:
            source = self.save_slot_dir(create=False) / "savegame.json"
        if source.name == "savegame.json":
            path = source.parent / "Backups"
        elif source == SAVE_FILE:
            path = SAVE_DIR / "Backups"
        else:
            path = self.save_slot_dir(create=create) / "Backups"
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def rolling_snapshot_path(self, folder, prefix):
        """Choose the empty or oldest of the two fixed rolling snapshot slots."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        slots = [folder / f"{prefix}_{index}.json.gz" for index in range(1, ROLLING_SAVE_SLOT_COUNT + 1)]
        missing = next((slot for slot in slots if not slot.exists()), None)
        return missing or min(slots, key=lambda slot: slot.stat().st_mtime)

    def prune_rolling_snapshot_files(self, folder, prefix):
        """Keep only the fixed rolling slots; remove legacy timestamped snapshots."""
        folder = Path(folder)
        allowed = {f"{prefix}_{index}.json.gz" for index in range(1, ROLLING_SAVE_SLOT_COUNT + 1)}
        for item in list(folder.glob("*.json")) + list(folder.glob("*.json.gz")) + list(folder.glob("*.tmp")):
            if item.name in allowed:
                continue
            try:
                item.unlink()
                sidecar = self.save_metadata_sidecar_path(item)
                if sidecar.exists():
                    sidecar.unlink()
            except FileNotFoundError:
                pass
            except Exception:
                LOGGER.exception("Could not remove stale rolling save file: %s", item)
        for manifest in folder.glob("*.manifest.json"):
            try:
                manifest.unlink()
            except FileNotFoundError:
                pass
            except Exception:
                LOGGER.exception("Could not remove stale rolling save manifest: %s", manifest)

    def rolling_backup_files(self, *, create=True):
        folder = self.save_backup_dir(create=create)
        if not folder.exists() or not folder.is_dir():
            return []
        files = [folder / f"backup_{index}.json.gz" for index in range(1, ROLLING_SAVE_SLOT_COUNT + 1)]
        return sorted((item for item in files if item.exists()), key=lambda item: item.stat().st_mtime, reverse=True)

    def backup_save_file(self, path, reason="manual"):
        path = Path(path)
        if not path.exists():
            return None
        backup_dir = self.save_backup_dir(path)
        target = self.rolling_snapshot_path(backup_dir, "backup")
        data = load_save_payload(path)
        metadata = dict(data.get("_save_meta", {}))
        metadata.update({
            "backup_created_at": datetime.now().isoformat(timespec="seconds"),
            "backup_source": path.name,
            "backup_reason": reason,
        })
        data["_save_meta"] = metadata
        atomic_write_json_gzip(target, data)
        self.write_save_metadata_sidecar(target, metadata)
        self.prune_rolling_snapshot_files(backup_dir, "backup")
        return target

    def restore_backup_file(self, source, target):
        """Validate a snapshot before protecting and atomically replacing its destination."""
        source = Path(source)
        target = Path(target)
        payload = load_save_payload(source)
        if not isinstance(payload, dict):
            raise ValueError("Backup payload is not a valid save object.")
        if target.exists():
            self.backup_save_file(target, "before_restore")
        atomic_write_split_save(target, payload)
        return target

    def prune_save_backups(self, keep=None):
        self.prune_rolling_snapshot_files(self.save_backup_dir(), "backup")

    def autosave_dir(self, kind="weekly", *, create=True):
        path = self.save_slot_dir(create=create) / "Autosaves" / str(kind).capitalize()
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def write_rolling_autosave(self, kind="weekly", snapshot=None):
        if getattr(self, "suppress_autosaves", False):
            return None
        if hasattr(self, "ensure_rule_defaults"):
            self.ensure_rule_defaults()
        if not self.rules.get("autosave_enabled", True):
            return None
        kind = "monthly" if kind == "monthly" else "weekly"
        label = f"{kind.title()} Autosave {self.format_game_date()}"
        path = self.rolling_snapshot_path(self.autosave_dir(kind), f"{kind}_autosave")
        data = dict(snapshot) if snapshot is not None else self.serialize_world()
        data["_save_meta"] = self.save_metadata(label)
        data["_save_meta"]["autosave_kind"] = kind
        try:
            # Level 3 materially shortens the UI pause on long saves while
            # retaining ordinary gzip compatibility and bounded retention.
            atomic_write_json_gzip(path, data, compresslevel=3)
            self.write_save_metadata_sidecar(path, data["_save_meta"])
            self.prune_rolling_autosaves(kind)
            return path
        except Exception as exc:
            LOGGER.exception("Rolling %s autosave failed: %s", kind, exc)
            return None

    def prune_rolling_autosaves(self, kind="weekly", keep=12):
        folder = self.autosave_dir(kind)
        self.prune_rolling_snapshot_files(folder, f"{kind}_autosave")

    def run_automatic_save_cycle(self, month_changed=False):
        if getattr(self, "suppress_autosaves", False) or not self.rules.get("autosave_enabled", True):
            return None, None
        if not month_changed:
            return None, None
        if hasattr(self, "ensure_rule_defaults"):
            self.ensure_rule_defaults()
        interval = max(1, int(self.rules.get("autosave_interval_months", 2)))
        completed_month = max(0, int(getattr(self, "month", 1)) - 1)
        if completed_month < 1 or completed_month % interval:
            return None, None
        snapshot = self.serialize_world()
        rolling = self.write_rolling_autosave("monthly", snapshot=snapshot)
        if rolling:
            self.event_log.insert(0, f"Save system: wrote two-month rolling autosave {rolling.name}.")
        return None, rolling

    def serialized_result_records(self):
        """Losslessly reference AI replay detail already stored in the archive.

        Runtime viewers still receive full logs. The compact on-disk record avoids
        writing identical commentary twice for the latest archived world events.
        """
        from replay_storage import pack_replay_log

        packages = list(getattr(self, "ai_event_archive", [])) + list(getattr(self, "player_event_archive", []))
        archive = {self.result_archive_key(item): item for item in packages}
        legacy = {self.result_record_fingerprint(item): item for item in packages if not item.get("record_id")}
        rows = []
        for record in self.result_records:
            saved = dict(record)
            package = archive.get(self.result_archive_key(record)) or legacy.get(self.result_record_fingerprint(record))
            if package and not isinstance(record.get("log"), ReplayLines) and not isinstance(package.get("log"), ReplayLines) and record.get("log") == package.get("log") and record.get("fight_logs") == package.get("fight_logs"):
                saved.pop("log", None)
                saved.pop("fight_logs", None)
                saved["_archive_ref"] = {"record_id": self.result_archive_key(package),
                                         "date": package.get("date", ""), "company": package.get("company", ""),
                                         "event": package.get("event_name", "")}
            rows.append(pack_replay_log(saved))
        return rows

    def json_safe_save_value(self, value):
        """Defensively flatten transient model references before writing a save.

        Event builders occasionally keep a featured Fighter reference in a
        runtime-only archive payload. A save must remain portable even if one
        slips into an archive or media metadata structure.
        """
        if isinstance(value, ReplayLines):
            return value
        if isinstance(value, Fighter):
            return serialize_fighter_model(value)
        if isinstance(value, Promotion):
            return self.json_safe_save_value(serialize_promotion_model(value))
        if isinstance(value, Gym):
            return serialize_gym_model(value)
        if isinstance(value, dict):
            return {str(key): self.json_safe_save_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.json_safe_save_value(item) for item in value]
        return value

    def relink_archived_result_records(self):
        """Restore de-duplicated save records to the normal full runtime shape."""
        from replay_storage import unpack_replay_log

        packages = list(getattr(self, "ai_event_archive", [])) + list(getattr(self, "player_event_archive", []))
        archive = {self.result_archive_key(item): item for item in packages}
        for record in self.result_records:
            unpack_replay_log(record)
            ref = record.get("_archive_ref")
            if not isinstance(ref, dict):
                continue
            if ref.get("record_id"):
                package = archive.get(ref["record_id"])
            else:
                matches = [item for item in packages
                           if (item.get("date", ""), item.get("company", ""), item.get("event_name", ""))
                           == (ref.get("date", ""), ref.get("company", ""), ref.get("event", ""))]
                # Old references lack identity. Keep unresolved evidence rather
                # than attach a different same-name, same-week card's results.
                package = matches[0] if len(matches) == 1 else None
            if package:
                record["log"] = package.get("log", [])
                record["fight_logs"] = package.get("fight_logs", [])
                record.pop("_archive_ref", None)

    def repair_premature_retirements(self):
        """Repair legacy feeder exits and introduce requested prime legend starts.

        This migration is confined to early-world saves, so an established
        long-running universe is never silently rewound.
        """
        restored = []
        retained = []
        early_world = getattr(self, "month", 1) <= 48
        prime_resets = set()
        if early_world:
            prime_ages = self.historic_prime_age_overrides()
            fighter_groups = [self.roster, self.free_agents, self.retired_fighters]
            fighter_groups.extend(promo.roster for promo in self.promotions)
            for group in fighter_groups:
                for fighter in group:
                    target_age = prime_ages.get(fighter.name)
                    if target_age is None or getattr(fighter, "prime_legend_age_override_version", 0) >= 1:
                        continue
                    fighter.age = target_age
                    fighter.prime_start = max(24, target_age - 3)
                    fighter.prime_end = max(fighter.prime_start + 5, target_age + 6)
                    fighter.prime_legend_age_override_version = 1
                    prime_resets.add(id(fighter))
        for fighter in self.retired_fighters:
            bad_early_exit = (
                fighter.age < 30
                and not getattr(fighter, "serious_injury", "")
                and str(getattr(fighter, "retirement_reason", "")).startswith("Retired after final fight")
            )
            prime_legend_reset = id(fighter) in prime_resets
            if not (bad_early_exit or prime_legend_reset):
                retained.append(fighter)
                continue
            fighter.retired = False
            fighter.retirement_pending = False
            fighter.retirement_fight_completed = False
            fighter.retirement_requested_month = 0
            fighter.retirement_reason = "Returned to free agency for a fresh career opportunity."
            fighter.contract_months = 0
            fighter.contract_type = "Free Agent"
            fighter.exclusive = False
            fighter.free_agent_months = 0
            fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + 4)
            restored.append(fighter)
        if not restored:
            return
        self.retired_fighters = retained
        existing = {fighter.fighter_id for fighter in self.free_agents}
        for fighter in restored:
            if fighter.fighter_id not in existing:
                self.free_agents.append(fighter)
                existing.add(fighter.fighter_id)

    def repair_player_scheduled_fighter_references(self):
        """Restore a legacy player booking before any display lookup occurs.

        Historical cards sometimes predate durable fighter IDs and a later
        retirement or release may have moved a booked athlete out of the player
        roster.  Repair that ownership once during transactional load rather
        than letting ordinary lookup mutate rosters as a side effect.  Ambiguous
        same-name legacy references are deliberately left unresolved so a save
        cannot silently assign the wrong athlete to a card.
        """
        references = []
        for event in getattr(self, "scheduled_events", []):
            for fight in event.get("fights", []):
                references.extend(
                    reference for reference in self.event_fight_participant_references(fight)
                    if reference and reference != "TBA"
                )

        roster_ids = {str(getattr(fighter, "fighter_id", "") or "") for fighter in self.roster}
        restored = []
        unresolved = []
        for reference in dict.fromkeys(str(reference) for reference in references):
            if reference in roster_ids:
                continue
            name_matches = [fighter for fighter in self.roster if fighter.name == reference]
            if len(name_matches) == 1:
                continue
            candidates = [
                fighter for fighter in self.retired_fighters + self.free_agents
                if str(getattr(fighter, "fighter_id", "") or "") == reference
            ]
            if not candidates:
                candidates = [
                    fighter for fighter in self.retired_fighters + self.free_agents
                    if fighter.name == reference
                ]
            if len(candidates) != 1:
                unresolved.append(reference)
                continue
            fighter = candidates[0]
            membership = getattr(self, "record_membership_event", None)
            membership_action = "return" if fighter in self.retired_fighters else "join"
            if callable(membership):
                membership(
                    fighter, membership_action,
                    company_name=getattr(self, "player_company_name", ""),
                    reason=(
                        "Returned to the player roster to honour an outstanding booked fight."
                        if membership_action == "return" else
                        "Restored to the player roster to honour an outstanding booked fight."
                    ),
                    source_transaction=f"load-restore-booked:{getattr(fighter, 'fighter_id', '')}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                )
            if fighter in self.retired_fighters:
                self.retired_fighters.remove(fighter)
                fighter.retired = False
                fighter.retirement_pending = True
                fighter.retirement_fight_completed = False
                fighter.retirement_reason = "Retirement deferred to honour an existing booked fight."
                notice_type = "Roster"
                subject = f"Booked Fight Restored - {fighter.name}"
                body = f"{fighter.name} was restored for an outstanding booked fight and will retire after that commitment."
            else:
                self.free_agents.remove(fighter)
                fighter.contract_months = max(1, int(getattr(fighter, "contract_months", 0) or 0))
                notice_type = "Contracts"
                subject = f"Booked Contract Restored - {fighter.name}"
                body = f"{fighter.name}'s outstanding event commitment was restored after an early roster transition."
            self.roster.append(fighter)
            roster_ids.add(str(getattr(fighter, "fighter_id", "") or ""))
            self.inbox.append({"subject": subject, "body": body, "type": notice_type, "resolved": False, "fighter_id": getattr(fighter, "fighter_id", "")})
            restored.append(getattr(fighter, "fighter_id", "") or fighter.name)
        return {"restored": restored, "unresolved": unresolved}

    def ensure_fighter_ids(self):
        """Give legacy saves permanent fighter identities and repair bad collisions."""
        seen = set()
        fighter_groups = [self.roster, self.free_agents, self.retired_fighters]
        fighter_groups.extend(promo.roster for promo in self.promotions)
        fighter_groups.extend(world.get("roster", []) for world in getattr(self, "combat_sport_worlds", {}).values())
        for group in fighter_groups:
            for fighter in group:
                fighter_id = str(getattr(fighter, "fighter_id", "") or "")
                if not fighter_id or fighter_id in seen:
                    fighter_id = f"FTR-{uuid4().hex[:16]}"
                    fighter.fighter_id = fighter_id
                seen.add(fighter_id)
        # Legacy friendships stored names only. Backfill an ID only when the
        # complete loaded world contains exactly one possible person.
        fighters = []
        seen_objects = set()
        for group in fighter_groups:
            for fighter in group:
                if id(fighter) not in seen_objects:
                    seen_objects.add(id(fighter))
                    fighters.append(fighter)
        by_name = {}
        for fighter in fighters:
            by_name.setdefault(str(getattr(fighter, "name", "") or ""), []).append(fighter)
        valid_ids = {str(getattr(fighter, "fighter_id", "") or "") for fighter in fighters}
        for fighter in fighters:
            friend_id = str(getattr(fighter, "friend_fighter_id", "") or "")
            if friend_id in valid_ids:
                continue
            fighter.friend_fighter_id = ""
            matches = [candidate for candidate in by_name.get(str(getattr(fighter, "friend", "") or ""), []) if candidate is not fighter]
            if len(matches) == 1:
                fighter.friend_fighter_id = matches[0].fighter_id

    def backfill_archived_fight_log_ids(self):
        """Attach IDs to legacy bout logs only when sport/division gives one answer."""
        fighters = []
        for group in [self.roster, self.free_agents, self.retired_fighters]:
            fighters.extend(group)
        for promo in self.promotions:
            fighters.extend(promo.roster)
        for world in getattr(self, "combat_sport_worlds", {}).values():
            fighters.extend(world.get("roster", []))

        def identify(name, sport, division):
            matches = [fighter for fighter in fighters if fighter.name == name]
            if sport:
                sport_matches = [fighter for fighter in matches if str(getattr(fighter, "primary_discipline", "") or "") == str(sport)]
                if sport_matches:
                    matches = sport_matches
            if division:
                division_matches = [fighter for fighter in matches if str(getattr(fighter, "sport_weight_class", "") or fighter.weight) == str(division)]
                if division_matches:
                    matches = division_matches
            return matches[0] if len(matches) == 1 else None

        seen_logs = set()
        for record in list(self.result_records) + list(self.ai_event_archive):
            for log in record.get("fight_logs", []) or []:
                marker = id(log)
                if marker in seen_logs:
                    continue
                seen_logs.add(marker)
                sport, division = log.get("sport", ""), log.get("weight", "")
                if not log.get("a_id"):
                    fighter = identify(str(log.get("a", "")), sport, division)
                    if fighter:
                        log["a_id"] = fighter.fighter_id
                if not log.get("b_id"):
                    fighter = identify(str(log.get("b", "")), sport, division)
                    if fighter:
                        log["b_id"] = fighter.fighter_id

    def serialize_world(self):
        # Identity migration is deterministic and RNG-free. It is the one
        # intentional state repair allowed during save so newly-created
        # promotions/cards cannot be persisted without stable IDs.
        self.ensure_foundation_ids()
        # Current rosters are captured as a known-present boundary only; the
        # adapter leaves the original join date unknown instead of backdating it.
        migrate_presence = getattr(self, "migrate_current_membership_presence", None)
        if callable(migrate_presence):
            migrate_presence()
        return {
            "player_company_name": self.player_company_name,
            "spectator_mode": getattr(self, "spectator_mode", False),
            "active_save_name": getattr(self, "active_save_name", "Game 1"),
            "active_save_group": getattr(self, "active_save_group", "Main"),
            "last_spectator_snapshot_year": getattr(self, "last_spectator_snapshot_year", 0),
            "player_region": self.player_region,
            "player_reputation": self.player_reputation,
            "company_show_personality": getattr(self, "company_show_personality", "Balanced"),
            "theme_name": self.theme_name,
            "cash": self.cash,
            "company_pop": self.company_pop,
            "company_stability": self.company_stability,
            "company_safety": getattr(self, "company_safety", 60),
            "company_milestone_progress": getattr(self, "company_milestone_progress", {}),
            "super_event_offers": getattr(self, "super_event_offers", []),
            "super_event_history": getattr(self, "super_event_history", []),
            "super_event_project": getattr(self, "super_event_project", None),
            "regional_invitations": deepcopy(getattr(self, "regional_invitations", [])),
            "regional_invitation_history": deepcopy(getattr(self, "regional_invitation_history", [])),
            "month": self.month,
            "week": self.week,
            "roster": [serialize_fighter_model(f) for f in self.roster],
            "free_agents": [serialize_fighter_model(f) for f in self.free_agents],
            "promotions": [serialize_promotion_model(p) for p in self.promotions],
            "combat_sport_worlds": {sport: {**world, "roster": [serialize_fighter_model(fighter) for fighter in world.get("roster", [])]} for sport, world in getattr(self, "combat_sport_worlds", {}).items()},
            # The nested division dictionaries must not alias live state. Load
            # transactions clear/repair the application before applying this
            # candidate, and a shared reference could erase scheduled cards
            # from the serialized snapshot itself.
            "player_combat_divisions": deepcopy(getattr(self, "player_combat_divisions", {})),
            "standings_history": getattr(self, "standings_history", {}),
            "regions": self.regions,
            "gyms": [serialize_gym_model(g) for g in getattr(self, "gyms", [])],
            "result_history": self.result_history,
            "result_records": self.json_safe_save_value(self.serialized_result_records()),
            "change_journal": self.json_safe_save_value(getattr(self, "change_journal", [])),
            "result_index": self.json_safe_save_value(getattr(self, "result_index", [])),
            "ai_event_archive": self.json_safe_save_value(self.ai_event_archive),
            "player_event_archive": self.json_safe_save_value(getattr(self, "player_event_archive", [])),
            "independent_showcase_counter": getattr(self, "independent_showcase_counter", 1),
            "retired_fighters": [serialize_fighter_model(f) for f in self.retired_fighters],
            "finance": self.finance,
            "media_companies": getattr(self, "media_companies", []),
            "media_market_history": getattr(self, "media_market_history", []),
            "media_market_last_month": getattr(self, "media_market_last_month", 0),
            "engine_settings": self.engine_settings,
            "business_settings": getattr(self, "business_settings", self.seed_business_settings()),
            "staff": self.staff,
            "staff_candidates": self.staff_candidates,
            "staff_management": deepcopy(getattr(self, "staff_management", {})),
            "drug_testing_state": deepcopy(getattr(self, "drug_testing_state", {})),
            "booking_workbench": deepcopy(getattr(self, "booking_workbench", {})),
            "contract_batch_workbench": deepcopy(getattr(self, "contract_batch_workbench", {})),
            "scouting": list(self.scouting)[-500:] if isinstance(getattr(self, "scouting", None), list) else [],
            "scouting_reports": {
                str(key): value for key, value in (getattr(self, "scouting_reports", {}) or {}).items()
                if isinstance(value, dict)
            } if isinstance(getattr(self, "scouting_reports", None), dict) else {},
            "scouting_searches": (
                [value for value in (getattr(self, "scouting_searches", []) or []) if isinstance(value, dict) and value.get("status") in ("In progress", "Monitoring")]
                + [value for value in (getattr(self, "scouting_searches", []) or []) if isinstance(value, dict) and value.get("status") not in ("In progress", "Monitoring")][-500:]
            ),
            "scouting_shortlist": list(dict.fromkeys(
                str(value) for value in (getattr(self, "scouting_shortlist", []) or []) if value
            ))[-2000:],
            "scouting_watchlists": [
                value for value in (getattr(self, "scouting_watchlists", []) or []) if isinstance(value, dict)
            ][:20],
            "scouting_decision_packs": [
                value for value in (getattr(self, "scouting_decision_packs", []) or []) if isinstance(value, dict)
            ][:40],
            "scouting_history": [
                value for value in (getattr(self, "scouting_history", []) or []) if isinstance(value, dict)
            ][-1000:],
            "scouting_knowledge": dict(getattr(self, "scouting_knowledge", {}) or {}),
            "scouting_alert_state": dict(getattr(self, "scouting_alert_state", {}) or {}),
            "scouting_quarantined_reports": [
                value for value in (getattr(self, "scouting_quarantined_reports", []) or []) if isinstance(value, dict)
            ][-250:],
            "achievement_log": getattr(self, "achievement_log", []),
            "historical_records": getattr(self, "historical_records", {}),
            "fanbase": getattr(self, "fanbase", {}),
            "academy": getattr(self, "academy", {}),
            "inbox": self.inbox,
            "inbox_hidden_types": sorted(getattr(self, "inbox_hidden_types", set())),
            "owner_goals": self.owner_goals,
            "belts": self.belts,
            "interim_belts": self.interim_belts,
            "special_belts": getattr(self, "special_belts", {}),
            "belt_history": self.belt_history,
            "closed_divisions": sorted(getattr(self, "closed_divisions", set())),
            "player_managed_divisions": sorted(getattr(self, "player_managed_divisions", set())),
            "rules": self.rules,
            "broadcasters": self.broadcasters,
            "weight_classes": self.weight_classes,
            "post_show_bonuses": self.post_show_bonuses,
            "scheduled_events": self.scheduled_events,
            "grand_prix_series": deepcopy(getattr(self, "grand_prix_series", [])),
            "pending_rebookings": getattr(self, "pending_rebookings", []),
            "news": self.news,
            "world_chronicle": getattr(self, "world_chronicle", []),
            "story_threads": self.json_safe_save_value(getattr(self, "story_threads", [])),
            "story_subscriptions": self.json_safe_save_value(getattr(self, "story_subscriptions", []))[-100:],
            "relationship_cases": self.json_safe_save_value(getattr(self, "relationship_cases", []))[-200:],
            "defunct_promotions": getattr(self, "defunct_promotions", []),
            "event_log": self.event_log,
            "season_stats": getattr(self, "season_stats", {}),
            "awards_history": getattr(self, "awards_history", []),
            "fight_timer_delay": self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 2150,
            "foundation": deepcopy(self.ensure_foundation_state()),
        }

    def load_game(self):
        path = self.active_save_path()
        if not path.exists() and SAVE_FILE.exists():
            path = SAVE_FILE
        if not path.exists():
            notice = "No active save exists yet. Use Save New / Overwrite to create a career slot."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No save", notice)
            return
        busy = self.show_busy_overlay("Loading save", "Reading save data...", 8)
        try:
            data = load_save_payload(path)
            self.update_busy_overlay("Rebuilding fighters, companies, and world history...", 32)
            self.apply_world_data(data)
        except Exception as exc:
            recovery_paths = self.rolling_backup_files()
            # A legacy previous-save file is read once as a fallback for saves
            # created before the two-slot policy. New saves no longer create it.
            legacy_previous = SAVE_FILE.with_name("savegame.previous.json")
            if legacy_previous.exists():
                recovery_paths.append(legacy_previous)
            for backup_path in recovery_paths:
                try:
                    self.update_busy_overlay(f"Trying recovery snapshot {backup_path.stem}...", 42)
                    self.apply_world_data(load_save_payload(backup_path))
                    self.booked.clear()
                    self.ensure_player_event_name()
                    self.update_busy_overlay("Refreshing the promoter dashboard...", 82)
                    self.refresh_all()
                    self.write_log()
                    self.update_busy_overlay("Recovery save loaded.", 100)
                    self.close_busy_overlay(busy)
                    busy = None
                    notice = (
                        f"The current quick save could not be read. Recovery snapshot {backup_path.stem} was loaded instead."
                    )
                    if not self._save_surface_notice(notice):
                        messagebox.showwarning("Backup loaded", notice)
                    LOGGER.warning("Quick save failed to load; restored previous backup: %s", exc)
                    return
                except Exception:
                    LOGGER.exception("Quick-save backup could not be loaded after primary failure")
            LOGGER.exception("Quick save could not be loaded: %s", exc)
            self.close_busy_overlay(busy)
            busy = None
            messagebox.showerror(
                "Load failed",
                f"That save could not be loaded and was left untouched.\n\n{type(exc).__name__}: {exc}",
            )
            return
        try:
            self.booked.clear()
            self.ensure_player_event_name()
            self.reconcile_title_shot_alerts()
            self.update_busy_overlay("Refreshing the promoter dashboard...", 82)
            self.refresh_all()
            self.update_busy_overlay("Finishing load...", 96)
            self.write_log()
            self.update_busy_overlay("Save loaded.", 100)
            notice = f"Loaded {path.name}; the active career is ready."
            if hasattr(self, "_save_surface_notice"):
                self._save_surface_notice(notice)
            elif hasattr(self, "set_save_manager_status"):
                self.set_save_manager_status(notice)
        finally:
            self.close_busy_overlay(busy)

    @staticmethod
    def _is_runtime_ui_value(value, seen=None):
        """Return whether a value contains live presentation/runtime state.

        Load staging must never copy a Tk object merely because it is later in
        a long collection.  This walks the complete graph with cycle handling;
        persistent fields are copied only when this guard says they are safe.
        """
        if isinstance(value, (tk.Misc, tk.Variable)) or hasattr(value, "tk") or callable(value):
            return True
        if seen is None:
            seen = set()
        identity = id(value)
        if identity in seen:
            return False
        seen.add(identity)
        if isinstance(value, dict):
            return any(PersistenceMixin._is_runtime_ui_value(item, seen) for item in value.values())
        if isinstance(value, (list, tuple, set, frozenset)):
            return any(PersistenceMixin._is_runtime_ui_value(item, seen) for item in value)
        return False

    def _sync_loaded_ui_state(self):
        """Apply a successfully committed load to live Tk controls."""
        try:
            if hasattr(self, "theme_name_var"):
                self.theme_name_var.set(self.theme_name)
                self.configure_style()
                self.retheme_plain_widgets(self.root)
            if hasattr(self, "engine_vars"):
                for key, var in self.engine_vars.items():
                    var.set(self.engine_settings.get(key, 1.0))
            if hasattr(self, "gate_multiplier_var"):
                self.gate_multiplier_var.set(self.business_settings.get("gate_multiplier", 1.0))
            if hasattr(self, "fight_timer_delay"):
                self.fight_timer_delay.set(max(120, min(3000, int(getattr(self, "_loaded_fight_timer_delay", 2150)))))
            self.set_player_event_location_default()
        except Exception:
            # The domain state is already valid and committed.  A stale lazy
            # widget must not turn that successful load into a destructive
            # rollback or a misleading load failure.
            LOGGER.exception("Loaded world committed, but a UI control could not be synchronized")

    def apply_world_data(self, data):
        """Validate and migrate a save off to the side, then commit atomically.

        The old loader assigned hundreds of fields directly to the live app.
        A late migration error therefore left a hybrid of the old and new
        careers.  The staging instance has the same domain helpers but no live
        Tk widgets, so failures leave ``self`` untouched.
        """
        staged = self.__class__.__new__(self.__class__)
        ui_keys = set()
        copy_memo = {}
        for key, value in self.__dict__.items():
            if self._is_runtime_ui_value(value):
                ui_keys.add(key)
                continue
            try:
                staged.__dict__[key] = deepcopy(value, copy_memo)
            except Exception:
                staged.__dict__[key] = value
        rng_state = random.getstate()
        try:
            staged._apply_world_data_unchecked(deepcopy(data))
        except Exception:
            random.setstate(rng_state)
            raise
        for key, value in staged.__dict__.items():
            if key not in ui_keys:
                self.__dict__[key] = value
        self._sync_loaded_ui_state()

    def _apply_world_data_unchecked(self, data):
        if hasattr(self, "editor_current_dirty"):
            self.editor_current_dirty = False
        self.active_save_name = self.normalized_save_name(data.get("active_save_name", getattr(self, "active_save_name", "Game 1")))
        self.active_save_group = self.normalized_save_group(data.get("active_save_group", getattr(self, "active_save_group", "Main")))
        self.last_spectator_snapshot_year = max(0, int(data.get("last_spectator_snapshot_year", 0)))
        self.player_company_name = data.get("player_company_name", PLAYER_PROMOTION_NAME)
        if self.player_company_name == "Cage Empire":
            self.player_company_name = PLAYER_PROMOTION_NAME
        self.spectator_mode = bool(data.get("spectator_mode", self.player_company_name == "Spectator"))
        self.player_region = data.get("player_region", "USA")
        self.player_reputation = data.get("player_reputation", "Regional Player Company")
        self.company_show_personality = data.get("company_show_personality", "Balanced")
        self.theme_name = data.get("theme_name", getattr(self, "theme_name", "Fight Night"))
        self.cash = data.get("cash", 275_000)
        self.company_pop = data.get("company_pop", 38)
        self.company_stability = data.get("company_stability", max(5, min(99, self.cash // 5000)))
        self.month = max(1, int(data.get("month", 1) or 1))
        self.week = max(1, min(4, int(data.get("week", 1) or 1)))
        self.ensure_foundation_state(deepcopy(data.get("foundation")))
        self.roster = [load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, f"player roster row {index}") for index, row in enumerate(data.get("roster", []), 1)]
        self.free_agents = [load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, f"free-agent row {index}") for index, row in enumerate(data.get("free_agents", []), 1)]
        for fighter in self.roster + self.free_agents:
            fighter.weight = self.game_weight_class(fighter.weight)
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.promotions = []
        self.defunct_promotions = list(data.get("defunct_promotions", []))
        for promotion_index, saved_row in enumerate(data.get("promotions", []), 1):
            if not isinstance(saved_row, dict):
                raise ValueError(f"promotion row {promotion_index} must be an object, not {type(saved_row).__name__}.")
            row = dict(saved_row)
            roster_rows = row.get("roster", [])
            if not isinstance(roster_rows, list):
                raise ValueError(f"promotion row {promotion_index} roster must be a list.")
            row["roster"] = [
                load_model_row(fighter, Fighter, FIGHTER_SAVE_FIELDS, f"promotion row {promotion_index} fighter {fighter_index}")
                for fighter_index, fighter in enumerate(roster_rows, 1)
            ]
            row["weight_classes"] = list(dict.fromkeys(
                self.game_weight_class(weight) for weight in row.get("weight_classes", [])
                if self.game_weight_class(weight) in WEIGHTS
            )) or list(WEIGHTS)
            row.setdefault("stability", max(5, min(99, row.get("cash", 0) // 20000)))
            row.setdefault("strategy", self.seed_promotion_strategy(row.get("name", ""), row.get("show_personality", "Balanced")))
            row.setdefault("strategic_rival", "")
            row.setdefault("executive", self.seed_promotion_executive(row.get("name", "")))
            row.setdefault("era_history", [])
            row.setdefault("legacy_score", 0)
            row.setdefault("closed_divisions", [])
            row.setdefault("closed_division_policy_set", False)
            row.setdefault("special_belts", {})
            row.setdefault("regional_division_activity", {})
            row.setdefault("is_child_promotion", False)
            row.setdefault("parent_company", "")
            row.setdefault("child_strategy", "Balanced")
            row.setdefault("parent_profit_share", 0)
            row.setdefault("startup_capital", 0)
            row.setdefault("initial_roster_budget", 0)
            row.setdefault("loaned_fighter_ids", [])
            for fighter in row["roster"]:
                fighter.weight = self.game_weight_class(fighter.weight)
                self.ensure_detailed_skills(fighter)
                self.ensure_fighter_business_stats(fighter)
            self.promotions.append(load_model_row(row, Promotion, PROMOTION_SAVE_FIELDS, f"promotion row {promotion_index}"))
        # A save is a sealed simulation state. Its fighter rosters must never
        # be repopulated from whichever universe database happens to be active
        # when the player loads it.
        if not self.promotions:
            raise ValueError("Save contains no promotion data and cannot be safely restored")
        self.repair_core_promotions(restore_missing=False)
        self.regions = data.get("regions", self.seed_regions())
        for region in REGIONS:
            self.regions.setdefault(region, {
                "economy": "stable",
                "legality": "regulated by athletic commissions",
                "drug_accuracy": 65,
                "mma_love": random.randint(35, 85),
                "promo_benefit": REGION_PROMO_BENEFITS.get(region, {"media": 1.0, "gate": 1.0, "morale": 1}),
                "teams": random.sample(CAMPS, k=min(3, len(CAMPS))),
                "areas": REGION_CITIES.get(region, [region]),
                "last_major_show": "No major shows yet",
            })
            self.regions[region].setdefault("fan_identity", "Local MMA community")
            self.regions[region].setdefault("crowd_preference", "Competitive fights")
        seeded_gyms = self.seed_gyms()
        if data.get("gyms"):
            self.gyms = [load_model_row(row, Gym, GYM_SAVE_FIELDS, f"gym row {index}") for index, row in enumerate(data.get("gyms", []), 1)]
            known_gyms = {gym.name for gym in self.gyms}
            self.gyms.extend(gym for gym in seeded_gyms if gym.name not in known_gyms)
        else:
            self.gyms = seeded_gyms
        self.result_history = list(data.get("result_history", []))[:RESULT_HISTORY_LIMIT]
        self.result_records = data.get("result_records", [])
        self.change_journal = list(data.get("change_journal", []))[-400:]
        self.ai_event_archive = data.get("ai_event_archive", [])
        self.player_event_archive = data.get("player_event_archive", [])[-150:]
        self.relink_archived_result_records()
        self.result_index = data.get("result_index", [])
        self.ensure_result_index()
        serialized_sport_worlds = data.get("combat_sport_worlds")
        self.combat_sport_worlds = serialized_sport_worlds if serialized_sport_worlds else self.seed_combat_sport_worlds()
        for sport, world in self.combat_sport_worlds.items():
            world["roster"] = [
                fighter if isinstance(fighter, Fighter) else load_model_row(fighter, Fighter, FIGHTER_SAVE_FIELDS, f"combat sport {sport} fighter {index}")
                for index, fighter in enumerate(world.get("roster", []), 1)
            ]
        self.player_combat_divisions = data.get("player_combat_divisions", {}) or {}
        self.standings_history = data.get("standings_history", {}) or {}
        self.independent_showcase_counter = max(1, data.get("independent_showcase_counter", 1))
        self.retired_fighters = [load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, f"retired fighter row {index}") for index, row in enumerate(data.get("retired_fighters", []), 1)]
        for fighter in self.retired_fighters:
            fighter.weight = self.game_weight_class(fighter.weight)
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.repair_premature_retirements()
        self.ensure_fighter_ids()
        for sport, division in list(self.player_combat_divisions.items()):
            if not isinstance(division, dict) or sport not in self.combat_sport_worlds:
                self.player_combat_divisions.pop(sport, None)
                continue
            for key in ("roster", "roster_ids", "rankings", "events", "scheduled_events", "booked_bouts", "awards", "hall_of_fame", "finance_history"):
                if not isinstance(division.get(key, []), list):
                    division[key] = []
            for key in ("titles", "title_ids", "title_history", "rankings_by_division", "records", "record_book", "season_stats"):
                if not isinstance(division.get(key, {}), dict):
                    division[key] = {}
            self.ensure_player_combat_division_identity(sport, self.combat_sport_worlds[sport])
        if hasattr(self, "repair_child_promotion_state"):
            self.repair_child_promotion_state()
        self.backfill_archived_fight_log_ids()
        self.finance = data.get("finance", self.seed_finance())
        self.media_companies = data.get("media_companies", []) or []
        self.media_market_history = data.get("media_market_history", []) or []
        self.media_market_last_month = data.get("media_market_last_month", 0)
        raw_engine_settings = data.get("engine_settings", {})
        self.engine_settings = self.normalize_engine_settings(raw_engine_settings)
        self.business_settings = self.normalize_business_settings(
            data.get("business_settings"), legacy_engine_settings=raw_engine_settings,
        )
        self.ensure_finance_defaults()
        self.staff = data.get("staff", self.seed_staff())
        self.staff_candidates = data.get("staff_candidates", self.seed_staff_candidates())
        self.ensure_staff_profiles()
        self.staff_management = data.get("staff_management", {}) if isinstance(data.get("staff_management", {}), dict) else {}
        if hasattr(self, "ensure_staff_management_state"):
            self.ensure_staff_management_state()
        self.drug_testing_state = data.get("drug_testing_state", {}) if isinstance(data.get("drug_testing_state", {}), dict) else {}
        if hasattr(self, "ensure_drug_testing_state"):
            self.ensure_drug_testing_state()
        self.booking_workbench = data.get("booking_workbench", {}) if isinstance(data.get("booking_workbench", {}), dict) else {}
        if hasattr(self, "ensure_booking_workbench_state"):
            self.ensure_booking_workbench_state()
        self.contract_batch_workbench = data.get("contract_batch_workbench", {}) if isinstance(data.get("contract_batch_workbench", {}), dict) else {}
        if hasattr(self, "ensure_contract_batch_state"):
            self.ensure_contract_batch_state()
        raw_scouting = data.get("scouting", [])
        self.scouting = list(raw_scouting)[-500:] if isinstance(raw_scouting, list) else []
        raw_reports = data.get("scouting_reports", {})
        self.scouting_reports = {
            str(key): dict(value) for key, value in raw_reports.items() if isinstance(value, dict)
        } if isinstance(raw_reports, dict) else {}
        raw_searches = data.get("scouting_searches", [])
        self.scouting_searches = (
            [dict(value) for value in raw_searches if isinstance(value, dict) and value.get("status") in ("In progress", "Monitoring")]
            + [dict(value) for value in raw_searches if isinstance(value, dict) and value.get("status") not in ("In progress", "Monitoring")][-500:]
        ) if isinstance(raw_searches, list) else []
        raw_shortlist = data.get("scouting_shortlist", [])
        self.scouting_shortlist = list(dict.fromkeys(
            str(key) for key in raw_shortlist if key
        ))[-2000:] if isinstance(raw_shortlist, list) else []
        raw_watchlists = data.get("scouting_watchlists", [])
        self.scouting_watchlists = [dict(value) for value in raw_watchlists if isinstance(value, dict)][:20] if isinstance(raw_watchlists, list) else []
        raw_decision_packs = data.get("scouting_decision_packs", [])
        self.scouting_decision_packs = [dict(value) for value in raw_decision_packs if isinstance(value, dict)][:40] if isinstance(raw_decision_packs, list) else []
        raw_history = data.get("scouting_history", [])
        self.scouting_history = [dict(value) for value in raw_history if isinstance(value, dict)][-1000:] if isinstance(raw_history, list) else []
        raw_knowledge = data.get("scouting_knowledge", {})
        self.scouting_knowledge = dict(raw_knowledge) if isinstance(raw_knowledge, dict) else {}
        raw_alert_state = data.get("scouting_alert_state", {})
        self.scouting_alert_state = dict(raw_alert_state) if isinstance(raw_alert_state, dict) else {}
        raw_quarantined = data.get("scouting_quarantined_reports", [])
        self.scouting_quarantined_reports = [
            dict(value) for value in raw_quarantined if isinstance(value, dict)
        ][-250:] if isinstance(raw_quarantined, list) else []
        self._scouting_state_migrated = False
        self.migrate_scouting_state()
        self.achievement_log = data.get("achievement_log", [])
        self.company_safety = max(0, min(100, int(data.get("company_safety", 60) or 60)))
        self.company_milestone_progress = data.get("company_milestone_progress", {}) or {}
        self.super_event_offers = data.get("super_event_offers", []) or []
        self.super_event_history = data.get("super_event_history", []) or []
        self.super_event_project = data.get("super_event_project")
        raw_regional_invitations = data.get("regional_invitations", [])
        self.regional_invitations = [dict(row) for row in raw_regional_invitations if isinstance(row, dict)] if isinstance(raw_regional_invitations, list) else []
        raw_regional_history = data.get("regional_invitation_history", [])
        self.regional_invitation_history = [dict(row) for row in raw_regional_history if isinstance(row, dict)][-120:] if isinstance(raw_regional_history, list) else []
        self.fanbase = data.get("fanbase", {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []})
        self.historical_records = data.get("historical_records", {}) or {}
        for key, value in {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}.items():
            self.fanbase.setdefault(key, value)
        self.academy = data.get("academy", self.academy_defaults() if hasattr(self, "academy_defaults") else {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True})
        if hasattr(self, "repair_academy"):
            self.repair_academy(self.academy)
        else:
            for key, value in {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True}.items(): self.academy.setdefault(key, value)
        for prospect in self.academy["prospects"] + self.academy["talent_pool"]:
            prospect.setdefault("amateur_weight", "Youth Openweight")
        self.inbox = data.get("inbox", [])
        self.inbox_hidden_types = set(data.get("inbox_hidden_types", []))
        self.owner_goals = data.get("owner_goals", self.seed_owner_goals())
        if hasattr(self, "ensure_owner_goal_records"):
            self.ensure_owner_goal_records()
        self.belts = self.normalize_belts(data.get("belts", self.blank_belts()))
        self.interim_belts = self.normalize_belts(data.get("interim_belts", self.blank_belts()))
        self.special_belts = self.normalize_special_belts(data.get("special_belts", {}))
        self.belt_history = self.normalize_belt_history(data.get("belt_history", self.blank_belt_history()))
        self.closed_divisions = set(data.get("closed_divisions", []))
        self.player_managed_divisions = set(data.get("player_managed_divisions", self.closed_divisions))
        current_delay = 2150
        if hasattr(self, "fight_timer_delay"):
            current_delay = self.fight_timer_delay.get()
        saved_delay = int(data.get("fight_timer_delay", current_delay))
        # 950 ms was the old shipped default. Move old-default saves to the
        # more readable live-fight pace, while respecting deliberate custom speeds.
        if saved_delay == 950:
            saved_delay = 2150
        self._loaded_fight_timer_delay = max(120, min(3000, saved_delay))
        self.rules = data.get("rules", {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200})
        self.rules.setdefault("scouting_mode", True)
        if self.spectator_mode:
            self.rules["scouting_mode"] = False
        self.ensure_rule_defaults()
        lineage_migration = self.migrate_lineal_belt_histories()
        if lineage_migration.get("updated"):
            summary = (
                f"Lineal belt history migration rebuilt {lineage_migration['updated']} promotion lineage set(s) "
                f"from archived title results without parallel champion changes."
            )
            self.change_journal.append({"date": self.format_game_date(), "type": "Migration", "summary": summary})
            self.change_journal = self.change_journal[-400:]
        future_lineage_repair = self.repair_future_belt_history_dates()
        if future_lineage_repair.get("entries"):
            summary = (
                f"Title lineage date repair corrected {future_lineage_repair['entries']} future-dated title "
                f"history entr{'y' if future_lineage_repair['entries'] == 1 else 'ies'} across "
                f"{future_lineage_repair.get('companies', 0)} promotion(s)."
            )
            self.change_journal.append({"date": self.format_game_date(), "type": "Migration", "summary": summary})
            self.change_journal = self.change_journal[-400:]
        self.broadcasters = data.get("broadcasters", [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        # A save written before broadcast contracts existed carries perpetual
        # providers; give them a term rather than letting them lapse on load.
        self.ensure_broadcast_contract_defaults()
        self.ensure_media_system()
        self.weight_classes = list(dict.fromkeys(
            self.game_weight_class(weight) for weight in data.get("weight_classes", list(WEIGHTS))
            if self.game_weight_class(weight) in WEIGHTS
        )) or list(WEIGHTS)
        self.post_show_bonuses = data.get("post_show_bonuses", {"fight": 5000, "ko": 5000, "sub": 5000})
        self.scheduled_events = data.get("scheduled_events", [])
        raw_grand_prix = data.get("grand_prix_series", [])
        self.grand_prix_series = [dict(row) for row in raw_grand_prix if isinstance(row, dict)] if isinstance(raw_grand_prix, list) else []
        # Older builds silently moved cancelled bouts to other cards or created a
        # dedicated Rebooked Bouts show. Player cards now remain entirely manual.
        rebooked_name = f"{self.player_company_name} Rebooked Bouts"
        self.scheduled_events = [event for event in self.scheduled_events if event.get("name") != rebooked_name]
        self.pending_rebookings = data.get("pending_rebookings", [])
        for event in self.scheduled_events:
            event.setdefault("week", 1)
            for fight in event.get("fights", []):
                supplied_plans = fight.get("fight_plans", {})
                supplied_plans = supplied_plans if isinstance(supplied_plans, dict) else {}
                fighter_ids = [str(fighter_id or "") for fighter_id in fight.get("fighter_ids", [])]
                fight["fight_plans"] = {
                    fighter_id: self.normalize_fight_plan(supplied_plans.get(fighter_id, "Balanced"))
                    for fighter_id in fighter_ids if fighter_id
                }
        if hasattr(self, "migrate_grand_prix_series"):
            self.migrate_grand_prix_series()
        # All persisted event collections are now present; migrate IDs against
        # the complete graph before any domain code starts referencing them.
        self.ensure_foundation_ids()
        migrate_presence = getattr(self, "migrate_current_membership_presence", None)
        if callable(migrate_presence):
            migrate_presence()
        booking_restore = self.repair_player_scheduled_fighter_references()
        if booking_restore["unresolved"]:
            refs = ", ".join(booking_restore["unresolved"][:3])
            raise ValueError(f"Scheduled card contains unresolved or ambiguous fighter reference(s): {refs}")
        self.repair_booking_conflicts()
        self.news = data.get("news", [])
        # Chronicle entries are newest-first; retain the newest 800 from older,
        # oversized saves rather than accidentally keeping their oldest stories.
        self.world_chronicle = data.get("world_chronicle", [])[:800]
        self.repair_story_threads(data.get("story_threads", []))
        raw_story_subscriptions = data.get("story_subscriptions", [])
        self.story_subscriptions = [dict(value) for value in raw_story_subscriptions if isinstance(value, dict)][-100:] if isinstance(raw_story_subscriptions, list) else []
        if hasattr(self, "ensure_story_subscriptions"):
            self.ensure_story_subscriptions()
        raw_relationship_cases = data.get("relationship_cases", [])
        self.relationship_cases = [dict(value) for value in raw_relationship_cases if isinstance(value, dict)][-200:] if isinstance(raw_relationship_cases, list) else []
        if hasattr(self, "ensure_relationship_cases"):
            self.ensure_relationship_cases()
        self.event_log = list(data.get("event_log", []))[:EVENT_LOG_LIMIT]
        self.season_stats = data.get("season_stats", {})
        self.awards_history = data.get("awards_history", [])
        self.clean_numbered_fighter_names()
        closed_division_repair = self.reconcile_closed_player_division_roster()
        if closed_division_repair:
            self.change_journal.append({
                "date": self.format_game_date(),
                "type": "Roster Repair",
                "summary": (
                    f"Released {closed_division_repair} fighter(s) retained in closed player divisions. "
                    "Reopen a division through Manage Divisions before signing fighters into it."
                ),
            })
            self.change_journal = self.change_journal[-400:]
        ai_closed_division_repair = self.reconcile_closed_ai_division_rosters()
        if ai_closed_division_repair:
            self.change_journal.append({
                "date": self.format_game_date(),
                "type": "Roster Repair",
                "summary": f"Released {ai_closed_division_repair} fighter(s) retained in closed AI divisions.",
            })
            self.change_journal = self.change_journal[-400:]
        regional_repairs = self.repair_regional_fighter_tracking()
        regional_title_repairs = self.repair_regional_title_state()
        if regional_repairs["origin"] or regional_repairs["activity"] or regional_repairs.get("division_activity", 0):
            self.change_journal.append({
                "date": self.format_game_date(),
                "type": "Migration",
                "summary": (
                    f"Regional tracking repaired {regional_repairs['origin']} feeder origins and "
                    f"{regional_repairs['activity']} last-fight activity dates; seeded "
                    f"{regional_repairs.get('division_activity', 0)} division activity markers."
                ),
            })
            self.change_journal = self.change_journal[-400:]
        if regional_title_repairs["divisions"]:
            self.change_journal.append({
                "date": self.format_game_date(),
                "type": "Migration",
                "summary": (
                    f"Regional title repair vacated {regional_title_repairs['divisions']} incorrectly appointed feeder titles "
                    f"and cleared stale title status from {regional_title_repairs['fighters']} fighter(s)."
                ),
            })
            self.change_journal = self.change_journal[-400:]
        self.normalize_gym_assignments()
        self.sync_gym_membership()
        loaded_fighters = list(self.roster) + list(self.free_agents) + list(self.retired_fighters)
        for promo in self.promotions:
            loaded_fighters.extend(promo.roster)
        for sport_world in self.combat_sport_worlds.values():
            loaded_fighters.extend(sport_world.get("roster", []))
        for fighter in loaded_fighters:
            fighter.camp_quality = self.gym_quality(fighter.camp)
        migration = self.migrate_detailed_skill_balance(loaded_fighters)
        if migration.get("fighters", 0):
            summary = (
                f"Detailed-skill balance repair updated {migration['fighters']:,} saturated fighter profiles "
                f"across {migration['groups']:,} skill groups. Average OVR change {migration['average_delta']:+.2f}; "
                f"largest change {migration['minimum_delta']} point(s)."
            )
            self.inbox.append({"subject": "Detailed Skill Balance Repair", "body": summary, "type": "Rules", "resolved": False})
            self.change_journal.append({"date": self.format_game_date(), "type": "Migration", "summary": summary})
            self.change_journal = self.change_journal[-400:]
        frame_repair = self.migrate_division_frame_mismatch(loaded_fighters)
        if frame_repair.get("repaired", 0) or frame_repair.get("reflagged", 0):
            summary = (
                f"Division frame repair reset {frame_repair['repaired']:,} fighter frame(s) that sat far below the "
                f"division they compete in (worst {frame_repair['worst']} pound(s) under natural size) and "
                f"refreshed the division-fit rating on {frame_repair.get('reflagged', 0):,} profile(s)."
            )
            self.inbox.append({"subject": "Division Frame Repair", "body": summary, "type": "Rules", "resolved": False})
            self.change_journal.append({"date": self.format_game_date(), "type": "Migration", "summary": summary})
            self.change_journal = self.change_journal[-400:]
        realism_updates = self.migrate_signature_real_fighter_profiles(loaded_fighters)
        if realism_updates:
            names = ", ".join(realism_updates)
            self.inbox.append({
                "subject": "Real Fighter Profile Update",
                "body": f"Authored engine profiles were applied to {names}. Existing career-earned rating movement was preserved.",
                "type": "Rules", "resolved": False,
            })
        identity_repair = self.migrate_real_fighter_identity_and_records(loaded_fighters)
        if identity_repair["identity"] or identity_repair["records"]:
            self.change_journal.append({
                "date": self.format_game_date(),
                "type": "Migration",
                "summary": (
                    f"Verified real-fighter identity data repaired {identity_repair['identity']} profile(s) "
                    f"and restored pre-universe record baselines for {identity_repair['records']} profile(s)."
                ),
            })
            self.change_journal = self.change_journal[-400:]
        self.rebalance_ai_finance_model()
        self.maintain_inbox()

    def set_player_event_location_default(self):
        """Start the next player card in the active promotion's home market."""
        region = self.player_region if self.player_region in REGIONS else "USA"
        cities = REGION_CITIES.get(region, REGION_CITIES["USA"])
        self.event_region.set(region)
        self.event_city.set(cities[0])
        if hasattr(self, "update_city_options"):
            self.update_city_options()

    def reconcile_closed_player_division_roster(self):
        """Keep closed player divisions empty when loading a legacy save."""
        closed = set(getattr(self, "closed_divisions", set()) or ())
        if not closed:
            return 0
        released = [
            fighter for fighter in self.roster
            if self.belt_key(fighter.gender, fighter.weight) in closed
        ]
        if not released:
            return 0
        released_names = {fighter.name for fighter in released}
        self.booked = [
            fight for fight in getattr(self, "booked", [])
            if not (set(self.event_fight_participants(fight)) & released_names)
        ]
        for event in getattr(self, "scheduled_events", []):
            event["fights"] = [
                fight for fight in event.get("fights", [])
                if not (set(self.event_fight_participants(fight)) & released_names)
            ]
        self.scheduled_events = [
            event for event in getattr(self, "scheduled_events", []) if event.get("fights")
        ]
        self.belts = self.normalize_belts(self.belts)
        self.interim_belts = self.normalize_belts(self.interim_belts)
        self.belt_history = self.normalize_belt_history(getattr(self, "belt_history", {}) or {})
        closed_holders = {
            key: (self.belts.get(key, ""), self.interim_belts.get(key, ""))
            for key in closed
        }
        existing_ids = {fighter.fighter_id for fighter in self.free_agents}
        for fighter in released:
            # Legacy saves can contain contracted fighters in a division that
            # is now closed.  Treat this as a real departure: preserve the
            # holder-linked vacancy and append an ID-linked membership fact
            # before changing champion flags or roster membership.
            self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
                fighter, self.roster, self.belts, self.interim_belts, self.belt_history,
                "Released while reconciling a closed player division.",
            )
            membership = getattr(self, "record_membership_event", None)
            if callable(membership):
                membership(
                    fighter, "leave", company_name=getattr(self, "player_company_name", ""),
                    reason="Released while reconciling a closed player division.",
                    source_transaction=f"load-reconcile-player-closed:{getattr(fighter, 'fighter_id', '')}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                )
            fighter.champion = False
            fighter.interim_champion = False
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.ai_offer_company = ""
            fighter.ai_offer_purse = 0
            fighter.ai_offer_months = 0
            fighter.ai_offer_signing_bonus = 0
            if fighter.fighter_id not in existing_ids:
                self.free_agents.append(fighter)
                existing_ids.add(fighter.fighter_id)
        # Clear any orphaned holder names left by a legacy save only after all
        # known holders have gone through vacate_fighter_belts.  Keep a
        # division-closure history row for those names so this repair remains
        # explainable in title lineage views.
        for key, (primary_holder, interim_holder) in closed_holders.items():
            self.belts[key] = ""
            self.interim_belts[key] = ""
            if primary_holder:
                self.belt_history = self.record_belt_history(
                    self.belt_history, key, "Division Closed", primary_holder,
                    "Closed division reconciled while loading a legacy save.",
                )
            if interim_holder:
                self.belt_history = self.record_belt_history(
                    self.belt_history, key, "Division Closed", interim_holder,
                    "Closed division reconciled while loading a legacy save.",
                )
        self.roster = [fighter for fighter in self.roster if fighter not in released]
        return len(released)

    def reconcile_closed_ai_division_rosters(self):
        """Release legacy AI roster entries in divisions their promotion has closed."""
        released_total = 0
        existing_ids = {fighter.fighter_id for fighter in self.free_agents}
        for promo in self.promotions:
            closed = self.company_closed_divisions(promo)
            if not closed:
                continue
            released = [
                fighter for fighter in promo.roster
                if self.belt_key(fighter.gender, fighter.weight) in closed
            ]
            if not released:
                continue
            released_names = {fighter.name for fighter in released}
            for event in list(getattr(promo, "scheduled_events", []) or []):
                event["fights"] = [
                    fight for fight in event.get("fights", [])
                    if not (set(self.event_fight_participants(fight)) & released_names)
                ]
            promo.scheduled_events = [
                event for event in (getattr(promo, "scheduled_events", []) or []) if event.get("fights")
            ]
            promo.belts = self.normalize_belts(promo.belts or {})
            promo.interim_belts = self.normalize_belts(promo.interim_belts or {})
            promo.belt_history = self.normalize_belt_history(getattr(promo, "belt_history", {}) or {})
            closed_holders = {
                key: (promo.belts.get(key, ""), promo.interim_belts.get(key, ""))
                for key in closed
            }
            for fighter in released:
                # Keep the AI/legacy repair on the same vacancy boundary as
                # normal contract expiry and roster cuts.
                promo.belts, promo.interim_belts, promo.belt_history = self.vacate_fighter_belts(
                    fighter, promo.roster, promo.belts, promo.interim_belts, promo.belt_history,
                    "Released while reconciling a closed AI division.",
                )
                membership = getattr(self, "record_membership_event", None)
                if callable(membership):
                    membership(
                        fighter, "leave", promotion=promo,
                        reason="Released while reconciling a closed AI division.",
                        source_transaction=f"load-reconcile-ai-closed:{getattr(fighter, 'fighter_id', '')}:{getattr(promo, 'name', '')}:{getattr(self, 'month', 0)}:{getattr(self, 'week', 0)}",
                    )
                fighter.champion = False
                fighter.interim_champion = False
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Free Agent"
                fighter.ai_offer_company = ""
                fighter.ai_offer_purse = 0
                fighter.ai_offer_months = 0
                fighter.ai_offer_signing_bonus = 0
                if fighter.fighter_id not in existing_ids:
                    self.free_agents.append(fighter)
                    existing_ids.add(fighter.fighter_id)
            for key, (primary_holder, interim_holder) in closed_holders.items():
                promo.belts[key] = ""
                promo.interim_belts[key] = ""
                if primary_holder:
                    promo.belt_history = self.record_belt_history(
                        promo.belt_history, key, "Division Closed", primary_holder,
                        "Closed division reconciled while loading a legacy save.",
                    )
                if interim_holder:
                    promo.belt_history = self.record_belt_history(
                        promo.belt_history, key, "Division Closed", interim_holder,
                        "Closed division reconciled while loading a legacy save.",
                    )
            promo.roster = [fighter for fighter in promo.roster if fighter not in released]
            released_total += len(released)
        return released_total

    def migrate_division_frame_mismatch(self, fighters):
        """One-time repair for frames left far below the division they compete in.

        The size-fit model measured a natural frame about twenty-five pounds
        lighter than the generator built, so nothing was ever flagged as
        undersized and nothing grew. Saves accumulated fighters whose frame had
        no relation to their class at all -- a 131lb light heavyweight. Growing
        eighty pounds is not something the monthly acclimatisation can
        plausibly do, so clearly broken frames are reset into their division's
        natural band once. Mild mismatches are left alone: those are a real
        part of the game and acclimatisation now handles them.
        """
        version = int(getattr(self, "rules", {}).get("division_frame_repair_version", 0) or 0)
        if version >= 1:
            return {"repaired": 0, "worst": 0}
        repaired = 0
        reflagged = 0
        worst = 0
        seen = set()
        for fighter in fighters:
            if id(fighter) in seen or getattr(fighter, "weight", "") not in WEIGHT_LIMITS:
                continue
            seen.add(id(fighter))
            walk = int(getattr(fighter, "walk_weight", 0) or 0)
            if not walk:
                continue
            natural = self.natural_walk_weight_for(fighter, fighter.weight)
            shortfall = natural - walk
            if shortfall > 20:
                worst = max(worst, shortfall)
                fighter.walk_weight = self.default_walk_weight(fighter)
                repaired += 1
            # Every stored penalty was written by the old model and reads zero.
            # Refresh it from the real frame, or a mild mismatch stays invisible
            # forever: monthly acclimatisation only runs on a fighter who is
            # already carrying a penalty, so it would never grow them in.
            current = self.division_size_penalty_for(fighter, fighter.weight)
            if current != int(getattr(fighter, "division_size_penalty", 0) or 0):
                fighter.division_size_penalty = current
                fighter.division_size_note = (
                    f"Undersized for {fighter.weight}: division-fit penalty {current}/14."
                    if current else "Natural division fit."
                )
                reflagged += 1
        self.rules["division_frame_repair_version"] = 1
        return {"repaired": repaired, "reflagged": reflagged, "worst": worst}

    def migrate_detailed_skill_balance(self, fighters):
        """One-time repair for saves created by group-wide detailed growth."""
        version = int(getattr(self, "rules", {}).get("detailed_skill_balance_version", 0) or 0)
        if version >= 1:
            return {"fighters": 0, "groups": 0, "average_delta": 0.0, "minimum_delta": 0}
        seen = set()
        reports = []
        for fighter in fighters:
            identity = id(fighter)
            if identity in seen:
                continue
            seen.add(identity)
            report = self.rebalance_saturated_detailed_skills(fighter, max_overall_drop=2)
            if report.get("groups"):
                reports.append(report)
        self.rules["detailed_skill_balance_version"] = 1
        deltas = [report["after"] - report["before"] for report in reports]
        return {
            "fighters": len(reports),
            "groups": sum(len(report["groups"]) for report in reports),
            "average_delta": round(sum(deltas) / max(1, len(deltas)), 2),
            "minimum_delta": min(deltas, default=0),
            "capped_before": sum(report.get("original_capped", 0) for report in reports),
            "capped_after": sum(report.get("new_capped", 0) for report in reports),
        }

    def migrate_signature_real_fighter_profiles(self, fighters):
        """Apply authored technique profiles once without resetting simulated careers."""
        updated = []
        seen = set()
        signature_profiles = None
        for fighter in fighters:
            if id(fighter) in seen or getattr(fighter, "primary_discipline", "MMA") != "MMA":
                continue
            seen.add(id(fighter))
            if getattr(fighter, "realism_profile_version", 0) >= 1:
                continue
            if signature_profiles is None:
                signature_profiles = self.signature_real_fighter_detailed_profiles()
            if self.apply_signature_real_fighter_profile(fighter, preserve_career=True, signature_profiles=signature_profiles):
                updated.append(fighter.name)
        return sorted(set(updated))

    def migrate_real_fighter_profiles(self, fighters):
        """One-time migration for saves made before deterministic real-fighter profiles."""
        seed_db = self.load_seed_fighter_database()
        records = {
            self.fighter_name_key(record.get("name", "")): record
            for record in seed_db.get("all_fighters", [])
            if isinstance(record, dict) and record.get("name")
        }
        recalibrated = 0
        for fighter in fighters:
            record = records.get(self.fighter_name_key(fighter.name))
            if not record or getattr(fighter, "rating_profile_version", 0) >= 3:
                continue
            baseline = int(record.get("profile_rating", record.get("rating", fighter.overall)) or fighter.overall)
            self.apply_real_fighter_profile(fighter, baseline)
            recalibrated += 1
        return recalibrated

    def real_fighter_universe_results(self, fighter):
        """Count only simulated professional results recorded in the ledger."""
        wins = losses = draws = 0
        name = str(fighter.name)
        for entry in getattr(fighter, "fight_history", []) or []:
            line = str(entry)
            if "amateur" in line.lower():
                continue
            if f"{name} def. " in line or "W over" in line:
                wins += 1
            elif "fought to a draw" in line:
                draws += 1
            elif (" def. " in line and name in line) or "L to" in line:
                losses += 1
        return wins, losses, draws

    def migrate_real_fighter_identity_and_records(self, fighters):
        """Repair verified identities and baseline records without rewinding careers."""
        seen = set()
        identity_updates = record_updates = 0
        for fighter in fighters:
            if id(fighter) in seen or getattr(fighter, "generated", False):
                continue
            seen.add(id(fighter))
            record = self.seed_fighter_record_for(fighter.name)
            identity = {}
            if record:
                identity = {
                    "city": record.get("hometown", ""),
                    "birth_country": record.get("birth_country", ""),
                    "citizenship": record.get("birth_country", ""),
                    "nationality": record.get("nationality", ""),
                }
            if not any(identity.values()):
                identity = self.real_fighter_identity_data(fighter.name)
            if not identity:
                continue
            if getattr(fighter, "real_identity_version", 0) < 2:
                if record:
                    if record.get("nationality"):
                        fighter.nationality = record["nationality"]
                    if record.get("birth_country"):
                        fighter.birth_country = record["birth_country"]
                        fighter.birth_region = COUNTRY_TO_REGION.get(fighter.birth_country, getattr(fighter, "birth_region", "") or fighter.region)
                    if record.get("hometown"):
                        fighter.hometown = record["hometown"]
                else:
                    self.apply_real_fighter_birthplace(fighter, fighter.region)
                fighter.real_identity_version = 2
                identity_updates += 1
            if getattr(fighter, "real_record_baseline_version", 0) < 2:
                wins, losses, draws = self.real_fighter_universe_results(fighter)
                fighter.record_history_baseline_w = max(0, fighter.record_w - wins)
                fighter.record_history_baseline_l = max(0, fighter.record_l - losses)
                fighter.record_history_baseline_d = max(0, fighter.record_d - draws)
                fighter.multi_sport_records = dict(getattr(fighter, "multi_sport_records", None) or {})
                fighter.multi_sport_records["MMA"] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
                fighter.real_record_baseline_version = 2
                record_updates += 1
        return {"identity": identity_updates, "records": record_updates}

    def migrate_legend_prime_ages(self, fighters):
        prime_ages = self.prime_legend_ages()
        rejuvenated = 0
        for fighter in fighters:
            target_age = prime_ages.get(fighter.name)
            if target_age is None or getattr(fighter, "legend_prime_age_version", 0) >= 1:
                continue
            fighter.age = target_age
            fighter.prime_start = max(23, target_age - 4)
            fighter.prime_end = max(target_age + 5, 33)
            fighter.legend_prime_age_version = 1
            rejuvenated += 1
        return rejuvenated

    def ensure_fighter_business_stats(self, fighter):
        if not getattr(fighter, "stance", ""):
            fighter.stance = random.choices(["Orthodox", "Southpaw", "Switch"], weights=[58, 29, 13], k=1)[0]
        if not getattr(fighter, "star_quality", 0):
            fighter.star_quality = max(1, min(99, round(fighter.popularity * 0.55 + fighter.overall * 0.25 + random.randint(0, 28))))
        if not getattr(fighter, "charisma", 0):
            fighter.charisma = max(1, min(99, round(fighter.popularity * 0.45 + random.randint(15, 55))))
        if not getattr(fighter, "professionalism", 0):
            fighter.professionalism = random.randint(38, 88)
        if not getattr(fighter, "injury_proneness", 0):
            fighter.injury_proneness = random.randint(8, 42)
        if not getattr(fighter, "finishing_instinct", 0):
            fighter.finishing_instinct = max(1, min(99, round((fighter.striking + fighter.grappling) / 2 + random.randint(-10, 18))))
        if not getattr(fighter, "media_presence", 0):
            fighter.media_presence = max(1, min(99, round(fighter.popularity * 0.55 + fighter.charisma * 0.35 + fighter.media_heat * 0.7)))
        if not getattr(fighter, "sponsor_appeal", 0):
            fighter.sponsor_appeal = max(1, min(99, round(fighter.star_quality * 0.35 + fighter.charisma * 0.25 + fighter.professionalism * 0.25 + fighter.popularity * 0.25)))
        if not getattr(fighter, "portrait_bg", "") or not getattr(fighter, "portrait_accent", ""):
            fighter.portrait_bg, fighter.portrait_accent = self.generate_portrait_palette(fighter.name)
        # This only creates a vector when a save has none. Existing vectors are
        # intentionally retained, even if a future portrait generator changes.
        ensure_portrait_identity(fighter)
        fighter.nationality = getattr(fighter, "nationality", "") or self.infer_nationality(fighter.name, fighter.region)
        # Identity fields were added after the original regional system.  Old
        # saves retain their existing base as a sensible local origin instead
        # of needing a destructive migration.
        if not getattr(fighter, "birth_region", ""):
            self.assign_regional_identity(fighter, fighter.region, birth_region=fighter.region, force=True)
        else:
            fighter.birth_country = getattr(fighter, "birth_country", "") or REGION_COUNTRIES.get(fighter.birth_region, fighter.birth_region)
            fighter.hometown = getattr(fighter, "hometown", "") or random.choice(REGION_CITIES.get(fighter.birth_region, [fighter.birth_region]))
            fighter.residence = getattr(fighter, "residence", "") or fighter.region
            fighter.training_location = getattr(fighter, "training_location", "") or fighter.residence
            fighter.fighting_base = getattr(fighter, "fighting_base", "") or fighter.residence
            fighter.cultural_connections = getattr(fighter, "cultural_connections", None) or list(dict.fromkeys([fighter.birth_region, fighter.residence, fighter.training_location]))
            markets = getattr(fighter, "regional_popularity", None) or {}
            fighter.regional_popularity = {
                region: max(0, min(100, int(value)))
                for region, value in markets.items()
                if region in REGIONS
            }
            fighter.regional_popularity[fighter.birth_region] = max(fighter.regional_popularity.get(fighter.birth_region, 0), min(65, 18 + fighter.popularity // 3))
            fighter.home_event_history = getattr(fighter, "home_event_history", None) or []
        fighter.record_d = getattr(fighter, "record_d", 0)
        fighter.interim_title_wins = max(0, getattr(fighter, "interim_title_wins", 0) or 0)
        fighter.interim_title_defenses = max(0, getattr(fighter, "interim_title_defenses", 0) or 0)
        fighter.special_titles = list(getattr(fighter, "special_titles", None) or [])
        history = fighter.fight_history or []
        # Old simulations could occasionally persist the exact same event line
        # twice. Preserve chronological order while repairing only exact repeats.
        seen_history, cleaned_history = set(), []
        for entry in history:
            key = str(entry).strip()
            if key and key in seen_history:
                continue
            seen_history.add(key)
            cleaned_history.append(entry)
        fighter.fight_history = cleaned_history
        fighter.bout_rating_history = getattr(fighter, "bout_rating_history", None) or []
        self.migrate_academy_amateur_history(fighter)
        self.repair_legacy_generated_entry(fighter)
        self.ensure_fighter_history_baseline(fighter)
        entry_year = max(2026, int(getattr(fighter, "universe_entry_year", 0) or 2026))
        fighter.annual_overalls = fighter.annual_overalls or {str(entry_year): fighter.overall}
        self.update_fighter_peak_overall(fighter)
        fighter.motivation = getattr(fighter, "motivation", 65) or 65
        fighter.retirement_pending = bool(getattr(fighter, "retirement_pending", False))
        fighter.retirement_requested_month = max(0, getattr(fighter, "retirement_requested_month", 0) or 0)
        fighter.retirement_fight_completed = bool(getattr(fighter, "retirement_fight_completed", False))
        fighter.retirement_fight_due_after_month = max(0, getattr(fighter, "retirement_fight_due_after_month", 0) or 0)
        # Day-precision clock. Saves written before cards carried a weekday have
        # neither value; zero means "fall back to the week-level fields".
        fighter.available_day = max(0, int(getattr(fighter, "available_day", 0) or 0))
        fighter.last_fight_day_index = max(0, int(getattr(fighter, "last_fight_day_index", 0) or 0))
        fighter.comeback_completion_prompted = bool(getattr(fighter, "comeback_completion_prompted", False))
        fighter.camp_quality = getattr(fighter, "camp_quality", 0) or self.gym_quality(fighter.camp)
        fighter.camp_joined_month = max(0, getattr(fighter, "camp_joined_month", 0) or 0)
        fighter.camp_history = getattr(fighter, "camp_history", None) or []
        fighter.walk_weight = getattr(fighter, "walk_weight", 0) or self.default_walk_weight(fighter)
        fighter.scale_weight = getattr(fighter, "scale_weight", 0.0) or 0.0
        fighter.missed_weight = getattr(fighter, "missed_weight", False)
        fighter.weight_cut_penalty = getattr(fighter, "weight_cut_penalty", 0) or 0
        fighter.elo_rating = getattr(fighter, "elo_rating", 1500) or 1500
        fighter.rivalry_history = getattr(fighter, "rivalry_history", None) or []
        fighter.serious_injury = getattr(fighter, "serious_injury", "") or ""
        fighter.serious_injury_pending = bool(getattr(fighter, "serious_injury_pending", False))
        fighter.serious_injury_history = getattr(fighter, "serious_injury_history", None) or []
        fighter.serious_injury_recurrence = max(0, getattr(fighter, "serious_injury_recurrence", 0) or 0)
        fighter.rivalry_heat = max(0, min(100, getattr(fighter, "rivalry_heat", 0) or 0))
        fighter.rivalry_origin = getattr(fighter, "rivalry_origin", "") or ""
        fighter.rivalry_rematch_due = bool(getattr(fighter, "rivalry_rematch_due", False))
        fighter.rivalry_last_month = max(0, getattr(fighter, "rivalry_last_month", 0) or 0)
        fighter.weight_class_history = getattr(fighter, "weight_class_history", None) or []
        fighter.weight_move_last_month = getattr(fighter, "weight_move_last_month", -99)
        fighter.career_achievements = getattr(fighter, "career_achievements", None) or []
        fighter.career_goal = getattr(fighter, "career_goal", "") or ""
        fighter.career_goal_target = max(0, getattr(fighter, "career_goal_target", 0) or 0)
        fighter.career_goal_progress = max(0, min(100, getattr(fighter, "career_goal_progress", 0) or 0))
        fighter.career_goal_history = getattr(fighter, "career_goal_history", None) or []
        fighter.career_win_streak = max(0, getattr(fighter, "career_win_streak", 0) or 0)
        fighter.crossroads_story_key = str(getattr(fighter, "crossroads_story_key", "") or "")
        fighter.farewell_story_key = str(getattr(fighter, "farewell_story_key", "") or "")
        relationship_keys = getattr(fighter, "relationship_story_keys", None)
        fighter.relationship_story_keys = list(dict.fromkeys(
            str(value) for value in relationship_keys if value
        ))[-4:] if isinstance(relationship_keys, list) else []
        fighter.career_goal_last_review = max(0, getattr(fighter, "career_goal_last_review", 0) or 0)
        fighter.career_arc = getattr(fighter, "career_arc", None) or None
        if not isinstance(fighter.career_arc, dict):
            fighter.career_arc = None
        fighter.career_arc_history = getattr(fighter, "career_arc_history", None) or []
        fighter.career_arc_last_offer_month = max(0, getattr(fighter, "career_arc_last_offer_month", 0) or 0)
        fighter.academy_graduate = bool(
            getattr(fighter, "academy_graduate", False)
            or "Fighting Academy" in str(getattr(fighter, "feeder_origin", ""))
            or any("Promoted from the Fighting Academy" in str(entry) for entry in (getattr(fighter, "fight_history", None) or []))
        )
        fighter.academy_graduated_month = max(0, getattr(fighter, "academy_graduated_month", 0) or 0)
        if fighter.academy_graduate and not fighter.academy_graduated_month:
            fighter.academy_graduated_month = max(1, getattr(fighter, "camp_joined_month", 0) or self.month)
        fighter.ranking_position = max(0, getattr(fighter, "ranking_position", 0) or 0)
        fighter.previous_ranking_position = max(0, getattr(fighter, "previous_ranking_position", 0) or 0)
        fighter.ranking_reason = getattr(fighter, "ranking_reason", "") or ""
        if not fighter.career_goal:
            self.assign_career_goal(fighter)
        fighter.negotiation_persona = getattr(fighter, "negotiation_persona", "") or "Professional"
        fighter.agent_name = getattr(fighter, "agent_name", "") or "Independent"
        fighter.free_agent_months = max(0, getattr(fighter, "free_agent_months", 0) or 0)
        fighter.player_talent_alerted = bool(getattr(fighter, "player_talent_alerted", False))
        fighter.player_talent_window_until = max(0, getattr(fighter, "player_talent_window_until", 0) or 0)
        # Career timing is a permanent archetype, not a camp-changeable trait.
        if getattr(fighter, "career_arc_version", 0) < 2 and getattr(fighter, "legend_prime_age_version", 0) < 1:
            legacy_trait = getattr(fighter, "trait", "")
            if legacy_trait == "Late Prime":
                fighter.career_archetype = "Late Maturation"
                fighter.trait = "Technical Learner"
            elif legacy_trait == "Early Peak":
                fighter.career_archetype = "Early Maturation"
                fighter.trait = "Fast Starter"
            elif not getattr(fighter, "career_archetype", "") or fighter.career_archetype == "Standard Prime":
                if fighter.prime_end >= 36:
                    fighter.career_archetype = "Durable Career"
                elif fighter.prime_start <= 24:
                    fighter.career_archetype = "Early Maturation"
                else:
                    fighter.career_archetype = "Balanced Development"
            self.assign_career_arc(fighter)
            fighter.career_arc_version = 2

    def repair_legacy_generated_entry(self, fighter):
        """Repair old saves where post-launch entrants inherited seed history.

        Before entry provenance existed, the generic generator gave every new
        fighter an opening-universe record and a 2026 rating snapshot. We only
        repair fighters whose current age makes it mathematically impossible
        for them to have been an eligible 16-year-old at the 2026 launch, so
        genuine real-world and opening-universe records are left intact.
        """
        current_year = 2026 + max(0, int(getattr(self, "month", 1)) - 1) // 12
        years_elapsed = max(0, current_year - 2026)
        if fighter.age - years_elapsed >= 16:
            return

        history_months = []
        for entry in fighter.fight_history or []:
            text = str(entry)
            marker = "Month "
            if marker not in text:
                continue
            tail = text.split(marker, 1)[1].lstrip()
            digits = ""
            for character in tail:
                if not character.isdigit():
                    break
                digits += character
            if digits:
                history_months.append(max(1, int(digits)))
        earliest_month = min(history_months) if history_months else 0
        earliest_possible_year = max(2026, current_year - max(0, fighter.age - 16))
        entry_year = 2026 + (earliest_month - 1) // 12 if earliest_month else earliest_possible_year
        entry_year = max(earliest_possible_year, min(current_year, entry_year))

        fighter.generated = True
        fighter.universe_entry_month = earliest_month
        fighter.universe_entry_year = entry_year
        fighter.record_history_baseline_w = 0
        fighter.record_history_baseline_l = 0
        fighter.record_history_baseline_d = 0
        peaks = dict(fighter.annual_overalls or {})
        fighter.annual_overalls = {
            str(year): score for year, score in peaks.items()
            if str(year).isdigit() and int(year) >= entry_year
        }
        if not fighter.annual_overalls:
            fighter.annual_overalls = {str(entry_year): fighter.overall}

    def migrate_academy_amateur_history(self, fighter):
        """Move old academy text rows out of a graduate's pro record ledger.

        Earlier saves stored academy bouts as plain ``fight_history`` strings.
        That made a graduate's amateur losses appear in their professional
        in-universe record. The migration is deliberately additive: it retains
        each old bout as a structured amateur entry, then removes only those
        academy rows from the professional history.
        """
        existing = list(getattr(fighter, "amateur_bout_history", None) or [])
        history = list(getattr(fighter, "fight_history", None) or [])
        academy_lines = [str(entry) for entry in history if "amateur" in str(entry).lower()]
        if not academy_lines:
            fighter.amateur_bout_history = existing
            return

        known = {
            (str(record.get("month", "")), str(record.get("week", "")), str(record.get("opponent", "")), str(record.get("result", "")), str(record.get("method", "")))
            for record in existing if isinstance(record, dict)
        }
        converted = []
        fighter_name = re.escape(str(fighter.name))
        for line in academy_lines:
            month_match = re.search(r"Month\s+(\d+)(?:\s*,?\s*Week\s+(\d+))?", line, re.IGNORECASE)
            month = int(month_match.group(1)) if month_match else 0
            week = int(month_match.group(2)) if month_match and month_match.group(2) else 1
            result, opponent, method, round_no = "-", "Unknown opponent", "-", 0
            winner = re.search(rf"Amateur\s*-\s*{fighter_name}\s+def\.\s+(.+?)\s+by\s+(.+?)\s*\(R(\d+)", line, re.IGNORECASE)
            loser = re.search(rf"Amateur\s*-\s*(.+?)\s+def\.\s+{fighter_name}\s+by\s+(.+?)\s*\(R(\d+)", line, re.IGNORECASE)
            draw = re.search(r"Amateur\s+draw\s*-\s*(.+?)\s+vs\s+(.+?)\s*\((.+?),\s*R(\d+)\)", line, re.IGNORECASE)
            if winner:
                result, opponent, method, round_no = "W", winner.group(1).strip(), winner.group(2).strip(), int(winner.group(3))
            elif loser:
                result, opponent, method, round_no = "L", loser.group(1).strip(), loser.group(2).strip(), int(loser.group(3))
            elif draw:
                first, second = draw.group(1).strip(), draw.group(2).strip()
                result, opponent, method, round_no = "D", (second if first.casefold() == fighter.name.casefold() else first), "Draw", int(draw.group(4))
            weight_match = re.search(r",\s*([^,()]+?)\s+Academy\s+Showcase\)", line, re.IGNORECASE)
            weight = weight_match.group(1).strip() if weight_match else "Youth Openweight"
            record = {"month": month, "week": week, "event": "Academy Showcase", "opponent": opponent,
                      "result": result, "method": method, "round": round_no, "weight": weight, "legacy": True}
            key = (str(month), str(week), opponent, result, method)
            if key not in known:
                known.add(key)
                converted.append(record)

        fighter.amateur_bout_history = (existing + converted)[:100]
        fighter.fight_history = [entry for entry in history if "amateur" not in str(entry).lower()]
        fighter.amateur_w = max(int(getattr(fighter, "amateur_w", 0) or 0), sum(item.get("result") == "W" for item in fighter.amateur_bout_history))
        fighter.amateur_l = max(int(getattr(fighter, "amateur_l", 0) or 0), sum(item.get("result") == "L" for item in fighter.amateur_bout_history))
        fighter.amateur_d = max(int(getattr(fighter, "amateur_d", 0) or 0), sum(item.get("result") == "D" for item in fighter.amateur_bout_history))
        fighter.amateur_history_migration_version = 1
        # Academy graduates start their professional career in-universe. This
        # avoids preserving a stale baseline derived from the old mixed ledger.
        if "Fighting Academy" in str(getattr(fighter, "feeder_origin", "")) or any("Promoted from the Fighting Academy" in str(entry) for entry in fighter.fight_history):
            fighter.record_history_baseline_w = 0
            fighter.record_history_baseline_l = 0
            fighter.record_history_baseline_d = 0

    def ensure_fighter_history_baseline(self, fighter):
        """Separate imported records from fights actually played in this universe."""
        baseline_fields = ("record_history_baseline_w", "record_history_baseline_l", "record_history_baseline_d")
        if all(getattr(fighter, field, -1) >= 0 for field in baseline_fields):
            return tuple(getattr(fighter, field) for field in baseline_fields)
        wins = losses = draws = 0
        name = str(fighter.name)
        for entry in getattr(fighter, "fight_history", []) or []:
            line = str(entry)
            # Amateur rows belong to their separate background ledger and must
            # never contribute to a professional universe baseline.
            if "amateur" in line.lower():
                continue
            if f"{name} def. " in line or "W over" in line:
                wins += 1
            elif "fought to a draw" in line:
                draws += 1
            elif " def. " in line and name in line or "L to" in line:
                losses += 1
        baseline = (
            max(0, int(getattr(fighter, "record_w", 0)) - wins),
            max(0, int(getattr(fighter, "record_l", 0)) - losses),
            max(0, int(getattr(fighter, "record_d", 0)) - draws),
        )
        fighter.record_history_baseline_w, fighter.record_history_baseline_l, fighter.record_history_baseline_d = baseline
        return baseline

    def default_walk_weight(self, fighter):
        limit = WEIGHT_LIMITS.get(fighter.weight, 170)
        spread = 10 if limit <= 135 else 15 if limit <= 170 else 22 if limit <= 205 else 35
        if fighter.gender == "Female":
            spread = max(8, spread - 4)
        natural_size = self.ds(fighter, "natural_size", 50) if getattr(fighter, "detailed_skills", None) else 50
        size_adjust = round((natural_size - 50) / 8)
        return min(295, limit + max(4, random.randint(max(5, spread // 2), spread) + size_adjust))

    def save_group_names(self):
        folders_root = SAVE_DIR / "Folders"
        groups = ["Main"]
        if folders_root.exists():
            groups.extend(sorted((folder.name for folder in folders_root.iterdir() if folder.is_dir()), key=str.lower))
        return groups

    def set_save_manager_status(self, message=""):
        if hasattr(self, "save_manager_status"):
            self.save_manager_status.config(text=str(message))

    def _save_surface_notice(self, message):
        """Keep routine Game & Saves feedback beside the action that caused it.

        Persistence methods are also used by headless tests and legacy callers
        before the Game & Saves page has been built.  Return whether a live
        status surface accepted the message so those callers retain their
        compatibility fallback without forcing a transient dialog on the
        normal page.
        """
        if hasattr(self, "save_manager_status"):
            self.set_save_manager_status(message)
            return True
        return False

    def refresh_save_selection_summary(self, _event=None):
        """Keep the save inspector and selection-dependent actions synchronized."""
        selected = self.save_slot_list.curselection() if hasattr(self, "save_slot_list") else ()
        files = getattr(self, "save_slot_files", [])
        has_selection = bool(selected and selected[0] < len(files))
        if has_selection:
            self._save_selected_identity = self.save_entry_identity(files[selected[0]])
        for button_name in (
            "save_load_button", "save_copy_button", "save_delete_button",
            "save_backup_button", "save_move_button", "save_migrate_archetypes_button",
        ):
            button = getattr(self, button_name, None)
            if button is not None:
                button.configure(state="normal" if has_selection else "disabled")
        if not has_selection:
            if hasattr(self, "save_selection_title"):
                self.save_selection_title.set("No save selected")
            if hasattr(self, "save_selection_detail"):
                self.save_selection_detail.set("Choose a career above to load, copy, move, back up, or delete it.")
            return
        path = Path(files[selected[0]])
        slot_name = getattr(self, "save_slot_sources", {}).get(path, self.save_slot_name_from_path(path))
        group = getattr(self, "save_slot_groups", {}).get(path, self.save_slot_group_from_path(path))
        kind = "Spectator snapshot" if path.parent.name == "Snapshots" else "Career save"
        try:
            metadata = self.read_save_metadata_fast(path) or {}
        except Exception:
            metadata = {}
        company = str(metadata.get("company", "Unknown company"))
        saved_at = str(metadata.get("saved_at", "Unknown time"))[:16].replace("T", " ")
        month = metadata.get("month", "?")
        week = metadata.get("week", "?")
        if month == "?":
            game_date = "Unknown game date"
        else:
            # Metadata is an untrusted library read.  A malformed or
            # overflow-sized month/week must not reach ``calendar_parts`` and
            # crash the inspector; the raw save remains untouched for an
            # explicit load/migration boundary.
            try:
                if isinstance(month, bool) or isinstance(week, bool):
                    raise ValueError("boolean calendar metadata")
                if isinstance(month, float) and not math.isfinite(month):
                    raise ValueError("non-finite month")
                if isinstance(week, float) and not math.isfinite(week):
                    raise ValueError("non-finite week")
                parsed_month = int(month)
                parsed_week = int(week)
                if not (1 <= parsed_month <= 1_000_000 and 1 <= parsed_week <= 4):
                    raise ValueError("calendar metadata outside display bounds")
                game_date = self.format_game_date(parsed_month, parsed_week)
            except (TypeError, ValueError, OverflowError):
                game_date = "Unknown game date"
        try:
            # Keep this selection reader non-mutating. ``active_save_path()``
            # creates the active slot folder on demand, which is appropriate
            # for an explicit save but not for repainting the library.
            save_slot_reader = getattr(self, "save_slot_dir", None)
            if callable(save_slot_reader) and hasattr(self, "active_save_name"):
                active_path = save_slot_reader(create=False) / "savegame.json"
            else:
                # Lightweight legacy/test hosts may only expose the original
                # active_save_path hook; retain that compatibility shape.
                active_path = self.active_save_path()
            active = path.resolve() == active_path.resolve()
        except (OSError, ValueError):
            active = False
        active_note = " | ACTIVE" if active else ""
        if hasattr(self, "save_selection_title"):
            self.save_selection_title.set(f"{slot_name}  |  {group}{active_note}")
        if hasattr(self, "save_selection_detail"):
            self.save_selection_detail.set(f"{kind}  |  {company}  |  {game_date}  |  Saved {saved_at}")

    def create_save_folder(self):
        name = self.normalized_save_group(self.save_new_folder_name.get() if hasattr(self, "save_new_folder_name") else "")
        if name == "Main":
            self.set_save_manager_status("Enter a distinct folder name, such as Tests or Long-Term Saves.")
            return
        self.save_group_root(name).mkdir(parents=True, exist_ok=True)
        if hasattr(self, "save_folder_target"):
            self.save_folder_target.set(name)
        self.set_save_manager_status(f"Created save folder: {name}")
        self.refresh_game_menu()

    def move_selected_save_to_folder(self):
        path = self.selected_save_path()
        if not path.exists():
            self.set_save_manager_status("Select an existing save before moving it.")
            return
        source_root = self.save_slot_root_from_path(path)
        slot_name = source_root.name
        source_group = self.save_slot_group_from_path(source_root / "savegame.json")
        target_group = self.normalized_save_group(self.save_folder_target.get() if hasattr(self, "save_folder_target") else "Main")
        if source_group == target_group:
            self.set_save_manager_status(f"{slot_name} is already in {target_group}.")
            return
        target_root = self.save_group_root(target_group) / slot_name
        if target_root.exists():
            self.set_save_manager_status(f"Cannot move: {target_group} already contains a save named {slot_name}.")
            return
        try:
            target_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_root), str(target_root))
            active_path = self.active_save_path()
            try:
                was_active = active_path.resolve().is_relative_to(source_root.resolve())
            except (OSError, ValueError):
                was_active = False
            if was_active:
                self.set_active_save_location(slot_name, target_group)
            self.set_save_manager_status(f"Moved {slot_name} from {source_group} to {target_group}.")
        except Exception as exc:
            LOGGER.exception("Could not move save folder %s: %s", source_root, exc)
            self.set_save_manager_status(f"Move failed: {type(exc).__name__}: {exc}")
        self.refresh_game_menu()

    def duplicate_selected_save(self):
        """Copy a complete save slot without changing the active career.

        Slot-local backups, autosaves, crash recovery and spectator snapshots
        belong to the career, so duplication deliberately copies the directory
        rather than only the primary JSON file.
        """
        selected_path = self.selected_save_path()
        if not selected_path.exists():
            self.set_save_manager_status("Select an existing save to duplicate.")
            return
        source_root = self.save_slot_root_from_path(selected_path)
        source_primary = source_root / "savegame.json"
        if not source_primary.exists():
            self.set_save_manager_status("The selected entry is not attached to a complete save slot.")
            return
        source_name = self.save_slot_name_from_path(source_primary)
        target_group = self.normalized_save_group(
            self.save_folder_target.get() if hasattr(self, "save_folder_target") else self.save_slot_group_from_path(source_primary)
        )
        requested = self.safe_filename(self.save_slot_name.get()) if hasattr(self, "save_slot_name") else ""
        if not requested or requested.casefold() == source_name.casefold():
            base = f"{source_name} Copy"
            requested = base
            suffix = 2
            while (self.save_group_root(target_group, create=False) / requested).exists():
                requested = f"{base} {suffix}"
                suffix += 1
        target_root = self.save_group_root(target_group) / requested
        if target_root.exists():
            self.set_save_manager_status(f"Cannot duplicate: {target_group} already contains '{requested}'.")
            return
        try:
            target_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_root, target_root, copy_function=shutil.copy2)
            copied_primary = target_root / "savegame.json"
            copied_data = load_save_payload(copied_primary)
            copied_data["active_save_name"] = requested
            copied_data["active_save_group"] = target_group
            metadata = dict(copied_data.get("_save_meta", {}) or {})
            metadata.update({"slot_name": requested, "folder": target_group, "saved_at": datetime.now().isoformat(timespec="seconds")})
            copied_data["_save_meta"] = metadata
            atomic_write_split_save(copied_primary, copied_data)
            self.write_save_metadata_sidecar(copied_primary, metadata)
        except Exception as exc:
            LOGGER.exception("Could not duplicate save slot %s to %s: %s", source_root, target_root, exc)
            if target_root.exists():
                try:
                    remove_save_folder(target_root)
                except Exception:
                    LOGGER.exception("Could not clean incomplete duplicated slot %s", target_root)
            self.set_save_manager_status(f"Copy failed: {type(exc).__name__}: {exc}")
            self.refresh_game_menu()
            return
        self.set_save_manager_status(f"Duplicated {source_name} as {requested} in {target_group}. The original remains active.")
        self.refresh_game_menu()

    def refresh_game_menu(self):
        if not hasattr(self, "save_slot_list"):
            return
        playable = [promo.name for promo in sorted(self.promotions, key=lambda promo: promo.name)
                    if promo.name != "Spectator" and not getattr(promo, "is_regional_feeder", False)
                    and "independent" not in promo.name.lower()]
        choices = ["Create New Promotion...", "Spectator Mode"] + list(dict.fromkeys([self.player_company_name] + playable))
        self.start_company_combo.configure(values=choices)
        if self.start_company_choice.get() not in choices:
            self.start_company_choice.set(self.player_company_name)
        current_save = self.save_slot_list.curselection()
        prior_save_identity = getattr(self, "_save_selected_identity", None)
        if current_save and current_save[0] < len(getattr(self, "save_slot_files", [])):
            prior_save_identity = self.save_entry_identity(self.save_slot_files[current_save[0]])
        current_db = self.database_list.curselection()
        prior_database_identity = getattr(self, "_database_selected_identity", None)
        if current_db and current_db[0] < len(getattr(self, "database_files", [])):
            prior_database_identity = self.database_entry_identity(self.database_files[current_db[0]])
        groups = self.save_group_names()
        if hasattr(self, "save_folder_filter_box"):
            self.save_folder_filter_box.configure(values=("All Saves",) + tuple(groups))
        if hasattr(self, "save_folder_target_box"):
            self.save_folder_target_box.configure(values=tuple(groups))
        if hasattr(self, "save_folder_filter") and self.save_folder_filter.get() not in ("All Saves",) + tuple(groups):
            self.save_folder_filter.set("All Saves")
        if hasattr(self, "save_folder_target") and self.save_folder_target.get() not in groups:
            self.save_folder_target.set(getattr(self, "active_save_group", "Main") if getattr(self, "active_save_group", "Main") in groups else "Main")
        visible_group = self.save_folder_filter.get() if hasattr(self, "save_folder_filter") else "All Saves"
        self.save_slot_list.delete(0, "end")
        self.save_slot_files = []
        self._save_slot_view_keys = []
        metadata_cache = getattr(self, "_save_metadata_cache", {})
        live_cache_keys = set()
        self.save_slot_sources = {}
        self.save_slot_groups = {}
        primary_paths = self.primary_save_paths(create=False)
        entries = []
        for file in primary_paths:
            group = self.save_slot_group_from_path(file)
            if visible_group != "All Saves" and group != visible_group:
                continue
            display_name = self.save_slot_name_from_path(file) if file.name == "savegame.json" else file.stem
            entries.append((file, display_name, "", group))
        for primary in primary_paths:
            slot_dir = primary.parent
            group = self.save_slot_group_from_path(primary)
            if visible_group != "All Saves" and group != visible_group:
                continue
            for snapshot in sorted((slot_dir / "Snapshots").glob("*.json.gz")) if (slot_dir / "Snapshots").exists() else []:
                entries.append((snapshot, snapshot.stem.replace(".json", ""), "Spectator Snapshot", group))
        for file, display_name, kind, group in entries:
            group_prefix = f"[{group}] " if visible_group == "All Saves" else ""
            label = group_prefix + (f"{display_name} | {kind}" if kind else display_name)
            metadata_available = False
            try:
                cache_key = str(file.resolve())
                signature = self.save_metadata_file_signature(file)
                live_cache_keys.add(cache_key)
                cached = metadata_cache.get(cache_key)
                if cached and cached[0] == signature:
                    meta = cached[1]
                else:
                    meta = self.read_save_metadata_fast(file)
                    signature = self.save_metadata_file_signature(file)
                    metadata_cache[cache_key] = (signature, meta)
                if meta:
                    metadata_available = True
                    company = meta.get("company", "Unknown")
                    month = meta.get("month", "?")
                    week = meta.get("week", "?")
                    saved_at = str(meta.get("saved_at", ""))[:16].replace("T", " ")
                    universe = meta.get("active_universe", "")
                    universe_note = f" | {universe}" if universe else ""
                    prefix = group_prefix + (f"{display_name} | {kind} | " if kind else f"{display_name} | ")
                    label = f"{prefix}{company} | {self.format_game_date(month, week)} | {saved_at}{universe_note}"
            except Exception:
                pass
            if not metadata_available:
                label = f"{label} | details unavailable"
            self.save_slot_files.append(file)
            self._save_slot_view_keys.append(self.save_entry_identity(file))
            self.save_slot_sources[file] = self.save_slot_name_from_path(file)
            self.save_slot_groups[file] = group
            self.save_slot_list.insert("end", label)
        self._save_metadata_cache = {key: value for key, value in metadata_cache.items() if key in live_cache_keys}
        if hasattr(self, "save_library_status"):
            self.save_library_status.set(f"{len(primary_paths)} careers  |  {len(entries)} shown")
        if hasattr(self, "save_library_empty_hint"):
            if not entries:
                hint = (
                    "No saved careers yet. Use Save New / Overwrite to create a slot, "
                    "or choose Import Quick in the database panel."
                    if not primary_paths else
                    "No entries match this folder filter. Choose All Saves or another folder to browse the library."
                )
                self.save_library_empty_hint.set(hint)
            else:
                self.save_library_empty_hint.set("")
        if hasattr(self, "save_active_title"):
            self.save_active_title.set(f"ACTIVE  |  {getattr(self, 'active_save_name', 'Unsaved Session')}")
        if hasattr(self, "save_active_detail"):
            active_group = getattr(self, "active_save_group", "Main")
            active_company = "Spectator Mode" if getattr(self, "spectator_mode", False) else getattr(self, "player_company_name", "Unknown company")
            self.save_active_detail.set(f"{active_company}  |  {active_group}  |  {self.format_game_date(self.month, self.week)}")
        self.database_list.delete(0, "end")
        self.database_files = []
        self._database_view_keys = []
        # Game & Saves is a library reader.  Do not create the active-universe
        # marker or normalise the default database merely to repaint the list;
        # explicit database selection/new-game paths own that write boundary.
        try:
            default_database = DATABASE_DIR / "Default Universe.universe.json"
        except Exception:
            default_database = DATABASE_DIR / "Default Universe.universe.json"
        active_database_name = default_database.name
        marker_path = DATA_DIR / "active_universe.txt"
        try:
            marker_name = marker_path.read_text(encoding="utf-8").strip()
            if marker_name and (DATABASE_DIR / marker_name).exists():
                active_database_name = marker_name
        except (OSError, UnicodeError):
            pass
        for file in sorted(DATABASE_DIR.glob("*.universe.json")):
            self.database_files.append(file)
            self._database_view_keys.append(self.database_entry_identity(file))
            active = " *ACTIVE*" if file.name == active_database_name else ""
            self.database_list.insert("end", f"[Universe] {file.stem.replace('.universe', '')}{active}")
        for file in sorted(path for path in DATABASE_DIR.glob("*.json")
                           if not path.name.endswith(".universe.json")
                           and not path.name.endswith(".conversion.json")):
            self.database_files.append(file)
            self._database_view_keys.append(self.database_entry_identity(file))
            kind = "Career Start" if file.with_name(f"{file.stem}.conversion.json").exists() else "Legacy/Section"
            self.database_list.insert("end", f"[{kind}] {file.stem}")
        if prior_save_identity and self.save_slot_list.size():
            restored = self.save_entry_index(self._save_slot_view_keys, prior_save_identity)
            if restored is not None:
                self.save_slot_list.selection_set(restored)
                if hasattr(self.save_slot_list, "activate"):
                    self.save_slot_list.activate(restored)
            else:
                # A filtered-out entry may return later, so keep its identity;
                # an entry that no longer exists must not be selected if the
                # same display name is later reused for a different save.
                try:
                    surviving_keys = {
                        self.save_entry_identity(item)
                        for item in self.primary_save_paths(create=False)
                    }
                    for primary in self.primary_save_paths(create=False):
                        snapshot_dir = primary.parent / "Snapshots"
                        if snapshot_dir.exists():
                            surviving_keys.update(self.save_entry_identity(item) for item in snapshot_dir.glob("*.json.gz"))
                except Exception:
                    surviving_keys = set()
                if prior_save_identity not in surviving_keys:
                    self._save_selected_identity = None
        self.refresh_save_selection_summary()
        if prior_database_identity and self.database_list.size():
            restored_database = self.save_entry_index(self._database_view_keys, prior_database_identity)
            if restored_database is not None:
                self.database_list.selection_set(restored_database)
                if hasattr(self.database_list, "activate"):
                    self.database_list.activate(restored_database)
                self._database_selected_identity = prior_database_identity
        if hasattr(self, "autosave_status_label"):
            raw_rules = getattr(self, "rules", {})
            rules = raw_rules if isinstance(raw_rules, dict) else {}
            status = "ON" if rules.get("autosave_enabled", True) else "OFF"
            weekly_count = len([item for pattern in ("*.json", "*.json.gz") for item in self.autosave_dir("weekly", create=False).glob(pattern) if not item.name.endswith(".manifest.json")]) if hasattr(self, "autosave_dir") else 0
            monthly_count = len([item for pattern in ("*.json", "*.json.gz") for item in self.autosave_dir("monthly", create=False).glob(pattern) if not item.name.endswith(".manifest.json")]) if hasattr(self, "autosave_dir") else 0
            backup_count = len(self.rolling_backup_files(create=False)) if hasattr(self, "rolling_backup_files") else 0
            interval = rules.get("autosave_interval_months", 2)
            legacy = f" | Weekly {weekly_count}/2" if weekly_count else ""
            self.autosave_status_label.config(
                text=f"Auto {status} | Every {interval} months | Monthly {monthly_count}/2{legacy} | Backups {backup_count}/2"
            )
        if hasattr(self, "refresh_spectator_pause_policy_ui"):
            self.refresh_spectator_pause_policy_ui()

    def player_company_as_promotion(self):
        self.ensure_player_media_state()
        self.ensure_foundation_ids()
        show_history = list(self.result_history[:12])
        if not show_history and self.event_log:
            show_history = list(self.event_log[:12])
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop, player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history)
        promotion = Promotion(
            self.player_company_name,
            self.player_region,
            self.company_pop,
            self.cash,
            self.roster,
            promotion_id=str(self.ensure_foundation_state().get("player_promotion_id", "") or ""),
            reputation=self.player_reputation,
            reputation_score=self.company_pop,
            stability=self.company_stability,
            show_history=show_history,
            event_counter=max(1, len(self.result_history) + len(self.scheduled_events) + 1),
            belts=self.normalize_belts(self.belts),
            interim_belts=self.normalize_belts(self.interim_belts),
            special_belts=self.normalize_special_belts(getattr(self, "special_belts", {})),
            belt_history=self.normalize_belt_history(self.belt_history),
            rules=dict(self.rules),
            broadcasters=[dict(item) for item in self.broadcasters],
            weight_classes=list(self.weight_classes),
            scheduled_events=list(self.scheduled_events),
            finance=json.loads(json.dumps(self.finance)),
            staff=[dict(item) for item in self.staff],
            scouting=list(self.scouting),
            inbox=[dict(item) for item in self.inbox],
            owner_goals=[dict(item) for item in self.owner_goals],
            post_show_bonuses=dict(self.post_show_bonuses),
            show_personality=getattr(self, "company_show_personality", "Balanced"),
            strategy=self.seed_promotion_strategy(self.player_company_name, getattr(self, "company_show_personality", "Balanced")),
            executive=self.seed_promotion_executive(self.player_company_name),
            era_history=[],
            academy=json.loads(json.dumps(self.repair_academy(getattr(self, "academy", {})))) if hasattr(self, "repair_academy") else {},
            closed_divisions=sorted(getattr(self, "closed_divisions", set())),
            closed_division_policy_set=True,
        )
        if hasattr(self, "apply_authored_promotion_overrides"):
            # The active player company may be a custom start or a company
            # taken over mid-career. Its live identity and roster always win;
            # database defaults only supply the secondary company systems.
            authored = dict(getattr(self, "_player_database_company_spec", {}) or {})
            for key in (
                "name", "region", "size", "cash", "roster", "reputation", "reputation_score", "stability",
                "show_history", "event_counter", "belts", "interim_belts", "special_belts", "belt_history",
                "scheduled_events", "finance", "staff", "scouting", "inbox", "owner_goals", "academy",
                "closed_divisions", "closed_division_policy_set",
            ):
                authored.pop(key, None)
            self.apply_authored_promotion_overrides(promotion, authored)
        return promotion

    def enter_spectator_mode(self):
        """Turn the currently controlled promotion over to the AI and observe the full world."""
        if getattr(self, "spectator_mode", False):
            return
        former_company = self.player_company_as_promotion()
        # A human-controlled regional company can live on a lean cash reserve;
        # an unattended AI company needs enough runway to actually stage cards.
        # The existing player company begins with a regional operating budget,
        # but the AI requires a full-card reserve before it will book. Give the
        # handoff company a one-time operating runway rather than bypassing the
        # same affordability checks used by every other promotion.
        prior_ai_cash = former_company.cash
        former_company.cash = max(former_company.cash, 2_000_000)
        if former_company.cash != prior_ai_cash and hasattr(self, "record_promotion_finance_transaction"):
            self.record_promotion_finance_transaction(
                former_company, "Spectator-mode operating runway", revenue=former_company.cash - prior_ai_cash,
                category="Rescue", source="Spectator handoff", counterparty=former_company.name,
                reference=f"spectator-runway:{former_company.name}:{self.month}",
            )
        former_company.show_personality = getattr(self, "company_show_personality", "Prospect Builder")
        former_company.strategy = self.seed_promotion_strategy(former_company.name, former_company.show_personality)
        former_company.executive = self.seed_promotion_executive(former_company.name)
        if not any(promo.name == former_company.name for promo in self.promotions):
            self.promotions.append(former_company)
        self.spectator_mode = True
        self.rules["scouting_mode"] = False
        self.player_company_name = "Spectator"
        self.player_region = "Worldwide"
        self.player_reputation = "World Observer"
        self.cash = 0
        self.company_pop = 0
        self.company_stability = 100
        self.roster = []
        self.scheduled_events = []
        self.grand_prix_series = []
        self.pending_rebookings = []
        self.booked = []
        self.result_history = []
        self.event_log = []
        self.news.insert(0, f"Spectator mode started. {former_company.name} is now AI-managed and the full MMA world will progress on its own.")
        if hasattr(self, "event_name"):
            self.event_name.set("Spectator Mode")
        self.refresh_all()
        self.write_log()

    def return_to_spectator_mode(self, confirm=True):
        """Resign from the current promotion and resume observing the world."""
        if getattr(self, "spectator_mode", False):
            self._company_takeover_notice("You are already observing the world simulation.", warning=False)
            return False
        company_name = self.player_company_name
        if confirm and not messagebox.askyesno(
            "Return to Spectator",
            f"Step away from {company_name}? The promotion will return to AI management, including its roster, contracts, scheduled cards, and finances. You can take control of another company later.",
        ):
            return False
        self.enter_spectator_mode()
        self.news.insert(0, f"Promoter move: you stepped away from {company_name} and returned to spectator mode.")
        self.record_world_story(
            "Promoter Move",
            f"The promoter stepped away from {company_name}.",
            f"{company_name} returns to AI management while the world continues under spectator observation.",
            [company_name],
            importance=2,
        )
        self.refresh_all()
        return True

    def exit_spectator_mode(self):
        self.spectator_mode = False

    def take_control_selected_company(self):
        name, sport = self.company_selected_identity()
        if not name:
            self._company_takeover_notice("Select a company first.")
            return
        if sport != "MMA":
            self._company_takeover_notice("Direct takeovers currently apply to MMA promotions. Open this circuit's history or manage your own child promotion instead.")
            return
        promo = next((item for item in self.promotions if item.name == name), None)
        if promo is not None and getattr(promo, "is_child_promotion", False):
            self._company_takeover_notice("Child promotions are managed from the parent company's child-promotion manager and cannot be taken over directly.")
            return
        if promo is not None and getattr(promo, "is_regional_feeder", False):
            self._company_takeover_notice("Regional feeder circuits are development pipelines, not controllable promotions.")
            return
        self.take_control_of_company(name)

    def _company_takeover_notice(self, message, warning=True):
        """Keep takeover guidance beside the selected company when possible."""
        handler = getattr(self, "_company_status_notice", None)
        if callable(handler):
            handler(message, warning=warning)
            return
        (messagebox.showwarning if warning else messagebox.showinfo)("Company", str(message))

    def take_control_of_company(self, company_name, keep_current=True):
        if company_name == self.player_company_name:
            self._company_takeover_notice(f"You already control {company_name}.", warning=False)
            return
        promo = next((item for item in self.promotions if item.name == company_name), None)
        if not promo:
            self._company_takeover_notice("That company is not available to control.")
            return
        if getattr(promo, "is_child_promotion", False):
            self._company_takeover_notice("Child promotions are managed by the parent company and cannot be taken over through the ordinary company takeover flow.")
            return False
        self.promotions.remove(promo)
        was_spectator = getattr(self, "spectator_mode", False)
        if keep_current and not was_spectator:
            self.promotions.append(self.player_company_as_promotion())
        self.exit_spectator_mode()
        self.player_company_name = promo.name
        self.player_region = promo.region
        self.player_reputation = promo.reputation
        self.cash = promo.cash
        self.company_pop = promo.reputation_score
        self.company_stability = promo.stability
        self.roster = self.reconcile_taken_over_roster(promo)
        self.academy = self.repair_academy(promo.academy or self.academy_defaults()) if hasattr(self, "repair_academy") else (promo.academy or {})
        self.closed_divisions = set(getattr(promo, "closed_divisions", None) or [])
        self.player_managed_divisions = set()
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(
            self.roster, promo.belts or {}, promo.name, promo.region, promo.reputation_score,
            player_owned=True, interim_belts=promo.interim_belts or {}, belt_history=promo.belt_history or {},
            closed_divisions=self.closed_divisions,
        )
        self.special_belts = self.normalize_special_belts(getattr(promo, "special_belts", {}) or {})
        self.rules = promo.rules or {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "active_fighter_target": 1200}
        self.ensure_rule_defaults()
        self.broadcasters = promo.broadcasters or [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}]
        self.weight_classes = promo.weight_classes or list(WEIGHTS)
        self.scheduled_events = promo.scheduled_events or []
        self.finance = promo.finance or self.seed_finance()
        self.ensure_finance_defaults()
        self.ensure_player_media_state()
        self.staff = promo.staff or self.seed_staff()
        self.staff_candidates = self.seed_staff_candidates()
        if hasattr(self, "ensure_staff_management_state"):
            # A takeover is a new player/company context.  Do not leak the
            # previous owner's autonomy policy into the acquired promotion.
            self.staff_management = self._default_staff_management_state()
            self.ensure_staff_management_state()
        if hasattr(self, "_default_drug_testing_state"):
            # A takeover starts a fresh player-owned compliance ledger; old
            # promotion records remain in the source promotion's saved data.
            self.drug_testing_state = self._default_drug_testing_state()
            self.ensure_drug_testing_state()
        if hasattr(self, "_default_booking_workbench_state"):
            self.booking_workbench = self._default_booking_workbench_state()
            self.ensure_booking_workbench_state()
        if hasattr(self, "_default_contract_batch_state"):
            self.contract_batch_workbench = self._default_contract_batch_state()
            self.ensure_contract_batch_state()
        self.scouting = promo.scouting or []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self.scouting_watchlists = []
        self.scouting_decision_packs = []
        self.scouting_history = []
        self.scouting_knowledge = {}
        self.scouting_alert_state = {}
        self.scouting_quarantined_reports = []
        self._scouting_state_migrated = True
        self.inbox = promo.inbox or []
        self.owner_goals = promo.owner_goals or self.seed_owner_goals()
        self.post_show_bonuses = promo.post_show_bonuses or {"fight": 5000, "ko": 5000, "sub": 5000}
        self.result_history = promo.show_history or []
        self.booked = []
        self.set_player_event_location_default()
        self.event_name.set(self.default_event_name())
        self.news.insert(0, f"You are now controlling {self.player_company_name}.")
        self.refresh_all()
        self.write_log()

    def reconcile_taken_over_roster(self, promo):
        """Renew stale AI contracts before an AI roster becomes player-owned."""
        roster = list(getattr(promo, "roster", []) or [])
        if not roster:
            return roster
        renewed = []
        for fighter in roster:
            if int(getattr(fighter, "contract_months", 0) or 0) > 0:
                continue
            # Imported/legacy AI rosters can have zero-month deals even though
            # the fighters are still part of the promotion's active plan.
            # A takeover is a change of ownership, not a mass release.
            fighter.contract_months = random.randint(12, 24)
            fighter.exclusive = True
            fighter.contract_type = "Exclusive"
            fighter.ai_offer_company = ""
            fighter.ai_offer_purse = 0
            fighter.ai_offer_months = 0
            fighter.ai_offer_signing_bonus = 0
            fighter.ai_offer_deadline_month = 0
            renewed.append(fighter)
        if renewed:
            names = ", ".join(fighter.name for fighter in renewed[:8])
            suffix = " and more" if len(renewed) > 8 else ""
            self.news.insert(0, f"Takeover contract reset: {len(renewed)} inherited AI deal(s) renewed for the player company ({names}{suffix}).")
        return roster

    def safe_filename(self, value):
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in value).strip()
        return cleaned or "Game"

    def selected_database_path(self):
        selected = self.database_list.curselection() if hasattr(self, "database_list") else []
        files = getattr(self, "database_files", [])
        if selected and selected[0] < len(files):
            return files[selected[0]]
        name = self.safe_filename(self.database_name.get() if hasattr(self, "database_name") else "Default Universe")
        path = DATABASE_DIR / f"{name}.universe.json"
        return path if path.exists() else DATABASE_DIR / f"{name}.json"

    def use_selected_universe_database(self):
        path = self.selected_database_path()
        if not path.name.endswith(".universe.json"):
            notice = "Select a [Universe] database pack first."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Universe Database", notice)
            return
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        notice = f"Universe selected: new games will now use {path.name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Universe Selected", notice)

    def clone_selected_universe_database(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        source = self.selected_database_path()
        if not source.exists() or not source.name.endswith(".universe.json"):
            source = self.ensure_default_universe_database()
        name = self.safe_filename(self.database_name.get() if hasattr(self, "database_name") else "")
        if not name or name in ("Default Database", "Default Universe"):
            name = f"{source.stem.replace('.universe', '')} Copy"
        target = DATABASE_DIR / f"{name}.universe.json"
        counter = 2
        while target.exists():
            target = DATABASE_DIR / f"{name} {counter}.universe.json"
            counter += 1
        data = json.loads(source.read_text(encoding="utf-8"))
        data["database_name"] = target.stem.replace(".universe", "")
        data["cloned_from"] = source.name
        data["cloned_at"] = datetime.now().isoformat(timespec="seconds")
        atomic_write_json(target, data)
        self.active_universe_marker().write_text(target.name, encoding="utf-8")
        self.refresh_game_menu()
        notice = f"Created and selected universe {target.name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Universe Cloned", notice)

    def reset_default_universe_database(self):
        if not messagebox.askyesno("Validate Default Universe", "Normalize the one-file Default Universe database and select it for new games?\n\nYour cloned custom universes will not be changed."):
            return
        path = self.universe_database_path("Default Universe")
        pack = self.load_universe_database_pack(path)
        atomic_write_json(path, pack)
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        notice = f"Default universe normalized and selected: {path.name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Default Universe Ready", notice)

    def open_database_folder(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(DATABASE_DIR)
        except Exception:
            notice = f"Database folder: {DATABASE_DIR}"
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Database Folder", str(DATABASE_DIR))

    def active_universe_pack_with_path(self):
        path = self.active_universe_database_path()
        return path, self.load_universe_database_pack(path)

    def backup_universe_pack(self, path):
        backup = path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(path, backup)
        return backup

    def open_universe_section_editor(self):
        section = self.universe_section_choice.get() if hasattr(self, "universe_section_choice") else "fighters"
        path, pack = self.active_universe_pack_with_path()
        sections = pack.setdefault("sections", {})
        value = sections.get(section, {})
        window = self.create_managed_window()
        window.title(f"Universe Section Editor - {section}")
        window.geometry("980x720")
        window.minsize(780, 520)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"EDIT UNIVERSE SECTION: {section.upper()}", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text=f"Active pack: {path.name}. Save creates a backup first. This edits the database pack used by new games, not the current save.", style="Inset.TLabel").pack(fill="x", padx=10, pady=(0, 8))
        section_status = tk.StringVar(value="")
        ttk.Label(window, textvariable=section_status, style="Inset.TLabel", anchor="w", justify="left", wraplength=940).pack(fill="x", padx=10, pady=(0, 6))
        frame = ttk.Frame(window, style="Panel.TFrame")
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        text = tk.Text(frame, wrap="none", font=("Consolas", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text.insert("end", json.dumps(value, indent=2))
        buttons = ttk.Frame(window, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        def save_section():
            try:
                edited = json.loads(text.get("1.0", "end").strip() or "{}")
            except Exception as exc:
                messagebox.showerror("Invalid JSON", f"Section was not saved.\n\n{type(exc).__name__}: {exc}")
                return
            issues = self.validate_universe_section(section, edited)
            if issues:
                messagebox.showwarning("Section Not Saved", "Fix these validation issues first:\n\n" + "\n".join(issues[:40]))
                return
            current_path, current_pack = self.active_universe_pack_with_path()
            self.backup_universe_pack(current_path)
            current_pack.setdefault("sections", {})[section] = edited
            current_pack["last_edited_at"] = datetime.now().isoformat(timespec="seconds")
            current_pack["last_edited_section"] = section
            atomic_write_json(current_path, current_pack)
            section_status.set(f"Saved {section} in {current_path.name}. A backup was created before the write.")
            self.refresh_game_menu()

        def validate_section():
            try:
                edited = json.loads(text.get("1.0", "end").strip() or "{}")
            except Exception as exc:
                messagebox.showerror("Invalid JSON", f"{type(exc).__name__}: {exc}")
                return
            issues = self.validate_universe_section(section, edited)
            if issues:
                section_status.set("Validation needs attention: " + " | ".join(issues[:8]))
            else:
                section_status.set(f"{section} section looks valid. No changes were written.")

        ttk.Button(buttons, text="Validate Section", command=validate_section).pack(side="left")
        ttk.Button(buttons, text="Save Section", style="Accent.TButton", command=save_section).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

    def validate_universe_section(self, section, value):
        """Validate editable universe JSON through the shared, non-mutating schema."""
        company_names = []
        if section != "companies":
            try:
                pack = self.load_universe_database_pack()
                companies = pack.get("sections", {}).get("companies", {})
                company_names = [row.get("name") for row in companies.get("promotions", []) if isinstance(row, dict)]
                player = companies.get("player_company", {})
                if isinstance(player, dict) and player.get("name"):
                    company_names.append(player["name"])
            except (OSError, ValueError, RuntimeError, TypeError) as exc:
                LOGGER.warning("Universe validation could not read company references: %s", exc)
        return shared_validate_universe_section(section, value, company_names=company_names)

    def _legacy_validate_universe_section(self, section, value):
        issues = []
        if section == "fighters":
            if not isinstance(value, dict):
                return ["fighters section must be an object."]
            for key in ("player_roster", "free_agents", "promotions"):
                if key not in value:
                    issues.append(f"Missing fighters.{key}")
            names = []
            for row in value.get("player_roster", []) + value.get("free_agents", []):
                if isinstance(row, list) and row:
                    names.append(row[0])
                elif isinstance(row, dict):
                    names.append(row.get("name", ""))
            for rows in value.get("promotions", {}).values():
                for row in rows:
                    if isinstance(row, list) and row:
                        names.append(row[0])
                    elif isinstance(row, dict):
                        names.append(row.get("name", ""))
            duplicates = [name for name, count in Counter(names).items() if name and count > 1]
            if duplicates:
                issues.append("Duplicate named fighters: " + ", ".join(duplicates[:12]))
        elif section == "combat_sports":
            if not isinstance(value, dict):
                return ["combat_sports section must be an object."]
            rosters = value.get("rosters", value)
            prime_divisions = value.get("prime_divisions", {})
            profiles = value.get("profiles", {})
            if not isinstance(rosters, dict):
                return ["combat_sports.rosters must be an object."]
            if not isinstance(prime_divisions, dict):
                issues.append("combat_sports.prime_divisions must be an object.")
                prime_divisions = {}
            if not isinstance(profiles, dict):
                issues.append("combat_sports.profiles must be an object.")
                profiles = {}
            all_skill_keys = {key for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
            for sport in ("Boxing", "Kickboxing", "Muay Thai", "Lethwei", "Wrestling", "Brazilian Jiu-Jitsu"):
                if sport not in rosters:
                    issues.append(f"Missing combat sport roster: {sport}")
                    continue
                names = rosters.get(sport, [])
                if not isinstance(names, list):
                    issues.append(f"{sport} roster must be a list.")
                    continue
                if len(names) < 12:
                    issues.append(f"{sport} roster is thin ({len(names)})")
                duplicates = [name for name, count in Counter(names).items() if name and count > 1]
                if duplicates:
                    issues.append(f"Duplicate {sport} athletes: " + ", ".join(duplicates[:10]))
                valid = {label for gender_ladder in COMBAT_SPORT_WEIGHT_CLASSES.get(sport, {}).values() for label, _limit in gender_ladder}
                for name, division in prime_divisions.get(sport, {}).items():
                    if division not in valid:
                        issues.append(f"Invalid {sport} division for {name}: {division}")
                sport_profiles = profiles.get(sport, {})
                if not isinstance(sport_profiles, dict):
                    issues.append(f"profiles.{sport} must be an object keyed by athlete name.")
                    continue
                missing = [name for name in names if name not in sport_profiles]
                if missing:
                    issues.append(f"Missing {sport} profiles: " + ", ".join(missing[:10]))
                orphans = [name for name in sport_profiles if name not in names]
                if orphans:
                    issues.append(f"Orphan {sport} profiles: " + ", ".join(orphans[:10]))
                for name in names:
                    profile = sport_profiles.get(name)
                    if not isinstance(profile, dict):
                        continue
                    for field in ("version", "rating", "prime_age", "record_w", "record_l", "record_d"):
                        if not isinstance(profile.get(field), int):
                            issues.append(f"{sport}/{name}: {field} must be an integer.")
                    rating = profile.get("rating", 0)
                    if isinstance(rating, int) and not 1 <= rating <= 99:
                        issues.append(f"{sport}/{name}: rating must be 1-99.")
                    if any(isinstance(profile.get(field), int) and profile[field] < 0 for field in ("record_w", "record_l", "record_d")):
                        issues.append(f"{sport}/{name}: records cannot be negative.")
                    if profile.get("style") not in STYLES:
                        issues.append(f"{sport}/{name}: invalid style {profile.get('style')}.")
                    if profile.get("trait") not in TRAITS:
                        issues.append(f"{sport}/{name}: invalid trait {profile.get('trait')}.")
                    if profile.get("behaviour") not in BEHAVIOURS:
                        issues.append(f"{sport}/{name}: invalid behaviour {profile.get('behaviour')}.")
                    bad_keys = [key for key in (profile.get("skill_mods", {}) or {}) if key not in all_skill_keys]
                    if bad_keys:
                        issues.append(f"{sport}/{name}: unknown skill modifiers " + ", ".join(bad_keys[:8]))
        elif section == "companies":
            if not isinstance(value, dict):
                return ["companies section must be an object."]
            if "player_company" not in value:
                issues.append("Missing companies.player_company")
            if not value.get("promotions"):
                issues.append("No AI promotions defined.")
            for promo in value.get("promotions", []):
                for key in ("name", "region", "size", "cash", "roster_key"):
                    if key not in promo:
                        issues.append(f"Promotion missing {key}: {promo.get('name', '<unnamed>')}")
        elif section == "media":
            if not isinstance(value, dict):
                return ["media section must be an object."]
            if not value.get("player_broadcasters"):
                issues.append("No player broadcasters defined.")
            packages = value.get("rights_packages", [])
            if not packages:
                issues.append("No media rights packages defined.")
            seen_media_ids = set()
            for package in packages:
                if not isinstance(package, dict) or not package.get("name"):
                    issues.append("Media rights package is missing a name.")
                    continue
                media_id = str(package.get("id", package["name"])).strip().lower()
                if media_id in seen_media_ids:
                    issues.append(f"Duplicate media rights id/name: {package['name']}")
                seen_media_ids.add(media_id)
                for key in ("reach", "prestige", "budget", "selectivity", "min_popularity", "min_card_quality", "min_production"):
                    if key in package and not 0 <= int(package[key]) <= 100:
                        issues.append(f"{package['name']}: {key} must be 0-100.")
                if int(package.get("base_fee", package.get("fee", 0))) < 0:
                    issues.append(f"{package['name']}: fee must not be negative.")
        elif section == "regions":
            if not isinstance(value, dict) or not value:
                issues.append("regions section must be a non-empty object.")
        return issues

    def validate_active_universe_database(self):
        path, pack = self.active_universe_pack_with_path()
        sections = pack.get("sections", {})
        issues = []
        for section in ("fighters", "companies", "combat_sports", "media", "regions"):
            issues.extend(f"{section}: {issue}" for issue in self.validate_universe_section(section, sections.get(section, {})))
        if not issues:
            notice = f"{path.name} passed the current validation checks."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Universe Validation", notice)
        else:
            notice = "Universe needs attention: " + " | ".join(issues[:6])
            if not self._save_surface_notice(notice):
                messagebox.showwarning("Universe Validation", "\n".join(issues[:60]))

    def save_selected_slot(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        requested_name = self.save_slot_name.get().strip() if hasattr(self, "save_slot_name") else ""
        if not requested_name:
            notice = "Enter a new save-slot name before saving."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Save name required", notice)
            return
        name = self.safe_filename(requested_name)
        group = self.normalized_save_group(self.save_folder_target.get() if hasattr(self, "save_folder_target") else getattr(self, "active_save_group", "Main"))
        path = self.save_slot_dir(name, group=group) / "savegame.json"
        previous_name = getattr(self, "active_save_name", "Game 1")
        previous_group = getattr(self, "active_save_group", "Main")
        if path.exists() and not messagebox.askyesno(
            "Overwrite Save Slot",
            f"'{name}' already exists in {group}.\n\nOverwrite this save? A recovery backup will be created first.",
        ):
            self.set_save_manager_status(f"Save cancelled. '{name}' was not overwritten.")
            return
        try:
            if path.exists():
                self.backup_save_file(path, "before_slot_save")
            self.set_active_save_location(name, group)
            data = self.serialize_world()
            data["_save_meta"] = self.save_metadata(name)
            atomic_write_split_save(path, data)
            self.write_save_metadata_sidecar(path, data["_save_meta"])
            self.prune_save_backups()
        except Exception as exc:
            self.set_active_save_location(previous_name, previous_group)
            LOGGER.exception("Save slot failed: %s", exc)
            messagebox.showerror("Save failed", f"The slot was not changed.\n\n{type(exc).__name__}: {exc}")
            return
        self.refresh_game_menu()
        saved_as = "Spectator Mode" if getattr(self, "spectator_mode", False) else getattr(self, "player_company_name", PLAYER_PROMOTION_NAME)
        self.set_save_manager_status(f"Saved {name} in {group}. Mode/company: {saved_as}")

    def selected_save_path(self):
        selected = self.save_slot_list.curselection()
        files = getattr(self, "save_slot_files", [])
        if selected and selected[0] < len(files):
            return files[selected[0]]
        name = self.safe_filename(self.save_slot_name.get())
        group = self.normalized_save_group(self.save_folder_target.get() if hasattr(self, "save_folder_target") else getattr(self, "active_save_group", "Main"))
        return self.save_slot_dir(name, group=group) / "savegame.json"

    def migrate_selected_save_archetypes(self):
        """Explicitly normalise renamed career-arc labels in one save slot.

        The selected save is read and transformed off to the side.  A rolling
        recovery snapshot is created before any write, and a healthy/current
        save is not rewritten.  If the selected slot is the active career we
        reload the migrated payload so the visible game and disk stay in sync.
        """
        path = Path(self.selected_save_path())
        if not path.exists():
            notice = "Select an existing save slot first."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Career profile migration", notice)
            return False
        try:
            payload = load_save_payload(path)
            migrated, changes = migrate_serialized_career_archetypes(payload)
        except Exception as exc:
            LOGGER.exception("Career-archetype migration preflight failed for %s", path)
            messagebox.showerror(
                "Migration failed",
                f"The save was not changed.\n\n{type(exc).__name__}: {exc}",
            )
            return False
        if not changes:
            self.set_save_manager_status(f"{path.name} already uses current career profile labels; no write was made.")
            return True
        preview = "\n".join(
            f"• {row['from']!s} → {row['to']!s} ({row['path']})"
            for row in changes[:12]
        )
        if len(changes) > 12:
            preview += f"\n• …and {len(changes) - 12} more fighter profile(s)."
        if not messagebox.askyesno(
            "Migrate career profiles",
            f"Normalise {len(changes)} legacy career profile label(s) in '{path.name}'?\n\n"
            "A recovery backup is created first. Unknown or healthy values remain untouched.\n\n"
            + preview,
        ):
            self.set_save_manager_status("Career-profile migration cancelled; the save was not changed.")
            return False
        try:
            # Refuse to write if the safety snapshot cannot be made.  This is
            # an explicit migration, so preserving the original is mandatory.
            backup = self.backup_save_file(path, "before_career_archetype_migration")
            metadata = dict(migrated.get("_save_meta", {}) or {})
            metadata["career_archetype_migration"] = {
                "version": CAREER_ARCHETYPE_MIGRATION_VERSION,
                "migrated_at": datetime.now().isoformat(timespec="seconds"),
                "changed": len(changes),
                "backup": str(Path(backup).name) if backup else "rolling backup",
            }
            migrated["_save_meta"] = metadata
            atomic_write_split_save(path, migrated)
            self.write_save_metadata_sidecar(path, metadata)
            try:
                active = Path(self.active_save_path()).resolve()
                is_active = active == path.resolve()
            except (OSError, ValueError):
                is_active = False
            if is_active:
                self.apply_world_data(migrated)
            notice = f"Migrated {len(changes)} career profile label(s) in {path.name}; recovery backup retained in Restore."
            self.refresh_game_menu()
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Career profiles migrated", notice)
            return True
        except Exception as exc:
            LOGGER.exception("Career-archetype migration failed for %s", path)
            self.set_save_manager_status(f"Migration failed; the original save was preserved: {type(exc).__name__}.")
            messagebox.showerror(
                "Migration failed",
                f"The original save was preserved.\n\n{type(exc).__name__}: {exc}",
            )
            return False

    def load_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            notice = "Select an existing save slot."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No save", notice)
            return
        busy = self.show_busy_overlay("Loading save slot", "Preparing the selected save...", 8)
        try:
            current_path = self.active_save_path()
            if current_path.exists() and current_path != path:
                self.update_busy_overlay("Creating a recovery snapshot of the current save...", 18)
                try:
                    self.backup_save_file(current_path, "before_slot_load")
                except Exception:
                    LOGGER.exception("Slot load backup failed; continuing with load into target slot: %s", current_path)
            self.update_busy_overlay("Reading save data...", 28)
            data = load_save_payload(path)
            self.update_busy_overlay("Rebuilding fighters, companies, and world history...", 42)
            self.apply_world_data(data)
            self.set_active_save_location(
                getattr(self, "save_slot_sources", {}).get(path, self.save_slot_name_from_path(path)),
                getattr(self, "save_slot_groups", {}).get(path, self.save_slot_group_from_path(path)),
            )
        except Exception as exc:
            LOGGER.exception("Save slot failed to load: %s", exc)
            self.close_busy_overlay(busy)
            busy = None
            messagebox.showerror("Load failed", f"That slot was left untouched.\n\n{type(exc).__name__}: {exc}")
            return
        try:
            self.booked.clear()
            self.update_busy_overlay("Refreshing the promoter dashboard...", 82)
            self.refresh_all()
            self.update_busy_overlay("Finishing load...", 96)
            self.write_log()
            self.set_save_manager_status(f"Loaded {self.active_save_name} from {self.active_save_group}.")
            self.update_busy_overlay("Save slot loaded.", 100)
        finally:
            self.close_busy_overlay(busy)

    def delete_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            notice = "Select an existing save slot."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No save", notice)
            return
        slot_name = self.save_slot_name_from_path(path)
        active_path = self.save_slot_dir(create=False) / "savegame.json"
        deleting_active_slot = path == active_path
        if not messagebox.askyesno("Delete Save Slot", f"Delete '{slot_name}'? A recovery copy will be kept."):
            return
        try:
            backup = self.backup_save_file(path, "before_slot_delete")
            # Slot-local Backups are removed with the slot, so retain a copy outside it.
            deleted_dir = SAVE_DIR / "Deleted Saves"
            deleted_dir.mkdir(parents=True, exist_ok=True)
            archive_name = f"{self.safe_filename(slot_name)}_{_crash_stamp()}{''.join(backup.suffixes)}"
            shutil.copy2(backup, deleted_dir / archive_name)
            if path.name == "savegame.json":
                remove_save_folder(self.save_slot_root_from_path(path))
            else:
                _make_path_writable(path)
                path.unlink()
            if deleting_active_slot:
                # Do not silently recreate the slot through the current session's autosave.
                self.set_active_save_name("Unsaved Session")
            self.refresh_game_menu()
            self.set_save_manager_status(f"Deleted {slot_name}. A recovery copy is in Deleted Saves.")
        except Exception as exc:
            LOGGER.exception("Could not delete save slot %s: %s", path, exc)
            messagebox.showerror("Delete failed", f"The save was not fully deleted.\n\n{type(exc).__name__}: {exc}")

    def backup_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            notice = "Select an existing save slot first."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No save", notice)
            return
        backup = self.backup_save_file(path, "manual")
        self.prune_save_backups()
        notice = f"Backup created for {path.name}: {Path(backup).name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Backup Created", f"Backed up {path.name}:\n{backup}")

    def open_saves_folder(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(SAVE_DIR)
        except Exception:
            notice = f"Saves folder: {SAVE_DIR}"
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Saves Folder", str(SAVE_DIR))

    def toggle_autosaves(self):
        if hasattr(self, "ensure_rule_defaults"):
            self.ensure_rule_defaults()
        self.rules["autosave_enabled"] = not self.rules.get("autosave_enabled", True)
        self.refresh_game_menu()

    def change_autosave_keep(self, key, amount):
        # Retained for compatibility with older UI bindings. Retention is fixed
        # to two rotating snapshots to prevent save-folder bloat.
        self.rules[key] = ROLLING_SAVE_SLOT_COUNT
        if key == "autosave_weekly_keep":
            self.prune_rolling_autosaves("weekly")
        elif key == "autosave_monthly_keep":
            self.prune_rolling_autosaves("monthly")
        else:
            self.prune_save_backups()
        self.refresh_game_menu()

    def open_save_backup_manager(self):
        sources = [
            ("Backup", self.save_backup_dir()),
            ("Weekly Autosave", self.autosave_dir("weekly")),
            ("Monthly Autosave", self.autosave_dir("monthly")),
        ]
        backups = []
        for label, folder in sources:
            for item in list(folder.glob("*.json")) + list(folder.glob("*.json.gz")):
                if not item.name.endswith(".manifest.json"):
                    backups.append((label, item))
        backups.sort(key=lambda row: row[1].stat().st_mtime, reverse=True)
        window = self.create_managed_window()
        window.title("Save Backup / Autosave Manager")
        window.geometry("860x520")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="SAVE BACKUP / AUTOSAVE MANAGER", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text="Each category keeps two rolling snapshots. Restore creates a backup of the destination first.", style="Inset.TLabel").pack(fill="x", padx=10, pady=(0, 8))
        body = ttk.Frame(window, style="Chrome.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        backup_list = tk.Listbox(body, font=("Consolas", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        backup_list.pack(side="left", fill="both", expand=True, padx=(0, 8))
        detail = tk.Text(body, width=38, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(side="left", fill="both")
        for label, item in backups:
            backup_list.insert("end", f"[{label}] {item.name} | {datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

        def selected_backup():
            sel = backup_list.curselection()
            return backups[sel[0]][1] if sel else None

        def show_detail(_event=None):
            item = selected_backup()
            detail.config(state="normal")
            detail.delete("1.0", "end")
            if item:
                text = f"File: {item.name}\nFolder: {item.parent}\nSize: {item.stat().st_size:,} bytes\nModified: {datetime.fromtimestamp(item.stat().st_mtime)}\n\n"
                try:
                    metadata = json.loads(read_json_text(item)).get("_save_meta", {})
                    if metadata:
                        text += "Snapshot metadata:\n" + json.dumps(metadata, indent=2)
                except Exception:
                    text += "Snapshot metadata could not be read."
                detail.insert("end", text)
            detail.config(state="disabled")

        def restore_backup():
            item = selected_backup()
            if not item:
                notice = "Select a backup first."
                if not self._save_surface_notice(notice):
                    messagebox.showinfo("Restore Backup", notice)
                return
            target_name = self.safe_filename(self.save_slot_name.get() or item.name.split("_before_")[0].split("_manual_")[0])
            target = self.save_slot_dir(target_name) / "savegame.json"
            if not messagebox.askyesno("Restore Backup", f"Restore this backup to slot '{target_name}'?\n\n{item.name}"):
                return
            try:
                self.restore_backup_file(item, target)
            except Exception as exc:
                LOGGER.exception("Backup restore failed from %s to %s", item, target)
                messagebox.showerror("Restore Backup Failed", f"The destination slot was left untouched.\n\n{type(exc).__name__}: {exc}")
                return
            self.refresh_game_menu()
            notice = f"Backup restored to {target.name}; load it deliberately when ready."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Backup Restored", notice)

        backup_list.bind("<<ListboxSelect>>", show_detail)
        buttons = ttk.Frame(window, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Restore To Slot Name", style="Accent.TButton", command=restore_backup).pack(side="left")
        ttk.Button(buttons, text="Open Saves Folder", command=self.open_saves_folder).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        if backups:
            backup_list.selection_set(0)
            show_detail()

    def open_pinned_checkpoint_manager(self):
        """Inspect and explicitly restore/delete manual checkpoints."""
        window = self.create_managed_window("pinned-checkpoints")
        window.title("Pinned Checkpoints")
        window.geometry("760x460")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="PINNED CHECKPOINTS", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(
            window,
            text="Manual, immutable snapshots kept outside rolling recovery. Restore writes to a chosen save slot; it never changes the active game automatically.",
            style="Inset.TLabel", wraplength=720,
        ).pack(fill="x", padx=10, pady=(0, 8))
        body = ttk.Frame(window, style="Inset.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        listing = tk.Listbox(body, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", exportselection=False, relief="flat")
        listing.pack(side="left", fill="both", expand=True, padx=(0, 8))
        detail = ttk.Label(body, text="Select a checkpoint to inspect its source, size and verification status.", style="Inset.TLabel", justify="left", anchor="nw", wraplength=330)
        detail.pack(side="left", fill="both", expand=True)
        rows = []

        def reload_rows():
            rows[:] = self.pinned_checkpoint_files()
            listing.delete(0, "end")
            for item in rows:
                try:
                    metadata = self.read_save_metadata_fast(item) or {}
                    date = metadata.get("checkpoint_date", "Unknown date")
                    size = f"{item.stat().st_size:,} bytes"
                except OSError:
                    date, size = "Unknown date", "Unknown size"
                listing.insert("end", f"{item.stem.replace('.json', '')} | {date} | {size}")
            if rows:
                listing.selection_set(0)
                show_detail()
            else:
                detail.config(text="No pinned checkpoints yet. Use Pin Active State from Game & Saves after reaching a boundary you want to keep.")

        def selected():
            choice = listing.curselection()
            return rows[choice[0]] if choice and choice[0] < len(rows) else None

        def show_detail(_event=None):
            item = selected()
            if item is None:
                detail.config(text="Select a checkpoint to inspect its source, size and verification status.")
                return
            metadata = self.read_save_metadata_fast(item) or {}
            detail.config(text=(
                f"{item.name}\n\n"
                f"Game date: {metadata.get('checkpoint_date', 'Unknown')}\n"
                f"Source save: {metadata.get('source_save', 'Unknown')}\n"
                f"Source group: {metadata.get('source_group', 'Main')}\n"
                f"Saved at: {str(metadata.get('saved_at', 'Unknown'))[:19].replace('T', ' ')}\n"
                f"Size: {item.stat().st_size:,} bytes\n"
                f"Status: {metadata.get('verification_status', 'Metadata unavailable')}"
            ))

        def restore_selected():
            item = selected()
            if item is None:
                notice = "Select a pinned checkpoint first."
                if not self._save_surface_notice(notice):
                    messagebox.showinfo("Restore checkpoint", notice)
                return
            target_name = self.safe_filename(self.save_slot_name.get() if hasattr(self, "save_slot_name") else "") or self.active_save_name
            target = self.save_slot_dir(target_name) / "savegame.json"
            if not messagebox.askyesno("Restore checkpoint", f"Restore this checkpoint to '{target_name}'? A recovery backup protects an existing destination.\n\n{item.name}"):
                return
            try:
                self.restore_backup_file(item, target)
                self.set_save_manager_status(f"Restored pinned checkpoint to {target_name}; load it deliberately when ready.")
                notice = f"Pinned checkpoint restored to {target_name}; the active game was not switched."
                if not self._save_surface_notice(notice):
                    messagebox.showinfo("Checkpoint restored", notice)
            except Exception as exc:
                LOGGER.exception("Pinned checkpoint restore failed: %s", exc)
                messagebox.showerror("Restore failed", f"The destination was left untouched.\n\n{type(exc).__name__}: {exc}")

        def delete_selected():
            item = selected()
            if item is None:
                notice = "Select a pinned checkpoint first."
                if not self._save_surface_notice(notice):
                    messagebox.showinfo("Delete checkpoint", notice)
                return
            if not messagebox.askyesno("Delete checkpoint", f"Delete '{item.name}'? This cannot be undone."):
                return
            if self.delete_pinned_checkpoint(item):
                reload_rows()

        listing.bind("<<ListboxSelect>>", show_detail)
        buttons = ttk.Frame(window, style="Inset.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Restore To Slot", style="Accent.TButton", command=restore_selected).pack(side="left")
        ttk.Button(buttons, text="Delete Selected", command=delete_selected).pack(side="left", padx=6)
        ttk.Button(buttons, text="Refresh", command=reload_rows).pack(side="left")
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        reload_rows()

    def export_database(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.database_name.get())
        data = self.serialize_world()
        for key in ("cash", "month", "scheduled_events", "event_log", "result_history", "result_records", "ai_event_archive", "player_event_archive", "finance", "inbox"):
            data.pop(key, None)
        data["database_name"] = name
        path = DATABASE_DIR / f"{name}.json"
        atomic_write_json(path, data)
        self.refresh_game_menu()
        notice = f"Database exported: {name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Database Exported", notice)

    def career_conversion_preview(self, name=None):
        """Return a staged new-start package without writing or changing the save."""
        requested = name
        if requested is None and hasattr(self, "database_name"):
            requested = self.database_name.get()
        requested = self.safe_filename(str(requested or "Career Start"))
        source_name = getattr(self, "active_save_name", "")
        if hasattr(self, "active_save_path"):
            try:
                source_name = str(self.active_save_path())
            except Exception:
                pass
        source_data = self.serialize_world()
        package, manifest = build_career_database_package(
            source_data, requested, source_save=source_name,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        return package, manifest

    def _career_conversion_summary(self, manifest, *, limit=14):
        rows = list(manifest.get("excluded_fields", []) or [])
        if not rows:
            return "No history or ongoing work needs to be excluded."
        lines = []
        for row in rows[:limit]:
            kind = str(row.get("kind", "excluded")).title()
            lines.append(f"• {kind}: {row.get('field', 'field')} ({row.get('count', 0)}) — {row.get('reason', '')}")
        if len(rows) > limit:
            lines.append(f"• …and {len(rows) - limit} more entries in the companion manifest.")
        return "\n".join(lines)

    def convert_career_to_database(self):
        """Export the current career as a safe, explicitly reviewed new start."""
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        raw_name = self.database_name.get() if hasattr(self, "database_name") else "Career Start"
        name = self.safe_filename(raw_name)
        target = DATABASE_DIR / f"{name}.json"
        manifest_path = DATABASE_DIR / f"{name}.conversion.json"
        # Conversion never silently overwrites a world database or its
        # provenance. A user can choose a new name, preserving both artifacts.
        if target.exists() or manifest_path.exists():
            messagebox.showwarning(
                "Database already exists",
                f"'{name}' already exists in the database folder. Choose a new destination name; the existing database was not changed.",
            )
            return None
        try:
            package, manifest = self.career_conversion_preview(name)
        except Exception as exc:
            LOGGER.exception("Career conversion preflight failed: %s", exc)
            messagebox.showerror("Conversion preflight failed", f"The career was not written.\n\n{type(exc).__name__}: {exc}")
            return None
        errors = [row for row in manifest.get("issues", []) if row.get("severity") == "error"]
        if errors:
            detail = "\n".join(
                f"• {row.get('entity', 'world')}.{row.get('field', 'field')}: {row.get('evidence', '')}"
                for row in errors[:14]
            )
            if len(errors) > 14:
                detail += f"\n• …and {len(errors) - 14} more structural issue(s)."
            messagebox.showerror(
                "Conversion needs repair",
                "The staged career has structural issues and was not written.\n\n" + detail,
            )
            return None
        exclusions = self._career_conversion_summary(manifest)
        if not messagebox.askyesno(
            "Review career conversion",
            f"Create new-start database '{name}'?\n\n"
            "Preserved: fighter identities, current skills/age, career records, roster ownership and supported contracts.\n"
            "Reset: time, cash, finance and inbox state.\n\n"
            "The following evidence will remain in a companion provenance manifest and will not be playable history:\n"
            f"{exclusions}\n\n"
            "The live career save will not be changed. Accept these exclusions and write both files?",
        ):
            self.set_save_manager_status("Career conversion cancelled; no database files were written.")
            return None
        try:
            # Write the manifest first so a database is never advertised without
            # its exclusion/provenance explanation. If the package write fails,
            # remove the newly-created manifest and leave the destination clean.
            atomic_write_json(manifest_path, manifest)
            atomic_write_json(target, package)
        except Exception as exc:
            LOGGER.exception("Career conversion write failed: %s", exc)
            for path in (target, manifest_path):
                try:
                    if path.exists():
                        path.unlink()
                except OSError:
                    LOGGER.exception("Could not clean failed career conversion artifact: %s", path)
            messagebox.showerror("Conversion failed", f"No playable database was left behind.\n\n{type(exc).__name__}: {exc}")
            return None
        self.refresh_game_menu()
        self.set_save_manager_status(f"Created career-start database '{name}' with a provenance manifest.")
        notice = f"Created career-start database '{name}' with a provenance manifest; the live save remains active and unchanged."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Career database created", notice)
        return target

    def import_quick_save_as_database(self):
        source = self.active_save_path()
        if not source.exists() and SAVE_FILE.exists():
            source = SAVE_FILE
        if not source.exists():
            notice = "No active save exists to import."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No quick save", notice)
            return
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.database_name.get())
        data = load_save_payload(source)
        for key in ("cash", "month", "scheduled_events", "event_log", "result_history", "result_records", "ai_event_archive", "player_event_archive", "finance", "inbox"):
            data.pop(key, None)
        data["database_name"] = name
        atomic_write_json(DATABASE_DIR / f"{name}.json", data)
        self.refresh_game_menu()
        notice = f"Imported quick save as database: {name}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Database Imported", notice)

    def load_selected_database(self):
        path = self.selected_database_path()
        if not path.exists():
            notice = "Select a database to load."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("No database", notice)
            return
        if path.name.endswith(".universe.json"):
            self.active_universe_marker().write_text(path.name, encoding="utf-8")
            self.new_game()
            notice = f"Started a new game from universe pack: {path.stem.replace('.universe', '')}."
            if not self._save_surface_notice(notice):
                messagebox.showinfo("Universe Loaded", notice)
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("cash", 275_000)
        data.setdefault("month", 1)
        data.setdefault("scheduled_events", [])
        data.setdefault("event_log", [])
        data.setdefault("result_history", [])
        data.setdefault("finance", self.seed_finance())
        data.setdefault("inbox", [])
        self.apply_world_data(data)
        self.booked.clear()
        self.refresh_all()
        self.write_log()
        notice = f"Started game from database: {path.stem}."
        if not self._save_surface_notice(notice):
            messagebox.showinfo("Database Loaded", notice)

    def open_create_promotion_mode(self):
        window = self.create_managed_window()
        window.title("Create New Promotion")
        screen_width = max(800, window.winfo_screenwidth())
        screen_height = max(650, window.winfo_screenheight())
        width = min(840, screen_width - 60)
        height = min(690, screen_height - 110)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(min(720, width), min(560, height))
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        window.grab_set()

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="FOUND A NEW PROMOTION", style="ScreenTitle.TLabel").pack(side="left", padx=12, pady=8)

        name_var = tk.StringVar(value="New Fighting Championship")
        region_var = tk.StringVar(value="USA")
        scale_var = tk.StringVar(value="Regional")
        personality_var = tk.StringVar(value="Balanced")
        roster_var = tk.StringVar(value="Viable (8 per division)")
        gender_var = tk.StringVar(value="Men Only")
        roster_style_var = tk.StringVar(value="Balanced")
        manual_draft_var = tk.BooleanVar(value=True)
        theme_var = tk.StringVar(value=getattr(self, "theme_name", "UFC"))

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        identity_tab = ttk.Frame(notebook, style="Inset.TFrame")
        sport_tab = ttk.Frame(notebook, style="Inset.TFrame")
        notebook.add(identity_tab, text="Promotion Identity")
        notebook.add(sport_tab, text="Divisions and Roster")

        identity_fields = (
            ("Promotion Name", name_var, None),
            ("Home Region", region_var, REGIONS),
            ("Starting Scale", scale_var, ("Small Local", "Regional", "National")),
            ("Event Philosophy", personality_var, ("Balanced", "Prospect Builder", "Star Builder", "Frequent Small Cards", "Seasonal", "Super Shows")),
            ("Interface Theme", theme_var, tuple(self.themes.keys())),
        )
        name_entry = None
        for row, (label, variable, values) in enumerate(identity_fields):
            ttk.Label(identity_tab, text=label, style="Inset.TLabel").grid(row=row, column=0, sticky="w", padx=16, pady=12)
            if values:
                widget = ttk.Combobox(identity_tab, textvariable=variable, values=values, state="readonly", width=32)
            else:
                widget = ttk.Entry(identity_tab, textvariable=variable, width=35)
                name_entry = widget
            widget.grid(row=row, column=1, sticky="ew", padx=16, pady=12)
        identity_tab.columnconfigure(1, weight=1)

        ttk.Label(sport_tab, text="Roster Foundation", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))
        ttk.Combobox(sport_tab, textvariable=roster_var, values=("Viable (8 per division)", "Established (10 per division)", "Deep (12 per division)"), state="readonly", width=28).grid(row=0, column=1, sticky="ew", padx=16, pady=(14, 8))
        ttk.Label(sport_tab, text="Divisions", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=16, pady=8)
        ttk.Combobox(sport_tab, textvariable=gender_var, values=("Men Only", "Women Only", "Men and Women"), state="readonly", width=28).grid(row=1, column=1, sticky="ew", padx=16, pady=8)
        ttk.Label(sport_tab, text="Roster Strategy", style="Inset.TLabel").grid(row=2, column=0, sticky="w", padx=16, pady=8)
        ttk.Combobox(sport_tab, textvariable=roster_style_var, values=("Balanced", "Star Led", "Prospect Heavy"), state="readonly", width=28).grid(row=2, column=1, sticky="ew", padx=16, pady=8)
        ttk.Checkbutton(sport_tab, text="Choose the initial roster in a budgeted draft", variable=manual_draft_var).grid(row=3, column=1, sticky="w", padx=16, pady=8)
        ttk.Label(sport_tab, text="Active Weight Classes", style="Inset.TLabel").grid(row=4, column=0, sticky="nw", padx=16, pady=8)
        weight_list = tk.Listbox(sport_tab, selectmode="multiple", exportselection=False, height=len(WEIGHTS), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
        for weight in WEIGHTS:
            weight_list.insert("end", weight)
        for default_weight in ("Featherweight", "Lightweight", "Welterweight"):
            if default_weight in WEIGHTS:
                weight_list.selection_set(WEIGHTS.index(default_weight))
        weight_list.grid(row=4, column=1, sticky="nsew", padx=16, pady=8)
        sport_tab.columnconfigure(1, weight=1)
        sport_tab.rowconfigure(4, weight=1)

        summary_var = tk.StringVar(value="")
        summary = ttk.Label(window, textvariable=summary_var, style="Inset.TLabel", anchor="w")
        summary.pack(fill="x", padx=12, pady=(0, 6))

        scale_data = {
            "Small Local": (22, 800_000, 58, "Local", 100_000, 240_000),
            "Regional": (38, 2_500_000, 64, "Regional", 300_000, 380_000),
            "National": (55, 7_500_000, 70, "National", 800_000, 600_000),
        }

        def update_summary(*_args):
            size, cash, stability, reputation, base_budget, division_budget = scale_data[scale_var.get()]
            count = {"Viable (8 per division)": 8, "Established (10 per division)": 10, "Deep (12 per division)": 12}[roster_var.get()]
            gender_count = 2 if gender_var.get() == "Men and Women" else 1
            weights = max(1, len(weight_list.curselection()))
            divisions = gender_count * weights
            budget = base_budget + divisions * division_budget
            summary_var.set(f"{reputation} | Cash ${cash:,} | Contract budget ${budget:,} | {divisions} divisions | Target roster {count * divisions}")

        for variable in (scale_var, roster_var, gender_var):
            variable.trace_add("write", update_summary)
        weight_list.bind("<<ListboxSelect>>", update_summary)
        update_summary()

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=10, pady=(0, 10))

        def begin_custom_game():
            name = " ".join(name_var.get().split())
            company_section = self.universe_section("companies", {}) if hasattr(self, "universe_section") else {}
            player_spec = (company_section or {}).get("player_company", {})
            seeded_names = {str(player_spec.get("name", PLAYER_PROMOTION_NAME)).lower()}
            for section_name in ("promotions", "regional_feeders"):
                for row in (company_section or {}).get(section_name, []):
                    if isinstance(row, dict) and row.get("name"):
                        seeded_names.add(str(row["name"]).lower())
            existing = seeded_names | {self.player_company_name.lower()} | {promo.name.lower() for promo in self.promotions}
            if len(name) < 3:
                messagebox.showwarning("Create Promotion", "Enter a promotion name of at least three characters.", parent=window)
                return
            if name.lower() in existing or name.lower() in {"spectator", "spectator mode"}:
                messagebox.showwarning("Create Promotion", "That promotion name already exists in this universe.", parent=window)
                return
            selected_weights = [WEIGHTS[index] for index in weight_list.curselection()]
            if not selected_weights:
                messagebox.showwarning("Create Promotion", "Select at least one weight class.", parent=window)
                return
            size, cash, stability, reputation, base_budget, division_budget = scale_data[scale_var.get()]
            genders = ["Male", "Female"] if gender_var.get() == "Men and Women" else (["Male"] if gender_var.get() == "Men Only" else ["Female"])
            recruitment_budget = base_budget + len(genders) * len(selected_weights) * division_budget
            self.pending_custom_promotion_config = {
                "name": name,
                "region": region_var.get(),
                "size": size,
                "cash": cash,
                "stability": stability,
                "reputation": reputation,
                "personality": personality_var.get(),
                "roster_depth": {"Viable (8 per division)": 8, "Established (10 per division)": 10, "Deep (12 per division)": 12}[roster_var.get()],
                "genders": genders,
                "weights": selected_weights,
                "theme": theme_var.get(),
                "roster_style": roster_style_var.get(),
                "manual_draft": manual_draft_var.get(),
                "recruitment_budget": recruitment_budget,
            }
            self.start_company_choice.set("Create New Promotion...")
            window.grab_release()
            window.destroy()
            self.new_game()

        ttk.Button(footer, text="Cancel", command=window.destroy).pack(side="right", padx=4)
        ttk.Button(footer, text="Found Promotion and Start", style="Accent.TButton", command=begin_custom_game).pack(side="right", padx=4)
        window.bind("<Escape>", lambda _event: window.destroy())
        if name_entry is not None:
            name_entry.focus_set()
            name_entry.selection_range(0, "end")

    def custom_roster_commitment_cost(self, fighter):
        """Estimated first-year commitment used only by the opening roster draft."""
        return max(6_000, round((fighter.purse * 2.5 + fighter.popularity * 350) / 500) * 500)

    def build_custom_roster_candidates(self, config):
        candidates = []
        scale_skill = {
            "Local": ((47, 67), (61, 75)),
            "Regional": ((51, 73), (68, 82)),
            "National": ((57, 80), (75, 90)),
        }
        core_range, star_range = scale_skill.get(config["reputation"], ((47, 70), (64, 78)))
        depth = max(8, int(config.get("roster_depth", 8)))
        candidate_count = max(18, depth * 2)
        existing = self.active_fighter_names()
        for weight in config["weights"]:
            for gender in config["genders"]:
                for index in range(candidate_count):
                    if index < 3:
                        min_skill, max_skill = star_range
                        age_override = random.randint(24, 31)
                    elif index >= candidate_count - 6:
                        min_skill, max_skill = core_range[0], min(core_range[1], core_range[0] + 13)
                        age_override = random.randint(18, 23)
                    else:
                        min_skill, max_skill = core_range
                        age_override = None
                    fighter = self.create_generated_fighter(
                        3, max(16, config["size"] // 2), min_skill, max_skill,
                        weight=weight, gender=gender, region=config["region"],
                        age_override=age_override, pre_universe=True,
                    )
                    self.avoid_name_collision(fighter, existing)
                    self.prepare_company_generated_fighter(
                        fighter, config["region"], config["name"], player_owned=True
                    )
                    fighter.purse = max(
                        1_500,
                        min(95_000, round(((fighter.overall - 35) ** 2 * 10 + fighter.popularity * 120) / 250) * 250),
                    )
                    fighter.contract_months = random.randint(10, 24)
                    target = self.gym_by_name(self.suggest_camp_for_fighter(fighter, config["region"]))
                    if target:
                        fighter.camp = target.name
                        fighter.camp_quality = target.quality
                    candidates.append(fighter)
        return candidates

    def auto_select_custom_roster(self, candidates, config):
        target = max(8, int(config.get("roster_depth", 8)))
        budget = max(1, int(config.get("recruitment_budget", 1_000_000)))
        style = config.get("roster_style", "Balanced")
        division_groups = []
        for weight in config["weights"]:
            for gender in config["genders"]:
                division = [fighter for fighter in candidates if fighter.weight == weight and fighter.gender == gender]
                if style == "Star Led":
                    score = lambda fighter: fighter.overall * 2.0 + fighter.popularity * 0.9 + fighter.star_quality * 0.7
                elif style == "Prospect Heavy":
                    score = lambda fighter: fighter.potential * 1.7 + max(0, 27 - fighter.age) * 2.2 + fighter.overall * 0.4
                else:
                    score = lambda fighter: fighter.overall * 1.15 + fighter.potential * 0.7 + fighter.popularity * 0.3 - self.custom_roster_commitment_cost(fighter) / 35_000
                baseline = sorted(division, key=self.custom_roster_commitment_cost)[:target]
                division_groups.append((division, score, baseline))

        # Reserve a complete affordable roster for every division first.  The old
        # sequential picker could spend heavily on the first weight classes and
        # leave the final one with seven fighters despite an adequate total budget.
        selected_groups = [list(baseline) for _division, _score, baseline in division_groups]
        spent = sum(self.custom_roster_commitment_cost(fighter) for group in selected_groups for fighter in group)
        for group_index, (division, score, _baseline) in enumerate(division_groups):
            picks = selected_groups[group_index]
            for candidate in sorted(division, key=score, reverse=True):
                if candidate in picks:
                    continue
                weakest = min(picks, key=score)
                if score(candidate) <= score(weakest):
                    continue
                revised = spent - self.custom_roster_commitment_cost(weakest) + self.custom_roster_commitment_cost(candidate)
                if revised <= budget:
                    picks[picks.index(weakest)] = candidate
                    spent = revised
        return [fighter for group in selected_groups for fighter in group]

    def open_initial_roster_draft(self, candidates, config):
        window = self.create_managed_window()
        window.title(f"Found {config['name']} - Initial Roster Draft")
        screen_width = max(1024, window.winfo_screenwidth())
        screen_height = max(720, window.winfo_screenheight())
        width = min(1280, screen_width - 50)
        height = min(820, screen_height - 80)
        window.geometry(f"{width}x{height}+{max(0, (screen_width-width)//2)}+{max(0, (screen_height-height)//2)}")
        window.minsize(min(960, width), min(650, height))
        window.configure(bg=self.colors["chrome"])
        window.transient(self.root)
        window.grab_set()

        budget = int(config.get("recruitment_budget", 1_000_000))
        target = max(8, int(config.get("roster_depth", 8)))
        selected_ids = {fighter.fighter_id for fighter in self.auto_select_custom_roster(candidates, config)}
        result = {"roster": None}
        fighter_map = {fighter.fighter_id: fighter for fighter in candidates}

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="BUILD YOUR FIRST ROSTER", style="ScreenTitle.TLabel").pack(side="left", padx=12, pady=8)
        budget_var = tk.StringVar()
        ttk.Label(header, textvariable=budget_var, style="ScreenTitle.TLabel").pack(side="right", padx=12, pady=8)

        controls = ttk.Frame(window, style="Chrome.TFrame")
        controls.pack(fill="x", padx=8, pady=6)
        gender_filter = tk.StringVar(value="All")
        weight_filter = tk.StringVar(value="All")
        search_var = tk.StringVar(value="")
        ttk.Label(controls, text="Search", style="Chrome.TLabel").pack(side="left", padx=(4, 3))
        ttk.Entry(controls, textvariable=search_var, width=22).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Gender", style="Chrome.TLabel").pack(side="left", padx=3)
        ttk.Combobox(controls, textvariable=gender_filter, values=("All",) + tuple(config["genders"]), state="readonly", width=10).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Division", style="Chrome.TLabel").pack(side="left", padx=3)
        ttk.Combobox(controls, textvariable=weight_filter, values=("All",) + tuple(config["weights"]), state="readonly", width=17).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text=f"Minimum 6, target {target} fighters per active division", style="Chrome.TLabel").pack(side="right", padx=8)

        body = ttk.Panedwindow(window, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        available_frame = ttk.Frame(body, style="Inset.TFrame")
        selected_frame = ttk.Frame(body, style="Inset.TFrame")
        body.add(available_frame, weight=3)
        body.add(selected_frame, weight=2)
        ttk.Label(available_frame, text="AVAILABLE FIGHTERS", style="Section.TLabel").pack(fill="x")
        ttk.Label(selected_frame, text="YOUR ROSTER", style="Section.TLabel").pack(fill="x")

        columns = ("name", "g", "division", "age", "ovr", "potential", "pop", "style", "purse", "cost")
        headings = (("name", "Fighter", 145), ("g", "G", 30), ("division", "Division", 90), ("age", "Age", 38),
                    ("ovr", "OVR", 42), ("potential", "POT", 42), ("pop", "Pop", 42), ("style", "Style", 90),
                    ("purse", "Purse", 70), ("cost", "Annual", 80))

        def make_tree(parent):
            frame = ttk.Frame(parent, style="Inset.TFrame")
            frame.pack(fill="both", expand=True)
            tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
            for key, label, column_width in headings:
                tree.heading(key, text=label)
                tree.column(key, width=column_width, anchor="w" if key in ("name", "style") else "center")
            scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            tree.pack(side="left", fill="both", expand=True)
            self.make_tree_sortable(tree)
            return tree

        available_tree = make_tree(available_frame)
        selected_tree = make_tree(selected_frame)
        status_var = tk.StringVar()
        status = ttk.Label(window, textvariable=status_var, style="Inset.TLabel", anchor="w")
        status.pack(fill="x", padx=10, pady=(0, 5))

        def values(fighter):
            return (fighter.name, fighter.gender[0], fighter.weight, fighter.age, fighter.overall,
                    fighter.potential, fighter.popularity, fighter.style, f"${fighter.purse:,}",
                    f"${self.custom_roster_commitment_cost(fighter):,}")

        def current_spend():
            return sum(self.custom_roster_commitment_cost(fighter_map[fighter_id]) for fighter_id in selected_ids)

        def division_counts():
            return Counter((fighter_map[fighter_id].gender, fighter_map[fighter_id].weight) for fighter_id in selected_ids)

        def refresh_draft(*_args):
            available_tree.delete(*available_tree.get_children())
            selected_tree.delete(*selected_tree.get_children())
            query = search_var.get().strip().lower()
            for fighter in candidates:
                if fighter.fighter_id in selected_ids:
                    selected_tree.insert("", "end", iid=fighter.fighter_id, values=values(fighter))
                    continue
                if gender_filter.get() != "All" and fighter.gender != gender_filter.get():
                    continue
                if weight_filter.get() != "All" and fighter.weight != weight_filter.get():
                    continue
                if query and query not in f"{fighter.name} {fighter.style} {fighter.weight}".lower():
                    continue
                available_tree.insert("", "end", iid=fighter.fighter_id, values=values(fighter))
            spent = current_spend()
            counts = division_counts()
            budget_var.set(f"COMMITTED ${spent:,} / ${budget:,}")
            weak = [f"{gender[0]} {weight}: {counts[(gender, weight)]}" for weight in config["weights"] for gender in config["genders"] if counts[(gender, weight)] < 6]
            status_var.set(("Needs depth: " + ", ".join(weak)) if weak else f"All divisions are viable. {len(selected_ids)} fighters selected; target {target} per division.")

        def add_selected(_event=None):
            additions = [fighter_map[row_id] for row_id in available_tree.selection() if row_id in fighter_map]
            projected = current_spend() + sum(self.custom_roster_commitment_cost(fighter) for fighter in additions)
            if projected > budget:
                status_var.set(f"Those contracts would exceed the ${budget:,} annual commitment budget by ${projected-budget:,}.")
                return
            selected_ids.update(fighter.fighter_id for fighter in additions)
            refresh_draft()

        def remove_selected(_event=None):
            selected_ids.difference_update(selected_tree.selection())
            refresh_draft()

        def auto_build():
            selected_ids.clear()
            selected_ids.update(fighter.fighter_id for fighter in self.auto_select_custom_roster(candidates, config))
            refresh_draft()

        def view_selected_profile():
            rows = selected_tree.selection() or available_tree.selection()
            if rows and rows[0] in fighter_map:
                self.open_fighter_profile_window(fighter_map[rows[0]])

        def finish_draft():
            counts = division_counts()
            weak = [(gender, weight) for weight in config["weights"] for gender in config["genders"] if counts[(gender, weight)] < 6]
            if weak:
                status_var.set("Cannot start: every active division needs at least 6 fighters.")
                return
            if current_spend() > budget:
                status_var.set("Cannot start: roster exceeds the annual contract commitment budget.")
                return
            result["roster"] = [fighter for fighter in candidates if fighter.fighter_id in selected_ids]
            window.grab_release()
            window.destroy()

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="Add Selected", style="Accent.TButton", command=add_selected).pack(side="left", padx=3)
        ttk.Button(footer, text="Remove Selected", command=remove_selected).pack(side="left", padx=3)
        ttk.Button(footer, text=f"Auto Build: {config.get('roster_style', 'Balanced')}", command=auto_build).pack(side="left", padx=3)
        ttk.Button(footer, text="View Profile", command=view_selected_profile).pack(side="left", padx=3)
        ttk.Button(footer, text="Start Career", style="Accent.TButton", command=finish_draft).pack(side="right", padx=3)
        available_tree.bind("<Double-1>", add_selected)
        selected_tree.bind("<Double-1>", remove_selected)
        for variable in (gender_filter, weight_filter, search_var):
            variable.trace_add("write", refresh_draft)
        window.protocol("WM_DELETE_WINDOW", finish_draft)
        refresh_draft()
        self.root.wait_window(window)
        return result["roster"] or self.auto_select_custom_roster(candidates, config)

    def custom_starting_roster(self, config):
        candidates = self.build_custom_roster_candidates(config)
        target = max(8, int(config.get("roster_depth", 8)))
        minimum_commitment = 0
        for weight in config["weights"]:
            for gender in config["genders"]:
                division_costs = sorted(
                    self.custom_roster_commitment_cost(fighter)
                    for fighter in candidates
                    if fighter.weight == weight and fighter.gender == gender
                )
                minimum_commitment += sum(division_costs[:target])
        config["recruitment_budget"] = max(
            int(config.get("recruitment_budget", 0)),
            ((minimum_commitment + 9_999) // 10_000) * 10_000,
        )
        if config.get("manual_draft", False):
            roster = self.open_initial_roster_draft(candidates, config)
        else:
            roster = self.auto_select_custom_roster(candidates, config)
        self.seed_relationships(roster)
        return roster

    def apply_custom_promotion_start(self, config):
        config = dict(config)
        config["weights"] = [weight for weight in config.get("weights", []) if weight in WEIGHTS] or ["Lightweight"]
        config["genders"] = [gender for gender in config.get("genders", []) if gender in ("Male", "Female")] or ["Male"]
        config["roster_depth"] = max(8, min(12, int(config.get("roster_depth", 8))))
        if "recruitment_budget" not in config:
            base, per_division = {
                "Local": (100_000, 240_000),
                "Regional": (300_000, 380_000),
                "National": (800_000, 600_000),
            }.get(config.get("reputation"), (200_000, 250_000))
            config["recruitment_budget"] = base + len(config["weights"]) * len(config["genders"]) * per_division
        original_company = self.player_company_as_promotion()
        original_company.show_personality = "Prospect Builder"
        original_company.strategy = self.seed_promotion_strategy(original_company.name, original_company.show_personality)
        original_company.executive = self.seed_promotion_executive(original_company.name)
        if not any(promo.name == original_company.name for promo in self.promotions):
            self.promotions.append(original_company)

        self.player_company_name = config["name"]
        self.player_region = config["region"]
        self.player_reputation = config["reputation"]
        self.company_pop = config["size"]
        self.company_stability = config["stability"]
        self.cash = config["cash"]
        self.roster = self.custom_starting_roster(config)
        self.weight_classes = list(config["weights"])
        active_keys = {self.belt_key(gender, weight) for gender in config["genders"] for weight in config["weights"]}
        self.closed_divisions = set(self.blank_belts()) - active_keys
        self.player_managed_divisions = set()
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.special_belts = {}
        self.belt_history = self.blank_belt_history()
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(
            self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop,
            player_owned=True, min_per_division=3, interim_belts=self.interim_belts, belt_history=self.belt_history,
            closed_divisions=self.closed_divisions,
        )
        self.finance = self.seed_finance()
        reach = max(18, min(68, round(self.company_pop * 0.75)))
        self.broadcasters = [{"name": f"{self.player_region} Fight Network", "reach": reach, "fee": max(8_000, self.company_pop * 900), "type": "Regional Streaming" if self.company_pop < 50 else "National TV / Streaming"}]
        self.ensure_player_media_state()
        self.staff = self.seed_staff()
        for index, member in enumerate(self.staff):
            if member.get("role") == "Scout":
                self.staff[index] = self.create_starting_scout(self.player_region, self.player_reputation)
                break
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        if hasattr(self, "ensure_staff_management_state"):
            self.ensure_staff_management_state()
        if hasattr(self, "_default_drug_testing_state"):
            self.drug_testing_state = self._default_drug_testing_state()
            self.ensure_drug_testing_state()
        self.booking_workbench = self._default_booking_workbench_state() if hasattr(self, "_default_booking_workbench_state") else {}
        if hasattr(self, "ensure_booking_workbench_state"):
            self.ensure_booking_workbench_state()
        self.contract_batch_workbench = self._default_contract_batch_state() if hasattr(self, "_default_contract_batch_state") else {}
        if hasattr(self, "ensure_contract_batch_state"):
            self.ensure_contract_batch_state()
        self.scouting = []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self.scouting_watchlists = []
        self.scouting_decision_packs = []
        self.scouting_history = []
        self.scouting_knowledge = {}
        self.scouting_alert_state = {}
        self.scouting_quarantined_reports = []
        self._scouting_state_migrated = True
        self.academy = self.academy_defaults() if hasattr(self, "academy_defaults") else {}
        self.inbox = []
        self.owner_goals = [
            {"goal_id": "owner-goal-cash", "goal": f"Keep cash above ${max(150_000, round(self.cash * 0.25)):,}", "metric": "cash", "target": max(150_000, round(self.cash * 0.25)), "deadline": 12, "status": "Active", "goal_type": "achieve_once", "start_month": 1, "owner_company": self.player_company_name},
            {"goal_id": "owner-goal-popularity", "goal": f"Reach company popularity {min(90, self.company_pop + 12)}", "metric": "popularity", "target": min(90, self.company_pop + 12), "deadline": 18, "status": "Active", "goal_type": "achieve_once", "start_month": 1, "owner_company": self.player_company_name},
            {"goal_id": "owner-goal-shows", "goal": "Run at least 4 shows", "metric": "shows", "target": 4, "deadline": 12, "status": "Active", "goal_type": "achieve_once", "start_month": 1, "owner_company": self.player_company_name},
        ]
        if hasattr(self, "ensure_owner_goal_records"):
            self.ensure_owner_goal_records()
        self.scheduled_events = []
        self.grand_prix_series = []
        self.pending_rebookings = []
        self.booked = []
        self.result_history = []
        self.event_log = []
        self.fanbase = {
            "core_support": max(24, min(55, self.company_pop)),
            "casual_reach": max(12, min(48, self.company_pop - 8)),
            "identity": f"{self.player_region} Independent Fight Community",
            "home_region": self.player_region,
            "event_history": [],
        }
        self.theme_name = config.get("theme", self.theme_name)
        if hasattr(self, "theme_name_var"):
            self.theme_name_var.set(self.theme_name)
            self.configure_style()
            self.retheme_plain_widgets(self.root)
        self.normalize_gym_assignments()
        self.sync_gym_membership()
        self.ensure_all_company_champions()
        self.set_player_event_location_default()
        if hasattr(self, "event_name"):
            self.event_name.set(self.default_event_name())
        self.news.insert(0, f"{self.player_company_name} was founded in {self.player_region} as a {self.player_reputation.lower()} promotion.")
        self.company_show_personality = config["personality"]
        self.record_world_story("Business", f"{self.player_company_name} enters the MMA world", f"A new {self.player_reputation.lower()} promotion has opened in {self.player_region} with {len(self.roster)} contracted fighters.", companies=[self.player_company_name])

    def new_game(self):
        if hasattr(self, "editor_current_dirty"):
            self.editor_current_dirty = False
        choice = self.start_company_choice.get() if hasattr(self, "start_company_choice") else PLAYER_PROMOTION_NAME
        custom_config = None
        if choice == "Create New Promotion...":
            custom_config = getattr(self, "pending_custom_promotion_config", None)
            if not custom_config:
                self.open_create_promotion_mode()
                return
            self.pending_custom_promotion_config = None
        if choice == "Cage Empire":
            choice = PLAYER_PROMOTION_NAME
        company_section = self.universe_section("companies", {}) if hasattr(self, "universe_section") else {}
        player_spec = (company_section or {}).get("player_company", {})
        self._player_database_company_spec = dict(player_spec) if isinstance(player_spec, dict) else {}
        self.player_company_name = player_spec.get("name", PLAYER_PROMOTION_NAME)
        self.spectator_mode = False
        self.player_region = player_spec.get("region", "USA")
        self.player_reputation = player_spec.get("reputation", "Regional Player Company")
        self.company_show_personality = player_spec.get("show_personality", player_spec.get("personality", "Balanced"))
        self.cash = max(500_000, int(player_spec.get("cash", 275_000) or 275_000))
        self.company_pop = player_spec.get("popularity", 38)
        self.company_stability = player_spec.get("stability", 52)
        self.month = 1
        self.week = 1
        self.name_counts = {}
        # A fresh universe must not inherit name reservations from the world
        # currently open. Without this reset, every authored fighter already
        # on an old promotion roster was treated as a duplicate and silently
        # replaced with generated roster filler on the new-game seed pass.
        self.promotions = []
        self.retired_fighters = []
        self._seeding_universe = True
        try:
            self.roster = self.seed_roster()
            self.free_agents = self.seed_free_agents()
            self.promotions = self.seed_promotions()
        finally:
            self._seeding_universe = False
        self.repair_core_promotions()
        self.regions = self.universe_section("regions", None) or self.seed_regions()
        self.gyms = self.seed_gyms()
        self.result_history = []
        self.result_records = []
        self.change_journal = []
        self.ai_event_archive = []
        self.player_event_archive = []
        self.independent_showcase_counter = 1
        self.retired_fighters = []
        self.finance = self.seed_finance()
        if isinstance(player_spec.get("finance"), dict):
            self.finance.update(deepcopy(player_spec["finance"]))
        self.engine_settings = self.seed_engine_settings()
        self.business_settings = self.seed_business_settings()
        if hasattr(self, "engine_vars"):
            for key, var in self.engine_vars.items():
                var.set(self.engine_settings.get(key, 1.0))
        if hasattr(self, "gate_multiplier_var"):
            self.gate_multiplier_var.set(self.business_settings.get("gate_multiplier", 1.0))
        self.staff = self.seed_staff()
        if isinstance(player_spec.get("staff"), list):
            self.staff = deepcopy(player_spec["staff"])
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        if hasattr(self, "ensure_staff_management_state"):
            self.ensure_staff_management_state()
        if hasattr(self, "_default_drug_testing_state"):
            self.drug_testing_state = deepcopy(player_spec.get("drug_testing_state", self._default_drug_testing_state())) if isinstance(player_spec.get("drug_testing_state", {}), dict) else self._default_drug_testing_state()
            self.ensure_drug_testing_state()
        self.booking_workbench = self._default_booking_workbench_state() if hasattr(self, "_default_booking_workbench_state") else {}
        if hasattr(self, "ensure_booking_workbench_state"):
            self.ensure_booking_workbench_state()
        self.contract_batch_workbench = self._default_contract_batch_state() if hasattr(self, "_default_contract_batch_state") else {}
        if hasattr(self, "ensure_contract_batch_state"):
            self.ensure_contract_batch_state()
        self.scouting = deepcopy(player_spec.get("scouting", [])) if isinstance(player_spec.get("scouting"), list) else []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self.scouting_watchlists = []
        self.scouting_decision_packs = []
        self.scouting_history = []
        self.scouting_knowledge = {}
        self.scouting_alert_state = {}
        self.scouting_quarantined_reports = []
        self._scouting_state_migrated = True
        self.academy = self.academy_defaults() if hasattr(self, "academy_defaults") else {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True}
        if isinstance(player_spec.get("academy"), dict):
            self.academy.update(deepcopy(player_spec["academy"]))
        self.inbox = []
        self.owner_goals = self.seed_owner_goals()
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.special_belts = {}
        self.belt_history = self.blank_belt_history()
        self.closed_divisions = self.bamma_initial_closed_divisions()
        self.player_managed_divisions = set()
        self.rules = {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "allow_mixed_gender": False, "active_fighter_target": 1200, "ai_offer_market_target": 100, "global_result_replay_limit": 2000, "auto_renew_enabled": False, "scouting_mode": True, "ui_matchup_insight_collapsed": True, "fight_night_audio_enabled": True, "fight_night_audio_output": "System default", "fight_night_audio_volume": 55, "autosave_enabled": True, "autosave_interval_months": 2, "autosave_weekly_keep": 2, "autosave_monthly_keep": 2, "save_backup_keep": 2, "save_retention_version": 4, "detailed_skill_balance_version": 1, "academy_upgrade_pricing_version": 2}
        if isinstance(player_spec.get("rules"), dict):
            self.rules.update(deepcopy(player_spec["rules"]))
        media_section = self.universe_section("media", {}) if hasattr(self, "universe_section") else {}
        self.broadcasters = deepcopy(player_spec["broadcasters"]) if isinstance(player_spec.get("broadcasters"), list) else media_section.get("player_broadcasters", self.default_player_media() if hasattr(self, "default_player_media") else [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        self.media_companies = []
        self.media_market_history = []
        self.media_market_last_month = 0
        self.ensure_media_system()
        self.weight_classes = list(player_spec.get("weight_classes", WEIGHTS))
        self.post_show_bonuses = deepcopy(player_spec.get("post_show_bonuses", {"fight": 5000, "ko": 5000, "sub": 5000}))
        self.news = ["A new game has started."]
        self.world_chronicle = []
        self.story_threads = []
        self.story_subscriptions = []
        self.relationship_cases = []
        self._story_thread_index = {}
        self.fanbase = {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}
        self.defunct_promotions = []
        self.booked = []
        self.scheduled_events = []
        self.grand_prix_series = []
        self.event_log = []
        self.clean_numbered_fighter_names()
        self.normalize_gym_assignments()
        self.sync_gym_membership()
        self.ensure_all_company_champions()
        if custom_config:
            self.apply_custom_promotion_start(custom_config)
            self.refresh_all()
            self.write_log()
            return
        if choice == "Spectator Mode":
            self.enter_spectator_mode()
            return
        if choice != self.player_company_name:
            self.take_control_of_company(choice, keep_current=True)
            self.news.insert(0, f"New game started as {self.player_company_name}.")
            return
        self.set_player_event_location_default()
        # Seed the opening free-agent depth and the first media offers here
        # rather than leaving them to the first market or media redraw.
        # Generating either from a redraw made simply looking at a screen
        # mutate the world and consume simulation RNG.
        self.ensure_free_agent_depth()
        if hasattr(self, "generate_media_offers"):
            self.ensure_player_media_state()
            self.generate_media_offers(force=True)
        self.refresh_all()
        self.write_log()
