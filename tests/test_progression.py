"""Tests for Level Progression and Skill Selection"""
import unittest
from unittest import mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pygame
from game.entities.brick import Brick, BrickKind
import game.engine as engine_module
import game.roguelite.effects as effects_module


class TestLevelProgression(unittest.TestCase):
    def test_next_level_triggers_level_summary(self):
        """Test that clearing bricks triggers the level summary before skill selection."""
        # Mock pygame display for initialization
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            
            # Verify start state
            self.assertEqual(game.state, "PLAYING")
            
            # Clear all bricks to trigger level end
            game.brick_grid.bricks = []
            
            # Update once to trigger the logic
            game.update(1/60)
            
            # State should have changed
            self.assertEqual(game.state, "LEVEL_SUMMARY")
            self.assertIsNotNone(game.last_level_summary)
            self.assertIsNotNone(game.skill_cards)

    def test_next_level_increments_level_number(self):
        """Test that the level number increments correctly after clearing."""
        with mock.patch('pygame.display.set_mode'):
            initial_level = 1
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            # Manually set level if it was 0 or 1 initially
            game.level = initial_level
            
            game.brick_grid.bricks = []
            game.update(1/60)
            
            self.assertEqual(game.level, initial_level + 1)


class TestSpecialBrickEffects(unittest.TestCase):
    def test_bomb_brick_damages_nearby_bricks(self):
        """Test that bomb bricks damage nearby bricks when destroyed."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            bomb = Brick(pygame.Rect(100, 100, 40, 20), hp=1, kind=BrickKind.BOMB)
            nearby = Brick(pygame.Rect(150, 100, 40, 20), hp=2)
            far = Brick(pygame.Rect(300, 100, 40, 20), hp=2)
            game.brick_grid.bricks = [bomb, nearby, far]

            bomb.take_damage(1)
            game.handle_special_brick_effects(bomb, destroyed=True)

            self.assertEqual(nearby.hp, 1)
            self.assertEqual(far.hp, 2)

    def test_pulse_brick_changes_ball_angle(self):
        """Test that pulse bricks add a small directional kick."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            pulse = Brick(pygame.Rect(100, 100, 40, 20), hp=2, kind=BrickKind.PULSE)
            ball = game.balls[0]
            ball.rect.centerx = pulse.rect.right + 5
            ball.dx = 0

            game.handle_special_brick_effects(pulse, ball, destroyed=False)

            self.assertGreater(ball.dx, 0)

    def test_charge_brick_adds_energy_on_destroy(self):
        """Test that charge bricks reward energy without requiring a skill."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            charge = Brick(pygame.Rect(100, 100, 40, 20), hp=1, kind=BrickKind.CHARGE)
            game.run_state.energy = 0

            charge.take_damage(1)
            game.handle_special_brick_effects(charge, destroyed=True)

            self.assertEqual(game.run_state.energy, 2)

    def test_regen_brick_repairs_nearby_brick(self):
        """Test that regen bricks can repair damaged neighbors."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            regen = Brick(pygame.Rect(100, 100, 40, 20), hp=2, kind=BrickKind.REGEN)
            damaged = Brick(pygame.Rect(145, 100, 40, 20), hp=3)
            damaged.hp = 1
            game.brick_grid.bricks = [regen, damaged]

            repaired = game.repair_nearby_brick(regen)

            self.assertTrue(repaired)
            self.assertEqual(damaged.hp, 2)

    def test_prism_brick_splits_ball_on_destroy(self):
        """Test that prism bricks create an extra ball when destroyed by a ball."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            prism = Brick(pygame.Rect(100, 100, 40, 20), hp=1, kind=BrickKind.PRISM)
            ball = game.balls[0]

            prism.take_damage(1)
            game.handle_special_brick_effects(prism, ball, destroyed=True)

            self.assertEqual(len(game.balls), 2)

    def test_sentry_brick_spawns_enemy_on_destroy(self):
        """Test that sentry bricks add a moving enemy pressure source."""
        with mock.patch('pygame.display.set_mode'):
            game = engine_module.GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            sentry = Brick(pygame.Rect(100, 100, 40, 20), hp=1, kind=BrickKind.SENTRY)

            sentry.take_damage(1)
            game.handle_special_brick_effects(sentry, destroyed=True)

            self.assertEqual(len(game.enemies), 1)


if __name__ == '__main__':
    unittest.main()
