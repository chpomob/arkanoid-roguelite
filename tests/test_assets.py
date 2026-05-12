"""Tests for procedural UI/game assets."""
import os
import sys
import unittest

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.assets import (
    draw_ball_sprite,
    draw_boss_sprite,
    draw_brick_sprite,
    draw_life,
    draw_paddle_sprite,
    draw_projectile_sprite,
    draw_skill_icon,
)
from game.bosses import boss_by_id
from game.ui import draw_background


class TestProceduralAssets(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.surface = pygame.Surface((180, 120), pygame.SRCALPHA)

    def assert_surface_has_pixels(self):
        alpha_bounds = self.surface.get_bounding_rect()
        self.assertGreater(alpha_bounds.width, 0)
        self.assertGreater(alpha_bounds.height, 0)

    def test_draw_gameplay_assets(self):
        """Test that core gameplay assets render non-empty pixels."""
        draw_paddle_sprite(self.surface, pygame.Rect(20, 80, 80, 14), (0, 228, 138))
        draw_ball_sprite(self.surface, pygame.Rect(80, 38, 14, 14), (255, 64, 198), [(72, 42)])
        draw_brick_sprite(self.surface, pygame.Rect(12, 12, 62, 20), (255, 214, 90), "bomb", 2, 3)
        draw_projectile_sprite(self.surface, pygame.Rect(132, 40, 5, 14), (68, 214, 255))
        draw_boss_sprite(self.surface, pygame.Rect(42, 46, 92, 42), (255, 86, 86), (255, 188, 66), 0.5)

        self.assert_surface_has_pixels()

    def test_draw_boss_background(self):
        """Test that boss backgrounds render without needing image assets."""
        surface = pygame.Surface((180, 120))

        draw_background(surface, boss_by_id("gate_sentinel"))

        self.assertNotEqual(surface.get_at((4, 4))[:3], (0, 0, 0))

    def test_draw_special_brick_markers(self):
        """Test that every special marker renders without crashing."""
        markers = ("tough", "bomb", "pulse", "charge", "regen", "prism", "sentry")
        for index, marker in enumerate(markers):
            rect = pygame.Rect(8 + (index % 3) * 56, 8 + (index // 3) * 34, 48, 22)
            draw_brick_sprite(self.surface, rect, (255, 214, 90), marker, 1, 1)

        self.assert_surface_has_pixels()

    def test_draw_ui_assets(self):
        """Test that skill and life icons render non-empty pixels."""
        draw_skill_icon(self.surface, pygame.Rect(20, 20, 42, 42), "SHD", (68, 214, 255))
        draw_life(self.surface, (100, 42), (0, 228, 138))

        self.assert_surface_has_pixels()


if __name__ == '__main__':
    unittest.main()
