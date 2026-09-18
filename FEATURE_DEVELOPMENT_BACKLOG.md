# MMA Warriors — Feature Development Backlog

## Purpose

This is the current feature-development map for the player-facing game. It is based on the active
Python implementation, regression coverage, the [archived July handoff](docs/archive/2026-09-18/CODEX_HANDOFF.md), and the grounded
`docs\COMPANY_MILESTONES_AND_SUPER_EVENTS_DESIGN.md`. It deliberately excludes fixes already
completed in the comprehensive code review unless they are prerequisites for a feature.

## Current product position

MMA Warriors already has a substantial simulation: player and AI promotions, event booking,
contracts, finance, rankings, awards, tournaments, academies, regional feeders, combat sports,
child promotions, media, world news, chronicle/history, spectator mode, and a persistent inbox.
The next development value is therefore concentrated in completing unfinished flows, making
management decisions more consequential, and improving the long-run calendar experience.

### Current status — approved scope closed; next-work queue executed

The approved first-playable G5 scope is complete. This includes the bounded
Testing Desk/title-decision and replacement evidence, Academy Coach v1, company
proposal and ownership-history v1, one-night tournament history, regional
feasibility/host invitations, spectator pause policies and pinned checkpoints,
editor preflight/conversion, and the source-bound L0 audit with retained
reports/manifests. The focused G5 verification run passes 164 tests and the
maintained regression runner is green. Active confirmation/appeal/sanction
tables, concurrent rights/audience-segment economics, and century-scale
qualification remain separately gated until their rules, calibration and
compatibility evidence are approved; they are not silently treated as
implemented. The approved multi-event Grand Prix and child-scheduling
extension is now implemented and verified, including 4/8/16-person fields,
staged cards, identity-safe replacement/postponement, tournament deciders and
rare AI scheduling.

The bounded 18 September stabilization, regression-evidence, packaging and
delivery-snapshot queue is tracked in
[`docs/LUNA_MAX_NEXT_WORK_PLAN.md`](docs/LUNA_MAX_NEXT_WORK_PLAN.md). Its execution
record is the current engineering handoff. Once that queue is complete, choose a
specific new product outcome or explicitly activate one of its held candidates;
do not restart P1.4, Chronicle export or a product-wide audit by default.

The managed-popup registry and calendar-advance notification aggregation are now implemented. They
should be treated as shared UX infrastructure for the feature work below: new screens must use
`UIMixin.create_managed_window()`, and routine progression output should use the inbox summary rather
than stacking modal dialogs.

## Prioritised action items

### P0 — No currently evidenced feature item

No unbuilt feature found in this audit is presently classified as a data-loss, security, or
production-crash risk. Remaining P0 work should be created only if a new audit finds a release
blocker.

### P1 — High-value player-facing development

#### P1.0 — COMPLETED — Make Combat Sports contracts and cards operational

**Delivered:** Player-owned Boxing, Kickboxing, Muay Thai/Lethwei, Wrestling, and BJJ divisions
now retain ID-first roster and booking links, including duplicate display names. Flagship transfers
use negotiated contracts, per-bout purses affect card costs, expired athletes receive a final renewal
window and then leave, and expired deals cannot be booked. Child cards have separate event numbering
and history from their AI flagship, complete finance metadata, and a one-card-per-month cadence.
Championships, lineage, season records, awards, and Hall of Fame careers are also ID-first; temporary
guest opponents are excluded from those permanent tables.
The player can now schedule a built card for a future month/week, choose production scale and
marketing spend, inspect a settlement-consistent forecast, cancel the booking, and let the weekly
calendar execute it with persistent athlete reservations, results, finance, Inbox, and replay data.
Boxing now uses level-aware six/eight/ten-round matchmaking, 12-round championships, three official
judge cards, and knockdown-led 10-8/10-7 scoring. Muay Thai uses three-round standard and five-round
title formats plus a separate effectiveness hierarchy for kicks, knees, elbows, dumps, balance,
and clinch work; Lethwei retains its five-round knockout-first identity.

**Verification:** `combat_sports_regression_test.py` protects roster and booking identity,
sport-native bout formats and judging, official scorecard evidence, flagship contract creation,
expiry departure, purse settlement, scheduled event timing/economics/cancellation, card cadence,
and circuit-state separation. Future slices should build scouting integration and
cross-promotion competition on this ownership and event foundation.

#### P1.1 — COMPLETED — Put child-promotion cards on the future event calendar

**Delivered:** `open_child_promotion_manager()` now has a Future Child Cards panel where the player
chooses an exact month/week and optional card name. A committed plan is an identity-bound planning
record (`event_id`, `promotion_id`, owner reference, target bout count, status, creation boundary)
stored on the child `Promotion.scheduled_events` list. It is surfaced by the shared Owned Calendar
and Upcoming readers without reserving fighters, assigning camps, spending cash, or drawing RNG at
planning time. One scheduled card per child month is enforced; malformed legacy rows are repaired
only at the sanctioned load boundary with deterministic IDs, while duplicate display names remain
safe through promotion identity.

At the due calendar boundary, the normal AI matchmaking, readiness, medical, title, finance, media,
settlement, replay, and history pipeline runs under the committed event name. The probabilistic AI
show roll cannot skip an explicitly committed card. If readiness, matchmaking, or budget checks fail,
the plan is retained as `Needs replacement` with a reason and Inbox task rather than silently running
a different card; the player can cancel it and choose a later date. Successful cards remove only the
planning row after the archived result is sealed. Cancellation is explicit and resolves by saved
promotion/event IDs.

**Verification:** `child_promotion_interactions_test.py` covers future-date validation, duplicate
month rejection, stable-ID cancellation, and unchanged roster ownership. `child_promotion_long_run_test.py`
continues to cover calendar execution, loans, contracts, child finance, save/load, and archived
events over a multi-week run. `ui_data_regression_test.py` protects the visible planning controls and
identity-bound row map.

#### P1.2 — COMPLETED — Finish the super-event execution loop

**Delivered:** The one-night Grand Prix Showcase path now runs through the ordinary booking and
settlement transaction. Milestone offers carry an immutable accepted-terms snapshot, approval deposit,
setup/security commitments, novelty and revision state. The event builder validates the minimum fight,
title and recognisable-star requirements before scheduling; invalid or stale project copies fail closed.
At settlement, attendance/capacity/profit/excitement evidence determines Success or Failed, the project
is sealed idempotently before popularity, stability, safety, reward and Chronicle effects are applied,
and a durable history row retains payment references, paid/unpaid components and explicit legacy-review
states. Cancellation/expiry leaves the approval deposit governed by the recorded terms and never leaves
a half-scheduled event. Repeated closeout or stale revisions cannot double-charge, refund, or award
effects.

**Verification:** `super_event_closeout_regression_test.py` covers offer identity, transition guards,
terms snapshots, approval, expiry, cancellation, stale-revision handling, malformed settlement evidence,
successful completion, and idempotent terminal history. The ordinary event and tournament suites cover
the Grand Prix card execution and replay path.

#### P1.3 — COMPLETED — Make promotion finance fully auditable

**Historical evidence:** The [archived July handoff](docs/archive/2026-09-18/CODEX_HANDOFF.md) lists finance completeness as follow-up work: weekly history
exists, but some direct cash actions may not yet be recorded as transactions.

**Delivered:** `world.py` now owns a canonical transaction shape for player and AI/child promotion
cash movements. Weekly close reconciles ledger totals to actual cash and writes an explicit,
reference-keyed `Reconciliation` transaction for legacy/direct mutations. Media, career journeys,
combat-sport cards, child transfers/startup/signings/distributions, AI event/overhead/rescue flows,
and direct business actions are covered. Finance and company detail surfaces expose reconciliation
status and weekly history.

**Verification:** `finance_audit_regression_test.py`, `contracts_finance_regression_test.py`,
`media_system_test.py`, `child_promotion_long_run_test.py`, and `stability_test.py` pass against the
implementation. New cash paths must continue to use the canonical helpers and add focused coverage.

**Likely files:** `world.py`, `events.py`, `views.py`, `persistence.py`, child-promotion methods,
`contracts_finance_regression_test.py`.

**Primary files changed:** `world.py`, `media.py`, `views.py`, `persistence.py`,
`finance_audit_regression_test.py`.

#### P1.4 — COMPLETE — Replace remaining routine modal advancement decisions with game-surface workflows

