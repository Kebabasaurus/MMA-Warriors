"""Regression coverage for shared, non-mutating universe validation."""

import json
import re
import tempfile
import unittest
from pathlib import Path

from admin import AdminMixin
from constants import COUNTRY_TO_REGION, REGION_COUNTRIES, REGIONS
from database_editor import fighter_row_from_record, sync_fighter_groups
from seeding import MMA_FIGHTER_DATABASE_SCHEMA, SeedMixin
from universe_validation import preflight_universe_pack, validate_universe_pack, validate_universe_pack_issues


ROOT = Path(__file__).resolve().parent
DEFAULT_PACK = ROOT / "Databases" / "Default Universe.universe.json"


class SeedProbe(SeedMixin, AdminMixin):
    def __init__(self, default_path):
        self.default_path = Path(default_path)

    def universe_database_path(self, _name):
        return self.default_path


class UniverseValidationRegressionTest(unittest.TestCase):
    def load_default(self):
        return json.loads(DEFAULT_PACK.read_text(encoding="utf-8"))

    def test_shipped_pack_passes_shared_validator(self):
        self.assertEqual(validate_universe_pack(self.load_default()), [])

    def test_shipped_fighter_identity_and_birthplace_data_is_complete(self):
        pack = self.load_default()
        fighters = pack["sections"]["fighters"]
        records = fighters["all_fighters"]
        fighter_ids = [str(record.get("fighter_id", "")).strip() for record in records]
        self.assertEqual(fighters["schema"], MMA_FIGHTER_DATABASE_SCHEMA)
        self.assertEqual(len(records), 1534)
        self.assertEqual(len(set(fighter_ids)), len(records))
        self.assertTrue(all(re.fullmatch(r"FTR-DU-[0-9a-f]{32}", fighter_id) for fighter_id in fighter_ids))
        self.assertTrue(all(record.get("birth_country") and record.get("hometown") for record in records))
        supported_birth_countries = set(COUNTRY_TO_REGION) | set(REGION_COUNTRIES.values())
        self.assertTrue(all(record["birth_country"] in supported_birth_countries for record in records))
        self.assertEqual(
            sum(record.get("birthplace_source") == "regional_fallback_v1" for record in records),
            728,
        )
        self.assertEqual(
            sum(record.get("birthplace_source") == "bundled_verified_identity" for record in records),
            1,
        )
        expected_styles = {
            "Jiri Prochazka": "Kickboxer",
            "Brandon Royval": "BJJ",
            "Lito Adiwang": "Sanda",
            "Kevin Belingon": "Sanda",
        }
        by_name = {record["name"]: record for record in records}
        self.assertEqual(
            {name: by_name[name]["style"] for name in expected_styles},
            expected_styles,
        )

        expected_player = [fighter_row_from_record(record) for record in records if record.get("placement") == "player_roster" or record.get("owner") == "BAMMA"]
        expected_free_agents = [fighter_row_from_record(record) for record in records if record.get("placement") == "free_agents" or record.get("owner") in ("Free Agent", "Legend")]
        self.assertEqual(fighters["player_roster"], expected_player)
        self.assertEqual(fighters["free_agents"], expected_free_agents)
        for owner, rows in fighters["promotions"].items():
            expected = [
                fighter_row_from_record(record)
                for record in records
                if record.get("owner") == owner
                and record.get("placement") not in ("player_roster", "free_agents")
            ]
            self.assertEqual(rows, expected, owner)

    def test_shipped_global_rights_packages_cover_every_region(self):
        media = self.load_default()["sections"]["media"]
        packages = {package["id"]: package for package in media["rights_packages"]}
        for package_id in (
            "local_fight_stream",
            "world_fight_pass",
            "prime_sports_network",
            "global_sports_plus",
        ):
            self.assertEqual(set(packages[package_id]["markets"]), set(REGIONS), package_id)

    def test_schema_five_requires_source_ids_but_legacy_sync_backfills_them(self):
        pack = self.load_default()
        fighters = pack["sections"]["fighters"]
        fighters["all_fighters"][0].pop("fighter_id")
        messages = validate_universe_pack(pack)
        self.assertTrue(any("fighter_id: is required by fighter schema 5+" in message for message in messages))

        fighters["schema"] = 4
        sync_fighter_groups(fighters)
        assigned = fighters["all_fighters"][0]["fighter_id"]
        self.assertRegex(assigned, r"^FTR-DU-[0-9a-f]{32}$")
        sync_fighter_groups(fighters)
        self.assertEqual(fighters["all_fighters"][0]["fighter_id"], assigned)
        self.assertEqual(validate_universe_pack(pack), [])

    def test_bad_media_and_scalar_types_are_reported_not_raised(self):
        pack = self.load_default()
        pack["sections"]["media"]["rights_packages"] = [{"name": "Broken", "base_fee": "not-a-number", "reach": "high"}]
        issues = validate_universe_pack_issues(pack)
        self.assertTrue(any(issue.section == "media" and issue.field == "base_fee" for issue in issues))
        self.assertTrue(any(issue.section == "media" and issue.field == "reach" for issue in issues))

    def test_mma_fighter_identity_enums_are_validated(self):
        pack = self.load_default()
        record = pack["sections"]["fighters"]["all_fighters"][0]
        record.update({
            "style": "Dynamic Attacker", "profile_style": "Wushu",
            "secondary_style": "Wushu", "trait": "Invented Trait",
            "behaviour": "Invented Behaviour",
            "signature_moves": ["not_a_real_move", "not_a_real_move", "one_two", "single_jab"],
        })
        issues = validate_universe_pack_issues(pack)
        fields = {
            issue.field for issue in issues
            if issue.section == "fighters" and issue.record == record["name"]
        }
        self.assertTrue({"style", "profile_style", "secondary_style", "trait", "behaviour", "signature_moves"} <= fields)

    def test_missing_cross_section_and_combat_data_are_reported(self):
        pack = self.load_default()
        del pack["sections"]["regions"]
        pack["sections"]["combat_sports"]["profiles"]["Boxing"] = "broken"
        messages = validate_universe_pack(pack)
        self.assertTrue(any(message.startswith("regions") for message in messages))
        self.assertTrue(any(message.startswith("combat_sports.Boxing.profiles") for message in messages))

    def test_normal_load_keeps_legacy_source_bytes_and_mtime_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / DEFAULT_PACK.name
            pack = self.load_default()
            del pack["sections"]["combat_sports"]["schema"]
            pack["sections"]["fighters"]["schema"] = 4
            pack["sections"]["fighters"]["all_fighters"][0].pop("fighter_id")
            path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
            before_bytes = path.read_bytes()
            before_mtime = path.stat().st_mtime_ns
            loaded = SeedProbe(path).load_universe_database_pack(path)
            self.assertGreaterEqual(loaded["sections"]["combat_sports"]["schema"], 4)
            self.assertRegex(
                loaded["sections"]["fighters"]["all_fighters"][0]["fighter_id"],
                r"^FTR-DU-[0-9a-f]{32}$",
            )
            self.assertEqual(path.read_bytes(), before_bytes)
            self.assertEqual(path.stat().st_mtime_ns, before_mtime)

    def test_preflight_is_structured_and_does_not_mutate_the_pack(self):
        pack = self.load_default()
        pack["sections"]["companies"]["promotions"][0]["parent_company"] = "Missing Parent"
        pack["titles"] = {"Male Lightweight": "No Such Fighter"}
        before = json.loads(json.dumps(pack))
        findings = preflight_universe_pack(pack)
        self.assertEqual(pack, before)
        self.assertTrue(findings)
        self.assertTrue(all({"severity", "category", "entity", "field", "evidence", "remedy"} <= set(row) for row in findings))
        self.assertTrue(any(row["field"] == "parent_company" and row["severity"] == "error" for row in findings))
        self.assertTrue(any(row["field"] == "Male Lightweight" and row["severity"] == "error" for row in findings))
        self.assertTrue(any(row["severity"] == "warning" and row["category"] == "population" for row in findings))

    def test_preflight_reports_explicit_payroll_over_cash_without_inventing_salary_fields(self):
        pack = self.load_default()
        fighter = next(row for row in pack["sections"]["fighters"]["all_fighters"] if row.get("placement") == "promotion")
        owner = fighter["owner"]
        company = next(
            row for row in pack["sections"]["companies"]["promotions"]
            if row.get("name") == owner or row.get("roster_key") == owner
        )
        fighter["salary"] = company["cash"] + 1
        findings = preflight_universe_pack(pack)
        self.assertTrue(any(row["category"] == "payroll" and row["entity"] == f"company:{company['name']}" for row in findings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
