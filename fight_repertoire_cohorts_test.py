"""Opportunity analysis retains zero-action appearances and fixed-pool limits."""
from copy import deepcopy
import unittest
from analysis.repertoire_opportunity_cohorts import analyze


class RepertoireCohortsTests(unittest.TestCase):
    def fixture(self):
        return (dict(all_bout_parity=True, registry_sha256='same', fights=1, bouts=[{'index':0}],
                     observations=[dict(bout_index=0,actor='a',round=1,tick=tick,style='Boxer',
                                        selected='used',pool=['used','unused']) for tick in (1,2)]),
                dict(registry_sha256='same',mean_distinct_moves_per_fighter=.5,
                     unobserved_active_move_ids=['unused','absent']))

    def test_zero_slot_matching_and_unused_partition(self):
        record, inventory = self.fixture()
        before = deepcopy((record,inventory))
        result = analyze(record,inventory)
        self.assertEqual(result['overall']['fighters'],2)
        self.assertEqual(result['overall']['mean_distinct'],.5)
        self.assertEqual(result['overall']['mean_fixed_pool_bound'],1)
        self.assertEqual(result['unused_offered_in_final_pool'],['unused'])
        self.assertEqual(result['unused_never_in_final_pool'],['absent'])
        self.assertEqual(sum(r['fighters'] for r in result['selection_count_cohorts'].values()),2)
        self.assertEqual((record,inventory),before)

    def test_duplicate_and_bad_membership_rejected(self):
        record, inventory = self.fixture()
        record['observations'].append(deepcopy(record['observations'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            analyze(record,inventory)
        record, inventory = self.fixture()
        record['observations'][0]['selected']='not_in_pool'
        with self.assertRaisesRegex(ValueError,'not in observed'):
            analyze(record,inventory)

    def test_missing_parity_registry_or_mean_disagreement_rejected(self):
        record, inventory = self.fixture()
        record['all_bout_parity']=False
        with self.assertRaisesRegex(ValueError,'parity'):
            analyze(record,inventory)
        record['all_bout_parity']=True
        inventory['registry_sha256']='different'
        with self.assertRaisesRegex(ValueError,'registries differ'):
            analyze(record,inventory)
        inventory['registry_sha256']='same'
        inventory['mean_distinct_moves_per_fighter']=7
        with self.assertRaisesRegex(ValueError,'does not reconcile'):
            analyze(record,inventory)


if __name__=='__main__':
    unittest.main()
