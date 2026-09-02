# Narrative System Audit and Development Plan

- **Status:** Living design and implementation record
- **Scope:** Emergent fighter, staff, promotion, and world narratives
- **Hard release rule:** Narrative development must not produce a repeatable slowdown in calendar
  simulation.

> [!IMPORTANT]
> **Simulation speed is a non-negotiable product requirement.** Narrative features may interpret
> events already being processed, but they may not add a second world simulation, a recurring
> whole-world scan, or history reconstruction during calendar advancement. A narrative phase is not
> complete if it creates a repeatable simulation slowdown, even when its stories work correctly.
> The design target is zero measurable regression. The percentage ceilings below are
> noise-tolerant automated rejection gates, not an allowance to spend simulation time.

## Decision rule for every narrative feature

A narrative feature may ship only when all of the following are true:

- it reacts to a domain event the simulation already processes;
- it uses a direct ID/key lookup or another explicitly bounded lookup;
- it adds no recurring whole-world, roster, Chronicle, Results, or fight-history scan;
- it leaves gameplay state and shared simulation RNG identical when narrative tracking is toggled;
- it keeps active, resolved, and per-thread data bounded over long careers;
- its clean paired performance readings show no repeatable simulation slowdown.

Passing the noise-tolerant automated ceiling is necessary but not sufficient. If repeated clean
measurements consistently get slower, the feature must be optimized, narrowed, deferred, or removed.

## Purpose

MMA Warriors already produces many of the facts needed for memorable careers: prospects develop,
champions emerge, rivals trade wins, contracts become strained, fighters suffer injuries, companies
rise or fail, and veterans retire. The next step is to connect those facts into persistent stories
with a beginning, escalation, meaningful decisions, consequences, and a visible conclusion.

Narrative development must **not slow calendar simulation down**. Story logic should interpret
events the simulation has already produced. It must not repeatedly search the whole world, rebuild
career histories, or run a second simulation alongside the existing one.

## Audit conclusion

The game is strongest when a story is already attached to gameplay. Rivalries affect matchmaking,
main-event value, event demand, popularity, legacy, and rematches. Serious injuries create real
medical decisions. Career journeys affect cash, promises, morale, trust, camps, development, and
contracts.

The weaker material is generated as an isolated headline. Viral clips, charity appearances, camp
trouble, rumours, and similar incidents change a value and enter a news feed, but they usually have
no durable identity, follow-up beat, escalation, or payoff.

The main design gap is therefore **narrative memory**, not a lack of simulation events.

## Current narrative inventory

| Narrative | What currently works | Current limitation |
| --- | --- | --- |
| Rivalries | Callouts create heat; media actions escalate it; feuds influence gates, matchmaking, main events, popularity, legacy, rematches, and deciders. | A fighter can have only one active rival. Public escalation is stronger than public resolution. |
| Title chases | Rankings, streaks, title opportunities, defenses, records, awards, and legacy naturally create rises and falls. | The individual facts are not assembled into one continuing title-chase or championship-reign story. |
| Career journeys | Six structured arcs cover academy champions, veteran final runs, professionalism, weight management, camp fit, and champion retention. | They apply only to the player roster, have limited branching, and are usually offered only once per type. |
| Injury and comeback | Serious injuries create surgery, accelerated rehabilitation, or retirement choices with lasting consequences. Comeback and farewell contracts exist. | Recovery has few intermediate beats and the return fight is not consistently framed as the payoff to the injury story. |
| Retirement and legacy | Decline, final-fight requests, meaningful-opponent selection, persistent Career Farewell chapters, retirement shows, records, career peaks, awards, and Hall of Fame induction form connected career endings. | Richer authored retrospectives and ceremonial variants remain future depth. |
| Academy lineage | Recruitment battles, personalities, promises, amateur bouts, tournaments, graduation, alumni, and matching rights support very long careers. | Much of the academy context becomes detached from the fighter after graduation. |
| Contracts | Personas, rival offers, promises, trust, morale, clauses, and market testing create meaningful tension. Renewal pressure, expiry, release, rival signings, returns, and cross-company revenge now remain connected in an ID-safe Contract Saga. | Holdouts and richer negotiation personalities can still gain more authored decisions and presentation. |
| Promotions | Strategies, executives, board mandates, rescues, buyouts, milestones, promotion rivalries, eras, child promotions, and feeder pathways create connected world history. | Executive/staff relationships and future-dated child events can deepen how those eras are experienced. |
| Gyms and relationships | Camp moves, gym history, rival academies, ID-safe friendship/stablemate aftermath, academy mentorship, coaching loyalty, gym splits, and post-split rematches now form durable chapters. | Broader mentor/protege relationships outside the academy and coach/staff poaching remain future depth. |
| Staff careers | Staff have durable IDs, roles, skills, morale, specialties, contracts, negotiations, and visible simulation effects. Appointments, renewal pressure, stalled talks, renewals, releases, and expiry now form Staff Tenure chapters. | Role-specific triumphs, failures, poaching, succession, and executive/staff relationships remain future depth. |
| Other sports | Crossovers, contender surges, title reigns, losses, retirement, records, awards, finance, and Hall of Fame careers form persistent chapters. | Richer same-sport rivalries and more authored crossover decisions remain future depth. |

