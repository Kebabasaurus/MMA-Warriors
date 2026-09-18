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

