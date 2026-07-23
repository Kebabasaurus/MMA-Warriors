# Company Milestones & Super Events — Grounded Design Document

> **Status:** Design proposal, contextualised against the current MMA Warriors codebase.
> **Source:** Rewrites the context-free GDD *"Player Company Milestones and Super Events"* so every
> idea is tied to a real system, the economy is rescaled to this game, and dead-weight ideas are cut.
> Nothing here is built yet — this is the plan.

---

## 0. How to read this document

The original GDD was written with no knowledge of MMA Warriors. It is directionally good but wrong on
two things that matter:

1. **Currency and scale.** The game runs in **US dollars**, not pounds, and at a *much* smaller scale
   than the GDD assumes (£5M–£1 billion). A healthy mid-game player promotion holds well under **$1M**
   cash; a strong event nets **$130k–$560k**; the largest bookable venue seats **14,500**. The GDD's
   thresholds are 10×–1000× too high and must be rescaled (§5).
2. **Reinvention.** The GDD proposes systems the game already has — an achievements/milestones engine,
   company history storage, event finance, legacy scoring, tournaments, retirement cards, and AI
   executives with ambition. Roughly half of this feature is *extending existing code*, not writing new
   systems (§2).

Every section below is tagged:
- **REUSE** — already exists; wire the feature into it.
- **EXTEND** — exists but needs new fields/branches.
- **BUILD** — genuinely new.
- **CUT / DEFER** — drop or postpone, with reason.

---

## 1. What the game actually is (the missing context)

| Concept | Real system today | File / symbol |
|---|---|---|
| Company money | `self.cash` (dollars) + `self.finance` ledger | `persistence.py`, `events.py` |
| Company prestige | `self.company_pop` (credibility, 0–100) | everywhere |
| Company stability | `self.company_stability` (0–100) | everywhere |
| Company legacy | `company_legacy_score` / `promo.legacy_score` (`rep*1.2 + size*0.6 + shows*2 + eras*3`) | `awards.py:324` |
| Achievements / milestones | `unlock_achievement()`, `achievement_log`, `evaluate_promotion_achievements()` | `awards.py:33,84` |
| Owner goals | metric/target/deadline/status list | `seeding.py:3488` |
| Event finance (player-only) | `calculate_event_finance()` → attendance, gate, broadcast, sponsorship, costs | `events.py:~2450` |
| Post-show prestige/stability | `pop_delta` / `stability_delta` after a show | `events.py:~2468` |
| Venues + capacity | `Local Gym 900 / Regional Arena 4200 / Casino Ballroom 7500 / National Sports Hall 14500` | `world.py:1235` |
| Tournaments ("Grand Prix") | `add_tournament_to_card()` — bracket bouts on one card | `ui.py`, `events.py` |
| Retirement / tribute cards | farewell bouts + independent retirement cards | `world.py`, `events.py` |
| Company history | `result_records`, `result_history`, `historical_records`, `record_book`, `era_history` | `awards.py`, `persistence.py` |
| World news | `record_world_story()` | `world.py:45` |
| Industry ranking / valuation proxy | `company_power_score()` + `industry_standings_rows()` (tiers Global/National/Regional/Local) | `views.py` |
| AI ambition | `promo.executive` (`archetype`, `board_mandate`, `job_security`, ambition) | `world.py`, `persistence.py` |
| Media / broadcast | media system, broadcasters, `media_outcome` | `media.py`, `events.py` |
| Regional draw | `regional_market_score()` / `regional_pull`, home connections | `world.py`, `events.py` |
| Atmosphere / fanbase | `event_atmosphere()`, fanbase window | `world.py`, `ui.py` |

**Reference economy (from a real month-17 mid-tier save):** cash ≈ $800k; gates $113k–$175k; profits
$130k–$560k; attendance 1,800–2,600 of a 4,200 seat arena; regional pull ×1.65. Endgame-wealthy players
plausibly reach a few million; AI majors sit around **$5M–$50M** (the power-score cash term saturates at
~$50M). **These are the anchors for every dollar figure in this document.**

