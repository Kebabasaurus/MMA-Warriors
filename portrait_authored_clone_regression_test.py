"""Guards against accidental duplicate full vectors in named portrait cohorts."""

from collections import defaultdict
import unittest

from fighter_portraits.ranked_101_200 import PORTRAIT_RANK_101_200_OVERRIDES


class AuthoredPortraitCloneRegressionTests(unittest.TestCase):
    def test_second_hundred_only_reuses_intentional_archive_looks(self):
        vectors = defaultdict(list)
        for name, identity in PORTRAIT_RANK_101_200_OVERRIDES.items():
            vectors[tuple(sorted(identity.items()))].append(name)
        duplicates = [names for names in vectors.values() if len(names) > 1]
        self.assertEqual(
            [["Quinton Jackson", "Quinton Jackson Legend"],
             ["Robbie Lawler", "Robbie Lawler Legend"],
             ["Wanderlei Silva", "Wanderlei Silva Legend"],
             ["Cris Cyborg", "Cris Cyborg SF"],
             ["Paddy Pimblett", "Paddy Pimblett CW"]],
            duplicates,
        )


if __name__ == "__main__":
    unittest.main()
