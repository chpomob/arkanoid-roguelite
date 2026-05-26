"""Tests for the Brick entities"""
import pygame
from game.viewport import Viewport
import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.brick import BRICK_KIND_INFO, Brick, BrickGrid, BrickKind


class TestBrick(unittest.TestCase):
    def test_initial_state(self):
        """Test a new brick's properties."""
        rect = pygame.Rect(0, 0, 20, 20)
        brick = Brick(rect)
        self.assertEqual(brick.hp, 1)
        self.assertTrue(brick.active)
        self.assertIsNotNone(brick.color)
        self.assertEqual(brick.kind, BrickKind.NORMAL)

    def test_damage(self):
        """Test that bricks take damage."""
        rect = pygame.Rect(0, 0, 20, 20)
        brick = Brick(rect, hp=3)
        self.assertTrue(brick.active)
        
        # Take 1 damage
        brick.take_damage(1)
        self.assertEqual(brick.hp, 2)
        self.assertTrue(brick.active)
        
        # Take 2 more damage
        brick.take_damage(2)
        self.assertFalse(brick.active)

    def test_reset(self):
        """Test the brick reset functionality."""
        rect = pygame.Rect(0, 0, 20, 20)
        brick = Brick(rect, hp=1)
        brick.take_damage(1)
        self.assertFalse(brick.active)
        
        brick.reset()
        self.assertTrue(brick.active)
        self.assertEqual(brick.hp, 1)


class TestBrickGrid(unittest.TestCase):
    def test_grid_generation(self):
        """Test that the brick grid generates correctly."""
        width, height = 1024, 768
        grid = BrickGrid(Viewport(width, height), cols=10, rows=5)
        
        # Check that grid stores its configuration
        self.assertEqual(grid.cols, 10)
        self.assertEqual(grid.rows, 5)
        # Check that 50 bricks are generated (rows * cols)
        self.assertEqual(len(grid.bricks), 50)

    def test_damage_brick_grid(self):
        """Test damaging bricks in the grid."""
        grid = BrickGrid(Viewport(1024, 768), cols=2, rows=2)
        self.assertEqual(len(grid.bricks), 4)
        
        # Damage first brick
        brick = grid.bricks[0]
        brick.take_damage(1)
        self.assertFalse(brick.active)
        
        # Update grid
        grid.update()
        self.assertEqual(len(grid.bricks), 3)

    def test_level_layouts_vary(self):
        """Test that later levels use different brick dispositions."""
        level_one = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=1)
        level_two = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=2)

        self.assertNotEqual(level_one.layout_name, level_two.layout_name)
        self.assertNotEqual(len(level_one.bricks), len(level_two.bricks))

    def test_hp_progression_is_capped(self):
        """Test that HP increases gradually instead of jumping every level."""
        level_three = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=3)
        level_six = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=6)

        level_three_max = max(brick.max_hp for brick in level_three.bricks)
        level_six_max = max(brick.max_hp for brick in level_six.bricks)

        self.assertGreaterEqual(level_six_max, level_three_max)
        self.assertLessEqual(level_six_max - level_three_max, 2)

    def test_special_interval_has_floor(self):
        """Test that special brick density remains bounded at high levels."""
        self.assertEqual(BrickGrid.special_interval(99, 19, 12), 12)
        self.assertEqual(BrickGrid.special_interval(99, 13, 8), 8)

    def test_special_bricks_unlock_after_early_levels(self):
        """Test that special bricks are introduced after the opening levels."""
        level_one = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=1)
        level_six = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=6)

        self.assertTrue(all(brick.kind == BrickKind.NORMAL for brick in level_one.bricks))
        self.assertTrue(any(brick.kind in (BrickKind.BOMB, BrickKind.PULSE, BrickKind.CHARGE) for brick in level_six.bricks))

    def test_advanced_special_bricks_unlock_later(self):
        """Test that richer brick behaviors are introduced after the basics."""
        level_nine = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=9)
        advanced = {BrickKind.REGEN, BrickKind.PRISM, BrickKind.SENTRY}

        self.assertTrue(any(brick.kind in advanced for brick in level_nine.bricks))

    def test_special_bricks_have_effect_labels(self):
        """Test that every non-normal special brick has player-facing effect metadata."""
        for kind in BrickKind:
            if kind == BrickKind.NORMAL:
                continue
            self.assertIn(kind, BRICK_KIND_INFO)
            label, effect = BRICK_KIND_INFO[kind]
            self.assertTrue(label)
            self.assertTrue(effect)

    def test_milestone_layouts_have_identity(self):
        """Test that milestone levels use named layouts and themes."""
        level_five = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=5)
        level_ten = BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=10)

        self.assertEqual(level_five.layout_name, "vault")
        self.assertEqual(level_ten.layout_name, "reactor")
        self.assertIsInstance(level_ten.theme_name, str)
        self.assertTrue(any(brick.kind == BrickKind.CHARGE for brick in level_ten.bricks))

    def test_layout_pool_has_more_variety(self):
        """Test that the layout pool offers many distinct identities across all levels."""
        layouts = {BrickGrid(Viewport(1024, 768), cols=10, rows=5, level=level).layout_name for level in range(1, 20)}
        self.assertGreaterEqual(len(layouts), 10)  # 14 unique across 19 levels

if __name__ == '__main__':
    unittest.main()
