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

