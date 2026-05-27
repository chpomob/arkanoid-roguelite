import pygame
import random
import math
from game.assets import draw_ball_sprite

class Ball:
    def __init__(self, screen_width, screen_height, paddle, y_offset=0):
        self._speed_base = 600  # ×100 units — skills modify this
        self._speed_px = 6.0    # self._speed_base / 100, actual pixels/frame
        self.size = 12
        self.x = screen_width / 2
        self.y = screen_height / 2 + y_offset
        self.dx = (self._speed_px * 0.5) * (1 if random.random() > 0.5 else -1)
        self.dy = -self._speed_px
        self.color = (255, 0, 255) # Magenta
        self.rect = pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
        self.paddle = paddle
        self.active = True
        self.trail = []
        self.hit_paddle = False
        self.previous_rect = self.rect.copy()
        self.base_size = self.size
        self.max_bounce_angle = math.radians(68)
        self.center_nudge = 0.13
        self.min_horizontal_speed = 0.55
        self.wall_exit_horizontal_speed = 0.9

    def sync_rect_to_position(self):
        self.rect.center = (int(self.x + 0.5), int(self.y + 0.5))

    def sync_px_speed(self):
        """Recalculate pixel speed from _speed_base, scale dx/dy proportionally."""
        new_px = self._speed_base / 100.0
        if self._speed_px > 0 and new_px != self._speed_px:
            scale = new_px / self._speed_px
            self.dx *= scale
            self.dy *= scale
        self._speed_px = new_px

    @property
    def speed(self):
        return self._speed_base / 100.0  # pixel speed for external code

    @speed.setter
    def speed(self, value):
        """Set _speed_base from a pixel-speed value (backward compat)."""
        self._speed_base = int(round(value * 100))
        self.sync_px_speed()

    def ensure_horizontal_motion(self, direction=None, minimum=None):
        minimum = self.min_horizontal_speed if minimum is None else minimum
        if abs(self.dx) >= minimum:
            return

        if direction is None:
            direction = 1 if self.dx >= 0 else -1
        self.dx = minimum if direction >= 0 else -minimum

    def move(self, screen_width, screen_height, playfield_top=0):
        if not self.active:
            self.rect.center = self.paddle.rect.center
            self.rect.y = self.paddle.rect.y - self.size // 2
            self.x = self.rect.centerx
            self.y = self.rect.centery
            self.previous_rect = self.rect.copy()
            self.trail = []
            self.color = (50, 50, 50)
            return

        self.previous_rect = self.rect.copy()
        self.x += self.dx
        self.y += self.dy
        self.sync_rect_to_position()

        trail_length = max(3, min(6, int(math.hypot(self.dx, self.dy))))
        while len(self.trail) >= trail_length:
            self.trail.pop(0)
        self.trail.append((self.rect.centerx, self.rect.centery))

        # Wall collisions. Clamp any overlap, then force a visible side exit.
        # This prevents shallow angles from being rounded into wall-hugging motion.
        if self.rect.left <= 0:
            self.rect.left = 0
            self.x = self.rect.centerx
            if self.dx < 0:
                self.dx = -self.dx
            self.ensure_horizontal_motion(1, self.wall_exit_horizontal_speed)
        elif self.rect.right >= screen_width:
            self.rect.right = screen_width
            self.x = self.rect.centerx
            if self.dx > 0:
                self.dx = -self.dx
            self.ensure_horizontal_motion(-1, self.wall_exit_horizontal_speed)
        
        if self.rect.top <= playfield_top and self.dy < 0:
            self.rect.top = playfield_top
            self.dy = -self.dy
            self.y = self.rect.centery
        
        self.ensure_horizontal_motion()

    def update(self, screen_width, screen_height, brick_layers, apply_damage=True, playfield_top=0):
        self.hit_paddle = False
        self.move(screen_width, screen_height, playfield_top)
        
        hit_brick = None
        
        # Paddle collision (Priority)
        for paddle_rect in [self.paddle.rect] + getattr(self.paddle, "extra_rects", []):
            if self.active and self.rect.colliderect(paddle_rect):
                if self.dy > 0:
                    self.bounce_off_paddle(paddle_rect)
                break
        
        # Brick collision
        if self.active:
            collisions = []
            for brick_layer in brick_layers:
                collisions.extend(brick_layer.query_rect(self.rect))
            
            if collisions:
                hit_brick = self.primary_collision_brick(collisions)
                axis = self.brick_collision_axis(hit_brick, collisions)
                self.dmg_brick(hit_brick, axis)
                if apply_damage:
                    hit_brick.take_damage(1)

        self.x = self.rect.centerx
        self.y = self.rect.centery
        return hit_brick

    def bounce_off_paddle(self, paddle_rect=None):
        paddle_rect = paddle_rect or self.paddle.rect
        half_width = max(1, paddle_rect.width / 2)
        offset = (self.rect.centerx - paddle_rect.centerx) / half_width
        offset = max(-1.0, min(1.0, offset))
        angle = self.paddle_bounce_angle(offset, self.dx, self.dy)
        speed = max(1, math.hypot(self.dx, self.dy), self.speed)
        self.dx = speed * math.sin(angle)
        self.dy = -abs(speed * math.cos(angle))
        self.rect.bottom = paddle_rect.top
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.hit_paddle = True

    def paddle_bounce_angle(self, offset, incoming_dx=None, incoming_dy=None):
        sign = -1 if offset < 0 else 1
        magnitude = abs(offset)
        source_dx = self.dx if incoming_dx is None else incoming_dx
        source_dy = self.dy if incoming_dy is None else incoming_dy

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

        if abs(self.dy) >= abs(self.dx):
            if self.dy > 0:
                return min(bricks, key=lambda brick: brick.rect.top)
            return max(bricks, key=lambda brick: brick.rect.bottom)

        if self.dx > 0:
            return min(bricks, key=lambda brick: brick.rect.left)
        return max(bricks, key=lambda brick: brick.rect.right)

    def brick_collision_axis(self, brick, collisions=None):
        collisions = collisions or [brick]
        vertical_motion = abs(self.dy) >= abs(self.dx)

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

        if self.dy > 0 and self.previous_rect.bottom <= brick.rect.top:
            return "vertical"
        if self.dy < 0 and self.previous_rect.top >= brick.rect.bottom:
            return "vertical"
        if self.dx > 0 and self.previous_rect.right <= brick.rect.left:
            return "horizontal"
        if self.dx < 0 and self.previous_rect.left >= brick.rect.right:
            return "horizontal"

        overlap_x = min(self.rect.right, brick.rect.right) - max(self.rect.left, brick.rect.left)
        overlap_y = min(self.rect.bottom, brick.rect.bottom) - max(self.rect.top, brick.rect.top)

        if overlap_x == overlap_y:
            return "horizontal" if abs(self.dx) > abs(self.dy) else "vertical"
        return "horizontal" if overlap_x < overlap_y else "vertical"

    def dmg_brick(self, brick, axis=None):
        axis = axis or self.brick_collision_axis(brick)

        if axis == "horizontal":
            self.dx = -self.dx
            # Clamp to the edge exactly at the point of entry/penetration to minimize "teleport" feel
            if self.rect.centerx < brick.rect.centerx:
                self.rect.right = brick.rect.left - 0.1
            else:
                self.rect.left = brick.rect.right + 0.1
        else:
            self.dy = -self.dy
            if self.rect.centery < brick.rect.centery:
                self.rect.bottom = brick.rect.top - 0.1
            else:
                self.rect.top = brick.rect.bottom + 0.1

        self.x = self.rect.centerx
        self.y = self.rect.centery
        
        # Remove game logic (damage) from physics logic.
        # brick.hit_color is kept for visual feedback before the engine destroys it or clears effects.
        brick.hit_color = (255, 255, 255)

    def draw(self, screen):
        if self.active:
            draw_ball_sprite(screen, self.rect, self.color, self.trail)