**Historical evidence:** The [archived July handoff](docs/archive/2026-09-18/CODEX_HANDOFF.md) identifies native-dialog cleanup as follow-up work. The recent
advance-notification work handles routine notices, but validation, delete confirmation, academy/
scouting decisions, and some fight-day flows still use Tk message boxes.

**Desired feature:** Use themed inline panels, inbox tasks, or a single decision center for routine
choices; retain modal confirmation only for destructive actions and explicit final approvals. Every
decision should have a clear consequence, cancel path, and save-safe state.

**Delivered first slice:** Due fight-day choices now use a managed themed decision surface with
explicit **Watch Live**, **Simulate Now**, and **Stay on This Week** actions. The card identity is
captured before the panel opens and revalidated before preparation/settlement, so closing or a
stale refresh cannot settle another event. The panel is a reader until an action is chosen and
does not prepare a package, consume RNG, or change the calendar on open. Spectator fast-forward
precondition and empty-result notices now write to the persistent simulation desk instead of
interrupting the player with native dialogs; the action methods return without changing state.

The second slice moves routine Scouting and Academy feedback into their existing workflow surfaces.
Scouting assignment validation now writes to the Target Board/Control Centre status line whenever
that page is built, with native informational fallback retained only for legacy/headless callers.
Academy balance, capacity, showcase, promotion-readiness, network, and empty-history notices now
remain in the managed Academy status/report area; a completed showcase recap is retained there as
well. Scout lead reports open in a managed reader window. Spending, releasing, early-debut, and
other irreversible approvals still use explicit confirmations, and no reader repaint performs a
repair, RNG draw, or gameplay mutation.

Academy alumni history is also a managed, sortable reader rather than a long modal message. It
retains the same graduate, pathway, amateur/pro record, current rating, and title-win facts, with
an explicit unavailable row for malformed retained entries.

Contract review now follows the same rule. Empty selections, batch quote blockers, combat-sport
renewal outcomes, and auto-negotiation summaries are written to the Contracts or Combat Sports
alert strip when the page is present. The batch workbench and ordinary renewal actions still retain
their explicit confirmation/commit boundary; this change only removes routine informational popups
and does not alter a saved term, purse, cash balance, or contract identity.

The roster/division reader now follows the same surface pattern. Missing selections, empty or
already-open divisions, closed-division release outcomes, and successful reopen/close summaries are
written to the themed Roster notice strip. The division manager still keeps an explicit confirmation
for the destructive close action, and fighter release remains confirmation-gated; only routine
feedback moved out of transient dialogs. Notice text includes the affected division or fighter and
the relevant payroll/future-bout consequence so the player can act without losing context.

The Free Agents market also has a persistent action notice. Missing or stale negotiation targets,
invalid purse/cash blockers, and successful signings are reported beside the market controls, while
the negotiation window itself remains the explicit terms-and-commit surface. This keeps a failed
market action recoverable after a refresh and does not change signing, contract, or finance owners.

The scheduler and booked-card editor now keep non-destructive validation in their existing status
surfaces. Past-date, duplicate, already-scheduled, unavailable-fighter, division/rules, TBA,
tournament-field, comparison, and replacement outcomes appear in the Matchmaker's Desk or editor
notice strip with a clear recovery instruction. Adding or staging a bout still uses the ordinary
identity-bound mutation path; the notice layer only changes how the outcome is presented.

The Combat Sports overview now has its own status line for missing sport selections, startup cash
blockers, failed child-division opens, and history-reader navigation. Opening a child promotion still
requires the existing irreversible-cost confirmation; the new line only keeps routine guidance in
the managed overview window.

The Media Desk now keeps campaign and rights decisions in context as well. Strategy changes, campaign
execution results, saved-plan validation/retarget/cancel outcomes, rights offer blockers, counters,
market-review results, renewals, and contract lifecycle feedback are written to dedicated status lines
beside the relevant controls. Refreshing the read-only dashboard no longer hides the last routine
outcome behind a transient dialog. Replacement-deal, paid-review, end-deal, and other irreversible
confirmations remain explicit, and the existing media/finance resolver and identity boundaries are
unchanged.

The context-reader audit also covers transfer, Combat Sports, company archive, career journey and Staff
surfaces. Transfer preflight blockers now return to an available roster/contracts/market notice when
one exists; Combat Sports release results use its contract alert; company archive gaps use the selected
company's next-step card; career-plan validation remains in the journey window; and Staff selection,
busy-assignment, commentator and release outcomes stay beside Staff controls. Staff profiles are now
scrollable managed readers retaining the complete role, specialty, progression, tenure-story and scout
evidence text. All of these are reader/presentation changes: releases, contract endings and other
irreversible commits retain explicit confirmation and stable identity boundaries.

The final receipt/archive slice keeps secondary readers equally recoverable. Settlement-receipt
selection/read failures now appear beside the immutable receipt list, Staff work-receipt gaps stay in
the Staff evidence strip, an absent tournament bracket is reported through Results, and the Fight Night
archive's no-replay state remains visible in its archive detail line. If a committed event's presentation
refresh fails, the saved-result warning is routed to the Results status surface when that page exists.
These paths retain compatibility dialogs only for headless or legacy callers, and none of the changes
rerun settlement, repair retained evidence, consume RNG or alter saved identities.

Company Milestones & Super Events now follows the same presentation rule: an unselected opportunity,
blocked approval, or completed planning cancellation is described in the window's status line. The
approval and cancellation owners, paid/sunk commitment facts, and explicit cancellation confirmation
are unchanged; only routine feedback remains visible beside the project it describes.

Simulation Lab now keeps its own routine guidance too. Missing simulator fighters, stale database
selections, mixed-gender/rules blockers, invalid tournament fields, unavailable sandbox brackets or
tournament nights, and missing play-audit results are written into the simulator result or bracket
report areas. The openweight prompt remains an explicit choice, and sandbox/read-only boundaries are
unchanged; no career data, finance, RNG or saved identity is changed by the status migration.
Play-audit export completion is likewise stated in the managed audit reader instead of a transient
success popup; the exported report remains a copy of the retained evidence and the active career is
untouched.
The Testing Providers & Policy reader also keeps invalid provider/policy selection feedback in its
summary line; the catalogue remains a planning boundary and never enables confirmation, appeal or
sanction mechanics by itself.

Game & Saves now follows the same context-first rule for routine persistence outcomes. Quick-save,
universe selection/clone/validation, backup/restore, database export/import/load, career-start
conversion completion, and missing-selection guidance are written beside the library controls when
the page is present. Overwrite, delete, restore, migration, conversion acceptance and other
destructive or high-impact choices remain explicit confirmations; write failures retain their
error/recovery dialogs. The status helper has a compatibility fallback for headless and legacy
callers, so this is a presentation change only and does not change save paths, atomicity, recovery
copies, active-career switching or database contents.
The universe section editor also keeps successful saves and validation results in its own status
line, while malformed JSON and failed writes remain actionable errors.

The standalone Database Editor now keeps selection guidance, stale-record warnings, required-field
feedback and empty bulk-edit guidance in its header status line. Validation and preflight retain
their detailed diagnostic dialogs where the full finding list matters, while successful checks are
summarised inline. This preserves explicit save/delete confirmations and all source identity and
read-only preflight boundaries.

Company selection and spectator handoff preconditions now follow the same context-first rule. The
Company reader's next-step notice explains missing selection, unavailable promotions, child/feeder
restrictions and already-active spectator state when that page is present; a compatibility dialog
fallback remains for headless/legacy callers. Takeover confirmation and all roster, finance and title
transition owners remain unchanged.

Company Editor repainting now follows the non-mutating reader boundary as well. Belt, interim,
special-belt, rules and broadcast-contract data are projected onto local defensive copies, so a
legacy or malformed envelope cannot be normalised simply by opening the editor. Explicit division,
special-belt, rule and broadcast actions retain their existing write owners.

Game Settings now follows the same boundary: rule, commentary and Fight Night audio values are
displayed from a defensive local projection, with malformed or missing values normalised only when
the player explicitly presses Apply. A cancelled settings visit therefore cannot rewrite the saved
rules envelope. This is a presentation/safety slice; it does not change any setting's gameplay
semantics or audio runtime.