## Existing narrative strengths to preserve

### Rivalry lifecycle

The current rivalry chain is the closest system to a complete emergent narrative:

```text
callout or competitive result
  -> persistent ID-linked rivalry and origin
  -> media escalation and heat
  -> higher matchmaking and headline value
  -> event-demand and gate effect
  -> fight result
  -> resolution, demanded rematch, or series decider
```

The future story layer should expose and remember this chain rather than replace it.

### Fighter career lifecycle

The game can already produce a long-form career:

```text
academy or regional origin
  -> development and gym decisions
  -> rankings and contender opportunities
  -> championship run
  -> contract leverage and public profile
  -> decline, injury, or comeback
  -> farewell, retirement, records, and Hall of Fame
```

The facts exist across several data structures and screens. The missing feature is a unified career
timeline that explains how one chapter caused the next.

### Promotion lifecycle

Company strategy, executive changes, board pressure, finance, rescues, buyouts, major signings,
media rights, milestones, academies, child companies, and super events can already produce promotion
history. These should become named eras and ongoing company stories when the same causes persist.

## Problems to correct before expansion

1. Losing a title currently completes the **Keep The Champion** journey as a successful completion,
   which then grants positive morale, motivation, and trust. A title loss should close the chapter
   with a suitable successful, bittersweet, or failed outcome.
2. Choosing **Set honest expectations** in a veteran final-run story applies an immediate trust and
   morale penalty but leaves the story active. Deadline failure can therefore punish the same choice
   a second time.
3. Rivalry conclusions update fighter history but are not consistently recorded as important public
   Chronicle outcomes.
4. Chronicle participants are stored mainly by display name. Narrative links should use fighter IDs
   and retain names only as presentation snapshots.
5. A Homegrown Champion story can extend repeatedly without an alternate ending or a deliberate
   player decision to continue it.
6. Friendship previously had a safe legacy resolver but almost no gameplay or narrative effect;
   the delivered relationship-aftermath chapter now supplies its competitive tests and conclusions.

## Narrative architecture

### Structured story threads

Add a persistent `story_threads` collection. It should not replace Results, fighter histories,
rivalries, titles, contracts, or the Chronicle. Those remain authoritative domain state. A story
thread is a compact index that connects their important events.

A thread should contain only bounded, JSON-safe data such as:

```python
{
    "story_id": "STORY-...",
    "type": "Rivalry",
    "status": "active",        # emerging, active, cooling, resolved, abandoned
    "phase": "rematch_due",
    "importance": 4,
    "fighter_ids": ["FTR-...", "FTR-..."],
    "fighter_names": ["Name A", "Name B"],
    "companies": ["Promotion"],
    "origin_ref": "event-or-action-reference",
    "stakes": "Series is level; the next fight decides the rivalry.",
    "started_month": 18,
    "last_updated_month": 24,
    "expires_month": 36,
    "beats": [
        {"month": 18, "week": 2, "kind": "callout", "ref": "...", "summary": "..."}
    ],
    "resolution": ""
}
```

IDs and stable references prevent duplicate names from linking to the wrong career. Presentation
names remain snapshots so retired, transferred, or renamed participants still read naturally.

### Event-driven updates

Story threads should advance only when an existing domain action reports a meaningful event:

- rivalry created, promoted, cooled, fought, or resolved;
- fight booked, completed, or cancelled;
- title opportunity earned, won, defended, or lost;
- contract promise made, fulfilled, broken, or declined;
- serious injury decision, recovery, return booking, or comeback result;
- academy recruitment, promise, tournament, graduation, or alumni milestone;
- promotion mandate, rescue, buyout, major signing, or milestone;
- retirement request, farewell booking, final result, or Hall of Fame induction.

The emitting method should call one small story helper after its normal state change. The helper
must find the relevant thread through an index or stable story key, append at most one beat, and
return. It must not scan every fighter or every Chronicle entry.

## Simulation-performance requirements

