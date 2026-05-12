import pygame
import random
from enum import Enum
from game.assets import draw_brick_sprite
from game.bosses import boss_by_id, is_boss_level
from game.ui import RETRO_PALETTE

class BrickKind(Enum):
    NORMAL = "normal"
    TOUGH = "tough"
    BOMB = "bomb"
    PULSE = "pulse"
    CHARGE = "charge"
    REGEN = "regen"
    PRISM = "prism"
    SENTRY = "sentry"


BRICK_KIND_INFO = {
    BrickKind.TOUGH: ("TOUGH", "extra hits"),
    BrickKind.BOMB: ("BOMB", "splash damage"),
    BrickKind.PULSE: ("PULSE", "kicks ball"),
    BrickKind.CHARGE: ("CHARGE", "adds energy"),
    BrickKind.REGEN: ("REGEN", "repairs bricks"),
    BrickKind.PRISM: ("PRISM", "splits ball"),
    BrickKind.SENTRY: ("SENTRY", "spawns enemy"),
}


class Brick:
    def __init__(self, rect, hp=1, color=(255, 100, 100), kind=BrickKind.NORMAL):
        self.rect = rect
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.base_color = color
        self.kind = kind
        self.active = True
        self.hit_color = None

    def hit(self, amount=1):
        return self.take_damage(amount)

    def draw(self, surface):
        if self.active:
            draw_color = self.hit_color if self.hit_color else self.color
            marker = None if self.kind == BrickKind.NORMAL else self.kind.value
            draw_brick_sprite(surface, self.rect, draw_color, marker, self.hp, self.max_hp)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def reset(self):
        self.active = True
        self.hp = self.max_hp
        self.color = self.base_color
        self.hit_color = None


def _layout_wall(row, col, level, cols, rows):
    return True

def _layout_stagger(row, col, level, cols, rows):
    return row % 2 == 0 or (col + level) % 2 == 0

def _layout_lanes(row, col, level, cols, rows):
    return col % 4 != 1 or row in (0, rows - 1)

