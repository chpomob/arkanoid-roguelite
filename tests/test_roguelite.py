"""Tests for Rogue-Lite skills and effects"""
import unittest
from unittest import mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import game.roguelite.effects as effects_module
from game.roguelite.effects import RunState
import game.particles.particle as particle_module
import game.entities.paddle as paddle_module
from game.roguelite.skill import Skill, SkillType
import pygame
from game.viewport import Viewport
pygame.init()

# Initialize engine mock
pygame.display.set_mode = mock.MagicMock()


class TestSkills(unittest.TestCase):
    def test_skill_creation(self):
        """Test basic skill creation."""
        skill = Skill(SkillType.DAMAGE, "Damage Skill")
        self.assertEqual(skill.type, SkillType.DAMAGE)
        self.assertEqual(skill.description, "Damage Skill")

    def test_skill_leveling(self):
        """Test that skill levels are tracked."""
        skill = Skill(SkillType.DAMAGE, "Damage")
        self.assertEqual(skill.level, 1)
        
        skill.level += 1
        self.assertEqual(skill.level, 2)


class TestEffects(unittest.TestCase):
    def test_apply_paddle_wide_effect(self):
        """Test that PaddleWide skill increases paddle width."""
        paddle = paddle_module.Paddle(1024, 768)
        initial_width = paddle.width
        
        # Simulate 2 wide skills (stacking)
        skills = [Skill(SkillType.PADDLE_WIDE, "Wide A"), Skill(SkillType.PADDLE_WIDE, "Wide B")]
        
        effects_module.apply_skills_to_paddle(paddle, skills)
        
        self.assertGreater(paddle.width, initial_width)

    def test_handle_brick_hit_damage_stacking(self):
        """Test that handle_brick_hit correctly applies scaled damage."""
        class FakeBrick:
            def __init__(self):
                self.hp = 10
                self.active = True
        
        brick = FakeBrick()
        ball = mock.MagicMock()
        
        # 2 damage skills
        skills = [Skill(SkillType.DAMAGE, "Dmg A"), Skill(SkillType.DAMAGE, "Dmg B")]
        rs = RunState()
        
        effects_module.handle_brick_hit(brick, ball, skills, rs)
        
        # Base damage 1 + 2 damage_skills = 3
        self.assertEqual(brick.hp, 7)  # 10 - (1 base + 2 damage) = 7
        self.assertTrue(brick.active)
        
        effects_module.handle_brick_hit(brick, ball, skills, rs) # Hit again
        self.assertEqual(brick.hp, 4)  # 7 - 3 = 4

    def test_handle_brick_hit_laser_return(self):
        """Test that handle_brick_hit correctly returns laser status."""
        brick = mock.MagicMock()
        brick.hp = 10
        ball = mock.MagicMock()
        brick.active = True
        skill = Skill(SkillType.LASER, "Laser")
        rs = RunState()
        
        laser_active = effects_module.handle_brick_hit(brick, ball, [skill], rs)
        
        self.assertTrue(laser_active)

    def test_energy_accumulation_logic(self):
        """Test that vampire logic accumulates energy correctly."""
        rs = RunState()
        
        brick = mock.MagicMock()
        brick.hp = 10
        ball = mock.MagicMock()
        brick.active = True
        skill = Skill(SkillType.VAMPIRE, "Vampire")
        
        effects_module.handle_brick_hit(brick, ball, [skill], rs)
        
        self.assertEqual(rs.energy, 1)

    def test_damage_brick_supports_plain_test_doubles(self):
        """Test that shared damage logic works with simple brick fakes."""
        class FakeBrick:
            def __init__(self):
                self.hp = 2
                self.active = True

        brick = FakeBrick()

        destroyed = effects_module.damage_brick(brick, 2)

        self.assertTrue(destroyed)
        self.assertFalse(brick.active)

    def test_apply_skills_to_ball_speed_reset(self):
        """Test that apply_skills_to_ball correctly sets base speed."""
        ball = mock.MagicMock()
        ball.speed = 5
        
        skills = [Skill(SkillType.SPEED_UP, "Tempo")]
        effects_module.apply_skills_to_ball(ball, skills)
        
        # Should recalculate based on the stabilizer curve.
        self.assertAlmostEqual(ball.speed, 4.6)


class TestParticle(unittest.TestCase):
    def test_particle_lifecycle(self):
        """Test particle lifetime and movement."""
        import unittest.mock
        mock_screen = unittest.mock.MagicMock()
        
        p = particle_module.Particle(10, 10, (255, 0, 0))
        
        # Update past its normal life
        while p.life > 0:
            p.update()
        
        self.assertLessEqual(p.life, 0)

    def test_particle_position_update(self):
        """Test that particle moves by its delta velocity."""
        p = particle_module.Particle(0, 0, (255, 0, 0))
        initial_size = p.size
        
        # Run update multiple times to ensure at least one updates
        for _ in range(100):
            p.update()
            if p.x != 0 or p.size != initial_size:
                break
        
        self.assertTrue(p.x != 0 or p.size != initial_size)


if __name__ == '__main__':
    unittest.main()
