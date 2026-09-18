# MMA Warriors AI Developer Guide

## Documentation navigation

`docs/README.md` indexes current documentation. Older reviews, proposals and handoff
prompts are retained under `docs/archive/2026-09-18/` with their original-path inventory.
Treat them as historical evidence, not current implementation instructions. Preserve
referenced technical contracts, audit evidence and plans containing deferred decisions;
when archiving a document, retain its bytes and update incoming references explicitly.

## Fight Night presentation

`fight_night_layout.py` builds the broadcast shell; `fight_night_presentation.py`
styles recorded lines without rewriting or filtering their content. Playback and
scorecard sealing remain in EventMixin. Feed visual accents must not treat incidental
or negated mentions of hurt/cuts as resolved events. `fight_night_archive.py` is
observational, with independent listbox selection and read-only full transcripts.
Keep 136px normal/104px compact portraits, responsive resize handling and useful
reading height at820x540 in the actual live window, not only the isolated layout.
Round bars may consume only presented telemetry, never future archived analysis.
Event preparation timelines are additive read models: they may display only the
already recorded campaign, press, weigh-in, cancellation and readiness evidence.
Store them with the canonical event package so Results and Fight Night archives
can inspect the same identities; opening a timeline must not rerun preparation,
consume RNG, alter card order or change settlement mechanics. Legacy packages
without `preparation_timeline` remain valid and render an explicit unavailable
state rather than fabricated outcomes. Per-stage completion keys are event-scoped
and may be present only for recorded stages; do not treat a missing key as a
permission to regenerate a press or weigh-in outcome.
The archive reader keeps this unavailable state reachable through an explicit
selectable entry even when no stage rows were saved; opening it is still
read-only and must not infer a press, weigh-in or readiness result.
Gym counts are synchronized during calendar advancement and existing gym
mutation/read paths, rather than every header repaint; World Hub refresh must
not rewrite membership state simply because the page was opened.
Title-miss replacement-corner controls must identify the saved corner (not only
the display name) and resolve its merit explanation by stable fighter ID; a
duplicate name must never select or describe the other corner.
Staff autonomy workers must run only after the completed calendar week's cards,
settlement and month-end business tasks. Pass the completed month/week into the
worker when the calendar has rolled forward, and record work against that
completed boundary rather than the next visible period.
Spectator fast-forward must return without evaluating committed Staff briefs or
granting recommendation/Full Auto authority; saved briefs remain untouched for
the player's return.
Spectator stop policies capture the source game revision when armed. Automatic
fast-forward and Resume must fail closed on an explicit revision mismatch before
starting calendar work; policies from legacy saves without the field remain
compatible. Clearing/replacing the stale policy is explicit, and ordinary save
loading stays independent of this guard.
The revision guard must also run at `begin_advance_sequence`, before due-card
checks, job creation, callbacks or Tk scheduling, so direct callers cannot bypass
the public fast-forward/Resume guard. Legacy policies without a revision remain
compatible; stale policy data is never rewritten by the failed attempt.
Rule-default/load projection must preserve the additive `source_revision` field;
it may represent a pre-guard legacy policy with an empty value but must never
filter an explicit revision away and thereby weaken the mismatch guard.
The simulation policy status reader must render an explicit stale-revision state
and bounded `Date target unavailable` state for malformed targets without
rewriting the saved envelope or calling calendar repair; Clear and Apply Policy
remain the explicit recovery boundaries.
Before an automated Marketing commit calls the Media resolver, its pure quote
must pass the saved brief-level spend ceiling as well as the company/action
guardrails; an over-ceiling quote becomes Needs attention with no spend.
Recommendations and Selective Recommendations are separate player choices:
the former may inspect every authored read-only department action, while the
latter may inspect only actions explicitly allow-listed on the brief. Never
expose a mutating action through either recommendation mode; a selective brief
that names one fails closed with Needs attention. Full Auto remains the only
mode allowed to run an explicitly selected mutating action, subject to the
existing permission, lead, quote, capacity, ceiling and reserve checks.
The Staff capability grid should list the safe read-action IDs for each
department, keeping the visible policy scope aligned with the saved brief and
calendar worker, and its viewport must fit every registered department or
provide an explicit scrollbar rather than silently clipping rows.
Each registered action also has an explicit evidence gate: a worker may seal a
recommendation or Full Auto work row only when the handler returns a non-empty
evidence key and a structured payload. Recommendation modes must reject any
reported spend; the capability read model should expose handler registration and
gated/ready state without normalising the save. A domain action's own evidence
may name its underlying Media action, so validation must not confuse domain and
staff action IDs.
The Staff page's long-run evidence audit is a pure diagnostic over the retained
brief/work/progression ledgers. It must report stable identity and contract
findings (missing/duplicate work or operation IDs, missing evidence, unsupported
actions, paid recommendations, malformed payloads, sealed incomplete briefs and
orphaned progression credits) with source IDs and counts for executed,
recommendation and qualified work. It must not normalise legacy rows, rerun a
handler, consume RNG/capacity/cash or award progression while being opened or
refreshed.
Staff roster, candidate and expiry table actions must resolve by saved
`staff_id`, not a visible row index. Preserve the selected employee through
refresh/sort when still visible; deterministic suffixes disambiguate duplicate
source IDs. ID-less legacy rows should use a deterministic fingerprint of their
retained fields; only a completely empty/malformed row may use an explicitly
non-durable UI fallback, and it must never be reassociated with another employee.
Child-promotion manager rows and ownership actions must likewise use stable
`promotion_id` references. A duplicate child display name is ambiguous and must
fail closed; only a unique legacy name may be used as a compatibility fallback.
Membership history readers (`foundation_membership_events` and interval/as-of
projections) must use the raw retained envelope and remain read-only even when
that envelope is malformed. Return an explicit empty/incomplete state and leave
normalisation to the sanctioned load/migration boundary.
The feature-development plan's progress count is two-level: G0–G5 are six
delivery gates, while the 63 non-deferred named cards are finer-grained work
units. The 14 D-cards are deferred/excluded and must not be presented as first
release work; card completion still requires its full acceptance contract,
regressions and any explicit policy decision.
The sidebar Event Log is a presentation reader over the complete persisted
`event_log`: style/classify lines without editing, filtering or reordering them.
Keep the empty state explicit, preserve scroll position through refresh/theme
changes, and do not make opening or repainting the log run a fight, settlement or
simulation task.
Routine selection/progress guidance belongs in the owning page status surface or
Inbox when available. Direct native information dialogs must be listed in the
dialog-inventory regression and guarded as a compatibility fallback; the native
Fight Day three-way choice is headless/legacy-only because desktop uses the
managed decision panel. Validation errors, destructive confirmations and final
approvals remain explicit dialogs.
Rules Help is an authored, stable catalogue (`rules_help.py`), not a second
rules engine. Search indexes only stored topic text and aliases; route links
must fail closed when a screen is unavailable, and opening or filtering help
must not evaluate mutable formulas, reveal hidden scouting values, consume RNG
or change gameplay state beyond the separately persisted UI search preference.
Company profile Follow state is also a reader: use `story_subscriptions_read_model`
while opening or repainting a company, and reserve `ensure_story_subscriptions`
for the explicit Follow/Unfollow mutation callback. A malformed subscription
envelope must remain unchanged during profile display.
Cash-runway readers must treat a non-mapping or malformed `finance` envelope as
unavailable data, not call a repair initializer or crash while calculating the
office baseline. Use a bounded fallback in `player_monthly_office_cost`; retain
the raw envelope and keep the forecast free of cash, schedule and RNG changes.
Finance refreshes are presentation readers: do not call `ensure_finance_defaults`,
write derived payroll/offer keys, or call the annual-history mutation owner while
repainting the page. Project malformed finance/history envelopes locally with
bounded values and explicit unavailable rows; calendar and explicit finance
actions remain the only write boundaries. Strategic-investment status and
upkeep used by Finance, runway and dashboard readers must use the explicit
non-repairing projection; do not let `owned_strategic_investments()` seed or
rewrite a malformed finance envelope during repaint. Purchases and calendar
upkeep retain the repairing action boundary.
Game & Saves is also a library reader: refreshes may enumerate existing save and
database paths but must not create the active-universe marker, normalize a
database, or repair autosave rules. Preserve path-bound selection and leave
loading, copying, deleting, backup, folder movement and database selection to
their explicit action handlers.
Matchmaking draft refreshes are presentation readers: apply card-order/main
metadata only to shallow display copies, preserve the saved `booked` order and
stable fight map, and do not repair the transient event-name field while
repainting available fighters. Add/move/edit/remove handlers remain the only
draft mutation boundary.
Regional Prospects readers must call `regional_candidate_assessment` with
`repair=False`, consuming only stored history baselines and bounded defaults.
Simulation, load/migration and explicit roster-transition owners retain the
baseline repair boundary; opening or filtering the table must not write fighter
history fields or consume RNG.
Regional Prospects throughput/backlog summaries are readers too: use a
non-repairing cache projection and never write the monthly eligibility cache or
repair malformed rules while the table is opened, filtered or refreshed.
Regional Prospects row keys must bind both the promotion and fighter identity,
with deterministic duplicate suffixes for repeated legacy pairs. Refreshes
restore the selected row only when that source identity remains visible; never
use the sorted row position as the action target.
Rankings must not expose a private fighter's derived rank/P4P score when
Scouting Mode hides their ratings. Keep public rank, movement, record and
scouting-safe estimates, but render the private score as `Hidden`; do not use a
tooltip, sort label or detail fallback to leak it.
Rankings refresh is presentation-only: calculate visible ordering and rank maps
locally and do not call `refresh_promotion_rankings` from the page reader.
Stored current/previous movement snapshots are updated only by calendar,
simulation or other explicit ranking owners.
Combat Sports overview and Records/History pages are read-only projections:
call the circuit-state reader with `repair=False` so legacy weight, title,
ranking and record-cache repairs occur only on explicit management, migration
or simulation paths. Preserve sport-native identities and never write to the
saved world merely because a reader was opened or refreshed.
Company standings and selected Combat Sports company profiles must use the same
non-repairing projection; switching a company row or refreshing standings must
not migrate circuit state as a side effect.
Combat Sports Records/History athlete opens must use the saved `title_ids`/
fighter IDs behind ranking rows. A display name is a compatibility fallback
only when it resolves to exactly one athlete in the selected circuit; duplicate
same-name careers fail closed instead of opening the first roster match.
Records/History title, finance and event tabs must defensively project malformed
retained rows as explicit unavailable evidence (including safe dates/amounts)
without repairing or dropping the raw history during refresh.
Company profiles and child-promotion management readers must use a defensive
promotion-strategy projection; opening or repainting them must not seed a
missing strategy or compatibility defaults. Strategy creation remains with
explicit gameplay/calendar owners.
Upcoming Cards refreshes must not call `repair_scheduled_event_names` or mutate
saved event names/card order. Project auto-generated names and locally ordered
fight lists onto a display copy, while `upcoming_event_rows` continues to map
the stable UI identity to the original event for explicit edit/cancel actions.
`refresh_event_economics_forecast` must call `selected_event_economics(repair=False)`
and use a bounded production baseline; explicit booking/apply actions retain the
normal repair boundary. A malformed finance envelope must never be normalized by
opening the booking reader.
`refresh_event_broadcaster_status` must likewise treat a malformed
`finance.media_rights` value as an unavailable empty mapping and keep the
saved envelope untouched; status repainting is not a media-contract repair path.
Regions profile readers should use a defensive copy of the selected row,
preserving an explicit unavailable state for non-mapping data and bounded
defaults for missing lists/indicators. Do not repair `regions` or infer profile
facts during `refresh_regions`/`refresh_region_profile`.
Fight History column visibility, order and widths are presentation preferences
stored in `ui_fighter_history_columns` plus the versioned
`ui_fighter_history_column_layout` envelope. The chooser may reorder visible
stable IDs, set widths only within 70–360px and restore hidden fields; retain
the complete row payload and preserve widths for hidden fields. Adding a future
field is additive to the registry and must not invalidate older layouts.
Capture native Fight History header-resize releases into the same envelope;
sorting and row clicks remain presentation-only.
Fight Night's canvas-backed Round Read and Bout Desk must bind wheel scrolling
to their own hovered content (including Button-4/Button-5) while leaving the
action timeline and native text/list/tree widgets to their existing handlers.
Use `semantic_status_palette` for positive/negative/warning/info/neutral
Treeview accents. Retheme known semantic tags when switching palettes so light
themes do not inherit pale dark-theme text; keep status words and all row data
intact, and leave unknown/authored tags untouched.
Lazy-built pages must receive this semantic pass immediately after construction,
not only during the initial application build or an explicit theme switch.
Apply the same mapping to known semantic Text tags (Assistant/Event Log), while
preserving authored headings and transcript content.
The registry also covers unread, owned/available, readiness, scouting-strength,
ranking-movement and injury tags. If a Treeview tag owns an authored background,
only apply the new foreground when it remains WCAG-readable against that
background; otherwise retain the existing authored light foreground. Never
trade contrast for a palette token.
Secondary Staff, booking, contract and read-only history states (ready,
preserved, partial, review, open, booked and closed) should use this same
semantic registry rather than adding fixed theme-specific colours.
Sponsor offer previews must show the contracted maximum per eligible event,
the current activation-adjusted estimate and remaining term separately. Include
the readiness reason and full/half-fee basis; calculating this card must remain
read-only (no offer refresh, cash spend, settlement or RNG draw).
Cash-runway scenario snapshots are explicit planning records: persist a stable
scenario ID, bounded assumptions, proposed edits, source revision and forecast
copy; mark changed inputs stale on read. Saving/reviewing a snapshot must not
move an event, apply prices or production, reserve cash, rerun settlement or
consume RNG.
Finance sensitivity controls may change only the read-only low/base/high
attendance assumptions, bounded to 0–200%; the table, saved forecast and labels
must use the same values and must not claim probability.
In stacked Matchmaking at laptop widths, reserve enough space for at least four
fighter rows at 1280×760; keep the draft-card controls reachable and let its
table scroll independently rather than collapsing the explorer.
Combat Sports contract rows must use stable sport/fighter identity keys, not
visible list positions. Preserve the selected athlete across refresh/filter
changes when still visible; retain duplicate source rows with deterministic
suffixes and never route an action to a different contract.
Delayed Matchmaking layout timers must be scheduled through a cancellable
helper and cancelled through the widget that registered them before teardown;
closing/rebuilding the page must not emit invalid Tcl command errors.
Run the three new Fight Night presentation/archive/layout suites plus experience,
smoke, audio/window lifecycle and stability tests. Do not rebuild an EXE unless asked.

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

## Spectator simulation controls

Persist spectator stop policies as plain data in the save's rules. Runtime
advance jobs may copy the policy and evaluate it only after a fully completed
calendar week; never serialise Tk callbacks or stop in the middle of a
synchronous world task. Target dates are exact internal month/week boundaries.
Event monitoring compares stable archive cursors and optional company/fighter
IDs without resolver calls or RNG. A stop records the last completed boundary
and reason, disables the armed policy, and requires an explicit Resume action;
repeated stop requests remain safe and do not settle a week twice. Spectator
fast-forward keeps its no-routine-prompt behaviour and never grants staff
permissions. Quick Save persists staged policy data; do not create automatic
unbounded checkpoint copies or overwrite rolling recovery slots. Manual pinned
checkpoints live in a separate bounded folder, carry source/date/size and
atomic-verification metadata, and can only be restored or deleted through an
explicit user action.

Scouting Target Board cards are read-only summaries of the selected visible
identity, report freshness/status, advisory verdict and current market context.
They must not expose hidden OVR/potential, commission a report, refresh a
dossier or alter shortlist state; clearing selection must clear every card so
stale fighter data cannot remain visible.

## App performance

Every roster departure must call `vacate_fighter_belts` before changing the
fighter's name, division, champion flags or roster membership. This includes
distressed buyouts, retirement/expiry, transfers, editor moves and editor retirement.
Never clear a departed holder directly from `belts`/`interim_belts`; the lineage must
retain the fighter, date and departure reason. Dethroning through a completed title
fight remains a crown transition, not an added vacancy.

Sponsor and media offer previews are observational: refreshing either screen must
not consume RNG or regenerate offers. Sponsor pitch briefs persist and influence only
the next allowed monthly pitch. Each sponsor/media offer permits one counter; failure
withdraws it, while acceptance keeps the established contract/save field shapes.
Sponsor activation is evaluated at event settlement: unmet trust, stability or
current-month champion/top-10 campaign requirements pay half the deal fee. Ranked
campaign matching uses the stored fighter name and current roster identity. Keep
negotiation rolls injectable for deterministic regression coverage.

The J5 Testing Desk catalogue is a planning contract: provider IDs and policy
preset IDs are stable, provider comparisons expose coverage/effectiveness/
turnaround and deterministic quotes, and greater authored effectiveness costs
more for the same sample count. Persist provider/sample selection without
changing the compatibility screening resolver until confirmation, appeal,
sanction and balance rules are approved. Drug Testing Officer review may read
frozen cases and quotes only; it must not commission samples, charge cash,
consume RNG, fabricate violations, create injuries or apply sanctions.

Owner objectives are durable calendar work, not a page-refresh side effect. New
rows carry a stable goal ID, owner/company reference, explicit semantics,
baseline/target and additive boundary observations/resolution. `refresh_owner_goals`
must remain a pure projection; only the completed-week worker may record
baselines, maintenance windows or terminal outcomes, and it must run after
cards, finance and monthly business tasks settle. A repeated boundary is
idempotent and creates at most one Inbox/news explanation. Legacy rows receive
deterministic IDs and an explicit unknown-history note; never reconstruct old
weekly evidence or turn a displayed legacy success into a new failure. Use the
canonical company event count for show objectives where available. Rankings
landing cards must label matching rows separately from capped visible rows and
must not infer hidden ratings or alter ranking order.

The Promoter Dashboard's Owned Calendar is a read-only index over the existing
MMA, owned-child and player combat-sport schedules. Preserve stable event IDs,
owner/source identity, participant references, reservation counts and explicit
legacy coverage. Selecting or opening a row may show a detail reader but must
not resolve fighters, create a second schedule, rerun a card or change finance,
ownership or event state. Company, source-sport and status filters are display
only, must preserve selection by a source-bound event identity (event ID plus
owner/source), assign deterministic suffixes for duplicate rows and disclose
shown-versus-indexed counts.

Regional Prospects rating visibility must use the promotion from the current
`(promo, fighter, assessment)` row. Do not reference an outer or stale company
variable while refreshing the table. Keep spectator and Scouting Mode reads safe.
Regional prospect selection details, Scouting Target Board summaries and fighter
comparison uncertainty text are also presentation readers: call
`scouting_report_for(..., migrate=False)` and never repair/migrate the saved
scouting collection merely because a row was selected. Explicit report
assignment and sanctioned load/migration remain the write boundary.

Drug Testing Cases is an observational reader over the retained testing
envelope. Opening or refreshing its rows, summary or workflow detail must not
call the save-repairing initialiser or normalise malformed legacy case data;
return an explicit empty/unavailable state and leave repair to the sanctioned
load/migration boundary. Stable case IDs remain the durable detail key.
Company Proposal Ledger refreshes must likewise read the retained append-only
proposal collection without calling the foundation repair initialiser; malformed
history renders an explicit empty/unavailable view and proposal details resolve
only by saved proposal ID.
Storylines and Followed Briefings are presentation readers: use a defensive
subscription projection and never normalise malformed snooze/cursor rows on
open or refresh. Keep repair confined to explicit follow, acknowledge, snooze,
and unfollow mutations.
Foundation work-receipt read models must remain diagnostic when numeric fields
are malformed; render a bounded explicit zero/unknown value and preserve the
raw receipt for audit rather than repairing it during refresh.
Testing Cases table rows must resolve by saved `case_id`; duplicate IDs get
deterministic UI suffixes, id-less legacy rows use only an explicit fingerprint,
and refresh preserves the selected row without rewriting case evidence.
Talent Relations case readers and Staff contract-review recommendations must use
a defensive projection over saved obligations; page refreshes cannot repair or
rewrite malformed legacy cases. Explicit case/open, acknowledge and action
mutations remain the only write boundary.

Regional Feasibility is a read-only, scouting-aware assessment. It may summarize
current player-roster pairings, ready champion/top-10 depth, visible regional free
agents, unlocked venues and already scheduled events, but it must not generate an
invitation, quote a new price, reveal hidden AI plans/rankings, reserve a fighter or
consume RNG. A thin division is reported as a blocker; title-challenger merit rules
are never waived by the feasibility view. Refreshing the Region Hub or its review
window must leave roster, calendar, finance and proposal state unchanged. Run
`regional_feasibility_regression_test.py` for public/scouted counts, no-RNG/no-state
drift, scheduled-event filtering and the thin-division merit blocker.

Membership history is authoritative append-only data: never silently truncate
the portable collection at the 10,000-row review threshold. Report when the
threshold is exceeded and page complete retained facts for interval/as-of
reads. Any future compaction or sidecar archive requires an explicit,
recoverable, versioned policy and regression coverage.

Title challenger eligibility is checked before challenger scoring in major and
regional defenses/vacancies. Require two wins and wins >= losses or a three-win
comeback streak. Do not waive merit for inactivity, promises or shallow divisions.
Apply the three-meeting cooldown before close-bout exemptions. Keep ranking snapshots
immutable; profile matchup badges read the selected row, not today's rankings.
Development plots use stored change order (not an elapsed-time axis), and signed
driver bars share one absolute scale. Full ledger columns/details remain accessible.
Overview career-pulse meters must respect scouting visibility. Keep fatigue inverted
as readiness, momentum normalized around 50, and skill bars ordered by current value.

AI inactivity priority applies only after sporting eligibility. Keep rating/rank
limits and champion protection. Rematch evidence uses bounded ID-linked histories;
missing scorecards are unknown. Run ai_card_logic_regression_test.py and the card
inactivity regression for booking changes. Changed pairings are intentional; fight
mechanics and outcome selection remain independent of matchmaking policy.

AI card caches belong inside build_ai_card only. Preserve initial roster order,
stable sorting, used-fighter filtering and random draw order. Rebuild-status and
overall caches assume no fighter development occurs within card construction.
Compare complete cards and terminal RNG against the prior builder when optimizing.

Signature assignment must cache overall within the call: dict.get evaluates its
default even when the skill exists. Signature migration passes a lookup scoped to
one load, avoiding stale global caches. Gzip writes use accelerated json.dumps with
1 MiB encoded chunks; retain atomic replacement and cleanup on failed writes.

Fighter Search uses a 200 ms debounce and 100-row pages. Preserve access to every
match and identity-based profile resolution when changing pagination. Visible
rows use saved fighter/company identity keys, with deterministic legacy
fingerprints and duplicate suffixes; selection restores only when that same
source identity remains visible. Routine
refreshes must not redraw hidden Academy/Combat Sports pages; navigation refreshes
them on entry. Gym counts are synchronized during calendar advancement and existing
gym mutation/read paths, rather than every header repaint. Gzip saves stream to a
unique temporary file and replace the destination only after compression finishes.
Load staging uses one deepcopy memo across fields to preserve shared identities.
Calendar diagnostics retain at most 200 task timings. Run
`app_performance_regression_test.py`, persistence and UI/data regressions for changes
to these paths. Calendar tasks remain synchronous; timings do not establish that
long tasks are responsive or that a measured speedup has occurred.

Booking Workbench proposals are planning records, not scheduled fights. Generation,
review and tentative medical drafts must be deterministic/read-only: no fighter
reservation, camp assignment, cash spend, weigh-in, title credit or new RNG draw.
Tentative medical slots may show only stored return/camp facts and must remain
non-binding until the ordinary event-week medical and booking checks pass. A draft
past its target date is `Needs replacement`; a candidate who becomes available is
`Ready to confirm`, never auto-filled. Keep stable fighter IDs, preserve the stored
snapshot while re-reading current eligibility, and run `booking_workbench_regression_test.py`
for duplicate-name, stale-date, identity and no-mutation coverage.
Draft Review must distinguish preserved pairings from unresolved TBA slots. Use an
explicit booking/fight ID when one exists; otherwise label the row `Legacy reference`
and do not invent durable identity from a mutable card position. Foundation migration
assigns deterministic `booking:draft:<ordinal>` IDs to legacy draft rows (and
`booking:<event_id>:<ordinal>` to event rows), retaining existing IDs, repairing
duplicates without consuming counters/RNG, and preserving the foundation ID helper
return shape. The locked-slot editor may propose one-corner alternatives only for
complete player draft rows with a stable ID; generation/review is read-only, the
original fight fingerprint is revalidated at commit, and stale or unavailable rows
fail closed. Commit preserves title/tier/plans/unaffected corners, records a
Foundation receipt and replacement history, and is retry-idempotent. It must not
edit scheduled event fights, invent a replacement, or rerun matchmaking mechanics.
Run `foundation_regression_test.py` and `booking_workbench_regression_test.py` for
identity, duplicate, stale, no-RNG, preservation and retry coverage. The ordinary
card editor remains the mutation path for all other changes.

Fight History's archived-opponent record is an at-the-time fact. In
`fighter_history_card_context`, if neither a matching replay nor a saved
`bout_rating_history` snapshot contains that record, display `Not recorded` rather
than reading the opponent's current `record`; current records can change after the
bout. Preserve any valid historical snapshot and its identity/rank fields. Keep
legacy entries with no opponent identity as `-`, and run the profile regression for
missing-versus-valid historical evidence.
When the legacy text does not identify an opponent, a same-date snapshot is not
considered a match: multiple bouts may share that date, so the reader must not
take the first snapshot by iteration order.

Membership history is an append-only, ID-linked fact collection. Use
`record_membership_event` for real contract and roster transitions before or at the
sanctioned mutation boundary, with fighter/promotion IDs, action (`join`, `leave`,
`loan`, `return`), effective date and precision, reason, event reference and source
transaction. Its deterministic transition key must deduplicate retries without RNG
or Foundation-counter drift; `foundation_membership_events` returns defensive,
filtered pages. Contract, free-agent/automatic-TBA/last-minute signings, feeder, retirement, AI
expiry/cut, academy matching-right, editor-removal, negotiated-swap and
closed-division load/live reconciliation paths must use the hook at their mutation
boundary. Child loans and recalls record both sides of the transition (parent
loan/return plus child join/leave) before either roster is changed.
The central automatic AI free-agent signing owner must record its promotion
`join` fact before moving the fighter from the market into the promotion roster,
using a stable source transaction so retries cannot duplicate the interval.
Never infer an old join date from a current roster: the migration adapter must say
`known present at migration` and label the coverage as incomplete.
The Profile History Company Timeline and full as-of/export window must derive
intervals from these facts rather than rebuilding them from mutable rosters. Title
history remains owned by crown/vacancy helpers and is joined read-only by stable
fighter ID, with name-only legacy rows marked incomplete or left unassigned when
duplicate names make identity unsafe.

