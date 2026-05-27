"""
Arkanoid Roguelite - Entry point with WASM error logging.

Pygbag / WebAssembly requires an async main loop.  This file provides
an async entry point that pygbag detects automatically.
"""
import asyncio
import sys
import os
import traceback

# Write errors to a file we can inspect
ERROR_LOG = "/tmp/arkanoid_error.log"

async def main():
    try:
        import pygame

        def detect_android():
            return os.environ.get("ANDROID_APP_PATH") is not None or os.environ.get("ANDROID_ARGUMENT") is not None

        def get_storage_paths():
            if detect_android():
                try:
                    from android.storage import app_storage_path
                    base = app_storage_path()
                except ImportError:
                    base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
            else:
                base = "."
            return {
                "save": os.path.join(base, "arkanoid_save.json"),
                "high_scores": os.path.join(base, "arkanoid_high_scores.json"),
                "keybindings": os.path.join(base, "arkanoid_keybindings.json"),
                "settings": os.path.join(base, "arkanoid_settings.json"),
                "stats": os.path.join(base, "arkanoid_stats.json"),
            }

        pygame.init()

        if detect_android():
            info = pygame.display.Info()
            w, h = info.current_w, info.current_h
        else:
            w, h = 1024, 768

        from game.engine import GameEngine
        paths = get_storage_paths()

        game = GameEngine(
            w, h,
            save_path=paths["save"],
            high_scores_path=paths["high_scores"],
            keybindings_path=paths["keybindings"],
            settings_path=paths["settings"],
            stats_path=paths["stats"],
        )

        if detect_android():
            pygame.mouse.set_visible(False)

        await game.run()
        pygame.quit()

    except Exception as e:
        try:
            with open(ERROR_LOG, "w") as f:
                f.write(f"ERROR: {e}\n")
                traceback.print_exc(file=f)
        except:
            pass
        raise

# NOTE: No ``if __name__ == "__main__": asyncio.run(main())`` here.
# Pygbag auto-detects async def main() and awaits it.
# On desktop, run with: python -c "import asyncio; from main import main; asyncio.run(main())"
