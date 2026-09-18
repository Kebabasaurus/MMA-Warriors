# Documentation index

Start with the row for your task. Read only the linked material needed for that
change, then search source by symbol. The compact maps are navigation aids; the
retained contracts and explicit policy decisions still govern implementation.

## Task routing

| Task | Start here | Detailed rules / evidence |
|---|---|---|
| Decide what to fix next / review the completed stabilization queue | [Luna Max next-work plan](LUNA_MAX_NEXT_WORK_PLAN.md) | Execution record, terminal checkpoint and separately gated optional candidates; feature ledger still governs approvals |
| Find code, trace a feature | [Architecture](ARCHITECTURE.md) | [Contract index](developer/contracts/README.md); search the feature and method name |
| UI refresh, row selection, profiles, scouting | [State ownership](STATE_OWNERSHIP.md) | Contracts 02, 05, 20, 25; [tab contrast](../TAB_ACCESSIBILITY.md) |
| Saves, migrations, databases, identity | [State ownership](STATE_OWNERSHIP.md) | Contracts 12, 13, 21; [testing](TESTING.md) |
| Calendar, Staff, finance, media, world AI | [Architecture](ARCHITECTURE.md), [state ownership](STATE_OWNERSHIP.md) | Contracts 02, 04, 05, 14, 19, 25 |
| Booking, weigh-ins, titles, tournaments | [Architecture](ARCHITECTURE.md) | Contracts 05, 12, 16, 18; approved feature ledger below |
| Fight mechanics, moves, commentary | [Current status pointers](CURRENT_STATE.md) | Contracts 07, 08, 17; [move schema](FIGHT_MOVE_SCHEMA.md); [evidence guide](../analysis/README.md) |
| Fight Night layout, playback, archive, audio | [Architecture](ARCHITECTURE.md) | Contracts 02, 12, 17, 24; [presentation guide](FIGHT_NIGHT_PRESENTATION.md) |
| Fighter traits, development, portraits | [Architecture](ARCHITECTURE.md) | Contracts 03, 06, 19; [traits](FIGHTER_TRAITS.md), [portrait specification](FIGHTER_PORTRAIT_IMPLEMENTATION_SPEC.md) |
| Choose tests, diagnose a failing gate | [Testing](TESTING.md) | [Canonical runner](../run_regression_suite.py); relevant subsystem contract |
| Reproduce or review a source delivery | [Delivery snapshot](developer/DELIVERY_SNAPSHOT.md) | Hashed manifest, exclusions and isolated-copy validation command |
| Player behavior or release workflow | [Quick start](../README.md), [player guide](PLAYER_GUIDE.md) | [Changelog](../CHANGELOG.md); search a feature instead of loading it all |
| Resume planning or review evidence | [Current status pointers](CURRENT_STATE.md) | Approved ledger / plan below; [analysis inventory](../analysis/README.md) |

The contract numbers refer to the numbered files in the
[contract index](developer/contracts/README.md). Broad legacy section titles can
contain newer rules for other domains, so also search that directory by feature.

```powershell
rg -n -C 6 'refresh_regions|Region Hub' docs/developer/contracts
rg -n 'def refresh_regions|def refresh_region_profile' views.py
```

## Plans and retained references

| Document | Purpose |
|---|---|
| [Luna Max next-work plan](LUNA_MAX_NEXT_WORK_PLAN.md) | 18 September working-tree audit, finite implementation sequence and completion evidence |
| [Game README](../README.md) | Compact player launch, test and build entry point |
| [Player guide](PLAYER_GUIDE.md) | Full feature descriptions and compatibility notes previously in the root README |
| [Changelog](../CHANGELOG.md) | Recorded changes and release notes |
| [Developer guide](../AGENTS.md) | Universal rules and required context routing |
| [Detailed developer contracts](developer/contracts/README.md) | Original full guide's rules, indexed by section; consult on demand |
| [Feature development plan](../analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md) | Approved implementation ledger, acceptance contracts and deferred decisions |
| [Feature backlog](../FEATURE_DEVELOPMENT_BACKLOG.md) | Current product priorities and delivered feature context |
| [Fight engine plan](../FIGHT_ENGINE_DEVELOPMENT_PLAN.md) | Engine design and retained balance contracts |
| [Moves and skills plan](../FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md) | Move, skill and combination development contracts |
| [Move system plan](FIGHT_MOVE_SYSTEM_PLAN.md) | Move architecture and implementation evidence |
| [Narrative plan](../NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md) | Narrative design and simulation-performance requirements |
| [Archived documents](archive/2026-09-18/README.md) | Older reviews, proposals and handoffs removed from the active document list |

The feature plan remains in its existing location because it contains deferred decisions
and links to implementation evidence. Gate closeout does not make every proposal in it
an implemented feature. Engine plans, technical specifications, trial reports, baseline
evidence, current guides and asset licences remain at their existing paths.

Archived documents are historical snapshots. Their old implementation prompts and
statements about missing features are not current instructions; use the developer guide,
current source and latest implementation ledger when continuing development.

## Keep future context small

Put a rule in its owning contract and link to it. Keep `AGENTS.md` universal, this
index task-oriented and the architecture/state/testing maps concise. Put feature
explanations in the player guide and release history in the changelog. Current
status pointers should link to the ledger, not duplicate its growing chronology.
When a contract becomes large, split at a coherent boundary and update these
routes; retain audit evidence and explicit superseding decisions together.
