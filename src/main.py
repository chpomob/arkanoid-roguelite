"""
Arkanoid Roguelite — Entry point

On desktop: runs at 1024x768 windowed.
On Android (pygame-ce + SDL2): runs fullscreen at native resolution with virtual touch controls.
"""
import sys
import os
import pygame

# Ensure src/ is on the path
src_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, src_dir)


def detect_android():
    """Detect if we're running on Android (Buildozer/p4a)."""
    return os.environ.get("ANDROID_APP_PATH") is not None or os.environ.get("ANDROID_ARGUMENT") is not None


def get_storage_paths():
    """Return platform-appropriate paths for save files."""
    if detect_android():
        # Android: use app's private data dir
        try:
            # python-for-android provides this
            from android.storage import app_storage_path
            base = app_storage_path()
        except ImportError:
            base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
        return {
            "save": os.path.join(base, "arkanoid_save.json"),
            "high_scores": os.path.join(base, "arkanoid_high_scores.json"),
            "keybindings": os.path.join(base, "arkanoid_keybindings.json"),
            "settings": os.path.join(base, "arkanoid_settings.json"),
            "stats": os.path.join(base, "arkanoid_stats.json"),
        }
    else:
        # Desktop: local files
        return {
            "save": "arkanoid_save.json",
            "high_scores": "arkanoid_high_scores.json",
            "keybindings": "arkanoid_keybindings.json",
            "settings": "arkanoid_settings.json",
            "stats": "arkanoid_stats.json",
        }


def main():
    is_android = detect_android()

    if is_android:
        # Fullscreen at native resolution (SDL2 scales the 1024x768 viewport)
        os.environ["SDL_VIDEO_ALLOW_SCREENSAVER"] = "0"
        pygame.init()
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h

        # On Android, use fullscreen with pygame-ce's SCALED flag
        # This renders at the logical resolution and SDL upscales
        screen = pygame.display.set_mode(
            (1024, 768),
            pygame.FULLSCREEN | pygame.SCALED | pygame.NOFRAME,
        )
        # Keep the logical size for game logic
        game_w, game_h = 1024, 768
    else:
        pygame.init()
        game_w, game_h = 1024, 768
        screen = pygame.display.set_mode((game_w, game_h))
        pygame.display.set_caption("Arkanoid Roguelite - Pixel Edition")

    from game.engine import GameEngine

    paths = get_storage_paths()
    game = GameEngine(
        game_w, game_h,
        save_path=paths["save"],
        high_scores_path=paths["high_scores"],
        keybindings_path=paths["keybindings"],
        settings_path=paths["settings"],
        stats_path=paths["stats"],
    )

    if is_android:
        # On Android, replace the screen with our fullscreen one
        game.screen = screen
        # Hide mouse cursor
        pygame.mouse.set_visible(False)

    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