The P1.4 closeout now includes an explicit native-dialog inventory regression. Direct routine
information dialogs are enumerated by module/function/title and must be guarded by the owning page
status surface (or an explicitly documented managed-reader/headless fallback). The regression also
asserts that Fight Day's native three-way prompt is reachable only when the themed decision surface
is unavailable. This keeps future routine popups reviewable while preserving validation errors,
destructive confirmations, final approvals and legacy/headless compatibility dialogs.

**Verification:** `ui_data_regression_test.py` passes 165 tests; the combined UI-data, persistence,
Combat Sports and title-decision bundle passes 195 tests. Source compilation, smoke and seeded
stability evidence remain clean. No EXE or user save was rebuilt or modified.

J11's simulation policy now includes an explicit source revision. New policies capture the current
game revision; automatic spectator fast-forward and Resume fail closed when a saved policy carries
a different revision, before any calendar task or callback starts. A policy from an older save with
no revision remains a compatible legacy policy. Clearing or replacing a stale policy is still an
explicit player action, and ordinary save loading is unaffected. This adds no new stop predicate,
does not run a partial week, and never rewrites a stale policy during the failed resume attempt.

The same compatibility check is enforced at the shared `begin_advance_sequence` scheduling boundary,
so direct or future callers cannot bypass the public spectator guards. The mismatch is rejected before
due-card inspection, job creation, callbacks or Tk scheduling; compatible legacy policies and all
non-spectator advances retain their existing behaviour.

**Verification:** `simulation_pause_policy_regression_test.py` passes 10 tests, including direct
scheduler bypass coverage; the related simulation, persistence, checkpoint and performance bundle
passes 24 tests. The full smoke playtest also passes with the documented headless
Matchmaking-coordinate probe skipped.

The rule-default load projection now preserves the additive `source_revision` field instead of
silently filtering it away. New policies therefore remain bound to the build that armed them after
load/default processing; policies that predate the field receive an empty legacy-compatible value.
This is a load-boundary compatibility repair, not a new stop predicate or an automatic policy rewrite.

**Verification:** `simulation_pause_policy_regression_test.py` passes 12 tests, including saved
revision preservation and legacy projection coverage; the related simulation, persistence, checkpoint
and performance bundle passes 26 tests. The full smoke playtest evidence remains the prior passing
run with the documented headless Matchmaking-coordinate probe skipped.

The persistent simulation-desk reader now fails visibly and safely for stale or malformed policy data:
an explicit revision mismatch is shown as stale with clear recovery actions, while malformed target
values render as unavailable instead of reaching calendar formatting and crashing. The reader remains
pure; valid and legacy-compatible policies keep their existing status text.

**Verification:** `simulation_pause_policy_regression_test.py` passes 14 tests, including stale-status
and malformed-target coverage. Source compilation and `git diff --check` are clean; no EXE or user
save was rebuilt or modified.

J4/G4 membership coverage now includes the central automatic AI free-agent signing owner. It records
the fighter's promotion `join` fact, with a stable transition key and source reason, before changing
the free-agent and promotion rosters. This keeps profile Company Timeline intervals complete for AI
market signings without altering contract economics, story output or RNG behaviour.

**Verification:** `foundation_regression_test.py` passes 33 tests, including the order-sensitive AI
signing hook and durable promotion identity assertion.

J4/G4 signing-boundary completion now extends the same pre-mutation rule to player free-agent
signings, automatic TBA fills, last-minute replacement picks and direct contract negotiations.
Regional feeder negotiations record both the feeder departure and player-company arrival before the
source roster changes, while negotiated swaps remain the single owner for both sides of the transfer.
The post-move narrative signing hook supports a membership-free mode so these paths cannot duplicate
append-only timeline facts. Contract, purse, finance, replacement and negotiation outcomes are
unchanged.

**Verification:** `foundation_regression_test.py` plus `ui_data_regression_test.py` pass 198 tests
together; source compilation and diff checks are clean. No EXE or user save was rebuilt or modified.

The explicit load-boundary repair for an already scheduled fight now records an
ID-linked player-company `join` or `return` fact before moving the fighter out
of the free-agent or retired collection. Retry-safe source keys, raw booking
evidence and fail-closed ambiguous-reference handling are preserved.

**Verification:** The foundation source regression covers this ordering with
the signing routes and continues to pass **33 tests**.

The routine intake audit is now complete for this boundary: AI opening rosters
and depth contracts, rival-academy graduates, academy MMA/feeder graduates, AI
emergency signings, regional wonderkid/proving-ground intake and regional youth
intake all record destination membership before roster insertion or free-agent
removal. The shared narrative signing hook runs afterward without a second
membership write. Selection, contract, finance, development and RNG behaviour
are unchanged.

**Verification:** Source compilation is clean and `foundation_regression_test.py`
passes 33 tests.

The foundation source gates now also assert ordering for every patched intake
owner: AI opening/depth and emergency signings, academy and rival-academy
graduation, regional wonderkid/proving-ground and youth intake, and the central
regional departure helper. The 34-test suite keeps these checks alongside the
runtime AI-signing assertion; no gameplay or RNG path was added.

**Verification update:** The post-change foundation suite passes 34 tests, the
UI-data suite passes 165, and the Combat Sports/persistence pair passes 21.
Compilation and diff checks remain clean; no EXE or user save was rebuilt or
modified.

Player-owned Combat Sports youth/free-agent signings now record their stable
destination-company `join` fact before changing the saved signable pool or
division roster. Cash, contract, sport-employer and ranking behaviour are
unchanged and duplicate membership rows are avoided.

**Verification:** `combat_sports_regression_test.py` and
`persistence_regression_test.py` pass 21 tests.

**Stability verification:** `stability_test.py` passed for seeds 2201, 2202 and
2203, reaching Month 4 with 179, 187 and 180 recorded events and 1, 1 and 2
ordinary retirements respectively. Calendar progression, event recording and
retirement handling remained stable.

**Likely files:** `ui.py`, `views.py`, `events.py`, `world.py`, `persistence.py`.

**Next slice:** keep the inventory as a release gate while moving on to the next source-backed
Stage 4 card. Any new routine selection/progress outcome must add its owning page or Inbox route
and inventory entry; native dialogs remain limited to intentional validation, destructive
confirmation, final approval or headless fallback. Keep destructive releases, deletes and final
financial approvals explicit; do not remove a dialog merely to make a test green.

**Verification checkpoint:** The current reader-boundary work has also passed the seeded stability
playtest across three independent seeds through Month 4, with normal event recording and retirement
handling intact. The closeout audit must preserve this evidence while it classifies any remaining
native dialogs; it must not trade simulation safety for a cosmetic dialog reduction.

#### P1.5 — COMPLETED — Turn the Fighting Academy into a complete youth pathway

**Delivered:** The Academy now supports 4/8/12-week development blocks and reports, tiered amateur
competition, strength of schedule, two-bout tournaments, titles, personality and retention,
save-persistent promises, multiple graduation pathways, regional matching rights, and rival AI
youth programmes that develop cohorts and compete for unsigned leads. The main Academy screen
exposes these workflows and rival-program intelligence without adding a second state owner.

**Verification:** `stability_test.py` covers legacy schema repair, development-block completion,
competition quality, tournament titles and finance, promises, forced at-risk departure, main and
regional graduation, matching rights, rival cohort graduation, duplicate identity and save/load.
It also injects late tournament, graduation, and matching-right failures to prove their cash,
finance, roster, prospect, belt, narrative, and RNG rollback guarantees, and guards rival ratings
against development-time regression. The 100-year audit remains responsible for proving that rival
intake does not overfill the world.

### P2 — Strategic depth and long-run quality

#### P2.1 — COMPLETED — Turn company milestones into a richer management progression

**Delivered:** Finance now projects every milestone's cash gap, event gap and approximate ETA from
the real rolling ledger and event pace while keeping popularity, stability and safety as explicit
non-predictive blockers. Annual profit, 12-month revenue mix and monthly roster/purse trends explain
how the company is moving toward those gates. Milestones unlock eight optional capital projects
across facilities, international operations, staff departments and prestige; each exposes its
purchase price, monthly upkeep, first-year commitment and bounded operational effect.

**Verification:** `player_finance_progression_regression_test.py` covers reporting aggregation,
revenue classification, roster-cost snapshots, milestone projection shape, project eligibility,
single-purchase protection, canonical capital/upkeep entries, event effects, serialization and
Finance-screen population. Super-event execution remains tracked separately in P1.2.

