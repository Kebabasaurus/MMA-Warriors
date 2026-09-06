"""Reproducible synthetic cohorts for visual QA, not demographic evidence.

Rows in the country sheets: UK, Nigeria, Japan, Brazil, India, Mexico.
The hairstyle sheet runs IDs 0 through 47 left to right, eight per row.
"""

import hashlib
import json
from pathlib import Path
import sys
from statistics import median
from time import process_time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from fighter_portraits.identity import portrait_identity
from fighter_portraits.render import rasterize_portrait
from fighter_portraits.styles import HAIR_STYLES
from analysis.portraits.generate_portrait_contact_sheet import png_bytes


def fighter(fid, country, gender, **traits):
    return SimpleNamespace(fighter_id=fid, name="Generated review", gender=gender,
                           birth_country=country, nationality=country, region="",
                           age=27, record_w=3, record_l=1, record_d=0,
                           portrait_identity=traits)


def sheet(rows, path, cell=104, columns=8):
    width = columns * cell
    height = ((len(rows)+columns-1)//columns)*cell
    pixels = [(18,20,26)]*(width*height)
    for index, row in enumerate(rows):
        image = rasterize_portrait(row,cell)
        ox,oy = (index%columns)*cell,(index//columns)*cell
        for y in range(cell):
            start = (oy+y)*width+ox
            pixels[start:start+cell] = image.pixels[y*cell:(y+1)*cell]
    path.write_bytes(png_bytes(width,height,pixels))


def main():
    out = ROOT / "analysis" / "portraits" / "diversity_v2"
    out.mkdir(exist_ok=True)
    manifest = {}
    for gender in ("Female", "Male"):
        rows = [fighter(f"review-{country}-{gender}-{i}",country,gender)
                for country in ("UK", "Nigeria", "Japan", "Brazil", "India", "Mexico") for i in range(8)]
        sheet(rows,out/f"{gender.lower()}_countries.png")
        manifest[gender] = [dict(name=r.name, id=r.fighter_id, country=r.birth_country,
                                 traits=portrait_identity(r)) for r in rows]
    styles = [fighter("review-style", "UK", "Female", hair_style=i, hair_colour=1, skin=1,
                      facial_hair=0, bg=0) for i in range(len(HAIR_STYLES))]
    sheet(styles,out/"hair_styles.png")
    # Same age/country/skin/hair colour/background: test visible shape diversity
    # without counting a background recolour as a different face.
    shapes = [fighter(f"review-shape-{i}","UK","Male",skin=2,hair_colour=1,bg=0) for i in range(48)]
    sheet(shapes,out/"same_colours.png")
    timing = {}
    for size in (72,98,104,180):
        durations = []
        for row in shapes[:8]:
            start = process_time()
            rasterize_portrait(row,size)
            durations.append((process_time()-start)*1000)
        timing[size] = {"median_ms": median(durations), "max_ms":max(durations)}
    manifest["render_cpu"] = timing
    manifest["sources"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted((ROOT/"fighter_portraits").glob("*.py"))}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(out),"cold_render_cpu":timing},indent=2))


if __name__ == "__main__":
    main()
