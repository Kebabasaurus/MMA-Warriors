import json
import gzip
import logging
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
from datetime import datetime
from logging.handlers import RotatingFileHandler
from uuid import uuid4
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion


LOGGER = logging.getLogger("mma_warriors")
_CRASH_APP = None


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
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    temporary.write_bytes(gzip.compress(payload, compresslevel=max(1, min(9, int(compresslevel)))))
    os.replace(temporary, path)


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
            return
        try:
            atomic_write_json_compact(self.save_metadata_sidecar_path(path), metadata)
        except Exception:
            LOGGER.exception("Could not write save metadata sidecar for %s", path)

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
            autosave_path = crash_folder / f"crash_autosave_{_crash_stamp()}.json"
            data["_save_meta"] = self.save_metadata("Crash Recovery")
            atomic_write_json_compact(autosave_path, data)
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
                self.backup_save_file(path, "before_quick_save")
            atomic_write_json_compact(path, data)
            self.write_save_metadata_sidecar(path, data["_save_meta"])
            self.prune_save_backups()
        except Exception as exc:
            LOGGER.exception("Quick save failed: %s", exc)
            messagebox.showerror("Save failed", f"The existing save was left untouched.\n\n{type(exc).__name__}: {exc}")
            return False
        messagebox.showinfo("Saved", f"Quick saved to {path.resolve()}\n\nTwo rolling recovery backups are kept in this game's Backups folder.")
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

    def primary_save_paths(self):
        """Return folder-based saves first, then legacy flat saves for migration."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
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

    def save_backup_dir(self, source_path=None):
        source = Path(source_path) if source_path else self.active_save_path()
        if source.name == "savegame.json":
            path = source.parent / "Backups"
        elif source == SAVE_FILE:
            path = SAVE_DIR / "Backups"
        else:
            path = self.save_slot_dir() / "Backups"
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

    def rolling_backup_files(self):
        folder = self.save_backup_dir()
        files = [folder / f"backup_{index}.json.gz" for index in range(1, ROLLING_SAVE_SLOT_COUNT + 1)]
        return sorted((item for item in files if item.exists()), key=lambda item: item.stat().st_mtime, reverse=True)

    def backup_save_file(self, path, reason="manual"):
        path = Path(path)
        if not path.exists():
            return None
        backup_dir = self.save_backup_dir(path)
        target = self.rolling_snapshot_path(backup_dir, "backup")
        data = json.loads(read_json_text(path))
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

    def prune_save_backups(self, keep=None):
        self.prune_rolling_snapshot_files(self.save_backup_dir(), "backup")

    def autosave_dir(self, kind="weekly"):
        path = self.save_slot_dir() / "Autosaves" / str(kind).capitalize()
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
        archive = {
            (item.get("date", ""), item.get("company", ""), item.get("event_name", "")): item
            for item in list(getattr(self, "ai_event_archive", [])) + list(getattr(self, "player_event_archive", []))
        }
        rows = []
        for record in self.result_records:
            saved = dict(record)
            key = (record.get("date", ""), record.get("company", ""), record.get("event", ""))
            package = archive.get(key)
            if package and record.get("log") == package.get("log") and record.get("fight_logs") == package.get("fight_logs"):
                saved.pop("log", None)
                saved.pop("fight_logs", None)
                saved["_archive_ref"] = {"date": key[0], "company": key[1], "event": key[2]}
            rows.append(saved)
        return rows

    def json_safe_save_value(self, value):
        """Defensively flatten transient model references before writing a save.

        Event builders occasionally keep a featured Fighter reference in a
        runtime-only archive payload. A save must remain portable even if one
        slips into an archive or media metadata structure.
        """
        if isinstance(value, Fighter):
            return asdict(value)
        if isinstance(value, Promotion):
            return asdict(value)
        if isinstance(value, Gym):
            return asdict(value)
        if isinstance(value, dict):
            return {str(key): self.json_safe_save_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.json_safe_save_value(item) for item in value]
        return value

    def relink_archived_result_records(self):
        """Restore de-duplicated save records to the normal full runtime shape."""
        archive = {
            (item.get("date", ""), item.get("company", ""), item.get("event_name", "")): item
            for item in list(getattr(self, "ai_event_archive", [])) + list(getattr(self, "player_event_archive", []))
        }
        for record in self.result_records:
            ref = record.pop("_archive_ref", None)
            if not isinstance(ref, dict):
                continue
            package = archive.get((ref.get("date", ""), ref.get("company", ""), ref.get("event", "")))
            if package:
                record["log"] = package.get("log", [])
                record["fight_logs"] = package.get("fight_logs", [])

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
                    # Conor's old profile was incorrectly calibrated as a
                    # late-career 82 despite this universe starting him at 27.
                    # Only opening-world saves receive this correction; later
                    # development remains part of that save's own history.
                    if fighter.name == "Conor McGregor" and getattr(fighter, "prime_rating_profile_version", 0) < 1:
                        self.apply_real_fighter_profile(fighter, 92)
                        fighter.prime_rating_profile_version = 1
                        fighter.potential = max(fighter.potential, 98)
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
        self.ensure_all_company_champions()
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
            "month": self.month,
            "week": self.week,
            "roster": [asdict(f) for f in self.roster],
            "free_agents": [asdict(f) for f in self.free_agents],
            "promotions": [asdict(p) for p in self.promotions],
            "combat_sport_worlds": {sport: {**world, "roster": [asdict(fighter) for fighter in world.get("roster", [])]} for sport, world in getattr(self, "combat_sport_worlds", {}).items()},
            "player_combat_divisions": getattr(self, "player_combat_divisions", {}),
            "standings_history": getattr(self, "standings_history", {}),
            "regions": self.regions,
            "gyms": [asdict(g) for g in getattr(self, "gyms", [])],
            "result_history": self.result_history,
            "result_records": self.json_safe_save_value(self.serialized_result_records()),
            "change_journal": self.json_safe_save_value(getattr(self, "change_journal", [])),
            "result_index": self.json_safe_save_value(getattr(self, "result_index", [])),
            "ai_event_archive": self.json_safe_save_value(self.ai_event_archive),
            "player_event_archive": self.json_safe_save_value(getattr(self, "player_event_archive", [])),
            "independent_showcase_counter": getattr(self, "independent_showcase_counter", 1),
            "retired_fighters": [asdict(f) for f in self.retired_fighters],
            "finance": self.finance,
            "media_companies": getattr(self, "media_companies", []),
            "media_market_history": getattr(self, "media_market_history", []),
            "media_market_last_month": getattr(self, "media_market_last_month", 0),
            "engine_settings": self.engine_settings,
            "staff": self.staff,
            "staff_candidates": self.staff_candidates,
            "scouting": self.scouting,
            "scouting_reports": getattr(self, "scouting_reports", {}),
            "scouting_searches": getattr(self, "scouting_searches", []),
            "scouting_shortlist": list(getattr(self, "scouting_shortlist", [])),
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
            "pending_rebookings": getattr(self, "pending_rebookings", []),
            "news": self.news,
            "world_chronicle": getattr(self, "world_chronicle", []),
            "defunct_promotions": getattr(self, "defunct_promotions", []),
            "event_log": self.event_log,
            "season_stats": getattr(self, "season_stats", {}),
            "awards_history": getattr(self, "awards_history", []),
            "fight_timer_delay": self.fight_timer_delay.get() if hasattr(self, "fight_timer_delay") else 2150,
        }

    def load_game(self):
        path = self.active_save_path()
        if not path.exists() and SAVE_FILE.exists():
            path = SAVE_FILE
        if not path.exists():
            messagebox.showinfo("No save", "No active save exists yet.")
            return
        try:
            data = json.loads(read_json_text(path))
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
                    self.apply_world_data(json.loads(read_json_text(backup_path)))
                    self.booked.clear()
                    self.ensure_player_event_name()
                    self.refresh_all()
                    self.write_log()
                    messagebox.showwarning("Backup loaded", f"The current quick save could not be read. Recovery snapshot {backup_path.stem} was loaded instead.")
                    LOGGER.warning("Quick save failed to load; restored previous backup: %s", exc)
                    return
                except Exception:
                    LOGGER.exception("Quick-save backup could not be loaded after primary failure")
            LOGGER.exception("Quick save could not be loaded: %s", exc)
            messagebox.showerror(
                "Load failed",
                f"That save could not be loaded and was left untouched.\n\n{type(exc).__name__}: {exc}",
            )
            return
        self.booked.clear()
        self.ensure_player_event_name()
        self.reconcile_title_shot_alerts()
        self.refresh_all()
        self.write_log()

    def apply_world_data(self, data):
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
        if hasattr(self, "theme_name_var"):
            self.theme_name_var.set(self.theme_name)
            self.configure_style()
            self.retheme_plain_widgets(self.root)
        self.cash = data.get("cash", 275_000)
        self.company_pop = data.get("company_pop", 38)
        self.company_stability = data.get("company_stability", max(5, min(99, self.cash // 5000)))
        self.month = max(1, int(data.get("month", 1) or 1))
        self.week = max(1, min(4, int(data.get("week", 1) or 1)))
        self.roster = [Fighter(**row) for row in data.get("roster", [])]
        self.free_agents = [Fighter(**row) for row in data.get("free_agents", [])]
        for fighter in self.roster + self.free_agents:
            fighter.weight = self.game_weight_class(fighter.weight)
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.promotions = []
        self.defunct_promotions = list(data.get("defunct_promotions", []))
        for row in data.get("promotions", []):
            row["roster"] = [Fighter(**fighter) for fighter in row.get("roster", [])]
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
            for fighter in row["roster"]:
                fighter.weight = self.game_weight_class(fighter.weight)
                self.ensure_detailed_skills(fighter)
                self.ensure_fighter_business_stats(fighter)
            self.promotions.append(Promotion(**row))
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
            self.gyms = [Gym(**row) for row in data.get("gyms", [])]
            known_gyms = {gym.name for gym in self.gyms}
            self.gyms.extend(gym for gym in seeded_gyms if gym.name not in known_gyms)
        else:
            self.gyms = seeded_gyms
        self.result_history = data.get("result_history", [])
        self.result_records = data.get("result_records", [])
        self.change_journal = list(data.get("change_journal", []))[-400:]
        self.ai_event_archive = data.get("ai_event_archive", [])
        self.player_event_archive = data.get("player_event_archive", [])[-150:]
        self.relink_archived_result_records()
        self.result_index = data.get("result_index", [])
        self.ensure_result_index()
        serialized_sport_worlds = data.get("combat_sport_worlds")
        self.combat_sport_worlds = serialized_sport_worlds if serialized_sport_worlds else self.seed_combat_sport_worlds()
        for world in self.combat_sport_worlds.values():
            world["roster"] = [fighter if isinstance(fighter, Fighter) else Fighter(**fighter) for fighter in world.get("roster", [])]
        self.player_combat_divisions = data.get("player_combat_divisions", {}) or {}
        self.standings_history = data.get("standings_history", {}) or {}
        self.independent_showcase_counter = max(1, data.get("independent_showcase_counter", 1))
        self.retired_fighters = [Fighter(**row) for row in data.get("retired_fighters", [])]
        for fighter in self.retired_fighters:
            fighter.weight = self.game_weight_class(fighter.weight)
            self.ensure_detailed_skills(fighter)
            self.ensure_fighter_business_stats(fighter)
        self.repair_premature_retirements()
        self.ensure_fighter_ids()
        self.backfill_archived_fight_log_ids()
        self.finance = data.get("finance", self.seed_finance())
        self.media_companies = data.get("media_companies", []) or []
        self.media_market_history = data.get("media_market_history", []) or []
        self.media_market_last_month = data.get("media_market_last_month", 0)
        self.engine_settings = data.get("engine_settings", self.seed_engine_settings())
        if hasattr(self, "engine_vars"):
            for key, var in self.engine_vars.items():
                var.set(self.engine_settings.get(key, 1.0))
        self.ensure_finance_defaults()
        self.staff = data.get("staff", self.seed_staff())
        self.staff_candidates = data.get("staff_candidates", self.seed_staff_candidates())
        self.ensure_staff_profiles()
        self.scouting = data.get("scouting", [])
        self.scouting_reports = data.get("scouting_reports", {})
        self.scouting_searches = data.get("scouting_searches", [])
        self.scouting_shortlist = list(dict.fromkeys(str(key) for key in data.get("scouting_shortlist", []) if key))
        self._scouting_state_migrated = False
        self.migrate_scouting_state()
        self.achievement_log = data.get("achievement_log", [])
        self.company_safety = max(0, min(100, int(data.get("company_safety", 60) or 60)))
        self.company_milestone_progress = data.get("company_milestone_progress", {}) or {}
        self.super_event_offers = data.get("super_event_offers", []) or []
        self.super_event_history = data.get("super_event_history", []) or []
        self.super_event_project = data.get("super_event_project")
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
        self.belts = self.normalize_belts(data.get("belts", self.blank_belts()))
        self.interim_belts = self.normalize_belts(data.get("interim_belts", self.blank_belts()))
        self.special_belts = self.normalize_special_belts(data.get("special_belts", {}))
        self.belt_history = self.normalize_belt_history(data.get("belt_history", self.blank_belt_history()))
        self.closed_divisions = set(data.get("closed_divisions", []))
        self.player_managed_divisions = set(data.get("player_managed_divisions", self.closed_divisions))
        if hasattr(self, "fight_timer_delay"):
            saved_delay = int(data.get("fight_timer_delay", self.fight_timer_delay.get()))
            # 950 ms was the old shipped default. Move old-default saves to the
            # more readable live-fight pace, while respecting deliberate custom speeds.
            if saved_delay == 950:
                saved_delay = 2150
            self.fight_timer_delay.set(max(120, min(3000, saved_delay)))
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
        self.broadcasters = data.get("broadcasters", [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        self.ensure_media_system()
        self.weight_classes = list(dict.fromkeys(
            self.game_weight_class(weight) for weight in data.get("weight_classes", list(WEIGHTS))
            if self.game_weight_class(weight) in WEIGHTS
        )) or list(WEIGHTS)
        self.post_show_bonuses = data.get("post_show_bonuses", {"fight": 5000, "ko": 5000, "sub": 5000})
        self.scheduled_events = data.get("scheduled_events", [])
        # Older builds silently moved cancelled bouts to other cards or created a
        # dedicated Rebooked Bouts show. Player cards now remain entirely manual.
        rebooked_name = f"{self.player_company_name} Rebooked Bouts"
        self.scheduled_events = [event for event in self.scheduled_events if event.get("name") != rebooked_name]
        self.pending_rebookings = data.get("pending_rebookings", [])
        for event in self.scheduled_events:
            event.setdefault("week", 1)
        self.repair_booking_conflicts()
        self.news = data.get("news", [])
        # Chronicle entries are newest-first; retain the newest 800 from older,
        # oversized saves rather than accidentally keeping their oldest stories.
        self.world_chronicle = data.get("world_chronicle", [])[:800]
        self.event_log = data.get("event_log", [])
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
        self.ensure_all_company_champions()
        self.rebalance_ai_finance_model()
        self.maintain_inbox()
        self.set_player_event_location_default()

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
        for key in closed:
            self.belts[key] = ""
            self.interim_belts[key] = ""
        existing_ids = {fighter.fighter_id for fighter in self.free_agents}
        for fighter in released:
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
            for key in closed:
                promo.belts[key] = ""
                promo.interim_belts[key] = ""
            for fighter in released:
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
            promo.roster = [fighter for fighter in promo.roster if fighter not in released]
            released_total += len(released)
        return released_total

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
        for fighter in fighters:
            if id(fighter) in seen or getattr(fighter, "primary_discipline", "MMA") != "MMA":
                continue
            seen.add(id(fighter))
            if getattr(fighter, "realism_profile_version", 0) >= 1:
                continue
            if self.apply_signature_real_fighter_profile(fighter, preserve_career=True):
                updated.append(fighter.name)
        return sorted(set(updated))

    def migrate_real_fighter_profiles(self, fighters):
        """One-time migration for saves made before deterministic real-fighter profiles."""
        real_names = {row[0] for rows in self.expanded_real_fighter_data().values() for row in rows}
        real_names.update(row[0] for row in self.cage_empire_fighter_data())
        real_names.update(row[0] for row in self.independent_fighter_data())
        real_names.update(row[0] for row in self.legend_fighter_data())
        profiles = self.real_fighter_profiles()
        recalibrated = 0
        for fighter in fighters:
            if fighter.name not in real_names or getattr(fighter, "rating_profile_version", 0) >= 3:
                continue
            baseline = profiles.get(fighter.name, {}).get("rating", fighter.overall)
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
            identity = self.real_fighter_identity_data(fighter.name)
            if not identity:
                continue
            if getattr(fighter, "real_identity_version", 0) < 2:
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
            fighter.regional_popularity = {region: max(0, min(100, int(markets.get(region, 0)))) for region in REGIONS}
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
        fighter.career_goal_last_review = max(0, getattr(fighter, "career_goal_last_review", 0) or 0)
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
            copied_data = json.loads(read_json_text(copied_primary))
            copied_data["active_save_name"] = requested
            copied_data["active_save_group"] = target_group
            metadata = dict(copied_data.get("_save_meta", {}) or {})
            metadata.update({"slot_name": requested, "folder": target_group, "saved_at": datetime.now().isoformat(timespec="seconds")})
            copied_data["_save_meta"] = metadata
            atomic_write_json_compact(copied_primary, copied_data)
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
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        playable = [promo.name for promo in sorted(self.promotions, key=lambda promo: promo.name)
                    if promo.name != "Spectator" and not getattr(promo, "is_regional_feeder", False)
                    and "independent" not in promo.name.lower()]
        choices = ["Create New Promotion...", "Spectator Mode"] + list(dict.fromkeys([self.player_company_name] + playable))
        self.start_company_combo.configure(values=choices)
        if self.start_company_choice.get() not in choices:
            self.start_company_choice.set(self.player_company_name)
        current_save = self.save_slot_list.curselection()
        current_db = self.database_list.curselection()
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
        metadata_cache = getattr(self, "_save_metadata_cache", {})
        live_cache_keys = set()
        self.save_slot_sources = {}
        self.save_slot_groups = {}
        primary_paths = self.primary_save_paths()
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
            self.save_slot_files.append(file)
            self.save_slot_sources[file] = self.save_slot_name_from_path(file)
            self.save_slot_groups[file] = group
            self.save_slot_list.insert("end", label)
        self._save_metadata_cache = {key: value for key, value in metadata_cache.items() if key in live_cache_keys}
        self.database_list.delete(0, "end")
        self.database_files = []
        if hasattr(self, "ensure_default_universe_database"):
            self.ensure_default_universe_database()
        try:
            active_database_name = self.active_universe_database_path().name
        except Exception:
            active_database_name = ""
        for file in sorted(DATABASE_DIR.glob("*.universe.json")):
            self.database_files.append(file)
            active = " *ACTIVE*" if file.name == active_database_name else ""
            self.database_list.insert("end", f"[Universe] {file.stem.replace('.universe', '')}{active}")
        for file in sorted(path for path in DATABASE_DIR.glob("*.json") if not path.name.endswith(".universe.json")):
            self.database_files.append(file)
            self.database_list.insert("end", f"[Legacy/Section] {file.stem}")
        if current_save and self.save_slot_list.size():
            self.save_slot_list.selection_set(min(current_save[0], self.save_slot_list.size() - 1))
        if current_db and self.database_list.size():
            self.database_list.selection_set(min(current_db[0], self.database_list.size() - 1))
        if hasattr(self, "autosave_status_label"):
            if hasattr(self, "ensure_rule_defaults"):
                self.ensure_rule_defaults()
            status = "ON" if self.rules.get("autosave_enabled", True) else "OFF"
            weekly_count = len([item for pattern in ("*.json", "*.json.gz") for item in self.autosave_dir("weekly").glob(pattern) if not item.name.endswith(".manifest.json")]) if hasattr(self, "autosave_dir") else 0
            monthly_count = len([item for pattern in ("*.json", "*.json.gz") for item in self.autosave_dir("monthly").glob(pattern) if not item.name.endswith(".manifest.json")]) if hasattr(self, "autosave_dir") else 0
            backup_count = len(self.rolling_backup_files()) if hasattr(self, "rolling_backup_files") else 0
            interval = self.rules.get("autosave_interval_months", 2)
            legacy = f" | Weekly {weekly_count}/2" if weekly_count else ""
            self.autosave_status_label.config(
                text=f"Auto {status} | Every {interval} months | Monthly {monthly_count}/2{legacy} | Backups {backup_count}/2"
            )

    def player_company_as_promotion(self):
        self.ensure_player_media_state()
        show_history = list(self.result_history[:12])
        if not show_history and self.event_log:
            show_history = list(self.event_log[:12])
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop, player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history)
        return Promotion(
            self.player_company_name,
            self.player_region,
            self.company_pop,
            self.cash,
            self.roster,
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
        former_company.cash = max(former_company.cash, 2_000_000)
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
            messagebox.showinfo("Spectator Mode", "You are already observing the world simulation.")
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
            messagebox.showinfo("No company", "Select a company first.")
            return
        if sport != "MMA":
            messagebox.showinfo("Combat-sport circuit", "Direct takeovers currently apply to MMA promotions. Open this circuit's history or manage your own child promotion instead.")
            return
        promo = next((item for item in self.promotions if item.name == name), None)
        if promo is not None and getattr(promo, "is_regional_feeder", False):
            messagebox.showinfo("Regional feeder", "Regional feeder circuits are development pipelines, not controllable promotions.")
            return
        self.take_control_of_company(name)

    def take_control_of_company(self, company_name, keep_current=True):
        if company_name == self.player_company_name:
            messagebox.showinfo("Already active", f"You already control {company_name}.")
            return
        promo = next((item for item in self.promotions if item.name == company_name), None)
        if not promo:
            messagebox.showinfo("Company unavailable", "That company is not available to control.")
            return
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
        self.roster = promo.roster
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
        self.scouting = promo.scouting or []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
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
            messagebox.showinfo("Universe Database", "Select a [Universe] database pack first.")
            return
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        messagebox.showinfo("Universe Selected", f"New games will now use:\n{path.name}")

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
        messagebox.showinfo("Universe Cloned", f"Created and selected:\n{target.name}")

    def reset_default_universe_database(self):
        if not messagebox.askyesno("Reset Default Universe", "Rebuild the default real-life universe database from the game's built-in source data?\n\nYour cloned custom universes will not be changed."):
            return
        path = self.universe_database_path("Default Universe")
        if path.exists():
            backup = path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy2(path, backup)
        atomic_write_json(path, self.build_universe_database_pack("Default Universe"))
        self.active_universe_marker().write_text(path.name, encoding="utf-8")
        self.refresh_game_menu()
        messagebox.showinfo("Default Restored", f"Default universe rebuilt and selected:\n{path.name}")

    def open_database_folder(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(DATABASE_DIR)
        except Exception:
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
        window = tk.Toplevel(self.root)
        window.title(f"Universe Section Editor - {section}")
        window.geometry("980x720")
        window.minsize(780, 520)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text=f"EDIT UNIVERSE SECTION: {section.upper()}", style="ScreenTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text=f"Active pack: {path.name}. Save creates a backup first. This edits the database pack used by new games, not the current save.", style="Inset.TLabel").pack(fill="x", padx=10, pady=(0, 8))
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
            messagebox.showinfo("Section Saved", f"Saved {section} in {current_path.name}.")
            self.refresh_game_menu()

        def validate_section():
            try:
                edited = json.loads(text.get("1.0", "end").strip() or "{}")
            except Exception as exc:
                messagebox.showerror("Invalid JSON", f"{type(exc).__name__}: {exc}")
                return
            issues = self.validate_universe_section(section, edited)
            messagebox.showinfo("Section Validation", "\n".join(issues[:40]) if issues else f"{section} section looks valid.")

        ttk.Button(buttons, text="Validate Section", command=validate_section).pack(side="left")
        ttk.Button(buttons, text="Save Section", style="Accent.TButton", command=save_section).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

    def validate_universe_section(self, section, value):
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
            messagebox.showinfo("Universe Validation", f"{path.name} passed the current validation checks.")
        else:
            messagebox.showwarning("Universe Validation", "\n".join(issues[:60]))

    def save_selected_slot(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        requested_name = self.save_slot_name.get().strip() if hasattr(self, "save_slot_name") else ""
        if not requested_name:
            messagebox.showinfo("Save name required", "Enter a new save-slot name before saving.")
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
            atomic_write_json_compact(path, data)
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

    def load_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            messagebox.showinfo("No save", "Select an existing save slot.")
            return
        try:
            current_path = self.active_save_path()
            if current_path.exists() and current_path != path:
                self.backup_save_file(current_path, "before_slot_load")
            self.apply_world_data(json.loads(read_json_text(path)))
            self.set_active_save_location(
                getattr(self, "save_slot_sources", {}).get(path, self.save_slot_name_from_path(path)),
                getattr(self, "save_slot_groups", {}).get(path, self.save_slot_group_from_path(path)),
            )
        except Exception as exc:
            LOGGER.exception("Save slot failed to load: %s", exc)
            messagebox.showerror("Load failed", f"That slot was left untouched.\n\n{type(exc).__name__}: {exc}")
            return
        self.booked.clear()
        self.refresh_all()
        self.write_log()
        self.set_save_manager_status(f"Loaded {self.active_save_name} from {self.active_save_group}.")

    def delete_selected_slot(self):
        path = self.selected_save_path()
        if not path.exists():
            messagebox.showinfo("No save", "Select an existing save slot.")
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
            messagebox.showinfo("No save", "Select an existing save slot first.")
            return
        backup = self.backup_save_file(path, "manual")
        self.prune_save_backups()
        messagebox.showinfo("Backup Created", f"Backed up {path.name}:\n{backup}")

    def open_saves_folder(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(SAVE_DIR)
        except Exception:
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
        window = tk.Toplevel(self.root)
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
                messagebox.showinfo("Restore Backup", "Select a backup first.")
                return
            target_name = self.safe_filename(self.save_slot_name.get() or item.name.split("_before_")[0].split("_manual_")[0])
            target = self.save_slot_dir(target_name) / "savegame.json"
            if not messagebox.askyesno("Restore Backup", f"Restore this backup to slot '{target_name}'?\n\n{item.name}"):
                return
            if target.exists():
                self.backup_save_file(target, "before_restore")
            atomic_write_text(target, read_json_text(item))
            self.refresh_game_menu()
            messagebox.showinfo("Backup Restored", f"Restored to {target.name}.")

        backup_list.bind("<<ListboxSelect>>", show_detail)
        buttons = ttk.Frame(window, style="Chrome.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(buttons, text="Restore To Slot Name", style="Accent.TButton", command=restore_backup).pack(side="left")
        ttk.Button(buttons, text="Open Saves Folder", command=self.open_saves_folder).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        if backups:
            backup_list.selection_set(0)
            show_detail()

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
        messagebox.showinfo("Database Exported", f"Exported database: {name}")

    def import_quick_save_as_database(self):
        source = self.active_save_path()
        if not source.exists() and SAVE_FILE.exists():
            source = SAVE_FILE
        if not source.exists():
            messagebox.showinfo("No quick save", "No active save exists to import.")
            return
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        name = self.safe_filename(self.database_name.get())
        data = json.loads(read_json_text(source))
        for key in ("cash", "month", "scheduled_events", "event_log", "result_history", "result_records", "ai_event_archive", "player_event_archive", "finance", "inbox"):
            data.pop(key, None)
        data["database_name"] = name
        atomic_write_json(DATABASE_DIR / f"{name}.json", data)
        self.refresh_game_menu()
        messagebox.showinfo("Database Imported", f"Imported quick save as database: {name}")

    def load_selected_database(self):
        path = self.selected_database_path()
        if not path.exists():
            messagebox.showinfo("No database", "Select a database to load.")
            return
        if path.name.endswith(".universe.json"):
            self.active_universe_marker().write_text(path.name, encoding="utf-8")
            self.new_game()
            messagebox.showinfo("Universe Loaded", f"Started a new game from universe pack: {path.stem.replace('.universe', '')}")
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
        messagebox.showinfo("Database Loaded", f"Started game from database: {path.stem}")

    def open_create_promotion_mode(self):
        window = tk.Toplevel(self.root)
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
        window = tk.Toplevel(self.root)
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
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        self.scouting = []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self._scouting_state_migrated = True
        self.academy = self.academy_defaults() if hasattr(self, "academy_defaults") else {}
        self.inbox = []
        self.owner_goals = [
            {"goal": f"Keep cash above ${max(150_000, round(self.cash * 0.25)):,}", "metric": "cash", "target": max(150_000, round(self.cash * 0.25)), "deadline": 12, "status": "Active"},
            {"goal": f"Reach company popularity {min(90, self.company_pop + 12)}", "metric": "popularity", "target": min(90, self.company_pop + 12), "deadline": 18, "status": "Active"},
            {"goal": "Run at least 4 shows", "metric": "shows", "target": 4, "deadline": 12, "status": "Active"},
        ]
        self.scheduled_events = []
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
        self.player_company_name = player_spec.get("name", PLAYER_PROMOTION_NAME)
        self.spectator_mode = False
        self.player_region = player_spec.get("region", "USA")
        self.player_reputation = player_spec.get("reputation", "Regional Player Company")
        self.company_show_personality = "Balanced"
        self.cash = max(500_000, round(player_spec.get("cash", 275_000) * 1.5))
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
        self.engine_settings = self.seed_engine_settings()
        if hasattr(self, "engine_vars"):
            for key, var in self.engine_vars.items():
                var.set(self.engine_settings.get(key, 1.0))
        self.staff = self.seed_staff()
        self.staff_candidates = self.seed_staff_candidates()
        self.ensure_staff_profiles()
        self.scouting = []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self._scouting_state_migrated = True
        self.academy = self.academy_defaults() if hasattr(self, "academy_defaults") else {"owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [], "weekly_cost": 0, "auto_train": True}
        self.inbox = []
        self.owner_goals = self.seed_owner_goals()
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.special_belts = {}
        self.belt_history = self.blank_belt_history()
        self.closed_divisions = self.bamma_initial_closed_divisions()
        self.player_managed_divisions = set()
        self.rules = {"rounds": 3, "title_rounds": 5, "round_length": 5, "drug_testing": "Standard", "judging_randomness": 2, "allow_mixed_gender": False, "active_fighter_target": 1200, "ai_offer_market_target": 100, "global_result_replay_limit": 2000, "auto_renew_enabled": False, "scouting_mode": True, "fight_night_audio_enabled": True, "fight_night_audio_output": "System default", "fight_night_audio_volume": 55, "autosave_enabled": True, "autosave_interval_months": 2, "autosave_weekly_keep": 2, "autosave_monthly_keep": 2, "save_backup_keep": 2, "save_retention_version": 4, "detailed_skill_balance_version": 1, "academy_upgrade_pricing_version": 2}
        media_section = self.universe_section("media", {}) if hasattr(self, "universe_section") else {}
        self.broadcasters = media_section.get("player_broadcasters", self.default_player_media() if hasattr(self, "default_player_media") else [{"name": "Regional Webcast", "reach": 22, "fee": 12000, "type": "Streaming"}])
        self.media_companies = []
        self.media_market_history = []
        self.media_market_last_month = 0
        self.ensure_media_system()
        self.weight_classes = list(WEIGHTS)
        self.post_show_bonuses = {"fight": 5000, "ko": 5000, "sub": 5000}
        self.news = ["A new game has started."]
        self.world_chronicle = []
        self.fanbase = {"core_support": 42, "casual_reach": 30, "identity": "Regional Fight Community", "home_region": self.player_region, "event_history": []}
        self.defunct_promotions = []
        self.booked = []
        self.scheduled_events = []
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
        self.refresh_all()
        self.write_log()
