"""Tests for Ball behavior — viewport-normalized."""
import math
import unittest
import sys
import os
import pygame
pygame.init()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.ball import Ball
from game.entities.paddle import Paddle


class TestBall(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(1024, 768)
        self.paddle = Paddle(self.vp)
        self.ball = Ball(self.vp, self.paddle)

    def test_ball_initialization(self):
        ball = Ball(self.vp, self.paddle)
        self.assertTrue(ball.active)
        self.assertAlmostEqual(ball.nsize, self.vp.legacy_s(12), places=5)
        self.assertEqual(ball.nx, 0.5)
        self.assertAlmostEqual(ball.ny, 0.5, places=2)

    def test_wall_bounce_syncs_float_position(self):
        ball = Ball(self.vp, self.paddle)
        # Place ball at right wall
        ball.nx = self.vp.legacy_x(800 - 2)
        ball.ny = self.vp.legacy_y(300)
        ball.sync_rect_to_position()
        ball.ndx = self.vp.nspeed(12)
        ball.ndy = 0

        ball.move(self.vp.legacy_y(0))

        # Should bounce (ndx becomes negative)
        self.assertLess(ball.ndx, 0)
        self.assertEqual(ball.rect.right, int(self.vp.w))
        # Normalized x should match projected rect center
        self.assertAlmostEqual(self.vp.px(ball.nx), ball.rect.centerx, delta=1)

    def test_wall_bounce_only_reverses_when_moving_into_wall(self):
        ball = Ball(self.vp, self.paddle)
        ball.rect.left = 0
        ball.nx = self.vp.from_screen(*ball.rect.center)[0]
        ball.ny = self.vp.from_screen(*ball.rect.center)[1]
        ball.ndx = -self.vp.nspeed(3)

        ball.move(self.vp.legacy_y(0))

        # Ball should NOT reverse — it was already moving away from wall
        self.assertGreater(ball.ndx, 0)

    def test_shallow_left_wall_exit_does_not_stick_to_side(self):
        ball = Ball(self.vp, self.paddle)
        ball.rect.left = 1
        ball.nx = self.vp.from_screen(*ball.rect.center)[0]
        ball.ny = self.vp.from_screen(*ball.rect.center)[1]
        ball.ndx = -self.vp.nspeed(0.4)

        ball.move(self.vp.legacy_y(0))

        self.assertLess(ball.rect.left, 0)  # should not be clamped if still overlapping
