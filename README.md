# MMA Warriors

Portrait catalogue v3 (source; not a rebuilt package) adds 50 hairstyles per gender:
98 men's and 77 women's generated choices. Women have no beards, stubble or moustaches;
men have 66 facial-hair options including none. Shared features gain 50 bounded
presets each; skin and natural hair now have 62 shades each with country-family
weights preserved. Existing complete saved portraits retain their appearance.
Fine facial differences remain subtle at thumbnail size. See
[portrait expansion counts, review and compatibility](docs/FIGHTER_PORTRAIT_EXPANSION.md).

Named portrait corrections give Markell Holmes dark skin, an afro and a chinstrap,
make Brett Akey bald, and author Conor McGregor's UFC July 2021 photo look.
These display overrides also apply to existing saves without rewriting their vectors.
See [the named portrait review](docs/FIGHTER_PORTRAIT_NAMED_CORRECTIONS.md).

The next ranked portrait pass authors 49 entries at database positions 51–100
from reviewed UFC/PFL/ONE photos; Matthew Green now has user-directed pale skin,
short dirty-blond hair, blue eyes and no facial hair, completing the 50-entry cohort. Three
authored-only hair shapes improve mullets and loose waves without changing
generated choices. See [sources and likeness limits](docs/FIGHTER_PORTRAIT_TOP_100_REVIEW.md).

## Version 3.0.9

Version 3.0.9 hardens long-running careers: child-promotion ownership is protected, duplicate fighter names are safe in live fights and player events, event completion and save loading are transactional, universe validation is shared and read-only, and release builds use an isolated regression runner plus a pinned offline toolchain. It also caps only the global result/event feeds—never fighter records or career totals—so long saves remain responsive. See [CHANGELOG.md](CHANGELOG.md) for the complete release notes.

The active feature-development map is maintained in [FEATURE_DEVELOPMENT_BACKLOG.md](FEATURE_DEVELOPMENT_BACKLOG.md). The staged mechanics roadmap is documented separately in [FIGHT_ENGINE_DEVELOPMENT_PLAN.md](FIGHT_ENGINE_DEVELOPMENT_PLAN.md), while [NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md](NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md) audits the existing emergent-story systems and defines an event-driven expansion that must preserve calendar performance. The frozen fight-engine Phase 0 distribution is in [analysis/FIGHT_ENGINE_BASELINE_REPORT.md](analysis/FIGHT_ENGINE_BASELINE_REPORT.md). The next major slices are future-dated child-promotion events, executable super-event projects, decision-center UX, and deeper long-run validation; finance reconciliation is already implemented and remains a required invariant for new cash paths.
When taking control of an AI promotion, stale zero-month inherited deals are renewed for 12-24 months so the promotion's roster stays intact.
`Build Portable.bat` now builds both `MMA Warriors.exe` and `MMA Warriors Database Editor.exe` into `dist\\MMA Warriors` every time.
The MMA Child Promotions manager includes live cash/stability/AI-mode metrics, roster filters, contract and potential data, fighter detail inspection, loans, recalls, and confirmed parent transfers. Child launches require an eligible opening roster; child companies cannot be taken over through the ordinary company flow; champion loans vacate parent belts; and transfers respect closed parent divisions.
Child promotion transfers renew an expired AI-signed fighter for a normal contract term, and parent profit shares appear in the main company's finance history.
This release expands the living-world simulation, improves watched fight-night presentation and commentary variety, adds career journeys and directed scouting, introduces the shipped Universe Database Editor, and strengthens UI scaling, AI scheduling, finance stability, contract negotiations, accessibility, and release packaging. Version 3.0.7 also consolidates starting-career selection into one dropdown and one Start action. Fighter source markers are kept as internal database metadata so intentional historical snapshots remain distinct without cluttering player-facing names. See [CHANGELOG.md](CHANGELOG.md) for the 3.0 release notes and hotfixes.

MMA Warriors is a deep Windows desktop promotion-management simulation. Choose any real-world-inspired promotion, take control of an existing company, or create a new one from scratch. Build a roster, negotiate contracts and transfer deals, book cards, develop prospects, manage finances and media, and try to turn a regional operation into the sport's defining brand.

Every career lives inside a persistent MMA world. Fighters age, improve or decline, move between promotions, chase titles, suffer injuries, join gyms, build rivalries, and eventually retire. Rival companies sign athletes, run events, spend money, and pursue their own identities, so your decisions reshape a living competitive landscape instead of a static roster.

## Version 3.0.7 Stabilization Notes

The current development build hardens the systems exercised by an end-to-end custom-promotion QA
career. Loads are transactional, repeated loads do not duplicate Results cards, and saving no longer
changes roster/champion state or advances simulation randomness. Contract inputs reject negative or
out-of-range values, agreed purses are paid in full, bonuses and PPV clauses share one forecast and
payout calculation, guarantees advance on official bouts, and expired deals cannot renew for free.

Scouting actions are safe before the Staff screen is first opened. Automatic idle-scout work is a
player setting that commissions at most one discounted paid dossier per week, and academy guidance
follows the live staff state. Regional team data and the
Eurasian circuit label are corrected, opening gym loads are capacity-aware, and Regions follows the
active dark theme. Negative company cash now creates visible stability and morale pressure instead
of functioning as consequence-free credit.

The Simulation Lab audit now emphasizes realistic matchups within six overall points and reports
low-, mid-, and high-tier finish rates. Fight-mechanical controls are labelled separately from the
business-only Gate Multiplier, all are bounded, and old saves automatically migrate the gate value
out of the versioned fight configuration. Its gate/profit output remains a labelled synthetic stress
test; use completed career events and the Finance ledger for the actual player economy. The accepted
fight calibration is 60.39% finishes, 16.48% KO and 19.04% TKO across the frozen 3,840-bout corpus.
The finish audit also protects the composition behind those headline numbers: competitive bouts
must remain within 48-54% finishes and 15-19% submissions, Doctor and Injury Stoppages must remain
reachable, and at least 6% of finishes in scheduled five-round bouts must occur in rounds four or
five. The current verified five-round late-finish share is 19.55%. These are release gates, not
post-fight overrides; mismatches intentionally finish much more often than realistic competitive
pairings. See [`docs/FIGHT_FINISH_SYSTEM_AUDIT.md`](docs/FIGHT_FINISH_SYSTEM_AUDIT.md) for the
historical-guide reconciliation and method-family rules.

Simulation Lab tuning controls have one bounded effect each:

