## 6. Promotions, Spectator Mode, and World AI

### Finance invariants

Player, child, and non-feeder AI cash movements must be recorded through the canonical finance
helpers in `world.py`. Transaction rows retain an ID, month/week, category, source, counterparty,
event, reference, entity, revenue, costs, and net movement; legacy ledger strings may remain for
presentation but are not the accounting source of truth. `close_finance_week()` and
`close_promotion_finance_week()` reconcile the stored ledger to actual cash and create an explicit
`Reconciliation` row for an unattributed legacy/direct mutation. New cash paths must add a focused
regression and use a stable reference so repeated weekly closes are idempotent. Finance UI surfaces
must show reconciliation status and promotion detail views must read the canonical weekly history.

Per-event ticket price, marketing spend, and production tier belong to the scheduled-event payload.
Old saves and AI cards that lack those keys must fall back to company-wide defaults without mutating
the source during serialization. Any new or changed event-economics field needs a legacy-shaped
load assertion and a current-format scheduled-card round trip in the focused economics regression.

Player career-stage balance has three derived rules. `apply_opening_player_contract_terms()` runs
only while seeding a new player roster and discounts curated, non-generated talent to the founder
contract factor; never reapply it during load or repair. `player_monthly_office_cost()` derives the
current office bill from the save-compatible base plus company popularity, and every player reserve,
forecast, and month-end charge must use that helper. `player_events_in_month()` drives commercial
cannibalization for a second or later settled player card in the same simulation month: attendance,
sponsor value, and broadcast income fall, but contracted purses, medical, marketing, and production
costs remain whole. Keep `analysis/player_finance_balance_audit.py` and the focused event-economics
regression synchronized when changing purses, media, sponsors, overhead, cadence, or milestone gates.

Long-career finance reporting is compact persistent state, not a second ledger. Canonical
`weekly_history` remains the source for the current annual rollup; `annual_history` preserves a
30-year summary and `roster_cost_history` preserves monthly roster/purse commitments after detailed
weekly rows expire. Revenue mix uses archived player-event breakdowns for gate, broadcast, sponsors
and merchandise, then adds non-event canonical income as Other. Never double-count the event-level
transaction. Milestone ETA may extrapolate cash and event pace, but must show popularity, stability
and safety as blockers rather than inventing a growth rate.

Finance landing-page KPI cards are presentation-only projections over those same helpers. Keep
cash on hand, recurring monthly commitments, expected media/sponsor income per event, and booked
purse/medical exposure visibly distinct; label income as an estimate and exposure as a booked-card
reserve. Cards must not add a charge, probability, or alternate balance, and the detailed weekly
history/runway tables remain the complete audit record.
The runway's conditional income must keep contracted sponsor maximums separate from the
activation-adjusted estimate for each due event. Use the pure sponsor activation preview only;
do not call settlement or state-normalising helpers from a forecast. Conditional rights/sponsor
receipts stay outside conservative/base/strong cash closes, and the UI must show the reason for
an at-risk half-fee estimate.

Super-event projects are append-only commitment records. Acceptance must retain
the canonical deposit/setup/security terms and a payment reference; closeout
must expose paid/sunk, refundable, and unpaid components plus a stable terminal
settlement key. Cancellation or expiry never invents a refund, and legacy rows
without an accepted terms snapshot remain explicit manual-review evidence.
Repeated completion/cancellation calls return the original terminal record and
must not charge, refund, or clear an unrelated project.

Strategic investments live in `finance["strategic_investments"]`. Purchases and monthly upkeep must
use canonical `Investment` transactions with stable references. Effects are applied by
`strategic_event_multiplier()` and must never reduce contracted fighter pay or bypass event
settlement. Capital approval and upkeep are transactions: restore cash, ownership, ledger rows and
change history if a late recording hook fails, and make a repeated monthly upkeep call idempotent.
New projects require a capital cost, upkeep, milestone/popularity gate, bounded effect,
safe old-save default, Finance UI row, and progression regression. `player_monthly_office_cost()` is
separate from strategic upkeep so forecasts and transaction categories remain explainable.

