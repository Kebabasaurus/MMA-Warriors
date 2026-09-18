# MMA Warriors

This detailed guide retains the feature descriptions from the former root README.
Use the [quick start](../README.md) for launch/build entry points and the
[documentation index](README.md) for focused development context. Paths in prose
and command examples are relative to the repository root. Dated trial results
remain recorded evidence, not verification of later source changes.

Start with the [documentation index](README.md) for current plans, developer
guidance and the archive of older reviews, proposals and handoff notes.

The Finance cash-runway reader is defensive against malformed legacy values:
production, medical, drug testing, sponsorship, media rights, rates, academy
costs and venue/tier inputs use bounded planning fallbacks without rewriting
finance, schedules, cash or RNG state. Saved runway snapshots remain
non-binding and are marked stale when their source inputs change.

Finance revenue-mix history also uses a defensive projection: malformed
archive, weekly-history or transaction rows are treated as unavailable while
valid event and non-event income remains separated, without altering retained
history.

AI roster-upgrade rollbacks also retain truthful Company Timeline evidence: if
the incoming deal fails after a temporary release, the incumbent's stable
return fact is recorded before the roster is restored.

The owned-company calendar is likewise defensive: malformed saved dates are
bounded for display and marked as partial coverage without changing schedules,
reservations, finance or RNG state.

Cash-runway cards now show a break-even attendance threshold when gate and
merchandise can cover committed costs within the venue capacity. Conditional
rights and sponsor receipts remain visibly separate from that threshold.

Staff readers also fail closed on malformed or non-finite legacy skill, morale,
salary, reputation and contract-term values. They preserve the raw row and
keep uncertain terms expired for access checks; only explicit contract actions
may mutate staff records.

Lead and specialty cost projections apply the same rule: non-finite skill,
morale or subtotal values are treated as unavailable, never allowed to distort
lead selection or produce a misleading saving.

The Staff capability and evidence audit surfaces invalid non-finite salary,
contract, morale and work fields with stable employee identities while leaving
the saved policy and employment records unchanged.

Media Rights contract and outcome readers likewise treat non-finite or malformed
terms as bounded zero/Needs review evidence, preserving legacy fee aliases and
contracts without settlement or additional random draws.

Sponsor previews apply the same safeguards to trust, stability, fee, fit, term
and conduct fields while showing contracted maximums separately from the active
full/half-fee estimate.

Testing Desk provider comparisons also bound malformed or non-finite cost and
sample inputs; quotes stay planning-only and cannot charge, reroll or change
the live screening policy.

Game & Saves includes an explicit **Migrate Profiles** action for legacy career
arc labels. It scans a selected slot without changing it, shows the exact
profile paths that need conversion, creates a recovery backup before writing,
and records a versioned migration note in the save metadata. Ordinary load and
healthy saves remain untouched.

MMA child promotions also support future-dated cards. The manager commits an
identity-bound card plan to the shared calendar without reserving fighters or
spending cash; matchmaking, readiness, settlement, media, and replay resolve on
the chosen week. A due card cannot be skipped by the normal AI show roll, and a
failed readiness or budget check remains visible as **Needs replacement** for
the player to cancel or rebook.

The Academy rival-program table is observational: missing rival youth-program
data is projected on a copy while calendar progression and explicit academy
actions retain the mutation boundary.
Rival-program rows use promotion identity keys with duplicate suffixes, so two
companies sharing a display name remain separately readable.

Detailed-skill profile readers use a deterministic, non-mutating projection.
Empty legacy profiles remain readable from their saved broad ratings, while
load/editor/simulation owners keep the RNG-backed repair boundary.
The legacy roster detail and upgraded profile cards show the live
trait-adjusted injury tendency alongside the retained base risk, so evolution
cannot leave the player looking at a stale number.

Combat Sports overview and records pages are observational readers: legacy
circuit repairs are projected on copies while explicit management and
simulation paths remain the only owners of weight, title and ranking updates.
Records/History ranking rows keep the saved title/fighter identity behind the
displayed names; a name-only fallback is used only for a unique athlete in the
selected circuit, so duplicate careers fail closed when opening a profile.
The same reader keeps malformed title, finance and event history visible as
explicit unavailable evidence with bounded dates/amounts, without rewriting the
retained records.
Company standings and selected company profiles use that same read-only circuit
projection when they display non-MMA entities.
Rankings refreshes likewise calculate the visible table without rewriting stored
fighter rank snapshots; simulation/calendar boundaries remain the mutation owner.
Child-promotion management and company-profile readers project saved strategy
data without seeding missing strategy fields; explicit gameplay owners retain
strategy creation and updates.

Rankings respect Scouting Mode for derived score fields: private fighters show `Hidden` instead of an exact score, while public rank, movement, records and scouting-safe estimates remain visible.
Company Rankings rows also carry stable promotion identities, keeping duplicate
same-named promotions' rosters and power calculations attached to the correct
source row.
Ranking scope choices disambiguate duplicate promotion names with their region
and source identity, while company and P4P/divisional rank maps use that same
identity behind the display label.
Legacy promotions without IDs use a deterministic roster-bound fingerprint so
two same-name/same-region records do not merge into one ranking group.

Regional Prospects refreshes are read-only: the table uses stored history baselines and a bounded assessment projection without writing fighter fields. Calendar/simulation and explicit migration owners retain the normal baseline repair boundary.
Its throughput summary also uses a non-repairing backlog projection; opening or filtering the table cannot write the monthly eligibility cache or repair malformed rules.
Regional Prospect rows are bound to both promotion and fighter identity, so
sorting/filtering cannot redirect a selected prospect to another regional
company; selection is restored only when the same source remains visible.
The Staff autonomy selector reads the saved company/department policy without
repairing it during repaint; only an explicit policy edit normalizes malformed
legacy values.
Selecting a Regional Prospect, Scouting Target Board row, or comparison card is
also read-only; uncertainty/details use the retained dossier with
`migrate=False`, so a page interaction cannot repair the scouting collection.

Matchmaking draft refreshes are observational: card metadata is projected onto display copies, saved fight order and identity mappings remain unchanged, and available-fighter repainting does not repair the event-name field. Explicit booking actions still own card mutations.

Media weekly-capacity reads are observational too. The dashboard uses the
non-repairing finance accessor, so a stale or malformed saved media envelope is
shown with bounded defaults without creating keys or rolling the week marker.

Game & Saves is a read-only library view: refreshing it cannot create the active-universe marker or repair autosave rules. It preserves path-bound save/database selection and leaves load, backup, copy, delete, and database-selection actions as explicit operations.

Routine selection and progress feedback stays in the owning page status strip or Inbox when that
surface is available. A source-level dialog inventory guards the remaining native information
fallbacks (including the headless-only Fight Day three-way choice), while validation errors,
destructive confirmations and final approvals remain explicit. This keeps context after refreshes
without changing save, finance, RNG or identity boundaries.

Spectator stop policies also capture the game revision that armed them. Automatic fast-forward and
Resume fail closed when an explicit saved revision no longer matches the running build, while
legacy policies without that field remain compatible. The player can clear or replace a stale
policy, and ordinary career loading remains independent of the guard.
The same check is enforced at the shared advance scheduler, so a direct or future caller cannot
bypass the protection; rejection happens before due-card inspection, job creation or Tk callbacks.
Rule-default/load processing preserves the saved revision as well, so reopening or loading a career
cannot silently downgrade a stale policy into a legacy-compatible one. Policies predating the field
remain readable with an empty legacy marker.
The simulation desk labels stale policies directly and projects malformed targets as unavailable,
keeping the reader safe while leaving repair to the explicit Clear or Apply Policy actions.

The Finance page is a read-only projection: refreshing it cannot repair the saved finance envelope, write derived payroll/offer values, or seal annual history. Malformed legacy finance data remains visible through bounded values and explicit unavailable states; calendar and explicit finance actions remain the write boundary. Strategic-investment ownership and upkeep use the same non-repairing projection, so opening Finance, runway or the dashboard cannot seed a missing `strategic_investments` mapping.

Upcoming Cards is a presentation projection: generated names and display ordering are calculated on a copy, while edit/cancel actions retain the source event identity. Refreshing the page cannot rewrite saved card data, and its economics/broadcaster strips read malformed finance defaults without repair or a crash.

Regions profiles use a defensive display projection. Malformed or incomplete regional rows show an explicit unavailable/neutral state, and refreshing the Regions page never rewrites the retained catalogue.

Cash-runway projections fail closed on malformed legacy finance containers: they use a bounded office-cost fallback, preserve the raw save, and show unavailable rights without spending or rerolling anything.

Company profile follow state is a read-only subscription projection. Opening or repainting a company does not normalize malformed story subscriptions; explicit Follow/Unfollow actions remain the write boundary.

Results landing pages keep malformed retained rows visible as explicit unavailable entries, while valid result IDs and detail routing remain source-bound and read-only.

World Fighter Search is a read-only history reader: universe-record labels use the defensive profile baseline projection and do not write imported-record metadata during search or pagination. Rows use source-bound fighter/company IDs (or deterministic legacy fingerprints), so page/filter refreshes cannot route a profile or comparison action to a different fighter.

Scouting readers fail closed on malformed evidence: invalid confidence/date fields remain unchanged, estimates do not infer a new report date, and current/full/discovery predicates return safe review outcomes.

Scouting Target Board and Scouting Centre refreshes are read-only projections. They preserve retained report/search evidence, tolerate malformed rows, and use `migrate=False` for display estimates; explicit scouting assignments remain the mutation boundary. Talent-search rows use saved assignment IDs or deterministic request fingerprints, so completion and resort cannot redirect a selected search.

Scouting Decision Packs are read-only until an explicit create/edit action: refreshes preserve saved evidence and identities, show malformed rows for review, and never commission reports or rewrite the scouting shelf.

Profile follow-state and Followed Story Briefings are defensive readers: malformed subscription or story rows remain safe and unchanged during refresh, while explicit follow/acknowledge/snooze/unfollow actions own mutations.

World Hub refreshes are read-only projections: company rows retain stable promotion identities (including deterministic legacy fallbacks), duplicate rows are disambiguated, and missing legacy show-history data is displayed without mutating the save.
Legacy Ledger company-era rows use the same promotion identity keys and
duplicate suffixes, so identical display names remain separate historical
companies.

Inbox refreshes are now read-only projections: legacy dates/read flags are
derived on copies, malformed rows stay visibly unavailable, and source-bound
actions still target the original saved message.

Drug Testing Cases is a frozen-evidence reader. Malformed saved envelopes are
labelled `Unavailable`/`Needs review` during refresh, with no repair, retest,
injury or sanction side effect; the timeline and table colours follow the active
semantic palette.

Staff policy summaries and the Staff management panel are defensive readers:
malformed legacy policy envelopes remain visible for audit without being
rewritten during refresh, while explicit policy and brief actions retain the
normal migration/write boundary.
Saved Staff brief IDs remain the action key across refreshes; duplicate or
legacy rows are visibly disambiguated and cannot redirect Commit, Requeue or
Cancel to another brief.
Staff roster, candidate and expiry rows likewise use saved `staff_id` values or
deterministic fingerprints of legacy fields. Only an empty malformed row uses
an explicit non-durable fallback, so sorting cannot redirect a staff action.

Dashboard decision rows use the active semantic palette, keeping urgent and
normal advice readable when the player switches between light and dark themes.

Media Rights offers are now identity-safe in the market reader. Saved offer IDs
or deterministic legacy term fingerprints retain selection across refreshes;
duplicate and malformed rows stay visible for review, while actions resolve only
through the saved row map. An id-less legacy offer is readable but not actionable,
so a refresh cannot accept or counter the wrong market row.
The Media Desk's spokesperson and target selectors likewise keep source-bound
fighter maps with readable duplicate suffixes, so campaigns and callouts cannot
silently target a same-name athlete after a refresh.

Booking Workbench commits are identity-safe across refreshes. Fill Selected Slot
and locked-slot replacement resolve the saved candidate fighter ID, fail closed
on missing/duplicate IDs, and preserve the existing exactly-once receipt owner;
malformed alternatives remain visible as unavailable review evidence. The legacy
option-index API is retained only for compatibility callers and tests.
The player roster reader also preserves the selected fighter by identity when
filters or status sorting rebuild the table, clearing the detail only when that
career is no longer visible.
The Free Agents market keeps the same selection contract: scouting, status and
closed-division filters restore the selected source fighter when still visible
and otherwise leave the scouting panel unselected.

The Promoter Dashboard also treats retained results, change-journal entries and
scouting queues as read-only evidence. Valid rows are copied into bounded
projections; malformed containers or rows stay visible as unavailable/review
evidence instead of crashing a repaint or being silently reassigned. Spectator
newest-result/newest-story ordering and content-bound notice selection remain
stable, and dashboard refreshes never repair or regenerate source data.

Storylines and World Chronicle use bounded, read-only projections. Malformed
legacy rows stay visible as `Needs review` or `Unavailable` with their stable
identity and retained context; opening or refreshing a reader never repairs,
regenerates, or marks story evidence as read. Context links prefer saved
fighter IDs and refuse ambiguous name-only company links.

Scouting supports named recruitment watchlists in addition to the compatibility
Main Watchlist. Create, rename, switch or archive a list from the Target Board;
membership and scouting evidence remain ID-linked and retained, while archived
lists stop driving active alerts. These actions do not commission reports,
reveal hidden ratings or sign fighters.

Fight Night opens on a control-centre landing page: watch a card that is due,
browse identity-safe recorded events, or jump to the complete office/event log.
Retained cards clearly distinguish replay-ready detail from results-only index
history. Browsing and replaying remain read-only and do not reapply results,
rerun preparation, or regenerate archived commentary; the full original log is
still available with semantic visual accents.

Finance and Media readers are resilient to older or partially malformed save
data. Finance history/outlook and reconciliation show explicit Unknown or
Unavailable evidence without repairing retained rows, while Media Rights
offers, contracts, campaigns and settlement receipts keep stable identities
and remain readable without generating offers, spending cash or consuming RNG.
Campaign history now retains source-bound row identities and a selected-campaign
detail strip; Awards/Records leaderboards likewise route profile opens through
fighter identity maps rather than duplicate-prone display names or sorted row
positions.
Achievements & Milestones uses the same historical identity discipline: new
fighter achievements retain `fighter_id`, dedupe by that identity, and resolve
profile opens through a unique legacy-aware resolver so duplicate names cannot
redirect the permanent record.
Other name-only legacy profile links (ranking detail, rivalry summaries and
generic tree rows) use the same unique-name compatibility projection; duplicate
or missing careers are left unavailable instead of being selected by list order.
The 12-week runway also keeps malformed forecast rows visible as planning
evidence and never reserves cash or moves a scheduled card while refreshing.
Saved scenario review uses the same defensive projection and keeps malformed
snapshots explicitly unavailable without applying their proposed edits.
Sponsor settlement also reports malformed duty evidence as at-risk instead of
crashing or inventing a qualifying payment.
Settlement receipt tables keep malformed amounts and sponsor rows visible for
review while preserving saved receipt/event identity and the full payload.
Owner Objectives use the same read-only projection: malformed rows are shown
as review evidence and opening the page cannot record a new outcome.
Media state initialisation preserves malformed contract/offer containers under
legacy-raw evidence before creating safe working lists, so migration remains
auditable.
Media settlement also fails closed on malformed package metrics, rights fees,
sponsor amounts and contract relationship/strike evidence; valid transitions
continue normally while the saved audience row records any review requirement.
Malformed monthly expiry or successor-entitlement terms are held for review,
so calendar processing cannot invent a deadline or overlap an invalid renewal.
Active-contract lookup is also non-mutating for readers, keeping a missing
legacy finance envelope untouched until an explicit load/action boundary.
Malformed custom rights-package fields now fall back to bounded values during
initialisation so a bad universe entry cannot prevent the Media system loading.
Rights history also shows `Needs review` for malformed lifecycle evidence
instead of falsely presenting an incomplete package as fulfilled.

AI media-deal review skips malformed saved offer terms while retaining those
offers for explicit review; valid offers continue through the normal strategy
selection path. Monthly media-market refresh likewise preserves malformed
outlet fields, marks them for review and keeps diagnostic averages bounded.

Media offer expiry and signing are also fail-closed for malformed legacy
rows: unknown expiry evidence remains available for review, and only offers
with stable identity and valid positive terms can create a contract or spend
cash.

Monthly sponsor and legacy rights expiry also holds malformed terms for review
without overwriting the saved values; valid agreements continue to expire once
through the normal calendar boundary.

Regional-host invitations also fail closed on malformed dates, guarantee terms
or settlement results. Invalid offers stay reviewable without binding an event
or paying a guarantee; valid exact-date, one-entitlement behaviour remains.

Counteroffers use the same boundary: malformed sponsor or rights terms remain
available for review and cannot be negotiated or charged, while valid counters
retain the existing one-roll negotiation and fee/guarantee rules.

Company hub detail tabs keep malformed legacy history, finance and Staff rows
visible as explicit unavailable/Unknown evidence. Opening the reader does not
repair or reinterpret roster, contract, finance or promotion state.

Sponsor cards distinguish the contracted maximum per eligible event from the
current activation-adjusted estimate and label whether the full or half fee
would apply. Legacy sponsor previews fail closed on malformed trust, terms or
campaign evidence without changing finance state or consuming RNG.

Foundation Staff work receipts expose bounded amounts together with explicit
Recorded/Unknown states and data-quality diagnostics. Malformed legacy quote,
spend or calendar values remain available for audit; budget and detail readers
skip unsafe numbers and show Unknown without repairing the save, spending cash
or consuming RNG.

The Staff Evidence Audit is a read-only diagnostic over work receipts,
progression and current employment evidence. It reports missing or duplicate
Staff IDs (including employed-versus-market collisions), missing roles and
malformed salary/contract terms with source labels and stable IDs. Opening or
refreshing it never repairs the save, reassigns staff, charges payroll or
consumes RNG.

Staff contract readers are defensive over malformed legacy terms. An invalid
contract-month value is shown as unavailable/expired for the read model while
the original value remains untouched for the explicit employment audit and
repair boundary.

Staff roster, candidate, expiry and specialty tables likewise keep malformed
legacy rows visible as unavailable evidence. Numeric display failures do not
rewrite the saved employee, and selecting a malformed row fails closed rather
than opening a different employee.

Staff contract targets, offer scores and expiry notices use bounded defensive
projections for malformed salary, reputation, heat and term values. Legacy
non-dictionary rows are skipped by warning readers, and no read or diagnostic
refresh rewrites the retained employment evidence.

The calendar contract tick also holds malformed terms for explicit review and
skips non-dictionary rows while retaining them in the roster; payroll totals
use valid numeric salaries only.

Finance cash-runway and roster-cost snapshots use the same defensive payroll
projection, keeping planning pages readable when older staff salary evidence is
malformed without rewriting that evidence.

AI monthly operating costs follow the same rule: invalid salary rows stay in
the promotion for audit and are excluded from payroll rather than treated as a
free hire or a crash.

Legacy Staff profile loading also tolerates malformed role and skill fields,
keeping the original values for review while using bounded fallbacks only for
derived display metadata.

Shared Staff skill and scouting-capacity/workload helpers apply the same
fail-closed projection, so malformed roster rows cannot break scouting pages or
route work to another employee.

