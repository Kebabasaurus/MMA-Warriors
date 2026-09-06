# Portrait diversity revision — 6 September 2026

This revision addresses generated women sharing the men's head/body construction,
weak country colour weighting, and hair/beard styles collapsing into similar masks.
It changes presentation only; it does not rebalance fights or edit fighter ratings.

## Visible changes

- Gender-normalised rendering: women's jaw/chin, neck/shoulder proportions, brows,
  softer face planes and athletic singlet. Female portraits suppress facial hair
  even when an older saved vector contains it. Women now generate from their own
  explicit 27-style catalogue, rather than having a chance of every men's cut.
- 48 stable hairstyle IDs (16 appended): bobs, pixie/fringes, centre/curtain parts,
  twin braids, double/low buns, curly puff/taper, tied locs, braided ponytail, shag,
  and mullet. Rounded crowns, tapered side locks, curl outlines and separate tails
  replace the shared block-like cap construction.
- 16 facial-hair options with distinct rendered shapes, including a bare jaw for
  moustaches, limited goatees/chops, and different short/heavy/long beard outlines.
- Nine additional independently hashed traits, each with ten choices: neck width,
  shoulder width, iris colour, nose length, lip fullness, hair volume, hair part,
  complexion patterns and feature position. Existing head/face ranges are stronger.
- Area-averaged antialiasing at the four UI sizes; no optional image dependency.
- Country refinements over broad regional colour profiles. For example, Nigeria
  and Morocco no longer receive the same weighting merely because both are in
  Africa. Known birth country wins over nationality, then region. Nationality
  adjectives and imported country aliases resolve to the same country profiles.

Colour weights are **art-direction priors, not measured demographic percentages**
or a claim about any individual's appearance. Every profile remains multi-valued;
mixed-population profiles remain broad. Geography does not select cultural props,
facial geometry, skills, popularity or ability. Authored individual overrides win,
except that female facial hair is always zero, including authored overrides.

## Save compatibility

Portrait version 2 adds keys; no existing key, numeric style ID or palette index is
removed or reordered. Missing new traits derive independently from fighter ID.
Stored skin/hair/other choices are preserved, so revised generation weights apply
to newly initialised identities, not an automatic restyling of existing saves.
Gender-aware drawing and geometry improvements apply to old identities immediately.
The subsequent women's-catalogue correction also projects an old generated men's
cut into the women's pool at display time. It does not rewrite the stored vector
or change its skin/face choices. Existing women's-pool styles stay unchanged;
explicit authored hair exceptions (such as a specific real fighter's shaved head)
remain valid. Beards, moustaches and stubble are prohibited in the effective female
identity after both saved values and overrides are merged, as well as in rendering.
The shipped database contains 1,534 fighters (231 women) and no prefilled portrait
vectors, so a new game uses the revised generator for all of them, subject to
authored overrides. Existing saves are not rewritten.
The override merge now preserves detailed icon fields when a partial top-rated
entry updates only hair/skin: it no longer replaces the whole icon dictionary.

## Reproducible review

Run `py -3 analysis/portraits/review_portrait_diversity.py` from the repository root.
The outputs under `analysis/portraits/diversity_v2` are development evidence, not
runtime assets:

- `female_countries.png` and `male_countries.png`: eight synthetic fighters per
  row; UK, Nigeria, Japan, Brazil, India, Mexico, in that order.
- `hair_styles.png`: the same man with all IDs 0–47, eight per row.
- `women_hair_styles.png`: the same woman with the 27 allowed generated styles;
  order and stable IDs are listed in `manifest.json` under `women_hair_styles`.
- `same_colours.png`: 48 men with fixed skin, hair colour, age and background, to
  expose actual shape differences rather than count background recolouring.
- `manifest.json`: country-cohort identities, renderer source hashes, cold raster
  CPU samples at 72/98/104/180 pixels (eight samples per size, excluding Tk upload).
- `shipped_women.png` and `shipped_women.json`: 32 women from the actual database,
  generated separately with the existing contact-sheet tool's `--review-set women`.

The reviewed images have more varied outlines and identifiable women, but remain
simple comic faces. Passing an exact-pixel uniqueness test does **not** establish
that no pair can look similar, nor does it prove a real fighter's likeness.
Fine texture and iris differences are less prominent at thumbnail size.

## Verification

`fighter_portrait_regression_test.py` has 32 passing tests, including:

- independent fighter-ID determinism, preserved old vectors and save round trips;
- observed country draws matching the configured weights (4,000 IDs per cohort);
- all 48 hair styles, 16 beard styles and 10 complexion options rendering distinctly
  with a fixed test face; 5,000 unique generated vectors and 128 distinct neutral-
  colour face crops;
- normalised female presentation, dedicated hairstyle-pool reachability and
  prohibition of all beard/moustache styles after saved values and overrides;
- import/render with site packages disabled and NumPy/Pillow explicitly blocked;
- no fighter-data or global-RNG mutation from drawing; full-bout and terminal-RNG
  equality after restyling in both legacy and native-release harnesses;
- deterministic image fingerprints, bounded LRU cache and the unchanged blue RTD seal.

The native parity test ran here. It explicitly skips only on older checkouts without
`fight_release.py`, so this portrait-only commit does not require unrelated pending
engine files; broken imports within an existing release module still fail.

The fighter-profile regression passes all nine tests. The explicit
`py -3 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json`
check passes all 3,840 bouts with `"failures": []` and exit status 0. The smoke test passes, with
its existing matchmaking click-selection probe skipped because this display cannot
lay out the fighter table. A final isolated smoke rerun after the drawing refinements
also passed with the same skip. The complete `py -3 run_regression_suite.py` run exited
0 with `ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`, including both 3,840-bout
baselines and the final stability playtest. No package/rebuild is performed by this
portrait revision.

The women's 27-style-catalogue follow-up was verified with a fresh complete isolated
suite (exit 0), all 32 portrait tests and all nine profile tests. Both calibration
checks passed again; the smoke display-layout skip remains unchanged. The women's
style and shipped-fighter sheets were regenerated and visually reviewed.