Narrative work is accepted only if it preserves calendar speed. This is a release gate, not a
best-effort target: a feature that breaches the budget must be optimized, narrowed, deferred, or
removed before release.

The product target is **no measurable simulation slowdown**. A result below the automated ceiling
is not sufficient when repeated profiling shows a consistent regression. The 3% and 5% thresholds
exist to prevent machine scheduling noise from producing unstable test failures; they do not create
a performance budget for narrative features to consume.

| Gate | Required result |
| --- | --- |
| Calendar architecture | No new weekly whole-world or history scan. |
| Product target | No repeatable increase in calendar-advance CPU time. |
| Short deterministic A/B | No more than 5% median overhead, including helper-entry cost. |
| Normal one-year profile | Target no more than 3% median overhead. |
| Populated 25-year profile | No more than 5% overhead. |
| Simulation integrity | Identical gameplay state and shared simulation RNG with narratives enabled or disabled. |
| Long-run scaling | Weekly cost must not rise with Chronicle or resolved-story history; save growth remains bounded. |

### Hard rules

1. **No new whole-world weekly narrative scan.** Do not add a `process_story_threads()` pass that
   loops through every fighter, promotion, result, or historical entry each week.
2. **No history reconstruction during advancement.** A weekly or monthly tick must never rebuild a
   story by reading complete fight histories, result archives, news, or Chronicle data.
3. **O(1) or bounded lookup on story events.** Maintain indexes such as participant ID, rivalry pair,
   company, and origin reference so an event updates its thread directly.
4. **Bound every collection.** Keep a small beat limit per thread, a bounded number of resolved
   threads, and compact archived summaries. Preserve career totals elsewhere rather than copying
   them into narrative state.
5. **Do not add narrative RNG to unrelated simulation.** Story copy selection should use a separate
   presentation stream or deterministic selection and must never change fight, development,
   matchmaking, finance, or world-simulation outcomes.
6. **Generate prose lazily.** Store structured facts and short summaries. Longer retrospective text
   should be assembled when a player opens a screen, not during weekly advancement.
7. **No background language-model calls.** The shipped game must produce stories locally from
   authored templates and simulation facts.
8. **Reuse existing calendar work.** If a monthly system already loops over fighters, it may emit a
   story transition at the point where it detects the condition. Do not repeat the loop later.
9. **Deduplicate at write time.** Stable event references must prevent save reloads, refreshes, or
   transaction retries from adding the same beat twice.
10. **Preserve transaction boundaries.** Event settlement, paid media, academy transitions, and
    other transactional actions must roll narrative writes back with their owning domain action.

### Recommended limits

- Maximum 12 detailed beats retained per active thread.
- Maximum 4 important beats retained in a resolved thread, plus one compact resolution summary.
- Maximum 300 active/cooling threads across the world.
- Maximum 1,200 resolved thread summaries, with low-importance entries pruned first.
- Maximum one ordinary narrative notification per weekly advance summary; player decisions may
  remain separately actionable.

The exact limits should be calibrated with long-run saves, but they must remain explicit constants
rather than unbounded lists.

### Performance verification

Use the canonical deterministic 12-week A/B regression to advance clean copies of the same seeded
world with narrative tracking enabled and disabled. It fixes otherwise entropy-based generated IDs
inside the test only, then requires identical gameplay state and shared simulation RNG. Longer
full-year and multi-decade profiling remains an explicit audit rather than making every shipping
suite prohibitively slow.

The automated release gate uses process CPU time for its median comparison and reports wall-clock
medians as a diagnostic. This measures the simulation work added by narratives without allowing an
unrelated Windows scheduler pause to decide the release. Alternating arm order, three paired samples,
the fixed noise allowance, and the 5% proportional ceiling remain in force; CPU timing is not a
license to weaken the performance budget.

Initial acceptance targets:

- no more than 3% median overhead for a normal one-year simulation;
- no more than 5% overhead in a populated 25-year career;
- no growth in weekly processing time proportional to Chronicle or resolved-story history;
- identical fight outcomes, finances, rankings, development, and world RNG state when only
  presentation wording changes;
- bounded save-size growth over 25-, 50-, and 100-year audits.

If a phase exceeds these limits, optimize or narrow it before adding more story types.
If it stays below the limits but produces a consistent positive regression across repeated clean
runs, optimize it anyway: the acceptance target remains no simulation slowdown.

## Player-facing presentation

### Active Storylines

Add a compact screen containing:

- emerging, active, cooling, and recently resolved threads;
- current phase and importance;
- what caused the story;
- what is at stake;
- its latest meaningful beat;
- the next decision or plausible simulation trigger;
- direct links to relevant fighter, company, event, gym, or result views.

