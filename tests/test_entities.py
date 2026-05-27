"""Tests for the Paddle entity — viewport-normalized."""
import pygame
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.paddle import Paddle


class TestPaddle(unittest.TestCase):
    def setUp(self):
        self.width = 1024
        self.height = 768
        self.vp = Viewport(self.width, self.height)
        self.paddle = Paddle(self.vp)

    def test_initial_state(self):
        self.assertEqual(self.paddle.lives, 3)
        self.assertTrue(self.paddle.is_alive)
        self.assertAlmostEqual(self.paddle.base_nw, 100 / 1024, places=4)
        self.assertAlmostEqual(self.paddle.nw, 100 / 1024, places=4)
        self.assertAlmostEqual(self.paddle.nh, 15 / 768, places=4)
        self.assertAlmostEqual(self.paddle.speed, self.vp.nspeed(7), places=3)
        self.assertEqual(self.paddle.color, (0, 228, 54))
        expected_x = self.vp.px(0.5 - self.paddle.nw / 2)
        self.assertEqual(self.paddle.rect.x, expected_x)

    def test_move_left(self):
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        prev_x = self.paddle.rect.x
        self.paddle.move(keys)
        self.assertLess(self.paddle.rect.x, prev_x)

    def test_move_right(self):
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        prev_x = self.paddle.rect.x
        self.paddle.move(keys)
        self.assertGreater(self.paddle.rect.x, prev_x)

    def test_move_bounds_left(self):
        for _ in range(200):
            self.paddle.move({pygame.K_LEFT: True, pygame.K_RIGHT: False})
        self.assertEqual(self.paddle.rect.x, 0)

    def test_move_bounds_right(self):
        for _ in range(200):
            self.paddle.move({pygame.K_LEFT: False, pygame.K_RIGHT: True})
        max_x = int(self.vp.w) - self.paddle.rect.width
        self.assertAlmostEqual(self.paddle.rect.x, max_x, delta=2)

    def test_reset(self):
        self.paddle.lives = 0
        self.paddle.is_alive = False
        self.paddle.rect.x = 0
        self.paddle.rect.y = 0

        self.paddle.reset()
        self.assertEqual(self.paddle.lives, 3)
        self.assertTrue(self.paddle.is_alive)
        expected_x = self.vp.px(0.5 - self.paddle.nw / 2)
        self.assertEqual(self.paddle.rect.x, expected_x)
        expected_y = self.vp.py(1.0 - self.vp.legacy_y(40) - self.paddle.nh)
        self.assertEqual(self.paddle.rect.y, expected_y)

    def test_width_scaling(self):
        self.paddle.add_width(20 / 1024)  # normalized bonus
        self.assertAlmostEqual(self.paddle.nw, 120 / 1024, places=4)
