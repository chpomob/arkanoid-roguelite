"""Smoke tests that render each game state to catch missing imports/screen crashes."""
import os
import sys
import unittest
from unittest import mock

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.engine import GameEngine
from game.roguelite.skill import Skill, SkillType
from game.bosses import boss_by_id


class TestScreenRendering(unittest.TestCase):
    """Verify every game state renders without crashing.
    
    Catches missing imports, NameErrors, and AttributeErrors in screen
    modules that unit tests don't detect because they mock display surfaces.
    """

    def setUp(self):
        pygame.init()

    def _draw_frame(self, game):
        """Force a single draw frame on a real surface."""
        surface = pygame.Surface((game.width, game.height))
        original = game.screen
        game.screen = surface
        with mock.patch('pygame.display.flip'):
            game.draw()
        game.screen = original

    def test_title_screen_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "TITLE"
            self._draw_frame(game)

    def test_playing_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "PLAYING"
            self._draw_frame(game)

    def test_playing_with_boss_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.level = 5
            game.current_boss_id = "gate_sentinel"
            game.state = "PLAYING"
            self._draw_frame(game)

    def test_skill_selection_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "SKILL_SELECTION"
            game.selected_skills = [Skill(SkillType.DAMAGE, "Damage")]
            game.skill_cards = []
            self._draw_frame(game)

    def test_level_summary_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.last_level_summary = {
                "level": 5, "theme": "Neon Gate", "layout": "wall",
                "boss": "Gate Sentinel",
                "bricks": 10, "bonus": 5000,
                "score_gained": 6000, "next_level": 6,
            }
            game.state = "LEVEL_SUMMARY"
            self._draw_frame(game)

    def test_brick_intro_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "BRICK_INTRO"
            game.pending_brick_intro_kinds = []
            self._draw_frame(game)

    def test_boss_intro_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.level = 5
            game.current_boss_id = "gate_sentinel"
            game.state = "BOSS_INTRO"
            self._draw_frame(game)

    def test_high_scores_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "SCORES"
            self._draw_frame(game)

    def test_controls_screen_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "CONTROLS"
            self._draw_frame(game)

    def test_settings_screen_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "SETTINGS"
            self._draw_frame(game)

    def test_skill_guide_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "SKILL_GUIDE"
            self._draw_frame(game)

    def test_paused_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "PAUSED"
            self._draw_frame(game)

    def test_paused_with_boss_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.level = 5
            game.current_boss_id = "gate_sentinel"
            game.state = "PAUSED"
            self._draw_frame(game)

    def test_game_over_renders(self):
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.state = "GAMEOVER"
            self._draw_frame(game)

    def test_handle_events_dispatch_has_all_required_attrs(self):
        """Verify handle_events doesn't crash due to missing dispatch attributes."""
        with mock.patch('pygame.display.set_mode'), \
             mock.patch('pygame.display.flip'), \
             mock.patch('pygame.event.get', return_value=[]):
            game = GameEngine(800, 600)
            game.state = "TITLE"
            # This exercises handle_events dispatch dicts
            game.run = lambda: (game.handle_events(), game.draw())
            with mock.patch.object(game, 'draw'):
                game.handle_events()
                game.handle_events()


if __name__ == '__main__':
    unittest.main()
