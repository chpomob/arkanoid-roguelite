"""Tests for Multi-Ball skill logic"""
import unittest
import sys
import os
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import game.roguelite.effects as effects_module
from game.roguelite.effects import RunState
from game.roguelite.skill import Skill, SkillType

class TestMultiBallSkill(unittest.TestCase):
    def test_handle_skills_multi_ball_creates_balls(self):
        """Test that Multi-Ball skill correctly appends new balls to the engine."""
        engine = mock.MagicMock()
        engine.viewport.w = 1024
        engine.viewport.h = 768
        engine.paddle.rect = mock.MagicMock()
        engine.balls = []
        
        # Create a Multi-Ball skill
        skill = Skill(SkillType.MULTI_BALL, "Extra Ball")
        
        # Apply the skill
        rs = RunState()
        effects_module.handle_skills(engine, [skill], rs)
        
        # Verify that exactly one ball was added (since we passed one skill)
        self.assertEqual(len(engine.balls), 1)
        
        # Verify properties of the new ball
        new_ball = engine.balls[0]
        self.assertTrue(hasattr(new_ball, 'active'))
        self.assertTrue(new_ball.active)
        self.assertTrue(hasattr(new_ball, 'speed'))

    def test_handle_skills_multi_ball_stack(self):
        """Test that applying multiple Multi-Ball skills creates more balls."""
        engine = mock.MagicMock()
        engine.viewport.w = 1024
        engine.viewport.h = 768
        engine.paddle.rect = mock.MagicMock()
        engine.balls = []
        
        skill1 = Skill(SkillType.MULTI_BALL, "Ball A")
        skill2 = Skill(SkillType.MULTI_BALL, "Ball B")
        rs = RunState()
        
        effects_module.handle_skills(engine, [skill1, skill2], rs)
        
        # With two Multi-Ball skills, we expect 2 balls to be added
        self.assertEqual(len(engine.balls), 2)

    def test_balls_count_increases_with_multi_ball(self):
        """Test that balls_count correctly tracks the total number of active balls."""
        rs = RunState()
        
        engine = mock.MagicMock()
        engine.viewport.w = 1024
        engine.viewport.h = 768
        engine.paddle.rect = mock.MagicMock()
        engine.balls = []
        
        skill = Skill(SkillType.MULTI_BALL, "Extra Ball")
        effects_module.handle_skills(engine, [skill], rs)
        
        # balls_count should have increased by 1
        self.assertEqual(rs.balls_count, 2)


class TestVampireEnergy(unittest.TestCase):
    def test_energy_decreases_on_heal(self):
        """Test that energy decreases when a heal is triggered."""
        paddle = mock.MagicMock()
        paddle.lives = 1
        result_energy = effects_module.apply_vampire(paddle, 15)
        
        self.assertEqual(result_energy, 7)
        self.assertEqual(paddle.lives, 2)

    def test_energy_does_nothing_if_below_threshold(self):
        """Test that energy does nothing when below the heal threshold."""
        paddle = mock.MagicMock()
        paddle.lives = 1
        
        result_energy = effects_module.apply_vampire(paddle, 7)
        
        self.assertEqual(result_energy, 7)
        self.assertEqual(paddle.lives, 1)

    def test_energy_heals_at_threshold(self):
        """Test that vampire healing triggers at the 8-energy threshold."""
        paddle = mock.MagicMock()
        paddle.lives = 1

        result_energy = effects_module.apply_vampire(paddle, 8)

        self.assertEqual(result_energy, 0)
        self.assertEqual(paddle.lives, 2)


if __name__ == '__main__':
    unittest.main()
