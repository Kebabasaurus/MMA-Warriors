# State ownership and safe change paths

Read this map for work touching UI, shared state, scheduling, identity or saves.
It summarizes recurring contracts; consult the [detailed rules](developer/contracts/README.md)
for the specific feature and [architecture map](ARCHITECTURE.md) for code owners.
Function names below are search targets rather than fixed line references.

## Read versus write boundaries

| State / surface | Safe reader | Authorized mutation owner |
|---|---|---|
| UI tables, details, search, rankings, profiles | Defensive local projection; restore selection by source identity; scouting-safe values | Explicit action callback; ranking snapshots only at their calendar/simulation owners |
| Finance, runway, event economics, investments | Non-repairing finance projection; `selected_event_economics(repair=False)`; bounded unknown values | Booking/apply, purchase, calendar upkeep and event settlement |
| Scouting / regional prospects | `scouting_report_for(..., migrate=False)`; `regional_candidate_assessment(..., repair=False)`; no cache repair | Report assignment, sanctioned migration, simulation or explicit roster transition |
| Combat Sports circuits, history, company standings | Circuit-state projection with `repair=False`; sport and athlete identity | Explicit management, migration or simulation |
| Media offers, capacity, campaign history | Saved offer/contract IDs; `media_actions_remaining_readonly`; no pitch or RNG | Explicit commit/counter/accept, calendar renewal/capacity owner, settlement |
| Staff briefs, employment, progression, audits | Retained ledgers; expose missing evidence without invoking handlers | Explicit policy/contract actions and `process_staff_autonomy_boundary` after completed-week business |
| Story follow/snooze/cursors | `story_subscriptions_read_model`; defensive retained history | Explicit follow, acknowledge, snooze and unfollow |
| Membership, titles, proposals, testing cases | Raw retained envelopes, stable saved IDs, explicit unavailable/incomplete evidence | Sanctioned migration or real domain transition; membership is append-only |
| Matchmaking / Upcoming Cards / Owned Calendar | Display copies and original-source row maps; never repair names/order on refresh | Explicit add/move/edit/remove/cancel; normal eligibility and booking checks |
| Workbench proposals / runway scenarios | Non-binding snapshots; re-read eligibility and mark stale | Explicit confirmed commit after source revalidation; save of a plan does not apply it |
| Fight Night / replay / preparation timeline | Recorded evidence only; no future telemetry or invented preparation | Event preparation and settlement own results; archive replay uses `apply_results=False` |
| Game & Saves / database library | Existing paths and metadata only; no marker creation/default repair | Explicit save/load/copy/delete/restore/select/conversion handlers |

These are ownership boundaries, not permission to normalize every load. Repairs
must remain narrowly sanctioned/versioned; healthy sealed careers and source
database bytes must survive ordinary reads and round trips unchanged.

## Identity and retained history

`Fighter` deliberately uses `eq=False`: in-memory membership uses object identity;
durable references use `fighter_id`. `Fighter.overall` is derived, not assignable.
Names are labels. Legacy name lookup is valid only for a unique match in the
selected scope; duplicate names must fail closed.

UI row maps bind saved identity plus source scope (for example, promotion and
fighter, or sport/company and event). Duplicate source IDs get deterministic UI
suffixes. Legacy fingerprints and genuinely non-durable fallbacks must stay
explicit and must not become invented persistent identity. Restore a selection
only when that same source is still visible; otherwise clear dependent details.

For departures, call `vacate_fighter_belts` before changing fighter identity,
division, champion flags or roster membership. Record real membership transitions
through `record_membership_event` before/at the mutation boundary; loans/returns
record both parent and child sides. Never infer old joins from today's roster.
The 10,000-row membership threshold is a warning, not a truncation policy.

## Calendar and settlement

The internal calendar has four weeks per month. `advance_month()` advances one
week synchronously; the UI uses `begin_advance_sequence()` and queued callbacks
over `calendar_week_steps()`. Individual domain tasks remain synchronous.

Staff autonomy and owner-objective observations belong to the completed boundary,
after cards, settlement and monthly business. Repeated boundaries are idempotent.
Spectator fast-forward neither evaluates committed Staff briefs nor grants their
authority. An armed stop policy with an explicit stale `source_revision` is
rejected before due-card checks/job creation/Tk scheduling; missing legacy fields
remain compatible. Status readers never rewrite the policy.

`finish_event` owns the player settlement transaction and retry evidence. Stage
durable state and RNG; restore both on failure. Keep live locks, threads, audio
stop signals and audio-only entropy outside rollback copies. World AI has its own
result application inside `simulate_ai_promotion_month`; inspect both paths for
shared result semantics. Presentation and audio must not consume simulation RNG.

## Persistence checklist

A new saved field needs a default, new-game seed where appropriate, serialization,
narrow legacy projection/migration, defensive readers and a round-trip/legacy test.
Paths are anchored by `constants.py` to the application/data root, never the shell's
working directory. Grouped slots keep backups and recovery data within their slot.
Maintain atomic replacement, containment checks for external blocks, one shared
deepcopy memo during load staging and idempotent archive indexing.

Further detail: contracts [12](developer/contracts/12-state-and-control-flow.md),
[13](developer/contracts/13-persistence.md),
[02](developer/contracts/02-reader-and-presentation-rules.md),
[05](developer/contracts/05-performance-and-domain-rules.md) and
[25](developer/contracts/25-product-and-identity-rules.md). Search the last three
for the feature even when their original headings appear unrelated.
