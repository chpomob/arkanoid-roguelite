"""Tests for Control skill behavior."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import game.roguelite.effects as effects_module
from game.roguelite.effects import RunState
from game.roguelite.skill import Skill, SkillType


class TestControlSkill(unittest.TestCase):
    def test_control_applies_to_all_balls(self):
        """Test that Control improves every active ball."""
        engine = mock.MagicMock()
        engine.viewport.w = 1024
        engine.viewport.h = 768
        engine.paddle.rect = mock.MagicMock()

        balls = []
        for center in ((100, 100), (120, 100)):
            ball = mock.MagicMock()
            ball.speed = 5
            ball.base_nsize = 12
            ball.nsize = 12
            ball.nx, ball.ny = center
            ball.rect.center = center
            ball.rect.nsize = (12, 12)
            ball.max_bounce_angle = 1.0
            ball.center_nudge = 0.13
            balls.append(ball)

        engine.balls = balls
        rs = RunState()
        effects_module.handle_skills(engine, [Skill(SkillType.CONTROL, "Control")], rs)

        self.assertTrue(all(ball.max_bounce_angle > 1.0 for ball in balls))


if __name__ == '__main__':
    unittest.main()
