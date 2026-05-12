"""Tests for scoring, high scores, and save/resume."""
import os
import sys
import tempfile
import unittest
from unittest import mock

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.entities.brick import Brick, BrickKind
from game.engine import GameEngine
from game.roguelite.skill import Skill, SkillType


class TestScoringAndPersistence(unittest.TestCase):
    def make_game(self, tmpdir):
        return GameEngine(
            800,
            600,
            save_path=os.path.join(tmpdir, "save.json"),
            high_scores_path=os.path.join(tmpdir, "scores.json"),
            keybindings_path=os.path.join(tmpdir, "keys.json"),
            settings_path=os.path.join(tmpdir, "settings.json"),
            stats_path=os.path.join(tmpdir, "stats.json"),
        )

    def test_high_scores_rank_level_before_score(self):
        """Test that deeper runs outrank lower-level score farming."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)

            ranked = game.sort_high_scores([
                {"level": 1, "score": 99999, "skills": 2},
                {"level": 3, "score": 100, "skills": 1},
            ])

            self.assertEqual(ranked[0]["level"], 3)

    def test_destroyed_special_bricks_award_more_score(self):
        """Test that special bricks are worth more than normal bricks."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            normal = Brick(pygame.Rect(0, 0, 20, 20), hp=1, kind=BrickKind.NORMAL)
            charge = Brick(pygame.Rect(0, 0, 20, 20), hp=1, kind=BrickKind.CHARGE)

            game.award_brick_score(normal, destroyed=True)
            normal_score = game.score
            game.score = 0
            game.award_brick_score(charge, destroyed=True)

            self.assertGreater(game.score, normal_score)
            self.assertEqual(game.level_bricks_destroyed, 2)

    def test_level_summary_tracks_clear_rewards(self):
        """Test that clearing a level records a summary before the draft."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            game.start_game(initial_skill_draft=False)
            game.level_bricks_destroyed = 8
            game.level_start_score = 100
            game.score = 250

            game.next_level()

            self.assertEqual(game.state, "LEVEL_SUMMARY")
            self.assertEqual(game.last_level_summary["bricks"], 8)
            self.assertEqual(game.last_level_summary["level"], 1)
            self.assertGreater(game.last_level_summary["bonus"], 0)

    def test_save_and_load_restores_run_progress(self):
        """Test that save/resume preserves level, score, lives, skills, and bricks."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            game.start_game(initial_skill_draft=False)
            game.level = 4
            game.score = 1234
            game.max_level_reached = 4
            game.paddle.lives = 2
            skill = Skill(SkillType.DAMAGE, "Damage")
            skill.level = 2
            game.selected_skills = [skill]
            game.global_skill_levels[SkillType.DAMAGE] = 2
            game.brick_grid.bricks[0].active = False
            game.brick_grid.bricks[1].hp = 1

            game.save_run()

            resumed = self.make_game(tmpdir)
            self.assertTrue(resumed.load_run())

            self.assertEqual(resumed.level, 4)
            self.assertEqual(resumed.score, 1234)
            self.assertEqual(resumed.max_level_reached, 4)
            self.assertEqual(resumed.paddle.lives, 2)
            self.assertEqual(resumed.selected_skills[0].type, SkillType.DAMAGE)
            self.assertEqual(resumed.selected_skills[0].level, 2)
            self.assertFalse(resumed.brick_grid.bricks[0].active)
            self.assertEqual(resumed.brick_grid.bricks[1].hp, 1)
            self.assertEqual(resumed.state, "PLAYING")

    def test_finish_run_records_high_score_and_removes_save(self):
        """Test that completed runs enter high scores and clear resume data."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            game.start_game(initial_skill_draft=False)
            game.score = 500
            game.max_level_reached = 3
            game.save_run()

            game.finish_run()

            self.assertEqual(game.state, "GAMEOVER")
            self.assertFalse(game.save_path.exists())
            self.assertEqual(game.high_scores[0]["level"], 3)
            self.assertEqual(game.high_scores[0]["score"], 500)
            self.assertEqual(game.stats["runs_finished"], 1)
            self.assertEqual(game.stats["best_level"], 3)

    def test_run_stats_persist(self):
        """Test that finished run stats are persisted to disk."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            game.start_game(initial_skill_draft=False)
            game.score = 321
            game.max_level_reached = 2
            game.run_bricks_destroyed = 11
            skill = Skill(SkillType.CANNON, "Cannon")
            game.selected_skills = [skill]

            game.finish_run()

            loaded = self.make_game(tmpdir)
            self.assertEqual(loaded.stats["runs_finished"], 1)
            self.assertEqual(loaded.stats["bricks_broken"], 11)
            self.assertEqual(loaded.stats["skill_counts"]["CANNON"], 1)

    def test_finish_run_records_stats_once(self):
        """Test that repeated finish calls do not duplicate persistent stats."""
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch('pygame.display.set_mode'):
            game = self.make_game(tmpdir)
            game.start_game(initial_skill_draft=False)

            game.finish_run()
            game.finish_run()

            self.assertEqual(game.stats["runs_finished"], 1)


if __name__ == '__main__':
    unittest.main()
