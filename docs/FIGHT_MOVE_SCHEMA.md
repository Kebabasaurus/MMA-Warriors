# MMA technique authoring schema

The public API is `fight_moves`. Definitions live in `fight_moves/catalogue/`; the schema,
validation and lookup implementation are separate modules. Definitions remain Python literals.
Keep historical batches in their explicit concatenation order. Never rename or remove a move ID:
saves use those IDs for signatures, mastery and career statistics.

Follow-ups form an import-validated `MoveChainGraph`. Cycles and unresolved target IDs are errors.
The graph preserves authored successor order, uses iterative topological construction and exposes
immutable adjacency/depth maps. `chain_depth(move_id)` reports maximum possible successor edges
(a leaf has zero); it is not an observed bout length. Runtime chain occurrence/depth evidence must
be measured from actual selected exchanges when the sequencing phase is integrated.

## MoveDefinition fields

| Field | Meaning and contract |
| --- | --- |
| `move_id` | Unique permanent identifier, also used by follow-ups and saves. |
| `name` | Human-readable technique name. |
| `parent_action` | Existing broad action whose calibrated resolver owns the outcome. |
| `positions` | Frozen set of legal starting positions, drawn from `ALL_POSITIONS`. |
| `targets` | Frozen target set. Empty means any target; a targeted move requires a requested target. |
| `attack_skills` | Tuple of supported detailed ratings used for proficiency. |
| `defense_skills` | Tuple of supported detailed defensive ratings. |
| `preferred_styles` | Supported style preferences; exclusive style tags require exactly one owner. |
| `minimum_skill` | Proficiency gate from 0 through 99. |
| `energy` | Positive technique exertion metadata; no extra broad gas deduction. |
| `miss_risk` | Positive metadata affecting later named selection, not broad accuracy. |
| `counter_risk` | Positive vulnerability metadata, not another counter or finish roll. |
| `follow_ups` | Ordered stable successor IDs, each resolving in the registry. Author 1–3 for new content. |
| `tags` | Tuple from the explicit `MOVE_TAGS` vocabulary. |
| `side` | Technique side, required for kicks. |
| `range_band` | Authored range identity, required for kicks. |
| `defense_families` | Tuple from `DEFENSE_FAMILIES`, used for matching named answers. |
| `entry_family` | Empty or one of `ENTRY_FAMILIES`; required for takedowns. |
| `finish_positions` | Possible legal finish states for takedown identity; actual trace controls the result. |
| `attack_path` | Empty or one of `ATTACK_PATHS`; required for submissions. |
| `failure_outcomes` | Explicit possible submission failures; actual resolver evidence controls narration. |
| `components` | Ordered combination weapons; evidence for broad aggregate volume, never extra attacks. |
| `deprecated` | Strict boolean, default `False`. Keep the ID loadable but exclude retired moves from selection and new learning. |

`DefenseDefinition` has `defense_id`, `name`, `families`, `positions`, `skills` and `tags`.
Families and tags use the schema's `DEFENSE_FAMILIES` and `DEFENSE_TAGS`; skills and positions
must be supported. The full closed vocabularies are maintained explicitly in
[`schema.py`](../fight_moves/schema.py), rather than inferred from whatever content was just authored.
The behavioral tag constants are shared with engine selection.

## Tag contracts

- `kick`: target, side, range band and defense families are required.
- `takedown`: entry family, finish positions and defense families are required.
- `submission`: attack path and explicit failure outcomes are required.
- `finisher`: standing strike, minimum skill at least 60, energy and counter risk above 1.
- `style-combination`: exactly one owning style and at least three ordered components.
- `style-finisher`: exactly one owning style, and a strike or submission tag.

The import-time validator rejects unknown vocabulary, duplicate IDs, missing historical IDs,
unknown skill/style/position references and unresolved follow-ups. Existing finisher rarity,
counter-window and style eligibility checks still apply after validation.

## Authoring helpers

```python
from fight_moves.presets import punch

technique = punch("lead_uppercut", "lead uppercut", styles=("Boxer",), tags=("power",))
```

`punch`, `kick`, `takedown`, `submission` and `recovery` supply family defaults and accept
explicit overrides. Kick target and side, takedown entry/finish positions, and submission
position/path/failures must be supplied. Tags extend defaults without duplicates. These helpers
do not rewrite any existing definition. Add suitable follow-ups and proficiency gates before
shipping a new specialist. Retiring content requires implementing an explicit deprecation path;
deleting an ID is never an alternative.

## Coverage and verification

`unreachable_moves()` and `coverage_report()` are available through `fight_moves.validation`.
Supply engine evidence, not `ALL_POSITIONS`, as reachability input. The coverage report records
the position before selection and actual action/target combination from complete fight traces;
an intermediate position path alone cannot prove that a move can be selected there.

`analysis/move_coverage_reference.json` is the initial documented allow-list of sample eligibility
warnings and thin pools/styles. Reasons distinguish position, parent action, target, skill and
style constraints. A skill median is a representative-roster diagnostic, not a maximum attainable
rating. Likewise, absence from 300 fights does not prove that a rare specialist is impossible.
The historical 16 common-position gaps are separately asserted by name in the coverage tests.
As content phases close a gap, tighten its reference allowance; never expand allowances merely
to pass a gate. New unsupported content, reduced existing pool depth and reduced style coverage
must fail verification.

```powershell
py -3 fight_move_coverage_regression_test.py
py -3 fight_move_parity_regression_test.py
py -3 tools/move_registry_parity.py --verify-followups analysis/move_registry_followup_diversity.json --followup-manifest analysis/move_followup_continuity_manifest.json
py -3 tools/move_registry_parity.py --verify analysis/move_registry_followup_continuity.json
py -3 fight_move_selection_parity_regression_test.py
py -3 tools/move_selection_parity.py --verify analysis/move_selection_followup_continuity.json
py -3 analysis/generate_move_coverage_report.py --verify analysis/move_coverage_reference.json --output analysis/move_coverage_report.json
py -3 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
```

Structural steps require identical parity; content phases need separately reviewed expansion
evidence. Never overwrite the original registry or fight-result baselines to conceal drift.

Defense tags `body` and `punch` are eligibility constraints: a body block cannot answer a head
attack, and a shoulder roll cannot answer a kick. Other defensive tags describe family/style.
The follow-up-continuity snapshot is the current exact structural reference. Its source-bound
manifest permits only the second 30 reviewed successor lists, after the frozen diversity layer.
The parity tests retain both separate successor manifests and the strict
schema-1-to-2 migration proof between immutable historical snapshots, and the selection suite
reconstructs historical content to preserve the original 44-bout refactor proof. The original Phase 31
snapshot and manifest retain the first trial that failed submission concentration; they are not
release acceptance evidence. The revised manifest substitutes eight named positional submission
successors. All earlier snapshots remain immutable evidence, and the parity test proves original
records through Slice 6 before checking the explicit successor-only migration and then the
default-false deprecation migration. The selection verifier validates both registry bindings
before permitting only its registry digest to change; all 44 bout hashes remain protected.
