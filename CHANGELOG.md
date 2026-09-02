# Changelog

## Unreleased

- Hardened generated-fighter style assignment. Every new entrant now finishes generation with a
  supported primary style and a validated non-duplicate secondary style, even if an enrichment path
  supplies a blank or legacy behaviour label; the repair is deterministic and adds no RNG draw.
- Improved between-round coach feedback. Verified head coaches and gyms now deliver a factual round
  read followed by a clear instruction based on knockdowns, damaging offense, gas, repeated moves,
  successful families or control. Balanced, Technical, Excitable and Concise voices present that
  feedback differently without consuming RNG; stablemate bouts do not assign one coach to both corners.
- Added fact-driven camp commentary. Fighters with a real matching Gym receive natural pre-fight
  corner introductions naming their saved camp, coach, location and specialties, plus bounded live
  calls when completed boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning
  evidence matches that Gym's strengths. Promotion, academy, unknown and legacy camp strings are
  described naturally but conservatively without invented coaches or specialties, while opponents
  from the same verified Gym receive one shared stablemate introduction instead of contradictory
  corner claims. Live camp calls are deterministic, capped at one per fighter per round and two per
  bout, and seeded A/B coverage proves they cannot affect fight mechanics, stats, scoring or results.
- Added natural fight-night commentary for all 46 saved fighter traits. Every bout now introduces
  each fighter's trait in broadcast language, while combat-relevant traits receive additional live
  callouts only when recorded targets, moves, positions, damage, gas, timing or fight context support
  them. Contextual calls are deterministically capped at one per fighter per round and two per bout;
  they consume no RNG and do not affect actions, damage, scoring or finish rates.
- Added one exclusive authored finisher for every supported MMA style. Striking disciplines receive
  style-native knockout techniques, wrestlers receive causal ground-and-pound stoppage sequences,
  and submission styles receive distinct chokes, joint locks and leg locks. Primary or secondary
  style ownership is required even when a move is saved as a signature. All 18 finishers appear in
  the representative 880-fight corpus and only identify the technique beneath an already-resolved
  KO, TKO or submission, so no damage, finish or stoppage roll was added.
- Added one exclusive authored combination for every supported MMA style. Boxing, kickboxing, Dutch
  kickboxing, Muay Thai, karate and taekwondo receive distinct ordered striking chains; Sanda,
  wrestling, catch wrestling, jiu-jitsu, Luta Livre, sambo, judo and the mixed disciplines receive
  style-native strike-to-entry, takedown, transition or submission-threat sequences. All 18 retain
  ordered component evidence, are available through a fighter's primary or secondary style, and are
  excluded from unrelated styles. The 880-fight representative report observes every addition with
  no dominance, legality, style-distance or reachability diagnostic; no broad action, damage or
  finish roll was added.
- Added twelve one-time visible-damage milestones across persistent head, body and leg trauma,
  including facial marking, torso bruising, guarded movement, leg welts, weight shifts and a
  visible limp. Exact structured cuts now name their recorded location and describe heavy bleeding
  or threatened vision only when those facts exist. These deterministic lines survive Broadcast,
  appear chronologically in replay analysis and consume no fight RNG or add damage/stoppage rolls.
  Post-fight recovery now also consumes the completed bout's trauma before career-stat cleanup;
  a 256-fight gate found 1,043 damage events with complete factual narration and Broadcast retention
  while the locked finish and action baselines remain the mechanical authority.
- Expanded the ground catalogue from 117 to 140 moves without changing grappling resolution. Six
  position-specific striking chains now distinguish guard, half guard, side control, mount, back
  control and turtle offense; five passing/climbing transitions, four sweeps, four recoveries/get-ups
  and four retention/control rides add further ground identity. Twenty-two additions appear in the ordinary
  880-fight representative corpus, while the turtle wrist-ride chain remains legally reachable in
  its specialist state. Ground-strike components reconcile at realistic volume and mounted TKO
  narration follows the causal registered move. The exact finish and broad-action baselines remain
  the authority, so none of this content adds a strike, pass, sweep, escape or finish roll.
- Expanded the standing technique catalogue from 101 to 117 moves. Ten new combinations add
  body-to-head boxing, stance shifts, pressure flurries, hand-to-kick chains and punch/elbow/knee
  sequences; six uncommon finishers add uppercuts, corkscrew crosses, spinning backfists, axe kicks,
  jumping front kicks and switch flying knees. These identities are selected after broad exchange
  resolution and never add a landing or finish roll, preserving the exact 2,319/633/731 frozen
  finish/KO/TKO corpus. Every addition appears in the representative 880-fight report, combination
  components reconcile at realistic volume, and causal registry moves now replace contradictory
  legacy strike names in both sudden and ordinary KO/TKO finish narration.
- Made MMA play-by-play reflect who the fighters are without changing what the fight engine decides.
  Standing calls now rotate by the recorded technique, relevant detailed strength and style family,
  with broader survival, clinch, transition, escape and damage language instead of a few repeated
  resets. Ground sequences now preserve the actual submission technique, named escape defense,
  top/bottom ownership, live position and natural escape consequence; referee stand-ups are recorded
  as officiating resets rather than false fighter escapes. Broadcast duplicate limiting now applies
  to important position calls as well as routine lines. A 256-fight permanent gate and 2,048-fight
  extended audit verify profile coverage, submission continuity and low repetition while the frozen
  result and action baselines remain the mechanical authority.
- Completed the finish-system follow-up audit without replacing the accepted fight balance. The
  canonical corpus remains exactly 2,319 finishes (60.39%), 633 KOs (16.48%) and 731 TKOs
  (19.04%); competitive bouts independently remain inside the 48-54% finish and 15-19%
  submission bands, while 19.55% of five-round finishes occur in rounds four or five. Permanent
  gates now reject lost doctor/injury reachability or deficient late-round finishes. Body- and
  leg-kick knockdowns no longer masquerade as injury stoppages, serious-cut doctor checks remain
  between-round only, and authored submission, doctor, injury, head-kick and walk-off endings now
  survive the final commentary sequence. Finish, KO, submission and highlight-KO method families
  are centralized so career stats, awards, recovery, excitement and contractual bonuses agree.
- Restored the visible fight story in the default Broadcast feed without changing fight resolution.
  Landed standing offense, completed takedowns, landed ground strikes, passes, sweeps, reversals and
  escapes are now prioritised during round compaction, while identical wording remains capped and
  condensed notes count the actual omitted standing,
  standing-striking, takedown, ground-control and ground-striking lanes. Successful sweeps that retain the same named position
  now use the recorded top/bottom ownership change instead of being miscalled as denied. The
  canonical release runner also verifies the frozen 3,840-fight action-frequency baseline alongside
  the unchanged 60.39% finish, 16.48% KO and 19.04% TKO gates.
- Made Fight Night audio continuous across the full live card. A loop-safe, crossfaded arena bed now
  stays open beneath walkouts, round bells and factual reactions instead of reopening the Windows
  output for every stretch of crowd ambience; later-round bells use the mastered crowd pack, and
  closing the live viewer cancels its bed and in-flight reactions. Knockdowns and finishes retain a
  reserved reaction slot, while decision and card-complete calls no longer suppress one another.
  Live audio stop events and audio-only system entropy are excluded from event rollback snapshots so
  an active audio session cannot prevent a completed card from settling.
- Expanded the fact-driven MMA broadcast without changing combat resolution. Landed, blocked,
  slipped, countered, transitioned and escaped exchanges now have deterministic wording variation;
  recorded signatures, technique mastery, stance lanes, plan changes, momentum, damage, camps,
  championship stakes and rivalries can add context only when the trace or bout data proves it.
  The live viewer can switch between Broadcast and Detailed feeds in place, shows the selected
  voice, separates rounds more clearly and highlights knockdowns and finishes. New commentary
  quality gates reject excessive repetition, missing or contradictory facts, broken finish
  continuity, duplicate results, technical-suffix leakage and any one-bout change to the accepted
  3,840-fight finish/KO/TKO calibration.
- Reworked MMA commentary as a presentation-only three-phase upgrade. Fight Night now defaults to a
  compact Broadcast feed that suppresses repeated low-value calls while preserving the complete
  stored transcript, every structural/evidential line, sealed-scorecard flow, and Detailed review.
  Exchange prose now comes from the recorded move, target, defense, outcome and position; finish copy
  follows the actual final technique; corner advice cites visible fight evidence; and persistent
  Balanced, Technical, Excitable and Concise voices change wording without changing fight mechanics.
- Improved full-world calendar performance without reducing simulated activity. AI promotions now
  compute their card day and fatigue policy once per readiness pass, fight commentary reuses the
  head-to-head result already stored in bout state, and regional intake batches reuse one collision
  set instead of rescanning the world for every recruit. Promotion monthly reviews are now assigned
  to stable, evenly distributed weekly groups; the sixteen regional circuits retain one card and
  one development review per circuit each month without a month-boundary card pile-up.
- Added named defensive technique identity beneath every exchange. Eighteen registry-backed defenses
  cover guards, parries, evasions, kick checks/catches, sprawls, whizzers, cage frames, underhook turns,
  hand fighting, wall walks, submission escapes and technical scrambles; traces and release reports
  retain the attempted defense without changing whether the calibrated broad action succeeds.
- Added persistent technique mastery for offensive moves and defenses. Camps develop focus-aligned
  techniques, sufficiently mastered moves can become signatures, academy prospects develop and carry
  mastery into their professional careers, and veteran mastery declines gradually after the athlete's
  prime. Profiles and academy reports expose the strongest techniques; legacy saves default safely.
- Added deliberate in-fight stance switching and defense/position-aware branching sequences. Skilled
  switchers and adaptable fighters can change side from plan and matchup evidence, while authored
  follow-ups can select an alternate legal branch after frames, evasions or escapes. Every switch and
  branch is retained in the trace and remains one ordinary broad action.
- Added a per-round replay analysis explorer showing effectiveness, top moves, named defenses, sequence
  paths, stance changes and corner-plan changes. Expanded the shipped authored-signature cohort from 40
  to 114 fighters across 13 styles, including natural homes for all 17 legal specialist techniques that
  are rare in the representative synthetic sample, and strengthened their legal selection priority. The locked 3,840-fight rates remain
  exactly 60.39% finishes, 16.48% KO and 19.04% TKO.
