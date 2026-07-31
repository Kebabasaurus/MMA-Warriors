"""Master the MMA Warriors crowd pack from licensed field recordings.

This is a developer tool, not a runtime dependency. It requires NumPy and
miniaudio, plus the source files named in assets/crowd_audio/LICENSES.md.
"""

from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

import miniaudio
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "crowd_audio"
SAMPLE_RATE = 44_100
CLEAN_STRIKE_TARGET_RMS_DB = -20.0
CLEAN_STRIKE_PEAK_CEILING_DB = -7.0
KNOCKDOWN_GASP_LAYER_GAIN = 0.55


SOURCES = (
    {
        "id": "gregor_quendel_crowd",
        "title": "Free Crowd Cheering Sounds",
        "creator": "Gregor Quendel",
        "license": "CC BY 4.0",
        "url": "https://opengameart.org/content/free-crowd-cheering-sounds",
    },
    {
        "id": "soundbiter_crowd_cheering",
        "title": "Crowd Cheering",
        "creator": "SoundBiterSFX / VoiceBosch",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/SoundBiterSFX/sounds/730908/",
    },
    {
        "id": "howardv_crowd_booing",
        "title": "crowd booing",
        "creator": "HowardV",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/HowardV/sounds/264378/",
    },
    {
        "id": "radiocounseling_crowd_gasp",
        "title": "Crowd gasp.wav",
        "creator": "RadioCounseling",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/RadioCounseling/sounds/635110/",
    },
    {
        "id": "evdawg_cheering_applause",
        "title": "Crowd Cheering and Applause",
        "creator": "Ev-Dawg",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/Ev-Dawg/sounds/360620/",
    },
    {
        "id": "itmightgetloud_excited",
        "title": "Millerntor Stadium Crowd Reaction Excited 01",
        "creator": "itmightgetloud / Philipp Feit",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/itmightgetloud/sounds/829453/",
    },
    {
        "id": "itmightgetloud_goal",
        "title": "Millerntor Stadium Crowd Reaction Goal 01",
        "creator": "itmightgetloud / Philipp Feit",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/itmightgetloud/sounds/829455/",
    },
    {
        "id": "itmightgetloud_ambience",
        "title": "Millerntor Stadium Crowd Reaction General Ambience 01",
        "creator": "itmightgetloud / Philipp Feit",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/itmightgetloud/sounds/829454/",
    },
    {
        "id": "trp_outrage_boo",
        "title": "Crowd, large outrage then booing reaction, hockey game, 2011.wav",
        "creator": "TRP",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/TRP/sounds/577098/",
    },
    {
        "id": "dr_skitz_gasp",
        "title": "gasp.wav",
        "creator": "dr_skitz",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/dr_skitz/sounds/353924/",
    },
    {
        "id": "dr_skitz_boo",
        "title": "boo.wav",
        "creator": "dr_skitz",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/dr_skitz/sounds/353925/",
    },
    {
        "id": "sounds_exciting_cheer",
        "title": "Crowd Cheering",
        "creator": "SoundsExciting",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/SoundsExciting/sounds/365132/",
    },
    {
        "id": "bansemer_applause",
        "title": "Large crowd applause.wav",
        "creator": "Bansemer",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/Bansemer/sounds/160493/",
    },
    {
        "id": "cognito_stadium_applause",
        "title": "applause.wav",
        "creator": "cognito perceptu",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/cognito%20perceptu/sounds/57587/",
    },
    {
        "id": "d_jones_goal_reaction",
        "title": "19 Football Crowd - Reaction To Goal.flac",
        "creator": "D.jones",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/D.jones/sounds/528799/",
    },
    {
        "id": "foolboy_crowd_cheer",
        "title": "Crowd Cheer",
        "creator": "FoolBoyMedia",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/FoolBoyMedia/sounds/397434/",
    },
    {
        "id": "mrrap_disappointed_oh",
        "title": "crowd oh - disappointed.mp3",
        "creator": "mrrap4food",
        "license": "CC0 1.0",
        "url": "https://freesound.org/people/mrrap4food/sounds/619007/",
    },
)