- **KO Power** scales strike-stoppage conversion.
- **Submission Finish** scales completed submission conversion.
- **Decision Noise** scales only the narrow ambiguity band available to judges.
- **Gas Cost** scales action workload.
- **Damage** scales landed strike damage.
- **Gate Multiplier** scales synthetic and career ticket revenue only; it never affects a fight.

## Run The Game

Double-click:

```text
Launch MMA Warriors.bat
```

Or run directly:

```powershell
python main.py
```

The packaged EXE has no Python requirement. Keep the whole `MMA Warriors` folder together and run it from a normal local folder, not from inside a ZIP archive. The game stores quick saves, save slots, databases, and logs beside the app when that folder is writable. If it is installed in a protected folder such as `Program Files`, it automatically uses `%LOCALAPPDATA%\MMA Warriors` instead.

The shipped starting universe is one editable file: `Databases\Default Universe.universe.json`. It contains MMA fighters, combat-sport athletes, companies, media, and regions. Cloned custom universes are separate files created only when the player makes one.

Every canonical MMA source row carries an immutable `fighter_id`, and new careers preserve that
identity instead of generating a different ID on each seed. The shipped database also provides a
non-empty birth country and hometown for every source fighter. Existing authored locations remain
untouched; previously incomplete rows are explicitly marked as either bundled verified identity
data or a deterministic regional fallback, so the source does not imply that inferred locations
were independently verified. Broad-reach media packages cover all 13 simulation regions.

`MMA Warriors Database Editor.exe` ships beside the game EXE. It is a developer-facing editor for universe files, with a database selector, browse/copy-current/save/save-as workflow, automatic backups, validation, bulk fighter/company changes, and per-record JSON editing. It edits starting databases only, never an active career save.

Universe validation is shared by the editor, game loader, and package build. Loading a universe never rewrites it: legacy compatibility defaults are normalised in memory, while an intentional reset/migration is the only workflow that writes a database file.
Legacy schema-four fighter databases receive deterministic source IDs during in-memory loading;
their bytes remain unchanged until the user explicitly saves them. Adding or duplicating a fighter
in the Database Editor always creates a fresh ID, while normal edits and company moves preserve it.

The game starts in the explicit **Dark Mode** theme. Themes can still be changed from the in-game theme selector, and native list controls follow the selected palette immediately.

All tab, detail-window, and popup tables support sorting by clicking their column headings. Numeric ratings, money, records, durations, dates, and text columns use the same shared sort behavior.

Each game now owns a self-contained folder, for example `Saves\Game 1\savegame.json`. The Career Library shows the active career in a high-contrast banner, reports visible career/snapshot counts, provides a scrollable slot browser, and reveals the selected company, game date, save time, group, and active status before an action is taken. Selection-only actions remain disabled until a valid row is chosen, while save, load, backup, restore, folder, and settings controls are grouped by purpose. Its two rolling recovery backups, autosaves, crash recovery files, and spectator archives stay inside that same `Game 1` folder, so multiple careers cannot overwrite one another. Autosaves use the same two-slot rolling policy per cadence, overwriting the oldest snapshot instead of accumulating files. Spectator Mode also writes a permanent archive at every completed decade, such as `Game 1 - 10 Years.json.gz`, under `Saves\Game 1\Snapshots`. Existing flat saves remain loadable and move to the folder layout the next time they are saved. A failed optional recovery snapshot is logged without blocking Quick Save or a switch to another slot. Save files must contain a JSON object; malformed top-level data is rejected before split-save blocks are processed. Restores validate the selected snapshot before backing up or replacing the destination, and a restore error leaves that slot untouched. Runtime diagnostics live in `Logs\mma_warriors.log`; unexpected failures create a separate report in `Logs\Crashes`.

Before moving a build to another laptop, run `Portable Check.bat` from the packaged folder. It confirms that the EXE is present and tells you whether runtime data will be stored beside it or in the user profile fallback.

Fight Night uses one live broadcast viewer for MMA, boxing, kickboxing, Muay Thai, wrestling, and Brazilian jiu-jitsu. Other-sport replays include sport-native round/period/match starts, clocked exchanges, cumulative scoring, stamina and condition reads, and an official result. Boxing runs six-, eight-, or ten-round non-title contests according to level and 12-round title fights; three independent cards produce unanimous, split, majority, and draw verdicts, with knockdowns reflected as 10-8 or 10-7 rounds. Standard Muay Thai runs three rounds and title bouts run five, with judging weighted toward effective kicks, knees, elbows, dumps, balance, and clinch control rather than generic strike volume; Lethwei contests remain five-round, knockout-first bouts. The default **Broadcast** commentary view derives a shorter feed from the complete stored transcript: repeated low-value calls are condensed, while round boundaries, meaningful damage, submissions, cuts, fouls, tactical changes, finishes, scorecards, metrics, and results always remain. Landed standing offense, completed takedowns, landed ground strikes, passes, sweeps, reversals and escapes receive evidence priority over routine movement; identical calls remain capped at two per round. Compact notes report how many standing, standing-striking, takedown, ground-control and ground-striking exchanges were omitted instead of replacing them with a generic reset. **Detailed** mode plays the complete stored transcript, and completed-bout review plus the per-round Analysis Explorer retain the underlying technical evidence. The active live bout can switch between Broadcast and Detailed without restarting playback or changing the archived transcript; clearer round separators and distinct knockdown/finish emphasis make long cards easier to scan, while a small status label shows the current Balanced, Technical, Excitable or Concise voice. Commentary density and voice remain persistent options under **Game & Saves -> Game Settings**. Exact judge cards and numerical totals remain sealed until the official result. Duplicate-name opponents retain separate red/blue identities, telemetry, result records, and replay labels. Only one live card can be open, advancing or skipping is state-guarded, full-card skips require confirmation, and settlement failures leave the report retryable. The viewer supports compact laptop layouts, keyboard controls, visible scrollbars, adjustable text size, Follow live, round/period navigation, and paced holds for round summaries and finishes. The end-event report is vertically scrollable, and archived replays preserve the original location, profit, excitement, and event context without applying results twice. Twelve one-time head, body and leg damage milestones make deterioration visible without adding new damage rolls: fighters can redden and bruise, protect a damaged midsection, shift their weight or develop a visible limp as the existing trauma totals rise. Exact cut calls use the recorded location, bleeding, swelling and vision-risk facts, and every such line is retained in Broadcast and the chronological Analysis Explorer.

