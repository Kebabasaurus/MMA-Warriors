import argparse
import gc
import gzip
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from constants import DETAILED_SKILL_GROUPS, GAME_START_YEAR


def read_save(path):
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def group_average(row, group):
    skills = row.get("detailed_skills") or {}
    keys = DETAILED_SKILL_GROUPS[group]
    return round(sum(int(skills.get(key, 50) or 50) for key in keys) / len(keys))


def overall(row):
    core = [int(row.get(key, 50) or 50) for key in ("striking", "wrestling", "grappling", "cardio", "chin")]
    if row.get("detailed_skills"):
        return round((sum(core) + group_average(row, "Mental") + group_average(row, "Physical")) / 7)
    return round(sum(core) / 5)


def percentile(values, fraction):
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def rating_band(value):
    if value < 50:
        return "<50"
    if value < 60:
        return "50-59"
    if value < 70:
        return "60-69"
    if value < 75:
        return "70-74"
    if value < 80:
        return "75-79"
    if value < 85:
        return "80-84"
    if value < 90:
        return "85-89"
    if value < 95:
        return "90-94"
    return "95+"


def source_group(row):
    origin = str(row.get("feeder_origin", "") or "").lower()
    if "academy" in origin:
        return "Academy"
    if any(token in origin for token in ("regional", "circuit", "league", "championship")):
        return "Regional pathway"
    if origin:
        return "Other recorded origin"
    return "No recorded origin"


