# MMA Warriors: current audit and Luna Max implementation plan

Audited: **18 September 2026**. Target: the current **3.0.10 working tree**.
Audience: Luna with Max reasoning, or another implementation agent.

## Start here — execution handoff

**Handoff reviewed: 18 September 2026. No implementation card was completed by
this review.**
This document is ready to execute when the user asks to implement it. The report
review itself is not an implementation run and does not activate optional scope.
The later authorized execution is now complete; the live checkpoint and
`Execution records` are the authority for current status, while this paragraph
retains the original review boundary.

For a request to “implement this plan,” the default scope is **all ten cards in
the current queue**, followed by the combined verification boundary in section 5.
Complete one card at a time and continue without asking permission between cards.
If the user names a smaller range, that range controls. Optional section 6 is
outside either scope. Section 7 contains the complete launch prompt.

On first start, read sections 1, 3 and 5 once, then the active card and its required
contracts. Section 2 is supporting evidence; section 6 is not startup reading.
On resume, read the queue and the latest checkpoint below, not the whole report.

### Live execution checkpoint

Update this small block in place at each completed card and before a handoff.
Do not replace the original audit observations with current implementation claims.

```text
Run status: COMPLETE
Authorized scope: complete ten-card ready queue (user request, 18 September 2026)
Current / next card: none; select the next product outcome explicitly
Completed cards: F01, F02, F03, T01, T02, T03, G01, R02, R01, D01
Blocked cards and exact unblock condition: none
Combined verification: PASSED — 187/187 registered suites; source digest 93347fa8de3bb45fa95a3fe11f29254c2e553ffc3cfaebec5bd19d19f1e9425e
Last evidence record: full-queue-final — exit 0; four routed artifacts; final stability seeds passed
Next concrete action: stop this queue; optional section 6 requires an explicit new scope
```

## 1. Decision: what to work on next

**Fix three reproduced Media defects first. Then strengthen the specific test
and delivery gaps below. Do not restart the completed feature programme.**

The application already has a substantial management loop, accepted feature
gates and an extensive test suite. The highest-value next step is making the
existing features trustworthy, not another global review or a large folder move.

This report supplies a finite implementation queue, not permission to implement
new game rules. The current task created documentation and gathered evidence;
it did **not** fix the runtime defects, certify a release or build an executable.
When asked to implement this plan, begin with **F01** and follow section 5.

| Order | Card | Outcome | Current state |
|---|---|---|---|
| 1 | F01 | A Media plan cannot exceed its cumulative spending limit | DONE; cumulative nested costs enforced |
| 2 | F02 | Same-named Media targets remain separately selectable | DONE; source-bound display map verified |
| 3 | F03 | Media Rights review shows only the relevant contract's history | DONE; contract-scoped read model verified |
| 4 | T01 | Regression runs leave an accurate, source-bound summary | DONE; optional atomic JSON summaries verified |
| 5 | T02 | Every runnable root test is registered or explicitly classified | DONE; inventory gate and seven classifications verified |
| 6 | T03 | Four known audit outputs stop overwriting previous runs | DONE; unique run artifact routing verified |
| 7 | G01 | Grand Prix has bounded, end-to-end lifecycle regression coverage | DONE; atomic four-card/reload/retry/failure matrix passed |
| 8 | R02 | One authoritative game packaging definition is actually tested | DONE; invoked root spec is the tested authority |
| 9 | R01 | Required source and assets form a reviewable delivery snapshot | DONE; hashed manifest and external-copy validation passed |
| 10 | D01 | Old backlog wording no longer sends agents through completed audits | DONE; active routing and qualification wording reconciled |

F01 has direct cash impact. F02 can bind an action to the wrong source. F03 can
mislead a contract decision. No P0/data-loss blocker was demonstrated in this
bounded audit; this is not a claim that the whole application is defect-free.
Tooling work follows those player-facing fixes rather than delaying them.

The table is the mutable execution queue. Keep the original finding under each
card, change its state here, and append its evidence record when completed.
The numbered queue, not the order of card descriptions below, controls execution.

Dependencies: F01–F03 are independent fixes in the same module, so implement them
sequentially. T03 should reuse T01's evidence format; it can use an explicit
standalone run manifest if T01 is blocked. T02 classifies any new tests added by
earlier cards. G01 is independent of the tooling enhancements. R02 precedes R01
so the snapshot includes the final packaging definition. D01 closes the status
wording, then refresh the snapshot manifest if it includes those documents.
No ready card depends on activating an optional feature or building an EXE.

### Read only what the current card needs

1. [AGENTS.md](../AGENTS.md): universal constraints and change package.
2. This report's current card, then the relevant rows in
   [architecture](ARCHITECTURE.md), [state ownership](STATE_OWNERSHIP.md) and
   [testing](TESTING.md).
3. Search the [contract directory](developer/contracts/README.md) for the named
   feature and symbols; read the complete matching rule and its policy context.
4. Read the named functions and their immediate readers/writers. Expand only
   when a concrete dependency requires it.

This queue is an execution recommendation. It does not supersede user decisions,
developer contracts, frozen references or the approved
[feature ledger](../analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md).
Newer explicit decisions control; old experiment results are not permissions.

## 2. Current situation and evidence quality

### What is already built

