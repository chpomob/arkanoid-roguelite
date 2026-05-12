"""Bot implementations for automated gameplay simulation.

Each bot produces:
- held_keys: set of action names to hold this frame (e.g. {"left", "right"})
- events: list of pygame events to post (for confirm, menu navigation, etc.)
"""

import math
import random
from abc import ABC, abstractmethod

import pygame


class BaseBot(ABC):
    """Abstract bot that controls the game through held keys and posted events."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self._frame = 0

    def reset(self):
        """Called when a new game/level starts."""
        self._frame = 0
        self._on_reset()

    def _on_reset(self):
        """Override in subclasses for per-bot reset logic."""
        pass

    @abstractmethod
    def held_keys(self, engine) -> set:
        """Return set of action names to hold this frame ('left', 'right', 'up', 'down', 'confirm')."""
        ...

    def events(self, engine, dt: float) -> list:
        """Return list of pygame events to post this frame (e.g. KEYDOWN for confirm)."""
        self._frame += 1
        return []


class SimpleBot(BaseBot):
    """Tracks the ball with the paddle and picks the first available skill.

    Has configurable reaction delay and paddle speed factor.
    """

    def __init__(self, seed: int = 42, reaction_delay: float = 0.0, speed_factor: float = 1.0):
        super().__init__(seed)
        self.reaction_delay = reaction_delay
        self.speed_factor = speed_factor
        self._consecutive_misses = 0

    def held_keys(self, engine) -> set:
        keys = set()

        # Always add confirm for menu/navigation states (before paddle logic)
        if engine.state in ("TITLE", "SKILL_SELECTION", "LEVEL_SUMMARY", "BRICK_INTRO", "BOSS_INTRO", "GAMEOVER"):
            keys.add("confirm")
            # Don't move paddle in menu states
            if engine.state != "PLAYING":
                return keys

        if not engine.balls:
            return keys

        ball = engine.balls[0]
        paddle = engine.paddle
        target_x = ball.rect.centerx

        # Don't chase if ball is moving upward
        if ball.dy <= 0:
            self._consecutive_misses = 0
            return keys

        # Apply reaction delay: ignore ball for first N frames after bounce
        if self.reaction_delay > 0:
            self._consecutive_misses += 1
            if self._consecutive_misses < self.reaction_delay * 60:
                return keys

        # Enemy shot dodging (priority over tracking)
        dodge = self._dodge_shots(engine)
        if dodge:
            keys.add(dodge)
            return keys

        center = paddle.rect.centerx
        diff = target_x - center

        # Dead zone to avoid jitter
        if abs(diff) < self.speed_factor * 5:
            return keys

        if diff < 0:
            keys.add("left")
        else:
            keys.add("right")

        return keys

    def events(self, engine, dt: float) -> list:
        evts = super().events(engine, dt)
        state = engine.state

        # Auto-advance through menus that use event-based confirm
        if state == "TITLE":
            evts.append(self._make_confirm(engine))

        return evts

    def _make_confirm(self, engine) -> pygame.event.Event:
        """Create a KEYDOWN event matching the confirm binding."""
        key = engine.keybindings.key_for_action("confirm", slot=0)
        return pygame.event.Event(pygame.KEYDOWN, {"key": key, "unicode": ""})

    def _dodge_shots(self, engine) -> str | None:
        """Return 'left' or 'right' to dodge incoming enemy shots, or None."""
        if not engine.enemy_shots:
            return None
        paddle = engine.paddle
        danger_zone = 200
        
        # Find all shots in danger zone
        threats = []
        for shot in engine.enemy_shots:
            if not shot.active:
                continue
            if shot.rect.bottom < paddle.rect.y - danger_zone:
                continue
            if shot.rect.top > paddle.rect.bottom + 10:
                continue
            threats.append(shot)
        
        if not threats:
            return None
        
        # Check if any shot will hit the paddle
        will_hit = False
        for shot in threats:
            # Project shot path to paddle y-level
            if shot.speed <= 0:
                continue
            frames_to_paddle = (paddle.rect.y - shot.rect.bottom) / shot.speed
            future_x = shot.rect.centerx + shot.dx * frames_to_paddle
            if abs(future_x - paddle.rect.centerx) < paddle.rect.width * 0.6 + 15:
                will_hit = True
                break
        
        if not will_hit:
            return None
        
        # Find safest direction: count threats left vs right of paddle
        left_threats = sum(1 for s in threats if s.rect.centerx < paddle.rect.centerx)
        right_threats = sum(1 for s in threats if s.rect.centerx > paddle.rect.centerx)
        
        if left_threats >= right_threats and paddle.rect.right < engine.width - 30:
            return "right"
        elif right_threats > left_threats and paddle.rect.left > 30:
            return "left"
        return None


class NoisyBot(SimpleBot):
    """Like SimpleBot but introduces random mistakes and reaction variance.

    noise: probability (0-1) of making a wrong move each frame
    jitter: max pixel offset for paddle positioning error
    miss_confirm: probability of failing to press confirm when needed
    """

    def __init__(self, seed: int = 42, noise: float = 0.05, jitter: float = 30.0, miss_confirm: float = 0.1):
        super().__init__(seed)
        self.noise = noise
        self.jitter = jitter
        self.miss_confirm = miss_confirm

    def held_keys(self, engine) -> set:
        keys = super().held_keys(engine)

        # Randomly invert or drop keys
        if self.rng.random() < self.noise:
            if keys:
                if self.rng.random() < 0.5:
                    keys = set()  # drop all
                else:
                    # invert direction
                    new = set()
                    for k in keys:
                        if k == "left":
                            new.add("right")
                        elif k == "right":
                            new.add("left")
                        else:
                            new.add(k)
                    keys = new

        return keys

    def events(self, engine, dt: float) -> list:
        evts = super().events(engine, dt)

        # Randomly miss confirm presses
        if self.rng.random() < self.miss_confirm:
            evts = [e for e in evts if not self._is_confirm(e, engine)]

        return evts

    def _is_confirm(self, event, engine) -> bool:
        confirm_key = engine.keybindings.key_for_action("confirm", slot=0)
        return event.type == pygame.KEYDOWN and event.key == confirm_key