### Rivalry and media-action invariants

Rivalry records and grudge economics resolve fighters by `fighter_id`. Display names may be retained
for copy and narrowly defined legacy repair, but an ambiguous name is not identity. Matchmaking,
Media Desk escalation, scheduled cards, and fight settlement must all preserve the same ID pair.

Paid or limited-use Media Desk actions are transactions: validate every selected fighter and rival
before charging cash, consuming an action, or changing rivalry/media state. If a late hook fails,
restore the staged cash, action counters, and affected media/rivalry state rather than leaving a
partial action. Add focused coverage for stale and duplicate-name rivals whenever this flow changes.

### Narrative-thread invariants

`story_threads` is a bounded interpretive index over authoritative fight, rivalry, title, contract,
academy, company, and career state. Domain methods emit one deduplicated beat after their real state
change; narrative code must never rescan the whole world, Chronicle, Results archive, or complete
fighter histories during weekly advancement. Active and resolved limits and per-thread beat limits
come from `constants.py`. Thread participants use stable fighter IDs, with names retained only as
presentation snapshots. Rivalries use `rival_fighter_id`, and friendships use `friend_fighter_id`;
legacy names may be backfilled only when the loaded world has one unambiguous match. The transient story-key index is rebuilt once after initialization/load and
maintained on writes. Active/resolved counts are maintained incrementally; do not normalize or sort
the whole collection on an ordinary write, and prune only after a hard cap is exceeded. Narrative
copy must not consume simulation RNG, and transaction rollback must
restore story state with the owning event or paid action. Long prose and career timelines are built
only when their view opens. Run `narrative_system_regression_test.py` after any story trigger,
identity, persistence, matchmaking-context, or career-journey change; run
`narrative_performance_regression_test.py` after changing thread indexing, pruning, or calendar
integration.

Contract Sagas use `Fighter.contract_story_key` as their only live pointer. Renewal warnings,
renewals, expiry/release, free-agent signing, return and cross-company revenge hooks must receive the
fighter and known company names from the domain event already in progress; they may not discover
stories by scanning rosters, free agents, promotions, Results or Chronicle. When
`narrative_tracking_enabled` is false, the lookup helper must return before reading the story key so
the paired performance regression measures the entire feature cost. Clear the fighter pointer only
after a resolving return or revenge outcome; keep the bounded resolved thread as career history.

Staff Tenure stories follow the same pattern through `staff_id` and the optional
`staff_story_key` stored on the staff dictionary. Appointment, contract-warning, negotiation,
renewal, release and expiry actions receive the already-known staff record directly and must not
scan the staff market, promotions, rosters, Chronicle or Results. Normalize missing legacy keys to
an empty string in `ensure_staff_profiles()`. Store bounded `staff_ids`, `staff_names`, and
`staff_role` snapshots on the thread, use the direct key for Staff Profile presentation, and return
before key lookup when narrative tracking is disabled.

Staff career contributions are first-of-kind tenure beats. Scouting reports pass their already-known
scout; medical clearance, settled player events and fulfilled promises may resolve one lead from the
small player staff list only after a qualifying outcome exists. Never run a staff-discovery pass or
inspect archived events to infer a contribution. Bound `contribution_kinds` and
`staff_milestone_kinds` to 12, clamp `staff_legacy_score` to 0–100, deduplicate before writing, and
normalize malformed legacy values without consuming simulation RNG. Event-settlement contribution
writes remain inside the existing event transaction and therefore roll back with a failed commit.

Feeder Pathways use `Fighter.feeder_story_key` as their only live pointer. Loan, recall, paid
transfer, player/AI fight settlement, contract departure, and retirement hooks must receive the
already-known fighter and company; they may not discover alumni by scanning child rosters, parent
rosters, Results, Chronicle, or fight history. `record_feeder_fight_result()` must retain its early
two-key exit before story/company work, and player/AI result callers must avoid entering it when
both supplied keys are empty. Child
undercard results do not need a beat; child main/title results, the first parent bout, one featured
parent breakthrough, and a parent title can advance the bounded chapter. Clear the live key only on
resolution. Loan, recall, and paid-transfer commits use the shared domain snapshot so a late story
failure restores rosters, belts, contracts, cash, ledgers, Chronicle, story indexes, and RNG.