| Area | Current evidence and boundary |
|---|---|
| Core management | Promotion operations, scouting, contracts, booking, finance, Media, Staff, Academy, child companies and spectator play are implemented. Use the [player guide](PLAYER_GUIDE.md) for behavior, not this audit as a replacement manual. |
| Approved feature programme | The latest ledger closes G5 for the approved bounded scope. G0–G5 are six gates; 63 non-deferred cards are finer work units. Do not treat older Stage 4 progress paragraphs as the current remaining-work count. |
| Grand Prix | The latest extension is recorded as implemented: 4/8/16 entrants, one to four cards within natural round limits, later-stage scheduling, replacements/postponement and the tournament-specific decider. G01 improves proof of the existing lifecycle; it does not reopen the feature design. |
| Testing Desk / J5 | Catalogue, quotes, frozen case evidence, read-only workflow and accepted title-decision paths are built. Full confirmation/appeal/sanction mechanics are not thereby active. |
| Long-career tooling / L0 | Isolated, source-bound audit tooling and checkpoints are accepted. A working audit tool or synthetic healthy sample is not evidence of a completed current-source 100-year qualification. |
| Routine dialogs | Backlog P1.4 is marked complete, with an intentional-dialog inventory. Reopen only for a specific regression or changed interaction, not because its old recommended sequence still says “closeout audit.” |
| Exports | Chronicle JSON/text export is already recorded as delivered. Do not propose “add Chronicle export” as a new missing feature. |
| Developer context | Compact entry-point instructions, indexed contracts, architecture/state/test maps and preserved archives are in place. Use that routing instead of repeatedly reading the full historic guides. |

The 14 deferred D-cards and any separately held extension remain outside the
ready queue unless explicitly activated. Accepted v1 features are complete for
their accepted scope even when a richer future version is described elsewhere.

### Fresh verification performed for this report

The following exact command completed with exit code **0** and
`ALL REQUESTED ISOLATED REGRESSION SUITES PASSED`:

```powershell
py -3.13 run_regression_suite.py grand_prix_regression_test.py rebooking_regression_test.py drug_testing_regression_test.py drug_testing_catalogue_regression_test.py booking_workbench_regression_test.py title_decision_resume_regression_test.py simulation_pause_policy_regression_test.py staff_management_regression_test.py media_plan_regression_test.py ui_data_regression_test.py
```

These are **ten selected suites**, not the full 179-entry canonical manifest.
The runner uses manifest order, isolates runtime data per suite and stops on a
failure. Additional in-memory probes reproduced F01–F03 using existing Media
harnesses/widget stubs; F01 and F02 were independently repeated. Careers and
executables were not used as test inputs or modified.

Passing suites did not detect these three behaviors. This is evidence for adding
the missing behavioral fixtures, not for weakening tests or declaring every
existing test inadequate. In particular, source-string assertions can verify
that an account-review surface exists without checking its aggregation result.

Not performed: the complete canonical suite, full native fight certification,
100-year qualification, packaged build/launch, or a live-window visual review.
Historical ledger pass counts remain historical. No release certification is
claimed, and no exact total of individual tests is inferred from clipped output.

Original audit handoff validation checked 80 local Markdown links across the touched
documents, the ten registered suite names in the recorded command, whitespace,
the six source/test fingerprints below and `git diff --check`. These checks
passed; they validate this documentation package, not untested gameplay.

The subsequent handoff-readiness review checked 55 local links in its three
touched documents, all five runner-command examples against the manifest, Python
fixture syntax, ten unique ordered cards, the same six source fingerprints,
code-fence/whitespace integrity and diff checks. All passed. No game suite was
rerun for that documentation-only review; the results above remain the original
audit run, not additional certification.

### Source identity and dirty-tree limitation

Git HEAD was `5dfb04f3d6d99b1416f8d3d4096c47b9058a3d4b`, but this audit was of
the **working tree**, not that commit. A full-path status inventory contained 49
tracked change entries and 593 untracked file entries before this report was
added. Counts are descriptive, not a cleanup list; directory-collapsed Git output
will count differently. Required runtime code is among the untracked files.

Selected raw-file SHA-256 fingerprints at audit time:

| File | SHA-256 |
|---|---|
| `main.py` | `47bf6a4500a72c017527b13e414a0b1ae0af1b9f8d9d7fbf8d4f62ee09d08003` |
| `media.py` | `7b6f3c835cd7def8b8f3d5cc7f0432abfdf892e67aace0c4f6013bc21d75739c` |
| `media_plan_regression_test.py` | `4bdf2abb14bf4e1af28afbb6f2a57a157d4e7c544c4f0c64b63d80977a4ba9d0` |
| `grand_prix.py` | `30106769a7c5515bca722f7637ee73a81c2fba262967163212b195d5a95727f5` |
| `grand_prix_regression_test.py` | `6762291d054916e52ecc1d76b2b17077d355f9800d3b27f0eeaf2bd463aece3b` |
| `run_regression_suite.py` | `433c7adfb87d9308bb8d5c26a34c66f37ef7a9cadafefb3cd2ced40f4110e03c` |

These fingerprints locate the observations; they are not a dependency-complete
test certificate. On changed source, check whether the named finding still
applies. If already fixed, verify its acceptance fixture and close that card;
do not recreate the bug or restart the whole audit.

## 3. Architecture Luna should preserve

### Actual application structure

`main.py::FightEmpireApp` composes sibling mixins over shared state. Its direct
base order is audio, UI, admin, seeding, Media, Staff, views, Grand Prix, events,
release fight engine, world, Foundation, booking workbench, contract batch
workbench, persistence and awards. Method-resolution order matters: search for
duplicate method names before adding a helper.

