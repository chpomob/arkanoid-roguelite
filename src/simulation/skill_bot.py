"""SkillTestBot factory: targets a specific skill from drafts for benchmarking.

Supports any base bot class via make_skill_bot_class() factory.
"""

import pygame

from game.roguelite.skill import SkillType
from simulation.bot import SimpleBot


def make_skill_bot_class(base_class):
    """Create a SkillTestBot subclass inheriting from the given base class."""

    class SkillTestBot(base_class):
        """Bot that attempts to pick a target skill from each draft."""

        def __init__(self, target_skill: SkillType, seed: int = 42, **kwargs):
            super().__init__(seed=seed, **kwargs)
            self.target_skill = target_skill
            self._target_clicked_this_draft = False

        def _on_reset(self):
            super()._on_reset()
            self._target_clicked_this_draft = False

        def events(self, engine, dt: float) -> list:
            evts = super().events(engine, dt)

            if engine.state == "SKILL_SELECTION" and engine.skill_cards and not self._target_clicked_this_draft:
                for card in engine.skill_cards:
                    if card.skill.type == self.target_skill:
                        click_x = card.rect.centerx
                        click_y = card.rect.centery
                        evts.append(pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {"pos": (click_x, click_y), "button": 1},
                        ))
                        self._target_clicked_this_draft = True
                        break

            if engine.state != "SKILL_SELECTION":
                self._target_clicked_this_draft = False

            return evts

    SkillTestBot.__name__ = f"SkillTestBot_{base_class.__name__}"
    return SkillTestBot


# Pre-built default
SkillTestBot = make_skill_bot_class(SimpleBot)