The screen should read saved thread indexes. It should not calculate every possible storyline when
opened.

### Matchmaking and events

Show a short **Why this fight matters** summary using already-resolved active threads. Examples:

- “Their first fight ended in a close decision; a rematch has been demanded.”
- “A win would give the veteran the final title opportunity promised by the promotion.”
- “The academy graduate is one victory from a credible championship challenge.”

Fight Night introductions and post-fight summaries should reference the same thread. They must not
alter the fight result or consume the simulation RNG.

### Fighter profiles

Add a unified Career Timeline that merges links to existing authoritative records:

- origin and academy graduation;
- important signings and promotion moves;
- title opportunities, wins, defenses, and losses;
- defining rivalries and series outcomes;
- serious injuries and comeback results;
- career-journey choices and conclusions;
- records, awards, farewell, retirement, and Hall of Fame.

This should be assembled lazily for the selected fighter and cached only if profiling shows a need.

### Annual review

The year-end review should identify a small set of evidence-backed stories: defining reign, rivalry,
breakthrough, comeback, collapse, signing, promotion turnaround, and retirement. It should select
from story threads updated during that year rather than scan all historical fight records.

## Recommended story types

### Phase 1: rivalry, title, and redemption

- Public callout -> promoted grudge -> first fight -> rematch -> decider.
- Contender surge -> eliminator -> title opportunity -> coronation or setback.
- Major upset -> rebuild -> redemption opportunity.
- Championship reign -> rising challenger -> defining defense or era-ending loss.
- Veteran final run -> ranked opportunity -> title chance or farewell.

These should be implemented first because the necessary mechanics and decisions already exist.

### Phase 2: career and relationships

- Serious injury -> treatment -> recovery updates -> return -> comeback outcome.
- Academy prospect -> graduation -> contender -> homegrown champion or release.
- Weight crisis -> support, division move, repeated miss, or career reinvention.
- Gym stagnation -> camp move -> breakthrough, failed fit, or gym split.
- Mentor/protege, stablemate friendship, competitive teammate, and coaching loyalty.
- Contract promise -> fulfillment, breach, reconciliation, holdout, or departure.

### Phase 3: promotion and world stories

- Regional promotion -> breakout signing -> media growth -> major-company status.
- Financial decline -> board mandate -> executive change -> rescue, recovery, or buyout.
- Competing promotions fighting over talent, markets, media packages, and event dates.
- Child promotion graduate or champion becoming a parent-company star.
- Hometown hero building a market and returning for a major event.

### Phase 4: other sports and crossover

- Combat-sport prospect, championship reign, upset, comeback, and retirement threads.
- Cross-sport temptation -> negotiation -> debut -> success or difficult adjustment -> MMA return.
- Parent-company athlete becoming a multi-sport attraction without losing stable career identity.

## AI use of story value

Story value may influence a decision but must not override credible sporting constraints. AI
promotions should be able to:

- prefer a credible overdue rematch;
- give an emerging contender an eliminator;
- choose a meaningful farewell opponent when one is available;
- protect or accelerate a prospect according to company identity;
- capitalize on a contract defection or promotion rivalry;
- stop repeatedly generating callouts that cannot lead to a plausible fight.

An indexed thread lookup can contribute a bounded matchmaking score. It must not introduce an
additional all-pairs search beyond the candidate pairs the matchmaker already evaluates.

## Implementation sequence

1. Correct the existing career-journey outcome issues and add focused regressions.
2. Add the save-compatible story-thread schema, bounded indexes, deduplication, and old-save defaults.
3. Convert rivalry creation, escalation, booking, results, draws, rematches, and resolution into the
   first complete story-thread pilot.
4. Add Active Storylines and **Why this fight matters** presentation.
5. Add title-chase, championship-reign, veteran-run, and redemption threads.
6. Add injury, academy, contract, gym, promotion, and crossover story types incrementally.
7. Run performance and 25-/50-/100-year stability audits after every phase.

## Implementation status

### Delivered foundation and Phase 1 core

- Persistent, save-compatible `story_threads` with stable story keys and fighter IDs.
- Transient direct-key index rebuilt after initialization/load rather than during calendar ticks.
- Hard active, resolved, and per-thread beat limits with write-time deduplication.
- Event-driven rivalry origin, escalation, draw, cooling, fight-result, rematch, settlement, and
  abandoned-feud beats.
- Event-driven title-chase, championship-reign, title-defense, title-loss, and redemption beats for
  player and major AI-promotion results.
