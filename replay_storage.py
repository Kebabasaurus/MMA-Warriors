"""Lossless on-disk references for commentary duplicated inside one replay."""

import json
import gzip
import hashlib
import weakref
from functools import lru_cache
from pathlib import Path


_LIVE_SOURCES = weakref.WeakSet()


@lru_cache(maxsize=2)
def _read_detail(path, digest):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        text = handle.read()
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
        raise ValueError("Replay detail checksum mismatch; restore the save and its DataBlocks together.")
    detail = json.loads(text)
    if not isinstance(detail, dict):
        raise ValueError("Invalid replay detail object")
    return detail


class ReplaySource:
    def __init__(self, path, digest):
        self.path = Path(path).resolve()
        self.digest = digest
        _LIVE_SOURCES.add(self)

    def lines(self, key, count):
        lines = _read_detail(str(self.path), self.digest).get(key)
        if not isinstance(lines, list) or len(lines) != count or not all(isinstance(line, str) for line in lines):
            raise ValueError("Replay commentary does not match its manifest")
        return lines


class ReplayLines(list):
    """List-compatible deferred text; metadata queries never read commentary.

    Copies used by transactional loading share an immutable source. Mutations
    detach into an ordinary local list so they cannot alter other snapshots.
    """
    def __init__(self, source, key, count):
        super().__init__()
        self.source, self.key, self.line_count = source, key, count

    def _values(self):
        return self.source.lines(self.key, self.line_count) if self.source else list(super().__iter__())

    def __len__(self):
        return self.line_count if self.source else super().__len__()

    def __iter__(self):
        return iter(self._values())

    def __getitem__(self, key):
        return self._values()[key]

    def __eq__(self, other):
        if isinstance(other, ReplayLines) and self.source and other.source:
            if (self.source.path, self.source.digest, self.key, self.line_count) == (other.source.path, other.source.digest, other.key, other.line_count):
                return True
        return self._values() == other

    def __ne__(self, other):
        return not self == other

    def __contains__(self, item):
        return item in self._values()

    def __add__(self, other):
        return self._values() + other

    def __radd__(self, other):
        return other + self._values()

    def __mul__(self, count):
        return self._values() * count

    __rmul__ = __mul__

    def __deepcopy__(self, memo):
        from copy import deepcopy
        result = ReplayLines(self.source, self.key, self.line_count) if self.source else deepcopy(self._values(), memo)
        memo[id(self)] = result
        return result

    def copy(self):
        return self._values().copy()

    def count(self, value):
        return self._values().count(value)

    def index(self, *args):
        return self._values().index(*args)

    def _detach(self):
        if self.source:
            values = self._values()
            super().extend(values)
            self.source = None

    def __setitem__(self, key, value):
        self._detach()
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._detach()
        super().__delitem__(key)

    def append(self, value):
        self._detach()
        super().append(value)

    def extend(self, values):
        self._detach()
        super().extend(values)

    def insert(self, index, value):
        self._detach()
        super().insert(index, value)

    def pop(self, index=-1):
        self._detach()
        return super().pop(index)

    def remove(self, value):
        self._detach()
        super().remove(value)

    def clear(self):
        self.source = None
        super().clear()

    def reverse(self):
        self._detach()
        super().reverse()

    def sort(self, *args, **kwargs):
        self._detach()
        super().sort(*args, **kwargs)

    def __iadd__(self, values):
        self.extend(values)
        return self

    def __imul__(self, count):
        self._detach()
        super().__imul__(count)
        return self


def pinned_replay_roots():
    return {source.path.parent.parent for source in list(_LIVE_SOURCES)}


def defer_replay_rows(rows, block_dir):
    """Resolve safe manifests without decompressing any commentary files."""
    for row in rows:
        manifest = row.pop("_replay_detail_v1", None)
        if manifest is None:
            continue
        if not isinstance(manifest, dict):
            raise ValueError("Invalid replay manifest")
        digest, counts = manifest.get("sha256"), manifest.get("counts")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid replay checksum")
        if not isinstance(counts, dict):
            raise ValueError("Invalid replay counts")
        root = Path(block_dir).resolve()
        path = (root / "replays" / (digest + ".json.gz")).resolve()
        if path.parent != root / "replays" or not path.is_file():
            raise ValueError("Replay file missing or unsafe; keep this save and its DataBlocks together.")
        source = ReplaySource(path, digest)
        for key, count in counts.items():
            if type(count) is not int or count < 0:
                raise ValueError("Invalid replay line count")
            if key == "log":
                row["log"] = ReplayLines(source, key, count)
            elif key.startswith("fight:") and key[6:].isdigit():
                index = int(key[6:])
                fights = row.get("fight_logs", [])
                if index >= len(fights) or not isinstance(fights[index], dict):
                    raise ValueError("Invalid replay bout reference")
                fights[index]["lines"] = ReplayLines(source, key, count)
            else:
                raise ValueError("Unknown replay detail field")
    return rows


