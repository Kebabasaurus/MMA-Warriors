# MMA Warriors AI Developer Guide

Build projects under `D:\CodexFILES`. Preserve existing user changes and careers.
This file is the small, always-read entry point. Detailed rules are in the linked
contracts; read the relevant rules before editing their subsystem.

## Find the right context

1. Use [docs/README.md](docs/README.md) to choose the task's documents.
2. Use [ARCHITECTURE.md](docs/ARCHITECTURE.md) for code ownership and entry points.
3. For state, UI, calendar or persistence work, read
   [STATE_OWNERSHIP.md](docs/STATE_OWNERSHIP.md).
4. Search the [detailed contracts](docs/developer/contracts/README.md) for the
   affected feature and symbols. Read the complete matching rule and its policy
   context; the old section titles sometimes cover several domains.
5. Select verification from [TESTING.md](docs/TESTING.md) and the matching contract.

```powershell
rg -n -C 6 'affected_symbol|feature name' docs/developer/contracts
rg -n 'def affected_symbol|class RelevantMixin' -g '*.py' -g '!analysis/**'
```

Use narrow searches and function-sized reads. Large plans, the changelog, full
player guide and analysis reports are references to consult when relevant, not
mandatory startup reading. Paths inside retained contract prose are relative to
the repository root. Follow actual Markdown links relative to their document.

## Rules for every change

- Inspect the working tree before and after work. Preserve unrelated changes;
  stage only requested work. Keep paths portable in source, scripts and tests.
- Trace both readers and writers of shared `FightEmpireApp` state. Check for
  duplicate mixin methods before adding helpers; `main.py` owns composition.
- Page open, refresh, sort, filter and selection are readers. They must not repair
  saves, seed defaults, simulate, settle, spend cash/capacity or consume RNG.
  Project malformed retained values defensively and show unavailable evidence.
  Repair belongs only to its sanctioned load/migration or explicit action owner.
- Resolve actions through saved fighter/promotion/event/booking/staff/case IDs,
  never visible positions or ambiguous names. Preserve selection only when the
  same source remains visible; use deterministic duplicate suffixes and explicit
  non-durable legacy fallbacks. Respect scouting visibility in every display.
- Preserve atomic save/load and event settlement, idempotent retries, retained
  history and RNG ordering. New save fields need defaults and compatibility tests.
  Do not alter user saves, immutable baselines or archived evidence as cleanup.
- Roster departures record membership facts and vacate titles before changing
  identity, division or ownership. Challenger merit precedes scoring; shallow
  divisions, promises and inactivity do not waive eligibility.
- Calendar tasks remain synchronous domain work. Staff and owner-objective
  workers run after the completed week's cards, settlement and business tasks.
  Spectator fast-forward never grants Staff authority. Stale armed source
  revisions fail closed before scheduling any calendar work.
- Preserve complete recorded fight transcripts; presentation consumes only
  presented evidence, and judge cards stay sealed until the official result.
- Run focused required checks; report actual evidence and environment limitations.
  Do not rebuild an EXE unless the user asks.

## Policy precedence

Current explicit user instructions control. This entry point owns documentation
workflow; [STATE_OWNERSHIP.md](docs/STATE_OWNERSHIP.md),
[ARCHITECTURE.md](docs/ARCHITECTURE.md) and [TESTING.md](docs/TESTING.md) provide current
navigation. Detailed contracts retain their original order and exceptions.
Do not treat an old experiment, failed candidate or recorded pass as a new approval
or fresh verification. Resolve any apparent conflict against its explicit later
decision and current source; do not invent a policy.

For fight mechanics, read the opening accepted-native policy in
[07](docs/developer/contracts/07-native-release-and-experiments.md) and current
finish-balance policy in
[08](docs/developer/contracts/08-finish-balance-and-experiments.md) before older
engine instructions. Normal play uses `ReleaseFightEngineMixin`; rejected trials
remain audit-only. The approved two-percentage-point headline tolerance supersedes
old identical-count balance requirements; neutral refactors still require exact
parity, and all remaining acceptance gates and immutable references still apply.

The [feature ledger](analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md)
owns approved scope and deferred decisions. G0–G5 are six gates; 63 non-deferred
cards are finer work units; the 14 D-cards remain excluded unless explicitly
approved. Later recorded approvals apply only to their named extension.

### Mandatory change package

1. Add a meaningful `CHANGELOG.md` entry for the observable change.
2. Update the relevant player/workflow documentation: `README.md` for quick-start
   or entry-point changes; `docs/PLAYER_GUIDE.md` for detailed feature behavior.
3. Update the affected developer contract/map linked from `AGENTS.md`. Edit this
   file only for a universal rule or routing change. A focused contract update
   fulfills the former requirement to append every feature detail to `AGENTS.md`.
4. Add/update and run the narrowest useful regression for changed behavior, plus
   required integration gates. Documentation-only changes need link, command,
   preservation and diff checks, without artificial game-runtime tests.

This routing policy supersedes old requirements to repeat feature prose across all
three root documents. Keep one authoritative explanation and link to it. Update
maps when ownership changes; use source symbols rather than brittle line numbers.

## Collaboration and retained evidence

Proceed with ordinary in-scope reversible work. Bounded parallel investigation,
implementation or review is permitted; assign distinct edit ownership and verify
the combined result. Ask only for missing essential decisions, scope expansion or
destructive/external actions not already authorized.

Historical reviews and handoffs live in [the archive](docs/archive/2026-09-18/README.md).
The original full guide and README are preserved there byte-for-byte; extraction
hashes and original section order are in
[context-migration.json](docs/developer/context-migration.json). Those hashes record
the migration, not a ban on intentional future contract edits. Archive moves must
retain bytes and update incoming references. See [analysis/README.md](analysis/README.md)
before moving, regenerating or discarding analysis artifacts.