A 36-file, field-recording-based crowd-audio pack is integrated into Fight Night from `assets\crowd_audio`. Its 12 trigger families each have three genuinely different variants for arena buildup, walkouts, opening roars, strikes, knockdowns, submission danger, inactivity, round endings, finishes, decision tension, split-card boos, and respectful post-fight applause. One loop-safe arena recording now remains open as a quiet, crossfaded bed for the entire live card; walkouts, mastered round bells and factual reactions layer above it without restarting the ambience. Fight Night randomly rotates variants without immediately repeating a take, honors their recommended mix gain, reserves reaction capacity for knockdowns and finishes, and limits lower-value overlap so commentary stays clear. Closing the live viewer stops its bed and outstanding reactions rather than allowing audio to bleed into the next screen; the live stop event and audio-only entropy remain outside card-settlement rollback data. Hometown appearances receive the strongest reaction lift; national, adopted-home, and training-base connections receive smaller boosts, and the live introduction explains who has the local support. The accepted revised-pack mixes remain Variant 1, while Variants 2 and 3 use alternate recordings rather than pitch-shifted copies. Brief gasp and "ooh" reactions are mixed below the sustained arena response. The manifest and `LICENSES.md` preserve trigger metadata, attribution, and CC0 provenance. A 0-100 slider in the live viewer changes the next cue's volume immediately and saves the same setting exposed under **Game & Saves -> Game Settings**. If the pack or Windows playback is unavailable, events continue with the original procedural fallback cues.

Striking commentary uses action-specific situation banks rather than shared generic calls. Boxing, kickboxing, Muay Thai, Lethwei presentation, and MMA distinguish entries, counters, body work, leg damage, kick checks, pocket/clinch work, rope or fence pressure, defensive exits, knockdowns, cuts, and damage-aware follow-up attacks. MMA exchange prose is rendered from the recorded actor, named move, target, defense, outcome, counter state and settled position instead of joining a selected technique to older broad-action text. Each supported MMA style owns an exclusive authored combination and finisher: striking disciplines retain ordered hand, kick, elbow and knee components plus style-native knockout techniques, wrestlers connect characteristic entries to ground-and-pound stoppages, and grapplers receive distinct chokes, joint locks and leg locks. A fighter may use these through either a primary or secondary discipline, but an unrelated style cannot inherit them from a signature assignment. Finishers only name the causal technique attached to an already-resolved KO, TKO or submission; they do not add another finish opportunity, and an individual legal signature finisher takes priority over the broader style finisher. Each bout records presentation-only fighter profiles derived from detailed attributes: the relevant strength and style family shape the vocabulary for punches, kicks, counters, clinch work, takedowns, transitions, control and escapes. All 46 fighter traits receive a natural pre-fight introduction. Combat-relevant traits can also shape a live call only when completed trace evidence supports the connection—for example a Body Hunter landing to the body, a Counter Specialist using a real counter window, or a Scramble Artist completing a transition. These contextual calls are capped at one per fighter per round and two per bout. A saved camp that matches a real Gym also receives a natural corner introduction using only its recorded coach, location and specialties. Live camp calls require a completed exchange matching the Gym's actual boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning specialty. Promotion, academy, unknown and legacy labels never inherit invented Gym facts, and contextual camp calls use the same one-per-round/two-per-bout cap. Ground calls distinguish top pressure from bottom survival, name the actual armbar/choke/leg lock and its registered defense, preserve the resulting position, and announce inactivity stand-ups as referee actions rather than fighter escapes. Deterministic bout salt and larger landed, blocked, slipped, survived, control, transition, escape and visible-damage pools vary otherwise identical exchanges without consuming any fight RNG. Recorded signature/mastery status, stance matchups, plan changes, momentum, accumulated damage, verified camp/coach identity, championship stakes and rivalry history can enrich the call only when that fact exists. Broad trauma narration never invents a fracture, organ injury or precise body-part diagnosis; only structured cuts name an exact location. Finish narration preserves authored submission chains, medical/injury evidence, head-kick and walk-off behavior while staying connected to the actual final move and position; body- and leg-kick knockdowns remain strike events unless the separate injury-stoppage check fires. Between-round advice cites visible gas, damage, repeated techniques, control and successful move families. Viewer compaction, trait/camp wording and voice selection do not change action selection, scoring, stoppages or the locked finish percentages.

## Developer Change Contract

Every implementation update, improvement, fix, balance adjustment, data change, UI change, tooling change, or packaging change ships as one complete change package:

1. Add a meaningful entry to the current release in `CHANGELOG.md`.
2. Update `README.md` wherever the feature, workflow, compatibility note, test coverage, or build instructions changed.
3. Update [`AGENTS.md`](AGENTS.md) with the affected architecture, invariant, integration point, pitfall, or verification rule.
4. Add or update focused automated regression coverage and run the affected test suite. When a behavior cannot be automated reliably, document and perform a reproducible manual check in addition to the closest stable automated invariant.

Documentation-only edits do not need artificial runtime tests, but their links, commands, formatting, and diff integrity must still be checked. A change is not complete merely because the code works; its tests and all three documents must describe the same behavior.

## Smoke Test

Before shipping a build, run:

```text
Run Smoke Tests.bat
```

`Run Smoke Tests.bat` and `Build Portable.bat` both call `run_regression_suite.py`. It runs every
maintained test sequentially in its own temporary runtime-data directory, including smoke,
persistence, contracts/finance, finance-audit reconciliation, UI data, focused fighter-Profile safety,
focused scouting lifecycle
and identity coverage, simulation-performance call-count and regional-cadence invariants, QA tooling,
media, all child-promotion regressions,
same-name fighter and save-integrity coverage, the full fight-plan/style/rules engine matrix,
shipped-universe validation, validator read-only loading, fight/audio cache cleanup, window
lifecycle, advancement-notification, focused event-economics and
grudge-match coverage, and the long stability playtest. Event-economics coverage includes legacy
scheduled cards, save/load round trips, ticket-demand boundaries, broadcast-dependent production
choices, and durable fighter-ID rivalry resolution.
This isolation prevents one test's active database,
save, cache, or log files from changing another test's result. Run an individual focused file only
when iterating locally; use the canonical runner before shipping.

The current development model is documented in [`docs/FIGHTER_DEVELOPMENT_GUIDE.md`](docs/FIGHTER_DEVELOPMENT_GUIDE.md); current clinch, cage, ground, and damage mechanics are documented in [`docs/FIGHT_DAMAGE_AND_CLINCH_AUDIT.md`](docs/FIGHT_DAMAGE_AND_CLINCH_AUDIT.md); shared per-theme tab colors and WCAG ratios are documented in [`TAB_ACCESSIBILITY.md`](TAB_ACCESSIBILITY.md).