def _layout_fortress(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row < 2 or abs(col - center) <= 3 or (row + col) % 4 == 0

def _layout_chevron(row, col, level, cols, rows):
    center = (cols - 1) / 2
    distance = abs(col - center)
    # At higher levels, open more gaps
    spacing = 2 if level >= 10 else 1
    return distance <= row * spacing + 1 or row == 0 or row == rows - 1

def _layout_broken_wall(row, col, level, cols, rows):
    return (row + col + level) % 5 != 0

def _layout_crossfire(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row in (0, rows - 1) or col in (1, cols - 2) or abs(col - center) <= row % 3

def _layout_well(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row == 0 or abs(col - center) >= row * 0.7 or (row + col) % 4 == 0

def _layout_vault(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row in (0, rows - 1) or col in (0, cols - 1) or abs(col - center) <= 1.5

def _layout_reactor(row, col, level, cols, rows):
    center = (cols - 1) / 2
    distance = abs(col - center)
    return row in (0, rows - 1) or distance <= 1.5 or (row in (1, rows - 2) and distance <= 3.5)

def _layout_sentinel_gate(row, col, level, cols, rows):
    return row in (0, rows - 1) or col in (1, cols - 2) or (row == 2 and col in (3, 6))

def _layout_pulse_nest(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row == 0 or abs(col - center) >= 2.5 or (row + col) % 4 == 0

def _layout_forge_ring(row, col, level, cols, rows):
    center = (cols - 1) / 2
    distance = abs(col - center)
    return row in (0, rows - 1) or distance >= 3.5 or (row in (1, 3) and col in (2, 7))

def _layout_prism_court(row, col, level, cols, rows):
    center = (cols - 1) / 2
    return row == 0 or row == rows - 1 or abs(col - center) <= row * 0.75 or (row + col) % 5 == 0

def _layout_archon_bastion(row, col, level, cols, rows):
    return row in (0, 1, rows - 1) or col in (0, cols - 1, 2, cols - 3)

def _layout_reactor_eye(row, col, level, cols, rows):
    center = (cols - 1) / 2
    distance = abs(col - center)
    return row in (0, rows - 1) or distance <= 2.5 or (row + col) % 3 != 1


LAYOUT_PREDICATES = {
    "wall": _layout_wall,
    "stagger": _layout_stagger,
    "lanes": _layout_lanes,
    "fortress": _layout_fortress,
    "chevron": _layout_chevron,
    "broken_wall": _layout_broken_wall,
    "crossfire": _layout_crossfire,
    "well": _layout_well,
    "vault": _layout_vault,
    "reactor": _layout_reactor,
    "sentinel_gate": _layout_sentinel_gate,
    "pulse_nest": _layout_pulse_nest,
    "forge_ring": _layout_forge_ring,
    "prism_court": _layout_prism_court,
    "archon_bastion": _layout_archon_bastion,
    "reactor_eye": _layout_reactor_eye,
}


class BrickGrid:
    def __init__(self, screen_width, screen_height, cols=10, rows=5, level=1, top=164, boss_id=None, seed=None):
        self.cols = cols
        self.rows = rows
        self.bricks = []
        self.level = level
        self.boss_id = boss_id
        self.boss_definition = boss_by_id(boss_id) if boss_id else None
        self.padding = 10
        self.brick_width = (screen_width - (self.padding * (cols + 1))) // cols
        self.brick_height = 25
        self.top = top
        self.layout_name = self.layout_for_level(level, self.boss_definition, seed=seed)
        self.theme_name = self.theme_for_level(level, self.boss_definition, seed=seed)
        self._create_grid(screen_width, level)

    def _create_grid(self, screen_width, level):
        current_y = self.top
        palette_colors = [
            RETRO_PALETTE["brick1"],
            RETRO_PALETTE["brick2"],
            RETRO_PALETTE["brick3"],
            RETRO_PALETTE["brick4"],
            RETRO_PALETTE["accent_alt"],
        ]
        for row in range(self.rows):
            current_x = self.padding
            for col in range(self.cols):
                if self.has_brick(row, col, level):
                    rect = pygame.Rect(current_x, current_y, self.brick_width, self.brick_height)
                    kind = self.kind_for_slot(row, col, level)
                    hp = self.hp_for_slot(row, level, kind)
                    color = self.color_for_kind(kind, palette_colors[row % len(palette_colors)])
                    self.bricks.append(Brick(rect, hp, color, kind))
                current_x += self.brick_width + self.padding
            current_y += self.brick_height + self.padding

    @staticmethod
    def layout_for_level(level, boss_definition=None, seed=None):
        if boss_definition:
            return boss_definition.arena
        if level % 10 == 0:
            return "reactor"
        if level % 5 == 0:
            return "vault"
        early = ["wall", "stagger", "lanes", "fortress"]
        mid = ["chevron", "broken_wall", "crossfire", "well", "sentinel_gate", "pulse_nest"]
        late = ["broken_wall", "crossfire", "well", "forge_ring", "prism_court", "archon_bastion", "reactor_eye"]
        if level <= 8:
            pool = early
        elif level <= 14:
            pool = mid
        else:
            pool = late
        if seed is not None and seed != 0:
            rng = random.Random(seed * 31 + level)
            return rng.choice(pool)
        return pool[(level - 1) % len(pool)]

    @staticmethod
    def theme_for_level(level, boss_definition=None, seed=None):
        if boss_definition:
            return boss_definition.theme
        themes = ["Neon Gate", "Pulse Yard", "Foundry", "Data Vault", "Sentinel Gate", "Forge Ring", "Prism Court"]
        if seed is not None and seed != 0:
            rng = random.Random(seed * 37 + (level - 1) // 3)
            return rng.choice(themes)
        return themes[((level - 1) // 3) % len(themes)]

    def has_brick(self, row, col, level):
        predicate = LAYOUT_PREDICATES.get(self.layout_name)
        if predicate is None:
            return True
        return predicate(row, col, level, self.cols, self.rows)

    def hp_for_slot(self, row, level, kind):
        # Slightly tougher early, ramps harder at mid, aggressive at L28+
        if level <= 12:
            base_hp = 1 + min(4, (level - 1) // 4)
        elif level <= 28:
            base_hp = 1 + min(6, (level - 8) // 3)
        else:
            base_hp = 3 + min(10, (level - 18) // 2)
        row_bonus = 1 if row >= max(1, self.rows - 2) and level >= 3 else 0
        kind_bonus = 1 if kind == BrickKind.TOUGH else 0
        return base_hp + row_bonus + kind_bonus

    @staticmethod
    def special_interval(level, base, floor):
        return max(floor, base - min(9, level // 2))

    def kind_for_slot(self, row, col, level):
        layout = self.layout_name
        center_col = self.cols // 2
        if is_boss_level(level) and self.boss_definition:
            return self.boss_kind_for_slot(row, col)
        if layout == "reactor" and level >= 10 and row in (1, self.rows - 2) and abs(col - center_col) <= 1:
            return BrickKind.CHARGE
        if layout == "vault" and level >= 5 and row in (0, self.rows - 1) and col in (1, self.cols - 2):
            return BrickKind.TOUGH
        if layout == "crossfire" and level >= 7 and (row == col % self.rows or row + col == self.cols - 1):
            return BrickKind.PULSE
        if layout == "well" and level >= 8 and row >= self.rows // 2 and abs(col - center_col) <= 1:
            return BrickKind.BOMB
        charge_interval = self.special_interval(level, 19, 12)
        bomb_interval = self.special_interval(level, 13, 8)
        pulse_interval = self.special_interval(level, 15, 9)
        if level >= 6 and (row * 7 + col * 3 + level) % charge_interval == 0:
            return BrickKind.CHARGE
        if level >= 3 and (row * 5 + col + level) % bomb_interval == 0:
            return BrickKind.BOMB
        if level >= 4 and (row + col * 2 + level) % pulse_interval == 0:
            return BrickKind.PULSE
        if level >= 7 and row <= 1 and (row * 3 + col * 5 + level) % 14 == 0:
            return BrickKind.REGEN
        if level >= 8 and (row * 4 + col * 7 + level) % 16 == 0:
            return BrickKind.PRISM
        if level >= 9 and row <= 2 and (row * 6 + col * 2 + level) % 18 == 0:
            return BrickKind.SENTRY
        if level >= 2 and row >= self.rows // 2 and (row + col + level) % 4 == 0:
            return BrickKind.TOUGH
        return BrickKind.NORMAL

    def boss_kind_for_slot(self, row, col):
        layout = self.layout_name
        center_col = self.cols // 2
        if layout == "sentinel_gate":
            if col in (1, self.cols - 2) or row == self.rows - 1:
                return BrickKind.TOUGH
            if row == 2 and col in (3, 6):
                return BrickKind.CHARGE
        if layout == "pulse_nest":
            if (row + col) % 3 == 0:
                return BrickKind.PULSE
            if row >= self.rows // 2 and abs(col - center_col) >= 3:
                return BrickKind.TOUGH
        if layout == "forge_ring":
            if row in (1, 3) and col in (2, 7):
                return BrickKind.BOMB
            if row in (0, self.rows - 1):
                return BrickKind.TOUGH
        if layout == "prism_court":
            if abs(col - center_col) <= 1 or (row + col) % 5 == 0:
                return BrickKind.PRISM
            if row == 0:
                return BrickKind.PULSE
        if layout == "archon_bastion":
            if col in (2, self.cols - 3) and row <= 2:
                return BrickKind.SENTRY
            if row == self.rows - 1:
                return BrickKind.CHARGE
            return BrickKind.TOUGH
        if layout == "reactor_eye":
            if abs(col - center_col) <= 1 and row in (1, 2, 3):
                return BrickKind.CHARGE
            if (row + col) % 4 == 0:
                return BrickKind.REGEN
            if row <= 1:
                return BrickKind.SENTRY
        return BrickKind.NORMAL

    @staticmethod
    def color_for_kind(kind, fallback):
        if kind == BrickKind.TOUGH:
            return (194, 213, 255)
        if kind == BrickKind.BOMB:
            return (255, 98, 86)
        if kind == BrickKind.PULSE:
            return (76, 219, 255)
        if kind == BrickKind.CHARGE:
            return (255, 219, 92)
        if kind == BrickKind.REGEN:
            return (95, 236, 128)
        if kind == BrickKind.PRISM:
            return (208, 118, 255)
        if kind == BrickKind.SENTRY:
            return (255, 148, 84)
        return fallback

    def draw(self, surface):
        for brick in self.bricks:
            brick.draw(surface)

    def update(self):
        self.bricks = [b for b in self.bricks if b.active]

    def get_brick_at(self, pos):
        for brick in self.bricks:
            if brick.rect.collidepoint(pos):
                return brick
        return None

    def get_nearby_bricks(self, source, radius):
        nearby = []
        for brick in self.bricks:
            if brick is source or not brick.active:
                continue
            dx = brick.rect.centerx - source.rect.centerx
            dy = brick.rect.centery - source.rect.centery
            if (dx * dx + dy * dy) <= radius * radius:
                nearby.append(brick)
        return nearby