Breakout Runs use `Fighter.breakout_story_key` as their only live pointer. The decisive-result hook
must reuse the eight-point Giant Slayer comparison already calculated by
`evaluate_fight_achievements()`; do not recompute derived ratings or discover upsets from Results,
Chronicle, rankings, rosters, or fight history. A qualifying upset may open one chapter, while only
the directly linked fighter's later result, draw, or retirement can advance it. Bound follow-up
counters and recent result references, clear the pointer on resolution, retain the resolved thread
as career history, and keep the story-aware AI bonus inside already-credible candidate pairs. The
player event transaction must restore both the pointer and thread after a late settlement failure.

Career Crossroads use `Fighter.crossroads_story_key` as their only live pointer. A new chapter may
open only from the already-settled third consecutive in-universe MMA loss for an established fighter
(age 30+, at least 18 professional bouts, or popularity 45+). Origin detection may inspect at most
the first four `bout_rating_history` rows; it must never reconstruct form from complete fight
history, Results, Chronicle, rankings, rosters, or a calendar scan. Once active, draws, later wins or
losses, division moves, release/contract exit, and final-fight retirement must use the direct key and
known domain participants. Keep recent result references and counters bounded, deduplicate retries,
clear the pointer only on resolution, and retain the resolved thread as career history. Player event
rollback must restore the pointer and exact thread, and AI story value remains limited to candidate
pairs the sporting matchmaker already accepted.

Fighter Relationship chapters use the deterministic pair-ID story key plus each participant's
bounded `relationship_story_keys` list. Friendship and featured stablemate results may begin a
chapter; draws, rematches, direct ID-backed rivalry tension, and a later meeting after a camp split
may advance or resolve it. Never query the story index for every ordinary bout: when neither current
friendship/stablemate status nor either fighter's active-key list applies, return before constructing
the pair key. Cap each fighter's list at four, remove the key from both participants on resolution,
and keep the resolved thread in the participant index for profile/annual history. Result callbacks
must deduplicate by stable reference, consume no shared RNG, and remain inside the player event
transaction so rollback restores both fighter-local lists and the exact pair thread. AI story value
may consider the active thread only for an already-credible candidate pair.

Career Farewell chapters use `Fighter.farewell_story_key` as the direct bridge from a retirement
decision to the final opponent and result. `mark_retirement_fight_required()` opens the chapter;
MMA, game-AI, regional, draw, no-contest, and other-sport settlement must resolve it with both known
participants before roster retirement removes the fighter. Meaningful-opponent scoring may only
reorder candidates the sporting matchmaker already accepted. Rival, friend and relationship links
must use fighter IDs; former-opponent meaning must read bounded structured `bout_rating_history`
opponent IDs, never display-name fight-history text. Do not add a retirement discovery pass. The
ordinary result path must exit after the existing `retirement_pending` field check, callbacks must
deduplicate, and player event rollback must restore the pointer, thread, Chronicle and RNG state.

Academy graduation is one such owning transaction: its rollback snapshot includes `story_threads`,
and the transient story indexes must be rebuilt after restoration. Never allow a failed late
graduation hook to leave a thread for a fighter who was not actually created or transferred.

Fighter Career Timeline presentation may combine the selected fighter's bounded local histories
with `story_threads_for_fighter()`. It must not search Results, Chronicle, archived cards, or the
wider fighter world. Annual review selection may inspect the bounded story-thread collection once
at year rollover; it must remain capped and must not become a weekly/monthly discovery pass.

AI story intent is a bounded bonus inside the candidate pairs the matchmaker already evaluates. It
must use cached direct story-key lookups, must never create another all-pairs pass, and must not make
an otherwise invalid matchup legal. The deterministic calendar A/B disables this decision feature
in both arms so it measures tracking cost and RNG purity rather than intentionally different cards.

