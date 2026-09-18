"""Release host isolation and live full-bout parity, not only mixin authoring."""
import subprocess
import sys
import unittest
from unittest.mock import patch

from analysis.verify_release_integration import verify, NativeHarness
from fight_release import survival_role_allows
from analysis.survival_expansion_candidate import role_allows
from fight_moves.release_registry import RELEASE_MOVE_DEFINITIONS
from fight_engine import FightEngineMixin


class ReleaseIntegrationTests(unittest.TestCase):
    def test_complete_native_bouts_equal_accepted_candidate(self):
        report = verify(12)
        self.assertTrue(report['all_complete_bouts_and_rng_equal'])
        self.assertEqual(report['failures'], [])
        self.assertEqual(len(report['pairs']), 12)

    def test_native_mismatch_cannot_pass(self):
        with patch.object(NativeHarness, '_release_head_damage', False):
            with self.assertRaisesRegex(ValueError, 'Native parity failed'):
                verify(12)

    def test_survival_roles_equal_in_every_geometry(self):
        for move in RELEASE_MOVE_DEFINITIONS:
            if move.parent_action != 'survive':
                continue
            for position in move.positions | {'range', 'leg entanglement'}:
                for top, bottom in (('a', 'b'), ('b', 'a'), ('a', 'a'), (None, None)):
                    for controller in ('a', 'b', None):
                        for actor in ('a', 'b', None):
                            state = dict(top=top, bottom=bottom, clinch_controller=controller)
                            self.assertEqual(survival_role_allows(move.move_id, position, actor, state),
                                             role_allows(move.move_id, position, actor, state))

    def test_release_import_does_not_activate_or_import_audit_code(self):
        script = ('import sys; import fight_release; import fight_moves; '
                  'from fight_engine import FightEngineMixin; '
                  'assert len(fight_moves.MOVE_DEFINITIONS)==346; '
                  'assert not getattr(FightEngineMixin,"_experimental_specialist_entries",False); '
                  'assert not any(k.startswith("analysis.") or k=="unittest.mock" for k in sys.modules)')
        result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
