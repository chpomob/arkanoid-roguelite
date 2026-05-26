"""Tests for Ball behavior"""
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
    def test_ball_init(self):
        """Test basic ball initialization."""
        width, height = 1024, 768
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        
        self.assertIsNotNone(ball.rect)
        self.assertEqual(ball.color, (255, 0, 255))
        self.assertTrue(ball.active)

    def test_ball_move_and_bounce(self):
        """Test that ball movement and wall bouncing work as intended."""
        width, height = 1024, 768
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        
        # Ensure the ball is moving to the right for this specific test
        ball.ndx = abs(ball.ndx) if ball.ndx != 0 else 5
        ball.ndy = -ball.speed

        # Check initial state
        self.assertGreater(ball.ndx, 0)
        self.assertLess(ball.ndy, 0) # Moving up initially
        
        # Move ball until it hits the right wall
        while ball.rect.right < width:
            ball.move(width, height)
        
        # Trigger one more move to hit the wall
        ball.move(width, height)
        
        # Now it should have bounced
        self.assertLess(ball.ndx, 0)

    def test_wall_bounce_syncs_float_position(self):
        """Test that side-wall bounces do not leave stale off-screen coordinates."""
        width, height = 800, 600
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        ball.nx = width - 2
        ball.ny = 300
        ball.rect.center = (int(ball.nx), int(ball.ny))
        ball.ndx = 12
        ball.ndy = 0

        ball.move(width, height)

        self.assertLess(ball.ndx, 0)
        self.assertEqual(ball.rect.right, width)
        self.assertEqual(ball.nx, ball.rect.centerx)

    def test_wall_bounce_only_reverses_when_moving_into_wall(self):
        """Test that a clamped edge position does not flip an alre.ndy escaping ball."""
        width, height = 800, 600
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        ball.rect.left = 0
        ball.nx = ball.rect.centerx
        ball.ny = ball.rect.centery
        ball.ndx = 3
        ball.ndy = 0

        ball.move(width, height)

        self.assertGreater(ball.ndx, 0)

    def test_shallow_left_wall_exit_does_not_stick_to_side(self):
        """Test that shallow positive horizontal motion escapes the left wall."""
        width, height = 800, 600
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        ball.rect.left = 0
        ball.nx = ball.rect.centerx
        ball.ny = 300
        ball.rect.centery = ball.ny
        ball.ndx = 0.5
        ball.ndy = 6

        ball.move(width, height)

        self.assertGreater(ball.rect.left, 0)
        self.assertGreaterEqual(ball.ndx, ball.min_horizontal_speed)

    def test_shallow_wall_bounce_separates_next_frame(self):
        """Test that a shallow side bounce moves away from the wall on the next frame."""
        width, height = 800, 600
        paddle = Paddle(Viewport(width, height))
        ball = Ball(Viewport(width, height), paddle)
        ball.nx = width - 3
        ball.ny = 300
        ball.rect.center = (int(ball.nx), int(ball.ny))
        ball.ndx = 0.25
        ball.ndy = 6

        ball.move(width, height)
        self.assertLess(ball.ndx, 0)
        self.assertEqual(ball.rect.right, width)

        ball.move(width, height)

        self.assertLess(ball.rect.right, width)
        self.assertLessEqual(ball.ndx, -ball.min_horizontal_speed)


if __name__ == '__main__':
    unittest.main()
