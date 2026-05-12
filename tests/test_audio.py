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


if __name__ == '__main__':
    unittest.main()