Title weight-miss decisions must be resumable from the saved pre-fight snapshot.
When `title_miss_decision_state.status` is `awaiting_player`, reuse its recorded
corner IDs and miss amounts; never roll `perform_weigh_in` again. Terminal
`resolved`, `rebooked`, `cancelled` and `needs_review` states are idempotent on
reload: retain the original evidence, do not reapply fines/vacancies or prompt a
second time, and fail closed to a cancelled/review state if an original corner
cannot be resolved. The existing player choices (Remove Belt, Rebook Fight, Keep
Belt, Cancel Fight and Last-Minute Replacement) remain authoritative; Keep Belt
keeps the title on the line. Pending snapshots retain the calculated one-time
purse fine and mark it applied exactly once on resume. This resume guard does not enable unresolved
challenger-miss policy, AI/spectator prompts or drug-testing sanctions. Run
`title_decision_resume_regression_test.py` with the title/replacement suite.

The last-minute replacement picker must apply the same title-challenger merit
owner before displaying candidates and again before commit. Ready does not mean
title-eligible: omit an unqualified challenger from a title dropdown, and fail
closed if the merit owner is unavailable. A champion-corner replacement is a
separate explicit non-challenger path; retain the title consequence in the
existing weigh-in owner. Keep company/world rank snapshots and identity-safe
replacement history unchanged. The weigh-in dialog must make this distinction
visible: qualifying challenger rows and the option count are labelled
title-eligible, while a champion-corner replacement uses a separate
non-challenger description. This is presentation-only and must not recalculate
merit, rankings or title consequences.

Company transfer and child-promotion proposals are append-only review records,
not a second ownership model. `create_company_proposal` must snapshot both
company IDs/names, every fighter ID/name/role, cash and currency, expiry or
recall boundary, terms and warnings before an explicit board/loan action.
`update_company_proposal` preserves the original snapshot while appending
idempotent status/outcome transitions; repeated terminal clicks return the
original evidence. The proposal ledger is read-only and must resolve by
proposal ID, never mutable names or list positions. Existing transfer, contract,
loan, recall and buyout handlers remain the sole mutation/finance/title owners;
stale roster, booking, title or cash checks become Needs review without
substituting another fighter. Creating or inspecting a proposal consumes no RNG,
does not change ownership and must not add an acceptance modifier or new fee.

Staff Marketing delegation has two explicit actions: `campaign_plan_review` is a
zero-spend recommendation, while `campaign_plan_commit` may run exactly the selected
existing Media campaign action only when the player has chosen Full Auto for Marketing
and committed a brief containing that action. The commit must preflight a pure quote
against the current spokesperson/target, shared action capacity and staff cash caps
before calling the Media resolver, then record its actual spend/evidence once and
qualify progression only for paid work.
Creating a brief without an action selects the safe review default, so legacy callers
cannot silently authorise spending. Missing spokesperson, stale target, failed quote,
insufficient capacity or reserve, and resolver rejection become Needs attention; never
substitute a fighter, retry a roll, or broaden Marketing authority to testing, booking,
medical clearance or title decisions. The Staff UI must make Review versus Commit
visible and preserve that action in the saved brief.

Matchmaking's `matchmaking_review` handler may reuse
`booking_workbench_candidate_rows` to return deterministic, identity-linked
alternatives with company/world rank, fit/build, hard blockers and cautions.
This is recommendation evidence only: it must not generate a proposal, reserve
a fighter, consume booking capacity or commit a card. Keep the automation flag
off until a separate player-approved booking commit handler is implemented.

Talent Relations' `contract_review` handler may include existing relationship
case rows for the selected fighter, preserving case IDs, current status and
recorded reasons. It must not open a new case, choose a support action, change
promise flags or mutate trust/morale; contract negotiation remains a separate
player-confirmed workflow.

Staff work receipts are summary cards plus a separate read-only detail view. The
detail lookup may match either the durable foundation operation ID or the
original staff work ID, and must retain the complete recommendation payload,
including identity-linked alternatives, ranking positions, blockers/cautions
and relationship cases. Opening or refreshing the detail view must not call a
handler, normalise save state, rerun a quote, consume RNG/capacity or substitute
a same-name fighter. Keep the full stored payload accessible for future fields.

Long-run audit checkpoints must scan Staff employment identity and obligations
as hard evidence: report missing/duplicate `staff_id` values (including
market-versus-employed collisions), missing roles, and invalid/negative
salary or contract terms without repairing, reassigning or consuming RNG.

Media settlement receipts follow the same pattern: summary rows remain compact,
while a detail reader may show rights delivery, production quality versus the
contracted requirement, audience outcome, sponsor duties and duty-period
evidence. Resolve by durable receipt/event ID from the saved finance block;
never rebuild history from current contracts, rerun settlement or regenerate
offers while inspecting a receipt. Preserve the complete stored payload and
explicitly show missing legacy history.
Media campaign history is also an at-the-time reader: prefer a saved
campaign/operation/evidence ID, otherwise use a content-bound legacy
fingerprint with deterministic duplicate suffixes. Preserve the selected
campaign across refresh/sort and expose its retained outcome in a read-only
detail strip; never route a campaign action through its visible row position or
rewrite the history envelope while repainting.
Media Desk spokesperson and target comboboxes must keep a source-bound fighter
map behind their display labels. Duplicate names receive deterministic visible
suffixes, selection is preserved by object/ID across refreshes, and campaign or
callout handlers resolve through the map before any name-only legacy fallback;
an ambiguous name must fail closed.
Awards/records leaderboards follow the same identity rule: retain the saved
fighter object behind each row, use its stable `fighter_id` (or a deterministic
legacy fingerprint), preserve selection through category/sport refreshes and
open profiles from that row map. Never resolve a duplicate-name athlete from
the visible name column or a sorted position.
Name-only profile, ranking-detail and rivalry readers must use the shared
`resolve_unique_fighter_name` compatibility helper. It may open a legacy link
only when exactly one saved career has that name; duplicate or missing names
remain an explicit unavailable state and must not be resolved by iteration
order.
Achievements & Milestones entries now retain `fighter_id` whenever the
achievement was unlocked for a fighter. Dedupe uses that ID for new rows,
while id-less legacy rows keep their historical name fallback; profile opens
resolve through `resolve_award_fighter` and fail closed when a legacy name is
ambiguous. The permanent ledger remains append-only and repainting the window
must not attach an achievement to a different same-named career.
Receipt table selection must use the saved receipt/event identity rather than a
mutable list index. Refreshing after a new settlement must retain the same
record when its identity is present; a legacy row with neither ID remains
visible under an explicit UI-only marker and must not be treated as durable
identity or silently reassociated.
Results landing rows should likewise use the saved result archive `record_id`
or `key` for selection and detail routing. Duplicate identities receive
deterministic UI suffixes; identity-less legacy shelf rows may use a positional
fallback only as a clearly non-durable display key.
The Staff autonomy selector must show the effective mode for its selected scope:
Company default reads the global mode, while a department reads its saved
override. Refreshes must not reset the visible scope to the global value or
apply a department edit to the wrong policy level. Selector repaint must read
the retained policy directly and must not invoke the save-repairing state
initializer; explicit policy edits remain the normalization boundary.
Staff work-receipt rows and detail routing must use the saved operation/work ID,
not a mutable list index. Preserve selection after refresh and add deterministic
suffixes for duplicate source IDs; identity-less legacy cards may use only a
clearly non-durable display fallback.
Dashboard decision-queue rows must preserve selection by a content/source-bound
read-model identity rather than a visible index. A changed source summary may
become a new notice, but unchanged advice must not jump to another action on
refresh; retain the original text, priority and route.

## Portrait catalogue version 3

Keep all 148 hairstyle IDs, 66 facial-hair IDs and palette/trait IDs append-only.
Male generation uses IDs 0..97; FEMALE_HAIR_STYLES retains its original 27 plus
98..147 (77 total). Gender belongs in rendering and the cache key. Force female
facial_hair=0 AFTER merging saved vectors and overrides, with an independent renderer
guard. Preserve the existing female non-catalogue display correction and authored
hair exceptions. Never rewrite valid complete saved identities on a version bump.
`expansion.py` supplies bounded intermediate controls: never use new raw IDs as
linear widths/lengths. Preserve original colour-family probability mass when adding
shades; country priors are broad art direction, not demographic measurements.
Run `fighter_portrait_regression_test.py`; retain all original catalogue-prefix and
v2 complete-vector pixel fingerprints. Generate/review v3 sheets with
`analysis/portraits/review_portrait_expansion.py`. Small anatomical steps can look
alike at 72px: never claim pixel uniqueness proves perceptual diversity or likeness.
See `docs/FIGHTER_PORTRAIT_EXPANSION.md` for counts, compatibility and review scope.

Optional authored `beard_colour` is a stable HAIR palette ID, not a new generated
draw. Its absence must preserve historical beard pixels and follow scalp colour;
its presence still greys with age and cannot bypass the female facial-hair guard.
Keep named display corrections non-mutating for stored identities. Reference and
review scope live in `docs/FIGHTER_PORTRAIT_NAMED_CORRECTIONS.md`.

The ranked 51–100 pass appends authored-only hair IDs 148..150 (151 total) and
burgundy dye after the original 60 dyes. Keep their generation weights zero:
98 male / 77 female generated choices and all historical draws remain unchanged.
Cristiane Justino's female presentation is portrait-only; never apply that named
correction to stored gender, division or simulation. Keep the 49 photo-reviewed
entries and Matthew Green's separate user override: pale skin, short dirty-blond
hair, blue eyes, no facial hair or dye; preserve his other traits. Retain old v3 prefixes
and non-cohort identity hashes.
See `docs/FIGHTER_PORTRAIT_TOP_100_REVIEW.md` for the 45 inspected references and
four Legend copies; these are approximate comic likenesses, not exact portraits.

The top-200 continuation lives in `fighter_portraits/ranked_101_200.py`. Keep all
100 explicit vectors display-only, complete (every identity trait except `bg`, plus
`beard_colour`) and non-mutating for stored identities. Its five archive copies
must remain independent dictionaries. Maintain the labelled top_101_200 review at
72/98/104/180px and its outside-top-200 effective-identity hash. See
`docs/FIGHTER_PORTRAIT_TOP_200_REVIEW.md`.

The top-300 continuation lives in `fighter_portraits/ranked_201_300.py`. Keep all
100 complete vectors display-only, including `beard_colour` and every identity trait
except `bg`. Maintain the labelled top_201_300 review at 72/98/104/180px and the
combined reviewed-cohort effective-identity hash. Sources guide an approximate comic likeness
only: do not download or ship reference photos, infer simulation facts, or rewrite
saved portrait vectors. See `docs/FIGHTER_PORTRAIT_TOP_300_REVIEW.md`.

## Native 440 release integration (6 September 2026)

This section supersedes earlier audit-only/default-off instructions **for the exact
accepted release recipe only**. `main.FightEmpireApp` uses
`fight_release.ReleaseFightEngineMixin`: cradle -> hold-transition -> release profile
-> legacy engine. The immutable `fight_moves/release_registry.py` profile reproduces
the accepted 440 definitions/order/fingerprint, mount successor repair and heel-hook
identity. Rejected tuning trials remain audit-only. Never enter candidate contexts,
AST-rewrite methods or mutate process-global registries during normal play.

`FightEngineMixin` and public historical registry retain the 346 reference profile.
Instance lookups and explicit registry parameters route release selection, chains,
components and labels consistently; static historical callers remain supported.
Persistence/editor/universe validation accept release IDs, and seeding/world use the
host profile. Keep all 94 added IDs save-compatible. Native kick scaling must match
the accepted combined trial's detailed `high_kick_power`/`low_kick_power` reads, not a
new global damage multiplier. Head scaling touches only the two landed base-impact
awards with actual standing head/high evidence. No extra draws/passes are permitted.

The user approved measuring the maximum-eight unused active IDs over **25,000 bouts**,
not 300. Ordinary concentration/content/chains remain at 300; identical defense clauses
remain fewer than ten per rolling 300. Raw reports retain all findings. Use explicit
composed acceptance, never erase the standard-sample absence observations. The full
3,840-bout/39-group calibration remains mandatory. Source-bound native reports and
complete-bout/RNG parity must establish integration; historical reports alone cannot.
`analysis/verify_release_integration.py` runs native bouts outside the candidate scope.
`analysis/evaluate_release_runtime.py` substitutes only disposable audit hosts. Native
hold/cradle flags enable provenance diagnostics without relying on trial-global state.
Run all six `fight_release_*_test.py` integration suites and the canonical full shipping
runner before packaging. Preserve portable Saves/Databases/Logs and launch-check both
artifacts; never shut down on a failed build or failed release check.

Legacy identity fixtures must distinguish neutral cage retention from a strong
standing-back transition and provide live knockdown/damage channels. Retirement
tests patch the host `_fight_move_registry`, not a disconnected world-module alias,
and cover both release and legacy development. Native certification retains raw
300/25,000/3,840 reports byte-for-byte. Its exact reviewed exception list covers only
the two migrated fixtures plus acceptance tests and the standalone certificate
validator; every allowed old/new hash is recorded. Source inventories and every
runtime/simulation/audit-helper hash remain exact, and both immutable calibration
reference hashes are checked. Never broaden this to ignore arbitrary test/helper
changes or reuse evidence after mechanics changes.

Every authored survived template must include both `{actor}` and `{move}`; template
count alone does not establish factual completeness. For causal `single_jab` KO/TKO,
`finish_strike_text` and `finish_sequence` reuse `exchange_display_move(causal_event)`
without changing the canonical ID, target or finish evidence. Keep real commentary
fixtures 9410906 and 9412207 in `fight_jab_wording_test.py`, and run the complete
256-bout commentary gate after wording changes.

Historical selection snapshots predate the default `portrait_version=0` and
`portrait_identity={}` fields and the expanded jab/survival/defense wording. Use the
explicit `--historical-portrait-fixtures --historical-wording` verification options
in `tools/move_selection_parity.py` only with its recognized immutable envelopes.
Reject nondefault portrait fields and unexpected renderer AST structure; retain all
other fixture fields, full trace hashes, checksums and strict comparator behavior.
New captures remain full current records/rendering. Historical scopes restore on
errors; current commentary is independently gated by the live commentary audit.

`analysis/survival_unused_diagnostics.py` scopes the paired repertoire observer to
the retained 440 candidate and records explicit current hold/style evidence. Preserve
single delegation, patch restoration, source hashes and exclusive output. Its
`fight_survival_unused_diagnostics_test.py` regression is part of the shipping suite.
In the verified standard sample, 19 of 27 absent moves have no scored/pool opportunity;
eight were offered but unselected. This is an observed-path diagnosis, not proof of
global impossibility or permission to force selection or waive the unused-ID ceiling.

Defense-clause variants in `commentary_defense_clause` use the recorded defender and
defense without inventing a counter, escape, damage or position change. Keep stable
selection and the fewer-than-ten rolling-300 repetition gate. The shipping runner
includes `fight_defense_wording_test.py` for repeated-fact and full-bout/RNG parity.
`analysis/benchmark_defense_wording.py` reconstructs the old three-clause helper by
removing the thirteen added expressions before formatting; slicing rendered choices
would retain their CPU cost. Require exact recognized AST shape, source/input/RNG
guards and full non-commentary parity. The three alternating 44-bout pairs show no
measured slowdown (2.063s/2.047s medians), not a speed guarantee. The shipping runner
includes `fight_defense_wording_benchmark_test.py` for reconstruction and parity checks.

`analysis/evaluate_joint_fight_candidate.py::reported_failures` collects every arm's
content, chain and measured-target failures before output and exit-status selection.
Retain the original per-arm lists and arm-qualified top-level findings. A successful
process exit on a frequency diagnostic does not establish release acceptance; never
ignore another failure category because measured_final_target_failures is empty.
`fight_candidate_context_regression_test.py` verifies all three arm-only failure paths,
saved/console report agreement and advisory-only success.

Single-jab wording variants belong only in exchange_display_move, using a deterministic
exchange fingerprint and SINGLE_JAB_DISPLAY_VARIANTS. Keep canonical single_jab IDs,
payloads, reads, chains and selections unchanged. Synonyms may describe a straight lead-hand
jab, but must not invent speed, power, feints, steps, stance side, target or landed outcomes.
Other authored jab identities retain their names. fight_jab_wording_test.py compares complete
audits after removing only trace commentary and asserts all terminal RNG streams match;
do not substitute extra move IDs or a presentation RNG draw for equivalent phrasing.

Named composed_survival uses at least50 authored survived templates in
evidence_driven_exchange_pool:25 standing and25 ground. Keep placeholders limited to
recorded facts (actor, defender, move, identity, after and position tail); do not invent
new mechanics or imply a successful escape. Preserve deterministic stable commentary
selection, no simulation RNG and the canonical move ID. fight_survival_commentary_test.py
counts both template pools; Fight Night and engine regressions must accept the contextual
label rather than require literal "single jab"-style wording.

The user explicitly approved 40 additional survival identities: the opt-in
--survival-expansion combined candidate has440 active moves/50 survival moves. This
supersedes the400-count target for that arm only, not normal or older candidates.
fight_moves/catalogue/survival_development.py is audit content, with immutable explicit
SURVIVAL_ROLES. analysis/survival_expansion_candidate.py filters the indexed survive
pool by actual roles and also corrects three legacy top/bottom recovery names. Missing
owners fail closed; knee-line ownership is not physical top. Retain emergency choice,
recovery amounts, skill/repetition scoring, RNG and non-survival options. Do not add
cosmetic clones, force follow-ups or claim new recovery/escape credit. Validate actual
new-ID trace roles in coverage and all full-calibration bouts. Default-off/nested/error
parity, catalogue validation and whole-bout CPU are required; no extra draws does not
prove neutral trajectories or zero cost. See docs/FIGHT_SURVIVAL_EXPANSION.md and run
fight_survival_catalogue_test.py plus fight_survival_expansion_test.py.
Detect survival validation through the scoped harness _survival_expansion_enabled flag,
not a marker on _move_candidates: the composed cradle wrapper hides method attributes.
Require selected-validation totals to reconcile with all40 new IDs; empty diagnostics
must fail if coverage contains a new survival selection. Nested trials inspect the same
class flag so wrappers cannot make an enabled trial appear disabled or stack its filter.
The verified440 candidate records19.03% concentration at300 and19.30% at3,000; all40
additions appear in3,000 with13,247 validated selections/zero invalid roles. All39 full
calibration summaries match the retained head/kick candidate. The3,000 absence list
contains four old specialist IDs; the fixed300 gate still has27 unused IDs. Preserve
this distinction. Paired44-bout CPU medians2.453/2.438 seconds show no measured slowdown,
not a guaranteed speedup. Initial coverage lacked validation activation and is superseded
by survival_expansion_440_verified_300.json, which preserves all five mechanical hashes.

Concentration diagnostics now retain per-move selection counts in joint coverage and
support --retained-damage in analysis/repertoire_selection_diagnostics.py. Count scored
eligibility separately from final-pool offers; neither proves every theoretically legal
action was considered. Capture gas/hurt before choose_action without rerunning emergency
checks; post-resolution named-selection gas is a different fact. Prove full audit and
terminal RNG parity. All ten active survive IDs account for287,295/1,107,314 selections
in the25,000-bout retained candidate, creating a25.9452% fixed-action top-ten lower bound.
No generic_survive was observed. Reweighting those IDs cannot clear25% on unchanged
action paths; changed IDs may still affect later mechanics, so this is not universal
infeasibility. Do not force attacks, pad IDs or waive the concentration gate. See
docs/FIGHT_MOVE_CONCENTRATION_PLAN.md and run fight_repertoire_diagnostics_test.py.

The user-approved --kick-power trial scales resolved kick_power by1.01 immediately
before the existing kick-margin contest. Keep kick type/target shares, kick frequency,
RNG calls, target-specific damage and all non-kick actions unchanged. The audit AST
must find exactly one kick-margin assignment and fail closed if that structure drifts;
the trial is default-off, nested-safe and restores RNG/methods. Run fight_kick_power_test.py
plus fresh full calibration and coverage. Record competitive, timing, mismatch and
coverage outcomes; do not waive other gates merely because the damage candidate was kept.

The user-authorized --standing-head-damage trial scales only landed base impact by1.02
for range/pocket jab, power punch and high kick with an actually resolved head target.
Body punches still use legacy head bookkeeping: never use damage_zone to choose scope.
Keep body/leg, clinch/ground strikes and separate knockdown bonuses unchanged. Fractional
impact preserves the small increase instead of rounding it away; downstream impact-based
knockdown/cut/stoppage checks see the scaled value. No direct probability multiplier or
new RNG draw. The audit helper AST-instruments exactly two existing damage awards and
rejects a changed two-award structure; report source hashes bind the rest of the resolver.
Production source stays untouched, scopes restore
methods/RNG and nested trials never stack. Run fight_standing_head_damage_test.py and
fresh full calibration/coverage; a benefit must not override timing or mismatch failures.
The completed 2% trial records 2,287 finishes/604 KO/734 TKO and 1,382 competitive
finishes (47.99%), but fails the exact 48% floor. The user accepted middle-timing drift as
an advisory for this trial. Keep the change experimental and disabled in normal play;
do not round the rate, raise the multiplier or waive other timing checks. Coverage still has 25 unused
IDs and 25.79% top-ten concentration. Preserve failed-candidate evidence.
The combined2% head-damage +1% kick-power calibration records2,292 finishes,
1,387/2,880 competitive (48.16%) and no full-calibration failures. Keep the kick trial
default-off until coverage passes; its300-bout sample still has25 unused IDs and25.66%
top-ten concentration. Preserve the accepted middle-timing advisory and do not infer
that clearing calibration proves content completeness or fixture-hash parity.

Audit-only --hold-transitions and --cradle-setup require experimental entries and remain
default-off. Top/guard chain identity requires an authored pair of actually dangerous
holds on immediately consecutive same-actor exchanges with unchanged round, position
and owners. Safe defenses, repeated holds, interventions, resets and horns cannot earn
it. Preserve actual technique names and transition evidence, never reroll to fit a chain.
Cradle preparation requires Catch ride intent, the existing contested control margin,
and only the existing three control points. Its next same-top side-control submission
gets one eligible crank ticket after adaptation; retain skill64, style and single-use
expiry on every actual hold draw. Creation/denial/cancellation remains generic with no
signature/mastery/chain credit. Validate both adjacent provenance paths in coverage AND
every bout of full calibration; missing or contradictory evidence is a hard failure.
The standalone helpers patch only disposable audit harnesses; reject disabled nested
scopes and restore patches/RNG on errors. Run the submission-chain/cradle tests, fresh
separate-slice and joint calibration, and whole-bout profiling before considering promotion.

The first completed submission-development trial records76 transitions/57 named chains
in3840 bouts, with all39 group summaries unchanged and competitive47.53% still failing.
Joint300 coverage has24 unused IDs, top-ten25.77%, and3 cradle roots/0uses. The900-bout
frequency run has6 cradle roots/0uses and11 unused IDs. The separate fixed240-bout Catch
cohort has61 cradle roots/0uses: preserve zeros, all hold alternatives, seeds and source
hashes rather than tune for sample use. Canonical fixtures contain no cradle roots and
cannot prove cradle-specific balance. Whole-bout800-move profiling adds2.55% CPU in this
sample; selector-only ratios omit wrappers. No universal neutrality/speed claim is valid.

The audit-only --heel-hook-identity repair reparents only heel_hook to leg_attack
and removes its counter tag; retain its knee-line position, skill 66 and all other
fields. A literal resolved heel hook may use that ID, never an inside/outside variant.
Do not enable the repair by default or rename a knee-line reversal as a submission:
counter_leg_lock still uses positional drafts and has no submission roll. The context
requires entries and restores registries/RNG through nested exceptions. Run
fight_heel_hook_identity_test.py, submission identity and leg authoring suites, then
fresh coverage and full calibration. No weights, extra draws or simulation passes are
part of this correction; isolated eligibility is not proof of sampled coverage.
Reject disabled nested contexts inside an enabled heel repair before copying the active
registry. The 900-bout trial observes three named heel hooks, reducing absences 13 to12;
the standard 300-bout sample stays at25. Full39 calibration groups match the mount base
and still fail competitive48%. Do not present extended reachability as passing the
ordinary unused-ID gate. The reports precede only the non-mechanical nesting guard;
retain their original hashes and this provenance distinction.

The subsequent 6 September user approval makes the unconditional 20–24 distinct-move
mean advisory too. Preserve its raw measurement and per-arm variety_advisories;
do not impose a replacement opportunity threshold. This supersedes older instructions
to retain that hard mean gate, not the aggregate unused-ID ceiling, concentration,
chain-share, balance, provenance or performance gates. Test both mean boundaries and
out-of-range values in fight_candidate_context_regression_test.py. Saved reports remain
immutable historical evidence; policy changes are not new mechanical measurements.

User policy on 6 September accepts attempted-chain median one for now. Keep the metric
and phase_31_advisories/chain_advisories, but remove only this median from Phase 31 and
joint hard gates. Do not remove interrupted roots or relax chain share, variety, unused
IDs, concentration, balance, correctness or performance. Historical reports remain intact.
analysis/repertoire_opportunity_cohorts.py derives cohorts from saved mount observations;
it performs no simulation. Preserve both fighter-bout slots including zero selections,
registry agreement, observed mean reconciliation and input hashes. Final-pool matching
is a fixed-path bound, not universal infeasibility. A move never offered in a final pool
is not proven illegal or unreachable. Do not automatically waive variety targets based
on these cohort results; propose policy separately. Run fight_repertoire_cohorts_test.py.

The audit-only --boxing-chain-pool trial filters only jab/power-punch action demand
against a pure current-state final-pool preview. Original preview still validates live
chains first; final resolution may change eligibility, so this is not guaranteed follow-up.
Preserve authored/counter priorities, score arithmetic, target fingerprints, static/rarity
gates, integer budgets and all alternatives. Initiative, caps and final selection stay
unchanged. Reject incompatible active nested tuning as well as same-call flags. Use
fight_boxing_chain_pool_test.py and fresh full calibration/coverage before promotion.
analysis/benchmark_boxing_chain_pool.py counts boxing_pool cumulatives separately from
select_exchange_move, then sums these disjoint paths; selector-only ratios hide added work.
analysis/chain_selection_diagnostics.py --gift-wrap-mount refreshes the base observer.
Do not use its captured raw preview bonuses as filtered-trial telemetry: its hook observes
the original preview before this action-only filter. The refreshed base has 4,667 roots,
1,522 completions, 961 positive-preview other-action losses and 37 authored-priority losses.
The pool-aware boxing trial records 1,548/4,656 coverage roots, variety16.5333 and chained
share20.62%, but median remains one and unused IDs rise to26. Full3,840/39-group calibration
records2,267 finishes /598 KO /727 TKO and competitive47.33%, worse than the mount base.
Timing passes. Do not promote based only on increased completions; retain both reports,
the mount-refined base, all acceptance failures and default-off status. The actual-bout
test at coverage seed9330000 R1tick18 observes authored Muay Thai priority over one_two
without changing the observed trial's complete audit or terminal RNG.
The boxing_pool_800 benchmark records combined selector/preview share12.27% versus
control10.74%, within15%; selector-only10.41% hides new work. Profiled44-bout CPU rises
9.45 to10.66 seconds with changed trajectories. Do not call this zero simulation cost
or a whole-career speed guarantee. Keep the rejected policy default-off.