- Deepened the technique layer without changing the calibrated broad outcome model. Complete fights
  now retain elite failed-shot/front-headlock, standing-back-control and leg-entanglement states;
  registry energy, miss risk and counter vulnerability shape later move choice; successful authored
  follow-ups create bounded two-tick sequences; and all 18 styles have explicit technique-tag identities.
  Stance lanes and striker/grappler matchups also influence legal technique selection, while corners
  evolve plans from repeated opponent moves and effective move families with evidence and confidence.
- Expanded the shipped authored-signature cohort from nine to 40 fighters across 11 styles. The
  Simulation Lab now reports top moves, completed sequences, signature effectiveness, average technique
  load/risk, stance-lane usage and fight-plan evolution. The general release report has grown to 880
  fights with distinct style-distance and open/closed/switch-stance checks, while a separate 720-fight
  specialist-transition report proves the rare positions and their legal follow-ups occur in complete
  bouts. The frozen 3,840-fight finish percentages and competitive finish converter remain unchanged.
- Completed the fight-move release audit. A deterministic 840-fight report now samples every supported
  style plus behaviour, tier and stance, and checks registry reachability, dominance, mismatch-only use,
  counter/position/target legality and energy bounds. All 101 moves are reachable and the safety checks
  are clean; the frozen 3,840-fight result and action baselines remain exact. Turtle breakdown and sit-out
  traces now use their real broad actions. Standing-skill development preserves its prior per-skill
  exposure after the three-skill boxing expansion, and the Database Editor audit safely handles sparse
  legacy skill overrides without mutating them on view.
- Expanded Fight Night and analysis presentation around the exact recorded technique. Calls now label
  target, defense and meaningful follow-up in text; completed rounds show bounded move-family
  effectiveness, Quick Fight Simulator results summarize each corner's main families, and fighter
  statistics retain career family/signature totals. Raw trace counts reconcile with every summary,
  official cards remain sealed, and presentation consumes no mechanics RNG.
- Added bounded tactical move selection beneath the existing fight plans. Prior public trace can make
  body/leg work and feints open later families, repeated techniques become less selectable, and
  adaptable counter fighters exploit real patterns only inside a counter window. Every choice retains
  explainable selection reasons, bout-local read counts cap at 12, and no new RNG or direct finish
  modifier was added.
- Added stable fighter signature moves. The Database Editor exposes three registry-backed selections,
  nine authored stars have first-cohort move sets, and skill-supported generated fighters receive
  deterministic signatures without RNG. Legal signatures are preferred but never guaranteed; traces,
  post-fight telemetry and career totals track attempts, effective uses and finishes. Unknown future
  IDs degrade safely, duplicate-name fighters remain independent, and outcome calibration is unchanged.
- Expanded the MMA registry to 101 moves with ground-strike chains, pressure passes, mount/back/turtle
  transitions, sweeps and reversals, major choke/arm-lock families, and legal ankle/knee/heel/toe-lock
  attacks. Every submission now validates its positional attack path and explicit failed-attempt
  outcomes; major grappling styles produce distinct legal technique mixes without adding a redundant
  submission-chaining rating or changing finish conversion.
- Expanded the MMA registry to 77 techniques with over-under, underhook and Thai-plum entries; cage
  pummels and exits; mixed shot entries; trips, throws, knee taps and high-crotch finishes; re-shots,
  whizzers, mat returns, standing rides, escapes and front-headlock go-behinds. Every takedown now
  validates an entry family, legal defenses and possible finish positions, with distinct Wrestling,
  Judo, Sambo and Sanda move mixes and unchanged calibrated outcomes.
- Expanded MMA standing technique coverage to 54 registered moves. Kicks now retain target, lead/rear
  side, range band and legal defensive families; new options include calf kicks, teeps, side/switch/
  question-mark/wheel/spinning kicks, punch-kick chains, intercepting/flying knees and step-in/spinning
  elbows. High-risk moves are skill-gated and uncommon, five major kicking styles produce distinct
  move mixes, and the exact 60.39% / 16.48% / 19.04% calibration remains unchanged.
- Added three distinct MMA boxing ratings—combination punching, body punching and counter timing—
  with deterministic legacy-save derivation, generation, development and editor/profile support.
  Seven new boxing sequences include double-jab-cross, cross-hook-cross, body/head changes and three
  counter-only returns. Technique skill now governs which legal sequence appears, counter moves need
  a real counter window, and broad damage/gas resolution remains unchanged at the exact 60.39% /
  16.48% / 19.04% calibration.
- Added the canonical MMA move registry and trace contract. The initial 32 named punches, combinations,
  kicks, entries, takedowns, clinch actions, ground transitions and submission families now retain
  stable IDs, legal positions, targets, skill/defense bundles, risk metadata and follow-ups beneath
  the existing calibrated actions. Technique selection is deterministic and uses an explicit generic
  fallback; broad action resolution and the 60.39% / 16.48% / 19.04% outcome calibration remain unchanged.
- Completed the move-expansion foundation. Jiri Prochazka and Brandon Royval now retain supported
  Kickboxer/BJJ styles, Lito Adiwang and Kevin Belingon use the supported Sanda identity, and shared
  universe validation rejects unsupported MMA styles, profile styles, secondary styles, traits and
  behaviours. Legacy Wushu/behaviour-as-style saves normalize safely. New universes deterministically
  give roughly 65% of fighters a distinct supported secondary discipline, displayed as a mixed style
  and contributing a bounded 35% action-selection influence. A new 3,840-bout action baseline freezes
  pre-expansion frequency and effectiveness; headline calibration remains exactly 60.39% finishes,
  16.48% KO and 19.04% TKO.
- Added a phased fight-engine moves, skills and combinations roadmap. It begins with the confirmed
  four-record unsupported-style repair and validator gap, then separates technique identity from
  style and behaviour before expanding boxing, kicks, clinch, wrestling, ground work, submissions,
  fighter signatures and tactical chains. Every phase retains the accepted 60.39% finish, 16.48% KO
  and 19.04% TKO calibration without changing competitive finish conversion.
- Repaired the shipped universe's source identity coverage. All 1,534 canonical MMA fighters now
  carry durable source IDs, all previously blank birthplace/hometown pairs have deterministic
  provenance-marked regional data, and the four broad-reach media packages now serve Russia,
  South Korea, the Middle East, and Africa. Legacy custom databases still receive stable IDs only
  in memory until explicitly saved, while Database Editor additions and duplicates mint fresh IDs.
- Added a narrative-system audit and phased development plan covering rivalries, title chases,
  career journeys, injuries, academies, contracts, promotion histories, relationships, and combat
  sports. The plan makes calendar speed a release constraint: narrative updates must be event-driven,
  indexed, bounded, transaction-safe, RNG-isolated, and verified against long-career performance
  budgets rather than adding a new whole-world weekly scan.
- Implemented the first narrative-system phase. Rivalries, title chases, championship reigns, title
  losses, and redemption runs now advance persistent ID-safe story threads directly from existing
  simulation events; matchmaking and Fight Night explain why a connected bout matters, while a new
  Storylines browser separates active and resolved chapters. Thread/beat limits, direct-key lookup,
  deduplication, legacy-save defaults, transaction rollback, and presentation-RNG isolation prevent
  narrative history from becoming a second simulation cost. Champion-retention title losses no
  longer receive success rewards, declined veteran runs cannot be penalized twice, and homegrown
  title projects receive at most one backed extension.
- Extended persistent narratives through serious-injury treatment, recovery clearance, return-fight
  payoff and medical retirement; contracted comeback/farewell commitments; academy graduate to
  homegrown champion lineage; and contract-promise fulfilment or breach. Fighter Profiles now read
  connected chapters from the direct participant index. Added a deterministic 12-week A/B calendar
  regression that requires identical gameplay and shared-RNG outcomes while enforcing the narrative
  overhead budget. Story status counts are now maintained incrementally, so routine writes remain
  constant-time and full bounded pruning occurs only when a hard active/resolved limit is exceeded.
- Expanded narrative memory across weight-cut turnarounds and division reinvention, camp-fit reviews
  and gym moves, ID-backed friendship/stablemate bouts, AI promotion strategy and ownership eras,
  other-sport contender/title/retirement careers, MMA transitions, and crossover-superfight results.
  Fighter Profiles now assemble a unified bounded Career Timeline lazily from direct story and
  fighter-local indexes. End-of-year awards select and archive at most eight defining current-year
  threads instead of reconstructing historical results. Friend relationships now persist a stable
  fighter ID and only migrate legacy names when one unambiguous loaded-world match exists.
- Added academy mentorship through graduation, fit/attention-driven gym splits, hometown-hero market
  milestones, talent-war signings, and bounded story-aware AI matchmaking. AI story value is cached
  only for already-credible candidate pairs and cannot bypass readiness, division, ranking, title,
  or stale-rematch rules. Replaced the noisy one-shot performance gate with three alternating paired
  samples; repeated 12-week aggregate runs remain inside the no-slowdown budget, with the current
  full-suite measurement at +2.69%. Added a synthetic 25-/50-/100-year
  storage regression that kept indexed update time flat and the current century payload below 800 KB.
  Academy graduation rollback now restores story threads and rebuilds their transient indexes when
  a late graduation hook fails.
- Expanded narrative scope with scored Promotion Rivalry chapters. Contested contract signings,
  academy recruitment and sanctioned superfights now build a deduplicated two-year series between
  known companies, with decisive and cycle-end resolutions but no recurring promotion scan.
  Significant fighters also retain room-specific coaching-loyalty chapters through arrivals,
  breakthroughs, title wins, setbacks and gym splits. Academy mentorship remains active after
  graduation through a persisted prospect ID and can resolve with the graduate's senior title win.
  The current canonical post-expansion paired calendar gate measured +2.69% overhead across 12 aggregate
  weeks, inside the 5% budget; its disabled arm exits before the new story-key work so the
  comparison includes the real helper cost.
- Expanded Hometown Hero stories beyond popularity thresholds. Main-event and title bookings in an
  established fighter's hometown or birth market now announce a homecoming, expose its stakes in
  fight context, and settle as a triumph, setback, heartbreak, unresolved result, or home-title
  payoff. Player and AI paths emit these beats from existing booking and regional-settlement events;
  the post-homecoming performance gate measured -2.28% overhead and added no calendar scan.
- Added persistent Contract Sagas connecting renewal pressure, stalled or broken talks, expiry,
  release, rival-company signings, returns and cross-company revenge fights. A fighter carries one
  direct optional thread key, duplicate names remain ID-safe, and legacy/current saves default and
  round-trip correctly. Contract helpers exit before story-key lookup when narratives are disabled,
  and the narrative plan now treats calendar-speed limits as an explicit release-blocking gate. The
  current deterministic paired test measured +0.68% median overhead with identical world/RNG state.