- ID-linked public Chronicle payoffs for rivalry, title, and redemption conclusions.
- World > Storylines browser plus **Why this fight matters** in matchmaking and Fight Night.
- Correct champion-retention failure semantics, single-penalty veteran decline, and one-extension
  limit for supported homegrown-title projects.
- Focused regression coverage for identity, bounds, deduplication, save normalization, RNG purity,
  UI observation, career outcomes, and a strict indexed event-update time budget.

### Delivered Phase 2 foundations and performance gate

- Serious-injury decisions, surgical recovery, accelerated rehabilitation, clearance, return-fight
  payoff, medical retirement, and contracted comeback/farewell commitments now remain connected.
- Academy graduation can continue through a durable lineage thread to a homegrown championship.
- Main-event and top-opponent contract promises now record partial fulfilment, fulfilment, and breach
  as one ID-linked chapter rather than unrelated inbox entries.
- Fighter profiles show their connected career stories lazily from the participant index.
- The shipping suite now includes three clean, alternating enabled/disabled samples covering 12
  aggregate weeks per arm. It verifies identical core fighter, promotion, finance, date, and RNG
  outcomes and enforces a 5% median budget with a small fixed scheduler-noise allowance.
- Story status counts are maintained incrementally. Ordinary creation, advancement, and resolution
  no longer sort or normalize the entire collection; a bounded prune runs only when an explicit
  active or resolved cap is exceeded. An earlier canonical paired audit measured a 5.644-second
  narrative median against a 5.849-second baseline: 3.50% faster in that run. Repeated paired
  results, including a +0.03% run, remain inside the release budget and show no measurable
  narrative slowdown beyond normal scheduler variation.

### Delivered wider world stories and retrospectives

- Weight-cut turnarounds now retain support plans, successful cuts, setbacks, completion, and
  division reinvention as one chapter.
- Camp-fit reviews and fighter gym moves retain the old room, destination, reason, and new fit;
  ID-backed friends and established stablemates can carry their competitive meeting into a
  relationship thread without a roster-name scan.
- AI strategy shifts, board mandates, executive changes, investor rescues, and distressed buyouts
  now advance a persistent promotion-era thread.
- Boxing, Kickboxing, Muay Thai/Lethwei, Wrestling, and Brazilian Jiu-Jitsu careers now retain
  contender surges, championship wins/defences/losses, farewell retirement, and MMA crossover
  transitions. Cross-promotional superfights close with a connected result.
- Fighter Profiles build a unified Career Timeline lazily from the direct participant index and
  bounded fighter-local histories; opening a profile never scans the wider world or reconstructs
  archived cards.
- The annual awards process selects at most eight defining threads updated during that year,
  stores them beside awards history, includes them in the year-end message, and creates a resolved
  annual-review chapter. This is one bounded year-end selection, not recurring calendar work.
- Friend relationships now retain `friend_fighter_id`; legacy name-only saves backfill it only when
  the complete loaded world has one unambiguous match.
- Academy mentor choices persist through graduation, fit/attention-driven departures become gym
  splits, regional popularity milestones form hometown-hero chapters, and major AI signings feed
  the acquiring promotion's talent-war era.
- AI matchmaking adds a small cached direct-index story value only to pairs already accepted by its
  sporting constraints. Rivalries, injury returns, comebacks, redemptions, title chases, and
  relationship tension can break credible ties or raise headline value, but cannot legalize an
  unsafe, stale, cross-division, unavailable, or implausibly ranked matchup.
- A synthetic 25-/50-/100-year storage regression proves the resolved cap, RNG isolation, lookup
  stability, and bounded serialized growth. The latest canonical payloads were 191,917 bytes at 25
  years, 383,617 bytes at 50 years, and 769,228 bytes at 100 years; the indexed probe remained
  effectively flat at 0.0276 to 0.0283 seconds.

### Delivered promotion rivalries and coaching legacy

- Contested player/AI contract signings, academy recruitment battles, and sanctioned
  cross-promotional superfights now contribute to one scored, two-year Promotion Rivalry chapter.
  Duplicate event references cannot score twice; a decisive series resolves, and the next real
  competitive event closes an unfinished prior cycle before starting the new one.
- Promotion rivalry creation receives both known companies directly from the owning event. It does
  not rank promotions, compare every roster, or run a recurring rivalry-discovery pass.
- Significant fighters now retain separate coaching-loyalty chapters for each training room. A gym
  move begins the partnership, meaningful wins and title breakthroughs validate it, major setbacks
  test it, and a later split resolves the old coaching chapter before the next one begins.
- Academy mentorship now remains active after graduation through an ID link stored on the graduate.
  A major senior setback becomes a mentorship test; a championship win supplies the payoff and
  resolution without searching academy alumni.