analysis/jab_timing_diagnostics.py compares mount versus mount-plus-jab on the exact full
calibration schedule and requires both sets of all canonical groups to reproduce saved
calibration evidence. Keep Early/Middle/Late relative to scheduled rounds, and Nonfinish
separate. Distinguish new/lost finishes from earlier/later finishes; a timing failure is
not proof of delayed stoppages. First named, mechanical and plan differences use actual
exchange facts, retaining unequal trace tails. Preserve input/source/registry hashes and
RNG; output is exclusive. Run fight_jab_timing_diagnostics_test.py. Disabled tactical
plans cannot explain frozen-corpus changes; selected IDs can alter chains and reads.
The completed pair reproduces all 39 groups and finds 25 gained/15 lost finishes, with
five later-period and three earlier-period finishes. Do not call this a general delay.
The original full report has prototype divergence labels: use its timing totals, not
its tail-based plan claims. Corrected --recheck-changed validates unchanged combat
sources, complete parent groups/schedule, and exact fresh audit/RNG hashes for all 75
changed method/round/winner bouts. It is not a new calibration or an account of unchanged
outcome paths. mechanical_projection is explicitly partial and retains triggering values;
tails are lengths, and plans compare only aligned actor/round/tick facts. Root-event
move_sequence.branch_options describes the prior chain, not the new root's successor map.

`--jab-readaptation --gift-wrap-mount` isolates earlier independent-jab repetition scoring
on the mount-refined candidate. Preserve the existing curve/cap, all live continuation
scores and every non-jab score. Enabled nested filters must agree, never stack or silently
inherit a different scope. The broad trial remains separately selectable and mutually
exclusive. Run fight_repertoire_readaptation_regression_test.py and fresh full calibration;
named selection can change downstream mechanics despite adding no RNG draws.
The full mount-plus-jab trial records 2,285 finishes / 605 KO / 719 TKO and competitive
47.92%, but adds a middle-finish timing failure. Coverage variety is only 16.45, with
25 unused active IDs and 1,511/4,666 completed roots. Do not promote it based on the
headline finish gain. The separately reproduced historical selection regression differs
only in all 44 fixture hashes; mechanics/trace/payload/count hashes match. Investigate
fixture provenance without rewriting references or claiming the shipping suite passed.

Current user policy supersedes older fixed300 named-content blocking rules: partition the
four known phase/slice named-move absence messages into content_frequency_advisories. Do not
discard observations or weaken unknown/structural failures, aggregate unused-ID ceilings,
variety, chain, correctness, balance or performance targets. Historical artifacts stay immutable.
analysis/repertoire_selection_diagnostics.py observes actual named selectors on the mount-refined
candidate, retaining every exchange and comparing full audits/terminal RNG against control.
Near unseen alternatives must belong to the final pool, not just the eligible registry; multiple
alternatives for one exchange are overlapping opportunities, not additive recoverable variety.
Run fight_repertoire_diagnostics_test.py for policy and observation regressions.

The mount-refinement scarf investigation found no demonstrated selector bug: coverage bout117
(seed9600002) no longer creates its three scarf setups after R1 tick11 takes a different mount
action. Its side-control occupancy falls13 to2. All other14 scarf observations match exactly,
including positive prepared shares in all eight uninterrupted menus. Do not force the old hold,
extend setup expiry or infer an eligibility regression from missing rare sample coverage.
Keep fixed300 content failures separate from any longer frequency diagnostic. See
docs/FIGHT_SCARF_COVERAGE_INVESTIGATION.md;29 focused setup/prepared-diagnostics tests pass.
analysis/gift_wrap_mount_scarf_frequency_900.json extends the identical combined schedule:
76 scarf roots reconcile to3 context changes,24 interventions,24 other actions,23 other
holds and2 uses. First300 prepared observations exactly match the prior refined report.
Long-run content reachability does not replace the fixed300 sample or any full calibration,
variety or chain gate. Do not present the absence of content failures at900 as release acceptance.

analysis/gift_wrap_mount_candidate.py tests --gift-wrap-mount independently of the broad
--gift-wrap-control trial. It changes only the mount hammerfist edge to high_mount_arm_pinch,
retaining rear_naked_choke/body_triangle_back_control and exactly three declared successors.
Do not silently add a fourth branch or remove ordinary hammerfist legality. Strictly validate
the replacement's mount-only source, complete DAG, context restoration and incompatible flags.
The preceding paired 300-bout trace probe found nine first divergences in back-control named
selection; coverage bout21 lost a R3 submission to a decision under the broad hip replacement.
Bout117 lost scarf coverage after a mount action divergence, not a back-control identity swap.
These are coverage-corpus attribution facts, not explanations of all full-calibration changes.
The completed mount refinement records2,275 finishes /605 KO /725 TKO across3,840 bouts and
39 groups; competitive47.53% is its sole calibration failure (floor48%). Timing passes.
Root completion22/58 and retained nine body triangles improve the local tradeoff, but overall
roots1522/4667, median one, variety16.4183, top-ten25.67% and25 unused IDs still fail coverage;
scarf_hold_straight_armbar remains absent. Keep --gift-wrap-mount as an explicit experimental
continuation point, not a production/default promotion. Do not call a positive local gain
full acceptance or infer all full-corpus outcomes from coverage bout21's recovered submission.

analysis/gift_wrap_control_candidate.py is the single-root --gift-wrap-control trial.
Only gift_wrap_transition's third successor changes from body_triangle_back_control to
hip_pressure_ride; retain strikes/choke branches, three-option limit, immutable IDs and
full-DAG validation. The verified live audit records six undeclared mount-control choices
among 58 attempted roots; these are opportunities, not guaranteed extra completions.
Measure displaced back-control completions and fresh full calibration/coverage before
promotion. Default off; run fight_gift_wrap_control_candidate_test.py for strict drift,
single-definition, nested/error restoration and source-immutability boundaries.
The completed gift-wrap trial is rejected for promotion: root completion improves 17/58 to
26/60, but all-root completion is only 1532/4677, median one, variety16.4367, top-ten25.71%
and 25 IDs unused; scarf_hold_straight_armbar also disappears. Full3,840/39-group calibration
has 2267 finishes /608 KO /725 TKO, competitive47.19% and middle timing failures. Retain
artifacts/default-off status, not the replacement in the default candidate. Bout60 proves
actual mount hip-pressure follow-through; changed root counts are not recovered fixed cases.

analysis/continuation_commitment_candidate.py is opt-in via --continuation-commitment.
It rescales returned positive action bonuses into a probability-bounded demand mixture
(q <= 0.5), only at gas >=42 and below the existing hurt guard. The original apportioner
runs once and prepared intent still combines by max. Initiative remains unscaled; no legal
option, expired root or named identity changes. Reject combining with stronger-continuation.
Require fresh five-arm coverage and complete calibration; the trial is not a shipping fix
until acceptance. Run fight_continuation_commitment_test.py for pure-mixture math, budget,
readiness, nested/error restoration, prepared-only parity and normal full-bout parity.
The first probability-commitment trial is rejected: full 3,840/39-group calibration records
2,269 finishes / 614 KO / 734 TKO, competitive 47.05% and early/middle timing failures.
Coverage chained share 21.88% does not pass median one, variety 16.0717, top-ten 25.98%
or 24 unused IDs. Keep it opt-in; do not treat the policy as the new default candidate.
Von Flue angle provenance must accept proven forward round changes as boundaries even when
the trace has exchanges only. Clear validator pending state, never runtime setups or chain
denominators. Reject stale facts after the boundary and malformed/backward round values.
The natural reproducer is coverage bout177, seed9320004, low-competitive-2, R2 tick18 under
the probability-commitment trial. Its pending wrap correctly expires before R3 tick1.

analysis/chain_selection_diagnostics.py observes actual calls only. Copy chain bonuses before
prepared intent mutates them; ignore initiative previews outside choose_action. Scope static,
rarity and pool observations to actual named selection. Preserve the established round-two root
denominator and retain every interruption. Positive preview probability is conditional on the
observed menu, not guaranteed final eligibility or a counterfactual win. Each bout must match
full control audit and all terminal RNG streams; preserve inputs/registry and reject source drift.
Run fight_chain_selection_diagnostics_test.py when changing these hooks. Keep all tooling outside
production state and never package the candidate on diagnostic success alone.
Apply resolved-hold compatibility only to submission parent actions: other actions carry empty
technique payloads. The authoritative chain_selection_verified_300 report supersedes both live
prototype reports (the resolved prototype misclassified non-submission payloads). Its 196 named
losses include 86 actual hold mismatches, 49 initial-context absences, 36 authored-priority losses,
11 ordinary-pool exclusions, four losing pool draws, five static/rarity rejections and five
remaining post-context absences. Do not call all 196 ranking failures or infer that positive
previews in 968 different-action cases guarantee final named eligibility.

analysis/repertoire_readaptation_candidate.py is an opt-in trial for one earlier repetition
exposure on independent named selections. Retain the base adaptability curve and 14-point cap;
live legal chain candidates keep the original score and sequence bonus. No new eligibility,
counter, signature or action-weight rule is implied. Run --repertoire-readaptation through the
joint evaluator, preserve default control arms and source hashes, and recalibrate the full
corpus: changed selected IDs are not inherently presentation-only. Never pad survival chains.
The completed readaptation trial is not accepted: 2,267 finishes / 611 KO / 715 TKO,
competitive 47.26% and middle timing failures across all 3,840 bouts/39 groups. Coverage
variety 17.1833 is an improvement, not a pass; median one, top-ten 25.53% and 23 unused
active IDs remain failures. Default control arms match specialist_style exactly and trial
normal/content-only/entries arms match that control. Keep the helper opt-in and retain both
coverage reports and full calibration; do not substitute improved variety for release acceptance.

The user has now approved testing stronger continuation above +2, not promotion or relaxed
acceptance. analysis/continuation_strength_candidate.py scales the existing legal action bonus
by 2 (maximum +4), only inside _chain_action_weights. Initiative previews remain unscaled;
prepared readiness combines by maximum after scaling and is not itself doubled. Preserve
skill/gas attenuation, ticket totals, every legal alternative, survival and expiry. Contexts
must not stack and must restore class/instance overrides and RNG on error. Use evaluator
--stronger-continuation; keep default candidate unchanged and retain fresh full calibration,
five-arm coverage, source fingerprints and every failure before considering any promotion.
The first +4 stronger_continuation trial is rejected for promotion: 2,289 finishes / 626 KO /
727 TKO across 3,840 bouts and 39 groups; competitive 47.47% with mid tier 44.48%, middle timing
drift and no sampled doctor stoppages fail calibration. Coverage chain share 21.47% improves,
but median stays one, top-ten worsens to 27.05% and 23 active IDs remain unused. Retain artifacts
and do not call zero sampled doctor stoppages proof of universal impossibility. The default
five-arm control exactly matches specialist_style coverage; the stronger helper stays opt-in.

Use docs/FIGHT_RELEASE_CHECKPOINT.md to distinguish verified regression health from candidate
acceptance. The full shipping run and post-style affected reruns passed; the smoke click-selection
probe was skipped for display layout. The specialist_style_combined_800 selector benchmark passes
at 10.88%, not a whole-career speed guarantee. Keep the audit-only scope of cap approval and candidate
failures visible; automatic goal continuations alone are not approval to change design constraints.

specialist_style_weights reuses ordinary top-style factors for genuine physical-top turtle
and front headlock only. Apply it after survival overrides, before specialist_plan_weights
and chain apportionment. Policy aliases are not new actions; preserve original menu keys/order,
primary/secondary style semantics and default-off parity. It is independent of enabled plans.
Never apply physical-top policy to leg knee-line ownership or expand the continuation cap.
Run fight_specialist_style_regression_test.py and fresh full calibration after changes here.
The specialist_style full candidate retains 3,840 fights/39 groups: 2,272 finishes, 606 KO,
725 TKO; competitive 47.40% still fails. Five-arm coverage preserves normal/content-only/chains
mechanics while entry arms change. Distinct 16.4117, chain share 20.18%, attempted median one,
top-ten 25.65% and 24 unused active IDs are mixed evidence, not complete acceptance.

candidate_context(entries=True) corrects fence_drive to the failed-shot pre-selection position.
force_cage is a controller action from failed shot, not a clinch/cage action; do not confuse
the resolver's cage destination with move eligibility. Preserve the stable ID and all other
fields, default-off registry identity, nested/error restoration and fresh candidate calibration.
The fence_source coverage artifact retains identical mechanics in all five arms, but substitutes
overhook_shoulder_fence_drive for fence_drive in the 23-unused list. Do not report this as a net
variety gain or force named tickets to eliminate the remaining sparse-sample absences.
Fresh fence_source calibration has 2,269 finishes / 604 KO / 724 TKO across 3,840 bouts and
39 groups. Competitive finishes at 47.26% remain its sole calibration failure. The unchanged
300-bout mechanical signatures did not imply full-corpus neutrality: one finish changed.

Candidate final-target reporting must cover the entire active registry: no more than eight
unobserved active IDs in the fixed 300-bout sample and at least 200 active moves with follow-ups.
registered_move_inventory excludes deprecated entries and cannot treat generic/unknown payloads
as registered coverage. Keep draft-only counts separately; two missing drafts do not establish
the total unused-move target. Older artifacts without the full inventory cannot prove that gate.
The complete_inventory five-arm report exactly preserves prior mechanical signatures. It finds
23 unused active IDs (including two drafts), failing the maximum eight, while 363 active moves
with follow-ups pass the 200 floor. Treat this as exposed missing evidence, not mechanical drift.

Candidate sequence creation passes independent_alternatives=True explicitly to the static updater.
Multiple legal successors have no designated next_move_id and are labeled legal-alternatives;
only a sole legal successor is designated. Create/count roots from nonempty legal_branches,
never from the optional designated ID. Selected defense tags do not prove a reaction, especially
when the attack landed. Preserve legacy behavior by default and all expiry/interruption accounting.
Fresh independent-continuation calibration retains 3,840 bouts/39 groups: 2,268 finishes,
604 KO and 724 TKO; competitive finishes 47.22% still fail. Coverage records distinct 16.4833,
chained 20.12%, attempted median 1 and top-ten 25.78%; two leg drafts remain unobserved.
The sparse graph trial is disabled in these measurements. Six provenance regressions cover
real recorder integration, alternative selection, legacy parity and all interrupted-root cases.
The fresh independent_continuations_combined_800_selector_benchmark.json passes at 10.89%
median selector share (three 44-bout samples); it is not a whole-career latency guarantee.

analysis/continuation_branch_candidate.py is an explicit audit-only sparse-root graph trial,
enabled through candidate_context(continuation_branches=True, chains=True) and evaluator
--continuation-branches. It adds alternatives to thirteen roots without replacing prior branches,
changing IDs or increasing the registry count. Preserve ordered immutable definitions, idempotent
nested application, duplicate rejection, full-DAG validation and the three-successor limit.
Default candidate and production graphs remain unchanged. The 84 observed extra action cases
are an optimistic fixed-path opportunity count, not predicted completions or median-two acceptance.
The sparse-branch trial records 2,270 finishes / 604 KO / 720 TKO and competitive 47.19%.
Coverage raises chained selections to 20.77% but lowers variety to 16.395, raises top-ten share
to 26.18% and leaves seven draft IDs unobserved. Keep this tradeoff opt-in, not the default candidate.
The fresh default five-arm control is exactly unchanged from the counter-fallback report.

Prior post-counter-fallback artifacts retain all 3,840 fixtures/39 calibration groups and five
300-bout coverage arms: 2,267 finishes, 604 KO, 723 TKO; competitive finishes 47.19% still fail.
Coverage distinct 16.4483, chained 20.20%, attempted median 1 and top-ten 25.70% retain their failures.
Only entangled_outside_heel_hook and entangled_rolling_kneebar draft IDs are unobserved; actual
controller pools and identity mappings support both. Five leg attacks cannot establish broken
eligibility or justify forced selection. Keep the earlier isolated reports for attribution.
analysis/counter_fallback_combined_800_selector_benchmark.json was collected by running the
existing benchmark inside candidate_context(entries=True, chains=True, draft_content=True),
importing its benchmark module inside that context (400 originals expanded to 800). It passes
the selector-share gate at 11.06%; distinguish this profiled ratio from total career latency.

Dirty-boxing chain lanes must reflect actual target resolution: misses retain head; only the
landed knee weapon changes the target to body. Use the shared cleaned weapon tickets and exact
discrete contest probability, including Erratic outcomes, without consuming RNG. Preserve the
real resolver draw order and final selector independence. Multiple successors in one target lane
are overlapping opportunities, not additive bonuses. Collect fresh full calibration after edits.
The chain experimental flag also resets last_actor/actor_streak before both new-round initiative
calls. Keep the existing within-round comeback branch intact, including its RNG. Test chains-only
and joint contexts plus default-off complete-bout parity with fight_round_streak_reset_test.py.
Do not use clinch-preview measurements as evidence for the subsequent round-streak candidate.
In chain-enabled _move_candidates, keep ordinary style combinations until final static/rarity
eligibility is known. Only _select_from_pool's surviving counter rows establish counter priority;
an empty or rejected counter lane must retain ordinary fallback. Keep default-off filtering and
style ownership gates unchanged. fight_counter_fallback_regression_test.py proves rejected-counter
fallback, valid-counter priority, preview/final agreement and complete-bout legacy parity.
The prepared-diagnostics natural scarf fixture is pinned to coverage bout84/style-coverage-9,
seed9710001, R1 tick15 after counter fallback. Retain nonempty observations and exact audited
trace/result/RNG parity; do not turn a disappeared setup into a vacuous passing assertion.

Bottom-guard entry intent is chosen before the existing sweep contest, candidate-only and with
leg skill >=62. Strictly compare leg/scramble/flexibility against bottom-control/transitions/strength;
ties retain the sweep. Cap the entry contest adjustment at two, with no extra draw. Successful
entry assigns knee-line ownership, never sweep, takedown, submission or physical-top credit.
Half guard is excluded. Keep generic_bottom_leg_entry identity and explicit bottom_leg_entry
trace provenance, cleared next exchange/horn. The coverage observer rejects missing facts and
false credit; run fight_bottom_leg_entry_regression_test.py and fresh full calibration before promotion.
The bottom-guard-entry artifacts retain all 3,840 fights and five coverage arms: 2,255 / 593 / 700,
competitive 46.98%, three coverage entries and eighteen leg exchanges. Eleven draft IDs remain
unobserved; do not call the new route sufficient specialist coverage or package this failing candidate.

`fight_moves/specialist_intent.py` maps physical-top turtle/front-headlock action keys to
existing top-plan policy keys only for lookup. Preserve original menu keys/order, enabled-plan
checks, finite clamped execution, actual ownership and survival precedence. Apply once before
chain apportionment, never as an added action or damage multiplier. Do not alias knee-line or
standing clinch control to physical top. `fight_specialist_plan_regression_test.py` covers both
slots, plan direction, disabled/default parity and the real menu hook. Fingerprint new policy
modules in candidate reports and reject edits during collection.
The frozen fixture schedule does not enable tactical plans. Natural-bout enabled-plan tests
prove that integration; unchanged frozen counts are not evidence of its balance benefit.
The combined near-score repertoire trial records 2,254 / 594 / 701 and passes timing, but
competitive finishes remain 46.91%, distinct variety 16.3367 and attempted median one.
Do not promote the tradeoff or hide the eleven unobserved drafts behind its small variety gain.

`fight_moves/selection_pool.py` is the shared pure ordinary pool builder for the candidate
selector and variety observer. Preserve top-five continuation priority before adding up to
three ordinary near-score choices (6.6 points from the best, maximum eight). Extra low-ranked
successors do not acquire forced chain preference. Authored singleton and eligible-counter
priority stay earlier. Default-off keeps the original five. Earlier fixed-five observer notes
remain applicable to legacy mode; candidate instrumentation must pass expanded mode explicitly.
`fight_repertoire_pool_regression_test.py` covers boundaries, priorities and actual selection.

Experimental repertoire anti-repetition pressure must not weaken as adaptability increases.
Retain the existing repeat threshold and 14-point cap, candidate-only chain switch and exact
legacy default-off formula. The actor's selection penalty is not an opponent defensive bonus.
`fight_move_adaptability_regression_test.py` protects monotonic direction, cap, unrelated
score components and parity. Named choices affect later mechanics; collect fresh complete
calibration and coverage rather than calling this a presentation-only adjustment.
The knee-line correction leaves all five coverage arms and full canonical groups unchanged.
The subsequent adaptability correction records 2,262 / 587 / 712, 47.19% competitive finishes,
16.23 distinct moves and 1,501/4,620 completed roots. It does not solve the remaining gates.
Keep both fresh calibration artifacts and their matching coverage reports; do not cite the
older counter-cadence measurements as evidence for this revised candidate.

Experimental `leg_escape` defence in leg entanglement must use the defending knee-line
owner's leg_locks, positional_ability and discipline with grappling, not generic bottom-game
escape expertise. Gate by actual defending ownership and preserve legacy default-off,
other-action and other-position arithmetic. Keep the existing coefficient total, thresholds
and random draws. `fight_leg_escape_defense_regression_test.py` protects skill direction,
both slots and default parity. Do not claim longer residence without fresh ordinary-fight
coverage and full balance calibration.

## Current finish-balance policy — supersedes exact-count instructions below

The user approved close historical finish rates rather than identical totals. Keep the frozen
3,840-fight schedule and all reference artifacts unchanged. `RESULT_RATE_TOLERANCE_PP = 2.0`
in `fight_engine_audit.py` bounds overall finish, KO and TKO rates against historical evidence;
the accepted comparator uses unrounded count-derived rates. The older baseline comparator uses
the same two-point headline tolerance. Retain its subgroup, family and timing protections,
competitive 48–54% finishes, competitive submission 15–19%, rare stoppage reachability and
five-round late-finish minimum. Exact trace parity remains mandatory for neutral refactors.
Earlier requirements to reproduce 2,319 / 633 / 731 exactly are historical and superseded only
for balance acceptance, not permission to force results, overwrite references or package a
candidate failing remaining gates. A policy-only reassessment of saved measurements is not
fresh mechanical calibration. Move variety, chain, legality and performance targets stay intact.

`analysis/round_counter_expiry.py` is a default-off, audit-harness-only boundary trial.
Before the first initiative score at tick one, clear only a counter with a proven positive
integer creation round older than the current round, and only in the joint entries/chains
candidate. Both fighters must see the cleared window; current-round age semantics remain
unchanged. The initiative hook substitutes for a missing round-start state hook, not a new
production lifecycle API. Preserve single delegation, zero extra RNG and nested/error
restoration. Require real-bout lifecycle coverage, default-off parity, complete calibration
groups and five-arm coverage before considering promotion; do not package a failing trial.
The round-expiry trial records 2,257 finishes / 586 KO / 708 TKO versus the control's
2,264 / 586 / 714: fixing this lifecycle alone does not recover the finish deficit.
Coverage CLI failures live inside each arm; aggregate their content, chain and measured-target
failures explicitly for display and exit status. Hash coverage/provenance builders as well
as mechanics so changed audit interpretation cannot share a source fingerprint.