## Build A Portable Windows Version

Run:

```text
Build Portable.bat
```

The script verifies the pinned offline build toolchain, runs the shipping tests and universe
validation first, then creates both executables:

```text
dist\MMA Warriors\MMA Warriors.exe
dist\MMA Warriors\MMA Warriors Database Editor.exe
```

`Build Database Editor.bat` remains available when only the standalone editor needs rebuilding; it
is not an additional required step after `Build Portable.bat`.

Both build commands verify the offline pinned toolchain in `build-toolchain.json` first; they never install packages. Install the exact versions from `requirements-build.txt` into the selected Python 3.13 environment before building.

Close the packaged game before rebuilding. The build script preserves packaged `Saves`, `Databases`, and `Logs` in a staging backup and restores them after PyInstaller replaces the folder.

## Current Core Features

- Choose an established promotion, `Create New Promotion...`, or `Spectator Mode` from the Starting Promotion dropdown, then use the single `Start New Game With Selected Promotion` button. Established choices include BAMMA, UFC, PFL, ONE Championship, RIZIN, KSW, Cage Warriors, LFA, Oktagon MMA, BRAVE Combat Federation, ACA, PRIDE Fighting Championships, Strikeforce, and World Extreme Cagefighting. The legacy promotions include prime-era legends such as Kimbo Slice, Kazushi Sakuraba, Gilbert Melendez, Cung Le, Miguel Torres, and more.
- Change control to another promotion through the company screen, or begin a custom-promotion career with its own region, scale, divisions, identity, and initial roster draft.
- Guide fighter career journeys from Roster > Career Goals: academy graduates can pursue a homegrown title, veterans can request a final run, troubled prospects can reset their habits or weight cut, camp fit can be rebuilt, and champions need real opponents, visibility, and contract security to stay invested.
- Follow persistent story threads from World > Storylines. Rivalries, title chases, championship
  reigns, title losses, and redemption runs retain ID-safe causes, stakes, bounded beats, and
  resolutions; linked matchmaking and Fight Night views explain why a connected bout matters.
  Injury returns, comeback contracts, academy-to-title careers, and contract promises also retain
  connected outcomes. Weight and camp reinventions, friendship/stablemate fights, promotion eras,
  other-sport title careers, and MMA crossovers now form connected chapters too. Fighter Profiles
  assemble a bounded Career Timeline only when opened, while each annual awards review archives up
  to eight defining stories from that year. Academy mentorship, gym splits, hometown heroes, talent
  wars, and story-aware AI matchmaking extend those connections without overriding sporting rules.
  Contested contract signings, academy recruitment and sanctioned superfights now build scored
  two-year rival-promotion arcs. Coaching partnerships carry meaningful wins, title breakthroughs,
  setbacks and gym splits, while academy mentorship follows a graduate into the senior career and
  can culminate in a championship. Established local stars booked into hometown or birth-market
  headline fights now carry visible homecoming stakes through triumph, heartbreak, an unresolved
  result, or a championship payoff.
  Contract Sagas connect the final renewal window, stalled talks, expiry or release, a rival-company
  signing, a return, and the first revenge fight against the former promotion without scanning the
  wider market or roster.
  Staff Tenure stories similarly connect appointments, renewal pressure, stalled talks, renewals,
  releases and expiry by durable staff ID; the current chapter is visible in Staff Profiles and the
  Storylines browser. First-of-kind scouting, medical, matchmaking, marketing, broadcast and fighter-
  relations outcomes now add bounded career achievements or setbacks plus a visible staff legacy.
  Feeder Pathways connect a child-promotion loan or paid transfer to featured child results, recall,
  parent debut, senior breakthrough, championship, departure, or retirement. The chapter follows
  the fighter by durable ID and appears in matchmaking, Fighter Profiles, Storylines, and the child
  operations detail rather than being reconstructed from alumni or fight history. Child roster moves
  are atomic: a late story failure restores belts, both rosters, cash, finance ledgers, Chronicle,
  story state, and simulation RNG.
  Breakout Runs now carry an eight-point underdog's Giant Slayer result beyond its achievement popup:
  a draw keeps expectations unresolved, later wins build or confirm the rise, major spotlights and
  titles provide a payoff, and repeated defeats or retirement close the chapter. The active pressure
  is visible in matchup context and bounded AI booking intent, while the full chapter appears in
  Storylines, Fighter Profile timelines, Chronicle, and annual review. Focused and canonical paired
  runs measured +0.64% and −1.61% CPU variance with identical gameplay/RNG state, showing no
  repeatable simulation slowdown.
  Career Crossroads now connect an established fighter's third consecutive simulated MMA loss to
  the decisions and results that follow: further decline, an unresolved draw, a division
  reinvention, a recovery or championship win, release, contract exit, or retirement. The active
  pressure is visible in matchup context and bounded AI booking intent, while the saved ID-safe
  chapter appears in Storylines, Fighter Profile timelines, Chronicle, and annual review. Its
  result hook reads at most four existing bout rows only when an eligible loser has no active key;
  all follow-ups use the direct fighter key, and no recurring simulation pass was added. Three clean
  paired runs ranged from -19.04% to +2.66% CPU variance with identical gameplay/RNG state, showing
  no repeatable slowdown; the complete isolated regression runner also passes.
  Fighter Relationship chapters now continue beyond the first friendship or featured-stablemate
  bout. A draw leaves the personal and sporting question open; later meetings can end in competitive
  respect, rivalry-driven fallout, a three-fight verdict, or a post-camp-split rematch. Active
  pair-story keys live only on the two involved fighters and cap at four, allowing a former
  stablemate story to survive a camp move while unrelated bouts return before pair-key or story-index
  work. Three optimized paired calendar runs ranged from -3.70% to +1.88% CPU variance with identical
  gameplay/RNG state, showing no repeatable slowdown after an unconditional-lookup prototype was
  rejected for breaching the speed gate; the complete isolated regression runner also passes.
  Retirement decisions now open a Career Farewell chapter too. Matchmaking and Fight Night explain
  the final-fight stakes; automated retirement cards prefer meaningful opponents already inside the
  legal candidate pool, and the ending remembers whether the opponent was a career rival, friend,
  former stablemate, significant former opponent, champion, or fellow veteran. The final result and
  both fighter identities remain visible in profiles, Storylines, Chronicle, and annual review. This
  uses a direct fighter story key and event settlement rather than another calendar scan. Three clean
  paired runs ranged from -1.96% to +4.44% CPU variance, and the canonical run measured +3.10%, with
  identical gameplay/RNG state; the complete isolated regression runner passes.
  Narrative updates are emitted by existing domain events and use bounded
  direct-key indexes, so they do not add another whole-world weekly simulation pass. A deterministic
  paired 12-week aggregate A/B regression verifies identical gameplay/RNG outcomes and enforces the
  calendar-speed budget. Three post-Feeder-Pathway runs retained identical state and ranged from
  −1.94% to +2.06% total narrative CPU variance, showing no repeatable slowdown and remaining inside
  the noise-tolerant 5% rejection ceiling; zero regression remains the design target rather than a
  budget to consume. A
  separate synthetic 25-/50-/100-year
  regression verifies bounded save growth and flat indexed lookup cost. Full collection
  normalization runs only when a hard story cap is exceeded. Failed academy graduations also restore
  their story state and transient indexes alongside roster, finance and simulation RNG state.