def split_replay_rows(rows, block_dir, write_gzip):
    """Write one card at a time, keeping all non-commentary evidence inline."""
    result = []
    for original in rows:
        row = dict(original)
        unpack_replay_log(row)
        detail = {}
        log = row.get("log")
        if isinstance(log, list):
            detail["log"] = list(log)
            row.pop("log")
        fights = row.get("fight_logs")
        if isinstance(fights, list):
            row["fight_logs"] = [dict(bout) for bout in fights]
            for index, bout in enumerate(row["fight_logs"]):
                lines = bout.get("lines")
                if isinstance(lines, list):
                    detail[f"fight:{index}"] = list(lines)
                    bout.pop("lines")
        if detail:
            encoded = json.dumps(detail, separators=(",", ":"))
            digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            destination = Path(block_dir) / "replays" / (digest + ".json.gz")
            if not destination.exists():
                write_gzip(destination, detail, compresslevel=3)
            row["_replay_detail_v1"] = {"sha256": digest, "counts": {key: len(value) for key, value in detail.items()}}
        result.append(row)
    return result


def pack_replay_log(record):
    """Return a serialized copy without mutating the live replay."""
    saved = dict(record)
    log, fights = saved.get("log"), saved.get("fight_logs")
    if isinstance(log, ReplayLines) or any(isinstance(bout.get("lines"), ReplayLines) for bout in fights or [] if isinstance(bout, dict)):
        return saved
    if "_replay_log_v1" in saved or not isinstance(log, list) or not isinstance(fights, list):
        return saved
    if not all(isinstance(line, str) for line in log):
        return saved
    positions = {}
    for bout_index, bout in enumerate(fights):
        if not isinstance(bout, dict) or not isinstance(bout.get("lines"), list):
            continue
        for line_index, line in enumerate(bout["lines"]):
            if isinstance(line, str):
                positions.setdefault(line, (bout_index, line_index))
    tokens = []
    index = 0
    while index < len(log):
        location = positions.get(log[index])
        if location is None:
            tokens.append(log[index])
            index += 1
            continue
        bout_index, start = location
        lines = fights[bout_index]["lines"]
        count = 1
        while index + count < len(log) and start + count < len(lines) and log[index + count] == lines[start + count]:
            count += 1
        tokens.append([bout_index, start, count])
        index += count
    if len(json.dumps(tokens, ensure_ascii=False)) + 32 < len(json.dumps(log, ensure_ascii=False)):
        saved.pop("log")
        saved["_replay_log_v1"] = tokens
    return saved


def unpack_replay_log(record):
    """Decode atomically; malformed references must not silently lose text."""
    if "_replay_log_v1" not in record:
        return
    tokens, fights = record["_replay_log_v1"], record.get("fight_logs")
    if not isinstance(tokens, list) or not isinstance(fights, list):
        raise ValueError("Invalid packed replay log")
    restored = []
    for token in tokens:
        if isinstance(token, str):
            restored.append(token)
            continue
        if not isinstance(token, list) or len(token) != 3 or any(type(value) is not int for value in token):
            raise ValueError("Invalid replay line reference")
        bout_index, start, count = token
        if not 0 <= bout_index < len(fights) or start < 0 or count <= 0:
            raise ValueError("Replay line reference out of bounds")
        bout = fights[bout_index]
        lines = bout.get("lines") if isinstance(bout, dict) else None
        if not isinstance(lines, list) or start + count > len(lines):
            raise ValueError("Replay line reference out of bounds")
        segment = lines[start:start + count]
        if not all(isinstance(line, str) for line in segment):
            raise ValueError("Invalid referenced replay text")
        restored.extend(segment)
    if "log" in record and record["log"] != restored:
        raise ValueError("Conflicting packed replay log")
    record["log"] = restored
    record.pop("_replay_log_v1")
