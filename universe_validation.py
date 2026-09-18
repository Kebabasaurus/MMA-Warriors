"""Side-effect-free validation for editable MMA Warriors universe packs.

This module is intentionally usable by the game, the database editor, and
release tooling.  Keep data normalisation/migration in ``seeding.py``: a
validator reports problems and never changes the supplied pack.
"""

from collections import Counter
from dataclasses import dataclass

from constants import BEHAVIOURS, COMBAT_SPORT_WEIGHT_CLASSES, DETAILED_SKILL_GROUPS, REGIONS, STYLES, TRAITS, WEIGHTS
from fight_moves.release_registry import RELEASE_MOVE_REGISTRY as MOVE_REGISTRY


FIGHTER_REQUIRED_FIELDS = ("name", "placement", "owner", "weight", "gender", "rating", "age", "region", "nationality")
COMPANY_REQUIRED_FIELDS = ("name", "region", "size", "cash", "roster_key")
REQUIRED_SECTIONS = ("fighters", "combat_sports", "companies", "media", "regions")
COMBAT_SPORTS = ("Boxing", "Kickboxing", "Muay Thai", "Lethwei", "Wrestling", "Brazilian Jiu-Jitsu")
# Curated records predate the compact simulation-region and active-weight
# selectors.  They are valid authored values and are mapped during seeding.
FIGHTER_WEIGHT_ALIASES = frozenset(("Atomweight", "Strawweight"))
FIGHTER_REGION_ALIASES = frozenset(("Argentina", "Latin America", "New Zealand"))


@dataclass(frozen=True)
class UniverseValidationIssue:
    section: str
    record: str
    field: str
    reason: str

    def __str__(self):
        location = ".".join(part for part in (self.section, self.record, self.field) if part)
        return f"{location}: {self.reason}" if location else self.reason


def _issue(issues, section, record, field, reason):
    issues.append(UniverseValidationIssue(section, str(record), field, reason))


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _number_in_range(issues, section, record, field, value, minimum, maximum):
    if not _integer(value):
        _issue(issues, section, record, field, "must be an integer")
    elif not minimum <= value <= maximum:
        _issue(issues, section, record, field, f"must be {minimum}-{maximum}")


