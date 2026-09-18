# Fighter portrait ranks 301–400 review

The fourth reviewed roster slice is the shipped `Default Universe.universe.json`
sorted by rating descending and then name ascending, positions 301–400. It starts
with Michael Venom Page and ends with Alexei Pergande. It deliberately excludes
Maxwell Djantou Nana, who is position 300 and remains in the preceding 201–300
slice.

`fighter_portraits/ranked_300_400.py` supplies 100 explicit, complete cosmetic
vectors. They are display-only and merge after a saved vector without mutating
the save, the roster, gender, ratings or simulation. Each direction uses the
existing source-rendered comic controls—hair silhouette, hair and beard colour,
facial hair, broad face proportions, and bounded facial controls. No new
catalogue IDs, random draws, dependencies or renderer paths were introduced.

The reviewed renders are under `analysis/portraits/top_301_400_2026_09/`:

- `review.html` is the labelled 180px gallery.
- `portraits_72.png`, `portraits_98.png`, `portraits_104.png`, and
  `portraits_180.png` cover the in-game display sizes.
- `identities.json` records the ordered names, IDs and effective identities.

The artwork is an approximate comic interpretation of the real athletes, not a
photograph or a guarantee of perceptual likeness. At 72px, small facial changes
can look alike; the review uses hair, beard, face outline and colour as the
strongest readable cues. Tattoos, scars, exact age, historical era and fine
facial detail remain outside its scope.

Regenerate the review set from the repository root:

```powershell
py -3 analysis/portraits/generate_portrait_contact_sheet.py --review-set top-rated --offset 300 --count 100 --columns 10 --cell 180 --out analysis/portraits/top_301_400_2026_09/portraits_180.png --manifest analysis/portraits/top_301_400_2026_09/identities.json --html analysis/portraits/top_301_400_2026_09/review.html
```

The portrait regression suite checks membership, trait ranges, non-mutating
saved-vector behaviour, source-rendered contact-sheet pixels at all four sizes,
and the labelled gallery payload. It also retains a manifest hash for everyone
outside the reviewed cohorts.