- Added ID-safe Staff Tenure stories connecting appointment, renewal warnings, stalled talks,
  renewal, release and natural expiry. Staff Profiles expose the current chapter and Storylines use
  the saved staff identity, while legacy staff default safely to no active key. Hooks reuse existing
  staff actions and the existing warning loop rather than adding calendar work; the post-change
  canonical paired test preserved identical world/RNG state.
- Expanded Staff Tenure into performance-backed staff careers. First-of-kind scouting dossiers,
  medical clearances, event matchmaking results, marketing outcomes, broadcast breakthroughs and
  fulfilled fighter promises now create bounded achievements or setbacks for the responsible staff
  lead. Profiles and Storylines expose a 0–100 legacy score and distinct milestone count; duplicate
  outcomes cannot farm beats or legacy. The post-expansion paired gate measured +0.49% CPU overhead
  with identical world/RNG state. Both arms now collect deferred startup garbage before timing so
  unrelated load cleanup cannot create a false calendar regression.
- Hardened the narrative performance gate after a Windows scheduling pause produced contradictory
  wall-clock results on unchanged code. The same alternating paired A/B now gates on process CPU
  time—the simulation work controlled by the game—while still reporting wall-clock medians for
  diagnosis; the existing 5% proportional ceiling and world/RNG equivalence checks remain unchanged.
- Added persistent Feeder Pathway careers for player-funded child promotions. Development loans and
  paid transfers now follow the same fighter through child main/title results, recall or promotion,
  parent debut, featured breakthrough, parent championship, departure, or retirement. Matchmaking,
  Fighter Profiles, Storylines, and the child operations screen expose the connected chapter by
  durable fighter ID. Rejected moves create no story, late hook failures restore rosters, belts,
  cash, ledgers, Chronicle, story indexes, and RNG, and ordinary fight settlement exits after two
  direct key checks without scanning rosters, alumni, Results, or history. Three post-change paired
  calendar runs retained identical gameplay/RNG state and ranged from −1.94% to +2.06% total
  narrative CPU variance, showing no repeatable slowdown and remaining inside the noise-tolerant
  rejection gate. The full 30-suite isolated regression run passes.
- Turned the one-shot Giant Slayer achievement into a persistent Breakout Run. An eight-point
  underdog win now carries prove-it pressure into draws, follow-up wins, setbacks, main events,
  title tests, championship arrivals, retirement, or a stalled run. The same ID-safe chapter appears
  in matchup context, Fighter Profile timelines, Storylines, annual review, Chronicle, and bounded AI
  matchmaking intent. The result hook reuses the achievement's already-computed upset flag, performs
  only direct-key lookups, consumes no simulation RNG, and added no calendar scan. Focused and clean
  canonical paired runs measured +0.64% and −1.61% CPU variance with identical gameplay/RNG state,
  showing no repeatable slowdown; all 30 isolated suites pass.
- Added ID-safe Career Crossroads for established fighters after a third consecutive simulated MMA
  loss. The chapter carries decline pressure into draws, deeper losing runs, division reinvention,
  recovery or championship wins, roster release, contract exit, and final-fight retirement; its
  current stakes appear in matchmaking, Fight Night, Fighter Profiles, Storylines, Chronicle,
  annual review, and bounded AI booking intent. Player, AI, and regional result hooks reuse the
  bout record already being settled, while inactive paths use direct empty-key checks and a
  four-result bounded origin lookup rather than a calendar or history scan. Current/legacy saves,
  duplicate callbacks and names, event rollback, and presentation RNG are covered. Three clean paired
  calendar runs ranged from -19.04% to +2.66% CPU variance with identical gameplay/RNG state, showing
  no repeatable slowdown and passing the noise-tolerant release gate; the complete isolated regression
  runner also passes.
- Expanded Fighter Relationship stories beyond a one-fight headline. Friends and featured
  stablemates now carry the first result into an unresolved draw, a respectful series conclusion,
  rivalry-driven fallout, a three-fight verdict, or a former-stablemate rematch after changing camps.
  Matchmaking, Fight Night, Fighter Profiles, Storylines, Chronicle, annual review, and bounded AI
  intent read the same pair-ID thread. Active keys are stored only on the involved fighters, capped
  at four, so unrelated bouts return before constructing a pair key or querying the story index;
  draws and regional cards now use the same relationship interpreter. Duplicate callbacks/names,
  legacy/current saves, thread normalization, RNG purity, and event rollback are covered. A rejected
  unconditional-lookup version failed the performance gate and was replaced; three optimized clean
  calendar runs ranged from -3.70% to +1.88% CPU variance with identical gameplay/RNG state, showing
  no repeatable slowdown. The complete isolated regression runner also passes.
- Turned retirement decisions into persistent Career Farewell chapters. Final-fight stakes now
  surface in matchmaking and Fight Night; automated retirement shows prefer an already-eligible
  career rival, friend, former stablemate, significant ID-backed former opponent, champion, or fellow
  veteran without expanding the candidate pool. The result retains the final opponent, relationship,
  outcome, Chronicle payoff, and both fighter IDs across MMA, AI, regional, draw, no-contest, and
  other-sport paths. Current and legacy saves, duplicate callbacks and names, normalization, RNG
  purity, and player-event rollback are covered. Three clean paired calendar runs ranged from -1.96%
  to +4.44% CPU variance, and the canonical run measured +3.10%, with identical gameplay/RNG state,
  no new recurring simulation pass, and the complete isolated regression runner passing.
- Added the fight-engine preservation foundation for the staged realism roadmap. A UI-free audit
  harness now freezes 3,840 fixed-seed bouts across competitive low/mid/high tiers, mismatches,
  styles, behaviours and bout lengths; records per-exchange position, action, damage and stat
  evidence; publishes confidence intervals; classifies every detailed fighter attribute as a direct
  fight input or documented pre-fight input; and restores caller RNG and fighter state. The new
  dedicated regression suite locks the existing 59.64% total finish rate, 15.70% KO rate, 19.66%
  TKO rate and 23.46% combined submission-family rate before later engine phases begin. MMA fights
  now also retain a structured `FightResult` containing per-exchange position, action, gas, damage,
  strike, takedown, submission and knockdown deltas plus scorecards, metrics and a terminal official
  result; the legacy result tuple remains unchanged. Presentation now uses a bout-local random
  stream, mechanically meaningful fouls are separated from atmospheric flavour, and changing the
  commentary phrase bank cannot alter a result. Combat, officiating and presentation now have
  explicit bout-local streams; exchange commentary renders through the recorded trace, whose events
  classify outcomes and retain hurt, cut, knockdown, position, control and stoppage evidence. The
  post-separation 3,840-bout audit remains at 59.79% finishes, 16.25% KO and 18.98% TKO without
  changing competitive finish conversion.
- Rebuilt MMA judging around round-local trace evidence. Judges now apply effective striking and
  grappling first, effective aggression only when offense is close, and control only when both are
  close; gas, home, experience, pressure and discipline no longer score by themselves. Clear
  dominance cannot be overturned by ordinary variance, evidence-backed 10-8 and rare 10-10 rounds
  are supported, and cards expose unanimous/split/majority decision and draw verdicts while keeping
  canonical save-compatible methods. Repeated fouls can produce a visible round-specific deduction.
  The post-judging corpus remains at 59.32% finishes, 16.25% KO and 19.24% TKO.
- Separated transient hurt from lasting head, body and leg trauma. Defensive success, survival and
  corner work can now settle hurt and restore bounded gas without healing accumulated damage. Body
  damage taxes sustained output, leg damage impairs kicks/shots/movement, and head trauma degrades
  reactions. Cuts retain location, severity, bleeding, swelling and vision risk; doctor stoppages
  identify that evidence, and the same Fight Night metrics now extend medical layoffs and severe
  injury holds. The calibrated corpus passes at 60.39% finishes, 16.48% KO and 19.04% TKO.
- Added a 356-bout full-system fight-engine regression spanning every fight plan, major style
  matchups, 3/5/6/7-round rules, extreme ratings and duplicate-name fighters. It reconciles every
  exchange with the final box score, position path, stoppage, scorecards and judging evidence. The
  audit found and fixed knockdowns being classified and scored against the defending corner,
  No Contest audit rows retaining winner/loser IDs, and survival erasing reported head trauma. A
  separate permanent trauma channel fixes the evidence without changing calibrated mechanics: the
  3,840-bout audit remains exactly 60.39% finishes, 16.48% KO and 19.04% TKO.
- Added ID-safe pre-fight plans for both player and game-AI MMA bouts. Matchmaking and the booked-card
  editor offer Balanced, pressure, counter, wrestling, cage, body, leg, submission, conservation,
  lead-protection and finish-chasing instructions. Plans alter action mix, targets and energy rather
  than overriding results; defended attacks create real counter windows, and adaptable corners can
  change approach between rounds using only visible fight evidence. Existing scheduled cards load as
  legacy Balanced bouts. The frozen 3,840-fight audit remains unchanged at 60.39% finishes, 16.48%
  KO and 19.04% TKO, without changing competitive finish conversion.
- Upgraded each MMA trace beat into a coherent exchange containing its setup, attack, explicit
  defensive response, counter opportunity or consumption, and follow-up. Failed attacks can now be
  audited as the source of a real counter window; fixed-seed samples confirm counter plans produce
  more successful counters than comparable pressure plans. Strike combinations retain each ordered
  attempted/landed component with a hard per-exchange bound. These additions consume no extra combat
  randomness, and the locked corpus remains at 60.39% finishes, 16.48% KO and 19.04% TKO.
- Added a validated MMA positional state machine. Failed shots, front headlocks, turtle, standing
  back control and leg entanglements now have legal ownership and escape routes alongside cage
  takedowns, re-shots, mat returns, wall get-ups and submission-defense consequences. Brief scramble
  positions are retained in the exchange path without pretending they were consolidated into the
  following beat. Impossible ownership and illegal transitions fail immediately in focused tests;
  wrestler, submission-specialist and striker samples follow distinct paths. The full audit remains
  unchanged at 60.39% finishes, 16.48% KO and 19.04% TKO.
- Completed the referee and foul-consequence pass without recalibrating finishes. Explicit referee
  profiles preserve the existing stoppage and stand-up values; foul records now include warnings,
  recovery time, intent and the responsible official, with a three-incident cap and scorecard
  deductions. Severe accidental fouls can produce a rules-correct No Contest or technical decision,
  and No Contests leave records, Elo and titles untouched across player, AI, academy and independent
  cards. Visible trauma also drives bounded medical, confidence and recurrence consequences, while
  early/late stoppage review flags never rewrite the official result.
