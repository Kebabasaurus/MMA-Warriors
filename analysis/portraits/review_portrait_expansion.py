"""V3 catalogue review: run from the repository root, stdlib only.

Produces numbered-in-manifest contact sheets, never changes fighters/saves.
Every sheet uses fixed face/colour controls so background changes cannot be
mistaken for silhouette diversity. Anatomical sheets vary one trait at a time.
"""

import hashlib
import json
from pathlib import Path
import sys
from time import process_time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analysis.portraits.review_portrait_diversity import fighter, sheet
from fighter_portraits.identity import portrait_identity
from fighter_portraits.styles import FEATURE_COUNTS, HAIR_STYLES, FACIAL_HAIR


def main():
    out = ROOT / "analysis/portraits/expansion_v3"
    out.mkdir(exist_ok=True)
    base = {key: 4 for key in FEATURE_COUNTS}
    base.update(head_w=45, skin=2, hair_colour=1, hair_style=0, facial_hair=0,
                bg=0, dye="", complexion=0, eye_size=1, jaw=2, chin=1, face_length=1)
    manifest = {"layout": "Left to right, ten columns; zero-based IDs recorded below.", "sheets": {}}
    start = process_time()
    for gender in ("Male", "Female"):
        hair_start = 48 if gender == "Male" else 98
        ids = list(range(hair_start, hair_start+50))
        rows = [fighter("expansion-fixed", "UK", gender, **dict(base, hair_style=i)) for i in ids]
        filename = f"{gender.lower()}_hair.png"
        sheet(rows, out/filename, cell=180, columns=10)
        manifest["sheets"][filename] = [{"id": i, "name": HAIR_STYLES[i][0]} for i in ids]
        sheet(rows, out/f"{gender.lower()}_hair_72.png", cell=72, columns=10)
        # Each row is one feature at ten evenly spaced new presets.
        traits = ("brow", "eye_shape", "eye_spacing", "eye_size", "nose", "mouth",
                  "jaw", "chin", "cheek", "face_length", "ear", "complexion")
        face_base = dict(base, hair_style=32 if gender == "Female" else 0)
        rows = [fighter("expansion-fixed", "UK", gender, **dict(face_base, **{trait:i}))
                for trait in traits for i in range(10, 60, 5)]
        filename = f"{gender.lower()}_features.png"
        sheet(rows, out/filename, cell=104, columns=10)
        manifest["sheets"][filename] = [{"trait": t, "id": i} for t in traits for i in range(10,60,5)]
        # Generated diversity under fixed colour choices, plus real country priors.
        rows = [fighter(f"expansion-{gender}-{i}", "UK", gender, skin=2,hair_colour=1,bg=0) for i in range(40)]
        sheet(rows,out/f"{gender.lower()}_same_colours.png", cell=104,columns=10)
        manifest["sheets"][f"{gender.lower()}_same_colours.png"] = [portrait_identity(r) for r in rows]
        rows = [fighter(f"expansion-{gender}-{country}-{i}",country,gender)
                for country in ("UK","Nigeria","Japan","Brazil","India","Mexico") for i in range(10)]
        sheet(rows,out/f"{gender.lower()}_countries.png",cell=104,columns=10)
        manifest["sheets"][f"{gender.lower()}_countries.png"] = [dict(country=r.birth_country,identity=portrait_identity(r)) for r in rows]
    rows = [fighter("expansion-fixed","UK","Male",**dict(base,facial_hair=i)) for i in range(16,66)]
    sheet(rows,out/"beards.png",cell=180,columns=10)
    manifest["sheets"]["beards.png"] = [{"id":i,"name":FACIAL_HAIR[i]} for i in range(16,66)]
    manifest["source_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((ROOT/"fighter_portraits").glob("*.py"))}
    manifest["feature_counts"] = FEATURE_COUNTS
    manifest["generation_cpu_seconds"] = process_time()-start
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(out),"cpu_seconds":manifest["generation_cpu_seconds"]}))


if __name__ == "__main__":
    main()
