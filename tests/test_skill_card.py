"""Tests for Skill Card Generation and Logic"""
import unittest
import sys
import os
from unittest import mock
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.roguelite.skill import SkillCard, Skill, SkillType


class TestSkillCardGeneration(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode = mock.MagicMock()
        
    def test_skill_card_level_tracking(self):
        """Test that SkillCard correctly tracks skill levels."""
        skill_levels = {}
        
        skill_type = SkillType.DAMAGE
        
        # Simulate the logic in game.engine next_level()
        current_level = skill_levels.get(skill_type, 0) + 1
        skill_levels[skill_type] = current_level
        
        skill = Skill(skill_type, f"Skill Level {current_level}")
        skill.level = current_level
        
        card = SkillCard(skill, 100, 300)
        
        # Verify that the skill passed to the card has the correct level
        self.assertEqual(card.skill.level, 1)

    def test_skill_card_level_stacking(self):
        """Test that skill levels stack correctly across levels."""
        skill_levels = {}
        skill_type = SkillType.SPEED_UP
        
        # First level
        level = skill_levels.get(skill_type, 0) + 1
        skill_levels[skill_type] = level
        
        # Second level
        level = skill_levels.get(skill_type, 0) + 1
        skill_levels[skill_type] = level
        
        self.assertEqual(skill_levels[skill_type], 2)

    def test_skill_card_initial_properties(self):
        """Test that SkillCard initializes with correct dimensions."""
        skill = Skill(SkillType.LASER, "Laser")
        card = SkillCard(skill, 100, 200)
        
        self.assertEqual(card.width, 200)
        self.assertEqual(card.height, 150)
        self.assertEqual(card.x, 100)
        self.assertEqual(card.y, 200)

    def test_skill_card_content_layout_does_not_overlap(self):
        """Test that text bands stay ordered inside upgrade cards."""
        skill = Skill(SkillType.CANNON, "Cannon Core (Level 3)")
        skill.level = 3
        card = SkillCard(skill, 100, 200, width=210, height=220)

        desc, hint, synergy, progress = card.content_layout(card.visual_rect(False))

        self.assertLess(desc.bottom, hint.top)
        self.assertLess(hint.bottom, synergy.top)
        self.assertLess(synergy.bottom, progress.top)
        self.assertLessEqual(progress.bottom, card.rect.bottom)

    def test_skill_card_draw_handles_compact_card(self):
        """Test that drawing a compact card does not crash."""
        screen = pygame.Surface((260, 220))
        skill = Skill(SkillType.GRAVITY_WELL, "Gravity Well (Level 4)")
        skill.level = 4
        card = SkillCard(skill, 20, 20, width=210, height=170)

        card.draw(screen)

        self.assertIsInstance(screen, pygame.Surface)


if __name__ == '__main__':
    unittest.main()