#### P2.2 — COMPLETED TOOLING — Build the source-bound generational audit workflow

**Historical evidence:** The [archived July handoff](docs/archive/2026-09-18/CODEX_HANDOFF.md) records a completed 30-year audit and a future overnight
100-year audit. The project goal is a living world, so three-generation stability is a product
feature requirement, not just a test statistic.

**Delivered:** Simulation Lab now has an explicit **Run 100-Year Audit** action. It runs the
deterministic, isolated spectator-world recipe with source/configuration identity, RNG state,
yearly checkpoints, and no writes to the active career save. Each yearly row now records active
fighters, viable/distressed promotions, free agents, retirees, elite population, cash, title
holders, regional feeders, archive/history size, combat-sport cards, and Academy population.

The qualification pass is pure evidence analysis. It stops the disposable audit for roster or
promotion extinction, multi-year title starvation, runaway average cash, or history growth above
the bounded retention ceiling. Lower free-agent supply and missing regional feeders are reported
as warnings rather than silently tuned. Findings carry a stable code, severity, source path, and
explanation; no repair, RNG draw, or balance change is performed automatically.

**Likely files:** `stability_test.py`, `admin.py`, `world.py`, `seeding.py`, `models.py`,
`child_promotion_long_run_test.py`.

**Verification:** `play_level_audit_regression_test.py` covers defensive yearly measurements,
source-bound checkpoints, read-only qualification, healthy multi-generation samples, and all
extinction/cash/title/history warning and error gates. The Simulation Lab UI exposes both the
configurable play audit and the canonical 100-year shortcut; resumption remains identity- and
RNG-checked.

**Qualification boundary:** “completed” here means the accepted L0 audit capability,
fixtures and source-bound resume/measurement workflow are delivered. It does not claim a
fresh current-source century run has completed or passed. That measured qualification remains
held until its seeds, time budget, thresholds and evidence destination are explicitly approved.

#### P2.3 — COMPLETED — Upgrade the highest-value information surfaces into decision centers

**Evidence:** the handoff calls out Companies, Regions, Personal Assistant, Staff/Scouting, and
Chronicle as the highest-value remaining interactive upgrades; current methods such as
`views.py:open_selected_company_hub()`, `open_selected_region_hub()`, `open_selected_assistant_notice()`,
`open_selected_staff_profile()`, and `open_world_chronicle()` are established surfaces to extend.

**Desired feature:** Each surface should answer “what changed, why it matters, and what can I do
next?” with linked actions, stale-data-safe refreshes, and no duplicate popup windows.

**Delivered first slice:** Industry Standings now includes a **NEXT STEP** card below the selected
company profile. It explains the current operating priority (card, finance, roster depth, or
strategic review) and provides two links into the existing management surfaces. The links retain
the standings row's stable company identity and revalidate it before opening, so a refresh or
duplicate display name cannot route the player into another promotion's workflow. The existing
Personal Assistant KPI/decision queue remains the shared notification registry and now complements
these company-specific actions.

The Regions page now uses the same pattern: it explains whether local pairings, scheduled shows,
or gym depth are the current constraint and provides identity-bound Feasibility, Fighters, Gyms,
or Region Hub actions. A malformed or unavailable region remains a disabled reader state, and
opening any card does not repair region data, book a show, reserve a fighter, or consume RNG.

The Staff desk now has a matching **NEXT STEP** card. It prioritises expiring contracts, retained
evidence/policy exceptions, uncovered specialist roles, and empty or active department briefs in
that order. Its links only open the existing expiry, roster, brief, scouting, or evidence readers;
the source projection is rechecked (saved staff IDs where available, deterministic legacy
fingerprints otherwise) before opening, so a refresh cannot redirect the player to another
employee or policy revision. The card is fully observational: it never negotiates, hires, fires,
commits a brief, spends cash, or grants staff authority.

Scouting's Target Board now has the same evidence-led card. It prioritises visible recommended
signings, stale reports, active assignments, and saved decision packs, then opens the matching
target, assignment, or pack reader. The visible target/assignment/pack IDs form the source key and
are checked again before selection, so page changes cannot send the player to a different fighter
or dossier. The card never commissions a report, changes a shortlist, negotiates, or signs.

The World Hub now connects its selected promotion, story, and gym context through a matching card.
It recommends the latest story reader, company context, Chronicle, gym profile, or Scouting page
based on the selected source and keeps every link read-only. Promotion, story, and gym row keys are
rechecked before opening, so sorting or a refresh cannot redirect the player to another company,
story, or facility.

The Promoter Dashboard's selected-decision detail now separates the recorded notice from its
consequence and destination. It labels the priority, explains why the issue matters (booking,
contracts, runway, scouting, medical, or career context), and keeps the existing source-bound
Open Context action. Selecting or repainting a notice remains a reader operation; no notice is
resolved, marked complete, or mutated by the detail panel.

**Verification:** `ui_data_regression_test.py` covers the Company, Region, Staff, Scouting,
World Hub, and Promoter Dashboard decision-center wiring. The linked readers revalidate their
source-bound identities before opening, tolerate malformed/legacy rows through existing defensive
projections, and remain read-only until the player enters an explicit workflow action.

#### P2.4 — COMPLETED — Normalize legacy save data during an explicit migration

**Delivered:** Game & Saves now exposes an explicit **Migrate Profiles** action for a selected save
slot. The preflight is a pure deep-copy projection that walks player, AI promotion, retired, and
combat-sport fighter rows and normalizes only authored legacy career-arc labels (`Standard Prime`,
`Early Peak`, `Late Developer`, and `Long Prime`) to the current four-name catalogue. Unknown labels
and healthy values remain unchanged, and every changed source path is shown before confirmation.

The write boundary refuses to proceed unless a rolling recovery snapshot is created first, writes the
versioned migration metadata into `_save_meta`, preserves split replay blocks through the normal
atomic writer, and reloads the active career when the selected slot is the active one. A no-op
healthy slot is not rewritten. The action is intentionally separate from ordinary load so opening or
refreshing Game & Saves never normalizes data as a side effect.

**Verification:** `persistence_regression_test.py` covers non-destructive nested migration, unknown
value preservation, source-path audit rows, and the save-menu action state; `ui_data_regression_test.py`
covers the visible migration control and explicit handler wiring.

### P3 — Content and polish after the above systems stabilize

- Expand super-event venue and ceremonial content only after the first executable format is stable.
- Add more regional identities, media voices, academy personality/challenge variants, and crowd/audio variants as
  data-driven content rather than new mechanics.
- Continue replacing static detail panels with linked profiles, filters, and clear empty states.
- Add player-facing export/share views for company history and the Chronicle once the underlying
  history data is fully reconciled. **Chronicle slice delivered:** World Chronicle now exports the
  current filtered, read-only projection as JSON or a readable text report through an explicit save
  dialog, preserving unavailable/legacy status labels and source facts. Export failures stay in the
  Chronicle footer and do not open a second modal or alter the retained history.
- **Fighter Search slice delivered:** profile and compare actions now report missing selections beside
  the page controls, preserving the 100-row identity-bound reader and Scouting Mode visibility rules.
  Search refresh, profile open, and comparison remain read-only operations over the saved world.
- **World Editor slice delivered:** routine fighter-editor guidance (missing name/employer, duplicate
  identity, missing selection and detailed-sheet access) now stays in the current-career header. Save,
  retirement and detailed-rating outcomes identify the affected fighter and remind the player that the
  career save is pending. Explicit retire approval, malformed-value errors and all title/membership
  mutation safeguards remain unchanged.
- **Gym viewer integrity slice delivered:** opening a gym profile now consumes the synchronized membership
  projection without recalculating counts or first-week capacity. Calendar advancement and explicit roster/
  mutation paths remain the write boundaries, keeping profile refreshes read-only.
- **Comeback membership boundary delivered:** a retired fighter returning through a player-approved comeback
  contract now records an ID-linked `return` fact before leaving the retired collection or re-entering the roster.
  The stable transaction key makes retries idempotent while preserving all contract, finance, retirement and RNG
  behaviour; the Foundation source gate covers the ordering.
- **Combat Sports release boundary delivered:** releasing a player-owned sport athlete now records both sides of
  the transition before updating saved division roster IDs or booked-bout projections. Title vacating remains first;
  the release and flagship return preserve the existing ranking, contract and RNG behaviour.