def validate_universe_section_issues(section, value, *, company_names=()):
    """Return structured issues for one section without throwing on bad input."""
    issues = []
    if section == "fighters":
        if not isinstance(value, dict):
            _issue(issues, section, "", "", "must be an object")
            return issues
        records = value.get("all_fighters", [])
        if not isinstance(records, list) or not records:
            _issue(issues, section, "all_fighters", "", "must contain fighter records")
            return issues
        try:
            fighter_schema = int(value.get("schema", 1) or 1)
        except (TypeError, ValueError):
            fighter_schema = 1
            _issue(issues, section, "", "schema", "must be an integer")
        fighter_ids, owner_pairs = set(), set()
        allowed_owners = {str(name) for name in company_names} | {"Free Agent", "Legend", ""}
        for index, record in enumerate(records):
            label = str(record.get("name", f"#{index}")) if isinstance(record, dict) else f"#{index}"
            if not isinstance(record, dict):
                _issue(issues, section, label, "", "fighter record must be an object")
                continue
            for field in FIGHTER_REQUIRED_FIELDS:
                if record.get(field) in (None, ""):
                    _issue(issues, section, label, field, "is required")
            for field in ("rating", "age", "record_w", "record_l", "record_d"):
                _number_in_range(issues, section, label, field, record.get(field, 0), 0 if field.startswith("record_") else (1 if field == "rating" else 14), 999 if field.startswith("record_") else (99 if field == "rating" else 70))
            if record.get("weight") not in set(WEIGHTS) | FIGHTER_WEIGHT_ALIASES:
                _issue(issues, section, label, "weight", "is not a supported division")
            if record.get("region") not in set(REGIONS) | FIGHTER_REGION_ALIASES:
                _issue(issues, section, label, "region", "is not a supported region")
            if record.get("gender") not in ("Male", "Female"):
                _issue(issues, section, label, "gender", "must be Male or Female")
            if record.get("style") not in STYLES:
                _issue(issues, section, label, "style", "is not a supported value")
            for field, choices in (
                ("profile_style", STYLES), ("secondary_style", STYLES),
                ("trait", TRAITS), ("behaviour", BEHAVIOURS),
            ):
                if record.get(field) not in (None, "") and record.get(field) not in choices:
                    _issue(issues, section, label, field, "is not a supported value")
            if (record.get("secondary_style")
                    and record.get("secondary_style") == record.get("style")):
                _issue(issues, section, label, "secondary_style", "must differ from the primary style")
            signature_moves = record.get("signature_moves", [])
            if not isinstance(signature_moves, list):
                _issue(issues, section, label, "signature_moves", "must be a list of up to three move IDs")
            elif len(signature_moves) > 3 or len(signature_moves) != len(set(signature_moves)):
                _issue(issues, section, label, "signature_moves", "must contain up to three unique move IDs")
            else:
                for move_id in signature_moves:
                    if move_id not in MOVE_REGISTRY:
                        _issue(issues, section, label, "signature_moves", f"contains unknown move ID {move_id!r}")
            fighter_id = str(record.get("fighter_id", "")).strip()
            if fighter_schema >= 5 and not fighter_id:
                _issue(issues, section, label, "fighter_id", "is required by fighter schema 5+")
            if fighter_id:
                if fighter_id in fighter_ids:
                    _issue(issues, section, label, "fighter_id", "duplicates another fighter ID")
                fighter_ids.add(fighter_id)
            owner = str(record.get("owner", ""))
            pair = (str(record.get("name", "")).casefold(), owner.casefold())
            if pair in owner_pairs:
                _issue(issues, section, label, "owner", "duplicates a fighter/owner pair")
            owner_pairs.add(pair)
            if company_names and owner not in allowed_owners:
                _issue(issues, section, label, "owner", "does not reference a known company or market owner")
    elif section == "companies":
        if not isinstance(value, dict):
            _issue(issues, section, "", "", "must be an object")
            return issues
        promotions = value.get("promotions", [])
        if not isinstance(promotions, list) or not promotions:
            _issue(issues, section, "promotions", "", "must be a non-empty list")
        seen = set()
        for index, company in enumerate(promotions if isinstance(promotions, list) else []):
            label = str(company.get("name", f"#{index}")) if isinstance(company, dict) else f"#{index}"
            if not isinstance(company, dict):
                _issue(issues, section, label, "", "promotion record must be an object")
                continue
            for field in COMPANY_REQUIRED_FIELDS:
                if company.get(field) in (None, ""):
                    _issue(issues, section, label, field, "is required")
            if company.get("region") not in REGIONS:
                _issue(issues, section, label, "region", "is not a supported region")
            if not _integer(company.get("cash")):
                _issue(issues, section, label, "cash", "must be an integer")
            key = str(company.get("name", "")).casefold()
            if key in seen:
                _issue(issues, section, label, "name", "duplicates another company")
            seen.add(key)
        feeders = value.get("regional_feeders", [])
        if not isinstance(feeders, list):
            _issue(issues, section, "regional_feeders", "", "must be a list")
        else:
            for index, feeder in enumerate(feeders):
                if not isinstance(feeder, dict):
                    _issue(issues, section, f"regional_feeders[{index}]", "", "must be an object")
                elif not feeder.get("name") or feeder.get("region") not in REGIONS:
                    _issue(issues, section, str(feeder.get("name", index)), "region", "needs a name and supported region")
    elif section == "combat_sports":
        if not isinstance(value, dict):
            _issue(issues, section, "", "", "must be an object")
            return issues
        rosters = value.get("rosters", value)
        profiles = value.get("profiles", {})
        divisions = value.get("prime_divisions", {})
        if not isinstance(rosters, dict):
            _issue(issues, section, "rosters", "", "must be an object")
            return issues
        if not isinstance(profiles, dict):
            _issue(issues, section, "profiles", "", "must be an object")
            profiles = {}
        if not isinstance(divisions, dict):
            _issue(issues, section, "prime_divisions", "", "must be an object")
            divisions = {}
        skill_keys = {key for group in DETAILED_SKILL_GROUPS.values() for key in group}
        for sport in COMBAT_SPORTS:
            names = rosters.get(sport)
            if not isinstance(names, list):
                _issue(issues, section, sport, "roster", "must be a list")
                continue
            duplicates = [name for name, count in Counter(names).items() if name and count > 1]
            if duplicates:
                _issue(issues, section, sport, "roster", f"contains duplicate athletes: {', '.join(map(str, duplicates[:10]))}")
            sport_profiles = profiles.get(sport, {})
            if not isinstance(sport_profiles, dict):
                _issue(issues, section, sport, "profiles", "must be an object keyed by athlete name")
                continue
            valid_divisions = {label for ladders in COMBAT_SPORT_WEIGHT_CLASSES.get(sport, {}).values() for label, _ in ladders}
            for name in names:
                profile = sport_profiles.get(name)
                if not isinstance(profile, dict):
                    _issue(issues, section, f"{sport}/{name}", "profile", "is missing or invalid")
                    continue
                for field in ("version", "rating", "prime_age", "record_w", "record_l", "record_d"):
                    _number_in_range(issues, section, f"{sport}/{name}", field, profile.get(field), 0, 999)
                if _integer(profile.get("rating")) and not 1 <= profile["rating"] <= 99:
                    _issue(issues, section, f"{sport}/{name}", "rating", "must be 1-99")
                for field, choices in (("style", STYLES), ("trait", TRAITS), ("behaviour", BEHAVIOURS)):
                    if profile.get(field) not in choices:
                        _issue(issues, section, f"{sport}/{name}", field, "is not a supported value")
                mods = profile.get("skill_mods", {})
                if not isinstance(mods, dict):
                    _issue(issues, section, f"{sport}/{name}", "skill_mods", "must be an object")
                else:
                    unknown = sorted(set(mods) - skill_keys)
                    if unknown:
                        _issue(issues, section, f"{sport}/{name}", "skill_mods", f"contains unknown skills: {', '.join(unknown[:8])}")
            for name, division in (divisions.get(sport, {}) if isinstance(divisions.get(sport, {}), dict) else {}).items():
                if division not in valid_divisions:
                    _issue(issues, section, f"{sport}/{name}", "prime_division", "is not a supported division")
    elif section == "media":
        if not isinstance(value, dict):
            _issue(issues, section, "", "", "must be an object")
            return issues
        broadcasters = value.get("player_broadcasters", [])
        packages = value.get("rights_packages", [])
        if not isinstance(broadcasters, list) or not broadcasters:
            _issue(issues, section, "player_broadcasters", "", "must be a non-empty list")
        if not isinstance(packages, list) or not packages:
            _issue(issues, section, "rights_packages", "", "must be a non-empty list")
        seen = set()
        for index, package in enumerate(packages if isinstance(packages, list) else []):
            label = str(package.get("name", f"#{index}")) if isinstance(package, dict) else f"#{index}"
            if not isinstance(package, dict) or not package.get("name"):
                _issue(issues, section, label, "", "rights package needs a name")
                continue
            key = str(package.get("id", package["name"])).casefold()
            if key in seen:
                _issue(issues, section, label, "id", "duplicates another rights package")
            seen.add(key)
            for field in ("reach", "prestige", "budget", "selectivity", "min_popularity", "min_card_quality", "min_production"):
                if field in package:
                    _number_in_range(issues, section, label, field, package[field], 0, 100)
            fee = package.get("base_fee", package.get("fee", 0))
            if not _integer(fee) or fee < 0:
                _issue(issues, section, label, "base_fee", "must be a non-negative integer")
    elif section == "regions":
        if not isinstance(value, dict) or not value:
            _issue(issues, section, "", "", "must be a non-empty object")
        else:
            missing = set(REGIONS) - set(value)
            if missing:
                _issue(issues, section, "", "", f"is missing regions: {', '.join(sorted(missing))}")
    else:
        _issue(issues, section, "", "", "is not a recognised universe section")
    return issues


