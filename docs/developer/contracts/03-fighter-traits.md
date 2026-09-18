## Trait catalogue and progression

`fighter_traits.TRAIT_DEFINITIONS` owns the stable 46-name order used by constants.
Every trait needs all explanatory fields and live mechanic evidence or explicit
Personality-only status. Keep cards observational and scouting-aware. Camp progress
uses distinct months, connected paths and a 12-month post-change cooldown; never
restore random unrelated replacements. Saved injury baselines anchor old risk rather
than attempting to reverse unknown seeding history. Do not rewrite legacy toughness
or detailed ratings. Current injury checks use `effective_injury_tendency`; stored
injury-proneness mutations remain base changes. Trait combat changes need fresh
source-bound checks: the previous native certificate is not evidence for new mechanics.
Run `fighter_traits_regression_test.py`, profile/persistence tests and native gates.
Recognized immutable historical fixture envelopes predate the three trait-save fields.
The historical adapter may omit only exact empty dict/list progress/history and a
None injury baseline, alongside the existing default portrait fields. Reject populated
or wrong-type values; retain every original field and every checksum. New captures
keep the complete current schema. This does not permit source-certificate exceptions.
Legacy roster/profile readers must show the current `effective_injury_tendency`
with the retained base `injury_proneness` when both are useful; never rewrite
the saved baseline merely to make the display agree.