Promotion Rivalry chapters are two-company, 24-month cycles updated only by an owning contested
signing, academy-recruitment result, or sanctioned superfight. Callers must pass the known companies;
never discover rivalries by comparing every promotion or roster. Stable event references protect the
scoreboard from duplicate callbacks. Coaching Loyalty is likewise event-driven: significant gym
moves open or close a room-specific chapter, and completed meaningful fights update only the two
participants' direct story keys. `Fighter.academy_prospect_id` is the persistent bridge from academy
mentorship to senior-career outcomes; old saves default it to empty rather than scanning alumni.

Hometown Hero chapters are also event-owned. `schedule_event()`/the immediate event path may frame
an already-booked main or title homecoming only when the known fighter has at least 60 market
popularity (or an existing hometown thread). Player and AI result settlement then update that direct
fighter/region key through `record_hometown_fight_story()`. Do not search scheduled events, regional
markets, rosters, or result archives to discover homecomings. Once a home-title or market-icon
resolution exists, later epilogue beats must not overwrite its phase or resolution.

### Shipped-universe source of truth

New careers load `Databases\Default Universe.universe.json` through
`load_universe_database_pack()`. Its `fighters`, `combat_sports`, `companies`, `media`, and `regions`
sections are independently editable and are the source of truth for the shipped starting world.
The pack has a top-level schema version, and complex sections such as `fighters` and
`combat_sports` also carry their own schema versions. Python seed specs provide defaults, generated
depth, and repair fallbacks; changing only a fallback may not change a new game built from the
database.

`universe_validation.py` is the sole side-effect-free schema validator for editor, runtime, and release tooling. It returns actionable section/record/field issues rather than throwing on malformed user JSON. `load_universe_database_pack()` may normalise old packs in memory, but normal loading must never rewrite a source database; explicit reset/migration operations own backups and writes.

All runtime `Toplevel` creators in `admin.py`, `awards.py`, `events.py`, `persistence.py`, and
`views.py` must call `UIMixin.create_managed_window()`. Its default key combines the call site with
available fighter/entity identity, so repeated clicks replace stale popups without conflating two
different fighters. Long-lived screens may provide an explicit stable key.

Fighter Profiles are observational views. Opening or reopening one must not consume simulation RNG,
generate or synchronize ratings, migrate saved history, initialize child-sport circuits, appoint
champions, or otherwise mutate career state. Resolve the displayed employer, opponent, result,
championship and archive by `fighter_id`/stable record identity; ambiguous legacy names may be
omitted but never guessed. Apply scouting visibility to every rendering surface, including portrait
text and identity rows. Profile action visibility is only convenience: contract, comeback, transfer,
and weight-move transactions must revalidate Spectator Mode and current ownership at commit time.
Keep the fixed Profile footer inside the physical display and register fighter windows with the same
explicit key used for focus/reuse.

Use `database_editor.py` or a carefully reviewed data edit for starting-universe changes, then
validate the file. The standalone database editor changes universe database packs; it does **not**
edit an active career save.

Event-city choices and generated-fighter hometowns come from `REGION_CITIES` in `constants.py`.
Keep each city in its broad simulation market (for example, Belleville and Kingston are Canadian
locations), and add smoke coverage for both the booking selector and identity pool. The universe
database's `regions[*].areas` list describes larger tracked areas such as Ontario; do not duplicate
individual cities there merely to make them available for events.

Curated fighter identity edits in the shipped database must keep the full record in
`fighters.all_fighters` synchronized with its compatibility tuple in `fighters.player_roster`,
`fighters.free_agents`, or `fighters.promotions`. For example, Brett Akey's Belleville hometown is
stored in both his `all_fighters` record and his `free_agents` tuple. Validate the database and
retain a named identity assertion in `smoke_test.py` after changing either representation.

### Company ownership invariant