- Start a Spectator Mode save to hand the selected player promotion to the AI, fast-forward the living world by week, month, year, or a chosen date, and watch any promotion's latest card in the live fight-night viewer before taking control of a company.
- Book main cards, prelims, early prelims, title fights, TBA fights, and career-affecting 4/8-fighter one-night MMA tournaments. Tournament entrants are seeded by rank, use the normal camp and weigh-in system, accumulate fatigue between rounds, can crown a champion in the final, and remain reserved from other bookings.
- Schedule shows by month and week, then watch or instantly simulate them.
- Advance from the persistent responsive top bar; long promotion names use the flexible center field while popularity, stability, cash, date, and advance controls remain readable. World simulation runs in queued steps with live phase/progress feedback, guarded controls, cached promotion-level card-date decisions, and efficient batched spectator fast-forward. Promotion monthly reviews are spread evenly across the four weekly advances; regional development still runs one card per circuit per month instead of accumulating at the month boundary.
- Quick Load and Save Manager slot loads show a themed, modal please-wait panel with named phases and a high-contrast accent progress bar while large career files are read, rebuilt, and refreshed. If Quick Load needs a recovery snapshot, the same panel identifies that recovery attempt before the result is shown.
- Mail / Decisions reserves a fixed two-row action area so all eight buttons are visible immediately without requiring a sash drag; the message table alone shrinks when vertical space is tight. It explains how many messages are shown, stored, filtered, unread, and actionable, and lets Show All clear every visibility filter. Owner Goals always retains a summary and labelled Expand / Collapse control, while compact guidance in Message Detail explains how to reveal context without a full-width onboarding alert.
- Matchmaking keeps Current Fight Card and its action buttons on-screen: the card sits beside Available Fighters on wide displays and moves above them on narrow displays. Expanded Show Details uses two compact control rows at wide widths, a three-row medium layout, and a safe stacked narrow layout while retaining every event field, scheduling action, status, forecast, and show tool. Its empty state explains how to add the first bout, and every fight keeps slot, matchup, weight, hype, build, fatigue, and medical-return information visible without page-level horizontal scrolling. Available Fighters opens in a focused Essentials view, with Readiness, Form & Fitness, and All 20 presets that preserve every scouting metric and the selected rows. Every ordinary row click toggles that fighter into or out of the selection, allowing pairs and 4/8-fighter tournament groups to be built without holding Ctrl; double-click opens the fighter directly under the pointer. Its five booking actions use one row when space permits and a two-row grid at the minimum pane width. Matchup Insight keeps step-by-step selection guidance, history, booking context, and the row-colour guide behind a labelled persistent disclosure, empty alert bands no longer consume table height, and Compare Selected opens the full side-by-side fighter viewer.
- Fight-night viewer with play-by-play, a tale-of-the-tape scoreboard, live round-by-round scores, high-contrast red/blue gas and condition bars on dark tracks, card progress and bout states, colour-coded knockdowns and finishes, auto-play, round timing, scorecards, skip controls, post-event bonuses, and live/completed tournament bracket viewing.
- End-of-year awards (Fighter, Fight, Knockout, Submission, Prospect, Veteran, and Promotion of the Year) crowned automatically each January, with a browsable awards history.
- A living world where fighters age a year each season, prospects break out, veterans decline, title contenders emerge on win streaks, and busy regions grow.
- Regional feeder circuits where 16+ prospects build records, develop, graduate to free agency, and can return to stay active; AI promotions scout them through budgeted, stealable contract offers.
- Fighting Academy and Combat Sports are main management screens in the left navigation, alongside Roster, Contracts, and Finance. Selecting either opens it in place instead of a separate window, so switching between management areas never loses the main application context. Detail views — academy prospect profiles and card replays, child-promotion management, and circuit records and history — still open as focused popups.
- Player-built Fighting Academy with hired-scout regional networks that take eight weeks to establish, scout-quality-driven lead strength and report accuracy, and no fallback phantom scout. Only one network can be active, and its live recruitment list caps at eight leads; major rival promotions run visible persistent youth programmes and may bid for the same regional talent. Prospects arrive aged 12–15 with 30–60 current rating; potential is normally 60–98, while 99–100 generational prospects are exceptionally rare. Manage each athlete through measurable 4/8/12-week development blocks, technical focus, workload and objectives, then review rating, readiness, skill, fatigue and bout gains in a saved block report. Personality, satisfaction, loyalty and academy promises create retention pressure and possible departures. Automatic cards are checked every four weeks, while every healthy prospect receives a safely matched full-engine amateur bout after an individual six-week cooldown. Competition progresses from local to international level with opponent quality, strength of schedule, entry costs, two-bout tournaments and amateur titles. Pros can graduate from age 16 (16–17 requires confirmation) to the MMA main roster, a 12-month developmental deal, an open player combat-sport division, or a regional feeder while the parent retains matching rights; an active right can be exercised from Academy Alumni with a canonical signing payment. Prospect decisions, bouts, transitions and alumni follow durable IDs so duplicate display names remain independent. Tournament entry, graduation and matching-right signing are transactional: if a late simulation, story or finance step fails, the game restores the affected money, records, rosters and prospect state instead of leaving a half-completed action.
- The Scouting target board and assignment centre use durable fighter and staff identities, preserve
  completed intelligence while an upgrade or fight observation is pending, and keep old dossiers
  visibly stale instead of refreshing them on load. Regional searches retain their ranked lead list
  and open the headline fighter directly. Filters and action controls reflow for laptop-width windows,
  while assignment history provides vertical and horizontal scrolling.