- **Staff progression malformed-baseline guard delivered:** quarterly qualification now validates the saved skill
  before consuming the quarter. A malformed legacy skill is left for explicit repair without crashing or losing the
  earned evidence; valid caps and gains retain the existing annual/80-point limits and idempotency.
- **AI Staff hire identity/term boundary delivered:** explicit AI employment now normalises salary and term,
  stamps the current contract dates, and suffixes duplicate saved staff IDs deterministically. Missing IDs use a
  retained-field fingerprint; affordability and role/runway policy remain unchanged.
- **Cash-runway malformed-finance guard delivered:** the read-only forecast now uses bounded fallbacks for malformed
  production, medical, testing, sponsorship, rights, rate, academy and tier/capacity inputs. It preserves the raw
  finance envelope, scheduled cards, cash and RNG state; the focused cash-runway suite covers nested/scalar legacy
  corruption without changing the planning contract.
- **Revenue-mix history reader hardened:** malformed archive, weekly-history and transaction rows are skipped as
  unavailable while valid ticket, broadcast, sponsorship, merchandise and non-event revenue remain separated. The
  reader preserves duplicate-ID filtering and never rewrites retained finance or archive data.
- **AI-upgrade rollback timeline guard delivered:** when a replacement signing fails after the incumbent is moved to
  free agency, the rollback now records a stable `return` fact before restoring the incumbent to the promotion.
  The append-only timeline therefore reflects the transient leave/return without changing selection, affordability,
  finance or RNG behaviour.
- **Owned-calendar date projection hardened:** the read-only calendar now bounds malformed current/event dates and
  reports partial coverage for invalid saved values, while preserving stable event/owner identities and leaving
  schedules, reservations, finance and RNG untouched.
- **Cash-runway break-even evidence delivered:** each committed-card quote now reports the gate-plus-merchandise
  attendance needed to cover its committed cost only when venue capacity can reach it. Conditional rights and sponsor
  receipts remain excluded and are shown separately; saved scenario details expose the same read-only evidence.
- **Cash-runway snapshot identity completed:** scenario freshness now fingerprints cash, company/staff/academy cost
  sources, rules, event venue/region/tier/broadcaster, super-event terms and stable participant facts. Any material
  source change marks the retained snapshot stale without resolving fighters, rerunning settlement or rewriting it.
- **Staff reader non-finite guard delivered:** staff skill, contract-term, contract-target, offer-score and warning
  projections now fail closed for `Infinity`/`NaN` and other malformed numeric legacy values. The retained staff row
  stays byte-for-byte unchanged, uncertain terms remain expired for access checks, and explicit contract mutation
  paths keep their existing validation boundary.
- **Staff lead projection guard delivered:** morale-adjusted lead selection and specialty-saving read models now
  treat non-finite skill, morale and subtotal inputs as bounded unavailable values. A malformed row cannot win a lead
  comparison through `Infinity`/`NaN`, and cost-note readers return a safe zero without rewriting the staff record.
- **Staff capability/evidence audit guard delivered:** capability, employment-audit and progression read models now
  surface non-finite salary, contract, morale and work values as invalid evidence while retaining stable staff IDs
  and leaving the save untouched.
- **Media Rights non-finite reader guard delivered:** contract eligibility, renewal/terminal history, terms and event
  outcome quote readers now bound `Infinity`/`NaN` and malformed values to zero or `Needs review`, preserving fee
  alias truth and retained contracts without extra RNG or settlement work.
- **Sponsor preview non-finite guard delivered:** activation previews, offer assessments and fee readers now bound
  malformed trust, stability, fee, fit, term and conduct values while keeping contracted maximums separate from the
  current full/half-fee estimate and leaving saved offers/deals untouched.
- **Testing Desk quote guard delivered:** provider/policy planning quotes now bound malformed or non-finite base
  costs, sample counts and authored multipliers without spending, drawing RNG or changing the live screening policy.
- **Regional Feasibility reader guard delivered:** malformed retained invitations,
  snapshots, dates, counts and scheduled rows now fail closed in the read-only
  review panel. Empty/unavailable evidence is explicit, stable venue text is
  preserved, and the reader cannot repair state, book a fight, spend cash or
  consume RNG.
- **Combat Sports history reader guard delivered:** Circuit Records & History
  now bounds malformed world/division containers, non-finite amounts and dates,
  and wrong-type rows while retaining explicit unavailable evidence. The
  `repair=False` projection remains read-only and cannot migrate titles,
  rankings, finance, events or RNG during refresh/open.
- **Regions profile reader guard delivered:** Region profile and next-step
  projections now bound non-finite indicators and pairing counts, filter
  malformed scheduled-event rows, and preserve explicit unavailable states.
  Refresh remains read-only and cannot repair region data, generate invitations,
  book events, spend cash or consume RNG.
- **Company standings projection guard delivered:** Rankings and Combat Sports
  company-power read models now bound malformed/non-finite roster ratings,
  reputation, stability, cash and champion values. Invalid rows cannot crash or
  win a comparison through `Infinity`/`NaN`; valid standings remain unchanged
  and the presentation path stays non-repairing and RNG-free. Non-mapping
  circuit/child-division envelopes are now rejected before field access.
- **Owner-goal projection guard delivered:** Inbox/Goals readers now bound
  malformed or non-finite objective metrics, targets, deadlines, baselines and
  duration values through one non-mutating helper. Invalid evidence remains
  visible without writing observations or outcomes; calendar workers retain the
  only owner-goal mutation boundary.
- **Drug Testing Cases reader guard delivered:** compliance-case summaries and
  workflow rows now bound malformed/non-finite sample counts and quote totals to
  explicit unavailable zero evidence while preserving case IDs and raw rows.
  Opening/filtering remains observational and cannot commission testing, spend,
  sanction or draw RNG.
- **Regional Prospects baseline guard delivered:** the non-repairing candidate
  assessment now treats malformed/non-finite saved history baselines as bounded
  zero evidence without rewriting fighters or feeder promotions. Eligibility,
  scouting visibility and identity-bound row actions retain their existing
  behaviour for valid records.
- **Inbox reader guard delivered:** display copies and action classification now
  bound malformed/non-finite message dates and contract terms without rewriting
  the retained inbox. Stable source identities, filters and explicit mail
  actions remain unchanged.
- **Event Log reader guard delivered:** malformed retained log collections now
  render an explicit load/migration review state instead of iterating arbitrary
  values. Valid log lines remain complete and ordered with semantic styling,
  scroll restoration and read-only behaviour preserved.
- **Staff capability action-ID parity delivered:** the capability read model
  now exposes safe read-action IDs separately from friendly labels. The Staff
  grid and selected-department detail show those stable IDs, while mutating
  actions remain excluded from recommendation scope. This keeps saved brief
  allow-lists, calendar-worker authority and the visible policy contract aligned.
- **Staff guardrail input boundary delivered:** budget, action-ceiling and
  department-brief quote paths fail closed for non-finite or overflow-sized
  amounts, returning validation/zero planning evidence without changing policy
  state or raising from a player-entered value.
- **Selected Combat Sports profile guard delivered:** malformed world/division
  envelopes now render an explicit unavailable company profile, while valid
  roster, title, event-history and finance projections use bounded read-only
  values. Profile switching cannot repair circuit state or consume RNG.
- **Finance reader overflow guard delivered:** Finance, History & Outlook and
  Cash Runway readers now catch overflow-sized legacy values and reject
  non-finite tax rates while preserving raw finance/history data and explicit
  mutation boundaries.
- **Game & Saves reader boundary delivered:** library refresh and selected-save
  summaries enumerate existing paths without creating Save/Database folders or
  active-slot state. Explicit save, copy, migration and database actions retain
  their write boundaries.
- **Combat Sports overview reader guard delivered:** malformed world/division
  containers now render safe unavailable rows and detail cards, with bounded
  circuit values and `repair=False` projection preserved for refresh/open.
- **Staff collection reader guard delivered:** Staff roster, candidate and
  expiry tables now project only list/tuple collections, so malformed legacy
  containers render an empty presentation without changing retained employment
  evidence or routing actions by row position. Effect summaries use the same
  safe projection; evidence-audit spend and revision readers also fail closed
  for overflow-sized values.
- **Combat Sports contract reader boundary delivered:** child-division
  membership is projected with `repair=False` during refresh, preserving the
  saved division while still resolving legacy names to stable fighter IDs.
  Malformed containers and non-finite month/purse values fail closed, and
  explicit sign/release/calendar owners retain the repairing path.
