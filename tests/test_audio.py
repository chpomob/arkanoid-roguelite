"""Tests for procedural audio safety."""
import os
import sys
import unittest
from unittest import mock

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.audio import SoundManager


class TestSoundManager(unittest.TestCase):
    def test_disabled_audio_is_safe_to_play(self):
        """Test that disabled audio behaves as a no-op."""
        audio = SoundManager(enabled=False)

        audio.play("brick")
        audio.play("missing")
        audio.set_volume(2)
        audio.set_muted(True)

        self.assertFalse(audio.enabled)
        self.assertEqual(audio.volume, 1.0)
        self.assertTrue(audio.muted)
        self.assertEqual(audio.sounds, {})

    def test_audio_device_failure_disables_sound(self):
        """Test that missing mixer/audio devices do not crash the game."""
        with mock.patch("pygame.mixer.get_init", return_value=None), \
             mock.patch("pygame.mixer.init", side_effect=pygame.error("no device")):
            audio = SoundManager()

        self.assertFalse(audio.enabled)

    def test_pitch_notes_scales_frequency_only(self):
        """Test that pitch variants preserve timing while changing frequency."""
        notes = [(100, 0.1, 0.2)]

        pitched = SoundManager.pitch_notes(notes, 1.5)

        self.assertEqual(pitched, [(150, 0.1, 0.2)])

    def test_rapid_projectile_sound_is_throttled(self):
        """Test that rapid repeated projectile sounds are rate-limited."""
        audio = SoundManager(enabled=False)
        sound = mock.Mock()
        audio.enabled = True
        audio.sounds = {"projectile": [sound]}
        times = iter([10.0, 10.01, 10.05])
        current = [10.05]

        def monotonic():
            try:
                current[0] = next(times)
            except StopIteration:
                pass
            return current[0]

        with mock.patch("game.audio.time.monotonic", side_effect=monotonic):
            audio.play("projectile")
            audio.play("projectile")
            audio.play("projectile")

        self.assertEqual(sound.play.call_count, 2)

    def test_repeated_same_volume_does_not_call_set_volume_again(self):
        """Test that cached volume avoids redundant mixer calls."""
        audio = SoundManager(enabled=False)
        sound = mock.Mock()
        audio.enabled = True
        audio.sounds = {"brick": [sound]}

        audio.play("brick", 0.5)
        audio.play("brick", 0.5)

        self.assertEqual(sound.play.call_count, 2)
        self.assertEqual(sound.set_volume.call_count, 1)


if __name__ == '__main__':
    unittest.main()