- Scouting assignments reveal no hidden conclusions until their work completes. Basic and observation
  dossiers retain uncertain ranges; exact current ratings require a repeated, high-confidence Full
  Evaluation, and all intel begins ageing after six months. Fight observations record the opponent,
  result, round count, significant strikes, takedowns, control and knockdowns alongside the scout's
  separate opinion. Search Aim selects the market while Search Priority optimizes for immediate
  ability, potential, value, marketability, or roster need; age and public style narrow the pool.
  Standard briefs balance time and cost, Priority briefs cost more but return faster, and Ongoing
  briefs retain their scout slot for a quarterly refresh. Thin exact pools may return clearly labelled
  Near Matches. Searches only discover existing fighters.
  Completed looks build regional knowledge and a bounded dossier timeline, while watchlisted fighters
  generate non-modal Inbox updates for material contract, employer, offer, injury, weight, record, or
  staleness changes. An established academy network closes, and its open leads are removed, if its
  assigned scout's contract ends; finite network setup and reports may still receive one month of grace.
- Playable Media Desk with a laptop-safe vertical layout: company media strategy, limited weekly campaign actions and fighter cooldowns, campaign risk/outcomes, public trust and buzz, contract offers, deal buyouts, delivery standards, outlet relationships, audience ratings/viewership, campaign history, a persistent editable outlet market, and direct Chronicle/news context. AI promotions negotiate, campaign, deliver, and renew through the same media-contract rules. Older headline-only saves and rights deals remain compatible.
- Detailed fight engine using striking, wrestling, grappling, clinch, physical, mental, stamina,
  momentum, traits, morale, camps, and fight context. Private fighter slots preserve clinch and cage
  ownership for duplicate-name athletes; unanswered-offense stoppages count landed sequences,
  clear on meaningful striking or grappling responses, and reset at the horn. Tournament fields and
  their temporary fatigue snapshots resolve by fighter identity rather than display name.
  New universes also give most fighters a supported secondary discipline derived deterministically
  from their detailed skills. It is shown as a mixed style and contributes a bounded share of action
  selection while the primary style remains the search and compatibility identity. Generated entrants
  are finalized with a supported primary style and validated non-duplicate secondary style, including
  deterministic repair for blank or legacy style labels.
  MMA boxing profiles now distinguish combination punching, body punching and counter timing. These
  ratings choose among named jabs, multi-punch chains, body/head changes and counter-only returns;
  legacy careers derive them from their existing ratings, and the broad calibrated damage/gas model
  remains unchanged.
  The named standing pool also covers low/calf kicks, teeps, round/side/switch/spinning kicks,
  punch-kick chains, knees and elbows. Its expanded sequences include body-to-head boxing, stance
  shifts, pressure flurries, double-jab and hook kick endings, and punch/elbow/knee chains. Six
  skill-gated finishers—rear uppercut, corkscrew cross, spinning backfist, axe kick, jumping front
  kick and switch flying knee—are uncommon technique identities beneath ordinary resolved offense;
  they never add another landing, damage or finish roll. Kick traces retain target, side, range and
  defensive-family metadata, while uncommon spinning and flying attacks require genuinely strong
  supporting skills.
  Clinch and wrestling traces distinguish ties, pummels, pressure, exits, shot setups, trips, throws,
  mat returns, standing rides, escapes and front-headlock transitions. Registered takedowns identify
  their entry, legal defense families and possible finish positions without bypassing the existing
  position/controller resolver.
  Ground traces now select among concrete strike chains, passes, transitions, reversals, chokes,
  arm locks and leg locks. Position-specific offense distinguishes postured guard elbows, half-guard
  crossface strikes, crucifix elbows, mounted hammerfists, back-control punches and turtle wrist-ride
  strikes. Headquarters, body-lock and underhook passes, knee-on-belly and gift-wrap transitions,
  scissor/flower/waiter/lockdown sweeps, post-and-build and tripod get-ups, guard/back recoveries and
  closed-guard retention and half-guard/mount/back rides deepen the same resolved position path. Submission definitions are
  position-legal and retain both their attack pathway and possible failed-attempt outcomes; the
  existing resolver remains the authority for whether position is retained, lost, reversed or
  returned to neutral.
  Fighters may also carry up to three stable signature move IDs. Legal signatures are preferred—not
  forced—and never bypass position, skill, defense, or finish rules. New fighters receive deterministic
  skill-supported sets, the Database Editor offers registry-backed authoring, scouted profiles reveal
  known signatures, and post-fight/career telemetry tracks their attempts, effective uses and finishes.
  Within one bout, capped public move reads let plans and adaptable fighters change their legal move
  mix: body/leg work and feints can set up later families, while obvious repetition becomes easier to
  anticipate. Trace selection reasons explain each such preference, and none directly modifies a
  move's landing or finish chance.
  Technique metadata now has bounded mechanical meaning below that broad resolver: costly or risky
  misses create short-lived selection pressure, real counter windows can exploit vulnerable moves,
  and an effective move may schedule its authored follow-up for up to two ticks. All 18 styles have
  explicit move-tag preferences; open, closed and switch-stance lanes and striker/grappler matchups
  further distinguish legal choices. Elite specialists can consolidate failed shots into front
  headlocks, cage pummels into standing back control, and guard attacks into leg entanglements.
  Enabled corners also evolve their plan from visible round evidence, recording the repeated move or
  effective family that caused each change and a bounded confidence value.
  Defenders now receive a legal named technique of their own—guard, parry, slip, check, catch, sprawl,
  whizzer, frame, underhook turn, hand fight, wall walk or submission escape—rather than a generic
  response label. Fighters persist move-specific offensive and defensive mastery: camps and academy
  plans develop it, high mastery can produce a learned signature, academy graduates carry it forward,
  and older veterans slowly lose sharpness after their prime. These ratings select technique identity
  below the unchanged broad outcome model.
  Skilled fighters may deliberately change between orthodox and southpaw based on their plan and the
  opponent's current stance. Authored sequences can branch after a defensive reaction or position
  change, but remain capped at two ticks and never create a free attack.
  Fight Night labels each recorded technique's target, defensive response and meaningful follow-up in
  text. Round reports use compact effective/used move-family summaries, while the Simulation Lab adds
  top techniques, sequence completions, signature effectiveness, technique load/risk, stance lanes and
  plan evolution; full fighter statistics retain career family/signature totals.
  Saved card replays also include a selectable round-analysis column with top moves, named defenses,
  effectiveness, completed sequence branches, stance switches and plan changes.
