"""S3 specialty catalogue regressions: truthful descriptions, no free-form buffs."""

import unittest

from staff_specialties import STAFF_SPECIALTY_DEFINITIONS, staff_specialty_definition, staff_specialty_snapshot, validate_staff_specialty_catalogue


class StaffSpecialtyTests(unittest.TestCase):
    def test_every_catalogue_entry_has_explanation_and_effect_classification(self):
        self.assertEqual(validate_staff_specialty_catalogue(), [])
        self.assertGreaterEqual(len(STAFF_SPECIALTY_DEFINITIONS), 18)

    def test_live_entries_are_limited_to_approved_effect_owners(self):
        live = [definition for definition in STAFF_SPECIALTY_DEFINITIONS.values() if definition["classification"] == "Live mechanic"]
        self.assertTrue(live)
        self.assertTrue(all(definition["role"] in {"Scout", "Marketing", "Talent Relations", "Broadcast Producer"} for definition in live))
        self.assertEqual(
            {definition["id"] for definition in live} - {"prospect_eye", "international_network", "womens_divisions", "campaign_coordinator", "contract_administrator", "production_coordinator"},
            set(),
        )

    def test_approved_specialties_explain_their_bounded_effect(self):
        expected = {
            "Campaign Coordinator": "paid media campaign",
            "Contract Administrator": "2%",
            "Production Coordinator": "production-staging",
        }
        for specialty, phrase in expected.items():
            definition = STAFF_SPECIALTY_DEFINITIONS[specialty]
            self.assertEqual(definition["classification"], "Live mechanic")
            self.assertIn(phrase.lower(), definition["advantages"].lower())
            self.assertIn("effective", definition["triggers"].lower())

    def test_unknown_legacy_specialty_is_retained_as_personality_only(self):
        definition = staff_specialty_definition("Legacy Focus", "Marketing")
        self.assertEqual(definition["classification"], "Personality only")
        self.assertIn("without guessing", definition["description"])
        snapshot = staff_specialty_snapshot({"staff_id": "S1", "name": "A", "role": "Marketing", "specialty": "Legacy Focus"})
        self.assertEqual(snapshot["staff_id"], "S1")
        self.assertEqual(snapshot["name"], "A")

    def test_snapshot_does_not_mutate_staff_member(self):
        member = {"name": "Maya", "role": "Scout", "specialty": "Prospect eye"}
        before = dict(member)
        snapshot = staff_specialty_snapshot(member)
        snapshot["advantages"] = "changed"
        self.assertEqual(member, before)
        self.assertEqual(member["specialty"], "Prospect eye")


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