The move-upgrade user has approved joint Phase 31 chain and Phase 34 specialist development.
The old sequential prerequisite in `docs/FIGHT_MOVE_SYSTEM_PLAN.md` is superseded only for
implementation order. Isolate and measure each mechanical slice; retain all final acceptance
targets, immutable references and locked 3,840-fight finish counts. Do not present pre-change
measurements as evidence for a new mechanical candidate or package a failing candidate.
`_experimental_specialist_entries` is an audit-harness-only opt-in for the unfinished entry
candidate. Do not persist, enable through the player UI or default it on before acceptance.
Use `analysis/evaluate_specialist_entry_candidate.py` for its read-only calibration; a failed
candidate audit is not a reason to loosen the canonical shipping runner.
`analysis/fight_candidate_context.py` is the single-threaded, disposable audit context for joint
chain/specialist trials and their draft catalogue. Pass its definitions explicitly to coverage
functions: Python default arguments otherwise retain the original registry and misreport candidate
pools. Restore every facade/engine binding and private flag on exit, including nested/error paths.
The joint evaluator's optional output uses exclusive creation; diagnostics cannot replace release
references. Coverage-arm success alone never establishes finish-calibration or full-plan acceptance.
Full candidate calibration artifacts retain all canonical groups as well as the headline summary.
`--coverage --combined-only --fights N` extends the identical combined-arm seed/spec schedule for
frequency investigations without rerunning unrelated arms. Keep its diagnostic scope explicit,
retain all content/variety failures, and reject `--combined-only` without `--coverage`; it cannot
shorten or replace calibration. Compare the default five-arm report before attributing any change
to diagnostic instrumentation.
Prepared-submission instrumentation belongs to `analysis/prepared_submission_diagnostics.py`,
not production fight state. Observe the returned action menu without rerunning apportionment;
snapshot pure technique tickets before the actual choice consumes setup. Reset observations per
bout and retain seed/spec identity when aggregating. Conditional expected-use sums describe the
observed paths only: missing menus are unknown, opponent interventions and emergency survival are
separate, and failed roots at horns/context changes remain in the existing trace follow-through
report. Preserve exact trace/result/RNG parity and do not tune weights to force a tiny sample's use.
Reconcile observations and summary counts with eligible trace follow-through roots by setup kind;
an empty diagnostic object cannot pass when the trace contains opportunities. Cancelled setups,
context changes and terminal boundaries are not live choice opportunities. Repetition acceptance
is fewer than ten identical clauses per rolling 300 bouts, not per arbitrarily long run. Keep
aggregate totals separate and test expiry, historical peaks and windows crossing block boundaries.
`analysis/compare_candidate_striking.py` compares current normal with the combined candidate on
identical fixed fixtures. Its significant-strike deltas belong to the acting fighter; damage
deltas are received, while knockdown deltas are scored and require recipient inversion. Label net
hurt changes honestly and do not infer unrecorded pressure resets or stoppage checks from result
names. Keep input/source/registry/trace hashes, RNG/input purity, exclusive output and the guard
against source changes during collection. Run only after mechanical edits settle.
Its finish cohorts come only from recorded exchange stoppages, knockdown deltas and final methods.
Keep bout-level knockdown-to-KO/TKO cohorts separate from exchange/action/position partitions;
never infer that every KO/TKO requires a knockdown. The complete current comparison has 1,452
normal versus 1,384 candidate bouts with a knockdown, 883 versus 819 of those reaching KO/TKO,
and an identical 481 KO/TKO bouts without a knockdown. Target lost knockdown opportunity before
changing post-knockdown stoppage logic.
Style and quality cohorts must each partition every exchange exactly once. Use the recorded actor
style, settled pre-exchange position, post-action gas, actor streak and real counter flag; do not
reconstruct them from final fighter state. The deficit is concentrated in high-gas standing work:
candidate high-gas kicks lose 759 exchanges and 81 knockdowns, while 437 extra high-gas power
punches still lose 17 knockdowns and 27 finishing exchanges. Do not apply a tired-fighter fix.
The comparison's `--calibration-corpus` mode uses the real baseline builder's complete fixture
schedule and canonical groups, not the move-coverage schedule. Reject simultaneous `--fights`;
verify all fixture names/seeds/configurations/order and group memberships against `build_baseline`.
Opposite directions in small move coverage and full calibration are evidence of corpus sensitivity,
not justification for a global damage multiplier.
The paired tool's optional standing-chain ablation bypasses `_chain_action_weights` only for
range/pocket in the second combined-candidate arm. Keep the patch scoped and exception-safe;
all other positions delegate unchanged. It must not disable named chains, specialist mechanics,
ground prepared-submission intent or alter production defaults. Treat outcomes as attribution
evidence, not acceptance of removing standing combinations.
Its mutually exclusive pocket-action-bias ablation disables only the candidate pocket menu's
1.10 power-punch, 0.85 kick and 1.05 clinch factors. Keep the flag audit-scoped, nested/error safe
and default-on inside the unchanged combined candidate. The full ablation reduced candidate
finishes from 2,264 to 2,258 and KO from 586 to 574 despite 11 more knockdowns; do not remove the
preference or mistake raw knockdown count for calibrated finish recovery.
Keep both failure comparisons and the reference corpus unchanged; detailed group output is
diagnostic evidence, not permission to average away a competitive-tier or locked-count failure.
The paired tool's `--failed-shot-retention-ablation` temporarily applies the legacy entry switch
only inside `resolve_takedown`, where the sole switch read controls denied-shot retention after
successful/cage branches. Preserve that narrow scope if the resolver gains other switch reads;
the ablation must not disable unrelated specialist behavior. Restore instance overrides, class
methods and RNG through nested/error paths. The nested `set_fight_position()` call must retain
the original entry flag so pending/ready submission setups still invalidate normally. Standing exits use settled trace destinations;
zero-takedown standing shots include cage progress and must not all be called failed attacks.
Require identical control-arm traces and complete canonical groups before using an ablation for
attribution. A benefit would justify investigating retention/escape intent, not deleting states.
The full legacy-retention ablation reaches 2,279 finishes / 609 KO / 724 TKO versus the
candidate's 2,264 / 586 / 714, but removes all failed-shot residence and still fails calibration.
All 23 extra KOs are mismatches; total knockdowns change only 1,661 to 1,662. Do not present
this as competitive KO recovery or accept disabling the specialist state. Retain both arms
and investigate intent-sensitive escape choices without dropping legal options.
`analysis/standing_counter_diagnostics.py` observes each actual initiative call once. Its denominator
is calls for both fighters, not exchanges. Keep previous-round and same-round age>2 observations
separate and retain no-window/unknown bins. Gas/hurt readiness does not establish an available
legal chain, so an opponent-window guard hit is not a measured lost initiative bonus or attack.
Preserve complete-bout trace/result/RNG parity and keep this instrumentation outside production.
The audit-only `analysis/failed_shot_escape_intent.py` applies a 1.58 disengagement demand factor
only to a Sprawl And Brawl fighter controlling a failed shot. Apportion the existing cleaned
integer budget with one ticket per alternative, then delegate normal chain weighting. Preserve
action order, survival overrides, default-off full-bout parity and non-stacking nested contexts.
Its full calibration retains every canonical group and failure; a passing coverage sample is
not evidence that this preference improves finishes or is ready for normal play.
The complete escape-intent trial records 2,265 / 591 / 714, versus 2,264 / 586 / 714 for the
control. Its 300-bout coverage arm and mechanical signature are exactly unchanged. Retain this
small outcome gain as audit-only evidence; competitive finish rate remains 47.26% and all final
calibration/content gates still apply. Do not call it an accepted replacement candidate.
`_chain_action_weights` previews candidate eligibility only after survival overrides and ordinary
style/plan modifiers. Counter preview must use the current counter window, not the previous
exchange flag. Preserve cleaned integer ticket totals, action order, two-tick expiry and failed-root
accounting; final named selection remains independent. The experimental switch defaults off.
Continuation intent now uses action-specific coordination, adaptability and discipline, attenuated
by gas. Its bonus is capped at 2 before integer apportionment; it never creates a legal action,
rescues a failed rarity/style/skill gate or changes the total draw range. Do not achieve chain
targets by removing interrupted roots, extending expired chains or forcing named successors.
Experimental standing cadence reuses the current legal chain preview for the five ordinary
range/pocket actions, contributing at most two initiative points without another RNG draw.
Suppress it below gas 22, above the existing hurt threshold or against the opponent's current
counter window; gas attenuation reaches full strength at 60. Non-standing positions get no bonus.
Preserve the existing initiative roll, actor-streak comeback handling and authoritative survival
overrides. Zero extra draws does not imply unchanged candidate trajectories: test default parity
and run fresh full candidate calibration after changing cadence.
For current actor-owned counter windows, continuation previews must respect the selector's
eligible-counter preference. Apply the same static/rarity/signature exclusions before deciding
that a counter alternative exists; ordinary branches in that lane then receive no opportunity.
Do not blanket-reject ordinary lanes without eligible counter moves. Equal-initiative tests must
explicitly equalize form/context and prove equal baseline scores, not depend on random setup luck.
Named-selection changes are not automatically presentation-only: selected IDs feed chain state
and move-read-based plan adaptation. Even a deterministic sampler with no extra RNG can alter
later actions and finishes. Require complete-bout mechanical evidence before claiming neutrality;
only alternate wording for the same factual move is inherently a presentation-only change.
Do not infer defensive reaction semantics from follow-up tuple indexes or a selected defense's
tags. A selected defense can be breached on a landed/knockdown/takedown result, and tuples encode
legal alternatives rather than universal primary/evasion/block lanes. The independently chosen
next action already allows any matching legal branch; add explicit authored provenance before
labeling a branch as reaction-driven.
Variety-opportunity diagnostics use maximum bipartite matching from observed exchanges to final
legal move IDs. Reconstruct the exact counter/authored/strongest-five/chain-preferred pools;
unwrapped selections are actual-ID singletons, and both fighter slots remain in the denominator
even with zero selections. Return the real selector result unchanged and prove audit/trace/RNG
parity. A fixed-pool bound cannot prove universal infeasibility: changed IDs can change later
plans, chains and trajectories. Never replace the ordinary 20–24 variety requirement with it.
The current draft registry combines five entry, nine front-headlock, ten turtle, seven failed-shot,
eight standing-back and fifteen leg-game identities (400 combined with production),
not a second production catalogue. Keep `DRAFT_MOVE_DEFINITIONS` explicit and validate all
definitions/graph edges together. Report actual draft-ID membership rather than treating any
unknown `generic_*` payload as a new authored move; bind registry content/lookup fingerprints
before simulation so changed successor maps cannot share apparently identical trial provenance.
Use actual pre-exchange position counts for pocket occupancy. Its denominator is range plus
pocket exchanges only; a distinct-context count cannot prove the 8% standing-distance target.
Keep missing/zero draft selections visible alongside legal reachability and aggregate variety.
Automatic specialist separation is neutral, not a successful fighter transition. Compute earned
response credit before separation; preserve genuine control work but do not award extra recovery,
plan/judging effectiveness, trait/camp praise or completed chains for the reset itself. Clear both
fighters' pending chains so a range-legal successor cannot survive the referee restart.
Chain-opportunity diagnostics must also count either actor's intervening neutral reset as an
interruption, including a reset on the next own action. Keep that failed root in the denominator
but exclude it from optimistic action/move successor opportunities.
Keep existing-move recommendations separated by root identity. Report the root's current
successors and action families, then union candidate action coverage once per observed case;
multiple legal IDs for one action are overlapping choices, not extra achievable completions.
The rejected one-two/mount/half-guard successor trial improved short-run variety but reduced the
full corpus to 2,243 finishes / 595 KO / 680 TKO; its one-two-only ablation produced
2,246 / 579 / 697. Do not restore either map without new mechanical evidence and the exact locked
2,319 / 633 / 731 counts.
Root completion cohorts must use facts already recorded on the root exchange: settled position,
outcome, actor streak, actor gas after the exchange and the count of declared successor action
families. Keep missing facts explicitly `unknown`, and reconcile every dimension to the same
attempted/completed denominator. Do not redefine attempted chains through a selective commitment
gate: the current gates that exceed 50% retain too few completed roots to satisfy chained-selection
share. The rejected turtle-hammerfist representative bonus swapped which rare draft was absent and
reduced candidate KO by one; upstream state frequency, not a blanket score bonus, is the next
specialist-frequency question.
Leg-entry retention must follow the existing dangerous non-finishing mechanical submission, not
a subsequently selected narrative move. The experimental gate compares knee-line skills without
another RNG draw; preserve default-off elite entry semantics. In leg entanglement `top` denotes
knee-line control, not physical top position. Counter-lock reversals add neither submission-attempt
nor takedown credit. Test draft authoring separately from actual ordinary entry frequency.
Submission identity compatibility lives in `fight_moves/submission_identity.py`. Pass resolved
technique evidence explicitly at post-resolution selection, before candidate-relative signature
exclusions. Never use stale last-submission state in action/chain previews, and never change the
mechanical technique draw to fit a preferred signature. Unproved delivery variants use generic
identity with no named signature/mastery credit. Isolated authoring payload tests prove eligibility
only; real resolver-to-trace tests must prove mechanical/named identity agreement.
Pocket residence uses pre-selection exchanges, not position-after labels. Include zero-beat
entry episodes at horns/finishes; record unobserved exits rather than guessing a transition.
The residence histogram's weighted sum must reconcile exactly to pocket occupancy, and every
observed episode must have an explicit exit/end reason in candidate diagnostics.
Experimental punch distance uses the existing contest and landed evidence, preserving pre-action
move/defense context and the strike's actual outcome. `distance_transition` records from/to,
responsible fighter and reason; defender pivots are not attacking success. Do not overwrite
knockdowns, finishes or another resolved position, and do not use psychological context pressure
as forward movement. Pocket inactivity resets inherit neutral reset credit/chain safeguards.
Submission audit contexts must distinguish compatible named identities from generic fallback and
incompatible named claims. Keep all attempts in the denominator and never count a wrong signature
as authored coverage. Candidate reports reject incompatible claims even when aggregate variety
looks healthy; generic concentration remains a separate content gap.
`fight_moves/submission_pool.py` adapts repeated weighted tickets before the existing mechanical
draw. Preserve pool length, per-index choke and leg/non-leg flags, and each original technique's
first occurrence. Variants require real registry action/position/ownership/minimum-skill and
exclusive-style eligibility. Preferred styles are not restrictions. Never infer Von Flue,
cradle or scarf-hold setups from position alone, and keep positional counter locks separate.
`submission_technique_tickets()` is the pure shared pool builder; only `submission_technique()`
draws the hold. Joint experimental chain previews count the union of compatible ticket indices
after per-technique signature exclusions and eligibility gates. Never consult stale resolved holds,
give every submission branch full probability, or add RNG to previewing an opportunity.
Experimental `_role_submission_options()` separates mechanical top/bottom geometry before variant
adaptation. Pool validity may change candidate technique/choke distributions and needs new calibration;
never preserve an impossible legacy hold merely to retain ticket statistics. Adapter conservation
tests compare the role-aware base input against its adapted output, while default-off semantic parity
protects production. Bottom mount/back wrist isolation does not establish sensible action frequency
or justify dominant-position bonuses. Experimental dominant bonuses and finish multipliers require
actual top ownership; bottom guard-work benefits require actual bottom guard/half guard. Preserve
legacy default-off semantics. `fight_submission_position_bonus_regression_test.py` checks threshold
boundaries, ownership, gas/danger evidence and top/guard compatibility. Top-guard Ezekiel is a valid
no-gi hold, not an unsupported gi-only setup; its existing minimum skill remains enforced.
Submission-defense selection receives explicit current `resolved_technique` evidence from the
trace recorder. In the experimental engine, actual hold family outranks generic/authored tags;
leg-lock-only defenses cannot defend confirmed non-leg submissions. Do not read stale technique
state during isolated selection or restrict positional knee-line counters as submission attempts.
`fight_submission_defense_regression_test.py` covers both roles, generic identities and resolver
integration; candidate coverage permanently rejects contradictory submission-defense tags.
Experimental top-guard straight-ankle entries use the existing submission draw/contest, with one
eligible ticket above leg skill 62. Resolve entry before submission danger/finish bonuses; entry
itself awards one attempt but no finish roll, pass, takedown, sweep or physical-top control credit.
`top` becomes knee-line ownership on success. Clear `last_top_leg_entry` on the next exchange and
at horns; trace/render from explicit entry facts, and validate them in candidate coverage. Keep
half guard excluded until trapped-leg extraction is actually modeled. The narrow regression is
`fight_top_leg_entry_regression_test.py`; locked calibration still gates promotion to normal play.
`von_flue_setup` is private, single-use ready state, created by explicit retained-wrap/angle
resolution or a proven subsequent shoulder-positioning beat. Its top/bottom slots, round and tick must match the
immediately following exchange. Pure previews cannot consume it; real technique selection consumes
it even when another hold wins. Other actions, transitions, horns and every finish path invalidate
the opportunity. Keep created/used trace facts independent of move names; `von_flue_setup_counts`
validates consecutive provenance, and `fight_von_flue_setup_regression_test.py` covers the lifecycle.
`scarf_hold_setup` uses the same immediate-next-exchange lifetime, but originates from contested
top-side `ground_control`. Preserve its existing three control points without adding submission,
damage or danger credit. Creation uses generic move identity: ordinary scarf orientation and arm
isolation do not prove reverse-scarf, crucifix, signature, mastery or chain completion. Only the
later actual scarf-hold armbar maps to its compatible IDs; keep Judo and minimum-skill gates.
`fight_scarf_hold_setup_regression_test.py` verifies real trace pairs and expiry; coverage rejects
missing/interrupted provenance and false named creation through `scarf_hold_setup_counts`.
Referee inactivity resets bypass `set_fight_position()`: explicitly clear private setup state there.
When a scarf setup was just created, retain a `cancelled` transient fact with referee-stand-up reason
so named selection stays generic; do not let cancellation license an unrelated control signature.
The report validates settled range/no owners and cannot treat cancelled evidence as a later setup.
Render referee stand-ups before setup-specific prose, without changing inactivity mechanics.
Experimental side-control setup intent is a pure pre-contest decision, not a selected move ID.
Compare arm-isolation and ride/pin skills; familiarity is nonexclusive and plan effects require
enabled plans and their bounded execution. Ties retain ordinary control. Only isolation intent
may run the scarf contest; never guarantee a named cradle or use move names to infer geometry.
The scarf provenance gate also rejects explicit signature/mastery/sequence credit on generic
creation or cancellation facts, not just a non-generic move payload.
Strong-denial plain bottom-half guillotines may assess grip retention and shoulder angle only
after the dangerous/finish branches, retaining the existing two top-control points. Grip retention
must be positive and angle nonnegative; a stopped choke or retained grip alone is not a Von Flue
opportunity. Keep `last_guillotine_defense` transient, clear it at the next resolution/horn, and
render from its current trace fact without an extra mechanics draw. The focused regression is
`fight_guillotine_defense_regression_test.py`; coverage checks finite scores, sign-derived flags,
owners, position and matching setup creation through `guillotine_defense_observation`.
Setup follow-through counts are diagnostics, not an alternative legality gate. Count all created
roots, including opponent interventions, other actions/holds and terminal boundaries; exclude
cancelled creations. Their totals must reconcile to the provenance-validated creation counts.
Prepared submission preference must use a pure current setup/eligibility preview independent of
named chains. Combine its action bonus with chain intent by maximum, not stacking, and apportion
the existing integer budget once. Preserve survival overrides and every legal action. Technique
reweighting follows variant adaptation, redirects only duplicate same-family tickets, retains each
alternative's first occurrence and per-index choke/leg flags, and adds no random draw. Readiness
is skill/gas/plan-execution bounded; no preference may extend expiry or force the named technique.
`fight_prepared_submission_regression_test.py` covers these boundaries and draw conservation.
`von_flue_pending_wrap` is not a ready setup or ticket. It comes only from an actual strongly
denied plain bottom-half guillotine with retained grip but no angle. The immediately following
same-top `ground_control` may contest angle using the existing margin plus bounded skill effect;
consume the pending wrap regardless of outcome. Other actions/actors, transitions, resets, horns
and finishes cancel it. Do not refresh pending or ready expiry. Angle work keeps only the existing
three control points, no new RNG/submission/damage/danger, and generic move identity. Ready setup
retains `source=angle_work` and `origin_tick`; used evidence must preserve both. Trace `von_flue_angle`
records pending/ready/cleared/cancelled facts; referee resets take narrative priority and preserve
attempted-control generic identity. Validate the full consecutive origin/angle/attempt path through
`analysis/von_flue_angle_provenance.py`, not a claimed ready flag alone. Run both angle regression
and provenance suites, default parity and fresh full candidate calibration before promotion.
Experimental specialist menus and attack bundles must reference supported detailed skills; broad
fight IQ is an explicit model property, not a synthetic detailed key. Preserve legacy default-off
arithmetic. `_fight_control_owner()` adds front headlock/turtle physical control without equating
leg-entanglement knee-line ownership with physical top. Record `last_control_award` at the existing
credit point before inactivity/incident handling with position, top, bottom, clinch_controller and
controller; clear it next resolution/horn and copy it to trace `control_award`. A later referee
stand-up may clear position but does not erase already earned control time. Coverage reconciles
the point snapshot to exact `control_delta`, while settled escapes/neutral resets award no phantom
control. Run `fight_specialist_accounting_regression_test.py` and full candidate calibration.

This guide is the working contract for coding agents that inspect, change, test, or package
MMA Warriors. Read it before editing. It documents how agents should collaborate, where game
state lives, and which product invariants must survive every change.

> **Terminology:** In this document, an **agent** is an AI coding collaborator. The promotions,
> executives, matchmakers, fighters, and media organizations simulated by the game are referred
> to as **game AI** or **simulation actors**. They are ordinary Python state and logic, not
> independent agent processes.

## 1. Working Agreement for Coding Agents

### Agent roles

The roles below describe responsibilities, not permanent identities. One agent may fill more
than one role on a small task.

- **Primary agent / integrator**: owns the user request end to end. It defines scope, inspects
  existing behavior, delegates bounded work where useful, resolves overlapping changes, runs the
  final verification, and reports what changed and what remains uncertain.
- **Investigator**: traces a bug or subsystem without making broad edits. It should return concrete
  evidence: relevant files and methods, reproduction conditions, likely cause, and suggested tests.
- **Implementer**: makes a focused change in explicitly owned files. It must preserve save
  compatibility and existing user changes, and should add or update the narrowest useful test.
- **Reviewer / verifier**: reviews the integrated diff rather than the intended design alone. It
  looks for regressions, stale documentation, save/load gaps, UI overflow, duplicated methods, and
  missing tests, then runs the checks appropriate to the change.

The primary agent remains responsible for the final result even when work is delegated.

### Multi-agent collaboration

Multi-agent delegation and parallel work are explicitly enabled for this project when independent
investigation, implementation, review, or testing can be performed safely.

1. Give each delegated task a narrow question, named file set, or read-only scope.
2. Avoid having two agents edit the same file at the same time. If overlap is unavoidable, name one
   integrator and have the other agent return findings instead of a competing patch.
3. Delegated agents should report evidence and assumptions, not only a conclusion.
4. The primary agent reviews the combined diff and runs the final tests after all edits settle.

Example delegation:

```text
Investigator: trace how a five-round bout chooses max_rounds; do not edit files.
Implementer: patch fight_engine.py and the focused regression in smoke_test.py.
Reviewer: inspect the final diff for missing structural commentary and run fight tests.
Primary: integrate, resolve conflicts, run the full shipping suite, and update docs.
```

### Approval policy

Do not ask for approval before ordinary, in-scope development work. Proceed autonomously with
reading, editing, testing, building, and other reversible project actions. Ask the user only when:

- essential information cannot be discovered locally;
- the choice would materially change the requested scope;
- the action affects external systems or people; or
- the action is destructive or difficult to reverse.

Preserve unrelated working-tree changes. Never delete or rewrite user saves unless explicitly
requested.

### Repository hygiene

- Inspect `git status --short` before and after work so existing edits are not mistaken for yours.
- Review untracked files before staging. Add required source, tests, documentation, and intentional
  assets; leave out saves, logs, caches, local databases, and generated build output unless the
  project explicitly tracks them.
- Stage only the files that belong to the requested change. Do not silently bundle unrelated user
  work into a commit.
- Run `git diff --check` before handoff to catch whitespace and patch artifacts.

### Mandatory change package

Every implementation update, improvement, bug fix, balance change, data change, UI change, tooling
change, or packaging change must include all of the following in the same working diff:

1. **`CHANGELOG.md`**: add a concise entry under the current release describing the observable fix,
   improvement, compatibility effect, or developer-facing change.
2. **`README.md`**: update the relevant feature, workflow, test, build, or compatibility description
   so the repository's main documentation matches the implemented behavior.
3. **`AGENTS.md`**: update the relevant architecture map, invariant, integration point, pitfall, test
   rule, or workflow guidance so a future coding agent does not reintroduce the old behavior.
4. **Tests**: add or update the narrowest useful automated regression and run the affected suite.
   A bug fix test should fail against the broken behavior and pass with the fix. An enhancement
   should cover its main path and important boundary or compatibility case.

These are required deliverables, not optional cleanup. Do not make empty timestamp/touch edits just
to satisfy the list; each document change must explain something useful about the change. If a
runtime behavior genuinely cannot be automated, add the closest stable invariant test and document
the reproducible manual verification. Documentation-only changes do not require a new game-runtime
test, but still require Markdown/link review and `git diff --check`.

### Definition of done

A meaningful code change is complete only when the primary agent has:

1. inspected the existing implementation and adjacent state flow;
2. implemented the smallest coherent fix;
3. added or updated regression coverage, or documented why only manual verification is possible;
4. run the checks appropriate to the affected subsystem;
5. reviewed the final diff for accidental or unrelated edits; and
6. made meaningful, synchronized updates to `CHANGELOG.md`, `README.md`, and `AGENTS.md`.

## 2. Product Goal and Design Principles

MMA Warriors is a Windows desktop MMA promotion-management simulation. The target feel is a deep,
living WMMA-style world: promotions compete, fighters age and develop, gyms matter, contracts and
morale matter, and fight outcomes emerge from the simulation rather than being forced.

The game should remain:

- a shippable Windows desktop game;
- a deep business and world simulation, not a web app;
- dark, readable, game-like, and uncluttered;
- data-rich but navigable; and
- compatible with existing careers whenever possible.

Treat the repository root as the directory containing this file. Do not put developer-specific
absolute paths or Windows usernames into source code, documentation, batch files, or tests.

## 3. Architecture at a Glance

The application was split from one large `main.py` into flat sibling modules. `FightEmpireApp` is
assembled from mixins so existing cross-cutting `self.some_method()` calls continue to work.

The current mixin order in `main.py` is:

```python
class FightEmpireApp(
    FightNightAudioMixin,
    UIMixin,
    AdminMixin,
    SeedMixin,
    MediaMixin,
    ViewMixin,
    EventMixin,
    FightEngineMixin,
    WorldMixin,
    PersistenceMixin,
    AwardsMixin,
):
    ...
```

Python resolves duplicate method names in that order. Before adding a common-sounding helper, use
`rg` to make sure another mixin does not already define it. Add a method to the module that owns its
behavior; add a true global constant or path anchor to `constants.py`.

### Source modules

| File | Primary responsibility | Important integration points |
| --- | --- | --- |
| `main.py` | Entry point, `FightEmpireApp`, initialization, startup splash, crash hooks, launcher | Imports every mixin; initializes shared state before builders and refreshes use it |
| `constants.py` | Version/title, path anchors, weights, regions, skills, names, camps, tuning constants | Paths must remain portable; fight and UI limits belong here |
| `models.py` | `Fighter`, `Gym`, and `Promotion` dataclasses | New fields need safe defaults and load repair |
| `ui.py` | `UIMixin`: theme setup, shared layout, sorting, all `build_*_tab` methods, and the managed popup registry | Widgets are populated by refresh methods in `views.py` and other domain mixins; runtime popups must use `create_managed_window()` |
| `views.py` | `ViewMixin`: `refresh_*` methods, profiles, rankings, contracts, staff, finance, matchmaking views | Reads shared app state; must tolerate old-save defaults |
| `admin.py` | `AdminMixin`: sim lab, engine settings, belts, champions, name cleanup | Useful for calibration and repair tools, not outcome fudging |
| `seeding.py` | `SeedMixin`: universe database loading, roster/company/region/gym seeding, generated fighters, repair data | Core-promotion and data-quality changes usually start here |
| `events.py` | `EventMixin`: scheduling, negotiations, weigh-ins, live fight window, `run_event`, `finish_event`, awards | Calls the fight engine, world result application, media, audio, and season tracking |
| `fight_engine.py` | `FightEngineMixin`: `simulate_fight`, action resolution, damage, stoppages, scoring, commentary | Returns simulation results; must not mutate presentation state unpredictably |
| `world.py` | `WorldMixin`: availability, result application, Elo, finance, calendar, aging, retirements, game AI promotions, market churn | Owns weekly/monthly world progression and AI-company activity |
| `persistence.py` | `PersistenceMixin`: serialization, load/apply, slots/folders, database import/export, crash recovery | All persistent model/state changes need a compatibility path here |
| `awards.py` | `AwardsMixin`: season tracking and end-of-year awards | Decisive player and AI fights must both call `record_season_result` |
| `media.py` | `MediaMixin`: media desk, stories, broadcaster/media-rights state and presentation | Persistent media fields need save defaults and `media_system_test.py` coverage |
| `audio.py` | `FightNightAudioMixin`: optional fight-night sound, manifest-driven crowd variants, continuous arena-bed sessions, and reaction playback lifecycle | Crowd WAVs live under `assets/crowd_audio`; the game must still work through procedural fallbacks when assets or playback support are unavailable |
| `real_sport_profiles.py` | Authored real-sport fighter/profile data | Keep data deterministic and consistent with seeding rules |
| `database_editor.py` | Standalone universe database editor | Has its own executable, spec, build script, and UI audit |

