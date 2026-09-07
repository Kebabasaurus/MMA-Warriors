# Rating positions 51–100: photo reference review

Reviewed 7 September 2026. This extends the existing top-50 pass; selection is the
shipped `Default Universe.universe.json`, sorted by rating descending then name
ascending, positions 51–100. It is not a current real-world ranking.

49 database records receive photo-reviewed cosmetic controls: 45 distinct people
and four additional Legend records. Matthew Green (position 51) subsequently
received user-directed pale skin, short dirty-blond hair, blue eyes and no facial
hair. All 50 entries now have authored direction. His other facial traits are
unchanged; this is a user specification, not a verified photographic likeness.

## Scope and compatibility

`fighter_portraits/ranked_51_100.py` authors all facial controls except background,
including observed hair, facial hair, skin colour and broad head proportions.
These are subjective art directions from the photographs below, not ethnicity
classifications or rating data. Named overrides merge for display, including old
saves; complete saved identities and all simulation fields remain untouched.

The shipped Cristiane Justino row says `gender="Male"`. The portrait normalizer
alone presents this exact name as female, including the independent no-beard
renderer guard and cache key. Her database gender, division and eligibility are
NOT repaired by this change. That separate data issue remains outstanding.

Three append-only, authored-only hairstyles are added: 148 wavy side part, 149
compact mullet, 150 shoulder sweep. A burgundy dye follows the existing 60 dyes.
There are now 151 hair IDs and 61 dyes plus natural/no-dye. Generated pools remain
98 male / 77 female choices with zero weight on the three additions. No generator
version bump or new trait draw is needed. The original 148 hair records, 66 beard
records, 60 dyes, old v2 pixel fingerprints and non-cohort identities are retained.

## Reference ledger

All 45 people below were visually inspected in the browser on the review date.
UFC entries use the named athlete page's full-body profile photo; the filename
identifies the selected image. PFL ranking entries use the named headshot from
that page. Source photos are not downloaded, copied into the repository or shipped.
Dates within image paths/names are identifiers, not independently verified shoot
dates. Profile images change; this review does not promise every fighter's latest
hairstyle or an exact historical-year match.

