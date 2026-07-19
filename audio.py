"""Procedural, non-blocking audio cues for the live fight-night presentation.

Everything here is synthesised on the fly with numpy so the game ships no audio
assets and stays fully self-contained. The cues aim for an MMA broadcast feel:
a metallic round bell, weighty punch impacts that vary shot to shot, crowd
swells, a roar on a finish, and applause to close a card. Machines without
numpy/sounddevice fall back to a single winsound beep, and any audio failure is
swallowed so it can never interrupt an event.
"""

import math
import threading
import time

try:
    import numpy as np
    import sounddevice as sd
except Exception:  # The game remains playable on machines without audio support.
    np = None
    sd = None


class FightNightAudioMixin:
    AUDIO_DEFAULT = "System default"
    _SAMPLE_RATE = 32000

    def available_fight_night_outputs(self):
        """Return visible output choices without making audio hardware required."""
        choices = [(self.AUDIO_DEFAULT, None)]
        if sd is None:
            return choices
        try:
            for index, device in enumerate(sd.query_devices()):
                if int(device.get("max_output_channels", 0) or 0) <= 0:
                    continue
                name = str(device.get("name", "Output device")).strip() or "Output device"
                choices.append((f"{name} [{index}]", index))
        except Exception:
            pass
        return choices

    def resolve_fight_night_output(self, label=None):
        label = str(label if label is not None else self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT))
        for choice, index in self.available_fight_night_outputs():
            if choice == label:
                return index
        return None

    def ensure_audio_defaults(self):
        self.rules.setdefault("fight_night_audio_enabled", True)
        self.rules.setdefault("fight_night_audio_output", self.AUDIO_DEFAULT)
        self.rules.setdefault("fight_night_audio_volume", 55)

    def fight_night_audio_status(self):
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return "Off"
        if sd is None or np is None:
            return "Windows default speaker"
        selected = self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT)
        return str(selected)

    # ---- Synthesis primitives ---------------------------------------------

    def _env(self, frame_count, attack, release, sr):
        """Linear attack/release amplitude envelope."""
        timeline = np.arange(frame_count, dtype=np.float32) / sr
        duration = frame_count / sr
        attack = max(1e-4, attack)
        release = max(1e-4, release)
        rise = np.minimum(1.0, timeline / attack)
        fall = np.minimum(1.0, np.maximum(0.0, duration - timeline) / release)
        return (rise * fall).astype(np.float32)

    def _bell(self, freq, duration, gain, sr):
        """A struck round bell: inharmonic partials with an exponential ring-down."""
        frame_count = max(1, int(sr * duration))
        timeline = np.arange(frame_count, dtype=np.float32) / sr
        wave = np.zeros(frame_count, dtype=np.float32)
        # Ratios and per-partial decay chosen to read as a metallic fight bell.
        for ratio, amp, decay in ((1.0, 1.0, 4.5), (2.76, 0.6, 6.5), (5.4, 0.4, 9.0), (8.9, 0.22, 12.0)):
            wave += amp * np.sin(2 * math.pi * freq * ratio * timeline) * np.exp(-timeline * decay)
        # Tiny strike transient so the onset has a bit of "clack".
        strike = min(frame_count, int(sr * 0.004))
        if strike:
            wave[:strike] += (np.random.rand(strike).astype(np.float32) * 2 - 1) * 0.4
        return (wave * gain).astype(np.float32)

    def _impact(self, duration, gain, sr, tone=150.0, sharpness=22.0):
        """A punch/kick impact: a pitch-dropping body plus a filtered noise slap."""
        frame_count = max(1, int(sr * duration))
        timeline = np.arange(frame_count, dtype=np.float32) / sr
        # Body: frequency sweeps down fast for a "thud".
        instantaneous = tone * np.exp(-timeline * 16.0) + 48.0
        body = np.sin(2 * math.pi * np.cumsum(instantaneous) / sr)
        # Slap: white noise smoothed into a low thwack.
        noise = np.random.rand(frame_count).astype(np.float32) * 2 - 1
        kernel = max(2, int(sr * 0.0009))
        slap = np.convolve(noise, np.ones(kernel, dtype=np.float32) / kernel, mode="same")
        env = np.exp(-timeline * sharpness).astype(np.float32)
        return ((body * 0.7 + slap * 0.55) * env * gain).astype(np.float32)

    def _crowd(self, duration, gain, sr, intensity=1.0, brightness=1.0, swell=0.4):
        """Filtered noise shaped into a crowd bed, roar, or applause wash."""
        frame_count = max(1, int(sr * duration))
        noise = np.random.rand(frame_count).astype(np.float32) * 2 - 1
        kernel = max(2, int(sr * 0.006 / max(0.25, brightness)))
        wash = np.convolve(noise, np.ones(kernel, dtype=np.float32) / kernel, mode="same")
        wash -= wash.mean()
        timeline = np.arange(frame_count, dtype=np.float32) / sr
        duration_s = frame_count / sr
        rise = np.minimum(1.0, timeline / max(1e-3, duration_s * swell))
        fall = np.minimum(1.0, np.maximum(0.0, duration_s - timeline) / max(1e-3, duration_s * 0.55))
        # Slow tremolo to suggest a surging, breathing crowd.
        tremolo = 1.0 + 0.25 * np.sin(2 * math.pi * (3.0 + 4.0 * intensity) * timeline)
        return (wash * rise * fall * tremolo * gain * intensity).astype(np.float32)

    def _mix(self, layers, sr):
        """Overlay (array, start_seconds) layers into one soft-limited buffer."""
        if not layers:
            return np.zeros(1, dtype=np.float32)
        total = max(int(start * sr) + len(buf) for buf, start in layers)
        mix = np.zeros(total, dtype=np.float32)
        for buf, start in layers:
            offset = int(start * sr)
            mix[offset:offset + len(buf)] += buf
        # Soft clip to keep dense finishes from distorting.
        peak = float(np.max(np.abs(mix))) if len(mix) else 0.0
        if peak > 0.99:
            mix = np.tanh(mix * (0.9 / peak)) * 0.95
        return mix.astype(np.float32)

    def _render_cue(self, cue, sr):
        """Compose a full waveform for a fight-night cue."""
        if cue == "bout_start":
            return self._mix([
                (self._crowd(0.85, 0.30, sr, intensity=0.9, brightness=0.8, swell=0.6), 0.0),
                (self._bell(760, 0.34, 0.5, sr), 0.05),
                (self._bell(760, 0.42, 0.5, sr), 0.33),
            ], sr)
        if cue == "round_start":
            return self._mix([(self._bell(820, 0.5, 0.6, sr), 0.0)], sr)
        if cue == "impact":
            # Per-shot variation so a flurry never sounds like one repeated blip.
            tone = float(np.random.uniform(120, 185))
            gain = float(np.random.uniform(0.5, 0.72))
            return self._impact(np.random.uniform(0.14, 0.2), gain, sr, tone=tone, sharpness=float(np.random.uniform(20, 27)))
        if cue == "knockdown":
            return self._mix([
                (self._impact(0.26, 0.85, sr, tone=95.0, sharpness=13.0), 0.0),
                (self._crowd(0.7, 0.5, sr, intensity=1.2, brightness=1.2, swell=0.15), 0.05),
            ], sr)
        if cue == "finish":
            return self._mix([
                (self._impact(0.22, 0.7, sr, tone=110.0, sharpness=16.0), 0.0),
                (self._crowd(1.15, 0.6, sr, intensity=1.4, brightness=1.4, swell=0.1), 0.02),
                (self._bell(700, 0.5, 0.4, sr), 0.18),
            ], sr)
        if cue == "decision":
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
        # Fallback: a neutral impact.
        return self._impact(0.16, 0.5, sr)

    def _fight_night_fallback_tone(self, cue):
        """Single (freq, ms) beep for machines without numpy/sounddevice."""
        return {
            "bout_start": (760, 150), "round_start": (820, 130), "impact": (150, 70),
            "knockdown": (95, 200), "finish": (700, 260), "decision": (560, 180),
            "card_complete": (620, 240), "preview": (740, 120),
        }.get(cue, (150, 90))

    def play_fight_night_sound(self, cue):
        """Play a short cue without blocking commentary playback or simulation."""
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return False
        now = time.monotonic()
        # A slightly shorter guard than a jab exchange so rapid strikes still land.
        if now - getattr(self, "_fight_night_last_sound_at", 0.0) < 0.06:
            return False
        self._fight_night_last_sound_at = now
        volume = max(0, min(100, int(self.rules.get("fight_night_audio_volume", 55)))) / 100
        if volume <= 0:
            return False

        def play():
            try:
                if sd is None or np is None:
                    import winsound
                    freq, ms = self._fight_night_fallback_tone(cue)
                    winsound.Beep(max(37, int(freq)), max(40, int(ms)))
                    return
                sr = self._SAMPLE_RATE
                audio = self._render_cue(cue, sr) * volume
                sd.play(audio, samplerate=sr, device=self.resolve_fight_night_output(), blocking=False)
            except Exception:
                # Device changes, unplugged headphones, and unavailable audio
                # drivers must never interrupt an event or surface a crash dialog.
                return

        threading.Thread(target=play, name="FightNightAudio", daemon=True).start()
        return True