- Finished the fight-engine cleanup and tuning migration. Removed two unused finish helpers, added
  versioned and validated fight-setting defaults, and moved Gate Multiplier into a separate
  versioned business setting with automatic old-save migration. Simulation Lab now identifies which
  controls affect mechanics and which affect business only. The accepted 3,840-bout calibration
  remains exactly 60.39% finishes, 16.48% KO and 19.04% TKO.

This development cycle expands the playable Combat Sports and Fighting Academy management loops,
turns Scouting into a persistent evidence-led department, hardens fighter identity and Fight Night,
and adds card-specific event economics backed by a broader release regression suite.

### Finance and Company Growth

- Expanded Finance into a long-career operating dashboard. A new History & Outlook page retains up
  to 30 annual revenue/cost/profit summaries, breaks the last 12 months of event revenue into ticket,
  broadcast, sponsor and merchandise streams, records monthly roster size and purse exposure, and
  projects milestone cash/event timing without pretending that popularity, stability or safety
  growth is predictable. Compact annual and roster snapshots remain useful after detailed weekly
  transaction retention rolls forward.
- Added eight persistent late-game strategic investments across facilities, international operations,
  staff departments and prestige projects. Each has an explicit milestone/popularity/cash gate,
  capital price, monthly upkeep and bounded event effect covering medical cost, attendance,
  broadcasting, sponsorship or merchandise. Purchases and upkeep use canonical finance transactions,
  existing saves default safely to no projects, and Finance exposes total first-year commitment and
  current monthly strategic burn before approval.

### Combat Sports

- Reworked Boxing and Muay Thai as distinct rulesets instead of presentation variants of one
  striking calculation. Boxing now scales non-title contests through six, eight, and ten rounds,
  uses 12-round title fights, records knockdown-led 10-8/10-7 rounds, and returns three official
  cards with unanimous, split, majority, and draw verdicts. Standard Muay Thai runs three rounds,
  title bouts run five, and its judges prioritize effective kicks, knees, elbows, dumps, balance,
  and clinch control; Lethwei remains a five-round knockout-first ruleset. Replays retain official
  cards and round evidence, while decision variants no longer inflate finish statistics.
- Completed the ownership-and-economics foundation for Boxing, Kickboxing, Muay Thai/Lethwei,
  Wrestling, and BJJ child promotions. Persistent player rosters and booked corners now repair to
  fighter IDs, including same-name athletes; flagship prospects use the same negotiated term,
  purse, exclusivity, and finance workflow as private-market recruits. Contracted purses are paid
  during card settlement, expired deals receive one renewal window before the athlete returns to
  the flagship, and expired athletes cannot be booked. Player cards now keep their own numbering
  and history, are limited to one per month, and write complete, collision-resistant finance
  metadata without incrementing the AI circuit. Added a focused Combat Sports regression suite.
- Fixed remaining Combat Sports identity leaks. Championship ownership, defenses, vacancies,
  lineage, season statistics, records, awards, Hall of Fame entries, card rotation, and world-roster
  repair now distinguish same-name athletes by `fighter_id`. Fight-night readiness commentary reads
  the ID-keyed telemetry instead of displaying false zeroes, and one-fight independent opponents no
  longer pollute permanent circuit records or win annual awards.
- Expanded player-owned Combat Sports into a future-event management loop. Matchmakers can now
  schedule a built card for a future month/week, choose Local, Regional, or Arena production,
  set a marketing budget, and see the same revenue/cost/profit forecast used at settlement.
  Scheduled cards persist across saves, reserve their athletes from smart cards, execute when the
  calendar enters their week, produce a completion Inbox item and replay, and can be cancelled from
  the new Upcoming Scheduled Cards panel. Contract, medical, duplicate-date, and one-card-per-month
  checks prevent invalid or overlapping shows.

### Fighting Academy

- Rebuilt the Fighting Academy into a long-term youth-development system. Prospects can follow
  measurable 4/8/12-week blocks with objectives and end-of-block reports; compete from local through
  international level with opponent quality, strength of schedule, two-bout tournaments and amateur
  titles; and develop persistent personalities, satisfaction, loyalty, promises and departure risk.
  Graduation now supports the main roster, a 12-month MMA developmental deal, player combat-sport
  divisions, or a regional feeder with retained matching rights that can be exercised from Alumni.
  Major rival promotions operate persistent regional youth programmes, graduate their own cohorts
  and compete for unsigned leads.
  The Academy page exposes the complete workflow plus a Rival Academies view. Null-shaped old saves
  repair safely, every identity-bearing ledger uses durable IDs, the live four-week card clock is
  accurate, and training fatigue remains consequential. Tournament entry, graduation and matching-
  right signing now roll back cash, finance, roster, belt, prospect and RNG state after a late
  failure; malformed schema-six prospect values are normalized, and rival development can no longer
  reduce a prospect's stored rating. Stability coverage exercises every phase and these failure paths.

### Fighter Profiles and Scouting

- Hardened fighter Profiles as observational, identity-safe views. Unscouted portraits no longer
  print exact ratings or private style details, duplicate-name fighters retain the correct employer,
  championship, opponent and W/L history, and distinct same-labelled archives remain searchable.
  Reopening a Profile now preserves its active window, laptop-sized displays keep the fixed action
  footer reachable, and child-sport Profile queries no longer initialize titles or rewrite rankings.
  Spectator Mode and stale Profile windows cannot sign, transfer, or move fighters after ownership
  changes; contract submission revalidates the live owner, and expired scouting reports stay hidden
  when negotiation opens. New championship history records retain durable fighter IDs.
- Made championship administration and belt history ID-first. Administrative belt awards,
  vacancies, previous-champion references, and history rows now retain `fighter_id` alongside
  display names so a same-name athlete cannot inherit another fighter's reign or Profile lineage.
- Hardened scouting across saves, staff assignments, report upgrades, and the recruitment UI.
  Ambiguous legacy name-keyed reports no longer leak intelligence between same-name fighters, and
  legacy migration no longer consumes simulation RNG or refreshes old dossiers as current. Scouts
  and their workloads use durable IDs, null-shaped old-save collections repair safely, and replacing
  a report preserves the last completed intelligence through cancellation or an expired observation.
  Talent searches can rediscover unusable reports, retain their ranked lead list, and open the
  headline fighter. The Scouting screen now reflows its controls at laptop widths, scrolls assignment
  history in both directions, shows real completion dates, and exposes cancelled/expired filters.
- Deepened scouting into an evidence-led recruitment department. Pending assignments no longer leak
  conclusions derived from hidden ratings, automatic dossiers are limited to one discounted paid
  assignment per week, and talent searches rank existing fighters without manufacturing new market
  supply. Searches now accept age and style constraints plus an ability, potential, value,
  marketability, or roster-need priority. Standard, faster paid Priority, and quarterly Ongoing
  briefs create explicit capacity choices, while thin pools return labelled Near Matches;
  completed work builds regional knowledge, durable dossier history, and deduplicated watchlist
  alerts. Live observations retain opponent, result and fight metrics, prior intelligence remains
  visible during upgrades, ageing reports lose certainty after six months, and exact current ratings
  require a high-confidence repeated full evaluation. Established academy networks now close when
  their assigned scout's contract expires instead of extending that contract forever.

### Fight Night and Simulation

- Hardened the watched Fight Night experience end to end. A live card is now a single guarded
  session, so reopening Watch cannot rerun press conferences or weigh-ins, active bouts cannot be
  skipped accidentally through the next-fight control, full-card skips require confirmation, and a
  failed transactional settlement remains retryable. Exact judge cards stay sealed until the
  result while public round telemetry continues to update. Duplicate-name corners retain distinct
  metrics, winner identity, projected records, and replay labels. Archived replays preserve their
  original location and event economics, while compact live layouts and the scrollable end-event
  report keep controls reachable on laptop displays.
- Fixed fight-state identity and response tracking: clinch controllers now retain their private
  per-bout slot, only landed strikes build unanswered-offense streaks, meaningful grappling and
  positional responses clear those streaks, and the horn resets them. Same-name tournament
  entrants now resolve and restore fatigue by identity, including alternate replacements, while
  ambiguous legacy friend names no longer alter fight-night context.

### Persistence and Save Safety

- Rebuilt Game & Saves as a clearer Career Library with an active-career banner, visible library
  counts, a scrollable save browser, selected-save metadata, grouped actions, and selection-aware
  controls that stay disabled until a valid career or snapshot is chosen.
- Hardened save operations against partial I/O failures: Quick Save and slot-load now continue when
  optional backup creation fails, while backup restore validates the source before touching the
  destination and reports backup/write failures without escaping the UI callback. Non-object JSON
  saves are now rejected cleanly before split-save hydration.
- Hardened save-folder housekeeping by skipping symlinked entries during external block pruning,
  preventing accidental deletion outside the intended save slot tree.

### Event Economics and Rivalries

- Made every card an economic decision. Ticket price was a single company-wide number nudged in $5
  steps, and it had no effect on turnout at all: raising it lifted the gate and cost nothing.
  Ticket price, production tier and marketing spend are now booked per event, and price drives
  attendance against what that specific card can carry. Gate revenue peaks a little above the
  market rate, so undercutting leaves money on the table and gouging empties seats and costs gate,
  atmosphere and merchandise. Marketing spend buys turnout with diminishing returns. The booking
  screen projects attendance, fill, gate and total spend live, names the market price, says whether
  you are priced about right, and warns when a card commits a dangerous share of your cash before a
  ticket is sold. Cards saved before this change, and every AI card, keep using the company-wide
  defaults.
- Tied production quality to who is actually watching. The four production tiers (Lean, Standard,
  Premium, Spectacle) trade staging cost against build, atmosphere and broadcast value, and the
  richer tiers only repay their cost behind real broadcast reach. With no coverage a lean show is
  correct; a regional webcast or streaming deal wants Standard; a cable deal justifies Premium; and
  Spectacle pays off once a wide-reach network is carrying the card. Production is now something to
  upgrade in step with your broadcast contract rather than a setting to leave alone.
- Priced untouched cards at the market rate. The company-wide default never scaled with the
  promotion, so a player who ignored the pricing lever drifted further from a sensible number the
  bigger they got, and could lose money on a card that should have been profitable. A card you have
  not priced yourself now follows the market rate automatically; editing the price takes manual
  control until the show is scheduled, and the next card starts on the market rate again.