| Fighter | Inspected source / image identifier | Authored direction |
|---|---|---|
| Max Holloway | [UFC](https://www.ufc.com/athlete/max-holloway), `HOLLOWAY_MAX_L_04-13.png` | Close black crop, light stubble, long angular face |
| Mirko Cro Cop | [UFC](https://www.ufc.com/athlete/mirko-cro-cop), `Mirko-Cro-Cop_829_LeftFullBodyImage.png` | Dark military crew, light stubble, square jaw |
| Mitch McKee | [PFL](https://pflmma.com/wt-fighter/mitch-mckee), `0928bb2feb88014da8f3c9a7c61f64ae-1-1.png` | Brown side part, small moustache/chin beard |
| Movsar Evloev | [UFC](https://www.ufc.com/athlete/movsar-evloev), `EVLOEV_MOVSAR_L_03-21.png` | Dark swept fringe, jaw beard, narrow face |
| Petr Yan | [UFC](https://www.ufc.com/athlete/petr-yan), `YAN_PETR_L_BELT_04-09.png` | Brown short crop, warmer beard, broad jaw |
| Timur Khizriev | [PFL rankings](https://pflmma.com/rankings), `c150dcda270a15a6d3896115c4fcf3a6-1.png` | Thick dark fringe, rounded face, jaw beard without moustache |
| Yaroslav Amosov PFL | [UFC](https://www.ufc.com/athlete/yaroslav-amosov), `AMOSOV_YAROSLAV_R_12-13.png` | Brown forward crop, full beard, broad angular face |
| AJ McKee | [PFL rankings](https://pflmma.com/rankings), `cd5cd8e572cf2ddf9e0b650849cbccaa-1.png` | Short black coils, full beard, medium-dark skin |
| Alexander Shabliy | [PFL rankings](https://pflmma.com/rankings), `d801bf76c778bb0b2e20f2d0fcd2fe23-1.png` | Brown side part, short beard, square jaw |
| Aljamain Sterling | [UFC](https://www.ufc.com/athlete/aljamain-sterling), `STERLING_ALJAMAIN_L_04-25.png` | Coiled black fade, full beard, medium-dark skin |
| Belal Muhammad | [UFC](https://www.ufc.com/athlete/belal-muhammad), `MUHAMMAD_BELAL_L_06-06.png` | Close dark hair, heavy black beard, long nose |
| Caio Borralho | [UFC](https://www.ufc.com/athlete/caio-borralho), `BORRALHO_CAIO_L_03-07.png` | Dark side part, clean jaw, broad face |
| Carlos Prates | [UFC](https://www.ufc.com/athlete/carlos-prates), `PRATES_CARLOS_L_08-17.png` | Short black curls, clean jaw, full lips |
| Corey Anderson | [PFL rankings](https://pflmma.com/rankings), `fe2b388df3e0dcd085003ebd44cedbc5-1-1.png` | Bald, long black beard, dark skin, broad neck |
| Cristiane Justino | [UFC](https://www.ufc.com/athlete/cris-cyborg), `CYBORG_CRIS_L_0.png` | Burgundy shoulder-length hair, angular female face |
| Dan Henderson | [UFC](https://www.ufc.com/athlete/dan-henderson), `Dan-Henderson_63_LeftFullBodyImage.png` | Close dark buzz, stubble, broad chin |
| Diego Lopes | [UFC](https://www.ufc.com/athlete/diego-lopes), `LOPES_DIEGO_L_06-14.png` | Brown side-part mullet, moustache, clean jaw |
| Dominick Cruz | [UFC](https://www.ufc.com/athlete/dominick-cruz), `CRUZ_DOMINICK_L_12-11.png` | Short black quiff, short beard, narrow angular face |
| Gadzhi Rabadanov | [PFL rankings](https://pflmma.com/rankings), `eef830383c34759dd9acebd4957d6ab6-1-1.png` | Dark swept fringe, full beard, narrow face |
| Gilbert Melendez | [UFC](https://www.ufc.com/athlete/gilbert-melendez), `MELENDEZ_GILBERT_L.png` | Short dark curls, heavy stubble, broad face |
| Jan Blachowicz | [UFC](https://www.ufc.com/athlete/jan-blachowicz), `BLACHOWICZ_JAN_L_08-01.png` | Close brown hair, warm full beard, broad head |
| Jiri Prochazka | [UFC](https://www.ufc.com/athlete/jiri-prochazka), `PROCHAZKA_JIRI_L_04-11.png` | Buzz cut (not bun), full brown beard, long face |
| Johnny Eblen | [PFL rankings](https://pflmma.com/rankings), `f7958e2f705c10be44497eaffdb1282f-1-1.png` | Brown side part, warmer beard, broad face |
| Joselyne Edwards | [UFC](https://www.ufc.com/athlete/joselyne-edwards), `EDWARDS_JOSELYNE_L_08-09.png` | Black paired braids, medium-brown skin, long face |
| Josh Hokit | [UFC](https://www.ufc.com/athlete/josh-hokit), `HOKIT_JOSH_L_06-14.png` | Buzz, black full beard, broad head and neck |
| Joshua Van | [UFC](https://www.ufc.com/athlete/joshua-van), `VAN_JOSHUA_L_BELT_05-09.png` | Black fade, moustache and small goatee |
| Kamaru Usman | [UFC](https://www.ufc.com/athlete/kamaru-usman), `USMAN_KAMARU_L_06-14.png` | Bald, dark skin, jaw stubble, broad face |
| Mauricio Rua | [UFC](https://www.ufc.com/athlete/mauricio-rua), `RUA_SHOGUN_L_0.png` | Dark buzz, heavy stubble, broad square head |
| Michael Morales | [UFC](https://www.ufc.com/athlete/michael-morales), `MORALES_MICHAEL_L_08-24.png` | Taller coiled fade, moustache/goatee, medium-brown skin |
| Nassourdine Imavov | [UFC](https://www.ufc.com/athlete/nassourdine-imavov), `IMAVOV_NASSOURDINE_L_09-06.png` | Short dark crop, full beard, long face |
| Norma Dumont | [UFC](https://www.ufc.com/athlete/norma-dumont), `DUMONT_NORMA_L_04-25.png` | High black ponytail, broad jaw |
| Ramazan Kuramagomedov | [PFL](https://pflmma.com/wt-fighter/ramazan-kuramagomedov), `f1b262ada9a25fdf6e2afcf94a4795b8-1-1.png` | Brown crop, warm jaw beard without moustache |
| Renat Khavalov | [PFL rankings](https://pflmma.com/rankings), `bd2a4c95644ef390ed2f9e66b793d0ed-1-1.png` | Dark buzz, jaw beard without moustache, long face |
| Ronda Rousey | [UFC](https://www.ufc.com/athlete/ronda-rousey), `Ronda-Rousey_241883_LeftFullBodyImage.png` | Loose dirty-blonde shoulder-length hair, light eyes |
| Sean Brady | [UFC](https://www.ufc.com/athlete/sean-brady), `BRADY_SEAN_L_05-09.png` | Brown fade, full beard, broad jaw |
| Urijah Faber | [UFC](https://www.ufc.com/athlete/urijah-faber), `FABER_URIJAH_L.png` | Light-brown loose side-part waves, stubble, cleft chin |
| Virna Jandiroba | [UFC](https://www.ufc.com/athlete/virna-jandiroba), `JANDIROBA_VIRNA_L_04-04.png` | Short curly top, clipped sides, long angular face |
| Yan Xiaonan | [UFC](https://www.ufc.com/athlete/yan-xiaonan), `XIAONAN_YAN_L_08-29.png` | Black topknot, broad cheeks |
| Aiemann Zahabi | [UFC](https://www.ufc.com/athlete/aiemann-zahabi), `ZAHABI_AIEMANN_R_06-14.png` | Close buzz, black beard, strong brows |
| Alexander Volkov | [UFC](https://www.ufc.com/athlete/alexander-volkov), `VOLKOV_ALEXANDER_L_05-09.png` | Light-brown slick tied-back hair, stubble, long face |
| Amanda Lemos | [UFC](https://www.ufc.com/athlete/amanda-lemos), `LEMOS_AMANDA_L_08-08.png` | Bleached short swept cut, angular face |
| Anatoly Malykhin BAMMA | [ONE](https://www.onefc.com/athletes/anatoly-malykhin/), profile hero image | Short brown crew (not bald), stubble, broad face/neck |
| Anthony Hernandez | [UFC](https://www.ufc.com/athlete/anthony-hernandez), `HERNANDEZ_ANTHONY_L_08-22.png` | Dark mullet, short full beard |
| Anthony Pettis | [UFC](https://www.ufc.com/athlete/anthony-pettis), `PETTIS_ANTHONY_L_0.png` | Black buzz, faint chin patch, angular jaw |
| Arnold Allen | [UFC](https://www.ufc.com/athlete/arnold-allen), `ALLEN_ARNOLD_L_05-16.png` | Light-brown cropped mullet, moustache/chin beard, light eyes |

Mirko Cro Cop Legend, Mauricio Rua Legend, Ronda Rousey Legend and Urijah Faber
Legend copy their corresponding archived-photo direction. These are independent
vector copies, not four independently verified era-specific looks.

## Visual review and limits

The review sheets and ordered identity manifest live under
`analysis/portraits/top_51_100_2026_09/`. `review.html` is a self-contained labelled
gallery of the 180px renders. Cells run left to right, top to bottom,
starting at rank 51 (Matthew Green, user-directed). The manifest supplies every name.
First review rejected overly curly Rousey/Faber hair and long side curtains on
the mullets. New masks use loose strands and narrow nape locks; Volkov's incorrect
ridgehawk selection and Jandiroba's overlong curly silhouette were also corrected.

These remain angular comic portraits. Hair/beard/colour direction is more faithful,
but facial resemblance is approximate, especially at 72px. Tattoos, eyewear, exact
hair strand patterns and precise historical age/era likeness are not reproduced.
The reference does not justify claiming photorealism, universal recognisability
or perceptual uniqueness. Existing career ageing/damage layers still apply.

Regenerate a sheet (repeat with cell 72, 98, 104, 180):

```powershell
py -3 analysis/portraits/generate_portrait_contact_sheet.py --review-set top-rated --offset 50 --count 50 --columns 10 --cell 180 --out analysis/portraits/top_51_100_2026_09/portraits_180.png --manifest analysis/portraits/top_51_100_2026_09/identities.json --html analysis/portraits/top_51_100_2026_09/review.html
```

Regression coverage checks exact cohort membership, old catalogue prefixes, the
unchanged non-cohort manifest, all authored trait ranges, saved-vector immutability,
female presentation/no-beard guards, all UI sizes and complete fight/RNG parity.
This source change does not rebuild the packaged executable.

## Initial 49-entry batch verification — 7 September 2026

- `py -3 fighter_portrait_regression_test.py`: 45 tests passed, including all
  reviewed sheet pixels at 72/98/104/180px and labelled gallery image/name checks.
- `py -3 fighter_profile_regression_test.py`: 9 tests passed.
- `py -3 smoke_test.py`: passed. Its matchmaking click-selection probe was skipped
  because the available display could not lay out the fighter table.
- `py -3 run_regression_suite.py`: exit 0, all requested isolated suites passed,
  including the final three-seed stability playtest. Its two 3,840-fight baseline
  verifications passed; engine verification returned `"failures": []` and action
  verification returned `"passed": true`. Existing diagnostic warnings remain.
- The 148 original v3 hair renders were compared with both renderer and hair code
  from `c4e4045`: identical 72px pixel digest, now retained as a regression. The
  original v2 pixel fixtures also pass. All 1,485 non-cohort shipped identities
  retain their pre-batch digest.
- The four PNG sheets were visually inspected. The HTML gallery's images and
  labels were checked programmatically; its browser layout was not previewed.

No ratings, database gender/divisions, combat mechanics, calibration references,
portable saves or packaged executables were edited for this batch.

## Matthew Green follow-up

The user's direction is stored separately in `PORTRAIT_USER_OVERRIDES`:
`skin=0` (pale/light), `hair_style=3` (short crop), `hair_colour=4` (dark/dirty
blond), `facial_hair=0`, `iris_colour=4` (blue), `dye=""`. Clearing dye prevents
a saved artificial colour from hiding the requested natural hair colour. Face shape,
other traits and the stored vector remain unchanged. The 50-entry sheets
and labelled gallery were refreshed; `matthew_green.png` is the individual preview.
This follow-up uses focused portrait/profile verification, not a rerun of the
full shipping suite recorded above. No executable was rebuilt.
The initial follow-up passed all 46 portrait tests and all nine profile tests. The
pale-skin correction refreshes the same visual artifacts and regression digests.
