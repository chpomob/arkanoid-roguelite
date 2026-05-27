import pygame
import random
import math
from game.assets import draw_ball_sprite
from game.viewport import Viewport


class Ball:
    """Ball with normalized physics. All positions/velocities in [0,1] space."""

    def __init__(self, *args, y_offset=0.0, **kwargs):
        """
        New API: Ball(viewport, paddle, y_offset=0.0)
        Legacy API: Ball(screen_width, screen_height, paddle, y_offset=0)
        """
        if len(args) >= 3:
            # Legacy: Ball(screen_width, screen_height, paddle, ...)
            from game.viewport import Viewport
            vp = args[2].vp if hasattr(args[2], 'vp') else Viewport(args[0], args[1])
            paddle = args[2]
            y_off = args[3] if len(args) > 3 else y_offset
        elif len(args) == 2:
            vp, paddle = args
            y_off = y_offset
        else:
            raise TypeError(f"Ball() requires (viewport, paddle) or (width, height, paddle)")

        self.vp = vp
        # Normalized speed (old 5 px/frame → n/sec)
        self.speed = vp.nspeed(5)  # ~0.293 n/s
        # Normalized size (12 / min(1024,768) = 12/768 ≈ 0.0156)
        self.nsize = vp.legacy_s(12)
        # Start centered horizontally, mid-screen vertically
        self.nx = 0.5
        self.ny = 0.5 + y_off
        self.ndx = (self.speed * 0.1) * (1 if random.random() > 0.5 else -1)
        self.ndy = -self.speed * 0.2
        self.color = (255, 0, 255)
        self.rect = self._compute_rect()
        self.paddle = paddle
        self.active = True
        self.trail = []
        self.hit_paddle = False
        self.previous_rect = self.rect.copy()
        self.base_nsize = self.nsize
        # Bounce physics (angles preserved — no normalization needed)
        self.max_bounce_angle = math.radians(68)
        self.center_nudge = 0.13
        # Speed thresholds — converted from old pixel/frame to normalized values
        self.min_horizontal_speed = vp.nspeed(0.55, fps=1.0)  # old: 0.55 px/frame
        self.wall_exit_horizontal_speed = vp.nspeed(0.9, fps=1.0)  # old: 0.9 px/frame

    def _compute_rect(self) -> pygame.Rect:
        """Build pygame.Rect from normalized coords via viewport."""
        ps = self.vp.nsize(self.nsize)
        cx = self.vp.px(self.nx)
        cy = self.vp.py(self.ny)
        return pygame.Rect(cx - ps // 2, cy - ps // 2, ps, ps)

    def sync_rect_to_position(self):
        """Update pixel rect to match normalized position."""
        self.rect = self._compute_rect()

    def ensure_horizontal_motion(self, direction=None, minimum=None):
        minimum = self.min_horizontal_speed if minimum is None else minimum
        if abs(self.ndx) >= minimum:
            return
        if direction is None:
            direction = 1 if self.ndx >= 0 else -1
        self.ndx = minimum if direction >= 0 else -minimum

    def move(self, *args, **kwargs):
        """Move ball in normalized space.
        Supports both new API move(playfield_top_n=0.0) and 
        legacy API move(screen_width, screen_height, playfield_top=0).
        """
        if len(args) >= 2 and isinstance(args[0], (int, float)):
            # Legacy call: move(screen_width, screen_height, playfield_top)
            _, _, playfield_top_px = (list(args) + [0])[:3]
        else:
            playfield_top_n = kwargs.get('playfield_top_n', kwargs.get('playfield_top', 0.0))
            if len(args) == 1:
                playfield_top_n = args[0]
            return self._move(playfield_top_n)

        # Convert legacy pixel top to normalized if needed
        playfield_top_n = 0.0
        if playfield_top_px > 0:
            # Legacy mode: playfield_top was in pixels from 1024-based coords
            playfield_top_n = playfield_top_px / self.vp._ref_h
        
        return self._move(playfield_top_n)

    def _move(self, playfield_top_n=0.0):
        """Internal move implementation in normalized space."""
        if not self.active:
            self.rect.center = self.paddle.rect.center
            self.rect.y = self.paddle.rect.y - self.vp.nsize(self.nsize) // 2
            self.nx = self.vp.from_screen(*self.rect.center)[0]
            self.ny = self.vp.from_screen(*self.rect.center)[1]
            self.previous_rect = self.rect.copy()
            self.trail = []
            self.color = (50, 50, 50)
            return

        self.previous_rect = self.rect.copy()
        # Apply velocity (normalized/sec) — dt is handled by caller
        self.nx += self.ndx / 60.0
        self.ny += self.ndy / 60.0
        self.sync_rect_to_position()

        trail_length = max(4, min(9, int(math.hypot(self.ndx * 20, self.ndy * 20))))
        while len(self.trail) >= trail_length:
            self.trail.pop(0)
        self.trail.append(self.rect.center)
        
        # Wall collisions (left/right edges)
        if self.rect.left <= 0:
            self.rect.left = 0
            self.nx = self.vp.from_screen(*self.rect.center)[0]
            if self.ndx < 0:
                self.ndx = -self.ndx
            self.ensure_horizontal_motion(1, self.wall_exit_horizontal_speed)
        elif self.rect.right >= self.vp.w:
            self.rect.right = int(self.vp.w)
            self.nx = self.vp.from_screen(*self.rect.center)[0]
            if self.ndx > 0:
                self.ndx = -self.ndx
            self.ensure_horizontal_motion(-1, self.wall_exit_horizontal_speed)

        # Top collision (playfield ceiling)
        playfield_top_px = self.vp.py(playfield_top_n)
        if self.rect.top <= playfield_top_px and self.ndy < 0:
            self.rect.top = playfield_top_px
            self.ndy = -self.ndy
            self.ny = self.vp.from_screen(*self.rect.center)[1]

        self.ensure_horizontal_motion()

    def update(self, *args, apply_damage=True, playfield_top_n=0.0, **kwargs):
        """
        Update ball physics and handle brick/paddle collisions.
        New: update(brick_layers, apply_damage=True, playfield_top_n=0.0)
        Legacy: update(screen_width, screen_height, brick_layers, apply_damage=True, playfield_top=0)
        """
        if len(args) >= 2 and isinstance(args[0], (int, float)):
            # Legacy: update(screen_width, screen_height, brick_layers, ...)
            brick_layers = args[2] if len(args) > 2 else []
            playfield_top_px = kwargs.get('playfield_top', 0) if 'playfield_top' in kwargs else (args[3] if len(args) > 3 else 0)
            playfield_top_n = playfield_top_px / self.vp._ref_h if playfield_top_px > 0 else 0.0
        elif len(args) >= 1 and hasattr(args[0], '__iter__'):
            brick_layers = args[0]
        elif 'brick_layers' in kwargs:
            brick_layers = kwargs['brick_layers']
        else:
            brick_layers = []
        self.hit_paddle = False
        self.move(playfield_top_n)

        hit_brick = None

        # Paddle collision
        for paddle_rect in [self.paddle.rect] + getattr(self.paddle, "extra_rects", []):
            if self.active and self.rect.colliderect(paddle_rect):
                if self.ndy > 0:
                    self.bounce_off_paddle(paddle_rect)
                break

        # Brick collision
        if self.active:
            collisions = []
            for brick_layer in brick_layers:
                for brick in brick_layer.bricks:
                    if brick.active and self.rect.colliderect(brick.rect):
                        collisions.append(brick)

            if collisions:
                hit_brick = self.primary_collision_brick(collisions)
                axis = self.brick_collision_axis(hit_brick, collisions)
                self.dmg_brick(hit_brick, axis)
                if apply_damage:
                    hit_brick.take_damage(1)

        # Re-sync normalized from pixel rect
        self.nx = self.vp.from_screen(*self.rect.center)[0]
        self.ny = self.vp.from_screen(*self.rect.center)[1]
        return hit_brick

    def bounce_off_paddle(self, paddle_rect=None):
        paddle_rect = paddle_rect or self.paddle.rect
        half_width = max(1, paddle_rect.width / 2)
        offset = (self.rect.centerx - paddle_rect.centerx) / half_width
        offset = max(-1.0, min(1.0, offset))
        angle = self.paddle_bounce_angle(offset, self.ndx, self.ndy)
        speed = max(0.01, math.hypot(self.ndx, self.ndy), self.speed * 0.2)
        self.ndx = speed * math.sin(angle)
        self.ndy = -abs(speed * math.cos(angle))
        self.rect.bottom = paddle_rect.top
        self.nx = self.vp.from_screen(*self.rect.center)[0]
        self.ny = self.vp.from_screen(*self.rect.center)[1]
        self.hit_paddle = True

    def paddle_bounce_angle(self, offset, incoming_ndx=None, incoming_ndy=None):
        sign = -1 if offset < 0 else 1
        magnitude = abs(offset)
        source_dx = self.ndx if incoming_ndx is None else incoming_ndx
        source_dy = self.ndy if incoming_ndy is None else incoming_ndy

        if magnitude < self.center_nudge:
            move_direction = getattr(self.paddle, "last_move_direction", 0)
            if move_direction == 0:
                move_direction = 1 if source_dx >= 0 else -1
            sign = move_direction
            magnitude = self.center_nudge

        eased = magnitude ** 1.35
        position_angle = sign * eased * self.max_bounce_angle
        incoming_angle = math.atan2(source_dx, max(0.01, abs(source_dy)))
        incoming_angle = max(-self.max_bounce_angle, min(self.max_bounce_angle, incoming_angle))

        arrival_weight = 0.18 + ((1.0 - magnitude) * 0.16)
        arrival_weight = max(0.18, min(0.36, arrival_weight))
        angle = (position_angle * (1.0 - arrival_weight)) + (incoming_angle * arrival_weight)

        min_angle = max(math.radians(5), self.max_bounce_angle * 0.07)
        if abs(angle) < min_angle:
            if abs(position_angle) >= min_angle:
                angle = math.copysign(min_angle, position_angle)
            elif abs(incoming_angle) >= min_angle:
                angle = math.copysign(min_angle, incoming_angle)
            else:
                angle = math.copysign(min_angle, sign)

        return max(-self.max_bounce_angle, min(self.max_bounce_angle, angle))

    def primary_collision_brick(self, bricks):
        if len(bricks) == 1:
            return bricks[0]
        if abs(self.ndy) >= abs(self.ndx):
            if self.ndy > 0:
                return min(bricks, key=lambda brick: brick.rect.top)
            return max(bricks, key=lambda brick: brick.rect.bottom)
        if self.ndx > 0:
            return min(bricks, key=lambda brick: brick.rect.left)
        return max(bricks, key=lambda brick: brick.rect.right)

    def brick_collision_axis(self, brick, collisions=None):
        collisions = collisions or [brick]
        vertical_motion = abs(self.ndy) >= abs(self.ndx)

        if len(collisions) > 1 and vertical_motion:
            has_left_contact = any(other.rect.centerx < self.rect.centerx for other in collisions)
            has_right_contact = any(other.rect.centerx > self.rect.centerx for other in collisions)
            if has_left_contact and has_right_contact:
                return "vertical"

        if len(collisions) > 1 and not vertical_motion:
            has_top_contact = any(other.rect.centery < self.rect.centery for other in collisions)
            has_bottom_contact = any(other.rect.centery > self.rect.centery for other in collisions)
            if has_top_contact and has_bottom_contact:
                return "horizontal"

        if self.ndy > 0 and self.previous_rect.bottom <= brick.rect.top:
            return "vertical"
        if self.ndy < 0 and self.previous_rect.top >= brick.rect.bottom:
            return "vertical"
        if self.ndx > 0 and self.previous_rect.right <= brick.rect.left:
            return "horizontal"
        if self.ndx < 0 and self.previous_rect.left >= brick.rect.right:
            return "horizontal"

        overlap_x = min(self.rect.right, brick.rect.right) - max(self.rect.left, brick.rect.left)
        overlap_y = min(self.rect.bottom, brick.rect.bottom) - max(self.rect.top, brick.rect.top)

        if overlap_x == overlap_y:
            return "horizontal" if abs(self.ndx) > abs(self.ndy) else "vertical"
        return "horizontal" if overlap_x < overlap_y else "vertical"

    def dmg_brick(self, brick, axis=None):
        axis = axis or self.brick_collision_axis(brick)

        if axis == "horizontal":
            self.ndx = -self.ndx
            if self.rect.centerx < brick.rect.centerx:
                self.rect.right = brick.rect.left - 1
            else:
                self.rect.left = brick.rect.right + 1
        else:
            self.ndy = -self.ndy
            if self.rect.centery < brick.rect.centery:
                self.rect.bottom = brick.rect.top - 1
            else:
                self.rect.left = brick.rect.bottom + 1

        self.nx = self.vp.from_screen(*self.rect.center)[0]
        self.ny = self.vp.from_screen(*self.rect.center)[1]
        brick.hit_color = (255, 255, 255)

    # Backward-compat aliases for tests/migration
    @property
    def dx(self): return self.ndx
    @dx.setter
    def dx(self, v): self.ndx = v

    @property
    def dy(self): return self.ndy
    @dy.setter
    def dy(self, v): self.ndy = v

    @property
    def x(self): return self.nx
    @x.setter
    def x(self, v): self.nx = v

    @property
    def y(self): return self.ny
    @y.setter
    def y(self, v): self.ny = v

    @property
    def size(self): return self.nsize
    @size.setter
    def size(self, v): self.nsize = v

    @property
    def base_size(self): return self.base_nsize
    @base_size.setter
    def base_size(self, v): self.base_nsize = v

    def draw(self, screen):
        if self.active:
            draw_ball_sprite(screen, self.rect, self.color, self.trail)
