"""Focused regressions for fight cache cleanup and Fight Night cue concurrency."""

import itertools
import threading
import time
import unittest
from unittest import mock

import audio as audio_module
from audio import FightNightAudioMixin
from fight_engine import FightEngineMixin


class FightCacheCleanupTests(unittest.TestCase):
    def test_failed_simulation_clears_temporary_caches_before_next_fight(self):
        probe = object.__new__(FightEngineMixin)
        observed = []

        def injected_simulation(_a, _b, _fight):
            observed.append((probe._fight_skill_bundle_cache, probe._fight_finish_conversion_cache))
            if len(observed) == 1:
                probe._fight_skill_bundle_cache["failed"] = True
                probe._fight_finish_conversion_cache["failed"] = True
                raise RuntimeError("injected fight failure")
            return "second fight completed"

        probe._simulate_fight_with_caches = injected_simulation
        a, b = object(), object()

        with self.assertRaisesRegex(RuntimeError, "injected fight failure"):
            probe.simulate_fight(a, b, {})

        self.assertFalse(hasattr(probe, "_fight_skill_bundle_cache"))
        self.assertFalse(hasattr(probe, "_fight_finish_conversion_cache"))
        self.assertEqual(probe.simulate_fight(a, b, {}), "second fight completed")
        self.assertEqual(len(observed), 2)
        self.assertEqual(observed[1], ({}, {}))

    def test_failed_simulation_restores_preexisting_cache_objects(self):
        probe = object.__new__(FightEngineMixin)
        old_bundle = {"old": 1}
        old_conversion = {"old": 2}
        probe._fight_skill_bundle_cache = old_bundle
        probe._fight_finish_conversion_cache = old_conversion

        def injected_simulation(_a, _b, _fight):
            probe._fight_skill_bundle_cache["new"] = 1
            probe._fight_finish_conversion_cache["new"] = 2
            raise ValueError("cache failure")

        probe._simulate_fight_with_caches = injected_simulation
        with self.assertRaisesRegex(ValueError, "cache failure"):
            probe.simulate_fight(object(), object(), {})

        self.assertIs(probe._fight_skill_bundle_cache, old_bundle)
        self.assertIs(probe._fight_finish_conversion_cache, old_conversion)
        self.assertEqual(old_bundle, {"old": 1})
        self.assertEqual(old_conversion, {"old": 2})


class AudioCueConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.probe = object.__new__(FightNightAudioMixin)
        self.probe.rules = {
            "fight_night_audio_enabled": True,
            "fight_night_audio_output": self.probe.AUDIO_DEFAULT,
            "fight_night_audio_volume": 55,
        }

    def test_audio_lock_initialization_is_stable_under_concurrency(self):
        locks = []
        barrier = threading.Barrier(24)

        def worker():
            barrier.wait()
            locks.append(self.probe._ensure_fight_night_audio_runtime())

        threads = [threading.Thread(target=worker) for _ in range(24)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(locks), 24)
        self.assertEqual(len({id(lock) for lock in locks}), 1)
        self.assertIs(locks[0], self.probe._fight_night_audio_lock)
        self.assertEqual(self.probe._fight_night_active_cues, 0)

    def test_concurrent_cues_are_bounded_and_always_release(self):
        playback_started = threading.Event()
        release_playback = threading.Event()
        self.probe._render_cue = lambda _cue, _sample_rate: [0.0]

        def fake_playback(_samples, _volume, _device):
            playback_started.set()
            release_playback.wait(timeout=2)

        self.probe._play_fight_night_samples = fake_playback
        self.probe._choose_crowd_audio = lambda _cue: None
        self.probe.resolve_fight_night_output = lambda: None
        start_times = itertools.count(100)
        accepted = []

        def play_one():
            accepted.append(self.probe.play_fight_night_sound("test-cue"))

        with mock.patch.object(audio_module.time, "monotonic", side_effect=lambda: next(start_times)):
            threads = [threading.Thread(target=play_one) for _ in range(12)]
            for thread in threads:
                thread.start()
            self.assertTrue(playback_started.wait(timeout=2))
            for thread in threads:
                thread.join(timeout=2)

        self.assertEqual(sum(accepted), self.probe._MAX_SIMULTANEOUS_CUES)
        self.assertEqual(self.probe._fight_night_active_cues, self.probe._MAX_SIMULTANEOUS_CUES)
        release_playback.set()
        deadline = time.monotonic() + 2
        while self.probe._fight_night_active_cues and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.probe._fight_night_active_cues, 0)


if __name__ == "__main__":
    unittest.main()
