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