- The canonical post-expansion paired calendar audit measured +2.69% overhead, and the preceding
  homecoming-enabled focused run measured -2.28%; both are inside the 5% budget across 12 aggregate
  weeks per arm. The disabled arm exits the new event helpers before any story-key work, so the
  comparison includes their real cost rather than hiding helper entry in both arms.

### Delivered hometown event arcs

- A locally established fighter booked into a main event or title fight in their hometown or birth
  market now receives a deduplicated homecoming announcement at the real booking event.
- The completed bout advances that same chapter into a triumph, setback, heartbreak, unresolved
  result, or home-title payoff. A title triumph resolves the chapter; later epilogues cannot erase
  its established resolution, while reaching icon-level market popularity remains a second valid
  conclusion.
- Matchmaking and Fight Night can surface the booked homecoming through two direct hometown-story
  lookups. Player and AI settlement reuse the regional-effects pass they already execute, with no
  recurring event, roster, result-history, or market scan.

### Delivered contract sagas

- The final renewal window, stalled or broken talks, expiry, release, new signing, rival-company
  defection, return signing, and the first cross-company revenge fight now remain in one persistent
  Contract Saga.
- Each fighter carries only a direct optional story key. Contract events update that thread at the
  point where the existing contract or fight transaction is already being processed; the feature
  performs no free-agent-market, roster, promotion, result-history, or Chronicle scan.
- Durable fighter IDs keep duplicate display names separate. Old saves default safely to no active
  contract story, current saves round-trip the key, and resolved returns or revenge fights clear the
  fighter's live pointer while retaining the bounded historical chapter.
- Matchmaking, Fight Night, Storylines, and Fighter Profiles can surface renewal pressure or a first
  fight against the former company from the existing direct story indexes.
- When narrative tracking is disabled for the deterministic A/B regression, contract helpers return
  before story-key lookup. The performance gate therefore includes the complete enabled-path cost.
- The post-Contract-Saga deterministic A/B measured a 5.630-second baseline median and a
  5.668-second narrative median across 12 aggregate weeks per arm: **+0.68% overhead**, comfortably
  inside the hard 5% release ceiling, with identical gameplay and shared simulation RNG state.

### Delivered staff tenure stories

- Player staff now carry an optional direct `staff_story_key` alongside their durable `staff_id`.
  Appointment, three-month and final-month renewal pressure, stalled renewal talks, successful
  renewal, player release, and natural contract expiry remain connected as one Staff Tenure.
- The current chapter appears in Staff Profiles, while the bounded Storylines browser titles the
  chapter with the staff member's saved name and can open its company context.
- Same-name employees remain separate because story identity uses `staff_id`. Current saves retain
  the direct key, legacy staff safely default to no chapter, and repaired threads bound staff IDs,
  display names, and roles.
- Tenures now retain first-of-kind work outcomes rather than reading as contract logs alone. A
  high-value scouting dossier, serious-injury clearance, standout or poorly received card, sellout
  or missed marketing campaign, broadcast breakthrough, and fulfilled fighter promise can become
  a career milestone or setback for the directly responsible department lead.
- Each tenure stores at most 12 distinct contribution categories and a bounded 0–100 staff legacy
  score. Repeating the same achievement type changes neither its beat list nor its score, while
  Staff Profiles and Storylines show the current legacy and distinct-milestone count.
- The existing staff-warning loop emits renewal beats in place. Hiring, renewal, release, and expiry
  emit from their owning actions; there is no second staff-market, company, roster, or history scan.
  Scouting, medical, event and promise milestones likewise emit only at their owning result. Disabled
  narrative tracking exits before resolving a staff lead or reading the direct key.
- The post-milestone paired A/B measured a 12.703-second CPU baseline median and a 12.766-second
  narrative median across 12 aggregate weeks per arm (**+0.49% measured CPU overhead**), with
  identical gameplay and shared simulation RNG state. Both arms run an explicit pre-timing garbage
  collection so deferred app/load cleanup cannot be mistaken for narrative calendar work.

### Delivered feeder pathways

- A fighter moved to a player-funded child promotion now carries one optional
  `feeder_story_key`. Development loans and paid transfers begin a Feeder Pathway; child main/title
  results, parent recall or transfer, the first senior bout, one featured breakthrough, a parent
  championship, departure, and retirement advance or close the same ID-safe chapter.
- Matchmaking and Fight Night can explain a graduate's senior stakes, Fighter Profiles inherit the
  chapter through the participant index, Storylines retains its bounded history, and the child
  operations detail shows the current phase and latest beat.
