"""Tests for Heal Skill Logic"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.paddle import Paddle
from game.roguelite.skill import Skill, SkillType
import game.roguelite.effects as effects_module


class TestHealSkill(unittest.TestCase):
    def test_apply_heal_increases_lives(self):
        """Test that HEAL skill correctly increases paddle lives."""
        paddle = Paddle(1024, 768)
        
        initial_lives = paddle.lives
        
        skills = [Skill(SkillType.HEAL, "Heal")]
        effects_module.apply_heal(paddle, skills)
        
        self.assertEqual(paddle.lives, initial_lives + 2)

    def test_apply_heal_has_max_limit(self):
        """Test that paddle lives cannot exceed 5 via heal."""
        paddle = Paddle(1024, 768)
        paddle.lives = 5 # Start at max
        
        skills = [Skill(SkillType.HEAL, "Heal")]
        effects_module.apply_heal(paddle, skills)
        
        self.assertEqual(paddle.lives, 5)

    def test_no_heal_skill_no_effect(self):
        """Test that no heal skill results in no changes."""
        paddle = Paddle(1024, 768)
        initial_lives = paddle.lives
        
        effects_module.apply_heal(paddle, [])
        
        self.assertEqual(paddle.lives, initial_lives)


if __name__ == '__main__':
    unittest.main()
