# Current-source portrait review — 18 September 2026

The registered portrait regression now binds its exact-pixel and labelled-gallery
checks to the current renderer and authored identity layers. The earlier September
review directories remain retained evidence; they were not overwritten.

Current review sets:

- `analysis/portraits/top_51_100_current_2026_09_18/`
- `analysis/portraits/top_101_200_current_2026_09_18/`
- `analysis/portraits/top_201_300_current_2026_09_18/`
- `analysis/portraits/top_301_400_current_2026_09_18/`

Each directory contains source-rendered 72, 98, 104 and 180 pixel contact sheets,
a labelled self-contained 180 pixel review page and the effective identity
manifest. They were generated from the shipped default universe with the current
ranked vectors, authored styles, signature marks, scalp finishes and tattoo layer.
The four 180 pixel sheets were visually inspected for complete grid rendering,
bounded silhouettes, skin/hair/background presentation and missing/corrupt cells.
No blocking render fault was observed; this is a presentation QA statement, not a
claim of photographic likeness.

The current Conor McGregor regression follows the later accepted authored-style
contract (`hair_style` 156 and its associated facial-hair/beard direction), which
supersedes the older named-correction snapshot. Existing source guides remain as
historical design evidence rather than being rewritten.

Regenerate one cohort by substituting its offset/count and all four cell sizes:

```powershell
py -3.13 analysis/portraits/generate_portrait_contact_sheet.py --review-set top-rated --offset 50 --count 50 --columns 10 --cell 180 --out analysis/portraits/top_51_100_current_2026_09_18/portraits_180.png --manifest analysis/portraits/top_51_100_current_2026_09_18/identities.json --html analysis/portraits/top_51_100_current_2026_09_18/review.html
```

Regeneration is an intentional source-bound review action. Do not overwrite the
older directories or refresh expected hashes merely to conceal a regression.