The older `main.original_backup_*.py` files, when present, are historical pre-split backups. They are
not the active implementation. Do not copy fixes into them.

### Tests, scripts, and runtime data

- `smoke_test.py`: broad startup, release-document synchronization, state, save/load, UI-adjacent,
  contract, and fight regressions.
- `persistence_regression_test.py`: transactional load, metadata sidecar, serialization purity, and
  Results-index idempotence regressions.
- `contracts_finance_regression_test.py`: contract validation, persistent clauses, same-name booking,
  guarantees, and canonical event-payout regressions.
- `finance_audit_regression_test.py`: canonical player/child transaction metadata, weekly cash
  reconciliation, and repairable direct-cash mutation coverage.
- `player_finance_progression_regression_test.py`: annual summaries, revenue mix, roster-cost
  snapshots, milestone projections, strategic investment gates/effects/upkeep, save persistence,
  and Finance-screen population.
- `ui_data_regression_test.py`: lazy staff/scouting UI, Results detail, gym capacity, regional data,
  themed Regions, and fighter-identity regressions.
- `fighter_profile_regression_test.py`: Profile employer/privacy, same-name history, archive identity,
  championship scoping, child-sport query purity, responsive geometry, and stale-action guards.
- `scouting_regression_test.py`: scouting identity migration, RNG purity, report lifecycle,
  rediscovery, staff identity, and recruitment UI-state regressions.
- `combat_sports_regression_test.py`: child-sport roster/booking identity, flagship contracts,
  expiry departures, purse settlement, scheduled-event lifecycle/economics, monthly card limits,
  and AI/player history separation.
- `qa_tooling_regression_test.py`: Simulation Lab isolation/calibration and portable launcher paths.
- `fight_engine_regression_test.py`: deterministic MMA audit purity, trace/stat consistency,
  detailed-attribute usage, and the frozen 3,840-bout finish-distribution parity corpus.
- `fight_engine_full_system_test.py`: 356 complete MMA bouts across every fight plan, major style
  matchups, 3/5/6/7-round rules, extreme ratings and same-name identities; reconciles trace evidence,
  position paths, stoppages, judging knockdowns and final box scores.
- `analysis/generate_fight_move_report.py`: deterministic 880-fight move report across every supported
  style plus behaviour, tier, stance and stance matchup; audits reachability, pairwise style distance,
  dominance, mismatch-only use, legality, move-energy metadata and ordinary use of every exclusive
  style combination and finisher without changing the frozen baseline. Its targeted reachability probe
  must adopt a move's preferred style before testing restricted style content; do not weaken runtime
  exclusivity.
- `analysis/generate_specialist_transition_report.py`: deterministic 720-fight complete-bout proof for
  failed-shot/front-headlock, standing-back-control and leg-entanglement states and legal follow-ups.
- `analysis/generate_fight_commentary_report.py`: deterministic 256-fight, four-voice commentary gate
  covering every factual outcome lane, stat-profile and failed-submission reaction coverage,
  standing/ground repetition, Broadcast compaction, actor/move/defense agreement, referee stand-up
  continuity, finish causality, duplicate results, placeholder removal, technical-suffix leakage,
  visible-damage actor/subject/symptom facts, exact cut locations, all supported trait introductions,
  contextual trait/camp evidence and call caps, verified camp-intro retention and Broadcast damage retention.
  Its `--seeds-per-matchup 64` mode is the 2,048-fight extended transcript audit.
- `analysis/generate_fight_action_baseline.py`: canonical 3,840-fight release gate for broad-action
  frequency, effectiveness, damage, energy, counters, positions and finishing contribution. The
  isolated regression runner verifies the checked-in baseline; do not treat it as an optional report.
- `stability_test.py`: longer-running deterministic and progression playtests.
- `media_system_test.py`: media-system state and workflow regressions.
- `child_promotion_long_run_test.py`: deterministic 48-week MMA child-promotion progression,
  event finance, parent profit sharing, contract countdown, protected loans, callback safety, and
  save/load persistence. It intentionally keeps only the child in the in-memory AI world so the
  calendar pipeline remains real while the focused regression stays fast enough for routine runs.
- `custom_promotion_division_integrity_test.py`: deterministic 48-week AI handoff regression that
  ensures annual weight movement cannot place fighters into a custom promotion's closed divisions.
- `child_promotion_interactions_test.py`: child takeover, empty-launch rollback, champion-loan belt
  protection, closed-division transfer rejection, transfer-ledger accounting, and loan repair.
- `identity_persistence_regression_test.py`: same-name live-fight and tournament identity, clinch
  ownership, unanswered-response semantics, ambiguous legacy relationships, event-commit rollback,
  forward/malformed save rows, and external-block path containment.
- `database_editor_save_as_test.py`: standalone editor Save As success, cancellation, validation,
  and write-failure state preservation.
- `database_editor_ui_audit.py`: database-editor UI audit.
- `universe_validation_regression_test.py`: shared editor/runtime validator malformed-data diagnostics and proof that normal legacy loading does not rewrite source bytes or mtime.
- `fight_audio_regression_test.py`: temporary fight-cache exception cleanup, continuous ambience
  lifecycle/crossfade, priority reservation, mastered later-round routing, and concurrent cue locking.
- `fight_night_experience_regression_test.py`: live-session re-entry, playback/control gating,
  duplicate-name winner identity, skip/review behavior, commit-failure recovery, replay cleanup, and
  responsive end-event invariants.
- `advance_notifications_regression_test.py`: routine contract/broadcast advancement notices collapse into one Inbox summary while due-event decisions remain modal.
- `window_lifecycle_regression_test.py`: runtime popup creators use the shared call-site/entity window registry.
- `event_economics_regression_test.py`: per-event ticket, marketing, production, legacy/default,
  save/load, and identity-safe grudge economics.
- `narrative_system_regression_test.py`: bounded ID-safe story threads, rivalry/title/redemption
  lifecycles, injury/academy/contract/staff/feeder/breakout/weight/gym/coaching/relationship/promotion-war/other-sport/crossover
  chapters, Chronicle linkage, lazy career timelines, annual-review selection, legacy/current save
  normalization, career-journey outcomes, presentation RNG purity, and indexed event-update performance.
- `narrative_performance_regression_test.py`: clean 12-week narrative-disabled/enabled calendar A/B
  comparison across three alternating paired samples, with deterministic test-only generated IDs,
  identical core-world/RNG assertions, a strict median CPU-time budget, and wall-clock diagnostics.
  CPU time is the release gate because it measures simulation work without turning an unrelated OS
  scheduler pause into a false regression; do not remove or loosen the 5% proportional ceiling.
- `narrative_long_run_storage_regression_test.py`: synthetic 25-/50-/100-year story growth, resolved
  cap, serialized-size, RNG isolation, and indexed-lookup scaling.
- `simulation_performance_regression_test.py`: promotion-level card-day caching, precomputed
  head-to-head reuse, batched regional name collision state, and one-card-per-month feeder
  staggering across all four calendar weeks.
- `run_regression_suite.py`: the canonical sequential test runner. It gives every suite an isolated
  `MMA_WARRIORS_DATA_DIR` with copied universe data so tests cannot race through shared saves,
  logs, markers, or caches.
- `Run Smoke Tests.bat`: runs the canonical isolated regression suite.
- `Launch MMA Warriors.bat`: starts the source game.
- `Build Portable.bat`: tests, validates the universe database, and builds both the game executable and the standalone database editor into `dist\\MMA Warriors`.
- `Build Database Editor.bat`: validates and builds only the standalone database editor when a
  full portable rebuild is unnecessary.
- `build-toolchain.json` and `requirements-build.txt`: the checked-in, offline-verifiable portable-build toolchain. Build scripts must validate these and must never install dependencies.
- `Portable Check.bat`: checks the packaged runtime.
- `README.md`: player, source-run, test, and build instructions.
- `FEATURE_DEVELOPMENT_BACKLOG.md`: evidence-backed player-facing feature priorities and phased
  development sequence. Keep it synchronized when a listed feature is shipped or materially
  re-scoped.
- `FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`: phased expansion of MMA styles, move definitions,
  combinations, skill coverage, signatures and tactical selection. Each mechanical slice must keep
  the accepted 60.39% finish, 16.48% KO and 19.04% TKO calibration and must not change
  `competitive_finish_conversion()`.
- `NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md`: audit and staged design for connecting existing simulation
  facts into persistent story threads. Narrative work must follow its performance guardrails: emit
  bounded updates from existing domain events, use indexed stable identities, isolate presentation
  RNG, and never add a second whole-world weekly history scan.
- `CHANGELOG.md`: release-facing behavior changes.
- `TAB_ACCESSIBILITY.md`: tab contrast and interaction requirements.
- `savegame.json`, `Saves/`, `Databases/`: runtime data. Do not delete or overwrite user careers.
- `Logs/mma_warriors.log`: rotating runtime log. `Logs/Crashes/` contains timestamped crash reports;
  crash autosaves live in the active slot's `Crash Recovery` folder.

## 4. State Ownership and Control Flow

`FightEmpireApp` is a shared stateful object. Mixins cooperate through `self`, so a local-looking
change can affect save/load, refreshes, and world simulation. Trace both writers and readers before
changing a field.

Two `Fighter` model invariants are especially important:

- `Fighter` uses `@dataclass(eq=False)` deliberately. In-memory membership and comparisons use
  object identity for performance. Persistent and UI identity uses `fighter_id`; display names are
  not unique identifiers.
- Live-fight state is private to one bout and uses per-fighter state keys, never `fighter.name`.
  Names are presentation only. ID-first resolution must be pure: do not restore, release, sign, or
  otherwise mutate roster ownership as a side effect of looking a fighter up.
- `Fighter.overall` is a derived read-only property. Change the underlying broad/detailed skills or
  use the relevant calibration helper; do not assign directly to `overall`.
- Model collections that are semantically always present use `default_factory`; persistence must still
  normalise old-save `null` values. Do not replace meaningful optional sentinels such as an inactive
  `Fighter.career_arc is None` with an empty object.

### Canonical flows

**Player fight flow**

```text
booking UI
  -> event-date availability checks
  -> perform_weigh_in (shared weight-cut model)
  -> simulate_fight (mechanics + complete structured commentary)
  -> finish_event
       -> record_season_result
       -> apply_result or apply_draw_result
       -> finance, injuries, rankings, history, awards, and media
  -> viewer and save/refresh
```

The watched presentation is a single live session. Never prepare the same due event again while a
viewer is active: preparation runs mutable press-conference and weigh-in rules. A different replay
must not replace or destroy an unresolved player card. Playback controls must follow bout state;
starting the next fight cannot discard an incomplete transcript, full-card skip requires an
explicit second action, and every bout becomes reviewable after completion or confirmed skip.
`finish_event` remains the settlement transaction; only mark the viewer finished after that commit
succeeds, and keep a failed settlement visibly retryable.

Live telemetry and result presentation are ID-first. Red and blue round metrics use corner slots,
not display names, and current fight logs retain `winner_id` alongside `a_id`/`b_id`. Exact judge
cards and numerical totals remain sealed until the official result; public round summaries may show
metrics, gas, momentum, and an explicitly unofficial leader. Archived replay packages preserve
event economics and location context but always use `apply_results=False`.

`finish_event` is a domain transaction. Stage the pre-event persistent state and RNG before the
first finance or result mutation; if any downstream award, media, archive, history, or refresh
hook fails, restore the staged state before surfacing the failure. UI presentation occurs only after
the commit succeeds. Runtime synchronization objects such as locks, threads and `threading.Event`
audio stop signals, plus non-copyable `random.SystemRandom` audio entropy, must remain live and outside
the deep-copied rollback snapshot.

**Game-AI fight flow**

```text
calendar_week_steps
  -> world_week_steps
  -> ai_should_run_show
  -> simulate_ai_promotion_month
  -> AI booking and perform_weigh_in
  -> simulate_fight
  -> AI-specific Elo, records, recovery, title, and finance updates
  -> record_season_result
  -> promotion history, media, and world state
```

Do not create a shortcut version of a shared rule for AI fights. Player events, AI cards, and
sandbox fights should call the same underlying mechanics wherever the rules are meant to match.
The current AI event path does not call `apply_result`; it performs equivalent domain updates inside
`simulate_ai_promotion_month`. When changing result semantics, inspect and test both paths.

**Save/load flow**

```text
live dataclasses and world dictionaries
  -> serialize_world / model serializers
  -> JSON in the active slot and group
  -> apply_world_data
  -> defaults + focused repair functions
  -> UI refresh
```

**Player event-economics flow**

```text
booking UI
  -> card-specific ticket price, marketing spend, and production tier
  -> projected attendance/gate/spend from the shared economics helpers
  -> scheduled-event serialization (legacy cards receive company defaults)
  -> finish_event transaction
       -> final demand, gate, merchandise, broadcast and production accounting
       -> canonical finance transaction
```

Forecast and settlement must call the same demand, pricing, production, and grudge helpers. A
booked rivalry is identified by durable fighter IDs; names are presentation and legacy fallback
only. A duplicate-name or stale legacy rivalry must never boost an unrelated bout.

### Calendar model

- A month has four simulation weeks.
- The displayed year is `2026 + (self.month - 1) // 12`.
- A new year begins when `self.month` rolls to 13, 25, and so on.
- Despite its legacy name, `advance_month()` synchronously advances **one week** for tests, audits,
  and non-UI callers. It consumes `calendar_week_steps()` and only crosses a month boundary when
  advancing from week 4.
- `begin_advance_sequence()` is the responsive Tk path. It also consumes `calendar_week_steps()`
  but schedules work through the event queue so the window remains usable.
- Promotion monthly reviews are assigned to stable, evenly sized weekly groups by
  `world_week_steps()`, and `world_month_steps()` must not repeat them at the boundary. Every
  promotion receives one development pass and monthly card opportunity per four-week month; every
  regional circuit runs one dedicated card. Keep feeder promotions out of the generic weekly
  `ai_should_run_show()` path.
- Routine post-advance contract, broadcast, and similar notices are accumulated by
  `queue_advance_notice()` and presented as one Inbox/news summary. Only genuine player decisions,
  such as a due event's watch/simulate choice, may remain modal.
- At a year boundary, the calendar rollover runs end-of-year awards and `age_world_one_year`.
- Annual aging is deterministic `+1`; do not add a second birthday path.

## 5. Save Compatibility and Persistent State

Do not break existing saves. New data must be optional when an old career does not contain it.

When adding a field to `Fighter`, `Promotion`, `Gym`, or a persisted world dictionary:

1. add a safe dataclass/default value where possible;
2. seed it for new universes;
3. serialize it if the existing serializer does not already do so;
4. restore it in `apply_world_data` with `get`, `setdefault`, or a focused repair helper;
5. update profile/refresh code so missing legacy data is harmless; and
6. add an old-save or round-trip assertion to `smoke_test.py`.

Example pattern:

```python
# models.py
morale_trend: int = 0

# persistence.py, while applying legacy data
fighter.morale_trend = int(saved.get("morale_trend", 0))

# smoke_test.py
assert loaded_fighter.morale_trend == 0      # legacy-shaped input
assert round_trip.morale_trend == original   # current save
```

### Path and slot rules

- `APP_DIR` comes from `__file__`, or from `sys.executable` in a packaged build.
- `DATA_DIR` uses `APP_DIR` when writable. In a protected install location it falls back to
  `%LOCALAPPDATA%\MMA Warriors`. `MMA_WARRIORS_DATA_DIR` is an explicit test-only/runtime override
  for an isolated data root; do not set it in shipped launchers.
- `SAVE_FILE`, `SAVE_DIR`, `DATABASE_DIR`, and `LOG_DIR` are anchored to `DATA_DIR`, never the
  current working directory.
- Existing ungrouped careers live at `Saves\<Slot>\savegame.json` and appear as the `Main` group.
- User-created groups live at `Saves\Folders\<Group>\<Slot>\savegame.json`.
- `active_save_group` is persisted. Backups, autosaves, snapshots, and crash recovery remain inside
  the owning slot and must move with it.
- Save discovery and manipulation must use `primary_save_paths`, `save_slot_name_from_path`, and
  `save_slot_group_from_path`. Do not assume every slot is exactly one directory below `SAVE_DIR`.

### Transactional load and result-index rules

- Treat a load as a transaction. Read, validate, migrate, and apply into a guarded candidate state;
  if any phase fails, restore the complete pre-load application state before showing the error.
  Reject a non-object top-level JSON value before external-block hydration or migration.
- `ensure_result_index()` is an idempotent migration. A detailed record already represented by the
  same stable archive/detail key is skipped. Only genuinely distinct cards may receive a sequenced
  key, and repeated Quick Loads must never grow the index.
- Save metadata is auxiliary. A metadata-write problem must not turn an already committed primary
  save into a reported total failure; record it as a recoverable cache warning and rebuild it later
  without leaving a blocking success/failure dialog open.
- Recovery snapshots taken before Quick Save or switching slots are best-effort and must not block
  the requested operation when snapshot creation fails. A backup restore is different: validate the
  source first, then protect the existing destination and atomically replace it; report any failure
  without changing the destination or letting an exception escape the UI callback.
- The Game & Saves Career Library keeps `save_slot_list` as the action index and refreshes its active
  banner, counts, selection inspector, and button state through `refresh_game_menu()` and
  `refresh_save_selection_summary()`. Selection-only actions must remain disabled when no valid row
  is selected, and the blank destination-name field must not be populated from the active career.
- External split-save blocks must use generated `DataBlocks/<save-stamp>/<known-key>.json.gz` paths
  below the owning save slot. Reject rooted paths, traversal, symlink escapes, and unexpected block
  names before reading them. Pruning must skip symlinked entries rather than following or deleting
  them.
- Model rows must be type-checked before dataclass construction. Missing required fields are a
  transactional load error; unknown forward-compatible fields are logged and ignored rather than
  crashing an otherwise usable career.

### Serialization purity

`serialize_world()` and ordinary save loading must be observational: they may normalize JSON-safe
representations, but must not top up divisions, appoint champions, add fighters, or consume
simulation RNG. Champion/division repair belongs to explicit new-game or calendar repair steps;
legacy migrations must be narrowly versioned and may not rewrite a healthy sealed career.
Regression tests must compare fighter counts, champion state, and RNG state across a round trip.

### Career-to-database conversion

`PersistenceMixin.convert_career_to_database()` is an explicit J12 migration path, not a
normal save or a database-editor overwrite. `build_career_database_package()` and
`career_conversion_preflight()` must remain pure over a serialized mapping: preserve stable
fighter/promotion IDs, current skills/age/records, roster ownership and supported contracts;
reset time, cash, finance, inbox, pause targets, scheduled work and other live commitments.
Nested promotion and combat-sport event ledgers must be stripped from the playable package.
Detailed history and every excluded obligation are retained in a sibling
`<name>.conversion.json` manifest with structured severity/entity/field/evidence/remedy rows.
Unknown fields, duplicate top-level fighter IDs, invalid divisions and missing promotion
owners are structural errors and refuse the write. Populated ongoing work requires a visible
acceptance prompt; cancellation and destination conflicts are non-destructive. Write the
manifest and database only after staged validation, clean both artifacts on a failed new
conversion, and never modify the source career save. Career-start databases are hidden from
the legacy list by their manifest suffix and are labelled in the Game & Saves database panel.
Run `j12_conversion_regression_test.py`, persistence/UI regressions and the smoke check when
this path changes. Do not rebuild an EXE or touch user saves as part of conversion work.

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

## 7. New Promotion Starts

`Create New Promotion...` is a real starting mode, not an editor shortcut.

- The Starting Promotion dropdown is the sole entry point for established, custom, and
  Spectator Mode starts. Keep `Start New Game With Selected Promotion` as the only action
  button in that panel; do not restore a separate create-promotion shortcut.

- The player chooses region, scale, event philosophy, theme, supported genders, and active weights.
- New starts use viable roster targets of 8, 10, or 12 fighters per active division.
- The default is Men Only with Featherweight, Lightweight, and Welterweight active. Do not silently
  reopen every division.
- `Balanced`, `Star Led`, and `Prospect Heavy` change automatic-draft priorities.
- The manual initial-roster draft exposes fighter profiles and annual contract commitment.
- Every active division needs at least six selected fighters, and the total must remain inside the
  scale/division budget.
- `auto_select_custom_roster` must reserve a complete affordable baseline for every active division
  before spending remaining budget on upgrades. Sequential spending can starve the last division.
- Closed divisions persist when saved/loaded, handed to AI, or taken over later.

## 8. Matchmaking and Availability

Matchmaking is event-date aware. `fighter.status` describes the fighter's current condition; it is
not enough to decide whether the fighter can compete on a future date.

- Use `fighter_booking_status(fighter, month, week)` for the human-readable week-level state.
- Use `fighter_available_for_date(fighter, month, week, day)` for authoritative named-day
  eligibility.
- Refresh available fighters immediately when event year, month, or week changes.
- The default `Ready` filter means ready for the selected event date.
- The `All` filter may show unavailable fighters with a precise label such as
  `Available Mar W3 2026`.
- Routine conflicts belong in the inline matchmaking notice, not a native Windows message box.

Example:

```python
status = self.fighter_booking_status(fighter, selected_month, selected_week)
event_day = self.selected_booking_day()
if self.fighter_available_for_date(fighter, selected_month, selected_week, event_day):
    eligible.append(fighter)
else:
    display_unavailable(fighter, status)
```

## 9. Fight Engine and Fight-Night Presentation

The fight engine must model the bout rather than pick a desired result and work backward.

`Fighter.style` is the supported primary compatibility and search identity. `secondary_style` is an
optional, distinct supported cross-training identity; display it through `Fighter.style_label` and
apply it only through bounded shared style helpers. Never store behaviours such as Dynamic Attacker
or Submission Hunter in either style field. New-universe secondary assignment is deterministic and
must not consume simulation RNG; old saves safely default to an empty secondary style.
Every `create_generated_fighter()` result must finish with a supported primary style and a validated
distinct secondary style. The final generator guard may normalize blank or legacy labels but must be
deterministic and must not add another random draw; smoke coverage should sample generated entrants.

### Mechanical intent

- Kicks depend on kick speed, power, technique, stamina, distance, and defense.
- Punches depend on hand speed, punch power, technique, head movement, guard, chin, and stamina.
- Grappling depends on takedowns and setup, sprawl, guard work, control, submissions and defense,
  stamina, and position.
- Stamina and momentum should visibly influence later exchanges.
- Ground, clinch, and cage position must reset or transition according to the rules; state must not
  leak impossibly across a horn.
- `clinch_controller`, `top`, `bottom`, damage, stamina, and unanswered offense use private per-bout
  fighter slots. Compare them through `fight_state_key()`, never a display name. An unanswered
  sequence advances only when significant strikes land, clears when the pressured fighter lands or
  creates a meaningful grappling/positional response, and resets at every horn.
- Tournament participant names are presentation. Resolve the aligned `fighter_ids` list for the
  bracket, replacements, and temporary state; use object identity for private in-memory snapshots
  such as pre-view fatigue so same-name entrants remain independent.
- Commentary must never describe new actions after a finish.
- Equal score totals must be capable of producing draws.
- End-of-fight output includes the completed rounds and scorecards where applicable.

### Round count

The event data decides championship pacing. A fight marked `title` or `main` uses the configured
`title_rounds` value, including player-selected six- and seven-round settings; ordinary fights use
the normal `rounds` count. Never hard-code five introductions or four transitions in the watcher.
Test title and non-title five-round main events plus an extended configured title fight.

### Commentary structure

Five-round fights generate enough text to exceed a Tk text widget's comfortable live-display size.
The engine and archived fight log retain every generated action call and the original round-summary
telemetry. The live watcher defaults to a derived `Broadcast` stream that may condense repeated,
low-value timestamped calls; `Detailed` mode and completed-bout review expose the complete stored
transcript. Viewer compaction must be deterministic, must not mutate the archive, and must never
consume a simulation RNG stream. Structural and evidential lines must always survive:

- tale of the tape and opening context;
- every round introduction;
- every horn/round transition;
- every round summary;
- stoppage and official-result lines; and
- decision scores.

The live watcher may redact exact judge cards until the official result, but it must not replace or
shorten the round-summary line itself. Apply any display name cleanup before inserting a line into
the Tk `Text` widget; post-insert formatting cannot repair text that was already presented or alter
its tags. `stability_test.py` must advance a real five-round title viewer through each round and
verify all five original summaries, the scorecard reveal, metrics, and official result remain visible.

The live density control is presentation state. Switching an active or completed bout between
Broadcast and Detailed must rebuild only the reached visible lines, preserve the same raw-source
playback frontier, keep sealed scorecards sealed and leave the archived transcript unchanged. Round
separators, knockdown emphasis and finish emphasis are Tk tags/layout only. The visible personality
indicator reports the voice saved with that fight log; it must not imply a mechanics setting.

`FIGHT_COMMENTARY_ROUND_LINE_LIMIT`, `FIGHT_COMMENTARY_ROUND_HEAD_LINES`, and
`FIGHT_COMMENTARY_ROUND_TAIL_LINES` bound only ordinary timestamped calls in the derived Broadcast
view. Important middle-round evidence outranks head/tail position, so never use a blind slice. Never
deduplicate or trim `FightResult.commentary`, the archived `lines`, or the structured trace. A legacy
technical suffix may be removed from Broadcast prose, while its target, defense, follow-up, move and
position remain available in Detailed commentary or `round_analysis`.

Completed offense and ground-state progress are important Broadcast evidence. Landed standing
strikes, successful takedowns, landed ground strikes, passes, sweeps/reversals, escapes and stand-ups
receive priority over routine movement; identical calls remain capped at two even when their position
or outcome makes them high-priority, and repeated failed
attempts or passive control may condense. A same-position sweep is proven by changed
top/bottom ownership even when the position label remains `guard`. Any compact note must count the
actual omitted standing, standing-striking, takedown, ground-control and ground-striking lanes without
inventing success, damage or a position change.

Fact-driven wording variation must be selected from stable trace/bout material or the isolated
presentation stream; it must never call the mechanics, officiating, judging or process-global RNG.
Every exchange call must agree with the recorded actor, move, outcome, named defense, counter flag and
settled position. Context is evidence-bound: signature/mastery comes from the selected move payload,
stance and plan from trace state, damage/momentum from completed public deltas, camp/coach from fighter
data, and championship/rivalry stakes from the scheduled bout and identity-safe relationship helpers.
The bout-local commentary profile may record derived standing, ground and defensive strengths, but it
is presentation evidence only: use the strength relevant to the recorded weapon or transition, never
consume RNG or change an exchange. A failed submission trace must retain the actual technique chosen by
`submission_technique()`, a legal named defense and a natural consequence. A referee inactivity reset
is a separate structured fact; never credit the preceding ride/cling action with escaping to range or
use the referee's reset as effective-action evidence for trait or camp praise. The contextual
generators must return before consuming their per-fighter call allowance on a referee stand-up. Never
append old-position colour after a fighter has reached the feet. Ground presence lines must respect
current top/bottom ownership and every `GROUND_POSITIONS` state.
Do not infer a coach, rivalry, stance switch, plan change, blocked strike or successful counter from
style flavour alone. A failed sweep, stand-up, pass or transition must be described as an attempt,
not settled success. KO/TKO attribution must use causal damage/impact evidence rather than whichever
non-damaging move happens to be the final trace row.

