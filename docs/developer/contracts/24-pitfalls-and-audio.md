## 16. Common Pitfalls

- Do not edit saves destructively.
- Do not remove `repair_core_promotions`; it keeps older saves viable.
- Do not put the active player company in `self.promotions` during a normal career.
- Do not make save paths current-working-directory relative.
- Do not assume `serialize_world` is currently side-effect free.
- Do not add pale hard-coded panels or theme-specific tab colors.
- Do not add a core promotion without updating repairs, data, smoke tests, and docs.
- Do not rely on `Cage Empire`; old references are backward-compatibility guards only.
- Do not add a new tab when an existing viewer or table can be extended cleanly.
- Do not use `fighter.status` as future-date availability.
- Do not flatten grouped save paths during load, move, backup, delete, snapshot, or quick save.
- Do not restore three-person custom divisions. Eight is the minimum normal target and six is the
  hard draft viability floor.
- Do not bypass `perform_weigh_in`, season tracking, or other shared mechanics for a new fight path.
- Do not trim global fight commentary in a way that can delete round structure or the official result.
- Treat `assets/crowd_audio/manifest.json` as the runtime source of cue intent for the integrated
  crowd pack. Keep audio optional, respect suggested gain, and use multiple reactions
  sparingly rather than allowing ambience to mask commentary. Preserve the source provenance and
  Gregor Quendel CC BY 4.0 credit in `assets/crowd_audio/LICENSES.md`. Rebuild mastered assets through
  `tools/build_crowd_audio_pack.py`; do not add generated noise beds or unlicensed recordings. Keep
  isolated gasp/"ooh" vocals below the sustained crowd bed so reactions accent rather than mask the
  fight commentary; the manifest's `mix_controls` records the accepted vocal-balance limits. Each of
  the 12 trigger families has three source-distinct variants. Preserve the accepted revised-pack cue
  as Variant 1 and name additions `_02`, `_03`, and so on so random playback can group files by
  `family` without breaking the stable base filename. The player must avoid immediate variant
  repeats, retain per-family cooldowns and a simultaneous-cue ceiling, and fall back procedurally if
  a manifest entry cannot be decoded. A manifest `loop` flag is required for the session-scoped
  ambience bed: `start_fight_night_audio_session()` opens one crossfaded loop across the live card,
  one-shot cues remain independently bounded, and `stop_fight_night_audio_session()` must run when
  the owning viewer closes so no sound bleeds into another screen or session. Keep the bed neutral;
  fighter-specific location gain belongs to the current bout's reactions and walkout. Audio variant
  choice and procedural fallbacks use the audio-only `SystemRandom`; never consume simulation RNG
  for sound presentation. Derive local crowd gain through
  `fighter_event_connection`: exact hometowns receive the largest bounded lift, followed by national
  home, adopted home, and training-base connections. Keep this effect presentation-only; it must not
  alter fight mechanics or create a second geographic-proximity model in `audio.py`. The live Fight
  Night viewer and Game Settings share `fight_night_audio_volume`; route both through
  `set_fight_night_audio_volume` so drag-time changes apply to the next cue, malformed legacy values
  repair safely, and saved volume remains clamped to 0-100.

