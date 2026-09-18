# Current status pointers

Navigation checked against the working tree on 18 September 2026. This page links
to authoritative records rather than copying their status or claiming a new test
pass. Refresh the linked source/ledger before using a historical measurement.

| Question | Authority |
|---|---|
| What should we work on next? | [Luna Max next-work plan](LUNA_MAX_NEXT_WORK_PLAN.md): completed finite queue, execution evidence and separately gated optional candidates; select a concrete next product outcome rather than restarting the audit |
| Runtime version? | `GAME_VERSION` in [constants.py](../constants.py); currently 3.0.10 |
| What was approved and actually delivered? | Latest implementation and policy entries in the [feature ledger](../analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md) |
| What is still held or deferred? | Explicit held decisions / D-cards in that ledger; gate closeout does not authorize every proposed feature |
| What runs in the application? | [main.py](../main.py), [architecture map](ARCHITECTURE.md), [fight_release.py](../fight_release.py) |
| Which fight acceptance policy applies? | Opening policies of contracts [07](developer/contracts/07-native-release-and-experiments.md) and [08](developer/contracts/08-finish-balance-and-experiments.md) |
| Which reports support an old release? | [Fight release checkpoint](FIGHT_RELEASE_CHECKPOINT.md) and its named source-bound artifacts; [analysis guide](../analysis/README.md) |
| What should I verify now? | [Testing map](TESTING.md), affected contract and actual changed source; recorded passes are historical |
| How is the current source delivery reproduced? | [Delivery snapshot](developer/DELIVERY_SNAPSHOT.md): hashed inputs, exclusions and isolated-copy validation |
| What changed recently? | Latest entries of [CHANGELOG.md](../CHANGELOG.md); search the relevant feature |

The current task's working-tree changes are the starting state. Do not infer a
clean baseline or completed testing from a ledger entry alone. The older July
handoff is in the [archive](archive/2026-09-18/README.md) and is not a continuation
prompt. Future handoffs should name the remaining work, exact files/symbols,
decisions and fresh verification evidence; keep history in the existing ledger.
