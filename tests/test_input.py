"""Tests for customizable key bindings."""
import os
import sys
import tempfile
import unittest

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.paddle import Paddle
from game.input import KeyBindings
from game.viewport import Viewport


class TestKeyBindings(unittest.TestCase):
    def test_default_bindings_include_arrows_and_wasd(self):
        """Test that movement defaults support arrows plus WASD."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bindings = KeyBindings(os.path.join(tmpdir, "keys.json"))

            self.assertIn(pygame.K_LEFT, bindings.bindings["left"])
            self.assertIn(pygame.K_a, bindings.bindings["left"])
            self.assertIn(pygame.K_RIGHT, bindings.bindings["right"])
            self.assertIn(pygame.K_d, bindings.bindings["right"])
            self.assertIn(pygame.K_UP, bindings.bindings["up"])
            self.assertIn(pygame.K_w, bindings.bindings["up"])
            self.assertIn(pygame.K_DOWN, bindings.bindings["down"])
            self.assertIn(pygame.K_s, bindings.bindings["down"])
            self.assertIn(pygame.K_g, bindings.bindings["skills"])
            self.assertIn(pygame.K_m, bindings.bindings["settings"])

    def test_custom_binding_persists(self):
        """Test that rebinding an action is saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "keys.json")
            bindings = KeyBindings(path)
            bindings.set_binding("left", 0, pygame.K_q)

            loaded = KeyBindings(path)

            self.assertIn(pygame.K_q, loaded.bindings["left"])
            self.assertNotIn(pygame.K_q, loaded.bindings["right"])

    def test_rebinding_reports_conflicts(self):
        """Test that duplicate key removal is reported to the caller."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bindings = KeyBindings(os.path.join(tmpdir, "keys.json"))

            conflicts = bindings.set_binding("left", 0, pygame.K_d)

            self.assertIn("right", conflicts)
            self.assertNotIn(pygame.K_d, bindings.bindings["right"])

    def test_paddle_uses_alternate_left_right_bindings(self):
        """Test that A and D move the paddle via configurable bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bindings = KeyBindings(os.path.join(tmpdir, "keys.json"))
            paddle = Paddle(Viewport(1024, 768))

            start_x = paddle.rect.x
            paddle.move({pygame.K_a: True}, bindings)
            self.assertLess(paddle.rect.x, start_x)

            start_x = paddle.rect.x
            paddle.move({pygame.K_d: True}, bindings)
            self.assertGreater(paddle.rect.x, start_x)


if __name__ == '__main__':
    unittest.main()
