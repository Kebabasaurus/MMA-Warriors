# Fighter Development Guide

This guide describes the current MMA Warriors development model so it can be audited and redesigned deliberately.

## Lifecycle

- Fighters enter regional development promotions at age 16 or later, then can graduate after results, current ability, and potential meet the feeder thresholds.
- Every month, active fighters recover fatigue, reduce injury time, receive a development check, receive a decline check, and update their yearly peak overall.
- Every year, all active fighters age by one. Pre-prime fighters can gain an additional skill point; post-prime fighters can decline.
- Retirement is assessed once per fighter per year in an individual stable review month, not every month. Booked player fighters defer retirement until the booked bout is complete.

## Potential And Prime

`potential` is an upper ceiling, not an automatic destination. A fighter only gains from monthly development when their current overall is below potential.

Prime windows are individual and permanent. New fighters and migrated saves receive a `Career Arc` based on conditioning, resilience, dedication, professionalism, and style. The archetypes are `Early Peak`, `Standard Prime`, `Late Developer`, and `Long Prime`. Grappling-heavy styles generally age a little more gracefully. Camp traits never alter an established prime window.

- Before prime: youth improves development and annual growth is possible.
- In prime: performance is stable and gets a small fight-context benefit.
- After prime: age increases decline probability; the risk rises each year past the prime end.
- A winning, well-conditioned, motivated veteran can very rarely improve after the nominal prime. The chance is capped at 4.5% per monthly development check, falls sharply after 45, and is not available to fighters on a poor run. It is a resurgence, not an age-reset.

## Monthly Development

The monthly development score uses:

- Gym quality and facilities
- Gym specialty fit
- Dedication / professionalism
- Individual career runway: early development, prime duration, and a small post-prime learning tail
- Positive momentum and morale
- Trait bonuses for `Gym Rat`, `Technical Learner`, `Adaptable`, and `Momentum Fighter`
- Gap between potential and current overall
- Fatigue, injury, and crowded-gym penalties

If this score clears a variable monthly threshold, the fighter gains one or two broad/detailed skill points. The detailed-skill update touches a random skill group, then broad ratings are recalculated from the detailed sheet.

## Monthly Decline

Decline pressure uses:

- Age beyond prime end
- Negative momentum and a poor loss record
- Low morale
- Injury proneness, active injury, and fatigue
- Buffers from professionalism, gym quality, facilities, good form, and veteran-longevity traits

If decline pressure clears its variable threshold, broad and detailed skills lose one point, or two in severe cases.

## Camps

Scheduled fights create camp weeks from the event date. Camp quality, specialty fit, professionalism, and camp length create `camp_boost`.

Camp boost affects fight initiative, action/defence values, weight-cut preparation, and between-round recovery. Good camps can also create small specialty skill improvements and trait changes, but neither is guaranteed.

## Traits

Traits can develop or shift in camp. Examples:

- `Gym Rat`, `Technical Learner`, `Adaptable`, and `Momentum Fighter` support development.
- The permanent `Career Arc` shapes prime timing. `Veteran Savvy` and `Warrior Spirit` can support durability and late-career form without changing that arc.
- `Fast Healer` and `Slow Healer` alter the post-fight availability window.
- `Body Hunter`, `Leg Kicker`, `Cage Specialist`, `Elbow Specialist`, `Scramble Artist`, and `Fight Finisher` affect shot selection or effectiveness in the fight engine.
- `Regional Star` and `Overlooked Talent` make a regional run more likely to convert into marketability and a return to free agency.
- `Bad Weight Cut`, `Fragile`, and `Erratic` create performance or health risk.
- `Submission Ace`, `Knockout Artist`, `Pressure Fighter`, and `Counter Specialist` influence action choice and fight context.

## Regional Proving Ground

Regional promotions can recruit young prospects and selected unsigned fighters up to age 33. An experienced fighter who misses out on a major-company deal may receive an `Overlooked Talent` second-chance run: wins build popularity, morale, momentum, and occasionally a skill point. A fighter can graduate after an ordinary prospect route or after a credible regional resurgence, then returns to the free-agent market with stronger signing value.

## What To Audit Next

- Whether potential should be split into physical, technical, and marketability ceilings.
- Whether a fighter's prime window should additionally depend on weight class and cumulative damage.
- Whether losses should cause confidence changes distinct from morale.
- Whether prospects need separate amateur records, regional-title routes, and manager/coach quality.
- Whether gym moves should have a short transition penalty before a new camp bonus applies.
- Whether yearly growth needs diminishing returns near a fighter's potential rather than a hard ceiling.
