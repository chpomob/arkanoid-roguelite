"""
Capture a boss-level gameplay GIF with several skills pre-loaded.

Run: python3 capture_boss_demo.py
Output: demo_boss.gif
"""
import os
import subprocess
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pygame
from game.engine import GameEngine
from game.roguelite.skill import Skill, SkillType
from game.entities.brick import BrickGrid
from simulation.bot import SimpleBot
from game.roguelite.effects import apply_skills_to_paddle, apply_skills_to_ball

FPS = 15
DURATION = 8  # seconds
OUTPUT_GIF = "demo_boss.gif"
FRAMES_DIR = "/tmp/arkanoid_boss_frames"


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    for f in os.listdir(FRAMES_DIR):
        os.remove(os.path.join(FRAMES_DIR, f))

    pygame.display.init()
    real_surface = pygame.Surface((1024, 768))

    import random
    random.seed(77)

    bot = SimpleBot(seed=77)

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
            engine.run_seed = 77
            bot.reset()

            # Give the bot several skills for visual variety
            preload = [
                SkillType.DAMAGE,
                SkillType.CHAIN_SPARK,
                SkillType.ECHO_PADDLES,
                SkillType.CANNON,
                SkillType.MULTI_BALL,
                SkillType.SHIELD,
            ]
            for i, st in enumerate(preload):
                s = Skill(st, f"Level {i+1}")
                s.level = i + 1
                engine.selected_skills.append(s)
                engine.global_skill_levels[st] = s.level

            apply_skills_to_paddle(engine.paddle, engine.selected_skills)
            for ball in engine.balls:
                apply_skills_to_ball(ball, engine.selected_skills)

            # Jump to boss level 5
            engine.level = 5
            engine.brick_grid = BrickGrid(
                engine.width, engine.height,
                level=engine.level,
                top=engine.playfield_top + 45,
                seed=engine.run_seed,
            )
            engine.spawn_level_enemies()
            engine.state = "PLAYING"

            dt = 1.0 / 60.0
            frame_out = 0

            for sim_frame in range(DURATION * 60):
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

                if sim_frame % 4 == 0:
                    pygame.image.save(engine.screen,
                                      f"{FRAMES_DIR}/frame_{frame_out:04d}.png")
                    frame_out += 1

                if engine.state == "GAMEOVER":
                    # Add lives to keep the demo going
                    engine.paddle.lives = 3
                    engine.state = "PLAYING"

    pygame.quit()

    print(f"Captured {frame_out} frames, building GIF...")
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


if __name__ == "__main__":
    main()
