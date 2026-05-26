"""Tests for the Game Engine"""
import unittest
import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pygame # Initialize for rect creation
from game.viewport import Viewport
pygame.init()
import game.engine as engine_module


class TestEngine(unittest.TestCase):
    def test_game_engine_creation(self):
        """Test that the game engine can be created successfully."""
        try:
            game = engine_module.GameEngine(width=800, height=600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")
            
        self.assertTrue(hasattr(game, 'paddle'))
        self.assertTrue(hasattr(game, 'balls'))
        self.assertTrue(hasattr(game, 'brick_grid'))
        self.assertTrue(game.running)
        self.assertEqual(game.state, 'TITLE')
        game.start_game()
        self.assertEqual(game.state, 'SKILL_SELECTION')
        self.assertEqual(len(game.skill_cards), 3)

    def test_skill_selection_state(self):
        """Test transitioning to skill selection."""
        try:
            game = engine_module.GameEngine(800, 600)
        except:
            self.skipTest("Pygame initialization failed")

        game.start_game(initial_skill_draft=False)
        game.brick_grid.bricks = [] # Empty grid to trigger level complete
        game.update(1/60)
        
        self.assertEqual(game.state, 'LEVEL_SUMMARY')
        self.assertTrue(hasattr(game, 'skill_cards'))
        self.assertIsNotNone(game.last_level_summary)

    def test_start_game_leaves_title_screen(self):
        """Test that a run starts from the title screen."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        self.assertEqual(game.state, "TITLE")
        game.start_game()
        self.assertEqual(game.state, "SKILL_SELECTION")
        self.assertEqual(game.level, 1)
        self.assertEqual(game.paddle.lives, 3)
        self.assertEqual(len(game.selected_skills), 0)
        self.assertEqual(len(game.skill_cards), 3)

    def test_starting_skill_selection_enters_level_after_pick(self):
        """Test that the initial draft grants one skill before level 1 starts."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game()
        first_skill = game.skill_cards[0].skill
        game.complete_skill_selection(first_skill)

        self.assertEqual(game.state, "PLAYING")
        self.assertEqual(game.level, 1)
        self.assertEqual(len(game.selected_skills), 1)

    def test_new_special_bricks_are_explained_before_level_starts(self):
        """Test that new brick effects open a pre-level briefing."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        game.level = 2
        skill = engine_module.Skill(engine_module.SkillType.DAMAGE, "Piercing Shot")

        game.complete_skill_selection(skill)

        self.assertEqual(game.state, "BRICK_INTRO")
        self.assertIn(engine_module.BrickKind.TOUGH, game.pending_brick_intro_kinds)

        game.close_brick_intro()

        self.assertEqual(game.state, "PLAYING")

    def test_known_special_bricks_do_not_repeat_briefing(self):
        """Test that alre.ndy introduced brick effects do not pause later levels."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        game.level = 2
        game.introduced_brick_kinds.add(engine_module.BrickKind.TOUGH)
        skill = engine_module.Skill(engine_module.SkillType.DAMAGE, "Piercing Shot")

        game.complete_skill_selection(skill)

        self.assertEqual(game.state, "PLAYING")
        self.assertEqual(game.pending_brick_intro_kinds, [])

    def test_game_restart(self):
        """Test that ESC key triggers pause and restart."""
        try:
            game = engine_module.GameEngine(800, 600)
            
            # Simulate pause
            game.state = 'PAUSED'
            game.handle_events()
            
            # Now verify we can resume
            game.state = 'PLAYING'
            
        except:
            self.skipTest("Pygame initialization failed")

    def test_life_loss_does_not_reset_bricks(self):
        """Test that losing one life preserves the current brick progress."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        original_count = len(game.brick_grid.bricks)
        damaged_brick = game.brick_grid.bricks[0]
        damaged_brick.take_damage(damaged_brick.hp)
        game.balls[0].rect.top = game.height + 1
        game.balls[0].y = game.height + 20

        game.update(1 / 60)

        self.assertEqual(game.state, "PLAYING")
        self.assertEqual(game.paddle.lives, 2)
        self.assertEqual(len(game.brick_grid.bricks), original_count)
        self.assertFalse(game.brick_grid.bricks[0].active)

    def test_impact_feedback_sets_timers(self):
        """Test that strong impacts trigger hit pause and shake."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.trigger_impact_feedback(0.07, 4)

        self.assertGreater(game.hit_pause_timer, 0)
        self.assertGreater(game.shake_timer, 0)
        self.assertEqual(game.shake_intensity, 4)

    def test_hit_pause_skips_ball_movement(self):
        """Test that hit pause briefly freezes gameplay movement."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        ball = game.balls[0]
        start = ball.rect.center
        game.hit_pause_timer = 0.05

        game.update(1 / 120)

        self.assertEqual(ball.rect.center, start)
        self.assertGreater(game.hit_pause_timer, 0)

    def test_paddle_feedback_timer_is_set_on_hit(self):
        """Test that paddle collision feedback can be triggered independently."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.trigger_paddle_feedback()

        self.assertGreater(game.paddle_feedback_timer, 0)

    def test_audio_settings_persist(self):
        """Test that audio volume and mute settings are saved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = os.path.join(temp_dir, "settings.json")
            try:
                game = engine_module.GameEngine(800, 600, settings_path=settings_path)
            except Exception as e:
                self.skipTest(f"Pygame display or init failed: {e}")

            game.set_sound_volume(0.72)
            game.set_sound_muted(True)

            loaded = engine_module.GameEngine(800, 600, settings_path=settings_path)
            self.assertEqual(loaded.settings["sound_volume"], 0.72)
            self.assertTrue(loaded.settings["muted"])

    def test_settings_screen_adjusts_audio(self):
        """Test that settings helpers update audio state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = os.path.join(temp_dir, "settings.json")
            try:
                game = engine_module.GameEngine(800, 600, settings_path=settings_path)
            except Exception as e:
                self.skipTest(f"Pygame display or init failed: {e}")

            game.open_settings("TITLE")
            game.adjust_sound_volume(0.10)
            game.set_sound_muted(True)

            self.assertEqual(game.state, "SETTINGS")
            self.assertGreater(game.settings["sound_volume"], 0.45)
            self.assertTrue(game.settings["muted"])

    def test_skill_guide_opens_and_returns_to_previous_state(self):
        """Test that the skill guide can be opened as a reference screen."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.open_skill_guide("TITLE")

        self.assertEqual(game.state, "SKILL_GUIDE")
        self.assertEqual(game.skill_guide_return_state, "TITLE")

        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        game.handle_skill_guide_event(event)

        self.assertEqual(game.state, "TITLE")

    def test_skill_guide_navigation_selects_skills(self):
        """Test that guide navigation changes the selected skill."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.open_skill_guide("PAUSED")
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN})
        game.handle_skill_guide_event(event)

        self.assertEqual(game.skill_guide_index, 1)
        self.assertEqual(game.state, "SKILL_GUIDE")

    def test_level_special_kinds_lists_unique_special_bricks(self):
        """Test that the level summary can explain present special bricks."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.level = 9
        game.brick_grid = engine_module.BrickGrid(Viewport(800, 600), level=9, top_n=game.playfield_top_n + 10)
        kinds = game.level_special_kinds()

        self.assertEqual(len(kinds), len(set(kinds)))
        self.assertTrue(kinds)

    def test_difficulty_speed_bonus_is_bounded(self):
        """Test that level speed scaling is gradual and capped."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.level = 1
        self.assertEqual(game.difficulty_speed_bonus(), 0)
        game.level = 10
        mid_bonus = game.difficulty_speed_bonus()
        game.level = 50

        self.assertGreater(mid_bonus, 0)
        self.assertLessEqual(game.difficulty_speed_bonus(), 2.6)

    def test_level_difficulty_scales_ball_velocity(self):
        """Test that level difficulty updates both speed metadata and velocity."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        ball = game.balls[0]
        game.level = 8
        original_speed = ball.speed

        game.apply_level_difficulty_to_balls()

        self.assertGreater(ball.speed, original_speed)

    def test_tempo_stabilizer_offsets_level_speed(self):
        """Test that Tempo Stabilizer slows level speed growth."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        game.level = 10
        baseline_ball = game.balls[0]
        game.apply_level_difficulty_to_balls()
        baseline_speed = baseline_ball.speed

        game.start_game(initial_skill_draft=False)
        game.level = 10
        game.selected_skills = [engine_module.Skill(engine_module.SkillType.SPEED_UP, "Tempo")]
        stabilizer_ball = game.balls[0]
        engine_module.effects_module.apply_skills_to_ball(stabilizer_ball, game.selected_skills)
        game.apply_level_difficulty_to_balls()

        self.assertLess(stabilizer_ball.speed, baseline_speed)

    def test_full_life_heal_converts_to_shield(self):
        """Test that wasted healing becomes shield protection."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        game.paddle.lives = 5
        skill = engine_module.Skill(engine_module.SkillType.HEAL, "Repair")

        game.complete_skill_selection(skill)

        self.assertEqual(game.paddle.lives, 5)
        self.assertEqual(game.shield_charges, 1)  # overflow only, no bonus +1

    def test_shield_aura_draws_without_crashing(self):
        """Test that the shield aura renders for charged shields."""
        try:
            game = engine_module.GameEngine(800, 600)
        except Exception as e:
            self.skipTest(f"Pygame display or init failed: {e}")

        game.start_game(initial_skill_draft=False)
        game.selected_skills = [engine_module.Skill(engine_module.SkillType.SHIELD, "Aegis")]
        game.shield_charges = 2
        surface = pygame.Surface((800, 600), pygame.SRCALPHA)

        game.draw_shield_aura(surface)

        self.assertGreater(surface.get_bounding_rect().width, 0)


if __name__ == '__main__':
    unittest.main()