| Layer / owner | Role and useful entry points | Boundary to preserve |
|---|---|---|
| `main.py`, `models.py`, `constants.py` | App composition, models, defaults and runtime paths | Do not introduce a second composition root or hard-coded local paths. |
| `ui.py`, `views.py` | Widget construction, lazy navigation and many read models; some domain actions still live in views | Refresh is observational. Names such as “view” do not prove purity. |
| `media.py`, `staff_management.py` | Campaigns/rights and permissioned Staff work | Quotes/readers do not spend; explicit domain actions own effects and receipts. |
| `feature_foundation.py` | Stable identities, transaction receipts and membership facts | Keep action identity and retry behavior; do not assign IDs from page refresh. |
| `events.py`, `grand_prix.py` | Booking, preparation, playback packages, settlement and bracket progression | Settlement is atomic; retain series/event/fighter IDs and recorded evidence. |
| `world.py`, `awards.py` | Ordered calendar tasks, AI, finance, rosters and seasons | Staff/owner work runs after the completed boundary's cards and business. |
| `fight_release.py`, `fight_release_extensions.py`, `fight_engine.py`, `fight_moves/` | Accepted release engine and reusable fight definitions | Normal play uses `ReleaseFightEngineMixin`; archived trials are not interchangeable engines. |
| `persistence.py` | `serialize_world`, staged `apply_world_data`, atomic save/load | New fields need explicit defaults, migration ownership and compatibility tests. |
| `run_regression_suite.py`, `analysis/`, `tools/` | Isolated tests, diagnostic tools and retained evidence | Runtime isolation does not automatically isolate report-output paths. |

The existing [architecture map](ARCHITECTURE.md) is the ongoing navigation owner.
Update that map when ownership actually changes instead of expanding this audit
into another permanent parallel architecture manual.

### Desired shape of each change

Use the existing flow: **UI selection by ID → pure preview/validation → explicit
domain action → durable evidence → read-only presentation**. Save/load and
calendar entry points reuse those owners; they must not invent parallel effects.

For F01, a small pure recorded-spend reader is a reasonable extraction. For F03,
a pure contract-history selector is a reasonable extraction. Both have an actual
caller and a concrete fixture. They do not require a new framework or service
container. Search for an existing compatible helper before adding another.

At audit time `views.py` had 25,637 lines and `world.py` had 24,272; `media.py` had
3,167. This increases navigation and shared-state risk, but size alone is not a
runtime defect. Do **not** make splitting these files a prerequisite for F01–F03.

If a later card justifies a module extraction, move one coherent pure reader or
domain component, preserve public mixin entry points, trace every caller and
compare outputs/state/RNG before and after. Do not simultaneously rename saved
keys, change rules, reorder the MRO and move modules. Folder reorganization is
not currently the highest-value work; source/asset relocation needs a separate
bounded reason and import/packaging checks.

### Non-negotiable invariants

- Page open/refresh/sort/filter/selection cannot repair state, reset capacity,
  advance time, spend, settle or consume RNG.
- Actions resolve stable source IDs, not display names or row positions. Keep
  source scope and scouting visibility; missing or ambiguous targets fail closed.
- Validate before domain side effects. Preserve atomic save/load/settlement,
  retry idempotency and complete recorded fight transcripts.
- Roster departures record membership and vacate titles before identity/ownership
  changes. Eligibility rules are not waived by promises or shallow divisions.
- Calendar work stays synchronous and ordered. Spectator advancement never
  grants Staff authority; stale armed source revisions fail before scheduling.
- Preserve careers, archived evidence and immutable baselines. Do not rebuild an
  EXE, commit unrelated changes or clean the working tree merely to finish a card.

## 4. Implementation cards

Each card includes a finite exit condition. “Ready” means ready for the next
authorized implementation pass, not that its changes have already been made.
Test lists below are focused starts; add the integration gates required by
[TESTING.md](TESTING.md) and the affected contract, based on actual changed code.

### F01 — Enforce cumulative campaign spending

**Evidence:** `media.py::execute_media_campaign_plan` validates prior spend with
`receipt.get("cost", 0)`, but its own writer stores the charge at
`receipt["outcome"]["cost"]`. The second paid action therefore ignores the first.

Minimal fixture using `MediaPlanHarness` from
[media_plan_regression_test.py](../media_plan_regression_test.py), under isolated
test execution:

```python
app = MediaPlanHarness()
action = "Highlight Package"
cost = app.media_plan_quote("Prospect Exposure", "fighter-1", action, app.roster[0])["amount"]
app.create_media_campaign_plan("Prospect Exposure", "fighter-1", action_ids=[action], spend_ceiling=cost)
before = app.cash
first = app.execute_media_campaign_plan(action, app.roster[0])[0]
app.week += 1
second = app.execute_media_campaign_plan(action, app.roster[0])[0]
# Observed: first=True, second=True, ceiling=7500, before-app.cash=15000.
# Required: first=True, second=False, before-app.cash=7500.
```

**Implement:** read committed actual costs from the authoritative receipt shape;
define conservative handling for explicitly supported legacy/malformed evidence.
Do not treat an unknowable prior charge as proven zero. Keep plan ceilings
separate from Staff brief ceilings, company reserves and weekly action capacity.

Use the nested outcome charge for current receipts. Accept a legacy root-level
charge only if an actual retained writer/fixture establishes that format; if both
exist, never add the same receipt twice. Negative, non-finite or invalid amounts
must not create extra budget. With a nonzero ceiling and unknowable prior spend,
reject the new paid commit with an explanatory status rather than repairing
history. These are defensive accounting choices, not a new spending formula.

**Acceptance:** exact-boundary spend succeeds; a later-week excess is denied
before resolver/RNG/cash/capacity effects; retries do not double-count; existing
nested receipts count; zero ceiling retains its current no-extra-cap meaning;
legacy/malformed cases give bounded, documented outcomes. Preserve existing
Foundation failure-receipt semantics rather than demanding no diagnostic record.

**Verify:** extend Media plan behavioral tests; run `media_plan_regression_test.py`,
`foundation_regression_test.py`, `media_system_test.py`, and finance integration
checks. Add Staff coverage only if its call path changes. Update the owning Media
contract and player spending explanation. **Stop when these acceptance cases and
applicable gates pass; no campaign rebalance or broad finance rewrite.**

### F02 — Disambiguate Media target selection