- **J5 durable testing-case lifecycle envelope delivered:** new compliance
  cases retain optional event identity and a defensive event reference plus
  explicit confirmation, appeal, provisional-restriction, sanction and final-
  resolution containers. The cases reader exposes stable lifecycle statuses
  and counts without repairing legacy rows, commissioning tests, spending
  cash, applying sanctions or consuming RNG. Confirmation/appeal/sanction
  mechanics remain policy-gated; the compatibility screening resolver and
  established `sanction_status` evidence are unchanged.
- **Fight History opponent-record evidence guard delivered:** archived
  snapshots are now accepted only when the opponent is identified by stable
  ID or exact archived name. A replay with no frozen opponent record shows
  `Not recorded` instead of a current mutable record or an ambiguous same-date
  snapshot; unidentified legacy rows retain their explicit `-` state.
- **Testing Cases evidence context delivered:** the case detail reader now
  shows event scope/source and a compact confirmation, appeal, restriction and
  sanction status summary beside the frozen test facts. It uses bounded
  read-model totals for malformed quotes and remains fully observational; no
  provider commission, sanction, cash change or RNG draw is added.
- **Contract-batch quote projection guard delivered:** renewal workbench
  planning now bounds malformed/non-finite purse, popularity, momentum, age,
  term and cash facts. Invalid values remain safe planning evidence without
  negotiations, spending, RNG or contract mutation; valid identity, ordering
  and partial-result behaviour is unchanged.
- **Company Proposal Ledger cash guard delivered:** malformed or non-finite
  retained cash terms now render as bounded zero evidence in table/detail
  projections. Proposal IDs and outcomes remain source-bound and the ledger
  reader stays append-only, non-repairing and RNG-free.
- **Storylines non-finite evidence guard delivered:** infinity, NaN and
  overflow-sized retained values in story importance, dates and promotion
  scoreboards now fail closed to bounded display values with a **Needs review**
  marker. The reader preserves authored beats, stable IDs and raw save data;
  opening or filtering it performs no repair, RNG draw or state mutation.
  Non-finite fallback dates are bounded as well, so a bad `started_month`
  cannot escape through a missing update date.
  Profile storyline queries and headless Followed Briefings use the same safe
  boundary, preserving source objects while preventing malformed dates from
  crashing filtering, sorting or calendar conversion.
- **Media desk numeric reader guard delivered:** dashboard, receipt and
  campaign-detail projections now fail closed on overflow-sized retained values
  (including non-finite action usage, receipt amounts, heat and cost) without
  changing offers, contracts, cash, RNG or campaign history.
  Settled-receipt detail applies the same bounded projection to rights, sponsor,
  total and relationship values, keeping malformed immutable evidence reviewable.
- **World Chronicle overflow guard delivered:** non-finite/overflow page limits
  and chronology dates now fail closed to bounded display evidence and
  `Date unavailable`/`Needs review`, preserving authored text, source identities
  and the raw archive without reader repair or mutation.
- **Profile Fight History academy-date guard delivered:** malformed or
  non-iterable amateur history envelopes now project to a safe empty ledger,
  while finite academy month/week values are bounded for display (negative
  months and impossible weeks cannot crash the formatter). Raw amateur rows,
  professional history, replay identity and the existing no-repair reader
  boundary are preserved.
- Professional Fight History uses the same container guard: a malformed saved
  `fight_history` value cannot be sliced as text or raise while the profile
  opens. Valid archived rows, replay identity and the explicit empty-history
  state remain unchanged.
- **Owned child-card schedule reader guard delivered:** a malformed
  `scheduled_events` envelope now projects to an empty display list, while
  retained month/week values are finite-checked and bounded before sort/date
  formatting. Event IDs and the explicit schedule/cancel handlers remain
  source-bound; opening the manager does not repair or reorder saved cards.
- Storyline list limits now fail closed for overflow-sized values as well as
  malformed types, remaining bounded to the authored maximum without changing
  the retained story collection.
- **AI Staff employment ledger guard delivered:** the read-only employment and
  market ledger now bounds overflow-sized limits and malformed salary, term,
  skill and morale values. Stable staff/promotion IDs and duplicate suffixes
  remain intact; the reader still cannot hire, expire, repair, spend or draw
  RNG.
- **Talent Relations case-reader guard delivered:** malformed/non-finite review
  and history boundaries now project to bounded zero evidence without changing
  case IDs, source obligations, history or the retained case shelf. Explicit
  acknowledgement/action/review handlers remain the only write boundary.
- The AI Staff employment ledger now also fails closed for malformed promotion,
  staff and market collection envelopes, preserving the raw source while
  returning an explicit empty read-model.
- Talent Relations evidence-reference and obligation collections are now
  type-checked, preventing malformed strings from becoming character entries
  in case details while preserving the raw case.
- Direct Talent Relations case-detail reads apply the same guard and bound the
  review month, so callers cannot bypass safety by passing a raw case row.
- **Title-miss resume evidence guard delivered:** non-finite or overflow-sized
  saved miss amounts now fail closed to the existing `needs_review` state while
  preserving the recorded fine and preventing a second scale roll, prompt,
  title mutation or RNG draw.
- Managed Staff Profile readers now bound malformed salary, tenure-story score
  and reputation values, preserving selected identity and retained source rows
  while showing safe/unknown evidence.
- The AI Staff Ledger window now skips malformed affordability snapshots and
  bounds cash, payroll and runway display values (including NaN/Infinity)
  without refreshing offers, hiring, expiry or retained employment data.
- Company hub Next Step cards now fail closed on malformed roster/event
  collections and non-finite cash/stability evidence while preserving the
  identity-bound selection and read-only company data.
- Managed Company Hub detail tabs now project complete fighter rows before
  sorting or rendering, showing an explicit unavailable-evidence notice for
  malformed roster entries without mutating the retained roster.
- Selected-company read models now defensively project MMA roster, finance,
  belt, staff and numeric summary envelopes before profile or hub rendering.
- Regional Prospects throughput/backlog readers now fail closed on malformed
  promotion, roster, free-agent and cached-count envelopes without rewriting
  the monthly eligibility cache.
- Regional Prospects candidate assessments now bound malformed/non-finite fighter
  values and missing promotion identity, preserving the non-repairing reader
  boundary while returning safe eligibility, win-rate and development labels.
- Upcoming Cards broadcaster status now renders malformed provider/rights data
  safely instead of crashing or repairing the saved finance envelope.
- Finance history table/detail readers now bound malformed month/week values
  before calendar formatting while retaining the raw identity-bound row.
- Staff display projections now clamp non-finite/oversized skill, morale and
  salary values while preserving malformed employment rows as review evidence.
- Media Desk dashboard, receipt and campaign readers now bound malformed or
  non-finite retained amounts without repairing finance evidence.
- The active media campaign-plan summary now treats malformed quote/detail
  payloads, completion ledgers and revision values as bounded display evidence;
  opening the plan editor cannot crash or rewrite the saved plan.
- Media settlement receipt details now match audience evidence by saved
  contract/outlet identity before using an event-only legacy fallback, keeping
  duplicate outlet names or repeated event labels from cross-linking records.
- Game & Saves selected-save details now fail closed on malformed or
  overflow-sized month/week metadata, showing an unavailable date without
  creating directories, normalising the save or changing selection identity.
- Game & Saves autosave/backup counters now enumerate with non-creating path
  helpers; refreshing the library no longer creates an active slot or recovery
  folders as a side effect.
- Foundation membership history readers now bound malformed paging, as-of and
  result-limit inputs, preserving the append-only envelope and avoiding crashes
  or unbounded profile slices during refresh.
- Regions profile/team readers now tolerate malformed gym, promotion and
  specialty rows with finite bounded sort keys and no refresh-time mutation.
- World Hub promotion/gym repaint now bounds malformed numeric, date, capacity
  and specialty fields while preserving stable selection and no membership
  synchronization on refresh.
- Fighter Search now projects malformed source collections and record-history
  fields safely while preserving 200-ms debounce, 100-row paging and identity
  selection restoration.
- Results archive/detail readers now bound malformed dates and play-by-play
  containers while retaining explicit unavailable rows and source identities.
- The full UI-data regression suite is green at **182 tests** after these reader
  hardening slices, and the smoke playtest remains green.
