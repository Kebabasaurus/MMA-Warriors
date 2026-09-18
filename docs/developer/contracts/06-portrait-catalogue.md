## Portrait catalogue version 3

Keep all 148 hairstyle IDs, 66 facial-hair IDs and palette/trait IDs append-only.
Male generation uses IDs 0..97; FEMALE_HAIR_STYLES retains its original 27 plus
98..147 (77 total). Gender belongs in rendering and the cache key. Force female
facial_hair=0 AFTER merging saved vectors and overrides, with an independent renderer
guard. Preserve the existing female non-catalogue display correction and authored
hair exceptions. Never rewrite valid complete saved identities on a version bump.
`expansion.py` supplies bounded intermediate controls: never use new raw IDs as
linear widths/lengths. Preserve original colour-family probability mass when adding
shades; country priors are broad art direction, not demographic measurements.
Run `fighter_portrait_regression_test.py`; retain all original catalogue-prefix and
v2 complete-vector pixel fingerprints. Generate/review v3 sheets with
`analysis/portraits/review_portrait_expansion.py`. Small anatomical steps can look
alike at 72px: never claim pixel uniqueness proves perceptual diversity or likeness.
See `docs/FIGHTER_PORTRAIT_EXPANSION.md` for counts, compatibility and review scope.

Optional authored `beard_colour` is a stable HAIR palette ID, not a new generated
draw. Its absence must preserve historical beard pixels and follow scalp colour;
its presence still greys with age and cannot bypass the female facial-hair guard.
Keep named display corrections non-mutating for stored identities. Reference and
review scope live in `docs/FIGHTER_PORTRAIT_NAMED_CORRECTIONS.md`.

The ranked 51–100 pass appends authored-only hair IDs 148..150 (151 total) and
burgundy dye after the original 60 dyes. Keep their generation weights zero:
98 male / 77 female generated choices and all historical draws remain unchanged.
Cristiane Justino's female presentation is portrait-only; never apply that named
correction to stored gender, division or simulation. Keep the 49 photo-reviewed
entries and Matthew Green's separate user override: pale skin, short dirty-blond
hair, blue eyes, no facial hair or dye; preserve his other traits. Retain old v3 prefixes
and non-cohort identity hashes.
See `docs/FIGHTER_PORTRAIT_TOP_100_REVIEW.md` for the 45 inspected references and
four Legend copies; these are approximate comic likenesses, not exact portraits.

The top-200 continuation lives in `fighter_portraits/ranked_101_200.py`. Keep all
100 explicit vectors display-only, complete (every identity trait except `bg`, plus
`beard_colour`) and non-mutating for stored identities. Its five archive copies
must remain independent dictionaries. Maintain the labelled top_101_200 review at
72/98/104/180px and its outside-top-200 effective-identity hash. See
`docs/FIGHTER_PORTRAIT_TOP_200_REVIEW.md`.

The top-300 continuation lives in `fighter_portraits/ranked_201_300.py`. Keep all
100 complete vectors display-only, including `beard_colour` and every identity trait
except `bg`. Maintain the labelled top_201_300 review at 72/98/104/180px and the
combined reviewed-cohort effective-identity hash. Sources guide an approximate comic likeness
only: do not download or ship reference photos, infer simulation facts, or rewrite
saved portrait vectors. See `docs/FIGHTER_PORTRAIT_TOP_300_REVIEW.md`.