Required regression scenarios include:

1. a five-round title decision with all five introductions and summaries;
2. a non-title five-round main-event decision with the same structure; and
3. a late round-five finish with the round-five introduction and official result preserved.

4. a configured seven-round title decision with all seven summaries, transitions, scorecards,
   metrics, and the official result preserved.

### Outcome calibration

The move-system expansion follows `docs/FIGHT_MOVE_SYSTEM_PLAN.md`. Its Step 0 reference is
`analysis/move_registry_parity.json`, captured directly from revision `4a73923` by
`tools/move_registry_parity.py --capture-ref 4a73923`. Capture refuses to overwrite a reference;
ordinary structural verification uses `--verify analysis/move_registry_parity.json` and writes
nothing. Preserve tuple and candidate order while sorting unordered sets. The parity regression
must reject reordered definitions and legal pools, changed fields and corrupt checksums. This
registry gate supplements, never replaces, the complete result and action corpus gates.
After approved content additions, preserve the original snapshot and its `compare_legacy`
projection against the immutable Slice 6 snapshot to protect every old record and lookup order.
Phase 31 permits only 125 reviewed successor-list updates through
`--verify-followups analysis/move_registry_slice6.json --followup-manifest analysis/move_followup_phase31_revised_manifest.json`.
The manifest binds the source checksum; every other field, ID, order and lookup remains exact.
The parity regression proves both historical links. Exact structural parity now uses the
separate `analysis/move_registry_followup_continuity.json` content snapshot. The prior Phase 31 snapshot is
connected through `compare_deprecation_update`, allowing only schema 1 to 2 and `deprecated=False`
on each move, into the immutable `analysis/move_registry_schema2.json`. A second successor-only
manifest, `analysis/move_followup_diversity_manifest.json`, binds that schema-2 source to the
30-root diversity update, followed by `analysis/move_followup_continuity_manifest.json` binding
the frozen diversity snapshot to the second 30-root layer. Each historical manifest must compare
its own source/destination, not silently allow all subsequent changes.
`analysis/compare_followup_diversity.py` compares the latest layer's complete paired bouts,
rejecting mechanical drift or a failure to improve chained selection share. Future content snapshots require
explicit reviewed additions, never replacement of the historical reference. Append new persisted
IDs to `EXPANSION_MOVE_IDS` so deletion protection covers new techniques as well as the original 200.
Sequence ownership checks must match the resolver in common and specialist ground positions,
including turtle, front headlock and leg entanglement. Chain acceptance cannot use a completed-only
median (which excludes interrupted roots by definition) as proof of the attempted-chain median.
The report records `phase_31_acceptance_failures`; `--require-phase31` enforces this unfinished
phase's targets before sign-off, separately from the already accepted content gates.
Use `analysis/generate_chain_opportunity_report.py` to diagnose failed roots before changing chain
weights or lifecycle. Keep its denominator aligned with the coverage report. Its best-three-action
bound ignores move eligibility and graph constraints and is conditional on existing observed roots;
never cite it as proof that a different catalogue cannot meet the target. Do not count an unrelated
action in an old occurrence unless a real declared graph edge connects it.
Separate emergency survival from other undeclared successor actions and from declared actions
without named completion. Derive declarations from the recorded branch IDs, not all moves sharing
an action. Trace-only diagnostics must not attribute losses to unrecorded ranking/eligibility gates;
retain every interrupted root and the existing optimistic-bound calculations.
The second, existing-technique bound must use union coverage over at most three move IDs, not
the sum of their individual counts. It filters both the root's settled context and the next
selection context, but intentionally omits skills, rarity, ranking and acyclicity. Preserve these
limitations when using the diagnostic to propose changes to the phase order.
`followup_defensive_continuity.py` is an unregistered append-only experiment, covered by the draft
authoring regression. Its four named recovery nodes have graph successors but ordinary `survive`
control outcomes do not seed another live step. Do not mark the longer-chain target complete from
those graph edges or add control tags merely to bypass the runtime effectiveness rule.
Use `tools/benchmark_move_selector.py --check` for the fixed 15% selector-time target at 800 moves.
It appends immutable benchmark-only clones, restores registry bindings and RNG, and compares repeat
mechanics. Windows CPU-clock quantization makes per-function CPU attribution unreliable; the tool
reports high-resolution cProfile attribution plus whole-sample CPU and wall time separately.
Structural selector edits must also pass `tools/move_selection_parity.py --verify analysis/move_selection_followup_continuity.json`.
The selection regression reconstructs the immutable schema-2 content in memory and checks all
44 original Phase 31 bout hashes through the strict deprecation migration. Preserve this historical
test as well as the current-content snapshot; the follow-up content update is not a refactor waiver.
Keep each catalogue source at or below 400 lines; the registry regression enforces the plan's
reviewability ceiling, so split new domain content rather than rebuilding a monolithic catalogue.
The immutable pre-refactor snapshot binds the exact registry checksum, complete fixture definitions,
ordered traces, move/defense/sequence payloads and mechanics for 44 bouts. It supplements rather
than replaces the 3,840-bout result/action gates. Never recapture this snapshot to hide refactor drift.
The six `_move_candidates`, `_move_static_score`, `_move_contextual_score`, `_move_rarity_gate`,
`_select_from_pool` and `_move_payload` helpers retain engine ownership of selection. Preserve
left-associated score addition, candidate-relative signature-finisher exclusion, authored-top
priority, counter restrictions, threshold boundaries and generic payload defaults when optimizing.
`_fight_move_score_cache` lives inside `simulate_fight` and must restore the previous object on
nested calls or exceptions. Cache by fighter and definition identity, retaining the definition;
same-ID registry replacements must not reuse stale scores. Do not cache dynamic candidate-relative
signature exclusions or exchange context across ticks. `fight_move_cache_regression_test.py`
protects warmup, isolation, development boundaries and replacement definitions.
Retirement uses `MoveDefinition.deprecated`, a strict boolean defaulting to false. Keep retired IDs
in `MOVE_REGISTRY`, signature/mastery normalization and replay lookup; exclude them from `MoveIndex`,
live successor branches, new generated signatures, camp growth and mastery-to-signature promotion. Existing retired
signatures/mastery remain intact (ordinary age decline may still apply). The deprecation tests
must distinguish preserving a learned move from acquiring a new one.
The registered `followup_diversity.py` layer has separate authoring tests. Clinch-entry successors
must be checked against the resulting clinch/cage state, not the entry's standing start position.
Keep historical authoring checks layered through explicit expected follow-ups, not field omissions.
Specialist attacks/back takes/escapes reset ground inactivity even on defended attempts, just like
ordinary submission and recovery attempts. Stationary rides/holds still advance referee inactivity.
Run `fight_ground_activity_regression_test.py` for both ownership directions and warning thresholds.
Phase 29's fresh 300-fight coverage report must show all 16 additions, at least six legal top
submissions in guard and half guard, and at most 25% concentration in one top submission. Retain
the ungated `top_submission_chain` for fighters below specialist skill gates. Technique identity
must not alter the broad submission resolver's selected choke/lock mechanics or finish result.
Phase 30/33 adds 33 moves and 22 defenses. Its full-fight report must show every new move, four
recoveries per ground position, two definitions per referenced defense family and fewer than ten
uses of an identical rendered defense clause across 300 fights. Count clauses actually present in
rendered commentary, not all candidate wording. Body-only and punch-only defensive tags constrain
selection before scoring. Name/wording choices must remain deterministic and consume no RNG.
Explicit kick/knee/elbow tags override a broad power-punch or dirty-boxing action when checking
punch-only defense eligibility; those calibrated actions are not proof of a boxing weapon.
The named-defense reachability probe must supply a permitted incoming target/weapon for restricted
defenses. Blank synthetic attack metadata is not evidence that a body-only or punch-only defense
is unreachable; keep the negative runtime eligibility test alongside the positive audit probe.
`analysis/compare_bottom_move_expansion.py` reconstructs the reviewed Phase 29 registry in memory
for paired 300-fight evidence: bottom vocabulary must grow while outcome and broad exchange
signatures remain equal. Do not overwrite user fighters, saves or historical source to run the pair.
Protect defensive mastery IDs through `PERSISTENT_DEFENSE_IDS` as well as move ID protection.

`fight_engine_audit.py` and `analysis/fight_engine_baseline.json` are the preservation authority for
the staged fight-engine roadmap. The UI-free harness clones its inputs, restores process RNG, and
captures per-exchange evidence without changing the underlying engine result. Before and after each
fight-engine phase, run `analysis/generate_fight_engine_baseline.py --verify
analysis/fight_engine_baseline.json`. Use `--exact-parity` only for an architecture slice that does
not intentionally remove legacy presentation draws from the combat stream. RNG separation is
accepted on the locked distribution gates, with hard overall/KO/TKO limits and confidence-aware
small-group checks; do not require identical individual outcomes after stream decoupling. Do not
regenerate the checked-in baseline after a code change merely to make drift disappear. A deliberate
baseline replacement requires an explicit balance change and synchronized report/document updates.
`analysis/fight_engine_action_baseline.json` is the pre-move-expansion authority for action frequency,
effectiveness, damage, energy, counter, position and finishing contribution. Regenerate it only for
an explicitly approved mechanical baseline replacement; verify it with
`analysis/generate_fight_action_baseline.py --verify analysis/fight_engine_action_baseline.json`.
The canonical isolated runner executes this verifier after the result baseline so presentation-only
changes prove that neither finish rates nor the amount and effectiveness of the ground game moved.

`compare_to_accepted_calibration()` is the exact headline release gate layered over the older
tolerance report. The canonical isolated runner executes the complete 3,840-fight verifier and must
reject a one-bout change from 2,319 finishes, 633 KOs or 731 TKOs. Do not weaken this to rounded-rate
comparison: the displayed 60.39% / 16.48% / 19.04% values are derived from those integer counts.
It must also reject a competitive finish rate outside 48-54%, a competitive submission-family rate
outside 15-19%, zero Doctor or Injury Stoppages, missing five-round evidence, or fewer than 6% of
five-round finishes in rounds four and five. The current accepted corpus has 1,408 competitive
finishes (48.89%), 488 competitive submission-family finishes (16.94%), four Doctor Stoppages, ten
Injury Stoppages, and 164 of 839 five-round finishes in rounds four or five (19.55%). These checks
reconcile the historical finish audit without applying its obsolete global retunes: mismatch bouts
drive the 60.39% aggregate, while competitive fights already meet its realism bands. Do not lower
global KO/submission conversion or halve championship dampers unless the user explicitly authorizes
a new mechanical baseline.

`FINISH_METHODS`, `KO_METHODS`, `SUBMISSION_METHODS`, and `KNOCKOUT_AWARD_METHODS` in `constants.py`
are the downstream method-classification authority. Career stats, seasonal counters, recovery,
contractual finish bonuses and excitement use the shared finish families. Knockout of the Year uses
the narrower highlight set so Doctor and Corner Stoppages cannot win a strike-highlight award.
Never reintroduce substring or exclusion-based finish detection in a consumer.

The original frozen baseline rates are 59.64% finishes, 15.70% KO, 19.66% TKO, 22.29% submission
and 1.17% technical submission across 3,840 fights. The accepted post-roadmap calibration is 60.39%
finishes, 16.48% KO and 19.04% TKO. Competitive low/mid/high and mismatch results are separate groups;
follow the tolerances in `FIGHT_ENGINE_DEVELOPMENT_PLAN.md`. Detailed-skill coverage also
distinguishes direct fight inputs from `dedication` and `weight_cutting`, which operate through camp/
development and weigh-in state respectively. Do not add a detailed fighter attribute without either
using it mechanically or documenting and testing its pre-fight role.

`FightResult` is the structured MMA result boundary. `simulate_fight_result()` returns it directly;
legacy callers continue through `simulate_fight()` and its five-item tuple. Native trace events use
private `a`/`b` slots and retain action, position ownership, gas, location damage, cuts, knockdowns,
strikes, takedowns and submission deltas, followed by exactly one `official_result` event. Adding
trace evidence must not consume RNG or change any baseline signature.

`fight_moves/` is the canonical MMA move registry, preserving the former module's public imports.
`schema.py` owns immutable definitions and closed metadata vocabularies; `catalogue/` contains
domain modules whose historical batches are concatenated in explicit order. Never regroup those
batches by family: tie-breaking and fallback order are compatibility behavior. `index.py` builds
immutable ordered lookup tables once; empty targets exclude targeted moves, while unknown targets
still allow untargeted moves. `validation.py` rejects unknown tags, metadata and removal of IDs in
`legacy_ids.py`; keep that permanent ID set synchronized with the historical parity reference.
Behavioral tag constants live in the schema and are reused by selection. Run both registry test
suites and the byte-identical parity gate after structural changes, followed by full fight gates.
`coverage.py` (re-exported by validation) reports eligibility relative to supplied engine contexts.
Use pre-exchange position/action/target triples from complete traces, never registry declarations
or intermediate position paths as proof of a selection opportunity. The 300-fight coverage reference
is a named allow-list for existing gaps, not evidence that rare specialist positions are impossible.
New gaps must fail; tighten resolved allowances rather than expanding them to hide dead content.
The variety report's denominator is every exchange selection; per-fighter variety includes both
corners, including a zero-action fighter. Keep draft authoring modules outside catalogue assembly
until the preceding runtime revision's gates finish; test combined definitions without mutating
the active registry. Register each reviewed batch with permanent IDs, an exact versioned snapshot
and fresh ordinary-fight appearance evidence before calling it delivered.
The Slice 5 paired test reconstructs `move_registry_phase30_33.json` and patches only an isolated
process's move lookup/registry for the two arms. Keep the reference immutable and compare broad
mechanical signatures alongside actual selection evidence; registry legality alone is insufficient.
The Slice 6 paired test uses the immutable Slice 5 snapshot. Its registration regression also
locks an authored minimum of 18 moves per supported style plus an exclusive combination/finisher;
do not restore the initial thin-style allowances once these floors have been reached.
When comparing a Slice 6 source definition with the live registry, apply the registered
`ACTION_DIVERSE_FOLLOWUP_UPDATES` and `CONTINUITY_FOLLOWUP_UPDATES` first. Those reviewed layers
intentionally replace `follow_ups`; equality against the earlier source literal is a stale test,
while any difference in another field remains a regression.
Skill-median warnings distinguish representative use from maximum-skill reachability. Authoring
helpers in `presets.py` leave existing definitions untouched; document fields and required metadata
in `docs/FIGHT_MOVE_SCHEMA.md` and run the coverage/preset regression plus unchanged parity.
Move IDs are stable trace/save-facing identity;
`fight_moves/chains.py` validates an immutable follow-up graph during registry construction.
Use iterative topological ordering so large catalogues do not depend on Python's recursion limit.
`chain_depth(move_id)` counts maximum possible successor edges (leaf zero); actual trace sequence
length must be measured from selected exchanges, never copied from this potential-depth value.
Run `fight_move_chain_regression_test.py` and exact registry parity after graph-only changes.
definitions must use supported positions, styles and detailed skills, and follow-up IDs must resolve.
Broad actions remain the calibrated resolution boundary. Deterministic move selection may use detailed
skills, style, stance, matchup and a real counter window, but must not consume mechanics, officiating,
judging or presentation RNG. Move energy, miss risk and counter vulnerability may only alter later
legal move identity through bounded, decaying bout-local state; they must not alter broad gas, damage,
landing or finish conversion. An unavailable move uses
an explicit `generic_<action>` fallback rather than inventing an illegal technique.

Release move audits must keep the frozen `matchup_specs()` corpus unchanged. Supplemental style coverage
belongs in `move_report_specs()` so the exact 3,840-fight result/action baselines remain comparable. A move
missing from the general sample is not automatically dead: the targeted registry reachability check must
prove whether a legal, skill-supported specialist can select it. Dominance comparisons must use the same
parent action and legal position, not aggregate techniques that cannot compete in the same state.
Direct registry reachability is not proof of full-fight reachability when a test supplies a target or position
that the broad resolver never emits. New ordinary standing and common-position ground content must also appear
in the representative 880-fight report; reserve probe-only absence for genuinely rare specialist
positions/actions. The expanded catalogue retains one exclusive combination and one
exclusive finisher for each of the 18 supported styles, ten earlier expanded standing combinations,
six uncommon authored standing finishers and 23 expanded ground techniques. The turtle wrist-ride striking chain
is the only latest addition intentionally absent from the representative corpus; targeted reachability and
the specialist transition path remain its gates.

Moves tagged `style-combination` must name exactly one supported `preferred_styles` owner, retain at
least three ordered `components`, and be filtered before scoring unless that owner is the fighter's
primary or secondary style. Signature or mastery data must never bypass this eligibility rule. These
chains remain identities beneath one already-resolved broad action: their components, follow-ups and
commentary may change, but they must not add a strike, landing, damage, transition or finish roll.

Moves tagged `style-finisher` follow the same single-owner primary/secondary-style restriction and
must be either a strike or submission. Their deterministic appearance window may make an already
selected technique more recognisable, but it must never create or convert a KO, TKO, submission,
damage event or stoppage. KO/TKO narration must use trace-backed impact from the causal move;
submission narration must use the last resolved submission payload. Every style finisher must remain
reachable, appear in the 880-fight representative report and preserve exactly one official result.
When a fighter owns another legal signature finisher, that individual signature takes selection
priority over the generic style finisher during the bounded authored-finisher window.

The Standing group includes `combination_punching`, `body_punching` and `counter_timing`. Legacy
non-empty detailed profiles derive them in `ensure_detailed_skills()` from existing saved ratings;
never replace them with generic 50s or consume RNG during load. Distance management remains the
existing footwork/feints/mobility/reach bundle rather than a duplicate detailed attribute.
Profile stats, detailed-skill popups and skill-card readers must use a copied,
deterministic projection rather than `ensure_detailed_skills()`. An empty
legacy dictionary may display bounded values derived from the saved broad
ratings, but opening or refreshing a profile must not generate, persist or
repair detailed skills. Explicit load, editor, simulation and migration paths
remain the only owners of the RNG-backed repair.
Academy rival-program tables must likewise call `rival_academy_program(...,
repair=False)` and render a defensive projection. They must not seed missing
AI youth-program strategy data while the Academy page is opened or refreshed;
calendar progression and explicit rival-academy actions keep the repairing
default.
When a detailed-skill group expands, preserve development exposure as well as serialization. Standing
training scales its successful-block point budget for these three added skills; otherwise a fixed budget
silently dilutes every striker's development even though fight-result calibration remains unchanged.

Kick-tagged registry moves must define a supported target, `side`, `range_band`, and at least one
`defense_families` entry. Spinning/flying/high-risk techniques require a meaningful minimum-skill
floor, energy/counter risk above neutral, and the deterministic rarity gate in move selection. Reuse
the existing high/low/creative kick, knee, elbow, flexibility, mobility and reflex ratings unless a
future skill audit proves a genuinely distinct axis.
The `finisher` tag is a rare identity gate, not a finish modifier. A finisher must be a skill-gated
standing strike with above-neutral energy and counter risk; its shared deterministic gate may select the
named move only after the broad action has resolved and must not consume RNG or alter finish conversion.
When a KO or TKO has causal trace evidence, the registry move is the authoritative strike name. Legacy
finish-color banks may not leave a second, contradictory uppercut/hook/kick beside that causal move.

Takedown-tagged registry moves must define `entry_family`, non-empty `defense_families`, and only
legal `finish_positions`. The resolved trace remains authoritative for the actual position path and
controller; registry metadata must never claim a finish position the broad resolver did not reach.
Current common shot and takedown success settles in guard/half guard, not side control. Draft
entry follow-ups must include legal top-ground continuations; a cage finish can cover a near-success
entry, but should not be the only branch offered after a completed takedown.
Hand fighting, underhooks and wall walking currently reuse clinch control/defense, cage wrestling,
get-ups and scrambles rather than adding duplicate detailed attributes.

Submission-tagged registry moves must define a position-legal `attack_path` and non-empty
`failure_outcomes`. The resolver's recorded `submission_escape` and actual position path remain
authoritative; move metadata may describe legal possibilities but must not invent a finish or a
transition. Chaining currently reuses transitions, positional ability, submission attack, leg locks,
control, scrambles and fight IQ rather than adding a catch-all submission-chaining rating.

Common ground moves must be restricted to positions where their broad action can actually be chosen.
Position-specific ground striking still resolves through `ground_strikes`; passes/climbs through
`advance_position`; sweeps through `sweep`; recoveries/get-ups through `recover_guard` or `stand_up`; and rides
through `ground_control`. Named identity must not directly change damage, success, position or finish chance.
Every authored ground-strike chain needs a factual component template that reconciles realistic 10-26-strike
broad volume, and a ground TKO must name the causal registered strike chain rather than generic legacy copy.
An effective registry move tagged `control` may seed one legal bounded follow-up from an existing `control`
outcome; this changes only later move identity and must never grant a free exchange or change control scoring.

`Fighter.signature_moves` contains at most three unique stable registry IDs. New-universe generation
may derive skill-supported signatures deterministically; ordinary save load must only normalize known
IDs and must not invent a new set. A legal signature receives a bounded selection preference but
never bypasses minimum skill, position, target, counter-window, defense, or finish resolution.
`career_signature_stats` folds the last fight's attempts/effective uses/finishes during the same
career-stat commit that clears `last_fight_stats`; preserve fighter-ID separation in persistence and UI.

`Fighter.move_mastery` contains normalized 0-100 values keyed by a move ID or `defense:<defense_id>`.
It is persistent fighter development, but it may only shape named technique selection beneath the broad
resolver. Camps may improve focus-aligned mastery and grant a signature at the audited threshold;
academy prospects retain their own mastery dictionary and copy it on graduation; annual veteran decline
may reduce high mastery after `prime_end + 2`. Legacy load defaults to an empty dictionary and must not
consume RNG or invent mastery merely by opening a profile.

`DEFENSE_REGISTRY` is the canonical defensive identity surface. Every exchange trace retains a known
`defense_id` and payload selected from the attacking move's legal defense families and the defender's
skills. Named defense is evidence, not a second success roll: never use it to retroactively change the
already-resolved outcome or consume another combat draw.

Tactical move reads are bout-local, derived only from earlier public trace, and capped per counter.
Plans may weight matching move tags; body/leg/setup evidence may open later families; repeated move IDs
may be penalized; and opponent-pattern counter bonuses require a real counter window. Preserve
`selection_reasons` for explainability. Never persist these reads, scan career history during a fight,
or convert a move-family preference into direct landing/finish probability.

Registry follow-ups may create a bout-local move chain only after effective use. A matching legal
alternative may receive continuation preference only after normal style, skill, target, counter
and rarity gates, and only within the strongest five ordinary candidates. Keep the authored-top
bypass. Selection happens after resolution, so ownership eligibility must use the supplied
pre-exchange snapshot, not the newly reversed top/bottom state. Seed successor roles from the
actual settled ownership; same-position sweeps are effective, referee resets are not.
Occurrence IDs use actor/starting round/tick and actual depth increments only on a selected branch;
do not confuse this with the graph's maximum possible depth.
follow-up receives a bounded selection preference for at most two ticks in the same round, and the trace
must identify its source and completed step. It remains one ordinary broad action, never a free attack.
Multiple follow-ups are legal branches. Choose only a branch valid for the resulting position, retain
the options/reason in trace evidence, and let a named frame/evasion/escape select the alternate branch.
Authored strike-combination templates must identify their actual component weapons and reconcile sequence
numbers and landed totals at realistic broad-action volume; a generic action fallback is not sufficient
coverage for a newly named sequence.
All supported primary styles must retain explicit tag preferences and stay distinguishable in the
pairwise release-report distance check. Stance and striker/grappler matchup reasons must remain traceable.
Dynamic stance changes are bout-local and cooldown-bound. They require a natural switch stance or high
footwork/adaptability, retain from/to/round/tick/plan evidence, and must not mutate the fighter's saved
base stance or add a new mechanics RNG draw.

Archived fight logs may persist bounded `round_analysis` derived from their completed trace. Replay UI
must tolerate old logs without it and show only recorded moves, defenses, sequences, stance switches and
plan history; it must not reconstruct results, expose sealed cards early or mutate career state.

Fight presentation must render from the completed trace. Natural Broadcast prose uses the recorded
actor, move, outcome and salient target, defense or position; it must never join a named move to the
older broad-action `result` text. Detailed commentary and `round_analysis` retain target, defense and
meaningful follow-up labels without raw bracket metadata. Finish prose must use the final exchange's
actual move and settled position, retain authored submission/medical/injury/head-kick/walk-off detail,
and contain at most one intervention clause and one official announcement. A body- or leg-kick
knockdown is not an `injury_stoppage`; only the separate body/leg stoppage check may assign that
finish method. Doctor review uses structured cut evidence and may become eligible only at the
between-round tick. Presentation-only walk-off variation may use the presentation stream, but an
existing mechanics draw must not be removed, added or reordered merely to select wording.
Round/UI summaries expose bounded move-family effective/used counts, never raw unbounded dumps or
unsealed judge totals. `last_fight_stats`, FightResult metrics and `career_move_family_stats` must
reconcile with the same exchange events; presentation must not draw simulation RNG.

At the start of a bout, `simulate_fight()` establishes explicit mechanics, officiating, and
presentation streams. All combat draws go through `fight_mechanics_rng()`, referee/stoppage/judging
draws through `fight_officiating_rng()`, and wording through the presentation helpers. Do not add a
direct `random.random()`, `random.randint()`, or `random.choice()` call to `fight_engine.py`; the
focused regression treats one as an accidental stream leak. The caller's public RNG advances to the
combat stream's final state so sequential unseeded cards continue to vary.

Commentary variation uses the bout-local presentation RNG through `fight_presentation_choice()` and
`fight_presentation_random()`. Do not add global `random` calls for wording, clocks, ambience, or
phrase selection. A foul or other event that changes gas, damage, position, scoring, or stoppage
risk belongs in a mechanical resolver before its text is rendered; `dynamic_flavor_line()` must
remain presentation-only. The phrase-bank regression must keep winner, method, round, stats and
cards identical when wording is replaced.