**Evidence:** `media_plan_target_options` returns IDs with unqualified labels;
`_selected_media_plan_target_id` resolves the first row matching the visible label.
`refresh_media_plan_targets` consumes those options. The reproduced fixture was:

```python
app = MediaPlanHarness()
app.scheduled_events = [
    {"event_id": "event-1", "name": "Shared Name", "month": 5, "week": 1},
    {"event_id": "event-2", "name": "Shared Name", "month": 6, "week": 1},
]
app._media_plan_target_rows = app.media_plan_target_options("Event Promotion", migrate=False)
app.media_plan_target_choice = ChoiceStub("Shared Name")
# Both labels are "Shared Name"; selection resolves to event-1, never event-2.
```

**Implement:** source-bound presentation labels and an explicit selection map.
Use deterministic disambiguation without modifying saved names. Audit only the
same editor's supported target types, not every selector throughout the game.

**Acceptance:** duplicate event and fighter names are separately selectable;
sponsor targets retain their saved agreement identity; saving/retargeting chooses
the intended ID; reorder/refresh preserves a still-visible source; removal or
ambiguous legacy data cannot silently substitute another target. Option reads
with `migrate=False` leave finance, Foundation state and RNG unchanged.

**Verify:** extend Media plan tests for duplicate names, reorder and missing
targets; run Media plan and UI-data suites plus relevant UI/lifecycle gates.
Perform one targeted native-selector check, recording environment limitations if
it cannot run. Update contract 25's identity rule as needed. **Stop at the named
editor behaviors; do not reopen all completed identity-hardening work.**

The native check may use an isolated Tk fixture with synthetic duplicate targets;
it must exercise the real widget/handler and verify the saved selected ID. It does
not require opening a user's career. Duplicate saved IDs or an obsolete ambiguous
label must fail closed; a pretty suffix does not make corrupt identity safe.

### F03 — Scope account review to the actual rights contract

**Evidence:** `media.py::refresh_media_dashboard` filters account-review history
by `outlet_id` (or name) without `contract_id`. For outlet `outlet-a`, one failed
delivery under contract `old` and one successful delivery under contract `new`
produce `1 delivered / 2 recorded` plus the old shortfall while `new` is active.
Expected: `1 delivered / 1 recorded`, without the predecessor's shortfall.

Fixture for a behavioral regression (feed it to the real reader/dashboard):

```python
history = [
    {"contract_id": "old", "outlet_id": "outlet-a", "delivered": False,
     "event": "Old deal event", "reason": "Old shortfall"},
    {"contract_id": "new", "outlet_id": "outlet-a", "delivered": True,
     "event": "New deal event"},
]
active = {"id": "new", "contract_id": "new", "outlet_id": "outlet-a",
          "name": "Outlet A", "months": 6, "events_remaining": 4}
```

**Implement:** select contract-specific retained evidence, preferably through a
small pure helper. Contract 25 already requires saved outlet/contract IDs first.
Known contradictory contract IDs must not match merely because the outlet does.
Specify the bounded legacy fallback only where identity is missing; if the term
cannot be established, show unavailable/legacy evidence rather than certainty.

**Acceptance:** two terms at one outlet stay separate; duplicate outlet names with
different IDs stay separate; zero deliveries is truthful; malformed/legacy rows
remain bounded and unmodified; refresh changes neither finance nor RNG. Preserve
the separate terminal-contract history view and current renewal/successor rules.

**Verify:** add a behavioral dashboard or pure-helper test using the two-term
fixture, plus a wiring check. Existing
`test_media_rights_promotes_read_only_account_review` source-string checks alone
are insufficient. Run Media plan/system/UI-data and applicable finance/UI gates.
**Stop when scope and purity are proven; do not redesign rights settlement.**

### T01 — Retain useful regression-run evidence

**Evidence:** `run_regression_suite.py::main` streams output and prints one final
status. It does not persist selected/passed/failed/not-run suites, timing or source
identity. Its failure message implies temporary data survives until process exit,
although leaving the `TemporaryDirectory` block removes it immediately.

**Implement:** an optional uniquely named run summary with exact command/selection,
interpreter, source fingerprint, per-suite outcome/duration and overall exit
status. Record unexecuted suites honestly. Correct the cleanup message. Include
the relevant untracked sources in identity; Git HEAD alone is insufficient.

**Acceptance:** stub-subprocess tests cover success, failure, interruption, unknown
suite and trailing not-run suites; existing positional selection, manifest order,
isolation and exit codes remain compatible. No automatic retries or automatic
resume; no stale-source pass reuse. Document how to retain evidence without
collecting private careers or secrets.

Start in `run_regression_suite.py::{main,isolated_environment}` and
`qa_tooling_regression_test.py`; add a dedicated runner test if that keeps the
existing tooling tests focused. Store summaries under a caller-selected directory
with unique run names, not one `latest.json`. Document the new option in
`docs/TESTING.md`; until implemented, the current runner accepts suite names only.
Handle catchable interruption truthfully; do not promise a completed summary after
an uncatchable process kill. A partial/in-progress file must never look like a pass.

**Verify:** add/register a narrow runner regression or extend its existing tooling
coverage, then perform one small real selected run. **Stop when summaries are
truthful and CLI behavior is preserved; do not build a generic CI platform.**

### T02 — Close the explicit test-inventory gap

**Evidence:** the manifest has 179 unique existing script entries, but these seven
runnable root tests are outside it:

- `fighter_portrait_regression_test.py`
- `fighter_portrait_ranked_101_200_test.py`
- `portrait_authored_clone_regression_test.py`
- `portrait_custom_style_regression_test.py`
- `portrait_scalp_finish_regression_test.py`
- `portrait_tattoo_regression_test.py`
- `g0_repair_regression_test.py`

Their absence is confirmed; maintenance status and passing status were not
established here. Some assertions protect non-mutation, version and sponsor
capacity, so do not assume these files are obsolete.

