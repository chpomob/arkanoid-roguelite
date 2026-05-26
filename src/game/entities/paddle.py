import pygame
from game.assets import draw_paddle_sprite, mix
from game.viewport import Viewport


class Paddle:
    """Paddle entity with normalized coordinates. Pixels only via Viewport."""

    def __init__(self, viewport: Viewport, color=(0, 228, 54), nw=0.0977, nh=0.0195):
        """
        Args:
            viewport: Viewport for normalized→pixel projection
            nw: normalized width (default 100/1024 ≈ 0.0977)
            nh: normalized height (default 15/768 ≈ 0.0195)
        """
        self.vp = viewport
        self.base_nw = nw
        self.nw = nw
        self.width_bonus = 0.0
        self.nh = nh
        # Backward-compat aliases for tests
        self.base_width = nw * viewport.w  # approximate; tests use raw values
        self.height = int(nh * viewport.h)  # backward compat
        self.width = int(self.rect.width) if hasattr(self, 'rect') and self.rect else int(nw * viewport.w)
        # Start centered horizontally, near bottom
        self.nx = 0.5 - nw / 2
        self.ny = 1.0 - viewport.legacy_y(40) - nh  # same as old y = height - 40
        self.speed = viewport.nspeed(7)  # normalized: old 7 px/frame
        self.color = color
        self.rect = self._compute_rect()
        self.lives = 3
        self.is_alive = True
        self.last_move_direction = 1
        self.extra_rects = []

    def _compute_rect(self) -> pygame.Rect:
        """Compute pixel rect from normalized coords."""
        return self.vp.rect_nw_nh(self.nx, self.ny, self.nw, self.nh)

    def add_width(self, amount: float):
        """Add normalized width bonus."""
        self.width_bonus += amount
        self.update_rect()

    def move(self, keys, keybindings=None, touch_nx=None):
        """
        Move paddle. If touch_nx is provided, paddle follows finger directly.
        Otherwise uses keyboard input via keybindings or raw key dict.
        """
        screen_w = 1.0  # normalized space

        if touch_nx is not None:
            target = touch_nx - self.nw / 2
            target = max(0.0, min(1.0 - self.nw, target))
            self.nx = target
            self.last_move_direction = 1 if self.nx > self.nx else (-1 if self.nx < self.nx else 0)
        else:
            self.last_move_direction = 0
            # Support both KeyBindings objects and raw key dicts
            if keybindings and hasattr(keybindings, 'action_down'):
                left = keybindings.action_down(keys, "left")
                right = keybindings.action_down(keys, "right")
            else:
                left = keys.get(pygame.K_LEFT, False) if hasattr(keys, 'get') else keys[pygame.K_LEFT]
                right = keys.get(pygame.K_RIGHT, False) if hasattr(keys, 'get') else keys[pygame.K_RIGHT]

            if left:
                self.nx -= self.speed / 60.0  # speed is n/s, per-frame = /fps
                self.last_move_direction = -1
            if right:
                self.nx += self.speed / 60.0
                self.last_move_direction = 1

            self.nx = max(0.0, min(1.0 - self.nw, self.nx))

        self.rect = self._compute_rect()

    def update_rect(self):
        """Recalculate rect after width change, keeping centered."""
        self.nw = max(0.05, self.base_nw + self.width_bonus)
        self.nx = 0.5 - self.nw / 2
        self.rect = self._compute_rect()

    def draw(self, screen, feedback=0.0):
        feedback = max(0.0, min(1.0, feedback))
        for rect in self.extra_rects:
            self._draw_segment(screen, rect, mix((70, 212, 255), (255, 255, 255), feedback * 0.45))
        self._draw_segment(screen, self.rect, mix(self.color, (255, 255, 255), feedback * 0.55))

    def _draw_segment(self, screen, rect, color):
        draw_paddle_sprite(screen, rect, color)

    def reset(self):
        self.lives = 3
        self.is_alive = True
        self.nx = 0.5 - self.nw / 2
        self.ny = 1.0 - self.vp.legacy_y(40) - self.nh
        self.rect = self._compute_rect()