Finance refresh and month-end office/payroll work use the same projection, so
invalid Staff rows cannot break recurring-cost settlement or the Finance tab.

The cash-runway planning view is defensive over legacy finance data. Malformed
or non-dictionary weekly transaction rows remain untouched and are excluded
from the paid-to-date total with an explicit unknowns notice, rather than being
coerced into a calendar boundary or silently repaired during refresh.

Super-event closeout is similarly fail-closed for malformed legacy terms or
settlement evidence: valid projects keep their existing idempotent settlement,
while invalid packages produce a review record without applying business
effects or inventing money.

Booking Workbench proposal readers and commits also fail closed on malformed
saved alternatives. The raw proposal remains available for review, and only a
validated identity-bound option can reach the existing explicit booking commit.

AI staff affordability previews likewise remain readable when an older employee
row contains an invalid salary; the diagnostic does not repair the row or
change hiring/expiry behavior.

Company History retention diagnostics distinguish valid and malformed retained
membership rows. The raw append-only archive is preserved, while the profile
header makes incomplete readable coverage explicit.

AI staff expiry preserves malformed legacy employees and holds their contract
for review instead of treating unknown terms as an expiry. Notices are
calendar-month deduplicated, and valid expiry/market behavior remains unchanged.

Staff progression quarter-close also keeps malformed work evidence in the
ledger but excludes it from qualification, preventing crashes or fabricated
skill gains while preserving the existing evidence audit.

Owned Calendar is a read-only index with explicit partial coverage: malformed
legacy schedule rows are counted in diagnostics and left untouched, while valid
events retain their source-bound identity and owner context.

Cash-runway scenario revisions likewise tolerate malformed legacy event dates,
recording a diagnostic count while preserving the schedule and keeping the
planning snapshot read-only.

Membership retention diagnostics now treat blank legacy IDs as incomplete
coverage rather than falsely reporting them as duplicate identities. Repeated
non-empty membership IDs remain visible as a genuine collision for review.
Company History also shows how many retained rows are ID-unknown, so incomplete
legacy coverage is visible without rewriting those facts.
Malformed retained month values are classified as date-unknown rather than
being presented as valid chronology.
Per-fighter membership totals use the complete retained pages, so long careers
are not under-counted in the Profile header.
Interval projections use the same strict date validation as the summary and do
not coerce malformed boolean, float or week values into chronology.

Lineal title-history migration preserves malformed legacy rows for review while
rebuilding only trustworthy title results; a bad historical row cannot crash
save loading or be silently discarded.

Title reconciliation now preserves lineage when a saved champion has left the
roster: it records an explicit name-only vacancy for manual review rather than
silently dropping the fact. Duplicate-name primary holders are left untouched
unless exactly one fighter is explicitly marked champion, preventing a repair
from assigning a belt or flags to the wrong identity.

Profile Company & Title History now paginates long retained histories in
250-row pages while keeping selection tied to recorded identities. Copy and
JSON export still use the complete unpaged payload, so the presentation layer
does not hide or delete older membership or title facts.

Company History now distinguishes an unavailable/malformed retained membership
archive from a genuinely empty one. The diagnostic summary and history header
preserve the raw envelope and direct repair to load/migration, so refreshing a
profile cannot silently normalize or fabricate membership facts.

Booking workbench review and medical-draft readers now inspect saved data
without normalizing malformed envelopes. Empty or unavailable legacy evidence
stays visible for diagnosis; only explicit save, generate and commit actions
write the workbench.

Booking Draft Review is now a read-only reader. It does not migrate or add
booking IDs during refresh; legacy rows remain visibly non-durable until the
normal Foundation migration boundary assigns their stable identity.

Interim-title cleanup is now identity-safe with duplicate fighter names: the
marked holder is cleared and recorded by stable ID, while an ambiguous legacy
name-only map remains unchanged for manual review.

Staff retention views now show the evidence behind a review—credited work and
periods, saved monthly pay and role assignment—while clearly keeping any
departure decision manual. Missing or malformed legacy values are labelled or
bounded without changing morale or employment state.

Company History now flags impossible or malformed retained membership dates as
incomplete evidence while preserving both source facts. Same-week joins,
leaves and returns remain distinct, and as-of reads never reorder or repair the
append-only ledger.

The AI Staff ledger now includes read-only six-month runway evidence for each
non-feeder promotion: current cash, monthly recurring operating/payroll basis,
no-revenue runway months and the reserve required before a proposed hire. The
market worker reuses this same pure affordability projection, so failed offers
remain available and no refresh performs a hire, spend, repair or RNG draw.

Staff progression and retention views now project saved evidence without
repairing malformed legacy state during refresh; progression changes remain
owned by the explicit quarter-close worker.

Combat-sport ownership changes now feed the same append-only membership
timeline as MMA contracts: crossover, release, private-market signing,
flagship buyout and academy-child graduation record their stable identity facts
at the roster mutation boundary, while generated circuit replenishment records
its join fact.

The in-game World Editor also keeps fighter selection attached to stable
owner-aware identities across sorting/filtering and records destination-company
membership when an employer is changed.

The standalone Database Editor includes a read-only **Preflight** check. It
separates structural schema/reference errors from playable-risk warnings such
as thin divisions, missing matching free-agent depth and explicitly authored
payroll above company cash. Findings include evidence and a suggested remedy;
the check works on a copy and never repairs or saves the live database.

The standalone Database Editor now keeps fighter and company selection bound to
the saved source record across sorting/filtering. Stable IDs are preferred,
legacy rows are labelled through deterministic fallback keys, and mutations
fail safely if the selected record has disappeared.

Legacy AI staff who predate durable `staff_id` values are retained in the
shared market when their contracts expire and are labelled as legacy records;
stable-ID employees continue to deduplicate safely. This prevents an expiry
tick from silently deleting historical staff data.

Super-event completion now confirms the terminal closeout before applying
derived popularity, stability, safety and news effects; stale completion
copies fail closed with Needs review and leave the live company unchanged.

Region Hub gym actions are identity-safe across the local list, and populated
Events tabs no longer display a misleading blank placeholder row.

Regions selection is now identity-safe across refreshes: the profile, Region
Hub and Feasibility actions stay attached to the saved region instead of a
mutable list position, with an explicit legacy fallback for older widgets.
The profile also includes a **NEXT STEP** card that explains the current local
pairing, show, or gym constraint and links directly to the relevant read-only
review. It rechecks the selected region before opening a hub or feasibility
window, so refreshing the list cannot redirect the action.

Super-event lifecycle records now protect their terminal state: stale
closeout attempts are harmless, successful projects retain their public
`Success` outcome while storing canonical `Completed` state, and unaccepted
or terminal projects cannot be scheduled from a stale editor. Lifecycle
transitions are explicit, and a revision mismatch pauses with `Needs review`
instead of clearing the live project.

The Testing Desk's Standard, Strict, Olympic and Off choices are validated and
revisioned through one saved policy boundary. Provider comparisons and quotes
remain planning-only until the full J5 confirmation, appeal and sanction rules
are approved.

Company Milestones & Super Events opportunity rows are identity-bound to saved
offer IDs, with deterministic legacy fingerprints and duplicate suffixes.
Refreshes preserve selection and cannot route an action to a different offer
because its visible row moved.

Invitation expiries are recorded through the same terminal closeout path:
unaccepted offers retain a zero-commitment history record, while stale planning
projects stay visible for review rather than disappearing from the active list.

Official Record Book details are bound to their scope and record key, so sorting
or refreshing cannot make a selected historical mark open a different record.

Achievements & Milestones detail and profile actions likewise follow stable
achievement identities through filtering and refreshes.

World Hub news details and story navigation use chronicle identities, so a
refresh cannot make the selected story jump to another headline.

Regional host invitations are an optional, persisted planning lane. A
quarterly deterministic offer appears only when the selected region has two
bookable local roster fighters and a reliable fixed staging quote. Accepting
an offer does not charge a deposit; it links the proposed venue/date to an
ordinary Matchmaking card, and the capped host guarantee is paid once only
when two local roster fighters complete bouts. Declined, expired, cancelled
and under-filled invitations retain their evidence and pay nothing.

Upcoming scheduled cards are identity-bound: saved event IDs are preferred,
legacy rows receive deterministic non-durable fingerprints, and duplicate
source IDs are suffixed predictably. Refreshing the list restores a still
visible selection, and due-event, edit, and cancel actions fail closed rather
than acting on whichever event moved into a visible row position.
The scheduled-card editor binds each bout row to its saved fight/bout/booking
identity as well, so card edits and replacement controls cannot follow a
changed visible position after refresh or reorder.
The Superfight Night builder also keeps its temporary card rows identity-bound
through refreshes and reorder operations.
World Chronicle detail and context actions likewise follow the selected
chronicle identity through filtering and duplicate rows.
Storylines is read-only at page open, so malformed legacy thread data is shown
as unavailable for review instead of being silently normalised.

Booking Workbench Draft Review binds selection to each saved booking reference,
with deterministic duplicate suffixes and an explicit legacy fallback for old
rows. Reordering the draft list cannot route a locked-slot proposal to a
different bout; only a stable complete pairing can enter the existing explicit
proposal/commit flow.
Proposal alternatives use the saved fighter identity as their UI key as well,
keeping Fill Selected Slot and Save Medical Draft attached to the chosen
opponent after a refresh.
The locked-slot replacement reader follows the same rule for its commit action,
with legacy options explicitly marked as non-durable.
Company Proposal Ledger refreshes likewise preserve proposal-ID selection,
surface missing legacy identity, and safely display duplicate source records.
The Profile Company & Title History reader uses the recorded fact identity (or
an explicit legacy fingerprint), so as-of filtering cannot redirect detail text
to another interval or title event.
Career Journeys uses the same identity-safe routing for profile and plan
actions, including duplicate-name and legacy-fighter handling.
Finance weekly history now keeps selection and detail tied to the saved
month/week row identity, with a visible legacy fallback for incomplete rows.
The Matchmaking draft-card table now uses saved booking identities (with
explicit non-durable legacy fallbacks and deterministic duplicate suffixes),
so refresh, reorder, Remove, Compare, Fill TBA, title toggles and move controls
continue to operate on the selected bout rather than a mutable row number.
Inbox messages, Owner Objectives and retired-fighter comeback rows now retain
source-bound selection through refreshes. Bulk-read, goal navigation and
comeback actions fail closed without their identity map; Staff member/candidate
actions do the same rather than guessing from a visible row position.
Media Desk headlines are identity-bound to their saved story/chronicle/event
records, with legacy fingerprints and selection restoration across refreshes;
reader navigation and context actions cannot follow a shifted headline index.
Assistant decision notices and Staff profiles similarly fail closed when a
source-bound map is missing, so stale numeric selections cannot retarget a
different notice or employee.
Academy card history and alumni rows now use event/fighter/prospect identity
keys with legacy fallbacks, keeping replay, profile and matching-right actions
attached to the selected record after a refresh.
Player Combat Sports running-order, scheduled-card and completed-card tables
now use identity-bound rows; Remove and Move remain attached to the selected
bout across refreshes and reorder operations.
Fighter Comparison measures are likewise keyed by stable measure IDs. The
detail panel resolves the selected metric through its row map, preserving the
correct values after filtering or refresh instead of relying on a visible row
position.
Company History interval projections retain the membership/event IDs behind
their boundaries and pass them to the Profile reader. Selection can therefore
follow the recorded fact through an as-of refresh, while old rows without IDs
remain clearly legacy and read-only.

The Drug Testing Cases ledger is also read-only at the page boundary. Case
rows, summaries, and workflow details read the retained evidence without
repairing the save; malformed or unavailable legacy case collections render an
empty ledger and remain for the normal load/migration repair path.
The Company Proposal Ledger uses the same non-mutating reader contract for its
append-only review records.
Followed Story Briefings also project subscriptions without repairing them on
page open or refresh; only explicit follow, acknowledge, snooze, or unfollow
actions write the normalised subscription state.
Malformed numeric fields in retained Foundation work receipts are rendered as
explicit zeroes in the read-only diagnostic card, never rewritten in the save.
Testing Cases rows remain bound to saved case IDs, with deterministic legacy
and duplicate handling and selection restoration across refreshes.
Talent Relations case registers likewise read malformed legacy obligations
without rewriting them; only explicit case actions use the repair/write path.

The Simulation Lab play-level audit can now resume safely from its latest
yearly checkpoint. Source/configuration identity and RNG/world state are
validated before restore; incompatible evidence is rejected and the active
career save is never touched. Each yearly boundary also records explicit
duplicate-identity, settlement, orphan-reference and negative-obligation
findings, stopping safely for review instead of silently repairing the
disposable observer world.
The same surface now includes a dedicated **Run 100-Year Audit** action. Its
yearly evidence covers generation/intake, retirements, promotion viability,
free-agent supply, championship holders, regional feeders, combat-sport cards,
cash and retained history size. A pure balance qualification pass stops only
the isolated audit for roster/promotion extinction, multi-year title
starvation, runaway cash or unbounded history; low free-agent or feeder supply
is surfaced as a warning. Findings retain severity, stable codes and source
paths so balancing changes are based on demonstrated evidence rather than
automatic tuning.

When a scheduled card becomes due, Fight Day now opens a managed decision
surface with separate **Watch Live**, **Simulate Now**, and **Stay on This Week**
actions. Opening it is read-only; the saved event identity is checked again
before preparation or settlement, preventing a stale panel from resolving a
different card. Routine advancement notices remain in the Inbox, while
destructive releases and final approvals retain explicit confirmations.
Spectator fast-forward precondition and empty-result messages now appear in the
persistent simulation desk, so a missing target or an empty 24-week search does
not interrupt the player with a native dialog.

Routine Scouting and Academy feedback now stays on the active workflow when
those pages are built: assignment blockers, balance/capacity limits, showcase
availability, promotion readiness, and network status appear in their status
or report areas. Academy scout lead reports use a managed reader window. Cash
spend, releases, early professional debuts, and other irreversible choices
still require an explicit confirmation.

Academy alumni history is presented in a managed table retaining graduate,
pathway, amateur/pro record, current rating, and title-win facts, including an
explicit unavailable row when a legacy entry is malformed.

Contracts uses the same presentation boundary: empty selections, batch-review
blockers, combat-sport renewal outcomes, and auto-negotiation summaries appear
in the page alert strip when available. The actual renewal, release, and cash
commit paths remain explicit and identity-bound.

Roster and Division Management now keep routine outcomes on the Roster page as
well. Missing or empty division selections, already-open divisions, close/reopen
results, and closed-division release summaries appear in a themed notice strip
with the affected fighter/division and the payroll or future-bout consequence;
destructive close and release confirmations remain explicit.

The Free Agents market keeps negotiation and signing feedback beside its controls,
including stale selections, invalid purse/cash blockers, and successful contract
joins. Terms and final commits remain in the explicit negotiation surface.

The Media Desk keeps routine campaign and rights outcomes visible beside the action
that produced them. Strategy changes, campaign/brief validation, retarget and cancel
results, offer blockers, counters, market reviews, renewals and contract lifecycle
feedback persist in dedicated status lines after a refresh. Paid reviews, deal
replacement, ending a contract and other irreversible choices retain explicit
confirmation; the underlying media and finance ownership remains unchanged.

Transfer preflight blockers, Combat Sports release outcomes, company archive gaps,
career-plan validation and Staff action guidance now return to their owning page or
managed reader when available. Staff profiles are scrollable managed readers with
the complete role, specialty, progression, tenure-story and scouting evidence package;
the reader does not mutate the saved staff record.

The Matchmaker's Desk and booked-card editor keep routine validation on their own
surfaces too: past dates, duplicate or unavailable fighters, division/rules
blockers, TBA/tournament review states, comparisons, and replacement outcomes
include a recovery instruction without stacking dialogs. Bout staging and final
event scheduling remain their existing explicit, identity-bound actions.

World Chronicle includes explicit **Export JSON** and **Export Report** actions.
They save the current filtered, read-only history projection—including legacy or
unavailable evidence labels—without changing the Chronicle or game state.

The Combat Sports overview keeps missing-selection, startup-funding, failed-open,
and history-navigation guidance in its own status line; launching a child division
still uses the explicit cost confirmation.

Fighter Search keeps missing-selection feedback beside its page controls, while
the 100-row identity-bound directory and Scouting Mode visibility rules remain
unchanged.

Promoter Dashboard decision details now separate the recorded notice from its
priority, consequence, and destination. The brief explains why a booking,
contract, runway, scouting, medical, or career issue matters and keeps the
existing source-bound context action; selecting a notice never resolves or
mutates it.

The Staff capability grid now reports the registered handler and evidence gate
for every department action, including whether that handler is available in the
current save. Full Auto and recommendation workers reject malformed, missing, or
paid recommendation evidence as `Needs attention` before they record work;
read-only capability inspection remains save- and RNG-neutral.

The Staff page also reports a pure long-run evidence audit. It counts executed,
recommendation and progression-qualified work, then flags missing or duplicate
work/receipt identities, unsupported actions, paid recommendations, incomplete
briefs, malformed recommendation payloads and progression references to work no
longer retained in the ledger. The audit is diagnostic only: it never normalises
the save, reruns a handler or awards progression.
View Evidence Audit opens a scrollable detail reader for those findings, keeping
the complete saved work/brief/action/boundary identifiers visible without
turning diagnosis into an automatic repair.
The Retention Watch table follows the same identity rule and keeps the selected
staff member attached through refresh or roster reordering.

Staff roster, candidate and expiry tables now route selection through durable
`staff_id` row keys (with an explicit legacy fallback when an old record has no
ID). Sorting or refreshing the page therefore keeps profile, hire, negotiate and
release actions attached to the selected employee instead of a mutable row
position; duplicate IDs receive deterministic display suffixes.
The refresh path also restores a still-visible selection by that same key after
sorting or list reordering.

The Staff desk includes a compact **NEXT STEP** card that turns those tables
into a decision surface. It prioritises contracts expiring within three months,
retained evidence or policy exceptions, uncovered specialist roles, and queued
department briefs, then links to the relevant expiry, roster, scouting, brief,
or audit reader. The card revalidates saved staff IDs (or deterministic legacy
fingerprints) before opening and is strictly observational: it cannot hire,
fire, negotiate, commit a brief, spend cash, or grant delegated authority.

Scouting's Target Board also surfaces a **NEXT STEP** card. It prioritises
visible recommended signings, stale reports, active assignments, and saved
decision packs, linking to the corresponding target, assignment, or pack reader.
Visible target, assignment, and pack identities are rechecked before selection;
the card never commissions reports, changes a shortlist, negotiates, or signs.

The World Hub now offers the same context bridge for its selected promotion,
story, or gym. It recommends a story reader, company context, Chronicle, gym
profile, or Scouting page and rechecks the selected source identity before
opening; the card is read-only and cannot alter world, roster, finance, or gym
state.

The Staff page's AI Staff Ledger is a read-only employment reader for non-feeder
promotions and the shared market. It keeps salary, contract term/expiry,
monthly roster payroll, morale and identity quality together in one scrollable
view. Stable promotion/staff IDs drive row identity; duplicate IDs get
deterministic suffixes and old name-only rows are labelled as legacy fallbacks.
Opening the ledger does not refresh offers, tick contracts, run affordability or
change the save.

