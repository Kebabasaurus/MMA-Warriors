# Rating positions 201–300 portrait review

This third ranked portrait cohort is selected from the shipped database by rating
descending and name ascending, positions 201–300. It adds 100 complete, display-only
vectors in `fighter_portraits/ranked_201_300.py`; the first entry is Brad Pickett and
the last is Maxwell Djantou Nana.

## Reference and scope

The directions use current promotional/profile photos where available for hair,
facial hair, skin palette, broad face proportions and visible eye colour. Official
fighter pages and promotion headshots are the preferred source; useful references
include [UFC athlete profiles](https://www.ufc.com/athletes/all),
[PFL fighter profiles](https://pflmma.com/fighters),
[ONE athlete profiles](https://www.onefc.com/athletes/), and published fighter
headshots for less widely covered roster members. For example, the review used the
current profile portraits for [Eldar Eldarov](https://fightersonly.com/article/ext/6747/Issue%2B161/1),
[Magomed Zaynukov](https://www.espn.com/mma/fighter/_/id/5311034/magomed-zaynukov),
[Razhab Shaydullaev](https://www.onefc.com/id/athletes/razhab-shaydullaev/) and
[Ustarmagomed Gadzhidaudov](https://aca-mma.com/en/fighters/ustarmagomed-gadzhidaudov-667_629).

No external photos are downloaded, copied into the repository or included in the
game. The result remains an angular comic interpretation, not a photographic or
biometric likeness. Tattoos, scars, precise historical hair eras and exact facial
geometry are deliberately out of scope. A later review may refine any direction.

Six women (plus the separate Liz Carmouche archive record) retain the renderer's
female presentation and final no-facial-hair guard. All entries author every identity
trait except the existing background and include `beard_colour`; the vectors merge for
display after a saved identity, so existing saves are never rewritten. They do not
change ratings, gender/division data, combat logic, RNG or generated portrait pools.

## Labelled visual review

The generated gallery is [review.html](../analysis/portraits/top_201_300_2026_09/review.html).
It contains runtime-rendered, labelled 180px comic portraits in rank order. Matching
72, 98 and 104px sheets and `identities.json` live alongside it. Inspecting all four
sizes matters: small changes that look distinct at 180px can collapse at a roster
thumbnail.

Regenerate the review with:

```powershell
py -3 analysis/portraits/generate_portrait_contact_sheet.py --review-set top-rated --offset 200 --count 100 --columns 10 --cell 180 --out analysis/portraits/top_201_300_2026_09/portraits_180.png --manifest analysis/portraits/top_201_300_2026_09/identities.json --html analysis/portraits/top_201_300_2026_09/review.html
```

Repeat with cells 72, 98 and 104 to refresh the remaining sheets.

## Verification

`fighter_portrait_regression_test.py` locks the exact cohort membership, complete
authored-vector bounds, non-mutating save behaviour, the combined reviewed-cohort
identity guard and the source-rendered sheets at all four UI sizes. The review is
cosmetic only; it does not require fight-calibration work or a rebuilt executable.