CUES = (
    ("pre_fight_arena_murmur", "before", 10.0, True, -4,
     "Low venue bed while the next bout is being introduced.", ("gregor_quendel_crowd",)),
    ("walkout_crowd_swell", "before", 5.0, False, -2,
     "Fighter walkout, champion entrance, or hometown reveal.", ("gregor_quendel_crowd",)),
    ("opening_bell_roar", "before", 3.5, False, -3,
     "Opening bell or the final referee instruction before Round 1.",
     ("soundbiter_crowd_cheering",)),
    ("clean_strike_ooh", "during", 1.6, False, -3,
     "A clearly landed high-impact strike that does not cause a knockdown.",
     ("radiocounseling_crowd_gasp",)),
    ("knockdown_gasp_roar", "during", 3.2, False, 0,
     "A knockdown, major slam, or sudden near-finish momentum swing.",
     ("radiocounseling_crowd_gasp", "gregor_quendel_crowd")),
    ("submission_attempt_swell", "during", 4.5, False, -3,
     "A deep submission attempt; fade early when the hold is escaped.",
     ("gregor_quendel_crowd",)),
    ("inactivity_boos", "during", 4.0, False, -5,
     "Sustained inactivity, repeated stalling, or a referee warning.",
     ("howardv_crowd_booing",)),
    ("round_end_applause", "during", 4.0, False, -4,
     "The horn after an entertaining or competitive round.",
     ("evdawg_cheering_applause",)),
    ("knockout_eruption", "after", 6.0, False, 0,
     "KO, TKO, dramatic submission, or tournament-winning finish.",
     ("soundbiter_crowd_cheering", "gregor_quendel_crowd")),
    ("decision_tension_murmur", "after", 6.0, True, -7,
     "Scorecard wait or other short official-result delay.", ("gregor_quendel_crowd",)),
    ("controversial_decision_boos", "after", 6.0, False, -3,
     "A split decision, unpopular winner, or strongly disputed scorecard.",
     ("howardv_crowd_booing",)),
    ("respectful_postfight_applause", "after", 6.0, False, -4,
     "Post-fight interview, retiring fighter, or losing fighter salute.",
     ("evdawg_cheering_applause",)),
)


def decode(path: Path) -> np.ndarray:
    decoded = miniaudio.decode_file(
        str(path), output_format=miniaudio.SampleFormat.FLOAT32,
        nchannels=2, sample_rate=SAMPLE_RATE,
    )
    return np.frombuffer(decoded.samples, dtype=np.float32).reshape(-1, 2).astype(np.float64)