- Made feuds bookable. A rivalry already fed hype quietly, but nothing surfaced it and nothing let
  the player build one, so the Media Desk and Matchmaking were effectively separate games.
  Selecting two rivals in Matchmaking now reports the grudge, its heat, its origin and whether a
  rematch is being demanded, and a booked grudge lifts both projected hype and the gate in
  proportion to heat, weighted down when the feud is buried on the prelims. Calling out an existing
  rival in the Media Desk escalates the feud instead of resetting it, and press conferences and
  press tours keep a live feud in the headlines, so a grudge can be built over several weeks and
  cashed in on fight night.
- Balanced the new event economics against the rest of the simulation before release. A demand floor
  meant gate revenue climbed for ever once it bound, making the maximum price the correct answer at
  up to nine times what a card could carry; demand now decays to zero and a badly priced show is
  allowed to flop. The market-price curve let drawing power compound with venue prestige, inflating
  a mature promotion's gate roughly sixfold against purses, overhead and production costs that do
  not grow at that rate; the curve is now shallow enough to keep late-career gates in proportion.
  Production tiers were cheap enough that the richest option was correct from the first televised
  card, so their costs were raised and their compounding build bonus reduced until each tier is the
  right answer somewhere on the broadcast ladder. Regression coverage pins the elasticity peak, the
  reach-dependent tier crossover, and the auto-pricing contract.
- Rebalanced player-company finances across career stages. Curated opening-roster fighters now begin
  on 55% founder-era contracts, making a credible first card affordable without discounting generated
  regional depth or changing existing saves. Monthly office costs now grow with company popularity,
  from the existing $12,000 regional base to meaningful national and global infrastructure, and a
  second or later player event in the same month suffers progressive audience, sponsor, and broadcast
  cannibalization while every signed purse and production cost remains fully payable. Finance forecasts
  expose the scaled office cost, focused regressions pin all three rules, and a reproducible early/mid/
  late audit lives under `analysis/`.
- Hardened the release candidate around those systems. Grudge matches and Media Desk escalation now
  resolve rivals by durable fighter ID so duplicate names cannot award hype or gate demand to the
  wrong bout; invalid or stale rival selections are rejected before cash or a limited media action
  is consumed. Scheduled-event economics retain safe defaults for older saves and round-trip their
  card-specific values. The focused regression is deterministic and part of the canonical isolated
  suite.

### Release and Verification

- Unified the release workflow: `Build Portable.bat` runs the shipping suite, validates the universe,
  and builds both the game and Database Editor, while the editor-only script remains an optional
  focused build. Build failure restores staged runtime data, stale staging data is cleared, and the
  portable check verifies both executables.
- Expanded the canonical isolated suite with focused Fighter Profile, Scouting, Combat Sports,
  Fight Night experience, and event-economics regressions. The release runner now exercises those
  systems alongside persistence, finance, UI data, media, child promotions, identity, audio,
  database validation/editor coverage, advancement notifications, popup lifecycle, and the
  multi-seed stability playtest.

## 3.0.9 - 2026-08-17

This release consolidates the child-promotion safeguards, persistence and identity hardening,
universe-data validation, release tooling, and UX/stability improvements completed since 3.0.8.

- Added `FEATURE_DEVELOPMENT_BACKLOG.md`, an evidence-backed roadmap separating completed systems
  from the next feature slices: child-promotion scheduling, executable super-events, finance
  reconciliation, decision-center UX, and 100-year simulation validation.
- Made player and AI/child promotion finance auditable: cash movements now use canonical transaction
  metadata, weekly closes reconcile ledger totals to actual cash with explicit repair entries, child
  promotion receipts/costs are recorded, and Finance surfaces show reconciliation status.

- Hardened MMA child-promotion ownership and interactions: empty launches roll back, ordinary
  takeovers are blocked, parent belts are vacated before champion loans, closed parent divisions
  reject transfers, paid transfers record parent-ledger fees with confirmation, and retired/orphaned
  loan metadata is repaired. The manager now guards duplicate windows, clears stale details, keeps
  identity labels consistent, and provides scrollable rosters.

- Added a deterministic 48-week child-promotion progression regression covering AI events, parent
  profit sharing, contracts, protected loans, callback safety, and save/load persistence.
- Fixed annual AI weight movement allowing custom-promotion fighters to enter divisions the
  promotion had deliberately closed; added a deterministic 48-week handoff regression.

- Fixed same-name fighters sharing live fight state. Scorecards, damage, stamina, control,
  knockdowns, and stat lines now use private per-bout identity slots, while names remain purely
  presentation text. Player event references resolve durable fighter IDs first and reject ambiguous
  legacy names instead of silently selecting or moving the wrong athlete.
- Made completed player events transactional: a late finance, awards, archive, media, or presentation
  failure restores the pre-event domain state and RNG rather than leaving a partially applied card.
- Hardened save loading: split-save data blocks must stay under the owning slot's generated
  `DataBlocks` folder, malformed model rows now report their exact location transactionally, and
  unknown forward-compatible model fields no longer crash a current build.
- Capped player result summaries and verbose event logs so long careers retain searchable results
  without unbounded save, startup, or Log-screen growth.
- Added a canonical isolated regression runner used by both the test and portable-build launchers.
  Every maintained suite, including child-promotion, identity/persistence, database-editor, and
  long-run stability coverage, now receives its own runtime-data directory.
- Fixed Database Editor Save As so a cancelled or failed validation/backup/write leaves the current
  database selection intact; added focused Save As regressions.
- Unified database-editor, runtime, and release-pack universe validation behind one side-effect-free
  schema check. Invalid scalar values now produce actionable diagnostics, and normal universe loads
  normalize legacy data in memory without modifying the selected source file.
- Made load staging inspect all nested runtime values, added profile-window reuse keyed by fighter ID,
  and made temporary fight caches plus fight-night audio cue locking safe on exception/concurrent paths.
- Model collection fields now use independent default factories while legacy `null` values remain accepted on load;
  optional career arcs retain their explicit inactive `None` state.
- Portable builds now verify the recorded offline CPython/PyInstaller toolchain instead of installing
  build dependencies during packaging; test failures identify their subsystem, deterministic seed, and data root.
- Migrated runtime `Toplevel` creators to the shared call-site/entity window registry, replacing stale
  duplicate popups and preserving fighter/entity identity in detail windows.
- Routine contract and broadcast notices from calendar advancement now become one Inbox/news summary;
  due-event decisions remain explicit modal blockers.

## 3.0.8 - 2026-08-02

This release reworks the scouting and recruitment loop, replaces one-off production providers with
negotiated broadcast contracts, rebuilds the Legacy Ledger, and moves Fighting Academy and Combat
Sports into the main navigation as normal management screens.

- Moved Fighting Academy and Combat Sports into the main navigation as normal management screens.
  Both previously opened their primary workspace in a separate window, so reaching them meant
  leaving the main application context and managing a floating window. Selecting either from the
  sidebar now switches the main screen in place, exactly like Roster, Contracts, or Finance, and the
  existing Finance, Scouting, and World entry points route to the same pages. Academy purchase moved
  from a popup to an inline empty state on the page, since a tab cannot raise a modal every time it
  is selected. Detail views are deliberately unchanged and still open as focused popups: academy
  prospect profiles and card replays, child-promotion management, and circuit records and history.
  Academy and Combat Sports state, saves, and simulation rules are untouched, and neither page is
  constructed until the player actually opens it.
- Fixed the Fighting Academy build page reporting a frozen cash balance. Unlike the popup it
  replaced, the panel stays on screen for as long as the player has no academy, so reading company
  cash once while building the page left it stuck at whatever the balance was when the page was
  first opened (commonly $0) and froze the Build Academy button in that state. The price check is
  now live, and when funds are short it names the shortfall instead of only the balance.
- Fixed the same page stretching to fill the whole scrollable screen, which pushed the price line
  and the Build Academy button far below the fold. It now keeps the compact proportions of the setup
  dialog it replaced.
- Changed Contracts ordering so fight-counted comeback deals no longer sit at the top of the table
  from the moment they are signed. A comeback contract now only pins to the top once it is down to
  three or fewer guaranteed bouts; longer commitments sort below the regular expiry-ordered roster.
- Added a "Closed divisions" toggle to Free Agents and Regional Prospects so talent in divisions you
  have closed can be shown or hidden. Both screens default to showing them, closed-division prospects
  are highlighted amber like the free-agent market already did, and Regional Prospects reports how
  many rows the toggle is hiding.
- Fixed scouts wasting their spare assignment slots. Auto-assignment only considered a scout with a
  completely empty workload, so a two- or three-slot scout holding a single player brief never used
  the rest of their capacity. Every free slot is now filled, which is where most of the lost scouting
  throughput was going: a 3-slot and a 2-slot scout now reach full workload in one week instead of
  idling four slots indefinitely.
- Rebuilt talent searches to return a shortlist instead of a single name. A search cost 2.4x-3.1x a
  basic report, occupied a scout for 2-5 weeks, and surfaced exactly one lead, so scouting the market
  broadly was never affordable. A search now returns 3-6 ranked leads (scaled by the scout's
  networking), each with its own dossier and signing verdict, at roughly a fifth of the previous cost
  per lead. The headline lead keeps the scout's best read; secondary names come in at lower
  confidence so a dedicated report is still worth buying on anyone you take seriously.
- Reworked the signing recommendation to judge roster fit by quality rather than headcount. Divisional
  need was measured purely as "fewer than ten fighters", so a 27-year-old 73 OVR was reported as not
  needed in a division of 27 journeymen. Recommendations now weigh where the fighter would slot into
  your existing division, reward an upgrade on your current top five, and state the projected
  divisional rank in the reason text.
- Stopped short-term problems vetoing good signings outright. Being injured or on a losing streak sat
  in the same hard-blocking list as a closed division, so any injury made a 90 OVR free agent an
  automatic PASS. Injuries and skids are now priced into the score as scaled concerns; only a closed
  division or pending retirement blocks a deal outright.
- Added plain-English descriptors for every scout verdict (RECOMMEND SIGNING, MONITOR, PASS, PENDING)
  and every recommendation logic mode (Balanced, Aggressive, Strict, Prospect Focus, Value Focus,
  Roster Need). Verdict meanings now appear in the Scouting legend, the Logic selector tooltip,
  completed-report inbox mail, and the Free Agents scouting panel, which also shows the same formal
  verdict the Scouting centre uses instead of an unrelated second opinion.
- Suppressed scouting dialogs during automatic assignment so a full scout or a cash shortfall can no
  longer interrupt week processing with a popup.
