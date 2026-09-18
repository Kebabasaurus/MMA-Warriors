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

Multi-event Grand Prix progression remains inside that same transaction. A settled
stage records one series-history row and materialises at most one uniquely identified
next event; the final stage records the champion and schedules nothing further.
Persist `grand_prix_series` and the scheduled stage together by stable series/event/
fighter IDs. A committed retry must not duplicate progression, payments or history,
and a failure after progression begins must restore both state and RNG before retry.

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

