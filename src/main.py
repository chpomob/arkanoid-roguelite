"""
Arkanoid Roguelite — Entry point.

On desktop: windowed 1024x768.
On Android: fullscreen at native resolution.
"""
import sys
import os
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


def main():
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

    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
