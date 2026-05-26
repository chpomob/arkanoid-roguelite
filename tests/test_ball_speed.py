"""Tests for Ball Speed Modification Logic"""
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


class TestBallSpeedModification(unittest.TestCase):
    def test_tempo_skill_slows_ball(self):
        """Test that Tempo Stabilizer lowers ball speed."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_speed = ball.speed
        
        skills = [Skill(SkillType.SPEED_UP, "Tempo")]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertLess(ball.speed, initial_speed)
        self.assertGreaterEqual(ball.speed, 3.0)

    def test_control_skill_increases_aiming_range(self):
        """Test that CONTROL skill improves paddle aiming."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_angle = ball.max_bounce_angle
        initial_nudge = ball.center_nudge
        
        skills = [Skill(SkillType.CONTROL, "Control")]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertGreater(ball.max_bounce_angle, initial_angle)
        self.assertGreater(ball.center_nudge, initial_nudge)

    def test_heavy_ball_skill_increases_size(self):
        """Test that GIANT_BALL skill correctly increases ball size."""
        paddle = Paddle(Viewport(1024, 768))
        ball = Ball(Viewport(1024, 768), paddle)
        
        initial_size = ball.nsize
        
        skills = [Skill(SkillType.GIANT_BALL, "Heavy Ball")]
        effects_module.apply_skills_to_ball(ball, skills)
        
        self.assertGreater(ball.nsize, initial_size)
        self.assertLessEqual(ball.nsize, 24)


if __name__ == '__main__':
    unittest.main()
