# Crowd Audio Pack

These WAV files are edited and mastered from real crowd field recordings for MMA Warriors. They
replace the initial synthetic audition cues and contain no generated noise layers. Fight Night
loads them through `manifest.json`, rotates source-distinct variants without immediate repeats,
and uses the procedural cues only as a missing-file or playback fallback.

The pack contains 36 files across 12 trigger families. Every family has three source-distinct
variants: the accepted revised-pack sound keeps the stable base filename as Variant 1, while `_02`
and `_03` are additional recordings or independently layered reactions rather than pitch shifts.

All cues are stereo, 16-bit PCM at 44.1 kHz. `manifest.json` lists their family and variant number,
source recordings, intended
phase, trigger, loop behavior, duration, and suggested playback gain. `LICENSES.md` contains the
required Gregor Quendel attribution and documents the CC0 sources. A `loop` value marks a file as
safe to loop in a future sustained ambience channel; the current player uses one bounded pass per
trigger so ambience cannot mask commentary. Keep the calmer beds beneath commentary and reserve
the loudest reactions for knockdowns and finishes.
Short vocal reactions are deliberately tucked below the sustained arena response: the clean-strike
"ooh" uses a lower master target, and the knockdown gasp is attenuated inside the layered roar.
Runtime gain also follows the shared fighter-location model: an exact hometown appearance gets the
largest bounded lift, with smaller boosts for broader home-market, adopted-home, and training-base
connections.

Rebuild the complete pack from a folder containing the licensed source MP3s with:

```powershell
python .\tools\build_crowd_audio_pack.py <source-folder>
```

The developer-only builder requires NumPy and miniaudio. Source filenames and credits are documented
in `LICENSES.md`; no audio-download or decoding dependency is required by the game itself.