When `take_control_of_company()` transfers an AI promotion to the player, it must reconcile stale zero-month AI contracts first. Those fighters remain in the inherited roster and receive fresh 12-24 month exclusive contracts; a takeover must never mass-release a company's roster merely because legacy AI contract terms reached zero.

The MMA Child Promotions manager in `views.py` is an operations screen, not just a launch dialog. Keep its promotion table synchronized with child cash, stability, roster size, protected loans, parent distributions, and AI mode. Roster filters must only change display; loan, recall, and parent-transfer actions must continue to use fighter IDs and the world-layer ownership rules.
Academy rival-program rows are a read-only promotion index and must use
promotion identity keys with deterministic duplicate suffixes; duplicate
display names must never collide or redirect a rival-program detail.
The manager must list only child promotions whose `parent_company` matches the active player company. Its child-roster status filter must not be applied to the separate parent-roster loan source. Parent profit-share transfers and child-fighter transfer fees must use the normal finance transaction recorder. Paid transfers require confirmation, respect closed parent divisions, and taking an expired AI-signed child fighter must assign a fresh contract rather than a one-month stub. Ordinary company takeover must reject child promotions. Empty launches must roll back capital and the promotion when no eligible opening roster can be signed. Champion loans vacate the parent belt before moving the fighter. Loan, recall, and paid-transfer actions are atomic and must retain their Feeder Pathway hook inside the rollback boundary. Load repair must clear stale loan markers for missing, mismatched, retired, or retirement-pending fighters; the manager must reset stale detail text after redraw, preserve duplicate identity labels, show the selected fighter's active feeder chapter, provide vertical roster scrollbars, and reuse one manager window.

During a normal player career, the player company is represented by player-owned fields such as
`self.player_company_name`, `self.roster`, `self.cash`, and `self.company_pop`. It must not also be
present in `self.promotions`, or it will be simulated twice.

`Create Your Own Promotion` keeps BAMMA in the world as an AI promotion. Spectator Mode is different:
it promotes the former player company into `self.promotions`, persists `spectator_mode`, and keeps
all observer fast-forward controls in the Game Menu observer panel.

### Current core promotions

The default player company is BAMMA. The core rival/company set includes:

- Ultimate Fighting Championship
- Professional Fighters League
- ONE Championship
- RIZIN Fighting Federation
- KSW
- Cage Warriors
- Legacy Fighting Alliance
- Oktagon MMA
- BRAVE Combat Federation
- Absolute Championship Akhmat
- PRIDE Fighting Championships
- Strikeforce
- World Extreme Cagefighting

Regional feeder promotions are also first-class world objects:

- Japan Fight Circuit
- UK Regional MMA
- North American Fighting League
- European Challenge MMA
- Asia Rising Championship
- Brazilian Combat Circuit
- Latin American MMA League
- Canadian Fight Alliance
- Oceania Combat League
- African MMA Championship
- Midwest Fight League
- Nordic Combat League
- Korean Fighting Championship
- South American Vale Tudo Circuit
- British Fight League
- Eurasian Fight Circuit

Feeders have `is_regional_feeder=True`, do not use the normal commercial-finance simulation, and
support young-prospect generation, development cards, and pathways. The Eurasian circuit has
authored male-only behavior; preserve its origin and roster-depth rules. A multi-fighter intake
batch must build the world-name collision set once, extend it after every generated recruit, and
reuse it for Eurasian renaming; do not rescan the complete fighter population per slot.

### Player-funded MMA child promotions

MMA child promotions are ordinary AI-managed `Promotion` objects with
`is_child_promotion=True`, `parent_company`, `child_strategy`, `parent_profit_share`, and
`loaned_fighter_ids`. They are launched from the Companies screen with player-selected startup
capital; the launch budget funds an opening MMA free-agent roster, after which the existing AI
card, contract, development, finance, and market systems manage the child normally.

The supported child identities are `Balanced`, `Youth Prospects`, `Big Names`, and
`Merit & Contenders`. The identity updates the child's persistent AI focus and card personality;
do not create a second matchmaking engine for it. Positive event profit distributes the configured
0-100% share to the parent company and records the transfer in the child's strategy/finance data.

