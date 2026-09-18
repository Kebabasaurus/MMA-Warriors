## 13. Data Quality

- Avoid duplicate fighters across companies unless intentionally represented as a historical/younger
  or market snapshot. Keep each object on its own durable `fighter_id`; source markers such as
  `Legend`, `FA`, and `BAMMA` are internal seed metadata and must not be exposed as raw suffixes.
  The shared display formatter renders a compact `(D)` marker after duplicate names, including
  narrative and belt-history text. Use company, market, division, or profile context when the
  player needs to distinguish same-name snapshots. Audit the opening world for duplicate IDs and
  normalized base names before changing seeded records.
- Fighter database schema 5 requires a non-empty unique `fighter_id` on every canonical
  `all_fighters` row. New universes preserve that source ID; grouped compatibility tuples omit it.
  Renaming, editing, or moving a source record must preserve its ID, while an intentional duplicate
  must mint a fresh ID. Legacy schema-four packs receive deterministic IDs in memory without source
  rewrites until explicitly saved through the Database Editor.
- The shipped database keeps `birth_country` and `hometown` non-empty for every canonical MMA
  fighter and synchronizes those fields to compatibility tuples. Preserve authored values.
  Deterministic regional fallbacks must carry `birthplace_source: regional_fallback_v1` and must
  not be described as verified biography; verified bundled matches use
  `birthplace_source: bundled_verified_identity`.
- Rights packages presented as global or broad-reach coverage must include every current `REGIONS`
  entry. Add a shipped-database regression whenever the region model or media market list changes.
- Never create names with a `2` suffix as a collision workaround.
- Keep male and female fighters correctly gendered.
- When adding women whose names are absent from `FEMALE_FIRST_NAMES`, update `infer_gender`.
- Keep each company deep enough to fill its active divisions and champions.
- Use real fighters where requested; generated fighters are acceptable for roster depth.
- Generated data and tests should be deterministic under an explicit seed. Isolate test RNG setup
  from serialization and unrelated name generation.
- `Promotion.reputation` is a compact level label used in the World Hub, not a prose-description
  field. Keep long company copy in an explicit description/identity field so it cannot overflow the
  Level column.
- Region `teams` entries must represent teams based in that region. Prefer deriving the display
  from `Gym.region`, and validate authored overrides against the gym database.

