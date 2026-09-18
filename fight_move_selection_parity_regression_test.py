"""Semantic selector parity protects payloads that registry snapshots cannot see."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import asdict
import io
import json
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fight_engine
import fight_moves
from analysis.compare_bottom_move_expansion import restore_definition
from fight_engine_audit import FightAuditHarness, move_report_specs, run_audited_fight, synthetic_fighter
from tools import move_selection_parity as parity
from tools.move_registry_parity import DEFAULT_REFERENCE, envelope


class SelectionDeprecationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.registry_reference = json.loads(DEFAULT_REFERENCE.with_name(
            "move_registry_phase31_revised.json").read_text(encoding="utf-8"))
        self.current_dump = deepcopy(self.registry_reference["dump"])
        self.current_dump["schema_version"] = 2
        for row in self.current_dump["moves"]:
            row["deprecated"] = False
        old_snapshot = {"schema_version": 1, "projection_version": 1, "fight_count": 2,
                        "registry_sha256": parity.digest(self.registry_reference["dump"]),
                        "specs": [{"id": "fixture-a"}, {"id": "fixture-b"}],
                        "bouts": [{"case_id": "a:0", "seed": 1, "trace_sha256": "trace-a"},
                                  {"case_id": "b:0", "seed": 2, "trace_sha256": "trace-b"}]}
        self.reference = parity.snapshot_envelope(old_snapshot)
        self.actual = deepcopy(old_snapshot)
        self.actual["registry_sha256"] = parity.digest(self.current_dump)

    def compare(self, reference=None, actual=None, registry_reference=None, current_dump=None):
        return parity.compare_snapshot_deprecation(
            self.reference if reference is None else reference,
            self.actual if actual is None else actual,
            self.registry_reference if registry_reference is None else registry_reference,
            self.current_dump if current_dump is None else current_dump)

    def test_verified_rebinding_preserves_both_references_and_strict_mode(self):
        before = deepcopy((self.reference, self.registry_reference, self.actual, self.current_dump))
        self.assertEqual(self.compare(), [])
        self.assertTrue(parity.compare_snapshot(self.reference, self.actual))
        self.assertEqual((self.reference, self.registry_reference, self.actual, self.current_dump), before)

    def test_source_and_destination_bindings_are_required(self):
        wrong_source = deepcopy(self.reference["snapshot"])
        wrong_source["registry_sha256"] = "wrong registry"
        self.assertTrue(self.compare(reference=parity.snapshot_envelope(wrong_source)))
        wrong_destination = deepcopy(self.actual)
        wrong_destination["registry_sha256"] = parity.digest(self.registry_reference["dump"])
        self.assertTrue(self.compare(actual=wrong_destination))
        another_source = deepcopy(self.registry_reference["dump"])
        another_source["moves"][0]["name"] = "Different source registry"
        self.assertTrue(self.compare(registry_reference=envelope(another_source, "wrong source")))

    def test_registry_changes_cannot_hide_behind_a_recomputed_binding(self):
        for field, value in (("deprecated", True), ("deprecated", 0), ("name", "changed technique")):
            with self.subTest(field=field, value=value):
                changed = deepcopy(self.current_dump)
                changed["moves"][0][field] = value
                actual = deepcopy(self.actual)
                actual["registry_sha256"] = parity.digest(changed)
                self.assertTrue(self.compare(actual=actual, current_dump=changed))

    def test_selection_drift_and_both_checksum_corruptions_fail(self):
        for change in (lambda d: d["bouts"][0].update(trace_sha256="changed"),
                       lambda d: d["bouts"].reverse(), lambda d: d["specs"].reverse(),
                       lambda d: d.update(projection_version=2),
                       lambda d: d["bouts"][0].update(seed=999)):
            actual = deepcopy(self.actual)
            change(actual)
            self.assertTrue(self.compare(actual=actual))
        for field in ("selection", "registry"):
            corrupt = deepcopy(self.reference if field == "selection" else self.registry_reference)
            corrupt["sha256"] = "0" * 64
            self.assertTrue(self.compare(**{"reference" if field == "selection" else "registry_reference": corrupt}))

    def test_cli_migration_is_read_only_and_rejects_flag_without_verify(self):
        with (patch.object(Path, "read_text", side_effect=[json.dumps(self.reference), json.dumps(self.registry_reference)]),
              patch.object(Path, "open", side_effect=AssertionError("Unexpected write")),
              patch.object(parity, "build_snapshot", return_value=self.actual),
              patch.object(parity, "build_dump", return_value=self.current_dump), redirect_stdout(io.StringIO())):
            self.assertEqual(parity.main(("--verify", "selection.json", "--verify-deprecation-from", "registry.json")), 0)
        with (patch.object(parity, "build_snapshot") as build, redirect_stderr(io.StringIO()),
              self.assertRaises(SystemExit)):
            parity.main(("--capture", "new.json", "--verify-deprecation-from", "registry.json"))
        build.assert_not_called()


class SelectionParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = synthetic_fighter("Selection parity A", 76, "BJJ", "Submission Hunter", 0)
        cls.b = synthetic_fighter("Selection parity B", 75, "Wrestler", "Control", 1)
        cls.audit = run_audited_fight(FightAuditHarness(), cls.a, cls.b, parity.SEED_BASE)

    def test_complete_payload_fields_order_and_mechanics_are_hashed(self):
        expected = parity.bout_fingerprints(self.audit)
        for payload, key in (("move", "moves_sha256"), ("defense", "defenses_sha256"),
                             ("move_sequence", "sequences_sha256")):
            audit = deepcopy(self.audit)
            event = next(event for event in audit["trace"] if payload in event)
            event[payload]["new_field"] = "detect any field, not just existing keys"
            changed = parity.bout_fingerprints(audit)
            self.assertNotEqual(changed[key], expected[key])
            self.assertNotEqual(changed["trace_sha256"], expected["trace_sha256"])
        for field in ("trace", "events"):
            audit = deepcopy(self.audit)
            audit[field].reverse()
            self.assertNotEqual(parity.bout_fingerprints(audit), expected)
        audit = deepcopy(self.audit)
        audit["method"] = "changed"
        self.assertNotEqual(parity.bout_fingerprints(audit)["mechanics_sha256"], expected["mechanics_sha256"])

    def test_projection_excludes_only_declared_redundancy_and_resolver_prose(self):
        before = deepcopy(self.audit)
        projection = parity.project_audit(self.audit)
        self.assertEqual(projection["trace"], self.audit["trace"])
        self.assertEqual(self.audit, before)
        audit = deepcopy(self.audit)
        audit["signature"] = "derived hash"
        audit["events"][0]["result"] = "resolver wording"
        self.assertEqual(parity.bout_fingerprints(audit), parity.bout_fingerprints(self.audit))

    def test_corrupt_reference_changed_bout_order_and_registry_fail(self):
        snapshot = {"bouts": [{"id": 1}, {"id": 2}], "registry_sha256": "registry"}
        reference = parity.snapshot_envelope(snapshot)
        self.assertEqual(parity.compare_snapshot(reference, snapshot), [])
        changed = deepcopy(snapshot)
        changed["bouts"].reverse()
        self.assertTrue(parity.compare_snapshot(reference, changed))
        changed = deepcopy(snapshot)
        changed["registry_sha256"] = "changed"
        self.assertTrue(parity.compare_snapshot(reference, changed))
        reference["snapshot"]["bouts"].reverse()
        self.assertEqual(parity.compare_snapshot(reference, snapshot),
                         ["Selection reference checksum does not match its snapshot"])

    def test_real_bouts_repeat_and_preserve_rng_and_input_fighters(self):
        original_rng = random.getstate()
        original_fighters = (asdict(self.a), asdict(self.b))
        repeated = run_audited_fight(FightAuditHarness(), self.a, self.b, parity.SEED_BASE)
        self.assertEqual(parity.bout_fingerprints(repeated), parity.bout_fingerprints(self.audit))
        with patch.object(parity, "move_report_specs", return_value=move_report_specs()[:2]):
            first = parity.build_snapshot()
            second = parity.build_snapshot()
        self.assertEqual(first, second)
        self.assertEqual(first["fight_count"], 2)
        self.assertEqual(random.getstate(), original_rng)
        self.assertEqual((asdict(self.a), asdict(self.b)), original_fighters)

    def test_rng_and_resolver_restored_on_exception(self):
        original_rng = random.getstate()
        engine = FightAuditHarness()
        original_resolver = engine.resolve_exchange
        with patch.object(engine, "simulate_fight", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                run_audited_fight(engine, self.a, self.b, parity.SEED_BASE)
        self.assertEqual(engine.resolve_exchange, original_resolver)
        self.assertEqual(random.getstate(), original_rng)
        def fail_after_random(*args, **kwargs):
            random.random()
            raise RuntimeError("snapshot failure")
        with patch.object(parity, "run_audited_fight", side_effect=fail_after_random):
            with self.assertRaises(RuntimeError):
                parity.build_snapshot()
        self.assertEqual(random.getstate(), original_rng)

    def test_capture_refuses_overwrite_before_simulating(self):
        with (patch.object(Path, "exists", return_value=True),
              patch.object(parity, "build_snapshot") as build,
              redirect_stderr(io.StringIO()), self.assertRaises(SystemExit)):
            parity.main(("--capture", "existing.json"))
        build.assert_not_called()

    def test_verify_is_read_only(self):
        snapshot = {"fight_count": 44, "bouts": []}
        with (patch.object(Path, "read_text", return_value=json.dumps(parity.snapshot_envelope(snapshot))),
              patch.object(Path, "open", side_effect=AssertionError("Unexpected file open")),
              patch.object(parity, "build_snapshot", return_value=snapshot), redirect_stdout(io.StringIO())):
            self.assertEqual(parity.main(("--verify", "reference.json")), 0)

    def test_historical_refactor_evidence_remains_exact_with_original_content(self):
        # New successor content legitimately changes selected identities. Keep
        # verifying the old refactor against its own frozen content as well as
        # the separate current-content snapshot; never overwrite the old proof.
        # Reconstruct its pre-portrait fixture schema and reviewed earlier copy;
        # every original fixture/native trace/payload checksum remains exact.
        root = DEFAULT_REFERENCE.parent
        registry = json.loads((root / "move_registry_schema2.json").read_text(encoding="utf-8"))
        source = json.loads((root / "move_registry_phase31_revised.json").read_text(encoding="utf-8"))
        reference = json.loads((root / "move_selection_phase31.json").read_text(encoding="utf-8"))
        definitions = {row["move_id"]: restore_definition(fight_moves.MoveDefinition, row)
                       for row in registry["dump"]["moves"]}
        ordered = tuple(definitions[key] for key in registry["dump"]["move_order"])
        index = fight_moves.MoveIndex(ordered)
        facade = SimpleNamespace(**vars(fight_moves))
        facade.MOVE_DEFINITIONS = ordered
        facade.legal_moves = index.legal_moves
        self.assertEqual(parity.build_dump(facade), registry["dump"])
        prior = (fight_engine.MOVE_REGISTRY, fight_engine.legal_moves, random.getstate())
        with (patch.object(parity, "fight_moves", facade),
              patch.multiple(fight_engine, MOVE_REGISTRY=definitions, legal_moves=index.legal_moves)):
            actual = parity.build_snapshot(historical_fixture_reference=reference,
                                           historical_wording_reference=reference)
        self.assertIs(fight_engine.MOVE_REGISTRY, prior[0])
        self.assertIs(fight_engine.legal_moves, prior[1])
        self.assertEqual(random.getstate(), prior[2])
        self.assertEqual(parity.compare_snapshot_deprecation(
            reference, actual, source, parity.build_dump(facade)), [])

    def test_historical_fixture_reconstruction_is_exact_and_default_only(self):
        before = asdict(self.a)
        record = parity.historical_fixture_record(self.a)
        later_defaults = {'portrait_version', 'portrait_identity', 'trait_progress',
                          'trait_history', 'trait_injury_baseline',
                          'loan_return_month', 'loan_return_week'}
        self.assertEqual(set(before) - set(record), later_defaults)
        self.assertEqual(record, {key: value for key, value in before.items()
                                 if key not in later_defaults})
        self.assertEqual(asdict(self.a), before)
        changed = deepcopy(self.a)
        changed.power += 1
        self.assertNotEqual(parity.digest(parity.historical_fixture_record(changed)), parity.digest(record))
        for field, value in (('portrait_version', 1), ('portrait_version', False),
                             ('portrait_identity', {'seed': 1}),
                             ('trait_progress', {'points': 1}), ('trait_progress', []),
                             ('trait_history', [{'month': 1}]), ('trait_history', {}),
                             ('trait_injury_baseline', ''), ('trait_injury_baseline', 'Gym Rat'),
                             ('loan_return_month', 1), ('loan_return_month', '0'),
                             ('loan_return_week', 1), ('loan_return_week', '0')):
            changed = deepcopy(self.a)
            setattr(changed, field, value)
            with self.assertRaises(ValueError):
                parity.historical_fixture_record(changed)

    def test_historical_fixture_reconstruction_requires_known_uncorrupted_reference(self):
        reference = json.loads((DEFAULT_REFERENCE.parent / 'move_selection_phase31.json').read_text())
        for changed in (parity.snapshot_envelope({'unknown': True}), deepcopy(reference)):
            if 'bouts' in changed['snapshot']:
                changed['snapshot']['bouts'][0]['seed'] += 1
            with patch.object(parity, 'run_audited_fight') as run:
                with self.assertRaises(ValueError):
                    parity.build_snapshot(historical_fixture_reference=changed)
                run.assert_not_called()

    def test_historical_fixture_option_cannot_capture(self):
        for option in ('--historical-portrait-fixtures', '--historical-wording'):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parity.main(('--capture', 'new.json', option))

    def test_historical_wording_preserves_all_non_commentary_and_rng(self):
        from analysis.generate_variety_opportunity_report import TerminalRngHarness
        old_engine, current_engine = TerminalRngHarness(), TerminalRngHarness()
        with parity.historical_wording():
            old = run_audited_fight(old_engine, self.a, self.b, parity.SEED_BASE)
        current = run_audited_fight(current_engine, self.a, self.b, parity.SEED_BASE)
        self.assertEqual(old_engine.terminal_rng_states, current_engine.terminal_rng_states)
        for audit in (old, current):
            for event in audit['trace']:
                event.pop('commentary', None)
        self.assertEqual(old, current)

    def test_historical_wording_restores_on_error_and_rejects_structure_drift(self):
        names = ('commentary_defense_clause', 'exchange_display_move', 'evidence_driven_exchange_pool')
        originals = {name: getattr(fight_engine.FightEngineMixin, name) for name in names}
        with self.assertRaisesRegex(RuntimeError, 'test'):
            with parity.historical_wording():
                raise RuntimeError('test')
        for name in names:
            self.assertIs(getattr(fight_engine.FightEngineMixin, name), originals[name])
        with patch.object(parity.inspect, 'getsource', return_value='def changed():\n    return None\n'):
            with self.assertRaises(ValueError):
                with parity.historical_wording():
                    self.fail('Malformed helper accepted')
        for name in names:
            self.assertIs(getattr(fight_engine.FightEngineMixin, name), originals[name])


if __name__ == "__main__":
    unittest.main()
