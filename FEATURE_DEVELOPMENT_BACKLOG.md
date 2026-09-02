# MMA Warriors — Feature Development Backlog

## Purpose

This is the current feature-development map for the player-facing game. It is based on the active
Python implementation, regression coverage, `docs\CODEX_HANDOFF.md`, and the grounded
`docs\COMPANY_MILESTONES_AND_SUPER_EVENTS_DESIGN.md`. It deliberately excludes fixes already
completed in the comprehensive code review unless they are prerequisites for a feature.

## Current product position

MMA Warriors already has a substantial simulation: player and AI promotions, event booking,
contracts, finance, rankings, awards, tournaments, academies, regional feeders, combat sports,
child promotions, media, world news, chronicle/history, spectator mode, and a persistent inbox.
The next development value is therefore concentrated in completing unfinished flows, making
management decisions more consequential, and improving the long-run calendar experience.

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

#### P1.1 — Put child-promotion cards on the future event calendar

**Evidence:** `docs\CODEX_HANDOFF.md` explicitly records that child promotions support manual and
smart cards but run immediately instead of using the parent-style future event calendar.

**Current state:** `views.py:open_child_promotion_manager()` supports manual booked cards and smart
cards. The child can run a card, but the card is not a normal future-dated event in the shared
calendar pipeline.

**Desired feature:** Let the player choose a future week, show the child card in the calendar and
upcoming-events views, prevent fighter/date conflicts, advance it through the normal queued
calendar flow, and preserve child-specific finance, history, loans, and replay data.

**Likely files:** `views.py`, `events.py`, `world.py`, `persistence.py`, `models.py`,
`child_promotion_interactions_test.py`, `child_promotion_long_run_test.py`.

**First slice:** create one shared child-event payload and route it through scheduling, date-aware
availability, execution, save/load, and cancellation. Add a multi-week regression proving that a
scheduled child event does not execute early and that a protected loan remains protected.

#### P1.2 — Finish the super-event execution loop

**Evidence:** `docs\COMPANY_MILESTONES_AND_SUPER_EVENTS_DESIGN.md` marks super-event opportunities as
new and says Phase 4 execution is not complete. The implementation in `awards.py` already has
milestones, offers, readiness, approval, and project state, but the full project lifecycle needs to
be completed and verified as a normal event.

**Current state:** `awards.py` owns milestone/offer state and readiness; `events.py` owns scheduling
and event finance. The design calls for approval, card build, budget, incidents, result, and history.

**Desired feature:** Accept an offer, build and validate the card, pay staged costs, handle a small
set of transparent event-week incidents, run the event through the ordinary fight/result/finance
transaction, and write a durable success/failure record. Failed or cancelled projects must refund or
retain funds according to explicit rules and never leave a half-scheduled event.

**Likely files:** `awards.py`, `events.py`, `world.py`, `persistence.py`, `views.py`,
`docs\COMPANY_MILESTONES_AND_SUPER_EVENTS_DESIGN.md`.

**First slice:** ship the recommended one-night Grand Prix Showcase using the existing tournament
bracket. Defer ceremonial and mega-stadium content until the shared transaction and rollback path is
proven.

#### P1.3 — COMPLETED — Make promotion finance fully auditable

**Evidence:** `docs\CODEX_HANDOFF.md` lists finance completeness as follow-up work: weekly history
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

#### P1.4 — Replace remaining routine modal advancement decisions with game-surface workflows

**Evidence:** `docs\CODEX_HANDOFF.md` identifies native-dialog cleanup as follow-up work. The recent
advance-notification work handles routine notices, but validation, delete confirmation, academy/
scouting decisions, and some fight-day flows still use Tk message boxes.

**Desired feature:** Use themed inline panels, inbox tasks, or a single decision center for routine
choices; retain modal confirmation only for destructive actions and explicit final approvals. Every
decision should have a clear consequence, cancel path, and save-safe state.

**Likely files:** `ui.py`, `views.py`, `events.py`, `world.py`, `persistence.py`.

**First slice:** audit messagebox call sites, classify them as notice/decision/destructive
confirmation, and migrate the highest-frequency advancement paths to the inbox/assistant surface.

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

#### P2.2 — Complete the 100-year generational simulation audit and balancing pass

**Evidence:** `docs\CODEX_HANDOFF.md` records a completed 30-year audit and a future overnight
100-year audit. The project goal is a living world, so three-generation stability is a product
feature requirement, not just a test statistic.

**Desired feature:** Validate that fighter generation, academy intake, retirement, promotion health,
free-agent supply, titles, finances, and regional feeders remain viable for 100 years. Record the
metrics and tune only demonstrated equilibrium failures.

**Likely files:** `stability_test.py`, `admin.py`, `world.py`, `seeding.py`, `models.py`,
`child_promotion_long_run_test.py`.

**First slice:** add a deterministic 100-year audit mode that emits compact yearly metrics and fails
on roster extinction, runaway cash, title starvation, or unbounded history growth.

#### P2.3 — Upgrade the highest-value information surfaces into decision centers

**Evidence:** the handoff calls out Companies, Regions, Personal Assistant, Staff/Scouting, and
Chronicle as the highest-value remaining interactive upgrades; current methods such as
`views.py:open_selected_company_hub()`, `open_selected_region_hub()`, `open_selected_assistant_notice()`,
`open_selected_staff_profile()`, and `open_world_chronicle()` are established surfaces to extend.

**Desired feature:** Each surface should answer “what changed, why it matters, and what can I do
next?” with linked actions, stale-data-safe refreshes, and no duplicate popup windows.

**First slice:** add actionable next-step cards to Companies and Personal Assistant, backed by stable
IDs and the shared notification registry.

#### P2.4 — Normalize legacy save data during an explicit migration

**Evidence:** `docs\CODEX_HANDOFF.md` notes that legacy fighters can still carry the internal
archetype string `Standard Prime`; profiles translate it, but stored data is not normalized.

**Desired feature:** Add a versioned, backup-preserving migration that normalizes known legacy values,
records the migration, and leaves healthy saves untouched during ordinary load.

**Likely files:** `persistence.py`, `models.py`, `smoke_test.py`, `persistence_regression_test.py`.

### P3 — Content and polish after the above systems stabilize

- Expand super-event venue and ceremonial content only after the first executable format is stable.
- Add more regional identities, media voices, academy personality/challenge variants, and crowd/audio variants as
  data-driven content rather than new mechanics.
- Continue replacing static detail panels with linked profiles, filters, and clear empty states.
- Add player-facing export/share views for company history and the Chronicle once the underlying
  history data is fully reconciled.

## Recommended sequence

1. Child-promotion future scheduling.
2. Super-event execution using one-night Grand Prix Showcase.
3. Routine decision-center migration.
4. 100-year audit and balancing.
5. Companies/Assistant/Regions decision-center improvements.
6. Legacy migration and content expansion.

This order keeps the calendar and money systems coherent before adding more visible endgame content,
and it reuses the existing event, finance, inbox, achievement, and persistence infrastructure.

## Already completed foundation relevant to this backlog

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