**Implement:** inspect and run each with equivalent runtime isolation. Register
maintained coverage or document an explicit exclusion, owner and reason. Add a
static inventory check requiring every runnable root test to be classified.
Do not weaken assertions, quietly delete tests or classify a real failure away.

**Acceptance:** seven explicit decisions, no orphan runnable root test, and an
inventory regression that catches an added unclassified test. Update
[TESTING.md](TESTING.md). **Stop there; migrating the entire test tree is not part
of this card.** Registering or excluding a test must not erase historic evidence.

### T03 — Make four audit-output paths run-specific

**Evidence:** canonical calls to the following tools replace fixed diagnostic
JSON destinations even with isolated runtime data:

- `analysis/generate_move_coverage_report.py`
- `analysis/compare_ground_move_expansion.py`
- `analysis/compare_striking_move_expansion.py`
- `analysis/compare_bottom_move_expansion.py`

This is loss of run history, not proof that frozen reference inputs are being
overwritten. The coverage tool explicitly guards its reference path.

**Implement:** unique per-run output destinations and a small provenance manifest,
ideally attached to T01's run ID. Preserve existing named artifacts and supported
direct-command behavior. Give scripts explicit output options where needed;
change runner arguments intentionally. Follow [analysis retention](../analysis/README.md).

**Acceptance:** two runs retain distinct outputs; verification still compares
against the same frozen inputs; reference hashes stay identical; failures remain
failures; unrelated analysis files do not change. Use temporary outputs and
focused fixtures for output-routing tests. **Stop after these four paths; do not
mass-move, regenerate or discard the historical analysis directory.**

### G01 — Prove the complete Grand Prix lifecycle

**Evidence:** `grand_prix_regression_test.py` currently has five tests: field/stage
distribution, registration plus a manually constructed next stage, replacement/
postponement, preliminary-versus-confirmed failure, and decider scope. Its harness
returns the constant `event-next` for every new event ID. This suite alone does
not prove multi-stage settlement, reload and retry behavior together. Other suites
may contain partial coverage; inspect named paths once and reuse it.

**Implement:** a bounded integration fixture through the actual event settlement
and persistence owners, not a new tournament simulator. Keep fight-result inputs
deterministic so the fixture proves orchestration rather than rebalances fights.

**Acceptance matrix:**

| Scenario | Required proof |
|---|---|
| 16 entrants over four cards | Each settled stage creates exactly one next stage with unique event identity and correct advancing IDs; final champion completes the series. |
| Save/reload between stages | Series, scheduled stage and entrants retain identity; no extra card or lost progress. |
| Retry committed settlement | No duplicate schedule, champion, payment or history record. |
| Injected settlement failure | State and RNG roll back through the existing settlement owner; retry yields one committed progression. |
| Injury / confirmed failure | Eligible replacement retains slot/division/gender/title constraints; no candidate postpones the whole tournament; preliminary positives alone do not substitute entrants. |
| Ordinary tournament/bout | Existing non-Grand-Prix behavior and normal draw rules remain unchanged. |

`events.py::finish_event` already guards committed settlement and wraps
`_finish_event_unchecked`, including progression, in rollback handling. Do not
declare the inner progression helper non-idempotent without testing that real
caller. Fix only defects demonstrated by this bounded matrix.

**Verify:** Grand Prix, relevant event/title/rebooking, persistence and identity
suites; add calendar or fight gates only for those actual changes. Record one
result per matrix row. **Stop when the matrix passes; no new tournament formats,
AI frequency tuning or full century run.**

### R01 — Establish a dependency-complete delivery snapshot

**Evidence:** active imports include untracked `staff_management.py`,
`grand_prix.py`, `fight_release.py`, `feature_foundation.py`, both workbenches and
`fight_moves/`. A passing local working tree does not prove a checkout of HEAD
contains the application. Untracked does not mean unwanted.

**Implement:** an explicit proposed delivery manifest covering required local
source, assets, databases, tests, fixtures and contracts; classify generated
outputs separately. Validate local imports and selected runtime file loads,
including non-import assets. Never blanket-add, ignore or delete existing files.

**Acceptance:** manifest-resolved files can form an isolated reviewable snapshot;
all active local imports and registered scripts/fixtures resolve from it; explicit
exclusions have reasons; paths remain portable; user careers are not included.
Record unresolved ownership decisions instead of silently omitting dependencies.
**Stop at the reviewed manifest/snapshot. Commit, push, cleanup and release are
separate actions, not implied by this card.**

Deliver a machine-readable manifest plus a short reproduction command in
`docs/developer/` (new files are allowed). Each included path needs its role and
content hash; exclusions need a reason. Include required untracked dependencies
without staging them. Build a validation copy in a new uniquely named directory
under `D:\CodexFILES`, outside this repository, if needed to test the manifest.
Exclude active Saves/Logs, credentials, unrelated attachments and build/cache
outputs; include explicitly required test fixtures rather than copying all
analysis history. Do not import `main.py` merely to enumerate dependencies.
Validate the actual copied snapshot, not just imports resolving back to this
checkout. If assets or imports cannot be classified safely, record the exact
remaining dependency instead of claiming a complete snapshot. Final handoff
edits must be reflected in the manifest before it is called current.

### R02 — Align packaging configuration and its tests

**Evidence:** `Build Portable.bat` invokes PyInstaller on `main.py` and generates
a spec under `build/`. The root `MMA Warriors.spec` excludes `numpy`, `sounddevice`
and `_sounddevice_data`, while that build command supplies no equivalent
exclusions. `qa_tooling_regression_test.py` checks the root spec and selected batch
fragments without proving they describe the same actual build. Package impact
has not been demonstrated.