- The maintained `run_regression_suite.py` now completes with
  `ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`, covering Fight Night,
  traits/profile/persistence, UI-data, Media/Staff/finance, scouting/regional,
  Combat Sports, identity, audio/window lifecycle, fight-engine calibration,
  full-system, database-editor and stability checks. The expected headless
  Matchmaking coordinate probe is still skipped; no EXE or user save was
  rebuilt or modified. Stage 4 remains active with four major gates and twelve
  named card areas unfinished or policy-gated.
- Matchmaking's stacked laptop layout now reserves a 720px scrollable workspace,
  a 520px fighter explorer and a compact draft-card pane so the filter/action
  header and at least four fighter rows remain readable. Side-by-side mode
  restores its previous 620px workspace. The new layout check and full UI-data
  suite pass **183 tests**; smoke remains green with the expected headless
  coordinate probe skipped. No EXE or user save was rebuilt or modified.
- Company milestone outlooks now clamp non-finite/overflow finance and history
  values before computing gaps and ETA, without repairing retained envelopes.
- Pending title-miss fine totals now use a finite bounded projection as well,
  preventing malformed evidence from becoming an unbounded purse debit during
  resume; no fresh weigh-in is used to repair it.
- Remove Belt now routes both primary and interim holders through canonical
  belt-vacancy lineage, preventing a stale interim flag or belt-map entry while
  keeping the title-on-the-line sanction snapshot explicit.

## Recommended sequence

1. Use the finite queue and live execution record in
   [`docs/LUNA_MAX_NEXT_WORK_PLAN.md`](docs/LUNA_MAX_NEXT_WORK_PLAN.md) for the
   current stabilization/delivery pass. Do not reopen its DONE cards without a
   reproduced regression or changed dependency.
2. After that queue is complete, select one concrete player outcome or explicitly
   activate one held candidate. Chronicle export is already delivered; “exports”
   alone is not a missing feature specification.
3. Run a current-source century qualification only as an explicitly scoped
   validation exercise with agreed seeds, duration, thresholds and output paths.
   Do not treat the delivered P2.2/L0 tooling as a historical century pass.

P1.4 remains complete and its dialog inventory remains a regression gate, not the
first step of another audit. This sequence preserves the calendar and money
contracts while keeping completed work closed.

## Already completed foundation relevant to this backlog

- Historical fight-selection fixtures remain reproducible after development-loan
  fields were added: only untouched zero return boundaries are omitted by the
  compatibility adapter, and populated/malformed values fail closed.
- Database-editor acceptance coverage binds each field operation to the saved
  fighter/company identity, keeping sorted or filtered rows from retargeting a
  test action through a stale visible index.

- Central managed-popup lifecycle in `ui.py` with runtime call-site migration across the main
  application modules.
- One aggregated Inbox/news summary for routine calendar-advance notices.
- Child-promotion ownership, loan, transfer, closed-division, empty-launch, and repair safeguards.
- Persistent achievement/milestone and super-event offer scaffolding.
- Isolated regression runner, long-run child-promotion coverage, and build-toolchain verification.
- Canonical finance transactions, weekly cash reconciliation, repair entries, and reconciliation
  status in player and promotion finance surfaces.
- Per-event ticket pricing, marketing spend, production tiers, and identity-safe grudge economics,
  with legacy scheduled-card defaults and focused save/load coverage.
- Academy showcase-card and alumni readers now preserve stable saved identities
  and keep malformed retained rows visible as unavailable evidence. Replay,
  graduate-profile and matching-right actions fail closed for those rows, while
  the source archive remains untouched. UI-data coverage is green at **184
  tests**; combined Academy/profile/UI checks are **217**, with smoke green and
  no EXE or user save rebuilt.
- Scouting Target Board refresh now clears all selected-target cards when
  filtering or paging removes the prior source-bound fighter, covering Tk
  versions that do not emit a selection event on row deletion. Identity,
  scouting reports and shortlist state remain read-only during repaint; the
  UI-data suite remains green at **184 tests**.
- Selected-target advice cards now use the active semantic palette, keeping
  recommendation, monitor and pass colours readable across theme changes while
  preserving the underlying scouting text and data.
- The Target Board legend now stores semantic keys on its native labels, so
  recommend/monitor/pass/shortlist/stale swatches retheme correctly without
  rewriting scouting state.
- Profile Overview now bounds malformed/non-finite momentum, morale, fatigue,
  activity, camp-week and skill values in a pure reader helper. Readiness stays
  fatigue-inverted, momentum remains centred on 50, scouting visibility is
  unchanged, and the profile regression passes **30 tests**.
- Profile comparison rows now use saved fighter IDs (or deterministic legacy
  fingerprints) with duplicate-safe suffixes, and query refresh restores or
  clears selection by source identity rather than mutable row position. The
  comparison chooser remains read-only and the profile regression covers both
  durable and ID-less legacy fighters (**31 tests**).
- Development tab evidence now uses a bounded, non-repairing projection for
  scores, drivers and retained camp/development chronicles. Malformed rows are
  shown as unavailable evidence, while stored change order and one signed
  driver scale remain intact (**32 profile tests; 184 UI-data tests**).
- Company & Title History malformed rows now use deterministic retained-content
  fingerprints (with duplicate-safe suffixes) instead of visible ordinals, so
  paging/sorting cannot retarget a history row.
- The legacy Academy Alumni dialog now uses the same saved-ID or deterministic
  fingerprint contract as the main Academy page, retaining unavailable rows
  without mutable index targets.
- Region Hub now routes through the defensive non-repairing region projection;
  malformed profiles and child rows remain visibly unavailable/safe without
  repairing regions or mutating roster, calendar, finance, memberships or RNG.
- Company Proposal Ledger ID-less legacy rows now use deterministic retained
  content/type fingerprints (with duplicate-safe suffixes), preserving the
  append-only reader's source binding across filter and sort refreshes.
- Storylines and World Chronicle legacy rows now use deterministic evidence/type
  identities even when participant or headline data is missing; empty/opaque
  rows remain unavailable and cannot fall back to mutable list positions.
- Media settlement receipts without saved IDs now use deterministic retained
  fact fingerprints, and stale/opaque Treeview IDs fail closed rather than
  resolving through the current receipt-list position.
- Cross-page legacy row identity is now content/type-bound across draft cards,
  booking slots, regional prospects, sponsor/World Hub rows, profile history,
  Regions, scouting packs and related readers; stale IDs fail closed and no
  refresh mutates source state.
- Finance history/runway/scenario and Awards/title-lineage readers now use
  recorded IDs/boundaries or deterministic retained-content fingerprints for
  legacy rows, preserving historical selection through refresh and reorder.
- Staff briefs, work receipts and exception readers now use saved IDs or
  deterministic retained-evidence fingerprints with duplicate-safe suffixes;
  malformed rows remain unavailable and cannot resolve by visible index.
- Shared Staff roster/candidate/contract rows and child scheduled-card rows now
  use deterministic retained-data identities when saved IDs are missing; stale
  or legacy event references fail closed for actions.
- Scouting assignment rows without a saved `assignment_id` now use deterministic
  retained request/content fingerprints, including empty or opaque legacy rows,
  rather than a visible list index. Saved search identities and read-only
  behaviour remain unchanged; Scouting coverage is 28 tests and UI-data remains
  green at 185 tests.
- The all-time Legacy Ledger now keys rows by source-bound fighter identity,
  with deterministic duplicate suffixes, instead of appending the displayed
  rank. Sorting/filtering cannot retarget a career row, and score/profile
  readers remain non-mutating.
- AI Staff employment rows without saved staff IDs now use deterministic
  retained employment/source fingerprints instead of visible indexes. Scouting
  watchlists without IDs receive content-bound keys, while duplicate generated
  legacy rows stay visible with suffixes; saved duplicate IDs keep their
  compatibility handling.
- Talent Relations now has a bounded Staff execution path for player-created
  renewal batches. The explicit `contract_batch_commit` action is available
  only to Full Auto; Recommendations and Selective Recommendations remain
  zero-spend contract reviews. The adapter requires a stable saved
  `contract-batch-*` target, preflights a conservative quote allowance against
  brief/monthly/action ceilings and cash reserve, then delegates to the
  existing Foundation-owned batch commit so per-fighter outcomes remain
  retry-idempotent. Actual row costs and structured evidence are retained in
  the Staff work ledger. The Staff UI explains the batch-ID prerequisite;
  ordinary Contracts creation and manual negotiation are unchanged.
