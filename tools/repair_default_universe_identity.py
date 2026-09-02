"""Apply deterministic identity completeness repairs to the shipped universe.

This is an explicit maintenance command, not a runtime migration. Existing
authored birthplaces are preserved. Missing locations use the bundled verified
identity data when possible and otherwise receive a deterministic regional
fallback marked with ``birthplace_source=regional_fallback_v1``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from constants import (
    COUNTRY_NATIONALITIES,
    COUNTRY_TO_REGION,
    REGION_CITIES,
    REGION_COUNTRIES,
    REGION_IDENTITY_PROFILES,
    REGIONS,
)
from database_editor import sync_fighter_groups
from models import deterministic_source_fighter_id


DATABASE = ROOT / "Databases" / "Default Universe.universe.json"
GLOBAL_PACKAGE_IDS = {
    "local_fight_stream",
    "world_fight_pass",
    "prime_sports_network",
    "global_sports_plus",
}
REGION_ALIASES = {
    "Argentina": "Brazil",
    "Latin America": "Mexico",
    "New Zealand": "Australia",
}
SPECIAL_PROFILES = {
    "Argentina": ("Argentina", "Argentine", ["Buenos Aires", "Cordoba", "Rosario", "Mendoza"]),
    "New Zealand": ("New Zealand", "New Zealander", ["Auckland", "Wellington", "Christchurch", "Hamilton"]),
}


def normalized_name(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return "".join(character for character in value.casefold() if character.isalnum())


def stable_index(fighter_id, label, length):
    digest = hashlib.sha256(f"regional-fallback-v1|{fighter_id}|{label}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % length


def verified_birthplaces():
    path = ROOT / "assets" / "real_fighter_birthplaces.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {normalized_name(name): value for name, value in payload.get("fighters", {}).items()}


def regional_profile(record):
    authored_region = str(record.get("region", "USA"))
    if authored_region in SPECIAL_PROFILES:
        return SPECIAL_PROFILES[authored_region]
    region = authored_region if authored_region in REGIONS else REGION_ALIASES.get(authored_region, "USA")
    profiles = list(REGION_IDENTITY_PROFILES.get(region, ()))
    if not profiles:
        country = next((country for country, mapped in COUNTRY_TO_REGION.items() if mapped == region), region)
        return country, COUNTRY_NATIONALITIES.get(country, str(record.get("nationality", region))), REGION_CITIES[region]
    nationality = str(record.get("nationality", "")).strip().casefold()
    matching = [profile for profile in profiles if str(profile[1]).casefold() == nationality]
    if not matching and region in ("UK", "Europe", "Asia", "Middle East", "Africa"):
        return REGION_COUNTRIES[region], str(record.get("nationality", region)), REGION_CITIES[region]
    choices = matching or profiles
    fighter_id = record["fighter_id"]
    return choices[stable_index(fighter_id, "country", len(choices))]


def repair(pack):
    sections = pack["sections"]
    fighters = sections["fighters"]
    records = fighters["all_fighters"]
    verified = verified_birthplaces()
    seen_ids = set()
    repaired_places = 0
    verified_places = 0

    for record in records:
        fighter_id = str(record.get("fighter_id", "")).strip() or deterministic_source_fighter_id(record)
        if fighter_id in seen_ids:
            raise ValueError(f"duplicate generated source fighter ID: {fighter_id}")
        record["fighter_id"] = fighter_id
        seen_ids.add(fighter_id)
        if (record.get("birth_country") or record.get("hometown")) and record.get("birthplace_source") != "regional_fallback_v1":
            continue

        before_place = (
            record.get("birth_country"),
            record.get("hometown"),
            record.get("birthplace_source"),
        )
        identity = verified.get(normalized_name(record.get("name", "")))
        city = str((identity or {}).get("city", "")).strip()
        country = str((identity or {}).get("birth_country", "") or (identity or {}).get("citizenship", "")).strip()
        if city and country and country in COUNTRY_TO_REGION:
            record["birth_country"] = country
            record["hometown"] = city
            record["birthplace_source"] = "bundled_verified_identity"
            verified_places += 1
        else:
            country, _nationality, cities = regional_profile(record)
            record["birth_country"] = country
            record["hometown"] = cities[stable_index(fighter_id, "city", len(cities))]
            record["birthplace_source"] = "regional_fallback_v1"
        after_place = (
            record.get("birth_country"),
            record.get("hometown"),
            record.get("birthplace_source"),
        )
        if after_place != before_place:
            repaired_places += 1

    fighters["schema"] = 5
    sync_fighter_groups(fighters)
    for package in sections["media"]["rights_packages"]:
        if package.get("id") in GLOBAL_PACKAGE_IDS:
            package["markets"] = list(REGIONS)
    return repaired_places, verified_places


def main():
    pack = json.loads(DATABASE.read_text(encoding="utf-8"))
    repaired_places, verified_places = repair(pack)
    DATABASE.write_text(json.dumps(pack, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"Ensured {len(pack['sections']['fighters']['all_fighters'])} source IDs and "
        f"{repaired_places} birthplace rows ({verified_places} bundled verified; "
        f"{repaired_places - verified_places} deterministic regional fallbacks)."
    )


if __name__ == "__main__":
    main()
