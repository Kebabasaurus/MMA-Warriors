"""Bounded UI work and streaming persistence regression checks."""
import gzip
import inspect
import random
import textwrap
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from views import ViewMixin
from persistence import atomic_write_json_gzip, PersistenceMixin
import seeding
from seeding import SeedMixin
from persistence_regression_test import fighter
from fight_moves.release_registry import RELEASE_MOVE_REGISTRY
from world import WorldMixin


class PerformanceTests(unittest.TestCase):
    def test_ai_card_cache_preserves_legality_and_is_local(self):
        host = SimpleNamespace(
            month=12, promotion_strategy=lambda promo: {"current_mode": "Balanced"},
            promotion_division_open=lambda promo, gender, weight: gender == "Male" and weight == "Lightweight",
            belt_key=lambda gender, weight: gender + weight,
            ai_title_contender_pressure=lambda *args: 0,
            ai_primary_title_holder_name=lambda *args: "",
            ai_story_matchup_value=lambda *args: (0, ""),
            ai_matchup_is_stale=lambda *args, **kwargs: False,
            ai_matchmaking_rank_gap_limit=lambda *args: 999,
            matchup_history_penalty=lambda *args: 0,
            rivalry_heat_between=lambda *args: 0,
            fighter_needs_matchmaking_rebuild=Mock(return_value=False),
        )
        promo = SimpleNamespace(name="Test FC", belts={}, belt_history={}, size=50)
        ready = [fighter(name=f"Candidate {i}", fighter_id=f"card-{i}", age=30) for i in range(24)]
        for f in ready:
            f.rival = ""
            f.last_fight_month = 11
        ready[-1].last_fight_month = 0
        card = WorldMixin.build_ai_card(host, promo, ready, 8)
        self.assertEqual(len(card), 2)
        participants = [f.fighter_id for row in card for f in (row["a"], row["b"])]
        self.assertEqual(len(participants), len(set(participants)))
        self.assertIn(ready[-1].fighter_id, participants)
        self.assertEqual(sum(row["main"] for row in card), 1)
        self.assertLessEqual(host.fighter_needs_matchmaking_rebuild.call_count, len(ready))
        # A subsequent call with no available athletes must not reuse a pool.
        self.assertEqual(WorldMixin.build_ai_card(host, promo, [], 8), [])

    def test_signature_migration_lookup_is_built_once(self):
        host = SimpleNamespace(signature_real_fighter_detailed_profiles=Mock(return_value={}),
                               apply_signature_real_fighter_profile=Mock(return_value=False))
        rows = [fighter(fighter_id=f"migration-{i}") for i in range(20)]
        for row in rows:
            row.realism_profile_version = 0
        self.assertEqual(PersistenceMixin.migrate_signature_real_fighter_profiles(host, rows), [])
        host.signature_real_fighter_detailed_profiles.assert_called_once_with()
        self.assertEqual(host.apply_signature_real_fighter_profile.call_count, 20)

    def test_signature_parity(self):
        source = textwrap.dedent(inspect.getsource(SeedMixin.assign_fighter_signature_moves))
        source = source.replace("    fallback_overall = fighter.overall\n", "")
        source = source.replace("details.get(key, fallback_overall)", "details.get(key, fighter.overall)")
        scope = dict(vars(seeding))
        exec(source, scope)
        host = SeedMixin()
        for release in (False, True):
            if release:
                host._fight_move_registry = RELEASE_MOVE_REGISTRY
                host._fight_move_definitions = tuple(RELEASE_MOVE_REGISTRY.values())
            for index in range(30):
                current = fighter(fighter_id=f"performance-{index}", detailed_skills={"conditioning": 40 + index})
                state = random.getstate()
                expected = scope["assign_fighter_signature_moves"](host, current)
                current.signature_moves = []
                self.assertEqual(host.assign_fighter_signature_moves(current), expected)
                self.assertEqual(random.getstate(), state)

    def test_search_pages_reach_every_match_and_clamp(self):
        value = lambda text: SimpleNamespace(get=lambda: text)
        fighters = [SimpleNamespace(name=f"Fighter {i:03}", retired=False,
                    primary_discipline="MMA", region="USA", nationality="USA",
                    gender="Male", weight="Lightweight", age=25, record="0-0",
                    last_fight="", overall=60) for i in range(205)]
        tree = Mock()
        tree.get_children.return_value = ()
        host = SimpleNamespace(
            world_fighter_tree=tree, all_database_fighters_with_companies=lambda: [("FC", f) for f in fighters],
            world_fighter_company_combo=Mock(), world_fighter_sport_combo=Mock(),
            world_fighter_search=value(""), world_fighter_company_filter=value("All"),
            world_fighter_gender_filter=value("All"), world_fighter_weight_filter=value("All"),
            world_fighter_sport_filter=value("All"), world_fighter_status_filter=value("Active"),
            player_company_name="FC", world_fighter_search_stat_visible=lambda *args: True,
            fighter_profile_stats_visible=lambda *args: True,
            fighter_display_name=lambda f: f.name, fighter_display_division=lambda f: f.weight,
            world_fighter_universe_record=lambda f: f.record, world_fighter_last_five=lambda f: "-",
            rules={}, world_fighter_search_count=Mock(), world_search_previous=Mock(), world_search_next=Mock(),
        )
        found = []
        host.scouting_display_value = ViewMixin.scouting_display_value.__get__(host)
        for page, expected in ((0, 100), (1, 100), (99, 5)):
            tree.insert.reset_mock()
            ViewMixin.refresh_world_fighter_search(host, page)
            self.assertEqual(tree.insert.call_count, expected)
            found.extend(f.name for _, f in host._world_fighter_search_rows.values())
        self.assertEqual(found, [f.name for f in fighters])
        host.world_search_next.configure.assert_called_with(state="disabled")

    def test_typing_coalesces_to_one_refresh(self):
        callbacks = {}
        def schedule(delay, callback):
            self.assertEqual(delay, 200)
            token = str(len(callbacks))
            callbacks[token] = callback
            return token
        root = SimpleNamespace(after=schedule, after_cancel=lambda token: callbacks.pop(token))
        host = SimpleNamespace(root=root, refresh_world_fighter_search=Mock())
        for _ in range(10):
            ViewMixin.schedule_world_fighter_search(host, "variable", "", "write")
        self.assertEqual(len(callbacks), 1)
        next(iter(callbacks.values()))()
        host.refresh_world_fighter_search.assert_called_once_with()

    def test_navigation_cancellation_clears_world_search_debounce(self):
        cancelled = []
        root = SimpleNamespace(after_cancel=lambda token: cancelled.append(token))
        host = SimpleNamespace(root=root, _world_search_after="world-token")
        ViewMixin.cancel_world_fighter_search(host)
        self.assertEqual(cancelled, ["world-token"])
        self.assertIsNone(host._world_search_after)

    def test_navigation_cancellation_clears_editor_debounce(self):
        cancelled = []
        root = SimpleNamespace(after_cancel=lambda token: cancelled.append(token))
        host = SimpleNamespace(root=root, _editor_refresh_after="editor-token")
        ViewMixin.cancel_database_editor_refresh(host)
        self.assertEqual(cancelled, ["editor-token"])
        self.assertIsNone(host._editor_refresh_after)

    def test_routine_refresh_does_not_redraw_hidden_pages(self):
        host = SimpleNamespace(
            refresh_header=Mock(), refresh_current_screen=Mock(),
            refresh_spectator_controls=Mock(), refresh_academy_tab=Mock(),
            refresh_combat_sports_tab=Mock(), _academy_window=object(),
            _combat_sports_redraw=Mock(),
        )
        ViewMixin.refresh_all(host)
        host.refresh_current_screen.assert_called_once_with()
        host.refresh_academy_tab.assert_not_called()
        host.refresh_combat_sports_tab.assert_not_called()
        ViewMixin.refresh_all(host, full=True)
        host.refresh_academy_tab.assert_called_once_with()
        host.refresh_combat_sports_tab.assert_called_once_with()

    def test_streamed_save_round_trip_and_failed_write_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json.gz"
            payload = {"roster": [{"name": "Fighter", "history": list(range(100))}] * 100}
            atomic_write_json_gzip(path, payload)
            with gzip.open(path, "rt", encoding="utf-8") as source:
                self.assertEqual(json.load(source), payload)
            old_bytes = path.read_bytes()
            with patch("persistence.json.dumps", side_effect=OSError("encoding failed")):
                with self.assertRaises(OSError):
                    atomic_write_json_gzip(path, {"new": True})
            self.assertEqual(path.read_bytes(), old_bytes)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
