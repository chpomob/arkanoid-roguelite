"""Tests for RunState consistency."""
import unittest
import sys
import os
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.roguelite.effects import RunState
import game.engine as engine_module


class TestModuleLevelState(unittest.TestCase):
    def test_energy_starts_at_zero(self):
        """Test that a fresh RunState starts with 0 energy."""
        rs = RunState()
        self.assertEqual(rs.energy, 0)

    def test_balls_count_starts_at_one(self):
        """Test that a fresh RunState starts with balls_count 1."""
        rs = RunState()
        self.assertEqual(rs.balls_count, 1)

    def test_engine_level_initial(self):
        """Test that a new engine starts at level 1."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            self.assertEqual(game.level, 1)


if __name__ == '__main__':
    unittest.main()