def find_one(source_root: Path, pattern: str) -> Path:
    matches = list(source_root.rglob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one source matching {pattern!r}; found {len(matches)}")
    return matches[0]


def cut(samples: np.ndarray, start: float, duration: float) -> np.ndarray:
    first = max(0, int(round(start * SAMPLE_RATE)))
    count = int(round(duration * SAMPLE_RATE))
    result = samples[first : first + count].copy()
    if len(result) < count:
        result = np.pad(result, ((0, count - len(result)), (0, 0)))
    return result


def loop_cut(samples: np.ndarray, start: float, duration: float, crossfade: float = 0.7) -> np.ndarray:
    count = int(round(duration * SAMPLE_RATE))
    overlap = int(round(crossfade * SAMPLE_RATE))
    source = cut(samples, start, duration + crossfade)
    result = source[:count].copy()
    blend = np.sin(np.linspace(0, math.pi / 2, overlap)) ** 2
    result[:overlap] = source[count : count + overlap] * (1 - blend[:, None]) + result[:overlap] * blend[:, None]
    return result


def loudest_cut(samples: np.ndarray, duration: float, edge_margin: float = 0.4) -> np.ndarray:
    block = max(1, int(SAMPLE_RATE * 0.1))
    mono_power = np.mean(samples * samples, axis=1)
    block_power = np.add.reduceat(mono_power, np.arange(0, len(mono_power), block))
    window_blocks = max(1, int(round(duration / 0.1)))
    energy = np.convolve(block_power, np.ones(window_blocks), mode="valid")
    margin_blocks = int(round(edge_margin / 0.1))
    if len(energy) > margin_blocks * 2:
        energy[:margin_blocks] = -1
        energy[-margin_blocks:] = -1
    start = int(np.argmax(energy)) * block / SAMPLE_RATE
    return cut(samples, start, duration)


def fade(samples: np.ndarray, attack: float, release: float) -> np.ndarray:
    result = samples.copy()
    attack_count = min(len(result), max(1, int(round(attack * SAMPLE_RATE))))
    release_count = min(len(result), max(1, int(round(release * SAMPLE_RATE))))
    result[:attack_count] *= (np.sin(np.linspace(0, math.pi / 2, attack_count)) ** 2)[:, None]
    result[-release_count:] *= (np.sin(np.linspace(math.pi / 2, 0, release_count)) ** 2)[:, None]
    return result


def clean_eq(samples: np.ndarray) -> np.ndarray:
    """Remove sub-bass handling noise and inaudible MP3-edge fizz without adding a noise layer."""
    spectrum = np.fft.rfft(samples, axis=0)
    frequencies = np.fft.rfftfreq(len(samples), 1 / SAMPLE_RATE)
    high_pass = np.clip((frequencies - 45) / 55, 0, 1)
    low_pass = np.clip((18_000 - frequencies) / 3_000, 0, 1)
    curve = (np.sin(high_pass * math.pi / 2) ** 2) * (np.sin(low_pass * math.pi / 2) ** 2)
    return np.fft.irfft(spectrum * curve[:, None], n=len(samples), axis=0)


def master(
    samples: np.ndarray,
    target_rms_db: float,
    looping: bool = False,
    peak_ceiling_db: float = -1.5,
) -> np.ndarray:
    result = clean_eq(samples - np.mean(samples, axis=0, keepdims=True))
    if not looping:
        result = fade(result, 0.025, 0.14)
    rms = float(np.sqrt(np.mean(result * result)))
    gain = (10 ** (target_rms_db / 20)) / max(rms, 1e-9)
    peak = float(np.max(np.abs(result)))
    gain = min(gain, (10 ** (peak_ceiling_db / 20)) / max(peak, 1e-9))
    return result * gain


def mix(duration: float, layers: tuple[tuple[np.ndarray, float, float], ...]) -> np.ndarray:
    result = np.zeros((int(round(duration * SAMPLE_RATE)), 2), dtype=np.float64)
    for samples, start, gain in layers:
        offset = int(round(start * SAMPLE_RATE))
        available = min(len(samples), len(result) - offset)
        if available > 0:
            result[offset : offset + available] += samples[:available] * gain
    return result


def write_wav(path: Path, samples: np.ndarray) -> None:
    pcm = np.round(np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm.tobytes())


def rising(samples: np.ndarray, start_gain: float = 0.5) -> np.ndarray:
    result = samples.copy()
    result *= np.linspace(start_gain, 1.0, len(result))[:, None]
    return result


def render_all(source_root: Path) -> dict[str, tuple[tuple[np.ndarray, tuple[str, ...]], ...]]:
    gregor = {
        number: decode(find_one(source_root, f"* - {number:02d} - *.mp3"))
        for number in (2, 3, 7, 8, 9, 10)
    }
    soundbiter = decode(find_one(source_root, "soundbiter_crowd_cheering.mp3"))
    booing = decode(find_one(source_root, "howardv_crowd_booing.mp3"))
    gasp = decode(find_one(source_root, "radiocounseling_crowd_gasp.mp3"))
    applause = decode(find_one(source_root, "evdawg_cheering_applause.mp3"))
    excited = decode(find_one(source_root, "itmightgetloud_excited.mp3"))
    goal = decode(find_one(source_root, "itmightgetloud_goal.mp3"))
    modern_ambience = decode(find_one(source_root, "itmightgetloud_ambience.mp3"))
    outrage_boo = decode(find_one(source_root, "trp_outrage_boo.mp3"))
    second_gasp = decode(find_one(source_root, "dr_skitz_gasp.mp3"))
    short_boo = decode(find_one(source_root, "dr_skitz_boo.mp3"))
    second_cheer = decode(find_one(source_root, "sounds_exciting_cheer.mp3"))
    large_applause = decode(find_one(source_root, "bansemer_applause.mp3"))
    stadium_applause = decode(find_one(source_root, "cognito_stadium_applause.mp3"))
    second_goal = decode(find_one(source_root, "d_jones_goal_reaction.mp3"))
    third_cheer = decode(find_one(source_root, "foolboy_crowd_cheer.mp3"))
    disappointed_oh = decode(find_one(source_root, "mrrap_disappointed_oh.mp3"))

    walkout = rising(cut(gregor[9], 7.0, 5.0), 0.55)
    walkout_2 = rising(loudest_cut(excited, 5.0), 0.52)
    walkout_3 = rising(loudest_cut(third_cheer, 5.0), 0.48)
    submission = rising(cut(gregor[2], 8.0, 4.5), 0.45)
    submission_2 = rising(loudest_cut(excited, 4.5), 0.40)
    submission_3 = rising(loudest_cut(gregor[8], 4.5), 0.42)
    knockdown_cheer = loudest_cut(gregor[3], 3.0)
    knockout_a = loudest_cut(soundbiter, 6.0)
    knockout_b = loudest_cut(gregor[3], 5.7)

    return {
        "pre_fight_arena_murmur": (
            (master(loop_cut(gregor[10], 5.0, 10.0), -24.0, True), ("gregor_quendel_crowd",)),
            (master(loop_cut(modern_ambience, 28.0, 10.0), -25.0, True), ("itmightgetloud_ambience",)),
            (master(loop_cut(gregor[7], 20.0, 10.0), -25.5, True), ("gregor_quendel_crowd",)),
        ),
        "walkout_crowd_swell": (
            (master(walkout, -18.0), ("gregor_quendel_crowd",)),
            (master(walkout_2, -18.0), ("itmightgetloud_excited",)),
            (master(walkout_3, -18.5), ("foolboy_crowd_cheer",)),
        ),
        "opening_bell_roar": (
            (master(loudest_cut(soundbiter, 3.5), -16.0), ("soundbiter_crowd_cheering",)),
            (master(loudest_cut(second_cheer, 3.5), -16.5), ("sounds_exciting_cheer",)),
            (master(loudest_cut(excited, 3.5), -16.0), ("itmightgetloud_excited",)),
        ),
        "clean_strike_ooh": (
            (master(cut(gasp, 0.0, 1.6), CLEAN_STRIKE_TARGET_RMS_DB,
                    peak_ceiling_db=CLEAN_STRIKE_PEAK_CEILING_DB), ("radiocounseling_crowd_gasp",)),
            (master(cut(second_gasp, 0.0, 1.6), -20.5,
                    peak_ceiling_db=CLEAN_STRIKE_PEAK_CEILING_DB), ("dr_skitz_gasp",)),
            (master(loudest_cut(disappointed_oh, 1.6, 0.0), -21.0,
                    peak_ceiling_db=CLEAN_STRIKE_PEAK_CEILING_DB), ("mrrap_disappointed_oh",)),
        ),
        "knockdown_gasp_roar": (
            (master(
                mix(3.2, ((gasp, 0.0, KNOCKDOWN_GASP_LAYER_GAIN), (knockdown_cheer, 0.16, 0.75))),
                -14.5,
            ), ("radiocounseling_crowd_gasp", "gregor_quendel_crowd")),
            (master(
                mix(3.2, ((second_gasp, 0.0, 0.52), (loudest_cut(goal, 3.0), 0.18, 0.75))),
                -14.5,
            ), ("dr_skitz_gasp", "itmightgetloud_goal")),
            (master(
                mix(3.2, ((loudest_cut(disappointed_oh, 1.5, 0.0), 0.0, 0.48),
                          (loudest_cut(excited, 3.0), 0.18, 0.76))),
                -15.0,
            ), ("mrrap_disappointed_oh", "itmightgetloud_excited")),
        ),
        "submission_attempt_swell": (
            (master(submission, -18.0), ("gregor_quendel_crowd",)),
            (master(submission_2, -18.0), ("itmightgetloud_excited",)),
            (master(submission_3, -18.5), ("gregor_quendel_crowd",)),
        ),
        "inactivity_boos": (
            (master(loudest_cut(booing, 4.0), -19.0), ("howardv_crowd_booing",)),
            (master(loudest_cut(outrage_boo, 4.0), -19.0), ("trp_outrage_boo",)),
            (master(cut(short_boo, 0.0, 4.0), -20.0), ("dr_skitz_boo",)),
        ),
        "round_end_applause": (
            (master(cut(applause, 0.7, 4.0), -18.0), ("evdawg_cheering_applause",)),
            (master(cut(stadium_applause, 0.6, 4.0), -18.5), ("cognito_stadium_applause",)),
            (master(loudest_cut(large_applause, 4.0), -18.5), ("bansemer_applause",)),
        ),
        "knockout_eruption": (
            (master(mix(6.0, ((knockout_a, 0.0, 0.8), (knockout_b, 0.3, 0.6))), -13.5),
             ("soundbiter_crowd_cheering", "gregor_quendel_crowd")),
            (master(loudest_cut(goal, 6.0), -14.0), ("itmightgetloud_goal",)),
            (master(mix(6.0, ((loudest_cut(second_goal, 6.0), 0.0, 0.82),
                              (loudest_cut(second_cheer, 5.5), 0.28, 0.45))), -14.0),
             ("d_jones_goal_reaction", "sounds_exciting_cheer")),
        ),
        "decision_tension_murmur": (
            (master(loop_cut(gregor[7], 11.0, 6.0), -27.0, True), ("gregor_quendel_crowd",)),
            (master(loop_cut(modern_ambience, 72.0, 6.0), -27.0, True), ("itmightgetloud_ambience",)),
            (master(loop_cut(gregor[10], 19.0, 6.0), -27.5, True), ("gregor_quendel_crowd",)),
        ),
        "controversial_decision_boos": (
            (master(loudest_cut(booing, 6.0), -17.0), ("howardv_crowd_booing",)),
            (master(loudest_cut(outrage_boo, 6.0), -17.5), ("trp_outrage_boo",)),
            (master(cut(short_boo, 0.0, 6.0), -19.0), ("dr_skitz_boo",)),
        ),
        "respectful_postfight_applause": (
            (master(cut(applause, 0.2, 6.0), -18.5), ("evdawg_cheering_applause",)),
            (master(cut(stadium_applause, 0.0, 6.0), -19.0), ("cognito_stadium_applause",)),
            (master(loudest_cut(large_applause, 6.0), -19.0), ("bansemer_applause",)),
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Folder containing the licensed source MP3 files")
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rendered = render_all(args.source_root.resolve())
    manifest_cues = []
    for cue_id, phase, duration, looping, gain_db, trigger, _default_sources in CUES:
        for variant, (samples, source_ids) in enumerate(rendered[cue_id], start=1):
            variant_id = cue_id if variant == 1 else f"{cue_id}_{variant:02d}"
            filename = f"{variant_id}.wav"
            write_wav(OUTPUT_DIR / filename, samples)
            manifest_cues.append({
                "id": variant_id, "family": cue_id, "variant": variant,
                "phase": phase, "duration": duration, "loop": looping,
                "suggested_gain_db": gain_db, "trigger": trigger, "file": filename,
                "sources": list(source_ids),
            })
            print(f"Wrote {filename}")
    manifest = {
        "format": "PCM WAV, stereo, 16-bit, 44100 Hz",
        "origin": "Edited and mastered from the licensed real crowd recordings listed in LICENSES.md.",
        "builder": "tools/build_crowd_audio_pack.py",
        "mix_controls": {
            "clean_strike_target_rms_db": CLEAN_STRIKE_TARGET_RMS_DB,
            "clean_strike_peak_ceiling_db": CLEAN_STRIKE_PEAK_CEILING_DB,
            "knockdown_gasp_layer_gain": KNOCKDOWN_GASP_LAYER_GAIN,
        },
        "variants_per_family": 3,
        "sources": list(SOURCES),
        "cues": manifest_cues,
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