- Rebuilt the Legacy Ledger. The all-time fighter list was a fixed-width text dump capped at 60 names
  with a single sport filter. It is now a sortable table of up to 400 careers with Sport, Status,
  Gender, Division, and name-search filters; columns for division, status, last company, win rate,
  peak ability, titles, defences and awards; Hall-of-Fame and retired rows colour-coded; double-click
  to open a full profile; and a breakdown line itemising exactly which career achievements produced
  the selected fighter's legacy score. Company Eras became a sortable table of legacy, reputation,
  show count and era count, with the full era history shown for the selected company instead of only
  the most recent three.
- Added a motivation adjustment to comeback negotiations. A retired fighter who wants to compete
  again now shaves up to 12% off their asking price, while one who has to be talked into it adds up
  to 6%, applied to the comeback premium as well. The curve is neutral at 65 motivation and
  interpolates between set anchor points: 0 = -6%, 30 = -4%, 50 = -2%, 65 = 0, 75 = +4.5%,
  85 = +7.5%, 100 = +12%. The negotiation window states the fighter's motivation and the exact
  adjustment.
- Replaced one-off production-provider purchases with real broadcast contracts. Adding a provider was
  a permanent unlock from a fixed list of three with no requirements and no expiry. Networks are now
  a six-tier ladder from Regional Webcast to Apex Worldwide, each gated behind a company-popularity
  requirement that must be met before talks open, signed for a fixed term of 12-24 months against a
  rights fee. Contracts count down monthly, warn in the inbox at two months remaining, and expire
  with a dialog prompting renewal; events still assigned to a lapsed network fall back to no coverage
  rather than being charged for a partner that no longer carries them. Company Editor lists remaining
  contract months per network plus the popularity needed to unlock the tiers still locked, and the
  booking screen shows the selected network's remaining term. Saves written before this change keep
  their providers and receive a full term on load rather than expiring immediately.

## 3.0.7 - 2026-08-02

This release carries the complete 3.0.6 Matt-Dev and Brett-Dev feature merge, including child
promotions, staff contracts and effects, academy progression, Dark Mode, sortable tables, finance
and save integrity fixes, extended Fight Night commentary, and the packaged Database Editor.

- Replaced exposed duplicate-source suffixes such as `BAMMA`, `FA`, and `Legend` with a compact
  `(D)` marker after the fighter's display name across player-facing screens while preserving raw
  names for save compatibility and identity resolution.
- Made champion, interim-champion, and duplicate markers idempotent across live Fight Night
  commentary, scoreboards, archived replays, official results, profiles, ledgers, news, inboxes,
  and matchup text. Existing output such as `(C) (C)` now renders with one champion marker.
- Included the spectator calendar crash fix, all merged child-promotion, staff, academy, finance,
  sorting, theme, save, stability, and five-round presentation fixes from the 3.0.6 release line.
- Rebuilt and validated both portable executables: `MMA Warriors.exe` and
  `MMA Warriors Database Editor.exe`.

## 3.0.6 - 2026-08-01

- Fixed a packaged calendar-advance crash in AI roster cuts and upgrade reviews. Scheduled fighters are now resolved through the shared durable-ID/legacy-name reference set before either review considers releasing or replacing them.
- Expanded staff into a real employment system: every staff role now has a documented gameplay effect, staff quality and morale influence those effects, and the Staff screen supports hiring, firing, severance, contract offers, renewal negotiations, and an Expiring Contracts tab. Legacy saves receive safe staff contract defaults.
- Connected Broadcast Producers, Drug Testing Officers, Doctors, and the existing scouting, marketing, matchmaking, and talent-relations roles to visible simulation outcomes including broadcast reach, testing cost and accuracy, medical costs, recovery, card building, scouting, promotion, and fighter negotiations.
- Balanced staff economics after audit: Talent Relations now gives quality-scaled cash leverage in fighter and transfer talks, compliance staff reduce manual testing costs as well as event costs, and Doctor recovery benefits scale across specialist quality instead of using a single threshold.
- Expanded Fighting Academy engagement with recurring development challenges. Players can choose specialist camps, pressure-test prospects in amateur bouts, or align coaching plans; decisions affect cost, fatigue, confidence, development, amateur experience, reputation, and the saved academy story history.
- Fixed secondary and popup data tables whose headings did not sort. Every `Treeview` now receives the shared numeric, date, record, and text sorting behavior, including Overall and other rating columns.
- Added an explicit Dark Mode theme as the default presentation, with neutral dark surfaces and readable gold/red accents. Save, database, and region list controls now start in the selected palette instead of flashing light gray.
- Fixed AI promotion takeovers carrying stale expired contracts into the player Contracts screen; inherited zero-month deals are now renewed for 12-24 months so the takeover does not mass-release the promotion's roster.
- Updated `Build Portable.bat` so every portable build validates and includes `MMA Warriors Database Editor.exe` alongside the game.
- Expanded the MMA Child Promotions manager with promotion health columns, AI operating mode, roster search, gender/division/status filters, contract and potential columns, fighter detail readouts, and double-click profile access.
- Fixed child-management ownership filtering, expired child-fighter transfers, parent profit-share ledger entries, and status filters hiding all parent loan candidates.
- Audited the opening fighter identities: all 4,850 live fighter objects have unique `fighter_id` values, while the 56 repeated base-name groups are intentional promotion/legend/free-agent career snapshots. Synthetic `Legend`, `FA`, and `BAMMA` suffixes are now hidden from roster, market, contract, scouting, profile, child-promotion, and fight-replay displays; raw names remain available internally for save compatibility and identity resolution.
- Fixed live five-round title-fight presentation trimming too much round-summary text. The watcher still keeps official judge cards sealed until the result, but each round now retains its unofficial cumulative score and gas telemetry, and a regression advances a title fight through all five rounds to verify summaries, scorecards, metrics, and the result remain visible.
- Changed Fight Night playback to full commentary mode. The engine no longer deduplicates repeated calls or inserts middle-exchange omission markers, and the live watcher renders the original round-summary lines instead of replacing them with condensed broadcast summaries. Official scorecards still reveal only at the result.
- Verified player-configured extended title fights: seven-round title/main-event cards now retain every round introduction, transition, summary, scorecard, metric, and final result in the live watcher.
- Rebuilt the `Matt-Dev` portable package with the full-commentary watcher and included `MMA Warriors Database Editor.exe`; `Portable Check.bat` passed while preserving packaged saves, databases, and logs.

### MMA AI Child Promotions

- Added player-funded MMA child promotions. The player chooses a large startup budget, a roster-building identity such as Youth Prospects or Big Names, and a 0-100% share of future child-promotion profits returned to the parent company.
- The child opens with a real MMA roster signed from the free-agent market, then runs through the existing AI promotion engine for matchmaking, cards, contracts, development, finance, and long-term strategy.
- Added a Companies-screen manager for launch, strategy and profit-share changes, parent-to-child fighter loans, recalls, and parent transfers of AI-signed child fighters. Loaned fighters remain parent-owned and cannot be released, replaced, contract-expired, retired, or removed by a child promotion's normal AI roster reviews.
- Added save-compatible child metadata, protected-loan repair, profit-distribution tracking, and smoke coverage for launch, finance, loans, recalls, and round-trip persistence.
### Brett-Dev Merge Notes

### Save, Load & Results Integrity

- Made career loads transactional: a read, migration, or apply failure restores the complete live
  career instead of leaving a partially replaced hybrid state.
- Made Results Database migration idempotent. Repeated Quick Loads no longer manufacture `|2`,
  `|3`, and later copies of the same completed card, while genuinely distinct same-week cards keep
  separate entries. Existing duplicated index rows are repaired on load.
- Made world serialization observational by moving champion/division repair out of the save writer;
  saving no longer adds fighters or consumes simulation RNG.
- A metadata-sidecar write problem is now logged as a recoverable cache warning after the primary
  save succeeds, rather than incorrectly reporting that the whole save failed.

### Contracts, Events & Financial Pressure

- Rejected negative or out-of-range contract money, percentage, PPV, and guarantee inputs before
  they can change cash or roster state. Terms remain normalized to the supported 1-60 month range.
- Player promotions now pay the full purse they negotiated. The hidden company-size discount was
  removed, and win, finish, PPV, and guarantee obligations use the same projection, payout, event
  report, and finance-ledger calculation.
- Guaranteed fights now advance on every official player bout, including draws, and unfinished
  commitments remain visible. Expired contracts leave or use the explicit paid auto-renew workflow;
  valuable fighters no longer silently receive a free random extension.
- Outside non-exclusive draws now use the shared draw-result path instead of being recorded as a
  loss. Event booking and conflict checks retain fighter IDs so duplicate display names remain
  independently bookable.
- Negative company cash now creates escalating, persistent financial-pressure consequences through
  stability, morale, and inbox warnings, and clears the streak after recovery.

### Scouting, World Data & UI

- Fixed Basic Dossier crashing after charging the player when Staff had not been opened. Lazy screen
  refreshes now tolerate unbuilt widgets, and successful scouting state stays synchronized.
- Added a player setting for automatic idle-scout assignments and clearer assignment messaging;
  academy guidance now recognizes an already-hired scout.
- Restored the Regions screen to the active dark palette and clears stale Results detail when a
  filter changes the visible card set.
- Corrected the Eurasian Fight Circuit's World Hub level label, repaired geographically incorrect
  regional team lists, and made opening gym membership/capacity balance prevent elite rooms from
  starting at several times their intended load.

### Balance, Tests & Portability

- Reworked the Simulation Lab audit around competitive low/mid/high-band matchups with overall gaps
  of six or less, per-tier finish rates, and restored RNG/name state. Its lightweight business
  stress figures are explicitly labelled synthetic rather than real player-event finance.
- Added focused regression suites for persistence, contracts/finance, scouting/world data, audit
  isolation, and portable batch-file path rules.
- Removed developer-specific `C:\Users\...` interpreter paths from the launcher, shipping tests,
  and build scripts. They now prefer the repository `.venv` and fall back to `py` or `python`.


### Fight Excitement