**Implement:** choose one authoritative game build definition and have static
checks inspect the path the canonical build actually uses. Trace dependencies
before choosing exclusions. Preserve both-executable packaging, assets and
runtime-folder backup/recovery behavior. Do not remove optional sound support
merely to make the two definitions textually similar.

**Acceptance:** entry point, assets, exclusions and outputs have one documented
authority; tooling tests exercise that authority and guard recovery requirements.
The README already accurately says full docs belong to the source checkout;
portable-doc bundling is not an additional defect to invent here.
**Stop after source/static checks. No executable build without a user request.**

This is an engineering choice, not a reason to ask for new game-design approval.
Prefer preserving the existing canonical batch build's behavior while unifying
its definition and tests. Do not silently activate the root spec's exclusions.
Record which definition became authoritative and why. Static acceptance closes
this configuration card only; packaged-runtime verification stays NOT RUN until
an executable build is separately requested.

### D01 — Reconcile stale next-work instructions once

**Evidence:** `FEATURE_DEVELOPMENT_BACKLOG.md` marks P1.4 complete but still leads
its “Recommended sequence” with P1.4 closeout. P2.2's completed label can be read
as century qualification, while the latest accepted L0 scope closes tooling and
holds the actual authorized century run separately.

**Implement:** point active sequencing to this queue; distinguish delivered audit
capability from measured qualification; preserve historical records and latest
explicit decisions. Do not overwrite accepted feature history with this report.
Use one current status block, not another growing chain of “latest” paragraphs.

**Acceptance:** README/docs routing leads to the next unfinished card; P1.4 stays
complete; L0 accepted tooling stays complete; the held century run is explicit;
Chronicle export is not scheduled again. Links, commands and diff checks pass.
**Stop after reconciliation; this is not a new product-wide audit.**

## 5. Progression protocol: finish features, avoid audit loops

### Start-of-card preflight: once

Read the current card and controlling rules. Inspect `git status`, identify
existing overlapping changes, locate named owners, and establish the smallest
failing fixture or missing acceptance case. If the source has changed since this
report, revalidate only the affected finding. Do not re-read all plans or run the
entire suite just to decide where to begin.

At the first preflight, record the starting dirty-file inventory and retain
before-edit content/diffs for files you touch. Existing modifications are not a
failure and do not require a clean checkout. Never reset or stash the whole tree
to establish a baseline. If another task changes an overlapping file while you
work, reconcile only that overlap; stop for direction if it cannot be preserved.

### Verification recipe

Run from the repository root. `py -3.13` was verified for the audit; use a working
configured Python if that launcher is unavailable and record the interpreter.
Do not invoke an unregistered test through the runner until it is registered.
Never import/run game harnesses against active career data to save setup time.

These commands are concrete starting gates, not new claims of passing results:

```powershell
# F01: accounting, transaction receipts and finance integration
py -3.13 run_regression_suite.py media_plan_regression_test.py foundation_regression_test.py media_system_test.py finance_audit_regression_test.py event_economics_regression_test.py

# F02 and F03: same Media/finance gates plus the affected UI surface
py -3.13 run_regression_suite.py media_plan_regression_test.py media_system_test.py finance_audit_regression_test.py event_economics_regression_test.py ui_data_regression_test.py window_lifecycle_regression_test.py smoke_test.py

# G01: lifecycle orchestration, identity, reload and event compatibility
py -3.13 run_regression_suite.py grand_prix_regression_test.py rebooking_regression_test.py title_decision_resume_regression_test.py last_minute_replacement_regression_test.py foundation_regression_test.py persistence_regression_test.py identity_persistence_regression_test.py smoke_test.py stability_test.py

# Existing tooling gate for T01/T02/R02; also run each new targeted runner test
py -3.13 run_regression_suite.py qa_tooling_regression_test.py
```

T02 runs its seven inspected tests under equivalent isolation before classification;
it does not assume all are suitable for registration. T03 needs output-routing
fixtures and the affected comparison/coverage checks using unique destinations,
not two destructive repetitions of old fixed-output commands. R01 verifies its
manifest/snapshot. D01 runs link, status-wording and diff checks only. If G01 changes
calendar or fight behavior, add those contracts' required checks; the command
above cannot substitute for them. Record the final selected gates once per card.

### Work one vertical slice through completion

1. Mark the card IN_PROGRESS. State its outcome and explicit non-goals.
2. Add the fixture, implement the smallest coherent fix and wire the real caller.
3. Verify the focused cases, then the required integration gates for actual changes.
4. Update the changelog, relevant player/workflow explanation and owning developer
   contract/map. Add new tests to the manifest or explicit classification.
5. Inspect the diff for unrelated changes, career/evidence writes and broken links.
6. Record acceptance evidence and mark DONE. Continue to the next READY card only
   within the user's authorized implementation scope.

Use states **READY → IN_PROGRESS → VERIFYING → DONE**. A failed acceptance case
returns to implementation on the **same card**. It does not create another audit
phase. Use BLOCKED only for a concrete missing decision, dependency or environment
requirement; record it and continue an independent ready card where authorized.

“Stop” in a card means **stop expanding that card and continue to the next one**,
not end the overall authorized run. F03 is a progress milestone, not the end of
the default full-queue handoff. Report milestones briefly while continuing work.

### Blockers and failed checks

- Fix a regression caused by the current card before calling it done. Repeat a
  failed check only after a code/environment change or a specific new hypothesis.
- A pre-existing unrelated failure is not permission for a new repair project.
  Capture its exact command, error and evidence that it predates this card where
  safely available; otherwise label attribution unknown. Do not claim a pass or
  silently exclude it. Continue independent work and report the integration gap.
- For unavailable Tk/display/dependencies, try safe existing local alternatives.
  Do not install software or rewrite tests simply to turn the check green. Leave
  required visual/integration acceptance BLOCKED if it cannot be performed.