- Loan, recall, and paid-transfer actions use the existing full domain snapshot. A late narrative
  exception restores rosters, belts, fighter state, parent/child cash and ledgers, Chronicle, story
  state/indexes, and simulation RNG rather than leaving a half-completed move.
- Player and game-AI fight settlement call the same result interpreter only when one supplied
  fighter carries a feeder key; the helper independently returns immediately when both keys are
  empty, before company normalization or story lookup. Active
  handling touches at most the two supplied fighters and their indexed thread; there is no child,
  parent, alumni, Results, Chronicle, or fight-history scan and no recurring calendar pass.
- Current saves round-trip the direct fighter key, legacy fighter rows default to an empty key,
  duplicate display names remain separate, rejected transfers create no thread, and result refs and
  thread collections remain bounded.
- Three clean post-change paired calendar runs retained identical gameplay and shared simulation RNG
  and ranged from −1.94% to +2.06% total narrative CPU variance. The changing sign shows no
  repeatable slowdown, every run passed the noise-tolerant gate, and the zero-regression target
  remains. The inactive feeder path performed no story update in the benchmark seed beyond its
  guarded direct-key branch.

### Delivered breakout runs

- The existing Giant Slayer threshold—an underdog defeating an opponent rated at least eight points
  higher—now opens one ID-safe Breakout Run instead of ending as a disconnected achievement.
- A draw preserves uncertainty; an ordinary follow-up win builds momentum; two follow-up wins, a
  main-event win, or a championship confirm the arrival. One loss creates pressure, while a second
  loss, a failed title test, or retirement supplies a durable ending. A championship upset resolves
  immediately as a complete shock result rather than creating redundant prove-it beats.
- Matchmaking and Fight Night expose the current pressure, bounded AI story value can influence only
  candidate pairs the sporting matchmaker already accepted, Fighter Profiles read the thread through
  the participant index, and Storylines, Chronicle, and annual review retain its evidence and verdict.
- The decisive hook reuses the achievement's already-known upset boolean. Later updates use only the
  fighter's optional `breakout_story_key`, bounded counters, and eight recent result references; no
  ranking, roster, Results, Chronicle, or history scan and no recurring calendar work were added.
- Duplicate callbacks and duplicate names remain independent, current/legacy saves round-trip or
  default the pointer safely, narrative copy consumes no shared RNG, and event rollback restores the
  pointer and exact thread. Focused and clean canonical paired runs measured +0.64% and −1.61% CPU
  variance with identical gameplay and shared simulation RNG state; the changing sign shows no
  repeatable slowdown, and all 30 isolated regression suites pass.

### Delivered career crossroads

- An established fighter now opens one ID-safe Career Crossroads after a third consecutive
  simulated MMA loss. Age 30+, at least 18 professional bouts, or popularity 45+ qualifies a
  fighter whose career has enough history or public weight for the run to matter.
- Draws preserve uncertainty, further losses deepen the decline, and a division move creates a
  visible reinvention whose next result remains consequential. A recovery win, championship return,
  roster release, contract exit, or final-fight retirement supplies a durable ending.
- Matchmaking and Fight Night expose the active pressure, bounded AI story value applies only after
  the sporting matchmaker has accepted a candidate pair, and Fighter Profiles, Storylines,
  Chronicle, and annual review retain the connected evidence and verdict.
- Player, game-AI, and regional result paths emit from the bout settlement already in progress.
  Origin detection reads at most four existing `bout_rating_history` rows for an eligible loser;
  follow-ups use only `crossroads_story_key`, bounded counters, eight recent result references, and
  the supplied participants. There is no recurring calendar, roster, Results, Chronicle, or full
  fight-history scan.
- Current saves round-trip the pointer and malformed thread counters normalize safely; legacy
  fighters default to no active chapter. Duplicate callbacks and display names remain independent,
  narrative copy consumes no shared RNG, division-move retries deduplicate, and event rollback
  restores the exact fighter pointer and thread.
- Three clean post-change paired calendar runs preserved identical gameplay and shared simulation RNG
  while ranging from -19.04% to +2.66% CPU variance. The changing sign shows no repeatable slowdown;
  every run passed the noise-tolerant rejection gate, the complete isolated regression runner passes,
  and zero measurable regression remains the product target.

### Delivered friendship and stablemate aftermath

- One ID-safe Fighter Relationship chapter now connects a first bout between friends or featured
  stablemates to later draws and rematches. A low-tension series can close through competitive
  respect; direct rivalry pressure can fracture the relationship and produce a three-fight verdict;
  former stablemates can settle a camp split in a later meeting.