- Fixed AI and regional cards scoring about fourteen points more exciting than the player's for no gameplay reason. Those paths passed raw combined popularity as promotional heat while player cards passed the real hype value, so the same fight scored 66 on an AI show and 53 on yours. Every caller now uses one scale, and the gap measures zero.
- Rebalanced the metric so the fight decides the score rather than the poster. Promotional heat was roughly three-quarters of the number: who was fighting moved it more than what they did, which sent Fight of the Night to the biggest names instead of the best fight. Heat now contributes about a fifth, and the bout itself drives 61% of the variation, up from 43%.
- Fixed a finish scoring worse than going the distance. Later rounds paid up to fifteen points while a knockout or submission paid twelve, so a five-round decision outscored a first-round knockout. Finishes now score eighteen and beat decisions by fourteen points on average.
- Removed round number as a driver of excitement entirely. A fight is exciting or it is not, and when it ends does not change that.
- The score now reads what actually happened in the cage instead of inferring it. Knockdowns, submission attempts, significant strikes landed per round, and how two-way the exchanges were all feed the number, using stats the fight engine already produced but nothing consumed. A back-and-forth war and a one-sided shutout no longer score the same.
- Halved the even-matchup bonus, which sat at 15 or 16 of a possible 16 on almost every bout and acted as a flat offset rather than telling good fights from bad ones.
- Recalibrated every threshold that reads excitement to the range real cards actually produce. Event grades of A and B required 78 and 64, above the highest score a card average could ever reach, so no show in the game could earn either; meanwhile the median card graded F and failed the owner-goal excitement check outright. Grades now run A at 53, B at 49, C at 44 and D at 40, producing a normal spread of 7% A, 21% B, 47% C, 21% D and 5% F.
- The owner-goal excitement gate now passes 82% of cards instead of either all or almost none, so it rewards a good show without being a formality.
- Retuned the fanbase reaction to the top and bottom fifth of card averages, and the technical-crowd bonus to a level a card can actually reach; both previously sat above the maximum and never triggered.
- Separated the per-fight bonus labels from the event-level bands. Individual bouts spread far wider than card averages, so Fight Night now flags roughly the top sixth of bouts as bonus contenders rather than reusing an event threshold no single fight was measured against.

### Build & Tests

- Fixed the portable build aborting before it reached PyInstaller. `Build Portable.bat` gates on the smoke test, which failed on every run with `AttributeError: 'FightEmpireApp' object has no attribute 'city_box'`: management screens build lazily when first opened, and the event-booking city check read a booking widget roughly two hundred lines before that screen was built. The test now opens the booking screen before reading from it, and repopulates its fighter table afterwards so later checks see the current roster.
- Made the Matchmaking click-selection check tolerate a display that cannot lay out the fighter table. It drove clicks through real pixel coordinates, which do not exist when the booking pane is never mapped on a headless or minimised build machine. The full assertions still run wherever Tk lays the table out; elsewhere the test reports the skip explicitly and still exercises the underlying selection logic, instead of failing a build for an environment limit.
- Raised the youth-market batch assertion to match the larger combat sport intake.

### Starting Database

- Brought every real fighter over 42 in the starting database down to their prime age, so a new world opens with recognisable names competing rather than retiring. Twenty-seven athletes were affected, including Bobby Lashley (50 to 30), Chael Sonnen (49 to 31), Vitor Belfort (49 to 27), Brock Lesnar (48 to 28) and Holly Holm (44 to 31). Each new age comes from the database's own convention of prime start plus three, so every fighter lands inside their authored prime window with ratings, records and profiles untouched.

### Combat Sports (Child Promotions)

- Opening a combat sport division now asks for confirmation first. Selecting a sport and pressing the manage button launched the promotion immediately and spent the $120,000 startup investment with no prompt; the dialog now states the cost, your cash after launch, that the promotion starts with no athletes, and that it cannot be undone. Insufficient funds are reported before anything is charged.
- Added a combat sport free-agent market, kept entirely separate from the MMA free-agent pool. Established athletes aged 22 to 33 arrive with real records, ratings and popularity, so a division can be staffed with competitors who are ready now rather than only teenagers.
- Fixed thin hiring markets. The signable pool targeted four athletes per division, capped additions at twelve per refresh, and only ever generated 18- and 19-year-olds — across roughly twenty divisions per sport that left many showing a single name or none. The youth target was raised and the free-agent pool added alongside it.
- Fixed a per-pass intake cap that left over half of Boxing's thirty-four gender and weight combinations short of four prospects however many times the market refreshed. Launching a division, or refreshing its market, now fills every division to its full target in a single pass instead of a fixed batch, while normal two-monthly replenishment stays paced. Every division of every combat sport now opens with six youth prospects and three established free agents per gender.
- Added contract terms for combat sport athletes. Signings previously set no contract length at all, so athletes could never expire, be renewed, or be negotiated with.
- Added negotiation to sport signings and renewals: a contract dialog shows the athlete's expected purse and term, lets you set both, and offers a Test Reaction check before sending. Athletes accept, hold out for closer terms, or reject outright based on their rating, popularity and age, with prospects favouring long deals and established names favouring short ones.
- Sport contracts now count down monthly and raise inbox warnings at three, two and one month, plus an expiry notice when a deal lapses.
- Added a Combat Sports tab to the Contracts screen listing every child-promotion athlete with sport, division, rating, time remaining and purse, using the same red/orange/yellow expiry highlighting as the MMA roster, with Negotiate Renewal and Release Athlete actions and a per-bout payroll total.

### Regional Titles & Lineage

- Fixed regional belts changing hands in ordinary development bouts. The championship flag was matched on the *division* rather than on the reserved contenders, so once a circuit booked a title fight every other bout in that division on the same card was flagged a championship too — and each one ran the crowning routine. The belt ended up on whoever won the last development bout of the night instead of the actual title contest, changed hands on cards where no title fight was scheduled, and left the real champion competing in bouts that were never recognised as defences. Championship status now matches the specific reserved pairing.
- Verified across 96 simulated feeder cards (390 bouts): divisions carrying more than one championship bout on a card went from roughly ten per month to zero, and reigning champions placed into non-title bouts went to zero.
- Added a TITLE LINEAGE panel to the fighter profile listing every championship event in a career — inaugural reigns, crownings, defences, and vacancies — across every promotion the fighter has competed for. The profile previously showed a single line and only for a *reigning* champion, so a vacated or lost title vanished from the fighter's record entirely; 156 vacated championships in the reference career were invisible.

### Title Fights & Booking Conflicts

- Fixed a scheduled title fight silently losing its champion, and with it the championship on the fighter's record. The double-booking repair that runs on every save load resolved clashes purely by date, so an ordinary undercard booking made a week earlier would win the fighter and the champion was quietly replaced with a TBA in their own title defence — leaving a belt advertised in a bout the champion never appeared in, an unrelated free agent signed into the empty corner on fight night, and the champion's record showing the other, non-title bout instead. Championship bouts now claim their fighters first regardless of date.
- A bout that still loses a fighter to a booking clash now has its championship sanction removed rather than continuing to advertise a belt nobody present can win, and the downgrade is announced in the news feed and the inbox.
- Interim status is now recomputed for title fights that survive a booking repair, instead of keeping whatever was true when the bout was first booked.
- Fixed any bout still holding a TBA slot skipping the weigh-in completely. Weigh-ins ran before the opponent was resolved, so neither corner was ever weighed: no scale weight was recorded, a missed weight could not be detected, and a blown cut could never downgrade a title bout to a catchweight non-title contest. A 240 lb fighter could contest a 155 lb championship without ever stepping on the scale. TBA opponents are now signed before the weigh-in, and the whole existing weight-miss, fine, and commission-removal pipeline applies to them normally.

### Fight Night

- Fixed the fight-log corner read always reporting an 8-week camp for both fighters. It read `red_camp` / `blue_camp` / `camp_weeks` from the booking dictionary, keys nothing has ever written, so every bout fell through to the hardcoded default and hid the real preparation — including short-notice replacements who had no camp at all. It now reads the fighter's actual camp length, matching the corner read already used elsewhere in the engine.

### Fighter Weight & Division Fit

**Root cause fix — walk weight was decided before the division was.**

- Fixed walk weight being derived from a randomly rolled division inside the fighter generator and then left stale when the caller overwrote the fighter's division. A fighter built as a heavyweight could be seeded straight into flyweight and keep a 295 lb frame, cutting 169 lb every camp and sitting permanently pinned at the maximum weigh-in penalty. This affected 13% of every world (43% of all regional-feeder fighters).
- Added a `weight` parameter to regional-feeder fighter creation so the division is known at build time instead of being patched on afterwards, and updated the initial feeder roster build and the monthly regional youth intake to pass it.
- Added `assign_fighter_division()` as the single supported way to change a fighter's division, so the frame and the class can no longer silently disagree.
- Added `plausible_walk_weight_band()`, derived from the same limit and spread constants as the fighter generator so the builder and the validator cannot drift apart again.
- Added `repair_walk_weight_for_division()`, which pulls an impossible frame back into its division's believable band and reports how far out it was.

**Save repair for existing careers.**

- Extended the division-frame migration to repair frames in both directions against each division's plausible band, rather than only the undersized tail, and bumped its version so careers created before this fix are repaired on load.
- The repair message now reports oversized and undersized counts separately along with the worst mismatch found.
- On the reference career this reset 861 frames (790 far too heavy for their class, 71 far too light; worst mismatch 148 lb) and refreshed division-fit ratings across the roster.

**Division moves.**

- Fixed the move-up path never checking whether a fighter could make the target weight. It measured frame fit only, so a 227 lb featherweight was waved into lightweight as an "undersized" move — he could not make 155 lb either, and moving up one class does not fix a frame that belongs three classes higher. Both directions now check cut feasibility.
- Fixed division-fit penalty messages blaming the wrong cause. The penalty is the sum of two independent terms — a frame that is light for the class, and a naturally small build — but the text hardcoded the walk-weight explanation, telling players a 227 lb lightweight's "walk weight is light for Lightweight" when every point came from his build. Messages now name the term that actually produced the penalty.
- Added `division_size_penalty_parts()` and `division_fit_reason()`; `division_size_penalty_for()` is now a thin wrapper over them so all callers stay consistent.
- A completed division move now carries the fighter's real frame across intact and only repairs it when it was never credible for either division.
- Made the closed-division roster reassignment generic to any promotion rather than one company, and made it move fighters to the nearest still-open division for their gender instead of a hardcoded Welterweight — dropping a heavyweight into welterweight moved them ninety pounds and left a frame that fitted neither.

**Acclimatisation.**

- Kept growing into a division as the loose, common path: a fighter competing above their natural size fills out toward the class over months, and the division-fit penalty eases as they do.
- Added the reverse path so an oversized fighter can recompose down toward their division, but only when the body allows it — cutting skill, conditioning, a smaller natural build and youth all gate it, at roughly half the speed and a third of the frequency of growing. Large-framed, poor-cutting or older fighters stay where they are and are steered toward a move up instead.
- Acclimatisation now runs on fighters carrying no penalty but an oversized frame, which the previous penalty-gated check skipped entirely.

