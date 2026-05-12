"""Tests for Skill Card Selection Logic"""
import unittest
import sys
import os
from unittest import mock
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from game.roguelite.skill import Skill, SkillType, SkillCard, SKILL_GUIDE, skill_rarity, skill_synergy, skill_upgrade_hint
from game.engine import GameEngine
from game.skill_descriptions import get_description


class TestSkillSelectionLogic(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode = mock.MagicMock()

    def test_get_description_returns_correct_text(self):
        """Test that the description function returns the correct format."""
        desc = get_description(SkillType.DAMAGE, 1)
        self.assertIn("1", desc)
        self.assertIn("Piercing Shot", desc)
        
        # Test another skill type
        desc_vamp = get_description(SkillType.VAMPIRE, 1)
        self.assertIn("Vampirism", desc_vamp)

    def test_skill_card_check_click_marks_selected(self):
        """Test that clicking inside a card updates its state."""
        skill = Skill(SkillType.DAMAGE, "Damage")
        card = SkillCard(skill, 100, 200)
        
        self.assertFalse(card.selected)
        self.assertTrue(card.check_click((120, 220)))
        self.assertTrue(card.selected)

    def test_skill_metadata_supports_draft_clarity(self):
        """Test that cards can expose rarity and build guidance."""
        self.assertEqual(skill_rarity(SkillType.DAMAGE, 1), "common")
        self.assertEqual(skill_rarity(SkillType.DAMAGE, 3), "rare")
        self.assertEqual(skill_rarity(SkillType.CANNON, 1), "uncommon")
        self.assertIn("Pairs", skill_synergy(SkillType.CANNON))
        self.assertIn("cooldown", skill_upgrade_hint(SkillType.CANNON))

    def test_skill_guide_covers_every_skill(self):
        """Test that the skill guide has useful detail for every skill."""
        for skill_type in SkillType:
            self.assertIn(skill_type, SKILL_GUIDE)
            guide = SKILL_GUIDE[skill_type]
            self.assertTrue(guide.get("effect"))
            self.assertTrue(guide.get("use"))
            self.assertTrue(guide.get("scales"))


class TestGlobalSkillLevels(unittest.TestCase):
    def test_complete_skill_selection_records_selected_level(self):
        """Test that selecting a skill records its level globally."""
        with mock.patch('pygame.display.set_mode'):
            game = GameEngine(800, 600)
            game.start_game(initial_skill_draft=False)
            skill = Skill(SkillType.DAMAGE, "Damage")
            skill.level = 2

            game.complete_skill_selection(skill)

        self.assertEqual(game.global_skill_levels[SkillType.DAMAGE], 2)


if __name__ == '__main__':
    unittest.main()