Child-promotion manager actions now resolve the selected child by stable
`promotion_id`; duplicate child names are treated as ambiguous and fail closed,
while unique legacy names remain compatible. This keeps loan, recall and parent
transfer proposals attached to the intended child company.

Company Timeline membership pages now read the raw retained history envelope
without repairing it on refresh. A malformed or unavailable historical section
returns an empty/explicitly incomplete view, leaving the save untouched for
diagnosis.

The feature plan reports its work at two levels: six delivery gates (G0–G5)
and 63 non-deferred named implementation cards. G5 is closed for the approved
first-playable scope, including the bounded Testing Desk/title-decision,
Academy Coach, proposal/history, tournament-history, regional-invitation,
pause/checkpoint, editor-conversion, L0 audit and multi-event Grand Prix/child-
scheduling slices. Active confirmation, appeal and sanction tables, concurrent
rights/audience-segment economics and century-scale qualification remain
explicit follow-on decisions; they are not silently counted as implemented.
The 14 D-cards remain deferred or excluded.

Finance's 12-week runway now separates the maximum sponsor package attached to
each booked card from an activation-adjusted estimate based on the saved trust,
stability, campaign, and delivery facts. Both are labelled conditional and the
cash closes remain conservative/base/strong ticket-and-merchandise scenarios.
The Finance page also supports explicitly named, non-binding runway snapshots
with a dedicated review reader. Each stores attendance assumptions, proposed
edits, the complete forecast and a source revision; later changes mark it stale
while preserving the original evidence. Saving or reviewing a snapshot never
reserves cash or moves a card.
The runway exposes bounded low/base/high attendance controls (0–200%); the
headings, forecast and saved snapshot use the same selected values.

Super-event approvals retain their accepted terms and payment reference. The
project and Results history now show paid/sunk, refundable, and unpaid amounts
with an idempotent terminal settlement key; legacy terms are marked for manual
refund review rather than receiving an invented refund.

Results now includes a durable Tournament History reader for one-night and
multi-event brackets. It indexes saved seeds and fighter IDs, substitutions,
stage matchups, champion/status and source references independently of replay
retention. Search and promotion filters are read-only; opening an edition can
inspect its source card when retained, while legacy cards without a saved
bracket are never reconstructed from current rosters.

Matchmaking's Tournament Field Review presents the selected draft's seeded
entrants, readiness and ready same-division alternates with company/world rank
snapshots. It is planning evidence only; weigh-in remains the owner of any
actual alternate entry.

Fight History's Choose Columns workbench is now a save-backed layout editor:
players can show or hide any retained field, move visible columns up or down,
and set a selected column width from 70–360px. The full history payload stays
intact, hidden-field widths are remembered, and Career/Rankings/Ratings/Event
Detail/All Columns presets remain available.
Dragging a ledger header also saves that column's width.

Staff Full Auto briefs record each completed action and resume only the
unattempted actions after a partial failure. Requeued work cannot rerun or
re-credit an already successful action, and the brief stays visibly partial
until its remaining actions finish. The brief table shows completed versus
selected actions alongside the retained work count. The brief editor supports
an ordered multi-select action allow-list for supported departments.

Media Rights now label cleanly fulfilled deals separately from terms that expire
with events still owed. Delivery-failure termination blocks a queued successor
for review, and settlement evidence keeps outlet/contract IDs to disambiguate
partners that share a display name.

Renewal offers open automatically at the two-month/two-entitlement boundary
without a refresh-time draw or spend, and rejected renewal evidence remains in
offer history.

Company History warns when the 10,000-fact review threshold is exceeded while
retaining every append-only membership fact for complete paginated/as-of reads.

Legacy/manual Media settlement outcomes inherit the active contract identity at
recording time, keeping receipts auditable even when older callers omit IDs.

Staff progression stores explicit per-work eligibility; paid work marked
non-progression is ignored at quarter close, and legacy rows without evidence
are not inferred as skill credit.

Media Rights also retains a read-only terminal-contract summary on the desk,
keeping fulfilled, shortfall-expired and terminated deals visible after the
active package ends.

Round Read and Bout Desk also scroll directly under the mouse, including Linux
wheel events, while native text/table controls and the main action timeline
keep their own scrolling behaviour.

Status colours are theme-aware across Fight History, Scouting and Sponsors;
switching between dark and light themes rethemes the semantic row accents while
keeping the same records and selected rows.
Screens opened lazily after a theme change receive the same pass on entry.
Assistant and Event Log alert text follows the same semantic palette.
Unread, owned/available, readiness, scouting-strength, ranking-movement and
injury states are covered too. Rows with authored dark backgrounds retain a
contrast-safe foreground after a live theme switch.
Secondary Staff, booking, contract and history states (ready, preserved,
partial, review, open, booked and closed) follow the same semantic registry.

Sponsor offer cards distinguish the contracted maximum per eligible event from
the current activation-adjusted estimate and term. They show the readiness
reason and full/half-fee basis without refreshing offers, spending cash or
drawing RNG.

Sponsor portfolio rows follow saved agreement/offer identity through refreshes
and reorderings, including deterministic fallbacks for legacy contracts.
Selecting an active partner opens a read-only duty and activation card and
disables accept/negotiate/reject actions until a live offer is selected.

Media Desk capacity is read-only while browsing: opening or refreshing the
page cannot reset a stale weekly action marker. Campaign commits remain the
only path that advances and consumes the shared media capacity.

Fighter Search and Database Editor debounce timers are cancelled on navigation,
so a hidden page cannot repaint after its 200 ms/150 ms callback expires.

The combined release-safety UI/media/profile/staff/persistence/scouting group
passes 215 tests after the current improvements; no EXE or user save was
rebuilt in this pass.

World Hub gym selection is identity-bound (gym ID, or a deterministic legacy
name/region fallback), so sorting or refreshing the table cannot move the
detail cards to another gym. The read-only refresh still leaves membership
counts untouched.

Company standings selection retains a stable promotion/circuit identity together
with the company and sport scope, preventing duplicate same-name rows from
swapping detail context after a filter or sort refresh. Name-only legacy links
fail closed unless the visible match is unique.
Archived company-card replays carry the promotion identity as well. Selecting a
same-named AI promotion therefore opens only its own replay; older archives
without that evidence remain unavailable when the standings name is ambiguous.
Finance milestone outlooks also project malformed weekly history defensively;
opening Finance shows a bounded unavailable trend without rewriting the saved
finance envelope.

At laptop widths the stacked Matchmaking layout keeps the fighter explorer at
least four readable rows while the draft-card pane stays compact and
independently scrollable.

Combat Sports contract rows are keyed by stable sport/fighter identity rather
than visible position, so filters and refreshes preserve the selected athlete;
duplicate source rows stay visible with deterministic suffixes.

Delayed Matchmaking layout callbacks are cancellable and destroy-safe, so
closing or rebuilding the page cannot leave stale Tk timers or Tcl errors.

Media settlement receipts are keyed by their saved receipt/event identity, so
refreshing the page keeps the same historical record selected even when a new
event is inserted. Legacy rows without either ID stay readable with an explicit
identity limitation and their complete payload is preserved.

The Results archive follows the same rule: saved `record_id`/`key` values drive
row identity, so filters and new cards cannot make the selected result jump to
another event. Legacy rows without an archive identity remain visible with a
UI-only fallback.

Staff autonomy controls now show the effective mode for the selected department
override (or the company default), and keep that scope through refreshes. This
makes Manual, Recommendations, Selective Recommendations and Full Auto choices
auditable before the player applies them.

Staff work receipts follow saved operation/work identities when the table is
rebuilt, keeping the selected evidence attached to the same action. Legacy
cards without an identity use a UI-only fallback and are not treated as durable
history.

Dashboard decision notices use content-bound identities, so routine refreshes
keep the selected advice instead of always jumping to the first row. If the
underlying advice changes, the updated notice is deliberately treated as new.

The Testing Desk now provides a provider/policy comparison step: three authored
service tiers show coverage, turnaround and deterministic total quotes, with
the more effective options priced higher for the same sample count. The chosen
provider and sample count are saved as planning configuration; the existing
compatibility screening path remains authoritative until confirmation, appeals
and sanction mechanics are enabled. A Drug Testing Officer can produce a
read-only case review with the same frozen evidence and quote, never a hidden
sample, charge, RNG roll or sanction.
Drug Testing Cases provides identity-safe search and status filters, then shows
provider/tier, policy, screening result, workflow state and the next available
read-only action before the complete stored payload. The provider comparison
highlights the active row and explains supported panels, confirmation posture
and false-positive handling.

Fight Night now uses a profile-style broadcast dashboard: larger 136px fighter
portraits (104px in compact windows), a dedicated action timeline, and Card,
Round Read and Bout Desk panels. Playback settings expand only when needed.
Replay has styled read-only transcripts, scrollbars, complete bout labels and
independent bout/round selection. Detailed commentary and archived results remain
intact; the viewer does not change simulation or reveal sealed results early.

Owner objectives are sealed by the completed calendar boundary, not by opening
Inbox. Each new objective has a stable ID, explicit achieve/maintain/improve
semantics and additive observations/resolution evidence; legacy rows are marked
when their historical boundary evidence is unavailable. The goal panel shows a
pure current projection, while the worker records deadline outcomes once and
explains them in Inbox/news. Rankings also distinguish all rows matching the
current scope from the capped rows currently displayed.

Title-miss replacement decisions fail closed when the selected fighter is no
longer valid or misses again: the bout is held for review with the replacement,
miss and one-time fine evidence preserved, rather than silently becoming a
catchweight contest.
For title bouts, the last-minute replacement dropdown applies the existing
challenger-merit rule before showing candidates and repeats it at commit; a
ready but unqualified fighter is not presented as title-eligible, and a missing
merit owner fails closed. The decision dialog labels qualifying rows and the
count summary as title-eligible challenger options, while champion-corner
replacement is described separately as an explicit non-challenger path.

Legacy Fight Night archives without the additive preparation timeline keep a
selectable Preparation entry that says the evidence is unavailable. The reader
does not infer press, weigh-in or readiness outcomes from the card summary.

World Hub refreshes do not recalculate gym membership. Gym load is synchronized
at calendar boundaries and explicit gym mutation/view paths, so ordinary
navigation remains observational.
The title-miss replacement selector labels the saved corner as well as the
fighter name and resolves merit by stable fighter ID, so duplicate names cannot
show the wrong eligibility explanation.

The Promoter Dashboard's Owned Calendar now combines the player's MMA, child
promotion and combat-sport schedules into stable read-only rows. Each row can
open a detail reader with source, owner, status, participants, reservations and
legacy identity coverage without rerunning or mutating the event. Company,
source and status filters preserve the selected event by a source-bound stable
identity (including owner and source, so duplicate event IDs cannot steal the
selection) and show how many rows are visible versus indexed.

Staff autonomy work is evaluated after the calendar boundary has settled its
cards, finance and month-end business tasks. Boundary evidence keeps the month
and week that actually completed, even when the visible calendar has rolled
forward.
The isolated long-run audit also checks Staff identity and obligation integrity:
missing or duplicate employee IDs, market/employed collisions, missing roles,
and invalid or negative salary/contract terms are retained as explicit findings
for review rather than repaired or silently reassigned.
Spectator simulation does not execute or prepare Staff briefs; saved work waits
for the player-controlled mode when they return.
Marketing briefs also enforce their own saved spend ceiling before Full Auto
calls Media, so an over-cap quote is surfaced for review without spending cash.
Recommendations and Selective Recommendations now have distinct scope:
Recommendations reviews every safe read-only action registered for the
department, while Selective Recommendations reviews only actions explicitly
chosen on the brief. Mutating actions (such as campaign commit) stay excluded
from both modes and are available only through an explicitly committed Full
Auto brief.
The Staff capability grid lists each department's safe review actions, so the
scope shown in the UI matches the saved brief and calendar worker. The grid
also fits every registered department instead of clipping the lower rows.

Fighter traits now share a 46-entry catalogue and category-coloured profile cards.
Expand Trait Effects for advantages, drawbacks, triggers and bounded strength.
Compatible camps build persistent progress across distinct months, followed by a
12-month evolution cooldown; random unrelated trait replacement is removed.
Weight Bully gains up to three points on size-dependent close-control actions.
Injury tendency and strike defence read the current trait. Legacy saved ratings
are preserved, with injury risk anchored on load rather than guessed backwards.
Gym Leader and Late Bloomer are explicitly Personality only (no live modifier).
This is source-only work, not a rebuilt or newly certified release.

Title Lineage now records a vacancy before every champion departure path,
including distressed ownership releases, expired AI retirement contracts, ordinary
AI contract exits, and World Editor employer changes or retirements. Existing fight
losses still close a reign as a dethroning rather than an invented vacancy.

Sponsor pitching is now an active monthly market: choose a brief, compare fit,
term and 12-month value, then sign or risk one counteroffer for 12% more per event.
Active partners show whether their activation duty is ready; missed trust, stability
or ranked-fighter campaign requirements cut that partner's event payment in half.
Media-rights offers now show total package value and delivery risk. Players can
counter once for a higher guarantee, wider reach, lower standards or a shorter
commitment, with rejection withdrawing the offer and cooling the outlet relationship.

Staff specialties now include three approved bounded live effects: Campaign
Coordinator saves 2% on eligible paid media actions, Contract Administrator
adds a 2% saving to the existing negotiation-administration basis (never fighter
pay), and Production Coordinator saves 2% on eligible production staging. The
effective department lead owns the effect; all other specialties remain clearly
descriptive. Quotes and settlement expose the same saving, and the Staff page
shows the approved effect beside the specialty evidence.
Broadcast Producer recommendations also expose resolved production quality,
contracted minimum, readiness, venue/region, bout count and settlement status;
the review remains read-only and does not spend or edit a card.

Regional Prospects uses each row's promotion when applying Scouting Mode to
overall and potential ratings, including spectator saves.

Combat Sports now opens with a selected-sport management strip for roster depth,
the next committed child-promotion card, contracts nearing expiry and the latest
recorded result. Refreshing or switching rows preserves the selected sport and
keeps the complete native rankings, card-building and history views available.
The strip is read-only and does not recalculate ratings, schedule cards or alter
sport ownership.

World Hub now surfaces selected company and gym context cards (identity,
promotion snapshot, gym tier/effective quality and capacity/morale) above the
retained tables. Refreshing keeps selected rows where possible; news, full
profiles and native management actions remain available below.

Scouting Target Board search waits 200 ms after typing before refreshing,
cancels superseded callbacks and disposes pending work when leaving the page or
closing the app. Explicit filter changes remain immediate, with identity-based
selection and pagination preserved.

Camp Plan is a resizable decision window with a draft status, workload
trade-offs and live medical-limit readout. Cancel closes without changing the
fighter; Set Camp Focus remains the existing explicit commit.

Title weight-miss decisions now retain a plain-data snapshot on the affected
bout: both corners, miss amounts, title roles, eligibility context, available
choices and the chosen sanction. Replacement handling preserves the original
champion identity before changing the slot. The snapshot is also carried into
the fight-log row and event preparation timeline so the archive can explain the
decision after settlement. Saved pending decisions resume from their recorded
miss evidence without a second weigh-in roll, and terminal choices are
idempotent after reload. The decision window previews the consequence of each
approved action before commitment and keeps unresolved vacant-belt policy
explicit. Results Database preparation details repeat the recorded decision,
title-on-line state and replacement reason without rerunning the bout.

Fighter History shows a selected-bout matchup with prominent company/world ranking
badges captured before the fight. The compact ledger retains selectable columns;
complete details can be expanded. Development includes an overall progression plot
(recorded changes, not evenly spaced dates), signed monthly-driver bars and optional
factor explanations. Historical saves are not rewritten by these display changes.
AI title challengers require two wins and a non-losing record, or three consecutive
wins to establish a comeback from a losing record. Shallow divisions wait for merit;
the same requirement applies to vacant belts. Three prior meetings require a
12-month break even when the scorecards were close.
Overview presents momentum, morale, readiness and activity as a career-pulse strip,
followed by a full visual skill assessment ordered from strength to development focus.
Scouted profiles use the same layout with only information the player has uncovered.

AI supporting bouts prioritize ready fighters idle for six months or longer within
credible rating/rank limits, and overdue divisions move up the queue. Available
champions idle six months seek eligible title defenses. Recorded draws, splits and
narrow scorecards support rematches after three months; repeated non-close sweeps
wait 18 months, and fourth meetings require a 12-month break. Rivalry heat cannot
bypass these checks. Unknown legacy scorecards are not assumed close.

AI card construction indexes ready fighters by division and reuses sorted pools,
overall ratings and rebuild checks within each card. Pairing rules and RNG order
remain unchanged; every new card builds fresh caches.

Fighter Search waits 200 ms after typing and displays 100 matches per page.
Routine refreshes update the visible Academy or Combat Sports page once; hidden
pages refresh on entry. Compressed saves use accelerated JSON encoding and bounded byte buffers, and
load staging shares a deepcopy memo to avoid duplicating shared objects.
Signature assignment calculates overall once per fighter; authored signature
migration builds its fallback lookup once per load.
The latest 200 calendar task durations are available in `_advance_task_timings`
for diagnostics. Run `py -3.13 app_performance_regression_test.py` for focused checks.

Portrait catalogue v3 (source; not a rebuilt package) adds 50 hairstyles per gender:
98 men's and 77 women's generated choices. Women have no beards, stubble or moustaches;
men have 66 facial-hair options including none. Shared features gain 50 bounded
presets each; skin and natural hair now have 62 shades each with country-family
weights preserved. Existing complete saved portraits retain their appearance.
Fine facial differences remain subtle at thumbnail size. See
[portrait expansion counts, review and compatibility](FIGHTER_PORTRAIT_EXPANSION.md).

Named portrait corrections give Markell Holmes dark skin, an afro and a chinstrap,
make Brett Akey bald, and author Conor McGregor's UFC July 2021 photo look.
These display overrides also apply to existing saves without rewriting their vectors.
See [the named portrait review](FIGHTER_PORTRAIT_NAMED_CORRECTIONS.md).

The next ranked portrait pass authors 49 entries at database positions 51–100
from reviewed UFC/PFL/ONE photos; Matthew Green now has user-directed pale skin,
short dirty-blond hair, blue eyes and no facial hair, completing the 50-entry cohort. Three
authored-only hair shapes improve mullets and loose waves without changing
generated choices. See [sources and likeness limits](FIGHTER_PORTRAIT_TOP_100_REVIEW.md).

Positions 101–200 now also have authored comic portraits and a labelled review gallery.
See [the ranked 101–200 portrait review](FIGHTER_PORTRAIT_TOP_200_REVIEW.md).

Positions 201–300 now have photo-directed, display-only comic portrait vectors and a
labelled four-size review gallery. No source photos are shipped and existing saved
identities are not rewritten. See [the ranked 201–300 portrait review](FIGHTER_PORTRAIT_TOP_300_REVIEW.md).

## Version 3.0.10

Normal play now uses the native 440-move engine: specialist positions, standing
combinations, proven submission transitions and cradle setups, 40 additional
role-appropriate survival moves, the retained 2% standing-head impact adjustment
and 1% kick-power adjustment. Saves retain the new signature/mastery IDs; the
database editor, universe validation, fighter development and Fight Night recognize
the same release catalogue. Existing careers do not require a reset.

