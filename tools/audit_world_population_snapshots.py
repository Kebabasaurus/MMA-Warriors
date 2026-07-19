import argparse
import gc
import gzip
import json
import statistics
from pathlib import Path


def read_save(path):
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def active_count(rows):
    return sum(not row.get("retired", False) for row in rows)


def analyze(path):
    data = read_save(path)
    promotions = data.get("promotions", [])
    majors = [promo for promo in promotions if not promo.get("is_regional_feeder", False)]
    regionals = [promo for promo in promotions if promo.get("is_regional_feeder", False)]
    major_rows = [(promo.get("name", "Unknown"), active_count(promo.get("roster", []))) for promo in majors]
    regional_rows = [(promo.get("name", "Unknown"), active_count(promo.get("roster", []))) for promo in regionals]
    player = active_count(data.get("roster", []))
    free_agents = active_count(data.get("free_agents", []))
    major_total = sum(count for _name, count in major_rows)
    regional_total = sum(count for _name, count in regional_rows)
    result = {
        "path": path,
        "month": int(data.get("month", 1) or 1),
        "player": player,
        "free_agents": free_agents,
        "major_total": major_total,
        "major_rows": major_rows,
        "regional_total": regional_total,
        "regional_rows": regional_rows,
        "total": player + free_agents + major_total + regional_total,
    }
    del data
    gc.collect()
    return result


def describe(rows):
    counts = [count for _name, count in rows]
    return f"{sum(counts)} across {len(counts)} (median {statistics.median(counts):.0f}, min {min(counts)}, max {max(counts)})"


def render(results):
    lines = ["MMA WARRIORS - REAL SAVE POPULATION SNAPSHOT AUDIT", ""]
    for row in sorted(results, key=lambda item: item["month"]):
        lines.extend([
            f"{row['path'].name} | internal month {row['month']}",
            f"Total active: {row['total']} | Player: {row['player']} | Free agents: {row['free_agents']}",
            f"Major rosters: {describe(row['major_rows'])}",
            f"Regional rosters: {describe(row['regional_rows'])}",
            "Smallest majors: " + " | ".join(f"{name} {count}" for name, count in sorted(row["major_rows"], key=lambda item: item[1])[:6]),
            "Largest majors: " + " | ".join(f"{name} {count}" for name, count in sorted(row["major_rows"], key=lambda item: item[1], reverse=True)[:6]),
            "",
        ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = render([analyze(path) for path in args.paths])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