def validate_universe_pack_issues(pack):
    """Return every pack issue, never raising for malformed editable JSON."""
    issues = []
    if not isinstance(pack, dict) or pack.get("type") != "universe_database":
        return [UniverseValidationIssue("", "", "type", "is not a universe database pack")]
    sections = pack.get("sections")
    if not isinstance(sections, dict):
        return [UniverseValidationIssue("", "", "sections", "must be an object")]
    company_section = sections.get("companies", {})
    company_names = []
    if isinstance(company_section, dict):
        for row in company_section.get("promotions", []):
            if isinstance(row, dict):
                company_names.extend(value for value in (row.get("name"), row.get("roster_key")) if value)
        company_names.extend(row.get("name") for row in company_section.get("regional_feeders", []) if isinstance(row, dict) and row.get("name"))
    player = company_section.get("player_company", {}) if isinstance(company_section, dict) else {}
    if isinstance(player, dict) and player.get("name"):
        company_names.append(player["name"])
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            _issue(issues, section, "", "", "is missing")
        else:
            issues.extend(validate_universe_section_issues(section, sections[section], company_names=company_names))
    return issues


def validate_universe_pack(pack):
    """Compatibility wrapper returning user-facing strings for UI and CLI callers."""
    return [str(issue) for issue in validate_universe_pack_issues(pack)]


