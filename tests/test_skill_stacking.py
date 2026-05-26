"""Tests for Stacked Skill Modifications"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.viewport import Viewport
from game.entities.ball import Ball
from game.entities.paddle import Paddle
from game.roguelite.skill import Skill, SkillType
import game.roguelite.effects as effects_module
from game.viewport import Viewport


class TestStackedSkills(unittest.TestCase):
    def test_stacked_tempo_skills(self):
        """Test that Tempo Stabilizer skills stack with a floor."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_speed = ball.speed
        
        skills = [
            Skill(SkillType.SPEED_UP, "Tempo"),
            Skill(SkillType.SPEED_UP, "Tempo")
        ]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertLess(ball.speed, initial_speed)
        self.assertGreaterEqual(ball.speed, 3.0)

    def test_stacked_heavy_ball_and_tempo(self):
        """Test that heavy ball and tempo upgrades both apply."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_speed = ball.speed
        initial_size = ball.nsize
        
        skills = [
            Skill(SkillType.SPEED_UP, "Tempo"),
            Skill(SkillType.GIANT_BALL, "Heavy Ball")
        ]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertLess(ball.speed, initial_speed)
        self.assertGreater(ball.nsize, initial_size)

    def test_multiple_heavy_ball_skills_stack(self):
        """Test that heavy ball skills stack to increase coverage."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_size = ball.nsize
        
        skills = [
            Skill(SkillType.GIANT_BALL, "Heavy 1"),
            Skill(SkillType.GIANT_BALL, "Heavy 2")
        ]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertEqual(ball.nsize, initial_size + 6)


if __name__ == '__main__':
    unittest.main()