- Fight-engine changes are guarded by a frozen 3,840-bout audit corpus, a focused regression suite,
  and a 356-bout full-system matrix spanning every plan, major style matchups, 3/5/6/7-round rules,
  extreme ratings, and duplicate-name identities. The current calibrated result remains 60.39%
  total finishes, including 16.48% KO and 19.04% TKO, with competitive tiers and mismatches measured
  separately. The audit restores its caller's RNG and never changes career fighters or saves; later
  mechanics work must pass the recorded distribution, method, timing, style and behaviour tolerances
  without changing the competitive-finish converter.
  `analysis/generate_fight_move_report.py` also builds an 880-fight technique report covering all 18
  supported styles plus behaviour, tier, stance and open/closed/switch matchups. It measures pairwise
  style distance and distinguishes specialist moves absent from the
  general sample from truly unreachable registry entries and flags dominant moves, mismatch-only moves,
  illegal counter/position/target use and unsafe energy metadata. The checked-in report currently finds
  all 176 moves reachable, all 18 exclusive style combinations, all 18 exclusive style finishers,
  all 16 earlier standing additions
  and 22 of 23 ground additions present in representative complete fights, no indistinct style pair
  and no safety diagnostic. The lone
  probe-only ground addition is the legal turtle wrist-ride striking chain. The separate
  `analysis/generate_specialist_transition_report.py` runs 720 complete fights to require failed-shot,
  standing-back-control and leg-entanglement states plus their legal action-family follow-ups.
  `analysis/generate_fight_commentary_report.py` adds a 256-fight four-voice release gate for factual
  actor/move/defense agreement, stat-profile coverage, failed-submission technique/escape continuity,
  all 46 trait introductions, factual trait/camp calls and per-round/per-bout caps, every commentary outcome lane, finish
  causality, duplicate-result and suffix/placeholder leakage,
  immediate standing/ground repetition, and a maximum of two identical Broadcast calls per round.
  It also audits every between-round coach line for verified speaker identity, an actionable instruction,
  natural wording and the absence of hidden-rating or developer-facing language.
  Pass `--seeds-per-matchup 64` for the 2,048-fight extended transcript audit.
  The canonical runner also regenerates the full 3,840-bout result and action-frequency corpora. It
  rejects a one-fight change from 2,319 finishes, 633 KOs or 731 TKOs and rejects drift in broad-action
  frequency, effectiveness, damage, energy, counter, position or finishing contribution.
  The phased move, combination and skill expansion is specified in
  [`FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`](FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md); its first slice
  has completed its style foundation, move registry, boxing, kicking, clinch, wrestling, ground,
  fighter-signature, tactical-selection, presentation/analysis and release-calibration phases.
  Each MMA simulation also retains a structured result and per-exchange mechanical trace for audits,
  replays and later commentary work while preserving the existing result interface. Commentary
  selection runs on a bout-local presentation stream; mechanically meaningful foul recovery is
  resolved separately, so replacing or expanding phrase banks cannot change the fight result.
  A validated technique registry now names the actual jab, combination, kick, entry, takedown,
  clinch action, ground transition or submission family beneath every broad action. These move IDs,
  legal positions, targets, skill bundles, defenses and follow-ups are retained in the trace without
  consuming combat RNG.
  Combat and referee/judging draws also have explicit bout-local streams. Each clocked exchange is
  rendered through its recorded trace event, which retains its outcome, damage and control deltas,
  state flags, commentary calls, and any official stoppage reason.
- MMA scorecards are derived from the recorded round exchanges rather than fighter reputation,
  remaining gas, hometown, experience, pressure, or presentation. Effective offense leads, then
  effective aggression, then control. Official cards can show justified 10-8 and 10-10 rounds,
  unanimous/split/majority verdicts, draw variants, and visible point deductions for repeated fouls.
- MMA damage distinguishes persistent head/body/leg trauma from transient hurt. A successful
  defensive response, survival sequence, or minute with the corner can reduce hurt and restore some
  gas, but cannot erase physical damage. Structured cuts identify location, severity, bleeding,
  swelling and vision risk for doctor decisions, while the final displayed trauma record also drives
  post-fight medical time and severe injury holds.
- MMA bookings support an ID-safe plan for each corner. Player and game-AI fighters use the same
  execution model: pressure, counter, wrestling, cage, body, leg, submission and pacing choices
  change actions, targets and energy use, while actual defended attacks open counter opportunities.
  Adaptable corners can revise a failing plan between rounds from visible fight evidence, with
  concise advice and a post-fight effectiveness recap. Existing cards remain on the legacy Balanced
  path, and the locked finish/KO/TKO distribution remains within its original preservation gates.
- Fight traces describe coherent exchanges rather than isolated result labels: the entry setup,
  attack, block/evade/parry/check/sprawl/frame/pummel/scramble, counter window and positional
  follow-up are retained together. Multi-strike actions preserve ordered attempted and landed
  components, while a bounded beat count keeps long AI cards and replays practical.
- Grappling follows a validated position graph with one legal owner per role. The trace can retain
  brief failed-shot, front-headlock, turtle, standing-back-control and leg-entanglement states inside
  a scramble, while only consolidated positions carry into the next exchange. Cage chains, re-shots,
  mat returns, wall escapes and submission defenses therefore read like MMA without generating
  impossible top/bottom combinations or changing the preserved finish distribution.
