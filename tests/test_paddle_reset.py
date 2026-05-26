"""Tests for Level Reset and Paddle Reset Logic"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.paddle import Paddle
from game.viewport import Viewport


class TestPaddleReset(unittest.TestCase):
    def test_paddle_reset_resets_lives(self):
        """Test that Paddle.reset() correctly resets lives to 3."""
        paddle = Paddle(Viewport(1024, 768))
        paddle.lives = 5
        
        paddle.reset()
        
        self.assertEqual(paddle.lives, 3)
        self.assertTrue(paddle.is_alive)

    def test_paddle_reset_keeps_width(self):
        """Test that Paddle.reset() keeps the width bonuses intact."""
        paddle = Paddle(Viewport(1024, 768))
        paddle.add_width(20)
        
        paddle.reset()
        
        self.assertEqual(paddle.width_bonus, 20)


if __name__ == '__main__':
    unittest.main()
