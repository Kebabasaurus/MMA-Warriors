"""Build a 100-fighter portrait contact sheet without runtime dependencies.

Run from the repository root, for example:
``py -3 analysis/portraits/generate_portrait_contact_sheet.py``.
The generated PNG is a development artifact and is not shipped by the game.
"""

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fighter_portraits.render import rasterize_portrait
from fighter_portraits.identity import portrait_identity
from fighter_portraits.overrides import PORTRAIT_OVERRIDES

DEFAULT_SOURCE = ROOT / "Databases" / "Default Universe.universe.json"
DEFAULT_OUTPUT = ROOT / "analysis" / "portraits" / "portrait_contact_sheet.png"


def png_bytes(width, height, pixels):
    raw = b"".join(
        b"\0" + bytes(max(0, min(255, round(channel))) for pixel in pixels[row * width:(row + 1) * width] for channel in pixel)
        for row in range(height)
    )
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def select_records(records, gender="", region="", review_set="all", style=None, names=()):
    """Select a reproducible visual-review cohort without changing game data."""
    selected = list(records)
    if gender:
        selected = [row for row in selected if str(row.get("gender", "")) == gender]
    if region:
        selected = [row for row in selected if str(row.get("region", "")) == region]
    if review_set == "overrides":
        selected = [row for row in selected if row.get("name") in PORTRAIT_OVERRIDES]
    elif review_set == "veterans":
        selected = [row for row in selected if int(row.get("age", 0) or 0) >= 35]
    elif review_set == "women":
        selected = [row for row in selected if row.get("gender") == "Female"]
    if style is not None:
        selected = [row for row in selected if portrait_identity(SimpleNamespace(**row))["hair_style"] == style]
    if names:
        requested = set(names)
        selected = [row for row in selected if row.get("name") in requested]
    return sorted(selected, key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("fighter_id", ""))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--cell", type=int, default=90)
    parser.add_argument("--columns", type=int, default=10)
    parser.add_argument("--gender", choices=("Male", "Female"))
    parser.add_argument("--region")
    parser.add_argument("--review-set", choices=("all", "overrides", "veterans", "women"), default="all")
    parser.add_argument("--style", type=int, choices=range(32))
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--manifest", type=Path, help="Optional JSON metadata beside a review image.")
    args = parser.parse_args()
    records = json.loads(args.source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
    records = select_records(records, args.gender or "", args.region or "", args.review_set, args.style, args.name)[:max(1, args.count)]
    if not records:
        raise SystemExit("No fighters matched the requested contact-sheet cohort.")
    columns = max(1, args.columns)
    rows = (len(records) + columns - 1) // columns
    width, height = columns * args.cell, rows * args.cell
    background = (18, 20, 26)
    pixels = [background] * (width * height)
    for index, record in enumerate(records):
        image = rasterize_portrait(SimpleNamespace(**record), args.cell).pixels
        ox, oy = (index % columns) * args.cell, (index // columns) * args.cell
        for y in range(args.cell):
            target = (oy + y) * width + ox
            pixels[target:target + args.cell] = image[y * args.cell:(y + 1) * args.cell]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(png_bytes(width, height, pixels))
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps([
            {"name": row.get("name"), "fighter_id": row.get("fighter_id"), "gender": row.get("gender"),
             "age": row.get("age"), "region": row.get("region"), "identity": portrait_identity(SimpleNamespace(**row))}
            for row in records
        ], indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} portraits to {args.out}")


if __name__ == "__main__":
    main()
