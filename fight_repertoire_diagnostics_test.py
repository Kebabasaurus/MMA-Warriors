"""Repertoire observations and relaxed named-frequency policy stay narrowly scoped."""
from copy import deepcopy
from dataclasses import replace
import unittest

from analysis.repertoire_selection_diagnostics import build_report, summarize, concentration_floor, observed_concentration_bounds
from fight_moves import MOVE_DEFINITIONS
from analysis.evaluate_joint_fight_candidate import partition_content_findings


class RepertoireDiagnosticsTests(unittest.TestCase):
    def test_bout_observer_is_pure_and_complete(self):
        report = build_report(2)
        self.assertTrue(report['all_bout_parity'])
        self.assertEqual(sum(x['selections'] for x in report['by_action'].values()), len(report['observations']))
        self.assertTrue(report['repeated_choice_with_near_unseen_alternatives'])

    def test_repetition_nearness_and_pool_membership(self):
        row = dict(selected='old', uses={'old':2}, action='jab', style='Boxer', kind='ordinary',
                   pool=['old','fresh'], scores={'old':10,'fresh':8,'excluded':10})
        before = deepcopy(row)
        report = summarize([row])
        self.assertEqual(report['by_action']['jab']['repeat_with_unseen_near_final_alternative'],1)
        self.assertEqual(report['repeated_choice_with_near_unseen_alternatives'][0]['alternative'],'fresh')
        for change in ({'uses':{'old':1}}, {'uses':{'old':2,'fresh':1}}, {'scores':{'old':10,'fresh':7.7}}):
            self.assertNotIn('repeat_with_unseen_near_final_alternative',summarize([dict(row,**change)])['by_action']['jab'])
        self.assertEqual(row,before)

    def test_only_known_named_absences_are_advisory(self):
        warnings = ['Phase 29 move absent from ordinary fights: scarf_hold_straight_armbar',
                    'Phase 30 move absent: example', 'Slice 5 move absent: example', 'Slice 6 move absent: example']
        failures = ['Phase 29 top submission concentration exceeds 25%',
                    'Phase 29 submission pool below six: guard', 'Unknown coverage error',
                    'More than eight active moves unobserved', 'Mean distinct moves outside 20-24']
        self.assertEqual(partition_content_findings(warnings+failures),(failures,warnings))

    def test_invalid_counts_rejected(self):
        for count in (0,-1,True):
            with self.assertRaises(ValueError):
                build_report(count)

    def test_current_combined_observer_records_choice_facts_and_reconciles(self):
        report = build_report(2, retained_damage=True)
        self.assertTrue(report['all_bout_parity'])
        self.assertEqual(report['total_selections'], sum(row['selected'] for row in report['move_counts']))
        for row in report['observations']:
            choice = row['choice_context']
            for key in ('actor', 'action', 'round', 'tick'):
                self.assertEqual(choice[key],row[key])
            self.assertGreaterEqual(choice['gas'],0)
        for row in report['move_counts']:
            bins = sum(n for key,n in row['cohorts'].items() if key.startswith('choice_gas_'))
            self.assertEqual(bins,row['selected'])

    def test_scored_and_offered_counts_are_opportunities_not_score_sums(self):
        row = dict(selected='old', uses={'old':2}, action='jab', style='Boxer', kind='ordinary',
                   pool=['old','fresh'], scores={'old':10,'fresh':8,'excluded':10})
        result = summarize([row,row])
        chosen = result['move_counts'][0]
        self.assertEqual((chosen['selected'],chosen['offered'],chosen['scored_eligible']),(2,2,2))
        self.assertEqual(result['top_ten_move_share_pct'],100)
        unused = {r['move_id']:r for r in result['move_counts']}
        self.assertEqual((unused['fresh']['selected'],unused['fresh']['offered']),(0,2))
        self.assertEqual((unused['excluded']['selected'],unused['excluded']['offered'],
                          unused['excluded']['scored_eligible']),(0,0,2))

    def test_small_action_family_is_lower_bound_not_predicted_result(self):
        base = MOVE_DEFINITIONS[0]
        ten = [replace(base,move_id=f'rest_{i}',parent_action='rest',deprecated=False) for i in range(10)]
        row = concentration_floor({'rest':26,'other':74},100,ten)[0]
        self.assertEqual(row['minimum_top_ten_pct'],26)
        eleven = ten + [replace(ten[0],move_id='extra')]
        self.assertEqual(concentration_floor({'rest':26,'other':74},100,eleven),[])
        eleven[-1] = replace(eleven[-1],deprecated=True)
        self.assertEqual(concentration_floor({'rest':26,'other':74},100,eleven)[0],row)
        with self.assertRaises(ValueError):
            concentration_floor({'rest':26},100,ten)

    def test_unregistered_and_wrong_action_cannot_establish_bound(self):
        move = replace(MOVE_DEFINITIONS[0],parent_action='rest',deprecated=False)
        good = dict(action='rest',selected=move.move_id)
        self.assertEqual(observed_concentration_bounds([good],[move])[0]['minimum_top_ten_pct'],100)
        for bad in (dict(action='rest',selected='generic_rest'),dict(action='other',selected=move.move_id)):
            rows = [bad] if bad['action']=='other' else [good,bad]
            self.assertEqual(observed_concentration_bounds(rows,[move]),[])


if __name__=='__main__':
    unittest.main()
