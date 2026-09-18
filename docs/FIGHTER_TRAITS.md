# Fighter traits

## Player presentation

The stable 46-name catalogue in `fighter_traits.py` owns categories, descriptions,
advantages, drawbacks, triggers and strength. Overview uses a compact card with
expandable Trait Effects; Identity starts expanded. Category accents follow the
dark profile theme. Unscouted fighters reveal neither the trait nor its progress.
Gym Leader and Late Bloomer are explicitly **Personality only**: their reputation
does not grant a live team bonus or move a fighter's actual prime ages.

## Live effects added or corrected

- Weight Bully: `clamp((natural_size - 60) / 10, 0, 3)` action-rating points for
  clinch, takedown, shoot, cage control, ground control and sweep actions. Missing
  natural-size evidence grants zero. Weight-cut/readiness penalties remain.
- Slow Starter: -3 action-rating points during the engine's early portion of round
  one, mirroring the existing Fast Starter timing flag.
- Iron Chin: +3 strike-defence rating; Fragile and Glass Cannon: -3. No submission
  defence bonus, knockout immunity or direct stoppage override is introduced.
- Fight Finisher: +4 finishing-action rating only when the *opponent's* hurt exceeds
  30% of that opponent's toughness. The previous own-hurt comparison was incorrect.
- Injury traits: current modifiers are +18 for Fragile/Injury Magnet/Slow Healer,
  and -10 for Iron Chin/Veteran Savvy/Fast Healer. Effective tendency is bounded
  to 1–100 and is consumed by training, injury, retirement and development checks.
- Non-MMA behaviour comparisons use the real Pressure, Counter and Cautious IDs;
  Dynamic Attacker remains supported. Trait IDs are not behaviour IDs.

Modifiers are action-rating points or tendency points, not percentage-point win
chances. Existing selector, stamina, recovery, commercial and development effects
remain active and are described individually in the catalogue.

## Camp evolution

Only a connected authored path may evolve. Camps need at least two weeks, quality
60, professionalism 60 and motivation 55. Each distinct game month can award progress
once. A qualifying camp earns `min(34, max(15, round(quality / 4 + min(weeks, 8))))`
points; ordinary quality-100 eight-week camps take four monthly credits to reach 100.
Examples are Gym Rat → Technical Learner → Adaptable and Big Finisher → Fight Finisher.
Reaching 100 records the transition and its reason, then starts a 12-month cooldown.
The latest 30 transitions persist; low-quality camps do not arbitrarily replace traits.
This intentionally changes career RNG consumption by removing the old trait lottery.

## Save compatibility

All existing trait names and their generation order remain stable. Progress, history
and the injury baseline are optional dataclass/save fields. New generated fighters
use an empty injury baseline and no permanently baked injury/toughness trait bonus.
Legacy fighters retain their stored attributes. On load, the current trait anchors
their existing injury tendency; subsequent trait differences apply live. The anchor
is a compatibility policy, **not** proof of which historical seed bonus was applied.
Previously baked toughness and other historical attributes cannot safely be undone
and are not rewritten. Raw injury-proneness progression still changes the base value.

## Verification scope

`fighter_traits_regression_test.py` checks catalogue coverage and live function
evidence for every mechanical trait, native attack/defence deltas, commercial and
behaviour effects, injury boundaries, deterministic camp progress and persistence.
Profile/UI and persistence regressions provide broader compatibility checks.
The 3,840-bout canonical native calibration tests release integration using neutral
Gym Rat fixtures; it is not a statistical balance study of all trait matchups.
The existing release certificate must not be reused for changed source. No EXE
was rebuilt and no user save was rewritten for this overhaul.

Historical selection fixtures predate the three new save fields. Their recognized
immutable-envelope adapter removes only exact defaults (`{}`, `[]`, `None`) and
rejects progressed, anchored or wrong-type values. All original fields, fixture
checksums and complete trace fingerprints remain exact; reference JSON is unchanged.
New captures retain the new fields. This is schema reconstruction, not permission
to ignore a changed simulation result or broaden source-certificate exceptions.

### Verified on 8 September 2026

- All 143 maintained suites completed successfully across the initial run (1–105)
  and resumed run (106–143) after the strict historical-schema correction. The
  smoke test skipped one display-limited matchmaking click/layout probe.
- All 13 dedicated trait regressions passed, including the legacy injury-100 boundary.
- All 46 trait identities completed paired native smoke bouts (92 simulations),
  preserving inputs and caller RNG and reproducing identical audits/terminal RNG.
- The final source-bound native calibration completed 3,840 bouts/39 groups with
  identical complete audits and terminal RNG against its candidate arm and no
  failures. `analysis/trait_overhaul_native_calibration_final_20260908.json` retains
  the final source inventory; it matched the workspace after collection.
- The 256-bout commentary gate passed with zero failures. Stability seeds 2201,
  2202 and 2203 reached Month 4 with 177, 175 and 190 recorded events respectively.
- Shared-card construction, expansion/privacy smoke checks and visual preview
  passed. Preview: `analysis/ui_previews/trait_card_v2.png`.
- No executable rebuilt, player save edited, or immutable reference replaced.