def validate_universe_section(section, value, *, company_names=()):
    return [str(issue) for issue in validate_universe_section_issues(section, value, company_names=company_names)]


def _preflight_row(severity, category, entity, field, evidence, remedy):
    """Build the stable, UI-friendly shape used by editor preflight readers."""
    return {
        "severity": str(severity),
        "category": str(category),
        "entity": str(entity),
        "field": str(field),
        "evidence": str(evidence),
        "remedy": str(remedy),
    }


def _preflight_numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _preflight_title_values(value):
    """Yield (field, holder) pairs from optional authored title structures."""
    if isinstance(value, dict):
        for field, holder in value.items():
            if isinstance(holder, (dict, list, tuple)):
                yield str(field), holder
            elif holder not in (None, "", False):
                yield str(field), holder
    elif isinstance(value, (list, tuple)):
        for index, holder in enumerate(value):
            yield str(index), holder


def _preflight_find_title_references(value, path=()):
    """Find optional belt/title-holder maps without treating ordinary booleans as titles."""
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            normalised = key_text.casefold().replace("-", "_").replace(" ", "_")
            if normalised in {"belts", "titles", "title_holders", "champions", "championships"}:
                yield path + (key_text,), child
            # A title map can be nested in an authored section; recurse so the
            # diagnostic still catches references without knowing every schema.
            yield from _preflight_find_title_references(child, path + (key_text,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _preflight_find_title_references(child, path + (str(index),))


def preflight_universe_pack(pack):
    """Return structural errors and playable-risk warnings without mutating *pack*.

    The ordinary validator remains the save gate.  This richer read model is
    intentionally observational: it reports authored data that is invalid or
    likely to produce a difficult opening, but never deletes a record, appoints
    a champion, signs a replacement or rewrites IDs.
    """
    findings = []
    for issue in validate_universe_pack_issues(pack):
        category = "reference" if any(token in issue.reason.casefold() for token in ("reference", "owner", "duplicate")) else "schema"
        findings.append(_preflight_row(
            "error", category, f"{issue.section}.{issue.record}" if issue.record else issue.section,
            issue.field, issue.reason, "Correct the authored record and run Preflight again.",
        ))
    if not isinstance(pack, dict):
        return findings
    sections = pack.get("sections")
    if not isinstance(sections, dict):
        return findings

    company_section = sections.get("companies", {})
    known_companies = {}
    if isinstance(company_section, dict):
        player = company_section.get("player_company")
        if isinstance(player, dict) and player.get("name"):
            known_companies[str(player["name"]).casefold()] = player
        for row in company_section.get("promotions", []):
            if isinstance(row, dict) and row.get("name"):
                known_companies[str(row["name"]).casefold()] = row
                if row.get("roster_key"):
                    known_companies[str(row["roster_key"]).casefold()] = row
        for row in company_section.get("regional_feeders", []):
            if isinstance(row, dict) and row.get("name"):
                known_companies[str(row["name"]).casefold()] = row

    # Parent-company links are optional, but when authored they must point to
    # a known company.  This is a structural reference error, not a repair job.
    if isinstance(company_section, dict):
        for index, row in enumerate(company_section.get("promotions", [])):
            if not isinstance(row, dict) or not row.get("parent_company"):
                continue
            parent = str(row["parent_company"])
            if parent.casefold() not in known_companies:
                findings.append(_preflight_row(
                    "error", "reference", f"companies.{row.get('name', index)}", "parent_company",
                    f"references unknown company {parent!r}",
                    "Point the child at an existing company or remove the optional parent reference.",
                ))

    fighters_section = sections.get("fighters", {})
    records = fighters_section.get("all_fighters", []) if isinstance(fighters_section, dict) else []
    if not isinstance(records, list):
        records = []
    active_groups = {}
    free_pool = {}
    salaries_by_owner = {}
    salary_fields = ("salary", "weekly_salary", "contract_salary", "annual_salary", "pay")
    for index, fighter in enumerate(records):
        if not isinstance(fighter, dict):
            continue
        owner = str(fighter.get("owner", "")).strip()
        placement = str(fighter.get("placement", "")).casefold()
        weight = str(fighter.get("weight", "")).strip() or "Unknown division"
        gender = str(fighter.get("gender", "")).strip() or "Unknown gender"
        key = (owner, weight, gender)
        is_free = placement in {"free_agent", "free_agents"} or owner.casefold() in {"free agent", "legend", ""}
        if is_free:
            free_pool[(weight, gender)] = free_pool.get((weight, gender), 0) + 1
        elif owner:
            active_groups.setdefault(key, []).append(fighter)
        for field in salary_fields:
            amount = fighter.get(field)
            if _preflight_numeric(amount) and amount > 0 and owner and not is_free:
                salaries_by_owner[owner] = salaries_by_owner.get(owner, 0) + amount
                break

    for (owner, weight, gender), group in sorted(active_groups.items(), key=lambda item: tuple(str(part).casefold() for part in item[0])):
        if len(group) < 2:
            entity = f"company:{owner}"
            findings.append(_preflight_row(
                "warning", "population", entity, f"{weight}/{gender}",
                f"only {len(group)} active fighter is authored in this division",
                "Add or acquire a plausible same-division opponent before booking a normal opening card.",
            ))
            available = free_pool.get((weight, gender), 0)
            if available == 0:
                findings.append(_preflight_row(
                    "warning", "population", entity, "available_talent",
                    f"no free agent is authored for {weight}/{gender}",
                    "Add a matching free agent or accept that this division may require a move-up/down or cancellation.",
                ))

    # Explicit payroll fields are optional in universe packs.  Only compare
    # them when authored, avoiding an invented salary model for older packs.
    if isinstance(company_section, dict):
        company_rows = []
        player = company_section.get("player_company")
        if isinstance(player, dict):
            company_rows.append(player)
        company_rows.extend(row for row in company_section.get("promotions", []) if isinstance(row, dict))
        for row in company_rows:
            display_owner = str(row.get("name", "")).strip()
            aliases = [display_owner, str(row.get("roster_key", "")).strip()]
            owner = next((alias for alias in aliases if alias and alias in salaries_by_owner), "")
            if not owner:
                continue
            cash = row.get("cash")
            if _preflight_numeric(cash) and salaries_by_owner[owner] > cash:
                findings.append(_preflight_row(
                    "warning", "payroll", f"company:{display_owner or owner}", "cash",
                    f"authored fighter payroll {salaries_by_owner[owner]:,.0f} exceeds starting cash {cash:,.0f}",
                    "Raise starting cash, reduce authored compensation, or mark the record as free agency.",
                ))

    # Optional title maps occur only in custom packs.  Resolve by immutable
    # fighter ID first and then exact authored name; current game rankings are
    # deliberately not consulted by this editor diagnostic.
    fighter_ids = {str(row.get("fighter_id")).strip() for row in records if isinstance(row, dict) and str(row.get("fighter_id", "")).strip()}
    fighter_names = {str(row.get("name")).casefold() for row in records if isinstance(row, dict) and str(row.get("name", "")).strip()}
    for path, title_map in _preflight_find_title_references(pack):
        for field, holder in _preflight_title_values(title_map):
            candidate = holder
            if isinstance(holder, dict):
                candidate = holder.get("fighter_id") or holder.get("fighter") or holder.get("name") or holder.get("holder")
            elif isinstance(holder, (list, tuple)):
                # A list may be an authored title row; only inspect the first
                # scalar holder when one is present.
                candidate = next((item for item in holder if isinstance(item, (str, int))), None)
            if candidate in (None, "", False):
                continue
            text = str(candidate).strip()
            if text and text not in fighter_ids and text.casefold() not in fighter_names:
                findings.append(_preflight_row(
                    "error", "reference", ".".join(path), field,
                    f"title holder {text!r} does not resolve to an authored fighter",
                    "Use a saved fighter_id or an exact authored fighter name; do not appoint a replacement during validation.",
                ))
    return findings
