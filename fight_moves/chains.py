"""Immutable acyclic follow-up graph; depths count possible successor edges."""
from collections import deque
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, init=False)
class MoveChainGraph:
    adjacency: object
    depths: object
    roots: tuple
    max_depth: int

    def __init__(self, definitions):
        definitions = tuple(definitions)
        edges = {m.move_id: tuple(m.follow_ups) for m in definitions}
        if len(edges) != len(definitions):
            raise ValueError("Chain graph requires unique move IDs")
        missing = sorted({target for targets in edges.values() for target in targets} - edges.keys())
        if missing:
            raise ValueError("Unresolved chain targets: " + ", ".join(missing))
        incoming = dict.fromkeys(edges, 0)
        for targets in edges.values():
            for target in targets:
                incoming[target] += 1
        roots = tuple(key for key, count in incoming.items() if count == 0)
        queue = deque(roots)
        ordered = []
        while queue:
            key = queue.popleft()
            ordered.append(key)
            for target in edges[key]:
                incoming[target] -= 1
                if incoming[target] == 0:
                    queue.append(target)
        if len(ordered) != len(edges):
            # Residual nodes include a cycle and anything downstream from it.
            residual = sorted(key for key, count in incoming.items() if count)
            raise ValueError("Chain cycle prevents ordering: " + ", ".join(residual))
        depths = {}
        for key in reversed(ordered):
            depths[key] = max((1 + depths[target] for target in edges[key]), default=0)
        object.__setattr__(self, "adjacency", MappingProxyType(edges))
        object.__setattr__(self, "depths", MappingProxyType(depths))
        object.__setattr__(self, "roots", roots)
        object.__setattr__(self, "max_depth", max(depths.values(), default=0))

    def chain_depth(self, move_id):
        """Maximum remaining graph depth, not a claimed completed fight sequence."""
        return self.depths[move_id]

    def report(self):
        return {"moves": len(self.adjacency), "edges": sum(map(len, self.adjacency.values())),
                "roots": list(self.roots), "unresolved_targets": [], "max_chain_depth": self.max_depth}


def validate_chain_graph(definitions):
    try:
        MoveChainGraph(definitions)
    except ValueError as error:
        return [str(error)]
    return []


def sequence_actor_role(position, actor, top, bottom):
    if position not in {"guard", "half guard", "side control", "mount", "back control",
                        "turtle", "front headlock", "leg entanglement"}:
        return ""
    return "top" if actor == top else "bottom" if actor == bottom else ""


def sequence_role_allows(action, position, actor, top, bottom):
    """Reject a same-position successor belonging to the opposite controller."""
    role = sequence_actor_role(position, actor, top, bottom)
    if role == "top":
        return action not in {"bottom_submission", "sweep", "recover_guard", "stand_up", "cling",
                              "turtle_escape", "front_headlock_escape", "leg_escape", "counter_leg_lock"}
    if role == "bottom":
        return action not in {"submission", "ground_strikes", "ground_control", "advance_position",
                              "take_back", "turtle_ride", "front_headlock_submission",
                              "leg_attack", "leg_control", "disengage_leg"}
    return True
