import json
from pathlib import Path
import numpy as np
import portrait_comic2 as pc

# Tier-1 authored override. Only what matters is specified.
# Braided rainbow is his signature since UFC 250 (2020).
OMALLEY = {"skin": 0, "hair_style": pc.HAIR_STYLES.index(next(s for s in pc.HAIR_STYLES if s[0]=="cornrows")),
           "dye": "rainbow", "beard": 4, "jaw": 1, "chin": 1, "cheek": 2,
           "head_w": 20, "brow": 1, "nose": 0, "bg": 4}

u = json.loads(Path("Databases/Default Universe.universe.json").read_text(encoding="utf-8"))
rows=[]
def walk(o):
    if isinstance(o,dict):
        if o.get("fighter_id") and o.get("name"): rows.append(o)
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(u)
f = next(r for r in rows if r["name"]=="Sean O'Malley")

variants = [
    ("cornrows / rainbow", dict(OMALLEY)),
    ("braided_back / sunset", dict(OMALLEY, hair_style=[i for i,s in enumerate(pc.HAIR_STYLES) if s[0]=="braided_back"][0], dye="sunset")),
    ("cornrows / ecuador", dict(OMALLEY, dye="ecuador")),
    ("man_bun / rainbow", dict(OMALLEY, hair_style=[i for i,s in enumerate(pc.HAIR_STYLES) if s[0]=="man_bun"][0])),
    ("curly_mop / natural", dict(OMALLEY, hair_style=[i for i,s in enumerate(pc.HAIR_STYLES) if s[0]=="curly_mop"][0], dye=None, hair_colour=2)),
    ("mohawk / toxic", dict(OMALLEY, hair_style=[i for i,s in enumerate(pc.HAIR_STYLES) if s[0]=="mohawk"][0], dye="toxic")),
]
S,gap = pc.S,12
cols=3; rowsn=2
sheet=np.zeros((rowsn*(S+gap)+gap, cols*(S+gap)+gap,3),np.uint8); sheet[:]=22
for i,(label,ov) in enumerate(variants):
    ov = {k:v for k,v in ov.items() if v is not None}
    r,c = divmod(i,cols)
    sheet[gap+r*(S+gap):gap+r*(S+gap)+S, gap+c*(S+gap):gap+c*(S+gap)+S] = pc.render(dict(f, _override=ov))
    print(f"  {i+1}. {label}")
pc.write_png("omalley_hair.png", sheet)
print("wrote omalley_hair.png")
