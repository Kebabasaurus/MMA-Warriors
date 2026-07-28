"""Procedural, non-blocking audio cues for the live fight-night presentation.

The cues are synthesised with Python's standard library, written to tiny
temporary WAV files, and played through the Windows default output. Any audio
failure is swallowed so it can never interrupt an event.
"""

import math
import os
import queue
import random
import re
import struct
import tempfile
import threading
import time
import wave

try:
    import ctypes
    from ctypes import wintypes
except Exception:
    ctypes = None
    wintypes = None


class FightNightAudioMixin:
    AUDIO_DEFAULT = "System default"
    _SAMPLE_RATE = 32000

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
        self.rules.setdefault("fight_night_audio_volume", 55)

    def fight_night_audio_status(self):
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return "Off"
        return str(self.rules.get("fight_night_audio_output", self.AUDIO_DEFAULT))

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
                sample += random.uniform(-0.4, 0.4)
            wave_data[i] = sample * gain
        return wave_data

    def _smooth_noise(self, frame_count, kernel):
        noise = [random.uniform(-1.0, 1.0) for _ in range(frame_count)]
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
        if cue == "bout_start":
            return self._mix([
                (self._crowd(0.85, 0.30, sr, intensity=0.9, brightness=0.8, swell=0.6), 0.0),
                (self._bell(760, 0.34, 0.5, sr), 0.05),
                (self._bell(760, 0.42, 0.5, sr), 0.33),
            ], sr)
        if cue == "round_start":
            return self._mix([(self._bell(820, 0.5, 0.6, sr), 0.0)], sr)
        if cue == "impact":
            tone = random.uniform(120, 185)
            gain = random.uniform(0.5, 0.72)
            return self._impact(random.uniform(0.14, 0.2), gain, sr, tone=tone, sharpness=random.uniform(20, 27))
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
        return self._impact(0.16, 0.5, sr)

    def _fight_night_fallback_tone(self, cue):
        """Single (freq, ms) beep if WAV playback is unavailable."""
        return {
            "bout_start": (760, 150), "round_start": (820, 130), "impact": (150, 70),
            "knockdown": (95, 200), "finish": (700, 260), "decision": (560, 180),
            "card_complete": (620, 240), "preview": (740, 120),
        }.get(cue, (150, 90))

    def _write_fight_night_wav(self, samples, volume):
        audio_dir = os.path.join(tempfile.gettempdir(), "mma_warriors_audio")
        os.makedirs(audio_dir, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(prefix="cue_", suffix=".wav", dir=audio_dir, delete=False)
        path = handle.name
        handle.close()
        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample * volume))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._SAMPLE_RATE)
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

    def _play_fight_night_samples(self, samples, volume, device_index=None):
        if ctypes is None or wintypes is None:
            path = self._write_fight_night_wav(samples, volume)
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

        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample * volume))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        data = ctypes.create_string_buffer(bytes(frames))
        fmt = WAVEFORMATEX(
            WAVE_FORMAT_PCM,
            1,
            self._SAMPLE_RATE,
            self._SAMPLE_RATE * 2,
            2,
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
            deadline = time.monotonic() + max(1.0, len(samples) / self._SAMPLE_RATE + 1.0)
            while not (header.dwFlags & WHDR_DONE) and time.monotonic() < deadline:
                time.sleep(0.01)
            winmm.waveOutReset(handle)
        finally:
            if prepared:
                try:
                    winmm.waveOutUnprepareHeader(handle, ctypes.byref(header), ctypes.sizeof(header))
                except Exception:
                    pass
            winmm.waveOutClose(handle)

    def play_fight_night_sound(self, cue):
        """Play a short cue without blocking commentary playback or simulation."""
        self.ensure_audio_defaults()
        if not self.rules.get("fight_night_audio_enabled", True):
            return False
        now = time.monotonic()
        if now - getattr(self, "_fight_night_last_sound_at", 0.0) < 0.10:
            return False
        self._fight_night_last_sound_at = now
        volume = max(0, min(100, int(self.rules.get("fight_night_audio_volume", 55)))) / 100
        if volume <= 0:
            return False
        if not hasattr(self, "_fight_night_audio_queue"):
            self._fight_night_audio_queue = queue.Queue(maxsize=6)

            def worker():
                while True:
                    queued_cue, queued_volume, device = self._fight_night_audio_queue.get()
                    try:
                        samples = self._render_cue(queued_cue, self._SAMPLE_RATE)
                        self._play_fight_night_samples(samples, queued_volume, device)
                    except Exception:
                        try:
                            import winsound
                            freq, ms = self._fight_night_fallback_tone(queued_cue)
                            winsound.Beep(max(37, int(freq)), max(40, int(ms)))
                        except Exception:
                            pass
                    finally:
                        self._fight_night_audio_queue.task_done()

            threading.Thread(target=worker, name="FightNightAudio", daemon=True).start()
        try:
            self._fight_night_audio_queue.put_nowait((cue, volume, self.resolve_fight_night_output()))
        except queue.Full:
            return False
        return True