- Ask only for an essential policy choice, destructive/external authority or an
  overlap that cannot be preserved. Record one precise question and the safe
  work still possible. If no authorized independent work remains, hand back the
  blocker; do not repeatedly re-audit it or promise unattended continuation.
- If a session ends mid-card, save the checkpoint with changed files, exact failing
  test/next command and what remains. On resume, finish that card; do not restart
  planning or count an incomplete acceptance case as DONE.

### Definition of done

A card is DONE when its listed user-visible behavior works, its acceptance cases
and required gates have actual results, failure/retry/legacy handling relevant to
the change is covered, documentation is accurate and unrelated work is preserved.
A missing required environment check remains explicitly unverified; do not mark
the card fully done by saying “should pass.” No unrelated optional feature needs
to be finished to close the card.

### Combined verification and final stop

After the authorized full queue is implemented, run the complete isolated
canonical runner **once for that final source state**, subject to the existing
contracts. Review its output destinations first: T03 addresses four known paths,
not every possible script. Use the isolated delivery snapshot or explicit fresh
output paths wherever the run could replace retained repository evidence. Keep
its source inputs and fixtures matched to the final working tree. Do not run
`Build Portable.bat` or a century-scale audit as part of this boundary.

Use T01's retained results, or a manual command/status log if it is blocked. A
fail-fast run leaves later suites NOT RUN, not passed. Diagnose a failure once;
fix caused defects within their card and rerun affected checks. Then execute
unattempted required suites explicitly. Previously passed results count only if
their source/dependencies are unchanged; otherwise rerun them. This is deliberate
verification accounting, not automatic retry/resume or a waiver of contract gates.

Full-queue success means all ten cards DONE, current snapshot metadata, all
required final checks accounted for and passed, and no unexplained career or
retained-evidence changes. If that cannot be reached, report completed cards,
remaining BLOCKED cards, exact unrun/failed checks and the next required decision.
Do not label partial work “all complete.” Once this terminal report is delivered,
stop. Optional candidates do not start automatically.

### Explicit anti-loop rules

- One bounded preflight and one closeout per card. Investigate further only for
  a failing acceptance case or a concrete newly exposed dependency.
- Do not repeatedly audit a DONE feature. Reopen it only for a reproduced
  regression, changed relevant source or a new user-approved requirement.
- Record incidental findings with trigger, owner and impact; do not add speculative
  cleanup to the active card. Fix a newly found blocker only if necessary for that
  card, otherwise queue it separately.
- A helper extraction is complete when its callers and behavior are verified.
  Do not turn it into an architectural rewrite because neighboring code is large.
- A test pass is reusable only for the source/dependencies it actually covered.
  After a localized edit, rerun affected checks, not every historic audit. Contract
  gates still apply; this rule cannot waive required verification.
- Run the full canonical suite at an authorized combined-integration/release
  boundary, or earlier if a governing contract requires it. Do not run expensive
  native/century experiments after every documentation or reader-only edit.
- After the ready queue is complete, deliver the result and request the next
  product priority. Do not manufacture another audit to keep working.

### Compact completion record

Keep one current queue at the top and append only a short evidence record per
completed card. Do not duplicate its entire description in the changelog.

```text
Card / status:
Changed files and source fingerprint:
Acceptance cases: pass / fail / not run, with exact reason
Commands and results; retained evidence path if created:
Player/workflow and developer-contract updates:
Remaining blocker or explicit none:
Next ready card:
```

Append completed-card records under `## Execution records` at the end of this
file, creating that heading on first use. Until then, the checkpoint is the sole
live state. Keep raw logs in the run's evidence destination, not pasted here.

When source changes invalidate evidence, record which checks became stale, not
“everything needs auditing again.” Keep run summaries small; retain verbose
outputs as evidence to consult only when needed.

## 6. Optional next features: decide once, then implement a bounded version

These are **not** part of the ready defect/tooling queue. Do not silently activate
them because an old plan mentions them.

### Candidate A — Full testing-case lifecycle

This is the clearest substantial next feature after stabilization, if selected
by the user. The ledger already records approved direction: player-selected
frequency; the same AI/spectator model a few times yearly; seven days to
confirmation and seven more to appeal; fighter-paid appeal; player warning or
suspension for a first confirmed offence; a longer suspension and company removal
for a repeat; explicit player decisions for booked-fight/title/result effects.
Provider curves and bounded suspension values are assigned to implementation
tuning. Do not ask the user to re-decide those recorded principles.

However, accepted built J5 scope explicitly leaves confirmation/appeal/sanction
activation as follow-on work. Obtain one clear scope activation and resolve only
genuine remaining choices against that record. Freeze the complete outcome table
before coding; do not repeatedly reopen policy during implementation.

If activated, use this progression:

1. Freeze versioned provider/policy and case-transition tables, including negative,
   invalid, inconclusive, confirmed and overturned results; declare acceptance.
2. Add prospective evidence/state and save compatibility without inventing old
   offences from injuries, nationality, traits or historical messages.
3. Implement scheduled confirmation and notices with idempotent due-work handling.
4. Implement appeals and sanctioned outcomes with separate medical/disciplinary
   restrictions and frozen paid/policy evidence.
5. Wire explicit player sporting decisions and only authorized Staff/AI actions.
6. Complete case UI/timeline/help and one end-to-end matrix spanning reload,
   retries, expiry and overturn. Close the version; defer enhancements explicitly.

### Candidate B — Concurrent rights / audience segments

Still held pending rules for shared inventory, allocation/ties, segments/effects,
bid/counter limits, affordability and settlement precedence. Fix F03 first.
Do not interpret existing offers or successor contracts as approval for multiple
simultaneous rights owners. A future implementation needs one agreed v1 contract
and a bounded acceptance matrix, not repeated speculative design audits.

### Candidate C — Century-scale qualification