The historical 346-move audit profile remains separate for immutable reference
checks. The application imports `fight_release.py`; it does not activate audit
contexts or patch global registries during play. There are no added simulation
passes or random draws. New fighters may receive newly available signatures.

Release verification uses 300 bouts for ordinary content/chain/concentration gates
and 25,000 for the maximum-eight unobserved-ID requirement, as approved by the user.
The full 3,840-bout balance corpus and rolling-300 repetition limit are unchanged.
`analysis/verify_release_integration.py --calibration-corpus --output analysis/NEW.json`
compares native and candidate complete bouts/RNG; `analysis/evaluate_release_runtime.py`
collects fresh native coverage with `--fights 300` or `--fights 25000` and an exclusive
`--output` path. The portable build runs the isolated shipping suites and packages
both game and editor. See `docs/FIGHT_RELEASE_CHECKPOINT.md` for verified build status.
Native certification preserves all original reports and records the narrowly reviewed
identity/retirement-test migrations separately; runtime and simulation-helper hashes
must still match exactly. Existing portable saves and the selected-universe marker
are preserved when installing this build.

Survival calls consistently name the acting fighter and move. Jab-caused KO/TKO
finish narration reuses the causal exchange's displayed jab label, so the attack
and official finish description agree. The 256-bout commentary gate checks these
alongside actor, defense, outcome and Broadcast-retention evidence.

Historical selection verification now explicitly reconstructs the original default
portrait-field schema and frozen jab/survival/defense wording for the two recognized
references. The shipping runner supplies `--historical-portrait-fixtures` and
`--historical-wording`; checksums and every fixture, trace and move fingerprint remain
strict. New captures retain all current fighter fields and current commentary.

Defended exchanges now draw from 16 deterministic defense-clause variants per
identity, reducing repeated calls while retaining the recorded defender and defense.
`fight_defense_wording_test.py` checks factual wording and complete-bout/RNG parity.
The paired whole-bout CPU check in `analysis/benchmark_defense_wording.py` measures
2.063s before versus 2.047s after across three alternating 44-bout samples, with
identical non-commentary facts and RNG. This shows no measured slowdown in that
small sample, not a guaranteed speed improvement or whole-career timing result.

Joint candidate coverage now returns a failing exit status when any arm reports a
content, chain or measured-target failure. The JSON retains each arm's findings and
adds a named top-level `failures` list. An empty list on an extended frequency run
does not replace the standard coverage, calibration or shipping checks.

`analysis/survival_unused_diagnostics.py --output analysis/NEW_UNUSED_STAGES.json`
records the current 440-move candidate's actual eligible pools, offers and resolved
holds, with complete paired-bout/RNG checks and source hashes. Its standard sample
has 27 absent IDs: 19 have no observed final-pool opportunity and eight were offered
but not selected. This diagnoses the coverage gap without forcing rare techniques.

Single-jab commentary now varies among eight equivalent labels, including lead-hand jab,
straight jab and single lead jab. The canonical `single_jab` identity and outcome remain
unchanged; wording is derived deterministically from the recorded exchange without RNG.
`py -3 -m unittest fight_jab_wording_test` verifies replay stability and complete-bout parity
apart from rendered commentary. These are wording variants, not additional catalogue IDs.

Named `composed_survival` commentary now has 50 authored survived templates, split across
standing and ground exchanges, while retaining the same canonical move and recovery rules.
Run `py -3 -m unittest fight_survival_commentary_test` to verify the authored template count.

The user-approved [survival expansion](FIGHT_SURVIVAL_EXPANSION.md) adds 40 recovery
techniques to the combined experimental engine: 50 survival choices and 440 moves total.
Use `--survival-expansion` with the retained combined audit flags. Position and ownership
checks distinguish top/bottom recovery, clinch control and knee-line protection; existing
survival resolution is reused. Normal play and packaged EXEs remain unchanged until release
acceptance. Run `fight_survival_catalogue_test.py` and `fight_survival_expansion_test.py`.
Verified 300-bout concentration falls from 25.66% to 19.03%. Full calibration retains all 39
group summaries exactly, including 48.16% competitive finishes. The paired CPU sample finds
no measured slowdown. Small-sample unused IDs still block overall release acceptance.
At 3,000 bouts all 40 additions appear, top-ten share is 19.30%, and 13,247 new recovery
selections have zero invalid roles. This longer frequency diagnostic is not a release
gate waiver or a new normal-play build.

The [move concentration investigation](FIGHT_MOVE_CONCENTRATION_PLAN.md) explains
why ordinary repetition damping cannot clear 25% on the observed action paths: ten
survival moves already account for 25.9452% of selections in 25,000 bouts. Use
`analysis/repertoire_selection_diagnostics.py --retained-damage --fights 300 --output analysis/NEW_OBSERVER.json`
for current-candidate selector observations with full-bout/RNG parity. New joint coverage
reports retain per-move counts. This is diagnostic work; all existing release gates remain.

`--kick-power` is a default-off audit trial for a 1% increase to resolved kick power
before the existing contest. It adds no random draws and does not affect kick target
selection, punch/body/leg damage or normal play. Run `py -3 -m unittest fight_kick_power_test`
before reviewing the full calibration.

`--standing-head-damage` tests a default-off2% increase to landed standing head-strike
impact in the audit harness. It excludes body/leg targets, clinch and ground strikes,
and separate knockdown bonuses. Fractional impact is retained; no extra random draw,
production-source rewrite or save setting is introduced. Use
`py -3 -m unittest fight_standing_head_damage_test` to verify scope and parity.
The full trial recovered 12 finishes and 13 competitive finishes, reaching 47.99%
competitive. The user accepted its middle-timing drift as advisory; the candidate remains
experimental until competitive and coverage blockers clear.
The [kick-power trial](FIGHT_KICK_POWER_TRIAL.md) adds 1% resolved kick power on top
of the retained head-damage change. Combined calibration reaches 48.16% competitive with
no calibration failures; coverage gates still prevent normal-play promotion.

Experimental submission development adds `--hold-transitions` (proven transitions between
real holds before top/guard chain credit) and `--cradle-setup` (contested cradle preparation
and single-use crank opportunity). Both remain audit-only, retain ordinary action/hold
choices, and add no simulation pass or RNG draw. Coverage and full calibration validate
their trace provenance. Run `fight_submission_chain_candidate_test` and
`fight_cradle_setup_candidate_test`; whole-bout CPU is measured by
`analysis/benchmark_submission_development.py`, not inferred from selector-only timing.
The [submission development report](FIGHT_SUBMISSION_DEVELOPMENT.md) records separate
and combined calibration, remaining coverage gaps and measured CPU cost. The fixed
supplementary Catch matchup tool (`analysis/cradle_matchup_diagnostics.py`) is separate
from canonical acceptance and never changes choices to obtain a desired move.

The audit-only `--heel-hook-identity --gift-wrap-mount` candidate repairs a catalogue
mismatch: an actual heel-hook submission can receive its named identity without a
standing counter window. It retains the skill threshold and separate positional
counter-grips. Run `py -3 -m unittest fight_heel_hook_identity_test` for scope, identity,
real resolver-to-trace and normal-play parity checks. Normal play remains unchanged;
coverage and calibration still gate promotion of the experimental 400-move engine.
The [unused-move repair report](FIGHT_UNUSED_MOVE_REPAIR.md) records three named
heel hooks in 900 ordinary diagnostic bouts, with absences reduced from 13 to 12.
The standard 300-bout unused-ID gate still fails; this is a verified partial repair.

The user has accepted attempted-chain median one for now: it remains measured and
reported as an advisory, not a release failure. Chain share, legality and other targets
are unchanged. The [opportunity-based variety review](FIGHT_VARIETY_TARGET_REVIEW.md)
explains the short-bout effect. Following user approval, the overall 20–24 distinct-move
mean is also advisory, with per-arm `variety_advisories` and raw means retained. Unused-ID,
concentration, balance and correctness limits remain hard gates. Neither policy change
adds simulation work or enables the experimental engine.

The audit-only `--boxing-chain-pool --gift-wrap-mount` trial filters boxing continuation
demand against the current legal named pool, preserving ordinary action choices, caps,
initiative and final selection. It adds no RNG draws and does not enable the candidate
in normal play. `analysis/benchmark_boxing_chain_pool.py` includes preview scoring cost
alongside selector cost at 800 moves, rather than hiding that work outside the selector.
The [completed combination trial](FIGHT_BOXING_COMBINATION_TRIAL.md) increases sampled
completed roots from 1,522 to 1,548, but competitive finishes fall to 47.33% in full
calibration. It remains disabled; the mount-refined base and release gates are unchanged.
Combined selector/preview cost is 12.27% at 800 moves, below 15%, but the profiled trial
adds processing time. This is not a claim of unchanged whole-career simulation speed.

`analysis/jab_timing_diagnostics.py --output analysis/NEW_TIMING.json` compares the full
mount-refined and jab-only calibration paths without altering mechanics. It reconciles
all canonical groups to both saved reports and separates new/lost finishes from timing
shifts. `--coverage-fights N` is explicitly a separate short diagnostic, not acceptance.
The [completed timing investigation](FIGHT_JAB_TIMING_INVESTIGATION.md) finds 25 gained
and 15 lost finishes, not a general delay. All 75 changed outcomes reproduce on recheck.
The jab trial stays disabled; only diagnostic attribution/reporting was corrected.

The audit-only `--jab-readaptation --gift-wrap-mount` trial isolates earlier repetition
readaptation to independent jabs on the mount-refined candidate. It reuses the existing
score curve and cap, preserves live follow-ups and other action scores, and does not
enable the candidate in normal play. Run coverage and full calibration separately;
`--fights` never shortens calibration.
The [completed repertoire trial](FIGHT_REPERTOIRE_TRIAL.md) improves competitive
finishes to 47.92% but adds a middle-timing failure and barely changes variety; it remains
unaccepted. A wider historical snapshot test also reports fixture-only hash drift,
with all 44 bouts' recorded mechanics and selection fingerprints unchanged.

Named-move absence findings in sampled coverage are now `content_frequency_advisories`,
not `content_gate_failures`, following the user's rare-sample policy. Structural/legality
checks, aggregate unused-ID ceiling, variety, chains, balance and performance stay unchanged.
The read-only `analysis/repertoire_selection_diagnostics.py` compares every mount-refined
bout with an uninstrumented control and reports repeated choices with unseen near-score
alternatives in the actual final pool. These observations are not guaranteed variety gains.

The [scarf-hold investigation](FIGHT_SCARF_COVERAGE_INVESTIGATION.md) traces lost
coverage to a changed fight path, not a demonstrated selection bug. The other14 live
setup observations match exactly; no forced technique, weight or expiry change was made.
An extended900-bout diagnostic records76 scarf setups and2 ordinary uses, with exact
first300 observation parity. This confirms reachability, not fixed-sample release acceptance.

The audit-only `--gift-wrap-mount` refinement retains gift-wrap's original back choke and
body-triangle branches, replacing its mount hammerfist edge with mount-only arm-pinch control.
Ordinary hammerfists remain legal; the three-branch limit and all identity gates remain intact.
It cannot combine with `--gift-wrap-control` and requires fresh coverage/full calibration.
The [completed refinement](FIGHT_GIFT_WRAP_TRIAL.md) improves gift-wrap completions
17/58 to 22/58 and competitive finishes47.40% to47.53%; full3,840/39-group calibration
records2,275 finishes and passes timing. It remains experimental: the48% floor and
coverage targets still fail. Thirty affected tests pass; ordinary play and EXE are unchanged.

The evaluator's audit-only `--gift-wrap-control` option tests one gift-wrap successor
replacement: hip-pressure riding instead of back-only body-triangle control. This
addresses observed mount-control choices without new IDs or forced actions. It remains
disabled pending fresh coverage and full calibration; ordinary play is unchanged.
The [completed single-root trial](FIGHT_GIFT_WRAP_TRIAL.md) raises gift-wrap root
completion from 17/58 to 26/60 but is rejected: competitive finishes fall to 47.19%,
middle timing fails and scarf-hold armbar coverage disappears. It remains opt-in.

The audit-only `--continuation-commitment` evaluator trial gives fresh, unhurt fighters
a bounded continuation-demand mixture using current skill/gas/target previews. It retains
one integer apportionment, every legal alternative and unchanged initiative/identity rules.
This is not a promoted engine; fresh full calibration and coverage gate any release use.
The first commitment trial is rejected: 2,269 finishes / 614 KO / 734 TKO across all
3,840 fights and 39 groups, with competitive finishes 47.05% and early/middle timing failures.
Chained share rises to 21.88% but median stays one and variety falls to 16.0717.
The Von Flue provenance validator now recognizes forward round changes in exchange-only
traces as horn expiry, without permitting stale setups or changing fight mechanics.
Fresh five-arm coverage confirms identical mechanical signatures; only the false boundary
failure disappears. The other release failures remain visible.

Run `py -3 analysis/chain_selection_diagnostics.py --fights 300 --output analysis/NEW.json`
for paired live chain-selection diagnostics. Every bout checks full audit and terminal RNG
parity against an uninstrumented control. Reports retain interrupted roots and distinguish
positive action previews from final eligibility and pool selection; this is not acceptance.
The [live audit findings](FIGHT_CHAIN_SELECTION_AUDIT.md) show 968 different-action
choices despite positive previews; only 51 named-stage losses involve eligible final-pool
exclusion or a losing draw. The verified 300-bout report preserves exact control parity.

The evaluator's `--repertoire-readaptation` trial applies the existing bounded repetition
curve one use earlier for independent choices. Genuine live follow-ups keep their existing
score; eligibility, counter/signature priority, action strength and mechanical rules are unchanged.
This remains audit-only: fresh 3,840-fight calibration records 2,267 finishes / 611 KO /
715 TKO, failing competitive finishes (47.26%) and middle timing. Coverage variety improves
to 17.1833 but still misses 20–24; chain median remains one, top-ten share is 25.53%, and
23 active IDs are unused. All default-control arms match the previous candidate exactly.
Selected IDs can change subsequent trajectories; these results do not authorize promotion.

The user-approved stronger-continuation trial is audit-only: add `--stronger-continuation`
to the joint evaluator to double the existing skill/gas-bounded action bonus (maximum +4).
It does not raise initiative bonuses, strengthen prepared submissions, change legal options,
extend expiry or relax any release target. Default candidate and normal play remain unchanged.
The first +4 trial is not accepted: its full 3,840-bout result is 2,289 finishes,
626 KO and 727 TKO, with competitive finishes 47.47% (mid tier 44.48%). Middle-fight
timing and zero sampled doctor stoppages also fail calibration. Chained share rises to
21.47%, but attempted median remains one and top-ten concentration worsens to 27.05%.
All five default-control arms exactly match the prior report; the trial stays opt-in.

See the [fight release checkpoint](FIGHT_RELEASE_CHECKPOINT.md) for the current
verified build status and unresolved acceptance gates. The full shipping run and
latest affected reruns pass; the fresh combined 800-move selector profile passes at
10.88%. One smoke click-selection probe remains unverified on the test display.
The 400-move candidate still fails acceptance and has not been packaged.

Experimental physical-top turtle/front-headlock menus now reuse ordinary top-position style
preferences before tactical-plan and chain weighting. This preserves existing primary/secondary
style influence without treating knee-line ownership as physical top. Survival overrides, legal
menu options and the +2 continuation cap remain unchanged; fresh candidate acceptance is required.
The fresh specialist-style calibration retains all 3,840 bouts/39 groups and records 2,272
finishes (606 KO, 725 TKO). Competitive finishes rise to 47.40% but still miss the 48% floor.
Coverage remains failing: distinct moves 16.4117, chained share 20.18%, attempted median one,
top-ten share 25.65% and 24 unused active IDs. Six affected isolated suites (60 tests) pass;
these correctness checks do not replace candidate release acceptance.

The experimental entry registry corrects the legacy fence-drive identity to its actual
failed-shot starting position, rather than its clinch/cage destination. The stable ID and
all other move properties remain intact; normal-play authoring is unchanged. Earlier candidate
measurements predate this correction and cannot establish acceptance of the updated candidate.
Fresh five-arm coverage restores fence-drive selection and preserves every arm's mechanical
signature, but still leaves 23 active IDs unused (a different fence-drive variant is now absent).
This is an eligibility fix, not evidence that the overall variety target passes.
Fresh full calibration retains 3,840 bouts and 39 groups: 2,269 finishes, 604 KO and 724 TKO.
Competitive finishes remain below acceptance at 47.26% (required 48–54%); this is the sole
calibration failure, separate from the unresolved coverage and chain-length failures.

Candidate reports now expose all unobserved active move IDs and the active follow-up count,
enforcing the plan's maximum eight unused moves and minimum 200 moves with successors.
These are distinct from draft-only coverage. This reporting correction changes no mechanics;
older reports containing only unused draft IDs do not establish the full catalogue target.
Fresh coverage finds 23 unused active moves against the limit of eight, including the two unused
drafts. The follow-up-count target passes at 363. All five mechanical signatures are unchanged.

Experimental chains no longer infer a preferred reaction from the selected defense's tags or
the successor tuple's order. Multiple legal successors remain alternatives for the existing
selector; successful roots are retained even without a designated successor. Normal play and
the two-tick chain lifetime remain unchanged pending candidate acceptance.

An optional sparse-root continuation trial adds legal alternatives to thirteen existing roots.
Run the joint evaluator with `--continuation-branches` to measure it; the default candidate and
normal game remain unchanged. It retains every existing branch, chain expiry, the +2 intent cap
and all release checks. New edges still depend on the real action, role, skill and identity gates.
This trial improved chained-selection share but worsened variety and specialist coverage; it
remains opt-in. Its full 3,840-fight result still fails competitive finish acceptance at 47.19%.

Pre-fence-source combined candidate checkpoint: 2,268 finishes in 3,840 fights (39 groups retained), with
competitive finishes at 47.22% against the required 48–54%. The 300-bout coverage records 16.4833
distinct moves per fighter, 20.12% chained selections, attempted-chain median one and 25.78%
top-ten concentration. Two draft IDs remain unobserved. The isolated fixes improve
correctness and coverage, but the 400-move engine is still not approved for packaging.
The independent-continuation 800-move selector profile passes at 10.89% median selector share across
three 44-bout samples. This is a profiled selector-cost check, not proof of unchanged career-day
simulation time or complete release acceptance.

Experimental clinch-chain previews account for both head and body targets, including the chance
that a missed strike never reaches the knee-weapon choice. This is an eligibility estimate using
the existing contest, not an extra attack or a guaranteed chain completion. Normal play retains
its original action selection and random draws.
The experimental chain engine also clears actor streaks at round breaks, matching the lifetime
of exchange sequences. Comeback intervention still operates normally inside each round. Both
changes require fresh candidate calibration and do not enable the experimental engine for play.
Candidate counter windows now retain ordinary authored fallback until counter eligibility is
known. A valid counter still wins preference; an unavailable counter no longer suppresses a
legal combination. This uses existing selection gates and adds no random draws.

