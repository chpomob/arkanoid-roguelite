"""Tests for boss levels, arenas, and persistence."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.bosses import boss_by_id, bosses_for_level, is_boss_level
from game.engine import GameEngine
from game.entities.brick import BrickGrid
from game.roguelite.skill import Skill, SkillType
from game.viewport import Viewport


class TestBossLevels(unittest.TestCase):
    def test_boss_levels_unlock_every_five_levels(self):
        """Test that milestone levels become boss encounters."""
        self.assertFalse(is_boss_level(4))
        self.assertTrue(is_boss_level(5))
        self.assertTrue(is_boss_level(10))
        self.assertEqual({boss.tier for boss in bosses_for_level(5)}, {1})
        self.assertGreaterEqual(len(bosses_for_level(5)), 2)

    def test_boss_grid_uses_dedicated_arena(self):
        """Test that boss levels use the selected boss arena and special layout."""
        boss = boss_by_id("gate_sentinel")
        grid = BrickGrid(Viewport(800, 600), level=5, top_n=164, boss_id=boss.boss_id)

        self.assertEqual(grid.layout_name, boss.arena)
        self.assertEqual(grid.theme_name, boss.theme)
        self.assertTrue(any(brick.kind.value != "normal" for brick in grid.bricks))

    def test_skill_selection_spawns_boss_and_briefing(self):
        """Test that entering a boss level picks a boss and opens its briefing."""
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.level = 5
            boss = boss_by_id("gate_sentinel")

            with mock.patch("game.engine.choose_boss_for_level", return_value=boss):
                game.complete_skill_selection(Skill(SkillType.DAMAGE, "Damage"))

            self.assertEqual(game.current_boss_id, boss.boss_id)
            self.assertEqual(game.state, "BOSS_INTRO")
            self.assertEqual(game.brick_grid.layout_name, boss.arena)
            self.assertIsNotNone(game.active_boss())

    def test_boss_level_requires_boss_defeat(self):
        """Test that clearing arena bricks alone does not finish a boss level."""
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            game.level = 5
            game.current_boss_id = "gate_sentinel"
            game.brick_grid = BrickGrid(Viewport(800, 600), level=5, top_n=game.playfield_top_n + 10, boss_id=game.current_boss_id)
            game.spawn_boss()
            for brick in game.brick_grid.bricks:
                brick.active = False

            self.assertFalse(game.boss_defeated())

            game.active_boss().active = False
            game.enemies = []
            self.assertTrue(game.boss_defeated())

    def test_boss_save_resume_restores_identity_and_hp(self):
        """Test that a saved boss encounter resumes the same boss state."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            save_path = os.path.join(tmpdir, "save.json")
            game = GameEngine(800, 600, save_path=save_path)
            game.level = 5
            game.current_boss_id = "pulse_mantis"
            game.brick_grid = BrickGrid(Viewport(800, 600), level=5, top_n=game.playfield_top_n + 10, boss_id=game.current_boss_id)
            boss = game.spawn_boss()
            boss.hp = 4
            game.save_run()

            resumed = GameEngine(800, 600, save_path=save_path)
            self.assertTrue(resumed.load_run())

            self.assertEqual(resumed.current_boss_id, "pulse_mantis")
            self.assertEqual(resumed.active_boss().hp, 4)
            self.assertEqual(resumed.brick_grid.layout_name, boss_by_id("pulse_mantis").arena)


if __name__ == '__main__':
    unittest.main()
