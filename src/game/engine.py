import asyncio
import time
import pygame
import json
import math
import os
import random
from pathlib import Path
from random import sample
from typing import Protocol, TypeVar

from game.bosses import boss_by_id, choose_boss_for_level, is_boss_level
import game.screens as screens
from game.ui import (
    draw_background,
    draw_arcade_button,
    draw_bar,
    draw_chip,
    draw_corner_brackets,
    draw_glow_text,
    draw_modal,
    draw_panel,
    draw_soft_glow,
    draw_text,
    draw_wrapped_text,
    pulse,
    RETRO_PALETTE,
)
from game.assets import draw_ball_sprite, draw_boss_sprite, draw_brick_sprite, draw_paddle_sprite, draw_skill_icon, mix, shade

from game.audio import SoundManager
from game.entities.paddle import Paddle
from game.entities.ball import Ball
from game.entities.brick import BRICK_KIND_INFO, BrickGrid, BrickKind
from game.entities.enemy import BaseEnemy, BossEnemy, Enemy, EnemyShot
from game.input import ACTIONS, KeyBindings
from game.roguelite.skill import Skill, SkillType, SkillCard, SKILL_GUIDE, SKILL_META, skill_synergy, skill_upgrade_hint
from game.skill_descriptions import get_description, HIGH_SCORE_LIMIT
import game.roguelite.effects as effects_module
from game.roguelite.effects import RunState
from game.roguelite.bullet import LaserBullet
from game.particles.particle import Particle

from game.viewport import Viewport
from game.android_touch import AndroidInput

SAVE_VERSION = 1
STATS_VERSION = 1
BRICK_SCORE = {
    BrickKind.NORMAL: 10,
    BrickKind.TOUGH: 18,
    BrickKind.BOMB: 28,
    BrickKind.PULSE: 24,
    BrickKind.CHARGE: 32,
    BrickKind.REGEN: 26,
    BrickKind.PRISM: 30,
    BrickKind.SENTRY: 34,
}


class ActiveEntity(Protocol):
    active: bool


TActive = TypeVar("TActive", bound=ActiveEntity)