- Matchmaking and Fight Night expose the active stakes, bounded AI story value applies only after a
  pair passes sporting constraints, and Fighter Profiles, Storylines, Chronicle, and annual review
  retain the same pair-ID evidence and resolution.
- Each participant carries at most four active `relationship_story_keys`. An unrelated bout with no
  current friendship/stablemate link and no saved active key returns before constructing the pair key
  or reading the story index. This preserves post-split continuity without imposing a relationship
  query on every fight, and adds no calendar, roster, Results, Chronicle, or history scan.
- Player, game-AI, regional, and draw settlement share the same interpreter. Stable event references
  deduplicate callbacks, current and legacy fighter rows round-trip or default the bounded key list,
  malformed thread counters normalize safely, same-name fighters remain independent, story copy
  consumes no shared RNG, and event rollback restores both fighter-local lists and the exact thread.
- An initial unconditional story-index lookup failed the paired performance gate and was rejected.
  The fighter-local-key architecture replaced it; three clean paired runs ranged from -3.70% to +1.88%
  CPU variance with identical gameplay and shared simulation RNG state. The changing sign shows no
  repeatable slowdown; the complete canonical isolated runner also passes.

### Delivered meaningful career farewells

- A retirement decision now opens one ID-safe Career Farewell chapter and carries its reason into the
  final booking and result. Matchmaking and Fight Night expose the stakes before the bout; Fighter
  Profiles, Storylines, Chronicle, and annual review retain the final opponent and outcome afterward.
- Automated retirement shows still begin with the existing legal opponent pool. Inside that pool,
  they may prefer a career rival, friend, former stablemate, significant former opponent, champion,
  or fellow veteran while retaining competitive rating, age, division, health, and availability
  constraints. Narrative meaning can reorder a legal list but cannot make an invalid matchup legal.
- Rival, friend, and relationship meaning uses durable fighter IDs. Former-opponent meaning reads at
  most 80 structured `bout_rating_history` rows and requires the opponent ID, so a same-name stranger
  cannot inherit another fighter's history. The selected connection is preserved in the archived
  retirement-show booking reason and the resolved thread.
- The direct `farewell_story_key` round-trips in current saves and defaults empty in legacy rows.
  Legacy careers already awaiting a final fight create and settle the chapter at the owning result.
  Stable result references prevent duplicate beats and Chronicle payoffs; malformed metadata
  normalizes safely; the player event transaction restores the pointer, thread, Chronicle, and RNG
  after a late failure.
- Player, game-AI, regional, draw, no-contest, and other-sport settlement share the same interpreter.
  Ordinary fighters return after the existing `retirement_pending` check, and no new calendar,
  roster, Results, Chronicle, or story-discovery scan was added. Three clean paired 12-week runs
  ranged from -1.96% to +4.44% CPU variance, and the canonical run measured +3.10%, with identical
  gameplay and shared simulation RNG state. The complete isolated regression runner also passes.

### Optional future expansion

- Optional full-world 25-/50-/100-year comparative calendar profiling beyond the shipping paired
  calendar gate and synthetic century-scale storage regression.
- Further authored variations for coach personalities, promotion-rivalry media presentation,
  cross-company competitive events, staff role-specific achievements and failures, executive/staff
  relationships, and hometown legacy epilogues beyond the delivered core paths.

## Completion audit

The expanded core plan is implemented. Narrative state is persisted, identity-safe, bounded, indexed and
updated only by events the simulation already processes. Academy graduation, event settlement and
other narrative-owning transactions restore story state and indexes on a late failure. The
canonical isolated regression suite passes, including the paired real-calendar performance gate,
synthetic century-scale storage audit, save compatibility, UI/profile observation, fight paths,
other sports, media, finance and long-run stability. The two items above are optional depth and QA
extensions rather than blockers for the shipped narrative system.

## Required regression coverage

- Duplicate-name participants remain linked by fighter ID.
- Old saves load with no story threads and continue normally.
- Current saves round-trip active and resolved threads.
- The same event reference cannot add a beat twice.
- Event, media, academy, and finance transaction rollback also restores narrative state.
- Rivalries cool, resolve, and archive without orphaning fighters.
- Career-story acceptance, decline, completion, failure, and title-loss outcomes apply once.
- Narrative wording changes do not alter simulation RNG or results.
- Active and resolved collections remain within their limits over long careers.
- Calendar performance remains inside the stated overhead budget.

## Definition of success

The improved system succeeds when a player can look at a fighter, matchup, promotion, or year and
understand not only **what happened**, but **why it mattered and what it led to**—while the calendar
continues advancing at effectively the same speed as before.
