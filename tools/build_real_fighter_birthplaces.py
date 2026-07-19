"""Build the packaged real-fighter birthplace map from Wikidata P19 records."""
import json
import argparse
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stability_test import destroy_root, new_app, silence_dialogs


OUT = ROOT / "assets" / "real_fighter_birthplaces.json"
AUDIT = ROOT / "audits" / "real_fighter_birthplace_coverage.txt"
ALIASES = (" CW", " WEC", " LFA")
COMBAT_DESCRIPTORS = (
    "mixed martial", "mma fighter", "martial artist", "professional wrestler",
    "amateur wrestler", "freestyle wrestler", "greco-roman wrestler", "boxer",
    "kickboxer", "muay thai", "judoka", "grappler", "bare-knuckle", "combat sambo",
)


def canonical_name(name):
    for suffix in ALIASES:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def query_batch(names):
    values = " ".join(json.dumps(name) + "@en" for name in names)
    query = f"""
SELECT ?person ?personLabel ?birthplaceLabel ?birthCountryLabel ?citizenshipLabel ?occupationLabel WHERE {{
  VALUES ?name {{ {values} }}
  ?person rdfs:label ?name; wdt:P31 wd:Q5; wdt:P19 ?birthplace.
  OPTIONAL {{ ?birthplace wdt:P17 ?birthCountry. }}
  OPTIONAL {{ ?person wdt:P27 ?citizenship. }}
  OPTIONAL {{ ?person wdt:P106 ?occupation. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"format": "json", "query": query})
    for attempt in range(5):
        request = urllib.request.Request(url, headers={"User-Agent": "MMAWarriorsBirthplaceAudit/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)["results"]["bindings"]
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))


def api_json(params):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"format": "json", **params})
    for attempt in range(6):
        request = urllib.request.Request(url, headers={"User-Agent": "MMAWarriorsBirthplaceAudit/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(2.5 * (attempt + 1))


def search_combat_entity(name):
    time.sleep(0.65)
    data = api_json({"action": "wbsearchentities", "search": name, "language": "en", "limit": 7, "type": "item"})
    candidates = []
    for row in data.get("search", []):
        description = row.get("description", "").lower()
        if any(term in description for term in COMBAT_DESCRIPTORS):
            label = row.get("label", "")
            score = (3 if label.casefold() == name.casefold() else 1) + (1 if "mixed martial" in description or "mma fighter" in description else 0)
            candidates.append((score, row.get("id", "")))
    if not candidates:
        return name, ""
    candidates.sort(reverse=True)
    return name, candidates[0][1]


def entity_rows(entity_ids):
    rows = {}
    for offset in range(0, len(entity_ids), 45):
        ids = entity_ids[offset:offset + 45]
        data = api_json({"action": "wbgetentities", "ids": "|".join(ids), "languages": "en", "props": "labels|claims"})
        rows.update(data.get("entities", {}))
    return rows


def claim_id(entity, prop):
    claims = entity.get("claims", {}).get(prop, [])
    for claim in claims:
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(value, dict) and value.get("id"):
            return value["id"]
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-fallback", action="store_true", help="Use slower API reconciliation for labels not resolved by SPARQL.")
    args = parser.parse_args()
    silence_dialogs()
    root, app, _errors = new_app(20260718)
    try:
        fighters = [fighter for fighter in app.all_database_fighters() if not getattr(fighter, "generated", False)]
        source_names = sorted({fighter.name for fighter in fighters})
    finally:
        destroy_root(root)

    canonical_names = sorted({canonical_name(name) for name in source_names})
    matches = {}
    ambiguous = set()
    for offset in range(0, len(canonical_names), 30):
        batch = canonical_names[offset:offset + 30]
        rows = query_batch(batch)
        by_name = {}
        for row in rows:
            name = row.get("personLabel", {}).get("value", "")
            city = row.get("birthplaceLabel", {}).get("value", "")
            if not name or not city or city.startswith("Q"):
                continue
            candidate = {
                "city": city,
                "birth_country": row.get("birthCountryLabel", {}).get("value", ""),
                "citizenship": row.get("citizenshipLabel", {}).get("value", ""),
                "wikidata": row.get("person", {}).get("value", ""),
                "occupations": set(),
            }
            candidates = by_name.setdefault(name, {})
            stored = candidates.setdefault(candidate["wikidata"], candidate)
            occupation = row.get("occupationLabel", {}).get("value", "").lower()
            if occupation:
                stored["occupations"].add(occupation)
        for name, candidates in by_name.items():
            if len(candidates) == 1:
                chosen = next(iter(candidates.values()))
                chosen.pop("occupations", None)
                matches[name] = chosen
            else:
                combat = [candidate for candidate in candidates.values()
                          if any(term in occupation for occupation in candidate["occupations"] for term in COMBAT_DESCRIPTORS)]
                if len(combat) == 1:
                    chosen = combat[0]
                    chosen.pop("occupations", None)
                    matches[name] = chosen
                else:
                    ambiguous.add(name)
        print(f"Queried {min(offset + len(batch), len(canonical_names))}/{len(canonical_names)}; matched {len(matches)}", flush=True)
        time.sleep(0.15)

    if args.search_fallback:
        unmatched = [name for name in canonical_names if name not in matches or name in ambiguous]
        fallback_ids = {}
        with ThreadPoolExecutor(max_workers=1) as pool:
            futures = [pool.submit(search_combat_entity, name) for name in unmatched]
            for index, future in enumerate(as_completed(futures), 1):
                name, entity_id = future.result()
                if entity_id:
                    fallback_ids[name] = entity_id
                if index % 75 == 0:
                    print(f"Reconciled {index}/{len(unmatched)} unmatched names; found {len(fallback_ids)} combat athletes", flush=True)
        entities = entity_rows(sorted(set(fallback_ids.values())))
        place_ids = []
        citizenship_ids = []
        for entity_id in fallback_ids.values():
            entity = entities.get(entity_id, {})
            place_ids.append(claim_id(entity, "P19"))
            citizenship_ids.append(claim_id(entity, "P27"))
        labels = entity_rows(sorted({value for value in place_ids + citizenship_ids if value}))
        for name, entity_id in fallback_ids.items():
            entity = entities.get(entity_id, {})
            place_id = claim_id(entity, "P19")
            if not place_id:
                continue
            citizenship_id = claim_id(entity, "P27")
            city = labels.get(place_id, {}).get("labels", {}).get("en", {}).get("value", "")
            citizenship = labels.get(citizenship_id, {}).get("labels", {}).get("en", {}).get("value", "")
            if city:
                matches[name] = {
                    "city": city,
                    "birth_country": citizenship,
                    "citizenship": citizenship,
                    "wikidata": f"http://www.wikidata.org/entity/{entity_id}",
                }
                ambiguous.discard(name)

    # Apply verified base identities to intentional younger-promotion variants.
    output = {}
    for name in source_names:
        base = canonical_name(name)
        if base in matches and base not in ambiguous:
            output[name] = matches[base]
    payload = {
        "schema": 1,
        "source": "Wikidata P19 (place of birth), P17 (birthplace country), and P27 (citizenship)",
        "source_url": "https://www.wikidata.org/wiki/Property:P19",
        "fighters": output,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    missing = [name for name in source_names if name not in output]
    lines = [
        "MMA WARRIORS - REAL FIGHTER BIRTHPLACE COVERAGE",
        f"Seeded named fighters: {len(source_names)}",
        f"Verified birthplace matches: {len(output)} ({len(output) / max(1, len(source_names)) * 100:.1f}%)",
        f"Unmatched or ambiguous: {len(missing)}",
        "",
        "UNMATCHED / AMBIGUOUS",
        *missing,
    ]
    AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {AUDIT}")


if __name__ == "__main__":
    main()
