"""Build a 100-fighter portrait contact sheet without runtime dependencies.

Run from the repository root, for example:
``py -3 analysis/portraits/generate_portrait_contact_sheet.py``.
The generated PNG is a development artifact and is not shipped by the game.
"""

import argparse
import base64
import html
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
from fighter_portraits.styles import HAIR_STYLES

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
    elif review_set == "top-rated":
        # Keep ranking order for the most valuable likeness review; alphabetical
        # sheets are useful for broad catalogues, not a top-fighter audit.
        selected = sorted(selected, key=lambda row: (-int(row.get("rating", 0) or 0), str(row.get("name", ""))))
    if style is not None:
        selected = [row for row in selected if portrait_identity(SimpleNamespace(**row))["hair_style"] == style]
    if names:
        requested = set(names)
        selected = [row for row in selected if row.get("name") in requested]
    if review_set == "top-rated":
        return selected
    return sorted(selected, key=lambda row: (str(row.get("name", "")).casefold(), str(row.get("fighter_id", ""))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0, help="Skip this many selected records (e.g. 50 for ranks 51--100).")
    parser.add_argument("--cell", type=int, default=90)
    parser.add_argument("--columns", type=int, default=10)
    parser.add_argument("--gender", choices=("Male", "Female"))
    parser.add_argument("--region")
    parser.add_argument("--review-set", choices=("all", "overrides", "veterans", "women", "top-rated"), default="all")
    parser.add_argument("--style", type=int, choices=range(len(HAIR_STYLES)))
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--manifest", type=Path, help="Optional JSON metadata beside a review image.")
    parser.add_argument("--html", type=Path, help="Optional self-contained labelled portrait review page.")
    args = parser.parse_args()
    records = json.loads(args.source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
    offset = max(0, args.offset)
    records = select_records(records, args.gender or "", args.region or "", args.review_set, args.style, args.name)[offset:offset + max(1, args.count)]
    if not records:
        raise SystemExit("No fighters matched the requested contact-sheet cohort.")
    columns = max(1, args.columns)
    rows = (len(records) + columns - 1) // columns
    width, height = columns * args.cell, rows * args.cell
    background = (18, 20, 26)
    pixels = [background] * (width * height)
    cards = []
    for index, record in enumerate(records):
        image = rasterize_portrait(SimpleNamespace(**record), args.cell).pixels
        if args.html:
            encoded = base64.b64encode(png_bytes(args.cell, args.cell, image)).decode("ascii")
            name = html.escape(str(record.get("name", "")))
            cards.append(f'<figure><img width="{args.cell}" height="{args.cell}" alt="{name}" '
                         f'src="data:image/png;base64,{encoded}"><figcaption>{offset+index+1}. {name}</figcaption></figure>')
        ox, oy = (index % columns) * args.cell, (index // columns) * args.cell
        for y in range(args.cell):
            target = (oy + y) * width + ox
            pixels[target:target + args.cell] = image[y * args.cell:(y + 1) * args.cell]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(png_bytes(width, height, pixels))
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
                            '<meta name="viewport" content="width=device-width,initial-scale=1">'
                            '<title>MMA Warriors portrait review</title><style>'
                            'body{background:#12141a;color:#f1eee8;font:16px system-ui;margin:24px}'
                            'main{display:flex;flex-wrap:wrap;gap:16px}figure{margin:0;max-width:180px}'
                            'figcaption{padding:8px 0;font-size:13px}img{max-width:100%;height:auto}'
                            '</style><h1>MMA Warriors portrait review</h1>'
                            '<p>Source-rendered comic portraits. Labels follow the selected cohort order; '
                            'top-rated uses rating descending, then name. Likeness is approximate.</p>'
                            '<main>' + ''.join(cards) + '</main></html>', encoding="utf-8")
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps([
            {"name": row.get("name"), "fighter_id": row.get("fighter_id"), "rating": row.get("rating"),
             "gender": row.get("gender"), "age": row.get("age"), "region": row.get("region"),
             "identity": portrait_identity(SimpleNamespace(**row))}
            for row in records
        ], indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} portraits to {args.out}")


if __name__ == "__main__":
    main()