`fight_commentary_mode` defaults to `Broadcast`; `fight_commentary_personality` defaults to
`Balanced`, with `Technical`, `Excitable`, and `Concise` as presentation-only alternatives. Both live
in `rules`, require old-save normalization, and may affect wording or density only. Corner advice may
cite completed public trace evidence such as gas, damage, control, repeated moves and effective
families; never expose hidden ratings or repeat developer-facing text about an unassigned plan.
Between-round feedback must name a verified head coach and Gym when available, give a factual round
read and a separate actionable instruction, and vary delivery by commentary personality without RNG.
If both opponents share one verified Gym, identify each fighter's camp corner without assigning the
same head coach to opposing stools. The commentary report permanently gates speaker/fighter identity,
actionable wording and hidden-rating leakage across representative complete fights.

`TRAIT_COMMENTARY_INTROS` must cover `TRAITS` exactly. Every saved trait receives one natural opening
line, but a live trait call requires completed trace evidence matching its claim: target, move tag,
counter, position, submission attempt, plan change, accumulated damage, recorded gas, timing or bout
context. `record_fight_trace_exchange()` stores the selected line and enforces at most one contextual
trait call per fighter per round and two per fighter per bout. Rendering that line is deterministic,
must not consume any RNG stream, and must never imply survival, a finish or an injury that has not
already been resolved. Do not restore the older random trait branches in `dynamic_flavor_line()`.

Camp commentary must resolve `Fighter.camp` against an actual current `Gym` before naming a coach,
city, region or specialty. Saved camp strings may instead be promotion, feeder, academy, unknown or
legacy labels; introduce those with natural neutral wording and never infer Gym facts from the label.
When both opponents resolve to the same verified Gym, emit one stablemate-room introduction rather
than assigning the same head coach to two opposing corners. A contextual
camp call requires a completed exchange matching one of the resolved Gym's recorded specialties:
boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning. Store the selected
line on the exchange trace, cap it at one per fighter per round and two per bout, preserve it in
Broadcast, and consume no RNG. `Prospect Development` is opening identity only unless future trace
evidence provides a genuine live-fight predicate. Focused coverage must compare the same seeded bout
with and without verified Gym metadata and require identical result, metrics, scoring, mechanical
trace and process RNG state.

Audit finish rates by fighter tier, not only across a random-paired pool. Random pairing
over-represents mismatches, which finish more easily than realistic cards.

MMA judging consumes `round_evidence_from_trace()` only. Do not award score value for gas,
professionalism, discipline, home support, experience, pressure, popularity, or names; those inputs
may change execution but are not judging criteria. Apply effective striking/grappling first,
effective aggression only when that evidence is close, and control only when both are close. Judge
variance belongs on the judging substream and only inside the ambiguity band, so scoring work cannot
change a later stoppage draw or reverse clear dominance. Store the player-facing verdict separately
from canonical `Decision`/`Draw` method values for save and downstream compatibility. Every 10-8 and
point deduction must retain round evidence in the official card and trace.

In-bout `damage`, `head_trauma`, `body`, and `leg` are persistent trauma channels; `hurt` is the
transient stun/instability channel used by immediate survival and calibrated stoppage checks. The
legacy `head` channel is a short-term reaction load and may settle during survival, while every head
impact must also increment `head_trauma`; trace and post-fight metrics expose only the permanent
channel. Defensive success, `survive`, and `recover_between_rounds()` may reduce `hurt` and restore
bounded gas, but must never subtract persistent location damage. Body trauma affects output/fatigue,
leg trauma affects mobility/kicks/shots/stand-ups, and head trauma affects reactions. Cuts use `cut_state`
  records with location, severity, bleeding, swelling and vision risk while the numeric `cuts` count
  remains compatibility telemetry. `last_fight_stats` is the shared Fight Night/post-fight medical
  record; recovery logic must read its damage and `cut_details` rather than inventing unrelated harm.
  Run `set_post_fight_recovery()` and `apply_visible_trauma_consequences()` before
  `commit_career_stats()`, because that final commit clears `last_fight_stats` after the medical
  evidence has been consumed.

Visible damage narration is a deterministic presentation layer over those persistent totals. A bout
latches each head, body and leg milestone once, records the structured event in its trace, and retains
the corresponding line in Broadcast and round analysis. It must not consume any RNG, alter trauma,
or add a stoppage opportunity. Broad milestones may describe only supported visible states such as
bruising, guarding, a weight shift or a limp; never infer fractures, organ damage, concussion, or an
exact body-part location. Exact location, bleeding, swelling and vision language must come from the
structured `cut_state` record. When damage copy changes, run the focused milestone/RNG regression,
the commentary report and both frozen result/action baselines.

Fight plans are scheduled-bout state keyed by `fighter_id`, never display name. Player-created
bouts must store an explicit plan for every known corner; `apply_world_data()` normalizes supported
values and gives legacy missing entries Balanced. AI/world bouts must set `ai_controlled` so
`ai_fight_plan()` uses the shared execution model. A payload with no plan marker is a compatibility
bout: it stays Balanced and does not begin automatic between-round switching. Plan effects belong
in action weights, target shares, counter opportunities and energy cost—not direct result or finish
modifiers. `adapt_fight_plans()` may read trace evidence, gas and visible trauma only. Evidence-led
changes retain the repeated opponent move or successful own family, adjustment round and confidence;
do not oscillate more than once in a round. When changing
plans, run `fight_engine_regression_test.py`, the save/load smoke test and the frozen 3,840-bout
verifier; do not alter `competitive_finish_conversion()` or regenerate the baseline to absorb drift.

Each exchange trace must retain a bounded `exchange` chain with setup, defensive response, counter
opportunity/consumption, follow-up, ordered combination components and no more than five phases.
Derive semantic labels from the already-resolved action, position and skills; recording trace detail
must never consume another mechanics draw. A counter is valid only when a prior failed or defended
attack created its `counter_window`. Combination components are evidence for aggregate strike stats,
not extra attacks: their landed count must stay at or below attempts. Preserve deterministic chains
and the controlled Counter-striking-versus-Pressure regression when changing initiative or actions.

`ALLOWED_FIGHT_TRANSITIONS`, `GROUND_POSITIONS`, `validate_fight_transition()` and
`set_fight_position()` are the MMA positional authority. Ground states require distinct `a`/`b`
top and bottom owners and no clinch controller; open range retains none. Use
`record_intermediate_position()` for a real but unconsolidated state inside one exchange, and keep
its complete validated `position_path` in the trace. Elite specialists may consolidate a failed shot,
standing rear lock or leg entanglement into a persistent next-tick state only at the audited thresholds;
the 720-fight specialist report must continue to prove each state has legal follow-up action families.
Other brief positions require the resolver to award durable control. Submission attempts that do not
finish must set `last_submission_escape`
with their retained, recovered, reversed or worsened consequence. Any new grappling position needs
an allowed entry, exit, action selection, ownership test and commentary consistent with the trace.

Competitive same-tier targets:

- Low tier (`overall < 68`): about 50-56% finishes.
- Mid tier (`overall 68-80`): about 32-42% finishes.
- High tier (`overall >= 80`): about 38-45% finishes.

The best single audit is realistic matchmaking: pair fighters with an overall gap of at most six
across all tiers. A useful comparison shape is Decision ~47%, KO ~16%, TKO ~15%, Submission ~19%,
or roughly 52% finishes. A mixed random pool may report 60-65% finishes because of mismatches; that
is expected and should not be tuned away by weakening the whole engine.

Historically, elite competitive fights became too decision-heavy because damage scaled with strike
margin while defense and KO thresholds rose with skill. The current model gives impact meaningful
raw-power scaling and flatter threshold growth. Tune mechanics and probabilities, then rerun the
per-tier audit. Never overwrite the final method merely to hit a target percentage.

## 10. Contracts, Weigh-ins, and Shared Rules

### Contract terms

Player-negotiated contract duration is normalized to 1-60 months. Duration is secondary to fair
compensation: fighters should not accept badly under-market base pay only because the company asks
for years of control. Security has diminishing value through 48 months and no additional scoring
benefit beyond that point. Keep `normalized_contract_months` and
`contract_duration_offer_score` aligned with the negotiation UI and smoke regressions.

All contract money and percentages are domain-validated, not merely widget-validated. Purse,
signing bonus, win bonus, finish-bonus percentage, PPV points, and guaranteed fights cannot be
negative, and invalid input must fail before cash or roster state changes. An agreed purse is paid at
its full contract value; company scale cannot silently discount it on fight night. Projection,
actual payout, the finance ledger, and the event report must consume the same clause calculation.
Every official player bout, including a draw, consumes one guaranteed fight. Ordinary guarantees
remain visible until fulfilled, and an expired deal never renews for free: use explicit negotiation
or the enabled paid auto-renew workflow.

### Weight cuts

Use `perform_weigh_in` for player events, AI cards, and sandbox fights. Do not add a second shortcut
calculation. Camp length, body fit, cut skill, scale weight, title-fight rules, and the resulting
performance penalty must stay consistent across every fight path.

## 11. Gyms, Development, and Awards

Gyms are first-class world objects. Their effects consider:

- quality, facilities, and reputation;
- room morale and capacity/crowding;
- specialties and scouting;
- fighter style fit; and
- fighter age, prime, potential, and dedication.

Opening gym membership must be capacity-aware. Shipped elite rooms should not begin at several
times their capacity, because `gym_attention_multiplier` then suppresses the development system the
gym is meant to showcase. Database/seed regressions should flag ordinary gyms above 150% opening
load and keep regional team labels geographically consistent with tracked gyms.

The gym viewer is accessible from the World Hub. If gym fields change, inspect and usually update:

- the `Gym` dataclass;
- `seed_gyms`;
- serialization and `apply_world_data`;
- `refresh_world` and `open_gym_viewer`; and
- `smoke_test.py` when core assumptions change.

Season statistics are fed by `record_season_result` for every decisive player and AI fight.
`run_end_of_year_awards` runs at the year rollover and appends to `awards_history`. Adding a new fight
path without season tracking silently biases awards toward whichever path still records results.

### Staff employment and effects

Staff are dictionary records in `self.staff` and `self.staff_candidates`, seeded in `seeding.py` and
repaired by `WorldMixin.ensure_staff_profiles()`. New or migrated records carry a role, skill,
salary, morale, `contract_months`, `contract_type`, `contract_start_month`,
`contract_expiry_month`, and negotiation heat. Old saves must receive those defaults without losing
the existing staff member.

`constants.STAFF_ROLE_EFFECTS` is the player-facing source of truth for the seven staff roles:
Scout, Doctor, Marketing, Matchmaker, Drug Testing Officer, Broadcast Producer, and Talent
Relations. Every listed role needs both a readable explanation in the Staff screen and a simulation
hook. Staff quality and morale flow through `staff_skill()` and `staff_effect()`; do not add a role
that only changes a label. Current hooks cover scouting and academy reports, recovery and medical
costs, hype and commercial reach, matchup/card quality, drug-test accuracy and cost, broadcast
quality/reach/production cost, and fighter negotiation leverage. Point effects and cash-valued
negotiation benefits are separate: use `staff_effect()` for bounded gameplay points and
`staff_negotiation_discount()` when converting Talent Relations quality into a dollar discount.
Manual drug testing must use the same compliance discount model as event accounting.
The first J5 compliance slice stores each manual sample as a stable,
save-owned preliminary case with fighter/test identity, policy snapshot and
evidence scope. A preliminary alert is not a proven violation and must never
be represented by mutating `fighter.injured` or disciplinary state. The
`None` policy must short-circuit before sampling, charging or consuming test
RNG. Read-only case inspection must return defensive copies and never rerun a
test. Provider selection, confirmation, appeals and sanctions remain gated
until their versioned policy/balance table is approved.

Monthly world progression checks staff expiry warnings before decrementing contracts. Expired staff
leave payroll and the roster unless finite Scout work (a report, search, or academy-network setup) is
still using them; that Scout is held for one month so the assignment can finish. An established
ongoing academy network is not finite work: contract expiry closes the network and its open leads
instead of renewing the assigned scout forever. Hiring, renewal, and firing use the Staff screen's
negotiation/severance actions, and firing a busy Scout is blocked. The Expiring Contracts tab is a
filtered operational view, not a second staff list: actions must resolve the selected staff member
by identity and continue to use the world-layer contract rules.

The Staff page's AI Staff Ledger is a read-only projection over non-feeder
promotion staff and the shared candidate market. It must expose source,
promotion/staff identity, role, specialty, skill, morale, salary, contract
term/expiry, roster payroll and identity quality without calling hiring,
affordability, contract-tick, offer-refresh or RNG paths. Stable promotion ID
plus staff ID is the row key; duplicate identities receive deterministic
suffixes, while name/role/index fallbacks are explicitly legacy and
non-durable. The complete underlying staff records remain untouched.
View Evidence Audit may expose the saved finding identifiers and messages in a
scrollable read-only reader; it must not reinterpret a finding as a repair
permission or execute the referenced work.
Retention Watch rows must use the same stable staff identity and restore a
still-visible selection after refresh/reordering. ID-less legacy rows may use a
clearly non-durable fallback, and rebuilding the table must not recalculate or
mutate contract, morale or retention state.

Scouting assignments resolve both fighters and staff by durable IDs. A legacy name-keyed fighter
report may migrate only when the name identifies exactly one live fighter; ambiguous reports must be
quarantined and must never become a read-through fallback for every namesake. Load repair must not
consume simulation RNG, and a legacy report without a trustworthy completion marker is stale rather
than newly current. Starting a replacement report keeps the prior completed snapshot available until
the new work succeeds; cancellation or observation expiry restores that snapshot. Cancelled,
expired, and stale dossiers are eligible for later talent-search rediscovery. Completed searches
retain their ordered fighter-ID lead list, while long assignment/search histories are bounded.
Pending reports contain no hidden-rating-derived notes or estimates. Opinion notes are generated only
at completion and remain separate from structured public/live-fight evidence. Automatic department
work is paid and capped at one dossier per calendar week. Talent searches rank existing world fighters
and must never create supply as a fallback; market churn owns new fighter creation. Search Aim selects
candidate scope, Search Priority changes ranking within that scope, and signing Logic controls the
post-report recommendation. Age/style constraints may return explicitly labelled Near Matches when
the exact pool is thin. Standard briefs finish normally, Priority briefs trade extra cost for time,
and Ongoing briefs retain a scout slot and refresh every 13 weeks; persistence and workload checks
must treat `Monitoring` searches as active. Region knowledge, current report state, bounded prior snapshots, ID-safe
watchlists, structured scouting history, and alert dedupe state are persistent. Report ageing begins
after 26 weeks, and exact current ratings require a comprehensive high-confidence repeated Full
Evaluation; do not turn a single report into a permanent exact-rating unlock. Every decisive and draw
MMA result path must pass ID-first opponent, outcome, method, fight context, and `last_fight_stats`
evidence to `complete_fight_observation()` before `commit_career_stats()` clears the live metrics.

When changing staff behavior, update `constants.py`, seeding, world progression, persistence/load
repair, `ui.py`, and `views.py` together. Add smoke coverage for role descriptions, offer scoring,
legacy migration, expiry removal, and round-trip persistence. Review the fighter Contracts tab as
the parallel player-facing negotiation pattern so staff and fighter contract UX remain consistent.

## 12. UI, Themes, and Accessibility

The user strongly dislikes unreadable or cluttered UI. The game is normally played maximized, but
layouts must still degrade cleanly at smaller supported widths.

- Avoid hard-coded white or pale backgrounds. Use `self.colors["cream"]`,
  `self.colors["text"]`, and the active palette.
- Refresh methods for lazily built screens must start with widget-existence guards. A domain action
  such as starting a scouting report may be used before Staff, Finance, or another screen is built;
  successful state changes must never fail because an unrelated tree does not exist yet.
- Do not leave player-facing `ttk.Progressbar` widgets on the native grey defaults. Loading activity
  uses `Activity.Horizontal.TProgressbar`; live-fight freshness uses the red/blue corner styles, all
  with a dark track and a fill-to-track contrast ratio of at least 3:1.
- Keep dense database screens sortable and filterable.
- Add double-click profile/viewer behavior where it is natural.
- Do not add giant explanatory landing pages or unnecessary tabs.
- Do not allow text to overlap. Keep buttons and badges stable in size.
- Use flexible grid columns for variable-length names and separate fixed cells for critical stats.
  For example, promotion name and `Popularity` must never share one clipped label.
- Prefer dark, game-like panels and inline status/decision areas.
- Reserve modal confirmation for destructive or genuinely blocking decisions.
- Synchronous operations that can visibly stall the Tk event loop, especially Quick Load and Save
  Manager slot loads, must open the reusable `show_busy_overlay` panel before heavy work, update it
  at stable phase boundaries, and close it in every success and failure path. Keep the panel modal so
  users cannot start a second state-changing action while the first is rebuilding shared state.
- Inbox and Matchmaking deliberately set `_force_viewport_width` because their internal responsive
  panes and table scrollbars own overflow. Do not let either screen's natural table width widen the
  entire page canvas again. `configure_inbox_panel_layout` stacks Owner Goals below Inbox on narrow
  pages; `configure_booking_panel_layout` moves Current Fight Card above Available Fighters.
- Matchmaking's Available Fighters tree always retains all 20 underlying columns. Its Essentials,
  Readiness, Form & Fitness, and All 20 presets change only `displaycolumns`; they must not rebuild
  rows, clear selection, or make any metric unreachable. The Compare Selected action reuses the
  shared fighter-comparison window instead of duplicating a second matchmaking tree. Its five
  booking actions use one row on wide panes and the 3+2 grid below 700 pixels; preserve both modes.
- Ordinary Available Fighters row clicks intentionally toggle that row into or out of the current
  selection without requiring Ctrl, for both matchup pairs and 4/8-fighter tournaments. Double-click
  must resolve and open the fighter directly under the pointer rather than the first selected row.
  Keep Matchup Insight synchronized with the empty, one-fighter, pair-ready, and tournament states.
- `configure_show_details_layout` owns the expanded Show Details geometry. It grids stable Event /
  Venue, location/provider, date, primary-action, and show-tool frames into wide, medium, or narrow
  arrangements; never rebuild or reparent their widgets. Keep `schedule_status`,
  `event_broadcaster_status`, and `event_atmosphere_status` managed and wrapped in every mode, and
  retain the canonical field attributes because refresh and event code writes through them.
- Matchup Insight preserves detailed selection history, booking context, and the row-colour guide
  behind a named persistent disclosure (`rules["ui_matchup_insight_collapsed"]`). Empty booking
  notice and title-warning labels must not reserve table height, but must reappear immediately when
  their variables contain actionable text.
- Collapsible content must use `disclosure_section`: its named Expand / Collapse button and summary
  remain visible when content is closed. The three disclosure states live in save-compatible `rules`
  keys. Never replace these with arrow-only headers or blank collapsed space.
- Do not restore full-width first-visit or `NEW HERE?` banners on dense management screens. Put brief
  instructions in persistent local summaries, table cues, detail placeholders, or meaningful empty
  states so onboarding help does not push data and action buttons below the viewport.
- Vertical resizers must keep applying their configured fractional target while the window moves
  through its startup and maximize sizes. Stop automatic placement only after the player releases
  directly on the sash; otherwise a small pre-maximized layout can permanently clip action footers.
  Mail / Decisions additionally reserves a 425-pixel top pane and grids its eight actions into two
  non-shrinking rows; only the Inbox table row may absorb a vertical-space shortage.
- Current Fight Card groups hype, build, fatigue A/B, and medical return A/B in its `booking` column
  so the complete card fits without page-level horizontal scrolling. Available Fighters intentionally
  retains all 20 dense columns and its local horizontal scrollbar, plus the visible column-count cue.
- `CLOSED` is too ambiguous. Free agents in a player-disabled division show `DIVISION CLOSED`, and
  the detail panel points to `Roster > Manage Divisions`.

The main window requests Windows' `zoomed` state and falls back safely when unavailable. Do not
replace that with a fixed screen-size geometry.

### Tabs and themes

Tab states must remain distinguishable for mouse and keyboard users: default, selected, hover, and
focus styling should meet the rules in `TAB_ACCESSIBILITY.md`. Derive tab colors through
`tab_style_palette`; do not hand-pick a one-off color that only works in one theme.

Known themes are:

- Base: `Dark Mode`, `Fight Night`, `Classic Green`, `Light Office`.
- Promotion: `BAMMA`, `UFC`, `PFL`, `Cage Warriors`, `ONE Championship`, `RIZIN`, `KSW`, `LFA`,
  `Oktagon`, `BRAVE`, `ACA`.
- Combat sport: `Boxing`, `Kickboxing`, `Muay Thai`, `Wrestling`, `BJJ`.
- Sports media: `Sky Sports`, `ESPN`, `BBC Sport`.
- Special: `Matrix`, `Champion`.

When changing shared UI, verify representative dark, light, promotion, and special themes, not only
the currently selected theme.

`Dark Mode` is the default startup theme. Plain Tk list controls must use `self.colors["tree"]`
and `self.colors["text"]` at construction time and remain covered by `retheme_plain_widgets` so
theme changes never expose a light-gray native control.

The academy's `active_challenge` and `challenge_history` are persistent coaching decisions. New
challenge choices must resolve through world-layer methods, update the prospect's development and
finance/amateur ledgers, and be repaired with safe defaults for older saves. The academy screen
must expose the active decision without interrupting calendar advancement with an unconditional
modal prompt.

Academy prospects and graduates are identity-first. Challenges, amateur opponent ledgers, replay
telemetry, alumni updates, and graduate Profile actions use `prospect_id` or `fighter_id`; a name is
only a unique legacy fallback. Academy repair normalizes null or malformed collection fields before
iterating them. Automatic showcase status must derive from `last_showcase_week` and the four-week
card check rather than presenting the compatibility-only `showcase_weeks` value as a countdown.
Individual prospects retain a six-week bout cooldown. Weekly training must preserve a meaningful
fatigue trade-off between Light, Standard, Intensive, and Recovery workloads.

Academy schema 6 adds five connected systems. `development_plan` is one active 4/8/12-week block;
completion writes an immutable row to both the prospect's `development_reports` and the academy's
`season_history`. Amateur records retain competition tier and opponent rating, which drive quality
points, strength of schedule, tournament eligibility, titles, and graduation readiness. Youth
trait, satisfaction, loyalty, promise and retention history are persistent; a broken promise or
unsustainable workload may cause a real recorded departure. Graduation destinations are explicit:
main roster, MMA developmental, an open player combat-sport division, or a regional feeder with a
12-month `released_rights` row. Active rights are exercised from Academy Alumni through
`exercise_academy_matching_right()`, which revalidates the fighter, division, cash and feeder belt,
then records canonical signing finance. Do not implement these as UI-only labels.

Major non-child, non-feeder AI promotions store their youth programme under
`Promotion.strategy["youth_academy"]`, which is already covered by Promotion serialization. Rival
cohorts are compact academy prospect dictionaries until graduation, then become ordinary Fighters
on the owning promotion roster. `process_rival_academies()` runs once at week 1, and rival bids on
player-network leads must preserve the lead's `prospect_id`. Keep intake bounded and include rival
academy throughput in long-run population audits before increasing its cadence.

Tournament entry, academy graduation, and matching-right exercise are domain transactions. Stage
cash, canonical finance, the prospect/academy ledgers, affected rosters and belts, narrative queues,
and RNG before their first mutation; a late fight, story, finance, or roster hook must restore that
state and return a failed action. Schema-six scalar repair must normalize malformed values as well as
missing ones. Rival cohort development may raise a stored readiness rating but must never lower it
when recalculating the compact broad-skill average. Keep the rollback assertions in
`stability_test.py` whenever these flows change.

Fighting Academy and Combat Sports are main notebook pages, not Toplevels. Their ownership and
refresh rules:

- `build_academy_tab` and `build_combat_sports_tab` are the registered screen builders; both are
  lazy, like every other screen. The academy delegates to `render_academy_screen`, which owns the
  page content and can rebuild it in place.
- The academy workspace is assembled against a single container widget held in `_academy_window`.
  It is a frame inside `academy_tab`, never a window: do not reintroduce `geometry`, `minsize`, or
  `WM_DELETE_WINDOW` handling there.
- An unbuilt academy renders an inline empty state offering the build purchase. A tab cannot open a
  modal every time it is selected, so the purchase decision belongs on the page.
- `refresh_academy_tab` and `refresh_combat_sports_tab` are the only refresh entry points.
  `refresh_academy_tab` rebuilds when ownership changes so buying an academy elsewhere replaces the
  empty state without a restart.
- Neither page appears in the `refresh_all(full=True)` sweep. `refresh_current_screen` builds a
  screen on demand, so listing them would construct widgets for a player who has never opened them.
  They are refreshed after the sweep, guarded on `_academy_window` / `_combat_sports_redraw` being
  set, which keeps a hidden-but-built page current without creating one.
- `open_academy_window` and `open_combat_sports_window` remain as routers to `select_tab` so
  existing entry points (Finance, Scouting, World news) keep working. They must not open a window.
- Retained detail popups — prospect profiles, card replays, child-promotion management, circuit
  records and history — still create Toplevels, parented to `self.root` rather than the page.

Player-owned Combat Sports divisions are persistent child promotions, distinct from each sport's
AI flagship circuit. `roster_ids` and booked-bout `a_id`/`b_id` fields are authoritative; retained
names are presentation and unambiguous legacy fallback only. Championship maps use `title_ids`, and
lineage, season statistics, records, awards, and Hall of Fame entries retain fighter IDs. One-fight
independent opponents are transient and must not enter persistent circuit statistics or awards.
Load/world repair must be deterministic, deduplicate by fighter ID, and never merge same-name
athletes. Every recruitment source, including flagship buyouts, must set
a negotiated purse, term, exclusivity, employer, and canonical finance transaction. A contract at
zero months receives the displayed renewal window and leaves on the next monthly review if it is
not renewed; expired athletes are not bookable. Player card costs pay the stored purse for both
corners, use a card-specific transaction reference and event label, and may settle at most once per
division per month. Player event counters, completed-card history, and media must not increment or
rewrite the AI flagship's equivalents. Changes to this flow require
`combat_sports_regression_test.py` plus the smoke suite.

Boxing and Muay Thai must remain mechanically distinct, not just commentary skins. Boxing bout
length is level-aware (six/eight/ten rounds) with 12-round title fights; three judge cards own the
official verdict and knockdowns can create 10-8/10-7 rounds. Standard Muay Thai is three rounds and
title Muay Thai is five, with effective kicks, knees, elbows, dumps, balance, and clinch control
weighted above undifferentiated punch volume. Lethwei shares the Muay Thai circuit but keeps five
rounds and a knockout-first/no-winner draw outcome. Preserve `scorecards` and `round_metrics` in
result and replay payloads, and route every new decision/draw label through
`combat_sport_is_decision()` so it cannot count as a finish or receive a stoppage round suffix.

