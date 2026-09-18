# Historical documentation archive — 18 September 2026

The original eight documents were moved out of the active root/docs listing during documentation
cleanup. Their original bytes are preserved, including historical instructions, dates,
source references and unresolved ideas. Archiving does not claim every proposal was built
or every audit finding was resolved. Current entry points are in the
[documentation index](../../README.md).

| Archived document | Original path | Reason retained as history |
|---|---|---|
| [Comprehensive code review](COMPREHENSIVE_CODE_REVIEW.md) | `COMPREHENSIVE_CODE_REVIEW.md` | August 17 source snapshot; no incoming repository references found |
| [Weight system audit](WEIGHT_SYSTEM_AUDIT.md) | `WEIGHT_SYSTEM_AUDIT.md` | Original defect investigation; the repair is recorded in the changelog |
| [Idea log](MMA_Game_Idea_Log_2.md) | `docs/MMA_Game_Idea_Log_2.md` | Early brainstorming, including proposals that must not be mistaken for approved work |
| [Multisport design](Multi-Sport_Combat_Universe_Design_Document_v2.md) | `docs/Multi-Sport_Combat_Universe_Design_Document_v2.md` | Original conceptual design; current behaviour is described in the game README and guides |
| [Database/editor design brief](DATABASE_SPLIT_AND_EDITOR_DESIGN_BRIEF.md) | `docs/DATABASE_SPLIT_AND_EDITOR_DESIGN_BRIEF.md` | Original database-split build brief; the database and standalone editor now exist |
| [Recovery history](LOST_FEATURES_AND_MULTISPORT_GUIDE.md) | `docs/LOST_FEATURES_AND_MULTISPORT_GUIDE.md` | July recovery checklist that includes superseded lost-feature statements |
| [July handoff](CODEX_HANDOFF.md) | `docs/CODEX_HANDOFF.md` | July 31 handoff; retained as historical evidence for the feature backlog |
| [Portrait handoff prompt](FIGHTER_PORTRAIT_HANDOFF_PROMPT.md) | `docs/FIGHTER_PORTRAIT_HANDOFF_PROMPT.md` | Original instruction to replace initials portraits; current portraits are implemented |

Two additional byte-for-byte snapshots preserve the working-tree documents from
immediately before the context-routing restructure on this date:

| Snapshot | Original path | Current location of the content |
|---|---|---|
| [Full developer guide](AGENTS.before-context-routing.md) | `AGENTS.md` | [Indexed developer contracts](../../developer/contracts/README.md); root guide owns current workflow |
| [Full root README](README.before-context-routing.md) | `README.md` | [Player guide](../../PLAYER_GUIDE.md), with rebased links and the current change-policy pointer |

[The migration manifest](../../developer/context-migration.json) records snapshot
hashes and the complete ordered section extraction. These snapshots include
pre-existing uncommitted work. Restoring one over a current entry point requires
an explicit decision and comparison; it is not an automatic rollback step.
Exact-path `.gitattributes` entries disable newline normalization for these two
snapshots so their recorded byte hashes survive future Git checkouts.

Paths and commands inside these snapshots describe their original repository context.
Backtick references are retained verbatim and should be interpreted from the repository
root, with the original paths above used for archived documents. The portrait technical
design and implementation specification remain in `docs/` as reference material.

To restore a document, move it from this directory to its listed original path after
checking that the destination does not exist, then update references that point here.
No files were permanently deleted by this cleanup.