class GameEngine:
    def __init__(self, width, height, save_path="arkanoid_save.json", high_scores_path="arkanoid_high_scores.json", keybindings_path="arkanoid_keybindings.json", settings_path="arkanoid_settings.json", stats_path="arkanoid_stats.json"):
        pygame.init()
        self.width = width
        self.height = height
        self.viewport = Viewport(1024, 768, width, height)
        self.save_path = Path(save_path)
        self.high_scores_path = Path(high_scores_path)
        self.settings_path = Path(settings_path)
        self.stats_path = Path(stats_path)
        self.settings = self.load_settings()
        self.keybindings = KeyBindings(keybindings_path)
        self.audio = SoundManager(
            enabled=bool(self.settings.get("sound_enabled", True)),
            volume=float(self.settings.get("sound_volume", 0.45)),
            muted=bool(self.settings.get("muted", False)),
        )
        self.screen = pygame.Surface((self.viewport.lw, self.viewport.lh))
        self.world_surface = pygame.Surface((self.viewport.lw, self.viewport.lh), pygame.SRCALPHA)
        self._warning_overlay = pygame.Surface((self.width, 34), pygame.SRCALPHA)
        # Android: fullscreen with hardware scaling
        android_flags = pygame.FULLSCREEN | pygame.SCALED | pygame.NOFRAME if (
            os.environ.get("ANDROID_APP_PATH") or os.environ.get("ANDROID_ARGUMENT")
        ) else 0
        self.display = pygame.display.set_mode((width, height), android_flags)
        pygame.display.set_caption("Arkanoid Roguelite - Pixel Edition")
        self.clock = pygame.time.Clock()
        self._last_tick = time.time()  # for pygbag manual dt timing
        self.running = True
        self.playfield_top = 154
        self.android_input = AndroidInput()
        self.run_seed = random.randint(0, 2**31 - 1)
        
        # Game State
        self.state = "TITLE"
        self.selected_skills = []
        
        # Full Skill Pool
        self.full_skill_pool = list(SkillType)
        
        # Entities
        self.paddle = Paddle(width, height)
        self.balls = [Ball(width, height, self.paddle)]
        self.bullets = []
        self.enemies = []
        self.enemy_shots = []
        self.brick_grid = BrickGrid(width, height, top=self.playfield_top + 45, seed=self.run_seed)
        self.current_boss_id = None
        self.run_state = RunState()
        self.global_skill_levels = {}
        self._heal_applied = False
        self.level = 1
        self.score = 0
        self.max_level_reached = 1
        self.particle_system = []
        self.shield_charges = 0
        self.split_charges = 0
        self.run_recorded = False
        self.last_save_message = ""
        self.high_scores = self.load_high_scores()
        self.stats = self.load_stats()
        self.level_bricks_destroyed = 0
        self.level_start_score = 0
        self.run_bricks_destroyed = 0
        self.last_level_summary = None
        self.introduced_brick_kinds = set()
        self.pending_brick_intro_kinds = []
        self.controls_index = 0
        self.controls_slot = 0
        self.settings_index = 0
        self.skill_guide_index = 0
        self.skill_guide_scroll = 0
        self.binding_capture = None
        self.controls_return_state = "TITLE"
        self.settings_return_state = "TITLE"
        self.skill_guide_return_state = "TITLE"
        self.last_binding_message = ""
        self.cannon_cooldown = 0
        self.seeker_cooldown = 0
        self.gravity_well_active = False
        self.gravity_well_was_active = False
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_intensity = 0
        self.hit_pause_timer = 0.0
        self.paddle_feedback_timer = 0.0
        
        # Fonts
        pygame.font.init()

        # State dispatch tables
        self._SAVEABLE_STATES = ("PLAYING", "PAUSED", "SKILL_SELECTION", "LEVEL_SUMMARY", "BRICK_INTRO", "BOSS_INTRO")
        self._KEYDOWN_HANDLERS = {
            "TITLE": self._kdh_title,
            "SCORES": self._kdh_scores,
            "LEVEL_SUMMARY": self._kdh_level_summary,
            "BRICK_INTRO": self._kdh_brick_intro,
            "BOSS_INTRO": self._kdh_boss_intro,
        }
        self._BACK_HANDLERS = {
            "PLAYING": lambda: setattr(self, "state", "PAUSED"),
            "PAUSED": lambda: setattr(self, "state", "PLAYING"),
            "SKILL_SELECTION": lambda: setattr(self, "state", "TITLE" if self.is_starting_skill_draft() else "PLAYING"),
            "GAMEOVER": self.restart_game,
        }
        self._MOUSE_HANDLERS = {
            "TITLE": self._mh_title,
            "LEVEL_SUMMARY": self._mh_level_summary,
            "BRICK_INTRO": self._mh_brick_intro,
            "BOSS_INTRO": self._mh_boss_intro,
            "SKILL_SELECTION": self._mh_skill_selection,
            "CONTROLS": self._mh_controls,
            "SETTINGS": self._mh_settings,
            "SKILL_GUIDE": self._mh_skill_guide,
        }
        self._POLL_HANDLERS = {
            "SKILL_SELECTION": self._poll_skill_selection,
            "LEVEL_SUMMARY": self._poll_level_summary,
            "BRICK_INTRO": self._poll_brick_intro,
            "BOSS_INTRO": self._poll_boss_intro,
        }
        self._DRAW_DISPATCH = {
            "TITLE": lambda: screens.draw_title(self.screen, self),
            "PLAYING": self.draw_playing,
            "SKILL_SELECTION": lambda: screens.draw_skill_selection(self.screen, self),
            "LEVEL_SUMMARY": lambda: screens.draw_level_summary(self.screen, self),
            "BRICK_INTRO": lambda: screens.draw_brick_intro(self.screen, self),
            "BOSS_INTRO": lambda: screens.draw_boss_intro(self.screen, self),
            "SCORES": lambda: screens.draw_high_scores(self.screen, self),
            "CONTROLS": lambda: screens.draw_controls_screen(self.screen, self),
            "SETTINGS": lambda: screens.draw_settings_screen(self.screen, self),
            "SKILL_GUIDE": lambda: screens.draw_skill_guide(self.screen, self),
            "GAMEOVER": lambda: screens.draw_game_over(self.screen, self),
        }

    @staticmethod
    def _compact_active(items: list[TActive]) -> None:
        """Remove inactive entities in-place; callers must not retain list iterators across updates."""
        alive = 0
        for item in items:
            if item.active:
                items[alive] = item
                alive += 1
        del items[alive:]

    async def run(self):
        while self.running:
            now = time.time()
            dt = min(0.05, now - self._last_tick)  # cap at 50ms to prevent spiral
            self._last_tick = now
            self.handle_events()
            if self.state == "PLAYING":
                self.update(dt)
            self.draw()
            await asyncio.sleep(0)  # Yield control for pygbag/WASM

    def handle_events(self):
        raw_events = pygame.event.get()
        self.android_input.process(raw_events, self.viewport)

        # Snapshot state before event loop — mouse/key handlers may
        # change state (e.g. TITLE→SKILL_SELECTION). The android
        # touch dispatch below must use the ORIGINAL state to avoid
        # re-dispatching the same click into the new state.
        _click_state = self.state

        for event in raw_events:
            if event.type == pygame.QUIT:
                self.running = False
                continue
            # Android finger events handled by AndroidInput
            if event.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
                continue
            if event.type == pygame.KEYDOWN:
                if self.state in ("CONTROLS", "SETTINGS", "SKILL_GUIDE"):
                    self._handle_keydown_modal(event)
                    continue

                handler = self._KEYDOWN_HANDLERS.get(self.state)
                if handler and handler(event):
                    continue

                # Global hotkeys (work in most states)
                if self.keybindings.event_matches(event, "controls"):
                    self.audio.play("menu")
                    self.open_controls(self.state)
                    continue

                if self.keybindings.event_matches(event, "settings"):
                    self.audio.play("menu")
                    self.open_settings(self.state)
                    continue

                if self.keybindings.event_matches(event, "skills"):
                    self.audio.play("menu")
                    self.open_skill_guide(self.state)
                    continue

                if self.keybindings.event_matches(event, "save") and self.state in self._SAVEABLE_STATES:
                    self.audio.play("save")
                    self.save_run(notify=True)
                    continue

                if self.keybindings.event_matches(event, "back"):
                    self.audio.play("menu")
                    handler = self._BACK_HANDLERS.get(self.state)
                    if handler:
                        handler()
                elif self.keybindings.event_matches(event, "scores") and self.state == "GAMEOVER":
                    self.state = "SCORES"
                elif self.keybindings.event_matches(event, "skills") and self.state == "GAMEOVER":
                    self.open_skill_guide("GAMEOVER")

            if event.type == pygame.MOUSEBUTTONDOWN:
                handler = self._MOUSE_HANDLERS.get(self.state)
                if handler:
                    handler(event)
                    # Consume click so android dispatch doesn't fire twice
                    self.android_input._click_pos = None

        # Android touch: menu clicks (tap not on a virtual button)
        # Use saved state — the for-loop may have changed self.state
        # (e.g. TITLE→SKILL_SELECTION). We must NOT re-dispatch the
        # same click into the new state.
        click_pos = self.android_input.click_pos()
        if click_pos:
            handler = self._MOUSE_HANDLERS.get(_click_state)
            if handler:
                fake_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": click_pos, "button": 1})
                handler(fake_event)

        # Android touch: pause action
        if self.android_input.action() == "pause" and self.state in ("PLAYING", "PAUSED"):
            if self.state == "PLAYING":
                self.state = "PAUSED"
            else:
                self.state = "PLAYING"

        # Key-polling for held-down confirm in certain states
        poll_handler = self._POLL_HANDLERS.get(self.state)
        if poll_handler:
            poll_handler()

    # --- Keydown state handlers ---

    def _handle_keydown_modal(self, event):
        if self.state == "CONTROLS":
            self.handle_controls_event(event)
        elif self.state == "SETTINGS":
            self.handle_settings_event(event)
        elif self.state == "SKILL_GUIDE":
            self.handle_skill_guide_event(event)

    def _kdh_title(self, event):
        if self.keybindings.event_matches(event, "confirm"):
            self.audio.play("select")
            self.start_game()
            return True
        if self.keybindings.event_matches(event, "resume"):
            self.audio.play("menu")
            self.load_run()
            return True
        if self.keybindings.event_matches(event, "scores"):
            self.audio.play("menu")
            self.state = "SCORES"
            return True
        if self.keybindings.event_matches(event, "back"):
            self.running = False
            return True
        return False

    def _kdh_scores(self, event):
        if self.keybindings.event_matches(event, "back") or self.keybindings.event_matches(event, "confirm"):
            self.audio.play("menu")
            self.state = "TITLE"
            return True
        return False

    def _kdh_level_summary(self, event):
        if self.keybindings.event_matches(event, "confirm") or self.keybindings.event_matches(event, "back"):
            self.audio.play("menu")
            self.state = "SKILL_SELECTION"
            return True
        return False

    def _kdh_brick_intro(self, event):
        if self.keybindings.event_matches(event, "confirm") or self.keybindings.event_matches(event, "back"):
            self.audio.play("menu")
            self.close_brick_intro()
            return True
        return False

    def _kdh_boss_intro(self, event):
        if self.keybindings.event_matches(event, "confirm") or self.keybindings.event_matches(event, "back"):
            self.audio.play("menu")
            self.close_boss_intro()
            return True
        return False

    # --- Mouse handlers ---

    def _mh_title(self, event):
        self.audio.play("select")
        self.start_game()

    def _mh_level_summary(self, event):
        if event.button == 1:
            self.audio.play("menu")
            self.state = "SKILL_SELECTION"

    def _mh_brick_intro(self, event):
        if event.button == 1:
            self.audio.play("menu")
            self.close_brick_intro()

    def _mh_boss_intro(self, event):
        if event.button == 1:
            self.audio.play("menu")
            self.close_boss_intro()

    def _mh_skill_selection(self, event):
        if event.button == 1:
            for card in self.skill_cards:
                if card.check_click(event.pos):
                    self.complete_skill_selection(card.skill)
                    break

    def _mh_controls(self, event):
        self.handle_controls_click(event.pos)

    def _mh_settings(self, event):
        self.handle_settings_click(event.pos)

    def _mh_skill_guide(self, event):
        self.handle_skill_guide_click(event.pos)

    # --- Poll handlers (held-down keys) ---

    def _poll_skill_selection(self):
        keys = pygame.key.get_pressed()
        if self.keybindings.action_down(keys, "confirm"):
            selected_card = next((card for card in self.skill_cards if card.selected), None)
            if selected_card is None and self.skill_cards:
                selected_card = self.skill_cards[0]
            if selected_card is not None:
                self.complete_skill_selection(selected_card.skill)

    def _poll_level_summary(self):
        keys = pygame.key.get_pressed()
        if self.keybindings.action_down(keys, "confirm"):
            self.state = "SKILL_SELECTION"

    def _poll_brick_intro(self):
        keys = pygame.key.get_pressed()
        if self.keybindings.action_down(keys, "confirm"):
            self.close_brick_intro()

    def _poll_boss_intro(self):
        keys = pygame.key.get_pressed()
        if self.keybindings.action_down(keys, "confirm"):
            self.close_boss_intro()

    def handle_controls_event(self, event):
        if self.binding_capture:
            if event.key == pygame.K_ESCAPE:
                self.binding_capture = None
                return
            action, slot = self.binding_capture
            conflicts = self.keybindings.set_binding(action, slot, event.key)
            if conflicts:
                labels = [dict(ACTIONS).get(name, name) for name in conflicts]
                self.last_binding_message = f"Removed duplicate from {', '.join(labels)}"
            else:
                self.last_binding_message = "Binding updated"
            self.binding_capture = None
            return

        action_count = len(ACTIONS)
        if self.keybindings.event_matches(event, "back"):
            self.state = self.controls_return_state
        elif self.keybindings.event_matches(event, "up"):
            self.controls_index = (self.controls_index - 1) % action_count
        elif self.keybindings.event_matches(event, "down"):
            self.controls_index = (self.controls_index + 1) % action_count
        elif self.keybindings.event_matches(event, "left"):
            self.controls_slot = max(0, self.controls_slot - 1)
        elif self.keybindings.event_matches(event, "right"):
            self.controls_slot = min(1, self.controls_slot + 1)
        elif self.keybindings.event_matches(event, "confirm"):
            action, _label = ACTIONS[self.controls_index]
            self.binding_capture = (action, self.controls_slot)
            self.audio.play("select")
        elif event.key == pygame.K_r:
            self.keybindings.reset()
            self.last_binding_message = "Defaults restored"
            self.audio.play("save")

    def open_controls(self, return_state):
        self.controls_return_state = return_state
        self.binding_capture = None
        self.last_binding_message = ""
        self.state = "CONTROLS"

    def open_settings(self, return_state):
        self.settings_return_state = return_state
        self.state = "SETTINGS"

    def open_skill_guide(self, return_state):
        self.skill_guide_return_state = return_state
        self.skill_guide_index = max(0, min(self.skill_guide_index, len(self.full_skill_pool) - 1))
        self.skill_guide_scroll = max(0, min(self.skill_guide_scroll, self.skill_guide_index))
        self.state = "SKILL_GUIDE"

    def handle_skill_guide_event(self, event):
        if self.keybindings.event_matches(event, "back") or self.keybindings.event_matches(event, "skills"):
            self.audio.play("menu")
            self.state = self.skill_guide_return_state
            return

        if self.keybindings.event_matches(event, "up"):
            self.skill_guide_index = max(0, self.skill_guide_index - 1)
            self.sync_skill_guide_scroll()
            self.audio.play("menu", 0.65)
        elif self.keybindings.event_matches(event, "down"):
            self.skill_guide_index = min(len(self.full_skill_pool) - 1, self.skill_guide_index + 1)
            self.sync_skill_guide_scroll()
            self.audio.play("menu", 0.65)

    def handle_skill_guide_click(self, pos):
        for index, row in self.skill_guide_rows():
            if row.collidepoint(pos):
                self.skill_guide_index = index
                self.sync_skill_guide_scroll()
                self.audio.play("menu", 0.65)
                return

    def sync_skill_guide_scroll(self):
        visible_count = self.skill_guide_visible_count()
        if self.skill_guide_index < self.skill_guide_scroll:
            self.skill_guide_scroll = self.skill_guide_index
        elif self.skill_guide_index >= self.skill_guide_scroll + visible_count:
            self.skill_guide_scroll = self.skill_guide_index - visible_count + 1

    def skill_guide_visible_count(self):
        panel_height = min(620, self.height - 80)
        return max(5, (panel_height - 132) // 34)

    def skill_guide_rows(self):
        panel = self.skill_guide_panel_rect()
        left = pygame.Rect(panel.x + 34, panel.y + 100, 226, panel.height - 152)
        visible_count = self.skill_guide_visible_count()
        rows = []
        for offset, skill_type in enumerate(self.full_skill_pool[self.skill_guide_scroll:self.skill_guide_scroll + visible_count]):
            index = self.skill_guide_scroll + offset
            rows.append((index, pygame.Rect(left.x + 8, left.y + 8 + offset * 34, left.width - 16, 28)))
        return rows

    def skill_guide_panel_rect(self):
        panel = pygame.Rect(0, 0, min(900, self.width - 70), min(620, self.height - 80))
        panel.center = (self.width // 2, self.height // 2)
        return panel

    def handle_settings_event(self, event):
        if self.keybindings.event_matches(event, "back"):
            self.audio.play("menu")
            self.state = self.settings_return_state
        elif self.keybindings.event_matches(event, "up") or self.keybindings.event_matches(event, "down"):
            self.settings_index = (self.settings_index + 1) % 2
            self.audio.play("menu")
        elif self.keybindings.event_matches(event, "left"):
            self.adjust_sound_volume(-0.05)
        elif self.keybindings.event_matches(event, "right"):
            self.adjust_sound_volume(0.05)
        elif self.keybindings.event_matches(event, "confirm"):
            if self.settings_index == 0:
                self.set_sound_muted(not bool(self.settings.get("muted", False)))
                self.audio.play("select")
            else:
                self.adjust_sound_volume(0.05)

    def adjust_sound_volume(self, delta):
        self.set_sound_volume(float(self.settings.get("sound_volume", 0.45)) + delta)
        self.audio.play("menu", 0.75)

    def handle_settings_click(self, pos):
        mute_rect, volume_rect = self.settings_option_rects()
        if mute_rect.collidepoint(pos):
            self.settings_index = 0
            self.set_sound_muted(not bool(self.settings.get("muted", False)))
            self.audio.play("select")
        elif volume_rect.collidepoint(pos):
            self.settings_index = 1
            ratio = (pos[0] - volume_rect.x) / max(1, volume_rect.width)
            self.set_sound_volume(ratio)
            self.audio.play("menu", 0.75)

    def handle_controls_click(self, pos):
        for index, (action, _label) in enumerate(ACTIONS):
            row = self.controls_row_rect(index)
            if not row.collidepoint(pos):
                continue
            self.controls_index = index
            key_a = pygame.Rect(row.right - 184, row.y + 7, 76, 26)
            key_b = pygame.Rect(row.right - 96, row.y + 7, 76, 26)
            self.controls_slot = 1 if key_b.collidepoint(pos) else 0
            self.binding_capture = (action, self.controls_slot)
            self.audio.play("select")
            break


    def update(self, dt):
        self.update_feedback(dt)
        if self.hit_pause_timer > 0:
            self.update_particles()
            self.fade_brick_hits()
            return

        keys = pygame.key.get_pressed()
        touch_x = self.android_input.paddle_target_x()
        self.paddle.move(self.width, keys, self.keybindings, touch_x=touch_x)
        self.update_helper_paddles()
        self.update_active_skills(keys, dt)
        
        self.run_state.balls_count = len(self.balls)
        self.update_particles()
        self.fade_brick_hits()
        self.update_bullets(dt)
        self.update_enemies(dt)
        self.update_enemy_shots(dt)
        prev_energy = self.run_state.energy
        self.run_state.energy = effects_module.apply_vampire(self.paddle, self.run_state.energy, self.selected_skills)
        if self.run_state.energy < prev_energy:  # heal triggered
            effects_module.spawn_vampire_particles(self)

        active_balls_count = self.update_balls()
        self.handle_bullet_hits()
        self.handle_ball_enemy_hits()
        self.handle_enemy_shot_hits()
        self.resolve_ball_collisions()

        if active_balls_count == 0:
            self.handle_no_active_balls()

        if self.level_is_boss():
            if self.boss_defeated():
                self.next_level()
        elif not any(brick.active for brick in self.brick_grid.bricks):
            self.next_level()

    def update_particles(self):
        # In-place removal: keep alive particles at front, trim rest.
        alive = 0
        for p in self.particle_system:
            p.update()
            if p.life > 0:
                self.particle_system[alive] = p
                alive += 1
        del self.particle_system[alive:]

    def fade_brick_hits(self):
        if not self._dirty_bricks:
            return
        keep = []
        for b in self._dirty_bricks:
            if b.hit_color:
                b.hit_color = tuple(max(0, c - 50) for c in b.hit_color)
                if b.hit_color == (0, 0, 0):
                    b.hit_color = None
                else:
                    keep.append(b)
        self._dirty_bricks = keep

    def update_bullets(self, dt):
        for b in self.bullets:
            b.update(dt)
            # Trail particle for laser bullets
            if hasattr(b, '_trail_color'):
                from game.particles.particle import Particle
                self.particle_system.append(Particle(
                    b.rect.centerx, b.rect.centery, b._trail_color, speed=1, size_range=(1, 2)))
            if b.rect.top < self.playfield_top:
                b.active = False
        self._compact_active(self.bullets)

    def update_enemies(self, dt):
        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.can_fire():
                shots = enemy.fire()
                self.enemy_shots.extend(shots)
                self.audio.play("projectile", 0.45)
        self._compact_active(self.enemies)

    def update_enemy_shots(self, dt):
        for shot in self.enemy_shots:
            shot.update(dt)
            if shot.rect.top > self.height or shot.rect.right < 0 or shot.rect.left > self.width:
                shot.active = False
        self._compact_active(self.enemy_shots)

    def update_balls(self):
        active_balls_count = 0
        for ball in self.balls:
            effects_module.apply_magnet(ball, self.paddle, self.selected_skills)
            effects_module.apply_gravity_well(ball, self.paddle, self.selected_skills, self.gravity_well_active)
            effects_module.apply_stasis_field(ball, self.paddle, self.selected_skills)
            effects_module.apply_time_warp(ball, self.paddle, self.selected_skills)
            hit_brick = ball.update(self.width, self.height, [self.brick_grid], apply_damage=False, playfield_top=self.playfield_top)
            
            if ball.hit_paddle:
                self.audio.play("paddle", 0.75)
                self.trigger_paddle_feedback()
                self.fire_paddle_projectiles(ball)
                self.trigger_split_charge(ball)
            
            if hit_brick:
                self.handle_ball_brick_hit(hit_brick, ball)

            # Giant ball particle trail
            if getattr(ball, '_giant_trail_chance', 0) > 0:
                import random as _random
                if _random.random() < ball._giant_trail_chance:
                    from game.particles.particle import Particle
                    self.particle_system.append(Particle(
                        ball.rect.centerx, ball.rect.centery,
                        ball._giant_color, speed=1, size_range=(2, 5)))

            if ball.rect.top > self.height:
                ball.active = False
            elif ball.rect.top < self.height:
                active_balls_count += 1

        if active_balls_count > 0:
            self._compact_active(self.balls)
            self.run_state.balls_count = len(self.balls)

        return active_balls_count

    def handle_ball_brick_hit(self, brick, ball):
        was_active = brick.active
        effects_module.handle_brick_hit(brick, ball, self.selected_skills, self.run_state)
        destroyed = was_active and not brick.active
        self._dirty_bricks.append(brick)  # track for fade animation
        self.audio.play("break" if destroyed else "brick", 0.9)
        if destroyed:
            self.trigger_impact_feedback(0.05, 2)
        self.award_brick_score(brick, destroyed)
        self.handle_special_brick_effects(brick, ball, destroyed)
        self.apply_chain_spark(brick)
        splash_bricks = effects_module.apply_explosive(self, brick, self.selected_skills)
        dmg_count = effects_module.skill_count(self.selected_skills, SkillType.DAMAGE)
        particle_count = 9 + dmg_count * 3 if destroyed else 5 + dmg_count
        self.spawn_particles(brick, particle_count, speed=4 if destroyed else 3, size_range=(2, 4) if destroyed else (1, 3))
        for splash_brick in splash_bricks:
            self._dirty_bricks.append(splash_brick)
            self.award_brick_score(splash_brick, not splash_brick.active)
            self.spawn_particles(splash_brick, 4, speed=4, size_range=(1, 3))

    def handle_bullet_hits(self):
        for bullet in self.bullets:
            if not bullet.active:
                continue
            pierce_count = effects_module.skill_count(self.selected_skills, SkillType.PIERCING_SHOTS)
            for brick in self.brick_grid.query_rect(bullet.rect):
                destroyed = effects_module.damage_brick(brick, getattr(bullet, "damage", 1))
                brick.hit_color = (255, 255, 255)
                self._dirty_bricks.append(brick)
                self.audio.play("break" if destroyed else "brick", 0.85)
                if destroyed:
                    self.trigger_impact_feedback(0.04, 2)
                self.award_brick_score(brick, destroyed, projectile=True)
                self.handle_special_brick_effects(brick, None, destroyed)
                remaining = self.get_bullet_pierce_remaining(bullet, pierce_count)
                if remaining > 0:
                    bullet.pierce_remaining = remaining - 1
                    self.advance_piercing_bullet(bullet)
                else:
                    bullet.active = False
                self.spawn_particles(brick, 7 if destroyed else 3, speed=4 if destroyed else 3, size_range=(2, 4) if destroyed else (1, 3))
                break
            if not bullet.active:
                continue
            for enemy in self.enemies:
                if enemy.active and bullet.rect.colliderect(enemy.rect):
                    destroyed = enemy.take_damage(getattr(bullet, "damage", 1))
                    remaining = self.get_bullet_pierce_remaining(bullet, pierce_count)
                    if remaining > 0:
                        bullet.pierce_remaining = remaining - 1
                        self.advance_piercing_bullet(bullet)
                    else:
                        bullet.active = False
                    if destroyed:
                        self.score += 40 + self.level * 6
                        self.spawn_enemy_particles(enemy)
                        self.trigger_impact_feedback(0.04, 2)
                    break
        self._compact_active(self.bullets)

    def get_bullet_pierce_remaining(self, bullet, default):
        remaining = getattr(bullet, "pierce_remaining", None)
        if isinstance(remaining, (int, float)):
            return remaining
        return default

    def advance_piercing_bullet(self, bullet):
        bullet.x += getattr(bullet, "dx", 0)
        bullet.y += getattr(bullet, "dy", -getattr(bullet, "speed", 0))
        bullet.rect.center = (bullet.x, bullet.y)

    def handle_ball_enemy_hits(self):
        for ball in self.balls:
            if not ball.active:
                continue
            for enemy in self.enemies:
                if enemy.active and ball.rect.colliderect(enemy.rect):
                    enemy.take_damage(1)
                    ball.dy = -abs(ball.dy)
                    ball.rect.bottom = enemy.rect.top
                    ball.y = ball.rect.centery
                    self.score += 40 + self.level * 6
                    self.spawn_enemy_particles(enemy)
                    self.audio.play("break", 0.75)
                    self.trigger_impact_feedback(0.04, 2)
                    break
        self._compact_active(self.enemies)

    def handle_enemy_shot_hits(self):
        # Only the main paddle takes damage — helper paddles are projections
        for shot in self.enemy_shots:
            if not shot.active:
                continue
            if shot.rect.colliderect(self.paddle.rect):
                shot.active = False
                self.handle_enemy_hit_player()
        self._compact_active(self.enemy_shots)

    def handle_enemy_hit_player(self):
        if self.shield_charges > 0:
            self.shield_charges -= 1
            self.audio.play("shield", 0.85)
            self.trigger_impact_feedback(0.08, 4)
            # Shield absorb particles
            for _ in range(8):
                self.particle_system.append(Particle(
                    self.paddle.rect.centerx, self.paddle.rect.y,
                    (100, 200, 255), speed=4, size_range=(2, 5)))
            return

        self.paddle.lives -= 1
        if self.paddle.lives <= 0:
            self.audio.play("gameover")
            self.trigger_impact_feedback(0.16, 6)
            self.finish_run()
        else:
            self.audio.play("life")
            self.trigger_impact_feedback(0.10, 4)
            self.reset_after_life_loss()

    def resolve_ball_collisions(self):
        for i, b1 in enumerate(self.balls):
            for b2 in self.balls[i+1:]:
                if b1.rect.colliderect(b2.rect):
                    overlap_x = min(b1.rect.right, b2.rect.right) - max(b1.rect.left, b2.rect.left)
                    overlap_y = min(b1.rect.bottom, b2.rect.bottom) - max(b1.rect.top, b2.rect.top)
                    
                    if overlap_x < overlap_y:
                        b1.dx, b2.dx = b2.dx, b1.dx
                        if b1.rect.centerx < b2.rect.centerx:
                            b1.rect.x -= overlap_x / 2
                            b2.rect.x += overlap_x / 2
                        else:
                            b1.rect.x += overlap_x / 2
                            b2.rect.x -= overlap_x / 2
                    else:
                        b1.dy, b2.dy = b2.dy, b1.dy
                        if b1.rect.centery < b2.rect.centery:
                            b1.rect.y -= overlap_y / 2
                            b2.rect.y += overlap_y / 2
                        else:
                            b1.rect.y += overlap_y / 2
                            b2.rect.y -= overlap_y / 2

    def handle_no_active_balls(self):
        self.paddle.lives -= 1
        if self.paddle.lives <= 0:
            self.audio.play("gameover")
            self.trigger_impact_feedback(0.16, 6)
            self.finish_run()
        else:
            self.audio.play("life")
            self.trigger_impact_feedback(0.12, 5)
            self.reset_after_life_loss()

    def update_feedback(self, dt):
        self.shake_timer = max(0.0, self.shake_timer - dt)
        self.hit_pause_timer = max(0.0, self.hit_pause_timer - dt)
        self.paddle_feedback_timer = max(0.0, self.paddle_feedback_timer - dt)

    def trigger_impact_feedback(self, pause=0.04, shake=2):
        self.hit_pause_timer = max(self.hit_pause_timer, pause)
        self.shake_timer = max(self.shake_timer, pause * 2.4)
        self.shake_duration = max(self.shake_duration, self.shake_timer)
        self.shake_intensity = max(self.shake_intensity, shake)

    def trigger_paddle_feedback(self):
        self.paddle_feedback_timer = 0.16

    def camera_offset(self):
        if self.shake_timer <= 0 or self.shake_intensity <= 0:
            return (0, 0)
        progress = self.shake_timer / max(0.001, self.shake_duration)
        amount = max(1, int(self.shake_intensity * progress))
        ticks = pygame.time.get_ticks()
        return (((ticks // 31) % (amount * 2 + 1)) - amount, ((ticks // 47) % (amount * 2 + 1)) - amount)

    def spawn_particles(self, brick, count, speed=3, size_range=(1, 3)):
        """Spawn directional explosion sparks from a brick."""
        cx, cy = brick.rect.centerx, brick.rect.centery
        for i in range(count):
            angle = math.radians(i * (360 / max(1, count)))
            self.particle_system.append(Particle(
                cx, cy, brick.color, speed=speed, size_range=size_range,
                directional=True, angle_bias=angle))

    def spawn_enemy_particles(self, enemy, count=8):
        """Spawn directional death burst from an enemy."""
        cx, cy = enemy.rect.centerx, enemy.rect.centery
        for i in range(count):
            angle = math.radians(i * (360 / max(1, count)))
            self.particle_system.append(Particle(
                cx, cy, enemy.color, speed=5, size_range=(2, 5),
                directional=True, angle_bias=angle))

    def spawn_enemy(self, x, y, speed=None, cooldown=None):
        enemy_speed = speed if speed is not None else min(2.2, 1.25 + self.level * 0.045)
        enemy_cooldown = cooldown if cooldown is not None else max(0.95, 2.2 - self.level * 0.055)
        bounds = (34, self.width - 34)
        self.enemies.append(Enemy(x, y, bounds, speed=enemy_speed, cooldown=enemy_cooldown))

    # ── Visual effect helpers ─────────────────────────────────────

    def _spawn_shockwave_ring(self, cx, cy, color, count=8):
        """Expanding ring of particles (PULSE brick effect)."""
        for i in range(count):
            angle = math.radians(i * (360 / count))
            self.particle_system.append(Particle(
                cx, cy, color, speed=4, size_range=(2, 4),
                directional=True, angle_bias=angle))

    def _spawn_explosion_burst(self, cx, cy, color, count=14):
        """Dense directional explosion (BOMB brick)."""
        for i in range(count):
            angle = math.radians(i * (360 / count))
            self.particle_system.append(Particle(
                cx, cy, (255, 160, 40), speed=6, size_range=(2, 6),
                directional=True, angle_bias=angle))
        # Hot white core sparks
        for _ in range(4):
            angle = random.uniform(0, math.pi * 2)
            self.particle_system.append(Particle(
                cx, cy, (255, 240, 200), speed=3, size_range=(1, 3),
                directional=True, angle_bias=angle))

    def _spawn_energy_drain(self, from_x, from_y, to_x, to_y, color, count=10):
        """Particles flowing from brick toward paddle (CHARGE brick)."""
        angle = math.atan2(to_y - from_y, to_x - from_x)
        for i in range(count):
            ox = from_x + random.uniform(-10, 10)
            oy = from_y + random.uniform(-5, 5)
            self.particle_system.append(Particle(
                ox, oy, color, speed=5, size_range=(2, 4),
                directional=True, angle_bias=angle))

    def _spawn_rainbow_burst(self, cx, cy, count=12):
        """Multi-colored particle burst (PRISM brick)."""
        rainbow = [(255, 100, 100), (255, 200, 50), (100, 255, 100),
                   (50, 180, 255), (180, 100, 255), (255, 150, 255)]
        for i in range(count):
            angle = math.radians(i * (360 / count))
            color = rainbow[i % len(rainbow)]
            self.particle_system.append(Particle(
                cx, cy, color, speed=5, size_range=(2, 5),
                directional=True, angle_bias=angle))

    def _spawn_portal_effect(self, cx, cy, color):
        """Expanding ring at enemy spawn point (SENTRY brick)."""
        for i in range(10):
            angle = math.radians(i * 36)
            self.particle_system.append(Particle(
                cx, cy, color, speed=2, size_range=(2, 4),
                directional=True, angle_bias=angle))
        # Dark smoke puffs
        for _ in range(4):
            self.particle_system.append(Particle(
                cx + random.uniform(-8, 8), cy + random.uniform(-4, 4),
                (30, 20, 30), speed=1, size_range=(2, 4)))

    def level_is_boss(self, level=None):
        return is_boss_level(self.level if level is None else level)

    def ensure_boss_for_level(self):
        if not self.level_is_boss():
            self.current_boss_id = None
            return None
        if self.current_boss_id:
            return boss_by_id(self.current_boss_id)
        boss = choose_boss_for_level(self.level)
        self.current_boss_id = boss.boss_id
        return boss

    def current_boss_definition(self):
        if not self.level_is_boss() or not self.current_boss_id:
            return None
        return boss_by_id(self.current_boss_id)

    def active_boss(self):
        return next((enemy for enemy in self.enemies if enemy.is_boss and enemy.active), None)

    def boss_defeated(self):
        return self.level_is_boss() and self.current_boss_id is not None and self.active_boss() is None

    def spawn_boss(self, hp=None):
        boss = self.ensure_boss_for_level()
        if boss is None:
            return None
        enemy = BossEnemy(boss, self.level, self.width, self.playfield_top)
        if hp is not None:
            enemy.hp = max(0, min(enemy.max_hp, int(hp)))
            enemy.active = enemy.hp > 0
        self.enemies = [enemy] if enemy.active else []
        return enemy

    def apply_chain_spark(self, source_brick):
        spark_count = effects_module.skill_count(self.selected_skills, SkillType.CHAIN_SPARK)
        if spark_count == 0:
            return []

        chained = []
        radius = 94 + spark_count * 18
        prev = source_brick
        for i in range(min(3, spark_count + 1)):
            candidates = [
                brick for brick in self.brick_grid.bricks
                if brick.active and brick is not source_brick and brick not in chained
            ]
            if not candidates:
                break
            target = min(candidates, key=lambda brick: math.hypot(brick.rect.centerx - prev.rect.centerx, brick.rect.centery - prev.rect.centery))
            if math.hypot(target.rect.centerx - prev.rect.centerx, target.rect.centery - prev.rect.centery) > radius:
                break
            dmg = 2 if i == 0 else 1
            destroyed = effects_module.damage_brick(target, dmg)
            target.hit_color = (100, 200, 255)
            self.award_brick_score(target, destroyed)
            # Lightning arc particles along a zigzag path
            self._spawn_lightning_arc(prev.rect.centerx, prev.rect.centery,
                                      target.rect.centerx, target.rect.centery,
                                      (80, 180, 255), count=12)
            # Impact sparks on target
            self.spawn_particles(target, 6, speed=5, size_range=(1, 4))
            chained.append(target)
            prev = target
        return chained

    def _spawn_lightning_arc(self, x1, y1, x2, y2, color, count=12):
        """Spawn particles along a jagged lightning path between two points."""
        dx, dy = x2 - x1, y2 - y1
        dist = max(1, math.hypot(dx, dy))
        for i in range(count):
            t = i / (count - 1) if count > 1 else 0.5
            # Zigzag offset perpendicular to the line
            perp_x = -dy / dist
            perp_y = dx / dist
            zigzag = (random.uniform(-1, 1) * 10 * math.sin(t * math.pi * 3))
            px = x1 + dx * t + perp_x * zigzag
            py = y1 + dy * t + perp_y * zigzag
            self.particle_system.append(Particle(
                px, py, color, speed=2, size_range=(2, 4),
                directional=True,
                angle_bias=math.atan2(dy, dx) + random.uniform(-0.3, 0.3)))

    def spawn_level_enemies(self):
        self.enemies = []
        self.enemy_shots = []
        if self.level_is_boss():
            self.spawn_boss()
            return
        if self.level < 3:
            return
        count = 1 + (1 if self.level >= 7 else 0) + (1 if self.level >= 12 else 0) + (1 if self.level >= 18 else 0) + (1 if self.level >= 25 else 0)
        spacing = self.width / (count + 1)
        y = self.playfield_top + 34
        for index in range(count):
            self.spawn_enemy(spacing * (index + 1), y + (index % 2) * 28)

    def award_brick_score(self, brick, destroyed, projectile=False):
        level_factor = 1 + (self.level - 1) * 0.12
        hit_value = max(1, int(self.level * (1 if projectile else 2)))
        self.score += hit_value
        if destroyed:
            base_value = BRICK_SCORE.get(brick.kind, BRICK_SCORE[BrickKind.NORMAL])
            hp_bonus = max(0, brick.max_hp - 1) * 4
            added = int((base_value + hp_bonus) * level_factor)
            added = effects_module.apply_score_boost(added, self.selected_skills)
            self.score += added
            self.level_bricks_destroyed += 1
            self.run_bricks_destroyed += 1
            # Life steal proc
            effects_module.apply_life_steal(self, self.selected_skills)

    def level_clear_bonus(self):
        boss_bonus = self.level * 260 if self.level_is_boss() else 0
        return (self.level * 500) + boss_bonus + (self.paddle.lives * 100) + (len(self.selected_skills) * 25)

    def build_level_summary(self, completed_level, bonus):
        return {
            "level": completed_level,
            "theme": getattr(self.brick_grid, "theme_name", "Run"),
            "layout": getattr(self.brick_grid, "layout_name", "wall"),
            "boss": self.current_boss_definition().name if self.level_is_boss(completed_level) and self.current_boss_id else None,
            "bricks": self.level_bricks_destroyed,
            "bonus": bonus,
            "score_gained": self.score - self.level_start_score,
            "next_level": completed_level + 1,
        }

    def reset_after_life_loss(self):
        self.run_state.energy = 0  # reset vampire charge on life loss
        self.run_state.balls_count = 1
        self.balls = [Ball(self.width, self.height, self.paddle)]
        self.bullets = []
        self.enemy_shots = []
        self.paddle.rect.x = int((self.width - self.paddle.width) / 2)
        self.paddle.rect.y = self.height - 40
        self.paddle.x = self.paddle.rect.x
        self.paddle.y = self.paddle.rect.y
        self.update_helper_paddles()

    def update_active_skills(self, keys, dt):
        self.cannon_cooldown = max(0, self.cannon_cooldown - dt)
        self.seeker_cooldown = max(0, self.seeker_cooldown - dt)
        self.gravity_well_active = (
            self.keybindings.action_down(keys, "down")
            or self.android_input.action() == "down"
        ) and effects_module.skill_count(self.selected_skills, SkillType.GRAVITY_WELL) > 0
        if self.gravity_well_active and not self.gravity_well_was_active:
            self.audio.play("well", 0.65)
        self.gravity_well_was_active = self.gravity_well_active

        if self.keybindings.action_down(keys, "up") or self.android_input.action() == "up":
            self.fire_cannon()
        self.fire_seeker()

    def fire_cannon(self):
        cannon_count = effects_module.skill_count(self.selected_skills, SkillType.CANNON)
        if cannon_count == 0 or self.cannon_cooldown > 0:
            return False

        damage = 1  # base damage, no level scaling
        color = RETRO_PALETTE["brick1"]
        bullet = LaserBullet((self.paddle.rect.centerx, self.paddle.rect.y - 6), damage=damage, color=color)
        bullet._trail_color = (255, 200, 50)
        self.bullets.append(bullet)
        if cannon_count >= 2:
            spread = min(1.4, 0.55 + cannon_count * 0.15)
            self.bullets.append(LaserBullet((self.paddle.rect.centerx - 16, self.paddle.rect.y - 4), dx=-spread, damage=1, color=RETRO_PALETTE["accent"]))
            self.bullets.append(LaserBullet((self.paddle.rect.centerx + 16, self.paddle.rect.y - 4), dx=spread, damage=1, color=RETRO_PALETTE["accent"]))

        self.cannon_cooldown = max(0.70, 1.0 - (cannon_count - 1) * 0.05)
        self.audio.play("cannon")
        return True

    def fire_seeker(self):
        seeker_count = effects_module.skill_count(self.selected_skills, SkillType.SEEKER)
        if seeker_count == 0 or self.seeker_cooldown > 0:
            return False

        target = self.find_seeker_target()
        if target is None:
            return False

        start = (self.paddle.rect.centerx, self.paddle.rect.y - 8)
        dx = target[0] - start[0]
        dy = target[1] - start[1]
        length = max(1.0, math.hypot(dx, dy))
        speed = min(11.0, 7.2 + seeker_count * 0.55)
        damage = 1 + (1 if seeker_count >= 3 else 0)
        self.bullets.append(LaserBullet(
            start,
            dx=(dx / length) * speed,
            dy=(dy / length) * speed,
            damage=damage,
            color=RETRO_PALETTE["brick2"],
            bounds_width=self.width,
            bounds_height=self.height,
        ))
        self.seeker_cooldown = max(0.75, 1.45 - seeker_count * 0.10)
        self.audio.play("projectile", 0.55)
        return True

    def find_seeker_target(self):
        candidates = [enemy.rect.center for enemy in self.enemies if enemy.active]
        candidates.extend(brick.rect.center for brick in self.brick_grid.bricks if brick.active)
        if not candidates:
            return None
        source = self.paddle.rect.center
        return min(candidates, key=lambda pos: math.hypot(pos[0] - source[0], pos[1] - source[1]))

    def next_level(self):
        completed_level = self.level
        bonus = self.level_clear_bonus()
        self.score += bonus
        self.last_level_summary = self.build_level_summary(completed_level, bonus)
        self.audio.play("level")
        self.trigger_impact_feedback(0.10, 4)
        self.level += 1
        self.current_boss_id = None
        self.max_level_reached = max(self.max_level_reached, self.level)
        self.state = "LEVEL_SUMMARY"
        self.enemies = []
        self.enemy_shots = []
        choice_count = effects_module.skill_count(self.selected_skills, SkillType.CHOICE)
        card_count = min(len(self.full_skill_pool), 3 + min(2, choice_count))
        selected_types = list(sample(self.full_skill_pool, card_count))
        self.build_skill_cards(selected_types)
        self.paddle.rect.x = int((self.width - self.paddle.width) / 2)
        self.paddle.x = self.paddle.rect.x
        self.save_run()

    def build_skill_cards(self, selected_types):
        card_count = max(1, len(selected_types))
        self.skill_cards = []
        card_width = min(230, max(125, (self.width - 130) // card_count))
        y = max(240, int(self.height * 0.43))
        card_height = min(220, max(190, self.height - y - 110))
        gap = 18
        total_width = (card_width * card_count) + (gap * (card_count - 1))
        start_x = max(30, (self.width - total_width) // 2)
        for i, st in enumerate(selected_types):
            current_level = self.global_skill_levels.get(st, 0) + 1
            new_skill = Skill(st, get_description(st, current_level))
            new_skill.level = current_level
            self.skill_cards.append(SkillCard(new_skill, start_x + i * (card_width + gap), y, card_width, card_height))

    def complete_skill_selection(self, skill):
        # Guard against double-dispatch: exact same Skill object re-fired by pygbag.
        if skill in self.selected_skills:
            return
        # Upgrade existing skill of same type, or add new one.
        existing = next((s for s in self.selected_skills if s.type == skill.type), None)
        if existing:
            existing.level = skill.level
            existing.description = skill.description
        else:
            self.selected_skills.append(skill)
        self.global_skill_levels[skill.type] = skill.level
        if skill.type == SkillType.SHIELD:
            self.shield_charges += 1
        if skill.type == SkillType.SPLIT_CHARGE:
            self.split_charges += 1 + min(2, skill.level)
        if skill.type == SkillType.HEAL:
            missing_lives = max(0, 5 - self.paddle.lives)
            overflow_heals = max(0, skill.level - missing_lives)
            self.shield_charges += overflow_heals  # no bonus shield
        boss = self.ensure_boss_for_level()
        self.brick_grid = BrickGrid(self.width, self.height, level=self.level, top=self.playfield_top + 45, boss_id=boss.boss_id if boss else None, seed=self.run_seed)
        self.spawn_level_enemies()
        self.balls = [Ball(self.width, self.height, self.paddle)]
        self.bullets = []
        effects_module.apply_skills_to_paddle(self.paddle, self.selected_skills)
        self.level_bricks_destroyed = 0
        self.level_start_score = self.score
        effects_module.handle_skills(self, [skill], self.run_state, self._heal_applied)
        self._heal_applied = True
        for ball in self.balls:
            effects_module.apply_skills_to_ball(ball, self.selected_skills)
        self.apply_level_difficulty_to_balls()
        self.run_state.balls_count = len(self.balls)
        self.open_level_intro_if_needed()
        self.audio.play("skill")
        self.save_run()

    def open_level_intro_if_needed(self):
        if self.level_is_boss():
            new_kinds = [kind for kind in self.level_special_kinds() if kind not in self.introduced_brick_kinds]
            self.pending_brick_intro_kinds = new_kinds
            self.introduced_brick_kinds.update(new_kinds)
            self.state = "BOSS_INTRO"
            return
        self.open_brick_intro_if_needed()

    def open_brick_intro_if_needed(self):
        new_kinds = [kind for kind in self.level_special_kinds() if kind not in self.introduced_brick_kinds]
        if new_kinds:
            self.pending_brick_intro_kinds = new_kinds
            self.introduced_brick_kinds.update(new_kinds)
            self.state = "BRICK_INTRO"
        else:
            self.pending_brick_intro_kinds = []
            self.state = "PLAYING"

    def close_brick_intro(self):
        self.pending_brick_intro_kinds = []
        self.state = "PLAYING"

    def close_boss_intro(self):
        self.pending_brick_intro_kinds = []
        self.state = "PLAYING"

    def start_game(self, initial_skill_draft=True):
        self.record_run_start()
        self.run_seed = random.randint(0, 2**31 - 1)
        self.level = 1
        self.score = 0
        self.max_level_reached = 1
        self.selected_skills = []
        self.global_skill_levels.clear()
        self._heal_applied = False
        self.shield_charges = 0
        self.split_charges = 0
        self.run_recorded = False
        self.last_save_message = ""
        self.level_bricks_destroyed = 0
        self.level_start_score = 0
        self.run_bricks_destroyed = 0
        self.last_level_summary = None
        self.introduced_brick_kinds = set()
        self.pending_brick_intro_kinds = []
        self._dirty_bricks = []  # bricks currently showing hit_color flash
        self.current_boss_id = None
        self.cannon_cooldown = 0
        self.seeker_cooldown = 0
        self.gravity_well_active = False
        self.gravity_well_was_active = False
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_intensity = 0
        self.hit_pause_timer = 0.0
        self.paddle_feedback_timer = 0.0
        self.paddle.reset(self.width, self.height)
        self.paddle.width_bonus = 0
        self.paddle.update_rect()
        self.run_state.energy = 0
        self.run_state.balls_count = 1
        self.balls = [Ball(self.width, self.height, self.paddle)]
        if not initial_skill_draft:
            self.apply_level_difficulty_to_balls()
        self.bullets = []
        self.enemies = []
        self.enemy_shots = []
        self.particle_system = []
        self.brick_grid = BrickGrid(self.width, self.height, level=self.level, top=self.playfield_top + 45, seed=self.run_seed)
        self.introduced_brick_kinds.update(self.level_special_kinds())
        if not initial_skill_draft:
            self.spawn_level_enemies()
        self.paddle.extra_rects = []
        if initial_skill_draft:
            # Mix RNG with wall-clock ticks so WASM builds get variety
            random.seed(self.run_seed ^ pygame.time.get_ticks())
            selected_types = list(sample(self.full_skill_pool, min(3, len(self.full_skill_pool))))
            self.build_skill_cards(selected_types)
            self.state = "SKILL_SELECTION"
        else:
            self.state = "PLAYING"
            self.level_start_score = self.score
        self.save_run()

    def restart_game(self):
        self.start_game()

    def is_starting_skill_draft(self):
        return self.state == "SKILL_SELECTION" and self.level == 1 and len(self.selected_skills) == 0

    def finish_run(self):
        self.state = "GAMEOVER"
        already_recorded = self.run_recorded
        if self.record_high_score():
            self.audio.play("highscore")
        if not already_recorded:
            self.record_run_stats()
        if self.save_path.exists():
            self.save_path.unlink()

    def serialize_run(self):
        state = "SKILL_SELECTION" if self.state in ("SKILL_SELECTION", "LEVEL_SUMMARY") else "PLAYING"
        return {
            "version": SAVE_VERSION,
            "state": state,
            "level": self.level,
            "score": self.score,
            "max_level_reached": self.max_level_reached,
            "lives": self.paddle.lives,
            "shield_charges": self.shield_charges,
            "split_charges": self.split_charges,
            "energy": self.run_state.energy,
            "cannon_cooldown": self.cannon_cooldown,
            "seeker_cooldown": self.seeker_cooldown,
            "level_bricks_destroyed": self.level_bricks_destroyed,
            "run_seed": self.run_seed,
            "run_bricks_destroyed": self.run_bricks_destroyed,
            "level_start_score": self.level_start_score,
            "boss": {
                "id": self.current_boss_id,
                "hp": boss.hp,
            } if (boss := self.active_boss()) else None,
            "selected_skills": [
                {"type": skill.type.name, "level": skill.level}
                for skill in self.selected_skills
            ],
            "global_skill_levels": {
                skill_type.name: level
                for skill_type, level in self.global_skill_levels.items()
            },
            "bricks": [
                {"active": brick.active, "hp": brick.hp}
                for brick in self.brick_grid.bricks
            ],
            "skill_cards": [
                {"type": card.skill.type.name, "level": card.skill.level}
                for card in getattr(self, "skill_cards", [])
            ],
        }

    def save_run(self, notify=False):
        data = self.serialize_run()
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if notify:
            self.last_save_message = f"Saved level {self.level}"

    def load_run(self):
        if not self.save_path.exists():
            self.last_save_message = "No save found"
            return False

        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.last_save_message = "Save unreadable"
            return False

        if data.get("version") != SAVE_VERSION:
            self.last_save_message = "Save incompatible"
            return False

        try:
            self.restore_run(data)
        except (KeyError, ValueError, TypeError):
            self.last_save_message = "Save invalid"
            return False

        self.last_save_message = f"Loaded level {self.level}"
        return True

    def restore_run(self, data):
        self.level = int(data["level"])
        self.score = int(data.get("score", 0))
        self.max_level_reached = max(int(data.get("max_level_reached", self.level)), self.level)
        self.shield_charges = int(data.get("shield_charges", 0))
        self.split_charges = int(data.get("split_charges", 0))
        self.run_recorded = False
        self.run_seed = int(data.get("run_seed", 0))
        self.cannon_cooldown = float(data.get("cannon_cooldown", 0))
        self.seeker_cooldown = float(data.get("seeker_cooldown", 0))
        self.level_bricks_destroyed = int(data.get("level_bricks_destroyed", 0))
        self.run_bricks_destroyed = int(data.get("run_bricks_destroyed", 0))
        self.level_start_score = int(data.get("level_start_score", self.score))
        self.last_level_summary = None
        saved_boss = data.get("boss") or {}
        self.current_boss_id = saved_boss.get("id") if self.level_is_boss() else None
        if self.level_is_boss() and not self.current_boss_id:
            self.ensure_boss_for_level()
        self.introduced_brick_kinds = self.special_kinds_through_level(max(1, self.level))
        self.pending_brick_intro_kinds = []
        self.gravity_well_active = False
        self.gravity_well_was_active = False
        self.shake_timer = 0.0
        self.shake_duration = 0.0
        self.shake_intensity = 0
        self.hit_pause_timer = 0.0
        self.paddle_feedback_timer = 0.0
        self.selected_skills = []
        self.global_skill_levels.clear()

        for name, level in data.get("global_skill_levels", {}).items():
            self.global_skill_levels[SkillType[name]] = int(level)

        for saved_skill in data.get("selected_skills", []):
            skill_type = SkillType[saved_skill["type"]]
            level = int(saved_skill["level"])
            skill = Skill(skill_type, get_description(skill_type, level))
            skill.level = level
            self.selected_skills.append(skill)

        self.run_state.energy = int(data.get("energy", 0))
        self.run_state.balls_count = 1
        self.paddle.reset(self.width, self.height)
        self.paddle.lives = int(data.get("lives", 3))
        effects_module.apply_skills_to_paddle(self.paddle, self.selected_skills)
        boss = self.current_boss_definition()
        self.brick_grid = BrickGrid(self.width, self.height, level=self.level, top=self.playfield_top + 45, boss_id=boss.boss_id if boss else None, seed=self.run_seed)
        for brick, saved_brick in zip(self.brick_grid.bricks, data.get("bricks", [])):
            brick.active = bool(saved_brick.get("active", True))
            brick.hp = int(saved_brick.get("hp", brick.hp))

        self.balls = [Ball(self.width, self.height, self.paddle)]
        for ball in self.balls:
            effects_module.apply_skills_to_ball(ball, self.selected_skills)
        self.apply_level_difficulty_to_balls()
        self.bullets = []
        self.particle_system = []
        if self.level_is_boss():
            self.spawn_boss(saved_boss.get("hp"))
        else:
            self.spawn_level_enemies()
        self.update_helper_paddles()

        if data.get("state") == "SKILL_SELECTION" and data.get("skill_cards"):
            card_types = [SkillType[item["type"]] for item in data["skill_cards"]]
            self.build_skill_cards(card_types)
            for card, saved_card in zip(self.skill_cards, data["skill_cards"]):
                card.skill.level = int(saved_card.get("level", card.skill.level))
                card.skill.description = get_description(card.skill.type, card.skill.level)
            self.state = "SKILL_SELECTION"
        else:
            self.state = "PLAYING"

    def special_kinds_through_level(self, level):
        kinds = set()
        for level_number in range(1, level + 1):
            grid = BrickGrid(self.width, self.height, level=level_number, top=self.playfield_top + 45, seed=self.run_seed)
            for brick in grid.bricks:
                if brick.kind in BRICK_KIND_INFO:
                    kinds.add(brick.kind)
        return kinds

    def load_high_scores(self):
        if not self.high_scores_path.exists():
            return []
        try:
            scores = json.loads(self.high_scores_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(scores, list):
            return []
        clean_scores = []
        for entry in scores:
            if not isinstance(entry, dict):
                continue
            clean_scores.append({
                "level": int(entry.get("level", 1)),
                "score": int(entry.get("score", 0)),
                "skills": int(entry.get("skills", 0)),
            })
        return self.sort_high_scores(clean_scores)

    def sort_high_scores(self, scores):
        return sorted(scores, key=lambda entry: (entry["level"], entry["score"]), reverse=True)[:HIGH_SCORE_LIMIT]

    def record_high_score(self):
        if self.run_recorded:
            return False
        self.run_recorded = True
        entry = {
            "level": self.max_level_reached,
            "score": self.score,
            "skills": len(self.selected_skills),
        }
        self.high_scores = self.sort_high_scores(self.high_scores + [entry])
        self.high_scores_path.parent.mkdir(parents=True, exist_ok=True)
        self.high_scores_path.write_text(json.dumps(self.high_scores, indent=2), encoding="utf-8")
        return entry in self.high_scores

    def load_stats(self):
        defaults = {
            "version": STATS_VERSION,
            "runs_started": 0,
            "runs_finished": 0,
            "best_level": 1,
            "total_score": 0,
            "bricks_broken": 0,
            "skill_counts": {},
        }
        if not self.stats_path.exists():
            return defaults
        try:
            data = json.loads(self.stats_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return defaults
        if not isinstance(data, dict):
            return defaults
        stats = {**defaults, **data}
        stats["skill_counts"] = dict(stats.get("skill_counts", {}))
        return stats

    def save_stats(self):
        self.stats_path.parent.mkdir(parents=True, exist_ok=True)
        self.stats_path.write_text(json.dumps(self.stats, indent=2), encoding="utf-8")

    def record_run_start(self):
        self.stats["runs_started"] = int(self.stats.get("runs_started", 0)) + 1
        self.save_stats()

    def record_run_stats(self):
        self.stats["runs_finished"] = int(self.stats.get("runs_finished", 0)) + 1
        self.stats["best_level"] = max(int(self.stats.get("best_level", 1)), self.max_level_reached)
        self.stats["total_score"] = int(self.stats.get("total_score", 0)) + self.score
        self.stats["bricks_broken"] = int(self.stats.get("bricks_broken", 0)) + self.run_bricks_destroyed
        skill_counts = dict(self.stats.get("skill_counts", {}))
        for skill in self.selected_skills:
            key = skill.type.name
            skill_counts[key] = int(skill_counts.get(key, 0)) + 1
        self.stats["skill_counts"] = skill_counts
        self.save_stats()

    def load_settings(self):
        defaults = {"sound_enabled": True, "sound_volume": 0.45, "muted": False}
        if not self.settings_path.exists():
            return defaults
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return defaults
        if not isinstance(data, dict):
            return defaults
        settings = {**defaults, **data}
        settings["sound_volume"] = max(0.0, min(1.0, float(settings.get("sound_volume", defaults["sound_volume"]))))
        settings["sound_enabled"] = bool(settings.get("sound_enabled", True))
        settings["muted"] = bool(settings.get("muted", False))
        return settings

    def save_settings(self):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def set_sound_volume(self, volume):
        volume = max(0.0, min(1.0, volume))
        self.settings["sound_volume"] = volume
        self.audio.set_volume(volume)
        self.save_settings()

    def set_sound_muted(self, muted):
        self.settings["muted"] = bool(muted)
        self.audio.set_muted(muted)
        self.save_settings()

    def draw(self):
        boss_background = self.current_boss_definition() if self.level_is_boss() and self.state in ("PLAYING", "BOSS_INTRO", "PAUSED") else None
        theme = getattr(self.brick_grid, "theme_name", "")
        draw_background(self.screen, boss_background, seed=self.run_seed, theme=theme)

        if self.state == "PAUSED":
            if self.level_is_boss():
                self.draw_playing()
            screens.draw_pause(self.screen, self)
        else:
            draw_fn = self._DRAW_DISPATCH.get(self.state)
            if draw_fn:
                draw_fn()
        
        # Scale logical surface to display — skip when 1:1 (common on web/desktop).
        if self.viewport.sx == 1.0 and self.viewport.sy == 1.0:
            self.display.blit(self.screen, (0, 0))
        else:
            scaled = pygame.transform.scale(self.screen, (self.width, self.height))
            self.display.blit(scaled, (0, 0))
        pygame.display.flip()

    def draw_playing(self):
        world_size = (self.viewport.lw, self.viewport.lh)
        if self.world_surface.get_size() != world_size:
            self.world_surface = pygame.Surface(world_size, pygame.SRCALPHA)
        world = self.world_surface
        world.fill((0, 0, 0, 0))
        feedback = self.paddle_feedback_timer / 0.16 if self.paddle_feedback_timer > 0 else 0.0
        self.paddle.draw(world, feedback=feedback)
        self.draw_shield_aura(world)
        for ball in self.balls:
            ball.draw(world)
        for p in self.particle_system:
            p.draw(world)
        for bullet in self.bullets:
            bullet.draw(world)
        for enemy in self.enemies:
            enemy.draw(world)
        for shot in self.enemy_shots:
            shot.draw(world)
        self.brick_grid.draw(world)
        pygame.draw.line(world, RETRO_PALETTE["line"], (0, self.playfield_top), (self.viewport.lw, self.playfield_top), 1)
        self.screen.blit(world, self.camera_offset())
        self.draw_bottom_warning()
        screens.draw_hud(self.screen, self)
        screens.draw_boss_hud(self.screen, self)
        # Virtual buttons only on Android touch; they overlap paddle on desktop/web
        if os.environ.get("ANDROID_APP_PATH") or os.environ.get("ANDROID_ARGUMENT"):
            self.android_input.draw(self.screen)

    def draw_shield_aura(self, surface):
        shield_level = effects_module.skill_count(self.selected_skills, SkillType.SHIELD)
        if self.shield_charges <= 0 and shield_level <= 0:
            return

        charge_ratio = min(1.0, self.shield_charges / max(1, shield_level + 1))
        pulse_amount = pulse(2.6, self.shield_charges * 0.55)
        now = pygame.time.get_ticks() / 1000.0
        aura_color = mix(RETRO_PALETTE["brick3"], RETRO_PALETTE["accent_alt"], min(1.0, shield_level * 0.18))
        alpha = 50 + int(charge_ratio * 60) + int(pulse_amount * 30)
        inflate_x = 22 + shield_level * 5 + self.shield_charges * 4
        inflate_y = 20 + shield_level * 3

        shield_rects = [self.paddle.rect] + getattr(self.paddle, "extra_rects", [])
        for rect in shield_rects:
            aura_rect = rect.inflate(inflate_x, inflate_y)

            # Outer glow ellipse
            glow = pygame.Surface((aura_rect.width + 22, aura_rect.height + 22), pygame.SRCALPHA)
            for i in range(4, 0, -1):
                r = pygame.Rect(2 + i, 2 + i, glow.get_width() - 4 - i * 2, glow.get_height() - 4 - i * 2)
                a = max(10, alpha // (i + 1))
                pygame.draw.ellipse(glow, (*aura_color, a), r, 1 + i)
            surface.blit(glow, (aura_rect.x - 11, aura_rect.y - 11))

            # Animated rotating arc segments
            num_segments = max(2, shield_level + self.shield_charges)
            for seg in range(num_segments):
                angle_start = now * 1.2 + seg * (2 * math.pi / num_segments)
                angle_span = math.radians(50 + shield_level * 8)
                seg_alpha = alpha - 15 + int(pulse(2.0, seg * 0.7) * 25)
                draw_rect = aura_rect.inflate(-4, -4)
                pygame.draw.arc(surface, (*aura_color, max(10, seg_alpha)),
                                draw_rect, angle_start, angle_start + angle_span, 2)

            # Bright inner core arc
            core_alpha = alpha + 20 + int(pulse(3.0) * 30)
            pygame.draw.arc(surface, (*RETRO_PALETTE["text_white"], min(100, core_alpha)),
                            aura_rect.inflate(-8, -6),
                            math.radians(200 + math.sin(now * 1.5) * 15),
                            math.radians(340 + math.sin(now * 1.5) * 15), 1)

            # Shield hex grid pattern — simplified for WASM perf
            if shield_level >= 2 or self.shield_charges >= 2:
                hex_alpha = 8 + int(pulse(1.8) * 7)
                step_x, step_y = 14, 12
                for hx in range(aura_rect.x + 8, aura_rect.right - 8, step_x):
                    for hy in range(aura_rect.y + 6, aura_rect.bottom - 4, step_y):
                        ox = 7 if (hy // step_y) % 2 else 0
                        px, py = hx + ox, hy
                        if aura_rect.collidepoint(px, py):
                            pygame.draw.circle(surface, (*aura_color, hex_alpha), (px, py), 1)

    def draw_bottom_warning(self):
        if not any(ball.active and ball.dy > 0 and ball.rect.bottom > self.height - 150 for ball in self.balls):
            return
        warning = pygame.Rect(0, self.height - 68, self.width, 34)
        if self._warning_overlay.get_size() != warning.size:
            self._warning_overlay = pygame.Surface(warning.size, pygame.SRCALPHA)
        overlay = self._warning_overlay
        overlay.fill((*RETRO_PALETTE["danger"], 20 + int(pulse(5.0) * 35)))
        self.screen.blit(overlay, warning)
        pygame.draw.line(self.screen, RETRO_PALETTE["danger"], warning.topleft, warning.topright, 2)






    def level_special_kinds(self, grid=None):
        grid = grid or self.brick_grid
        kinds = []
        for brick in grid.bricks:
            if brick.kind in BRICK_KIND_INFO and brick.kind not in kinds:
                kinds.append(brick.kind)
        return kinds




    def skill_usage_text(self, skill_type, guide):
        usage = guide.get("use", "")
        if skill_type == SkillType.CANNON:
            key = self.keybindings.action_label("up")
            return f"Active. Press {key} when the cooldown is ready."
        if skill_type == SkillType.GRAVITY_WELL:
            key = self.keybindings.action_label("down")
            return f"Active. Hold {key} while the ball is falling."
        return usage


    def controls_row_rect(self, index):
        panel_width = min(680, self.width - 70)
        panel_height = min(620, self.height - 80)
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        return pygame.Rect(panel_x + 44, panel_y + 112 + index * 42, panel_width - 88, 36)

    def settings_option_rects(self):
        panel_width = min(560, self.width - 90)
        panel_height = min(380, self.height - 120)
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        return (
            pygame.Rect(panel_x + 54, panel_y + 132, panel_width - 108, 46),
            pygame.Rect(panel_x + 54, panel_y + 194, panel_width - 108, 46),
        )




    def difficulty_speed_bonus(self):
        bonus = min(2.6, max(0, (self.level - 1) * 0.10))
        if self.level > 1 and (self.level - 1) % 5 == 0:
            bonus = max(0, bonus - 0.22)
        return bonus

    def apply_level_difficulty_to_balls(self):
        stabilizer_count = effects_module.skill_count(self.selected_skills, SkillType.SPEED_UP)
        speed_bonus = max(0, self.difficulty_speed_bonus() - stabilizer_count * 0.28)
        for ball in self.balls:
            target_speed = min(10.6, ball.speed + speed_bonus)
            current_speed = max(0.01, math.hypot(ball.dx, ball.dy))
            scale = target_speed / current_speed
            ball.dx *= scale
            ball.dy *= scale
            ball.speed = target_speed

    def update_helper_paddles(self):
        drone_count = effects_module.skill_count(self.selected_skills, SkillType.DRONES)
        echo_count = effects_module.skill_count(self.selected_skills, SkillType.ECHO_PADDLES)
        patrol_count = effects_module.skill_count(self.selected_skills, SkillType.PATROL_PADDLES)
        self.paddle.extra_rects = []
        if drone_count == 0 and echo_count == 0 and patrol_count == 0:
            return

        if drone_count:
            # Drones fire auto-projectiles upward (offensive support)
            if not hasattr(self, '_drone_timer'):
                self._drone_timer = 0
            self._drone_timer += 1
            if self._drone_timer >= max(25, 90 - drone_count * 10):
                self._drone_timer = 0
                color = RETRO_PALETTE["brick1"]
                for offset in [-20, 20]:
                    self.bullets.append(LaserBullet(
                        (self.paddle.rect.centerx + offset, self.paddle.rect.y - 10),
                        dy=-8, color=color, damage=1))

        if echo_count:
            width = min(92, 46 + echo_count * 10)
            y = self.paddle.rect.y - 68
            # Smooth follow: echo paddle lags behind main paddle (inertia)
            if not hasattr(self, '_echo_x'):
                self._echo_x = float(self.paddle.rect.centerx)
            target_x = float(self.paddle.rect.centerx)
            # Lerp factor: higher echo_count = faster follow (less lag)
            lerp = min(0.35, 0.08 + echo_count * 0.06)
            self._echo_x += (target_x - self._echo_x) * lerp
            center = pygame.Rect(0, y, width, self.paddle.height)
            center.centerx = int(self._echo_x)
            center.x = max(0, min(self.width - width, center.x))
            self.paddle.extra_rects.append(center)
            if echo_count >= 2:
                side_width = max(34, width - 24)
                gap = 44
                left = pygame.Rect(max(0, center.left - gap - side_width), y - 26, side_width, self.paddle.height)
                right = pygame.Rect(min(self.width - side_width, center.right + gap), y - 26, side_width, self.paddle.height)
                self.paddle.extra_rects.extend([left, right])

        if patrol_count:
            width = min(84, 44 + patrol_count * 8)
            travel = max(80, min(230, self.width // 4 + patrol_count * 18))
            phase = pulse(1.35, patrol_count * 0.4)
            x = self.paddle.rect.centerx - travel // 2 + int(phase * travel) - width // 2
            y = self.paddle.rect.y - 104
            patrol = pygame.Rect(max(0, min(self.width - width, x)), y, width, self.paddle.height)
            self.paddle.extra_rects.append(patrol)
            if patrol_count >= 2:
                mirror_x = self.width - patrol.right
                self.paddle.extra_rects.append(pygame.Rect(max(0, min(self.width - width, mirror_x)), y - 24, width, self.paddle.height))

    def fire_paddle_projectiles(self, ball):
        laser_count = effects_module.skill_count(self.selected_skills, SkillType.LASER)
        volley_count = effects_module.skill_count(self.selected_skills, SkillType.VOLLEY)
        ricochet_count = effects_module.skill_count(self.selected_skills, SkillType.RICOCHET)
        scatter_count = effects_module.skill_count(self.selected_skills, SkillType.SCATTER_SHOT)
        if laser_count:
            bullet = LaserBullet(ball.rect.center, damage=1)
            bullet._trail_color = (255, 100, 100)
            self.bullets.append(bullet)
            self.audio.play("projectile", 0.65)
        if volley_count:
            spread = min(2.6, 1.3 + volley_count * 0.30)
            color = RETRO_PALETTE["brick3"]
            b1 = LaserBullet((ball.rect.centerx - 10, ball.rect.centery), dx=-spread, color=color)
            b2 = LaserBullet((ball.rect.centerx + 10, ball.rect.centery), dx=spread, color=color)
            b1._trail_color = (100, 255, 200); b2._trail_color = (100, 255, 200)
            self.bullets.extend([b1, b2])
            if volley_count >= 2:
                self.bullets.append(LaserBullet((ball.rect.centerx, ball.rect.centery - 6), dy=-8.5, color=color))
            self.audio.play("projectile", 0.75)
        if ricochet_count:
            direction = 1 if ball.dx >= 0 else -1
            spread = min(3.5, 2.2 + ricochet_count * 0.30)
            damage = 1
            color = RETRO_PALETTE["brick3"]
            self.bullets.append(LaserBullet(
                (ball.rect.centerx, ball.rect.centery),
                dx=direction * spread,
                dy=-7.0,
                damage=damage,
                color=color,
                bounces=ricochet_count,
                bounds_width=self.width,
                bounds_height=self.height,
            ))
            self.audio.play("projectile", 0.7)
        if scatter_count:
            count = min(4, 2 + scatter_count)  # 3-4 projectiles
            start = -(count - 1) / 2
            color = RETRO_PALETTE["brick1"]
            for index in range(count):
                dx = (start + index) * 0.95
                self.bullets.append(LaserBullet(
                    (ball.rect.centerx, ball.rect.centery),
                    dx=dx,
                    dy=-8.4,
                    damage=1,
                    color=color,
                    bounds_width=self.width,
                    bounds_height=self.height,
                ))
            self.audio.play("projectile", 0.72)

    def handle_special_brick_effects(self, brick, ball=None, destroyed=False):
        if brick.kind == BrickKind.PULSE and ball is not None:
            self.audio.play("pulse", 0.65)
            direction = 1 if ball.rect.centerx >= brick.rect.centerx else -1
            ball.dx += direction * 0.75
            limit = max(1.0, ball.speed * 1.05)
            ball.dx = max(-limit, min(limit, ball.dx))
            # Pulse shockwave ring
            self._spawn_shockwave_ring(brick.rect.centerx, brick.rect.centery,
                                       RETRO_PALETTE["brick3"], count=6)
        elif brick.kind == BrickKind.REGEN and not destroyed:
            self.repair_nearby_brick(brick)

        if not destroyed:
            return

        if brick.kind == BrickKind.BOMB:
            self.audio.play("bomb", 0.9)
            self.trigger_impact_feedback(0.08, 5)
            # Directional explosion burst from source
            self._spawn_explosion_burst(brick.rect.centerx, brick.rect.centery,
                                        brick.color, count=14)
            for nearby in self.brick_grid.get_nearby_bricks(brick, 74):
                destroyed_nearby = effects_module.damage_brick(nearby, 1)
                nearby.hit_color = (255, 255, 255)
                self.award_brick_score(nearby, destroyed_nearby)
                for _ in range(3):
                    self.particle_system.append(Particle(
                        nearby.rect.centerx, nearby.rect.centery, nearby.color,
                        speed=5, size_range=(1, 4),
                        directional=True,
                        angle_bias=math.atan2(nearby.rect.centery - brick.rect.centery,
                                              nearby.rect.centerx - brick.rect.centerx)))
        elif brick.kind == BrickKind.CHARGE:
            self.audio.play("charge", 0.75)
            self.run_state.energy += 2
            # Energy absorption — particles flow from brick toward paddle
            self._spawn_energy_drain(brick.rect.centerx, brick.rect.centery,
                                     self.paddle.rect.centerx, self.paddle.rect.y,
                                     RETRO_PALETTE["brick1"], count=10)
        elif brick.kind == BrickKind.PULSE:
            # Extra burst on destruction
            self._spawn_shockwave_ring(brick.rect.centerx, brick.rect.centery,
                                       RETRO_PALETTE["brick3"], count=10)
        elif brick.kind == BrickKind.PRISM and ball is not None:
            self.spawn_prism_ball(ball)
            # Rainbow particle burst
            self._spawn_rainbow_burst(brick.rect.centerx, brick.rect.centery, count=12)
        elif brick.kind == BrickKind.SENTRY:
            self.spawn_enemy(brick.rect.centerx, brick.rect.centery + 34)
            self.audio.play("projectile", 0.55)
            # Spawn portal effect
            self._spawn_portal_effect(brick.rect.centerx, brick.rect.centery,
                                      RETRO_PALETTE["brick4"])

    def repair_nearby_brick(self, source):
        candidates = [
            brick for brick in self.brick_grid.get_nearby_bricks(source, 86)
            if brick.active and brick.hp < brick.max_hp
        ]
        if not candidates:
            return False
        target = min(candidates, key=lambda brick: brick.hp)
        target.hp += 1
        target.hit_color = RETRO_PALETTE["paddle"]
        self.audio.play("charge", 0.45)
        # Healing particles flow from source to target
        for i in range(5):
            t = i / 4.0
            px = source.rect.centerx + (target.rect.centerx - source.rect.centerx) * t
            py = source.rect.centery + (target.rect.centery - source.rect.centery) * t
            self.particle_system.append(Particle(
                px, py, RETRO_PALETTE["paddle"], speed=1, size_range=(1, 3)))
        return True

    def spawn_prism_ball(self, ball):
        if len(self.balls) >= 7:
            return False
        new_ball = self.clone_ball(ball)
        new_ball.dx = -ball.dx if abs(ball.dx) > 0.5 else ball.speed * 0.5
        new_ball.dy = -abs(ball.dy) if ball.dy > 0 else ball.dy
        self.balls.append(new_ball)
        self.run_state.balls_count = len(self.balls)
        self.audio.play("split", 0.75)
        return True

    def clone_ball(self, ball):
        new_ball = Ball(self.width, self.height, self.paddle)
        new_ball.x = ball.x
        new_ball.y = ball.y
        new_ball.rect.center = ball.rect.center
        new_ball.speed = ball.speed
        new_ball.size = ball.size
        new_ball.base_size = ball.base_size
        new_ball.max_bounce_angle = ball.max_bounce_angle
        new_ball.center_nudge = ball.center_nudge
        new_ball.dx = ball.dx
        new_ball.dy = ball.dy
        return new_ball

    def trigger_split_charge(self, ball):
        if self.split_charges <= 0 or len(self.balls) >= 6:
            return

        self.split_charges -= 1
        self.audio.play("split", 0.85)
        new_ball = self.clone_ball(ball)
        new_ball.dx = -ball.dx if abs(ball.dx) > 0.4 else -ball.speed * 0.45
        self.balls.append(new_ball)


# Standalone desktop entry point (not used by pygbag).
# python3 -c "import asyncio; from game.engine import GameEngine; asyncio.run(GameEngine(1024,768).run())"