This is validation work, not a missing game feature. Before starting, fix source
identity and agree seeds, duration/time budget, thresholds and output locations.
Preserve raw failures/checkpoints. A time-limited partial run is partial evidence,
not a 100-year pass. Repair a specific evidenced failure, rerun the affected
qualification as required, and stop once the agreed criteria are met. Do not
launch it automatically merely because this report exists.

### Content and export enhancements

Regional/media/Academy content and a company-history export can be considered
after the user selects a concrete player outcome. Confirm the exact missing
surface once; Chronicle export is already delivered. Content expansion is not a
reason to change finance balance, unlock deferred rules or postpone the fixes.

## 7. Handoff instruction for Luna

Full-queue launch prompt:

> Implement the complete ready queue in docs/LUNA_MAX_NEXT_WORK_PLAN.md:
> F01, F02, F03, T01, T02, T03, G01, R02, R01 and D01, in that order. Complete each
> card's acceptance tests, required integration checks and documentation before
> moving on. Continue through the queue without asking between cards; F03 is not
> a stopping point. If genuinely blocked, record the exact blocker and continue
> independent authorized cards. Maintain the live checkpoint, queue states and
> concise evidence records. Preserve existing unrelated changes, saves and
> retained evidence. Do not restart a whole-project audit, activate optional
> section 6, commit/push, clean the repository or build an EXE. Finish with the
> combined verification boundary and report completed cards, remaining blockers
> and actual checks. Stop when the queue is complete or no safe authorized work
> remains.

The report is reachable through normal documentation routing. The launch prompt
above is retained as the completed run's scope record; it is not an instruction
to repeat DONE cards. Optional section 6 or any new feature requires a separate
explicit request, and reviewing this document never starts background work.

## Execution records

### F01 / DONE

- Changed `media.py` and `media_plan_regression_test.py`; current source identity
  is recorded by the final runner summary.
- Cumulative nested receipt costs, malformed evidence and zero-ceiling behavior
  pass the Media/Foundation/finance integration gates.
- Player guidance, contract 25 and the changelog were updated. No blocker.

### F02 / DONE

- Added deterministic Media target labels and a display-to-source identity map;
  selection survives reorder and clears when its source disappears.
- Duplicate event/fighter/sponsor fixtures and a native hidden-Tk selector probe
  pass. Duplicate durable IDs fail closed outside sanctioned migration. No blocker.

### F03 / DONE

- Media Rights delivery history is contract-ID scoped; contradictory IDs are
  excluded and unscoped legacy rows are reported separately.
- Pure-selector and dashboard/purity fixtures plus the shared Media/UI gates pass.
  Player guidance, contract 25 and changelog were updated. No blocker.

### T01 / DONE

- `run_regression_suite.py` now writes optional unique atomic JSON summaries with
  selection, interpreter, source identity, duration and truthful terminal status.
- Success, fail-fast, interruption, unknown selection, collision and source-
  identity fixtures pass in `regression_runner_regression_test.py`. No blocker.

### T02 / DONE

- Seven previously omitted runnable root tests are registered; the root inventory
  gate requires every `*_test.py` to be registered or explicitly classified.
- All seven pass. Current portrait reference sheets are preserved in new dated
  directories; the 50-case main portrait suite passes. No blocker.

### T03 / DONE

- The three expansion comparisons accept explicit output paths; retained runner
  mode routes them and move coverage to a unique run artifact directory and hashes
  each artifact in the summary.
- Routing/collision and QA-tooling gates pass. Testing and analysis guidance were
  updated. No blocker.

### G01 / DONE

- `grand_prix_regression_test.py` uses unique IDs and the real
  `EventMixin.finish_event` boundary for a deterministic 16-person/four-card
  lifecycle, JSON reload, committed retry and injected state/RNG rollback.
- The nine-suite G01 command passed, including stability; smoke retained its
  documented headless Matchmaking layout skip. Contracts 12/player guidance and
  changelog were updated. No blocker.

### R02 / DONE

- Root `MMA Warriors.spec` is the game-package authority invoked by
  `Build Portable.bat`; it owns entry point, assets, output and dependency policy.
  The prior optional-module exclusions were not activated.
- Packaging QA and runner-summary gates pass. Contract 22 and the README were
  updated. Packaged-runtime verification is NOT RUN because no EXE was authorized.

### R01 / DONE

- `docs/developer/delivery-manifest.json` classifies and hashes required source,
  assets, database, tests, named fixtures, contracts and build inputs; exclusions
  have reasons and unresolved ownership decisions are empty.
- The validator checks the copied tree's hashes, import graph, registered inputs,
  package assets and syntax. An external snapshot under `D:\CodexFILES` passed
  validation plus smoke, Grand Prix and packaging QA from inside the copy.
  Final content identity remains authoritative in the manifest. No blocker.

### D01 / DONE

- `FEATURE_DEVELOPMENT_BACKLOG.md` now keeps P1.4 closed, distinguishes delivered
  P2.2/L0 tooling from a held current-source century qualification, and does not
  reschedule Chronicle export.
- README/current-status routing points to this terminal execution record and the
  explicit next-product selection boundary. Link/diff checks are part of combined
  closeout. No blocker.

### Combined verification / PASSED

- `py -3.13 run_regression_suite.py --summary-dir
  "D:\CodexFILES\MMA-Warriors-verification-20260918" --run-id
  full-queue-final` passed all 187 registered suites with exit code 0; no suite
  failed or remained unrun. Four generated analysis artifacts were routed to the
  run-specific external artifact directory.
- The summary records 344 Python source inputs with aggregate SHA-256
  `93347fa8de3bb45fa95a3fe11f29254c2e553ffc3cfaebec5bd19d19f1e9425e`.
  The native smoke run retained its documented headless Matchmaking layout skip;
  its suite passed. No EXE or century-scale audit was run.
