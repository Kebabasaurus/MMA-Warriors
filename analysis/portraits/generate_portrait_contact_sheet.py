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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--cell", type=int, default=90)
    args = parser.parse_args()
    records = json.loads(args.source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"][:max(1, args.count)]
    columns = 10
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
    print(f"Wrote {len(records)} portraits to {args.out}")


if __name__ == "__main__":
    main()
