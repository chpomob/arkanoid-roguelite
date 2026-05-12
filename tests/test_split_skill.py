"""Tests for Blast Skill Logic"""
import unittest
import sys
import os
from unittest import mock
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.brick import Brick
from game.roguelite.skill import Skill, SkillType
import game.roguelite.effects as effects_module


class TestBlastSkill(unittest.TestCase):
    def test_blast_damages_nearby_bricks(self):
        """Test that Blast cross-pattern deals double damage to adjacent bricks."""
        source = Brick(pygame.Rect(100, 100, 20, 20), hp=2)
        nearby = Brick(pygame.Rect(140, 100, 20, 20), hp=3)
        far = Brick(pygame.Rect(260, 100, 20, 20), hp=2)

        engine = mock.MagicMock()
        engine.brick_grid.bricks = [source, nearby, far]
        engine.brick_grid.brick_width = 20
        engine.brick_grid.brick_height = 20
        engine.brick_grid.padding = 10

        damaged = effects_module.apply_explosive(engine, source, [Skill(SkillType.EXPLOSIVE, "Blast")])

        self.assertIn(nearby, damaged)
        self.assertEqual(nearby.hp, 1)  # cross-pattern: 2 damage (hp 3→1)
        self.assertNotIn(far, damaged)   # outside cross-pattern and circular range
        self.assertEqual(far.hp, 2)

    def test_blast_stacks_adds_chain_reactions(self):
        """Test that stacked Blast triggers chain reactions from destroyed bricks."""
        source = Brick(pygame.Rect(100, 100, 20, 20), hp=2)
        victim = Brick(pygame.Rect(140, 100, 20, 20), hp=1)  # cross-pattern: 2 dmg → destroyed
        chain_target = Brick(pygame.Rect(170, 100, 20, 20), hp=3)  # closer for reduced radius

        engine = mock.MagicMock()
        engine.brick_grid.bricks = [source, victim, chain_target]
        engine.brick_grid.brick_width = 20
        engine.brick_grid.brick_height = 20
        engine.brick_grid.padding = 10

        # Seed 1 triggers the 60% chain reaction (random() = 0.134)
        import random
        random.seed(1)

        damaged = effects_module.apply_explosive(
            engine,
            source,
            [Skill(SkillType.EXPLOSIVE, "Blast 1"), Skill(SkillType.EXPLOSIVE, "Blast 2")]
        )

        self.assertIn(victim, damaged)
        self.assertFalse(victim.active)  # destroyed by cross-pattern
        self.assertIn(chain_target, damaged)  # caught by chain reaction splash
        self.assertEqual(chain_target.hp, 2)  # chain splash: 1 damage (hp 3→2)


if __name__ == '__main__':
    unittest.main()