def analyze(path):
    data = read_save(path)
    month = int(data.get("month", 1) or 1)
    week = int(data.get("week", 1) or 1)
    year = GAME_START_YEAR + (month - 1) // 12
    calendar_month = (month - 1) % 12 + 1
    rows = [row for row in data.get("free_agents", []) if not row.get("retired", False)]
    values = [overall(row) for row in rows]
    ages = [int(row.get("age", 0) or 0) for row in rows]
    potentials = [int(row.get("potential", overall(row)) or overall(row)) for row in rows]
    unsigned = [max(0, int(row.get("free_agent_months", 0) or 0)) for row in rows]
    bands = Counter(rating_band(value) for value in values)
    source = Counter(source_group(row) for row in rows)
    entry_months = Counter(int(row.get("universe_entry_month", 0) or 0) for row in rows if row.get("generated", False))
    originless_entries = Counter(
        int(row.get("universe_entry_month", 0) or 0)
        for row in rows
        if row.get("generated", False) and source_group(row) == "No recorded origin"
    )
    gender = Counter(str(row.get("gender", "Unknown") or "Unknown") for row in rows)
    generated = sum(bool(row.get("generated", False)) for row in rows)
    current_week = (month - 1) * 4 + week
    market_available = sum(
        not row.get("injured", 0)
        and not row.get("retirement_pending", False)
        and not row.get("ai_offer_company", "")
        for row in rows
    )
    unavailable_reasons = Counter()
    for row in rows:
        if row.get("retirement_pending", False):
            unavailable_reasons["retirement pending"] += 1
        if row.get("injured", 0):
            unavailable_reasons["injured"] += 1
        if row.get("ai_offer_company", ""):
            unavailable_reasons["AI offer live"] += 1
        if int(row.get("fatigue", 0) or 0) >= 70:
            unavailable_reasons["high fatigue"] += 1
        if int(row.get("available_week", 0) or 0) > current_week:
            unavailable_reasons["recovery cooldown"] += 1
    available = sum(
        not row.get("injured", 0)
        and int(row.get("fatigue", 0) or 0) < 70
        and int(row.get("available_week", 0) or 0) <= current_week
        and not row.get("retirement_pending", False)
        for row in rows
    )
    young_quality = Counter()
    age_bands = Counter()
    division_values = {}
    for row, value in zip(rows, values):
        age = int(row.get("age", 0) or 0)
        age_label = "U21" if age <= 20 else "21-25" if age <= 25 else "26-30" if age <= 30 else "31-35" if age <= 35 else "36-40" if age <= 40 else "41+"
        age_bands[age_label] += 1
        division_values.setdefault((row.get("gender", "Unknown"), row.get("weight", "Unknown")), []).append(value)
        if age <= 23 and value >= 70:
            young_quality["U24 70+"] += 1
        if age <= 25 and value >= 80:
            young_quality["U26 80+"] += 1
        if age <= 29 and value >= 85:
            young_quality["U30 85+"] += 1
    top = sorted(
        ((overall(row), int(row.get("potential", 0) or 0), int(row.get("age", 0) or 0),
          int(row.get("free_agent_months", 0) or 0), row.get("name", "Unknown"),
          row.get("gender", "?"), row.get("weight", "?"), source_group(row)) for row in rows),
        reverse=True,
    )[:15]
    identities = {
        str(row.get("fighter_id") or f"NAME:{row.get('name', 'Unknown')}"): {
            "name": row.get("name", "Unknown"), "overall": overall(row),
            "age": int(row.get("age", 0) or 0), "months": int(row.get("free_agent_months", 0) or 0),
        }
        for row in rows
    }
    contracted_rows = list(data.get("roster", []))
    for promo in data.get("promotions", []):
        if promo.get("is_regional_feeder", False):
            continue
        contracted_rows.extend(promo.get("roster", []))
    contracted_values = [overall(row) for row in contracted_rows if not row.get("retired", False)]
    contracted = len(contracted_values)
    result = {
        "path": str(path), "label": path.parent.parent.name + " / " + path.name if path.parent.name == "Snapshots" else path.parent.name + " / " + path.name,
        "month": month, "week": week, "date": f"{year}-{calendar_month:02d} W{week}",
        "count": len(rows), "available": available, "market_available": market_available,
        "unavailable_reasons": unavailable_reasons, "contracted": contracted,
        "mean": statistics.mean(values) if values else 0, "median": statistics.median(values) if values else 0,
        "p10": percentile(values, .10), "p90": percentile(values, .90), "max": max(values, default=0),
        "age_mean": statistics.mean(ages) if ages else 0, "age_median": statistics.median(ages) if ages else 0,
        "potential_mean": statistics.mean(potentials) if potentials else 0,
        "unsigned_mean": statistics.mean(unsigned) if unsigned else 0, "unsigned_median": statistics.median(unsigned) if unsigned else 0,
        "unsigned_12": sum(value >= 12 for value in unsigned), "unsigned_24": sum(value >= 24 for value in unsigned),
        "unsigned_60": sum(value >= 60 for value in unsigned),
        "generated": generated, "real": len(rows) - generated, "bands": bands, "source": source,
        "entry_months": entry_months, "originless_entries": originless_entries,
        "gender": gender, "young_quality": young_quality, "age_bands": age_bands,
        "divisions": {key: (len(group), statistics.mean(group), max(group)) for key, group in division_values.items()},
        "contracted_mean": statistics.mean(contracted_values) if contracted_values else 0,
        "contracted_max": max(contracted_values, default=0),
        "contracted_80": sum(value >= 80 for value in contracted_values),
        "contracted_90": sum(value >= 90 for value in contracted_values),
        "contracted_95": sum(value >= 95 for value in contracted_values),
        "top": top, "identities": identities,
    }
    del data, rows
    gc.collect()
    return result


def comparison(previous, current):
    before = previous["identities"]
    after = current["identities"]
    retained_ids = before.keys() & after.keys()
    joined_ids = after.keys() - before.keys()
    left_ids = before.keys() - after.keys()
    retained_change = [after[key]["overall"] - before[key]["overall"] for key in retained_ids]
    joined_values = [after[key]["overall"] for key in joined_ids]
    left_values = [before[key]["overall"] for key in left_ids]
    return {
        "retained": len(retained_ids), "joined": len(joined_ids), "left": len(left_ids),
        "retained_change": statistics.mean(retained_change) if retained_change else 0,
        "joined_mean": statistics.mean(joined_values) if joined_values else 0,
        "left_mean": statistics.mean(left_values) if left_values else 0,
        "joined_80": sum(value >= 80 for value in joined_values), "left_80": sum(value >= 80 for value in left_values),
    }