- Playable Boxing, Kickboxing, Muay Thai/Lethwei, Wrestling, and Brazilian Jiu-Jitsu child promotions with AI promotions, manual or smart cards, titles, finances, sport-specific development, contracts, future event planning, and paced live replays. Opening one creates an empty branded promotion named for your chosen parent company, such as `UFC BJJ`: negotiate with private-market athletes or flagship prospects, build **Your Booked Card**, then run it immediately or schedule it for a future month/week. Scheduled shows support Local, Regional, or Arena production and a marketing budget; the manager displays a revenue/cost/profit forecast calculated by the same economics used when the calendar executes the card. Upcoming cards persist across saves, reserve their athletes from other smart cards, can be cancelled, and create an Inbox result plus replay when completed. Every recruit receives a real term and per-bout purse; those purses are paid in card settlement, expiring deals receive a renewal window, and unresolved expired deals return to the flagship circuit. Child cards are limited to one per month and retain their own numbering, history, and economics instead of altering the AI flagship. Stable fighter IDs preserve same-name roster members, champions, booked corners, season awards, records, and Hall of Fame careers across saves; temporary independent opponents remain one-night participants and never enter permanent award tables. Child-promotion setup, signings, and card profit/loss feed into parent-company cash while also tracking their own revenue, costs and history. Native development follows each sport's own technical skill pool, potential ceiling and prime/decline curve; gym quality, facilities, fit, dedication, professionalism, morale, activity, fatigue and injury all affect progress. Child-promotion rosters and athlete profiles show a normalized Sport Rating, career stage, potential runway, 12-month trend and recent development instead of misleading MMA overall growth. BJJ playback tracks standing, guard, side-control, mount, and back-control ownership so takedowns, pulls, sweeps, passes, escapes, recoveries, and submission chains follow legal positional sequences; submission results now end on a visible winner-led tap sequence. Each circuit uses its own authentic weight ladder (including kg wrestling classes and IBJJF-style BJJ classes), with 270 real athletes seeded into career-appropriate prime divisions.
- Division Management is available from Roster. Closing a gender/weight division releases its athletes to free agency, vacates its belts and removes booked bouts; it can later be reopened for free. Closed divisions are removed from roster and Matchmaking selectors but their free agents remain visible and highlighted. Free-agent information visibility is controlled persistently in **Game & Saves → Game Settings**; new games require scouting reports by default.
- Expanded style identities including Dutch kickboxing, Taekwondo, Sanda, freestyle and catch wrestling, Luta Livre, and submission grappling; styles influence action selection and matchup context.
- Shared weight-management model across live cards, AI cards, and the Simulation Lab: walking weight, natural size, cutting skill, camp length, camp quality, scale weight, missed weight, and cut penalties all affect the bout. Player fighters can only change division when their body can credibly make the move.
- Simulation Lab with gender and weight-class filters, side-by-side fighter scouting cards, full profile access, one-off fight watching, engine audits, and sandbox 4/8/16-fighter tournaments that never alter careers or saves.
- Fighter profiles with portraits, nationality, records, rankings, detailed skill sheets, camp info,
  morale, annual overall peaks, and ID-safe fight history. Profiles are read-only views: opening one
  does not generate ratings, consume simulation randomness, migrate child-sport titles, or rewrite
  the career. Scouting hides exact portrait and private identity ratings until the report permits
  them; duplicate names retain the correct employer, championships, opponents, and results. Profile
  actions revalidate current ownership, remain disabled in Spectator Mode, and stay reachable on
  laptop-sized displays. Intentional duplicate career snapshots use a compact `(D)` marker after the
  display name instead of exposing internal `Legend`, `FA`, or `BAMMA` suffixes; durable `fighter_id`
  values still distinguish the records.
- Curated real-fighter profiles with deterministic ratings, real fighting styles, career-appropriate traits, and one-time migration for older saves; see [`docs/REAL_FIGHTER_RATING_AUDIT.md`](docs/REAL_FIGHTER_RATING_AUDIT.md).
- Company and world rankings by gender, division, company, and worldwide scope.
- Contracts, bidding wars, exclusive/non-exclusive deals, market churn, and AI signings. Player negotiations cap terms at 60 months, and long-term security only adds meaningful value when compensation is competitive.
- Rival AI promotions run shows, manage budgets, sign fighters, and produce event histories.
- Book each event against its own economics: ticket price responds to card-specific demand,
  marketing has diminishing returns, and Lean/Standard/Premium/Spectacle production trades cost
  against atmosphere and broadcast reach. Legacy scheduled cards and AI cards retain safe
  company-wide defaults. Matchmaking surfaces active grudges, and rivalry heat can be built through
  Media Desk actions and converted into card hype and gate demand without confusing same-name
  fighters. Curated opening talent starts on affordable founder-era deals; national and global office
  costs scale with company popularity; and running several player cards in one month progressively
  divides attendance, sponsor value, and broadcast reach without reducing contracted fighter pay.
  The deterministic assumptions and early/mid/late outputs are documented in
  [`analysis/PLAYER_FINANCE_BALANCE_REPORT.md`](analysis/PLAYER_FINANCE_BALANCE_REPORT.md).
- Finance separates weekly cashflow from long-term planning. History & Outlook shows annual profit,
  a 12-month ticket/broadcast/sponsor/merchandise revenue mix, monthly roster and top-ten purse
  exposure, and cash/event milestone projections with explicit popularity, stability and safety
  blockers. Strategic Investments provides milestone-gated facilities, international operations,
  staff departments and prestige projects with visible capital, upkeep and permanent effects;
  purchases and monthly operations appear in the same canonical ledger as ordinary company spending.
- World regions with cities, local popularity, economy, drug-testing accuracy, venues, and promotional benefits. Canada's selectable event and generated-fighter locations include the Ontario cities of Belleville and Kingston, and authored Canadian free agent Brett Akey starts from Belleville.
- Gym system with quality, facilities, reputation, morale, specialties, capacity, scouting, camp development, and a gym viewer.
- Fighter development, aging, retirement, unretirement flow, morale, injuries, fatigue, weight cuts, traits, rivalries, and media callouts. Promotions do not renew declared retirees at contract expiry; retirement-pending free agents can receive ordinary showcase bouts, while a two-year queue of at least ten pairable veterans creates a popularity-ordered independent retirement card. Cards stay within gender/weight classes, carry at most 12 bouts, and are capped at two in one week even under a severe backlog.
- Staff management with a Roster & Market view and an Expiring Contracts tab: hire candidates, negotiate salary and term, renew deals, fire staff with severance, and inspect a plain-language explanation of all seven staff roles. Staff skill and morale affect scouting, medical recovery and costs, marketing, matchmaking, testing, broadcast production, and fighter negotiations; the fighter Contracts tab provides the parallel fighter renewal workflow.
- Full database editor with searchable world roster, fighter identity/combat/contract editing, promotion/free-agent transfers, retirement, editable detailed fight attributes, save slots, database export/load, searchable results, and event replay archive.

## Shipping Checklist

1. Run `Run Smoke Tests.bat` and confirm the isolated full regression suite passes.
2. Start the game from `Launch MMA Warriors.bat`.
3. Confirm the Game Menu company picker shows every listed promotion once, including Oktagon MMA, BRAVE Combat Federation, and ACA.
4. Schedule a small event for the current week and simulate it.
5. Save, close, relaunch, and load the save.
6. Run `Build Portable.bat` and confirm it creates both the game and Database Editor executables.
7. Run `Portable Check.bat` from `dist\MMA Warriors`; it checks both packaged executables and the runtime-data location.
8. On the target laptop, extract/copy the complete `dist\MMA Warriors` folder to a local writable location, then launch `MMA Warriors.exe` once before moving across any existing saves.
