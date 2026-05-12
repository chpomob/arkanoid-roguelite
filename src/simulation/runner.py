"""Headless game runner for bot-driven simulation.

Wraps GameEngine to run frame-by-frame with injected events and
patched key states, collecting RunResults.
"""

import os
from unittest import mock

import pygame

from game.engine import GameEngine
from game.bosses import boss_by_id, is_boss_level, BOSS_CATALOG
from simulation.bot import BaseBot
from simulation.metrics import RunResult


class GameRunner:
    """Runs a single bot-driven game simulation headlessly.

    Usage:
        bot = SimpleBot(seed=123)
        runner = GameRunner(bot, max_frames=50000)
        result = runner.run()
    """

    def __init__(self, bot: BaseBot, seed: int = 42, max_frames: int = 200000,
                 width: int = 800, height: int = 600, skip_draw: bool = True):
        self.bot = bot
        self.seed = seed
        self.max_frames = max_frames
        self.width = width
        self.height = height
        self.skip_draw = skip_draw

    def run(self) -> RunResult:
        """Execute a full simulation run. Returns RunResult."""
        import random as _random
        import tempfile
        _random.seed(self.seed)

        real_surface = pygame.Surface((self.width, self.height))

        # Use temp dir for save files to avoid cross-process contention
        with tempfile.TemporaryDirectory() as tmpdir:
            save = os.path.join(tmpdir, "save.json")
            highscores = os.path.join(tmpdir, "highscores.json")
            keys = os.path.join(tmpdir, "keys.json")
            settings = os.path.join(tmpdir, "settings.json")
            stats = os.path.join(tmpdir, "stats.json")

            with mock.patch("pygame.display.set_mode", return_value=real_surface), \
                 mock.patch("pygame.display.flip"), \
                 mock.patch("pygame.display.set_caption"):
                pygame.init()
                engine = GameEngine(self.width, self.height,
                                    save_path=save, high_scores_path=highscores,
                                    keybindings_path=keys, settings_path=settings,
                                    stats_path=stats)
                self.bot.reset()
                return self._step_loop(engine)

    def _step_loop(self, engine: GameEngine) -> RunResult:
        frames = 0
        dt = 1.0 / 60.0
        boss_kills = []
        deaths = 0
        prev_lives = engine.paddle.lives

        engine.draw()  # initial draw to set up state

        while engine.running and frames < self.max_frames:
            # Stop when game is over
            if engine.state == "GAMEOVER":
                break

            # Inject bot events
            for event in self.bot.events(engine, dt):
                pygame.event.post(event)

            prev_level = engine.level

            # Patch key state for this frame
            held = self.bot.held_keys(engine)
            with self._patch_keys(engine, held):
                engine.handle_events()
                if engine.state == "PLAYING":
                    engine.update(dt)

            # Draw (skip in headless mode for speed)
            if not self.skip_draw:
                engine.draw()

            # Boss killed if level increased from a boss level
            if engine.level_is_boss(prev_level) and engine.level > prev_level:
                boss = self._boss_for_level(prev_level)
                if boss and boss.name not in boss_kills:
                    boss_kills.append(boss.name)

            # Boss killed if level increased from a boss level
            if engine.level_is_boss(prev_level) and engine.level > prev_level:
                boss = self._boss_for_level(prev_level)
                if boss and boss.name not in boss_kills:
                    boss_kills.append(boss.name)

            # Track deaths
            current_lives = engine.paddle.lives
            if current_lives < prev_lives:
                deaths += prev_lives - current_lives
            prev_lives = current_lives

            frames += 1

        reason = "max_frames" if frames >= self.max_frames else "gameover"
        return RunResult(
            seed=self.seed,
            level_reached=engine.level,
            score=engine.score,
            skills=[s.type.name for s in engine.selected_skills],
            bricks_broken=engine.run_bricks_destroyed,
            deaths=deaths,
            boss_kills=boss_kills,
            frames=frames,
            reason=reason,
        )

    @staticmethod
    def _boss_for_level(level):
        """Return the boss definition that would be used for a given level."""
        candidates = [b for b in BOSS_CATALOG
                      if b.tier == max(1, min(3, level // 5))]
        return candidates[0] if candidates else None

    @staticmethod
    def _patch_keys(engine, held_actions: set):
        """Context manager that patches pygame.key.get_pressed to include held_actions."""
        # Build a fake key array: True for keys matching held actions
        fake_array = list(pygame.key.get_pressed())

        for action in held_actions:
            for slot in range(2):
                key = engine.keybindings.key_for_action(action, slot)
                if 0 <= key < len(fake_array):
                    fake_array[key] = True

        return mock.patch("pygame.key.get_pressed", return_value=fake_array)


def run_many(bot_class, seeds: list[int], max_frames: int = 100000, **bot_kwargs) -> list[RunResult]:
    """Run the same bot with multiple seeds. Returns list of RunResults."""
    results = []
    for seed in seeds:
        bot = bot_class(seed=seed, **bot_kwargs)
        runner = GameRunner(bot, seed=seed, max_frames=max_frames)
        results.append(runner.run())
    return results
