"""Immutable ordered lookup tables, built once instead of scanning per exchange."""
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, init=False)
class MoveIndex:
    _by_key: object
    _unrestricted: object
    _by_action: object
    _by_style: object
    _by_tag: object

    def __init__(self, definitions):
        definitions = tuple(definitions)
        targets = {"", "head", "body", "leg"}
        targets.update(target for move in definitions for target in move.targets)
        by_key, unrestricted, by_action, by_style, by_tag = {}, {}, {}, {}, {}
        for move in definitions:
            if getattr(move, "deprecated", False):
                continue
            by_action.setdefault(move.parent_action, []).append(move)
            for style in move.preferred_styles:
                by_style.setdefault(style, []).append(move)
            for tag in move.tags:
                by_tag.setdefault(tag, set()).add(move.move_id)
            for position in move.positions:
                if not move.targets:
                    unrestricted.setdefault((move.parent_action, position), []).append(move)
                for target in targets:
                    if not move.targets or target in move.targets:
                        by_key.setdefault((move.parent_action, position, target), []).append(move)
        for field, values in (("_by_key", by_key), ("_unrestricted", unrestricted),
                              ("_by_action", by_action), ("_by_style", by_style)):
            object.__setattr__(self, field, MappingProxyType({key: tuple(rows) for key, rows in values.items()}))
        object.__setattr__(self, "_by_tag", MappingProxyType({key: frozenset(ids) for key, ids in by_tag.items()}))

    def legal_moves(self, parent_action, position, target=""):
        key = (parent_action, position, target or "")
        result = self._by_key.get(key)
        if result is not None:
            return result
        # Legacy callers may supply an unknown target: untargeted moves remain legal.
        return self._unrestricted.get((parent_action, position), ())

    def by_action(self, action):
        return self._by_action.get(action, ())

    def by_style(self, style):
        return self._by_style.get(style, ())

    def by_tag(self, tag):
        return self._by_tag.get(tag, frozenset())