---

## 2. Core architecture — three layers on existing rails

The GDD's own conclusion (§18) is correct and maps cleanly onto our code:

1. **Company Milestone** *(EXTEND `achievements`)* — a permanent, earned status. This is the existing
   promotion-achievement system with richer, multi-condition unlock rules and a progress view.
2. **Super-Event Opportunity** *(BUILD)* — a rare, expiring invitation gated behind a milestone. New
   lightweight object living in the inbox/news pipeline.
3. **Super-Event Project** *(EXTEND the event flow)* — approval → card build → budget → incidents →
   result. This is `schedule_event` + `calculate_event_finance` + a new event-week incident pass,
   with the result written to the existing history stores.

Reaching a money threshold *unlocks the milestone*; the milestone *unlocks the chance of an
opportunity*; the opportunity is a *project the player still has to execute*. Money is necessary, never
sufficient — exactly the GDD's intent, and easy to enforce because prestige/stability/roster already
exist as separate gates.

---

## 3. Milestones — EXTEND the achievements engine

Do **not** build a parallel milestone system. The `achievement_log` + `unlock_achievement()` already
persists (scope, target, company, id, title, description, year/month). Add:

- A **milestone registry** (a data table, config-driven per the GDD's "configurable values" note): each
  entry = `{id, name, cash_threshold, sustained_months, extra_conditions[], unlocks[]}`.
- A monthly **milestone check** hooked into the existing month tick (alongside `process_retirements`,
  `refresh_promotion_rankings`, and the standings snapshot I added). It evaluates conditions and calls
  `unlock_achievement("Promotion", company, company, milestone_id, name, desc)` once.
- Milestones are **permanent** once earned (achievements never un-earn). Spending an *unlock* still
  requires live cash + stability at spend time — enforced by the opportunity/project layer, not the
  milestone.

> Note: the achievement **"Established Promotion"** already exists (10 recorded events, `awards.py:91`).
> Reconcile names — either rename the GDD's £10M tier or keep the event-count achievement and give the
> money tier a distinct name (e.g. *"Established Operation"*).

---

## 4. Milestone requirements — REUSE existing signals, BUILD two

The GDD's requirement lists map almost entirely onto existing fields:

| GDD requirement | Backing signal today | Tag |
|---|---|---|
| Minimum company balance | `self.cash` | REUSE |
| Positive finances over N months | monthly `finance` ledger / profit history | REUSE (needs a rolling flag) |
| Minimum prestige | `company_pop` | REUSE |
| Financial stability | `company_stability` | REUSE |
| Roster depth / weight-class coverage | roster by `WEIGHTS`, division rank maps | REUSE |
| Recognised champions | `self.belts` holders | REUSE |
| At least one major star | `fighter.popularity ≥ 55` / star_quality | REUSE |
| Event history / successful large events | `result_records`, `historical_records` | REUSE |
| Years in operation | `self.month` vs company start month | REUSE |
| No unpaid contracts / overdue costs / debt | finance ledger, `cash < 0` checks | REUSE |
| **Safety / welfare / cancellation record** | injuries + medical exist, but no aggregate | **BUILD** (§6.3) |
| **Commission / scandal standing** | drug-testing rule exists; no scandal metric | **BUILD** (§6.3) |

So milestone gating is ~80% wiring existing values, plus one new derived **Company Safety & Standing**
score (§6.3).

---

## 5. Rescaled milestone tiers (dollars, this economy)

The GDD's eight £ tiers are collapsed to **five** and rescaled to the real economy. Treat every number
as a **starting point for playtesting**, exposed through `engine_settings` so it can scale with a future
economy/difficulty multiplier (the GDD's "configurable" requirement).

| Tier | Cash (proposed) | Sustained | Extra gate | Primary unlock |
|---|---|---|---|---|
| **Financially Secure** | **$1M** | 6 mo positive | stability ≥ 45 | Company development projects (§8) |
| **National Power** | **$5M** | 12 mo | strong national popularity (`company_pop` high + regional draw) | Stadium (mega-venue) events |
| **Major Organisation** | **$15M** | 12 mo | successful large-event history + ≥1 champion | Historic-venue opportunities |
| **Combat Sports Institution** | **$40M** | 12 mo | high safety & standing (§6.3) | Ceremonial / landmark events |
| **Legacy Empire** | **$100M** | 24 mo | multiple stars + long history | Once-per-save spectacles (White House, §9) |

Rationale: $1M is already ~50 strong events of banked profit — a real achievement at this economy.
$100M is deliberately at the edge of what the systems even represent (power-score cash saturates at
~$50M), making *Legacy Empire* a genuine end-of-save trophy. If playtesting shows players never clear
$5M, the whole table divides down cleanly.

**CUT:** the 8-tier granularity and the £-scale table. **DEFER:** "Worldwide Icon / Industry Leader /
Government-backed" as distinct tiers — fold their unlocks into the five above.

---

## 6. New systems to build

### 6.1 Mega-venue tier — BUILD
Today the venue ceiling is 14,500 (`world.py:1235`). Add a **stadium/mega class** (e.g.
`National Stadium 55,000`, `Mega Stadium 90,000`, plus one-off historic/ceremonial venues) with:
- much higher **fixed setup cost** (temporary construction, security) folded into `calculate_event_finance`;
- an **attendance-risk** relationship — a half-empty stadium tanks atmosphere/stability (the atmosphere
  and post-show `stability_delta` code already punish low `attendance_ratio`, so this mostly falls out
  for free once capacity is large);
- **novelty decay** for repeats (§6.5).

Extend the existing `venue_capacity` dict + the venue combobox; gate the big classes behind milestones
so they don't appear in the normal booking screen.

### 6.2 Company valuation — REUSE, don't build
The GDD repeatedly wants a "company valuation." **Do not add a new field.** `company_power_score()`
(built for Industry Standings) already blends cash, reputation, stability, roster strength, star power,
champions, and depth into one number. Surface *that* as "Company Valuation / Standing" and reuse it for
readiness (§10) and milestone flavor. One concept, one source of truth.

### 6.3 Company Safety & Standing score — BUILD (small)
The one genuinely missing signal. Derive a 0–100 rolling score from data that **already exists**:
- injury/serious-injury rate on the player roster, medical spend adequacy (`finance` medical line);
- event cancellation rate (cancelled vs scheduled events);
- drug-testing rule strictness (`rules["drug_testing"]`);
- a lightweight **scandal flag** (new, boolean/short-lived) set by future misconduct events.

Store as `self.company_safety` (default 60, save-safe). Used as a milestone gate and a readiness input.
This is the smallest new subsystem and unlocks the "excellent safety record" gating the ceremonial
tiers demand.

### 6.4 Super-event opportunity object — BUILD
A small dict persisted in a new `self.super_event_offers` list (default `[]`):
`{id, kind, venue, earliest_month, deadline_month, est_cost_low, est_cost_high, requirements[], rewards[], approval_difficulty, status}`.
Generated by a monthly roll (gated by unlocked milestones) and surfaced as an **inbox item + news
story** via the existing `inbox` and `record_world_story()`. Mirrors how retirement-fight and
weight-move recommendations already arrive in the inbox.

### 6.5 Novelty / cooldown modifier — BUILD (small)
Track recent spectacles (count + months) and apply the GDD's decay (100→80→60→40%). Multiply into hype
in `fight_hype`/finance for super events only. Store `self.super_event_history` (default `[]`).

---

## 7. Super-event categories — consolidated & grounded

The GDD lists ~40 event names across 5 categories. Consolidate to **four kinds**, each mapped to systems
we have:

1. **Ceremonial / Government** *(BUILD gating, REUSE event flow)* — White House, royal palace, state
   tribute. High prestige, **capped attendance** (low gate), heavy security cost, strict approval. The
   value is prestige + `company_pop` + a permanent history entry, not profit.
2. **Historic Venue** *(EXTEND venues)* — castle, amphitheatre, former Olympic site. Reduced capacity,
   higher setup, prestige/legacy payoff. New venue entries + cooldowns.
3. **Mega-Venue / Record Attempt** *(BUILD venue tier)* — 55k–90k stadium; needs multiple title/star
   fights on the card (enforce via card requirements, §Stage 4). Breaks attendance/gate records into
   `record_book`.
4. **Special Format** *(mostly REUSE)* — one-night Grand Prix **already exists** as `add_tournament_to_card`;
   Champions-vs-Champions / Legends-vs-Prospects / anniversary / retirement supercard reuse tournaments,
   retirement cards, and title logic with tuned matchmaking. This category is the cheapest to ship.

**CUT:** the long flavor lists (Nation-vs-Nation, race-circuit, disaster-relief variants, etc.) as
*content*, not systems — add a handful, expose the rest as data later. **DEFER:** outdoor **weather**
mechanics (nice flavor, low priority) and charity/tribute economics beyond the retirement cards we
already have.

---

## 8. Company development projects — REUSE heavily, EXTEND lightly

Earlier milestones unlock permanent, purchasable projects. Many GDD projects **duplicate existing
systems** — reuse them:

| GDD project | Already exists as | Action |
|---|---|---|
| Fighter development programme / academy | **Academy** system | REUSE (maybe a milestone discount) |
| Scouting department | scouting reports / scout window | REUSE |
| Company Hall of Fame | **HoF window** (`open_hall_of_fame_window`) | REUSE |
| Medical team | staff + medical spend | REUSE / minor buff |
| Records/archive system | `record_book` / `historical_records` | REUSE (it's the Record Book) |
| Company awards ceremony | annual **awards** system | REUSE |
| Cancellation insurance / legal / forecasting | new passive modifiers | **EXTEND** (small buffs) |
| Custom company arena | **owned mega-venue** | ties to §6.1 |

Net: development projects are mostly a **staff/upgrade spend screen** that toggles buffs and unlocks the
owned-arena path — not a new content pillar.

---

## 9. Worked example — White House Fight Night (rescaled)

Once-per-save, behind **Legacy Empire**. Rescaled requirements:
- cash ≥ **$100M**, with ≥ **$40M** projected to remain after costs (post-event reserve, §12);
- `company_pop` ≥ 90; strong USA regional popularity;
- ≥ 10 years operating; excellent **safety & standing** (§6.3);
- ≥ 1 globally recognised champion; multiple prior stadium events; no active scandal; government approval.

Restrictions: capped live attendance (prestige not gate), extreme security cost, strict fighter
eligibility, full-card approval, high cancellation insurance. Formats = Ceremonial Showcase /
Championship Supercard / National Celebration / Legends Celebration (four `card_tier`-like presets).
Success → permanent history entry, one-off achievement, prestige bump, unique news/commentary. Failure →
big loss, prestige/stability hit, media criticism (the post-show deltas already model most of this).

---

## 10. Event Readiness rating — BUILD (thin UI computation)

A single 0–100 score shown on each opportunity, weighted per the GDD:
`financial 25% · prestige 20% · card quality 20% · star power 15% · safety 10% · venue relationship 10%`.
Every input already exists (`cash`, `company_pop`, card build/hype, star counts, §6.3 safety,
regional/venue relationship). Reuse the **breakdown-panel pattern** from the Industry Standings screen so
players see *why* the score moves — that panel already renders labelled component contributions.

---

## 11. Data model / save compatibility (respect the save)

All new state must default gracefully so existing saves load unchanged (this project has a hard
save-protection rule). New fields, all defaulted:

- `self.company_safety` → 60
- `self.super_event_offers` → `[]`
- `self.super_event_history` → `[]`
- `self.company_milestones` → `[]` (or reuse `achievement_log` entirely and skip this)
- optional per-project buff flags in `self.rules` (already the config bucket)

Persist alongside `standings_history` in `save_payload` / `apply_world_data`, defaulting on load — the
exact pattern used for the standings history I added.

---

## 12. Anti-exploit — REUSE the month tick

The GDD's protections map to existing mechanics:
- **Sustained balance** → the monthly milestone check tracks consecutive qualifying months (a counter on
  the milestone), so a one-frame spike doesn't qualify.
- **Post-event reserve** → enforced in the opportunity/project accept step against live `cash`.
- **Loan discount** → if/when loans exist, exclude borrowed cash from the qualifying figure.
- **Card quality gate** → reuse existing card build/hype requirements; money can't buy a weak card past
  approval.
- **Opportunity expiry / cancellation penalty / diminishing returns** → `deadline_month`, a reliability
  hit on repeated cancels (feeds §6.3), and the novelty decay (§6.5).

---

## 13. AI-controlled promotions — REUSE executives

AI promotions already have `executive` with archetype, ambition, `board_mandate`, and `job_security`.
Let ambitious/wealthy AI executives roll for their own super events, generating `record_world_story`
news and record-book entries — no new AI brain, just a hook in the existing monthly executive review.
**DEFER** until the player-side loop is proven.

---

## 14. Ideas explicitly CUT or DEFERRED (per "some ideas may be useless")

- **£ currency & £5M–£1B tiers** — CUT; rescaled to $ (§5).
- **Standalone "company valuation" field** — CUT; reuse `company_power_score` (§6.2).
- **8 milestone tiers** — CUT to 5.
- **Most development projects** — REUSE existing academy/HoF/records/awards/staff instead of new builds (§8).
- **Long event flavor lists** (Nation-vs-Nation, race circuit, many ceremonial variants) — DEFER as data/content.
- **Outdoor weather mechanics** — DEFER (flavor, low ROI).
- **"Once per company generation"** — SIMPLIFY to once-per-save (single player company per save).
- **Broad new charity/tribute economy** — DEFER; retirement/tribute cards already exist.

---

## 15. Phased roadmap

1. **Phase 1 — Milestones (mostly wiring).** Milestone registry + monthly check + progress UI on the
   existing Achievements window. Rescaled $ tiers. Ships value immediately (long-term goals) with almost
   no new subsystems.
2. **Phase 2 — Safety & Standing + Valuation surfacing.** Build `company_safety` (§6.3); surface
   `company_power_score` as valuation. Unlocks the ceremonial gates.
3. **Phase 3 — Opportunity pipeline + Readiness.** `super_event_offers`, inbox/news generation,
   readiness score, expiry/cooldown. No event execution yet — just the offer loop.
4. **Phase 4 — Super-event execution.** Mega-venue tier, approval stage, card-requirement checklist,
   preparation budget, event-week incidents, legacy result into history. Start with **Special-Format**
   (reuses tournaments) as the cheapest first shippable super event, then Mega-Venue, then Ceremonial.
5. **Phase 5 — Development projects + AI super events.** Buff/upgrade screen; AI executive hook.

---

## 16. Open decisions for the player/designer

1. **Economy scale:** are the §5 dollar thresholds roughly right, or is the target endgame wealth lower
   (divide the table by ~5)?
2. **Milestone store:** reuse `achievement_log` outright, or a dedicated `company_milestones` list with
   richer progress data?
3. **First super event to build:** recommend **one-night Grand Prix / Special-Format** first — it reuses
   `add_tournament_to_card` and proves the pipeline with minimal new code.
4. **Ceremonial scope:** ship White House only, or a small set (palace/stadium/castle) from day one?