Future Combat Sports cards live in each player division's `scheduled_events`, never in the MMA
`self.scheduled_events` collection. Their payload keeps event ID, month/week, production, marketing,
forecast, and ID-first bouts. Scheduling validates future date, roster ownership, medical
availability, contract coverage, duplicate corners, and the one-card-per-month rule. Scheduled
athletes are unavailable to manual/automatic card generation. `calendar_week_steps()` executes due
cards after entering the new week; forecast and settlement call `combat_sport_event_forecast()` so
the displayed business decision cannot diverge from the charged result. Cancellation removes only
the selected event and does not mutate fighter recovery or contracts.

Upcoming MMA scheduled-card rows must use saved event IDs, or deterministic explicit legacy
fingerprints when an old row has no ID. `refresh_upcoming` keeps an identity-to-event map and
restores a still-visible selection after refresh/reorder. Due-event, edit, and cancel handlers
resolve through that map and fail closed when it is unavailable; they must never convert a visible
Treeview row position into an event index.

The scheduled-card editor must apply the same identity boundary to each bout row. Prefer saved
`fight_id`, `bout_id`, `booking_id` or `match_id`; use a deterministic explicit legacy fingerprint
when none exists, suffix duplicates, preserve the selected fight object through refresh/reorder and
resolve Remove, Move, title/tier/plan, TBA and last-minute replacement actions through the map.

The temporary Superfight Night card builder must likewise keep a source-bound row map. Use fighter
IDs/names plus crossover state for a deterministic legacy-safe key, suffix duplicates, preserve the
selected bout object through refresh/reorder, and fail closed rather than routing Remove or Move
from a visible row index.

World Chronicle's Listbox is a presentation reader: map the selected display key to the retained
chronicle entry before opening context or detail, suffix duplicate keys deterministically, and do not
route actions from `rows[selected_index]` after filtering or refresh.

Storylines page construction must not call `ensure_story_thread_index` or otherwise repair the
retained `story_threads` collection. Use a defensive read projection and treat a malformed or
unavailable collection as an explicit empty/unavailable state; explicit narrative mutations keep
the normal repair/index boundary.

Every `ttk.Treeview` is sortable by heading. Main tabs may call `make_tree_sortable` explicitly for
custom behavior, but secondary and popup tables rely on the shared Treeview class fallback in
`ui.py`; do not add a new column table with permanently static headings.

Fighter presentation is a boundary concern. `fighter_display_name()` and
`display_fighter_names_in_text()` must be idempotent: stored names may be raw or may already carry
`(C)`, `(IC)`, or `(D)` from an older presentation path, but a screen must render each marker once.
Keep event logs and identity matching raw; normalize only when populating labels, tables, news,
inbox detail, belt history, or Fight Night commentary.

AI roster reviews run during calendar advancement and must use
`scheduled_fighter_references(include_booked=True)` before considering a release or upgrade.
That helper returns durable fighter IDs with legacy-name fallback; keep both review passes safe for
scheduled fighters and cover the path in `ui_data_regression_test.py` so a packaged advance cannot
fail on an undefined schedule set.

## 13. Data Quality

- Avoid duplicate fighters across companies unless intentionally represented as a historical/younger
  or market snapshot. Keep each object on its own durable `fighter_id`; source markers such as
  `Legend`, `FA`, and `BAMMA` are internal seed metadata and must not be exposed as raw suffixes.
  The shared display formatter renders a compact `(D)` marker after duplicate names, including
  narrative and belt-history text. Use company, market, division, or profile context when the
  player needs to distinguish same-name snapshots. Audit the opening world for duplicate IDs and
  normalized base names before changing seeded records.
- Fighter database schema 5 requires a non-empty unique `fighter_id` on every canonical
  `all_fighters` row. New universes preserve that source ID; grouped compatibility tuples omit it.
  Renaming, editing, or moving a source record must preserve its ID, while an intentional duplicate
  must mint a fresh ID. Legacy schema-four packs receive deterministic IDs in memory without source
  rewrites until explicitly saved through the Database Editor.
- The shipped database keeps `birth_country` and `hometown` non-empty for every canonical MMA
  fighter and synchronizes those fields to compatibility tuples. Preserve authored values.
  Deterministic regional fallbacks must carry `birthplace_source: regional_fallback_v1` and must
  not be described as verified biography; verified bundled matches use
  `birthplace_source: bundled_verified_identity`.
- Rights packages presented as global or broad-reach coverage must include every current `REGIONS`
  entry. Add a shipped-database regression whenever the region model or media market list changes.
- Never create names with a `2` suffix as a collision workaround.
- Keep male and female fighters correctly gendered.
- When adding women whose names are absent from `FEMALE_FIRST_NAMES`, update `infer_gender`.
- Keep each company deep enough to fill its active divisions and champions.
- Use real fighters where requested; generated fighters are acceptable for roster depth.
- Generated data and tests should be deterministic under an explicit seed. Isolate test RNG setup
  from serialization and unrelated name generation.
- `Promotion.reputation` is a compact level label used in the World Hub, not a prose-description
  field. Keep long company copy in an explicit description/identity field so it cannot overflow the
  Level column.
- Region `teams` entries must represent teams based in that region. Prefer deriving the display
  from `Gym.region`, and validate authored overrides against the gym database.

## 14. Testing and Shipping

Use the configured bundled Python runtime when available. Otherwise use a local Python 3
installation with Tkinter. Commands in documentation must be repository-relative; replace `python`
with the full path to the configured interpreter when necessary.

### Fast syntax check

```powershell
$PythonSources = Get-ChildItem -LiteralPath . -Filter '*.py' -File | Select-Object -ExpandProperty FullName
python -m py_compile $PythonSources
```

### Shipping test suite

```powershell
.\Run Smoke Tests.bat
```

The batch file pauses for interactive use. Automated agents may run the equivalent commands
directly:

```powershell
python .\run_regression_suite.py
```

Validate the shipped universe database after data or editor changes:

```powershell
python .\database_editor.py --validate '.\Databases\Default Universe.universe.json'
python .\database_editor_ui_audit.py
```

Tkinter startup tests require a Python installation with working Tcl/Tk data. If a sandboxed
runtime cannot find `init.tcl`, distinguish an environment failure from a game failure and rerun
with the configured Windows runtime when permitted.

### Release metadata

`constants.py::GAME_VERSION` is the runtime version source. For a release, keep it synchronized with
the version shown in `README.md` and the newest section of `CHANGELOG.md`. Changelog entries should
describe player-visible behavior and important compatibility changes, not merely list edited files.

### Test selection

| Change | Minimum verification |
| --- | --- |
| Documentation only | Read rendered Markdown, check links/commands, run `git diff --check` |
| Models, seeding, saves, calendar, game AI | Syntax check + smoke + stability |
| Scouting reports, searches, staff identity, or recruitment UI | Syntax check + `scouting_regression_test.py` + smoke |
| Fight mechanics or commentary | Syntax check + `fight_engine_regression_test.py` + `fight_engine_full_system_test.py` + frozen 3,840-bout result and action audits + smoke |
| Fight Night viewer, replay, or event presentation | Syntax check + smoke + `fight_night_experience_regression_test.py` + stability |
| Media Desk or rights | Syntax check + smoke + media-system test |
| Event economics or rivalries | Syntax check + smoke + `event_economics_regression_test.py` + media-system test when media actions change |
| Shared UI/theme/layout | Syntax check + smoke + manual maximized-window check in representative themes |
| Fighter Profile, history, or Profile-launched actions | Syntax check + `fighter_profile_regression_test.py` + smoke |
| Universe data or database editor | Syntax check + universe `--validate` command + `database_editor_ui_audit.py`; build if packaging changed |
| Packaging, assets, paths, startup | Full shipping suite + portable build + launch packaged executable briefly |

Randomized tests should assert robust invariants or aggregate behavior. Do not hide a real
regression by widening a threshold without explaining why the sample design was wrong.

The Simulation Lab fight audit is a competitive calibration tool: generate named low/mid/high
bands, prefer overall gaps of six or less, report finish rates per band, and restore RNG/name state
after the run. Its lightweight gate/profit stress figures are labelled synthetic and must not be
presented as the player event-finance model.

Fight tuning and business tuning are separate persisted surfaces. `engine_settings` contains only
the versioned, bounded mechanics keys declared by `FIGHT_ENGINE_SETTING_DEFAULTS`; Gate Multiplier
lives in versioned `business_settings`. Load through the normalization helpers so malformed values
are clamped and legacy saves migrate `engine_settings.gate_multiplier` without changing behavior.
Simulation Lab must label mechanics controls separately from business-only controls. No Contest is
a participation/medical settlement: it completes contracted participation and recovery but must not
change W/L/D records, Elo, season awards, rivalries or titles. Technical decisions require the
completed-round threshold and the already-sealed cards. Referee review flags are observational and
must never rewrite an official result. Do not restore the removed `finish_chance()` or
`finish_method()` shortcut; all finishes resolve through the active exchange/stoppage mechanics.

### Portable builds

For the complete portable package:

```powershell
.\Build Portable.bat
```

To rebuild only the standalone universe editor:

```powershell
.\Build Database Editor.bat
```

Launcher/test/build batch files resolve Python from the repository `.venv` first, then the `py` or
`python` command available on `PATH`. Never commit a developer username or absolute interpreter
path; packaged builds still take precedence in the player launcher.

The game build must preserve these runtime folders and files in `dist\MMA Warriors`:

```text
Saves
Databases
Logs
README.md
Portable Check.bat
```

`Build Portable.bat` is the canonical release build and must produce both `MMA Warriors.exe` and
`MMA Warriors Database Editor.exe`; do not require a second editor build in release instructions.
Failure paths must restore any staged `Saves`, `Databases`, and `Logs`, and stale staging data must
not resurrect files deliberately removed from the package. `Portable Check.bat` must verify both
executables.

Never solve a build problem by deleting runtime saves. After a packaging or core-runtime change,
start the packaged `MMA Warriors.exe` briefly and run the portable check when available.

## 15. Common Change Recipes

### Add a persistent fighter or promotion field

```text
model default
  -> seed value
  -> serialize
  -> legacy load default/repair
  -> viewer or simulation consumer
  -> old-save + round-trip smoke assertions
```

### Add a new core promotion

```text
shipped universe company + fighter ownership data
  -> authored Python roster data and fallback promotion seed spec
  -> old-save repair
  -> executive/strategy/identity/broadcaster data
  -> champion and division viability
  -> universe validation + smoke expectations
  -> README/changelog
```

### Add a new fight result path

```text
simulate_fight result
  -> finish/result presentation
  -> apply_result
  -> injury/ranking/finance updates
  -> record_season_result
  -> event and promotion history
  -> save/load regression
```

### Change a shared UI header or tab

```text
build widget with flexible geometry
  -> refresh every field independently
  -> verify long values and spectator mode
  -> verify keyboard/mouse states across representative themes
  -> check maximized and narrower supported widths
```

## 16. Common Pitfalls

- Do not edit saves destructively.
- Do not remove `repair_core_promotions`; it keeps older saves viable.
- Do not put the active player company in `self.promotions` during a normal career.
- Do not make save paths current-working-directory relative.
- Do not assume `serialize_world` is currently side-effect free.
- Do not add pale hard-coded panels or theme-specific tab colors.
- Do not add a core promotion without updating repairs, data, smoke tests, and docs.
- Do not rely on `Cage Empire`; old references are backward-compatibility guards only.
- Do not add a new tab when an existing viewer or table can be extended cleanly.
- Do not use `fighter.status` as future-date availability.
- Do not flatten grouped save paths during load, move, backup, delete, snapshot, or quick save.
- Do not restore three-person custom divisions. Eight is the minimum normal target and six is the
  hard draft viability floor.
- Do not bypass `perform_weigh_in`, season tracking, or other shared mechanics for a new fight path.
- Do not trim global fight commentary in a way that can delete round structure or the official result.
- Treat `assets/crowd_audio/manifest.json` as the runtime source of cue intent for the integrated
  crowd pack. Keep audio optional, respect suggested gain, and use multiple reactions
  sparingly rather than allowing ambience to mask commentary. Preserve the source provenance and
  Gregor Quendel CC BY 4.0 credit in `assets/crowd_audio/LICENSES.md`. Rebuild mastered assets through
  `tools/build_crowd_audio_pack.py`; do not add generated noise beds or unlicensed recordings. Keep
  isolated gasp/"ooh" vocals below the sustained crowd bed so reactions accent rather than mask the
  fight commentary; the manifest's `mix_controls` records the accepted vocal-balance limits. Each of
  the 12 trigger families has three source-distinct variants. Preserve the accepted revised-pack cue
  as Variant 1 and name additions `_02`, `_03`, and so on so random playback can group files by
  `family` without breaking the stable base filename. The player must avoid immediate variant
  repeats, retain per-family cooldowns and a simultaneous-cue ceiling, and fall back procedurally if
  a manifest entry cannot be decoded. A manifest `loop` flag is required for the session-scoped
  ambience bed: `start_fight_night_audio_session()` opens one crossfaded loop across the live card,
  one-shot cues remain independently bounded, and `stop_fight_night_audio_session()` must run when
  the owning viewer closes so no sound bleeds into another screen or session. Keep the bed neutral;
  fighter-specific location gain belongs to the current bout's reactions and walkout. Audio variant
  choice and procedural fallbacks use the audio-only `SystemRandom`; never consume simulation RNG
  for sound presentation. Derive local crowd gain through
  `fighter_event_connection`: exact hometowns receive the largest bounded lift, followed by national
  home, adopted home, and training-base connections. Keep this effect presentation-only; it must not
  alter fight mechanics or create a second geographic-proximity model in `audio.py`. The live Fight
  Night viewer and Game Settings share `fight_night_audio_volume`; route both through
  `set_fight_night_audio_volume` so drag-time changes apply to the next cue, malformed legacy values
  repair safely, and saved volume remains clamped to 0-100.

## 17. Current Product Direction

Prefer focused, testable improvements in these areas:

- more readable fight-night pacing and presentation;
- better AI scheduling so promotions avoid overbooking tired fighters;
- finance tuning for gates and media rights by region and company reputation;
- deeper staff contracts, poaching, development, and specialist scouting;
- more gym/camp stories and long-term development tracking;
- feeder promotions as a prospect pathway, retaining budgeted AI offers instead of instant random
  signings;
- stronger company identity and personality in AI booking;
- robust Spectator Mode as a true observer save;
- one shared weight-cut model through `perform_weigh_in`; and
- more polished fighter profiles, charts, and fight histories.

Keep every change focused, testable, portable, and save-compatible.
- Game & Saves is a read-model over the save library: retain the selected slot by normalized path identity (not display name or mutable row index) across refreshes, folder filters and duplicate names. Empty/filter states must explain the safe next action; unavailable metadata is labelled without hiding the slot. Keep all existing load/copy/delete/backup/recovery confirmations and targets unchanged.
- Database/world rows on the same page follow the same path-bound identity rule, so a refresh cannot redirect Load DB or Use Selected Universe to a different file with a similar stem.
- Storyline readers must use saved `story_id`/`story_key` identities and restore the selected thread after filter/refresh changes. Legacy threads without an identity may use an explicitly labelled read-only fallback; never target a mutation from a mutable story row index.
- World Chronicle readers should retain the selected entry by `chronicle_id`/`entry_id`/`story_id` where present. Legacy read-only entries may use an explicitly non-durable fallback; filtering must not silently change the detail/context target.
- MMA roster rows must retain selection by fighter identity across filter/refresh rebuilds. If a selected fighter is filtered out or departed, clear the selection rather than binding detail actions to another row; row mapping remains presentation-only.
- MMA Contracts rows must retain selection by fighter identity across filter/refresh rebuilds, matching the Combat Sports contract table. If a selected fighter is filtered out or departed, clear the selection rather than binding actions to another row; renewal/release remain the existing handlers.
- The Contracts and Combat Sports `Show` filters share one predicate: monthly expiry filters exclude fight-counted comeback/final-retirement obligations, and Non-Exclusive uses the actual contract flag. Refreshing filters must not tick terms or change contracts.
- Rankings rows must use a mode/company/fighter identity key and restore the selected row after scope/filter refresh. Duplicate source identities get deterministic UI suffixes; company rows remain separate from fighter rows. The detail pane must read the selected row’s stored scope/ranks and scouting visibility.
- Matchmaking Available Fighters must retain the selected fighter by stable fighter identity across date/filter/refresh rebuilds. If the selected fighter is no longer visible or eligible, clear the selection; never bind Add/Compare actions to a replacement row.
- Free-agent Market refreshes must preserve the selected source fighter when scouting/status filters rebuild the table; if that fighter is no longer visible, leave the detail panel unselected rather than substituting another market row. Refresh remains a read-only projection.
- Scouting assignment rows must retain selection by saved `assignment_id` for new talent searches and report fighter identity. Legacy searches without IDs should fingerprint their authored request fields; only an empty/malformed row keeps an explicit non-durable compatibility fallback. Duplicate source IDs receive deterministic UI suffixes.
- Profile Fight History rows must retain selection by archived bout/history identity through filters and layout refreshes. Legacy rows can use a clearly non-durable fact fingerprint; duplicate source rows get deterministic suffixes, and opponent/card actions must read the selected stored row.
- Sponsor portfolio rows must retain selection by saved `agreement_id` for active deals and saved offer `id` for market offers; legacy dictionaries may use deterministic term fingerprints but never a mutable `active-<index>` key as durable identity. Duplicate legacy rows receive deterministic UI suffixes. Selecting an active deal is read-only: show its stored duty status/current activation preview and disable offer-only accept/counter/reject actions. Refreshing the market must not pitch, regenerate offers, spend cash or draw RNG.
- Media Desk browsing must use `media_actions_remaining_readonly`; opening or repainting the desk may not initialise/reset a stale weekly marker. Only an explicit campaign commit or the calendar's existing boundary owner may advance or consume media capacity.
- Debounced Fighter Search and Database Editor callbacks must be cancelled when navigation leaves their page and must fail closed if the Tk root is closing. Preserve the existing 200 ms search / 150 ms editor debounce and page selection; hidden pages must not redraw from stale timers.
- World Hub gym rows must retain selection by `gym_id`/`id` where available, or a deterministic legacy name/region identity with duplicate suffixes. Refreshing the read-only gym table must not resynchronize membership counts or redirect its detail cards after sorting.
- Legacy Ledger company-era rows must use the promotion identity helper with deterministic duplicate suffixes; never key the era reader by a company display name alone.
- Company standings selection must retain both company identity and sport scope; same-named MMA and combat-sport entities must not redirect the detail pane after sorting/filter refresh. Rows carry a stable promotion or sport-scoped circuit identity behind the visible name; duplicate same-name rows remain separately selectable, while name-only legacy restoration fails closed unless the visible match is unique.
- Company-card replay view/watch actions must resolve AI packages through the selected promotion identity when one is saved. New packages retain `promotion_id`; legacy name-only packages may be used only for a unique visible company, and duplicate same-name standings rows fail closed rather than opening the first archive.
- Finance milestone outlooks are projections: `company_milestone_projection` must defensively handle malformed finance/history rows with bounded values and must not seed, normalise or rewrite the saved envelope during refresh.
- Company Rankings must retain a stable promotion/circuit identity and source roster for every row; duplicate display names may not use a first-name lookup for power, selection or detail routing.
- Rankings scope selectors must disambiguate duplicate promotion names with a source-bound label/map. Company and P4P/divisional rank maps must key by the selected promotion identity, while preserving the readable display name.
- ID-less promotion identities in Rankings must include a deterministic retained-roster fingerprint; name/region alone is not sufficient when duplicate legacy promotions share both fields.
- Media Desk readers must use a non-mutating finance accessor and `media_plan_target_options(..., migrate=False)` during refresh; legacy defaults/IDs are repaired only by explicit plan save/commit actions.
- Rankings must label P4P and divisional scopes separately; movement may only use a previous snapshot from the same ranking scope, otherwise show an explicit unavailable state.
- Media Rights account review is a saved-evidence read model: delivery history, shortfalls, strikes, deadlines and successor status must not settle, repair or regenerate contracts during refresh.
- Staff Full Auto multi-action briefs must persist completed action IDs. A partial failure is resumable only for unattempted actions; requeue may not rerun, recharge or re-credit a successful action. Keep the brief visibly `Partially completed` with the recorded exception until all allow-listed actions finish, and preserve the existing retry/idempotency evidence.
- Staff brief action allow-lists must be identity-deduplicated at creation so one action cannot produce duplicate attempt keys or progress entries; preserve the first authored order.
- Staff brief UI must expose the ordered allow-list as a multi-select control; retain the legacy first-action projection for compatibility, and save only actions supported by the selected department.
- Media Rights lifecycle labels are authoritative: a cleanly delivered quota is `Fulfilled`, a term with event entitlements still owed is `Expired with shortfall`, and delivery-failure termination is `Terminated`. A queued successor may activate only after a `Fulfilled` predecessor at the next calendar boundary; a breached/shortfall predecessor marks it `Needs review` and never auto-activates it.
- Media settlement/audience evidence should carry stable `outlet_id` and `contract_id` when known. Account-review readers match those IDs first and use display names only for legacy rows without identity; refreshes remain read-only.
- Renewal availability opens at the declared two-month or two-entitlement boundary through the calendar owner, without refresh-time RNG or spend. Rejected/superseded renewal offers remain in offer history; the account reader must surface `Needs review` successors and their reason.
- Membership History must report an explicit threshold notice when retained facts exceed 10,000 while keeping the full append-only collection and complete paginated/as-of reads. The threshold is a review warning, never a truncation trigger.
- When recording a legacy/manual Media outcome, enrich a copy from the active contract with `outlet_id`/`contract_id` when available; never mutate the caller's outcome or infer identity from a mutable row position.
- Staff progression must persist each executed work item's explicit `progression_eligible` evidence. Quarter-close growth may count only rows explicitly marked true; paid rows marked false or missing the field remain unknown/non-qualifying, and retries must not create a second credit.
- Booking Workbench Draft Review rows must route through the saved booking/fight identity, never a visible row position. Foundation-migrated rows use their durable ID; legacy rows remain explicitly non-durable fallbacks, and duplicate source IDs receive deterministic suffixes. Reordering or refreshing the reader must not retarget a locked-slot proposal.
- Booking Workbench proposal alternatives must likewise use saved fighter identity UI keys (with explicit legacy fallbacks and duplicate suffixes); Fill and Save Medical Draft actions may not resolve the selected option from a mutable visible index after refresh.
- Locked-slot replacement alternatives must use the same saved fighter identity map; Commit Selected Replacement may not convert the visible selection directly into an option index after refresh.
- Company Proposal Ledger rows must preserve proposal-ID selection through status refreshes, use deterministic suffixes for duplicate source IDs, and label missing legacy IDs as non-durable; detail routing may not use names or visible positions.
- Profile Company & Title History rows must resolve detail through a recorded membership/title fact identity or an explicitly non-durable legacy fingerprint; as-of refreshes must preserve a still-visible selection and may not index into the visible list.
- Career Journeys rows and actions must route through fighter identity keys, with explicit legacy fallbacks and duplicate suffixes; profile/plan actions may not resolve the selected fighter from a mutable visible index.
- Finance weekly-history rows must use saved month/week identity keys or explicit legacy fallbacks, preserve selection through refreshes, and route detail through the saved row map rather than a visible index.
- Matchmaking draft-card rows must use saved booking/fight identity keys, with explicit non-durable legacy fallbacks and deterministic duplicate suffixes. Refreshes must restore a still-visible selected bout; Remove, Compare, Fill TBA, title-toggle and move-up/down actions must resolve through the identity map and never convert a visible row position into a `booked` index.
- Inbox rows must use a saved message/source identity where available or an explicit deterministic legacy fingerprint; refresh/filter/sort must restore a still-visible message and visible-mail actions must route through the saved row map. Owner Objective navigation and retired-fighter comeback actions follow the same identity rule. Staff member/candidate handlers fail closed when their stable row map is unavailable and may not guess from a mutable visible index.
- Media Desk/story readers must use saved story, chronicle, entry or event identity where present, with explicit deterministic legacy fingerprints for old headlines. Refresh must restore a still-visible story, and selected-story/context/Previous/Next actions must resolve through the saved row map rather than a mutable headline position; compatibility aliases for stale legacy IDs are read-only and non-durable.
- Assistant decision-queue notices and Staff profile readers must resolve selected records through their source-bound row maps; stale numeric/visible-position selections fail closed rather than opening a different notice or employee after refresh.
- Staff evidence validation must happen before sealing an executed work row. A handler must return a non-empty evidence key and payload; recommendation modes cannot report spend, and malformed responses become `Needs attention` without a work receipt. Domain evidence may name its underlying action rather than the staff wrapper action.
- Academy showcase-history and alumni readers must use saved event/fighter/prospect identity keys or explicit deterministic legacy fingerprints. Refreshes must preserve selection, and replay/profile/matching-right actions may not resolve a record from a mutable visible index.
- Player Combat Sports running-order bout, scheduled-card and completed-card rows must use saved identity keys or explicit deterministic legacy fingerprints. Remove/Move and replay/cancellation actions must resolve through their row maps and may not convert a visible position into a list index after refresh.
- Fighter Comparison measure rows must use stable measure IDs and a source-bound row map. Detail-panel selection may not resolve through a mutable visible row index after filtering or refresh; duplicate labels receive deterministic suffixes and every displayed comparison value remains available.
- Company History interval projections should retain the membership/event IDs that formed their boundaries and pass those IDs through Profile readers. As-of refreshes must preserve the authoritative fact when present; legacy rows without IDs remain explicit non-durable fallbacks.
- Media Rights desk terminal-contract summaries are read-only projections of saved rows; preserve and show `Fulfilled`, `Expired with shortfall`, and `Terminated` history after the active package ends without rebuilding state or inferring from list positions.
- Drug Testing case readers must remain frozen-evidence projections: show recorded sample/spend totals and the collection/screening/confirmation/appeal/final timeline without rerunning tests or reclassifying injuries. Staff's Testing Cases route must use the same case read model; confirmation, appeals, sanctions and provider-specific outcomes remain gated until their approved policy tables exist.
- Manual compatibility testing must quote its existing sample cost before `random.sample` or any test roll. Empty rosters and insufficient cash fail closed with a visible deferral and no charge, case ID, RNG draw or partial evidence.
- J9 regional host invitations are deterministic planning offers: issue at most one per quarter only when the regional feasibility read model proves two bookable local roster fighters and a reliable fixed staging/venue quote. Persist the offer, four-week acceptance expiry, 8–16-week event window, capped 10% guarantee and one entitlement key. Accept/decline/expire/cancel are explicit and zero-penalty; bind only to an ordinary event with the exact saved region, venue and date. Pay once at settlement only when two local roster fighters complete bouts, otherwise record an unfulfilled zero. Opening the Region Hub must never generate an offer, charge cash, consume RNG or create a booking.