- Shared fighter Treeview row IDs now use saved fighter identity as the base
  key across roster, Contracts, Matchmaking, Free Agents, Regions and company
  views. The visible index is no longer part of a unique row key; malformed
  duplicate identities receive deterministic suffixes, and existing source
  dictionaries keep selection/actions bound to the same fighter through sort
  and filter refreshes.
- Last-Minute Replacement candidate rows now keep ID-less legacy fighters
  visible through deterministic retained-content fingerprints with duplicate
  suffixes. The prompt and commit use that key instead of object identity, so
  sorting/reloading cannot collapse or retarget a same-name candidate.
- Title-miss Rebook Fight now retains stable fighter IDs and the original
  title/interim/special-belt/main-event terms when it moves a cancelled bout to
  an existing future card. Name-only legacy rows fail closed when duplicate
  careers make the target ambiguous; the original weigh-in decision remains on
  the cancelled event while the new card receives a fresh official weigh-in.
- Rebook requests with no suitable future card now remain as durable
  `needs_review` entries with one actionable notice and a quiet retry path. A
  later eligible card moves the same identity-linked title terms once without
  creating a result, duplicate fine or additional RNG draw.
- Staff retention readers now key empty/malformed legacy rows by deterministic
  opaque type/content fingerprints, and restore selection by the same retained
  object before falling back to a durable saved staff ID. Sorting cannot
  reassociate a duplicate unavailable row with another employee.
- Booking Workbench option and draft-review readers now key rows by saved
  fighter/booking identity or deterministic retained-data fingerprints, with
  duplicate suffixes for identical legacy rows. Visible positions are never
  used for review or commit routing, preserving unresolved slots and candidate
  evidence through refresh/reorder.
- Academy amateur-history profile rows now use saved bout/fight/event IDs or
  deterministic retained-content fingerprints with duplicate suffixes. Legacy
  malformed records stay visible as unavailable evidence, and row identity is
  independent of the displayed list position.
- Managed Fighter Profile and Company History windows now use saved fighter IDs
  or deterministic retained identity projections instead of process-local
  object IDs, keeping legacy profile focus/refresh behaviour stable and
  ambiguity-safe.
- Staff profile compatibility repair now derives missing staff IDs from
  retained employment facts rather than source list positions, preserving
  legacy staff/candidate identity when rows are reordered before load.
- Owner Objective compatibility repair now derives missing goal IDs from
  retained objective facts rather than source list positions, preserving
  observation/action routing through legacy goal reorder and duplicates.
- Talent Relations case compatibility repair now derives missing case IDs from
  retained fighter/source/obligation evidence rather than source list positions,
  preserving review and action routing through legacy case reorder and duplicates.
- Followed Story subscription compatibility repair now derives missing IDs from
  retained target and coverage/creation facts rather than source list positions,
  preserving acknowledge, snooze and unfollow routing through legacy reorder and duplicates.
- Scouting Decision Pack compatibility repair now derives missing IDs from
  retained pack/candidate facts rather than source list positions, preserving
  update/archive routing through legacy pack reorder and duplicates.
- Manual compatibility testing now validates finance, cost and cash before
  sampling, charging or case creation, failing closed on malformed/non-finite
  retained values while preserving the gated J5 confirmation/sanction lifecycle.
- Matchmaking draft move/remove actions now resolve through source-bound fight
  identity or a unique saved booking ID; duplicate equal legacy rows fail closed
  instead of routing to the first row.
- Media story reader navigation now follows source identity or a unique retained
  story ID; duplicate equal legacy headlines no longer jump to the first row.
- Detached story-ID fallback now preserves the original identity field, avoiding
  cross-field matches between legacy `story_id` and `story_key` values.
- Combat Sports card Remove and Move Up/Down actions now use source-bound bout
  identity or a unique saved bout/booking/fight ID; duplicate equal legacy
  rows fail closed rather than routing through a visible/list position.
- The compatibility Academy window now captures source-bound lead/prospect
  identity for sign, pass, profile, training, promote and release actions;
  a unique saved `prospect_id` is the only detached fallback and duplicates
  fail closed.
- Inbox fighter context and action eligibility now use saved fighter identity
  first and a unique name-only legacy fallback; duplicate same-name careers
  fail closed rather than receiving another fighter's context or decision.
- World Hub gym actions now use the retained source-bound row map, falling back
  to a name only when exactly one saved gym matches; duplicate gym names remain
  visible but cannot route an action to the wrong profile.
- Simulation Lab tournament selection now stores stable fighter row keys and
  resolves Draw & Seed/run actions through the retained fighter object, with
  duplicate-name compatibility deliberately failing closed.
- Simulation Lab corner comboboxes now disambiguate duplicate names and route
  scouting/profile/quick-fight actions through the selected fighter identity.
- Staff review handlers now use exact fighter identity first and a unique
  name-only compatibility fallback; duplicate-name targets fail closed.
- Super-event readiness/card validation now resolve fighter IDs first and
  report ambiguous legacy participants as unavailable without crashing.
- Matchmaking tournament review, TBA fill and title-toggle handlers now use
  stable fighter resolution and route ambiguity to the booking notice surface.
- Event conflict repair and earliest-card-date validation now use a safe
  stable-ID resolver and expose unavailable legacy identities without crashing.
- Event scheduling/cancellation/run projections now carry stable participant
  references through all reader and mutation boundaries.
- Event-atmosphere and championship-value readers now share the stable
  participant projection and omit unresolved/ambiguous legacy corners rather
  than rebinding a duplicate display name.
- Division closure, special-belt actions and card-editor previews now use
  saved fighter identities, with explicit unavailable states when a legacy
  duplicate name cannot be resolved safely.
- Development now has a clear outlook band, ceiling-gap signal, shared signed
  driver scale and recent recorded-change ledger; the reader never invents a
  time axis or treats its monthly score as guaranteed growth.
- Staff qualification auditing now retains and reports malformed work/brief
  rows, missing operation IDs and unsupported statuses, preserving raw save
  data while making long-run evidence gaps actionable.
- Progression envelopes and credited-work lists receive the same explicit
  malformed-payload diagnostics without changing the saved ledger.
- Long-run yearly audit measurements now expose Staff work-log, brief,
  exception and progression totals plus malformed-evidence counts, keeping
  qualification reporting aligned with the retained Staff evidence ledger.
- Hard-invariant audit coverage now validates Staff work/operation identity and
  progression-credit references without repairing the retained evidence.
- Yearly long-run measurements now expose player and AI/child Staff payroll
  totals plus malformed-salary counts for affordability qualification.
- Yearly long-run measurements now expose a bounded overdue-commitment total
  and source breakdown for explicit super-event, booking, medical, Media,
  Staff, owner-objective, fighter-career and Academy deadlines; malformed or
  missing due data fails closed without mutating retained work.
- Native calendar advances now retain bounded per-task timing diagnostics and
  isolated yearly audit snapshots keep count/total/max/per-task summaries;
  timing evidence is observational and cannot change calendar, RNG, finance or
  save behaviour.
- Yearly audit measurements now retain free-agent availability, eligible
  challenger depth, vacant-title duration and explicit expired-offer counts;
  malformed historical dates remain unknown without mutating title lineage.
- The managed Play Audit report now displays those metrics and calendar timing
  evidence in a labelled reader section with bounded legacy-value formatting.
- Each yearly audit row now receives a pure evidence-quality check for missing
  or inconsistent supply/title/timing fields; warnings are visible without
  repairing the checkpoint or changing the isolated world.
- Manual Testing Desk commissions now honour the player's saved provider and
  sample-count choice, apply the authored provider price multiplier, bound the
  run to available roster size, and retain the selected provider/quote on each
  case. Provider-specific detection and the confirmation/appeal/sanction
  lifecycle remain gated until the J5 policy table is approved.
- Long-run qualification now records player, AI and owned-child active-talent
  cohorts, per-company active divisions and eligible challengers, per-source
  scheduled-event coverage and pure missing/duplicate fighter, promotion and
  event identity counts; the audit report displays them without repairing
  retained state.
- Testing Desk case records now retain distinct negative, preliminary-positive,
  inconclusive and invalid outcomes, with review-only timelines and filters;
  unknown result input fails closed instead of becoming a negative finding,
  while legacy status-only rows remain readable without reader repair.
