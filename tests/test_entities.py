"""Tests for the Paddle entity"""
import pygame
import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.paddle import Paddle


class TestPaddle(unittest.TestCase):
    def setUp(self):
        """Set up a basic Paddle for testing."""
        self.width = 1024
        self.height = 768
        self.paddle = Paddle(self.width, self.height)

    def test_initial_state(self):
        """Test that the paddle initializes with correct default properties."""
        self.assertEqual(self.paddle.lives, 3)
        self.assertTrue(self.paddle.is_alive)
        self.assertEqual(self.paddle.base_width, 100)
        self.assertEqual(self.paddle.width, 100)
        self.assertEqual(self.paddle.height, 15)
        self.assertEqual(self.paddle.speed, 11)
        self.assertEqual(self.paddle.color, (0, 228, 54))
        # Verify position based on width
        expected_x = (self.width - 100) / 2
        self.assertEqual(self.paddle.rect.x, expected_x)

    def test_move_left(self):
        """Test moving the paddle left."""
        keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        prev_x = self.paddle.rect.x
        self.paddle.move(self.width, keys)
        self.assertLess(self.paddle.rect.x, prev_x)

    def test_move_right(self):
        """Test moving the paddle right."""
        keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        prev_x = self.paddle.rect.x
        self.paddle.move(self.width, keys)
        self.assertGreater(self.paddle.rect.x, prev_x)

    def test_move_bounds_left(self):
        """Test that the paddle stops at the left edge."""
        # Move until edge
        for _ in range(200):
            self.paddle.move(self.width, {pygame.K_LEFT: True, pygame.K_RIGHT: False})
        self.assertEqual(self.paddle.rect.x, 0)

    def test_move_bounds_right(self):
        """Test that the paddle stops at the right edge."""
        for _ in range(200):
            self.paddle.move(self.width, {pygame.K_LEFT: False, pygame.K_RIGHT: True})
        self.assertEqual(self.paddle.rect.x, self.width - self.paddle.width)

    def test_reset(self):
        """Test that the paddle resets correctly."""
        self.paddle.lives = 0
        self.paddle.is_alive = False
        self.paddle.rect.x = 0
        self.paddle.rect.y = 0

        self.paddle.reset(self.width, self.height)
        self.assertEqual(self.paddle.lives, 3)
        self.assertTrue(self.paddle.is_alive)
        # Centered X
        expected_x = (self.width - self.paddle.width) / 2
        self.assertEqual(self.paddle.rect.x, expected_x)
        # Bottom Y
        self.assertEqual(self.paddle.rect.y, self.height - 40)

    def test_width_scaling(self):
        """Test that the paddle's dynamic width is handled."""
        self.paddle.add_width(20)
        self.assertEqual(self.paddle.width, 120)
        self.assertEqual(self.paddle.rect.width, 120)
        # Check if it stays centered
        expected_x = (self.width - 120) / 2
        self.assertEqual(self.paddle.rect.x, expected_x)


if __name__ == '__main__':
    unittest.main()