The experimental specialist engine can enter knee-line control from bottom guard when leg-entry
skills exceed ordinary sweeping skills (leg skill at least 62). This is a positional entry, not
a completed sweep or submission. It uses the existing contest with a bounded adjustment, keeps
half guard excluded, and remains disabled in normal play. The bottom-leg-entry regression covers
ownership, thresholds, trace credit, expiry and default-off parity.
The full bottom-entry trial passes overall-rate and timing checks but still falls below competitive
finish acceptance (46.98%). Its 300-bout coverage has 16.3333 distinct moves per fighter and
attempted-chain median one; this is development progress, not a release-ready 400-move engine.

Experimental turtle and front-headlock controllers now apply their enabled tactical plans to
legal specialist choices before chain weighting. Previously these menus paid plan-dependent
energy costs without receiving the matching action preferences. Physical-top policy does not
apply to leg knee-line ownership or standing-back control. Disabled plans and normal play stay
unchanged, and this integration remains subject to full candidate calibration.

The experimental selector tests a bounded wider ordinary repertoire: after counter filtering,
up to three extra alternatives may join the strongest five if within 6.6 score points of the
best. Authored winners stay singletons and established top-five chain continuations take priority.
This is not shipped or accepted merely because it creates more possible choices; fresh coverage,
balance and performance evidence remain mandatory.
The latest combined trial clears finish timing but still fails competitive balance (46.91%),
distinct-move variety (16.3367) and attempted-chain median (one). It is not packaged. Its
source-guarded `joint_candidate_specialist_top_plans_*` reports retain all failures and groups;
the fresh 800-move selector benchmark passes at 14.20%.

Finish-balance acceptance now permits **two percentage points** of drift in overall finishes,
KO and TKO rates rather than identical historical counts. This keeps overall finishes near
60.4% (roughly 58.4–62.4%) on the same 3,840-bout schedule. Both historical comparison gates
use this headline tolerance; subgroup, method-family, timing and competitive-fight checks remain.
Historical JSON references are not regenerated. This policy change does not enable the 400-move
candidate or relax its variety, chain, legality or simulation-performance requirements.
Experimental leg escapes now oppose actual knee-line retention skills when the defender owns
the entanglement. This is a specialist skill-model correction, not a guaranteed escape delay
or move-frequency increase; the legacy engine remains unchanged until candidate acceptance.
The experimental chain candidate also corrects repertoire adaptation: adaptable fighters
receive stronger bounded pressure to vary repeated techniques, not weaker pressure. This
changes move selection and requires fresh fight calibration; it is not presentation-only.
The latest measured candidate produces 2,262 finishes / 587 KO / 712 TKO, with 47.19%
competitive finishes. Competitive balance, middle timing, variety and chain completion remain
open, so it has not replaced the playtest executable. The fresh 800-move selector benchmark
passes at 13.89% median; see the working plan for the retained full-corpus artifacts.

The move-system upgrade is in development, not yet packaged. Chain improvements and specialist
position mechanics are now being developed together in independently tested slices. This changes
the implementation order only: the 400-move goal, variety/chain targets and frozen 3,840-fight
finish-balance checks remain release gates under the tolerance policy above.
See [the working plan](FIGHT_MOVE_SYSTEM_PLAN.md).
The first specialist-entry candidate is developer-only: `py -3 analysis/evaluate_specialist_entry_candidate.py`
prints its full frozen-corpus comparison and fails when calibration differs. It never rewrites
the accepted baseline or enables the candidate in a career.
Joint trials use `py -3 analysis/evaluate_joint_fight_candidate.py --coverage` for a five-arm,
300-bout-per-arm comparison, or omit `--coverage` for the full locked calibration. The optional
`--output` creates a new diagnostic JSON file and refuses to overwrite an existing file. Draft
move definitions are scoped to the audit and restored afterwards; they are not extra shipped moves.
For a larger fixed-corpus frequency investigation, use
`py -3 analysis/evaluate_joint_fight_candidate.py --coverage --combined-only --fights 3000`.
This runs the same deterministic combined arm without repeating the four comparison arms; it
retains content and variety failures and cannot replace or shorten the full calibration gate.
Experimental coverage includes prepared-submission observations: actual action-ticket probability,
prepared-hold ticket share, readiness and realized choices. Expected-use totals are conditional on
the observed ordinary menus, not predictions under different tactics. Opponent interruptions and
emergency survival stay separate; the audit adds no mechanical random draws or runtime save fields.
Observation totals reconcile with actual setup roots, so entirely missing telemetry cannot pass.
Defense repetition is checked within every rolling 300-fight window, including windows crossing
sample boundaries; whole-run totals remain visible separately for extended audits.
For current-normal versus candidate striking evidence, run
`py -3 analysis/compare_candidate_striking.py --fights 300 --output analysis/current_normal_vs_candidate_striking.json`.
The paired diagnostic reports recorded strike attempts, landings, damage, knockdowns, finishing
exchanges and resets by action, position and actor style. Quality cohorts also retain the actor's
post-action gas band, streak band and real counter status. Its bout cohorts distinguish knockdown
bouts that do and do not reach KO/TKO from KO/TKO bouts without a recorded knockdown. It preserves fighters/RNG,
refuses existing output and rejects source changes during collection. Net hurt changes are not
claimed as isolated recovery or stoppage-check counts.
Use `--calibration-corpus` instead of `--fights` to compare the exact 3,840-bout calibration
schedule per side, including canonical rating/style groups. This mode cannot be shortened;
the ordinary 300-fight move-coverage sample is not a substitute for diagnosing calibration drift.
Add `--standing-chain-ablation` to compare the combined candidate with the same candidate's
range/pocket chain-weight redistribution bypassed. This is an attribution experiment only:
ground/clinch preferences, named sequences, pocket mechanics and finish formulas remain active.
Alternatively, `--pocket-action-bias-ablation` removes only the candidate pocket menu's
power-punch/kick/clinch redistribution. Full-corpus
evidence rejects the pocket ablation: it changes 2,264 candidate finishes to 2,258 and KO from
586 to 574, so the normal candidate keeps its current pocket preference.
Use a new output filename; neither diagnostic arm is enabled in normal careers.
`--failed-shot-retention-ablation` isolates the candidate's retained denied-shot scramble by
using the legacy retention gate inside takedown resolution only. Successful takedowns and cage
progress still resolve normally. All three ablations are mutually exclusive. The report also
counts standing departures by action/destination and standing shots with no recorded takedown,
including cage progress. These are observed paths, not estimates of attacks a fighter would
otherwise have thrown. Use the full calibration corpus to judge finish consequences; this
diagnostic does not approve removing specialist positions or change normal simulation cost.
The completed full-corpus ablation reaches 2,279 finishes / 609 KO / 724 TKO but still fails
the locked counts and removes observed failed-shot residence. Its gains are insufficient for
promotion; see the [standing opportunity audit](FIGHT_STANDING_OPPORTUNITY_AUDIT.md).
`py -3 analysis/standing_counter_diagnostics.py --fights 300 --output analysis/standing_counter_opportunities_300.json`
observes counter-window ages at both fighters' initiative calls. Previous-round windows and
same-round ages above two ticks are separate from recent/unknown metadata. These counts show
where the candidate's opponent-window guard applies; they do not prove a lost legal continuation,
changed actor or missing finish. The observer preserves complete fight results, traces and RNG.
`py -3 analysis/failed_shot_escape_intent.py --output analysis/failed_shot_escape_intent_calibration.json`
tests a narrower audit-only preference: Sprawl And Brawl fighters controlling a failed shot
prefer disengagement using a 1.58 demand factor. It preserves the original integer ticket total,
action order, every alternative, survival overrides and subsequent chain weighting. It does not
change normal play; the command returns failure while any canonical result gate remains unmet.
The tested preference reaches 2,265 finishes / 591 KO / 714 TKO and leaves the 300-bout coverage
arm unchanged. It remains an explicit failed-calibration trial, not a shipped gameplay setting.
The separate audit command
`py -3 analysis/round_counter_expiry.py --output analysis/round_counter_expiry_calibration.json`
tests expiring prior-round counters before initiative in the combined candidate only.
Add `--coverage` with a different new filename for the full five-arm content comparison.
It changes no same-round expiry rules, production settings or executable. Both modes report
retained failures and return nonzero when their gates fail. The round-expiry trial reaches
2,257 finishes / 586 KO / 708 TKO, worsening the combined candidate's finish calibration,
and remains audit-only. The experimental initiative benefit applies to a live legal
continuation. Skill readiness and remaining gas bound it; hurt, exhaustion and an opponent's
counter window suppress it. It neither guarantees the next action nor extends a combination.
Actor-owned counter windows also preserve counter-technique priority: an ordinary follow-up
cannot earn continuation credit when eligible counters make that follow-up unavailable.
`analysis/generate_variety_opportunity_report.py` diagnoses distinct-move headroom in the
combined candidate's observed final selection pools. Its matching bound retains counter,
authored, strongest-five and continuation priority, and includes fighters with no selections.
It is not a substitute for the ordinary variety gate or proof about different fight trajectories.
Follow-up tuple order is not treated as universal defensive-reaction metadata. Alternative legal
branches remain available through the independently selected next action; explicit reaction
semantics require authored provenance rather than inferred tuple positions.
Chain opportunity diagnostics separate survival, other undeclared actions and declared actions
without named completion. Failed roots remain in the denominator; trace-only output does not
claim to identify hidden eligibility or ranking decisions.
The current trial catalogue contains 400 moves (346 active definitions plus 54 specialist drafts).
Its final fifteen drafts cover five leg attacks and ten controls, escapes, positional counters
and disengagements. Experimental leg entry retains a mechanically attempted knee line after a
dangerous non-finishing bottom submission; it does not add a finish roll or require a special trait.
Full-catalogue authoring is not release acceptance: ordinary frequency, variety and calibration
still need to pass before these drafts are registered in normal play.
Experimental submission selection now uses explicit compatibility with the mechanically resolved
technique. Unproved delivery details cannot earn a different move's signature or mastery credit;
an unmatched technique uses a generic identity while commentary retains the actual lock's name.
Candidate reports distinguish compatible named submissions, honest generic fallbacks and
contradictory named identities by technique and position; a wrong named identity fails the
measured quality gate rather than improving apparent move variety.
The experimental submission pool now resolves 21 eligible authored variants before its existing
random draw. It preserves the weighted pool's length and each slot's choke/leg category, using
position, ownership, skill and exclusive-style restrictions. Attacks needing unmodelled setups
remain unavailable rather than being invented by the commentary.
Experimental base pools now distinguish top and bottom ownership: full-guard attacks cannot be
drawn underneath mount, and mounted holds cannot be drawn from side control. Unsupported setup
and gi-dependent labels are excluded. This changes candidate technique distributions and requires
fresh calibration; the adapter still conserves its own input tickets. Bottom attack frequency
remains development work, not accepted balance. Experimental dominant-position submission bonuses
now require the attacker to own top position; a fighter trapped underneath does not inherit them.
Bottom guard-work bonuses apply only from actual bottom guard/half guard. The valid top-guard
no-gi Ezekiel remains available, with its existing named-technique eligibility requirements.
Experimental follow-through now depends on the relevant combination/grappling skill, adaptability,
discipline and remaining energy instead of a flat action bonus. It only favours already eligible
live continuations; survival, defensive interruptions and independent move selection still apply.
Submission continuation previews share the resolver's current technique pool without drawing RNG.
Only mechanically available holds contribute to intent, and overlapping branches count once.
Experimental submission defenses use the current resolved hold, even when its move identity is
generic. Leg-only escapes are excluded against non-leg submissions, and candidate reports reject
that contradiction without changing fight RNG.
Experimental top-guard leg attacks now begin with a contested straight-ankle entry. Winning the
knee line leads to the existing leg attack/escape/counter menus; the entry itself cannot finish
or earn a pass, takedown or physical-top control bonus. Reports separately count valid entries,
denials and inconsistent trace evidence. Half-guard entries still need their own extraction setup.
Experimental Von Flue opportunities now require an explicitly retained plain-guillotine neck wrap
from bottom half guard. Only the top fighter's immediately following exchange can use it; other
actions, position changes, the horn and finishes invalidate it. Setup alone cannot force a choke.
The experimental strong-guillotine defense assessment separates stopping choke pressure from
clearing the grip and gaining a shoulder angle. It preserves the existing top-control award;
only retained grip plus the angle can create a later Von Flue opportunity, without an extra roll.
When the grip remains but the angle is missing, the experimental engine now preserves one
immediate positioning opportunity. The same top fighter must win a subsequent control contest;
the defender can clear the wrapping arm, and intervening actions/resets cancel the opportunity.
Positioning itself grants no submission attempt or finish roll. A successfully prepared choke
still has its separate, unchanged one-exchange expiry and must actually be selected.
Experimental scarf-hold armbars likewise require a contested near-arm isolation from top side
control, followed immediately by a separate submission attempt. Setup keeps ordinary control
credit but cannot claim an unrelated named control, signature or completed chain. Both setup
families have consecutive trace-provenance gates and remain disabled in normal play.
If a referee stand-up ends the setup exchange, the opportunity is cancelled immediately and the
stand-up takes narration priority; the feed cannot leave either fighter underneath at range.
The experimental setup selector distinguishes arm isolation from ordinary ride/pin intent using
technical skills, bounded style familiarity and enabled fight plans. Success alone must not turn
every side-control hold into scarf hold or remove ordinary controls from consideration.
Registry fingerprints bind the exact definitions, successor graph and lookup order used by each arm.
Joint coverage reports include actual exchange occupancy, action counts and per-draft selection
counts. Pocket use is measured against range-plus-pocket exchanges, not all fight time or the
number of distinct position contexts.
Full candidate calibration artifacts also retain every canonical group, including tier and
matchup breakdowns, so balance diagnosis is not limited to aggregate finish rates.
Setup follow-through reports retain interrupted opportunities and distinguish opponent actions,
other top actions/holds, context changes and boundaries from actual use; cancellation is not a root.
Prepared-attack preference remains bounded and optional: current legal setup, technical readiness,
gas and enabled plan execution can favour the follow-up without overriding survival, removing
alternative actions/holds or extending setup lifetime. Technique weighting uses the existing draw.
Pocket reports also count entries, observed residence lengths and exits, including episodes cut
short by a horn or finish before another exchange. They do not count a transition label as time
spent inside.
The experimental distance slice now lets successful punches establish persistent pocket range,
with defensive pivots and range-favouring jabs providing exits. Inside action preferences differ
modestly, while distance alone adds no damage, control or recovery credit. These changes remain
disabled in normal play pending the same calibration and coverage gates.
Experimental specialist ratings use supported detailed skills for standing escapes, front-headlock
submissions and position-specific rides/drives. Front-headlock and turtle control time belongs to
the actual controller; leg-entanglement knee-line ownership is not treated as physical top control.
Audit traces record the control-credit point before a later referee reset so time can reconcile
without inventing a control award from the final position alone.
Experimental stalled-scramble separations now retain genuine control work without granting
unearned recovery or success credit. Both fighters' combinations end at the neutral restart;
coach/trait commentary does not praise the referee's intervention as a fighter achievement.
Chain diagnostics retain these interrupted attempts and exclude neutral restarts from potential
continuations, so their optimistic coverage figures cannot hide referee-broken sequences.

Version 3.0.10 hardens long-running careers: child-promotion ownership is protected, duplicate fighter names are safe in live fights and player events, event completion and save loading are transactional, universe validation is shared and read-only, and release builds use an isolated regression runner plus a pinned offline toolchain. It also adds staged Grand Prix scheduling with identity-safe replacements, postponements and tournament deciders, while capping only the global result/event feeds—never fighter records or career totals—so long saves remain responsive. See [CHANGELOG.md](../CHANGELOG.md) for the complete release notes.

The active feature-development map is maintained in [FEATURE_DEVELOPMENT_BACKLOG.md](../FEATURE_DEVELOPMENT_BACKLOG.md). The staged mechanics roadmap is documented separately in [FIGHT_ENGINE_DEVELOPMENT_PLAN.md](../FIGHT_ENGINE_DEVELOPMENT_PLAN.md), while [NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md](../NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md) audits the existing emergent-story systems and defines an event-driven expansion that must preserve calendar performance. The frozen fight-engine Phase 0 distribution is in [analysis/FIGHT_ENGINE_BASELINE_REPORT.md](../analysis/FIGHT_ENGINE_BASELINE_REPORT.md). Future-dated child-promotion events, staged Grand Prix competitions, the executable Grand Prix Showcase super-event, explicit legacy profile migration, the evidence-backed 100-year observer audit, and the first decision-center pass across Company, Regions, Staff, Scouting, World Hub, and the Promoter Dashboard are now implemented; the remaining roadmap focus is routine modal cleanup and content expansion. Finance reconciliation remains a required invariant for new cash paths.
When taking control of an AI promotion, stale zero-month inherited deals are renewed for 12-24 months so the promotion's roster stays intact.
`Build Portable.bat` now builds both `MMA Warriors.exe` and `MMA Warriors Database Editor.exe` into `dist\\MMA Warriors` every time.
The MMA Child Promotions manager includes live cash/stability/AI-mode metrics, roster filters, contract and potential data, fighter detail inspection, loans, recalls, and confirmed parent transfers. Child launches require an eligible opening roster; child companies cannot be taken over through the ordinary company flow; champion loans vacate parent belts; and transfers respect closed parent divisions.
Child promotion transfers renew an expired AI-signed fighter for a normal contract term, and parent profit shares appear in the main company's finance history.
Protected parent fighters may use a time-bounded development loan with an agreed return month/week. The manager shows the term, returns the fighter through the existing belt/membership pathway at the first safe weekly boundary, and surfaces any delay caused by a committed child bout; zero-date legacy loans remain open-ended until recalled.
This release expands the living-world simulation, improves watched fight-night presentation and commentary variety, adds career journeys and directed scouting, introduces the shipped Universe Database Editor, and strengthens UI scaling, AI scheduling, finance stability, contract negotiations, accessibility, and release packaging. Version 3.0.7 also consolidates starting-career selection into one dropdown and one Start action. Fighter source markers are kept as internal database metadata so intentional historical snapshots remain distinct without cluttering player-facing names. See [CHANGELOG.md](../CHANGELOG.md) for the 3.0 release notes and hotfixes.

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
pairings. See [`docs/FIGHT_FINISH_SYSTEM_AUDIT.md`](FIGHT_FINISH_SYSTEM_AUDIT.md) for the
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

The Game & Saves **Career → DB** action is a deliberate J12 conversion for creating a new-start
world from the current career. It preserves fighter identities, current supported skills/age,
career records, roster ownership and supported contracts, but resets time, cash, finance, inbox,
pause targets and active work so a new game cannot resume an old card or obligation. Completed
history and every excluded ongoing item are retained in a labelled `<name>.conversion.json`
provenance manifest with a structured preflight report; they are not imported as playable history.
The prompt lists the exact exclusions and requires acceptance. Structural issues or an existing
destination stop the write, and cancellation or a failed staged write leaves both the source save
and destination untouched. Career-start databases are labelled separately from legacy databases
in the panel and can be loaded like any other starting world.

The game starts in the explicit **Dark Mode** theme. Themes can still be changed from the in-game theme selector, and native list controls follow the selected palette immediately.

