# MMA Warriors — Gameplay, Systems and UX Development Plan

Reviewed 12 September 2026. Revised into a gameplay, systems and UX implementation plan. The implementation ledger at the end records verified work; the document itself does not authorise unlisted changes.

## Start here — controlling implementation specification

**Revision 3 — implementation in progress:** the original audit and feature rationale are retained below. Detailed task cards define code scope and tests; Revision 3 records the user's confirmed autonomy, title-miss and replacement choices, plus the verified implementation ledger. The plan is now an executable handoff for the approved slices; unresolved HOLD items remain explicitly gated and must not be guessed.

Authority within this document: explicit later user instructions and current AGENTS.md first; explicitly confirmed Revision 2 decisions next; detailed implementation cards and unapproved design proposals remain subject to those decisions. Do not combine conflicting old and new defaults or treat a proposed number as approved. Deferred features require their own scope decisions. The documentation pass does not independently authorise unlisted changes; the implementation ledger records only the user-directed slices that have actually been built and verified.

The filename is now `MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md`; `UI_REVIEW.md` was its former name. Its containing review folder is retained so existing evidence locations do not move. Future task prompts must use the new full path. The implementation ledger below records actual code/test changes; it supersedes the earlier audit-only wording.

### Latest implementation ledger entry — Grand Prix and child-scheduling extension

The previously held multi-event Grand Prix/child-scheduling slice is now
implemented under the user's confirmed policy. Tournaments support 4, 8 or 16
entrants. A Grand Prix may occupy 1–4 event cards, with the natural bracket
limits of 1–2 cards for four entrants, 1–3 for eight entrants, and 1–4 for
sixteen entrants. The player selects the opening date; later stages schedule
on the next best available date after the preceding event settles. Contracts,
purses and ownership carry through normally.

Injured or confirmed drug-failure entrants use ordinary matchmaking eligibility
for a replacement while preserving the original weight class, gender, title
status and tournament slot. If no eligible replacement exists, the whole
tournament moves to the next best date. Preliminary drug positives do not
trigger this policy. Tournament draws are resolved by a tournament-only
15-minute decider; if it still has no finish, judges select the winner.
Normal fight draws remain unchanged. AI promotions may create a separate,
rare Grand Prix at most once per year without changing ordinary scheduling;
century-scale qualification remains a development-only audit.

The new `grand_prix_regression_test.py` covers field sizing, stage
distribution, identity-safe registration, replacement/postponement, confirmed
drug-failure gating and decider isolation. The maintained regression runner,
fight-engine checks, child-promotion interaction/long-run checks and the final
stability playtest all pass. No EXE, active career or user save was rebuilt or
modified.

### Latest implementation ledger entry — G5 closeout for the approved scope

G5 is now closed for every bounded expansion that has an approved rule set and
working compatibility evidence. The accepted package includes the player-owned
Testing Desk catalogue/quote and frozen preliminary-case workflow; resumable
title-miss decisions (Remove Belt, Rebook Fight, Keep Belt with the title on the
line, Cancel Fight and Last-Minute Replacement); stable replacement/rank and
title-lineage evidence; the Academy Coach v1 role; company proposal and
ownership-history v1; one-night tournament history; regional feasibility and
host invitations; spectator pause policies and pinned checkpoints; editor
preflight/conversion; and the bounded, source-bound L0 audit with retained raw
reports, manifests and read-only history. These slices are identity-safe,
reload-safe, non-repairing on read and covered by the focused and maintained
regression suites.

The focused G5 verification run passes **164 tests**. The maintained
`run_regression_suite.py` also reports `ALL REQUESTED ISOLATED REGRESSION
SUITES PASSED`; the documented headless Matchmaking coordinate probe remains
the only environment skip. No EXE, active career or user save was rebuilt or
modified.

This closes the G5 gate for the approved first-playable release; it does not
silently enable rules that have not been specified. The following are retained
as explicit follow-up decisions rather than being represented as implemented:

| Held extension | Decisions required before implementation |
|---|---|
| Confirmed testing, appeals and sanctions | Jurisdiction and frequency; provider/effectiveness ranges and costs; confirmation/resample timing; first/repeat sanction table; appeal timing and payer; AI/spectator scope; booking, title and result consequences. |
| Multi-event Grand Prix and expanded child scheduling | Implemented and closed by the latest ledger entry above; future rule changes require a new policy decision. |
| Concurrent rights, audience segments and premium inventory | Shared-inventory ownership; allocation/tie rules; segment definitions and effects; bid/counter limits; affordability and settlement precedence. |
| Century-scale qualification | Authorised duration/seeds/source identities and explicit pass thresholds for population, finance, backlog and invariant evidence. |

Any of these can be opened as a separately approved follow-on slice. Until its
rules are supplied, the current G5 implementation remains the complete and
safe release boundary.

### Latest policy decision record — J5 drug-testing lifecycle

The player has now approved the core direction for the active testing model.
Testing frequency is chosen by the player; AI/spectator promotions use the same
model only a few times per year. A preliminary positive has **7 days** to reach
confirmation, and the fighter has a further **7 days** to appeal. The fighter
pays the appeal cost. For a first confirmed offence the player chooses between
a warning and a time suspension; a repeat offence receives a longer suspension
and removal from the company. Any effect on a booked fight, title or recorded
result pauses for an explicit player decision at that time rather than being
applied automatically.

Provider tiers, effectiveness/cost curves and the bounded suspension-duration
values remain implementation tuning owned by the development pass. They must
be visible, deterministic and capped; they cannot alter a result or sporting
record without the explicit player decision above. Jurisdiction-specific
eligibility and the exact player testing controls remain part of the same
settings surface and must be saved with the case's frozen policy snapshot.

### Latest implementation ledger entry — Stage 4 user acceptance of built J5/L0 scope

The user has accepted J5 and L0 as complete for the implementation that is
currently built. J5's accepted scope includes the player-owned Testing Desk
catalogue and quote flow, frozen case/evidence ledger, read-only workflow and
timeline, title-miss prompt with Remove Belt, Rebook Fight, Keep Belt, Cancel
Fight and Last-Minute Replacement, stable title/replacement identity, ranking
snapshots and settlement/lineage evidence. L0's accepted scope includes the
isolated source-bound audit runner, explicit seed and time limit, weekly/yearly
checkpoints, source-mismatch refusal, raw report and manifest retention,
read-only Audit History and defensive hard-invariant/measurement reporting.

This acceptance closes the two named implementation areas without claiming
unbuilt optional policy expansions as active mechanics. Confirmation/appeal/
sanction tables and the authorised century-scale qualification remain clearly
labelled follow-up work if those systems are later approved; they do not alter
the current J5/L0 acceptance. The combined current J5/title/replacement/audit
verification run passes **158 tests**, and the fresh source-matched audit retained its bounded
time-limit report/checkpoint without touching the user's save or EXE. Stage 4
of 6 remains active with **4 major gates** and **0 named card areas** awaiting
implementation under this acceptance.

### Latest implementation ledger entry — Stage 4 A5 relationship cases accepted

The built Talent Relations relationship-case slice is accepted as complete for
the approved v1 scope. Cases open only from an existing Contract Promise or
Career Journey and retain a stable case ID, fighter/source identity, original
obligations, reason, evidence references, due month, acknowledgement and
review history. The read model derives current duties from the authoritative
promise/story records, so partial delivery, unresolved work, transfer,
retirement and departure remain truthful without copying or rewriting the
underlying promise flags. Duplicate names stay separate by fighter ID, while
ID-less legacy rows receive deterministic IDs with duplicate-safe suffixes.

The player can acknowledge, select an existing supported action or review the
case; those case-management actions are idempotent and do not grant morale,
trust, title merit, deadline extensions, cash or RNG effects. Any real support
cost/effect remains in its existing authorised workflow. Malformed retained
cases render bounded evidence through a pure reader and remain untouched until
an explicit mutation or load/migration boundary. Relationship, Story Briefing,
Staff and UI-data coverage is green, including the focused relationship/story/
staff run (**78 tests**) and the maintained full regression runner. The current
accepted slice therefore has **0 named A5 areas** awaiting implementation;
future negotiated extensions, new relationship formulas and punitive rules
remain separately gated. Stage 4 of 6 remains active with **4 major gates**;
no EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 A6 recruitment packs accepted

The built Scouting Decision Packs slice is accepted as complete for the
approved v1 scope. The player can create a named pack from two to four
identity-linked targets, record its purpose, comparison context and notes,
rename it, and move it through the explicit Considering, Needs report, Ready
for negotiation or Archived decision states. Each pack captures the best
completed dossier evidence available at creation while current employer,
division, record and availability are re-read by fighter ID; departed or
retired candidates remain visible as historical alternatives with a warning.

Pack refreshes and target-board reads are observational: they do not commission
reports, expose hidden ratings, sign anyone, spend cash or consume scouting RNG.
ID-less legacy packs receive deterministic identity with duplicate-safe suffixes,
and edits route by saved pack ID rather than list position. The focused
recruitment-pack/story/relationship/staff run passes **12 tests**, with the
maintained full regression runner also green. Report updates, automatic signing,
new price mechanics and other policy-dependent recruitment effects remain
future gates. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 A7 followed stories accepted

The built Followed Stories and Story Briefings slice is accepted as complete
for the approved v1 scope. The player can follow or unfollow a thread, fighter
or company, acknowledge a retained beat through an explicit cursor, and snooze
notifications without deleting history. Briefings group recorded beats under
their durable story identity, show current stakes and disclose an expired
cursor/coverage gap instead of inventing continuity. Resolved threads and
unfollowed history remain readable.

Story and briefing readers are pure projections: opening, refreshing or sorting
does not advance a cursor, generate narrative, consume RNG or mutate the saved
subscription shelf. Malformed rows remain unchanged; ID-less legacy follows
receive deterministic identity from retained target/coverage facts with
duplicate-safe suffixes, and actions resolve by subscription ID. The focused
Story Briefing suite passes **8 tests** and is included in the maintained full
regression runner. New notification formulas, causal narrative generation and
automatic actions remain separately gated. No EXE or user save was rebuilt or
modified.

### Current stage summary — Stage 4 closed, accepted built-card queue clear

Stage **4 of 6** is closed for the approved first-playable scope. The previously tracked
Stage-4 named implementation inventory is now closed for its approved built
slices: S3, S4, J1, J4, J5, J6, J7, J8, A1, A2, A3 and L0 all have an accepted
or explicitly user-accepted implementation entry above. That leaves **0 named
card areas awaiting implementation in the accepted v1 queue**. The remaining
work is one optional G5 gate rather than an unlabelled backlog of missing cards.
Held expansions (active testing confirmation/appeal/sanction tables, optional
child/tournament economics and century-scale qualification) remain separate
policy decisions and are not silently counted as complete. No EXE or user save
was rebuilt or modified.

### Stage 4 closeout — G2/G3/G4 complete for the approved first-playable scope

Stage **4 of 6 is complete** for the approved first-playable upgrade. The
shared G2 management loop is covered by the maintained page/read-model,
identity, empty/error, responsive and no-mutation checks. G3 commercial
lifecycle work is covered by the Media, rights, sponsor-duty, renewal,
production, cash-runway and super-event closeout suites, including exactly-once
receipts and stale/reload boundaries. G4 Staff/AI work is covered by the
player-selected four-mode autonomy policy, accountable lead attribution,
evidence-gated work/progression, retention readout, durable AI employment,
affordability, payroll and expiry/market-return coverage.

The complete maintained `run_regression_suite.py` finished with
`ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`; the smoke, stability,
native-window, audio, Fight Night, persistence, UI-data, Media, Staff, profile,
testing, title/replacement, finance, scouting, regional, Combat Sports,
Foundation and long-run evidence suites all passed. `py_compile` and
`git diff --check` are clean. The expected headless Matchmaking coordinate
probe remains a documented environment skip, not a product failure.

**Remaining after Stage 4:** one optional gate, **G5**, remains policy-gated:
expanded confirmation/appeal/sanction tables, broader child/tournament/
rights economics and century-scale qualification require their own decisions
and calibration. They are not required to ship the approved first-playable
upgrade and have not been silently enabled. No EXE or user save was rebuilt or
modified.

### Latest verification ledger entry — Stage 4 integrated regression closeout

The maintained `run_regression_suite.py` completed with
`ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`. The run covered the Fight
Night presentation/archive/layout and experience suites, trait/profile/
persistence and identity paths, UI-data, Media, Staff, finance, scouting,
regional, Combat Sports, Foundation, tournament, booking, replacement/title
decision, J5 Testing Desk, L0 checkpoint/audit, native release, audio/window
lifecycle, fight-engine calibration, database-editor and stability checks.
The expected headless Matchmaking coordinate probe remained the documented
skip; it is not a product failure. Stage 4's accepted built scope is therefore
verified, with **0 named J5/L0 areas** left. No EXE or user save was rebuilt or
modified.

### Latest implementation ledger entry — Stage 4 J5 named-holder review wording

Upcoming Cards and archived Results now label a saved named-belt holder
directly in the title-eligibility line, alongside win/retain eligibility. The
wording is sourced only from the retained snapshot and remains `unknown` for
legacy rows without the field. Focused profile/title/replacement/audit
coverage remains **114 tests**; compilation and `git diff --check` are clean.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
open or policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 special-belt settlement role evidence

Settlement evidence now reads the saved named-belt-holder role, including
legacy snapshots whose generic champion flags are false. A holder's successful
defence is recorded as `retained` rather than a new title win; challenger and
unknown-role outcomes remain distinct. This is an evidence-only correction and
does not enable new sanction rules. Focused profile/title/replacement/audit
coverage passes **114 tests**; compilation and `git diff --check` are clean.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
open or policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 special-belt eligibility evidence

Title-miss snapshots now distinguish a named special-belt holder from the
generic champion/interim flags. The holder is retained as eligible to win and
eligible to retain, with an additive `special_belt_holder` evidence field;
challengers continue through the existing title-merit check. Upcoming review,
archived Results and settlement evidence can therefore describe the correct
role without recomputing current rankings or enabling new sanction rules.
Focused profile/title/replacement/audit coverage passes **113 tests**;
compilation and `git diff --check` are clean. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** open or policy-gated: J5 and L0.
No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 named-belt departure lineage

Named special-belt vacancy is now enforced at every roster-departure boundary,
not only the player contract path. Loans, recalls, child transfers, academy
matching rights, regional signings, retirement, expiry, distressed buyouts,
AI roster cuts/upgrades, swaps and editor removals pass the actual owning
promotion into the vacancy writer. The writer records the stable holder ID and
reason in that promotion's belt history, clears the saved holder, and removes
only the titles vacated there, preserving unrelated named titles on a fighter.
This prevents a child departure from changing the player's belts and ensures a
fighter who leaves with a named title always leaves an auditable vacancy. The
title-miss Remove Belt branch also handles named-belt holders by stable ID, and
  AI holder-protection recognises named-belt holders when evaluating roster cuts.
Focused profile/title/replacement/audit coverage passes **113 tests**; the
affected departure compatibility set passes **124 tests**;
compilation and `git diff --check` are clean. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** open or policy-gated: J5 and L0.
No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 narrow title-stakes weigh-in parity

The live weigh-in decision boundary now treats a saved `divisional_title` or
named `special_belt` as title stakes even when the broad `title` flag is absent.
The same bounded title-cut limit, explicit player choice, replacement review and
sanction evidence therefore apply to every retained title-stakes form. A
successful replacement keeps the title on the line unless the replaced corner
was a champion whose belt was explicitly protected by the existing rule. This
closes a legacy booking inconsistency without adding unapproved sanction,
appeal or AI policy. The focused title/replacement/audit set passes **71
tests**; `py_compile` and `git diff --check` are clean. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 per-corner title eligibility evidence

Title-miss snapshots now retain explicit `eligible_to_win` and
`eligible_to_retain` facts for every recorded corner. The Upcoming review and
archived Results readers expose those retained values, while legacy snapshots
without the fields show `unknown` instead of recomputing current rankings or
silently applying a new sanction rule. This completes the evidence shape for
the current safe J5 slice; confirmation, appeal, sanction, AI/spectator and
full policy-table mechanics remain gated by the decisions listed in J5/R06.
The focused title/replacement/audit set passes **72 tests**; compilation and
diff checks are clean. Stage 4 of 6 remains active with **4 major gates** and
**2 named card areas** open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 observed title-settlement evidence

The existing settlement transaction now appends the observed title outcome to
the retained sanction snapshot and matching fight log: official method,
winner/loser IDs, before/after holder flags, on-line state, outcome and a plain
reason. The snapshot update merges rather than replaces the original belt scope
and per-corner eligibility evidence. Matching is stable-ID first and refuses
to guess from duplicate names or row positions. Review and archived Results
display the settlement line as read-only evidence. Champion replacement now
also clears a named special belt from the bout and records it as not contested,
matching the existing absent-holder behavior. No sanction, appeal or AI policy
was invented. The focused title/replacement/audit set passes **73 tests**;
compilation and diff checks are clean. Stage 4 of 6 remains active with **4
major gates** and **2 named card areas** open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 explicit sanction envelope scope

All decision-branch sanction snapshots now retain additive `scheduled_title`,
`belt_id` and `title_key` fields with the original miss and eligibility facts.
The writer merges these fields instead of replacing the historical snapshot;
legacy rows without a retained scope stay unavailable rather than being
inferred from today's division or rankings. Focused title/replacement/audit
coverage remains **73 tests**, with compilation and diff checks clean. Stage 4
of 6 remains active with **4 major gates** and **2 named card areas** open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 malformed sanction settlement guard

The settlement evidence path now handles a wrong-type legacy sanction envelope
without normalising or overwriting it. It retains the raw field, stores the
separate observed settlement evidence and updates a matching stable-ID fight
log when available; duplicate names and row positions remain ineligible for
matching. This keeps a malformed historical field from aborting an otherwise
valid card settlement. Focused title/replacement/audit coverage remains **73
tests**, with compilation and diff checks clean. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** open or policy-gated: J5 and
L0. No EXE or user save was rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J4/J5 Fight History title evidence

Profile Fight History now carries the retained title decision and observed
settlement evidence into its read-only detail card, alongside the existing
at-the-time rankings, opponent record and replay provenance. The reader uses
stable archived IDs and keeps missing legacy evidence unavailable; it never
substitutes the opponent's current record or title state. The focused
profile/title/replacement/audit set passes **111 tests**; compilation and diff
checks are clean. Stage 4 of 6 remains active with **4 major gates** and **2
named card areas** open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

### Latest implementation ledger entry — Stage 4 J5 special-belt holder replacement guard

Emergency replacement now identifies a named special-belt holder by the saved
holder ID, with a unique legacy-name fallback, rather than relying only on the
generic `champion` flag. Replacing that holder clears every title flag,
including the named special belt, and records the bout as not contested. A
duplicate-name legacy holder fails closed. The focused
profile/title/replacement/audit set passes **111 tests**; compilation and diff
checks are clean. Stage 4 of 6 remains active with **4 major gates** and **2
named card areas** open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

## Overall assessment

The profile and Academy upgrades provide a useful visual direction, but the application still mixes several different generations of layout. The main problems are misplaced visual priority, inconsistent colours, crowded nested panels, and labels/previews that do not always describe the underlying game state correctly.

Fix the functional issues before extending the visual redesign. Matchmaking can hide its central interaction at a normal window size; Fight Night still loses intended key-moment separation; Rankings bypasses scouting visibility; commercial decisions can show misleading costs or remove an existing agreement.

### Scope and evidence

- Reviewed the current working source, not a newly rebuilt EXE. Existing game code, user saves and EXEs were not changed.
- Inspected a fresh disposable source session at a 1366×900 client geometry: Game & Saves, Dashboard, World, Regional Prospects, Rankings, Matchmaking and the sidebar Fight Night page. Applied Dark Mode and Light Office in that disposable session; closed it without saving.
- Reviewed profile, development, history, Fight Night, management and commercial code, with targeted in-memory/Tk diagnostics. Existing profile preview images were supporting visual evidence, not fresh screenshots of a rebuilt executable.
- This was a bounded review, not an exhaustive playthrough of every dialog, theme, save, editor operation or simulation outcome. Testing V2 was not loaded or modified.
- Priority **P1** means address in the first fix pass; **P2** means a confirmed correctness/usability issue for the next pass. Design recommendations are separated below.

## Confirmed issues

### 1. P1 — Matchmaking hides the fighter-selection table at ordinary window sizes

At 1366×900 with Show Details expanded, the layout switches to stacked mode and compresses Find Your Matchup until only its search row and part of its buttons are visible. The fighter table is clipped inside the pane, so ordinary outer-page scrolling cannot reveal it.

The outer split permits a 250px top pane, while its nested layout requires at least 150px for Draft Fight Card plus 230px for the fighter pane, before accounting for the latter's many controls. An isolated probe using the actual layout method allocated just 102px to the fighter pane when the outer split was 400px high. See [outer allocation](<D:/CodexFILES/MMA Warriors/ui.py:3158>), [stacked layout](<D:/CodexFILES/MMA Warriors/ui.py:1024>) and [fighter controls](<D:/CodexFILES/MMA Warriors/ui.py:3183>).

**Fix:** guarantee room for the controls and at least 4–6 fighter rows. In stacked mode, make the card collapsible/tabbed or allow the complete content to establish the page's scroll height. Test actual responsive geometry without forcing a different layout.

### 2. P1 — Fight Night's timestamps override key-moment separation

The clock tag inherits normal paragraph margins, spacing and background, then receives higher priority than event tags. Real Tk measurements showed an ordinary stamped action and a highlighted hit both taking 31px and starting at the same horizontal position, despite extra spacing being configured for the hit. The timestamp also interrupts the coloured background. See [tag defaults and priorities](<D:/CodexFILES/MMA Warriors/fight_night_presentation.py:89>).

**Fix:** restrict the clock tag to timestamp typography. Apply background, indentation and separation at the event-paragraph level. Assert rendered paragraph geometry, not only tag configuration.

### 3. P1 — Fight Night misses actual finishes and highlights some defended attacks

The current classifier does not cover several phrases the engine actually emits. With normal timestamps, examples include:

| Recorded wording | Current category | Problem |
|---|---|---|
| “The referee has seen enough and stops the contest.” | action | Actual stoppage loses finish emphasis |
| A submission chain connects and the defender “has to tap” | impact | Submission finish looks like an ordinary hit |
| Defender “goes unconscious” | action | Finish is not highlighted |
| Defender catches a body jab “on an elbow and pivots away” | impact | A defended strike looks like a key hit |
| Attacker looks for an elbow but the defender removes the lane | impact | Attempt is presented as impact |

See [classifier](<D:/CodexFILES/MMA Warriors/fight_night_presentation.py:37>) and authored examples at [stoppage](<D:/CodexFILES/MMA Warriors/fight_engine.py:5634>), [submission](<D:/CodexFILES/MMA Warriors/fight_engine.py:5461>) and [defended jab](<D:/CodexFILES/MMA Warriors/fight_engine.py:5276>).

**Fix:** bind emphasis to recorded event evidence where available; otherwise cover the real authored phrases with narrow, negation-aware classification. Preserve every original line and avoid inventing a landed outcome from a technique mention.

### 4. P1 — Rankings bypasses Scouting Mode

An unknown rival can show “Hidden” in the profile/scouting policy but expose exact overall in both Rankings modes and the ranking detail panel. A minimal fixture returned hidden visibility while Rankings displayed **OVR 77**. See [P4P rows](<D:/CodexFILES/MMA Warriors/views.py:13341>), [division rows](<D:/CodexFILES/MMA Warriors/views.py:13360>) and [detail](<D:/CodexFILES/MMA Warriors/views.py:13448>).

**Fix:** reuse the shared visibility/estimate policy for all displayed ratings. Public results and rankings can remain visible without revealing hidden ability.

### 5. P1 — Signing a ninth sponsor silently removes an active agreement

Acceptance inserts the new deal and truncates the active portfolio to eight. There is no capacity warning, replacement choice or departure explanation. The generated market contains 12 distinct categories, so this is not restricted to artificial duplicate-category data. An isolated acceptance check removed an existing deal with 12 months remaining. See [acceptance](<D:/CodexFILES/MMA Warriors/media.py:938>) and [market categories](<D:/CodexFILES/MMA Warriors/media.py:734>).

**Fix:** enforce a disclosed capacity before signing, or require an explicit replacement decision. Never silently discard an active contract.

### 6. P1 — Media campaign preview can show the wrong price

Changing spokesperson refreshes targets but not the action summary. Press Tour cost depends on fighter popularity: changing a popularity-40 fighter to popularity-90 can leave a **$12,000** preview while submission charges **$22,000**. See [selection binding](<D:/CodexFILES/MMA Warriors/ui.py:1697>), [target refresh](<D:/CodexFILES/MMA Warriors/views.py:7686>) and [price calculation](<D:/CodexFILES/MMA Warriors/media.py:354>).

**Fix:** recalculate price, eligibility, risk and action-point cost whenever a relevant input changes. Submission must validate the same terms the preview presents.

### 7. P2 — Theme changes leave mixed styles and unreadable status text

Switching an already-open Dashboard from Dark Mode to Light Office left its cards in the old dark colours while surrounding panels changed. The header became difficult to read, and urgent rows were extremely faint. `retheme_plain_widgets` handles Text/Listbox/Entry/Spinbox but not the custom card Frames/Labels and drawings. See [theme application](<D:/CodexFILES/MMA Warriors/ui.py:792>) and [widget traversal](<D:/CodexFILES/MMA Warriors/ui.py:828>).

Independently, several semantic row colours are fixed pale colours on Light Office's pale background. Measured contrast: Fight History wins **1.22:1**, losses **1.67:1**; active sponsors **1.22:1**; scouting recommendation **1.45:1**. Rankings and Regional Prospects were also visibly faint in the live inspection. See [history colours](<D:/CodexFILES/MMA Warriors/views.py:2901>), [scouting](<D:/CodexFILES/MMA Warriors/ui.py:2504>) and [sponsors](<D:/CodexFILES/MMA Warriors/ui.py:2722>).

**Fix:** centralise theme-aware semantic foreground/background pairs and retheme custom widgets explicitly. Test freshly opened pages and pages already open during a theme switch; retain text/icon statuses alongside colour.

### 8. P2 — Ranking labels combine different ranking systems

The profile's Identity & Career badge labels a gender-and-division world rank as **P4P**. Rankings detail also reads stored company division positions regardless of the selected mode. A two-division fixture displayed company/world P4P **#2** in the selected row but **“Rank: #1 | Previous: #2 | Movement: ▲1”** in the detail. The movement column similarly uses divisional history. See [profile badge](<D:/CodexFILES/MMA Warriors/views.py:2392>), [division-only calculation](<D:/CodexFILES/MMA Warriors/views.py:1271>) and [ranking detail](<D:/CodexFILES/MMA Warriors/views.py:13432>).

The P4P summary also counts champions in all matching rows while rendering only the first 50; the live page said **“208 champions shown.”** See [limit and count](<D:/CodexFILES/MMA Warriors/views.py:13337>).

**Fix:** distinguish Company Division, World Division, Company P4P and World P4P consistently. Detail and movement must describe the selected row's ranking system, or explicitly label their different scope. Count visible rows when saying “shown.”

### 9. P2 — Finance's monthly-burn forecast includes injuries across the world

The display counts injuries through `all_fighter_objects()`, including rivals, free agents and retirees, and adds $1,400 each to monthly burn. Actual monthly overhead and per-event medical settlement do not use that scope/frequency. See [forecast](<D:/CodexFILES/MMA Warriors/views.py:12989>), [fighter enumeration](<D:/CodexFILES/MMA Warriors/admin.py:1298>), [monthly costs](<D:/CodexFILES/MMA Warriors/world.py:6397>) and [event medical costs](<D:/CodexFILES/MMA Warriors/world.py:6087>).

**Fix:** derive forecasts from the same costs used at settlement. Separate committed monthly overhead, booked-event liabilities and contingent medical estimates.

### 10. P2 — Staff's “acceptance percentage” is actually an offer score

The dialog labels the score as an estimated percentage, but acceptance is `score + uniform(-8, 8) >= 62`. A displayed 70% always succeeds; 54% effectively never succeeds; 62% corresponds to 50%. See [preview and submission](<D:/CodexFILES/MMA Warriors/views.py:12815>).

**Fix:** show a probability derived from the actual roll, or rename the display “Offer strength.”

### 11. P2 — “Refresh Offers” performs an undisclosed paid action

The Media Rights button immediately spends **$3,500** and replaces the current offers without showing a price on the button or confirming the replacement. See [button](<D:/CodexFILES/MMA Warriors/ui.py:1785>) and [handler](<D:/CodexFILES/MMA Warriors/media.py:686>).

**Fix:** distinguish a free screen refresh from a paid market review. Show the price and replacement consequence before the player commits.

### 12. P2 — Sponsor value labels imply unsupported income forecasts

“12-MO VALUE” multiplies a fee **per event** by remaining months, capped at 12. This assumes one event per month and full activation without stating either assumption. Finance's expected sponsor income/event also totals full fees even where unmet activation requirements halve payment. See [value calculation](<D:/CodexFILES/MMA Warriors/media.py:797>) and [Finance summary](<D:/CodexFILES/MMA Warriors/views.py:12985>).

**Fix:** separate contracted maximum from expected payment, disclose event-count assumptions, and show activation requirements beside each active agreement.

### 13. P2 — Contracts filter does not apply to Combat Sports

The Show filter sits above both MMA and Combat Sports tabs, but the sports refresh ignores it. “Final month” can therefore still show 12-month sports contracts. See [filter placement](<D:/CodexFILES/MMA Warriors/ui.py:2914>) and [sports refresh](<D:/CodexFILES/MMA Warriors/views.py:689>).

**Fix:** implement consistent filtering or visibly scope the control to the MMA tab.

### 14. P2 — Profile Injury Risk can disagree with live trait effects

Contract & Business displays stored `injury_proneness`, while current injury checks use trait-adjusted `effective_injury_tendency`. They can diverge after trait evolution relative to the saved baseline. See [profile field](<D:/CodexFILES/MMA Warriors/views.py:2666>) and [live calculation](<D:/CodexFILES/MMA Warriors/fighter_traits.py:86>).

**Fix:** show current effective risk, with the stored baseline available in explanatory details if useful. Do not rewrite saved baselines to repair a display.

### 15. P2 — Compact Fight Night becomes difficult to read with Settings open

In the actual EventMixin window at **820×540**, the commentary viewport measured **511×179px** with Settings closed and **511×82px** with Settings open. See [layout](<D:/CodexFILES/MMA Warriors/fight_night_layout.py:36>).

**Fix:** move settings into a separate dialog/overlay or use a compact arrangement that preserves reading height and the established portrait sizes.

### 16. P2 — Round Read and Bout Desk do not respond to the mouse wheel

These canvas panels have scrollbars but no wheel bindings. A 60-line summary retained its scroll position after a wheel event. See [scroller construction](<D:/CodexFILES/MMA Warriors/fight_night_layout.py:120>).

**Fix:** use the existing wheel-aware scrolling behaviour, scoped to the hovered panel so it does not hijack another reader.

## General appearance and workflow improvements

These are design recommendations, not additional confirmed simulation errors.

| Page/area | Main issue | Recommended direction |
|---|---|---|
| Dashboard | Good card foundation, but duplicate Booking calls to action and a long queue compete for attention | One clear next action, grouped risks, concise “since last week” changes; retain full advice on selection |
| Game & Saves | Fresh empty library occupies most of the page; starting/spectator controls extend below the fold | Strong empty-state start/load choices; separate career management from database administration |
| Matchmaking | Show setup, draft card and fighter controls compete vertically | A compact show summary and protected fighter workspace; persistent selected-pair/action area |
| Profile / Core Skills | Persistent identity header plus repeated tab headings consume space; rating colours use warning red for some respectable abilities | Compact header option, coherent skill scale, tightly aligned bars and supporting labels |
| Fight History | Large selected-bout/ranking panels dominate the ledger; retained preview shows about five rows at 1200×880 | Collapsible or side-positioned comparison details; larger record viewport; preserve every field and custom column control |
| Development | Contribution bars help, but “Monthly score” and the next useful action need explanation | A plain-language outlook and management suggestion, with the complete existing driver breakdown retained |
| Finance / Sponsors | Dense summary text, short portfolio table and weak active-deal detail | Cash/commitment/event-income cards; selected agreement with fee, expiry, activation checklist and expected payment |
| Media Desk / Rights | Costs, offer terms and campaign inputs are spread across controls | A single live decision preview; clear negotiated/available/blocked states and next-action feedback |
| Staff | Short roster/market tables followed by a large effects text block | Department cards for lead staff, effects, vacancies and expiry; selected candidate comparison |
| Contracts | Wide ledger and legend-heavy presentation | Internal scrollbars, selected-contract summary and clearly separated renew/release actions |
| Scouting / Fighter Search / Free Agents | Different discovery pages use different filter, refresh and table conventions | Shared filter layout, visible result counts and preserved selection; retain Search pagination and hidden-rating policy |
| Regional Prospects | Empty default filter looks like a blank page; muted rows are particularly faint in Light Office | Explain why nobody qualifies and offer “Browse developing fighters”; use readable status badges |
| World / Companies / Regions | Older table-plus-text layouts; World clips right-side buttons and gym columns at 1366px | Selected-company/gym cards, responsive stacking, wrapped news excerpts and local table scrolling |
| Rankings | Dense wide table with ambiguous Co/World/Move labels | Explicit ranking scope labels, concise leader cards and a detail panel that agrees with the row |
| Combat Sports | Broad table and plain detail transcript; refresh resets sport selection | Preserve selection and introduce a selected-sport management summary |
| Academy | Newer Development Hub and decision bar provide clearer hierarchy | Reuse its patterns elsewhere; no additional definite Academy error found in this bounded pass |
| Sidebar Fight Night | Navigation opens an old plain-text Event Report, separate from the upgraded live viewer | Rename it Event Log/Archive or create a coherent Fight Night landing page linking live events and archives |

The old sidebar log is still a plain Courier Text widget and `write_log` inserts unstyled text. See [page](<D:/CodexFILES/MMA Warriors/ui.py:4122>) and [refresh](<D:/CodexFILES/MMA Warriors/world.py:19411>). This is a navigation/presentation mismatch, not evidence that the separate live viewer lost its entire redesign.

Other useful refinements: make Camp Plan resizable and show gym/readiness trade-offs ([dialog](<D:/CodexFILES/MMA Warriors/views.py:14078>)); debounce Scouting search, which currently refreshes on every key release ([binding](<D:/CodexFILES/MMA Warriors/ui.py:2430>)). Actual search latency was not benchmarked, so no performance improvement is claimed.

## Recommended implementation order

1. **Protect decisions and state:** sponsor capacity, campaign preview accuracy, scouting visibility, finance forecasts and ranking semantics.
2. **Restore core workflows:** Matchmaking's real responsive layout, Fight Night classification/separation, compact reading height and wheel scrolling.
3. **Unify the visual foundation:** theme-aware status colours, custom-widget retheming, readable headers, consistent spacing and table controls.
4. **Upgrade older pages:** Finance/Staff/Contracts, then World/Companies/Regions, and the Fight Night landing page. Compact the profile/history header areas alongside this work.

Retain full records, explanations and column access. Use progressive disclosure for secondary details; do not solve density by deleting information.

## Verification performed and gaps

Ran through the isolated regression runner:

| Suite | Result |
|---|---|
| fight_night_presentation_test.py | 3 passed |
| fight_night_archive_regression_test.py | 3 passed |
| fight_night_layout_regression_test.py | 5 passed |
| ui_data_regression_test.py | 22 passed |

**33 checks passed.** These results do not invalidate the defects above:

- Existing Fight Night tests check selected phrases and configured styles, not all real finish wording or rendered timestamp/event paragraph geometry.
- Compact layout tests use abbreviated settings controls, missing the actual window's 82px open-settings reader.
- The existing smoke test explicitly forces horizontal Matchmaking layout after noting the stacked layout squeezes its rows away ([smoke_test.py:1017](<D:/CodexFILES/MMA Warriors/smoke_test.py:1017>)). New geometry tests must not bypass the broken mode.
- Regional Prospects opened and populated **1,120** rows in the disposable session when All Regional was selected. The prior undefined-company crash was not reproduced; its row-promotion regression also passed.
- No fresh game exception appeared during the inspected navigation. This is not a blanket crash-free certification.
- Full shipping/native calibration suites were not rerun: no mechanics were changed and no EXE was packaged.

After fixes, add targeted regressions for all affected decisions plus live geometry/theme-switch checks, then run the applicable integration suites before any separately requested rebuild.

## Actual game updates — Media and Staff systems

Added 12 September 2026 at the user's request. **Status: partially implemented; the ledger below is authoritative.** This section covers changes to gameplay, not merely presentation. The existing UI findings above remain valid; the additional system findings below extend that review. Implemented slices are explicitly marked in the ledger; proposed mechanics and unresolved HOLD items remain gated.

### Direction

Make these systems a connected management loop:

**Choose a priority → assign responsible staff → commit a limited budget/capacity → deliver work → review the consequences → adjust the next plan.**

The player should make meaningful choices about the next show and the next month, without needing to repeat routine clicks every week. Staff should explain what they are doing, Media should explain what each campaign is trying to achieve, and completed events should show which commercial commitments were met.

New effects, penalties and progression are explicit balance changes. They must not be slipped into the UI repair pass or described as simulation-neutral.

### What already exists and should be retained

| System | Existing gameplay foundation |
|---|---|
| Media campaigns | Eight actions, seven strategies, Marketing-dependent weekly capacity of 2–4 points for the player, costs, fighter/callout cooldowns, outcome bands, popularity limits, public trust and rivalry effects. [Campaign rules](<D:/CodexFILES/MMA Warriors/media.py:176>), [resolution](<D:/CodexFILES/MMA Warriors/media.py:351>). |
| Broadcast rights | Eight default outlets plus universe additions; territory, reach, standards, fees, event quotas, bonuses, replacement/termination costs, relationships and termination after three delivery failures. One counter per offer. [Market](<D:/CodexFILES/MMA Warriors/media.py:23>), [contracts](<D:/CodexFILES/MMA Warriors/media.py:259>), [delivery](<D:/CodexFILES/MMA Warriors/media.py:579>). |
| Sponsors | Monthly pitch briefs, competing offers, category conflicts, one counter, and trust/stability/ranked-campaign activation checks that can halve event fees. [Pitches](<D:/CodexFILES/MMA Warriors/media.py:721>), [activation](<D:/CodexFILES/MMA Warriors/media.py:812>). |
| Staff | Seven hireable roles; skill and morale determine effective quality, with bounded passive effects. Salary/term negotiation, expiry warnings, severance and staff identities already exist. [Roles](<D:/CodexFILES/MMA Warriors/constants.py:18>), [effective quality](<D:/CodexFILES/MMA Warriors/world.py:2487>), [contracts](<D:/CodexFILES/MMA Warriors/world.py:2529>). |
| Scouts | Detailed skills, specialties, assignment capacity, reports, regional searches, ongoing work, Academy-network ownership and optional automatic assignment. These are working systems to integrate, not rebuild. [Assignment logic](<D:/CodexFILES/MMA Warriors/world.py:8997>), [automatic work](<D:/CodexFILES/MMA Warriors/world.py:9278>). |
| Staff stories | ID-linked tenures, first-of-kind contributions/setbacks and legacy records. These are observational history, not an existing skill-development system. [Contributions](<D:/CodexFILES/MMA Warriors/world.py:1638>). |
| AI and persistence | AI promotions already choose media deals and run some campaigns. Player and promotion finance preserve contract, campaign, relationship and audience records; `media_rights` aliases the active contract. [AI media](<D:/CodexFILES/MMA Warriors/media.py:525>), [save-state compatibility](<D:/CodexFILES/MMA Warriors/media.py:103>). |

### Additional system findings

#### Media: where the current gameplay needs work

1. **Campaigns have weak event targeting.** Event audience lift takes recent campaign heat from the current/previous month, capped to the first eight records, without matching a campaign to that event, its fighters or its region. Most actions share the same outcome formula. Regional Tour records the region in its description, but that target is not used by this event-lift calculation. This limits the distinction between planning a specific show and generating general publicity. [Event campaign lift](<D:/CodexFILES/MMA Warriors/media.py:588>).
2. **The displayed backfire percentage is not the actual chance.** The advertised `risk` value is not used by campaign resolution; outcome bands come from fighter/Marketing/strategy quality and an integer random roll. Correct this before making risk a strategic choice. [Preview](<D:/CodexFILES/MMA Warriors/media.py:362>), [actual bands](<D:/CodexFILES/MMA Warriors/media.py:414>).
3. **Production standards are advertised but not enforced in the reviewed delivery rules.** Eligibility checks active status, coverage and territory; delivery checks rating/card quality. Neither checks the advertised `min_production`. A diagnostic requiring production 99 remained eligible with production quality 1. Define a canonical production-quality value before adding enforcement or financial consequences. [Eligibility](<D:/CodexFILES/MMA Warriors/media.py:336>), [delivery](<D:/CodexFILES/MMA Warriors/media.py:598>).
4. **Delivery and relationship feedback can contradict one another.** A high-rating event can fail the card requirement, receive a breach strike, and still gain relationship +4. The high-rating relationship branch runs before the delivery check. Distinguish audience appreciation from contractual compliance, or make the combined relationship assessment consistent. [Relationship calculation](<D:/CodexFILES/MMA Warriors/media.py:599>), [breach recording](<D:/CodexFILES/MMA Warriors/media.py:608>).
5. **Expiry does not distinguish fulfilment from shortfall.** A deal with events still outstanding is labelled Completed when its months run out. The system also lacks a dedicated forward-start renewal workflow. [Monthly lifecycle](<D:/CodexFILES/MMA Warriors/media.py:544>).
6. **Negotiated guarantee fields can disagree.** Higher Guarantee updates `fee` but not `guarantee_per_event`. A diagnostic produced 11,000 versus 10,000. Synchronise these fields through counter, signing and settlement; audit legacy reconciliation without silently reducing an agreed fee. [Counter](<D:/CodexFILES/MMA Warriors/media.py:920>).
7. **Sponsor duties need explicit timing.** Brand placement currently passes automatically; that can remain automatic fulfilment. The monthly-event duty has no separate month-end missed-duty assessment. Distinguish automatic delivery, player action, pending period-end work and completed obligations. Preserve the established half-fee rule for existing checked conditions. [Activation rules](<D:/CodexFILES/MMA Warriors/media.py:812>).

The earlier sponsor-capacity, stale-price, paid-refresh and misleading-valuation findings are prerequisites too.

#### Staff: where the current gameplay needs work

1. **The wrong employee can receive credit.** Live effects choose the highest morale-adjusted quality, but the visible/narrative lead is chosen by raw skill. Resolve the actual contributor consistently. [Effect](<D:/CodexFILES/MMA Warriors/world.py:2487>), [visible lead](<D:/CodexFILES/MMA Warriors/views.py:12040>), [story attribution](<D:/CodexFILES/MMA Warriors/world.py:1625>).
2. **Additional non-Scout staff have little marginal use.** Passive bonuses take a maximum, not a sum, and only Scouts have recognised workload. Extra hires generally add payroll without increasing a department's passive effect or active capacity. The hire preview should explain this accurately. [Quality calculation](<D:/CodexFILES/MMA Warriors/world.py:2487>), [busy check](<D:/CodexFILES/MMA Warriors/world.py:2558>).
3. **Non-Scout specialisations and careers are shallow mechanically.** Specialties are largely descriptive, skills/reputation are effectively static in ordinary operations, and morale/negotiation heat are driven mainly by contract interactions. Existing legacy stories must not be presented as skill XP. [Profile defaults](<D:/CodexFILES/MMA Warriors/world.py:2637>), [negotiation](<D:/CodexFILES/MMA Warriors/views.py:12777>).
4. **AI hiring lacks a durable employment transition.** The market removes a candidate before checking affordability. A successful branch can charge money and announce a hire without adding that person to the promotion's existing staff collection. The fix needs coherent employment, payroll and expiry handling, not just a different headline. [AI hiring](<D:/CodexFILES/MMA Warriors/views.py:12882>), [promotion staff field](<D:/CodexFILES/MMA Warriors/models.py:406>).
5. **Academy calculations reference an unavailable role.** They read `staff_skill("Trainer")`, but Trainer is absent from the seven-role hireable catalogue. Ordinary games therefore use the fallback. Adding an Academy Coach would change development and requires a deliberate design/calibration pass. [Academy reads](<D:/CodexFILES/MMA Warriors/world.py:7427>), [training quality](<D:/CodexFILES/MMA Warriors/world.py:7597>).
6. **Compliance needs its own gameplay redesign before more autonomy.** Manual testing rolls positives for sampled fighters without consulting a persisted violation state and represents the consequence as injury. Better officers increase that roll. Define findings, confirmation and suspension separately before permitting automatic testing or advertising stronger detection as a straightforward benefit. Never reinterpret old injuries as historical violations. [Current testing](<D:/CodexFILES/MMA Warriors/views.py:12957>).

### Media upgrade plan

#### M1 — Persistent campaign plans with a clear purpose

Introduce an optional plan for the next event or a defined monthly objective. A plan records its target, responsible staff ID, budget ceiling, permitted actions, deadline and intended outcome. Existing immediate campaign actions remain available and use the same capacity pool.

Start with one primary plan per promotion. This is a proposed initial scope, not an approved balance limit. Preserve the existing weekly action-point budget in the first implementation; opening or editing a plan must not consume points, spend money or roll outcomes.

| Objective | Player decision | Proposed gameplay distinction |
|---|---|---|
| Promote the next show | Choose the scheduled event, featured fighters and spend ceiling | Campaign contribution primarily follows that event; postponement/cancellation prompts a retarget or cancellation decision. |
| Build a prospect | Choose a developing fighter and suitable appearances | Slower, focused exposure with existing popularity ceilings; repeated identical appearances have diminishing value. No purchased skill or guaranteed sporting opportunity. |
| Support a sponsor | Choose the relevant partner and eligible spokesperson | A completed qualifying appearance supplies evidence for the agreed activation duty; it does not produce an extra duplicate sponsorship payment. |
| Enter a region | Choose a target region and matching event | A bounded, time-limited regional campaign contribution affects relevant shows instead of automatically boosting unrelated events. |
| Protect trust | Choose a response to a recorded controversy or reputational problem | Trade campaign capacity and spending for a bounded trust-recovery opportunity; no instant erasure of history. |

Make action choice matter through context, suitability, timing and opportunity cost. Keep interviews useful for small promotions; expensive campaigns should offer a particular advantage, not universally dominate free actions. Match campaign lift to event/fighter/region IDs and apply a declared decay window. The current aggregate lift bounds can be an initial calibration reference, but keeping a cap does not prove unchanged balance.

New campaign records retain stable IDs plus display-name snapshots. Historical name-only records remain readable and explicitly unlinked where attribution is uncertain; do not invent targets or replay their effects during migration.

**M1 acceptance:** a campaign for Event A has a defined, bounded relationship to Event B; duplicate names resolve correctly; one completion charges once; moving an event does not silently reroll work; repeated page refreshes change neither state nor RNG.

#### M2 — Broadcaster account management and renewals

Use the existing relationship system rather than adding a second goodwill currency.

- Give new agreements a small delivery plan: two or three measurable commitments, each with a period, evidence source and declared consequence. Examples include eligible shows delivered, agreed production standard and an appearance by a scheduled headliner.
- Base obligations on choices the player controls. Do not require a particular fighter to win, a knockout to occur or a manufactured rematch.
- Provide a monthly account review: delivered work, shortfalls, upcoming deadlines and renewal outlook. Offer choices such as improve production, redirect campaign capacity, negotiate a make-good where supported, or accept the stated consequence.
- Introduce renewal discussions before expiry. Two months or two remaining events is a proposed starting trigger to test. Offer similar terms, a guarantee/obligation trade-off, or a return to the market; retain one counter per offer.
- A scheduled successor contract starts when the current deal ends. It must not accidentally buy out the current agreement, overlap payments or reset owed events.
- Record Fulfilled, Expired with shortfall and Terminated distinctly. Existing saves receive no invented retrospective debts or breach strikes.

First define how production quality is measured and whether a missed standard affects eligibility, bonuses or delivery compliance. Apply newly enforced consequences prospectively with clear terms, especially for legacy contracts that were signed under the old rules.

**M2 acceptance:** production boundaries and every obligation have source-backed evidence; high audience approval cannot silently cancel a contractual breach; renewal survives save/reload; current and successor deals never pay for the same entitlement twice.

#### M3 — Sponsor portfolio work and event settlement receipts

- Keep automatic placement automatic and label it as such.
- Make meaningful duties visible in one portfolio plan. Existing qualifying campaigns should fulfil the relevant duty without requiring an extra confirmation click.
- Keep the existing current-roster/current-month champion or top-10 rule for legacy ranked campaigns. New identity links must not weaken that rule.
- Treat monthly duties as pending until their deadline. Introduce any new missed-month consequence only through clearly versioned, prospectively accepted terms; do not add an undisclosed penalty on top of existing half-fee settlement.
- Keep trust and stability meaningful. Reject unsupported promises instead of allowing the player to sign obligations the UI cannot explain.
- At event settlement, produce one commercial receipt showing guarantee, bonus, each sponsor's payment, shortfall reasons, completed duties and relationship changes. Reopening a report is read-only.

Preserve the eight-sponsor capacity unless a separate design decision changes it. Portfolio growth should mean choosing and servicing appropriate partners, not stacking unlimited income.

#### Later Media expansions

Defer outlet-specific audience segments, real concurrent regional/non-exclusive packages, premium specials and ambassador contracts until the single-plan/renewal lifecycle is stable. Although current deals can be labelled Non-exclusive, acceptance still replaces the active deal; concurrent distribution requires explicit conflict, rights-selection and settlement rules. Rival competition for scarce premium broadcast slots also needs AI/economic calibration before introduction.

### Staff upgrade plan

#### S1 — Department briefs and accountable work

Create persistent department priorities with a responsible employee, work queue, spending permission and an evidence-backed review. Balanced/default briefs preserve current passive effects and existing unattended behaviour.

Initially resolve the automatic lead using actual effective quality. Show lead, supporting staff, current commitments and the marginal value of a proposed hire. Do not stack all same-role skill bonuses. An explicit manual appointment system can follow when the consequences of choosing a different lead are clearly defined.

| Department | Initial active work | Trade-off or boundary |
|---|---|---|
| Marketing | Prepare the media plan, recommend appearances/pitches and manage approved work | Event promotion versus prospect exposure versus sponsor duty within the existing action and spending limits. |
| Matchmaking | Prepare shortlists under contender-building, prospect-development or commercial priorities | Suggestions must first pass existing sporting merit, medical, rematch and champion protections. The player still approves the card. |
| Talent Relations | Maintain a renewal/retention queue and prepare terms for priority fighters | Retain key talent versus control wage growth. Reuse existing negotiation/batch-renewal rules; sign only within explicit delegated limits. |
| Scouting | Surface existing assignments, capacity, ongoing searches and Academy-network work | Reuse the current system and auto-assignment policy; do not charge twice or create a second competing queue. |
| Medical | Review upcoming fighter availability and flag follow-up/return-date problems | Initially an actionable case queue using existing medical mechanics, not permission to clear injuries or shorten confirmed layoffs. |
| Broadcast | Review the next show's production plan and contractual readiness | Budget versus agreed quality; identify delivery risk before committing costs. Do not invent a second production bonus. |
| Compliance | Present current testing policy, costs and unresolved concerns | Do not delegate automatic tests until the separate finding/suspension model is approved and validated. |

Pilot the active workflow in Marketing, Matchmaking and Talent Relations. Use one optional active department project per non-Scout department initially; measure workload from real commitments rather than adding a generic fatigue bar. Additional employees can later provide bounded concurrent-project capacity or cover absences, not unlimited passive percentage bonuses.

Prepared advice and executed work must be distinct. A recommendation does not spend money, satisfy a sponsor or count as staff development. Every executable project states its cost, duration, output and relevant existing mechanic before commitment.

#### S2 — Delegation with limits and useful reporting

**User decision, 12 September 2026:** staff autonomy is chosen by the player: Manual, Recommendations, Selective Recommendations, or Full Auto. Selective Recommendations means the player chooses which topics/departments may produce advice. R06 defines the mode boundaries and remaining choices. Players control delegated action types, per-action ceiling, monthly budget, minimum cash reserve and permitted target pool. Manual and delegated actions consume the same budgets/capacity; delegation creates no extra attempts or free rolls.

Pause stale or invalid work when its fighter, staff member, event or contract changes. Explain the reason and ask for a new decision; do not silently substitute another fighter or spend against changed terms.

Use one monthly operations review plus actionable exceptions: expiring agreements, a blocked assignment, an unaffordable commitment or a delivery deadline. Avoid mandatory weekly popups. If a player leaves the default policy alone, the current basic game should continue without a new penalty for not using the feature.

**S1/S2 acceptance:** the credited employee is the actual responsible contributor; no same-role passive stacking; saved projects resume once; employee departure releases or explicitly hands over work; no automatic signing, firing, testing or spending outside the selected policy.

#### S3 — Specialisations, development and retention

After the project system is proven, connect non-Scout specialties to narrow mechanics with an explanation, trigger, advantage, trade-off and cap. Do not turn all descriptive specialties into generic bonuses. Unknown legacy specialties can remain explicitly descriptive until mapped safely.

Add gradual development from distinct completed work over sustained periods. A maximum of one skill point per quarter is a possible starting tuning target, not a promised shipping number. Retain current effect ceilings, add diminishing returns, and test against task-farming. Narrative milestones and merely opening a page must never award development.

Build retention around sustained role satisfaction, agreed workload, tenure and contract competitiveness. Provide warnings and a chance to respond before a new departure mechanism fires. Let unsuccessful negotiation heat cool over a defined period only as an explicit balance change. Preserve existing salary/term offers, severance and contract warnings.

Do not make task progression depend on narrative tracking being enabled. Commit actual work first; then use the existing tenure/contribution system to describe it. A sellout is evidence of an event outcome, not proof that a named employee caused all the revenue.

#### S4 — Durable AI employment and later specialist systems

Fix AI staff recruitment as a complete lifecycle: resolve an affordable target, commit the same staff ID to a bounded promotion staff list, debit once, charge appropriate ongoing payroll, tick the contract, and handle expiry/return to market. An unaffordable attempt retains the candidate. Retain any valid pre-existing promotion staff and do not manufacture past employment from old headlines.

Measure the effect of added ongoing costs before releasing this change; a hire-record fix must not create unlimited AI payroll or bankrupt smaller promotions. Extend staff benefits to AI only through declared, bounded rules rather than accidental player-only advantages.

Two later projects need separate mechanical sign-off:

- **Academy Coach:** append a deliberate hireable role or explicitly route coaching through the existing gym system. Retain the old fallback for existing saves until the new role/path is used. Validate fighter development before changing Trainer reads.
- **Compliance and suspension:** model recorded findings, confirmation/appeal policy where supported, suspension distinct from injury, costs and booking eligibility. Stronger officers should improve the defined testing process, not simply create more arbitrary injured fighters. Existing injuries remain injuries.

### Implementation sequence and release boundaries

| Batch | Deliverable | Exit condition |
|---|---|---|
| G0 — Integrity and truthful rules | Sponsor capacity, preview/counter consistency, actual staff-lead attribution, defined media delivery/expiry semantics and reproductions for AI hiring gaps | Existing agreements/identities preserved; no misleading price/probability; each proposed new enforcement rule clearly separated from a display repair. |
| G1 — Shared work records | Additive plan/brief state, stable target IDs, commitment validation and exactly-once completion records | Default/disabled path retains existing behaviour; save/reload, cancellation, budget and stale-target tests pass. |
| G2 — First playable management loop | M1 targeted campaign plan plus S1/S2 pilot departments and monthly review | Player can plan, delegate within limits, see delivered work and make the next decision without repetitive mandatory clicks. |
| G3 — Commercial lifecycle | M2/M3 broadcaster objectives, prospective renewals, sponsor duty timing and unified receipts | Player/AI settlement reconciles; no duplicate payment, reset quota or retroactive legacy penalty. |
| G4 — Staff careers and AI | Durable AI employment, bounded specialties/progression/retention | Long-run affordability, anti-farming and identity/lifecycle tests pass before new bonuses ship. |
| G5 — Optional expansion | Academy Coach, compliance model, audience segments or concurrent rights | Each has its own approved rules, calibration and compatibility evidence. Not required for the first playable upgrade. |

The UI work should consume these verified rules and work records, not duplicate their calculations. Media and Staff pages can then show plan cards, assignment status, deadlines and actual results alongside the earlier layout upgrades.

### Save, economy and simulation safeguards

- Add optional, versioned plan/department/objective records without replacing existing employment or finance dictionaries. Preserve unknown fields, salaries, terms, staff IDs, Scout references, contract IDs, tenure keys, histories and the `media_rights` object alias.
- Old saves start with neutral/default briefs and no invented overdue objectives. Do not reconstruct missed commitments, old campaign targets, vanished sponsors or AI employees from ambiguous text.
- Snapshot agreed terms and references when work is committed. Keep active obligations until resolved; a display-history cap must not discard unresolved work.
- Keep all previews observational. Existing ensure/remaining-capacity helpers can normalise state or reset counters; do not call them blindly inside a supposedly pure calculator.
- Integrate into existing calendar and event-settlement ownership. Pay and apply results once, persist them, and make report/replay reads non-mutating. Keep player and AI finance paths reconciled; do not add a second rights guarantee or sponsor payout.
- Run bounded work queues during calendar advancement; do not scan complete world histories on each refresh. Record responsible IDs and evidence as work completes.
- Presentation fixes should preserve RNG and outcomes. Opted-in gameplay changes intentionally alter management results and possibly later career trajectories; use fresh seeded evidence and source-bound release checks, not an old UI or native certificate as proof of neutrality.
- Keep sporting eligibility and fight-engine selection separate. Staff/media strategy must not purchase title merit, force a rematch, select a winner or expose future fight telemetry.

### Verification and balancing plan

Add focused Media/Staff system regressions alongside the existing suites:

1. **State and identity:** duplicate names, existing IDs, legacy portfolios/staff lists, no-staff baseline, raw-skill versus effective-quality leads, and save/reload mid-plan.
2. **Commitment safety:** repeated previews preserve state/RNG; cancellation preserves uncommitted funds; stale terms cannot charge; manual/delegated work share limits; one work item/event settles once.
3. **Media rules:** all actual campaign outcome boundaries, target matching and decay, counter aliases, production standards, delivery versus relationship consistency, fulfilled versus expired-shortfall deals, successor renewals and sponsor period timing.
4. **Staff rules:** Scout capacity and expiry protections remain intact; no passive stacking; project ownership/handover; progression caps and anti-farming; narratives disabled still permit legitimate work.
5. **AI lifecycle:** failed recruitment retains candidates; successful employment persists once with one debit; payroll/expiry/market return remain bounded; spectator simulation needs no player prompts.
6. **Economy:** compare small, medium and major promotions over multiple seeds and calendars. Track profitability, campaign spend, exposure growth, sponsor fulfilment, rights breaches/renewals, staff payroll, AI survival and player actions required per month. Include no events, several events, cancelled shows and long unattended advancement. Targets must be agreed from baselines before tuning, not chosen after a favourable run.
7. **Native/development gates:** new Academy, medical, training or other mechanically relevant staff effects require fresh applicable source-bound checks. Run the repository's full shipping and release requirements before any separately requested packaging; do not widen certificate exceptions to avoid new evidence.

For this added review, **`media_system_test.py` and `contracts_finance_regression_test.py` passed through the isolated runner**. Their existing player/AI/save checks are a baseline, not validation of the proposed mechanics. No gameplay upgrade, save migration, balance calibration or EXE rebuild was performed in this task.

## Developer-journal comparison — recommended MMA Warriors features

### Recommendation: extend the management loop before adding more simulation systems

**The best next release is a connected booking, event-preparation and staff workflow, supported by trustworthy historical records.** MMA Warriors already has much of the underlying simulation. The opportunity is to make its choices, consequences and continuing obligations visible and manageable.

This section extends the Media/Staff roadmap above; it does not replace it or authorise implementation. The comparison uses the current working source and the [WMMA6 developer's journal, including its numbered entries and concluding feature list](https://forum.greydogsoftware.com/topic/62175-wmma6-developers-journal/#comment-1584182). Journal references identify inspiration only. The designs, priorities, data structures and acceptance requirements below are original proposals for MMA Warriors, not descriptions of WMMA6's internal implementation.

The source prompts most relevant to this plan are:

| Journal entries | Inspiration | Our work item |
|---|---|---|
| 5, 22, 26, 43, 143 | Booking assistance and workload reduction | J1, J3 |
| 36, 108, 123, 144 | Event promotion and fighter relationships | J2 |
| 109, 119–122, 137, 146 | Contract and employment context | J3, existing S3 |
| 10–12, 20, 30, 81 | Historical and ranking context | J4 |
| 24–25, concluding list | Recorded disciplinary and title decisions | J5 |
| 61, 72, 82, 134 | Coaching and understandable assessments | J6, J10 |
| 14, 21, 75–79 | Company cooperation and subsidiaries | J7 |
| 86–93 | Tournament organisation and memory | J8 |
| 32–33, 83 | Regional opportunity and division planning | J9 |
| 17, 38, 68–70, 136 | Help, feedback and discovery | J10 |
| 106, 110–111 | Advancement and recovery controls | J11 |
| 7, 116–117, concluding list | Editor safety and reusable configurations | J12 |

**Status terminology:** “Extend” means a working source path already exists, not that the complete proposed experience exists. “New layer” means new persistent state or rules are needed over an existing foundation. “Not located” describes this targeted inspection, not proof that no related code exists anywhere. Priority is a planning judgement, not a measured player-impact score or delivery estimate.

### J1 — A booking workbench that explains and remembers the plan

**High priority · Extend · builds on S1/S2.** Matchup suggestions, date/division filters and booking warnings already exist. The current assistant offers a recommendation; it is not a new system we need to invent. Both assistant/manual eligibility paths still reject a currently injured fighter before future-date clearance. See [assistant recommendations](<D:/CodexFILES/MMA Warriors/views.py:13866>), [booking warnings](<D:/CodexFILES/MMA Warriors/views.py:3599>) and [manual validation](<D:/CodexFILES/MMA Warriors/views.py:13607>).

Combat Sports also already has [card auto-fill](<D:/CodexFILES/MMA Warriors/views.py:6558>). Reuse its interaction lessons without routing MMA pairings through a different sport's builder or assuming the two sports share eligibility rules.

Upgrade this into a card workbench with three explicit actions: suggest an opponent for a selected fighter, fill selected empty slots, and propose a complete draft. Show the proposed pairings and unresolved slots before commitment. Keep existing bookings locked unless the player explicitly includes them for replacement.

Persist per-fighter instructions such as preferred next window, development aim and permitted opposition range. Show why a pairing fits, why alternatives were excluded, the expected camp window and the purse commitment. These are Matchmaker department briefs, not a second assignment currency or an independent matchmaker formula.

For future bookings, introduce **tentative reservation versus cleared to compete**. Derive the earliest provisional date from recorded medical availability plus required preparation. Recheck on scheduling, injury change and event preparation; unresolved clearance prevents the bout. Never enable future booking by simply removing the current injury check.

**Acceptance:** preview leaves state/RNG untouched; locking a bout preserves it; duplicate names resolve by fighter ID; suggestions respect budgets, readiness, rematch cooldowns and sporting merit. The same eligibility decision must appear in manual booking, assistant explanations and execution. No staff brief can force an unqualified title challenger.

### J2 — Event preparation becomes the first playable Media/Staff project

**High priority · Extend · the first delivery slice of M1 and S1/S2.** Press interactions already generate hype, media heat and possible rivalries; weigh-ins already produce weight outcomes, fines and cancellations. They currently execute together during result preparation. See [press resolution](<D:/CodexFILES/MMA Warriors/events.py:3651>) and [event preparation](<D:/CodexFILES/MMA Warriors/events.py:3848>).

Build one event preparation board with four stages: campaign commitments, media appearance, weigh-in decisions and final readiness. Each stage shows its responsible employee, deadline, cost and status. Reuse existing media action capacity and campaign targets; do not create an additional free set of promotional attempts.

Let the player choose which booked matchup receives attention, the intended audience and an appropriate approach. Distinguish promotional interest, sporting momentum and personal rivalry in both labels and mechanics. A Marketing brief can amplify an existing sporting story without creating personal hatred; a fighter's reluctance can redirect the plan without requiring a new popup every week.

Persist completed stage outputs, then let Fight Night display a read-only pre-show recap with portrait cards and clear consequences. Moving a stochastic stage earlier is a simulation change: define when its existing draw occurs, consume it once and never reroll when the page is reopened. Cancelled/replaced bouts require an explicit campaign retarget/cancel decision.

**Acceptance:** preparation, watch and simulate paths consume the same stored stage results; a reload cannot repeat hype, fines or payouts; sponsor and broadcaster obligations use the same event ID and final delivered card. No archived future outcome is shown before its stage has resolved.

### J3 — A contract desk with budgets, exceptions and a forward view

**High priority · Extend · S2/S3 and M2.** Selected-fighter renewals and opt-in automatic core renewals already exist. See [selected renewal workflow](<D:/CodexFILES/MMA Warriors/views.py:889>) and [automatic renewal policy](<D:/CodexFILES/MMA Warriors/world.py:19312>).

Put expiring fighter, staff and commercial agreements into a common planning view, while retaining their different negotiation rules. Show current commitments, proposed changes, renewal dates, guaranteed costs and contingent amounts separately. “Renew selected” should prepare a reviewable batch, not hide many independent spending decisions behind one button.

Currently the selected-fighter action negotiates immediately and limits the results popup to 40 lines ([batch results](<D:/CodexFILES/MMA Warriors/views.py:906>)). Add a complete scrollable result ledger so every attempted renewal remains inspectable, including failures beyond the popup limit.

Extend automation with permitted contract types, per-deal caps, a monthly ceiling and a minimum reserve. Display exception cards for an unaffordable request, rejected term or missing decision. Retention assessments should explain actual activity, pay and role concerns instead of relying only on the latest result; tournament participation must remain visible when considering a fighter's recent contribution.

Rights successors continue to follow M2: future start dates, no overlapping guarantees and no reset of an outgoing delivery obligation. A pending offer reserves an estimated commitment only under a declared policy; it is not booked expenditure until accepted. Do not invent automatic salary escalators or retroactive dissatisfaction in legacy contracts.

**Acceptance:** batch preview does not sign or spend; partial failures are individually reported; manual and automated work share limits; a reload cannot renew twice. Test exact reserves, changing demands, counter withdrawal, simultaneous expiries and a poor month with no event revenue.

### J4 — Company memory and fight-history truth

**High priority · Existing records plus a new historical index.** Pre-bout records, employers and company/world divisional rankings are already captured. Company and world P4P calculations also exist; neither should be described as a missing feature. See [ranking snapshots](<D:/CodexFILES/MMA Warriors/world.py:5312>), [bout ledger fields](<D:/CodexFILES/MMA Warriors/world.py:5412>) and [P4P maps](<D:/CodexFILES/MMA Warriors/views.py:13535>).

There is a specific historical-truth issue to include in the first fix pass: when no suitable archived card is found, the [legacy profile fallback](<D:/CodexFILES/MMA Warriors/views.py:1564>) can substitute the opponent's **current** record for an absent historical record. Replace that fallback with an explicit “Not recorded” state. This is a source-confirmed path; a focused reproduction is still needed before changing it.

Add a company timeline with “As of” selection, title reigns, roster arrivals/departures, significant events and alumni profiles. Current promotion state includes roster, title and era records, but a complete dated membership ledger was not located in the [promotion schema](<D:/CodexFILES/MMA Warriors/models.py:385>). Record future join, transfer, loan, recall and departure events with stable IDs and reasons. An old fight proves an appearance, not the exact date of employment.

Keep the profile's compact fight cards, opponent portraits and pre-fight rank badges, with a full configurable ledger underneath. Separate “at the time” from “today”; label company/division/P4P scope explicitly. Persist column choices by stable column keys so later fields can be added without resetting layouts or discarding underlying data.

The existing [bout snapshot hot list](<D:/CodexFILES/MMA Warriors/world.py:5445>) is bounded. For new durable history, archive compact records before trimming working lists rather than making every refresh scan an unlimited list. Retain existing data; missing older snapshots remain unknown. Keep belt departure handling through the existing vacancy function and preserve the original reign and departure reason.

**Acceptance:** renames, transfers, retirements, identical names, expired replays and save/reload leave old records/ranks unchanged. Test multiple appearances in one week and incomplete legacy dates. Historical browsing must not generate fighters, update rankings or modify title history.

### J5 — A commission record, separate from injury state

**High value, larger rules change · New layer · extends S4.** The current testing action records positives in a message and increases `injured`; that is not a durable disciplinary history. See [drug-testing settlement](<D:/CodexFILES/MMA Warriors/views.py:12957>).

Create a case ledger with fighter ID, event/test reference, finding date, status, applied sanction, start/end dates and resolution evidence. Treat a recorded finding, an active suspension and a medical layoff as different facts. Booking should explain every active restriction; lifting one restriction must not clear another. Repeat-case consequences require explicit rules and balancing, not inference from old injuries or free-text messages.

Also introduce per-corner title eligibility. The current [MMA weigh-in path](<D:/CodexFILES/MMA Warriors/events.py:4483>) removes title flags when a bout continues after a miss. A prospective sanction record distinguishes the scheduled championship, each fighter's eligibility to win/retain it and the settlement decision. **User decision, 12 September 2026:** a champion missing weight prompts the player to decide; automatic stripping is not the approved policy. See R10 for persisted decisions, outstanding option scope and unattended simulation handling. Do not rewrite past results.

**Acceptance:** test champion-only, challenger-only and both-corner misses across either winner, draw and no-contest; divisional/interim/special belts; player/AI events; replacements and tournaments. Verify vacancy reasons, defence counts and immutable historical sanctions. Existing injuries stay injuries; no automatic old offence history is fabricated.

### J6 — Coaching careers, not another unexplained training bonus

**Medium priority · New career links over existing staff/gym systems · S3/S4.** Treat this as the Academy Coach extension already identified above, not a duplicate generic staff overhaul.

Gyms already carry a named head coach and quality/specialties ([gym schema](<D:/CodexFILES/MMA Warriors/models.py:369>)); Academy development reads a Trainer skill even though the current hiring catalogue does not offer that role ([Academy read](<D:/CodexFILES/MMA Warriors/world.py:7427>), [hireable roles](<D:/CodexFILES/MMA Warriors/constants.py:18>)). Connect these existing concepts deliberately instead of adding an unrelated second coaching model.

Begin with one explicit coaching responsibility: a named lead working with a defined fighter group and focus for a sustained period. Show existing gym quality, assigned work and the relevant coaching contribution separately. A retired fighter can become a staff candidate through a linked career transition, retaining the original fighter identity and history; combat success alone must not imply excellent coaching skill.

Link the new staff ID to the source fighter ID rather than replacing or moving the retired fighter object. Define comeback availability and prevent duplicate recruitment before this pathway is enabled.

Reuse the trait catalogue's explanatory standard for specialties: trigger, advantage, drawback and cap. Do not multiply the existing passive staff effect simply because several people share a role. Add mentor/personality narratives only when actual relationship or work evidence exists, and label flavour-only text honestly.

**Acceptance:** departure/handover, reassignment, workload ceilings and distinct-period progression; no development from opening profiles or narrative milestones; no silent rewrite of old camp effects. Any development or recovery change needs fresh applicable mechanical evidence before release.

### J7 — A company-relations desk built around existing transfers and children

**Medium priority · Extend plus new agreement records.** Fighter-for-fighter/cash transfers and child-company launch, loans, recalls and profit sharing already exist. See [transfer commitment](<D:/CodexFILES/MMA Warriors/views.py:2216>) and [child-company lifecycle](<D:/CodexFILES/MMA Warriors/world.py:2930>). A general bilateral treaty ledger was not located in this inspection.

Unify these actions as proposal cards with both companies, relevant fighter IDs, outgoing/incoming value, term, obligations and expiry. Start with existing transactions and explain their affordability and booking restrictions before adding reciprocal event or talent agreements.

Make any new relationship score evidence-based: fulfilled terms, failed commitments and unresolved disputes, with visible dates and reasons. Relations should affect a defined negotiation rule, not silently rewrite competitive rankings. Preserve subsidiary history when ownership changes; any future spin-off requires an explicit asset, cash, contract and title transition plan.

**Acceptance:** each transfer moves the same object/ID exactly once, pays once and vacates a departing champion through the sanctioned history path. Loan return, duplicate names, player takeover and save/reload must not duplicate fighters or employees. No automatic company destruction or roster purge is part of this proposal.

### J8 — A durable tournament hub

**Medium priority · Extend.** Tournament simulation, bracket viewing, champion honours and bracket storage already exist. See [completed bracket display](<D:/CodexFILES/MMA Warriors/events.py:4705>) and [event record storage](<D:/CodexFILES/MMA Warriors/events.py:5039>).

Add one searchable index by tournament, edition, division, date and participant. Each edition retains entrant IDs, substitutions, stage results and champion as compact records independent of the full replay cache. Link the tournament page to the participant's ordinary fight ledger; do not manufacture a second professional result for an existing bout.

Improve entry/seed/alternate review and expose the complete upcoming field before scheduling. Save draw decisions once. Later multi-event competitions should reuse event readiness and withdrawal handling, rather than bypass them because a fighter occupies a bracket slot.

**Acceptance:** replay expiry retains the bracket, champion and individual results; name changes remain linked; each elimination adds the correct single result; substitutions and cancelled stages retain their reasons; company transfers do not erase participation.

### J9 — Regional and divisional planning before commitment

**Medium priority · Extend; invitations are a later new layer.** Venue capacity/access and regional economic factors already exist. Division management shows roster counts and open/closed state. See [venue progression](<D:/CodexFILES/MMA Warriors/world.py:5864>), [regional factors](<D:/CodexFILES/MMA Warriors/world.py:5945>) and [division manager](<D:/CodexFILES/MMA Warriors/views.py:553>).

Add a region/calendar planner showing known competing events, local roster availability, venue access and forecast commitments. Label forecasts as estimates, not guaranteed gate income. A division feasibility panel should show currently bookable pairings, eligible challenger depth, known/scouted recruitment options and expected payroll pressure. Separate unavailable, unscouted and genuinely unsuitable candidates.

Once those calculations are reliable, prototype an optional host invitation: specific region/date, offer expiry, guarantee, agreed local participation and cancellation terms. Connect it to M2/M3 commitments and receipts. Assess the actual offer when accepted; merely visiting a region page must not create or reroll one.

**Acceptance:** thin divisions report the shortage without waiving title merit; closing/reopening does not invent a champion or move fighter weight classes; forecasts use the same finance inputs as settlement. Invitations must pass affordability and calendar conflict checks without promising hidden future AI schedules.

### J10 — Explain the game where the decision is made

**High priority for help/feedback; medium for new comparisons · Extend.** There is already a [first-week guide](<D:/CodexFILES/MMA Warriors/views.py:115>), [fighter comparison](<D:/CodexFILES/MMA Warriors/views.py:5204>) and a [paginated search](<D:/CodexFILES/MMA Warriors/views.py:5115>). The current search text includes name, company, sport, region and nationality; richer biography/alias search would be an extension, not a replacement search engine.

Build a small searchable help catalogue linked directly from decisions: rank scope, challenger merit, camp readiness, staff contribution, delivery obligations and finance terminology. Use actual calculation helpers for “Why?” explanations rather than duplicating formulas in UI prose. Follow the trait cards' concise description/effects pattern.

Replace routine success dialogs with a persistent inline confirmation and optional details; retain confirmation for destructive or substantial commitments. Give disabled actions a reason. Keep colour as an accent alongside words/icons, never the only way to distinguish a positive result, deadline or restriction.

An optional skill comparison can show placement within a clearly labelled cohort. Exact private ratings must not leak through a percentile, sort order, tooltip or cached comparison. If only scouted fighters are available, label the comparison as a known sample, not a world percentile. Fix the existing visibility leaks before expanding this feature.

**Acceptance:** keyboard navigation, readable contrast, narrow layouts and no clipped decision controls; one shared visibility policy across every profile/ranking/comparison path; search retains the 200 ms debounce, 100-row pages and access to all results. Help/refresh preserves RNG and stored assessments.

### J11 — Smarter unattended advancement with safe stopping

**Medium priority · Extend.** Spectator date targets, a safe stop request and a queued advance sequence already exist. There is also a stop predicate used when looking for an event. See [spectator controls](<D:/CodexFILES/MMA Warriors/world.py:5151>) and [advance sequence](<D:/CodexFILES/MMA Warriors/world.py:6561>). Recovery saves and fallback loading already exist in [persistence](<D:/CodexFILES/MMA Warriors/persistence.py:665>) and [load recovery](<D:/CodexFILES/MMA Warriors/persistence.py:1125>).

Expose optional pause policies for selected event types, tracked fighters/companies and actionable management deadlines. An unattended spectator preset should run to its chosen date without ordinary award or news prompts; a management preset can stop for decisions the player has not delegated. Record the stop reason and last completed boundary, then offer a clear resume action.

Preserve the current week-boundary safety model. Individual calendar tasks remain synchronous; changing progress labels does not establish responsiveness. Benchmark the longest task and test stop requests during event resolution, autosave and month-end work. Do not promise immediate mid-fight interruption.

If players want permanent milestone backups, make them explicit pinned checkpoints outside the rolling recovery slots, with disk-use visibility and verification. Do not silently disable existing retention or create unlimited annual full-save copies.

**Acceptance:** no repeated settlement after pause/resume or crash recovery; no extra RNG from stop-rule evaluation; exactly the requested target date; no surprise player decisions in spectator mode. Use a disposable long-running save, not Testing V2, for the initial regression run.

### J12 — An editor preflight and safe configuration presets

**Medium priority · Extend.** Structured universe validation already checks field values, divisions, IDs and ownership. See [shared validation](<D:/CodexFILES/MMA Warriors/universe_validation.py:52>). Rule controls and defaults also exist in [game settings](<D:/CodexFILES/MMA Warriors/views.py:11330>).

Add a read-only preflight distinguishing invalid data from playable-but-risky setup: divisions without plausible opponents, unaffordable payroll, missing title-holder references and insufficient available talent. Report specific entities and remedies. Do not “repair” a world by silently deleting fighters, auto-signing replacements or making a new champion.

Start reusable presets with already supported settings. A preset should show a before/after diff, affect an explicit scope and preserve event-agreed terms. Save an active career as a new database only through a separate conversion workflow with retained identities, documented treatment of histories and no overwrite of the live save.

**Acceptance:** validation is non-mutating; import/export round-trips retain IDs and unknown supported fields; invalid references are rejected with useful locations; preset application cannot retroactively change a completed bout. New combat rule families require their own engine design and certification, not just extra checkboxes.

### Ideas to defer or deliberately not copy

These boundaries keep the plan deliverable and protect existing careers:

- **Daily-calendar conversion:** MMA Warriors already exposes calendar labels and day-sensitive event calculations, but advances on a four-week-per-month model ([calendar implementation](<D:/CodexFILES/MMA Warriors/world.py:79>)). A real-date migration touches contract terms, cooldowns, camps, history ordering and every calendar task. Keep it a separately scoped migration, not a cosmetic date change.
- **Combat-engine changes and exotic rule formats:** perform a gap analysis against the accepted 440-move release first. New strike rates, damage modifiers, disqualification policies or exhibition settlement semantics need fresh native evidence and professional-record isolation. A competitor's feature list is not a balance target or a valid replacement certificate.
- **Manual published rankings:** potentially useful later, but store overrides with date, scope and reason separately from calculated merit. They must not bypass eligibility, change the world table silently or rewrite pre-bout snapshots. Clear explanations and correct existing scopes are higher priority.
- **Owned broadcasting networks, reality competitions and broad economic/era controls:** require their own playable prototype, cash-flow model and AI policy. First complete M1–M3 and staff lifecycle work. Additional currencies or brand meters need a demonstrated decision they improve.
- **Destructive history pruning, forced company-elimination caps or automatic roster purges:** not recommended. Preserve fighter identity and career records; use indexed archival storage and measured performance work. Recovery files and narrative hot lists are not a licence to erase the career ledger.
- **Multiplayer and broad scenario scripting:** separate architecture projects, not additions to the present UI overhaul. Establish save ownership, execution order, script validation and compatibility requirements before estimating them.

### Delivery order integrated with the existing report

The journal should strengthen the existing batches, not create a competing roadmap. Small presentation slices can ship before the larger rule changes when their data contracts are ready.

| Existing batch | Additions from this comparison | Completion evidence |
|---|---|---|
| G0 — Integrity | J4 legacy-record fallback; existing UI/scouting fixes; J10 truthful action feedback | Focused reproductions pass; no current-state substitution for absent historical facts. |
| G1 — Shared records | Stable event/work references for J1/J2/J3; compact membership/tournament indexes for J4/J8 | Additive save/reload and identity tests; neutral legacy defaults; no record loss or duplicate completion. |
| G2 — First playable loop | J1 assisted draft + J2 preparation board + J3 contract review; J10 contextual help | Player can plan a card, assign its promotion, review commitments and follow delivery without repetitive mandatory clicks. |
| G3 — Commercial lifecycle | Existing M2/M3, then J9 regional planning; trial invitations only after forecasts reconcile | Terms, campaign work and settlement receipts agree; forecasts remain explicitly uncertain. |
| G4 — Staff and AI | Existing durable employment; J6 coaching career links after passive attribution is correct | Bounded workload/progression and affordable long-run AI employment; no duplicate role bonuses. |
| G5 — Optional expansion | J5 disciplinary/title rules, J7 new agreements, expanded J8 competitions, J11 pause/checkpoint options and J12 conversion tools | Separate rule approvals and compatibility evidence for each; none required to finish the first management loop. |

**Recommended first playable package:** fix the confirmed UI/integrity issues, then deliver a card draft, one targeted event campaign, named staff responsibility, a commitment review and a stored post-event receipt. Pair that with historical-record clarity. This gives the player a complete improvement they can test before larger systems are added.

### How we will verify the eventual implementation

Reuse the existing `ui_data_regression_test.py`, `app_performance_regression_test.py`, `contracts_finance_regression_test.py`, `media_system_test.py`, `scouting_regression_test.py`, persistence/identity suites and relevant booking, narrative and release gates. Add focused cases for each J-item's acceptance conditions; existing passing tests do not validate proposed features.

Test presentation on actual windows at normal and compact sizes, across themes and with scouting restrictions. Test management with no staff, duplicate names, thin divisions, several same-period events, no revenue, cancellations and simultaneous departures. Test historical views after replay trimming, transfers, retirement and reload. Use seeded player and unattended spectator cohorts for economic and calendar changes; retain raw results and failures.

This appendix records the **original source-backed design review** and its
historical evidence boundary. It did not itself modify Testing V2 or rebuild an
EXE. The implementation ledger below is the current authority for the later
user-directed slices that were actually built and tested; the review findings
and earlier test results remain scoped to the evidence available when written.

## Additional development priorities — completing the player experience

Added 12 September 2026 following a further source/backlog comparison. **Add seven focused extensions, not seven disconnected subsystems.** The highest-value additions are project closeout, promotion-wide cash planning and a shared owned-company calendar. Relationship, recruitment and news tools should then help the player act on information the simulation already produces.

These are additional to M1–M3, S1–S4 and J1–J12. They reuse those plans' records, permission limits, identity rules and presentation components. Priority describes recommended order, not measured demand or a delivery estimate. This pass inspected code and existing design documents; it did not run the game or new regression cases.

### What the older backlog must not lead us to rebuild

The [feature backlog](<D:/CodexFILES/MMA Warriors/FEATURE_DEVELOPMENT_BACKLOG.md>) and [milestone design document](<D:/CodexFILES/MMA Warriors/docs/COMPANY_MILESTONES_AND_SUPER_EVENTS_DESIGN.md>) are useful context, but some statements lag the source:

- **Super-events already execute.** Approval, deposit payment, card validation, scheduling, event finance and outcome history are connected. A2 below completes exceptions and reconciles terms; it does not rebuild the entire execution path.
- **Combat Sports already supports future cards.** Do not confuse its owned sport divisions with the separately AI-managed MMA child promotions. A1 defines the remaining calendar/control gap precisely.
- **Ticket pricing, production, marketing, finance transactions and capital-project upkeep already exist.** A3 adds a cross-event forward view; it does not introduce those mechanics again.
- **Scouting already has named watchlist data and change alerts; fighters already have promises and Career Journeys; news already has story threads and a weekly digest.** A5–A7 expose and connect these foundations.
- **A play-level audit already accepts up to 100 years.** The remaining requirement is current, reproducible long-run evidence and better diagnostics, not simply adding a “100 years” option.

The source-backed descriptions below take precedence for this report. No other backlog/design file was edited in this update.

### A1 — One owned-company calendar, with an explicit MMA child scheduling mode

**High priority · Extend scheduling and ownership workflows · depends on J1/J7.** Player MMA events use the main event pipeline; owned Combat Sports cards already have [future scheduling and reservations](<D:/CodexFILES/MMA Warriors/world.py:13278>) and [due-event processing](<D:/CodexFILES/MMA Warriors/world.py:13345>). The [MMA child manager](<D:/CodexFILES/MMA Warriors/views.py:9448>) currently exposes AI strategy, funding and roster loans rather than that same future-card editor. Do not describe it as an already equivalent manual scheduler.

**Player experience:** a calendar with lanes for the main promotion, owned sport divisions and MMA children. Event cards show date, operating company, approval status, fighter reservations and the company that pays. Clicking a card opens its existing editor or a read-only AI view; the overview must not flatten different ownership models into one wallet or one roster.

**First implementation slice:** build a read-only index over actual scheduled records. Then add an opt-in “parent-approved card” workflow for an MMA child: choose a date, review an AI proposal or manually edit a draft, validate against the child's roster/budget, and commit through its own settlement owner. Keep ordinary AI management as the default. Suppress a conflicting automatic card when a committed manual card occupies that child's permitted period; do not increase event cadence accidentally.

Store a stable event ID, operating-company reference, source system and status. Derive the calendar view from those records instead of keeping a second mutable schedule. Revalidate loans, recalls, contract expiry and medical readiness at commitment and execution. An AI event that has not actually been scheduled is a forecast, not a confirmed booking.

**Acceptance:** no early or duplicate execution; postponement/cancellation releases only the correct reservations; parent/child finances and histories remain separate; loan recalls cannot create simultaneous bookings; renames and reload preserve links. Include due events in different sports during the same week. Do not merge sport-specific rankings, rules or professional records.

### A2 — Super-event commitments, deadlines and cancellation closeout

**High priority · Completion and integrity work · extends J2/J8/J9.** Existing [approval](<D:/CodexFILES/MMA Warriors/awards.py:255>), [scheduling](<D:/CodexFILES/MMA Warriors/events.py:214>) and [completion](<D:/CodexFILES/MMA Warriors/awards.py:277>) already form a playable route. The missing product work is making every exceptional route understandable and complete.

Three source findings should become focused reproductions in G0:

1. **Agreed terms and settlement use different keys.** [Templates](<D:/CodexFILES/MMA Warriors/awards.py:192>) store `security` and `revenue`; approval includes security in its commitment check. Settlement instead reads [`security_cost`](<D:/CodexFILES/MMA Warriors/world.py:6083>) and [`revenue_multiplier`](<D:/CodexFILES/MMA Warriors/world.py:6021>). No conversion appears in the inspected approval/scheduling route, so those template terms fall back to zero security cost and a neutral revenue multiplier there.
2. **Accepted planning projects have no equivalent deadline closeout.** [Expiry](<D:/CodexFILES/MMA Warriors/awards.py:179>) transitions Offered items but retains Planning items after the deadline; scheduling then rejects an out-of-window project. The plan needs an explicit abandon/extension/expiry resolution.
3. **Ordinary card cancellation does not close the project.** The [cancellation path](<D:/CodexFILES/MMA Warriors/events.py:519>) removes the event and clears relevant camps, but does not resolve the embedded super-event agreement, outstanding offer, money or project history.

**Player experience:** a project card with paid, refundable, non-refundable and still-due amounts; a deadline; remaining card requirements; and Proceed, Reschedule or Cancel actions. Show the consequences before confirmation. Completion should compare the agreed project budget with the full project result, including evidenced prior deposits, while retaining the ordinary event's own finance report.

**Implementation:** normalise terms once at acceptance, retain an immutable agreement snapshot and use one closeout transaction for success, failure, cancellation or expiry. Link all campaign/staff work to that project so orphan tasks are closed or deliberately handed over. Record a terminal outcome once; reopening a page must not charge, reward or clear another active project.

New refund rules and extension rights must be prospective, visible terms. Preserve evidenced legacy payments without inventing arrears, refunds, ticket presales or commitments from current template prices. Reconciling a field mismatch can alter the economy: test and document it rather than treating it as presentation-only. Add random event incidents only after these paths are reliable.

**Acceptance:** planning timeout, cancellation before/after scheduling, rescheduling inside/outside the window, lost required fighter, repeated clicks and reload at every stage. Reconcile deposit/setup/security and project totals exactly once; retain cancelled history; leave no orphan agreement or event. Legacy completed events remain unchanged.

### A3 — A promotion-wide cash runway and scenario planner

**High priority · New planning view over existing finance · builds on J3/J9.** Existing [event economics](<D:/CodexFILES/MMA Warriors/world.py:6010>) already respond to pricing, marketing and production. The [booking preview](<D:/CodexFILES/MMA Warriors/views.py:4270>) is narrower than full settlement, while [capital projects](<D:/CodexFILES/MMA Warriors/world.py:6169>) and [milestone projections](<D:/CodexFILES/MMA Warriors/world.py:6353>) already provide useful commitment/history inputs.

**Player experience:** a rolling 12-week cash calendar, matching three in-game months. Show opening cash, already-paid items, recurring bills, event commitments and explicitly conditional receipts. Highlight the lowest projected balance and why it occurs. Individually affordable shows should not hide a combined cash shortage between event dates.

Allow saved, non-mutating scenarios such as moving a show, reducing production or changing ticket price. Compare a conservative, baseline and stronger-demand assumption set; label these as assumptions, not measured probability intervals. Display break-even attendance only when it is achievable within venue capacity and the model's revenue/cost behaviour supports it.

**Implementation:** first extract reusable, pure forecast components from the actual finance rules. Do not add up the current partial booking previews and label that complete profit. Include due-date timing, payroll/upkeep, guarantees, conditional sponsor/rights payments, taxes where applicable, and relevant prior deposits. Keep each company's cash separate; only declared transfers or distributions cross ownership boundaries.

A scenario is advice, not a reservation or purchase. “Apply scenario” must show an exact change list and revalidate current events, prices, contracts and reserves through their existing commitment actions. Preserve recorded actuals and display forecast error afterwards without rewriting the original forecast.

**Acceptance:** two shows competing for cash; bills before revenue; no events; a failed sponsor condition; cancelled/postponed cards; paid deposits not counted twice; stale scenario inputs; negative/zero demand and capacity ceilings. Preview preserves state/RNG, and settled actuals reconcile to the canonical ledger. Establish forecast error from test cohorts before promising predictive accuracy.

### A4 — Durable owner objectives and a periodic strategy review

**High priority for objective truth; medium for the expanded review · Extend.** Goals already exist and persist. However, [the current refresh method](<D:/CodexFILES/MMA Warriors/views.py:11803>) assigns Complete/Failed/Active from today's values whenever the UI refreshes. An achieved cash target can revert, and a target reached after its deadline can become Complete. “Achieve once” and “maintain a threshold” are not distinct rules there.

**Player experience:** a quarterly review with a small set of explicit objectives and progress cards. Each states whether it means achieve once, maintain for a period, or improve from an agreed starting point. Show the target, evidence window, deadline, blockers and final outcome. Keep this separate from permanent milestone unlocks and day-to-day staff assignments.

**Implementation:** persist objective ID, owner/company reference, type, baseline, start, deadline, observations and resolution. Evaluate from calendar/business events; render pages observationally. Achievement objectives seal their result when met on time; maintenance objectives record the required observation cadence and evaluate the complete period. A revised objective is a versioned agreement with a reason, not a silent reset.

Start with recognition and useful planning feedback. New dismissal, owner interference or punitive financial rules need separate approval and balance work. Legacy objectives without adequate history should retain their original fields and an explicit legacy-evidence limitation; do not manufacture a past success or failure.

**Acceptance:** exact deadline boundaries, late achievement, falling cash after an achieve-once success, interrupted maintenance periods, unknown legacy metrics, company takeover and spectator mode. Repeated UI refresh must not change progress or outcomes. Test without the goals page ever being opened.

### A5 — Fighter relationship cases with evidence-based follow-up

**Medium priority · Extend Career Journeys and promises · connects J3/S1.** [Career Journeys](<D:/CodexFILES/MMA Warriors/views.py:3314>) already offers plans, progress and reviews; [contract promises](<D:/CodexFILES/MMA Warriors/world.py:14470>) already have deadlines and real trust/morale consequences. Do not introduce a second satisfaction score or replace these systems.

**Player experience:** turn a recorded concern into an actionable case: what happened, why the fighter is unhappy, what remains owed, available support and the review date. Portrait-led case cards can distinguish an opportunity promise, a career setback and a relationship warning without reducing everything to “morale low.”

**First slice:** link a case ID to the existing promise/career source and fighter ID. Let the player acknowledge it, choose an existing relevant support action, or decline to make another commitment. At review, compare the selected action with actual recorded delivery. Preserve partial fulfilment and unresolved obligations. Merely talking or acknowledging the case must not grant a repeatable morale reward.

Talent Relations can prepare the evidence and surface reminders under S1/S2. It cannot erase a failed promise, grant title merit or restart a deadline. Any later negotiated extension must have its own stated rules. Old unexplained trust changes should say that the reason was not recorded.

**Acceptance:** partial delivery, departure, retirement, transfer, duplicate names, repeated review and reload. Benefits occur only through the existing authorised action; case display is RNG-neutral; support costs are charged once. Extend promise/narrative tests rather than storing contradictory copies of the promise flags.

### A6 — Saved recruitment decision packs and usable named watchlists

**Medium priority · Extend scouting · connects J9/J10.** The current system already has [ID-safe watchlists](<D:/CodexFILES/MMA Warriors/world.py:8722>), [material-change alerts](<D:/CodexFILES/MMA Warriors/world.py:8764>) and [named-list saved data](<D:/CodexFILES/MMA Warriors/world.py:8935>). The inspected UI exposes [active-list toggles](<D:/CodexFILES/MMA Warriors/views.py:12478>); a full named-list manager was not located in those paths.

**Player experience:** save a small recruitment decision such as “replacement headliner” or “next season's prospects.” It contains a purpose, two to four candidates, player notes, known costs, dossier date/confidence and a decision state. Show why each fits and which unanswered scouting question matters next. This is a specific recruitment choice, not another division-depth score.

**First slice:** expose create/rename/switch/archive list actions, then attach purpose and decision metadata to existing candidate IDs. Link existing reports and comparisons; provide an explicit paid/assigned “update report” action rather than refreshing assessments for free. Keep player opinion separate from recorded facts. Overlapping estimates should remain inconclusive instead of producing a spurious certain winner.

No pack signs a fighter or spends money automatically. If a candidate leaves the market, keep the decision history and explain the change rather than removing the record. Deleting a list deletes only that list, not fighter data or scouting reports.

**Acceptance:** list/notes persistence, duplicate names, stale/partial dossiers, retired/unavailable candidates, overlapping lists and alert deduplication. No hidden ratings, invented asking prices or changed scouting RNG. Reuse existing search debounce, pagination and Scout assignment capacity.

### A7 — Followed-story briefings: what changed since the player last checked

**Medium priority · Extend world news · connects J4/J11.** The [story reader](<D:/CodexFILES/MMA Warriors/views.py:7553>) already supports contextual navigation. The [weekly digest](<D:/CodexFILES/MMA Warriors/narrative_presentation.py:124>) intentionally selects up to five stories from the most recent significant week. It is not a personalised catch-up across a long absence.

**Player experience:** follow selected fighters, companies or story threads and receive a grouped “since your last review” briefing. Show the new development, present stakes and an existing relevant action. A rivalry, prospect career or rival promotion's rebuild should remain one continuing thread with access to every retained original beat, not a stack of near-identical headlines.

**First slice:** persist subscriptions and last-acknowledged beat cursors. Compose the briefing lazily from recorded evidence, with unread-only, follow/unfollow and snooze controls. Acknowledgement is an explicit user action; refreshing or sorting should not mark unseen material as read. Retain the general feed and digest for users who do not customise anything.

Use J4's durable identity/index work, bounded queries and existing story links. If old source beats have expired, disclose the coverage gap instead of inventing continuity. Staff may surface a decision, but the briefing must not execute it or reveal hidden scouting data/future results.

**Acceptance:** repeated refresh produces no fabricated new beat; rename-safe subscriptions; multiple developments remain accessible beneath one summary; resumed long simulations provide correct unread boundaries; resolved stories remain readable. No additional simulation/RNG pass and no scan of the entire career on every repaint.

### Required enabler — current long-career evidence and useful diagnostics

**Release requirement, not another mandatory gameplay system.** [The existing play-level audit](<D:/CodexFILES/MMA Warriors/admin.py:693>) already creates a fresh observer world and supports up to 100 years, with annual snapshots and headline warnings. That capability is not proof that today's source has completed a satisfactory century-long test. This update did not run such a test or verify an existing century certificate.

Extend the current audit with resumable, source-bound checkpoints, structured annual reports and explicit invariant failures. Cover company/division survival, recruit availability, title vacancy duration and eligible challengers, staff affordability, overdue commitments, duplicate identities, orphan scheduled work, archive size and calendar-task timings. Aggregate headline cash/population figures alone can conceal a dead division or permanently unresolved project.

Use several seeds and promotion sizes; include both unattended spectator worlds and defined player-management policies. Keep fixture/source hashes, timing definitions, complete failures and all output. Stop safely on an invariant failure and retain diagnostic state in a disposable audit location; do not silently fix the world or tune only the failing seed. Default paths should retain prior state/RNG behaviour where no gameplay change is intended.

A small optional observer health view may consume these recorded metrics, but raw audit-only ability or economic data must not leak into a scouting-restricted player view. No automatic world reset, forced signings, trait changes or retirement purges are authorised as balancing shortcuts. Test Testing V2 only through a separately authorised copy-based validation, never by modifying the user's original save during an audit.

### Integrated priority and scope control

These additions should be absorbed into the existing delivery batches. The table gives their smallest independently useful result; larger mechanics remain behind their own validation.

| Addition | Place in the existing roadmap | Smallest useful delivery |
|---|---|---|
| A2 — Project closeout | G0 reproductions/term integrity, then G1 state and G3 lifecycle | An accepted project can finish, expire or cancel with one reconciled record and no orphan obligation. |
| A4 — Owner objectives | G0 refresh-purity regression, G1 saved outcomes, later G2 review UI | Correct deadline/type semantics without new punishments. |
| A1 — Owned-company calendar | G1 shared event references, G2 read-only overview, G5 opted-in MMA child control | All actual owned schedules visible without changing AI autonomy or sport rules. |
| A3 — Cash runway | G1 shared pure forecasts, G3 forward planning | Three in-game months of commitments with labelled assumptions and the lowest projected balance. |
| A5 — Relationship cases | G2 existing actions/evidence; S1 Talent Relations integration | One concern and review linked to an existing promise or career plan. |
| A6 — Recruitment packs | G2 scouting workflow, after visibility/identity safeguards | Named list management, purpose/notes and dated comparison evidence. |
| A7 — Followed stories | G1 identity/index dependency, G2 reader extension | A saved, factual catch-up on followed threads without a new simulation pass. |
| Long-career qualification | Baseline before gameplay changes; repeat through G3–G5 and before packaging | Reproducible raw evidence across seeds and a clear failure/stop record. |

**Keep the first playable release bounded:** add A2's closeout integrity, A4's truthful goal outcomes and A1's read-only schedule overview to the earlier recommended booking/campaign/staff package. Deliver A3 after its forecasts reconcile. Relationship cases, recruitment packs and personalised news can follow as smaller interface releases. Do not hold all existing UI fixes until every additional feature is built.

Use one shared visual vocabulary: summary cards with portraits or company identity, status/deadline badges, a clear next action, and an expandable evidence/ledger area. Preserve full records, configurable columns and the compact-window reading space. Do not add another generic staff organisation system, extra morale/hype currencies, decorative meters or a new modal dialog for every stage.

**Verification for this report update:** targeted source inspection and document/link checks only. The new findings are not runtime-tested fixes; all acceptance criteria describe future work. No source code, user saves, EXEs or other design/backlog documents were changed.

## Implementation handoff for Luna — detailed task specifications

**Status: active implementation handoff.** This section turns every earlier repair, page recommendation and feature into a bounded task. The implementation ledger below records which slices have now shipped; all unmarked cards remain work to do. It supplements the original evidence rather than replacing it. Refer to the original numbered finding/J/M/S/A section for its source links; function names and ownership are more durable than line numbers, which may move during implementation.

### How to commission the work

Give Luna one task ID, or one explicitly listed dependency bundle, per implementation request. Do not ask it to implement this entire report in one pass. Each task must finish with evidence, remaining risks and the exact next dependency, not an unqualified claim that the whole roadmap is complete.

Copyable future task prompt:

> Implement only task **[ID.slice]** from `D:/CodexFILES/MMA Warriors/analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md`, following its Revision 2 design decision and execution-queue row as well as the detailed card/shared contracts. Read current AGENTS.md and inspect the source before editing. Reproduce the defect or confirm the foundation first. Preserve unrelated work, all saves, identities, historical records and the current EXEs. Do not build/launch packaged EXEs, run long simulations, start agents or enable deferred features unless separately authorised. Implement the specified slice and chosen design defaults; add its acceptance cases, run applicable isolated tests, and report exact completion evidence. A release/calibration gate is not permission to invent a different design or waive a failing test. Do not automatically proceed beyond the commissioned slice.

For a documentation-only request, substitute “expand/review the specification” for “implement” and do not run the implementation checks. The current thread is an implementation run, so each completed slice must update the ledger and its focused verification evidence.

#### Completion contract applying to every implementation card

1. **Establish the baseline:** read the actual handler, calculation, persistence owner and tests. Confirm whether the issue is still present; do not reintroduce behaviour that a later change already fixed. Record existing dirty files and do not revert them.
2. **Stay in scope:** edit only the feature's domain owner, necessary UI adapter, save adapter and tests. No opportunistic engine, portrait, trait, ranking or economy refactor. New module names below are suggestions, not files claimed to exist.
3. **Keep readers observational:** refresh, sort, resize, preview, archive playback and report export do not spend, reset allowances, draw RNG, change eligibility or advance work. Existing `ensure_*` helpers may mutate; separate load/commit normalisation from pure reads.
4. **Commit through one owner:** revalidate an action against current state immediately before applying it. Return either a complete committed result or an explicit failure. Preserve the existing operation's RNG behaviour on its unchanged path; new rollback/transaction guarantees must be tested rather than assumed.
5. **Protect identity and history:** resolve fighters/staff/events by persistent IDs. Keep display-name snapshots for historical readability. Never match an ambiguous old name to an arbitrary current entity; show unavailable/ambiguous evidence. Do not replace a historical rank or record with today's value.
6. **Preserve saves:** additive, versioned defaults; no new overdue tasks, penalties or invented past facts on load. Preserve unknown supported fields, object aliases and shared identities. Migrations run in the staged load/explicit conversion path, never on every repaint.
7. **Prove the change:** add a failing regression first for a repair; for a feature, test the baseline and new path separately. Record assertions, command, exit status and any skipped UI/native checks. Old results in this report are not evidence for a new patch.
8. **Handoff:** list exact task IDs completed, files changed, migration behaviour, gameplay changes, test results and unresolved decisions. A visual task includes before/after evidence from a disposable source session when separately authorised. No EXE rebuild without an explicit rebuild request.

#### Working-state and money contracts for new features

Use these proposed interfaces across M/S/J/A work; settle names in the foundation task before independent feature implementation. They are not permission to rewrite all existing saves.

| Record | Minimum proposed fields | Ownership and rules |
|---|---|---|
| Entity reference | entity type, persistent ID, display-name snapshot; legacy resolution status | Reuse existing fighter/staff/sport-event IDs. For entities without IDs, add a saved deterministic counter/namespace at creation or staged migration. Do not use Python object IDs, current names or new random draws as durable identity. |
| Work item | ID, schema version, owning company, source feature, target references, responsible staff ID, created/due calendar values, state, revision, terms snapshot, evidence references | A lightweight common envelope, not one universal mechanic. Domain systems still own their calculations and allowed transitions. |
| Quote | action/target IDs, relevant state revision, itemised costs, affordability/eligibility reasons, capacity use, expiry conditions | Generated without mutation. A stale quote fails or returns a new reviewable quote; it must not silently charge revised terms. |
| Commitment | accepted quote/terms, funding company, payment schedule, reserved versus paid amounts, approval reference | A reservation is not a ledger debit. Define precisely which existing bill/contract owner will pay; do not invent a second payment scheduler. |
| Outcome receipt | source/work/event IDs, accepted terms revision, actual payments/effects, evidence and reasons, completion date, unique settlement key | Store at the existing settlement boundary. Repeated execution returns the existing outcome. Ledger entry, status and receipt must be saved consistently. |
| Display preferences | page ID, schema version, stable column/filter keys, sorting, collapsed sections | Unknown keys survive where possible; new columns get defaults. Hiding a column or archiving a view never deletes business/history data. |
| Historical index | entity/event IDs, date precision, compact immutable facts, archive locator, coverage status | Bounded working cache over retained facts. Missing archived detail remains unavailable; it is never reconstructed from current state. |

Default work states: Draft → Ready for review → Committed → In progress → Completed. Needs attention, Cancelled and Expired require explicit domain transitions. Closing a window is not cancellation; deleting a draft cannot cancel a signed agreement. Completed receipts are immutable; a subsequent correction is a linked adjustment, not an overwrite.

Calendar values use the existing month/week/day representation. Record whether a date is known to day, week or month; do not imply daily precision for old weekly records. Currency is integer dollars unless an existing contract explicitly uses another representation. Store percentage units unambiguously; do not mix `0.25` and `25` in the same field.

#### Shared UI acceptance specification

- Use managed windows, existing Tk/ttk structure and the established profile/Academy visual direction. Introduce reusable theme-aware cards and tables rather than a new UI toolkit or web shell.
- A page has one primary action, a short summary, its main working area, and optional details. Full information remains accessible; no limit silently drops records. Keep separate action colours and semantic result colours.
- Proposed test sizes: 1366×900 normal, 1200×880 profile/history, and the established 820×540 live Fight Night minimum. Check 100% and 125% display scaling where the test environment supports them; report unsupported checks honestly.
- Proposed readability gates: normal text/status foreground-background contrast at least 4.5:1; status also has a text/icon cue. Rows and buttons must fit their font, including scaled text. No essential button beyond an unreachable edge.
- Preserve selected entity, valid sort/filter and scroll position on routine refresh. If a selection disappears, explain why and choose a deliberate fallback rather than opening another person's details.
- Keyboard focus order follows visual order. Enter activates the intended review/action; Escape closes a transient detail without committing. Wheel events affect the hovered scroll region only, with bindings removed when the window closes.
- Empty, loading, stale, unaffordable, blocked, legacy-incomplete and error states must be designed, not left as blank panels. A disabled action explains the reason.
- These are acceptance targets for future implementation, not claims that the current app meets them. If the actual minimum geometry cannot meet a target, report the measured conflict before weakening it.

#### Test execution contract and named groups

The inspected [isolated runner](<D:/CodexFILES/MMA Warriors/run_regression_suite.py>) accepts **positional suite filenames**, not a `--tests` flag. It recognises registered suite names, runs them in fresh runtime-data directories and stops at the first failure. Use the project's configured Python interpreter; verify its environment before the future test run. Example, not executed in this report update:

```powershell
python .\run_regression_suite.py ui_data_regression_test.py persistence_regression_test.py
```

New suites must be registered in the runner before passing their filenames. A failed runner removes its temporary runtime on exit; any important failure evidence must be captured deliberately into a task-specific diagnostic location, with no user save copied or modified without authority. Never change the runner to conceal failing tests.

| Group | Registered suites to use as applicable |
|---|---|
| T-UI | `ui_data_regression_test.py`, `app_performance_regression_test.py`, `window_lifecycle_regression_test.py`, `smoke_test.py` |
| T-Profile | `fighter_profile_regression_test.py`, `fighter_traits_regression_test.py`, `scouting_regression_test.py` |
| T-FightNight | `fight_night_presentation_test.py`, `fight_night_archive_regression_test.py`, `fight_night_layout_regression_test.py`, `fight_night_experience_regression_test.py`, `fight_audio_regression_test.py`, `window_lifecycle_regression_test.py`, `smoke_test.py`, `stability_test.py` |
| T-Finance | `contracts_finance_regression_test.py`, `finance_audit_regression_test.py`, `player_finance_progression_regression_test.py`, `event_economics_regression_test.py`, `media_system_test.py` |
| T-Identity | `persistence_regression_test.py`, `identity_persistence_regression_test.py`, `ui_data_regression_test.py` |
| T-World | `ai_card_logic_regression_test.py`, `child_promotion_interactions_test.py`, `child_promotion_long_run_test.py`, `custom_promotion_division_integrity_test.py`, `combat_sports_regression_test.py`, `stability_test.py` |
| T-Narrative | `narrative_system_regression_test.py`, `narrative_long_run_storage_regression_test.py`, `narrative_performance_regression_test.py`, `advance_notifications_regression_test.py` |
| T-Editor | `universe_validation_regression_test.py`, `database_editor_save_as_test.py`, `database_editor_ui_audit.py`, plus T-Identity |

Run focused groups first, then the relevant combined regression set. Before separately authorised packaging, run the canonical complete shipping runner and current AGENTS.md native-release requirements. Changes affecting combat/development need fresh source-bound evidence; a passing UI group or an old release certificate does not qualify them. Long simulations, calibration runs and packaging should be separately scoped rather than hidden inside a small page task.

### Foundation task F0 — shared contracts before gameplay expansion

**Dependencies:** none for design; preserve all existing behaviour. **Owners:** `models.py`, `persistence.py`, the existing domain owners in `world.py`/`media.py`/`events.py`; a small proposed pure work-record helper module is acceptable if it prevents duplication.

**Implement in order:** (1) inventory existing IDs, terms, receipt/ledger references and aliases; (2) define versioned envelopes above using existing fields wherever possible; (3) implement pure validation/reference resolution; (4) add staged additive defaults; (5) provide quote/commit/result interfaces without enabling any new automatic action; (6) exercise reload and failure paths with a single disposable work item before wiring a department.

**Do not:** convert the entire world into a new generic entity framework, introduce a second RNG stream as a shortcut, add global caches of mutable fighters, replace the finance ledger, or migrate old text into asserted historical events.

**Tests/done:** T-Identity plus targeted default/no-op state and terminal RNG equality, duplicate names, missing targets, unknown fields, repeated migration, failed commitment and receipt reload. Publish the field/state contract in this report's implementation record. Subsequent tasks must consume the same contract or explicitly version an approved extension.

### Repair task cards U01–U16 — one card for every original finding

#### U01 — Protect the Matchmaking fighter workspace

**Goal/owners:** repair finding 1 in `ui.py::configure_booking_panel_layout` and the Matchmaking construction; `views.py` only for state restoration. No booking logic changes.

**Steps:** reproduce the real stacked layout with Show Details open; measure actual pane/control/table heights; remove contradictory minimum allocations; give the central fighter table a protected area. At narrow widths, make draft/details collapsible rather than squeezing all three regions into the same vertical strip. Recalculate on debounced resize without repeatedly overriding a user's viable sash position.

**UI/data:** retain current booked order, selected pair, filters and status. A compact show summary remains visible with Schedule and its readiness reason. Save only an optional layout preference, not geometry derived from another monitor.

**Tests/done:** actual 1366×900 and narrower source windows show controls plus at least four full fighter rows, with six the target where space allows; all extra rows remain scrollable. Exercise details toggles, long names and resize. T-UI. Remove test workarounds that force horizontal mode only after a regression demonstrates the real mode works; do not relax the fixture to hide clipping.

#### U02 — Restore timestamped paragraph separation

**Goal/owners:** finding 2, `fight_night_presentation.py`; preserve recorded text exactly.

**Steps:** make the clock tag own only timestamp font/foreground; remove its background, margin and spacing overrides. Apply event colour, left accent/indent and above/below spacing to the complete paragraph including the timestamp and wrapped continuations. Define deterministic tag priority so emphasis survives selection and theme changes.

**UI/data:** ordinary action stays quiet; impacts, damage and finishes gain distinct semantic accents. No line insertion/removal, narrative rewriting or simulation metadata change is required.

**Tests/done:** compare real Text-widget bounding boxes for stamped/unstamped normal, impact, damage and finish paragraphs; assert wrapping, background continuity and extra key-moment separation. Verify transcript bytes before/after styling and selection-copy completeness. T-FightNight; check Light Office and dark themes. Configuration-only tag tests do not satisfy this task.

#### U03 — Classify actual moments, not technique mentions

**Goal/owners:** finding 3, presentation classifier and tests. Do not change engine wording to fit the classifier.

**Steps:** collect current authored examples for landed impacts, knockdowns, resolved damage, stoppages, taps/unconsciousness, attempts, blocks and negated injury. Prefer matching already-presented structured evidence with the correct line/exchange; otherwise use narrow ordered rules, finish before damage before impact. Ambiguous lines remain ordinary action. A submission being attempted is not a finish.

**Data/UI:** optional presentation metadata must be tied to the displayed exchange only. Never consult later round analysis to colour earlier playback. Preserve full commentary and canonical move/outcome facts.

**Tests/done:** fixtures include all five wording examples in finding 3, incidental elbow mentions, recovered/avoided hurt and multiline wraps. Assert both correct positives and deliberate negatives; compare full text and RNG. T-FightNight. Any required change outside presentation routing is a separate reviewed task, not an incidental resolver patch.

#### U04 — Close every Rankings scouting leak

**Goal/owners:** finding 4; `views.py::refresh_rankings`, selected-row detail and shared scouting display helpers.

**Steps:** enumerate every ability-bearing cell, header card, tooltip and detail; route each through the same visibility/estimate policy used by profiles. Public record/ranking position stays public. Disable or clearly restrict ability sorting when it would reveal hidden values; do not expose an exact sort key through an otherwise hidden column.

**Data:** separate raw domain ranking facts from the redacted display row. Do not redact the saved fighter or recompute competitive rankings using displayed estimates. Cached rows must be keyed by the relevant visibility/assessment revision and invalidated on scouting-mode change.

**Tests/done:** owned, unscouted rival, partly scouted, complete/stale report and spectator fixtures in both ranking modes; selection, sort, tooltip and refresh all agree. T-UI, T-Profile, T-Identity. The existing OVR-77 leak fixture becomes a negative assertion for every exposed surface.

#### U05 — Enforce sponsor capacity without losing agreements

**Goal/owners:** finding 5; sponsor assessment/acceptance in `media.py`, portfolio actions in `views.py`/`ui.py`.

**Chosen first slice:** retain the eight-deal limit and block a ninth new signing before payment or RNG. Explain “8 of 8 slots used” with a link to review active agreements. Do not implement automatic replacement; an explicit termination workflow can be separately commissioned.

**Steps/data:** validate capacity and category conflict again at commit; remove acceptance truncation of live deals. Preserve already-over-cap legacy portfolios and all their terms, but prevent further additions until below capacity. A failed signing leaves the offer and every active agreement unchanged unless an existing rule explicitly consumes it.

**Tests/done:** 7→8 succeeds; 8→9 and stale-preview 7→8→9 fail safely; duplicate category, expired deal cleanup and legacy 9+ records preserve identities. Compare cash/RNG/contracts on failure and reload. T-Finance/T-Identity. Never recover missing old sponsors by inventing them from headlines.

#### U06 — One campaign quote for preview and submission

**Goal/owners:** finding 6 and media finding 2; `media.py::media_action_preview`, action resolver and selection bindings in `ui.py`/`views.py`.

**Steps:** extract a pure quote using action, strategy, spokesperson, target, current limits and staff quality. Recompute on every relevant input change, including target validity after a spokesperson change. Submit the selected IDs and quote revision; reject stale terms or present the revised quote before any spending.

**Risk display:** initially show truthful qualitative outcome guidance if exact probability is not implemented. Do not label the unused risk parameter as actual backfire probability. An exact probability display must enumerate the real bounded roll and all outcome thresholds without sampling or consuming RNG.

**Tests/done:** popularity-40→90 Press Tour shows and charges the same amount; stale target, cooldown, insufficient AP/cash, strategy/staff change and repeat click are covered. Preview is pure, cancellation free, allowed action charged once. T-Finance/T-UI; no new campaign balance formula in this repair.

#### U07 — Theme-aware semantic components

**Goal/owners:** finding 7; theme application/traversal in `ui.py`, custom cards/canvases and semantic Treeview/Text tags across affected pages.

**Steps:** define a small semantic token map per theme for success, warning, danger, neutral and selected states. Give custom component owners a retheme callback; refresh colours without destroying widgets or selection. Reconfigure canvas items and Text/Treeview tags, not just ttk styles. Remove stale callbacks when windows close.

**UI/data:** use consistent colours for meaning, not arbitrary ability thresholds. Keep text/icons and contrast targets from the shared UI contract. No theme setting can affect simulation or visibility policy.

**Tests/done:** open Dashboard/Profile/History/Sponsors/Scouting, switch theme while open, compare with freshly opened equivalents; exercise hover, disabled, selected and urgent states. Verify widget counts do not grow and callbacks do not target destroyed windows. T-UI/T-Profile. Include colour-pair assertions and actual rendered checks, not only palette existence.

#### U08 — Canonical ranking scope and movement

**Goal/owners:** finding 8; profile badge, ranking row builders, detail panel and rank maps in `views.py`.

**Steps:** represent the four scopes explicitly: company division, world division, company P4P, world P4P. Build each visible row with scope/current rank/previous rank/date or unavailable reason; detail consumes that selected row. Only show movement when a previous snapshot exists for the same scope and cohort. Rename the profile's division badge instead of calling it P4P.

**Data:** do not create historical P4P movement from divisional history. Treat champion status separately where the scope does not rank champions as `C`. Count rendered rows when saying “shown,” and total matches separately.

**Tests/done:** two-division fixture from finding 8; P4P and division ranks deliberately differ; pagination/truncation counts, champion/interim and missing prior scope are correct. T-UI/T-Profile/T-Identity. No ranking-score or challenger-policy change.

#### U09 — Reconcile monthly-burn scope

**Goal/owners:** finding 9; `views.py::refresh_finance` and the actual overhead/event-cost helpers in `world.py`.

**Steps:** inventory each current monthly charge and its payer; extract a pure overhead projection using the same inputs, units and cadence. Present recurring committed overhead separately from scheduled-event liabilities and contingent medical estimates. Do not count rivals, free agents or retirees merely because they are injured.

**Data/UI:** retain actual ledger entries unchanged. Forecasts carry an as-of date and explicit exclusions until all settlement components are covered. A3's future planning must consume this corrected helper; do not make a second rival-inclusive estimate for a card.

**Tests/done:** add unrelated injured world fighters and assert player recurring burn is unchanged; verify player staff/upkeep and scheduled-event costs in the correct period. Zero events, injury recovery and ownership changes remain consistent. T-Finance/T-UI. Reconcile forecast definitions, not an assumed $1,400 replacement formula.

#### U10 — Truthful staff offer strength

**Goal/owners:** finding 10; staff negotiation preview/submission in `views.py`, score helper in `world.py`.

**Chosen first slice:** rename the existing output to “Offer strength” and explain it is a score, not a percentage. Keep the actual negotiation formula and random roll unchanged. Show affordability and any independent hard blocker separately.

**Steps:** find all labels/tooltips/results using the misleading percent; use the same score inputs as submit; refresh on salary, term, target and relevant staff state. Do not claim guaranteed success from strength if another acceptance condition can fail.

**Tests/done:** fixtures at the existing 54/62/70 score boundaries show scores without `%`; a preview performs no draw; injected low/high negotiation rolls still yield the historical decisions. Changing a label does not change money or RNG. T-Finance/T-UI. A later exact-probability enhancement must account for every hard gate, not just the final roll.

#### U11 — Separate refresh from paid market review

**Goal/owners:** finding 11; Media Rights button in `ui.py` and `media.py::media_refresh_offers`.

**Steps:** make ordinary page refresh a pure rerender of existing offers. Rename the paid action to “Review market — $3,500” using the actual current price source, not duplicated UI arithmetic. Present the replacement consequence, then commit only after explicit confirmation and fresh affordability validation.

**Data/UI:** cancelled review leaves cash/offers/RNG unchanged. Preserve the current market-review rules and fee unless separately changed. Keep negotiation history accessible when replacing available offers; do not terminate a signed agreement as part of a market search.

**Tests/done:** free refresh repeated, cancelled paid review, insufficient cash, successful review and stale confirmation all covered; one debit/one intended offer generation only. T-Finance/T-UI/T-Identity. The free refresh must not call an offer-generation helper indirectly.

#### U12 — Honest sponsor valuation and activation display

**Goal/owners:** finding 12; sponsor assessment/payment in `media.py`, Finance summary in `views.py`.

**Steps:** show contracted maximum per eligible event, current activation-adjusted estimate and remaining term separately. Remove fee×months as an unqualified annual valuation. If a horizon estimate is useful, require/display the assumed eligible event count and activation assumptions and label it as a scenario.

**Data/UI:** calculate the current event estimate through the existing activation helper, with reasons for half payment. Future duty fulfilment is unknown, not automatically full. Do not pre-settle duties or modify current campaign evidence while assessing them.

**Tests/done:** automatic placement, low trust/stability, qualifying/nonqualifying ranked campaign, no event and multiple events; max and estimated payments reconcile to the existing settlement path. T-Finance/T-UI. This repair adds no missed-month penalty or automatic sponsor action.

#### U13 — Consistent contract filtering across sports

**Goal/owners:** finding 13; Contracts UI and MMA/Combat Sports row refresh in `views.py`.

**Steps:** define a shared predicate for the existing Show options using each row's real remaining term/status. Apply it before insertion on both tabs. If a status has no sport equivalent, explain it rather than silently showing all rows. Preserve selected sport and a still-visible contract ID.

**Data/UI:** filter view models only; do not tick contract months during refresh. Show filtered count/total count and a clear empty state. Keep release and renewal actions attached to the selected current contract, not a stale row index.

**Tests/done:** final-month, longer-term and expired fixtures across MMA and each owned sport; switch filters/tabs, mutate a contract and refresh, test duplicate names and empty lists. T-UI/T-Identity plus `combat_sports_regression_test.py`. A common filter label must have one documented meaning.

#### U14 — Display live injury tendency without changing stored baselines

**Goal/owners:** finding 14; profile Contract & Business rendering, `fighter_traits.py::effective_injury_tendency`.

**Steps:** replace the raw risk display with the existing effective calculation where visible; details explain base value, trait-relative effect and current effective tendency. Clearly distinguish that attribute from an actual calibrated injury probability. Respect the profile's scouting policy.

**Data:** no rewrite of `injury_proneness`, toughness, detailed ratings or saved injury baseline. An evolved trait changes the view through the live helper; unknown historical baseline is handled by that helper's existing compatibility rules.

**Tests/done:** pre/post trait evolution, None legacy baseline, base mutation, visible/hidden rival and save/reload. Compare profile output with the helper, assert stored fields unchanged and no draw. T-Profile/T-Identity. Do not use this display task to retune injuries.

#### U15 — Preserve compact Fight Night reading height

**Goal/owners:** finding 15; `fight_night_layout.py` plus actual EventMixin window integration in `events.py`.

**Chosen layout:** in compact mode, move full settings into a managed transient panel/window; retain only playback essentials in the broadcast shell. Settings must not reduce the live reader to the measured 82px height. Preserve 136px normal/104px compact portraits.

**Steps/UI:** measure available client area after actual controls/fonts; set a protected reader minimum, with a proposed acceptance floor of 160px at 820×540 and at least six complete commentary lines. Resize panes gracefully, retain scroll/playback position, and restore focus on closing settings.

**Tests/done:** actual live window, not the abbreviated layout harness; settings open/closed, resizing across breakpoint, long fighter names, audio controls and repeated close/reopen. T-FightNight. If the minimum cannot be met with current font scaling, report measured geometry and propose a reviewed compact control layout rather than shrinking portraits or deleting transcript content.

#### U16 — Local wheel support for Fight Night side panels

**Goal/owners:** finding 16; scroller construction in `fight_night_layout.py` and existing wheel-routing utility.

**Steps:** bind wheel input to the panel viewport and its child content while hovered; normalise direction/step consistently with the app. Keep the reader and other scrollers independent. Dispose bindings when panels/windows are destroyed; avoid an unrestricted global bind that captures all app scrolling.

**Data/UI:** preserve scrollbar operation, keyboard navigation and text selection. At a scroll limit, use the established app policy rather than accidentally scrolling a different reader.

**Tests/done:** long Round Read/Bout Desk content moves on wheel; cursor over main commentary moves only that reader; short content and destroyed/reopened panels cause no error or duplicate scroll. T-FightNight/T-UI. Confirm both actual wheel behaviour and unchanged transcript/telemetry.

### Page implementation cards V01–V19

Every page card inherits the complete shared UI contract, T-UI and any listed domain tests. These are presentation slices: they must not enable the later gameplay features merely because space has been reserved for them. Where a feature is not implemented, omit its action or explicitly mark it unavailable; never display fabricated progress.

#### V01 — Dashboard / Promoter Dashboard

**Owners/dependencies:** Dashboard builders in `ui.py`, assistant refresh in `views.py`; U07. **Build:** one primary next-action card based on existing due work; grouped medical/contract/finance risks; a small recorded-change area; selectable full advice below. Remove duplicated Booking calls to action, not access to booking. Rank urgency by actual due/blocked status, not a new gameplay score. **State:** preserve a selected notice by its source reference; dismissal changes only the existing notice state. **Verify:** no risks, multiple simultaneous risks, spectator mode, stale/departed targets, and long advice; all original advice remains reachable. Done when the user can identify the next action without opening every panel and every card opens the right current context. Add T-Narrative.

#### V02 — Game & Saves

**Owners/dependencies:** save-page construction in `ui.py`, existing actions in `persistence.py`; U07. **Build:** an empty-library start/load/import explanation, compact current-save summary, and clearly separated career controls versus database administration. Put spectator mode and its date target in a dedicated section without hiding save recovery. **State:** preserve selected slot/folder and use existing save/restore/delete confirmation handlers; do not introduce destructive convenience actions. **Verify:** empty library, many slots, duplicate display names in different folders, unavailable file, corrupt-save recovery and narrow width. All actions retain their original targets and backup behaviour. Add T-Identity; restoration tests operate on disposable data only.

#### V03 — Matchmaking visual organisation

**Owners/dependencies:** `ui.py` Matchmaking and `views.py` booking refresh; U01/U07/U08. **Build:** compact show/economics summary, protected fighter workspace, persistent selected-pair summary and a collapsible draft/detail area. Keep Schedule visibly disabled with a reason when readiness fails. **State:** filters, sort, chosen fighters and card order survive preview/resize; no silent rebooking. **Verify:** long cards, empty roster, no eligible pair, short-notice/TBA and title/interim indicators; row selection and action target agree. J1 adds future workbench behaviour separately. Add `ai_card_logic_regression_test.py` only if recommendation routing changes; presentation alone must not alter candidate order or draws.

#### V04 — Profile identity, overview and Core Skills

**Owners/dependencies:** profile construction in `views.py`, `fighter_profile_overview.py`, existing skill presenters; U07/U08/U14. **Build:** compact persistent identity header and tighter sections, removing repeated headings and oversized empty bands. Align skill labels/bars/current values; retain speciality and detailed drilldowns. Use one explained skill scale, not warning red for ordinary ability. **State:** selected fighter/tab and scouting scope remain stable. Career pulse keeps fatigue inverted as readiness, momentum centred on 50 and skills ordered by current value. **Verify:** rookie/veteran, no history, hidden/stale scouting, long names and resize. Do not expose a hidden value through bar width. Add T-Profile/T-Identity; preserve trait cards and portrait identity.

#### V05 — Fight History layout and column controls

**Owners/dependencies:** history/profile renderer in `views.py`; U07/U08 and J4 for historical facts. **Build:** a useful ledger first, compact selected-bout summary second; use a collapsible or side-positioned portrait/ranking comparison rather than two large permanent panels. At 1200×880 target at least eight complete ledger rows with details collapsed, and keep the selected bout's details one action away. **State:** column visibility/order/width, filter and selection use stable keys; mandatory context columns can be pinned while all stored fields remain accessible. **Verify:** no history, hundreds of bouts, missing replay, long method text, duplicate names and new columns after migration. Add T-Profile/T-Identity. No deletion/truncation as a layout solution.

#### V06 — Development tab

**Owners/dependencies:** existing development presenters in `views.py` and profile helper modules; U07/U14. **Build:** an explained current outlook, compact recent changes, signed driver bars and a clearly labelled link to the existing relevant camp/career action. Explain “Monthly score” using its real source and unit; do not call it a guaranteed future skill gain. **State:** plots use stored change order, not a fabricated elapsed-time axis; all signed drivers share one absolute scale and the full ledger remains accessible. **Verify:** zero/equal/mixed-sign drivers, missing months, decline and hidden ratings. Actions use the selected fighter and existing gates. Add T-Profile; no development formula or trait progression change.

#### V07 — Finance and Sponsors

**Owners/dependencies:** Finance/Sponsor builders and refresh in `ui.py`/`views.py`, `media.py`; U05/U09/U12/U07. **Build:** separate cash, recurring commitments and estimated event receipts; a taller full sponsor portfolio; selected-deal card with term, fee basis, capacity and activation checklist. Label actual, committed, maximum and forecast amounts distinctly. **State:** selected contract by ID, no automatic pitch/offer refresh. **Verify:** over-cap legacy portfolio, zero/negative cash, half-fee duty and expired offer; amount and status match domain helpers. Add T-Finance/T-Identity. M3 later adds receipts and duties; A3 later adds runway, without duplicating these baseline cards.

#### V08 — Media Desk and Rights

**Owners/dependencies:** Media builders, preview adapters, `media.py`; U06/U07/U11 and M2 integrity. **Build:** inputs beside one live quote, explicit Available/Blocked/Countered/Withdrawn/Signed states, and a selected agreement's term/delivery summary. Keep paid review visually separate from free refresh. **State:** invalid targets clear with an explanation; changing spokesperson refreshes all dependent inputs. **Verify:** long outlet terms, no candidates, stale quote, used counter and insufficient capacity/cash. A user can tell what will happen and what it costs before acting. Add T-Finance/T-Identity. Do not implement concurrent contracts or new campaign effects in this visual card.

#### V09 — Staff

**Owners/dependencies:** Staff builders/refresh, `world.py` staff helpers; U07/U10/S1 lead correction. **Build:** department summaries for actual effective lead, supporting employees, vacancy and expiry; sizeable roster/market tables; selected candidate compared with the current lead. State explicitly when an extra hire does not increase a passive bonus. **State:** candidate/employment identity survives refresh; hiring/renewal/release remain separate actions with actual costs. **Verify:** raw-skill/effective-quality disagreement, multiple same-role hires, busy Scout, empty market and expiring employee. Add T-Finance/T-Identity and scouting regressions. Do not display narrative tenure as XP or specialty text as a mechanical buff.

#### V10 — Contracts

**Owners/dependencies:** Contract pages in `ui.py`/`views.py`; U07/U13. **Build:** locally scrollable ledger, selected-contract summary, clear status chips and visually separate review/renew/release actions. Move legends into concise contextual help. **State:** preserve sport and selected contract; after an action update the same row or explain its departure. **Verify:** multiple selections, expired/final-month filters, long terms, narrow widths and vanished candidates. Add T-Finance/T-Identity and sport coverage. J3 handles future batch review; do not silently convert immediate renewals into a different negotiation policy while restyling the page.

#### V11 — Scouting / Fighter Search / Free Agents

**Owners/dependencies:** discovery builders/refresh in `ui.py`/`views.py`, existing scouting helpers; U04/U07 and V19. **Build:** consistent filter order, reset action, matching/visible counts, selected-entity card and report freshness. Preserve each page's different market/visibility semantics rather than forcing all into one query. **State:** Search retains 200 ms debounce and 100-row pages; other lists retain access to all matches. **Verify:** filters yielding zero results, a fighter changing employer mid-refresh, hidden attributes, stale dossier and pagination selection. Add T-Profile/T-Identity. A6 exposes named packs later; no free re-scouting from a refresh button.

#### V12 — Regional Prospects

**Owners/dependencies:** regional prospects refresh and filters in `views.py`/`ui.py`; U07/U04 policy. **Build:** explain the currently selected eligibility/filter criteria; a genuine empty state offers an explicit broader “Browse developing fighters” filter change. Improve status contrast and selected prospect context. **State:** use the promotion from the current `(promo, fighter, assessment)` row; never an outer company variable. **Verify:** no qualifying prospects, broad result set, spectator mode, unscouted rival and repeated navigation; ratings remain correctly scoped. Add T-UI/scouting regressions. Broadening the view changes only filtering, not who qualifies as a ranked or signable prospect.

#### V13 — World / Companies / Regions

**Owners/dependencies:** world/company/region builders and hubs; U07. **Build:** compact selected-company/gym summary cards, wrapped factual news excerpts, local horizontal scrolling for wide tables and responsive action rows. Show current information and links to full history; forecasts must be labelled. **State:** preserve region/company/gym IDs or validated legacy references across refresh; do not force all hidden pages to redraw. **Verify:** long company/gym names, many columns, multiple ownership types, absent news and 1366px width; right-hand buttons stay reachable. Add T-UI/T-World/T-Narrative. J7/J9 add strategic mechanics later, not inside this layout pass.

#### V14 — Rankings

**Owners/dependencies:** `views.py::refresh_rankings` and ranking page builder; U04/U07/U08. **Build:** explicit scope selector, concise leader/context cards and a large table with a detail pane derived from the selected row. Label “shown” versus “matching” counts. **State:** maintain mode/filter selection and do not derive hidden ability from a tooltip/summary. **Verify:** mismatched P4P/division ranks, missing prior rankings, champion badges, 50-row truncation and a mode switch while details are open. Add T-Profile/T-UI. Presentation must preserve underlying ranking order; a scoring/eligibility change requires a separate approved task.

#### V15 — Combat Sports

**Owners/dependencies:** Combat Sports builders/management windows and refresh in `views.py`; U07/U13. **Build:** selected-sport summary for roster, next committed card, contract risks and recent results; retain sport-native details and full transcript access. Wrap controls or use internal scrollbars rather than shrinking the whole table. **State:** restore the selected sport and entity after refresh, respecting actual ownership and reservations. **Verify:** each supported sport, no owned division, no card, scheduled card and stale athlete; correct native record/rank labels. Add `combat_sports_regression_test.py`/T-Identity. Do not route MMA and other sports into one fight or results model.

#### V16 — Academy consistency and regression protection

**Owners/dependencies:** existing Academy Development Hub and decision bar; U07. **Scope:** Academy is the visual reference, not an evidenced broken subsystem. Reuse its successful grouping and align theme tokens, focus, empty states and resizing where needed. Keep all 4/8/12-week blocks, competitions, promises, reports and graduation paths intact. **State:** no reset of selected cohort or development block; hidden Academy screens remain unrefreshed until navigation. **Verify:** empty/full cohorts, pending decision, report, graduation, assigned Scout and a long-running block across reload. Add `stability_test.py`, scouting and T-Identity. Do not add new training effects as part of visual consistency.

#### V17 — Fight Night landing page / sidebar Event Log

**Owners/dependencies:** sidebar page in `ui.py`, `world.py::write_log`, existing live/archive entry points; U02/U03/U07/U15/U16. **Build:** distinguish “Watch due event,” “Browse recorded events” and “Full event log.” Recommended first slice is a clear landing page using existing routes, not replacing the sealed replay engine. The old Courier log remains available as a complete record with an honest name. **State:** opening archives never settles events; live action is offered only for the appropriate due event. **Verify:** no due event, ongoing card, archived card without full replay and spectator mode. Add T-FightNight. No double application or future telemetry.

#### V18 — Camp Plan usability

**Owners/dependencies:** `views.py` Camp Plan dialog; U07 and J1's future readiness distinction when implemented. **Build:** resizable window with readable gym selection, current focus/workload, expected preparation trade-offs and medical limitations. Link to existing gym/career context rather than duplicating development advice. **State:** changes remain draft until the existing commit action; cancel restores no new mutation. Display stored/estimated camp facts with their correct units and visibility. **Verify:** long gym names, no eligible gym, short-notice camp, injured fighter, hidden information and resizing. Add T-Profile/T-Identity. No extra training roll, new injury probability or automatic optimal gym selection.

#### V19 — Debounced Scouting search

**Owners/dependencies:** Scouting key bindings in `ui.py` and query refresh in `views.py`; independent of Search's already-existing pagination. **Build:** a 200 ms pending Tk callback for text edits, cancelling the previous callback; explicit filter changes/Enter can request a current query immediately. Capture query revision and discard stale scheduled refreshes. **State:** dispose pending callbacks on navigation/window close; retain identity-based selected result and do not regenerate discoveries. **Verify:** rapid typing triggers only the final scheduled refresh, closing early causes no Tcl error, and final results equal an immediate query. Add T-UI/scouting tests. Measure latency separately; reduced refresh count is not itself proof of a speedup.

### Media and Staff implementation cards

#### M1 — Campaign plan, targeting and outcome evidence

**Owners/dependencies:** F0, U06/U11; `media.py` owns actions/outcomes, `world.py` calendar scheduling, `views.py`/`ui.py` presentation, `persistence.py` staged storage.

**Data:** add a versioned plan envelope with objective enum, event/fighter/region/sponsor target references, display snapshots, responsible staff, spend ceiling, allowed action IDs, deadline and status. A completed action stores its original outcome, audience contribution, target and evidence key. Preserve old name-only campaigns as readable legacy records without invented links.

**Build sequence:** (1) save/edit one optional primary plan with no new effect; (2) display existing actions and remaining shared AP/cooldowns; (3) commit an existing action through its current resolver and attach evidence once; (4) add explicit retarget/cancel when the event/fighter changes; (5) only then implement approved target-specific lift and decay with fresh balance tests.

**Objective-specific rules:** event promotion follows the selected event; prospect exposure affects only allowed existing popularity/heat paths, not skill; sponsor work fulfils an existing agreed duty without an extra payout; regional work has a declared geographic scope; trust repair links to recorded harm and cannot erase it. Each action quote states its purpose, cost, cooldown and effect uncertainty.

**HOLD for active-effect slice:** exact spillover to unrelated events, decay curve, objective multipliers and prospect diminishing returns need agreed/calibrated values. Until then the plan is organisational, and the existing campaign outcome formula remains unchanged. Do not present unimplemented targeting as an active bonus.

**Tests/done:** T-Finance/T-Identity/T-Narrative; Event A versus B, duplicate names, delayed/cancelled event, old records, AP exhaustion, stale quote and reload after completion. Evidence and payment occur once; preview/edit is pure. Deliver the organisational slice separately from any retuned economics.

#### M2 — Rights account, delivery rules and forward renewal

**Owners/dependencies:** F0, U11, U06-style quote purity; `media.py` eligibility/counter/monthly/event delivery, Finance UI and persistence aliases.

**Integrity subtask M2-I:** reproduce guarantee alias drift, production omission, relationship/breach divergence and shortfall-labelled-Completed. Define one terms accessor; newly accepted/countered records write both legacy guarantee fields consistently. For conflicting existing terms, preserve originals and expose a reconciliation warning; do not choose a lower payment without an explicit migration rule.

**Account data/UI:** current agreement, optional successor, versioned obligation list, period start/end, evidence, actual delivered counts, separate audience feedback/compliance reasons and immutable receipts. Show source facts beside each obligation. Default first-slice display can truthfully show audience approval and a delivery breach separately without changing their existing numeric effects.

**Renewal steps:** create a new offer referencing the current deal; review quote and one allowed counter; commit a successor with a start trigger tied to the predecessor's end. Define activation at one calendar boundary and use the existing payment owner. Revalidate eligibility/territory/exclusivity then; do not reset predecessor shortfalls or charge a replacement buyout as a renewal.

**HOLD:** canonical production-quality mapping, new minimum-production penalties, make-good terms, the exact renewal opening window and legacy fee-conflict precedence require explicit rules. The initial UI can disclose an unenforced standard; it must not claim compliance is validated until it is.

**Tests/done:** T-Finance/T-Identity plus exact boundary tests for months/events, failed counter, stale accepted offer, successor reload, territory mismatch, high ratings with a deficient card and one guarantee per entitlement. New enforcement applies only to versioned accepted terms. Both old and new fields/aliases remain save-compatible.

#### M3 — Sponsor duties and one commercial receipt

**Owners/dependencies:** F0, U05/U12, M1 evidence; `media.py` sponsor activation, `events.py`/`world.py` event settlement, Finance receipt display.

**Data:** duty ID/type/period/evidence requirement/status attached to an agreement; receipt references event ID and every settled sponsor/rights entitlement. Preserve original sponsor dictionaries and current fee/term semantics. Automatic placement is automatic, not an incomplete task the player must click.

**Build sequence:** expose an activation checklist using current rules; attach qualifying campaign evidence; create receipt rows at the existing event-settlement boundary; add expandable payment arithmetic and shortfall reasons. A monthly duty is Pending until period close, not Failed simply because the month started. Retain legacy current-month/current-roster champion/top-10 matching and half-fee settlement.

**UI:** active partner cards show maximum fee, estimated actual fee, period and action needed. A receipt distinguishes guarantee, bonus, each sponsor fee and relationship changes; it links to evidence without mutating it. Over-cap legacy portfolios remain intact.

**HOLD:** any new monthly missed-duty fine, additional capacity, replacement-buyout policy or stacking interaction must be separately specified. Do not layer a new penalty over the existing half-fee rule by default.

**Tests/done:** T-Finance/T-Identity; placement, qualifying/nonqualifying campaign, transferred/renamed fighter, no event, several events, cancelled event and period boundary. Every ledger payment has one receipt entry; reopen/reload cannot pay twice. Include historical receipts whose source campaign is no longer available.

#### S1 — Actual department lead and accountable briefs

**Owners/dependencies:** F0 for new briefs; lead-attribution repair can start independently. `world.py::staff_skill`, `staff_member_for_role`, contribution records and Staff UI.

**Lead repair:** use one effective-quality selection rule for passive effect, visible lead and future contribution attribution; preserve stable tie behaviour from the current implementation. Do not retrospectively rewrite staff history. Hire previews state whether the candidate replaces a lead or adds no passive effect.

**Brief data:** department, objective, selected targets, automatic lead ID, allowed existing actions, due period, spend limits and linked work items. Balanced/no-brief preserves current passive mechanics. No new staff fatigue meter.

**Pilot implementation:** Marketing consumes M1 plans; Matchmaking produces J1 recommendations; Talent Relations prepares J3/A5 reviews. Scouting displays its existing queue/capacity rather than owning duplicated assignments. Medical initially flags existing return-date problems; Broadcast initially checks existing terms/production readiness; Compliance remains advisory until J5 is approved.

**Workflow:** create/edit draft → responsible lead validates → recommendation prepared → player or authorised S2 commits existing action → evidence review. Extra employees do not unlock concurrency or stacking unless separately approved. Employee departure invalidates responsibility and exposes a handover, not silent substitution.

**Tests/done:** T-Finance/T-Identity/scouting/T-Narrative; differing skill/morale rankings, ties, no staff, multiple same-role staff, departing lead and disabled narratives. Advice is not completed work or XP. Preserve all existing passive caps and Scout ownership.

#### S2 — Bounded delegation and exception reporting

**Owners/dependencies:** F0/S1 and the domain action to be delegated; existing calendar work queue and notification aggregation.

**Policy data:** owner/company, player-selected autonomy mode, recommendation topic filters, action allowlist, permitted target set, per-action ceiling, monthly ceiling, minimum cash reserve, review period, explicit enabled flag and revision. Support all four R06 modes; never migrate an old generic toggle into broader permission. Keep Scout automation's existing scope distinct. Selective Recommendations is player-scoped advice, while the new-game initial selection remains a separate consultation item.

**Execution:** inspect due committed work once at its calendar boundary; obtain a pure current quote; verify permission, shared capacity and remaining budget; commit through the original domain action; record actual spend/evidence. Competing actions reserve/revalidate against the same running budget before each commit. Deterministic priority order must be documented and tested.

**Exceptions:** unaffordable, changed terms, departed staff/fighter, invalid event or expired permission moves work to Needs attention. Show one grouped review with exact reasons and actions. No auto-retry that produces more negotiation rolls; repeated calendar processing returns the existing attempt record.

**Scope boundaries:** media delegation does not authorise other departments. Full Auto is a supported player choice, not a synonym for media-only automation: each action needs a registered permission, domain handler and tests before the UI may advertise it as automated. Existing sporting and medical eligibility cannot be overridden by staff. Testing automation additionally requires J5's implemented provider/case rules and explicit testing permission. Champion-miss decisions remain player prompts under R10. Unsupported actions must be identified, not silently described as automated.

**Tests/done:** T-Finance/T-Identity/T-Narrative; manual plus automatic capacity use, exact reserve edge, simultaneous work, revoked permission, failure mid-commit, restart and missing target. Default path preserves behaviour/RNG. A report lists authorised actions and actual spend, not only “staff handled it.”

#### S3 — Staff specialties, progression and retention

**Owners/dependencies:** proven S1/S2 work evidence, S4 employment lifecycle; staff definition/effect helpers and persistence.

**Definition catalogue:** each specialty has ID, explanation, applicable work, trigger, bounded advantage, drawback/cost and live mechanic or explicit descriptive-only classification. Preserve unknown legacy specialty strings. Do not attach bonuses by parsing free text.

**Progression data:** employee ID, distinct completed-work periods, credited work IDs, last gain date and growth history. Only successful eligible work can qualify; merely opening a page, toggling narratives, duplicate receipts or repeated trivial actions cannot. Reputation/skill and narrative legacy are separate concepts.

**Retention:** expose workload/pay/role concerns with observed evidence and a future review. Acknowledgement is not a morale boost. Renewal and severance use existing actions; departure closes/hands over work through S1. Keep genuine existing morale/contract changes separate from newly proposed satisfaction mechanics.

**Effect implementation boundary (approved v1):** the exact non-Scout effect table is now explicit and limited to three entries. **Campaign Coordinator** reduces eligible paid media campaign cost by 2%; **Contract Administrator** reduces the existing negotiation-administration basis by 2% and never changes fighter salary, purse, signing bonus or selected terms; **Production Coordinator** reduces eligible production staging by 2%, excluding security, guarantees, athlete pay, medical and testing. One effective lead owns an effect, the reduction is applied after existing modifiers, rounded once and capped at 2% of the eligible pre-specialty subtotal. Free actions stay free. The catalogue and Staff readout show the trigger, advantage and boundary; all other legacy specialties remain descriptive-only.

**Remaining HOLD:** progression growth caps/curve, cooling of negotiation heat, satisfaction thresholds and new departure probabilities still need a separate balanced specification. The earlier one-point-per-quarter figure remains a trial proposal, not approved shipping behaviour. These effects do not authorize new AI payroll, medical/testing automation or combat/training changes without their own source-bound and long-run gates.

**Status: COMPLETE for the approved v1 specialty/progression slice.** The
catalogue, three bounded live cost effects, one-effective-lead rule and
evidence-backed progression worker are implemented and visible in the Staff
readout. Paid, executed work must carry durable work/lead/evidence identities,
span three distinct months and two targets before one skill point can be
awarded; the annual +4 cap, skill ceiling and duplicate/legacy/malformed
evidence guards are enforced. Retention remains an observed review surface,
and every unapproved satisfaction, negotiation-heat cooling or departure
probability mechanic remains held by the explicit policy gate above.

**Tests/done:** T-Finance/T-Identity/T-Narrative, anti-farming fixtures and multi-seed employment economics before effects ship. No role stacking or exceeding existing caps. Any medical/training/combat impact triggers fresh relevant source-bound gates.

#### S4 — Durable AI employment and specialist routing

**Owners/dependencies:** S1 lead rules, existing employment/finance helpers; AI hiring in `views.py`, promotion state in `models.py`, monthly lifecycle in `world.py`.

**Steps:** identify candidate without removing them; check role need, affordability and the existing purchase rules; atomically move the same staff ID into the promotion's staff collection and record one debit. Integrate retained employee salary/term with the appropriate monthly payroll/expiry owner. On failure leave the candidate in the market; on expiry release or renew through an explicit transition.

**Compatibility:** retain valid pre-existing AI staff; don't create employees from old hire headlines. Define a bounded headcount/payroll policy before enabling new ongoing AI costs; a data repair alone does not approve unlimited recruiting. Do not silently give AI new passive buffs.

**Specialist split:** Academy Coach work is J6; disciplinary/automatic testing is J5. The Trainer fallback remains until J6's mechanics are approved. Compliance UI must not present random positives-as-injury as a proven detection model.

**Tests/done:** T-Finance/T-World/T-Identity; unaffordable candidate retained,
affordable hire persisted once, repeated processing, existing staff,
expiry/market return, financial distress and reload. Long-run payroll/AI
survival evidence is required for the enabled lifecycle. Report any new
ongoing cost separately from the original missing-list mutation repair.
Two-year expiry/market-boundary coverage, affordability/read-only projections,
malformed-term preservation and payroll evidence are now green. **Status:
COMPLETE for the approved durable-employment slice.**

### Journal-inspired implementation cards J1–J12

#### J1 — Explainable MMA booking workbench

**Owners/dependencies:** U01/U04/U08, F0/S1; existing assistant/manual validation in `views.py`, date/readiness helpers in `world.py`, scheduling in `events.py`.

**Data:** saved promotion brief plus optional fighter-ID exceptions: preferred window, development/commercial emphasis and allowed opposition range. Draft proposals contain IDs, current quote/readiness evidence, locked existing bout IDs and unresolved slots; they are not scheduled fights.

**Implementation:** (1) extract/share eligibility reasons without changing outcomes; (2) show several explainable alternatives for the selected fighter; (3) propose filling selected empty slots while preserving locked pairings; (4) offer an entire reviewable draft; (5) commit selected changes through current add/schedule handlers after revalidation. Do not use the stochastic builder on refresh; any stochastic proposal generation must be an explicit action with defined draw behaviour.

**Future medical bookings:** separate a tentative planning slot from a firm booking. Initial safe slice shows recorded earliest return and camp requirements without changing the existing hard block. Activating tentative reservation requires an approved clearance/confirmation deadline and cancellation policy; never promise recovery or allow an uncleared fighter to compete.

**UI:** card slot, selected pair and each excluded alternative show exact reasons: unavailable, unaffordable, sporting ineligible or outside player preference. Preferences rank eligible candidates only.

**Tests/done:** T-World/T-Identity/T-UI; locked bouts, duplicate names, shallow divisions, champion protection, title merit, rematch cooldowns, changing injuries and dates. Default scoring/order/RNG stays unchanged where intended; a deliberately new proposal policy is measured separately.

**Status: COMPLETE for the approved v1 workbench slice.** The explicit,
RNG-pure proposal path now reuses current availability and matchup evidence,
retains blocked alternatives and shallow-division explanations, refreshes
injury/date/rematch state before commit, and fails closed on duplicate or
ambiguous identities. Pair-level title-holder/challenger merit and special-belt
checks run again at the receipt-backed commit boundary; locked existing bouts,
unresolved TBA slots and unaffected corners remain preserved. The separate
future extension that would make a medical planning note into a firm
reservation remains policy-gated pending clearance deadlines, cancellation
terms and sanction rules; the shipped slice never promises recovery or reserves
a fighter.

#### J2 — Persisted event-preparation timeline

**Owners/dependencies:** F0/M1/M3, U02/U03; `events.py::prepare_event_result`, press/weigh-in resolvers, existing live/archive presenters.

**Data:** event ID, preparation revision, stage states, recorded press/weigh-in outcomes, affected fighter IDs, campaign evidence and final readiness. Stage completion keys must survive reload and link to the normal event package.

**Build:** first show existing stored outcomes as cards with no timing change. Next allow campaign planning before the event through M1. Only a separately approved timing slice moves stochastic press/weigh-in resolution earlier: resolve once at its chosen calendar boundary, save the output, and have watch/simulate consume that output rather than rerun the resolver.

**Change handling:** replacing a fighter invalidates only the relevant unresolved/pre-commit stage; do not rewrite an already-recorded weigh-in. Explain which costs/work remain sunk, which must be retargeted and whether a new official resolution is needed. A cancelled event closes linked work through A2/M3, not by deleting evidence.

**Tests/done:** T-FightNight/T-Finance/T-Identity/T-World; full watch versus simulate equivalence, reload after every stage, double preparation, replacements, TBA, tournament entrants and cancelled cards. No future telemetry or second hype/fine. HOLD the earlier-resolution stage until draw order, sanction/replacement policy and save interruption semantics are specified.

#### J3 — Reviewable contract batches and forward commitments

**Owners/dependencies:** U10/U13, F0/S2/M2; current contract batch/auto-renew helpers, Finance quote and Contracts UI.

**Data/UI:** a batch ID with selected contract/fighter IDs, quoted terms, current status, required cash, contingent obligations and per-row result. The batch review lists every row, including failures beyond the old 40-line popup; an expandable result ledger remains saved/readable.

**Execution:** keep explicit user selection; identity-deduplicate; quote without negotiations; show total guaranteed exposure and ordering. On confirmation process through the existing negotiation handler in a documented stable order, rechecking reserve and target status per row. Partial success is allowed only when explained in advance; show each actual success/failure without rerolling failed offers. Do not promise all-or-nothing negotiation if the existing action cannot provide it.

**Automation:** reuse S2 permissions; current core auto-renew remains the legacy/default policy. Optional expanded policies must state allowed targets and deal types. Rights successors use M2; staff contracts retain their distinct expiry/severance rules.

**Tests/done:** T-Finance/T-Identity plus sport tests; duplicate selection, concurrent cash commitments, retirement, target leaving between review/commit, partial results and restart. HOLD new salary escalators, loyalty penalties or retention weights. Review UI may ship before expanded automation.

#### J4 — Historical truth, company membership and configurable records

**Owners/dependencies:** U08/V05, F0; `world.py` bout snapshots, `views.py` historical fallback, `admin.py` title transitions, `persistence.py` historical storage.

**Repair slice:** replace only the missing-historical-opponent-record fallback with “Not recorded”; retain valid snapshots and replay matching. Test historical and today's records deliberately differing. Do not populate missing values from contemporary ranks/ratings.

**New data:** append-only membership events with event ID, company/fighter IDs, action (join/leave/loan/return), effective date/precision, reason and source transaction. Capture on real transitions before identity or roster mutation. For imported current rosters use “known present at migration,” not an invented join date. Title events remain owned by existing crown/vacancy helpers.

**History UI/index:** as-of views derive from supported membership intervals and title history; label incomplete coverage. Durable compact bout/tournament facts remain separate from bounded replay caches. Column settings use stable keys and preserve future unknown keys; provide complete details/export of recorded fields, never hidden ability.

**Tests/done:** T-Identity/T-Profile/T-World; rename, transfer, retirement, editor departure, return loan, same-week bouts and missing dates/replays. No duplicate vacancies after a completed title fight. Existing checksums/historical fixtures remain unchanged; archive migration needs measured load/save cost and an explicit retention policy before release.

**Status: COMPLETE for the approved truth, identity and reader slice.** The
profile fallback now reports `Not recorded` when an at-the-time opponent fact
is absent; valid archived IDs and rank snapshots remain authoritative. Future
membership transitions are append-only and identity-bound across signing,
transfer, loan/return, retirement, editor and title-vacancy boundaries. The
Company Timeline, as-of/interval projections, title-lineage joins, complete
history paging/export and configurable stable column layout retain malformed or
legacy evidence with explicit coverage labels rather than inventing dates or
current records. A destructive archive-retention/compaction policy remains
held until separately specified and measured; this card adds no pruning.

#### J5 — Disciplinary cases and per-corner title sanction

**Owners/dependencies:** F0, existing medical/booking/weight/title owners; `views.py::run_drug_tests`, `events.py::run_weigh_ins`, world eligibility and title transition helpers. **Status:** rules design must precede active mechanics.

**Data design:** case ID, fighter/test/event IDs, provider and frozen policy/price versions, sample/confirmation records, evidence availability, provisional restriction, sanction start/end, appeal/review records and final resolution. Confirmation and appeals are required parts of the approved full-system direction, not optional cosmetic links. Separately store medical return and disciplinary restriction. Title sanction snapshots contain scheduled belt, each corner's eligible-to-win/retain flags, player decision and actual settlement decision/reason.

**Safe first slice:** read-only display of recorded test messages and existing medical limitations, explicitly labelled legacy evidence; prospective case storage scaffolding without reclassifying old injuries. Do not call an unconfirmed finding a violation or implement a fictional detection model as truth.

**Confirmed direction:** player-selected staff autonomy; a player prompt for champion weight misses; a full testing system with player-customisable strictness and testing providers whose greater effectiveness costs more. R06/R10 supersede the earlier media-only autonomy, automatic weight-miss vacancy and simplified automatic confirmation proposals. **Remaining specification work:** precise title-decision options and AI/spectator policy; testing-policy jurisdiction, effectiveness model, provider numbers, confirmation/appeal timing and sanction bounds. Record full outcome tables and distinguish user choices from proposed balancing values before enabling mechanics.

**Execution/tests after approval:** one domain evaluator shared by booking and settlement; a suspension ending clears only itself. Cross-product tests of either/both weight misses × either winner/draw/NC × belt type, plus replacements/tournaments and expiry boundaries. T-World/T-Identity/T-Finance and fresh applicable native gates. No automatic delegated testing before this card's mechanics are approved.

#### J6 — Explicit Academy coaching and second careers

**Owners/dependencies:** S3/S4/F0; `Gym` and staff records in `models.py`, Academy Trainer reads, hiring and retirement transitions.

**Safe first slice:** accurately expose current gym head-coach text/quality and the Academy fallback without pretending the named person is already an employed staff object. Define a linked mentor candidate with a new staff ID plus original fighter ID; keep the retired fighter object, records and portraits intact.

**Workflow:** eligible retired fighter considered → aptitude/terms preview → explicit hiring → assigned cohort/focus and bounded work → review → expiry/handover. Decide comeback availability before permitting an active comeback to coexist with full-time mentoring. Never infer coaching skill directly from fame or clone the fighter into a second career record.

**Decision / v1 implementation:** use a deliberate hireable Academy Coach
route. The legacy gym/head-coach Trainer remains the fallback when no active
Academy Coach is assigned; an explicit hired coach may supervise one active
cohort and contributes one bounded quality adjustment to that block. The
candidate keeps a separate stable staff ID while a retired-fighter link, when
available, preserves the original fighter identity and record. Salary, expiry,
handover review, reassignment and comeback blocking are explicit boundaries.
Default training remains unchanged when no coach is assigned. This is the
single owner of S4's coach extension, not a second overlapping implementation.

**Tests/done:** T-Identity/T-Profile/T-World, duplicate recruitment, legacy
gyms, expiry, no coach, reassignment and comeback cases. Evidence-linked
progression uses S3; all development/trait changes require fresh source-bound
checks. No hidden random trait replacement. **Status: COMPLETE for the
approved v1 coaching slice.**

#### J7 — Structured company proposals and ownership history

**Owners/dependencies:** F0/A1 references, existing transfer/loan/profit-share handlers; company hubs in `views.py`, child lifecycle in `world.py`.

**First slice:** wrap existing swap/cash/loan actions in a reviewable proposal with both parties, fighter IDs, costs, expiry and warnings. Confirm current ownership/bookings/title consequences before delegating to the existing commit handler. Record accepted/rejected/withdrawn outcome and terms; preserve existing AI acceptance rules.

**Later agreements:** a treaty record needs allowed transactions, obligations, term, termination and factual relationship evidence. A relationship score cannot become an unexplained modifier or silently loosen sporting merit. Use one history/reference owner shared with J4.

**Ownership change:** snapshot cash, contracts, staff, loans, titles and outstanding work before a spin-off/acquisition; define which obligations transfer and which end. Do not implement this from a company rename or by duplicating rosters. HOLD bilateral scoring, treaty effects and spin-off allocation rules until specified.

**Tests/done:** T-World/T-Finance/T-Identity; stale proposal, moved fighter, booked champion, duplicate names, insufficient cash, accepted transfer once, loan recall and parent takeover. All departures call the sanctioned vacancy path before roster/identity mutation. No forced company purge or automatic war/elimination policy.

#### J8 — Tournament editions, seeds and durable history

**Owners/dependencies:** F0/J4, existing tournament simulator/bracket/settlement in `events.py`; J1 readiness if future editions are added.

**Data:** tournament series ID, edition ID, sport/division, date/precision, entrant IDs, initial seed/draw, substitutions, stages/bout references, champion and terminal status. Keep compact facts outside replay retention; original event/bracket records remain authoritative and linked.

**Build:** index existing unambiguous editions without inventing missing rounds; expose searchable edition history; add entrant/seed/alternate review to the existing one-night format; save any draw once. Stage results link to the ordinary professional ledger rather than adding a duplicate win/loss. Record withdrawals with reasons.

**HOLD:** multi-event competition rules for carry-over injuries, replacement slots, expired contracts, advancement on draw/NC and postponement. Do not bypass ordinary eligibility because a fighter already appears in a bracket.

**Tests/done:** T-World/T-Identity plus tournament-specific cases registered in the runner; duplicate names, substitutions, tie/NC policy, replay expiry, rename, transfer, cancellation and reload between stages. Index queries are bounded, summaries reconcile to stored bouts, and seeding review does not reroll or change outcomes on refresh.

#### J9 — Regional opportunity and division feasibility

**Owners/dependencies:** U04/U09, A1/A3 for calendar/finance; venue/region/domain helpers in `world.py`, division manager in `views.py`.

**Data/UI:** pure assessment with as-of date, current region/venue inputs, known eligible roster/pairs, scouting coverage, payroll assumptions and explicit blockers. Show signable versus merely observed talent; label unknown prices/availability. Do not include unrevealed AI future plans as confirmed conflicts.

**Build:** expose existing venue access and regional factors; compute read-only division depth using current merit/medical/contract rules; show a region event planner using actual schedules. Opening/closing a division retains its existing cost/vacancy semantics and never auto-moves weight classes.

**Invitation slice:** new versioned offer with host, date window, guarantee, local-participation requirement, expiry and cancellation terms. Generate only at an approved calendar/action boundary, never on refresh. Link to M2/M3/A2 so terms settle once. HOLD the invitation-generation frequency, economics and consequences until calibrated.

**Tests/done:** T-World/T-Finance/T-Profile; shallow/no division, unscouted market, occupied venue/date, missing local headliner and changing roster. “No eligible challenger” remains a blocker. Proposed growth forecasts are assumptions; evidence must precede claims of profitability or sustainable expansion.

#### J10 — Searchable rules help and trustworthy comparisons

**Owners/dependencies:** U04/U08/U14/U07; existing guide, comparison, search and visibility helpers.

**Data:** stable help topic ID, title, short explanation, supported action links and linked domain terms. Store user search preferences separately; do not copy mutable formula results into permanent help text. A proposed help catalogue can live in a new small data module.

**Build:** start with ranking scopes, title eligibility, availability/camps, staff contribution, campaign costs, obligations and finance vocabulary. Each topic has a concise answer, “why blocked?” reasons and a working route back to the selected context. Inline confirmation and disabled reasons follow V/U cards; preserve destructive confirmations.

**Comparison slice:** add cohort labels/date/coverage to existing comparisons before introducing percentiles. Exact percentile calculation is permitted only for a legitimately visible cohort and tie policy. With partial scouting, show the known sample or qualitative uncertainty, never a hidden world ranking disguised as a percentile.

**Tests/done:** T-UI/T-Profile/T-Identity; help text agrees with fixtures for domain helpers, stale links fail gracefully, keyboard search works and dark/light themes remain readable. Alias/biography search indexes only stored visible text and retains pagination. No new gameplay or assessment RNG.

#### J11 — Persistent simulation pause policies and checkpoints

**Owners/dependencies:** A1/A7 for optional tracked sources; existing `begin_advance_sequence`, stop requests, save/recovery code.

**Data:** target date, explicitly chosen stop conditions, watched entity IDs, last completed boundary and stop reason; configuration separate from a live runtime callback. Saved resumability must reconstruct a valid job from committed game state, not serialise Tk callbacks or partially executed methods.

**Build:** expose current safe stop; add pure predicates for actual recorded events/actionable obligations at completed week boundaries; offer a deliberate resume using remaining target and still-valid policy. Preserve spectator's no-routine-prompt preset. An auto-advance job never grants staff permissions it did not already have.

**Checkpoints:** optional pinned save records show size/date/source and verification status; keep them separate from two-slot rolling recovery. Pin/delete requires explicit user action. No unlimited automatic annual copies or automatic deletion of career data.

**Tests/done:** advance notifications, T-Identity/T-World/T-UI; exact target, repeated stop, reload boundary, failed save, no matching event, retired watched fighter and disabled predicate. Do not claim immediate stop inside a synchronous task; measure the longest blocking step. Long-run test execution requires its own authorised budget/scope.

#### J12 — Editor preflight, presets and career-to-database conversion

**Owners/dependencies:** F0/J4 identity contracts; shared universe validation, database editor and persistence.

**Preflight:** return structured issue rows with severity, entity/field, evidence and suggested remedy. Separate invalid references/schema from playable-but-risky population/payroll/depth warnings. Rendering/exporting warnings cannot repair, sign, delete or appoint anyone.

**Preset slice:** support only existing settings, with named preset ID/version and a before/after diff. Validate the complete proposed configuration, identify its scope (new game/current future bookings), and commit explicitly. Completed event terms remain frozen. Do not add unsupported combat switches to satisfy a template name.

**Conversion slice:** separate destination, preserved live save, staged validation and atomic output. The approved v1 policy is a **new-start database**, never a cloned active save: preserve fighter/promotion IDs, current supported skills/age, career records, roster ownership and supported contracts; reset time, cash, finance, inbox, pause targets and active work. Strip nested scheduled/event/finance ledgers from the playable package. Retain completed history and every excluded obligation in a sibling, labelled `<name>.conversion.json` provenance manifest with structured severity/entity/field/evidence/remedy rows. Unknown fields, duplicate top-level fighter IDs, invalid divisions and missing promotion owners are structural errors and refuse the write; populated ongoing work is shown in an exact exclusion report and requires explicit acceptance. Cancellation, destination conflicts and failed staged output are non-destructive. No silent flattening of saved outcomes into new starting records.

**Tests/done:** T-Editor/T-Identity; duplicate IDs, missing owner/title references, invalid division, unknown fields, cancelled conversion, destination conflict and round trip. Validation remains pure, live save hash unchanged, failed output leaves no half-valid database. New combat rule families are D02, not this task.

### Additional-feature implementation cards A1–A7

#### A1 — Owned-company calendar and optional child control

**Owners/dependencies:** F0/J7 references, V03/V15/V13; `events.py` main schedule, `world.py` sport scheduling/due processing, MMA child lifecycle and views.

**Read-only slice:** project actual scheduled records into one calendar row shape: source system, event ID, owning/paying company, date, sport, status, participants/reservations and valid action route. Do not copy events into a second schedule. Display AI forecasts separately when no committed event exists.

**Interaction:** filter by owner/sport/date; open the source editor or read-only AI detail; show cross-company fighter/loan conflicts without merging wallets. Preserve selection across refreshed source lists.

**Controlled-child slice:** opt-in parent-approved draft, child-funded quote, current roster/loan/medical validation, future commit and due execution through the child's normal result/finance owner. Default remains AI-managed. Specify manual-versus-auto cadence precedence; one committed card must not generate an extra automatic card in its occupied period.

**HOLD:** manual MMA child approval/AI override and conflict priority rules before enabling that mode. Calendar browsing is independently shippable.

**Tests/done:** T-World/T-Identity/T-Finance; same-week multi-sport shows, loan recall, expired athlete, rename, postponement/cancellation, failed due event and reload. No early/double execution or cross-owner cash transfer. Apply F0's stable IDs rather than exposing list indices as durable event references.

**Status:** COMPLETE for the approved read-only owned-calendar slice. The
controlled MMA child scheduler remains a separately held policy decision for
manual approval, AI-cadence precedence and cross-company conflict priority.

#### A2 — Project closeout and complete commitment accounting

**Owners/dependencies:** F0/M3; `awards.py` super-event terms/lifecycle, `events.py` schedule/cancel, `world.py` finance. Can begin with G0 reproductions before new work state.

**Repair sequence:** reproduce `security` versus `security_cost` and `revenue` versus `revenue_multiplier`; define an accepted-terms normaliser and preserve original values for compatibility review. Add tests at approval, schedule and settlement, not only the UI quote. Define how old accepted conflicting records are handled before changing their economics.

**State machine:** Offered → Planning → Scheduled → Completed/Failed, with explicit Cancelled/Expired branches. Each transition validates current status/revision. A planning deadline needs closeout; a scheduled cancellation resolves its offer and linked work. Use one terminal settlement key so repeated calls cannot duplicate refunds, rewards or history.

**Money:** show paid/sunk/refundable/unpaid components; ordinary event profit remains distinct from full project result including evidenced deposits. No refund without an actual payment reference. Cancellation terms are frozen at acceptance; legacy missing terms receive a disclosed neutral/manual-review path, not an invented debt.

**HOLD:** legacy fee precedence, refund schedule, deadline extension rights and any new incident penalties. Integrity fixes that change future event revenue/cost require fresh economy tests.

**Tests/done:** T-Finance/T-Identity/T-World; every state/reload, duplicate closeout, partial failure, lost required star, cancellation, expiry and another concurrently active project. No orphan work or clearing unrelated projects. Retain old completed history unchanged.

**Status:** COMPLETE for the approved lifecycle-integrity slice. Legacy fee
precedence, refund schedule, deadline extension rights and new incident
penalties remain explicit policy holds; no unapproved economics are inferred.

#### A3 — Cross-event cash scenarios

**Owners/dependencies:** U09/U12, F0/A1, M2/M3/A2 agreed terms; existing finance and capital/upkeep helpers.

**Model:** 12 weekly buckets with opening/closing cash, committed inflows/outflows, conditional receipts and assumption-based estimates, per paying company. Store scenario ID, input revisions, edits and forecast snapshot; actuals remain canonical ledger data. Avoid summing partial previews as complete profit.

**Build:** extract pure settlement-aligned components; list recurring costs and agreed due dates; forecast actual scheduled events; add conservative/base/stronger-demand assumptions; calculate lowest balance and feasible break-even. Label unavailable cost/uncertainty rather than returning a deceptively exact total.

**Apply workflow:** draft scenarios do nothing; compare changes; show diff and fresh quote; then apply individually approved schedule/price/production changes through their owners. If one cannot apply, preserve an explicit partial-application result or cancel before starting under the chosen policy. No implicit new cash reservation.

**Tests/done:** T-Finance/T-Identity; shared cash shortage, payroll between shows, paid deposits, conditional rights/sponsors, taxes, no events, capacity ceiling, stale assumptions and cancellation. Repeated scenarios preserve state/RNG. HOLD probability claims and new demand curves; measure historical forecast errors before describing accuracy. Old forecast snapshots remain available for comparison.

**Status:** COMPLETE for the approved review-only sensitivity and snapshot
slice. Probability claims, new demand curves and any multi-event auto-apply
workflow remain held; individual existing editors remain the only mutation
owners.

#### A4 — Calendar-owned objective outcomes

**Owners/dependencies:** F0, existing owner-goal definitions/persistence and `views.py::refresh_owner_goals`; calendar/event evidence owners.

**Data:** objective ID, owner/company, type (`achieve_once`, `maintain`, `improve_from_baseline`), agreed baseline/target, start/deadline/precision, observation cadence, progress evidence and terminal resolution. Preserve original legacy fields.

**Steps:** first stop UI refresh from deciding outcomes; build pure progress projection; move evaluation to defined business/calendar boundaries; seal once-on-time achievements; evaluate maintenance across its full observation period; record revisions rather than overwrite targets. A current value reached late cannot silently count as on-time evidence.

**Legacy rule:** unknown historical completion remains explicitly legacy/unverified, with current progress separate. Do not turn a previously displayed Complete into a newly punitive failure. New objectives use exact versioned semantics from creation.

**Review UI:** quarterly summary, evidence and next action; no auto-dismissal, owner intervention or financial penalty in the first slice. Revised agreement requires explicit confirmation.

**Tests/done:** T-Identity/T-UI/T-Narrative; page never opened, deadline boundary, late hit, cash fall after sealed achievement, broken maintenance, unknown metric, takeover and spectator. HOLD observation frequency/reward policy where not already defined. Status persistence and display purity are independently testable.

#### A5 — Relationship cases, not a duplicate promise system

**Owners/dependencies:** S1 Talent Relations, J3, F0; existing Career Journeys, promise flags/deadlines and story references.

**Data:** case ID, fighter/source promise or career ID, reason/evidence references, acknowledgement, selected existing support action, review date and resolution. Existing promise/career state stays authoritative; derive outstanding duties instead of copying contradictory flags.

**Workflow:** record-backed concern opens case → user reviews facts → choose an existing support action or no new promise → existing domain commits any effect/cost → review compares actual evidence → close with remaining duties clearly identified. A case may stay open after partial delivery. Departure/retirement explicitly closes or transfers responsibility without deleting the story.

**UI:** portrait, cause, what is owed, due date, realistic available actions and full history. Old low trust without a recorded cause says “Reason unavailable.” Do not invent a psychological diagnosis or a personal feud from a score.

**Tests/done:** T-Narrative/T-Identity/T-Finance; partial promise, repeated acknowledgement, repeated review, missing evidence, renamed/same-name fighters, support failure, departure and reload. No benefit or RNG from talking/display. HOLD new deadline extensions and morale formulas; existing supported actions can be linked immediately.

#### A6 — Recruitment decision packs

**Owners/dependencies:** U04/V11, F0, existing scouting/watchlist identities and assignments; do not rebuild the watchlist engine.

**Data:** pack ID/name/purpose, selected existing watchlist, candidate IDs, player notes, comparison criteria, dossier reference/date/confidence, decision state and timestamps. Player opinion is explicitly separate from scout facts. Rename/archive list operations affect the list only.

**Build:** expose create/rename/switch/archive existing named lists; attach a two-to-four-candidate decision pack; show dated side-by-side public/scouted facts and missing information; route “request updated report” through the actual Scout/cost/capacity action. Recommendations must explain uncertainty, not sort hidden true ability.

**Lifecycle:** unavailable or retired candidates remain visible as historical alternatives with a current warning. Refresh updates current availability while preserving the earlier decision snapshot. Deleting a pack/list never deletes a fighter/report. Multiple-list alerts share existing deduplication.

**Tests/done:** scouting/T-Identity/T-UI; duplicate names, overlapping lists, stale reports, no scout/cash, partial estimates, candidate departure, archive/reopen and reload. No free scouting, fabricated prices, automatic signing or revealed hidden stats. Existing 200 ms/100-row Search behaviour remains intact.

#### A7 — Followed-story catch-up

**Owners/dependencies:** F0/J4 durable references; existing narrative thread/reader/digest code, inbox adapter. Do not replace the general weekly digest.

**Data:** subscription ID/type/entity or thread ID, user enabled/snoozed state and last explicitly acknowledged beat cursor. Store a coverage boundary so expired old material is recognisable. Do not use the current array position as a durable cursor.

**Build:** follow/unfollow in existing profile/company/story contexts; query retained newer beats with bounded indexes; group by story while keeping originals accessible; show current stakes and existing safe action links. Mark read only on acknowledgement or an explicitly documented open/read action, never on background refresh.

**Behaviour:** no new simulation/narrative generation pass. A summary may condense recorded facts but must not invent a causal explanation, future outcome or hidden scouting information. Snooze affects notifications, not underlying history; resolved threads remain readable.

**Tests/done:** T-Narrative/T-Identity/T-UI; multiple new beats, unchanged refresh, name change, deleted/expired source segment, duplicate subscriptions, long absence and reload. A coverage gap is visible rather than silently treated as “nothing happened.” Measure query/refresh cost on large retained histories before claiming scalability.

### Long-run task L0 — qualification and diagnostic evidence

**Dependencies/owners:** stable targeted feature tests, current release profile, existing `admin.py::run_play_level_audit`, isolated runtime/persistence and calendar task diagnostics. This is not an instruction to run a century simulation during a page task or this documentation update.

**Implementation plan:** extract or wrap the existing fresh-world audit so it can run with an explicit seed, duration and source inventory in an isolated task directory. Retain the real weekly loop and native release host. Add periodic checkpoint metadata: completed week, configuration, relevant RNG states, source/schema/registry hashes and output cursor. Resume only when inputs match; reject incompatible source changes rather than silently continue mixed evidence.

**Measurements:** retain per-year and per-company/division active talent, recruit availability, eligible title challengers, vacancy duration, events, cash/commitments, staff counts/payroll, case/project backlogs, expired offers, duplicate identities, archive sizes and bounded task timings. Separate player/AI, owned child/sport and region/gender/division cohorts. Headline total population must not conceal empty divisions. Use actual records, not a second simulated approximation.

**Failure semantics:** hard invariants include duplicate settlement, broken identity/ownership, impossible negative remaining obligations and orphan references that prevent resolution. Population/finance/variety thresholds are policy/balance gates: record the baseline and obtain thresholds before tuning, rather than declaring arbitrary extremes failures after the run. Stop safely and retain a diagnostic checkpoint on a hard invariant failure. Do not auto-repair the world to finish the audit.

**Run plan for a future authorised audit:** short seeded smoke → a multi-year cohort across small/medium/major conditions → longer spectator and explicit player-policy cohorts → the agreed century qualification. Preserve failed seeds and all raw reports; no claim that a capability or older certificate establishes a completed current run. Report total simulated weeks, all seed/configuration/source identities, wall-clock timing and interrupted/incomplete runs.

**Tests/done:** fresh versus resumed short-run full-state/RNG parity, rejected source mismatch, checkpoint failure cleanup, source report accounting, no user's save mutation, and no audit hooks left on live classes. Native calibration remains independently required for relevant mechanical changes. Testing V2 is not the audit workspace; any use of a copy must be separately authorised and its original hash retained.

### Deferred and excluded cards D01–D14

These cards ensure every deferred point is covered without turning “mentioned in a report” into implementation approval. **Luna must not enable them in an unattended batch unless the user specifically selects the card and resolves its decision gate.** It may document a bounded design when asked; it should continue other authorised READY tasks when one of these remains blocked.

#### D01 — Real-date calendar migration

**Why separate:** the current four-week month/day refinement is a save and scheduling contract. **Required design:** canonical real-date representation; mapping for every existing deadline, camp, cooldown, history interval and term; treatment of ambiguous weekly dates; leap years and month-end billing; event-order stability. **First permitted deliverable:** conversion matrix and reversible migration prototype on disposable fixtures, not a live-save rewrite. **Gate/tests:** user approves timing/economic interpretation; compare every due action and legacy history precision across old/new calendars, restore on failed conversion, and measure long-run effects. No automatic “week 4 means month's final day” assumption.

#### D02 — New combat behaviour, exhibition settlement or rule formats

**Why separate:** existing 440-move native certification does not certify new mechanics. **Required design:** exact allowed actions/scoring/round/stoppage rules, sport and title applicability, professional-record/award/rank treatment, AI booking and save compatibility. **First slice:** a gap/evidence matrix against the current engine and supported rule settings. **Gate/tests:** approval of each rule set; fresh source-bound calibration, commentary/content/provenance/RNG and full shipping checks. Exhibitions need explicit isolated accounting and must not leak into professional history. Never enable experimental candidate contexts or copy another game's balance targets as production defaults.

#### D03 — Manual published rankings

**Design:** optional published-list version containing scope, date, ordered fighter IDs, reason and editor/user provenance, separate from calculated merit. **UI:** show override status and compare with the calculated list; restoring automatic ranking is explicit. **Gate:** decide who can edit, whether past published versions appear in future bout snapshots, and whether overrides have any commercial effect. They cannot bypass sporting eligibility or rewrite existing history. **Tests:** duplicate/missing fighters, division changes, tied positions, version rollback and old pre-bout snapshots; unknown legacy scope stays unknown. Do not add it merely to hide U08's labelling bug.

#### D04 — Owned broadcaster operation

**Design:** an ownership asset with purchase/capital costs, recurring operating costs, coverage/capacity, programming commitments, staff responsibility and closure/disposal terms. Current paid access/contracts are not ownership. **First slice:** financial model and one non-active hypothetical outlet screen using A3 assumptions. **Gate:** approve investment scale, audience/revenue sources, competition/exclusivity and AI participation after M2/M3 settle reliably. **Tests:** no double rights revenue, transfer/closure obligations, insolvency, repeated distribution and save identities. Do not relabel an existing broadcaster contract “owned” or grant unlimited free reach.

#### D05 — Reality competition

**Design:** season/episode/participant IDs, recruitment/eligibility, filming schedule, staff/production budgets, competitive format, participant compensation, eliminations and post-season contracts. Decide which bouts are professional/exhibition and who owns athlete rights. **First slice:** a paper playable loop and a disposable state-machine prototype after J8/A1/A2. **Gate:** format, funding, outcomes and professional-record semantics must be approved. **Tests:** withdrawal/replacement, injuries, expired contracts, saved season resumes and exactly-once elimination/payments. No forced winner, free fighter generation or covert fight-engine changes to achieve a television story.

#### D06 — Era/economic configuration

**Design:** versioned settings with declared units/scope for wages, production, demand and revenue, plus effective date and applicability to future versus signed agreements. **First slice:** baseline sensitivity report using A3/L0, not a blanket multiplier. **Gate:** approve which values change and why; preserve the real value/terms of existing contracts unless conversion is explicitly chosen. **Tests:** small/large company affordability, savings/debt treatment, legacy prices, inflation compounding and multiple simulated generations. Do not tune thresholds just to make super-events easily affordable or call a power score a dollar valuation.

#### D07 — Destructive pruning and forced company elimination — excluded

**Decision:** do not implement fighter/history deletion, arbitrary company survival caps or roster purges under this roadmap. **Alternative work:** J4/J8 archival indexes, bounded caches and L0 measurements. Preserve IDs, portrait vectors, professional facts, title lineage and ongoing obligations. **Acceptance for any storage optimisation:** complete logical-record comparison, checksum retention where required, full archive access, atomic save failure recovery and measured memory/load/refresh cost. A log/replay retention rule is not permission to remove compact career facts. Any later destructive archival policy requires a new explicit user decision and recovery design.

#### D08 — Multiplayer

**Design:** save authority, turn ownership, conflict handling, authentication if networked, deterministic execution boundary, secret scouting/offer information and shared history. **First slice:** architecture/authority document; do not add socket or cloud services to this desktop overhaul. **Gate:** user selects local hot-seat versus networked play and approves its security/compatibility requirements. **Tests:** conflicting bookings/spends, disconnected player, replayed command, stale turn and information leakage; a single authoritative settlement owner. No promise that the current synchronous single-player world can be made multiplayer through UI changes alone.

#### D09 — General scenario scripting

**Design:** bounded declarative triggers/conditions/actions with versioned schemas, permitted evidence, idempotent event keys and safe validation. Prefer catalogued actions over arbitrary Python execution. **First slice:** read-only editor validation of a small sample scenario using existing facts. **Gate:** agree supported action list, how scripts affect RNG/economy, error handling and save compatibility. **Tests:** cyclic triggers, repeat execution, invalid IDs, impossible conditions, malicious/unbounded input and partial failure. Never execute instructions copied from imported documents or allow a narrative trigger to force a winner or bypass sporting eligibility.

#### D10 — Concurrent regional/non-exclusive rights

**Design:** entitlement records specifying territory, platform, event class, period, exclusivity, guarantee and priority; a pure conflict/selection evaluator determines which accepted deals can coexist. Existing Non-exclusive labels do not establish this engine. **First slice:** conflict-preview matrix and no new active concurrency. **Gate:** settlement allocation, overlap precedence, subscriber/viewer deduplication and legacy single-contract alias treatment approved after M2. **Tests:** overlapping territories/dates, partial coverage, successor activation, cancelled events and one payment per entitlement. No summing all reach or guarantees indiscriminately.

#### D11 — Outlet audience segments

**Design:** small, explained audience categories with source/assumption labels, event/fighter suitability and bounded effects on already-defined demand components. Do not infer real-world demographics from fighter names or countries. **First slice:** descriptive account preferences using current terms, without new numeric modifiers. **Gate:** segment definitions, shares, calibration and visible uncertainty before enabling demand changes. **Tests:** shares/units reconcile, no duplicated audience across D10 deals, small/no-audience cases and pure previews. Keep total effect budgets bounded and verify that low-cost campaign choices remain useful.

#### D12 — Premium special-event media packages

**Design:** a one-event rights package with event/project ID, agreed coverage, production obligation, guarantee/bonus and cancellation terms. Reuse M2/A2 rather than creating another super-event settlement. **First slice:** preview an offer attached to an existing approved project; no separate random incident generation. **Gate:** conflict with ordinary rights, payment precedence and eligibility before acceptance is enabled. **Tests:** cancellation/reschedule, missing required card, normal rights overlap, refund accounting and reload. No extra fee solely because the same event appears in two UI sections.

#### D13 — Fighter ambassador agreements

**Design:** contracted fighter ID, partner ID, approved appearance types/count, term, compensation payer, exclusivity, injury/transfer/retirement treatment and evidence keys. **First slice:** draft/preview using existing sponsor campaign evidence; not a new free popularity action. **Gate:** athlete compensation, consent/availability, conflicts with employment and consequences of non-delivery. **Tests:** overlapping duties, unavailable spokesperson, departure, partial fulfilment and exactly-once payments. Never make an ambassador deal purchase sporting merit, hidden skill or an automatic title shot.

#### D14 — Scarce premium broadcast inventory and AI competition

**Design:** explicit slot inventory by period/outlet/event type, reservation/expiry rules, transparent selection criteria and bounded AI spending. Scarcity must exist as a real shared resource, not arbitrary rejection text. **First slice:** simulated market model after D10/D12 with retained seeds and no active player effect. **Gate:** allocation policy, tie handling, bid/counter limits, affordability and fairness approved/calibrated. **Tests:** simultaneous offers, expired reservations, duplicate acceptance, AI insolvency and save/resume. No offer reroll on refresh or hidden unlimited AI budget.

### Complete coverage register

Use this register during every future handoff. A point is complete only when its implementation card and shared acceptance contract are satisfied; a cross-reference is not proof of completion. All statuses start **PLANNED** in this report.

| Original report point | Implementation owner/card | Notes preventing omission or duplicate work |
|---|---|---|
| Confirmed issues 1–16 | U01–U16, one-to-one | Each has its own reproduction and focused regression. |
| Dashboard; Game & Saves; Matchmaking | V01; V02; V03 | U01 remains the separate geometry repair. |
| Profile/Core Skills; Fight History; Development | V04; V05; V06 | U14 fixes live injury display; J4 owns historical facts. |
| Finance/Sponsors; Media/Rights; Staff; Contracts | V07; V08; V09; V10 | Visual slices consume domain helpers, not new formulas. |
| Scouting/Search/Free Agents; Regional Prospects | V11; V12 | Hidden ratings, selection and counts remain protected. |
| World/Companies/Regions; Rankings; Combat Sports | V13; V14; V15 | Native sport and ranking scopes remain distinct. |
| Academy; sidebar Fight Night | V16; V17 | Preserve the working Academy; link rather than duplicate live/replay state. |
| Camp Plan resizing; Scouting debounce | V18; V19 | Explicitly included beyond the main page table. |
| Media finding 1: generic campaign targeting | M1, with J2 timing integration | New target effects gated from organisational plan UI. |
| Media finding 2: false risk percentage | U06, then M1 | Derive actual bands or use truthful non-probability wording. |
| Media findings 3/4: production and relationship contradiction | M2-I/M2 | Distinguish display truth from new enforcement. |
| Media findings 5/6: expiry and guarantee alias | M2-I/M2 | Preserve agreed legacy terms; successor is not replacement. |
| Media finding 7: sponsor duty timing | M3 | No retroactive or stacked undisclosed penalty. |
| Staff findings 1/2: wrong lead and marginal extra hire | S1/V09 | Shared effective-quality rule; no passive stacking. |
| Staff finding 3: specialty/progression shallowness | S3 | Evidence-based development; narrative legacy is not XP. |
| Staff finding 4: AI employee loss/non-persistence | S4 | Full employment/payroll/expiry, not only a headline. |
| Staff finding 5: Trainer fallback | J6, referenced by S4 | Exactly one coaching implementation owner. |
| Staff finding 6: random positives as injury | J5, referenced by S4 | Rules HOLD before automatic testing. |
| M1/M2/M3; S1/S2/S3/S4 proposed features | Matching named cards | Every objective, department and lifecycle covered above. |
| J1/J2/J3/J4 | Matching named cards | Booking, preparation, contracts, history. |
| J5/J6/J7/J8 | Matching named cards | Discipline, coaching, corporate proposals, tournaments. |
| J9/J10/J11/J12 | Matching named cards | Regions, help/comparison, advancement, editor. |
| A1/A2/A3/A4 | Matching named cards | Owned calendar, project closeout, runway, owner outcomes. |
| A5/A6/A7 | Matching named cards | Relationships, recruitment, followed stories. |
| 100-year/world-health requirement | L0 | Existing audit capability retained; current evidence required. |
| Earlier Media expansions | D04, D10–D14 | Ownership, concurrency, segments, specials, ambassadors and scarce slots all covered. |
| Daily calendar; new engine/rules; manual rankings | D01; D02; D03 | Separate decision gates and data contracts. |
| Reality competitions; era economics | D05; D06 | Not part of first management release. |
| Destructive pruning / forced caps | D07 | Deliberately excluded, with a non-destructive alternative. |
| Multiplayer; scenario scripting | D08; D09 | Architecture and authority first. |
| Save, finance, RNG, scouting, UI and native safeguards | Shared completion/data/UI/test contracts plus F0/L0 | Apply to every card; not optional separate chores. |

### Dependency order and unattended execution rules

**READY** means a task's bounded repair/presentation slice can be implemented after checking its current source. **DEPENDENCY** means it needs named preceding work. **HOLD** means a gameplay/migration policy is intentionally unresolved; do not invent it to keep running. A feature can have a READY observational slice and a HOLD active-mechanics slice.

1. **G0 repair batches:** U05/U06/U11/U12 (commercial decisions); U04/U08/U14 (profile/ranking truth); U09/U10 (finance/staff labels); U01–U03/U15/U16 (workflow/Fight Night); U07 (theme foundation). Add J4's historical fallback, M2-I, S1's actual-lead repair, A2's reproductions and A4's refresh-purity reproduction. These are separate bounded tasks, not a licence to change their new-rule slices.
2. **G1 shared state:** F0, agreed historical/event references for J4/A1/J8, quote/receipt ownership and migration tests. Resolve common data contracts before two features create incompatible IDs, counters or ledgers.
3. **G2 first playable interface:** V01–V19 in their prerequisite order; M1 organisational plan, S1 pilot briefs, J1 draft review, J3 batch review, J10 help and A1 read-only calendar. Enable S2 only for individually approved action types. A4's versioned objectives require its explicitly selected semantics.
4. **G3 commercial lifecycle:** approved M1 targeting, M2/M3, A2 closeout and A3 forecasts. Pass finance/identity boundaries before adding new obligations. A5/A6/A7 can ship as separately scoped interface extensions when their source records are stable.
5. **G4 staff/AI:** S4 durable employment with an approved cost policy, then S3 effects/progression only after work evidence and balance decisions. Run relevant long-run qualification.
6. **G5 optional mechanics:** J5/J6, new J7 treaties, multi-event J8, invitations in J9, controlled MMA children in A1, J11 resume/checkpoints and J12 conversion after their specific gates. D-cards remain deferred unless explicitly selected.

When the user authorises a batch, Luna should maintain a short task ledger in its implementation handoff: task ID, scope slice, status, dependencies, changed files, tests and blockers. It may continue another authorised READY task if one is blocked. It must not claim a blocked mechanical slice is done because its UI exists, broaden the batch, reset test fixtures, weaken acceptance gates, silently rebuild or overwrite a user save.

**Shared-file rule:** tasks in this report frequently touch `views.py`, `world.py`, `events.py`, `media.py` and `persistence.py`. Complete/review one domain slice before starting another overlapping rewrite. Do not use parallel agents unless the user separately asks for them and file ownership is made explicit.

**Pause/report immediately for:** unexpected save corruption; current source diverging from a native certificate; an unresolved historical identity/fee conflict; a required new gameplay policy; a failed baseline that prevents attribution; or an unsafe external/destructive action. Keep evidence and continue only independent authorised work. No sweeping cleanup/reset and no certificate exceptions to conceal a failure.

### Per-task completion record for Luna

Use this compact structure after each commissioned card; fill real results, never predictions:

```text
Task ID and approved slice:
Baseline finding / current source confirmation:
Implementation summary and files:
Data/schema/legacy behaviour:
Gameplay/RNG impact (or proven unchanged scope):
Regression command(s), exit status and assertions added:
UI evidence and measured geometry/theme checks, if applicable:
Save/identity/finance/native checks required and completed:
Known limitations / HOLD decisions:
Status: COMPLETE / PARTIAL / BLOCKED
Next authorised dependency-ready task:
EXE rebuilt: No, unless separately authorised and verified
```

**The detailed handoff remains the governing plan for unimplemented work.** The implementation ledger below records staged changes made after the plan was commissioned. Proposed mechanics remain gated by the explicit user decisions and release tests; no simulation, save migration or EXE build is implied by a completed repair/presentation stage.

## Revision 2 design decisions and execution queue

### R00 — What this pass corrected and how to use it

The earlier pass covered 77 cards, but coverage alone did not establish implementation readiness. This review found unresolved policy choices in active gameplay, whole-card dependencies that could form cycles, over-large tasks combining UI with mechanics, and no precise order for completing shared foundations. This section is being revised through user consultation; the final execution queue and consistency pass remain outstanding.

**Design-ready does not mean balance-validated or implemented.** Only statements explicitly labelled as user decisions are confirmed. Other first-version rules below are unapproved recommendations, including numerical tuning and exclusions; they must not silently become approved defaults in an unattended implementation task. New mechanics still need the applicable source-bound evidence before release. A test failure triggers diagnosis, not permission to change these rules until the tests pass.

Proposed task suffixes mean **`.a` = repair, pure adapter or first working workflow using existing effects; `.b` = additional mechanics/persistence extension.** Do not assume every card has both. The final queue must enumerate existing slices and prerequisites before unattended handoff. D-cards remain separately scoped, and D07 remains excluded. There is no implementation authority during this documentation task.

The detailed card supplies purpose, owners, tests and exclusions. Its R-rule supplies confirmed decisions where explicitly labelled and otherwise proposed refinements. An unresolved HOLD is not waived by an unapproved recommendation. Reconcile remaining contradictions and complete the ordered queue after consultation.

### R01 — Foundation slices, identifiers and failure behaviour

Split F0 into **F0.a identity/read models** and **F0.b quotes/work/receipts**. Neither depends on Media, Staff, child scheduling or UI redesign. This removes the S1↔M1/J1 and J4↔J7/A1 dependency loops: these systems depend on shared interfaces, not each other's completed pages.

F0.a assigns missing promotion/MMA-event/work IDs using saved, monotonically increasing namespace counters. On legacy load, walk the existing persisted collection order exactly once, retain an explicit old-reference map and leave ambiguous references unresolved. Repeated migration retains assigned IDs and counters. Existing fighter/staff/sport-event IDs are untouched. Do not derive new IDs from a name, array index exposed to the user, UUID randomness or Python object identity.

F0.b uses separate domain collections with a common envelope, not a single global job engine. Commit flow is: read quote → verify target/revision/permission → validate complete state delta and current funds → apply through domain owner → record ledger/evidence/status under one operation key → save through the existing atomic save owner. A re-entry with the same key returns the existing receipt. No resume path may apply only half of a previously saved financial result.

For multi-row actions, use explicitly reviewable **partial completion**, not pretend rollback of negotiations already observed. Record each attempted row before continuing; restart resumes unattempted rows only. For a single business transaction, failure must leave either the full result or the original state, including relevant RNG. Use scoped snapshots of affected state rather than broad globals; prove shared-identity restoration on injected failure.

Historical retained facts remain in versioned save-owned collections for v1, with bounded in-memory indexes and paginated readers. **No external archive sidecar in v1:** portable saves must remain self-contained. Measure save growth; designing a future sidecar is not permission to trim compact facts. Do not reconstitute already-lost old data.

### R02 — UI, repairs and source-evidence decisions

U01–U16 and V01–V19 retain their precise card scopes. The stated geometry/contrast targets are acceptance requirements, not discretionary suggestions. U07 comes before page styling. U01/U02/U03/U15/U16 may implement structure/logic first but their final review uses U07 tokens. Add no new art generation, toolkit or screen-wide animation.

U10 v1 is **Offer strength**, not probability. U06 v1 removes the false backfire percentage; an exact later percentage may enumerate the existing 45 integer roll outcomes, accounting for every score term, without RNG. No approximate “risk %” from the unused spec field. U05 v1 blocks new signings at eight and preserves existing over-cap portfolios; replacement negotiations are out of scope.

A “pure” preview must not call `calculate_event_media_outcome(..., apply=False)` unchanged: the inspected implementation still normalises state and draws `random.uniform`. Extract read-only deterministic components and show uncertainty/assumptions. Similarly, ensure/remaining-capacity helpers must not reset counters on repaint. Explicit repeated-state/RNG assertions are mandatory.

Every visual task includes the originally listed empty/blocked/stale/scouting states. If a recorded row lacks identity or history, display the limitation; no guessed details, hidden sort keys or inactive feature buttons made to look functional.

### R03 — M1 managed campaigns: exact first-version effects

M1.a is an optional single primary plan with manual execution of existing actions and recorded targets. Its UI must say that it organises existing actions while the legacy generic audience-lift rule remains active. M1.b enables a versioned target-aware lift calculation for newly executed managed actions only; existing campaign outcomes, costs/AP, cooldowns, popularity cap, heat and trust changes remain unchanged.

Each new completed action has exactly one audience attribution mode: event, prospect, sponsor, region or trust. Event mode contributes only to its event ID (factor 1); prospect mode contributes when that fighter actually appears (0.5); sponsor mode contributes when its spokesperson appears on that event (0.5), while duty evidence separately uses the signed rules; region mode contributes only in its recorded region (0.75); trust mode has no extra event audience lift (0). Negative heat uses the same matching factor—targeting must not discard backlash.

For versioned actions, age 0–3 completed weeks has time factor 1, age 4–7 has 0.5, and older actions contribute zero. Build one stable newest-first eligible list, using completion sequence to break date ties; consider at most eight rows and calculate `clamp(sum(heat × match_factor × time_factor) / 8, -8, 14)`. Legacy rows retain their current/current-previous-month eligibility and generic factor; deduplicate action IDs and apply the combined cap once. Do not stack a second legacy lift on top. Store which rows contributed in the event receipt.

No added skill gain, prospect multiplier, free AP or new objective-specific trust bonus. “Repeated exposure diminishes” in v1 means the existing cooldown/cap plus the explicit audience time decay, not an undisclosed extra formula. Reassignment affects unperformed work only; completed action targets never change. Cancellation leaves spent campaign costs sunk and unused plan budget unspent. Manual retarget creates a new plan revision for future actions.

Acceptance examples: matching heat 16 at age 2 contributes 2 before other rows/cap; the same event-targeted action contributes zero to another event; age 5 halves that contribution; cancelled target never transfers past lift to a replacement event. These are design examples, not measured outcome improvements. Multi-seed audience/economy comparison is a release gate for `.b`.

### R04 — M2 rights: quality, compliance, aliases and renewal

M2.a fixes representations and provides a complete account view. For a legacy fee conflict, retain both original fields and snapshot **the amount the existing payment path actually reads** (`fee` when present, otherwise `guarantee_per_event`) as the compatibility payment basis. Label the discrepancy; do not average, maximise, lower, back-charge or rewrite old receipts. New accepted/countered versioned terms write one canonical amount and synchronise both compatibility aliases.

M2.b defines production quality by the selected MMA production tier: Lean 20, Standard 45, Premium 65, Spectacle 85 on a 0–100 contractual scale. This is a disclosed contractual classification, not a derived probability or cost amount. No Coverage fails coverage eligibility regardless of tier. Legacy saved events with no tier retain their documented Standard default. For other sport tiers, v1 displays “not supported by this rights workflow” rather than guessing a conversion.

For new versioned agreements, insufficient production means **delivery fails**, not retroactive denial of an otherwise earned coverage guarantee. The existing performance bonus is withheld and the existing breach-strike mechanism applies once; no additional fine. Keep existing rating/card tests. Delivered events receive existing success relationship adjustments; an eligible but undelivered event receives -5, even if ratings were high. Preserve audience appreciation as a separate explanatory fact, not a second relationship currency. Legacy numeric treatment stays on its compatibility version until renewal.

Renewal opens when months remaining ≤2 OR event entitlements remaining ≤2. One open successor offer and one committed successor are permitted, with the existing single-counter rule. No new negotiation fee. A successor starts at the first calendar boundary after the predecessor terminates normally or fulfils its quota; do not stack the same event under both. A breach-terminated predecessor does not auto-activate the successor: mark it Needs review and obtain a new valid commitment. End states are Fulfilled, Expired with shortfall and Terminated; no new historical debt.

New v1 obligations are only the existing eligible-show count plus published rating/card/production conditions. Bespoke headliner commitments, make-goods and extra penalties are not part of M2.b. This closes the earlier open choices without creating another obligation engine. Test exact tier thresholds, alias conflicts, quota-before-term, term-before-quota and successor activation/rejection.

### R05 — M3 duties and commercial receipt boundaries

M3.a shows the existing eight-slot portfolio and duty checklist. M3.b stores complete per-event receipts and monthly review evidence; **it adds no new monetary missed-month sanction**. Placement fulfils automatically. An event/campaign duty remains Pending until its period ends, then records Met or Missed; only already-agreed activation/payment rules affect money.

Snapshot trust/stability, current roster identity and qualifying campaign facts at settlement, then apply the existing full/half-fee calculation once. A receipt separates maximum fee, actual fee, evidence and reason; a later change in rank, trust or employment cannot revise that receipt. Multiple events use distinct event entitlement keys. An appearance cannot be counted twice toward a count-based duty, but can serve different explicitly compatible agreements without duplicating any payment.

Termination/replacement remains the existing explicit contract action, not an automatic “make room” mechanism. No future annual-income estimate without a stated event-count scenario. Signed terms and actual payments survive portfolio/UI limits.

### R06 — S1/S2 departments and player-selected autonomy

**User decision — 12 September 2026:** autonomy belongs to the player. Support Manual, Recommendations, Selective Recommendations and Full Auto. Do not impose the previous media-only delegation ceiling as the finished feature.

| Mode | Intended behaviour | Authority |
|---|---|---|
| Manual | Player initiates actions; on-demand information and mandatory warnings remain accessible. | No new background staff execution. |
| Recommendations | Staff prepare actionable advice with reasons, costs and expected effects. | Player approves each action; advice itself spends nothing. |
| Selective Recommendations | Advice only for the action IDs explicitly selected on the brief; unsupported or mutating selections are surfaced as Needs attention. | No execution without approval. |
| Full Auto | Staff execute supported responsibilities under the player's configured policy and report results. | Explicit department/action scope and spending limits; not unlimited funds or permission to bypass game rules. |

**Implementation design, subject to remaining choices:** expose a company-level mode with department overrides and a clear effective-mode summary. Keep legacy Scout/auto-renew controls visible and reconcile them explicitly; do not expand them during migration. A mode change affects uncommitted work only. Turning automation off cancels queued execution authority without undoing paid work or deleting recommendations/history.

S1.a unifies effective lead attribution using current morale-adjusted quality and stable roster-order ties. S1.b supplies shared work records independently of feature pages. Department capacity and cadence must use each domain's existing limits; the earlier proposed universal one-action-per-week limit is not a user decision. Additional staff must not create unexplained passive stacking or extra attempts.

For every department, define an explicit capability matrix: advice available, actions automatable, required handler, costs/capacity, target restrictions, stop conditions and completion evidence. Marketing, matchmaking, talent/contracts, scouting, production and compliance must each be assessed. Stage implementation by supported handlers; do not call a partially automated department fully implemented. Medical clearance and sporting eligibility remain authoritative regardless of autonomy; title weight-miss decisions use the player prompt in R10.

Each execution revalidates a pure quote, permitted targets, per-action/monthly caps, cash reserve and shared capacity. Log action/attempt IDs and actual results once. An ordinary refresh must not recommend through new simulation draws, spend, regenerate offers or retry a failed negotiation. Full Auto may undertake later genuinely new allowed work, but may not reroll a completed failed attempt. Changed terms, missing staff, expired permissions or unaffordable actions require an exception rather than silent substitution.

Testing automation is supported only after J5 has provider, policy, case and financial handlers, and only when separately enabled by the player. Choosing Full Auto for Marketing does not permit testing or dismissal. Routine completed work appears in a digest; actionable exceptions remain accessible. Existing savings, histories and disabled-path RNG behaviour remain protected.

**Remaining consultation:** confirm the default new-game mode, department overrides and whether any additional high-impact actions must always request approval even within Full Auto. The approved champion-miss prompt remains mandatory unless the user separately approves a standing-policy alternative. The Selective Recommendations semantics are now fixed: only explicitly selected brief actions are reviewed, and mutating actions are rejected in recommendation modes.

**Acceptance additions:** test all four modes, per-department scope, manual/full-auto shared capacity, toggles with queued and completed work, zero-authority migrations, stale quotes, partial failure/reload, mixed legacy automation and full activity-log reconciliation. Tests must show that advice never counts as execution or staff progression.

### R07 — S3 specialties/progression and S4 AI careers

S4.a repairs the missing employment transition without inventing prior employees. S4.b enables prospective ongoing payroll for versioned new AI hires. Limit new AI hiring to one employee per role and one hire per promotion per month; preserve legacy excess staff, but do not add more to occupied roles. After the existing hiring fee, require cash to cover six months of projected existing recurring operating costs plus the proposed employee salary. Reject unaffordable hires without removing the candidate. Use the current candidate/acceptance logic and draw order, adding no refresh-time recruitment. Expiry releases staff to market; automatic replacement is a later normal hiring attempt, not a free immediate hire. Existing AI passive effects remain unchanged in this version.

S3.a catalogues/explains specialties and tracks real completed work. S3.b supports three authored non-Scout specialties only: **Campaign Coordinator** reduces eligible paid media campaign cost by 2%; **Contract Administrator** reduces an existing staff negotiation administration fee by 2%, never salary/purse; **Production Coordinator** reduces eligible production staging cost by 2%, excluding security, guarantees, athlete pay and medical/testing. Use one effective department lead, apply after existing eligible modifiers, round once to integer dollars, and cap the new saving at 2% of that eligible pre-specialty subtotal. Assign the matching role; all other legacy specialties remain explicitly descriptive. A free action stays free and earns no credit solely from the specialty.

Non-Scout progression is deterministic: within each three-month game quarter, three successfully completed, genuinely capacity-consuming/paid domain actions in three distinct months and for at least two distinct targets qualify for +1 skill at quarter close. Maximum +4 per game year; no gains above 80 through this system, and never lower an existing higher value. Failed/cancelled work, quotes, reviews, signings without actual employment and narrative milestones do not qualify. Record credited action IDs. No extra reputation, morale or negotiation-heat mutation in v1.

Retention v1 gives evidence-backed warnings and manual existing renewal/release choices only; no new random resignations, satisfaction score or automatic heat cooling. This resolves the earlier retention scope. `.b` effects/payroll/growth require the relevant finance, long-run and source-bound checks before release; the stated numbers are trial design defaults, not proven balance.

### R08 — J1/J2/J3 planning and execution boundaries

**J1:** v1 adds Explain/Suggest/Fill unlocked slots/Review draft while preserving existing candidate eligibility and underlying default scoring. A saved brief filters or prioritises only eligible candidates. Proposals requiring stochastic choices run once from an explicit Generate action; refresh merely displays them. A tentative medical slot is **a non-binding draft**: no camp assignment, title promise, cash reservation or firm booking. Show existing earliest return and camp requirements; confirm through normal medical checks no later than the start of the event week. An unresolved draft expires to Needs replacement and cannot execute. There is no new medical-clearance bypass or projected recovery guarantee.

**J2:** v1 does not move press/weigh-in resolution earlier. Campaign planning occurs in advance; official preparation runs at the existing event-preparation boundary and stores its outputs once. The screen separates Planned from Officially resolved. Changing an uncommitted draft is allowed; resolved official evidence is not rewritten. Earlier stochastic resolution is outside v1, not a missing decision for Luna to make.

**J3:** batch review uses partial completion, in existing stable priority order. Each row has its own immutable quote/attempt/result. If funds fall below the reserve, stop unattempted rows as Needs review; do not undo a completed negotiation or reroll a failure. Manual batch confirmation is still required. Expanded automatic fighter renewals, new salary escalators, loyalty penalties and card-placement morale changes are excluded from v1. Existing auto-renew preserves its scope.

### R09 — J4/J8 durable history and tournaments

J4.a removes current-record fallback and adds truthful scope/coverage labels. J4.b adds future membership facts and compact bout indexes through F0.a; it does not depend on J7's new proposal UI. Hook existing actual transitions first, then future proposals call the same owner. Retain all compact facts in portable saves; missing pre-migration periods show incomplete coverage. Stored frame/display preferences cannot delete facts.

J8.a indexes completed one-night editions, saved draw/seeds, entrants/substitutions and original result references, independent of replay retention. Never fabricate an edition/round from ambiguous names. J8.b v1 improves the existing one-night entry/alternate review only. **Multi-event Grand Prix is a separately selected format:** eight adults, three rounds initially four weeks apart, ordinary medical/contract clearance at each stage, no forced acceleration; allow one stage postponement of up to four weeks, then withdraw an uncleared entrant. Use a reserve only before that entrant's first bout; later withdrawals give the opponent a tournament walkover, not a professional win. An unresolved draw/NC uses the higher pre-recorded tournament seed for bracket advancement only, explicitly labelled and never rewriting the bout result. No ad-hoc extra bout or result reroll. Do not enable this format without its dedicated fixture/calibration work.

### R10 — J5: player title decisions and a full configurable testing system

**User decisions — 12 September 2026:**
- When a champion misses weight, prompt the player and let them decide. The confirmed menu is **Remove Belt**, **Rebook Fight**, **Keep Belt**, **Cancel Fight**, and **Last-Minute Replacement**. The user explicitly confirmed that **Keep Belt means the title remains on the line**. Last-Minute Replacement must offer ready fighters of the same weight class in a dropdown showing their ranking positions.
- Build the full drug-testing system, with player-customisable strictness and a choice of testing company; more effective companies cost more.

These replace the earlier automatic champion stripping, automatically sustained findings, fixed eight-/sixteen-week sanctions and blanket prohibition on testing automation. Those earlier proposals are withdrawn, not approved defaults.

#### Title decision workflow

At the official weigh-in, create a durable pending decision containing event/bout/belt IDs, recorded weight evidence, each corner's status and the scheduled title terms. Show the champion and challenger prominently, then explain each available decision's consequences for belt ownership, eligibility to win, defence credit and whether the bout proceeds.

Do not strip a title or continue the affected fight while the required player decision is unresolved. Save/reload must restore the same prompt without another weigh-in roll. Simulate/Go must stop at a safe persisted pre-fight boundary for this decision, not run the fight first and ask afterwards. This may require a narrower event-preparation interruption boundary than J11's ordinary completed-week stop; implement resumable preparation before enabling the prompt in long simulation.

**Confirmed choices — user decisions, 12 September 2026:** show **Remove Belt**, **Rebook Fight**, **Keep Belt**, **Cancel Fight**, and **Last-Minute Replacement**. Keep Belt means the title is still contested; it does not need a separate title-defence option. Choosing an option must show its consequences before commitment; unresolved consequences below remain explicit consultation items.

| Choice | Confirmed meaning | Implementation design and unresolved consequence |
|---|---|---|
| Remove Belt | Strip the champion of this belt because of the weight miss. | Record one vacancy with the fighter, date, decision and reason through the existing title-history owner. Confirm whether a challenger who made weight may still win the vacant belt in the scheduled bout; do not infer this from stripping alone. |
| Rebook Fight | Move the matchup to a later booking rather than execute it on the current card. | Proposed workflow: open a rescheduling draft for the same fighters, validate dates, availability, camps and costs, and commit through the booking owner. Do not invent a new date, result or additional payment. Proposed belt handling is to retain the holder pending the rebooked fight; this consequence still needs confirmation. |
| Keep Belt | **User-confirmed:** the title remains on the line despite the champion's weight miss. | Preserve the scheduled title contest and apply ordinary championship settlement: a champion win retains the belt with normal defence credit; an otherwise eligible challenger win transfers the belt; draw/NC uses existing title-retention and defence-count rules. Do not vacate at weigh-in or downgrade the bout to non-title because of this champion weight miss. |
| Cancel Fight | **User-confirmed:** cancel this bout rather than proceed or rebook it. | Close only the affected booking and its unperformed work; preserve the scheduled matchup, weigh-in evidence and cancellation reason. Do not generate a result, defence credit or replacement booking. Proposed belt handling is to retain the holder because stripping is a separate choice; confirm this consequence before enabling settlement. |
| Last-Minute Replacement | **User-confirmed:** offer ready fighters in the same weight class in a dropdown with their ranking positions. | Stage a replacement for the affected corner, show the updated matchup and costs, revalidate eligibility, and commit through the existing booking/preparation owners. Replacement alone must not silently strip a champion, invent a vacant title or bypass title merit. |

#### Last-Minute Replacement — ranked candidate picker

**Ownership/order:** J5 owns the player decision and title sanction; J1 supplies a shared pure candidate/eligibility adapter; J2 owns invalidating and resolving only the changed preparation stages. F0 supplies stable booking/fighter/attempt references. Build these adapters and resumable preparation before enabling this option. Do not create a second matchmaking or title-settlement engine inside the dropdown.

**Candidate eligibility:** query fighters of the same stored weight class and compatible competition category who can legally be booked for this promotion and event date. Apply current contract/roster/loan permissions, medical and disciplinary clearance, suspension, camp/readiness and schedule-conflict rules. Exclude the remaining opponent, the withdrawn fighter, fighters already used on the card and conflicting bookings. Use existing sanctioned short-notice eligibility if supported; do not waive minimum preparation requirements merely to fill the dropdown. If no such pathway exists, record that implementation dependency rather than label an unready fighter Ready. No free-agent signing, cross-company transfer, weight-class change or extra clearance is implied by selection.

**Title eligibility is separate from readiness:** apply challenger merit before title scoring, including the existing two-win/wins-at-least-losses or three-win comeback rule, three-meeting cooldown and champion protection. For a confirmed title contest, offer only title-eligible replacements. A ready fighter who fails title merit cannot become eligible through this emergency flow. Do not assume the contest becomes non-title to admit them. If the failed-weight champion is replaced, show the resulting belt question explicitly; replacement does not grant stripping authority, and title disposition must be resolved before the fight proceeds. The combined replacement/title policy remains a consultation item.

**Dropdown presentation:** use a searchable, keyboard-accessible dropdown with readable candidate rows. Every selectable row displays fighter name, **Company Division Rank** and **World Division Rank**, for example an illustrative `Fighter Name — Company #3 · World #24`. Show `C` or `IC` with a champion/interim label where applicable, distinguish Unranked from Unknown/Unavailable, and never substitute pound-for-pound position for a division ranking. Company rank belongs to the event promotion; a fighter with no position there must not borrow another company's rank. Use stable fighter IDs rather than labels or list positions so duplicate names remain safe. Search/pagination must retain access to every qualifying candidate.

**Selected-candidate preview:** show the replacement and retained opponent with portraits, record, weight class, dated ranking badges, readiness/clearance and title-eligibility explanation. Use the profile visual theme and legitimate scouting visibility; do not reveal hidden overall or detailed ability. Show replacement cost/terms and any known effects on camps, card obligations and previous spending, using actual quotes rather than invented fees. Proposed default ordering is company division rank, then world division rank, with unranked entries last and stable ID tie-breaking; this is presentation order, not an automatic selection or recommendation of hidden ability.

**Interaction:** opening/searching/selecting only previews; it does not spend, book, consume RNG, rerun weigh-ins or remove the original fighter. Confirm revalidates the candidate, quote, event state and title terms. A stale candidate yields a reason and refreshed choice, never a silent substitute. Back closes the picker and returns to the pending decision unchanged. With zero eligible candidates, explain why and retain Rebook Fight and Cancel Fight; do not manufacture an eligible fighter.

**Commit and history:** replace only the intended unresolved slot through its domain owner and retain original booking, withdrawn fighter, weight evidence, replacement identity, decision date, accepted terms and reason. Do not execute a completed bout again or rewrite completed preparation for the unaffected corner. Resolve required replacement-specific clearance/weigh-in once through J2 before fight execution. Snapshot both actual competitors' company/world rankings at the authoritative pre-bout boundary for J4/Fight History; the removed fighter's former ranking remains original-booking evidence, never the replacement's pre-fight rank. A later rank change or rename must not rewrite these snapshots.

**Tests/done:** same-class eligibility and incompatible-category rejection; medical/disciplinary/camp/contract failures; existing-card/conflicting bookings; champion protection and title merit; duplicate names; ranked/unranked/unknown positions; company versus world versus P4P scope; scouting mode; empty/large candidate sets; keyboard access and small-window layout; stale quote/availability; cancellation without mutation; save/reload before and after confirmation; exactly-once payment and replacement weigh-in; unchanged unaffected preparation; full watch/simulate parity and immutable pre-bout ranks. Run booking/card inactivity regressions, T-World/T-Identity/T-UI/T-Finance and relevant preparation/profile/persistence tests. No EXE rebuild is authorised by this planning addition.

#### Shared title-decision completion rules

For Rebook Fight, cancelling the rescheduling editor returns to the unresolved decision; it must not accidentally execute the original bout or partially move it. A successful rebooking retains an explicit link from the original scheduled slot to the new booking, preserves the original weigh-in evidence, and performs a new official weigh-in only at the rescheduled event. Review affected camps, remaining card, title obligations and already-paid costs without deleting evidence or resetting unrelated event preparation. Moving the fight must not award a win, loss, defence or vacancy by itself. No valid new booking means an unresolved decision with an explanation, not an eligibility bypass.

**Cancel Fight implementation and acceptance:** distinguish cancelling this bout from cancelling the whole event and from dismissing the decision dialog. Show affected card slots, title/contract obligations and evidenced paid, refundable or unpaid costs before confirmation. Use the existing booking/cancellation owners and accepted terms; do not invent an automatic fine, purse payment or refund. Invalidate only this bout's unperformed preparation/camp/work links, retaining historical evidence and unrelated card state. A confirmed cancellation seals once and cannot execute after resume or simulate; repeated clicks and reloads cannot duplicate financial adjustments. If the remaining card cannot run, surface its normal validation/review path rather than silently cancelling the event or inserting another fighter. Tests cover confirmation/dismissal, paid costs, missing terms, last bout on the card, tournament-linked bouts, save/reload and no phantom professional result or title defence. Any tournament advancement follows its separately approved withdrawal rules, not an invented fight win.

**Keep Belt implementation and acceptance:** persist the player's explicit title-on-the-line decision in the pre-bout sanction snapshot, linked to the recorded champion weight miss. Preparation/resume and settlement must read that same snapshot rather than reapplying the old automatic non-title downgrade. The weigh-in evidence remains unchanged; accepting the title contest does not falsely record that the champion made weight. Test champion win, eligible challenger win, draw and NC; confirm exactly one ordinary title settlement, correct defence counts, no weight-miss vacancy, correct history badges, and identical behaviour after save/reload or watch/simulate. A later actual roster departure still follows the normal vacancy rule.

The decision screen must ultimately have a tested outcome table for every supported choice and corner/weight/belt combination. Keep ordinary medical and sporting eligibility authoritative; the player choice only grants the specific title/booking treatment that is approved, not a general override. The confirmed Keep Belt rule waives the champion-miss title downgrade only; treatment of a challenger who also misses remains a separate unresolved case.

Persist the chosen policy and per-corner eligibility before resolution. If the chosen option vacates the title, call the existing vacancy owner before changing champion flags and record the reason. A later crowning is a transition, not a second vacancy. Draw/NC, replacement, both-miss, vacant, interim/special-belt and tournament handling must be explicit. Completed legacy results and lineage remain unchanged.

**Open scope:** whether prompts cover only player-controlled promotions or also AI/spectator events; whether non-champion misses also prompt; and the deterministic AI policy. Do not pause a whole spectator universe for every AI case without this decision. Staff Full Auto does not silently answer the approved player prompt.

#### Drug-testing playable loop

**Required design direction:** configure policy → compare providers → review coverage and quote → commission tests manually or through authorised staff → collect/process samples → preliminary result → confirmation where required → notice/provisional restriction → review/appeal → final outcome and sanction → expiry/clearance. Support negative, inconclusive, invalid and overturned findings, not only sustained violations. A preliminary finding is not a proven violation and is never stored as an injury.

**Provider catalogue:** stable provider ID, description, supported tests, coverage/capacity, screening effectiveness, confirmation reliability, false-positive handling, turnaround and itemised collection/testing/confirmation/appeal costs. More effective service must have an explained higher cost for comparable scope. Show the differences before commitment; do not simply multiply an unconditional positive roll or claim an expensive provider guarantees a positive result. Names are fictional/authored unless separately requested otherwise. Exact provider count, values and prices remain design proposals pending a complete balance table.

**Evidence model:** separate prospective underlying simulated prohibited-use/evidence state from what a provider observes, and distinguish true detection from an erroneous or inconclusive finding. Persist sample evidence and attempt IDs so confirmation/appeals inspect the same case rather than generating a fresh offence or rerolling the world. Explain that this is fictional game modelling, not real toxicology. Keep restricted evidence out of player-facing/scouting views until legitimately known. Never infer past violations from old injuries, traits, nationality, messages or officer quality.

**Strictness controls:** design visible settings for test coverage/frequency, selection scope, confirmation requirements, provisional restrictions, first/repeat sanctions and appeal process. Provide a summary of current rules, anticipated itemised cost and booking consequences before acceptance. User approval of customisation does not yet fix permissible ranges, presets or who has jurisdiction; resolve these before coding active effects. Provider effectiveness, prevalence and sanction strictness are separate quantities. Stronger staff may improve an explicitly supported process/cost component, not create more underlying violations.

**Case persistence:** store fighter/event/test/provider IDs; accepted price and policy versions; sample collection and due dates; preliminary/confirmed evidence; notices; review/appeal deadlines; decisions and reasons; paid/refundable/outstanding amounts; independent medical and disciplinary restrictions. Subsequent policy/provider changes apply prospectively and cannot clear an existing case or replace its frozen rules. Repeated page opens, calendar processing and reloads cannot produce another sample, charge or sanction.

**Player experience:** policy/settings panel, provider comparison cards, coverage/quote preview, due-work calendar, case cards with a clear timeline, evidence/details and decision buttons, plus separate spending and suspension summaries. Surface affected future bookings with reasons. Avoid repeated modal notices for routine negative results; unresolved actionable decisions must remain visible. Staff autonomy controls who commissions/processes permitted work, not whether confirmed evidence is fabricated or erased.

**Costs and outcomes:** distinguish collection, screening, confirmation and appeal charges, with explicit payer and cancellation/refund terms. Define athlete appeal behaviour and resolution against persisted evidence; no paid guaranteed clearance or infinitely repeatable appeal rolls. Suspension expiry clears only that disciplinary restriction. Fine, purse, result-reversal and title-vacancy consequences require explicit approved rules, including exactly-once settlement and preservation of original result provenance if amendments are permitted.

**Remaining consultation/design gate:** promotion versus world-wide jurisdiction; provider and policy ranges; confirmation/review timing; first/repeat penalty bounds; appeals and payer; AI policy; testing frequency; and financial/result/title consequences. The full system is the approved scope, but these numbers and powers are not approved merely by that scope. Resolve and version the tables before activating mechanics.

**Execution order:** case/provider/policy contracts and pure quotes → underlying evidence and testing handlers → confirmation/appeal lifecycle → independent eligibility and sanctions → policy/provider/case UI → explicitly authorised staff automation → player/AI/spectator and long-run qualification. J5 title decisions may use separate slices, but share immutable event references and interruption contracts.

**Acceptance:** injected-roll true/false/negative/inconclusive cases; confirmation upholds/overturns; appeal accepted/rejected/late; first/repeat offences; unavailable provider/capacity/funds; changed policy/provider mid-case; cancellation; same-week boundaries; save/reload at every stage; no repeated charge/draw/sanction; expiry with an independent injury; future booked fighters; player/AI parity under the same policy; no fabricated legacy findings. Test the entire approved title-option × corner-miss × outcome × belt matrix. Run T-World/T-Identity/T-Finance and fresh relevant native/source-bound gates before release.

## Implementation progress

### Stage 1 of 6 — G0 repair pass: COMPLETE

The first dependency stage is complete. Existing G0 work and this pass now cover the sixteen confirmed repair issues without changing the approved gameplay scope:

- Media and sponsor truth: campaign previews no longer call an authored exposure score a probability; changing a spokesperson immediately reprices the action; paid media-market refresh states its cost and replacement effect before commitment; sponsor portfolios stop at eight without silently discarding an active deal; sponsor value is labelled as a one-event-per-month maximum; Finance separates fixed monthly burn from booked-event medical exposure and uses activation-adjusted sponsor income.
- Visibility and labels: Rankings uses scouting-aware OVR display, visible-row champion counts and selected-row ranking scope; the profile badge is labelled World Division rather than P4P; Profile Injury Risk reads the live effective tendency while preserving the stored baseline.
- Workflow and presentation: stacked Matchmaking grows its scroll region and reserves fighter-table height; Combat Sports honours the shared Contracts filter; Fight Night classification recognises recorded stoppages, taps and unconsciousness while leaving defended/attempted attacks unaccented; custom Tk card widgets remap known semantic colours when themes change. Existing timestamp separation, compact reading height and wheel-scoped scrolling remain covered by the Fight Night suites.

**Files changed in this stage:** `media.py`, `views.py`, `ui.py`, `fight_night_presentation.py`, `fight_night_presentation_test.py`, and `g0_repair_regression_test.py`.

**Verification:** `py -3 -m py_compile media.py views.py ui.py fight_night_presentation.py g0_repair_regression_test.py` passed; `g0_repair_regression_test.py` passed (4 tests); `fight_night_presentation_test.py` passed (3 tests); `fight_night_layout_regression_test.py` passed (5 tests); `fight_night_archive_regression_test.py` passed (3 tests); `media_system_test.py` passed; `ui_data_regression_test.py` passed (22 tests). No save, simulation, native release certificate or EXE was changed or rebuilt.

**Next stage:** Stage 2 of 6 — G1 shared state and data contracts. Remaining major stages: **5** (G1, G2, G3, G4 and G5). Stage 2 must establish durable identity/read-model and quote/work/receipt contracts before new Staff, Media, calendar, history or replacement mechanics are added.

### Stage 2 of 6 — G1 shared state and data contracts: COMPLETE

G1 now provides the durable contracts that later feature stages can share without
creating incompatible IDs or duplicate ledgers:

- **Stable identity migration:** promotions receive an append-only `promotion_id`
  and persisted event dictionaries receive an `event_id` when absent. Existing
  IDs, fighter/staff/sport identities, names, list order and combat outcomes are
  preserved. A save-owned legacy-reference map records the explicit collection
  ordinal used for each generated identity, so repeated load/save cycles produce
  the same result. The top-level player company receives its own promotion ID
  even though it is represented by top-level fields at runtime. Duplicate IDs are
  repaired deterministically against the complete staged event graph.
- **Save-owned work records:** `FoundationMixin` supplies a versioned state block
  with independent promotion/event/work counters, operation receipts and bounded
  historical collections. It is part of the normal atomic save payload; there is
  no external sidecar that can drift from the career save. Historical readers are
  paged and bounded so long-running careers do not force an unbounded UI load.
- **Quote and commitment boundary:** pure `foundation_quote` data is observational
  and includes domain, action, target, amount, currency, details and timestamp.
  `foundation_commit` first checks an optional expected revision and validation
  callback, then applies the domain-owned change and records one receipt. Reusing
  an operation key returns the original committed/rejected/stale receipt without
  charging or applying again. Failed attempts retain an attempt count and may be
  retried; successful rows remain sealed.
- **Partial work:** `foundation_commit_rows` gives each row a deterministic child
  operation key. A multi-row batch therefore keeps successful rows when a later
  row fails and a restart skips only already committed rows. Domain handlers may
  supply snapshot/restore callbacks for full rollback when an apply operation
  fails; no coordinator path consumes RNG.
- **Compatibility and scope:** old saves without the foundation block load with
  neutral defaults and are migrated on the staged copy before commit. New saves
  include the complete current block. No legacy fighter fields, title lineage,
  detailed ratings, external database records or native fight mechanics were
  rewritten.

**Files changed in this stage:** `models.py` (append-only Promotion identity),
`feature_foundation.py` (new shared contracts), `main.py` (mixin integration),
`persistence.py` (save/load migration and player-company identity), and
`foundation_regression_test.py` (fourteen-test contract suite covering booking
identity migration and the first membership-history adapter).

**Verification:** `py -3 -m py_compile feature_foundation.py models.py main.py persistence.py foundation_regression_test.py` passed; `foundation_regression_test.py` passed (14 tests); `persistence_regression_test.py` passed; `identity_persistence_regression_test.py` passed. The existing save staging, forward-field compatibility, checksum and identity paths remain green. No EXE, native release certificate, simulation balance or unrelated UI page was rebuilt.

**Next stage:** Stage 3 of 6 — G2 presentation/read-model and workflow shell. Remaining major stages: **4** (G2, G3, G4 and G5). G2 will expose these IDs/quotes/receipts through shared filters, column preferences, progress/status panels and accessible empty/error states before domain-specific Staff, Media, calendar, fight-history or replacement controls are added.

### Stage 3 of 6 — G2 first playable interface: bounded replacement-workbench slice COMPLETE

The first G2/J5-facing workflow is now usable without changing the sealed fight
engine: the booked-card editor has a dedicated **Last-Minute Replacement** row.
The player chooses the affected corner, receives a dropdown of ready fighters in
the exact same gender/weight division, and sees each candidate's company rank,
world rank, record and current readiness. Candidate discovery is read-only until
the player presses **Offer Replacement**; active Rankings-page filters cannot hide
or relabel a replacement's actual position.

The commit changes only the selected unresolved slot. A free-agent candidate is
moved into the player's roster once, receives the existing one-fight terms, and
gets a fresh camp assignment; an already-rostered candidate keeps their identity.
The original fighter/name/ID, selected corner, replacement date, source and
pre-replacement company/world rank are appended to `replacement_history`. The
unaffected corner's preparation is not rerun, and a title booking is marked for
the separate title-review decision rather than silently stripping or inventing a
championship. Tournament fields retain their existing alternate flow.

**Files changed in this slice:** `events.py` (read-only candidate adapter,
rank-scope-safe labels, explicit replacement commit and editor controls) and
`last_minute_replacement_regression_test.py` (same-division/rank and evidence
retention tests). The shared G1 foundation remains the identity/save owner.

**Verification:** `py -3 -m py_compile events.py last_minute_replacement_regression_test.py` passed; `last_minute_replacement_regression_test.py` passed (3 tests); `ui_data_regression_test.py` passed (22 tests). Candidate filtering covers injured, fatigued, wrong-division, duplicate-name and already-booked cases in the adapter path, and the title-decision provider is injectable for deterministic coverage. No fight mechanics/outcome selection, title lineage, native release registry or EXE was changed; the player weigh-in decision is a preparation/UI boundary only.

**Explicit boundary:** this slice is the replacement workbench for unresolved or
future booked cards. A follow-up title-miss prompt shell now exposes the confirmed
five choices during a player weigh-in, including the same ranked replacement
dropdown; the provider hook is injectable for deterministic tests. Durable
pre-fight save/reload interruption, complete title/outcome matrix, title-merit
qualification across every branch and testing-company mechanics remain G5 work.
The UI does not claim those durable mechanics are already complete. The remaining G2 page cards
(dashboard, saves, profile/history, finance/media/staff/contracts, scouting,
rankings, combat sports, Academy, Fight Night landing and camp plan) continue to
use their existing routes and must be completed/reviewed before G2 is closed.

**Transition:** Stage 4 of 6 — G2 completion and G3 commercial lifecycle is now underway. Remaining major stages: **4** (G2 completion, G3 remainder, G4 and G5). The first campaign, rights, sponsor-receipt, Staff-autonomy and read-only calendar slices now run through the G1 quote/receipt owner; finish the shared page/read-model shell and the remaining lifecycle handlers next. Do not enable the unresolved R10 title-miss mechanics merely because the replacement dropdown exists.

### Stage 4 progress — M1 organisational campaign + Staff/autonomy/S3 evidence foundation + A2–A7/J1/J2/J3/J6/J10/S4 forward slices: COMPLETE (G2/G3/G4 still in progress)

The first approved commercial slice is now playable without retuning campaign
economics. Media state owns one versioned `media_primary_plan` envelope plus a
bounded plan history. A plan records one of the five approved objectives (event
promotion, prospect exposure, sponsor duty, regional work or trust repair), a
stable target reference and display snapshot, the selected existing action(s), a
spend ceiling, responsible staff reference, deadline fields, revision and status.
Old saves receive neutral `None`/empty plan defaults; no campaign target is
invented from old headlines or name-only history.

The desk exposes an explicit brief editor. Objective changes rebuild the target
list from current event/fighter/sponsor/region identities; the action list is
restricted to actions already supported by the current resolver; and the spend
ceiling is visible before commitment. Saving or replacing a brief has no
audience, popularity, trust, heat, cash, cooldown or RNG effect. Retargeting
updates only the unresolved plan and revision, preserving completed evidence;
cancelling records a terminal plan copy and runs no action. A stale or departed
target is surfaced as a review problem rather than silently redirected.

Running a campaign while a plan is active goes through the existing
`resolve_media_campaign` path. A pure quote states action points, cost, target
match, remaining weekly capacity and the explicit uncertainty that the existing
outcome roll still applies. A committed action receives one plan ID and one
evidence key in campaign history and one G1 operation receipt. The operation key
is stable for plan/week/action/fighter/target, so a retry after a refresh or
save/reload returns the original result without a second spend, cooldown, RNG
draw or popularity/heat change. The plan status/revision changes only after a
successful resolver call; a failed resolver leaves it retryable.

The Media Desk now also includes a read-only settlement-receipts panel. Each
row shows date, event, rights amount, sponsor amount and delivery state; selecting
one expands the outlet, production tier/quality, shortfall reason, individual
sponsor statuses and relationship change. Refreshing or reopening the panel
only reads the saved receipt collection.

The settlement panel now has a managed **View selected** detail brief (also
available by double-click). It separates rights delivery, production quality
versus the contracted requirement, audience outcome, sponsor duty status and
duty-period evidence, then retains a complete stored-payload section for future
fields. `media_commercial_receipt_details` resolves by durable receipt/event ID
against the current saved finance block and returns a defensive snapshot; it
does not call state-normalising offer/contract helpers, rerun settlement or
consume RNG. Missing legacy history remains explicitly absent rather than
being reconstructed from current contracts.

This slice does not yet implement target-specific audience multipliers, decay,
spillover, sponsor payment or new trust rules. The existing campaign formula and
activation settlement remain authoritative. The first M2/M3 integrity slice now
also exposes a read-only rights-terms accessor: conflicting legacy `fee` and
`guarantee_per_event` aliases are reported with the amount the existing payment
path reads, while newly accepted/countered terms synchronise both aliases and
carry a versioned Standard production label. It does not rewrite a conflicting
legacy deal. Event settlement now creates one bounded commercial receipt per
event, separating rights income, each sponsor entitlement, Met/Shortfall reason
and relationship change; repeated settlement/report opening returns the existing
receipt without decrementing contracts or paying again. Production enforcement
now maps the selected MMA tier to Lean 20, Standard 45, Premium 65 or Spectacle
85: an eligible but under-produced event still receives its contracted guarantee,
but is marked undelivered, with no performance bonus and the existing -5
relationship change. A bounded renewal workflow is now present: the player can prepare a successor
offer tied to the current contract, accept it without an immediate fee or
overlapping guarantee, and see it activate only after the predecessor completes
at the monthly boundary. Repeated acceptance is idempotent; a changed/expired
predecessor rejects the offer. Versioned sponsor agreements now carry a duty
envelope and event evidence; duties stay Pending during their period, then close
as Met only when qualifying evidence exists or Missed otherwise. The monthly
review archives the result without adding a new fine or changing the existing
full/half-fee rule. Legacy sponsor dictionaries remain readable without
inventing retroactive evidence. Renewals also allow exactly one retry-safe
counter choice (guarantee, reach, standards or commitment); a failed counter
withdraws the offer and a repeated click returns the sealed result. This slice
does not yet add make-good terms or a missed-duty sanction.

The first accountable Staff/autonomy slice is now also in place. A save-owned
`staff_management` envelope records the player's default policy, optional
department overrides, spending/review guardrails, draft briefs, work history,
exceptions and an evidence-only progression ledger. The four explicit policies are **Manual**, **Recommendations**,
**Selective Recommendations** and **Full Auto**. They are not decorative labels:
the effective mode is resolved per department, invalid values fall back to
Manual, and changing policy increments a revision without retroactively running
work. The UI exposes the mode, department override, current lead, capability
flags, active briefs and grouped `Needs attention` exceptions in one panel.

The capability matrix is deliberately honest while execution owners are still
being completed. Marketing now exposes two bounded built-in actions: reviewing an
existing M1 campaign plan produces a pure quote/evidence card at zero spend, while
an explicitly selected `campaign_plan_commit` runs the selected existing Media
action through its resolver when the player has chosen Full Auto for Marketing.
The commit uses a pure preflight against the current spokesperson, target,
capacity, plan ceiling and staff cash guardrails before calling the Media resolver,
then records actual spend/evidence once; missing spokesperson,
stale target, insufficient budget or resolver failure becomes `Needs attention`.
Briefs created without an action default to Review, preventing legacy callers from
silently authorising spending. The Staff UI now makes Review versus Commit visible.
Scouting and Doctor now also have
bounded read-only Full Auto reviews: a Scout can inspect an existing dossier and
return its saved confidence/recommendation, while a Doctor can report the
stored injury/return boundary. Neither starts a paid assignment, clears a
fighter or changes booking eligibility. Matchmaking's review handler now reuses
the deterministic Booking Workbench candidate read model to return actionable
identity-linked alternatives with ranks, fit/build, hard blockers and cautions;
it still generates no proposal, reserves no fighter and commits no card.
Matchmaking, Talent Relations and
Broadcast Producer can prepare advice/briefs, but their automation flags remain
off. Talent Relations advice now includes any existing identity-linked
relationship cases and their recorded reasons without opening or resolving a
case. Drug Testing Officer is shown as unavailable until the J5 provider/case
system exists. The legacy Scout auto-assignment rule remains a separate setting
and is labelled as such, so selecting Full Auto cannot silently turn unrelated
legacy behaviour on. Lead selection uses the existing staff roster,
role aliases (Scout/Matchmaker), morale-adjusted skill and stable roster-order
tie-breaking; it does not invent a new passive bonus.

A department brief is a reviewable draft with a stable brief ID, objective,
target references, allowed existing action IDs, lead identity, due fields,
spending ceiling, revision and status. Saving, quoting or cancelling a brief
does not spend cash, consume action points, roll RNG, change popularity or
execute work. Cancellation is explicit and terminal; stale targets and future
execution exceptions remain visible for the later worker slice. This gives the
player a real autonomy decision surface now while keeping unsupported Full Auto
work fail-closed rather than pretending that an advisory row completed a task.

Recommendation mode now has an evidence-producing handler seam rather than a
placeholder status. When a department exposes an allow-listed read-only
handler, the boundary invokes it with the saved brief and records the returned
evidence, target, action, lead identity and an explicit `requires_player_action`
flag in the work log. Handler failures become visible `Needs attention`
exceptions; they never execute the domain operation, spend cash, consume
capacity or award progression. Injected handlers are supported for deterministic
tests, while the built-in handlers remain observational until their department
execution contracts are separately approved. This makes Recommendations and
Selective Recommendations useful now without allowing advice to masquerade as
completed work.

The Staff work panel now has a second, read-only inspection layer. Selecting a
receipt and choosing **View selected** opens a managed evidence brief that keeps
the compact table readable while exposing the complete staff work row, foundation
operation receipt, quote/actual spend, boundary, lead, evidence key and any
stored handler result. Matchmaking advice is rendered as a ranked alternative
list with company/world positions, fit/build scores, hard blockers and cautions;
Talent Relations advice is rendered as identity-linked open cases with their
recorded reasons. The dialog also includes a full stored-payload section, so
future handler fields remain accessible without another schema or UI migration.
The lookup is a defensive snapshot: opening it never normalises state, refreshes
offers, reruns a handler, consumes RNG/capacity, or changes a brief. A missing or
stale operation is reported instead of silently substituting a same-name row.

The first S2 boundary hook is also connected to the weekly calendar work list.
The player explicitly commits a draft before it can be inspected. At most one
inspection is recorded per committed brief at a given saved month/week boundary,
so a brief created later in the same week still gets its own review. Recommendations
move to `Recommendation Ready` with a work-log row; Full Auto checks the
registered capability and, because the current departments are not yet
approved for automatic execution, moves unsupported work to `Needs attention`
with the exact reason. A repeated boundary call returns the existing attempt,
does not spend cash, consume media/scouting capacity or roll negotiation RNG,
and never claims that a recommendation completed a domain action. The policy
also stores bounded monthly spend and minimum-cash-reserve guardrails,
editable beside the mode; invalid values fail closed and every change advances
the policy revision. The boundary hook is the safe execution seam for the next
S2 handler work, not a hidden media-only auto mode.

The S3 safe first slice is now present as `staff_specialties.py`. It is a
central catalogue for the current specialty names with stable IDs, role and
category, plain-language explanation, bounded advantage, drawback/boundary,
trigger, strength and an explicit `Live mechanic` or `Personality only`
classification. The three Scout specialties that already have source-backed
scouting branches remain live; Doctor, Marketing, Matchmaker, Compliance,
Broadcast and Talent labels are descriptive until their own mechanics are
approved and tested. Unknown legacy/future strings are kept and rendered as
descriptive-only, never parsed into a bonus. Completed Full Auto work can opt
into a progression credit only when its handler supplies an evidence key and
`progression_eligible`; credits are deduplicated by work ID and distinct
month/week period. At a completed three-month quarter, three successful
capacity-consuming/paid actions in three distinct months and at least two
distinct targets qualify one deterministic +1 skill gain, capped at skill 80 and
four gains per game year. Zero-spend reviews, failed/cancelled work, signings
without employment and narrative milestones never qualify. The Staff panel and
profile dialog show specialty, credit/period totals, gain history and an observed
retention watch (contract review due, low morale or missing identity), so a player
can distinguish a real effect from role flavour without rewriting stored
employees or narrative history. Recommendations, page visits and duplicate
receipts never earn progression credit.

The S4 employment safety repair is also applied to the existing AI staff-market
path. A candidate is removed from the shared market only after the selected AI
promotion passes the affordability check; an unaffordable candidate is returned
to the market rather than lost. An affordable hire moves the same stable
`staff_id` into the promotion's staff collection and records one signing debit.
New AI hiring is bounded to one employee per role per promotion per game month,
and the promotion must retain six months of projected overhead plus the proposed
salary after the signing fee. Existing staff remain valid even when they exceed
that new-role cap. AI staff payroll is now part of the same monthly operating-cost
receipt; a monthly contract tick returns an expired employee to the shared market
with the same identity and records the departure. No automatic free replacement
is created. This closes the basic employment/payroll/expiry lifecycle while
preserving the existing signing roll and spectator-mode no-prompt path; passive
role bonuses and the full anti-farming long-run qualification remain gated.

J6 now has its own additive **Academy Coach** route. The role and three descriptive
specialties are appended to the candidate catalogue without renumbering existing
roles or turning gym `head_coach` strings into staff employees. Existing saves keep
the exact `staff_skill("Trainer")` fallback until the player hires and explicitly
assigns a coach. One coach may supervise one active prospect block; assigning a
second active cohort is rejected. The assigned block stores coach staff ID,
effective quality and the bounded adjustment `clamp((effective_quality - 45) ×
0.05, -2, +2)` as evidence. The adjustment is applied once to the existing Academy
trainer-quality input, not directly to fighter ratings, traits or combat outcomes.
Coach expiry/departure clears only the active assignment, retains the development
plan/reports and raises a review note so the player can choose a replacement.

The remaining G2 shared read-model slice now exposes foundation operation
receipts as pure display cards. Each card has a stable operation ID/key, domain,
action, target, normalized status label, attempt count, quoted amount, actual
spend, error and evidence key. Domain/status filters and summary counts operate
on copies of the saved state, so sorting, refresh and detail rendering cannot
repair a save or spend a budget. Staff work receipts use this same adapter and
show quote versus actual spend, evidence and receipt identity beside grouped
exceptions; the underlying work history remains available when a Foundation
receipt is not present. This gives the player one consistent “what was planned,
what happened, and why” readout across the Media and Staff slices.

The first A1 read-only calendar slice is now connected to the Promoter Dashboard.
`owned_schedule_index` combines the top-level MMA schedule, player-owned MMA child
promotion schedules and player-owned combat-sport division schedules into one
sorted display model while retaining the operating company, source sport, event
ID, venue, bout count, status and player-owned boundary for every row. The adapter
does not create a second schedule, settle a due card, reserve a fighter or mutate
legacy events that lack an ID; those rows carry a visible `Legacy reference` label.
Due, scheduled, completed and cancelled states are derived from the stored event
record and current calendar only. Rival promotions and non-owned children are
excluded, so the dashboard cannot imply that the player's wallet or roster controls
another company's card. `owned_schedule_regression_test.py` covers stable IDs,
legacy references, ordering, ownership filtering, due status, limits and refresh
purity. A future A1 child-card editor remains gated behind the separate commitment
and settlement rules in the detailed card.

The A4 goal-outcome repair is now live in the existing owner-goal panel. Legacy
goals default to the documented **achieve once** semantic; optional versioned
rows may explicitly use **maintain** (threshold plus required evidence months) or
**improve** (a persisted baseline plus a target delta). Evaluation is centralized
in `owner_goal_evaluate`: complete and failed outcomes are sealed with the
observed month/value, so a later cash dip cannot undo a success and a late
recovery cannot erase a missed deadline. Improve goals record their baseline on
first evaluation; maintain goals record the month their evidence window starts.
The dashboard labels each row with its semantic and keeps progress units aligned
to the metric. No objective creates a new fine, reward, RNG draw or gameplay
effect, and old goal dictionaries remain readable. `owner_goal_regression_test.py`
covers legacy achieve-once persistence, missed-deadline sealing and both explicit
semantic variants.

The first A3 cash-planning slice is now live on Finance → History & Outlook as a
read-only 12-week runway. It starts from the actual current cash balance and
shows the amount already paid in the open week, then applies recurring office,
staff, strategic-upkeep and Academy bills on the same weekly/monthly boundaries
used by the calendar. Committed main-promotion cards are quoted from their
stored purses, venue, production tier, marketing, medical and testing settings;
cancelled/completed cards are excluded, and child-promotion/Combat Sports
wallets remain explicitly outside the player-MMA cash line. Each due card is
shown with three bounded sensitivity closes (80%, 100% and 120% of baseline
attendance, capped by venue capacity), not probability bands. Rights and sponsor
receipts are listed as conditional and are deliberately excluded from the close
until activation is settled. The lowest baseline balance and the cards causing
it are called out so individually affordable cards cannot hide an intervening
cash shortage. The forecast does not write ledgers, reserve fighters, consume
RNG or create a scenario record; applying edits remains deferred to the existing
booking/commitment editors. `cash_runway_regression_test.py` covers empty
calendars, month-boundary bills, competing cards, finite rights allocation,
conditional receipts, scenario ordering and state/RNG stability.

The first A2 closeout slice is now connected to the same super-event records.
New approvals normalise the template's `security`/`revenue` terms into a
versioned accepted snapshot (`security_cost`/`revenue_multiplier`) while
retaining the authored template values for audit. Settlement therefore cannot
silently fall back to zero security or neutral revenue for a newly accepted
project; the approval deposit is still the only amount paid at acceptance, and
remaining setup/security stay visible until the card settles. Planning projects
that pass their deadline now close as `Expired` at the next month boundary,
without an invented refund or penalty. The milestones window has an explicit
Cancel Planning Project action; it keeps a paid deposit sunk, does not charge
unperformed work, clears only the matching active project and retains a
terminal history row. Cancelling a scheduled super-event card uses that same
idempotent closeout, so the event, offer and project cannot leave an orphaned
agreement or duplicate history. Completed projects are guarded by the same
terminal ID check and continue to receive their existing sporting/popularity
effects exactly once. `super_event_closeout_regression_test.py` covers canonical
terms, deposit accounting, planning expiry, scheduled cancellation and
duplicate closeout calls. Legacy offered/accepted records remain readable; no
completed event is rewritten and no discretionary extension or new cancellation
fine is introduced.

The first A6 recruitment-decision slice is now live on Scouting → Decision Packs.
The player can select two to four visible targets on the Target Board and save a
named decision with a purpose, comparison criteria, dated ID-linked public facts,
and the best completed dossier snapshot currently available. Current employer,
division, record and availability are re-read by identity at display time, while
the captured report ranges and player notes remain historical evidence. A departed
or retired candidate therefore stays visible as an unavailable alternative instead
of disappearing or being replaced by a same-name fighter. The pack state is an
explicit Considering / Needs report / Ready for negotiation / Archived decision;
Ready never signs a fighter, spends cash or changes scouting confidence. Rename,
state and note edits update only the pack, and opening a candidate resolves by
fighter ID. Refreshing the board or pack list never commissions a report or rolls
scouting RNG. `recruitment_decision_pack_regression_test.py` covers the two-to-four
boundary, evidence immutability, explicit states/notes and departed-candidate
history; persistence save/load now retains up to 40 packs without deleting the
existing watchlist or report collections.

The first A5 relationship-case slice is now available from Staff → Talent
Relations Cases. A case can only be opened from an existing active Contract
Promise or Career Journey, and its source reference, fighter ID, original
obligations, reason, due month and evidence history are retained. The case view
re-derives current promise/arc state from the authoritative fighter and story
records, so partial delivery is visible, a missing/retired fighter closes with a
truthful departure note, and a transfer is shown as responsibility moving between
companies. Duplicate names remain separate by fighter ID. The player can
acknowledge a case, record an existing support action or review the evidence;
these actions are idempotent and have no morale, trust, title-merit, deadline,
cash or RNG effect by themselves. Career/contract buttons link back to the
existing authorised workflows, where any real cost or effect is still applied
once. `relationship_case_regression_test.py` covers repeated opening, partial
fulfilment, duplicate-name departure, transfer handling and the no-benefit
acknowledgement/action boundary. Cases persist separately from, and never
overwrite, promise flags or Career Journey records.

The first A7 followed-story slice is now live from World Hub/Storylines and the
story reader. Follow/unfollow targets use a thread ID, fighter ID or company
name and persist an explicit acknowledgement cursor plus snooze window. Story
Briefings group retained beats under one continuing thread, show current stakes,
and disclose when the cursor's older source beat has expired instead of inventing
continuity. Refresh, sorting and opening a reader never advance a cursor or run
simulation/narrative generation; only Acknowledge Latest moves the cursor to an
actual retained beat. Snoozing hides the notification while history accumulates,
and unfollowing leaves all storylines readable. `story_briefing_regression_test.py`
covers new-beat boundaries, cursor acknowledgement, company subscriptions,
snooze/unfollow retention and expired-cursor coverage gaps.

The first J1 **Explainable Booking Workbench** slice is now live in Matchmaking.
The player can save one identity-linked anchor brief with an explicit Sporting,
Development, Commercial or Balanced emphasis and a bounded opposition OVR range.
Generating alternatives is an explicit action, never a side effect of refresh,
sorting or opening the page. Each proposal stores the target date, brief revision,
current company/world rank snapshot, record, OVR, match fit/build evidence and
the exact distinction between hard blockers (medical return, injury, fatigue,
retirement, closed division, existing booking or wrong division) and advisory
cautions (rematch/merit warning or the brief's preferred range). A blocked row
remains visible so a shallow division is explainable rather than silently empty.

Review re-reads current identity and eligibility while preserving the generated
snapshot; a departed or changed fighter becomes Unavailable/Blocked instead of
being replaced by a same-name row. Filling an option is an explicit player action
that revalidates both corners and appends the same canonical draft-card shape as
the ordinary Add Matchup path. The fill carries proposal provenance, uses no
new RNG, reserves no cash and does not assign camp or title credit. Foundation
receipts make the operation retry-safe: a repeated click returns the existing
receipt and never adds a second bout. `booking_workbench_regression_test.py`
covers deterministic generation/RNG purity, rank and identity snapshots,
hard-block versus caution presentation, stale review, canonical fill, duplicate
clicks and receipt idempotence; persistence retains the brief/proposal envelope
without changing legacy saves.

The J1 tentative-medical follow-up is now also usable as a deliberately
non-binding planning boundary. A blocked same-division candidate can be saved as
an identity-linked medical draft, with the earliest recorded return, current camp
weeks/quality and the exact confirmation rule preserved in the snapshot. The
Matchmaking proposal window exposes the facts beside the blocking reasons, while
the standalone Medical Drafts view re-reads current status without rewriting the
stored evidence. A candidate who clears is shown as `Ready to confirm`; a target
date that has passed is shown as `Needs replacement`. Saving/reviewing the draft
does not reserve a fighter, assign camp, spend cash, consume capacity, run a
weigh-in, grant title credit or draw RNG. Normal event-week medical and booking
checks remain authoritative, and no recovery guarantee is inferred. This completes
the safe planning/read-model portion of J1; firm tentative reservations, recovery
promises and title-decision interruption remain outside the approved slice.
`booking_workbench_regression_test.py` now covers preview purity, identity-linked
draft persistence/idempotence, live-ready review and stale-date expiry.
The adjacent Draft Review read model now separates preserved pairings from
unresolved TBA slots without pretending that a legacy card position is a durable
booking identity. Explicit booking/fight IDs are displayed when supplied;
otherwise the row is labelled `Legacy reference`. Foundation migration now supplies
deterministic draft/event-scoped IDs for legacy rows and repairs duplicates without
RNG or global counter drift. Complete stable draft rows can open the bounded
locked-slot editor: deterministic same-division alternatives carry current rank,
medical and blocker evidence; the original fight fingerprint is retained; stale
rows fail closed; and commit replaces exactly one corner while preserving title,
tier, plans and unaffected fights. The player must explicitly commit through a
Foundation receipt; replacement history is appended, retries are idempotent, and
scheduled event fights remain read-only. `booking_workbench_regression_test.py`
covers identity migration, options, stale rejection, preservation, no-RNG, retry and
unknown-evidence retention.

The first J3 **Reviewable Contract Batch** slice is now live from Contracts.
The player explicitly selects roster fighters and receives one saved, pure quote
per identity: proposed purse, term, guaranteed fights, signing bonus, up-front
cash and guaranteed exposure, plus current expiry state, ranking context and
contingent clauses. Duplicate selections collapse by fighter ID, the displayed
order is stable, and review never runs negotiation or consumes RNG. A review
re-reads the current roster while keeping the quoted terms as historical
evidence; a departed, retiring or changed fighter is shown as unavailable or
blocked rather than silently substituted.

Confirmation is explicit and explains partial success before any work starts.
Each row is revalidated against the live roster and committed through its own
Foundation operation key, using the established negotiation handler in stable
order. Successes and failures are retained in a readable result ledger; a
failed row is sealed rather than rerolled, and a repeated click returns the
existing batch result without a second negotiation or charge. The Contracts
page keeps the legacy single-fighter and legacy auto-renew controls, while the
new Review Renewal Batch button provides the safer quote-first path. Expanded
automation policies, salary escalators and all-or-nothing negotiation remain
out of scope for this slice.

The first J2 **Event Preparation Timeline** slice is now stored in every newly settled event
package and rendered in the End of Event summary as four compact cards: Campaign / media,
Press conference, Weigh-ins and Final readiness. The cards read the existing press and weigh-in
lines, cancelled-bout count, stable fighter-ID references (excluding TBA), stable per-stage
completion keys and any already recorded
event-targeted media action evidence. They distinguish recorded outcomes from an honest “No
recorded outcome” state and make the final readiness state explicit when a bout was cancelled.
The timeline is an additive read model (`schema_version` 1, `preparation_revision` 1); it does
not resolve a press conference, rerun a weigh-in, consume RNG, alter card order or change fight
mechanics. Because it is included in the canonical event package, the same evidence remains
available to the read-only event archive after settlement. Existing packages without the field
continue to render normally. Earlier stochastic-resolution timing, pre-event campaign planning,
replacement invalidation and resumable pre-fight decisions remain held for the separately specified
J2/G5 slices; this pass deliberately avoids changing draw order or save interruption semantics.
`j2_event_preparation_regression_test.py` covers identity de-duplication, TBA exclusion, stable
stage ordering, campaign evidence linking, missing-outcome honesty, input immutability and RNG
purity.

The first J10 **Rules Help** slice is now a normal Tools → Rules Help page rather than a separate
manual. `rules_help.py` owns eight stable authored topics covering company/world ranking scope,
title merit, availability and camps, staff autonomy, campaign costs, contract obligations, finance
vocabulary and event preparation. Each topic contains a concise explanation, an honest blocked-state
description, stored aliases/terms for search and a route back to the relevant existing screen. The
search preserves catalogue order, searches only that authored visible text, returns defensive copies
and stores only the UI query preference; it never evaluates live rankings, formulas, scouting data,
or gameplay RNG. A stale/missing route disables the action rather than guessing a destination. The
detail view also works alongside partial scouting because it explains unknown values instead of
showing hidden world data. `rules_help_regression_test.py` covers catalogue completeness, stable
IDs/order, case-insensitive defensive search, RNG purity and fail-closed route wiring. The page is
presentation-only; contextual comparison percentiles and any new rules remain outside this slice.
The comparison window now also displays a truthful cohort context: as-of date,
gender/division, visible-count coverage and a complete-versus-known-sample label. The adapter
deduplicates by fighter identity, excludes retired rows, and counts only ratings legitimately visible
under Scouting Mode. It never computes a percentile, exposes hidden values or turns a partial sample
into a false ranking. `j10_comparison_regression_test.py` covers complete and partial cohorts,
identity de-duplication, stable date/coverage labels, input immutability and RNG purity.

**Files changed:** `media.py`, `staff_management.py`, `main.py`, `persistence.py`, `events.py`,
`ui.py`, `views.py`, `world.py`, `media_plan_regression_test.py`,
`staff_specialties.py`, `feature_foundation.py`, `staff_management_regression_test.py`,
`foundation_regression_test.py`,
`staff_specialty_regression_test.py`, `staff_employment_regression_test.py`,
`owned_schedule_regression_test.py`,
`owner_goal_regression_test.py`,
`cash_runway_regression_test.py`,
`super_event_closeout_regression_test.py`,
`recruitment_decision_pack_regression_test.py`,
`relationship_case_regression_test.py`,
`story_briefing_regression_test.py`, `booking_workbench.py`,
`booking_workbench_regression_test.py`, `contract_batch_workbench.py`,
`contract_batch_workbench_regression_test.py`, `j2_event_preparation_regression_test.py`,
`fight_night_archive.py`, `fight_night_archive_regression_test.py`,
`rules_help.py`, `rules_help_regression_test.py`,
`j10_comparison_regression_test.py`,
`simulation_pause_policy_regression_test.py`,
`pinned_checkpoint_regression_test.py`,
`play_level_audit.py`, `play_level_audit_regression_test.py`,
`academy_coach_regression_test.py`,
`constants.py`, `seeding.py`,
and `run_regression_suite.py`.

**Verification:** `media_plan_regression_test.py` passed (11 tests),
`staff_management_regression_test.py` passed (22 tests),
`staff_specialty_regression_test.py` passed (4 tests),
`staff_employment_regression_test.py` passed (3 tests),
`academy_coach_regression_test.py` passed (4 tests),
`media_system_test.py` passed, `persistence_regression_test.py` passed,
`identity_persistence_regression_test.py` passed, `foundation_regression_test.py`
passed (14 tests), `narrative_system_regression_test.py` passed,
`narrative_long_run_storage_regression_test.py` passed,
`simulation_performance_regression_test.py` passed,
`owned_schedule_regression_test.py` passed (2 tests),
`owner_goal_regression_test.py` passed (3 tests),
`cash_runway_regression_test.py` passed (3 tests),
`super_event_closeout_regression_test.py` passed (3 tests),
`recruitment_decision_pack_regression_test.py` passed (3 tests),
`relationship_case_regression_test.py` passed (4 tests),
`story_briefing_regression_test.py` passed (3 tests),
`booking_workbench_regression_test.py` passed (11 tests),
`contract_batch_workbench_regression_test.py` passed (3 tests),
`j2_event_preparation_regression_test.py` passed (2 tests),
`fight_night_archive_regression_test.py` passed (4 tests),
`rules_help_regression_test.py` passed (4 tests),
`j10_comparison_regression_test.py` passed (3 tests),
`ui_data_regression_test.py` passed (28 tests), and `smoke_test.py` passed;
`window_lifecycle_regression_test.py` passed,
`py_compile` passed for the changed modules. No EXE, native fight mechanics,
title lineage or saved career was rebuilt or rewritten.
The maintained `run_regression_suite.py` then completed with
`ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`; its expected headless
Matchmaking click-selection probe was skipped because that display cannot lay
out the fighter table. Stability also passed after the Tk cleanup callbacks
were exercised.

**Next implementation slice:** finish the remaining G2 shared page/read-model
cards and real domain handlers against the G4 Staff execution seam. J1's first
deterministic proposal/review/fill path and J3's quote-first contract batch are
now usable, and J2's first recorded-outcome preparation timeline is now usable;
J10's searchable authored help page and truthful comparison context are now usable;
J1's non-binding tentative medical planning is now usable; firm medical reservation
and scheduled-event editing remain bounded follow-ups. The Draft Review now makes
preserved pairings and unresolved TBA slots visible, and complete stable pairings
can enter the locked-slot multi-proposal editor described above. This editor is
limited to the unscheduled player draft card until a separate scheduled-event
domain owner and interruption contract are approved.
A5 Talent
Relations and A7 story briefings now consume durable evidence rather than making
parallel narrative state; A6 packs, J6 Academy Coach assignment, and the basic
S4 AI employment/payroll/expiry lifecycle are also durable. Marketing Review/Commit
is now the first genuinely executable staff-domain pair. The remaining non-testing departments now have
registered, read-only review handlers and explicit player-facing permission scopes, but their
automation flags stay off where a review could otherwise be mistaken for booking, negotiation,
production or testing authority. Next add only separately approved execution handlers and
evidence-gated S3 progression, then complete the deeper
G5 testing/title-decision lifecycle and its long-run gates. J9.a's read-only
regional feasibility and the first G5 title-decision resume guard are now
implemented below; they do not authorise the held invitation, testing-sanction
or full title-outcome slices.
J4's first membership-history slices are now durable as well: transition hooks,
known-present migration boundaries, interval derivation and the Profile History
Company Timeline are implemented and covered. The full read-only as-of/index/export
window is now live, including title-history joins and incomplete-coverage labels.
The remaining J4 work is the retention/load policy, title-history edge cases and
broader behavioural coverage; missing dates must remain explicitly unknown in every
future query or export.
J7.a structured company proposals for swaps and parent/child moves are now
usable through the transfer and child-promotion desks, with a read-only ledger,
stable fighter/company IDs, expiry or recall boundaries, warnings and
idempotent outcomes. J7.b's time-bounded return-date loan and later treaty or
ownership mechanics remain separately held behind their own policy decisions;
the bounded loan-return slice is now implemented as a follow-up below.
The generic worker boundary is now implemented: it consumes only explicitly
allow-listed actions, enforces per-action/monthly ceilings and minimum cash reserve,
emits a work record plus exception when a brief cannot run, and requires a player
decision for unsupported or high-impact work. Each new handler must be separately
injectable, preserve its existing domain operation/receipt contract, and be
retry-safe before that department's `automation` flag is enabled. A visible Requeue
action lets the player correct permissions/terms and retry an exception deliberately;
it does not reset other briefs or duplicate the previous attempt. M2/M3 follow-up is
presentation/detail polish: show production evidence, successor terms, duty-period
evidence and richer receipt inspection without changing the settled economics above.
Remaining major stages: **4** (G2 completion/G3 remainder, G4 Staff autonomy and
employment, and G5 durable testing/title-decision lifecycle).

**Stage 4 staff evidence follow-up (12 September 2026):** the Matchmaking and
Talent Relations handlers now return the existing Booking Workbench candidate
rows and open relationship-case rows as structured, identity-linked evidence.
The Staff UI exposes that evidence through a managed read-only receipt detail
window; the compact table remains a summary and the full payload remains
available for audit. `staff_work_details` matches either the durable operation
ID or the original work ID and searches foundation receipts by their stored
operation identity, avoiding the common mistake of treating the operation key
and generated receipt ID as the same field. The new regression proves nested
alternatives/cases survive the lookup and that reading the detail does not
mutate the save-owned work log. This is still a G2/G3/G4 presentation/read-model
slice: it does not enable Matchmaking booking, Talent Relations negotiation, new
sponsor penalties or any new staff gameplay effect.

The legacy sidebar Fight Night route is now a styled, scrollable **Event Log**
landing page rather than an unstructured Courier text dump. It keeps every
stored log line in order, adds a count/read-only summary, and applies
theme-aware semantic accents to event headers, dividers, results, key moments,
office actions and system notices. The renderer preserves the reader's scroll
position during refresh/theme changes and is called by the existing `write_log`
path, so simulation and event recording behaviour remain unchanged. Empty saves
receive an explicit next-step message; no history is deleted or inferred.

The maintained runner was rerun after this follow-up. Every suite before the
final Stability playtest passed, including the 22-test Staff suite, UI-data,
Fight Night, profile, media, persistence, native release/audit and full-system
checks. The first Stability invocation hit its existing seeded talent-ecosystem
distribution bound (`High-level regional development is missing or
overproduced`); a standalone rerun completed with `STABILITY PLAYTEST PASSED`
for seeds 2201–2203. Treat the one failed full-run attempt as a retained
diagnostic rather than silently calling that invocation green; the rerun shows
the failure is not reproducible in the current source and no Staff/UI change
touches the regional-development mechanics.

After the Event Log and landing-card slices, the focused UI-data suite passed 28 tests and the
full smoke playtest passed again (with only the documented headless
Matchmaking-coordinate probe skipped). The first smoke attempt caught and
closed a missing theme-colour token before any user data or simulation state was
affected.

The Finance landing page now adds a compact, read-only decision strip above
the existing Cashflow/Sponsors and History/Outlook notebooks. Four cards make
current cash, recurring monthly commitments, expected media-plus-active-sponsor
income per booked event, and booked purse/medical exposure visible at a glance.
The cards are populated from the same values already used by the Finance
summary and cash-runway forecast; they do not create a second ledger, apply a
new probability, or charge medical costs as a recurring monthly bill. Exposure
is explicitly labelled as booked-card reserve, while event income remains an
estimate and the detailed transaction/history tables remain the complete
record. Theme changes use existing semantic colours and the cards have no
action callbacks, so repainting, sorting, tab switching and refresh remain
observational. `ui_data_regression_test.py` covers all four card keys and
their shared refresh inputs (28 tests total), and the full smoke playtest
passed after the change.

The Contracts landing page now adds a selected-fighter read-only brief beneath
the existing ledger controls. It brings the selected fighter's division, rank
or champion status, contract type, purse, term/expiry, morale and recorded
special obligations into one readable summary, while keeping the full table,
filters and renewal/batch actions unchanged. Comeback and retirement-bout
terms use their existing fight-counted labels. The brief explicitly states
that renewal remains a player action; selecting, refreshing or opening a
profile never negotiates, charges or changes a contract. `ui_data_regression_test.py`
now covers the brief's identity/obligation wiring (28 tests total).

The Regions landing page now pairs its complete profile text with four
read-only context cards: local market/economy, regulatory status, estimated
drug-testing accuracy and regional MMA interest. The cards also disclose the
tracked-area, local-promotion, known-gym and booked-show counts so a player can
read the commercial context without parsing a paragraph. They are populated
from the selected region's existing data and current owned schedule; no
regional rating, legal rule or testing mechanic is changed, and the full
profile remains available below. `ui_data_regression_test.py` covers all four
card keys and refresh bindings (28 tests total).

The Companies / Industry Standings page now adds four selected-company context
cards above the retained full profile: industry rank, composite power, roster
depth and operating stability. Supporting notes keep the tracked-company
denominator, champion/star count, credibility and cash visible without forcing
the player to parse the profile paragraph. The complete roster, event calendar,
strategy and power-breakdown text remains below, and all cards read the existing
standings row selected by stable sport/name identity. Sorting, filtering,
opening a company hub or switching to spectator mode remains unchanged; no
power, rank, cash or AI strategy values are recalculated by the UI. The
`ui_data_regression_test.py` source contract now covers these cards (28 tests
total). The Results Database detail pane now also leads with four read-only
cards for the selected event's date, main-event headline, stored bout count,
and recorded gate/profit result. The complete result text and full replay
actions remain unchanged, and empty/filtered states clear the cards rather
than leaving stale event data visible. Selecting or refreshing a result never
reruns an event or alters its archived record; the new source contract is
covered by the UI-data suite (28 tests total). These Finance, Contracts,
Regions, Companies and Results cards close another set of shared G2 landing
surfaces; they do not close Stage 4 because the remaining domain-handler and
G5 lifecycle gates still require their own contracts and regressions.

The post-card full smoke pass built every lazy screen and passed, including
the Finance, Contracts, Regions, Companies and Results pages. It retained the
known headless Matchmaking-coordinate skip and did not touch a save or EXE.

The first J11 implementation slice now persists a versioned spectator
`simulation_pause_policy` inside the existing rules envelope. The observer
panel can arm an exact internal month/week target and optionally pause after a
new hosted world event; company and fighter filters are supported by stable
stored identity, while the UI keeps the current no-routine-prompt spectator
preset. The runtime advance job copies this plain data, captures an archive
cursor and evaluates it only after the current week has fully settled. It never
serialises Tk callbacks, runs a resolver, grants staff authority or consumes an
extra RNG draw. A user stop or matched policy records the last completed
boundary and a bounded reason, disables the armed policy, and exposes Resume;
Resume rebuilds the remaining week count from the saved target and refreshes
the event cursor so the same event cannot immediately retrigger. Clear is
idempotent. This is deliberately a policy/resume slice: manual pinned
checkpoint files and actionable management-deadline predicates remain a later
J11 increment, and no automatic copies are created. `simulation_pause_policy_regression_test.py`
covers exact target boundaries, event/company/fighter filtering, RNG purity,
reload-shaped cursor data, nonmatching events and repeated clear. Compile and
smoke coverage also exercise the new lazy Game & Saves controls.

The second J11 increment adds explicit pinned checkpoints without changing
rolling recovery. **Pin Active State** serialises the current world through the
existing atomic gzip writer into a separate per-slot `Pinned Checkpoints`
folder. Each record carries source save/group, game date, saved-at timestamp,
byte size and an atomic-verification status; duplicate labels receive a stable
suffix and a twelve-file cap prevents accidental disk growth. The manager
shows those fields, restores only to a user-chosen destination slot after
confirmation (protecting an existing destination with the normal recovery
backup), and deletes only a validated file inside the active checkpoint folder
after confirmation. Pinning, restoring and deleting never switch the active
career, run simulation, settle an event or overwrite rolling autosaves. Failed
writes leave no checkpoint. `pinned_checkpoint_regression_test.py` covers
separate-folder output, duplicate labels, the bounded limit, failed atomic
writes and path-safe deletion. Actionable management-deadline predicates and
source/version-gated long-run checkpoint resumes remain later J11 work.

Verification for this J11 slice: `simulation_pause_policy_regression_test.py`
passed (6 tests), `pinned_checkpoint_regression_test.py` passed (5 tests),
`persistence_regression_test.py` and `window_lifecycle_regression_test.py`
passed, `ui_data_regression_test.py` passed (28 tests), `py_compile` passed,
and `smoke_test.py` passed with the known headless Matchmaking-coordinate
probe skipped. No EXE or user save was rebuilt or modified.

The next V11 presentation slice adds a selected-target strip to the Scouting
Target Board. Four cards expose only visible, identity-linked context: fighter
and division, dossier freshness/status, advisory verdict and current market
context. The cards are populated from the same saved report and scouting
visibility helpers used by the table, clear on selection loss, and retain the
full filters, pagination, report actions and dated evidence below. They never
reveal hidden OVR/potential, commission a dossier, roll scouting RNG or mutate
the shortlist. `ui_data_regression_test.py` now covers the four card keys and
refresh wiring (29 tests); compile and the full smoke lifecycle also exercise
the lazy screen.

The first V15 presentation slice now leads the Combat Sports Universe page with
four selected-sport management cards: AI versus owned roster depth and readiness,
the next committed child-promotion card, contracts within two months of expiry,
and the latest recorded result. Refreshing or changing rows restores the same
sport by stable sport ID rather than silently jumping to the first row. The
cards read the existing child-division schedule, roster contract fields and
recorded event history; they never schedule a card, recalculate ratings, change
ownership or reveal MMA-only data through a sport-native screen. Full circuit
rankings, card-building controls, records, title lineage and transcript/history
views remain available below and in the existing management windows. Empty
states explicitly say when a child promotion has not been opened or no card/result
is recorded. `ui_data_regression_test.py` now covers the four card keys, selected
sport retention and native schedule/contract fields (30 tests); compile and the
full smoke lifecycle exercise the lazy page.

The V19 Scouting search slice now schedules Target Board typing through a
200-millisecond pending callback. A newer keystroke cancels the prior callback;
the callback also carries a revision so a stale scheduled refresh cannot repaint
newer results. Explicit company/gender/division/intel/logic filter changes still
refresh immediately. Leaving Scouting or closing the application disposes the
pending callback, while the existing identity-based selection and page access
remain intact. The search remains read-only: no dossier, RNG draw or shortlist
mutation is triggered by typing. `ui_data_regression_test.py` now covers the
debounce, revision guard, cancellation and navigation disposal (32 tests total).

**Stage 4 progress update:** the V15 Combat Sports management strip, V18 Camp
Plan decision window and V19 Scouting debounce are now complete observational
UI slices. They preserve the existing sport, camp, scouting, finance and
identity owners; no new simulation mechanics or hidden-information paths were
introduced. Focused UI-data coverage is 32 tests and the full smoke playtest
passes with the documented headless Matchmaking-coordinate probe skipped.
Stage 4 of 6 remains active. Remaining major stages: **4** (G2 completion/G3
commercial lifecycle, G4 staff execution/evidence gates, and G5 durable
testing/title-decision lifecycle). The next dependency-ready work must be a
separately scoped domain handler or an approved G5 contract slice; do not treat
these presentation completions as permission to enable unsupported automation
or title-miss settlement.

The next V13 World Hub slice adds four read-only context cards above the
promotion/gym split: selected company identity, promotion snapshot, selected
gym facts and gym capacity/morale. Promotion and gym row IDs are retained across
refresh when available; if a row disappears, the cards show the explicit empty
state. Existing world tables, wrapped factual news, profile links and management
buttons remain the source of truth. The cards do not recalculate reputation,
cash, training quality or ownership and do not create or settle events.

The first bounded G5 title-miss evidence slice now writes a versioned,
plain-data `title_miss_decision_state` before the player prompt. It retains the
event reference/date, both corner identities, miss amounts, champion/interim
roles, title-eligibility context and the complete five-choice action list. Once
the provider returns, the chosen action, reason, replacement ID and terminal or
needs-review status are recorded; Keep Belt and Remove Belt also carry an
explicit `title_sanction_snapshot` so later settlement can distinguish a
champion weight miss from an ordinary made-weight defence. The replacement
branch captures the removed fighter before mutating the slot, preserving the
correct champion identity and title-review consequence. This is evidence and
provenance only: the resumable pre-fight save/reload prompt, full choice ×
corner × belt/outcome matrix, rebooking editor and testing-company mechanics
remain gated G5 work. `last_minute_replacement_regression_test.py` now covers
the snapshot shape, source ordering, preparation/archive projection,
pre-commit consequence copy and Results-card rendering (8 tests).
The same state is copied into each applicable `fight_logs` row and into the
event's stored preparation timeline as `title_miss_decisions`, including the
action, reason, replacement identity, missed-corner evidence and whether the
title remained on the line. This is still observational provenance: it does not
make the pre-fight prompt resumable, rerun settlement, or decide the unresolved
Remove Belt/Replacement title matrix.

The title-miss dialog now also keeps a visible consequence preview for every
approved action (including the ranked replacement path) and labels unresolved
vacant-belt/rebooking policy as unresolved. Hover/focus changes only this
presentation copy; no resolver, ranking read, title mutation or RNG draw runs
until the existing explicit choice is committed.
The Results Database preparation view now renders the retained title decision,
status, title-on-line state, replacement identity and reason alongside the
stored weigh-in lines; it remains read-only and works for legacy records that
have no decision field.

**Stage 4 progress update (title evidence archive):** focused title/replacement
coverage is 8 tests, the preparation-timeline contract remains 2 tests, the UI
data suite remains 33 tests, and the post-change smoke playtest passes with the
documented headless Matchmaking-coordinate probe skipped. No EXE or user save
was touched. Stage 4 of 6 remains active; **4 major stages remain** (G2/G3
completion, G4 Staff execution/evidence gates, and G5's durable
testing/title-decision lifecycle).

**Stage 4 progress update (S3 specialty mechanics):** the central staff
specialty catalogue now carries the three approved live non-Scout definitions
and their complete explanations. `StaffManagementMixin.staff_specialty_cost_reduction`
selects the single morale-adjusted effective department lead and returns a pure,
integer, 2%-capped saving for the named eligible subtotal. Campaign Coordinator
is applied by the shared media quote/settlement spec; Contract Administrator is
included in the existing negotiation-administration target basis and is visible
in the negotiation card; Production Coordinator is applied only to staged
production and the finance result exposes both the staging subtotal and saving.
New candidates can surface these specialists through a deterministic identity
assignment that preserves legacy random draw order. The Staff readout now shows
the approved effect alongside mechanic status and work credits. Coverage is
5 specialty tests, 23 Staff-management tests, the media-system regression and
event-economics regression; all pass. The G0 UI geometry probe remains the same
known headless 45px/60px failure and is unrelated to this slice. No EXE or user
save was touched. Stage 4 of 6 remains active; **4 major stages remain**.

The follow-up scope check also hardens ownership: `_media_action_spec` accepts
the resolving promotion context, so a player Campaign Coordinator can never
discount an AI/child promotion's campaign. The media regression now covers that
cross-company quote boundary; player and foreign quotes retain the same
pre-specialty price basis and only the owning player's lead can produce the
approved saving.

**Stage 4 progress update (J12 career-to-database conversion):** the approved
R13 policy is now executable as a bounded workflow. `career_conversion_preflight`
returns structured error rows for unknown fields, duplicate top-level fighter IDs,
invalid divisions and missing promotion owners without mutating the source. The
staged package preserves stable fighter/promotion identities, current supported
skills/age, records, roster ownership and contracts; it resets live time, cash,
finance, inbox, pause targets and active work, including nested promotion and
combat-sport event ledgers. A sibling `<name>.conversion.json` manifest retains
completed history and every excluded obligation with exact counts and provenance,
and the UI requires explicit acceptance before writing. Existing destinations are
never overwritten; cancellation and failed writes clean up safely, and the source
career remains untouched. Game & Saves labels the resulting database as **Career
Start** while hiding its manifest from the database selector. Coverage is the new
5-test `j12_conversion_regression_test.py`, persistence regression, UI-data
regression and the isolated runner; all pass. No EXE or user save was touched.
Stage 4 of 6 remains active; **4 major stages remain** (G2/G3 completion, G4
Staff execution/evidence gates, and G5's durable testing/title-decision lifecycle).

**Stage 4 progress update (J1 booking identity and locked-slot editor):** the
Foundation identity layer now runs after event IDs are assigned and migrates every
missing draft/event fight to a deterministic namespace (`booking:draft:<ordinal>` or
`booking:<event_id>:<ordinal>`). Existing IDs are retained; duplicate IDs receive a
stable suffix; object aliases are assigned once; and no global Foundation counter or
RNG state changes. The return shape of `ensure_foundation_ids` is unchanged. Draft
Review now exposes a **Propose Locked-Slot Change** action only for complete player
draft rows with stable IDs. The proposal stores the booking ID, selected corner,
original participant/fight snapshot and fingerprint, and a bounded deterministic
same-division alternative list with company/world ranks, medical facts, blockers and
cautions. Generation and review are read-only and never reserve, spend, rerun
matchmaking or touch scheduled event fights. Commit revalidates the fingerprint and
live eligibility, replaces exactly one corner, preserves title/tier/plans/main status
and every unaffected fight, appends a replacement-history record, and seals
one Foundation receipt. Repeated commits return that receipt; stale, missing or
changed cards fail closed without mutation. Coverage is now `foundation_regression_test.py`
(14 tests, including the later membership-history assertions) plus
`booking_workbench_regression_test.py` (11 tests); both pass with
`py_compile`, and the existing persistence/UI-data suites remain green. No EXE or
user save was touched. Stage 4 of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (J4 historical-record truth):** the profile history
resolver no longer substitutes an opponent's current record when an archived replay
and saved pre-bout snapshot both lack the at-the-time record. It now keeps the
recorded opponent identity and returns `Not recorded`; a legacy line with no
opponent identity remains `-`. Valid archived replay and `bout_rating_history`
snapshots remain authoritative, including their stored IDs and ranking fields.
`fighter_profile_regression_test.py` adds missing-evidence, valid-snapshot and
identity-safe timeline regressions (19 tests total); compilation and the focused profile suite pass. No
fight outcome, ranking, save schema, EXE or user save was changed. Stage 4 of 6
remains active; **4 major stages remain**.

**Stage 4 progress update (J4 membership-history foundation):** the shared
Foundation now exposes `record_membership_event` and a filtered, paged
`foundation_membership_events` read model. Facts are append-only and linked to
stable fighter/promotion IDs, action (`join`, `leave`, `loan`, `return`), event
reference, effective month/week plus precision, reason and source transaction.
The membership ID is a deterministic hash of the transition identity, so repeated
callbacks return the original fact without consuming simulation RNG or a global
counter. Contract signing/exit hooks record before narrative work; child-promotion
loan, recall and paid-transfer paths record both sides of the roster transition
before roster/identity mutation inside the atomic action. Reads return defensive copies and preserve
unknown future fields. This is deliberately not a retroactive join-date inference:
current imported rosters are represented by the new `known present at migration`
adapter without a fabricated join date. Profile History now shows a compact
Company Timeline with current/closed intervals and an explicit incomplete-coverage
label. A managed full-history window supports as-of Month/Week filtering, title
history context, defensive detail inspection, clipboard copy and explicit JSON export;
refresh never reruns simulation or mutates recorded facts. Live and load-time closed
division reconciliation now vacates each known title holder before release, records
orphaned holder history, and appends a membership leave fact. Free-agent,
automatic-TBA and last-minute replacement signings, academy/regional/generated AI entries, and both
sides of child recall/loan transitions now use the same join/leave boundary. Coverage is now
`foundation_regression_test.py` (15 tests) and
`fighter_profile_regression_test.py` (19 tests), including deduplication, ID linkage,
pagination, unknown-field preservation, no-RNG/no-counter drift, contract-hook
capture, interval projection, migration-label rendering and source coverage for
retirement, AI expiry/cuts, regional exits, academy matching rights, editor removal,
negotiated swaps, closed-division reconciliation and contract-deal paths. Academy matching-right rollback now also
restores the membership collection if a later finance/story step fails. No
completed-bout outcome, ranking, save checksum, EXE or user save was changed;
the repaired departure boundaries intentionally add the missing holder-linked
vacancy/history facts.
The maintained isolated runner completed with `ALL REQUESTED ISOLATED REGRESSION
SUITES PASSED` for Foundation, Profile, Booking, UI-data, Persistence and Narrative;
the final changed modules also compile cleanly. Stage 4 of 6 remains active;
**4 major stages remain**.

### R11 — J6 coaching: one role, one effect and preserved identities

Choose a **hireable Academy Coach role**, appended without altering existing role IDs. Gym head-coach strings remain gym presentation; do not silently turn them into staff employees. Existing saves without a hired coach retain the exact Trainer fallback path. A linked retired-fighter candidate retains the original fighter record and gets a separate staff ID; offer role skill 45 initially, independent of fighting fame. Hiring uses the existing staff quote/terms system; the player may decline. No automatically generated salary offer without the existing market/quote basis.

One effective Academy Coach may supervise one existing development block/cohort. Its bounded new training-quality adjustment is `clamp((effective_staff_quality - 45) × 0.05, -2, +2)` applied once to the Academy trainer-quality input, not to fighter ratings or trait probabilities directly. Do not also substitute the full new staff score into the Trainer fallback; that would double the change. A completed block is the development evidence unit, never a page visit. No new combat/recovery buff or random replacement trait.

A comeback requires explicitly suspending/ending the coaching assignment first; no full-time fighting and coaching credit for the same period. Expiry/departure preserves completed blocks and requires a review of future assignments. Additive role migration and fresh development/native qualification are required before enabling this effect. This resolves the role-versus-gym choice; additional coach specialisations are not in v1.

### R12 — J7/J9 corporate and regional v1 boundaries

J7.a provides structured quotes/history for current transfers/loans with no new acceptance modifier. J7.b's new agreement is limited to a **one-fighter time-bounded development loan between an owned parent and child**, using existing loan protections plus an agreed return date. It cannot include an unrelated third party, new goodwill score or title-merit waiver. Return at the first safe boundary after the last already-committed bout; show the delay. No new fee beyond the existing explicit transfer/loan operation. General bilateral treaties, attacks and spin-off ownership changes are outside v1; future spin-off design must assign each asset/obligation exactly once and may not be implemented through rename.

J9.a feasibility uses existing public/scouted facts and currently signable/bookable candidates; no invented future prices. J9.b's optional invitation is one concrete region/date offer, generated at most once per quarter and only if there is no open invitation. Select deterministically from feasible known venues/regions using the existing assessment then stable region/venue order; opening a page never generates it. The offer expires after four weeks and proposes an event 8–16 weeks ahead. Declining/expiry has no new penalty.

The host guarantee is 10% of the quoted fixed staging/venue component, rounded once, capped at $25,000, paid only after at least two roster fighters whose stored region matches the host region complete bouts at that event. If a reliable fixed-cost quote or two eligible local participants is unavailable, issue no invitation. No extra deposit, travel model or cancellation fine. A cancelled/unfulfilled invitation pays zero, records its outcome, and does not create debt. Use one event entitlement key and existing event finance; future larger invitations require a new version and calibration.

### R13 — J10/J11/J12 comparison, time and conversion decisions

**J10 comparison:** tied values receive the midpoint rank in the displayed visible cohort; show cohort size/date and “known sample” when coverage is incomplete. Suppress numeric percentiles for fewer than ten legitimately visible fighters. Never rank a hidden value. Help is local authored data linked to actual helpers, not generated advice that can contradict rules.

**J11 stopping:** evaluate predicates only after a fully completed week. User Stop finishes that boundary and records it; resumed jobs rebuild from the saved boundary and remaining target, not a partial callback. A failed week is an error, not resumable completed progress. Pinned checkpoints are manual, immutable copies with visible size, and never count as rolling recovery slots. Version/source mismatch blocks automatic resume; ordinary save loading remains separately supported. This is the fixed v1 behaviour, not instant interruption inside a bout.

**J12 conversion:** v1 exports a **new-start database**, not a cloned active save. Preserve fighter IDs/identity, current supported skills/age, records as starting career totals, and current supported roster ownership. Keep detailed career/title history in a labelled provenance section only if the existing database schema supports it; otherwise require export of a companion provenance manifest and explicitly state that it is not imported as playable history. Never discard it silently. Ongoing work, scheduled events, pending offers, unserved disciplinary cases and unsupported new fields prevent “complete conversion”; present an exact exclusion report and require explicit acceptance of the listed exclusions. The live save remains untouched and independently recoverable. Do not change cumulative records again when importing the exported starting totals. No automatic current-career migration or mass rewrite of old archetypes is part of this card.

### R14 — A1/A2 schedules and project-closeout rules

A1.a indexes real schedules without taking control. A1.b is opt-in controlled MMA child scheduling for one future card at a time, no more than one manually committed card per child/game month. The child funds its card from its own wallet. Manual commitment suppresses that child's automatic card in the occupied month; cancellation before execution releases the slot, with AI resuming only at its next ordinary planning boundary. Never create an extra same-week catch-up event. Recall/transfer that would invalidate a committed card requires review; no silent booking substitution. Sport cards keep their existing cadence and native settlement.

A2.a adds a new terms version on new acceptance. New templates map `security` to canonical `security_cost` and `revenue` to `revenue_multiplier` once; persist both original template and canonical accepted snapshot. Already accepted legacy projects retain the effective existing payment path (including missing-key defaults) with an explicit legacy-terms notice. Do not suddenly charge old security or apply an unearned uplift based on today's template. Never alter completed events.

A2.b cancellation rules: a paid approval deposit is non-refundable; unpaid setup/security is not charged; there is no ticket refund without a recorded pre-sale transaction. Cancel before/during planning or after scheduling closes the agreement and its unperformed linked work once. Past campaign costs remain sunk. Expiry occurs at the first week boundary after the last allowed event date if still Planning; Scheduled projects retain their agreed date and use ordinary due execution. No discretionary extension in v1: reschedule within the original window or cancel. No added cancellation fine/safety deduction; existing ordinary completed success/failure effects remain unchanged. A project-only closeout must not clear another active project's reference.

### R15 — A3/A4/A5–A7 forward views and persistent decisions

**A3:** show baseline components and demand scenarios at 80%, 100% and 120% of the pure baseline attendance, bounded to capacity. These are sensitivity assumptions, not likelihood bands. Recompute gate, variable costs and taxes through the same pure components; fixed payments stay fixed. Use an explicit unknown component instead of claiming complete profit where the shared calculator is incomplete. Applying a scenario is v1 **review-only**: link to individual existing editors, no multi-event auto-commit. This removes partial-application ambiguity while retaining a usable planning tool.

**A4:** new achieve-once goals observe actual qualifying business-event completions and week closes; success must occur by deadline inclusively and seals once. Maintenance goals observe at every completed week boundary within their declared interval, not intraday balances; a single miss fails the maintenance condition. Baseline-improvement goals store the accepted starting value and test the net change at deadline. Quarterly reviews are every three game months. Rewards are informational recognition only in v1. Legacy goals show saved legacy status plus separately computed current progress; do not invent historical weekly observations or penalties. Evaluation never depends on opening the page.

**A5:** review date defaults to the authoritative promise/career deadline, not a new independent clock; without one, offer the next month-end review. Acknowledgement/no-action has zero mechanical benefit. Existing support actions retain their existing prices/effects; no deadline extensions or new morale formula. The case closes after resolution/departure with a recorded reason, never by deleting the promise.

**A6:** one pack contains 2–4 candidate IDs, purpose, notes and explicit Considering/Needs report/Ready for negotiation/Archived statuses. Ready means the player's decision state, not guaranteed affordability/signability. Watchlists can contain more fighters; they are not limited to pack size. Archiving removes the pack from active views but preserves its evidence and notes. Candidate changes never auto-hire, update reports for free or rewrite old comparison snapshots.

**A7:** opening a followed-story briefing does not mark it read. Acknowledge updates cursors only through the latest included beat per thread; later unseen beats remain unread. Default catch-up is chronological by last new beat, grouped per thread, with no five-story truncation of unread access—use pagination. Snooze suppresses the notification, not accumulation/history. Pruned source intervals show a coverage gap; do not substitute a contemporary narrative for missing history.

**Stage 4 progress update (J7.a structured company proposals):** the shared
Foundation now stores append-only, ID-linked proposal snapshots for explicit
fighter swaps and parent/child roster moves. Each proposal retains both
company identities, every participating fighter ID and display snapshot,
cash/currency, expiry or recall boundary, terms, warnings and a stable
proposal ID. Status transitions (draft, countered, awaiting fighter terms,
completed, rejected and needs review) preserve the original terms and are
idempotent on repeated clicks. The transfer desk records a proposal before the
first board roll and carries its ID through fighter contract acceptance; stale
ownership, title, booking or cash checks seal the proposal as Needs review
without substituting another fighter. The child-promotion manager now asks for
explicit confirmation before loan, recall or paid parent transfer, stores the
same proposal evidence and exposes a read-only Company Proposal Ledger with
status filtering and full warnings/outcome details. Existing board, contract,
loan, recall, buyout, finance, belt and membership mechanics remain the domain
owners; no new acceptance modifier, fee, goodwill score or automatic transfer
was added. `foundation_regression_test.py` (18 tests) now covers stable proposal IDs,
defensive reads, no-RNG/no-counter drift, terminal idempotency and retained
fighter identities; the focused Foundation, Booking, Profile, UI-data,
Persistence and Narrative runner passes. J7.b's bounded return-date loan is
now implemented in the follow-up below; general treaties and
ownership/spin-off rules remain held. Stage 4 of 6 remains active; **4 major
stages remain**.

**Stage 4 progress update (J4 retention/load evidence):** the membership
read model now exposes a non-mutating retention summary for the portable save:
retained row count versus the 10,000-fact bound, unique/duplicate IDs, fighter
and company coverage, known versus migration-unknown dates, and oldest/newest
known months. The full Company History window surfaces that coverage beside
the selected fighter and keeps incomplete migration dates explicit. This is
diagnostic evidence only; it does not trim facts, create an external sidecar,
or change the save schema. The new Foundation regression covers unknown-date
gaps, stable counts and state immutability; Foundation/Profile/Persistence and
the real Tk history-window probe remain green (the maintained smoke path also
passed immediately before this read-model-only addition). An explicit measured
retention policy and any future archive format are still required before
compaction is allowed. Stage 4
of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (J9.a regional feasibility review):** Regions now has a
read-only Feasibility Review that is deliberately separate from invitation or
booking generation. `WorldMixin.regional_feasibility_snapshot` takes an explicit
region and as-of Month/Week, then reads only the current player roster, ordinary
date-based availability, stored region/gender/weight/ranking facts, visible
regional free agents, unlocked venues and already scheduled event records. The
review reports active/local/ready roster counts, same-division pairing capacity,
ready champion/top-10 depth, local per-bout purse exposure, known versus
unscouted market options, venue access, scheduled shows, market conditions and
plain-language blockers/assumptions. A Region Hub action opens the managed review
window with six summary cards, evidence and a refresh control; it does not mutate
roster, calendar, finance, proposals, RNG or scouting records. Unknown free agents
remain unknown in Scouting Mode, hidden AI schedules/rankings are not inferred and
no future price is invented. If a division is thin, the review says so and keeps
the normal challenger-merit rule intact rather than waiving eligibility. The
dedicated `regional_feasibility_regression_test.py` covers deterministic counts,
venue/event-region filtering, public/scouted visibility, no-RNG/no-state drift and
the thin-division merit blocker; the real Tk window probe also passes. J9.b
quarterly invitations, guaranteed host economics and any new regional commitment
remain held for a later decision and balance pass. Stage 4 of 6 remains active;
**4 major stages remain**.

**Stage 4 progress update (G5 title-decision resume guard):** official weigh-in
snapshots can now survive an interruption between recording the scale evidence
and the player's choice. `EventMixin.run_weigh_ins` recognises an
`awaiting_player` `title_miss_decision_state`, resolves the saved corner IDs and
miss amounts, and resumes the existing choice dialog without calling
`perform_weigh_in` or charging a second miss fine. Terminal `resolved`,
`rebooked`, `cancelled` and `needs_review` states are also idempotent after
reload: the original evidence is rendered once, cancellation/review state is
restored when needed and no title vacancy, replacement, prompt or additional
scale roll is repeated. An unresolvable saved corner fails closed into a
reviewable cancellation rather than substituting a same-name fighter. The
`title_decision_resume_regression_test.py` suite covers pending Keep Belt resume,
terminal reload, no-weigh-in-call, no-fine and no-RNG guarantees; the existing
last-minute replacement, fight-engine and focused profile/persistence suites
remain green. This is the interruption/idempotency foundation only: the full
save-boundary UI, challenger/both-miss matrix, AI/spectator policy, rebooking
editor and drug-testing lifecycle remain gated G5 work. Stage 4 of 6 remains
active; **4 major stages remain**.

**Stage 4 progress update (G5 terminal choice idempotency and J9.a eligibility
evidence):** the title-miss decision branch now seals Rebook Fight and Cancel
Fight before returning the cancelled bout. A reload therefore replays the
recorded weigh-in/cancellation evidence without a second scale roll, fine,
rebooking queue entry or prompt; both terminal choices are covered by the
seven-test `title_decision_resume_regression_test.py` suite. The Regional
Feasibility read model now reuses the live booking workbench hard-blocker
adapter when available, so future bookings, closed divisions and other
ordinary conflicts are not counted as bookable pairings; ready-versus-blocked
counts remain separate and older/read-only harnesses keep their safe fallback.
Regional free-agent counts now exclude retired, injured, already-offered and
non-MMA entries and honour the selected as-of date when the existing date
checker is available. The regional suite is now 3 tests and remains RNG/state
pure. No invitation, title-outcome, testing-sanction or new fee rule was
enabled. Stage 4 of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (J4 duplicate-name title-holder guard):** legacy belt
maps still store a display name for compatibility, but `vacate_fighter_belts`
now requires the departing fighter to be the live champion/interim holder or
the sole matching name on that roster before clearing the belt. A same-name
non-holder can leave without creating a false vacancy; the actual holder's
departure still records an ID-linked `Vacated`/`Interim Vacated` fact. The
profile regression now covers this duplicate-name case (20 tests), alongside
the existing lineage, membership and archived-record checks. No belt schema,
title result or saved career was rewritten. Stage 4 of 6 remains active;
**4 major stages remain**.

**Stage 4 progress update (J4 retention boundary):** membership transitions are
now genuinely append-only in the portable foundation. The previous writer's
implicit `rows[-10000:]` slice was removed, so a long-running career no longer
silently loses older company facts. Ten thousand remains a visible diagnostic
threshold (`within_limit` becomes false above it), not a destructive policy;
any future compaction or sidecar must be explicitly versioned and recoverable.
The interval read model now pages through the complete retained collection
before applying as-of filtering and returns a generous presentation cap, while
the per-page API remains bounded for UI responsiveness. A 10,001-row regression
proves the final fact, retention warning and full interval projection survive;
Foundation coverage is now 19 tests. Stage 4 of 6 remains active; **4 major
stages remain**.

**Stage 4 progress update (G5 Keep Belt enforcement):** the confirmed Keep Belt
choice now prevents the later generic weight-miss path from downgrading the
scheduled contest to catchweight/non-title. The explicit sanction snapshot,
title and divisional-title flags remain on the bout, and a severe double-miss
does not consume the obsolete commission-cancellation RNG roll once the player
has chosen Keep Belt. The title-decision regression now covers single and
double-miss Keep Belt behaviour plus the terminal Rebook/Cancel paths (7
tests). Remove Belt, Rebook, Cancel and Replacement continue to use their
existing explicit branches; unresolved challenger/both-miss policy remains
held. Stage 4 of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (G5 pending-fine evidence):** a pending title-miss
snapshot now carries each missed corner's calculated purse fine and a single
`miss_fine_applied` marker. If preparation is interrupted before the choice,
resume adds that recorded amount exactly once; terminal reloads do not add it
again. Unresolvable pending identities fail closed while still retaining the
known fine evidence for settlement review. Every recorded corner identity is
validated, including a corner that made weight, so a missing non-missed
identity cannot be silently replaced by a same-name/current-roster fighter.
This closes the local weigh-in accounting gap without changing fine rates or
introducing a new draw. The title-decision suite now has 7 tests and the full
fight-engine regression passes. The focused bundle also passes persistence,
foundation (19), last-minute replacement (8), UI/data (33), profile (20) and
regional feasibility (3); `py_compile`, `git diff --check` and the full smoke
test pass (with the known headless Matchmaking-coordinate probe skipped).
Stage 4 of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (J5 compliance case foundation):** manual testing now
creates a stable test/case identity for each sampled fighter and persists the
fighter snapshot, policy, provider-compatibility ID, preliminary result and
evidence scope. A preliminary alert is explicitly informational: it does not
write `injured`, title eligibility or disciplinary state, so a test cannot be
mistaken for a medical injury or a proven violation. The existing policy
accuracy basis, Drug Testing Officer lift and event-accounting cost discount
are unchanged. The `None` policy now exits before sampling, charging or
consuming test RNG. A read-only Drug Testing Cases window exposes the frozen
rows and defensive detail payloads, and the new
`drug_testing_regression_test.py` covers positive/negative evidence,
idempotent case identity, disabled-policy purity and cost/policy snapshots.
The live save round-trip and Tk window probe pass. Provider selection,
confirmation, appeals, sanctions and staff automation remain explicitly gated
until their versioned policy/balance table is approved. Stage 4 of 6 remains
active; **4 major stages remain**.

**Stage 4 progress update (J7.b bounded development-loan return):** the
parent/child loan contract now supports an optional agreed return month/week
without changing the existing parent contract, transfer fee or ownership
rules. The Child Promotions manager asks for the date during loan confirmation
and shows it in the child-roster Return column and selected-fighter detail;
legacy open-ended loans continue to show “parent recall required.” The
fighter date fields are part of the normal dataclass save schema and load
repair clears malformed, orphaned, retired or retirement-pending loan dates.
At each weekly world boundary, after due cards have settled and before new
bookings, the return worker checks the agreed date. A loan with no later
committed child card returns on that boundary through the existing atomic
recall path, preserving belt vacatur, parent/child membership facts and the
Feeder Pathway story while clearing the date. A scheduled child bout on or
after the agreed date holds the fighter until the first boundary after that
commitment and emits one readable Inbox/news delay notice; no replacement,
title waiver, treaty effect, fee or RNG draw is introduced.
`child_promotion_loan_return_regression_test.py` proves save/load round-trip,
pre-date non-return, exact-boundary return, committed-bout delay, attributed
membership/story evidence and RNG purity; the existing child interaction,
48-week long-run, Foundation and Persistence suites also pass. General
bilateral treaties, child manual scheduling, ownership/spin-off allocation
and policy-dependent testing sanctions remain held for later decisions. Stage
4 of 6 remains active; **4 major stages remain**.

**Stage 4 progress update (A4 owner-objective boundary + V14 ranking scope):**
owner-goal rows now have stable IDs, explicit semantics and additive observation/
resolution fields. New-game rows are seeded with those fields; older rows receive
deterministic IDs and an explicit limitation that historical weekly evidence is
unknown. The Inbox goals panel now performs a pure current projection: opening,
refreshing or filtering it cannot create a baseline, start a maintenance window,
record an observation or seal a result. A completed-calendar worker runs after
scheduled cards, finance and monthly business work, evaluates each non-terminal
goal against the inclusive completed boundary, records one observation and emits
one idempotent Inbox/news explanation when a goal completes or fails. Show goals
use the canonical company-event count where available, and no reward, penalty,
RNG draw or retroactive legacy failure was introduced. The owner-goal suite now
covers preview purity, exact-boundary completion, late failure and repeated
boundary idempotency.

Rankings now label **matching** rows separately from **shown** rows in the scope
summary cards. The distinction is explicit for the 50-row pound-for-pound cap and
75-row division cap (company boards report both counts), while the selected-row
detail, stable identity resolution, scouting visibility and underlying ranking
order remain unchanged. The focused UI-data, owner-goal and persistence suites
pass; Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 staff execution/evidence gates and G5 durable testing/title
decision lifecycle).

**Stage 4 progress update (G5 replacement fail-closed boundary):** a selected
short-notice title replacement now has an explicit terminal safety path when its
identity is stale, cannot be resolved after commit, or misses the scale itself.
The bout is marked `needs_review` and returned in the cancelled/preparation
ledger with the original corners, replacement identity, miss amount, title
sanction snapshot and the existing one-time purse fine. A second scale roll,
automatic catchweight conversion, duplicate prompt or duplicate fine is not
allowed after reload. This is a lifecycle/integrity guard, not a new testing or
title-merit rule; a future approved policy can resolve the saved review. The
title-decision suite now covers invalid selection and second-miss replacement
paths. Stage 4 of 6 remains active with **4 major stages remaining**.

**Stage 4 progress update (G5 testing-desk contract + Staff evidence):** the
first J5 provider/policy boundary is now implemented as `drug_testing_catalogue.py`.
Three stable authored provider IDs expose tier, coverage, effectiveness label,
turnaround, confirmation posture and a deterministic cost multiplier; four
existing policy IDs expose strictness and coverage language. The new
`drug_testing_quote` adapter is read-only and RNG-free, clearly marks the quote
as planning-only, and prices the more effective authored tiers higher for the
same sample count. Provider and sample selection persist in the existing
`drug_testing_state` envelope with a configuration revision; invalid selections
fail closed and legacy states retain the compatibility provider. The Company
Editor and Staff pages now open a Testing Desk comparison window with policy,
sample count, provider selection and quote, while explicitly stating that the
live compatibility resolver is unchanged until confirmation/appeal/sanction
rules are approved. Drug Testing Officer now has a read-only
`testing_case_review` recommendation handler that returns frozen cases,
provider/policy context and the quote without commissioning, charging, drawing
RNG, creating injury or applying a sanction. Coverage is
`drug_testing_catalogue_regression_test.py` (9 tests), the Staff suite (24),
the existing drug-testing suite (4), UI-data (34), persistence and smoke; all
pass. No provider-specific screening outcome, confirmation, appeal, sanction,
AI automation or EXE/user save change was introduced. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (V01 Dashboard notice identity):** the Promoter
Dashboard decision queue now assigns each notice a deterministic content-bound
read-model identity and restores the selected row after refresh/reordering.
The detail panel and action route read the stored row mapping, so a stale list
index cannot open a different context. If the underlying advice text changes,
the notice intentionally becomes a new projection; no source text, priority or
route was rewritten. `ui_data_regression_test.py` covers stable and changed
notice identities. Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 progress update (G3 broadcaster account review):** Media Rights now
includes a compact, read-only broadcaster account review beneath the active
contract summary. It reports delivered versus recorded events, the remaining
event quota, breach strikes, renewal timing, the first recorded shortfalls and
whether a successor offer/contract is queued. It reads only saved audience and
contract evidence; opening or refreshing the page cannot settle delivery,
repair a contract, regenerate offers or alter RNG. `ui_data_regression_test.py`
covers the panel and source fields. The combined release-safety group passes
**211 tests**; Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 progress update (S2 autonomy scope projection):** the Staff policy
controls now project the effective saved mode for the selected scope. Company
default shows the global autonomy mode; selecting Marketing, Matchmaking,
Scouting or another department shows that department's override immediately,
and a panel refresh keeps the same scope. Applying a policy therefore cannot
silently edit a different level than the player selected. The four modes remain
player-controlled, with the existing capability matrix and guardrails unchanged.
`staff_management_regression_test.py` covers both override and company-default
projection. Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 progress update (U07 semantic status colours):** the shared UI palette
now derives positive, negative, warning, information and neutral row colours
from the active table surface. Fight History, Scouting and Sponsor tables use
these semantic IDs instead of fixed pale accents; the live retheme pass updates
the known Treeview tags when switching between dark and light themes while
leaving row values, selection and unknown authored tags untouched. Status words
remain present, so colour is an additional cue rather than the only meaning.
Lazy-built screens receive the same semantic pass immediately after construction,
so opening a page after a theme change cannot reintroduce fixed dark-theme
accents.
Known Assistant and Event Log Text tags are included in that pass; authored
headings and transcript content remain untouched.
`ui_data_regression_test.py` covers the WCAG contrast floor for both surface
families, and `fight_night_layout_regression_test.py` verifies a live theme
switch updates a semantic Treeview tag. The focused suite passes (65 tests),
`py_compile` passes, and no save schema, simulation, RNG, finance, title, native
release or EXE change was introduced. Stage 4 of 6 remains active; **4 major
stages remain** (G2/G3 completion, G4 Staff execution and evidence gates, and
G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (U07 coverage and contrast guard):** the semantic
registry now also covers unread inbox rows, owned/available finance entries,
readiness and scouting-strength states, ranking movement and injury indicators.
Treeview tags that carry an authored dark background are checked before the
foreground is replaced; a palette candidate is applied only when it remains
WCAG-readable against that row background, otherwise the existing authored
light foreground is preserved. This keeps warning, recommendation and medical
rows legible in both theme families while retaining their explicit status text.
Secondary Staff, booking, contract and read-only history statuses (ready,
preserved, partial, review, open, booked and closed) are included in the same
registry, so newly opened pages do not reintroduce fixed accents.
The live-tag regression now exercises a dark-background status as well as a
foreground-only status. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).

**Stage 4 progress update (V08 legacy-envelope purity):** the Media Desk now
uses a non-mutating finance reader for KPI, plan-summary and offer-target
repaints. Legacy finance defaults and foundation IDs are no longer seeded by
opening or filtering the page; explicit plan creation/commit remains the
boundary that can normalise durable state. The focused media/UI/performance
bundle passes **79 tests** after this slice. Stage 4 of 6 remains active with
**4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

The J5 evidence contract is now frozen per case as well: each screening row
stores the provider snapshot/version, policy snapshot/version, sample count,
configuration context and the actual total paid alongside its preliminary
result. Case detail shows this as a readable timeline before the complete
payload. Retried reads remain defensive, and later configuration changes do
not rewrite earlier evidence. The provider selection and case evidence also
round-trip through the existing atomic save/load transport. Disabled policy quotes explicitly resolve to zero
samples and zero cost, preventing the comparison UI from presenting a charge
for an off setting. The legacy seeded `Enhanced` policy label is preserved in
quotes rather than silently being relabelled as Standard. Each case now has a
pure workflow projection that separates collection, preliminary alert,
confirmation, appeal and final-outcome stages, with gated next actions shown
without inventing sanctions or sporting effects.

The testing ledger now consumes one shared `drug_testing_case_read_model` for
the cases page and the Drug Testing Officer review. It adds stable display
labels for collection boundary, provider/tier, policy, screening result,
workflow state and the next available action, while retaining the complete
stored evidence and nested workflow projection. Search and status filtering
are identity-safe and operate on the frozen case rows; they do not rerun a
screen, draw RNG or alter a case. The cases table consequently shows the
decision-relevant summary before the player opens the full payload, and staff
recommendations use the same labels rather than maintaining a second ledger
interpretation. `drug_testing_catalogue_regression_test.py` now covers this
filtering/defensive projection (9 tests total), alongside the existing Staff
(24), UI-data, persistence and smoke checks. Provider-specific outcomes,
confirmation, appeals, sanctions, AI automation, title consequences and the
EXE remain intentionally gated. Stage 4 of 6 remains active with **4 major
stages remaining**.

The provider comparison also exposes the selected provider's supported panels,
confirmation posture, false-positive handling and authored notes beneath the
comparison grid. The current selection is visibly highlighted after refresh,
so the quote and explanatory detail cannot drift away from the row the player
is evaluating. This remains a planning/read-model enhancement: it adds no
provider-specific screening draw or charge.

The Broadcast Producer review adapter now returns a fuller production evidence
card: resolved tier and quality, contracted minimum, readiness assessment,
venue/region, bout count, settlement status and the existing cost basis. It
reuses the current production-quality resolver when available and falls back
to a disclosed baseline without writing event state. This gives Staff advice
the same evidence needed for the Media rights delivery decision while keeping
the automation flag off; no production spend, card edit or rights outcome is
created by a review.

The approved last-minute replacement picker now applies title eligibility at
the candidate-read-model boundary. A ready fighter is omitted from a title
replacement dropdown when the existing challenger-merit owner rejects the
record; if that owner is unavailable, the title picker fails closed instead
of labelling an unqualified fighter Ready. Replacing a champion remains a
separate, explicit path because the existing title workflow removes that
corner from the contest rather than treating the replacement as a challenger.
The commit path repeats the same check before mutation. The replacement suite
now covers this filtering and retains the existing ranking, duplicate-name,
stale-selection and save-safe cases (10 tests); no new title result, vacancy or
ranking calculation is introduced.

The same decision surface now explains the filtered result instead of leaving
the player to infer it from rank columns: when challenger merit is required,
each visible row carries a `Title eligible` label and the status line says how
many title-eligible challenger options remain. If the missed corner is a
champion, the dialog instead calls the rows title replacement options because
the replacement is not being scored as a challenger. Empty states retain the
existing fail-closed wording. This is a presentation-only projection over the
already filtered rows; it does not rerun eligibility, ranking, weigh-in or RNG
logic, and the established champion/non-challenger path remains authoritative.

The same dialog now labels each missed corner with its fighter name and saved
corner number, then resolves the selected missed fighter by stable ID before
choosing the challenger-merit wording. Duplicate names therefore cannot cause
the title explanation to follow the wrong corner; name-only legacy rows retain
the existing deterministic fallback. This remains presentation-only and does
not alter the replacement or title owners.

The Staff execution seam now honours the calendar boundary contract. The
weekly worker was moved out of the pre-settlement world-step list and is queued
after scheduled cards, finance and month-end business tasks. `calendar_week_steps`
passes the completed month/week to `process_staff_autonomy_boundary`, which
records advice/execution against the period that actually completed even if the
calendar has already rolled to the next week or month. Direct isolated callers
keep the current-date default. `staff_management_regression_test.py` now covers
both ordinary and month-end ordering (28 tests), including the owner-goal step
remaining after Staff work; no new handler, spend rule or RNG draw was added.
The same worker now fails closed in Spectator mode: committed briefs remain
saved but neither Recommendations nor Full Auto is evaluated during unattended
fast-forward. The Staff/simulation regression bundle covers this no-authority
path (36 tests combined), preserving the existing no-routine-prompt spectator
behaviour.
The Marketing commit path now also enforces each brief's saved spend ceiling
before calling Media: the pure quote is rejected as Needs attention when it
exceeds that cap, and the resolver/cash path is not entered. The generic worker
rechecks the ceiling against returned spend for injected handlers as a second
boundary. `staff_management_regression_test.py` now covers this over-cap case
(28 tests); no new budget, resolver or RNG rule was introduced.

The Fight Night archive now also makes the legacy preparation coverage gap
reachable instead of silently hiding it. When a historical package has no
`preparation_timeline`, the Preparation tab contains a muted selectable
“Unavailable: no preparation timeline retained” row; selecting it renders the
explicit unavailable message. The result-card Preparation action remains
available for the same reason. This is an additive reader affordance only: it
does not invent stage states, readiness, press or weigh-in outcomes, alter the
package, or rerun any event work. `fight_night_archive_regression_test.py` now
covers both the recorded-stage and legacy-unavailable paths (5 tests).

The World Hub refresh path was also tightened to honour the read-only page
contract. It no longer calls `sync_gym_membership` while rebuilding the
promotion/gym tables, so navigation and full header repaint cannot rewrite gym
member counts or apply opening-capacity repair. Calendar advancement and
explicit gym mutation/view paths remain the synchronization owners. The UI-data
suite now guards this boundary (35 tests) while the existing gym-capacity
regression continues to cover the authoritative synchronization helper.

The maintained full runner was also exercised after the latest source slice.
Every suite through the commercial, Staff, UI, persistence, smoke and fight
mechanics checks passed until `fight_move_selection_parity_regression_test.py`.
That existing historical-fixture gate reported one failure:
`test_historical_refactor_evidence_remains_exact_with_original_content`
(`Selection parity changed: bouts`). The testing/read-model and production
review changes do not touch the move-selection modules; the failure is retained
as an unresolved source-bound diagnostic rather than waived or called green.

**Stage 4 progress update (S2 autonomy scope):** the four player-selected
autonomy modes now have distinct recommendation semantics. Broad
**Recommendations** reviews every authored read-only action registered for a
department. **Selective Recommendations** reviews only the action IDs the
player explicitly placed on that brief; an explicitly requested mutating action
is rejected with a visible Needs attention result rather than being silently
run or replaced. Marketing campaign commit therefore remains Full Auto-only,
and still passes the existing lead, permission, pure quote, capacity, brief
ceiling, monthly ceiling and cash-reserve checks before Media can mutate state.
Legacy briefs without an action keep their safe read-only default. The scope is
also visible in the Staff capability grid's Review actions column. Its viewport
fits all seven registered departments, so lower capabilities are not silently
clipped. The change is isolated to `staff_management.py` and `ui.py`, and
covered by two new regression cases in `staff_management_regression_test.py`
(30 tests total); no save schema,
simulation, RNG, finance or EXE change was introduced. Stage 4 of 6 remains
active; **4 major stages remain** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (U12 honest sponsor valuation):** the Sponsor Market
offer card now separates the contracted maximum fee per eligible event from the
current activation-adjusted estimate and the remaining term. It reports the
same full/half-fee basis used by settlement and gives the exact current
readiness reason (trust, stability, ranked-campaign evidence or monthly-event
requirement) instead of presenting fee × months as guaranteed income. The
legacy `annual` assessment field remains for compatibility, but it is no longer
the primary UI label. The activation preview reads existing finance, roster and
campaign facts directly; it does not normalise state, refresh offers, spend,
settle or draw RNG. `media_system_test.py` now covers maximum/estimate
separation and an at-risk readiness case. Stage 4 of 6 remains active with
**4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (G4 Staff receipt identity):** the Staff work-receipt
table now keys visible cards by their saved foundation operation ID or original
work ID. Refreshing after new advice or completed work therefore retains the
same evidence selection and detail payload; duplicate source identities receive
deterministic UI suffixes without changing the receipt ledger. Identity-less
legacy fallback cards remain display-only and are not presented as durable
history. `staff_management_regression_test.py` covers operation selection
retention and legacy fallback IDs. Stage 4 of 6 remains active with **4 major
stages remaining** (G2/G3 completion, G4 Staff execution and evidence gates,
and G5 durable testing/title-decision lifecycle).

**Latest Stage 4 status:** the current implementation ledger includes the M2
rights lifecycle/evidence-identity and J4 membership-retention-warning slices
described above. The latest combined verification bundle passes **255 tests**;
`py_compile` and `git diff --check` are clean. Stage 4 of 6 remains active with
**4 major stages remaining** (G2/G3 completion, G4 Staff execution and evidence
gates, and G5 durable testing/title-decision lifecycle). No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (A3 revenue-mix history reader):** The Finance
revenue-mix projection now treats malformed archive, weekly-history,
transaction and month values as unavailable rows instead of crashing or
coercing the retained envelope. Valid event streams and non-event revenue
remain separated, duplicate transaction IDs are still excluded, and the
source finance/archive objects are untouched. The cash-runway/revenue-reader
regression bundle passes **13 tests**, with clean compilation and diff checks.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 identity follow-up (Simulation Lab corner selectors):** Red and Blue
corner comboboxes now keep a retained label-to-fighter map. Duplicate names are
shown with gender, division and identity context, and profile/scouting/quick
simulation actions resolve the selected fighter object rather than calling a
name-only first-match lookup. Legacy labels are accepted only when exactly one
career has that name; equal-name careers fail closed. This remains a sandbox
reader/simulation path and does not alter saved careers or records. The focused
UI-data identity check passes with clean compilation. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 scheduling identity follow-up (event projection boundary):** event
scheduling, cancellation and immediate-run snapshots now resolve participant
references through `_resolve_event_fighter`, preferring saved IDs and failing
closed on ambiguous legacy names. Conflict labels, camp reset, availability
checks and copied `fighter_ids` therefore remain attached to the original
career through cancellation, reorder and run paths. The existing title,
replacement, rebooking and finance owners remain unchanged. Focused event,
replacement, rebooking, title-decision and UI checks pass (**26 tests**) with
clean compilation. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 scheduling-reader follow-up (legacy fighter identity failures):**
Scheduled-card conflict repair and earliest-valid-date checks now use a shared
safe event fighter resolver. Saved IDs remain authoritative; duplicate or
missing legacy names produce explicit unavailable scheduling feedback and do
not crash the reader or mutate a card corner. Valid conflict repair still uses
the existing TBA downgrade and title-stake owner, with no new finance, camp,
RNG or settlement behaviour. The event, replacement, rebooking and title
decision regressions pass (**25 tests**) with clean compilation. Stage 4 remains
active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (event-derived readers):** event atmosphere and
settlement championship-value calculations now consume the same stable
participant projection used by scheduling, cancellation and immediate-run
snapshots. Aligned `fighter_ids` are authoritative; a missing or ambiguous
legacy name is omitted from the derived read rather than rebound to the first
same-named career. Tournament entrants and ordinary two-corner bouts remain
supported, and the existing event economics/settlement formulas are unchanged
for fully resolved cards. The event, replacement, rebooking, title-decision,
full UI-data (**192 tests**) and smoke suites pass, including the documented
headless Matchmaking probe skip. Stage 4 remains active with **4 major gates**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 identity follow-up (division and card-editor actions):** closing a
player division now matches booked and scheduled corners by saved fighter ID,
not by the visible name set; purse exposure and removals therefore cannot
include a duplicate same-named career. Special-belt vacate/delete actions use
the saved `holder_id`, accept a name-only fallback only for one retained match,
and clear the holder identity when the belt is vacated. Matchmaking card
refresh, Compare and automatic event naming now project unresolved/ambiguous
legacy corners as an explicit unavailable row or label instead of raising or
selecting the first name match. The action owners, title lineage and card
economics remain unchanged for valid identities. Full UI-data (**192 tests**),
event/replacement/rebooking/title-decision (**25 tests**) and smoke suites pass;
the documented headless Matchmaking probe remains the only skip. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Matchmaking tournament corner safeguards):**
Tournament Field Review, Fill TBA and Toggle Title now resolve each corner via
the saved fighter identity and fail closed with a booking-surface notice when
only an ambiguous legacy name remains. Review rows show an unavailable entrant
instead of raising; mutation handlers leave the card unchanged until the
identity is repaired or refreshed. No booking, title, finance, camp, RNG or
save state changes occur on the failed path. The focused UI-data routing test
and clean compilation pass. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 identity follow-up (Super-event readiness readers):** super-event
readiness and card validation now resolve each booked corner through its saved
`fighter_id` before considering a legacy display name. Ambiguous same-name
legacy corners are treated as unavailable rather than raising during a page
read or crediting the first career; valid ID-linked duplicate-name corners
remain distinct. The helper is observational and does not alter booking,
finance, title or RNG state. `super_event_closeout_regression_test.py` now
covers ID-linked duplicates and ambiguous legacy rows; all 19 tests pass with
clean compilation. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 identity follow-up (Simulation Lab tournament selections):** the
Simulation Lab tournament Listbox now retains source-bound fighter row keys
and a key-to-fighter map across filter refreshes. Draw & Seed selects those
keys, and tournament execution resolves the original fighter objects directly
instead of reading display names and calling a first-match resolver. A legacy
widget may restore a name only when that name is unique in the refreshed
source list; duplicate names remain visible but are not silently reassociated.
The sandbox remains non-persistent and does not change career records. The
UI-data suite now covers the source-map contract and passes **192 tests** with
clean compilation. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 presentation follow-up (G5 case workflow):** the read-only Drug
Testing Cases ledger now reports aggregate samples collected, recorded testing
spend and unresolved review count alongside the existing case totals. Selecting
a case updates a five-stage visual timeline for collection, preliminary
screening, confirmation, review/appeal and final outcome; the status words stay
visible and theme-derived colours are only an additional cue. Staff now exposes
a direct **Testing Cases** route beside Run Drug Tests and Testing Providers,
so the player's compliance review and the Drug Testing Officer recommendation
open the same frozen case read model. `drug_testing_case_read_model` adds
defensive recorded-total and next-action labels without changing saved evidence.
The focused testing/Staff/UI set passes **109 tests**, and the broader release-
safety bundle passes **270 tests**; `py_compile` and `git diff --check` are
clean. Provider-specific screening, confirmation, appeals, sanctions, AI or
spectator automation and title consequences remain gated by the approved J5
policy/balance tables. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution/evidence gates and G5
durable testing/title-decision lifecycle). No EXE or user save was rebuilt or
modified.

**Latest Stage 4 integrity status:** the M2 settlement boundary also enriches a
copy of legacy/manual outcomes with active outlet and contract IDs when known,
without mutating caller input or inventing identity. The latest combined
verification bundle passes **253 tests**; `py_compile` and `git diff --check`
are clean. Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 legacy outcome identity):** the commercial
settlement boundary now copies and enriches legacy/manual outcome dictionaries
from the active rights contract when IDs are available. This keeps outlet and
contract identity in the saved audience row and receipt without mutating the
caller-provided object or guessing from a mutable UI row. The focused Media
and Foundation checks plus the broader bundle pass **253 tests**. Stage 4 of 6
remains active with **4 major stages remaining** (G2/G3 completion, G4 Staff
execution and evidence gates, and G5 durable testing/title-decision lifecycle).
No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Inbox duplicate-name safety):** Inbox action
resolution now honours a saved `fighter_id` first and only uses a name-only
legacy fallback when exactly one retained career matches. Duplicate same-name
fighters therefore leave the message unresolved instead of opening or
evaluating the first roster/free-agent/retired row. The UI's related-fighter
reader follows the same rule, while saved message/source identity and all
medical/contract action owners remain unchanged. The UI-data suite passes
**191 tests**, smoke passes with only the documented headless Matchmaking
coordinate probe skipped, and compilation is clean. No EXE or user save was
rebuilt or modified. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated.

**Stage 4 identity follow-up (legacy Academy actions):** the compatibility
Academy window now captures the selected lead/prospect source object and routes
Sign, Pass, Profile, Training, Promote and Release through that retained
identity. A unique saved `prospect_id` is the only detached compatibility
fallback; duplicate or missing identities fail closed instead of using the
current Listbox position. Refreshes restore the same visible source where it
still exists, while the managed Academy page and saved recruitment/training
semantics remain unchanged. `ui_data_regression_test.py` and the Academy coach
suite pass (**194 focused tests**); smoke also passes with only the documented
headless Matchmaking coordinate probe skipped. No EXE or user save was rebuilt
or modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 progress update (S3 progression evidence gate):** executed Staff
work rows now persist the handler's explicit `progression_eligible` decision.
Quarter-close skill growth counts only rows marked true, so paid work marked
non-progression and legacy rows with no evidence remain non-qualifying instead
of receiving an inferred skill credit. Added a regression for paid non-
progression work and preserved the existing three-month/two-target rule. The
combined verification bundle passes **254 tests**; Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle). No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (M2 terminal-contract history reader):** Media Rights
now exposes a bounded, read-only projection of saved contract rows for the desk
summary. Fulfilled, shortfall-expired and terminated agreements remain visible
after the active package ends, with stable IDs, remaining entitlements and
delivery strikes; no state repair or list-position inference occurs. The latest
combined verification bundle passes **255 tests**. Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle). No EXE or
user save was rebuilt or modified.

The maintained full runner subsequently passed all suites through the broader
UI/Media/Staff coverage, but stopped at the native historical selection-parity
gate on `Selection parity changed: bouts`. This is retained as a native
diagnostic; no certificate exception was widened and the focused 253-test
bundle remains green.

**Stage 4 progress update (M2/M3 receipt identity):** the settlement receipt
reader now keys each visible row by its saved `receipt_id` or `event_id`, and
restores selection by that identity after a refresh. A newly inserted settlement
therefore cannot make the player inspect a different historical event merely
because list indexes shifted. Duplicate source identities receive deterministic
UI suffixes without changing saved data. Legacy receipts with neither durable
ID remain readable under an explicit UI-only marker; the detail reader keeps
the complete stored payload and says that re-association is unavailable rather
than guessing an identity. `media_plan_regression_test.py` now covers identity
retention, legacy markers and the pure read-model path. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (G2 Results archive identity):** the Results landing
table now uses each saved result archive's `record_id` or `key` for its visible
row identity. Filter changes and insertion of a newer result therefore retain
the same selected event and detail payload instead of following a mutable list
position. Duplicate source identities receive deterministic UI suffixes without
altering archive data. Rows reconstructed from identity-less legacy shelves
retain a positional display fallback and are not presented as durable history.
`ui_data_regression_test.py` covers the saved-identity refresh path alongside
the existing legacy filter path. Stage 4 of 6 remains active with **4 major
stages remaining** (G2/G3 completion, G4 Staff execution and evidence gates,
and G5 durable testing/title-decision lifecycle).
The final release-safety pass for this slice also passed 121 focused Fight
Night/profile/media/UI/persistence tests, plus the standalone media-system and
full smoke checks; `py_compile` and `git diff --check` are clean.
The media regression also snapshots the finance envelope and RNG state around
offer assessment, proving that the richer card remains an observational read.
At settlement, the existing sponsor owner now receives the settled event as
evidence for the “Deliver at least one event each month” requirement, so the
offer estimate and the receipt use the same full/half-fee decision. No new
penalty or obligation was added.

**Stage 4 progress update (G2 Matchmaking stacked geometry):** at laptop
widths, the vertically stacked booking workspace now reserves a compact draft
card pane and leaves the fighter explorer with at least four readable rows at
1280×760. The draft card still keeps its own table and action controls, while
the fighter list remains the primary selection surface instead of collapsing to
a 45px strip. `g0_repair_regression_test.py` now passes its stacked-layout
geometry assertion alongside the media and UI checks (53 tests in the combined
focused run). No booking identity, candidate order, card state, simulation,
RNG, finance, title, save or EXE behaviour changed. Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (U13 Combat Sports contract identity):** the Combat
Sports contract ledger no longer keys rows by their filtered display index.
Each row now uses the stable sport/fighter identity, and the selected athlete
is restored after a refresh or shared expiry-filter change when still visible.
If corrupted source data produces a duplicate identity, the first row keeps
the canonical key and later rows receive deterministic duplicate suffixes so
all retained contracts remain visible and actionable. No contract terms,
ownership, payroll or renewal rules changed; this is an identity-safe
presentation repair. `ui_data_regression_test.py` covers the stable-key,
selection-restoration and duplicate-row contract. Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (G2 Matchmaking timer lifecycle):** delayed vertical
pane placement and scroll-region refreshes now use one cancellable timer per
purpose. Cancellation is performed through the widget that registered the
callback, removing its Tcl command from Tkinter's cleanup list; destroy guards
also tolerate a close racing the timer. This eliminates the prior invalid
command errors when the Matchmaking page was rebuilt or the test window closed,
without changing card order, selection, or scheduling mechanics.
`ui_data_regression_test.py` covers the cancellation/helper contract and the
stacked G0 teardown now completes without Tcl errors. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).
The final focused release-safety run passed 123 tests and the post-fix full
smoke test passed with only the documented headless Matchmaking coordinate
probe skipped; no EXE or user save was rebuilt.

**Stage 4 progress update (G2 Fight Night reader scrolling):** the canvas-backed
Round Read and Bout Desk panels now route mouse-wheel and Linux Button-4/
Button-5 input from their hovered labels and frames to the panel's own vertical
canvas. Native text/list/tree widgets and the separate action timeline retain
their existing handlers, so a wheel event cannot move an unrelated page. The
content and telemetry remain unchanged; this is a scoped presentation repair.
`fight_night_layout_regression_test.py` now grows both readers beyond the
viewport and verifies that hovered content moves the correct canvas without a
callback error. The focused Fight Night/profile/UI suite passes (63 tests) and
`py_compile` passes. No save schema, simulation, RNG, finance, title, native
release or EXE change was introduced. Stage 4 of 6 remains active; **4 major
stages remain** (G2/G3 completion, G4 Staff execution and evidence gates, and
G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (G2 Fight History layout controls):** the Profile
History ledger now has a versioned, save-backed layout envelope in addition to
the existing visibility preference. **Choose Columns** keeps the complete
stable-ID column registry and adds a visible-order list with Move Up/Move Down
controls, a selected-column width editor constrained to 70–360px, Show All and
Career Default actions, and the existing per-field checkboxes. Apply preserves
the player's order for visible fields, appends newly shown fields in canonical
registry order, and retains widths for hidden fields so temporarily hiding a
column cannot erase its layout. Every row value and historical snapshot remains
unchanged; this is a presentation/read-model preference only and does not
reconstruct opponent records or current rankings. `fighter_profile_regression_test.py`
and `ui_data_regression_test.py` cover the layout contract; the focused profile/UI
suite passes (58 tests), and `py_compile` passes. Native Treeview header drags
persist through the same stable layout envelope as the chooser. No save migration, simulation,
RNG, finance, title, native release or EXE change was introduced. Stage 4 of 6
remains active; **4 major stages remain** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).

The Owned Calendar follow-up adds Company, Source and Status filters. Filter
changes rebuild only the read-only projection, preserve the selected event by
stable ID when it remains visible, and report shown rows against the indexed
total. Reset clears those view preferences only. The UI-data contract now
covers the controls and stable-selection path; no schedule, identity, finance
or simulation owner was changed.

**Stage 4 progress update (A1 owned-calendar detail reader):** the existing
Owned Calendar projection now retains participant references and reservation
counts alongside each stable event row. The Dashboard supports selection and
double-click inspection through a managed read-only detail reader showing the
operating company, source sport, date, status, venue, bout count, participant
IDs and legacy identity coverage. It never resolves a fighter, duplicates the
schedule, reruns a card or changes ownership/finance; the owning page remains
the only mutation route. `owned_schedule_regression_test.py` now verifies
participant identity retention and legacy rows, while `ui_data_regression_test.py`
covers the detail-reader contract (38 focused tests total). No save schema,
simulation, RNG, finance or EXE change was introduced. Stage 4 of 6 remains
active; **4 major stages remain** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (U12 honest sponsor valuation):** the Sponsor Market
offer card now separates the contracted maximum fee per eligible event from the
current activation-adjusted estimate and the remaining term. It reports the
same full/half-fee basis used by settlement and gives the exact current
readiness reason (trust, stability, ranked-campaign evidence or monthly-event
requirement) instead of presenting fee × months as guaranteed income. The
legacy `annual` assessment field remains for compatibility, but it is no longer
the primary UI label. The activation preview reads existing finance, roster and
campaign facts directly; it does not normalise state, refresh offers, spend,
settle or draw RNG. `media_system_test.py` now covers maximum/estimate
separation and an at-risk readiness case. Stage 4 of 6 remains active with
**4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).
**Stage 4 progress update (V02 Game & Saves identity and empty states):** the
Game & Saves library now retains its selected save or spectator snapshot by a
normalized path identity instead of a mutable list position. This keeps two
same-named slots in different folders distinct and survives refreshes, folder
filter changes and reorderings; a missing identity fails closed rather than
selecting a different career. The library now explains an empty catalogue or a
filter with no matches, and rows whose sidecar/legacy metadata is unavailable
say so while remaining available to the existing recovery-backed actions. The
new `PersistenceMixin.save_entry_identity`/`save_entry_index` helpers and
`persistence_regression_test.py` cover duplicate-folder identity, reorder
restoration and missing-row safety. Database/world rows use the same
path-bound identity, so similarly named universe files cannot steal a Load DB
or Use Selected Universe action after refresh. The save payload, recovery policy,
load/copy/delete/backup handlers and database targets are unchanged; this is a
read-model/UI slice only. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).
**Stage 4 progress update (G2 storyline reader identity):** the Storylines
reader now keys rows by saved `story_id`/`story_key` and restores the selected
thread when a filter or refresh changes ordering. Legacy threads with no
durable identity receive a clearly non-durable fallback derived from recorded
participants/opening facts when possible; fully unidentifiable rows remain
read-only and never target a mutation from a row index. The detail/follow/context
routes still consume the selected stored thread, and `ui_data_regression_test.py`
covers saved-ID preference plus deterministic legacy identity. This is a
read-model improvement only: narrative beats, subscriptions, RNG and world
state are unchanged. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).
**Stage 4 progress update (V10 MMA Contracts identity):** the MMA Contracts
ledger now captures the selected fighter's stable identity before a filter or
refresh rebuild, then restores that same row when it remains visible. A
filtered-out or departed fighter is left unselected rather than silently
redirecting renewal/release to the next list position. Combat Sports already
uses the same identity contract, so both sport surfaces now agree while the
existing expiry predicates, finance terms and action handlers remain unchanged.
`ui_data_regression_test.py` covers the source contract. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (U13 shared contract filters):** MMA Contracts and
Combat Sports now call one `contract_filter_matches` predicate for the existing
Show options. Expiring/Final month mean calendar-month obligations and exclude
fight-counted comeback or final-retirement deals; Non-Exclusive reads the real
contract flag. Refreshing a filter remains a pure view operation, and identity
selection restoration is preserved on both tables. Regression coverage checks
the boundary and special-obligation cases without changing term ticking,
renewal economics or release behaviour.

**Stage 4 progress update (G2 Chronicle reader identity):** the World Chronicle
dialog now retains its selected entry through story-type filter refreshes using
stored `chronicle_id`/`entry_id`/`story_id` where available. Legacy entries get
an explicitly non-durable fallback, while the existing context/profile route
still reads the currently selected stored row. No chronicle entry, narrative
beat or world state is rewritten; `ui_data_regression_test.py` covers the
identity preference and reorder case. Stage 4 of 6 remains active with **4
major stages remaining** (G2/G3 completion, G4 Staff execution and evidence
gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (V14 Rankings identity):** Rankings now builds
mode/company/fighter-bound row IDs and restores the selected row after scope or
filter refreshes. Company rows remain distinct from fighter rows, duplicate
source identities receive deterministic UI suffixes, and a missing row fails
closed instead of moving the detail pane to another contender. The selected
row's stored company/world rank and scouting-visible values remain the detail
source; rank order and scoring are unchanged. `ui_data_regression_test.py`
covers the identity helper and refresh contract. Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 verification pass (Game/Saves, Contracts, Rankings and readers):**
`persistence_regression_test.py` and `ui_data_regression_test.py` now cover
save/database identity, shared contract filters, MMA contract retention,
Rankings retention, Storylines and World Chronicle identity. The focused
release-safety bundle passed **177 tests**, `py_compile` passed for changed
modules, `git diff --check` reported no whitespace errors, and the full smoke
playtest passed (with only the documented headless Matchmaking click probe
skipped). No EXE or user save was rebuilt or modified. Stage 4 of 6 remains
active with **4 major stages remaining**.
**Stage 4 progress update (V03 Matchmaking selection):** the Available
Fighters table now captures the selected fighter's stable identity before a
date/filter/refresh rebuild and restores that same row when it remains in the
visible eligible set. A fighter who becomes unavailable or is filtered out is
left unselected, preventing Add/Compare actions from drifting to another row.
The existing readiness, title, ranking and booking rules remain the owners of
eligibility; this change only strengthens the read-model selection contract.
`ui_data_regression_test.py` covers the source boundary. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).
**Stage 4 progress update (V11 scouting assignment identity):** the Scouting
Centre now retains the selected report/search row through refreshes. New talent
searches use their saved `assignment_id`; identity-less legacy searches retain
their compatibility key and are never presented as newly durable history.
Malformed duplicate IDs receive deterministic UI suffixes. The assignment
detail/actions still read the current stored row, while search timing, cost,
Scout capacity, dossier visibility and RNG remain unchanged. `scouting_regression_test.py`
and `ui_data_regression_test.py` cover the existing legacy row and saved-ID
source contract. Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).
**Stage 4 progress update (V05 Fight History selection):** the profile Fight
History ledger now keys visible rows by the archived bout/history reference
when one exists and otherwise by a clearly legacy fact fingerprint. Filter and
column-layout refreshes restore the selected bout when it remains visible;
missing or duplicate identities fail safely instead of redirecting opponent or
replay actions. The complete row payload, historical rank snapshots and
scouting visibility remain unchanged. `ui_data_regression_test.py` covers the
identity contract; no history is deleted or reconstructed. Stage 4 of 6 remains
active with **4 major stages remaining** (G2/G3 completion, G4 Staff execution
and evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (V07 sponsor portfolio identity/detail):** active
sponsor agreements now use their saved `agreement_id` (or a deterministic
fingerprint of preserved legacy terms) as the portfolio row identity, while
market offers use their saved offer ID. Duplicate or identity-less legacy rows
receive deterministic UI suffixes; refreshes and offer expiry therefore cannot
move a selection to another partner. Selecting an active agreement opens a
read-only detail card with its fee ceiling, term, agreement ID, stored duty
status and current activation preview, and disables accept/counter/reject until
the player selects a live offer. The offer actions still resolve only through
the saved offer ID, and the refresh path does not pitch, regenerate, spend or
draw RNG. `ui_data_regression_test.py` covers agreement/offer/fallback identity
and the action boundary; the focused media/UI/persistence slice passes 66
tests. No sponsor dictionary, settlement owner, save migration, simulation or
EXE behavior was changed. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).

**Stage 4 progress update (V08 Media Desk refresh purity):** the Media Desk's
weekly capacity card now reads through `media_actions_remaining_readonly`.
A stale saved week marker is reported as a fresh capacity without being written
back merely because the player opened, selected an offer or changed a filter;
the normal campaign commit path still owns marker initialisation and capacity
consumption. The selected-offer quote also reads the existing finance envelope
without state repair, so an informational view cannot normalise a save or
consume simulation state. `media_plan_regression_test.py` covers the stale
marker boundary and the existing offer/settlement tests remain green. Stage 4
of 6 remains active with **4 major stages remaining** (G2/G3 completion, G4
Staff execution and evidence gates, and G5 durable testing/title-decision
lifecycle).

**Stage 4 progress update (V13 company standings scope):** Company standings
now capture the selected row as `(company, sport)` and restore through the same
scope-aware selector. A same-named MMA promotion and combat-sport circuit can
therefore coexist without a refresh moving the detail pane to the wrong entity;
filters and ranking calculations remain unchanged. `ui_data_regression_test.py`
covers the source boundary. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).

**Stage 4 progress update (V13 World Hub gym identity):** World Hub gym rows
now use a saved gym ID when present, or a deterministic name/region fallback
for legacy gyms; duplicate source rows receive safe UI suffixes. A refresh
captures the selected gym's identity and restores it after sorting or changed
membership values, while missing/filtered rows fail closed. The read-only
projection still does not synchronize membership counts or mutate gym data.
`ui_data_regression_test.py` covers the identity helper and source contract.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 verification pass (sponsor/media/debounce follow-up):** the broader
UI, media, profile, staff, persistence, identity, scouting and Fight Night
release-safety group passes **192 tests** after the V07/V08/V13/V19 slices. The
standalone media-system integration check also passes, `py_compile` passes for
changed modules, and `git diff --check` reports no whitespace errors. No EXE or
user save was rebuilt or modified. Stage 4 of 6 remains active with **4 major
stages remaining** (G2/G3 completion, G4 Staff execution and evidence gates,
and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (V19 debounced search lifecycle):** Fighter Search
and Database Editor now cancel pending debounced callbacks when navigation
leaves their page. Scheduled callbacks also check that the owning page is still
active and catch a closing Tk root, so hidden pages cannot repaint from stale
150/200 ms work. The existing debounce delays, 100-row search pagination,
filters and editor identity state remain unchanged. `app_performance_regression_test.py`
covers coalescing and explicit cancellation; the focused bundle now passes 76
tests. Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 verification update (company-scope follow-up):** the combined UI,
media, profile, staff, persistence, identity, scouting and Fight Night
release-safety group now passes **210 tests**. The finance/cash-runway,
contracts and combat-sports follow-up adds **16 passing tests**, and the
standalone media-system integration check still passes. `py_compile` and
`git diff --check` remain clean for the latest changes. No EXE or user save was
rebuilt or modified. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).

**Stage 4 progress update (U08 ranking scope semantics):** Rankings now
change their headers and detail labels with the selected board: Company/World
P4P, Company/World Division, or Company Rank/Scope. The movement column is
limited to the persisted divisional current/previous pair; P4P explicitly says
that a same-scope snapshot is unavailable instead of relabelling divisional
history. Row metadata keeps the selected scope attached to the detail reader,
while ranking calculations, scouting redaction, order and stored fighter data
remain unchanged. `ui_data_regression_test.py` covers the labels and the
scope-specific movement guard. The combined release-safety group passes
**210 tests**. Stage 4 of 6 remains active with **4 major stages remaining**
(G2/G3 completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Latest Stage 4 verification (G3 account-review slice):** the current
combined UI, Media, Staff, profile, persistence, identity, scouting, Finance,
Combat Sports and Fight Night set passes **211 tests**. The standalone media
integration test and `py_compile` also pass, and `git diff --check` reports no
whitespace errors. No EXE or user save was rebuilt or modified. Stage 4 of 6
remains active with **4 major stages remaining** (G2/G3 completion, G4 Staff
execution and evidence gates, and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (S2 partial Full Auto resume):** multi-action Staff
Full Auto briefs now persist `completed_action_ids` alongside their work IDs.
When one action succeeds and a later action fails, `_staff_record_exception`
keeps the brief visibly `Partially completed`; an explicit requeue filters out
the recorded successful actions and retries only the remaining allow-listed
actions. Legacy briefs derive the same completion set from their executed work
rows. This prevents duplicate domain commits, charges and progression credits
while retaining the original exception and work evidence. A no-handler, budget,
permission or resolver failure still fails closed, and all actions must finish
before the brief is sealed `Completed`. `staff_management_regression_test.py`
covers injected mid-brief failure, retry at a later boundary, action-call
counts, work-log identity and final completion. The combined release-safety
group now passes **212 tests**; `media_system_test.py`, `py_compile` and
`git diff --check` also pass. No EXE or user save was rebuilt or modified.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle).

**Stage 4 presentation follow-up (S2 brief progress):** the Staff autonomy
table now exposes an `Actions` progress column (`completed / selected`) next to
the retained work count. It reads the saved allow-list and completed action
IDs, so Draft, Recommendation Ready, partial and Completed briefs explain
their progress without hiding any original fields or changing worker state.
`staff_management_regression_test.py` covers the empty and partial progress
projections. The combined release-safety group now passes **213 tests**;
`py_compile` and `git diff --check` remain clean. No EXE or user save was
rebuilt or modified. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution and evidence gates, and G5
durable testing/title-decision lifecycle).

**Stage 4 integrity follow-up (S2 action identity):** Staff brief creation now
deduplicates the allow-listed action IDs while preserving their first authored
order. This prevents duplicate action attempt keys and duplicate progression
credits, and keeps the `completed / selected` progress column meaningful. The
new regression covers duplicate action input without changing targets, costs
or the saved brief contract. The combined release-safety group now passes
**214 tests**; `py_compile` and `git diff --check` remain clean. No EXE or user
save was rebuilt or modified. Stage 4 of 6 remains active with **4 major
stages remaining** (G2/G3 completion, G4 Staff execution and evidence gates,
and G5 durable testing/title-decision lifecycle).

**Stage 4 progress update (M2 rights lifecycle and evidence identity):** Media
Rights now uses explicit terminal states: a cleanly delivered quota becomes
`Fulfilled`, a term that ends while event entitlements remain becomes `Expired
with shortfall`, and three delivery failures become `Terminated`. A pending
successor activates only at the next calendar boundary after a fulfilled
predecessor; a shortfall or breach marks the successor `Needs review` with a
reason instead of silently overlapping or replacing the failed deal. The prior
legacy-alias migration path was also guarded so a just-terminated contract is
not resurrected as a fresh active package while its settlement receipt is being
written. Media outcomes and commercial receipts now retain outlet and contract
IDs when available, and the account-review reader matches those IDs before
falling back to legacy display names. Added regression coverage for term
shortfall, breach successor blocking, fulfilled successor activation and
identity-preserving receipts; the combined verification bundle passes **218
tests**. Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution and evidence gates, and G5 durable
testing/title-decision lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 progress update (M2 renewal boundary and decision evidence):** the
calendar owner now opens a no-cost renewal offer when an active rights deal
reaches two months or two event entitlements remaining. The offer is prepared
without a refresh-time RNG draw or spend, and a player can still review,
counter, accept or reject it explicitly. Rejected and superseded renewal offers
are retained in the existing offer-history envelope. The account summary now
surfaces a queued successor, a live offer or a `Needs review` successor with its
breach/shortfall reason. Focused Media Rights coverage and the combined bundle
pass **220 tests**; `py_compile` and `git diff --check` remain clean. Stage 4 of
6 remains active with **4 major stages remaining** (G2/G3 completion, G4 Staff
execution and evidence gates, and G5 durable testing/title-decision lifecycle).
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 membership retention warning):** the append-only
Company History read model now returns an explicit threshold notice once the
retained membership collection exceeds 10,000 facts. The UI carries that notice
in the historical-index header while preserving the full collection and its
complete paginated/as-of reader; the threshold remains a review warning, not a
truncation trigger. `foundation_regression_test.py` now asserts the warning on
an 10,001-row fixture. The broader verification bundle passes **252 tests**;
`py_compile` and `git diff --check` remain clean. Stage 4 of 6 remains active
with **4 major stages remaining** (G2/G3 completion, G4 Staff execution and
evidence gates, and G5 durable testing/title-decision lifecycle). No EXE or
user save was rebuilt or modified.

**Stage 4 presentation follow-up (S2 multi-action authoring):** the Staff
brief editor now uses a theme-aware ordered multi-select list for the
department's supported actions. Saving reads every selected action in authored
order, keeps the legacy first-action `StringVar` projection for compatibility,
and falls back to the safe default when nothing is selected. Department
changes rebuild the list without carrying an invalid action across scopes. This
exposes the same allow-list that the worker persists and resumes, rather than
making multi-action support reachable only through an internal caller.
`staff_management_regression_test.py` covers default selection and saving both
Marketing actions in order. The combined release-safety group now passes
**252 tests**; `py_compile` and `git diff --check` remain clean. No EXE or user
save was rebuilt or modified. Stage 4 of 6 remains active with **4 major
stages remaining** (G2/G3 completion, G4 Staff execution and evidence gates,
and G5 durable testing/title-decision lifecycle).

**Latest Stage 4 status:** the current implementation ledger includes the M2
rights lifecycle/evidence-identity and J4 membership-retention-warning slices
described above. The latest combined verification bundle passes **255 tests**;
`py_compile` and `git diff --check` are clean. Stage 4 of 6 remains active with
**4 major stages remaining** (G2/G3 completion, G4 Staff execution and evidence
gates, and G5 durable testing/title-decision lifecycle). No EXE or user save was
rebuilt or modified.

**Latest Stage 4 presentation follow-up (G5 case workflow):** the read-only Drug
Testing Cases ledger now reports aggregate samples collected, recorded testing
spend and unresolved review count alongside the existing case totals. Selecting
a case updates a five-stage visual timeline for collection, preliminary
screening, confirmation, review/appeal and final outcome; the status words stay
visible and theme-derived colours are only an additional cue. Staff now exposes
a direct **Testing Cases** route beside Run Drug Tests and Testing Providers,
so the player's compliance review and the Drug Testing Officer recommendation
open the same frozen case read model. `drug_testing_case_read_model` adds
defensive recorded-total and next-action labels without changing saved evidence.
The focused testing/Staff/UI set passes **109 tests**, and the broader release-
safety bundle passes **270 tests**; `py_compile` and `git diff --check` are
clean. Provider-specific screening, confirmation, appeals, sanctions, AI or
spectator automation and title consequences remain gated by the approved J5
policy/balance tables. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution/evidence gates and G5
durable testing/title-decision lifecycle). No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (G5 testing funds preflight):** manual
compatibility testing now calculates the existing per-sample cost, staff
discount and sample count before selecting fighters or drawing a screening
result. An empty roster or insufficient cash creates a visible deferred-test
notice and leaves cash, RNG, test sequence and case evidence unchanged. This
closes the partial/unfunded testing path without enabling provider-specific
outcomes, confirmation, appeals or sanctions. `drug_testing_regression_test.py`
now covers the no-sampling/no-charge boundary; the focused testing/Staff/UI set
passes **110 tests** and the broader release-safety bundle passes **271 tests**.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution/evidence gates and G5 durable testing/title-
decision lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Fight History chooser):** the managed Choose
Columns window on Fighter Profile now uses the same saved `fighter_id` or
deterministic retained legacy identity projection as the profile and Company
History windows. Rebuilding a profile therefore reuses the existing chooser
for the same fighter instead of creating a second window keyed by Python's
process-local object address. The layout envelope, column order/widths and
historical row payload are unchanged; this is a UI lifecycle/identity repair
only. `ui_data_regression_test.py` now covers the chooser source contract and
the focused profile/UI set passes 33 tests with clean compilation. Stage 4 of
6 remains active with **4 major stages remaining** (G2/G3 completion, G4
Staff execution/evidence gates and G5 durable testing/title-decision
lifecycle). No EXE or user save was rebuilt or modified.

Stage 4 progress update (J8.a durable tournament hub): one-night tournament
editions are now retained in the permanent Results index rather than depending
on replay commentary. Tournament simulation authors an identity-safe entrant
list (entrant_ids), deterministic seed order with recorded rank snapshots,
division/gender, optional series ID, and the existing stage/match result
evidence. Event closeout adds a stable edition ID and source result references;
compact index migration preserves the new fields and unknown future bracket
metadata defensively. The new Results -> Tournament History reader is
read-only and searchable by promotion or text, shows field/champion/status/
replay availability, and expands each edition into seeded field,
substitutions, stage matches and original result references. Open Source Card
resolves the saved archive identity when a replay exists and otherwise opens
the compact card summary; it never resolves current rosters, reruns a
tournament, consumes RNG or changes settlement. Legacy cards without a
retained bracket are not given fabricated editions.
j8_tournament_history_regression_test.py covers compact persistence,
identity-safe filtering, defensive reads, legacy fallback, no-RNG/no-state
drift and simulator metadata; ui_data_regression_test.py covers the Results
entry point and detail markers. The focused J8/UI/event bundle passes 63 tests;
py_compile and git diff --check are clean. Stage 4 of 6 remains active with
4 major stages remaining (G2/G3 completion, G4 Staff execution/evidence gates
and G5 durable testing/title-decision lifecycle). No EXE or user save was
rebuilt or modified.

Stage 4 progress update (J8.b one-night field review): Matchmaking now has a
managed, read-only Tournament Field Review for the selected draft tournament.
The seeded-field panel preserves authored order, fighter IDs and selected-date
readiness, including an explicit identity-unavailable state. The alternate
panel uses a pure same-division/gender availability adapter, excludes seeded
and already-booked identities, and displays current company/world rank
snapshots, records and readiness. It never calls the stochastic replacement
scorer, signs a free agent, rerolls seeding, changes the draft or bypasses
weigh-in eligibility; actual alternate entry remains owned by the existing
weigh-in flow. The saved bracket's stable edition/source references and
Tournament History reader remain the historical record. The J8 regression now
covers alternate filtering, duplicate/busy exclusion, rank ordering,
no-RNG/no-state drift and the UI review contract; the broader focused bundle
passes 278 tests, with py_compile and git diff --check clean. Stage 4 of 6
remains active with 4 major stages remaining (G2/G3 completion, G4 Staff
execution/evidence gates and G5 durable testing/title-decision lifecycle). No
EXE or user save was rebuilt or modified.

The saved-report reader is also reachable after Simulation Lab is rebuilt;
opening it uses the selected seed/year pair and reports an explicit unavailable
state when that pair has no retained file. This keeps report persistence a
real user-facing recovery path rather than a write-only log artifact.

**Stage 4 verification update (full maintained regression runner):** after the
Matchmaking draft-source and Media story-reader identity fixes, the maintained
isolated runner completed with `ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`.
This includes the 190-test UI-data suite, Staff/Media/booking/title-decision,
profile, persistence, engine, Fight Night, Combat Sports, long-run child
promotion and stability suites. The stability playtest reached Month 4 for
seeds 2201–2203; its expected headless Matchmaking coordinate probe remained
the only documented skip. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Matchmaking draft action source identity):**
card move-up, move-down and remove actions now resolve the selected row through
the source object retained by the card reader, with a unique saved
`booking_id` as the only detached compatibility fallback. Equal legacy fight
dictionaries without either identity anchor fail closed instead of routing to
the first equal row. This keeps duplicate legacy drafts safe through refresh,
sort and action handling without changing card order semantics or booking
rules. UI-data and Booking Workbench coverage passes (**204 focused tests**),
smoke passes with the documented headless Matchmaking probe skipped, and
compilation/diff checks are clean. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 identity follow-up (Media story reader navigation):** story-reader
navigation now resolves the selected Media Desk row by source-object identity,
with a unique retained story ID as the detached compatibility fallback. Equal
legacy headline dictionaries therefore remain distinct during Previous/Next
navigation; an equal detached row without a durable ID opens as an external
World Hub/Chronicle brief instead of silently selecting the first Media row.
The UI-data suite passes (**190 tests**) with clean compilation. Stage 4 remains
active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 Staff identity follow-up (department target resolution):** Staff's
  built-in review adapters now enumerate retained fighter objects first, match
  an explicit `fighter_id` uniquely, and accept a name-only legacy target only
  when exactly one career matches. Duplicate same-name careers therefore fail
  closed with a visible unavailable-target result rather than routing medical,
  scouting, matchmaking or contract advice to the first object. The adapter
  remains read-only and does not spend, draw RNG, create cases or alter staff
  progression. `staff_management_regression_test.py` adds duplicate-name and
  stable-ID coverage; its 60 tests pass with clean compilation. Stage 4 remains
  active with **4 major gates** and **12 named card areas** unfinished or
  policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (World Hub gym action routing):** the World Hub
Gym Viewer action now resolves the selected row through `_world_gym_rows` and
returns the retained gym object directly. A pre-identity widget may use a
name-only compatibility fallback only when exactly one saved gym has that
name; duplicate names fail closed rather than opening the first match after a
sort or refresh. The change is presentation/action routing only: gym counts,
membership, training, finance and world state remain untouched by repainting.
`ui_data_regression_test.py` now guards the source-map and unique-fallback
contract; the complete UI-data suite passes **191 tests** with clean
compilation. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Regression integrity follow-up (historical selection fixture compatibility):**
The immutable phase-31 selection verifier now recognises the two later-added
development-loan return fields as save-only defaults. Historical reconstruction
may omit `loan_return_month=0` and `loan_return_week=0` only when both values are
exactly their untouched defaults; populated, malformed or non-integer values
fail closed. This keeps every frozen bout, fixture and registry checksum exact
without hiding active loan state. The historical selection parity suite passes
**18 tests**. The child-promotion interaction harness also silences both native
notice variants used by the compatibility guard and passes its full workflow.

**Stage 4 delivery slice (A3 break-even attendance):** Cash-runway event
quotes now expose a break-even attendance only when gate plus merchandise can
cover the committed card cost within venue capacity. The calculation reuses
the same ticket, merchandise and grudge inputs as the low/base/high scenarios,
explicitly excludes conditional rights and sponsor receipts, and reports the
reason when capacity cannot reach the threshold. Saved scenario details now
show each committed card's break-even evidence without applying edits or
changing finance, schedule or RNG state. The cash-runway suite passes **14
tests**, with clean compilation and diff checks. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

Pending title-miss fine evidence now uses the same finite bounded projection;
an invalid saved total cannot crash resume or become an unbounded purse debit.
It remains reviewable and is never recomputed from a fresh weigh-in.

The settled-receipt detail projection applies the same boundary to each sponsor
amount, rights amount, sponsor total and relationship delta. Infinity, NaN and
overflow values render as zero evidence rather than raising while the immutable
receipt remains available for review.

**Stage 4 integrity follow-up (A7 World Chronicle overflow guard):** The
World Chronicle read model now bounds non-finite or overflow-sized page limits
and chronology dates. An invalid date is rendered as `Date unavailable` with a
`Needs review` marker; valid headlines, authored details, stable source-bound
identities and duplicate suffixes remain intact. The projection never repairs,
filters out or rewrites the retained chronicle, and context actions still use
the source identity map. The focused UI-data check passes with clean
compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 verification checkpoint (maintained regression runner):** The
maintained runner completed its full pre-parity set and the post-parity
selection/follow-up, coverage, registry, commentary, baseline, Fight Night,
universe, audio, notification, lifecycle, database-editor and stability suites.
The only interruption was an unattended child-promotion warning dialog in the
test harness; silencing both native notice variants resolved it and the
focused rerun finished with **ALL REQUESTED ISOLATED REGRESSION SUITES PASSED**.
The runner produced no save, EXE or user-career mutation. Stage 4 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated.

**Stage 4 integrity follow-up (A3 scenario source revision completeness):**
Saved runway snapshots now fingerprint the cash balance, company operating
inputs, staff/academy cost sources, testing rule, event venue/region/
broadcaster/tier, super-event terms and stable participant facts in addition to
the existing date/price/rights/sponsor inputs. Changing any of those sources
marks the snapshot `Stale inputs` on read while retaining its original
forecast. The revision remains pure and does not resolve fighters, rerun
settlement or rewrite the saved envelope; the cash-runway suite passes **15
tests** with clean compilation and diff checks. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (G4 AI Staff Ledger read model):** The Staff page now
offers a read-only AI Staff Ledger for non-feeder promotion employees and the
shared market. It puts source, promotion/staff identity, role, specialty, skill,
morale, salary, contract term/expiry, roster payroll and identity quality in a
single scrollable reader. Stable promotion/staff IDs drive row identity;
duplicate IDs receive deterministic suffixes, while ID-less name/role/index
rows are explicitly marked as legacy fallbacks. The adapter skips malformed
records and regional feeders without repairing them, and opening the ledger
does not tick contracts, refresh offers, run affordability, spend cash or
consume RNG. Regression coverage verifies purity, feeder exclusion, duplicate
identity handling and bounded row limits. This improves G4 observability but
does not close the gate: AI hiring economics, retention thresholds and any new
specialist bonuses remain governed by the existing lifecycle and policy holds.
The same Staff surface now has a View Evidence Audit reader that expands each
retained finding with its work/brief/action/boundary identifiers while remaining
diagnostic-only; it does not turn a finding into an automatic repair permission.
Retention Watch rows now use the same stable staff identity rule and preserve a
still-visible selection through refresh/reordering. ID-less rows are explicitly
legacy fallbacks; the refresh remains a read-only projection of the existing
contract and morale facts.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3
completion, G4 Staff execution/evidence gates and G5 durable testing/title-
decision lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J1 Draft Review identity routing):** The Draft
Review reader now binds each row to its saved booking/fight reference rather
than indexing back into the visible list. Foundation-migrated rows retain their
durable IDs; old rows remain explicitly labelled legacy fallbacks, and duplicate
source IDs receive deterministic UI suffixes. Selection, detail text and the
locked-slot proposal action all resolve through that identity map, so a reorder
cannot direct an edit at another bout. The mutation boundary, stale fingerprint
check and explicit Foundation commit remain unchanged. This closes the J1
reader-routing slice but not the full assisted booking workbench acceptance
contract. Stage 4 of 6 remains active with **4 major stages remaining** and
**13 named card areas** still unfinished or policy-gated. No EXE or user save
was rebuilt or modified.

**Stage 4 progress update (J1 proposal-option identity routing):** The
alternative table inside the Booking Workbench now keys each option by its
saved fighter identity. Legacy snapshots retain an explicit `legacy-option`
fallback and duplicate source IDs receive deterministic suffixes. Detail,
Fill Selected Slot and Save Medical Draft all resolve through that map rather
than converting the visible selection into a list index; a current eligibility
refresh therefore cannot retarget a different opponent. This is still a
presentation/identity slice: proposal snapshots, stale validation and the
existing explicit commit owner remain unchanged. Stage 4 of 6 remains active
with **4 major stages remaining** and **13 named card areas** still unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J1 locked-slot option identity):** The locked-slot
replacement reader now uses saved replacement fighter IDs for its Treeview keys,
with explicit legacy fallbacks and deterministic duplicate suffixes. Detail and
Commit Selected Replacement resolve through the identity map, preserving the
existing stale-fingerprint and receipt-backed mutation boundary while avoiding
visible-index retargeting after a refresh. This closes the remaining J1 option
reader-routing slice; the broader assisted workbench still requires its full
acceptance and user-flow gate. Stage 4 of 6 remains active with **4 major
stages remaining** and **13 named card areas** still unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J7 proposal-ledger identity):** The Company
Proposal Ledger now preserves the saved proposal identity through status-filter
refreshes. Missing IDs are displayed as explicit non-durable legacy references,
duplicate source IDs receive deterministic suffixes, and the detail reader
restores a still-visible selection by the same identity key. Proposal terms,
warnings and outcomes remain read-only projections; no transfer, loan or cash
handler is invoked by opening or refreshing the ledger. This closes the J7
ledger-routing slice, while bilateral agreement and ownership-allocation rules
remain policy-gated. Stage 4 of 6 remains active with **4 major stages
remaining** and **13 named card areas** still unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 Company & Title History identity):** The
Profile Company & Title History reader now keys each interval/event row by its
recorded membership/title/source identity where available. Legacy rows use a
deterministic fact fingerprint and remain explicitly non-durable; duplicate
keys receive suffixes. As-of filtering and refresh restore a still-visible
selection through that map, while export continues to contain the complete
recorded rows. Opening, filtering or exporting remains read-only and cannot
route detail through a mutable list index. Stage 4 of 6 remains active with
**4 major stages remaining** and **13 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update:** After the intake-boundary changes, the
foundation source suite passes **34 tests**, the UI-data suite passes **165**,
and the Combat Sports/persistence pair passes **21**. Compilation and diff
checks remain clean. These are additive integrity checks only; Stage 4 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (Combat Sports private-market boundary):**
Player-owned Combat Sports youth/free-agent signings now append their stable
destination-company `join` fact before removing the candidate from the saved
signable pool or mutating the player division roster. The existing cash,
contract, sport-employer and ranking updates remain unchanged, and no second
membership row is created. `combat_sports_regression_test.py` and
`persistence_regression_test.py` pass **21 tests**; no EXE or user save was
rebuilt or modified.

**Stage 4 verification update (intake stability):** The broader stability
playtest passed for seeds **2201, 2202 and 2203**, each reaching Month 4 with
179, 187 and 180 recorded events respectively and 1, 1 and 2 ordinary
retirements. This confirms the membership-boundary and intake changes do not
destabilise calendar progression, event recording or retirement handling.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (V04 roster selection):** The player roster
reader now captures the selected fighter's source identity before a filter or
status refresh, restores that same row when it remains visible and refreshes
its detail card. If the career is filtered out or has departed, no replacement
row is selected for the old detail context. This is presentation-only and
leaves roster, contract and champion mutation owners unchanged. The UI-data
regression covers the identity-based refresh contract and focused compilation
remains clean. Stage 4 of 6 remains active with **4 major stages remaining**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 progress update (V06 Development tab):** Fighter Profile's
Development page now treats the monthly value as a labelled outlook signal,
not a promised rating gain. The header exposes a presentation-only score band,
ceiling gap and signed-driver summary; the explanatory callout states what the
band means and why the result is not guaranteed. Recent retained development
changes are shown in a compact ledger with recorded date, before/after values,
change type and reason, while malformed evidence remains explicitly
unavailable. The driver chart keeps one absolute scale for positive and
negative contributions, and the existing stored change order/chronicle stays
available below it. `fighter_profile_regression_test.py` passes **33 tests**;
the full UI-data suite passes **192 tests**, smoke passes with only the
documented headless Matchmaking probe skipped, and compilation/diff checks are
clean. The combined UI/profile run passes **225 tests**; no development
formula, trait progression, save migration, RNG or EXE behaviour changed.
Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (G2 Regions reader identity):** The active Regions
page now keeps a source-bound key for every displayed region and resolves the
selected region through that key in the profile, Region Hub and Feasibility
actions. Refreshing or adding/reordering region rows therefore cannot make a
selection follow a stale visible index; a legacy widget falls back only to its
own displayed value when that value is still a valid saved region. The region
data and all hub/feasibility calculations remain read-only. `ui_data_regression_test.py`
now covers stable and legacy region keys plus reordered selection; the focused
UI-data suite passes **88 tests**, with compilation and `git diff --check` clean.
This closes a G2 presentation/routing slice only; regional invitation and
feasibility mechanics remain under their existing J9 policy boundaries. Stage
4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** still unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (G2 Region Hub gym reader):** The Region Hub's
local-gym list now resolves double-click actions through stable gym identities,
with deterministic duplicate suffixes, instead of indexing the current gym
list directly. The Events tab also shows its empty-state message only when no
events exist, avoiding a misleading blank row on populated regions. This is a
read-only presentation safeguard; gym membership, event schedules and hub
state are unchanged. The focused UI-data suite passes **88 tests**, compilation
and `git diff --check` are clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (World Hub news identity routing):** World Hub news
detail, context and reader actions now resolve through source-bound chronicle
keys. Refreshes retain the selected story when it remains visible, and
pre-keyed legacy windows use an explicit non-durable fallback rather than
claiming a durable identity. The UI data suite now passes **85 tests** with
the new selection coverage; compilation and diff checks remain clean. This is
a reader-safety slice and does not generate, reorder or mutate world stories.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** still unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 progress update (Awards reader identity routing):** Achievements &
Milestones now binds detail and fighter-profile actions to a stable achievement
ID/target key, with deterministic fingerprints for ID-less legacy entries and
suffixes for duplicates. Filtering and refresh preserve a still-visible
selection without mutating the achievement ledger. The focused Awards suite
now has **15 tests** including record-book and achievement identity coverage;
compilation and diff checks remain clean. This is a presentation/safety slice;
achievement unlock semantics and historical data remain unchanged. Stage 4 of
6 remains active with **4 major stages remaining** and **12 named card areas**
still unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A2 record-book identity routing):** The Official
Record Book now binds each row to a scope/key identity rather than the sorted
visible position. World, promotion and event records remain fully readable,
and duplicate display keys receive deterministic suffixes without changing the
saved historical ledger. The closeout suite now has **15 tests**, including
record-book identity coverage; compilation, event economics and diff checks
remain clean. This is a presentation-routing hardening slice and does not
rewrite record holders or history. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S3 Career Journeys identity routing):** The Career
Journeys reader now keys each fighter row by the saved fighter identity, with
explicit legacy fallbacks and deterministic suffixes for duplicate IDs. Profile
opening and career-plan actions resolve through that map rather than converting
the current selection into a visible-list index. This is an identity/safety
slice only: existing career-goal and relationship mechanics remain the domain
owners, and no goal, trust or contract state is changed by opening the reader.
Stage 4 of 6 remains active with **4 major stages remaining** and **13 named
card areas** still unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 progress update (A3 Finance history identity):** Finance weekly
history now uses saved month/week keys, explicit legacy fallbacks for
incomplete rows, and deterministic suffixes for duplicate boundaries. Refresh
restores a still-visible week through the saved row map, and the detail reader
uses that map rather than converting a selection into a visible-list index.
Incomplete legacy fields are rendered safely without altering the ledger. This
is a presentation/identity slice; runway scenarios and settlement ownership
remain unchanged. Stage 4 of 6 remains active with **4 major stages remaining**
and **13 named card areas** still unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 progress update (J1 Matchmaking draft-card identity):** The live
Matchmaking draft-card table now keeps an identity map from each Treeview row to
its saved booking/fight object. Durable booking IDs are preferred; legacy rows
use an explicit non-durable fallback and duplicate source IDs receive
deterministic suffixes. Refresh restores a still-visible selection by object
identity. Remove, Compare, Fill TBA, title-toggle and Move Up/Down resolve the
selected fight through that map, so sorting/reordering or a refresh cannot route
an action to a different card row. This is a presentation/identity safety slice;
booking validation, title consequences and the ordinary commit path remain
unchanged. Stage 4 of 6 remains active with **4 major stages remaining** and
**13 named card areas** still unfinished or policy-gated. No EXE or user save
was rebuilt or modified.

**Stage 4 progress update (Inbox, Owner Objectives and roster identity):** Inbox
message rows now keep a source-bound map keyed by saved message/event/goal or
assignment identity, with deterministic legacy fingerprints and duplicate
suffixes. Refresh/filter/sort restores a still-visible message, and bulk-read
uses the row map rather than converting a display ID into an inbox index. Owner
Objective rows use the saved goal ID (or an explicit legacy fingerprint) for
navigation and preserve selection through repaint. Retired-fighter comeback
actions resolve through stable fighter IDs, and Staff member/candidate actions
fail closed if their identity map is missing. These are presentation/safety
slices; message resolution, goal boundary evaluation, contract mutation and
comeback negotiation remain their existing domain owners. Stage 4 of 6 remains
active with **4 major stages remaining** and **13 named card areas** still
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Media Desk story identity):** Media Desk headline
rows now bind to saved story/chronicle/entry/event identity, with explicit
legacy fingerprints and deterministic duplicate suffixes. Refresh restores a
still-visible selected story by object identity; the read preview, context
links and Previous/Next reader navigation resolve from that entry rather than
a mutable headline position. A read-only compatibility alias accepts stale
`story:<position>` selections from older windows but is never inserted as a
durable row ID. This is a presentation/reader-safety slice; narrative storage,
subscriptions and context mutations remain unchanged. Stage 4 of 6 remains
active with **4 major stages remaining** and **13 named card areas** still
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Assistant and Staff reader fail-closed routing):**
The assistant decision queue and Staff profile readers now require their
source-bound selection maps. A stale numeric/visible-position selection is
discarded rather than opening a different notice or employee after refresh.
This tightens the existing saved-ID presentation contract without changing
staff employment, recommendations or decision outcomes. Stage 4 of 6 remains
active with **4 major stages remaining** and **13 named card areas** still
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Academy history identity):** Academy showcase-card
history and alumni tables now bind rows to saved event/fighter/prospect identity
where available, with deterministic legacy fingerprints and duplicate suffixes.
Refresh restores a still-visible selected record; replay, profile and matching-
right actions resolve through the identity map rather than a mutable row index.
This is a presentation/safety slice; academy training, graduation and matching-
right settlement mechanics remain unchanged. Stage 4 of 6 remains active with
**4 major stages remaining** and **13 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Player Combat Sports identity routing):** Player
Combat Sports running-order bouts, scheduled cards and completed-card rows now
use saved identity keys or deterministic legacy fingerprints with duplicate
suffixes. Remove/Move and replay/cancellation actions resolve through their
row maps, so refreshing or reordering the table cannot retarget another
matchup. This is a presentation/identity safety slice; sport rules, settlement
and scheduling ownership remain unchanged. Stage 4 of 6 remains active with
**4 major stages remaining** and **13 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Fighter Comparison measure identity):** Comparison
metrics now receive stable hashed measure IDs, deterministic duplicate suffixes
and a source-bound row map. The detail panel resolves the selected metric from
that map, so view filters and refreshes cannot display another measure's values
because a visible row number shifted. This preserves all existing comparison
content and remains a presentation/reader-safety slice; scouting visibility,
advantage wording and booking rules are unchanged. Stage 4 of 6 remains active
with **4 major stages remaining** and **13 named card areas** still unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 interval source identity):** Company History
interval projections now retain the membership and event IDs behind their start
and end boundaries. Profile timeline rows carry those IDs into the read-only
history table, allowing an as-of refresh to preserve the authoritative recorded
fact rather than relying on a display-text fingerprint. Legacy intervals and
title rows without a source ID remain explicitly non-durable and unchanged.
This strengthens J4's historical truth/identity contract without altering
membership transitions, title lineage or save data. Stage 4 of 6 remains active
with **4 major stages remaining** and **13 named card areas** still unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 dependency audit (current handoff boundary):** all currently
unblocked read-model, identity, persistence, presentation and safety slices in
the implementation ledger have an owner, source contract and regression
coverage. The remaining work is intentionally not guessed from the ignored
reference image or from mutable live state. G2/G3 now have the additive
super-event commitment ledger and sponsor maximum-versus-activation estimate,
but still require the remaining owned-calendar closeout and approved commercial
forecast/child-calendar rules. G4 now has the supported-handler matrix,
evidence-gated execution and a pure long-run qualification audit; it still
requires approved qualification thresholds and any player-facing corrective
workflow before those diagnostics can become progression or automation gates.
G5 still requires explicit policy tables before enabling
provider-specific drug-testing outcomes, confirmation/appeal/sanction rules,
AI or spectator testing automation, and the unresolved challenger-miss/title
consequence matrix. J8.a and J8.b are complete as read-only tournament
history/field-review slices; expanding them into multi-event series or
automatic alternates remains a separate approval-gated feature. No EXE or user
save has been rebuilt or modified in this pass.

**Stage 4 progress update (J5 case-reader purity):** the Drug Testing Cases
ledger now reads the retained case envelope without invoking its save-repairing
initialiser. Case rows, summary counts, details and workflow projections are
defensive read models; a malformed or unavailable legacy `cases` collection
returns an explicit empty ledger and leaves the original payload untouched for
the sanctioned load/migration boundary. This closes a J5 presentation/safety
slice only; provider-specific outcomes, confirmation, appeals, sanctions and
automation remain policy-gated. The focused drug-testing catalogue/case suite
passes **16 tests** with `py_compile` and `git diff --check` clean. Stage 4 of
6 remains active with **4 major stages remaining** and **13 named card areas**
still unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J7 proposal-reader purity):** the Company Proposal
Ledger now reads its append-only review collection directly rather than calling
the save-repairing Foundation initialiser. A malformed or unavailable legacy
proposal collection therefore renders an empty/unavailable reader and leaves
the original payload untouched for the normal load/migration boundary; valid
proposal snapshots remain defensive and resolve by saved proposal ID. This is
a J7 presentation/safety slice only and does not enable new ownership or treaty
mechanics. The focused Foundation regression now passes **22 tests** with
`py_compile` and `git diff --check` clean. Stage 4 of 6 remains active with
**4 major stages remaining** and **13 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A5 story-briefing reader purity):** Followed Story
Briefings and the Storylines detail reader now consume a defensive subscription
projection. Opening or refreshing either reader no longer repairs malformed
snooze/cursor rows; unavailable rows remain explicitly absent while the
normalised write boundary is retained for explicit follow, acknowledge,
snooze, and unfollow actions. The briefing regression now covers malformed
subscription evidence and no state drift. This is a presentation/safety slice;
story generation and narrative progression are unchanged. Stage 4 of 6 remains
active with **4 major stages remaining** and **13 named card areas** still
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (G1/G4 malformed receipt projection):** Foundation
work-receipt cards now remain readable when retained numeric fields are invalid:
the diagnostic projection reports bounded zero values while preserving the raw
receipt unchanged for audit and the sanctioned repair boundary. This protects
Staff and shared history readers from a malformed legacy row without masking
the underlying evidence. The focused Foundation/Staff bundle now includes this
regression; Stage 4 of 6 remains active with **4 major stages remaining** and
**13 named card areas** still unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 progress update (J5 case identity routing):** Testing Cases rows now
bind their Treeview identity to the saved `case_id`, assign deterministic
suffixes for duplicate legacy rows, and use a clearly non-durable fingerprint
when a historical row has no ID. Refresh restores the same visible case and
detail payload when present; the stored evidence and IDs are never rewritten.
This is a J5 UI identity slice only and does not enable testing outcomes,
confirmation, appeals or sanctions. Stage 4 of 6 remains active with **4 major
stages remaining** and **13 named card areas** still unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S3/J4 Talent Relations reader purity):** Talent
Relations case rows now use a defensive projection over the saved obligation
shelf. The register and Staff contract-review reads tolerate malformed legacy
numeric/history fields without repairing or rewriting the source; explicit
case opening, acknowledgement and action selection retain the existing
normalisation/write owner. This closes a reader-safety slice only and does not
add new retention, satisfaction or automatic contract mechanics. Stage 4 of 6
remains active with **4 major stages remaining** and **13 named card areas**
still unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Current stage-count accounting (14 September 2026):** There are six delivery
gates in this roadmap: **G0–G5**. The detailed, non-deferred implementation
inventory contains **63 named cards**: F0 (1), U01–U16 (16), V01–V19 (19),
M1–M3 (3), S1–S4 (4), J1–J12 (12), A1–A7 (7) and L0 (1). These are work
units, not six more monolithic builds; a card may contain several independently
testable read-model, UI, persistence or gameplay slices. The report also names
**14 deferred/excluded D-cards** (D01–D14, with D07 explicitly excluded); they
are not on the first playable completion path and require separate approval.

For the currently authorised path, **12 named card areas still have an
unfinished or policy-gated slice**: S3, S4, J1, J4, J5, J6, J7, J8,
A1, A2, A3 and L0. The J9.a feasibility and J9.b invitation slices are now
delivered; the rest have a delivered bounded slice, although their
acceptance tests and release gates still apply. In practical terms: Stage 4 is
the active gate; G2/G3 closeout, G4 staff/AI qualification and G5
testing/title/optional-mechanics decisions are the four remaining major tracks,
while the 12-card list is the finer-grained work still to close. This count is
planning inventory only—not a time estimate—and a card does not become complete
until its full acceptance contract, regression coverage and any explicit user
decision are satisfied.

**Stage 4 progress update (G4 Staff identity routing):** Staff roster, market and
expiry tables now bind every action to the saved `staff_id` rather than a visible
row position. Refreshes and sortable views preserve the same employee for
profile, hire, negotiate and release actions, restoring a still-visible
selection; deterministic suffixes disambiguate
duplicate source IDs, and records without an ID use an explicit legacy-only
fallback. The UI data regression covers stable and legacy keys. This closes the
identity-reroute portion of S4, but does not change contracts, payroll or AI
employment economics; those still need the approved long-run survival evidence.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3 completion,
G4 Staff execution/evidence gates and G5 durable testing/title-decision
lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 history reader purity):** Membership event and
interval/as-of readers now inspect the raw retained history envelope instead of
calling the save-repairing foundation initialiser during a page refresh. A
malformed collection therefore returns an explicit empty/incomplete projection
without changing the save; the normal load/migration boundary remains the only
repair owner. Foundation regressions cover malformed event pages and intervals.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3 completion,
G4 Staff execution/evidence gates and G5 durable testing/title-decision
lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A1/J7 child-company identity routing):** The child
promotion manager now assigns stable row IDs from `promotion_id` and keeps the
selected child through refresh/reordering. Loan, recall and parent-transfer
actions pass that identity into the existing mutation owners; duplicate display
names fail closed instead of selecting the first match, while unique legacy
names remain compatible. This is an identity/safety slice only: it does not
enable the still-gated child-event scheduler or new ownership/treaty economics.
Stage 4 of 6 remains active with **4 major stages remaining** (G2/G3 completion,
G4 Staff execution/evidence gates and G5 durable testing/title-decision
lifecycle). No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A1 Owned Calendar identity routing):** The dashboard
calendar now assigns deterministic Treeview IDs from the saved event ID plus
owner/source identity, rather than the visible row position. Duplicate source
rows receive stable suffixes, legacy references remain visibly non-durable, and
filter/refresh/reorder restores the selected event only when that same source
identity is still present. The read-only index and detail reader remain
mutation-free; controlled child scheduling and ownership economics are still
policy-gated. Stage 4 of 6 remains active with **4 major stages remaining**.

**Stage 4/L0 progress update (Staff employment integrity evidence):** The
isolated hard-invariant scan now checks player, AI-promotion and market Staff
collections for missing or duplicate identities, market/employed collisions,
missing roles and invalid or negative salary/contract terms. Findings carry a
stable code/path/detail and are retained in the audit checkpoint without
normalising the world or changing RNG. This closes an evidence slice for S4/L0;
it does not set long-run affordability, retention or qualification thresholds.
Stage 4 of 6 remains active with **4 major stages remaining**.

**Stage 4 progress update (A3 scenario snapshots):** Finance now exposes a
named, non-binding runway scenario snapshot action. The saved record contains
bounded attendance assumptions, proposed edits, the complete settlement-aligned
forecast and a source revision digest. Repeating the same request is
idempotent; changing a scheduled card or finance/right term marks the saved
record `Stale inputs` while retaining its original evidence. Applying an edit
remains an explicit action in the existing event/finance editor; no snapshot
save/review moves a card, reserves cash, reruns settlement or consumes RNG.
The Finance page also includes a read-only saved-scenario reader showing
assumptions, proposed (unapplied) edits, freshness and the stored lowest-balance
evidence.
The runway now exposes bounded 0–200% low/base/high attendance controls; table
headings, forecast values and the saved snapshot share the selected assumptions,
which remain sensitivities rather than probability claims.
Stage 4 of 6 remains active with **4 major stages remaining**.

**Stage 4 progress update (L0 reproducible play-audit checkpoints):** the
Simulation Lab play-level audit now writes one bounded, atomic checkpoint at
each completed in-game year. The checkpoint contains the explicit seed and
target, source/configuration/native-profile fingerprints, encoded RNG state,
serialized isolated observer-world state, accumulated methods/yearly health
measurements, hard-invariant findings and an output cursor. A separate **Resume Play Audit** action
validates the complete identity and progress before restoring the observer
world; a changed source, ruleset, target or malformed checkpoint fails closed
without touching the active career. Checkpoint writes clean up temporary files
on failure, preserve the previous valid destination, and never install audit
hooks on the live class or write the user's save. Explicit invariant checks
are limited to unambiguous saved evidence; thin divisions, low cash and other
balance observations remain measurements rather than arbitrary failures. The
report now includes coverage accounting for completed weekly boundaries and
method totals. `play_level_audit.py` and `play_level_audit_regression_test.py`
cover fresh/resumed RNG and state round-trip, source/configuration mismatch
rejection, bounded measurements, malformed payloads, atomic-failure cleanup,
hard-invariant findings and report-accounting gaps. This is an L0 evidence and
diagnostics slice only: it does not claim population/finance thresholds are
approved balance gates or enable any deferred gameplay card. The broader
focused verification bundle now passes **287 tests**; `py_compile`, the
maintained isolated runner slice and `git diff --check` are clean. Stage 4 of 6
remains active with **4 major stages remaining** (G2/G3 completion, G4 Staff
execution/evidence gates and G5 durable testing/title-decision lifecycle). No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (G4 handler evidence gate + G3 forecast basis):** Staff
autonomy now validates the accountable handler response before sealing any
recommendation or Full Auto work row. A missing evidence key, invalid spend,
paid recommendation, or malformed payload becomes `Needs attention`; successful
work retains the complete evidence and progression flags. The capability grid
also shows per-action handler registration and `Ready` versus `Gated` state for
the current save, without normalising policy or staff data. Finance's read-only
12-week runway now reports each booked card's contracted sponsor maximum beside
an activation-adjusted estimate derived from the pure trust/stability/campaign/
delivery preview. The estimate includes the at-risk agreement reason, while
conditional rights/sponsor receipts remain outside cash closes and all existing
runway scenarios remain unchanged. New regressions cover every department's
capability/evidence contract, malformed Full Auto output, sponsor maximum versus
estimate, and forecast purity. The focused Staff/UI/audit/Finance bundle passes
**111 tests**; `py_compile` and `git diff --check` are clean. No EXE or user save
was rebuilt or modified. Stage 4 of 6 remains active with **4 major stages
remaining** (G2/G3 completion, G4 Staff execution/evidence gates and G5 durable
testing/title-decision lifecycle).

**Stage 4 progress update (G4 long-run Staff qualification audit):** The Staff
page now exposes a pure evidence audit over the retained work, brief and
progression ledgers. It counts executed actions, read-only recommendations,
calendar boundaries and progression-qualified work, then reports stable findings
for missing or duplicate work/operation identities, missing evidence,
unsupported actions, paid recommendations, malformed recommendation payloads,
briefs sealed before every allow-listed action completed, and progression credits
that point to work no longer retained. Findings carry the relevant work, brief,
action and boundary IDs so a player or future maintenance tool can investigate
without trusting a visible row index. This is an observational qualification
signal only: opening or refreshing it never normalises legacy state, reruns a
handler, spends cash, consumes RNG/capacity or grants progression. The Staff
regression suite now covers both a malformed ledger and a healthy complete
ledger; the focused Staff slice passes **41 tests** with `py_compile` and
`git diff --check` clean. G4 remains active because long-run policy thresholds
and any player-facing corrective workflow still require explicit approval. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (G2 upcoming-card identity routing):** the Upcoming
Cards reader now assigns each scheduled event a stable UI identity from its
saved `event_id`, with a deterministic non-durable fingerprint for legacy rows
that have no ID and predictable suffixes for duplicate source identities.
`refresh_upcoming` retains the event map and restores a still-visible
selection after filtering, refresh or reorder. Due-event, edit and cancel
handlers resolve through that map and fail closed when a stale or missing map
is encountered; a visible Treeview position can no longer select a different
event after the list changes. The smoke harness now selects by the same map,
and `ui_data_regression_test.py` covers the identity contract. This is a
presentation/routing safety slice only: scheduling, cancellation, settlement,
fighter availability, finance, RNG, saves and EXE output are unchanged. Stage
4 of 6 remains active with **4 major stages remaining** and **13 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (G2 scheduled-card editor identity routing):** the
scheduled-card editor now binds each bout row to a saved `fight_id`, `bout_id`,
`booking_id` or `match_id` when available. Legacy rows use deterministic
content fingerprints, duplicate source rows receive presentation-only suffixes,
and the selected fight object is restored after a card refresh or reorder.
Remove, move, title/interim, tier, plan, TBA replacement and last-minute
replacement controls resolve through the identity map before calculating the
current list position, so a changed visible row cannot retarget another bout.
`ui_data_regression_test.py` covers the editor contract and the full smoke suite
passes after the change. This is a routing/presentation safety slice only:
the ordinary editor remains the mutation owner, while bout mechanics, title
rules, fighter availability, finance, RNG, saves and EXE output are unchanged.
Stage 4 of 6 remains active with **4 major stages remaining** and **13 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (G2 Superfight Night card identity routing):** the
temporary Superfight Night builder now assigns each local card row a stable
fighter-based key plus crossover state, suffixing duplicate source rows
without altering the eventual event package. Refreshing or moving the card
restores the selected bout object, while Remove and Move fail closed if their
source-bound map is unavailable; no visible row position is converted directly
into a list index. `ui_data_regression_test.py` covers the contract. This is a
presentation/routing safety slice only: card fees, fighter eligibility,
settlement, fight mechanics, finance, RNG, saves and EXE output are unchanged.
Stage 4 of 6 remains active with **4 major stages remaining** and **13 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (G2 World Chronicle reader identity):** World
Chronicle now keeps a key-to-entry map for its filtered Listbox. Detail and
context actions resolve through that map, while duplicate identity keys receive
deterministic suffixes; filtering or a future refresh therefore cannot make an
action follow a changed visible row. The underlying chronicle payload remains
unchanged and the reader stays read-only. `ui_data_regression_test.py` covers
the routing contract. Stage 4 of 6 remains active with **4 major stages
remaining** and **13 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (A5 Storylines reader purity):** Storylines page
construction no longer invokes the save-repairing story-thread indexer. A
defensive `story_thread_index_read_model` returns only retained valid rows and
leaves malformed or unavailable collections untouched; the UI presents an
explicit empty reader rather than silently normalising history on open. Existing
story follow/acknowledge/write boundaries remain unchanged. The combined Story
Briefing/UI suite passes **89 tests**, and the source compiles cleanly. Stage 4
of 6 remains active with **4 major stages remaining** and **13 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J9.b regional host invitation lifecycle):** Regions
now has an optional, persisted regional-host invitation lane. The quarterly
generator is deterministic and issues an offer only when the feasibility
read-model can prove two bookable local roster fighters and a reliable fixed
staging/venue quote. Each offer stores its stable invitation and entitlement
IDs, four-week acceptance window, 8–16-week proposed event window, quote basis
and capped 10% host guarantee. The Region Hub exposes Generate, Accept, Decline,
Withdraw and Book-in-Matchmaking actions without generating offers on page
open. Acceptance binds only to an ordinary event with the exact saved region,
venue and date; cancellation, expiry and under-filled cards record zero-paid
terminal outcomes. Settlement pays the guarantee once, after two distinct
local roster fighters complete bouts, through the existing finance ledger, with
no deposit, travel charge, RNG draw or duplicate entitlement. The new
`regional_invitation_regression_test.py` covers deterministic quarterly limits,
identity binding, paid/unfulfilled/cancelled/expired outcomes, idempotency and
malformed quote rejection; the focused 97-test invitation/affected-path bundle,
smoke test and source compile pass. This closes the J9.b implementation slice but does not invent
larger invitation formats or override existing event booking rules. Stage 4 of
6 remains active with **4 major stages remaining** and **12 named card areas**
still unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Delivery timing note (14 September 2026, superseded by the latest forecast
below):** The inventory count above is not an estimate of twelve equal-sized
features. Most delivered cards now need only acceptance hardening; the
remaining work is concentrated in four tracks. Earlier planning used a
25–40-hour range; after the J12, J4, S3 and S4 evidence slices, the current
range is **13–21 focused engineering hours**, plus **4–6 hours for full
regression, native-window QA and an EXE release pass** once the user authorises
a rebuild. The lower end assumes the remaining policy gates stay unchanged
and the known historical parity fixture diagnostic is recorded as a
schema-era compatibility finding. The upper end allows for held rules work
(testing/provider numbers, child scheduling and long-run staff thresholds) to
be specified, implemented and calibrated. This forecast excludes new deferred
D-cards, broad fight-engine changes, and any unrequested save conversion. No
EXE or user save is rebuilt or modified by this estimate.

For planning purposes, that remaining effort breaks down as follows:

| Track | Remaining scope | Working estimate |
|---|---|---:|
| G2/G3 closeout | J1 booking-workbench completion, A2 commitment closeout and A3 forecast/review acceptance, including stale/reload/partial-result cases | 8–14 hours |
| G4 Staff/AI | S3 evidence-backed progression/retention acceptance and S4 prospective AI employment affordability/expiry checks | 5–9 hours |
| G5 rules and optional mechanics | J5 confirmation/appeal/title-sanction tables, J6 coaching ownership, J7/J8/A1 held mechanics, and the remaining L0 release evidence | 10–17 hours, depending on policy decisions |
| Release verification | Full maintained runner, native-window smoke/resize checks, parity diagnosis, packaging and an authorised EXE build | 4–6 hours |

These ranges overlap slightly because shared regressions are written while each
track is implemented. The main schedule risk is not UI coding: it is deciding
the exact J5 jurisdiction/provider/confirmation/sanction table and whether the
held child-promotion and tournament rules are enabled in this release. If those
remain deferred, the lower end is realistic; if they are enabled, use the upper
end and allow another calibration pass. The known historical move-selection
parity difference is a fixture/schema-era diagnostic, not a reason to weaken the
historical adapter or silently change the current game.

**Stage 4 progress update (A2 terminal-state guard):** Super-event closeout now
fails closed for a stale offer already marked `Completed`, `Failed`, `Cancelled`
or `Expired`, and completion only accepts a scheduled project (status-less
legacy packages remain readable). A stale terminal object cannot apply a second
closeout or popularity/stability/safety effect, and the booking owner now
rejects an unaccepted or terminal project before it can bypass the approval
terms. Lifecycle transitions now use an explicit state matrix, and a revision
mismatch returns `Needs review` without clearing the live offer; scheduled-card
cancellation respects that fail-closed result. A live-status mismatch now
pauses the same way even when the revision number happens to match. The
closeout regression suite now covers stale-terminal retry, cancelled-event
completion attempts, the canonical `Success` → `Completed` state transition,
transition boundaries, revision mismatch and status mismatch; all ten tests,
the event-economics script, source
compilation and `git diff --check` pass. This is a
lifecycle-integrity slice only: it does not invent refund terms, deadlines or
new project penalties. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** still unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (J5 testing-desk policy selection):** The Testing
Desk now persists a validated Standard/Strict/Olympic/Off policy choice through
one domain setter, increments its configuration revision only when the choice
changes, and leaves provider-specific detection, confirmation, appeals and
sanctions explicitly gated. The UI uses that setter rather than mutating the
rules dictionary directly, while provider/sample quotes remain read-only and
RNG-free. The J5 catalogue regression now covers invalid choices, idempotency,
revision evidence and RNG purity; 13 tests, compilation and diff checks pass.
This is configuration/read-model progress, not an enabled disciplinary model.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** still unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 progress update (A2 opportunity identity routing):** Company
Milestones & Super Events now binds each opportunity row to its saved offer
ID. Legacy offers without an ID receive a deterministic terms fingerprint and
duplicate source IDs receive predictable UI suffixes; no action converts a
visible row position back into an offer index. Refreshing the window preserves
the selected offer when it is still present, while the full saved offer payload
remains unchanged. The closeout regression suite now has **11 tests**, including
stable-ID, legacy-fingerprint, duplicate-suffix and no-mutation coverage;
compilation and diff checks pass. This closes only the UI identity-routing
slice of A2; commitment, refund and broader milestone acceptance work remains
within the active G2/G3 track. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A2 expiry retention):** Offer and planning deadline
workers now route both unaccepted and accepted expiries through the same
terminal closeout owner. Unaccepted invitations record an `Expired` history
row with zero paid/commitment amounts and apply the existing safety consequence
once. If a planning closeout is stale or revision-conflicted, the worker keeps
the live opportunity visible with an explicit review reason instead of dropping
it and leaving an orphaned project. Repeated expiry processing is idempotent;
the focused closeout suite now has **13 tests**, with compilation and diff
checks clean. This remains an A2 lifecycle-integrity slice; legacy refund and
deadline-policy HOLDs are unchanged. Stage 4 of 6 remains active with **4
major stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A2 completion-effects boundary):** Super-event
completion now seals the terminal project closeout before applying popularity,
stability, safety or news/story effects. If the closeout owner returns
`Needs review` for a stale status or revision, completion returns that evidence
without changing the live company's derived values or publishing a misleading
headline. The closeout regression now covers this injected review path; the
focused suite passes **16 tests**, the event-economics regression passes, and
source compilation/diff checks are clean. This is lifecycle-integrity
hardening only: accepted terms, refund policy and sporting thresholds are
unchanged. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** still unfinished or policy-gated. No EXE or user save
was rebuilt or modified.

**Stage 4 progress update (J7 terminal proposal evidence):** Company proposal
transitions now treat `committed`, `rejected`, `withdrawn`, `expired`,
`failed` and `cancelled` rows as immutable terminal evidence. A repeated
terminal click returns the original snapshot even if a stale caller supplies
different wording or terms; only an explicit `Needs review` row remains
recoverable. The Foundation regression now covers altered terminal retries;
the focused Foundation suite passes **22 tests**, the A2 closeout suite passes
**16 tests**, and compilation/diff checks are clean. This preserves the
existing transfer/loan mutation owners and adds no ownership, cash or RNG
mechanic. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** still unfinished or policy-gated. No EXE or user save
was rebuilt or modified.

**Current delivery forecast (14 September 2026, after the latest hardening):**
The implementation ledger now has bounded, tested slices for 51 of the 63
non-deferred named cards. The remaining work is concentrated rather than 12
equal-sized builds: four major tracks remain (G2/G3 closeout, G4 Staff/AI
qualification, G5 held rules/optional mechanics, and release verification),
covering 12 named card areas. With the current policy decisions held, expect
approximately **14–22 focused engineering hours** to close the remaining
implementation and acceptance gaps, followed by **4–6 hours** for the full
maintained runner, native-window/resize checks, parity diagnosis and an
authorised EXE build. If J5's provider/appeal/sanction rules, J6 coaching
ownership, child scheduling or other currently held mechanics are newly
approved, use the upper end and allow an additional calibration pass. The 14
deferred D-cards, broad fight-engine changes and unrequested save conversion
remain outside this estimate. No EXE or user save was rebuilt or modified for
this forecast.

**Stage 4 progress update (S4 legacy AI employment retention):** AI staff
contract expiry now returns employees from older saves that lack a durable
`staff_id` to the shared market instead of silently dropping them. Stable-ID
rows retain retry-safe de-duplication; ID-less rows remain separate legacy
records so duplicate names/roles are never merged by guesswork. The Staff
employment regression now has **6 tests** covering stable hire/expiry identity,
affordability, ledger purity and legacy retention; the focused suite,
compilation and diff checks pass. This closes the legacy expiry/data-retention
slice only; approved long-run payroll, retention and qualification thresholds
remain the remaining S4 policy gate. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (maintained runner):** The maintained runner
passed the Fight Night presentation/archive/layout groups, trait and release
gates, smoke, persistence, testing, tournament, Foundation (22), title
decision, booking, preparation, rules/help, pause/checkpoint, finance,
narrative, UI-data (88), profile (21), performance, AI-card, scouting,
regional, media, Staff/autonomy/specialty/employment, Academy, schedule,
owner-goal, runway, closeout (16), recruitment, relationship, story, child
promotion and the available fight-engine suites. It stops at the existing
historical `fight_move_selection_parity_regression_test.py` assertion
`Selection parity changed: bouts`; all mechanics match, while the fixture
digest differs because the current Fighter schema carries newer persisted
fields. This remains a release-diagnostic/fixture refresh decision, not a
reason to weaken the historical adapter or change current fight selection.
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J12 Database Editor identity routing):** The
standalone Database Editor no longer stores fighter/company selection as a
mutable source-list index. Refreshes build source-object maps keyed by saved
fighter/company IDs where available, with deterministic hashed legacy keys and
duplicate suffixes. Sorting and filtering therefore preserve the selected
record, and add/duplicate/delete operations remove or target that exact source
object instead of whatever row later occupies the old index. Five new
identity regressions pass, alongside compilation and diff checks. This closes
the editor selection/mutation safety slice; preflight validation, presets and
career-conversion policy remain within J12's broader acceptance contract.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** still unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 progress update (J12 validation read-only boundary):** The standalone
Database Editor's Validate action now diagnoses a deep-copied candidate rather
than synchronising or backfilling the live in-memory pack. This keeps rendering
warnings observational; grouped fighter views and legacy ID backfills remain
owned by the explicit save boundary. A new regression proves the live pack is
unchanged after Validate, alongside the existing identity, Save As and shared
validator coverage (20 focused tests pass). The editor's preflight/preset/
conversion acceptance contract is now split cleanly between read-only
diagnostics and explicit writes. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J12 structured opening preflight):** Database Editor
now exposes a separate read-only Preflight action. It returns stable finding
rows with severity, category, entity, field, evidence and remedy: shared schema
errors remain hard errors, while thin owned divisions, zero matching free-agent
depth and explicitly authored payroll above company cash are labelled
playable-risk warnings. Optional parent-company and title-holder references are
resolved without using current rankings or appointing replacements. Preflight
operates on a copied candidate and never normalises, signs, deletes, spends or
writes the live pack. The validator/editor bundle now passes **22 focused
tests**, plus compilation and diff checks. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 combat-sport membership transitions):** Player
combat-sport crossover and release now write both sides of the ownership change
(`leave` then `join`) against the child/flagship company identities before the
roster is changed. Private-market signings and flagship buyouts now record the
child join (and, for a buyout, the flagship leave) against the stable fighter
ID before the new contract is committed. Academy graduates entering a
player-owned child division also receive a child-promotion join fact. AI
combat-sport replenishment records each generated athlete's join fact with a
stable fighter-bound transition key. These hooks keep company timelines truthful
without inferring names, rankings or current-record state, and retries remain
deduplicated by the existing Foundation membership adapter. Six transition
regressions now cover crossover, release, retirement, private signing,
flagship buyout and academy graduation; the focused combat-sports and
Foundation bundle passes **42 tests**, with compilation and diff checks clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** still
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J12 current-career editor identity and transfer
history):** The in-game World Editor now keys visible fighter rows by the
stable fighter identity plus owner context instead of a mutable sort position;
ID-less legacy rows receive a deterministic, explicitly UI-only digest and
duplicate rows are suffixed during refresh. A selected source object therefore
survives filter/sort changes. Employer changes now record the destination
company's join fact at the editor transfer boundary after the old-company leave
hook and before roster insertion; moving to Free Agent does not invent a
company. The editor identity/transfer regressions pass, and the combined
Database Editor, combat-sports and Foundation bundle passes **51 tests** with
clean compilation and diff checks. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S3 progression reader purity):** Staff progression
snapshots now project directly from the retained state instead of invoking the
save-repairing staff initializer during profile or retention reads. Malformed
legacy lists/dictionaries are rendered as bounded empty/known evidence without
rewriting the raw envelope; quarter-close qualification and explicit staff
mutations still use the normal write boundary. The new no-mutation regression
and the Staff management, specialty and employment bundle pass **54 tests**;
compilation and diff checks are clean. Stage 4 of 6 remains active with **4
major stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Current delivery forecast after the S4 runway slice (14 September 2026):**
The six-month AI payroll/runway evidence is now implemented and verified, but
it does not by itself approve new recruiting, retention thresholds or
qualification bonuses. At the current scope, expect approximately **13–21
focused engineering hours** for the remaining implementation and acceptance
gaps, followed by **4–6 hours** for the maintained full runner, native-window
and resize checks, parity diagnosis and an authorised EXE build. The lower end
assumes the held J5/J6/J8 mechanics remain specification-only; newly approved
provider/appeal/sanction rules, coaching ownership or tournament scheduling
would require the upper end plus a calibration pass. The 14 deferred D-cards,
broad fight-engine changes and unrequested save conversion remain outside this
estimate. No EXE or user save was rebuilt or modified for this forecast.

**Stage 4 verification update after the S4 runway slice:** The maintained
runner passed every suite through the Fight Night, profile, persistence,
testing, tournament, Foundation, title-decision, booking, preparation,
finance, narrative, UI-data, Media, Staff/autonomy/specialty/employment,
Academy, schedule, owner-goal, runway, closeout, recruitment, relationship,
story, child-promotion and fight-engine groups. It again stops only at the
pre-existing historical selection-parity assertion
`Selection parity changed: bouts`; current mechanics match and the fixture
digest differs because the current Fighter schema carries newer persisted
fields. The new S4 snapshot tests and UI projection introduce no additional
failure. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 interval conflict evidence):** The membership
 interval read model now detects retained facts with an end date before the
 recorded start, as well as malformed date fields, without sorting, repairing
 or dropping the append-only source rows. Such intervals are explicitly marked
 incomplete, carry a coverage note into the Profile Company History reader,
 and remain visible during an as-of query because their active period cannot be
 truthfully resolved. Same-week join/leave/return boundaries remain separate
 intervals and terminate/start at the same recorded boundary without merging.
 Two regressions cover same-week projection, out-of-order facts, malformed
 dates, as-of visibility and no-mutation behavior; the Foundation/Profile/UI
 bundle passes **133 tests** with clean compilation and diff checks. This closes
 an interval-read truthfulness slice; J4 retention/load policy and title-history
 edge decisions remain held. Stage 4 of 6 remains active with **4 major stages
 remaining** and **12 named card areas** still unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 AI runway evidence):** AI employment now exposes
 a pure affordability snapshot for a promotion and optional market candidate.
 It reports current cash, existing staff payroll, monthly recurring cost, the
 six-month runway requirement, current and post-signing no-revenue runway
 months, one-time signing cost, post-signing cash and explicit role blockers.
 The Staff ledger surfaces the cash/monthly/runway figures for each non-feeder
 promotion, while the market worker reuses the same snapshot before moving the
 candidate and recording its single debit.
 Refreshing the ledger or computing a snapshot never repairs strategy data,
 creates identities, removes candidates, spends cash or consumes RNG. Two new
 regressions cover runway arithmetic, role blockers and no-mutation behaviour;
 the Staff employment suite now passes **8 tests**. This evidence closes the
 read-model portion of S4; long-run survival thresholds and any new AI
 recruiting policy remain held for the S4 policy gate. Stage 4 of 6 remains
 active with **4 major stages remaining** and **12 named card areas** still
 unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S3 observed retention evidence):** Staff
 progression snapshots now return structured workload (credited work and
 distinct periods), saved monthly pay and role-assignment evidence in addition
 to contract and morale observations. Staff Profile surfaces these facts and
 labels retention as manual review; no satisfaction score, departure threshold,
 morale adjustment or automatic exit is inferred. Missing roles and malformed
 salaries remain bounded (`Operations`/zero) while the snapshot stays
 observational. Two regressions cover the evidence shape and missing-role
 behavior; the Staff management, specialty, employment, Profile and UI-data
 bundle passes **166 tests** with clean compilation and diff checks. This
 closes the evidence/readout portion of S3; progression growth caps, heat
 cooling and new departure mechanics remain held. Stage 4 of 6 remains active
 with **4 major stages remaining** and **12 named card areas** still unfinished
 or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 interim-title identity edge):** Interim-belt
 clearing now resolves duplicate display names through the fighter's explicit
 `interim_champion` marker. A legacy name-only map with no unique marker fails
 closed and remains available for manual review; it does not clear either
 fighter or append guessed lineage. Successful clears retain the stable
 fighter ID in the `Interim Belt Cleared` history fact. The Profile/Foundation
 identity bundle passes **46 tests** with clean compilation and diff checks.
 This closes the duplicate-name interim cleanup slice; broader title-history
 migration/retention policy remains held. Stage 4 of 6 remains active with
 **4 major stages remaining** and **12 named card areas** still unfinished or
 policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J1 Draft Review purity):** The booking workbench's
 draft-card reader no longer invokes Foundation booking-ID migration while the
 player is only viewing the card. Existing stable booking IDs remain intact;
 rows missing an ID are labelled `Legacy reference` with an explicit
 UI-only fallback, so a refresh cannot add identity, change the card or cause a
 later edit to follow a mutable position. The booking workbench, Foundation
 and UI-data bundle passes **123 tests** with clean compilation and diff
 checks. This closes the Draft Review read-only identity slice; firm medical
 reservations and any scheduled-event mutation policy remain gated by J1's
 approval contract. Stage 4 of 6 remains active with **4 major stages
 remaining** and **12 named card areas** still unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 progress update (J1 workbench reader envelope safety):** Booking
 brief, proposal-review, locked-slot-review and tentative-medical readers now
 project the retained envelope directly and defensively. A malformed legacy
 `brief`, proposal list or medical-plan collection renders as empty/unavailable
 evidence without inserting defaults, assigning counters or rewriting unknown
 fields during refresh. Explicit save/generate/commit operations still use the
 normal write-boundary normalizer. A new regression covers malformed brief,
 proposal, locked-slot and medical-plan data; the Booking/Foundation/UI-data
 bundle passes **124 tests** with clean compilation and diff checks. This
closes another J1 read-model safety slice; firm medical reservations and
scheduled-event mutation policy remain gated. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** still unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4/L0 malformed membership archive state):** The
membership retention summary now distinguishes a genuinely empty archive from
a malformed historical envelope. It returns explicit `available` and
`coverage` values plus a repair-boundary notice, while the Profile Company
History header displays `Archive unavailable` instead of implying that no facts
were ever retained. Membership pages still read the raw envelope and do not
normalise, truncate or fabricate rows; the sanctioned load/migration boundary
remains the only repair owner. Two Foundation regressions cover malformed
collection shapes (including a malformed top-level historical envelope),
no-mutation behaviour and the explicit unavailable state. The
Foundation/Profile/UI bundle passes **136 tests** with clean compilation
and `git diff --check`. This closes another J4/L0 diagnostic/read-model slice;
retention policy and long-run thresholds remain held. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (maintained runner after archive-state slice):**
The current maintained runner passed the Fight Night presentation/archive/layout,
trait/release, smoke, persistence, drug-testing, tournament, Foundation
(26), title-decision, booking (12), preparation, rules/help, pause/checkpoint,
finance, narrative/performance, UI-data (88), profile (22), performance,
AI-card, scouting, regional, Media (22), Staff/autonomy (44), specialty and
employment, Academy, owned schedule, owner goals, cash runway, super-event
closeout (16), recruitment, relationship/story, child-promotion and available
fight-engine groups. It stopped only at the pre-existing
`fight_move_selection_parity_regression_test.py` historical fixture assertion
(`Selection parity changed: bouts`); current mechanics match and the fixture
digest differs because the Fighter schema carries newer persisted fields. The
new malformed-membership coverage introduces no additional runner failure.
No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 complete-history pagination):** The Profile
Company & Title History reader now derives up to the full retained history
before rendering and paginates the visible table in 250-row pages. Previous/
Next controls report the page and total recorded rows, preserve selection by
the existing source-bound history identity, and keep Copy Details/Export JSON
on the complete unpaged payload. Title-history projection uses the same
generous diagnostic bound, while malformed or migration-unknown facts remain
explicitly labelled. No retention rows are deleted, normalised, reordered in
the source envelope or fabricated by paging. The combined Foundation/Profile/
UI bundle remains green at **136 tests**, `smoke_test.py` passes (with its
documented headless Matchmaking-coordinate probe skipped), and compilation/
`git diff --check` are clean. This closes the long-history presentation slice of J4;
retention/compaction policy and title-history migration decisions remain held.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (Finance strategic-investment reader boundary):**
Finance, runway and dashboard projections now call the non-repairing strategic
investment ownership/upkeep view. A malformed or non-mapping finance envelope
therefore remains unchanged while the page reports bounded investment status
and recurring upkeep; explicit purchase and calendar-upkeep owners still use
the repairing path. The UI-data regression covers both malformed envelope
shapes and the source boundary. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (Regional Prospects throughput reader boundary):**
The Regional Prospects table now obtains its graduation-throughput summary from
a non-repairing backlog projection. Opening, filtering or refreshing the table
cannot write the monthly eligibility cache or repair malformed rules, while
calendar and simulation owners retain the cache's mutation boundary. The
UI-data regression covers malformed cache values and no rules drift. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (A3/S4 defensive payroll projections):** Finance
cash-runway and roster-cost snapshots now use bounded salary parsing and skip
malformed or non-dictionary Staff rows instead of raising during a planning
refresh. The retained staff records stay unchanged, while valid salary values
continue to feed the recurring-bill projection and cost history. A cash-runway
regression covers malformed salary evidence, no mutation and the unchanged
fixed-cost result; the focused cash-runway bundle passes **10 tests**, with
compilation and `git diff --check` clean. This closes another A3/S4 read-model
safety slice; scenario application, payroll policy and specialist acceptance
remain in the active G4 track. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 workflow follow-up (Game & Saves context feedback):** Routine
 persistence outcomes now remain beside the Game & Saves controls when that
 surface is available. Quick-save, active-universe selection and cloning,
 default-pack validation, backup/restore, database export/import/load,
 career-start conversion completion, and missing-selection guidance use the
 shared save-manager status line rather than interrupting the player with a
 transient informational dialog. High-impact choices (overwrite, delete,
 restore confirmation, migration acceptance and conversion acceptance) and
 write/validation failures retain their explicit modal or error/recovery path.
 A compatibility fallback keeps legacy/headless callers safe when no status
 widget exists; no save path, atomic writer, recovery policy, active-career
 switch, database payload or RNG boundary changes. `ui_data_regression_test.py`
 now covers the source contract (157 tests in the focused UI/persistence
 bundle), `smoke_test.py` passes with the documented headless Matchmaking
 probe skipped, and compilation/diff checks are clean. Stage 4 of 6 remains
 active with **4 major stages remaining** and **12 named card areas**
 unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 title-lineage reconciliation safety):** Company
  title reconciliation now records an explicit name-only `Vacated` or
  `Interim Vacated` lineage fact when a saved holder is no longer present in
  the source roster. The retained row carries the display name, no invented
  fighter ID, and a manual-review note; repeated reconciliation does not append
  duplicate facts. Primary belt maps with duplicate display names now fail
  closed unless exactly one matching fighter is explicitly marked champion,
  while a unique marker safely disambiguates the saved holder. No departed
  fighter is reassigned, no current record is consulted, and no RNG or finance
  state is touched. Three Profile regressions cover missing-holder vacancy
  evidence, ambiguous duplicate-name preservation and explicit-marker
  resolution; the combined Foundation/Profile/UI bundle passes **139 tests**
  with clean compilation and diff checks. This closes another identity-safe J4
  reconciliation slice; broader historical migration and retention/compaction
  policy remain held. Stage 4 of 6 remains active with **4 major stages
 remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
 user save was rebuilt or modified.

**Stage 4 verification update (maintained runner after title-lineage slice):**
The maintained runner passed all suites through Fight Night, persistence,
Foundation, title decisions, booking, finance, Media, Staff/autonomy,
Profile/UI-data, regional, child-promotion and fight-engine coverage. Smoke
passed with the documented headless Matchmaking-coordinate probe skipped. The
runner again stopped only at the pre-existing
`fight_move_selection_parity_regression_test.py` historical fixture assertion
(`Selection parity changed: bouts`); current mechanics remain equal and the
fixture digest differs because the current Fighter schema retains newer fields.
The three new title-lineage regressions introduce no additional failure. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 membership identity diagnostics):** The
membership retention read model now separates blank legacy IDs from actual
duplicate durable IDs. ID-less historical rows remain retained and count only
as incomplete coverage; the duplicate counter reports repeated non-empty IDs
without inflating the finding when several old rows predate stable identity.
The Company History header also exposes the ID-unknown count. The new
Foundation regression covers this distinction, and the focused
Foundation/Profile/UI bundle passes **140 tests** with clean compilation and
diff checks. This closes another J4/L0 diagnostic slice; historical migration
coverage and any future compaction policy remain held. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 malformed date classification):** Membership
retention diagnostics now treat non-numeric legacy month values as
date-unknown, alongside null migration dates, while retaining the raw values
for audit. Oldest/newest known-month summaries use only validated integer
months, so the Company History header cannot imply chronology from malformed
input. A new Foundation regression covers valid, malformed and null month
values; the focused Foundation/Profile/UI bundle passes **141 tests** with
clean compilation and diff checks. This closes another J4/L0 diagnostic slice;
historical migration coverage and future compaction policy remain held. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 complete membership totals):** The Profile
Company History header now uses a pure paged count over all retained
membership facts for the selected fighter, rather than the first 100-row page
returned by the UI reader. Long-career totals therefore agree with the full
history table and export while preserving the raw append-only envelope. A new
Foundation regression covers a 1,001-row history and confirms no mutation;
the focused Foundation/Profile/UI bundle passes **142 tests** with clean
compilation and diff checks. This closes another J4 presentation-truth slice;
historical migration coverage and future compaction policy remain held. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (history diagnostics and current smoke):** After
the membership count, ID-gap and malformed-date changes, the current
`smoke_test.py` passes. It still reports the documented headless
Matchmaking-coordinate probe as skipped because that display cannot lay out
the fighter table; no gameplay, save, RNG or EXE path is affected. The focused
Foundation/Profile/UI bundle remains green at **142 tests**, with clean
compilation and `git diff --check`. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 strict interval date validation):** Membership
interval projection now applies the same strict calendar parsing as the
retention summary. Boolean and float month values, malformed week values and
other non-integer boundaries remain retained but produce explicit incomplete /
unknown chronology rather than being coerced into a date. As-of reads keep
those contradictory facts visible without reordering or repairing the source.
A new Foundation regression covers these malformed types and no-mutation
behaviour; the focused Foundation/Profile/UI bundle passes **143 tests** with
clean compilation and diff checks. This closes another J4/L0 diagnostic slice;
historical migration coverage and future compaction policy remain held. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J4 malformed title-history migration safety):** The
load-boundary lineal title-history migration now treats non-dictionary legacy
rows as retained review evidence rather than calling mapping methods on them
or dropping them from the rebuilt history. Trustworthy lineal entries are
rebuilt and sorted; malformed/forward-compatible rows remain attached with an
explicitly non-lineal diagnostic path, and the migration remains idempotent.
A new Foundation regression covers preservation and version sealing; the
focused Foundation/Profile/UI bundle passes **144 tests** with clean
compilation and diff checks. This closes another J4 migration-safety slice;
historical identity coverage and future compaction policy remain held. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (current smoke after strict date validation):**
`smoke_test.py` passes after the interval reader change, with only the
documented headless Matchmaking-coordinate probe skipped. The 143-test focused
Foundation/Profile/UI bundle, compilation and `git diff --check` remain clean;
no save, RNG, gameplay settlement or EXE path was changed. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (current smoke after title-history migration):**
`smoke_test.py` was rerun after the malformed lineal title-history migration
hardening and still passes. The documented headless Matchmaking-coordinate probe
remains skipped because that display cannot lay out the fighter table; the run
reports the expected roster/free-agent/promotion/gym summary and a completed
sample fight. The focused Foundation/Profile/UI bundle remains at **144 tests**;
`py_compile` and the scoped `git diff --check` are clean. This verifies that the
load-boundary preservation change introduces no runtime or save-path regression.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A3 malformed finance projection evidence):** The
cash-runway read model now handles malformed or non-dictionary legacy
`week_transactions` rows without coercing them into a different calendar week
or mutating the retained finance shelf. Valid rows still contribute to the
paid-to-date figure; invalid rows are excluded from that figure and an explicit
unknowns notice reports their count and preserves the source for audit. A new
cash-runway regression covers malformed dates, costs and row shapes, asserting
state/RNG purity; the focused runway bundle passes **8 tests**, with clean
compilation and scoped diff checks. This closes another A3 legacy-evidence
read-model slice; scenario application and broader forecast policy remain
unchanged. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 verification update (maintained runner after A3 hardening):** The
maintained `run_regression_suite.py` reached the cash-runway, super-event,
recruitment, relationship, story, child-promotion, persistence, UI-data,
Profile, Staff, Media, scouting, regional and available fight-engine groups
successfully. It then stopped only at the pre-existing historical
`fight_move_selection_parity_regression_test.py` fixture assertion
(`Selection parity changed: bouts`); current mechanics still match and the
fixture digest differs because the Fighter schema retains newer persisted
fields. The new malformed-finance regression passes as part of the runner's
8-test cash-runway group, and the latest smoke test also passes with the
documented headless Matchmaking-coordinate probe skipped. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A2 malformed closeout evidence):** Super-event
closeout now reads malformed legacy terms with bounded diagnostic fallbacks and
fails closed with `Needs review` when a settlement package has invalid
attendance, capacity, profit or excitement evidence. A valid project still
uses the existing one-time closeout owner; an invalid package applies no
popularity, stability, safety, cash or history effect. Two new closeout
regressions cover malformed terms and malformed settlement data; the focused
closeout suite passes **18 tests**, the event-economics regression passes, and
compilation/diff checks are clean. This closes another A2 lifecycle-integrity
slice; prospective refund/deadline terms remain policy-gated. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (J1 malformed proposal options):** Booking Workbench
proposal and locked-slot readers now project malformed option lists or rows as
explicit unavailable evidence instead of raising or silently filtering them.
The two commit owners preflight the retained option before the explicit
write-boundary normaliser, so a rejected malformed click cannot rewrite the raw
proposal or route to another fighter. Valid identity-bound proposals retain the
existing deterministic commit and receipt behavior. A new regression covers
malformed lists, mixed option rows, no-mutation rejection and raw-evidence
preservation; the combined Booking/Foundation/UI bundle passes **132 tests**,
with clean compilation and scoped diff checks. This closes another J1 reader /
commit-integrity slice; firm medical reservations and scheduled-event mutation
policy remain held. Stage 4 of 6 remains active with **4 major stages remaining**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 verification update (current smoke after A2/J1 hardening):**
`smoke_test.py` passes after the super-event closeout and Booking Workbench
fail-closed changes. The documented headless Matchmaking-coordinate probe is
still skipped because that display cannot lay out the fighter table; the
ordinary roster, promotion, gym and sample-fight checks remain green. No save,
RNG or EXE path was changed. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (S4 malformed AI employment evidence):** The AI staff
affordability/runway projection now tolerates malformed legacy salary fields
without repairing or dropping the retained employee row. The invalid salary is
treated as zero only inside the read-only diagnostic, while the original row
remains available for explicit review and the hiring/expiry owners are
unchanged. A new regression covers malformed salary evidence and state/RNG
purity; the focused Staff employment/management bundle passes **53 tests**, with
clean compilation and scoped diff checks. This closes another S4 diagnostic
slice; approved long-run payroll, retention and qualification thresholds remain
the policy gate. Stage 4 of 6 remains active with **4 major stages remaining**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 progress update (J4 malformed membership-row diagnostics):** The
membership retention summary now separates valid and malformed retained rows,
and the Profile Company History header surfaces the malformed count alongside
date-unknown and ID-unknown coverage. Readable event pages continue to filter
defensively; the raw append-only archive is never normalised or truncated during
refresh. A new Foundation regression covers mixed valid/non-dictionary rows,
retention counts, readable filtering and no-mutation behavior. The combined
Foundation/Profile/UI bundle passes **145 tests**, with clean compilation and
scoped diff checks. This closes another J4/L0 evidence-clarity slice; historical
migration coverage and future compaction policy remain held. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 AI expiry malformed-term retention):** The AI
staff contract worker now holds malformed legacy `contract_months` evidence for
explicit review instead of silently treating it as an expiry. Non-dictionary
legacy staff rows are retained for audit, the original malformed value is kept,
review notices are deduplicated per calendar month, and payroll projection is
defensive. Valid expiry and identity-preserving market return behavior remains
unchanged. A new regression covers retention, no duplicate notices and no data
loss; the focused Staff employment/management bundle passes **54 tests**, with
clean compilation and scoped diff checks. This closes another S4 employment
integrity slice; approved long-run payroll, retention and qualification
thresholds remain the policy gate. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 verification update (current smoke after S4 expiry hardening):**
`smoke_test.py` passes after the AI staff expiry-worker change. The documented
headless Matchmaking-coordinate probe remains skipped because that display
cannot lay out the fighter table; roster, promotion, gym and sample-fight
checks remain green. No save, RNG, gameplay settlement or EXE path was changed.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (S3 malformed progression evidence):** Staff
quarter-close progression now skips malformed legacy spend/month evidence rather
than crashing or allowing it to qualify a skill gain. Invalid work rows remain
in the retained ledger for audit; malformed skill baselines fail closed without
changing the employee. A new regression covers valid qualification alongside
malformed work rows and confirms the ledger is preserved; the focused Staff
management/employment bundle passes **55 tests**, with clean compilation and
scoped diff checks. This closes another S3/L0 evidence-gate slice; long-run
qualification thresholds and progression balance remain policy-gated. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A1 owned-calendar source coverage):** The read-only
Owned Calendar index now exposes indexed/shown counts and an explicit partial
coverage diagnostic when legacy schedule containers or event rows are
malformed. Valid event IDs, owner/source separation, status projection and
display-only filtering are unchanged; no schedule, fighter, ownership or
finance state is repaired or mutated during refresh. The dashboard summary
surfaces malformed source-row counts, and a new regression covers mixed valid
and malformed MMA/child schedules. The combined Owned Calendar/UI-data bundle
passes **91 tests**, with clean compilation and scoped diff checks. This closes
another A1/L0 read-model evidence slice; child scheduling/control policy
remains held. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 verification update (current smoke after Owned Calendar diagnostics):**
`smoke_test.py` passes after the dashboard switched to the diagnostic Owned
Calendar projection. The documented headless Matchmaking-coordinate probe is
still skipped because that display cannot lay out the fighter table; roster,
promotion, gym and sample-fight checks remain green. No save, RNG, schedule,
ownership or EXE path was changed. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (A3 malformed event-date revisions):** Cash-runway
scenario source revisions now sort malformed legacy event dates defensively and
expose a diagnostic count rather than crashing during save or read. The raw
scheduled event values remain unchanged; no planning refresh coerces or repairs
their dates. A new regression covers source-revision diagnostics, scenario save
and schedule purity; the focused cash-runway bundle passes **9 tests**, with
clean compilation and scoped diff checks. This closes another A3 legacy-input
read-model slice; scenario application and forecast policy remain unchanged.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 verification update (maintained runner after the latest slices):** The
 maintained runner passed Fight Night presentation/archive/layout, trait and
 release gates, smoke, persistence, testing, tournament, Foundation, title
 decision, booking, preparation, rules/help, pause/checkpoint, finance,
 narrative, UI-data, profile, performance, AI-card, scouting, regional,
 media, Staff/autonomy/specialty/employment, Academy, schedule, owner-goal,
 runway, super-event closeout, recruitment, relationship, story, child
 promotion and the available fight-engine suites. It stopped at the existing
 historical `fight_move_selection_parity_regression_test.py` assertion
 `Selection parity changed: bouts`; the mechanics still agree, while the
 fixture digest differs because the current Fighter schema carries newer
 persisted fields. This remains a release-diagnostic/fixture decision, not a
reason to weaken the historical adapter or rewrite the fixture. The focused
A2/event-economics check also passes **18 tests**. Stage 4 of 6 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 malformed staff-term reader boundary):** Staff
contract remaining/status readers now fail closed on malformed legacy term
values instead of raising during a page refresh or Academy Coach assignment
check. The raw term remains unchanged for the employment audit and explicit
repair boundary, while valid contract and expiry behavior is unchanged. The
focused Staff employment/Academy bundle passes **15 tests**, with compilation
and `git diff --check` clean. This closes a defensive S4 read-model slice;
long-run retention, affordability and specialist policy acceptance remain in
the active G4 track. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (S4 Staff table evidence safety):** Staff roster,
candidate, expiry and specialty readers now project missing, non-numeric or
non-dictionary legacy employee rows as explicit unavailable evidence. Invalid
values never rewrite the retained employee, and selecting a malformed row
fails closed instead of opening a guessed profile. Contract term/status and
Academy Coach assignment checks share the same safe projection. The focused
Staff employment/management/Academy bundle passes **61 tests**, with
compilation and `git diff --check` clean. This closes another S4 read-model
slice; long-run retention, affordability and specialist policy acceptance
remain in the active G4 track. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 Staff contract negotiation evidence safety):**
Contract-target and offer-score readers now fail closed for malformed salary,
reputation, negotiation-heat and term inputs, including non-dictionary legacy
rows. Expiry-warning generation skips malformed rows and treats an invalid
salary as an explicit zero only inside the notice; the raw staff evidence is
never repaired, reassigned or dropped. Valid offer scoring and warning text
remain unchanged. New regressions cover malformed offer inputs, unchanged
retained rows and warning-reader safety; the focused Staff
employment/management/Academy bundle passes **63 tests**, with compilation and
`git diff --check` clean. This closes another S4 defensive contract-reader
slice; long-run retention, affordability and specialist policy acceptance
remain in the active G4 track. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 contract-tick retention):** The player-staff
calendar contract worker now holds malformed legacy terms for explicit review
instead of decrementing or expiring them, and keeps non-dictionary roster rows
available to the audit. Review notices are idempotent at the saved
month/week boundary. Payroll aggregation skips malformed salary rows and
continues to produce a bounded total, while valid expiry, assignment hold and
departure behavior remains unchanged. A regression covers malformed `None`
terms, retained raw salary/term evidence, non-dictionary rows, no duplicate
notice and payroll safety; the focused Staff employment/management/Academy
bundle passes **64 tests**, with compilation and `git diff --check` clean. This
closes another S4 employment lifecycle slice; long-run retention,
affordability and specialist policy acceptance remain in the active G4 track.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 progress update (S4 AI payroll settlement safety):** AI monthly
operating-cost settlement now skips malformed or non-dictionary Staff salary
rows while preserving them in the promotion's retained employment evidence.
Valid salaries continue to affect the existing overhead calculation and
finance receipt; invalid market salaries cannot become a free hire and remain
available for explicit review. A Staff employment regression covers AI
operating-cost settlement, raw-row retention and malformed-market handling; the
focused Staff employment bundle passes **17 tests**, with compilation and
`git diff --check` clean. This closes another S4 employment/payroll boundary;
long-run retention, affordability and specialist policy acceptance remain in
the active G4 track. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (S4 Staff compatibility-load safety):** Staff
compatibility-profile loading now handles malformed role and skill fields
without rewriting those source values. Derived specialty, reputation and Scout
subskills use bounded fallbacks, so a legacy employee row can still be opened
and audited instead of crashing the load boundary. A Staff employment
regression covers malformed role/skill retention and derived-field safety; the
focused Staff employment bundle passes **18 tests**, with compilation and
`git diff --check` clean. This closes another S4 legacy-load slice; employment
policy, retention thresholds and specialist mechanics remain in the active G4
track. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 verification update (Staff/Finance integration):** The normal
`smoke_test.py` path passes after the contract-reader, payroll and malformed
market hardening. It still reports the documented headless Matchmaking
coordinate probe as skipped because that display cannot lay out the fighter
table; roster, promotion, gym, sample-fight, persistence and quick-save checks
remain green. The focused Staff/Academy/cash-runway bundle passes **77 tests**
and compilation plus scoped diff checks are clean. No EXE, user save, RNG or
settlement state was changed by verification. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated.

**Stage 4 progress update (S4/Scouting helper safety):** Shared Staff skill,
role-information, scout-capacity and scout-workload helpers now fail closed on
malformed employee rows, numeric values and scouting containers. Non-dictionary
legacy rows are ignored for calculations but remain in the roster for audit;
valid staff identity and workload matching are unchanged. A Staff employment
regression covers safe skill/role/capacity/workload projections and duplicate
identity avoidance; the focused Staff employment bundle passes **19 tests**,
with compilation and `git diff --check` clean. This closes another S4/scouting
read-model slice; employment policy, retention thresholds and specialist
mechanics remain in the active G4 track. Stage 4 of 6 remains active with **4
major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A3/S4 Finance payroll boundary):** Finance refresh
and month-end office/payroll work now use the defensive Staff salary projection.
Malformed or non-dictionary rows remain retained for audit and contribute no
invented payroll, while valid salary evidence continues to drive the existing
recurring-cost receipt and runway display. A Staff employment regression covers
the month-end payroll task and raw-row preservation; the focused Staff
employment bundle passes **20 tests**, with compilation and `git diff --check`
clean. This closes another A3/S4 recurring-cost read/write boundary; scenario
application, payroll policy and specialist acceptance remain in the active G4
track. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 verification update (latest smoke after Staff/scouting hardening):**
`smoke_test.py` passes, including roster/promotion/gym setup, sample-fight,
persistence and quick-save checks; the documented headless Matchmaking
coordinate probe remains explicitly skipped because that display cannot lay
out the fighter table. The combined Staff/Academy/Scouting/cash-runway focus
passes **103 tests**, and the touched modules compile cleanly with
`git diff --check`. The maintained runner remains green through all available
groups and stops only at the known historical
`fight_move_selection_parity_regression_test.py` fixture-digest assertion
(`Selection parity changed: bouts`); no new failure is introduced. No EXE,
user save, RNG or settlement state was changed by verification. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated.

**Stage 4 verification update (latest affected-surface bundle):** The current
Staff, Academy, Scouting, Finance/runway, UI-data, Fight Night experience,
Profile and related presentation regressions pass together (**240 tests**).
This confirms the defensive Staff/scouting changes did not regress identity
selection, lazy page construction, profile history, Fight Night rendering or
read-only finance behavior. The normal smoke path also passes; the maintained
full runner's only known stop remains the historical fight-move parity fixture
digest mismatch documented above. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (S4 Staff employment audit evidence):** The long-run
Staff Evidence Audit now includes the retained employed roster and shared
market as hard evidence. It reports malformed/non-dictionary rows, missing
durable Staff IDs, missing roles, invalid or negative salary and contract-term
values, and duplicate IDs within a source or across employed-versus-market
sources. Findings carry the source label and Staff ID so a reviewer can locate
the exact record without relying on a mutable row position. The audit remains a
pure diagnostic: it does not call compatibility repair, reassign identities,
tick contracts, charge payroll, consume RNG or alter the work/progression
ledger. The audit window now shows source and Staff ID columns with horizontal
scrolling while preserving the complete JSON detail for each finding. Focused
Staff, employment, Academy, Scouting, cash-runway and UI-data regressions pass
**192 tests**, with compilation and scoped `git diff --check` clean. Stage 4 of
6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (Foundation receipt data-quality evidence):**
Foundation work-card projections now keep their existing bounded numeric fields
while also exposing Recorded/Unknown state and a diagnostic list for malformed
attempt, quote and actual-spend values. Staff budget readers skip malformed
calendar boundaries and spend fields without normalising the retained work
ledger. The Staff work table and read-only receipt detail use Unknown rather
than crashing or presenting a coerced zero, and show the underlying data-quality
note when one exists. The raw receipt remains untouched for audit and all valid
budget, receipt and progression behaviour is unchanged. Foundation and Staff
regressions pass **79 tests**, with compilation and scoped `git diff --check`
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V11 Scouting talent-search identity):**
Scouting Centre talent-search rows now prefer their saved `assignment_id` and
otherwise fingerprint the authored search request (scout, region, division,
focus, level, priority, style, age band and start boundary). Mutable status and
result fields are excluded, so completing a search or resorting the reader does
not redirect the selected assignment. Completely empty/malformed legacy rows
retain an explicit non-durable fallback, while duplicate source IDs receive
deterministic suffixes. The change is reader/identity-only: report evidence,
scouting capacity, RNG and assignment mutation remain untouched. Focused UI and
scouting regressions cover durable IDs, legacy fingerprints and source-bound
result fighters; compilation remains clean. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (M2 sponsor activation preview):** Active sponsor
cards now place the contracted maximum, activation-adjusted current estimate,
full/half-fee basis, term and readiness reason in one decision surface. Legacy
trust, stability, fee, term, roster and campaign-history values are projected
defensively; malformed evidence cannot crash the comparison reader or rewrite
Finance state, and the settlement-owned activation path remains unchanged.
The sponsor preview regression now covers malformed legacy inputs, explicit
at-risk wording and state/RNG purity. Media-plan regressions pass **23 tests**,
with compilation and scoped `git diff --check` clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (company hub legacy-data reader):** Company detail
tabs now project malformed history, finance containers and Staff rows as
explicit unavailable/Unknown evidence. Non-dictionary Staff records remain
visible for audit, missing salary/skill values no longer raise formatting
errors, and valid company summaries/actions retain their existing meaning. The
reader does not repair, reassign or reinterpret roster, contract, promotion or
finance state while opening or refreshing the hub. A UI-data regression guards
the defensive projection; the affected UI-data suite passes **89 tests**, with
compilation and scoped `git diff --check` clean. Stage 4 of 6 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A3/M2 commercial reader resilience):** Finance
history, annual outlook, roster-cost and selected-week detail readers now keep
malformed legacy rows visible as explicit Unavailable/Unknown evidence. Safe
numeric projections prevent a bad retained amount from aborting the Finance
refresh, while the raw history remains unchanged. Finance reconciliation now
returns a diagnostic for malformed retained values and leaves valid balance
semantics unchanged. The Media Rights dashboard and settlement reader apply
the same boundary to malformed contracts, offers, campaign history and
receipts: stable IDs are retained where present, identity-less rows are shown
under explicit legacy markers, and opening/refreshing remains free of offer
generation, settlement, cash spend and RNG draws. Added regressions cover
malformed rights terms and UI history projections; the affected Media/UI
bundle passes **115 tests**, with compilation and scoped `git diff --check`
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 progress update (A3 cash-runway reader resilience):** The 12-week
cash-runway table now projects malformed forecast rows as explicit
Unavailable/Unknown evidence, uses bounded numeric display values, and keeps
duplicate offsets from causing widget identity errors. Summary cards tolerate
malformed as-of, recurring and conditional sections while retaining the
planning-only/no-reservation contract. Saved scenario counts ignore malformed
rows without repairing the retained snapshots. The affected Finance, Media,
Staff, Foundation and UI bundle passes **204 tests**, with compilation and
scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 progress update (A3 saved-scenario reader resilience):** The saved
cash-runway scenario window now keeps malformed snapshot rows visible as an
explicit unavailable entry, bounds attendance assumptions for display, and
uses safe date/horizon/forecast formatting. Duplicate scenario IDs remain
deterministically addressable; the detail reader retains the full saved
payload without applying edits, moving events, reserving cash or rerunning a
forecast. Finance, Media, Staff, Foundation and UI regressions pass **251
tests**, with compilation and scoped `git diff --check` clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 sponsor settlement guard):** The
settlement-owned sponsor activation path now fails closed on malformed legacy
trust, threshold, campaign-history, roster and event-month values. Valid
full/half-fee settlement semantics remain unchanged; an unavailable duty is
reported as an at-risk reason rather than crashing the event path or inventing
evidence. The focused Media/UI bundle passes **116 tests**, with compilation
and scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 receipt display guard):** Media settlement
receipt tables and their structured detail reader now tolerate malformed
numeric amounts, relationship deltas, sponsor rows and receipt containers.
Rows remain selectable through saved receipt/event identity, while malformed
legacy entries stay visible under explicit review markers and the complete
stored payload remains available. The reader still cannot settle, regenerate,
charge or consume RNG. The focused Media/UI bundle passes **117 tests**, with
compilation and scoped `git diff --check` clean. Stage 4 of 6 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 progress update (A4 owner-objective reader resilience):** The Owner
Objectives reader now treats a malformed/non-list saved objective collection
as an empty projection without rewriting it, and keeps malformed individual
rows visible as `Unavailable owner objective / Review required`. Invalid
deadlines no longer crash the refresh; metric projection remains read-only,
while the completed-calendar worker remains the sole boundary for observations
and terminal outcomes. The Owner Goals and UI-data regressions pass **97
tests**, with compilation and scoped `git diff --check` clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (Finance/Media/Staff/UI integration):** The
maintained affected-surface runner passes the Finance, Media, Foundation,
Staff, Academy, Scouting, cash-runway, Owner Objectives and UI-data suites
together (**261 tests**). The isolated runner also passes each requested suite,
including the smoke path's documented headless Matchmaking skip. Compilation
and scoped `git diff --check` remain clean. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 legacy media envelope retention):** The
explicit Media state boundary now retains malformed non-list contract/offer
containers under legacy-raw keys before preparing safe working collections.
Malformed rights terms no longer crash state initialisation, while active
contract detection remains positive-integer bounded and valid legacy aliases
continue to migrate exactly as before. This is an explicit action/load-boundary
repair, not a refresh-time offer generation or settlement side effect. Media
plan regressions pass **27 tests**, with compilation and scoped
`git diff --check` clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 settlement numeric boundary):** Rights
eligibility and event-audience calculations now fail closed when legacy
contract terms, package metrics, fighter media values or event fight lists are
malformed. Sponsor fee calculation also returns a bounded zero rather than
raising on an invalid retained fee. During settlement, valid entitlement and
relationship fields continue through the ordinary transition; malformed
relationship/strike evidence is left untouched and the saved audience row is
marked `Needs review` with the affected fields. A non-list sponsor envelope
cannot suppress the rights receipt. The Media plan regression suite now passes
**32 tests**, including malformed settlement inputs and the review-row
presentation, with compilation and
scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 monthly lifecycle boundary):** Media month
processing now holds an active contract with malformed month evidence for
explicit review while retaining the original value, so a calendar tick cannot
guess an expiry or terminate a package silently. Pending renewals with a
malformed entitlement count remain `Needs review` and are not activated after
a fulfilled predecessor. Valid expiry, shortfall, termination and successor
activation semantics are unchanged. The Media plan regression suite passes
**34 tests**, including malformed calendar-boundary cases, with compilation
and scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 read-only active-contract lookup):** The
active-rights accessor now reads through the non-mutating finance envelope, so
dashboard/account refreshes and missing-legacy-state checks cannot seed or
rewrite finance merely to determine whether a contract exists. Explicit media
load, settlement and acceptance owners still initialise their state before
writing. Media plan and media-system regressions pass **36 tests**, with
compilation and scoped `git diff --check` clean. Stage 4 of 6 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 custom rights-package load):** Media-system
initialisation now bounds malformed custom rights-package numbers and treats a
single string market as one market instead of splitting it into characters.
Invalid custom values fall back to the authored baseline while retaining valid
custom overrides; a malformed universe package can no longer abort startup or
leave the Media catalogue empty. Media plan/system regressions pass **37
tests**, with compilation and scoped `git diff --check` clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 rights-history lifecycle truth):** The
read-only contract-history projection now returns `Needs review` when retained
month, entitlement or delivery-strike evidence is malformed, rather than
coercing unknown values into a false `Fulfilled` label. Valid `Fulfilled`,
`Expired with shortfall` and `Terminated` rows retain their existing semantics;
no refresh-time repair or settlement is introduced. Media plan/system
regressions pass **38 tests**, with compilation and scoped `git diff --check`
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (M2 AI offer and market refresh boundary):** AI
media-deal review now filters saved offers through an identity and numeric-term
gate before scoring them. A malformed legacy offer is retained in the saved
collection and marked for review; it cannot be selected, priced or passed to
the acceptance owner, while a valid sibling offer can still be evaluated by
the normal strategy logic. Active-contract checks use the same bounded month
and entitlement interpretation, and malformed promotion strategy, size or
reputation values no longer raise during review. Monthly media-market refresh
also keeps malformed outlet volatility, budget and base-fee fields untouched,
records an explicit review reason and uses bounded values only for the
diagnostic market snapshot. Valid outlets continue to receive their ordinary
budget/fee movement. The Media plan suite passes **40 tests** and the combined
Media/system/UI focused bundle passes **131 tests**, with compilation and
scoped `git diff --check` clean. Stage
4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (M2 offer expiry and signing boundary):** Saved
Media offer expiry now retains non-dictionary rows and offers with unknown
expiry values for review instead of dropping them or raising during a refresh.
The explicit acceptance owner resolves only dictionary offers with a stable
ID, positive numeric fee/reach/month/event terms and an outlet identity; a
malformed offer remains in place, records a review marker and cannot spend
cash or create a contract. Normal valid expiry, rejection and acceptance
semantics remain unchanged. The Media plan suite passes **42 tests** and the
combined Media/system/UI focused bundle passes **133 tests**, with compilation
and scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 negotiation boundary):** Sponsor and Media
Rights counteroffers now resolve only dictionary rows with parseable numeric
terms and company evidence. Malformed fee, fit, reach, standards, commitment
or relationship values remain attached to their original offer with an
explicit review marker; they cannot be countered, charged, removed or
converted into a contract. Valid counters preserve the existing one-counter
roll, fee/guarantee synchronisation and relationship changes. The combined
Media/system/UI focused bundle passes **135 tests** and the broader affected
Finance/Media/Staff/Foundation/Academy/Scouting/UI bundle passes **278 tests**,
with compilation and scoped `git diff --check` clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (M2 sponsor envelope and media-system inputs):**
Sponsor agreements are now part of the explicit Media state boundary, so a
malformed saved agreement container is retained under a legacy-raw key before
safe working lists are prepared. Sponsor offer selection ignores non-dict
legacy rows, while acceptance keeps the existing eight-deal protection and
cannot format, sign or remove an invalid offer. Media-system startup also
retains malformed company containers, bounds the saved market-month marker
and uses safe promotion/company values for action capacity and market scoring.
The original raw evidence remains available for review; valid sponsor and
market behaviour is unchanged. The Media plan suite passes **44 tests** and the
broader affected Finance/Media/Staff/Foundation/Academy/Scouting/UI bundle
passes **282 tests**, with compilation and scoped `git diff --check` clean.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (M2 monthly sponsor expiry boundary):** The
monthly business tick now retains malformed sponsor agreements and unknown
term values for explicit review, while valid agreements still decrement and
expire exactly once. The legacy media-rights fallback follows the same rule:
malformed terms remain untouched rather than being guessed over or replacing
the saved package. The normal Media contract path continues to own modern
contract expiry, preventing duplicate decrements. Finance/Media/Staff/
Foundation/Academy/Scouting/UI regressions pass **284 tests**, with compilation
and scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J9 regional invitation lifecycle boundary):**
Regional-host invitation date arithmetic and quarter checks now fail closed on
malformed retained values. Expiry holds an offered/accepted/scheduled row for
review when its boundary is unknown, rather than silently expiring or deleting
it. Binding refuses malformed guarantee or local-completion terms without
mutating the event, and settlement ignores malformed result containers or
cash/entitlement values without paying an unverified guarantee. Valid
generation, exact region/venue/date binding, one-entitlement payment and
zero-penalty cancellation remain unchanged. Regional invitation/feasibility,
Media and the broader affected bundle pass **294 tests**, with compilation and
scoped `git diff --check` clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J8 durable tournament-history reader):** The
read-only Tournament History index now isolates malformed retained draw
containers from valid editions. Non-list bracket envelopes remain excluded
without aborting the page; malformed entrant, entrant-ID, seed, substitution,
result-reference or stage containers keep their edition row addressable with
an explicit `review_reasons` marker. The permanent result-index writer also
preserves a malformed tournament envelope under a legacy-raw key and safely
filters malformed fight/stage rows. Only structurally valid draw/stage facts
are presented, so the detail reader cannot iterate a legacy scalar as a match
or invent a result. Review-required rows carry a visible status badge in the
history table as well as the detail explanation. Valid seeds, substitutions, stage matches, replay state,
stable edition/source IDs and future fields remain unchanged, and opening or
filtering the history does not resolve fighters, refresh archives, draw RNG or
write preferences. `j8_tournament_history_regression_test.py` plus
`ui_data_regression_test.py` and persistence checks pass **100 tests**; the
post-change smoke playtest passes with the documented headless Matchmaking
probe skipped. Compilation and scoped `git diff --check` are clean. Stage 4 of
6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 delivery slice (V17 Fight Night control centre):** The former
single-purpose Event Log page now opens as a Fight Night control centre. A
read-only status panel distinguishes a card due now from the next scheduled
card and keeps the existing Watch Due Event route intact. A Recorded Events
index is projected from the saved player/AI replay shelves and permanent
result index, de-duplicated by saved result identity with an explicit legacy
display fallback. Each row shows date, promotion, event, bout count and
whether a full replay is retained or only results/index evidence remains.
Double-clicking a replay opens the existing no-reapply replay path; a
results-only card remains browseable through the existing result-card reader.
Browse Results and Watch Latest Replay actions are shortcuts to existing
read-only routes, while Jump to Full Log exposes the complete original
`event_log` with the established semantic colours. Refreshing the landing
page only rebuilds these projections, preserves archive identities and never
prepares a card, reruns preparation, settles a fight, regenerates commentary,
or changes the source log. `fight_night_archive_rows` and the new UI
regression cover duplicate identities, stale replay badges,
replay/results-only labelling and source immutability. The focused UI/Fight
Night runner passes **128 tests**; the post-change smoke playtest passes with
the documented headless Matchmaking probe skipped. Compilation and scoped
`git diff --check` are clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 delivery slice (A6 named scouting watchlists):** Scouting now
exposes explicit named-list management alongside the compatibility Main
Watchlist. The Target Board provides create, rename, switch and archive
actions, with duplicate display names disambiguated by a stable watchlist-ID
suffix. The saved list keeps fighter IDs and alert settings separate from
scouting reports and two-to-four-candidate Decision Packs; archiving stops a
list driving active alerts but retains its members, notes, reports and pack
references. The active selector is rebuilt from a defensive read model, so
opening or refreshing Scouting does not normalise malformed retained rows.
Explicit actions resolve by watchlist ID, preserve the existing shortlist
mirror for `WATCH-main`, and fail closed for archived/unavailable lists.
Creating or editing a list never commissions a report, reveals hidden ratings,
signs a fighter or deletes evidence. `scouting_regression_test.py` now passes
**26 tests**, including list lifecycle, archived-member retention and
malformed-reader immutability; the UI data suite passes **93 tests**. The
post-change smoke playtest also passes with the documented headless
Matchmaking probe skipped. The affected source compiles cleanly and `git
diff --check` is clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 delivery slice (A7/J10 defensive story and chronicle readers):** The
Storylines, World Chronicle and World Hub news readers now read through bounded, non-mutating
projections. Valid rows retain their saved story/chronicle identities, recorded
beats, participants, context routes and filter/selection behaviour. Malformed
legacy rows or fields remain visible as `Needs review`/`Unavailable` with a
specific data-quality note; invalid dates no longer crash a reader or turn into
fabricated calendar facts. The projection never repairs, deduplicates, drops
retained evidence, regenerates a story, or advances a followed-story cursor;
explicit load/migration and follow/acknowledge actions remain the only write
boundaries. Context links prefer saved fighter IDs and fail closed for
duplicate name-only companies across World Hub, Chronicle and Media story
readers. `ui_data_regression_test.py` now passes **95
tests**, and the combined story-briefing/UI runner passes **100 tests**. The
affected source compiles cleanly and `git diff --check` is clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 delivery slice (V01 defensive Dashboard readers):** Dashboard result,
change-journal and scouting panels now consume bounded, non-mutating projections
before formatting cards or queue rows. Valid mappings are copied for presentation;
malformed result containers/rows and malformed journal evidence remain visible as
explicit `Unavailable` review rows, while malformed scouting report/search
entries are skipped safely without aborting the repaint. Spectator Mode retains
newest-result and newest-story ordering, and the existing content/source-bound
notice IDs and selection restoration are unchanged. The helper layer never
repairs, truncates, deduplicates or regenerates retained data, and no dashboard
refresh can spend cash, draw RNG, advance the calendar or substitute a different
notice/action. `ui_data_regression_test.py` plus the Story Briefing suite now pass
**102 tests**; the affected source compiles cleanly and scoped `git diff --check`
is clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 delivery slice (J1 identity-safe Workbench commits):** Booking
Workbench and locked-slot replacement controls now resolve the selected option by
the saved candidate fighter ID after a reader refresh. The UI keeps its stable
Treeview identity map and refuses to commit an option without an ID or when the
retained proposal contains duplicate IDs; it never converts the visible row back
into a mutable option index. The existing index-shaped commit methods remain as
compatibility owners for older callers, while new identity wrappers resolve one
saved match and delegate to the same Foundation quote/validation/exactly-once
receipt path. Locked-slot edits retain the original fingerprint and unaffected
corner, and malformed saved alternatives remain visible as unavailable review
rows. Tentative medical drafts use the selected stored row directly and remain
non-binding. `booking_workbench_regression_test.py`, `ui_data_regression_test.py`
and the Story Briefing suite pass **117 tests**; source compilation is clean and
scoped `git diff --check` reports no errors. Stage 4 of 6 remains active with **4
major stages remaining** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 duplicate-name profile links):** Generic
tree-profile fallbacks, Rankings detail and rivalry summaries now share
`resolve_unique_fighter_name`. They can use an id-less legacy display name
only when exactly one saved career matches; duplicate or missing names remain
unavailable instead of being selected by roster iteration order. Stable row
maps and saved IDs remain preferred, and this reader-only compatibility change
does not alter ratings, rankings, rivalry state or gameplay. The UI-data
regression covers unique, duplicate and missing-name outcomes; compilation and
focused tests remain clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 delivery slice (V08 Media Rights offer identity):** The Media Rights
market reader now projects each saved offer through a source-bound identity map.
Authored offer IDs are authoritative; id-less legacy dictionaries receive a
deterministic fingerprint of their retained terms, and completely empty legacy
rows receive an explicitly non-durable UI marker. Duplicate identities get
deterministic suffixes. Refreshes preserve the selected offer by that identity,
while accept, counter and reject resolve only to the mapped saved offer ID; an
id-less or malformed row remains readable for review but cannot mutate a
different offer. Existing contract/offer schemas, one-counter rule, quote and
settlement owners are unchanged, and refresh remains free of offer generation,
cash spend and RNG. `media_system_test.py`, `media_plan_regression_test.py`,
`booking_workbench_regression_test.py`, `ui_data_regression_test.py` and the
Story Briefing suite pass **167 focused tests**; compilation and scoped
`git diff --check` are clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (S3/S4 Staff policy reader boundary):** Staff
summary, effective-autonomy and management-panel refreshes now use defensive
read projections over the retained policy envelope. A malformed legacy mode,
brief, exception, cap or container renders a safe fallback and remains available
to the evidence audit; the repaint never calls `ensure_staff_management_state`,
rewrites rows, increments revisions or changes delegation authority. Explicit
policy/brief edits and the completed-calendar worker continue to own normalisation
and writes. Staff management, UI and Story Briefing coverage passes **150 tests**;
source compilation and scoped `git diff --check` are clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 delivery slice (V01 dashboard semantic accents):** Promoter Dashboard
decision rows now use the shared semantic status palette: urgent notices use the
negative token and normal notices use the warning token, with contrast selected
from the active theme. The same tags are included in the live retheme registry,
so switching palettes cannot leave pale dark-theme text on light surfaces. This
is presentation-only: notice content, source-bound selection, routes and saved
event/journal evidence are unchanged. Dashboard/UI and Story Briefing coverage
passes **102 tests**; `ui.py` compiles and scoped `git diff --check` is clean.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (S3/S4 Staff brief identity):** Staff brief
refreshes now retain the saved `brief_id` as the action key, add deterministic
suffixes when duplicate source IDs are present, and keep id-less legacy rows
explicitly non-durable. Commit, Requeue and Cancel resolve the selected row
through the saved brief map; a visible position or a suffixed UI key is never
passed to the mutation owner. Malformed brief/target/action containers remain
readable without a refresh-time repair. Staff management and UI regressions pass
**49 tests**; source compilation and scoped `git diff --check` are clean. Stage
4 of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J5 frozen Drug Testing reader health):** Drug
Testing case readers now expose an explicit envelope-health projection. A
non-mapping or non-list retained case container reports `Unavailable`; malformed
rows in an otherwise readable list report `Needs review` with a count. The
reader never invokes the save-repairing initializer, retests a fighter, changes
injury/title state, creates a sanction or rewrites evidence. The Cases window
distinguishes an empty ledger from unavailable saved evidence, and its row/timeline
accents use the shared semantic palette while preserving every status word and
stored field. Drug Testing, Staff, UI and Story Briefing coverage passes **170
tests**; source compilation and scoped `git diff --check` are clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V01 Inbox reader boundary):** Inbox refreshes
now derive missing legacy dates and read flags on defensive display copies,
retain malformed rows as explicit unavailable evidence, and keep source-bound
message mappings for Resolve, medical decisions and context navigation. Sorting,
filtering and the 160-row display cap operate on the projection; opening Inbox
no longer calls `normalize_inbox_messages`, rewrites the retained shelf or
changes message state. Explicit mail actions and the calendar/migration owners
remain the only write paths. The Inbox/UI regression plus the post-change smoke
playtest pass; `world.py`/`views.py` compile and scoped `git diff --check` is
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V13 World Hub promotion reader):** World Hub
promotion rows now resolve through saved `promotion_id` values when present,
with deterministic name/region fingerprints for legacy rows and deterministic
suffixes for duplicate identities. Refreshes retain the selected company by
identity across reputation sorting and never reinterpret a stale Treeview key
as another promotion. Missing or malformed legacy `show_history` containers are
read as an empty display state rather than repaired during repaint; the
calendar/load owners remain the only write boundaries. The World Hub/UI
regression bundle passes **104 tests**, source compilation and scoped
`git diff --check` are clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (A7 followed-story reader boundary):** Fighter
profile follow-state checks now use `story_subscriptions_read_model` instead
of the save-repairing subscription initializer. Followed Story Briefings also
prefer the defensive storyline projection and safely skip malformed retained
thread rows in headless hosts. Opening a profile, storyline or briefing keeps
subscription snooze/cursor fields, story beats and raw containers unchanged;
only explicit follow, acknowledge, snooze and unfollow actions may normalize or
write them. Story Briefing, UI and source-bound reader tests pass **106 tests**;
`world.py`/`views.py` compile and scoped `git diff --check` are clean. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A6 Decision Pack reader boundary):** Scouting
Decision Pack refreshes now consume retained rows through a defensive projection
without calling `ensure_scouting_decision_packs`. Valid saved `pack_id` values
remain the durable row key; id-less legacy rows use deterministic fingerprints,
duplicate source IDs receive suffixes, and malformed/non-dictionary rows stay
visible as `Unavailable` review entries. Selection is restored by the original
source row or stable base identity, while create/edit actions retain the normal
explicit migration/write owner. The read model safely bounds malformed
candidate lists, comparison criteria and week values without commissioning a
report, changing shortlist state, consuming RNG or rewriting saved evidence.
Recruitment decision-pack, UI and source compilation checks pass **104 tests**;
scoped `git diff --check` is clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 scouting evidence parsing):** Scouting
confidence, completion-date and estimate helpers now fail closed on malformed
retained fields. Invalid values remain untouched, confidence falls back to a
bounded safe value, current/full/discovery predicates refuse to infer freshness,
and range estimates return the supplied default rather than inventing a report
date. This prevents malformed legacy dossiers from crashing Target Board,
Scouting Centre or profile comparisons while preserving the existing
assignment/migration write boundary. Scouting, performance and UI coverage
passes **138 tests**; `world.py`/`views.py` compile and scoped
`git diff --check` are clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 Scouting reader boundary):** Target Board
and Scouting Centre refreshes now stay on defensive projections instead of
calling `migrate_scouting_state` while a page is being opened or repainted.
Retained reports/searches are filtered to safe mapping rows, malformed
containers remain empty rather than being rewritten, and display estimates use
`migrate=False`/the already-read report. This keeps Scouting Mode values dated
and evidence-bound without commissioning a report, drawing RNG, changing the
shortlist or mutating the saved shelf. Scouting, performance, UI and source
compilation checks pass **146 tests**; scoped `git diff --check` is clean. Stage
4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 Fighter Search history reader):** World
Fighter Search now derives its universe-record label through the non-mutating
`fighter_history_baseline_for_profile` projection. Search, filtering and
pagination no longer call `ensure_fighter_history_baseline` or write imported
record metadata merely because a row is displayed. Existing historical fields,
identity-bound rows and profile history remain unchanged. UI, performance and
source compilation checks pass **139 tests**; scoped `git diff --check` is
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V01 Results landing reader health):** Results
landing refreshes now project malformed retained shelf rows into explicit
`Unavailable` entries with a diagnostic copy of the raw value, rather than
crashing the page or silently dropping evidence. Valid result IDs, duplicate
suffix handling, selection restoration and read-only detail routing remain
unchanged; no result is re-simulated or rebuilt from current rosters. The UI
and profile/results coverage passes **138 tests**; `views.py` compiles and
scoped `git diff --check` is clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A7 company-profile story reader):** Company
profile Follow state now consumes `story_subscriptions_read_model` rather than
calling the save-repairing subscription initializer while the profile is
opened. The explicit Follow/Unfollow callback still normalizes at its mutation
boundary and resolves the saved subscription ID, so malformed subscription
rows remain unchanged and cannot redirect a later action. The UI/source reader
regression passes **111 tests**; `views.py` compiles and scoped
`git diff --check` is clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (A3 cash-runway malformed finance guard):** The
read-only runway now tolerates a non-mapping or malformed legacy `finance`
container. `player_monthly_office_cost` uses a bounded office baseline when the
stored value cannot be parsed, while the forecast continues to derive staff,
Academy and rights values from defensive local data. The raw finance envelope,
cash, schedule and RNG remain unchanged; unavailable rights are shown as zero
conditional receipts rather than raising an exception. `cash_runway_regression_test.py`
passes **11 tests**, and source compilation plus scoped `git diff --check` are
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V01 Upcoming Cards projection):** Upcoming
refreshes no longer repair saved scheduled-event names or reorder their fight
lists as a side effect of repainting. Each row receives a shallow display copy
with a local fight-list projection before generated-name formatting; the stable
`upcoming_event_rows` map still points to the original event for the existing
edit/cancel owners. The UI identity source checks and full smoke path remain
green; `views.py` and `ui_data_regression_test.py` compile cleanly and scoped
`git diff --check` reports no errors. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V03 booking forecast reader):** The Upcoming
Cards display now keeps generated-name formatting and local fight ordering on a
display copy, and its economics forecast calls
`selected_event_economics(repair=False)` with a bounded production baseline.
Explicit booking/apply actions retain the existing repair owner, while simply
opening or repainting the page cannot normalize a malformed finance envelope,
rewrite a saved event or redirect the stable edit/cancel map. The UI source
regressions and event-economics checks pass; `events.py`/`views.py` compile
cleanly and scoped `git diff --check` reports no errors. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V03 broadcaster-status reader):** The booking
page's broadcaster strip now projects a malformed saved `media_rights` value as
an unavailable empty mapping instead of crashing while rendering the selected
provider. This is presentation-only: it does not repair the contract, rerun a
quote, alter rights or change the stable event action map. The UI source checks,
event-economics regression and smoke path remain clean; `views.py` compiles and
scoped `git diff --check` reports no errors. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13 Regions profile reader health):** Regions
profiles now use a defensive copy of the selected retained row. Non-mapping
catalogues or rows render an explicit unavailable state; missing list fields
become empty display lists and malformed numeric indicators use bounded neutral
values. The Regions refresh does not repair the saved catalogue, change gym or
promotion state, or infer hidden facts. UI source checks and smoke remain green;
`views.py` and `ui_data_regression_test.py` compile cleanly and scoped
`git diff --check` reports no errors. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V07 Finance reader purity):** Finance refreshes
now use a defensive local finance projection instead of calling the
save-repairing defaults helper or writing derived payroll/offer fields. The
annual outlook derives the current-year line locally from retained weekly
history and the current boundary; opening or repainting Finance cannot seal or
overwrite annual history. Malformed containers and rows remain visible through
bounded values and explicit unavailable states. The UI-data suite now checks the
reader source boundary; `views.py` and its focused tests compile cleanly and
scoped `git diff --check` reports no errors. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V02 Game & Saves reader boundary):** Game &
Saves refreshes now enumerate the retained save/database library without
creating the active-universe marker, normalizing the default database, or
repairing autosave rules. The saved marker is read when present; otherwise the
packaged Default Universe is labelled as the active fallback without a write.
Path-bound save/database selection and all load, copy, delete, backup, folder
and database-selection handlers remain unchanged. Source regressions,
compilation and scoped `git diff --check` are clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V03 Matchmaking draft reader):** Matchmaking
refreshes now project the existing main-event/tier metadata onto shallow fight
copies, leaving the saved `booked` list and stable fight-to-row map untouched
until an explicit add, move, edit or remove action. Available-fighter refresh
also stops repairing the transient event-name field. Identity, title and
readiness calculations remain unchanged. UI source regressions,
`views.py` compilation and scoped `git diff --check` are clean; the smoke path
continues to pass with its documented headless coordinate probe skipped. Stage
4 of 6 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (V12 Regional Prospects reader):** Regional
Prospects refreshes now request the shared candidate assessment with
`repair=False`. The table consumes saved fighter history baselines and bounded
defaults without writing baseline fields, while simulation, load/migration and
roster-transition owners retain the established repair path. Filtering and
navigation therefore remain RNG/state neutral and continue to use the current
promotion row for every rating. UI source checks, compilation and scoped
`git diff --check` are clean; Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (V14 Rankings scouting visibility):** Ranking
rows now keep public company/world position, movement, record and
scouting-safe OVR estimates visible while masking the derived divisional/P4P
score as `Hidden` for fighters whose private ratings are not visible. The
ranking order and eligibility owners remain unchanged; no tooltip or detail
fallback exposes the score. UI-data source checks, compilation and scoped
`git diff --check` are clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V15 Combat Sports reader boundary):** Combat
Sports overview and Records/History pages now project legacy circuit state on
defensive copies. Opening or refreshing them cannot assign sport weight
classes, crown champions, or rewrite ranking/record caches; explicit child
management, migration and simulation owners retain those repairs. The focused
Combat Sports regression covers no state drift, while the UI source, compile
and smoke checks remain clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13/V15 company standings reader):** Company
standings and selected Combat Sports company profiles now consume the same
non-repairing circuit projection. Changing a company row or refreshing the
standings table cannot migrate sport weights, titles, rankings or record caches;
the explicit management/simulation paths remain the write boundary. Source
regressions, compilation and focused Combat Sports tests remain clean. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V14 Rankings refresh boundary):** Rankings
refreshes now calculate visible ordering, scope labels and rank maps locally
without calling the mutable `refresh_promotion_rankings` owner. Stored
current/previous movement snapshots remain intact until calendar or simulation
processing records a new boundary, while private score masking and public rank
visibility remain unchanged. The UI source regression, focused suite and
compilation remain clean. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13 company strategy reader):** Company
profiles, selected-company data and the child-promotion manager now consume a
defensive promotion-strategy projection. Opening or repainting these readers
cannot seed a missing strategy or add compatibility defaults to a saved
promotion; explicit strategy/calendar gameplay owners remain unchanged. The
source regression, focused UI suite and compilation remain clean. Stage 4 of 6
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V04 detailed-skills reader boundary):** Fighter
stats text, detailed-skill popups, profile skill cards and the legacy skill-tree
reader now consume a copied deterministic projection. Opening or refreshing a
profile cannot invoke the RNG-backed `ensure_detailed_skills` repair owner or
write to the fighter. Empty legacy dictionaries remain readable through
bounded values derived from saved broad ratings; partial dictionaries preserve
stored values and derive only the three known compatibility fields for display.
Explicit load, editor, migration and simulation paths retain ownership of
persisted repairs. The profile regression covers no fighter/RNG drift, and the
profile cards/popup label the projection so it cannot be mistaken for
persisted detail. The focused compile/test checks remain clean. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V16 Academy rival-program reader):** The
Academy's rival-program table now calls the youth-program helper in
non-repairing mode. Missing AI youth-program data is projected on a defensive
copy for sorting and display, so opening or refreshing the Academy page cannot
seed a promotion strategy or persist default rival-academy fields. Calendar
progression and explicit rival-academy actions retain the repairing path. The
UI-data regression covers no strategy drift; focused compilation and tests
remain clean. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (V11 scouting selection readers):** Regional
Prospect selection details, Scouting Target Board summaries and comparison
uncertainty text now use the retained dossier with `migrate=False`. A row
selection or comparison therefore cannot invoke scouting migration, repair a
malformed/legacy report container or change RNG/state; explicit report
assignment and sanctioned load/migration remain the write boundaries. The
UI-data regression now guards all three readers, and the focused UI/profile/
combat-sports suites plus stability playtest remain clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 Fighter Search identity):** Fighter Search
 rows now use saved fighter/company identity keys, deterministic fingerprints
 for ID-less legacy rows and duplicate suffixes instead of visible global
 indexes. Filter and pagination refreshes restore a selected fighter only when
 the same source identity remains visible; profile and comparison actions keep
 using the refreshed identity map. The UI/performance regressions cover stable
 IDs, company-scope separation, legacy fallback and full 100-row page access.
 Focused compilation and tests remain clean. Stage 4 of 6 remains active with
 **4 major stages remaining** and **12 named card areas** unfinished or
 policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G3 Media campaign history identity):** Media
 campaign-history rows now prefer saved campaign/operation/evidence IDs and use
 content-bound fingerprints with deterministic duplicate suffixes for legacy
 rows. Refreshes retain a selected campaign by source identity rather than its
 visible position, and the desk exposes a read-only detail strip containing the
 retained outcome, heat and cost. Malformed rows remain visible as explicit
 unavailable evidence; no campaign is rerun, regenerated or rewritten while
 the page is repainted. The UI-data suite covers stable/changed identities and
 the new source-bound detail path. Stage 4 of 6 remains active with **4 major
 stages remaining** and **12 named card areas** unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 Awards/Records identity):** The Records
 leaderboard now retains each source fighter behind its row, uses stable
 `fighter_id` keys (or deterministic fingerprints for ID-less legacy records),
 restores selection after category or sport refreshes and opens profiles through
 the source row map. Duplicate names can no longer redirect a profile open to a
 different athlete after sorting. The UI-data regression covers saved and
 legacy row keys plus the source-bound open path. Stage 4 of 6 remains active
 with **4 major stages remaining** and **12 named card areas** unfinished or
 policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V12 Regional Prospects row identity):**
Regional Prospects rows now bind promotion and fighter identity in a stable
source key, add deterministic suffixes for duplicate legacy pairs and restore
the selected prospect only when the same source remains visible. Sorting and
filtering therefore cannot redirect a later profile/scouting action to another
regional company; the existing non-repairing assessment and per-row promotion
rating rules remain unchanged. The UI-data regression covers cross-promotion
separation and refresh markers. Stage 4 of 6 remains active with **4 major
 stages remaining** and **12 named card areas** unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G3 Media Desk fighter identity):** Media Desk
 spokesperson and same-division target selectors now retain source-bound maps
 behind their readable labels, add deterministic suffixes for duplicate names,
 and preserve the selected fighter across dashboard refreshes. Campaign and
 callout handlers resolve through those maps before attempting a unique-name
 compatibility fallback, so a duplicate-name row fails closed rather than
 targeting the wrong athlete. The change is presentation/identity-only and
 does not alter media costs, rolls or campaign outcomes. The UI-data regression
 covers selector map/source markers. Stage 4 of 6 remains active with **4 major
 stages remaining** and **12 named card areas** unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V11 Achievements identity):** Fighter
Achievements & Milestones entries now retain `fighter_id` at unlock time and
deduplicate by immutable identity, so two active careers with the same display
name can earn the same milestone independently. The profile action resolves
through `resolve_award_fighter`: valid IDs open the saved career, while id-less
legacy names open only when unique and otherwise fail closed. Existing fields
remain intact, the permanent ledger stays append-only, and repainting the
window cannot mutate or reassign historical achievements. The UI-data
regression covers independent same-name unlocks and the identity-aware reader;
compile and focused tests remain clean. Stage 4 of 6 remains active with **4
major stages remaining** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V09 Staff legacy-row identity):** Staff
roster, candidate and expiring-contract readers now key populated ID-less
records by a deterministic fingerprint of retained name/role/specialty and
contract fields rather than the current sorted position. Duplicate rows still
receive deterministic suffixes; a completely empty or malformed row remains
visible under an explicitly non-durable fallback. Saved `staff_id` actions,
selection preservation and the employment/brief mutation boundaries are
unchanged. The focused UI, Staff management and employment regressions cover
identity stability through resort and malformed-row handling; compilation is
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V04/V11 roster and market selection):** Player
Roster and Free Agents refreshes now capture the selected source fighter before
rebuilding their filtered tables, restore that same identity when it remains
visible and refresh the associated detail/scouting panel. A filtered-out or
departed career is not replaced by the first visible row. These are
presentation-only projections: no fighter creation, scouting migration, cash,
RNG or contract mutation occurs during refresh. UI-data source regressions and
focused compilation remain clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V05 Fight History opponent snapshot match):**
Fight History now requires an opponent name or ID match before using a saved
`bout_rating_history` snapshot when no archived replay is available. A
name-less legacy row on a date with multiple bouts therefore cannot inherit the
first snapshot by iteration order; it remains explicitly unavailable while
valid identity-linked snapshots still provide the at-the-time record and rank
fields. This preserves all retained history and changes only the defensive
reader. The fighter-profile regression covers the ambiguous same-date case;
focused compilation and tests remain clean. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13 Legacy Ledger company identity):** The
all-time Legacy Ledger now keys company-era rows through promotion IDs or the
shared deterministic name/region identity helper, adding duplicate suffixes
without changing saved promotion data. Two companies with the same display
name remain independently selectable and their era detail cannot be redirected
by Treeview collisions. The UI-data regression covers stable and duplicate
promotion identities; this is a reader-only change with focused compilation
clean. Stage 4 of 6 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 integrity follow-up (V16 Academy rival-program identity):** The
Academy rival-program reader now keys each visible company through the shared
promotion identity helper and deterministic duplicate suffixes. Duplicate
company names therefore remain separate rows instead of colliding in Tk's
Treeview; the projection remains read-only and does not repair youth programs,
change bids or consume RNG. The UI-data regression covers stable and duplicate
promotion keys, with focused compilation and tests clean. Stage 4 of 6 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V15 Combat Sports history athlete identity):**
Records/History ranking rows now retain the source athlete behind each division
row. Saved `title_ids`/fighter IDs are preferred; a display-name fallback is
accepted only when exactly one athlete in the selected circuit matches, so
duplicate same-name careers fail closed instead of opening the first roster
match. The change is a read-only routing repair: circuit state, rankings,
titles, records and profile data remain untouched during refresh or profile
open. `ui_data_regression_test.py` and `combat_sports_regression_test.py` pass
with clean compilation. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (S2 autonomy selector reader boundary):** The
Staff autonomy selector now reads the retained company/department policy
directly while repainting. A malformed legacy envelope no longer gets filled or
rewritten merely because the selected scope changed or the page refreshed;
explicit policy edits remain the sole normalization boundary. The selector still
shows the department override when one exists and falls back to the company mode
otherwise. `staff_management_regression_test.py` and `ui_data_regression_test.py`
pass with clean compilation. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (V15 Combat Sports history malformed-row
projection):** Records/History now defensively projects malformed retained
title-history, finance and event rows into explicit unavailable text while
keeping valid entries and all raw source data intact. Dates and amounts use
bounded display values, malformed containers become honest empty states, and
the reader remains free of migration, settlement and RNG work. The existing
saved-identity athlete routing remains in force. `ui_data_regression_test.py`
and `combat_sports_regression_test.py` pass with clean compilation. Stage 4 of
6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13 company standings entity identity):**
Industry standings now attach a stable promotion ID or sport-scoped
circuit/player identity to every visible company row. The profile, power trend,
breakdown and selected-company data readers resolve through that source row;
duplicate same-name entities remain separate after sorting/filtering, while
name-only legacy restoration succeeds only when the visible match is unique.
Legacy standings history is carried forward into the identity-scoped key during
the explicit snapshot owner without changing existing history fields. The
focused UI-data and Combat Sports suites pass with clean compilation. Stage 4
of 6 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G3 Media capacity reader):** The weekly
capacity display now uses the non-repairing media-finance projection. A stale
marker is reported without rolling it, and a malformed/non-mapping legacy
envelope remains untouched rather than being replaced with seeded defaults.
The Media Plan regression covers both stale-marker and malformed-envelope
reads; source compilation is clean. Stage 4 of 6 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (Rules Help malformed-rules guard):** Help
construction now treats a non-mapping saved rules envelope as unavailable for
the optional UI search preference. Filtering still searches only the authored
catalogue, while a valid mapping persists the search text as the separately
allowed UI preference. Opening Help cannot seed gameplay defaults or crash on a
legacy rules value; the Rules Help regression covers the guarded write path.
Stage 4 of 6 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (V13 archived company-card identity):** New AI
and independent replay packages retain a stable promotion reference. Company
standings card view/watch actions now resolve through the selected source row,
so duplicate same-name promotions cannot open another company's archive.
Legacy name-only packages remain available for a unique visible company and
fail closed when the standings name is ambiguous; no replay, settlement or
simulation state is changed by the reader. The UI-data regression covers exact
identity matching and the ambiguous legacy state, with focused compilation and
tests clean. Stage 4 of 6 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (Finance milestone projection boundary):** The
Finance History & Outlook milestone cards now consume a defensive projection
of retained weekly history. Non-mapping envelopes, malformed rows and invalid
numeric values produce bounded trend/ETA values rather than a crash or an
implicit repair. The projection remains read-only; calendar/month-end owners
retain all milestone and history writes. The UI-data and player-finance
regressions pass with clean compilation. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (Rankings company-entity identity):** Company
Rankings now constructs each row from its own promotion object and stable
promotion identity. Duplicate display names therefore retain independent
roster, cash and power calculations instead of resolving the first matching
promotion by name. The ranking row key includes that identity, preserving
selection through refresh without changing stored standings or gameplay. The
UI-data regression and focused compilation pass; no EXE or user save was
rebuilt or modified. Stage 4 of 6 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated.

**Stage 4 integrity follow-up (Rankings scope identity):** Promotion scope
choices now keep a source-bound promotion map and add a readable region/ID
suffix only when names collide. Worldwide and scoped reads therefore select
the intended roster, while company and P4P/divisional rank maps key each entry
by the promotion identity behind its display name. The detail pane treats
promotion rows as promotion rows instead of attempting a name-based fighter
fallback. UI-data, Combat Sports and focused profile checks remain clean; no
EXE or user save was rebuilt or modified. Stage 4 of 6 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated.
Scope selection is restored by source identity when a promotion's display label
changes after a refresh.

The legacy fallback is roster-bound as well as name/region-bound. Two old
promotions that share both display fields therefore receive independent
fingerprints and cannot merge their company rank groups or scope selections.

**Stage 4 integrity follow-up (Profile live injury-risk display):** The
legacy roster detail now reports the trait-adjusted `effective_injury_tendency`
and labels the retained `injury_proneness` baseline beside it. This keeps the
older roster reader consistent with the upgraded profile's current-risk card
without rewriting historical baselines or changing injury mechanics. The
profile/UI-data regressions and compilation remain clean; no EXE or user save
was rebuilt or modified.

**Stage 4 workflow follow-up (P1.4 routine media/context feedback):** The Media
Desk now retains campaign strategy, campaign execution, plan validation,
retarget/cancel, rights offer, counter, market-review, renewal and contract
lifecycle outcomes in dedicated status lines beside the relevant controls.
Routine results therefore survive a dashboard refresh without interrupting the
player with transient informational dialogs; paid reviews, deal replacement,
ending a contract and other irreversible actions still require their existing
explicit confirmations. Transfer preflight blockers, Combat Sports release
outcomes, company archive gaps, career-plan validation and Staff selection,
assignment, commentator and release guidance now use their owning page or
managed reader status when available. Staff profiles are scrollable managed
readers that retain role, specialty, progression, tenure-story and scouting
evidence. These changes are presentation-only and preserve stable IDs, finance
owners, RNG boundaries and save shapes. Focused UI, Media, foundation,
booking-workbench and Combat Sports regressions pass; no EXE or user save was
rebuilt or modified. Stage 4 of 6 remains active with the remaining G2/G3
closeout, G4 Staff/AI qualification and G5 policy-gated mechanics still to
complete.

**Stage 4 workflow follow-up (P1.4 receipt/archive feedback):** Secondary
readers now keep routine guidance in context as well. Settlement-receipt
selection and unavailable-record outcomes are written beside the immutable Media
receipt list; Staff work-receipt selection/read gaps stay in the Staff evidence
strip; an event without a retained tournament bracket reports through the
Results status surface; and the Fight Night archive keeps the no-replay state in
its archive detail line. If a committed event settles but its presentation
refresh fails, the saved-result warning is routed to Results when available.
Compatibility dialogs remain only for headless or legacy callers. These changes
do not rerun settlement, normalise retained evidence, consume RNG or alter
saved identities. Focused Media/UI, Combat Sports and Fight Night archive
regressions pass with compilation and diff checks clean; Stage 4 remains active
with the same G2/G3, G4 and G5 delivery gates still requiring their full
acceptance contracts.

**Stage 4 workflow follow-up (P1.4 milestone-project feedback):** Company
Milestones & Super Events now keeps unselected-opportunity guidance, approval
blockers and completed planning-cancellation outcomes in a dedicated status
line inside the managed project window. Paid/sunk commitment facts, approval
and cancellation owners, and the explicit destructive cancellation confirmation
remain unchanged. This is a presentation-only continuation of the decision-
center pass: it does not approve a project, spend cash, alter terms, rerun
readiness, or consume RNG while the reader is open. Super-event closeout,
economics and UI regressions pass; the Stage 4 gates remain active until their
full acceptance contracts are complete.

**Stage 4 workflow follow-up (P1.4 Simulation Lab feedback):** Simulation Lab
now keeps routine guidance in its result/report areas. Missing fighters, stale
database selections, mixed-gender/rules blockers, invalid tournament fields,
unavailable sandbox brackets or tournament nights, and missing play-audit
results are visible beside the tool that needs attention. The openweight
simulator prompt remains an explicit choice. This is presentation-only and
preserves sandbox isolation, career data, finance, RNG and saved identities.
Simulation, audit, tournament-history and UI regressions pass; Stage 4 remains
active until the remaining gate contracts and policy decisions are complete.

Play-audit export completion is also retained in the managed audit reader. The
exported file is a copy of the saved evidence, while the active career and its
simulation state remain untouched.

The Testing Providers & Policy reader also keeps invalid provider or policy
selection feedback in its summary line. The provider catalogue remains a
planning-only contract: changing it cannot commission samples or enable
confirmation, appeal or sanction mechanics before J5's approved policy table.

**Stage 4 workflow follow-up (P1.4 Game & Saves context feedback):** Routine
persistence outcomes now remain beside the Game & Saves controls when that
surface is available. Quick-save, active-universe selection and cloning,
default-pack validation, backup/restore, database export/import/load,
career-start conversion completion, and missing-selection guidance use the
shared save-manager status line rather than interrupting the player with a
transient informational dialog. High-impact choices (overwrite, delete,
restore confirmation, migration acceptance and conversion acceptance) and
write/validation failures retain their explicit modal or error/recovery path.
A compatibility fallback keeps legacy/headless callers safe when no status
widget exists; no save path, atomic writer, recovery policy, active-career
switch, database payload or RNG boundary changes.

The universe section editor follows the same local-feedback rule: successful
section saves and validation results are retained in an editor status line,
while malformed JSON and failed writes remain actionable errors.

**Stage 4 verification update after the Game & Saves slice:** The focused
UI-data and persistence bundle passes **157 tests**, the smoke playtest passes
with the documented headless Matchmaking-coordinate probe skipped, and the
changed persistence/test modules compile cleanly. The maintained runner was
rerun: all suites through the available fight-engine groups pass until the
existing historical `fight_move_selection_parity_regression_test.py` fixture
assertion (`Selection parity changed: bouts`). This save-surface presentation
change introduces no additional failure and does not justify weakening or
refreshing that source-bound historical fixture. Stage 4 of 6 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 workflow follow-up (P1.4 Database Editor context feedback):** The
standalone Database Editor now keeps routine selection guidance, stale-record
warnings, required-field feedback and empty bulk-edit guidance in its header
status line. Successful validation and preflight checks are summarised there,
while detailed finding lists remain available in their diagnostic dialogs.
Explicit save/delete confirmations, malformed-input errors, source identity
maps and the read-only preflight boundary are unchanged. The UI-data,
Database Editor identity and universe-validation bundle passes **177 tests**
with clean compilation, and the smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 workflow follow-up (P1.4 World Editor context feedback):** The
Current Career Editor now keeps routine missing-name, invalid-employer,
duplicate-identity and missing-selection guidance in the editor header when the
page is available. Fighter saves, retirements and detailed-rating saves identify
the affected fighter and the pending career-save state beside the controls.
Headless/legacy callers retain the native dialog fallback; retire confirmation,
malformed-value handling and the existing title-vacancy/membership mutation
boundaries remain unchanged. The focused UI-data suite passes **159 tests**,
source compilation is clean, and the smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with **4
major stages remaining** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V13 Gym Viewer reader boundary):** Opening a
gym profile now reads the existing synchronized membership projection without
calling `sync_gym_membership`; counts and first-week capacity can only change
through calendar advancement or explicit roster/mutation owners. The UI-data
regression suite now guards both World Hub refresh and Gym Viewer opening
against reader-time rewrites. The focused suite passes **159 tests**, source
compilation is clean, and the smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 workflow follow-up (P1.4 company/spectator context feedback):**
Company selection, takeover and return-to-spectator preconditions now use the
company reader's persistent next-step notice whenever that surface is present.
The player can see why a company cannot be selected, why a child or feeder is
not controllable, or that spectator mode is already active without losing the
context of the selected row. Legacy/headless callers retain a native-dialog
fallback; takeover confirmation and all roster/finance/title transition
boundaries remain unchanged. The focused UI-data suite passes **160 tests**,
source compilation is clean, and the smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (V14 Company Editor reader projection):** The
Company Editor now projects belt, interim-title, special-belt, rule and
broadcast-contract envelopes onto local defensive copies while repainting.
Opening or refreshing the editor therefore cannot normalise malformed legacy
data, seed missing rule/contract defaults or rewrite the saved title state.
Explicit division, special-belt, rule and broadcast actions retain their normal
mutation boundaries. Malformed special-belt values render as bounded empty
history/zero-defence evidence instead of crashing. The focused UI-data suite
passes **161 tests**, source compilation is clean, and the smoke playtest passes
with the documented headless Matchmaking-coordinate probe skipped. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 verification update (stability playtest after the reader-boundary
slices):** The seeded long-run stability playtest completed successfully for
seeds 2201, 2202 and 2203, reaching Month 4 without an unhandled simulation
failure. The runs recorded 169, 182 and 175 events respectively; one seed
also exercised two normal fighter retirements. This confirms the recent
Game & Saves, Database Editor, World Editor, Gym Viewer and Company Editor
presentation changes do not destabilise calendar progression or retirement
handling. The combined focused UI-data, persistence, Combat Sports and
title-decision bundle passes **191 tests**; profile/fight-night regressions
and the application-performance regressions also pass. Stage 4 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (V02 Game Settings reader projection):** Game
Settings now builds a defensive local projection for rule, commentary and
Fight Night audio values. Opening or cancelling the editor cannot seed missing
defaults or rewrite malformed retained settings; the explicit Apply action
continues to normalise and persist the chosen values. The UI-data suite now
passes **162 tests**, the combined focused bundle passes **192 tests**, source
compilation is clean and the smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 workflow follow-up (P1.4 dialog inventory closeout):** Added an
explicit source-level inventory regression for direct native information dialogs.
Every retained `showinfo` call is now accounted for by its owning page/status
surface (Game & Saves, Database Editor, Contracts/Market, Results, World Hub,
Media, Roster, Staff or the managed reader) and must include a compatibility
guard before the fallback is reached. The only native three-way fight-day
choice is likewise asserted to be the headless/legacy fallback; the desktop
path remains the themed Watch Live / Simulate Now / Stay on This Week panel.
This closes the routine-popup audit without weakening intentional validation,
destructive confirmation, final-approval or error dialogs. The UI-data suite
passes **165 tests** and the combined focused bundle passes **195 tests**;
compilation and the existing smoke/stability evidence remain clean. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

The inventory also covers the shared warning/info compatibility helpers. Their
dynamic messagebox selection is asserted to remain inside the named status
notice helpers, so a new routine fallback must declare its owning surface before
it can be merged.

**Stage 4 integrity follow-up (J11 simulation source guard):** Newly armed
spectator stop policies now retain the current game revision alongside their
target and archive cursor. A saved policy with an explicit revision mismatch
fails closed before fast-forward or Resume can start; the player can still load
the career normally, clear the stale policy, or arm a new one. Legacy policies
without the field remain compatible, and evaluation remains week-boundary,
read-only and RNG-free. The simulation-pause regression now covers revision
capture, legacy compatibility, mismatch blocking and no policy rewrite; the
suite passes **9 tests**, and the full smoke playtest passes with the documented
headless Matchmaking-coordinate probe skipped. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (J11 direct scheduling guard):** The source-revision
check now also lives at `begin_advance_sequence`, the common cooperative
scheduler boundary. This closes the bypass where a legacy caller could invoke
the scheduler directly after the public spectator entry points had rejected an
incompatible saved policy. An enabled policy carrying a different game revision
now stops before due-card checks, job creation, callbacks, or Tk scheduling;
legacy policies without a revision remain compatible and the stale envelope is
left untouched. The regression suite passes **10 tests** and the related
simulation/persistence/checkpoint/performance bundle passes **24 tests**. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J11 policy projection preservation):** The
rule-default load projection now retains the additive `source_revision` field
when normalising a saved spectator policy. Previously, a load/default pass
could filter that field out, silently turning a stale policy into a legacy
policy and defeating the scheduler guard. New revisions remain exact, missing
revisions are represented as an empty legacy-compatible value, and explicit
policy actions still own writes. The simulation-pause suite passes **12 tests**
and the related simulation/persistence/checkpoint/performance bundle passes
**26 tests**. Stage 4 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (J11 policy status reader):** The persistent
simulation desk now treats an enabled policy with an explicit revision mismatch
as stale and explains the required player action without rewriting the save.
Malformed target values are projected as `Date target unavailable` rather than
being passed to calendar formatting and crashing the reader. Valid targets keep
their existing display, and legacy policies remain compatible. The
simulation-pause suite passes **14 tests**; compilation and diff checks are
clean. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (J4/G4 automatic AI membership transition):** The
central AI free-agent signing owner now records an ID-linked `join` fact before
removing the fighter from the free-agent pool and appending them to the
promotion roster. The transition key is stable across retries and the existing
contract/finance/story operations remain unchanged. This closes the missing
Company Timeline entry for ordinary AI market signings while preserving the
append-only, RNG-neutral history reader. `foundation_regression_test.py` passes
**33 tests**, including an order-sensitive assertion that the membership fact
exists at the roster mutation boundary. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 signing-boundary completion):** The same
pre-mutation membership boundary now covers player free-agent signings,
automatic TBA fills, last-minute replacement picks and direct contract
negotiations. Regional feeder signings record both the feeder `leave` and player
company `join` before the source roster is changed; swap commits remain the
single owner for both sides of a negotiated transfer. The narrative
`record_contract_signing` hook accepts a membership-free mode so these paths do
not duplicate their append-only facts after the roster move. Existing purse,
contract, finance, replacement and negotiation mechanics are unchanged.
`foundation_regression_test.py` and `ui_data_regression_test.py` pass **198
tests** together; source compilation and diff checks are clean. Stage 4 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 booked-fight restoration):** The explicit
 load-boundary repair that restores a fighter for an already scheduled bout now
 records an ID-linked player-company `join` or `return` fact before moving the
 fighter out of the free-agent/retired collection. The source transaction is
 stable for retry-safe loads, the raw booking evidence remains unchanged, and
 unresolved or ambiguous references still fail closed. The foundation source
 regression now checks this ordering alongside the signing routes; the focused
foundation suite passes **33 tests**. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 Combat Sports release boundary):**
Player-owned Combat Sports releases now write the child-company `leave` and
flagship-circuit `join` facts before changing the saved division roster IDs or
booked-bout projection. Title vacating still precedes the transition, while
the release remains a read-only return to the flagship circuit with no change
to contract, ranking or RNG rules. Combat Sports regression coverage now
observes both membership calls while the athlete is still present in the
division; the focused suite passes **21 tests**, with clean compilation and
diff checks. Stage 4 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (S3 progression malformed-baseline guard):**
The quarterly Staff progression worker now validates a saved skill baseline
before marking a qualifying quarter as consumed. A malformed legacy skill no
longer raises during the worker or permanently loses an earned progression
credit; the evidence remains available for the next explicit repair/quarter
close. Valid capped and +1 outcomes keep their existing annual ceiling,
80-point limit, credited work IDs and idempotent quarter key. The Staff
regression suite passes **51 tests**, with clean compilation and diff checks.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (S4 AI staff identity/term boundary):** The
prospective AI staff hire now normalises the retained salary and contract term
at the explicit hire boundary, records the current start/expiry months, and
disambiguates a duplicate saved `staff_id` with a deterministic suffix before
the employee enters an AI roster. Legacy candidates with missing IDs receive
a fingerprint over their retained fields; affordability, one-role-per-month,
and six-month runway checks remain unchanged. The employment regression suite
passes **21 tests**, with clean compilation and diff checks. Stage 4 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 comeback membership boundary):** Retired
fighters returning through a player-approved comeback contract now emit an
ID-linked `return` fact before leaving the retired collection or re-entering
the active roster. The stable `comeback-signing` transaction key keeps a
retry-safe timeline without changing contract terms, retirement flags, purse,
cash or RNG behaviour. A source regression now guards the ordering alongside
the existing signing and restoration routes; the focused Foundation suite
passes **34 tests**, with clean compilation and diff checks. Stage 4 remains
active with **4 major stages remaining** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 intake source gates):** The membership
 ordering regression now covers every patched intake owner (AI opening/depth and
 emergency signings, academy and rival-academy graduation, regional wonderkid,
 proving-ground and youth intake, plus regional departures). The source checks
 ensure each destination fact is emitted before the corresponding roster or
 free-agent mutation, and remain compatible with the 34-test foundation suite.
 No new gameplay or RNG behaviour is introduced. Stage 4 remains active with
 **4 major stages remaining** and **12 named card areas** unfinished or
 policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 intake-boundary completion):** AI opening
 rosters, opening-depth contracts, rival-academy graduates, academy MMA and
 feeder graduates, AI emergency signings, regional wonderkid/proving-ground
 intake and regional youth intake now record their destination-company fact
 before appending a fighter to that roster (and before removing a free agent
 where applicable). The shared contract-signing narrative hook is called in
 membership-free mode after the move, preventing duplicate history rows while
 preserving all existing intake selection, contract, finance, development and
 RNG behaviour. This completes the routine market/intake membership audit for
 the current Stage 4 slice. Source compilation is clean and the focused
 foundation suite passes **33 tests**. Stage 4 remains active with **4 major
 stages remaining** and **12 named card areas** unfinished or policy-gated. No
 EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A3 cash-runway malformed finance guard):** The
read-only cash-runway forecast now bounds malformed numeric values inside an
otherwise present finance envelope (production, medical, drug-testing,
sponsorship, rights, merchandise/tax rates, academy costs and tier/capacity
inputs) instead of raising or repairing the save. Forecast rows remain
settlement-aligned, and the raw finance, schedule, cash and RNG state are
unchanged. Regressions cover malformed scalar and nested finance values plus
revenue-mix history; the cash-runway suite passes **15 tests**, with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12
named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (J4/G4 AI-upgrade rollback boundary):** If an
AI upgrade signing cannot complete after the incumbent has been moved to the
free-agent shelf, the rollback now records an ID-linked `return` fact before
restoring that incumbent to the promotion roster. This keeps the append-only
Company Timeline truthful for the transient leave/return while preserving the
existing affordability, selection, finance and RNG behaviour. The Foundation
suite passes **35 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A1 owned-calendar date projection):** The
read-only owned-company calendar now bounds malformed current and event
month/week values, reports explicit partial coverage for invalid saved dates,
and keeps source schedules unchanged. Stable event/owner identity, status and
participant projections remain intact; no scheduling, reservation, finance or
RNG owner is called by the reader. The owned-calendar suite passes **4 tests**,
with clean compilation and diff checks. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (S4/J6 non-finite staff reader guard):** Staff
skill, contract-term, contract-target, offer-score and warning projections now
fail closed for non-finite numeric legacy values such as `Infinity` and `NaN`,
matching the existing malformed-string behaviour. The raw staff row remains
unchanged, expired/uncertain terms do not grant access, and explicit contract
mutation paths retain their existing validation boundary. The focused staff
employment suite passes **22 tests**, with clean compilation and diff checks.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G4 Staff lead projection):** The morale-adjusted
lead selector and approved specialty-saving readers now treat non-finite or
malformed skill, morale and subtotal values as unavailable bounded defaults.
Malformed staff rows cannot win a lead comparison through `Infinity`/`NaN`, and
read-only cost notes return zero rather than raising or mutating the retained
row. Explicit staff policy and contract actions keep their existing write
boundaries. The Staff management suite passes **52 tests**, with clean
compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (G4 Staff capability/evidence audit):** The
capability matrix, employment evidence audit and progression snapshot now
handle non-finite salary, contract, morale and work values as explicit invalid
evidence instead of raising or normalising the save. Lead/action readiness
remains bounded and all findings retain the stable staff source ID. The Staff
management suite passes **53 tests**, with clean compilation and diff checks.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G3 Media Rights non-finite reader guard):**
Rights contract eligibility, renewal status, terminal-history, terms and
event-outcome quote readers now fail closed for non-finite and malformed saved
numbers. They return bounded zero/Needs review evidence, preserve fee-alias
truth and leave the retained contract untouched; event quote fallback also
keeps rating output numeric without drawing an extra RNG value. The Media Plan
suite passes **53 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G3 Sponsor preview non-finite guard):** Sponsor
activation previews, offer assessments and settlement-fee readers now treat
non-finite trust, stability, fee, fit, term and conduct values as unavailable
bounded evidence. They keep the contracted maximum separate from the current
full/half-fee estimate, do not refresh offers or mutate finance while previewing,
and preserve the raw offer/deal for explicit review. The Media Plan suite passes
**54 tests**, with clean compilation and diff checks. Stage 4 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G5 Testing Desk quote guard):** The authored
provider/policy comparison quote now bounds non-finite base cost and sample
count inputs, validates the authored cost multiplier and remains explicitly
planning-only. A malformed quote cannot raise, spend cash, draw RNG or alter
the live compatibility screening policy; provider effectiveness and sanctions
remain gated as designed. The Testing Desk catalogue suite passes **15 tests**,
with clean compilation and diff checks. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A3 Regional Feasibility reader guard):** The
regional feasibility review now projects malformed retained invitations and
snapshots defensively. Non-mapping snapshots/invitations show the safe empty
state, invalid dates and numeric counts use bounded display values, malformed
scheduled rows are ignored rather than crashing the window, and venue lists
remain text-only. The reader still calls only the non-repairing feasibility
projection; opening, refreshing or reviewing the panel cannot book, generate an
offer, reserve a fighter, spend cash or consume RNG. Regional feasibility and UI
data suites pass **169 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J8 Combat Sports history reader guard):** The
read-only Circuit Records & History window now treats malformed world/division
containers and non-finite title/finance date values as unavailable evidence.
Invalid rows remain visible as explicit unavailable entries where possible;
safe amounts and bounded dates prevent `Infinity`, `NaN` or wrong-type legacy
values from crashing the reader. The circuit projection remains
`repair=False`, so opening the window cannot migrate crowns, rankings, finance,
events or RNG state. The UI data suite passes **167 tests**, with clean
compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (J9 Regions profile reader guard):** The Regions
profile projection now bounds non-finite drug-accuracy and local-pulse values,
handles malformed feasibility pairings and filters malformed scheduled-event
rows without changing the retained region catalogue. Unavailable region data
continues to render explicitly, while the profile and next-step readers remain
read-only and do not repair regions, generate invitations, book events, spend
cash or consume RNG. The UI data suite passes **168 tests**, with clean
compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (V14/J8 company standings projection):** The
company-power and combined standings read models now use bounded numeric
projections for malformed or non-finite reputation, stability, cash, champion,
rating and popularity values. Bad roster containers or fighter values cannot
crash the Rankings/Combat Sports company browser or win a comparison through
`Infinity`/`NaN`; valid values and ranking order remain unchanged. This is still
a presentation reader and does not refresh saved rankings, repair circuit
state, mutate rosters or consume RNG. The UI data suite passes **169 tests**,
with clean compilation and diff checks. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

The same projection now rejects non-mapping combat-sport world and player
division envelopes before reading promotion, roster, title or cash fields. A
malformed circuit therefore appears as an empty/limited standings source rather
than redirecting to another sport or invoking a repair path; the focused
Combat Sports regression remains green at **21 tests**.

**Stage 4 integrity follow-up (A4 owner-goal projection guard):** Owner
objective readers now use one bounded, non-mutating integer projection for cash,
popularity, show counts, targets, deadlines, baselines and maintenance periods.
`Infinity`, `NaN`, wrong-type and malformed retained values render as explicit
safe evidence instead of crashing Inbox/Goals or being written back. The
calendar worker remains the only boundary allowed to record observations,
baselines or terminal outcomes. Owner-goal/UI-data focused checks pass, with
the UI data suite at **170 tests**, plus clean compilation and diff checks. Stage
4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (G5 Drug Testing Cases reader guard):** The
retained compliance-case list, summary and workflow rows now treat non-finite
sample counts and quote totals as unavailable zero evidence instead of raising
or normalising a saved case. Durable case IDs, provider/policy snapshots and
workflow labels remain intact, malformed rows stay reviewable through the
explicit reader-status state, and opening/filtering the ledger never commissions
testing, charges cash, applies sanctions or consumes RNG. The UI-data suite now
passes **171 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J9 Regional Prospects baseline guard):** The
non-repairing regional-candidate assessment now treats non-finite or wrong-type
saved history baselines as zero for display-only eligibility calculations. It
does not write the baseline back, rerun migration, consume RNG or change the
feeder roster; valid historical baselines continue to drive the same
promotion/fighter assessment and stable row identity. The UI-data/regional
prospect regression covers `Infinity`, `NaN` and wrong-type baselines; the full
UI-data suite passes **171 tests**, with clean compilation and diff checks. Stage
4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (U03 Inbox reader guard):** Inbox display copies
and action classification now fail closed on non-finite or malformed message
dates and fighter contract terms. `Infinity`, `NaN` and wrong-type legacy
values are projected to bounded display defaults without normalising the saved
message shelf; source identity, sorting, unread/action labels and explicit mail
mutation handlers remain intact. The UI-data inbox/read-model checks pass, with
clean compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 integrity follow-up (U07 Event Log reader guard):** The sidebar Event
Log now distinguishes a malformed retained collection from a genuinely empty
archive. A non-list value produces an explicit load/migration review line and a
zero recorded-line count; valid lines remain complete, ordered and untouched,
with semantic styling and scroll restoration preserved. Rendering remains
observational and cannot run fights, settlement, calendar work or simulation.
The full UI-data suite passes **171 tests**, with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G4 Staff capability action-ID parity):** The
Staff capability read model now exposes `safe_read_action_ids` separately from
friendly action labels. The Staff page's capability grid shows those stable IDs,
and the selected-department detail repeats them alongside the handler,
execution mode, target scope, cost/capacity limits, stop conditions and evidence
contract. Mutating actions such as `campaign_plan_commit` remain absent from
recommendation IDs, so the saved brief allow-list and calendar worker cannot be
misread as granting recommendation authority. The Staff management suite passes
**55 tests**, UI-data remains at **171 tests**, and compilation/diff checks are
clean. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (G4 Staff guardrail input boundary):** Staff
budget, action-ceiling and department-brief quote paths now fail closed for
`Infinity`, `NaN` and overflow-sized values. Invalid player-entered amounts
return a clear validation result or a zero read-only quote rather than raising,
spending, or rewriting the retained policy. The sanctioned mutation boundary
still owns valid policy changes; the Staff management suite passes **55 tests**
and compilation/diff checks remain clean. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J8 selected Combat Sports profile guard):** The
selected-company reader now rejects malformed combat-sport world or player
division envelopes before entering the non-repairing circuit projection and
returns an explicit unavailable profile. Valid profiles defensively project
roster, event-history, title, finance, cash, reputation and stability values;
the shared roster reader also fails closed for non-mapping worlds and malformed
roster containers. Opening or switching a company therefore cannot migrate
divisions, titles, rankings, finance or RNG. The UI-data suite passes **172
tests**, with clean compilation and diff checks. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (A3 Finance reader overflow guard):** Finance,
History & Outlook and Cash Runway display readers now catch overflow-sized
legacy numbers as well as malformed strings. Tax-rate presentation also rejects
non-finite values instead of attempting to format them. The readers continue to
project defensive copies, preserve raw finance/history envelopes and leave
calendar, cash, settlement, RNG and annual-history mutation to their explicit
owners. The UI-data suite passes **173 tests**, with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (U02 Game & Saves reader boundary):** The save
library refresh now enumerates existing paths without creating missing Save or
Database directories, and the default-universe display path no longer invokes a
creator. Selection summaries compare against a non-creating active-slot path,
while lightweight legacy hosts retain their compatibility hook. Explicit save,
copy, move, migration and database-selection actions keep their existing write
owners. Persistence regression passes, the Game & Saves UI-data check remains
green, and no active-universe marker, database normalisation, autosave repair,
career save or user data was changed by a refresh.

**Stage 4 integrity follow-up (J8 Combat Sports overview reader guard):** The
Combat Sports landing tab now projects malformed world/division containers as
safe empty or unavailable rows, filters invalid event/roster/title data in its
detail cards, and bounds circuit cash, reputation and event counts. Its
`repair=False` projection remains presentation-only; opening or refreshing the
overview cannot seed weights, crowns, rankings, finance, schedules or RNG. The
Combat Sports regression passes **21 tests**, the UI-data suite is now **174
tests**, and compilation/diff checks are clean. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (G4 Staff collection reader guard):** Staff roster,
candidate and expiry refreshes now project only list/tuple employment
collections. A malformed legacy `staff` or `staff_candidates` envelope is
treated as an explicit empty table for presentation, while the raw value stays
unchanged for audit or sanctioned repair. Effect summaries use the same
projection, so opening the Staff page cannot iterate `None`/mapping containers
or redirect an action through a visible row position. The Staff management
suite passes **56 tests** and the UI-data suite passes **175 tests** after the
malformed-collection regression; compilation and diff checks remain clean. Stage 4 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

The Staff evidence audit and summary revision reader also catch overflow-sized
ledger values, reporting invalid spend or a bounded revision instead of
raising. The retained work log and policy envelope remain byte-for-byte
unchanged, and explicit policy/worker mutation boundaries are unaffected.

The same Staff surface now bounds non-finite skill, salary and morale values in
the roster display itself. Invalid cells show `—` while the retained employee
row remains available to the evidence audit and explicit repair path.

**Stage 4 integrity follow-up (G5 durable testing-case lifecycle envelope):**
J5 case records now retain optional event identity and a defensive event
reference alongside the frozen fighter, provider, policy, sample and quote
evidence. New records also carry explicit empty confirmation, appeal,
provisional-restriction, sanction and final-resolution containers. A
preliminary positive therefore remains visibly gated rather than being
silently promoted to a violation, injury, title consequence or sanction. The
workflow reader projects these containers without repairing legacy rows; it
returns stable counts and statuses for future confirmation/appeal policy work,
while preserving the raw payload and existing `sanction_status` field.

This slice deliberately does not commission a provider selected in the
planning desk, introduce confirmation rolls, create appeals, apply sanctions,
or change AI/spectator behaviour. Those mechanics remain policy-gated until
their jurisdiction, timing, evidence, balance and retry rules are approved.
The focused drug-testing and catalogue regressions pass **21 tests**, with
clean compilation and diff checks. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (U13 Combat Sports contract reader boundary):**
Combat Sports contract refreshes now call the identity compatibility helper in
`repair=False` mode. Legacy name-only child-division membership is projected
onto a defensive roster-ID map for display, while malformed world/division
containers yield an empty reader rather than raising. Contract months and
purses are bounded for invalid/non-finite values, duplicate same-name athletes
remain separate by fighter ID, and the saved division is unchanged until an
explicit sign, release or calendar-expiry owner runs. The Combat Sports
regression passes **23 tests** and its UI identity check remains green;
compilation and diff checks remain clean. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J12 database-editor identity audit):** The
database-editor acceptance harness now selects the source fighter/company
record directly before reading or applying fields. Compatibility selection
indices remain populated for older callers, but sorting and filtering cannot
leave the audit pointed at a different row. The UI audit passes **64,410
fighter values, 136 company values, 54 fighter fields and 8 company fields**;
database validation and save-as coverage remain green. Stage 4 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J4 historical opponent-record evidence):**
Fight History now requires a stable archived opponent ID or an exact archived
opponent name before it can use a same-date `bout_rating_history` snapshot.
When a replay omits the at-the-time opponent record and no matching snapshot
exists, the reader shows `Not recorded` instead of `-` or today's mutable
record. Unidentified legacy rows still retain their explicit `-` state, and
valid ID-linked snapshots continue to win over current roster values. The
fighter-profile regression suite passes **28 tests**, with clean compilation
and diff checks. Stage 4 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 presentation follow-up (G5 Testing Cases evidence context):** The
Drug Testing Cases detail reader now surfaces the saved event scope (or an
explicit manual/no-event label) and its source reference next to the test
identity. The workflow section also summarises confirmation records, appeals,
provisional restriction and sanction status, so a player can distinguish a
preliminary alert from a future action without opening the raw JSON payload.
Malformed quote totals continue to use the bounded read-model value, keeping
detail inspection safe and non-mutating. The combined drug-testing and profile
regressions pass **49 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (J3 contract-batch quote projection):** Renewal
workbench quotes now fail closed on malformed retained purse, popularity,
momentum, age, term or cash values. Non-finite and overflow-sized facts become
bounded planning evidence, while valid quote formulas, identity
deduplication, row order and partial-commit semantics remain unchanged. Quote
generation remains RNG-free and does not negotiate, spend or rewrite a saved
contract. The focused contract-batch regression passes **4 tests**, with clean
compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 presentation follow-up (J7 company-proposal cash evidence):** The
Company Proposal Ledger now projects malformed or non-finite retained cash
terms as bounded zero evidence in both its table and detail reader. Proposal
IDs, parties, fighter snapshots, expiry text and terminal outcomes remain
source-bound; opening or filtering the ledger still cannot repair the
append-only history, select another proposal, spend cash or consume RNG. The
existing Foundation reader regression remains green, with clean compilation
and diff checks. Stage 4 remains active with **4 major stages remaining** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 integrity follow-up (A7 non-finite storyline evidence):** The
Storylines reader now fails closed for infinity, NaN and overflow-sized values
in importance, update dates, beat dates and promotion scoreboards. These values
are projected to bounded display defaults and marked **Needs review** while the
raw retained thread remains untouched for the sanctioned load/migration path.
Stable story IDs, duplicate suffixes, selection restoration, follow state and
all authored beat text remain unchanged. A UI-data regression covers non-finite
legacy numbers and verifies that opening the reader is read-only; the full UI
data suite passes **176 tests**, with clean compilation and diff checks. Stage 4
remains active with **4 major stages remaining** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

The fallback path is also bounded: when a malformed `last_updated_month` would
otherwise inherit a non-finite `started_month`, the reader uses an explicit zero
date and retains the review marker. This closes the remaining default-value
escape without changing the saved chronology or its load/migration owner.

Profile storyline context and headless Followed Briefings now use the same
fail-closed numeric boundary. Non-finite dates are treated as an unavailable
boundary for filtering and sorting, and malformed calendar conversion cannot
abort the reader. The query returns the original retained thread objects where
the profile API requires identity, but performs no repair or ordering write.

**Stage 4 integrity follow-up (G3 Media desk numeric reader boundary):** The
read-only Media Rights dashboard, settled-receipts reader and selected campaign
detail now catch overflow-sized retained values as well as malformed strings.
Non-finite action usage, receipt amounts, campaign heat and campaign cost become
bounded display evidence; active offers, contracts, campaign history and source
identities remain untouched. The explicit media action/settlement owners retain
all spend, RNG and contract mutation authority. Media plan regressions pass
**56 tests**, with clean compilation and diff checks. Stage 4 remains active
with **4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 presentation follow-up (Fight History academy-date guard):** The
Profile Fight History reader now treats a malformed `amateur_bout_history`
container as an empty display projection instead of assuming it is iterable.
Academy month/week values are converted through a finite, overflow-safe helper;
negative months and impossible weeks are bounded to safe display values while
the retained amateur records remain byte-for-byte untouched. This keeps the
academy ledger readable for legacy or externally edited saves and preserves the
existing separation between amateur history and professional replay evidence.
The focused fighter-profile and UI-data regressions pass **207 tests**, with
clean compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

The same profile projection now rejects a non-list/tuple professional
`fight_history` envelope before slicing or parsing it. A malformed legacy field
therefore shows the existing empty-history state instead of being iterated as
characters or raising a type error; valid list/tuple history and every archived
bout identity remain unchanged.

The storyline reader's own page-limit boundary now catches overflow-sized
limits as well as malformed types, so an external `Infinity`/huge value cannot
abort the list before row projection. The limit remains bounded to the authored
reader maximum and no retained story data is changed.

**Stage 4 reader-safety follow-up (owned child-card schedule):** The child
promotion manager now projects a malformed `scheduled_events` envelope as an
empty list and bounds retained month/week values through a finite helper before
sorting or formatting them. Negative, non-finite and overflow-sized dates no
longer crash the manager or reach the calendar formatter; stable event IDs,
saved card order and explicit schedule/cancel mutation handlers remain intact.
The UI-data identity suite covers the guard, with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 staff-reader follow-up (AI employment ledger):** The read-only AI
staff employment ledger now catches overflow-sized limits and numeric fields in
salary, term, skill and morale projections. Infinity, NaN and other malformed
values become bounded display evidence; stable staff/promotion identities,
duplicate suffixes and the retained employment/market rows remain unchanged.
The ledger still performs no hiring, expiry, payroll, repair or RNG work. The
focused employment regression covers non-finite rows and limit handling, with
clean compilation and diff checks. Stage 4 remains active with **4 major stages
remaining** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 staff-reader follow-up (Talent Relations cases):** The defensive
relationship-case projection now catches overflow-sized review and history
boundaries as well as malformed strings. Non-finite dates become bounded zero
evidence while case IDs, source obligations, history rows and the raw retained
case shelf remain untouched. Existing explicit acknowledgement, action and
review handlers retain the only mutation boundary. The focused relationship
case regression passes **5 tests**, with clean compilation and diff checks.
Stage 4 remains active with **4 major stages remaining** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or modified.

The AI employment ledger also guards the retained promotion, staff and market
collections themselves. Non-list/tuple envelopes now render as an empty
read-model rather than being iterated as strings or raising; valid rows still
retain stable identity and duplicate handling, and the malformed source values
remain available for the sanctioned load/migration boundary.

The Talent Relations projection also type-checks evidence-reference and
obligation collections. A legacy string is no longer split into character
entries in the case detail; it becomes an explicit empty evidence list while
the complete raw case remains preserved for load/migration review.

The direct case-detail projection now applies the same guard when called with a
raw case, bounding its review month and refusing to iterate malformed original
obligations. This keeps both the table and detail paths consistent without
normalising the retained case.

The managed Staff Profile reader now applies the same overflow-safe boundary to
salary, tenure-story legacy score and reputation evidence. A malformed numeric
field cannot abort the profile window; it renders the existing bounded/unknown
state while preserving the selected employee and retained source row.

**Stage 4 integrity follow-up (G5 title-miss numeric evidence):** Resumable
title-miss decisions now reject non-finite or overflow-sized saved miss amounts
before they can be treated as official evidence. The fight is held in the
existing `needs_review` state, the recorded one-time fine is preserved, and no
fresh scale roll, prompt, title mutation or RNG draw occurs. Valid pending and
terminal choices remain unchanged. The title-decision resume suite passes **10
tests**, with clean compilation and diff checks. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

The Remove Belt choice now vacates either a primary or interim holder through
the canonical belt-lineage helper. Interim champions no longer retain a stale
interim flag or belt-map entry after the player's explicit decision; the title
stays on the line for the bout as recorded by the sanction snapshot.

The AI Staff Ledger window now treats affordability snapshots as optional,
read-only evidence: non-mapping snapshots are skipped, cash/payroll values use
finite bounded formatting, and non-finite runway values render as unavailable
rather than crashing or displaying `nan`. The retained employment rows,
promotion/staff identities and hiring boundaries are unchanged. The focused
Staff UI/employment checks pass **26 tests**, with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

The company hub's identity-bound Next Step reader now treats malformed roster
and scheduled-event envelopes as zero visible items and bounds cash/stability
through the same finite numeric projection. A corrupt company summary therefore
still renders a safe action recommendation without mutating the selected row,
promotion strategy or retained company data. Its focused UI regression passes,
with clean compilation and diff checks.

The managed Company Hub now also projects its roster defensively before any
sorting, belt summary or profile link is built. Non-list envelopes and malformed
fighter rows are omitted from the reader with an explicit unavailable-evidence
notice; the retained roster and all identity-bound company actions remain
untouched. This closes a UI crash boundary without weakening scouting or
ranking visibility for valid fighters. The focused company/UI checks pass, with
clean compilation and diff checks.

The selected-company projection now applies the same defensive roster,
collection, mapping and finite numeric boundaries before either the profile pane
or Company Hub consumes it. Malformed MMA roster rows, finance/belt envelopes,
staff collections and summary amounts are projected as safe values with a
reader status marker; no source object or strategy is repaired on open. Focused
company-reader regressions pass, with clean compilation and diff checks.

The isolated smoke playtest also passes after this projection change, with only
the documented headless Matchmaking coordinate probe skipped. Roster,
promotion, gym, sample-fight, persistence and quick-save checks remain green;
no EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (Regional Prospects throughput reader):** The
regional backlog/throughput projection now fails closed on malformed promotion,
roster and free-agent collections, and catches overflow-sized cached backlog
values. Regional Prospects continues to call the non-repairing throughput path;
opening or filtering the table cannot rewrite its monthly cache or consume RNG.
The focused Regional/UI regression passes with clean compilation and diff
checks. Stage 4 remains active with **4 major stages remaining** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 integrity follow-up (Regional Prospects assessment reader):**
Candidate assessment now bounds non-finite or malformed age, record, potential,
momentum and popularity values before calculating eligibility, win rate,
development status or blocked reasons. Missing or invalid promotion identity is
treated as an unknown origin rather than raising or matching the wrong company.
The `repair=False` reader therefore remains observational: it cannot seed a
history baseline, rewrite a fighter, consume RNG or change backlog state. The
assessment, throughput, feasibility and scouting regressions pass **32 tests**;
compilation and diff checks are clean. Stage 4 remains active with **4 major
stages remaining** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 integrity follow-up (company milestone projection):** Finance/history
milestone outlooks now reject non-finite and overflow-sized saved values and
clamp converted magnitudes before calculating cash gaps, event gaps or ETA.
Malformed weekly-history and result rows remain omitted from the read model,
while the raw finance/history envelopes stay untouched for the sanctioned load
or gameplay repair boundary. The focused milestone/finance regressions pass
**2 tests**, with clean compilation and diff checks. Stage 4 remains active with
**4 major stages remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

The maintained runner's first pass reached the existing narrative-performance
budget and reported a runtime-only miss; the isolated benchmark immediately
reran green (CPU median overhead **+0.88%**). No narrative source or gameplay
state changed, so this is retained as benchmark variance rather than a
functional regression. The full UI-data suite remains green at **179 tests**.

**Stage 4 reader-safety follow-up (Upcoming Cards broadcaster status):** The
event-provider status reader now projects malformed broadcaster and media-rights
fields through finite bounded values. Invalid reach, fee, term or entitlement
values render as safe zero/expired or unavailable evidence rather than raising;
the retained finance envelope is not repaired. Provider rows are type-checked so
an incomplete legacy entry cannot abort the Upcoming Cards page. Existing event
economics and identity-bound card actions remain unchanged; the focused UI
checks pass with clean compilation and diff checks. No EXE or user save was
rebuilt or modified.

**Stage 4 reader-safety follow-up (Media Desk evidence):** Media dashboard,
settlement-receipt and campaign-detail readers now bound non-finite and
oversized retained amounts before formatting. Rights income, sponsor totals,
relationship changes, campaign cost/heat and receipt amounts therefore render
safe values instead of risking a formatting crash or unbounded UI payload. The
source finance envelope, offer history, delivery evidence and identity maps
remain untouched; Media plan/system and UI-data checks pass **58 tests** with
clean compilation and diff checks. No EXE or user save was rebuilt or modified.

Finance history rows now use bounded display month/week projections in both the
table and selected-week detail reader. A malformed retained date cannot reach
calendar formatting and crash the page; its original row remains available
through the identity map for review. The Finance/media malformed-history and
overflow checks remain green, with no refresh-time finance repair or RNG effect.

**Stage 4 reader-safety follow-up (Staff display projection):** Staff skill,
morale and salary fields now reject non-finite values and clamp converted
legacy magnitudes to their display-safe ranges (0–100 for ratings and morale;
zero to a bounded annual salary ceiling). Malformed rows still remain visible
as unavailable evidence, while ordinary employment, payroll and contract
owners retain their existing values and mutation boundaries. Staff employment
and UI-data regressions pass **25 tests**, with clean compilation and diff
checks. No EXE or user save was rebuilt or modified.

**Stage 4 reader-safety follow-up (Media campaign-plan summary):** The active
campaign-plan summary now projects malformed quote/detail mappings,
completion-ledger containers and revision values through finite bounded
display helpers. A legacy quote containing `Infinity`, a non-mapping detail
payload or a string completion ledger therefore renders a safe zero/unknown
summary rather than raising during formatting; the retained plan, quote source
and action receipts remain untouched. The media-plan regression passes **57
tests**, with clean compilation and diff checks. Stage 4 remains active with
**4 major gates remaining** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Media settlement evidence):** Receipt detail
readers now resolve audience history through the saved `contract_id` and
`outlet_id` before considering an event-only match. If identity-bearing rows
disagree, the reader will not bind a different contract merely because an
event label or display name matches; only identity-less legacy rows may use
the explicit event fallback. The source receipt, audience ledger and duty
history remain unchanged, and the Media plan/system identity checks pass **58
tests** with clean compilation and diff checks. No EXE or user save was rebuilt
or modified.

**Stage 4 reader-safety follow-up (Game & Saves metadata):** The selected-save
inspector now bounds month/week metadata before calling the calendar formatter.
 Non-finite, malformed or overflow-sized legacy dates render `Unknown game date`
 while company, save identity and action state remain visible; the reader does
 not create directories, normalize the save or alter the retained metadata.
 The persistence regression and compile/diff checks pass, including the new
 malformed-date case. No EXE or user save was rebuilt or modified.

The same reader boundary now applies to library counts: autosave and rolling
backup enumeration accepts `create=False`, so refreshing Game & Saves never
creates the active save slot, `Autosaves` folders or `Backups` folders merely
to display zero counts. Explicit save, backup and autosave owners retain their
normal create-on-write behavior. Persistence regression and compilation remain
green; no EXE or user save was rebuilt or modified.

**Stage 4 reader-safety follow-up (membership history paging):** Foundation
membership readers now bound malformed paging, as-of and result-limit inputs
without converting a profile refresh into an exception or an unbounded slice.
Non-finite, boolean, overflow-sized and non-numeric presentation arguments fail
closed to bounded defaults; the append-only membership envelope and all source
IDs remain unchanged. Foundation membership regressions pass **36 tests**, with
clean compilation and no EXE or user save rebuilt or modified.

**Stage 4 reader-safety follow-up (Regions profile context):** Region team and
profile summaries now type-check retained gym, promotion and specialty
collections, use finite bounded sort keys, and tolerate malformed limits or
legacy row attributes. A damaged gym/promotion row is skipped or shown as
unavailable evidence rather than aborting the Regions page; the source region,
gym and promotion collections remain untouched. Focused Regions/UI checks pass
with clean compilation and no EXE or user save rebuilt or modified.

**Stage 4 reader-safety follow-up (World Hub repaint):** World Hub promotion
and gym rows now project malformed collections and numeric fields through
finite bounded helpers before sorting or formatting. Invalid show-history dates,
capacity/load, momentum, tier inputs and specialty containers render explicit
safe values while stable promotion/gym identities and selection restoration are
preserved. The refresh remains observational and does not synchronize gym
membership or repair the retained world. The full UI-data suite passes **179
tests** and the smoke playtest passes; no EXE or user save was rebuilt or
modified.

**Stage 4 reader-safety follow-up (Fighter Search source projection):** The
200-ms debounced Fighter Search now receives a defensive source projection:
malformed roster/free-agent/promotion/combat-sport/retired collections are
skipped without mutation, while universe-record and recent-form summaries
bound non-finite legacy record fields. Search identity, 100-row pagination,
scouting visibility and selection restoration remain unchanged. Focused
Fighter Search/UI checks pass with clean compilation; no EXE or user save was
rebuilt or modified.

**Stage 4 reader-safety follow-up (Results archive detail):** Results list and
selected-card detail now bound malformed retained event dates and play-by-play
containers before calendar formatting. Invalid rows remain visible as explicit
unavailable evidence, while the result identity map, replay availability and
raw archive remain unchanged. Focused Results/UI checks pass with clean
compilation; no EXE or user save was rebuilt or modified.

The complete UI-data regression suite passes **182 tests** after the World Hub,
Fighter Search and Results reader slices; the smoke playtest remains green.

**Stage 4 verification update (maintained regression runner):** The complete
`run_regression_suite.py` pass now reaches the end of the requested isolated
suite catalogue successfully. Fight Night presentation/archive/layout and
experience checks, trait/profile/persistence/runtime audits, UI-data
(**182 tests**), media (**58 plan/system checks**), Staff, finance, scouting,
regional, Combat Sports, identity, audio/window lifecycle, fight-engine
calibration, full-system, database-editor and stability playtests all pass.
The runner reports `ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`; the
documented headless Matchmaking coordinate probe remains the only intentional
smoke skip. This closes the current verification baseline without changing
EXEs or user saves. Stage 4 remains active with **4 major gates** and **12
named card areas** unfinished or policy-gated; the next implementation slice
must still respect the G2/G3 closeout, G4 Staff/AI qualification and G5
policy contracts rather than treating a green reader suite as approval for
unresolved mechanics.

**Stage 4 presentation follow-up (V03 stacked Matchmaking workspace):** The
narrow Matchmaking layout now raises its outer scrollable workspace to 720px,
reserves a 520px fighter-explorer pane and keeps the draft-card pane compact.
The sash placement leaves the filter/action header and at least four readable
32px fighter rows together at laptop widths; the card table remains internally
scrollable. Switching back to side-by-side restores the 620px workspace and
the wider table density. This is presentation-only and does not alter fighter
eligibility, booking identity or saved cards. The new layout regression and
full UI-data suite pass **183 tests**, `smoke_test.py` remains green with its
documented headless Matchmaking coordinate probe skipped, and the source
compiles cleanly. No EXE or user save was rebuilt or modified.

**Stage 4 reader-safety follow-up (V16 Academy archive identity):** Academy
showcase-card and alumni readers now keep malformed retained rows visible as an
explicit `Unavailable retained record` state. Valid dictionaries continue to
bind directly to their saved card/event or fighter/prospect identity; malformed
rows use a deterministic type/value fingerprint plus duplicate suffix rather
than a mutable table index. Replay, graduate-profile and matching-right actions
remain disabled for unavailable rows, while the original Academy collections
are left untouched for the sanctioned repair/load boundary. The new regression
proves valid identity preservation, malformed-row visibility and source
immutability; Academy, profile and UI-data checks pass **217 combined tests**
(UI-data alone **184**), smoke remains green with the documented headless
Matchmaking probe skipped, and the source compiles cleanly. No EXE or user save
was rebuilt or modified. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated.

**Stage 4 reader-safety follow-up (Scouting Target Board selection clearing):**
Filtering, paging or narrowing the Target Board can remove a selected fighter
without Tk emitting a selection event. The refresh reader now explicitly clears
the identity, intel, advice and market cards whenever the prior source-bound row
is no longer visible, preventing stale scouting evidence from being mistaken for
the newly filtered result set. Retained report data, shortlist state and fighter
identities remain untouched; selecting a still-visible row continues to restore
its summary. The UI-data suite passes **184 tests**, the focused scouting checks
and compilation/diff checks are clean, and no EXE or user save was rebuilt or
modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 presentation follow-up (Scouting Target Board semantic cards):**
Selected-target advice cards and the board legend now use the active semantic
status palette for recommend, monitor, pass, shortlisted and stale states
instead of fixed dark-theme colours. The legend widgets retain their semantic
keys so live theme changes retheme them as well; status words remain visible as
text. This is presentation-only: no scouting report, shortlist, ranking or
fighter data changes. Focused UI-data checks and compilation/diff checks pass;
Stage 4 remains active with **4 major gates** and **12 named card areas**
unfinished or policy-gated.

**Stage 4 reader-safety follow-up (Profile Overview metric projection):** The
Overview now projects retained momentum, morale, fatigue, activity, camp weeks
and native skill bars through a finite bounded reader helper before rendering
meters, readiness and the ordered assessment. A malformed or non-finite legacy
value therefore becomes a safe display value without rewriting the fighter or
revealing hidden ratings in scouting mode; readiness still uses the inverted
fatigue measure and momentum remains centred on 50. The profile regression now
covers the projection and the focused suite passes **30 tests**, with clean
compilation and diff checks. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 identity follow-up (Profile comparison picker):** The fighter
comparison chooser now binds each visible row to the saved fighter ID, with a
deterministic retained-field fingerprint for ID-less legacy fighters and a
stable duplicate suffix when source keys repeat. Query refreshes restore the
same source-bound selection only when that fighter remains visible; when a
filter or the first-150 display cap removes it, the old selection is cleared
instead of being silently retargeted by row position. Comparison actions still
open the existing read-only comparison workflow and do not alter fighter,
scouting or roster data. The profile regression now covers durable and legacy
identity keys (31 tests), with clean compilation and diff checks. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 reader-safety follow-up (Development evidence projection):** The
Development tab now consumes a defensive projection of its calculated score,
factor list and retained development/camp chronicles. Non-finite or malformed
values used by meters and plots are bounded to display-safe ranges; malformed
chronicle rows remain visible as explicit unavailable evidence rather than
being dropped or treated as a new development result. The trajectory continues
to plot stored change order (with the current overall appended only for
context), and the signed driver bars retain one shared absolute scale. The
fighter, development ledger, camp history and RNG are untouched by repainting.
The profile regression now covers malformed factors and chronicles (32 tests),
the UI-data suite remains green at **184 tests**, smoke passes with the
documented headless Matchmaking probe skipped, and compilation/diff checks are
clean. Stage 4 remains active with **4 major gates** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Company history malformed-row keys):** The
Company & Title History reader no longer uses a malformed row's visible ordinal
as its Treeview identity. Scalar/container legacy rows are fingerprinted from
their retained content and type, while opaque values fall back to a type-based
key with deterministic duplicate suffixes. Valid membership/title IDs and
identity-bound actions are unchanged; refresh, paging and export remain
read-only, and the raw retained envelope is not normalised. The profile and
focused UI-data identity checks pass with clean compilation/diff checks. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Legacy Academy Alumni window):** The older
Academy Alumni dialog now follows the same stable-row contract as the current
Academy page. Saved fighter/prospect/alumni IDs are preferred; ID-less and
malformed rows receive deterministic retained-content/type fingerprints with
duplicate-safe suffixes, and malformed entries remain visibly unavailable.
Changing the dialog's ordering or opening it cannot retarget a graduate or
rewrite the Academy archive. The Academy identity/UI checks pass with clean
compilation and diff checks. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 reader-safety follow-up (Region Hub projection):** The Region Hub
now consumes the same defensive, non-repairing region projection as the
Regions profile readers. A missing, non-mapping or malformed retained region
envelope renders an explicit unavailable profile with bounded numeric fields,
safe areas/teams/benefits and no inferred world facts; gym, fighter, event and
promotion lists also ignore malformed rows without rewriting the source
collections. Opening the hub, refreshing it or switching its region leaves
regions, roster, calendar, finance, memberships and RNG untouched, while
explicit management paths retain their normal repair/mutation boundaries.
Focused Region Hub checks pass (3 tests), the profile suite remains green at
**32 tests**, and compilation/diff checks are clean. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Company Proposal legacy keys):** The read-only
Company Proposal Ledger now fingerprints ID-less retained proposal rows from
their canonical content/type instead of using the visible ordinal. Saved
`proposal_id` values remain authoritative; duplicate source IDs receive
deterministic suffixes, and the detail reader continues to resolve through the
row map without mutating the append-only foundation collection. Refreshing,
filtering or sorting the ledger therefore cannot retarget a legacy proposal or
create a new proposal record. The focused identity check and full UI-data suite
pass (**184 tests**) with clean compilation/diff checks. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Storylines and World Chronicle legacy keys):**
Story and Chronicle readers no longer fall back to the visible list position
when a retained row has no saved story/entry ID. Their legacy keys are derived
from the recorded participant, company, boundary, headline and raw-type
evidence; completely empty or opaque rows still receive a deterministic
unavailable key and duplicate-safe suffix. Existing saved IDs remain
authoritative, and the readers stay non-mutating, so sorting, filtering and
theme refreshes cannot retarget a storyline or chronology entry. Focused
identity/defensive-reader checks pass with clean compilation/diff checks. Stage
4 remains active with **4 major gates** and **12 named card areas** unfinished
or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Media settlement receipt legacy keys):** Media
settlement receipts without a saved `receipt_id` or `event_id` now use a
deterministic fingerprint of their retained date/event/company and settlement
facts, with duplicate-safe display suffixes. Opaque malformed rows receive a
type/content UI key and the selected-receipt reader refuses stale pre-upgrade
IDs instead of resolving a current list position. Receipt detail remains an
observational projection: no finance repair, settlement, offer refresh or RNG
work is triggered by opening or repainting the table. Media identity and
malformed-reader regressions pass with clean compilation/diff checks. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (cross-page legacy row contract):** The remaining
ordinal fallbacks in the first-playable readers were replaced with
content/type fingerprints and duplicate-safe suffixes. This covers matchmaking
draft cards and unresolved booking slots, regional-prospect pairs, sponsor
market rows, World Hub companies/gyms and empty Regions rows, profile-history
rows, and scouting decision packs. Saved IDs remain authoritative; malformed or
opaque rows stay explicitly unavailable, and stale pre-upgrade IDs fail closed
instead of resolving the current visible position. No refresh changes card
order, roster, scouting, sponsor, finance, region or RNG state. Focused
identity checks pass (22 tests) and the maintained runner is green, including
UI-data **185 tests**, booking, media and profile suites. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Finance and Awards legacy keys):** Finance weekly
history, cash-runway forecasts and saved scenario readers now bind rows to the
recorded month/week, offset, scenario ID or a deterministic retained-content
fingerprint when that evidence is absent. Awards fighter leaderboards and
title-lineage detail rows likewise fingerprint ID-less records, including
empty/opaque legacy entries, and use duplicate-safe suffixes. Refreshing or
sorting these readers cannot route detail to a different historical row; the
finance envelope, award ledger, cash forecast and RNG remain untouched. Focused
finance/awards/media/booking checks pass (**93 tests**) with clean compilation
and diff checks. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 staff-reader follow-up (brief/work/exception keys):** Staff brief
rows, work receipts and exception evidence now prefer their saved brief,
operation, work or exception IDs and otherwise use deterministic fingerprints
of retained planning/evidence fields. Duplicate source rows receive suffixes;
malformed or opaque rows remain visible only as unavailable evidence and cannot
be resolved through a mutable list index. Staff refreshes preserve source-bound
selection and do not normalize policy, execute handlers, spend cash, consume
RNG or award progression. Staff management regressions pass (**56 tests**) with
clean compilation/diff checks. Stage 4 remains active with **4 major gates**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 staff/child-management identity follow-up:** The shared Staff roster,
candidate and contract table helper now fingerprints ID-less retained staff
records, including empty/malformed rows, instead of using the visible index.
Child-promotion scheduled cards similarly use saved `event_id` values or a
retained name/date/status/venue fingerprint; missing IDs remain legacy
references and cancellation still fails closed until an explicit durable event
identity exists. Existing staff IDs, promotion IDs, fighter IDs and event
actions remain unchanged. Focused Staff/child-management checks pass (**59
tests**) with clean compilation/diff checks. Stage 4 remains active with **4
major gates** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 identity follow-up (Scouting legacy search keys):** The Scouting
assignment reader now fingerprints an ID-less retained search from its
authored request fields, and falls back to deterministic retained content/type
evidence when an imported row has none of those fields. The old visible
`search:legacy:row-N` key is no longer produced, so sorting, filtering or
refreshing the assignment list cannot retarget a legacy search. Saved
`assignment_id` rows remain authoritative; malformed entries stay readable and
read-only. `scouting_regression_test.py` now covers index-independent empty and
opaque rows (28 tests), and the full UI-data suite remains green at 185 tests.
Compilation and diff checks are clean. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 identity follow-up (Legacy Ledger rank-independent rows):** The
all-time Legacy Ledger now uses the source-bound fighter identity as its
Treeview key instead of appending the displayed legacy rank. Sorting or
filtering therefore cannot turn a career into a different row identity; any
unexpected duplicate source key receives a deterministic suffix. The existing
profile-opening and score-breakdown routes remain unchanged, and no legacy
score, record or archive data is recalculated by the reader. UI-data identity
coverage includes the source contract; focused identity tests, compilation and
diff checks pass. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 identity follow-up (World Staff and watchlist readers):** The AI
staff-employment read model now fingerprints ID-less staff rows from retained
employment facts and promotion/source context rather than using their visible
index. The Scouting watchlist reader likewise fingerprints ID-less watchlists,
retains duplicate generated rows with deterministic suffixes, and keeps the
existing duplicate authored-ID compatibility behaviour. Both readers remain
non-mutating; stable saved IDs stay authoritative and no hiring, expiry,
shortlist or RNG path changed. Staff employment, Scouting and identity-focused
regressions pass (25 and 29 tests respectively), with clean compilation and
diff checks. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 Staff execution slice (Talent Relations renewal batches):** Talent
Relations now has an explicit `contract_batch_commit` action in the Staff
capability catalogue. The player still creates and reviews a renewal batch in
the Contracts workbench; a Staff brief must name that saved `contract-batch-*`
ID and explicitly allow-list the commit action. Recommendations and Selective
Recommendations expose only the zero-spend contract review, while Full Auto
alone can invoke the existing batch owner. Before invoking it, the adapter
checks every currently eligible row, applies a conservative 1.75x allowance to
exclusive quotes (3x for legacy non-exclusive quotes), and validates the
brief ceiling, monthly/action ceilings, cash and reserve. Missing IDs, malformed
quotes, stale/departed fighters and empty eligible sets fail closed without a
negotiation attempt. The existing Foundation row operations remain authoritative
and retry-idempotent; actual per-row cost is now retained in the sealed result,
and Staff work rows retain the complete structured result/evidence payload for
audit and UI detail. Focused Staff management (**59 tests**) and contract-batch
workbench (**4 tests**) suites pass with clean compilation/diff checks. The
Staff page now explains that Talent Relations targets an existing batch ID and
does not create one automatically. Stage 4 remains active with **4 major gates**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 identity follow-up (fighter Treeview rows):** Shared fighter tables
no longer include the visible source/list index in their base row IDs. Roster,
Contracts, Matchmaking availability, Free Agents, Regional Fighters, company
rosters and company rankings now bind rows to the saved fighter identity; only
malformed duplicate source identities receive a deterministic `#N` suffix in
the current projection. Existing selection/mapping handlers continue to use
their source-bound dictionaries, so sorting/filtering cannot retarget a unique
fighter. The UI-data suite passes (**187 tests**) with clean compilation and
diff checks. No gameplay, ranking, roster, save or EXE state was changed.

**Stage 4 title-decision follow-up (identity-safe rebooking):** The Rebook Fight
branch now captures the cancelled bout's stable participant IDs and its title,
interim/special-belt, main-event, tier, region/city and fight-plan terms at the
decision boundary. The calendar worker resolves those same fighters by ID (a
name-only legacy row is accepted only when the name is unique), checks future
card conflicts by both ID and display name, and recreates the saved championship
sanction for the new official weigh-in. The terminal title-miss decision is not
copied into the new fight; the old event retains the original evidence and the
rescheduled card receives a fresh weigh-in/prompt. Rebooking remains limited to
an existing suitable future player card, preserves the no-result/no-defence
boundary, and does not add a new RNG draw. `rebooking_regression_test.py` covers
title-term/ID retention and duplicate-name fail-closed behaviour; the title
decision, replacement and smoke suites pass (25 combined title/replacement
checks plus the normal smoke path). Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 title-decision follow-up (legacy replacement identity):** The
Last-Minute Replacement candidate reader now keeps ID-less legacy fighters
visible using deterministic retained-content fingerprints, with `#N` suffixes
for exact duplicate rows. The selected candidate key is carried through the
title prompt and replacement commit, so an imported fighter cannot be routed by
object identity or silently collapsed with a same-name row. Saved fighter IDs
remain authoritative and the replacement operation/eligibility rules are
unchanged. `last_minute_replacement_regression_test.py` now covers repeatable
ID-less duplicate keys (11 tests); title-decision, rebooking and smoke checks
remain green. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 title-decision follow-up (durable rebooking review):** A Rebook Fight
 request is no longer discarded when the current calendar has no suitable future
 player card. The pending plain-data entry now moves once to `needs_review`,
 retains its stable fighter IDs, saved title/tier/fight-plan terms and source
 weigh-in link, and records the last checked boundary plus an actionable reason.
 The worker stays quiet on repeated scans, then moves the same request exactly
 once when a later eligible card appears; no new fight result, title defence,
 fine or RNG draw is created by the retry. Ambiguous name-only legacy careers
 remain held for review instead of being reassociated. `rebooking_regression_test.py`
 now covers title retention, duplicate-name fail-closed resolution and the
 unavailable-card/quiet-retry/later-move path (3 tests); the title-decision,
 replacement and smoke suites remain green. Stage 4 remains active with **4
 major gates** and **12 named card areas** unfinished or policy-gated. No EXE or
user save was rebuilt or modified.

**Stage 4 identity follow-up (opaque Staff retention rows):** Staff retention
readers no longer manufacture `row-N` keys for empty or malformed legacy
records. These rows now receive deterministic type/content fingerprints with an
explicit opaque marker, and selection restoration prefers the same retained
source object before using a durable saved `staff_id` after reload. Duplicate
opaque rows therefore remain visible without allowing a sort or refresh to
select a different employee. `staff_management_regression_test.py` covers
empty/non-dict row keys and the existing 59-test Staff suite remains green.
Stage 4 remains active with **4 major gates** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Academy amateur-history rows):** Academy profile
history rows now use saved bout/fight/event/record identities where available,
with deterministic retained-content fingerprints for older free-form entries
and duplicate suffixes for identical rows. Malformed retained records remain
visible as explicit unavailable rows. The profile history reader no longer
binds a row to its displayed position, so filtering/reordering cannot make an
old amateur result point at a different bout. `ui_data_regression_test.py`
covers deterministic keys, malformed-row handling and the no-index source
contract. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 identity follow-up (legacy fighter profile windows):** Profile and
Company History readers now use saved `fighter_id` values or a deterministic
retained identity projection for their managed-window keys. Process-local
object IDs no longer decide which legacy profile window receives a refresh or
focus request, while the underlying historical reader still fails closed when
an ID-less career is ambiguous. `ui_data_regression_test.py` and the profile
suite cover the fallback key and existing historical evidence rules. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Booking Workbench legacy rows):** Booking
Workbench option and draft-review readers now derive UI row keys from saved
`fighter_id`/`booking_id` values and otherwise from deterministic retained-data
fingerprints. The visible list position is never used as the durable action
target; exact duplicate legacy rows receive deterministic suffixes while the
stored source row remains attached to its review/commit callback. This keeps
unresolved TBA slots and candidate alternatives visible without collapsing or
retargeting them after a refresh or reorder. `ui_data_regression_test.py`
covers position-independent option and draft keys; compile, UI-data, Staff,
rebooking and smoke checks remain green. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 identity follow-up (Staff profile migration):** the load/startup
compatibility repair for ID-less staff rows no longer hashes the source list
index into a saved `staff_id`. It now uses retained scope/name/role/contract
facts, with deterministic suffixes only for exact duplicate identities;
existing IDs remain authoritative. Reordering a legacy staff or candidate
collection before repair therefore preserves the same employee identity,
while malformed rows still follow the established defensive path. The
`staff_employment_regression_test.py` position-independence case and the
combined Staff/persistence checks pass (**85 focused tests**); no payroll,
expiry, RNG, save format or gameplay rule changed. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or policy-gated.
No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Owner Objectives migration):** legacy owner-goal
rows now receive their compatibility `goal_id` from retained company, goal,
metric, target, deadline and semantic fields instead of the source list
position. Exact duplicate legacy objectives receive deterministic `#2`, `#3`
suffixes, while existing IDs remain authoritative. Reordering an old goal
collection before load therefore cannot attach observations or actions to a
different objective; the existing explicit boundary worker and pure page
reader remain unchanged. `owner_goal_regression_test.py` and the full
UI-data suite pass (**195 focused tests**), with clean compilation. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Talent Relations case migration):** ID-less
retained relationship cases now receive a deterministic identity from their
fighter, source and obligation evidence rather than `CASE-<row number>`.
Exact duplicate legacy cases remain visible with deterministic suffixes; saved
case IDs stay authoritative, and the defensive reader still leaves the raw
collection untouched until an explicit mutation or load repair. This keeps
Staff contract review, acknowledgement and action routing attached to the same
historical case after reorder. Relationship, Story Briefing, Staff and UI-data
coverage passes (**260 focused tests**) and the smoke playtest passes. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 identity follow-up (Followed Story subscriptions):** ID-less legacy
follow rows now receive deterministic IDs from their retained target identity
and coverage/creation facts rather than `SUB-<row number>`. Exact duplicate
legacy follows remain visible with deterministic suffixes; saved subscription
IDs stay authoritative, and story/briefing readers continue to project without
rewriting the raw collection. Reordering a legacy subscription shelf therefore
cannot retarget acknowledge, snooze or unfollow actions. Story Briefing,
Relationship, Staff and UI-data coverage passes (**261 focused tests**) with
clean compilation. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 identity follow-up (Scouting Decision Pack migration):** ID-less
legacy recruitment packs now receive deterministic IDs from retained pack name,
purpose, watchlist, candidate and creation facts rather than `PACK-<row
number>`. Exact duplicate legacy packs remain visible with deterministic
suffixes; saved pack IDs stay authoritative, and the scouting page remains a
read-only projection until an explicit pack mutation or migration boundary.
Reordering an old pack shelf therefore cannot redirect update/archive actions
to a different candidate comparison. Recruitment-pack, Story Briefing,
Relationship, Staff and UI-data coverage passes (**265 focused tests**) with
clean compilation. Stage 4 remains active with **4 major gates** and **12 named
card areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 G5 integrity follow-up (manual testing failure boundary):** the
existing compatibility testing action now validates the retained finance
envelope, testing cost, staff lift and cash projection before it calls
`random.sample` or creates a case ID. Non-mapping finance, non-finite costs and
non-finite cash fail closed with a visible deferral; no sample, charge, case,
ledger write or test RNG is consumed. After validation, the explicit action
uses the validated cash projection for the charge so a malformed string/float
cannot fail after a screening roll. Provider-specific outcomes,
confirmation, appeals and sanctions remain gated by the approved J5 policy
tables. Drug-testing, catalogue, Staff and UI-data coverage passes (**270
focused tests**), smoke passes with the documented headless Matchmaking probe
skipped, and compilation/diff checks are clean. Stage 4 remains active with
**4 major gates** and **12 named card areas** unfinished or policy-gated. No
EXE or user save was rebuilt or modified.

**Stage 4 verification update (full maintained regression runner):** the
maintained isolated runner completed with `ALL REQUESTED ISOLATED REGRESSION
SUITES PASSED` after the Matchmaking and Media identity repairs. It covered the
190-test UI-data suite plus Staff, Media, booking, title-decision, profile,
persistence, engine, Fight Night, Combat Sports, long-run child-promotion and
stability suites. Stability reached Month 4 for seeds 2201–2203; the expected
headless Matchmaking coordinate probe remained the only documented skip. No EXE
or user save was rebuilt or modified.

**Stage 4 identity follow-up (Combat Sports running-order actions):** the
Combat Sports card editor now resolves Remove and Move Up/Down through the
selected bout's retained source object, with a unique saved `bout_id`,
`booking_id` or `fight_id` as the only detached compatibility fallback.
Equal legacy bout dictionaries without an identity anchor fail closed instead
of routing the action to the first equal row. Duplicate names, title flags and
running-order positions therefore remain attached to the original saved bout
through refresh and reorder. `ui_data_regression_test.py` and
`combat_sports_regression_test.py` cover the identity-map contract; the
combined UI/Combat Sports set passes **213 tests**, with clean compilation and
diff checks. This is a presentation/action-routing repair only: card order,
booking rules, settlement and sport results are unchanged. Stage 4 remains
active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 G4 qualification follow-up (Staff evidence audit):** the long-run
Staff diagnostic now treats malformed retained envelopes as evidence findings
rather than silently dropping them. Non-list `work_log`/`briefs` collections
produce explicit collection findings; non-mapping rows remain visible as
source-bound row findings; executed and recommendation work must carry both a
durable `work_id` and `operation_id`; and unknown work statuses are reported as
unsupported. The audit remains a pure projection: it does not repair rows,
rewrite the save, rerun handlers, spend cash, consume RNG or award progression.
Regression coverage verifies malformed rows/collections, missing operation IDs,
unsupported statuses, malformed progression envelopes/credit lists and no state
drift alongside the existing evidence, duplicate-ID, paid-recommendation and
orphaned-progression checks. Staff regression coverage passes (**63 tests**); no EXE or user save was rebuilt or
modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 verification update (maintained suite after Staff audit):** the full
`run_regression_suite.py` pass completed with `ALL REQUESTED ISOLATED REGRESSION
SUITES PASSED`. It covered Fight Night presentation/archive/layout and audio,
trait and release gates, smoke and persistence, title-decision resume and
rebooking, booking/contract workbenches, J10 help/comparison, simulation
pause/checkpoints, long-run Staff/AI employment and specialty progression,
Finance/Media, relationship/recruitment/story/calendar, Combat Sports, editor
validation and the full engine/action coverage set. The run retained its
documented headless Matchmaking coordinate-probe skip; the stability playtest
passed for seeds 2201–2203. No EXE or user save was rebuilt or modified. Stage
4 remains active with **4 major gates** and **12 named card areas** unfinished
or policy-gated; this is a qualification checkpoint, not a claim that the
remaining G5 policy tables are approved.

**Stage 4 L0 qualification follow-up (Staff evidence metrics):** yearly
play-level audit measurements now include bounded Staff work-log, brief,
exception and progression counts, credited-work totals and malformed-evidence
counts. The projection preserves non-mapping rows and malformed collections as
diagnostic counts without normalising `staff_management` or invoking Staff
handlers. `play_level_audit_regression_test.py` passes (13 tests), with clean
compilation. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 L0 qualification follow-up (Staff ledger invariants):** the
read-only hard-invariant scan now checks Staff work-log and operation identity,
malformed work/progression rows and progression credits that point to missing
work. Duplicate or missing identities are reported with source-bound paths;
the scan never normalises the ledger, invokes a Staff handler, spends cash or
consumes RNG. `play_level_audit_regression_test.py` passes (14 tests), with
clean compilation. Stage 4 remains active with **4 major gates** and **12
named card areas** unfinished or policy-gated. No EXE or user save was rebuilt
or modified.

**Stage 4 L0 qualification follow-up (Staff affordability evidence):** yearly
measurements now retain bounded monthly Staff payroll totals for the player and
AI/child promotions, along with malformed-salary counts and per-company
payroll fields. Invalid salary data is classified as unknown; no finance
envelope, employment row, RNG state or live cash balance is repaired. The
focused audit/Staff suites pass (**78 tests**) with clean compilation. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 L0 qualification follow-up (overdue commitment evidence):** yearly
measurements now project explicit overdue commitments by source: super-event
offers, booking and locked-slot proposals, tentative medical plans, Media
campaign plans, Staff briefs, owner objectives, fighter promises/career arcs
and Academy promises. Each row is evaluated against the serialized month/week
boundary and an active/terminal status; missing clocks, malformed deadlines and
legacy rows without an explicit due field fail closed rather than creating a
new overdue task. The report includes a bounded total plus a source breakdown,
while the reader leaves every retained envelope, finance value, RNG state and
live commitment untouched. Focused audit/Staff coverage passes (**80 tests**)
with clean compilation and diff checks. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 L0 qualification follow-up (calendar task timings):** the native
weekly calendar loop now records each task's elapsed wall-clock time in a
bounded diagnostic ring, including synchronous audit advances as well as the
cooperative UI path. The isolated audit copies and clears that ring at each
year boundary and stores a compact count, total, maximum and per-task summary
alongside the real serialized world measurement. Malformed, negative, non-finite
or oversized timing values are ignored or clamped; timings never affect
calendar order, RNG, finance, save state or stop-policy decisions. The focused
audit/Staff suites pass (**81 tests**) with clean compilation and diff checks.
Stage 4 remains active with **4 major gates** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 L0 qualification follow-up (roster/title supply evidence):** yearly
measurements now retain free-agent availability, the native record-based count
of eligible non-champion challengers, current vacant-title count and bounded
vacancy duration in weeks, plus explicit expired-offer counts. Vacancy duration
uses only an empty retained title map paired with a latest `Vacated` history
entry carrying a parseable saved boundary; missing or malformed dates remain
unknown. Challenger depth applies the existing two-win and wins-or-three-win
comeback gate without inventing rankings or resolving display names. Expired
offers are counted from retained terminal rows only. The read model remains
non-mutating and the focused audit/Staff suites pass (**82 tests**) with clean
compilation. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated. No EXE or user save was rebuilt or
modified.

**Stage 4 L0 presentation follow-up (audit report evidence):** the managed
Play Audit report now surfaces the new supply/commitment metrics and the latest
calendar timing summary in a labelled section instead of leaving them buried in
the checkpoint payload. Legacy or malformed timing values are bounded locally
for display, and the report never rewrites the retained snapshot. This is a
reader-only presentation change; the focused audit/Staff suites remain green
(**82 tests**) with clean compilation. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated. No EXE or user
save was rebuilt or modified.

**Stage 4 L0 qualification follow-up (measurement evidence audit):** the pure
audit layer now checks each yearly row for the required supply/title metrics,
bounded vacancy relationships and calendar timing summaries. Missing fields,
malformed/non-finite values, maximums larger than totals and missing per-task
timing maps become explicit warning findings; they never stop the isolated
world, repair a checkpoint or alter gameplay. The managed report retains these
findings under a dedicated Measurement Evidence section. The focused
audit/Staff suites pass (**83 tests**) with clean compilation. Stage 4 remains
active with **4 major gates** and **12 named card areas** unfinished or
policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 G5 follow-up (Testing Desk selection reaches manual commission):** the
explicit manual testing action now honours the saved Testing Desk provider and
sample-count selection. The provider's deterministic authored multiplier is
included in the quoted/charged amount, bounded by available roster size, and
the selected provider snapshot, policy snapshot and itemised quote are frozen
on each case. The established compatibility screening accuracy path is
unchanged; provider-specific detection, confirmation, appeals, sanctions and
staff commissioning remain gated by the approved J5 rules table. Regression
coverage proves premium/enhanced pricing, selected-provider case identity,
roster-bounded sampling and no change to the default legacy path. Drug-testing,
catalogue, Staff and smoke checks pass with clean compilation/diff checks.
Stage 4 remains active with **4 major gates** and **12 named card areas**
unfinished or policy-gated. No EXE or user save was rebuilt or modified.

**Stage 4 L0 qualification follow-up (cohort and identity evidence):** yearly
audit measurements now separate player, AI-promotion and owned-child cohorts,
report active talent, division counts, Staff and scheduled-event coverage for
each cohort, and expose each company's active divisions and eligible challenger
count alongside scheduled event counts for player, AI, child and owned Combat
Sports sources. A pure identity-quality projection counts missing and
duplicate fighter, promotion and event IDs without inventing replacements; the
managed report presents these values alongside the supply/commitment evidence.
Malformed rows remain diagnostic and the audit does not repair state, rerun
handlers or change RNG. The focused play-audit suite passes (**84 tests**) with
clean compilation and diff checks. Stage 4 remains active with **4 major gates**
and **12 named card areas** unfinished or policy-gated. No EXE or user save was
rebuilt or modified.

**Stage 4 G5 follow-up (J5 distinct sample outcomes):** the durable Testing
Desk case contract now preserves negative, preliminary-positive, inconclusive
and invalid sample outcomes as separate evidence. Case cards, filters, summary
metrics and timelines distinguish those states; inconclusive and invalid
samples remain reviewable without being treated as a proven violation, injury,
confirmation or sanction. Unknown result input fails closed to an explicit
invalid sample rather than silently becoming negative; legacy rows with the old
status-only shape retain their recorded negative/review meaning without a save
rewrite. Existing compatibility testing still produces its established
positive/negative results, and provider
selection, confirmation, appeals, sanctions and sporting consequences remain
gated by the approved J5 tables. Focused drug-testing/catalogue tests pass with
clean compilation; no EXE or user save was rebuilt or modified.

**Stage 4 G5 follow-up (J5 case-scope presentation):** the Testing Desk case
ledger now exposes the retained event scope as a source-bound list column, with
manual/no-event cases labelled explicitly. Search includes stored event
reference fields, while display never resolves a live event by name or repairs
the saved case envelope. The full event ID/reference remains available in the
detail payload. The focused drug-testing/catalogue suite passes (27 tests) with
clean compilation; no EXE or user save was rebuilt or modified. Confirmation,
appeal, sanction and sporting-consequence mechanics remain gated by the
approved J5 policy tables.

**Stage 4 G5 follow-up (J5 provider quote transparency):** Testing Desk
planning quotes now retain a bounded base-screening subtotal and explicit
provider-service adjustment in addition to the frozen total. The provider
comparison surface shows that arithmetic before selection, so a premium quote
is understandable rather than an unexplained multiplier. This is still a
planning/manual-commission boundary: no new confirmation, appeal, sanction or
provider-specific detection mechanics are implied. Drug-testing/catalogue
regressions pass (27 tests) with clean compilation; no EXE or user save was
rebuilt or modified.

**Stage 4 G5 presentation follow-up (title-miss replacement decision):** the
managed title-weight-miss panel now exposes the already-approved replacement
route as an explicit `LAST-MINUTE REPLACEMENT` section and button. The panel
explains that the player is selecting a ready same-division candidate and can
review company/world ranks before committing; existing stable fighter/corner
identity, medical/schedule/title rechecks, replacement history and belt rules
remain the mutation boundary. This closes a discoverability gap only and does
not add a new replacement candidate or alter title mechanics. Title-decision
and replacement regressions pass (22 tests) with clean compilation; no EXE or
user save was rebuilt or modified.

**Stage 4 G4/S3 progression integrity follow-up:** quarter-close Staff skill
progression now requires both a durable `work_id` and `lead_id` on each
qualifying executed receipt. Rows sharing a work ID are all excluded as
ambiguous, so retained duplicate receipts cannot qualify a gain and row order
cannot decide which target/month is credited. The existing three-distinct-month,
two-target, paid-work, annual-cap and skill-ceiling rules remain unchanged.
Staff management, specialty and employment regressions pass (95 tests) with
clean compilation; no EXE or user save was rebuilt or modified.

**Stage 4 G4/S3 progression evidence presentation:** Staff specialty rows now
show a compact, source-bound progression summary covering credited work,
distinct periods, qualified quarters and current-year skill-cap usage. Staff
profile readers expose the same summary beside retention evidence, so the
player can understand why a specialist is progressing without treating a
page-open, review or malformed legacy row as completed work. This is a
read-only projection; quarter-close qualification, caps and mutation owners
are unchanged. Staff management, specialty, employment and UI-data coverage
passes (287 combined tests) with clean compilation; no EXE or user save was
rebuilt or modified.

**Stage 4 G0/J4 profile-reader hardening:** Profile company-timeline rendering
now treats malformed membership-reader envelopes and non-mapping retained rows
as unavailable evidence. Valid intervals still retain their saved company and
boundary identities, while the owning page shows its explicit incomplete state
instead of crashing or silently binding a detail action to a different row.
This is a presentation-only guard; membership repair remains confined to the
load/migration boundary. Fighter Profile regressions pass (34 tests) with clean
compilation and diff checks. No EXE or user save was rebuilt or modified. Stage
4 remains active with **4 major gates** and **12 named card areas** unfinished
or policy-gated.

**Stage 4 J4 lineage-identity follow-up:** lineal title reconstruction from
 archived result cards now prefers the recorded `winner_id` and retains both
 `fighter_id` and `opponent_id` on rebuilt title rows. Defense/crown transitions
 therefore remain bound to the correct career when two fighters share a display
 name; legacy rows recover IDs only when the name is unambiguous and are left
 out of reconstruction when the winner label cannot identify one career. The
 migration remains an explicit load-boundary repair and keeps malformed legacy
 rows untouched. Foundation coverage passes (38 tests), Fighter Profile coverage
 passes (34 tests), compilation and diff checks are clean. No EXE or user save
 was rebuilt or modified. Stage 4 remains active with **4 major gates** and
 **12 named card areas** unfinished or policy-gated.

**Stage 4 J4 lineage-retention follow-up:** title-history migration now
deduplicates retained non-lineal rows with fighter, opponent, title-event and
event identities alongside the visible date/action/note fields. Two legacy
facts with the same text but different careers therefore remain separately
auditable instead of being collapsed by a display-only key. This is a
load-boundary preservation repair: it creates no synthetic IDs, changes no
live belt state and keeps malformed rows untouched. Foundation coverage passes
(39 tests), Fighter Profile coverage passes (34 tests), compilation and diff
checks are clean. No EXE or user save was rebuilt or modified. Stage 4 remains
active with **4 major gates** and **12 named card areas** unfinished or
policy-gated.

**Stage 4 G0/J4 title-reader boundary:** Profile title-history projection now
clamps malformed/non-finite result limits and fails closed for non-list belt
history containers. A malformed legacy history envelope therefore remains
available for explicit migration diagnostics without crashing or changing the
saved record. Valid ID-bound title rows and scouting/name ambiguity rules are
unchanged. Fighter Profile and Foundation coverage pass (74 combined tests),
compilation and diff checks are clean. No EXE or user save was rebuilt or
modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 J4 title-history evidence follow-up:** Profile History now carries
the archived opponent name and stable opponent ID from title-lineage facts
through the read model, detail view and export payload. Presentation row
fingerprints include both fighter and opponent identities, preventing
same-text title events from collapsing or retargeting during sorting, paging
or refresh. This preserves recorded evidence only; it does not resolve a
current opponent record or alter title mechanics. Fighter Profile and
Foundation coverage pass (75 combined tests), compilation and diff checks are
clean. No EXE or user save was rebuilt or modified. Stage 4 remains active
with **4 major gates** and **12 named card areas** unfinished or
policy-gated.

**Stage 4 verification update (J4 title-history evidence):** The complete
UI-data regression suite passes **192 tests** after the opponent-identity
projection, alongside the 36-test Fighter Profile and 39-test Foundation
groups. Source compilation and scoped diff checks remain clean. The reader
changes do not rebuild an EXE, write a user save, resolve current rankings or
alter title settlement. Stage 4 remains active with **4 major gates** and
**12 named card areas** unfinished or policy-gated.

**Stage 4 G3/A3 forecast evidence follow-up:** Cash-runway projections now
distinguish a malformed non-list `week_transactions` shelf from a genuine
empty paid-history shelf. The forecast reports an explicit unavailable-row
diagnostic while preserving the raw finance envelope and leaving cash, RNG,
schedule and ledger state untouched. The cash-runway regression passes 16
tests, with clean compilation and diff checks. No EXE or user save was rebuilt
or modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 G3/A3 scenario-archive boundary:** The saved cash-runway scenario
reader now projects a labelled unavailable archive row when the retained
scenario collection is malformed. The Finance window shows the repair-boundary
message rather than implying that zero snapshots were ever saved; valid rows
still receive current/stale input labels and remain read-only. The raw finance
envelope is untouched. Cash-runway coverage passes 17 tests, the native-dialog
inventory passes 3 tests, and compilation/diff checks are clean. No EXE or user
save was rebuilt or modified. Stage 4 remains active with **4 major gates**
and **12 named card areas** unfinished or policy-gated.

**Stage 4 verification update (A3 Finance reader):** The complete UI-data
regression suite was rerun after the scenario archive change and passes **192
tests**. Focused cash-runway coverage remains green at 17 tests; source
compilation and scoped diff checks are clean. No EXE or user save was rebuilt
or modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 G3/A3 scenario-status follow-up:** Finance now distinguishes an
unavailable saved-scenario archive from a real archive containing zero, current
or stale snapshots. The summary surface no longer counts the transient
`Unavailable` diagnostic row as a saved planning record; it reports the
load/migration repair boundary and keeps the no-reservation guidance visible.
Valid snapshot counts, freshness labels and the read-only scenario window are
unchanged. The affected UI-data suite passes **192 tests**, the cash-runway
suite passes **17 tests**, and scoped compilation/diff checks remain clean. No
EXE or user save was rebuilt or modified. Stage 4 remains active with **4 major
gates** and **12 named card areas** unfinished or policy-gated.

**Stage 4 G4/J6 coaching-career follow-up:** Academy Coach market candidates
now support the approved retired-fighter career link. The retained fighter
stays in the retired archive with their original identity and record, while
the candidate receives a separate staff identity, an authored skill-45
starting baseline, and the normal market salary/term quote. Repeated market
refreshes exclude a fighter already linked to an active staff or candidate
row. Staff profile readers explain the provenance and preserve the explicit
comeback boundary. Contract validation now fails closed when that linked
coach is actively supervising a development block; ending the Academy
assignment is the required player action before comeback talks. No fighter
record, roster membership, Academy block, cash, RNG or save envelope is
mutated by the link projection. The Academy Coach, staff-employment and
staff-management regression groups pass **99 tests**; source compilation
and scoped diff checks are clean. No EXE or user save was rebuilt or
modified. Stage 4 remains active with **4 major gates** and **12 named card
areas** unfinished or policy-gated.

**Stage 4 G4/S3 progression-ledger follow-up:** The explicit quarter-close
worker now records every strict qualifying work ID and distinct boundary into
the retained progression envelope before applying a skill gain. This covers
legacy work logs that predate the progression sub-ledger without letting a
reader repair malformed evidence: only executed, paid, progression-eligible
rows with unique IDs, valid lead identity, three distinct months and at least
two targets are considered. The gain history, credited IDs and period list
therefore reconcile after reload, while annual caps and the skill ceiling stay
unchanged. Staff-management regression coverage passes **64 tests** with clean
compilation and diff checks. No EXE or user save was rebuilt or modified. Stage
4 remains active with **4 major gates** and **12 named card areas** unfinished
or policy-gated.

**Stage 4 G4/S4 employment-boundary follow-up:** A two-year deterministic
boundary regression now exercises AI staff expiry and market return across
multiple contract lengths. Each month keeps active and market staff IDs
unique, expiry is retry-safe, the same retained employee returns with the
standard market term, and no stale employment row remains after the boundary.
The staff-employment regression group passes **27 tests** with clean
compilation and diff checks. This is qualification evidence for the existing
employment lifecycle; it does not add automatic replacement hiring or a new
passive staff effect. No EXE or user save was rebuilt or modified. Stage 4
remains active with **4 major gates** and **12 named card areas** unfinished or
policy-gated.

**Stage 4 G0 roster-transition identity follow-up:** Distressed promotion
buyouts now retain and release roster members by stable fighter identity
rather than display name. Two careers that share a name therefore cannot be
accidentally retained together or routed through the wrong free-agent
transition. Legacy id-less rows use only a bounded in-memory object fallback
for this one operation; no synthetic ID is written and the existing belt
vacancy, membership and finance boundaries remain unchanged. Foundation
coverage passes **39 tests** and the complete UI-data group passes **192
tests**, with clean compilation and diff checks. No EXE or user save was
rebuilt or modified. Stage 4 remains active with **4 major gates** and **12
named card areas** unfinished or policy-gated.

**Current acceptance ledger — J6 closed:** The approved v1 Academy coaching
card is now complete. A deliberate hireable Academy Coach route is implemented
with the legacy Trainer fallback, one active cohort per coach, one bounded
quality adjustment, stable retired-fighter career links, expiry/handover
review, explicit reassignment and the comeback boundary. Academy Coach,
Fighter Profile, persistence, Foundation and UI-data checks pass, including
duplicate recruitment and malformed/read-only reader coverage. Historical
ledger entries retain their original counts; the current remaining scope is
**Stage 4 of 6**, with **4 major gates** and **11 named card areas** still
open or policy-gated. The remaining named areas are S3, S4, J1, J4, J5, J7,
J8, A1, A2, A3 and L0. No EXE or user save was rebuilt or modified.

**Current acceptance ledger — S4 closed:** The durable AI employment card is
now complete for the approved lifecycle. Hiring is identity-preserving and
affordability-gated by the six-month no-revenue recurring-cost reserve;
unaffordable or malformed candidates remain in the market, role and
same-month duplicate hiring are blocked, payroll/expiry use the explicit
contract owner, and expired staff return once to the shared market with their
identity intact. The read-only employment ledger, malformed-row diagnostics,
financial-pressure handling and two-year retry-safe boundary coverage pass.
The current scope is **Stage 4 of 6**, with **4 major gates** and **10 named
card areas** still open or policy-gated. The remaining named areas are S3, J1,
J4, J5, J7, J8, A1, A2, A3 and L0. No EXE or user save was rebuilt or
modified.

**Current acceptance ledger — J1 closed:** The approved v1 Explainable MMA
booking-workbench slice is now complete. It provides explicit deterministic
alternatives, current evidence and exact blocker/caution reasons; it keeps
stable fighter and booking identities through refresh/reorder, preserves locked
pairings and TBA slots, and commits only after rechecking medical availability,
date, booking conflicts, rematch cooldown, title-holder/challenger merit and
special-belt ownership. The safe medical draft remains non-binding by design;
firm medical reservations still require the separate policy gate recorded on
the J1 card. Booking-workbench, Foundation, UI-data, compilation and diff
checks are green. The current remaining scope is **Stage 4 of 6**, with **4
major gates** and **9 named card areas** still open or policy-gated. The
remaining named areas are S3, J4, J5, J7, J8, A1, A2, A3 and L0. No EXE or
user save was rebuilt or modified.

**Current acceptance ledger — S3 closed:** The approved v1 Staff specialties,
progression and retention slice is now complete. The central catalogue
explains every known specialty and preserves unknown legacy labels as
descriptive-only; Campaign Coordinator, Contract Administrator and Production
Coordinator apply only their lead-scoped, post-modifier, 2%-capped savings to
the approved cost bases. Progression is earned only from paid, executed,
evidence-backed work across three distinct months and two targets, with stable
work IDs, annual/skill ceilings, duplicate rejection and malformed-evidence
guards. Staff and domain economics suites pass (64 Staff Management, 5
Specialty, Media and Event Economics). Satisfaction/departure probabilities
and negotiation-heat cooling remain explicitly policy-gated. The current
remaining scope is **Stage 4 of 6**, with **4 major gates** and **8 named card
areas** still open or policy-gated. The remaining named areas are J4, J5, J7,
J8, A1, A2, A3 and L0. No EXE or user save was rebuilt or modified.

**Current acceptance ledger — J4 closed:** The approved historical-truth and
company-memory slice is now complete. Fighter History uses only matching
archived opponent evidence or `Not recorded`, pre-bout company/world ranks and
title facts remain immutable, and the append-only membership ledger covers
future roster transitions with stable IDs, reasons and source transactions.
Company Timeline/as-of readers, title-lineage joins, complete membership
totals/paging, malformed-row diagnostics, history export and stable configurable
columns are read-only and preserve explicit incomplete coverage. Foundation,
Fighter Profile and identity/persistence regressions pass (39, 36 and the
identity group). Destructive archive compaction remains a separate policy gate;
no historical data was pruned. The current remaining scope is **Stage 4 of 6**,
with **4 major gates** and **7 named card areas** still open or policy-gated.
The remaining named areas are J5, J7, J8, A1, A2, A3 and L0. No EXE or user
save was rebuilt or modified.

**Stage 4 progress update (J7 acceptance closeout):** The approved v1 company
proposal and ownership-history slice is now complete. Swap and parent/child
proposal snapshots retain stable company and fighter IDs, rank/display facts,
cash/currency, expiry or agreed return boundary, terms, warnings and the full
status/outcome trail in the append-only Foundation ledger. The transfer desk
creates the proposal before board negotiation and carries its ID through
fighter terms; stale ownership, moved fighters, booked fighters, champions,
closed divisions, duplicate-name company references and insufficient cash fail
closed as Needs review without substituting another identity. Child loan,
recall and paid parent-transfer commits use the same explicit proposal evidence,
vacate belts before roster mutation, and write attributed membership, finance,
story and receipt facts exactly once. Time-bounded development loans return at
the agreed weekly boundary, hold behind an already-committed child bout until
the first safe boundary, show the delay in Inbox, and remain save/load safe and
retry-idempotent. Foundation, child-promotion interaction, loan-return and
narrative regressions are green; compilation and diff checks are clean. This
closes J7 for the approved v1 slice. Bilateral treaties, goodwill/acceptance
modifiers and spin-off/acquisition asset allocation remain explicit policy
holds and are not being represented as implemented. Stage 4 of 6 remains
active with **4 major gates** and **6 named card areas** still open or
policy-gated. The remaining named areas are J5, J8, A1, A2, A3 and L0. No EXE
or user save was rebuilt or modified.

**Stage 4 progress update (J8 acceptance closeout):** The approved one-night
tournament-history slice is now complete. Durable Results indexing preserves
stable series/edition/source identities, entrant IDs, original seed and
at-the-time rank snapshots, substitutions, stage and bout references,
champion, terminal status and replay availability without depending on replay
commentary. The history reader is searchable by promotion/text, projects
malformed draw containers as explicit Review required evidence, and never
resolves today's rosters, reruns a draw, changes settlement or writes on open
or refresh. Matchmaking's Tournament Field Review preserves authored seeded
order and exposes a pure same-division/gender alternate pool with identity,
rank and readiness evidence; actual alternate entry remains owned by the
existing weigh-in flow. The focused J8 history/field suite and UI-data suite
pass (201 tests in the combined run), with compilation and diff checks clean.
This closes J8 for the approved one-night slice. Multi-event Grand Prix rules
(carry-over injuries, stage postponement, replacement timing, expired
contracts, advancement on draw/NC and later withdrawals) remain explicit
policy holds and are not represented as implemented. Stage 4 of 6 remains
active with **4 major gates** and **5 named card areas** still open or
policy-gated. The remaining named areas are J5, A1, A2, A3 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 progress update (A1/A2/A3 acceptance closeout):** Three approved
planning and commitment slices are now complete. A1's Owned Calendar indexes
actual MMA, owned-child and Combat Sports schedules by source-bound event and
owner identity, retains participants/reservations and legacy coverage,
supports display-only filters/detail, and never duplicates or executes a
source schedule. A2's super-event lifecycle seals accepted-term mappings,
validates status/revision transitions, records offered/planning/scheduled
expiry and cancellation outcomes with one terminal settlement key, preserves
legacy paid/unpaid/refund uncertainty for manual review, and blocks stale or
malformed closeout before derived effects. A3's cash-runway planner projects
bounded weekly buckets from settlement-aligned components, separates
conditional rights/sponsor estimates, reports capacity-limited break-even,
stores idempotent source-revisioned scenario snapshots and marks changed
inputs stale without applying edits. Owned Calendar, cash-runway,
super-event, event-economics, Foundation and persistence regressions are
green; the focused run passed 4, 17, 19, event-economics, Foundation 39 and
persistence checks respectively, with diff checks clean. Controlled child
scheduling, legacy fee/refund policy, probability claims and new demand
curves remain explicit policy holds. Stage 4 of 6 remains active with **4
major gates** and **2 named card areas** still open or policy-gated. The
remaining named areas are J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 L0 qualification checkpoint:** The current diagnostic infrastructure
is green for the evidence it is designed to prove. The maintained run passed
the smoke test (with only the documented headless Matchmaking coordinate probe
skipped), all **21** play-level-audit/checkpoint regressions, and the seeded
stability playtest for seeds 2201, 2202 and 2203. Checkpoints preserve source
and configuration identity, reject mismatches, retain yearly measurement and
hard-invariant evidence, clean up failed atomic writes, and restore the
caller RNG; the stability run reached Month 4 in each disposable world. This
does not close L0: the plan still requires an authorised current multi-year /
century qualification with preserved raw reports, explicit threshold policy,
all seed/configuration/source identities and any blocking findings. No user
save or EXE was touched.

**Stage 4 G5 follow-up (J5 duplicate case identity):** Drug Testing Cases now
fail closed when a generic detail or workflow lookup encounters more than one
retained row with the same durable `case_id`. The table continues to preserve
both rows with deterministic `case:<id>` / `#2` display keys, while the raw
case envelope stays unchanged and the sanctioned migration boundary remains
the only repair owner. The focused catalogue plus legacy drug-testing suite
passes **28 tests**, with compilation and diff checks clean. This is a
read-model integrity repair only; confirmation, appeals, sanctions, AI
commissioning and sporting consequences remain gated by the unresolved J5
policy tables. Stage 4 of 6 remains active with **4 major gates** and **2
named card areas** still open or policy-gated: J5 and L0. No EXE or user save
was rebuilt or modified.

**Stage 4 L0 live-audit repair and qualification evidence:** The first real
one-year observer run reached its yearly checkpoint and exposed two report
integration defects: live Combat Sports worlds store `events` as an integer
counter rather than a list, and Promotion uses `reputation_score` rather than
the report's assumed `popularity` field. The audit reader now accepts both
counter/list evidence shapes, skips malformed sport rows defensively and uses
the saved reputation score as its bounded display fallback. The same run also
identified that newly generated AI staff-market rows entered without durable
IDs, while spectator handoff intentionally projects the player's staff into
both top-level and promotion-owned views. New market candidates now receive a
deterministic, collision-safe `staff_id`; the invariant scan treats the
spectator projection as one employment record and continues to report true
cross-source collisions. The focused audit/staff suites pass **51 tests**.
The fresh 1-year run then completed with **9,874 fights**, **0 report-accounting
errors**, **0 hard-invariant findings**, a retained checkpoint and no active
save mutation. This is meaningful current-run evidence, but it does not close
L0: the authorised multi-year/century qualification, explicit threshold policy,
and retained cross-seed/source reports are still required. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 explicit-seed contract:** The Simulation Lab play audit now
exposes a bounded seed field. The selected seed is included in the source and
configuration identity, drives the isolated observer RNG, appears in the raw
report, and is part of the checkpoint filename. Resume therefore cannot mix a
checkpoint from another seed with the requested run; the existing default
`260712` path remains compatible. The focused audit suite now passes **24
tests**, including seed/path/identity coverage. This advances the multi-seed
qualification prerequisite but does not claim the authorised multi-year or
century evidence is complete. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 L0 raw-report retention:** A completed or failed play audit now
persists its exact human-readable report beside the seed/year checkpoint using
an atomic replacement. The report path is derived from the same bounded seed
and duration, and the Results action can read it back after the in-memory UI
state has been recreated. The reader is read-only, size-bounded and fails
closed; report persistence failures are disclosed in the in-memory result
rather than mutating the active save. The focused audit suite now passes **25
tests**, including seed-bound report round-trip coverage. This closes the
evidence-retention subtask of L0, but not the authorised multi-year/century
qualification or threshold policy. Stage 4 of 6 remains active with **4 major
gates** and **2 named card areas** still open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

**Stage 4 L0 audit manifest/index:** Each isolated play-audit report now has a
bounded, atomic manifest row keyed by seed, target duration and source/config
identity. The row records completed weeks, terminal status, source and
identity digests, and the paired report/checkpoint paths. Re-running the same
recipe replaces its row instead of duplicating evidence; malformed or absent
manifests read as an explicit empty index and are never repaired by a reader.
This makes retained multi-seed qualification evidence discoverable after UI
rebuilds without relying on in-memory state. The focused audit suite passes
**26 tests**. The authorised multi-year/century runs, threshold policy and
cross-seed qualification remain open, so L0 is not closed. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 evidence-history reader:** Simulation Lab now exposes an Audit
History window backed by the retained manifest. It lists status, seed, target
duration, completed weeks, update time and source/config identity, and opens a
selected raw report in a separate read-only window. Missing, oversized or
malformed evidence remains an explicit unavailable state; selecting or opening
history cannot resume an audit, repair the manifest, rerun the world or change
the active career. The focused audit suite passes **27 tests**, including a
bounded/non-repairing manifest-reader regression. This closes the evidence
discoverability subtask, not the authorised qualification itself. Stage 4 of 6
remains active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 interrupted-run retention:** Yearly checkpoint creation now also
updates the manifest with `paused`, `failed_invariant` or `complete` status, so
an interrupted long run remains discoverable before a terminal raw report is
written. A real disposable two-year run reached its first 48-week boundary
cleanly (`48/96` weeks, one retained yearly snapshot) before being stopped;
the checkpoint and paused manifest row were retained, with no active-career
mutation. Source/configuration binding still prevents that older checkpoint
from being resumed after later source changes, rather than mixing evidence.
This advances interrupted-run evidence but does not close the authorised
multi-year/century qualification or threshold policy. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 current-source one-year qualification:** After the manifest and
interrupted-run changes settled, a fresh seed `260714` completed the full
48-week observer loop against the current source identity. It produced
**9,764 fights**, one yearly boundary row, **0 report-accounting errors**, no
hard-invariant section, a retained raw report, checkpoint and `complete`
manifest row. The report exposes the measured backlog evidence (including two
legacy owner-goal deadlines) rather than hiding it; no automatic repair or
threshold judgement was applied. This is current-source one-year evidence,
not the authorised multi-year/century qualification. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 spectator backlog classification:** The audit measurement now
recognises that player-owned owner objectives are intentionally paused when a
promotion is handed to the AI for spectator mode. Active objectives whose
deadlines pass are reported under `spectator_paused_owner_goals` instead of
being counted as overdue commitments; ordinary player-world measurements keep
the existing overdue-owner-goal evidence. The projection remains read-only and
does not change the calendar worker. The focused audit suite passes **28
tests**, including spectator/non-spectator distinction and no-mutation
coverage. This removes a false qualification signal but does not close L0.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 L0 refreshed current-source evidence:** Following the spectator
backlog classification, fresh seed `260715` completed 48/48 observer weeks
against the new source identity. It produced **10,237 fights**, **0
report-accounting errors**, no hard-invariant findings, zero genuine overdue
commitments and two explicitly paused spectator owner-goal rows. Its raw
report, checkpoint and `complete` manifest row are retained. This is current
one-year evidence only; the authorised multi-year/century run and approved
threshold policy remain open. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 L0 qualification review summary:** Audit History now computes a pure
review summary over retained rows: complete, paused and failed counts, unique
seeds, current-source matches, available raw reports and explicit threshold
policy status. Source comparison is attempted only for valid year-boundary
recipes; malformed or non-year rows remain visible as unknown instead of being
rewritten. The summary is display-only and cannot resume a run, repair a
manifest or alter a career. The focused audit suite passes **29 tests**. L0's
multi-year/century runs and threshold approval remain open. Stage 4 of 6
remains active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 final current-source evidence pass:** With the source frozen after
the qualification-reader work, seed `260716` completed a fresh 48/48-week
observer run: **9,898 fights**, **0 report-accounting errors**, no
hard-invariant findings, zero genuine overdue commitments and two explicitly
paused spectator owner-goal rows. The manifest now contains four retained
seeds (three complete, one paused), three available raw reports and one
current-source match; all rows remain source-bound and readable in Audit
History. The current one-year result is strong evidence, but it does not
replace the authorised multi-year/century qualification or threshold approval.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 L0 current-source two-year qualification:** A fresh seed `260717`
completed the full **96/96-week** isolated spectator observer loop against the
current source identity. The retained report records **20,816 fights**, two
yearly boundary rows with **0 report-accounting errors**, no hard-invariant
findings, zero genuine overdue commitments and three explicitly paused
spectator owner-goal rows. The manifest now holds five source-bound recipes:
four complete rows (including this two-year run) and one retained paused
two-year checkpoint; Audit History exposes the complete raw report and
checkpoint without mutation. This closes L0's current-source multi-year
evidence slice, but not the authorised century/cross-seed qualification or the
explicit threshold-policy approval. Stage 4 of 6 remains active with **4 major
gates** and **2 named card areas** still open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

**Stage 4 L0 cross-seed recipe coverage reader:** Audit History's pure
qualification summary now groups complete current-source recipes by duration
and lists their unique seeds. The reader therefore distinguishes, for example,
one-year coverage from a complete two-year recipe without treating a paused
checkpoint or stale-source row as qualification evidence. It remains
read-only: no report, manifest, save, threshold or simulation state is
rewritten. The focused audit suite passes **30 tests**. Century/cross-seed
qualification beyond the retained recipes and explicit threshold approval
remain open. Stage 4 of 6 remains active with **4 major gates** and **2 named
card areas** still open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

**Stage 4 L0 additional source-bound two-year seed:** After the cross-seed
reader was added, fresh seed `260718` completed **96/96 observer weeks** against
the then-current source digest. The retained report records **21,187 fights**, two
yearly boundary rows with **0 report-accounting errors**, no hard-invariant
findings, zero genuine overdue commitments and three explicitly paused
spectator owner-goal rows. Its raw report, checkpoint and complete manifest row
are source-bound and available in Audit History; the earlier `260717` two-year
row remains retained as a pre-reader historical source and is correctly kept
separate by the current-source grouping. A fresh same-source comparison is
still needed before claiming cross-seed coverage. The authorised century
qualification and explicit threshold-policy approval remain open. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** still open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 interrupted same-source comparison:** A second source-matched
two-year recipe (`260719`) reached its first retained yearly boundary at
**48/96 weeks**. The paused checkpoint and manifest row preserve the isolated
world, RNG state, source/configuration identity and all first-year evidence;
no active career mutation occurred. This is useful interrupted-run evidence,
but it is not counted as a complete cross-seed qualification run until the
remaining boundary is completed or the run is explicitly superseded. The
authorised century qualification and threshold-policy approval remain open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 challenger-only miss guard:** The confirmed Remove Belt action now
fails closed when the recorded miss belongs only to a challenger and no
champion/interim holder is present to vacate. The saved scale/fine evidence,
decision and title snapshot remain intact, while the bout is held as
Needs review with no guessed vacancy or title settlement. Champion, interim,
both-miss and Keep Belt paths remain covered by the existing title-decision
regressions; the challenger-only consequence is still a policy decision for
the full J5 table. The focused J5 decision/provider suites pass **51 tests**.
This closes a rules-integrity gap in the existing slice but does not close J5:
confirmation, appeal, sanction, AI/spectator and full financial/result/title
policy tables remain open. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 J5 replacement identity retention:** Last-Minute Replacement now
retains the deterministic candidate reference for an ID-less legacy fighter in
replacement history and the Foundation operation receipt, alongside the
modern `fighter_id` when one exists. The removed corner also keeps a stable
source reference for retry keys instead of falling back to a visible row
position. Duplicate legacy candidates remain independently selectable and
safe after refresh. The focused replacement/title/provider suites pass
**52 tests**. This closes the legacy-identity acceptance gap in the current
replacement slice, but J5's confirmation, appeal, sanction, AI/spectator and
full policy tables remain open. Stage 4 of 6 remains active with **4 major
gates** and **2 named card areas** still open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

**Stage 4 J5 case identity retention:** Manual screening cases now preserve a
deterministic `fighter_reference` for ID-less legacy fighters and use a
source-order suffix for exact duplicate retained rows. Modern fighter-ID case
hashes remain byte-for-byte compatible, so existing saves keep retry
idempotency. Two duplicate legacy careers sampled under one test ID remain two
distinct cases rather than silently collapsing into one. The focused
J5/provider/replacement/title suites pass **53 tests**. Confirmation, appeals,
sanctions, AI/spectator handling and the remaining policy tables remain open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 legacy replacement resolution:** Title-miss replacement execution
now resolves a newly selected ID-less legacy fighter through its saved fighter
ID when present, or its unique retained name as a compatibility fallback.
Duplicate names remain unresolved rather than redirecting the bout to another
career. The path also keeps the headless compatibility boundary guarded when
the optional Foundation owner is unavailable. The focused
J5/provider/replacement/title suites pass **54 tests**. This closes the
post-commit legacy-resolution gap; confirmation, appeals, sanctions,
AI/spectator handling and the remaining policy tables remain open. Stage 4 of
6 remains active with **4 major gates** and **2 named card areas** still open
or policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 legacy cost projection:** Drug Testing Cases now projects a
retained legacy `cost` field when an older case has no quote envelope, so the
recorded spend remains visible in both the row detail and summary totals.
Malformed values still project as bounded zero/unavailable evidence and the
raw case remains untouched. The focused J5/provider/replacement/title suites
pass **55 tests**. This closes the legacy spend-display gap, while the full
confirmation, appeal, sanction, AI/spectator and policy-table acceptance work
remains open. Stage 4 of 6 remains active with **4 major gates** and **2 named
card areas** still open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

**Stage 4 J5 frozen-contract validation:** New manual testing cases now fail
closed when an unknown provider or policy is supplied, or when a supplied
provider/policy snapshot names a different contract than the case identity.
Valid legacy `Enhanced` policy labels remain compatible, and a missing snapshot
is filled from the selected catalogue entry. This prevents the ledger from
showing a provider, strictness or quote that differs from the frozen case
contract without changing any confirmation, appeal, sanction or sporting
rules. The focused J5/provider/replacement/title suites pass **56 tests**;
compilation and diff checks are clean. This closes a contract-integrity gap in
the current J5 slice, while the full policy-table acceptance work remains open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 ID-less fighter reference correction:** New cases for legacy
fighters without a saved `fighter_id` now retain a blank ID and use the
deterministic `fighter_reference` as the only identity key. Case filtering can
resolve that reference directly, while display names remain presentation-only;
duplicate same-name careers therefore cannot collapse into one case. The
focused J5/provider/replacement/title suites pass **56 tests**, with
compilation and diff checks clean. This closes a legacy identity-field
ambiguity in the current J5 slice; confirmation, appeals, sanctions,
AI/spectator handling and the remaining policy tables remain open. Stage 4 of 6
remains active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 unavailable-contract projection:** Testing Desk configuration and
quote readers now expose an explicit unavailable state when a saved provider or
policy is absent from the current catalogue. They no longer display a baseline
provider or `$0` quote as if it were valid; the raw saved selection remains
untouched and recovery requires the player's explicit catalogue selection.
The provider window uses the same unavailable wording. The focused
J5/provider/replacement/title suites pass **57 tests**, with compilation and
diff checks clean. This closes a malformed-configuration presentation gap in
the current J5 slice; confirmation, appeals, sanctions, AI/spectator handling
and the remaining policy tables remain open. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** still open or policy-gated: J5 and
L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 commission fail-closed boundary:** Manual compatibility testing
now validates the saved provider and policy before calling the sample selector,
charging cash or drawing a result. An unknown saved contract or malformed
testing envelope produces a deferred Inbox explanation and leaves cash, case
state and RNG unchanged; valid legacy `Enhanced` remains supported. The
focused J5/provider/replacement/title suites pass **58 tests** and the wider
J5/foundation/persistence/staff run passes **106 tests**, with compilation and
diff checks clean. This closes a charge-before-rejection acceptance gap in the
current J5 slice; confirmation, appeals, sanctions, AI/spectator handling and
the remaining policy tables remain open. Stage 4 of 6 remains active with **4
major gates** and **2 named card areas** still open or policy-gated: J5 and L0.
No EXE or user save was rebuilt or modified.

**Stage 4 J5 malformed-envelope commission guard:** The manual commission path
now also rejects a non-mapping saved rules envelope before any sample, charge or
RNG operation. Testing Desk quotes and configuration remain bounded and
explicitly unavailable for malformed rules/finance data rather than showing a
default contract. The focused J5/provider/replacement/title suites pass **59
tests**, with compilation and diff checks clean. This closes the malformed
envelope execution gap in the current J5 slice; confirmation, appeals,
sanctions, AI/spectator handling and the remaining policy tables remain open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 reader compatibility verification:** The complete focused J5,
replacement and title set remains green at **59 tests**; the wider
rebooking/Foundation/identity/persistence/Staff compatibility set passes **106
tests**; and the UI-data plus play-audit regression set passes **222 tests**.
These checks confirm the unavailable-contract projection is non-mutating and
does not disturb the existing identity, persistence, or audit readers. This is
verification evidence only and does not resolve J5's confirmation, appeal,
sanction, AI/spectator or policy-table decisions. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** still open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 retained-case protection:** Manual testing now refuses to start
when the saved case collection is non-list or contains malformed rows. This
prevents the explicit commission action from invoking the repair initializer
and dropping legacy evidence before a sample, charge or RNG draw. The raw
envelope remains available for the sanctioned migration/review path. The
focused J5/provider/replacement/title suite remains green at **59 tests**, with
compilation and diff checks clean. Confirmation, appeals, sanctions,
AI/spectator handling and the remaining policy tables remain open. Stage 4 of 6
remains active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 disabled-policy writer boundary:** The durable case writer now
rejects direct case creation under the `Off`/`None` policy, matching the normal
manual commission path's no-sample/no-charge/no-case contract. The retained
state stays unchanged and the focused J5/provider/replacement/title suite
passes **60 tests**, with compilation and diff checks clean. This closes a
direct-writer policy bypass in the current J5 slice; confirmation, appeals,
sanctions, AI/spectator handling and the remaining policy tables remain open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 malformed-case reader projection:** The Testing Cases reader now
detects unknown or cross-wired provider/policy snapshots and malformed quote
envelopes without rewriting them. Such rows display an explicit unavailable
contract, use a review action instead of a baseline provider, and are excluded
from spend totals; valid legacy rows with omitted contract fields remain
readable. Reader health reports the count of unavailable contracts, while the
raw case remains available for migration/audit. The focused
J5/provider/replacement/title suite passes **61 tests**, with compilation and
diff checks clean. This closes a retained-evidence presentation/accounting gap
in the current J5 slice; confirmation, appeals, sanctions, AI/spectator
handling and the remaining policy tables remain open. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 reader regression verification:** The focused J5/provider,
replacement and title suite remains green at **61 tests**; the affected
Testing/Staff/UI reader set passes **292 tests** after the unavailable-contract
projection. Compilation and diff checks are clean. This verifies that malformed
contract evidence is surfaced without mutation and that valid legacy spend
records remain compatible; the full J5 confirmation, appeal, sanction,
AI/spectator and policy-table acceptance work remains open. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 explicit policy-cycle recovery:** The explicit settings action for
Drug Testing now handles both a malformed saved rules envelope and an
unknown legacy policy label without raising an exception. It restores the
documented `Standard` policy only through that user-invoked recovery boundary
and records the change in Inbox; passive readers and manual commissioning
remain non-repairing and fail closed. The focused Drug Testing suites pass
**38 tests**, with compilation and diff checks clean. This closes a settings
crash/recovery gap without choosing any unapproved confirmation, appeal,
sanction, AI/spectator or policy-table values. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** still open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 affected-suite verification:** After the explicit policy-cycle
recovery change, the affected Testing/Staff/UI compatibility set passes **294
tests**. This confirms that the new repair boundary remains isolated from
non-mutating case readers, retained contract evidence, staff projections and
existing UI data contracts. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 L0 source-inventory completeness:** The audit source identity now
includes `views.py` and `drug_testing_catalogue.py`, which own the reader and
Testing Desk contracts used by the current release. A checkpoint made before
either file changes is consequently rejected as stale rather than counted as
current-source evidence. The L0 regression suite passes **31 tests**. This
closes the source-inventory omission, but current-source multi-year/century
qualification, cross-seed evidence and threshold-policy approval remain open.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 focused-suite verification:** The focused provider, replacement,
title-decision and Drug Testing regression set now passes **63 tests** after
the explicit policy-cycle recovery. This confirms the new settings boundary
and the existing identity/title paths together without enabling unapproved
confirmation, appeal, sanction or AI/spectator mechanics. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 empty frozen-contract guard:** Retained rows that contain a
provider or policy ID but an empty frozen snapshot now project an explicit
unavailable contract and a review action. The raw case remains unchanged, and
legacy rows that omit those fields remain readable. The focused
J5/provider/replacement/title suite passes **64 tests**. The current-source
L0 audit was restarted after this source-bound change so its eventual evidence
cannot be mislabelled as current. Stage 4 of 6 remains active with **4 major
gates** and **2 named card areas** still open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

The affected Testing/Staff/UI compatibility set was rerun after this guard and
passes **295 tests**. Stage 4 of 6 remains active with **4 major gates** and
**2 named card areas** still open or policy-gated: J5 and L0. No EXE or user
save was rebuilt or modified.

**Stage 4 L0 current-source checkpoint:** The fresh isolated audit started with
seed **260720** has reached the first yearly boundary at **48/96 weeks**. Its
checkpoint carries the complete 21-file runtime source inventory and the current
source digest `5fe46d42117f8b0d0a18c510516e0f36e52f569a32bf04cb8e816254d9e24b37`;
the retained hard-invariant list is empty. The run remains active for the second
year. This is partial evidence only: it does not yet satisfy the multi-seed,
longer-duration or approved threshold-policy requirements, and it must not be
presented as a completed L0 qualification. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** still open or policy-gated: J5 and
L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 explicit-decision hold:** Dismissing or returning an invalid title
weight-miss prompt no longer defaults to Keep Belt. The recorded scale result,
fine and missed-corner identities are retained with `awaiting_player` status;
preparation returns a read-only pending package and will not simulate, archive,
settle or charge the event until the player chooses Remove Belt, Rebook Fight,
Keep Belt, Cancel Fight or a validated last-minute replacement. Reopening uses
the stored press/weigh-in evidence and does not roll RNG again. The focused
J5/title/replacement/audit set passes **101 tests**, and the wider affected
Staff/UI set passes **357 tests** with compilation and diff checks clean.

**Stage 4 L0 bounded-audit control:** Play-level audits now have a configurable
wall-clock limit (default **300 seconds**, bounded to **30–1,800 seconds** in
the Simulation Lab). A timeout is evaluated only after a completed weekly world
step. The exact world and RNG state are written to a resumable checkpoint;
mid-year stops do not fabricate a yearly snapshot, and reports/manifest rows
identify `time_limit` separately from paused, failed-invariant and complete.
The limit is evidence metadata, not part of source identity, so a player may
resume with a different limit. This keeps L0 evidence honest while allowing
feature work to proceed without another unbounded audit. The prior seed 260720
48/96 checkpoint remains retained as partial historical evidence and is stale
against the current source digest after the J5 change. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 pending-status visibility:** Attempting to settle a card while a
title-miss decision is unresolved now routes the retained reason to the
Results status surface as a warning. Watch and settle paths both remain
non-mutating: no settlement ID, archive row, finance charge, calendar advance
or fight execution can occur until the player commits one of the approved
choices. The focused title/provider/replacement regression set passes **102
tests**; compilation and diff checks remain clean. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** still open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 frozen-settings visibility:** Testing cases now project whether the
current Testing Desk provider or policy differs from the provider/policy frozen
when that case was commissioned. The ledger and case detail show this as
`Current settings differ` while retaining the original quote, evidence and
contract; changing the desk never reruns, recharges or rewrites an existing
case. Missing current settings fail closed as an explicit unavailable status.
The focused J5/provider/replacement/title/audit set passes **103 tests**. Stage
4 of 6 remains active with **4 major gates** and **2 named card areas** still
open or policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 commission approval preview:** The Staff Testing Desk now routes
the manual `Run Drug Tests` action through an explicit review step. Before any
sample, charge or RNG work, the player sees the selected provider and policy,
effective sample count, quoted maximum, staff-discount estimate, projected
cash-after-charge, coverage and all blocking reasons. The preview is a pure
reader and the existing screening action remains the only commit boundary; it
still records preliminary evidence only and cannot create an injury, proven
violation or sanction. The focused J5/provider/replacement/title/audit set
passes **106 tests**. The confirmation step re-reads the contract after the
dialog and rejects a stale provider, policy, quote, cash or roster state
without commissioning. Stage 4 of 6 remains active with **4 major gates** and
**2 named card areas** still open or policy-gated: J5 and L0. No EXE or user
save was rebuilt or modified.

**Stage 4 J5 frozen workflow contract:** Every case workflow projection now
includes a defensive copy of the provider, policy, version, sample-count and
quote terms accepted at commission. Case review can therefore use one stable
historical contract even after current desk settings change; the projection is
read-only and retains malformed raw values for later sanctioned repair. The
Testing Desk catalogue suite passes **31 tests**. Stage 4 of 6 remains active
with **4 major gates** and **2 named card areas** still open or policy-gated:
J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 pending-card discoverability:** Upcoming Cards now projects saved
title-miss decisions onto the card status as `Decision required` or `Review
required`, using the retained participant references and without rerunning
weigh-ins, resolving rankings or mutating the scheduled event. This makes a
save/reload interruption visible before the player attempts Watch or settle.
The UI/data plus focused Testing Desk/title suites pass **238 and 106 tests**
respectively. Stage 4 of 6 remains active with **4 major gates** and **2 named
card areas** still open or policy-gated: J5 and L0. No EXE or user save was
rebuilt or modified.

**Stage 4 J5 central decision read model:** Retained title-miss decisions now
have one source-bound projection for Results, Upcoming Cards and archives. It
preserves stable fighter references, action/status, allowed choices, title-on-
line/vacancy flags, replacement identity, missed-corner evidence and an
explicit legacy-reference marker without inventing a durable fight ID. The
projection is defensive and read-only, and the preparation timeline consumes
the same rows. Title/replacement/preparation coverage passes **31 tests**.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 title-decision review surface:** Upcoming Cards now includes a
read-only **Review Title Decision** action for cards paused at a saved
weigh-in boundary. The managed panel lists each affected bout, recorded
corners, decision/review status, committed action (when present), title state,
replacement identity and the exact permitted choices/reason. It resolves by
the selected event's stable identity and consumes the central title-decision
projection; opening, selecting or closing the panel cannot rerun weigh-ins,
resolve rankings, settle a card or alter the saved event. Headless callers
receive the same pure rows for regression coverage. The focused
title/replacement/preparation suite passes **32 tests** and the affected UI/data
set remains green at **226 tests**. Stage 4 of 6 remains active with **4 major
gates** and **2 named card areas** still open or policy-gated: J5 and L0. No
EXE or user save was rebuilt or modified.

**Stage 4 J5 legacy sanction discoverability:** Upcoming Cards now derives its
decision/review status from the central title-decision projection, with a
defensive fallback for view-only callers. Rows that retain only an explicit
`review_required` sanction envelope are therefore surfaced as **Review
required** after reload instead of appearing ordinary or waiting for the
player to discover the block by attempting Watch/Simulate. Terminal sanctions
remain hidden from the pending status, and the reader leaves the raw event
unchanged. The targeted UI-data/title suite passes **15 tests**. Stage 4 of 6
remains active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 L0 bounded-clock contract:** The play-audit wall-clock decision is
now centralised in a tested monotonic helper. It clamps every supplied limit
through the same 30–1,800 second policy as the Simulation Lab and only reports
the limit reached after a finite elapsed interval; malformed start/clock
metadata fails closed so the weekly loop can retain its exact state rather
than claim a timeout from bad evidence. The audit runner uses this helper at
the existing completed-week boundary, and the L0 regression suite passes **35
tests** without running a long simulation. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** still open or policy-gated: J5 and
L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 archived decision evidence:** The Results preparation reader now
shows the full retained title-miss context alongside the action and title
state: permitted choices, recorded miss amounts and replacement identity when
present, plus the existing reason and status. It consumes the same defensive
projection used by Upcoming Cards and archives, preserves legacy/unavailable
evidence and remains read-only. The focused title/replacement/preparation
suite passes **32 tests**. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 L0 audit budget visibility:** While a bounded play audit advances,
the Simulation Lab status now reports elapsed seconds and the remaining
configured budget alongside the year/week percentage. The display is derived
from the same monotonic clock and clamped limit used by the stop decision; it
does not alter source identity, checkpoint contents or simulation state. The
L0 regression suite passes **36 tests** without running a long simulation.
Stage 4 of 6 remains active with **4 major gates** and **2 named card areas**
still open or policy-gated: J5 and L0. No EXE or user save was rebuilt or
modified.

**Stage 4 J5 stable belt scope:** Title-miss decision snapshots and their
central read model now retain an explicit belt ID when one was saved, plus a
stable title scope for ordinary division belts or named special belts. Legacy
rows use an explicit scope only when it was retained on the fight and otherwise
show it as unavailable; they never infer a historical belt from a fighter's
current division or fabricate a durable belt ID. Upcoming review and archived
Results show the scope with the decision evidence, preserving the scheduled
title join when later rankings, names or roster state change.
Title/replacement/preparation coverage remains green at **32 tests**. Stage 4
of 6 remains active with **4 major gates** and **2 named card areas** still
open or policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 pending title state:** The title-decision projection now
distinguishes a scheduled title awaiting the player's choice from a title that
was finally kept or removed. Upcoming review and archived Results therefore
show **Title scheduled; decision pending** until settlement, instead of
misleadingly reporting **Title not contested** because the sanction envelope
has not been committed. This preserves the original title stakes without
inventing a final outcome. The focused title/replacement/preparation suite
passes **33 tests**. Stage 4 of 6 remains active with **4 major gates** and **2
named card areas** still open or policy-gated: J5 and L0. No EXE or user save
was rebuilt or modified.

**Stage 4 J5 pending-stakes identity:** The saved decision contract now treats
`title`, `divisional_title` and named special-belt stakes as scheduled title
evidence, even when a legacy fight omitted the broad `title` flag. Modern
snapshots carry the stable title scope and explicit belt ID when available;
legacy readers never infer historical scope from a fighter's current division.
The review and archived Results wording therefore remains correct through
pending, kept and removed states. Focused title/replacement/preparation
coverage passes **35 tests**. Stage 4 of 6 remains active with **4 major gates**
and **2 named card areas** still open or policy-gated: J5 and L0. No EXE or
user save was rebuilt or modified.

**Stage 4 J5 replacement rank snapshots:** Last-minute replacement history now
stores a pre-bout ranking envelope for the removed corner, incoming replacement
and retained opponent, including source identity, employer, company/world rank
and capture date. A free agent is explicitly unranked inside the player's
promotion until signed; their world position remains available. The envelope is
captured before the fight slot is mutated and retained alongside the existing
replacement history/receipt, so later Fight History readers can distinguish
the replacement's rank from the removed fighter's original evidence. The
focused replacement/title suite passes **17 tests**. Stage 4 of 6 remains
active with **4 major gates** and **2 named card areas** still open or
policy-gated: J5 and L0. No EXE or user save was rebuilt or modified.

**Stage 4 J5 title-merit parity:** Last-minute replacement eligibility now
uses the complete saved title-stakes test (`title`, `divisional_title` or a
named special belt) for both candidate filtering and commit-time revalidation.
A legacy bout that omitted the broad `title` flag can no longer admit an
unqualified challenger through the emergency dropdown, and its replacement
history records the same explicit title-review requirement. The focused
replacement/title suite passes **17 tests**. Stage 4 of 6 remains active with
**4 major gates** and **2 named card areas** still open or policy-gated: J5 and
L0. No EXE or user save was rebuilt or modified.