**Tracking.**

- Added a per-fighter `division_fit_log` recording every acclimatisation step with date, division, walk weight, direction and resulting division fit, retained for the last 24 entries and persisted with the career.
- Added a DIVISION ACCLIMATION panel to the fighter profile showing the recent trail and the net frame change over it.
- The profile's Walk Weight row now shows the difference against the division limit, and a new Camp Cut row shows how much the fighter has to lose to make weight.

**Measured effect on the reference career:** every division's frames now sit inside their plausible band (0 out of band, previously 793 fighters more than 25 lb over their limit); newly generated feeder fighters are correct at birth (0 of 400 out of band, previously 252 of 400); with a normal eight-week camp 1,968 of 2,000 fighters make weight on a 10 lb median cut and a median penalty of 0; and the annual division review still applies about one move per promotion per year.

## 3.0.5 - 2026-07-31

### Fight Night Audio

- Added a 0-100 volume slider directly to the live Fight Night viewer; changes take effect on the next cue, persist with the career, and share the same normalized setting as Game Settings.
- Added and integrated a 36-file crowd-audio pack, edited and mastered from licensed real field recordings, with three distinct variants for each of 12 pre-fight, live-fight, finish, and decision trigger families.
- Fight Night now rotates non-repeating variants for arena buildup, walkouts, opening roars, clean strikes, knockdowns, submission danger, inactivity, round endings, finishes, decision tension, split-card boos, and respectful post-fight applause.
- Playback honors the manifest's per-cue gain, limits simultaneous reactions and repeat frequency so commentary stays clear, and falls back to the existing procedural cues when an asset or playback service is unavailable.
- Hometown fighters now receive the strongest audible crowd lift, while national, adopted-home, and training-base appearances receive smaller nearby-market boosts; the Fight Night introduction identifies the active local connection.
- Included source and license documentation, a reproducible mastering tool, and a cue manifest with suggested triggers, loop capability, duration, playback gain, and provenance.
- Reduced the clean-strike vocal reaction by 3 dB and attenuated the gasp layer inside the knockdown roar so short crowd exclamations no longer overpower the broader arena response.
- Preserved every accepted revised-pack mix as Variant 1 and added alternate-source Variants 2 and 3, including modern large-stadium ambience, goal eruptions, hockey outrage, group gasps, boos, cheers, and applause.

### World Locations

- Added Belleville and Kingston, Ontario to Canada's event-city and generated-fighter hometown pool.
- Updated Brett Akey's authored hometown from the province-level Ontario label to Belleville.

### Fight Night Commentary

- Fixed long five-round fights occasionally losing late-round introductions, transitions, summaries, or action commentary when the fight log exceeded its global line limit.
- Replaced global fight-log truncation with per-round commentary compaction that preserves the opening and closing exchanges while always retaining round boundaries, finishes, scorecards, recaps, and fight metrics.
- Applied the fix to both championship fights and non-title five-round main events.
- Added regression coverage for full-distance title and non-title main events, commentary bounds, and a final-tick Round 5 stoppage.

### Interface Polish

- Made ordinary Matchmaking row clicks toggle fighters into or out of the current selection, so players can build pairs and tournament groups without keyboard modifiers; double-click still opens the fighter under the pointer, and the persistent Matchup Insight summary explains the interaction.
- Replaced the low-contrast grey progress treatment with high-contrast loading bars and distinct red/blue fight freshness bars on a dark track.
- Reworked the top status bar so long promotion names use the flexible space available in maximized windows, while popularity, stability, cash, date, and advance controls remain separate and fully readable.
- Added a modal, themed loading panel with phase and progress feedback for Quick Load and Save Manager slot loads, including recovery-snapshot attempts, so large careers no longer appear frozen while their world state and screens are rebuilt.
- Rebuilt Mail / Decisions discoverability with explicit Owner Goals collapse/expand controls, persistent goal summaries, filter-aware message counts, a one-click Show All action, selection guidance, and responsive side-by-side/stacked panels.
- Reworked Add Show / Matchmaking so Show Details keeps a labelled toggle and status summary, the Current Fight Card remains visible beside fighters or above them on narrow windows, and an instructional empty-card state explains the booking flow.
- Compacted expanded Show Details into two control rows and one shared schedule/broadcast status row on wide screens, with medium and narrow layouts that safely stack the same fields, actions, and forecasts instead of clipping them.
- Consolidated fight-card hype, build, fatigue, and medical-return values into one visible booking-information column, eliminating the page-level horizontal scroll that previously hid the card while preserving the complete 20-column fighter table and its own labelled table scrollbar.
- Gave Available Fighters focused Essentials, Readiness, and Form & Fitness table views plus an All 20 view, preserving every scouting metric while making the default Matchmaking workspace easier to scan.
- Reclaimed fighter-table height with a compact, persistent Matchup Insight disclosure and alerts that only occupy space when they contain actionable text; matchup history, booking context, and the row-colour guide remain available through the labelled Expand control.
- Added a Compare Selected action that opens the existing full side-by-side fighter comparison directly from Matchmaking; all five booking actions use one row on wide fighter panes and a safe two-row grid at narrow widths.
- Shortened the fighter-table view cue so it stays on one line while its tooltip retains the full list of available scouting and readiness metrics.
- Fixed vertical splitters locking to the smaller pre-maximized startup height. Mail / Decisions now also reserves a 425-pixel top pane and a fixed two-row action grid, guaranteeing that all eight Inbox buttons appear at startup even if the sash begins at its minimum; later player adjustments remain preserved.
- Removed the full-width `NEW HERE?` alerts. Concise guidance remains beside Inbox counts, Message Detail, the fighter-column cue, and the empty fight card without consuming the vertical space needed by tables and actions.
- Added responsive layout and sash-startup regressions, full inbox-filter reset coverage, and per-theme contrast checks for the remaining inline discovery cues.

### Contract Negotiations

- Rebalanced free-agent contract evaluation so base purse and annualized compensation matter more than raw contract length.
- Added compensation-gated diminishing returns for contract security through 48 months; longer terms provide no additional signing advantage.
- Enforced the negotiation system's 60-month contract limit even when a player manually enters a higher value.
- Added regression coverage for minimum-pay long-term offers, competitively paid contracts, low-cost prospects, and the duration cap.

### Interface Accessibility

- Rebuilt shared notebook-tab states across all 24 themes with WCAG AA text contrast, a minimum 3:1 selected-surface change, larger labels, and redundant outline/elevation cues for the current tab.
- Added automated per-theme contrast checks and a documented tab palette/state guide.
- The main game window now opens maximized, while retaining its responsive fallback geometry for smaller displays and test environments.

### Developer Workflow

- Made synchronized `CHANGELOG.md`, `README.md`, and `AGENTS.md` updates a required part of every implementation improvement or fix.
- Required focused regression coverage for behavior changes, with documented reproducible manual verification only when reliable automation is not practical.
- Added smoke coverage that keeps runtime version metadata and the documented change contract synchronized across the project guides.
- Corrected the README build instructions to distinguish the portable game build from the separately validated Database Editor build.

## 3.0.4 - 2026-07-30

### Veteran Career Integrity

- Reworked late-career decline so it tapers after meaningful losses from a fighter's peak rather than reducing long-serving veterans into implausibly low-rated active fighters.
- Retirement reviews now account for the ability a fighter has lost from their career peak, while a hard review at age 46 prevents indefinitely active veterans.

## 3.0.3 - 2026-07-30

### Regional Championship Booking

- Fixed regional champions being booked in ordinary development bouts between title defenses. Regional titleholders now only compete when the belt is on the line; if no suitable challenger is ready, they sit out.
- Ranked vacant-title participants and defending challengers by divisional merit instead of promoting whichever ordinary development pairing happened to be drawn first.
- Preserved championship stakes in feeder-promotion fight logs so fighter histories correctly identify title bouts.
- Added regression coverage for champion-only defenses, title cadence, contender selection, and archived title flags.

## 3.0.2 - 2026-07-30

### Database Editor And Universe Data

- Rebuilt the fighter Skills tab as an all-skill sheet: each of the 67 individual attributes has a direct labelled 1-99 slider and numeric input, grouped by fighting discipline.
- Added live Current OVR, Suggested OVR, and difference readouts; database authors can apply the entire sheet, synchronize broad core ratings, or use the calculated suggested OVR.
- Authored exact opening detailed skills, career archetypes, Prime Start, and Prime End values for every seeded MMA fighter. The Database Editor and future new games now use the same values.
- Clarified `prime_age` as an optional legend-age override. Normal fighters now display their actual Prime Start and Prime End values and blank optional overrides no longer block edits.
- Hardened seed record lookup so same-name curated variants on different promotions keep their own authored profile rather than accidentally borrowing another variant's values.
- Added a hidden-Tk editor acceptance audit that exercises all database field controls, all 67 skill sliders, skill-sheet persistence, and authored prime windows without saving the database.

## 3.0.1 - 2026-07-30

### Hotfixes

- Fixed the shipped Universe Database Editor failing at startup because its window title referenced an undefined `GAME_TITLE` constant.

## 3.0.0 - 2026-07-30

### Highlights

- Expanded MMA finish logic with a much larger set of submissions, technical submissions, striking stoppages, TKO outcomes, and context-aware broadcast commentary.
- Improved watched-card pacing and fight-night presentation, including complete-card end handling, keyboard arrow navigation, and broader visual theme support.
- Made booking calendar-aware with named event days, recovery and camp time measured in days, and better AI contender availability and scheduling.
- Added player-directed scouting goals, recommendation controls, randomized starting scouts for custom companies, and stronger stat-driven scouting results.
- Added fighter career journeys: academy homegrown-title aims, veteran final runs, discipline and weight-management support, camp-fit work, and champion retention pressure.
- Consolidated the starting universe into one editable database file and shipped the MMA Warriors Universe Database Editor with safer selectors, copying, validation, filters, sorting, and constrained inputs.
- Improved UI responsiveness and dense-screen usability across rankings, profiles, editor tools, themes, and varied desktop resolutions.
- Reworked AI promotion financial stability and simulation efficiency while preserving save compatibility and the existing finance protections.

### Compatibility

- Existing career saves remain supported. New fields have load-time defaults and repair paths where needed.
- The distributed universe database is `Databases\\Default Universe.universe.json`; active saves remain separate and are never edited by the database editor.
