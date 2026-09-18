# Analysis and evidence navigation

This directory contains executable audit tools, frozen reference inputs, retained
candidate/release measurements and visual review artifacts. Filenames such as
`candidate`, `latest` or `verified` do not establish current release acceptance.
Read the controlling contract and the report's source identity before using it.

| Need | Entry points |
|---|---|
| Approved feature scope and implementation evidence | [Feature ledger](ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md) |
| Native release integration / acceptance | [Release checkpoint](../docs/FIGHT_RELEASE_CHECKPOINT.md), `verify_release_integration.py`, `validate_fight_release.py` |
| Historical fight/action references | `fight_engine_baseline.json`, `fight_engine_action_baseline.json`; corresponding `generate_*_baseline.py` verification tools |
| Registry and selection parity | `move_registry_followup_continuity.json`, `move_selection_followup_continuity.json`; [runner](../run_regression_suite.py) supplies exact flags |
| Move coverage | `move_coverage_reference.json`, `generate_move_coverage_report.py`; accepted rare-ID policy remains in developer contract 07 |
| Candidate experiments | `fight_candidate_context.py`, `evaluate_joint_fight_candidate.py`, named trial/diagnostic tools and [trial documents](../docs/README.md) |
| Portrait / UI review evidence | `portraits/`, `ui_previews/`, `ui_review_20260912/`; use the owning manifest/review before regenerating images |
| Career/play audits | `save_review_2033_20260908/`, explicit play-audit scripts and their retained reports; never substitute a user career for isolated input |

## Retention and output rules

- Frozen references, accepted certificates, raw measurements, provenance manifests
  and evidence cited by plans/tests are retained inputs. Preserve bytes, checksums
  and source identity. A changed mechanic requires fresh measurements.
- A failed candidate is useful evidence. Preserve its failure list and comparison
  arms; do not overwrite it with a passing-looking summary.
- Some tools write reports into this directory even when launched by the isolated
  regression runner. Runtime-data isolation protects careers; it does not make
  every analysis output temporary. Inspect the runner's exact arguments first.
- Existing untracked files are not automatically disposable. Search references
  before proposing a move or deletion; keep original paths in a recovery inventory
  and update consumers explicitly if a move is authorized.
- For a new discretionary experiment, choose a new output path accepted by that
  tool and record the command, source revision/hash, seed/corpus, date and limits.
  Do not overwrite an existing reference or invent an unsupported `--output` flag.

Search first instead of loading large JSON reports:

The canonical runner's optional `--summary-dir`/`--run-id` mode retains a
source-bound JSON summary. It routes the move-coverage output and the three
registered move-expansion comparison outputs to a unique sibling artifact
directory, leaving prior named diagnostics intact. Direct tool use should pass
its own `--output`; the three expansion scripts retain their historical fixed
default only for compatibility.

```powershell
rg -n 'release_native_engine_certification_v2|move_coverage_reference' docs run_regression_suite.py
rg -n 'add_argument|output|verify' analysis/validate_fight_release.py
```

No blanket ignore, cleanup, relocation or new retention policy is introduced by
this index. The [documentation map](../docs/README.md) routes to detailed contracts.
