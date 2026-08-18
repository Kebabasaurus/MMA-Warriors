"""Focused regressions for durable fight identity and transactional persistence."""

from copy import deepcopy
import json
import random
import tempfile
import tkinter as tk
from pathlib import Path

from main import FightEmpireApp
from persistence import load_save_payload


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_raises(exception_type, action, message):
    try:
        action()
    except exception_type:
        return
    raise AssertionError(message)


def main():
    random.seed(60117)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root)
        app.new_game()

        # Two real fighters can share a display name. Live fight bookkeeping,
        # scorecards, and stats must remain separate by durable identity.
        a, b = app.roster[:2]
        b.name = a.name
        winner, loser, _method, _round, _lines = app.simulate_fight(
            a, b,
            {"fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id]},
        )
        require(winner in (a, b) and loser in (a, b) and winner is not loser,
                "same-name fight did not retain distinct winner and loser objects")
        require(a.last_fight_stats is not None and b.last_fight_stats is not None,
                "same-name fight did not retain both stat lines")
        require(a.last_fight_stats is not b.last_fight_stats,
                "same-name fight reused one fighter stat dictionary")
        require(app.resolve_fighter(a.fighter_id) is a,
                "fighter ID did not resolve before display-name fallback")
        require(app.resolve_fighter(a.name) is None,
                "ambiguous display-name lookup selected an arbitrary fighter")

        # An exception after an event starts mutating state must roll the whole
        # player card back, including the early cash/finance mutations.
        before_cash = app.cash
        before_finance = deepcopy(app.finance)
        original_media = app.record_media_event_outcome

        def fail_media(*_args, **_kwargs):
            raise RuntimeError("injected media failure")

        app.record_media_event_outcome = fail_media
        package = {
            "profit": 12_345,
            "projected_pop": app.company_pop + 1,
            "projected_stability": app.company_stability + 1,
            "finance": {"total_revenue": 0, "total_expense": 0},
            "event_name": "Injected Rollback",
            "results": [],
            "media_outcome": {"reach": 1},
        }
        require_raises(RuntimeError, lambda: app.finish_event(None, package),
                       "injected finish-event failure was swallowed")
        app.record_media_event_outcome = original_media
        require(app.cash == before_cash and app.finance == before_finance,
                "failed event commit left cash or finance mutations behind")

        # Future fields should not crash a current executable; malformed rows
        # should fail transactionally without touching the live career.
        saved = app.serialize_world()
        forward = deepcopy(saved)
        forward["roster"][0]["future_only_field"] = "ignored by this build"
        app.apply_world_data(forward)
        before_name = app.roster[0].name
        malformed = deepcopy(forward)
        malformed["roster"][0] = []
        require_raises(ValueError, lambda: app.apply_world_data(malformed),
                       "malformed roster row did not report a validation error")
        require(app.roster[0].name == before_name,
                "malformed transactional load altered the live career")

        # Sidecar paths must stay inside the owning save's generated block dir.
        with tempfile.TemporaryDirectory() as temp_dir:
            save = Path(temp_dir) / "savegame.json"
            save.write_text(json.dumps({"_external_blocks": {"event_log": "../outside.json.gz"}}), encoding="utf-8")
            require_raises(ValueError, lambda: load_save_payload(save),
                           "external block traversal path was accepted")

        print("Identity and persistence regression tests passed")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
