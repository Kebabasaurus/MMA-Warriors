"""Focused regressions for durable fight identity and transactional persistence."""

from copy import deepcopy
import json
import random
import tempfile
import tkinter as tk
from pathlib import Path
from unittest.mock import patch

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

        # Replay presentation must preserve both durable corners even when the
        # archived commentary contains the same raw name for each fighter.
        same_name_line = f"{a.name} vs {a.name} — {a.name} probes and {a.name} counters."
        same_name_log = {
            "a": a.name, "b": b.name,
            "a_id": a.fighter_id, "b_id": b.fighter_id,
            "weight": a.weight,
        }
        rendered_line = app.display_fighter_names_in_text(same_name_line, same_name_log)
        require(f"{app.fighter_display_name(a)} (Red) vs {app.fighter_display_name(b)} (Blue)" in rendered_line,
                "same-name replay heading collapsed the two durable corner identities")
        require(app.display_fighter_names_in_text(rendered_line, same_name_log) == rendered_line,
                "same-name replay presentation was not idempotent")

        # A result replay carries its archived event report into the live
        # viewer; otherwise the finale reports fake zero profit/excitement and
        # cannot resolve the original location context.
        replay_capture = {}
        original_open_live = app.open_live_fight_window

        def capture_replay(event, replay_package, apply_results=True, on_complete=None):
            replay_capture.update({
                "event": event,
                "package": replay_package,
                "apply_results": apply_results,
                "on_complete": on_complete,
            })

        app.open_live_fight_window = capture_replay
        replay_record = {
            "date": "Month 7 Week 3", "company": app.player_company_name,
            "event": "Identity Replay", "profit": "$45,678",
            "summary": "Identity Replay completed.",
        }
        replay_archive = {
            "date": "Month 7 Week 3", "company": app.player_company_name,
            "event": "Identity Replay",
            "event_name": "Identity Replay",
            "venue": "National Arena", "region": "Europe", "city": "London",
            "month": 7, "week": 3, "day": "Saturday",
            "profit": 45_678, "average_excitement": 73,
            "finance": {"attendance": 8_765}, "fight_count": 1,
            "summary": "Identity Replay completed.",
            "log": ["Identity Replay completed."],
            "fight_logs": [{"heading": "Replay bout", "lines": ["Replay result"]}],
            "tournament_brackets": [{"title": "Replay Grand Prix"}],
        }
        app.player_event_archive.insert(0, replay_archive)
        app.watch_result_card(replay_record)
        app.open_live_fight_window = original_open_live
        require(replay_capture.get("apply_results") is False,
                "archived card replay attempted to apply world results")
        require(all(replay_capture["package"].get(key) == replay_archive[key]
                    for key in ("profit", "average_excitement", "finance", "region", "city", "venue", "fight_count", "tournament_brackets")),
                "archived card replay dropped event report metadata")
        require(all(replay_capture["event"].get(key) == replay_archive[key]
                    for key in ("venue", "region", "city", "month", "week", "day")),
                "archived card replay dropped event location or date context")

        # Clinch ownership uses the same private slots as every other live
        # channel. The existing controller must maintain cage control instead
        # of being treated as an opponent attempting a reversal.
        original_attack = app.action_attack_value
        original_defence = app.action_defence_value
        app.action_attack_value = lambda *_args: 0
        app.action_defence_value = lambda *_args: 0
        fight_state = {
            "fighter_keys": {id(a): "a", id(b): "b"},
            "position": "cage", "top": None, "bottom": None,
            "clinch_controller": "a", "clinch_ticks": 4,
            "unanswered": {"a": 0, "b": 0},
            "stats": {
                "a": {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0},
                "b": {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0},
            },
        }
        round_stats = {
            "a": {"impact": 0, "control": 0, "danger": 0},
            "b": {"impact": 0, "control": 0, "danger": 0},
        }
        # A neutral contest tests ordinary retention. The release engine may
        # legitimately turn an overwhelming win into a standing rear body lock.
        with patch.object(app.fight_mechanics_rng(), "randint", return_value=0):
            app.resolve_exchange(a, b, "cage_control", fight_state, round_stats)
        require(fight_state["clinch_controller"] == "a" and fight_state["clinch_ticks"] == 5,
                "existing cage controller was misclassified as the trapped fighter")
        require(fight_state["position"] == "cage" and round_stats["a"]["control"] == 3,
                "ordinary cage retention lost its position or earned control")
        app.action_attack_value = lambda *_args: 100
        with patch.object(app.fight_mechanics_rng(), "randint", return_value=0):
            app.resolve_exchange(a, b, "cage_control", fight_state, round_stats)
        require(fight_state["position"] == "standing back control"
                and fight_state["clinch_controller"] == "a" and fight_state["clinch_ticks"] == 0
                and round_stats["a"]["control"] == 6,
                "successful rear-body-lock transition lost the same-name fighter's private slot")

        # A miss is not unanswered offense, while a meaningful takedown answers
        # an earlier striking sequence even if the responder never throws back.
        miss_state = {
            "fighter_keys": {id(a): "a", id(b): "b"},
            "position": "range", "top": None, "bottom": None,
            "clinch_controller": None, "unanswered": {"a": 0, "b": 0},
            "knockdowns": {"a": 0, "b": 0},
            "damage": {"a": 0, "b": 0}, "body": {"a": 0, "b": 0},
            "stats": {
                "a": {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0},
                "b": {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0},
            },
        }
        app.action_attack_value = lambda *_args: 0
        app.action_defence_value = lambda *_args: 100
        app.resolve_exchange(a, b, "jab", miss_state, round_stats)
        require(miss_state["unanswered"]["b"] == 0,
                "missed strike incorrectly increased unanswered offense")
        miss_state["unanswered"]["a"] = 5
        app.action_attack_value = lambda *_args: 100
        app.action_defence_value = lambda *_args: 0
        app.resolve_exchange(a, b, "shoot", miss_state, round_stats)
        require(miss_state["unanswered"]["a"] == 0,
                "successful takedown did not answer the prior striking sequence")
        app.action_attack_value = original_attack
        app.action_defence_value = original_defence

        # Legacy friend names are only safe when unique in the owning roster.
        friend_duplicate = app.roster[2]
        friend_duplicate_original_name = friend_duplicate.name
        a.friend = b.name
        friend_duplicate.name = b.name
        require(app.resolve_friend_target(a) is None,
                "ambiguous friend name resolved to an arbitrary same-name fighter")
        friend_duplicate.name = friend_duplicate_original_name
        require(app.resolve_friend_target(a) is b,
                "unique legacy friend name did not resolve to the intended fighter")

        # Tournament simulation must resolve the aligned IDs and restore each
        # same-name entrant's own pre-view fatigue value.
        a.fatigue, b.fatigue = 11, 37
        original_simulate_fight = app.simulate_fight
        app.simulate_fight = lambda first, second, _fight: (first, second, "Decision", 3, [])
        tournament = {
            "fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id],
            "tournament": True, "tournament_entrants": [a.name, b.name],
            "tournament_name": "Identity Probe Grand Prix", "title": False,
            "divisional_title": False, "interim": False, "special_belt": "",
            "main": True, "tier": "Main Card",
        }
        tournament_event = {
            "name": "Identity Probe", "venue": "Regional Arena",
            "region": app.player_region, "city": "London",
        }
        app.simulate_event_tournament(tournament_event, tournament)
        app.simulate_fight = original_simulate_fight
        require((a.fatigue, b.fatigue) == (11, 37),
                "same-name tournament entrants shared one fatigue snapshot")

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