All tab, detail-window, and popup tables support sorting by clicking their column headings. Numeric ratings, money, records, durations, dates, and text columns use the same shared sort behavior.

Each game now owns a self-contained folder, for example `Saves\Game 1\savegame.json`. The Career Library shows the active career in a high-contrast banner, reports visible career/snapshot counts, provides a scrollable slot browser, and reveals the selected company, game date, save time, group, and active status before an action is taken. Selection-only actions remain disabled until a valid row is chosen, while save, load, backup, restore, folder, and settings controls are grouped by purpose. Its two rolling recovery backups, autosaves, crash recovery files, and spectator archives stay inside that same `Game 1` folder, so multiple careers cannot overwrite one another. Autosaves use the same two-slot rolling policy per cadence, overwriting the oldest snapshot instead of accumulating files. Spectator Mode also writes a permanent archive at every completed decade, such as `Game 1 - 10 Years.json.gz`, under `Saves\Game 1\Snapshots`. Existing flat saves remain loadable and move to the folder layout the next time they are saved. A failed optional recovery snapshot is logged without blocking Quick Save or a switch to another slot. Save files must contain a JSON object; malformed top-level data is rejected before split-save blocks are processed. Restores validate the selected snapshot before backing up or replacing the destination, and a restore error leaves that slot untouched. Runtime diagnostics live in `Logs\mma_warriors.log`; unexpected failures create a separate report in `Logs\Crashes`.

Before moving a build to another laptop, run `Portable Check.bat` from the packaged folder. It confirms that the EXE is present and tells you whether runtime data will be stored beside it or in the user profile fallback.

Fight Night uses one live broadcast viewer for MMA, boxing, kickboxing, Muay Thai, wrestling, and Brazilian jiu-jitsu. Other-sport replays include sport-native round/period/match starts, clocked exchanges, cumulative scoring, stamina and condition reads, and an official result. Boxing runs six-, eight-, or ten-round non-title contests according to level and 12-round title fights; three independent cards produce unanimous, split, majority, and draw verdicts, with knockdowns reflected as 10-8 or 10-7 rounds. Standard Muay Thai runs three rounds and title bouts run five, with judging weighted toward effective kicks, knees, elbows, dumps, balance, and clinch control rather than generic strike volume; Lethwei contests remain five-round, knockout-first bouts. The default **Broadcast** commentary view derives a shorter feed from the complete stored transcript: repeated low-value calls are condensed, while round boundaries, meaningful damage, submissions, cuts, fouls, tactical changes, finishes, scorecards, metrics, and results always remain. Landed standing offense, completed takedowns, landed ground strikes, passes, sweeps, reversals and escapes receive evidence priority over routine movement; identical calls remain capped at two per round. Compact notes report how many standing, standing-striking, takedown, ground-control and ground-striking exchanges were omitted instead of replacing them with a generic reset. **Detailed** mode plays the complete stored transcript, and completed-bout review plus the per-round Analysis Explorer retain the underlying technical evidence. The active live bout can switch between Broadcast and Detailed without restarting playback or changing the archived transcript; clearer round separators and distinct knockdown/finish emphasis make long cards easier to scan, while a small status label shows the current Balanced, Technical, Excitable or Concise voice. Commentary density and voice remain persistent options under **Game & Saves -> Game Settings**. Exact judge cards and numerical totals remain sealed until the official result. Duplicate-name opponents retain separate red/blue identities, telemetry, result records, and replay labels. Only one live card can be open, advancing or skipping is state-guarded, full-card skips require confirmation, and settlement failures leave the report retryable. The viewer supports compact laptop layouts, keyboard controls, visible scrollbars, adjustable text size, Follow live, round/period navigation, and paced holds for round summaries and finishes. The end-event report is vertically scrollable, and archived replays preserve the original location, profit, excitement, and event context without applying results twice. Event summaries and Results/Fight Night archives also expose a read-only preparation timeline with recorded campaign evidence, press, weigh-ins and final readiness; legacy cards without that field remain readable and opening the cards never reruns preparation or consumes RNG. Twelve one-time head, body and leg damage milestones make deterioration visible without adding new damage rolls: fighters can redden and bruise, protect a damaged midsection, shift their weight or develop a visible limp as the existing trauma totals rise. Exact cut calls use the recorded location, bleeding, swelling and vision-risk facts, and every such line is retained in Broadcast and the chronological Analysis Explorer.

A 36-file, field-recording-based crowd-audio pack is integrated into Fight Night from `assets\crowd_audio`. Its 12 trigger families each have three genuinely different variants for arena buildup, walkouts, opening roars, strikes, knockdowns, submission danger, inactivity, round endings, finishes, decision tension, split-card boos, and respectful post-fight applause. One loop-safe arena recording now remains open as a quiet, crossfaded bed for the entire live card; walkouts, mastered round bells and factual reactions layer above it without restarting the ambience. Fight Night randomly rotates variants without immediately repeating a take, honors their recommended mix gain, reserves reaction capacity for knockdowns and finishes, and limits lower-value overlap so commentary stays clear. Closing the live viewer stops its bed and outstanding reactions rather than allowing audio to bleed into the next screen; the live stop event and audio-only entropy remain outside card-settlement rollback data. Hometown appearances receive the strongest reaction lift; national, adopted-home, and training-base connections receive smaller boosts, and the live introduction explains who has the local support. The accepted revised-pack mixes remain Variant 1, while Variants 2 and 3 use alternate recordings rather than pitch-shifted copies. Brief gasp and "ooh" reactions are mixed below the sustained arena response. The manifest and `LICENSES.md` preserve trigger metadata, attribution, and CC0 provenance. A 0-100 slider in the live viewer changes the next cue's volume immediately and saves the same setting exposed under **Game & Saves -> Game Settings**. If the pack or Windows playback is unavailable, events continue with the original procedural fallback cues.

Striking commentary uses action-specific situation banks rather than shared generic calls. Boxing, kickboxing, Muay Thai, Lethwei presentation, and MMA distinguish entries, counters, body work, leg damage, kick checks, pocket/clinch work, rope or fence pressure, defensive exits, knockdowns, cuts, and damage-aware follow-up attacks. MMA exchange prose is rendered from the recorded actor, named move, target, defense, outcome, counter state and settled position instead of joining a selected technique to older broad-action text. Each supported MMA style owns an exclusive authored combination and finisher: striking disciplines retain ordered hand, kick, elbow and knee components plus style-native knockout techniques, wrestlers connect characteristic entries to ground-and-pound stoppages, and grapplers receive distinct chokes, joint locks and leg locks. A fighter may use these through either a primary or secondary discipline, but an unrelated style cannot inherit them from a signature assignment. Finishers only name the causal technique attached to an already-resolved KO, TKO or submission; they do not add another finish opportunity, and an individual legal signature finisher takes priority over the broader style finisher. Each bout records presentation-only fighter profiles derived from detailed attributes: the relevant strength and style family shape the vocabulary for punches, kicks, counters, clinch work, takedowns, transitions, control and escapes. All 46 fighter traits receive a natural pre-fight introduction. Combat-relevant traits can also shape a live call only when completed trace evidence supports the connection—for example a Body Hunter landing to the body, a Counter Specialist using a real counter window, or a Scramble Artist completing a transition. These contextual calls are capped at one per fighter per round and two per bout. A saved camp that matches a real Gym also receives a natural corner introduction using only its recorded coach, location and specialties. Live camp calls require a completed exchange matching the Gym's actual boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning specialty. Promotion, academy, unknown and legacy labels never inherit invented Gym facts, and contextual camp calls use the same one-per-round/two-per-bout cap. Ground calls distinguish top pressure from bottom survival, name the actual armbar/choke/leg lock and its registered defense, preserve the resulting position, and announce inactivity stand-ups as referee actions rather than fighter escapes. Deterministic bout salt and larger landed, blocked, slipped, survived, control, transition, escape and visible-damage pools vary otherwise identical exchanges without consuming any fight RNG. Recorded signature/mastery status, stance matchups, plan changes, momentum, accumulated damage, verified camp/coach identity, championship stakes and rivalry history can enrich the call only when that fact exists. Broad trauma narration never invents a fracture, organ injury or precise body-part diagnosis; only structured cuts name an exact location. Finish narration preserves authored submission chains, medical/injury evidence, head-kick and walk-off behavior while staying connected to the actual final move and position; body- and leg-kick knockdowns remain strike events unless the separate injury-stoppage check fires. Between-round advice cites visible gas, damage, repeated techniques, control and successful move families. Viewer compaction, trait/camp wording and voice selection do not change action selection, scoring, stoppages or the locked finish percentages.

## Developer Change Contract

