# Detailed developer contracts

These 25 files retain every section of the former root `AGENTS.md`, in original
order, without changing their text during extraction. They remain reference rules
for the affected subsystem. [The root guide](../../../AGENTS.md) now owns universal
workflow and routing; its documentation policy supersedes the old instruction to
append every feature change to all three root documents.

Use [task routing](../../README.md) and search here by feature or symbol. The
original early headings cover mixed domains, so do not rely on a filename alone.
Read the complete matching rule and connected exceptions before editing. Large
experiment histories need only be opened for work on those mechanics/evidence.

| File | Original section / useful search scope |
|---|---|
| [01](01-documentation-navigation.md) | Documentation navigation and archive preservation |
| [02](02-reader-and-presentation-rules.md) | Fight Night; reader purity, finance, Staff autonomy, stable identities, semantic themes, layouts |
| [03](03-fighter-traits.md) | Trait catalogue, camp progression, injury baselines, fixture compatibility |
| [04](04-spectator-controls.md) | Spectator pause/checkpoints and scouting target summaries |
| [05](05-performance-and-domain-rules.md) | Performance; membership, titles, booking, Staff, Media, owner objectives, reader and identity additions |
| [06](06-portrait-catalogue.md) | Portrait catalogue and named/ranked appearance rules |
| [07](07-native-release-and-experiments.md) | Accepted native 440 integration **first**; retained development/experiment contracts afterwards |
| [08](08-finish-balance-and-experiments.md) | Current finish tolerance **first**; retained candidate diagnostics afterwards |
| [09](09-working-agreement.md) | Retained collaboration/change-package wording; root guide controls current documentation workflow |
| [10](10-product-principles.md) | Desktop product principles and portable paths |
| [11](11-architecture-reference.md) | Earlier module/test inventory; use [current architecture](../../ARCHITECTURE.md) for actual composition |
| [12](12-state-and-control-flow.md) | Shared state, player/AI result flows, calendar and transactions |
| [13](13-persistence.md) | Save defaults, slot paths, atomic loads, serialization, career-to-database conversion |
| [14](14-world-and-promotions.md) | Finance, media, narrative, universe, ownership, child companies, world AI |
| [15](15-new-promotion-starts.md) | Custom-promotion start and draft viability |
| [16](16-matchmaking.md) | Booking and future-date availability |
| [17](17-fight-engine-and-commentary.md) | Fight mechanics, round structure, commentary and retained calibration requirements |
| [18](18-contracts-and-weigh-ins.md) | Contract terms, shared rules and weight cuts |
| [19](19-development-and-staff.md) | Gyms, fighter development, awards and Staff employment/effects |
| [20](20-ui-and-accessibility.md) | UI, managed windows, themes, tabs, responsiveness and accessibility |
| [21](21-data-quality.md) | Universe/fighter data quality and identity |
| [22](22-testing-and-shipping.md) | Detailed testing/packaging requirements; [testing map](../../TESTING.md) gives current commands |
| [23](23-change-recipes.md) | Persistent fields, promotions, result paths and UI change recipes |
| [24](24-pitfalls-and-audio.md) | Cross-cutting pitfalls, audio source/licence and lifecycle contracts |
| [25](25-product-and-identity-rules.md) | Product direction plus later selection, Staff, Media, membership and planning rules |

## Precedence and maintenance

The opening accepted-release policy in 07 supersedes older audit-only instructions
only for the accepted recipe. The opening finish policy in 08 supersedes old exact
headline counts for balance acceptance; neutral refactors still need exact parity.
Neither permits discarded acceptance failures or reuse of stale certification.
Later explicit user decisions in the [feature ledger](../../../analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md)
apply to their named scope. Historical measurements do not certify new code.

Keep new detailed rules with their owning domain and update this index if scope
changes. Prefer editing an existing rule over appending another paraphrase.
Before extracting a larger contract further, preserve its linked evidence and
explicit superseding decisions together. Source paths in retained prose/code
examples are repository-root-relative, as in the original guide.

The byte-for-byte [original snapshot](../../archive/2026-09-18/AGENTS.before-context-routing.md)
and [migration manifest](../context-migration.json) record original ranges and
hashes. These prove lossless extraction on 18 September 2026; they are historical
provenance, not current-content hashes to update after every intentional edit.
