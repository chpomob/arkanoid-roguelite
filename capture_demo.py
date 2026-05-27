"""
Capture gameplay frames and generate an animated GIF for the README.

Uses the existing simulation runner with draw enabled.
Run: python3 capture_demo.py
Output: demo.gif
"""
import os
import subprocess
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pygame
from game.engine import GameEngine
from simulation.bot import SimpleBot

FPS = 15
DURATION = 8  # seconds
OUTPUT_GIF = "demo.gif"
FRAMES_DIR = "/tmp/arkanoid_demo_frames"


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    # Clean previous frames
    for f in os.listdir(FRAMES_DIR):
        os.remove(os.path.join(FRAMES_DIR, f))

    pygame.display.init()
    real_surface = pygame.Surface((1024, 768))

    import random
    random.seed(42)

    bot = SimpleBot(seed=42)

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
            engine = GameEngine(1024, 768,
                                save_path=save, high_scores_path=highscores,
                                keybindings_path=keys, settings_path=settings,
                                stats_path=stats)
            engine.start_game(initial_skill_draft=False)
            engine.run_seed = 42
            bot.reset()

            # Capture title screen first (2 frames)
            for _ in range(FPS // 3):
                engine.draw()
                pygame.image.save(engine.screen,
                                  f"{FRAMES_DIR}/frame_{frame_count():04d}.png")

            # Press confirm to start (bot handles the rest)
            fake_enter = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
            pygame.event.post(fake_enter)
            engine.handle_events()
            if engine.state == "PLAYING":
                engine.update(1.0 / 60.0)

            dt = 1.0 / 60.0
            total_frames = DURATION * FPS

            for _ in range(DURATION * 60):  # 60fps simulation
                # Bot controls
                for event in bot.events(engine, dt):
                    pygame.event.post(event)

                held = bot.held_keys(engine)
                fake_array = list(pygame.key.get_pressed())
                for action in held:
                    for slot in range(2):
                        key = engine.keybindings.key_for_action(action, slot)
                        if 0 <= key < len(fake_array):
                            fake_array[key] = True

                with mock.patch("pygame.key.get_pressed", return_value=fake_array):
                    engine.handle_events()
                    if engine.state == "PLAYING":
                        engine.update(dt)

                engine.draw()

                # Save every 4th simulation frame (60/4=15fps output)
                if _counter.frame % 4 == 0:
                    pygame.image.save(engine.screen,
                                      f"{FRAMES_DIR}/frame_{_counter.frame // 4:04d}.png")
                _counter.frame += 1

                if engine.state == "GAMEOVER":
                    break

    pygame.quit()

    # Build GIF
    frame_files = sorted(os.listdir(FRAMES_DIR))
    print(f"Captured {len(frame_files)} frames, building GIF...")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{FRAMES_DIR}/frame_%04d.png",
        "-vf", f"fps={FPS},scale=512:384:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        OUTPUT_GIF,
    ], check=True)

    size_kb = os.path.getsize(OUTPUT_GIF) / 1024
    print(f"Done: {OUTPUT_GIF} ({size_kb:.0f} KB)")


class _FrameCounter:
    frame = 0


_counter = _FrameCounter()


def frame_count():
    return _counter.frame


if __name__ == "__main__":
    main()