The current change-package policy is maintained in
[AGENTS.md](../AGENTS.md#mandatory-change-package). Update detailed feature behavior
here, quick-start instructions in the root README, and the owning developer
contract when its rules change. Keep release history in the changelog and link
to authoritative explanations instead of repeating them.

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

The current development model is documented in [`docs/FIGHTER_DEVELOPMENT_GUIDE.md`](FIGHTER_DEVELOPMENT_GUIDE.md); current clinch, cage, ground, and damage mechanics are documented in [`docs/FIGHT_DAMAGE_AND_CLINCH_AUDIT.md`](FIGHT_DAMAGE_AND_CLINCH_AUDIT.md); shared per-theme tab colors and WCAG ratios are documented in [`TAB_ACCESSIBILITY.md`](../TAB_ACCESSIBILITY.md).

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
- Start a Spectator Mode save to hand the selected player promotion to the AI, fast-forward the living world by week, month, year, or a chosen date, and watch any promotion's latest card in the live fight-night viewer before taking control of a company. The observer panel can stage an exact target-date stop or pause after the next hosted event; the policy is saved as data, records the completed boundary/reason, and resumes deliberately without replaying a settled week.
- Pin an active state manually before a long run; the separate Checkpoints manager shows source, game date, size and atomic-verification status and can restore to a chosen slot or delete after confirmation. Pinned snapshots are bounded and never replace rolling recovery files.
- Book main cards, prelims, early prelims, title fights, TBA fights, and career-affecting 4/8/16-fighter MMA tournaments. Ordinary tournaments remain one-night by default; Grand Prix entries can be spread across 1–4 event cards within their bracket limits. Tournament entrants are seeded by rank, use the normal camp and weigh-in system, accumulate fatigue between rounds, can crown a champion in the final, and remain reserved from other bookings. Each completed stage and its uniquely identified next card save together, so reloads retain the bracket and a settlement retry cannot create another stage. Injuries or confirmed drug failures use normal eligible replacements or move the whole Grand Prix, and tournament draws use a tournament-only 15-minute decider with judges selecting a winner at the limit.
- Schedule shows by month and week, then watch or instantly simulate them.
- Advance from the persistent responsive top bar; long promotion names use the flexible center field while popularity, stability, cash, date, and advance controls remain readable. World simulation runs in queued steps with live phase/progress feedback, guarded controls, cached promotion-level card-date decisions, and efficient batched spectator fast-forward. Promotion monthly reviews are spread evenly across the four weekly advances; regional development still runs one card per circuit per month instead of accumulating at the month boundary.
- Quick Load and Save Manager slot loads show a themed, modal please-wait panel with named phases and a high-contrast accent progress bar while large career files are read, rebuilt, and refreshed. If Quick Load needs a recovery snapshot, the same panel identifies that recovery attempt before the result is shown.
- Mail / Decisions reserves a fixed two-row action area so all eight buttons are visible immediately without requiring a sash drag; the message table alone shrinks when vertical space is tight. It explains how many messages are shown, stored, filtered, unread, and actionable, and lets Show All clear every visibility filter. Owner Goals always retains a summary and labelled Expand / Collapse control, while compact guidance in Message Detail explains how to reveal context without a full-width onboarding alert.
- Matchmaking keeps Current Fight Card and its action buttons on-screen: the card sits beside Available Fighters on wide displays and moves above them on narrow displays. Expanded Show Details uses two compact control rows at wide widths, a three-row medium layout, and a safe stacked narrow layout while retaining every event field, scheduling action, status, forecast, and show tool. Its empty state explains how to add the first bout, and every fight keeps slot, matchup, weight, hype, build, fatigue, and medical-return information visible without page-level horizontal scrolling. Available Fighters opens in a focused Essentials view, with Readiness, Form & Fitness, and All 20 presets that preserve every scouting metric and the selected rows. Every ordinary row click toggles that fighter into or out of the selection, allowing pairs and 4/8-fighter tournament groups to be built without holding Ctrl; double-click opens the fighter directly under the pointer. Its five booking actions use one row when space permits and a two-row grid at the minimum pane width. Matchup Insight keeps step-by-step selection guidance, history, booking context, and the row-colour guide behind a labelled persistent disclosure, empty alert bands no longer consume table height, and Compare Selected opens the full side-by-side fighter viewer.
- The Matchmaking Booking Workbench also stores optional tentative medical drafts for a blocked same-division candidate. Each draft keeps the fighter IDs, target date, earliest recorded return and current camp facts, and can be reviewed from Medical Drafts. It is explicitly non-binding: no fighter reservation, camp assignment, cash spend, weigh-in, title credit or recovery promise is made; at event week the normal medical and booking checks run again. A passed target date is shown as Needs replacement and a candidate who clears is shown as Ready to confirm rather than being auto-booked.
- Matchmaking also has a Draft Review showing preserved pairings and unresolved TBA slots. Foundation migration gives legacy draft rows deterministic event/draft-scoped booking IDs without touching RNG; a host that cannot run migration labels any unresolved fallback as Legacy reference. Complete stable draft pairings can open a locked-slot proposal window: alternatives are ranked with company/world positions and blockers, the card is unchanged until an explicit commit, and stale cards are rejected. One-corner replacement preserves the title, tier, plans and unaffected fights, records a receipt/history entry, and is retry-safe; scheduled event fights remain read-only.
- Staff autonomy briefs expose an explicit delegated action. Marketing can either prepare a free campaign review or, only after the player selects Full Auto and commits the brief, run the selected existing Media action after a pure preflight against its normal capacity, cash-reserve and target checks. The action, actual spend and evidence are retained in the Staff work receipt; a missing spokesperson or stale/unaffordable campaign becomes Needs attention rather than being retried or silently substituted.
- Matchmaking staff recommendations reuse the same Booking Workbench model as the manual screen, so advice includes identity-linked alternatives, company/world ranks, fit/build scores, hard blockers and cautions without generating, reserving or committing a bout.
- Talent Relations reviews include existing relationship-case IDs, statuses and recorded reasons for the selected fighter; they do not open, resolve or mutate cases, promises, trust or morale.
- Staff work receipts include a View selected read-only evidence brief. It keeps the compact table readable while exposing the full stored payload, including Matchmaking alternatives and open Talent Relations cases; opening the detail never reruns a handler, quote or RNG.
- Manual Drug Testing now records stable, save-owned screening cases with fighter identity, policy, preliminary result and evidence scope. Preliminary alerts never become injuries or sanctions, and the `None` policy performs no sampling, charge or test roll. Drug Testing Cases is a read-only ledger; confirmation, provider selection, appeals and sanctions remain separately gated.
- Fighter Profile History treats missing at-the-time opponent records as an evidence gap: it shows `Not recorded` instead of substituting the opponent's current record. Valid archived replay or bout snapshots still win, and legacy entries with no opponent identity remain `-`; an unidentified same-date row never borrows the first snapshot from another bout.
- Company membership history is recorded as append-only, ID-linked join/leave/loan/return facts for contract, market-entry (including automatic TBA and last-minute replacements), feeder, academy, editor, swap and closed-division transitions. Each fact keeps its effective date precision, reason and source transaction; repeated callbacks are deduplicated without RNG or counter drift. Child loans and recalls retain both sides of the move, and title holders are vacated through the shared lineage helper before departure. Fighter Profile History now shows a compact Company Timeline with closed/current intervals and an explicit incomplete-coverage label, plus a full read-only window with as-of filtering, title context, copy and JSON export. Imported current rosters are represented as known present at migration, never assigned an invented join date; the searchable index retains that distinction.
- Automatic AI free-agent signings use the same membership hook before moving a fighter between the market and a promotion roster, so those company intervals appear in Profile History with a stable source transaction.
- Player free-agent signings, direct contract negotiations, automatic TBA fills and last-minute replacements now write their incoming company fact before the roster move; feeder negotiations record both sides at the same boundary and the narrative hook suppresses duplicate writes.
- The explicit load repair for an already scheduled bout records a stable player-company `join`/`return` fact before restoring a fighter to the roster, while ambiguous references remain unresolved and raw booking evidence is preserved.
- AI opening/depth and emergency signings, academy and rival-academy graduates, and regional intake routes record destination membership before roster insertion, keeping Company Timeline coverage complete without altering their existing selection or development behaviour.
- Foundation source checks cover those intake boundaries and the regional departure helper, so future roster changes cannot silently bypass the historical timeline.
- Player-owned Combat Sports market signings record their destination-company fact before entering the division roster, preserving the same timeline guarantees outside MMA.
- The post-change stability playtest reaches Month 4 successfully for seeds 2201–2203, with normal event and retirement processing intact.
- Media settlement receipts include a View selected read-only evidence brief with separated rights delivery, production quality, audience outcome, sponsor duties and duty-period history; the complete stored receipt remains available and inspection never reruns settlement.
- The sidebar Fight Night route is a styled, scrollable Event Log with complete stored history, a read-only line-count summary, and theme-aware accents for event headers, results, key moments, office actions and system notices.
- Company transfers and child-promotion loans/recalls now begin with explicit, identity-linked proposal records. The Company Proposal Ledger shows both parties, fighter IDs and ranking snapshots, cash, expiry/recall boundary, warnings and the recorded outcome; stale ownership, booking, title or cash state is surfaced for review rather than silently substituted. Existing negotiation, finance, belt and membership rules remain authoritative.
- Regions include a read-only Feasibility Review with current bookable pairings, ready champion/top-10 depth, visible versus unscouted local free agents, unlocked venues, scheduled shows and explicit blockers. It is scouting-aware and RNG-free: refreshing it never books, reserves, prices or creates an invitation, and thin divisions never bypass title merit.
- Fight-night viewer with play-by-play, a tale-of-the-tape scoreboard, live round-by-round scores, high-contrast red/blue gas and condition bars on dark tracks, card progress and bout states, colour-coded knockdowns and finishes, auto-play, round timing, scorecards, skip controls, post-event bonuses, and live/completed tournament bracket viewing including staged Grand Prix progress.
- End-of-year awards (Fighter, Fight, Knockout, Submission, Prospect, Veteran, and Promotion of the Year) crowned automatically each January, with a browsable awards history.
- A living world where fighters age a year each season, prospects break out, veterans decline, title contenders emerge on win streaks, and busy regions grow.
- Regional feeder circuits where 16+ prospects build records, develop, graduate to free agency, and can return to stay active; AI promotions scout them through budgeted, stealable contract offers.
- Fighting Academy and Combat Sports are main management screens in the left navigation, alongside Roster, Contracts, and Finance. Selecting either opens it in place instead of a separate window, so switching between management areas never loses the main application context. Detail views — academy prospect profiles and card replays, child-promotion management, and circuit records and history — still open as focused popups.
- Player-built Fighting Academy with hired-scout regional networks that take eight weeks to establish, scout-quality-driven lead strength and report accuracy, and no fallback phantom scout. Only one network can be active, and its live recruitment list caps at eight leads; major rival promotions run visible persistent youth programmes and may bid for the same regional talent. Prospects arrive aged 12–15 with 30–60 current rating; potential is normally 60–98, while 99–100 generational prospects are exceptionally rare. Manage each athlete through measurable 4/8/12-week development blocks, technical focus, workload and objectives, then review rating, readiness, skill, fatigue and bout gains in a saved block report. Personality, satisfaction, loyalty and academy promises create retention pressure and possible departures. Automatic cards are checked every four weeks, while every healthy prospect receives a safely matched full-engine amateur bout after an individual six-week cooldown. Competition progresses from local to international level with opponent quality, strength of schedule, entry costs, two-bout tournaments and amateur titles. Pros can graduate from age 16 (16–17 requires confirmation) to the MMA main roster, a 12-month developmental deal, an open player combat-sport division, or a regional feeder while the parent retains matching rights; an active right can be exercised from Academy Alumni with a canonical signing payment. Prospect decisions, bouts, transitions and alumni follow durable IDs so duplicate display names remain independent. Tournament entry, graduation and matching-right signing are transactional: if a late simulation, story or finance step fails, the game restores the affected money, records, rosters and prospect state instead of leaving a half-completed action.
- The Scouting target board and assignment centre use durable fighter and staff identities, preserve
  completed intelligence while an upgrade or fight observation is pending, and keep old dossiers
  visibly stale instead of refreshing them on load. Regional searches retain their ranked lead list
  and open the headline fighter directly. Filters and action controls reflow for laptop-width windows,
  while assignment history provides vertical and horizontal scrolling. Selecting a target now surfaces
  identity/division, intel freshness, scout advice and market context in a compact read-only card strip;
  clearing the selection clears those cards without revealing hidden ratings or commissioning a report.
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
  opponent's current stance. Authored sequences can branch after a recorded defensive attempt or position
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
  Expansion registration checks validate the final assembled move definitions, including reviewed
  successor-only Phase 31 layers, while continuing to lock every other authored technique field.
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
  The next expansion follows [the Fight Move System Plan](FIGHT_MOVE_SYSTEM_PLAN.md).
  Before restructuring, `tools/move_registry_parity.py --verify-legacy analysis/move_registry_parity.json`
  checks all expanded definition fields, original ordering and the complete legal-lookup key space
  against revision `4a73923`. The isolated runner includes this check and negative regressions for
  reordered definitions, changed fields, target semantics and corrupted reference data.
  The technique registry now lives in the `fight_moves/` package, with separate striking, clinch,
  wrestling, submission, escape and signature catalogues. Immutable lookup tables replace a full
  catalogue scan on every exchange; authoring validation rejects unknown tags and removed legacy IDs.
  [The move schema guide](FIGHT_MOVE_SCHEMA.md) documents every field and the punch, kick,
  takedown, submission and recovery helpers. The isolated runner also checks 300 complete fights
  against `analysis/move_coverage_reference.json`, rejecting new eligibility gaps or reductions in
  existing pool/style depth. Sample absence is reported separately from proof of impossibility.
  Phase 29 expands the catalogue to 216 moves, including 25 top submissions: eight are legal from
  guard and nine from half guard. A 300-fight gate requires all 16 additions to appear and no single
  top submission to exceed 25% of selections. The original registry snapshot stays immutable;
  `analysis/move_registry_phase29.json` separately captures the reviewed expanded definitions.
  The following batch brings the registry to 249 moves and 40 defenses. Every ground position has
  at least four recovery identities, every referenced defensive family has two named answers, and
  the 300-fight gate checks all 33 additions plus fewer than ten uses of any identical rendered
  defense clause. Slice 5 adds 53 standing/clinch moves, and Slice 6 adds 44 wrestling/ground moves,
  bringing the active total to 346. Exact structural parity uses `analysis/move_registry_followup_continuity.json`.
  Phase 31 explicitly updates 125 original follow-up lists; 163 of the original 200 moves now
  have successors. The checksum-bound `analysis/move_followup_phase31_revised_manifest.json` records
  the only permitted differences from the immutable Slice 6 snapshot.
  Defensive reachability probes respect incoming weapon/target restrictions, including punch-only
  shoulder rolls and body-only blocks. Knees and elbows cannot receive a shoulder-roll defense
  merely because they share a broad power-punch action with boxing techniques.
  The coverage report also records distinct moves per fighter, top-ten selection share and chained
  selection share. New domain batches may be tested as drafts before registration; a draft file
  alone does not mean its techniques are active in fights.
  `analysis/compare_striking_move_expansion.py` tests the 53-move standing/clinch expansion against
  the frozen 249-move content snapshot in 300 paired bouts, requiring all additions to appear,
  increased variety and unchanged mechanical evidence without writing to any career.
  Referee inactivity resets cannot trigger trait or camp praise for a fighter-created response.
  The wrestling/ground expansion is checked against actual resolver landings: successful
  shots and takedowns use guard/half guard, with cage continuations for near-successful entries.
  All 18 styles now meet the 18-technique floor while retaining their exclusive combination and
  finisher. `analysis/compare_ground_move_expansion.py` verifies the 44 additions in paired bouts.
  Follow-ups are also checked as an immutable directed graph: missing targets or cycles fail at
  import. Graph depth reports possible successor edges, not a claim about a sequence completed in a fight.
  Live sequence traces separately record occurrence identity and actual depth. Legal alternatives
  can continue a chain when the next action differs from the preferred branch, with the same
  two-tick/round boundary and no extra mechanics roll. Referee resets never seed a fighter chain.
  Ownership checks also cover turtle, front-headlock and leg-entanglement roles.
  The coverage report exposes interrupted starts as well as completed sequences; use
  `--require-phase31` to enforce the development targets, including a median of two across
  all attempted chains in fights reaching round two. That full phase is not yet signed off.
  `tools/benchmark_move_selector.py` profiles 44 complete bouts over three repeats with an
  in-memory 800-move catalogue and verifies registry/RNG restoration. Its `--check` option enforces
  the fixed 15% selector-time target. The optimized implementation measured 14.06% median
  in the three-sample 800-move diagnostic, down from 27.99%; the canonical runner enforces the ceiling.
  Selection-level regression uses `tools/move_selection_parity.py --verify analysis/move_selection_followup_continuity.json`:
  it protects full ordered traces and chosen payloads across 44 complete fights, not just results.
  The selection regression also reconstructs the prior frozen content in memory and verifies the
  original 44-fight refactor evidence, so new follow-up authoring does not discard that protection.
  The selector now separates candidate filtering, static and contextual scores, authored rarity,
  weighted choice and payload construction into six focused engine helpers.
  Catalogue files have an automated 400-line ceiling to keep future move expansions reviewable.
  Static fighter/move scores are cached only for the current bout; dynamic stance, plan, reads
  and chain context is refreshed for every selection. Fighter development between bouts remains visible.
  Move schema 2 adds a default-false retirement flag. Retired IDs stay available to old signatures,
  mastery and replay labels but cannot enter active move pools or be newly learned in camps.
  All current moves remain active; the explicit schema migration permits no other definition changes.
  Thirty action-diverse follow-up lists now connect jabs, clinch entries/exits and top-ground work
  to different legal next actions. The paired 300-fight gate reports 15.53% chained selections
  versus 12.03% before, with identical broad mechanics. This does not yet meet the attempted-chain
  median target. `analysis/compare_followup_diversity.py` preserves that paired evidence gate.
  A second 30-root layer adds clinch, top-control, passing and bottom-recovery alternatives,
  reaching 17.51% chained selections and 19.64% concentration in the leading top submission.
  The paired gate now compares this latest layer against the immutable first-diversity snapshot.
  `analysis/generate_chain_opportunity_report.py` explains interrupted roots and timely next-action
  opportunities. Its optimistic three-action ceiling applies only to the observed root cohort;
  it is diagnostic evidence, not a replacement acceptance target or an impossibility proof.
  A tighter diagnostic computes the best union of three existing techniques with legal positions,
  roles and targets, counting each opportunity once rather than summing overlapping candidates.
  It also keeps each root identity separate, showing its current successors, candidate IDs,
  action-family coverage and observed position/target contexts. A reviewed three-root successor
  trial improved the 300-fight display to 21.25% chained selections and 26.21% top-ten share, but
  full calibration fell to 2,243 finishes / 595 KO / 680 TKO. Its one-two-only ablation also failed
  at 2,246 / 579 / 697. Both maps were removed; normal and candidate fights retain the prior graph.
  Completion cohorts now expose root position/outcome, actor streak, post-exchange gas and declared
  action breadth. On the current 4,615-root candidate sample, no single honest commitment signal
  exceeds 41% completion. Conjunctions that cross 50% retain at most 25.08% of completed roots,
  which would sacrifice the separate 15% chained-selection target. Extreme action/cadence probes
  can manufacture median two, but push chain share above 31% and worsen concentration; none are
  integrated. A representative turtle-hammerfist probe was likewise removed: it produced two
  ordinary uses but displaced another rare specialist and changed candidate KO 586 to 585.
  Specialist attacks and escapes count as activity for referee decisions; stationary rides and
  holds still risk stand-ups. `fight_ground_activity_regression_test.py` covers both ownership directions.
  The phased move, combination and skill expansion is specified in
  [`FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`](../FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md); its first slice
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
- Curated real-fighter profiles with deterministic ratings, real fighting styles, career-appropriate traits, and one-time migration for older saves; see [`docs/REAL_FIGHTER_RATING_AUDIT.md`](REAL_FIGHTER_RATING_AUDIT.md).
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
  [`analysis/PLAYER_FINANCE_BALANCE_REPORT.md`](../analysis/PLAYER_FINANCE_BALANCE_REPORT.md).
- Finance separates weekly cashflow from long-term planning. History & Outlook shows annual profit,
  a 12-month ticket/broadcast/sponsor/merchandise revenue mix, monthly roster and top-ten purse
  exposure, and cash/event milestone projections with explicit popularity, stability and safety
  blockers. Strategic Investments provides milestone-gated facilities, international operations,
  staff departments and prestige projects with visible capital, upkeep and permanent effects;
  purchases and monthly operations appear in the same canonical ledger as ordinary company spending.
  The landing page also surfaces read-only cards for cash on hand, recurring monthly commitments,
  expected media-plus-active-sponsor income per event, and booked purse/medical exposure; these
  reuse the canonical ledger and clearly distinguish estimates from committed exposure.
- World regions with cities, local popularity, economy, drug-testing accuracy, venues, and promotional benefits. Canada's selectable event and generated-fighter locations include the Ontario cities of Belleville and Kingston, and authored Canadian free agent Brett Akey starts from Belleville.
- The Regions screen pairs its complete profile with quick-read cards for market, regulation, testing accuracy and local MMA interest, including current local promotion, gym and booked-show counts.
- Gym system with quality, facilities, reputation, morale, specialties, capacity, scouting, camp development, and a gym viewer.
- Fighter development, aging, retirement, unretirement flow, morale, injuries, fatigue, weight cuts, traits, rivalries, and media callouts. Promotions do not renew declared retirees at contract expiry; retirement-pending free agents can receive ordinary showcase bouts, while a two-year queue of at least ten pairable veterans creates a popularity-ordered independent retirement card. Cards stay within gender/weight classes, carry at most 12 bouts, and are capped at two in one week even under a severe backlog.
- Staff management with a Roster & Market view and an Expiring Contracts tab: hire candidates, negotiate salary and term, renew deals, fire staff with severance, and inspect a plain-language explanation of all seven staff roles. Staff skill and morale affect scouting, medical recovery and costs, marketing, matchmaking, testing, broadcast production, and fighter negotiations; the fighter Contracts tab provides the parallel fighter renewal workflow.
- Drug Testing has a durable, read-only compliance case ledger with provider/policy planning quotes, recorded sample and spend summaries, a five-stage case timeline, searchable evidence and a direct Staff Testing Cases route. Preliminary alerts are clearly separated from confirmed violations; confirmation, appeals, sanctions and provider-specific live outcomes remain disabled until their approved policy tables are implemented.
- Contracts keeps its full filterable MMA and combat-sports ledgers while a selected-fighter brief surfaces rank/champion status, purse, term/expiry, morale and recorded obligations before the player chooses a renewal action.
- Rules Help is available from the Tools navigation. Search stable, authored topics for ranking scopes, title eligibility, availability/camps, staff contribution, campaign costs, obligations, finance vocabulary, and Fight Night preparation. Each result explains the decision and links back to the relevant screen; incomplete or legacy data is labelled rather than filled from hidden rankings or regenerated formulas.
- Fighter Comparison labels the as-of date and legitimate visible cohort. Scouting-limited comparisons show a known sample and omit hidden ratings instead of inventing percentiles or presenting today's world table as historical evidence.
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
- Game & Saves keeps selection on a stable save/snapshot path identity across refreshes and folder filters, including duplicate display names in separate folders. Empty or filtered libraries explain the next safe action, and entries with unavailable metadata are labelled without changing the existing recovery-backed handlers.
- Database/world selection on the same page is path-bound as well, preventing a refresh from redirecting a load action to a similarly named universe file.
- Storyline browsing now follows saved thread IDs and retains the selected story across filters/refreshes; identity-less legacy threads are clearly non-durable and remain read-only.
- World Chronicle selection now follows stored chronicle/story identity through type filters instead of always jumping to the newest entry.
- MMA Contracts now retains the selected fighter by identity during filter/refresh rebuilds, so renewal and release actions cannot drift to a different row.
- MMA and Combat Sports Contracts now use the same Show-filter semantics for monthly expiry, final month, and Non-Exclusive rows.
- Rankings now keeps the selected company/fighter row by mode-scoped identity through refreshes, including duplicate-source safeguards.
- Matchmaking Available Fighters now retains the selected fighter by identity through filter/date refreshes and clears safely when that fighter is no longer eligible.
- Scouting assignments now retain new searches by saved assignment ID, with explicit compatibility handling for legacy searches and duplicate-ID safety.
- Profile Fight History now retains the selected archived bout through filters/layout refreshes, using durable bout identity when available and clearly non-durable legacy fallback rows otherwise.
- Media Desk refreshes are read-only for legacy finance envelopes; plan-target ID migration remains explicit at plan save/commit rather than occurring during a repaint.
- Managed campaign plans enforce a saved nonzero spending ceiling across all completed actions, including earlier weeks. Current receipts use their retained outcome cost; incomplete legacy spend evidence blocks a new paid capped-plan commit rather than treating prior spend as zero. A zero ceiling still adds no separate cap.
- Same-named event, fighter and sponsor plan targets have source-bound selector labels. Refresh/reorder keeps the same saved source selected and departure clears it. Media Rights account review attributes delivery evidence to the active contract ID, excluding a predecessor at the same outlet and visibly reporting same-outlet legacy rows that lack a contract ID.
- Rankings use explicit P4P and Division scope labels; P4P movement shows an unavailable same-scope state until an immutable P4P snapshot exists.
- Media Rights includes a read-only account review for delivery history, quota, shortfalls, strikes, renewal timing and successor contracts.
- Tournament History keeps durable editions readable when legacy draw, seed,
  entrant or stage containers are malformed, marking unavailable fields for
  review without fabricating results or mutating the archive.
- Comeback contracts record an ID-linked Company Timeline return fact before a
  retired fighter leaves the retired collection and re-enters the active roster;
  the transaction key is retry-safe and the existing contract and finance rules
  remain unchanged.
- Releasing a player-owned Combat Sports athlete records both the child-company
  departure and flagship-circuit return before saved division membership IDs are
  changed, while title vacating and all ranking/contract rules remain intact.
- Staff quarterly progression validates a saved skill baseline before consuming
  qualifying evidence, preserving malformed legacy rows for explicit repair and
  leaving the existing annual and 80-point caps unchanged.
- AI Staff employment normalises salary and contract dates at hire and
  disambiguates duplicate saved staff IDs with deterministic suffixes while
  preserving the existing affordability and role policy.
- Regional Feasibility is a defensive read-only projection: malformed retained
  invitation/snapshot values render as bounded or unavailable evidence, invalid
  scheduled rows cannot crash the review, and refresh never repairs, books,
  reserves, spends or draws RNG.
- Combat Sports Records & History likewise projects malformed circuit and
  history values safely, labels unavailable rows, and keeps title/ranking,
  finance, event and RNG state unchanged while the reader is opened or
  refreshed.
- Regions profile and next-step readers bound malformed indicators and pairing
  counts, skip invalid scheduled rows, and keep unavailable regional evidence
  visible without repairing, booking, spending or drawing RNG.
- Rankings and Combat Sports company standings bound malformed/non-finite
  roster and business values, preserving valid ordering while keeping the read
  model non-repairing and RNG-free; malformed circuit envelopes are rejected
  before field access.
- Owner Goals/Inbox readers bound malformed objective values without recording
  observations or outcomes; the completed-week worker remains the sole write
  boundary.
- Drug Testing Cases keeps malformed sample/quote values as explicit
  unavailable evidence while preserving case identity and raw rows; the reader
  never commissions tests, spends cash, applies sanctions or draws RNG.
- Regional Prospects treats malformed/non-finite saved history baselines as
  bounded display-only evidence without migrating fighters or changing feeder
  state, while valid assessments and scouting restrictions remain intact.
- Inbox readers bound malformed/non-finite dates and contract terms in display
  copies, preserving source identity and saved messages while keeping actions
  explicit.
- Event Log now distinguishes malformed retained collections from an empty
  archive, preserving complete ordered lines and read-only styling without
  running simulation or settlement work.
- Staff capability read models now expose stable safe read-action IDs alongside
  friendly labels. The Staff grid and detail view keep those IDs aligned with
  saved brief allow-lists and calendar-worker authority, while mutating actions
  remain excluded from recommendation modes.
- Staff budget, action-ceiling and brief-quote inputs fail closed for
  non-finite/overflow values, preserving the retained policy and returning a
  safe validation or zero planning result.
- Selected Combat Sports profiles fail closed on malformed world/division
  envelopes and project valid roster, title, history and finance data without
  repairing circuit state or drawing RNG.
- Finance, History & Outlook and Cash Runway readers catch overflow-sized
  legacy values and non-finite tax rates while preserving raw finance/history
  data and explicit calendar/settlement mutation boundaries.
- Game & Saves refreshes and selected-save summaries enumerate existing paths
  without creating folders or active-slot state; explicit save and migration
  actions remain the only write boundaries.
- Combat Sports overview refreshes fail closed on malformed world/division data,
  using bounded detail values and non-repairing projection without seeding
  circuit state or drawing RNG.
- Staff roster, candidate and expiry refreshes now fail closed on malformed
  employment collections, preserving raw evidence and stable action routing;
  overflow-sized Staff ledger values and non-finite roster cells render as
  bounded invalid evidence without mutating policy or work history.
- Combat Sports contract refreshes now use a non-repairing identity projection
  for legacy child-division membership, keeping duplicate athletes separated
  by fighter ID and leaving saved rosters untouched until an explicit contract
  or calendar action. Malformed containers and non-finite terms show safely.
- Historical fight-selection verification recognises development-loan return
  fields as save-only additions: exact zero defaults are omitted for frozen
  phase-31 fixtures, while populated or malformed values fail closed.
- Database-editor UI acceptance checks now bind reads and applies to saved
  fighter/company records rather than visible row positions, so sorting and
  filtering cannot retarget a field operation.
- Drug-testing case records now retain optional event identity and defensive
  event references, with explicit empty confirmation, appeal,
  provisional-restriction, sanction and final-resolution containers. The
  workflow/cases readers project those statuses and counts without repairing
  legacy evidence, commissioning tests, spending cash, applying sanctions or
  consuming RNG; confirmation and sanction mechanics remain policy-gated.
- Fight History now uses an archived opponent ID or exact name before applying
  a historical record snapshot. Missing at-the-time records display `Not
  recorded`, while unidentified legacy rows remain `-`; current roster records
  can no longer rewrite an old bout.
- Drug Testing Cases details now surface event scope/source and a compact
  lifecycle summary for confirmation, appeals, restrictions and sanctions,
  keeping preliminary alerts visibly distinct from gated future actions while
  preserving the read-only, no-RNG/no-spend contract.
- Renewal workbench quotes now fail closed on malformed or non-finite retained
  contract facts, using bounded planning values without negotiating, spending,
  changing contracts or consuming RNG. Valid identity deduplication and
  per-row partial results are unchanged.
- Company Proposal Ledger cash terms now fail closed to bounded display values
  for malformed/non-finite retained rows, preserving proposal identity and
  outcomes without repairing history, spending cash or consuming RNG.
- Storylines now fail closed for non-finite or overflow-sized retained
  importance, date and scoreboard values. The presentation projection marks
  the row **Needs review** while preserving authored beats, stable selection
  identity and the raw save; opening or filtering the reader remains
  non-mutating. Missing update dates also reject non-finite `started_month`
  fallbacks instead of allowing malformed chronology to reach the formatter.
  Profile storyline context and headless Followed Briefings apply the same
  bounded date handling without repairing retained threads.
- Media Rights dashboard, settled receipts and campaign detail also fail closed
  on overflow-sized/non-finite retained numbers, keeping those readers
  non-mutating while preserving source-bound offers, contracts and history.
  Receipt detail also bounds rights, sponsor, total and relationship amounts so
  malformed immutable settlement evidence cannot crash the reader.
- World Chronicle likewise bounds non-finite/overflow page limits and dates,
  retaining authored chronology with explicit `Date unavailable`/`Needs review`
  evidence and no archive repair during refresh.
- Profile Fight History now fails closed when the legacy amateur-history
  container is malformed. Academy month/week values use finite, overflow-safe
  bounded projection, so invalid dates remain readable without rewriting the
  saved amateur ledger or changing professional replay/history identity.
- The professional Fight History envelope is also type-checked before parsing;
  malformed legacy values render as the existing empty-history state rather
  than being sliced or iterated as text.
- The owned child-card manager now safely projects malformed scheduled-card
  data and bounds non-finite/invalid dates before sorting or formatting, while
  preserving saved event IDs, card order and explicit schedule/cancel actions.
- Storyline reader limits also catch overflow-sized values and stay within the
  authored page bound without mutating retained threads.
- The AI Staff employment ledger now fails closed on overflow-sized limits and
  malformed salary/term/skill/morale values, preserving identities and the raw
  employment/market rows without running lifecycle actions.
- Talent Relations case readers also bound malformed/non-finite review and
  history dates without repairing retained cases or changing their source-bound
  obligations and IDs.
- AI Staff employment reads also reject malformed promotion/staff/market
  collections without iterating or rewriting the retained source.
- Talent Relations case evidence and obligation collections are type-checked so
  malformed strings render as empty evidence rather than character lists.
- Direct case-detail projections use the same bounded review-date and obligation
  handling as the table reader.
- Resumable title-miss decisions reject non-finite/overflow saved miss amounts
  into the existing review state without rerolling the scale or applying title,
  fine or RNG side effects twice.
- Saved pending fine totals are bounded on resume, so malformed values cannot
  crash preparation or create an unbounded purse charge.
- Remove Belt correctly vacates interim as well as primary holders through the
  shared lineage helper while retaining explicit title-on-line evidence.
- Managed Staff Profiles also fail closed on malformed salary, story-score and
  reputation values without changing the selected employee or retained row.
- The AI Staff Ledger treats malformed affordability snapshots and non-finite
  cash, payroll and runway values as bounded read-only evidence.
- Company hub Next Step cards also fail closed on malformed roster/event
  collections and non-finite cash/stability evidence without changing the
  selected company or retained data.
- Company Hub detail tabs now project complete fighter rows before sorting or
  rendering, with an explicit unavailable-evidence notice for malformed rows.
- Selected-company read models defensively project MMA roster, finance, belt,
  staff and numeric summary envelopes before profile or hub rendering.
- Regional Prospects throughput/backlog readers fail closed on malformed
  source collections and cached counts without rewriting the monthly cache.
- Regional Prospects assessment rows now use bounded numeric projections and a
  safe promotion identity, so malformed scouting data cannot crash or mutate a
  fighter/history baseline during refresh.
- Company milestone projections now fail closed on non-finite or oversized
  finance/history values while leaving the saved reader source unchanged.
- Upcoming Cards broadcaster status now renders malformed provider/rights data
  safely instead of crashing or repairing the saved finance envelope.
- Finance history rows now display safe bounded dates even when legacy month/week
  fields are malformed, without rewriting the saved history.
- Staff tables now bound malformed skill, morale and salary values without
  changing employment or payroll data.
- Media Desk evidence readers now render bounded safe amounts for malformed
  retained receipts and campaigns without changing saved finance data.
- Media campaign-plan summaries now fail closed on malformed quote details,
  completion ledgers and revision values while keeping the saved plan read-only.
- Media receipt detail now resolves audience history by saved contract/outlet
  IDs first and only uses an explicit legacy event fallback when IDs are absent.
- Game & Saves selected-save metadata now shows `Unknown game date` for
  malformed/overflow calendar fields without repairing the retained save.
- Game & Saves refresh counts existing autosaves/backups without creating
  missing active-slot or recovery directories.
- Foundation membership history readers now fail closed on malformed paging,
  as-of and limit inputs without mutating the retained append-only history.
- Regions profile and team summaries now skip malformed legacy gym/promotion
  rows and use bounded sort/display values without rewriting world data.
- World Hub promotion and gym rows now project malformed dates, numeric fields,
  capacity and specialties safely while keeping refresh read-only.
- Fighter Search now skips malformed source rows and bounds legacy record
  summaries without changing its debounce, paging or scouting rules.
- Results archive/detail readers now show unavailable evidence for malformed
  dates or play-by-play containers without changing retained result data.
- The complete UI-data regression suite remains green at **182 tests** after
  the latest World Hub, Fighter Search and Results reader checks.
- The maintained regression runner now completes all requested isolated suites,
  including Fight Night, traits/profile/persistence, UI-data, Media, Staff,
  finance, scouting/regional, Combat Sports, identity, audio/window lifecycle,
  fight-engine calibration, full-system, database-editor and stability checks.
  The documented headless Matchmaking coordinate probe remains intentionally
  skipped; no EXE or user save was rebuilt or modified.
- Matchmaking's stacked laptop layout now reserves a scrollable 720px workspace
  and a 520px fighter explorer, keeping its filters/actions and at least four
  readable fighter rows visible while the draft card stays compact. Wide mode
  restores the normal workspace height; the full UI-data suite is green at
  **183 tests**.
- Academy showcase-card and alumni readers preserve stable saved identities and
  keep malformed retained rows visible as unavailable evidence. Replay,
  graduate-profile and matching-right actions fail closed for unavailable rows;
  the source archive remains untouched. UI-data coverage is now **184 tests**
  (217 combined Academy/profile/UI checks), smoke is green, and no EXE or user
  save was rebuilt.
- Scouting Target Board cards are now explicitly cleared when a filter or page
  change removes the previously selected fighter, so stale identity/intel/advice
  context cannot remain visible after a Tk row deletion. This is a read-only
  presentation guard; reports, shortlists and source identities are unchanged.
- Target Board advice cards use semantic theme colours for recommendation,
  monitor and pass states, so the same status remains readable in alternate
  palettes.
- Target Board legend swatches carry semantic keys and are rethemed with the
  page, keeping shortlist and stale indicators readable after a live theme
  change.
- Profile Overview meters and ordered skill bars now use finite bounded display
  projections for malformed legacy values, preserving fatigue-as-readiness,
  momentum-centred pulse semantics and scouting visibility without mutating
  fighter data.
- Profile comparison chooser rows now bind to saved fighter IDs (or
  deterministic legacy fingerprints), disambiguate duplicates, and restore or
  clear selection by source identity when search results change.
- Development evidence is projected defensively for the profile reader:
  malformed scores, drivers and chronicle rows remain visible as unavailable
  evidence without changing saved development history or the plot's recorded
  change order.
- Malformed Company & Title History rows are keyed by deterministic retained
  content fingerprints, not visible row positions, preserving safe paging and
  sorting actions.
- The legacy Academy Alumni dialog now follows the same stable saved-identity
  and unavailable-row handling as the main Academy page.
- Region Hub now uses the defensive non-repairing region reader, with bounded
  profile values and safe malformed-row handling that cannot mutate world state
  during repaint.
- Company Proposal Ledger legacy rows now use deterministic retained-content
  identities rather than visible ordinals, so refreshes cannot retarget the
  selected proposal or rewrite the append-only history.
- Storylines and World Chronicle legacy rows now use deterministic evidence
  keys instead of visible ordinals, preserving safe selection through reorder
  and keeping malformed/empty entries explicitly unavailable.
- Media settlement receipt rows now use retained-fact fingerprints when saved
  IDs are absent; opaque or stale IDs fail closed and cannot retarget a receipt
  through the visible list position.
- Legacy rows across matchmaking, booking, regional prospects, sponsor/World
  Hub, profile history, Regions and scouting packs now use deterministic
  content/type identities, preserving safe selection through reorder/filter
  refreshes without source mutation.
- Finance history/runway/scenario and Awards/title-lineage rows now follow the
  same recorded-ID or deterministic fingerprint contract for legacy evidence.
- Staff brief/work/exception readers now use saved IDs or deterministic
  retained-evidence keys, preserving selection through refresh without policy
  normalization or handler execution.
- Staff roster/candidate/contract and child-card readers now fingerprint
  ID-less retained rows, keeping selection and cancellation safe through
  refreshes without mutable-index routing.
- Scouting assignment readers now fingerprint ID-less retained searches from
  request/content evidence, including empty or opaque legacy rows, so list
  refreshes cannot retarget a search through its visible position.
- The all-time Legacy Ledger now uses source-bound fighter identities rather
  than displayed ranks for row keys, preserving safe selection through sort and
  filter refreshes without changing legacy scores or career history.
- AI Staff employment and Scouting watchlist readers now use deterministic
  retained-content identities when saved IDs are absent, preserving duplicate
  legacy rows and keeping refreshes independent of visible indexes.
- Talent Relations Staff briefs can now explicitly delegate a player-created
  contract renewal batch to Full Auto. The batch ID, quote ceiling, cash caps,
  stable fighter rows, actual costs and Foundation evidence are all retained;
  Recommendations remain read-only and the ordinary Contracts workflow is
  unchanged.
- Fighter tables now use saved fighter identities for their row keys across
  roster, contracts, matchmaking, free-agent, region and company views. Sort
  and filter refreshes cannot retarget a unique fighter; malformed duplicate
  identities receive safe deterministic suffixes.
- Rebooked title-miss bouts now carry stable fighter IDs and their original
  championship terms to an existing future card without copying the terminal
  weigh-in decision; the rescheduled card receives a fresh official weigh-in,
  and ambiguous name-only legacy rows fail closed.
- Last-Minute Replacement keeps ID-less legacy candidates visible with
  deterministic content keys and duplicate suffixes; prompt selection and
  commit no longer depend on object identity.
- Rebook requests with no suitable future card remain in a durable
  `needs_review` state with one actionable notice and quiet retries; a later
  eligible card moves the same identity-linked title terms once.
- Staff retention rows with empty or malformed legacy data now use deterministic
  opaque keys and source-object selection restoration, preventing duplicate
  unavailable rows from swapping identities after refresh or sort.
- Booking Workbench option and draft-review rows now use saved fighter/booking
  IDs or deterministic retained-content keys with duplicate suffixes; sorting
  and refreshes cannot retarget a legacy candidate or unresolved draft slot.
- Academy amateur-history rows now bind to saved bout/event identities or
  deterministic legacy fingerprints, keeping malformed evidence visible and
  preventing profile history selection from following a visible index.
- Fighter Profile and Company History window keys now use saved IDs or
  deterministic legacy identity projections rather than Python object IDs.
- The Fighter Profile Choose Columns window now uses that same durable fighter
  identity, so profile rebuilds reuse the correct managed chooser instead of
  keying it by a process-local object address.
- ID-less legacy Staff and candidate rows now receive compatibility identities
  from retained employment facts rather than their source list position, so
  reordering before load cannot swap the employee attached to a saved record.
- Legacy Owner Objectives now receive IDs from retained goal facts rather than
  list positions; duplicate objectives are suffixed deterministically, keeping
  boundary observations attached to the correct goal after reorder.
- ID-less Talent Relations cases now receive deterministic identities from
  retained fighter/source/obligation facts rather than row positions; duplicate
  legacy cases remain visible with stable suffixes and reader refreshes leave
  the raw case collection untouched.
- ID-less Followed Story subscriptions now receive deterministic identities from
  retained target and coverage facts rather than row positions; duplicate legacy
  follows stay distinct and reader refreshes remain non-mutating.
- ID-less Scouting Decision Packs now receive deterministic identities from
  retained pack and candidate facts rather than row positions; duplicate legacy
  packs stay distinct while the scouting page remains a projection reader.
- Manual compatibility testing now fails closed on malformed finance, testing
  cost or cash values before sampling, charging or creating case evidence; valid
  runs use the validated cash projection for the one explicit charge.
- Matchmaking draft move/remove actions now resolve through the selected source
  fight identity (or a unique saved booking ID), failing closed for equal
  unanchored legacy rows instead of targeting the first match.
- Media story reader navigation now follows the selected source row (or a unique
  retained story ID), keeping equal legacy headlines distinct and avoiding a
  silent jump to the first story.
- Detached Media story IDs now match their original identity field exactly, so a
  `story_id` cannot accidentally resolve a `story_key` row with the same text.
- Combat Sports running-order Remove and Move Up/Down actions now resolve by
  retained bout identity (or a unique saved bout/booking/fight ID), so equal
  legacy bout dictionaries fail closed instead of routing to the first row.
- The compatibility Academy window now routes lead/prospect actions through
  the retained source object or a unique saved `prospect_id`; duplicate or
  missing identities fail closed instead of following a Listbox position.
- Inbox-related fighter actions now resolve saved fighter IDs first and fail
  closed for ambiguous name-only legacy messages, preventing duplicate-name
  careers from receiving another fighter's context or medical decision.
- World Hub gym actions now resolve through the selected source-bound gym row;
  a name-only compatibility fallback is accepted only for one retained match,
  so duplicate gym names fail closed after refresh or sorting.
- Simulation Lab tournament selections now retain fighter identity keys across
  filter refreshes and seed/run actions; duplicate display names are no longer
  resolved through the first name match.
- Simulation Lab corner selectors now disambiguate duplicate fighter names and
  resolve profile, scouting and quick-fight actions through the retained
  fighter object rather than a name-only lookup.
- Staff department handlers now resolve target fighters by stable ID first and
  accept a name-only legacy target only when exactly one career matches;
  duplicate-name advice/review rows fail closed.
- Super-event readiness and card validation now resolve saved fighter IDs and
  fail closed for ambiguous legacy names instead of crashing or crediting the
  first same-named career.
- Matchmaking tournament review, TBA fill and title-toggle actions now resolve
  fighter IDs safely and surface an unavailable/ambiguous identity notice
  instead of raising or mutating the wrong card corner.
- Scheduled-card conflict repair and earliest-date checks now use a safe
  identity resolver; ambiguous legacy names become explicit unavailable
  scheduling feedback instead of crashing the reader.
- Scheduling, cancellation and immediate-run snapshots now preserve stable
  fighter references throughout their event projections, including legacy
  cards with duplicate display names.
  Event-atmosphere and championship-value readers use the same stable
  participant references, so missing or ambiguous legacy corners are omitted
  safely instead of being rebound to the first same-named fighter.
- Division closure, special-belt vacate/delete actions and card-editor previews
  now resolve saved fighter IDs and fail closed with an unavailable display for
  ambiguous legacy corners; future bouts and title metadata cannot be removed
  or retargeted through a duplicate display name.
- Fighter Profile's Development tab now separates the monthly outlook from
  guaranteed growth, shows a labelled score band/ceiling gap, uses one shared
  signed-driver scale and adds a compact recent-change ledger without mutating
  retained development evidence.
- Staff's long-run evidence audit now reports malformed work/brief collections
  and rows, missing operation IDs, and unsupported work statuses without
  normalising the retained ledger.
- It also flags malformed progression envelopes and credited-work lists while
  preserving the raw progression evidence for explicit repair boundaries.
- Yearly play-level audit measurements now include bounded Staff work-log,
  brief, exception and progression counts, credited-work totals and malformed
  evidence counts. This is a read-only qualification projection and leaves
  retained Staff ledgers untouched.
- The audit's hard-invariant scan now also flags duplicate Staff work or
  operation IDs, missing completed-work identities, malformed work/progression
  rows and orphaned progression credits without invoking Staff handlers.
- Yearly measurements now retain bounded Staff payroll totals for player and
  AI/child companies, plus malformed-salary counts, so long-run affordability
  evidence is visible without rewriting finance or Staff records.
- Yearly measurements now retain a bounded overdue-commitment total and
  source breakdown for explicit super-event, booking, medical, Media, Staff,
  owner-objective, fighter-career and Academy deadlines. Missing clocks or
  malformed due fields fail closed; audit reads remain non-mutating.
- Native calendar advances now retain bounded per-task timing diagnostics for
  isolated yearly audit snapshots, without affecting calendar order, RNG,
  finance or saved game state.
- Yearly audit measurements now retain free-agent availability, eligible
  challenger depth, title-vacancy duration and explicit expired-offer counts;
  malformed historical dates remain unknown instead of being inferred.
- The managed Play Audit reader now presents those supply/commitment metrics
  and the latest calendar timing summary in a labelled evidence section,
  including bounded display handling for legacy timing rows.
- Each yearly audit row is also checked for missing or inconsistent required
  evidence; findings are shown as warnings without repairing the checkpoint or
  changing the isolated world.
- Manual Testing Desk commissions now use the saved provider and sample-count
  selection, apply the deterministic provider quote, and freeze provider/quote
  evidence on each case while leaving the compatibility resolver and gated J5
  consequence rules unchanged.
- Play Audit now exposes separate player/AI/owned-child talent cohorts,
  per-company active divisions and eligible challengers, scheduled-event
  source coverage and missing/duplicate identity counts for fighters,
  promotions and events without changing the isolated world.
- Testing Desk case history distinguishes negative, preliminary-positive,
  inconclusive and invalid samples, keeping uncertain evidence reviewable
  without turning it into an injury, violation or sanction; legacy status-only
  rows retain their recorded meaning during display.
