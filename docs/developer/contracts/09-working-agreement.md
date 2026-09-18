## 1. Working Agreement for Coding Agents

### Agent roles

The roles below describe responsibilities, not permanent identities. One agent may fill more
than one role on a small task.

- **Primary agent / integrator**: owns the user request end to end. It defines scope, inspects
  existing behavior, delegates bounded work where useful, resolves overlapping changes, runs the
  final verification, and reports what changed and what remains uncertain.
- **Investigator**: traces a bug or subsystem without making broad edits. It should return concrete
  evidence: relevant files and methods, reproduction conditions, likely cause, and suggested tests.
- **Implementer**: makes a focused change in explicitly owned files. It must preserve save
  compatibility and existing user changes, and should add or update the narrowest useful test.
- **Reviewer / verifier**: reviews the integrated diff rather than the intended design alone. It
  looks for regressions, stale documentation, save/load gaps, UI overflow, duplicated methods, and
  missing tests, then runs the checks appropriate to the change.

The primary agent remains responsible for the final result even when work is delegated.

### Multi-agent collaboration

Multi-agent delegation and parallel work are explicitly enabled for this project when independent
investigation, implementation, review, or testing can be performed safely.

1. Give each delegated task a narrow question, named file set, or read-only scope.
2. Avoid having two agents edit the same file at the same time. If overlap is unavoidable, name one
   integrator and have the other agent return findings instead of a competing patch.
3. Delegated agents should report evidence and assumptions, not only a conclusion.
4. The primary agent reviews the combined diff and runs the final tests after all edits settle.

Example delegation:

```text
Investigator: trace how a five-round bout chooses max_rounds; do not edit files.
Implementer: patch fight_engine.py and the focused regression in smoke_test.py.
Reviewer: inspect the final diff for missing structural commentary and run fight tests.
Primary: integrate, resolve conflicts, run the full shipping suite, and update docs.
```

### Approval policy

Do not ask for approval before ordinary, in-scope development work. Proceed autonomously with
reading, editing, testing, building, and other reversible project actions. Ask the user only when:

- essential information cannot be discovered locally;
- the choice would materially change the requested scope;
- the action affects external systems or people; or
- the action is destructive or difficult to reverse.

Preserve unrelated working-tree changes. Never delete or rewrite user saves unless explicitly
requested.

### Repository hygiene

- Inspect `git status --short` before and after work so existing edits are not mistaken for yours.
- Review untracked files before staging. Add required source, tests, documentation, and intentional
  assets; leave out saves, logs, caches, local databases, and generated build output unless the
  project explicitly tracks them.
- Stage only the files that belong to the requested change. Do not silently bundle unrelated user
  work into a commit.
- Run `git diff --check` before handoff to catch whitespace and patch artifacts.

### Mandatory change package

Every implementation update, improvement, bug fix, balance change, data change, UI change, tooling
change, or packaging change must include all of the following in the same working diff:

1. **`CHANGELOG.md`**: add a concise entry under the current release describing the observable fix,
   improvement, compatibility effect, or developer-facing change.
2. **`README.md`**: update the relevant feature, workflow, test, build, or compatibility description
   so the repository's main documentation matches the implemented behavior.
3. **`AGENTS.md`**: update the relevant architecture map, invariant, integration point, pitfall, test
   rule, or workflow guidance so a future coding agent does not reintroduce the old behavior.
4. **Tests**: add or update the narrowest useful automated regression and run the affected suite.
   A bug fix test should fail against the broken behavior and pass with the fix. An enhancement
   should cover its main path and important boundary or compatibility case.

These are required deliverables, not optional cleanup. Do not make empty timestamp/touch edits just
to satisfy the list; each document change must explain something useful about the change. If a
runtime behavior genuinely cannot be automated, add the closest stable invariant test and document
the reproducible manual verification. Documentation-only changes do not require a new game-runtime
test, but still require Markdown/link review and `git diff --check`.

### Definition of done

A meaningful code change is complete only when the primary agent has:

1. inspected the existing implementation and adjacent state flow;
2. implemented the smallest coherent fix;
3. added or updated regression coverage, or documented why only manual verification is possible;
4. run the checks appropriate to the affected subsystem;
5. reviewed the final diff for accidental or unrelated edits; and
6. made meaningful, synchronized updates to `CHANGELOG.md`, `README.md`, and `AGENTS.md`.

