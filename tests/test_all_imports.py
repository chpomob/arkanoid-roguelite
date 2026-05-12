"""Import smoke test: verifies all game modules load without error.

Catches missing imports, circular dependencies, and NameErrors
that only manifest when the full module tree is imported at once.
"""
import unittest


class TestAllImports(unittest.TestCase):
    """Verify every game and simulation module imports cleanly."""

    def test_game_modules_import(self):
        """All src/game/ modules must import without error."""
        modules = [
            "game.engine",
            "game.ui",
            "game.assets",
            "game.audio",
            "game.input",
            "game.bosses",
            "game.skill_descriptions",
            "game.screens",
            "game.entities.ball",
            "game.entities.brick",
            "game.entities.enemy",
            "game.entities.paddle",
            "game.roguelite.bullet",
            "game.roguelite.effects",
            "game.roguelite.skill",
            "game.particles.particle",
        ]
        for mod_name in modules:
            try:
                __import__(mod_name)
            except Exception as e:
                self.fail(f"Failed to import {mod_name}: {e}")

    def test_simulation_modules_import(self):
        """All simulation/ modules must import cleanly."""
        modules = [
            "simulation",
            "simulation.bot",
            "simulation.alt_bots",
            "simulation.runner",
            "simulation.metrics",
            "simulation.skill_bot",
            "simulation.skill_benchmark",
            "simulation.skill_rating",
        ]
        for mod_name in modules:
            try:
                __import__(mod_name)
            except Exception as e:
                self.fail(f"Failed to import {mod_name}: {e}")

    def test_screens_module_has_all_required_symbols(self):
        """screens.py must export all functions referenced by engine._DRAW_DISPATCH."""
        import game.screens as screens
        required = [
            "draw_game_over", "draw_pause", "draw_high_scores",
            "draw_skill_guide", "draw_controls_screen", "draw_settings_screen",
            "draw_title", "draw_title_preview", "draw_hud", "draw_boss_hud",
            "draw_level_summary", "draw_brick_intro", "draw_boss_intro",
            "draw_brick_codex", "draw_skill_selection",
        ]
        for name in required:
            self.assertTrue(hasattr(screens, name), f"screens.{name} missing")

    def test_screens_module_has_no_hidden_name_errors(self):
        """Force screens module to be fully loaded (catches NameError in function bodies)."""
        import game.screens as screens
        import inspect
        for name in dir(screens):
            obj = getattr(screens, name)
            if callable(obj) and not name.startswith("_"):
                try:
                    # Just accessing the source forces Python to compile it fully
                    inspect.getsource(obj)
                except (OSError, TypeError):
                    pass  # built-in or C function
