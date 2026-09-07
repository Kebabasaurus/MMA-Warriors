# Portrait catalogue expansion v3

Source change; no executable was rebuilt. Adds fifty presets per existing shared
identity category, fifty hairstyles to each gender's generation pool, and fifty
men's facial-hair presets. Women remain clean-shaven after saved values and authored
overrides merge, with a second independent renderer guard.

| Category | Previous | Now |
|---|---:|---:|
| Men's generated hairstyles | 48 | 98 |
| Women's generated hairstyles | 27 | 77 |
| Global stable hairstyle registry | 48 | 148 |
| Men's facial hair (including none) | 16 | 66 |
| Women's facial hair | none | none |
| Skin ramps / natural hair ramps / backgrounds, each | 12 | 62 |
| Authored dye palettes (plus natural/empty) | 10 | 60 |
| Iris colours | 10 | 60 |
| Brows, eye shapes, spacing, size, noses, mouths, jaws, chins, cheeks, face lengths, ears, each | 10 | 60 |
| Neck width, shoulder width, nose length, lip fullness, hair volume, part, complexion, feature offset, each | 10 | 60 |
| Head width | 100 | 150 |

Age and injury layers remain derived continuous state, not additional selectable
identity categories. Their saturation rules are unchanged. Expanded nose presets
retain a 40% wear-eligible share before the existing independent career-wear draw.

## What the extra options mean

Hair adds ten silhouette families with five variants for each gender. Crown offset,
fringe, part, side length/taper and buns/tails/locks alter geometry. New curls use
broken curved strands, braids retain vertical ink and dye bands, and long hair has
directional grain. Beard variants alter jaw coverage, chin extension, moustache
span/droop and opacity, with jaw coverage restricted below the existing 0.735 band.

Shared anatomical additions are fifty bounded intermediate proportions, **not fifty
wholly different anatomical types**. Neighbouring IDs can look alike at 72 pixels;
even palette additions are subtle undertone variations. This expands combinations,
not the art quality or recognisability of every individual face. The renderer is
still stylised and angular; passing pixel uniqueness is not proof that every pair
of fighters looks unrelated, or that a real fighter is recognisable.

## Compatibility and cosmetic isolation

- Existing palette entries, style IDs, keys and complete saved-vector rendering
  remain unchanged. The three v2 pixel fingerprints are retained, now bound to
  complete captured v2 vectors in `analysis/portraits/legacy_v2_vectors.json`.
- Generator version 3 is used only for new/backfilled vectors. Missing fields in
  partial identities are still independently derived. No bulk save migration.
- The prior authorised female non-catalogue hair display correction remains;
  explicit authored hair exceptions are preserved, but never female facial hair.
- Mature shaved and buzzed fighters now receive one of 24 fighter-ID-stable
  scalp finishes (matte/sheen, stubble, thinning, temple/horseshoe shadow and
  restrained texture). This is derived cosmetic state from age 30, not a
  persisted identity field: complete saved vectors and the original young
  v3 raster fingerprints remain unchanged.
- Portrait version 4 adds an append-only 240-design tattoo catalogue. New or
  backfilled vectors receive a rare, fighter-ID-stable tattoo draw; hand-authored
  real-fighter tattoos are limited to marks visible in the portrait crop.
- New shades split each original colour family's probability between its old and
  appended shades. Country-family probability mass is exactly preserved; there is
  no uniformly weighted tail that washes out the country priors. These remain
  broad art-direction priors, not demographic measurements or individual claims.
- Each trait uses its own fighter-ID hash; no simulation RNG or ratings are read.
  Runtime stays standard-library-only. Cache bounds and status seals are unchanged.

## Review and verification

Run `py -3 analysis/portraits/review_portrait_expansion.py` to regenerate the v3
review set. `expansion_v3/manifest.json` records ordered IDs, effective identities
and source SHA-256 hashes. Hair sheets contain all fifty additions per gender at
180 and 72 pixels; beard sheets contain all fifty additions. Feature sheets vary
one trait per row, ten sampled new presets from left to right. Same-colour cohorts
remove background/skin/hair recolouring as a source of apparent diversity. Country
rows are UK, Nigeria, Japan, Brazil, India and Mexico; these are synthetic examples.

Review found weak bun outlines and dot-like curl texture in the first pass; these
were revised before final review. The retained sheets show the revised output.

The 37 focused portrait tests and nine profile tests pass. Standalone smoke passed
with the existing display-layout click-selection probe skipped. The required
3,840-bout engine baseline verification exited 0 with `"failures": []`.
The first full-suite attempt passed all six native release suites, then stopped at
the smoke test's generated-elite Muay Thai Clinch skill-diversity assertion. No
simulation/test assertion was changed or waived. The unchanged full-suite retry
completed successfully, including all six native release suites, both 3,840-bout
baselines, Fight Night, database/editor validation and the final stability playtest
(seeds 2201, 2202 and 2203 reached Month 4). The final 37-test portrait rerun also
passed with the highest new IDs exercised through the real save serializer.
The smoke skill-repair path uses UUID-derived variation, so the printed Python
random seed does not fully pin its generated fixtures; the initial failure is
retained here rather than silently treated as a clean first-pass run.

Checks ran against the current dev working tree. Unrelated native-engine edits
were left untouched and are not included in the portrait expansion commit.

Twelve cold raster samples per UI size (six new styles per gender) measured CPU
medians of 23.44 / 46.88 / 46.88 / 140.62 ms at 72 / 98 / 104 / 180 pixels, with
maxima 31.25 / 62.50 / 62.50 / 187.50 ms. These are local samples, excluding Tk
image upload, not a frame-time or whole-career performance guarantee. The existing
192-entry image cache is unchanged.

The focused suite
covers append-only catalogues, exact colour-family probabilities, all new controls
at 72/98/104/180 for both genders, legacy pixel parity, no female facial hair,
stdlib-only rendering, save round trips, and full-bout/terminal-RNG cosmetic parity
for both historical and native release engines.
