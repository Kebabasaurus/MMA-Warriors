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