def render(results):
    lines = ["MMA WARRIORS - FREE AGENT SNAPSHOT AUDIT", ""]
    order = ("<50", "50-59", "60-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95+")
    for result in results:
        lines.extend([
            f"{result['label']} | {result['date']} | internal month {result['month']}",
            f"Free agents: {result['count']} ({result['market_available']} market-available; {result['available']} fight-ready) | Contracted MMA fighters: {result['contracted']}",
            "Unavailable flags: " + " | ".join(f"{key} {value}" for key, value in result["unavailable_reasons"].most_common()),
            f"OVR mean/median: {result['mean']:.1f}/{result['median']:.1f} | P10/P90: {result['p10']}/{result['p90']} | Maximum: {result['max']} | Potential mean: {result['potential_mean']:.1f}",
            f"Contracted OVR: mean {result['contracted_mean']:.1f} | maximum {result['contracted_max']} | 80+ {result['contracted_80']} | 90+ {result['contracted_90']} | 95+ {result['contracted_95']}",
            f"OVR bands: " + " | ".join(f"{key} {result['bands'][key]}" for key in order),
            f"Age mean/median: {result['age_mean']:.1f}/{result['age_median']:.1f} | Generated/real: {result['generated']}/{result['real']} | Gender: " + ", ".join(f"{key} {value}" for key, value in result['gender'].most_common()),
            "Age bands: " + " | ".join(f"{key} {result['age_bands'][key]}" for key in ("U21", "21-25", "26-30", "31-35", "36-40", "41+")),
            f"Unsigned months mean/median: {result['unsigned_mean']:.1f}/{result['unsigned_median']:.1f} | 12m+ {result['unsigned_12']} | 24m+ {result['unsigned_24']} | 60m+ {result['unsigned_60']}",
            "Sources: " + " | ".join(f"{key} {value}" for key, value in result['source'].most_common()),
            "Generated entry months: " + " | ".join(f"M{key} {value}" for key, value in result["entry_months"].most_common(12)),
            "Originless entry months: " + " | ".join(f"M{key} {value}" for key, value in result["originless_entries"].most_common(12)),
            "Young quality: " + " | ".join(f"{key} {result['young_quality'][key]}" for key in ("U24 70+", "U26 80+", "U30 85+")),
            "Top free agents:",
        ])
        for value, potential, age, months, name, gender, weight, source in result["top"]:
            lines.append(f"  {name} | {gender} {weight} | OVR {value} POT {potential} | age {age} | unsigned {months}m | {source}")
        lines.append("Free-agent divisions (count / mean / max):")
        for (gender_name, weight), (count, mean_value, max_value) in sorted(result["divisions"].items()):
            lines.append(f"  {gender_name} {weight}: {count} / {mean_value:.1f} / {max_value}")
        lines.append("")
    if len(results) > 1:
        lines.append("SNAPSHOT FLOW")
        for previous, current in zip(results, results[1:]):
            flow = comparison(previous, current)
            lines.append(
                f"{previous['date']} -> {current['date']}: retained {flow['retained']} | entered {flow['joined']} (mean {flow['joined_mean']:.1f}, 80+ {flow['joined_80']}) | "
                f"left {flow['left']} (mean {flow['left_mean']:.1f}, 80+ {flow['left_80']}) | retained OVR change {flow['retained_change']:+.1f}"
            )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()
    results = [analyze(Path(value)) for value in args.paths]
    results.sort(key=lambda item: (item["month"], item["week"], item["path"]))
    report = render(results)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