Loans move a fighter from the player roster into the child roster while preserving the parent
contract. The fighter's `loaned_from_company`/`loaned_to_promotion` fields and the child's
`loaned_fighter_ids` index must stay synchronized. Child contract expiry, roster cuts, upgrade
replacements, distressed buyouts, retirement removal, and save repair must protect loaned fighters;
only the parent loan manager can recall them; the parent may also take an AI-signed child fighter by
paying the transfer fee. A bounded development loan may additionally persist
`loan_return_month`/`loan_return_week`; at that agreed boundary the weekly world pipeline returns
the fighter only after any already-committed child bout has settled, surfaces a delay notice when
needed, records the membership/Feeder Pathway return, and clears both date fields. Zero values
retain the legacy open-ended recall contract. Return processing is deterministic and must not add
fees, title waivers, treaty effects or simulation RNG. New fields require safe load defaults and a
round-trip regression in `smoke_test.py` plus the focused loan-return suite.

The child-promotion manager also owns an explicit Future Child Cards workflow. A scheduled card is a
planning record on the child `Promotion.scheduled_events` list with stable `event_id`,
`promotion_id`, owner reference, target month/week, optional target bout count, and status. Planning
must not reserve fighters, assign camps, spend cash, run matchmaking, or draw RNG; the shared Owned
Calendar and Upcoming readers may only project the saved record. Enforce one scheduled card per child
month and resolve cancellation by saved promotion/event identity. At the due boundary an explicit
card bypasses the probabilistic AI show roll but uses the ordinary readiness, matchmaking, medical,
title, finance, media, replay, and history pipeline. If readiness, matchup, or budget validation fails,
retain the plan as `Needs replacement` with an explanatory Inbox task; do not silently run a substitute
card or repeatedly retry it. Legacy child schedule rows receive deterministic IDs only at load repair.

### How game-AI promotions decide

Promotion behavior is persistent state, not a fresh random personality on every card:

- `show_personality` is the stable event-cadence and card-construction identity, such as
  `Super Shows`, `Seasonal`, or `Prospect Builder`.
- `strategy` stores stable identity (`identity`, `media_voice`, star/prospect/merit focus, risk and
  commercial traits) plus mutable state such as `current_mode`, financial pressure, roster health,
  and market momentum.
- `executive` stores leadership traits (`aggression`, `patience`, `discipline`, job security) and a
  board mandate with progress and deadline state.
- `update_ai_promotion_strategy` chooses `Financial Recovery`, `Prospect Rebuild`, `Star Chasing`,
  `Contender Cycle`, `Title Push`, or `Balanced` from cash, stability, reputation, momentum, and the
  persistent identity.
- `ai_should_run_show` gates scheduling with cash, named-day readiness, fatigue limits, roster depth,
  current mode, executive pressure, and show personality.
- `ai_offer_*` fields on a fighter represent a visible pending contract offer. The offer persists
  until its deadline and resolves later; do not replace this with instant random signing.
- Regional feeders branch into development-focused behavior and bypass normal commercial finance.

Simplified decision flow:

```python
strategy = self.update_ai_promotion_strategy(promotion)
if self.ai_should_run_show(promotion):
    self.simulate_ai_promotion_month(promotion)

# Separately, the contract market creates a pending offer.
fighter.ai_offer_company = promotion.name
fighter.ai_offer_deadline_month = self.month + 1
# A later market step accepts, rejects, or clears it.
```

When adding, removing, or renaming a core promotion:

1. update the `companies` section of the shipped universe database and the relevant fighter
   ownership/roster records;
2. update authored Python fighter data and fallback `default_promotion_specs`/`seed_promotions`;
3. update `repair_core_promotions` so old saves heal;
4. update promotion executives, strategies, identities, and `promotion_broadcasters` where relevant;
5. update regional feeder specs if it is a feeder;
6. validate the universe database and update `smoke_test.py`; and
7. update `README.md` and release notes when player-visible.

