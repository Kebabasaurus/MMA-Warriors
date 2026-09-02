"""Optional, non-blocking audio for the live fight-night presentation.

Licensed crowd recordings are selected from the bundled crowd-audio manifest.
The original procedural cues remain as a fail-safe so missing assets, a damaged
manifest, or unavailable Windows playback can never interrupt an event.
"""

import array
import json
import math
import os
import random
import re
import struct
import sys
import tempfile
import threading
import time
import wave

from constants import ASSET_DIR

try:
    import ctypes
    from ctypes import wintypes
except Exception:
    ctypes = None
    wintypes = None


class FightNightAudioMixin:
    # Each app instance gets its own cue lock.  This class-level guard only
    # protects the one-time lazy creation for callers that construct the mixin
    # without going through the full application initializer (including tests).
    _fight_night_audio_init_lock = threading.Lock()
    DEFAULT_FIGHT_NIGHT_AUDIO_VOLUME = 55
    AUDIO_DEFAULT = "System default"
    _SAMPLE_RATE = 44100
    _CROWD_AUDIO_DIR = ASSET_DIR / "crowd_audio"
    _CROWD_CUE_FAMILIES = {
        "pre_fight": "pre_fight_arena_murmur",
        "bout_start": "pre_fight_arena_murmur",  # Backward-compatible alias.
        "walkout": "walkout_crowd_swell",
        "opening": "opening_bell_roar",
        "round_start": "opening_bell_roar",
        "impact": "clean_strike_ooh",
        "knockdown": "knockdown_gasp_roar",
        "submission": "submission_attempt_swell",
        "inactivity": "inactivity_boos",
        "round_end": "round_end_applause",
        "finish": "knockout_eruption",
        "decision_pending": "decision_tension_murmur",
        "controversial_decision": "controversial_decision_boos",
        "decision": "respectful_postfight_applause",
        "card_complete": "respectful_postfight_applause",
    }
    _CROWD_CUE_COOLDOWNS = {
        "pre_fight_arena_murmur": 8.0,
        "walkout_crowd_swell": 5.0,
        "opening_bell_roar": 3.0,
        "clean_strike_ooh": 2.4,
        "knockdown_gasp_roar": 2.8,
        "submission_attempt_swell": 5.0,
        "inactivity_boos": 8.0,
        "round_end_applause": 4.0,
        "knockout_eruption": 5.0,
        "decision_tension_murmur": 6.0,
        "controversial_decision_boos": 6.0,
        "respectful_postfight_applause": 5.0,
    }
    _MAX_SIMULTANEOUS_CUES = 4
    _HIGH_PRIORITY_CUES = {
        "knockdown", "finish", "decision", "controversial_decision", "card_complete",
    }

    def available_fight_night_outputs(self):
        """Return visible output choices without requiring optional audio modules."""
        choices = [(self.AUDIO_DEFAULT, None)]
        if ctypes is None:
            return choices
        try:
            winmm = ctypes.WinDLL("winmm")
        except Exception:
            return choices
        try:
            count = int(winmm.waveOutGetNumDevs())
        except Exception:
            return choices
        for index in range(count):
            name = self._wave_output_device_name(winmm, index)
            if name:
                choices.append((f"{name} [{index}]", index))
        return choices

    def resolve_fight_night_output(self, label=None):
        label = str(label if label is not None else self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT))
        if label == self.AUDIO_DEFAULT:
            return None
        match = re.search(r"\[(\d+)\]\s*$", label)
        if match:
            return int(match.group(1))
        return None

    def ensure_audio_defaults(self):
        self.rules.setdefault("fight_night_audio_enabled", True)
        self.rules.setdefault("fight_night_audio_output", self.AUDIO_DEFAULT)
        self.rules["fight_night_audio_volume"] = self.normalize_fight_night_audio_volume(
            self.rules.get("fight_night_audio_volume", self.DEFAULT_FIGHT_NIGHT_AUDIO_VOLUME)
        )

    def normalize_fight_night_audio_volume(self, value):
        """Return a safe whole-number percentage for UI, saves, and playback."""
        try:
            value = round(float(value))
        except (TypeError, ValueError, OverflowError):
            value = self.DEFAULT_FIGHT_NIGHT_AUDIO_VOLUME
        return max(0, min(100, int(value)))

    def set_fight_night_audio_volume(self, value):
        """Apply and persist a volume change from any Fight Night control."""
        volume = self.normalize_fight_night_audio_volume(value)
        self.rules["fight_night_audio_volume"] = volume
        return volume

    def fight_night_audio_volume(self):
        self.ensure_audio_defaults()
        return int(self.rules["fight_night_audio_volume"])

    def fight_night_audio_status(self):
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return "Off"
        return str(self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT))

    def _ensure_fight_night_audio_runtime(self):
        """Return the per-instance cue lock, creating runtime state once."""
        with FightNightAudioMixin._fight_night_audio_init_lock:
            lock = getattr(self, "_fight_night_audio_lock", None)
            if lock is None:
                lock = threading.Lock()
                self._fight_night_audio_lock = lock
            if not hasattr(self, "_fight_night_active_cues"):
                self._fight_night_active_cues = 0
            if not hasattr(self, "_fight_night_audio_session_stop"):
                self._fight_night_audio_session_stop = threading.Event()
            if not hasattr(self, "_fight_night_ambience_thread"):
                self._fight_night_ambience_thread = None
            if not hasattr(self, "_fight_night_audio_rng"):
                self._fight_night_audio_rng = random.SystemRandom()
            return lock

    def _fight_night_rng(self):
        """Return audio-only entropy that cannot advance simulation RNG."""
        self._ensure_fight_night_audio_runtime()
        return self._fight_night_audio_rng

    # ---- Bundled crowd recordings ---------------------------------------

    def _crowd_audio_manifest(self):
        """Load and cache the optional crowd pack without making it required."""
        if hasattr(self, "_fight_night_crowd_manifest"):
            return self._fight_night_crowd_manifest
        manifest = {}
        try:
            path = self._CROWD_AUDIO_DIR / "manifest.json"
            candidate = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(candidate, dict) and isinstance(candidate.get("cues"), list):
                manifest = candidate
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
        self._fight_night_crowd_manifest = manifest
        return manifest

    def _crowd_audio_entries_for_cue(self, cue):
        """Return safe, playable manifest entries for one logical game cue."""
        family = self._CROWD_CUE_FAMILIES.get(str(cue), "")
        if not family:
            return []
        root = self._CROWD_AUDIO_DIR.resolve()
        entries = []
        for entry in self._crowd_audio_manifest().get("cues", []):
            if not isinstance(entry, dict) or entry.get("family") != family:
                continue
            filename = str(entry.get("file", ""))
            if not filename or filename != os.path.basename(filename):
                continue
            try:
                path = (root / filename).resolve()
                if path.parent != root or not path.is_file():
                    continue
                gain_db = float(entry.get("suggested_gain_db", 0.0))
            except (OSError, TypeError, ValueError):
                continue
            entries.append({**entry, "path": path, "suggested_gain_db": gain_db})
        return sorted(entries, key=lambda item: (int(item.get("variant", 0)), item["path"].name))

    def _choose_crowd_audio(self, cue):
        """Choose a source-distinct variant without repeating the last take."""
        entries = self._crowd_audio_entries_for_cue(cue)
        if not entries:
            return None
        family = self._CROWD_CUE_FAMILIES[str(cue)]
        previous = getattr(self, "_fight_night_last_crowd_variant", {}).get(family)
        choices = [entry for entry in entries if entry["path"].name != previous] or entries
        selected = self._fight_night_rng().choice(choices)
        if not hasattr(self, "_fight_night_last_crowd_variant"):
            self._fight_night_last_crowd_variant = {}
        self._fight_night_last_crowd_variant[family] = selected["path"].name
        return selected

    def _read_crowd_audio(self, path):
        """Read one mastered PCM asset and reject unsupported file formats."""
        with wave.open(str(path), "rb") as wav_file:
            channels = int(wav_file.getnchannels())
            sample_width = int(wav_file.getsampwidth())
            sample_rate = int(wav_file.getframerate())
            compression = wav_file.getcomptype()
            if channels not in (1, 2) or sample_width != 2 or compression != "NONE":
                raise ValueError("Unsupported crowd-audio WAV format")
            frames = wav_file.readframes(wav_file.getnframes())
        return frames, channels, sample_rate

    def _scale_pcm16(self, frames, gain):
        """Apply settings and manifest gain to little-endian signed PCM."""
        gain = max(0.0, min(1.0, float(gain)))
        if gain >= 0.999:
            return frames
        samples = array.array("h")
        samples.frombytes(frames)
        if sys.byteorder != "little":
            samples.byteswap()
        for index, sample in enumerate(samples):
            samples[index] = max(-32768, min(32767, int(sample * gain)))
        if sys.byteorder != "little":
            samples.byteswap()
        return samples.tobytes()

    def _crossfade_pcm16_loop(self, frames, channels, sample_rate, crossfade_ms=180):
        """Return a seamless PCM loop by blending its tail back into its head.

        The loop starts immediately after the original head and ends on the
        sample immediately before that point. This keeps both joins contiguous
        while the tail/head overlap removes the audible restart in crowd beds.
        """
        channels = max(1, int(channels))
        sample_rate = max(1, int(sample_rate))
        samples = array.array("h")
        samples.frombytes(frames)
        if sys.byteorder != "little":
            samples.byteswap()
        frame_count = len(samples) // channels
        overlap = min(
            max(2, int(sample_rate * max(20, int(crossfade_ms)) / 1000)),
            frame_count // 4,
        )
        if frame_count < 8 or overlap < 2:
            return frames
        head_end = overlap * channels
        tail_start = (frame_count - overlap) * channels
        middle = samples[head_end:tail_start]
        blended = array.array("h")
        denominator = max(1, overlap - 1)
        for frame_index in range(overlap):
            blend = frame_index / denominator
            for channel in range(channels):
                head_sample = samples[frame_index * channels + channel]
                tail_sample = samples[tail_start + frame_index * channels + channel]
                blended.append(int(round(tail_sample * (1.0 - blend) + head_sample * blend)))
        loop_samples = array.array("h", middle)
        loop_samples.extend(blended)
        if sys.byteorder != "little":
            loop_samples.byteswap()
        return loop_samples.tobytes()

    def fight_night_decision_reaction(self, scorecard_lines):
        """Use the boos family only for a close 2-1 judges' vote."""
        vote_line = next(
            (line for line in scorecard_lines if str(line).strip().startswith("Judges' vote:")),
            "",
        )
        vote_match = re.search(r"Judges' vote: .*? (\d+), .*? (\d+)\s*$", str(vote_line))
        if vote_match and sorted(map(int, vote_match.groups())) == [1, 2]:
            return "controversial_decision"
        return "decision"

    def fight_night_local_crowd_profile(self, fighters, region, city=""):
        """Describe and mix a hometown or nearby-market crowd connection."""
        neutral = {"gain": 1.0, "level": "Neutral", "fighter": "", "both_local": False, "summary": ""}
        if not region or not hasattr(self, "fighter_event_connection"):
            return neutral
        connections = []
        for fighter in fighters:
            if not fighter:
                continue
            connection = self.fighter_event_connection(fighter, region, city)
            strength = max(0.0, min(1.0, float(connection.get("strength", 0.0) or 0.0)))
            connections.append((strength, str(connection.get("level", "Neutral")), fighter))
        connections.sort(key=lambda row: row[0], reverse=True)
        local = [row for row in connections if row[0] >= 0.52]
        if not local:
            return neutral
        top_strength, top_level, top_fighter = local[0]
        both_local = len(local) > 1
        if both_local:
            average_strength = sum(row[0] for row in local[:2]) / 2
            gain = min(1.18, 1.08 + average_strength * 0.10)
            summary = "Both fighters have strong local ties, creating a divided but louder arena."
        else:
            gain = min(1.20, 1.0 + top_strength * 0.20)
            hometown = str(getattr(top_fighter, "hometown", "") or "")
            if top_level == "Hometown" and hometown:
                summary = f"{top_fighter.name} is fighting in their hometown of {hometown}; the home crowd is especially loud."
            else:
                summary = f"{top_fighter.name} has a {top_level.lower()} connection and receives a stronger local reaction."
        return {
            "gain": round(gain, 3),
            "level": top_level,
            "fighter": str(getattr(top_fighter, "name", "")),
            "both_local": both_local,
            "summary": summary,
        }

    # ---- Synthesis primitives ---------------------------------------------

    def _env(self, frame_count, attack, release, sr):
        """Linear attack/release amplitude envelope."""
        duration = frame_count / sr
        attack = max(1e-4, attack)
        release = max(1e-4, release)
        return [
            min(1.0, (i / sr) / attack) * min(1.0, max(0.0, duration - (i / sr)) / release)
            for i in range(frame_count)
        ]

    def _bell(self, freq, duration, gain, sr):
        """A struck round bell: inharmonic partials with an exponential ring-down."""
        frame_count = max(1, int(sr * duration))
        wave_data = [0.0] * frame_count
        strike = min(frame_count, int(sr * 0.004))
        partials = ((1.0, 1.0, 4.5), (2.76, 0.6, 6.5), (5.4, 0.4, 9.0), (8.9, 0.22, 12.0))
        for i in range(frame_count):
            t = i / sr
            sample = 0.0
            for ratio, amp, decay in partials:
                sample += amp * math.sin(2 * math.pi * freq * ratio * t) * math.exp(-t * decay)
            if i < strike:
                sample += self._fight_night_rng().uniform(-0.4, 0.4)
            wave_data[i] = sample * gain
        return wave_data

    def _smooth_noise(self, frame_count, kernel):
        rng = self._fight_night_rng()
        noise = [rng.uniform(-1.0, 1.0) for _ in range(frame_count)]
        kernel = max(2, int(kernel))
        smoothed = [0.0] * frame_count
        window = 0.0
        for i, sample in enumerate(noise):
            window += sample
            if i >= kernel:
                window -= noise[i - kernel]
            smoothed[i] = window / min(i + 1, kernel)
        return smoothed

    def _impact(self, duration, gain, sr, tone=150.0, sharpness=22.0):
        """A punch/kick impact: a pitch-dropping body plus a filtered noise slap."""
        frame_count = max(1, int(sr * duration))
        slap = self._smooth_noise(frame_count, max(2, int(sr * 0.0009)))
        wave_data = [0.0] * frame_count
        phase = 0.0
        for i in range(frame_count):
            t = i / sr
            instantaneous = tone * math.exp(-t * 16.0) + 48.0
            phase += 2 * math.pi * instantaneous / sr
            body = math.sin(phase)
            env = math.exp(-t * sharpness)
            wave_data[i] = (body * 0.7 + slap[i] * 0.55) * env * gain
        return wave_data

    def _crowd(self, duration, gain, sr, intensity=1.0, brightness=1.0, swell=0.4):
        """Filtered noise shaped into a crowd bed, roar, or applause wash."""
        frame_count = max(1, int(sr * duration))
        kernel = max(2, int(sr * 0.006 / max(0.25, brightness)))
        wash = self._smooth_noise(frame_count, kernel)
        mean = sum(wash) / len(wash)
        duration_s = frame_count / sr
        wave_data = [0.0] * frame_count
        for i, sample in enumerate(wash):
            t = i / sr
            rise = min(1.0, t / max(1e-3, duration_s * swell))
            fall = min(1.0, max(0.0, duration_s - t) / max(1e-3, duration_s * 0.55))
            tremolo = 1.0 + 0.25 * math.sin(2 * math.pi * (3.0 + 4.0 * intensity) * t)
            wave_data[i] = (sample - mean) * rise * fall * tremolo * gain * intensity
        return wave_data

    def _mix(self, layers, sr):
        """Overlay (samples, start_seconds) layers into one soft-limited buffer."""
        if not layers:
            return [0.0]
        total = max(int(start * sr) + len(buf) for buf, start in layers)
        mix = [0.0] * total
        for buf, start in layers:
            offset = int(start * sr)
            for i, sample in enumerate(buf):
                mix[offset + i] += sample
        peak = max((abs(sample) for sample in mix), default=0.0)
        if peak > 0.99:
            scale = 0.9 / peak
            mix = [math.tanh(sample * scale) * 0.95 for sample in mix]
        return mix

    def _render_cue(self, cue, sr):
        """Compose a full waveform for a fight-night cue."""
        if cue in ("pre_fight", "bout_start"):
            return self._mix([
                (self._crowd(0.85, 0.30, sr, intensity=0.9, brightness=0.8, swell=0.6), 0.0),
                (self._bell(760, 0.34, 0.5, sr), 0.05),
                (self._bell(760, 0.42, 0.5, sr), 0.33),
            ], sr)
        if cue == "walkout":
            return self._crowd(1.2, 0.38, sr, intensity=1.0, brightness=1.0, swell=0.55)
        if cue == "opening":
            return self._mix([
                (self._bell(820, 0.55, 0.62, sr), 0.0),
                (self._crowd(0.9, 0.34, sr, intensity=1.0, brightness=1.1, swell=0.2), 0.05),
            ], sr)
        if cue == "round_start":
            return self._mix([(self._bell(820, 0.5, 0.6, sr), 0.0)], sr)
        if cue == "impact":
            rng = self._fight_night_rng()
            tone = rng.uniform(120, 185)
            gain = rng.uniform(0.5, 0.72)
            return self._impact(rng.uniform(0.14, 0.2), gain, sr, tone=tone, sharpness=rng.uniform(20, 27))
        if cue == "knockdown":
            return self._mix([
                (self._impact(0.26, 0.85, sr, tone=95.0, sharpness=13.0), 0.0),
                (self._crowd(0.7, 0.5, sr, intensity=1.2, brightness=1.2, swell=0.15), 0.05),
            ], sr)
        if cue == "submission":
            return self._crowd(0.9, 0.42, sr, intensity=1.05, brightness=1.0, swell=0.2)
        if cue == "inactivity":
            return self._crowd(0.75, 0.24, sr, intensity=0.65, brightness=0.65, swell=0.15)
        if cue == "round_end":
            return self._crowd(0.85, 0.34, sr, intensity=0.85, brightness=1.35, swell=0.2)
        if cue == "finish":
            return self._mix([
                (self._impact(0.22, 0.7, sr, tone=110.0, sharpness=16.0), 0.0),
                (self._crowd(1.15, 0.6, sr, intensity=1.4, brightness=1.4, swell=0.1), 0.02),
                (self._bell(700, 0.5, 0.4, sr), 0.18),
            ], sr)
        if cue == "decision_pending":
            return self._crowd(0.9, 0.22, sr, intensity=0.55, brightness=0.65, swell=0.15)
        if cue in ("decision", "controversial_decision"):
            return self._mix([
                (self._bell(560, 0.42, 0.42, sr), 0.0),
                (self._crowd(0.85, 0.32, sr, intensity=0.8, brightness=1.5, swell=0.3), 0.1),
            ], sr)
        if cue == "card_complete":
            return self._mix([
                (self._crowd(1.25, 0.5, sr, intensity=1.0, brightness=1.6, swell=0.25), 0.0),
                (self._bell(620, 0.45, 0.3, sr), 0.0),
            ], sr)
        if cue == "preview":
            return self._mix([
                (self._bell(660, 0.28, 0.32, sr), 0.0),
                (self._bell(880, 0.32, 0.28, sr), 0.14),
            ], sr)
        return self._impact(0.16, 0.5, sr)

    def _fight_night_fallback_tone(self, cue):
        """Single (freq, ms) beep if WAV playback is unavailable."""
        return {
            "pre_fight": (520, 100), "bout_start": (760, 150), "walkout": (680, 150),
            "opening": (820, 160), "round_start": (820, 130), "impact": (150, 70),
            "knockdown": (95, 200), "submission": (460, 150), "inactivity": (180, 120),
            "round_end": (620, 160), "finish": (700, 260), "decision_pending": (440, 130),
            "controversial_decision": (180, 220), "decision": (560, 180),
            "card_complete": (620, 240), "preview": (740, 120),
        }.get(cue, (150, 90))

    def _write_fight_night_wav(self, samples, volume):
        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample * volume))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        return self._write_fight_night_pcm_wav(bytes(frames), 1, self._SAMPLE_RATE)

    def _write_fight_night_pcm_wav(self, frames, channels, sample_rate):
        audio_dir = os.path.join(tempfile.gettempdir(), "mma_warriors_audio")
        os.makedirs(audio_dir, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(prefix="cue_", suffix=".wav", dir=audio_dir, delete=False)
        path = handle.name
        handle.close()
        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(frames)
        return path

    def _play_fight_night_wav(self, path):
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME)

    def _wave_output_device_name(self, winmm, index):
        if ctypes is None or wintypes is None:
            return ""

        class WAVEOUTCAPS(ctypes.Structure):
            _fields_ = [
                ("wMid", wintypes.WORD),
                ("wPid", wintypes.WORD),
                ("vDriverVersion", wintypes.UINT),
                ("szPname", ctypes.c_wchar * 32),
                ("dwFormats", wintypes.DWORD),
                ("wChannels", wintypes.WORD),
                ("wReserved1", wintypes.WORD),
                ("dwSupport", wintypes.DWORD),
            ]

        caps = WAVEOUTCAPS()
        try:
            result = winmm.waveOutGetDevCapsW(index, ctypes.byref(caps), ctypes.sizeof(caps))
        except Exception:
            return ""
        if result != 0:
            return ""
        return str(caps.szPname).strip()

    def _play_fight_night_pcm(self, frames, channels, sample_rate, device_index=None, cancel_event=None):
        if ctypes is None or wintypes is None:
            path = self._write_fight_night_pcm_wav(frames, channels, sample_rate)
            try:
                self._play_fight_night_wav(path)
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass
            return

        winmm = ctypes.WinDLL("winmm")
        CALLBACK_NULL = 0
        WAVE_FORMAT_PCM = 1
        WAVE_MAPPER = ctypes.c_uint(-1).value
        WHDR_DONE = 0x00000001

        class WAVEFORMATEX(ctypes.Structure):
            _fields_ = [
                ("wFormatTag", wintypes.WORD),
                ("nChannels", wintypes.WORD),
                ("nSamplesPerSec", wintypes.DWORD),
                ("nAvgBytesPerSec", wintypes.DWORD),
                ("nBlockAlign", wintypes.WORD),
                ("wBitsPerSample", wintypes.WORD),
                ("cbSize", wintypes.WORD),
            ]

        class WAVEHDR(ctypes.Structure):
            _fields_ = [
                ("lpData", wintypes.LPSTR),
                ("dwBufferLength", wintypes.DWORD),
                ("dwBytesRecorded", wintypes.DWORD),
                ("dwUser", ctypes.c_size_t),
                ("dwFlags", wintypes.DWORD),
                ("dwLoops", wintypes.DWORD),
                ("lpNext", ctypes.c_void_p),
                ("reserved", ctypes.c_size_t),
            ]

        data = ctypes.create_string_buffer(frames)
        block_align = channels * 2
        fmt = WAVEFORMATEX(
            WAVE_FORMAT_PCM,
            channels,
            sample_rate,
            sample_rate * block_align,
            block_align,
            16,
            0,
        )
        handle = wintypes.HANDLE()
        device = WAVE_MAPPER if device_index is None else int(device_index)
        if winmm.waveOutOpen(ctypes.byref(handle), device, ctypes.byref(fmt), 0, 0, CALLBACK_NULL) != 0:
            raise RuntimeError("waveOutOpen failed")
        header = WAVEHDR(ctypes.cast(data, wintypes.LPSTR), len(frames), 0, 0, 0, 0, None, 0)
        prepared = False
        try:
            if winmm.waveOutPrepareHeader(handle, ctypes.byref(header), ctypes.sizeof(header)) != 0:
                raise RuntimeError("waveOutPrepareHeader failed")
            prepared = True
            if winmm.waveOutWrite(handle, ctypes.byref(header), ctypes.sizeof(header)) != 0:
                raise RuntimeError("waveOutWrite failed")
            duration = len(frames) / max(1, sample_rate * block_align)
            deadline = time.monotonic() + max(1.0, duration + 1.0)
            while not (header.dwFlags & WHDR_DONE) and time.monotonic() < deadline:
                if cancel_event is not None and cancel_event.is_set():
                    break
                time.sleep(0.01)
            winmm.waveOutReset(handle)
        finally:
            if prepared:
                try:
                    winmm.waveOutUnprepareHeader(handle, ctypes.byref(header), ctypes.sizeof(header))
                except Exception:
                    pass
            winmm.waveOutClose(handle)

    def _play_fight_night_looping_pcm(self, frames, channels, sample_rate, stop_event, device_index=None):
        """Loop one prepared crowd bed on a persistent Windows output stream."""
        if ctypes is None or wintypes is None:
            while not stop_event.is_set():
                self._play_fight_night_pcm(
                    frames, channels, sample_rate, device_index, cancel_event=stop_event,
                )
            return

        winmm = ctypes.WinDLL("winmm")
        CALLBACK_NULL = 0
        WAVE_FORMAT_PCM = 1
        WAVE_MAPPER = ctypes.c_uint(-1).value
        WHDR_BEGINLOOP = 0x00000004
        WHDR_ENDLOOP = 0x00000008

        class WAVEFORMATEX(ctypes.Structure):
            _fields_ = [
                ("wFormatTag", wintypes.WORD),
                ("nChannels", wintypes.WORD),
                ("nSamplesPerSec", wintypes.DWORD),
                ("nAvgBytesPerSec", wintypes.DWORD),
                ("nBlockAlign", wintypes.WORD),
                ("wBitsPerSample", wintypes.WORD),
                ("cbSize", wintypes.WORD),
            ]

        class WAVEHDR(ctypes.Structure):
            _fields_ = [
                ("lpData", wintypes.LPSTR),
                ("dwBufferLength", wintypes.DWORD),
                ("dwBytesRecorded", wintypes.DWORD),
                ("dwUser", ctypes.c_size_t),
                ("dwFlags", wintypes.DWORD),
                ("dwLoops", wintypes.DWORD),
                ("lpNext", ctypes.c_void_p),
                ("reserved", ctypes.c_size_t),
            ]

        data = ctypes.create_string_buffer(frames)
        block_align = channels * 2
        fmt = WAVEFORMATEX(
            WAVE_FORMAT_PCM,
            channels,
            sample_rate,
            sample_rate * block_align,
            block_align,
            16,
            0,
        )
        handle = wintypes.HANDLE()
        device = WAVE_MAPPER if device_index is None else int(device_index)
        if winmm.waveOutOpen(ctypes.byref(handle), device, ctypes.byref(fmt), 0, 0, CALLBACK_NULL) != 0:
            raise RuntimeError("waveOutOpen failed")
        header = WAVEHDR(
            ctypes.cast(data, wintypes.LPSTR),
            len(frames),
            0,
            0,
            WHDR_BEGINLOOP | WHDR_ENDLOOP,
            0xFFFFFFFF,
            None,
            0,
        )
        prepared = False
        try:
            if winmm.waveOutPrepareHeader(handle, ctypes.byref(header), ctypes.sizeof(header)) != 0:
                raise RuntimeError("waveOutPrepareHeader failed")
            prepared = True
            if winmm.waveOutWrite(handle, ctypes.byref(header), ctypes.sizeof(header)) != 0:
                raise RuntimeError("waveOutWrite failed")
            stop_event.wait()
            winmm.waveOutReset(handle)
        finally:
            if prepared:
                try:
                    winmm.waveOutUnprepareHeader(handle, ctypes.byref(header), ctypes.sizeof(header))
                except Exception:
                    pass
            winmm.waveOutClose(handle)

    def _play_fight_night_samples(self, samples, volume, device_index=None, cancel_event=None):
        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample * volume))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        self._play_fight_night_pcm(
            bytes(frames), 1, self._SAMPLE_RATE, device_index, cancel_event=cancel_event,
        )

    def _play_crowd_audio_entry(self, entry, volume, device_index=None, cancel_event=None):
        frames, channels, sample_rate = self._read_crowd_audio(entry["path"])
        manifest_gain = 10 ** (float(entry.get("suggested_gain_db", 0.0)) / 20.0)
        frames = self._scale_pcm16(frames, volume * manifest_gain)
        self._play_fight_night_pcm(
            frames, channels, sample_rate, device_index, cancel_event=cancel_event,
        )

    def start_fight_night_audio_session(self, context_gain=1.0):
        """Start one continuous arena bed for the lifetime of a live card."""
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return False
        volume = self.fight_night_audio_volume() / 100
        if volume <= 0:
            return False
        context_gain = max(0.75, min(1.20, float(context_gain or 1.0)))
        audio_lock = self._ensure_fight_night_audio_runtime()
        with audio_lock:
            active_thread = self._fight_night_ambience_thread
            active_stop = self._fight_night_audio_session_stop
            if active_thread is not None and active_thread.is_alive() and not active_stop.is_set():
                return True
            session_stop = threading.Event()
            self._fight_night_audio_session_stop = session_stop
            self._fight_night_last_sound_at = 0.0
            self._fight_night_last_cue_at = {}
            crowd_entry = self._choose_crowd_audio("pre_fight")
            if not crowd_entry or not bool(crowd_entry.get("loop", False)):
                return False
            device = self.resolve_fight_night_output()

        def ambience_worker():
            try:
                frames, channels, sample_rate = self._read_crowd_audio(crowd_entry["path"])
                manifest_gain = 10 ** (float(crowd_entry.get("suggested_gain_db", 0.0)) / 20.0)
                frames = self._scale_pcm16(frames, volume * context_gain * manifest_gain)
                frames = self._crossfade_pcm16_loop(frames, channels, sample_rate)
                self._play_fight_night_looping_pcm(
                    frames, channels, sample_rate, session_stop, device,
                )
            except Exception:
                # The arena bed is optional. One-shot procedural reactions remain
                # available if the manifest or selected device cannot sustain it.
                pass
            finally:
                with audio_lock:
                    if self._fight_night_audio_session_stop is session_stop:
                        self._fight_night_ambience_thread = None

        thread = threading.Thread(
            target=ambience_worker,
            name="FightNightAudio-Ambience",
            daemon=True,
        )
        with audio_lock:
            self._fight_night_ambience_thread = thread
        try:
            thread.start()
        except Exception:
            with audio_lock:
                if self._fight_night_ambience_thread is thread:
                    self._fight_night_ambience_thread = None
            return False
        return True

    def stop_fight_night_audio_session(self, wait=False):
        """Stop the arena bed and cancel active reactions from the live card."""
        audio_lock = self._ensure_fight_night_audio_runtime()
        with audio_lock:
            stop_event = self._fight_night_audio_session_stop
            thread = self._fight_night_ambience_thread
            stop_event.set()
            self._fight_night_last_sound_at = 0.0
            self._fight_night_last_cue_at = {}
        if wait and thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.75)
        return True

    def play_fight_night_sound(self, cue, context_gain=1.0):
        """Play a short cue without blocking commentary playback or simulation."""
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return False
        volume = self.fight_night_audio_volume() / 100
        context_gain = max(0.75, min(1.20, float(context_gain or 1.0)))
        volume *= context_gain
        if volume <= 0:
            return False
        audio_lock = self._ensure_fight_night_audio_runtime()
        family = self._CROWD_CUE_FAMILIES.get(str(cue))
        cue_key = str(cue)
        high_priority = cue_key in self._HIGH_PRIORITY_CUES
        with audio_lock:
            now = time.monotonic()
            if now - getattr(self, "_fight_night_last_sound_at", 0.0) < 0.10:
                return False
            cue_ceiling = self._MAX_SIMULTANEOUS_CUES if high_priority else self._MAX_SIMULTANEOUS_CUES - 1
            if self._fight_night_active_cues >= cue_ceiling:
                return False
            if family:
                last_cue_times = getattr(self, "_fight_night_last_cue_at", {})
                cooldown = self._CROWD_CUE_COOLDOWNS.get(family, 0.0)
                if now - last_cue_times.get(cue_key, 0.0) < cooldown:
                    return False
            self._fight_night_active_cues += 1
            if family:
                if not hasattr(self, "_fight_night_last_cue_at"):
                    self._fight_night_last_cue_at = {}
                self._fight_night_last_cue_at[cue_key] = now
            self._fight_night_last_sound_at = now
            crowd_entry = self._choose_crowd_audio(cue)
            session_stop = self._fight_night_audio_session_stop
            if session_stop.is_set():
                session_stop = None
        device = self.resolve_fight_night_output()

        def worker():
            try:
                if crowd_entry:
                    try:
                        self._play_crowd_audio_entry(
                            crowd_entry, volume, device, cancel_event=session_stop,
                        )
                        return
                    except Exception:
                        pass
                samples = self._render_cue(cue, self._SAMPLE_RATE)
                self._play_fight_night_samples(
                    samples, volume, device, cancel_event=session_stop,
                )
            except Exception:
                try:
                    import winsound
                    freq, ms = self._fight_night_fallback_tone(cue)
                    winsound.Beep(max(37, int(freq)), max(40, int(ms)))
                except Exception:
                    pass
            finally:
                with audio_lock:
                    self._fight_night_active_cues = max(0, self._fight_night_active_cues - 1)

        try:
            threading.Thread(target=worker, name=f"FightNightAudio-{cue}", daemon=True).start()
        except Exception:
            with audio_lock:
                self._fight_night_active_cues = max(0, self._fight_night_active_cues - 1)
            return False
        return True
