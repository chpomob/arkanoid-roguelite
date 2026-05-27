import math
from abc import ABC, abstractmethod

import pygame

from game.assets import draw_boss_sprite, draw_enemy_sprite, draw_projectile_sprite
from game.ui import RETRO_PALETTE


class EnemyShot:
    def __init__(self, start_pos, speed=5.0, damage=1, dx=0.0, color=None):
        self.x = start_pos[0]
        self.y = start_pos[1]
        self.speed = speed
        self.dx = dx
        self.damage = damage
        self.active = True
        self.rect = pygame.Rect(self.x - 3, self.y - 4, 6, 12)
        self.color = color or RETRO_PALETTE["danger"]

    def update(self, dt):
        self.x += self.dx
        self.y += self.speed
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, screen):
        draw_projectile_sprite(screen, self.rect, self.color)


class BaseEnemy(ABC):
    """Shared interface for all enemy types (regular and boss)."""

    is_boss: bool = False
    active: bool
    rect: pygame.Rect
    color: tuple

    @abstractmethod
    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def take_damage(self, amount: int = 1) -> bool:
        ...

    @abstractmethod
    def can_fire(self) -> bool:
        ...

    @abstractmethod
    def fire(self) -> list:
        """Return a list of EnemyShot instances."""
        ...

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        ...


class Enemy(BaseEnemy):
    is_boss: bool = False

    def __init__(self, x, y, bounds, speed=1.45, cooldown=1.8, hp=1):
        self.x = x
        self.y = y
        self.bounds = bounds
        self.speed = speed
        self.direction = 1
        self.cooldown = cooldown
        self.fire_timer = cooldown
        self.hp = hp
        self.active = True
        self.rect = pygame.Rect(int(x - 14), int(y - 10), 28, 20)
        self.color = RETRO_PALETTE["brick4"]

    def update(self, dt):
        self.x += self.speed * self.direction
        if self.x <= self.bounds[0]:
            self.x = self.bounds[0]
            self.direction = 1
        elif self.x >= self.bounds[1]:
            self.x = self.bounds[1]
            self.direction = -1
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.rect.center = (int(self.x), int(self.y))

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def can_fire(self):
        return self.active and self.fire_timer <= 0

    def fire(self):
        self.fire_timer = self.cooldown
        return [EnemyShot((self.rect.centerx, self.rect.bottom + 4))]

    def draw(self, screen):
        if self.active:
            draw_enemy_sprite(screen, self.rect, self.color)


class BossEnemy(BaseEnemy):
    is_boss: bool = True

    def __init__(self, definition, level, screen_width, playfield_top):
        self.definition = definition
        self.name = definition.name
        self.tier = definition.tier
        self.level = level
        self.x = screen_width / 2
        self.base_y = playfield_top + 68
        self.y = self.base_y
        self.bounds = (72, screen_width - 72)
        self.speed = definition.speed + max(0, level - definition.tier * 5) * 0.025
        self.direction = 1
        self.cooldown = max(0.62, definition.cooldown - (definition.tier - 1) * 0.05)
        self.fire_timer = self.cooldown * 0.65
        self.max_hp = definition.hp + max(0, level - 5) // 2 * 100
        self.hp = self.max_hp
        self.active = True
        self.color = definition.color
        self.accent = definition.accent
        self.phase = 0.0
        self.rect = pygame.Rect(0, 0, 108, 48)
        self.rect.center = (int(self.x), int(self.y))

    def update(self, dt):
        self.phase += dt
        health_ratio = self.hp / max(1, self.max_hp)
        haste = 1.0 + (1.0 - health_ratio) * 0.30
        self.x += self.speed * haste * self.direction
        if self.x <= self.bounds[0]:
            self.x = self.bounds[0]
            self.direction = 1
        elif self.x >= self.bounds[1]:
            self.x = self.bounds[1]
            self.direction = -1
        self.y = self.base_y + math.sin(self.phase * (1.7 + self.tier * 0.18)) * (8 + self.tier * 2)
        self.fire_timer = max(0.0, self.fire_timer - dt)  # no haste on fire rate
        self.rect.center = (int(self.x), int(self.y))

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def can_fire(self):
        return self.active and self.fire_timer <= 0

    def fire(self):
        self.fire_timer = self.cooldown
        origin = (self.rect.centerx, self.rect.bottom + 6)
        shot_speed = 4.2 + self.tier * 0.45
        color = self.accent
        pattern = self.definition.pattern
        if pattern == "spread":
            return [EnemyShot(origin, shot_speed, dx=dx, color=color) for dx in (-1.25, 0, 1.25)]
        if pattern == "alternating":
            side = -1 if int(self.phase * 2) % 2 == 0 else 1
            return [EnemyShot(origin, shot_speed, dx=side * 1.9, color=color), EnemyShot((origin[0] - side * 28, origin[1]), shot_speed * 0.95, dx=-side * 0.8, color=color)]
        if pattern == "burst":
            return [EnemyShot((origin[0] + offset, origin[1]), shot_speed + index * 0.25, dx=offset / 38, color=color) for index, offset in enumerate((-40, 0, 40))]
        if pattern == "fan":
            return [EnemyShot(origin, shot_speed, dx=dx, color=color) for dx in (-2.2, -1.1, 0, 1.1, 2.2)]
        if pattern == "cross":
            return [
                EnemyShot(origin, shot_speed, dx=0, color=color),
                EnemyShot((origin[0] - 44, origin[1] - 4), shot_speed * 0.92, dx=1.35, color=color),
                EnemyShot((origin[0] + 44, origin[1] - 4), shot_speed * 0.92, dx=-1.35, color=color),
            ]
        if pattern == "storm":
            wave = math.sin(self.phase * 2.4)
            return [EnemyShot(origin, shot_speed + abs(dx) * 0.12, dx=dx + wave * 0.35, color=color) for dx in (-2.4, -1.2, 0, 1.2, 2.4)]
        return [EnemyShot(origin, shot_speed, color=color)]

    def draw(self, screen):
        if self.active:
            draw_boss_sprite(screen, self.rect, self.color, self.accent, self.phase)
